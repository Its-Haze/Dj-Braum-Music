"""Discord Cog for all Music commands"""
import asyncio
import re

import discord
import spotipy
import wavelink
from discord import app_commands
from discord.ext import commands

from src.essentials.checks import (  # pylint:disable=import-error
    in_same_channel,
    member_in_voicechannel,
)
from src.utils.music_helper import MusicHelper  # pylint:disable=import-error


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot, music: MusicHelper) -> None:
        self.bot = bot
        self.music = music

    @app_commands.command(name="join", description="Braum joins your voice channel.")
    @in_same_channel()
    @member_in_voicechannel()
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if (
            not interaction.guild.voice_client
        ):  ## If user is in a VC and bot is not, join it.
            await interaction.user.voice.channel.connect(
                cls=wavelink.Player, self_deaf=True
            )
            return await interaction.followup.send(embed=await self.music.in_vc())

    @app_commands.command(name="leave", description="Braum leaves your voice channel.")
    @in_same_channel()
    @member_in_voicechannel()
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.guild.voice_client:  ## If bot is in a VC, leave it.
            await interaction.guild.voice_client.disconnect()
            return await interaction.followup.send(embed=await self.music.left_vc())

        else:  ## If bot is not in VC, respond.
            return await interaction.followup.send(
                embed=await self.music.already_left_vc()
            )

    @app_commands.command(
        name="pause", description="Braum pauses the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, pause the currently playing track.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the current player.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve currently playing track's info.

            if not player.is_paused():  ## If the current track is not paused, pause it.
                await interaction.guild.voice_client.pause()
                return await interaction.followup.send(
                    embed=await self.music.common_track_actions(track, "Paused")
                )

            else:  ## Otherwise, respond.
                return await interaction.followup.send(
                    embed=await self.music.already_paused(track)
                )

    @app_commands.command(
        name="resume", description="Braum resumes the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, resume the currently playing track.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the current player.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve currently playing track's info.

            if player.is_paused():  ## If the current track is paused, resume it.
                await interaction.guild.voice_client.resume()
                return await interaction.followup.send(
                    embed=await self.music.common_track_actions(track, "Resumed")
                )

            else:  ## Otherwise, respond.
                return await interaction.followup.send(
                    embed=await self.music.already_resumed(track)
                )

    @app_commands.command(
        name="stop", description="Braum stops the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, stop the currently playing track.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve currently playing track's info.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the current player.
            await interaction.followup.send(
                embed=await self.music.common_track_actions(track, "Stopped")
            )

            return (
                await interaction.guild.voice_client.stop()
            )  ## Stop the track after sending the embed.

    @app_commands.command(
        name="skip", description="Braum skips the currently playing track."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, skip the currently playing track.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve currently playing track's info.
            await interaction.followup.send(
                embed=await self.music.common_track_actions(track, "Skipped")
            )

            return (
                await interaction.guild.voice_client.stop()
            )  ## Skip the track after sending the embed.

    @app_commands.command(name="queue", description="Braum shows you the queue.")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, show the current queue.
            return await interaction.followup.send(
                embed=await self.music.show_queue(
                    await self.music.get_queue(interaction.guild), interaction.guild
                )
            )  ## Show the queue.

    @app_commands.command(name="shuffle", description="Braum shuffles the queue.")
    @in_same_channel()
    @member_in_voicechannel()
    async def shuffle(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, shuffle the current queue.
            queue = await self.music.get_queue(
                interaction.guild
            )  ## Retrieve the current queue.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve the current track.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the current player.

            if len(queue) == 0:  ## If there are no tracks in the queue, respond.
                return await interaction.followup.send(
                    embed=await self.music.empty_queue()
                )

            else:
                await self.music.shuffle(queue)  ## Shuffle the queue.
                if (
                    not player.queue_loop
                ):  ## If the queue loop is not enabled, place the current track at the end of the queue.
                    player.queue.put(
                        track
                    )  ## Add the current track to the end of the queue.
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

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, resume the currently playing track.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve currently playing track's info.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the current player.

            return await interaction.followup.send(
                embed=await self.music.display_track(
                    track, interaction.guild, False, True
                )
            )

    @app_commands.command(name="volume", description="Braum adjusts the volume.")
    @app_commands.describe(
        volume_percentage="The percentage to set the volume to. Accepted range: 0 to 100."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def volume(self, interaction: discord.Interaction, *, volume_percentage: int):
        """Sets the volume %"""
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, resume the currently playing track.

            if volume_percentage > 100:  ## Volume cannot be greater than 100%.
                return await interaction.followup.send(
                    embed=await self.music.volume_too_high()
                )

            else:
                await self.music.modify_volume(
                    interaction.guild, volume_percentage
                )  ## Adjust the volume to the specified percentage.
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
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, try to remove the requested track.
            remove_msg = await self.music.queue_track_actions(
                await self.music.get_queue(interaction.guild), track_index, "Removed"
            )  ## Store the info beforehand as the track will be removed.

            if remove_msg != False:  ## If the track exists in the queue, respond.
                await self.music.remove_track(
                    await self.music.get_queue(interaction.guild), track_index
                )  ## Remove the track.
                return await interaction.followup.send(embed=remove_msg)

            else:  ## If the track was not removed, respond.
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
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, try to remove the requested track.
            skipped_msg = await self.music.queue_track_actions(
                await self.music.get_queue(interaction.guild), track_index, "Skipped to"
            )  ## Store the info beforehand as the track will be removed.

            if skipped_msg != False:  ## If the track exists in the queue, respond.
                await self.music.skipto_track(
                    interaction.guild, track_index
                )  ## Skip to the requested track.
                await interaction.guild.voice_client.stop()  ## Stop the currently playing track.
                return await interaction.followup.send(embed=skipped_msg)

            else:  ## If the track was not skipped, respond.
                return await interaction.followup.send(
                    embed=await self.music.track_not_in_queue()
                )

    @app_commands.command(name="empty", description="Braum empties the queue.")
    @in_same_channel()
    @member_in_voicechannel()
    async def empty(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif interaction.guild.voice_client:  ## If bot is in a VC, empty the queue.
            queue = await self.music.get_queue(
                interaction.guild
            )  ## Retrieve the current queue.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the player.

            if len(queue) == 0:  ## If there are no tracks in the queue, respond.
                return await interaction.followup.send(
                    embed=await self.music.empty_queue()
                )

            else:  ## Otherwise, clear the queue.
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
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, enable/disable the loop.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the player.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve the currently playing track.

            if not player.loop:  ## If the loop is not enabled, enable it.
                await interaction.followup.send(
                    embed=await self.music.common_track_actions(track, "Looping")
                )  ## Send the msg before enabling the loop to avoid confusing embed titles.

                player.loop = True
                player.looped_track = track  ## Store the currently playing track so that it can be looped.
                return

            else:  ## If the loop is already enabled, disable it.
                player.loop = False
                return await interaction.followup.send(
                    embed=await self.music.common_track_actions(
                        track, "Stopped looping"
                    )
                )

    @app_commands.command(
        name="queueloop", description="Braum loops the current queue."
    )
    @in_same_channel()
    @member_in_voicechannel()
    async def queueloop(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.music.get_player(
            interaction.guild
        ) or not await self.music.get_track(
            interaction.guild
        ):  ## If nothing is playing, respond.
            return await interaction.followup.send(
                embed=await self.music.nothing_is_playing()
            )

        elif (
            interaction.guild.voice_client
        ):  ## If bot is in a VC, enable/disable the queue loop.
            player = await self.music.get_player(
                interaction.guild
            )  ## Retrieve the player.
            track = await self.music.get_track(
                interaction.guild
            )  ## Retrieve the currently playing track.
            queue = await self.music.get_queue(
                interaction.guild
            )  ## Retrieve the current queue.

            if (
                len(queue) < 1 and not player.queue_loop
            ):  ## If there is less than 1 track in the queue and there is not a current queueloop, respond.
                return await interaction.followup.send(
                    embed=await self.music.less_than_1_track()
                )

            if not player.queue_loop:  ## If the queue loop is not enabled, enable it.
                await interaction.followup.send(
                    embed=await self.music.common_track_actions(
                        None, "Looping the queue"
                    )
                )  ## Send the msg before enabling the queue loop to avoid confusing embed titles.

                player.queue_loop = True
                player.queue_looped_track = track  ## Add the currently playing track.
                return

            else:  ## If the queue loop is already enabled, disable it.
                player.queue_loop = False
                player.queue_looped_track = (
                    None  ## Prevents the current track from constantly being assigned.
                )

                return await interaction.followup.send(
                    embed=await self.music.common_track_actions(
                        None, "Stopped looping the queue"
                    )
                )

    @app_commands.command(name="play", description="Braum plays your desired song.")
    @app_commands.describe(spotify="Enter a spotify song Name, Link, Album, Playlist")
    @in_same_channel()  # if member is in the same voice channel as the client.
    @member_in_voicechannel()  # If member is connected to a voice channel.
    async def play(self, interaction: discord.Interaction, *, spotify: str):
        """
        Play command
        Accepts normal text querys
        If link is found, it will run /url and validate spotify urls
        """
        await interaction.response.defer()

        if not interaction.guild.voice_client:  ## If user is in a VC, join it.
            vc: wavelink.Player = await interaction.user.voice.channel.connect(
                cls=wavelink.Player, self_deaf=True
            )
        else:
            vc: wavelink.Player = (
                interaction.guild.voice_client
            )  ## Otherwise, initalize voice_client.

        if re.match(self.music.url_regex, spotify):  ## If a URL is entered, respond.
            # self.url validates that it is a valid spotify URL
            return await self.url(interaction=interaction, spotify_url=spotify)

        try:
            track = await wavelink.YouTubeMusicTrack.search(
                spotify, return_first=True
            )  ## Search for a song.
        except (
            IndexError,
            TypeError,
        ):  ## If no results are found or an invalid query was entered, respond.
            return await interaction.followup.send(
                embed=await self.music.no_track_results()
            )

        vc.reply = (
            interaction.channel
        )  ## Store the channel id to be used in track_start.

        final_track = await self.music.gather_track_info(
            track.title, track.author, track
        )  ## Modify the track info.

        if vc.is_playing():  ## If a track is playing, add it to the queue.
            await interaction.followup.send(
                embed=await self.music.added_track(final_track)
            )  ## Use the modified track.

            return await vc.queue.put_wait(
                final_track
            )  ## Add the modified track to the queue.

        else:  ## Otherwise, begin playing.
            msg = await interaction.followup.send(
                embed=await self.music.started_playing()
            )  ## Send an ephemeral as now playing is handled by on_track_start.

            vc.loop = (
                False  ## Set the loop value to false as we have just started playing.
            )
            vc.queue_loop = False  ## Set the queue_loop value to false as we have just started playing.
            vc.looped_track = None  ## Used to store the currently playing track in case the user decides to loop.
            vc.queue_looped_track = None  ## Used to re-add the track in a queue loop.

            await vc.play(final_track)  ## Play the modified track.
            await asyncio.sleep(5)
            return await interaction.followup.delete_message(
                msg.id
            )  ## Delete the message after 5 seconds.

    async def url(self, interaction: discord.Interaction, *, spotify_url: str):
        """
        Validates the URL to check for open.spotify links only
        Adds the spotify song/album/playlist to the queue
        """

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

    @play.autocomplete("spotify")
    async def autocomplete_callback(
        self,
        interaction: discord.Interaction,
        current: str,  # pylint:disable=unused-argument
    ):
        """
        Auto suggestion for queryng spotify
        clickable options appear and spotify link the linked value
        """
        if current != "":
            query_searched = await self.music.search_songs(current, limit=5)

            formatted_result = await self.music.format_query_search_results(
                query_searched
            )

            return [
                app_commands.Choice(
                    name=f"{song['song_name']} - {song['artists']} - {self.music.convert_ms(song['duration'])}",
                    value=song["external_url"],  # This is a spotify track link.
                )
                for song in formatted_result
            ]


async def setup(bot):
    music = MusicHelper()
    await bot.add_cog(Music(bot, music))
