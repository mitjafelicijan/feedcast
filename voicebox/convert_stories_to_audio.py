import os
import sys
import copy
import sqlite3
import datetime
import base64
import openai
import dotenv
import logging

from feeds import feeds
from pydantic import BaseModel
from openai import OpenAI

script_name = os.path.basename(__file__)
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{script_name}] %(levelname)s - %(message)s")

dotenv.load_dotenv()
if os.getenv("OPENAI_KEY") is None:
    logging.error("OpenAI key not found!")
    sys.exit(1)

oai_client = openai.OpenAI(api_key = os.getenv("OPENAI_KEY"))
today = datetime.date.today().strftime("%Y-%m-%d")
tts_voice = "nova"

# SQLite connection stuff.
conn = sqlite3.connect("cache.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# System prompt for OpenAI.
sys_prompt = []
sys_prompt.append("Read this as a morning news radio newscaster and make it terse and short even if the article is long.")
sys_prompt.append("Avoid mentioning publications like Fox or CNN etc in the stories. Focus on the content of the story.")
sys_prompt.append("I should not be longer than 20 seconds.")

# Loop through all categories.
cur.execute("SELECT DISTINCT(category) AS category FROM stories WHERE cdate=?", (today,))
categories = cur.fetchall()
for category in categories:
    category = category["category"]

    # Create proper audio folders.
    audio_dir = f"audio/{today}/{category}/stories"
    try:
        os.makedirs(audio_dir, exist_ok=True)
    except:
        logging.error("Could not create audio directory %s", audio_dir)
        sys.exit(1)

    # Get stories from cache database.
    user_prompt = []
    cur.execute("SELECT * FROM stories WHERE cdate=? AND category=? AND selected=1 AND processed=0", (today, category))
    stories = cur.fetchall()
    for story in stories:
        try:
            prompt = copy.deepcopy(sys_prompt)
            prompt.append(f"Speak in a tone that is appropriate for category {category}.")
            completion = oai_client.chat.completions.create(
                model="gpt-4o-audio-preview",
                modalities=["text", "audio"],
                audio={"voice": tts_voice, "format": "mp3"},
                messages=[
                    { "role": "system", "content": "\n".join(prompt) },
                    { "role": "user", "content": story["summary"] }
                ],
            )

            audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)
            with open(f"{audio_dir}/{story['hash']}.mp3", "wb") as f:
                f.write(audio_bytes)

            cur.execute("UPDATE stories SET processed=1 WHERE hash=?", (story["hash"],))
            conn.commit()

            logging.info("Successfully created audio file for hash %s in category %s", story["hash"], category)
        except Exception as e:
            logging.error("Could not create audio file for hash %s with error %s", story["hash"], e)

conn.close()

