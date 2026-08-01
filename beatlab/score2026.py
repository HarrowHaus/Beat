"""beatlab.score2026 — "PREACHER'S CRUSH" : the 2026 Ye beat.

Concept from catalog research: Preacher Man's church + King's menace.
Bully-era DNA (chipmunk-soul chop, gospel organ, SP-1200 grit, sub-2:30 form)
crushed through Yeezus/industrial processing, resolving into a celestial
"Mission Control" outro with a Picardy lift and tape slow-down.

84 BPM half-time, ~57% MPC swing. C minor: Cm9 - Fm9 - Bb13sus - G7#9.

Arrangement (46 bars ~ 2:11):
  0-3    intro     un-quantized raw chop + vinyl + radiophonic drone, no drums
  4-11   verse A   swung boom-bap drums + 808 + bass; organ sneaks in bar 8
  12-19  hook      chop up an octave, choir, tambourine, full 808
  20-27  verse B   "crush": loop printed through fuzz, snare -> metal clank,
                   dark -12st chop answers, organ out
  28-31  bridge    a cappella chop + sub only (edit-culture mute)
  32-39  hook 2    full + wailing vox lead + interstellar 5ths synth
  40-45  outro     drums out; Cm -> Abmaj7 -> Eb lift; tape slow-down
"""
import numpy as np
import pretty_midi

from .engine import (
    SR, Sequencer, synth_808, synth_hat, synth_clap, synth_snare,
    synth_supersaw, synth_darkpad, butter, env_exp, soft_clip,
)
from .samples import load
from .soul import (
    synth_vox, synth_organ, synth_choir, vinyl_bed, crush, tape_saturate,
)

BPM = 84
SWING = 0.14  # odd-16th delay, in sixteenths (~57% MPC swing)

# roots (808): C1 F1 Bb1 G1
ROOTS = [24, 29, 34, 31]
# organ voicings, top line Eb->F->G->(G/#9)
CHORDS = [
    [48, 55, 58, 63],   # Cm9 (rootless colors on organ, C in the 808)
    [53, 60, 63, 65],   # Fm9
    [56, 60, 63, 67],   # Abmaj7/Bb -> Bb13sus
    [55, 59, 65, 70],   # G7#9
]
TURNAROUND = ([56, 60, 63, 67], [55, 59, 65, 70])  # bar 8s: Abmaj7 | G7#9
OUTRO_CHORDS = [[48, 55, 58, 63], [44, 56, 60, 63], [51, 55, 58, 63]]  # Cm Abmaj7 Eb

# 2-bar pseudo-soul chop phrase: (step, midi, dur_16ths, vowel, reversed)
PHRASE_A = [(0, 72, 2, "oh", 0), (2, 75, 2, "ah", 0), (4, 77, 3, "eh", 0),
            (7, 79, 1, "oh", 0), (8, 75, 2, "ah", 0), (10, 72, 5, "oo", 0)]
PHRASE_B = [(0, 79, 2, "ah", 0), (2, 77, 2, "oh", 0), (4, 75, 2, "ah", 0),
            (6, 72, 2, "oo", 0), (8, 67, 6, "ah", 0), (14, 75, 2, "eh", 1)]

WAIL = [(0, 79, 6), (8, 77, 4), (12, 75, 4)], [(0, 77, 10), (12, 72, 4)]

midi_notes = {"808": [], "chop": [], "organ": []}


def synth_tamb(seed=95):
    n = int(0.13 * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    sos_x = butter(butter(x, 4200, 'high', order=6), 9500, 'low')
    flutter = 1 + 0.5 * np.sin(2 * np.pi * 55 * np.arange(n) / SR)
    return sos_x * env_exp(n, 0.045) * flutter * 0.7


def synth_clank(seed=97):
    """Metallic industrial hit — the Yeezus snare replacement."""
    n = int(0.28 * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    ring = np.sin(2 * np.pi * 917 * t) + 0.7 * np.sin(2 * np.pi * 1531 * t) \
        + 0.5 * np.sin(2 * np.pi * 2489 * t)
    x = x * 0.4 + x * ring * 0.9
    x = butter(butter(x, 700, 'high'), 6000, 'low')
    return soft_clip(crush(x * env_exp(n, 0.07), bits=7, downsample=4, mix=0.7), 3.0)


def synth_tom(midi, seed=99):
    n = int(0.3 * SR)
    f = 440 * 2 ** ((midi - 69) / 12)
    fr = f * 2 ** (-np.linspace(0, 0.6, n))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR)
    x += 0.2 * np.random.default_rng(seed).standard_normal(n) * env_exp(n, 0.01)
    return soft_clip(x * env_exp(n, 0.11), 2.0) * 0.9


def slowdown(x, end_rate=0.62):
    """Tape-stop-ish: playback rate eases from 1.0 to end_rate (pitch falls)."""
    rate = np.linspace(1.0, end_rate, len(x))
    idx = np.cumsum(rate)
    idx = idx[idx < len(x) - 1]
    return x[idx.astype(int)]


def build():
    seq = Sequencer(BPM)
    kick = load("kicks/hard-kick-03.wav")
    kick_sp = crush(kick, bits=12, downsample=3, mix=0.6)          # SP-1200 print
    stomp = tape_saturate(crush(kick, bits=6, downsample=5, mix=0.85), drive=3.5)
    clap_sp = crush(load("claps/clap-01.wav"), bits=12, downsample=3, mix=0.6)

    t_808 = seq.track("808", gain_db=-2.0)
    t_kick = seq.track("kick", gain_db=-4.5)
    t_hats = seq.track("hats", gain_db=-15, pan=0.1)
    t_tamb = seq.track("hats_tamb", gain_db=-14, pan=-0.25)
    t_clap = seq.track("clap", gain_db=-6.5)
    t_clank = seq.track("clap_clank", gain_db=-7)
    t_toms = seq.track("kick_toms", gain_db=-9)
    t_chop = seq.track("chop", gain_db=-7.5)
    t_organ = seq.track("organ", gain_db=-12.5)
    t_choir = seq.track("pad_choir", gain_db=-10.5)
    t_lead = seq.track("lead_wail", gain_db=-11)
    t_syn = seq.track("lead_stars", gain_db=-15, pan=0.3)
    t_fx = seq.track("fx", gain_db=-14)

    sx = seq.sixteenth
    duck = []
    rng = np.random.default_rng(2026)

    def sw(step):
        return step + SWING if (isinstance(step, int) and step % 2 == 1) else step

    def at(bar, step=0.0, loose=0.0):
        t = seq.at(bar, sw(step))
        return t + rng.uniform(-loose, loose) if loose else t

    # ---------- element writers ----------
    def bass_bar(bar, sub_only=False):
        root = ROOTS[bar % 4]
        hits = [(0, 6), (7, 3), (11, 5)] if bar % 2 == 0 else [(0, 7), (10, 6)]
        for step, dur in hits:
            t0 = at(bar, step)
            x = synth_808(root, dur * sx, drive=2.8 if not sub_only else 1.3,
                          punch=0.0 if sub_only else 1.0)
            t_808.add(t0, x * (0.45 if sub_only else 1.0))
            midi_notes["808"].append((root, t0, t0 + dur * sx))

    def drums_bar(bar, mode="boom", hats=True, tamb=False):
        ks = [0, 7, 14] if bar % 2 == 0 else [0, 3, 7, 14]
        for step in ks:
            t0 = at(bar, step)
            if mode == "boom":
                t_kick.add(t0, kick_sp * (1.0 if step == 0 else 0.85))
            else:  # crush mode: industrial stomp doubles the kick
                t_kick.add(t0, kick_sp * 0.7)
                t_kick.add(t0, stomp * 0.9)
            duck.append(t0)
        t0 = at(bar, 8)
        if mode == "boom":
            t_clap.add(t0, clap_sp)
            t_clap.add(t0, synth_snare() * 0.45)
        else:
            t_clank.add(t0, synth_clank(seed=97 + bar))
        if bar % 2 == 1:  # rimshot ghost on 2.5
            t_clap.add(at(bar, 6), synth_snare() * 0.16)
        if hats:
            for step in (2, 6, 10, 14):
                t_hats.add(at(bar, step), synth_hat(dur=0.05) * 0.75)
            t_hats.add(at(bar, 7), synth_hat(dur=0.035) * 0.5)  # push before snare
        if tamb:
            t_tamb.add(at(bar, 8), synth_tamb(seed=95 + bar))

    def toms_bar(bar):
        for step, m in ((4, 43), (12, 36), (13, 43)):
            t_toms.add(at(bar, step), synth_tom(m, seed=99 + bar + step))

    def chop_2bars(bar, transpose=0, formant=1.45, gain=1.0, loose=0.0,
                   vowel_override=None):
        for b, phrase in ((bar, PHRASE_A), (bar + 1, PHRASE_B)):
            for step, midi, dur, vowel, rev in phrase:
                m = midi + transpose
                x = synth_vox(m, dur * sx * 1.1, vowel=vowel_override or vowel,
                              formant_shift=formant, seed=61 + b * 7 + step)
                x = tape_saturate(crush(x, bits=12, downsample=4, mix=0.55), 1.8)
                if rev:
                    x = x[::-1].copy()
                edge = int(0.004 * SR)
                x[:edge] *= np.linspace(0, 1, edge)
                x[-edge:] *= np.linspace(1, 0, edge)
                t0 = at(b, step, loose=loose)
                t_chop.add(t0, x * gain)
                midi_notes["chop"].append((m, t0, t0 + dur * sx))

    def organ_bar(bar, gain=1.0):
        if bar % 8 == 7:  # turnaround: Abmaj7 | G7#9, half bar each
            for i, ch in enumerate(TURNAROUND):
                t0 = at(bar, i * 8)
                t_organ.add(t0, synth_organ(ch, 8 * sx * 1.05) * gain)
                for m in ch:
                    midi_notes["organ"].append((m, t0, t0 + 8 * sx))
        else:
            ch = CHORDS[bar % 4]
            t0 = at(bar, 0)
            t_organ.add(t0, synth_organ(ch, seq.bar * 1.02) * gain)
            for m in ch:
                midi_notes["organ"].append((m, t0, t0 + seq.bar))

    def choir_bars(bar, n_bars=2, chord=(60, 63, 67), vowel="oo", gain=1.0):
        t_choir.add(at(bar), synth_choir(list(chord), n_bars * seq.bar,
                                         vowel=vowel, seed=81 + bar) * gain)

    def wail_2bars(bar):
        for b, phrase in ((bar, WAIL[0]), (bar + 1, WAIL[1])):
            for step, midi, dur in phrase:
                x = synth_vox(midi, dur * sx * 1.15, vowel="ah", formant_shift=1.2,
                              vib_depth=0.6, vib_hz=6.0, seed=105 + b + step)
                t_lead.add(at(b, step), tape_saturate(x, 2.0))

    def stars_2bars(bar):
        for b, (m1, m2) in ((bar, (79, 86)), (bar + 1, (77, 84))):
            for m in (m1, m2):  # open 5ths/octaves, high + wide
                t_syn.add(at(b, 0), synth_supersaw(m, 2 * seq.beat, detune=0.18,
                                                   voices=5, bright=6500) * 0.5)

    # ---------------- arrangement ----------------
    total_bars = 46
    t_fx.add(0.0, vinyl_bed(total_bars * seq.bar + 2, seed=91) * 0.9)

    # intro 0-3: raw loose chop + drone, no drums
    t_fx.add(0.0, butter(synth_darkpad([36, 43, 44], 4 * seq.bar), 800, 'low') * 0.5)
    chop_2bars(0, transpose=0, gain=0.8, loose=0.028)
    chop_2bars(2, transpose=0, gain=0.9, loose=0.028)

    # verse A 4-11
    for b in range(4, 12):
        bass_bar(b)
        drums_bar(b, mode="boom", hats=(b % 8 != 7))
        if b % 2 == 0:
            chop_2bars(b, gain=0.9)
        if b >= 8:
            organ_bar(b, gain=0.85)

    # hook 12-19: chipmunk octave up, choir, tambourine
    for b in range(12, 20):
        bass_bar(b)
        drums_bar(b, mode="boom", hats=(b % 8 != 7), tamb=True)
        if b % 2 == 0:
            chop_2bars(b, transpose=12, formant=1.55, gain=0.95)
            choir_bars(b, 2, chord=(60, 63, 67), vowel="oo", gain=0.9)
        organ_bar(b)

    # verse B 20-27: the crush — fuzzed loop, clank, dark chop
    for b in range(20, 28):
        bass_bar(b)
        drums_bar(b, mode="crush", hats=False)
        toms_bar(b) if b % 4 == 2 else None
        if b % 2 == 0:
            chop_2bars(b, transpose=-12, formant=0.8, gain=1.1, vowel_override="oh")

    # bridge 28-31: a cappella chop + sub only
    for b in range(28, 32):
        bass_bar(b, sub_only=True)
        if b % 2 == 0:
            chop_2bars(b, transpose=12, formant=1.55, gain=1.0, loose=0.02)

    # hook 2 32-39: full + wail + interstellar synth
    for b in range(32, 40):
        bass_bar(b)
        drums_bar(b, mode="boom", hats=(b % 8 != 7), tamb=True)
        organ_bar(b)
        if b % 2 == 0:
            chop_2bars(b, transpose=12, formant=1.55, gain=0.95)
            choir_bars(b, 2, chord=(60, 63, 67), vowel="ah", gain=1.0)
            wail_2bars(b)
            stars_2bars(b)

    # outro 40-45: drums out, Cm -> Abmaj7 -> Eb (Picardy lift), tape slow-down
    for i, b in enumerate((40, 42, 44)):
        ch = OUTRO_CHORDS[i]
        org = synth_organ(ch, 2 * seq.bar * 1.02) * 0.9
        cho = synth_choir([m + 12 for m in ch[1:]], 2 * seq.bar, vowel="oo",
                          seed=120 + b) * 0.9
        if b == 44:  # final chord: tape slow-down
            org, cho = slowdown(org), slowdown(cho)
        t_organ.add(at(b), org)
        t_choir.add(at(b), cho)
        for m in ch:
            midi_notes["organ"].append((m, at(b), at(b) + 2 * seq.bar))
    t_808.add(at(40), synth_808(24, 2 * seq.bar, drive=1.4, punch=0.0) * 0.6)

    return seq, duck, total_bars


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("chop", 52), ("organ", 19)):
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
    mix_path, pre_peak = mix_and_master(stems, duck, BPM, "output2026")
    export_midi("output2026/beat.mid")
    print(f"mix: {mix_path} (pre-normalize peak {pre_peak:.3f})")


if __name__ == "__main__":
    main()
