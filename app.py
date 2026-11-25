import logging
import shutil
import uuid
from pathlib import Path

import gradio as gr

import gemini
import video
from config import get_env

DATA = Path(get_env("DATA_DIR", "data"))
API_KEY = get_env("API_KEY", "")
MAX_BYTES = int(get_env("MAX_UPLOAD_MB", "4096")) * 1024 * 1024
CHUNK_SECONDS = int(get_env("CHUNK_SECONDS", "1200"))
WORKERS = int(get_env("WORKERS", "2"))
EXTENSIONS = [".mp4", ".mov", ".mkv", ".webm"]


def seconds(stamp: str) -> float:
    total = 0.0
    for part in stamp.strip().split(":"):
        total = total * 60 + float(part)
    return total


def pipeline(src: Path, opts: dict):
    """Yields progress strings and returns (duration, highlights) with clips cut."""
    total = video.duration(str(src))
    found = []
    starts = range(0, max(1, int(total)), CHUNK_SECONDS)
    for i, offset in enumerate(starts):
        yield f"Analyzing chunk {i + 1}/{len(starts)}"
        length = min(CHUNK_SECONDS, total - offset)
        if length < opts["min_len"]:
            continue
        proxy = src.parent / f"chunk{i}.mp4"
        video.make_proxy(str(src), str(proxy), offset, length)
        cuts = video.shot_cuts(str(proxy))
        for h in gemini.analyze(str(proxy), opts["count"], opts["min_len"],
                                opts["max_len"], opts["language"]):
            try:
                a, b = seconds(h.start), seconds(h.end)
            except ValueError:
                continue
            if not 0 <= a < b <= length + 1:  # drop made-up timestamps
                continue
            a, b = video.snap(a, cuts), min(video.snap(b, cuts), length)
            if b - a < 1:
                continue
            if h.spoiler and not opts["include_spoilers"]:
                continue
            found.append({**h.model_dump(), "start": round(offset + a, 2),
                          "end": round(offset + b, 2)})
        proxy.unlink()

    top = sorted(found, key=lambda h: h["score"], reverse=True)[: opts["count"]]
    top.sort(key=lambda h: h["start"])
    for n, h in enumerate(top):
        yield f"Cutting clip {n + 1}/{len(top)}"
        h["clip"] = str(src.parent / f"clip{n}.mp4")
        video.cut_clip(str(src), h["clip"], h["start"], h["end"])
    return total, top


def highlight(file, count, min_len, max_len, language, include_spoilers, max_minute):
    if not file:
        raise gr.Error("Upload a video first")
    ext = Path(file).suffix.lower()
    if ext not in EXTENSIONS:
        raise gr.Error(f"Allowed types: {EXTENSIONS}")
    if min_len >= max_len:
        raise gr.Error("Min length must be smaller than max length")

    folder = DATA / uuid.uuid4().hex
    folder.mkdir(parents=True)
    src = folder / f"source{ext}"
    shutil.move(file, src)

    try:
        try:
            total = video.duration(str(src))
        except (RuntimeError, ValueError):
            raise gr.Error("Not a readable video")
        if max_minute and max_minute * 60 < total:  # spoiler cutoff
            yield "Trimming to the cutoff", gr.update(), gr.update()
            trimmed = folder / "trimmed.mp4"
            video.cut_clip(str(src), str(trimmed), 0, max_minute * 60)
            src.unlink()
            src = trimmed

        opts = dict(count=int(count), min_len=int(min_len), max_len=int(max_len),
                    language=language, include_spoilers=include_spoilers)
        steps = pipeline(src, opts)
        while True:
            try:
                yield next(steps), gr.update(), gr.update()
            except StopIteration as done:
                total, top = done.value
                break
    except gr.Error:
        raise
    except Exception:
        logging.exception("job in %s failed", folder)
        raise gr.Error("Processing failed, see server logs")

    clips = [(h["clip"], f"{h['category']} · {h['score']}/10 · {h['start']}s-{h['end']}s")
             for h in top]
    rows = [{k: v for k, v in h.items() if k != "clip"} for h in top]
    yield f"Done: {len(top)} highlights in a {total:.0f}s video", rows, clips


with gr.Blocks(title="Highlight API") as demo:
    gr.Markdown("# Trailer highlights\nUpload a video. Gemini picks the moments and ffmpeg cuts the clips.")
    with gr.Row():
        with gr.Column():
            file = gr.File(label="Video", file_types=EXTENSIONS, type="filepath")
            count = gr.Slider(1, 30, value=8, step=1, label="Highlights")
            min_len = gr.Slider(1, 30, value=3, step=1, label="Min length (s)")
            max_len = gr.Slider(2, 60, value=12, step=1, label="Max length (s)")
            language = gr.Radio(["Vietnamese", "English"], value="Vietnamese", label="Reason language")
            spoilers = gr.Checkbox(label="Include spoilers")
            max_minute = gr.Number(label="Ignore everything after this minute (optional)",
                                   minimum=0, value=None)
            run = gr.Button("Find highlights", variant="primary")
        with gr.Column():
            status = gr.Textbox(label="Status", interactive=False)
            gallery = gr.Gallery(label="Clips", columns=3)
            table = gr.JSON(label="Highlights")
    run.click(highlight, [file, count, min_len, max_len, language, spoilers, max_minute],
              [status, table, gallery], concurrency_limit=WORKERS, api_name="highlight")


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=8000,
        auth=("admin", API_KEY) if API_KEY else None,
        max_file_size=MAX_BYTES,
        allowed_paths=[str(DATA.resolve())],
    )
