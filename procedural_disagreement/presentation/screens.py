"""The rear wall's display panels: what each screen shows, as functions of track time.

Pure presentation rules, like presentation/emission.py: profile-blind functions of track time
that the look layer only draws. Each screen is a 64 x 48 grid of virtual pixels, and the wall
together one 320 x 144 canvas. What it shows is in a cold, pale, nearly monochrome light:

    lyric   while a line is sung and the wall is seen, the line, in Chinese, across the screens
            that can be read in the shot (presentation/lyrics.py). It takes the whole wall: the
            screens without text show the idle raster. It is the only text the screens ever show.
    video   real footage on the wall's canvas, where there is footage (from 1:00; made by
            tools/make_crt_video.py). Until then, and wherever there is none, the provisional
            content below.
    provisional: an idle raster; single coarse blocks (the film's block vocabulary); single
            irregular traces (the scrawls). No numbers, interface or spectrum display. (Rows of
            bars were tried and read as lines of text, so they are not used.)

    0:00-0:20   dark, except the opening's panel, which wakes with its authored light at 0:09.5
    0:20        with the coupling the other panels wake, row by row; idle raster
    0:40-1:00   the lyric (A, sung twice)
    1:00        blocks: one coarse block per screen, its size and place stepping on the beat
    1:20-1:30   the bass drops: blocks give way to traces; the attractor panel holds one block
    1:30-1:37   the blocks come back and run along the rows toward the disposal side
    4:15-4:25   dark, except the screens that carry the refrain's words while it is sung
    4:25-4:40   dark

(Which lines are on the screens is measured: in 1:20-1:37 the camera is too close for the
screens to carry a line, and those lines stand in the room as text instead. See lyrics.py.)

Revised 2026-10-21 (director): the screens were dark from 4:15 so that the coda's marks read
against dark glass; now the refrain's words are on the screens that carry them while it is sung,
and the marks on those panels give way to them. Everything else in the coda is as it was.

Brightness leans a little with the low band; sparse pixels flicker with the high band (the
provisional content only).
"""

import json
import os
from functools import lru_cache

from ..core import audio, layout, outer, stablehash, timeline
from ..core.ease import smoother, window
from . import lyrics

ROWS, COLUMNS = 3, 5
#: Virtual pixels per screen.
PIXELS = (64, 48)

SEED = 911
BLOCKS_START = timeline.SYSTEM_DIVERGENCE
TRACES = (timeline.ABSENT_ATTRACTOR, timeline.PROSTHETIC_RECRUITMENT)
RUN = (timeline.PROSTHETIC_RECRUITMENT, timeline.LANDFILL_CUT)
DARK_FROM = outer.CODA_START

#: The idle raster's level, the blocks' and traces' level (both 0..1 of the screen's brightness).
IDLE = 0.05
LIT = 1.0
#: How far the low band leans the brightness, and the high band's flicker at full level.
LEAN = 0.15
FLICKER = 0.012


def _stroke(t, start, seconds):
    return smoother(window(t, start, start + seconds))


def wake(row, col, t):
    """0..1: whether the screen is on. The opening's panel wakes with its own authored light. From
    4:15 only the screens that carry the lyric are on, and only while it is there."""
    if t >= DARK_FROM:
        return 1.0 if (row, col) in lyrics.crt_cells(t) else 0.0
    if (row, col) == layout.ATTRACTOR_PANEL:
        return _stroke(t, outer.OPENING_PANEL, 0.8)
    return _stroke(t, outer.OPENING_COUPLE + row * timeline.BEAT * 2, 0.6)


def blocks(t):
    """0..1: how far the screens show blocks (the rest is the idle raster or traces)."""
    on = _stroke(t, BLOCKS_START, 0.6)
    off = _stroke(t, TRACES[0], 0.5) - _stroke(t, TRACES[1], 0.5)
    return max(0.0, on - off)


def traces(t):
    """0..1: how far the screens show traces."""
    return _stroke(t, TRACES[0], 0.5) - _stroke(t, TRACES[1], 0.5)


#: Block sizes in virtual pixels: (smallest, largest) side, on an 8-pixel grid.
BLOCK = (8, 32)


@lru_cache(maxsize=None)
def _draw(row, col, beat, k):
    return stablehash.value(SEED, (row * COLUMNS + col) * 100003 + beat * 13 + k)


def block(row, col, t):
    """(x0, y0, x1, y1) in virtual pixels of the screen's block, stepping on the beat; during the
    run (1:30-1:37) the pattern travels along the rows, column by column. Its size leans with the
    mid band."""
    beat = int(t / timeline.BEAT)
    if RUN[0] <= t < RUN[1]:
        beat -= col
    reach = 0.5 + 0.5 * audio.level("mid", t)
    low, high = BLOCK
    w = 8 * round((low + (high - low) * _draw(row, col, beat, 0) * reach) / 8)
    h = 8 * round((low + (high - low) * _draw(row, col, beat, 1) * reach) / 8)
    x = 8 * int(_draw(row, col, beat, 2) * (PIXELS[0] - w) / 8)
    y = 8 * int(_draw(row, col, beat, 3) * (PIXELS[1] - h) / 8)
    return float(x), float(y), float(x + w), float(y + h)


def trace(row, col, t):
    """(seed, progress 0..1) of the screen's trace: a new trace every two bars of the music, drawn
    left to right over the first bar."""
    period = timeline.BEAT * 8
    phrase = int((t - TRACES[0]) // period) if t >= TRACES[0] else 0
    progress = min(1.0, max(0.0, (t - TRACES[0] - phrase * period) / (timeline.BEAT * 4)))
    return float((row * COLUMNS + col) * 131 + phrase * 17 % 1000), progress


def hold(row, col, t):
    """1 on the attractor panel while the traces run: it holds one steady block."""
    return traces(t) if (row, col) == layout.ATTRACTOR_PANEL else 0.0


def lean(t):
    return 1.0 + LEAN * (audio.level("low", t) - 0.5)


def flicker(t):
    return FLICKER * audio.level("high", t)


def lyric(t):
    """1 while a line of the lyric is on the wall, else 0: it switches on and off on the frame."""
    return 1.0 if lyrics.crt_index(t) >= 0 else 0.0


def lyric_index(t):
    """Which line: its index in the lyric canvas (lyrics.crt_lines())."""
    return float(max(0, lyrics.crt_index(t)))


#: Footage on the wall: grey steps, and its brightest as a share of the screens' full light (the
#: lyric is drawn at LIT, above it).
VIDEO_LEVELS = 8
VIDEO_CAP = 0.6
#: Independent feeds (director, 2026-10-22): the footage starts from a clean, full-colour,
#: smoothly sampled baseline (approved), and is taken back toward the CRT look one step at a time.
#: The steps applied, in order: "tint" (the picture's own luminance in the screens' cold cyan,
#: brightness kept; approved), "scanlines" (the screens' raster over the picture, light; approved).
#: Later steps (scanlines, fewer pixels, fewer levels) are added here once
#: approved; an empty tuple is the clean baseline.
VIDEO_STAGES = ("tint", "scanlines")
#: Stage B: how far the scanlines darken the lower part of each of the screen's 48 rows. Approved
#: light (director, 2026-10-22): half the depth of the screens' own raster on the lyric (0.65),
#: which cost the footage too much fine detail.
VIDEO_SCANLINES = 0.325
#: Real footage for the wall, as frames of its canvas (tools/make_crt_video.py).
VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "assets", "video", "crt", "canvas")


@lru_cache(maxsize=None)
def video_format():
    """How the footage's frames are laid out, or None while there is none: {"first", "last" (frames
    of the film), "layout" ("wall": one picture across all fifteen screens; "same": the whole
    picture on every screen), "screen" (its pixels on one screen, across and down), "canvas" (a
    frame's pixels)}. Written by tools/make_crt_video.py."""
    manifest = os.path.join(VIDEO, "manifest.json")
    if not os.path.exists(manifest):
        return None
    with open(manifest, encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("layout") == "feeds":
        return {"first": data["first"], "last": data["last"], "layout": "feeds", "stream": data["stream"],
                "frames": data["frames"], "size": tuple(data["size"]), "screens": data["screens"]}
    return {"first": data["first"], "last": data["last"], "layout": data.get("layout", "wall"),
            "screen": tuple(data.get("screen", PIXELS)), "canvas": tuple(data["canvas"])}


def video_frames():
    """(first, last) frame of the film that has a frame of footage, or None while there is none."""
    form = video_format()
    return (form["first"], form["last"]) if form else None


def video(t):
    """1 where there is footage for this moment, from 1:00 until the room goes down, else 0."""
    span = video_frames()
    if span is None or not BLOCKS_START <= t < DARK_FROM:
        return 0.0
    return 1.0 if span[0] <= timeline.frame_of(t) <= span[1] else 0.0
