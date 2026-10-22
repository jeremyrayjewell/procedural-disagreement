"""The lower space, drawn. Its shape comes from ``core.landfill``: this module only builds it.

A terrain of compacted waste (benches, steep faces, ridges, basins, a berm under every chute),
strata set into the steep faces, debris of the upper world's own parts buried in it at every
depth and angle, discarded limbs, chutes hanging from a ceiling that is never seen, and a few
of those chutes still working while the camera flies over.

Nothing here is visible from the chamber: it all lies under the chamber's opaque floor.
Every placement is a function of (seed, index) and identical in every profile. Dense profiles
use a finer terrain mesh and append more debris after the shared pieces. Thousands of objects
share four meshes; the terrain is a few dozen tiles.
"""

import math

import bmesh
import bpy

from ..core import choreography as ch
from ..core import climax, hinge, network, prosthesis
from ..core import landfill as field
from ..core import layout, stablehash
from ..core.vec import add, q_axis_angle, q_mul
from . import materials as mat
from . import refrain as refrain_scene

#: Name of the collection holding the whole lower space.
COLLECTION = "Landfill"

# Linear RGB. The pit is dark; refuse is the upper world's materials, dulled.
_SHELL = (0.010, 0.011, 0.013)
#: Distance itself: nothing at all.
_VOID = (0.0, 0.0, 0.0)
_WASTE = (0.088, 0.090, 0.086)
_CHUTE = (0.07, 0.075, 0.08)

_TILE = 30.0
#: Shared (preview) counts. Dense profiles double the debris; everything else is fixed.
_DEBRIS = 7000
_ARMS = 170
_STRATA = 300
#: Degrees of elbow flexion on an arm that is disposed of broadside to the camera.
_BROADSIDE_BEND = 50.0


def build(geo, materials, anim, profile, seed):
    upper = geo.collection
    pit = bpy.data.collections.new(COLLECTION)
    upper.children.link(pit)
    geo.collection = pit    # everything below goes in its own collection (see tools/blender_entry.py)
    geo.plain = True        # and every box is an instance of the one shared cube
    try:
        return _build(geo, materials, anim, profile, seed + 7000)
    finally:
        geo.plain = False
        geo.collection = upper


def _build(geo, materials, anim, profile, seed):
    root = geo.empty("Landfill")
    opaque, energy = materials.opaque, materials.energy
    dense = 2 if profile.wall_pipes else 1
    f = field.frame()
    crest, shelf, floor_z, centre = f["crest"], f["shelf"], f["floor"], f["centre"]

    # Shell: darkness. The floor only shows where the waste thins to nothing.
    span = layout.LANDFILL_SPAN
    geo.box("PitFloor", root, (centre[0], centre[1], floor_z - 0.2), (span, span, 0.4), opaque, _SHELL)
    ceiling = geo.box("PitCeiling", root, (centre[0], centre[1], -0.45), (span, span, 0.4), opaque, _SHELL)
    whole = tuple(ceiling.scale)
    # It is there whenever it could be seen from below or stood on (see core.hinge).
    anim.add(ceiling, "scale", lambda t: whole if hinge.ceiling_present(t) else (0.0, 0.0, 0.0))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        size = (0.5, span, -floor_z) if dx else (span, 0.5, -floor_z)
        geo.box("PitWall", root, (centre[0] + dx * span * 0.5, centre[1] + dy * span * 0.5, floor_z * 0.5), size, opaque, _SHELL)

    _terrain(geo, root, opaque, seed, fine=dense > 1)

    make = _Maker(geo, root, opaque)

    # ---- our station
    stop = add(layout.RECEIVER_POSITION, layout.DISPOSAL_ROUTE)
    _chute(geo, root, opaque, energy, (layout.FLOOR_CHANNEL_X, stop[1]), layout.LANDFILL_CHUTE_BOTTOM, 1.0, 0.0, 1.0, 1.0, True)
    pad = geo.box("RefusePlatform", root, (crest[0], crest[1], crest[2] - 0.08), (3.0, 2.2, 0.16), opaque, _tone(mat.STRUCTURE, 0.9))
    pad.rotation_quaternion = q_axis_angle((0.0, 0.0, 1.0), 20.0)
    pad = geo.box("RefusePlatform", root, (shelf[0], shelf[1], shelf[2] - 0.07), (2.6, 1.6, 0.14), opaque, _tone(mat.STRUCTURE, 0.75))
    pad.rotation_quaternion = q_axis_angle((0.0, 0.0, 1.0), -30.0)
    _loose_pieces(geo, root, opaque, anim, crest)

    # ---- every other station's chute, out to where they can no longer be made out
    for station in field.stations():
        near = field.distance_to_flight(station.x, station.y) < 80.0
        visible = max(0.32, field.shade(station.x, station.y))
        _chute(geo, root, opaque, energy, (station.x, station.y), station.bottom, station.scale, station.heading,
               station.glow * visible, visible, near)

    clear = [(crest[0], crest[1], 1.7), (shelf[0], shelf[1], 1.5)] + [(s.x, s.y, 2.2) for s in field.staged_sites()]
    _strata(make, seed + 100, clear)
    _debris(make, seed + 200, clear, dense, crest)
    _arms(make, seed + 300, clear)

    _station_level(geo, root, opaque, anim)
    refrain_scene.build(geo, root, opaque, energy, anim)

    # ---- stations still working: something comes down while the camera flies over
    for index, site in enumerate(field.staged_sites()):
        _chute(geo, root, opaque, energy, (site.x, site.y), site.bottom, 1.1, 30.0 + 50.0 * index, 1.0, 1.0, True)
    for index, event in enumerate(field.events()):
        _disposed(make, anim, event, index)

    return root


# ---------------------------------------------------------------- the level above


def _station_level(geo, root, opaque, anim):
    """The level the chutes hang from: trunks, mains, a unit and a spur for every station, and
    a dark shell standing in for distance. All of it is above the pit's ceiling."""
    for piece in hinge.pieces():
        tone = {"trunk": hinge.TRUNK, "main": hinge.MAIN, "unit": hinge.UNIT, "spur": hinge.SPUR, "via": hinge.VIA,
                "bay": hinge.BAY, "fine": hinge.FINE, "cell": hinge.CELL}[piece.kind]
        obj = geo.box("Level" + piece.kind.capitalize(), root, piece.center, piece.size, opaque, (0.0, 0.0, 0.0))
        anim.add(obj, "color", lambda t, piece=piece, tone=tone: _tone(tone, hinge.visibility(piece, t)) + (1.0,))
        if network.moves(piece) or prosthesis.moves(piece) or climax.moves(piece):
            # A few large structures take part in the procedure after 3:00, a few more in the
            # compensation after 3:30, and from 4:00 most of the level.
            anim.add(obj, "location", lambda t, piece=piece: add(add(
                add(piece.center, network.piece_offset(piece, t)), prosthesis.piece_offset(piece, t)),
                climax.piece_offset(piece, t)))

    cx, cy = hinge.shell_centre()
    radius, height, sides = hinge.SHELL_RADIUS, hinge.SHELL_HEIGHT, 12
    width = 2.0 * radius * math.tan(math.pi / sides) + 2.0
    for k in range(sides):
        angle = 360.0 * k / sides
        a = math.radians(angle)
        wall = geo.box("LevelShell", root, (cx + math.cos(a) * radius, cy + math.sin(a) * radius, hinge.GROUND + height * 0.5),
                       (1.0, width, height), opaque, _VOID)
        wall.rotation_quaternion = q_axis_angle((0.0, 0.0, 1.0), angle)
    geo.box("LevelShell", root, (cx, cy, hinge.GROUND + height), (2.2 * radius, 2.2 * radius, 1.0), opaque, _VOID)
    # The ground of the level runs on beyond the pit's own ceiling, out past the shell.
    centre, half, far = field.frame()["centre"], layout.LANDFILL_SPAN * 0.5, 2.0 * radius
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        size = (far, 2.0 * (half + far), 0.4) if dx else (2.0 * half, far, 0.4)
        geo.box("LevelGround", root, (centre[0] + dx * (half + far * 0.5), centre[1] + dy * (half + far * 0.5), hinge.GROUND - 0.2),
                size, opaque, _SHELL)


# ---------------------------------------------------------------- terrain


def _terrain(geo, root, opaque, seed, fine):
    """The waste surface, as square tiles. Tiles near the flight are finely meshed; further
    out they are coarse and darker; where the field has faded to nothing there are none."""
    f = field.frame()
    half = layout.LANDFILL_SPAN * 0.5 - 10.0
    n = int(2.0 * half / _TILE)
    for i in range(n):
        for j in range(n):
            x0 = f["centre"][0] - half + i * _TILE
            y0 = f["centre"][1] - half + j * _TILE
            cx, cy = x0 + _TILE * 0.5, y0 + _TILE * 0.5
            shade = max(field.shade(x, y) for x, y in ((cx, cy), (x0, y0), (x0 + _TILE, y0), (x0, y0 + _TILE), (x0 + _TILE, y0 + _TILE)))
            if shade <= 0.0:
                continue
            near = field.distance_to_flight(cx, cy) < 70.0
            cells = (30 if fine else 15) if near else 6
            step = _TILE / cells

            bm = bmesh.new()
            grid = [[bm.verts.new((x0 + a * step, y0 + b * step, field.surface(x0 + a * step, y0 + b * step) + 0.02))
                     for b in range(cells + 1)] for a in range(cells + 1)]
            for a in range(cells):
                for b in range(cells):
                    bm.faces.new((grid[a][b], grid[a + 1][b], grid[a + 1][b + 1], grid[a][b + 1]))
            mesh = bpy.data.meshes.new("PD_waste")
            bm.to_mesh(mesh)
            bm.free()

            tile = bpy.data.objects.new("Waste", mesh)
            geo.collection.objects.link(tile)
            tile.parent = root
            tile.active_material = opaque
            tone = field.shade(cx, cy) * stablehash.uniform(seed, i * 131 + j, 0.86, 1.12)
            tile.color = _tone(_WASTE, max(0.12, tone)) + (1.0,)


# ---------------------------------------------------------------- strata


def _strata(make, seed, clear):
    """Layers showing in the steep faces between benches: thin slabs stacked into the face,
    of different lengths and tones, with now and then something longer running through them."""
    placed = 0
    index = 0
    while placed < _STRATA and index < 9000:
        index += 1
        s = seed + index * 17
        along = stablehash.uniform(s, 0, -28.0, 150.0)
        across = stablehash.uniform(s, 1, -62.0, 62.0)
        x, y = field.from_flight(along, across)
        shade = field.shade(x, y)
        if shade < 0.3 or _inside(x, y, clear, 3.0):
            continue
        drop, downhill = field.steepness(x, y)
        if drop < 0.85:
            continue
        placed += 1
        contour = math.degrees(math.atan2(downhill[1], downhill[0])) + 90.0
        base = field.surface(x, y) - 0.55
        for k in range(6):
            ls = s + 1000 + k * 7
            length = stablehash.uniform(ls, 0, 2.2, 6.0)
            slide = stablehash.uniform(ls, 1, -1.2, 1.2)
            inward = 0.25 + stablehash.uniform(ls, 2, 0.0, 0.5)
            px = x - downhill[0] * inward + math.cos(math.radians(contour)) * slide
            py = y - downhill[1] * inward + math.sin(math.radians(contour)) * slide
            rotation = q_mul(q_axis_angle((0.0, 0.0, 1.0), contour + stablehash.uniform(ls, 3, -7.0, 7.0)),
                             q_axis_angle((0.0, 1.0, 0.0), stablehash.uniform(ls, 4, -4.0, 4.0)))
            tone = shade * (0.62, 1.2, 0.8, 1.45, 0.7, 1.05)[k] * stablehash.uniform(ls, 5, 0.85, 1.15)
            kind = int(stablehash.value(ls, 6) * 9)
            z = base + k * 0.25
            if kind == 0:       # a rib running through the layers
                make.box("StrataRib", (px, py, z), (length + 1.5, 0.35, 0.3), mat.WALL, 0.5 * tone, rotation)
            elif kind == 1:     # conduit
                make.box("StrataDuct", (px, py, z), (length, 0.09, 0.09), mat.JOINT, 2.4 * tone, rotation)
            elif kind == 2:     # a slice of body
                make.box("StrataBody", (px, py, z), (0.85, 0.42, 0.15), mat.BODY, 0.6 * tone, rotation)
            else:
                make.box("Stratum", (px, py, z), (length, 1.5, 0.21), _WASTE, 1.25 * tone, rotation)
        if placed % 3 == 0:
            # An arm reaching out of the face.
            make.arm((x - downhill[0] * 0.3, y - downhill[1] * 0.3, base + stablehash.uniform(s, 5, 0.3, 1.2)),
                     q_mul(q_axis_angle((0.0, 0.0, 1.0), contour - 90.0 + stablehash.uniform(s, 6, -35.0, 35.0)),
                           q_axis_angle((0.0, 1.0, 0.0), stablehash.uniform(s, 7, -25.0, 25.0))), shade)


# ---------------------------------------------------------------- debris


def _debris(make, seed, clear, dense, crest):
    """Refuse in three sizes, densest along the flight, each piece sunk into the surface and
    turned to any angle. Large pieces go deepest: they are landmarks only where an end shows."""
    for i in range(_DEBRIS * dense):
        s = seed + i * 29
        along = stablehash.uniform(s, 0, -40.0, 185.0)
        # Concentrated toward the flight line: three pieces in four fall within 40 m of it.
        spread = stablehash.uniform(s, 1, -1.0, 1.0)
        across = 115.0 * spread * abs(spread) ** 1.4
        x, y = field.from_flight(along, across)
        shade = field.shade(x, y)
        if stablehash.value(s, 2) > shade or _inside(x, y, clear, 0.0):
            continue
        pick = stablehash.value(s, 3)
        size = 2 if pick < 0.035 else 1 if pick < 0.27 else 0
        near_landing = math.hypot(x - crest[0], y - crest[1]) < 4.5
        if size == 2 and near_landing:
            continue
        reach = (0.25, 0.7, 1.9)[size]
        sink = reach * (stablehash.uniform(s, 4, 0.25, 1.15) if size < 2 else stablehash.uniform(s, 4, 0.7, 1.4))
        rotation = _lying_rotation(s, 25.0) if near_landing else _any_rotation(s)
        make.piece(size, s, (x, y, field.surface(x, y) - sink + reach * 0.3), rotation, shade)


def _arms(make, seed, clear):
    """Discarded arms along the flight. More than half are only partly out of the waste."""
    placed = 0
    for i in range(_ARMS * 4):
        if placed >= _ARMS:
            break
        s = seed + i * 41
        x, y = field.from_flight(stablehash.uniform(s, 0, -18.0, 150.0), stablehash.uniform(s, 1, -46.0, 46.0))
        shade = field.shade(x, y)
        if shade < 0.35 or _inside(x, y, clear, 0.3):
            continue
        placed += 1
        buried = stablehash.value(s, 2) < 0.58
        rotation = _any_rotation(s) if buried else _lying_rotation(s, 24.0)
        make.arm((x, y, field.surface(x, y) + (-0.22 if buried else 0.12)), rotation, shade * stablehash.uniform(s, 3, 0.75, 1.2))


def _inside(x, y, discs, margin):
    return any(math.hypot(x - cx, y - cy) < r + margin for cx, cy, r in discs)


def _tone(color, k):
    return tuple(c * k for c in color)


def _any_rotation(s):
    """A uniformly random orientation from three hashes: no axis is preferred."""
    u1, u2, u3 = stablehash.value(s, 90), stablehash.value(s, 91), stablehash.value(s, 92)
    a, b = math.sqrt(1.0 - u1), math.sqrt(u1)
    return (b * math.cos(2 * math.pi * u3), a * math.sin(2 * math.pi * u2), a * math.cos(2 * math.pi * u2), b * math.sin(2 * math.pi * u3))


def _lying_rotation(s, limit):
    """Roughly flat, at any heading, tipped up to ``limit`` degrees."""
    heading = q_axis_angle((0.0, 0.0, 1.0), stablehash.uniform(s, 93, 0.0, 360.0))
    axis = stablehash.uniform(s, 94, 0.0, 2.0 * math.pi)
    return q_mul(q_axis_angle((math.cos(axis), math.sin(axis), 0.0), stablehash.uniform(s, 95, -limit, limit)), heading)


class _Maker:
    """Creates refuse. Every kind is a part of the world above."""

    def __init__(self, geo, root, opaque):
        self.geo, self.root, self.opaque = geo, root, opaque

    def box(self, name, position, size, color, k, rotation):
        obj = self.geo.box(name, self.root, position, size, self.opaque, _tone(color, k))
        obj.rotation_quaternion = rotation
        return obj

    def cylinder(self, name, position, radius, height, color, k, rotation):
        obj = self.geo.cylinder(name, self.root, position, radius, height, self.opaque, _tone(color, k))
        obj.rotation_quaternion = rotation
        return obj

    def piece(self, size, s, position, rotation, shade):
        """``size`` is 0 small, 1 medium, 2 large. ``s`` seeds every choice."""
        def u(k, lo, hi):
            return stablehash.uniform(s, 40 + k, lo, hi)

        value = shade * u(0, 0.55, 1.25)        # modest value variation, to separate overlaps
        kind = int(stablehash.value(s, 30) * 8)
        box, cyl = self.box, self.cylinder
        if size == 0:
            if kind == 0:
                return box("RefuseShard", position, (u(1, 0.5, 1.1), u(2, 0.4, 0.9), 0.10), mat.FIXTURE, 0.5 * value, rotation)
            if kind == 1:
                return box("RefuseStub", position, (u(1, 0.6, 1.4), 0.33, 0.28), mat.WALL, 0.5 * value, rotation)
            if kind == 2:
                return box("RefuseDuct", position, (u(1, 0.3, 0.9), 0.09, 0.09), mat.JOINT, 2.4 * value, rotation)
            if kind == 3:
                return box("RefuseLump", position, (u(1, 0.3, 0.6), u(2, 0.3, 0.6), u(3, 0.2, 0.5)), mat.STRUCTURE, value, rotation)
            if kind == 4:
                return box("RefuseSlice", position, (0.19, 0.20, 0.12), mat.BODY, 0.6 * value, rotation)
            if kind == 5:
                return self.geo.sphere("RefuseJoint", self.root, position, u(1, 0.17, 0.24), self.opaque, _tone(mat.JOINT, 1.8 * value))
            if kind == 6:
                return box("RefuseSheet", position, (u(1, 0.6, 1.0), u(2, 0.4, 0.7), 0.05), mat.FIXTURE, 0.42 * value, rotation)
            return box("RefuseBlade", position, (0.9, 0.22, 0.08), mat.STRUCTURE, 0.9 * value, rotation)
        if size == 1:
            if kind == 0:
                return box("RefusePanel", position, (2.35, 2.0, 0.14), mat.FIXTURE, 0.5 * value, rotation)
            if kind == 1:
                return box("RefuseRib", position, (u(1, 2.0, 3.5), 0.35, 0.3), mat.WALL, 0.5 * value, rotation)
            if kind == 2:
                return cyl("RefuseColumn", position, 0.32, u(1, 1.2, 2.0), mat.BODY, 0.4 * value, rotation)
            if kind == 3:
                return box("RefuseCabinet", position, (0.6, u(1, 0.8, 1.4), u(2, 0.8, 1.5)), mat.FIXTURE, 0.45 * value, rotation)
            if kind == 4:
                return box("RefuseBlock", position, (u(1, 0.8, 1.4), u(2, 0.7, 1.2), u(3, 0.4, 0.8)), mat.STRUCTURE, value, rotation)
            if kind == 5:
                return box("RefuseHousing", position, (1.0, 1.0, 0.5), mat.STRUCTURE, 0.8 * value, rotation)
            if kind == 6:
                return box("RefuseTorso", position, (0.85, 0.42, 0.15), mat.BODY, 0.6 * value, rotation)
            return box("RefuseHead", position, (0.6, 0.16, 0.06), mat.JOINT, 2.0 * value, rotation)
        if kind < 2:
            return box("RefuseBeam", position, (u(1, 4.0, 6.5), 0.35, 0.3), mat.WALL, 0.5 * value, rotation)
        if kind < 4:
            return cyl("RefuseShaft", position, 0.32, 3.2, mat.BODY, 0.4 * value, rotation)
        if kind == 4:
            return box("RefuseBase", position, (1.4, 1.4, 0.5), mat.STRUCTURE, 0.9 * value, rotation)
        if kind == 5:
            return box("RefuseDeck", position, (u(1, 2.4, 3.4), u(2, 1.6, 2.4), 0.16), mat.STRUCTURE, 0.8 * value, rotation)
        return box("RefuseMachine", position, (u(1, 1.8, 3.0), u(2, 1.4, 2.2), u(3, 1.0, 1.8)), mat.STRUCTURE, 0.7 * value, rotation)

    def arm(self, position, rotation, value, name="DiscardedArm", bend=0.0):
        """An arm like the one above, reduced to its parts. Grey, like everything else here.
        ``bend`` is degrees of flexion at the elbow, about the arm's own y axis."""
        S = layout.FIGURE_SCALE
        arm = self.geo.empty(name, self.root, position, rotation)
        body, joint = _tone(mat.BODY, 0.6 * value), _tone(mat.JOINT, 1.6 * value)
        self.geo.box("DiscardedUpper", arm, (-0.26 * S, 0, 0), (0.28 * S, 0.105 * S, 0.115 * S), self.opaque, body)
        self.geo.sphere("DiscardedElbow", arm, (-0.08 * S, 0, 0), 0.10 * S, self.opaque, joint)
        lower, at = arm, -0.08 * S
        if bend:
            lower, at = self.geo.empty("DiscardedLower", arm, (-0.08 * S, 0, 0), q_axis_angle((0.0, 1.0, 0.0), bend)), 0.0
        self.geo.box("DiscardedFore", lower, (at + 0.17 * S, 0, 0), (0.25 * S, 0.09 * S, 0.095 * S), self.opaque, body)
        self.geo.box("DiscardedHand", lower, (at + 0.35 * S, 0, 0), (0.10 * S, 0.05 * S, 0.10 * S), self.opaque, body)
        return arm

    def leg(self, position, rotation, value, name="DiscardedLeg"):
        """A leg: thigh, knee, shin, foot."""
        S = layout.FIGURE_SCALE
        leg = self.geo.empty(name, self.root, position, rotation)
        body, joint = _tone(mat.BODY, 0.6 * value), _tone(mat.JOINT, 1.6 * value)
        self.geo.box("DiscardedThigh", leg, (-0.27 * S, 0, 0), (0.36 * S, 0.15 * S, 0.16 * S), self.opaque, body)
        self.geo.sphere("DiscardedKnee", leg, (-0.05 * S, 0, 0), 0.12 * S, self.opaque, joint)
        self.geo.box("DiscardedShin", leg, (0.17 * S, 0, 0), (0.33 * S, 0.12 * S, 0.13 * S), self.opaque, body)
        self.geo.box("DiscardedFoot", leg, (0.38 * S, 0.05 * S, 0), (0.05 * S, 0.26 * S, 0.13 * S), self.opaque, body)
        return leg

    def torso(self, position, rotation, value, name="DiscardedTorso"):
        """A torso block: three of the slabs the figure above is stacked from, and a spine."""
        S = layout.FIGURE_SCALE
        torso = self.geo.empty(name, self.root, position, rotation)
        body, joint = _tone(mat.BODY, 0.6 * value), _tone(mat.JOINT, 1.6 * value)
        for k, width in enumerate((0.41, 0.46, 0.50)):
            self.geo.box("DiscardedSlab", torso, ((k - 1) * 0.097 * S, 0, 0), (0.085 * S, width * S, 0.24 * S), self.opaque, body)
        spine = self.geo.cylinder("DiscardedSpine", torso, (0, 0, 0.14 * S), 0.035 * S, 0.30 * S, self.opaque, joint)
        spine.rotation_quaternion = q_axis_angle((0.0, 1.0, 0.0), 90.0)
        return torso


# ---------------------------------------------------------------- fixtures


def _disposed(make, anim, event, index):
    """Something coming down another chute while the camera flies over."""
    builder = {"arm": make.arm, "leg": make.leg, "torso": make.torso}[event.kind]
    # Seen broadside, an arm is flexed at the elbow: upper arm and forearm make an angle, which
    # is what tells an arm from a bar at a distance.
    extra = {"bend": _BROADSIDE_BEND} if event.broadside else {}
    # Paler than anything lying in the field: it has not been here long enough to dull.
    obj = builder((event.x, event.y, event.bottom + 0.5), (1.0, 0.0, 0.0, 0.0), 2.1, name="Disposed%d" % (index + 1), **extra)
    anim.add(obj, "location", lambda t: field.event_pose(event, t)[0])
    anim.add(obj, "rotation_quaternion", lambda t: field.event_pose(event, t)[1])
    # Not there at all until its chute releases it.
    anim.add(obj, "scale", lambda t: (1.0, 1.0, 1.0) if field.event_pose(event, t)[2] else (0.0, 0.0, 0.0))


def _loose_pieces(geo, root, opaque, anim, crest):
    """Three light pieces at the edge of the platform that shift when the forearm lands."""
    for i in range(3):
        angle = math.radians(40.0 + i * 115.0)
        r = layout.LANDFILL_CREST_RADIUS * 0.82
        rest = (crest[0] + math.cos(angle) * r, crest[1] + math.sin(angle) * r, crest[2] + 0.05)
        piece = geo.box("RefuseLoose", root, rest, (0.55, 0.4, 0.06), opaque, _tone(mat.FIXTURE, 0.6))
        rest_rotation = q_axis_angle((0.0, 0.0, 1.0), 25.0 + i * 50.0)
        outward = (math.cos(angle), math.sin(angle), 0.0)
        turn_axis = (-math.sin(angle), math.cos(angle), 0.0)
        anim.add(piece, "location", lambda t, rest=rest, outward=outward: add(
            rest, tuple(c * 0.07 * ch.landfill_nudge(t) for c in outward)))
        anim.add(piece, "rotation_quaternion", lambda t, rest_rotation=rest_rotation, turn_axis=turn_axis, i=i: q_mul(
            q_axis_angle(turn_axis, (6.0 + 2.0 * i) * ch.landfill_nudge(t)), rest_rotation))


def _chute(geo, root, opaque, energy, at, bottom, scale, heading, glow, tone, detailed):
    """A rectangular chute hanging from the pit ceiling, with a lit mouth. Distant ones are a
    single block: at that range only the shape and the light can be told."""
    across, along = layout.DISPOSAL_APERTURE[0] * scale, layout.DISPOSAL_APERTURE[1] * scale
    top = -0.65
    mid, height, wall = (top + bottom) * 0.5, top - bottom, 0.12
    turn = q_axis_angle((0.0, 0.0, 1.0), heading)
    walls = _tone(_CHUTE, tone)
    if not detailed:
        block = geo.box("ChuteBlock", root, (at[0], at[1], mid), (across + 2 * wall, along + 2 * wall, height), opaque, walls)
        block.rotation_quaternion = turn
        mouth = geo.box("ChuteMouth", root, (at[0], at[1], bottom - 0.02), (across, along, 0.03), energy, _tone(mat.LIGHT_PANEL, glow))
        mouth.rotation_quaternion = turn
        return
    frame = geo.empty("Chute", root, (at[0], at[1], 0.0), turn)
    for sx in (-1, 1):
        geo.box("ChuteWall", frame, (sx * (across * 0.5 + wall * 0.5), 0.0, mid), (wall, along + 2 * wall, height), opaque, walls)
    for sy in (-1, 1):
        geo.box("ChuteWall", frame, (0.0, sy * (along * 0.5 + wall * 0.5), mid), (across, wall, height), opaque, walls)
    # The light of the station above, seen from below.
    geo.box("ChuteMouth", frame, (0.0, 0.0, bottom + 0.15), (across, along, 0.03), energy, _tone(mat.LIGHT_PANEL, glow))
