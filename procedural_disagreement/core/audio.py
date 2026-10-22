"""The soundtrack's measured level, as slow envelopes for the presentation layer.

Read from ``analysis/audio_features.json``, the objective timing layer. Nothing here is a cue
and nothing here may move, show or hide anything: these envelopes exist only so that light can
lean a little with the music. They are functions of absolute track time, bounded to 0..1, and
smoothed so that nothing flickers.
"""

import json
import os
from functools import lru_cache

_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "analysis", "audio_features.json")
#: The decibel range mapped onto 0..1 for each band: quiet passages sit near 0, the loudest at 1.
_RANGE = {"low": (-12.0, 20.0), "mid": (-8.0, 18.0), "high": (-18.0, 8.0), "rms": (-10.0, 22.0)}
#: Seconds the envelopes are averaged over: about a beat. Slower than any transient.
_SMOOTH = 0.6


@lru_cache(maxsize=None)
def _bands():
    with open(_FILE, encoding="utf-8") as handle:
        frames = json.load(handle)["frames"]
    hop = frames["hop_seconds"]
    half = max(1, int(_SMOOTH * 0.5 / hop))
    result = {}
    for band, (quiet, loud) in _RANGE.items():
        raw = [min(1.0, max(0.0, (value - quiet) / (loud - quiet))) for value in frames[band + "_db"]]
        # A running mean, by prefix sums.
        sums = [0.0]
        for value in raw:
            sums.append(sums[-1] + value)
        smooth = []
        for i in range(len(raw)):
            a, b = max(0, i - half), min(len(raw), i + half + 1)
            smooth.append((sums[b] - sums[a]) / (b - a))
        result[band] = smooth
    return hop, result


def level(band, t):
    """0..1: the smoothed level of "low", "mid", "high" or "rms" at track time t. Zero outside
    the track."""
    hop, bands = _bands()
    values = bands[band]
    x = t / hop
    if x <= 0.0 or x >= len(values) - 1:
        return 0.0
    i = int(x)
    return values[i] + (values[i + 1] - values[i]) * (x - i)
