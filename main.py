# ============================================================================
# main.py ver2 (FastAPI + Discord Bot 同一イベントループ・ログ強化版)
# ============================================================================
# 【目的】
# - Bot が起動していない原因を Railway ログで完全に可視化する
# - FastAPI と Discord Bot を同一イベントループで安定起動
# - 起動ログ・例外ログを強化し、問題箇所を特定しやすくする
# ============================================================================

import os
import asyncio
import discord
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

print("=== main.py ver2: 起動開始 ===")

# ---------------------------------------------------------------------------
# Discord Bot 設定
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"=== Discord Bot ログイン成功: {bot.user} ===")

@bot.event
async def on_connect():
    print("=== Discord Bot: Discord API に接続中 ===")

@bot.event
async def on_disconnect():
    print("=== Discord Bot: 切断されました ===")

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
# Discord Bot 起動
# ---------------------------------------------------------------------------
async def start_bot():
    print("=== Discord Bot 起動開始 ===")
    token = os.environ.get("DISCORD_TOKEN")

    if not token:
        print("=== 致命的エラー: DISCORD_TOKEN が設定されていません ===")
        return

    try:
        await bot.start(token)
    except Exception as e:
        print(f"=== Bot 起動エラー: {e} ===")

# ---------------------------------------------------------------------------
# FastAPI 起動
# ---------------------------------------------------------------------------
async def start_api():
    print("=== FastAPI 起動開始 ===")
    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# ---------------------------------------------------------------------------
# メイン（Bot + FastAPI を同時起動）
# ---------------------------------------------------------------------------
async def main():
    print("=== main() 開始: Bot + FastAPI 同時起動 ===")
    await asyncio.gather(
        start_bot(),
        start_api()
    )

if __name__ == "__main__":
    print("=== asyncio.run(main()) 実行 ===")
    asyncio.run(main())
