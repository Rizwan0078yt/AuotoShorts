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
print("Script started!")
client = Groq(api_key=GROQ_API_KEY)

WORK_DIR = "/home/runner/work/AuotoShorts/AuotoShorts"

VIDEO_URLS = [
    "https://www.dropbox.com/scl/fi/efsgvqdzsxhmzrfklgg6d/Minecraft-Gameplay-Free-To-Use-Gameplay_720p.mp4?rlkey=ixo2sn2z8yshe48m1eo0b8mfp&st=p8r7eu0u&dl=1",
    "https://www.dropbox.com/scl/fi/438139ar9rjxnxi5by0z0/Wreckfest-2-Gameplay-Free-To-Use_720p-1.mp4?rlkey=igu67c3bmc94j4hlgatkg27ox&st=1nep6py6&dl=1",
]

def get_youtube_client():
    creds = pickle.load(open(WORK_DIR + "/token.pickle", "rb"))
    return build("youtube", "v3", credentials=creds)

def download_video(output="gameplay.mp4"):
    url = random.choice(VIDEO_URLS)
    response = requests.get(url, stream=True)
    with open(WORK_DIR + "/" + output, "wb") as f:
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
            "content": "Write a 55-second YouTube Shorts script about: " + topic + "\n\nRules:\n- Start with a shocking hook\n- Keep sentences short\n- End with a cliffhanger\n- Also give me a title, description and 10 tags\n\nFormat as JSON:\n{\"script\": \"...\", \"title\": \"...\", \"description\": \"...\", \"tags\": [\"tag1\",\"tag2\"]}\n\nReturn ONLY the JSON, nothing else."
        }]
    )
    text = response.choices[0].message.content
    return json.loads(text)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2) + "," + str(ms).zfill(3)

async def create_voice_and_subs(script):
    voice = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(script, voice)
    words = []
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "WordBoundary":
            start = chunk["offset"] / 10000000
            dur = chunk["duration"] / 10000000
            end = start + dur
            words.append((start, end, chunk["text"]))
        elif chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
    print("Got " + str(len(words)) + " word timings and " + str(len(audio_chunks)) + " audio chunks")
    audio_path = WORK_DIR + "/voice.mp3"
    with open(audio_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)
    print("Voice saved!")
    srt_path = WORK_DIR + "/subs.srt"
    if len(words) > 0:
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, (start, end, word) in enumerate(words, 1):
                f.write(str(i) + "\n")
                f.write(format_time(start) + " --> " + format_time(end) + "\n")
                f.write(word + "\n\n")
        print("SRT created with timings!")
    else:
        words_list = script.split()
        duration_per_word = 0.4
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, word in enumerate(words_list):
                start = i * duration_per_word
                end = start + duration_per_word
                f.write(str(i + 1) + "\n")
                f.write(format_time(start) + " --> " + format_time(end) + "\n")
                f.write(word + "\n\n")
        print("SRT created from script words!")

def build_video():
    os.chdir(WORK_DIR)
    cmd1 = [
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
        "temp_video.mp4"
    ]
    subprocess.run(cmd1, check=True)
    print("Base video built!")
    srt_path = WORK_DIR + "/subs.srt"
    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        cmd2 = [
            "ffmpeg", "-y",
            "-i", "temp_video.mp4",
            "-vf", "subtitles=subs.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFF00,OutlineColour=&H00000000,Bold=1,Outline=3,Alignment=2,MarginV=150'",
            "-c:a", "copy",
            "final_video.mp4"
        ]
        subprocess.run(cmd2, check=True)
        print("Subtitles burned!")
    else:
        os.rename("temp_video.mp4", "final_video.mp4")
        print("No subtitles!")

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
    media = MediaFileUpload(
        WORK_DIR + "/final_video.mp4",
        chunksize=-1,
        resumable=True
    )
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    print("Uploaded! Video ID: " + response["id"])
    return response["id"]

def main():
    print("Getting trending topic...")
    topic = get_trending_topic()
    print("Topic: " + topic)
    print("Generating script...")
    data = generate_script(topic)
    print("Title: " + data["title"])
    print("Creating voice and subtitles...")
    asyncio.run(create_voice_and_subs(data["script"]))
    print("Downloading gameplay...")
    download_video()
    print("Building video...")
    build_video()
    print("Uploading to YouTube...")
    youtube = get_youtube_client()
    video_id = upload_to_youtube(
        youtube,
        data["title"],
        data["description"],
        data["tags"]
    )
    print("Live at: https://youtube.com/shorts/" + video_id)

main()
