# ============================================================================
# main.py (Bot + FastAPI + イベントループ修正版 + ログ強化)
# ============================================================================

import os
import threading
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import discord
import asyncio
import datetime

# ===== ログ関数 =====
def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

# ===== Discord Bot =====
log("=== Discord Bot 起動開始 ===")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    log(f"Discord Bot ログイン成功: {bot.user}")
    log("Guild一覧: " + ", ".join([g.name for g in bot.guilds]))

# ===== FastAPI =====
app = FastAPI()

class PostData(BaseModel):
    channelId: str
    message: str
