import json 
import machine
import uasyncio as asyncio
from modules.detector import BounceDetector
from modules.indicator import DeviceIndicator
from modules.notifier import BackendNotifier


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


async def main():
    cfg = load_config()

    indicator = DeviceIndicator(cfg["notifier"])
    try:
        from net import wifi_manager
        wifi_manager.connect()
    except Exception as e:
        await indicator.error()
        print("WiFi init error:", e)
    detector = BounceDetector(cfg["detector"])
    notifier = BackendNotifier(cfg["notifier"], indicator=indicator)

    print("Waiting for detector events...")
    async for event in detector:
        print("Detector event:", event)
        await notifier.send_event(event)

    print("Main loop done.")

asyncio.run(main())