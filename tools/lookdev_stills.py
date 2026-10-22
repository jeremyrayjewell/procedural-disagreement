"""Runs inside Blender. Look-development stills: single frames of the film through the lookdev
profile. Each still is built on its own, so frames from anywhere in the film cost the same.

    blender -b --factory-startup --python tools/lookdev_stills.py -- [--scale 50] [--samples 32] [--out DIR] 2:13 4:19.1 ...

Times are track time (seconds or m:ss). Nothing is saved but the images.
"""

import os
import sys
import time

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from procedural_disagreement.core import choreography, profiles, timeline  # noqa: E402
from procedural_disagreement.scene import build, landfill  # noqa: E402


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"--scale": "100", "--samples": "", "--out": os.path.join(ROOT, "renders", "lookdev", "stills"), "--tag": ""}
    times = []
    while arguments:
        argument = arguments.pop(0)
        if argument in options:
            options[argument] = arguments.pop(0)
        else:
            times.append(timeline.parse_time(argument))
    profile = profiles.LOOKDEV.with_overrides(samples=int(options["--samples"]) if options["--samples"] else None,
                                              scale=int(options["--scale"]))
    options["--out"] = os.path.abspath(options["--out"])      # Blender reads a bare relative path its own way
    os.makedirs(options["--out"], exist_ok=True)
    for t in times:
        frame = timeline.frame_of(t)
        name = "look%s_%s_f%06d.png" % (options["--tag"], timeline.format_time(timeline.time_of(frame)).replace(":", "m").replace(".", "s"), frame)
        if os.path.exists(os.path.join(options["--out"], name)):
            print("[look] %s already rendered" % name)       # an interrupted run can simply be started again
            continue
        started = time.time()
        scene = build.build(profile, frame, frame)
        built = time.time() - started
        pit = bpy.data.collections.get(landfill.COLLECTION)
        if pit is not None:
            pit.hide_render = not choreography.camera_is_below(timeline.time_of(frame))
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(options["--out"], name)
        started = time.time()
        bpy.ops.render.render(write_still=True)
        print("[look] %s  frame %d  %dx%d  %d samples  build %.1f s  render %.1f s  -> %s" % (
            timeline.format_time(timeline.time_of(frame)), frame, profile.width, profile.height, profile.samples,
            built, time.time() - started, name))
        sys.stdout.flush()


main()
