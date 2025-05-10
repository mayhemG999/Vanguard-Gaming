import guilded
from guilded.ext import commands
import asyncio
import time
import json
import os
from collections import defaultdict
import random
from datetime import datetime

BOT_TOKEN = "gapi_H3AelwC+zSla9NJ8dCggWiHEfaTTcF0TcR8tohUO1QCErd+e67nQOeW5WJ0TTT8CAAxgJjfGqYtD8TQ7B8mnQw=="
OWNER_ID = "dwr5DOW4"

DEFAULT_EMOTE_ID = 2790195  # Your default emote ID


CONFIG_FILE = "config.json"
BACKUP_FILE = "backup.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def is_staff(ctx):
    config = load_config()
    staff_role_id = config.get("staff_role_id")
    return (
        (staff_role_id and staff_role_id in [r.id for r in ctx.author.roles])
        or ctx.author.id == OWNER_ID
    )

join_times = {}
message_logs = defaultdict(list)
muted_users = set()

JOIN_LIMIT = 5
JOIN_INTERVAL = 10
SPAM_THRESHOLD = 5
SPAM_INTERVAL = 4

bot = commands.Bot(command_prefix="/")
bot.owner_id = OWNER_ID

def can_configure(ctx):
    return ctx.author.id == OWNER_ID or ctx.author.id == ctx.guild.owner_id

@bot.event
async def on_ready():
    print(f"🟢 Bot is online, bot name: {bot.user.name}")
    try:
        await bot.set_status(content="Vanguard Gaming", emote=DEFAULT_EMOTE_ID)
        print("✅ Status set successfully!")
    except Exception as e:
        print(f"❌ Failed to set status: {e}")

@bot.command()
async def setstatus(ctx, *, status: str):
    """Change the bot's custom status."""
    try:
        await bot.set_status(content=status, emote=DEFAULT_EMOTE_ID)
        await ctx.send(f"✅ Status updated to: `{status}`")
    except Exception as e:
        await ctx.send(f"❌ Failed to update status: {e}")




@bot.event
async def on_member_join(member):
    join_times[str(member.id)] = str(datetime.utcnow())
    now = time.time()
    timestamps = list(join_times.values())
    timestamps = [float(t) for t in timestamps if now - float(t) < JOIN_INTERVAL]

    if len(timestamps) > JOIN_LIMIT:
        await member.ban(reason="Anti-raid: Mass join detected.")
        print(f"⚠️ Banned {member.name} for mass joining.")

@bot.event
async def on_message(message):
    if message.author.id in muted_users:
        return

    now = time.time()
    logs = message_logs[message.author.id]
    logs.append(now)
    message_logs[message.author.id] = [t for t in logs if now - t < SPAM_INTERVAL]

    if len(message_logs[message.author.id]) > SPAM_THRESHOLD:
        await message.channel.send(f"{message.author.mention} is spamming. Muted.")
        muted_users.add(message.author.id)
        await mute_user(message.author)

    if bot.user in message.mentions or message.content.startswith("/botinfo"):
        embed = guilded.Embed(
            title="Greetings!",
            description="Hello, I am Vanguard.\nI help keep your server safe!",
            color=guilded.Color.blue()
        )
        embed.add_field(name="Need help?", value="[Support Server](https://guilded.gg/Vanguardgaming)", inline=False)
        embed.add_field(name="Creator", value="Made by [Mayhem](https://www.guilded.gg/u/Mayhem999)", inline=False)
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

async def mute_user(user):
    try:
        await user.edit(nick="[Muted]")
    except Exception as e:
        print(f"Error muting {user.name}: {e}")

@bot.command()
async def backup(ctx):
    g = ctx.guild
    if g is None:
        return await ctx.send("Run this inside a server.")

    data = {
        "join_times": join_times,
        "message_logs": dict(message_logs),
        "muted_users": list(muted_users),
        "roles": [r.name for r in g.roles],
        "categories": {},
        "channels": []
    }

    for ch in g.channels:
        if ch.category_id:
            cat = await ch.category() if callable(getattr(ch, "category", None)) else ch.category
            data["categories"][str(ch.category_id)] = cat.name if cat else "Unnamed‑Category"

        data["channels"].append({
            "name": ch.name,
            "category_id": ch.category_id,
            "type": str(ch.type)
        })

    try:
        with open(BACKUP_FILE, "w") as f:
            json.dump(data, f, indent=4)
        await ctx.send("✅ Backup saved.")
    except Exception as e:
        await ctx.send(f"❌ Error saving backup: {e}")

@bot.command()
async def restore(ctx):
    msg = await ctx.send("♻️ Restoring server structure...")

    try:
        with open(BACKUP_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        return await msg.edit(content=f"❌ Couldn't load backup: {e}")

    global join_times, message_logs, muted_users
    join_times = data.get("join_times", [])
    message_logs = defaultdict(list, data.get("message_logs", {}))
    muted_users = set(data.get("muted_users", []))

    g = ctx.guild
    if g is None:
        return await msg.edit(content="❌ This command must be used inside a server.")

    for role_name in data.get("roles", []):
        try:
            await g.create_role(name=role_name)
        except Exception:
            continue

    cat_id_map = {}
    for old_id, cat_name in data.get("categories", {}).items():
        try:
            category = await g.create_channel(name=cat_name, type="category")
            cat_id_map[old_id] = category.id
        except Exception:
            continue

    for ch in data.get("channels", []):
        ch_type = ch.get("type", "text")
        ch_name = ch.get("name", "unnamed-channel")
        parent_id = ch.get("category_id")
        new_cat_id = cat_id_map.get(str(parent_id))

        try:
            await g.create_channel(name=ch_name, type=ch_type, category_id=new_cat_id)
        except Exception:
            continue

    await msg.edit(content="✅ Restored!")

@bot.command()
async def getroleid(ctx, *, name):
    role = next((r for r in ctx.guild.roles if r.name.lower() == name.lower()), None)
    if role:
        await ctx.send(f"The ID for role `{role.name}` is `{role.id}`.")
    else:
        await ctx.send("❌ Role not found.")

@bot.command()
async def listroles(ctx):
    roles = ctx.guild.roles
    if not roles:
        return await ctx.send("❌ No roles found.")

    role_list = "\n".join([f"- {role.name} (`{role.id}`)" for role in roles])
    await ctx.send(f"**Server Roles:**\n{role_list}")

@bot.command()
async def mute(ctx, member: guilded.Member):
    if not is_staff(ctx):
        return await ctx.send("⛔ You don't have permission.")
    muted_users.add(member.id)
    await ctx.send(f"{member.name} has been muted.")
    await mute_user(member)

@bot.command()
async def unmute(ctx, member: guilded.Member):
    if not is_staff(ctx):
        return await ctx.send("⛔ You don't have permission.")
    if member.id in muted_users:
        muted_users.remove(member.id)
        await ctx.send(f"{member.name} has been unmuted.")
    else:
        await ctx.send("That user isn't muted.")

@bot.command()
async def kick(ctx, member: guilded.Member, *, reason=None):
    if not is_staff(ctx):
        return await ctx.send("⛔ You don't have permission.")
    await member.kick(reason=reason)
    await ctx.send(f"{member.name} has been kicked.")

@bot.command()
async def ban(ctx, member: guilded.Member, *, reason=None):
    if not is_staff(ctx):
        return await ctx.send("⛔ You don't have permission.")
    await member.ban(reason=reason)
    await ctx.send(f"{member.name} has been banned.")

@bot.command()
async def warn(ctx, member: guilded.Member, *, reason="No reason provided"):
    if not is_staff(ctx):
        return await ctx.send("⛔ You don't have permission.")
    await ctx.send(f"⚠️ {member.mention} has been warned: {reason}")

@bot.command()
async def talk(ctx):
    await ctx.send("Hello! What would you like to talk about?")
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    try:
        response = await bot.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        return await ctx.send("You took too long to respond.")
    user_input = response.content.lower()
    responses = {
        "hi": "Hello there! How are you today?",
        "bye": "Goodbye! See you later!",
        "help": "Sure! How can I assist you?",
    }
    await ctx.send(responses.get(user_input, "That's interesting! Tell me more."))
    await ctx.send("Type 'end' to stop chatting.")
    try:
        response2 = await bot.wait_for('message', timeout=60.0, check=check)
        if response2.content.lower() == "end":
            await ctx.send("Okay, bye!")
        else:
            await ctx.send("Let's continue chatting!")
    except asyncio.TimeoutError:
        await ctx.send("Looks like you're done chatting!")

# ------------------ PING ------------------
@bot.command()
async def ping(ctx):
    """Simple latency check (custom format)."""
    latency_ms = bot.latency * 1000
    await ctx.send(f"The bot is running```Latency: {latency_ms:.0f} ms```")


bot.run(BOT_TOKEN)
