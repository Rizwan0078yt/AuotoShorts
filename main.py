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

async def text_to_speech(script, filename="voice.mp3"):
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(filename)
    print("Voice saved!")

def build_video():
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", "gameplay.mp4",
        "-i", "voice.mp3",
        "-map", "0:v",
        "-map", "1:a",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
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

    print("🎙️ Creating voiceover...")
    asyncio.run(text_to_speech(data["script"]))

    print("🎮 Downloading gameplay...")
    download_video()

    print("🎬 Building video...")
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
