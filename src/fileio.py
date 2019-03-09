import os
import re
import stagger
import unicodedata


class FileManager:

    def __init__(self, track_dir):
        self.track_dir = track_dir

    def short_track_uri(self, track_uri):
        return re.sub('spotify:track:', '', track_uri)

    def create_track_path(self, track_uri, track_title, no_ext=False):
        """Can create the track_path without the extension, because
        the extension is later added by the youtube dl module."""
        t_id = self.short_track_uri(track_uri)
        t_title = unicodedata.normalize('NFKD', track_title)
        t_title = re.sub('[^\w\s-]', '', t_title).strip().lower()
        t_title = re.sub('[-\s]+', '-', t_title)
        file_name = "{}_{}".format(t_id, t_title)
        path = os.path.join(self.track_dir, file_name)
        if no_ext:
            return path
        else:
            return path + ".mp3"

    def get_track_path(self, track_uri):
        print("track_uri: {}".format(track_uri))
        track_path = self.track_exists(track_uri)
        if track_path is None:
            raise Exception('Track does not exist')
        return track_path

    def track_exists(self, track_uri):
        """Takes the track uri and searches for the matching file.
        If a file is found its fully qualified filename is returned.
        Otherwise None is returned."""
        t_id = self.short_track_uri(track_uri)
        tracks = os.listdir(self.track_dir)
        for track in tracks:
            print(track)
            if track.startswith(t_id):
                return os.path.join(self.track_dir, track)
        return None

    def remove_track(self, t_uri):
        track = self.track_exists(t_uri)
        if track:
            os.remove(track)

    def write_track_info(self, track, track_file):
        tag = stagger.read_tag(track_file)
        tag.title = track.title
        tag.artist = track.artist
        tag.album = track.album
        tag.album_artist = track.album_artist
        tag.track = track.track_number
        tag.write()
