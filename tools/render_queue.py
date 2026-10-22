#!/usr/bin/env python3
"""Renders the final film's master PNG sequence chunk by chunk, unattended, and stops itself on trouble.

    python tools/render_queue.py --output-dir DIR [--device cpu] [--from 0] [--to 8399] [--chunk 25] [--probe 10]

Each chunk is one run of tools/render.py --profile final --start-frame A --end-frame B --skip-existing
(so frames already done are skipped, and an interrupted queue simply starts again). Chunks are --chunk
frames long; where the film enters a heavier environment (the landfill, the level, the station level,
the climax and pull-out) the first chunk there is a --probe-frame diagnostic, and the queue carries on
only if time and memory held steady through it.

After every chunk it checks every frame of the chunk (a complete PNG at 3840 x 2160), and appends to
progress.log beside the output folder: the range, the elapsed time, the seconds a frame, the peak
memory, the frames done of the whole film, and the disk space left. It stops, and says why, if a frame
fails the check, Blender fails, memory grows abnormally, the disk gets low, a chunk is dramatically
slower than its environment so far, or a file named STOP appears in the output folder (a clean stop
after the current chunk).
"""

import argparse
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from procedural_disagreement.core import hinge, outer, profiles, refrain, timeline  # noqa: E402
from render import frame_path, png_complete  # noqa: E402

#: Where the film enters a heavier environment: (first frame, name). The first chunk there is a probe.
ENVIRONMENTS = (
    (0, "room"),
    (timeline.frame_of(timeline.LANDFILL_CUT), "landfill"),
    (timeline.frame_of(hinge.START), "level from above"),
    (timeline.frame_of(refrain.START), "station level"),
    (timeline.frame_of(outer.CODA_START - 15.0), "climax and pull-out"),
    (timeline.frame_of(outer.CODA_START) + 1, "room (coda and ending)"),
)
LAST_FRAME = timeline.frame_of(outer.ENDING_END) - 1
#: Stop if a frame's working set passes this, or its peak passes PEAK (GB); the machine has 11.8.
WORKING_LIMIT = 8.0
PEAK_LIMIT = 9.5
#: Stop if the output drive has less than this left (GB).
DISK_FLOOR = 15.0
#: Stop if a chunk takes this many times its environment's median seconds a frame so far.
SLOWDOWN = 3.0
FRAME_LINE = re.compile(r"\[pd\] frame (\d+) .*?\s([\d.]+) s(?:\s+memory ([\d.]+) GB, peak ([\d.]+) GB)?")


def environment_of(frame):
    current = ENVIRONMENTS[0]
    for start, name in ENVIRONMENTS:
        if frame >= start:
            current = (start, name)
    return current


def next_boundary(frame):
    later = [start for start, _ in ENVIRONMENTS if start > frame]
    return min(later) if later else LAST_FRAME + 1


def done_count(folder, first, last, width, height):
    return sum(png_complete(frame_path(folder, f), width, height) for f in range(first, last + 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", required=True, help="the canonical frames folder")
    parser.add_argument("--device", default="cpu", help="Cycles device for this machine (default cpu)")
    parser.add_argument("--from", dest="first", type=int, default=0)
    parser.add_argument("--to", dest="last", type=int, default=LAST_FRAME)
    parser.add_argument("--chunk", type=int, default=25)
    parser.add_argument("--probe", type=int, default=10)
    parser.add_argument("--blender", default=os.environ.get("BLENDER"))
    args = parser.parse_args()

    folder = os.path.abspath(args.output_dir)
    os.makedirs(folder, exist_ok=True)
    log_path = os.path.join(os.path.dirname(folder), "progress.log")
    final = profiles.FINAL
    stop_file = os.path.join(folder, "STOP")

    def log(line):
        stamped = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M"), line)
        print(stamped, flush=True)
        with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(stamped + "\n")

    def halt(reason):
        log("STOPPED: " + reason)
        sys.exit(1)

    seconds_by_environment = {}
    probed = set()
    frame = args.first
    log("queue started: frames %d-%d into %s, %d-frame chunks, %s" % (args.first, args.last, folder, args.chunk, args.device))
    while frame <= args.last:
        if os.path.exists(stop_file):
            halt("STOP file found in %s (delete it to carry on)" % folder)
        start, name = environment_of(frame)
        probe = start not in probed and frame == start and start != 0
        size = args.probe if probe else args.chunk
        end = min(frame + size - 1, next_boundary(frame) - 1, args.last)
        todo = [f for f in range(frame, end + 1) if not png_complete(frame_path(folder, f), final.width, final.height)]
        if not todo:
            frame = end + 1
            continue
        command = [sys.executable, os.path.join(ROOT, "tools", "render.py"), "--profile", "final",
                   "--start-frame", str(frame), "--end-frame", str(end), "--skip-existing",
                   "--device", args.device, "--output-dir", folder]
        if args.blender:
            command += ["--blender", args.blender]
        began = time.time()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        elapsed = time.time() - began
        frames = [(int(m.group(1)), float(m.group(2)), float(m.group(3) or 0), float(m.group(4) or 0))
                  for m in FRAME_LINE.finditer(result.stdout)]
        if result.returncode != 0:
            halt("render.py failed on %d-%d (exit %d):\n%s" % (frame, end, result.returncode, result.stdout[-3000:]))
        bad = [f for f in range(frame, end + 1) if not png_complete(frame_path(folder, f), final.width, final.height)]
        if bad:
            halt("frame(s) %s failed validation after chunk %d-%d" % (bad, frame, end))
        times = [t for _, t, _, _ in frames]
        mean = statistics.mean(times) if times else 0.0
        peak = max((p for _, _, _, p in frames), default=0.0)
        working = max((w for _, _, w, _ in frames), default=0.0)
        free = shutil.disk_usage(folder).free / 2 ** 30
        total = done_count(folder, 0, LAST_FRAME, final.width, final.height)
        log("%s %d-%d (%s%s): %d rendered, %.0f s elapsed, %.0f s a frame, peak %.1f GB, %d of %d frames done, %.0f GB free" % (
            "probe" if probe else "chunk", frame, end, name, "" if not probe else ", first in this environment",
            len(frames), elapsed, mean, peak, total, LAST_FRAME + 1, free))
        if working > WORKING_LIMIT or peak > PEAK_LIMIT:
            halt("memory: working set %.1f GB, peak %.1f GB in %d-%d" % (working, peak, frame, end))
        if free < DISK_FLOOR:
            halt("disk: %.0f GB left on the output drive" % free)
        history = seconds_by_environment.setdefault(start, [])
        if history and mean > SLOWDOWN * statistics.median(history):
            halt("%.0f s a frame in %d-%d, against a median of %.0f s so far in the %s" % (
                mean, frame, end, statistics.median(history), name))
        if probe and len(times) >= 6:
            # Steady through the probe: neither time nor memory climbing from its first frames to its last.
            early, late = statistics.mean(times[1:4]), statistics.mean(times[-3:])
            grew = frames[-1][2] - frames[0][2]
            if late > 1.5 * early or grew > 1.5:
                halt("the %s probe was not steady: %.0f s a frame at first, %.0f s at the end; working set +%.1f GB" % (
                    name, early, late, grew))
        probed.add(start)
        history.extend(times)
        frame = end + 1
    log("queue finished: frames %d-%d" % (args.first, args.last))


if __name__ == "__main__":
    main()
