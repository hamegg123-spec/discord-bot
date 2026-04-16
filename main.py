# ============================================================================
# main.py (Bot + FastAPI + イベントループ修正版 + ログ強化 + ver25.0対応)
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

# 旧API（Android → Railway 直接投稿用）
class PostData(BaseModel):
    channelId: str
    message: str

@app.post("/post")
async def post_message(data: PostData):
    log(f"/post 受信: channelId={data.channelId}, message={data.message}")

    channel = bot.get_channel(int(data.channelId))

    if channel is None:
        log(f"エラー: チャンネル {data.channelId} が見つからない")
        return {"status": "channel_not_found"}

    try:
        bot.loop.create_task(channel.send(data.message))
        log(f"Discord 投稿タスク作成 → {data.channelId}")
        return {"status": "sent"}
    except Exception as e:
        log(f"Discord 投稿エラー: {e}")
        return {"status": "error", "detail": str(e)}

# ===== 新API（Workers ver25.0 → Railway Bot 用） =====
class CastleEvent(BaseModel):
    channelId: str
    text: str   # ★ Workers ver25.0 のフィールド名に合わせる

@app.post("/postCastleEvent")
async def post_castle_event(data: CastleEvent):
    log(f"/postCastleEvent 受信: channelId={data.channelId}, text={data.text}")

    channel = bot.get_channel(int(data.channelId))

    if channel is None:
        log(f"エラー: チャンネル {data.channelId} が見つからない")
        return {"status": "channel_not_found"}

    try:
        # ★ Discord Bot のイベントループにタスクを投げる（安定版）
        bot.loop.create_task(channel.send(data.text))
        log(f"Discord 投稿タスク作成（城落ち） → {data.channelId}")
        return {"status": "sent"}
    except Exception as e:
        log(f"Discord 投稿エラー（城落ち）: {e}")
        return {"status": "error", "detail": str(e)}

# ===== Discord Bot を別スレッドで起動 =====
def start_discord_bot():
    token = os.environ["DISCORD_TOKEN"]  # ★ あなたの安定版は DISCORD_TOKEN
    log("Discord Bot スレッド開始")
    asyncio.run(bot.start(token))

threading.Thread(target=start_discord_bot).start()

# ===== FastAPI をメインスレッドで起動 =====
if __name__ == "__main__":
    log("FastAPI 起動開始 (0.0.0.0:8080)")
    uvicorn.run(app, host="0.0.0.0", port=8080)
