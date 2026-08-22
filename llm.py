from google import genai
import os
from dotenv import load_dotenv
load_dotenv()
import base64

client = genai.Client(api_key=os.getenv("API_KEY"))
path = r"""C:\Users\liaml\Downloads\square_waveform.png"""
with open(path, "rb") as image_file:
    image_bytes = image_file.read()

with open("system.md", "r", encoding="utf-8") as file:
    system_instruction = file.read()

user_prompt = input("What would you like described? ")

interaction = client.interactions.create(
    model="gemini-3.5-flash",
    system_instruction=system_instruction,
    input=[
        {"type": "text", "text": user_prompt},
        {
            "type": "image",
            "data": base64.b64encode(image_bytes).decode('utf-8'),
            "mime_type": "image/png"
        }
    ]
)

print(interaction.output_text)
