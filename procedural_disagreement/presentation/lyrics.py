"""The sung lyric, in its final Traditional Chinese translation, and where it is shown.

Pure presentation rules, like presentation/screens.py. The translation is the director's, final,
and used exactly as written. The timing is the songwriter-confirmed alignment in
docs/lyric_alignment.md (first syllable to last, per line). Every sung line is shown once, in
one of two forms that belong to the shot:

    crt     on the rear wall's CRTs, when enough of them are visible and readable;
    world   as Chinese text suspended in the scene, when they are not.

Which, and exactly how, is measured from the scene and the cameras by tools/lyric_layout.py and
recorded in assets/lyrics/layout.json; this module holds the text, the timing, the phrase
groups and the packing rule that both sides share.
"""

import itertools
import json
import os
from functools import lru_cache

from ..core import hinge, outer, timeline
from . import glyphs

#: The final translation (director, 2026-10-21). Do not edit the wording.
TEXT = {
    "A1": "捨棄那冒犯性的軀幹",
    "A2": "卻將它封聖於殘肢",
    "B1": "我寧願它從未存在",
    "B2": "也想知道它在哪座垃圾掩埋場",
    "C1": "這些潦草的土地致謝聲明",
    "C2": "這些強人胸前的勳表",
}
#: The same lines in their phrases, for breaking them into rows: each line is two halves, and each
#: half one or two phrases. Breaking between the halves costs nothing, between the phrases of a
#: half a little, inside a phrase a lot (BREAK). Joined, each is exactly its line.
GROUPS = {
    "A1": (("捨棄",), ("那冒犯性的", "軀幹")),
    "A2": (("卻將它", "封聖"), ("於殘肢",)),
    "B1": (("我寧願",), ("它從未存在",)),
    "B2": (("也想知道",), ("它在哪座", "垃圾掩埋場")),
    "C1": (("這些", "潦草的"), ("土地", "致謝聲明")),
    "C2": (("這些", "強人"), ("胸前的", "勳表")),
}
#: The words of each line: a word is never split across two screens if it can be helped (director,
#: 2026-10-21: not 「土地致」 / 「謝聲明」). Joined, each is exactly its line.
WORDS = {
    "A1": ("捨棄", "那", "冒犯性", "的", "軀幹"),
    "A2": ("卻", "將", "它", "封聖", "於", "殘肢"),
    "B1": ("我", "寧願", "它", "從未", "存在"),
    "B2": ("也", "想", "知道", "它", "在", "哪座", "垃圾", "掩埋場"),
    "C1": ("這些", "潦草", "的", "土地", "致謝", "聲明"),
    "C2": ("這些", "強人", "胸前", "的", "勳表"),
}
#: What a break between rows costs, by where it falls (see _breaks): between the halves, between
#: two phrases of a half, between two words of a phrase, inside a word. A row of a single
#: character costs ORPHAN.
BREAK = {3: 0, 2: 3, 1: 6, 0: 10}
ORPHAN = 2
#: What a break between two screens of one row costs: between phrases, nothing; between words, a
#: little; inside a word, a lot. Each character a screen holds beyond the row's usual number costs
#: one, so a screen takes a whole word rather than half of one, but not without need.
SCREEN_BREAK = {3: 0, 2: 0, 1: 1, 0: 10}
#: What each character more on a screen costs, against the breaks: one large character a screen
#: is worth a break between two phrases, not one inside a phrase.
CROWD = 4

#: Each statement as (line, first syllable, end of last syllable), in track seconds, from
#: docs/lyric_alignment.md. Couplets repeat verbatim at the offsets the document gives.
_A = (("A1", 40.0, 44.6), ("A2", 44.97, 49.4))
_B = (("B1", 90.1, 94.5), ("B2", 94.85, 99.4))
_C = (("C1", 80.1, 82.1), ("C2", 82.55, 84.6))


def _shift(lines, by):
    return tuple((name, a + by, b + by) for name, a, b in lines)


SUNG = (_A + _shift(_A, 10.0) + _C + _B + _shift(_B, 10.0)
        + sum((_shift(_C, 60.0 + 5.0 * k) for k in range(8)), ())
        + _shift(_C, 175.0) + _shift(_C, 180.0))

#: A line stays up through a pause shorter than this into the next line, so a couplet is not
#: blinked off between its lines; the last line of a statement holds this much after it ends.
BRIDGE = 0.8
TAIL = 0.3
#: World-space text: font pixels between its rows.
WORLD_GAP = 4
#: The camera cuts: a line that is being sung across one is shown in two parts.
CUTS = (timeline.LANDFILL_CUT, hinge.CUT, outer.CODA_START + 1.0 / 30.0)

LAYOUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      "assets", "lyrics", "layout.json")


def windows():
    """[(key, line, start, end)]: when each line is shown, split at camera cuts."""
    spans = []
    ordered = sorted(SUNG, key=lambda s: s[1])
    for i, (name, start, end) in enumerate(ordered):
        following = ordered[i + 1][1] if i + 1 < len(ordered) else None
        if following is not None and following - end < BRIDGE:
            end = following
        else:
            end = end + TAIL
        edges = [start] + [c for c in CUTS if start < c < end] + [end]
        for part, (a, b) in enumerate(zip(edges, edges[1:])):
            spans.append(("%s@%.2f%s" % (name, start, "" if part == 0 else "/%d" % part), name, a, b))
    return spans


def sung(key):
    """(first syllable, end of last syllable) of the statement a window (lyrics.windows()) shows."""
    name, rest = key.split("@")
    start = float(rest.split("/")[0])
    return next((a, b) for n, a, b in SUNG if n == name and abs(a - start) < 0.005)


def _breaks(groups):
    """The line's text, and for each place between two of its characters how strong a break it is:
    3 between the halves, 2 between phrases, 1 between words, 0 inside a word."""
    text, strength = "", []
    for major in groups:
        for j, minor in enumerate(major):
            for k, character in enumerate(minor):
                if text:
                    strength.append(3 if j == 0 and k == 0 else 2 if k == 0 else 0)
                text += character
    words = next((WORDS[key] for key, line in TEXT.items() if line == text), (text,))
    position = 0
    for word in words[:-1]:
        position += len(word)
        strength[position - 1] = max(strength[position - 1], 1)
    return text, strength


def screens(groups, offset, row, limits, per):
    """How a row of text (starting `offset` characters into its line) is split over screens that
    hold at most `limits` characters each, in order: (cost, imbalance, the pieces), or None. Cheapest breaks
    first (SCREEN_BREAK, and one for each character a screen holds beyond `per`), then the pieces
    nearest `per` characters each."""
    _, strength = _breaks(groups)
    best = None
    for cuts in itertools.combinations(range(1, len(row)), len(limits) - 1):
        edges = (0,) + cuts + (len(row),)
        pieces = [row[a:b] for a, b in zip(edges, edges[1:])]
        if any(len(piece) > limit for piece, limit in zip(pieces, limits)):
            continue
        total = sum(SCREEN_BREAK[strength[offset + c - 1]] for c in cuts)
        total += sum(max(0, len(piece) - per) for piece in pieces)
        key = (total, sum(abs(len(piece) - per) for piece in pieces))
        if best is None or key < best[0]:
            best = (key, pieces)
    return (best[0][0], best[0][1], best[1]) if best else None


def cost(groups, rows_text):
    """What a packing's breaks cost (BREAK, ORPHAN)."""
    _, strength = _breaks(groups)
    total, position = 0, 0
    for row in rows_text[:-1]:
        position += len(row)
        total += BREAK[strength[position - 1]]
    return total + ORPHAN * sum(len(row) == 1 for row in rows_text)


def pack(groups, rows, per_screen):
    """Lays a line out on rows of screens (or of world-space character cells).

    `rows` is how many cells each row has, top first; `per_screen` how many characters a cell
    holds. Of every way of breaking the line into rows that fit, the one whose breaks cost least
    (see cost()), then the one with fewest rows. Returns the text of each row used, top first, or
    None if the line does not fit."""
    text, _ = _breaks(groups)
    capacity = [n * per_screen for n in rows]
    best = None
    for count in range(1, len(capacity) + 1):
        for cuts in itertools.combinations(range(1, len(text)), count - 1):
            edges = (0,) + cuts + (len(text),)
            pieces = [text[a:b] for a, b in zip(edges, edges[1:])]
            if any(len(piece) > room for piece, room in zip(pieces, capacity)):
                continue
            key = (cost(groups, pieces), count)
            if best is None or key < best[0]:
                best = (key, pieces)
    return best[1] if best else None


def best_pack(groups, rows, options):
    """The packing to use: of the characters-per-cell `options` that fit, the one whose breaks
    cost least, counting CROWD for each character a cell beyond one; then the fewest characters a
    cell. Returns (per_cell, rows_text) or None."""
    found = []
    for per in options:
        text = pack(groups, rows, per)
        if text is not None:
            found.append((cost(groups, text) + CROWD * (per - 1), per, text))
    if not found:
        return None
    _, per, text = min(found, key=lambda f: (f[0], f[1]))
    return per, text


@lru_cache(maxsize=None)
def layout():
    """The measured layout (assets/lyrics/layout.json), or None before it is made."""
    if not os.path.exists(LAYOUT):
        return None
    with open(LAYOUT, encoding="utf-8") as handle:
        return json.load(handle)


def crt_lines():
    """The lines shown on the CRTs, in order. A line's place in this list is its index in the
    lyric canvas (see canvas())."""
    data = layout()
    return [e for e in data["windows"] if e["mode"] == "crt" and "cells" in e] if data else []


def world_lines():
    """The lines shown as text in the scene, in order."""
    data = layout()
    return [e for e in data["windows"] if e["mode"] == "world"] if data else []


def _at(t):
    for index, entry in enumerate(crt_lines()):
        if entry["start"] <= t < entry["end"]:
            return index, entry
    return -1, None


def crt_index(t):
    """Index of the CRT line showing at track time t, or -1."""
    return _at(t)[0]


def crt_cells(t):
    """The screens, as (row, col), that carry text at track time t."""
    entry = _at(t)[1]
    return {(cell[0], cell[1]) for cell in entry["cells"]} if entry else set()


def coda_cells():
    """The screens that carry text at any time in the coda."""
    return {(cell[0], cell[1]) for e in crt_lines() if e["start"] >= outer.CODA_START for cell in e["cells"]}


#: The CRT wall as one picture: 5 screens across, 3 down, each 64 x 48 pixels.
CANVAS = (320, 144)
#: Where each character goes on its screen, top left, in screen pixels, by how many a screen holds.
#: One or two characters are drawn two screen pixels to a font pixel (32 x 32); three or four, one.
SLOTS = {1: ((16, 8),), 2: ((0, 8), (32, 8)), 3: ((8, 16), (24, 16), (40, 16)), 4: ((0, 16), (16, 16), (32, 16), (48, 16))}


def canvas(entry):
    """A CRT line drawn on the whole wall's canvas: rows top first, 1 where a pixel is lit."""
    width, height = CANVAS
    pixels = [0] * (width * height)
    text = "".join(TEXT.values())
    per = entry["per_screen"]
    for row, col, chars in entry["cells"]:
        x0, y0 = col * 64, (2 - row) * 48
        # A screen holding more than the line's usual number (a whole word) uses the next slots.
        for character, (x, y) in zip(chars, SLOTS[max(per, len(chars))]):
            glyphs.stamp(pixels, width, character, x0 + x, y0 + y, entry["scale"], text)
    return pixels


def world_bitmap(entry):
    """A line's world-space text: (width, height, pixels with rows top first), each row of text
    centred, WORLD_GAP font pixels between rows, and a clear pixel all round."""
    rows = entry["world"]["rows"]
    width = 16 * max(len(r) for r in rows) + 2
    height = 16 * len(rows) + WORLD_GAP * (len(rows) - 1) + 2
    pixels = [0] * (width * height)
    text = "".join(TEXT.values())
    for k, row in enumerate(rows):
        x = 1 + (width - 2 - 16 * len(row)) // 2
        for i, character in enumerate(row):
            glyphs.stamp(pixels, width, character, x + 16 * i, 1 + k * (16 + WORLD_GAP), 1, text)
    return width, height, pixels
