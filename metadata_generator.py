"""
Metadata Generator — OpenRouter + AI Style Support
Har channel ka alag AI style ho sakta hai
"""

import json
import logging
import requests

log = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

AI_STYLE_PROMPTS = {
    "energetic": "Create VIRAL, high-energy titles with emojis. Use power words like SHOCKING, INSANE, MUST WATCH. Make it clickbait but honest.",
    "professional": "Create professional, informative titles. Clear and value-focused. No clickbait.",
    "funny": "Create funny, witty titles with humor. Use jokes and casual language. Make people laugh.",
    "educational": "Create educational titles that explain what viewers will learn. Use 'How to', 'Why', 'What is' format.",
    "custom": ""  # User ka custom prompt use hoga
}


class MetadataGenerator:
    def __init__(self, api_key: str = None, ai_style: str = "energetic", custom_prompt: str = None):
        import os
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.ai_style = ai_style
        self.custom_prompt = custom_prompt

        if not self.api_key:
            raise ValueError("OpenRouter API key missing!")

    def generate(self, filename: str) -> dict:
        clean_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")

        # Style prompt choose karo
        if self.ai_style == "custom" and self.custom_prompt:
            style_instruction = self.custom_prompt
        else:
            style_instruction = AI_STYLE_PROMPTS.get(self.ai_style, AI_STYLE_PROMPTS["energetic"])

        prompt = f"""You are a YouTube SEO expert for Indian content creators.
Style instruction: {style_instruction}
Video filename: "{clean_name}"

Return ONLY valid JSON (no markdown):
{{
  "title": "YouTube title with emoji max 60 chars following the style",
  "description": "400 word SEO description with hook in first 2 lines, timestamps, CTA",
  "hashtags": "#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8 #tag9 #tag10 #tag11 #tag12 #tag13 #tag14 #tag15",
  "thumbnail_text": "MAX 4 WORDS CAPS"
}}"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://tubeautomate.app",
                "X-Title": "TubeAutomate"
            }
            payload = {
                "model": FREE_MODEL,
                "messages": [
                    {"role": "system", "content": "Return only valid JSON, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 1000
            }

            resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=40)

            if resp.status_code == 429:
                import time
                time.sleep(30)
                resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=40)

            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            metadata = json.loads(raw)

            for field in ["title", "description", "hashtags", "thumbnail_text"]:
                if field not in metadata:
                    raise ValueError(f"'{field}' missing")

            if len(metadata["title"]) > 100:
                metadata["title"] = metadata["title"][:97] + "..."

            log.info(f"✅ Metadata: {metadata['title']}")
            return metadata

        except Exception as e:
            log.error(f"Metadata error: {e}")
            return {
                "title": f"🔥 {clean_name[:55]}",
                "description": f"Watch: {clean_name}\n\n00:00 Intro\n02:00 Main\n05:00 End\n\nLike & Subscribe! 🔔",
                "hashtags": "#viral #trending #youtube #india #entertainment",
                "thumbnail_text": "WATCH NOW"
            }
