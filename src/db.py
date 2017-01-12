import sqlite3


Q_INIT_PLAYLISTS_TABLE = """
CREATE TABLE playlists
(uri TEXT PRIMARY KEY,
 name TEXT)
""".strip()

Q_INIT_PLAYLIST_TRACKS_TABLE = """
CREATE TABLE playlisttracks
(playlist_uri TEXT,
 track_uri TEXT)
""".strip()

Q_INIT_TRACKS_TABLE = """
CREATE TABLE tracks
(track_uri TEXT PRIMARY KEY,
 youtube_link TEXT,
 ignore_flag INTEGER,
 deleted_flag INTEGER)
""".strip()

Q_INSERT_PLAYLIST = """
INSERT INTO playlists (uri, name)
VALUES (?, ?)
""".strip()

Q_REMOVE_PLAYLIST = """ 

""".strip() #T TODO

class Database:
    """each function is its own transaction"""

    def __init__(self, filename):
        self.filename = filename
        self._conn = sqlite3.connect(filename)

    def close(self):
        self._conn.close()

    def init(self):
        c = self._conn.cursor()
        c.execute(Q_INIT_PLAYLISTS_TABLE)
        c.execute(Q_INIT_PLAYLIST_TRACKS_TABLE)
        c.execute(Q_INIT_TRACKS_TABLE)

# add playlist

    def add_playlist(self, playlist_uri):
        """adds the playlist_uri with an empty name"""
        śelf._conn.cursor().execute(

# remove playlist

    def remove_playlist(self, playlist_uri):
        """removes the playlist from the playlists table and the
        playlist-tracks table, and sets the delete flag for every song
        that isn't in any playlist anymore after the playlist was deleted."""
        pass

# sync lists

    def get_playlists(self):
        pass

    def set_playlist_name(self, playlist_uri, name):
        """sets the playlist name"""
        pass

    def get_tracks(self, playlist_uri):
        """returns a list of track_uri of tracks which are in the playlist"""
        pass

    def add_track(self, playlist_uri, track_uri):
        """adds the track to the playlist and adds the track to the tracks
        table, respecively unsets the deleted-flag"""
        pass

    def remove_track(self, playlist_uri, track_uri):
        """removes a track from the playlist and sets the deleted flag on the
        track if it isn't in any other playlist"""
        pass

# infer youtube links

    def get_tracks_for_infer(self):
        """returns all the tracks that don't contain a link, are not ignored
        and are not deleted.  list of track_uri"""
        pass

    def set_track_link(self, track_uri, youtube_link):
        """sets the youtube_link for the track"""
        pass

# update files

    def get_deleted_tracks(self):
        """returns all tracks that carry the deleted-flag.  list of
        track_uri"""
        pass

    def get_tracks_for_download(self):
        """returns all tracks which are not ignored, not deleted and carry a
        youtube_link.  returns a list of (track_uri, youtube_link)"""
        pass
