"""Runs inside Blender. Builds the scene for a profile, then renders frames or stays open.

Normally launched by tools/render.py; directly:
    blender -b --factory-startup --python tools/blender_entry.py -- --profile preview --first 1050 --last 1949 --out renders/preview/frames
"""

import argparse
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from procedural_disagreement.core import choreography, profiles, timeline  # noqa: E402
from procedural_disagreement.scene import build, landfill  # noqa: E402
from render import png_complete  # noqa: E402


def _memory():
    """(working set, peak working set) of this process in GB, where the platform says; else None."""
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        kernel32 = ctypes.WinDLL("kernel32")
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        query = kernel32.K32GetProcessMemoryInfo
        query.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        query.restype = wintypes.BOOL
        if query(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters.WorkingSetSize / 2 ** 30, counters.PeakWorkingSetSize / 2 ** 30
    except (AttributeError, OSError, ImportError):
        pass
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20
        return None, peak
    except ImportError:
        return None


def main():
    parser = argparse.ArgumentParser(prog="blender_entry")
    parser.add_argument("--profile", choices=sorted(profiles.PROFILES), default="preview")
    parser.add_argument("--first", type=int, required=True, help="first frame")
    parser.add_argument("--last", type=int, required=True, help="last frame, inclusive")
    parser.add_argument("--frames", help="comma-separated frames to render instead of the whole range")
    parser.add_argument("--out", help="directory for frame_NNNNNN.png files")
    parser.add_argument("--engine", choices=sorted(profiles.ENGINES))
    parser.add_argument("--samples", type=int)
    parser.add_argument("--scale", type=int, default=100)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--resume", action="store_true", help="skip frames whose file already exists")
    parser.add_argument("--save-blend", help="save the built scene to this .blend")
    parser.add_argument("--open", action="store_true", help="build only and leave Blender open")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    profile = profiles.PROFILES[args.profile].with_overrides(
        engine=profiles.ENGINES.get(args.engine), samples=args.samples, scale=args.scale)
    scene = build.build(profile, args.first, args.last, device=args.device)

    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_blend))
        print("[pd] saved %s" % os.path.abspath(args.save_blend))

    if args.open:
        bpy.app.timers.register(_look_through_camera, first_interval=0.2)
        return

    if not args.out:
        return
    frames = [int(f) for f in args.frames.split(",")] if args.frames else list(range(args.first, args.last + 1))
    render(scene, frames, os.path.abspath(args.out), args.resume)


def render(scene, frames, out_dir, resume):
    os.makedirs(out_dir, exist_ok=True)
    started = time.time()
    rendered = 0
    width = scene.render.resolution_x * scene.render.resolution_percentage // 100
    height = scene.render.resolution_y * scene.render.resolution_percentage // 100
    for position, frame in enumerate(frames, 1):
        path = os.path.join(out_dir, "frame_%06d.png" % frame)
        # Only a whole PNG at this resolution counts as rendered; anything else is rendered again.
        if resume and png_complete(path, width, height):
            continue
        frame_started = time.time()
        # The pit under the floor is thousands of objects that no shot above the floor can see.
        # Leaving it out of those frames changes no pixel and keeps the preview fast.
        pit = bpy.data.collections.get(landfill.COLLECTION)
        if pit is not None:
            pit.hide_render = not choreography.camera_is_below(timeline.time_of(frame))
        scene.frame_set(frame)
        # Written under another name and renamed when whole, so a render cut off mid-file never
        # leaves a frame that looks finished.
        partial = os.path.join(out_dir, "frame_%06d.partial.png" % frame)
        scene.render.filepath = partial
        bpy.ops.render.render(write_still=True)
        os.replace(partial, path)
        rendered += 1
        memory = _memory()
        print("[pd] frame %d  t=%s  (%d/%d)  %.2f s%s" % (
            frame, timeline.format_time(timeline.time_of(frame)), position, len(frames), time.time() - frame_started,
            "  memory %.2f GB, peak %.2f GB" % memory if memory and memory[0] is not None else ""))
        sys.stdout.flush()
    print("[pd] rendered %d frame(s) in %.1f s (%d already present)" % (
        rendered, time.time() - started, len(frames) - rendered))


def _look_through_camera():
    """For inspection: camera view, object colours, timeline at the first frame."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.region_3d.view_perspective = "CAMERA"
                space.shading.type = "SOLID"
                space.shading.color_type = "OBJECT"
                space.overlay.show_relationship_lines = False
    return None


if __name__ == "__main__":
    main()
