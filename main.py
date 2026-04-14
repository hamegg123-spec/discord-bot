import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import discord

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)
app = FastAPI()

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

async def start_all():
    bot_task = asyncio.create_task(bot.start(os.environ["DISCORD_TOKEN"]))
    uvicorn_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
        ).serve()
    )
    await asyncio.gather(bot_task, uvicorn_task)

if __name__ == "__main__":
    asyncio.run(start_all())
