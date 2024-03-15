"""
This module contains the `Responses` class,
which holds methods for responding to interactions related to music playback.
"""

import logging as logger
from typing import Any

import discord
import wavelink

from src.utils.functions import Functions
from lyricsgenius.types import Song


class Responses(Functions):  # pylint:disable=too-many-public-methods
    """
    This class contains methods that return Discord embeds
    for various responses used in the Dj-Braum-Music bot.
    """

    async def user_not_in_vc(self) -> discord.Embed:
        """
        When /join is used but member is not in a voice channel.
        """
        embed = discord.Embed(
            title="**You are not in a voice channel.**",
            colour=discord.Colour.red(),
        )

        return embed

    async def no_connection_permissions(self) -> discord.Embed:
        """
        When user is not permitted to join a voice channel.
        """
        embed = discord.Embed(
            title="**Can't connect to the voice channel. Verify the permissions and try again.**",
            colour=discord.Colour.red(),
        )
        return embed

    async def nightcore_disable(self) -> discord.Embed:
        """
        Disable Nightcore, by running the command again.
        """
        embed = discord.Embed(
            title="**Disabling Nightcore mode.**",
            colour=discord.Colour.green(),
        )
        return embed

    async def nightcore_enable(self) -> discord.Embed:
        """
        When /nightcore is enabled.
        """
        embed = discord.Embed(
            title="**Enabling Nightcore processing..**",
            colour=discord.Colour.green(),
        )
        embed.set_footer(
            text="Note: If you want to disable the filter, run the same command again.\nFilters automatically reset when all songs in the queue have been played."
        )
        return embed

    async def coult_not_connect(self) -> discord.Embed:
        """
        When /join is used but interaction.user is not of the type Interaction.Member.
        """
        return discord.Embed(
            title="**Sorry, but I couldn't join the voice channel. Please make sure you are connected to a voice channel**",
            colour=self.err_color,
        )

    async def in_vc(self) -> discord.Embed:
        """
        When /join is used and member is in a voice channel.
        """
        return discord.Embed(
            title="**Joined voice channel.**",
            colour=self.sucess_color,
        )

    async def already_in_vc(self) -> discord.Embed:
        """
        when /join is used while the Client is in a VoiceChannel
        """
        return discord.Embed(
            title="**I am already in a voice channel.**",
            colour=discord.Colour.orange(),
        )

    async def left_vc(self) -> discord.Embed:
        """
        When the Client leaves a channel
        """
        return discord.Embed(
            title="**Left voice channel.**",
            colour=self.sucess_color,
        )

    async def already_left_vc(self) -> discord.Embed:
        """
        when /leave is triggered and the client is not connected
        """
        return discord.Embed(
            title="**I am not in a voice channel.**",
            colour=discord.Colour.orange(),
        )

    async def nothing_is_playing(self) -> discord.Embed:
        """
        When nothing is playing
        """
        return discord.Embed(
            title="**Nothing is playing at the moment**.",
            colour=self.err_color,
        )

    async def nothing_in_history(self) -> discord.Embed:
        """
        When nothing is in history
        """
        return discord.Embed(
            title="**Nothing in history to display**.",
            colour=self.err_color,
        )

    async def no_track_results(self) -> discord.Embed:
        """
        When no tracks were found
        """
        return discord.Embed(
            title="**Unable to find any results!**",
            colour=self.err_color,
        )

    async def display_track(
        self,
        player: wavelink.Player,
        track: wavelink.Playable,
        is_queued: bool = False,
        is_playing: bool = False,
    ) -> discord.Embed:
        """
        Displays the current track.
        """

        # Fetch extra information from spotify if exists.
        if track.source != "spotify":
            _search_result = await wavelink.Playable.search(
                f"{track.title} {track.author}",
                source="spsearch",
            )

            track_metadata = _search_result[0]

        embed = discord.Embed(title="**Now Playing**", colour=self.sucess_color)

        if any([is_queued, is_playing, player.loop, player.queue_loop]):
            if (
                not is_queued and player.loop
            ):  ## If the track is not queued and the loop is enabled.
                embed = discord.Embed(
                    title="**Now Playing (Track Loop Enabled)**",
                    colour=self.sucess_color,
                )

            elif (
                not is_queued and player.queue_loop
            ):  ## If the track is not queued and the queue loop is enabled.
                embed = discord.Embed(
                    title="**Now Playing (Queue Loop Enabled)**",
                    colour=self.sucess_color,
                )

            elif (
                is_queued and player.loop
            ):  ## If both the track is queued and the loop is enabled.
                embed = discord.Embed(
                    title="**Queued Track (Another Track Is Looping)**",
                    colour=self.sucess_color,
                )

            elif (
                is_queued and player.queue_loop
            ):  ## If both the track is queued and the queue loop is enabled.
                embed = discord.Embed(
                    title="**Queued Track (Queue Loop Enabled)**",
                    colour=self.sucess_color,
                )

            elif (
                is_queued and not player.loop
            ):  ## If the track is queued and the loop is not enabled.
                embed = discord.Embed(
                    title="**Queued Track**", colour=self.sucess_color
                )

        if not track.uri:
            meta_uri = track_metadata.uri
        embed.add_field(
            name="Name",
            value=f"[{track.title}]({track.uri or meta_uri})",
            inline=False,
        )
        if not track.artist.url:
            meta_artist_url = track_metadata.artist.url
        embed.add_field(
            name="Author",
            value=f"[{track.author}]({track.artist.url or meta_artist_url})",
            inline=False,
        )

        if not track.album.name:
            meta_album_name = track_metadata.album.name
        if not track.album.url:
            meta_album_url = track_metadata.album.url
        embed.add_field(
            name="Album",
            value=f"[{track.album.name or meta_album_name}]({track.album.url or meta_album_url})",
            inline=False,
        )

        if is_playing:  ## If /nowplaying is called, show the duration played.
            embed.add_field(
                name="Duration Played",
                value=f"{self.convert_ms(int(player.position))}/{self.convert_ms(track.length)}",
                inline=False,
            )  ## Format the duration's into MM:SS

        else:  ## Otherwise, just show the track's duration.
            embed.add_field(
                name="Duration",
                value=self.convert_ms(track.length),
                inline=False,
            )

        # Seems like release date is gone..
        # embed.add_field(
        #     name="Release Date", value=track.album.release_date, inline=False
        # )
        embed.set_thumbnail(url=track.artwork)
        if track.source != "spotify":
            embed.set_footer(
                text="Note: Youtube tracks may not have accurate metadata."
            )
        return embed

    async def started_playing(self) -> discord.Embed:
        """
        When a Session has started
        """
        return discord.Embed(
            title="**Started Session.**",
            colour=self.sucess_color,
        )

    async def show_queue(
        self,
        queue_info: list[wavelink.Playable],
        guild_id,
    ) -> discord.Embed:
        """
        Shows the queue
        """
        player = await self.get_player(guild_id)  ## Retrieve the player.
        queue_list = []  ## To store the tracks in the queue.
        title = "**Queue**"

        if len(queue_info) == 0:  ## If there are no tracks in the queue, respond.
            return await self.empty_queue()

        for i, track in enumerate(
            list(queue_info)[:20], start=1
        ):  ## Loop through all items in the queue.
            queue_list.append(
                f"**{i}.** [{track.title}]({track.uri}) - [{track.author}]({track.artist.url})"
            )  ## Add each track to the list.

        if player.queue_loop:  ## If the queue loop is enabled, change the title.
            title = "**Queue (Queue Loop Enabled)**"

        embed = discord.Embed(
            title=title,
            description="\n".join(queue_list),
            colour=self.sucess_color,
        )

        embed.set_footer(text="Note: A max of 20 tracks are displayed in the queue.")
        embed.set_thumbnail(url=queue_info[0].artwork)
        return embed

    async def show_history(
        self,
        queue_info: list[wavelink.Playable],
        interaction: discord.Interaction,
    ) -> discord.Embed:
        """
        Shows the history
        """
        history_list = []  ## To store the tracks in the queue.
        title = "**History (Latest song on top)**"

        if len(queue_info) == 0:  ## If there are no tracks in the queue, respond.
            return await self.empty_history()

        for i, track in enumerate(
            list(reversed(queue_info))[:10], start=1
        ):  ## Loop through all items in the queue.
            history_list.append(
                f"**{i}.** [{track.title}]({track.uri}) - [{track.author}]({track.artist.url})",
            )  ## Add each track to the list.

        embed = discord.Embed(
            title=title,
            description="\n".join(history_list),
            colour=self.sucess_color,
        )

        embed.set_footer(text="Note: A max of 10 tracks are displayed in the history.")
        embed.set_thumbnail(url=queue_info[-1].artwork)
        embed.set_author(
            name=f"{interaction.user.display_name or interaction.user.name}",
            icon_url=interaction.user.display_avatar.url or interaction.user.avatar.url,
        )

        return embed

    async def empty_queue(self) -> discord.Embed:
        """
        Empties the queue
        """
        return discord.Embed(
            title="**The queue is currently empty.**",
            colour=discord.Colour.orange(),
        )

    async def empty_history(self) -> discord.Embed:
        """
        Empties the queue
        """
        return discord.Embed(
            title="**The history is currently empty.**",
            colour=discord.Colour.orange(),
        )

    async def shuffled_queue(self) -> discord.Embed:
        """
        When the queue has been shuffled
        """
        return discord.Embed(
            title="**Shuffled the queue**.",
            colour=self.sucess_color,
        )

    async def volume_too_high(self) -> discord.Embed:
        """
        When volume has reached 100% and Member tried to increase it.
        """
        return discord.Embed(
            title="**Volume cannot be greater than 100%.**",
            colour=self.err_color,
        )

    async def volume_set(self, percentage: int) -> discord.Embed:
        """
        Set the volume
        """
        return discord.Embed(
            title=f"**Volume has been set to {percentage}%.**",
            colour=self.sucess_color,
        )

    async def queue_track_actions(
        self,
        queue: wavelink.Queue,
        track_index: int,
        embed_title: str,
    ) -> discord.Embed:
        """
        Used for remove and skipto.
        """
        try:
            embed = discord.Embed(
                title=f"**{embed_title} {queue[track_index - 1].title} - {queue[track_index -1].author}.**",
                colour=self.sucess_color,
            )  ## The track exists in the queue.

        except IndexError:  ## If the track was not found in the queue, return False.
            logger.exception("Track not found in queue.")

        return embed

    async def common_track_actions(
        self,
        track_info: wavelink.Playable,
        embed_title: str,
    ) -> discord.Embed:
        """
        Used for pause, resume, loop, queueloop.
        """
        if track_info is None:
            ## If no track info is passed, just display the embed's title.
            # Used in the case of queueloop.
            return discord.Embed(title=f"**{embed_title}.**", colour=self.sucess_color)

        return discord.Embed(
            title=f"**{embed_title} {track_info.title} - {track_info.author}.**",
            colour=self.sucess_color,
        )

    async def track_not_in_queue(self) -> discord.Embed:
        """
        When the track is not in a queue.
        """
        return discord.Embed(
            title="**Invalid track number.**",
            colour=self.err_color,
        )

    async def no_tracks_in_queue(self) -> discord.Embed:
        """
        No tracks in the queue.
        """
        return discord.Embed(
            title="**There are no more tracks in the queue.**",
            colour=discord.Colour.dark_purple(),
        )

    async def left_due_to_inactivity(self) -> discord.Embed:
        """
        When the Client has been inactive
        and leaves.
        """
        return discord.Embed(
            title="**Left VC due to inactivity.**",
            colour=self.err_color,
        )

    async def less_than_1_track(self) -> discord.Embed:
        """
        When there is less than 1 track in queue.
        """
        return discord.Embed(
            title="**There needs to be 1 or more tracks in the queue!**",
            colour=self.err_color,
        )

    async def added_playlist_to_queue(self) -> discord.Embed:
        """
        When a playlist is added to the queue.
        """
        return discord.Embed(
            title="**Added Spotify playlist to the queue.**",
            colour=self.sucess_color,
        )

    async def cleared_queue(self) -> discord.Embed:
        """
        When the queue has been cleared.
        """
        return discord.Embed(
            title="**Emptied the queue.**",
            colour=self.sucess_color,
        )

    async def invalid_url(self) -> discord.Embed:
        """
        When the spotify url is invalid.
        """
        return discord.Embed(
            title="**Invalid Spotify URL entered.**",
            colour=self.err_color,
        )

    async def podcasts_not_supported(self) -> discord.Embed:
        """
        When a spotify podcast or artist is provided instead of a track and playlist
        """
        return discord.Embed(
            title="**Spotify podcasts or artists are not supported.**",
            colour=self.err_color,
        )

    async def added_track(
        self,
        track_info: wavelink.Playable,
        user: discord.User,
    ) -> discord.Embed:
        """
        When a track is added to the queue
        """
        embed = discord.Embed(
            # title=f"**Added {track_info.title} - {track_info.author} to the queue.**",
            colour=self.sucess_color,
        )

        embed.set_author(
            name=f"{user.display_name or user.name} added {track_info.title} - {track_info.author} to the queue.",
            icon_url=user.display_avatar.url or user.avatar.url,
            url=track_info.uri or None,
        )

        return embed

    async def only_supported_urls(self) -> discord.Embed:
        """
        When someone does not put a valid url
        """
        return discord.Embed(
            title="**Only Spotify & Youtube Music URLs are supported!**",
            colour=self.err_color,
        )

    async def display_new_releases(self, new_releases) -> discord.Embed:
        """
        Shows the top 10 releases
        """
        embed = discord.Embed(title="**New Releases**", colour=self.sucess_color)

        embed.add_field(
            name="Top 10",  ## Display all the newly released tracks,
            value="\n".join(
                [
                    f"**{i}.** [{item['name']}]({item['external_urls']['spotify']})"
                    for i, item in enumerate(new_releases["albums"]["items"], start=1)
                ]
            ),
        )

        embed.set_thumbnail(
            url=new_releases["albums"]["items"][0]["images"][0]["url"]
        )  ## Set the thumbnail to the newest track.
        return embed

    async def display_trending(self, trending) -> discord.Embed:
        """
        Shows the top 10 trending songs
        """
        value = "\n".join(
            [
                f"**{i}.** [{item['track']['name']}]({item['track']['external_urls']['spotify']}) - {item['track']['artists'][0]['name']}"
                for i, item in enumerate(trending["items"], start=1)
            ]
        )
        embed = discord.Embed(title="**Trending**", colour=self.sucess_color)

        embed.add_field(
            name="Top 10",  ## Display all the trending tracks,
            value=value,
        )

        embed.set_thumbnail(
            url=trending["items"][0]["track"]["album"]["images"][0]["url"]
        )  ## Set the thumbnail to the top trending track.
        return embed

    async def autosuggestion_trending_spotify(self, trending) -> dict[str, Any]:
        """
        Shows the top 10 trending songs in the autocompletion for /play
        """
        payload = {}
        value = "\n".join(
            [
                f"**{i}.** [{item['track']['name']}]({item['track']['external_urls']['spotify']}) - {item['track']['artists'][0]['name']}"
                for i, item in enumerate(trending["items"], start=1)
            ]
        )

        for i, item in enumerate(trending["items"], start=1):
            payload[i] = {
                "name": item["track"]["name"],
                "url": item["track"]["external_urls"]["spotify"],
                "artist": item["track"]["artists"][0]["name"],
            }

        embed = discord.Embed(title="**Trending**", colour=self.sucess_color)

        embed.add_field(
            name="Top 10",  ## Display all the trending tracks,
            value=value,
        )

        embed.set_thumbnail(
            url=trending["items"][0]["track"]["album"]["images"][0]["url"]
        )  ## Set the thumbnail to the top trending track.
        return embed

    async def display_playlist(
        self,
        playlist: wavelink.tracks.Playlist,
        type: str = "Playlist",
    ) -> discord.Embed:
        """
        Display playlist data
        """

        embed = discord.Embed(
            title=f"**Queued {type}**",
            colour=self.sucess_color,
        )
        if playlist.name:
            if playlist.url:
                embed.add_field(
                    name="Name",
                    value=f"[{playlist.name}]({playlist.url})",
                    inline=False,
                )
            else:
                embed.add_field(name="Name", value=(f"{playlist.name}"), inline=False)

        if playlist.author:
            embed.add_field(name="Author", value=f"{playlist.author}", inline=False)
        else:
            if playlist.tracks:
                track = playlist.tracks[0]
                if track.author:
                    embed.add_field(
                        name="Author", value=f"{track.author}", inline=False
                    )
        if playlist.tracks:
            embed.add_field(name="Tracks", value=len(playlist.tracks), inline=False)
        if playlist.artwork:
            embed.set_thumbnail(url=playlist.artwork)
        else:
            if playlist.tracks:
                track = playlist.tracks[0]
                if track.artwork:
                    embed.set_thumbnail(url=track.artwork)

        embed.set_footer(
            text="Note: some playlists may not have accurate metadata. Especially if they are from Youtube/Youtube Music."
        )
        return embed

    async def _display_playlist(self, playlist_url) -> discord.Embed:
        """
        shows all the tracks from a playlist url
        """
        playlist_info = await self.playlist_info(
            playlist_url
        )  ## Retrieve info about the playlist.

        embed = discord.Embed(title="**Queued Playlist**", colour=self.sucess_color)
        embed.add_field(
            name="Name",
            value=f"[{playlist_info['name']}]({playlist_info['external_urls']['spotify']})",
            inline=False,
        )

        embed.add_field(
            name="User",
            value=f"[{playlist_info['owner']['display_name']}]({playlist_info['owner']['external_urls']['spotify']})",
            inline=False,
        )

        embed.add_field(
            name="Tracks", value=playlist_info["tracks"]["total"], inline=False
        )
        embed.set_thumbnail(
            url=playlist_info["images"][0]["url"]
        )  ## Set the thumbnail to the playlist's artwork.
        return embed

    async def display_album(self, album_url) -> discord.Embed:
        """
        Displays the album
        """
        album_info = await self.album_info(
            album_url
        )  ## Retrieve info about the playlist.

        embed = discord.Embed(title="**Queued Album**", colour=self.sucess_color)
        embed.add_field(
            name="Name",
            value=f"[{album_info['name']}]({album_info['external_urls']['spotify']})",
            inline=False,
        )

        embed.add_field(
            name="Author",
            value=f"[{album_info['artists'][0]['name']}]({album_info['artists'][0]['external_urls']['spotify']})",
            inline=False,
        )

        embed.add_field(
            name="Release Date", value=album_info["release_date"], inline=False
        )
        embed.add_field(name="Tracks", value=album_info["total_tracks"], inline=False)
        embed.set_thumbnail(
            url=album_info["images"][0]["url"]
        )  ## Set the thumbnail to the album's artwork
        return embed

    async def display_vote(self) -> tuple[discord.Embed, discord.ui.View]:
        """
        Used for the vote command.
        """
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        item: discord.ui.Button = discord.ui.Button(
            style=style,
            label="Vote!",
            url=self.vote_url,
        )
        view.add_item(item=item)

        embed = discord.Embed(
            title="**Click the button below to vote for me!**", colour=self.sucess_color
        )
        return embed, view

    async def display_invite(self) -> tuple[discord.Embed, discord.ui.View]:
        """
        Used for the invite command.
        """
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        item: discord.ui.Button = discord.ui.Button(
            style=style,
            label="Invite!",
            url=self.invite_url,
        )
        view.add_item(item=item)

        embed = discord.Embed(
            title="**Click the button below to invite me!**",
            colour=self.sucess_color,
        )
        return embed, view

    async def display_support(self) -> tuple[discord.Embed, discord.ui.View]:
        """
        Used for the support command.
        """
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        item: discord.ui.Button = discord.ui.Button(
            style=style,
            label="Support!",
            url=self.support_url,
        )
        view.add_item(item=item)

        embed = discord.Embed(
            title="**Click the button below join my support server!**",
            colour=self.sucess_color,
        )
        return embed, view

    async def display_lyrics(
        self,
        lyrics: Song,
        user: discord.User,
    ) -> discord.Embed:
        """
        Displays the lyrics.
        """
        description = lyrics.lyrics.split("\n", 1)[1]
        title = "Lyrics"

        if lyrics.title and lyrics.artist:
            title = f"{lyrics.title} - {lyrics.artist}"

        embed = discord.Embed(
            title=title, description=description, colour=self.sucess_color
        )
        if lyrics.song_art_image_url:
            embed.set_thumbnail(url=lyrics.song_art_image_url)

        embed.set_author(
            name=f"Lyrics requested by {user.display_name or user.name}",
            icon_url=user.display_avatar.url or user.avatar.url,
        )

        return embed

    async def lyrics_not_found(self, track: wavelink.Playable) -> discord.Embed:
        """
        When the lyrics are not found.
        """
        return discord.Embed(
            title=f"No lyrics found for {track.title} - {track.author}",
            colour=self.err_color,
        )

    async def display_lyrics_error_only_spotify_song_allowed(self) -> discord.Embed:
        """
        Display an embed saying "Sorry, only Spotify tracks are supported."
        """
        return discord.Embed(
            title="Sorry, only Spotify tracks are supported.", colour=self.err_color
        )

    async def lyrics_too_long(self) -> discord.Embed:
        """
        When the lyrics are over 4096 characters long.
        """
        return discord.Embed(
            title="**The Lyrics in this song are over 4096 characters!**",
            description="The correct lyrics were probably not found..\nPlease be aware that this is an experimental feature and may not work for all songs.",
            colour=self.err_color,
        )

    async def log_track_started(
        self, track: wavelink.Playable, guild: str
    ) -> discord.Embed:
        """
        Sends to the dedicated LOG channel.
        >> A track has been added.
        """
        return discord.Embed(
            title=f"**{track.title} - {track.author} started on Guild: {guild}.**",
            colour=self.sucess_color,
        )

    async def log_track_finished(
        self, track: wavelink.Playable, guild: str
    ) -> discord.Embed:
        """
        sends a dedicated LOG message.
        >> A track has finished.
        """
        return discord.Embed(
            title=f"**{track.title} - {track.author} finished on Guild: {guild}.**",
            colour=self.err_color,
        )

    async def display_search(self, search_query) -> discord.Embed:
        """
        Displays the search results.
        """
        search_results = await self.search_songs(
            search_query
        )  ## Retrieve search results.
        formatted_results = await self.format_search_results(
            search_results
        )  ## Format the search results.

        embed = discord.Embed(
            title="**Search Results**",
            description=formatted_results,
            colour=self.sucess_color,
        )

        embed.set_thumbnail(
            url=search_results["tracks"]["items"][0]["album"]["images"][0]["url"]
        )  ## Set the thumbnail to the first track's artwork.
        embed.set_footer(
            text="Tip: Copy any one of the track or album hyperlinks and play them with /url."
        )
        return embed

    async def already_paused(self, track_info: wavelink.Playable) -> discord.Embed:
        """
        When the wavelink player is already paused.
        """
        return discord.Embed(
            title=f"**{track_info.title} - {track_info.author} is already paused!**",
            colour=self.err_color,
        )

    async def already_resumed(self, track_info) -> discord.Embed:
        """
        When the wavelink player is already resumed.
        """
        return discord.Embed(
            title=f"**{track_info.title} - {track_info.author} has already been resumed!**",
            colour=self.err_color,
        )

    @staticmethod
    async def on_joining_guild(guild: discord.Guild) -> discord.Embed:
        """
        Embed for when braum joins a server.
        """
        title = (
            f"**BRAUM HAS JOINED** -->, {guild.name}\n"
            f"Owner is ``@{guild.owner.name}``\n"
            f"This server has {guild.member_count} members!"
        )
        return discord.Embed(
            title=title,
            colour=discord.Colour.green(),
        )

    @staticmethod
    async def on_leaving_guild(guild: discord.Guild) -> discord.Embed:
        """
        Embed for when braum leaves a server.
        """
        title = (
            f"**BRAUM HAS LEFT** -->, {guild.name}\n"
            f"Owner was ``@{guild.owner.name}``\n"
            f"This server had {guild.member_count} members!"
        )

        return discord.Embed(
            title=title,
            colour=discord.Colour.green(),
        )

    async def already_in_voicechannel(
        self,
        channel,
    ) -> discord.Embed:
        """
        When the client is already connected to a voice channel.
        """
        return discord.Embed(
            title="**Dj braum is already connected to a voice channel!**",
            description=f"Join me here --> <#{channel.id}>",
            colour=self.err_color,
        )
