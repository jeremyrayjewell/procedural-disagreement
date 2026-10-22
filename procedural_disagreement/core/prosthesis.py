"""Network-scale prosthetic compensation, 3:30-4:00.

At 3:20 the network turned to a lane in which nothing stands. At 3:30 the lane ends. From the
bass return the network does not fill it and does not mend it. It learns to route function
around it.

There is a path around the lane's end that uses only what survives: along the north bank,
round the two stations that close the lane, and back along the south bank. Station by station
along that path, a station stops running the whole procedure for itself and takes one part of
it for the path: one turns its head to the next station (a donor), the next runs its carriage
(a carrier), the next brings its yoke fully down (a receiver), and so on. What each used to do
whole, three now do between them, in sequence, round the absence.

Station 237 is first. It already faces the lane; it keeps that, and takes a second relation:
its head goes back and forth between the lane and station 224. Station 224 has no machinery.
It takes part as a block: it indexes along its trunk and becomes the corner of the path.

Nothing here adds an object, draws a connection or touches the lane. Everything is a function
of position and absolute time and is exactly the network's own state at 3:30.0.
"""

import math
from functools import lru_cache

from . import hinge, landfill, network, refrain, timeline
from .ease import smoother, window
from .vec import q_camera_look

START = network.END
#: The first heavy bass hit after the return. Station 237 takes its second relation.
SEED = timeline.cue("prosthesis_seed")
#: Station 224 indexes along its trunk.
RELAY = timeline.cue("prosthesis_relay")
#: The path begins to recruit along both banks.
DETOUR = timeline.cue("prosthesis_detour")
#: Recruitment quickens and routing itself takes a part.
WIDEN = timeline.cue("prosthesis_widen")
#: A target boundary: nothing after it is authored.
END = timeline.cue("prosthesis_end")

DONOR, CARRIER, RECEIVER = "donor", "carrier", "receiver"
#: The three parts are three different kinds of movement. A donor's head assembly reaches this
#: far sideways along the platform's edge as it turns; a receiver's yoke comes this far down;
#: a carrier's carriage runs this far along its rail. They are amounts
#: in the world, the same for every station however far it is from the camera.
DONOR_REACH = 1.2
RECEIVER_DROP = 1.8
#: Metres along its rail a carrier's carriage runs to: further than the 1.6 m any station's own
#: procedure took it. Its extension is the procedure's own 0.5 m.
CARRIER_RUN = 2.4

#: The station that has no machinery and takes part as a block.
RELAY_STATION = 224

#: The path, in the order function passes along it: the north bank eastward, round the lane's
#: end, the south bank westward. Each entry is (station, role, when it is recruited). Roles
#: repeat donor, carrier, receiver along the path, with station 237 a donor.
#:
#: The times are set by what the camera can see. Each station is recruited, on the beat grid,
#: while it is in the picture: 237 and the block first; then the camera looks back across the
#: lane's end and the north bank takes its parts, outward from 237; then, as the camera comes
#: round, the south bank, outward from the block. Between those there are holds: nothing is
#: handed on while nobody could see it.
PATH = (
    (195, RECEIVER, 222.5),
    (210, DONOR, 221.25),
    (225, CARRIER, None),           # on the DETOUR cue
    (238, RECEIVER, 216.875),
    (237, DONOR, None),             # the seed: recruited on the SEED cue
    (209, CARRIER, 226.25),
    (194, RECEIVER, None),          # on the WIDEN cue
    (177, DONOR, 236.25),
    (178, CARRIER, 237.5),
)
#: The path's two ends, 195 and 178, are the stations either side of the lane's mouth: it goes
#: all the way round. Three stations beside the path are recruited with one on it, at the same
#: moment, and act with it as one composite station: (station, the one it joins).
PARTNERS = ((193, 194), (211, 210), (176, 177))
_SEED_STATION = 237
#: Seconds between one station on the path and the next taking its turn: two beats.
_STEP = 2.0 * timeline.BEAT
_RECRUITING = 1.5


@lru_cache(maxsize=None)
def recruits():
    """{station: (role, when recruited, place on the path)}."""
    result = {}
    for place, (station, role, when) in enumerate(PATH):
        if when is None:
            when = {237: SEED, 225: DETOUR, 194: WIDEN}[station]
        result[station] = (role, when, place)
    for station, joins in PARTNERS:
        result[station] = result[joins]
    return result


def recruited(station, t):
    """Whether a station has taken its part in the path: 1.0 from the moment it does."""
    entry = recruits().get(station)
    return 1.0 if entry is not None and t >= entry[1] else 0.0


def turn(station, t):
    """Seconds into a station's current turn on the path, or None before it has been
    recruited. Its first turn starts the moment it is recruited, so its part is seen at once;
    a turn comes round every three bars, like the procedure it replaces."""
    when = recruits()[station][1]
    if t < when:
        return None
    return (t - when) % refrain.PERIOD


def _act(q):
    """0..1: one part's stroke within a turn: out, held, and back. Nothing before recruitment."""
    if q is None:
        return 0.0
    return smoother(window(q, 0.0, 1.4)) - smoother(window(q, 3.0, 4.3))


def next_on_path(station):
    """The station a donor turns its head to: the next along the path. For 237 that is the
    block, 224, which stands between it and the next station with machinery."""
    if station == _SEED_STATION:
        return RELAY_STATION
    for partner, joins in PARTNERS:
        if station == partner:
            return next_on_path(joins)
    place = recruits()[station][2]
    return PATH[min(place + 1, len(PATH) - 1)][0]


def _kit(station):
    for kit in refrain.kits() + refrain.later_kits():
        if kit.station == station:
            return kit
    raise KeyError(station)


# ---------------------------------------------------------------- stations


def head_yaw(kit, t):
    base = network.base_head_yaw(kit, t)
    entry = recruits().get(kit.station)
    if entry is None or entry[0] != DONOR:
        return base
    # It keeps the relation it had (to the lane, or to its own platform) and takes a second:
    # its head goes to the next station on the path and comes back, every turn.
    target = landfill.stations()[next_on_path(kit.station)]
    hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
    to_next = math.degrees(math.atan2(target.x - hx, hy - target.y))
    swing = (to_next - base + 180.0) % 360.0 - 180.0
    return base + swing * _act(turn(kit.station, t))


def carriage(kit, t):
    run, extend = network.base_carriage(kit, t)
    entry = recruits().get(kit.station)
    if entry is None or entry[0] != CARRIER:
        return run, extend
    # From wherever it was left, the whole run and the whole extension, and back to where it
    # was left: completeness comes back, but only for this part.
    act = _act(turn(kit.station, t))
    return run + (CARRIER_RUN - run) * act, extend + (refrain.CARRIAGE_EXTEND - extend) * act


def yoke_drop(kit, t):
    drop = network.base_yoke_drop(kit, t)
    entry = recruits().get(kit.station)
    if entry is None or entry[0] != RECEIVER:
        return drop
    # Further than any station's own procedure took it. There it stopped short of a shoulder;
    # here there is nothing to stop short of, only a function to take.
    return drop + (RECEIVER_DROP - drop) * _act(turn(kit.station, t))


def donor_reach(kit, t):
    """Metres a donor's head assembly (column, rotor and head together) has moved along its
    edge of the platform, toward the platform's middle, as its head turns to the next station:
    it does not only look that way, it leans into it. Zero for every other station."""
    entry = recruits().get(kit.station)
    if entry is None or entry[0] != DONOR:
        return 0.0
    return DONOR_REACH * _act(turn(kit.station, t))


# ---------------------------------------------------------------- the block, and routing

#: Metres station 224 indexes along its trunk early on, and again on the WIDEN cue.
RELAY_INDEX = (1.6, 1.0)
#: When its first index begins, and how long it takes.
RELAY_BEGINS = SEED + timeline.BEAT
RELAY_STROKE = 1.2
#: Metres the trunk runs beside the corner of the path rise when they take the receiver's part.
_TRUNK_RISE = 0.6
#: The trunk runs that do: (column, row). Two under and beside station 224, one beside 237.
_TRUNK_RUNS = ((14, 11), (14, 12), (15, 12))


def _stroke(t, start, seconds=1.6):
    return smoother(window(t, start, start + seconds))


def _is_relay(piece):
    return piece.station == RELAY_STATION and piece.kind in ("unit", "spur")


@lru_cache(maxsize=None)
def _trunk_run(piece):
    """Which of the recruited trunk runs a piece is: its index, or None."""
    if piece.kind != "trunk":
        return None
    for index, (column, row) in enumerate(_TRUNK_RUNS):
        if piece.column == column and abs(piece.center[1] - hinge.row_y(row)) < 0.01:
            return index
    return None


def moves(piece):
    return _is_relay(piece) or _trunk_run(piece) is not None


def piece_offset(piece, t):
    """Metres a piece of the level is displaced by the compensation. Zero at and before 3:30.0."""
    if t <= START:
        return 0.0, 0.0, 0.0
    t = min(t, END)
    if _is_relay(piece):
        # Its first index is over before the camera passes above it: it starts a beat after
        # station 237's head and is done by 3:33.1, while the block is still in the picture.
        return 0.0, RELAY_INDEX[0] * _stroke(t, RELAY_BEGINS, RELAY_STROKE) + RELAY_INDEX[1] * _stroke(t, WIDEN), 0.0
    index = _trunk_run(piece)
    if index is not None:
        # Routing takes a part that only stations had: it rises and settles as a receiver's
        # yoke comes down and goes back, on the path's own clock.
        taken = smoother(window(t, WIDEN + index * timeline.BAR * 0.5, WIDEN + index * timeline.BAR * 0.5 + _RECRUITING))
        q = (t - WIDEN - index * _STEP) % refrain.PERIOD
        return 0.0, 0.0, _TRUNK_RISE * _act(q) * taken
    return 0.0, 0.0, 0.0


# ---------------------------------------------------------------- camera

@lru_cache(maxsize=None)
def _camera_keys():
    """Out of the lane, between the two stations that close it, and round with the path: a
    turn to the right about station 224 and back west along the south bank."""
    start = network.camera_position(START)
    dt = 1.0 / 3000.0
    before = network.camera_position(START - dt)
    velocity = tuple((a - b) / dt for a, b in zip(start, before))
    g = hinge.GROUND
    return (
        (START, start, velocity),
        (START + 5.5, (188.5, 140.0, g + 9.75), (3.0, -3.4, 0.4)),
        (START + 10.0, (193.5, 125.5, g + 10.75), (-1.2, -2.9, 0.15)),
        (START + 15.0, (182.0, 116.5, g + 11.25), (-3.3, -0.5, 0.05)),
        (START + 22.5, (157.0, 121.0, g + 11.75), (-3.2, 1.2, 0.05)),
        (END, (133.0, 133.0, g + 12.0), (-2.8, 1.6, 0.0)),
    )


@lru_cache(maxsize=None)
def _look_keys():
    """Degrees clockwise from +y, and degrees below the horizon. It looks into the turn."""
    dt = 1.0 / 3000.0

    def angles(t):
        from .vec import q_rotate
        f = q_rotate(network.camera_pose(t)[1], (0.0, 0.0, -1.0))
        return math.degrees(math.atan2(f[0], f[1])), -math.degrees(math.asin(f[2]))

    yaw0, pitch0 = angles(START)
    yaw1, pitch1 = angles(START - dt)
    return (
        # The path turns right, round station 224. The gaze turns left, the other way round:
        # past 237 and 224, back across the lane's end to the north bank (3:36-3:42), on across
        # the lane to the south bank (3:45-3:55), and it meets the direction of travel again at
        # 4:00. So the camera goes round the absence and looks across it the whole way.
        ((START, yaw0, (yaw0 - yaw1) / dt), (START + 2.5, 135.0, 5.0), (START + 4.0, 112.0, -24.0),
         (START + 5.5, 70.0, -27.0), (START + 7.0, 36.0, -18.0), (START + 8.75, 14.0, -8.0),
         (START + 10.0, 6.0, -5.0), (START + 12.5, -8.0, -6.0), (START + 15.0, -25.0, -7.0),
         (START + 17.5, -40.0, -5.5), (START + 20.0, -50.0, -4.0), (START + 22.5, -60.0, -2.5),
         (START + 25.0, -64.0, 0.0), (END, -56.0, 1.0)),
        ((START, pitch0, (pitch0 - pitch1) / dt), (START + 2.5, 4.2, 0.0), (START + 8.0, 10.0, 0.0),
         (START + 15.0, 11.5, 0.0), (END, 11.5, 0.0)),
    )


def camera_position(t):
    return network.hermite(min(t, END), _camera_keys())


def camera_pose(t):
    """The hinge camera from 3:30 on: (position, rotation, vertical field of view)."""
    t = min(t, END)
    yaw_keys, pitch_keys = _look_keys()
    yaw, pitch = math.radians(network.hermite(t, yaw_keys)), math.radians(network.hermite(t, pitch_keys))
    forward = (math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), -math.sin(pitch))
    return camera_position(t), q_camera_look(forward), network.camera_pose(START)[2]
