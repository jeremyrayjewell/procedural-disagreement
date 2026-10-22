"""The clinical chamber: a long ribbed room with ceiling light panels, a central plinth and an
overhead lamp. Static. The shell and all major fixtures are identical in every profile; dense
profiles add seeded pipework along the walls."""

from ..core import choreography as ch
from ..core import layout, outer, stablehash
from ..core.vec import add, q_rotate
from . import materials as mat


def _lean_from_foot(anim, rib, rest, lean):
    """Lets a rib lean about its foot by ``lean(t)``: its centre swings, its base stays put."""
    half = rest[2]
    foot = (rest[0], rest[1], 0.0)
    anim.add(rib, "rotation_quaternion", lean)
    anim.add(rib, "location", lambda t: add(foot, q_rotate(lean(t), (0.0, 0.0, half))))


def _carriage(anim, cabinet, x, y, h):
    """One cabinet runs along the wall rail and extends upward from its base (see choreography)."""
    rest = tuple(cabinet.scale)

    def location(t):
        slide, extension = ch.reindex_carriage(t)
        return (x, y - slide, (h + extension) * 0.5)

    anim.add(cabinet, "location", location)
    anim.add(cabinet, "scale", lambda t: (rest[0], rest[1], rest[2] * (h + ch.reindex_carriage(t)[1]) / h))


def build(geo, materials, anim, profile, seed, phantom):
    """``phantom`` is the variant whose absent limb loads the room (see choreography)."""
    root = geo.empty("Chamber")
    opaque, energy = materials.opaque, materials.energy

    half = layout.CHAMBER_HALF_WIDTH
    height = layout.CHAMBER_HEIGHT
    y_min, y_max = layout.CHAMBER_Y_MIN, layout.CHAMBER_Y_MAX
    length = y_max - y_min
    y_mid = (y_max + y_min) * 0.5

    # Shell.
    geo.box("Floor", root, (0, y_mid, -0.1), (half * 2 + 0.4, length + 0.4, 0.2), opaque, mat.FLOOR)
    geo.box("Ceiling", root, (0, y_mid, height + 0.1), (half * 2 + 0.4, length + 0.4, 0.2), opaque, mat.WALL)
    for side in (-1, 1):
        geo.box("Wall", root, (side * (half + 0.1), y_mid, height * 0.5), (0.2, length, height), opaque, mat.WALL)
    geo.box("WallBack", root, (0, y_max + 0.1, height * 0.5), (half * 2, 0.2, height), opaque, mat.WALL)
    geo.box("WallFront", root, (0, y_min - 0.1, height * 0.5), (half * 2, 0.2, height), opaque, mat.WALL)

    # Ribs and a dark band along the side walls give the approach its parallax.
    recruited = 0
    for y in layout.rib_ys():
        for side in (-1, 1):
            rib = geo.box("Rib", root, layout.rib_position(side, y), layout.RIB_SIZE, opaque, mat.WALL)
            if side == layout.RECRUITED_RIB_SIDE and y == layout.RECRUITED_RIB_Y:
                # The body moves this one as the distal segment of its missing limb.
                # It is the only rib in the room that ever moves.
                _lean_from_foot(anim, rib, layout.rib_position(side, y), lambda t: ch.recruited_rotation(phantom, t))
                recruited += 1
    if recruited != 1:
        raise ValueError("The recruited rib (y = %s) matched %d ribs; it must match exactly one. "
                         "Ribs stand at y = %s." % (layout.RECRUITED_RIB_Y, recruited, layout.rib_ys()))
    for side in (-1, 1):
        geo.box("Band", root, (side * (half - 0.06), y_mid, 1.1), (0.12, length, 0.08), opaque, mat.TRIM)
        # Floor channels converge on the plinth.
        geo.box("Channel", root, (side * 2.4, y_mid, 0.011), (0.12, length, 0.02), opaque, mat.TRIM)

    # Where the receiver stops, the +x channel can open into an aperture. Closed, this plate is
    # exactly as wide as the channel and the same colour, so it cannot be told from it.
    stop = add(layout.RECEIVER_POSITION, layout.DISPOSAL_ROUTE)
    across, along = layout.DISPOSAL_APERTURE
    aperture = geo.box("Aperture", root, (layout.FLOOR_CHANNEL_X, stop[1], 0.012),
                       (layout.FLOOR_CHANNEL_WIDTH, along, 0.021), opaque, mat.TRIM)
    closed = tuple(aperture.scale)
    widen = across / layout.FLOOR_CHANNEL_WIDTH
    anim.add(aperture, "scale", lambda t: (closed[0] * (1.0 + (widen - 1.0) * ch.disposal_aperture(t)), closed[1], closed[2]))

    # Back wall panels with seeded relief.
    for row in range(3):
        for col in range(5):
            depth = stablehash.uniform(seed, row * 5 + col, 0.05, 0.18)
            center = (-5.2 + col * 2.6, y_max - depth * 0.5, 1.25 + row * 2.25)
            panel = geo.box("Panel", root, center, (2.35, depth, 2.0), opaque, mat.FIXTURE)
            if (row, col) == layout.ATTRACTOR_PANEL:
                anim.add(panel, "rotation_quaternion", lambda t: ch.panel_attend(phantom, t))
                # Before the case it stands a little out of its place along the wall.
                anim.add(panel, "location", lambda t, center=center: (center[0] + outer.opening_panel(t), center[1], center[2]))

    # Ceiling light panels.
    y = y_min + 3.0
    while y < y_max:
        for side in (-1, 1):
            geo.box("LightPanel", root, (side * 2.6, y, height - 0.04), (2.2, 0.7, 0.06), energy, mat.LIGHT_PANEL)
        y += 4.0

    # Seeded cabinets along the side walls. The bay around y = 6.5 is kept clear for the conduit drops.
    carriages = 0
    for i in range(layout.CABINET_COUNT):
        for side in (-1, 1):
            spec = layout.cabinet(seed, i, side)
            if spec is None:
                continue
            y, h, w = spec
            cabinet = geo.box("Cabinet", root, (side * layout.CABINET_X, y, h * 0.5), (0.6, w, h), opaque, mat.FIXTURE)
            if (i, side) == layout.REINDEX_CABINET:
                _carriage(anim, cabinet, side * layout.CABINET_X, y, h)
                carriages += 1
    if carriages != 1:
        raise ValueError("The re-indexing carriage %r matched %d cabinets; it must match exactly one."
                         % (layout.REINDEX_CABINET, carriages))

    # Plinth the figure stands on.
    geo.cylinder("PlinthStep", root, (0, 0, 0.09), 2.0, 0.18, opaque, mat.FLOOR)
    geo.cylinder("Plinth", root, (0, 0, layout.PLINTH_HEIGHT * 0.5), 1.5, layout.PLINTH_HEIGHT, opaque, mat.FIXTURE)

    # Overhead lamp.
    # It travels on its stem: raised until it docks on the risers. The stem goes up through
    # the ceiling with it.
    for lamp in (geo.cylinder("LampStem", root, (0, 0, (height + 6.17) * 0.5), 0.08, height - 6.17, opaque, mat.TRIM),
                 geo.cylinder("LampBody", root, (0, 0, 6.1), 0.95, 0.14, opaque, mat.FIXTURE),
                 geo.cylinder("LampFace", root, (0, 0, layout.LAMP_UNDERSIDE - 0.01), 0.8, 0.02, energy, mat.LIGHT_PANEL)):
        rest = tuple(lamp.location)
        anim.add(lamp, "location", lambda t, rest=rest: (rest[0], rest[1], rest[2] + outer.lamp_height(t)))

    # Density only: thin horizontal pipes high on the side walls, above anything that moves.
    for i in range(profile.wall_pipes):
        for side in (-1, 1):
            index = 5000 + i * 2 + (1 if side > 0 else 0)
            z = stablehash.uniform(seed, index, 5.6, 6.7)
            inset = stablehash.uniform(seed, index + 1000, 0.42, 0.62)
            radius = stablehash.uniform(seed, index + 2000, 0.015, 0.04)
            pipe = geo.cylinder("WallPipe", root, (side * (half - inset), y_mid, z), radius, length, opaque, mat.STRUCTURE)
            pipe.rotation_quaternion = (0.7071068, 0.7071068, 0.0, 0.0)  # lay along Y

    return root
