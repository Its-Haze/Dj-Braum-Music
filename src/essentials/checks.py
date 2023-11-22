"""
This module holds all appcommand.checks.
They will raise an error if condition is not met.

They will be used as decorators for common commands.
"""
import logging as logger

import discord
import rich
import wavelink
from discord import app_commands
from discord.ext import commands

from src.essentials.errors import (
    MustBeInNsfwChannel,
    MustBeSameChannel,
    NotConnectedToVoice,
    PlayerNotConnected,
)


def member_in_voicechannel():
    """If member is connected to a voice chat"""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            logger.info("%s is not a member", interaction.user)
            return False

        logger.info("Checking if %s is connected to a voice channel", interaction.user)
        if not interaction.user.voice:  ## If user is not in a VC, respond.
            logger.info("%s is not connected to a voice channel", interaction.user)
            raise NotConnectedToVoice("You are not connected to a voice channel!")
        return True

    return app_commands.check(predicate)


def player_connected():
    """
    If Dj Braum is connected to a voice channel.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            logger.info("%s is not a member", interaction.user)
            return False

        logger.info("Checking if Dj Braum is connected to a voice channel")
        player: wavelink.Player = wavelink.NodePool.get_node().get_player(
            interaction.guild.id
        )

        if not player.is_connected:
            logger.info("Dj Braum is not connected to any voice channel")
            raise PlayerNotConnected("Dj Braum is not connected to any voice channel.")
        logger.info("Dj Braum is connected to a voice channel")
        return True

    return app_commands.check(predicate)


def in_same_channel():
    """
    If the user is in the same voice channel as Dj Braum.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        logger.debug(
            "If the user is in the same voice channel as Dj Braum %s", interaction
        )

        if not isinstance(interaction.user, discord.Member):
            logger.info("%s is not a member", interaction.user)
            return False

        if not isinstance(interaction.user.voice, discord.VoiceState):
            logger.info("%s is not connected to a voice channel", interaction.user)
            return False
        if not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
            logger.info("%s is not connected to a voice channel", interaction.user)
            return False

        logger.info("Checking if user is in the same voice channel as Dj Braum")
        player = wavelink.NodePool.get_node().get_player(interaction.guild.id)
        if not isinstance(player, wavelink.Player):
            logger.info(
                "Dj Braum is not connected to any voice channel, let's connect him"
            )
            return True

        try:
            if player.channel.id != interaction.user.voice.channel.id:
                logger.info("User is not in the same voice channel as Dj Braum")
                raise MustBeSameChannel(
                    "Please join to the channel where the bot is connected"
                )
        except AttributeError as exc:
            logger.exception("Player is not connected to any voice channel")
            raise PlayerNotConnected(
                "Dj Braum is not connected to any voice channel."
            ) from exc
        logger.info("User is in the same voice channel as Dj Braum")
        return True

    return app_commands.check(predicate)


def in_nsfw_channel():
    """
    If the user is in a nsfw channel.
    """

    def predicate(ctx) -> bool:
        logger.debug("Checking if user is in a nsfw channel %s", ctx)
        if not ctx.guild:
            logger.info("Command is not used in a guild")
            return False
        if ctx.channel.is_nsfw():
            return True
        else:
            logger.info("User is not in a nsfw channel")
            raise MustBeInNsfwChannel(
                "You must be in a nsfw channel to use this command"
            )

    return commands.check(predicate)


def allowed_to_connect():
    """Checks if the Client has permissions to join the current members voice channel"""

    def predicate(interaction: discord.Interaction):
        """Checks if the Client has permissions to join the current members voice channel"""
        logger.debug(
            "Checking if client has permissions to join the current members voice channel. %s",
            interaction,
        )
        if not isinstance(interaction.user, discord.Member):
            logger.info("%s is not a member", interaction.user)
            return False
        if not isinstance(interaction.guild, discord.Guild):
            logger.info("%s is not a guild", interaction.guild)
            return False
        if not isinstance(interaction.user.voice, discord.VoiceState):
            logger.info("%s is not connected to a voice channel", interaction.user)
            return False
        if not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
            logger.info("%s is not connected to a voice channel", interaction.user)
            return False

        if (
            interaction.user.voice.channel.permissions_for(interaction.guild.me)
            == discord.Permissions.connect
        ):
            logger.info(
                "Client has permissions to join the current members voice channel"
            )
            return True

    return app_commands.check(predicate)
