"""Timing, in absolute track time.

``t`` everywhere in this project is seconds from the start of the music. Frame ``n`` shows
``t = n / FPS``, so frame numbers, file names and audio offsets all agree for any interval
of the finished video. Nothing here may depend on a render profile.

Event times are not written here: they are read from the directorial cue file in ``cues/``,
which is edited by hand. This module only gives them names.
"""

import json
import os

FPS = 30

#: Root seed for every seeded variation.
SEED = 4401

CUE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "cues", "poc_0035_0105.json")

with open(CUE_FILE, encoding="utf-8") as _handle:
    _DATA = json.load(_handle)


def cue(name):
    """Track time of a named directorial cue."""
    try:
        return float(_DATA["cues"][name]["t"])
    except KeyError:
        raise KeyError("Cue %r is missing from %s" % (name, CUE_FILE)) from None


#: The section this proof of concept covers.
SECTION_START = float(_DATA["section"]["start"])
SECTION_END = float(_DATA["section"]["end"])
#: How far the choreography currently extends. The approach above stays defined on the section.
TIMELINE_END = float(_DATA["timeline_end"])

# Musical grid. Used only to lock cyclic motion to the pulse of the track.
BPM = float(_DATA["tempo"]["bpm"])
BEAT = 60.0 / BPM
BAR = 4.0 * BEAT
#: A known downbeat; phases of cyclic motion are measured from it.
DOWNBEAT = float(_DATA["tempo"]["downbeat"])

# Camera.
CAMERA_AIM_START = cue("camera_aim_start")
CAMERA_AIM_END = cue("camera_aim_end")
CAMERA_EMPHASIS = cue("camera_emphasis")

# The disagreement spreads from the body into the surrounding system.
SYSTEM_DIVERGENCE = cue("system_divergence")

# The body acts on a limb it no longer has.
PHANTOM_LOAD = cue("phantom_load")

# The system measures and accepts its new state: one bar each.
REINDEX_FIRST = cue("reindex_first")
REINDEX_SECOND = cue("reindex_second")
REINDEX_CROSSCHECK = cue("reindex_crosscheck")
REINDEX_ACCEPT = cue("reindex_accept")

# The room begins to organise itself around the place where the limb is not.
ABSENT_ATTRACTOR = cue("absent_attractor")

# The body begins to treat a piece of the chamber as part of its missing limb.
PROSTHETIC_RECRUITMENT = cue("prosthetic_recruitment")

# The removed parts are processed as waste.
DISPOSAL_HANDLING = cue("disposal_handling")
DISPOSAL_TRANSPORT = cue("disposal_transport")
LANDFILL = cue("landfill")
DISPOSAL_SEALED = cue("disposal_sealed")
#: The cut to the space below, and the moment the forearm lands in it.
LANDFILL_CUT = cue("landfill_cut")
LANDFILL_IMPACT = cue("landfill_impact")
#: The flight over the landfill: it starts, it starts to climb, it reaches its widest view.
LANDFILL_FLYOVER = cue("landfill_flyover")
LANDFILL_FLYOVER_CLIMB = cue("landfill_flyover_climb")
LANDFILL_FLYOVER_WIDE = cue("landfill_flyover_wide")

# Cutting plane A: the cut the primary reality performs.
PLANE_A_ENTER = cue("plane_a_enter")
PLANE_A_ARRIVE = cue("plane_a_arrive")
PLANE_A_RETREAT_START = cue("plane_a_retreat_start")
PLANE_A_RETREAT_END = cue("plane_a_retreat_end")

# Cutting plane B: the cut the first alternate reality performs.
PLANE_B_ENTER = cue("plane_b_enter")
PLANE_B_ARRIVE = cue("plane_b_arrive")
PLANE_B_RETREAT_START = cue("plane_b_retreat_start")
PLANE_B_RETREAT_END = cue("plane_b_retreat_end")

# The planes contest each other's position and the alternate realities split off.
DISAGREEMENT_START = cue("disagreement_start")
DIVERGENCE_END = cue("divergence_end")

# The procedure, in each of its two main versions.
PRIMARY_CUT = cue("primary_cut")
PRIMARY_INFRASTRUCTURE_FAILURE = cue("primary_infrastructure_failure")
PRIMARY_REGION_AT_REST = cue("primary_region_at_rest")
ALTERNATE_CUT = cue("alternate_cut")
ALTERNATE_INFRASTRUCTURE_FAILURE = cue("alternate_infrastructure_failure")
ALTERNATE_REGION_AT_REST = cue("alternate_region_at_rest")


def frame_of(t):
    return int(round(t * FPS))


def time_of(frame):
    return frame / FPS


def parse_time(text):
    """Seconds from ``"72.5"``, ``"1:12.5"`` or ``"0:01:12.5"``."""
    seconds = 0.0
    for part in str(text).strip().split(":"):
        seconds = seconds * 60.0 + float(part)
    return seconds


def format_time(t):
    minutes = int(t // 60)
    return "%d:%05.2f" % (minutes, t - minutes * 60)
