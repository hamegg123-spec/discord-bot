# ============================================================================
# main.py ver7 (Railway 最終安定版・貼り替えOK)
# ============================================================================

import os
import threading
import discord
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

print("=== main.py ver7: 起動開始 ===")

# ---------------------------------------------------------------------------
# Discord Bot
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"=== Discord Bot ログイン成功: {bot.user} ===")

def run_bot():
    print("=== Discord Bot スレッド起動開始 ===")
    token = os.environ["DISCORD_TOKEN"]
    bot.run(token)  # ← 永続ブロック（スレッド内なので問題なし）

# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
app = FastAPI()

class EventPayload(BaseModel):
    channelId: str
    message: str

@app.post("/post")
async def post_event(payload: EventPayload):
    print(f"=== /post 受信: {payload} ===")

    channel = bot.get_channel(int(payload.channelId))
    if channel is None:
        print("=== エラー: チャンネルが見つかりません ===")
        return {"ok": False, "error": "Channel not found"}

    try:
        await channel.send(payload.message)
        print("=== Discord 投稿成功 ===")
        return {"ok": True}
    except Exception as e:
        print(f"=== Discord 投稿失敗: {e} ===")
        return {"ok": False, "error": str(e)}

# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== main.py ver7: メイン開始 ===")

    # Discord Bot を別スレッドで永続起動
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # FastAPI をフォアグラウンドで起動（Railway が必要とするプロセス）
    port = int(os.environ.get("PORT", 8080))
    print(f"=== FastAPI 起動: ポート {port} ===")

    uvicorn.run(app, host="0.0.0.0", port=port)
