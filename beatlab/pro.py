"""beatlab.pro — release-grade sound sources.

- Kit808: professionally produced tuned 808s (chromatic, styles: Long,
  Distorted, Punchy, Sub, Classic, Vintage, Bright), pitched to any MIDI note.
- DrumKit: velocity-layered pro one-shots (soft/mid/hard).
- ChoirSampler: real recorded choir sustains (Sonatina Chorus, male/female),
  chromatic, pitched and stacked into chords.
- RiserKit: produced risers/downlifters.
- SurgeSynth: Surge XT rendered headless via surgepy with factory patches.
- conv_reverb: convolution with real impulse responses (EMT-140 plate,
  Voxengo halls).

Sources live in the session scratchpad (see README for clone commands);
override with BEATLAB_PRO env var.
"""
import glob
import os
import re

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .engine import SR

PRO_DIR = os.environ.get(
    "BEATLAB_PRO",
    "/tmp/claude-0/-home-user-Beat/46e08380-25a6-5652-aa66-dd3b51c68911/scratchpad")

NOTE_VAL = {"C": 0, "Cs": 1, "Db": 1, "D": 2, "Ds": 3, "Eb": 3, "E": 4,
            "F": 5, "Fs": 6, "Gb": 6, "G": 7, "Gs": 8, "Ab": 8, "A": 9,
            "As": 10, "Bb": 10, "B": 11}


def _load_mono(path):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        x = resample_poly(x, SR, sr)
    return x


def _pitch(x, semitones):
    """Playback-rate pitch shift (tape-style; duration changes)."""
    if abs(semitones) < 0.01:
        return x
    ratio = 2 ** (-semitones / 12)
    n = max(int(len(x) * ratio), 8)
    idx = np.linspace(0, len(x) - 1, n)
    return np.interp(idx, np.arange(len(x)), x)


class Kit808:
    """Tuned 808 sampler: nearest chromatic sample, repitched to target."""

    def __init__(self, style="Long"):
        self.notes = {}
        for p in glob.glob(f"{PRO_DIR}/Free-808-Producer-Kit/808_kit/{style}/*.wav"):
            m = re.search(r"_([A-G]s?)(\d)\.wav$", p)
            if m:
                midi = 12 * (int(m.group(2)) + 1) + NOTE_VAL[m.group(1)]
                self.notes[midi] = p
        if not self.notes:
            raise FileNotFoundError(f"no 808s for style {style}")
        self._cache = {}

    def note(self, midi, dur, fade=0.03):
        base = midi % 12 + 36  # kit spans C2-B2 (midi 36-47)
        if base not in self._cache:
            self._cache[base] = _load_mono(self.notes[base])
        x = _pitch(self._cache[base], midi - base)
        n = int(dur * SR)
        if len(x) > n:
            x = x[:n].copy()
            f = min(int(fade * SR), n // 2)
            x[-f:] *= np.linspace(1, 0, f)
        return x


class DrumKit:
    """Velocity-layered pro one-shots: name('Kick_Trap', vel='hard')."""

    def __init__(self):
        self.files = {}
        root = f"{PRO_DIR}/Free-Drum-Producer-Kit"
        for p in glob.glob(f"{root}/**/*.wav", recursive=True):
            self.files[os.path.basename(p)[:-4]] = p
        self._cache = {}

    def one(self, name, vel="hard", gain=1.0):
        key = f"{name}_{vel}"
        if key not in self._cache:
            if key not in self.files:
                raise KeyError(f"{key} not in kit ({sorted(self.files)[:8]}...)")
            self._cache[key] = _load_mono(self.files[key])
        return self._cache[key] * gain


class ChoirSampler:
    """Real recorded choir (Sonatina Chorus): chords from chromatic sustains."""

    def __init__(self):
        self.samples = {"male": {}, "female": {}}
        pat = f"{PRO_DIR}/sso/Sonatina Symphonic Orchestra/Samples/Chorus/*.wav"
        for p in glob.glob(pat):
            m = re.search(r"chorus-(male|female)-([a-g])(#?)(\d)\.wav$", p)
            if m:
                g, note, sharp, octv = m.groups()
                val = NOTE_VAL[note.upper() + ("s" if sharp else "")]
                midi = 12 * (int(octv) + 1) + val
                self.samples[m.group(1)][midi] = p
        self._cache = {}

    def _one(self, midi, gender):
        bank = self.samples[gender]
        base = min(bank, key=lambda k: abs(k - midi))
        if (gender, base) not in self._cache:
            self._cache[(gender, base)] = _load_mono(bank[base])
        return _pitch(self._cache[(gender, base)], midi - base)

    def chord(self, midis, dur, gender="male", attack=0.15, release=0.3):
        n = int(dur * SR)
        out = np.zeros(n)
        for m in midis:
            x = self._one(m, gender)
            x = np.tile(x, int(np.ceil(n / len(x))))[:n] if len(x) < n else x[:n]
            out += x
        out /= max(len(midis), 1)
        a, r = int(attack * SR), int(release * SR)
        out[:a] *= np.linspace(0, 1, a)
        out[-r:] *= np.linspace(1, 0, r)
        return out


class RiserKit:
    def __init__(self):
        root = f"{PRO_DIR}/Free-Riser-Producer-Kit"
        self.risers = sorted(glob.glob(f"{root}/**/*Riser*.wav", recursive=True))
        self.downs = sorted(glob.glob(f"{root}/**/*Downlifter*.wav", recursive=True))

    def riser(self, i=0, dur=None):
        x = _load_mono(self.risers[i % len(self.risers)])
        if dur:  # keep the END of the riser at the hit point
            n = int(dur * SR)
            x = x[-n:] if len(x) > n else x
        return x

    def downlifter(self, i=0):
        return _load_mono(self.downs[i % len(self.downs)])


class SurgeSynth:
    """Surge XT factory patches rendered offline via surgepy."""

    def __init__(self, patch, sr=SR):
        import surgepy
        self.s = surgepy.createSurge(sr)
        matches = glob.glob(f"/usr/share/surge-xt/patches_factory/**/{patch}.fxp",
                            recursive=True) or \
            glob.glob(f"/usr/share/surge-xt/patches_3rdparty/**/{patch}.fxp",
                      recursive=True)
        if not matches:
            raise FileNotFoundError(f"Surge patch not found: {patch}")
        self.s.loadPatch(matches[0])
        self.block = self.s.getBlockSize()

    def render(self, notes, total_dur, vel=100, tail=1.5):
        """notes: [(t_sec, midi, dur_sec)] -> stereo (2, n) at SR."""
        nblocks = int(np.ceil((total_dur + tail) * SR / self.block))
        buf = self.s.createMultiBlock(nblocks)
        events = []
        for t, m, d in notes:
            events.append((t, "on", m))
            events.append((t + d, "off", m))
        events.sort()
        cursor = 0
        for t, kind, m in events:
            b = int(t * SR / self.block)
            if b > cursor:
                self.s.processMultiBlock(buf, cursor, b - cursor)
                cursor = b
            if kind == "on":
                self.s.playNote(0, int(m), vel, 0)
            else:
                self.s.releaseNote(0, int(m), 0)
        if cursor < nblocks:
            self.s.processMultiBlock(buf, cursor, nblocks - cursor)
        return np.array(buf[:2])


def conv_reverb(stereo, ir_path, mix=0.25):
    """Convolution reverb with a real IR (expects (2, n) float array)."""
    from pedalboard import Pedalboard, Convolution
    board = Pedalboard([Convolution(ir_path, mix=mix)])
    return board(stereo.astype(np.float32), SR)


IR = {
    "plate_med": f"{PRO_DIR}/irs/emt140/emt_140_medium_1.wav",
    "plate_dark": f"{PRO_DIR}/irs/emt140/emt_140_dark_1.wav",
    "hall": f"{PRO_DIR}/irs/voxengo/Large Wide Echo Hall.wav",
    "room": f"{PRO_DIR}/irs/voxengo/Small Drum Room.wav",
    "church": f"{PRO_DIR}/irs/voxengo/St Nicolaes Church.wav",
}
