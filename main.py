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
    """
    Cloudflare Workers からの城落ちイベントを受け取り、
    Discord の指定チャンネルに text をそのまま送信する。
    """
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
        log(f"[INFO] Discord 送信開始: ch={channel_id_int}, text={data.text}")
        await channel.send(data.text)
        log(f"[INFO] Discord 送信完了: ch={channel_id_int}")
        return {"status": "sent"}
    except Exception as e:
        log(f"[ERROR] Discord 送信失敗: {e}")
        return {"status": "error", "detail": str(e)}

# ===== FastAPI サーバー起動（別スレッド） =====
def start_fastapi():
    port = int(os.getenv("PORT", "8000"))
    log(f"FastAPI 起動: 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

# ===== エントリポイント =====
if __name__ == "__main__":
    # FastAPI を別スレッドで起動
    api_thread = threading.Thread(target=start_fastapi, daemon=True)
    api_thread.start()

    # Discord Bot をメインスレッドで起動
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        log("[FATAL] DISCORD_BOT_TOKEN が環境変数に設定されていません")
    else:
        log("Discord Bot 接続開始")
        bot.run(token)
