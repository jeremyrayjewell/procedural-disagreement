"""Stateless seeded random.

A value depends only on (seed, index), never on call order. The final profile can therefore
add objects, fragments and whole realities without shifting the randomness of anything the
preview profile also contains.
"""

_MASK = 0xFFFFFFFF


def value(seed, index):
    """Uniform value in [0, 1)."""
    h = ((seed & _MASK) * 374761393 + (index & _MASK) * 668265263) & _MASK
    h = ((h ^ (h >> 13)) * 1274126177) & _MASK
    h ^= h >> 16
    return (h & 0xFFFFFF) / 16777216.0


def uniform(seed, index, low, high):
    return low + (high - low) * value(seed, index)


def choice(seed, index, options):
    return options[int(value(seed, index) * len(options)) % len(options)]
