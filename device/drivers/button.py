from machine import Pin
class Button:
    def __init__(self, pin, pull=Pin.PULL_UP):
        self.p = Pin(pin, Pin.IN, pull)
    def pressed(self):
        return self.p.value() == 0
