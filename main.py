import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import discord

# Discord Bot クライアント
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

# FastAPI（Cloudflare Workers → Bot の受け口）
app = FastAPI()

class EventPayload(BaseModel):
    channelId: str
    message: str

@app.post("/post")
async def post_event(payload: EventPayload):
    try:
        channel = bot.get_channel(int(payload.channelId))
        if channel is None:
            return {"ok": False, "error": "Channel not found"}

        await channel.send(payload.message)
        return {"ok": True}

    except Exception as e:
        return {"ok": False, "error": str(e)}

# Bot 起動
async def start_bot():
    await bot.start(os.environ["DISCORD_TOKEN"])

# Railway 起動ポイント
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))