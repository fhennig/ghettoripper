import spotipy
import spotipy.util as util
import re
import stagger


class SpotifyInterface:

    def __init__(self, username=None):
        """if username is given, authenticate, otherwise don't"""
        if username:
            token = util.prompt_for_user_token(username, scope="-")
            self.sp = spotipy.Spotify(auth=token)
        else:
            self.sp = spotipy.Spotify()

    def get_playlist_name_and_tracks(self, playlist_uri):
        """returns (name, [track_uri, track_uri, ...])"""
        user_uri = extract_userid_from_playlist_uri(playlist_uri)
        playlist = self.sp.user_playlist(user_uri, playlist_uri)
        tracklist = []
        for item in playlist["tracks"]["items"]:
            tracklist.append(item["track"]["uri"])
        return playlist["name"], playlist["snapshot_id"], tracklist

    def get_track_query_string(self, track_uri):
        track = self.sp.track(track_uri)
        artists = track['artists'][0]['name']
        for artist in track['artists'][1:]:
            artists += "; " + artist['name']
        return artists + " " + track['name']

    def write_track_info(self, t_uri, mp3_file):
        track = self.sp.track(t_uri)
        tag = stagger.read_tag(mp3_file)
        tag.title = track['name']
        artists = track['artists'][0]['name']
        for artist in track['artists'][1:]:
            artists += "; " + artist['name']
        tag.artist = artists
        tag.album = track['album']['name']
        album_artists = track['album']['artists'][0]['name']
        for artist in track['album']['artists'][1:]:
            album_artists += "; " + artist['name']
        tag.album_artist = album_artists
        tag.track = track['track_number']
        tag.write()


def extract_userid_from_playlist_uri(playlist_uri):
    return re.match("spotify:user:([^:]*):", playlist_uri).groups()[0]
