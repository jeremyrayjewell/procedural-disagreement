"""The field, 4:00-4:15: the compensation stops being a route and becomes the network.

At 4:00 twelve stations and a block pass function round the lane's end, one to the next. From
4:00 that way of working spreads outward from the route, station by station, as far as there
are stations; then the level's own structure joins it; then everything runs as one machine.

One number organises all of it: how far a thing stands from the lane. A station takes its part
when the spread reaches it, ten metres a beat, and from then on it works on that same clock, so
that what the nearer station finishes the further one begins. The route's own stations, which
were recruited one at a time while the camera watched, slip onto that clock. The large
structures move later, further and more slowly than any station.

The lane stays what it was. Nothing here moves anything in it, nothing goes into it, nothing
crosses it and nothing marks it. Structures that the lane cut respond on both sides of it at
the same moment, as if they were still one piece: that is the only relation across it.

Nothing here adds an object. Everything is a function of position and absolute time, is
profile-blind, and is exactly the compensation's own state at 4:00.0. From 4:25, where the
film's ending is already built, nothing here applies.
"""

import math
from functools import lru_cache

from . import hinge, landfill, network, prosthesis, refrain, stablehash, timeline
from .ease import smoother, window
from .vec import q_camera_look, q_rotate

START = prosthesis.END
#: The loudest bar of the passage: the fine runs begin to pair.
LINES = timeline.cue("climax_lines")
#: The harmony changes and the heaviest low hit of the passage follows: structure joins.
COUPLING = timeline.cue("climax_coupling")
#: The last run of heavy hits: everything, at once.
SATURATION = timeline.cue("climax_saturation")
#: The last heavy hit before the music gives way. Every large stroke arrives here.
PEAK = timeline.cue("climax_peak")
#: A target boundary: nothing after it is authored.
END = timeline.cue("climax_end")
#: From here the film's ending stands as it was built, and nothing in this module applies.
_ENDING = timeline.cue("ending_start")

DONOR, CARRIER, RECEIVER = prosthesis.DONOR, prosthesis.CARRIER, prosthesis.RECEIVER
_ROLES = (DONOR, CARRIER, RECEIVER)

#: Metres from the lane the spread covers in a beat.
SPREAD = 10.0


def active(t):
    return START < t < _ENDING


def reached(distance):
    """When the spread reaches something this many metres from the lane: on the beat grid."""
    return START + timeline.BEAT * round(distance / SPREAD)


# ---------------------------------------------------------------- stations


def _kits():
    return {kit.station: kit for kit in refrain.kits() + refrain.later_kits()}


@lru_cache(maxsize=None)
def distance(station):
    """Metres from a station to the lane. A station that acts as one with another on the
    route stands, for this, where that one does."""
    for partner, joins in prosthesis.PARTNERS:
        if station == partner:
            station = joins
    place = landfill.stations()[station]
    return network.lane_distance(place.x, place.y)


@lru_cache(maxsize=None)
def recruits():
    """{station: (role, when recruited)}: the route's stations as they were, and then every
    other station that has machinery. A new one's part is settled by where it stands on the
    grid, so that neighbours differ; its moment, by how far it stands from the lane."""
    result = {station: (role, when) for station, (role, when, _) in prosthesis.recruits().items()}
    for station, kit in sorted(_kits().items()):
        if station in result:
            continue
        cell = hinge.column_of(kit.x) + int((kit.y - hinge.row_y(0)) // 24.0 + 1)
        result[station] = (_ROLES[cell % 3], reached(distance(station)))
    return result


def role(station):
    entry = recruits().get(station)
    return entry[0] if entry else None


#: The route's stations slip onto the field's clock over this window. It is as long as a turn,
#: so that no station ever has to run backward to get there.
_SLIP_FROM = START + 1.5 * timeline.BAR


@lru_cache(maxsize=None)
def _slip(station):
    """Seconds a route station's clock has to move to stand where the spread would have put
    it. Nothing, for a station the spread recruited: it started there."""
    if station not in prosthesis.recruits():
        return 0.0
    when = recruits()[station][1]
    period = refrain.PERIOD
    return (reached(distance(station)) - when + period * 0.5) % period - period * 0.5


def turn(station, t):
    """Seconds into a station's current turn, or None before it has been recruited. Until the
    slip begins this is exactly the route's clock."""
    when = recruits()[station][1]
    if t < when:
        return None
    return (t - when - _slip(station) * smoother(window(t, _SLIP_FROM, SATURATION))) % refrain.PERIOD


def _act(q):
    """0..1: one part's stroke within a turn: out, held, and back. As on the route."""
    if q is None:
        return 0.0
    return smoother(window(q, 0.0, 1.4)) - smoother(window(q, 3.0, 4.3))


def acting(station, t):
    """Whether a recruited station's part is in motion at time t."""
    q = turn(station, t)
    return q is not None and (0.0 < q < 1.4 or 3.0 < q < 4.3)


@lru_cache(maxsize=None)
def hands_to(station):
    """The station a donor turns its head to. On the route, the next along it. In the field,
    the nearest station that stands further from the lane: function is passed outward."""
    if station in prosthesis.recruits():
        return prosthesis.next_on_path(station)
    kits = _kits()
    here = kits[station]
    others = [(math.hypot(kit.x - here.x, kit.y - here.y), other) for other, kit in kits.items() if other != station]
    further = [entry for entry in others if distance(entry[1]) > distance(station)]
    return min(further or others)[1]


def head_yaw(kit, t):
    if not active(t):
        return prosthesis.head_yaw(kit, t)
    base = network.base_head_yaw(kit, t)
    if role(kit.station) != DONOR:
        return base
    target = landfill.stations()[hands_to(kit.station)]
    hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
    to_next = math.degrees(math.atan2(target.x - hx, hy - target.y))
    swing = (to_next - base + 180.0) % 360.0 - 180.0
    return base + swing * _act(turn(kit.station, t))


def carriage(kit, t):
    if not active(t):
        return prosthesis.carriage(kit, t)
    run, extend = network.base_carriage(kit, t)
    if role(kit.station) != CARRIER:
        return run, extend
    act = _act(turn(kit.station, t))
    return run + (prosthesis.CARRIER_RUN - run) * act, extend + (refrain.CARRIAGE_EXTEND - extend) * act


def yoke_drop(kit, t):
    if not active(t):
        return prosthesis.yoke_drop(kit, t)
    drop = network.base_yoke_drop(kit, t)
    if role(kit.station) != RECEIVER:
        return drop
    return drop + (prosthesis.RECEIVER_DROP - drop) * _act(turn(kit.station, t))


def donor_reach(kit, t):
    """Metres a donor's head assembly has moved along its edge of the platform."""
    if not active(t):
        return prosthesis.donor_reach(kit, t)
    if role(kit.station) != DONOR:
        return 0.0
    return prosthesis.DONOR_REACH * _act(turn(kit.station, t))


# ---------------------------------------------------------------- the lane, kept clear


def lane_clearance(center, size, samples=9):
    """Metres from a footprint to the lane: zero if any part of it is inside."""
    nearest = None
    for i in range(samples):
        for j in range(samples):
            x = center[0] + size[0] * (i / (samples - 1.0) - 0.5)
            y = center[1] + size[1] * (j / (samples - 1.0) - 0.5)
            along, across = network.lane_coordinates(x, y)
            gap = math.hypot(max(0.0, -along, along - network.LANE_LENGTH), max(0.0, abs(across) - network.LANE_HALF_WIDTH))
            nearest = gap if nearest is None else min(nearest, gap)
    return nearest


def _piece_distance(piece):
    return network.lane_distance(piece.center[0], piece.center[1])


@lru_cache(maxsize=None)
def _standing():
    """Everything that stands on the level and is not fine: what a moving thing must not hit."""
    return tuple(piece for piece in hinge.pieces() if piece.kind in ("trunk", "main", "unit", "spur", "via", "bay"))


def _clear(piece, dx, dy, margin, ignore=(), kinds=None):
    """Whether a piece moved by up to (dx, dy) touches nothing that stands (itself, and
    anything belonging to the stations in ``ignore``, apart)."""
    cx, cy = piece.center[0] + dx * 0.5, piece.center[1] + dy * 0.5
    sx, sy = piece.size[0] + abs(dx), piece.size[1] + abs(dy)
    for other in _standing():
        if other is piece or (other.station >= 0 and other.station in ignore):
            continue
        if kinds is not None and other.kind not in kinds:
            continue
        if (abs(other.center[0] - cx) < (other.size[0] + sx) * 0.5 + margin
                and abs(other.center[1] - cy) < (other.size[1] + sy) * 0.5 + margin):
            return False
    return True


# ---------------------------------------------------------------- relays

#: Metres a plain block indexes along its trunk, and back, each turn.
RELAY_INDEX = 2.0
#: Fraction of the plain blocks within reach that take part: they are occasional.
_RELAYING = 0.6
#: Metres from the lane within which a plain block may; and no nearer than this.
_RELAY_REACH = (24.0, 150.0)
#: Metres every moving thing keeps from the lane, at least.
LANE_MARGIN = 2.0


@lru_cache(maxsize=None)
def relays():
    """{station: (when it first indexes, +1 or -1 along its trunk)}: plain blocks, with no
    machinery, that take part as station 224 did. A block may only if it has no bays, and its
    whole stroke touches nothing and stays well out of the lane."""
    kits = _kits()
    units = {piece.station: piece for piece in hinge.pieces() if piece.kind == "unit"}
    bays = [piece.center for piece in hinge.pieces() if piece.kind == "bay"]
    result = {}
    for station, place in enumerate(landfill.stations()):
        if station in kits or station == prosthesis.RELAY_STATION or station not in units:
            continue
        d = network.lane_distance(place.x, place.y)
        if not _RELAY_REACH[0] < d < _RELAY_REACH[1]:
            continue
        if stablehash.value(timeline.SEED + 71000, station) >= _RELAYING:
            continue
        if any(abs(x - place.x) < 0.1 and abs(y - place.y) < 12.0 for x, y, _ in bays):
            continue
        unit = units[station]
        for sign in (1, -1):
            reach = sign * RELAY_INDEX
            swept = (unit.center[0], unit.center[1] + reach * 0.5), (unit.size[0], unit.size[1] + RELAY_INDEX)
            # It slides along its own trunk, as 224 does, so the trunk is not in its way.
            if (_clear(unit, 0.0, reach, 0.5, ignore=(station,), kinds=("main", "unit", "spur", "bay"))
                    and lane_clearance(*swept) > 2.0 * LANE_MARGIN):
                result[station] = (reached(d), sign)
                break
    return result


def relay_offset(station, t):
    """Metres a relaying block is along its trunk from where it stands."""
    when, sign = relays()[station]
    if t < when:
        return 0.0
    return sign * RELAY_INDEX * _act((t - when) % refrain.PERIOD)


# ---------------------------------------------------------------- large structures

#: Metres every other fine run moves sideways, toward the next: they pair.
LINE_SHIFT = 1.0
#: Metres every other column of holding cells shears along itself: a grid becomes a bond.
CELL_SHEAR = 2.0
#: Metres the heavy main and the heavy trunk rise with the coupling, and how much further at
#: the peak.
BUS_RISE = (2.0, 1.0)
#: Metres every other trunk and main within reach rises at saturation.
RUN_RISE = 1.6
#: Metres from the lane within which they do.
RUN_REACH = 150.0
#: Seconds a large stroke takes: a bar. A station's takes 1.4.
_SLOW = timeline.BAR
#: Seconds from SATURATION to PEAK: the strokes that end together.
_LAST = PEAK - SATURATION


def _stroke(t, start, seconds):
    return smoother(window(t, start, start + seconds))


def _parity(value, pitch):
    return 1 if int(round(value / pitch)) % 2 == 0 else -1


@lru_cache(maxsize=None)
def part(piece):
    """What a piece of the level does in this passage: None, or a tuple whose first entry is
    its kind of movement. Nothing that lies in the lane does anything."""
    if network.intrusion(piece) is not None:
        return None
    d = _piece_distance(piece)
    if piece.kind in ("unit", "spur"):
        return ("relay", piece.station) if piece.station in relays() else None
    if piece.kind == "fine":
        along_y = piece.size[1] > piece.size[0]
        sign = _parity(piece.center[0] if along_y else piece.center[1], 4.0)
        dx, dy = (sign * LINE_SHIFT, 0.0) if along_y else (0.0, sign * LINE_SHIFT)
        for way in (1, -1):
            moved = (piece.center[0] + way * dx, piece.center[1] + way * dy)
            if lane_clearance(moved, piece.size) < LANE_MARGIN:
                return None
        return "line", dx, dy, LINES + timeline.BEAT * round(d / (4.0 * SPREAD))
    if piece.kind == "cell":
        sign = _parity(piece.center[0], 2.0)
        for way in (1, -1):
            moved = (piece.center[0], piece.center[1] + way * sign * CELL_SHEAR)
            if lane_clearance(moved, piece.size) < LANE_MARGIN:
                return None
        if not _clear(piece, 0.0, CELL_SHEAR, 0.3) or not _clear(piece, 0.0, -CELL_SHEAR, 0.3):
            return None
        # Column by column outward, and every one of them there before saturation.
        return "cell", sign, COUPLING + timeline.BEAT * min(round(d / (2.0 * SPREAD)), 3)
    if piece.kind in ("trunk", "main", "via"):
        run = _run_of(piece)
        if run is None or _under_a_platform(run):
            return None
        order = cut_order(run)
        if _is_bus(run):
            if order is None:
                # The heavy trunk is whole: it goes outward from where it meets the heavy main.
                order = abs(_index(run) - hinge.BUS_MAIN_ROW)
            return ("bus", COUPLING + timeline.BEAT * order) if order <= 8 else None
        d = _piece_distance(run)
        if d > RUN_REACH:
            return None
        steps = order - 1 if order is not None else round(d / 25.0)
        return "run", SATURATION + timeline.BEAT * 0.5 * min(steps, 6)
    return None


@lru_cache(maxsize=None)
def _under_a_platform(run):
    """Whether a run passes through a station that has machinery. Such a run stays down: risen,
    it would stand in the place the station keeps empty."""
    for kit in _kits().values():
        if abs(run.center[0] - kit.x) < run.size[0] * 0.5 + 4.0 and abs(run.center[1] - kit.y) < run.size[1] * 0.5 + 4.0:
            return True
    return False


def _line(run):
    """Which trunk or main a run is a length of."""
    return ("trunk", run.column) if run.kind == "trunk" else ("main", int(round(run.center[1] * 10)))


def _index(run):
    """A run's place along its trunk or main, counted in runs."""
    if run.kind == "trunk":
        return int(round((run.center[1] - hinge.row_y(0)) / 24.0))
    return int(round((run.center[0] - hinge.column_x(0)) / 24.0))


@lru_cache(maxsize=None)
def _cuts():
    """{trunk or main: where the lane cut it}: the places of its runs that lie in the lane."""
    result = {}
    for piece in hinge.pieces():
        if piece.kind in ("trunk", "main") and network.intrusion(piece) is not None:
            result.setdefault(_line(piece), []).append(_index(piece))
    return result


def cut_order(run):
    """For a run of a trunk or main that the lane cut: how many runs it is from the cut, 1 for
    the run next to it on either side. None for a run of a trunk or main that is whole. The
    two sides of a cut respond at the same moment, as if they were still one piece."""
    cut = _cuts().get(_line(run))
    if cut is None:
        return None
    return min(abs(_index(run) - place) for place in cut)


def _is_bus(run):
    return ((run.kind == "trunk" and run.column == hinge.BUS_TRUNK_COLUMN)
            or (run.kind == "main" and abs(run.center[1] - hinge.row_y(hinge.BUS_MAIN_ROW)) < 0.01))


@lru_cache(maxsize=None)
def _trunk_runs():
    return {(piece.column, int(round(piece.center[1] * 10))): piece for piece in hinge.pieces() if piece.kind == "trunk"}


def _run_of(piece):
    """The run a piece rises with: itself, or for a junction block the trunk run it stands on.
    None for a junction on a run that lies in the lane: it has nothing to rise with."""
    if piece.kind != "via":
        return piece
    column = hinge.column_of(piece.center[0])
    row = int((piece.center[1] - hinge.row_y(0) + 12.0) // 24.0)
    run = _trunk_runs().get((column, int(round(hinge.row_y(row) * 10))))
    if run is None or network.intrusion(run) is not None:
        return None
    return run


def moves(piece):
    return part(piece) is not None


def piece_offset(piece, t):
    """Metres a piece of the level is displaced by this passage. Zero at and before 4:00.0,
    and from 4:25.0."""
    if not active(t):
        return 0.0, 0.0, 0.0
    what = part(piece)
    if what is None:
        return 0.0, 0.0, 0.0
    kind = what[0]
    if kind == "relay":
        return 0.0, relay_offset(what[1], t), 0.0
    t = min(t, END)
    if kind == "line":
        # They pair, hold, and at saturation cross to pair with the neighbour on the other side.
        k = _stroke(t, what[3], _SLOW) - 2.0 * _stroke(t, SATURATION, _LAST)
        return what[1] * k, what[2] * k, 0.0
    if kind == "cell":
        k = _stroke(t, what[2], _SLOW) - 2.0 * _stroke(t, SATURATION, _LAST)
        return 0.0, what[1] * CELL_SHEAR * k, 0.0
    if kind == "bus":
        return 0.0, 0.0, BUS_RISE[0] * _stroke(t, what[1], _SLOW) + BUS_RISE[1] * _stroke(t, SATURATION, _LAST)
    return 0.0, 0.0, RUN_RISE * _stroke(t, what[1], _SLOW * 0.5)


# ---------------------------------------------------------------- sight

#: Metres further the level can be seen by the time the camera is high.
_SIGHT_MORE = 105.0


def sight_more(t):
    if not active(t):
        return 0.0
    return _SIGHT_MORE * smoother(window(t, START, START + 5.0 * timeline.BAR))


# ---------------------------------------------------------------- camera

#: Metres above the ground of the level, and degrees below the horizon, at 4:15.
_HEIGHT = 50.0
_PITCH = 32.0


@lru_cache(maxsize=None)
def _camera_keys():
    """It leaves 4:00 exactly as it arrives, travelling west. It bears left and climbs, backing
    away from the lane it has just gone round, and never stops."""
    start = prosthesis.camera_position(START)
    dt = 1.0 / 3000.0
    before = prosthesis.camera_position(START - dt)
    velocity = tuple((a - b) / dt for a, b in zip(start, before))
    g = hinge.GROUND
    return (
        (START, start, velocity),
        (START + 5.0, (120.6, 135.6, g + 19.0), (-2.3, -0.5, 2.5)),
        (START + 10.0, (109.4, 123.4, g + 35.0), (-2.1, -3.0, 3.4)),
        (END, (98.9, 105.6, g + _HEIGHT), (-1.6, -3.2, 2.0)),
    )


@lru_cache(maxsize=None)
def _look_keys():
    """Degrees clockwise from +y, and degrees below the horizon. It goes on turning right, as
    it was at 4:00, round to the lane."""
    dt = 1.0 / 3000.0

    def angles(t):
        f = q_rotate(prosthesis.camera_pose(t)[1], (0.0, 0.0, -1.0))
        return math.degrees(math.atan2(f[0], f[1])), -math.degrees(math.asin(f[2]))

    yaw0, pitch0 = angles(START)
    yaw1, pitch1 = angles(START - dt)
    dx, dy = network.lane_point(network.LANE_LENGTH * 0.5)
    final = _camera_keys()[-1][1]
    to_lane = math.degrees(math.atan2(dx - final[0], dy - final[1]))
    return (
        _smooth(yaw0, (yaw0 - yaw1) / dt, to_lane),
        ((START, pitch0, (pitch0 - pitch1) / dt), (START + 5.0, 16.0, 1.6), (START + 10.0, 26.0, 1.8),
         (END, _PITCH, 0.6)),
    )


#: The gaze's turn, as (seconds after 4:00, degrees turned to the right since 4:00). It does
#: its turning early, while the spread is still passing from station to station: fastest at
#: about 4:04, settling as the structure joins, and all but still from 4:08.5, so that what is
#: seen to move from then on is the level and not the view.
_TURN = ((1.0, 2.0), (2.0, 9.5), (3.0, 22.5), (4.0, 38.5), (5.0, 54.5), (6.25, 70.0), (7.5, 80.0), (8.5, 84.6),
         (10.0, 87.4), (11.25, 88.5), (12.5, 89.1), (14.375, 90.3))
#: Degrees a second it is turning as it arrives at 4:15.
_TURNING_AT_END = 3.0


def _smooth(yaw0, rate0, yaw_end):
    """Keys of (time, yaw, rate) through ``_TURN`` whose rates make the turn's acceleration
    continuous as well as its speed: a cubic spline with its speed fixed at both ends."""
    times = [START] + [START + at for at, _ in _TURN] + [END]
    values = [yaw0] + [yaw0 + turned for _, turned in _TURN] + [yaw_end]
    n = len(times)
    h = [times[i + 1] - times[i] for i in range(n - 1)]
    slope = [(values[i + 1] - values[i]) / h[i] for i in range(n - 1)]
    # Solve for the rates at the inner keys: each row says the acceleration is the same on
    # both sides of a key.
    lower, diagonal, upper, right = [0.0] * n, [1.0] * n, [0.0] * n, [0.0] * n
    right[0], right[-1] = rate0, _TURNING_AT_END
    for i in range(1, n - 1):
        lower[i], diagonal[i], upper[i] = h[i], 2.0 * (h[i - 1] + h[i]), h[i - 1]
        right[i] = 3.0 * (h[i] * slope[i - 1] + h[i - 1] * slope[i])
    for i in range(1, n):
        factor = lower[i] / diagonal[i - 1]
        diagonal[i] -= factor * upper[i - 1]
        right[i] -= factor * right[i - 1]
    rates = [0.0] * n
    rates[-1] = right[-1] / diagonal[-1]
    for i in range(n - 2, -1, -1):
        rates[i] = (right[i] - upper[i] * rates[i + 1]) / diagonal[i]
    rates[0], rates[-1] = rate0, _TURNING_AT_END
    return tuple(zip(times, values, rates))


def camera_position(t):
    if not active(t):
        return prosthesis.camera_position(t)
    return network.hermite(min(t, END), _camera_keys())


def camera_pose(t):
    """The hinge camera from 4:00 on: (position, rotation, vertical field of view)."""
    if not active(t):
        return prosthesis.camera_pose(t)
    t = min(t, END)
    yaw_keys, pitch_keys = _look_keys()
    yaw, pitch = math.radians(network.hermite(t, yaw_keys)), math.radians(network.hermite(t, pitch_keys))
    forward = (math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), -math.sin(pitch))
    return camera_position(t), q_camera_look(forward), prosthesis.camera_pose(START)[2]
