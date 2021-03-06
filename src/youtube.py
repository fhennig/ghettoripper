# import youtube_dl
import requests
from bs4 import BeautifulSoup
import logging
import youtube_dl


log = logging.getLogger()


def best_hit_for_query(query_str):
    log.debug("YouTube query string: %s", query_str)
    yt_results_page = requests.get('https://www.youtube.com/results',
                                   params={'search_query': query_str})
    items_parse = BeautifulSoup(yt_results_page.text, "html.parser")
    first_result = items_parse.find_all(attrs={'class': 'yt-uix-tile-link'})[0]
    check = 1
    while not first_result['href'].find('channel') == -1 or not first_result['href'].find('googleads') == -1:
        first_result = items_parse.find_all(attrs={'class':'yt-uix-tile-link'})[check]
        check += 1
    del check
    full_link = "youtube.com" + first_result['href']
    log.debug("Found result: '%s' (%s)", first_result['title'], full_link)
    return full_link, first_result['title']


def download_video(link, output_path):
    """the link to download and the destination path,
    without the file extension!
    The extension is added according to the type of audio file."""
    ydl_opts = {'format': 'bestaudio',
                'outtmpl': output_path + '.%(ext)s',
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])


def test_best_hit():
    link, title = best_hit_for_query("Cari Lekebusch Farfalla")
    download_video(link, 'cari_test')


if __name__ == "__main__":
    test_best_hit()
