"""Materials and reality styles.

Every material reads the object's colour and alpha (Object Info node). That one animated
property carries energy and translucency in all three engines: Workbench shows object colour
directly, EEVEE and Cycles read it through the node tree. So there are only a handful of
materials no matter how many objects or realities are built.
"""

import warnings

import bpy

# Linear RGB.
WALL = (0.35, 0.38, 0.37)
FLOOR = (0.20, 0.22, 0.22)
TRIM = (0.06, 0.07, 0.075)
FIXTURE = (0.44, 0.46, 0.45)
LIGHT_PANEL = (1.0, 1.0, 0.95)
BODY = (0.58, 0.56, 0.51)
JOINT = (0.03, 0.035, 0.04)
STRUCTURE = (0.13, 0.145, 0.16)
ENERGY = (0.22, 0.78, 1.0)
PLANE_A = (0.07, 0.60, 1.0)
PLANE_B = (1.0, 0.30, 0.03)
FOG = (0.50, 0.56, 0.56)

#: Opacity of a cutting plane's sheet at nominal strength; its frame is drawn stronger.
PLANE_SHEET_ALPHA = 0.5

BODY_ROLES = ("body", "joint", "structure")
ENERGY_ROLES = ("conduit", "cell")


class Materials:
    def __init__(self):
        self.opaque = _opaque()
        self.energy = _energy()
        self.ghost = _translucent("PD_Ghost", emission=0.7, rim=True)
        self.plane = _translucent("PD_Plane", emission=1.3, rim=False)

    def volume(self, density):
        material, nodes, links = _new("PD_Volume")
        scatter = nodes.new("ShaderNodeVolumeScatter")
        scatter.inputs["Color"].default_value = FOG + (1.0,)
        scatter.inputs["Density"].default_value = density
        links.new(scatter.outputs["Volume"], nodes.new("ShaderNodeOutputMaterial").inputs["Volume"])
        return material

    def style(self, variant):
        return GhostStyle(self, variant.tint) if variant.ghost else SolidStyle(self)


class SolidStyle:
    """The primary reality: opaque parts, emissive energy."""

    _COLORS = {"body": BODY, "joint": JOINT, "structure": STRUCTURE}

    def __init__(self, materials):
        self._materials = materials

    def material(self, role):
        return self._materials.energy if role in ENERGY_ROLES else self._materials.opaque

    def color(self, role, energy=1.0, opacity=1.0):
        if role in ENERGY_ROLES:
            level = 0.04 + 0.96 * energy
            return (ENERGY[0] * level, ENERGY[1] * level, ENERGY[2] * level, 1.0)
        return self._COLORS[role] + (1.0,)


class GhostStyle:
    """An alternate reality: one translucent tint; energy shows as brightness."""

    _LEVELS = {"body": 0.55, "joint": 0.22, "structure": 0.38}

    def __init__(self, materials, tint):
        self._materials = materials
        self._tint = tint

    def material(self, role):
        return self._materials.ghost

    def color(self, role, energy=1.0, opacity=1.0):
        level = 0.30 + 0.95 * energy if role in ENERGY_ROLES else self._LEVELS[role]
        return (self._tint[0] * level, self._tint[1] * level, self._tint[2] * level, opacity)


# ---------------------------------------------------------------- node trees


def _new(name):
    material = bpy.data.materials.new(name)
    if material.node_tree is None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    return material, nodes, links


def _opaque():
    material, nodes, links = _new("PD_Opaque")
    info = nodes.new("ShaderNodeObjectInfo")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.55
    links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


def _energy():
    material, nodes, links = _new("PD_Energy")
    info = nodes.new("ShaderNodeObjectInfo")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 4.0
    links.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
    links.new(bsdf.outputs["BSDF"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return material


def _translucent(name, emission, rim):
    """Mix of see-through and self-lit colour, weighted by object alpha (and, optionally,
    by how edge-on the surface is, which gives shells a readable outline)."""
    material, nodes, links = _new(name)
    info = nodes.new("ShaderNodeObjectInfo")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    glow = nodes.new("ShaderNodeEmission")
    glow.inputs["Strength"].default_value = emission
    links.new(info.outputs["Color"], glow.inputs["Color"])

    factor = info.outputs["Alpha"]
    if rim:
        weight = nodes.new("ShaderNodeLayerWeight")
        weight.inputs["Blend"].default_value = 0.35
        shaped = nodes.new("ShaderNodeMath")
        shaped.operation = "MULTIPLY_ADD"
        links.new(weight.outputs["Facing"], shaped.inputs[0])
        shaped.inputs[1].default_value = 0.55
        shaped.inputs[2].default_value = 0.45
        scaled = nodes.new("ShaderNodeMath")
        scaled.operation = "MULTIPLY"
        scaled.use_clamp = True
        links.new(shaped.outputs[0], scaled.inputs[0])
        links.new(info.outputs["Alpha"], scaled.inputs[1])
        factor = scaled.outputs[0]

    mix = nodes.new("ShaderNodeMixShader")
    links.new(factor, mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(glow.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])

    # EEVEE: alpha-blend rather than dither. Attribute names differ across versions.
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "BLENDED"
    elif hasattr(material, "blend_method"):
        material.blend_method = "BLEND"
    material.use_backface_culling = False
    return material
