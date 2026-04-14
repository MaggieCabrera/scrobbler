import threading
import time
import pylast
from config import (
    LASTFM_API_KEY,
    LASTFM_API_SECRET,
    MIN_PLAY_SECONDS,
    MIN_PLAY_RATIO,
)


class Scrobbler:
    def __init__(self, session_key):
        self.network = pylast.LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
            session_key=session_key,
        )
        self._current = None
        self._started_at = None

    @property
    def current(self):
        return self._current

    def track_changed(self, new_track):
        """
        Call when a new track is identified.
        Scrobbles the previous track if it qualifies, then updates state.
        Returns True if the track actually changed.
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
        enough_ratio = (played / duration >= MIN_PLAY_RATIO) if duration else True

        if played >= MIN_PLAY_SECONDS and enough_ratio:
            threading.Thread(
                target=self._scrobble,
                args=(self._current, self._started_at),
                daemon=True,
            ).start()

    def _update_now_playing(self):
        artist = self._current["artist"]
        title = self._current["title"]
        threading.Thread(
            target=self._do_update_now_playing,
            args=(artist, title),
            daemon=True,
        ).start()

    def _do_update_now_playing(self, artist, title):
        try:
            self.network.update_now_playing(artist=artist, title=title)
        except Exception as e:
            print(f"  [error] now playing: {e}")

    def _scrobble(self, track, start_time):
        try:
            self.network.scrobble(
                artist=track["artist"],
                title=track["title"],
                timestamp=int(start_time),
            )
            print(f"\n  [scrobbled] {track['artist']} — {track['title']}")
        except Exception as e:
            print(f"  [error] scrobble: {e}")
