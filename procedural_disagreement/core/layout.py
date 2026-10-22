"""Where things are.

World units are metres, Z up. The camera approaches along +Y; the figure stands at the origin
facing -Y. Everything here is profile-independent: it fixes the composition.
"""

from dataclasses import dataclass

from .vec import Z, add, mul, q_align_z, q_rotate

# ---------------------------------------------------------------- chamber

CHAMBER_HALF_WIDTH = 7.0
CHAMBER_HEIGHT = 7.0
CHAMBER_Y_MIN = -17.0
CHAMBER_Y_MAX = 11.0
PLINTH_HEIGHT = 0.5
#: Underside of the overhead lamp; the figure's risers end here.
LAMP_UNDERSIDE = 6.03

# ---------------------------------------------------------------- camera

CAMERA_START = (0.5, -15.5, 2.9)
CAMERA_END = (-1.3, -6.2, 2.65)
#: Opens on the whole figure...
CAMERA_TARGET_START = (0.0, 0.0, 2.5)
#: ...and settles on the arm that is being argued over.
CAMERA_TARGET_END = (0.8, -0.4, 3.0)
#: On the emphasis cue the aim turns a few degrees into the room, toward the system that branches.
CAMERA_TARGET_SYSTEM = (2.2, 1.0, 3.1)
#: After the approach, the aim settles on the empty volume the removed forearm used to occupy.
CAMERA_TARGET_PHANTOM = (1.45, -0.55, 2.80)
#: The disposal passage is watched from further back and higher, looking down the floor
#: channel: the room gets larger and the route becomes visible.
CAMERA_DISPOSAL_POSITION = (-2.6, -8.5, 4.2)
CAMERA_DISPOSAL_TARGET = (2.2, 2.0, 1.6)
CAMERA_FOV_START = 36.0
#: The outer frame: where the film's first image and its last are seen from. The plinth and
#: the lamp over it are on the left; the tower and the wall carriage are to the right.
OUTER_CAMERA_POSITION = (-2.2, -10.5, 2.5)
OUTER_CAMERA_TARGET = (1.2, 0.5, 3.0)
OUTER_CAMERA_FOV = 36.0
CAMERA_FOV_END = 33.0

# ---------------------------------------------------------------- figure

#: The figure is authored at roughly human size ("figure units") and scaled up to be monumental.
FIGURE_SCALE = 1.7


def fig(p):
    """Figure units, origin at the feet -> world metres."""
    return (p[0] * FIGURE_SCALE, p[1] * FIGURE_SCALE, p[2] * FIGURE_SCALE + PLINTH_HEIGHT)


@dataclass(frozen=True)
class Module:
    """One module of a limb: a box slice or a ball joint. Figure units."""

    ball: bool
    #: Extent along the limb.
    length: float
    width: float
    depth: float
    offset: tuple = (0.0, 0.0, 0.0)


def _slice(length, width, depth, offset=(0.0, 0.0, 0.0)):
    return Module(False, length, width, depth, offset)


def _ball(length, diameter):
    return Module(True, length, diameter, diameter)


#: Gap between consecutive modules, figure units.
MODULE_GAP = 0.006

# Module order matters: ProcedureVariant.cut_index refers to positions in these tuples.
ARM_MODULES = (
    _ball(0.10, 0.13),              # 0  shoulder
    _slice(0.07, 0.105, 0.115),     # 1  upper arm
    _slice(0.07, 0.105, 0.115),     # 2
    _slice(0.07, 0.105, 0.115),     # 3
    _slice(0.07, 0.105, 0.115),     # 4
    _ball(0.08, 0.10),              # 5  elbow
    _slice(0.06, 0.09, 0.095),      # 6  forearm
    _slice(0.06, 0.09, 0.095),      # 7
    _slice(0.06, 0.09, 0.095),      # 8
    _slice(0.06, 0.09, 0.095),      # 9
    _slice(0.10, 0.05, 0.10),       # 10 hand
)

LEG_MODULES = (
    _ball(0.08, 0.14),              # 0  hip
    _slice(0.12, 0.15, 0.16),       # 1  thigh
    _slice(0.12, 0.15, 0.16),       # 2
    _slice(0.12, 0.15, 0.16),       # 3
    _ball(0.08, 0.12),              # 4  knee
    _slice(0.11, 0.12, 0.13),       # 5  shin
    _slice(0.11, 0.12, 0.13),       # 6
    _slice(0.11, 0.12, 0.13),       # 7
    _ball(0.04, 0.09),              # 8  ankle
    _slice(0.05, 0.13, 0.26, (0.0, -0.05, 0.0)),  # 9  foot
)

TORSO_SLAB_WIDTHS = (0.34, 0.37, 0.41, 0.46, 0.50)


def module_tops(modules):
    """Distance from the limb's origin to the start of each module, figure units."""
    tops, cursor = [], 0.0
    for module in modules:
        tops.append(cursor)
        cursor += module.length + MODULE_GAP
    return tops


def boundary_distance(modules, index):
    """Metres along the limb from its origin to the boundary where module ``index`` begins."""
    return (module_tops(modules)[index] - MODULE_GAP * 0.5) * FIGURE_SCALE


def arm_origin(side):
    return fig((side * 0.31, 0.0, 1.60))


def arm_rotation(side):
    """Modules stack along the limb's local -Z. The arms are held forward, outward and a little
    down, presented for the procedure, which turns any cut across them to face the camera."""
    return q_align_z((-side * 0.45, 0.78, 0.43), hint=Z)


def leg_origin(side):
    return fig((side * 0.13, 0.0, 1.00))


def arm_cut_point(side, cut_index):
    """Where a cut at ``cut_index`` crosses the arm's axis, in its own reality's space."""
    down = q_rotate(arm_rotation(side), mul(Z, -boundary_distance(ARM_MODULES, cut_index)))
    return add(arm_origin(side), down)


def arm_elbow_distance():
    """Metres from the shoulder to the centre of the elbow joint."""
    return (module_tops(ARM_MODULES)[5] + ARM_MODULES[5].length * 0.5) * FIGURE_SCALE


def arm_length():
    """Metres from the shoulder to the tip of the hand."""
    return (module_tops(ARM_MODULES)[-1] + ARM_MODULES[-1].length) * FIGURE_SCALE


#: Base of the torso stack: the pivot for whole-torso compensation.
TORSO_PIVOT = fig((0.0, 0.0, 1.16))


def arm_axis(side):
    """Direction pointing back up the arm: the normal of a clean cut."""
    return q_rotate(arm_rotation(side), Z)


# ---------------------------------------------------------------- dependencies


def conduit_path(side):
    """From behind the shoulder, up and over to the side wall, back along the room,
    down to the tower base."""
    return (
        (side * 0.56, 0.16, 3.12),
        (side * 0.56, 0.90, 3.12),
        (side * 0.56, 0.90, 5.20),
        (side * 6.30, 0.90, 5.20),
        (side * 6.30, 6.50, 5.20),
        (side * 6.30, 6.50, 0.90),
        (side * 5.60, 6.50, 0.90),
    )


def tower_position(side):
    return (side * 5.0, 6.5, 0.0)


def cabinet(seed, i, side):
    """(y, height, width along the wall) of the i-th cabinet on one side wall, or None where
    the bay is kept clear for the conduit drops. Seeded, and the same in every profile."""
    from . import stablehash
    index = 100 + i * 2 + (1 if side > 0 else 0)
    y = CHAMBER_Y_MIN + 2.0 + i * 3.0 + stablehash.uniform(seed, index, -0.5, 0.5)
    if abs(y - 6.5) < 1.8:
        return None
    h = stablehash.uniform(seed, index + 1000, 0.8, 1.7)
    w = stablehash.uniform(seed, index + 2000, 0.8, 1.5)
    return y, h, w


CABINET_COUNT = 9
#: Distance of the cabinets' centre line from the room's centre line.
CABINET_X = CHAMBER_HALF_WIDTH - 0.65
#: The cabinet that turns out to be a carriage on the wall rail, as (index, side): the one on
#: the right wall between the body and the failed tower.
REINDEX_CABINET = (6, 1)


#: Side-wall ribs stand every 2 m along the room.
RIB_SIZE = (0.35, 0.3, CHAMBER_HEIGHT)


def rib_ys():
    """Where the side-wall ribs actually stand along the room: every 2 m, at even y."""
    ys, y = [], CHAMBER_Y_MIN + 1.0
    while y < CHAMBER_Y_MAX:
        ys.append(y)
        y += 2.0
    return ys


def rib_position(side, y):
    return (side * (CHAMBER_HALF_WIDTH - 0.175), y, CHAMBER_HEIGHT * 0.5)


#: The system branch hinges about the vertical riser the conduit climbs behind the shoulder,
#: so the two interpretations share the figure and disagree about everything beyond it.
SYSTEM_BRANCH_SIDE = 1
SYSTEM_BRANCH_PIVOT = (0.56, 0.90, 0.0)
#: Ribs that belong to the branch. They stand at odd y, in the gaps between the chamber's own
#: ribs (which are at even y), so they emerge at 1:00 as ribs the primary room does not have.
#: Approved as rendered.
SYSTEM_BRANCH_RIBS_Y = (3.0, 5.0, 7.0, 9.0)

#: The solid wall rib the body recruits as a distal segment of its missing limb. It belongs to
#: the chamber, and its movement at 1:30 is the first time any solid rib moves in the film.
#:
#: History: earlier events (phantom load at 1:06.25, absent attractor at 1:25) were once written
#: to lean solid ribs too, but were configured at odd y, where no rib stands (see rib_ys), and
#: so never produced any motion. The footage was approved as rendered and that is canonical.
#: Those responses have been removed rather than activated.
RECRUITED_RIB_SIDE = 1
RECRUITED_RIB_Y = 4.0
#: One panel of the far back wall, as (row, column): top row, clear of the figure in the upper left of frame.
ATTRACTOR_PANEL = (2, 2)


def back_panel_center(row, col):
    """Centre of a back-wall panel on the wall plane (its relief depth is seeded separately)."""
    return (-5.2 + col * 2.6, CHAMBER_Y_MAX, 1.25 + row * 2.25)


#: Where the shoulder articulates when the socket takes part: a point this far inboard of the
#: shoulder ball (toward the neck) and slightly above it, in metres, for the +x arm.
SHOULDER_SOCKET_OFFSET = (-0.10, 0.0, 0.02)

TOWER_CELLS = 6
TOWER_ROTOR_HEIGHT = 2.9
TOWER_HEAD_HEIGHT = 3.7

#: Tray that collects the removed arm in the primary reality.
RECEIVER_POSITION = (2.15, -0.6, 0.0)

# ---------------------------------------------------------------- disposal

#: The floor channel on the +x side: a dark strip the length of the room. It turns out to be a track.
FLOOR_CHANNEL_X = 2.4
FLOOR_CHANNEL_WIDTH = 0.12
#: How the receiver travels: sideways onto the channel, then along it away from the figure.
DISPOSAL_ROUTE = (FLOOR_CHANNEL_X - RECEIVER_POSITION[0], 3.6, 0.0)
#: How far it then goes down. Enough to take the tray and everything on it under the floor.
DISPOSAL_DROP = 2.2
#: Highest point of what the receiver carries (the top of the arm lying on the tray), in metres.
DISPOSAL_LOAD_TOP = 1.56
#: Where the alternate's removed forearm is set down: world position of its cut end, on the
#: tray beside the primary's arm, lying along +x like it.
DISPOSAL_FOREARM_POSITION = (1.90, -0.40, 1.43)
#: The aperture the channel opens into where the receiver stops: (width across, length along).
DISPOSAL_APERTURE = (2.4, 1.3)

# ---------------------------------------------------------------- landfill

#: Bottom of the chute that hangs under the aperture, below the chamber floor.
LANDFILL_CHUTE_BOTTOM = -1.9
#: The heap under our chute: radius of its flat crest, and its height above the pit floor.
LANDFILL_CREST_RADIUS = 1.7
LANDFILL_HEAP_HEIGHT = 7.0
#: The pit is square, this many metres on a side: nearly five hundred times the chamber's
#: floor area. Its walls are never seen: the field darkens to nothing well short of them.
LANDFILL_SPAN = 440.0
#: Where the pit's centre lies relative to our heap. Our station is not in the middle of it:
#: the field runs on much further in the direction the camera flies.
LANDFILL_CENTRE_OFFSET = (40.0, 48.0)
#: The camera below. It starts under the pit ceiling, far enough back to take in the pit,
#: looking up at the chute; it goes down with the fall and closes in, ending a few metres
#: from the crest of the heap.
LOWER_CAMERA_START = (-6.5, -5.0, -5.5)
LOWER_CAMERA_END = (-1.8, -1.2, -21.4)
LOWER_CAMERA_FOV = 50.0

# ---------------------------------------------------------------- cutting planes

PLANE_SIZE = 1.0
