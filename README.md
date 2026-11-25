# Highlight

Upload a video in the browser, get recommended trailer highlights and clips.

## Run
Put your keys in `.env` (`GEMINI_API_KEY`, `API_KEY`, `GEMINI_BASE_URL`), then:

    docker compose up -d --build

Open http://localhost:8000. If `API_KEY` is set, log in with username `admin` and `API_KEY` as the password.

Without Docker you need `ffmpeg` and `ffprobe` on PATH: `pip install -r requirements.txt && python app.py`.

Gradio also exposes the same function as an API (see "Use via API" at the bottom of the page),
for example with `gradio_client`.

Options: highlights count, min/max clip length (seconds), language (Vietnamese|English),
include spoilers, and a minute cutoff (ignore everything after it).

## Limits (hackathon scope)
- Run a single server process; jobs run inside the request, so closing the tab cancels the wait.
- Uploaded videos and clips stay on disk until you delete them.
- Upload size is checked by Gradio against `MAX_UPLOAD_MB`.
- Plain HTTP: add TLS before using it outside a private network.
- A highlight crossing a 20-minute chunk boundary can be missed.
- Video is sent to Google: check content rights. Free-tier data may be used by Google to improve products.
