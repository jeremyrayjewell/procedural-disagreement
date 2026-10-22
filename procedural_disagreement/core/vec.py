"""Minimal vector and quaternion maths on plain tuples.

Kept free of ``mathutils`` so the choreography can be evaluated and tested outside Blender.
Conventions match Blender: right-handed, Z up, quaternions as (w, x, y, z).
"""

import math

X = (1.0, 0.0, 0.0)
Y = (0.0, 1.0, 0.0)
Z = (0.0, 0.0, 1.0)
Q_IDENTITY = (1.0, 0.0, 0.0, 0.0)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def normalize(a):
    return mul(a, 1.0 / length(a))


def lerp(a, b, t):
    return a + (b - a) * t


def v_lerp(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def q_axis_angle(axis, degrees):
    half = math.radians(degrees) * 0.5
    s = math.sin(half)
    return (math.cos(half), axis[0] * s, axis[1] * s, axis[2] * s)


def q_mul(a, b):
    """Rotation ``b`` followed by rotation ``a``."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def q_conj(q):
    return (q[0], -q[1], -q[2], -q[3])


def q_rotate(q, v):
    w, x, y, z = q
    u = (x, y, z)
    t = mul(cross(u, v), 2.0)
    return add(add(v, mul(t, w)), cross(u, t))


def q_slerp(a, b, t):
    d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    if d < 0.0:
        b = (-b[0], -b[1], -b[2], -b[3])
        d = -d
    if d > 0.9995:
        q = tuple(lerp(a[i], b[i], t) for i in range(4))
    else:
        theta = math.acos(d)
        sa = math.sin((1.0 - t) * theta)
        sb = math.sin(t * theta)
        q = tuple(a[i] * sa + b[i] * sb for i in range(4))
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q)


def q_between(a, b):
    """The shortest rotation that turns direction ``a`` into direction ``b``."""
    a, b = normalize(a), normalize(b)
    axis = cross(a, b)
    size = length(axis)
    if size < 1e-12:
        return Q_IDENTITY
    return q_axis_angle(mul(axis, 1.0 / size), math.degrees(math.atan2(size, dot(a, b))))


def q_from_axes(x, y, z):
    """Quaternion of the rotation whose local X, Y, Z axes are the given orthonormal vectors."""
    m00, m10, m20 = x
    m01, m11, m21 = y
    m02, m12, m22 = z
    trace = m00 + m11 + m22
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        return (0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s)
    if m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        return ((m21 - m12) / s, 0.25 * s, (m01 + m10) / s, (m02 + m20) / s)
    if m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        return ((m02 - m20) / s, (m01 + m10) / s, 0.25 * s, (m12 + m21) / s)
    s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
    return ((m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, 0.25 * s)


def q_camera_look(forward, up=Z):
    """Orientation of a Blender camera (looks down local -Z, local +Y is up) facing ``forward``."""
    back = normalize(mul(forward, -1.0))
    right = normalize(cross(up, back))
    return q_from_axes(right, cross(back, right), back)


def q_align_z(axis, hint=Y):
    """Orientation whose local Z is ``axis``; ``hint`` fixes the roll about it."""
    z = normalize(axis)
    x = normalize(cross(hint, z))
    return q_from_axes(x, cross(z, x), z)
