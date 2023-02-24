"""Discord Cog for all Music commands"""
import asyncio
import re
import typing

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from logs import settings
from src.essentials.checks import in_same_channel, member_in_voicechannel
from src.utils.music_helper import MusicHelper
from src.utils.spotify_models import SpotifyTrack
from src.utils.views import TracksDropdownView

logger = settings.logging.getLogger(__name__)


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

        if interaction.guild is not None:
            # If user is in a VC and bot is not, join it.
            if interaction.guild.voice_client is None:
                await interaction.user.voice.channel.connect(
                    cls=wavelink.Player,
                    self_deaf=True,
                )
                return await interaction.followup.send(
                    embed=await self.music.in_vc(),
                )
            else:
                # If client is already connected to a voice channel
                return await interaction.followup.send(
                    embed=await self.music.already_in_vc(),
                )

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

    @app_commands.command(name="leave", description="Braum leaves your voice channel.")
    @in_same_channel()
    @member_in_voicechannel()
    async def leave(self, interaction: discord.Interaction):
        """
        /leave command
        """
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
        """
        /pause command
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
                # If something went wrong. reply the interaction

        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

    @app_commands.command(name="queue", description="Braum shows you the queue.")
    async def queue(self, interaction: discord.Interaction):
        """
        /queue command
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
        ):  ## If bot is in a VC, show the current queue.
            return await interaction.followup.send(
                embed=await self.music.show_queue(
                    await self.music.get_queue(interaction.guild), interaction.guild
                )
            )  ## Show the queue.

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

    @app_commands.command(name="shuffle", description="Braum shuffles the queue.")
    @in_same_channel()
    @member_in_voicechannel()
    async def shuffle(self, interaction: discord.Interaction):
        """
        /shuffle command
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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

    @app_commands.command(name="empty", description="Braum empties the queue.")
    @in_same_channel()
    @member_in_voicechannel()
    async def empty(self, interaction: discord.Interaction):
        """
        /empty command
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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

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

        # If something went wrong. reply the interaction
        return await interaction.followup.send(
            embed=await self.music.unexpected_response()
        )  # FIXME: raise an error that the error_handler cog can listen to.

    @app_commands.command(
        name="search", description="Braum searches Spotify for tracks!"
    )
    @app_commands.describe(search_query="The name of the song to search for.")
    async def search(self, interaction: discord.Interaction, *, search_query: str):
        """
        Search command for
        """
        await interaction.response.defer()
        print("in search command")

        embed, youtube_tracks = await self.music.display_search(
            search_query=search_query
        )

        view = TracksDropdownView(tracks=youtube_tracks)

        return await interaction.followup.send(
            embed=embed, view=view
        )  ## Display the invite embed.

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

        print(search)

        voice_client = await self.music.initalize_voice_client(interaction=interaction)

        ## If a URL is entered, respond.
        if re.match(self.music.url_regex, search):
            print("Its an URL")
            # self.url validates that it is a valid spotify URL
            return await self.url(interaction=interaction, spotify_url=search)
        print("I SHOULD NOT BE EXECUTED!")
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
        voice_client.reply = interaction.channel

        ## Modify the track info.
        final_track = await self.music.gather_track_info(
            track.title, track.author, track
        )

        ## If a track is playing, add it to the queue.
        if voice_client.is_playing():

            ## Use the modified track.
            await interaction.followup.send(
                embed=await self.music.added_track(final_track)
            )

            ## Add the modified track to the queue.
            return await voice_client.queue.put_wait(final_track)

        else:
            ## Otherwise, begin playing.

            ## Send an ephemeral as now playing is handled by on_track_start.
            msg = await interaction.followup.send(
                embed=await self.music.started_playing()
            )

            ## Set the loop value to false as we have just started playing.
            voice_client.loop = False

            ## Set the queue_loop value to false as we have just started playing.
            voice_client.queue_loop = False

            ## Used to store the currently playing track in case the user decides to loop.
            voice_client.looped_track = None

            ## Used to re-add the track in a queue loop.
            voice_client.queue_looped_track = None

            ## Play the modified track.
            await voice_client.play(final_track)

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
        print(spotify_url, "After the ? has been splitted off.")

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
        if "https://open.spotify.com" in current.lower().strip():
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
