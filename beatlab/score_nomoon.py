"""beatlab.score_nomoon — "NO MOON" : an original composition.

Not modeled on any song from the research corpus — the corpus is vocabulary
here, not a template. What makes it its own piece:

  - Functional harmony, rare in this space: a i-VI-III-VII cycle
    (Gm9 - Ebmaj7 - Bbadd9 - Fadd9) instead of a static vamp, with a real
    harmonic-minor cadence bridge (Cm - D7b9 - Gm).
  - A singable 2-bar motif played by FM bell + synthesized voice in UNISON —
    one composite timbre, neither bell nor voice.
  - Tresillo (3+3+2) rhythmic cell in the 808 and hat accents.
  - Cyclical form: the song ends as it began, motif alone over vinyl.

138 BPM half-time (backbeat ~69), G minor. 80 bars ~ 2:19.

Arrangement:
  0-3    intro    motif alone (bell+vox unison) over vinyl
  4-11   verse 1  groove enters: 808 tresillo, clap on 3, e-piano — motif rests
  12-19  hook 1   motif returns, organ swells, low choir answers phrase ends
  20-35  verse 2  16 bars of vocal space; sparse bell answers only
  36-43  hook 2
  44-51  bridge   Cm - D7b9 - Gm cadence x2; drums thin to hats, choir swell
  52-67  hook x2  fullest: + high shimmer, open hats
  68-79  outro    peel back to motif alone; final Gm(add9) held, tape fade
"""
import numpy as np
import pretty_midi

from .engine import (
    SR, Sequencer, synth_808, synth_hat, synth_openhat, synth_clap,
    synth_snare, synth_supersaw, synth_bell,
)
from .samples import load
from .soul import synth_vox, synth_organ, synth_epiano, synth_choir, vinyl_bed
from .score2026 import slowdown

BPM = 138

G1, Eb1, Bb1, F1, C1, D1 = 31, 27, 34, 29, 24, 26
BASS_CYCLE = [G1, Eb1, Bb1, F1]
BRIDGE_BASS = [C1, D1, G1, G1]

CHORDS = [
    [55, 62, 65, 69],   # Gm9
    [51, 58, 62, 67],   # Ebmaj7
    [58, 62, 65, 72],   # Bbadd9
    [53, 57, 60, 67],   # Fadd9
]
BRIDGE_CHORDS = [
    [48, 55, 60, 63],   # Cm
    [50, 54, 60, 63],   # D7b9
    [55, 62, 65, 69],   # Gm9
    [55, 62, 65, 70],   # Gm add color
]
FINAL_CHORD = [55, 62, 69, 74]  # Gm(add9) open voicing

# the motif: 2 bars, 16th grid, G minor — (step, midi, dur_16ths)
MOTIF_1 = [(0, 79, 2), (2, 82, 2), (4, 81, 2), (6, 79, 2), (8, 74, 4), (12, 77, 4)]
MOTIF_2 = [(0, 79, 2), (2, 86, 2), (4, 84, 2), (6, 82, 2), (8, 81, 6), (14, 79, 2)]
# choir answer at hook phrase-ends (low, 3 notes): D-Eb-D sigh
ANSWER = [(8, [50, 55, 58], 6)]

TRESILLO = [0, 3, 6]  # the 3+3+2 cell start points; +8 begins the second half

midi_notes = {"808": [], "motif": [], "chords": []}


def build():
    seq = Sequencer(BPM)
    sx = seq.sixteenth
    kick = load("kicks/hard-kick-03.wav")

    t_808 = seq.track("808", gain_db=-2.5)
    t_kick = seq.track("kick", gain_db=-7)
    t_hats = seq.track("hats", gain_db=-14, pan=0.1)
    t_clap = seq.track("clap", gain_db=-7.5)
    t_bell = seq.track("bell", gain_db=-9)
    t_vox = seq.track("chop_vox", gain_db=-10.5)
    t_ep = seq.track("organ_ep", gain_db=-13)
    t_org = seq.track("organ", gain_db=-14)
    t_choir = seq.track("pad_choir", gain_db=-10)
    t_shim = seq.track("lead_shimmer", gain_db=-17, pan=-0.3)
    t_fx = seq.track("fx", gain_db=-16)

    duck = []
    at = seq.at

    def motif_2bars(bar, gain=1.0, vox=True):
        """Bell + voice in unison — the composite lead timbre."""
        for b, phrase in ((bar, MOTIF_1), (bar + 1, MOTIF_2)):
            for step, midi, dur in phrase:
                t0 = at(b, step)
                t_bell.add(t0, synth_bell(midi, dur * sx * 1.8) * gain)
                if vox:
                    v = synth_vox(midi, dur * sx * 1.1, vowel="oo",
                                  formant_shift=1.15, vib_depth=0.25,
                                  seed=61 + b * 5 + step)
                    t_vox.add(t0, v * gain * 0.9)
                midi_notes["motif"].append((midi, t0, t0 + dur * sx))

    def bass_bar(bar, roots=None, soft=False):
        root = (roots or BASS_CYCLE)[bar % 4]
        nxt = (roots or BASS_CYCLE)[(bar + 1) % 4]
        # tresillo cell + backbeat-half answer + approach into next bar
        hits = [(0, 3, None), (3, 3, None), (6, 2, None),
                (8, 3, None), (11, 3, None), (14, 2, nxt if nxt != root else None)]
        if soft:
            hits = [(0, 6, None), (8, 6, None)]
        for step, dur, glide in hits:
            t0 = at(bar, step)
            x = synth_808(root, dur * sx, glide_to=glide, drive=2.2,
                          punch=0.6 if not soft else 0.0)
            t_808.add(t0, x * (0.6 if soft else 0.85))
            midi_notes["808"].append((root, t0, t0 + dur * sx))
            if not soft and step in (0, 6, 11):
                t_kick.add(t0, kick * 0.6)
                duck.append(t0)

    def drums_bar(bar, openh=False, thin=False):
        if not thin:
            t0 = at(bar, 8)
            t_clap.add(t0, synth_clap())
            t_clap.add(t0, synth_snare() * 0.4)
        for step in range(0, 16, 2):
            acc = 1.0 if step in (0, 6, 8, 14) else 0.55  # tresillo accents
            t_hats.add(at(bar, step), synth_hat(dur=0.05) * acc * 0.8)
        if openh:
            t_hats.add(at(bar, 14), synth_openhat() * 0.6)

    def chords_bar(bar, inst="ep", chords=None, gain=1.0):
        ch = (chords or CHORDS)[bar % 4]
        t0 = at(bar)
        if inst == "ep":
            for j, m in enumerate(ch):  # gentle roll
                t_ep.add(at(bar, j * 0.5), synth_epiano(m, seq.bar * 1.1) * 0.8 * gain)
        else:
            t_org.add(t0, synth_organ(ch, seq.bar * 1.02) * 0.8 * gain)
        for m in ch:
            midi_notes["chords"].append((m, t0, t0 + seq.bar))

    def answer_bar(bar):
        for step, midis, dur in ANSWER:
            t_choir.add(at(bar, step), synth_choir(midis, dur * sx * 1.6,
                                                   vowel="oh", seed=90 + bar) * 0.9)

    # ---------------- arrangement ----------------
    total = 80
    t_fx.add(0.0, vinyl_bed(total * seq.bar + 3, seed=97) * 0.6)

    # intro 0-3: motif alone, twice
    motif_2bars(0, gain=0.85)
    motif_2bars(2, gain=0.95)

    # verse 1: 4-11 — groove enters, motif rests
    for b in range(4, 12):
        bass_bar(b)
        drums_bar(b)
        chords_bar(b, "ep")

    # hook 1: 12-19 — motif + organ + choir answers
    for b in range(12, 20):
        bass_bar(b)
        drums_bar(b, openh=(b % 2 == 1))
        chords_bar(b, "organ")
        if b % 2 == 0:
            motif_2bars(b)
        else:
            answer_bar(b)

    # verse 2: 20-35 — 16 bars of vocal space, sparse bell answers
    for b in range(20, 36):
        bass_bar(b)
        drums_bar(b)
        chords_bar(b, "ep")
        if b % 4 == 3:  # one bell answer per 4 bars
            t_bell.add(at(b, 10), synth_bell(74, 5 * sx) * 0.6)

    # hook 2: 36-43
    for b in range(36, 44):
        bass_bar(b)
        drums_bar(b, openh=(b % 2 == 1))
        chords_bar(b, "organ")
        if b % 2 == 0:
            motif_2bars(b)
        else:
            answer_bar(b)

    # bridge 44-51: the cadence — drums thin, choir swell, harmony leads
    for i, b in enumerate(range(44, 52)):
        bass_bar(b, roots=BRIDGE_BASS, soft=True)
        drums_bar(b, thin=True)
        chords_bar(b, "organ", chords=BRIDGE_CHORDS, gain=1.1)
        if i in (2, 6):
            ch = BRIDGE_CHORDS[(b - 44) % 4]
            t_choir.add(at(b), synth_choir([m + 12 for m in ch[1:]], 2 * seq.bar,
                                           vowel="ah", seed=110 + b) * 1.0)

    # double hook 52-67: fullest — + shimmer, open hats
    for b in range(52, 68):
        bass_bar(b)
        drums_bar(b, openh=True)
        chords_bar(b, "organ")
        if b % 2 == 0:
            motif_2bars(b)
            t_shim.add(at(b), synth_supersaw(91, 2 * seq.beat, detune=0.12,
                                             voices=5, bright=5000) * 0.35)
        else:
            answer_bar(b)

    # outro 68-79: cyclical — peel back to the opening
    for b in range(68, 72):
        bass_bar(b, soft=True)
        drums_bar(b, thin=True)
        chords_bar(b, "ep", gain=0.8)
    motif_2bars(72, gain=0.9)
    motif_2bars(74, gain=0.75)
    motif_2bars(76, gain=0.55, vox=False)  # voice leaves first, bell lingers
    final = synth_organ(FINAL_CHORD, 3.5) * 0.7
    t_org.add(at(78), slowdown(final, end_rate=0.8))
    t_choir.add(at(78), synth_choir([m + 12 for m in FINAL_CHORD[1:]], 3.2,
                                    vowel="oo", seed=120) * 0.8)

    return seq, duck, total


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("motif", 11), ("chords", 4)):
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
    mix_path, pre_peak = mix_and_master(stems, duck, BPM, "output_nomoon")
    export_midi("output_nomoon/beat.mid")
    print(f"mix: {mix_path} (pre-normalize peak {pre_peak:.3f})")


if __name__ == "__main__":
    main()
