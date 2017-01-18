# Ghettoripper

'Rip' Spotify playlists via youtube videos and update downloaded files.

## Configuration

Configuration is done by setting environment variables.

    SPOTIPY_CLIENT_ID='<YOUR_SPOTIFY_KEY_ID>'
    SPOTIPY_CLIENT_SECRET='<YOUR_SPOTIFY_KEY_SECRET>'
    SPOTIPY_REDIRECT_URI='http://localhost/'  # value doesn't matter
    GHETTORIPPER_USERNAME='<YOUR_SPOTIFY_USERNAME>'
    GHETTORIPPER_BASEDIR='/home/<YOUR_USERNAME>/Music/Ghettoripper'  # any directory you want
    
## Usage

- Call 'add-list <playlist URI>' for each playlist you want to download.
- Call 'update' 
- Enjoy files!

To download tracks which were added to the lists you downloaded, simply call 'update' again.

    usage: ghettoripper.py [-h]
                           {add-list,rm-list,sync,infer,update-tracks,update-lists,update,ignore,unignore,delignored}
                           ...
    
    positional arguments:
      {add-list,rm-list,sync,infer,update-tracks,update-lists,update,ignore,unignore,delignored}
                            sub-command help
        add-list            Add a playlist to the database
        rm-list             Remove a playlist from the database
        sync                Synchronize tracklists and playlist names from spotify
        infer               Infer YouTube video links for the tracks
        update-tracks       Download missing tracks and remove tracks that were
                            deleted
        update-lists        (Re)generate all playlist files
        update              shortcut for: sync, infer, update-tracks, update-lists
        ignore              Ignore the given track uris
        unignore            Unignore the given track uris
        delignored          Remove tracks that are ignored
    
    optional arguments:
      -h, --help            show this help message and exit

## File structure

    $GHETTORIPPER_BASEDIR
    ├── ghettoripper.sqlite
    ├── playlists
    │   ├── fertiger_Minimal.m3u
    │   ├── Minimal_Techno_-_Tech_House.m3u
    │   └── Techstep.m3u
    └── tracks
        ├── spotify:track:01whzdYiUQD9aK9TbX7EbZ.mp3
        ├── spotify:track:02nwohaKLZbtec9jG6V7lc.mp3
        ├── ...
