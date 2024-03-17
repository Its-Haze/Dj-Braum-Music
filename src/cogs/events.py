"""Discord cog for all Wavelink events"""

import logging as logger
import discord

import wavelink
from discord.ext import commands

from src.credentials.loader import EnvLoader
from src.utils.responses import Responses

from src.utils.views import PlayerControlsView


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
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """
        Fires when the lavalink server is connected
        """
        logger.info("Node: <{%s}> is ready!", payload.node.identifier)
        logger.info("Node status = %s", payload.node.status)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """
        Fires when a track ends.
        """

        player = payload.player
        track = payload.track

        if hasattr(player, "custom_queue"):
            custom_queue: wavelink.Queue = player.custom_queue
            custom_queue.history.put(track)

        logger.info("Track ended because of reason: %s", payload.reason)

        # Reset filters after all songs in the queue have been played.
        if hasattr(player, "nightcore") and player.nightcore:
            player.nightcore = False
            filters: wavelink.Filters = player.filters
            filters.timescale.reset()
            await player.set_filters(filters)

        # Cleanup the "now playing" message that was sent in "track_start" event.
        if hasattr(player, "now_playing_message") and player.now_playing_message:
            try:
                await player.now_playing_message.delete()
            except discord.errors.NotFound:
                logger.warning("Tried to delete a message that no longer exists.")
            player.now_playing_message = None

        logging_channel = self.bot.get_channel(
            int(self.env.logging_id)
        )  ## Retrieve the logging channel.
        await logging_channel.send(
            embed=await self.responses.log_track_finished(payload.track, player.guild)
        )  ## Send the log embed.

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self,
        payload: wavelink.TrackStartEventPayload,
    ) -> None:
        """
        Fires when a track starts.
        """

        track = payload.track

        logger.info(
            "Track successfully started title=(%s), author=(%s), source=(%s)",
            track.title,
            track.author,
            track.source,
        )
        logger.debug("Track started with payload: %s", track.raw_data)

        player: wavelink.Player = payload.player

        if not player:
            logger.error(
                "Player not found, when starting track %s",
                payload,
                exc_info=True,
            )
            return

        embed = await self.responses.display_track(
            player,
            payload.track,
        )  ## Build the track info embed.

        if hasattr(player, "reply"):
            view = PlayerControlsView(responses=self.responses)

            view.previous.disabled = False
            if hasattr(player, "custom_queue"):
                if player.custom_queue.history.is_empty:
                    view.previous.disabled = True

            view.for_you.style = discord.ButtonStyle.grey
            view.for_you.emoji = "🚀"

            if player.autoplay == wavelink.AutoPlayMode.enabled:
                view.for_you.style = discord.ButtonStyle.green
                view.for_you.emoji = "<a:I_Check:812904249175834644>"

            reply: discord.interactions.InteractionChannel = player.reply

            try:
                message = await reply.send(
                    embed=embed,
                    view=view,
                    delete_after=track.length / 1000,
                )

                player.now_playing_message = message
            except discord.errors.Forbidden:
                logger.error(
                    "Tried to send a message to a channel where the bot has no permissions.\n Buttons might now show correctly.."
                )

        logging_channel = self.bot.get_channel(
            int(self.env.logging_id)
        )  ## Retrieve the logging channel.

        await logging_channel.send(
            embed=await self.responses.log_track_started(
                payload.track, payload.player.guild
            )
        )  ## Send the log embed.


async def setup(bot):
    """
    Setup the cog.
    """
    await bot.add_cog(MusicEvents(bot))
