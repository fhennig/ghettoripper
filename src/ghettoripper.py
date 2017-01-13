import argparse
import spotify
import db
import os


def init(db_file, track_dir):
    database = db.Database(db_file)
    database.init()
    os.mkdirs(track_dir)
    database.close()


def add_playlist(db_file, playlist_uri):
    database = db.Database(db_file)
    database.add_playlist(playlist_uri)
    database.close()


def remove_playlist(db_file, playlist_uri):
    database = db.Database(db_file)
    database.remove_playlist(playlist_uri)
    database.close()


def sync(db_file, username):
    database = db.Database(db_file)
    si = spotify.SpotifyInterface(username)
    p_uris = database.get_playlists()
    for p_uri in p_uris:
        name, new_tracks = si.get_playlist_name_and_tracks(p_uri)
        db.set_playlist_name(p_uri, name)
        current_tracks = db.get_tracks(p_uri)
        added_tracks = [t for t in new_tracks if t not in current_tracks]
        deleted_tracks = [t for t in current_tracks if t not in new_tracks]
        for t in added_tracks:
            db.add_track(p_uri, t)
        for t in deleted_tracks:
            db.remove_track(p_uri, t)
    database.close()


def infer(db_file, username):
    pass


def update_files(db_file, track_dir):
    pass


def main():
    parser = argparse.ArgumentParser(description="Spotify Ripper, ghetto style")
    subparsers = parser.add_subparsers(dest="subcommand",
                                       help="sub-command help")

    p_init = subparsers.add_parser('init', help="Initialize database and directory structure")

    p_add_list = subparsers.add_parser('add-list', help="Add a playlist to the database")
    p_add_list.add_argument("uri", help="The URI of the playlist")

    p_remove_list = subparsers.add_parser('rm-list', help="Remove a playlist from the database")
    p_remove_list.add_argument("uri", help="The URI of the playlist to remove")

    p_sync = subparsers.add_parser('sync', help="Synchronize tracklists and playlist names from spotify")
    p_sync.add_argument("username", help="Your spotify username, required to read the data")

    p_infer = subparsers.add_parser('infer', help="Infer YouTube video links for the tracks")
    p_infer.add_argument("username", help="Your spotify username, required to read the data")

    p_update_files = subparsers.add_parser('update-files', help="Download missing tracks and remove tracks that were deleted")
    p_update_files.add_argument("username", help="Your spotify username, required to read the data")

    p_update = subparsers.add_parser('update', help="Syncs, infers links, updates files")
    p_update.add_argument("username", help="Your spotify username, required to read the data")

    args = parser.parse_args()

    db_path = "ghettoripper.db"
    track_dir = "tracks"
    cmd = args.subcommand

    if cmd == 'ini':
        init(db_path, track_dir)
    elif cmd == 'add-list':
        add_playlist(db_path, args.uri)
    elif cmd == 'rm-list':
        remove_playlist(db_path, args.uri)
    elif cmd == 'sync':
        sync(db_path, args.username)
    elif cmd == 'infer':
        infer(db_path, args.username)
    elif cmd == 'update-files':
        update_files(db_path, track_dir)
    elif cmd == 'update':
        sync(db_path, args.username)
        infer(db_path, args.username)
        update_files(db_path, track_dir)


if __name__ == "__main__":
    main()
