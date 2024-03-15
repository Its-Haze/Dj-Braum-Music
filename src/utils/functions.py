"""
This file contains basic functionalities for AbstractBaseClass and Responses.
"""

import logging as logger
import random
from time import gmtime, strftime
from typing import Any, Optional

import discord
import wavelink
from lyricsgenius.types import Song

from spotipy import SpotifyException

from src.utils.abc import AbstractBaseClass
from src.utils.spotify_models import SpotifyTrack


class Functions(AbstractBaseClass):  # pylint:disable=too-many-public-methods
    """
    Contains all functions used in the music cog.
    Any functionality that is used more than once should be placed here.
    """

    async def get_track(self, guild: discord.Guild) -> wavelink.Playable | None:
        """Returns info about the current track."""
        player = await self.get_player(guild=guild)
        if player is None:
            logger.warning("Ran 'get_track' but got an empty player back.")
            return None
        return player.current

    async def get_player(self, guild: discord.Guild) -> wavelink.Player | None:
        """Returns player info."""
        # return wavelink.NodePool.get_node().get_player(guild.id)
        return wavelink.Pool.get_node().get_player(guild.id)

    async def get_queue(self, guild: discord.Guild) -> wavelink.Queue:
        """Returns the queue."""

        player = await self.get_player(guild=guild)
        if player is None:
            logger.error("Player not found!: method get_queue")
            return None
        return player.queue

    async def shuffle(self, queue: wavelink.Queue) -> wavelink.Queue:
        """Shuffles the queue."""
        return random.shuffle(queue)

    async def modify_volume(self, guild: discord.Guild, volume: int) -> None:
        """
        Modifies the volume of the audio player for a given guild.

        Args:
            guild (discord.Guild): The guild for which to modify the volume.
            volume (int): The new volume level to set.

        Returns:
            None.
        """
        player = await self.get_player(guild)

        if isinstance(player, wavelink.Player):
            await player.set_volume(volume)

        return None

    async def remove_track(self, queue: wavelink.Queue, track_index: int) -> None:
        """
        Remove the track from the queue. 1 is subtracted as the queue starts from 0.
        """
        del queue[track_index - 1]

    async def skipto_track(
        self,
        guild: discord.Guild,
        track_index: int,
    ) -> None:
        """
        Place a requested track at the front of the queue and remove it from the queue.
        """
        player = await self.get_player(guild)  ## Retrieve the player.
        queue = await self.get_queue(guild)  ## Retrieve the queue.
        if isinstance(player, wavelink.Player) and isinstance(queue, wavelink.Queue):
            player.queue.put_at_front(
                queue[track_index - 1]
            )  ## Place the requested track at the front of the queue.
            del queue[track_index]  ## Remove the track from the queue.

    async def get_new_releases(self) -> Any | None:
        """
        Returns 10 newly released tracks from spotify.
        """
        return self.spotify.new_releases(limit=10)

    async def get_trending(self) -> Any | None:
        """
        Returns 10 tracks in the trending playlist.
        """
        return self.spotify.playlist_tracks(self.trending_uri, limit=10)

    async def playlist_info(
        self,
        playlist_url: str,
    ) -> Any | None:
        """
        Returns info about the playlist.
        """
        playlist_id = playlist_url.split("/")[-1].split("?")[
            0
        ]  ## Returns only the playlist ID.
        return self.spotify.playlist(playlist_id)

    async def album_info(
        self,
        album_url: str,
    ) -> Any | None:
        """
        Returns info about the album.
        """
        album_id = album_url.split("/")[-1].split("?")[0]  ## Returns only the album ID.
        return self.spotify.album(album_id)

    async def search_spotify_track(self, url: str) -> wavelink.Playable | None:
        """
        Search for a track on Spotify based on a given URL.
        If no track is found, return None.

        Defaults to YouTube for non URL based queries.
        """
        # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
        # LavaSrc needs to be configured to use Spotify API. Check application.yml for more details.
        # Defaults to YouTube for non URL based queries...
        tracks = await wavelink.Playable.search(url)
        if not tracks:
            logger.warning("User used an invalid track URL for spotify.%s", url)
            return None
        track = list(tracks)[0]
        return track

    async def get_lyrics(
        self,
        track: wavelink.Playable,
    ) -> Optional[Song]:
        """
        Returns the lyrics of a song. If no lyrics are found, return None.
        Expecting track to be of source "spotify" only.
        """
        self.genius.verbose = True
        lyrics = self.genius.search_song(track.title, artist=track.author)

        if not isinstance(lyrics, Song):
            logger.debug(
                "Lyrics not found! track=(%s), artist=(%s)", track.title, track.author
            )
            return None

        logger.info("Lyrics found! track=(%s), artist=(%s)", track.title, track.author)
        return lyrics

    async def search_songs(
        self, search_query: str, category: str = "track", limit: int = 10
    ):
        """
        Search for songs on Spotify based on a given query.

        Args:
            search_query (str): The search query to use.
            category (str, optional): The category of the search. Defaults to "track".
            limit (int, optional): The maximum number of results to return. Defaults to 10.

        Returns:
            dict: A dictionary containing the search results.
        """
        search_results = self.spotify.search(
            q=f"{search_query}", limit=limit, type=category
        )
        return search_results

    async def format_search_results(self, search_results):
        """
        Formats the search results obtained from Spotify API into a string that can be displayed to the user.

        Args:
        - search_results (dict): A dictionary containing the search results obtained from Spotify API.

        Returns:
        - str: A formatted string containing the search results.
        """
        all_tracks = [
            (
                f"**{i}.** [{track['name']}]({track['external_urls']['spotify']}) - "
                f"[{track['album']['name']}]({track['album']['external_urls']['spotify']}) - "
                f"[{track['artists'][0]['name']}]({track['artists'][0]['external_urls']['spotify']})"
            )
            for i, track in enumerate(search_results["tracks"]["items"], start=1)
        ]
        return "\n".join(all_tracks)

    async def format_query_search_results_track(
        self,
        search_results: dict,
        limit: int = 5,
    ) -> list[SpotifyTrack]:
        """
        Formats and sorts Spotify track search results.

        Args:
            search_results (dict): The search results returned by the Spotify API.
            limit (int, optional): The maximum number of tracks to return. Defaults to 5.

        Returns:
            list[SpotifyTrack]: A list of SpotifyTrack objects sorted by popularity in descending order.
        """
        formatted_and_sorted_tracks = SpotifyTrack.from_search_results(
            search_result=search_results["tracks"]["items"][:limit],
        )

        return self.sort_spotify_tracks_by_popularity(formatted_and_sorted_tracks)

    def sort_spotify_tracks_by_popularity(
        self, formatted_and_sorted_tracks: list[SpotifyTrack]
    ) -> list[SpotifyTrack]:
        return sorted(
            formatted_and_sorted_tracks,
            key=lambda fl: fl.popularity,
            reverse=True,
        )

    # async def format_query_search_results_album(
    #     self,
    #     search_results: dict,
    #     limit: int = 5,
    # ) -> list[SpotifyAlbum]:
    #     """
    #     Returns a list of spotify Albums
    #     """
    #     formatted_and_sorted_albums = SpotifyAlbum.from_search_results(
    #         search_result=search_results.get("albums").get("items")[:limit],
    #     )

    #     return sorted(
    #         formatted_and_sorted_albums,
    #         key=lambda fl: fl.total_tracks,
    #         reverse=True,
    #     )

    def convert_ms(self, milliseconds: int) -> str:
        """
        Converts milliseconds to a string in the format of 'minutes:seconds'.

        Args:
        - milliseconds (int): The number of milliseconds to convert.

        Returns:
        - str: The converted time in the format of 'minutes:seconds'.
        """
        _seconds = milliseconds // 1000
        minutes, seconds = divmod(_seconds, 60)
        return f"{minutes}:{seconds if seconds >9 else f'0{seconds}'}"
