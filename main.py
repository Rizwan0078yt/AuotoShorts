import os
import asyncio
import requests
import json
import edge_tts
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def get_trending_topic():
    topics = [
        "a mysterious disappearance that shocked the world",
        "the scariest animal encounter ever recorded",
        "a secret government experiment gone wrong",
        "the most bizarre unsolved mystery in history",
        "a survival story that seems impossible",
    ]
    import random
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

Format your response as JSON like this:
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
    print(f"Voice saved: {filename}")

def main():
    print("🔥 Getting trending topic...")
    topic = get_trending_topic()
    print(f"Topic: {topic}")

    print("✍️ Generating script...")
    data = generate_script(topic)
    print(f"Title: {data['title']}")

    print("🎙️ Creating voiceover...")
    asyncio.run(text_to_speech(data["script"]))

    print("✅ Done! Script and voice ready.")
    print(f"Title: {data['title']}")
    print(f"Description: {data['description']}")
    print(f"Tags: {data['tags']}")

if __name__ == "__main__":
    main()
