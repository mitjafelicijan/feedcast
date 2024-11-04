import os
import sys
import sqlite3
import datetime
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

conn = sqlite3.connect("cache.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# OpenAI structured response model.
class Story(BaseModel):
    title: str
    hash: str

class Stories(BaseModel):
    stories: list[Story]

# System prompt for OpenAI.
sys_prompt = []
sys_prompt.append("You are a content editor working for an online publication and you select only newsworthy and contextually unique stories.")
sys_prompt.append("Each line consists of story ID as a hash and a title.")
sys_prompt.append("Return back the list of just 20 unique stories.")

# Loop through all categories.
cur.execute("SELECT DISTINCT(category) AS category FROM stories WHERE cdate=?", (today,))
categories = cur.fetchall()
for category in categories:
    category = category["category"]

    # Get stories from cache database.
    user_prompt = []
    cur.execute("SELECT * FROM stories WHERE cdate=? AND category=?", (today, category))
    stories = cur.fetchall()
    for story in stories:
        user_prompt.append(", ".join((story["hash"], story["title"])))

    completion = oai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        response_format=Stories,
        messages=[
            {"role": "system", "content": "\n".join(sys_prompt)},
            {"role": "user", "content": "\n".join(user_prompt)}
        ],
    )

    # Update database by setting selected stories flag to 1.
    selected_stories = completion.choices[0].message.parsed.stories
    for story in selected_stories:
        try:
            logging.info(f"Selected: {category} - {story.title}")
            cur.execute("UPDATE stories SET selected=1 WHERE hash=?", (story.hash,))
            conn.commit()
        except:
            logging.critical("Error selecting: {story.title}")

conn.close()

