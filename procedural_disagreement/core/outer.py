"""The film's outer frame: what the system is before the case and after it.

OPENING, 0:00-0:35. The system exists before the case. Pieces of the apparatus acknowledge
themselves one at a time, in the dark; a body turns out to be standing among them; on the bass
entry the system couples; on the last hit before the film proper it is ready.

ENDING, 4:25-4:40. The system persists after the case. The same grammar, with nobody there:
the apparatus is intact, uncoupled, and still arranged around the place the body stood.

Everything here is a function of absolute track time and is exactly neutral inside the locked
film (0:35 to the start of the ending): strokes are at rest, the clock is the track's own, the
coupling and the light are exactly 1. Nothing here knows about render profiles or Blender.
"""

from functools import lru_cache

from . import layout, timeline
from .ease import smoother, window

OPENING_END = timeline.SECTION_START

#: The ending is a target: nothing between the end of the developed film and here is authored.
ENDING_START = timeline.cue("ending_start")
ENDING_END = timeline.cue("ending_end")

# The opening's hits: the heavy low transients of the first twenty seconds (they come every
# bar, a little after two seconds in), the bass entry, and the hit that closes the phrase.
OPENING_HEAD = timeline.cue("opening_head")
OPENING_CARRIAGE = timeline.cue("opening_carriage")
OPENING_TRAY = timeline.cue("opening_tray")
OPENING_PANEL = timeline.cue("opening_panel")
OPENING_BODY = timeline.cue("opening_body")
OPENING_SHOULDER = timeline.cue("opening_shoulder")
OPENING_COUPLE_START = timeline.cue("opening_couple_start")
OPENING_COUPLE = timeline.cue("opening_couple")
OPENING_SEAT = timeline.cue("opening_seat")
OPENING_READY = timeline.cue("opening_ready")

# The ending's hits: three of the coda's isolated transients, further and further apart.
ENDING_HEAD = timeline.cue("ending_head")
ENDING_CARRIAGE = timeline.cue("ending_carriage")
ENDING_CONFIRM = timeline.cue("ending_confirm")
#: From here the track is silent, and nothing in the picture moves.
ENDING_SILENCE = timeline.cue("ending_silence")


def in_opening(t):
    return t < OPENING_END


def in_ending(t):
    return t >= ENDING_START


# The coda, 4:15-4:25: the room again, straight after the widest view of the network, with
# nobody in it. It is seen from the outer frame and ends in exactly the ending's first state.
CODA_START = timeline.cue("climax_end")
#: The second statement of the refrain begins: what the first set out is withdrawn.
CODA_AGAIN = timeline.cue("coda_again")
#: The last withdrawal begins.
CODA_WITHDRAW = timeline.cue("coda_withdraw")
#: The last sung word ends. Everything is as the ending finds it.
CODA_SILENT = timeline.cue("coda_silent")


def in_coda(t):
    """After the frame at 4:15.0, which belongs to the network, and before 4:25.0."""
    return CODA_START < t < ENDING_START


def after_the_case(t):
    """The room with nobody in it: the coda and the ending."""
    return t > CODA_START


def stroke(t, start, seconds):
    """One eased move from rest to rest: 0 before ``start``, 1 after ``start + seconds``."""
    return smoother(window(t, start, start + seconds))


# ---------------------------------------------------------------- the subject

#: The empty coordinate the ending is arranged around: the shoulder the arm was removed from.
#: It is the point the tower head faced in the opening, when there was a shoulder there, and
#: again when it re-indexed the amputated body.
EMPTY_COORDINATE = layout.arm_origin(1)


def subject_presence(t):
    """1 while there is a body on the plinth, 0 once it has gone.

    REQUIRED STATE AT 4:25.0: the body is absent. How it leaves is not authored; until it is,
    this is a step at the start of the ending."""
    # It is not removed on screen. It was there when the film left this room at 1:36; on the
    # other side of the cut at 4:15 it is not.
    return 0.0 if after_the_case(t) else 1.0


def alternates_presence(t):
    """Factor on every translucent reality. None of them outlasts the case."""
    return 0.0 if after_the_case(t) else 1.0


# ---------------------------------------------------------------- coupling

#: Seconds the system takes to run up to speed once it has coupled.
_RUN_UP = 4.0


def coupling(t):
    """0..1: how far the system is running as one thing. Exactly 1 inside the film.

    Before the bass entry nothing circulates: conduits carry nothing, rotors stand, cells are
    dark. On the entry it couples and runs up evenly. REQUIRED STATE AT 4:25.0: uncoupled
    again (0); how it winds down is not authored."""
    if in_ending(t):
        return 0.0
    if in_coda(t):
        # What is left of it, running for nobody; it dies with the second statement.
        return _CODA_COUPLING * (1.0 - smoother(window(t, CODA_AGAIN, CODA_AGAIN + _CODA_RUN_DOWN)))
    return window(t, OPENING_COUPLE, OPENING_COUPLE + _RUN_UP)


#: How far the system is still running when the coda finds it, and seconds it takes to stop.
_CODA_COUPLING = 0.5
_CODA_RUN_DOWN = 3.0


def clock(t):
    """The time that cyclic motion runs on: the closed-form integral of ``coupling``.

    Inside the film it is exactly ``t``, so everything periodic is exactly where the locked
    film has it. Before coupling it stands still; during the run-up it advances at a speed
    that rises evenly to 1; in the ending it stands still again."""
    full = OPENING_COUPLE + _RUN_UP
    if t >= ENDING_START:
        return ENDING_START
    if in_coda(t):
        # It runs down to exactly where the ending holds it: the ending's value, less whatever
        # coupling is still to come. (The room was not in the picture before the cut, so where
        # it starts from is not seen to differ.)
        u = window(t, CODA_AGAIN, CODA_AGAIN + _CODA_RUN_DOWN)
        still_to_fall = 0.5 - (u ** 6 - 3.0 * u ** 5 + 2.5 * u ** 4)        # integral of 1 - smoother, from u to 1
        return ENDING_START - _CODA_COUPLING * (max(0.0, CODA_AGAIN - t) + _CODA_RUN_DOWN * still_to_fall)
    if t >= full:
        return t
    x = window(t, OPENING_COUPLE, full)
    return full - _RUN_UP * 0.5 * (1.0 - x * x)


# ---------------------------------------------------------------- strokes of the apparatus

#: Degrees the tower head stands turned aside before it is addressed, and metres above its seat.
HEAD_PARKED_YAW = 52.0
HEAD_PARKED_LIFT = 0.25
_HEAD_STROKE = 1.5


def opening_head(t):
    """(toward_body, seated), each 0..1, for the head of the tower on the body's right.

    On its hit it turns from where it was parked to face the place the body's shoulder is,
    which is still dark. Later it turns to its working heading and lowers onto its seat."""
    return stroke(t, OPENING_HEAD, _HEAD_STROKE), stroke(t, OPENING_SEAT, _HEAD_STROKE)


def ending_head(t):
    """0..1: the same head turning from the carriage it was last checked against to face the
    empty coordinate."""
    return stroke(t, ENDING_HEAD, _HEAD_STROKE)


#: Metres short of its station the carriage waits before it is addressed.
CARRIAGE_SHORT = 0.6


def opening_carriage(t):
    """Metres the carriage still has to run along the wall rail to reach its station."""
    return CARRIAGE_SHORT * (1.0 - stroke(t, OPENING_CARRIAGE, 1.5))


def ending_carriage(t):
    """(run, extend), each 0..1: the carriage runs to the body's line again and extends."""
    return stroke(t, ENDING_CARRIAGE, 1.6), stroke(t, ENDING_CARRIAGE + 1.2, 1.3)


#: Where the tray waits, relative to its place beside the plinth.
TRAY_SHORT = (0.8, 0.0, 0.0)


def opening_tray(t):
    """Fraction of ``TRAY_SHORT`` the tray still has to travel."""
    return 1.0 - stroke(t, OPENING_TRAY, 1.4)


#: Metres along the wall the rear panel stands out of its place before it settles.
PANEL_SHORT = 0.5


def opening_panel(t):
    """Metres the rear panel still has to slide along the wall to reach its place."""
    return PANEL_SHORT * (1.0 - stroke(t, OPENING_PANEL, 1.3))


#: Degrees the conduit ends stand open, away from the shoulders, before the system couples.
CONDUIT_OPEN = 24.0


def conduit_open(t):
    """Degrees the last run of each conduit is still swung away from the shoulder. They close
    on the bass entry: the stroke ends on the hit."""
    return CONDUIT_OPEN * (1.0 - stroke(t, OPENING_COUPLE_START, OPENING_COUPLE - OPENING_COUPLE_START))


#: Metres the overhead lamp hangs above the risers before it docks on them. It docks twice:
#: over the body, when the system is ready, and over nothing, as the last thing that happens.
LAMP_RAISED = 0.4
LAMP_RAISED_ENDING = 0.2


def lamp_height(t):
    """Metres the overhead lamp is above its docked position.

    REQUIRED STATE AT 4:25.0: undocked, ``LAMP_RAISED_ENDING`` above the risers."""
    if in_ending(t):
        return LAMP_RAISED_ENDING * (1.0 - stroke(t, ENDING_CONFIRM, 0.5))
    if in_coda(t):
        # It has been docked on the risers since 0:30. As the last withdrawal begins it lets go
        # of them: there is nothing under it to be ready for.
        return LAMP_RAISED_ENDING * stroke(t, CODA_WITHDRAW, _CODA_LAMP)
    return LAMP_RAISED * (1.0 - stroke(t, OPENING_READY, 0.9))


#: Seconds the lamp takes to undock in the coda.
_CODA_LAMP = 1.4

#: When the last stroke of the film ends.
LAST_MOTION = ENDING_CONFIRM + 0.5


# ---------------------------------------------------------------- light
#
# The preview has no lamps to switch, so light is a factor on each object's colour: 0 is unlit,
# 1 is the film's ordinary appearance. It is exactly 1 inside the film. A lit engine can use
# the same curves for real lamps; that is the final-render layer and is not built.

#: Level of the whole room once the system has coupled, and in the ending.
_ROOM_COUPLED = 0.30
_ROOM_ENDING = 0.26
#: Level of the whole room when the coda finds it.
_ROOM_CODA = 0.55


@lru_cache(maxsize=None)
def room_light(t):
    """0..1: light on everything, wherever it is."""
    if in_ending(t):
        return _ROOM_ENDING
    if in_coda(t):
        # Lit enough to read what is on its surfaces; through the second statement it goes down
        # to the level the ending holds.
        return _ROOM_CODA + (_ROOM_ENDING - _ROOM_CODA) * stroke(t, CODA_AGAIN, CODA_SILENT - CODA_AGAIN)
    if t >= OPENING_READY + 1.5:
        return 1.0
    coupled = _ROOM_COUPLED * stroke(t, OPENING_COUPLE, 2.5)
    return coupled + (1.0 - _ROOM_COUPLED) * stroke(t, OPENING_READY, 1.5)


@lru_cache(maxsize=None)
def zones():
    """Local pools of light: (name, centre, radius). Each comes on with one hit."""
    tower = layout.tower_position(1)
    cabinet = layout.cabinet(timeline.SEED, *layout.REINDEX_CABINET)
    panel = layout.back_panel_center(*layout.ATTRACTOR_PANEL)
    shoulder = EMPTY_COORDINATE
    return (
        ("head", (tower[0], tower[1], layout.TOWER_HEAD_HEIGHT + 0.3), 1.7),
        ("carriage", (layout.CABINET_X, cabinet[0], 0.9), 1.7),
        ("tray", (layout.RECEIVER_POSITION[0] + 0.3, layout.RECEIVER_POSITION[1], 1.0), 1.5),
        ("panel", (panel[0], panel[1], panel[2]), 1.7),
        ("plinth", (0.0, 0.0, 1.0), 2.4),
        ("shoulder", (shoulder[0] * 0.5, shoulder[1], shoulder[2] + 0.1), 1.9),
        ("lamp", (0.0, 0.0, layout.LAMP_UNDERSIDE), 1.5),
    )


@lru_cache(maxsize=None)
def zone_levels(t):
    """How far each pool of light is on, in the order of ``zones``."""
    if in_ending(t):
        # They return in the order the apparatus responds: head, carriage, then the lamp over
        # the empty plinth. Nothing lights the tray (it is gone), the panel or the shoulder.
        head = stroke(t, ENDING_HEAD, 0.4)
        carriage = stroke(t, ENDING_CARRIAGE, 0.4)
        last = stroke(t, ENDING_CONFIRM, 0.4)
        return (head, carriage, 0.0, 0.0, last, 0.0, last)
    if in_coda(t):
        # No pool is lit: nothing in the room is being attended to.
        return (0.0,) * 7
    on = [stroke(t, cue, 0.35) for cue in (OPENING_HEAD, OPENING_CARRIAGE, OPENING_TRAY, OPENING_PANEL,
                                           OPENING_BODY, OPENING_SHOULDER)]
    return tuple(on) + (stroke(t, OPENING_READY, 0.35),)


def zone_weights(point):
    """How strongly each pool of light reaches a point: 1 inside 55% of its radius, falling
    smoothly to 0 at its edge."""
    weights = []
    for _, centre, radius in zones():
        d = sum((a - b) ** 2 for a, b in zip(point, centre)) ** 0.5
        weights.append(1.0 - smoother(window(d, 0.55 * radius, radius)))
    return tuple(weights)


def light(weights, t):
    """0..1: light on something whose ``zone_weights`` are given. Exactly 1.0 inside the film."""
    level = room_light(t)
    if level >= 1.0:
        return 1.0
    for weight, on in zip(weights, zone_levels(t)):
        if weight > 0.0:
            level = max(level, weight * on)
    return min(1.0, level)

