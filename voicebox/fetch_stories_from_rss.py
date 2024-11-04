import os
import sys
import feedparser
import requests
import hashlib
import readability
import html2text
import urllib.parse
import sqlite3
import datetime
import dotenv
import logging

from feeds import feeds

script_name = os.path.basename(__file__)
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{script_name}] %(levelname)s - %(message)s")

def clean_html_tags(html_string):
    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = True
    clean_string = h.handle(html_string)
    return clean_string

dotenv.load_dotenv()
if os.getenv("OPENAI_KEY") is None:
    logging.error("OpenAI key not found!")
    sys.exit(1)

# SQLite connection stuff.
conn = sqlite3.connect("cache.db")
cur = conn.cursor()

today = datetime.date.today().strftime("%Y-%m-%d")

cur.execute("""
    CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY,
            hash TEXT UNIQUE,
            link TEXT,
            title TEXT,
            summary TEXT,
            cdate TEXT,
            domain TEXT,
            selected INT DEFAULT 0,
            processed INT DEFAULT 0,
            category TEXT
    )
""")

for category in feeds:
    feed_urls = feeds[category]

    for feed_url in feed_urls:
        doc = feedparser.parse(feed_url)
        domain = urllib.parse.urlparse(feed_url).netloc

        for entry in doc.entries:
            entry_html = requests.get(entry.link)
            entry_doc = readability.Document(entry_html.content)
            entry_hash = hashlib.md5(entry.link.encode()).hexdigest()
            entry_summary = clean_html_tags(entry_doc.summary())

            try:
                logging.info(f"New entry: {entry_doc.title()}")
                cur.execute("INSERT INTO stories(hash, link, title, summary, cdate, domain, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (entry_hash, entry.link, entry.title, entry_summary, today, domain,category,))
                conn.commit()
            except sqlite3.IntegrityError:
                logging.error(f"Already in database: {entry_doc.title()}")

conn.close()

