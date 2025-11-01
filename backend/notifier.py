import asyncio
from datetime import datetime

import slack_sdk.web.async_client


class SlackNotifier:
    def __init__(self, cfg):
        self.cfg = cfg
        self.channel_name = cfg["channel"]
        self.client = slack_sdk.web.async_client.AsyncWebClient(token=cfg["token"])
        self.assets_url = cfg["assets_url"].rstrip("/")

    def _asset_url(self, asset_filename):
        return f"{self.assets_url}/{asset_filename}"

    async def init(self):
        self.channel_id = await self._get_channel_id(self.channel_name)
        auth_resp = await self.client.auth_test()
        self.bot_id = auth_resp["bot_id"]
        

    async def _get_channel_id(self, channel_name):
        resp = await self.client.conversations_list(exclude_archived=True, types="private_channel")
        for ch in resp["channels"]:
            if ch["name"] == channel_name or ch["name_normalized"] == channel_name:
                return ch["id"]
        raise ValueError(f"Channel {channel_name} not found")


    async def _get_historical_messages(self, limit=10):
        resp = await self.client.conversations_history(channel=self.channel_id, limit=limit)
        return resp["messages"]

    async def notify(self, room_state):
        blocks = [ 
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Looks like we have some news regarding the pingpong room:"
                }
            },
            {
                 "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"The room is now {room_state.state}! Since <!date^{room_state.last_state_change_time:.0f}^{{time}}| >",
                },
                "accessory": {
                    "type": "image",
                    "image_url": self._asset_url(f"pingpong-icon-{room_state.state}.png"),
                    "alt_text": "pingpong icon"
                }
            },
        ]

        await self.post_or_update(blocks)

    async def post_or_update(self, blocks):
        last_messages = await self._get_historical_messages(1)
        should_update = "bot_id" in last_messages[0] and last_messages[0]["bot_id"] == self.bot_id

        if should_update:
            await self.client.chat_update(channel=self.channel_id, ts=last_messages[0]["ts"], blocks=blocks)
        else:
            await self.client.chat_postMessage(channel=self.channel_id, blocks=blocks)
