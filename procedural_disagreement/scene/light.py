"""Light, as a factor on object colour.

The preview engine has no lamps to dim, and the film's opening and ending are mostly dark. So
light is carried where energy and translucency already are: in each object's colour. Every
object in the room takes the level ``core.outer.light`` gives for where it stands. Inside the
locked film that level is exactly 1 and colours pass through untouched.
"""

import bpy

from ..core import outer


def apply(anim, objects):
    """Puts every mesh in ``objects`` under the light. Objects that already animate their
    colour keep doing so; the light multiplies it."""
    bpy.context.view_layer.update()
    existing = {target.as_pointer(): index for index, (target, path, _) in enumerate(anim._channels)
                if path == "color"}
    for obj in objects:
        if obj.type != "MESH":
            continue
        weights = outer.zone_weights(tuple(obj.matrix_world.translation))
        index = existing.get(obj.as_pointer())
        if index is None:
            rest = tuple(obj.color)
            anim.add(obj, "color", _lit(lambda t, rest=rest: rest, weights))
        else:
            target, path, base = anim._channels[index]
            anim._channels[index] = (target, path, _lit(base, weights))


def _lit(base, weights):
    def color(t):
        value = base(t)
        level = outer.light(weights, t)
        if level >= 1.0:
            return value
        return (value[0] * level, value[1] * level, value[2] * level, value[3])
    return color
