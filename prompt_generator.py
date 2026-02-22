import os
import json
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

def get_todays_theme():
    """Reads schedule.json and returns today's theme."""
    try:
        with open("schedule.json", "r") as f:
            schedule = json.load(f)
        today = datetime.now().strftime("%A")
        return schedule.get(today, "Casual Lifestyle Photo")
    except Exception as e:
        print(f"Error reading schedule: {e}")
        return "Casual Lifestyle Photo"

def generate_prompt_and_caption():
    """Generates an image generation prompt and an Instagram caption based on today's theme."""
    theme = get_todays_theme()
    print(f"Today's Theme: {theme}")
    
    if not client:
         return [
             f"Hyper realistic photo of a person, full face portrait, {theme}, 4k, detailed.",
             f"Hyper realistic photo of a person side profile looking away, {theme}, 4k.",
             f"Hyper realistic photo of a person's hands holding coffee or doing an activity, {theme}, 4k."
         ], f"Living my best life #{theme.replace(' ', '').replace('/', '')}"

    system_prompt = f"""
You are a creative director for a top AI Influencer on Instagram. 
Today's post theme is: "{theme}".

Your job is to design a "Photo Dump" style carousel post consisting of 3 distinct image generation prompts and 1 caption.
The 3 images must look like they were taken on the EXACT same day, in the EXACT same place, wearing the EXACT same outfit.

Step 1: Invent a highly specific Outfit and a highly specific Location matching today's theme.
Step 2: Write 3 prompts using that exact same Outfit and Location, just changing the camera angle and the subject's pose/action.

1. **IMAGE PROMPT 1 (The Main Portrait):** A very detailed portrait or mirror selfie showing the subject's face clearly. 
2. **IMAGE PROMPT 2 (The Detail/Vibe Shot):** A lifestyle shot (e.g., holding a coffee cup, sitting with a book, or side angle). The face can be partially visible or side profile.
3. **IMAGE PROMPT 3 (The Candid/Action Shot):** Another distinct lifestyle shot (e.g., walking, laughing looking away, interacting with the environment).

CRITICAL RULES FOR ALL 3 PROMPTS:
- **CONSISTENCY:** You MUST describe the EXACT same outfit and exactly the same background location in all 3 prompts. Do not change the colors or environment.
- **REALISM (ANTI-AI LOOK):** The user's reference face is very soft. You MUST add these exact phrases to every prompt to force realism: "Raw candid photography, shot on 35mm lens, unapologetically natural unfiltered skin texture, visible pores, realistic lighting shadows, highly authentic, NOT soft, NO AI smoothing, real life photography."
- **NO PHYSICAL DESCRIPTORS:** NEVER use words like 'woman', 'girl', 'man', 'beautiful', 'young', or describe the subject's physical facial features in the prompt. Use neutral terms like 'the person' or 'the subject'. DO NOT mention the word 'AI'.

Output EXACTLY in this JSON format:
{{
  "prompts": [
    "prompt 1 text here...",
    "prompt 2 text here...",
    "prompt 3 text here..."
  ],
  "caption": "Your catchy Instagram caption with 5-10 trending hashtags (no emojis)"
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
        )
        output = response.text.strip()
        # Clean markdown formatting if present
        if output.startswith("```json"):
            output = output[7:-3].strip()
        elif output.startswith("```"):
            output = output[3:-3].strip()
            
        data = json.loads(output)
        return data.get("prompts", []), data.get("caption", f"Living my best life #{theme.replace(' ', '')}")
        
    except Exception as e:
        print(f"Error calling or parsing Gemini API: {e}")
        return [
             f"Hyper realistic photo of a person, full face portrait, {theme}, 4k, detailed.",
             f"Hyper realistic photo of a person side profile looking away, {theme}, 4k.",
             f"Hyper realistic photo of a person's hands holding coffee or doing an activity, {theme}, 4k."
        ], f"Living my best life #{theme.replace(' ', '')}"

if __name__ == "__main__":
    import sys
    # Forcing UTF-8 encoding for standard output
    sys.stdout.reconfigure(encoding='utf-8')
    prompt, caption = generate_prompt_and_caption()
    print("\n[PROMPT]\n", prompt)
    print("\n[CAPTION]\n", caption)
