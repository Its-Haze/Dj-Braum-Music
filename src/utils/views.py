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

    def change_nightcore_button_style(
        self,
        style: discord.ButtonStyle,
    ) -> discord.ui.Button:
        for button in self.children:
            if button.custom_id == "experimental-nightcore":
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
            self.change_nightcore_button_style(discord.ButtonStyle.grey)

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
        self.change_nightcore_button_style(discord.ButtonStyle.green)

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
                "✨ 'For You' is enabled! (Braum AI) will keep the music flowing with songs tailored to your session's vibe. The more you listen, the more personalized your playlist becomes. Enjoy a musical journey tailored by Braum, just for you!",
                delete_after=20,
            )
            button.style = discord.ButtonStyle.green
            button.emoji = "<a:I_Check:812904249175834644>"

        else:
            player.autoplay = wavelink.AutoPlayMode.partial
            await interaction.channel.send(
                "🚀 'For You' is disabled! (Braum AI) will no longer automatically add songs to your queue.",
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
