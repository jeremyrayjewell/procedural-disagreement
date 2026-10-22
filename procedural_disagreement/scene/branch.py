"""The system branch: the disagreement leaving the body.

Until its cue there is one right-hand dependency: a conduit route, a tower, and the wall ribs
the route runs past. From the cue there are two. The second is built by the same code as the
first, from the same variant, so it starts exactly coincident and in the same state; it then
hinges away about the riser behind the figure's shoulder. Both share the figure and disagree
about where everything beyond it is.
"""

import math

from ..core import choreography as ch
from ..core import layout, variants
from . import reality


def build(geo, materials, anim, profile, seed):
    v = variants.system_branch()
    parts = reality.Parts(geo, materials.style(v), v, presence=ch.system_branch_presence)

    pivot = layout.SYSTEM_BRANCH_PIVOT
    hinge = geo.empty("SystemBranch", None, pivot)
    hinge.rotation_mode = "XYZ"
    anim.add(hinge, "rotation_euler", lambda t: (0.0, 0.0, math.radians(ch.system_branch_angle(t))))
    anim.add(hinge, "location", lambda t: (pivot[0], pivot[1], pivot[2] + ch.system_branch_lift(t)))
    # Collapsed to nothing until its cue, so it costs nothing to render before then.
    anim.add(hinge, "scale", lambda t: (1.0, 1.0, 1.0) if ch.system_branch_presence(t) > 0.0 else (0.0, 0.0, 0.0))

    # Everything below is placed in world coordinates, as the primary's is.
    world = geo.empty("SystemBranchWorld", hinge, tuple(-c for c in pivot))

    side = layout.SYSTEM_BRANCH_SIDE
    reality.build_dependency(parts, anim, profile, world, side, v.cut_time, seed)
    for y in layout.SYSTEM_BRANCH_RIBS_Y:
        parts.box("Rib", world, layout.rib_position(side, y), layout.RIB_SIZE, "structure")

    parts.register_colors(anim)
    return hinge
