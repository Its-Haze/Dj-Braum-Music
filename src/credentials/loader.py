"""Credentials Loader"""
import os
from dataclasses import dataclass

import dotenv

dotenv.load_dotenv(dotenv_path="src/credentials/.env")  ## Load enviroment variables.


@dataclass
class EnvLoader:
    """
    Class for loading environments
    """

    # Bot Info
    bot_token: str | None
    vote_url: str | None
    invite_url: str | None
    support_server_url: str | None

    # Lavalink Server Info
    lavalink_host: str | None
    lavalink_port: str | None
    lavalink_pass: str | None

    # Spotify Credentials
    spotify_client_id: str | None
    spotify_client_secret: str | None
    spotify_trending_id: str | None

    # Logging Channel
    logging_id: str | None

    # Genius
    genius: str | None

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
                "genius": os.getenv("GENIUSKEY")
            }
        )
