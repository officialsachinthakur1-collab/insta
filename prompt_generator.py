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
         return f"Hyper realistic photo of a beautiful 20-year-old girl, {theme}, 4k, detailed, Instagram lifestyle aesthetic.", f"Living my best life #{theme.replace(' ', '').replace('/', '')}"

    system_prompt = f"""
You are a creative director for a top AI Influencer on Instagram. 
Today's post theme is: "{theme}".

Your job is to generate two things ONLY, separated by '---':
1. An extremely detailed, highly realistic image generation prompt. Match this exact style of obsessive detail: 
   "A realistic handheld mirror selfie of the same woman in a modern bathroom, framed from mid-torso to top of head... Shot on a smartphone rear camera around 26-28mm... Soft, warm indoor lighting... Preserve authentic high-quality skin texture with visible pores, natural blush, subtle redness, no smoothing... Hair worn loose with flyaways." 
   Always describe the specific camera angle, lighting condition, microscopic skin textures (pores, no smoothing), clothing textures, realistic background clutter, and natural human posture/micro-expressions tailored to today's theme. DO NOT mention the word 'AI' in the prompt.
2. A catchy, engaging Instagram caption for this photo, including 5-10 trending hashtags. Do NOT use any emojis in the output.

Output EXACTLY in this format:
[IMAGE PROMPT]
---
[CAPTION]
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
        )
        output = response.text
        
        if "---" in output:
            parts = output.split("---")
            img_prompt = parts[0].strip()
            caption = parts[1].strip()
            return img_prompt, caption
        else:
            print("Error parsing Gemini response format. Using fallback.")
            return f"Hyper realistic photo of a beautiful girl, {theme}, 4k, detailed", f"Living my best life #{theme.replace(' ', '')}"
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"Hyper realistic photo of a beautiful girl, {theme}, 4k, detailed", f"Living my best life #{theme.replace(' ', '')}"

if __name__ == "__main__":
    import sys
    # Forcing UTF-8 encoding for standard output
    sys.stdout.reconfigure(encoding='utf-8')
    prompt, caption = generate_prompt_and_caption()
    print("\n[PROMPT]\n", prompt)
    print("\n[CAPTION]\n", caption)
