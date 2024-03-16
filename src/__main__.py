"""
- This file contains the main code for the Dj Braum Music Discord bot.
- It imports necessary modules and sets up the bot with the appropriate settings.
- It also defines event handlers for when the bot is ready,
- Joins a new guild, or leaves a guild.
- Defines a function to connect to a self-hosted Lavalink server for playing music.
"""

import asyncio
import logging as logger
import os
import typing

import discord
import wavelink
from discord.ext import commands

from logs.logger import setup_logging
from src.credentials.loader import EnvLoader
from src.utils.cogs_loader import cog_loader, cog_reloader
from src.utils.responses import Responses
from rich import inspect

env_loader = EnvLoader.load_env()
setup_logging()


class Bot(commands.Bot):
    def __init__(self) -> None:
        # intents = discord.Intents.all()
        # intents.message_content = True
        intents = discord.Intents.none()
        intents.guilds = True
        intents.voice_states = True

        command_prefix = "$$$"
        help_command = None
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="music | /play",
        )

        super().__init__(
            intents=intents,
            command_prefix=command_prefix,
            help_command=help_command,
            activity=activity,
        )

    async def setup_hook(self) -> None:
        """
        Setup hook, better than putting this in on_ready event.
        """
        logger.info("Setting up the Hook!")

        logger.info(
            "Using Lavalink host:port >> %s:%s",
            os.getenv("LAVAHOST"),
            os.getenv("LAVAPORT"),
        )
        try:
            # Use node_local for local testing.
            # node_local: wavelink.Node = wavelink.Node(
            #     uri=f"http://localhost:2333",
            #     password="youshallnotpass",
            # )
            node_docker: wavelink.Node = wavelink.Node(
                uri=f"http://{env_loader.lavalink_host}:{env_loader.lavalink_port}",
                password=env_loader.lavalink_pass,
            )

            await wavelink.Pool.connect(
                nodes=[node_docker],
                client=self,
            )
        except Exception as esx:
            logger.exception("Failed to connect to lavalink server")
            raise esx

    ### Bot Events
    async def on_ready(self):
        """This event runs when the bot is connected and ready to be used."""

        ## Create task to connect to the lavalink server.
        lines = "~~~" * 30

        logger.info(
            "\n%s\n%s is online in %s servers, and is ready to play music\n%s",
            lines,
            self.user,
            len(self.guilds),
            lines,
        )

    async def on_guild_join(self, guild: discord.Guild):
        """When braum joins a guild it adds that guild and a default server prefix to database"""
        join_msg = (
            "🎵 Dj Braum, your personal support is here! 🎶\n\n"
            "Ready to dive into endless tunes? Start by using my slash commands. Simply type ``/play`` followed by a song title, YouTube, or Spotify link (including songs, albums, and playlists) to get started.\n\n"
            "Looking for more? I've got plenty of commands to enhance your listening experience. Just type ``/`` and choose Dj Braum to explore all the possibilities.\n\n"
            "And there's more - as songs play, you'll see interactive buttons to control your music effortlessly. Don't miss out on the 🚀``For You`` feature! Activate Braum AI, and I'll keep the music going based on your session's history, ensuring there's never a dull moment. Your queued songs always get priority, seamlessly blending with AI recommendations for the perfect mix.\n"
            "Let's make every moment musical! 🎉"
        )
        logger.info(
            "Braum has joined %s, this guild has %s members",
            guild.name,
            guild.member_count,
        )

        # Logs that braum has joined a Guild to a logging channel.
        if env_loader.joined_left_channel_id:
            logging_channel = self.get_channel(int(env_loader.joined_left_channel_id))
            logger.info("Logging channel is %s", logging_channel)

            if isinstance(logging_channel, discord.channel.TextChannel):
                await logging_channel.send(
                    embed=await Responses.on_joining_guild(guild=guild)
                )  ## Send the log embed.
            else:
                logger.error(
                    "Was not able to send a logging message for [on_guild_join]."
                    "Logging channel is not a text channel."
                )
        inspect(guild)
        # First, try to send message to system channel
        if (
            guild.system_channel
            and guild.system_channel.permissions_for(guild.me).send_messages
        ):
            try:
                await guild.system_channel.send(join_msg)
                return  # If successful, we don't need to do anything else
            except Exception as exc:
                logger.exception("Failed to send message to system channel")
                raise exc

        # If we reach here, system channel is not available, let's find a suitable channel
        all_channels = [
            channel
            for channel in guild.text_channels
            if channel.permissions_for(guild.me).send_messages and not channel.is_nsfw()
        ]
        logger.info("All channels: %s", all_channels)

        if not all_channels:  # If there's no valid channels
            try:
                if not isinstance(guild.owner, discord.Member):
                    logger.error("Guild owner is not a member")
                    return

                await guild.owner.send(
                    "Thanks for inviting Braum.\n\n"
                    f"It seems like I can't send messages in {guild.name}.\n"
                    "Please give permissions to send messages in text channels.\n"
                    "Otherwise i am kinda useless :(\n\n\n"
                    "When i have permission to send messages in text channels, "
                    "try to use the ``!help`` command to see what i can do :)."
                )
            except discord.Forbidden:
                logger.error("Guild owner has disabled DM's" * 10)
            return  # After sending DM or logging error, exit function

        # If we reach here, there's at least one valid channel
        valid_channels = [
            channel
            for channel in all_channels
            if "general" in channel.name.lower() or "bot" in channel.name.lower()
        ]

        # Pick the first 'valid' channel, or if there's none, the first 'all' channel
        channel_to_send = valid_channels[0] if valid_channels else all_channels[0]
        await channel_to_send.send(join_msg)

    async def on_guild_remove(self, guild: discord.Guild):
        """
        Triggers when the Client leaves the Guild
        """
        logger.info(
            "Braum has left %s, this guild had %s members",
            guild.name,
            guild.member_count,
        )
        # Logs that braum has left a Guild
        logging_channel = self.get_channel(
            int(env_loader.joined_left_channel_id)
        )  ## Retrieve the logging channel.
        if not isinstance(logging_channel, discord.channel.TextChannel):
            logger.error("Logging channel is not a text channel")
            return

        await logging_channel.send(
            embed=await Responses.on_leaving_guild(guild=guild)
        )  ## Send the log embed.

    async def on_voice_state_update(
        self,
        member: discord.member.Member,
        before: discord.member.VoiceState,
        after: discord.member.VoiceState,
    ):
        """
        Triggers when the voicestate of the client changes
        - Joins a voice channel
        - Leaves a voice channel
        - When voice state updates.
        """
        if not isinstance(self.user, discord.ClientUser):
            logger.error("User is not a discord.ClientUser object")
            return

        if member.id == self.user.id:
            await self._handle_bot_voice_update(before, after, member.guild.id)
        else:
            await self._handle_user_voice_update(before, after, member.guild.id)

    async def _handle_bot_voice_update(self, before, after, guild_id: int):
        """
        Handles the voice state update of the bot.
        """
        # When the bot is disconnected from a voice channel
        if before.channel and not after.channel:
            player = await self.get_player(guild_id=guild_id)

            if player is not None:
                try:
                    await player.disconnect()
                except AttributeError as error:
                    logger.error(
                        "Player was unable to be disconnected when kicked out of a channel"
                    )
                    raise error

    async def _handle_user_voice_update(self, before, after, guild):
        """
        Handles the voice state update of a user.
        """
        # When someone disconnects from the voice channel.
        if before.channel and not after.channel:
            player = await self.get_player(guild)

            if player is None or player.channel.id != before.channel.id:
                return

            if all(
                member.bot for member in player.channel.members
            ):  # If there are no members in the vc, leave.
                player.queue.clear()  # Clear the queue.
                await player.stop()  # Stop the currently playing track.
                await player.disconnect()  # Leave the VC.

    async def get_player(self, guild_id: int):
        """
        Returns the player for the guild.
        """
        return wavelink.Pool().get_node().get_player(guild_id)


async def main():
    """main function"""

    async with Bot() as bot:
        await cog_loader(client=bot)

        @bot.command(name="sync")
        @commands.guild_only()
        @commands.is_owner()
        async def _sync(
            ctx: commands.Context,
            guilds: commands.Greedy[discord.Object],
            spec: typing.Optional[typing.Literal["~", "*", "^"]] = None,
        ) -> None:
            """
            A normal client.command for syncing app_commands.tree

            Works like:
            !sync -> global sync
            !sync ~ -> sync current guild
            !sync * -> copies all global app commands to current guild and syncs
            !sync ^ -> clears all commands from the current guild target and syncs (removes guild commands)
            !sync id_1 id_2 -> syncs guilds with id 1 and 2
            """
            if not guilds:
                if spec == "~":
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                elif spec == "*":
                    ctx.bot.tree.copy_global_to(guild=ctx.guild)
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                elif spec == "^":
                    ctx.bot.tree.clear_commands(guild=ctx.guild)
                    await ctx.bot.tree.sync(guild=ctx.guild)
                    synced = []
                else:
                    synced = await ctx.bot.tree.sync()

                await ctx.send(
                    f"Synced {len(synced)} commands "
                    f"{'globally' if spec is None else 'to the current guild.'}"
                )
                return

            ret = 0
            for guild in guilds:
                try:
                    await ctx.bot.tree.sync(guild=guild)
                except discord.HTTPException:
                    pass
                else:
                    ret += 1

            await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

        @bot.command(name="close", alias="shutdown")
        @commands.guild_only()
        @commands.is_owner()
        async def _close(
            ctx: commands.Context,
        ) -> None:
            """
            Shutdown command for Braum
            """
            await ctx.send("Bot will shutdown soon")
            await bot.close()

        @bot.command(name="reload", alias="cogs")
        @commands.guild_only()
        @commands.is_owner()
        async def _reload(
            ctx: commands.Context,
        ) -> None:
            """
            reloads cogs for Braum
            """
            await cog_reloader(client=bot)
            await ctx.send("Cogs are being reloaded")

        await bot.start(token=env_loader.bot_token)


if __name__ == "__main__":
    assert env_loader.bot_token is not None, "NO TOKEN IN .ENV file"
    asyncio.run(main())
