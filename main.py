# ============================================================================
# main.py (Discord Bot + FastAPI + Workers ver25.0 対応版)
# - Workers からの JSON: { "channelId": "...", "text": "..." } を受け取り、
#   指定チャンネルにそのまま送信する。
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
def log(msg: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

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

# ★ Workers ver25.0 に合わせてフィールド名を text に変更
class PostData(BaseModel):
    channelId: str
    text: str

# ★ Workers 側の env.RAILWAY_URL のパスに合わせる
#   例: env.RAILWAY_URL = "https://xxx.railway.app/postCastleEvent"
@app.post("/postCastleEvent")
async def post_castle_event(data: PostData):
    try:
        channel_id_int = int(data.channelId)
    except ValueError:
        log(f"[ERROR] channelId が数値に変換できない: {data.channelId}")
        return {"status": "invalid_channelId"}

    channel = bot.get_channel(channel_id_int)
    if channel is None:
        log(f"[ERROR] チャンネルが見つからない: {channel_id_int}")
        return {"status": "channel_not_found"}

    try:
        log(f"[INFO] Discord 送信開始（スレッドセーフ）: ch={channel_id_int}, text={data.text}")

        # ★ Discord Bot のイベントループにタスクを投げる
        future = asyncio.run_coroutine_threadsafe(
            channel.send(data.text),
            bot.loop
        )

        # ★ Discord 側の送信完了を待つ（例外も拾える）
        future.result()

        log(f"[INFO] Discord 送信完了: ch={channel_id_int}")
        return {"status": "sent"}

    except Exception as e:
        log(f"[ERROR] Discord 送信失敗: {e}")
        return {"status": "error", "detail": str(e)}
