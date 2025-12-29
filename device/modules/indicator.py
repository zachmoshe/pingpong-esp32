import machine 
import neopixel 
import uasyncio as asyncio


COLOR_OFF = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_MAGENTA = (255, 0, 255)
COLOR_WHITE = (255, 255, 255)

_BLINK_DURATION_MS = 128

_LED_GPIO_PIN = 2

class DeviceIndicator:
    def __init__(self, cfg):
        # Init LED notification
        self.led = neopixel.NeoPixel(machine.Pin(_LED_GPIO_PIN), 1, bpp=3)
        self.led.fill((0, 0, 0))
        self.led.write()

    async def blink(self, color, times):
        for _ in range(times):
            self.led.fill(color)
            self.led.write()
            await asyncio.sleep_ms(_BLINK_DURATION_MS)
            self.led.fill(COLOR_OFF)
            self.led.write()
            await asyncio.sleep_ms(_BLINK_DURATION_MS)

    async def error(self):
        await self.blink(COLOR_RED, 3)

    async def info(self):
        await self.blink(COLOR_BLUE, 1)

    async def pingpong_bounce(self):
        await self.blink(COLOR_GREEN, 1)

