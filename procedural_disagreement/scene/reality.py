"""One complete version of events: a figure, its dependent infrastructure and the procedure
performed on it. The primary reality is solid; alternates are built by this same code from a
different ProcedureVariant and a translucent style."""

import math

from ..core import choreography as ch
from ..core import layout, outer
from ..core.vec import add, q_axis_angle, q_mul, q_rotate

S = layout.FIGURE_SCALE


class Parts:
    """Creates the parts of one reality in its style and remembers which ones carry energy."""

    def __init__(self, geo, style, variant, presence=None):
        self.geo = geo
        self.style = style
        self.variant = variant
        #: 0..1 fade of the whole group, for translucent styles.
        self.presence = presence or (lambda t: ch.presence(variant, t))
        #: (object, role, energy function of t or None)
        self.tracked = []

    def box(self, name, parent, center, size, role, energy=None):
        obj = self.geo.box(name, parent, center, size, self.style.material(role), self.style.color(role))
        return self._track(obj, role, energy)

    def cylinder(self, name, parent, center, radius, height, role, energy=None):
        obj = self.geo.cylinder(name, parent, center, radius, height, self.style.material(role), self.style.color(role))
        return self._track(obj, role, energy)

    def sphere(self, name, parent, center, diameter, role, energy=None):
        obj = self.geo.sphere(name, parent, center, diameter, self.style.material(role), self.style.color(role))
        return self._track(obj, role, energy)

    def _track(self, obj, role, energy):
        if self.variant.ghost:
            # Translucent shells should not darken the solid reality.
            obj.visible_shadow = False
        self.tracked.append((obj, role, energy))
        return obj

    def register_colors(self, anim):
        """Energy and (for alternates) the reality's fade both travel in the object colour."""
        v, style = self.variant, self.style
        for obj, role, energy in self.tracked:
            if not v.ghost and energy is None:
                continue

            def color(t, role=role, energy=energy):
                level = energy(t) if energy else 1.0
                opacity = v.ghost_opacity * self.presence(t) if v.ghost else 1.0
                return style.color(role, level, opacity)

            anim.add(obj, "color", color)


def build(geo, materials, anim, profile, variant, seed):
    v = variant
    parts = Parts(geo, materials.style(v), v)
    root = geo.empty("Reality_" + v.name)

    if v.ghost:
        anim.add(root, "location", lambda t: ch.reality_offset(v, t))
        # Collapsed to nothing until it starts to split off, so it costs nothing to render.
        anim.add(root, "scale", lambda t: (1.0, 1.0, 1.0) if ch.presence(v, t) > 1e-4 else (0.0, 0.0, 0.0))

    _build_figure(parts, anim, profile, root)
    build_dependency(parts, anim, profile, root, v.side, v.cut_time, seed)
    if v.include_idle_dependencies:
        # The opposite arm keeps its own tower running throughout: the control case.
        build_dependency(parts, anim, profile, root, -v.side, ch.NEVER, seed)
    if v.include_receiver:
        _build_receiver(parts, anim, root)

    parts.register_colors(anim)
    return root


# ---------------------------------------------------------------- figure


def _build_figure(parts, anim, profile, root):
    v = parts.variant
    core = parts.geo.empty("Figure", root)

    def at(p):
        return layout.fig(p)

    def size(x, y, z):
        return (x * S, y * S, z * S)

    pelvis = parts.box("Pelvis", core, at((0, 0, 1.06)), size(0.40, 0.24, 0.16), "body")
    # The body is the subject. The risers and conduits that served it are apparatus and stay.
    subject = [pelvis]

    # Everything above the pelvis hangs from one pivot at the base of the torso, so the torso
    # can compensate as a whole. Positions below are still written in the reality's space.
    torso = parts.geo.empty("Torso", core, layout.TORSO_PIVOT)
    subject.append(torso)
    if v.phantom:
        anim.add(torso, "rotation_quaternion", lambda t: ch.torso_compensation(v, t))

    def on_torso(p):
        return tuple(a - b for a, b in zip(p, layout.TORSO_PIVOT))

    # Torso: stacked slabs, widening toward the shoulders, slowly ventilating.
    for i, width in enumerate(layout.TORSO_SLAB_WIDTHS):
        slab = parts.box("TorsoSlab", torso, on_torso(at((0, 0, 1.2025 + i * 0.097))), size(width, 0.22 + i * 0.01, 0.085), "body")
        rest = tuple(slab.scale)
        anim.add(slab, "scale", lambda t, i=i, rest=rest: (rest[0] * ch.breath(i, t), rest[1] * ch.breath(i, t), rest[2]))

    # Machine parts on the back.
    parts.cylinder("Spine", torso, on_torso(at((0, 0.14, 1.38))), 0.035 * S, 0.60 * S, "joint")
    for side in (-1, 1):
        parts.cylinder("Tank", torso, on_torso(at((side * 0.20, 0.13, 1.25))), 0.05 * S, 0.25 * S, "structure")

    # Risers: the body is plumbed into the room through the overhead lamp.
    riser_bottom = at((0, 0, 1.5))[2]
    riser_top = layout.LAMP_UNDERSIDE
    for side in (-1, 1):
        x, y, _ = at((side * 0.09, 0.16, 0))
        parts.cylinder("Riser", core, (x, y, (riser_bottom + riser_top) * 0.5), 0.022 * S, riser_top - riser_bottom, "structure")

    # Head: featureless block with a dark sensor band.
    parts.cylinder("Neck", torso, on_torso(at((0, 0, 1.69))), 0.05 * S, 0.08 * S, "joint")
    parts.box("Head", torso, on_torso(at((0, 0, 1.85))), size(0.19, 0.21, 0.24), "body")
    parts.box("SensorBand", torso, on_torso(at((0, -0.10, 1.87))), size(0.15, 0.03, 0.07), "joint")

    for side in (-1, 1):
        cut_index = v.cut_index if side == v.side else None
        detached, stump, _ = _build_limb(parts, profile, torso, "Arm", on_torso(layout.arm_origin(side)),
                                      layout.arm_rotation(side), layout.ARM_MODULES, cut_index)
        if stump is not None:
            anim.add(stump, "rotation_quaternion", lambda t: ch.stump_pose(v, t))
            if v.phantom:
                # During recruitment the shoulder turns about its socket, a little inboard of
                # the ball: the stump's pivot shifts and the ball swings with it.
                anim.add(stump, "location", lambda t: ch.stump_shift(v, t))
                ball = _shoulder_ball(stump)
                rest = tuple(ball.location)
                anim.add(ball, "location", lambda t, rest=rest: ch.socket_swing(v, rest, t))
        if detached is not None:
            rest = tuple(detached.location)
            anim.add(detached, "location", lambda t, rest=rest: tuple(r + o for r, o in zip(rest, ch.detach_pose(v, t)[0])))
            anim.add(detached, "rotation_quaternion", lambda t: ch.detach_pose(v, t)[1])
        subject.append(_build_limb(parts, profile, core, "Leg", layout.leg_origin(side), None, layout.LEG_MODULES, None)[2])

    if not v.ghost:
        for obj in subject:
            rest = tuple(obj.scale)
            anim.add(obj, "scale", lambda t, rest=rest: tuple(c * outer.subject_presence(t) for c in rest))


def _shoulder_ball(stump):
    """The limb's first module, the joint ball, which sits beside the stump under the limb."""
    for child in stump.parent.children:
        if child.type == "MESH" and child.name.startswith("Joint"):
            return child
    raise ValueError("Limb %s has no shoulder joint" % stump.parent.name)


def _build_limb(parts, profile, parent, name, origin, rotation, modules, cut_index):
    """A stack of modules hanging along the limb root's local -Z.

    If ``cut_index`` is given, modules at or beyond it are grouped under a pivot placed at the
    cut: detaching the region is then the pose of one object. Modules left between the joint
    and the cut are grouped under a second pivot at the joint, the stump. Returns
    (detached pivot, stump pivot); either may be None.
    """
    geo = parts.geo
    limb = geo.empty(name, parent, origin, rotation)
    detached, stump, pivot_z = None, None, 0.0
    if cut_index is not None:
        pivot_z = -layout.boundary_distance(modules, cut_index)
        detached = geo.empty(name + "Detached", limb, (0.0, 0.0, pivot_z))
        if cut_index > 1:
            stump = geo.empty(name + "Stump", limb)

    tops = layout.module_tops(modules)
    for index, module in enumerate(modules):
        beyond_cut = detached is not None and index >= cut_index
        # Module 0 is the joint itself and never moves.
        group = detached if beyond_cut else stump if (stump is not None and index >= 1) else limb
        shift = -pivot_z if beyond_cut else 0.0

        # Dense profiles split each slice into thinner fragments within the same envelope.
        pieces = 1 if module.ball else profile.slice_subdivisions
        gap = layout.MODULE_GAP * 0.6
        piece_length = (module.length - gap * (pieces - 1)) / pieces
        for piece in range(pieces):
            along = tops[index] + piece * (piece_length + gap) + piece_length * 0.5
            center = (module.offset[0] * S, module.offset[1] * S, -along * S + shift)
            if module.ball:
                parts.sphere("Joint", group, center, module.width * S, "joint")
            else:
                parts.box("Slice", group, center, (module.width * S, module.depth * S, piece_length * S), "body")
    return detached, stump, limb


# ---------------------------------------------------------------- dependency: region -> conduit -> tower


def build_dependency(parts, anim, profile, root, side, sever_time, seed):
    """Remote infrastructure kept alive by one arm. Severing that arm is the only thing that
    can make it fail; ``sever_time`` is ch.NEVER for a dependency that stays intact."""
    v = parts.variant
    fail_time = sever_time + v.signal_travel
    tower_seed = seed + (1 if side > 0 else 2)

    _build_conduit(parts, anim, profile, root, layout.conduit_path(side), sever_time, pulled=v.phantom and side == v.side,
                   opens=side if not v.ghost else 0)

    tower = parts.geo.empty("Tower", root, layout.tower_position(side))
    if v.phantom and side == v.side:
        # Pivot at its foot: the tower braces against the phantom load.
        anim.add(tower, "rotation_quaternion", lambda t: ch.tower_lean(v, t))
    parts.box("Base", tower, (0, 0, 0.25), (1.4, 1.4, 0.5), "structure")
    parts.cylinder("Column", tower, (0, 0, 2.1), 0.32, 3.2, "body")

    # Rotor: six blades so the rotation, and its stopping, reads at a distance.
    rotor = parts.geo.empty("Rotor", tower, (0, 0, layout.TOWER_ROTOR_HEIGHT))
    rotor.rotation_mode = "XYZ"
    anim.add(rotor, "rotation_euler", lambda t: (0.0, 0.0, math.radians(ch.rotor_angle(v, t, fail_time))))
    parts.cylinder("Hub", rotor, (0, 0, 0), 0.5, 0.12, "joint")
    for i in range(6):
        arm = parts.geo.empty("BladeArm", rotor, rotation=q_axis_angle((0.0, 0.0, 1.0), i * 60.0))
        parts.box("Blade", arm, (0.85, 0, 0), (0.9, 0.22, 0.08), "structure")

    # Indicator cells face the camera. Index 0 is the top cell and the first to be lost.
    for i in range(layout.TOWER_CELLS):
        parts.box("Cell", tower, (0, -0.36, 2.4 - i * 0.3), (0.30, 0.08, 0.22), "cell",
                  energy=lambda t, i=i: ch.cell_energy(v, i, t, fail_time, tower_seed))

    # Head: the part that separates. Its pivot is at its base so it can tilt over.
    head = parts.geo.empty("Head", tower, (0, 0, layout.TOWER_HEAD_HEIGHT))
    if v.reindexed and side == v.side:
        # Left as the failure put it, until the room re-indexes it.
        anim.add(head, "location", lambda t: (0.0, 0.0, layout.TOWER_HEAD_HEIGHT + ch.reindex_head(v, t, fail_time)[0][2]))
        anim.add(head, "rotation_quaternion", lambda t: ch.reindex_head(v, t, fail_time)[1])
    else:
        _fallen_head(anim, head, v, side, fail_time)
    parts.box("HeadBlock", head, (0, 0, 0.3), (1.0, 1.0, 0.5), "structure")
    parts.cylinder("HeadCap", head, (0, 0, 0.7), 0.25, 0.3, "body")
    parts.box("HeadCell", head, (0, -0.52, 0.3), (0.6, 0.06, 0.16), "cell",
              energy=lambda t: ch.head_cell_energy(t, fail_time))


def _fallen_head(anim, head, v, side, fail_time):
    anim.add(head, "location", lambda t: (0.0, 0.0, layout.TOWER_HEAD_HEIGHT + ch.head_pose(v, t, fail_time)[0][2]))
    if v.phantom and side == v.side:
        # Later, over its slump, this head turns to face the empty point.
        anim.add(head, "rotation_quaternion",
                 lambda t: q_mul(ch.tower_head_aim(v, t), ch.head_pose(v, t, fail_time)[1]))
    else:
        anim.add(head, "rotation_quaternion", lambda t: ch.head_pose(v, t, fail_time)[1])


def _build_conduit(parts, anim, profile, root, path, sever_time, pulled=False, opens=0):
    """A segmented duct along a polyline. Each segment's energy is the conduit's energy at its
    arc position, so segment count (a profile choice) does not change what the pulses do.
    A ``pulled`` conduit is also displaced, point by point, by the phantom load."""
    v = parts.variant
    thickness = 0.09
    conduit = parts.geo.empty("Conduit", root)

    legs = [(a, b, math.dist(a, b)) for a, b in zip(path, path[1:])]
    total = sum(leg[2] for leg in legs)

    travelled = 0.0
    for leg_index, (a, b, leg_length) in enumerate(legs):
        # Every leg of the route runs along a world axis.
        axis = max(range(3), key=lambda k: abs(b[k] - a[k]))
        count = max(1, int(leg_length / profile.conduit_pitch))
        step = leg_length / count
        for s in range(count):
            along = (s + 0.5) * step
            center = tuple(a[k] + (b[k] - a[k]) * along / leg_length for k in range(3))
            size = [thickness] * 3
            size[axis] = step * 0.82
            u = (travelled + along) / total
            segment = parts.box("Segment", conduit, center, tuple(size), "conduit",
                                energy=lambda t, u=u: ch.conduit_energy(u, t, sever_time, v.signal_travel))
            if pulled and leg_index == 0:
                _pull_and_aim(anim, segment, center, u, v, path[1])
            elif opens and leg_index == 0:
                _swing_open(anim, segment, center, path[1], opens)
            elif pulled:
                _pull(anim, segment, center, u, v)
        travelled += leg_length
        if leg_index < len(legs) - 1:
            elbow = parts.box("Elbow", conduit, b, (thickness * 1.6,) * 3, "structure")
            if pulled:
                _pull(anim, elbow, b, travelled / total, v)


def _pull_and_aim(anim, obj, rest, u, variant, corner):
    """The conduit's last run: displaced by the phantom load like the rest, and later turned,
    as a whole, about the corner it hangs from."""
    def pulled(t):
        return tuple(r + d - c for r, d, c in zip(rest, ch.conduit_displacement(variant, u, t), corner))

    anim.add(obj, "location", lambda t: add(corner, q_rotate(ch.conduit_end_aim(variant, t), pulled(t))))
    anim.add(obj, "rotation_quaternion", lambda t: ch.conduit_end_aim(variant, t))


def _swing_open(anim, obj, rest, corner, side):
    """The conduit's last run, before the system couples: swung away from the shoulder about
    the corner it hangs from. ``side`` gives the direction: outward."""
    arm = tuple(r - c for r, c in zip(rest, corner))

    def turn(t):
        return q_axis_angle((0.0, 0.0, 1.0), side * outer.conduit_open(t))

    anim.add(obj, "location", lambda t: add(corner, q_rotate(turn(t), arm)))
    anim.add(obj, "rotation_quaternion", turn)


def _pull(anim, obj, rest, u, variant):
    anim.add(obj, "location", lambda t: tuple(r + d for r, d in zip(rest, ch.conduit_displacement(variant, u, t))))


def _build_receiver(parts, anim, root):
    """The tray that collects the removed arm. Later it turns out to be a carriage."""
    receiver = parts.geo.empty("Receiver", root, layout.RECEIVER_POSITION)
    anim.add(receiver, "location", lambda t: add(layout.RECEIVER_POSITION, ch.receiver_offset(t)))
    parts.cylinder("Foot", receiver, (0, 0, 0.03), 0.35, 0.06, "structure")
    parts.cylinder("Post", receiver, (0, 0, 0.64), 0.08, 1.28, "structure")
    parts.box("Tray", receiver, (0, 0, 1.31), (1.7, 0.55, 0.06), "joint")
