# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Highlight: a small Gradio app. A user uploads a video in the browser, and the app returns recommended trailer highlights plus cut clips. Gemini (called through the BiFrost gateway's OpenAI-compatible API, `GEMINI_BASE_URL`) picks the moments and ffmpeg cuts the clips. There are no tests, linter or build step.

## Run

Put the env vars in `.env` (loaded by `config.get_env`), then `docker compose up -d --build`. The UI is at http://localhost:7860.

Without Docker you need `ffmpeg` and `ffprobe` on PATH: `pip install -r requirements.txt && python app.py`. Run a single server process.

If `API_KEY` is set, Gradio login is username `admin` with `API_KEY` as the password. If it is empty, auth is disabled.

Env vars: `GEMINI_API_KEY`, `GEMINI_BASE_URL`, `API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`), `DATA_DIR` (default `data`), `MAX_UPLOAD_MB` (4096), `CHUNK_SECONDS` (90), `MAX_REQUEST_MB` (1), `WORKERS` (2, the Gradio concurrency limit), `LOG_LEVEL` (INFO).

## Architecture

The flow is the "Find highlights" button → `highlight()` generator, which streams progress and the final clips to the page.

- `app.py` holds the Gradio UI and the pipeline orchestration.
  - `highlight` moves the upload to `DATA/<uuid>/source.<ext>` and validates it with ffprobe. If a cutoff minute is set, it trims the video up front as a spoiler cutoff. It then drives `pipeline`.
  - `pipeline` splits the source into `CHUNK_SECONDS` chunks. For each chunk it makes a 480p proxy, detects shot cuts, and asks Gemini for highlights. It then validates the timestamps, snaps them to shot cuts, filters spoilers, and offsets times back to the full-video timeline. After all chunks, it keeps the top `count` by score, sorts them by start time, and cuts the clips from the original source. It yields progress strings.
  - There is no job registry: the work runs inside the Gradio event. Clips stay on disk under `DATA`, which is passed to `launch(allowed_paths=...)`.
- `config.py` has `get_env()`, which loads `.env` and reads variables.
- `gemini.py` sends a tiny per-chunk copy (`video.make_upload`: 240p, 1 fps, mono 24k, about 10 KB/s) inline, base64-encoded as a `file` part, to the OpenAI-compatible `POST {GEMINI_BASE_URL}/chat/completions` (BiFrost: `https://demeter.fptplay.net/v1`, Bearer auth) with a pydantic `Highlights` JSON schema as `response_format`. It uses `httpx` directly and retries 429/502/503/504. There is no Files API: the gateway has none. The gateway's proxy (openresty) rejects bodies over exactly 1 MiB with a 413 (measured), which is why `CHUNK_SECONDS` is 90. `MAX_REQUEST_MB` (1) refuses chunks whose body is bigger. Ask the gateway owner to raise `client_max_body_size` to allow longer chunks. The prompt asks for times as MM:SS relative to the chunk. `app.pipeline` parses them with `seconds()` and discards out-of-range or invalid ones.
- `video.py` is a thin subprocess wrapper over ffprobe and ffmpeg: `duration`, `make_proxy`, `shot_cuts` (scene-detect via `showinfo`), `snap`, and `cut_clip` (re-encodes, so cuts are frame-accurate).

## Known limitations

These are accepted hackathon trade-offs, listed in README.md.
- A highlight that crosses a chunk boundary can be missed.
- Jobs run inside the request, so closing the tab cancels the wait.
- Plain HTTP only.
