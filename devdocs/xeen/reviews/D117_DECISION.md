# D-117: outdoor beds too loud (2026-11-23)

**Question** (the user, from Discord players: "the birds chirping in Vertigo ... might be too loud"): should the
outdoor ambience beds be turned down, which, by how much and where?

## Evidence (asking session)

- X1 Vertigo Meadows: 8 `xeen_amb_meadow` emitters (0.35, 6000/15000, day only, pan: false), the same 8 places for
  `xeen_amb_night` (0.3, night only), 4 `xeen_amb_lagoon` (0.6, 3500/9000). About 2 meadow emitters are heard at once
  on average, up to 6; Vertigo town is inside the full-volume circle of two.
- Clip loudness (ffmpeg ebur128): meadow -17.9 LUFS (51 % of its energy above 2 kHz), night -16.7 (100 %), savannah
  -16.7 (97 %), volcano -17.2, sky -19.7, darkside -20.7, desert -20.7, lagoon -24.5, tundra -24.4, mine -32.1.
- With the overlapping emitters (power sum) and the default sliders (sounds 3.5 dB over music,
  `devdocs/mm9_rework/MM9_AMBIENT_VOLUME_RE.md`): X1's meadow heard at about -23 LUFS median, -21 at most, against
  music at about -15 LUFS. Ambience shares the World group's slider; a player cannot lower it alone.

## Ruling (decider, read-only)

**DECISION.** Option A, narrowed: cut three bed clips at install, -6 dB, through a per-job `gain_db` in `jobs.yml`
applied by `install.py`: `xeen_amb_meadow`, `xeen_amb_savannah`, `xeen_amb_night`. Every other bed unchanged. No
scene volume, `beds.yml` or per-map bed changes, no rebuilds. AUDIO.md's Levels paragraph updated. No engine Ambience
slider (D) and no regenerated birdsong (E) for now.

**WHY.** The complaint is about the treble beds, which are also the three loudest clips, nearly all energy above
2 kHz, looping every 28-43 s; LUFS under-rates how a constant high band nags, and between music tracks the bed is all
one hears. The fault is in the clips, not the placement: they are equally hot on every map using them, so levelling
at install fixes the source data once (clips under -20 RMS are already normal, and install already re-levels for
`bed_highpass_hz`). -6 dB lands them about level with the lagoon and tundra beds, about 14 dB under the music. Option
C rebuilds four maps to fix three clips; D is engine and settings work touching MM9 and MM6-MM8's audio settings (the
user's call); E spends credits on what is mostly a level problem. MM6-MM9 unchanged.

**WHO ACTS.** AU: the field, install.py, reinstall of the three, AUDIO.md. Then a check by ear in Vertigo town by
day and night at the default sliders.

**REVERSIBLE.** Entirely: remove the field and reinstall.

**CONFIDENCE.** About 70 %. Least sure of the amount (from measurements, not ears): if it still sounds busy, -8 dB
for the meadow alone. Also unsure whether players mind the loudness or the repetition of the loop; if complaints
continue after the cut, a sparser loop (E) is the next answer.

## Done (2026-11-23)

`install.py` `apply_gain` (after any high-pass re-levelling, before the ADPCM pack); `gain_db: -6` on the three jobs;
the three WAVs reinstalled (meadow -23.9, night -22.7, savannah -22.7 LUFS; no other WAV and no sounds.txt row
changed). The check by ear is still open.
