"""beatlab.crate — real-instrument 'old record' factory.

Plays REAL recorded instruments (VSCO-2 Community Edition, CC0: upright
piano, tremolo solo violin, chapel organ) into an original composition,
then prints it like a worn 197x record: wow/flutter, vinyl noise, dark
lowpass, mono-ish image, gentle saturation. The output is crate-dig sample
material that is ours — the $uicideboy$/Memphis chop tradition without the
clearance problem.
"""
import glob
import os
import re

import numpy as np

from .engine import SR, butter, soft_clip
from .pro import PRO_DIR, NOTE_VAL, _load_mono, _pitch

VSCO = f"{PRO_DIR}/vsco"


class VSCOSampler:
    """Generic VSCO folder sampler: parses <Note><Octave> from filenames."""

    def __init__(self, pattern, prefer=("mf", "f", "pp"), name="inst"):
        self.notes = {}
        for p in glob.glob(pattern):
            m = re.search(r"_([A-G]#?b?)(\d)_", os.path.basename(p))
            if not m:
                continue
            note, octv = m.groups()
            note = note.replace("b", "s")  # crude flat handling
            val = NOTE_VAL.get(note.replace("#", "s"))
            if val is None:
                continue
            midi = 12 * (int(octv) + 1) + val
            self.notes.setdefault(midi, []).append(p)
        if not self.notes:
            raise FileNotFoundError(pattern)
        self.prefer = prefer
        self.name = name
        self._cache = {}

    def _file(self, midi, rr=0):
        base = min(self.notes, key=lambda k: abs(k - midi))
        files = sorted(self.notes[base])
        for dyn in self.prefer:  # prefer a dynamic layer if present
            hits = [f for f in files if f"_{dyn}_" in f]
            if hits:
                files = hits
                break
        return base, files[rr % len(files)]

    def note(self, midi, dur, rr=0, fade=0.05):
        base, path = self._file(midi, rr)
        if path not in self._cache:
            self._cache[path] = _load_mono(path)
        x = _pitch(self._cache[path], midi - base)
        n = int(dur * SR)
        if len(x) > n:
            x = x[:n].copy()
            f = min(int(fade * SR), n // 2)
            x[-f:] *= np.linspace(1, 0, f)
        return x


def wow_flutter(x, wow_hz=0.6, wow_depth=0.004, flutter_hz=7.0, flutter_depth=0.0008):
    """Playback-speed instability of a worn turntable/tape."""
    n = len(x)
    t = np.arange(n) / SR
    warp = t + wow_depth * np.sin(2 * np.pi * wow_hz * t) / (2 * np.pi * wow_hz) \
             + flutter_depth * np.sin(2 * np.pi * flutter_hz * t) / (2 * np.pi * flutter_hz)
    idx = np.clip(warp * SR, 0, n - 1)
    return np.interp(idx, np.arange(n), x)


def print_dusty(stereo, year_tone=6800, hiss=0.010, crackle_rate=8.0, seed=77):
    """Worn-record print: wow/flutter, dark LP, vinyl noise, narrow, warm clip."""
    L = wow_flutter(stereo[0])
    R = wow_flutter(stereo[1], wow_hz=0.6)  # same warp phase family
    y = np.stack([L, R])
    y = np.stack([butter(c, year_tone, 'low') for c in y])
    y = np.stack([butter(c, 55, 'high') for c in y])
    mid = y.mean(axis=0)
    y = 0.45 * y + 0.55 * np.stack([mid, mid])       # old narrow image
    y = soft_clip(y * 1.3, 1.8) * 0.85               # console warmth
    rng = np.random.default_rng(seed)
    n = y.shape[1]
    h = butter(rng.standard_normal(n), 2800, 'high') * hiss
    crackle = np.zeros(n)
    ticks = rng.integers(0, n, size=int(n / SR * crackle_rate))
    crackle[ticks] = rng.uniform(-0.6, 0.6, len(ticks))
    crackle = butter(crackle, 900, 'high') * 0.5
    return y + np.stack([h + crackle, h + crackle])
