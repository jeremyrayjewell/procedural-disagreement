"""Versions of the procedure.

A ``ProcedureVariant`` says where the cut falls, when, how the removed region travels and what
the dependent infrastructure does about it. One reality is built from exactly one variant;
realities disagree because their variants differ. Distances are metres.
"""

import math
from dataclasses import dataclass, replace

from . import layout, stablehash, timeline
from .vec import Q_IDENTITY, X, Y, Z, q_align_z, q_axis_angle, q_conj, q_mul

#: The alternate realities are tinted like the plane that produces them.
GHOST_TINT = (1.0, 0.34, 0.04)
#: The system branch belongs to neither plane: a pale, neutral shell.
SYSTEM_BRANCH_TINT = (0.62, 0.80, 0.92)
SYSTEM_BRANCH_OPACITY = 0.6


@dataclass(frozen=True)
class ProcedureVariant:
    name: str

    # Presentation of the reality as a whole.
    ghost: bool
    ghost_opacity: float
    tint: tuple
    #: How far this reality drifts from the primary once the disagreement starts.
    reality_offset: tuple
    #: Seconds after DISAGREEMENT_START that this reality begins to split off.
    divergence_delay: float

    # The cut.
    #: +1 or -1: which arm.
    side: int
    #: Index into the limb's module list; modules at or beyond it are removed.
    cut_index: int
    #: Tilt of the visible cutting plane away from a clean perpendicular cut.
    plane_tilt: tuple
    cut_time: float

    # Travel of the removed region.
    #: Initial separation along the limb axis.
    release_gap: float
    detach_duration: float
    detach_travel: tuple
    #: Final rotation of the removed region, in limb space.
    detach_rotation: tuple

    # Consequences for the dependent infrastructure.
    #: Time for the loss of signal to travel the conduit from body to tower.
    signal_travel: float
    tower_spin_down: float
    #: Fraction of rotor speed that survives (0 = stops dead).
    tower_residual_spin: float
    tower_cells_lost: int
    tower_head_lift: float
    tower_head_rotation: tuple

    # Scene dressing that only one reality should own.
    include_idle_dependencies: bool = False
    include_receiver: bool = False

    # How the cut itself reads, in geometry and motion.
    #: Seconds for the release along the limb axis to open ``release_gap``.
    release_duration: float = 0.9
    #: Degrees the remaining stump swings back from the cut, opposing the removed section.
    stump_recoil: float = 0.0
    #: Extra drift of the whole reality away from the primary as it carries out its cut,
    #: as a fraction of ``reality_offset``.
    act_divergence: float = 0.0

    #: This reality's body still models the removed limb and acts on it (see choreography).
    phantom: bool = False
    #: The tower this reality's cut brought down is later re-indexed by the room.
    reindexed: bool = False
    #: The removed region is eventually carried off and disposed of with the receiver.
    disposed: bool = False
    #: It first has to be set down on the receiver (it was not collected when it was cut).
    disposal_needs_handling: bool = False

    @property
    def tower_fail_time(self):
        """Moment the loss of signal reaches the tower."""
        return self.cut_time + self.signal_travel


#: World orientation of the removed arm at rest: lying along +X on the receiver tray.
_LYING_ON_TRAY = q_align_z((-1.0, 0.0, 0.035), hint=Z)


def _limb_space(side, world_rotation):
    """A world orientation expressed relative to the arm's attached pose."""
    return q_mul(q_conj(layout.arm_rotation(side)), world_rotation)


def primary():
    """Plane A's version: the whole arm comes off at the shoulder and is laid on the receiver;
    the tower stops, goes dark and its head separates."""
    return ProcedureVariant(
        name="Primary",
        ghost=False,
        ghost_opacity=1.0,
        tint=(1.0, 1.0, 1.0),
        reality_offset=(0.0, 0.0, 0.0),
        divergence_delay=0.0,
        side=1,
        cut_index=1,
        plane_tilt=Q_IDENTITY,
        cut_time=timeline.PRIMARY_CUT,
        release_gap=0.05,
        detach_duration=timeline.PRIMARY_REGION_AT_REST - timeline.PRIMARY_CUT,
        detach_travel=(0.89, -0.46, -1.70),
        detach_rotation=_limb_space(1, _LYING_ON_TRAY),
        signal_travel=timeline.PRIMARY_INFRASTRUCTURE_FAILURE - timeline.PRIMARY_CUT,
        tower_spin_down=4.0,
        tower_residual_spin=0.0,
        tower_cells_lost=6,
        tower_head_lift=0.5,
        tower_head_rotation=q_mul(q_axis_angle(Z, 25.0), q_axis_angle(Y, 4.0)),
        include_idle_dependencies=True,
        include_receiver=True,
        disposed=True,
        reindexed=True,
    )


def alternate():
    """Plane B's version: a later, lower, tilted cut leaves a stump; the removed part sinks
    instead of being collected; the tower is only crippled and its head slumps."""
    return ProcedureVariant(
        name="Alternate",
        ghost=True,
        ghost_opacity=0.42,
        tint=GHOST_TINT,
        # Sideways and behind: the alternate shows as a fringe, never in front of the primary.
        reality_offset=(0.22, 0.12, 0.0),
        divergence_delay=0.0,
        side=1,
        cut_index=4,
        plane_tilt=q_mul(q_axis_angle(X, 9.0), q_axis_angle(Y, 14.0)),
        cut_time=timeline.ALTERNATE_CUT,
        # A short, quick stroke opens a clear gap on the cue; the stump swings back the other
        # way; the whole reality steps further from the primary. Readable without colour.
        release_gap=0.22,
        release_duration=0.5,
        stump_recoil=10.0,
        act_divergence=0.6,
        detach_duration=timeline.ALTERNATE_REGION_AT_REST - timeline.ALTERNATE_CUT,
        # Sideways, clear of both the stump and the primary's arm on the tray, turning to hang
        # vertically: three versions of the limb, three different silhouettes.
        detach_travel=(0.30, -0.25, -0.25),
        detach_rotation=_limb_space(1, Q_IDENTITY),
        phantom=True,
        disposed=True,
        disposal_needs_handling=True,
        signal_travel=timeline.ALTERNATE_INFRASTRUCTURE_FAILURE - timeline.ALTERNATE_CUT,
        tower_spin_down=5.0,
        tower_residual_spin=0.3,
        tower_cells_lost=3,
        tower_head_lift=0.0,
        tower_head_rotation=q_axis_angle(Y, 16.0),
    )


def extra_alternate(k):
    """The k-th further alternate (k >= 1): a fainter, seeded disagreement about the same cut.

    Only dense profiles build these. Each depends on (SEED, k) alone, so adding more of them
    never changes the ones already there.
    """
    seed = timeline.SEED + 9000 + 17 * k
    angle = stablehash.uniform(seed, 0, 0.0, 2.0 * math.pi)
    radius = 0.16 + 0.07 * k
    warmth = stablehash.uniform(seed, 1, 0.0, 1.0)
    return ProcedureVariant(
        name="Alternate%02d" % (k + 1),
        ghost=True,
        ghost_opacity=0.28,
        tint=(1.0, 0.22 + 0.25 * warmth, 0.04 + 0.30 * (1.0 - warmth)),
        reality_offset=(math.cos(angle) * radius, abs(math.sin(angle)) * radius * 0.6, 0.0),
        divergence_delay=timeline.BEAT * k,
        side=1,
        cut_index=stablehash.choice(seed, 2, (2, 3, 5, 6, 7)),
        plane_tilt=Q_IDENTITY,
        # Scattered on the half-bars between the two main cuts.
        cut_time=timeline.PRIMARY_CUT + 2.0 * timeline.BEAT * k,
        release_gap=0.05,
        detach_duration=stablehash.uniform(seed, 4, 5.0, 7.0),
        detach_travel=(
            stablehash.uniform(seed, 5, 0.1, 0.9),
            stablehash.uniform(seed, 6, -0.8, 0.1),
            stablehash.uniform(seed, 7, -1.4, -0.5),
        ),
        detach_rotation=q_mul(
            q_axis_angle(Y, stablehash.uniform(seed, 8, -60.0, 30.0)),
            q_axis_angle(X, stablehash.uniform(seed, 9, -25.0, 25.0)),
        ),
        signal_travel=timeline.BAR,
        tower_spin_down=stablehash.uniform(seed, 11, 3.0, 6.0),
        tower_residual_spin=stablehash.uniform(seed, 12, 0.0, 0.6),
        tower_cells_lost=1 + int(stablehash.value(seed, 13) * 6),
        tower_head_lift=stablehash.uniform(seed, 14, 0.0, 0.4),
        tower_head_rotation=q_mul(
            q_axis_angle(Z, stablehash.uniform(seed, 15, -30.0, 30.0)),
            q_axis_angle(Y, stablehash.uniform(seed, 16, -18.0, 18.0)),
        ),
    )


def system_branch():
    """The second interpretation of the primary's own dependency: same conduit, same tower, same
    state, somewhere else. It is the primary variant drawn as a shell, so it emerges from the
    primary exactly and differs from it only in where it is."""
    return replace(
        primary(),
        name="SystemBranch",
        ghost=True,
        ghost_opacity=SYSTEM_BRANCH_OPACITY,
        tint=SYSTEM_BRANCH_TINT,
        include_idle_dependencies=False,
        include_receiver=False,
        # The branch is the interpretation the room does not update: its tower stays as it fell.
        reindexed=False,
    )


def for_profile(profile):
    """All realities a profile builds. The first two are identical in every profile."""
    return [primary(), alternate()] + [extra_alternate(k) for k in range(1, profile.extra_alternates + 1)]
