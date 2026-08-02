"""beatlab.score_kvlt — "KVLT" : industrial Yeezus flip of an original
black metal recording.

The premise: Ye finds a black metal record, chops it, and interpolates the
riff — but cleared/changed enough to be legally distinct. Here the 'record'
IS ours (beatlab/blackmetal.py renders an original song in the idiom:
tremolo power-chord riff in E minor/Phrygian, blast beats, shrieks, necro
demo-tape print), so the flip is clean by construction. The source ships
alongside the beat as provenance (sample_source.flac).

The flip, Yeezus-style:
  - chops pitched DOWN 3 semitones: source Em -> beat in C# minor (the
    Yeezus/Vultures key center) — the classic crate pitch-flip
  - MPC re-trigger chops as the hook melody; one reversed chop per cycle
  - a Surge lead INTERPOLATES the riff at quarter-note speed (the
    'replayed, legally distinct' layer)
  - industrial half-time drums: distorted kick, fat snare+stomp on 3,
    scarce hats; rock-tom accents in the final hooks
  - sub-first 808s per the machine-ears calibration (C#1/A0/B0 roots)
  - BLAST BREAK: 4 bars where the raw source's blast beats burst through
    unpitched, then a 2-bar clean choir mute (the sacred interruption)
    before the loudest section

144 BPM half-time (source recorded at 144 -> chops loop on-grid).
82 bars ~ 2:17.

Arrangement:
  0-3    crate open   raw source plays, LP-filtered, stutter fill into
  4-11   hook 1       chops -3st + 808 + industrial drums
  12-27  verse        sparse: 808/drums, chop stabs, synth stabs
  28-35  hook 2
  36-39  BLAST BREAK  raw blast + shriek over droning 808
  40-55  verse 2      interpolation lead enters, builds
  56-61  dbl hook A
  62-63  MUTE         clean real choir, 2 bars, everything out
  64-71  dbl hook B   max: chops + interpolation + tom accents
  72-81  outro        chop -12st decays, reversed source tail, tape stop
"""
import numpy as np
import pretty_midi

from .engine import SR, Sequencer
from .blackmetal import render_source, RIFF_CYCLE
from .industrial import synth_stab, synth_rock_tom, synth_stomp_clap
from .pro import Kit808, DrumKit, ChoirSampler, RiserKit, SurgeSynth, _pitch, conv_reverb, IR
from .score2026 import slowdown

BPM = 144
PITCH = -3  # Em source -> C#m beat

CS1, A0, B0 = 25, 21, 23
BASS_ROOTS = [CS1, CS1, A0, B0]
STAB_CSM = [49, 56, 61]
CHOIR_E = [52, 56, 61, 64]  # C#m/E colour for the interruption (real choir range)

# interpolation of the source riff, quarter-note speed, C# minor
INTERP_1 = [(0, 61, 4), (4, 62, 2), (6, 64, 2), (8, 61, 4), (12, 59, 4)]
INTERP_2 = [(0, 57, 4), (4, 59, 4), (8, 61, 8)]

midi_notes = {"808": [], "interp": [], "riff": []}


def build():
    seq = Sequencer(BPM)
    sx = seq.sixteenth
    bar_s = seq.bar

    print("rendering original black metal source...")
    src = render_source(bpm=BPM, n_bars=16)
    src_bar = int(bar_s * SR)

    def chop(bar_i, n_steps, pitch=PITCH, rev=False):
        """Slice n_steps sixteenths starting at source bar bar_i, repitch."""
        a = bar_i * src_bar
        x = src[:, a: a + int(n_steps * sx * SR)].mean(axis=0)
        if pitch:
            x = _pitch(x, pitch)
        n = int(n_steps * sx * SR)
        x = x[:n]
        if rev:
            x = x[::-1].copy()
        f = max(int(0.005 * SR), 1)
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
        return x

    k808 = Kit808("Distorted")
    k808_sub = Kit808("Sub")
    drums = DrumKit()
    choir = ChoirSampler()
    risers = RiserKit()

    t_808 = seq.track("808", gain_db=-3.5)
    t_kick = seq.track("kick", gain_db=-5)
    t_snr = seq.track("clap", gain_db=-5)
    t_stomp = seq.track("indus_stomp", gain_db=-8)
    t_hats = seq.track("hats", gain_db=-11)
    t_chop = seq.track("metal_chop", gain_db=-7.5)
    t_src = seq.track("metal_src", gain_db=-6.5)
    t_stab = seq.track("acid_stabs", gain_db=-11)
    t_toms = seq.track("indus_toms", gain_db=-7)
    t_choir = seq.track("pro_choir", gain_db=1.5)
    t_fx = seq.track("fx", gain_db=-12)

    total_bars = 82
    duck = []
    at = seq.at
    interp_notes = []

    def bass_bar(bar, drone=False):
        root = BASS_ROOTS[bar % 4]
        hits = [(0, 6), (7, 3), (11, 5)] if bar % 2 == 0 else [(0, 7), (10, 6)]
        if drone:
            hits = [(0, 14)]
        for step, dur in hits:
            t0 = at(bar, step)
            t_808.add(t0, k808.note(root, dur * sx))
            t_808.add(t0, k808_sub.note(root, dur * sx) * 0.9)
            midi_notes["808"].append((root, t0, t0 + dur * sx))

    def drums_bar(bar, hats=True, toms=False):
        ks = [0, 7, 11] if bar % 2 == 0 else [0, 7, 10, 13]
        for step in ks:
            t0 = at(bar, step)
            t_kick.add(t0, drums.one("Kick_Distorted", "hard"))
            duck.append(t0)
        t0 = at(bar, 8)
        t_snr.add(t0, drums.one("Snare_Fat", "hard"))
        t_snr.add(t0, drums.one("Clap_Tight", "mid", 0.6))
        t_stomp.add(t0, synth_stomp_clap(seed=341 + bar))
        if hats:
            for step in (2, 6, 10, 14):
                t_hats.add(at(bar, step), drums.one("Hat_Vintage808", "mid", 0.8))
        if toms:
            for step, m in ((12, 37), (14, 32)):
                t_toms.add(at(bar, step), synth_rock_tom(m, seed=bar + step))

    def chops_2bars(bar):
        """The hook chop pattern: MPC re-triggers of the guitar bars."""
        e = bar % 8  # rotate source material
        t_chop.add(at(bar, 0), chop(e % 4, 8))
        t_chop.add(at(bar, 8), chop((e + 1) % 4, 6))
        t_chop.add(at(bar, 14), chop((e + 1) % 4, 2))          # re-trigger
        t_chop.add(at(bar + 1, 0), chop((e + 2) % 4, 8))
        t_chop.add(at(bar + 1, 8), chop((e + 2) % 4, 4))       # stutter
        t_chop.add(at(bar + 1, 12), chop(e % 4, 4, rev=True))  # reversed tail

    def interp_2bars(bar):
        for b, phrase in ((bar, INTERP_1), (bar + 1, INTERP_2)):
            for step, midi, dur in phrase:
                interp_notes.append((b, step, midi, dur))
                midi_notes["interp"].append((midi, at(b, step), at(b, step) + dur * sx))

    # ---------------- arrangement ----------------
    # crate open 0-3: the 'record' plays raw
    t_src.add(at(0), src[:, : 3 * src_bar] * 0.9)
    for k in range(3):  # stutter fill on bar 3 beat 4
        t_chop.add(at(3, 12 + k), chop(0, 1, pitch=0))
    t_fx.add(at(3, 8), risers.riser(40, dur=0.5 * bar_s) * 0.6)

    # hook 1: 4-11
    t_fx.add(at(4), drums.one("Crash_Dark", "hard", 0.7))
    for b in range(4, 12):
        bass_bar(b)
        drums_bar(b)
        if b % 2 == 0:
            chops_2bars(b)

    # verse 12-27: sparse
    t_fx.add(at(12), risers.downlifter(2) * 0.6)
    for b in range(12, 28):
        bass_bar(b)
        drums_bar(b, hats=(b % 4 != 3))
        if b % 4 == 0:
            t_chop.add(at(b, 8), chop(b % 4, 4))
        if b % 4 == 2:
            t_stab.add(at(b, 0), synth_stab(STAB_CSM, 3 * sx, seed=b))
            t_stab.add(at(b, 7), synth_stab(STAB_CSM, 3 * sx, seed=b + 1))

    # hook 2: 28-35
    t_fx.add(at(28), drums.one("Crash_Bright", "mid", 0.6))
    for b in range(28, 36):
        bass_bar(b)
        drums_bar(b)
        if b % 2 == 0:
            chops_2bars(b)

    # BLAST BREAK 36-39: the raw record tears through
    t_src.add(at(36), src[:, 4 * src_bar: 8 * src_bar])
    for b in range(36, 40):
        bass_bar(b, drone=True)
    t_fx.add(at(39, 8), risers.riser(55, dur=0.5 * bar_s) * 0.7)

    # verse 2: 40-55 — interpolation enters
    for b in range(40, 56):
        bass_bar(b)
        drums_bar(b, hats=(b >= 44))
        if b % 2 == 0:
            interp_2bars(b)
        if b % 8 == 4:
            t_chop.add(at(b, 8), chop((b // 2) % 4, 4))

    # double hook A: 56-61
    t_fx.add(at(56), drums.one("Crash_Dark", "hard", 0.8))
    for b in range(56, 62):
        bass_bar(b)
        drums_bar(b)
        if b % 2 == 0:
            chops_2bars(b)
            interp_2bars(b)

    # MUTE 62-63: the sacred interruption — clean real choir, nothing else
    L = choir.chord(CHOIR_E, 2 * bar_s, "male")
    Rr = choir.chord([m + 0.14 for m in CHOIR_E], 2 * bar_s, "male")
    off = int(0.012 * SR)
    Rr = np.concatenate([np.zeros(off), Rr])[:len(L)]
    t_choir.add(at(62), np.stack([L, Rr]) * 1.2)

    # double hook B: 64-71 — maximum density
    t_fx.add(at(64), drums.one("Crash_Dark", "hard", 0.9))
    for b in range(64, 72):
        bass_bar(b)
        drums_bar(b, toms=True)
        if b % 2 == 0:
            chops_2bars(b)
            interp_2bars(b)

    # outro 72-81: decay
    for b in range(72, 76):
        bass_bar(b)
        drums_bar(b, hats=False)
        if b % 2 == 0:
            t_chop.add(at(b, 0), chop(b % 4, 8, pitch=-12))
    rev_tail = src[:, :2 * src_bar][:, ::-1].mean(axis=0) * 0.6
    t_src.add(at(76), np.stack([rev_tail, rev_tail]))
    final = chop(3, 16, pitch=PITCH)
    t_chop.add(at(78), slowdown(final, end_rate=0.55))
    t_fx.add(at(78), risers.downlifter(3) * 0.7)

    for root, _ in RIFF_CYCLE[0]:
        midi_notes["riff"].append((root, 0.0, 1.0))

    # --- Surge interpolation lead ---------------------------------------
    print("rendering interpolation lead...")
    syn = SurgeSynth("Broken One")
    notes = [(at(b, s), m, d * sx) for b, s, m, d in interp_notes]
    lead = syn.render(notes, total_bars * bar_s)

    stems, dur = seq.render_stems(total_bars, tail=4.0)
    n = stems["808"].shape[1]
    pad = np.zeros((2, n))
    m = min(n, lead.shape[1])
    pad[:, :m] = lead[:, :m] * 10 ** (-11.5 / 20)
    stems["pro_interp"] = pad

    stems["pro_choir"] = conv_reverb(stems["pro_choir"], IR["church"], mix=0.35).astype(np.float64)
    stems["clap"] = conv_reverb(stems["clap"], IR["plate_dark"], mix=0.08).astype(np.float64)

    return stems, duck, dur, src


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("interp", 30), ("riff", 30)):
        inst = pretty_midi.Instrument(program=prog, name=name)
        for midi, t0, t1 in midi_notes[name]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=midi, start=t0, end=t1))
        pm.instruments.append(inst)
    pm.write(path)


def main():
    import soundfile as sf
    from .mix import mix_and_master
    stems, duck, dur, src = build()
    print(f"{len(stems)} stems, {dur:.1f}s")
    mix_path, pre_peak = mix_and_master(stems, duck, BPM, "output_kvlt")
    sf.write("output_kvlt/sample_source.flac", src.T, SR, subtype="PCM_24")
    export_midi("output_kvlt/beat.mid")
    import pyloudnorm
    x, sr = sf.read(mix_path)
    print(f"mix: {mix_path}  {pyloudnorm.Meter(sr).integrated_loudness(x):.1f} LUFS")


if __name__ == "__main__":
    main()
