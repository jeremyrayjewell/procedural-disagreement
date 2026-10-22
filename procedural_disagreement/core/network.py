"""The network, 3:00-3:30: one system, and then the absence it is organised around.

Until 3:00 every station runs the same procedure on its own time, each a beat or two after its
neighbour. From 3:00 that changes in kind.

3:00-3:20. The stations stop being many machines doing the same thing. Around the junction of
the heavy trunk and the heavy main, ring by ring, they fall into step: each ring of stations
comes to share one phase, and neighbouring rings stand exactly one bar apart, so that what one
ring finishes the next begins. Two large structures take part: a whole array of holding cells
indexes down and back, and a length of the heavy main rises and settles.

3:20-3:30. The bass goes. Through the stations there runs a diagonal lane in which nothing
stands. Nothing marks it. From 3:20 the stations along it leave their own empty platforms and
turn to it; their procedures stop short and hold; the low cells that lay across the lane
withdraw into the ground, and the trunks that cross it sink. The camera is travelling down it.

Everything is a function of position and absolute time, is profile-blind, and is exactly the
refrain's own state at 3:00.0. Nothing here is drawn except through what the scene layer does
with stations and pieces that already exist.
"""

import math
from functools import lru_cache

from . import hinge, refrain, timeline
from .ease import smoother, window
from .vec import q_camera_look

START = refrain.END
#: The array of cells indexes down and the heavy main rises; and when they return.
RESPONSE = timeline.cue("network_response")
RELEASE = timeline.cue("network_release")
#: The bass drops out. The network turns to the lane.
VOID = timeline.cue("network_void")
#: A target boundary: nothing after it is authored.
END = timeline.cue("network_end")


def hermite(t, keys):
    """A value that passes through ``keys`` = ((time, value, rate), ...) with those rates:
    piecewise cubic, so it is closed-form and has no corners. Values may be tuples."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for (t0, p0, v0), (t1, p1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            h = t1 - t0
            u = (t - t0) / h
            a = 2 * u ** 3 - 3 * u ** 2 + 1
            b = (u ** 3 - 2 * u ** 2 + u) * h
            c = -2 * u ** 3 + 3 * u ** 2
            d = (u ** 3 - u ** 2) * h
            if isinstance(p0, tuple):
                return tuple(a * x0 + b * w0 + c * x1 + d * w1 for x0, w0, x1, w1 in zip(p0, v0, p1, v1))
            return a * p0 + b * v0 + c * p1 + d * v1
    return keys[-1][1]


# ---------------------------------------------------------------- the lane

#: Where the lane starts, its direction (degrees from +x toward +y), its length, and half the
#: width in which nothing stands above the low routing. It is not built: it was found. It is
#: the widest straight gap among the stations ahead of where the refrain ends.
LANE_START = (121.0, 187.8)
LANE_ANGLE = -35.0
LANE_LENGTH = 60.0
LANE_HALF_WIDTH = 8.0


def lane_direction():
    a = math.radians(LANE_ANGLE)
    return math.cos(a), math.sin(a)


def lane_coordinates(x, y):
    """(metres along the lane from its start, metres to its left) of a point."""
    dx, dy = lane_direction()
    px, py = x - LANE_START[0], y - LANE_START[1]
    return px * dx + py * dy, -px * dy + py * dx


def lane_distance(x, y):
    """Metres from a point to the lane's axis (to its nearer end, beyond the ends)."""
    along, across = lane_coordinates(x, y)
    beyond = max(0.0, -along, along - LANE_LENGTH)
    return math.hypot(across, beyond)


def lane_point(along):
    dx, dy = lane_direction()
    return LANE_START[0] + dx * along, LANE_START[1] + dy * along


# ---------------------------------------------------------------- camera

_LANE_SPEED = 5.5
#: Degrees below the horizon the camera looks while the lane lasts.
LANE_PITCH = 10.0
#: Metres above the ground of the level: over the heavy main, and in the lane.
_OVER, _IN = 12.25, 6.25


@lru_cache(maxsize=None)
def _camera_keys():
    """The flight as keys of (time, position, velocity). It leaves 3:00 exactly as the refrain
    arrives: same place, same velocity."""
    start = refrain.camera_position(START)
    dt = 1.0 / 3000.0
    before = refrain.camera_position(START - dt)
    velocity = tuple((a - b) / dt for a, b in zip(start, before))
    dx, dy = lane_direction()
    g = hinge.GROUND

    def lane(along, z):
        x, y = lane_point(along)
        return x, y, g + z

    into = (_LANE_SPEED * dx, _LANE_SPEED * dy, 0.0)
    return (
        (START, start, velocity),
        # Onto the line of the heavy main, along its south side.
        (START + 7.0, (66.0, 185.0, g + 10.0), (4.2, 0.0, 0.35)),
        # Across the trunks, toward the junction of the heavy trunk and the heavy main.
        (START + 16.0, (102.0, 185.2, g + _OVER), (4.2, 0.0, 0.0)),
        # Over the junction and down, turning into the lane as the bass leaves.
        (VOID, lane(-1.5, 10.5), (_LANE_SPEED * 0.93, _LANE_SPEED * -0.36, -0.9)),
        (VOID + 4.0, lane(19.0, _IN + 0.4), (into[0], into[1], -0.15)),
        (END, lane(52.0, _IN), into),
    )


@lru_cache(maxsize=None)
def _look_keys():
    """Where the camera looks: degrees east of +y, and degrees below the horizon."""
    dt = 1.0 / 3000.0

    def angles(t):
        from .vec import q_rotate
        f = q_rotate(refrain.camera_pose(t)[1], (0.0, 0.0, -1.0))
        return math.degrees(math.atan2(f[0], f[1])), -math.degrees(math.asin(f[2]))

    yaw0, pitch0 = angles(START)
    yaw1, pitch1 = angles(START - dt)
    lane = 90.0 - LANE_ANGLE
    return (
        ((START, yaw0, (yaw0 - yaw1) / dt), (START + 6.0, 92.0, 0.5), (START + 16.0, 90.0, 0.0),
         (VOID + 1.0, lane - 4.0, 4.0), (VOID + 4.0, lane, 0.0), (END, lane, 0.0)),
        # It comes into the lane looking 10 degrees down and keeps looking down while the lane
        # lasts, so that the lane's floor is in the picture. From 3:27, as the lane runs out, it
        # lifts its gaze again: what is beyond the lane comes back into view, and is meant to.
        ((START, pitch0, (pitch0 - pitch1) / dt), (START + 10.0, 11.0, 0.0), (VOID, 10.0, -0.4),
         (VOID + 1.5, 9.6, 0.0), (VOID + 4.0, LANE_PITCH, 0.0), (VOID + 7.0, LANE_PITCH, 0.0), (END, 5.0, -0.8)),
    )


def camera_position(t):
    if t > END:
        from . import climax
        return climax.camera_position(t)
    return hermite(t, _camera_keys())


def camera_pose(t):
    """The hinge camera from 3:00 on: (position, rotation, vertical field of view)."""
    if t > END:
        from . import climax
        return climax.camera_pose(t)
    yaw_keys, pitch_keys = _look_keys()
    yaw, pitch = math.radians(hermite(t, yaw_keys)), math.radians(hermite(t, pitch_keys))
    forward = (math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), -math.sin(pitch))
    return camera_position(t), q_camera_look(forward), refrain.camera_pose(START)[2]


# ---------------------------------------------------------------- stations fall into step

#: The junction the organisation spreads from: the heavy trunk and the heavy main.
def hub():
    return hinge.column_x(hinge.BUS_TRUNK_COLUMN), hinge.row_y(hinge.BUS_MAIN_ROW)


_RING = 40.0            # metres between rings of stations around the hub
_RING_DELAY = 1.25      # seconds later each ring starts to fall into step
_LOCKING = 8.0          # seconds a station takes to do it


def ring(kit):
    hx, hy = hub()
    return int(round(math.hypot(kit.x - hx, kit.y - hy) / _RING))


@lru_cache(maxsize=None)
def _shift(kit):
    """Seconds a station's procedure has to slip to stand where its ring stands: every ring
    starts on a bar line, and each ring a bar after the one inside it."""
    target = START + (ring(kit) % 3) * timeline.BAR
    return (target - kit.begins + refrain.PERIOD * 0.5) % refrain.PERIOD - refrain.PERIOD * 0.5


def locked(kit, t):
    """0..1: how far a station has fallen into step with its ring."""
    start = START + ring(kit) * _RING_DELAY
    return smoother(window(t, start, start + _LOCKING))


def phase(kit, t):
    """Seconds into the current run of the procedure, or None if it has not begun. At 3:00.0
    this is exactly the refrain's phase; it slips, never backward, until the ring agrees."""
    begins = kit.begins + _shift(kit) * locked(kit, t)
    if t < begins:
        return None
    return (t - begins) % refrain.PERIOD


# ---------------------------------------------------------------- the void

#: Stations within this many metres of the lane's axis turn to it.
LANE_REACH = 46.0


def beside_lane(kit):
    return lane_distance(kit.x, kit.y) < LANE_REACH


def incompletion(t):
    """0..1: how far every procedure has stopped reaching its end."""
    return smoother(window(t, VOID, VOID + 2.5))


def held(kit, t):
    """0..1: how far a station beside the lane has left its procedure and holds, turned to the
    lane. Nearer stations first."""
    if not beside_lane(kit):
        return 0.0
    start = VOID + 0.06 * lane_distance(kit.x, kit.y)
    return smoother(window(t, start, start + 3.0))


#: Where a held station's parts stay: suspended, not reset.
_HELD_RUN = 0.8
_HELD_DROP = 0.3


def _strokes(kit, t):
    """(to_empty, to_carriage, back, run, extend, drop): the procedure's strokes, each 0..1,
    as the refrain defines them."""
    p = phase(kit, t)
    if p is None:
        return None
    s = refrain.stroke_in_procedure
    return (s(p, 0.0, 1.4), s(p, 3.75, 1.2), s(p, 6.0, 1.3),
            s(p, 1.25, 1.4) - s(p, 6.0, 1.3), s(p, 4.2, 1.0) - s(p, 5.6, 0.8), s(p, 2.5, 1.2) - s(p, 5.0, 1.0))


def carriage(kit, t):
    """(metres run, metres extended). From 3:30 a station recruited to the path round the
    lane may be doing this for the path and not for itself."""
    if t > END:
        from . import climax
        return climax.carriage(kit, t)
    return base_carriage(kit, t)


def yoke_drop(kit, t):
    if t > END:
        from . import climax
        return climax.yoke_drop(kit, t)
    return base_yoke_drop(kit, t)


def head_yaw(kit, t):
    if t > END:
        from . import climax
        return climax.head_yaw(kit, t)
    return base_head_yaw(kit, t)


def base_carriage(kit, t):
    strokes = _strokes(kit, t)
    if strokes is None:
        return 0.0, 0.0
    w, h = incompletion(t), held(kit, t)
    run = refrain.CARRIAGE_RUN * strokes[3] * (1.0 - 0.45 * w)
    extend = refrain.CARRIAGE_EXTEND * strokes[4] * (1.0 - w)
    return run + (_HELD_RUN - run) * h, extend * (1.0 - h)


def carriage_position(kit, t):
    run, extend = carriage(kit, t)
    return kit.x + kit.front * (refrain.CARRIAGE_HOME + run), kit.y + refrain.RAIL_Y, refrain.TOP + 1.0 + extend


def _base_carriage_position(kit, t):
    run, extend = base_carriage(kit, t)
    return kit.x + kit.front * (refrain.CARRIAGE_HOME + run), kit.y + refrain.RAIL_Y, refrain.TOP + 1.0 + extend


def base_yoke_drop(kit, t):
    strokes = _strokes(kit, t)
    if strokes is None:
        return 0.0
    h = held(kit, t)
    drop = refrain.YOKE_DROP * strokes[5] * (1.0 - 0.6 * incompletion(t))
    return drop + (_HELD_DROP - drop) * h


def lane_yaw(kit):
    """Degrees about +z that turn a station's head to face the nearest point of the lane."""
    hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
    along, _ = lane_coordinates(hx, hy)
    px, py = lane_point(min(max(along, 0.0), LANE_LENGTH))
    return math.degrees(math.atan2(px - hx, hy - py))


def base_head_yaw(kit, t):
    rest, to_empty = refrain.head_rest_and_working_yaw(kit)
    strokes = _strokes(kit, t)
    yaw = rest
    if strokes is not None:
        hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
        cx, cy, _ = _base_carriage_position(kit, t)
        to_carriage = math.degrees(math.atan2(cx - hx, hy - cy))
        a, b, c = strokes[0], strokes[1], strokes[2]
        yaw = rest + (to_empty - rest) * a + (to_carriage - to_empty) * b + (rest - to_carriage) * c
    h = held(kit, t)
    if h <= 0.0:
        return yaw
    turn = (lane_yaw(kit) - yaw + 180.0) % 360.0 - 180.0        # the short way round
    return yaw + turn * h


# ---------------------------------------------------------------- large structures

_CELLS_INDEX = 0.45         # metres the array of cells goes down, and comes back
_MAIN_RISE = 0.8            # metres the length of heavy main rises, and settles
#: Whatever lies in the lane goes down by its own height and this much more, so that the
#: ground closes over it and no stub is left.
_CLEARED_BELOW = 0.06
#: The lane is cleared in bands this many metres long, ahead of the camera.
_BAND = 5.0
#: Seconds one band takes to go down.
_CLEARING = 1.2


def _stroke(t, start, seconds=1.6):
    return smoother(window(t, start, start + seconds))


def _in_array(piece):
    """The array of holding cells the heavy main runs through."""
    x0, x1, y0, y1 = hinge.region_bounds(0)
    return piece.kind == "cell" and x0 < piece.center[0] < x1 and y0 < piece.center[1] < y1


def _risen_main(piece):
    """The length of heavy main between the trunk the camera leaves and the lane."""
    return (piece.kind == "main" and abs(piece.center[1] - hinge.row_y(hinge.BUS_MAIN_ROW)) < 0.01
            and 45.0 < piece.center[0] < 172.0)


@lru_cache(maxsize=None)
def intrusion(piece):
    """Where a piece of routing first comes inside the lane: metres along it, or None if no
    part of its footprint is within the lane's width. Stations, their bays and their spurs
    never are: that is how the lane was found."""
    if piece.kind in ("unit", "bay", "spur"):
        return None
    first = None
    for i in range(9):
        for j in range(9):
            x = piece.center[0] + piece.size[0] * (i / 8.0 - 0.5)
            y = piece.center[1] + piece.size[1] * (j / 8.0 - 0.5)
            along, across = lane_coordinates(x, y)
            if 0.0 <= along <= LANE_LENGTH and abs(across) < LANE_HALF_WIDTH:
                first = along if first is None else min(first, along)
    return first


def _across_lane(piece):
    return intrusion(piece) is not None


def clearing_time(piece):
    """When a piece in the lane starts to go down: band by band along the lane, on the beat,
    always ahead of the camera. The first two bands go at 3:20.0; the next three a beat apart;
    after that a beat and a half apart, so the last is still going down at 3:30."""
    band = int(intrusion(piece) // _BAND)
    quick = max(0, min(band, 4) - 1)
    slow = max(0, band - 4)
    return VOID + timeline.BEAT * (quick + 1.5 * slow)


def moves(piece):
    """Whether a piece of the level takes part at all."""
    return _in_array(piece) or _risen_main(piece) or _across_lane(piece)


def piece_offset(piece, t):
    """Metres a piece of the level is displaced at time t. Zero at and before 3:00.0."""
    if t <= START:
        return 0.0, 0.0, 0.0
    t = min(t, END)
    z = 0.0
    if _in_array(piece):
        z -= _CELLS_INDEX * (_stroke(t, RESPONSE) - _stroke(t, RELEASE))
    if _risen_main(piece):
        z += _MAIN_RISE * (_stroke(t, RESPONSE + timeline.BAR * 0.5) - _stroke(t, RELEASE + timeline.BAR * 0.5))
    if _across_lane(piece):
        z -= (piece.size[2] + _CLEARED_BELOW) * _stroke(t, clearing_time(piece), _CLEARING)
    return 0.0, 0.0, z


# ---------------------------------------------------------------- the frames beside the lane

#: How many of the nearest stations on each side turn their overhead frames, and by how much:
#: a part of the 35 degrees that would square a frame to the lane, all in the same sense.
_FLANKING_EACH_SIDE = 4
GANTRY_TURN = 12.0
#: Metres ahead of the camera, along the lane, at which a station's frame begins to turn.
_GANTRY_LEAD = 20.0


@lru_cache(maxsize=None)
def flanking():
    """The stations nearest the lane, a few on each side: {station index: when its frame
    begins to turn}. Each begins on a beat, as the camera comes within reach of it."""
    from . import refrain as r
    sides = {1: [], -1: []}
    for kit in r.kits() + r.later_kits():
        along, across = lane_coordinates(kit.x, kit.y)
        # Bordering it: beside its length (or just off either end), and near.
        if -8.0 < along < LANE_LENGTH + 6.0 and abs(across) < 40.0:
            sides[1 if across > 0 else -1].append((abs(across), kit.station, along))
    chosen = sorted((along, station) for side in sides.values() for _, station, along in sorted(side)[:_FLANKING_EACH_SIDE])
    result = {}
    for order, (along, station) in enumerate(chosen):
        # While it is still ahead of the camera, and never two at once: half a beat apart at least.
        t = VOID
        while t < END and lane_coordinates(*camera_position(t)[:2])[0] < along - _GANTRY_LEAD:
            t += timeline.BEAT * 0.5
        result[station] = max(t, VOID + timeline.BEAT * (1.0 + 0.5 * order))
    return result


def gantry_yaw(kit, t):
    """Degrees about +z that a station's overhead frame (posts, beam and yoke together) is
    turned. Zero except for the few stations nearest the lane, after 3:20."""
    begins = flanking().get(kit.station)
    if begins is None or t <= VOID:
        return 0.0
    return -GANTRY_TURN * _stroke(min(t, END), begins)


def arrival(t):
    """0..1: stations built out only for this passage coming out of the dark. They were plain
    units until 3:00.0, as the locked film shows them."""
    return smoother(window(t, START, START + 6.0))
