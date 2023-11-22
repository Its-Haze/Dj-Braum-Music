"""Credentials Loader"""
import os
from dataclasses import dataclass
from typing import Optional

import dotenv

dotenv.load_dotenv(dotenv_path=".env")  ## Load enviroment variables.


@dataclass
class EnvLoader:  # pylint:disable=too-many-instance-attributes
    """
    Class for loading environments
    """

    # Bot Info
    bot_token: Optional[str]
    vote_url: Optional[str]
    invite_url: Optional[str]
    support_server_url: Optional[str]

    # Lavalink Server Info
    lavalink_host: Optional[str]
    lavalink_port: Optional[str]
    lavalink_pass: Optional[str]

    # Spotify Credentials
    spotify_client_id: Optional[str]
    spotify_client_secret: Optional[str]
    spotify_trending_id: Optional[str]

    # Logging Channel
    logging_id: Optional[str]

    # Genius
    genius: Optional[str]

    @classmethod
    def load_env(cls):
        """
        Loads all environment variables
        """
        return cls(
            **{
                # Bot Info
                "bot_token": os.getenv("TOKEN"),
                "vote_url": os.getenv("VOTE_URL"),
                "invite_url": os.getenv("INVITE_URL"),
                "support_server_url": os.getenv("SUPPORT_SERVER_URL"),
                # Lavalink Server Info
                "lavalink_host": os.getenv("LAVAHOST"),
                "lavalink_port": os.getenv("LAVAPORT"),
                "lavalink_pass": os.getenv("LAVAPASS"),
                # Spotify Credentials
                "spotify_client_id": os.getenv("SPOTID"),
                "spotify_client_secret": os.getenv("SPOTCLIENT"),
                "spotify_trending_id": os.getenv("SPOTIFY_TRENDING_ID"),
                "logging_id": os.getenv("LOGID"),
                "genius": os.getenv("GENIUSKEY"),
            }
        )
