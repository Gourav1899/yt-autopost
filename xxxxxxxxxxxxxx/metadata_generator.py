"""
Metadata Generator — OpenRouter Free API
OpenAI ki jagah OpenRouter use karta hai
Free model: meta-llama/llama-3.1-8b-instruct:free
"""

import os
import json
import logging
import requests

log = logging.getLogger(__name__)

OPENROUTER_FREE_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class MetadataGenerator:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY set nahi hai!")

    def generate(self, filename: str) -> dict:
        clean_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

        prompt = f"""You are a YouTube SEO expert for Indian content creators.
Video filename: "{clean_name}"
Return ONLY valid JSON (no markdown, no extra text):
{{
  "title": "Catchy title with emoji max 60 chars",
  "description": "400 word SEO description. Hook in first 2 lines. Timestamps: 00:00 Intro, 02:00 Main Content, 05:00 Outro. CTA at end.",
  "hashtags": "#viral #trending #youtube #india #entertainment #shorts #hulk #marvel #action #fight #motivation #subscribe #like #fyp #explore",
  "thumbnail_text": "MAX 4 WORDS CAPS"
}}"""

        try:
            log.info(f"🧠 OpenRouter call: '{clean_name}'")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://yt-autopost-bot.onrender.com",
                "X-Title": "YT Auto Post Bot"
            }
            payload = {
                "model": OPENROUTER_FREE_MODEL,
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
                log.warning("Rate limit — 30s wait...")
                time.sleep(30)
                resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=40)

            resp.raise_for_status()
            raw = resp.json()['choices'][0]['message']['content'].strip()
            raw = raw.replace('```json', '').replace('```', '').strip()

            metadata = json.loads(raw)
            for field in ['title', 'description', 'hashtags', 'thumbnail_text']:
                if field not in metadata:
                    raise ValueError(f"'{field}' missing")

            if len(metadata['title']) > 100:
                metadata['title'] = metadata['title'][:97] + '...'

            log.info(f"✅ Title: {metadata['title']}")
            return metadata

        except Exception as e:
            log.error(f"OpenRouter error: {e}")
            return self._fallback(clean_name)

    def _fallback(self, name: str) -> dict:
        log.warning("⚠️ Fallback metadata use ho raha hai")
        return {
            "title": f"🔥 {name[:55]}",
            "description": f"Watch: {name}\n\n00:00 Intro\n02:00 Main\n05:00 End\n\nLike & Subscribe! 🔔",
            "hashtags": "#viral #trending #youtube #india #entertainment #shorts #hulk #marvel",
            "thumbnail_text": "WATCH NOW"
        }
