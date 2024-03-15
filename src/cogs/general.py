"""General discord Cog"""

import logging as logger

import discord
from discord import app_commands
from discord.ext import commands

from src.utils.functions import Functions
from src.utils.responses import Responses


class General(commands.Cog):
    """
    Cog for General commands.
    """

    bot: commands.Bot

    def __init__(self, bot) -> None:
        self.bot = bot
        self.responses = Responses()
        self.functions = Functions()

    @app_commands.command(
        name="newreleases",
        description="Braum shows you the newly released tracks of the day.",
    )
    async def newreleases(self, interaction: discord.Interaction):
        """
        Shows the 10 latest releases
        """
        await interaction.response.defer()

        return await interaction.followup.send(
            embed=await self.responses.display_new_releases(
                await self.functions.get_new_releases()
            )
        )  ## Display the trending embed.

    @app_commands.command(
        name="trending", description="Braum shows you the trending tracks of the day."
    )
    async def trending(self, interaction: discord.Interaction):
        """
        Shows the trending chart
        """
        await interaction.response.defer()

        return await interaction.followup.send(
            embed=await self.responses.display_trending(
                await self.functions.get_trending()
            )
        )  ## Display the new releases embed.

    @app_commands.command(
        name="vote", description="Vote for Braum to help grow the bot!"
    )
    async def vote(self, interaction: discord.Interaction):
        """
        Vote command for top.gg
        """
        await interaction.response.defer()

        embed, view = await self.responses.display_vote()

        return await interaction.followup.send(
            embed=embed, view=view
        )  ## Display the vote embed.

    @app_commands.command(name="support", description="Join my support server!")
    async def support(self, interaction: discord.Interaction):
        """
        Show the embed for joining Braums support server
        """
        await interaction.response.defer()

        embed, view = await self.responses.display_support()

        return await interaction.followup.send(
            embed=embed, view=view
        )  ## Display the vote embed.

    @app_commands.command(name="invite", description="Invite Braum to other servers!")
    async def invite(self, interaction: discord.Interaction):
        """
        Invite link for braum
        """
        await interaction.response.defer()

        embed, view = await self.responses.display_invite()

        return await interaction.followup.send(
            embed=embed, view=view
        )  ## Display the invite embed.

    @app_commands.command(
        name="search", description="Braum searches Spotify for tracks!"
    )
    @app_commands.describe(search_query="The name of the song to search for.")
    async def search(self, interaction: discord.Interaction, *, search_query: str):
        """
        Search command for
        """
        await interaction.response.defer()

        return await interaction.followup.send(
            embed=await self.responses.display_search(search_query)
        )  ## Display the invite embed.

    async def fetch_lyrics(self, interaction: discord.Interaction):
        """
        Fetch the lyrics of the current song.
        """
        await interaction.response.defer(
            ephemeral=True
        )  ## Send as an ephemeral to avoid clutter.

        if not (current_track := await self.functions.get_track(interaction.guild)):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        if current_track.source != "spotify":
            return await interaction.followup.send(
                embed=await self.responses.display_lyrics_error_only_spotify_song_allowed()
            )

        lyrics = await self.functions.get_lyrics(current_track)

        if not lyrics:
            return await interaction.followup.send(
                embed=await self.responses.lyrics_not_found(current_track)
            )

        lyrics_embed = await self.responses.display_lyrics(
            lyrics, interaction.user
        )  ## Retrieve the lyrics and embed it.

        try:
            return await interaction.followup.send(
                embed=lyrics_embed
            )  ## Display the lyrics embed.
        except (
            discord.HTTPException
        ):  ## If the lyrics are more than 4096 characters, respond.
            return await interaction.followup.send(
                embed=await self.responses.lyrics_too_long()
            )

    @app_commands.command(
        name="lyrics", description="Will try to fetch the lyrics of the current song."
    )
    async def lyrics(self, interaction: discord.Interaction):
        """
        Fetch the lyrics of the current song.
        """
        await self.fetch_lyrics(interaction)


async def setup(bot):
    """
    Setup the cog.
    """
    await bot.add_cog(General(bot))
