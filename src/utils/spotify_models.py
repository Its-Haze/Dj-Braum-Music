"""
HOLDS CUSTOM SPOTIFY MODELS.
"""

from dataclasses import dataclass

from logs import settings  # pylint:disable=import-error

logger = settings.logging.getLogger(__name__)


@dataclass(frozen=True, repr=False, eq=False)
class SpotifyTrack:
    """
    Represents a spotify track.
    """

    __KEYS = {
        NAME_KEY := "name",
        ARTISTS_KEY := "artists",
        DURATION_MS_KEY := "duration_ms",
        POPULARITY_KEY := "popularity",
        EXTERNAL_URLS_KEY := "external_urls",
    }

    # Required
    name: str
    artists: str
    duration_ms: int
    popularity: int
    external_urls: str

    @classmethod
    def from_search_results(cls, search_result: list[dict]) -> list["SpotifyTrack"]:
        """
        Returns a SpotifyTrack object with all attributes from a spotify search.
        """
        return [
            cls(
                **{
                    cls.NAME_KEY: track[cls.NAME_KEY],
                    cls.ARTISTS_KEY: " & ".join(
                        [f[cls.NAME_KEY] for f in track[cls.ARTISTS_KEY]]
                    ),
                    cls.DURATION_MS_KEY: track[cls.DURATION_MS_KEY],
                    cls.POPULARITY_KEY: track[cls.POPULARITY_KEY],
                    cls.EXTERNAL_URLS_KEY: track[cls.EXTERNAL_URLS_KEY]["spotify"],
                }
            )
            for track in search_result
        ]


@dataclass(frozen=True, repr=False, eq=False)
class SpotifyAlbum:
    """
    Represents a spotify album.
    """

    __KEYS = [
        NAME_KEY := "name",
        ARTISTS_KEY := "artists",
        EXTERNAL_URLS_KEY := "external_urls",
        RELEASE_DATE_KEY := "release_date",
        TOTAL_TRACKS_KEY := "total_tracks",
        ALBUM_TYPE_KEY := "album_type",
    ]
    __ALBUM_TYPES = {  # Putting this for future refference.
        TYPE_ALBUM := "album",
        TYPE_SINGLE := "single",
        TYPE_COMPILATION := "compilation",
    }

    name: str
    artists: str
    external_urls: str
    release_date: str
    total_tracks: int
    album_type: str

    @classmethod
    def from_search_results(cls, search_result: list[dict]) -> list["SpotifyAlbum"]:
        """
        Returns a SpotifyAlbum object with all attributes from a spotify album search.
        """
        return [
            cls(
                **{
                    cls.NAME_KEY: album[cls.NAME_KEY],
                    cls.ARTISTS_KEY: " & ".join(
                        [f[cls.NAME_KEY] for f in album[cls.ARTISTS_KEY]]
                    ),
                    cls.EXTERNAL_URLS_KEY: album[cls.EXTERNAL_URLS_KEY]["spotify"],
                    cls.RELEASE_DATE_KEY: album[cls.RELEASE_DATE_KEY],
                    cls.TOTAL_TRACKS_KEY: album[cls.TOTAL_TRACKS_KEY],
                    cls.ALBUM_TYPE_KEY: album[cls.ALBUM_TYPE_KEY],
                }
            )
            for album in search_result
        ]
