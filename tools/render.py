#!/usr/bin/env python3
"""Render any interval of the video and encode it to MP4 with the music.

    python tools/render.py                                  preview of the whole section (0:35-1:05)
    python tools/render.py --start 0:48 --end 0:54          a short range
    python tools/render.py --stills 12                      12 stills + contact sheet: fastest check
    python tools/render.py --engine eevee --start 0:50 --end 0:52
    python tools/render.py --profile final                  on the rendering machine
    python tools/render.py --profile final --resume         continue an interrupted render
    python tools/render.py --open                           build the scene and open it in Blender

Times are absolute track time (seconds or m:ss). Frame n shows t = n / 30, and frame files are
named by frame number, so separately rendered ranges line up and can be encoded together.

Needs only the Python standard library, Blender, and ffmpeg.
"""

import argparse
import glob
import math
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from procedural_disagreement.core import profiles, timeline  # noqa: E402

AUDIO_EXTENSIONS = (".wav", ".flac", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".aif", ".aiff")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=sorted(profiles.PROFILES), default="preview")
    parser.add_argument("--start", default=str(timeline.SECTION_START), help="start, track time (default 0:35)")
    parser.add_argument("--end", default=str(timeline.SECTION_END), help="end, track time, exclusive (default 1:05)")
    parser.add_argument("--stills", type=int, metavar="N", help="render N evenly spaced stills and a contact sheet instead of a video")
    parser.add_argument("--step", type=int, default=1, metavar="N",
                        help="review only: render every Nth frame into its own folder and encode at FPS/N (2 gives 15 fps)")
    parser.add_argument("--engine", choices=sorted(profiles.ENGINES), help="override the profile's render engine")
    parser.add_argument("--samples", type=int, help="override the profile's sample count")
    parser.add_argument("--scale", type=int, default=100, metavar="PERCENT", help="resolution scale (default 100)")
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "optix", "cuda", "hip", "metal", "oneapi"),
                        help="Cycles device (default: best available GPU)")
    parser.add_argument("--audio", help="music file (default: the audio file in audio/)")
    parser.add_argument("--resume", "--skip-existing", dest="resume", action="store_true",
                        help="skip frames already rendered: a complete PNG at the profile's resolution (same settings assumed)")
    parser.add_argument("--output-dir", metavar="DIR",
                        help="where the full-rate frames go (default renders/<profile>/frames): the one canonical "
                             "sequence, wherever there is room for it")
    parser.add_argument("--start-frame", type=int, metavar="N", help="first frame, absolute (instead of --start)")
    parser.add_argument("--end-frame", type=int, metavar="N",
                        help="last frame, absolute and inclusive (instead of --end). A frame range is a chunk of the "
                             "master PNG sequence in renders/<profile>/frames/: it is never encoded on its own")
    parser.add_argument("--no-encode", action="store_true", help="render frames only")
    parser.add_argument("--encode-only", action="store_true", help="encode frames already rendered")
    parser.add_argument("--open", action="store_true", help="build the scene and open it in Blender for inspection")
    parser.add_argument("--save-blend", action="store_true", help="also save the built scene as a .blend")
    parser.add_argument("--blender", default=os.environ.get("BLENDER"), help="path to the Blender executable")
    parser.add_argument("--ffmpeg", default=os.environ.get("FFMPEG"), help="path to ffmpeg")
    parser.add_argument("--verbose", action="store_true", help="show all of Blender's output")
    args = parser.parse_args()

    chunk = args.start_frame is not None or args.end_frame is not None
    if chunk:
        if args.start_frame is None or args.end_frame is None:
            parser.error("--start-frame and --end-frame go together")
        if args.stills or args.step > 1 or args.encode_only:
            parser.error("a frame range renders the master sequence: no --stills, --step or --encode-only")
        first, last = args.start_frame, args.end_frame
        start, end = timeline.time_of(first), timeline.time_of(last + 1)
        args.no_encode = True
    else:
        start, end = timeline.parse_time(args.start), timeline.parse_time(args.end)
        first, last = timeline.frame_of(start), timeline.frame_of(end) - 1
    if last < first:
        parser.error("the range ends before it starts")
    count = last - first + 1

    out_root = os.path.join(ROOT, "renders", args.profile)
    os.makedirs(out_root, exist_ok=True)
    span = "f%06d-%06d" % (first, last)

    blender_args = ["--profile", args.profile, "--first", str(first), "--last", str(last),
                    "--scale", str(args.scale), "--device", args.device]
    if args.engine:
        blender_args += ["--engine", args.engine]
    if args.samples:
        blender_args += ["--samples", str(args.samples)]
    if args.resume:
        blender_args.append("--resume")
    if args.save_blend:
        blender_args += ["--save-blend", os.path.join(out_root, "pd_%s_%s.blend" % (args.profile, span))]

    if args.open:
        run_blender(args, blender_args + ["--open"], background=False)
        return

    if args.stills:
        n = max(1, min(args.stills, count))
        frames = sorted({first + round(i * (count - 1) / max(1, n - 1)) for i in range(n)})
        frames_dir = os.path.join(out_root, "stills")
        if not args.encode_only:
            run_blender(args, blender_args + ["--out", frames_dir, "--frames", ",".join(map(str, frames))])
        if not args.no_encode:
            contact_sheet(args, frames_dir, frames, os.path.join(out_root, "contact_%s_%s.png" % (args.profile, span)))
        return

    if args.step > 1:
        # A review clip at a reduced frame rate. Its frames never mix with the full-rate ones.
        frames = list(range(first, last + 1, args.step))
        frames_dir = os.path.join(out_root, "frames_step%d" % args.step)
        if not args.encode_only:
            print("Rendering %s  %s - %s  every %d frames (%d frames)" % (
                args.profile, timeline.format_time(start), timeline.format_time(end), args.step, len(frames)))
            run_blender(args, blender_args + ["--out", frames_dir, "--frames", ",".join(map(str, frames))])
        if not args.no_encode:
            encode(args, frames_dir, first, last,
                   os.path.join(out_root, "pd_%s_%s_%dfps.mp4" % (args.profile, span, timeline.FPS // args.step)), frames)
        return

    frames_dir = os.path.abspath(args.output_dir) if args.output_dir else os.path.join(out_root, "frames")
    if not args.encode_only:
        todo = list(range(first, last + 1))
        if args.resume:
            profile = profiles.PROFILES[args.profile].with_overrides(scale=args.scale)
            todo = [f for f in todo if not png_complete(frame_path(frames_dir, f), profile.width, profile.height)]
            if not todo:
                print("All %d frames %d-%d are already rendered in %s." % (count, first, last, frames_dir))
                return
        print("Rendering %s  %s - %s  (frames %d-%d: %d to render, %d already done)" % (
            args.profile, timeline.format_time(start), timeline.format_time(end), first, last, len(todo), count - len(todo)))
        # Build only as much of the film as the frames still to render span.
        blender_args[blender_args.index("--first") + 1] = str(todo[0])
        blender_args[blender_args.index("--last") + 1] = str(todo[-1])
        run_blender(args, blender_args + ["--out", frames_dir, "--frames", ",".join(map(str, todo))])
    if not args.no_encode:
        encode(args, frames_dir, first, last, os.path.join(out_root, "pd_%s_%s.mp4" % (args.profile, span)))


# ---------------------------------------------------------------- blender


def find_blender(explicit):
    if explicit:
        if not os.path.exists(explicit):
            sys.exit("Blender not found at %r." % explicit)
        return explicit
    found = shutil.which("blender")
    if found:
        return found
    candidates = []
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            candidates += glob.glob(os.path.join(base, "Blender Foundation", "*", "blender.exe"))
    candidates += glob.glob("/Applications/Blender*.app/Contents/MacOS/Blender")
    if not candidates:
        sys.exit("Blender not found. Put it on PATH, pass --blender, or set the BLENDER environment variable.")
    return sorted(candidates)[-1]


def run_blender(args, script_args, background=True):
    command = [find_blender(args.blender)]
    if background:
        command.append("-b")
    # Factory settings: the result must not depend on anyone's preferences or add-ons.
    command += ["--factory-startup", "--python-exit-code", "1",
                "--python", os.path.join(ROOT, "tools", "blender_entry.py"), "--"] + script_args

    if not background:
        subprocess.Popen(command)
        print("Opening Blender with the built scene. Scrub the timeline or press Space to play.")
        return

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    tail = []
    for line in process.stdout:
        line = line.rstrip()
        tail = (tail + [line])[-40:]
        if args.verbose or line.startswith("[pd]"):
            print(line, flush=True)
    if process.wait() != 0:
        if not args.verbose:
            print("\n".join(tail))
        sys.exit("Blender exited with code %d." % process.returncode)


# ---------------------------------------------------------------- ffmpeg


def find_ffmpeg(explicit):
    found = explicit or shutil.which("ffmpeg")
    if not found or not (os.path.exists(found) or shutil.which(found)):
        sys.exit("ffmpeg not found. Put it on PATH, pass --ffmpeg, or set the FFMPEG environment variable.")
    return found


def find_audio(explicit):
    if explicit:
        if not os.path.exists(explicit):
            sys.exit("Audio file not found: %r." % explicit)
        return explicit
    folder = os.path.join(ROOT, "audio")
    if os.path.isdir(folder):
        tracks = sorted(f for f in os.listdir(folder) if f.lower().endswith(AUDIO_EXTENSIONS))
        if tracks:
            return os.path.join(folder, tracks[0])
    return None


def frame_path(frames_dir, frame):
    return os.path.join(frames_dir, "frame_%06d.png" % frame)


def png_complete(path, width, height):
    """Whether a file is a whole PNG of the given size: the signature, a header with that width and
    height, and the closing IEND chunk (a render cut off while being written has none)."""
    try:
        size = os.path.getsize(path)
        if size < 57:
            return False
        with open(path, "rb") as handle:
            head = handle.read(24)
            handle.seek(size - 12)
            tail = handle.read(12)
    except OSError:
        return False
    return (head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR"
            and int.from_bytes(head[16:20], "big") == width and int.from_bytes(head[20:24], "big") == height
            and tail[4:8] == b"IEND")


def encode(args, frames_dir, first, last, output, frames=None):
    """``frames``, if given, are the evenly spaced frames of a reduced-rate review clip."""
    step = (frames[1] - frames[0]) if frames and len(frames) > 1 else 1
    missing = [f for f in (frames or range(first, last + 1)) if not os.path.exists(frame_path(frames_dir, f))]
    if missing:
        sys.exit("Cannot encode: %d of %d frames are missing from %s (first missing: %d)." % (
            len(missing), last - first + 1, frames_dir, missing[0]))

    count = last - first + 1
    audio = find_audio(args.audio)
    final = args.profile == "final"
    command = [find_ffmpeg(args.ffmpeg), "-y", "-loglevel", "error"]
    if frames:
        listing = os.path.join(frames_dir, "frames.txt")
        with open(listing, "w", encoding="utf-8") as handle:
            for f in frames:
                name = os.path.basename(frame_path(frames_dir, f))
                handle.write("file '%s'%sduration %.6f%s" % (name, os.linesep, step / timeline.FPS, os.linesep))
        command += ["-f", "concat", "-safe", "0", "-i", listing, "-r", "%g" % (timeline.FPS / step)]
    else:
        command += ["-framerate", str(timeline.FPS), "-start_number", str(first),
                    "-i", os.path.join(frames_dir, "frame_%06d.png")]
    if audio:
        # Frame n is track time n / FPS, so the audio is simply cut at the same place.
        command += ["-ss", "%.6f" % timeline.time_of(first), "-t", "%.6f" % (count / timeline.FPS), "-i", audio,
                    "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "256k" if final else "160k"]
    command += ["-frames:v", str(len(frames) if frames else count), "-c:v", "libx264", "-preset", "slow" if final else "veryfast",
                "-crf", "14" if final else "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", output]
    subprocess.run(command, check=True)

    print("Video -> %s" % output)
    if audio:
        print("Audio: %s from %s" % (audio, timeline.format_time(timeline.time_of(first))))
    else:
        print("WARNING: the video is silent. No music file found: put the track in audio/ or pass --audio.")


def contact_sheet(args, frames_dir, frames, output):
    listing = os.path.join(frames_dir, "contact.txt")
    with open(listing, "w", encoding="utf-8") as handle:
        for frame in frames:
            handle.write("file '%s'\n" % frame_path(frames_dir, frame).replace("\\", "/"))
    columns = min(4, len(frames))
    rows = math.ceil(len(frames) / columns)
    subprocess.run([find_ffmpeg(args.ffmpeg), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listing,
                    "-vf", "scale=480:-2,tile=%dx%d:padding=4" % (columns, rows), "-frames:v", "1", output], check=True)
    os.remove(listing)
    print("Stills -> %s" % frames_dir)
    print("Contact sheet -> %s" % output)


if __name__ == "__main__":
    main()
