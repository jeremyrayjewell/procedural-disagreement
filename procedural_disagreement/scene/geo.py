"""Primitive geometry. Everything visible is made through here.

Positions and sizes come from the caller and are identical in every profile; the profile only
decides tessellation and bevels.
"""

import math

import bmesh
import bpy


class Geo:
    def __init__(self, profile, collection):
        self.profile = profile
        self.collection = collection
        self._meshes = {}
        #: While set, boxes are never given their own bevelled mesh. For debris fields, where
        #: thousands of boxes must go on sharing one.
        self.plain = False

    # ------------------------------------------------------------ objects

    def empty(self, name, parent=None, location=(0.0, 0.0, 0.0), rotation=None):
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_size = 0.15
        return self._place(obj, parent, location, rotation)

    def box(self, name, parent, center, size, material, color):
        bevel = self.profile.bevel_width
        if bevel > 0.0 and not self.plain and min(size) > bevel * 4.0:
            # A bevel needs true dimensions, so the box gets its own mesh.
            obj = bpy.data.objects.new(name, self._box_mesh(size))
            modifier = obj.modifiers.new("Bevel", "BEVEL")
            modifier.width = bevel
            modifier.segments = 2
        else:
            obj = bpy.data.objects.new(name, self._shared("cube", self._unit_cube))
            obj.scale = size
        return self._finish(obj, parent, center, material, color)

    def cylinder(self, name, parent, center, radius, height, material, color):
        """Cylinder along local Z."""
        obj = bpy.data.objects.new(name, self._shared("cylinder", self._unit_cylinder))
        obj.scale = (radius * 2.0, radius * 2.0, height)
        return self._finish(obj, parent, center, material, color)

    def sphere(self, name, parent, center, diameter, material, color):
        obj = bpy.data.objects.new(name, self._shared("sphere", self._unit_sphere))
        obj.scale = (diameter, diameter, diameter)
        return self._finish(obj, parent, center, material, color)

    def quad(self, name, parent, size, material, color):
        """Square sheet in local XY."""
        obj = bpy.data.objects.new(name, self._shared("quad", self._unit_quad))
        obj.scale = (size, size, 1.0)
        return self._finish(obj, parent, (0.0, 0.0, 0.0), material, color)

    def _finish(self, obj, parent, center, material, color):
        obj.active_material = material
        if self.profile.look:
            # Many objects share one mesh. Where surfaces are going to differ, each object
            # carries its own material and the shared mesh carries none.
            slot = obj.material_slots[0]
            slot.link = "OBJECT"
            slot.material = material
        obj.color = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
        return self._place(obj, parent, center, None)

    def _place(self, obj, parent, location, rotation):
        self.collection.objects.link(obj)
        obj.parent = parent
        obj.location = location
        # Quaternions throughout: baked rotations interpolate cleanly and never hit gimbal lock.
        obj.rotation_mode = "QUATERNION"
        if rotation is not None:
            obj.rotation_quaternion = rotation
        return obj

    # ------------------------------------------------------------ meshes

    def _shared(self, key, make):
        mesh = self._meshes.get(key)
        if mesh is None:
            bm = bmesh.new()
            make(bm)
            mesh = self._to_mesh(bm, "PD_" + key)
            self._meshes[key] = mesh
        return mesh

    def _box_mesh(self, size):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]
            v.co.y *= size[1]
            v.co.z *= size[2]
        return self._to_mesh(bm, "PD_box")

    @staticmethod
    def _unit_cube(bm):
        bmesh.ops.create_cube(bm, size=1.0)

    def _unit_cylinder(self, bm):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=self.profile.cylinder_segments,
                              radius1=0.5, radius2=0.5, depth=1.0)
        _smooth(bm)

    def _unit_sphere(self, bm):
        segments = self.profile.sphere_segments
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=max(4, segments // 2), radius=0.5)
        _smooth(bm)

    @staticmethod
    def _unit_quad(bm):
        verts = [bm.verts.new(p) for p in ((-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0))]
        bm.faces.new(verts)

    @staticmethod
    def _to_mesh(bm, name):
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        return mesh


def _smooth(bm):
    """Smooth-shade curved surfaces, keeping hard edges (such as cylinder rims) sharp."""
    limit = math.radians(40.0)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        if len(edge.link_faces) == 2 and edge.calc_face_angle() > limit:
            edge.smooth = False
