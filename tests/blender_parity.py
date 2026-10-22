"""Runs inside Blender (see tools/check.py). Builds the preview and final profiles and verifies
that they agree on composition: the camera and every animated pivot must have the same world
transform at the same frame. Geometry density and render settings are allowed to differ."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procedural_disagreement.core import profiles, timeline  # noqa: E402
from procedural_disagreement.scene import build  # noqa: E402

FIRST = timeline.frame_of(timeline.SECTION_START)
LAST = timeline.frame_of(timeline.TIMELINE_END) - 1
SAMPLES = sorted({FIRST, LAST} | set(range(FIRST, LAST, 37)))
TOLERANCE = 1e-5


def snapshot(profile):
    # Workbench for both: this test is about transforms, and must not need a GPU.
    scene = build.build(profile.with_overrides(engine="BLENDER_WORKBENCH"), FIRST, LAST)
    data = {}
    for frame in SAMPLES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for obj in scene.objects:
            if obj.type not in {"EMPTY", "CAMERA", "LIGHT"}:
                continue
            matrix = obj.evaluated_get(depsgraph).matrix_world
            data[(obj.name, frame)] = [v for row in matrix for v in row]
        data[("Camera.lens", frame)] = [scene.camera.evaluated_get(depsgraph).data.lens]
    return data


def main():
    preview = snapshot(profiles.PREVIEW)
    final = snapshot(profiles.FINAL)

    missing = sorted({k[0] for k in preview} - {k[0] for k in final})
    worst, worst_key = 0.0, None
    for key, values in preview.items():
        if key not in final:
            continue
        error = max(abs(a - b) for a, b in zip(values, final[key]))
        if error > worst:
            worst, worst_key = error, key

    shared = len({k[0] for k in preview} & {k[0] for k in final})
    extra = len({k[0] for k in final} - {k[0] for k in preview})
    print("[pd] parity: %d shared pivots/camera/lights over %d frames, max deviation %.2e; final adds %d pivots" % (
        shared, len(SAMPLES), worst, extra))
    if missing:
        print("[pd] FAIL: present in preview but not in final: %s" % ", ".join(missing[:10]))
        sys.exit(1)
    if worst > TOLERANCE:
        print("[pd] FAIL: %s differs by %.3e at frame %d" % (worst_key[0], worst, worst_key[1]))
        sys.exit(1)
    print("[pd] parity OK")


if __name__ == "__main__":
    main()
