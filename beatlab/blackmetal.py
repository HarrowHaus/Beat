"""beatlab.blackmetal — an original 'black metal recording' to be sampled.

Synthesizes a legally-original source track in the black metal idiom:
tremolo-picked power-chord guitar (double-tracked), traditional blast
beats, shrieked-vocal proxies, then prints the whole thing through a
'necro' demo-tape chain (harsh, thin, bitcrushed, hissy). The output is
the crate-dig 'sample' that the beat then chops — no clearance needed
because the source is ours.
"""
import numpy as np
from scipy import signal as sps

from .engine import SR, env_exp, note_to_hz, soft_clip, butter
from .industrial import synth_scream
from .pro import DrumKit


def _saw(f, n, det_cents, ph):
    t = np.arange(n) / SR
    return sps.sawtooth(2 * np.pi * f * 2 ** (det_cents / 1200) * t + ph)


def bm_tremolo(riff, sixteenth_s, seed=0):
    """One guitar take: riff = [(midi_root, n_sixteenths)], tremolo-picked
    power chords (root+5th+octave), per-strike humanization, amp distortion,
    cab filtering. Returns mono."""
    rng = np.random.default_rng(seed)
    n16 = int(sixteenth_s * SR)
    out = []
    for root, n_hits in riff:
        f = note_to_hz(root)
        for _ in range(n_hits):
            strike = np.zeros(n16)
            for iv, g in ((0, 1.0), (7, 0.9), (12, 0.55)):
                fi = f * 2 ** (iv / 12)
                strike += g * _saw(fi, n16, rng.uniform(-9, 9), rng.uniform(0, 6.28))
            pick = rng.standard_normal(int(0.004 * SR)) * 0.8
            strike[: len(pick)] += pick
            env = np.ones(n16)
            a = int(0.003 * SR)
            env[:a] = np.linspace(0.2, 1, a)
            env[-int(n16 * 0.08):] *= np.linspace(1, 0.55, int(n16 * 0.08))
            out.append(strike * env * rng.uniform(0.88, 1.0))
    x = np.concatenate(out)
    x = soft_clip(x * 2.2, 4.5)                    # amp
    x = butter(butter(x, 5200, 'low'), 95, 'high')  # cab
    x += 0.35 * butter(x, 2800, 'high')             # fizz
    return x * 0.8


def bm_blast(n_bars, bar_s, seed=0):
    """Traditional blast: alternating kick/snare 16ths, hat 8ths. Mono."""
    drums = DrumKit()
    kick = drums.one("Kick_Punchy", "mid", 0.9)
    snare = drums.one("Snare_Crack", "hard", 0.8)
    hat = drums.one("Hat_Closed", "mid", 0.5)
    rng = np.random.default_rng(seed)
    n = int(n_bars * bar_s * SR)
    out = np.zeros(n + SR)
    s16 = bar_s / 16
    for b in range(n_bars):
        for step in range(16):
            t = (b * bar_s + step * s16 + rng.uniform(-0.004, 0.004)) * SR
            i = max(int(t), 0)
            smp = kick if step % 2 == 0 else snare
            g = rng.uniform(0.85, 1.0)
            j = min(i + len(smp), len(out))
            out[i:j] += smp[: j - i] * g
            if step % 2 == 0:
                j2 = min(i + len(hat), len(out))
                out[i:j2] += hat[: j2 - i]
    return out[:n]


def bm_shriek(dur=1.0, seed=0):
    x = synth_scream(dur, f_start=650, f_end=2100, seed=seed)
    # ragged AM roughness — torn vocal cords, not a siren
    t = np.arange(len(x)) / SR
    rough = 1 - 0.45 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 31 * t + 3 * np.sin(2 * np.pi * 7 * t))))
    return x * rough


def print_necro(stereo):
    """The demo-tape print: thin, harsh, crushed, hissy, narrow."""
    from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter,
                            PeakFilter, Distortion, Bitcrush, Compressor)
    board = Pedalboard([
        HighpassFilter(150),
        PeakFilter(cutoff_frequency_hz=3100, gain_db=4.0, q=0.9),
        Distortion(drive_db=7),
        Bitcrush(bit_depth=10),
        LowpassFilter(9500),
        Compressor(threshold_db=-16, ratio=5, attack_ms=2, release_ms=60),
    ])
    y = board(stereo.astype(np.float32), SR)
    # narrow the image (bad room, one mic) + tape hiss
    mid = y.mean(axis=0)
    y = 0.3 * y + 0.7 * np.stack([mid, mid])
    rng = np.random.default_rng(13)
    hiss = butter(rng.standard_normal(y.shape[1]), 3500, 'high') * 0.006
    return y + hiss


# the original riff — E natural minor with a Phrygian F, ours entirely
RIFF_A = [(40, 8), (41, 4), (43, 4)]     # E . . F G
RIFF_B = [(40, 8), (43, 4), (45, 4)]     # E . . G A
RIFF_C = [(36, 8), (38, 4), (40, 4)]     # C . . D E
RIFF_D = [(41, 8), (40, 8)]              # F -> E (phrygian resolve)
RIFF_CYCLE = [RIFF_A, RIFF_B, RIFF_C, RIFF_D]


def render_source(bpm=144, n_bars=16):
    """The full original 'black metal song' the beat will sample."""
    bar_s = 4 * 60 / bpm
    s16 = bar_s / 16
    n = int(n_bars * bar_s * SR)
    L = np.zeros(n + 2 * SR)
    R = np.zeros(n + 2 * SR)
    for b in range(n_bars):
        riff = RIFF_CYCLE[b % 4]
        gl = bm_tremolo(riff, s16, seed=100 + b)
        gr = bm_tremolo(riff, s16, seed=200 + b)   # true double-track
        i = int(b * bar_s * SR)
        L[i:i + len(gl)] += gl
        R[i:i + len(gr)] += gr
    # blast beats from bar 4; drop out bars 12-13 for the 'atmospheric' gap
    for start, bars in ((4, 8), (14, 2)):
        bl = bm_blast(bars, bar_s, seed=start) * 0.75
        i = int(start * bar_s * SR)
        L[i:i + len(bl)] += bl
        R[i:i + len(bl)] += bl
    # shrieks at phrase turns
    for b, seed in ((7, 1), (11, 2), (15, 3)):
        sh = bm_shriek(1.1, seed=seed) * 0.6
        i = int((b * 4 + 2) * (bar_s / 4) * SR)
        L[i:i + len(sh)] += sh
        R[i:i + len(sh)] += sh * 0.8
    src = np.stack([L[:n], R[:n]])
    return print_necro(src)
