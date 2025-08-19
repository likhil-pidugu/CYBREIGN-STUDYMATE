import edge_tts
import asyncio

async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text=text, voice="en-IN-PrabhatNeural")
    await communicate.save(output_file)

asyncio.run(generate_tts("hi hello bye", "output.mp3"))
