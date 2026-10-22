"""The station level at standing height, drawn. Its shape comes from ``core.refrain``.

Each built-out station gets what stands on its unit: an empty platform, an overhead yoke on two
posts, a head on a column with a rotor under it, and a carriage on a rail. Then the two surface
conditions: scrawls and bars. Everything is unlit, and so invisible, until the camera's sight
reaches it after 2:20.
"""

from ..core import climax, network, refrain
from ..core.vec import q_axis_angle, q_rotate
from . import materials as mat

_Z = (0.0, 0.0, 1.0)


def build(geo, root, opaque, energy, anim):
    for kit in refrain.kits():
        _station(geo, root, opaque, energy, anim, kit)
    tones = {"apron": refrain.APRON, "scrawl": refrain.SCRAWL, "bar": refrain.BAR}
    # Stations and marks added for the passage after 3:00 come last, and stay dark until then.
    for kit in refrain.later_kits():
        _station(geo, root, opaque, energy, anim, kit, arrives=network.arrival)
    for mark in refrain.marks():
        obj = geo.box("Mark" + mark.kind.capitalize(), root, mark.center, mark.size, opaque, (0.0, 0.0, 0.0))
        obj.rotation_quaternion = mark.rotation
        # Unseen, a mark is the colour of what it lies on: the ground of the level is not quite
        # black, a station's unlit face is.
        on_ground = mark.center[2] < refrain.GROUND_MARKS_BELOW
        _lit(anim, obj, tones[mark.kind], mark.center, unseen=refrain.GROUND_TONE if on_ground else (0.0, 0.0, 0.0))
        if on_ground:
            # Until 2:20 it lies just under the surface it will lie on, so that not even its
            # edges show in the hinge's last image.
            anim.add(obj, "location", lambda t, at=mark.center: at if t > refrain.START else (at[0], at[1], at[2] - 0.3))
    _later_marks(geo, root, opaque, anim, tones)


def _later_marks(geo, root, opaque, anim, tones):
    for mark in refrain.later_marks():
        obj = geo.box("Mark" + mark.kind.capitalize(), root, mark.center, mark.size, opaque, (0.0, 0.0, 0.0))
        obj.rotation_quaternion = mark.rotation
        _lit(anim, obj, tones[mark.kind], mark.center, level=network.arrival)


def _lit(anim, obj, tone, point, level=None, unseen=(0.0, 0.0, 0.0)):
    """The object shows its tone as far as the camera's sight has reached ``point``."""
    def color(t):
        k = refrain.seen(point, t) * (level(t) if level else 1.0)
        return tuple(u + (c - u) * k for u, c in zip(unseen, tone)) + (1.0,)
    obj.color = unseen + (1.0,)
    anim.add(obj, "color", color)


def _station(geo, root, opaque, energy, anim, kit, arrives=None):
    f, top = kit.front, refrain.TOP
    here = (kit.x, kit.y, top)
    name = "Station%03d" % kit.station
    frame = geo.empty(name, root, here)

    def part(obj, tone=refrain.MACHINE, level=None):
        if arrives is not None:
            own = level
            level = (lambda t: arrives(t) * own(t)) if own else arrives
        _lit(anim, obj, tone, here, level)
        return obj

    # The place for a subject. Nothing is ever on it.
    part(geo.cylinder("StationPlatform", frame, (0, 0, 0.125), 1.3, 0.25, opaque, (0, 0, 0)), refrain.PLATFORM)

    # Overhead: a yoke riding down two posts toward the platform.
    turns = kit.station in network.flanking()

    def turned(t):
        return q_axis_angle(_Z, network.gantry_yaw(kit, t))

    for side in (-1, 1):
        post = part(geo.cylinder("StationPost", frame, (0, side * 2.6, 2.2), 0.12, 4.4, opaque, (0, 0, 0)))
        if turns:
            anim.add(post, "location", lambda t, side=side: q_rotate(turned(t), (0.0, side * 2.6, 2.2)))
    beam = part(geo.box("StationBeam", frame, (0, 0, 4.4), (0.3, 5.5, 0.3), opaque, (0, 0, 0)))
    yoke = geo.empty("StationYoke", frame, (0, 0, refrain.YOKE_HEIGHT))
    if turns:
        # The whole overhead frame turns about the platform it stands over.
        anim.add(beam, "rotation_quaternion", turned)
        anim.add(yoke, "rotation_quaternion", turned)
    anim.add(yoke, "location", lambda t: (0.0, 0.0, refrain.YOKE_HEIGHT - refrain.yoke_drop(kit, t)))
    part(geo.box("StationYokeBar", yoke, (0, 0, 0), (0.5, 5.0, 0.2), opaque, (0, 0, 0)))
    part(geo.cylinder("StationYokeFace", yoke, (0, 0, -0.17), 1.0, 0.14, opaque, (0, 0, 0)), refrain.MACHINE_LIGHT)

    # A head on a column, with a rotor under it.
    hx, hy = f * refrain.HEAD_AT[0], refrain.HEAD_AT[1]
    column = part(geo.cylinder("StationColumn", frame, (hx, hy, refrain.HEAD_COLUMN * 0.5), 0.3, refrain.HEAD_COLUMN, opaque, (0, 0, 0)),
                  refrain.MACHINE_LIGHT)
    rotor = geo.empty("StationRotor", frame, (hx, hy, 1.15))
    anim.add(rotor, "rotation_quaternion", lambda t: q_axis_angle(_Z, refrain.rotor_angle(t) % 360.0))
    part(geo.box("StationBlade", rotor, (0, 0, 0), (1.7, 0.2, 0.07), opaque, (0, 0, 0)))
    part(geo.box("StationBlade", rotor, (0, 0, 0), (0.2, 1.7, 0.07), opaque, (0, 0, 0)))
    head = geo.empty("StationHead", frame, (hx, hy, refrain.HEAD_COLUMN))
    if climax.role(kit.station) == climax.DONOR:
        # A donor's whole head assembly travels along its edge of the platform, together.
        for obj, z in ((column, refrain.HEAD_COLUMN * 0.5), (rotor, 1.15), (head, refrain.HEAD_COLUMN)):
            anim.add(obj, "location", lambda t, z=z: (hx, hy + climax.donor_reach(kit, t), z))
    anim.add(head, "rotation_quaternion", lambda t: q_axis_angle(_Z, refrain.head_yaw(kit, t)))
    part(geo.box("StationHeadBlock", head, (0, 0, 0.225), (0.9, 0.9, 0.45), opaque, (0, 0, 0)))
    part(geo.box("StationHeadCell", head, (0, -0.47, 0.25), (0.55, 0.06, 0.15), energy, (0, 0, 0)), mat.ENERGY, refrain.coupling)

    # A carriage on a rail along one edge.
    part(geo.box("StationRail", frame, (0, refrain.RAIL_Y, 0.04), (7.0, 0.14, 0.08), opaque, (0, 0, 0)))
    carriage = part(geo.box("StationCarriage", frame, (f * refrain.CARRIAGE_HOME, refrain.RAIL_Y, 0.5), (0.8, 0.7, 1.0), opaque, (0, 0, 0)),
                    refrain.MACHINE_LIGHT)
    rest = tuple(carriage.scale)

    def location(t):
        run, extend = refrain.carriage(kit, t)
        return (f * (refrain.CARRIAGE_HOME + run), refrain.RAIL_Y, (1.0 + extend) * 0.5)

    anim.add(carriage, "location", location)
    anim.add(carriage, "scale", lambda t: (rest[0], rest[1], rest[2] * (1.0 + refrain.carriage(kit, t)[1])))
