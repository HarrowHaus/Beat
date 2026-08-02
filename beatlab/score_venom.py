"""beatlab.score_venom — "ANTIVENOM" : in the style of VENOM / FIELD TRIP
(¥$ ft. Playboi Carti, Vultures 2).

Identity of the reference: the Portishead "Machine Gun" industrial drum-machine
loop — bit-crushed, bone-dry, metallic — under raw Vultures-era synth drones,
122 BPM half-time in F# minor, harmony static (i with bVI/bVII moves), drums
ARE the melody, then a beat-switch outro into a warmer soul bed (the Kodak
section move). All sounds synthesized/CC0 — the Machine Gun character is
recreated, not sampled.

Arrangement (76 bars ~ 2:30 at 122):
  0-3    intro    industrial loop + drone, no 808
  4-11   hook 1   + 808, full drums, bell motif
  12-27  verse A  (Carti) strip melody: loop + sub only, stutter fills every 4
  28-35  hook 2
  36-47  verse B  (Toliver) drone back + delay bell throws, hats drop mid-way
  48-55  verse C  sparse: half drums, dark drone swells
  56-63  hook 3   fullest: + high stars line
  64-75  outro    BEAT SWITCH: loop out; e-piano Dmaj7-C#m7-F#m9 + choir,
                  soft clean drums, gentle 808 — warm resolve, tape fade
"""
import numpy as np
import pretty_midi

from .engine import (
    SR, Sequencer, synth_808, synth_hat, synth_snare, synth_supersaw,
    synth_bell, butter, env_exp, soft_clip, _saw_bank, env_adsr,
)
from .samples import load
from .soul import synth_epiano, synth_choir, vinyl_bed, crush, tape_saturate

BPM = 122  # half-time feel (~61)

F1s, E1, D1 = 30, 28, 26          # 808 roots: F#1, E1, D1
BASS_ROOTS = [F1s, F1s, D1, E1]   # i | i | bVI | bVII
DRONE_CHORDS = [
    [42, 45, 49, 54],  # F#m
    [42, 45, 49, 54],
    [38, 45, 50, 54],  # D
    [40, 47, 52, 56],  # E
]
# beat-switch outro: Dmaj7 | C#m7 | F#m9 | F#m9
OUTRO_KEYS = [[50, 54, 57, 61], [49, 52, 56, 59], [42, 49, 52, 57], [42, 49, 52, 59]]
BELL_MOTIF = [(0, 85, 3), (10, 83, 3)], [(4, 78, 4)]  # C#6 B5 | F#5 — sparse, eerie

midi_notes = {"808": [], "drone": [], "keys": []}


def synth_mg_kick():
    """Blunt, short, clipped drum-machine kick."""
    n = int(0.16 * SR)
    f = 120 * 2 ** (-np.linspace(0, 3.2, n))
    x = np.sin(2 * np.pi * np.cumsum(np.maximum(f, 48)) / SR) * env_exp(n, 0.04)
    x = crush(soft_clip(x, 4.0), bits=6, downsample=5, mix=0.8)
    return butter(x, 6000, 'low')


def synth_mg_snare(seed=201):
    """Metallic, splattery, painful — the Machine Gun snare character."""
    n = int(0.17 * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    ring = (np.sign(np.sin(2 * np.pi * 331 * t)) * 0.6
            + np.sign(np.sin(2 * np.pi * 473 * t)) * 0.5
            + np.sin(2 * np.pi * 1870 * t) * 0.4)
    x = noise * 0.55 + ring * 0.75 + noise * ring * 0.5
    x = butter(butter(x, 380, 'high'), 5200, 'low')
    x = soft_clip(x * env_exp(n, 0.05), 5.0)
    return crush(x, bits=6, downsample=4, mix=0.85) * 0.95


def synth_drone(midis, dur, seed=211):
    """Dark detuned analog drone, low-passed — the Vultures bed."""
    n = int(dur * SR)
    x = np.zeros(n)
    for i, m in enumerate(midis):
        f0 = 440 * 2 ** ((m - 69) / 12)
        x += _saw_bank([f0 * 2 ** (c / 1200) for c in (-11, -5, 0, 6, 12)], n, seed + i)
    x /= len(midis)
    t = np.arange(n) / SR
    wob = 1 + 0.05 * np.sin(2 * np.pi * 0.35 * t)
    x = butter(x, 1400, 'low', order=4) * wob
    return x * env_adsr(n, a=min(0.6, dur * 0.25), d=0.1, s=0.9, r=min(1.0, dur * 0.3))


def build():
    seq = Sequencer(BPM)
    sx = seq.sixteenth
    mg_kick, mg_snare = synth_mg_kick(), synth_mg_snare()
    trap_kick = load("kicks/hard-kick-03.wav") * 0.5

    t_808 = seq.track("808", gain_db=-2.5)
    t_ik = seq.track("indus_kick", gain_db=-4.0)
    t_is = seq.track("indus_snare", gain_db=-5.0)
    t_kick = seq.track("kick", gain_db=-10)
    t_hats = seq.track("hats", gain_db=-16, pan=0.1)
    t_drone = seq.track("drone", gain_db=-13)
    t_bell = seq.track("bell", gain_db=-13, pan=-0.15)
    t_stars = seq.track("lead_stars", gain_db=-16, pan=0.3)
    t_keys = seq.track("organ_keys", gain_db=-11)
    t_choir = seq.track("pad_choir", gain_db=-12)
    t_clap = seq.track("clap", gain_db=-9)
    t_fx = seq.track("fx", gain_db=-15)

    duck = []
    at = seq.at  # straight grid — no swing on this one

    def loop_bar(bar, stutter=False, sparse=False):
        """The recreated Machine Gun loop: dry, mono, relentless."""
        kicks = [0, 6] if bar % 2 == 0 else [0, 6, 7]
        if sparse:
            kicks = [0]
        for step in kicks:
            t0 = at(bar, step)
            t_ik.add(t0, mg_kick)
            t_kick.add(t0, trap_kick)  # clean layer underneath
            duck.append(t0)
        t_is.add(at(bar, 8), mg_snare)
        if stutter:  # machine-gun 32nd burst across beat 4
            for k in range(8):
                t_is.add(at(bar, 12 + k * 0.5),
                         synth_mg_snare(seed=201 + k) * (0.35 + 0.08 * k))

    def hats_bar(bar, trip=False):
        for step in (0, 2, 4, 6, 8, 10, 12, 14):
            vel = 0.6 if step % 4 else 0.8
            t_hats.add(at(bar, step), synth_hat(dur=0.05) * vel)
        if trip:
            for k in range(3):
                t_hats.add(at(bar, 12 + k * (4 / 3)), synth_hat(dur=0.04) * 0.7)

    def bass_bar(bar, soft=False):
        root = BASS_ROOTS[bar % 4]
        nxt = BASS_ROOTS[(bar + 1) % 4]
        hits = [(0, 6, None), (7, 4, None), (12, 4, nxt if nxt != root else None)]
        if soft:
            hits = [(0, 6, None), (8, 5, None)]
        for step, dur, glide in hits:
            t0 = at(bar, step)
            x = synth_808(root, dur * sx, glide_to=glide,
                          drive=1.6 if soft else 2.6, punch=0.0 if soft else 0.8)
            t_808.add(t0, x * (0.5 if soft else 1.0))
            midi_notes["808"].append((root, t0, t0 + dur * sx))

    def drone_4bars(bar, gain=1.0):
        for i in range(4):
            ch = DRONE_CHORDS[i]
            t0 = at(bar + i)
            t_drone.add(t0, synth_drone(ch, seq.bar * 1.05, seed=211 + bar + i) * gain)
            for m in ch:
                midi_notes["drone"].append((m, t0, t0 + seq.bar))

    def bell_2bars(bar):
        for b, phrase in ((bar, BELL_MOTIF[0]), (bar + 1, BELL_MOTIF[1])):
            for step, midi, dur in phrase:
                t_bell.add(at(b, step), synth_bell(midi, dur * sx * 2.2) * 0.8)

    # ---------------- arrangement ----------------
    total = 76
    t_fx.add(0.0, vinyl_bed(total * seq.bar + 2, seed=93) * 0.7)

    # intro 0-3: loop + drone, no 808
    for b in range(4):
        loop_bar(b, stutter=(b == 3))
    drone_4bars(0, gain=0.8)

    # hook 1: 4-11
    for b in range(4, 12):
        loop_bar(b, stutter=(b % 4 == 3))
        hats_bar(b, trip=(b % 4 == 2))
        bass_bar(b)
        if b % 4 == 0:
            drone_4bars(b)
        if b % 2 == 0:
            bell_2bars(b)

    # verse A 12-27 (Carti): strip melody — loop + sub only
    for b in range(12, 28):
        loop_bar(b, stutter=(b % 4 == 3))
        hats_bar(b, trip=False) if b % 8 < 6 else None
        bass_bar(b)

    # hook 2: 28-35
    for b in range(28, 36):
        loop_bar(b, stutter=(b % 4 == 3))
        hats_bar(b, trip=(b % 4 == 2))
        bass_bar(b)
        if b % 4 == 0:
            drone_4bars(b)
        if b % 2 == 0:
            bell_2bars(b)

    # verse B 36-47 (Toliver): drone back, bell throws, hats drop at 42
    for b in range(36, 48):
        loop_bar(b, stutter=(b % 4 == 3))
        if b < 42:
            hats_bar(b)
        bass_bar(b)
        if b % 4 == 0:
            drone_4bars(b, gain=0.85)
        if b % 4 == 0:
            bell_2bars(b)

    # verse C 48-55: sparse — half drums, drone swells
    for b in range(48, 56):
        loop_bar(b, sparse=(b % 2 == 1))
        bass_bar(b, soft=(b % 4 >= 2))
        if b % 4 == 0:
            drone_4bars(b, gain=1.1)

    # hook 3: 56-63 — fullest
    for b in range(56, 64):
        loop_bar(b, stutter=(b % 4 == 3))
        hats_bar(b, trip=(b % 4 == 2))
        bass_bar(b)
        if b % 4 == 0:
            drone_4bars(b)
        if b % 2 == 0:
            bell_2bars(b)
            for m in (78, 85):  # high F#5/C#6 stars
                t_stars.add(at(b), synth_supersaw(m, 2 * seq.beat, detune=0.15,
                                                  voices=5, bright=5500) * 0.4)

    # outro 64-75: BEAT SWITCH — warm bed, industrial loop gone
    for i, b in enumerate(range(64, 76)):
        ch = OUTRO_KEYS[i % 4]
        t0 = at(b)
        for j, m in enumerate(ch):
            t_keys.add(at(b, j), synth_epiano(m, seq.bar * 1.1) * 0.8)  # soft roll
            midi_notes["keys"].append((m, at(b, j), at(b, j) + seq.bar))
        if i % 4 == 0:
            t_choir.add(t0, synth_choir([m + 12 for m in ch[1:]], 4 * seq.bar,
                                        vowel="oo", seed=130 + b) * 0.8)
        if i < 10:  # soft clean drums, gone for final 2 bars
            t_kick.add(at(b, 0), trap_kick * 1.2)
            t_kick.add(at(b, 6), trap_kick * 0.9)
            t_clap.add(at(b, 8), synth_snare() * 0.4)
            bass_bar(b, soft=True)
    # tape-fade final two bars
    fade = synth_drone(DRONE_CHORDS[0], 2 * seq.bar, seed=250) * 0.5
    t_drone.add(at(74), fade * np.linspace(1, 0, len(fade)) ** 0.7)

    return seq, duck, total


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("drone", 89), ("keys", 4)):
        inst = pretty_midi.Instrument(program=prog, name=name)
        for midi, t0, t1 in midi_notes[name]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=midi, start=t0, end=t1))
        pm.instruments.append(inst)
    pm.write(path)


def main():
    from .mix import mix_and_master
    seq, duck, bars = build()
    stems, dur = seq.render_stems(bars, tail=4.0)
    print(f"rendered {len(stems)} stems, {dur:.1f}s")
    mix_path, pre_peak = mix_and_master(stems, duck, BPM, "output_venom")
    export_midi("output_venom/beat.mid")
    print(f"mix: {mix_path} (pre-normalize peak {pre_peak:.3f})")


if __name__ == "__main__":
    main()
