from google import genai
import os
import threading
from dotenv import load_dotenv
load_dotenv()
import base64
import time

# Globals
with open("system.md", "r", encoding="utf-8") as file:
    SYSTEM_INSTRUCTION = file.read()
API_KEY = os.getenv("API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite")

# For each new chat create a new llm object
class llm():
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.interaction = None
        self.status_completed = None

    def loading(self, max_counter=7):
        start = time.time()
        counter = 0 
        step = 1

        while not self.status_completed:
            print(
                f"Thinking {'.'*counter + ' '*(max_counter-counter)}\t\t{round(time.time() - start, 3)}s", 
                end="\r", 
                flush=True
            )
            time.sleep(0.1)

            if counter >= max_counter:
                step = -1    
            elif counter <= 0:
                step = 1
            counter += step

        self.status_completed = False


    def query(self, prompt: str, image_bytes=None, details=None):
        global LLM_MODEL, SYSTEM_INSTRUCTION

        self.status_completed = False

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
        self.status_completed = True

        return self.interaction.output_text

