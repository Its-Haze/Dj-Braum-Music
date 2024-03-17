"""Discord Cog for all Music commands"""

import logging as logger
import re

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from src.essentials.checks import (
    allowed_to_connect,
    in_same_channel,
    member_in_voicechannel,
)
from src.utils.functions import Functions
from src.utils.responses import Responses
from src.utils.spotify_models import SpotifyTrack


class Music(commands.Cog):
    """
    This cog holds all Music related commands
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.responses = Responses()
        self.functions = Functions()

    @app_commands.command(name="join", description="Braum joins your voice channel.")
    @allowed_to_connect()
    @in_same_channel()
    @member_in_voicechannel()
    async def join(self, interaction: discord.Interaction):
        """
        /Join command
        """
        await interaction.response.defer()
        voice_channel: discord.channel.VocalGuildChannel = (
            interaction.user.voice.channel  # type:ignore
        )
        guild: discord.Guild = interaction.guild  # type:ignore

        logger.info("Joining %s", voice_channel)

        if not guild.voice_client:  # If user is in a VC and bot is not, join it.
            await voice_channel.connect(cls=wavelink.Player, self_deaf=True)

            embed = await self.responses.in_vc()
            return await interaction.followup.send(embed=embed)

        return await interaction.followup.send(
            embed=await self.responses.already_in_vc()
        )

    @app_commands.command(name="leave", description="Braum leaves your voice channel.")
    @in_same_channel()
    @member_in_voicechannel()
    async def leave(self, interaction: discord.Interaction):
        """
        /leave command
        """
        await interaction.response.defer()
        guild: discord.Guild = interaction.guild
        if not guild.voice_client:  # If bot is not in a VC, respond.
            return await interaction.followup.send(
                embed=await self.responses.already_left_vc()
            )

        await interaction.guild.voice_client.disconnect()
        return await interaction.followup.send(embed=await self.responses.left_vc())

    @app_commands.command(
        name="pause", description="Braum pauses the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def pause(self, interaction: discord.Interaction):
        """
        /pause command
        """
        await interaction.response.defer()

        ## Retrieve the current player.
        player = await self.functions.get_player(interaction.guild)

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve currently playing track's info.
        track = await self.functions.get_track(interaction.guild)

        # If the player is already paused, respond
        if player.paused:
            return await interaction.followup.send(
                embed=await self.responses.already_paused(track)
            )

        ## If the current track is not paused, pause it.
        await player.pause(not player.paused)
        return await interaction.followup.send(
            embed=await self.responses.common_track_actions(track, "Paused")
        )

    @app_commands.command(
        name="resume", description="Braum resumes the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def resume(self, interaction: discord.Interaction):
        """
        /resume command
        """
        await interaction.response.defer()

        ## Retrieve the current player.
        player = await self.functions.get_player(interaction.guild)

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve currently playing track's info.
        track = await self.functions.get_track(interaction.guild)

        ## If the current track is paused, resume it.
        if player.paused:
            await player.pause(not player.paused)
            return await interaction.followup.send(
                embed=await self.responses.common_track_actions(track, "Resumed")
            )

        ## Otherwise, respond.
        return await interaction.followup.send(
            embed=await self.responses.already_resumed(track)
        )

    @app_commands.command(
        name="stop", description="Braum stops the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def stop(self, interaction: discord.Interaction):
        """
        /stop command
        """
        await interaction.response.defer()

        if not await self.functions.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## If bot is in a VC, stop the currently playing track.
        ## Retrieve currently playing track's info.
        track = await self.functions.get_track(interaction.guild)

        ## Retrieve the current player.
        player = await self.functions.get_player(interaction.guild)
        await interaction.followup.send(
            embed=await self.responses.common_track_actions(track, "Stopped")
        )

        ## Stop the track after sending the embed.
        return await player.stop()

    @app_commands.command(
        name="skip", description="Braum skips the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def skip(self, interaction: discord.Interaction):
        """
        /skip command
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve the current player.
        player = await self.functions.get_player(interaction.guild)

        ## Retrieve currently playing track's info.
        track = await self.functions.get_track(interaction.guild)
        await interaction.followup.send(
            embed=await self.responses.common_track_actions(track, "Skipped")
        )

        ## Skip the track after sending the embed.
        return await player.skip()

    @app_commands.command(name="queue", description="Braum shows you the queue.")
    async def queue(self, interaction: discord.Interaction):
        """
        /queue command
        """
        await interaction.response.defer()

        if not await self.functions.get_player(
            interaction.guild
        ) or not await self.functions.get_track(interaction.guild):
            ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Show the queue.
        return await interaction.followup.send(
            embed=await self.responses.show_queue(
                await self.functions.get_queue(interaction.guild), interaction.guild
            )
        )

    @app_commands.command(
        name="history",
        description="Braum shows you the history of songs that have been played.",
    )
    async def history(self, interaction: discord.Interaction):
        """
        /history command
        """
        await interaction.response.defer()

        player = await self.functions.get_player(interaction.guild)

        if not hasattr(player, "custom_queue"):
            return await interaction.followup.send(
                embed=await self.responses.nothing_in_history()
            )

        history_tracks: wavelink.Queue = player.custom_queue.history
        if not history_tracks:
            return await interaction.followup.send(
                embed=await self.responses.nothing_in_history()
            )

        ## Show the queue.
        return await interaction.followup.send(
            embed=await self.responses.show_history(list(history_tracks), interaction)
        )

    @app_commands.command(name="shuffle", description="Braum shuffles the queue.")
    @in_same_channel()
    @member_in_voicechannel()
    async def shuffle(self, interaction: discord.Interaction):
        """
        /shuffle command
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve the current queue.
        queue = await self.functions.get_queue(interaction.guild)

        ## Retrieve the current track.
        track = await self.functions.get_track(interaction.guild)

        ## Retrieve the current player.
        player = await self.functions.get_player(interaction.guild)

        ## If there are no tracks in the queue, respond.
        if len(queue) == 0:
            return await interaction.followup.send(
                embed=await self.responses.empty_queue()
            )

        else:
            ## Shuffle the queue.
            await self.functions.shuffle(queue)

            ## If the queue loop is not enabled, place the current track at the end of the queue.
            if not player.queue_loop:
                ## Add the current track to the end of the queue.
                player.queue.put(track)
            return await interaction.followup.send(
                embed=await self.responses.shuffled_queue()
            )

    @app_commands.command(name="nightcore", description="Braum enables nightcore mode.")
    async def nightcore(self, interaction: discord.Interaction):
        """
        /nightcore command sets the filter to a nightcore.
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve the current player.
        player = await self.functions.get_player(interaction.guild)
        if not player:
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## If nightcore mode is already enabled, respond.
        if hasattr(player, "nightcore") and player.nightcore:

            player.nightcore = False
            filters: wavelink.Filters = player.filters
            filters.timescale.reset()
            await player.set_filters(filters)
            return await interaction.followup.send(
                embed=await self.responses.nightcore_disable()
            )

        ## Enable nightcore mode.
        player.nightcore = True
        filters: wavelink.Filters = player.filters
        filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
        await player.set_filters(filters)
        return await interaction.followup.send(
            embed=await self.responses.nightcore_enable()
        )

    @app_commands.command(
        name="nowplaying", description="Braum shows you the currently playing song."
    )
    async def nowplaying(self, interaction: discord.Interaction):
        """
        Displays the currently playing song.
        """
        await interaction.response.defer()

        player = wavelink.Pool().get_node().get_player(interaction.guild.id)
        if not player:
            # handle edge cases
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## If nothing is playing, respond.
        if not player.playing:
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve currently playing track's info.
        track = await self.functions.get_track(interaction.guild)

        return await interaction.followup.send(
            embed=await self.responses.display_track(player, track, True)
        )

    @app_commands.command(name="volume", description="Braum adjusts the volume.")
    @app_commands.describe(
        volume_percentage="The percentage to set the volume to. Accepted range: 0 to 100."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def volume(self, interaction: discord.Interaction, *, volume_percentage: int):
        """
        Sets the volume %
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Volume cannot be greater than 100%.
        if volume_percentage > 100:
            return await interaction.followup.send(
                embed=await self.responses.volume_too_high()
            )

        ## Adjust the volume to the specified percentage.
        await self.functions.modify_volume(interaction.guild, volume_percentage)
        return await interaction.followup.send(
            embed=await self.responses.volume_set(percentage=volume_percentage)
        )

    @app_commands.command(
        name="remove", description="Braum removes a track from the queue."
    )
    @app_commands.describe(
        track_index="The number of track to remove. Find out the track number using /queue."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def remove(self, interaction: discord.Interaction, *, track_index: int):
        """
        /remove command
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Store the info beforehand as the track will be removed.
        remove_msg = await self.responses.queue_track_actions(
            await self.functions.get_queue(interaction.guild), track_index, "Removed"
        )

        ## If the track exists in the queue, respond.
        if remove_msg:
            ## Remove the track.
            await self.functions.remove_track(
                await self.functions.get_queue(interaction.guild), track_index
            )
            return await interaction.followup.send(embed=remove_msg)

        ## If the track was not removed, respond.
        return await interaction.followup.send(
            embed=await self.responses.track_not_in_queue()
        )

    @app_commands.command(
        name="skipto", description="Braum skips to a specific track in the queue."
    )
    @app_commands.describe(
        track_index="The number of track to skip to. Find out the track number using /queue."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def skipto(self, interaction: discord.Interaction, *, track_index: int):
        """
        /skipto command
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Store the info beforehand as the track will be removed.
        skipped_msg = await self.responses.queue_track_actions(
            await self.functions.get_queue(interaction.guild), track_index, "Skipped to"
        )

        ## If the track exists in the queue, respond.
        if skipped_msg:
            ## Skip to the requested track.
            await self.functions.skipto_track(interaction.guild, track_index)
            ## Stop the currently playing track.
            await interaction.guild.voice_client.stop()
            return await interaction.followup.send(embed=skipped_msg)

        ## If the track was not skipped, respond.
        return await interaction.followup.send(
            embed=await self.responses.track_not_in_queue()
        )

    @app_commands.command(name="empty", description="Braum empties the queue.")
    @in_same_channel()
    @member_in_voicechannel()
    async def empty(self, interaction: discord.Interaction):
        """
        /empty command
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.functions.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## If bot is in a VC, empty the queue.
        elif interaction.guild.voice_client:
            ## Retrieve the current queue.
            queue = await self.functions.get_queue(interaction.guild)

            ## Retrieve the player.
            player = await self.functions.get_player(interaction.guild)

            ## If there are no tracks in the queue, respond.
            if len(queue) == 0:
                return await interaction.followup.send(
                    embed=await self.responses.empty_queue()
                )

            ## Otherwise, clear the queue.
            player.queue.clear()
            return await interaction.followup.send(
                embed=await self.responses.cleared_queue()
            )

    @app_commands.command(
        name="loop", description="Braum loops the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def loop(self, interaction: discord.Interaction):
        """
        /loop command
        """
        await interaction.response.defer()

        ## Retrieve the player.
        player: wavelink.Player = await self.functions.get_player(interaction.guild)

        ## If nothing is playing, respond.
        if not player.playing:  # includes paused.
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## Retrieve the currently playing track.
        track = await self.functions.get_track(interaction.guild)

        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            return await interaction.followup.send(
                embed=await self.responses.common_track_actions(
                    track, "Stopped looping"
                )
            )
        else:
            player.queue.mode = wavelink.QueueMode.loop
            return await interaction.followup.send(
                embed=await self.responses.common_track_actions(track, "Looping")
            )

    @app_commands.command(
        name="queueloop", description="Braum loops the current queue."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def queueloop(self, interaction: discord.Interaction):
        """
        /queueloop command
        """
        await interaction.response.defer()

        ## Retrieve the player.
        player = await self.functions.get_player(interaction.guild)

        ## If nothing is playing, respond.
        if not player.playing:
            return await interaction.followup.send(
                embed=await self.responses.nothing_is_playing()
            )

        ## If there is less than 1 track in the queue and there is not a current queueloop, respond.
        if len(player.queue) < 1:
            return await interaction.followup.send(
                embed=await self.responses.less_than_1_track()
            )

        if player.queue.mode == wavelink.QueueMode.loop_all:
            player.queue.mode = wavelink.QueueMode.normal
            return await interaction.followup.send(
                embed=await self.responses.common_track_actions(
                    None, "Stopped looping the queue"
                )
            )
        else:
            player.queue.mode = wavelink.QueueMode.loop_all

            return await interaction.followup.send(
                embed=await self.responses.common_track_actions(
                    None, "Looping the queue"
                )
            )

    @app_commands.command(name="play", description="Braum plays your desired song.")
    @app_commands.describe(
        search="Search for songs or paste YouTube/Spotify links directly.",
    )
    @allowed_to_connect()
    @in_same_channel()
    @member_in_voicechannel()
    async def play(
        self,
        interaction: discord.Interaction,
        *,
        search: str,
    ):
        """
        /play command to play a song, album or playlist.
        If a spotify link is entered, it will be added to the queue.
        If a track name is entered, it will be searched and added to the queue.
        """
        await interaction.response.defer()
        logger.info(
            "/Play command executed with search=(%s), by=(%s), in the guild=(%s)",
            search,
            interaction.user,
            interaction.guild,
        )

        # SEARCH FOR TRACKS
        try:
            found_tracks: wavelink.Search = await wavelink.Playable.search(search)
        except wavelink.exceptions.LavalinkLoadException as e:
            logger.warning(
                "Nothing critical, but searching for tracks failed: %s %s",
                e,
                {"search": search},
                exc_info=True,
            )
            logger.info("Sending out [Unable to find any results!] embed")
            return await interaction.followup.send(
                embed=await self.responses.no_track_results()
            )
        if not found_tracks:
            ## If no results are found or an invalid query was entered, respond.
            logger.info(
                "did not find any tracks. Sending out [Unable to find any results!] embed: %s",
                {"search": search},
            )
            return await interaction.followup.send(
                embed=await self.responses.no_track_results()
            )

        # CONNECT TO VOICE CHANNEL
        if not interaction.guild.voice_client:
            player: wavelink.Player = await interaction.user.voice.channel.connect(
                cls=wavelink.Player, self_deaf=True
            )
        else:
            ## Otherwise, initalize voice_client.
            player: wavelink.Player = interaction.guild.voice_client

        # INITIALIZE PLAYER ATTRIBUTES
        player.reply = interaction.channel
        player.now_playing_message = None

        if not hasattr(player, "custom_queue"):
            # Store all tracks in a custom queue.
            # This is meant to deliver a better history experience. (see /history)
            player.custom_queue = wavelink.Queue(history=True)

        # Automatically play the next track in the queue.
        # But not recommendations.
        if player.autoplay == wavelink.AutoPlayMode.disabled:
            player.autoplay = wavelink.AutoPlayMode.partial

        # ADD TRACKS TO QUEUE AND PLAY THEM
        if not isinstance(found_tracks, wavelink.tracks.Playlist):
            # A track has been found
            logger.info("User entered a track. Adding to queue. %s", search)
            track = found_tracks[0]
            await player.queue.put_wait(track)
            if not player.playing:
                # If nothing is playing, play the song.
                await player.play(player.queue.get(), volume=50)

            return await interaction.followup.send(
                embed=await self.responses.added_track(track, interaction.user)
            )

        # ADD PLAYLIST TO QUEUE AND PLAY IT
        logger.info("Playlist found")
        playlist = found_tracks  # just for clarity
        tracks: wavelink.Playable = playlist.tracks
        logger.info(
            "Playlist detected, Adding tracks to queue, %s",
            {
                "name": playlist.name,
                "author": playlist.author,
                "type": playlist.type,
                "url": playlist.url,
            },
        )
        for i, track in enumerate(tracks):
            logger.info(
                "Adding track to queue: %s",
                {
                    "source": track.source,
                    "title": track.title,
                    "identifier": track.identifier,
                },
            )
            await player.queue.put_wait(track)
            if i == 1 and not player.playing:
                await player.play(player.queue.get(), volume=50)

        return await interaction.followup.send(
            embed=(
                await self.responses.display_playlist(
                    playlist,
                    type=(
                        "Playlist"
                        if playlist.type and playlist.type == "playlist"
                        else "Album"
                    ),
                )
            )
        )

    @play.autocomplete("search")
    async def play_autocomplete(
        self,
        interaction: discord.Interaction,  # pylint:disable=unused-argument
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Auto suggestion for queryng spotify
        clickable options appear and spotify link the linked value
        """
        limit = 7

        if current.strip() == "":
            # When no search query has been entered, display trending songs.
            try:
                trending: dict = await self.functions.get_trending()

                trending_choice: list[SpotifyTrack] = SpotifyTrack.from_search_results(
                    [track["track"] for track in trending["items"]]
                )
            except Exception as e:
                logger.error("Error getting trending songs: %s", e, exc_info=True)

            if not trending_choice:
                return [
                    app_commands.Choice(
                        name="The only song you should listen to!",
                        value="https://open.spotify.com/track/6ctO0maVSlFzn31wR0GpNg",
                    ),
                ]

            my_tracks = self.format_songs_to_autocomplete(trending_choice)
            return my_tracks

        if "https://" in current.lower().strip() and not (
            "open.spotify.com" in current.lower() or "youtube.com" in current.lower()
        ):
            return [
                app_commands.Choice(
                    name="Only Youtube and Spotify links are supported!",
                    value=current,
                )
            ]
        elif "https://" in current.lower().strip():
            return [
                app_commands.Choice(
                    name=current,
                    value=current,
                ),
            ]

        query_searched = await self.functions.search_songs(
            current.lower(),
            category="track",
            limit=limit,
        )
        formatted_track_results: list[SpotifyTrack] = (
            await self.functions.format_query_search_results_track(
                search_results=query_searched, limit=limit
            )
        )
        my_tracks = []

        for song in formatted_track_results:
            long_name = f"{song.name} - {song.artists} - {self.functions.convert_ms(song.duration_ms)}"
            short_name = f"{song.name} - {self.functions.convert_ms(song.duration_ms)}"

            my_tracks.append(
                app_commands.Choice(
                    name=long_name if len(long_name) < 100 else short_name,
                    value=song.external_urls,
                )
            )
        return my_tracks

    def format_songs_to_autocomplete(
        self,
        trending_choice: list[SpotifyTrack],
        sorted_by_popularity: bool = True,
    ) -> list[app_commands.Choice]:

        if sorted_by_popularity:
            trending_choice = self.functions.sort_spotify_tracks_by_popularity(
                trending_choice
            )

        my_tracks: app_commands.Choice = []
        for song in trending_choice:
            long_name = f"{song.name} - {song.artists} - {self.functions.convert_ms(song.duration_ms)}"
            short_name = f"{song.name} - {self.functions.convert_ms(song.duration_ms)}"

            my_tracks.append(
                app_commands.Choice(
                    name=long_name if len(long_name) < 100 else short_name,
                    value=song.external_urls,
                )
            )
        return my_tracks


async def setup(bot):
    """
    Setup the cog.
    """
    await bot.add_cog(Music(bot))
