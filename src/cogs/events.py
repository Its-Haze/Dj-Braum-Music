"""Discord cog for all Wavelink events"""
import logging as logger

import wavelink
from discord.ext import commands

from src.credentials.loader import EnvLoader
from src.utils.responses import Responses


class MusicEvents(commands.Cog):
    """
    Cog that triggers on Music events for.
    """

    bot: commands.Bot

    def __init__(self, bot) -> None:
        self.bot = bot
        self.responses = Responses()
        self.env = EnvLoader.load_env()

    ### Lavalink Events
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """
        Fires when the lavalink server is connected
        """
        logger.info("Node: <{%s}> is ready!", node.id)
        logger.info("Node status = %s", node.status)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        """
        Fires when a track ends.
        """

        player = payload.player
        ctx = payload.player.reply  ## Retrieve the guild's channel id.

        logger.info("on_wavelink_track_end")

        # MOVED TO "VOICE_STATE_UPDATE"

        # if all(
        #     member.bot for member in player.channel.members
        # ):  ## If there are no members in the vc, leave.
        #     player.queue.clear()  ## Clear the queue.
        #     await player.stop()  ## Stop the currently playing track.
        #     await player.disconnect()  ## Leave the VC.
        #     await ctx.send(embed=await self.music.left_due_to_inactivity())

        if (
            not player.queue.is_empty and not player.loop and not player.queue_loop
        ):  ## If the queue is not empty and the loop is disabled, play the next track.
            next_track = await player.queue.get_wait()  ## Retrieve the queue.
            await player.play(next_track)

        elif (
            player.loop
        ):  ## If the loop is enabled, replay the track using the existing `looped_track` variable.
            await player.play(player.looped_track)

        elif (
            player.queue_loop
        ):  ## If the queue loop is enabled, replay the track using the existing `looped_track` var.
            player.queue.put(
                player.queue_looped_track
            )  ## Add the current track back to the queue.
            next_track = await player.queue.get_wait()  ## Retrieve the queue.
            await player.play(next_track)

        else:  ## Otherwise, stop the track.
            await player.stop()
            await ctx.send(
                embed=await self.responses.no_tracks_in_queue(), delete_after=15
            )  ## Let the user know that there are no more tracks in the queue.

        logging_channel = self.bot.get_channel(
            int(self.env.logging_id)
        )  ## Retrieve the logging channel.
        logger.info("Song ended because of reason: %s", payload.reason)
        await logging_channel.send(
            embed=await self.responses.log_track_finished(payload.track, player.guild)
        )  ## Send the log embed.

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, payload: wavelink.payloads.TrackEventPayload
    ):
        """
        Fires when a track starts.
        """
        logger.info("Event: on_wavelink_track_start")

        ctx = payload.player.reply  ## Retrieve the guild's channel id.

        if (
            payload.player.queue_loop
        ):  ## If the queue loop is enabled, assign queue_looped_track to the current track.
            payload.player.queue_looped_track = payload.track

        embed = await self.responses.display_track(
            payload.track, payload.player.guild, False, False
        )  ## Build the track info embed.
        await ctx.send(
            embed=embed, delete_after=60
        )  ## Send the embed when a track starts and delete it after 60 seconds.

        logging_channel = self.bot.get_channel(
            int(self.env.logging_id)
        )  ## Retrieve the logging channel.
        await logging_channel.send(
            embed=await self.responses.log_track_started(
                payload.track, payload.player.guild.id
            )
        )  ## Send the log embed.


async def setup(bot):
    """
    Setup the cog.
    """
    await bot.add_cog(MusicEvents(bot))
