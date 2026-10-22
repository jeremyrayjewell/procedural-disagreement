#!/usr/bin/env python3
"""Turns real footage for the CRT wall into frames of the wall's canvas.

    python tools/make_crt_video.py [--ffmpeg PATH] [--source DIR] [--out DIR]

Reads every video file in assets/video/crt/ (in name order, one after another) and writes
assets/video/crt/canvas/: one 320 x 144 grey frame for each frame of the film from 1:00 for as
long as the footage lasts, up to the cut at 1:36.9 after which the wall is not seen, and
manifest.json. The look picks them up on its next build: the screens show the footage wherever
there is a frame of it, except while a line of the lyric is on the wall, which takes priority
(presentation/screens.py). Film time 1:00 is the footage's first frame; the footage runs on
under the lyric. Delete the canvas folder to go back to the provisional content.

The footage is centre-cropped to the canvas's shape and scaled to it nearest-pixel (each canvas
pixel is one source pixel: nothing is smoothed), made grey, quantised to VIDEO_LEVELS steps and
held between the screens' idle raster and VIDEO_CAP of their full light, below the lyric's.
Nothing is generated: with no footage there is nothing to write.

Needs numpy, Pillow and ffmpeg.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from procedural_disagreement.core import timeline  # noqa: E402
from procedural_disagreement.presentation import screens  # noqa: E402

SOURCE = os.path.join(ROOT, "assets", "video", "crt")
EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".mpg", ".mpeg", ".gif")


def frames(ffmpeg, path, width, height):
    """The file's frames at the film's rate, cropped and scaled nearest-pixel, grey: (n, h, w)."""
    command = [ffmpeg, "-v", "error", "-i", path, "-an", "-vf",
               "fps=%d,scale=%d:%d:force_original_aspect_ratio=increase:flags=neighbor,crop=%d:%d,format=gray"
               % (timeline.FPS, width, height, width, height), "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, height, width)


def level(grey):
    """Grey 0..255 to the screens' content level: VIDEO_LEVELS steps from IDLE to VIDEO_CAP."""
    steps = np.minimum(grey.astype(np.int32) * screens.VIDEO_LEVELS // 256, screens.VIDEO_LEVELS - 1)
    return screens.IDLE + (screens.VIDEO_CAP - screens.IDLE) * steps / (screens.VIDEO_LEVELS - 1.0)


#: Which clip each screen starts on, by row from the top: every clip once in the first eight,
#: and no two screens side by side, above one another or corner to corner on the same clip.
FEED_CLIPS = ((1, 2, 3, 4, 5), (6, 7, 8, 1, 2), (3, 4, 5, 6, 7))
#: The stream the screens play: the film's frame rate, a clean picture.
FEED_SIZE = (960, 540)


def _count(ffprobe, path):
    out = subprocess.run([ffprobe, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_frames", "-of", "csv=p=0", path], check=True, stdout=subprocess.PIPE)
    return int(out.stdout.decode().strip())


def feeds(ffmpeg, sources, out):
    """Independent monitors: the clips, one after another in name order, as one clean stream at the
    film's frame rate; each screen plays it from the start of its own clip (FEED_CLIPS), a screen
    whose clip is already playing elsewhere from half-way through it, and on round to the first
    clip after the last. 30 fps by dropping frames: nothing is sped up."""
    ffprobe = os.path.join(os.path.dirname(ffmpeg), "ffprobe" + os.path.splitext(ffmpeg)[1])
    out = os.path.abspath(out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    parts, clips, start = [], [], 0
    for k, path in enumerate(sources):
        part = os.path.join(out, "part_%02d.mp4" % k)
        subprocess.run([ffmpeg, "-v", "error", "-y", "-i", path, "-an", "-vf",
                        "fps=%d,scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos,pad=%d:%d:-1:-1"
                        % (timeline.FPS, FEED_SIZE[0], FEED_SIZE[1], FEED_SIZE[0], FEED_SIZE[1]),
                        "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-g", "15", "-pix_fmt", "yuv420p", part],
                       check=True)
        n = _count(ffprobe, part)
        clips.append({"file": os.path.basename(path), "start": start, "frames": n})
        parts.append(part)
        start += n
        print("[video] %s: %d frames from %d" % (os.path.basename(path), n, clips[-1]["start"]))
    listing = os.path.join(out, "parts.txt")
    with open(listing, "w", encoding="utf-8", newline="\n") as handle:
        handle.writelines("file '%s'\n" % os.path.basename(p) for p in parts)
    subprocess.run([ffmpeg, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy",
                    os.path.join(out, "stream.mp4")], check=True, cwd=out)
    for p in parts + [listing]:
        os.remove(p)
    total = _count(ffprobe, os.path.join(out, "stream.mp4"))
    seen, assignment = set(), {}
    for top, clip_row in enumerate(FEED_CLIPS):
        for col, number in enumerate(clip_row):
            clip = clips[(number - 1) % len(clips)]
            again = number in seen
            seen.add(number)
            assignment["%d,%d" % (screens.ROWS - 1 - top, col)] = {
                "clip": clip["file"], "offset": clip["start"] + (clip["frames"] // 2 if again else 0)}
    first = timeline.frame_of(screens.BLOCKS_START)
    last = timeline.frame_of(timeline.LANDFILL_CUT) - 1
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"made_by": "tools/make_crt_video.py", "layout": "feeds", "first": first, "last": last,
                   "stream": "stream.mp4", "frames": total, "size": list(FEED_SIZE), "clips": clips,
                   "screens": assignment, "cap": screens.VIDEO_CAP}, handle, indent=1)
    print("[video] stream %d frames (%.1f s); screens play it from their own clip, %s-%s -> %s" % (
        total, total / float(timeline.FPS), timeline.format_time(timeline.time_of(first)),
        timeline.format_time(timeline.time_of(last)), out))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ffmpeg", default=os.environ.get("FFMPEG") or shutil.which("ffmpeg"), help="path to ffmpeg")
    parser.add_argument("--source", default=SOURCE, help="folder of footage (default assets/video/crt)")
    parser.add_argument("--out", default=screens.VIDEO, help="folder for the canvas frames (default assets/video/crt/canvas)")
    parser.add_argument("--layout", choices=("wall", "same", "feeds"), default="feeds",
                        help="wall: one picture across the 15 screens (default); same: the whole picture on every "
                             "screen; feeds: every screen its own monitor, playing the footage from its own point")
    parser.add_argument("--detail", type=int, default=1, metavar="N",
                        help="footage pixels a screen pixel, each way (default 1: 64 x 48 a screen)")
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error("ffmpeg not found: pass --ffmpeg or set FFMPEG")
    sources = sorted(p for p in glob.glob(os.path.join(args.source, "*")) if p.lower().endswith(EXTENSIONS))
    if not sources:
        sys.exit("No footage in %s (%s)." % (args.source, ", ".join(EXTENSIONS)))
    if args.layout == "feeds":
        return feeds(args.ffmpeg, sources, args.out)
    screen = (screens.PIXELS[0] * args.detail, screens.PIXELS[1] * args.detail)
    if args.layout == "wall":
        width, height = screen[0] * screens.COLUMNS, screen[1] * screens.ROWS
    else:
        width, height = screen
    first = timeline.frame_of(screens.BLOCKS_START)
    end = timeline.frame_of(timeline.LANDFILL_CUT)
    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out)
    # Blender reads the frame before the first for every frame before it: a blank canvas.
    Image.fromarray(np.full((height, width), round(screens.IDLE * 255), np.uint8)).save(
        os.path.join(args.out, "frame_%06d.png" % (first - 1)))
    frame, used = first, []
    for path in sources:
        if frame >= end:
            break
        clip = frames(args.ffmpeg, path, width, height)
        take = clip[:end - frame]
        for picture in take:
            Image.fromarray(np.round(level(picture) * 255).astype(np.uint8)).save(
                os.path.join(args.out, "frame_%06d.png" % frame))
            frame += 1
        used.append({"file": os.path.basename(path), "frames": int(len(take)), "of": int(len(clip))})
        print("[video] %s: %d frame(s) used of %d" % (os.path.basename(path), len(take), len(clip)))
    if frame == first:
        sys.exit("The footage has no frames.")
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"made_by": "tools/make_crt_video.py", "first": first, "last": frame - 1, "sources": used,
                   "layout": args.layout, "screen": list(screen), "canvas": [width, height],
                   "levels": screens.VIDEO_LEVELS, "cap": screens.VIDEO_CAP}, handle, indent=1)
    print("[video] frames %d-%d (%s-%s) -> %s" % (first, frame - 1, timeline.format_time(timeline.time_of(first)),
                                                   timeline.format_time(timeline.time_of(frame - 1)), args.out))


if __name__ == "__main__":
    main()
