# ============================================================================
# main.py ver26.6
#   - Discord 投稿順序安定化（1秒ディレイ + キュー方式）
# ----------------------------------------------------------------------------
# 【変更履歴】
# [2026-05-02] senoo / Copilot
# - Discord のメッセージ順序が前後する問題を解決するため、
#   Railway 側で「投稿キュー + 1秒ディレイ」方式を導入。
# - /postCastleEvent で受信したメッセージを即時送信せず、
#   非同期キューに積み、専用タスクが 1 件ずつ 1 秒間隔で送信。
# - FastAPI / Discord Bot の構造は変更せず、最小修正で安定化。
#
# ----------------------------------------------------------------------------
# 【変更内容】
# - asyncio.Queue() を導入し、Discord 投稿を逐次処理に変更。
# - send_worker() タスクが queue から 1 件ずつ取り出し、
#   Discord に送信 → 1 秒 sleep → 次のメッセージ、という流れに変更。
# - /postCastleEvent は「キューに積むだけ」に変更。
# - ログを強化し、キュー投入・送信開始・送信完了を明確化。
#
# ----------------------------------------------------------------------------
# 【変更理由】
# - Discord API は同一秒に複数メッセージが届くと timestamp が前後し、
#   表示順が崩れる仕様があるため。
# - Railway 側で 1 秒ディレイを入れることで timestamp が毎回別秒になり、
#   Discord の表示順が完全に安定する。
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

# ★ Discord 投稿キュー（1秒ディレイ用）
send_queue = asyncio.Queue()

@bot.event
async def on_ready():
    log(f"Discord Bot ログイン成功: {bot.user}")
    log("Guild一覧: " + ", ".join([g.name for g in bot.guilds]))

    # ★ 投稿ワーカー開始
    bot.loop.create_task(send_worker())
    log("Discord 投稿ワーカー開始")

# ============================================================================
# ★ Discord 投稿ワーカー（1件ずつ 1秒間隔で送信）
# ============================================================================
async def send_worker():
    while True:
        channel, text = await send_queue.get()
        try:
            log(f"[SEND_WORKER] 送信開始 → {channel.id}")
            await channel.send(text)
            log(f"[SEND_WORKER] 送信完了 → {channel.id}")
        except Exception as e:
            log(f"[SEND_WORKER] 送信エラー: {e}")
        finally:
            # ★ 次のメッセージまで 1 秒待つ（順序安定化の核心）
            await asyncio.sleep(1)
            send_queue.task_done()

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

    # ★ キューに積むだけ
    await send_queue.put((channel, data.message))
    log(f"[QUEUE] 投稿キューに追加（旧API） → {data.channelId}")

    return {"status": "queued"}

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

    # ★ キューに積むだけ（即時送信しない）
    await send_queue.put((channel, data.text))
    log(f"[QUEUE] 投稿キューに追加（城落ち） → {data.channelId}")

    return {"status": "queued"}

# ===== Discord Bot を別スレッドで起動 =====
def start_discord_bot():
    token = os.environ["DISCORD_TOKEN"]
    log("Discord Bot スレッド開始")
    asyncio.run(bot.start(token))

threading.Thread(target=start_discord_bot).start()

# ===== FastAPI をメインスレッドで起動 =====
if __name__ == "__main__":
    log("FastAPI 起動開始 (0.0.0.0:8080)")
    uvicorn.run(app, host="0.0.0.0", port=8080)
