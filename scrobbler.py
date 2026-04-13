import time
import pylast
from config import (
    LASTFM_API_KEY,
    LASTFM_API_SECRET,
    LASTFM_USERNAME,
    LASTFM_PASSWORD,
    MIN_PLAY_SECONDS,
    MIN_PLAY_RATIO,
)


class Scrobbler:
    def __init__(self):
        if not all([LASTFM_API_KEY, LASTFM_API_SECRET, LASTFM_USERNAME, LASTFM_PASSWORD]):
            raise RuntimeError("Last.fm credentials are not set in .env")

        self.network = pylast.LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
            username=LASTFM_USERNAME,
            password_hash=pylast.md5(LASTFM_PASSWORD),
        )
        self._current = None       # dict: artist, title, duration
        self._started_at = None    # timestamp when current track was first detected

    @property
    def current(self):
        return self._current

    def track_changed(self, new_track):
        """
        Call this when a new track is identified.
        Scrobbles the previous track if it qualifies, then updates state.
        Returns True if the track actually changed, False if it's the same one.
        """
        new_id = (new_track["artist"].lower(), new_track["title"].lower())
        current_id = (
            (self._current["artist"].lower(), self._current["title"].lower())
            if self._current
            else None
        )

        if new_id == current_id:
            return False

        if self._current and self._started_at:
            self._maybe_scrobble()

        self._current = new_track
        self._started_at = time.time()
        self._update_now_playing()
        return True

    def _maybe_scrobble(self):
        played = time.time() - self._started_at
        duration = self._current.get("duration", 0)

        long_enough = played >= MIN_PLAY_SECONDS
        enough_ratio = (played / duration >= MIN_PLAY_RATIO) if duration else True

        if long_enough and enough_ratio:
            self._scrobble(self._current, self._started_at)

    def _update_now_playing(self):
        try:
            self.network.update_now_playing(
                artist=self._current["artist"],
                title=self._current["title"],
            )
        except Exception as e:
            print(f"  [error] now playing: {e}")

    def _scrobble(self, track, start_time):
        try:
            self.network.scrobble(
                artist=track["artist"],
                title=track["title"],
                timestamp=int(start_time),
            )
            print(f"  [scrobbled] {track['artist']} — {track['title']}")
        except Exception as e:
            print(f"  [error] scrobble: {e}")
