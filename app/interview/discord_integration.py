# Optional: create a Discord voice channel and return an invite link.
# Requires discord.py and a bot token. For MVP we recommend Jitsi (see jitsi.py).
import asyncio

async def create_voice_channel_and_invite(guild_id: int, channel_name: str = "ai-hr-interview"):
    import discord
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    link = None

    @client.event
    async def on_ready():
        try:
            guild = client.get_guild(guild_id)
            if guild is None:
                print("Guild not found")
            else:
                channel = await guild.create_voice_channel(channel_name)
                invite = await channel.create_invite(max_age=3600, max_uses=1, unique=True)
                nonlocal link
                link = invite.url
        finally:
            await client.close()

    await client.start(os.getenv("DISCORD_BOT_TOKEN"))
    return link
