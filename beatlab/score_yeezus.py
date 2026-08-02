"""beatlab.score_yeezus — "CARNIVAL SKINHEAD" : Yeezus x Vultures fusion.

Research-derived spec: 145 BPM (New Slaves 141 / FUK SUMN 142 / VULTURES 146 /
CARNIVAL 148 intersection), C# minor with Phrygian b2 (D natural) in the
industrial stabs. Rubin rule enforced: max ~5 elements at once, keep asking
what can come OUT.

The grammar:
  - On Sight: broken screaming acid line, cold open, no drums
  - New Slaves: two-chord punk-length stabs replace drums in verse B
  - Black Skinhead: quarter-note tom gallop + breathing/screams as percussion
  - Blood on the Leaves: TNGHT brass cannon detonation after the interruption
  - THE INTERRUPTION: mid-song hard mute -> clean wide gospel choir (E major
    glow) a cappella -> smash-cut into the loudest section of the record
  - CARNIVAL: stadium crowd chant rides the hook as the melody
  - Send It Up: dancehall outro — dembow perc + pitched vocal, then one
    unresolved choir chord

Arrangement (91 bars ~ 2:30 @ 145):
  0-7    cold open   acid riff solo, broken/clipping, filter creeping open
  8-23   verse A     half-time 808 grid + stabs; hats join bar 16
  24-31  pre         tom gallop enters + pant loop, riff opens full
  32-47  hook 1      gallop + chant + siren; scream chops as fills
  48-55  verse B     New Slaves mode: stabs + sparse 808, drums OUT
  56-59  INTERRUPTION clean gospel choir a cappella, wide/wet
  60-75  drop        brass + gallop + half-time 808 + chant (max density)
  76-83  Ty pocket   808 + chant + open space for stacked falsettos
  84-90  outro       dembow + pitched dancehall vox; unresolved choir chord
"""
import numpy as np
import pretty_midi

from .engine import (
    SR, Sequencer, synth_808, synth_hat, synth_snare, synth_chant,
    butter, soft_clip, env_exp,
)
from .samples import load
from .soul import synth_vox, synth_choir, crush, tape_saturate
from .industrial import (
    synth_303, synth_rock_tom, synth_stab, synth_brass, synth_scream,
    synth_stomp_clap, synth_pant,
)

BPM = 145

CS1, B0, A0 = 25, 23, 21           # 808 roots: C#1, B0, A0
BASS_ROOTS = [CS1, CS1, A0, B0]
STAB_CSM = [49, 56, 61]            # C#m
STAB_D = [50, 57, 62]              # D major — the Phrygian bII
CHOIR_E = [52, 56, 59, 64]         # E major glow (relative major)
CHOIR_END = [50, 57, 62, 66]       # D major — unresolved final chord

# 2-bar acid riff: (step, midi, dur_16ths, accent, slide_from)
RIFF_A = [(0, 49, 1, 1, None), (2, 49, 1, 0, None), (4, 52, 1, 0, None),
          (6, 50, 1, 1, None), (8, 49, 1, 0, None), (10, 56, 2, 1, 49),
          (13, 52, 1, 0, None), (14, 50, 2, 0, 52)]
RIFF_B = [(0, 49, 1, 1, None), (2, 61, 1, 1, 49), (4, 56, 1, 0, None),
          (6, 50, 1, 0, None), (8, 49, 2, 1, None), (11, 47, 1, 0, None),
          (12, 49, 4, 1, 47)]

# hook chant melody (Carnival "oh-oh-oh-oh"), quarter notes: C# E C# B
CHANT_MEL = [61, 64, 61, 59]

midi_notes = {"808": [], "riff": [], "stabs": [], "brass": []}


def synth_siren(dur, seed=401):
    n = int(dur * SR)
    t = np.arange(n) / SR
    lfo = 2 * np.abs((t * 1.2) % 1 - 0.5)  # triangle
    f = 620 + 640 * lfo
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return soft_clip(x, 2.0) * env_exp(n, dur * 0.6) * 0.5


def build():
    seq = Sequencer(BPM)
    sx = seq.sixteenth
    kick = load("kicks/hard-kick-03.wav")
    kick_dry = crush(kick, bits=8, downsample=2, mix=0.5)

    t_808 = seq.track("808", gain_db=-2.5)
    t_kick = seq.track("kick", gain_db=-5.5)
    t_toms = seq.track("indus_toms", gain_db=-4.5)
    t_snr = seq.track("clap", gain_db=-8)
    t_stomp = seq.track("indus_stomp", gain_db=-6.5)
    t_hats = seq.track("hats", gain_db=-16, pan=0.08)
    t_riff = seq.track("acid_riff", gain_db=-8.5)
    t_stab = seq.track("acid_stabs", gain_db=-9.5)
    t_brass = seq.track("brass", gain_db=-5.5)
    t_chant = seq.track("chant", gain_db=-8.5)
    t_choir = seq.track("pad_choir", gain_db=0.0)
    t_pant = seq.track("hats_pant", gain_db=-12, pan=-0.2)
    t_vox = seq.track("chop_dh", gain_db=-8.5)
    t_fx = seq.track("fx", gain_db=-13)

    duck = []
    at = seq.at

    def riff_2bars(bar, cutoff=900, gain=1.0):
        for b, phrase in ((bar, RIFF_A), (bar + 1, RIFF_B)):
            for step, midi, dur, acc, slide in phrase:
                x = synth_303(midi, dur * sx * 1.05, accent=bool(acc),
                              slide_from=slide, cutoff=cutoff)
                t0 = at(b, step)
                t_riff.add(t0, x * gain)
                midi_notes["riff"].append((midi, t0, t0 + dur * sx))

    def bass_bar(bar, sparse=False):
        root = BASS_ROOTS[bar % 4]
        nxt = BASS_ROOTS[(bar + 1) % 4]
        hits = [(0, 6, None), (7, 3, None), (12, 4, nxt if nxt != root else None)]
        if sparse:
            hits = [(0, 10, None)]
        for step, dur, glide in hits:
            t0 = at(bar, step)
            x = synth_808(root, dur * sx, glide_to=glide, drive=3.2)
            t_808.add(t0, x)
            midi_notes["808"].append((root, t0, t0 + dur * sx))
            if not sparse:
                t_kick.add(t0, kick_dry * 0.8)
                duck.append(t0)

    def halftime_bar(bar, hats=True):
        bass_bar(bar)
        t_snr.add(at(bar, 8), synth_snare() * 0.9)
        t_snr.add(at(bar, 8), crush(load("claps/clap-01.wav"), bits=8,
                                    downsample=2, mix=0.5) * 0.7)
        if hats:
            for step in (2, 6, 10, 14):
                t_hats.add(at(bar, step), synth_hat(dur=0.05) * 0.7)

    grng = np.random.default_rng(913)

    def gallop_bar(bar, screams=False):
        """Black Skinhead: triplet long-short-short tom gallop (Beautiful
        People cell), live-drummer humanization, pant offbeats."""
        trip = seq.bar / 12
        for pos in range(12):
            accent = pos % 3 == 0
            ghost = pos % 3 == 2
            if not (accent or ghost):
                continue
            t0 = seq.at(bar) + pos * trip + grng.uniform(-0.008, 0.008)
            m = (37 if (pos // 3) % 2 == 0 else 32) + (5 if ghost else 0)
            m += grng.uniform(-0.5, 0.5)  # +-3% pitch drift
            tom = synth_rock_tom(m, seed=301 + bar * 12 + pos)
            t_toms.add(max(t0, 0.0), tom * (1.0 if accent else 0.5))
            if accent:
                t_kick.add(max(t0, 0.0), kick_dry)
                duck.append(max(t0, 0.0))
        for step in (4, 12):  # stomp-clap backbeat
            t_stomp.add(at(bar, step), synth_stomp_clap(seed=341 + bar))
        if bar % 2 == 1:
            for step in (2, 6, 10, 14):
                t_pant.add(at(bar, step), synth_pant(seed=351 + bar + step))
        if screams and bar % 4 == 3:
            t_fx.add(at(bar, 14), synth_scream(0.45, seed=331 + bar))

    def stabs_bar(bar, density=2):
        """New Slaves two-chord punk stabs: C#m | C#m | D | C#m rotation."""
        chord = STAB_D if bar % 4 == 2 else STAB_CSM
        steps = [0, 7] if density == 2 else [0, 5, 7, 12]
        for step in steps:
            t0 = at(bar, step)
            t_stab.add(t0, synth_stab(chord, 3 * sx, seed=311 + bar))
            for m in chord:
                midi_notes["stabs"].append((m, t0, t0 + 3 * sx))

    def chant_bar(bar):
        for beat, midi in enumerate(CHANT_MEL):
            t_chant.add(at(bar, beat * 4),
                        synth_chant(midi, dur=0.3, voices=10, seed=51 + bar + beat))

    def brass_bar(bar):
        """Blood on the Leaves drop grammar: long cannon on 1, answer on 3&."""
        root = [49, 49, 50, 52][bar % 4]
        t0 = at(bar, 0)
        t_brass.add(t0, synth_brass(root, 5 * sx, seed=321 + bar))
        midi_notes["brass"].append((root, t0, t0 + 5 * sx))
        t1 = at(bar, 10)
        t_brass.add(t1, synth_brass(root - 12, 4 * sx, seed=322 + bar) * 0.85)
        midi_notes["brass"].append((root - 12, t1, t1 + 4 * sx))

    # ---------------- arrangement ----------------
    total = 91

    # cold open 0-7: acid riff alone, filter creeping open
    for i, b in enumerate(range(0, 8, 2)):
        riff_2bars(b, cutoff=500 + i * 260, gain=0.85)

    # verse A 8-23: half-time 808 + stabs; hats join 16
    for b in range(8, 24):
        halftime_bar(b, hats=(b >= 16))
        stabs_bar(b, density=2)
        if b % 2 == 0 and b >= 12:
            riff_2bars(b, cutoff=1100, gain=0.5)  # riff tucked low

    # pre 24-31: gallop enters, riff opens full
    for b in range(24, 32):
        gallop_bar(b)
        bass_bar(b, sparse=True)
        if b % 2 == 0:
            riff_2bars(b, cutoff=1600 + (b - 24) * 100, gain=0.9)

    # hook 1 32-47: gallop + chant + siren + screams
    for b in range(32, 48):
        gallop_bar(b, screams=True)
        halftime_bar(b, hats=False)
        chant_bar(b)
        if b % 2 == 0:
            riff_2bars(b, cutoff=2400, gain=1.0)
        if b % 8 == 0:
            t_fx.add(at(b), synth_siren(2 * seq.bar, seed=401 + b))

    # verse B 48-55: New Slaves mode — stabs + sparse 808, drums out
    for b in range(48, 56):
        stabs_bar(b, density=2 if b < 52 else 4)
        if b % 2 == 0:
            bass_bar(b, sparse=True)

    # THE INTERRUPTION 56-59: clean gospel choir, wide and wet, nothing else
    for i, b in enumerate((56, 58)):
        ch = CHOIR_E if i == 0 else [m + (0 if i == 0 else -2) for m in CHOIR_E]
        t_choir.add(at(b), synth_choir([m + 12 for m in ch], 2 * seq.bar * 1.02,
                                       vowel="ah", seed=140 + b) * 2.0)

    # drop 60-75: brass + gallop + half-time 808 + chant — the loudest section
    for b in range(60, 76):
        gallop_bar(b, screams=(b % 8 == 7))
        halftime_bar(b, hats=False)
        brass_bar(b)
        chant_bar(b)

    # Ty pocket 76-83: 808 + chant + space
    for b in range(76, 84):
        bass_bar(b)
        t_snr.add(at(b, 8), synth_snare() * 0.5)
        if b % 2 == 0:
            chant_bar(b)

    # outro 84-90: dancehall drop — dembow + pitched vox, then one chord
    for b in range(84, 90):
        for step, g in ((0, 1.0), (3, 0.7), (8, 1.0), (11, 0.7)):  # dembow
            t_kick.add(at(b, step), kick_dry * g * 0.9)
            if step in (3, 11):
                t_snr.add(at(b, step), synth_snare() * 0.45)
        if b % 2 == 0:  # pitched dancehall vox phrase
            for step, m, d, vw in ((0, 61, 3, "eh"), (4, 59, 2, "oh"),
                                   (7, 56, 4, "ah")):
                x = synth_vox(m, d * sx * 1.2, vowel=vw, formant_shift=0.95,
                              vib_depth=0.5, seed=150 + b + step)
                t_vox.add(at(b, step), tape_saturate(x, 2.2))
    t_choir.add(at(90), synth_choir([m + 12 for m in CHOIR_END], 2.8,
                                    vowel="oo", seed=160) * 1.2)

    return seq, duck, total


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("riff", 87), ("stabs", 62), ("brass", 61)):
        inst = pretty_midi.Instrument(program=prog, name=name)
        for midi, t0, t1 in midi_notes[name]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=midi, start=t0, end=t1))
        pm.instruments.append(inst)
    pm.write(path)


def main():
    from .mix import mix_and_master
    seq, duck, bars = build()
    stems, dur = seq.render_stems(bars, tail=3.5)
    print(f"rendered {len(stems)} stems, {dur:.1f}s")
    mix_path, pre_peak = mix_and_master(stems, duck, BPM, "output_yeezus")
    export_midi("output_yeezus/beat.mid")
    print(f"mix: {mix_path} (pre-normalize peak {pre_peak:.3f})")


if __name__ == "__main__":
    main()
