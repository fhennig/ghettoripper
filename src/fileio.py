import os
import re
import stagger
import track as tr


class FileManager:

    def __init__(self, track_dir):
        self.track_dir = track_dir

    def track_path(self, track_uri, no_ext=False):
        t_id = re.sub('spotify:track:', '', track_uri)
        if no_ext:
            return os.path.join(self.track_dir, t_id)
        else:
            return os.path.join(self.track_dir, t_id + ".mp3")

    def track_exists(self, track_uri):
        return os.path.exists(self.track_path(track_uri))

    def remove_track(self, t_uri):
        if self.track_exists(t_uri):
            os.remove(self.track_path(t_uri))

    def write_track_info(self, track):
        tag = stagger.read_tag(self.track_path(track.uri))
        tag.title = track.title
        tag.artist = track.artist
        tag.album = track.album
        tag.album_artist = track.album_artist
        tag.track = track.track_number
        tag.write()
