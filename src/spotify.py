import spotipy
import spotipy.util as util
import re
import track


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

    def get_track_info(self, t_uris):
        """reads multiple tracks into track objects"""
        tracks = self.sp.tracks(t_uris)["tracks"]
        result = []
        for t in tracks:
            tr = track.Track(t["uri"])
            tr.title = t["name"]
            artists = t['artists'][0]['name']
            for artist in t['artists'][1:]:
                artists += "; " + artist['name']
            tr.artist = artists
            tr.album = t['album']['name']
            album_artists = t['album']['artists'][0]['name']
            for artist in t['album']['artists'][1:]:
                album_artists += "; " + artist['name']
            tr.album_artist = album_artists
            tr.track_number = tf['track_number']
            result.append(tr)
        return result



def extract_userid_from_playlist_uri(playlist_uri):
    return re.match("spotify:user:([^:]*):", playlist_uri).groups()[0]
