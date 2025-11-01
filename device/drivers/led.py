from machine import Pin
class LED:
    def __init__(self, pin, active_high=True):
        self.p = Pin(pin, Pin.OUT)
        self.ah = active_high
        self.off()
    def on(self):
        self.p.value(1 if self.ah else 0)
    def off(self):
        self.p.value(0 if self.ah else 1)
    def toggle(self):
        self.p.value(0 if self.p.value() else 1)
