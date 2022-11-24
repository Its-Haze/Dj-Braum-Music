import discord
import wavelink
from discord import app_commands
from discord.ext import commands
from errors import (
    MustBeInNsfwChannel,
    MustBeSameChannel,
    NotConnectedToVoice,
    PlayerNotConnected,
)


def voice_connected():
    """If voice is connected"""

    def predicate(ctx):
        try:
            ctx.author.voice.channel
            return True
        except AttributeError:
            raise NotConnectedToVoice("You are not connected to any voice channel.")

    return commands.check(predicate)


def player_connected():
    def predicate(ctx):
        player: wavelink.Player = ctx.bot.wavelink.get_player(
            ctx.guild.id, cls=wavelink.Player
        )

        if not player.is_connected:
            raise PlayerNotConnected("Dj Braum is not connected to any voice channel.")
        return True

    return commands.check(predicate)


def in_same_channel():
    def predicate(ctx):
        player: wavelink.Player = ctx.bot.wavelink.get_player(
            ctx.guild.id, cls=wavelink.Player
        )

        if not player.is_connected:
            raise PlayerNotConnected("Player is not connected to any voice channel.")

        try:
            return player.channel_id == ctx.author.voice.channel.id
        except:
            raise MustBeSameChannel(
                "Please join to the channel where bot is connected."
            )

    return commands.check(predicate)


def in_nsfw_channel():
    def predicate(ctx):
        if not ctx.guild:
            return
        if ctx.channel.is_nsfw():
            return True
        else:
            raise MustBeInNsfwChannel()

    return commands.check(predicate)


def allowed_to_connect():
    """Checks if the Client has permissions to join the current members voice channel"""

    def predicate(interaction: discord.Interaction):
        if (
            interaction.user.voice.channel.permissions_for(interaction.guild.me)
            == discord.Permissions.connect
        ):
            return True

    return app_commands.check(predicate)
