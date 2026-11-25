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

logging.basicConfig(level=get_env("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


def seconds(stamp: str) -> float:
    total = 0.0
    for part in stamp.strip().split(":"):
        total = total * 60 + float(part)
    return total


def pipeline(src: Path, opts: dict):
    """Yields progress strings and returns (duration, highlights) with clips cut."""
    total = video.duration(str(src))
    log.info("pipeline start: %.0fs video, opts=%s", total, opts)
    found = []
    starts = range(0, max(1, int(total)), CHUNK_SECONDS)
    for i, offset in enumerate(starts):
        yield f"Analyzing chunk {i + 1}/{len(starts)}"
        length = min(CHUNK_SECONDS, total - offset)
        if length < opts["min_len"]:
            log.info("chunk %d/%d skipped: %.1fs is shorter than min_len", i + 1, len(starts), length)
            continue
        log.info("chunk %d/%d: offset=%ss length=%.0fs", i + 1, len(starts), offset, length)
        proxy = src.parent / f"chunk{i}.mp4"
        video.make_proxy(str(src), str(proxy), offset, length)
        cuts = video.shot_cuts(str(proxy))
        log.info("chunk %d: %d shot cuts", i + 1, len(cuts))
        kept = 0
        picks = gemini.analyze(str(proxy), opts["count"], opts["min_len"],
                                opts["max_len"], opts["language"])
        log.info("chunk %d: Gemini returned %d highlights", i + 1, len(picks))
        for h in picks:
            try:
                a, b = seconds(h.start), seconds(h.end)
            except ValueError:
                log.warning("chunk %d: unparsable time %r-%r", i + 1, h.start, h.end)
                continue
            if not 0 <= a < b <= length + 1:  # drop made-up timestamps
                log.warning("chunk %d: out-of-range time %r-%r (chunk is %.0fs)",
                            i + 1, h.start, h.end, length)
                continue
            a, b = video.snap(a, cuts), min(video.snap(b, cuts), length)
            if b - a < 1:
                log.info("chunk %d: dropped %.1fs highlight after snapping", i + 1, b - a)
                continue
            if h.spoiler and not opts["include_spoilers"]:
                log.info("chunk %d: dropped spoiler at %.1fs (%s)", i + 1, offset + a, h.reason)
                continue
            kept += 1
            found.append({**h.model_dump(), "start": round(offset + a, 2),
                          "end": round(offset + b, 2)})
        log.info("chunk %d: kept %d of %d", i + 1, kept, len(picks))
        proxy.unlink()

    top = sorted(found, key=lambda h: h["score"], reverse=True)[: opts["count"]]
    top.sort(key=lambda h: h["start"])
    log.info("selected %d of %d candidates", len(top), len(found))
    for n, h in enumerate(top):
        yield f"Cutting clip {n + 1}/{len(top)}"
        h["clip"] = str(src.parent / f"clip{n}.mp4")
        log.info("clip %d: %ss-%ss score=%s %s", n, h["start"], h["end"], h["score"], h["category"])
        video.cut_clip(str(src), h["clip"], h["start"], h["end"])
    log.info("pipeline done: %d clips", len(top))
    return total, top


def highlight(file, count, min_len, max_len, language, include_spoilers, max_minute):
    if not file:
        raise gr.Error("Upload a video first")
    ext = Path(file).suffix.lower()
    if ext not in EXTENSIONS:
        log.warning("rejected upload %s: unsupported type", Path(file).name)
        raise gr.Error(f"Allowed types: {EXTENSIONS}")
    if min_len >= max_len:
        raise gr.Error("Min length must be smaller than max length")

    folder = DATA / uuid.uuid4().hex
    folder.mkdir(parents=True)
    src = folder / f"source{ext}"
    shutil.move(file, src)
    log.info("job %s: received %s (%.1f MB)", folder.name, Path(file).name, src.stat().st_size / 1e6)

    try:
        try:
            total = video.duration(str(src))
        except (RuntimeError, ValueError):
            log.warning("job %s: ffprobe could not read the upload", folder.name)
            raise gr.Error("Not a readable video")
        if max_minute and max_minute * 60 < total:  # spoiler cutoff
            log.info("job %s: trimming %.0fs video to minute %s", folder.name, total, max_minute)
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
        log.exception("job %s failed", folder.name)
        raise gr.Error("Processing failed, see server logs")

    clips = [(h["clip"], f"{h['category']} · {h['score']}/10 · {h['start']}s-{h['end']}s")
             for h in top]
    rows = [{k: v for k, v in h.items() if k != "clip"} for h in top]
    log.info("job %s: done, %d highlights", folder.name, len(top))
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
