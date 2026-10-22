"""Network emission: the level acquiring a functional state. Presentation only.

Nothing here moves, shows or hides anything, or reads or writes an object's colour. It says,
for a piece of the level and a time, how strongly a small embedded response is lit, 0..1 or a
little over. The look layer turns that into light; the preview never sees it.

3:00-3:20. The state starts at the junction of the heavy trunk and the heavy main and goes
outward along the routing, ring by ring, in the order the film's own stations fall into step.
"""

import math
from functools import lru_cache

from ..core import climax, hinge, landfill, network, prosthesis, stablehash, timeline
from ..core.ease import smoother, window

START = network.START
#: Nothing after this is designed yet: levels simply hold.
END = network.VOID

#: Metres of routing to a ring, as the film's own rings; and seconds between one ring and the next.
RING = 40.0
RING_EVERY = timeline.BAR
#: Rings that respond. Beyond the last, the level is too far to matter.
RINGS = 8
#: A response comes up in this many seconds, then settles toward ``HOLD`` of its peak.
RISE = 0.5
SETTLE = 2.0
HOLD = 0.5

#: Peak strength by kind of piece, and the fraction of such pieces that respond at all.
#: The junction is the clearest source; everything else is weaker, and most fine runs stay dark.
STRENGTH = {"junction": (1.0, 1.0), "bus": (1.0, 1.0), "via": (1.0, 1.0), "main": (0.825, 1.0), "trunk": (0.675, 1.0),
            "fine": (0.45, 0.12), "cell": (1.0, 1.0)}
#: The source: the one place the two heavy runs cross. Twice an ordinary run's peak, and the
#: strongest thing between 3:00 and 3:20.
SOURCE = 1.5
_SEED = timeline.SEED + 97000


def route_distance(x, y):
    """Metres from the junction to a point, going along the routing: it runs square to itself."""
    hx, hy = network.hub()
    return abs(x - hx) + abs(y - hy)


def ring_of(x, y):
    return int(round(route_distance(x, y) / RING))


def reached(ring):
    """When the state reaches a ring: the junction at 3:00.0, then a ring a bar."""
    return START + RING_EVERY * ring


def _is_bus(piece):
    return ((piece.kind == "trunk" and piece.column == hinge.BUS_TRUNK_COLUMN)
            or (piece.kind == "main" and abs(piece.center[1] - hinge.row_y(hinge.BUS_MAIN_ROW)) < 0.01))


@lru_cache(maxsize=None)
def part(piece, index):
    """(kind, ring, peak strength) for a piece of the level that responds, or None. Station
    bodies, bays and holding cells never do; nor does anything that lies in the lane."""
    if piece.kind not in ("trunk", "main", "via", "fine") or network.intrusion(piece) is not None:
        return None
    ring = ring_of(piece.center[0], piece.center[1])
    if ring >= RINGS:
        return None
    kind = piece.kind
    if _is_bus(piece):
        kind = "junction" if ring == 0 else "bus"
    strength, share = STRENGTH[kind]
    if stablehash.value(_SEED, index) >= share:
        return None
    return kind, ring, strength


def envelope(t, begins):
    """0..1: one response: up quickly, then settling to a low hold. It holds from 3:20."""
    if t <= begins:
        return 0.0
    t = min(t, END)
    rise = min(1.0, (t - begins) / RISE)
    rise = rise * rise * (3.0 - 2.0 * rise)
    return rise * (HOLD + (1.0 - HOLD) * math.exp(-(t - begins) / SETTLE))


# ---------------------------------------------------------------- 3:20-3:30: round the lane
#
# The bass goes and the network turns to a lane in which nothing stands. The state it acquired
# does not go on building. Everywhere it eases back a little; and beside the lane it goes out,
# band by band, just ahead of each band's clearing. Nothing is lit in the lane, at its edge or
# across it: what marks the lane is that the routing beside it has gone quiet, while the
# stations that face it keep their small lights.

#: When the passage round the lane ends. Nothing after it is designed: levels hold.
LANE_END = network.END
#: How much of its level the whole field keeps once the bass has gone, and how long it takes.
FIELD_KEPT = 0.7
FIELD_EASES = timeline.BAR
#: Metres from the lane's axis within which routing goes quiet entirely, and by which it is
#: untouched; and how much of its level the quietest routing keeps.
QUIET_WITHIN = 16.0
QUIET_BEYOND = 42.0
QUIET_KEPT = 0.08


def field(t):
    """Factor on every response: 1 until 3:20, easing to ``FIELD_KEPT`` as the bass leaves."""
    return 1.0 - (1.0 - FIELD_KEPT) * smoother(window(t, END, END + FIELD_EASES))


def lane_quiet(x, y, t):
    """0..1: how far routing at a point has gone quiet because of the lane. Nearest the lane
    most; and along it in the order the lane is cleared, a little ahead of each band."""
    if t <= END:
        return 0.0
    distance = network.lane_distance(x, y)
    if distance >= QUIET_BEYOND:
        return 0.0
    near = 1.0 - smoother(window(distance, QUIET_WITHIN, QUIET_BEYOND))
    along, _ = network.lane_coordinates(x, y)
    band = int(min(max(along, 0.0), network.LANE_LENGTH - 0.01) // 5.0)
    clears = END + timeline.BEAT * (max(0, min(band, 4) - 1) + 1.5 * max(0, band - 4))      # as network.clearing_time
    return near * smoother(window(min(t, LANE_END), clears - 0.6, clears + 1.2))


def _round_the_lane(x, y, t):
    return field(t) * (1.0 - (1.0 - QUIET_KEPT) * lane_quiet(x, y, t))


# ---------------------------------------------------------------- 3:30-4:00: the route
#
# Function is routed round the lane, station by station. Nothing new is invented for it: the
# same two marks as before, a station's cell and the inset of its junction block, now say what
# the station is doing.
#
#   The route.  When a station is recruited, the junction block where it joins its trunk comes
#               back up, and stays: the route is lit in the order the film recruits it.
#   A donor     gives: its cell flares while its head is turned to the next station.
#   A receiver  takes: its cell goes down while its yoke is down.
#   A carrier   passes it on: its junction block, in the routing, pulses while its carriage runs.
#   The block   (224) has no cell: only its junction block answers, when it indexes.
#
# Every one of these follows the film's own clock for that station (``prosthesis.turn``), so
# none of them is a new event. Nothing is lit in the lane or across it.

ROUTE_START = prosthesis.START
#: What a recruited station's junction block comes up to, as a peak; it settles like any other.
ROUTE = 1.0
#: How much a donor's cell gains at the height of its stroke, as strength; how much of its
#: light a receiver's cell loses at the depth of its stroke; and how much a carrier's junction
#: block gains during its stroke.
#: From 3:30 the whole field is in another state: every station's cell rests low, over this
#: many seconds, keeping this share of its light. A cell at full is already as bright as the
#: picture can show, so nothing could be seen to brighten from there; from rest it can. Then
#: a cell has three states: full, it gives; at rest, it is available; out, it takes.
CELL_REST = 0.12
CELL_RESTS_OVER = 1.25
#: A receiver's cell loses this much of its rest at the depth of its stroke: it goes out.
RECEIVER_DIM = 0.97
CARRIER_PULSE = 1.2
#: A station's first stroke, the one it makes as it is recruited, is its full response; every
#: later stroke is this share of it, so that what has just joined owns the picture and what
#: joined earlier goes on working behind it.
LATER_STROKES = 0.45


def _later(t, begins):
    """One response, as ``envelope``, for a response that begins after 3:20."""
    if t <= begins:
        return 0.0
    rise = min(1.0, (t - begins) / RISE)
    rise = rise * rise * (3.0 - 2.0 * rise)
    return rise * (HOLD + (1.0 - HOLD) * math.exp(-(t - begins) / SETTLE))


def acting(station, t):
    """0..1: how far into its stroke a recruited station is, on the film's own clock. Up to
    4:00 that is the route's clock; from 4:00 the climax's, which every station with machinery
    joins and which is the route's own clock until the route begins to slip onto it."""
    if t > CLIMAX_START:
        return _climax_acting(station, t)
    if t <= ROUTE_START or station not in prosthesis.recruits():
        return 0.0
    t = min(t, prosthesis.END)
    first = t - prosthesis.recruits()[station][1] < prosthesis.refrain.PERIOD
    return prosthesis._act(prosthesis.turn(station, t)) * (1.0 if first else LATER_STROKES)


def role(station, t=None):
    if t is not None and t > CLIMAX_START:
        return climax.role(station)
    entry = prosthesis.recruits().get(station)
    return entry[0] if entry else None


@lru_cache(maxsize=None)
def _junction_blocks():
    """{index of a junction block's piece: the station whose spur meets its trunk there}."""
    result = {}
    stations = landfill.stations()
    for index, piece in enumerate(hinge.pieces()):
        if piece.kind != "via":
            continue
        for number, station in enumerate(stations):
            if abs(station.y - piece.center[1]) < 0.01 and abs(hinge.column_x(hinge.column_of(station.x)) - piece.center[0]) < 0.01:
                result[index] = number
                break
    return result


def route_level(index, t):
    """What the route adds to a junction block: nothing unless its station is on the route."""
    if t > CLIMAX_START:
        return _climax_route_level(index, t)
    if t <= ROUTE_START:
        return 0.0
    station = _junction_blocks().get(index)
    if station is None:
        return 0.0
    if station == prosthesis.RELAY_STATION:
        return ROUTE * _later(t, prosthesis.RELAY_BEGINS)
    entry = prosthesis.recruits().get(station)
    if entry is None:
        return 0.0
    level = ROUTE * _later(t, entry[1])
    if entry[0] == prosthesis.CARRIER:
        level += CARRIER_PULSE * acting(station, t)
    return level


def level(piece, index, t):
    """How strongly a piece's response is lit at time t."""
    what = part(piece, index)
    if what is None:
        # Outside the 3:00 domain a piece can only ever answer the climax.
        what = climax_part(piece, index)
        if what is None or t <= CLIMAX_START:
            return 0.0
        return _climax_level(piece, what, t)
    if t <= START:
        return 0.0
    held = what[2] * envelope(t, reached(what[1])) * _round_the_lane(piece.center[0], piece.center[1], t)
    if t > CLIMAX_START:
        # The climax does not add to what was there: where it reaches, it is what is there.
        held = max(held, _climax_level(piece, what, t))
    if piece.kind == "via" and t > ROUTE_START:
        # The route re-lights its own junction blocks, wherever they stand.
        held = max(held, route_level(index, t))
    return held


def cell_rest(t):
    """0..1: how far the field's cells have gone down to rest. Nothing at or before 3:30.0."""
    return smoother(window(t, ROUTE_START, ROUTE_START + CELL_RESTS_OVER))


def cell_dim(kit, t):
    """0..1: how much of its own light a station's cell has given up at time t.

    From 3:30 every cell rests low. A donor's comes back to full while it gives; a receiver's
    goes out while it takes; a carrier's, and every other station's, stays at rest."""
    rest = (1.0 - CELL_REST) * cell_rest(t)
    kind, stroke = role(kit.station, t), acting(kit.station, t)
    if kind == prosthesis.DONOR:
        return rest * (1.0 - stroke)
    if kind == prosthesis.RECEIVER:
        return rest + (1.0 - rest) * RECEIVER_DIM * stroke
    return rest


def source_level(t):
    """The junction itself: it wakes first, at 3:00.0, and then holds like everything else."""
    if t <= START:
        return 0.0
    # The lane starts beside the junction. When it opens, the source goes quiet with the rest.
    return SOURCE * envelope(t, START) * _round_the_lane(*network.hub(), t)


def cell_level(kit, t):
    """A station's cell confirms when its own ring, the film's, is reached."""
    ring = network.ring(kit)
    if t <= START or ring >= RINGS:
        return 0.0
    # A station's cell is not routing: it stays lit beside the lane, facing it.
    return STRENGTH["cell"][0] * envelope(t, reached(ring)) * field(t)


# ---------------------------------------------------------------- 4:00-4:15: the climax
#
# Nothing new is drawn. The marks the network already has are driven by the climax's own
# authored clock instead of standing still.
#
#   Stations.  Every station with machinery keeps the 3:30 grammar, on the climax's clock:
#              full gives, rest is available, out takes, a carrier's junction block pulses.
#              Exactly the same levels as 3:30-4:00: a donor at 4:13 means what it meant at
#              3:42.9. First strokes 100%, repeats 45%.
#   Routing.   An inlay lights when the spread reaches it: the spread leaves the lane at 4:00
#              and its clock is distance from the lane, so the first marks are at the ends the
#              lane cut. Nothing is lit in the lane, and no inlay stands within ``CUT_CLEAR``
#              metres of a cut end, so nothing implies transmission across the gap.
#   Structure. When a bus or a trunk run makes its authored rise, its response is refreshed:
#              it comes back up toward the peak it already had, never above it.
#   Occupancy. From the coupling, and more from saturation, responses settle less and the
#              field keeps more of them: the crescendo is in how much is held, not how bright
#              any one mark is. From the peak to 4:15 it holds.

CLIMAX_START = climax.START
#: The settled share of a routing response, and the share of it the field keeps, at 4:00, from
#: the coupling, and at the peak. Routing only: station cells keep the 3:30 levels.
CLIMAX_HOLD = (HOLD, 0.65, 0.85)
CLIMAX_FIELD = (FIELD_KEPT, 0.85, 1.0)
#: Metres from a cut end within which no inlay is lit.
CUT_CLEAR = 2.0


def _stage(t, values):
    """A value that moves from the first to the second over the bar after the coupling, and
    from the second to the third between saturation and the peak; then it holds."""
    t = min(t, climax.END)
    first, second, third = values
    value = first + (second - first) * smoother(window(t, climax.COUPLING, climax.COUPLING + timeline.BAR))
    return value + (third - value) * smoother(window(t, climax.SATURATION, climax.PEAK)) if t > climax.SATURATION else value


def climax_hold(t):
    return _stage(t, CLIMAX_HOLD)


def climax_field(t):
    return _stage(t, CLIMAX_FIELD)


def _climax_envelope(t, begins):
    """One routing response in the climax: up in ``RISE``, then settling toward the climax's
    own hold, which rises with the stages."""
    if t <= begins:
        return 0.0
    t = min(t, climax.END)
    rise = min(1.0, (t - begins) / RISE)
    rise = rise * rise * (3.0 - 2.0 * rise)
    hold = climax_hold(t)
    return rise * (hold + (1.0 - hold) * math.exp(-(t - begins) / SETTLE))


@lru_cache(maxsize=None)
def spread_reaches(piece):
    """When the climax's spread reaches a piece: by its distance from the lane, on the beat."""
    return climax.reached(network.lane_distance(piece.center[0], piece.center[1]))


@lru_cache(maxsize=None)
def structural_stroke(piece):
    """When a piece makes an authored rise in the climax, or None. A bus rises twice."""
    what = climax.part(piece)
    if what is None or what[0] not in ("bus", "run"):
        return None
    return (what[1], climax.SATURATION) if what[0] == "bus" else (what[1],)


def _climax_level(piece, what, t):
    strength = what[2]
    if what[1] is None and piece.kind == "fine":
        # A fine run that joins at saturation: when the saturation wave reaches it.
        return strength * _climax_envelope(t, saturation_reaches(piece)) * climax_field(t)
    response = _climax_envelope(t, spread_reaches(piece))
    for begins in structural_stroke(piece) or ():
        # A refresh, not a boost: back up toward the peak this piece already has.
        response = max(response, _climax_envelope(t, begins))
    return strength * response * climax_field(t)


def _climax_acting(station, t):
    entry = climax.recruits().get(station)
    if entry is None:
        return 0.0
    t = min(t, climax.END)
    first = t - entry[1] < prosthesis.refrain.PERIOD
    return climax._act(climax.turn(station, t)) * (1.0 if first else LATER_STROKES)


def _climax_route_level(index, t):
    station = _junction_blocks().get(index)
    if station is None:
        return 0.0
    if station == prosthesis.RELAY_STATION:
        return ROUTE * _later(t, prosthesis.RELAY_BEGINS)
    relay = climax.relays().get(station)
    if relay is not None:
        return ROUTE * _later(min(t, climax.END), relay[0])
    entry = climax.recruits().get(station)
    if entry is None:
        return 0.0
    level = ROUTE * _later(min(t, climax.END), entry[1])
    if entry[0] == prosthesis.CARRIER:
        level += CARRIER_PULSE * _climax_acting(station, t)
    return level


@lru_cache(maxsize=None)
def cut_end(piece):
    """For a run that the lane cut, (axis, where along it the cut is, which side the run is
    on: +1 or -1); otherwise None. Its inlays stop ``CUT_CLEAR`` short of the cut."""
    if piece.kind not in ("trunk", "main") or network.intrusion(piece) is not None:
        return None
    order = climax.cut_order(piece)
    if order != 1:
        return None
    line = climax._line(piece)
    places = climax._cuts()[line]
    index = climax._index(piece)
    axis = 1 if piece.kind == "trunk" else 0
    half = piece.size[axis] * 0.5
    if index < min(places):
        return axis, piece.center[axis] + half, -1
    return axis, piece.center[axis] - half, 1


# The climax's own domain. From 4:00 the 3:00 rings no longer bound what can answer: every
# trunk and main within the climax's authored reach of the lane can, each when the spread
# actually reaches it, so the far field is not switched on at 4:00 but joins as the spread
# arrives. Fine runs stay as sparse as before until saturation; from then about one in three
# can answer, each when the authored saturation wave reaches it.

#: Metres from the lane within which routing can answer the climax: its structural reach.
CLIMAX_REACH = climax.RUN_REACH
#: The share of fine runs that can answer from saturation.
FINE_AT_SATURATION = 1.0 / 3.0


def _climax_kind(piece):
    if piece.kind == "via":
        return "via"
    if _is_bus(piece):
        return "bus"
    return piece.kind


@lru_cache(maxsize=None)
def climax_part(piece, index):
    """(kind, None, peak strength) for a piece outside the 3:00 domain that can answer the
    climax, or None. Its strength is its kind's own: nothing is brighter for being late."""
    if piece.kind not in ("trunk", "main", "via", "fine") or network.intrusion(piece) is not None:
        return None
    if network.lane_distance(piece.center[0], piece.center[1]) > CLIMAX_REACH:
        return None
    kind = _climax_kind(piece)
    strength, share = STRENGTH[kind]
    if kind == "fine":
        if stablehash.value(_SEED, index) >= FINE_AT_SATURATION:
            return None
    elif stablehash.value(_SEED, index) >= share:
        return None
    return kind, None, strength


@lru_cache(maxsize=None)
def saturation_reaches(piece):
    """When the authored saturation wave reaches a piece: outward from the lane, as the runs rise."""
    d = network.lane_distance(piece.center[0], piece.center[1])
    return climax.SATURATION + timeline.BEAT * 0.5 * min(round(d / 25.0), 6)


# Denser instrumentation. The marks a run already has are never moved; the climax adds more
# between them. From the coupling one more per period of the run's own spacing (about 4-7 m
# apart in all), from saturation one more again (about 2.5-4.5 m), each run's added marks
# admitted only once the authored wave has reached it: the coupling's, outward from the lane
# over three bars, and the saturation's, as the runs rise. They answer exactly as the run's own
# marks do: the same level, the same ceiling.

#: Seconds an added mark takes to come up once admitted.
DENSE_ADMIT = RISE


@lru_cache(maxsize=None)
def dense_admitted(piece):
    """(when a run's coupling marks are admitted, when its saturation marks are)."""
    d = network.lane_distance(piece.center[0], piece.center[1])
    coupling = max(spread_reaches(piece), climax.COUPLING + timeline.BEAT * round(d / (2.0 * climax.SPREAD)))
    return coupling, saturation_reaches(piece)


def dense(piece, layer, t):
    """0..1: how far a run's added marks of a layer (0 coupling, 1 saturation) are admitted."""
    if t <= CLIMAX_START or piece.kind not in ("trunk", "main") or network.intrusion(piece) is not None:
        return 0.0
    if network.lane_distance(piece.center[0], piece.center[1]) > CLIMAX_REACH:
        return 0.0
    begins = dense_admitted(piece)[layer]
    return smoother(window(min(t, climax.END), begins, begins + DENSE_ADMIT))
