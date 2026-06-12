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

WORK_DIR = "/home/runner/work/AuotoShorts/AuotoShorts"

def get_youtube_client():
    creds = pickle.load(open(f"{WORK_DIR}/token.pickle", "rb"))
    return build("youtube", "v3", credentials=creds)

def download_video(output="gameplay.mp4"):
    url = random.choice(VIDEO_URLS)
    response = requests.get(url, stream=True)
    with open(f"{WORK_DIR}/{output}", "wb") as f:
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

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

async def create_voice_and_subs(script):
    voice = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(script, voice)
    words = []
    async for chunk in communicate.stream():
        if chunk["type"] == "WordBoundary":
            start = chunk["offset"] / 10000000
            dur = chunk["duration"] / 10000000
            end = start + dur
            words.append((start, end, chunk["text"]))
    srt_path = f"{WORK_DIR}/subs.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, end, word) in enumerate(words, 1):
            f.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{word}\n\n")
    print(f"SRT created with {len(words)} words at {srt_path}")
    communicate2 = edge_tts.Communicate(script, voice)
    await communicate2.save(f"{WORK_DIR}/voice.mp3")
    print("Voice saved!")

def build_video():
    gameplay = f"{WORK_DIR}/gameplay.mp4"
    voice = f"{WORK_DIR}/voice.mp3"
    subs = f"{WORK_DIR}/subs.srt"
    temp = f"{WORK_DIR}/temp_video.mp4"
    final = f"{WORK_DIR}/final_video.mp4"

    # Step 1 — merge gameplay + voice
    cmd1 = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", gameplay,
        "-i", voice,
        "-map", "0:v",
        "-map", "1:a",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-t", "60",
        temp
    ]
    subprocess.run(cmd1, check=True)
    print("Base video built!")

    # Step 2 — burn subtitles
    cmd2 = [
        "ffmpeg", "-y",
        "-i", temp,
        "-vf", f"subtitles={subs}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFF00,OutlineColour=&H00000000,Bold=1,Outline=3,Alignment=2,MarginV=150'",
        "-c:a", "copy",
        final
    ]
    subprocess.run(cmd2, check=True)
    print("Subtitles burned!")

def upload_to_youtube(youtube, title, description, tags):
    final = f"{WORK_DIR}/final_video.mp4"
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
    media = MediaFileUpload(final, chunksize=-1, resumable=True)
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
    asyncio.run(create_voice_and_subs(data["script"]))

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
