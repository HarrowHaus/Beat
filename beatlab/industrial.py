"""beatlab.industrial — Yeezus-era instrument rack.

Acid 303 voice with envelope-swept resonant lowpass (block-wise RBJ biquad
with state carry), rock toms, hollow minimal stabs, brass-cannon stacks,
scream-proxy FX, stomp claps.
"""
import numpy as np
from scipy import signal as sps

from .engine import SR, env_exp, env_adsr, note_to_hz, soft_clip, butter

BLOCK = 64


def resonant_lp(x, cutoff_env, q=8.0):
    """Time-varying resonant 2-pole lowpass (RBJ), block-wise with state carry."""
    y = np.empty_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), BLOCK):
        fc = float(np.clip(cutoff_env[min(i + BLOCK // 2, len(x) - 1)], 40, SR * 0.45))
        w0 = 2 * np.pi * fc / SR
        alpha = np.sin(w0) / (2 * q)
        cw = np.cos(w0)
        b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
        a = np.array([1 + alpha, -2 * cw, 1 - alpha])
        b, a = b / a[0], a / a[0]
        y[i:i + BLOCK], zi = sps.lfilter(b, a, x[i:i + BLOCK], zi=zi)
    return y


def synth_303(midi, dur, accent=False, slide_from=None, cutoff=900, res=9.0,
              env_amt=2800, wave="saw", drive=3.5, crushed=True):
    """TB-303-style acid voice. accent = louder + wider filter sweep;
    slide_from = exponential pitch glide from another MIDI note."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f1 = note_to_hz(midi)
    if slide_from is not None:
        f0 = note_to_hz(slide_from)
        f = f0 * (f1 / f0) ** np.minimum(t / min(0.06, dur * 0.5), 1)
    else:
        f = np.full(n, f1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sps.sawtooth(ph) if wave == "saw" else sps.square(ph)
    amt = env_amt * (1.6 if accent else 1.0)
    cut_env = cutoff + amt * env_exp(n, 0.09 if accent else 0.16)
    x = resonant_lp(x, cut_env, q=res)
    x *= env_adsr(n, a=0.003, d=0.08, s=0.55, r=min(0.03, dur * 0.2))
    x = soft_clip(x * (1.5 if accent else 1.0), drive)
    if crushed:  # On Sight broken-speaker edge
        q = 2 ** 5
        x = 0.65 * x + 0.35 * np.round(x * q) / q
    return x * 0.8


def synth_rock_tom(midi=45, dur=0.4, seed=301):
    """Floor tom: triangle-ish pitch drop + skin noise, roomy but tight."""
    n = int(dur * SR)
    f0 = note_to_hz(midi)
    f = f0 * 2 ** (-np.linspace(0, 0.5, n))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    body += 0.3 * np.sin(2 * 2 * np.pi * np.cumsum(f) / SR)
    skin = np.random.default_rng(seed).standard_normal(n) * env_exp(n, 0.008)
    x = body * env_exp(n, 0.13) + 0.25 * butter(skin, 2000, 'high')
    return soft_clip(x, 2.2) * 0.95


def synth_stab(midis, dur, pw=0.18, seed=311):
    """New Slaves-style hollow menacing stab: narrow-pulse detuned pair,
    bandpassed, hard attack, fast die."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, m in enumerate(midis):
        f = note_to_hz(m)
        for det in (-7, 0, 6):  # cents
            fd = f * 2 ** (det / 1200)
            x += sps.square(2 * np.pi * fd * t + 0.7 * i, duty=pw)
    x /= (len(midis) * 3)
    x = butter(butter(x, 3800, 'low'), 140, 'high')
    return x * env_adsr(n, a=0.002, d=0.25, s=0.35, r=min(0.08, dur * 0.3))


def synth_brass(midi, dur, voices=9, seed=321):
    """TNGHT-style brass cannon: big detuned saw stack, pitch scoops UP into
    the note (horn attack), formant bump ~500-1500 Hz, saturated."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    f0 = note_to_hz(midi)
    x = np.zeros(n)
    for v in range(voices):
        det = rng.uniform(-18, 18)
        scoop = 2 ** (-1.2 * np.exp(-t / 0.045) / 12)  # rise ~1 semitone into pitch
        f = f0 * 2 ** (det / 1200) * scoop
        x += sps.sawtooth(2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6.28))
    x /= voices
    y = butter(x, 4500, 'low')
    for fc, g in ((520, 1.0), (1150, 0.6)):  # brassy formant push
        sos = sps.butter(2, [fc * 0.7 / (SR / 2), fc * 1.4 / (SR / 2)], 'band', output='sos')
        y += g * 0.6 * sps.sosfilt(sos, x)
    y *= env_adsr(n, a=0.012, d=0.1, s=0.85, r=min(0.09, dur * 0.25))
    return soft_clip(y, 2.8) * 0.85


def synth_scream(dur=0.5, f_start=900, f_end=1600, seed=331):
    """Scream-proxy FX: formant-swept saw+noise cluster, pitch rising, torn."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    f = np.geomspace(f_start * 0.35, f_end * 0.4, n)
    src = sps.sawtooth(2 * np.pi * np.cumsum(f) / SR) + 0.7 * rng.standard_normal(n)
    sweep = np.geomspace(f_start, f_end, n)
    y = np.zeros(n)
    for mult, g in ((1.0, 1.0), (1.9, 0.6), (3.1, 0.35)):
        out = np.zeros(n)
        for i in range(0, n, 512):
            fc = sweep[min(i + 256, n - 1)] * mult
            lo, hi = fc * 0.75 / (SR / 2), min(fc * 1.3, 19000) / (SR / 2)
            sos = sps.butter(2, [lo, hi], 'band', output='sos')
            out[i:i + 512] = sps.sosfilt(sos, src[i:i + 512])
        y += g * out
    env = env_adsr(n, a=0.02, d=0.1, s=0.8, r=min(0.12, dur * 0.3))
    return soft_clip(y * env, 4.0) * 0.7


def synth_stomp_clap(seed=341):
    """Stadium stomp-clap: big group clap + low thud."""
    n = int(0.3 * SR)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for off in (0, 0.009, 0.02, 0.031):
        o = int(off * SR)
        x[o:] += rng.standard_normal(n - o) * env_exp(n - o, 0.05) * 0.7
    x = butter(butter(x, 700, 'high'), 7000, 'low')
    thud = np.sin(2 * np.pi * 85 * np.arange(n) / SR * 2 ** (-np.arange(n) / n)) * env_exp(n, 0.05)
    return soft_clip(x + 0.8 * thud, 2.5) * 0.85


def synth_pant(dur=0.22, seed=351):
    """Breath/pant percussion (Black Skinhead texture)."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    env = np.sin(np.pi * np.arange(n) / n) ** 2
    sos = sps.butter(2, [500 / (SR / 2), 4000 / (SR / 2)], 'band', output='sos')
    return sps.sosfilt(sos, x) * env * 0.5
