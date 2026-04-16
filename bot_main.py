import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
import discord
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
app = FastAPI()

class PostData(BaseModel):
    channelId: str
    message: str

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@app.post("/send")
async def send_message(data: PostData):
    channel = bot.get_channel(int(data.channelId))
    if channel is None:
        # キャッシュになければ fetch
        channel = await bot.fetch_channel(int(data.channelId))
    await channel.send(data.message)
    return {"status": "ok"}

# Discord Bot をバックグラウンドで動かす
def start_bot():
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(DISCORD_TOKEN))

start_bot()
