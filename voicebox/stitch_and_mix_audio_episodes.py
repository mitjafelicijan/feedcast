import os
import sys
import copy
import sqlite3
import datetime
import dotenv
import logging
import eyed3

from pydub import AudioSegment

script_name = os.path.basename(__file__)
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{script_name}] %(levelname)s - %(message)s")

today = datetime.date.today().strftime("%Y-%m-%d")

# SQLite connection stuff.
conn = sqlite3.connect("cache.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Effects etc.
bumper = AudioSegment.from_mp3("effects/bumper.mp3")
jingle = AudioSegment.from_mp3("effects/jingle.mp3")

# Loop through all categories.
cur.execute("SELECT DISTINCT(category) AS category FROM stories WHERE cdate=?", (today,))
categories = cur.fetchall()
for category in categories:
    category = category["category"]

    # Creates a fresh episode and adds jingle at start.
    episode = copy.deepcopy(jingle)

    # Create proper audio folders.
    audio_dir = f"audio/{today}/{category}"

    # Get stories from cache database.
    user_prompt = []
    cur.execute("SELECT hash FROM stories WHERE cdate=? AND category=? AND selected=1 AND processed=1", (today, category))
    stories = cur.fetchall()
    for story in stories:
        audio_file = f"{audio_dir}/stories/{story['hash']}.mp3"
        if os.path.exists(audio_file):
            episode += AudioSegment.from_mp3(audio_file)
            episode += (bumper - 4)

    # Export full episode on disk.
    episode_file = f"{audio_dir}/episode-{today}-{category}.mp3"
    episode.export(episode_file, format="mp3", bitrate="192k")

    # Add metadata to episode.
    category_title = category.replace("-", " ").title()
    audiofile = eyed3.load(episode_file)
    audiofile.tag.artist = "Feedcast"
    audiofile.tag.album = category_title
    audiofile.tag.album_artist = "Feedcast"
    audiofile.tag.title = f"{category_title}: Episode {today}"
    audiofile.tag.release_date = eyed3.core.Date.parse(today)
    audiofile.tag.recording_date = eyed3.core.Date.parse(today)
    audiofile.tag.save()

