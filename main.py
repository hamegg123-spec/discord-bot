# ============================================================================
# main.py (FastAPI + Discord Bot 同一イベントループ版)
# ============================================================================

import os
import asyncio
import discord
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Discord Bot 設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

# FastAPI
app = FastAPI()

# POST で受け取る JSON
class EventPayload(BaseModel):
    channelId: str
    message: str

# Discord 投稿 API
@app.post("/post")
async def post_event(payload: EventPayload):
    channel = bot.get_channel(int(payload.channelId))
    if channel is None:
        return {"ok": False, "error": "Channel not found"}

    await channel.send(payload.message)
    return {"ok": True}

# Bot 起動（FastAPI と同じイベントループで動かす）
async def start_bot():
    await bot.start(os.environ["DISCORD_TOKEN"])

# メイン（FastAPI + Bot を同時起動）
def main():
    loop = asyncio.get_event_loop()

    # Discord Bot をバックグラウンドで起動
    loop.create_task(start_bot())

    # FastAPI を同じイベントループで起動
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
