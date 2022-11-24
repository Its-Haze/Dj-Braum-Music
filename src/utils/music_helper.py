import random
from time import gmtime, strftime
from typing import Literal

import discord
import lyricsgenius
import spotipy
import wavelink
from spotipy import Spotify, SpotifyClientCredentials, SpotifyException

from src.credentials.loader import EnvLoader
from src.utils.responses import Responses


class MusicHelper(Responses):
    """
    inherits from Responses --> Functions --> ABC

    This class is the one you should instanciate when using it in cogs
    """

    discord: discord
    wavelink: wavelink
    spotify: Spotify
    spot_exception: SpotifyException
    genius: lyricsgenius.Genius
    err_color: Literal[16711680]
    sucess_color: Literal[3403400]
    trending_uri: str | None
    vote_url: str | None
    invite_url: str | None
    support_url: str | None
    strftime: strftime
    gmtime: gmtime
    random: random
    url_regex: Literal

    def __init__(self):
        self.env = EnvLoader.load_env()

        self.discord = discord
        self.wavelink = wavelink

        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.env.spotify_client_id,
                client_secret=self.env.spotify_client_secret,
            )
        )
        self.spot_exception = (
            spotipy.client.SpotifyException
        )  ## Used to identify incorrect spotify results.

        self.genius = lyricsgenius.Genius(self.env.genius)  ## Used to retrieve lyrics.
        self.genius.verbose = False

        ## Removes [Chorus], [Intro] from the lyrics.
        self.genius.remove_section_headers = True
        self.genius.skip_non_songs = True

        self.err_color = 0xFF0000  ## Used for unsucesful embeds.
        self.sucess_color = 0x33EE88  ## Used for sucessful embeds.
        self.trending_uri = (
            self.env.spotify_trending_id  ## The playlist ID used to retrieve trending tracks.
        )
        self.vote_url = self.env.vote_url
        self.invite_url = self.env.invite_url
        self.support_url = self.env.support_server_url
        self.strftime = strftime
        self.gmtime = gmtime
        self.random = random
        self.url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    def __await__(self):
        return self.async_init().__await__()
