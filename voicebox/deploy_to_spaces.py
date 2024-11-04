import os
import sys
import json
import sqlite3
import urllib.parse
import datetime
import dotenv
import logging

from boto3 import session
from botocore.client import Config

script_name = os.path.basename(__file__)
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{script_name}] %(levelname)s - %(message)s")

dotenv.load_dotenv()
if os.getenv("DO_ACCESS_ID") is None:
    logging.error("DigitalOcean keys not found!")
    sys.exit(1)

bucket = os.getenv("DO_BUCKET")
region = os.getenv("DO_REGION")
today = datetime.date.today().strftime("%Y-%m-%d")
api_object = {
    "created": today,
    "featured": [],
    "categories": [],
}

# SQLite connection stuff.
conn = sqlite3.connect("cache.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# S3 stuff.
session = session.Session()
client = session.client("s3",
    region_name=os.getenv("DO_REGION"),
    endpoint_url=f"https://{region}.digitaloceanspaces.com",
    aws_access_key_id=os.getenv("DO_ACCESS_ID"),
    aws_secret_access_key=os.getenv("DO_SECRET_KEY"),
)

# Loop through all categories.
cur.execute("SELECT DISTINCT(category) AS category FROM stories WHERE cdate=?", (today,))
categories = cur.fetchall()
for category in categories:
    category = category["category"]

    api_category = {
        "title": category.replace("-", " ").title(),
        "key": category,
        "audio": f"https://{bucket}.{region}.digitaloceanspaces.com/feedcast/episodes/episode-{today}-{category}.mp3",
        "sources": [],
    }

    # Create proper audio folders.
    audio_dir = f"audio/{today}/{category}"

    episode_file = f"audio/{today}/{category}/episode-{today}-{category}.mp3"
    if os.path.exists(episode_file):
        cur.execute("SELECT * FROM stories WHERE cdate=? AND category=? AND selected=1 AND processed=1", (today, category))
        stories = cur.fetchall()
        for story in stories:
            domain = urllib.parse.urlparse(story["link"]).netloc
            api_category["sources"].append({
                "title": story["title"],
                "link": story["link"],
                "domain": domain,
            })

        client.upload_file(f"audio/{today}/{category}/episode-{today}-{category}.mp3", bucket, f"feedcast/episodes/episode-{today}-{category}.mp3")
        client.put_object_acl(Bucket=bucket, Key=f"feedcast/episodes/episode-{today}-{category}.mp3", ACL="public-read")

        api_object["categories"].append(api_category)
        logging.info("Episode %s has been uploaded", episode_file)
    else:
        print("file not exist")

# Saving API content JSON locally.
with open("api_object.json", "w") as file:
    json.dump(api_object, file, indent=4)

# Uploading api content JSON.
client.upload_file("api_object.json", bucket, "feedcast/content/today.json")
client.put_object_acl(Bucket=bucket, Key="feedcast/content/today.json", ACL="public-read")
client.upload_file("api_object.json", bucket, f"feedcast/content/content-{today}.json")
client.put_object_acl(Bucket=bucket, Key=f"feedcast/content/content-{today}.json", ACL="public-read")
logging.info("API content JSON has been uploaded")

conn.close()

