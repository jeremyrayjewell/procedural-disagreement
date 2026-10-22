"""The coda's marks, drawn. What they are and when they are there comes from ``core.coda``.

They are built after everything else, so nothing that existed before is renamed, and they are
not under the room's light: a mark's tone is its own. Outside the coda every one of them has no
size at all.
"""

from ..core import coda, outer
from . import materials as mat


def build(geo, materials, anim):
    root = geo.empty("Coda")
    for mark in coda.marks():
        obj = geo.box("Coda" + mark.kind.capitalize(), root, mark.center, mark.size, materials.opaque, (0.0, 0.0, 0.0))
        obj.rotation_quaternion = mark.rotation
        obj.scale = (0.0, 0.0, 0.0)
        anim.add(obj, "location", lambda t, mark=mark: coda.pose(mark, t)[0])
        anim.add(obj, "scale", lambda t, mark=mark: coda.pose(mark, t)[1])
        # Its tone comes up out of the tone of what it is on, as that surface is lit just then.
        surface = mat.FLOOR if mark.surface == "floor" else mat.FIXTURE
        tone = coda.SCRAWL if mark.kind == "scrawl" else coda.BAR

        def color(t, mark=mark, surface=surface, tone=tone):
            k, lit = coda.pose(mark, t)[2], outer.room_light(t)
            return tuple(u * lit + (c - u * lit) * k for u, c in zip(surface, tone)) + (1.0,)

        anim.add(obj, "color", color)
    return root
