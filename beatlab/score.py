"""beatlab.score — "HARROW" : rage x Vultures hybrid instrumental.

Spec (from catalog research): 148 BPM half-time, A minor w/ Phrygian b2 color.
Clap/snare on beat 3 only. 808 doubles as kick, glides into bar turns.
Chant stabs on beats 2 & 4 in hooks (CARNIVAL device). Energy via mutes.

Arrangement (80 bars ~ 2:12):
  0-3   intro      filtered lead alone, riser into drop
  4-11  hook 1     full stack; drum mute last half of bar 11
  12-27 verse 1    lead out -> bell counter; 808/hats/clap/low pad
  28-35 hook 2     full; cold stop on beat 3 of bar 35
  36-51 verse 2    as v1; hats out 44-46, return w/ roll 47
  52-55 breakdown  drums out: chant + choir + 808 swells; riser
  56-71 double hook + open hats; octave 808 stabs 68-71
  72-79 outro      peel layers, lead filters down, tail
"""
import numpy as np
import pretty_midi

from .engine import (
    SR, Sequencer, synth_808, synth_hat, synth_openhat, synth_clap,
    synth_snare, synth_supersaw, synth_darkpad, synth_bell, synth_chant,
    synth_riser, butter,
)
from .samples import Tuned808, load

BPM = 148
A1, E1, F1, Bb1, C2, A2 = 33, 28, 29, 34, 36, 45

# 808 bassline, 4-bar cycle: Am | Am(+C) | F | E->Bb phrygian turn, glide home.
# (step, midi, dur_steps, glide_to)
BASS_CYCLE = [
    [(0, A1, 3, None), (3, A1, 3, None), (6, A1, 4, None), (10, A1, 3, None), (13, A1, 3, None)],
    [(0, A1, 3, None), (3, A1, 3, None), (6, C2, 4, None), (10, A1, 3, None), (13, A1, 3, A1)],
    [(0, F1, 3, None), (3, F1, 3, None), (6, F1, 4, None), (10, F1, 3, None), (13, F1, 3, None)],
    [(0, E1, 3, None), (3, E1, 3, None), (6, E1, 4, None), (10, Bb1, 3, None), (13, Bb1, 3, A1)],
]

# Rage lead ostinato, 2-bar cycle, octave 5, Phrygian Bb inside. (step, midi, dur)
LEAD_A = [(0, 81, 2), (2, 84, 2), (4, 83, 2), (6, 82, 2), (8, 81, 4), (12, 76, 4)]
LEAD_B = [(0, 81, 2), (2, 84, 2), (4, 88, 2), (6, 83, 2), (8, 82, 6), (14, 81, 2)]

# Sparse bell counter-line for verses (keeps 1-4k free), 2-bar cycle.
BELL_A = [(0, 69, 6), (10, 72, 4)]
BELL_B = [(0, 69, 4), (6, 70, 4), (12, 76, 4)]

PAD_CHORD = [45, 52, 57, 60]  # low Am voicing, scooped in the mix

HATS_8THS = [0, 2, 4, 6, 8, 10, 12, 14]

midi_notes = {"808": [], "lead": [], "bell": []}


def _rec_midi(part, midi, t0, dur):
    midi_notes[part].append((midi, t0, t0 + dur))


def build():
    seq = Sequencer(BPM)
    s808 = Tuned808("808s/808-bass-dist.wav")
    kick = load("kicks/hard-kick-03.wav")
    crash = load("fx/fx-cymbal.wav")
    sx = seq.sixteenth

    t_808 = seq.track("808", gain_db=-2.5)
    t_kick = seq.track("kick", gain_db=-6)
    t_hats = seq.track("hats", gain_db=-13, pan=0.12)
    t_clap = seq.track("clap", gain_db=-7)
    t_lead = seq.track("lead", gain_db=-10)
    t_bell = seq.track("bell", gain_db=-12, pan=-0.2)
    t_pad = seq.track("pad", gain_db=-14)
    t_chant = seq.track("chant", gain_db=-9)
    t_fx = seq.track("fx", gain_db=-12)

    duck_times = []

    def bass_bar(bar, cut_after=None, stab=False, swell_only=False):
        for step, midi, dur, glide in BASS_CYCLE[bar % 4]:
            if cut_after is not None and step >= cut_after:
                continue
            t0 = seq.at(bar, step)
            d = dur * sx
            if swell_only:
                if step not in (0, 10):
                    continue
                x = synth_808(midi, d * 3, drive=1.5, punch=0.0)
                x *= np.linspace(0.15, 1.0, len(x)) ** 2
                t_808.add(t0, butter(x, 300, 'low') * 0.45)
            else:
                t_808.add(t0, s808.note(midi, d) * 0.85)
                t_808.add(t0, synth_808(midi, d, glide_to=glide) * 0.7)
                t_kick.add(t0, kick * 0.9)
                duck_times.append(t0)
            _rec_midi("808", midi, t0, d)
        if stab:
            t0 = seq.at(bar, 14)
            t_808.add(t0, synth_808(A2, 2 * sx, drive=3.0))
            _rec_midi("808", A2, t0, 2 * sx)

    def hats_bar(bar, roll=False, trips=False, openh=False):
        for step in HATS_8THS:
            t_hats.add(seq.at(bar, step), synth_hat() * 0.8)
        if roll:  # 32nd roll across beat 4
            for k in range(8):
                t_hats.add(seq.at(bar, 12 + k * 0.5), synth_hat(dur=0.04) * (0.5 + 0.06 * k))
        if trips:  # triplet burst w/ upward pitch envelope
            for k in range(6):
                t_hats.add(seq.at(bar, 12 + k * (4 / 6)), synth_hat(tone=9000 + 900 * k) * 0.85)
        if openh:
            t_hats.add(seq.at(bar, 15), synth_openhat() * 0.7)

    def clap_bar(bar, cut_after=None):
        if cut_after is not None and 8 >= cut_after:
            return
        t0 = seq.at(bar, 8)
        t_clap.add(t0, synth_clap())
        t_clap.add(t0, synth_snare() * 0.5)
        t_clap.add(t0, load("claps/clap-01.wav") * 0.8)

    def lead_2bars(bar, bright=9000, gain=1.0):
        for step, midi, dur in LEAD_A:
            t0 = seq.at(bar, step)
            t_lead.add(t0, synth_supersaw(midi, dur * sx * 1.05, bright=bright) * gain)
            _rec_midi("lead", midi, t0, dur * sx)
        for step, midi, dur in LEAD_B:
            t0 = seq.at(bar + 1, step)
            t_lead.add(t0, synth_supersaw(midi, dur * sx * 1.05, bright=bright) * gain)
            _rec_midi("lead", midi, t0, dur * sx)

    def bell_2bars(bar):
        for b, pat in ((bar, BELL_A), (bar + 1, BELL_B)):
            for step, midi, dur in pat:
                t0 = seq.at(b, step)
                t_bell.add(t0, synth_bell(midi, dur * sx * 1.6))
                _rec_midi("bell", midi, t0, dur * sx)

    def pad_4bars(bar, gain=1.0):
        t_pad.add(seq.at(bar), synth_darkpad(PAD_CHORD, 4 * seq.bar) * gain)

    def chant_bar(bar):
        for step in (4, 12):  # beats 2 & 4 — the CARNIVAL device
            t_chant.add(seq.at(bar, step), synth_chant(seed=51 + bar * 7 + step))

    # ---------------- arrangement ----------------
    # intro 0-3: filtered lead alone, riser into the drop
    for b in (0, 2):
        lead_2bars(b, bright=2600, gain=0.8)
    t_fx.add(seq.at(2), synth_riser(dur=2 * seq.bar))

    # hook 1: 4-11
    t_fx.add(seq.at(4), crash * 0.6)
    for b in range(4, 12):
        mute = 8 if b == 11 else None  # drum mute, back half of last bar
        bass_bar(b, cut_after=mute, stab=(b % 4 == 3 and b != 11))
        hats_bar(b, roll=(b % 4 == 1), trips=(b % 4 == 3), openh=(b % 2 == 1))
        clap_bar(b, cut_after=mute)
        chant_bar(b)
        if b % 2 == 0:
            lead_2bars(b)

    # verse 1: 12-27 — lead out, bell in, low pad
    for b in range(12, 28):
        bass_bar(b, stab=(b % 4 == 3))
        hats_bar(b, roll=(b % 4 == 1), trips=(b % 4 == 3))
        clap_bar(b)
        if b % 2 == 0:
            bell_2bars(b)
        if b % 4 == 0:
            pad_4bars(b, gain=0.8)

    # hook 2: 28-35 — cold stop on beat 3 of bar 35
    t_fx.add(seq.at(28), crash * 0.6)
    for b in range(28, 36):
        mute = 8 if b == 35 else None
        bass_bar(b, cut_after=mute, stab=(b % 4 == 3 and b != 35))
        if b != 35:
            hats_bar(b, roll=(b % 4 == 1), trips=(b % 4 == 3), openh=(b % 2 == 1))
        else:
            hats_bar(b)  # straight hats only, dies at the stop
        clap_bar(b, cut_after=mute)
        chant_bar(b)
        if b % 2 == 0:
            lead_2bars(b)

    # verse 2: 36-51 — WLR sparseness: hats out 44-46, return w/ roll 47
    for b in range(36, 52):
        bass_bar(b, stab=(b % 4 == 3))
        if b < 44 or b == 47:
            hats_bar(b, roll=(b % 4 == 1 or b == 47), trips=(b % 4 == 3 and b != 47))
        clap_bar(b)
        if b % 2 == 0:
            bell_2bars(b)
        if b % 4 == 0:
            pad_4bars(b, gain=0.8)

    # breakdown 52-55: Vultures moment — drums out, chant + choir + 808 swells
    for b in range(52, 56):
        chant_bar(b)
        bass_bar(b, swell_only=True)
    pad_4bars(52, gain=1.3)
    t_fx.add(seq.at(55), synth_riser(dur=seq.bar))

    # double hook 56-71: everything + open hats; octave stabs 68-71
    t_fx.add(seq.at(56), crash * 0.7)
    for b in range(56, 72):
        bass_bar(b, stab=(b % 4 == 3 or b >= 68))
        hats_bar(b, roll=(b % 4 == 1), trips=(b % 4 == 3), openh=True)
        clap_bar(b)
        chant_bar(b)
        if b % 2 == 0:
            lead_2bars(b)
        if b % 4 == 0:
            pad_4bars(b, gain=0.7)

    # outro 72-79: peel layers, filter the lead down to close
    for b in range(72, 74):
        bass_bar(b)
        hats_bar(b)
        clap_bar(b)
    for i, b in enumerate((72, 74, 76, 78)):
        lead_2bars(b, bright=6000 - i * 1300, gain=0.85 - i * 0.15)
    pad_4bars(76, gain=0.9)

    return seq, duck_times


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("lead", 81), ("bell", 10)):
        inst = pretty_midi.Instrument(program=prog, name=name)
        for midi, t0, t1 in midi_notes[name]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=midi, start=t0, end=t1))
        pm.instruments.append(inst)
    pm.write(path)


def main():
    from .mix import mix_and_master
    seq, duck_times = build()
    stems, dur = seq.render_stems(80, tail=3.0)
    print(f"rendered {len(stems)} stems, {dur:.1f}s")
    mix_path, pre_peak = mix_and_master(stems, duck_times, BPM, "output")
    export_midi("output/beat.mid")
    print(f"mix: {mix_path} (pre-normalize peak {pre_peak:.3f})")


if __name__ == "__main__":
    main()
