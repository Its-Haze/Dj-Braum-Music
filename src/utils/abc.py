"""
Music helper module.
Contains all responses and functions!
"""

from typing import Final, Optional

import discord
import lyricsgenius
import spotipy
from spotipy import Spotify, SpotifyClientCredentials

from src.credentials.loader import EnvLoader


class AbstractBaseClass:  # pylint:disable=too-many-instance-attributes
    """
    Abstract Base Class to be inherited by other classes such as Responses or Functions.
    """

    spotify: Spotify
    genius: lyricsgenius.Genius

    err_color: discord.Colour
    sucess_color: discord.Colour
    trending_uri: Optional[str]
    vote_url: Optional[str]
    invite_url: Optional[str]
    support_url: Optional[str]

    URL_REGEX: Final[str] = (
        r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    )
    URL_REGEX_HTTPS: Final[str] = (
        r"/https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#()?&//=]*)/"
    )

    def __init__(self):
        self.env = EnvLoader.load_env()

        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.env.spotify_client_id,
                client_secret=self.env.spotify_client_secret,
            )
        )

        self.genius = lyricsgenius.Genius(self.env.genius)  ## Used to retrieve lyrics.
        self.genius.verbose = False

        ## Removes [Chorus], [Intro] from the lyrics.
        self.genius.remove_section_headers = True
        self.genius.skip_non_songs = True

        self.err_color = discord.Colour.red()  ## Used for unsucesful embeds.
        self.sucess_color = discord.Colour.green()  ## Used for sucessful embeds.
        self.trending_uri = (
            self.env.spotify_trending_id  ## The playlist ID used to retrieve trending tracks.
        )
        self.vote_url = self.env.vote_url
        self.invite_url = self.env.invite_url
        self.support_url = self.env.support_server_url

    async def async_init(self):
        """Add any async initialization code here"""

    def __await__(self):
        return self.async_init().__await__()
