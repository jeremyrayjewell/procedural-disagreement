"""procedural-disagreement: a deterministic, pre-rendered procedural music video.

``core``  -- timing, variants, layout and choreography as pure functions of absolute
             track time. No Blender imports; runs under any Python.
``scene`` -- builds the Blender scene from ``core`` and bakes the choreography to keyframes.
"""
