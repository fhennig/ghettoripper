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
(uri TEXT PRIMARY KEY,
 youtube_link TEXT,
 ignore_flag INTEGER,
 deleted_flag INTEGER)
""".strip()

Q_INSERT_PLAYLIST = """
INSERT INTO playlists (uri, name)
VALUES (?, ?)
""".strip()

Q_REMOVE_PLAYLIST_1 = """
DELETE FROM playlists
WHERE uri = ?
""".strip()

Q_REMOVE_PLAYLIST_2 = """
DELETE FROM playlisttracks
WHERE playlist_uri = ?
""".strip()

Q_REMOVE_PLAYLIST_3 = """
UPDATE tracks
SET deleted_flag = 1
WHERE NOT EXISTS
(SELECT track_uri FROM playlisttracks
 WHERE tracks.uri = playlisttracks.track_uri)
""".strip()

Q_SELECT_PLAYLIST_URIS = """
SELECT uri FROM playlists
""".strip()

Q_SET_PLAYLIST_NAME = """
UPDATE playlists
SET name = ?
WHERE playlists.uri = ?
""".strip()

Q_GET_PLAYLIST_TRACKS = """
SELECT track_uri FROM playlisttracks
WHERE playlisttracks.playlist_uri = ?
""".strip()

Q_ADD_PLAYLIST_TRACK = """
INSERT INTO playlisttracks (playlist_uri, track_uri)
VALUES (?, ?)
""".strip()

Q_ADD_TRACK_OR_UPDATE = """
INSERT OR REPLACE INTO tracks (uri, youtube_link, ignore_flag, deleted_flag)
VALUES (?,
        COALESCE((SELECT youtube_link FROM tracks where uri = ?), ''),
        COALESCE((SELECT ignore_flag FROM tracks where uri = ?), 0),
        0)
""".strip()

Q_REMOVE_PLAYLIST_TRACK = """
DELETE FROM playlisttracks
WHERE playlisttracks.playlist_uri = ? AND playlisttracks.track_uri = ?
""".strip()

Q_MARK_TRACK_AS_DELETED = """
UPDATE tracks
set deleted_flag = 1
WHERE tracks.uri = ?
""".strip()

Q_GET_TRACKS_FOR_INFER = """
SELECT uri from tracks
WHERE youtube_link = "" AND ignore_flag = 0 AND deleted_flag = 0
""".strip()

Q_SET_TRACK_LINK = """
UPDATE tracks
SET youtube_link = ?
WHERE tracks.uri = ?
""".strip()

Q_GET_DELETED_TRACKS = """
SELECT uri FROM tracks
WHERE tracks.deleted_flag = 1
""".strip()

Q_GET_TRACKS_FOR_DOWNLOAD = """
SELECT uri, youtube_link FROM tracks
WHERE tracks.youtube_link != ""
  AND tracks.ignore_flag = 0
  AND tracks.deleted_flag = 0
""".strip()


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
        c = self._conn.cursor()
        c.execute(Q_INSERT_PLAYLIST, (playlist_uri, ""))
        c.close()
        self._conn.commit()

# remove playlist

    def remove_playlist(self, playlist_uri):
        """removes the playlist from the playlists table and the
        playlist-tracks table, and sets the delete flag for every song
        that isn't in any playlist anymore after the playlist was deleted."""
        c = self._conn.cursor()
        c.execute(Q_REMOVE_PLAYLIST_1, (playlist_uri,))
        c.execute(Q_REMOVE_PLAYLIST_2, (playlist_uri,))
        c.execute(Q_REMOVE_PLAYLIST_3)
        c.close()
        self._conn.commit()

# sync lists

    def get_playlists(self):
        """return a list of playlist_uris"""
        c = self._conn.cursor()
        c2 = c.execute(Q_SELECT_PLAYLIST_URIS)
        uris = [t[0] for t in c2.fetchall()]
        c.close()
        c2.close()
        self._conn.commit()
        return uris

    def set_playlist_name(self, playlist_uri, name):
        """sets the playlist name"""
        c = self._conn.cursor()
        c.execute(Q_SET_PLAYLIST_NAME, (name, playlist_uri))
        c.close()
        self._conn.commit()

    def get_tracks(self, playlist_uri):
        """returns a list of track_uri of tracks which are in the playlist"""
        c = self._conn.cursor()
        c2 = c.execute(Q_GET_PLAYLIST_TRACKS, (playlist_uri,))
        uris = [t[0] for t in c2.fetchall()]
        c.close()
        c2.close()
        self._conn.commit()
        return uris

    def add_track(self, playlist_uri, track_uri):
        """adds the track to the playlist and adds the track to the tracks
        table, respectively unsets the deleted-flag"""
        c = self._conn.cursor()
        c.execute(Q_ADD_PLAYLIST_TRACK, (playlist_uri, track_uri))
        c.execute(Q_ADD_TRACK_OR_UPDATE, (track_uri, track_uri, track_uri))
        c.close()
        self._conn.commit()

    def remove_track(self, playlist_uri, track_uri):
        """removes a track from the playlist and sets the deleted flag on the
        track if it isn't in any other playlist"""
        c = self._conn.cursor()
        c.execute(Q_REMOVE_PLAYLIST_TRACK, (playlist_uri, track_uri))
        c.execute(Q_MARK_TRACK_AS_DELETED, (track_uri, ))
        c.close()
        self._conn.commit()

# infer youtube links

    def get_tracks_for_infer(self):
        """returns all the tracks that don't contain a link, are not ignored
        and are not deleted.  list of track_uri"""
        c = self._conn.cursor()
        c2 = c.execute(Q_GET_TRACKS_FOR_INFER)
        uris = [t[0] for t in c2.fetchall()]
        c.close()
        c2.close()
        self._conn.commit()
        return uris

    def set_track_link(self, track_uri, youtube_link):
        """sets the youtube_link for the track"""
        c = self._conn.cursor()
        c.execute(Q_SET_TRACK_LINK, (youtube_link, track_uri))
        c.close()
        self._conn.commit()

# update files

    def get_deleted_tracks(self):
        """returns all tracks that carry the deleted-flag.  list of
        track_uri"""
        c = self._conn.cursor()
        c2 = c.execute(Q_GET_DELETED_TRACKS)
        uris = [t[0] for t in c2.fetchall()]
        c.close()
        c2.close()
        self._conn.commit()
        return uris

    def get_tracks_for_download(self):
        """returns all tracks which are not ignored, not deleted and carry a
        youtube_link.  returns a list of (track_uri, youtube_link)"""
        c = self._conn.cursor()
        c2 = c.execute(Q_GET_TRACKS_FOR_DOWNLOAD)
        uris = [(t[0], t[1]) for t in c2.fetchall()]
        c.close()
        c2.close()
        self._conn.commit()
        return uris
