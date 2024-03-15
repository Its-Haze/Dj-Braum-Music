import logging as logger

from discord.app_commands import CheckFailure


class NotConnectedToVoice(CheckFailure):
    """User not connected to any voice channel"""

    pass


class PlayerNotConnected(CheckFailure):
    """Player not connected"""

    pass


class MustBeSameChannel(CheckFailure):
    """Player and user not in same channel"""

    pass


class MustBeInNsfwChannel(CheckFailure):
    """User not in Nsfw channel"""

    pass


class MissingConnectionPermissions(CheckFailure):
    """User is not allowed to connect to the voice channel"""

    pass
