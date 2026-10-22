"""The coda, 4:15-4:25: what the system keeps of someone who is not there.

Straight after the widest view of the network the film cuts back to the room, seen from the
outer frame. Nobody is on the plinth. What the room has instead is on its surfaces, in the two
conditions the station level carried in the background from 2:20: scrawls and ranked bars.

The refrain is sung twice. The first time the two conditions are set out: the scrawls first,
then, beside them and not out of them, the bars. The second time they are withdrawn: the
scrawls, piece by piece; then the bars, group by group and row by row, the last of them inside
the last sung word. At 4:25 nothing explicit is left, only the apparatus.

No mark is writing: a scrawl is a crooked walk of short straight pieces, a bar is a plain
rectangle in a ranked row. Everything is seeded, a function of absolute time, the same in every
profile, and absent outside the coda.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

from . import layout, outer, stablehash, timeline
from .ease import smoother, window
from .vec import q_axis_angle

START = outer.CODA_START
#: By the first "scrawls" the irregular marks are all there.
SCRAWLS = timeline.cue("coda_scrawls")
#: The ordered condition begins.
ORDER = timeline.cue("coda_order")
#: By the first "bars" the ranked rows are all there.
BARS = timeline.cue("coda_bars")
#: The second statement: withdrawal.
AGAIN = outer.CODA_AGAIN
#: The second "scrawls": the last irregular marks go inside the word.
UNSCRAWLED = timeline.cue("coda_unscrawled")
#: The bars begin to go.
WITHDRAW = outer.CODA_WITHDRAW
#: The second "bars": only the last group is left.
LAST = timeline.cue("coda_last")
#: The last sung word ends; nothing explicit is left.
SILENT = outer.CODA_SILENT
END = outer.ENDING_START

_SEED = timeline.SEED + 83000

#: Linear RGB. A scrawl is a pale scratch; a bar is brighter and flatter, as on the stations.
SCRAWL = (0.42, 0.43, 0.44)
BAR = (0.80, 0.81, 0.82)

#: Panels of the rear wall that carry scrawls, as (row, column): low and to the left, where
#: the wall is seen past the plinth.
SCRAWLED_PANELS = ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 4), (2, 4))
#: The traces: (row, first column, last column, whether it runs up into the row above instead
#: of along). Each runs the length of its panels.
SCRAWLED_RUNS = ((0, 1, 3, False), (1, 0, 2, False), (1, 4, 4, True))
#: Panels that carry ranked bars, in the order they come, with the one that goes last, last.
#: That one is the panel the outer frame sees behind the place the chest was.
BARRED_PANELS = ((2, 1), (0, 4), (1, 3))

_PANEL = (2.35, 2.0)        # a rear panel's width and height
_PROUD = 0.02               # metres a mark stands out of the surface it is on


@dataclass(frozen=True)
class Mark:
    """One small box of a surface condition, and when it is there."""
    #: "scrawl" or "bar".
    kind: str
    center: tuple
    size: tuple
    rotation: tuple
    #: Which of ``size`` is its length: the dimension it grows and shrinks along.
    long: int
    #: (start, seconds) of its arrival and of its going.
    arrives: tuple
    leaves: tuple
    #: For a bar: the unit direction, in the world, of the squared end it retracts toward.
    toward: tuple = (0.0, 0.0, 0.0)
    #: Where it is: "wall" or "floor"; and which group (panel, or floor patch) it belongs to.
    surface: str = "wall"
    group: int = 0


def _panel_face(row, col):
    """(x of its centre, y of its face, z of its centre) for a rear panel."""
    x, y, z = layout.back_panel_center(row, col)
    depth = stablehash.uniform(timeline.SEED, row * 5 + col, 0.05, 0.18)
    return x, layout.CHAMBER_Y_MAX - depth, z


def _face_at(x, z):
    """y of the face of the rear panel a point of the wall is on, or None on a seam or on a
    panel that carries no scrawl."""
    for row, col in SCRAWLED_PANELS:
        cx, y, cz = _panel_face(row, col)
        if abs(x - cx) < _PANEL[0] * 0.5 - 0.06 and abs(z - cz) < _PANEL[1] * 0.5 - 0.06:
            return y
    return None


def _trace(seed, start, heading, steps, step, limits, clear=0.34, base=None):
    """A crooked line that never comes back on itself: a walk that keeps turning a little,
    stays inside limits, and will not come within ``clear`` of any earlier part of itself. So it
    cannot close a loop or cross, which is what makes a mark look like a picture or a
    character. If it has nowhere to go, it stops short."""
    points = [start]
    for k in range(steps):
        u, v = points[-1]
        for attempt in range(7):
            turn = stablehash.uniform(seed, 10 + k * 7 + attempt, -42.0, 42.0)
            length = step * stablehash.uniform(seed, 400 + k, 0.6, 1.25)
            u2 = u + math.cos(math.radians(heading + turn)) * length
            v2 = v + math.sin(math.radians(heading + turn)) * length
            inside = limits[0] < u2 < limits[1] and limits[2] < v2 < limits[3]
            if base is not None and abs((heading + turn - base + 180.0) % 360.0 - 180.0) > 72.0:
                inside = False          # a trace keeps going the way it is going
            if inside and all(math.hypot(u2 - a, v2 - b) > clear for a, b in points[:-1]):
                heading += turn
                points.append((u2, v2))
                break
        else:
            # Hemmed in: turn right round once and try from there, or stop.
            heading += 150.0
            if k == steps - 1 or len(points) < 2:
                break
    return points


def _scrawls(result):
    # ---- on the rear wall: a few long traces, each running on across several panels and
    # broken wherever it meets a seam. A trace metres long, in no box, is not a character.
    strokes = []
    for group, (row, first, last, upward) in enumerate(SCRAWLED_RUNS):
        low = _panel_face(row, first)
        high = _panel_face(row + (1 if upward else 0), last)
        limits = (low[0] - _PANEL[0] * 0.5 + 0.15, high[0] + _PANEL[0] * 0.5 - 0.15,
                  low[2] - _PANEL[1] * 0.5 + 0.2, high[2] + _PANEL[1] * 0.5 - 0.2)
        s = _SEED + group * 211
        base = 90.0 if upward else 0.0
        start = ((limits[0] + limits[1]) * 0.5 + stablehash.uniform(s, 0, -0.5, 0.5), limits[2] + 0.1) if upward else (
            limits[0] + 0.1, (limits[2] + limits[3]) * 0.5 + stablehash.uniform(s, 0, -0.4, 0.4))
        length = (limits[3] - limits[2]) if upward else (limits[1] - limits[0])
        points = _trace(s, start, base, int(length / 0.3), 0.4, limits, clear=0.45, base=base)
        pieces = []
        for (u0, v0), (u1, v1) in zip(points, points[1:]):
            u, v = (u0 + u1) * 0.5, (v0 + v1) * 0.5
            face = _face_at(u, v)
            if face is None:
                continue                # a seam: the trace is broken here
            piece = math.hypot(u1 - u0, v1 - v0)
            angle = math.degrees(math.atan2(v1 - v0, u1 - u0))
            pieces.append(((u, face - _PROUD, v), (piece + 0.05, 2.0 * _PROUD, 0.09), q_axis_angle((0.0, 1.0, 0.0), -angle), False))
        # Short branches off it, every few pieces, to one side or the other: it is scratched,
        # not drawn. They are the first of it to go.
        for i in range(2, len(points) - 1, 3):
            (u0, v0), (u1, v1) = points[i], points[i + 1]
            along = math.degrees(math.atan2(v1 - v0, u1 - u0))
            side = 1.0 if (i // 3 + group) % 2 else -1.0        # alternately to either side
            angle = along + side * stablehash.uniform(s, 720 + i, 48.0, 80.0)
            reach = stablehash.uniform(s, 740 + i, 0.2, 0.32)
            u, v = u0 + math.cos(math.radians(angle)) * reach * 0.5, v0 + math.sin(math.radians(angle)) * reach * 0.5
            face = _face_at(u, v)
            if face is not None and _face_at(u0, v0) is not None:
                pieces.append(((u, face - _PROUD, v), (reach, 2.0 * _PROUD, 0.07), q_axis_angle((0.0, 1.0, 0.0), -angle), True))
        strokes.append(("wall", group, pieces))
    # ---- on the floor, beside the plinth: longer walks, lying flat
    for k in range(5):
        s = _SEED + 5000 + k * 71
        # Either side of the plinth, where the outer frame sees the floor.
        bearing = math.radians((180.0 if k % 2 else 0.0) + stablehash.uniform(s, 0, -28.0, 34.0))
        radius = stablehash.uniform(s, 1, 3.3, 4.6)
        centre = (math.cos(bearing) * radius, math.sin(bearing) * radius)
        # Like the traces on the wall, it keeps going the way it is going: a wavering run
        # across the view, which cannot fold back into an outline.
        base = 180.0 if stablehash.value(s, 2) < 0.5 else 0.0
        points = _trace(s, (-1.9 if base == 0.0 else 1.9, 0.0), base, 9, 0.5, (-2.2, 2.2, -0.6, 0.6), clear=0.45, base=base)
        pieces = []
        for (u0, v0), (u1, v1) in zip(points, points[1:]):
            length = math.hypot(u1 - u0, v1 - v0)
            angle = math.degrees(math.atan2(v1 - v0, u1 - u0))
            pieces.append(((centre[0] + (u0 + u1) * 0.5, centre[1] + (v0 + v1) * 0.5, 0.03), (length + 0.06, 0.13, 0.03),
                           q_axis_angle((0.0, 0.0, 1.0), angle), False))
        strokes.append(("floor", len(SCRAWLED_RUNS) + k, pieces))

    # Each walk comes up on its own moment before the word, piece after piece. It stays whole
    # through the second statement until the word that names it, and goes inside that word:
    # branches first, then from both ends inward, so that it shortens and breaks before it is gone.
    count = len(strokes)
    for index, (surface, group, pieces) in enumerate(strokes):
        s = _SEED + 9000 + index * 37
        begins = START + (SCRAWLS - START - 1.1) * stablehash.value(s, 0)
        goes = UNSCRAWLED - 0.1 + 0.1 * ((index * 5) % count) / (count - 1.0)
        main = sum(1 for piece in pieces if not piece[3])
        for k, (center, size, rotation, branch) in enumerate(pieces):
            inward = min(k, main - 1 - k)
            comes = begins + (0.04 * k if not branch else 0.04 * main + 0.05)
            leaves = goes if branch else goes + 0.08 + 0.22 * inward / max(1.0, (main - 1) // 2) + 0.03 * stablehash.value(s, 20 + k)
            result.append(Mark("scrawl", center, size, rotation, 0, (comes, 0.3), (leaves, 0.2), surface=surface, group=group))


#: A bar's width and height, the pitch along a row, and the pitch between rows.
_BAR = (0.46, 0.24)
_BAR_PITCH = (0.55, 0.38)
#: How many bars each row of a panel has, from the top row down: ranked.
_RANKS = ((4, 3, 1), (4, 2, 1), (4, 3, 2, 1))


def _bars(result):
    for group, (row, col) in enumerate(BARRED_PANELS):
        x, y, z = _panel_face(row, col)
        ranks = _RANKS[group]
        left = x - (ranks[0] * _BAR_PITCH[0] - (_BAR_PITCH[0] - _BAR[0])) * 0.5
        top = z + (len(ranks) - 1) * _BAR_PITCH[1] * 0.5
        last = group == len(BARRED_PANELS) - 1
        # They come panel by panel and, within a panel, row by row from the top.
        comes = ORDER + (BARS - ORDER - 0.75) * group / (len(BARRED_PANELS) - 1.0)
        # They go panel by panel, row by row from the longest. The last panel goes inside the
        # last word, and its last row ends with it.
        if last:
            goes, per_row = LAST - 0.1, (SILENT - 0.2 - (LAST - 0.1)) / (len(ranks) - 1.0)
        else:
            goes, per_row = WITHDRAW + (LAST - 0.45 - WITHDRAW) * group / (len(BARRED_PANELS) - 1.0), 0.14
        for r, count in enumerate(ranks):
            for k in range(count):
                center = (left + _BAR[0] * 0.5 + k * _BAR_PITCH[0], y - _PROUD, top - r * _BAR_PITCH[1])
                result.append(Mark("bar", center, (_BAR[0], 2.0 * _PROUD, _BAR[1]), (1.0, 0.0, 0.0, 0.0), 0,
                                   (comes + 0.16 * r + 0.035 * k, 0.26), (goes + per_row * r + 0.02 * (count - 1 - k), 0.2),
                                   toward=(-1.0, 0.0, 0.0), surface="wall", group=group))


@lru_cache(maxsize=None)
def marks():
    """Every mark of the coda, in a fixed order: the scrawls, then the bars."""
    result = []
    _scrawls(result)
    _bars(result)
    return tuple(result)


def level(mark, t):
    """0..1: how far a mark is there. Nothing at or before 4:15.0, and nothing from 4:25.0."""
    if not START < t < END:
        return 0.0
    there = smoother(window(t, mark.arrives[0], mark.arrives[0] + mark.arrives[1]))
    if mark.kind == "scrawl":
        # The scrawls are faintly there from the first frame: they did not start with the cut.
        there = 0.3 + 0.7 * there
    return there * (1.0 - smoother(window(t, mark.leaves[0], mark.leaves[0] + mark.leaves[1])))


def pose(mark, t):
    """(location, scale, how far it stands out from its surface in tone, 0..1) of a mark at
    time t. Scale is all zeros when it is not there.

    A scrawl grows a little along itself as it comes, and shortens to nothing as it goes. A
    bar comes at its full size and goes by drawing back into its squared end."""
    amount = level(mark, t)
    if amount <= 0.0:
        return mark.center, (0.0, 0.0, 0.0), 0.0
    going = smoother(window(t, mark.leaves[0], mark.leaves[0] + mark.leaves[1]))
    coming = amount / (1.0 - going) if going < 1.0 else 0.0
    size = list(mark.size)
    center = mark.center
    if mark.kind == "scrawl":
        size[mark.long] *= (0.6 + 0.4 * coming) * (1.0 - going)
    else:
        size[mark.long] *= 1.0 - going
        shift = mark.size[mark.long] * 0.5 * going
        center = tuple(c + d * shift for c, d in zip(center, mark.toward))
    return center, tuple(size), coming


def extent(kind, t, surface=None):
    """How much of a condition is there: the summed length of its marks, in metres."""
    total = 0.0
    for mark in marks():
        if mark.kind == kind and (surface is None or mark.surface == surface):
            total += pose(mark, t)[1][mark.long]
    return total


def groups_present(kind, t):
    """Which groups of a condition still have anything there."""
    return sorted({mark.group for mark in marks() if mark.kind == kind and level(mark, t) > 0.0})
