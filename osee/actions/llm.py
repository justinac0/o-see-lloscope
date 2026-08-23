from google import genai
import os
from dotenv import load_dotenv
load_dotenv()
import base64

# Globals
with open("system.md", "r", encoding="utf-8") as file:
    SYSTEM_INSTRUCTION = file.read()
API_KEY = os.getenv("API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")

# For each new chat create a new llm object
class llm():
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.interaction = None

    def query(self, prompt: str, image_bytes=None, details=None):
        global LLM_MODEL, SYSTEM_INSTRUCTION

        inputs = [{"type": "text", "text": prompt}]

        if image_bytes:
            inputs.append(
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode('utf-8'),
                    "mime_type": "image/png"
                }
        )

        kwargs = {
            "model": LLM_MODEL,
            "system_instruction": SYSTEM_INSTRUCTION,
            "input": inputs
        }

        if self.interaction != None:
            kwargs["previous_interaction_id"] = self.interaction.id

        self.interaction = self.client.interactions.create(**kwargs)
        print(self.interaction.output_text)
        return

if __name__ == "__main__":
    chat = llm()

    print("What would you like described? Type q or ctrl+ c to exit.")
    prompt = input("Chat: ")

    path = r"""C:\Users\liaml\Downloads\square_waveform.png"""
    with open(path, "rb") as image_file:
        image_bytes = image_file.read()

    chat.query(prompt=prompt, image_bytes=image_bytes)

    while True:
        prompt = input("\nChat: ")
        if (prompt == 'q') or (prompt == 'Q'): break
        chat.query(prompt=prompt)