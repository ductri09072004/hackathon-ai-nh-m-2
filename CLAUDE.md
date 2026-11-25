# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Highlight: a small Gradio app. A user uploads a video in the browser, and the app returns recommended trailer highlights plus cut clips. Gemini (called through the BiFrost gateway when `GEMINI_BASE_URL` is set) picks the moments and ffmpeg cuts the clips. There are no tests, linter or build step.

## Run

Put the env vars in `.env` (loaded by `config.get_env`), then `docker compose up -d --build`. The UI is at http://localhost:8000.

Without Docker you need `ffmpeg` and `ffprobe` on PATH: `pip install -r requirements.txt && python app.py`. Run a single server process.

If `API_KEY` is set, Gradio login is username `admin` with `API_KEY` as the password. If it is empty, auth is disabled.

Env vars: `GEMINI_API_KEY`, `GEMINI_BASE_URL`, `API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`), `DATA_DIR` (default `data`), `MAX_UPLOAD_MB` (4096), `CHUNK_SECONDS` (1200), `WORKERS` (2, the Gradio concurrency limit), `LOG_LEVEL` (INFO).

## Architecture

The flow is the "Find highlights" button → `highlight()` generator, which streams progress and the final clips to the page.

- `app.py` holds the Gradio UI and the pipeline orchestration.
  - `highlight` moves the upload to `DATA/<uuid>/source.<ext>` and validates it with ffprobe. If a cutoff minute is set, it trims the video up front as a spoiler cutoff. It then drives `pipeline`.
  - `pipeline` splits the source into `CHUNK_SECONDS` chunks. For each chunk it makes a 480p proxy, detects shot cuts, and asks Gemini for highlights. It then validates the timestamps, snaps them to shot cuts, filters spoilers, and offsets times back to the full-video timeline. After all chunks, it keeps the top `count` by score, sorts them by start time, and cuts the clips from the original source. It yields progress strings.
  - There is no job registry: the work runs inside the Gradio event. Clips stay on disk under `DATA`, which is passed to `launch(allowed_paths=...)`.
- `config.py` has `get_env()`, which loads `.env` and reads variables.
- `gemini.py` uploads the proxy to the Gemini Files API and polls until it is ACTIVE. It then calls `client.interactions.create` with a pydantic `Highlights` JSON schema as the response format, and deletes the uploaded file in `finally`. The prompt asks for times as MM:SS relative to the chunk. `app.pipeline` parses them with `seconds()` and discards out-of-range or invalid ones.
- `video.py` is a thin subprocess wrapper over ffprobe and ffmpeg: `duration`, `make_proxy`, `shot_cuts` (scene-detect via `showinfo`), `snap`, and `cut_clip` (re-encodes, so cuts are frame-accurate).

## Known limitations

These are accepted hackathon trade-offs, listed in README.md.
- A highlight that crosses a chunk boundary can be missed.
- Jobs run inside the request, so closing the tab cancels the wait.
- Plain HTTP only.
