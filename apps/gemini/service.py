from google import genai
from google.genai import types
import os
import json
import mimetypes
import re

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_json(text: str):
    match = re.search(r"\[.*\]", text, re.S)
    if not match:
        return []
    try:
        return json.loads(match.group())
    except Exception:
        return []


def detect_foods(image_path: str):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            "画像の食材だけを日本語のJSON配列で返して（例: [\"トマト\",\"卵\"]）",
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        ]
    )

    if not response.text:
        return []

    return extract_json(response.text)


def generate_recipe(foods: list[str]):
    prompt = f"""
次の食材で1つだけ簡単なレシピを作ってください。

食材:
{foods}

出力形式:
料理名:
材料:
作り方:
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text or ""