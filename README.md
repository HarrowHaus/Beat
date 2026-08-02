# Beat productions


Seven instrumentals, produced entirely in code (headless, no DAW), mixed and
mastered production-ready for vocals.

---

## Machine ears (`beatlab/ears.py`)

The pipeline now listens to itself — no human feedback required:

- **Reference calibration**: 30-second preview fingerprints of the actual
  commercial corpus (ALL RED, CARNIVAL, VULTURES, FIELD TRIP, EVILJ0RDAN,
  Praise God, Hurricane, Type Shit, PREACHER MAN via the iTunes preview API)
  — band balance, onset density, crest factor, dynamics, percussive ratio.
  `RefBank.gap_report()` flags any render feature >1.3 sigma from the refs.
- **CLAP perceptual critic** (LAION audio-text model, runs on CPU): scores
  renders against pro/amateur text prompts and by embedding similarity to
  the reference corpus. `ClapCritic.rank()` = a learned taste function.

First calibration pass on HEIRLOOM moved sub energy from 0.18 to 0.66
(refs: 0.53), crest from 6.3 to 7.6 dB (refs: 9.1), while CLAP places all
six beats' "professional" scores inside the commercial reference band.

# KVLT — industrial Yeezus flip of an original black metal record

**Listen:** `output_kvlt/beat_mix.mp3` · master: `output_kvlt/beat_mix.flac`
**The "sample":** `output_kvlt/sample_source.flac` — an ORIGINAL black metal
song written and recorded for this beat (tremolo power-chord riff in
E minor/Phrygian, blast beats, shrieks, necro demo-tape print), so the flip
is clearance-clean by construction.

The flip, Yeezus-style: chops pitched −3 st (Em → **C♯ minor**, the Yeezus
key center), MPC re-triggers/stutters/one reversed chop as the hook melody,
a Surge lead **interpolating** the riff at quarter-note speed (the
legally-distinct replay layer), industrial half-time drums (distorted kick,
fat snare + stomp on 3), sub-first 808s per the machine-ears calibration.
**Blast break** at bars 36–39 where the raw record tears through; 2-bar
clean real-choir mute at 62–63 (the sacred interruption) before the
loudest section; tape-stop outro over the reversed source.

| | |
|---|---|
| BPM | **144** half-time (source recorded at 144 — chops loop on-grid) |
| Key | **C♯ minor** (source in E minor, pitched −3) |
| Length | 82 bars ≈ 2:17 · −10.5 LUFS · −4 dBFS TP |
| Ears | born calibrated: sub 0.46 (refs 0.53), presence 0.017 (refs 0.026) |

12 stems + MIDI in `output_kvlt/`. Rebuild: `python -m beatlab.score_kvlt`

---

# HEIRLOOM — first fully release-grade production (v2 pipeline)

**Listen:** `output_heirloom/beat_mix.mp3` · master: `output_heirloom/beat_mix.flac`

Original composition on the upgraded professional pipeline — no synthesized
toy timbres:

- **Surge XT** (full open-source synth) rendered headless via **surgepy**
  (built from source): factory patches *Deep End* (bass), *Belle* (motif
  pluck), *Choir Pad Thing*, *DX EP* (keys), *Minor 7* (stabs)
- **Professionally produced tuned 808s** (chromatic kits; Long style in
  verses, Distorted in the final hooks) + **velocity-layered** pro
  kicks/claps/hats (soft/mid/hard = real humanization)
- **Real recorded choir** (Sonatina Chorus, male + female) printed through
  a **real church impulse response**; EMT-140 plate on claps and pluck —
  convolution, not algorithmic reverb
- Produced risers, downlifters, crashes for every transition

| | |
|---|---|
| BPM | **146** half-time |
| Key | **B♭ minor** — B♭m / B♭m / G♭maj7 / Fm7 |
| Length | 84 bars ≈ 2:18 |
| Loudness | **−8.8 LUFS integrated**, −4 dBFS true peak — commercial level with vocal headroom |
| Stereo | 6.7% side energy >500 Hz, dead-mono sub <150 Hz (verified) |

12 stems + MIDI in `output_heirloom/`. Rebuild: `python -m beatlab.score_heirloom`
(requires the pro source layer — see `beatlab/pro.py` docstring for the
clone/build commands: Surge XT + surgepy, GareBear99 kits, Sonatina Chorus,
Voxengo/EMT-140 IRs).

---

# NO MOON — an original composition

**Listen:** `output_nomoon/beat_mix.mp3` · master: `output_nomoon/beat_mix.flac`

Not modeled on any song — the corpus research is vocabulary here, not a
template. **138 BPM half-time, G minor, 80 bars ≈ 2:19.**

What makes it its own piece: **functional harmony** (a i–VI–III–VII cycle,
Gm9–E♭maj7–B♭add9–Fadd9, with a real harmonic-minor cadence bridge
Cm–D7♭9–Gm) instead of the genre's static vamps; a singable two-bar motif
played by **FM bell and synthesized voice in unison** — one composite
timbre; a **tresillo (3+3+2)** cell driving the 808 and hat accents; low
choir "answers" at hook phrase-ends; and a **cyclical form** — the song
ends as it began, motif alone over vinyl, the voice leaving before the
bell. 11 stems + MIDI in `output_nomoon/`.

Rebuild: `python -m beatlab.score_nomoon`

---

# CARNIVAL SKINHEAD — Yeezus × Vultures fusion

**Listen:** `output_yeezus/beat_mix.mp3` · master: `output_yeezus/beat_mix.flac`

Twin research tracks fed this one: a composition/style study of Yeezus
(track-by-track BPM/keys/producers, Rick Rubin's documented 15-day
strip-down, the structural-interruption grammar) and a sound-design study
(TB-303 diode-ladder behavior, wavefolding, brass-cannon recipes, choir
ensemble realism).

| | |
|---|---|
| BPM | **145** — New Slaves (141) / FUK SUMN (142) / VULTURES (146) / CARNIVAL (148) intersection |
| Key | **C♯ minor**, Phrygian ♭II (D major) in the stabs |
| Length | 91 bars ≈ 2:30 |
| Headroom | −4 dBFS true peak, vocal-ready |

The grammar, per song it's borrowed from: **On Sight** — cold open on a
broken screaming acid line (two saws detuned −45 cents through an
envelope-swept resonant lowpass, then a wavefolder — the modular
ingredient). **New Slaves** — verse B strips to two-chord 45%-pulse stabs
with a sub-octave saw undertone; drums out. **Black Skinhead** — triplet
long-short-short tom gallop (live-humanized ±8 ms/±3%), pant-breath
percussion, Tarzan-scream fills. **Blood on the Leaves** — TNGHT brass
cannons detonate after the interruption. **THE INTERRUPTION** — hard mute
at bar 56 into a clean, wide gospel choir in the relative E major (per-voice
onset scatter, formant-length variation), then smash-cut into the loudest
section. **CARNIVAL** — stadium chant rides every hook as the melody.
**Send It Up** — dancehall dembow outro with pitched vox, ending on one
unresolved D-major choir chord.

Mix rules from the research: dry, center, clipped — only the choir and
chant get width, so width itself is the structural contrast. 14 stems +
MIDI in `output_yeezus/`. Rebuild: `python -m beatlab.score_yeezus`

---

# ANTIVENOM — in the style of VENOM / FIELD TRIP (¥$, Vultures 2)

**Listen:** `output_venom/beat_mix.mp3` · master: `output_venom/beat_mix.flac`

The reference ("VENOM" is the leak title of FIELD TRIP, the Carti "spittin'
out venom" track) is built on the Portishead "Machine Gun" industrial
drum-machine loop. This recreates that character from scratch — no sample:
a blunt bit-crushed kick and a **metallic, splattery snare** (noise × square
ring-mod, 6-bit crush, bone-dry, mid-forward), with machine-gun 32nd stutter
bursts at 4-bar turnarounds.

| | |
|---|---|
| BPM | **122**, half-time feel (~61), straight grid — no swing |
| Key | **F♯ minor**, static drone harmony: i / i / ♭VI / ♭VII |
| Length | 76 bars ≈ 2:30 |
| Headroom | −4 dBFS true peak, vocal-ready |

The drums are the melody: dark low-passed analog drones and a sparse eerie
bell motif are the only pitched content over a gliding F♯–E–D 808. Verse A
strips to loop + sub (Carti's pocket), verse B floats the drone back with
bell delay throws (Toliver's pocket), then the **beat-switch outro** drops
the industrial loop for a warm Rhodes bed (Dmaj7–C♯m7–F♯m9) with choir —
the Kodak-section move. 12 stems + MIDI in `output_venom/`.

Rebuild: `python -m beatlab.score_venom`

---

# PREACHER'S CRUSH — the 2026 Ye beat

**Listen:** `output2026/beat_mix.mp3` · master: `output2026/beat_mix.flac`

Concept (from 2025–26 catalog research): **"Preacher Man's church + King's
menace."** Bully-era DNA — chipmunk-soul chop, gospel organ, SP-1200 grit,
sub-2:30 song form — crushed through Yeezus-grade industrial processing,
resolving into a celestial outro with a Picardy lift and a tape slow-down.

| | |
|---|---|
| BPM | **84** half-time, ~57% MPC swing on 16ths |
| Key | **C minor** — Cm9 → Fm9 → B♭13sus → G7♯9, A♭maj7/G7♯9 turnaround |
| Length | 46 bars ≈ 2:15 (Bully brevity is a feature) |
| Headroom | −4 dBFS true peak, vocal-ready |

Signature moves, all research-derived: the "soul sample" is **synthesized from
scratch** (glottal source → vowel formants → vibrato), chipmunk-shifted
(+1 octave, formants up) in hooks and pitched −12 with dark formants in the
crush section; every chop is printed through 12-bit SP-1200-style rate
reduction and tape saturation over a vinyl bed. Drums are swung boom-bap
(kick displacement, ghost rimshots, no trap rolls) that mutate into an
industrial stomp with a **metallic clank replacing the snare** in verse B —
the *Sisters and Brothers* fuzz-the-loop move. A cappella chop+sub bridge
(Ye edit culture), wailing vox lead + interstellar 5ths in hook 2, then
drums-out organ/choir outro: Cm → A♭maj7 → **E♭ major lift** with tape
slow-down on the final chord.

Arrangement: intro (raw un-quantized chop) → verse A (organ sneaks in) →
hook (chipmunk + choir + tambourine) → **crush** → a cappella bridge →
hook 2 (+wail, +stars) → celestial outro. 13 stems + MIDI in `output2026/`.

Rebuild: `python -m beatlab.score2026`

---

# HARROW — rage × Vultures hybrid instrumental

A Playboi Carti / Vultures-era Kanye West style rap beat, produced entirely
in code (headless — no DAW), mixed and mastered production-ready for vocals.

**Listen:** `output/beat_mix.mp3` (preview) · `output/beat_mix.flac` (24-bit master)

## Spec

| | |
|---|---|
| BPM | **148**, half-time feel (backbeat ≈74) |
| Key | **A minor**, Phrygian ♭2 (B♭) color in lead and bass turn |
| Length | 80 bars ≈ 2:12 |
| Headroom | −4 dBFS true peak, no brickwall crush — vocal-ready |

Reference corpus: BACKR00MS (146/Am), ALL RED (143/Am), CARNIVAL (148/C♯m),
VULTURES (146/C♯m), FUK SUMN (142/Em), Stop Breathing, EVILJ0RDAN.

## Production notes (research-derived)

- **808 is the kick** (F1lthy convention): CC0-sampled distorted 808 retuned per
  note, layered with a synthesized gliding sine sub; hard-kick transient on top.
- **Clap/snare on beat 3 only** — the half-time trap backbeat.
- Hi-hats: straight 8ths punctured by 32nd rolls (bar 2 of each loop) and
  pitched triplet bursts (bar 4); WLR-style full hat dropouts in verse 2.
- **Chant stabs on beats 2 & 4** of every hook — the CARNIVAL crowd device,
  synthesized as detuned formant-filtered voice clusters.
- Rage lead: 7-voice detuned supersaw ostinato (2-bar loop), low-passed ~7–9 kHz.
- Whole instrumental bus runs through **one shared soft-clipper** (Working On
  Dying method) so elements melt together.
- Energy managed by **mutes, not additions**: drum mute at bar 11, cold stop at
  bar 35 beat 3, drums-out breakdown at 52–55, layer-peel outro.

## Arrangement (bars)

```
0–3    intro       filtered lead alone, riser
4–11   hook 1      full stack, chant on 2&4
12–27  verse 1     lead out → sparse bell; vocal owns 1–4 kHz
28–35  hook 2      cold stop on beat 3 of bar 35
36–51  verse 2     hats out 44–46 (WLR sparseness), return with roll
52–55  breakdown   drums out: chant + choir pad + filtered 808 swells
56–71  double hook + open hats, octave 808 stabs 68–71
72–79  outro       layers peel, lead filters down
```

## Vocal-ready mixing

- −4 dBFS true-peak master, glue compression only (no limiter smash)
- −3 to −4 dB pocket carved at ~3 kHz on lead/pad/chant + master for vocal presence
- Sub mono-folded below 150 Hz; rumble high-passed below 24 Hz
- Everything except 808/kick sidechain-ducks on 808 hits (the pump)
- Stems delivered so the vocal engineer can ride the lead under hook vocals

## Files

- `output/beat_mix.flac` — 24-bit 44.1 kHz master (`beat_mix.wav` regenerable:
  `python -c "import soundfile as sf; d,sr=sf.read('output/beat_mix.flac'); sf.write('output/beat_mix.wav',d,sr,subtype='PCM_24')"`)
- `output/beat_mix.mp3` — 320 kbps preview
- `output/stem_*.flac` — 9 stems: 808, kick, hats, clap, lead, bell, pad, chant, fx
- `output/beat.mid` — MIDI of 808 line, lead, bell (tempo-mapped, 148 BPM)

## Rebuild from source

```bash
pip install numpy scipy soundfile pedalboard mido pretty_midi
git clone https://github.com/Boochi44/free-drum-samples.git /path/to/kit  # CC0 1.0
BEATLAB_KIT=/path/to/kit/drum-samples/01-hard-trap python -m beatlab.score
```

`beatlab/engine.py` — synthesis + 16th-grid sequencer ·
`beatlab/samples.py` — CC0 kit loader, 808 root-pitch detect/retune ·
`beatlab/mix.py` — per-stem chains + mastering ·
`beatlab/score.py` — the song itself.

Drum one-shots: [Boochi44/free-drum-samples](https://github.com/Boochi44/free-drum-samples)
(CC0 1.0 — free for commercial use, no attribution required).
