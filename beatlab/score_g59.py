"""beatlab.score_g59 — "BURNT CATHEDRAL" : $uicideboy$ meets Vultures.

The fusion: $B are the heirs of Memphis occult rap — eerie pitched-down
crate loops, cowbell phonk, murky blown-out 808s, claustrophobic mixes —
while Vultures is gothic STADIUM minimalism: chant hooks, real choirs,
sustained 808 drones, negative space. Research confirmed the method is
authentically theirs: $crim demonstrably builds hits from royalty-free
'vinyl crate' construction kits, so we fabricate the crate ourselves.

The crate: an original 1971-style private-press gospel-soul record played
on REAL instruments (VSCO upright piano, tremolo violin, cello; Sonatina
male choir), recorded at 169 BPM in E minor, printed dusty (wow/flutter,
crackle, dark LP), then pitched DOWN 3 semitones — the Memphis tape trick —
landing at exactly 142 BPM in C# minor. Progression i-bVI-bVII-v becomes
C#m-A-B-G#m: the Vultures anthem motion, hidden inside the crate.

Structure (the $B two-part beat switch, ~2:49, 100 bars @142 half-time):
  PART A — murky closet (0:00-1:35)
    0-3    intro     murk loop alone + crackle + pitched-down vox snippet
    4-27   verse A1  phonk grid: cowbell ostinato, 16th hats w/ pitched
                     rolls, rim+clap on 3, Memphis 808 bounce, bone dry
    28-35  hook      evil music-box nursery melody (bell+vox unison, dist)
    36-55  verse A2  + shaker and rim ghosts (the 90s-NY nod)
  SWITCH (1:35-1:42)
    56-59  drums die, loop filters down, tape-stop, dead-phone-line beeps
  PART B — burnt cathedral (1:42-2:32)
    60-89  the crate REVEALED: full choir+strings loop at brightness thru
           a real church IR, sustained 808 drones (C#-A-B), stomp-claps on
           2&4, crowd chant hook; bar 72 = one bar of dead silence
  90-99  outro       choir tail + crackle + 808, abrupt end (no fade)
"""
import numpy as np
import pretty_midi

from .engine import SR, Sequencer, synth_chant, synth_808, butter
from .industrial import synth_stomp_clap
from .engine import synth_bell
from .soul import synth_vox
from .crate import VSCOSampler, print_dusty, VSCO
from .pro import Kit808, DrumKit, ChoirSampler, RiserKit, SurgeSynth, _pitch, _load_mono, conv_reverb, IR, PRO_DIR
from .score2026 import slowdown

BPM = 142
SRC_BPM = BPM * 2 ** (3 / 12)  # 168.9 — so the -3st tape-pitch lands at 142
PITCH = -3

CS1, A0, B0 = 25, 21, 23
# Part A Memphis 808 roots (C#, C#, A, B in the sub octave)
BASS_A = [CS1, CS1, A0, B0]
# source chords in E minor (played at 169, heard at 142 in C#m after pitch)
SRC_CHORDS = [
    [52, 55, 59, 64],   # Em
    [48, 55, 60, 64],   # C
    [50, 57, 62, 66],   # D
    [47, 54, 59, 62],   # Bm
]
SRC_MELODY = [  # tremolo violin, one phrase per 4 bars: (bar, beat, midi, beats)
    (0, 0, 76, 3), (0, 3, 79, 1), (1, 0, 77, 2), (1, 2, 76, 2),
    (2, 0, 74, 3), (2, 3, 71, 1), (3, 0, 71, 4),
]
# evil music-box nursery hook (C# minor, after everything is in beat key)
NURSERY = [(0, 73, 2), (2, 76, 2), (4, 73, 2), (6, 71, 2), (8, 69, 2), (10, 71, 2), (12, 73, 4)]

midi_notes = {"808": [], "nursery": [], "crate": []}


def render_crate():
    """The original 1971 record: real instruments, dusty print, 12 bars @169."""
    up = VSCOSampler(f"{VSCO}/Keys/Upright Nr1/*.wav", prefer=("pp", "mf"))
    vln = VSCOSampler(f"{VSCO}/Strings/Solo Violin/Trem/*.wav", prefer=("v1", "v2"))
    cel_glob = f"{VSCO}/Strings/Solo Cello/*/*.wav"
    try:
        cello = VSCOSampler(cel_glob, prefer=("v1", "mf"))
    except FileNotFoundError:
        cello = None
    choir = ChoirSampler()

    bar_s = 4 * 60 / SRC_BPM
    n = int(12 * bar_s * SR) + 2 * SR
    L, R = np.zeros(n), np.zeros(n)

    def put(t, x, gL=1.0, gR=1.0):
        i = int(t * SR)
        j = min(i + len(x), n)
        L[i:j] += x[: j - i] * gL
        R[i:j] += x[: j - i] * gR

    for b in range(12):
        ch = SRC_CHORDS[b % 4]
        for j, m in enumerate(ch):  # felted rolled piano
            put(b * bar_s + j * 0.06, up.note(m, bar_s * 1.1, rr=b + j) * 0.8,
                1.0, 0.85)
        root = ch[0] - 12
        if cello:
            put(b * bar_s, cello.note(root, bar_s * 1.05, rr=b) * 0.5, 0.8, 1.0)
        else:
            t = np.arange(int(bar_s * SR)) / SR
            x = np.sin(2 * np.pi * 440 * 2 ** ((root - 69) / 12) * t) * 0.25
            put(b * bar_s, butter(x, 400, 'low'))
        for m in ch:
            midi_notes["crate"].append((m, b * bar_s, (b + 1) * bar_s))
    for bar, beat, m, dur in SRC_MELODY + [(b0 + 4, bt, m, d) for b0, bt, m, d in SRC_MELODY] \
            + [(b0 + 8, bt, m, d) for b0, bt, m, d in SRC_MELODY]:
        put(bar * bar_s + beat * bar_s / 4, vln.note(m, dur * bar_s / 4 * 1.1, rr=bar) * 0.45,
            0.85, 1.0)
    for b in range(8, 12):  # the resolution: male choir enters — Part B's reveal
        ch = SRC_CHORDS[b % 4]
        put(b * bar_s, choir.chord(ch[:3], bar_s * 1.05, "male") * 0.9)
        put(b * bar_s + 0.013, choir.chord([m + 0.12 for m in ch[:3]], bar_s * 1.05, "male") * 0.7,
            0.0, 1.4)
    src = print_dusty(np.stack([L, R]))
    # the Memphis tape trick: whole record pitched down 3 semitones
    return np.stack([_pitch(src[0], PITCH), _pitch(src[1], PITCH)])


def build():
    seq = Sequencer(BPM)
    sx = seq.sixteenth
    bar_s = seq.bar

    print("recording the 1971 crate source (real instruments)...")
    crate = render_crate()
    cbar = int(bar_s * SR)  # after pitching, source bars == beat bars

    def loop_slice(bar_i, n_bars, lp=None, gain=1.0):
        x = crate[:, bar_i * cbar: (bar_i + n_bars) * cbar].copy()
        if lp:
            x = np.stack([butter(c, lp, 'low') for c in x])
        f = int(0.006 * SR)
        x[:, :f] *= np.linspace(0, 1, f)
        x[:, -f:] *= np.linspace(1, 0, f)
        return x * gain

    k808 = Kit808("Distorted")
    k808_sub = Kit808("Sub")
    drums = DrumKit()
    cowbell = _load_mono(f"{PRO_DIR}/drum-machines/TR-808/cowbell.ogg") \
        if __import__('glob').glob(f"{PRO_DIR}/drum-machines/TR-808/cowbell.*") \
        else _load_mono(f"{PRO_DIR}/drum-machines/Roland-CR-8000/cowbell.ogg")

    t_808 = seq.track("808", gain_db=-3.5)
    t_kick = seq.track("kick", gain_db=-5.5)
    t_clap = seq.track("clap", gain_db=-5.5)
    t_stomp = seq.track("indus_stomp", gain_db=-7.5)
    t_hats = seq.track("hats", gain_db=-8.5)
    t_cow = seq.track("hats_cow", gain_db=-10, pan=0.15)
    t_perc = seq.track("hats_perc", gain_db=-14, pan=-0.25)
    t_loopA = seq.track("dusty_loop", gain_db=-6)
    t_loopB = seq.track("pro_reveal", gain_db=-5.5)
    t_bell = seq.track("bell", gain_db=-9)
    t_vox = seq.track("chop_vox", gain_db=-11)
    t_chant = seq.track("chant", gain_db=-8)
    t_fx = seq.track("fx", gain_db=-13)

    duck = []
    at = seq.at

    def bass_A(bar):
        """Loose Memphis bounce, occasional phrygian slide."""
        root = BASS_A[bar % 4]
        pats = [[(0, 4), (6, 2), (10, 4)], [(0, 3), (7, 3), (12, 4)],
                [(0, 6), (8, 2), (11, 5)], [(0, 4), (6, 2), (10, 3), (14, 2)]]
        for step, dur in pats[bar % 4]:
            t0 = at(bar, step)
            t_808.add(t0, k808.note(root, dur * sx))
            t_808.add(t0, k808_sub.note(root, dur * sx) * 0.85)
            midi_notes["808"].append((root, t0, t0 + dur * sx))
        if bar % 8 == 6:  # b2 slide colour (D natural) — synth glide layer
            t0 = at(bar, 14)
            t_808.add(t0, synth_808(26, 2 * sx, glide_to=25, drive=2.2) * 0.5)

    def drums_A(bar, extra=False):
        for step in ([0, 7, 11] if bar % 2 == 0 else [0, 3, 7, 10]):
            t0 = at(bar, step)
            t_kick.add(t0, drums.one("Kick_Trap", "hard"))
            duck.append(t0)
        t0 = at(bar, 8)
        t_clap.add(t0, drums.one("Snare_Rimshot", "hard"))
        t_clap.add(t0, drums.one("Clap_Tight", "mid", 0.7))
        # $B murk is sparser than the phonk stereotype (mined: 5.4 onsets/s):
        # straight 8ths, 16th ghosts only leading into each 4th bar
        for step in range(0, 16, 2):
            vel = "hard" if step % 4 == 0 else "mid"
            t_hats.add(at(bar, step), drums.one("Hat_Trap", vel, 0.85))
        if bar % 4 == 2:
            for step in (9, 11, 13, 15):
                t_hats.add(at(bar, step), drums.one("Hat_Trap", "soft", 0.6))
        if bar % 4 == 3:  # pitch-bent roll into the next bar
            for k in range(6):
                x = _pitch(drums.one("Hat_Trap", "mid"), k * 0.8)
                t_hats.add(at(bar, 13 + k * 0.5), x * 0.7)
        for step, g in ((0, 1.0), (6, 0.85), (8, 0.7), (12, 0.85)):  # cowbell ostinato
            t_cow.add(at(bar, step), _pitch(cowbell, 1) * g)
        if extra:
            for step in (2, 6, 10, 14):
                t_perc.add(at(bar, step), drums.one("Shaker", "mid", 0.7))
            if bar % 2 == 1:
                t_perc.add(at(bar, 6), drums.one("Snare_Rimshot", "soft", 0.4))

    def nursery_2bars(bar, dist=True):
        for step, m, dur in NURSERY:
            t0 = at(bar, step)
            b = synth_bell(m, dur * sx * 1.8)
            v = synth_vox(m, dur * sx * 1.1, vowel="oo", formant_shift=1.3,
                          vib_depth=0.15, seed=61 + bar + step)
            x = b * 0.8
            x[:len(v)] += v * 0.6
            if dist:
                x = np.tanh(x * 2.4) / np.tanh(2.4)
            t_bell.add(t0, x)
            midi_notes["nursery"].append((m, t0, t0 + dur * sx))

    def bass_B(bar):
        root = [CS1, CS1, A0, B0][bar % 4]
        t0 = at(bar, 0)
        t_808.add(t0, k808.note(root, 15 * sx))          # sustained drone
        t_808.add(t0, k808_sub.note(root, 15 * sx) * 0.9)
        midi_notes["808"].append((root, t0, t0 + 15 * sx))
        duck.append(t0)

    def drums_B(bar):
        for step in (4, 12):  # stadium stomp-claps on 2 & 4
            t0 = at(bar, step)
            t_stomp.add(t0, synth_stomp_clap(seed=400 + bar * 16 + step))
            t_stomp.add(t0, drums.one("Clap_Trap", "hard", 0.8))
        for step in (2, 10):  # sparse offbeat ticks
            t_hats.add(at(bar, step), drums.one("Hat_Closed", "soft", 0.5))

    def chant_bar(bar):
        for beat, m in ((0, 61), (4, 64), (8, 61), (12, 59)):
            t_chant.add(at(bar, beat), synth_chant(m, dur=0.32, voices=12,
                                                   seed=500 + bar + beat))

    # ================= PART A: the murky closet =================
    murk = loop_slice(0, 2, lp=3200, gain=0.9)
    t_loopA.add(at(0), murk)
    t_loopA.add(at(2), loop_slice(2, 2, lp=3200, gain=0.9))
    snip = synth_vox(49, 1.2, vowel="oh", formant_shift=0.75, vib_depth=0.1, seed=9)
    t_vox.add(at(2, 4), np.tanh(snip * 2) * 0.8)  # pitched-down vox snippet

    for b in range(4, 28):     # verse A1
        t_loopA.add(at(b), loop_slice(b % 8 if b % 8 < 4 else b % 4, 1, lp=3400, gain=0.85))
        bass_A(b)
        drums_A(b)

    for b in range(28, 36):    # hook: evil nursery music-box
        t_loopA.add(at(b), loop_slice(b % 4, 1, lp=3400, gain=0.8))
        bass_A(b)
        drums_A(b)
        if b % 2 == 0:
            nursery_2bars(b)

    for b in range(36, 56):    # verse A2 (+ shaker, rim ghosts)
        t_loopA.add(at(b), loop_slice(b % 8 if b % 8 < 4 else b % 4, 1, lp=3400, gain=0.85))
        bass_A(b)
        drums_A(b, extra=True)

    # ================= THE SWITCH =================
    t_loopA.add(at(56), loop_slice(0, 1, lp=2200, gain=0.8))
    t_loopA.add(at(57), loop_slice(1, 1, lp=1100, gain=0.7))
    stopped = loop_slice(2, 1, lp=900, gain=0.75)
    t_loopA.add(at(58), np.stack([slowdown(stopped[0], 0.4), slowdown(stopped[1], 0.4)]))
    tone = np.sin(2 * np.pi * 425 * np.arange(int(bar_s * SR)) / SR) * 0.22
    gate = (np.arange(len(tone)) / SR % 0.5) < 0.25   # dead-phone-line beeps
    t_fx.add(at(59), tone * gate)

    # ================= PART B: the burnt cathedral =================
    for b in range(60, 90):
        if b == 72:
            continue  # one full bar of dead silence — the negative space
        rb = 8 + (b % 4)  # the choir bars of the record, revealed bright
        t_loopB.add(at(b), loop_slice(rb, 1, gain=1.0))
        bass_B(b)
        drums_B(b)
        if b >= 68 and b % 2 == 0:
            chant_bar(b)

    # outro 90-99: choir + crackle + 808 tail, abrupt end
    for b in range(90, 98):
        t_loopB.add(at(b), loop_slice(8 + (b % 4), 1, gain=0.8))
    t_808.add(at(96), k808.note(CS1, 8 * sx) * 0.9)
    end = loop_slice(11, 1, gain=0.75)
    t_loopB.add(at(98), np.stack([slowdown(end[0], 0.5), slowdown(end[1], 0.5)]))

    stems, dur = seq.render_stems(100, tail=3.0)
    stems["pro_reveal"] = conv_reverb(stems["pro_reveal"], IR["church"], mix=0.3).astype(np.float64)
    stems["chant"] = conv_reverb(stems["chant"], IR["church"], mix=0.25).astype(np.float64)
    return stems, duck, dur, crate


def export_midi(path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    for name, prog in (("808", 38), ("nursery", 10), ("crate", 0)):
        inst = pretty_midi.Instrument(program=prog, name=name)
        for midi, t0, t1 in midi_notes[name]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=midi, start=t0, end=t1))
        pm.instruments.append(inst)
    pm.write(path)


def main():
    import soundfile as sf
    from .mix import mix_and_master
    stems, duck, dur, crate = build()
    print(f"{len(stems)} stems, {dur:.1f}s")
    mix_path, _ = mix_and_master(stems, duck, BPM, "output_g59")
    sf.write("output_g59/crate_source.flac", crate.T, SR, subtype="PCM_24")
    export_midi("output_g59/beat.mid")
    import pyloudnorm
    x, sr = sf.read(mix_path)
    print(f"mix: {mix_path}  {pyloudnorm.Meter(sr).integrated_loudness(x):.1f} LUFS")


if __name__ == "__main__":
    main()
