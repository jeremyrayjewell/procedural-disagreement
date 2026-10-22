"""The hinge, 1:52.5-2:20: leaving the individual case.

Above the pit there is a level the film has not shown: the level the chutes hang from. Seen
from there the scattered chutes turn out to be stations on a regular system. Every station
hangs by a short spur from a straight trunk; the trunks are parallel and evenly spaced; a few
heavier mains cross them. The waste is what lies under that system.

This module says what is on that level, how it is toned, and what of it can be seen when. It
is profile-blind and a function of position and absolute time only. The camera's flight up
through the level is in ``choreography``; the scene layer draws what is described here.

Nothing on this level can be seen from below (the pit's ceiling is in the way) or from inside
the chamber, so nothing here changes any frame before 1:52.5.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

from . import choreography as ch
from . import landfill, layout, stablehash, timeline
from .ease import smoother, window
from .vec import q_camera_look, sub

#: The flight leaves the locked flyover here.
START = timeline.TIMELINE_END
#: The pit's ceiling stops hiding the level above, and the level begins to show.
OPEN = timeline.cue("hinge_open")
#: The level is fully legible; the music starts to drain.
DRAIN = timeline.cue("hinge_drain")
#: The hard cut.
CUT = timeline.cue("hinge_cut")
#: A target boundary: nothing after it is authored.
END = timeline.cue("hinge_end")

#: z of the top of the pit's ceiling slab: the ground of the station level.
GROUND = -0.25
_STEP = 24.0            # the station grid's pitch (see landfill.stations)

#: Linear RGB of the parts of the system, before distance takes them.
TRUNK = (0.20, 0.21, 0.22)
MAIN = (0.27, 0.28, 0.29)
UNIT = (0.12, 0.125, 0.13)
SPUR = (0.16, 0.165, 0.17)
VIA = (0.31, 0.32, 0.33)
BAY = (0.12, 0.125, 0.13)
FINE = (0.15, 0.155, 0.16)
CELL = (0.105, 0.11, 0.115)

# Seen from high enough, the level has a hierarchy and regions, like the routing of a die:
# a very few heavy buses, the trunks and mains, and in some rectangular regions a fine local
# layer. None of it is anything but disposal plant; it is only very regular.

#: The one trunk and the one main that are heavy buses: (index, width, height).
_BUS_TRUNK = (11, 4.0, 1.5)
_BUS_MAIN = (14, 5.0, 1.6)
#: Rectangular regions of the grid, as (first column, last column, first row, last row, fill).
#: "lines-y" and "lines-x" are fine local runs along or across the trunks; "cells" is an array
#: of small holding cells. They lie ahead of where the camera comes up, and are not symmetric.
_REGIONS = (
    (10, 13, 12, 14, "cells"),
    (6, 9, 12, 15, "lines-y"),
    (11, 15, 9, 10, "lines-x"),
    (4, 7, 8, 10, "cells-wide"),
    (14, 16, 12, 15, "lines-x"),
)
#: Fraction of stations that have a row of bays either side of them, along their trunk.
_BAYED = 0.38

#: Every this-many-th row carries a main.
_MAIN_EVERY = 4


@dataclass(frozen=True)
class Piece:
    """One box on the station level."""
    #: "trunk", "main", "unit" or "spur".
    kind: str
    center: tuple
    size: tuple
    #: Which trunk it belongs to (trunks and their spurs and units), or -1.
    column: int
    #: Which station it serves (units and spurs), or -1.
    station: int


def _origin():
    """Corner of the station grid, and how many cells it has each way: as landfill.stations."""
    f = landfill.frame()
    half = layout.LANDFILL_SPAN * 0.5 - 12.0
    return f["centre"][0] - half, f["centre"][1] - half, int(2.0 * half / _STEP)


def column_x(i):
    return _origin()[0] + (i + 0.5) * _STEP


def row_y(j):
    return _origin()[1] + (j + 0.5) * _STEP


def column_of(x):
    return int((x - _origin()[0]) // _STEP)


def _near_chamber(center, size):
    """Whether a box would come within two metres of the chamber, which stands on this level."""
    half = layout.CHAMBER_HALF_WIDTH + 2.4
    return (abs(center[0]) - size[0] * 0.5 < half
            and layout.CHAMBER_Y_MIN - 2.4 < center[1] + size[1] * 0.5
            and center[1] - size[1] * 0.5 < layout.CHAMBER_Y_MAX + 2.4)


@lru_cache(maxsize=None)
def pieces():
    """Everything on the station level, in a fixed order."""
    x0, y0, n = _origin()
    result = []

    def box(kind, x_low, x_high, y_low, y_high, height, column=-1, station=-1):
        center = ((x_low + x_high) * 0.5, (y_low + y_high) * 0.5, GROUND + height * 0.5)
        size = (x_high - x_low, y_high - y_low, height)
        if not _near_chamber(center, size):
            result.append(Piece(kind, center, size, column, station))

    # Trunks: one straight line per column of the grid, the length of the field, in cell-long runs.
    # One of them is a heavy bus.
    for i in range(n):
        half, height = (_BUS_TRUNK[1] * 0.5, _BUS_TRUNK[2]) if i == _BUS_TRUNK[0] else (0.8, 0.75)
        for j in range(n):
            box("trunk", column_x(i) - half, column_x(i) + half, y0 + j * _STEP, y0 + (j + 1) * _STEP, height, column=i)
    # Mains: heavier, across the trunks, on every fourth row. One of them is a heavy bus.
    for j in range(_MAIN_EVERY // 2, n, _MAIN_EVERY):
        half, height = (_BUS_MAIN[1] * 0.5, _BUS_MAIN[2]) if j == _BUS_MAIN[0] else (1.3, 1.1)
        for i in range(n):
            box("main", x0 + i * _STEP, x0 + (i + 1) * _STEP, row_y(j) - half, row_y(j) + half, height)
    # Stations: a unit over every chute, square to the grid whatever way its chute is turned,
    # and a spur from it to its column's trunk.
    for index, station in enumerate(landfill.stations()):
        i = column_of(station.x)
        box("unit", station.x - 4.0, station.x + 4.0, station.y - 4.0, station.y + 4.0, 2.6, column=i, station=index)
        low, high = sorted((column_x(i), station.x))
        box("spur", low, high, station.y - 0.45, station.y + 0.45, 0.5, column=i, station=index)

    # ---- the finer structure. Everything above stays exactly as it was; this is appended.
    solid = [piece for piece in result if piece.kind in ("trunk", "main", "unit", "spur")]
    axis = n // 2       # the trunk the film is left with after the cut: nothing is added to it

    def clear(x_low, x_high, y_low, y_high, margin):
        """Whether a footprint stands clear of every trunk, main, unit and spur."""
        for piece in solid:
            if (abs(piece.center[0] - (x_low + x_high) * 0.5) < (piece.size[0] + x_high - x_low) * 0.5 + margin
                    and abs(piece.center[1] - (y_low + y_high) * 0.5) < (piece.size[1] + y_high - y_low) * 0.5 + margin):
                return False
        return True

    # Junctions: where a spur meets its trunk there is a block standing a little proud of both.
    for index, station in enumerate(landfill.stations()):
        i = column_of(station.x)
        if i != axis:
            box("via", column_x(i) - 1.2, column_x(i) + 1.2, station.y - 1.2, station.y + 1.2, 1.5)
    # Bays: some stations have a row of two either side of them, in line along the trunk, so
    # that from far enough away a station is a short row of cells and not one square.
    for index, station in enumerate(landfill.stations()):
        if column_of(station.x) == axis or stablehash.value(timeline.SEED + 52000, index) >= _BAYED:
            continue
        for offset in (-9.4, -6.0, 6.0, 9.4):
            y = station.y + offset
            if clear(station.x - 3.0, station.x + 3.0, y - 1.3, y + 1.3, 0.3):
                box("bay", station.x - 3.0, station.x + 3.0, y - 1.3, y + 1.3, 1.5)
    # Regions: a fine local layer, lower than everything it runs between.
    for first_i, last_i, first_j, last_j, fill in _REGIONS:
        left, right = x0 + first_i * _STEP, x0 + (last_i + 1) * _STEP
        bottom, top = y0 + first_j * _STEP, y0 + (last_j + 1) * _STEP
        if fill == "lines-y":
            x = left + 4.0
            while x < right - 2.0:
                if min(abs(x - column_x(i)) for i in range(n)) > 2.0:
                    for j in range(first_j, last_j + 1):
                        box("fine", x - 0.3, x + 0.3, y0 + j * _STEP, y0 + (j + 1) * _STEP, 0.3)
                x += 4.0
        elif fill == "lines-x":
            y = bottom + 4.0
            while y < top - 2.0:
                if min(abs(y - row_y(j)) for j in range(n) if j % _MAIN_EVERY == _MAIN_EVERY // 2) > 4.0:
                    for i in range(first_i, last_i + 1):
                        box("fine", x0 + i * _STEP, x0 + (i + 1) * _STEP, y - 0.3, y + 0.3, 0.3)
                y += 4.0
        else:
            size, pitch = ((3.2, 5.2), (6.0, 8.0)) if fill == "cells" else ((5.0, 5.0), (8.0, 8.0))
            x = left + pitch[0] * 0.5
            while x < right:
                y = bottom + pitch[1] * 0.5
                while y < top:
                    if clear(x - size[0] * 0.5, x + size[0] * 0.5, y - size[1] * 0.5, y + size[1] * 0.5, 0.6):
                        box("cell", x - size[0] * 0.5, x + size[0] * 0.5, y - size[1] * 0.5, y + size[1] * 0.5, 0.9)
                    y += pitch[1]
                x += pitch[0]
    return tuple(result)


def _reach_centre():
    """The point the level is seen around: ahead of where the camera comes up through it."""
    return landfill.from_flight(150.0, 0.0)


#: The part of the level that keeps its full tone: a broad rectangle square to the trunks,
#: (x low, x high, y low, y high), and the metres over which it goes dark outside that. No
#: edge is drawn: the field is simply where the level can be seen.
_FIELD = (-20.0, 215.0, 20.0, 225.0)
_FIELD_EDGE = 50.0
#: The dark shell that stands in for distance: its radius and its height.
SHELL_RADIUS = 300.0
SHELL_HEIGHT = 330.0


def reach(x, y):
    """0..1: how much of its tone something on the level keeps. Like the field below, it
    darkens with distance until it cannot be told from the dark, well short of any edge."""
    outside = math.hypot(max(_FIELD[0] - x, 0.0, x - _FIELD[1]), max(_FIELD[2] - y, 0.0, y - _FIELD[3]))
    return 1.0 - smoother(window(outside, 0.0, _FIELD_EDGE))


def shell_centre():
    return _reach_centre()


# ---------------------------------------------------------------- what can be seen, and when


def ceiling_present(t):
    """Whether the pit's ceiling is there. It is, except while the camera rises through the
    level above it: what was simply darkness overhead turns out to have been this."""
    return not (OPEN <= t < CUT)


def emergence(t):
    """0..1: the level coming out of the dark as the camera approaches and passes it."""
    return smoother(window(t, OPEN, DRAIN))


@lru_cache(maxsize=None)
def _axis():
    """The one trunk left visible after the cut, the station left beside it, and where the
    camera stands: (column, station index, camera position, camera target)."""
    x0, y0, n = _origin()
    column = n // 2
    x = column_x(column)
    # A station on this column, north of the chamber, with clear trunk beyond it.
    candidates = [(station.y, index) for index, station in enumerate(landfill.stations())
                  if column_of(station.x) == column and 70.0 < station.y < row_y(n - 5)]
    y, index = min(candidates)
    station = landfill.stations()[index]
    side = 1.0 if station.x >= x else -1.0
    position = (x - side * 6.0, y - 46.0, GROUND + 2.6)
    target = (x - side * 0.5, y + 30.0, GROUND + 1.0)
    return column, index, position, target


def still_camera():
    """The camera after the cut: (position, rotation, vertical field of view). It does not
    move until 2:20."""
    _, _, position, target = _axis()
    return position, q_camera_look(sub(target, position)), layout.LOWER_CAMERA_FOV


def still_camera_position():
    return _axis()[2]


def still_camera_target():
    return _axis()[3]


def axis_column():
    """The trunk the film is left with after the cut."""
    return _axis()[0]


#: The row whose main is the heavy bus, and the column whose trunk is.
BUS_MAIN_ROW = _BUS_MAIN[0]
BUS_TRUNK_COLUMN = _BUS_TRUNK[0]


def region_bounds(index):
    """(x low, x high, y low, y high) of one of the level's rectangular regions."""
    x0, y0, _ = _origin()
    first_i, last_i, first_j, last_j, _ = _REGIONS[index]
    return x0 + first_i * _STEP, x0 + (last_i + 1) * _STEP, y0 + first_j * _STEP, y0 + (last_j + 1) * _STEP


def main_rows():
    return tuple(range(_MAIN_EVERY // 2, _origin()[2], _MAIN_EVERY))


#: Metres along the trunk, from the camera, by which the one remaining axis has gone dark.
_AXIS_FADE = 190.0


def visibility(piece, t):
    """0..1 factor on a piece's tone at time t.

    Before the level opens: nothing. While the camera rises through and over it: everything,
    as far as ``reach`` allows. After the cut: one trunk, fading along its length, and one
    station on it. REQUIRED STATE AT 2:20.0: exactly that, and nothing else."""
    if t < CUT:
        return emergence(t) * reach(piece.center[0], piece.center[1])
    left = _left_after_cut(piece)
    if t <= END:
        return left
    # From 2:20 the camera travels, and the level comes out of the dark as far as it can see.
    from . import refrain
    return max(left, refrain.seen(piece.center, t))


def _left_after_cut(piece):
    column, station, position, _ = _axis()
    if piece.kind == "trunk" and piece.column == column:
        ahead = piece.center[1] - position[1]
        return 1.0 - smoother(window(ahead, 30.0, _AXIS_FADE))
    if piece.station == station:
        return 0.55
    return 0.0
