"""Runs inside Blender. Works out, shot by shot, where each sung line is shown, and writes
assets/lyrics/layout.json, which presentation/lyrics.py and the look read.

    blender -b --factory-startup --python tools/lyric_layout.py -- [--profile final] [--step 3] [--only KEY ...]

Every sung line (lyrics.windows()) is stepped through with the film's own cameras. Of each of the
rear wall's 15 CRTs it asks, frame by frame: is all of its glass in the picture, facing the
camera, hidden by nothing, large enough to read, and lit by the film? The screens that are so for
nearly the whole line carry it, laid out at its phrase boundaries (lyrics.best_pack). If it does
not fit on them, the line is shown in the scene instead: a block of text fixed at one place in
the world, where it stays in the picture and readable for the whole line, is hidden by nothing,
and lies over empty space rather than over what is happening.

Occlusion is tested against each object's box (its mesh's bounds, posed): exact for the film's
boxes, on the side of hidden for its cylinders and spheres. See-through things (the ghosts, the
planes) hide nothing, and neither do the coda's marks, over which the lyric takes priority; but
world-space text is not put over the ghosts or the planes either: they are not empty space.

The final profile is measured by default: its geometry is what the film is seen with. Results are
merged into the file line by line, so a run can be repeated for some lines only.
"""

import json
import math
import os
import sys
import time

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from procedural_disagreement.core import choreography, coda, outer, profiles, timeline  # noqa: E402
from procedural_disagreement.presentation import lyrics, screens  # noqa: E402
from procedural_disagreement.scene import build, landfill, look  # noqa: E402

# This tool makes assets/lyrics/layout.json: its builds must not insist on finding it.
look.REQUIRE_ASSETS = False

#: A screen carries text if it passes on at least this share of the line's frames.
SHARE = 0.85
#: Least cosine between a screen's facing and the way to the camera.
FACING = 0.3
#: Least height of a screen's glass in the picture, in lines of a 1080-line frame, for text at two
#: screen pixels to a font pixel (one or two characters a screen) and at one (three or four).
READABLE = {2: 45.0, 1: 100.0}
#: Least light the film gives a panel (0..1 of its full authored light) for its screen to count.
LIT = 0.2
#: Where on a screen the text goes, in its 64 x 48 pixels (x0, x1, y0, y1; y down), by how many
#: characters it holds: one or two at two pixels a font pixel, three or four at one. That part of
#: the glass must be in the picture and hidden by nothing.
REGIONS = {1: (16, 48, 8, 40), 2: (0, 64, 8, 40), 3: (8, 56, 16, 32), 4: (0, 64, 16, 32)}
#: The points tested, in the same pixels.
XS = (0.5,) + tuple(range(4, 64, 4)) + (63.5,)
YS = (8.5,) + tuple(range(12, 40, 4)) + (39.5,)
#: What stops no ray: by name, and by material.
IGNORED = ("CodaScrawl", "CodaBar", look.LYRIC_TEXT)
SEE_THROUGH = ("PD_Ghost", "PD_Plane")
#: Lines measured in one build: the build bakes this much of the film at most.
CHUNK = 10.5

#: World-space text: characters a row at most; glyph height as a share of the frame's height.
WORLD_ROW = 8
WORLD_GLYPH = 0.036
#: Where it may sit, as the camera sees it in the middle of the line: share of the frame across
#: and up, and metres in front of the camera.
WORLD_ACROSS = (0.25, 0.5, 0.75)
WORLD_UP = (0.80, 0.70, 0.30, 0.20)
WORLD_DEPTH = (5.0, 8.0, 12.0, 18.0, 26.0, 40.0, 60.0)
#: It must stay this far inside the frame, and its glyphs within this range of their size in the
#: middle of the line.
WORLD_MARGIN = 0.04
WORLD_SIZE = (0.55, 1.8)
#: What world-space text may be seen against: the void, or these plain surfaces of the place, at
#: least WORLD_OFF times the text's own distance behind it (closer, it would read as written on
#: them). Rays look this far past the text, in multiples of its distance.
PLAIN = ("Wall", "Ceiling", "Floor", "PitCeiling", "PitFloor", "PitWall", "LevelGround", "LevelShell", "Waste")
WORLD_OFF = 0.3
WORLD_FAR = 40.0
#: How much worse than a line's own best place a place may score and still be usable for it, so
#: that consecutive lines can share one (continuity()).
WORLD_STAY = 0.2
#: If no place holds for the whole line, the text is shown for as long as one does: at least this.
WORLD_SHORTEST = 1.0

WIDTH, HEIGHT = 1920, 1080


class Measure:
    """The built scene, read for rays: every object a camera ray can meet, as a posed box."""

    def __init__(self, scene):
        self.scene = scene
        self.objects = list(scene.objects)
        n = len(self.objects)
        pit = bpy.data.collections.get(landfill.COLLECTION)
        below = {o.as_pointer() for o in pit.all_objects} if pit is not None else set()
        self.blocks = np.zeros(n, bool)
        self.see_through = np.zeros(n, bool)
        self.in_pit = np.zeros(n, bool)
        self.low = np.zeros((n, 3))
        self.high = np.zeros((n, 3))
        self.panels = {}
        for i, obj in enumerate(self.objects):
            self.in_pit[i] = obj.as_pointer() in below
            if obj.type != "MESH":
                continue
            corners = np.array([tuple(c) for c in obj.bound_box])
            self.low[i], self.high[i] = corners.min(axis=0), corners.max(axis=0)
            name = obj.name.split(".")[0]
            if name == "Panel":
                row = int(round((obj.location[2] - 1.25) / 2.25))
                col = int(round((obj.location[0] + 5.2) / 2.6))
                self.panels[(row, col)] = i
            material = obj.material_slots[0].material if obj.material_slots else None
            if name.startswith(IGNORED) or material is None:
                continue
            if material.name.startswith(SEE_THROUGH):
                self.see_through[i] = True
                continue
            self.blocks[i] = True
        assert len(self.panels) == 15, "expected the 15 rear panels, found %d" % len(self.panels)

    def at(self, frame):
        """Poses everything at a frame; returns the camera."""
        self.scene.frame_set(frame)
        n = len(self.objects)
        flat = np.empty(n * 16, np.float32)
        self.scene.objects.foreach_get("matrix_world", flat)
        # Stored column by column: transpose to rows.
        self.matrix = flat.reshape(n, 4, 4).transpose(0, 2, 1).astype(np.float64)
        colour = np.empty(n * 4, np.float32)
        self.scene.objects.foreach_get("color", colour)
        self.colour = colour.reshape(n, 4)
        seen = np.empty(n, bool)
        self.scene.objects.foreach_get("visible_camera", seen)
        hidden = np.empty(n, bool)
        self.scene.objects.foreach_get("hide_render", hidden)
        below = choreography.camera_is_below(timeline.time_of(frame))
        live = (self.blocks | self.see_through) & seen & ~hidden & (self.colour[:, 3] >= 0.05) & (below | ~self.in_pit)
        # A box with no size stops nothing.
        live &= np.abs(np.linalg.det(self.matrix[:, :3, :3])) > 1e-12
        self.live = np.flatnonzero(live)
        self.opaque = self.blocks[self.live]
        self.inverse = np.linalg.inv(self.matrix[self.live])
        # World bounds of each live box, to keep only those near a bundle of rays.
        centre = (self.low[self.live] + self.high[self.live]) * 0.5
        half = (self.high[self.live] - self.low[self.live]) * 0.5
        rot = self.matrix[self.live, :3, :3]
        world_centre = np.einsum("kij,kj->ki", rot, centre) + self.matrix[self.live, :3, 3]
        world_half = np.einsum("kij,kj->ki", np.abs(rot), half)
        self.box_low, self.box_high = world_centre - world_half, world_centre + world_half
        camera = self.scene.camera
        depsgraph = bpy.context.evaluated_depsgraph_get()
        projection = np.array(camera.calc_matrix_camera(depsgraph, x=WIDTH, y=HEIGHT))
        self.view = np.linalg.inv(np.array(camera.matrix_world))
        self.view_projection = projection @ self.view
        self.camera_matrix = np.array(camera.matrix_world)
        self.eye = self.camera_matrix[:3, 3].copy()
        self.tan = (1.0 / projection[0, 0], 1.0 / projection[1, 1])
        return camera

    def project(self, points):
        """(x, y) as shares of the frame (0..1 inside), and whether in front of the camera."""
        h = np.c_[points, np.ones(len(points))] @ self.view_projection.T
        w = h[:, 3]
        safe = np.where(np.abs(w) < 1e-9, 1e-9, w)
        return (h[:, :2] / safe[:, None] + 1.0) * 0.5, w > 1e-6

    def hits(self, targets, start=0.0, see_through=False, which=False):
        """For rays from the camera to each target: the nearest share of the way (start..1) at which
        a box is met, or inf (and, if `which`, the index of the object met, or -1). See-through
        things (ghosts, planes) count only if `see_through`: they hide nothing, but they are there to
        be seen."""
        targets = np.asarray(targets, np.float64)
        best = np.full(len(targets), np.inf)
        met_by = np.full(len(targets), -1)
        if not len(self.live):
            return (best, met_by) if which else best
        low = np.minimum(targets.min(axis=0), self.eye)
        high = np.maximum(targets.max(axis=0), self.eye)
        near = np.all(self.box_high >= low, axis=1) & np.all(self.box_low <= high, axis=1)
        near = np.flatnonzero(near if see_through else near & self.opaque)
        way = targets - self.eye
        for k in range(0, len(near), 384):
            pick = near[k:k + 384]
            inverse = self.inverse[pick]
            index = self.live[pick]
            o = np.einsum("kij,j->ki", inverse[:, :3, :3], self.eye) + inverse[:, :3, 3]
            d = np.einsum("kij,rj->kri", inverse[:, :3, :3], way)
            with np.errstate(divide="ignore", invalid="ignore"):
                t1 = (self.low[index][:, None, :] - o[:, None, :]) / d
                t2 = (self.high[index][:, None, :] - o[:, None, :]) / d
                enter = np.nanmax(np.fmin(t1, t2), axis=2)
                leave = np.nanmin(np.fmax(t1, t2), axis=2)
            enter = np.maximum(enter, start)
            met = (leave >= enter) & (enter < 1.0)
            nearest = np.where(met, enter, np.inf)
            first = nearest.argmin(axis=0)
            here = nearest[first, np.arange(len(targets))]
            closer = here < best
            best = np.where(closer, here, best)
            met_by = np.where(closer, index[first], met_by)
        return (best, met_by) if which else best


def glass(measure, row, col):
    """(test points on the screen's glass, its centre, its outward facing, its top and bottom
    middle), in the world. The points are at XS x YS of its 64 x 48 pixels."""
    i = measure.panels[(row, col)]
    matrix = measure.matrix[i]
    low, high = measure.low[i], measure.high[i]
    size = high - low
    mx, mz = look.SCREEN_BEZEL / 2.35, look.SCREEN_BEZEL / 2.0
    out = 0.002 / max(1e-9, np.linalg.norm(matrix[:3, 1]))
    columns, rows = screens.PIXELS

    def world(x, y):
        u, v = x / columns, 1.0 - y / rows
        return (matrix @ np.array([low[0] + size[0] * (mx + u * (1.0 - 2.0 * mx)), low[1] - out,
                                   low[2] + size[2] * (mz + v * (1.0 - 2.0 * mz)), 1.0]))[:3]

    points = np.array([world(x, y) for y in YS for x in XS])
    facing = -matrix[:3, 1] / np.linalg.norm(matrix[:3, 1])
    return points, world(columns * 0.5, rows * 0.5), facing, np.array([world(columns * 0.5, 0.0), world(columns * 0.5, rows)])


_PIXEL = np.array([(x, y) for y in YS for x in XS])
_IN_REGION = {per: (_PIXEL[:, 0] >= x0) & (_PIXEL[:, 0] <= x1) & (_PIXEL[:, 1] >= y0) & (_PIXEL[:, 1] <= y1)
              for per, (x0, x1, y0, y1) in REGIONS.items()}


def frames_of(start, end, step):
    first, last = timeline.frame_of(start), timeline.frame_of(end) - 1
    frames = list(range(first, last + 1, step))
    if frames[-1] != last:
        frames.append(last)
    return frames


def measure_screens(measure, frames):
    """{(row, col): record} of, frame by frame, whether each screen can carry text, and where."""
    record = {cell: {"pass": dict.fromkeys(REGIONS, 0), "out": 0, "hidden": 0, "dark": 0, "heights": []}
              for cell in measure.panels}
    for frame in frames:
        measure.at(frame)
        t = timeline.time_of(frame)
        for (row, col), i in measure.panels.items():
            r = record[(row, col)]
            points, centre, facing, ends = glass(measure, row, col)
            where, ahead = measure.project(points)
            inside = ahead & np.all(where >= 0.005, axis=1) & np.all(where <= 0.995, axis=1)
            toward = measure.eye - centre
            faces = float(facing @ toward) / max(1e-9, np.linalg.norm(toward)) > FACING
            if not faces or not inside.any():
                r["out"] += 1
                continue
            (_, top), (_, bottom) = measure.project(ends)[0]
            r["heights"].append(abs(top - bottom) * HEIGHT)
            light = float(measure.colour[i, :3].max()) / look.SCREEN_LIT
            awake = t >= screens.DARK_FROM or screens.wake(row, col, t) >= 0.99
            if light < LIT or not awake:
                r["dark"] += 1
                continue
            clear = inside & ~(measure.hits(points) < 1.0 - 1e-4)
            if not clear.all():
                r["hidden"] += 1
            for per, region in _IN_REGION.items():
                r["pass"][per] += bool(clear[region].all())
    return record


def _room(entry, row, col, per, scale):
    """The most characters a screen can take at a scale: one more than `per` if the part of its
    glass that many would occupy is readable, else `per`."""
    most = max(OPTIONS[scale])
    if per < most and entry["screens"]["%d,%d" % (row, col)]["share"][str(most)] >= SHARE:
        return most
    return per


def _spans(cols):
    """A wall row's usable columns, split where more than one screen between them cannot be read:
    a row of text may step over one hidden screen (the lamp in front of the middle, say) and read
    on, but not over more."""
    spans = []
    for col in cols:
        if spans and col - spans[-1][-1] <= 2:
            spans[-1].append(col)
        else:
            spans.append([col])
    return spans


#: Characters a screen, by scale (screen pixels a font pixel).
OPTIONS = {2: (1, 2), 1: (3, 4)}
#: In the coda the lyric goes round the panels with the ranked bars if it can: the bars are what
#: its second line names, and the last of them goes inside the last sung word.
CODA_CLEAR = coda.BARRED_PANELS


def _usable(entry, per, scale, avoid=()):
    """The screens of a measured line that can carry `per` characters at `scale`."""
    out = []
    for key, screen in entry["screens"].items():
        cell = tuple(int(v) for v in key.split(","))
        if screen["share"][str(per)] >= SHARE and screen["height"] >= READABLE[scale] and cell not in avoid:
            out.append(cell)
    return out


def crt_option(entry, scale, avoid=()):
    """The best layout of a measured line at a scale, as (cost, characters a screen,
    [[row, col, text]]), or None. Each row of text goes on the widest span of a wall row (of two as
    wide, the one nearer the middle of the wall), centred on it. Cheapest breaks between rows
    first (lyrics.cost, and lyrics.CROWD for each character a screen beyond one), then fewest
    characters a screen."""
    groups = lyrics.GROUPS[entry["line"]]
    found = []
    for per in OPTIONS[scale]:
        usable = _usable(entry, per, scale, avoid)
        rows = []
        for row in (2, 1, 0):
            cols = sorted(c for r, c in usable if r == row)
            if cols:
                rows.append((row, max(_spans(cols), key=lambda span: (len(span), -abs(sum(span) / len(span) - 2.0)))))
        texts = lyrics.pack(groups, [len(span) for _, span in rows], per) if rows else None
        if texts is None:
            continue
        cells, split, offset = [], 0, 0
        for (row, span), text in zip(rows, texts):
            # Over how many of the span's screens, centred on it: whole words to a screen where
            # it can be, a screen taking one more character than usual if its glass is clear for it.
            options = []
            for need in range(1, len(span) + 1):
                start = (len(span) - need) // 2
                chosen = span[start:start + need]
                limits = [_room(entry, row, col, per, scale) for col in chosen]
                result = lyrics.screens(groups, offset, text, limits, per)
                if result is not None:
                    options.append((result[0], result[1], need, chosen, result[2]))
            if not options:
                break
            c, _, _, chosen, pieces = min(options, key=lambda o: o[:3])
            split += c
            cells += [[row, col, piece] for col, piece in zip(chosen, pieces)]
            offset += len(text)
        else:
            found.append((lyrics.cost(groups, texts) + lyrics.CROWD * (per - 1) + split, per, cells))
    return min(found, key=lambda f: (f[0], f[1])) if found else None


def _blocks(lines):
    """Lines in runs sung together in one shot: the same camera, each starting as the last ends
    (the couplets, the refrain's repetitions). A block is shown in one way throughout: the brief
    allows a change from the CRTs to world-space text only at a cut."""
    out = []
    for e in lines:
        if out and e["camera"] == out[-1][-1]["camera"] and e["start"] - out[-1][-1]["end"] < 1.0:
            out[-1].append(e)
        else:
            out.append([e])
    return out


def assign(results):
    """Decides, block by block, CRTs or world-space text, and lays out the CRT lines. A block is on
    the CRTs if every line of it can be; its lines then share one size of text: two screen pixels
    a font pixel unless one breaks the lines more cheaply over the block."""
    for block in _blocks(sorted(results.values(), key=lambda e: e["start"])):
        coda_block = block[0]["start"] >= outer.CODA_START
        best = None
        for avoid in ((tuple(CODA_CLEAR), ()) if coda_block else ((),)):
            for scale in (2, 1):
                options = [crt_option(e, scale, avoid) for e in block]
                if all(options) and (best is None or sum(o[0] for o in options) < best[0]):
                    best = (sum(o[0] for o in options), scale, options, avoid)
            if best is not None:
                break
        for e in block:
            for name in ("scale", "per_screen", "cells", "avoid"):
                e.pop(name, None)
            e["mode"] = "crt" if best is not None else "world" if e["world"] is not None else "none"
        if best is None:
            continue
        for e, (_, per, cells) in zip(block, best[2]):
            e.update(scale=best[1], per_screen=per, cells=cells, avoid=[list(c) for c in best[3]])


def world_rows(line):
    return lyrics.best_pack(lyrics.GROUPS[line], [WORLD_ROW] * 3, (1,))[1]


def world_layout(measure, key, line, frames, start, end, step):
    """Where to fix the line's text in the world. Candidates are placed as the camera sees them at
    a few moments of the line (its middle first) and followed through all of it. A placement holds
    on a frame if the text is wholly in the picture, its glyphs are within WORLD_SIZE of their size
    when placed, and nothing hides it. The placement held longest wins, then the one over the
    emptiest space; if none holds for the whole line (the camera falls, say), the text is shown for
    as long as the winner holds, at least WORLD_SHORTEST, and never from later than WORLD_SHORTEST
    before the line's last syllable: a line is not put up after it has been sung. Returns (the
    placement, every placement that would do), or (None, [])."""
    rows = world_rows(line)
    across, up = max(len(r) for r in rows), len(rows) + (len(rows) - 1) * lyrics.WORLD_GAP / 16.0
    n = len(frames)
    anchors = sorted({frames[n // 2], frames[0], frames[-1], frames[n // 4], frames[(3 * n) // 4]},
                     key=lambda f: abs(f - frames[n // 2]))
    candidates = []
    for anchor in anchors:
        measure.at(anchor)
        eye, rotation = measure.eye.copy(), measure.camera_matrix[:3, :3].copy()
        tan_x, tan_y = measure.tan
        right, upward, forward = rotation[:, 0], rotation[:, 1], -rotation[:, 2]
        for depth in WORLD_DEPTH:
            glyph = WORLD_GLYPH * 2.0 * depth * tan_y
            for sy in WORLD_UP:
                for sx in WORLD_ACROSS:
                    centre = eye + forward * depth + right * (2 * sx - 1) * tan_x * depth + upward * (2 * sy - 1) * tan_y * depth
                    candidates.append({"anchor": [sx, sy, depth], "at": frames.index(anchor), "centre": centre,
                                       "glyph": glyph, "right": right, "up": upward, "rotation": rotation,
                                       "ok": [], "behind": {}})
    w_half, h_half = across * 0.5, up * 0.5
    grid = [(a, b) for b in np.linspace(-0.4, 0.4, 3) for a in np.linspace(-0.45, 0.45, 5)]
    for i, frame in enumerate(frames):
        measure.at(frame)
        for c in candidates:
            g, right, upward = c["glyph"], c["right"], c["up"]
            corners = np.array([c["centre"] + right * sx * w_half * g + upward * sy * h_half * g
                                for sx in (-1, 1) for sy in (-1, 1)])
            where, ahead = measure.project(corners)
            ok = bool(ahead.all() and (where >= WORLD_MARGIN).all() and (where <= 1.0 - WORLD_MARGIN).all())
            if ok:
                (_, a), (_, b) = measure.project(np.array([c["centre"] + upward * g * 0.5, c["centre"] - upward * g * 0.5]))[0]
                ok = WORLD_SIZE[0] * WORLD_GLYPH <= abs(a - b) <= WORLD_SIZE[1] * WORLD_GLYPH
            if ok:
                points = np.array([c["centre"] + right * sx * 2 * w_half * g + upward * sy * 2 * h_half * g for sx, sy in grid])
                ok = not (measure.hits(points, see_through=True) < 1.0 - 1e-4).any()
                if ok and (i % 4 == 0 or i == c["at"]):
                    # What it is seen against. Empty space is the void, or a plain surface of the
                    # place (PLAIN) not so close behind that the text would sit on it; anything
                    # else (the figure, a ghost, a panel, a conduit) is not empty, however far.
                    far = measure.eye + (points - measure.eye) * WORLD_FAR
                    met, by = measure.hits(far, start=1.0 / WORLD_FAR + 1e-4, see_through=True, which=True)
                    clear = []
                    for t, k in zip(met, by):
                        if k < 0:
                            clear.append(1.0)
                        elif measure.objects[k].name.split(".")[0].startswith(PLAIN):
                            clear.append(min(1.0, (t * WORLD_FAR - 1.0) / WORLD_OFF))
                        else:
                            clear.append(0.0)
                    c["behind"][i] = float(np.mean(clear))
            c["ok"].append(ok)
    sung_end = lyrics.sung(key)[1]
    viable = []
    for c in candidates:
        k = c["at"]
        if not c["ok"][k]:
            continue
        a = k
        while a > 0 and c["ok"][a - 1]:
            a -= 1
        b = k
        while b < n - 1 and c["ok"][b + 1]:
            b += 1
        shown = (start if a == 0 else timeline.time_of(frames[a]), end if b == n - 1 else timeline.time_of(frames[b] + 1))
        if shown[1] - shown[0] < min(WORLD_SHORTEST, end - start) or shown[0] > sung_end - WORLD_SHORTEST:
            continue
        behind = [v for i, v in c["behind"].items() if a <= i <= b]
        sx, sy, depth = c["anchor"]
        score = float(np.mean(behind)) + 0.1 * (sy > 0.5) - 0.05 * abs(math.log2(depth / 10.0))
        viable.append({"rows": rows, "centre": [round(float(v), 4) for v in c["centre"]],
                       "rotation": [round(float(v), 6) for v in _quaternion(c["rotation"])],
                       "glyph": round(float(c["glyph"]), 5),
                       "anchor": c["anchor"] + [round(timeline.time_of(frames[c["at"]]), 3)],
                       "shown": [round(v, 4) for v in shown], "held": b - a,
                       "score": round(score, 3), "behind": round(float(np.mean(behind)), 3)})
    if not viable:
        return None, []
    return max(viable, key=lambda v: (v["held"], v["score"])), viable


def _quaternion(m):
    """(w, x, y, z) of a rotation matrix."""
    w = math.sqrt(max(0.0, 1.0 + m[0, 0] + m[1, 1] + m[2, 2])) * 0.5
    x = math.copysign(math.sqrt(max(0.0, 1.0 + m[0, 0] - m[1, 1] - m[2, 2])) * 0.5, m[2, 1] - m[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1.0 - m[0, 0] + m[1, 1] - m[2, 2])) * 0.5, m[0, 2] - m[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1.0 - m[0, 0] - m[1, 1] + m[2, 2])) * 0.5, m[1, 0] - m[0, 1])
    return w, x, y, z


def window(measure, key, line, start, end, step):
    frames = frames_of(start, end, step)
    started = time.time()
    record = measure_screens(measure, frames)
    entry = {"key": key, "line": line, "text": lyrics.TEXT[line], "start": round(start, 4), "end": round(end, 4),
             "camera": measure.scene.camera.name, "frames": [frames[0], frames[-1]], "measured": len(frames),
             "screens": {}}
    usable, heights = {per: [] for per in REGIONS}, {}
    for (row, col), r in sorted(record.items()):
        heights[(row, col)] = float(np.median(r["heights"])) if r["heights"] else 0.0
        shares = {per: r["pass"][per] / float(len(frames)) for per in REGIONS}
        entry["screens"]["%d,%d" % (row, col)] = {
            "share": {str(per): round(v, 3) for per, v in shares.items()}, "height": round(heights[(row, col)], 1),
            "out": round(r["out"] / float(len(frames)), 3), "hidden": round(r["hidden"] / float(len(frames)), 3),
            "dark": round(r["dark"] / float(len(frames)), 3)}
        for per, share in shares.items():
            if share >= SHARE:
                usable[per].append((row, col))
    crt = any(crt_option(entry, scale) for scale in OPTIONS)
    # Placed in the world as well, whatever the screens can do: whether the line's block is on the
    # CRTs is decided once the whole block is measured (assign()).
    entry["world"], entry["_options"] = world_layout(measure, key, line, frames, start, end, step)
    print("[lyrics] %-12s %6.2f-%6.2f  %-12s CRTs %-3s  %s  (%.1f s)" % (
        key, start, end, entry["camera"], "yes" if crt else "no",
        "world: %s at %s" % (" / ".join(entry["world"]["rows"]), entry["world"]["anchor"]) if entry["world"] else "world: NONE",
        time.time() - started))
    sys.stdout.flush()
    return entry


def chunks(windows):
    out = []
    for w in sorted(windows, key=lambda w: w[2]):
        if out and w[3] - out[-1][0][2] <= CHUNK:
            out[-1].append(w)
        else:
            out.append([w])
    return out


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    profile, step, only = profiles.FINAL, 3, []
    while arguments:
        argument = arguments.pop(0)
        if argument == "--profile":
            profile = profiles.PROFILES[arguments.pop(0)]
        elif argument == "--step":
            step = int(arguments.pop(0))
        elif argument == "--only":
            only.append(arguments.pop(0))
        else:
            sys.exit("Unknown argument %r" % argument)
    windows = lyrics.windows()
    keys = {w[0] for w in windows}
    if only:
        missing = [k for k in only if k not in keys]
        if missing:
            sys.exit("Unknown line(s) %s. Known: %s" % (", ".join(missing), ", ".join(sorted(keys))))
        windows = [w for w in windows if w[0] in only]
    existing = lyrics.layout() or {}
    results = {e["key"]: e for e in existing.get("windows", []) if e["key"] in keys}
    os.makedirs(os.path.dirname(lyrics.LAYOUT), exist_ok=True)
    for chunk in chunks(windows):
        first, last = timeline.frame_of(chunk[0][2]), timeline.frame_of(chunk[-1][3])
        started = time.time()
        scene = build.build(profile, first, last)
        measure = Measure(scene)
        print("[lyrics] built %s-%s in %.0f s: %d objects, %d can stop a ray" % (
            timeline.format_time(chunk[0][2]), timeline.format_time(chunk[-1][3]), time.time() - started,
            len(measure.objects), int(measure.blocks.sum())))
        for key, line, start, end in chunk:
            results[key] = window(measure, key, line, start, end, step)
            write(results, profile, step)
    for e in sorted(results.values(), key=lambda e: e["start"]):
        if e["mode"] == "crt":
            text = " / ".join("".join(c[2] for c in e["cells"] if c[0] == row) for row in (2, 1, 0))
            where = "CRTs x%d, %d a screen: %s" % (e["scale"], e["per_screen"], " ".join("%d,%d" % (c[0], c[1]) for c in e["cells"]))
        elif e["mode"] == "world":
            text, where = " / ".join(e["world"]["rows"]), "world at %s, shown %s" % (e["world"]["anchor"], e["world"]["shown"])
        else:
            text, where = e["text"], "FAIL: nowhere"
        print("[lyrics] %-12s %7.2f-%7.2f  %-24s %s" % (e["key"], e["start"], e["end"], text, where))
    print("[lyrics] %d line(s) measured; %s" % (len(windows), lyrics.LAYOUT))


def continuity(results):
    """Keeps world-space text where it was from line to line within a shot (director, 2026-10-21).
    Consecutive lines of a block shown in the world share one place (across, up, depth, each as its
    own camera sees it) for as long as some place is usable for all of them: held as long as the
    line's best place is, and scoring within WORLD_STAY of it. Of the places they share, the one
    with the highest total score. A line measured in an earlier run keeps its place."""
    def usable(e):
        options = e.get("_options") or [e["world"]]
        held = max(o.get("held", 0) for o in options)
        top = max(o["score"] for o in options if o.get("held", 0) == held)
        found = {}
        for o in options:
            k = tuple(o["anchor"][:3])
            if o.get("held", 0) == held and o["score"] >= top - WORLD_STAY and (k not in found or o["score"] > found[k]["score"]):
                found[k] = o
        return found

    for block in _blocks(sorted(results.values(), key=lambda e: e["start"])):
        if block[0]["mode"] != "world":
            continue
        i = 0
        while i < len(block):
            run, shared = [usable(block[i])], set(usable(block[i]))
            while i + len(run) < len(block) and shared & set(usable(block[i + len(run)])):
                run.append(usable(block[i + len(run)]))
                shared &= set(run[-1])
            place = max(shared, key=lambda k: sum(u[k]["score"] for u in run))
            for e, u in zip(block[i:i + len(run)], run):
                e["world"] = u[place]
            i += len(run)


def write(results, profile, step):
    """Writes the file, every CRT line laid out, so that it is whole even if a run stops."""
    assign(results)
    continuity(results)
    data = {"made_by": "tools/lyric_layout.py", "profile": profile.name, "step": step,
            "windows": [{k: v for k, v in e.items() if not k.startswith("_")}
                        for e in sorted(results.values(), key=lambda e: e["start"])]}
    with open(lyrics.LAYOUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)


main()
