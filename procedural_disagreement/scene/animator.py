"""Turns functions of time into keyframes.

Builders register channels: "this property of this datablock follows this function of t".
``bake`` samples every channel once per frame and writes the result as linear keyframes, so the
built scene is an ordinary, self-contained .blend: it scrubs in the viewport and renders
anywhere without running any Python. Channels that never change are set once and get no curve.
"""

import bpy

from ..core import timeline

_LINEAR = 1  # enum value of Keyframe.interpolation 'LINEAR'


class Animator:
    def __init__(self):
        self._channels = []
        self._fcurve_collections = {}

    def add(self, target, path, fn):
        """``target.path`` follows ``fn(t)``, which returns a float or a tuple of floats."""
        self._channels.append((target, path, fn))

    def bake(self, first_frame, last_frame):
        """Samples frames first..last inclusive. Returns (animated, constant) channel counts."""
        frames = list(range(first_frame, last_frame + 1))
        times = [timeline.time_of(f) for f in frames]
        animated = constant = 0

        for target, path, fn in self._channels:
            samples = [_as_tuple(fn(t)) for t in times]
            if path == "rotation_quaternion":
                _make_continuous(samples)

            if all(s == samples[0] for s in samples):
                value = samples[0]
                if path.startswith('["'):
                    # A custom property, by name.
                    target[path[2:-2]] = value[0]
                    constant += 1
                    continue
                try:
                    setattr(target, path, value[0] if len(value) == 1 else value)
                except TypeError:
                    # An on/off property: it takes a truth value, not a number.
                    setattr(target, path, bool(value[0]))
                constant += 1
                continue

            fcurves = self._fcurves_for(target)
            for index in range(len(samples[0])):
                fcurve = fcurves.new(path, index=index)
                points = fcurve.keyframe_points
                points.add(len(frames))
                co = [0.0] * (2 * len(frames))
                co[0::2] = frames
                co[1::2] = [s[index] for s in samples]
                points.foreach_set("co", co)
                points.foreach_set("interpolation", [_LINEAR] * len(frames))
                fcurve.update()
            animated += 1

        return animated, constant

    def _fcurves_for(self, target):
        """One action per datablock, created on first use."""
        key = target.as_pointer()
        fcurves = self._fcurve_collections.get(key)
        if fcurves is not None:
            return fcurves

        action = bpy.data.actions.new("PD_" + target.name)
        animation = target.animation_data_create()
        animation.action = action
        if hasattr(action, "slots"):
            # Blender 4.4+: actions are layered and slotted.
            slot = action.slots.new(id_type=target.id_type, name=target.name)
            animation.action_slot = slot
            strip = action.layers.new("Bake").strips.new(type="KEYFRAME")
            fcurves = strip.channelbag(slot, ensure=True).fcurves
        else:
            fcurves = action.fcurves
        self._fcurve_collections[key] = fcurves
        return fcurves


def _as_tuple(value):
    if isinstance(value, (int, float)):
        return (float(value),)
    return tuple(float(v) for v in value)


def _make_continuous(quaternions):
    """q and -q are the same rotation; keep consecutive samples in the same hemisphere so
    interpolation between frames never takes the long way round."""
    for i in range(1, len(quaternions)):
        a, b = quaternions[i - 1], quaternions[i]
        if sum(x * y for x, y in zip(a, b)) < 0.0:
            quaternions[i] = tuple(-x for x in b)
