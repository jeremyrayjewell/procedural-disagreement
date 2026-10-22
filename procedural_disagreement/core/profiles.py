"""Render profiles.

A profile may change how the picture is rendered and how densely geometry is built.
It may never change timing, camera, seeds, placement of major geometry or choreography:
none of ``timeline``, ``layout``, ``variants`` or ``choreography`` reads a profile.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class RenderProfile:
    name: str
    #: BLENDER_WORKBENCH, BLENDER_EEVEE or CYCLES.
    engine: str
    width: int
    height: int
    samples: int

    # Geometric density. Silhouettes and positions stay put; only the amount of detail changes.
    cylinder_segments: int
    sphere_segments: int
    #: Each limb slice is split into this many thinner fragments.
    slice_subdivisions: int
    #: Length of one conduit segment, in metres.
    conduit_pitch: float
    #: Edge bevel on boxes, in metres. 0 disables it and lets boxes share one mesh.
    bevel_width: float
    #: Seeded pipes added along each side wall.
    wall_pipes: int
    #: Alternate realities beyond the first, each a seeded variation of the procedure.
    extra_alternates: int

    # Expensive effects.
    volumetric_density: float
    motion_blur: bool
    denoise: bool

    #: Whether the look (materials by class, real light) is applied. Presentation only: it
    #: never changes a transform, a colour, a camera or a cue.
    look: bool = False

    def with_overrides(self, engine=None, samples=None, scale=None):
        changes = {}
        if engine:
            changes["engine"] = engine
        if samples:
            changes["samples"] = samples
        if scale and scale != 100:
            # Keep dimensions even: video encoders require it.
            changes["width"] = max(2, int(self.width * scale / 100) // 2 * 2)
            changes["height"] = max(2, int(self.height * scale / 100) // 2 * 2)
        return replace(self, **changes) if changes else self


#: Practical on integrated graphics: Workbench, a few hundred objects, no volumetrics.
PREVIEW = RenderProfile(
    name="preview",
    engine="BLENDER_WORKBENCH",
    width=640,
    height=360,
    samples=8,
    cylinder_segments=16,
    sphere_segments=12,
    slice_subdivisions=1,
    conduit_pitch=0.40,
    bevel_width=0.0,
    wall_pipes=0,
    extra_alternates=0,
    volumetric_density=0.0,
    motion_blur=False,
    denoise=False,
)

#: For the collaborator's GPU: the approved look's scene exactly as lookdev builds it, at final
#: output quality (director, 2026-10-22). Only resolution and samples differ from LOOKDEV, and the
#: device (a GPU, chosen at render time). It used to add scene content of its own (three more
#: ghost realities, the figure's slices split in four, wall pipes, twice the landfill, twice the
#: conduit segments, smooth primitives, bevels); none of that was ever part of the approved look,
#: so it is gone (docs/final_render.md).
FINAL = RenderProfile(
    name="final",
    engine="CYCLES",
    width=3840,
    height=2160,
    # Provisional: the lowest of the counts the GPU benchmark (tools/benchmark_final.py) compares;
    # set to the lowest that is clean and stable in all four environments.
    samples=128,
    cylinder_segments=16,
    sphere_segments=12,
    slice_subdivisions=1,
    conduit_pitch=0.40,
    bevel_width=0.0,
    wall_pipes=0,
    extra_alternates=0,
    # No haze and no motion blur (decided 2026-10-21): the haze would scatter light into the
    # locked lighting, and depth is the look's camera-only distance fog; early real-time 3D had
    # no motion blur, and hard temporal edges belong to the look.
    volumetric_density=0.0,
    motion_blur=False,
    denoise=True,
    look=True,
)

#: Look development: the preview's own scene, object for object, seen through a lit engine.
#: Enough samples to show problems; not a delivery profile.
LOOKDEV = RenderProfile(
    name="lookdev",
    engine="CYCLES",
    width=1920,
    height=1080,
    samples=48,
    cylinder_segments=16,
    sphere_segments=12,
    slice_subdivisions=1,
    conduit_pitch=0.40,
    bevel_width=0.0,
    wall_pipes=0,
    extra_alternates=0,
    volumetric_density=0.0,
    motion_blur=False,
    denoise=True,
    look=True,
)

PROFILES = {p.name: p for p in (PREVIEW, FINAL, LOOKDEV)}

ENGINES = {
    "workbench": "BLENDER_WORKBENCH",
    "eevee": "BLENDER_EEVEE",
    "cycles": "CYCLES",
}
