"""What everything is doing at time ``t``.

Every function here is pure: it takes absolute track time (and static data) and returns a pose
or a level. Nothing accumulates from frame to frame, so any frame can be evaluated alone, in
any order, on any machine, in any profile. Things that look cumulative are closed-form.
"""

import math
from dataclasses import dataclass

from . import layout, outer, stablehash, timeline
from .ease import clamp01, out_cubic, pulse, smooth_window, smoother, window
from .vec import (
    Q_IDENTITY, X, Y, Z, add, cross, lerp, mul, normalize, q_align_z, q_axis_angle, q_between,
    q_camera_look, q_conj, q_mul, q_rotate, q_slerp, sub, v_lerp,
)

#: Sever time for a dependency whose region is never removed.
NEVER = 1e9


def variants_alternate():
    """The alternate variant, whose removed forearm the lower camera watches. Imported here,
    late, because variants itself builds on this package's layout."""
    from . import variants
    return variants.alternate()

# ---------------------------------------------------------------- camera

#: Fraction of the camera's path covered by the emphasis surge.
CAMERA_SURGE = 0.10


def _outer_camera():
    """The frame the film starts in and ends in: the plinth under its lamp on the left, the
    tower and the wall carriage to the right."""
    rotation = q_camera_look(sub(layout.OUTER_CAMERA_TARGET, layout.OUTER_CAMERA_POSITION))
    return layout.OUTER_CAMERA_POSITION, rotation, layout.OUTER_CAMERA_FOV


def camera_pose(t):
    """The upper camera: (position, rotation, vertical field of view in degrees)."""
    if outer.in_opening(t):
        return _opening_camera(t)
    if outer.after_the_case(t):
        # The coda and the ending are seen from the same place, and it never moves.
        return _outer_camera()
    return _film_camera(t)


#: When the opening's camera begins to leave the held frame.
_OPENING_CAMERA_LEAVES = 6.0


def _opening_camera(t):
    """One move: out of the outer frame, back down the room, and into the approach. It joins
    the approach at 0:35 with the approach's own position, aim, lens and velocity, so there is
    no seam: it eases onto the line the approach is already travelling."""
    position, rotation, fov = _outer_camera()
    onto = smoother(window(t, _OPENING_CAMERA_LEAVES, outer.OPENING_END))
    if onto <= 0.0:
        return position, rotation, fov
    # The approach, run backward in a straight line from its first frame.
    before = t - outer.OPENING_END
    line = add(layout.CAMERA_START, mul(_CAMERA_COAST_VELOCITY, before))
    line_fov = layout.CAMERA_FOV_START + _CAMERA_FOV_RATE * before
    line_rotation = q_camera_look(sub(layout.CAMERA_TARGET_START, line))
    return v_lerp(position, line, onto), q_slerp(rotation, line_rotation, onto), lerp(fov, line_fov, onto)


def _film_camera(t):
    """The slow approach: (position, rotation, vertical field of view in degrees).

    The move never comes to rest inside the section: it is a slice of a longer shot.
    """
    u = clamp01((t - timeline.SECTION_START) / (timeline.SECTION_END - timeline.SECTION_START))
    # Mostly linear with a gentle ease, so the camera is already moving on the first frame.
    drift = lerp(u, smoother(u), 0.5)
    # Emphasis: part of the approach is held back and spent as a surge that starts on the cue
    # and decays over a bar. The path and its end points are unchanged.
    surge = out_cubic(window(t, timeline.CAMERA_EMPHASIS, timeline.CAMERA_EMPHASIS + timeline.BAR))
    travel = (1.0 - CAMERA_SURGE) * drift + CAMERA_SURGE * surge
    aim = smooth_window(t, timeline.CAMERA_AIM_START, timeline.CAMERA_AIM_END)
    position = v_lerp(layout.CAMERA_START, layout.CAMERA_END, travel)
    target = v_lerp(layout.CAMERA_TARGET_START, layout.CAMERA_TARGET_END, aim)
    # With the surge, the aim opens from the arm toward the part of the room that branches.
    reveal = smooth_window(t, timeline.CAMERA_EMPHASIS, timeline.CAMERA_EMPHASIS + timeline.BAR)
    target = v_lerp(target, layout.CAMERA_TARGET_SYSTEM, reveal)
    fov = lerp(layout.CAMERA_FOV_START, layout.CAMERA_FOV_END, travel)
    if t > timeline.SECTION_END:
        # Past the approach: no new move. The camera coasts on at the speed it arrived with,
        # slowing, and its aim settles a little onto the empty volume where the limb was.
        position = add(position, mul(_CAMERA_COAST_VELOCITY, _coast(t - timeline.SECTION_END, 12.0)))
        settle = smooth_window(t, timeline.SECTION_END, timeline.PHANTOM_LOAD + timeline.BAR)
        target = v_lerp(target, layout.CAMERA_TARGET_PHANTOM, CAMERA_PHANTOM_BIAS * settle)
        # Nothing further. The coast has ended and the aim has settled well before the
        # absent-attractor cue, so that passage is watched from a fixed frame: the room
        # reorganises inside the picture, and the camera neither follows nor points.
        if t > timeline.DISPOSAL_TRANSPORT:
            # The hold ends when the disposal starts to move. One eased move, back and up,
            # onto a wider frame that shows the route. It does not follow the object.
            leave = smoother(window(t, timeline.DISPOSAL_TRANSPORT, timeline.DISPOSAL_TRANSPORT + 2.0 * timeline.BAR))
            position = v_lerp(position, layout.CAMERA_DISPOSAL_POSITION, leave)
            target = v_lerp(target, layout.CAMERA_DISPOSAL_TARGET, leave)
    return position, q_camera_look(sub(target, position)), fov


def _coast(tau, duration):
    """Distance covered, per unit of initial speed, while decelerating evenly to rest."""
    tau = min(tau, duration)
    return tau - tau * tau / (2.0 * duration)


#: How far the aim moves from the branching system toward the empty volume after the approach.
CAMERA_PHANTOM_BIAS = 0.6
# The camera's velocity as the approach ends, so the coast continues it without a seam.
_CAMERA_COAST_VELOCITY = mul(
    sub(layout.CAMERA_END, layout.CAMERA_START),
    (1.0 - CAMERA_SURGE) * 0.5 / (timeline.SECTION_END - timeline.SECTION_START),
)
# The approach starts at the same speed it ends with; its lens narrows at this rate as it starts.
_CAMERA_FOV_RATE = ((layout.CAMERA_FOV_END - layout.CAMERA_FOV_START)
                    * (1.0 - CAMERA_SURGE) * 0.5 / (timeline.SECTION_END - timeline.SECTION_START))


# ---------------------------------------------------------------- realities


def presence(variant, t):
    """0..1: how far an alternate reality has split off. The primary is always fully present."""
    if not variant.ghost:
        return 1.0
    delay = variant.divergence_delay
    return smooth_window(t, timeline.DISAGREEMENT_START + delay, timeline.DIVERGENCE_END + delay) * outer.alternates_presence(t)


def reality_offset(variant, t):
    """Alternates start coincident with the primary, drift apart, and step a little further
    away as they carry out their own cut."""
    act = out_cubic(window(t, variant.cut_time, variant.cut_time + variant.release_duration))
    return mul(variant.reality_offset, presence(variant, t) * (1.0 + variant.act_divergence * act))


def cut_point(variant, t):
    """Where this reality's cut falls, in world space (follows the reality's drift)."""
    return add(layout.arm_cut_point(variant.side, variant.cut_index), reality_offset(variant, t))


def detach_pose(variant, t):
    """Pose of the removed region relative to where it was attached, in limb space.

    A short release along the limb axis that starts at full speed on the cue, a hold, then
    the authored travel.
    """
    cut = variant.cut_time
    release = out_cubic(window(t, cut, cut + variant.release_duration))
    travel = smoother(window(t, cut + 0.6, cut + variant.detach_duration))
    limb = layout.arm_rotation(variant.side)
    offset = add(
        (0.0, 0.0, -variant.release_gap * release),
        mul(q_rotate(q_conj(limb), variant.detach_travel), travel),
    )
    rotation = q_slerp(Q_IDENTITY, variant.detach_rotation, travel)
    if variant.disposed and t > timeline.DISPOSAL_HANDLING:
        offset, rotation = _disposed(variant, t, limb, offset, rotation)
    return offset, rotation


def _disposed(variant, t, limb, offset, rotation):
    """What the disposal procedure does to a removed region, on top of where it was left.
    Nothing here comes from the body or the phantom chain: the motion is imposed from outside."""
    if variant.disposal_needs_handling:
        # Turned flat and set down on the tray, in a straight line, by nothing visible.
        handled = disposal_handling(t)
        resting = add(add(layout.arm_cut_point(variant.side, variant.cut_index), reality_offset(variant, t)),
                      q_rotate(limb, offset))
        correction = sub(layout.DISPOSAL_FOREARM_POSITION, resting)
        offset = add(offset, mul(q_rotate(q_conj(limb), correction), handled))
        # A plain quarter turn from hanging to lying along +x: no roll, nothing expressive.
        lying = q_mul(q_conj(limb), q_between((0.0, 0.0, -1.0), (1.0, 0.0, 0.0)))
        rotation = q_slerp(rotation, lying, handled)
    # Then it goes wherever the receiver goes, until the floor; after that it falls.
    offset = add(offset, q_rotate(q_conj(limb), discard_displacement(variant, t)))
    return offset, q_mul(q_conj(limb), q_mul(discard_tumble(variant, t), q_mul(limb, rotation)))


def stump_pose(variant, t):
    """Rotation of what remains of the limb, in limb space, about the joint it hangs from.

    On the cut the stump swings back, away from the removed section, and stays there: the two
    halves move in opposite directions, which reads as a separation even in silhouette.
    """
    recoil = _stump_recoil_local(variant, t)
    if not variant.phantom:
        return recoil
    # The stump is the only visible part of the limb the body still thinks it is moving.
    return q_mul(recoil, phantom_shoulder(variant, t))   # load, then recruitment


def _stump_recoil_local(variant, t):
    """The stump's swing back from its own cut, in limb space."""
    cut = variant.cut_time
    angle = variant.stump_recoil * out_cubic(window(t, cut, cut + variant.release_duration))
    limb = layout.arm_rotation(variant.side)
    outward = mul(layout.arm_axis(variant.side), -1.0)
    world = q_axis_angle(normalize(cross(outward, Z)), angle)
    return q_mul(q_conj(limb), q_mul(world, limb))


def breath(slab_index, t):
    """Slow ventilation of the torso slabs: a horizontal scale factor."""
    return 1.0 + 0.014 * math.sin(t * (2.0 * math.pi / 4.5) - slab_index * 0.45)


# ---------------------------------------------------------------- dependencies

#: Pulses along a conduit at any moment.
_WAVES = 5.0
#: One pulse leaves the body every two beats, on the beat.
_PULSE_RATE = 1.0 / (2.0 * timeline.BEAT)


def conduit_energy(u, t, sever_time, travel_duration):
    """Energy of the conduit at arc position ``u`` (0 = body, 1 = infrastructure).

    Pulses travel body-to-infrastructure. After the region is severed, darkness follows the
    same route, so cause can be traced to effect across the room.
    """
    wave = 0.5 + 0.5 * math.cos(2.0 * math.pi * (u * _WAVES - (outer.clock(t) - timeline.DOWNBEAT) * _PULSE_RATE))
    energy = (0.22 + 0.78 * wave ** 3) * outer.coupling(t)
    if t >= sever_time:
        # Front of the darkness, overshooting both ends so every segment fully dies.
        front = lerp(-0.06, 1.06, window(t, sever_time, sever_time + travel_duration))
        energy *= smooth_window(u, front - 0.05, front + 0.05)
    return energy


#: Six blades: one blade passes a given point on every beat.
_SPIN = 60.0 / timeline.BEAT  # degrees per second


def rotor_angle(variant, t, fail_time):
    """Rotor angle in degrees: the closed-form integral of its speed.

    Speed is constant until failure, then eases quadratically to the residual fraction.
    """
    if t <= fail_time:
        return _SPIN * outer.clock(t)
    d = variant.tower_spin_down
    r = variant.tower_residual_spin
    u = clamp01((t - fail_time) / d)
    v = 1.0 - u
    during = d * (r * u + (1.0 - r) * (1.0 - v * v * v) / 3.0)
    after = r * max(0.0, t - fail_time - d)
    return _SPIN * (fail_time + during + after)


def cell_energy(variant, index, t, fail_time, seed):
    """Energy of indicator cell ``index`` (0 = top, the first to be lost)."""
    energy = (0.8 + 0.2 * math.sin(outer.clock(t) * 1.7 + index * 0.9)) * outer.coupling(t)
    if index < variant.tower_cells_lost:
        dark = fail_time + 0.5 + index * 0.4
        if dark - 0.6 < t < dark:
            # Stutter before dying, hashed on a fixed 14 Hz clock rather than on frames.
            energy *= 0.35 + 0.65 * stablehash.value(seed + index, int(math.floor(t * 14.0)))
        energy *= 1.0 - window(t, dark, dark + 0.2)
    return energy


def head_cell_energy(t, fail_time):
    return (1.0 - smooth_window(t, fail_time, fail_time + 0.3)) * outer.coupling(t)


def head_pose(variant, t, fail_time):
    """Tower head relative to its seat: (offset, rotation)."""
    h = smoother(window(t, fail_time + 1.0, fail_time + 4.5))
    return (0.0, 0.0, variant.tower_head_lift * h), q_slerp(Q_IDENTITY, variant.tower_head_rotation, h)


# ---------------------------------------------------------------- system branch

#: Degrees the branch swings in the first bar after its cue, and degrees it goes on to drift
#: by the end of the section.
_BRANCH_SNAP = 7.0
_BRANCH_DRIFT = 5.0


# The release: on the cue the branch unlatches from the primary. In a fifth of a second it
# lifts clear and turns through the first part of its swing, so there are visibly two of
# everything within a few frames of the hit; the slow hinge takes over from there.
_BRANCH_RELEASE_SECONDS = 0.2
#: Metres the whole branch rises off its seat, and stays risen.
_BRANCH_RELEASE_LIFT = 0.18
#: Degrees of the first bar's swing that are spent in the release.
_BRANCH_RELEASE_DEGREES = 1.5


def _branch_release(t):
    start = timeline.SYSTEM_DIVERGENCE
    return out_cubic(window(t, start, start + _BRANCH_RELEASE_SECONDS))


def system_branch_presence(t):
    """0 until the cue, fully there three frames later."""
    return window(t, timeline.SYSTEM_DIVERGENCE, timeline.SYSTEM_DIVERGENCE + 0.1) * outer.alternates_presence(t)


def system_branch_lift(t):
    """Metres the branch has risen from where the primary stands."""
    return _BRANCH_RELEASE_LIFT * _branch_release(t)


def system_branch_angle(t):
    """Degrees the branch has hinged away from the primary, about a vertical axis.

    A quick release on the cue, then the swing eases over one bar and never quite stops.
    The totals are unchanged: _BRANCH_SNAP by the end of the bar's ease, plus the drift.
    """
    start = timeline.SYSTEM_DIVERGENCE
    snap = out_cubic(window(t, start, start + timeline.BAR))
    drift = window(t, start, timeline.SECTION_END)
    angle = (_BRANCH_RELEASE_DEGREES * _branch_release(t)
             + (_BRANCH_SNAP - _BRANCH_RELEASE_DEGREES) * snap
             + _BRANCH_DRIFT * drift)
    if t > timeline.SECTION_END:
        # Carries on at the rate it had, slowing, rather than stopping dead.
        rate = _BRANCH_DRIFT / (timeline.SECTION_END - start)
        angle += rate * _coast(t - timeline.SECTION_END, 8.0)
    return angle


# ---------------------------------------------------------------- phantom load
#
# After the amputation the body still carries a model of the limb at its old kinematic
# position, and at the cue it begins a movement with it. The limb is not drawn. What is drawn
# is everything that answers to it: the stump turns at the shoulder, the torso compensates,
# and the load of the absent forearm travels down the conduit to the tower.
# The removed piece itself is not involved: detach_pose knows nothing about any of this.

#: Seconds of the initial flinch.
_PHANTOM_FLINCH = 0.15
#: Share of the gesture spent in the flinch.
_PHANTOM_FLINCH_SHARE = 0.45
#: The gesture peaks this long after the cue, then takes a bar to settle.
_PHANTOM_PEAK = 2.0 * timeline.BEAT
_PHANTOM_SETTLE = timeline.BAR
#: What is left afterwards. The system does not return to neutral.
_PHANTOM_RESIDUE = 0.28
#: Distal joints start later than the shoulder.
_PHANTOM_DISTAL_LAG = 0.15

#: Shoulder: degrees of lift and of inward swing at the peak. Visible, through the stump.
_PHANTOM_SHOULDER_LIFT = 14.0
_PHANTOM_SHOULDER_SWING = 8.0
#: Elbow: degrees of flexion at the peak. Never visible; there is no elbow.
_PHANTOM_ELBOW_FLEX = 30.0

#: Seconds for the load to travel the conduit from the body to the tower.
_PHANTOM_PROPAGATION = 2.0 * timeline.BEAT
#: Metres a conduit segment moves per metre of phantom-hand displacement, at the body end.
_PHANTOM_CONDUIT_GAIN = 0.25
#: Degrees the tower leans against the load, per metre.
_PHANTOM_TOWER_GAIN = 2.0
#: Torso compensation at the peak, in degrees: yaw against the swing, lean away from the arm.
_PHANTOM_TORSO_YAW = 2.0
_PHANTOM_TORSO_LEAN = 1.2


def phantom_activation(t, lag=0.0):
    """0..1 course of the gesture: a quick flinch, a slower reach to the peak, an incomplete
    settling. 0 before the cue; ends at the residue, not at 0."""
    tau = t - timeline.PHANTOM_LOAD - lag
    if tau <= 0.0:
        return 0.0
    flinch = out_cubic(window(tau, 0.0, _PHANTOM_FLINCH))
    reach = smooth_window(tau, _PHANTOM_FLINCH, _PHANTOM_PEAK)
    settle = smooth_window(tau, _PHANTOM_PEAK, _PHANTOM_PEAK + _PHANTOM_SETTLE)
    rise = _PHANTOM_FLINCH_SHARE * flinch + (1.0 - _PHANTOM_FLINCH_SHARE) * reach
    return rise * (1.0 - (1.0 - _PHANTOM_RESIDUE) * settle)


def _phantom_shoulder_world(variant, t, later=True):
    """World rotation of the phantom limb at the shoulder. ``later`` includes what the chain
    does after the phantom load (the recruitment gesture); the load is measured without it."""
    a = phantom_activation(t)
    outward = mul(layout.arm_axis(variant.side), -1.0)
    lift_axis = normalize(cross(outward, Z))
    lift = q_axis_angle(lift_axis, _PHANTOM_SHOULDER_LIFT * a)
    swing = q_axis_angle(Z, -_PHANTOM_SHOULDER_SWING * variant.side * a)
    load = q_mul(swing, lift)
    if not later:
        return load
    return q_mul(q_axis_angle(lift_axis, _RECRUIT_SHOULDER * recruitment_gesture(t)), load)


def phantom_shoulder(variant, t):
    """Rotation of the phantom limb at the shoulder, in limb space."""
    limb = layout.arm_rotation(variant.side)
    return q_mul(q_conj(limb), q_mul(_phantom_shoulder_world(variant, t), limb))


def phantom_chain(variant, t, drift=True):
    """The invisible limb: world positions of its (shoulder, elbow, hand), in its reality's
    space, from the pre-amputation pose plus the gesture. Forward kinematics, two joints.

    ``drift`` includes everything the chain does after the phantom load: the slow flexion of
    the elbow during the absent-attractor passage, and the recruitment gesture. The phantom
    *load* is measured without them, so later passages do not re-run the load's consequences."""
    pose, flex = _phantom_joints(variant, t, later=drift)
    upper = layout.arm_elbow_distance()
    fore = layout.arm_length() - upper
    elbow_local = (0.0, 0.0, -upper)
    hand_local = add(elbow_local, q_rotate(flex, (0.0, 0.0, -fore)))
    shoulder = layout.arm_origin(variant.side)
    return shoulder, add(shoulder, q_rotate(pose, elbow_local)), add(shoulder, q_rotate(pose, hand_local))


def _phantom_joints(variant, t, later=True):
    """The chain's two joints: (world rotation of the upper arm, elbow flexion in limb space)."""
    limb = layout.arm_rotation(variant.side)
    pose = q_mul(_phantom_shoulder_world(variant, t, later), limb)
    degrees = _PHANTOM_ELBOW_FLEX * phantom_activation(t, _PHANTOM_DISTAL_LAG)
    if later:
        degrees += _ATTRACTOR_ELBOW_DRIFT * attractor_progress(t)
        degrees += _RECRUIT_ELBOW * recruitment_gesture(t - _RECRUIT_DISTAL_LAG)
    return pose, q_axis_angle(X, degrees * variant.side)


def phantom_forearm(variant, t):
    """World orientation of the phantom forearm: the upper arm's rotation, then the elbow's."""
    pose, flex = _phantom_joints(variant, t)
    return q_mul(pose, flex)


def phantom_load(variant, t):
    """Displacement of the phantom hand from where the real hand used to rest, in metres.
    This vector is the load the rest of the system responds to."""
    if not variant.phantom:
        return (0.0, 0.0, 0.0)
    return sub(phantom_chain(variant, t, drift=False)[2],
               phantom_chain(variant, timeline.PHANTOM_LOAD, drift=False)[2])


def torso_compensation(variant, t):
    """The torso's answer to the gesture: a small yaw against the swing and a lean away from
    the arm, about the base of the torso."""
    a = phantom_activation(t) if variant.phantom else 0.0
    yaw = q_axis_angle(Z, _PHANTOM_TORSO_YAW * variant.side * a)
    lean = q_axis_angle(Y, -_PHANTOM_TORSO_LEAN * variant.side * a)
    return q_mul(yaw, lean)


def conduit_displacement(variant, u, t):
    """How far the conduit at arc position ``u`` is pulled by the phantom load. The pull
    reaches each point later the further it is from the body, and weakens along the way."""
    load = phantom_load(variant, t - u * _PHANTOM_PROPAGATION)
    return mul(load, _PHANTOM_CONDUIT_GAIN * (1.0 - 0.5 * u))


def tower_lean(variant, t):
    """The tower braces against the load once it arrives: it leans directly away from the
    horizontal direction the phantom hand has moved in."""
    load = phantom_load(variant, t - _PHANTOM_PROPAGATION)
    size = math.hypot(load[0], load[1])
    if size < 1e-9:
        return Q_IDENTITY
    # Rotating about (y, -x, 0) carries the top of the tower toward (-x, -y).
    total = math.sqrt(size * size + load[2] * load[2])
    return q_axis_angle((load[1] / size, -load[0] / size, 0.0), _PHANTOM_TOWER_GAIN * total)


# ---------------------------------------------------------------- re-indexing
#
# After the amputation and the body's own response to it, the room runs a routine: it measures
# the state it is now in and accepts it. Nothing is hurt, nothing fails and the body does
# nothing. Two pieces of solid apparatus act, one bar apart:
#
#   first index   the head of the tower the cut brought down, left lifted and turned aside,
#                 levels, lowers and turns to face the shoulder the arm was removed from;
#   second index  a cabinet on the wall, which is a carriage on the wall rail, runs toward the
#                 body's line and stops;
#   cross-check   the head turns from the body to the carriage, and as it arrives the
#                 carriage extends: the two are checked against each other;
#   accepted      the carriage retracts and backs off, the head follows it and rises. Neither
#                 goes back to where it was. That arrangement is the state the room now keeps.
#
# Every move is one eased stroke between two rests: no overshoot, no oscillation.

#: Seconds each stroke takes.
_REINDEX_STROKE = 1.6
#: Metres the head hangs above its seat while it works, and where it ends.
_REINDEX_HEAD_WORKING = 0.20
_REINDEX_HEAD_ACCEPTED = 0.42
#: Metres the carriage runs along the wall toward the body, and how much of that it keeps.
_REINDEX_SLIDE = 0.75
_REINDEX_SLIDE_KEPT = 0.20
#: Metres the carriage extends upward, and how much of that it keeps.
_REINDEX_EXTENSION = 0.50
_REINDEX_EXTENSION_KEPT = 0.12
#: Seconds after the head starts toward the carriage that the carriage starts to extend.
_REINDEX_HANDOVER = 0.6
#: When the last stroke ends. Everything is at rest from here on.
REINDEX_END = timeline.REINDEX_ACCEPT + 0.6 + 1.2


def _stroke(t, start, seconds=_REINDEX_STROKE):
    return smoother(window(t, start, start + seconds))


def reindex_carriage(t):
    """(metres run along the wall toward the body, metres extended upward) for the carriage.

    In the opening it arrives at its station from further along the wall (a negative run).
    In the ending it leaves the arrangement it accepted at 1:20 and repeats the cross-check
    position, against nothing, and stays there."""
    if outer.in_opening(t):
        return -outer.opening_carriage(t), 0.0
    if outer.in_ending(t):
        run, extend = outer.ending_carriage(t)
        return (lerp(_REINDEX_SLIDE_KEPT, _REINDEX_SLIDE, run),
                lerp(_REINDEX_EXTENSION_KEPT, _REINDEX_EXTENSION, extend))
    out = _stroke(t, timeline.REINDEX_SECOND)
    back = _stroke(t, timeline.REINDEX_ACCEPT + 0.6, 1.2)
    slide = _REINDEX_SLIDE * out - (_REINDEX_SLIDE - _REINDEX_SLIDE_KEPT) * back
    up = _stroke(t, timeline.REINDEX_CROSSCHECK + _REINDEX_HANDOVER, 1.3)
    down = _stroke(t, timeline.REINDEX_ACCEPT, 0.9)
    extension = _REINDEX_EXTENSION * up - (_REINDEX_EXTENSION - _REINDEX_EXTENSION_KEPT) * down
    return slide, extension


def reindex_carriage_rest():
    """(x, y, height) of the carriage before any of this: where the cabinet has always stood."""
    index, side = layout.REINDEX_CABINET
    y, height, _ = layout.cabinet(timeline.SEED, index, side)
    return side * layout.CABINET_X, y, height


def reindex_carriage_top(t):
    """World position of the centre of the carriage's top face."""
    x, y, height = reindex_carriage_rest()
    slide, extension = reindex_carriage(t)
    return x, y - slide, height + extension


def _head_yaw_toward(side, point):
    """Degrees about +z that turn a tower head, which faces along its local -y, toward a point."""
    tower = layout.tower_position(side)
    return math.degrees(math.atan2(point[0] - tower[0], tower[1] - point[1]))


def reindex_head(variant, t, fail_time):
    """Head of a re-indexed tower relative to its seat: (offset, rotation). Until the first
    index this is exactly ``head_pose``: the head as the failure left it."""
    offset, fallen = head_pose(variant, t, fail_time)
    if not variant.reindexed:
        return offset, fallen
    to_body = _head_yaw_toward(variant.side, layout.arm_origin(variant.side))
    if outer.in_opening(t):
        # Before the case: parked, then turned to the body, then seated at its working heading.
        toward, seated = outer.opening_head(t)
        yaw = lerp(lerp(outer.HEAD_PARKED_YAW, to_body, toward), 0.0, seated)
        return (0.0, 0.0, outer.HEAD_PARKED_LIFT * (1.0 - seated)), q_axis_angle(Z, yaw)
    if t <= timeline.REINDEX_FIRST:
        return offset, fallen
    if outer.in_ending(t):
        # After the case: from the carriage it was last checked against, to the empty coordinate.
        accepted, level = reindex_head(variant, outer.ENDING_START - 1.0, fail_time)
        yaw = math.degrees(2.0 * math.atan2(level[3], level[0]))
        return accepted, q_axis_angle(Z, lerp(yaw, to_body, outer.ending_head(t)))
    # The failure left it turned about the vertical and tipped. Take those apart.
    yaw_fallen = math.degrees(2.0 * math.atan2(fallen[3], fallen[0]))
    tip = q_mul(q_axis_angle(Z, -yaw_fallen), fallen)

    first = _stroke(t, timeline.REINDEX_FIRST)
    cross = _stroke(t, timeline.REINDEX_CROSSCHECK, 1.4)
    accept = _stroke(t, timeline.REINDEX_ACCEPT, 1.2)

    # Once it has turned to the carriage it stays on it, wherever the carriage goes.
    to_carriage = _head_yaw_toward(variant.side, reindex_carriage_top(t))
    yaw = lerp(lerp(yaw_fallen, to_body, first), to_carriage, cross)
    lift = lerp(offset[2], _REINDEX_HEAD_WORKING, first) + (_REINDEX_HEAD_ACCEPTED - _REINDEX_HEAD_WORKING) * accept
    return (0.0, 0.0, lift), q_mul(q_axis_angle(Z, yaw), q_slerp(tip, Q_IDENTITY, first))


# ---------------------------------------------------------------- absent attractor
#
# phantom_load: the amputated body still contains a model of the lost limb.
# absent_attractor: the system outside the body begins to organise itself around it.
#
# The phantom hand's position becomes a coordinate that several unrelated structures come to
# agree on. Nothing is placed there. Each structure acknowledges it in its own way and in its
# own time, by turning or leaning, never by travelling toward it, and each keeps its new
# orientation. Three things stay distinct: the removed piece (material remainder, untouched),
# the phantom chain (bodily memory), and this locus (a place the room now has).

#: Seconds from the cue to full convergence: one phrase.
_ATTRACTOR_SPAN = 4.0 * timeline.BAR
#: Degrees the invisible elbow goes on flexing, which carries the locus away from the removed piece.
_ATTRACTOR_ELBOW_DRIFT = 20.0
#: Bars after the cue at which the conduit's end and the tower head begin to respond.
_ATTRACTOR_CONDUIT_DELAY = 0.0
_ATTRACTOR_TOWER_DELAY = 1.0
#: Bars after the cue at which the far wall panel begins to respond.
_ATTRACTOR_PANEL_DELAY = 3.0


def attractor_progress(t, delay_bars=0.0):
    """0..1 for a response that starts ``delay_bars`` after the cue. Every response arrives at
    the same moment, the end of the phrase, however late it started; none of them reverses."""
    start = timeline.ABSENT_ATTRACTOR + delay_bars * timeline.BAR
    return smoother(window(t, start, timeline.ABSENT_ATTRACTOR + _ATTRACTOR_SPAN))


def phantom_locus(variant, t):
    """World position of the phantom hand: the empty coordinate. Derived from the invisible
    chain and its reality's drift, and from nothing else."""
    return add(phantom_chain(variant, t)[2], reality_offset(variant, t))


def attractor_point(variant):
    """Where the locus has settled when the responses converge. The responses aim here."""
    return phantom_locus(variant, timeline.ABSENT_ATTRACTOR + _ATTRACTOR_SPAN)


def _attractor_point_local(variant):
    """The same point in the variant's own reality space, for parts that live there."""
    return phantom_chain(variant, timeline.ABSENT_ATTRACTOR + _ATTRACTOR_SPAN)[2]


def conduit_end_aim(variant, t):
    """Rotation of the conduit's last run, about the corner it hangs from.

    That run ended at the shoulder. It turns until it points at where the hand would be: the
    conduit keeps its place and changes what it is addressed to."""
    if not variant.phantom:
        return Q_IDENTITY
    path = layout.conduit_path(variant.side)
    full = q_between(sub(path[0], path[1]), sub(_attractor_point_local(variant), path[1]))
    return q_slerp(Q_IDENTITY, full, attractor_progress(t, _ATTRACTOR_CONDUIT_DELAY))


def tower_head_face():
    """Point on the tower head's front face, relative to the tower's foot."""
    return (0.0, -0.52, layout.TOWER_HEAD_HEIGHT + 0.3)


def tower_head_aim(variant, t):
    """Extra rotation of the tower head, applied over its slump: it turns until its face looks
    at the empty point."""
    if not variant.phantom:
        return Q_IDENTITY
    head = add(layout.tower_position(variant.side), (0.0, 0.0, layout.TOWER_HEAD_HEIGHT + 0.3))
    full = q_between((0.0, -1.0, 0.0), sub(_attractor_point_local(variant), head))
    return q_slerp(Q_IDENTITY, full, attractor_progress(t, _ATTRACTOR_TOWER_DELAY))


def panel_attend(variant, t):
    """A panel of the far wall turns until its normal passes through the point: across, and
    down, since the panel is high on the wall. The latest response, and the furthest away."""
    center = layout.back_panel_center(*layout.ATTRACTOR_PANEL)
    full = q_between((0.0, -1.0, 0.0), sub(attractor_point(variant), center))
    return q_slerp(Q_IDENTITY, full, attractor_progress(t, _ATTRACTOR_PANEL_DELAY))


# ---------------------------------------------------------------- prosthetic recruitment
#
# phantom_load: the body moves as though the missing limb still exists.
# absent_attractor: the environment reorganises around the missing limb's location.
# prosthetic_recruitment: one part of the environment begins to function as though it IS
# part of the missing limb.
#
# The stump makes a slow, deliberate movement. The invisible chain carries it through the
# absent elbow. One solid wall rib, across the room and attached to nothing, then turns about
# its foot through exactly the rotation the phantom forearm has made, two beats later. Nothing
# joins them. The relation is the only thing added.

#: Degrees the stump articulates at the shoulder at the height of the gesture.
_RECRUIT_SHOULDER = 8.8
#: The rib does not take the forearm's rotation one for one. It takes this fraction of it,
#: chosen so that the rib's own extent stays what it was when the body's gesture was smaller.
_RECRUIT_RIB_EXTENT = 7.5
#: Further degrees at the absent elbow, which starts a little after the shoulder.
_RECRUIT_ELBOW = 1.0
_RECRUIT_DISTAL_LAG = 0.3
#: The rib answers this long after the body: two beats, which is when the bass lands.
_RECRUIT_DELAY = 2.0 * timeline.BEAT
RECRUIT_GAIN = _RECRUIT_RIB_EXTENT / (_RECRUIT_SHOULDER + _RECRUIT_ELBOW)


def recruitment_gesture(t):
    """Course of the body's gesture, 0..1 of its full extent: out over two beats, held for two,
    then settling to a residue. One clear statement, answered once by the rib, and over before
    the lyric turns to what has become of the limb. (It used to go back and out a second time;
    that was cut so the disposal could take the passage.)"""
    tau = t - timeline.PROSTHETIC_RECRUITMENT
    if tau <= 0.0:
        return 0.0
    beat = timeline.BEAT
    out = smoother(window(tau, 0.0, 2.0 * beat))
    settle = smoother(window(tau, 4.0 * beat, 6.0 * beat))
    return out - (1.0 - RECRUIT_RESIDUE) * settle


#: What the gesture leaves behind, as a fraction of its full extent. Incorporation persists.
RECRUIT_RESIDUE = 0.2


def recruited_rotation(variant, t):
    """Rotation of the recruited rib about its foot.

    It is a fixed fraction of the rotation the phantom forearm has made since the cue, taken
    ``_RECRUIT_DELAY`` earlier: R_rib(t) = [F(t - d) * F(cue)^-1] ^ RECRUIT_GAIN, with F the
    forearm's world orientation and the power meaning the same rotation through that fraction
    of its angle. The rib is not aimed at anything. It is driven as the distal segment of the
    chain."""
    if not variant.phantom:
        return Q_IDENTITY
    then = t - _RECRUIT_DELAY
    if then <= timeline.PROSTHETIC_RECRUITMENT:
        return Q_IDENTITY
    reference = phantom_forearm(variant, timeline.PROSTHETIC_RECRUITMENT)
    return q_slerp(Q_IDENTITY, q_mul(phantom_forearm(variant, then), q_conj(reference)), RECRUIT_GAIN)


def _recruit_shoulder_local(variant, t):
    """The recruitment gesture's rotation at the shoulder, in limb space."""
    limb = layout.arm_rotation(variant.side)
    outward = mul(layout.arm_axis(variant.side), -1.0)
    world = q_axis_angle(normalize(cross(outward, Z)), _RECRUIT_SHOULDER * recruitment_gesture(t))
    return q_mul(q_conj(limb), q_mul(world, limb))


def _socket_local(variant):
    """Where the shoulder articulates during recruitment, in limb space: a little inboard of
    the shoulder ball, so the ball itself swings with the gesture."""
    offset = layout.SHOULDER_SOCKET_OFFSET
    return q_rotate(q_conj(layout.arm_rotation(variant.side)), (offset[0] * variant.side, offset[1], offset[2]))


def socket_swing(variant, point, t):
    """Where a point of the proximal shoulder assembly (in limb space) is carried by the
    recruitment gesture: turned about the socket. Identity before the cue."""
    if not variant.phantom:
        return point
    socket = _socket_local(variant)
    return add(socket, q_rotate(_recruit_shoulder_local(variant, t), sub(point, socket)))


def stump_shift(variant, t):
    """Translation of the stump's pivot, in limb space, that makes its recruitment rotation
    turn about the socket instead of about the shoulder ball's own centre."""
    if not variant.phantom:
        return (0.0, 0.0, 0.0)
    socket = _socket_local(variant)
    turned = sub(socket, q_rotate(_recruit_shoulder_local(variant, t), socket))
    # The stump's earlier recoil is applied outside the recruitment gesture.
    return q_rotate(_stump_recoil_local(variant, t), turned)


# ---------------------------------------------------------------- disposal
#
# The institution stops treating the removed part as part of a person and processes it as
# material. The black tray that collected the primary's arm at 0:56 is the receiver of a
# disposal system: the alternate's forearm, left hanging since 0:55, is turned flat and set
# down on it; the receiver runs along the floor channel, which is a track; where it stops the
# channel opens into an aperture; receiver and load go down through the floor; the floor
# closes. Routine, externally imposed, and indifferent to everything the body is still doing:
# the phantom chain, its load, the room's convergence and the recruited rib are all untouched.

#: Beats the receiver takes to run the channel, and to go down.
_DISPOSAL_RUN_BEATS = 3.0
_DISPOSAL_DROP_BEATS = 1.0


def disposal_handling(t):
    """0..1: the alternate's forearm being turned flat and set down on the tray."""
    return smoother(window(t, timeline.DISPOSAL_HANDLING, timeline.DISPOSAL_TRANSPORT))


def disposal_carriage(t):
    """World displacement of the receiver, and of everything riding on it."""
    run = smoother(window(t, timeline.DISPOSAL_TRANSPORT, timeline.DISPOSAL_TRANSPORT + _DISPOSAL_RUN_BEATS * timeline.BEAT))
    drop = disposal_drop(t)
    route = layout.DISPOSAL_ROUTE
    down = layout.DISPOSAL_DROP * drop
    threshold = disposal_threshold_time()
    if t > threshold:
        # Out of sight under the floor the receiver has nothing more to carry. It stops just
        # below, inside the chute, instead of running on to its full travel.
        down = layout.DISPOSAL_DROP * disposal_drop(threshold) + 0.2 * out_cubic(window(t, threshold, threshold + 0.12))
    return (route[0] * run, route[1] * run, route[2] * run - down)


def disposal_drop(t):
    """0..1: how far down the receiver has gone. A lowering at an even rate, not a fall."""
    return smooth_window(t, timeline.LANDFILL, timeline.LANDFILL + _DISPOSAL_DROP_BEATS * timeline.BEAT)


def disposal_threshold_time():
    """The moment the last of the load passes below the floor: after this nothing of the
    removed parts can be seen. Solved from the lowering curve."""
    need = layout.DISPOSAL_LOAD_TOP / layout.DISPOSAL_DROP
    lo, hi = timeline.LANDFILL, timeline.LANDFILL + _DISPOSAL_DROP_BEATS * timeline.BEAT
    for _ in range(60):
        mid = (lo + hi) * 0.5
        if disposal_drop(mid) < need:
            lo = mid
        else:
            hi = mid
    return hi


def disposal_aperture(t):
    """0..1: how far the floor channel has opened where the receiver stops. It opens over the
    beat before the receiver has to go through and closes over the two beats after."""
    beat = timeline.BEAT
    opening = smooth_window(t, timeline.LANDFILL - 2.0 * beat, timeline.LANDFILL - beat)
    closing = smooth_window(t, timeline.LANDFILL + _DISPOSAL_DROP_BEATS * beat, timeline.DISPOSAL_SEALED)
    return opening * (1.0 - closing)


# ---------------------------------------------------------------- landfill
#
# Below the floor the removed parts stop being carried and fall. The fall starts at the
# threshold with exactly the speed the receiver was lowering them at, so the motion is
# continuous across the cut to the camera below; from there it is gravity. They land on a heap
# of what has been disposed of before. Nothing in this section knows about the body.

_GRAVITY = 9.81


def _release_speed():
    """Metres per second the load is going down at as it passes the floor."""
    duration = _DISPOSAL_DROP_BEATS * timeline.BEAT
    u = (disposal_threshold_time() - timeline.LANDFILL) / duration
    return layout.DISPOSAL_DROP * 6.0 * u * (1.0 - u) / duration


def _discard_profile(variant):
    """How each removed part falls. The alternate's forearm is the one the lyric is about: it
    falls straight, lands on the crest of the heap at the impact cue, and hops once. The
    primary's arm drifts aside and lands a little later and lower, among arms like it."""
    fall = timeline.LANDFILL_IMPACT - disposal_threshold_time()
    if variant.disposal_needs_handling:
        return {"fall": fall, "drift": (0.0, 0.0), "axis": Y, "tumble": 165.0, "settle": 23.0,
                "hop": 0.18, "hop_time": 0.4, "slide": (-0.20, 0.10, 0.0)}
    return {"fall": fall + 0.12, "drift": (1.2, -0.9), "axis": X, "tumble": 80.0, "settle": 10.0,
            "hop": 0.0, "hop_time": 0.25, "slide": (0.12, -0.09, 0.0)}


def discard_fall(variant, tau):
    """World displacement of a removed part ``tau`` seconds after it passes the floor."""
    k = _discard_profile(variant)
    airborne = min(tau, k["fall"])
    position = (k["drift"][0] * airborne, k["drift"][1] * airborne,
                -_release_speed() * airborne - 0.5 * _GRAVITY * airborne * airborne)
    if tau > k["fall"]:
        # Arrival: one short hop (for the forearm), a little slide, then rest.
        s = window(tau - k["fall"], 0.0, k["hop_time"])
        position = add(position, mul(k["slide"], out_cubic(s)))
        position = add(position, (0.0, 0.0, 4.0 * k["hop"] * s * (1.0 - s)))
    return position


def discard_displacement(variant, t):
    """World displacement of a removed part during the whole disposal: carried, then falling."""
    threshold = disposal_threshold_time()
    if t <= threshold:
        return disposal_carriage(t)
    return add(disposal_carriage(threshold), discard_fall(variant, t - threshold))


def discard_tumble(variant, t):
    """World rotation a removed part picks up as it falls: an even turn, not a gesture."""
    tau = t - disposal_threshold_time()
    if tau <= 0.0:
        return Q_IDENTITY
    k = _discard_profile(variant)
    turn = k["tumble"] * min(tau, k["fall"]) / k["fall"]
    if tau > k["fall"]:
        turn += k["settle"] * out_cubic(window(tau - k["fall"], 0.0, k["hop_time"]))
    return q_axis_angle(k["axis"], turn)


def discard_position(variant, t):
    """World position of a removed part's cut end."""
    limb = layout.arm_rotation(variant.side)
    rest = add(layout.arm_cut_point(variant.side, variant.cut_index), reality_offset(variant, t))
    return add(rest, q_rotate(limb, detach_pose(variant, t)[0]))


def discard_landing(variant):
    """Where a removed part finally lies, in the world."""
    return discard_position(variant, timeline.TIMELINE_END)


def discard_impact_time(variant):
    return disposal_threshold_time() + _discard_profile(variant)["fall"]


def landfill_nudge(t):
    """0..1: loose pieces on the crest shifting as the forearm lands. Once, and they stay."""
    return out_cubic(window(t, timeline.LANDFILL_IMPACT, timeline.LANDFILL_IMPACT + 0.3))


def lower_camera_pose(t):
    """The camera below the floor: (position, rotation, vertical field of view).

    Two movements. It is cut to as the forearm comes out of the chute, goes down with the fall
    and ends close to the heap as the forearm lands. Then, once the forearm has settled, it
    leaves: forward over the heap and on across the field, climbing.
    """
    if t <= timeline.LANDFILL_FLYOVER:
        return _lower_camera_fall(t)
    if outer.in_ending(t):
        # Not the camera the ending is seen through. It stays where the ending's lock recorded
        # it: on the flyover's own line, as if the hinge had never left it.
        return _lower_camera_flyover(t, hinge=False)
    return _lower_camera_flyover(min(t, HINGE_CUT))


# ---- the hinge: from 1:52.5 the same flight goes up, through the level the chutes hang from
# and on above it, slowing and tipping down until the field is nearly a plan. Everything here
# is zero, with zero rate, at 1:52.5, so the locked flyover runs into it without a seam.

HINGE_START = timeline.TIMELINE_END
HINGE_OPEN = timeline.cue("hinge_open")
HINGE_DRAIN = timeline.cue("hinge_drain")
HINGE_CUT = timeline.cue("hinge_cut")
#: Metres the camera has risen above the flyover's height by the drain cue, and by the cut.
_HINGE_RISE = (10.8, 177.0)
#: Fraction of its cruising speed the camera has lost by the cut.
_HINGE_SLOWED = 0.75
#: Degrees below the horizon it comes to look, and when it gets there: two seconds before the
#: cut it is as near a plan view as it goes, still moving, still in perspective.
_HINGE_PITCH = 72.0
_HINGE_PITCH_REACHED = HINGE_CUT - 2.0


def hinge_rise(t):
    """Metres the camera has climbed above the flyover: a power law through the two heights
    above, so it starts with no rate at all and is still accelerating at the cut."""
    s = max(0.0, min(t, HINGE_CUT) - HINGE_START)
    if s <= 0.0:
        return 0.0
    a, b = HINGE_DRAIN - HINGE_START, HINGE_CUT - HINGE_START
    power = math.log(_HINGE_RISE[1] / _HINGE_RISE[0]) / math.log(b / a)
    return _HINGE_RISE[0] * (s / a) ** power


def hinge_lag(t):
    """Metres the camera has fallen behind its cruise: from the drain cue its forward speed
    eases down. Closed form: the integral of a smoothstep."""
    u = window(t, HINGE_DRAIN, HINGE_CUT)
    return _FLY_CRUISE * _HINGE_SLOWED * (HINGE_CUT - HINGE_DRAIN) * (u * u * u - 0.5 * u * u * u * u)


def hinge_pitch(t):
    """Degrees further down the camera looks than the flyover did."""
    return (_HINGE_PITCH - _FLY_PITCH[1]) * smoother(window(t, HINGE_DRAIN - 0.5, _HINGE_PITCH_REACHED))


def which_camera(t):
    """"upper", "lower" or "hinge": the camera the film is seen through at time t."""
    if t < timeline.LANDFILL_CUT or outer.after_the_case(t):
        return "upper"
    return "lower" if t < HINGE_CUT else "hinge"


#: Metres per second: the first low glide, and the cruise it builds to after the climb begins.
_FLY_GLIDE = 2.2
_FLY_CRUISE = 6.0
#: Metres the camera rises over the flight.
_FLY_RISE = 14.6
#: Degrees below the horizon the camera looks: as the climb begins, and at the widest view.
#: It lifts its gaze as it rises, which is what brings the far field and the chutes into frame.
_FLY_PITCH = (17.0, 14.0)


def flyover_heading():
    """Unit horizontal direction of the flight: from where the camera stood, over the forearm."""
    start = _lower_camera_fall(timeline.LANDFILL_FLYOVER)[0]
    landing = discard_landing(variants_alternate())
    return normalize((landing[0] - start[0], landing[1] - start[1], 0.0))


def flyover_distance(t):
    """Metres flown forward. Speed starts at zero and approaches the glide speed; from the
    climb cue it approaches the cruise speed. Closed-form, so there is nothing to integrate."""
    tau = max(0.0, t - timeline.LANDFILL_FLYOVER)
    glide = _FLY_GLIDE * (tau - 0.6 * (1.0 - math.exp(-tau / 0.6)))
    tc = max(0.0, t - timeline.LANDFILL_FLYOVER_CLIMB)
    return glide + (_FLY_CRUISE - _FLY_GLIDE) * (tc - 2.0 * (1.0 - math.exp(-tc / 2.0)))


def flyover_height(t):
    """Metres risen: barely at first, then the whole climb between its cue and the widest view."""
    lift = 0.6 * smooth_window(t, timeline.LANDFILL_FLYOVER, timeline.LANDFILL_FLYOVER_CLIMB)
    return lift + (_FLY_RISE - 0.6) * smoother(window(t, timeline.LANDFILL_FLYOVER_CLIMB, timeline.LANDFILL_FLYOVER_WIDE))


def _lower_camera_flyover(t, hinge=True):
    start, rotation, fov = _lower_camera_fall(timeline.LANDFILL_FLYOVER)
    heading = flyover_heading()
    lag, rise, tip = (hinge_lag(t), hinge_rise(t), hinge_pitch(t)) if hinge else (0.0, 0.0, 0.0)
    position = add(add(start, mul(heading, flyover_distance(t) - lag)), (0.0, 0.0, flyover_height(t) + rise))

    # It stops looking at the forearm and looks where it is going: the forearm slides down
    # the frame and out of it. Nothing follows it.
    landing = discard_landing(variants_alternate())
    at_forearm = normalize(sub((landing[0], landing[1], landing[2] + 0.4), start))
    pitch = math.radians(lerp(_FLY_PITCH[0], _FLY_PITCH[1],
                              smooth_window(t, timeline.LANDFILL_FLYOVER_CLIMB, timeline.LANDFILL_FLYOVER_WIDE))
                         + tip)
    ahead = (heading[0] * math.cos(pitch), heading[1] * math.cos(pitch), -math.sin(pitch))
    turn = smooth_window(t, timeline.LANDFILL_FLYOVER + 0.2, timeline.LANDFILL_FLYOVER + 2.6)
    return position, q_camera_look(normalize(v_lerp(at_forearm, ahead, turn))), fov


def _lower_camera_fall(t):
    """It opens looking up at the chute, stays on the forearm for most of the fall, and only
    settles onto the landing place at the end."""
    forearm = variants_alternate()
    start, impact = timeline.LANDFILL_CUT, timeline.LANDFILL_IMPACT
    descent = smoother(window(t, start - 0.15, impact + 0.3))
    position = v_lerp(layout.LOWER_CAMERA_START, layout.LOWER_CAMERA_END, descent)
    falling = discard_position(forearm, max(t, start))
    landing = discard_landing(forearm)
    lead = 0.05 + 0.95 * smooth_window(t, impact - 0.3, impact + 0.1)
    target = (landing[0], landing[1], lerp(falling[2], landing[2] + 0.4, lead))
    return position, q_camera_look(sub(target, position)), layout.LOWER_CAMERA_FOV


def camera_is_below(t):
    """Which of the two cameras the film is seen through."""
    return timeline.LANDFILL_CUT <= t <= outer.CODA_START


def receiver_offset(t):
    """Where the receiver is, relative to its place beside the plinth: short of it in the
    opening, then wherever the disposal carries it."""
    if outer.in_opening(t):
        return mul(outer.TRAY_SHORT, outer.opening_tray(t))
    return disposal_carriage(t)


# ---------------------------------------------------------------- cutting planes


#: Seconds for a plane to become visible on its cue: three frames, so it reads as a hit.
_PLANE_APPEAR = 0.1


@dataclass(frozen=True)
class PlaneCue:
    enter: float
    arrive: float
    retreat_start: float
    retreat_end: float
    #: Where the plane waits before sliding in, relative to its cut.
    entry_offset: tuple
    #: Phase of the contest oscillation; the two planes are in antiphase.
    phase: float


PLANE_A = PlaneCue(
    timeline.PLANE_A_ENTER, timeline.PLANE_A_ARRIVE,
    timeline.PLANE_A_RETREAT_START, timeline.PLANE_A_RETREAT_END,
    entry_offset=(2.5, 0.0, 0.6), phase=0.0,
)
PLANE_B = PlaneCue(
    timeline.PLANE_B_ENTER, timeline.PLANE_B_ARRIVE,
    timeline.PLANE_B_RETREAT_START, timeline.PLANE_B_RETREAT_END,
    entry_offset=(0.0, -1.2, 1.8), phase=math.pi,
)


def plane_pose(cue, owner, rival, t):
    """A cutting plane: (position, rotation, scale factor, opacity).

    ``owner`` is the variant whose cut this plane performs; ``rival`` is the one it argues with.
    Opacity may exceed 1 during the flash at the moment of the cut.
    """
    cut = cut_point(owner, t)
    cut_time = owner.cut_time
    arrive = smoother(window(t, cue.enter, cue.arrive))
    # The plane is there from its cue, announced by a short flare, and then slides into place.
    present = window(t, cue.enter, cue.enter + _PLANE_APPEAR)
    flare = pulse(t, cue.enter, cue.enter + _PLANE_APPEAR, cue.enter + 0.2, cue.enter + 1.0)

    # The contest: while both planes are present each one lunges toward the other's cut,
    # then settles exactly on its own before it is carried out.
    contest = pulse(t, timeline.DISAGREEMENT_START, timeline.DISAGREEMENT_START + 1.0, cut_time - 0.6, cut_time)
    # One lunge every two beats, the two planes alternating.
    wobble = math.sin((t - timeline.DOWNBEAT) * (math.pi / timeline.BEAT) + cue.phase)
    lunge = contest * max(0.0, wobble)

    position = add(cut, mul(cue.entry_offset, 1.0 - arrive))
    position = add(position, mul(sub(cut_point(rival, t), cut), 0.3 * lunge))

    # Plane normal along the limb axis, plus this procedure's tilt and a little unrest.
    unrest = q_mul(q_axis_angle(X, 2.5 * contest * wobble), q_axis_angle(Y, 3.5 * contest * wobble))
    rotation = q_mul(q_align_z(layout.arm_axis(owner.side)), q_mul(owner.plane_tilt, unrest))

    # Flash as the cut is carried out, then stay as a dimmer record of it until the retreat.
    flash = pulse(t, cut_time - 0.15, cut_time, cut_time + 0.1, cut_time + 1.2)
    opacity = present * (0.6 + 0.3 * contest * wobble) + 0.5 * flare + 0.9 * flash
    opacity *= 1.0 - 0.45 * smooth_window(t, cut_time + 1.0, cut_time + 3.0)
    opacity *= 1.0 - smooth_window(t, cue.retreat_start, cue.retreat_end)

    return position, rotation, 1.0 + 0.12 * flash, opacity
