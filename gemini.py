import time

from google import genai
from pydantic import BaseModel, Field

from config import get_env

MODEL = get_env("GEMINI_MODEL", "gemini-3.8-flash")
BASE_URL = get_env("GEMINI_BASE_URL")
API_KEY = get_env("GEMINI_API_KEY")


class Highlight(BaseModel):
    start: str = Field(description="Start time in this video, MM:SS")
    end: str = Field(description="End time in this video, MM:SS")
    score: int = Field(description="Trailer value, 1-10")
    category: str = Field(description="action, emotion, comedy, romance, suspense or dialogue")
    reason: str = Field(description="Why this moment works in a trailer")
    spoiler: bool = Field(description="True if it reveals a twist, death or ending")


class Highlights(BaseModel):
    highlights: list[Highlight]


PROMPT = """You are a movie trailer editor. Watch and listen to this video segment.
Pick up to {count} moments that would work in a trailer. Each must be {lo}-{hi} seconds long,
start and end at natural points (no cut mid-sentence) and not overlap another.
Judge picture, dialogue, music and sound together. Score strictly.
Mark spoiler=true for twists, deaths, reveals or resolutions.
Times are MM:SS from the start of this segment. Write each reason in {language}."""


def analyze(path: str, count: int, lo: int, hi: int, language: str) -> list[Highlight]:
    # GEMINI_BASE_URL routes calls through the BiFrost gateway
    client = genai.Client(api_key=API_KEY, http_options={"base_url": BASE_URL} if BASE_URL else None)
    video = client.files.upload(file=path)
    try:
        deadline = time.time() + 600
        while not video.state or video.state.name != "ACTIVE":
            if video.state and video.state.name == "FAILED":
                raise RuntimeError("Gemini could not process the video")
            if time.time() > deadline:
                raise TimeoutError("Gemini file processing timed out")
            time.sleep(5)
            video = client.files.get(name=video.name)

        result = client.interactions.create(
            model=MODEL,
            input=[
                {"type": "video", "uri": video.uri, "mime_type": video.mime_type,
                 "resolution": "low"},
                {"type": "text", "text": PROMPT.format(count=count, lo=lo, hi=hi, language=language)},
            ],
            response_format={"type": "text", "mime_type": "application/json",
                             "schema": Highlights.model_json_schema()},
        )
        return Highlights.model_validate_json(result.output_text).highlights
    finally:
        client.files.delete(name=video.name)
