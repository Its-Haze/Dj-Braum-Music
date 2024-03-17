import discord
import discord
from discord.ext import commands
from discord.ui import Button, View
import wavelink

from src.utils.responses import Responses
import logging as logger


class PlayerControlsView(View):
    def __init__(self, responses: Responses):
        super().__init__()
        self.responses = responses

        self.control_flag = False  # default to being "off"
        self.control_flag_buttons = []

        self.experimental_feature_flag = False  # default to being "off"
        self.experimental_feature_flag_buttons = []

    def get_player(self, interaction: discord.Interaction):
        return wavelink.Pool().get_node().get_player(interaction.guild.id)

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.primary,
        emoji="⏮️",
        disabled=True,
    )
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player: wavelink.Player = self.get_player(interaction)

        if not player:
            self.clear_items()

            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning("Tried to edit a message that no longer exists.")
                return

        if not hasattr(player, "custom_queue"):
            logger.error("Player has no custom queue initialized.")

        if player.queue.mode != wavelink.QueueMode.normal:
            # Reset the queue mode to normal. if user skips a track while in loop mode.
            player.queue.mode = wavelink.QueueMode.normal

        prev_track: wavelink.Playable = player.custom_queue.history[-1]
        await player.play(prev_track)

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_resume_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()

            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning("Tried to edit a message that no longer exists.")
                return

        await player.pause(not player.paused)
        button.label = "Resume" if player.paused else "Pause"
        button.emoji = "▶️" if player.paused else "⏸️"

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️")
    async def skip_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()
            return await interaction.response.edit_message(view=self)

        if player.queue.is_empty and player.autoplay != wavelink.AutoPlayMode.enabled:
            await interaction.channel.send(
                embed=await self.responses.empty_queue(),
                delete_after=10,
            )
            self.clear_items()

        # when skipping a track, player.queue.mode should be reset to normal
        if player.queue.mode != wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.normal

        await player.skip()

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    async def history(self, interaction: discord.Interaction):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()
            return await interaction.response.edit_message(view=self)

        if not hasattr(player, "custom_queue"):
            return await interaction.channel.send(
                embed=await self.responses.nothing_in_history(),
                delete_after=10,
            )

        history_tracks: wavelink.Queue = player.custom_queue.history
        if not history_tracks:
            return await interaction.channel.send(
                embed=await self.responses.nothing_in_history(),
                delete_after=10,
            )

        ## Show the queue.
        await interaction.channel.send(
            embed=await self.responses.show_history(list(history_tracks), interaction)
        )

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    async def lyrics(self, interaction: discord.Interaction):
        """
        Fetch the lyrics of the current song.
        """
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()
            return await interaction.response.edit_message(view=self)

        # send as an ephemeral to avoid clutter.
        # await interaction.response.defer(ephemeral=True)

        if not (current_track := await self.responses.get_track(interaction.guild)):
            return await interaction.channel.send(
                embed=await self.responses.nothing_is_playing(),
                delete_after=10,
            )

        if current_track.source != "spotify":
            return await interaction.channel.send(
                embed=await self.responses.display_lyrics_error_only_spotify_song_allowed(),
                delete_after=10,
            )

        song_lyrics = await self.responses.get_lyrics(current_track)

        if not song_lyrics:
            return await interaction.channel.send(
                embed=await self.responses.lyrics_not_found(current_track),
                delete_after=10,
            )

        lyrics_embed = await self.responses.display_lyrics(
            song_lyrics, interaction.user
        )  ## Retrieve the lyrics and embed it.

        try:
            await interaction.channel.send(
                embed=lyrics_embed,
            )  ## Display the lyrics embed.
        except (
            discord.HTTPException
        ):  ## If the lyrics are more than 4096 characters, respond.
            await interaction.channel.send(
                embed=await self.responses.lyrics_too_long(),
                delete_after=10,
            )
        finally:
            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning("Tried to edit a message that no longer exists.")

    def change_button_style(
        self,
        style: discord.ButtonStyle,
        custom_id: str,
    ) -> discord.ui.Button:
        for button in self.children:
            if button.custom_id == custom_id:
                button.style = style

    async def nightcore(self, interaction: discord.Interaction):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()
            return await interaction.response.edit_message(view=self)

        ## If nightcore mode is already enabled, respond.
        if hasattr(player, "nightcore") and player.nightcore:

            player.nightcore = False
            filters: wavelink.Filters = player.filters
            filters.timescale.reset()
            await player.set_filters(filters)
            await interaction.channel.send(
                embed=await self.responses.nightcore_disable(),
                delete_after=10,
            )
            self.change_button_style(
                style=discord.ButtonStyle.grey,
                custom_id="experimental-nightcore",
            )

            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning(
                    "Tried to edit a message that no longer exists.", exc_info=True
                )
                return

        ## Enable nightcore mode.
        player.nightcore = True
        filters: wavelink.Filters = player.filters
        filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
        await player.set_filters(filters)
        await interaction.channel.send(
            embed=await self.responses.nightcore_enable(),
            delete_after=10,
        )
        self.change_button_style(
            style=discord.ButtonStyle.green,
            custom_id="experimental-nightcore",
        )

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning(
                "Tried to edit a message that no longer exists.", exc_info=True
            )

    @discord.ui.button(
        label="For You",
        style=discord.ButtonStyle.primary,
        emoji="🚀",
    )
    async def for_you(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()

            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning("Tried to edit a message that no longer exists.")
                return

        if not player.autoplay == wavelink.AutoPlayMode.enabled:
            player.autoplay = wavelink.AutoPlayMode.enabled
            await interaction.channel.send(
                embed=await self.responses.for_you_enabled(),
                delete_after=20,
            )
            button.style = discord.ButtonStyle.green
            button.emoji = "<a:I_Check:812904249175834644>"

        else:
            player.autoplay = wavelink.AutoPlayMode.partial
            await interaction.channel.send(
                embed=await self.responses.for_you_disabled(),
                delete_after=5,
            )
            button.style = discord.ButtonStyle.grey
            button.emoji = "🚀"

        if not hasattr(player, "custom_queue"):
            logger.error("Player has no custom queue initialized.")

            custom_queue: wavelink.Queue = player.custom_queue
            if custom_queue.history.is_empty:
                self.previous.disabled = True

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    async def loop_track(self, interaction: discord.Interaction):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()
            return await interaction.response.edit_message(view=self)

        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            self.change_button_style(
                style=discord.ButtonStyle.grey,
                custom_id="controls-loop-track",
            )
        else:
            player.queue.mode = wavelink.QueueMode.loop
            self.change_button_style(
                style=discord.ButtonStyle.green,
                custom_id="controls-loop-track",
            )

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    async def loop_queue(self, interaction: discord.Interaction):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()
            return await interaction.response.edit_message(view=self)

        if player.queue.mode == wavelink.QueueMode.loop_all:
            player.queue.mode = wavelink.QueueMode.normal
            self.change_button_style(
                style=discord.ButtonStyle.grey,
                custom_id="controls-loop-queue",
            )
        else:
            player.queue.mode = wavelink.QueueMode.loop_all
            self.change_button_style(
                style=discord.ButtonStyle.green,
                custom_id="controls-loop-queue",
            )

        try:
            return await interaction.response.edit_message(view=self)
        except discord.errors.NotFound:
            logger.warning("Tried to edit a message that no longer exists.")

    @discord.ui.button(
        label="Controls",
        style=discord.ButtonStyle.grey,
        emoji="🔧",
    )
    async def controls(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()

            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning("Tried to edit a message that no longer exists.")
                return

        self.control_flag = not self.control_flag

        if self.control_flag:
            loop_track_style = discord.ButtonStyle.grey
            if player.queue.mode == wavelink.QueueMode.loop:
                loop_track_style = discord.ButtonStyle.green

            loop_queue_style = discord.ButtonStyle.grey
            if player.queue.mode == wavelink.QueueMode.loop_all:
                loop_queue_style = discord.ButtonStyle.green

            loop_track = Button(
                label="Loop Track",
                style=loop_track_style,
                emoji="🔄",
                custom_id="controls-loop-track",
            )
            loop_queue = Button(
                label="Loop Queue",
                style=loop_queue_style,
                emoji="🔁",
                custom_id="controls-loop-queue",
            )

            self.control_flag_buttons = [
                loop_track,
                loop_queue,
            ]

            # Add (functions) to be called when the button is clicked.
            loop_track.callback = self.loop_track
            loop_queue.callback = self.loop_queue

            for _button in self.control_flag_buttons:
                self.add_item(_button)
            button.style = discord.ButtonStyle.green
        else:
            for _button in self.children:
                if _button in self.control_flag_buttons:
                    self.remove_item(_button)

            button.style = discord.ButtonStyle.grey

        return await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Experimental",
        style=discord.ButtonStyle.red,
        emoji="🔍",
    )
    async def experimental(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        player: wavelink.Player = self.get_player(interaction)
        if not player:
            self.clear_items()

            try:
                return await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                logger.warning("Tried to edit a message that no longer exists.")
                return

        self.experimental_feature_flag = not self.experimental_feature_flag

        if self.experimental_feature_flag:
            nightcore_style = discord.ButtonStyle.grey
            if hasattr(player, "nightcore") and player.nightcore:
                nightcore_style = discord.ButtonStyle.green
            nightcore = Button(
                label="Nightcore",
                style=nightcore_style,
                emoji="🌙",
                custom_id="experimental-nightcore",
            )
            lyrics = Button(
                label="Lyrics",
                style=discord.ButtonStyle.grey,
                emoji="📜",
                custom_id="experimental-lyrics",
            )
            feature_requests = Button(
                label="Support?",
                style=discord.ButtonStyle.url,
                url="https://discord.gg/cbVdqU7X7j",
                emoji="<a:KittyPat:638301285845696522>",
            )
            history = Button(
                label="History",
                style=discord.ButtonStyle.gray,
                emoji="📖",
                custom_id="experimental-history",
            )

            self.experimental_feature_flag_buttons = [
                nightcore,
                lyrics,
                history,
                feature_requests,
            ]

            # Add (functions) to be called when the button is clicked.
            nightcore.callback = self.nightcore
            lyrics.callback = self.lyrics
            history.callback = self.history
            for _button in self.experimental_feature_flag_buttons:
                self.add_item(_button)
            button.style = discord.ButtonStyle.green
        else:
            for _button in self.children:
                if _button in self.experimental_feature_flag_buttons:
                    self.remove_item(_button)

            button.style = discord.ButtonStyle.red

        return await interaction.response.edit_message(view=self)
