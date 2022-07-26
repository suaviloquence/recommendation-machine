#!/usr/bin/env python3
import os
import logging
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, cast

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
import dotenv

__version__ = "0.1.1"

URL = "https://www.last.fm/music/+recommended/tracks"

logger = logging.getLogger("recommendation-machine")


@dataclass
class Song:
    youtube_link: str
    title: str
    artist: str


def main():
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

        for page in range(1, 4):
            logger.info(f"Scraping page {page}")
            response = session.get(URL, params={"page": page})
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

    for song in songs:
        logger.info(f'Now playing song "{song.title} - {song.artist}"')
        try:
            cmd = watch_command % {"url": shlex.quote(song.youtube_link)}
            logger.debug(f"Running command {cmd}")
            subprocess.run(shlex.split(cmd), check=True)
        except subprocess.CalledProcessError as e:
            logger.error("Error running watch command: ", exc_info=e)


if __name__ == "__main__":
    main()
