#!/usr/bin/env python3
"""Times the final profile on the render machine, to choose its sample count.

    python tools/benchmark_final.py [--samples 128,256,512] [--frames 3] [--device auto] [--scale 100]

For each of four environments it renders a few consecutive frames at each sample count, at the
final profile's full resolution on the GPU, and writes them to renders/benchmark/<environment>/
as s<samples>_f<frame>.png, with every frame's render time in renders/benchmark/benchmark.json.
It prints the times and what the whole film would cost at each count. The consecutive frames are
for judging temporal stability (flip through them); the counts for judging noise. Choose the
lowest count that is clean and stable in every environment (docs/final_render.md).

Needs only the Python standard library and Blender.
"""

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

#: (name, track time of the first frame, the stretch of the film it stands for)
ENVIRONMENTS = (
    ("room_crt_bank", 62.0, ((0.0, 96.9), (255.0, 280.0))),      # the room, the CRT footage, the ghosts
    ("landfill", 102.0, ((96.9, 112.5),)),                       # refuse, world-space lyric text
    ("station_level", 193.5, ((112.5, 240.0),)),                 # the network, its shadows, dark surfaces
    ("pullout", 254.37, ((240.0, 255.0),)),                      # the climax's widest view, fog, darkness
)
OUT = os.path.join(ROOT, "renders", "benchmark")


def inner(samples, count, device, scale):
    """Runs inside Blender."""
    import bpy
    from procedural_disagreement.core import choreography, profiles, timeline
    from procedural_disagreement.scene import build, landfill
    results = []
    for name, t, _ in ENVIRONMENTS:
        first = timeline.frame_of(t)
        scene = build.build(profiles.FINAL.with_overrides(scale=scale), first, first + count - 1, device=device)
        pit = bpy.data.collections.get(landfill.COLLECTION)
        folder = os.path.join(OUT, name)
        os.makedirs(folder, exist_ok=True)
        # A one-sample render first, untimed: loading the scene onto the device is not rendering.
        scene.cycles.samples = 1
        scene.frame_set(first)
        if pit is not None:
            pit.hide_render = not choreography.camera_is_below(t)
        scene.render.filepath = os.path.join(folder, "warmup.png")
        bpy.ops.render.render(write_still=True)
        for n in samples:
            scene.cycles.samples = n
            for frame in range(first, first + count):
                if pit is not None:
                    pit.hide_render = not choreography.camera_is_below(timeline.time_of(frame))
                scene.frame_set(frame)
                scene.render.filepath = os.path.join(folder, "s%d_f%06d.png" % (n, frame))
                started = time.time()
                bpy.ops.render.render(write_still=True)
                seconds = time.time() - started
                results.append({"environment": name, "samples": n, "frame": frame, "seconds": round(seconds, 2)})
                print("[bench] %-14s %4d samples  frame %d  %7.1f s" % (name, n, frame, seconds))
                sys.stdout.flush()
                with open(os.path.join(OUT, "benchmark.json"), "w", encoding="utf-8", newline="\n") as handle:
                    json.dump(results, handle, indent=1)


def report(samples):
    with open(os.path.join(OUT, "benchmark.json"), encoding="utf-8") as handle:
        results = json.load(handle)
    print("\nSeconds a frame (mean of the consecutive frames):")
    print("%-16s" % "" + "".join("%10d" % n for n in samples))
    means = {}
    for name, _, _ in ENVIRONMENTS:
        row = []
        for n in samples:
            times = [r["seconds"] for r in results if r["environment"] == name and r["samples"] == n]
            means[(name, n)] = sum(times) / len(times) if times else None
            row.append("%10.1f" % means[(name, n)] if times else "%10s" % "-")
        print("%-16s" % name + "".join(row))
    print("\nThe whole film (8,400 frames), each environment weighted by the stretch it stands for:")
    for n in samples:
        hours = 0.0
        for name, _, spans in ENVIRONMENTS:
            if means.get((name, n)) is None:
                hours = None
                break
            hours += sum(b - a for a, b in spans) * 30 * means[(name, n)] / 3600.0
        print("  %4d samples: %s" % (n, "%.0f hours" % hours if hours is not None else "incomplete"))
    print("\nFrames: %s (flip through each environment's consecutive frames at each count)." % OUT)


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    options = {"--samples": "128,256,512", "--frames": "3", "--device": "auto", "--scale": "100",
               "--blender": os.environ.get("BLENDER")}
    inside = "--inner" in arguments
    arguments = [a for a in arguments if a != "--inner"]
    while arguments:
        key = arguments.pop(0)
        if key not in options:
            sys.exit("Unknown option %r. Options: %s" % (key, ", ".join(options)))
        options[key] = arguments.pop(0)
    samples = [int(n) for n in options["--samples"].split(",")]
    if inside:
        inner(samples, int(options["--frames"]), options["--device"], int(options["--scale"]))
        return
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from render import find_blender
    blender = find_blender(options["--blender"])
    os.makedirs(OUT, exist_ok=True)
    command = [blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python", os.path.abspath(__file__),
               "--", "--inner", "--samples", options["--samples"], "--frames", options["--frames"],
               "--device", options["--device"], "--scale", options["--scale"]]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    for line in process.stdout:
        if line.startswith(("[bench]", "[pd] Cycles device", "[pd] WARNING", "Traceback", "Error")):
            print(line.rstrip())
    if process.wait() != 0:
        sys.exit("Blender failed (exit %d)." % process.returncode)
    report(samples)


if __name__ == "__main__":
    main()
