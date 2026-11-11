from fileinput import filename
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from html.parser import HTMLParser
from pathlib import Path
from bs4 import BeautifulSoup

from mutagen import mp3

import json
import re
import datetime
import time
import requests
import SSLAdapter

DEFAULT_CIPHERS = ":".join(
    [
        "ECDHE+AESGCM",
        "ECDHE+CHACHA20",
        "DHE+CHACHA20",
        "ECDH+AESGCM",
        "DH+AESGCM",
        "ECDH+AES",
        "DH+AES",
        "RSA+AESGCM",
        "RSA+AES",
        "!aNULL",
        "!eNULL",
        "!MD5",
        "!DSS",
        "!AESCCM",
    ]
)
#next
#Typed dicts
#new class typed_dicts -> artist
#You will give artist as dict

#static variables. Change to custom folder/ target url
filepath = "Full path to bandcamp downloads folder here"
isolated_url = "Your Bandcamp URL here"

# Create the SSL context with the custom ciphers
# in SSLAdapter.py
#create ctx
ctx = SSLAdapter.create_urllib3_context()
ctx.load_default_certs()
ctx.set_ciphers(DEFAULT_CIPHERS)

#create session
session = requests.Session()
session.headers = {
    "User-Agent": f'AudioPhile/1.0'
}

#mount the SSLAdapter to the session with custom SSL
ssl_adapter = SSLAdapter.SSLAdapter(ssl_context=ctx)
session.mount("https://", ssl_adapter)

source_url = session.get(isolated_url, timeout=(10, 30))
source_url.raise_for_status()  # Raise an exception for HTTP errors

htmltext = source_url.text
source_soup = BeautifulSoup(htmltext, 'html.parser')

def create_directory(filename: str) -> None:
    if not os.path.exists(filename):
        print(f"Directory doesn't exist, creating: {filename}")
        os.mkdir(filename)
    else:
        print(f"Directory already exists: {filename}")

#scrape the bandcamp page
def get_bandcamp_tracklist(url: str) -> str:
    filtered_soup = re.findall(
        r'<script type="application/ld\+json">.*?</script>',
        str(source_soup),
        re.DOTALL,
    )
    if filtered_soup:
        print("Found ld+json object:")
        #print(filtered_soup)
    else:
        print("Nothing found. Invalid URL.")

    tracklist = re.findall(
        r'{"@type":"MusicRelease".*?}',
        str(filtered_soup),
        re.DOTALL,
    )
    return tracklist

#iterate through tracklist as json objects
#return dictionary of download links, names, metadata
#metadata: name(str), artist(str), album(str), url(str), release_date(str), genre(str), track_number(int))
def scrape_bandcamp_tracks(tracklist: list) -> list:
    download_list = []
    name_list = []

    track_dictionary = {}


    for json_track in tracklist:
        track = json.loads(json_track)
        track_id = track["@id"]

        #print the track ID for debugging purposes
        #print(track["@id"])

        print("JSON:")
        print (track)
        


        track_url = session.get(track_id)
        print(f"Track page status: {track_url.status_code}")
        track_url.raise_for_status()
        track_htmltext = track_url.text
        track_soup = BeautifulSoup(track_htmltext, 'html.parser')

        track_name = re.findall(
            r'<title>(.*?)</title>',
            str(track_soup),
            re.DOTALL,
        )

        #
        artist_name = re.findall(
            r'"byArtist"\s*:\s*\{[^{}]*?"name"\s*:\s*"([^"]+)"',
            str(track_soup),
            re.DOTALL,
        )

        #
        album_name = re.findall(
            r'"inAlbum"\s*:\s*\{[^{}]*?"name"\s*:\s*"([^"]+)"',
            str(track_soup),
            re.DOTALL,
        )

        tralbum_filtered_url = re.findall(
            r'"mp3-128"\s*:\s*"(https?://[^"]+)',
            str(track_soup),
            re.DOTALL,
        )

        #
        release_date = re.findall(
            r'"datePublished"\s*:"(.*?)"',
            str(track_soup),
            re.DOTALL,
        )

        #
        genre = re.findall(
            r'"genre"\s*:\s*"[^"]*/([^/"?]+)"',
            str(track_soup),
            re.DOTALL,
        )

        keywords = re.findall(
            r'"keywords"\s*:\s*\[(.*?)\]',
            str(track_soup),
            re.DOTALL,
        )

        print("Track Metadata:")
        print(f"Track Name: {track_name[0] if track_name else 'N/A'}")
        print(f"Artist Name: {artist_name[0] if artist_name else 'N/A'}")
        print(f"Album Name: {album_name[0] if album_name else 'N/A'}")
        print(f"Release Date: {release_date[0] if release_date else 'N/A'}")
        print(f"Genre: {genre[0] if genre else 'N/A'}")
        print(f"Keywords: {keywords[0] if keywords else 'N/A'}")
        print(f"Download URL: {tralbum_filtered_url[0] if tralbum_filtered_url else 'N/A'}")

        if tralbum_filtered_url and track_name:
            track_dictionary[track_name[0]] = {
                "artist": artist_name[0] if artist_name else 'N/A',
                "album": album_name[0] if album_name else 'N/A',
                "url": tralbum_filtered_url[0],
                "release_date": release_date[0] if release_date else 'N/A',
                "genre": genre[0] if genre else 'N/A',
                "keywords": keywords[0] if keywords else 'N/A',
            }
        else:
            print("No mp3-128 URL found.")
        print("\n")
        print("-----Track Dictionary:------")
        print("\n")
        print(track_dictionary)
    return track_dictionary

#variables List, str, List
def download(track_dictionary: dict, filepath: str, files_list: list) -> bool:
    attempts = 0
    skip = False
    download_loop = True
    failed_downloads = []

    album_name = list(track_dictionary.values())[0]["album"]

    for name in track_dictionary.keys():
        dict_artist = track_dictionary[name]["artist"]
        dict_album = track_dictionary[name]["album"]
        dict_url = track_dictionary[name]["url"]
        dict_release_date = track_dictionary[name]["release_date"]
        dict_genre = track_dictionary[name]["genre"]
        dict_keywords = track_dictionary[name]["keywords"]

        #filename .mp3
        full_filepath = filepath + dict_album + "/" + name + ".mp3"
        filename = filepath.rsplit('/', 1)[1]

        print(f"Downloading track: {name}")
        print(f"Artist: {dict_artist}")
        print(f"Album: {dict_album}")
        print(f"Release Date: {dict_release_date}")
        print(f"Genre: {dict_genre}")
        print(f"Keywords: {dict_keywords}")
        print(f"Download URL: {dict_url}")
        print(f"Full Filepath: {full_filepath}")

        while download_loop:
            try:
                print(f"Attempting to download: {name}")
                request = session.get(dict_url, stream=True)
                print(
                    f"Download status: {request.status_code}; "
                    f"final host: {urlparse(request.url).netloc}; "
                    f"content type: {request.headers.get('content-type')}"
                )
                response_code = request.status_code

                #check if response code is 200, if not, print error and break
                if response_code != 200:
                    print(f"Failed to download {name}, HTTP status code: {response_code}")
                    failed_downloads.append(name)
                    break

                file_length = int(request.headers.get('content-length', 0))
                total = int(file_length / 100)

                #check if file exists
                if os.path.exists(full_filepath):
                    print(f"File already exists: {full_filepath}")
                    skip = True
                    break
                elif os.path.exists(full_filepath[:-4]):
                    print(f"File: {filename[:-4]} already exists and is complete, skipping..")
                    skip = True
                    break
                with open(full_filepath, 'wb') as f:
                    if file_length is None:
                        f.write(request.content)
                    else:
                        dl = 0
                        for data in request.iter_content(chunk_size=total):
                            dl += len(data)
                            f.write(data)
                            done = int(50 * dl / file_length)
                            print(f"\r[{'=' * done}{' ' * (50 - done)}] {dl}/{file_length} bytes", end='')


                #check local filesize and redownload if needed
                local_size = os.path.getsize(full_filepath)
                if local_size != file_length and attempts != 3:
                    print(f"\nFile size mismatch: {local_size} != {file_length}, redownloading..")
                    attempts += 1
                    continue
                elif attempts == 3:
                    print("Maximum attempts reached, skipping..")
                    #cleanup file
                    os.remove(full_filepath)
                    break
                else:
                    print(f"\nDownload complete: {filename}")
                    break
            except Exception as e:
                print(e)
                print("Downloading failed..")
                download_loop = False
    print("Download loop complete.")
    print(f"Failed downloads: {failed_downloads}")
    return failed_downloads




tracklist = get_bandcamp_tracklist(source_url)

#Print tracklist
print("Tracklist:" + "\n")
print(tracklist)

track_dictionary = scrape_bandcamp_tracks(tracklist)

for key, value in track_dictionary.items():
    print("For track: " + key)
    print(value)
    print("\n")

album_name = list(track_dictionary.values())[0]["album"]
print(f"Album Name: {album_name}")

folder_path = os.path.join(filepath, album_name)
print(f"Folder Path: {folder_path}")
create_directory(folder_path)

if download(track_dictionary, filepath, tracklist) == []:
    print("All downloads complete.")
else:
    print("Some downloads failed.")
