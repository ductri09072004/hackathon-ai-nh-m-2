import logging
import re
import subprocess
import time

log = logging.getLogger("video")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    log.debug("%s finished in %.1fs: %s", cmd[0], time.time() - t0, " ".join(cmd))
    if p.returncode != 0:
        log.error("%s exited %d: %s", cmd[0], p.returncode, p.stderr[-500:])
        raise RuntimeError(f"{cmd[0]} failed: {p.stderr[-500:]}")
    return p


def duration(path: str) -> float:
    out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "csv=p=0", path]).stdout
    return float(out.strip())


def make_proxy(src: str, dst: str, start: float, length: float) -> None:
    """Small 480p copy of one chunk: faster to upload than the source."""
    _run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", str(length), "-i", src,
          "-vf", "scale=-2:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
          "-c:a", "aac", "-b:a", "96k", dst])


def make_upload(src: str, dst: str) -> None:
    """Tiny copy for sending inline to Gemini (no Files API): Gemini samples ~1 fps anyway.
    About 10 KB/s, so a 90 s chunk stays under the gateway's 1 MiB request limit."""
    _run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", "scale=-2:240", "-r", "1",
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "36", "-ac", "1",
          "-c:a", "aac", "-b:a", "24k", dst])


def shot_cuts(path: str, threshold: float = 0.3) -> list[float]:
    p = _run(["ffmpeg", "-i", path, "-an", "-vf",
              f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", p.stderr)]


def snap(t: float, cuts: list[float], tolerance: float = 1.5) -> float:
    near = min(cuts, key=lambda c: abs(c - t), default=None)
    return near if near is not None and abs(near - t) <= tolerance else t


def cut_clip(src: str, dst: str, start: float, end: float) -> None:
    _run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", str(end - start), "-i", src,
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", dst])
