import json
import uasyncio as asyncio
from modules.detector import BounceDetector
from modules.indicator import DeviceIndicator
from modules.notifier import BackendNotifier
import boot

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

async def main():
    cfg = load_config()

    indicator = DeviceIndicator(cfg["indicator"] | cfg["general"])
    try:
        from net import wifi_manager
        wifi_manager.connect()
    except Exception as e:
        await indicator.error()
        print("WiFi init error:", e)

    try:
        detector = BounceDetector(cfg["detector"] | cfg["general"])
        notifier = BackendNotifier(cfg["notifier"] | cfg["general"], indicator=indicator)
    except Exception as e:
        await indicator.error()
        print("Couldn't initialize device components:", e)
        return

    await indicator.info()

    async for event in detector:
        await notifier.send_event(event)
        await indicator.pingpong_bounce()

if not getattr(boot, "SAFE_MODE", False):
    asyncio.run(main())
else:
    print("SAFE MODE active - main.py not running")