import asyncio
import os
import dotenv
from slack_sdk.web.async_client import AsyncWebClient

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_NAME = "deci-pingpong"

slack_client = AsyncWebClient(token=BOT_TOKEN)



async def _get_channel_id(channel_name):
    resp = await slack_client.conversations_list(exclude_archived=True, types="private_channel")
    for ch in resp["channels"]:
        if ch["name"] == channel_name or ch["name_normalized"] == channel_name:
            return ch["id"]
    raise ValueError(f"Channel {channel_name} not found")


async def _get_all_messages(channel_id):
    resp = await slack_client.conversations_history(channel=channel_id, limit=10)
    return resp["messages"]


async def main():
    channel_id = await _get_channel_id(SLACK_CHANNEL_NAME)
    messages = await _get_all_messages(channel_id)
    for m in messages:
        await slack_client.chat_postMessage(channel=channel_id, text=f"Look at me!!: {m['text']}")
        print ("--------------------------------")



if __name__ == "__main__":
    asyncio.run(main())
    