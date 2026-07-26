import os
import json
import asyncio
import threading
from datetime import datetime, timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, jsonify

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Blackhole Bot is running 24/7!"

@app.route('/status')
def status():
    return jsonify({"status": "online", "timestamp": datetime.now(timezone.utc).isoformat()})

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- BOT CONFIGURATION ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
EVENT_MINUTE = int(os.environ.get("EVENT_MINUTE", 0))
CHANNELS_FILE = "channels.json"

# --- EVENT IMAGES ---
IMAGES = {
    "30m": "https://media.discordapp.net/attachments/1476195716648009929/1530564249238241353/Untitled-1.png?ex=6a660889&is=6a64b709&hm=d8e38f9837fe631ad9afdc0d22ceaa1f4bef9142920d7c7c8df52bd0a3d995be&=&format=webp&quality=lossless",
    "10m": "https://media.discordapp.net/attachments/1476195716648009929/1530564247774298153/10_minutes.png?ex=6a660889&is=6a64b709&hm=8a2ade4a92786edcdaed126c442a9fc076e0b5dd8b8ec3d7e50bfcd1824e10a8&=&format=webp&quality=lossless",
    "5m": "https://media.discordapp.net/attachments/1476195716648009929/1530564247212523560/5_minutes.png?ex=6a660889&is=6a64b709&hm=aaf802ac565670fbea0ea1d9798502fb8be83e024758432e8050d81aa48eff56&=&format=webp&quality=lossless",
    "1m": "https://cdn.discordapp.com/attachments/1476195716648009929/1530727365460758638/Untitled-1.png?ex=6a66a073&is=6a654ef3&hm=dd29a2de90f861ce37e6726e973fca5a295a7dd469e2fde13a39bacb9e4d3152&",
    "started": "https://media.discordapp.net/attachments/1476195716648009929/1530564248428613663/Started.png?ex=6a660889&is=6a64b709&hm=638760c3e696b18c13c36ed60aad97386b613f5d6a5c9158f112cbd52bf17406&=&format=webp&quality=lossless",
}

# --- COLOR THEMES ---
COLORS = {
    "30m": 0x3498DB,
    "10m": 0xF1C40F,
    "5m": 0xE67E22,
    "1m": 0xE74C3C,
    "countdown": 0x9B59B6,
    "started": 0x2ECC71
}

# --- DISCORD CLIENT INITIALIZATION ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- STORAGE HELPERS ---
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_channels(data):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- SLASH COMMANDS ---
@bot.tree.command(name="setchannel", description="Set the channel where Blackhole Event alerts will be sent.")
@app_commands.checks.has_permissions(administrator=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target_channel = channel or interaction.channel
    channels = load_channels()
    channels[str(interaction.guild_id)] = target_channel.id
    save_channels(channels)
    
    await interaction.response.send_message(
        f"✅ Blackhole notifications channel successfully set to {target_channel.mention}!",
        ephemeral=True
    )

@setchannel.error
async def setchannel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You need Administrator permissions to use this command.", ephemeral=True)

# --- BROADCAST HELPER ---
async def broadcast_embed(title, description, color, image_url=None):
    channels = load_channels()
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Blackhole Event System • Auto Notifier", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    if image_url:
        embed.set_image(url=image_url)

    sent_messages = []
    for guild_id, channel_id in channels.items():
        try:
            ch = bot.get_channel(int(channel_id))
            if ch:
                msg = await ch.send(embed=embed)
                sent_messages.append((ch, msg))
        except Exception as e:
            print(f"Failed to send alert to channel {channel_id}: {e}")
            
    return sent_messages

# --- CALCULATION HELPER ---
def get_next_event_time():
    now = datetime.now(timezone.utc)
    next_event = now.replace(minute=EVENT_MINUTE, second=0, microsecond=0)
    if next_event <= now:
        next_event += timedelta(hours=1)
    return next_event

# --- BACKGROUND NOTIFICATION LOOP ---
async def bot_loop():
    await bot.wait_until_ready()
    print("🌌 Background Alert Loop Active.")

    while not bot.is_closed():
        next_event = get_next_event_time()
        event_ts = int(next_event.timestamp())

        # --- 30 MINUTES ALERT ---
        now = datetime.now(timezone.utc)
        sleep_30m = (next_event - timedelta(minutes=30) - now).total_seconds()
        if sleep_30m > 0:
            await asyncio.sleep(sleep_30m)
            await broadcast_embed(
                title="⏳ Blackhole Event Alert",
                description=f"The **Blackhole Event** will begin in **30 minutes**!\n\n**Start Time:** <t:{event_ts}:F>\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["30m"],
                image_url=IMAGES["30m"]
            )

        # --- 10 MINUTES ALERT ---
        now = datetime.now(timezone.utc)
        sleep_10m = (next_event - timedelta(minutes=10) - now).total_seconds()
        if sleep_10m > 0:
            await asyncio.sleep(sleep_10m)
            await broadcast_embed(
                title="⏰ Blackhole Event Approaching",
                description=f"Prepare yourselves! Only **10 minutes** remaining!\n\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["10m"],
                image_url=IMAGES["10m"]
            )

        # --- 5 MINUTES ALERT ---
        now = datetime.now(timezone.utc)
        sleep_5m = (next_event - timedelta(minutes=5) - now).total_seconds()
        if sleep_5m > 0:
            await asyncio.sleep(sleep_5m)
            await broadcast_embed(
                title="🌌 Blackhole Event Impending",
                description=f"Final preparations! **5 minutes** left until spawn!\n\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["5m"],
                image_url=IMAGES["5m"]
            )

        # --- 1 MINUTE ALERT ---
        now = datetime.now(timezone.utc)
        sleep_1m = (next_event - timedelta(minutes=1) - now).total_seconds()
        if sleep_1m > 0:
            await asyncio.sleep(sleep_1m)
            await broadcast_embed(
                title="⚠️ Blackhole Event Imminent",
                description=f"Get into position! **1 minute** remaining!\n\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["1m"],
                image_url=IMAGES["1m"]
            )

        # --- LIVE 3... 2... 1... COUNTDOWN ---
        now = datetime.now(timezone.utc)
        sleep_3s = (next_event - timedelta(seconds=3) - now).total_seconds()
        if sleep_3s > 0:
            await asyncio.sleep(sleep_3s)
            
            sent_msgs = await broadcast_embed(
                title="🚨 LIVE COUNTDOWN",
                description="# 3️⃣ ...",
                color=COLORS["countdown"]
            )
            
            await asyncio.sleep(1)
            for ch, msg in sent_msgs:
                try:
                    embed = discord.Embed(title="🚨 LIVE COUNTDOWN", description="# 2️⃣ ..", color=COLORS["countdown"])
                    await msg.edit(embed=embed)
                except Exception:
                    pass

            await asyncio.sleep(1)
            for ch, msg in sent_msgs:
                try:
                    embed = discord.Embed(title="🚨 LIVE COUNTDOWN", description="# 1️⃣ .", color=COLORS["countdown"])
                    await msg.edit(embed=embed)
                except Exception:
                    pass

        # --- EVENT STARTED ALERT ---
        now = datetime.now(timezone.utc)
        sleep_start = (next_event - now).total_seconds()
        if sleep_start > 0:
            await asyncio.sleep(sleep_start)

        await broadcast_embed(
            title="🚨 BLACKHOLE EVENT HAS STARTED! 🚨",
            description="The Blackhole is now **ACTIVE**! Jump into the game immediately!",
            color=COLORS["started"],
            image_url=IMAGES["started"]
        )

        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    bot.loop.create_task(bot_loop())

if __name__ == "__main__":
    # Start webserver thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Run Discord Bot
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your DISCORD_TOKEN environment variable!")
    else:
        bot.run(DISCORD_TOKEN)