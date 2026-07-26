import os
import json
import asyncio
import threading
from datetime import datetime, timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Nuclear Blackhole Monitoring System is active 24/7!"

@app.route('/status')
def status():
    return jsonify({"status": "online", "system": "radiation_monitors", "timestamp": datetime.now(timezone.utc).isoformat()})

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
EVENT_MINUTE = int(os.environ.get("EVENT_MINUTE", 0))

CHANNELS_FILE = "channels.json"
ROLES_FILE = "roles.json"

ALLOWED_GUILDS = [1459542443509944373, 1462506305427083406, 1530735325213757470]

DEFAULT_CHANNELS = {
    "1462506305427083406": 1530810264642130041
}

DEFAULT_ROLES = {
    "1462506305427083406": 1530810691877863525
}

IMAGES = {
    "30m": "https://media.discordapp.net/attachments/1476195716648009929/1530564249238241353/Untitled-1.png?ex=6a660889&is=6a64b709&hm=d8e38f9837fe631ad9afdc0d22ceaa1f4bef9142920d7c7c8df52bd0a3d995be&=&format=webp&quality=lossless",
    "10m": "https://media.discordapp.net/attachments/1476195716648009929/1530564247774298153/10_minutes.png?ex=6a660889&is=6a64b709&hm=8a2ade4a92786edcdaed126c442a9fc076e0b5dd8b8ec3d7e50bfcd1824e10a8&=&format=webp&quality=lossless",
    "5m": "https://media.discordapp.net/attachments/1476195716648009929/1530564247212523560/5_minutes.png?ex=6a660889&is=6a64b709&hm=aaf802ac565670fbea0ea1d9798502fb8be83e024758432e8050d81aa48eff56&=&format=webp&quality=lossless",
    "1m": "https://cdn.discordapp.com/attachments/1476195716648009929/1530727365460758638/Untitled-1.png?ex=6a66a073&is=6a654ef3&hm=dd29a2de90f861ce37e6726e973fca5a295a7dd469e2fde13a39bacb9e4d3152&",
    "started": "https://media.discordapp.net/attachments/1476195716648009929/1530564248428613663/Started.png?ex=6a660889&is=6a64b709&hm=638760c3e696b18c13c36ed60aad97386b613f5d6a5c9158f112cbd52bf17406&=&format=webp&quality=lossless",
}

COLORS = {
    "30m": 0xF1C40F,        # Radiation Caution Yellow
    "10m": 0xE67E22,        # Biohazard Orange
    "5m": 0xFF3300,         # Critical Thermal Red-Orange
    "1m": 0x990000,         # Dark Emergency Red
    "countdown": 0x8E44AD,  # Toxic Singularity Purple
    "started": 0x00FF66     # Radioactive Meltdown Neon Green
}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def load_channels():
    data = DEFAULT_CHANNELS.copy()
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r") as f:
                file_data = json.load(f)
                data.update(file_data)
        except Exception:
            pass
    return data

def save_channels(data):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_roles():
    data = DEFAULT_ROLES.copy()
    if os.path.exists(ROLES_FILE):
        try:
            with open(ROLES_FILE, "r") as f:
                file_data = json.load(f)
                data.update(file_data)
        except Exception:
            pass
    return data

def save_roles(data):
    with open(ROLES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_allowed_guild():
    def predicate(interaction: discord.Interaction):
        if interaction.guild_id not in ALLOWED_GUILDS:
            raise app_commands.CheckFailure("Unauthorized Server")
        return True
    return app_commands.check(predicate)

@bot.tree.command(name="setchannel", description="Set the bunker alert channel for Nuclear Blackhole notifications.")
@app_commands.checks.has_permissions(administrator=True)
@is_allowed_guild()
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target_channel = channel or interaction.channel
    channels = load_channels()
    channels[str(interaction.guild_id)] = target_channel.id
    save_channels(channels)
    
    await interaction.response.send_message(
        f"☣️ **NUCLEAR BROADCAST SET:** Alert channel established at {target_channel.mention}!",
        ephemeral=True
    )

@bot.tree.command(name="setroleping", description="Set the Hazmat/Survival team role to ping for nuclear alerts.")
@app_commands.checks.has_permissions(administrator=True)
@is_allowed_guild()
async def setroleping(interaction: discord.Interaction, role: discord.Role):
    roles = load_roles()
    roles[str(interaction.guild_id)] = role.id
    save_roles(roles)
    
    await interaction.response.send_message(
        f"☢️ **HAZMAT PROTOCOL UPDATED:** Emergency ping role assigned to {role.mention}!",
        ephemeral=True
    )

@bot.tree.command(name="countdownevent", description="Monitor the radiation telemetry and countdown to the next Nuclear Blackhole.")
@is_allowed_guild()
async def countdownevent(interaction: discord.Interaction):
    next_event = get_next_event_time()
    event_ts = int(next_event.timestamp())

    def get_countdown_embed():
        now = datetime.now(timezone.utc)
        diff = max(0, int((next_event - now).total_seconds()))
        hours, remainder = divmod(diff, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            formatted_time = f"{hours}h {minutes:02d}m {seconds:02d}s"
        else:
            formatted_time = f"{minutes:02d}m {seconds:02d}s"

        embed = discord.Embed(
            title="☢️ RAD-MONITOR: Nuclear Blackhole Telemetry",
            description=(
                f"**Detonation Time:** <t:{event_ts}:F>\n"
                f"**Live Time to Meltdown:** `{formatted_time}`\n"
                f"**Relative Time:** <t:{event_ts}:R>"
            ),
            color=COLORS["countdown"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Nuclear Hazard System • Radiation Monitoring Active", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        return embed

    await interaction.response.send_message(embed=get_countdown_embed())

    try:
        msg = await interaction.original_response()
        for _ in range(30):
            await asyncio.sleep(2)
            await msg.edit(embed=get_countdown_embed())
    except Exception:
        pass

@bot.tree.command(name="testmessage", description="Simulate a Nuclear Blackhole warning alert siren.")
@app_commands.checks.has_permissions(administrator=True)
@is_allowed_guild()
@app_commands.choices(option=[
    app_commands.Choice(name="30m - Radiation Spike", value="30m"),
    app_commands.Choice(name="10m - Hazard Warning", value="10m"),
    app_commands.Choice(name="5m - Core Instability", value="5m"),
    app_commands.Choice(name="1m - Evacuation Siren", value="1m"),
    app_commands.Choice(name="start - Nuclear Singularity Active", value="started")
])
async def testmessage(interaction: discord.Interaction, option: app_commands.Choice[str]):
    opt = option.value
    next_event = get_next_event_time()
    event_ts = int(next_event.timestamp())

    if opt == "30m":
        await broadcast_embed(
            title="☢️ RAD-ALERT: Blackhole Criticality Spike Detected",
            description=f"Sensors report high radioactive charge! The **Nuclear Blackhole Event** will form in **30 minutes**!\n\n**Detonation Time:** <t:{event_ts}:F>\n**Countdown:** <t:{event_ts}:R>",
            color=COLORS["30m"],
            image_url=IMAGES["30m"],
            ping=False
        )
    elif opt == "10m":
        await broadcast_embed(
            title="⚠️ HAZARD WARNING: Radiation Levels Escalating",
            description=f"Core instability rising! Severe fallout expected! Only **10 minutes** until singularity breach!\n\n**Countdown:** <t:{event_ts}:R>",
            color=COLORS["10m"],
            image_url=IMAGES["10m"],
            ping=False
        )
    elif opt == "5m":
        await broadcast_embed(
            title="☣️ CRITICAL WARNING: Core Breach Imminent",
            description=f"Equip hazmat gear and prep for deployment! **5 minutes** left before total nuclear meltdown!\n\n**Countdown:** <t:{event_ts}:R>",
            color=COLORS["5m"],
            image_url=IMAGES["5m"],
            ping=True
        )
    elif opt == "1m":
        await broadcast_embed(
            title="🚨 SIREN PROTOCOL: CODE RED SINGULARITY",
            description=f"ALL UNITS DOCK NOW! **1 minute** until the Nuclear Blackhole erupts!\n\n**Countdown:** <t:{event_ts}:R>",
            color=COLORS["1m"],
            image_url=IMAGES["1m"],
            ping=True
        )
    elif opt == "started":
        await broadcast_embed(
            title="💥 NUCLEAR BLACKHOLE DETONATION ACTIVE! 💥",
            description="**TOTAL MELTDOWN IN PROGRESS!** The Radioactive Blackhole has erupted! CONTAIN THE SINGULARITY IMMEDIATELY!",
            color=COLORS["started"],
            image_url=IMAGES["started"],
            ping=True
        )

    await interaction.response.send_message(f"✅ Nuclear alert test executed for stage: `{option.name}`", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if "Unauthorized Server" in str(error):
            await interaction.response.send_message("❌ Unauthorized sector. Access denied.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ You require High Command (Administrator) authorization for this protocol.", ephemeral=True)

async def broadcast_embed(title, description, color, image_url=None, ping=True):
    channels = load_channels()
    roles = load_roles()
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Nuclear Hazard System • Automated Siren Protocol", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    if image_url:
        embed.set_image(url=image_url)

    sent_messages = []
    for guild_id_str, channel_id in channels.items():
        if int(guild_id_str) not in ALLOWED_GUILDS:
            continue
            
        try:
            ch = bot.get_channel(int(channel_id))
            if ch is None:
                ch = await bot.fetch_channel(int(channel_id))
                
            if ch:
                content = ""
                if ping:
                    role_id = roles.get(guild_id_str)
                    if role_id:
                        content = f"<@&{role_id}>"

                msg = await ch.send(content=content, embed=embed)
                sent_messages.append((ch, msg))
        except discord.Forbidden:
            print(f"❌ ERROR: Bot lacks broadcast permissions in channel {channel_id}")
        except Exception as e:
            print(f"❌ ERROR: Radiation warning failed for channel {channel_id}: {e}")
            
    return sent_messages

def get_next_event_time():
    now = datetime.now(timezone.utc)
    next_event = now.replace(minute=EVENT_MINUTE, second=0, microsecond=0)
    if next_event <= now:
        next_event += timedelta(hours=1)
    return next_event

async def bot_loop():
    await bot.wait_until_ready()
    print("☢️ Nuclear Telemetry Loop Online & Monitoring.")

    while not bot.is_closed():
        next_event = get_next_event_time()
        event_ts = int(next_event.timestamp())

        now = datetime.now(timezone.utc)
        sleep_30m = (next_event - timedelta(minutes=30) - now).total_seconds()
        if sleep_30m > 0:
            await asyncio.sleep(sleep_30m)
            await broadcast_embed(
                title="☢️ RAD-ALERT: Blackhole Criticality Spike Detected",
                description=f"Sensors report high radioactive charge! The **Nuclear Blackhole Event** will form in **30 minutes**!\n\n**Detonation Time:** <t:{event_ts}:F>\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["30m"],
                image_url=IMAGES["30m"],
                ping=False
            )

        now = datetime.now(timezone.utc)
        sleep_10m = (next_event - timedelta(minutes=10) - now).total_seconds()
        if sleep_10m > 0:
            await asyncio.sleep(sleep_10m)
            await broadcast_embed(
                title="⚠️ HAZARD WARNING: Radiation Levels Escalating",
                description=f"Core instability rising! Severe fallout expected! Only **10 minutes** until singularity breach!\n\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["10m"],
                image_url=IMAGES["10m"],
                ping=False
            )

        now = datetime.now(timezone.utc)
        sleep_5m = (next_event - timedelta(minutes=5) - now).total_seconds()
        if sleep_5m > 0:
            await asyncio.sleep(sleep_5m)
            await broadcast_embed(
                title="☣️ CRITICAL WARNING: Core Breach Imminent",
                description=f"Equip hazmat gear and prep for deployment! **5 minutes** left before total nuclear meltdown!\n\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["5m"],
                image_url=IMAGES["5m"],
                ping=True
            )

        now = datetime.now(timezone.utc)
        sleep_1m = (next_event - timedelta(minutes=1) - now).total_seconds()
        if sleep_1m > 0:
            await asyncio.sleep(sleep_1m)
            await broadcast_embed(
                title="🚨 SIREN PROTOCOL: CODE RED SINGULARITY",
                description=f"ALL UNITS DOCK NOW! **1 minute** until the Nuclear Blackhole erupts!\n\n**Countdown:** <t:{event_ts}:R>",
                color=COLORS["1m"],
                image_url=IMAGES["1m"],
                ping=True
            )

        now = datetime.now(timezone.utc)
        sleep_3s = (next_event - timedelta(seconds=3) - now).total_seconds()
        if sleep_3s > 0:
            await asyncio.sleep(sleep_3s)
            
            sent_msgs = await broadcast_embed(
                title="☢️ DETONATION SEQUENCE",
                description="# 3️⃣ ...",
                color=COLORS["countdown"],
                ping=False
            )
            
            await asyncio.sleep(1)
            for ch, msg in sent_msgs:
                try:
                    embed = discord.Embed(title="☢️ DETONATION SEQUENCE", description="# 2️⃣ ..", color=COLORS["countdown"])
                    await msg.edit(embed=embed)
                except Exception:
                    pass

            await asyncio.sleep(1)
            for ch, msg in sent_msgs:
                try:
                    embed = discord.Embed(title="☢️ DETONATION SEQUENCE", description="# 1️⃣ .", color=COLORS["countdown"])
                    await msg.edit(embed=embed)
                except Exception:
                    pass

        now = datetime.now(timezone.utc)
        sleep_start = (next_event - now).total_seconds()
        if sleep_start > 0:
            await asyncio.sleep(sleep_start)

        await broadcast_embed(
            title="💥 NUCLEAR BLACKHOLE DETONATION ACTIVE! 💥",
            description="**TOTAL MELTDOWN IN PROGRESS!** The Radioactive Blackhole has erupted! CONTAIN THE SINGULARITY IMMEDIATELY!",
            color=COLORS["started"],
            image_url=IMAGES["started"],
            ping=True
        )

        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Clear duplicate guild commands
    for guild_id in ALLOWED_GUILDS:
        guild = discord.Object(id=guild_id)
        bot.tree.clear_commands(guild=guild)
        try:
            await bot.tree.sync(guild=guild)
            print(f"Cleared duplicate guild commands for sector {guild_id}.")
        except Exception as e:
            print(f"Failed to clear guild commands for sector {guild_id}: {e}")

    # Sync clean global commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global nuclear command(s).")
    except Exception as e:
        print(f"Failed to sync global commands: {e}")

    bot.loop.create_task(bot_loop())

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your DISCORD_TOKEN environment variable!")
    else:
        bot.run(DISCORD_TOKEN)
