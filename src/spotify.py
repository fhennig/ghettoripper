import spotipy
import spotipy.util as util
import re


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
        return playlist["name"], tracklist

    # TODO can be extended for BPM, genre etc.
    def get_track_info(self, track_uri):
        track = self.sp.track(track_uri)
        info = {}
        info['title'] = track['name']
        artists = track['artists'][0]['name']
        for artist in track['artists'][1:]:
            artists += "; " + artist['name']
        info['artist'] = artists
        info['album'] = track['album']['name']
        album_artists = track['album']['artists'][0]['name']
        for artist in track['album']['artists'][1:]:
            album_artists += "; " + artist['name']
        info['album_artist'] = album_artists
        info['track_number'] = track['track_number']
        return info


def extract_userid_from_playlist_uri(playlist_uri):
    return re.match("spotify:user:([0-9]*):", playlist_uri).groups()[0]
