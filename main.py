"""Main file to run the Bot from."""
import asyncio
import logging.handlers
import typing

import discord
import wavelink
from discord.ext import commands

from logs import settings
from src.credentials.loader import EnvLoader
from src.utils.cogs_loader import cog_loader, cog_reloader
from src.utils.music_helper import MusicHelper

env_loader = EnvLoader.load_env()
logger = settings.logging.getLogger("bot")

## Default intents are enough as slash commands are used.
intents = discord.Intents.all()
client = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    activity=discord.Activity(
        type=discord.ActivityType.playing,
        name="music | /play",
    ),
)

## Slash commands.
# slash = app_commands.CommandTree(client)
# music = MusicHelper()
# --------------------------------------------
# @tasks.loop(minutes=5)
# async def update_status():  ## Updates the bot's status every 5 minutes.
#     """Updates the bot every five minutes"""
#     ## Retrieve all the bots servers.
#     server_count = client.guilds
#     await client.change_presence(
#         activity=discord.Activity(
#             type=discord.ActivityType.playing,
#             ## Update the status with bot's the guild count.
#             name=f"music | /play | Supporting {len(server_count)} Servers!",
#         )
#     )


async def connect_nodes():
    """Connects to the self hosted lavalink server"""
    logger.info("Connecting Nodes")
    await client.wait_until_ready()  ## Wait until the bot is ready.
    await wavelink.NodePool.create_node(
        bot=client,
        host=env_loader.lavalink_host,
        port=env_loader.lavalink_port,
        password=env_loader.lavalink_pass,
    )  ## Connect to the lavalink server.


### Bot Events
@client.event
async def on_ready():
    """This event runs when the bot is connected and ready to be used."""

    ## Create task to connect to the lavalink server.
    client.loop.create_task(connect_nodes())
    lines = "~~~" * 30
    logger.info(
        "\n%s\n%s is online in %s servers, and is ready to play music\n%s",
        lines,
        client.user,
        len(client.guilds),
        lines,
    )

    ## Start the update status loop.
    # await update_status.start()


@client.event
async def on_guild_join(guild: discord.Guild):
    """When braum joins a guild it adds that guild and a default server prefix to database"""
    join_msg = (
        "I Am Braum!, Your Personal Support!!\n\n"
        "To start playing music, just use my slash commands!\n"
        "``/play`` | Accepts song title's, spotify links (Songs, Albums, Artists)\n"
        "``/queue`` | Shows all the songs that are in queue\n"
        "``/remove`` | Removes a song from the queue based on their position (run /queue first)\n"
        "``/empty`` | Removes all songs from the queue\n"
        "``/loop`` | Loops the current playing song\n"
        "``/queueloop`` | Loops the whole queue\n"
        "``/shuffle`` | Shuffles the queue\n\n"
        "There are many more commands to choose from..\n"
        "Type ``/`` and select Dj Braum to list all of my commands"
    )

    # Logs that braum has joined a Guild
    logging_channel = client.get_channel(
        int(env_loader.logging_id)
    )  ## Retrieve the logging channel.
    await logging_channel.send(
        embed=await MusicHelper.on_joining_guild(guild=guild)
    )  ## Send the log embed.

    if (
        guild.system_channel
        and guild.system_channel.permissions_for(guild.me).send_messages
    ):
        await guild.system_channel.send(join_msg)
    else:
        all_channels = [
            channel
            for channel in guild.text_channels
            if channel.permissions_for(guild.me).send_messages and not channel.is_nsfw()
        ]
        if len(all_channels) == 0:
            try:
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
        else:
            valid_channels = [
                channel
                for channel in all_channels
                if "general" in channel.name.lower() or "bot" in channel.name.lower()
            ]
            if len(valid_channels) == 0:
                valid_channel = all_channels[0]
                await valid_channel.send(join_msg)
            else:
                valid_channel = valid_channels[0]
                await valid_channel.send(join_msg)


@client.event
async def on_guild_remove(guild: discord.Guild):
    """
    Triggers when the Client leaves the Guild
    """
    leave_msg = (
        "I am sorry, but i have to roam to another lane now..\n"
        "It was nice supporting you ❤️\n\n"
        "If you ever need me again, click on my profile and select ``Add to server``"
    )

    # Logs that braum has left a Guild
    logging_channel = client.get_channel(
        int(env_loader.logging_id)
    )  ## Retrieve the logging channel.
    await logging_channel.send(
        embed=await MusicHelper.on_leaving_guild(guild=guild)
    )  ## Send the log embed.

    try:
        await guild.owner.send(leave_msg)
    except discord.Forbidden:
        logger.exception("Guild owner has disabled DM's")


@client.event
async def on_voice_state_update(
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
    if member.id == client.user.id:
        if before.channel and after.channel is None:
            # When the bot is disconnected from a voice channel
            player: wavelink.Player = wavelink.NodePool.get_node().get_player(
                guild=member.guild
            )
            if player is not None:
                try:
                    await player.disconnect()
                except AttributeError as error:
                    logger.error(
                        "Player was unable to be disconnected when kicked out of a channel"
                    )
                    raise error
        elif before.channel is None and after.channel is not None:
            pass
            # When the bot connects to a voice channel
        else:
            pass
            # Bot state stays the same
    else:
        # If someone else joined/left
        if before.channel and after.channel is None:
            # When someone disconnects to the voice channel.
            player: wavelink.Player = wavelink.NodePool.get_node().get_player(
                guild=member.guild
            )
            if player is None:
                # If the player is not connected to any channel.
                return

            if player.channel.id != before.channel.id:
                # if the player is connected to another voice channel.
                return
            if all(
                member.bot for member in player.channel.members
            ):  # If there are no members in the vc, leave.
                player.queue.clear()  # Clear the queue.
                await player.stop()  # Stop the currently playing track.
                await player.disconnect()  # Leave the VC.

        elif before.channel is None and after.channel is not None:
            # When someone connects to the voice channel
            pass
        else:
            # When the members state stays the same.
            pass


## Sync slash comands.
@client.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
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


@client.command(name="close", alias="shutdown")
@commands.guild_only()
@commands.is_owner()
async def close(
    ctx: commands.Context,
) -> None:
    """
    Shutdown command for Braum
    """
    await ctx.send("Bot will shutdown soon")
    await client.close()

@client.command(name="reload", alias="cogs")
@commands.guild_only()
@commands.is_owner()
async def reload(
    ctx: commands.Context,
) -> None:
    """
    reloads cogs for Braum
    """
    await cog_reloader(client=client)
    await ctx.send("Cogs are being reloaded")


async def main():
    """main function"""

    await cog_loader(client=client)
    await client.start(token=env_loader.bot_token)


if __name__ == "__main__":
    assert env_loader.bot_token is not None, "NO TOKEN IN .ENV file"
    asyncio.run(main())
