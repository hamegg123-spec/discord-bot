
import os
import threading
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import discord
import asyncio

# ===== Discord Bot =====
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"=== Discord Bot ログイン成功: {bot.user} ===")

# ===== FastAPI =====
app = FastAPI()

class PostData(BaseModel):
    channelId: str
    message: str

@app.post("/post")
async def post_message(data: PostData):
    channel = bot.get_channel(int(data.channelId))
    if channel:
        await channel.send(data.message)
        return {"status": "sent"}
    else:
        return {"status": "channel_not_found"}

# ===== Discord Bot を別スレッドで起動 =====
def start_discord_bot():
    token = os.environ["DISCORD_TOKEN"]
    asyncio.run(bot.start(token))

threading.Thread(target=start_discord_bot).start()

# ===== FastAPI をメインスレッドで起動 =====
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

