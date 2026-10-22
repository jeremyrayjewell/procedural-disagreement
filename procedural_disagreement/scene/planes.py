"""The two competing cutting planes.

Plane A belongs to the primary reality and plane B to the first alternate. Each tracks its own
reality's cut point, so when the alternate drifts away plane B goes with it.
"""

from ..core import choreography as ch
from ..core import layout
from . import materials as mat


def build(geo, materials, anim, primary, alternate):
    root = geo.empty("Disagreement")
    _build_plane(geo, materials, anim, root, "PlaneA", ch.PLANE_A, primary, alternate, mat.PLANE_A)
    _build_plane(geo, materials, anim, root, "PlaneB", ch.PLANE_B, alternate, primary, mat.PLANE_B)
    return root


def _build_plane(geo, materials, anim, root, name, cue, owner, rival, color):
    def pose(t):
        return ch.plane_pose(cue, owner, rival, t)

    pivot = geo.empty(name, root)
    anim.add(pivot, "location", lambda t: pose(t)[0])
    anim.add(pivot, "rotation_quaternion", lambda t: pose(t)[1])
    anim.add(pivot, "scale", lambda t: (pose(t)[2],) * 3)

    size = layout.PLANE_SIZE
    sheet = geo.quad("Sheet", pivot, size, materials.plane, color)
    anim.add(sheet, "color", lambda t: color + (min(1.0, mat.PLANE_SHEET_ALPHA * pose(t)[3]),))

    # A stronger frame keeps the plane legible where the sheet is nearly edge-on.
    bar = 0.014
    half = size * 0.5
    for i, (center, dims) in enumerate((
        ((half, 0, 0), (bar, size, bar)),
        ((-half, 0, 0), (bar, size, bar)),
        ((0, half, 0), (size, bar, bar)),
        ((0, -half, 0), (size, bar, bar)),
    )):
        edge = geo.box("Edge", pivot, center, dims, materials.plane, color)
        anim.add(edge, "color", lambda t: color + (min(1.0, 0.95 * pose(t)[3]),))
        edge.visible_shadow = False
    sheet.visible_shadow = False
