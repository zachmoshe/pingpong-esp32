import uasyncio as asyncio
import urequests


class BackendNotifier:

    def __init__(self, cfg, indicator):
        self.server_url = cfg["http"]["server_url"]
        if self.server_url.endswith("/"):
            self.server_url = self.server_url[:-1]

        self.event_endpoint = f"{self.server_url}/pingpong-event"
        self.ping_endpoint = f"{self.server_url}/ping"

        self.indicator = indicator
        asyncio.create_task(self._test_endpoint())


    async def _test_endpoint(self):
        try:
            print(f"Sending request to {self.ping_endpoint}")
            response = urequests.get(self.ping_endpoint, timeout=1)
            print("got resp ", response)
            if response.status_code != 200:
                raise Exception(f"Error testing endpoint: Got status code {response.status_code}")
            print("before closing")
            response.close()
            print("after closing")
            await self.indicator.info()
            print("after indicating")

        except Exception as e:
            print(f"Error testing endpoint: {e}")
            await self.indicator.error()


    async def send_event(self, event):
        try:
            data = {"event": event}
            response = urequests.post(self.event_endpoint, json=data, timeout=1)
            print(f"Sent event to backend: {data}")
            print(f"Response: [{response.status_code}] {response.text}")
            await self.indicator.info()

        except Exception as e:
            await self.indicator.error()
            print(f"Error sending event to backend: {e}")