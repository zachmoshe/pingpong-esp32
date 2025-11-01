from machine import I2S, Pin
import uasyncio as asyncio
from ulab import numpy as np

from lib import wav

_SCK_PIN = 25
_WS_PIN = 26
_SD_PIN = 32
_DEFAULT_SAMPLE_RATE = 16000
_DEFAULT_SAMPLES_PER_FRAME = 512

_CONVERT_TO_24_BIT_WEIGHT = np.array([2**24, 2**16, 2**8])

class BounceDetector:

    def __init__(self, cfg):
        self.sample_rate = cfg.get("sample_rate", _DEFAULT_SAMPLE_RATE)
        self.samples_per_frame = cfg.get("samples_per_frame", _DEFAULT_SAMPLES_PER_FRAME)
        
        self.i2s = I2S(
            0,
            sck=Pin(_SCK_PIN),       # BCLK
            ws=Pin(_WS_PIN),        # LRCLK
            sd=Pin(_SD_PIN),        # Mic DOUT
            mode=I2S.RX,
            bits=32,
            format=I2S.MONO,
            rate=self.sample_rate,
            ibuf=1024,
        )
        self.buf = bytearray(self.samples_per_frame * 4)
        self.u8_2d = np.frombuffer(self.buf, dtype=np.uint8).reshape((self.samples_per_frame, 4))            # [sample, byte]


    def __aiter__(self):
        # Return the iterator object itself
        return self

    async def __anext__(self):
        with wav.WAVWriter(file_path="output.wav", sample_rate=self.sample_rate, channels=1, bits_per_sample=24) as wav_writer:
            while True:
                n = self.i2s.readinto(self.buf)
                if n != len(self.buf):
                    print(f"Expected {len(self.buf)} samples, got {n}")
                    continue
                elif n <= 0:
                    print("No samples read")
                    continue

                u24 = np.dot(self.u8_2d[:, :3], _CONVERT_TO_24_BIT_WEIGHT)
                wav_writer.write(u24.tobytes())
                print(wav_writer.data_size)