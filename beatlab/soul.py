"""beatlab.soul — gospel/soul-era instruments: pitched vocal chops, organ,
e-piano, rich choir, vinyl texture, lo-fi degradation.

The vocal-chop voice is a glottal-ish pulse source through vowel formant
filters with vibrato and formant-shift — the 'pitched-up soul sample'
timbre synthesized from scratch (no copyrighted sample needed).
"""
import numpy as np
from scipy import signal as sps

from .engine import SR, env_adsr, env_exp, note_to_hz, soft_clip, butter, _saw_bank

# vowel formant tables (F1, F2, F3) — male-ish, shifted up for chipmunk color
VOWELS = {
    "ah": (730, 1090, 2440),
    "eh": (530, 1840, 2480),
    "ee": (270, 2290, 3010),
    "oh": (570, 840, 2410),
    "oo": (300, 870, 2240),
}


def synth_vox(midi, dur, vowel="ah", formant_shift=1.45, vib_hz=5.5,
              vib_depth=0.35, breath=0.06, seed=61):
    """One sung-vowel note, pitched-up-soul-chop character."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    f0 = note_to_hz(midi)
    # vibrato that eases in (natural singing)
    vib = vib_depth * np.minimum(t / 0.18, 1) * np.sin(2 * np.pi * vib_hz * t)
    f = f0 * 2 ** (vib / 12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    # glottal-ish source: saw softened + pulse energy
    src = sps.sawtooth(ph) * 0.6 + sps.square(ph, duty=0.3) * 0.25
    src += breath * rng.standard_normal(n)
    y = np.zeros(n)
    for fc, g in zip(VOWELS[vowel], (1.0, 0.7, 0.3)):
        fc = min(fc * formant_shift, 16000)
        sos = sps.butter(2, [fc * 0.82 / (SR / 2), min(fc * 1.22, 20000) / (SR / 2)],
                         'band', output='sos')
        y += g * sps.sosfilt(sos, src)
    y = butter(y, 6 * f0, 'low') + 0.12 * butter(src, 8000, 'high') * env_exp(n, 0.05)
    return y * env_adsr(n, a=0.02, d=0.08, s=0.85, r=min(0.1, dur * 0.25))


def chop_phrase(notes, vowel_cycle=("oh", "ah", "eh", "oo"), gap=0.012, **kw):
    """Stitch vox notes into a chopped phrase with hard cut edges (MPC chop feel)."""
    bufs = []
    for i, (midi, dur) in enumerate(notes):
        x = synth_vox(midi, dur, vowel=vowel_cycle[i % len(vowel_cycle)],
                      seed=61 + i, **kw)
        edge = int(0.004 * SR)  # hard chop: tiny fades only
        x[:edge] *= np.linspace(0, 1, edge)
        x[-edge:] *= np.linspace(1, 0, edge)
        bufs.append(x)
        bufs.append(np.zeros(int(gap * SR)))
    return np.concatenate(bufs)


def synth_organ(midis, dur, click=0.6):
    """Gospel Hammond-ish: drawbar sines + key click + slow rotary shimmer."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rot = 1 + 0.04 * np.sin(2 * np.pi * 0.8 * t)  # chorale-speed rotary
    x = np.zeros(n)
    for m in midis:
        f = note_to_hz(m)
        for mult, g in ((0.5, 0.6), (1, 1.0), (2, 0.7), (3, 0.4), (4, 0.3), (6, 0.15)):
            x += g * np.sin(2 * np.pi * f * mult * t * rot + 0.1 * np.sin(2 * np.pi * 6.5 * t))
        ck = np.random.default_rng(int(m)).standard_normal(int(0.006 * SR))
        x[:len(ck)] += click * 0.15 * butter(ck, 2500, 'high')
    x /= max(len(midis), 1)
    return x * env_adsr(n, a=0.01, d=0.05, s=0.95, r=min(0.15, dur * 0.3)) * 0.7


def synth_epiano(midi, dur, seed=71):
    """FM Rhodes-ish key: 2-op FM, bell-ish tine + soft body."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note_to_hz(midi)
    idx = 1.8 * env_exp(n, 0.3)
    tine = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 14.02 * t)) * 0.35
    body = np.sin(2 * np.pi * f * t + 0.9 * env_exp(n, 0.5) * np.sin(2 * np.pi * f * 1.0 * t))
    x = (body + tine) * env_adsr(n, a=0.004, d=0.35, s=0.45, r=min(0.2, dur * 0.3))
    return soft_clip(x, 1.2) * 0.8


def synth_choir(midis, dur, vowel="ah", spread=14, seed=81):
    """Big stacked choir: multiple detuned vox per note, no chop edges."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for i, m in enumerate(midis):
        for v in range(3):
            det = rng.uniform(-spread, spread) / 100
            x += synth_vox(m + det * 0.12, dur, vowel=vowel, formant_shift=1.1,
                           vib_depth=0.2, vib_hz=4.5 + 0.4 * v, seed=seed + i * 3 + v)
    x /= (len(midis) * 3)
    return x * env_adsr(n, a=min(0.3, dur * 0.25), d=0.1, s=0.9, r=min(0.6, dur * 0.3)) * 1.6


def vinyl_bed(dur, seed=91):
    """Dusty vinyl noise + crackle ticks."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    hiss = butter(rng.standard_normal(n), 3000, 'high') * 0.02
    crackle = np.zeros(n)
    ticks = rng.integers(0, n, size=int(dur * 9))
    crackle[ticks] = rng.uniform(-1, 1, len(ticks))
    crackle = butter(crackle, 1200, 'high') * 0.35
    wow = 1 + 0.15 * np.sin(2 * np.pi * 0.55 * np.arange(n) / SR)
    return (hiss + crackle) * wow


def crush(x, bits=8, downsample=3, mix=0.5):
    """Bitcrush/rate-reduce for industrial grit."""
    q = 2 ** (bits - 1)
    y = np.round(x * q) / q
    y = np.repeat(y[::downsample], downsample)[:len(x)]
    return x * (1 - mix) + y * mix


def tape_saturate(x, drive=2.2):
    """Asymmetric tape-ish saturation with HF rolloff."""
    y = np.tanh(x * drive + 0.08 * x ** 2) / np.tanh(drive)
    return butter(y, 12000, 'low')
