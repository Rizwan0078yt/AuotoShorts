import os
import asyncio
import requests
import gdown
import json
import random
import subprocess
import edge_tts
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

VIDEO_IDS = [
    "1WqxvNGgmqfcGpRzGsmezF1TzxV6sxrGQ/view?usp=drive_link",
    "1r4oqa2lu4ILR-imTK4K9M4CF__0V-EFO/view?usp=drive_link",
]

def download_video(file_id, output="gameplay.mp4"):
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t"
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
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-af", "volume=0.3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-t", "60",
        "final_video.mp4"
    ]
    subprocess.run(cmd, check=True)
    print("Video built!")

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
    video_id = random.choice(VIDEO_IDS)
    download_video(video_id)

    print("🎬 Building video...")
    build_video()

    print("✅ Video ready!")
    print(f"Title: {data['title']}")
    print(f"Description: {data['description']}")
    print(f"Tags: {data['tags']}")

if __name__ == "__main__":
    main()
