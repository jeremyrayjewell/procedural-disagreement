"""Runs inside Blender (see tools/check.py). Guards the approved parts of the film.

Each reference file records, for a spread of frames inside a locked interval, the world
transform and colour of every object in the preview scene, and the camera's lens. This test
rebuilds the scene and compares. New objects may be added; nothing recorded may move, change
colour or disappear.

    blender -b --factory-startup --python tests/blender_locked.py                     compare all
    blender -b --factory-startup --python tests/blender_locked.py -- --write NAME     record one

Only record a reference when that interval has been approved, and before changing the code.
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procedural_disagreement.core import profiles, timeline  # noqa: E402
from procedural_disagreement.scene import build  # noqa: E402

REFERENCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference")

#: name -> times sampled. Everything inside each interval is locked.
REFERENCES = {
    # The approach, both cuts, both failures, the system branch.
    "locked_0035_0105": (35.0, 40.1, 45.0, 47.5, 50.0, 50.5, 52.5, 55.0, 55.2, 56.25, 57.5, 60.0, 60.1, 60.2,
                         61.25, 62.5, 64.0, 65.0),
    # Phantom load and its residue, up to the absent-attractor cue.
    "locked_0105_0120": (65.5, 66.0, 66.2667, 66.4, 66.9, 67.5, 68.0, 68.75, 69.5, 70.0, 71.0, 72.5, 75.0,
                         77.0, 79.0, 80.0),
    # The absent attractor, from its cue to convergence, seen from a held camera.
    "locked_0120_0130": (80.5, 81.25, 82.5, 83.75, 85.0, 86.25, 87.5, 88.0, 88.75, 89.5, 89.9667, 90.0),
    # Recruitment bridge, disposal, the cut, the fall, and the flyover with its four disposals
    # (the third, at 1:47.5, is the second sung "landfill").
    "locked_0130_0152": (90.5, 91.25, 92.5, 93.75, 95.0, 96.25, 96.65, 96.9, 97.5, 98.4, 98.8, 100.0, 102.5,
                         103.2, 105.0, 106.0, 107.5, 108.0, 108.5, 109.3, 110.0, 111.0, 112.4667),
    # The outer frame. Opening: the system before the case, up to the frame the film proper starts on.
    "locked_0000_0035": (0.0, 2.5, 3.6, 5.5, 8.0, 10.5, 12.5, 17.5, 19.8, 20.5, 22.0, 26.0, 27.5, 30.4, 31.0,
                         34.0, 34.9667),
    # Ending: the system after the case. Its first frame is the state 4:15-4:25 must arrive at.
    "locked_0425_0440": (265.0, 267.5, 268.6, 271.5, 273.5, 275.9, 276.3, 278.0, 279.9667),
    # The hinge: up through the level the chutes hang from, the die-like field, the cut, the reset.
    # Its last frame is the state the refrain section starts from.
    "locked_0152_0220": (112.5, 115.0, 117.5, 118.6, 120.0, 123.0, 126.0, 129.0, 131.0, 133.0, 134.9667, 135.0,
                         137.5, 139.9667),
    # The refrain: the level at standing height, coupled at 2:20, the procedure from 2:40. Its
    # last frame is the state the section after 3:00 starts from.
    "locked_0220_0300": (140.0, 141.0, 142.5, 145.0, 150.0, 155.0, 160.0, 161.4, 163.0, 165.0, 168.0, 171.0,
                         174.0, 177.0, 179.9667, 180.0),
    # The network: stations fall into step, the array and the heavy main respond, and from 3:20
    # the finite lane is cleared and held. Its last frame is where the bass returns.
    "locked_0300_0330": (180.5, 183.0, 186.0, 188.0, 190.0, 193.0, 196.0, 198.0, 200.0, 200.6, 201.5, 203.0,
                         204.5, 206.0, 207.5, 209.0, 209.9667, 210.0),
    # Compensation: function is routed round the lane, station by station, as donor, relay,
    # receiver and carrier. Its last frame is where the largest peak of the track begins.
    "locked_0330_0400": (210.5, 211.25, 212.0, 212.65, 213.1, 215.0, 216.875, 217.6, 218.3, 220.0, 220.7,
                         221.4, 222.5, 225.0, 226.25, 227.0, 230.0, 230.7, 231.4, 233.0, 236.25, 237.0,
                         237.5, 238.2, 238.9, 239.9667, 240.0),
    # The field: the compensation spreads to every station, the level's own structure joins,
    # and it runs as one machine round the empty lane. Its last frame is where the music gives way.
    "locked_0400_0415": (240.5, 241.25, 242.5, 243.75, 244.5, 245.0, 245.7, 246.25, 246.875, 247.5, 248.2,
                         248.75, 249.4, 250.0, 250.7, 251.25, 251.9, 252.5, 253.125, 253.8, 254.375, 254.7,
                         254.9667, 255.0),
    # The coda: one cut back to the room, nobody there; scrawls and ranked bars set out by the
    # first statement of the refrain and withdrawn by the second. Its last frame is the frame
    # before the ending's first.
    "locked_0415_0425": (255.0333, 255.5, 256.0, 256.65, 257.5, 258.0, 258.5, 259.1, 260.0, 261.0, 261.5,
                         261.65, 261.75, 261.85, 262.0, 262.1, 262.2, 262.5, 262.8, 263.3, 263.9, 264.1,
                         264.3, 264.5, 264.6, 264.9667),
}
TRANSFORM_TOLERANCE = 2e-5
COLOR_TOLERANCE = 2e-5


def snapshot(times):
    """{frame: {object name: 12 transform values + 4 colour values}} for the preview scene."""
    scene = bpy.context.scene
    data = {}
    for frame in (timeline.frame_of(t) for t in times):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        record = {}
        for obj in scene.objects:
            evaluated = obj.evaluated_get(depsgraph)
            values = [v for row in evaluated.matrix_world for v in row][:12] + list(evaluated.color)
            record[obj.name] = [round(v, 6) for v in values]
        record["Camera.lens"] = [round(scene.camera.evaluated_get(depsgraph).data.lens, 6)]
        data[str(frame)] = record
    return data


def path_of(name):
    return os.path.join(REFERENCE_DIR, name + ".json")


def compare(name, reference, current):
    problems, worst = [], 0.0
    for frame, record in reference.items():
        now = current.get(frame, {})
        for obj, values in record.items():
            if obj not in now:
                problems.append("frame %s: %s is missing" % (frame, obj))
                continue
            for i, (a, b) in enumerate(zip(values, now[obj])):
                worst = max(worst, abs(a - b))
                if abs(a - b) > (COLOR_TOLERANCE if i >= 12 else TRANSFORM_TOLERANCE):
                    problems.append("frame %s (%s): %s %s differs by %.2e" % (
                        frame, timeline.format_time(timeline.time_of(int(frame))), obj,
                        "colour" if i >= 12 else "transform", abs(a - b)))
                    break
    times = REFERENCES[name]
    added = len(next(iter(current.values()))) - len(next(iter(reference.values())))
    print("[pd] %s (%s-%s): %d objects x %d frames, max deviation %.1e, %d object(s) added since" % (
        name, timeline.format_time(times[0]), timeline.format_time(times[-1]),
        len(next(iter(reference.values()))), len(reference), worst, added))
    for line in problems[:12]:
        print("[pd] FAIL: " + line)
    if problems:
        print("[pd] FAIL: %d difference(s) in %s" % (len(problems), name))
    return not problems


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    writing = arguments[1] if arguments[:1] == ["--write"] else None
    if writing is not None and writing not in REFERENCES:
        sys.exit("Unknown reference %r. Known: %s" % (writing, ", ".join(REFERENCES)))

    # "--profile NAME" compares another profile against the same references: for a profile
    # that only changes presentation, every recorded transform and colour must still hold.
    profile = profiles.PREVIEW
    if "--profile" in arguments:
        profile = profiles.PROFILES[arguments[arguments.index("--profile") + 1]]
        if writing:
            sys.exit("References are recorded from the preview profile only.")
        print("[pd] comparing profile %r against the preview's references" % profile.name)
    names = [writing] if writing else list(REFERENCES)
    # "--only NAME" compares one reference window, building only its frames: the whole film in
    # one build of a lit profile no longer fits in memory on the development machine.
    if "--only" in arguments:
        names = [arguments[arguments.index("--only") + 1]]
        if names[0] not in REFERENCES:
            sys.exit("Unknown reference %r. Known: %s" % (names[0], ", ".join(REFERENCES)))
    frames = [timeline.frame_of(t) for name in names for t in REFERENCES[name]]
    build.build(profile, min(frames), max(frames))

    if writing:
        data = snapshot(REFERENCES[writing])
        os.makedirs(REFERENCE_DIR, exist_ok=True)
        with open(path_of(writing), "w", encoding="utf-8") as handle:
            json.dump({"interval": [REFERENCES[writing][0], REFERENCES[writing][-1]], "frames": data},
                      handle, separators=(",", ":"))
        print("[pd] reference %s written: %d frames, %d objects" % (writing, len(data), len(next(iter(data.values())))))
        return

    ok = True
    for name in names:
        if not os.path.exists(path_of(name)):
            print("[pd] FAIL: no reference recorded for %s" % name)
            ok = False
            continue
        with open(path_of(name), encoding="utf-8") as handle:
            reference = json.load(handle)["frames"]
        ok = compare(name, reference, snapshot(REFERENCES[name])) and ok
    if not ok:
        sys.exit(1)
    print("[pd] locked sequences unchanged")


if __name__ == "__main__":
    main()
