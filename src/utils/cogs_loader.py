"""
Just a function for loading all cogs for the client
"""
import os

from discord.ext import commands

from logs import settings

logger = settings.logging.getLogger(__name__)


async def cog_loader(client: commands.Bot):
    """unloads all cogs."""
    for filename in os.listdir("src/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await client.load_extension(f"src.cogs.{filename[:-3]}")
            logger.info(f"Loaded src.cogs.{filename[:-3]}")

async def cog_reloader(client: commands.Bot):
    """reload all cogs."""
    for filename in os.listdir("src/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await client.reload_extension(f"src.cogs.{filename[:-3]}")
            logger.info(f"Loaded src.cogs.{filename[:-3]}")
