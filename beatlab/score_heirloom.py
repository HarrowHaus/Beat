"""beatlab.score_heirloom — "HEIRLOOM" : first fully release-grade production.

Original composition (no reference-song grammar) on the v2 pro pipeline:
  - Surge XT factory patches rendered headless (surgepy): Deep End bass,
    Belle pluck motif, Choir Pad Thing, DX EP keys, Minor 7 stabs
  - Professionally produced tuned 808s (Long in verses, Distorted in the
    final hooks), velocity-layered kicks/claps/hats
  - REAL recorded choir (Sonatina Chorus) through a real church impulse
    response; plate IR on claps and pluck
  - Produced risers/downlifters/crashes for transitions

146 BPM half-time, Bb minor. i - i - VI - v7: Bbm | Bbm | Gbmaj7 | Fm7.
84 bars ~ 2:18.

Arrangement:
  0-3    intro    pluck motif + male choir swell (church), crash into
  4-11   hook 1   full: 808 Long, drums, motif, choir chords
  12-27  verse 1  stripped: 808 + drums + low pad; keys sneak in at 20
  28-35  hook 2
  36-51  verse 2  8 sparse, then keys + denser hats
  52-59  bridge   drums out: DX EP keys + female choir answers + sub swells
  60-75  dbl hook Distorted 808s, stab accents, full choir + motif
  76-83  outro    peel; final Bbm choir chord rings in the church
"""
import numpy as np
import pretty_midi

from .engine import SR, Sequencer
from .pro import (
    Kit808, DrumKit, ChoirSampler, RiserKit, SurgeSynth, conv_reverb, IR,
)

BPM = 146

BB1, GB1, F1 = 34, 30, 29
BASS_ROOTS = [BB1, BB1, GB1, F1]
CHOIR_CHORDS = [
    [46, 53, 58, 61],   # Bbm
    [46, 53, 58, 61],
    [42, 53, 58, 61],   # Gbmaj7
    [41, 53, 56, 60],   # Fm7
]
KEYS_CHORDS = [
    [58, 65, 70, 73],   # Bbm, up an octave for the EP
    [58, 65, 70, 73],
    [54, 65, 70, 73],   # Gbmaj7
    [53, 65, 68, 72],   # Fm7
]
STAB_CHORD = [58, 61, 65]  # Bbm triad for Minor 7 stab accents

# the motif: 2 bars, 16th grid — (step, midi, dur_16ths)
MOTIF_1 = [(0, 70, 2), (2, 73, 2), (4, 72, 2), (6, 68, 2), (8, 65, 4), (12, 68, 4)]
MOTIF_2 = [(0, 73, 2), (2, 77, 3), (5, 75, 3), (8, 72, 4), (12, 70, 4)]
# female choir answer phrase for the bridge (single notes)
FEM_ANSWER = [(8, 77, 6), (14, 75, 8)]

midi_notes = {"808": [], "motif": [], "keys": [], "choir": []}


def build():
    seq = Sequencer(BPM)
    sx = seq.sixteenth
    bar_s = seq.bar

    k808_long = Kit808("Long")
    k808_sub = Kit808("Sub")
    k808_dist = Kit808("Distorted")
    drums = DrumKit()
    choir = ChoirSampler()
    risers = RiserKit()

    # --- Surge parts rendered as full-length stereo stems ----------------
    total_bars = 84
    total_s = total_bars * bar_s

    def sched(notes_bars):
        """[(bar, step, midi, dur_steps)] -> [(t, midi, dur_s)]"""
        return [(seq.at(b, s), m, d * sx) for b, s, m, d in notes_bars]

    pluck_notes, bass_notes, pad_notes, keys_notes, stab_notes = [], [], [], [], []

    t_808 = seq.track("808", gain_db=-3.5)
    t_kick = seq.track("kick", gain_db=-5)
    t_hats = seq.track("hats", gain_db=-6.5)
    t_clap = seq.track("clap", gain_db=-4)
    t_perc = seq.track("hats_perc", gain_db=-15, pan=-0.3)
    t_choir = seq.track("pro_choir", gain_db=-8)
    t_fx = seq.track("fx", gain_db=-11)

    duck = []
    at = seq.at

    def bass_bar(bar, kit, gain=1.0):
        root = BASS_ROOTS[bar % 4]
        hits = [(0, 6), (7, 3), (11, 5)] if bar % 2 == 0 else [(0, 7), (10, 3), (13, 3)]
        for step, dur in hits:
            t0 = at(bar, step)
            t_808.add(t0, kit.note(root - 12, dur * sx) * gain)
            t_808.add(t0, k808_sub.note(root - 12, dur * sx) * 0.9 * gain)
            t_808.add(t0, kit.note(root, dur * sx) * 0.35 * gain)
            midi_notes["808"].append((root, t0, t0 + dur * sx))
            bass_notes.append((bar, step, root + 24, min(dur, 3)))  # synth doubles up 2 octaves

    def drums_bar(bar, dense=False, kicks=True):
        if kicks:
            ks = [0, 7, 11] if bar % 2 == 0 else [0, 7, 10, 13]
            for step in ks:
                t0 = at(bar, step)
                t_kick.add(t0, drums.one("Kick_Punchy", "hard"))
                t_kick.add(t0, drums.one("Kick_Deep", "mid", 0.6))
                duck.append(t0)
        t0 = at(bar, 8)
        t_clap.add(t0, drums.one("Clap_Trap", "hard"))
        t_clap.add(t0, drums.one("Snare_Trap", "mid", 0.55))
        t_hats.add(t0, drums.one("Tambourine", "mid", 0.8))
        # hats: velocity-layered 8ths, 16th ghosts when dense
        for step in range(0, 16, 2):
            vel = "hard" if step % 4 == 0 else "mid"
            t_hats.add(at(bar, step), drums.one("Hat_Trap", vel, 0.9))
            if step % 8 == 0:
                t_hats.add(at(bar, step), drums.one("Hat_Closed", "hard", 0.55))
        if dense:
            for step in (3, 7, 11, 15):
                t_hats.add(at(bar, step), drums.one("Hat_Trap", "soft", 0.7))
            if bar % 4 == 3:
                t_hats.add(at(bar, 12), drums.one("Hat_Roll16th", "hard", 0.8))
        if bar % 2 == 1:
            t_hats.add(at(bar, 14), drums.one("Hat_Open", "mid", 0.7))
        if bar % 4 == 2:
            t_perc.add(at(bar, 6), drums.one("Claves", "mid", 0.6))

    def motif_2bars(bar):
        for b, phrase in ((bar, MOTIF_1), (bar + 1, MOTIF_2)):
            for step, midi, dur in phrase:
                pluck_notes.append((b, step, midi, dur))
                midi_notes["motif"].append((midi, at(b, step), at(b, step) + dur * sx))

    def choir_bar(bar, gain=1.0):
        ch = CHOIR_CHORDS[bar % 4]
        L = choir.chord(ch, bar_s * 1.05, "male")
        R = choir.chord([m + 0.14 for m in ch], bar_s * 1.05, "male")
        off = int(0.011 * SR)  # decorrelated section: detune + time scatter
        R = np.concatenate([np.zeros(off), R])[:len(L)]
        t_choir.add(at(bar), np.stack([L, R]) * gain)
        for m in ch:
            midi_notes["choir"].append((m, at(bar), at(bar) + bar_s))

    def keys_bar(bar, gain=1.0):
        ch = KEYS_CHORDS[bar % 4]
        for j, m in enumerate(ch):
            keys_notes.append((bar, j * 0.5, m, 14))
        for m in ch:
            midi_notes["keys"].append((m, at(bar), at(bar) + bar_s))

    # ---------------- arrangement ----------------
    # intro 0-3
    motif_2bars(0)
    motif_2bars(2)
    choir_bar(2, 0.7)
    choir_bar(3, 0.8)
    t_fx.add(at(3, 8), risers.riser(12, dur=0.5 * bar_s) * 0.7)

    # hook 1: 4-11
    t_fx.add(at(4), drums.one("Crash_Dark", "hard", 0.7))
    for b in range(4, 12):
        bass_bar(b, k808_long)
        drums_bar(b)
        choir_bar(b)
        if b % 2 == 0:
            motif_2bars(b)

    # verse 1: 12-27
    t_fx.add(at(12), risers.downlifter(1) * 0.6)
    for b in range(12, 28):
        bass_bar(b, k808_long)
        drums_bar(b)
        pad_notes.append((b, 0, KEYS_CHORDS[b % 4][0] - 12, 15))
        if b >= 20:
            keys_bar(b, 0.7)

    # hook 2: 28-35
    t_fx.add(at(28), drums.one("Crash_Bright", "mid", 0.6))
    for b in range(28, 36):
        bass_bar(b, k808_long)
        drums_bar(b)
        choir_bar(b)
        if b % 2 == 0:
            motif_2bars(b)

    # verse 2: 36-51 — sparse 8, then building 8
    for b in range(36, 52):
        bass_bar(b, k808_long)
        drums_bar(b, dense=(b >= 44), kicks=(b not in (43,)))
        if b >= 44:
            keys_bar(b, 0.8)

    # bridge 52-59: drums out
    for b in range(52, 60):
        keys_bar(b)
        if b % 2 == 0:
            choir_bar(b, 0.8)
        else:
            for step, midi, dur in FEM_ANSWER:
                x = choir._one(midi, "female")
                n = min(int(dur * sx * SR), len(x))
                x = x[:n].copy()
                f = max(int(0.08 * SR), 1)
                x[:f] *= np.linspace(0, 1, f)
                x[-f:] *= np.linspace(1, 0, f)
                t_choir.add(at(b, step), np.stack([x, x]) * 0.8)
        if b % 2 == 0:
            bass_bar(b, k808_long, gain=0.45)
    t_fx.add(at(58), risers.riser(30, dur=2 * bar_s) * 0.8)

    # double hook 60-75: Distorted 808s, stabs
    t_fx.add(at(60), drums.one("Crash_Dark", "hard", 0.8))
    for b in range(60, 76):
        bass_bar(b, k808_dist, gain=1.2)
        drums_bar(b, dense=True)
        choir_bar(b)
        if b % 2 == 0:
            motif_2bars(b)
        if b % 4 == 0:
            stab_notes.append((b, 8, STAB_CHORD[0], 2))

    # outro 76-83: peel
    for b in range(76, 80):
        bass_bar(b, k808_long, gain=0.8)
        drums_bar(b, kicks=(b < 78))
    motif_2bars(80)
    choir_bar(80, 0.9)
    choir_bar(81, 0.8)
    x = choir.chord(CHOIR_CHORDS[0], 4.5, "male", attack=0.3, release=2.0)
    t_choir.add(at(82), np.stack([x, x]))

    # --- render Surge stems ----------------------------------------------
    print("rendering Surge parts...")
    surge_stems = {}
    parts = [
        ("pro_bass", "Deep End", bass_notes, -14),
        ("pro_pluck", "Belle", pluck_notes, -10),
        ("pro_pad", "Choir Pad Thing", pad_notes, -19),
        ("pro_keys", "DX EP", keys_notes, -14),
        ("pro_stab", "Minor 7", stab_notes, -13),
    ]
    for name, patch, notes, gain_db in parts:
        if not notes:
            continue
        syn = SurgeSynth(patch)
        audio = syn.render(sched(notes), total_s)
        surge_stems[name] = audio * 10 ** (gain_db / 20)
        print(f"  {name} ({patch}): peak {np.abs(audio).max():.3f}")

    # --- print real spaces (convolution) ---------------------------------
    stems, dur = seq.render_stems(total_bars, tail=4.5)
    n = stems["808"].shape[1]
    for name, audio in surge_stems.items():
        pad = np.zeros((2, n), dtype=np.float64)
        m = min(n, audio.shape[1])
        pad[:, :m] = audio[:, :m]
        stems[name] = pad

    stems["pro_choir"] = conv_reverb(stems["pro_choir"], IR["church"], mix=0.35).astype(np.float64)
    stems["pro_pluck"] = conv_reverb(stems["pro_pluck"], IR["plate_med"], mix=0.18).astype(np.float64)
    stems["clap"] = conv_reverb(stems["clap"], IR["plate_dark"], mix=0.10).astype(np.float64)
    stems["pro_keys"] = conv_reverb(stems["pro_keys"], IR["room"], mix=0.12).astype(np.float64)

    return stems, duck, dur


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("motif", 8), ("keys", 4), ("choir", 52)):
        inst = pretty_midi.Instrument(program=prog, name=name)
        for midi, t0, t1 in midi_notes[name]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=midi, start=t0, end=t1))
        pm.instruments.append(inst)
    pm.write(path)


def main():
    from .mix import mix_and_master
    stems, duck, dur = build()
    print(f"{len(stems)} stems, {dur:.1f}s")
    mix_path, pre_peak = mix_and_master(stems, duck, BPM, "output_heirloom")
    export_midi("output_heirloom/beat.mid")
    # verify loudness
    import pyloudnorm, soundfile as sf_
    x, sr = sf_.read(mix_path)
    lufs = pyloudnorm.Meter(sr).integrated_loudness(x)
    print(f"mix: {mix_path}  integrated {lufs:.1f} LUFS, pre-peak {pre_peak:.3f}")


if __name__ == "__main__":
    main()
