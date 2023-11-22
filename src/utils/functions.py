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
from rich import inspect
from spotipy import SpotifyException

from src.utils.abc import AbstractBaseClass
from src.utils.spotify_models import SpotifyTrack


class Functions(AbstractBaseClass):  # pylint:disable=too-many-public-methods
    """
    Contains all functions used in the music cog.
    Any functionality that is used more than once should be placed here.
    """

    async def get_track(self, guild: discord.Guild) -> wavelink.tracks.Playable | None:
        """Returns info about the current track."""
        player = await self.get_player(guild=guild)
        if player is None:
            logger.warning("Ran 'get_track' but got an empty player back.")
            return None
        return player.current

    async def get_player(self, guild: discord.Guild) -> wavelink.Player | None:
        """Returns player info."""
        return wavelink.NodePool.get_node().get_player(guild.id)

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

    async def gather_track_info(
        self,
        title: str,
        artist: str,
        track_info: wavelink.YouTubeMusicTrack,
    ) -> wavelink.YouTubeMusicTrack:
        """Use info from spotify to modify existing track_info."""
        search_results = self.spotify.search(
            q=f"{title} {artist}", limit=1
        )  ## Search spotify for metadata.

        logger.info("Gather track information")
        inspect(search_results["tracks"]["items"][0])

        track_info.title = search_results["tracks"]["items"][0]["name"]
        track_info.title_url = search_results["tracks"]["items"][0]["external_urls"][
            "spotify"
        ]
        track_info.author = search_results["tracks"]["items"][0]["artists"][0]["name"]
        track_info.author_url = search_results["tracks"]["items"][0]["artists"][0][
            "external_urls"
        ]["spotify"]
        track_info.album = search_results["tracks"]["items"][0]["album"]["name"]
        track_info.album_url = search_results["tracks"]["items"][0]["album"][
            "external_urls"
        ]["spotify"]
        track_info.cover_url = search_results["tracks"]["items"][0]["album"]["images"][
            0
        ]["url"]
        track_info.release_date = search_results["tracks"]["items"][0]["album"][
            "release_date"
        ]
        track_info.duration = search_results["tracks"]["items"][0]["duration_ms"]
        return track_info

    async def gather_track_info_cached(
        self,
        track_info: wavelink.YouTubeMusicTrack,
        track_metadata: dict[str, Any],
    ) -> wavelink.YouTubeMusicTrack:
        """
        Use info from existing spotify results to avoid many requests. Used in /url for tracks.
        """

        track_info.title = track_metadata["name"]
        track_info.title_url = track_metadata["external_urls"]["spotify"]
        track_info.author = track_metadata["artists"][0]["name"]
        track_info.author_url = track_metadata["artists"][0]["external_urls"]["spotify"]
        track_info.album = track_metadata["album"]["name"]
        track_info.album_url = track_metadata["album"]["external_urls"]["spotify"]
        track_info.cover_url = track_metadata["album"]["images"][0]["url"]
        track_info.release_date = track_metadata["album"]["release_date"]
        return track_info

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

    async def add_spotify_url(
        self,
        guild: discord.Guild,
        media_url: str,
        channel_id: int,
        url_type: str,
    ) -> bool | None:
        """
        Adds either a spotify playlist or album to the queue.
        """
        media_id = media_url.split("/")[-1].split("?")[
            0
        ]  ## Returns only the playlist ID.
        player = await self.get_player(guild)  ## Retrieve the player.

        if player is None:
            logger.error("Player not found!: method add_spotify_url")
            return None

        ## Check whether or not the guild's player contains certain values.
        if not hasattr(player, "reply"):
            ## Define the same values as in the play command since the player attributes do not exist yet.
            player.reply = channel_id
            player.loop = False
            player.queue_loop = False
            player.looped_track = None
            player.queue_looped_track = None

        if url_type == "playlist":
            try:
                media_tracks = self.spotify.playlist_tracks(
                    media_id
                )  ## Used to retrieve all tracks in a playlist.
            except SpotifyException:  ## If nothing was found, return none.
                return None

        elif url_type == "album":
            try:
                media_tracks = self.spotify.album_tracks(
                    media_id
                )  ## Used to retrieve all tracks in an album.
            except SpotifyException:  ## If nothing was found, return none.
                return None

        for i, track in enumerate(
            media_tracks["items"], start=0
        ):  ## Loop through all tracks in the playlist/album.
            if i == 1 and not await self.get_track(
                guild
            ):  ## If the first track has been added to queue and nothing else is currently playing.
                next_track = await player.queue.get_wait()  ## Retrieve the queue.
                await player.play(
                    next_track
                )  ## Immediatley play the first track to avoid waiting for the entire queue to be loaded.
                player.looped_track = next_track

            try:
                title = track["track"]["name"]
                artist = track["track"]["artists"][0]["name"]
            except KeyError:  ## spotify albums have different paths.
                title = track["name"]
                artist = track["artists"][0]["name"]

            track_name = f"{title} {artist}"  ## Collect the track name and artist name from self.spotify.

            try:
                medias = await wavelink.YouTubeMusicTrack.search(
                    track_name
                )  ## Search for the song in the playlist.
                media = list(medias)[0]
            except IndexError:  ## If no results were found, skip to the next track.
                pass

            final_track = await self.gather_track_info(
                media.title, media.author, media
            )  ## Modify the playlist track info with spotify before adding to the queue.

            await player.queue.put_wait(
                final_track
            )  ## Add the playlist/album to the queue.
        return True  ## Return true to avoid conflicts with SpotifyException.

    async def add_track(self, guild, track_url, channel_id):
        """
        Adds a self.spotify track to the queue.
        """
        track_id = track_url.split("/")[-1].split("?")[0]  ## Returns only the track ID.
        player = await self.get_player(guild)  ## Retrieve the player.
        queue = await self.get_queue(guild)  ## Retreieve the queue.

        if not hasattr(
            player, "reply"
        ):  ## Check whether or not the guild's player contains certain values.
            player.reply = channel_id  ## Define the same values as in the play command since the player attributes do not exist yet.
            player.loop = False
            player.queue_loop = False
            player.looped_track = None
            player.queue_looped_track = None

        else:  ## Otherwise, ignore.
            pass

        try:
            track_info = self.spotify.track(track_id)  ## Retrieve track info.
        except SpotifyException:  ## If nothing was found, return none.
            return None

        title = track_info["name"]
        artist = track_info["artists"][0]["name"]
        track_name = (
            f"{title} {artist}"  ## Collect the track name and artist name from spotify.
        )

        try:
            tracks = await wavelink.YouTubeMusicTrack.search(track_name)
            track = list(tracks)[0]
        except IndexError:  ## If no results were found, pass.
            pass

        final_track = await self.gather_track_info_cached(
            track, track_info
        )  ## Modify the track info with existing self.spotify info before adding to the queue.

        if await self.get_track(
            guild
        ):  ## If something is currently playing, add the track to the queue.
            await player.queue.put_wait(final_track)  ## Add the track to the queue.
            return final_track  ## Return the track info required for the added to queue embed.

        else:  ## Otherwise play it now.
            await player.play(final_track)
            return final_track  ## Return the track info required for the added to queue embed.

    async def get_lyrics(self, search_query: str) -> Optional[str]:
        """
        Returns the lyrics of a song. If no lyrics are found, return None.
        """
        track = self.genius.search_song(search_query)

        if not isinstance(track, Song):
            logger.error("Lyrics not found!")
            return None

        logger.info("Lyrics found!")
        return track.lyrics.split("\n", 1)[1]

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
