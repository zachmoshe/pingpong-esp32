import uasyncio as asyncio
import urequests
import requests


class BackendNotifier:

    def __init__(self, cfg, indicator):
        self.server_url = cfg["server_url"]
        if self.server_url.endswith("/"):
            self.server_url = self.server_url[:-1]

        self.event_endpoint = f"{self.server_url}{cfg["pingpong_event_endpoint"]}"
        self.ping_endpoint = f"{self.server_url}{cfg["ping_endpoint"]}"

        self.indicator = indicator

        self._test_endpoint()


    def _test_endpoint(self):
        try:
            response = requests.get(self.ping_endpoint, timeout=1)
            if response.status_code != 200:
                raise Exception(f"Error testing endpoint: Got status code {response.status_code}: {response.text}")

        except Exception as e:
            print(f"Error testing endpoint: {e}")
            raise RuntimeError("Failed to reach backend endpoints") from e


    async def send_event(self, event):
        try:
            data = event.to_dict()
            response = urequests.post(self.event_endpoint, json=data, timeout=1)
            if response.status_code != 200:
                raise Exception(f"Error sending event to backend: Got status code {response.status_code}: {response.text}")

        except Exception as e:
            await self.indicator.error()
            print(f"Error sending event to backend: {e}")