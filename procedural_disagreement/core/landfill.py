"""The disposal field below the chamber, as data and functions. No Blender.

Three things live here, all profile-blind and all functions of position or time alone:

* the terrain: one continuous surface of compacted waste, with ridges, flat benches, steep
  faces between them, basins, and a berm under every chute;
* the stations: where the other chutes hang, all the way out to the dark;
* the disposals: other body parts coming down other chutes while the camera flies over.

The scene layer draws these. The camera's flight and the forearm's fall are in choreography.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

from . import choreography as ch
from . import layout, stablehash, timeline, variants
from .ease import clamp01, smooth
from .vec import Q_IDENTITY, lerp, q_axis_angle, q_mul

_SEED = timeline.SEED + 31000
_GRAVITY = 9.81

#: Height of one compacted layer, in metres: the rise of each bench.
BENCH = 1.7
#: Spacing of the station grid, and how far each station may stray from it.
_STATION_STEP = 24.0
_STATION_JITTER = 8.5


# ---------------------------------------------------------------- where things are


@lru_cache(maxsize=None)
def frame():
    """Fixed points of the field, derived from where the lyric's forearm lands.

    Returns a dict: ``crest`` (centre and height of the platform it lands on), ``shelf`` (the
    lower platform, for the primary's arm), ``floor`` (z of the pit floor), ``centre`` (of the
    pit), ``start`` (where the flyover begins), ``heading`` and ``right`` (unit vectors of the
    flight and of screen-right while flying)."""
    landing = ch.discard_landing(variants.alternate())
    landing_arm = ch.discard_landing(variants.primary())
    crest = (landing[0] - 0.37, landing[1], landing[2] - 0.10)        # the forearm rests lying toward -x
    shelf = (landing_arm[0] + 0.64, landing_arm[1], landing_arm[2] - 0.12)
    heading = ch.flyover_heading()
    return {
        "crest": crest,
        "shelf": shelf,
        "floor": crest[2] - layout.LANDFILL_HEAP_HEIGHT,
        "centre": (crest[0] + layout.LANDFILL_CENTRE_OFFSET[0], crest[1] + layout.LANDFILL_CENTRE_OFFSET[1]),
        "start": ch.lower_camera_pose(timeline.LANDFILL_FLYOVER)[0],
        "heading": heading,
        "right": (heading[1], -heading[0], 0.0),
    }


def flight_coordinates(x, y):
    """(along, across) of a point relative to the flyover: metres ahead of where the flight
    starts, and metres to the right of its line."""
    f = frame()
    dx, dy = x - f["start"][0], y - f["start"][1]
    return dx * f["heading"][0] + dy * f["heading"][1], dx * f["right"][0] + dy * f["right"][1]


def from_flight(along, across):
    """World (x, y) of a point given in flight coordinates."""
    f = frame()
    return (f["start"][0] + f["heading"][0] * along + f["right"][0] * across,
            f["start"][1] + f["heading"][1] * along + f["right"][1] * across)


def distance_to_flight(x, y):
    along, across = flight_coordinates(x, y)
    return abs(across) if along > -10.0 else math.hypot(along, across)


@lru_cache(maxsize=None)
def _flight_profile():
    """(metres flown, camera z) through the flyover, for keeping the ground clear of the camera."""
    samples, t = [], timeline.LANDFILL_FLYOVER
    while t <= timeline.TIMELINE_END + 4.0:
        samples.append((ch.flyover_distance(t), frame()["start"][2] + ch.flyover_height(t)))
        t += 0.25
    return tuple(samples)


def _camera_height_at(along):
    samples = _flight_profile()
    if along <= samples[0][0]:
        return samples[0][1]
    for (d0, z0), (d1, z1) in zip(samples, samples[1:]):
        if along <= d1:
            return lerp(z0, z1, (along - d0) / max(1e-9, d1 - d0))
    return samples[-1][1]


# ---------------------------------------------------------------- stations


@dataclass(frozen=True)
class Station:
    x: float
    y: float
    #: Height of the berm of waste under the chute, above the surrounding terrain.
    berm: float
    #: z of the chute's mouth.
    bottom: float
    scale: float
    heading: float
    #: 0..1: how brightly the mouth is lit.
    glow: float


@lru_cache(maxsize=None)
def stations():
    """Every other station in the field: a jittered grid out to the edge. Some plots are empty.
    None stands on our own heap, in the camera's way, or where a disposal is staged."""
    f = frame()
    half = layout.LANDFILL_SPAN * 0.5 - 12.0
    n = int(2.0 * half / _STATION_STEP)
    reserved = [(f["crest"][0], f["crest"][1], 19.0)] + [(x, y, 13.0) for x, y in _staged_sites()]
    result = []
    for i in range(n):
        for j in range(n):
            s = _SEED + i * 977 + j * 131
            x = f["centre"][0] - half + (i + 0.5) * _STATION_STEP + stablehash.uniform(s, 0, -_STATION_JITTER, _STATION_JITTER)
            y = f["centre"][1] - half + (j + 0.5) * _STATION_STEP + stablehash.uniform(s, 1, -_STATION_JITTER, _STATION_JITTER)
            if stablehash.value(s, 2) < 0.14:
                continue
            if any(math.hypot(x - rx, y - ry) < r for rx, ry, r in reserved):
                continue
            along, across = flight_coordinates(x, y)
            # Over the flight line the chutes are short, so the camera passes under them.
            deepest = -3.5 if (abs(across) < 12.0 and along > -12.0) else -12.0
            result.append(Station(
                x, y,
                berm=stablehash.uniform(s, 3, 1.6, 4.6),
                bottom=stablehash.uniform(s, 4, deepest, -1.5),
                scale=stablehash.uniform(s, 5, 0.7, 1.5),
                heading=stablehash.uniform(s, 6, 0.0, 180.0),
                glow=stablehash.uniform(s, 7, 0.25, 1.0),
            ))
    return tuple(result)


@lru_cache(maxsize=None)
def _station_cells():
    """Stations bucketed on a coarse grid, so the terrain can find the ones near a point."""
    cells = {}
    for station in stations():
        cells.setdefault((int(station.x // 16.0), int(station.y // 16.0)), []).append(station)
    return cells


# ---------------------------------------------------------------- terrain


def _lattice(seed, ix, iy):
    return stablehash.value(seed + ix * 7919, iy)


def _noise(x, y, seed):
    """Smooth value noise in [0, 1]."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = smooth(x - ix), smooth(y - iy)
    a, b = _lattice(seed, ix, iy), _lattice(seed, ix + 1, iy)
    c, d = _lattice(seed, ix, iy + 1), _lattice(seed, ix + 1, iy + 1)
    return lerp(lerp(a, b, fx), lerp(c, d, fx), fy)


def raw_height(x, y):
    """Metres of waste above the pit floor, before it is compacted and before any clearances."""
    # Broad drifts, and long ridges running across them at an angle.
    drift = _noise(x / 41.0, y / 41.0, _SEED + 1)
    u, v = x * 0.819 + y * 0.574, -x * 0.574 + y * 0.819
    ridge = 1.0 - abs(2.0 * _noise(u / 19.0, v / 63.0, _SEED + 2) - 1.0)
    grain = _noise(x / 13.0, y / 13.0, _SEED + 3)
    h = 14.0 * (0.5 * drift + 0.32 * ridge + 0.18 * grain) ** 1.3 - 3.9      # basins where this goes negative
    # A berm under every chute.
    cx, cy = int(x // 16.0), int(y // 16.0)
    cells = _station_cells()
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            for station in cells.get((cx + ox, cy + oy), ()):
                d2 = (x - station.x) ** 2 + (y - station.y) ** 2
                if d2 < 196.0:
                    h += station.berm * math.exp(-d2 / 30.0)
    return max(0.0, h)


def _compact(h):
    """Pressed into layers: flat benches a BENCH apart, with steep faces between them."""
    level = math.floor(h / BENCH)
    within = h / BENCH - level
    benched = (level + smooth(clamp01((within - 0.34) / 0.3))) * BENCH
    return lerp(h, benched, 0.82)


def height(x, y):
    """Metres of waste above the pit floor at (x, y): the surface everything rests on."""
    f = frame()
    h = _compact(raw_height(x, y))
    floor = f["floor"]

    # Nothing rises into the camera along its flight.
    along, across = flight_coordinates(x, y)
    if -6.0 < along and abs(across) < 11.0:
        clearance = _camera_height_at(along) - 3.4 - floor + max(0.0, abs(across) - 5.0) * 1.2
        h = min(h, clearance)

    # Our own heap: a flat top exactly under the platform the forearm lands on, falling away
    # on all sides, and low enough around it that the landing is never hidden.
    top = f["crest"][2] - 0.2 - floor
    r = math.hypot(x - f["crest"][0], y - f["crest"][1])
    if r < 9.5:
        slope = top - max(0.0, r - 2.3) * 0.85
        h = min(h, slope) if r > 2.3 else top
        h = max(h, slope - 1.6) if r < 6.5 else h
    # The lower platform, where the primary's arm lands, must stand clear.
    shelf = f["shelf"]
    if math.hypot(x - shelf[0], y - shelf[1]) < 2.1:
        h = min(h, shelf[2] - 0.3 - floor)
    # Nor where the camera waits during the fall.
    wait = layout.LOWER_CAMERA_END
    if math.hypot(x - wait[0], y - wait[1]) < 4.2:
        h = min(h, wait[2] - 2.6 - floor)

    # Where a disposal is staged the ground is a basin, so the fall is long and the landing open.
    for ex, ey in _staged_sites():
        d = math.hypot(x - ex, y - ey)
        if d < 7.0:
            h = min(h, 1.2 + max(0.0, d - 3.5) * 1.1)
    return max(0.0, h)


def surface(x, y):
    """World z of the waste surface at (x, y)."""
    return frame()["floor"] + height(x, y)


def steepness(x, y):
    """(drop in metres over two metres of ground, unit downhill direction) at (x, y)."""
    gx = height(x + 1.0, y) - height(x - 1.0, y)
    gy = height(x, y + 1.0) - height(x, y - 1.0)
    size = math.hypot(gx, gy)
    if size < 1e-9:
        return 0.0, (1.0, 0.0)
    return size, (-gx / size, -gy / size)


# ---------------------------------------------------------------- disposals elsewhere


@dataclass(frozen=True)
class DisposalEvent:
    """Another station disposing of something while the camera flies. Nothing is random about
    it: where, when and what are all given."""
    name: str
    #: "arm", "leg" or "torso".
    kind: str
    #: Track time at which the object leaves the chute.
    release: float
    x: float
    y: float
    #: z of the chute's mouth.
    bottom: float
    #: Whether it falls broadside to the camera, turning in the plane of the picture.
    broadside: bool = False


@dataclass(frozen=True)
class StagedSite:
    """A chute placed by hand, over a basin dug for it. The terrain and the stations are
    shaped around these, so they never move."""
    #: Position in flight coordinates: metres ahead of the flight's start, metres to its right.
    along: float
    across: float
    #: z of the chute's mouth.
    bottom: float

    @property
    def x(self):
        return from_flight(self.along, self.across)[0]

    @property
    def y(self):
        return from_flight(self.along, self.across)[1]


def staged_sites():
    """Each in front of the camera at a different distance: near and readable, far, mid, and
    one in the widest view. The third stands idle: its disposal moved to a nearer station."""
    return (
        StagedSite(25.0, 6.0, -19.5),
        StagedSite(94.0, -28.0, -11.0),
        StagedSite(87.0, 22.0, -9.0),
        StagedSite(92.0, -12.0, -8.0),
    )


@lru_cache(maxsize=None)
def _staged_sites():
    return tuple((site.x, site.y) for site in staged_sites())


#: The ordinary station, in flight coordinates, that disposes of an arm on the second sung
#: "landfill". Chosen because it is already in the picture then, about 30 m from the camera.
_SECOND_LANDFILL_STATION = (73.7, 15.8)


def station_near(along, across):
    """The station standing at these flight coordinates. There must be one within a metre."""
    x, y = from_flight(along, across)
    station = min(stations(), key=lambda s: math.hypot(s.x - x, s.y - y))
    if math.hypot(station.x - x, station.y - y) > 1.0:
        raise ValueError("no station stands at flight coordinates (%.1f, %.1f)" % (along, across))
    return station


@lru_cache(maxsize=None)
def events():
    sites = staged_sites()
    other = station_near(*_SECOND_LANDFILL_STATION)

    def at(cue, kind, x, y, bottom, broadside=False):
        return DisposalEvent(cue, kind, timeline.cue(cue), x, y, bottom, broadside)

    return (
        at("landfill_disposal_1", "torso", sites[0].x, sites[0].y, sites[0].bottom),
        at("landfill_disposal_2", "leg", sites[1].x, sites[1].y, sites[1].bottom),
        # Under the second sung "-fill": another arm, from another station, going where ours went.
        at("landfill_disposal_3", "arm", other.x, other.y, other.bottom, broadside=True),
        at("landfill_disposal_4", "arm", sites[3].x, sites[3].y, sites[3].bottom),
    )


#: Metres per second an object is moving as it leaves a chute: the speed of the tray above it.
_EXIT_SPEED = 3.0
#: How long each kind is, tip to tip, in metres. Used to keep it clear of the ground at rest.
EVENT_LENGTH = {"arm": 1.45, "leg": 1.7, "torso": 0.85}


def event_rest_height(event):
    """World z at which the object comes to rest."""
    return surface(event.x, event.y) + 0.12


def event_fall_time(event):
    """Seconds from leaving the chute to reaching the waste."""
    drop = event.bottom - event_rest_height(event)
    return (-_EXIT_SPEED + math.sqrt(_EXIT_SPEED ** 2 + 2.0 * _GRAVITY * drop)) / _GRAVITY


def event_impact_time(event):
    return event.release + event_fall_time(event)


@lru_cache(maxsize=None)
def _sight_line(event):
    """Unit horizontal direction from the camera to the event, halfway through its fall. The
    camera's path does not depend on any event, so this is a fact about where it already is."""
    camera = ch.lower_camera_pose(event.release + 0.5 * event_fall_time(event))[0]
    dx, dy = event.x - camera[0], event.y - camera[1]
    size = math.hypot(dx, dy)
    return dx / size, dy / size


def event_pose(event, t):
    """(position, rotation, visible) of a disposed object at time t.

    Before its release it is out of sight above the mouth of its chute. Then it falls under
    gravity, turning at an even rate, lands, slides a hand's width and stays."""
    tau = t - event.release
    if tau <= 0.0:
        return (event.x, event.y, event.bottom + 0.5), Q_IDENTITY, False
    fall = event_fall_time(event)
    airborne = min(tau, fall)
    z = event.bottom - _EXIT_SPEED * airborne - 0.5 * _GRAVITY * airborne * airborne
    s = stablehash.value(_SEED + 500, int(event.release * 100.0))
    axis = (math.cos(s * 6.283), math.sin(s * 6.283), 0.0)
    heading = 360.0 * s
    if event.broadside:
        # It turns about the line of sight, so its length stays across the picture all the way down.
        sight = _sight_line(event)
        axis = (sight[0], sight[1], 0.0)
        heading = math.degrees(math.atan2(sight[1], sight[0])) + 90.0
    turn = (70.0 + 80.0 * s) * airborne / fall
    position = (event.x, event.y, z)
    if tau > fall:
        settle = 1.0 - (1.0 - clamp01((tau - fall) / 0.3)) ** 3
        position = (event.x + axis[1] * 0.12 * settle, event.y - axis[0] * 0.12 * settle, event_rest_height(event))
        # It ends lying flat, whatever angle it arrived at.
        turn = lerp(turn, 180.0 if turn > 90.0 else 0.0, settle)
    return position, q_mul(q_axis_angle(axis, turn), q_axis_angle((0.0, 0.0, 1.0), heading)), True


def shade(x, y):
    """0..1: how much of its tone something at (x, y) keeps. The field darkens with distance
    from the flight until it cannot be told from the dark around it, long before any wall."""
    along, across = flight_coordinates(x, y)
    # Distance from the stretch of the flight line the camera actually covers.
    ahead = max(0.0, along - 95.0)
    behind = max(0.0, -along - 5.0)
    d = math.hypot(abs(across), ahead * 0.55 + behind * 1.4)
    return max(0.0, min(1.0, 1.08 - d / 140.0))
