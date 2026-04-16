# ============================================================================
# main.py (FastAPI + Discord Bot 同一イベントループ・完全版)
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

@app.post("/post")
async def post_event(payload: EventPayload):
    channel = bot.get_channel(int(payload.channelId))
    if channel is None:
        return {"ok": False, "error": "Channel not found"}

    await channel.send(payload.message)
    return {"ok": True}

# Discord Bot 起動
async def start_bot():
    await bot.start(os.environ["DISCORD_TOKEN"])

# FastAPI 起動（uvicorn.Server を await する）
async def start_api():
    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# メイン（Bot + FastAPI を同一イベントループで同時起動）
async def main():
    # Bot と FastAPI を同時に起動
    await asyncio.gather(
        start_bot(),
        start_api()
    )

if __name__ == "__main__":
    asyncio.run(main())
