"""The look: materials, light and render settings for a lit engine. Presentation only.

Nothing here moves, scales, shows or hides anything, and nothing here touches an object's
colour: the film's darkness, energy and translucency are still carried there, exactly as in the
preview, so what can be seen and when is unchanged. This module only decides how a surface
answers light, and where the light comes from. It runs for profiles whose ``look`` is set and
does nothing at all for the others.

The film's darkness is a factor on object colour. A lit engine would still show a highlight on
a black object, which would reveal things the film keeps unseen, so every material ties its
specular response to its own colour: what the film has made dark answers no light at all.
"""

import math
import os

import bpy

from ..core import audio, climax, hinge, outer, refrain, timeline
from ..presentation import emission, glyphs, lyrics, screens
from ..core.ease import smoother, window
from ..core.vec import Z, q_camera_look

# (roughness, metallic, bevel radius in metres) for each class of surface. The differences are
# small on purpose: classes are told apart by how they take light, not by colour.
CLASSES = {
    "wall": (0.72, 0.0, 0.02),
    "floor": (0.50, 0.0, 0.015),
    # The rear wall's 15 panels: reserved for a later CRT / display treatment. Until then they
    # answer light exactly as the floor class does, but no room or floor texture may reach them.
    "display": (0.50, 0.0, 0.015),
    # The chamber's floor and the plinth's lower step: their own class so that a floor treatment
    # reaches nothing else (not the plinth top, trim, aprons, level ground or pit ceiling).
    "chamber_floor": (0.50, 0.0, 0.015),
    # The room's pale fixtures that move: the wall cabinets and carriages and the lamp housing. The
    # machinery class's values; their own class so that a fixture treatment reaches nothing else.
    "fixture": (0.34, 0.60, 0.008),
    "trunk": (0.46, 0.55, 0.04),        # routing: restrained metal
    "via": (0.46, 0.55, 0.04),          # junction blocks: the same metal
    "fine": (0.46, 0.55, 0.04),         # fine runs: the same metal
    "main": (0.36, 0.65, 0.05),         # heavier routing: a little brighter in the highlight
    "station": (0.40, 0.0, 0.05),       # station bodies: dark, smooth, not metal
    "machinery": (0.34, 0.60, 0.008),   # what moves
    "kit": (0.34, 0.60, 0.008),         # station machinery: the same, but see UNREVEALED below
    "kit_floor": (0.50, 0.0, 0.015),    # a station's platform: floor, and likewise
    "debris": (0.90, 0.0, 0.0),
    "waste": (0.90, 0.0, 0.0),          # the continuous waste ground: the debris class's values
    "pit": (0.90, 0.0, 0.0),            # the pit's near-black floor and walls: likewise
    "body": (0.52, 0.0, 0.0),
    "body_shell": (0.52, 0.0, 0.0),
    "apron": (0.50, 0.0, 0.015),        # the level's mark aprons: the floor class's values
    "echo": (0.40, 0.0, 0.05),          # the pull-out's distant copies of the network (look only)     # the figure's pale shell: the body class's values           # the same family as the room's fixtures, a little softer
    "bar": (0.28, 0.35, 0.0),           # applied modules: smoother and a little metallic, still pale
}

_PREFIXES = (
    ("bar", ("MarkBar", "CodaBar")),
    ("main", ("LevelMain",)),
    ("trunk", ("LevelTrunk",)),
    ("via", ("LevelVia",)),
    ("fine", ("LevelFine",)),
    ("kit_floor", ("StationPlatform",)),
    ("display", ("Panel",)),
    ("chamber_floor", ("Floor", "PlinthStep")),
    ("apron", ("MarkApron",)),
    ("fixture", ("Cabinet", "LampBody")),
    ("floor", ("LevelGround", "MarkApron", "Floor", "Plinth", "PitCeiling", "Channel",
               "Aperture", "Band")),
    ("station", ("LevelUnit", "LevelBay", "LevelCell", "LevelSpur")),
    ("kit", ("Station",)),
    ("machinery", ("Cabinet", "Lamp", "Tray", "Receiver", "Rotor", "Blade", "HeadBlock", "Base", "Tower")),
    ("waste", ("Waste",)),
    ("pit", ("PitFloor", "PitWall")),
    ("debris", ("Refuse", "Strat", "Discarded", "Disposed", "Chute")),
)


#: The figure's pale shell, as distinct from its joints and its dark structure. (Only the solid
#: figure: the ghost copies have the translucent ghost material, which the look never touches.)
BODY_SHELL = ("Pelvis", "TorsoSlab", "Head", "Slice")


#: A scrawl is drawn as a run of thin boxes. Which way such a box lies decides which of its own
#: axes points out of the surface it is on, and which runs across the trace:
#: {class: (index of the axis out of the surface, index of the axis across the trace)}.
SCRAWLS = {"scrawl_face": (0, 2), "scrawl_wall": (1, 2), "scrawl_flat": (2, 1)}


def _scrawl_kind(obj):
    """Which way a scrawl's boxes lie: on a station's upright face, on the rear wall, or flat."""
    if obj.name.startswith("Coda"):
        # The coda's marks have no size until they are there; where they are says which they are.
        return "scrawl_flat" if obj.location[2] < 0.1 else "scrawl_wall"
    thin = min(range(3), key=lambda i: obj.scale[i])
    return "scrawl_face" if thin == 0 else "scrawl_flat"


def classify(obj):
    """Which class of surface an object is, from what it is called and what it belongs to."""
    name = obj.name.split(".")[0]
    if name in ("MarkScrawl", "CodaScrawl"):
        return _scrawl_kind(obj)
    for kind, prefixes in _PREFIXES:
        if name.startswith(prefixes):
            return kind
    parent = obj.parent
    while parent is not None:
        if parent.name.startswith("Figure"):
            return "body_shell" if name.startswith(BODY_SHELL) else "body"
        parent = parent.parent
    return "wall"


#: Network emission. The names of the per-object values that carry a piece's response and, for
#: the two runs that cross at the junction, the source; the colour of a response (the film's
#: own cold accent, paler); and, for runs, how it is laid into the metal: as short inlays, never
#: as a lit line.
GLOW = "pd_glow"
SOURCE = "pd_source"
DIM = "pd_dim"
#: For a run the lane cut: where along it the cut is, and which side of it the run lies (+1 or
#: -1; 0 for every other run). Its inlays stop short of the cut.
CUT_AT = "pd_cut_at"
CUT_SIDE = "pd_cut_side"
#: For a trunk or main in the climax: how far its coupling and its saturation inlays have been
#: admitted, 0..1. Absent, and so nothing, everywhere else and before 4:00.
DENSE = ("pd_dense_coupling", "pd_dense_saturation")
#: Where, within one period of a run's own spacing, its added inlays may start: each period
#: picks its own place, from a hash of (run, tier, period), so the added marks are irregular
#: along a run and not only from run to run. The original inlay stands at the start of each
#: period and is never moved. Bounds, in metres from the start of the period, for a period p:
#: the coupling mark starts in [DENSE_GAP + length, 0.45 p]; the saturation mark in
#: [0.45 p + length + DENSE_GAP, p - length - DENSE_GAP]. So no two marks are ever closer than
#: DENSE_GAP, edge to edge, and the spacing stays about a half, then a third, of the period.
DENSE_GAP = 0.6
DENSE_SPLIT = 0.45
#: Across a run, an added mark's centre may stand off the centre line by up to this share of the
#: width it could use (the run's width less the mark's), half to either side: within the middle
#: 55% of that width. Each added mark gets its own, from a hash of (run, tier, period): some
#: left, some right, some near the middle, never at the edge and never alternating. The
#: original marks stay on the centre line.
DENSE_ACROSS = 0.55
#: The width of the run a piece is, in metres, for the added marks to stay on it.
RUN_WIDTH = "pd_run_width"
GLOW_COLOR = (0.30, 0.72, 1.0)
#: An inlay's length in metres, and the range its spacing is drawn from. Each run has its own
#: spacing and its own offset, fixed by which run it is: instruments set where each was needed,
#: not marks painted at a pitch.
GLOW_INLAY = (0.9, 6.0, 11.0)
#: Classes of the level that can carry a response, and the axis a run of that class lies along.
#: A junction block carries a small inset in the middle of its top instead.
GLOWING = {"trunk": "y", "main": "x", "fine": "xy", "via": ""}
#: How much of a run's width an inlay takes; how much of a junction block's top its inset takes
#: (as a side: 0.5 is a quarter of the area); and the overall gain on every response.
GLOW_WIDTH = 0.3
#: An inlay's width in metres, by class of run. It is a size, not a share of the run: a heavy run
#: carries the same instrument as an ordinary one, and it does not grow with the metal round it.
GLOW_WIDTH_BY_CLASS = {"trunk": 0.8, "main": 1.0}
#: A response is turned down when it is close to the camera: full from the far distance in
#: metres, down to the given share at the near one. Otherwise whatever happens to be under the
#: camera outweighs the whole field, and the passage looks brightest wherever the camera is low.
GLOW_NEAR = (10.0, 45.0, 0.3)
GLOW_INSET = 0.5
GLOW_GAIN = 0.4
#: Metres across of the source: the one place where the heavy trunk and the heavy main cross.
SOURCE_SIZE = 3.4
#: The source is a frame, this many metres thick, not a filled tile: it is a different kind of
#: mark from an inlay and cannot be taken for one. No inlay lies within this many metres of it.
SOURCE_FRAME = 0.45
SOURCE_CLEAR = 7.0


def _response(nodes, links, info, bsdf, inlaid, width=None):
    """Adds a piece's response to ``bsdf`` as emission. It is embedded: only on the face that
    looks up; on a run only at short inlays fixed in the world; on a junction block only in a
    small inset; and never brighter than the film has the piece lit, so nothing the film keeps
    dark is given away."""
    def math(operation, a, b=None):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        for socket, value in zip(node.inputs, (a, b)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]

    def attribute(name):
        node = nodes.new("ShaderNodeAttribute")
        node.attribute_type = "OBJECT"
        node.attribute_name = name
        return node.outputs["Fac"]

    geometry = nodes.new("ShaderNodeNewGeometry")
    normal = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geometry.outputs["True Normal"], normal.inputs["Vector"])
    up = math("GREATER_THAN", normal.outputs["Z"], 0.5)
    place = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geometry.outputs["Position"], place.inputs["Vector"])
    coordinate = nodes.new("ShaderNodeTexCoord")
    own = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coordinate.outputs["Object"], own.inputs["Vector"])

    strength = math("MULTIPLY", attribute(GLOW), up)
    if inlaid:
        length, nearest, furthest = GLOW_INLAY
        # Measured along the run, so an inlay lies square across it.
        along = math("ADD", place.outputs["X"] if "x" in inlaid else 0.0, place.outputs["Y"] if "y" in inlaid else 0.0)
        # This run's own spacing and offset, from which run it is.
        which = info.outputs["Random"]
        pitch = math("ADD", nearest, math("MULTIPLY", which, furthest - nearest))
        offset = math("MULTIPLY", math("FRACT", math("MULTIPLY", which, 7.31)), pitch)
        within = math("FLOORED_MODULO", math("ADD", along, offset), pitch)
        marks = math("LESS_THAN", within, length)
        if inlaid in ("x", "y"):
            # Where across the run this point is, in metres from the run's own centre line.
            centre = nodes.new("ShaderNodeSeparateXYZ")
            links.new(info.outputs["Location"], centre.inputs["Vector"])
            axis = "Y" if inlaid == "x" else "X"
            across = math("SUBTRACT", place.outputs[axis], centre.outputs[axis])
            # The original marks: a slot in the middle of the width, not a band across it.
            marks = math("MULTIPLY", marks, math("LESS_THAN", math("ABSOLUTE", across), width * 0.5))
            usable = math("MAXIMUM", math("SUBTRACT", attribute(RUN_WIDTH), width), 0.0)
            # The climax adds inlays between the ones already there, without moving them: one
            # more per period from the coupling, one more from saturation, each admitted only
            # once its wave has reached this run.
            period = math("FLOOR", math("DIVIDE", math("ADD", along, offset), pitch))
            split = math("MULTIPLY", pitch, DENSE_SPLIT)
            bounds = ((DENSE_GAP + length, split),
                      (math("ADD", split, length + DENSE_GAP), math("SUBTRACT", pitch, length + DENSE_GAP)))
            for layer, ((low, high), name) in enumerate(zip(bounds, DENSE)):
                key = nodes.new("ShaderNodeCombineXYZ")
                links.new(period, key.inputs["X"])
                links.new(math("MULTIPLY", which, 1000.0), key.inputs["Y"])
                key.inputs["Z"].default_value = 17.0 + 11.0 * layer
                hashed = nodes.new("ShaderNodeTexWhiteNoise")
                hashed.noise_dimensions = "3D"
                links.new(key.outputs["Vector"], hashed.inputs["Vector"])
                start = math("ADD", low, math("MULTIPLY", hashed.outputs["Value"], math("SUBTRACT", high, low)))
                inside = math("SUBTRACT", within, start)
                # Its own place across the run.
                side = nodes.new("ShaderNodeCombineXYZ")
                links.new(period, side.inputs["X"])
                links.new(math("MULTIPLY", which, 1000.0), side.inputs["Y"])
                side.inputs["Z"].default_value = 41.0 + 11.0 * layer
                drift = nodes.new("ShaderNodeTexWhiteNoise")
                drift.noise_dimensions = "3D"
                links.new(side.outputs["Vector"], drift.inputs["Vector"])
                off = math("MULTIPLY", math("SUBTRACT", drift.outputs["Value"], 0.5), math("MULTIPLY", usable, DENSE_ACROSS))
                slot = math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", across, off)), width * 0.5)
                added = math("MULTIPLY", math("MULTIPLY", math("GREATER_THAN", inside, 0.0), math("LESS_THAN", inside, length)),
                             math("MULTIPLY", attribute(name), slot))
                marks = math("MAXIMUM", marks, added)
        strength = math("MULTIPLY", strength, marks)
        if inlaid in ("x", "y"):
            # Nothing within a few metres of a cut end: no mark implies transmission across it.
            side = attribute(CUT_SIDE)
            past = math("MULTIPLY", side, math("SUBTRACT", place.outputs["X" if inlaid == "x" else "Y"], attribute(CUT_AT)))
            clear = math("MAXIMUM", math("LESS_THAN", math("ABSOLUTE", side), 0.5), math("GREATER_THAN", past, emission.CUT_CLEAR))
            strength = math("MULTIPLY", strength, clear)
    else:
        # A junction block: a small inset in the middle of its top, not the block.
        inside = math("MULTIPLY", math("LESS_THAN", math("ABSOLUTE", own.outputs["X"]), GLOW_INSET * 0.5),
                      math("LESS_THAN", math("ABSOLUTE", own.outputs["Y"]), GLOW_INSET * 0.5))
        strength = math("MULTIPLY", strength, inside)
    if inlaid in ("x", "y"):
        # The source: where the two heavy runs cross, and nowhere else. Only those two runs
        # carry a value for it; on every other run it is nothing.
        from ..core import network
        hx, hy = network.hub()
        far = math("MAXIMUM", math("ABSOLUTE", math("SUBTRACT", place.outputs["X"], hx)),
                   math("ABSOLUTE", math("SUBTRACT", place.outputs["Y"], hy)))
        frame = math("MULTIPLY", math("LESS_THAN", far, SOURCE_SIZE * 0.5), math("GREATER_THAN", far, SOURCE_SIZE * 0.5 - SOURCE_FRAME))
        source = math("MULTIPLY", math("MULTIPLY", attribute(SOURCE), up), frame)
        strength = math("MULTIPLY", strength, math("GREATER_THAN", far, SOURCE_CLEAR))
        strength = math("MAXIMUM", strength, source)
    # Turned down near the camera.
    nearest, furthest, least = GLOW_NEAR
    view = nodes.new("ShaderNodeCameraData")
    by_distance = nodes.new("ShaderNodeMapRange")
    by_distance.clamp = True
    by_distance.interpolation_type = "SMOOTHSTEP"
    by_distance.inputs["From Min"].default_value = nearest
    by_distance.inputs["From Max"].default_value = furthest
    by_distance.inputs["To Min"].default_value = least
    by_distance.inputs["To Max"].default_value = 1.0
    links.new(view.outputs["View Distance"], by_distance.inputs["Value"])
    strength = math("MULTIPLY", strength, by_distance.outputs["Result"])
    lit = math("MULTIPLY", strength, _value(nodes, links, info.outputs["Color"]))      # 0 while unseen, 0.5 when lit
    bsdf.inputs["Emission Color"].default_value = GLOW_COLOR + (1.0,)
    links.new(math("MULTIPLY", lit, 2.0 * GLOW_GAIN), bsdf.inputs["Emission Strength"])


def _fog(nodes, links, shader, emission=None):
    """`shader` seen through the level's distance fog, on camera rays only; `emission`, if given,
    is added after the fog, unchanged. Returns the shader socket to output."""
    def math(operation, a, b, clamp=False):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        node.use_clamp = clamp
        for socket, x in zip(node.inputs, (a, b)):
            if isinstance(x, float):
                socket.default_value = x
            else:
                links.new(x, socket)
        return node.outputs["Value"]

    camera = nodes.new("ShaderNodeCameraData")
    near, far = FOG
    amount = math("DIVIDE", math("SUBTRACT", camera.outputs["View Distance"], near), far - near, clamp=True)
    path = nodes.new("ShaderNodeLightPath")
    amount = math("MULTIPLY", amount, path.outputs["Is Camera Ray"])
    # Black above the horizon: how far the view looks up.
    geometry = nodes.new("ShaderNodeNewGeometry")
    looking = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geometry.outputs["Incoming"], looking.inputs["Vector"])
    rise = nodes.new("ShaderNodeMapRange")
    rise.interpolation_type = "SMOOTHSTEP"
    rise.inputs["From Min"].default_value, rise.inputs["From Max"].default_value = FOG_RISE
    rise.inputs["To Min"].default_value, rise.inputs["To Max"].default_value = 1.0, 0.0
    links.new(math("MULTIPLY", looking.outputs["Z"], -1.0), rise.inputs["Value"])
    colour = nodes.new("ShaderNodeEmission")
    colour.inputs["Color"].default_value = FOG_COLOUR + (1.0,)
    links.new(rise.outputs["Result"], colour.inputs["Strength"])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(amount, mix.inputs["Fac"])
    links.new(shader, mix.inputs[1])
    links.new(colour.outputs["Emission"], mix.inputs[2])
    out = mix.outputs["Shader"]
    if emission is not None:
        add = nodes.new("ShaderNodeAddShader")
        links.new(out, add.inputs[0])
        links.new(emission, add.inputs[1])
        out = add.outputs["Shader"]
    return out


def _surface(kind, retro=None):
    """A class's material. With `retro` (map path, metres per tile), its colour is multiplied by
    that low-resolution grey map, box-projected in metres; emission is not touched."""
    roughness, metallic, bevel = CLASSES[kind]
    material = bpy.data.materials.new("PD_Look_" + kind)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    info = nodes.new("ShaderNodeObjectInfo")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if retro:
        links.new(_retro_colour(nodes, links, info, *retro), bsdf.inputs["Base Color"])
    else:
        links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    # Specular follows the surface's own value, up to the ordinary 0.5: black takes no highlight.
    links.new(_value(nodes, links, info.outputs["Color"]), bsdf.inputs["Specular IOR Level"])
    if bevel > 0.0:
        # Rounded edges in shading only: every box keeps its exact shape.
        edge = nodes.new("ShaderNodeBevel")
        edge.samples = 2
        edge.inputs["Radius"].default_value = bevel
        links.new(edge.outputs["Normal"], bsdf.inputs["Normal"])
    if kind in GLOWING:
        _response(nodes, links, info, bsdf, inlaid=GLOWING[kind], width=GLOW_WIDTH_BY_CLASS.get(kind))
    out = bsdf.outputs["BSDF"]
    if kind in FOGGED:
        emission = None
        if kind in GLOWING:
            # The inlays leave the surface and are added back after the fog: the same light.
            strength = bsdf.inputs["Emission Strength"]
            source = strength.links[0].from_socket
            links.remove(strength.links[0])
            strength.default_value = 0.0
            glow = nodes.new("ShaderNodeEmission")
            glow.inputs["Color"].default_value = bsdf.inputs["Emission Color"].default_value
            links.new(source, glow.inputs["Strength"])
            emission = glow.outputs["Emission"]
        out = _fog(nodes, links, out, emission)
    links.new(out, nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


def _retro_colour(nodes, links, info, path, tile):
    """The object's colour multiplied by a grey map (box-projected in metres, nearest-neighbour)
    about a mean of 1, by the object's own contrast (TONE). Uses the object's SCALE."""
    def attribute(name):
        node = nodes.new("ShaderNodeAttribute")
        node.attribute_type = "OBJECT"
        node.attribute_name = name
        return node

    def math(operation, a, b):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        for socket, x in zip(node.inputs, (a, b)):
            if isinstance(x, float):
                socket.default_value = x
            else:
                links.new(x, socket)
        return node.outputs["Value"]

    coords = nodes.new("ShaderNodeTexCoord")
    metres = nodes.new("ShaderNodeVectorMath")
    metres.operation = "MULTIPLY"
    links.new(coords.outputs["Object"], metres.inputs[0])
    links.new(attribute(SCALE).outputs["Vector"], metres.inputs[1])
    tiles = nodes.new("ShaderNodeVectorMath")
    tiles.operation = "SCALE"
    tiles.inputs["Scale"].default_value = 1.0 / tile
    links.new(metres.outputs["Vector"], tiles.inputs[0])
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(os.path.normpath(path), check_existing=True)
    texture.image.colorspace_settings.name = "Non-Color"
    texture.projection, texture.projection_blend, texture.interpolation = "BOX", 0.0, "Closest"
    links.new(tiles.outputs["Vector"], texture.inputs["Vector"])
    factor = math("ADD", math("MULTIPLY", math("MULTIPLY", math("SUBTRACT", texture.outputs["Color"], 0.5), 2.0),
                              attribute(TONE).outputs["Fac"]), 1.0)
    colour = nodes.new("ShaderNodeVectorMath")
    colour.operation = "SCALE"
    links.new(info.outputs["Color"], colour.inputs[0])
    links.new(factor, colour.inputs["Scale"])
    return colour.outputs["Vector"]


#: The room's painted shell: walls, ribs and ceiling. Approved 2026-10-19 (A2): a visibly
#: low-resolution grey surface in the manner of late-PS1-era textures. A 64 x 64 grey map
#: (assets/textures/room_shell/retro_ps1_01, made by tools/make_retro_maps.py: mottling and
#: per-texel grain, 8 levels through a 4 x 4 ordered dither) is box-projected in each object's own
#: space, scaled to metres, with 10 cm texels, sampled nearest-neighbour. It only multiplies the
#: object's own colour, about a mean of 1: black stays black, and every authored light, reveal and
#: colour state is kept. Nothing else about the surface changes. The rear wall's display panels
#: are a different class and never take it.
SHELL = ("Wall", "WallBack", "WallFront", "Ceiling", "Rib")
SHELL_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "assets", "textures", "room_shell", "retro_ps1_01", "modulation.png")
#: Metres one tile covers: 64 texels, so 10 cm each.
SHELL_TILE = 6.4
#: How far the map moves the colour, +-: walls and ribs, and the ceiling, whose darker blue-grey
#: takes the full contrast as stains.
SHELL_TONE = 0.20
SHELL_TONE_BY_NAME = {"Ceiling": 0.11}
#: The chamber floor and the plinth's lower step. Approved 2026-10-19 (F1-LARGE): the shell's
#: language with its own map (same recipe, own seeds), colour only. Its texels are 20 cm, twice the
#: walls': the floor is seen at a grazing angle, where 10 cm texels fall below a pixel in depth, and
#: matching their apparent size on screen matters more than matching their size in metres.
FLOOR_MAP = os.path.join(os.path.dirname(os.path.dirname(SHELL_MAP)), "retro_floor_01", "modulation.png")
FLOOR_TILE = 12.8
FLOOR_TONE = 0.20
#: The room's pale fixtures that move (the cabinets and carriages and the lamp housing). Approved
#: 2026-10-19 (X3, "PS1 prop"): unlike the architecture, which tiles in metres, each prop takes
#: one 16 x 16 texture stretched once over each face, so its texels differ from prop to prop and
#: stretch with it (the carriage's texture stretches as it extends, as on hardware of the era),
#: in 4 flat levels, plus one flat tone per face. Colour only, about a mean of 1; the plinth top
#: and the dark trim and tray are not props in this sense and stay clean.
PROP_MAP = os.path.join(os.path.dirname(os.path.dirname(SHELL_MAP)), "retro_prop_01", "modulation.png")
PROP_TONE = 0.14
PROP_FACE_TONE = 0.06
#: The figure's pale shell. Approved 2026-10-20 (B1): the props' logic, a texture-mapped character
#: model of the era, softer because it is the focal human object: texture +-8.4%, face tone +-3.6%
#: (about +-12% in all). Its joints and dark structure stay clean; its ghost copies have the ghost
#: material, which the look never touches.
BODY_TONE = (0.084, 0.036)
#: The station level (provisionally approved 2026-10-20, N1): its structure takes the
#: architecture's tiled logic (its own map, 40 cm texels, +-20%, colour only; the inlay and cell
#: emission is not touched); station machinery takes the props' logic (X3).
LEVEL_MAP = os.path.join(os.path.dirname(os.path.dirname(SHELL_MAP)), "retro_level_01", "modulation.png")
LEVEL_TILE = 25.6
LEVEL_TONE = 0.20
LEVEL_STRUCTURE = ("trunk", "via", "fine", "main", "station", "kit_floor", "apron")
#: Distance fog on the station level, in the manner of early real-time 3D (2026-10-20): what the
#: camera sees fades linearly with distance into a very dark blue-grey, black above the horizon,
#: so the level, the distance shell and the sky meet without an edge. Camera rays only: it adds
#: no light, changes no reflection, and the network's emission is added after it, untouched.
#: Metres (start, full), the colour at the horizon, and the rise over which it goes to black.
FOG = (110.0, 700.0)
FOG_COLOUR = (0.010, 0.012, 0.016)
FOG_RISE = (0.02, 0.35)
#: Classes the fog applies to: the level's own surfaces (the room is never that far), and the pit's
#: near-black walls, whose rim shows from above (their colour is the fog's own, so the pit is not
#: changed). "floor" carries the level ground and the pit's ceiling, "wall" the shell.
FOGGED = LEVEL_STRUCTURE + ("kit", "floor", "wall", "pit", "echo")
#: The landfill (provisionally approved 2026-10-20, L1): the waste ground takes the floor's
#: tiled logic (its own map, 20 cm texels, +-25%); the refuse, strata, discarded parts and chutes,
#: being discarded props, take the props' logic (X3). The near-black pit floor and walls are left.
WASTE_MAP = os.path.join(os.path.dirname(os.path.dirname(SHELL_MAP)), "retro_waste_01", "modulation.png")
WASTE_TILE = 12.8
WASTE_TONE = 0.25
#: Per object: its contrast (+-), and its world scale in metres per unit of its own coordinates.
TONE = "pd_tone"
SCALE = "pd_scale"


def _world_scale(obj):
    """An object's scale with its parents', axis by axis (nothing in the room is sheared)."""
    scale = list(obj.scale)
    parent = obj.parent
    while parent is not None:
        scale = [a * b for a, b in zip(scale, parent.scale)]
        parent = parent.parent
    return tuple(scale)


def _prop(name, kind, tone=PROP_TONE, face_tone=PROP_FACE_TONE):
    """A prop's material in the manner of early 3D: the class's own values, with its colour
    multiplied by one small texture stretched once over each face (unless `tone` is 0) and by one
    flat tone per face."""
    roughness, metallic, bevel = CLASSES[kind]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    info = nodes.new("ShaderNodeObjectInfo")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    links.new(_value(nodes, links, info.outputs["Color"]), bsdf.inputs["Specular IOR Level"])

    def math(operation, a, b):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        for socket, x in zip(node.inputs, (a, b)):
            if isinstance(x, float):
                socket.default_value = x
            else:
                links.new(x, socket)
        return node.outputs["Value"]

    def vector(operation, a, b):
        node = nodes.new("ShaderNodeVectorMath")
        node.operation = operation
        for socket, x in zip(node.inputs, (a, b)):
            if isinstance(x, tuple):
                socket.default_value = x
            else:
                links.new(x, socket)
        return node.outputs["Vector"]

    # One copy of the texture per face: 0..1 across each face of the object's bounding box (the
    # same on a stretched unit box and on a true-size bevelled mesh).
    coords = nodes.new("ShaderNodeTexCoord")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(os.path.normpath(PROP_MAP), check_existing=True)
    texture.image.colorspace_settings.name = "Non-Color"
    texture.projection, texture.projection_blend, texture.interpolation = "BOX", 0.0, "Closest"
    texture.extension = "EXTEND"
    links.new(coords.outputs["Generated"], texture.inputs["Vector"])
    # One flat tone per face: which way the face points (in the object's own space, as drawn, so
    # each facet of a faceted cylinder is its own), hashed with the object.
    geometry = nodes.new("ShaderNodeNewGeometry")
    facing = nodes.new("ShaderNodeVectorTransform")
    facing.vector_type, facing.convert_from, facing.convert_to = "NORMAL", "WORLD", "OBJECT"
    links.new(geometry.outputs["True Normal"], facing.inputs["Vector"])
    snap = nodes.new("ShaderNodeVectorMath")
    snap.operation = "SNAP"
    links.new(vector("ADD", vector("MULTIPLY", facing.outputs["Vector"], (4.0, 4.0, 4.0)), (0.5, 0.5, 0.5)), snap.inputs[0])
    snap.inputs[1].default_value = (1.0, 1.0, 1.0)
    seed = nodes.new("ShaderNodeVectorMath")
    seed.operation = "SCALE"
    seed.inputs[0].default_value = (13.1, 7.7, 3.3)
    links.new(info.outputs["Random"], seed.inputs["Scale"])
    hashed = nodes.new("ShaderNodeTexWhiteNoise")
    hashed.noise_dimensions = "3D"
    links.new(vector("ADD", snap.outputs["Vector"], seed.outputs["Vector"]), hashed.inputs["Vector"])
    face = math("MULTIPLY", math("SUBTRACT", hashed.outputs["Value"], 0.5), 2.0 * face_tone)
    if tone:
        pattern = math("MULTIPLY", math("SUBTRACT", texture.outputs["Color"], 0.5), 2.0 * tone)
        factor = math("ADD", math("ADD", pattern, face), 1.0)
    else:
        factor = math("ADD", face, 1.0)
    colour = nodes.new("ShaderNodeVectorMath")
    colour.operation = "SCALE"
    links.new(info.outputs["Color"], colour.inputs[0])
    links.new(factor, colour.inputs["Scale"])
    links.new(colour.outputs["Vector"], bsdf.inputs["Base Color"])
    edge = nodes.new("ShaderNodeBevel")
    edge.samples = 2
    edge.inputs["Radius"].default_value = bevel
    links.new(edge.outputs["Normal"], bsdf.inputs["Normal"])
    out = bsdf.outputs["BSDF"]
    if kind in FOGGED:
        out = _fog(nodes, links, out)
    links.new(out, nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


#: The rear wall's 15 display panels as CRT-like screens (approved design 2026-10-20). The box
#: sides and a 10 cm bezel keep the panel's authored colour; the inner front face is dark glass
#: carrying a 64 x 48 raster with scanlines, showing what presentation/screens.py says. The screens' light
#: is seen by the camera only: it lights nothing and is in no reflection. It is tied to the
#: panel's own authored light, so a screen is dark wherever the film has the panel dark.
SCREEN_BEZEL = 0.10
SCREEN_GLASS = 0.25
SCREEN_ROUGHNESS = 0.15
SCREEN_COLOUR = (0.55, 0.85, 1.0)
SCREEN_STRENGTH = 0.8
#: The panels' authored colour at full light (FIXTURE), to read how lit a panel is.
SCREEN_LIT = 0.44
#: The objects that carry the lyric as text in the scene (see presentation/lyrics.py).
LYRIC_TEXT = "LyricText"
SCREEN_PROPS = ("pd_lyric", "pd_lyric_on", "pd_video", "pd_wake", "pd_blocks", "pd_traces", "pd_hold", "pd_lean", "pd_flicker", "pd_frame",
                "pd_trace_seed", "pd_trace_progress", "pd_bx0", "pd_by0", "pd_bx1", "pd_by1")


def _display(feed=None):
    """The screens' material (see SCREEN_*). With `feed` (independent monitors, see
    screens.video_format()), the frame of the footage stream this screen starts from."""
    roughness, metallic, bevel = CLASSES["display"]
    material = bpy.data.materials.new("PD_Look_display")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    info = nodes.new("ShaderNodeObjectInfo")

    def connect(socket, x):
        if isinstance(x, (int, float)):
            socket.default_value = x
        else:
            links.new(x, socket)

    def math(operation, a, b=None, clamp=False):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        node.use_clamp = clamp
        connect(node.inputs[0], a)
        if b is not None:
            connect(node.inputs[1], b)
        return node.outputs["Value"]

    def attribute(name):
        node = nodes.new("ShaderNodeAttribute")
        node.attribute_type = "OBJECT"
        node.attribute_name = name
        return node.outputs["Fac"]

    def between(x, low, high):
        return math("MULTIPLY", math("GREATER_THAN", x, low), math("LESS_THAN", x, high))

    # Where on the panel: 0..1 across its bounding box's width (x) and height (z), the same on a
    # stretched unit box and on a true-size bevelled mesh.
    coords = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"], place.inputs["Vector"])
    u = place.outputs["X"]
    v = place.outputs["Z"]
    # The front face looks into the room, along the box's -Y.
    geometry = nodes.new("ShaderNodeNewGeometry")
    facing = nodes.new("ShaderNodeVectorTransform")
    facing.vector_type, facing.convert_from, facing.convert_to = "NORMAL", "WORLD", "OBJECT"
    links.new(geometry.outputs["True Normal"], facing.inputs["Vector"])
    normal = nodes.new("ShaderNodeSeparateXYZ")
    links.new(facing.outputs["Vector"], normal.inputs["Vector"])
    front = math("LESS_THAN", normal.outputs["Y"], -0.5)
    width, height = 2.35, 2.0
    mx, my = SCREEN_BEZEL / width, SCREEN_BEZEL / height
    screen = math("MULTIPLY", front, math("MULTIPLY", between(u, mx, 1.0 - mx), between(v, my, 1.0 - my)))
    su = math("DIVIDE", math("SUBTRACT", u, mx), 1.0 - 2.0 * mx)
    sv = math("DIVIDE", math("SUBTRACT", v, my), 1.0 - 2.0 * my)
    columns, rows = screens.PIXELS
    across = math("MULTIPLY", su, float(columns))
    down = math("MULTIPLY", math("SUBTRACT", 1.0, sv), float(rows))
    px = math("FLOOR", across)
    py = math("FLOOR", down)
    centre = math("DIVIDE", math("ADD", px, 0.5), float(columns))

    # Blocks: one coarse rectangle, on the virtual-pixel grid.
    lit_block = math("MULTIPLY", between(px, math("SUBTRACT", attribute("pd_bx0"), 0.5), attribute("pd_bx1")),
                     between(py, math("SUBTRACT", attribute("pd_by0"), 0.5), attribute("pd_by1")))
    # Traces: one crooked line, a virtual pixel thick, drawn left to right.
    walk = nodes.new("ShaderNodeTexNoise")
    walk.noise_dimensions = "2D"
    walk.inputs["Scale"].default_value = 1.0
    walk.inputs["Detail"].default_value = 2.0
    combine = nodes.new("ShaderNodeCombineXYZ")
    links.new(math("MULTIPLY", px, 0.09), combine.inputs["X"])
    links.new(attribute("pd_trace_seed"), combine.inputs["Y"])
    links.new(combine.outputs["Vector"], walk.inputs["Vector"])
    line = math("FLOOR", math("ADD", math("MULTIPLY", math("SUBTRACT", walk.outputs["Fac"], 0.5), 60.0), rows * 0.5))
    on_line = math("COMPARE", py, line)
    on_line.node.inputs[2].default_value = 0.5
    lit_trace = math("MULTIPLY", on_line, math("LESS_THAN", centre, attribute("pd_trace_progress")))
    # The attractor's one steady block.
    block = math("MULTIPLY", between(px, 25.5, 38.5), between(py, 17.5, 30.5))
    # Sparse flicker with the high band.
    grain = nodes.new("ShaderNodeTexWhiteNoise")
    grain.noise_dimensions = "3D"
    cell = nodes.new("ShaderNodeCombineXYZ")
    links.new(px, cell.inputs["X"])
    links.new(py, cell.inputs["Y"])
    links.new(attribute("pd_frame"), cell.inputs["Z"])
    links.new(cell.outputs["Vector"], grain.inputs["Vector"])
    lit_flicker = math("LESS_THAN", grain.outputs["Value"], attribute("pd_flicker"))

    content = math("MAXIMUM", screens.IDLE, math("MULTIPLY", attribute("pd_blocks"), lit_block))
    content = math("MAXIMUM", content, math("MULTIPLY", attribute("pd_traces"), lit_trace))
    content = math("MAXIMUM", content, math("MULTIPLY", attribute("pd_hold"), block))
    content = math("MAXIMUM", content, math("MULTIPLY", lit_flicker, 0.35))

    def mix(a, b, factor):
        return math("ADD", a, math("MULTIPLY", math("SUBTRACT", b, a), factor))

    def scanlines(rows_down):
        # The lower part of every virtual row is dark.
        return math("ADD", 0.35, math("MULTIPLY", 0.65, math("LESS_THAN", math("FRACT", rows_down), 0.65)))

    scan = scanlines(down)
    # Real footage where there is any, in place of all that; the lyric while it is sung, in place
    # of everything. The lyric is this screen's part of the wall's one canvas, a canvas pixel to a
    # screen pixel; the footage is read on its own grid (screens.video_format()), with the raster
    # following that grid's rows. All read nearest-pixel.
    canvas_w, canvas_h = lyrics.CANVAS
    canvas_x = math("ADD", math("ADD", attribute("pd_cx"), px), 0.5)
    canvas_y = math("ADD", math("ADD", attribute("pd_cy"), py), 0.5)
    footage = _footage()
    video_rgb = None
    if footage is not None and feed is not None:
        # An independent monitor: the picture fills the screen's height, its own aspect kept, and
        # the width that does not fit is cut off left and right, evenly (director, 2026-10-22: no
        # letterbox); in colour, sampled smoothly; the footage's own light, held at VIDEO_CAP of
        # the screens'. No raster grid or scanlines (clarity baseline).
        form = screens.video_format()
        seen_share = (2.35 - 2.0 * SCREEN_BEZEL) / (2.0 - 2.0 * SCREEN_BEZEL) * form["size"][1] / form["size"][0]
        picture_u = math("ADD", 0.5, math("MULTIPLY", math("SUBTRACT", su, 0.5), seen_share))
        where = nodes.new("ShaderNodeCombineXYZ")
        links.new(picture_u, where.inputs["X"])
        links.new(sv, where.inputs["Y"])
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = footage
        texture.interpolation, texture.extension = "Linear", "CLIP"
        user = texture.image_user
        user.frame_duration = form["frames"]
        user.frame_start = form["first"] - feed
        user.frame_offset = 0
        user.use_cyclic = True
        user.use_auto_refresh = True
        links.new(where.outputs["Vector"], texture.inputs["Vector"])
        picture = texture.outputs["Color"]
        if "tint" in screens.VIDEO_STAGES:
            # Stage A: the picture's own luminance, in the screens' cyan scaled to a luminance of
            # one, so that nothing gets brighter or darker, only colder.
            grey = nodes.new("ShaderNodeRGBToBW")
            links.new(picture, grey.inputs["Color"])
            luminance = 0.2126 * SCREEN_COLOUR[0] + 0.7152 * SCREEN_COLOUR[1] + 0.0722 * SCREEN_COLOUR[2]
            cold = nodes.new("ShaderNodeVectorMath")
            cold.operation = "SCALE"
            cold.inputs[0].default_value = tuple(c / luminance for c in SCREEN_COLOUR)
            links.new(grey.outputs["Val"], cold.inputs["Scale"])
            picture = cold.outputs["Vector"]
        if "scanlines" in screens.VIDEO_STAGES:
            # Stage B: the screens' raster, 48 rows, the lower part of each darker.
            dark = math("GREATER_THAN", math("FRACT", down), 0.65)
            rows_light = nodes.new("ShaderNodeVectorMath")
            rows_light.operation = "SCALE"
            links.new(picture, rows_light.inputs[0])
            links.new(math("SUBTRACT", 1.0, math("MULTIPLY", dark, screens.VIDEO_SCANLINES)), rows_light.inputs["Scale"])
            picture = rows_light.outputs["Vector"]
        video_rgb = (picture, screen)
    elif footage is not None:
        form = screens.video_format()
        fw, fh = form["screen"]
        f_down = math("MULTIPLY", math("SUBTRACT", 1.0, sv), float(fh))
        fx = math("ADD", math("FLOOR", math("MULTIPLY", su, float(fw))), 0.5)
        fy = math("ADD", math("FLOOR", f_down), 0.5)
        if form["layout"] == "wall":
            # One picture across the wall: this screen's section of it.
            fx = math("ADD", math("MULTIPLY", attribute("pd_cx"), fw / float(columns)), fx)
            fy = math("ADD", math("MULTIPLY", attribute("pd_cy"), fh / float(rows)), fy)
        cw, ch = form["canvas"]
        seen = _read(nodes, links, footage, math("DIVIDE", fx, float(cw)),
                     math("SUBTRACT", 1.0, math("DIVIDE", fy, float(ch))), sequence=(form["first"], form["last"]))
        content = mix(content, math("MAXIMUM", screens.IDLE, seen), attribute("pd_video"))
        scan = mix(scan, scanlines(f_down), attribute("pd_video"))
    lines = lyrics.crt_lines()
    if lines:
        atlas_rows = float(canvas_h * len(lines))
        atlas_y = math("ADD", math("MULTIPLY", attribute("pd_lyric"), float(canvas_h)), canvas_y)
        glyph = _read(nodes, links, _lyric_canvas(lines), math("DIVIDE", canvas_x, float(canvas_w)),
                      math("SUBTRACT", 1.0, math("DIVIDE", atlas_y, atlas_rows)))
        content = mix(content, math("MAXIMUM", screens.IDLE, math("MULTIPLY", glyph, screens.LIT)), attribute("pd_lyric_on"))
        scan = mix(scan, scanlines(down), attribute("pd_lyric_on"))
    # How lit the film has the panel.
    channels = nodes.new("ShaderNodeSeparateColor")
    links.new(info.outputs["Color"], channels.inputs["Color"])
    light = math("DIVIDE", math("MAXIMUM", channels.outputs["Red"], math("MAXIMUM", channels.outputs["Green"],
                                                                          channels.outputs["Blue"])),
                 SCREEN_LIT, clamp=True)
    level = math("MULTIPLY", math("MULTIPLY", content, scan), math("MULTIPLY", attribute("pd_lean"), attribute("pd_wake")))
    level = math("MULTIPLY", math("MULTIPLY", level, light), screen)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metallic
    glass = nodes.new("ShaderNodeVectorMath")
    glass.operation = "SCALE"
    links.new(info.outputs["Color"], glass.inputs[0])
    links.new(math("SUBTRACT", 1.0, math("MULTIPLY", screen, 1.0 - SCREEN_GLASS)), glass.inputs["Scale"])
    links.new(glass.outputs["Vector"], bsdf.inputs["Base Color"])
    links.new(math("SUBTRACT", roughness, math("MULTIPLY", screen, roughness - SCREEN_ROUGHNESS)), bsdf.inputs["Roughness"])
    links.new(_value(nodes, links, info.outputs["Color"]), bsdf.inputs["Specular IOR Level"])
    edge = nodes.new("ShaderNodeBevel")
    edge.samples = 2
    edge.inputs["Radius"].default_value = bevel
    links.new(edge.outputs["Normal"], bsdf.inputs["Normal"])
    glow = nodes.new("ShaderNodeEmission")
    glow.inputs["Color"].default_value = SCREEN_COLOUR + (1.0,)
    links.new(math("MULTIPLY", level, SCREEN_STRENGTH), glow.inputs["Strength"])
    if video_rgb is not None:
        rgb, inside = video_rgb
        # Where the footage plays (and no lyric is up), its own colour at its own light.
        playing = math("MULTIPLY", attribute("pd_video"), math("SUBTRACT", 1.0, attribute("pd_lyric_on")))
        own = math("MULTIPLY", math("MULTIPLY", inside, screens.VIDEO_CAP),
                   math("MULTIPLY", math("MULTIPLY", attribute("pd_lean"), attribute("pd_wake")), light))
        lit = nodes.new("ShaderNodeVectorMath")
        lit.operation = "SCALE"
        links.new(rgb, lit.inputs[0])
        links.new(own, lit.inputs["Scale"])
        idle = nodes.new("ShaderNodeVectorMath")
        idle.operation = "SCALE"
        idle.inputs[0].default_value = SCREEN_COLOUR
        links.new(level, idle.inputs["Scale"])
        # idle + (footage - idle) * playing
        change = nodes.new("ShaderNodeVectorMath")
        change.operation = "SUBTRACT"
        links.new(lit.outputs["Vector"], change.inputs[0])
        links.new(idle.outputs["Vector"], change.inputs[1])
        part = nodes.new("ShaderNodeVectorMath")
        part.operation = "SCALE"
        links.new(change.outputs["Vector"], part.inputs[0])
        links.new(playing, part.inputs["Scale"])
        total = nodes.new("ShaderNodeVectorMath")
        total.operation = "ADD"
        links.new(idle.outputs["Vector"], total.inputs[0])
        links.new(part.outputs["Vector"], total.inputs[1])
        links.new(total.outputs["Vector"], glow.inputs["Color"])
        glow.inputs["Strength"].default_value = SCREEN_STRENGTH
        for link in list(glow.inputs["Strength"].links):
            links.remove(link)
    seen = nodes.new("ShaderNodeAddShader")
    links.new(bsdf.outputs["BSDF"], seen.inputs[0])
    links.new(glow.outputs["Emission"], seen.inputs[1])
    path = nodes.new("ShaderNodeLightPath")
    camera_only = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], camera_only.inputs["Fac"])
    links.new(bsdf.outputs["BSDF"], camera_only.inputs[1])
    links.new(seen.outputs["Shader"], camera_only.inputs[2])
    links.new(camera_only.outputs["Shader"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


def _drive_screen(anim, obj):
    """Gives a panel its screen's values over time, from presentation/screens.py."""
    row = int(round((obj.location[2] - 1.25) / 2.25))
    col = int(round((obj.location[0] + 5.2) / 2.6))
    for name in SCREEN_PROPS:
        obj[name] = 0.0
    # Its part of the wall's canvas: 64 x 48 pixels, the top row of the wall at the top.
    obj["pd_cx"] = float(col * screens.PIXELS[0])
    obj["pd_cy"] = float((screens.ROWS - 1 - row) * screens.PIXELS[1])
    anim.add(obj, '["pd_lyric_on"]', screens.lyric)
    anim.add(obj, '["pd_lyric"]', screens.lyric_index)
    anim.add(obj, '["pd_video"]', screens.video)
    anim.add(obj, '["pd_wake"]', lambda t: screens.wake(row, col, t))
    anim.add(obj, '["pd_blocks"]', screens.blocks)
    anim.add(obj, '["pd_traces"]', screens.traces)
    anim.add(obj, '["pd_hold"]', lambda t: screens.hold(row, col, t))
    anim.add(obj, '["pd_lean"]', screens.lean)
    anim.add(obj, '["pd_flicker"]', screens.flicker)
    anim.add(obj, '["pd_frame"]', lambda t: float(timeline.frame_of(t) % 997))
    anim.add(obj, '["pd_trace_seed"]', lambda t: screens.trace(row, col, t)[0])
    anim.add(obj, '["pd_trace_progress"]', lambda t: screens.trace(row, col, t)[1])
    for i, name in enumerate(("pd_bx0", "pd_by0", "pd_bx1", "pd_by1")):
        anim.add(obj, '["%s"]' % name, lambda t, i=i: screens.block(row, col, t)[i])


def _bitmap(name, width, height, top_first):
    """An image of 0/1 pixels (rows top first), to be read nearest-pixel. Packed, so a saved
    .blend keeps it."""
    import numpy as np
    image = bpy.data.images.new(name, width, height, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    grey = np.asarray(top_first, np.float32).reshape(height, width)[::-1]
    rgba = np.ones((height, width, 4), np.float32)
    rgba[:, :, :3] = grey[:, :, None]
    image.pixels.foreach_set(rgba.ravel())
    image.update()
    image.pack()
    return image


def _lyric_canvas(lines):
    """Every CRT line's canvas, one under another, the first at the top (see lyrics.crt_lines)."""
    pixels = []
    for entry in lines:
        pixels.extend(lyrics.canvas(entry))
    return _bitmap("PD_LyricCanvas", lyrics.CANVAS[0], lyrics.CANVAS[1] * len(lines), pixels)


def _footage():
    """The footage's canvas frames as an image sequence, or None while there are none."""
    span = screens.video_frames()
    if span is None:
        return None
    form = screens.video_format()
    if form["layout"] == "feeds":
        # One clean stream, every screen at its own point in it (see _display).
        image = bpy.data.images.load(os.path.join(screens.VIDEO, form["stream"]), check_existing=True)
        image.colorspace_settings.name = "sRGB"
        return image
    # The frame before the first is a blank canvas: Blender reads it for every frame before.
    image = bpy.data.images.load(os.path.join(screens.VIDEO, "frame_%06d.png" % (span[0] - 1)), check_existing=True)
    image.source = "SEQUENCE"
    image.colorspace_settings.name = "Non-Color"
    return image


def _read(nodes, links, image, u, v, sequence=None):
    """The image's grey at (u, v), nearest-pixel. For an image sequence, `sequence` is the (first,
    last) frame of the film its frames are numbered by."""
    where = nodes.new("ShaderNodeCombineXYZ")
    links.new(u, where.inputs["X"])
    links.new(v, where.inputs["Y"])
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation, texture.extension = "Closest", "EXTEND"
    if sequence is not None:
        # Film frame n reads file n; every frame before the first reads the blank file before it
        # (Blender's frame 0 of a sequence), every frame after the last, the last.
        first, last = sequence
        user = texture.image_user
        user.frame_duration = last - first + 1
        user.frame_start = first
        user.frame_offset = first - 1
        user.use_auto_refresh = True
        user.use_cyclic = False
    links.new(where.outputs["Vector"], texture.inputs["Vector"])
    return texture.outputs["Color"]


#: World-space lyric text (see presentation/lyrics.py): hard Unifont pixels in a pale, cold,
#: nearly grey light, held below the CRTs' cyan. It is seen by the camera and nothing else: it
#: lights nothing, casts nothing, and is in no reflection.
LYRIC_COLOUR = (0.80, 0.86, 0.90)
LYRIC_STRENGTH = 0.55


def _lyric_material(name, image):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    if hasattr(material, "emission_sampling"):
        material.emission_sampling = "NONE"
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    coords = nodes.new("ShaderNodeTexCoord")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation, texture.extension = "Closest", "CLIP"
    links.new(coords.outputs["UV"], texture.inputs["Vector"])
    glow = nodes.new("ShaderNodeEmission")
    glow.inputs["Color"].default_value = LYRIC_COLOUR + (1.0,)
    glow.inputs["Strength"].default_value = LYRIC_STRENGTH
    clear = nodes.new("ShaderNodeBsdfTransparent")
    shader = nodes.new("ShaderNodeMixShader")
    links.new(texture.outputs["Color"], shader.inputs["Fac"])
    links.new(clear.outputs["BSDF"], shader.inputs[1])
    links.new(glow.outputs["Emission"], shader.inputs[2])
    links.new(shader.outputs["Shader"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


def build_lyric_text(scene, anim):
    """The lines shown in the scene rather than on the CRTs: each a flat block of text fixed in
    the world where tools/lyric_layout.py placed it, facing the camera as it was in the middle of
    the line, there for exactly the line's window. Returns how many."""
    lines = lyrics.world_lines()
    for k, entry in enumerate(lines):
        width, height, pixels = lyrics.world_bitmap(entry)
        mesh = bpy.data.meshes.new("PD_LyricText")
        mesh.from_pydata([(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0)], [], [(0, 1, 2, 3)])
        uv = mesh.uv_layers.new(name="UVMap")
        for loop, (u, v) in zip(uv.data, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
            loop.uv = (u, v)
        mesh.materials.append(_lyric_material("PD_Look_lyric", _bitmap("PD_LyricText.%03d" % k, width, height, pixels)))
        obj = bpy.data.objects.new(LYRIC_TEXT, mesh)
        scene.collection.objects.link(obj)
        place = entry["world"]
        obj.location = place["centre"]
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = place["rotation"]
        size = (width / 16.0 * place["glyph"], height / 16.0 * place["glyph"], 1.0)
        obj.scale = (0.0, 0.0, 0.0)
        a, b = place["shown"]
        anim.add(obj, "scale", lambda t, a=a, b=b, size=size: size if a <= t < b else (0.0, 0.0, 0.0))
        for path in _RAYS:
            setattr(obj, path, path == "visible_camera")
    return len(lines)


def _yield_to_lyric(anim, scene):
    """In the coda the lyric takes priority over the marks on the panels that carry it: those
    marks are not drawn at all (director's revision, 2026-10-21). The marks on every other panel
    and on the floor are as they were. Returns how many marks give way."""
    cells = lyrics.coda_cells()
    giving = set()
    for obj in scene.objects:
        # The rear wall's marks, by where they stand (built at their centres, here unmoved).
        if obj.name.split(".")[0] in ("CodaScrawl", "CodaBar") and obj.location[1] > 10.0:
            cell = (int(round((obj.location[2] - 1.25) / 2.25)), int(round((obj.location[0] + 5.2) / 2.6)))
            if cell in cells:
                giving.add(obj.as_pointer())
                for path in _RAYS:
                    setattr(obj, path, False)
    anim._channels = [c for c in anim._channels if not (c[1] in _RAYS and c[0].as_pointer() in giving)]
    return len(giving)


def _shell():
    """The shell's material: the wall class, with its colour multiplied by the shell map."""
    return _retro("PD_Look_shell", "wall", SHELL_MAP, SHELL_TILE)


def _retro(name, kind, path, tile, roughness_step=0.0):
    """A class's material with its colour multiplied by a low-resolution grey map, and, if
    `roughness_step` is set, its roughness moved by the same map (+-, in the map's own steps)."""
    roughness, metallic, bevel = CLASSES[kind]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    info = nodes.new("ShaderNodeObjectInfo")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    # Specular follows the object's own colour, not the textured one, as for every class.
    links.new(_value(nodes, links, info.outputs["Color"]), bsdf.inputs["Specular IOR Level"])

    def attribute(name):
        node = nodes.new("ShaderNodeAttribute")
        node.attribute_type = "OBJECT"
        node.attribute_name = name
        return node

    def math(operation, a, b):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        for socket, x in zip(node.inputs, (a, b)):
            if isinstance(x, float):
                socket.default_value = x
            else:
                links.new(x, socket)
        return node.outputs["Value"]

    # Where on the map: the object's own coordinates in metres, so the texels ride with it.
    coords = nodes.new("ShaderNodeTexCoord")
    metres = nodes.new("ShaderNodeVectorMath")
    metres.operation = "MULTIPLY"
    links.new(coords.outputs["Object"], metres.inputs[0])
    links.new(attribute(SCALE).outputs["Vector"], metres.inputs[1])
    tiles = nodes.new("ShaderNodeVectorMath")
    tiles.operation = "SCALE"
    tiles.inputs["Scale"].default_value = 1.0 / tile
    links.new(metres.outputs["Vector"], tiles.inputs[0])
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(os.path.normpath(path), check_existing=True)
    texture.image.colorspace_settings.name = "Non-Color"
    texture.projection, texture.projection_blend, texture.interpolation = "BOX", 0.0, "Closest"
    links.new(tiles.outputs["Vector"], texture.inputs["Vector"])
    # 1 + (map - 0.5) * 2 * tone: a factor about 1 on the object's own colour.
    factor = math("ADD", math("MULTIPLY", math("MULTIPLY", math("SUBTRACT", texture.outputs["Color"], 0.5), 2.0),
                              attribute(TONE).outputs["Fac"]), 1.0)
    colour = nodes.new("ShaderNodeVectorMath")
    colour.operation = "SCALE"
    links.new(info.outputs["Color"], colour.inputs[0])
    links.new(factor, colour.inputs["Scale"])
    links.new(colour.outputs["Vector"], bsdf.inputs["Base Color"])
    if roughness_step:
        links.new(math("ADD", math("MULTIPLY", math("SUBTRACT", texture.outputs["Color"], 0.5), 2.0 * roughness_step),
                       roughness), bsdf.inputs["Roughness"])
    edge = nodes.new("ShaderNodeBevel")
    edge.samples = 2
    edge.inputs["Radius"].default_value = bevel
    links.new(edge.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


#: Classes whose objects stand in the scene before the film reveals them: what stands on a
#: station, and the bars. Until the film gives such an object a colour it is black. The preview
#: drew that black against a dark top, where it barely showed; under real light it would stand
#: out as a cut-out and throw a shadow. So while it is black it is not there to any ray: it is
#: not seen, casts nothing and reflects nothing; and the moment the film gives it a colour it is.
#: This reads the film's own reveal, the object's colour, and nothing else: there is no second
#: timing. Station bodies, routing, cells, the pit and everything in the room are not in these
#: classes and are drawn black when they are black.
UNREVEALED = ("kit", "kit_floor", "bar", "kit_energy")


_RAYS = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter",
         "visible_shadow")


def _unannounced(anim, obj):
    """Ties whether any ray can meet an object to whether the film has given it a colour.

    Each ray-visibility switch follows the object's own colour channel, the very function the
    film animates it with: off while that is black, on the moment it is not. It adds no timing
    of its own; change the film's reveal and this follows. (A see-through material would do the
    same, but many of these objects stand exactly on the surface under them, and a ray that
    passes through one face of such a pair is liable to miss the other. A driver would too, but
    an object driving itself from its own colour is a dependency cycle.)"""
    colour = None
    for target, path, fn in anim._channels:
        if path == "color" and target == obj:
            colour = fn
    rest = tuple(obj.color)

    def there(t):
        value = colour(t) if colour is not None else rest
        return 1.0 if max(value[0], value[1], value[2]) > 0.0 else 0.0

    for path in _RAYS:
        anim.add(obj, path, there)


#: Emission strength of the film's energy surfaces (cells, conduits, chute mouths), and of the
#: room's practical sources (ceiling panels, the lamp's face). The practical ones are held lower
#: so that when the film dims them they are seen to dim, and do not simply clip to white.
EMISSION = {"energy": 4.0, "practical": 1.8}
#: The highest channel of an energy surface's colour when the film has it idle, with a margin.
IDLE = 0.05


#: How a scrawl is made to read as a trace in its surface and not as a thing lying on it.
#: Degrees its two lips are tilted toward each other (an incised groove, shallow); the size in
#: metres of the grain that frays its edges; and how much of the width at the very edge survives.
SCRAWL_GROOVE = 20.0
SCRAWL_GRAIN = 0.045
SCRAWL_EDGE = 0.95
#: Factor on a scrawl's tone, in the material only.
SCRAWL_LIFT = 1.18


def _axis(index):
    return tuple(1.0 if i == index else 0.0 for i in range(3))


def _scrawl(kind):
    """A scratch. Of every box of a trace only the face lying in the surface is drawn, so no
    box has sides, ends or joints, and the trace has no thickness; across its
    width the normal tips inward a little from each side, as the two lips of a shallow cut; its
    edges are frayed by a fine grain fixed in the world, which runs on unbroken from box to box;
    it has no highlight and throws no shadow. Its colour is the film's, untouched."""
    out, across = SCRAWLS[kind]
    material = bpy.data.materials.new("PD_Look_" + kind)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    info = nodes.new("ShaderNodeObjectInfo")
    geometry = nodes.new("ShaderNodeNewGeometry")
    coordinate = nodes.new("ShaderNodeTexCoord")

    def world(axis):
        node = nodes.new("ShaderNodeVectorTransform")
        node.vector_type = "NORMAL"
        node.convert_from, node.convert_to = "OBJECT", "WORLD"
        node.inputs["Vector"].default_value = axis
        unit = nodes.new("ShaderNodeVectorMath")
        unit.operation = "NORMALIZE"
        links.new(node.outputs["Vector"], unit.inputs[0])
        return unit.outputs["Vector"]

    def math(operation, a, b=None, clamp=False):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        node.use_clamp = clamp
        for socket, value in zip(node.inputs, (a, b)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]

    def vector(operation, a, b=None, scale=None):
        node = nodes.new("ShaderNodeVectorMath")
        node.operation = operation
        links.new(a, node.inputs[0])
        if b is not None:
            links.new(b, node.inputs[1])
        if scale is not None:
            if isinstance(scale, (int, float)):
                node.inputs["Scale"].default_value = scale
            else:
                links.new(scale, node.inputs["Scale"])
        return node

    # The surface's own normal, turned to face whoever is looking.
    outward = world(_axis(out))
    facing = vector("DOT_PRODUCT", outward, geometry.outputs["Incoming"]).outputs["Value"]
    flat = vector("SCALE", outward, scale=math("SIGN", facing)).outputs["Vector"]
    # Where across the trace this point is: -1 at one edge, 0 in the middle, 1 at the other.
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coordinate.outputs["Object"], split.inputs["Vector"])
    place = math("MULTIPLY", split.outputs[across], 2.0)
    # The two lips of a cut face each other across it: under light from above the upper lip
    # is in shade and the lower one catches it, which is what tells a cut from a ridge.
    tip = math("MULTIPLY", place, math_tan(SCRAWL_GROOVE))
    lean = vector("SCALE", world(_axis(across)), scale=tip).outputs["Vector"]
    normal = vector("NORMALIZE", vector("ADD", flat, lean).outputs["Vector"]).outputs["Vector"]

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    # Its tone is the film's, lifted a little in the material only, so that a line this thin
    # survives motion and compression. The object's colour is not touched.
    lifted = nodes.new("ShaderNodeVectorMath")
    lifted.operation = "SCALE"
    links.new(info.outputs["Color"], lifted.inputs[0])
    lifted.inputs["Scale"].default_value = SCRAWL_LIFT
    links.new(lifted.outputs["Vector"], bsdf.inputs["Base Color"])
    links.new(normal, bsdf.inputs["Normal"])

    # Frayed edges: whole in the middle, eaten away toward either edge by a grain that belongs
    # to the wall or the floor, not to the box.
    grain = nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 1.0 / SCRAWL_GRAIN
    grain.inputs["Detail"].default_value = 2.0
    links.new(geometry.outputs["Position"], grain.inputs["Vector"])
    edge = math("ABSOLUTE", place)
    kept = math("ADD", grain.outputs[0], math("MULTIPLY", math("SUBTRACT", 1.0, edge), 0.9))
    solid = math("GREATER_THAN", kept, SCRAWL_EDGE)
    # Only the face that lies in the surface is drawn. A box's sides and ends are what make a
    # run of boxes look like a chain: without them there is no thickness and there are no joints.
    square = vector("DOT_PRODUCT", outward, geometry.outputs["True Normal"]).outputs["Value"]
    solid = math("MULTIPLY", solid, math("GREATER_THAN", math("ABSOLUTE", square), 0.5))
    # Nothing of it stands in the way of light: it is in the surface, and casts nothing.
    path = nodes.new("ShaderNodeLightPath")
    seen = math("MULTIPLY", solid, math("SUBTRACT", 1.0, path.outputs["Is Shadow Ray"]))
    mix = nodes.new("ShaderNodeMixShader")
    links.new(seen, mix.inputs["Fac"])
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs["BSDF"], mix.inputs[1])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    # Where two boxes of a trace overlap, their faces lie in the same plane and each would
    # shade the other black: the "dark joints". Shadow rays have to be allowed through.
    for holder in (material, getattr(material, "cycles", None)):
        if holder is not None and hasattr(holder, "use_transparent_shadow"):
            holder.use_transparent_shadow = True
    return material


def math_tan(degrees):
    return math.tan(math.radians(degrees))


def _value(nodes, links, color):
    """A socket carrying the highest channel of ``color``, times four, clamped, halved: the
    ordinary 0.5 of specular for anything with a value, and none for black."""
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(color, split.inputs["Color"])
    high = nodes.new("ShaderNodeMath")
    high.operation = "MAXIMUM"
    links.new(split.outputs[0], high.inputs[0])
    links.new(split.outputs[1], high.inputs[1])
    highest = nodes.new("ShaderNodeMath")
    highest.operation = "MAXIMUM"
    links.new(high.outputs[0], highest.inputs[0])
    links.new(split.outputs[2], highest.inputs[1])
    level = nodes.new("ShaderNodeMath")
    level.operation = "MULTIPLY"
    level.use_clamp = True
    links.new(highest.outputs[0], level.inputs[0])
    level.inputs[1].default_value = 4.0
    half = nodes.new("ShaderNodeMath")
    half.operation = "MULTIPLY"
    links.new(level.outputs[0], half.inputs[0])
    half.inputs[1].default_value = 0.5
    return half.outputs[0]


def _emitter(kind):
    """An energy surface. Like every other surface here, it answers light only as far as the
    film has it lit: a conduit that carries nothing is not picked out by a highlight."""
    material = bpy.data.materials.new("PD_Look_" + kind)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    strength = EMISSION["energy" if kind == "kit_energy" else kind]
    info = nodes.new("ShaderNodeObjectInfo")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4
    links.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
    # The film leaves an idle energy surface almost, not quite, black (a twenty-fifth of its
    # colour). Flat shading shows that as dark; emission would show it as faintly lit, and a
    # cell that is meant to be off would read as on. So the idle level emits nothing, and
    # emission comes in just above it.
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(info.outputs["Color"], split.inputs["Color"])
    high = nodes.new("ShaderNodeMath")
    high.operation = "MAXIMUM"
    links.new(split.outputs[0], high.inputs[0])
    links.new(split.outputs[1], high.inputs[1])
    highest = nodes.new("ShaderNodeMath")
    highest.operation = "MAXIMUM"
    links.new(high.outputs[0], highest.inputs[0])
    links.new(split.outputs[2], highest.inputs[1])
    above = nodes.new("ShaderNodeMapRange")
    above.clamp = True
    above.inputs["From Min"].default_value = IDLE
    above.inputs["From Max"].default_value = IDLE + 0.12
    above.inputs["To Min"].default_value = 0.0
    above.inputs["To Max"].default_value = strength
    links.new(highest.outputs[0], above.inputs["Value"])
    if kind == "kit_energy":
        # A station's cell confirms when the state reaches its ring: a little more of its own light.
        more = nodes.new("ShaderNodeAttribute")
        more.attribute_type = "OBJECT"
        more.attribute_name = GLOW
        gate = nodes.new("ShaderNodeMath")
        gate.operation = "MULTIPLY"
        gate.use_clamp = True
        links.new(above.outputs["Result"], gate.inputs[0])
        gate.inputs[1].default_value = 1000.0                       # on only where the cell itself is on
        extra = nodes.new("ShaderNodeMath")
        extra.operation = "MULTIPLY"
        links.new(more.outputs["Fac"], extra.inputs[0])
        links.new(gate.outputs[0], extra.inputs[1])
        total = nodes.new("ShaderNodeMath")
        total.operation = "ADD"
        links.new(above.outputs["Result"], total.inputs[0])
        links.new(extra.outputs[0], total.inputs[1])
        # And it can give its light up: a receiver's cell goes down while it takes.
        less = nodes.new("ShaderNodeAttribute")
        less.attribute_type = "OBJECT"
        less.attribute_name = DIM
        kept = nodes.new("ShaderNodeMath")
        kept.operation = "SUBTRACT"
        kept.inputs[0].default_value = 1.0
        links.new(less.outputs["Fac"], kept.inputs[1])
        dimmed = nodes.new("ShaderNodeMath")
        dimmed.operation = "MULTIPLY"
        links.new(total.outputs[0], dimmed.inputs[0])
        links.new(kept.outputs[0], dimmed.inputs[1])
        links.new(dimmed.outputs[0], bsdf.inputs["Emission Strength"])
    else:
        links.new(above.outputs["Result"], bsdf.inputs["Emission Strength"])
    links.new(_value(nodes, links, info.outputs["Color"]), bsdf.inputs["Specular IOR Level"])
    links.new(bsdf.outputs["BSDF"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


def assign_materials(scene, materials, anim):
    """Gives every opaque object the material of its class, and every energy surface one that
    answers light only as far as it is lit. Translucent and plane materials are left as they
    are. Returns how many objects each class has."""
    made, counts = {}, {}
    for obj in scene.objects:
        if obj.type != "MESH" or not obj.material_slots:
            continue
        slot = obj.material_slots[0]
        if slot.material is materials.energy:
            kind = ("practical" if obj.name.startswith(("LightPanel", "LampFace"))
                    else "kit_energy" if obj.name.startswith("Station") else "energy")
            if kind not in made:
                made[kind] = _emitter(kind)
        elif slot.material is materials.opaque:
            kind = classify(obj)
            name = obj.name.split(".")[0]
            if kind == "wall" and name in SHELL:
                kind = "shell"
                obj[SCALE] = _world_scale(obj)
                obj[TONE] = SHELL_TONE_BY_NAME.get(name, SHELL_TONE)
                if kind not in made:
                    made[kind] = _shell()
            # Architecture tiles a low-resolution map in metres; props take one texture per face.
            if kind in LEVEL_STRUCTURE:
                obj[SCALE] = _world_scale(obj)
                obj[TONE] = LEVEL_TONE
                if kind not in made:
                    made[kind] = _surface(kind, retro=(LEVEL_MAP, LEVEL_TILE))
            if kind == "waste":
                obj[SCALE] = _world_scale(obj)
                obj[TONE] = WASTE_TONE
                if kind not in made:
                    made[kind] = _surface(kind, retro=(WASTE_MAP, WASTE_TILE))
            if kind in ("kit", "debris") and kind not in made:
                made[kind] = _prop("PD_Look_" + kind, kind)
            if kind == "display":
                _drive_screen(anim, obj)
                form = screens.video_format()
                if form is not None and form["layout"] == "feeds":
                    # Every screen its own monitor: its own material, playing the footage from
                    # its own point.
                    cell = "%d,%d" % (int(round((obj.location[2] - 1.25) / 2.25)), int(round((obj.location[0] + 5.2) / 2.6)))
                    slot.material = _display(feed=form["screens"][cell]["offset"])
                    counts[kind] = counts.get(kind, 0) + 1
                    continue
                if kind not in made:
                    made[kind] = _display()
            if kind == "body_shell" and kind not in made:
                made[kind] = _prop("PD_Look_body_shell", "body_shell", *BODY_TONE)
            if kind == "fixture" and kind not in made:
                made[kind] = _prop("PD_Look_fixture", "fixture")
            if kind == "chamber_floor":
                obj[SCALE] = _world_scale(obj)
                obj[TONE] = FLOOR_TONE
                if kind not in made:
                    made[kind] = _retro("PD_Look_chamber_floor", "chamber_floor", FLOOR_MAP, FLOOR_TILE)
            if kind not in made:
                made[kind] = _scrawl(kind) if kind in SCRAWLS else _surface(kind)
        else:
            continue
        slot.material = made[kind]
        if kind in UNREVEALED:
            _unannounced(anim, obj)
        if kind in SCRAWLS:
            # A trace is seen and nothing else. Where two of its boxes overlap their faces lie
            # in one plane, and rays leaving one meet the other at no distance at all, which
            # shades every joint black. A scratch does not light or shade anything anyway.
            obj.visible_shadow = False
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_transmission = False
        counts[kind] = counts.get(kind, 0) + 1
    return counts


# ---------------------------------------------------------------- light

#: The station level's one key: a low, cold, distant source. W/m2, the unit direction it travels
#: in, and its angular size in degrees.
LEVEL_KEY = (2.2, (0.75, 0.35, -0.56), 1.5)
LEVEL_KEY_COLOR = (0.86, 0.93, 1.0)
#: What the level gets from everywhere else: very little.
LEVEL_AMBIENT = 0.012
#: The pit: a broad dim source under its ceiling, so that the waste is there to be made out and
#: no more. Metres square, height, watts.
PIT_FILL = (420.0, -0.9, 90000.0)
#: The room: watts of each broad fill above the ceiling, and of the lamp over the plinth.
ROOM_FILL = 220.0
ROOM_LAMP = 1300.0
#: How far the light leans with the music: the fraction of a light's strength that the low band
#: can add. It is small, smoothed over about a beat, and never takes anything to black.
LEAN = 0.14


def _lean(t):
    """1.0 at silence, up to 1 + LEAN at the track's loudest low end."""
    return 1.0 + LEAN * audio.level("low", t)


def drive_emission(scene, anim):
    """Gives every piece of the level that responds, and every station's cell, its value over
    time. The value is a custom property of the object: it is not its colour, its place or its
    visibility, and the preview never reads it. Returns how many objects carry one."""
    by_name = {obj.name: obj for obj in scene.objects}

    def named(base, n):
        return by_name.get(base if n == 0 else "%s.%03d" % (base, n))

    count, seen = 0, {}
    for index, piece in enumerate(hinge.pieces()):
        base = "Level" + piece.kind.capitalize()
        n = seen.get(base, 0)
        seen[base] = n + 1
        obj = named(base, n)
        if obj is None:
            continue
        if piece.kind == "via" and abs(piece.center[0] - hinge.column_x(hinge.BUS_TRUNK_COLUMN)) < 0.01:
            # A junction block on the heavy trunk is exactly as high as the trunk, so their tops
            # lie in one plane and each shades the other black (as the boxes of a scrawl did).
            # Such a block is seen, and takes no other part in the light.
            obj.visible_shadow = False
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_transmission = False
        if emission.part(piece, index) is None and emission.climax_part(piece, index) is None:
            continue
        obj[GLOW] = 0.0
        if os.environ.get("PD_NO_EMISSION"):
            # Review only: the same build with the network layer switched off.
            continue
        anim.add(obj, '["%s"]' % GLOW, lambda t, piece=piece, index=index: emission.level(piece, index, t))
        cut = emission.cut_end(piece)
        if cut is not None:
            obj[CUT_AT], obj[CUT_SIDE] = cut[1], float(cut[2])
        if piece.kind in ("trunk", "main"):
            obj[RUN_WIDTH] = piece.size[0] if piece.kind == "trunk" else piece.size[1]
            for layer, name in enumerate(DENSE):
                obj[name] = 0.0
                anim.add(obj, '["%s"]' % name, lambda t, piece=piece, layer=layer: emission.dense(piece, layer, t))
        if (emission.part(piece, index) or ("",))[0] == "junction":
            obj[SOURCE] = 0.0
            anim.add(obj, '["%s"]' % SOURCE, emission.source_level)
        count += 1
    for n, kit in enumerate(refrain.kits() + refrain.later_kits()):
        obj = named("StationHeadCell", n)
        if obj is None:
            continue
        obj[GLOW] = 0.0
        if os.environ.get("PD_NO_EMISSION"):
            continue
        anim.add(obj, '["%s"]' % GLOW, lambda t, kit=kit: emission.cell_level(kit, t))
        obj[DIM] = 0.0
        anim.add(obj, '["%s"]' % DIM, lambda t, kit=kit: emission.cell_dim(kit, t))
        count += 1
    return count


def _keep_off(light, objects, name):
    """Stops ``light`` from lighting ``objects`` directly. Everything else is lit as before, and
    the objects still receive every other light and all indirect light."""
    excluded = bpy.data.collections.new(name)
    for obj in objects:
        excluded.objects.link(obj)
    light.light_linking.receiver_collection = excluded
    for entry in excluded.collection_objects:
        entry.light_linking.link_state = "EXCLUDE"
    return len(excluded.objects)


def _room_fill(t):
    """Factor on the room's broad fills. Inside the film they lean a little with the music;
    elsewhere they are constant. They do not follow the room's authored level: that is already
    in every object's colour, and dimming the fills as well darkens the room twice."""
    return _lean(t) if outer.room_light(t) >= 1.0 else 1.0


def _lamp_state(t):
    """Factor on the lamp over the plinth: the lamp is on when the film has it on.

    In the opening it is off until READY (0:30), when the film lights the lamp's pool and the
    lamp docks; so the tray, the plinth and the body are not lit by a lamp that is not yet on,
    and READY is the lamp's light arriving. After the cut it is at the room's level until the
    film lights the plinth and the lamp (4:35.7). Inside the film it is on."""
    zones = outer.zone_levels(t)
    if outer.in_opening(t):
        return zones[6]
    if t > outer.CODA_START:
        return max(outer.room_light(t), zones[4], zones[6])
    return 1.0


def _sky(world, background):
    """What the camera sees of the world: the fog's colour at the horizon, black above. Light and
    reflections still take the world's ambient only."""
    nodes, links = world.node_tree.nodes, world.node_tree.links
    output = next(n for n in nodes if n.bl_idname == "ShaderNodeOutputWorld")
    coords = nodes.new("ShaderNodeTexCoord")
    look = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"], look.inputs["Vector"])
    rise = nodes.new("ShaderNodeMapRange")
    rise.interpolation_type = "SMOOTHSTEP"
    rise.inputs["From Min"].default_value, rise.inputs["From Max"].default_value = FOG_RISE
    rise.inputs["To Min"].default_value, rise.inputs["To Max"].default_value = 1.0, 0.0
    links.new(look.outputs["Z"], rise.inputs["Value"])
    sky = nodes.new("ShaderNodeBackground")
    sky.inputs["Color"].default_value = FOG_COLOUR + (1.0,)
    links.new(rise.outputs["Result"], sky.inputs["Strength"])
    path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    links.new(background.outputs["Background"], mix.inputs[1])
    links.new(sky.outputs["Background"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])


def build_lights(geo, anim, scene):
    """Lights for what the preview drew with flat shading: the level above the pit, and the pit."""
    strength, direction, angle = LEVEL_KEY
    data = bpy.data.lights.new("LevelKey", "SUN")
    data.energy = strength
    data.angle = math.radians(angle)
    data.color = LEVEL_KEY_COLOR
    key = bpy.data.objects.new("LevelKey", data)
    geo.collection.objects.link(key)
    key.location = (0.0, 0.0, 200.0)
    key.rotation_mode = "QUATERNION"
    key.rotation_quaternion = q_camera_look(direction, Z)
    anim.add(data, "energy", lambda t: strength * _lean(t))
    # The key belongs to the level. While the pit's ceiling is open (1:57.5 to 2:15) it would
    # otherwise fall straight onto the waste, which would then compete with the routing above
    # it. The waste keeps the pit's own light and whatever the level throws down indirectly.
    waste = [obj for obj in scene.objects if obj.type == "MESH" and classify(obj) in ("debris", "waste", "pit")]
    kept_off = _keep_off(key, waste, "PD_KeyExcludes")
    print("[pd] look: level key kept off %d objects of the pit" % kept_off)

    span, height, watts = PIT_FILL
    data = bpy.data.lights.new("PitFill", "AREA")
    data.shape = "SQUARE"
    data.size = span
    data.energy = watts
    data.color = (0.9, 0.95, 1.0)
    fill = bpy.data.objects.new("PitFill", data)
    geo.collection.objects.link(fill)
    from ..core import landfill
    centre = landfill.frame()["centre"]
    fill.location = (centre[0], centre[1], height)
    fill.rotation_mode = "QUATERNION"
    fill.rotation_quaternion = q_camera_look((0.0, 0.0, -1.0), (0.0, 1.0, 0.0))
    fill.visible_camera = False
    anim.add(data, "energy", lambda t: watts * _lean(t))

    # The room's own lights lean too, and only inside the film: in the opening and the ending
    # the room's light is the film's own and is left alone.
    stage_lamp = bpy.data.objects.get("Lamp")
    if stage_lamp is not None:
        # The lamp is the authored source: its light goes where it goes. (Inside the film it is
        # docked, so this is its rest; it moves only in the opening and after the cut.) The
        # stage's own light object is part of the locked picture and is left where it is, dark;
        # the look's spot is a copy of it that moves.
        lamp = stage_lamp.data.copy()
        lamp.name = "LampSpot"
        stage_lamp.data.energy = 0.0
        spot = bpy.data.objects.new("LampSpot", lamp)
        for collection in stage_lamp.users_collection:
            collection.objects.link(spot)
        spot.rotation_mode = stage_lamp.rotation_mode
        spot.rotation_quaternion = stage_lamp.rotation_quaternion
        spot.rotation_euler = stage_lamp.rotation_euler
        spot.location = stage_lamp.location
        lamp.energy = ROOM_LAMP
        anim.add(lamp, "energy", lambda t: ROOM_LAMP * _lamp_state(t))
        rest = tuple(stage_lamp.location)
        anim.add(spot, "location", lambda t, rest=rest: (rest[0], rest[1], rest[2] + outer.lamp_height(t)))
    for name in ("CeilingFront", "CeilingBack"):
        light = bpy.data.lights.get(name)
        if light is not None:
            # The room is lit by what can be seen to light it: its ceiling panels and the lamp
            # over the plinth. The broad sources above the ceiling only lift the shadows.
            light.energy = ROOM_FILL
            rest = light.energy
            anim.add(light, "energy", lambda t, rest=rest: rest * _room_fill(t))

    # The black shell that stands in for distance must not stand between the level and its light;
    # and the camera does not see it either: it would be a wall at the end of the world. In its
    # place the camera sees the fog's own gradient (below), so the distance has no edge.
    for obj in scene.objects:
        if obj.name.startswith("LevelShell"):
            obj.visible_shadow = False
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_camera = False

    world = scene.world
    if world is not None and world.node_tree is not None:
        background = world.node_tree.nodes.get("Background")
        if background is not None:
            background.inputs["Color"].default_value = (0.55, 0.62, 0.70, 1.0)
            background.inputs["Strength"].default_value = LEVEL_AMBIENT
            _sky(world, background)


def render_settings(scene, profile):
    if scene.render.engine != "CYCLES":
        return
    cycles = scene.cycles
    cycles.max_bounces = 4
    cycles.diffuse_bounces = 2
    cycles.glossy_bounces = 3
    cycles.transmission_bounces = 2
    cycles.transparent_max_bounces = 32      # a trace is many see-through faces deep where its boxes meet
    cycles.volume_bounces = 0
    cycles.caustics_reflective = False
    cycles.caustics_refractive = False
    cycles.sample_clamp_indirect = 4.0
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.03
    cycles.use_denoising = profile.denoise
    # A one-pixel box filter: no blending across neighbouring pixels, so the shell's texels and
    # every geometric edge stay hard (approved 2026-10-19 as part of the film's look; Cycles'
    # default is a 1.5 px Blackman-Harris). The denoiser is guided by albedo and normals, which
    # keeps texel boundaries in the albedo sharp.
    cycles.pixel_filter_type = "BOX"
    cycles.filter_width = 1.0
    cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    cycles.denoising_prefilter = "ACCURATE"
    try:
        cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass


#: The pull-out's sense of an endless network (look only, 2026-10-20). Simplified static copies
#: of the network's structure (its runs, junction blocks and station bodies, as boxes at rest) are
#: laid around it, one tile on each side and corner, each turned a quarter further so that the
#: repetition does not read; the long fog takes them before they can be compared. They carry the
#: network's tiled surface and no emission. They are lit only for the pull-out: black before the
#: climax (so the 2:20-4:00 reveal is the film's own), up over its first bars, black from 4:15.
ECHO_CLASSES = ("trunk", "via", "fine", "main", "station")
ECHO_GREY = 0.12
ECHO_SPACING = 420.0
ECHO_RISE = 8.0


def _echo_light(t):
    if t >= outer.CODA_START:
        return 0.0
    return smoother(window(t, climax.START, climax.START + ECHO_RISE))


def build_echoes(scene, anim):
    """Adds the echo tiles (see ECHO_*). Returns how many tiles."""
    bpy.context.view_layer.update()
    pieces = [o for o in scene.objects if o.type == "MESH" and classify(o) in ECHO_CLASSES]
    if not pieces:
        return 0
    verts, faces = [], []
    lo, hi = [1e9, 1e9], [-1e9, -1e9]
    for o in pieces:
        m = o.matrix_world
        base = len(verts)
        for v in o.data.vertices:
            p = m @ v.co
            verts.append((p.x, p.y, p.z))
            lo, hi = [min(lo[0], p.x), min(lo[1], p.y)], [max(hi[0], p.x), max(hi[1], p.y)]
        faces.extend([tuple(base + i for i in poly.vertices) for poly in o.data.polygons])
    cx, cy = (lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5
    # The mesh is centred on the network's own centre, so a tile can turn about it.
    mesh = bpy.data.meshes.new("PD_Echo")
    mesh.from_pydata([(x - cx, y - cy, z) for x, y, z in verts], [], faces)
    mesh.update()
    material = _surface("echo", retro=(LEVEL_MAP, LEVEL_TILE))
    mesh.materials.append(material)
    k = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            k += 1
            echo = bpy.data.objects.new("LevelEcho", mesh)
            scene.collection.objects.link(echo)
            echo.location = (cx + dx * ECHO_SPACING, cy + dy * ECHO_SPACING, 0.0)
            echo.rotation_euler = (0.0, 0.0, math.radians(90.0 * k))
            echo[SCALE] = (1.0, 1.0, 1.0)
            echo[TONE] = LEVEL_TONE
            echo.color = (0.0, 0.0, 0.0, 1.0)
            anim.add(echo, "color", lambda t: (ECHO_GREY * _echo_light(t),) * 3 + (1.0,))
            # While black they are not there to any ray: a black shape in the fog would stand as
            # a dark skyline against the brighter horizon before the climax.
            _unannounced(anim, echo)
    return k


#: Whether a build with the look insists on every asset the film's look reads. Only the tool that
#: measures the lyric layout (and so makes assets/lyrics/layout.json) turns this off.
REQUIRE_ASSETS = True


def required_assets():
    """Every file the look reads, by project-relative location. A look build without one of them would
    not fail on its own but quietly lose something (no lyric, the old screen content), so it is
    checked up front."""
    from ..core import audio
    files = [lyrics.LAYOUT, os.path.join(screens.VIDEO, "manifest.json"), glyphs.FONT, audio._FILE,
             SHELL_MAP, FLOOR_MAP, PROP_MAP, LEVEL_MAP, WASTE_MAP]
    form = screens.video_format()
    if form is not None and form["layout"] == "feeds":
        files.append(os.path.join(screens.VIDEO, form["stream"]))
    return files


def apply(geo, materials, anim, scene, profile):
    """Everything the look adds. Returns {class: object count}, or None if the profile has no look."""
    if not profile.look:
        return None
    if REQUIRE_ASSETS:
        missing = [f for f in required_assets() if not os.path.exists(f)]
        if missing:
            raise FileNotFoundError("The look needs these files, and they are missing (see docs/final_render.md, "
                                    "Render assets; tools/assets_manifest.py --verify):\n  " + "\n  ".join(missing))
    counts = assign_materials(scene, materials, anim)
    print("[pd] look: %d CRT lines, %d lines as text in the scene, %d coda marks give way to the lyric" % (
        len(lyrics.crt_lines()), build_lyric_text(scene, anim), _yield_to_lyric(anim, scene)))
    print("[pd] look: %d echo tiles round the network" % build_echoes(scene, anim))
    print("[pd] look: %d objects carry a network response" % drive_emission(scene, anim))
    build_lights(geo, anim, scene)
    render_settings(scene, profile)
    return counts
