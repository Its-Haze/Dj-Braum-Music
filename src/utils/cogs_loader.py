"""
Just a function for loading all cogs for the client
"""
import os

from discord.ext import commands

from logs import settings  # pylint:disable=import-error

logger = settings.logging.getLogger(__name__)


async def cog_loader(client: commands.Bot):
    """unloads all cogs."""
    for filename in os.listdir("./src/cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"src.cogs.{filename[:-3]}")
            print(f"Loaded src.cogs.{filename[:-3]}")
