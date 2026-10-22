#!/usr/bin/env python3
"""The film's required assets: every file the final render, its encode and its checks read, with
size and SHA-256, so a render machine can prove it has exactly the intended media.

    python tools/assets_manifest.py            record: write assets/MANIFEST.json and docs/render_assets.md
    python tools/assets_manifest.py --verify   check this copy against assets/MANIFEST.json (exit 1 on any difference)

Code is not listed: Git carries it. These are the data and media files, project-relative.
Needs only the Python standard library.
"""

import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "assets", "MANIFEST.json")
TABLE = os.path.join(ROOT, "docs", "render_assets.md")

#: (pattern, group, purpose). Every pattern must match at least one file.
ASSETS = (
    ("audio/mix4_master_24bit.wav", "source media",
     "The definitive audio master (280.000 s, 44.1 kHz, 24-bit PCM stereo): the film's soundtrack, muxed by "
     "tools/render.py when encoding, and the source analysis/audio_features.json was measured from"),
    ("assets/video/crt/0[1-8].mp4", "source media",
     "The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py)"),
    ("cues/poc_0035_0105.json", "render", "The directorial cue file: every authored event time"),
    ("analysis/audio_features.json", "render",
     "The soundtrack measured (tools/analyze_audio.py, from the audio master: its SHA-1 is recorded inside): "
     "the envelopes the light leans with"),
    ("assets/lyrics/layout.json", "render", "Where every sung line is shown (tools/lyric_layout.py)"),
    ("assets/fonts/unifont/unifont_all-17.0.05.hex.gz", "render",
     "GNU Unifont 17.0.05, the lyric's only glyph source (no fallback)"),
    ("assets/fonts/unifont/unifont_all-17.0.05.hex.gz.sig", "licence and provenance", "GNU's signature for the font file"),
    ("assets/fonts/unifont/COPYING", "licence and provenance", "Unifont licence (GPL v2+ with the font embedding exception)"),
    ("assets/fonts/unifont/OFL-1.1.txt", "licence and provenance", "Unifont licence (SIL Open Font License 1.1)"),
    ("assets/fonts/unifont/SOURCE.txt", "licence and provenance", "Where the font came from"),
    ("assets/video/crt/canvas/stream.mp4", "render",
     "The CRT stream every screen plays (made from clips 01-08 by tools/make_crt_video.py; approved 2026-10-22)"),
    ("assets/video/crt/canvas/manifest.json", "render", "Which screen starts on which clip of the stream"),
    ("assets/textures/room_shell/retro_*_01/modulation.png", "render",
     "The look's low-resolution grey maps (tools/make_retro_maps.py)"),
    ("tests/reference/*.json", "checks", "The recorded locked sequences tools/check.py compares against"),
)
#: Generated maps that nothing reads (kept only if present; not required).
UNUSED = ("assets/textures/room_shell/retro_n64_01/modulation.png",)


def files():
    out = []
    for pattern, group, purpose in ASSETS:
        matches = sorted(p for p in glob.glob(os.path.join(ROOT, pattern)) if os.path.relpath(p, ROOT).replace(os.sep, "/") not in UNUSED)
        if not matches:
            sys.exit("Required asset missing: %s (%s)" % (pattern, purpose))
        for path in matches:
            out.append((os.path.relpath(path, ROOT).replace(os.sep, "/"), group, purpose))
    return out


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def record():
    entries = []
    for rel, group, purpose in files():
        path = os.path.join(ROOT, rel)
        entries.append({"path": rel, "group": group, "purpose": purpose, "bytes": os.path.getsize(path), "sha256": sha256(path)})
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"made_by": "tools/assets_manifest.py", "assets": entries}, handle, indent=1)
    lines = ["# Render assets", "",
             "Every data and media file the final render, its encode and its checks read (code is in Git).",
             "Made by `tools/assets_manifest.py`; check a copy with `python tools/assets_manifest.py --verify`.", "",
             "| Path | Group | Size | SHA-256 | Purpose |", "| --- | --- | --- | --- | --- |"]
    for e in entries:
        lines.append("| `%s` | %s | %s | `%s` | %s |" % (e["path"], e["group"], _size(e["bytes"]), e["sha256"], e["purpose"]))
    total = sum(e["bytes"] for e in entries)
    lines += ["", "%d files, %s." % (len(entries), _size(total)), ""]
    with open(TABLE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    print("Recorded %d assets (%s) in %s and %s." % (len(entries), _size(total), MANIFEST, TABLE))


def verify():
    if not os.path.exists(MANIFEST):
        sys.exit("No assets/MANIFEST.json to check against.")
    with open(MANIFEST, encoding="utf-8") as handle:
        entries = json.load(handle)["assets"]
    problems = []
    for e in entries:
        path = os.path.join(ROOT, e["path"])
        if not os.path.exists(path):
            problems.append("missing: %s" % e["path"])
        elif os.path.getsize(path) != e["bytes"] or sha256(path) != e["sha256"]:
            problems.append("different: %s (expected %s)" % (e["path"], e["sha256"]))
    if problems:
        print("\n".join(problems))
        sys.exit("%d of %d assets missing or different." % (len(problems), len(entries)))
    print("All %d assets present and identical to the manifest." % len(entries))


def _size(n):
    return "%.1f MB" % (n / 1e6) if n >= 1e5 else "%.1f kB" % (n / 1e3)


if __name__ == "__main__":
    verify() if "--verify" in sys.argv[1:] else record()
