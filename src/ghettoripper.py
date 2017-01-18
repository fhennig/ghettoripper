import argparse
import spotify
import db
import os
import logging
import youtube
import string
import re


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def valid_filename(s):
    valid_chars = "-_.()/ %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    filename = filename.replace('/', '-')
    return filename


def t_id(t_uri):
    return re.sub('spotify:track:', '', t_uri)


def add_playlist(db_file, playlist_uri):
    database = db.Database(db_file)
    database.add_playlist(playlist_uri)
    database.close()


def remove_playlist(db_file, playlist_uri):
    database = db.Database(db_file)
    database.remove_playlist(playlist_uri)
    database.close()


def sync(db_file, username):
    logger.info("Starting sync")
    database = db.Database(db_file)
    si = spotify.SpotifyInterface(username)
    p_uris = database.get_playlists()
    logger.info("Found %s playlists for sync", len(p_uris))
    for p_uri in p_uris:
        name, snapshot_id, new_tracks = si.get_playlist_name_and_tracks(p_uri)
        old_name, old_snapshot_id = database.get_playlist_info(p_uri)
        if snapshot_id == old_snapshot_id:
            logger.info("Playlist '%s' unchanged", name)
            continue
        database.set_playlist_info(p_uri, name, snapshot_id)
        database.remove_playlist_tracks(p_uri)
        for i, t in enumerate(new_tracks):
            database.add_track(p_uri, t, i + 1)
        logger.info("Playlist: '%s' updated", name)
    database.mark_removed_tracks()
    database.close()
    logger.info("Sync finished")


def infer(db_file, username):
    logger.info("Starting infer")
    database = db.Database(db_file)
    si = spotify.SpotifyInterface(username)
    t_uris = database.get_tracks_for_infer()
    logger.info("Found %s tracks for infer", len(t_uris))
    for t_uri in t_uris:
        if t_uri.startswith('spotify:local'):
            database.set_ignore_flag(t_uri, True)
            logger.info("Ignoring local track: %s", t_uri)
            continue
        q_str = si.get_track_query_string(t_uri)
        logger.info("Track query:  '%s' (%s)", q_str, t_uri)
        try:
            yt_link, yt_title = youtube.best_hit_for_query(q_str)
        except IndexError:
            database.set_ignore_flag(t_uri, True)
            logger.info("Ignoring track, no results found")
            continue
        database.set_track_link(t_uri, yt_link)
        logger.info("Track result: '%s' (%s)", yt_title, yt_link)
    database.close()
    logger.info("Infer finished")


def update_files(db_file, track_dir, username):
    logger.info("Updating files")
    database = db.Database(db_file)
    t_uris = database.get_deleted_tracks()
    si = spotify.SpotifyInterface(username)
    for t_uri in t_uris:
        os.remove(os.path.join(track_dir, t_id(t_uri) + '.mp3'))
    logger.info("Removed %s files", len(t_uris))
    t_infos = database.get_tracks_for_download()
    t_missing = [(t_uri, t_link) for (t_uri, t_link) in t_infos
                 if not os.path.exists(os.path.join(track_dir, t_id(t_uri) + '.mp3'))]
    logger.debug("t_infos: %s", t_infos)
    logger.debug("track_dir: %s", track_dir)
    logger.info("Found %s/%s tracks missing", len(t_missing), len(t_infos))
    for t_uri, yt_link in t_missing:
        path = os.path.join(track_dir, t_id(t_uri))
        mp3_path = path + ".mp3"
        youtube.download_video(yt_link, path)
        si.write_track_info(t_uri, mp3_path)
    logger.info("Files updated")


def set_link(db_file, t_uri, yt_link):
    database = db.Database(db_file)
    database.set_track_link(t_uri, yt_link)
    database.close()


def ignore_tracks(db_file, t_uris):
    database = db.Database(db_file)
    for t_uri in t_uris:
        database.set_ignore_flag(t_uri, True)
    logger.info("Ignored %s tracks", len(t_uris))
    database.close()


def unignore_tracks(db_file, t_uris):
    database = db.Database(db_file)
    for t_uri in t_uris:
        database.set_ignore_flag(t_uri, False)
    logger.info("Unignored %s tracks", len(t_uris))
    database.close()


def delete_ignored_tracks(db_file, tracks_dir):
    database = db.Database(db_file)
    t_uris = database.get_ignored_tracks()
    t_paths = [os.path.join(tracks_dir, t_id(t_uri) + ".mp3") for t_uri in t_uris]
    to_delete = [p for p in t_paths if os.path.exists(p)]
    logger.info("Ignored tracks: %s, to delete: %s", len(t_paths), len(to_delete))
    for t_p in to_delete:
        os.remove(t_p)
    database.close()
    logger.info("Removed tracks.")


def generate_playlist_files(db_file, tracks_dir, playlist_dir):
    """use_uris: if the playlist uris should be used for the name"""
    database = db.Database(db_file)
    p_uris = database.get_playlists()
    logger.info("%s playlists", len(p_uris))
    created_files = []
    for p_uri in p_uris:
        t_uris = database.get_tracks(p_uri)
        name, _ = database.get_playlist_info(p_uri)
        filename = valid_filename(name) + ".m3u"
        logger.info("writing playlist %s (%s)", p_uri, filename)
        filename = os.path.join(playlist_dir, filename)
        with open(filename, "w") as f:
            for t_uri in t_uris:
                f.write("../tracks/%s.mp3\n" % (t_id(t_uri)))
            created_files.append(filename)
    for f in os.listdir(playlist_dir):  # remove playlist files with old names
        f = os.path.join(playlist_dir, f)
        if f.endswith(".m3u") and os.path.isfile(f) and f not in created_files:
            logger.info("removing old file %s", f)
            os.remove(f)
    database.close()


def read_conf():
    conf = {}
    # access to os.environ might raise KeyError
    conf['username'] = os.environ['GHETTORIPPER_USERNAME']
    conf['basedir'] = os.environ['GHETTORIPPER_BASEDIR']
    conf['tracksdir'] = os.path.join(conf['basedir'], 'tracks')
    conf['listsdir'] = os.path.join(conf['basedir'], 'playlists')
    conf['dbfile'] = os.path.join(conf['basedir'], 'ghettoripper.sqlite')
    return conf


def init(conf):
    if not os.path.exists(conf['basedir']):
        logger.info('Creating base directory: %s', conf['basedir'])
        os.makedirs(conf['basedir'])
    if not os.path.exists(conf['tracksdir']):
        logger.info('Creating tracks directory: %s', conf['tracksdir'])
        os.makedirs(conf['tracksdir'])
    if not os.path.exists(conf['listsdir']):
        logger.info('Creating playlists directory: %s', conf['listsdir'])
        os.makedirs(conf['listsdir'])
    if not os.path.exists(conf['dbfile']):
        logger.info("Initializing database: %s", conf['dbfile'])
        database = db.Database(conf['dbfile'])
        database.init()
        database.close()
    # TODO it would be fancy if the spotipy cache file would be initialized here


def main():
    parser = argparse.ArgumentParser(description="Spotify Ripper, ghetto style")
    subparsers = parser.add_subparsers(dest="subcommand",
                                       help="sub-command help")

    p_add_list = subparsers.add_parser('add-list', help="Add a playlist to the database")
    p_add_list.add_argument("uri", help="The URI of the playlist")

    p_remove_list = subparsers.add_parser('rm-list', help="Remove a playlist from the database")
    p_remove_list.add_argument("uri", help="The URI of the playlist to remove")

    p_sync = subparsers.add_parser('sync', help="Synchronize tracklists and playlist names from spotify")

    p_infer = subparsers.add_parser('infer', help="Infer YouTube video links for the tracks")

    p_update_files = subparsers.add_parser('update-tracks', help="Download missing tracks and remove tracks that were deleted")

    p_genlists = subparsers.add_parser('update-lists', help="(Re)generate all playlist files")

    p_update = subparsers.add_parser('update', help="shortcut for: sync, infer, update-tracks, update-lists")
    
    p_ignore = subparsers.add_parser('ignore', help="Ignore the given track uris")
    p_ignore.add_argument('uri', nargs='+', help="The track uris to ignore")

    p_unignore = subparsers.add_parser('unignore', help="Unignore the given track uris")
    p_unignore.add_argument('uri', nargs='+', help="The track uris to unignore")

    p_del_ignored = subparsers.add_parser('delignored', help="Remove tracks that are ignored")

    args = parser.parse_args()
    logger.debug("args: %s", args)

    conf = read_conf()
    username = conf['username']
    db_path = conf['dbfile']
    track_dir = conf['tracksdir']
    playlists_dir = conf['listsdir']
    init(conf)

    cmd = args.subcommand

    if cmd == 'add-list':
        add_playlist(db_path, args.uri)
    elif cmd == 'rm-list':
        remove_playlist(db_path, args.uri)
    elif cmd == 'sync':
        sync(db_path, username)
    elif cmd == 'infer':
        infer(db_path, username)
    elif cmd == 'update-tracks':
        update_files(db_path, track_dir, username)
    elif cmd == 'update-lists':
        generate_playlist_files(db_path, track_dir, playlists_dir)
    elif cmd == 'update':
        sync(db_path, username)
        infer(db_path, username)
        update_files(db_path, track_dir, username)
        generate_playlist_files(db_path, track_dir, playlists_dir)
    elif cmd == 'ignore':
        ignore_tracks(db_path, args.uri)
    elif cmd == 'unignore':
        unignore_tracks(db_path, args.uri)
    elif cmd == 'delignored':
        delete_ignored_tracks(db_path, track_dir)


if __name__ == "__main__":
    main()
