"""Discord cog for all Wavelink events"""
import wavelink
from discord.ext import commands

from logs import settings  # pylint:disable=import-error
from src.credentials.loader import EnvLoader  # pylint:disable=import-error
from src.utils.music_helper import MusicHelper  # pylint:disable=import-error

logger = settings.logging.getLogger(__name__)


class MusicEvents(commands.Cog):
    """
    Cog that triggers on Music events for.
    """

    bot: commands.Bot
    music: MusicHelper
    env: EnvLoader

    def __init__(self, bot, music, env) -> None:
        self.bot = bot
        self.music = music
        self.env = env

    ### Lavalink Events
    @commands.Cog.listener()
    async def on_wavelink_node_ready(
        self, node: wavelink.Node
    ):  ## Fires when the lavalink server is connected
        logger.info(f"Node: <{node.identifier}> is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: wavelink.Player, track, reason
    ):  ## Fires when a track ends.
        ctx = player.reply  ## Retrieve the guild's channel id.

        if all(
            member.bot for member in player.channel.members
        ):  ## If there are no members in the vc, leave.
            player.queue.clear()  ## Clear the queue.
            await player.stop()  ## Stop the currently playing track.
            await player.disconnect()  ## Leave the VC.
            await ctx.send(embed=await self.music.left_due_to_inactivity())

        elif (
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
                embed=await self.music.no_tracks_in_queue(), delete_after=15
            )  ## Let the user know that there are no more tracks in the queue.

        logging_channel = self.bot.get_channel(
            int(self.env.logging_id)
        )  ## Retrieve the logging channel.
        await logging_channel.send(
            embed=await self.music.log_track_finished(track, player.guild)
        )  ## Send the log embed.

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, player: wavelink.Player, track
    ):  ## Fires when a track starts.
        ctx = player.reply  ## Retrieve the guild's channel id.

        if (
            player.queue_loop
        ):  ## If the queue loop is enabled, assign queue_looped_track to the current track.
            player.queue_looped_track = track

        embed = await self.music.display_track(
            track, player.guild, False, False
        )  ## Build the track info embed.
        await ctx.send(
            embed=embed, delete_after=60
        )  ## Send the embed when a track starts and delete it after 60 seconds.

        logging_channel = self.bot.get_channel(
            int(self.env.logging_id)
        )  ## Retrieve the logging channel.
        await logging_channel.send(
            embed=await self.music.log_track_started(track, player.guild)
        )  ## Send the log embed.


async def setup(bot):
    env = EnvLoader.load_env()
    music = MusicHelper()
    await bot.add_cog(MusicEvents(bot, music, env))
