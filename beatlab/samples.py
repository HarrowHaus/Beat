"""beatlab.samples — CC0 one-shot loading and repitching.

Kit: Boochi44/free-drum-samples (CC0 1.0), cloned at build time; samples are
resampled to retune (classic 808 repitch — pitch and length move together).
"""
import os
import numpy as np
import soundfile as sf
from scipy import signal as sps

from .engine import SR, note_to_hz

KIT_DIR = os.environ.get(
    "BEATLAB_KIT",
    "/tmp/claude-0/-home-user-Beat/46e08380-25a6-5652-aa66-dd3b51c68911/scratchpad/"
    "free-drum-samples/drum-samples/01-hard-trap",
)

_cache = {}


def load(rel):
    if rel not in _cache:
        x, sr = sf.read(os.path.join(KIT_DIR, rel))
        if x.ndim > 1:
            x = x.mean(axis=1)
        if sr != SR:
            x = sps.resample_poly(x, SR, sr)
        _cache[rel] = x
    return _cache[rel]


def detect_root_hz(x, fmax=200.0):
    """Autocorrelation pitch detect on the sustained portion of a bass one-shot."""
    seg = x[int(0.1 * SR): int(0.6 * SR)]
    seg = seg - seg.mean()
    ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    lo = int(SR / fmax)
    peak = lo + np.argmax(ac[lo: int(SR / 25)])
    return SR / peak


def repitch(x, semitones):
    ratio = 2 ** (semitones / 12)
    n_out = int(len(x) / ratio)
    return sps.resample(x, n_out)


class Tuned808:
    """A sampled 808 retunable to any MIDI note."""

    def __init__(self, rel="808s/808-bass-dist.wav"):
        self.raw = load(rel)
        self.root_hz = detect_root_hz(self.raw)

    def note(self, midi, dur=None):
        target = note_to_hz(midi)
        semis = 12 * np.log2(target / self.root_hz)
        x = repitch(self.raw, semis)
        if dur is not None:
            n = int(dur * SR)
            if len(x) > n:  # fade instead of hard truncate
                x = x[:n].copy()
                f = min(int(0.02 * SR), n)
                x[-f:] *= np.linspace(1, 0, f)
            elif len(x) < n:  # loop-sustain the tail for long notes
                x = np.pad(x, (0, n - len(x)))
        return x
