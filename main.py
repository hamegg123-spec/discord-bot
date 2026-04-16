# ============================================================================
# main.py (Bot 専用・Worker Service 用)
# ============================================================================

import os
import discord

print("=== Discord Bot 起動開始 ===")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"=== Discord Bot ログイン成功: {bot.user} ===")

if __name__ == "__main__":
    token = os.environ["DISCORD_TOKEN"]
    bot.run(token)
