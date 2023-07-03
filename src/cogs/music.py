"""Discord Cog for all Music commands"""
import asyncio
import logging as logger
import re

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from src.essentials.checks import in_same_channel, member_in_voicechannel
from src.utils.music_helper import MusicHelper
from src.utils.spotify_models import SpotifyTrack


class Music(commands.Cog):
    """
    This cog holds all Music related commands
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.music = MusicHelper()

    @app_commands.command(name="join", description="Braum joins your voice channel.")
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

            embed = await self.music.in_vc()
            return await interaction.followup.send(embed=embed)

    @app_commands.command(name="leave", description="Braum leaves your voice channel.")
    @in_same_channel()
    @member_in_voicechannel()
    async def leave(self, interaction: discord.Interaction):
        """
        /leave command
        """
        await interaction.response.defer()

        await interaction.guild.voice_client.disconnect()
        return await interaction.followup.send(embed=await self.music.left_vc())

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
        player = await self.music.get_player(interaction.guild)

        ## If nothing is playing, respond.
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve currently playing track's info.
        track = await self.music.get_track(interaction.guild)

        # If the player is already paused, respond
        if player.is_paused():
            return await interaction.followup.send(
                embed=await self.music.already_paused(track)
            )

        ## If the current track is not paused, pause it.
        await interaction.guild.voice_client.pause()
        return await interaction.followup.send(
            embed=await self.music.common_track_actions(track, "Paused")
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
        player = await self.music.get_player(interaction.guild)

        ## If nothing is playing, respond.
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve currently playing track's info.
        track = await self.music.get_track(interaction.guild)

        ## If the current track is paused, resume it.
        if player.is_paused():
            await interaction.guild.voice_client.resume()
            return await interaction.followup.send(
                embed=await self.music.common_track_actions(track, "Resumed")
            )

        ## Otherwise, respond.
        return await interaction.followup.send(
            embed=await self.music.already_resumed(track)
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

        if not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## If bot is in a VC, stop the currently playing track.
        ## Retrieve currently playing track's info.
        track = await self.music.get_track(interaction.guild)

        ## Retrieve the current player.
        player = await self.music.get_player(interaction.guild)
        await interaction.followup.send(
            embed=await self.music.common_track_actions(track, "Stopped")
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
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve the current player.
        player = await self.music.get_player(interaction.guild)

        ## Retrieve currently playing track's info.
        track = await self.music.get_track(interaction.guild)
        await interaction.followup.send(
            embed=await self.music.common_track_actions(track, "Skipped")
        )

        ## Skip the track after sending the embed.
        return await player.stop()

    @app_commands.command(name="queue", description="Braum shows you the queue.")
    async def queue(self, interaction: discord.Interaction):
        """
        /queue command
        """
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(interaction.guild):
            ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Show the queue.
        return await interaction.followup.send(
            embed=await self.music.show_queue(
                await self.music.get_queue(interaction.guild), interaction.guild
            )
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
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve the current queue.
        queue = await self.music.get_queue(interaction.guild)

        ## Retrieve the current track.
        track = await self.music.get_track(interaction.guild)

        ## Retrieve the current player.
        player = await self.music.get_player(interaction.guild)

        ## If there are no tracks in the queue, respond.
        if len(queue) == 0:
            return await interaction.followup.send(embed=await self.music.empty_queue())

        else:
            ## Shuffle the queue.
            await self.music.shuffle(queue)

            ## If the queue loop is not enabled, place the current track at the end of the queue.
            if not player.queue_loop:
                ## Add the current track to the end of the queue.
                player.queue.put(track)
            return await interaction.followup.send(
                embed=await self.music.shuffled_queue()
            )

    @app_commands.command(
        name="nowplaying", description="Braum shows you the currently playing song."
    )
    async def nowplaying(self, interaction: discord.Interaction):
        """
        Displays the currently playing song.
        """
        await interaction.response.defer()

        ## If nothing is playing, respond.
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve currently playing track's info.
        track = await self.music.get_track(interaction.guild)

        return await interaction.followup.send(
            embed=await self.music.display_track(track, interaction.guild, False, True)
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
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Volume cannot be greater than 100%.
        if volume_percentage > 100:
            return await interaction.followup.send(
                embed=await self.music.volume_too_high()
            )

        ## Adjust the volume to the specified percentage.
        await self.music.modify_volume(interaction.guild, volume_percentage)
        return await interaction.followup.send(
            embed=await self.music.volume_set(volume_percentage)
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
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Store the info beforehand as the track will be removed.
        remove_msg = await self.music.queue_track_actions(
            await self.music.get_queue(interaction.guild), track_index, "Removed"
        )

        ## If the track exists in the queue, respond.
        if remove_msg:
            ## Remove the track.
            await self.music.remove_track(
                await self.music.get_queue(interaction.guild), track_index
            )
            return await interaction.followup.send(embed=remove_msg)

        ## If the track was not removed, respond.
        return await interaction.followup.send(
            embed=await self.music.track_not_in_queue()
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
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Store the info beforehand as the track will be removed.
        skipped_msg = await self.music.queue_track_actions(
            await self.music.get_queue(interaction.guild), track_index, "Skipped to"
        )

        ## If the track exists in the queue, respond.
        if skipped_msg:
            ## Skip to the requested track.
            await self.music.skipto_track(interaction.guild, track_index)
            ## Stop the currently playing track.
            await interaction.guild.voice_client.stop()
            return await interaction.followup.send(embed=skipped_msg)

        ## If the track was not skipped, respond.
        return await interaction.followup.send(
            embed=await self.music.track_not_in_queue()
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
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## If bot is in a VC, empty the queue.
        elif interaction.guild.voice_client:
            ## Retrieve the current queue.
            queue = await self.music.get_queue(interaction.guild)

            ## Retrieve the player.
            player = await self.music.get_player(interaction.guild)

            ## If there are no tracks in the queue, respond.
            if len(queue) == 0:
                return await interaction.followup.send(
                    embed=await self.music.empty_queue()
                )

            ## Otherwise, clear the queue.
            player.queue.clear()
            return await interaction.followup.send(
                embed=await self.music.cleared_queue()
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

        ## If nothing is playing, respond.
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve the player.
        player = await self.music.get_player(interaction.guild)

        ## Retrieve the currently playing track.
        track = await self.music.get_track(interaction.guild)

        ## If the loop is not enabled, enable it.
        if not player.loop:
            ## Send the msg before enabling the loop to avoid confusing embed titles.
            await interaction.followup.send(
                embed=await self.music.common_track_actions(track, "Looping")
            )
            player.loop = True

            ## Store the currently playing track so that it can be looped.
            player.looped_track = track
            return

        player.loop = False
        return await interaction.followup.send(
            embed=await self.music.common_track_actions(track, "Stopped looping")
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

        ## If nothing is playing, respond.
        if not await self.music.get_track(interaction.guild):
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        ## Retrieve the player.
        player = await self.music.get_player(interaction.guild)

        ## Retrieve the currently playing track.
        track = await self.music.get_track(interaction.guild)
        ## Retrieve the current queue.
        queue = await self.music.get_queue(interaction.guild)

        ## If there is less than 1 track in the queue and there is not a current queueloop, respond.
        if len(queue) < 1 and not player.queue_loop:
            return await interaction.followup.send(
                embed=await self.music.less_than_1_track()
            )

        ## If the queue loop is not enabled, enable it.
        if not player.queue_loop:
            ## Send the msg before enabling the queue loop to avoid confusing embed titles.
            await interaction.followup.send(
                embed=await self.music.common_track_actions(None, "Looping the queue")
            )
            player.queue_loop = True

            ## Add the currently playing track.
            player.queue_looped_track = track
            return

        ## If the queue loop is already enabled, disable it.
        player.queue_loop = False

        ## Prevents the current track from constantly being assigned.
        player.queue_looped_track = None

        return await interaction.followup.send(
            embed=await self.music.common_track_actions(
                None, "Stopped looping the queue"
            )
        )

    @app_commands.command(name="play", description="Braum plays your desired song.")
    @app_commands.describe(
        # category="Select a category for your search! | Track, Album, Spotify_Link",
        search="Enter your spotify search here! / You can also enter a Spotify URL here",
    )
    # @app_commands.choices(
    #     category=[
    #         app_commands.Choice(name="Track", value="track"),
    #         app_commands.Choice(name="Album", value="album"),
    #     ]
    # )
    @in_same_channel()
    @member_in_voicechannel()
    async def play(
        self,
        interaction: discord.Interaction,
        *,
        search: str,
        # category: typing.Optional[discord.app_commands.Choice[str]],
    ):
        """
        Play command
        Accepts normal text querys
        If link is found, it will run /url and validate spotify urls
        """
        await interaction.response.defer()

        ## If user is in a VC, join it.

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(
                cls=wavelink.Player, self_deaf=True
            )
        else:
            ## Otherwise, initalize voice_client.
            vc: wavelink.Player = interaction.guild.voice_client

        ## If a URL is entered, respond.
        if re.match(self.music.url_regex, search):
            # self.url validates that it is a valid spotify URL
            return await self.url(interaction=interaction, spotify_url=search)

        try:
            ## Search for a song.
            track = await wavelink.YouTubeMusicTrack.search(search, return_first=True)
        except (
            IndexError,
            TypeError,
        ):
            ## If no results are found or an invalid query was entered, respond.
            return await interaction.followup.send(
                embed=await self.music.no_track_results()
            )

        ## Store the channel id to be used in track_start.
        vc.reply = interaction.channel

        ## Modify the track info.
        final_track = await self.music.gather_track_info(
            track.title, track.author, track
        )

        ## If a track is playing, add it to the queue.
        if vc.is_playing():
            ## Use the modified track.
            await interaction.followup.send(
                embed=await self.music.added_track(final_track)
            )

            ## Add the modified track to the queue.
            return await vc.queue.put_wait(final_track)

        else:
            ## Otherwise, begin playing.

            ## Send an ephemeral as now playing is handled by on_track_start.
            msg = await interaction.followup.send(
                embed=await self.music.started_playing()
            )

            ## Set the loop value to false as we have just started playing.
            vc.loop = False

            ## Set the queue_loop value to false as we have just started playing.
            vc.queue_loop = False

            ## Used to store the currently playing track in case the user decides to loop.
            vc.looped_track = None

            ## Used to re-add the track in a queue loop.
            vc.queue_looped_track = None

            ## Play the modified track.
            await vc.play(final_track)

            ## Delete the message after 5 seconds.
            await asyncio.sleep(5)
            return await interaction.followup.delete_message(msg.id)

    async def url(self, interaction: discord.Interaction, *, spotify_url: str):
        """
        Validates the URL to check for open.spotify links only
        Adds the spotify song/album/playlist to the queue
        """

        if "?" in spotify_url:
            spotify_url = spotify_url.split("?")[0]

        if (
            "https://open.spotify.com/playlist" in spotify_url
        ):  ## If a spotify playlist url is entered.
            playlist = await self.music.add_spotify_url(
                interaction.guild, spotify_url, interaction.channel, "playlist"
            )  ## Add the playlist to the queue.

            if (
                playlist is not None
            ):  ## If the playlist was added to the queue, respond.
                return await interaction.followup.send(
                    embed=await self.music.display_playlist(spotify_url)
                )  ## Display playlist info.
            else:
                return await interaction.followup.send(
                    embed=await self.music.invalid_url()
                )

        elif (
            "https://open.spotify.com/album" in spotify_url
        ):  ## If a spotify album url is entered.
            album = await self.music.add_spotify_url(
                interaction.guild, spotify_url, interaction.channel, "album"
            )  ## Add the album to the queue.

            if album is not None:  ## If the album was added to the queue, respond.
                return await interaction.followup.send(
                    embed=await self.music.display_album(spotify_url)
                )  ## Display album info.
            else:
                return await interaction.followup.send(
                    embed=await self.music.invalid_url()
                )

        elif (
            "https://open.spotify.com/track" in spotify_url
        ):  ## If a spotify track url is entered.
            track = await self.music.add_track(
                interaction.guild, spotify_url, interaction.channel
            )  ## Add the track to the queue, return tracks info.

            if track is not None:  ## If the track was added to the queue, respond.
                return await interaction.followup.send(
                    embed=await self.music.added_track(track)
                )
            else:
                return await interaction.followup.send(
                    embed=await self.music.invalid_url()
                )

        elif (
            "https://open.spotify.com/show" in spotify_url
            or "https://open.spotify.com/artist" in spotify_url
        ):  ## Spotify podcasts or artists are not supported.
            return await interaction.followup.send(
                embed=await self.music.podcasts_not_supported()
            )

        else:  ## Let the user know that only spotify urls work.
            return await interaction.followup.send(
                embed=await self.music.only_spotify_urls()
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
        # category = interaction.namespace.category
        not_found_choice = [
            app_commands.Choice(
                name="The only song you should listen to!",
                value="https://open.spotify.com/track/6ctO0maVSlFzn31wR0GpNg",
            )
        ]

        if current.strip() == "":
            return not_found_choice
        if "https://" in current.lower().strip():
            return [
                app_commands.Choice(
                    name="Spotify URL's are supported!",
                    value=current,
                )
            ]

        query_searched = await self.music.search_songs(
            current.lower(),
            category="track",
            limit=limit,
        )
        # if category == "track" or not category:
        formatted_track_results: list[
            SpotifyTrack
        ] = await self.music.format_query_search_results_track(
            search_results=query_searched, limit=limit
        )
        my_tracks = []

        for song in formatted_track_results:
            long_name = f"{song.name} - {song.artists} - {self.music.convert_ms(song.duration_ms)}"
            short_name = f"{song.name} - {self.music.convert_ms(song.duration_ms)}"

            my_tracks.append(
                app_commands.Choice(
                    name=long_name if len(long_name) < 100 else short_name,
                    value=song.external_urls,
                )
            )
        return my_tracks

        # DEPRECATED :: ALBUM SEARCHES.

        # elif category == "album":
        #     formatted_album_results: list[
        #         SpotifyAlbum
        #     ] = await self.music.format_query_search_results_album(
        #         search_results=query_searched, limit=limit
        #     )
        #     my_albums = []
        #     for album in formatted_album_results:
        #         long_name = (
        #             f"{album.name} - {album.artists} - tracks: {album.total_tracks}"
        #         )
        #         short_name = f"{album.name} - tracks: {album.total_tracks}"
        #         my_albums.append(
        #             app_commands.Choice(
        #                 name=long_name if len(long_name) < 100 else short_name,
        #                 value=album.external_urls,
        #             )
        #         )
        #     return my_albums


async def setup(bot):
    """
    Setup the cog.
    """
    await bot.add_cog(Music(bot))
