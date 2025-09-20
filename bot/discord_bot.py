import os
import sqlite3
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0") or "0")
DEVELOPER_ROLE_ID = int(os.getenv("DISCORD_DEVELOPER_ROLE_ID", "0") or "0")
DB_PATH = os.getenv("SQLITE_PATH") or "./devices.db"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def db_conn():
    return sqlite3.connect(DB_PATH)

def ensure_purchase(discord_id: str, discord_name: str):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT discord_id FROM purchases WHERE discord_id=?", (discord_id,))
        if not cur.fetchone():
            cur.execute(
                """INSERT INTO purchases(discord_id, discord_name, purchase_date, expires_date, slots_allowed, slots_used)
                   VALUES (?, ?, ?, ?, 1, 0)""",
                (discord_id, discord_name, datetime.now(), datetime.now() + timedelta(days=365)),
            )
            conn.commit()

@bot.event
async def on_ready():
    print(f"{bot.user} connected.")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    got_role_now = any(r.id == DEVELOPER_ROLE_ID for r in after.roles) and                    not any(r.id == DEVELOPER_ROLE_ID for r in before.roles)

    if got_role_now:
        discord_id = str(after.id)
        discord_name = f"{after.name}#{after.discriminator}"
        ensure_purchase(discord_id, discord_name)

        try:
            await after.send(
                "🎉 Thanks for your purchase!\n\n"
                f"**Step 1**: Open on your iOS device and log in:\n{BASE_URL}/register\n\n"
                "Follow the prompts to install a configuration profile to capture your UDID automatically."
            )
        except discord.Forbidden:
            pass

@bot.command()
async def status(ctx: commands.Context):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT udid, product, apple_registered, registered_date
                       FROM devices WHERE discord_id=? ORDER BY registered_date DESC""", (str(ctx.author.id),))
        rows = cur.fetchall()

    if not rows:
        await ctx.send("No devices registered yet. Use the link I DM'd you or visit /register.")
        return

    embed = discord.Embed(title="Your Devices", color=discord.Color.blue())
    for udid, product, registered, created in rows:
        status = "✅ Active" if registered else "⏳ Processing"
        embed.add_field(
            name=product or "Device",
            value=f"UDID: `{udid[:8]}...` • {status}\nAdded: {created}",
            inline=False
        )
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Missing DISCORD_BOT_TOKEN")
    bot.run(TOKEN)
