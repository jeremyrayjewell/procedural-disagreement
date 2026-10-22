"""The filtered refrain, 2:20-3:00: the system without a subject, seen from inside.

The hinge left one trunk and one station in darkness. From 2:20 the camera travels along that
trunk at the height of the stations. The level turns out to be made of working stations: each
has an empty platform, an overhead yoke over it, a head on a column and a carriage on a rail.
Nobody is on any platform.

Two conditions inhabit the surfaces, as the refrain names them: scrawls (irregular, wandering,
unreadable marks) and medal bars (short ranked rectangular plates). They are conditions of
the place, not events: nothing here is cued to a repetition of the lyric.

At 2:20 the level couples, as the chamber did at 0:20, but around no one. From 2:40 the
stations run their procedure, one after another, around empty coordinates.

Everything is a function of position and absolute time, is profile-blind, and is exactly the
hinge's own state at 2:20.0. What is where is described here; the scene layer draws it.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

from . import hinge, landfill, stablehash, timeline
from .ease import smoother, window
from .vec import Q_IDENTITY, q_axis_angle, q_camera_look, q_mul, sub, v_lerp

START = hinge.END
#: The stations begin to run their procedure.
PROCEDURE = timeline.cue("refrain_procedure")
#: A target boundary: nothing after it is authored.
END = timeline.cue("refrain_end")

_SEED = timeline.SEED + 61000
#: z of the top of every station unit.
TOP = hinge.GROUND + 2.6


def _ramp_integral(t, start, end):
    """Integral from -infinity to t of a smoothstep rising over [start, end]."""
    u = window(t, start, end)
    return (end - start) * (u * u * u - 0.5 * u * u * u * u) + max(0.0, t - end)


# ---------------------------------------------------------------- camera

#: Metres per second along the trunk: the first, observing speed, and what is added to it.
_GLIDE = 2.0
_GLIDE_MORE = 1.6
#: Metres it moves sideways, to pass between two stations instead of over one.
_SIDESTEP = 5.8
#: Height above the ground of the level: at the start, by the procedure cue, and at the end.
_HEIGHTS = (2.6, 5.75, 7.75)


def camera_travel(t):
    """Metres travelled along the trunk since 2:20. It starts from rest."""
    t = min(t, END)
    return _GLIDE * _ramp_integral(t, START, START + 6.0) + _GLIDE_MORE * _ramp_integral(t, PROCEDURE, PROCEDURE + 6.0)


def camera_position(t):
    if t > END:
        from . import network
        return network.camera_position(t)
    start = hinge.still_camera_position()
    travel = camera_travel(t)
    y = start[1] + travel
    x = start[0] + _SIDESTEP * smoother(window(y, start[1] + 18.0, start[1] + 48.0))
    z = (hinge.GROUND + _HEIGHTS[0]
         + (_HEIGHTS[1] - _HEIGHTS[0]) * smoother(window(t, START + 2.0, PROCEDURE))
         + (_HEIGHTS[2] - _HEIGHTS[1]) * smoother(window(t, PROCEDURE, END)))
    return x, y, z


def _bus_y():
    """The heavy main the passage ends beside."""
    return hinge.row_y(hinge.BUS_MAIN_ROW)


def camera_pose(t):
    """The hinge camera from 2:20 on: (position, rotation, vertical field of view).

    It looks along the trunk it travels, a little toward the stations. Late on it turns toward
    the heavy main ahead, and it is still turning, and still travelling, at 3:00."""
    if t <= START:
        return hinge.still_camera()
    if t > END:
        from . import network
        return network.camera_pose(t)
    position = camera_position(t)
    start, target = hinge.still_camera_position(), hinge.still_camera_target()
    along = (target[0], target[1] + (position[1] - start[1]), target[2])
    bus = (position[0] + 80.0, _bus_y() + 1.0, hinge.GROUND + 2.0)
    turn = smoother(window(t, PROCEDURE + 6.0, END + 4.0))
    return position, q_camera_look(sub(v_lerp(along, bus, turn), position)), hinge.still_camera()[2]


# ---------------------------------------------------------------- light, as distance

#: Metres from the camera within which the level can be seen: by 2:30, by 2:40, and by 3:00.
_SIGHT = (55.0, 85.0, 135.0)
_SIGHT_EDGE = 40.0
#: Exponent of the first opening: below 1, it opens fastest at the start.
_SIGHT_OPENING = 0.75


def sight(t):
    """Metres the level can be seen from the camera. Nothing at 2:20.0: it opens outward from
    where the camera stands as the system couples, and widens again with the procedure."""
    # The first opening starts at once and slows: something is coming out of the dark from the
    # first frame after 2:20, without the whole of it arriving any sooner.
    reach = (_SIGHT[0] * window(t, START, START + 10.0) ** _SIGHT_OPENING
             + (_SIGHT[1] - _SIGHT[0]) * smoother(window(t, START + 10.0, PROCEDURE))
             + (_SIGHT[2] - _SIGHT[1]) * smoother(window(t, PROCEDURE, END)))
    if t > END:
        # From 4:00 the camera climbs, and can see further.
        from . import climax
        reach += climax.sight_more(t)
    return reach


def seen(point, t):
    """0..1: how far something at ``point`` is out of the dark at time t. Zero at and before
    2:20.0, so the hinge's last frame is untouched."""
    if t <= START:
        return 0.0
    reach = sight(t)
    camera = camera_position(t)
    distance = math.hypot(point[0] - camera[0], point[1] - camera[1])
    # While sight is still shorter than its usual soft edge, the edge is as wide as the sight:
    # what is nearest comes fully out of the dark first, not everything faintly at once.
    return 1.0 - smoother(window(distance, reach - min(_SIGHT_EDGE, reach), reach))


# ---------------------------------------------------------------- coupling, without a body

_RUN_UP = 4.0


def coupling(t):
    """0..1: the level running as one thing. It couples at 2:20, as the chamber did at 0:20."""
    return window(t, START, START + _RUN_UP)


def clock(t):
    """The time station rotors run on: the closed-form integral of ``coupling``."""
    x = window(t, START, START + _RUN_UP)
    return _RUN_UP * 0.5 * x * x + max(0.0, t - START - _RUN_UP)


#: Degrees per second: one blade past a given point on every beat, as in the chamber.
_SPIN = 60.0 / timeline.BEAT


def rotor_angle(t):
    return _SPIN * clock(t)


# ---------------------------------------------------------------- stations


@dataclass(frozen=True)
class Kit:
    """A station as it is at standing height: what stands on its unit."""
    station: int
    #: Centre of the unit's top face.
    x: float
    y: float
    #: +1 or -1: which way along x its trunk lies. Its working face is on that side.
    front: int
    #: When its procedure first starts.
    begins: float


#: Corners of the part of the level the passage moves through: stations inside it are built
#: out. Further off they remain the plain units the hinge showed.
_BUILT = (0.0, 140.0, 85.0, 225.0)
#: The station the procedure starts from, and metres the wave covers per beat.
_WAVE_ORIGIN = 131
_WAVE_PER_BEAT = 6.0


@lru_cache(maxsize=None)
def kits():
    stations = landfill.stations()
    origin = stations[_WAVE_ORIGIN]
    result = []
    for index, station in enumerate(stations):
        if not (_BUILT[0] < station.x < _BUILT[1] and _BUILT[2] < station.y < _BUILT[3]):
            continue
        front = 1 if hinge.column_x(hinge.column_of(station.x)) >= station.x else -1
        beats = round(math.hypot(station.x - origin.x, station.y - origin.y) / _WAVE_PER_BEAT)
        result.append(Kit(index, station.x, station.y, front, PROCEDURE + beats * timeline.BEAT))
    return tuple(result)


#: Stations further along, built out only once the camera turns toward them at 3:00. Until
#: then they are the plain units the locked film shows.
_BUILT_LATER = (140.0, 215.0, 138.0, 222.0)


@lru_cache(maxsize=None)
def later_kits():
    stations = landfill.stations()
    origin = stations[_WAVE_ORIGIN]
    result = []
    for index, station in enumerate(stations):
        if not (_BUILT_LATER[0] <= station.x < _BUILT_LATER[1] and _BUILT_LATER[2] < station.y < _BUILT_LATER[3]):
            continue
        front = 1 if hinge.column_x(hinge.column_of(station.x)) >= station.x else -1
        beats = round(math.hypot(station.x - origin.x, station.y - origin.y) / _WAVE_PER_BEAT)
        result.append(Kit(index, station.x, station.y, front, PROCEDURE + beats * timeline.BEAT))
    return tuple(result)


# Where things stand on a unit, relative to the centre of its top face. x is given for a
# station whose trunk lies toward +x and is mirrored for the others.
HEAD_AT = (-2.8, -2.8)
HEAD_COLUMN = 1.7
RAIL_Y = 3.3
CARRIAGE_HOME = -2.6
YOKE_HEIGHT = 3.9
#: The empty coordinate of a station: where a shoulder would be, over its platform.
EMPTY_AT = (0.3, 0.0, 2.7)

#: The procedure, in seconds from its start. It takes three bars and then begins again.
PERIOD = 3.0 * timeline.BAR
_HEAD_TURN = 86.5          # degrees: the turn the chamber's tower head made at 0:02
_CARRIAGE_RUN = 1.6
_CARRIAGE_EXTEND = 0.5
_YOKE_DROP = 0.8           # of the 0.96 m it would need to reach a shoulder: it stops short
CARRIAGE_RUN, CARRIAGE_EXTEND, YOKE_DROP = _CARRIAGE_RUN, _CARRIAGE_EXTEND, _YOKE_DROP


def empty_coordinate(kit):
    return kit.x + kit.front * EMPTY_AT[0], kit.y + EMPTY_AT[1], TOP + EMPTY_AT[2]


def _phase(kit, t):
    """Seconds into the current run of the procedure, or None if it has not begun."""
    if t < kit.begins:
        return None
    return (t - kit.begins) % PERIOD


def _stroke(phase, start, seconds):
    return smoother(window(phase, start, start + seconds))


stroke_in_procedure = _stroke


def carriage(kit, t):
    """(metres run along its rail toward the platform's line, metres extended upward)."""
    if t > END:
        from . import network
        return network.carriage(kit, t)
    phase = _phase(kit, t)
    if phase is None:
        return 0.0, 0.0
    run = _stroke(phase, 1.25, 1.4) - _stroke(phase, 6.0, 1.3)
    extend = _stroke(phase, 4.2, 1.0) - _stroke(phase, 5.6, 0.8)
    return _CARRIAGE_RUN * run, _CARRIAGE_EXTEND * extend


def carriage_position(kit, t):
    """Centre of the carriage's top, in the world."""
    run, extend = carriage(kit, t)
    return kit.x + kit.front * (CARRIAGE_HOME + run), kit.y + RAIL_Y, TOP + 1.0 + extend


def head_yaw(kit, t):
    """Degrees about +z of the station's head, which faces along its local -y.

    At rest it stands turned aside. In the procedure it turns to the empty coordinate, then
    to the carriage, then back."""
    if t > END:
        from . import network
        return network.head_yaw(kit, t)
    hx, hy = kit.x + kit.front * HEAD_AT[0], kit.y + HEAD_AT[1]

    def toward(point):
        return math.degrees(math.atan2(point[0] - hx, hy - point[1]))

    to_empty = toward(empty_coordinate(kit))
    rest = to_empty - kit.front * _HEAD_TURN
    phase = _phase(kit, t)
    if phase is None:
        return rest
    to_carriage = toward(carriage_position(kit, t))
    a, b, c = _stroke(phase, 0.0, 1.4), _stroke(phase, 3.75, 1.2), _stroke(phase, 6.0, 1.3)
    return rest + (to_empty - rest) * a + (to_carriage - to_empty) * b + (rest - to_carriage) * c


def head_rest_and_working_yaw(kit):
    """(degrees at rest, degrees facing its own empty coordinate) for a station's head."""
    hx, hy = kit.x + kit.front * HEAD_AT[0], kit.y + HEAD_AT[1]
    empty = empty_coordinate(kit)
    to_empty = math.degrees(math.atan2(empty[0] - hx, hy - empty[1]))
    return to_empty - kit.front * _HEAD_TURN, to_empty


def yoke_drop(kit, t):
    """Metres the overhead yoke has come down toward the platform."""
    if t > END:
        from . import network
        return network.yoke_drop(kit, t)
    phase = _phase(kit, t)
    if phase is None:
        return 0.0
    return _YOKE_DROP * (_stroke(phase, 2.5, 1.2) - _stroke(phase, 5.0, 1.0))


# ---------------------------------------------------------------- conditions: scrawls and bars


@dataclass(frozen=True)
class Mark:
    """One small box of a surface condition."""
    #: "apron" (a dark plate marks lie on), "scrawl" or "bar".
    kind: str
    center: tuple
    size: tuple
    rotation: tuple


#: Strokes moved by hand because, as seeded, their plate could be read as a picture: a
#: (plate, stroke) gets (metres across, metres along, degrees) added to where and how it starts.
#: Nothing else about any scrawl is changed.
_UNPICTURED = {(0, 1): (-1.1, 3.4, 30.0), (0, 2): (1.0, -0.6, -55.0), (6, 1): (1.2, 0.6, -70.0), (6, 3): (-0.9, 4.2, -50.0),
               (3, 0): (0.9, 1.6, 35.0), (3, 2): (-0.6, 3.0, -30.0)}

#: Fractions of built-out stations whose working face carries each condition. Some carry both.
_BARRED = 0.62
_SCRAWLED = 0.55
#: The station the hinge left lit carries neither: its face is part of the 2:20 image.
_BARE = _WAVE_ORIGIN


def _wander(seed, start, heading, steps, step, limits):
    """A crooked line: points of a walk that keeps turning a little and stays inside limits."""
    points, (u, v) = [start], start
    for k in range(steps):
        heading += stablehash.uniform(seed, 10 + k, -48.0, 48.0)
        length = step * stablehash.uniform(seed, 40 + k, 0.55, 1.25)
        u2 = u + math.cos(math.radians(heading)) * length
        v2 = v + math.sin(math.radians(heading)) * length
        if not (limits[0] < u2 < limits[1]):
            heading = 180.0 - heading
            u2 = u + math.cos(math.radians(heading)) * length
        if not (limits[2] < v2 < limits[3]):
            heading = -heading
            v2 = v + math.sin(math.radians(heading)) * length
        u, v = u2, v2
        points.append((u, v))
    return points


@lru_cache(maxsize=None)
def marks():
    """Every mark, in a fixed order. Seeded; the same in every profile."""
    result = []

    # ---- on the working faces of stations: bars high on the face, scrawl below them
    for kit in kits():
        _station_marks(kit, result)
    _ground_marks(result)
    return tuple(result)


@lru_cache(maxsize=None)
def later_marks():
    """The same conditions on the stations built out after 3:00."""
    result = []
    for kit in later_kits():
        _station_marks(kit, result)
    return tuple(result)


def _station_marks(kit, result):
    if True:
        if kit.station == _BARE:
            return
        s = _SEED + kit.station * 131
        face_x = kit.x + kit.front * 4.0
        proud = kit.front * 0.03
        if stablehash.value(s, 0) < _BARRED:
            # Ranked: rows of equal plates, each row shorter than the one above, squared up at one end.
            count = 4 + int(stablehash.value(s, 2) * 2)
            left = kit.y - 3.3 + stablehash.uniform(s, 3, 0.0, 1.0)
            for row in range(3):
                for k in range(count):
                    result.append(Mark("bar", (face_x + proud, left + 0.45 + k * 1.08, TOP - 0.45 - row * 0.42),
                                       (0.06, 0.9, 0.26), Q_IDENTITY))
                count = max(1, count - 1 - int(stablehash.value(s, 5 + row) * 2))
            # And the same ranking laid flat along the front edge of the top, where it is seen
            # from above: three rows, the longest nearest the edge.
            count = 5 + int(stablehash.value(s, 8) * 2)
            left = kit.y - 3.4 + stablehash.uniform(s, 9, 0.0, 0.8)
            for row in range(3):
                for k in range(count):
                    result.append(Mark("bar", (kit.x + kit.front * (3.55 - row * 0.45), left + 0.4 + k * 0.98, TOP + 0.025),
                                       (0.3, 0.8, 0.05), Q_IDENTITY))
                count = max(1, count - 1 - int(stablehash.value(s, 12 + row) * 2))
        if stablehash.value(s, 20) < _SCRAWLED:
            for stroke in range(3):
                ss = s + 1000 + stroke * 53
                start = (stablehash.uniform(ss, 0, -3.0, 3.0), stablehash.uniform(ss, 1, 0.35, 0.85))
                points = _wander(ss, start, stablehash.uniform(ss, 2, -30.0, 30.0), 7, 0.7, (-3.6, 3.6, 0.2, 1.0))
                for (u0, v0), (u1, v1) in zip(points, points[1:]):
                    length = math.hypot(u1 - u0, v1 - v0)
                    angle = math.degrees(math.atan2(v1 - v0, u1 - u0))
                    result.append(Mark("scrawl", (face_x + proud, kit.y + (u0 + u1) * 0.5, hinge.GROUND + (v0 + v1) * 0.5),
                                       (0.05, length + 0.06, 0.1), q_axis_angle((1.0, 0.0, 0.0), angle)))



def _ground_marks(result):
    # ---- on the ground beside the trunk the camera travels: dark aprons, scrawled on
    camera, trunk_x = hinge.still_camera_position(), hinge.column_x(hinge.axis_column())
    side = 1.0 if camera[0] > trunk_x else -1.0
    mains = [hinge.row_y(j) for j in hinge.main_rows()]
    for k in range(7):
        s = _SEED + 90000 + k * 97
        y = camera[1] + 9.0 + k * 13.5 + stablehash.uniform(s, 0, -2.0, 2.0)
        if min(abs(y - m) for m in mains) < 8.5:
            continue
        cx = trunk_x + side * 3.4
        result.append(Mark("apron", (cx, y, hinge.GROUND + 0.03), (4.2, 9.5, 0.06), Q_IDENTITY))
        for stroke in range(4):
            ss = s + 500 + stroke * 61
            start = (stablehash.uniform(ss, 0, -1.4, 1.4), stablehash.uniform(ss, 1, -4.0, 0.0))
            heading = 90.0 + stablehash.uniform(ss, 2, -35.0, 35.0)
            if (k, stroke) in _UNPICTURED:
                dx, dy, turn = _UNPICTURED[(k, stroke)]
                start, heading = (start[0] + dx, start[1] + dy), heading + turn
            points = _wander(ss, start, heading, 8, 0.85, (-1.8, 1.8, -4.4, 4.4))
            for (u0, v0), (u1, v1) in zip(points, points[1:]):
                length = math.hypot(u1 - u0, v1 - v0)
                angle = math.degrees(math.atan2(v1 - v0, u1 - u0))
                result.append(Mark("scrawl", (cx + (u0 + u1) * 0.5, y + (v0 + v1) * 0.5, hinge.GROUND + 0.085),
                                   (length + 0.08, 0.14, 0.05), q_axis_angle((0.0, 0.0, 1.0), angle)))


#: Linear RGB of the conditions and of the station machinery.
APRON = (0.055, 0.058, 0.06)
#: The ground of the level (the pit ceiling's own tone), and the height below which a mark lies on it.
GROUND_TONE = (0.010, 0.011, 0.013)
GROUND_MARKS_BELOW = hinge.GROUND + 0.15
SCRAWL = (0.21, 0.215, 0.22)
BAR = (0.40, 0.41, 0.42)
MACHINE = (0.16, 0.17, 0.18)
MACHINE_LIGHT = (0.30, 0.31, 0.32)
PLATFORM = (0.24, 0.25, 0.25)
