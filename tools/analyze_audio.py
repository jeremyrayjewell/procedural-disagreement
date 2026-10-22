#!/usr/bin/env python3
"""Layer 1 of 2: objective audio features for the whole track.

    python tools/analyze_audio.py                       analyse the track in audio/ -> analysis/audio_features.json
    python tools/analyze_audio.py --report 0:30 1:10    print a readable breakdown of an interval

The output is plain JSON that any tool can read. It describes the music; it decides nothing.
Visual events are chosen by hand in cues/ (layer 2), using this as a reference.

Analysing needs numpy and scipy (soundfile is used if present). Reading the result, including
--report, needs neither.
"""

import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from procedural_disagreement.core import timeline  # noqa: E402
from render import find_audio  # noqa: E402

DEFAULT_OUTPUT = os.path.join(ROOT, "analysis", "audio_features.json")

N_FFT = 2048
HOP = 512
#: Band edges in Hz.
BANDS = {"low": (20.0, 150.0), "mid": (150.0, 2500.0), "high": (2500.0, 16000.0)}
SPECTRUM_BANDS = 48
#: Structural novelty is computed on the spectrum averaged to this rate, with this kernel half-width.
NOVELTY_RATE = 4.0
NOVELTY_KERNEL_SECONDS = 6.0
HARMONY_KERNEL_SECONDS = 4.0


def load_mono(path):
    """Samples as float32 mono, and the sample rate."""
    import numpy as np
    try:
        import soundfile
        samples, rate = soundfile.read(path, dtype="float32", always_2d=True)
    except ImportError:
        from scipy.io import wavfile
        rate, raw = wavfile.read(path)
        samples = raw.astype(np.float32) / (np.iinfo(raw.dtype).max if raw.dtype.kind == "i" else 1.0)
        samples = samples.reshape(len(samples), -1)
    return samples.mean(axis=1), int(rate)


def a_weighting_db(freqs):
    """IEC 61672 A-weighting in dB: how loud each frequency is perceived to be."""
    import numpy as np
    f2 = np.maximum(freqs, 1e-6) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / (
        (f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2))
    return 20.0 * np.log10(np.maximum(ra, 1e-12)) + 2.0


def log_filterbank(freqs, bands, lo, hi):
    """Triangular filters with log-spaced centres: a compact, roughly perceptual spectrum."""
    import numpy as np
    edges = np.geomspace(lo, hi, bands + 2)
    bank = np.zeros((bands, len(freqs)), dtype=np.float32)
    for i in range(bands):
        left, centre, right = edges[i], edges[i + 1], edges[i + 2]
        bank[i] = np.maximum(0.0, np.minimum((freqs - left) / (centre - left), (right - freqs) / (right - centre)))
    return bank


def track_beats(envelope, hop_seconds):
    """Tempo by autocorrelation, then beats by dynamic programming (Ellis 2007): the sequence
    of onsets that is both strong and evenly spaced at the tempo. Returns (bpm, beat frames)."""
    import numpy as np
    env = envelope - envelope.mean()
    env = env / (env.std() + 1e-9)

    # Tempo: autocorrelation peak between 60 and 200 BPM, with a gentle preference for ~120.
    size = 1 << int(np.ceil(np.log2(len(env) * 2)))
    spectrum = np.fft.rfft(env, size)
    autocorrelation = np.fft.irfft(spectrum * np.conj(spectrum))[:len(env)]
    lags = np.arange(int(60.0 / 200.0 / hop_seconds), int(60.0 / 60.0 / hop_seconds) + 1)
    prior = np.exp(-0.5 * np.log2(60.0 / (lags * hop_seconds) / 120.0) ** 2)
    best = int(np.argmax(autocorrelation[lags] * prior))
    period = float(lags[best])
    if 0 < best < len(lags) - 1:
        a, b, c = autocorrelation[lags[best] - 1], autocorrelation[lags[best]], autocorrelation[lags[best] + 1]
        period += 0.5 * (a - c) / (a - 2.0 * b + c)

    tightness = 100.0
    local = np.maximum(envelope / (envelope.std() + 1e-9), 0.0)
    score = local.copy()
    back = np.full(len(env), -1, dtype=np.int64)
    lo, hi = int(round(period * 0.5)), int(round(period * 2.0))
    offsets = np.arange(-hi, -lo + 1)
    penalty = -tightness * np.log(-offsets / period) ** 2
    for t in range(hi, len(env)):
        candidates = score[t + offsets] + penalty
        k = int(np.argmax(candidates))
        score[t] = local[t] + candidates[k]
        back[t] = t + offsets[k]

    tail = len(env) - int(period)
    t = tail + int(np.argmax(score[tail:]))
    beats = []
    while t >= 0:
        beats.append(t)
        t = back[t]
    return 60.0 / (period * hop_seconds), np.array(beats[::-1])


def analyse(path):
    import numpy as np
    from scipy.signal import find_peaks

    y, sr = load_mono(path)
    duration = len(y) / sr
    hop_seconds = HOP / sr
    freqs = np.fft.rfftfreq(N_FFT, 1.0 / sr)
    window = np.hanning(N_FFT).astype(np.float32)
    padded = np.pad(y, N_FFT // 2, mode="reflect")
    frames = 1 + (len(padded) - N_FFT) // HOP

    a_weights = 10.0 ** (a_weighting_db(freqs) / 10.0)
    band_rows = {name: (freqs >= lo) & (freqs < hi) for name, (lo, hi) in BANDS.items()}
    bank = log_filterbank(freqs, SPECTRUM_BANDS, 30.0, 16000.0)
    # Pitch classes (0 = C ... 11 = B) of the bins between 55 Hz and 2 kHz, for harmony.
    pitch_rows = np.zeros((12, len(freqs)), dtype=np.float32)
    tonal = (freqs >= 55.0) & (freqs <= 2000.0)
    classes = np.round(12.0 * np.log2(np.maximum(freqs, 1.0) / 440.0) + 9.0).astype(int) % 12
    pitch_rows[classes[tonal], np.nonzero(tonal)[0]] = 1.0
    chroma = np.zeros((12, frames), dtype=np.float32)

    rms = np.zeros(frames)
    loudness = np.zeros(frames)
    centroid = np.zeros(frames)
    bands = {name: np.zeros(frames) for name in BANDS}
    spectrum_db = np.zeros((SPECTRUM_BANDS, frames), dtype=np.float32)

    def db(x):
        return 10.0 * np.log10(np.maximum(x, 1e-12))

    # The spectrogram is consumed in chunks, so memory stays small for any track length.
    chunk = 2048
    norm = float((window ** 2).sum())
    sample = np.arange(N_FFT)[None, :]
    for start in range(0, frames, chunk):
        stop = min(frames, start + chunk)
        index = (np.arange(start, stop) * HOP)[:, None] + sample
        power = np.abs(np.fft.rfft(padded[index] * window, axis=1)) ** 2 / norm
        total = power.sum(axis=1)
        rms[start:stop] = total
        loudness[start:stop] = (power * a_weights).sum(axis=1)
        centroid[start:stop] = (power * freqs).sum(axis=1) / np.maximum(total, 1e-12)
        for name, rows in band_rows.items():
            bands[name][start:stop] = power[:, rows].sum(axis=1)
        spectrum_db[:, start:stop] = db(power @ bank.T).T
        chroma[:, start:stop] = (power @ pitch_rows.T).T

    spectrum_db = np.maximum(spectrum_db, spectrum_db.max() - 80.0)

    # Transients: spectral flux, the rise across bands from one frame to the next.
    flux = np.maximum(0.0, np.diff(spectrum_db, axis=1, prepend=spectrum_db[:, :1]))
    onset_envelope = flux.mean(axis=0)
    onset_envelope = onset_envelope / (float(np.percentile(onset_envelope, 99)) or 1.0)
    low_flux = flux[:12].mean(axis=0)   # roughly below 150 Hz: kick and bass hits
    low_flux = low_flux / (float(np.percentile(low_flux, 99)) or 1.0)

    local_average = np.convolve(onset_envelope, np.ones(43) / 43.0, mode="same")   # ~0.5 s
    onset_frames, _ = find_peaks(onset_envelope, height=local_average + 0.08, distance=4, prominence=0.08)
    onsets = [{"t": round(float(f * hop_seconds), 3), "strength": round(float(onset_envelope[f]), 3)}
              for f in onset_frames]

    tempo, beat_frames = track_beats(onset_envelope, hop_seconds)
    beats = [round(float(f * hop_seconds), 3) for f in beat_frames]

    # Bar phase, assuming 4/4: the beat-of-four that is, on average, the loudest. (Low-frequency
    # hits alone are a poor guide: a kick pattern often leans on other beats.)
    beat_span = max(1, int(np.median(np.diff(beat_frames))))
    loud = db(loudness)

    def accent(frame):
        return float(loud[frame:frame + beat_span].mean())

    phase_strength = [float(np.mean([accent(f) for f in beat_frames[p::4]])) for p in range(4)]
    downbeats = beats[int(np.argmax(phase_strength))::4]

    # Structural novelty (Foote): a checkerboard kernel slid along the self-similarity matrix
    # of the spectrum's shape. High where what follows differs from what came before.
    block = max(1, int(round(1.0 / (NOVELTY_RATE * hop_seconds))))
    usable = (frames // block) * block
    pooled = spectrum_db[:, :usable].reshape(SPECTRUM_BANDS, -1, block).mean(axis=2)
    pooled = (pooled - pooled.mean(axis=1, keepdims=True)) / (pooled.std(axis=1, keepdims=True) + 1e-9)
    pooled = pooled / (np.linalg.norm(pooled, axis=0, keepdims=True) + 1e-9)
    similarity = pooled.T @ pooled
    half = int(NOVELTY_KERNEL_SECONDS * NOVELTY_RATE)
    axis = np.arange(-half, half) + 0.5
    taper = np.exp(-0.5 * (axis / (half * 0.5)) ** 2)
    kernel = np.outer(taper, taper) * np.outer(np.sign(axis), np.sign(axis))
    edge = np.pad(similarity, half, mode="edge")
    novelty = np.array([float((edge[i:i + 2 * half, i:i + 2 * half] * kernel).sum())
                        for i in range(similarity.shape[0])])
    novelty = np.maximum(novelty, 0.0)
    novelty = novelty / (novelty.max() or 1.0)
    novelty_rate = 1.0 / (block * hop_seconds)
    peaks, _ = find_peaks(novelty, distance=int(novelty_rate * 3), prominence=0.04)
    sections = [{"t": round(float(p / novelty_rate), 2), "novelty": round(float(novelty[p]), 3)} for p in peaks]

    # Harmonic novelty: the same checkerboard measure on pitch-class content alone, with a
    # shorter kernel. High where the harmony after a moment differs from the harmony before it,
    # whatever the loudness or timbre are doing.
    pooled_chroma = np.sqrt(chroma[:, :usable].reshape(12, -1, block).mean(axis=2))
    pooled_chroma = pooled_chroma / (np.linalg.norm(pooled_chroma, axis=0, keepdims=True) + 1e-9)
    harmonic_similarity = pooled_chroma.T @ pooled_chroma
    h_half = int(HARMONY_KERNEL_SECONDS * NOVELTY_RATE)
    h_axis = np.arange(-h_half, h_half) + 0.5
    h_taper = np.exp(-0.5 * (h_axis / (h_half * 0.5)) ** 2)
    h_kernel = np.outer(h_taper, h_taper) * np.outer(np.sign(h_axis), np.sign(h_axis))
    h_edge = np.pad(harmonic_similarity, h_half, mode="edge")
    harmonic_novelty = np.array([float((h_edge[i:i + 2 * h_half, i:i + 2 * h_half] * h_kernel).sum())
                                 for i in range(harmonic_similarity.shape[0])])
    harmonic_novelty = np.maximum(harmonic_novelty, 0.0)
    harmonic_novelty = harmonic_novelty / (harmonic_novelty.max() or 1.0)
    h_peaks, _ = find_peaks(harmonic_novelty, distance=int(novelty_rate * 2), prominence=0.05)
    harmonic_changes = [{"t": round(float(p / novelty_rate), 2), "novelty": round(float(harmonic_novelty[p]), 3)}
                        for p in h_peaks]
    # Strongest pitch class in each pooled frame: a crude trace of the root / tonal centre.
    dominant = [int(c) for c in pooled_chroma.argmax(axis=0)]

    def series(values, digits):
        return [round(float(v), digits) for v in values]

    with open(path, "rb") as handle:
        digest = hashlib.sha1(handle.read()).hexdigest()

    return {
        "source": {"file": os.path.basename(path), "sha1": digest, "duration": round(duration, 3), "sample_rate": sr},
        "method": {
            "tool": "tools/analyze_audio.py", "n_fft": N_FFT, "hop": HOP, "bands_hz": BANDS, "meter_assumed": "4/4",
            "notes": "dB values are relative to digital full scale. Onset strengths are normalised to their "
                     "99th percentile. Downbeats are an estimate: the beat-of-four that is loudest on average.",
        },
        "tempo_bpm": round(float(tempo), 2),
        "beats": beats,
        "downbeats": downbeats,
        "onsets": onsets,
        "section_candidates": sections,
        "frames": {
            "hop_seconds": hop_seconds,
            "rms_db": series(db(rms), 2),
            "loudness_db": series(db(loudness), 2),
            "low_db": series(db(bands["low"]), 2),
            "mid_db": series(db(bands["mid"]), 2),
            "high_db": series(db(bands["high"]), 2),
            "centroid_hz": series(centroid, 0),
            "onset_strength": series(onset_envelope, 3),
            "low_onset_strength": series(low_flux, 3),
        },
        "novelty": {"hop_seconds": 1.0 / novelty_rate, "values": series(novelty, 3)},
        "harmony": {
            "hop_seconds": 1.0 / novelty_rate,
            "novelty": series(harmonic_novelty, 3),
            "change_candidates": harmonic_changes,
            "dominant_pitch_class": dominant,
            "pitch_class_names": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
        },
    }


# ---------------------------------------------------------------- report (reads the JSON only)


def report(data, start, end):
    frames = data["frames"]
    hop = frames["hop_seconds"]

    def span(name, a, b):
        first = max(0, int(a / hop))
        return frames[name][first:max(first + 1, int(b / hop))]

    def mean(name, a, b):
        values = span(name, a, b)
        return sum(values) / len(values)

    def peak(name, a, b):
        return max(span(name, a, b))

    beat = 60.0 / data["tempo_bpm"]
    print("%s  %.2f BPM (beat %.3f s, bar %.3f s)  duration %s" % (
        data["source"]["file"], data["tempo_bpm"], beat, beat * 4, timeline.format_time(data["source"]["duration"])))

    print("\nSection-change candidates (novelty peaks):")
    for s in data["section_candidates"]:
        if start - 10 <= s["t"] <= end + 10:
            print("   %s  novelty %.2f" % (timeline.format_time(s["t"]), s["novelty"]))

    harmony = data.get("harmony")
    if harmony:
        names = harmony["pitch_class_names"]
        hh = harmony["hop_seconds"]
        print("\nHarmonic-change candidates:")
        for s in harmony["change_candidates"]:
            if start <= s["t"] <= end:
                print("   %s  harmonic novelty %.2f" % (timeline.format_time(s["t"]), s["novelty"]))
        print("\nPer bar ('bar' from the cue file's tempo):  loudness, low, high, strongest pitch classes, harmonic novelty at the bar line")
        bar = timeline.BAR
        t = timeline.DOWNBEAT + bar * int((start - timeline.DOWNBEAT) // bar)
        while t < end:
            if t >= start:
                a, b = int(t / hh), int((t + bar) / hh)
                counts = {}
                for c in harmony["dominant_pitch_class"][a:b]:
                    counts[c] = counts.get(c, 0) + 1
                top = sorted(counts, key=lambda c: -counts[c])[:2]
                hn = harmony["novelty"][min(len(harmony["novelty"]) - 1, a)]
                print("   %s  %6.1f %6.1f %6.1f   %-7s  %.2f %s" % (
                    timeline.format_time(t), mean("loudness_db", t, t + bar), mean("low_db", t, t + bar),
                    mean("high_db", t, t + bar), "/".join(names[c] for c in top), hn, "#" * int(hn * 30)))
            t += bar

    print("\nPer second:  loudness / low / mid / high (dB), brightness (Hz), novelty")
    nh = data["novelty"]["hop_seconds"]
    t = start
    while t < end:
        v = data["novelty"]["values"][min(len(data["novelty"]["values"]) - 1, int(t / nh))]
        print("   %s  %6.1f %6.1f %6.1f %6.1f  %5.0f  %.2f %s" % (
            timeline.format_time(t), mean("loudness_db", t, t + 1), mean("low_db", t, t + 1),
            mean("mid_db", t, t + 1), mean("high_db", t, t + 1), mean("centroid_hz", t, t + 1), v, "#" * int(v * 30)))
        t += 1.0

    downbeats = set(data["downbeats"])
    print("\nPer beat ('|' marks an estimated bar start):  loudness, low, mid, high, brightness, onset, low hit")
    beats = [b for b in data["beats"] if start <= b < end]
    for i, b in enumerate(beats):
        nxt = beats[i + 1] if i + 1 < len(beats) else b + beat
        print(" %s %s  %6.1f %6.1f %6.1f %6.1f  %5.0f   %4.2f   %4.2f" % (
            "|" if b in downbeats else " ", timeline.format_time(b),
            mean("loudness_db", b, nxt), mean("low_db", b, nxt), mean("mid_db", b, nxt), mean("high_db", b, nxt),
            mean("centroid_hz", b, nxt), peak("onset_strength", b - 0.03, b + 0.08),
            peak("low_onset_strength", b - 0.03, b + 0.08)))

    print("\nStrongest transients:")
    strong = sorted((o for o in data["onsets"] if start <= o["t"] < end), key=lambda o: -o["strength"])[:30]
    for o in sorted(strong, key=lambda o: o["t"]):
        print("   %s  %.2f" % (timeline.format_time(o["t"]), o["strength"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audio", help="music file (default: the audio file in audio/)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--report", nargs=2, metavar=("START", "END"),
                        help="print a breakdown of an interval from the existing analysis")
    args = parser.parse_args()

    if args.report:
        with open(args.output, encoding="utf-8") as handle:
            report(json.load(handle), timeline.parse_time(args.report[0]), timeline.parse_time(args.report[1]))
        return

    audio = find_audio(args.audio)
    if not audio:
        sys.exit("No music file found: put the track in audio/ or pass --audio.")
    data = analyse(audio)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(data, handle, separators=(",", ":"))
    print("%s: %.2f BPM, %d beats, %d onsets, %d section candidates -> %s" % (
        data["source"]["file"], data["tempo_bpm"], len(data["beats"]), len(data["onsets"]),
        len(data["section_candidates"]), args.output))


if __name__ == "__main__":
    main()
