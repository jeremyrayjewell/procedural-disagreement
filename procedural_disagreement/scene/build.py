"""Assembles the scene for a profile and bakes a frame range."""

import time

import bpy

from ..core import timeline, variants
from . import branch, chamber, coda, landfill, light, look, planes, reality, stage
from .animator import Animator
from .geo import Geo
from .materials import Materials


def build(profile, first_frame, last_frame, device="auto"):
    """Replaces the current file with the built scene, baked for first_frame..last_frame.

    The scene is constructed from code every time; no .blend is a source file.
    """
    started = time.time()
    _clear()
    scene = bpy.context.scene
    scene.name = "procedural-disagreement"

    geo = Geo(profile, scene.collection)
    materials = Materials()
    anim = Animator()

    realities = variants.for_profile(profile)
    chamber.build(geo, materials, anim, profile, timeline.SEED, phantom=realities[1])

    # Everything every profile has is built first and in the same order, so shared objects get
    # the same names in every profile; whatever a denser profile adds comes after.
    for variant in realities[:2]:
        reality.build(geo, materials, anim, profile, variant, timeline.SEED)
    # The planes argue between the first two realities.
    planes.build(geo, materials, anim, realities[0], realities[1])
    branch.build(geo, materials, anim, profile, timeline.SEED)
    for variant in realities[2:]:
        reality.build(geo, materials, anim, profile, variant, timeline.SEED)

    # Light is a factor on everything built so far: the room and all it contains.
    light.apply(anim, scene.collection.objects)

    landfill.build(geo, materials, anim, profile, timeline.SEED)
    # The coda's marks come last of all, so that nothing built before them is renamed.
    coda.build(geo, materials, anim)

    upper = stage.build_camera(geo, anim, scene)
    stage.build_lower_camera(geo, anim, scene, upper)
    stage.build_lighting(geo, scene)
    stage.build_atmosphere(geo, materials, profile)
    stage.apply_profile(scene, profile, device)
    # Presentation only, and only for profiles that ask for it.
    look.apply(geo, materials, anim, scene, profile)

    scene.frame_start = first_frame
    scene.frame_end = last_frame
    # One frame of margin either side so motion blur has something to sample.
    animated, constant = anim.bake(first_frame - 1, last_frame + 1)
    scene.frame_set(first_frame)   # also selects the camera for that frame, through the markers

    print("[pd] built '%s': %d objects, %d realities, %d animated channels (%d constant), %.1f s" % (
        profile.name, len(scene.objects), len(realities), animated, constant, time.time() - started))
    return scene


def _clear():
    """Empties the file's data without touching the window layout, so this works both in
    background renders and when the scene is built inside an open Blender."""
    for collection in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                       bpy.data.cameras, bpy.data.worlds, bpy.data.actions):
        for block in list(collection):
            collection.remove(block)
    bpy.context.scene.timeline_markers.clear()
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
