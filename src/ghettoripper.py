import argparse
import spotify
import db
import os
import logging
import youtube


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


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
        yt_link, yt_title = youtube.best_hit_for_query(q_str)
        database.set_track_link(t_uri, yt_link)
        logger.info("Track query: '%s', result: '%s' (%s)",
                    q_str, yt_link, yt_title)
    database.close()
    logger.info("Infer finished")


def update_files(db_file, track_dir, username):
    logger.info("Updating files")
    database = db.Database(db_file)
    t_uris = database.get_deleted_tracks()
    si = spotify.SpotifyInterface(username)
    for t_uri in t_uris:
        os.remove(os.path.join(track_dir, t_uri + '.mp3'))
    logger.info("Removed %s files", len(t_uris))
    t_infos = database.get_tracks_for_download()
    t_missing = [(t_uri, t_link) for (t_uri, t_link) in t_infos
                 if not os.path.exists(os.path.join(track_dir, t_uri + '.mp3'))]
    logger.debug("t_infos: %s", t_infos)
    logger.debug("track_dir: %s", track_dir)
    logger.info("Found %s/%s tracks missing", len(t_missing), len(t_infos))
    for t_uri, yt_link in t_missing:
        path = os.path.join(track_dir, t_uri)
        mp3_path = path + ".mp3"
        youtube.download_video(yt_link, path)
        si.write_track_info(t_uri, mp3_path)
    logger.info("Files updated")


def read_conf():
    conf = {}
    # access to os.environ might raise KeyError
    conf['username'] = os.environ['GHETTORIPPER_USERNAME']
    conf['basedir'] = os.environ['GHETTORIPPER_BASEDIR']
    conf['tracksdir'] = os.path.join(conf['basedir'], 'tracks')
    conf['playlistsdir'] = os.path.join(conf['basedir'], 'playlists')
    conf['dbfile'] = os.path.join(conf['basedir'], 'ghettoripper.sqlite')
    return conf


def init(conf):
    if not os.path.exists(conf['basedir']):
        logger.info('Creating base directory: %s', conf['basedir'])
        os.makedirs(conf['basedir'])
    if not os.path.exists(conf['tracksdir']):
        logger.info('Creating tracks directory: %s', conf['tracksdir'])
        os.makedirs(conf['tracksdir'])
    if not os.path.exists(conf['playlistsdir']):
        logger.info('Creating playlists directory: %s', conf['playlistsdir'])
        os.makedirs(conf['playlistsdir'])
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

    p_update_files = subparsers.add_parser('update-files', help="Download missing tracks and remove tracks that were deleted")

    p_update = subparsers.add_parser('update', help="Syncs, infers links, updates files")

    args = parser.parse_args()
    logger.debug("args: %s", args)

    conf = read_conf()
    username = conf['username']
    db_path = conf['dbfile']
    track_dir = conf['tracksdir']
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
    elif cmd == 'update-files':
        update_files(db_path, track_dir, username)
    elif cmd == 'update':
        sync(db_path, username)
        infer(db_path, username)
        update_files(db_path, track_dir)


if __name__ == "__main__":
    main()
