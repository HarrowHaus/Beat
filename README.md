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
