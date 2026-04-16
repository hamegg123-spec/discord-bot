# ============================================================================
# main.py ver6 (FastAPI shutdown 原因特定 MAX 版)
# ============================================================================

import os
import asyncio
import discord
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

print("=== main.py ver6: 起動開始 ===")

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
# FastAPI（lifespan ログ強化）
# ---------------------------------------------------------------------------
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    print("=== FastAPI: startup イベント発火 ===")

@app.on_event("shutdown")
async def on_shutdown():
    print("=== FastAPI: shutdown イベント発火 ===")

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
# Discord Bot 起動（バックグラウンド）
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
# FastAPI 起動（メインタスク）
# ---------------------------------------------------------------------------
async def start_api():
    print("=== FastAPI 起動開始 ===")
    port = int(os.environ.get("PORT", 8080))

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="debug",  # ← debug に変更
        timeout_keep_alive=5
    )
    server = uvicorn.Server(config)

    print("=== FastAPI: server.serve() 開始 ===")
    await server.serve()
    print(f"=== FastAPI: server.serve() 終了 / should_exit={server.should_exit} ===")

# ---------------------------------------------------------------------------
# メイン（FastAPI をメイン、Bot をバックグラウンド）
# ---------------------------------------------------------------------------
async def main():
    print("=== main() 開始: FastAPI メイン + Bot バックグラウンド ===")

    # Bot をバックグラウンドで起動
    asyncio.create_task(start_bot())

    # FastAPI をメインタスクとして永続起動
    await start_api()

if __name__ == "__main__":
    print("=== asyncio.run(main()) 実行 ===")
    asyncio.run(main())
