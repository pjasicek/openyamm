# Xeen music: the original notes, modern instruments (2026-11-23)

The user asked whether the original Might and Magic IV/V music could sound modern instead of 16-bit. These
renders play every note of the game's own songs (`reference/mm4_5_world_of_xeen/unpacked/music/*/*.m`, all 55)
with sampled instruments in place of the AdLib FM chip. Since U-13 (2026-11-23) eight of them are Xeen's themes
92001–92008 (`devdocs/xeen/MUSIC.md` lists which).

## How

1. **Read the song** (`xeen_song.py`). The `.m` format comes from `output/xeen_music/README.md`, read from the
   game's driver. Each of the music channels 0–6 is one monophonic voice. Notes, waits, instrument slots and
   subroutine calls are walked once per pass at the driver's 72.80 Hz tick. Two things the FM drivers ignore are
   used here:
   - **Note velocities:** they come from the original sequence.
   - **Controller 0:** the MIDI (MT-32) channel volume, 0–127. The FM mixes, controllers 2 and 5, switch off parts
     the chip could not carry; the MT-32 mix keeps them.
   - **Channel 8:** General MIDI percussion stored as raw drum numbers (36 kick, 38 snare, 42 hi-hat, 49 crash,
     54 tambourine, 61–62 bongos, 69 cabasa, 75 claves ...). The AdLib never played these drums.
2. **Choose instruments** (`orchestrate.py`, then by hand). There is one General MIDI instrument for each channel
   and each FM instrument slot, because a channel that switches from a bass sound to a lead sound gets two. The
   choice comes from what the part plays: register, note lengths, how busy it is, and whether the FM patch
   sustains. Roles are bass, held chords, arpeggio, bells, plucks, the tune and counter-lines; the sci-fi songs use
   a synth palette. `orchestration/<face>_<name>.yml` is never overwritten once it exists, so hand-tuning is safe.
   `xeen_castle.yml` is hand-orchestrated.
3. **Render** (`render.py`). FluidSynth 2.4.4 is built from source in `output/xeen_music_modern/third_party/`,
   because the PC has none; without libsndfile it writes 16-bit raw output. It plays the MuseScore General
   soundfont (MIT; FluidR3 lineage; the credits are in its licence file, which must be kept with derivative work).
   Each channel and slot is rendered as its own part and mixed here:
   - velocities with a slow phrase drift and small random variation;
   - onsets loosened by about 7 ms;
   - held notes swell (CC11);
   - a short legato overlap on sustained instruments;
   - equal-power stereo placement;
   - a synthetic stereo hall reverb (our own impulse: early reflections, then decaying noise that darkens);
   - a 30 Hz high-pass, gentle compression and a limiter;
   - a final level of -17 dBFS RMS with peaks at most -1 dBFS, like 92001–92008.
4. **Loop:** three passes are rendered and the second is kept. It opens with the first pass's reverb and
   releases, and its first second is crossfaded from the third pass's opening. Mastering runs before the cut, so
   the end runs into the start without a click. Cavern's wrap jump is 0.003, against an ordinary sample step of
   0.057.

## Pitch

Every song decodes a whole tone below the composer's MT-32 recordings and every arrangement:
- town is F major here, G major there;
- outdoors is C minor here, D minor there;
- end game is A-flat here, B-flat there;
- the sci-fi theme is B-flat minor here, C minor there.

The emulated AdLib renders in `output/xeen_music` read in the same lower keys. The renders follow the composed keys:
`TRANSPOSE = 2` in `render.py`, and a `transpose` key per song overrides it. Whether a real AdLib also played a
whole tone low was not checked. The FM patches' frequency multiples are not applied (`patch_octave`), because the
MT-32 played the same note data at its written pitch.

## Checks (`checks.py`)

- **Harmony against the downloaded recordings:** chroma DTW, compared with the same recording shifted 1–11
  semitones. Castle scores 0.94 against 0.72 for the wrong keys, the sci-fi theme 0.96 against 0.65, outdoors 0.93
  against 0.80.
- **Loop wrap, level and peak** for every song.

Results are in `work/checks.json` and on the page.

## Listening

Run `python3 review_page.py`, then open `review/index.html` from disk. Each song has the new render and the AdLib
render. The game's theme songs also have 90 s of the MT-32 recording or arrangement
(`../xeen_music_alike_20261123/work/ref_clips`, git-ignored). Renders are in `out/` (`.wav` and 320 kbit/s `.mp3`).

## Running

```sh
PY=<venv with numpy scipy mido pyyaml pedalboard soundfile librosa>
$PY describe.py xeen/town                 # what each channel plays
$PY orchestrate.py --all                  # drafts for songs without an orchestration file
$PY render.py xeen/town xeen/outdoors     # out/xeen_town.{wav,mp3}
$PY checks.py && python3 review_page.py
```
