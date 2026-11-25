import base64
import json
import logging
import time
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from config import get_env

log = logging.getLogger("gemini")

MODEL = get_env("GEMINI_MODEL", "gemini-3.8-flash")
# OpenAI-compatible endpoint: the BiFrost gateway (https://demeter.fptplay.net/v1) or Gemini directly
BASE_URL = get_env("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
API_KEY = get_env("GEMINI_API_KEY")
MAX_BODY_BYTES = int(float(get_env("MAX_REQUEST_MB", "1")) * 1024 * 1024)  # the gateway 413s above 1 MiB

RETRIES = 4  # the gateway returns occasional 504s
RETRY_STATUS = {429, 502, 503, 504}


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
    data = base64.b64encode(Path(path).read_bytes()).decode()  # inline: no file-upload endpoint
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "file", "file": {"filename": "segment.mp4",
                                      "file_data": f"data:video/mp4;base64,{data}"}},
            {"type": "text", "text": PROMPT.format(count=count, lo=lo, hi=hi, language=language)},
        ]}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "highlights", "schema": Highlights.model_json_schema()}},
    }
    size = len(json.dumps(payload))
    log.info("sending %s inline: request body %d KB of %d KB allowed (base_url=%s)",
             path, size // 1000, MAX_BODY_BYTES // 1000, BASE_URL)
    if size > MAX_BODY_BYTES:
        raise ValueError(f"request body is {size / 1e6:.2f} MB, over the {MAX_BODY_BYTES / 1e6:.2f} MB "
                         "limit: lower CHUNK_SECONDS or raise MAX_REQUEST_MB")
    t0 = time.time()
    try:
        for attempt in range(1, RETRIES + 1):
            r = httpx.post(f"{BASE_URL}/chat/completions", json=payload, timeout=600,
                           headers={"Authorization": f"Bearer {API_KEY}"})
            if r.status_code not in RETRY_STATUS or attempt == RETRIES:
                break
            log.warning("HTTP %d from the gateway, retry %d/%d", r.status_code, attempt, RETRIES - 1)
            time.sleep(5 * attempt)
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code} from {BASE_URL}: {r.text[:500]}")
        log.info("%s responded in %.1fs", MODEL, time.time() - t0)
        return Highlights.model_validate_json(r.json()["choices"][0]["message"]["content"]).highlights
    except Exception:
        log.exception("Gemini analysis failed for %s", path)
        raise
