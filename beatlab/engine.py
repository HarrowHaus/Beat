"""beatlab.engine — headless synthesis + sequencing engine for trap/rage production.

Everything renders to float64 numpy buffers at SR, then stems are mixed and
mastered with pedalboard. No DAW, no audio device needed.
"""
import numpy as np
from scipy import signal as sps

SR = 44100


# ---------------------------------------------------------------- utilities
def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a=0.005, d=0.05, s=0.6, r=0.05, sr=SR):
    a_n, d_n, r_n = int(a * sr), int(d * sr), int(r * sr)
    s_n = max(n - a_n - d_n - r_n, 0)
    env = np.concatenate([
        np.linspace(0, 1, max(a_n, 1)),
        np.linspace(1, s, max(d_n, 1)),
        np.full(s_n, s),
        np.linspace(s, 0, max(r_n, 1)),
    ])
    return env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


def note_to_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def butter(x, cutoff, kind, order=4):
    ny = SR / 2
    c = np.clip(np.atleast_1d(cutoff) / ny, 1e-5, 0.999)
    sos = sps.butter(order, c if len(c) > 1 else c[0], btype=kind, output='sos')
    return sps.sosfilt(sos, x)


# ---------------------------------------------------------------- drums
def synth_808(midi, dur, glide_to=None, glide_time=0.08, drive=2.5, punch=1.0):
    """Distorted sustained 808: sine core, pitch drop attack, optional glide."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = note_to_hz(midi)
    # attack pitch drop (click/punch), 2 octaves down over ~30ms
    f = np.full(n, f0)
    drop_n = int(0.03 * SR)
    f[:drop_n] = f0 * 2 ** (2 * np.linspace(1, 0, drop_n))
    if glide_to is not None:
        g_n = int(glide_time * SR)
        f1 = note_to_hz(glide_to)
        start = n - g_n
        if start > drop_n:
            f[start:] = np.geomspace(f0, f1, g_n)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase)
    # subtle 2nd harmonic for speaker translation
    body += 0.25 * np.sin(2 * phase)
    amp = env_adsr(n, a=0.002, d=0.08, s=0.85, r=min(0.12, dur * 0.3))
    x = soft_clip(body * amp, drive)
    # punchy click layer
    click = np.random.default_rng(3).standard_normal(int(0.008 * SR)) * env_exp(int(0.008 * SR), 0.002)
    click = butter(click, 2500, 'high')
    x[:len(click)] += punch * 0.35 * click
    return butter(x, 7000, 'low') * 0.9


def synth_kick(dur=0.35):
    n = int(dur * SR)
    f = 150 * 2 ** (-np.linspace(0, 5, n))  # fast pitch sweep 150->~5Hz feel
    f = np.maximum(f, 45)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.06)
    return soft_clip(x, 1.8)


def synth_hat(dur=0.06, tone=9000, seed=7):
    n = int(dur * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    # metallic: sum of square oscillators ring-modding the noise
    t = np.arange(n) / SR
    metal = sum(sps.square(2 * np.pi * f * t) for f in (3011, 4517, 5673, 6863))
    x = x * 0.4 + 0.15 * metal
    x = butter(x, tone, 'high', order=6)
    return x * env_exp(n, 0.012)


def synth_openhat(dur=0.3, seed=8):
    n = int(dur * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    x = butter(x, 7500, 'high', order=6)
    return x * env_exp(n, 0.09)


def synth_clap(seed=11):
    """Layered noise bursts ~ classic 909-style trap clap."""
    n = int(0.35 * SR)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for i, off in enumerate((0, 0.012, 0.024, 0.036)):
        o = int(off * SR)
        burst = rng.standard_normal(n - o) * env_exp(n - o, 0.004 if i < 3 else 0.07)
        x[o:] += burst * (0.7 if i < 3 else 1.0)
    x = butter(butter(x, 900, 'high'), 8500, 'low')
    return soft_clip(x, 1.5) * 0.8


def synth_snare(seed=13):
    n = int(0.25 * SR)
    tone = np.sin(2 * np.pi * 185 * np.arange(n) / SR) * env_exp(n, 0.04)
    noise = np.random.default_rng(seed).standard_normal(n) * env_exp(n, 0.06)
    noise = butter(noise, 1800, 'high')
    return soft_clip(tone * 0.5 + noise * 0.8, 1.6) * 0.85


def synth_perc_blip(midi=84, dur=0.09):
    n = int(dur * SR)
    f = note_to_hz(midi)
    x = np.sin(2 * np.pi * f * np.arange(n) / SR + 4 * np.sin(2 * np.pi * f * 2.01 * np.arange(n) / SR))
    return x * env_exp(n, 0.02) * 0.5


# ---------------------------------------------------------------- synths
def _saw_bank(freqs, n, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        ph = rng.uniform(0, 1)
        out += sps.sawtooth(2 * np.pi * f * t + 2 * np.pi * ph)
    return out / len(freqs)


def synth_supersaw(midi, dur, detune=0.35, voices=7, bright=9000, seed=0):
    """Rage-style bright detuned supersaw."""
    n = int(dur * SR)
    f0 = note_to_hz(midi)
    dets = np.linspace(-detune, detune, voices)
    x = _saw_bank([f0 * 2 ** (d / 12) for d in dets], n, seed)
    x += 0.5 * _saw_bank([2 * f0 * 2 ** (d / 12) for d in dets], n, seed + 1)
    x = butter(x, bright, 'low')
    x = butter(x, 180, 'high')
    return x * env_adsr(n, a=0.004, d=0.06, s=0.8, r=0.08)


def synth_darkpad(midis, dur, seed=21):
    """Gothic choir-ish pad: detuned saws through formant-ish bandpass stack."""
    n = int(dur * SR)
    x = np.zeros(n)
    for i, m in enumerate(midis):
        f0 = note_to_hz(m)
        x += _saw_bank([f0 * 2 ** (d / 1200) for d in (-9, -4, 0, 5, 8)], n, seed + i)
    x /= len(midis)
    # vowel "ah/oh" formants
    y = np.zeros(n)
    for fc, g in ((620, 1.0), (900, 0.7), (2400, 0.25)):
        sos = sps.butter(2, [max(fc * 0.75, 40) / (SR / 2), min(fc * 1.3, 20000) / (SR / 2)], 'band', output='sos')
        y += g * sps.sosfilt(sos, x)
    # slow swell + vibrato-ish amplitude motion
    t = np.arange(n) / SR
    lfo = 1 + 0.06 * np.sin(2 * np.pi * 0.9 * t)
    return y * env_adsr(n, a=min(0.4, dur * 0.3), d=0.1, s=0.9, r=min(0.8, dur * 0.3)) * lfo * 0.8


def synth_bell(midi, dur, seed=31):
    """FM bell/music-box pluck — WLR-style eerie topline material."""
    n = int(dur * SR)
    f = note_to_hz(midi)
    t = np.arange(n) / SR
    idx = 3.0 * env_exp(n, 0.15)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.53 * t))
    return x * env_exp(n, min(0.5, dur)) * 0.7


def synth_chant(midi=57, dur=0.22, voices=6, seed=51):
    """Staccato crowd-chant stab ('hey!'): detuned saw voices through open-vowel
    formants, slight downward pitch scoop, breath-noise onset."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    f0 = note_to_hz(midi)
    x = np.zeros(n)
    for v in range(voices):
        det = rng.uniform(-40, 40)  # cents — a crowd, not a synth
        f = f0 * 2 ** (det / 1200) * 2 ** (-1.5 * t / dur / 12)  # scoop down
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6.28)
        x += sps.sawtooth(ph)
    x /= voices
    y = np.zeros(n)
    for fc, g in ((700, 1.0), (1200, 0.8), (2600, 0.35)):  # open "eh/ey" vowel
        sos = sps.butter(2, [fc * 0.7 / (SR / 2), min(fc * 1.35, 20000) / (SR / 2)], 'band', output='sos')
        y += g * sps.sosfilt(sos, x)
    breath = rng.standard_normal(int(0.02 * SR)) * env_exp(int(0.02 * SR), 0.006)
    y[:len(breath)] += 0.3 * butter(breath, 2000, 'high')
    return soft_clip(y * env_adsr(n, a=0.008, d=0.1, s=0.5, r=0.06), 2.0) * 0.8


def synth_riser(dur=1.8, seed=41):
    n = int(dur * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    cut = np.geomspace(300, 12000, n)
    # time-varying one-pole highpass approximation via fft-free trick: chunked filtering
    out = np.zeros(n)
    chunk = 2048
    for i in range(0, n, chunk):
        c = cut[min(i + chunk // 2, n - 1)]
        out[i:i + chunk] = butter(x[i:i + chunk], c, 'high', order=2)
    return out * np.linspace(0, 1, n) ** 2 * 0.6


# ---------------------------------------------------------------- sequencer
class Track:
    def __init__(self, name, gain_db=0.0, pan=0.0):
        self.name, self.gain_db, self.pan = name, gain_db, pan
        self.events = []  # (time_sec, mono_buffer)

    def add(self, time_sec, buf):
        self.events.append((time_sec, buf))

    def render(self, total_dur):
        n = int(total_dur * SR)
        L, R = np.zeros(n), np.zeros(n)
        g = 10 ** (self.gain_db / 20)
        pl = np.cos((self.pan + 1) * np.pi / 4)
        pr = np.sin((self.pan + 1) * np.pi / 4)
        for t0, buf in self.events:
            i = int(t0 * SR)
            if i < 0:
                buf = buf[-i:]
                i = 0
            j = min(i + len(buf), n)
            if i >= n or len(buf) == 0:
                continue
            seg = buf[: j - i]
            L[i:j] += seg * g * pl
            R[i:j] += seg * g * pr
        return np.stack([L, R])


class Sequencer:
    def __init__(self, bpm, beats_per_bar=4):
        self.bpm = bpm
        self.beat = 60.0 / bpm
        self.bar = self.beat * beats_per_bar
        self.sixteenth = self.beat / 4
        self.tracks = {}

    def track(self, name, **kw):
        if name not in self.tracks:
            self.tracks[name] = Track(name, **kw)
        return self.tracks[name]

    def at(self, bar, sixteenth=0.0):
        return bar * self.bar + sixteenth * self.sixteenth

    def render_stems(self, total_bars, tail=2.0):
        dur = total_bars * self.bar + tail
        return {name: tr.render(dur) for name, tr in self.tracks.items()}, dur
