import time 
from ulab import numpy as np


class BounceDetectedEvent:
    def __init__(self, bounce_ctr):
        self.timestamp = time.ticks_ms()
        self.bounce_ctr = bounce_ctr
    
    def to_dict(self):
        return {
            "type": "bounce-detected",
            "timestamp": self.timestamp,
            "bounce_ctr": self.bounce_ctr
        }

class DebugSamplesEvent:
    def __init__(self, samples, is_bounce, bounce_ctr, sample_rate):
        self.timestamp = time.ticks_ms()
        self.samples = samples
        self.is_bounce = is_bounce
        self.bounce_ctr = bounce_ctr
        self.sample_rate = sample_rate

    def to_dict(self):
        return {
            "type": "debug-samples",
            "timestamp": self.timestamp,
            "samples": np.array(self.samples, dtype=np.int16).tolist(),
            "is_bounce": self.is_bounce,
            "bounce_ctr": self.bounce_ctr,
            "sample_rate": self.sample_rate
        }

    