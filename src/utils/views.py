
import discord
import rich
import wavelink

from src.cogs.music import MusicHelper


# Defines a custom Select containing colour options
# that the user can choose. The callback function
# of this class is called when the user changes their choice
class TracksDropdown(discord.ui.Select):
    def __init__(self, tracks: list[wavelink.YouTubeMusicTrack]):
        self.tracks = tracks
        self.music = MusicHelper()

        list_of_numbers = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
        ]

        options = [
            discord.SelectOption(
                label=f"{track.info.get('title')}",
                description=f"{track.info.get('author').split(',')[0]} - {self.music.convert_ms(milliseconds=track.info.get('length'))}",
                emoji=list_of_numbers[i],
                value=f"{i}",
            )
            for i, track in enumerate(self.tracks)
        ]
        rich.inspect(options)

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Choose your song...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        await interaction.response.defer()

        rich.inspect(self)

        # Get the selected value from the dropdown list 1-10
        value: int = int(self.values[0])

        # Get the selected track
        track = self.tracks[value]

        # Initalize voice client
        voice_client = await self.music.initalize_voice_client(interaction=interaction)

        # ###############################################################
        # FIXME: COPIED FROM THE /PLAY COMMAND... REMAKE INTO FUNCTIONS #
        # ###############################################################

        ## Store the channel id to be used in track_start.
        voice_client.reply = interaction.channel

        ## If a track is playing, add it to the queue.
        if voice_client.is_playing():

            ## Use the modified track.
            await interaction.followup.send(embed=await self.music.added_track(track))

            ## Add the modified track to the queue.
            return await voice_client.queue.put_wait(track)

        else:
            ## Otherwise, begin playing.

            ## Send an ephemeral as now playing is handled by on_track_start.
            await interaction.followup.send(embed=await self.music.started_playing())

            ## Set the loop value to false as we have just started playing.
            voice_client.loop = False

            ## Set the queue_loop value to false as we have just started playing.
            voice_client.queue_loop = False

            ## Used to store the currently playing track in case the user decides to loop.
            voice_client.looped_track = None

            ## Used to re-add the track in a queue loop.
            voice_client.queue_looped_track = None

            ## Play the modified track.
            return await voice_client.play(track)


class TracksDropdownView(discord.ui.View):
    def __init__(self, tracks: list[wavelink.YouTubeMusicTrack]):
        super().__init__()
        self.tracks = tracks

        # Adds the dropdown to our view object.
        self.add_item(TracksDropdown(tracks=self.tracks))
