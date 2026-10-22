"""Camera, lights, atmosphere and render settings.

Camera and light placement are fixed. ``apply_profile`` is the only place a render profile
touches the scene's render settings.
"""

import math
import warnings

import bpy

from ..core import choreography as ch
from ..core import hinge, layout, outer, refrain, timeline
from ..core.vec import Z, q_camera_look, sub
from . import materials as mat

_SENSOR_HEIGHT = 24.0


def build_camera(geo, anim, scene):
    data = bpy.data.cameras.new("Camera")
    data.sensor_fit = "VERTICAL"
    data.sensor_height = _SENSOR_HEIGHT
    data.clip_start = 0.1
    data.clip_end = 100.0

    camera = bpy.data.objects.new("Camera", data)
    geo.collection.objects.link(camera)
    camera.rotation_mode = "QUATERNION"
    scene.camera = camera

    anim.add(camera, "location", lambda t: ch.camera_pose(t)[0])
    anim.add(camera, "rotation_quaternion", lambda t: ch.camera_pose(t)[1])
    # Field of view as focal length, which is what Blender animates.
    anim.add(data, "lens", lambda t: _SENSOR_HEIGHT * 0.5 / math.tan(math.radians(ch.camera_pose(t)[2]) * 0.5))
    return camera


def build_lower_camera(geo, anim, scene, upper):
    """The camera below the floor, and the cut to it.

    The cut is a timeline marker that switches the scene's active camera, not an animated jump
    of one camera: nothing is interpolated across it, so motion blur cannot smear it.
    """
    data = bpy.data.cameras.new("CameraLower")
    data.sensor_fit = "VERTICAL"
    data.sensor_height = _SENSOR_HEIGHT
    data.clip_start = 0.1
    data.clip_end = 400.0
    data.lens = _SENSOR_HEIGHT * 0.5 / math.tan(math.radians(layout.LOWER_CAMERA_FOV) * 0.5)

    camera = bpy.data.objects.new("CameraLower", data)
    geo.collection.objects.link(camera)
    camera.rotation_mode = "QUATERNION"
    anim.add(camera, "location", lambda t: ch.lower_camera_pose(t)[0])
    anim.add(camera, "rotation_quaternion", lambda t: ch.lower_camera_pose(t)[1])

    first = scene.timeline_markers.new("upper", frame=0)
    first.camera = upper
    cut = scene.timeline_markers.new("lower", frame=timeline.frame_of(timeline.LANDFILL_CUT))
    cut.camera = camera

    # The second hard cut: to a camera standing on the level above the pit. It does not move.
    still_data = bpy.data.cameras.new("CameraHinge")
    still_data.sensor_fit = "VERTICAL"
    still_data.sensor_height = _SENSOR_HEIGHT
    still_data.clip_start = 0.1
    still_data.clip_end = 400.0
    position, rotation, fov = hinge.still_camera()
    still_data.lens = _SENSOR_HEIGHT * 0.5 / math.tan(math.radians(fov) * 0.5)
    still = bpy.data.objects.new("CameraHinge", still_data)
    geo.collection.objects.link(still)
    still.rotation_mode = "QUATERNION"
    still.location = position
    still.rotation_quaternion = rotation
    # From 2:20 it travels.
    anim.add(still, "location", lambda t: refrain.camera_pose(t)[0])
    anim.add(still, "rotation_quaternion", lambda t: refrain.camera_pose(t)[1])
    second = scene.timeline_markers.new("hinge", frame=timeline.frame_of(hinge.CUT))
    second.camera = still

    # The third hard cut: back to the room, on the first frame after 4:15.0.
    room = scene.timeline_markers.new("room", frame=timeline.frame_of(outer.CODA_START) + 1)
    room.camera = upper
    # The ending is seen through the upper camera too.
    back = scene.timeline_markers.new("upper_again", frame=timeline.frame_of(outer.ENDING_START))
    back.camera = upper
    return camera


def build_lighting(geo, scene):
    """Two broad ceiling sources and the lamp over the figure. Used by EEVEE and Cycles;
    Workbench has its own fixed studio lighting."""
    y_mid = (layout.CHAMBER_Y_MAX + layout.CHAMBER_Y_MIN) * 0.5
    length = layout.CHAMBER_Y_MAX - layout.CHAMBER_Y_MIN
    for name, y in (("CeilingFront", y_mid - length * 0.25), ("CeilingBack", y_mid + length * 0.25)):
        data = bpy.data.lights.new(name, "AREA")
        data.shape = "RECTANGLE"
        data.size = layout.CHAMBER_HALF_WIDTH * 2.0 - 2.0
        data.size_y = length * 0.5 - 1.0
        data.energy = 1400.0
        data.color = (0.95, 0.98, 1.0)
        _add_light(geo, name, data, (0.0, y, layout.CHAMBER_HEIGHT - 0.15), (0.0, 0.0, -1.0))

    data = bpy.data.lights.new("Lamp", "SPOT")
    data.energy = 900.0
    data.spot_size = math.radians(75.0)
    data.spot_blend = 0.4
    data.shadow_soft_size = 0.4
    data.color = (1.0, 0.95, 0.88)
    position = (0.0, -0.6, 5.95)
    _add_light(geo, "Lamp", data, position, sub((0.0, 0.0, 2.4), position))

    # The pit below has one source: under its ceiling, over the heap our chute feeds. Workbench
    # ignores it; it is for the engines that light. Untested at final quality.
    data = bpy.data.lights.new("PitLamp", "AREA")
    data.shape = "RECTANGLE"
    data.size = 16.0
    data.size_y = 16.0
    data.energy = 60000.0
    data.color = (0.95, 0.98, 1.0)
    stop = (layout.FLOOR_CHANNEL_X, layout.RECEIVER_POSITION[1] + layout.DISPOSAL_ROUTE[1], -1.2)
    _add_light(geo, "PitLamp", data, stop, (0.0, 0.0, -1.0))

    world = bpy.data.worlds.new("World")
    if world.node_tree is None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = mat.FOG + (1.0,)
        background.inputs["Strength"].default_value = 0.08
    world.color = mat.FOG
    scene.world = world


def _add_light(geo, name, data, location, direction):
    light = bpy.data.objects.new(name, data)
    geo.collection.objects.link(light)
    light.location = location
    light.rotation_mode = "QUATERNION"
    # Lights, like cameras, point down their local -Z.
    up = (0.0, 1.0, 0.0) if abs(direction[2]) > 0.99 * math.sqrt(sum(c * c for c in direction)) else Z
    light.rotation_quaternion = q_camera_look(direction, up)
    return light


def build_atmosphere(geo, materials, profile):
    """A thin haze filling the room. Only profiles that can afford volumetrics get one."""
    if profile.volumetric_density <= 0.0:
        return None
    y_mid = (layout.CHAMBER_Y_MAX + layout.CHAMBER_Y_MIN) * 0.5
    length = layout.CHAMBER_Y_MAX - layout.CHAMBER_Y_MIN
    size = (layout.CHAMBER_HALF_WIDTH * 2.0 - 0.05, length - 0.05, layout.CHAMBER_HEIGHT - 0.05)
    haze = bpy.data.objects.new("Haze", geo._box_mesh(size))
    geo.collection.objects.link(haze)
    haze.location = (0.0, y_mid, layout.CHAMBER_HEIGHT * 0.5)
    haze.active_material = materials.volume(profile.volumetric_density)
    haze.display_type = "WIRE"
    haze.visible_shadow = False
    return haze


def apply_profile(scene, profile, device="auto"):
    render = scene.render
    render.engine = profile.engine
    render.resolution_x = profile.width
    render.resolution_y = profile.height
    render.resolution_percentage = 100
    render.fps = timeline.FPS
    render.fps_base = 1.0
    render.image_settings.file_format = "PNG"
    render.image_settings.color_mode = "RGB"
    # Lossless either way: 50% writes files about 11% smaller than Blender's default 15% for about
    # a tenth of a second more a 4K frame; 90% would save twice that at 17 s a frame (2026-10-22).
    render.image_settings.compression = 50
    render.use_file_extension = True
    render.film_transparent = False
    render.use_motion_blur = profile.motion_blur

    # Reproducible files: no random dither on 8-bit output, and no date, host or render-time
    # metadata in the image, so the same frame rendered twice is the same file.
    render.dither_intensity = 0.0
    for name in dir(render):
        if name.startswith("use_stamp_"):
            setattr(render, name, False)

    # Same display transform everywhere, so profiles agree on tone.
    for transform in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = transform
            break
        except TypeError:
            continue

    if profile.engine == "BLENDER_WORKBENCH":
        shading = scene.display.shading
        shading.light = "STUDIO"
        shading.color_type = "OBJECT"      # object colour and alpha: energy and translucency
        shading.show_cavity = True
        shading.cavity_type = "BOTH"
        shading.show_object_outline = False
        shading.show_specular_highlight = False
        # Workbench shadows come from one infinite light and the ceiling would shadow the whole room.
        shading.show_shadows = False
        shading.background_type = "VIEWPORT"
        shading.background_color = mat.FOG
        scene.display.render_aa = "5" if profile.samples >= 5 else "FXAA"
    elif profile.engine == "BLENDER_EEVEE":
        scene.eevee.taa_render_samples = profile.samples
        scene.eevee.use_shadows = True
        scene.eevee.use_raytracing = False
        scene.eevee.volumetric_samples = 32
    elif profile.engine == "CYCLES":
        cycles = scene.cycles
        cycles.samples = profile.samples
        cycles.use_denoising = profile.denoise
        cycles.use_adaptive_sampling = True
        cycles.volume_bounces = 1 if profile.volumetric_density > 0.0 else 0
        cycles.device = "GPU" if _enable_gpu(device) else "CPU"
        render.use_persistent_data = True
    else:
        raise ValueError("Unknown render engine %r" % profile.engine)


def _enable_gpu(device):
    """Selects the best available Cycles GPU backend. Returns False if rendering must use the CPU."""
    if device == "cpu":
        return False
    try:
        preferences = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return False
    backends = ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI") if device == "auto" else (device.upper(),)
    for backend in backends:
        try:
            preferences.compute_device_type = backend
        except TypeError:
            continue
        preferences.refresh_devices()
        gpus = [d for d in preferences.devices if d.type != "CPU"]
        if gpus:
            for d in preferences.devices:
                d.use = d.type != "CPU"
            print("[pd] Cycles device: %s (%s)" % (backend, ", ".join(d.name for d in gpus)))
            return True
    print("[pd] WARNING: no supported GPU found for Cycles; rendering on the CPU.")
    return False
