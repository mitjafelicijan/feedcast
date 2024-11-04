import os
import sys
import sqlite3
import datetime
import openai
import dotenv
import logging

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

# Get stories from cache database.
user_prompt = []
cur.execute("SELECT * FROM stories WHERE cdate=?", (today,))
rows = cur.fetchall()
for row in rows:
    user_prompt.append(", ".join((row["hash"], row["title"])))

# Make call to OpenAI to get unique stories out.
class Story(BaseModel):
    title: str
    hash: str

class Stories(BaseModel):
    stories: list[Story]

sys_prompt = []
sys_prompt.append("You are a content editor working for an online publication and you select only newsworthy and contextually unique stories.")
sys_prompt.append("Each line consists of story ID as a hash and a title.")
sys_prompt.append("Return back the list of just 20 unique stories.")

completion = oai_client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    response_format=Stories,
    messages=[
        {"role": "system", "content": "\n".join(sys_prompt)},
        {"role": "user", "content": "\n".join(user_prompt)}
    ],
)

# Update database by setting selected stories flag to 1.
stories = completion.choices[0].message.parsed.stories
for story in stories:
    try:
        logging.info(f"Selected: {story.title}")
        cur.execute("UPDATE stories SET selected=1 WHERE hash=?", (story.hash,))
        conn.commit()
    except:
        logging.critical("Error selecting: {story.title}")

conn.close()

