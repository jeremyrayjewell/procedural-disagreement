"""Stateless easing. Every animation is built from these and absolute time."""


def clamp01(u):
    return 0.0 if u < 0.0 else 1.0 if u > 1.0 else u


def window(t, start, end):
    """0 before ``start``, 1 after ``end``, linear between."""
    if end <= start:
        return 1.0 if t >= end else 0.0
    return clamp01((t - start) / (end - start))


def smooth(u):
    return u * u * (3.0 - 2.0 * u)


def smoother(u):
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def out_cubic(u):
    v = 1.0 - u
    return 1.0 - v * v * v


def smooth_window(t, start, end):
    return smooth(window(t, start, end))


def pulse(t, in_start, in_end, out_start, out_end):
    """Rises over [in_start, in_end], holds at 1, falls over [out_start, out_end]."""
    return smooth_window(t, in_start, in_end) * (1.0 - smooth_window(t, out_start, out_end))
