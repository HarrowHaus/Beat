"""beatlab.mix — stem processing and vocal-ready mastering with pedalboard."""
import numpy as np
import soundfile as sf
from pedalboard import (
    Pedalboard, Compressor, Distortion, HighpassFilter, LowpassFilter,
    PeakFilter, Reverb, Delay, Limiter, Gain, Chorus, HighShelfFilter,
    LowShelfFilter,
)

from .engine import SR


def _proc(board, stereo):
    return board(stereo.astype(np.float32), SR)


CHAINS = {
    "808": Pedalboard([
        HighpassFilter(28),
        Distortion(drive_db=6),
        Compressor(threshold_db=-12, ratio=4, attack_ms=8, release_ms=90),
        LowpassFilter(6500),
        Gain(-1.0),
    ]),
    "kick": Pedalboard([
        HighpassFilter(35),
        Compressor(threshold_db=-10, ratio=4, attack_ms=3, release_ms=60),
    ]),
    "hats": Pedalboard([
        HighpassFilter(600),
        PeakFilter(cutoff_frequency_hz=4500, gain_db=2.5, q=0.8),
        HighShelfFilter(cutoff_frequency_hz=9000, gain_db=4.0),
        Compressor(threshold_db=-18, ratio=2.5),
    ]),
    "clap": Pedalboard([
        HighpassFilter(250),
        Reverb(room_size=0.35, wet_level=0.12, dry_level=0.88),
        Compressor(threshold_db=-14, ratio=3),
    ]),
    "lead": Pedalboard([
        HighpassFilter(220),
        Chorus(rate_hz=0.6, depth=0.15, mix=0.25),
        # carve vocal pocket in the loud lead
        PeakFilter(cutoff_frequency_hz=3000, gain_db=-3.5, q=0.9),
        Delay(delay_seconds=0.24, feedback=0.25, mix=0.14),
        Reverb(room_size=0.5, wet_level=0.15, dry_level=0.85),
        Compressor(threshold_db=-16, ratio=3),
    ]),
    "pad": Pedalboard([
        HighpassFilter(160),
        PeakFilter(cutoff_frequency_hz=2800, gain_db=-4.0, q=0.8),
        Reverb(room_size=0.8, wet_level=0.35, dry_level=0.65),
    ]),
    "bell": Pedalboard([
        HighpassFilter(300),
        Delay(delay_seconds=0.32, feedback=0.35, mix=0.22),
        Reverb(room_size=0.7, wet_level=0.28, dry_level=0.72),
    ]),
    "fx": Pedalboard([
        HighpassFilter(200),
        Reverb(room_size=0.7, wet_level=0.3, dry_level=0.7),
    ]),
    "pro": Pedalboard([            # release-grade sources: gentle glue only,
        HighpassFilter(90),        # space is pre-printed via convolution IRs
        PeakFilter(cutoff_frequency_hz=2800, gain_db=-2.5, q=0.9),
        Chorus(rate_hz=0.35, depth=0.12, mix=0.16),  # subtle width/motion
        Compressor(threshold_db=-18, ratio=2.2, attack_ms=12, release_ms=140),
    ]),
    "acid": Pedalboard([           # On Sight riff/stabs: distorted, DRY, center
        HighpassFilter(110),
        Distortion(drive_db=12),
        PeakFilter(cutoff_frequency_hz=2800, gain_db=-3.0, q=0.9),  # vocal pocket
        Compressor(threshold_db=-12, ratio=4, attack_ms=4, release_ms=80),
        LowpassFilter(9500),
    ]),
    "brass": Pedalboard([          # TNGHT cannon: big, saturated, dry
        HighpassFilter(140),
        Distortion(drive_db=8),
        PeakFilter(cutoff_frequency_hz=3000, gain_db=-2.5, q=1.0),
        Compressor(threshold_db=-12, ratio=3.5, attack_ms=6, release_ms=100),
    ]),
    "indus": Pedalboard([          # Machine Gun-style loop: crushed, DRY, mid-forward
        HighpassFilter(70),
        Distortion(drive_db=10),
        PeakFilter(cutoff_frequency_hz=1200, gain_db=3.0, q=0.7),
        Compressor(threshold_db=-10, ratio=6, attack_ms=2, release_ms=50),
        LowpassFilter(9000),
    ]),
    "drone": Pedalboard([
        HighpassFilter(90),
        PeakFilter(cutoff_frequency_hz=2600, gain_db=-4.0, q=0.8),  # vocal pocket
        LowpassFilter(5500),
        Chorus(rate_hz=0.3, depth=0.2, mix=0.3),
        Compressor(threshold_db=-18, ratio=2),
    ]),
    "chop": Pedalboard([
        HighpassFilter(60),
        PeakFilter(cutoff_frequency_hz=400, gain_db=2.0, q=0.8),   # sample warmth
        PeakFilter(cutoff_frequency_hz=2200, gain_db=-2.5, q=0.9),  # vocal pocket
        HighShelfFilter(cutoff_frequency_hz=8000, gain_db=1.5),     # chipmunk sheen
        Compressor(threshold_db=-16, ratio=3, attack_ms=10, release_ms=120),
        Reverb(room_size=0.4, wet_level=0.1, dry_level=0.9),
    ]),
    "organ": Pedalboard([
        HighpassFilter(100),
        PeakFilter(cutoff_frequency_hz=3000, gain_db=-3.0, q=0.9),
        Reverb(room_size=0.55, wet_level=0.18, dry_level=0.82),
        Compressor(threshold_db=-16, ratio=2.5),
    ]),
    "chant": Pedalboard([
        HighpassFilter(280),
        Distortion(drive_db=9),
        PeakFilter(cutoff_frequency_hz=3000, gain_db=-4.0, q=0.9),  # vocal pocket
        Chorus(rate_hz=0.4, depth=0.3, mix=0.4),  # widen the crowd
        Reverb(room_size=0.6, wet_level=0.22, dry_level=0.78),
        Compressor(threshold_db=-15, ratio=3),
    ]),
}

MASTER = Pedalboard([
    HighpassFilter(24),
    LowShelfFilter(cutoff_frequency_hz=90, gain_db=1.5),      # weight
    PeakFilter(cutoff_frequency_hz=300, gain_db=-1.5, q=0.8),  # mud control
    PeakFilter(cutoff_frequency_hz=3200, gain_db=-0.5, q=1.0), # vocal pocket
    HighShelfFilter(cutoff_frequency_hz=11000, gain_db=1.0),   # air
    Compressor(threshold_db=-16, ratio=1.4, attack_ms=35, release_ms=220),  # glue
    Limiter(threshold_db=-4.05, release_ms=80),                # vocal headroom
])


def sidechain_duck(stereo, trigger_times, bpm, depth=0.45, release_beats=0.7):
    """Duck a buffer at 808/kick hits — the trap 'pump'."""
    n = stereo.shape[1]
    env = np.ones(n)
    rel = int(release_beats * (60 / bpm) * SR)
    curve = 1 - depth * (1 - np.linspace(0, 1, rel) ** 1.5)
    for t in trigger_times:
        i = int(t * SR)
        j = min(i + rel, n)
        env[i:j] = np.minimum(env[i:j], curve[: j - i])
    return stereo * env


def mono_below(stereo, hz=150):
    """Mono-fold the sub region for club/phone playback safety."""
    lo_l = _proc(Pedalboard([LowpassFilter(hz)]), stereo)
    hi = stereo - lo_l
    mono = lo_l.mean(axis=0, keepdims=True)
    return hi + np.repeat(mono, 2, axis=0)


def mix_and_master(stems, duck_times, bpm, out_dir, stem_gains=None):
    """Process stems, sum, master. Writes stems + final mix. Returns mix path."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    stem_gains = stem_gains or {}
    processed = {}
    for name, buf in stems.items():
        chain = CHAINS.get(name.split("_")[0], Pedalboard([HighpassFilter(30)]))
        x = _proc(chain, buf)
        x *= 10 ** (stem_gains.get(name, 0.0) / 20)
        processed[name] = x

    n = max(x.shape[1] for x in processed.values())
    bus = np.zeros((2, n), dtype=np.float32)
    for name, x in processed.items():
        pad = np.zeros((2, n), dtype=np.float32)
        pad[:, : x.shape[1]] = x
        processed[name] = pad
        if name.split("_")[0] not in ("808", "kick"):
            pad = sidechain_duck(pad, duck_times, bpm, depth=0.25)
        bus += pad

    # F1lthy method: one shared soft-clipper across the whole instrumental bus
    bus = np.tanh(bus * 1.05) / np.tanh(1.05)
    bus = mono_below(bus, 150)
    master = _proc(MASTER, bus)
    peak = np.abs(master).max()
    if peak > 10 ** (-4 / 20):  # enforce -4 dBFS true peak headroom for vocals
        master *= 10 ** (-4 / 20) / peak

    for name, x in processed.items():
        sf.write(os.path.join(out_dir, f"stem_{name}.wav"), x.T, SR, subtype="PCM_24")
    mix_path = os.path.join(out_dir, "beat_mix.wav")
    sf.write(mix_path, master.T, SR, subtype="PCM_24")
    return mix_path, peak
