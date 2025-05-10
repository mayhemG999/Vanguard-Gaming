from guilded.ext import commands
import guilded

bot = commands.Bot(command_prefix="/")

DEFAULT_EMOTE_ID = 2790195  # Your default emote ID

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    try:
        await bot.set_status(content="Ready to serve!", emote=DEFAULT_EMOTE_ID)
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

bot.run("gapi_H3AelwC+zSla9NJ8dCggWiHEfaTTcF0TcR8tohUO1QCErd+e67nQOeW5WJ0TTT8CAAxgJjfGqYtD8TQ7B8mnQw==")
