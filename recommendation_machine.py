#!/usr/bin/env python3
import os
import logging
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from argparse import ArgumentParser
from typing import Iterator, List, cast, Protocol

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
import dotenv

__version__ = "0.2.0"


logger = logging.getLogger("recommendation-machine")


@dataclass
class Song:
    youtube_link: str
    title: str
    artist: str


class GetSongs(Protocol):
    def get_songs(self, session: requests.Session) -> List[Song]:
        ...


class Recommendations:
    URL = "https://www.last.fm/music/+recommended/tracks"

    def get_songs(self, session: requests.Session) -> List[Song]:
        songs: List[Song] = []

        for page in range(1, 4):
            logger.info(f"Scraping page {page}")
            response = session.get(self.URL, params={"page": page})
            soup = BeautifulSoup(response.text, "lxml")
            logger.info(f"Scraping page {cast(Tag, soup.title).text}")

            for song in cast(
                Iterator[Tag], soup.find_all(class_="recommended-tracks-item")
            ):
                title = cast(Tag, song.find(itemprop="name")).text.strip()
                artist = cast(Tag, song.find(itemprop="byArtist")).text.strip()

                play_link = cast(
                    Tag | None, song.find(class_="desktop-playlink")
                )

                if play_link is None:
                    logger.info(
                        f'Skipping song "{title} - {artist}" without play link'
                    )
                    continue

                songs.append(Song(cast(str, play_link["href"]), title, artist))

        return songs


class Playlist:
    URL = "https://www.last.fm/user/_/playlists/%(playlist_id)d"
    playlist_id: int

    def __init__(self, playlist_id: int):
        super().__init__()

        self.playlist_id = playlist_id

    def get_songs(self, session: requests.Session) -> List[Song]:
        songs: List[Song] = []

        url = self.URL % { 'playlist_id': self.playlist_id }

        logger.info("Scraping {url}")

        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        title = cast(Tag, soup.find("h1")).text

        logger.info(f"Found playlist {title}")

        for button in cast(Iterator[Tag], soup.find_all(class_="chartlist-play-button")):
            title = cast(str, button["data-track-name"])
            artist = cast(str, button["data-artist-name"])
            play_link = cast(str, button["data-youtube-url"])

            songs.append(Song(play_link.strip(), title.strip(), artist.strip()))


        return songs

class Link:
    URL = "https://www.last.fm/%(page)s"
    page: str

    def __init__(self, page: str):
        super().__init__()

        self.page = page

    def get_songs(self, session: requests.Session) -> List[Song]:
        songs: List[Song] = []

        url = self.URL % { 'page': self.page }

        logger.info(f"Scraping {url}")

        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        title = cast(Tag, soup.find("h1")).text

        logger.info(f"Page {title}")

        for button in cast(Iterator[Tag], soup.find_all(class_="chartlist-play-button")):
            title = cast(str, button["data-track-name"])
            artist = cast(str, button["data-artist-name"])
            play_link = cast(str, button["data-youtube-url"])

            songs.append(Song(play_link.strip(), title.strip(), artist.strip()))


        return songs



def play(song_getter: GetSongs):
    logging.basicConfig(
        level=logging.DEBUG, format="[%(name)s] %(levelname)s: %(message)s"
    )

    dotenv.load_dotenv(Path(__file__).parent / ".env")
    session_id = os.getenv("LASTFM_SESSION_ID")
    watch_command = os.getenv("WATCH_COMMAND")

    if session_id is None:
        print("Environment variable LASTFM_SESSION_ID required.")
        return

    if watch_command is None:
        print("Environment variable WATCH_COMMAND required.")
        return

    songs: List[Song] = []

    with requests.Session() as session:
        session.cookies.set("sessionid", session_id)
        session.headers["user-agent"] = f"recommendation-machine {__version__}"

        songs = song_getter.get_songs(session)

    for song in songs:
        logger.info(f'Now playing song "{song.title} - {song.artist}"')
        try:
            cmd = watch_command % {"url": shlex.quote(song.youtube_link)}
            logger.debug(f"Running command {cmd}")
            subprocess.run(shlex.split(cmd), check=True)
        except subprocess.CalledProcessError as e:
            logger.error("Error running watch command: ", exc_info=e)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-l", "--loop", action="store_true", help="Infinitely loop"
    )

    subcommands = parser.add_subparsers(title="Play mode", required=True, dest="mode")

    recommendations = subcommands.add_parser(
        "recommendations", help="Play user's recommended tracks"
    )

    playlist = subcommands.add_parser(
        "playlist", help="Play specified playlist"
    )
    playlist.add_argument(
        "playlist_id",
        type=int,
        help="Playlist ID (https://last.fm/user/.../playlists/PLAYLIST_ID",
    )

    link = subcommands.add_parser("link", help="Play specified link")
    link.add_argument("page", type=str, help="last.fm/[page]")

    args = parser.parse_args()

    song_getter: GetSongs

    match args.mode:
        case "recommendations":
            song_getter = Recommendations()
        case "playlist":
            song_getter = Playlist(args.playlist_id)
        case "link":
            song_getter = Link(args.page)
        case other:
            raise Exception(f"unknown mode {other}")

    play(song_getter)

    while args.loop:
        play(song_getter)
