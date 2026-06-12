import os
import asyncio
import requests
import json
import random
import subprocess
import pickle
import edge_tts
from groq import Groq
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

VIDEO_URLS = [
    "https://www.dropbox.com/scl/fi/efsgvqdzsxhmzrfklgg6d/Minecraft-Gameplay-Free-To-Use-Gameplay_720p.mp4?rlkey=ixo2sn2z8yshe48m1eo0b8mfp&st=p8r7eu0u&dl=1",
    "https://www.dropbox.com/scl/fi/438139ar9rjxnxi5by0z0/Wreckfest-2-Gameplay-Free-To-Use_720p-1.mp4?rlkey=igu67c3bmc94j4hlgatkg27ox&st=1nep6py6&dl=1",
]

def get_youtube_client():
    creds = pickle.load(open("token.pickle", "rb"))
    return build("youtube", "v3", credentials=creds)

def download_video(output="gameplay.mp4"):
    url = random.choice(VIDEO_URLS)
    response = requests.get(url, stream=True)
    with open(output, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    print("Video downloaded!")

def get_trending_topic():
    topics = [
        "a mysterious disappearance that shocked the world",
        "the scariest animal encounter ever recorded",
        "a secret government experiment gone wrong",
        "the most bizarre unsolved mystery in history",
        "a survival story that seems impossible",
    ]
    return random.choice(topics)

def generate_script(topic):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Write a 55-second YouTube Shorts script about: {topic}

Rules:
- Start with a shocking hook
- Keep sentences short
- End with a cliffhanger
- Also give me a title, description and 10 tags

Format as JSON:
{{"script": "...", "title": "...", "description": "...", "tags": ["tag1","tag2"]}}

Return ONLY the JSON, nothing else."""
        }]
    )
    text = response.choices[0].message.content
    return json.loads(text)

async def text_to_speech_with_timing(script, audio_file="voice.mp3", srt_file="subs.srt"):
    voice = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(script, voice)
    words = []
    with open(srt_file, "w") as srt:
        idx = 1
        async for chunk in communicate.stream():
            if chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10000000
                dur = chunk["duration"] / 10000000
                end = start + dur
                word = chunk["text"]
                words.append((start, end, word))
                srt.write(f"{idx}\n")
                srt.write(f"{format_time(start)} --> {format_time(end)}\n")
                srt.write(f"{word}\n\n")
                idx += 1
    communicate2 = edge_tts.Communicate(script, voice)
    await communicate2.save(audio_file)
    print("Voice and subtitles saved!")

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

import os
import asyncio
import requests
import json
import random
import subprocess
import pickle
import edge_tts
from groq import Groq
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

VIDEO_URLS = [
    "PASTE_FIRST_DROPBOX_LINK_HERE",
    "PASTE_SECOND_DROPBOX_LINK_HERE",
]

def get_youtube_client():
    creds = pickle.load(open("token.pickle", "rb"))
    return build("youtube", "v3", credentials=creds)

def download_video(output="gameplay.mp4"):
    url = random.choice(VIDEO_URLS)
    response = requests.get(url, stream=True)
    with open(output, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    print("Video downloaded!")

def get_trending_topic():
    topics = [
        "a mysterious disappearance that shocked the world",
        "the scariest animal encounter ever recorded",
        "a secret government experiment gone wrong",
        "the most bizarre unsolved mystery in history",
        "a survival story that seems impossible",
    ]
    return random.choice(topics)

def generate_script(topic):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Write a 55-second YouTube Shorts script about: {topic}

Rules:
- Start with a shocking hook
- Keep sentences short
- End with a cliffhanger
- Also give me a title, description and 10 tags

Format as JSON:
{{"script": "...", "title": "...", "description": "...", "tags": ["tag1","tag2"]}}

Return ONLY the JSON, nothing else."""
        }]
    )
    text = response.choices[0].message.content
    return json.loads(text)

async def text_to_speech_with_timing(script, audio_file="voice.mp3", srt_file="subs.srt"):
    voice = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(script, voice)
    words = []
    with open(srt_file, "w") as srt:
        idx = 1
        async for chunk in communicate.stream():
            if chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10000000
                dur = chunk["duration"] / 10000000
                end = start + dur
                word = chunk["text"]
                words.append((start, end, word))
                srt.write(f"{idx}\n")
                srt.write(f"{format_time(start)} --> {format_time(end)}\n")
                srt.write(f"{word}\n\n")
                idx += 1
    communicate2 = edge_tts.Communicate(script, voice)
    await communicate2.save(audio_file)
    print("Voice and subtitles saved!")

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def build_video():
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", "gameplay.mp4",
        "-i", "voice.mp3",
        "-map", "0:v",
        "-map", "1:a",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles=subs.srt:force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Bold=1,Outline=3,Shadow=1,Alignment=2,MarginV=120'",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-t", "60",
        "final_video.mp4"
    ]
    subprocess.run(cmd, check=True)
    print("Video built!")

def upload_to_youtube(youtube, title, description, tags):
    body = {
        "snippet": {
            "title": title,
            "description": description + "\n\n#Shorts",
            "tags": tags + ["Shorts", "viral"],
            "categoryId": "24"
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    media = MediaFileUpload("final_video.mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    print(f"✅ Uploaded! Video ID: {response['id']}")
    return response['id']

def main():
    print("🔥 Getting trending topic...")
    topic = get_trending_topic()
    print(f"Topic: {topic}")

    print("✍️ Generating script...")
    data = generate_script(topic)
    print(f"Title: {data['title']}")

    print("🎙️ Creating voiceover and subtitles...")
    asyncio.run(text_to_speech_with_timing(data["script"]))

    print("🎮 Downloading gameplay...")
    download_video()

    print("🎬 Building video with captions...")
    build_video()

    print("📤 Uploading to YouTube...")
    youtube = get_youtube_client()
    video_id = upload_to_youtube(
        youtube,
        data["title"],
        data["description"],
        data["tags"]
    )
    print(f"🎉 Live at: https://youtube.com/shorts/{video_id}")

if __name__ == "__main__":
    main()

def upload_to_youtube(youtube, title, description, tags):
    body = {
        "snippet": {
            "title": title,
            "description": description + "\n\n#Shorts",
            "tags": tags + ["Shorts", "viral"],
            "categoryId": "24"
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    media = MediaFileUpload("final_video.mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    print(f"✅ Uploaded! Video ID: {response['id']}")
    return response['id']

def main():
    print("🔥 Getting trending topic...")
    topic = get_trending_topic()
    print(f"Topic: {topic}")

    print("✍️ Generating script...")
    data = generate_script(topic)
    print(f"Title: {data['title']}")

    print("🎙️ Creating voiceover and subtitles...")
    asyncio.run(text_to_speech_with_timing(data["script"]))

    print("🎮 Downloading gameplay...")
    download_video()

    print("🎬 Building video with captions...")
    build_video()

    print("📤 Uploading to YouTube...")
    youtube = get_youtube_client()
    video_id = upload_to_youtube(
        youtube,
        data["title"],
        data["description"],
        data["tags"]
    )
    print(f"🎉 Live at: https://youtube.com/shorts/{video_id}")

if __name__ == "__main__":
    main()
