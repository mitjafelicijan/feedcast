import requests
import html2text
import openai
import base64
from pathlib import Path
from readability import Document
import config

openai.api_key = config.OPENAI_KEY
client = openai.OpenAI(api_key = config.OPENAI_KEY)

def clean_html_tags(html_string):
    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = True
    clean_string = h.handle(html_string)
    return clean_string

def summarize_text(text):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            { "role": "system", "content": config.OPENAI_SUMMARY_SYSTEM_PROMPT },
            { "role": "user", "content": text },
        ]
    )
    return completion.choices[0].message.content



def summary_to_mp3(tts_text, tts_voice, output_file):
    completion = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": tts_voice, "format": "mp3"},
        messages=[
            { "role": "system", "content": config.OPENAI_AUDIO_SYSTEM_PROMPT },
            { "role": "user", "content": tts_text }
        ],
    )

    wav_bytes = base64.b64decode(completion.choices[0].message.audio.data)
    with open(f"{tts_voice}-{output_file}", "wb") as f:
        f.write(wav_bytes)

def text_to_mp3(tts_text, tts_voice, output_file):
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=tts_voice,
        input=tts_text,
    )

    response.write_to_file(f"{tts_voice}-{output_file}")

url = "https://mitjafelicijan.com/the-abysmal-state-of-gnu-linux-and-a-case-against-shared-object-libraries.html"
url = "https://edition.cnn.com/2024/11/03/politics/donald-trump-disputing-election-results/index.html"
url = "https://www.cnbc.com/2024/11/02/election-mentions-jump-on-company-conference-calls-as-nov-5-approaches.html"
url = "https://www.cnbc.com/2024/11/03/24-year-old-was-laid-off-from-her-6-figure-tech-jobnow-she-shucks-oysters-for-parties.html"
url = "https://www.cnbc.com/2024/11/03/nearly-1-billion-has-been-spent-on-political-ads-over-the-last-week.html"

response = requests.get(url)
doc = Document(response.content)
title = doc.title()
summary = clean_html_tags(doc.summary())
# summerized_summary = summarize_text(summary)
print(title)
print("*" * 100)
print(summary)
# print("*" * 100)
# print(summerized_summary)

voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
for voice in voices:
    print(f"- {voice}")
    summary_to_mp3(f"{title}\n{summary}", voice, "story-segment.mp3")

# text_to_mp3(title, voice, "story-title.mp3")
# summary_to_mp3(summary, voice, "story-summary.mp3")
# summary_to_mp3(f"{title}\n{summary}", voice, "story-all.mp3")


