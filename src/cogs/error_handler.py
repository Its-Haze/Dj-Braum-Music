"""Discord cog for all Wavelink events"""
import logging as logger

import discord
import wavelink
from discord.ext import commands

from src.essentials.errors import MustBeSameChannel, NotConnectedToVoice
from src.utils.music_helper import MusicHelper


class ErrorHandler(commands.Cog):
    """
    Cog that triggers on error events.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.music = MusicHelper()
        bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        """Triggers when a error is raised."""
        await interaction.response.defer()

        if isinstance(error, NotConnectedToVoice):
            return await interaction.followup.send(
                embed=await self.music.user_not_in_vc()
            )
        if isinstance(error, MustBeSameChannel):
            player: wavelink.Player = wavelink.NodePool.get_node().get_player(
                guild=interaction.guild
            )
            return await interaction.followup.send(
                embed=await self.music.already_in_voicechannel(channel=player.channel)
            )


async def setup(bot):
    """
    Setup for the cog.
    """
    await bot.add_cog(ErrorHandler(bot))
