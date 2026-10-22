"""GNU Unifont glyphs, pixel for pixel, for the lyric (see presentation/lyrics.py).

Unifont is a bitmap font: every glyph is a 16-pixel-high grid of on and off pixels (16 wide for
Chinese, 8 for Latin), so the text can only ever be drawn in hard square pixels, never smoothed.
The font file (assets/fonts/unifont/) is read directly; nothing here depends on Blender.
"""

import gzip
import os
from functools import lru_cache

FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "assets", "fonts", "unifont", "unifont_all-17.0.05.hex.gz")
HEIGHT = 16


@lru_cache(maxsize=None)
def _font(characters):
    wanted = {"%04X" % ord(c) for c in characters}
    found = {}
    with gzip.open(FONT, "rt", encoding="ascii") as handle:
        for line in handle:
            code, _, bits = line.strip().partition(":")
            if code in wanted:
                found[chr(int(code, 16))] = bits
    return found


def glyph(character, font_of=""):
    """The glyph as rows of 0/1, top row first: 16 rows of 16 (or 8) pixels. `font_of` names the
    text the character comes from, so the font file is read once for all of it."""
    bits = _font(frozenset(font_of or character)).get(character)
    if bits is None:
        raise KeyError("Unifont has no glyph for %r (U+%04X)" % (character, ord(character)))
    digits = len(bits) // HEIGHT
    return tuple(tuple((int(bits[r * digits:(r + 1) * digits], 16) >> (digits * 4 - 1 - x)) & 1
                       for x in range(digits * 4)) for r in range(HEIGHT))


def stamp(canvas, width, character, x, y, scale=1, font_of=""):
    """Sets the pixels of a glyph in `canvas` (a flat list, rows top first, `width` wide) to 1,
    with its top left at (x, y), each font pixel `scale` x `scale` canvas pixels."""
    for r, row in enumerate(glyph(character, font_of)):
        for c, on in enumerate(row):
            if on:
                for dy in range(scale):
                    start = (y + r * scale + dy) * width + x + c * scale
                    canvas[start:start + scale] = [1] * scale
