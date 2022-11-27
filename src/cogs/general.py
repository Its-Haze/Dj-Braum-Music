"""General discord Cog"""

import discord
from discord import app_commands
from discord.ext import commands

from src.utils.music_helper import MusicHelper  # pylint:disable=import-error


class General(commands.Cog):
    """
    Cog for General commands.
    """

    bot: commands.Bot
    music: MusicHelper

    def __init__(self, bot, music) -> None:
        self.bot = bot
        self.music = music

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
            embed=await self.music.display_new_releases(
                await self.music.get_new_releases()
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
            embed=await self.music.display_trending(await self.music.get_trending())
        )  ## Display the new releases embed.

    @app_commands.command(
        name="vote", description="Vote for Braum to help grow the bot!"
    )
    async def vote(self, interaction: discord.Interaction):
        """
        Vote command for top.gg
        """
        await interaction.response.defer()

        embed, view = await self.music.display_vote()

        return await interaction.followup.send(
            embed=embed, view=view
        )  ## Display the vote embed.

    @app_commands.command(name="support", description="Join my support server!")
    async def support(self, interaction: discord.Interaction):
        """
        Show the embed for joining Braums support server
        """
        await interaction.response.defer()

        embed, view = await self.music.display_support()

        return await interaction.followup.send(
            embed=embed, view=view
        )  ## Display the vote embed.

    @app_commands.command(name="invite", description="Invite Braum to other servers!")
    async def invite(self, interaction: discord.Interaction):
        """
        Invite link for braum
        """
        await interaction.response.defer()

        embed, view = await self.music.display_invite()

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
            embed=await self.music.display_search(search_query)
        )  ## Display the invite embed.

    @app_commands.command(
        name="lyrics", description="Braum finds lyrics for (almost) any song!"
    )
    @app_commands.describe(song_name="The name of the song to retrieve lyrics for.")
    async def lyrics(self, interaction: discord.Interaction, *, song_name: str):
        await interaction.response.defer(
            ephemeral=True
        )  ## Send as an ephemeral to avoid clutter.

        lyrics_embed = await self.music.display_lyrics(
            await self.music.get_lyrics(song_name)
        )  ## Retrieve the lyrics and embed it.

        try:
            return await interaction.followup.send(
                embed=lyrics_embed
            )  ## Display the lyrics embed.
        except discord.HTTPException:  ## If the lyrics are more than 4096 characters, respond.
            return await interaction.followup.send(
                embed=await self.music.lyrics_too_long()
            )


async def setup(bot):
    music = MusicHelper()
    await bot.add_cog(General(bot, music))
