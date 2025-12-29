import math
import time

from machine import I2S, Pin
import uasyncio as asyncio
from ulab import numpy as np
from ulab import scipy as scipy
import urequests

from lib import wav
from modules import events 


_SCK_PIN = 25
_WS_PIN = 26
_SD_PIN = 32
_DEFAULT_SAMPLE_RATE = 16000
_INITIAL_MAX_VALUE = 50

_CONVERT_TO_24_BIT_WEIGHT = np.array([2**24, 2**16, 2**8])


def _butter_sos_even(N, fc_hz, fs_hz, btype='lowpass'):
    """
    Return SOS (shape [N/2, 6]) like scipy.signal.butter(..., output='sos')
    btype: 'lowpass' or 'highpass'
    N must be even.
    """
    if (N % 2) != 0:
        raise ValueError('Order N must be even for this implementation.')
    if btype not in ('lowpass', 'highpass'):
        raise ValueError('btype must be lowpass or highpass')

    fs = float(fs_hz)
    fc = float(fc_hz)

    # Bilinear prewarp for target cutoff: wc = 2*fs*tan(pi*fc/fs)
    wc = 2.0 * fs * math.tan(math.pi * fc / fs)
    # Bilinear constant s = c*(1 - z^-1)/(1 + z^-1)
    c = 2.0 * fs

    # Prepare SOS array: [b0, b1, b2, 1.0, a1, a2]
    sos = np.zeros((N // 2, 6))

    # Butterworth pole angles for quadratic sections (real coeffs)
    # phi_k = pi/2 + (2k-1)*pi/(2N), k=1..N/2
    for k in range(1, N // 2 + 1):
        phi = math.pi * 0.5 + (2*k - 1) * math.pi / (2.0 * N)
        cosphi = math.cos(phi)

        # Analog quadratic denominator: s^2 - 2*wc*cos(phi)*s + wc^2
        A0, A1, A2 = 1.0, -2.0 * wc * cosphi, wc * wc

        # Analog numerator per section:
        # Low-pass: omega_c^2
        # High-pass: s^2
        if btype == 'lowpass':
            B0, B1, B2 = 0.0, 0.0, wc * wc
        else:  # highpass
            B0, B1, B2 = 1.0, 0.0, 0.0

        # Bilinear transform: multiply through by (1 + z^-1)^2
        # Useful identities:
        # (1 - z^-1)^2 = 1 - 2z^-1 + z^-2
        # (1 + z^-1)^2 = 1 + 2z^-1 + z^-2
        # (1 - z^-1)(1 + z^-1) = 1 - z^-2

        # Denominator (digital, unnormalized)
        d0 = A0*(c*c) + A1*c + A2
        d1 = -2.0*A0*(c*c) + 2.0*A2
        d2 = A0*(c*c) - A1*c + A2

        # Numerator (digital, unnormalized)
        if btype == 'lowpass':
            # B2 * (1 + 2z^-1 + z^-2)
            n0 = B2
            n1 = 2.0*B2
            n2 = B2
        else:
            # B0*c^2 * (1 - 2z^-1 + z^-2)
            n0 = B0*(c*c)
            n1 = -2.0*B0*(c*c)
            n2 = B0*(c*c)

        # Normalize so a0 = 1
        inv_d0 = 1.0 / d0
        b0 = n0 * inv_d0
        b1 = n1 * inv_d0
        b2 = n2 * inv_d0
        a1 = d1 * inv_d0
        a2 = d2 * inv_d0

        idx = k - 1
        sos[idx, 0] = b0
        sos[idx, 1] = b1
        sos[idx, 2] = b2
        sos[idx, 3] = 1.0
        sos[idx, 4] = a1
        sos[idx, 5] = a2

    return sos



class BounceDetector:

    def __init__(self, cfg):
        self.sample_rate = cfg.get("sample_rate", _DEFAULT_SAMPLE_RATE)
        self.window_size_ms = cfg["window_size_ms"]
        self.window_size_samples = int(self.window_size_ms * self.sample_rate / 1000)
        self.debug = cfg.get("debug", False)

        self.i2s = I2S(
            0,
            sck=Pin(_SCK_PIN),       # BCLK
            ws=Pin(_WS_PIN),        # LRCLK
            sd=Pin(_SD_PIN),        # Mic DOUT
            mode=I2S.RX,
            bits=32,
            format=I2S.MONO,
            rate=self.sample_rate,
            ibuf=min(4096, self.window_size_samples * 4),
        )
        self.buf = bytearray(self.window_size_samples * 4)
        self.u8_2d = np.frombuffer(self.buf, dtype=np.uint8).reshape((self.window_size_samples, 4))   # [sample, byte]

        self.rolling_max_short = _INITIAL_MAX_VALUE
        self.rolling_max_long = _INITIAL_MAX_VALUE
        self.rolling_max_short_decay_factor = cfg["rolling_max_short_decay_factor"]
        self.rolling_max_long_decay_factor = cfg["rolling_max_long_decay_factor"]
        self.bounce_threshold = cfg["bounce_threshold"]

        self.highpass_filter_cutoff_freq = cfg["highpass_filter_cutoff_freq"]
        self.highpass_filter_sos = _butter_sos_even(4, self.highpass_filter_cutoff_freq, self.sample_rate, btype='highpass')
        self.prev_highpass_filter_output = 0
        self.prev_highpass_filter_input = 0

        self.bounce_ctr = 0 

        self.server_url = cfg["server_url"]
        if self.server_url.endswith("/"):
            self.server_url = self.server_url[:-1]
        self.debug_audio_samples_endpoint = f"{self.server_url}{cfg['debug_audio_samples_endpoint']}"


    def __aiter__(self):
        # Return the iterator object itself
        return self

    async def __anext__(self):

        while True:
            n = self.i2s.readinto(self.buf)
            if n != len(self.buf):
                print(f"Expected {len(self.buf)} samples, got {n}")
                continue
            elif n <= 0:
                print("No samples read")
                continue

            samples = np.array(
                np.dot(self.u8_2d[:, :3], _CONVERT_TO_24_BIT_WEIGHT),
                dtype=np.int16
            )
            samples = scipy.signal.sosfilt(self.highpass_filter_sos, samples)
            window_max_value = np.max(samples)  
            self.rolling_max_short = self.rolling_max_short_decay_factor * self.rolling_max_short + (1 - self.rolling_max_short_decay_factor) * window_max_value
            self.rolling_max_long = self.rolling_max_long_decay_factor * self.rolling_max_long + (1 - self.rolling_max_long_decay_factor) * window_max_value
            signal = (window_max_value - self.rolling_max_short) / self.rolling_max_long
            is_bounce = signal > self.bounce_threshold

            if self.debug:
                await self._send_debug_samples_to_backend(samples, is_bounce)

            if is_bounce:
                self.bounce_ctr += 1
                return events.BounceDetectedEvent(bounce_ctr=self.bounce_ctr)



    async def _send_debug_samples_to_backend(self, samples, is_bounce):
        """Send samples to the backend via HTTP POST"""
        payload = events.DebugSamplesEvent(samples, is_bounce, self.bounce_ctr, self.sample_rate)
        try:
            response = urequests.post(
                self.debug_audio_samples_endpoint,
                json=payload.to_dict(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                print(f"Backend returned status {response.status_code} {response.text}")
            
            response.close()
            
        except Exception as e:
            print(f"Error sending to backend: {e}")
