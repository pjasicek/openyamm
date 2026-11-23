# Xeen sound-alike themes (2026-11-23)

The user asked for Eleven Music tracks that sound like the original Might and Magic IV/V themes, "capturing the
essence". Eight takes were made, one for each of Xeen's own theme slots 92001–92008 (devdocs/xeen/MUSIC.md). They are
**not installed**: the user compares them first.

- **References:** real MT-32 recordings of the originals and Xeen Music's prototype arrangements, downloaded from
  YouTube into `work/ref/` (git-ignored, never committed, published or uploaded). The video ids are in
  `work/ref/list.txt`, and the arranger's notes (instruments, commissions) are in `work/ref/*.desc.txt`. The licence
  check of the Xeen Music store (all rights reserved, no redistribution) was done the same day.
- **Analysis:** `analyse.py` measures tempo, key per 30 s, meter, chords per bar and the top line from a basic-pitch
  transcription, and draws a spectrogram and chroma. `pianoroll.py` draws a transcription excerpt with a beat grid.
  Results are in `work/analysis/`.
- **Generation:** `jobs.yml` (`tools/run_elevenlabs.sh`) used music_v2_5 with one 150 s seamless loop per theme, the
  same settings as 92001–92008. It cost 18 000 credits. Each prompt describes tempo, key, chord motion, groove,
  instruments, mood and era. No prompt names a composer, game or work, and no reference audio is sent: Eleven Music's
  audio reference accepts only music you made yourself. The takes therefore share the originals' character, not
  their melodies.
- **Comparison:** run `python3 compare_page.py`, then open `review/compare.html` from disk. Each section has 90 s of
  each original beside the new take and the theme it would replace. The page is local only, because the originals
  are not ours.

## Measured against the targets

| Take | Target | Measured |
| --- | --- | --- |
| Cloudside overworld | D minor, 96 BPM | D minor, 96 |
| Darkside overworld | A minor, 80 | C minor, 81 (doubled to 161) |
| Cloudside towns | G major, 112 | G major, 112 |
| Darkside towns | B minor, 84 | B minor / D major, 83 |
| Castles | G major / E minor, 66 | A minor, 65 (doubled to 129) |
| Dungeons | E minor, 64 | E minor / E major, 65 (doubled to 129) |
| Ancients | C minor, 123 | C major, 123 |
| Finale | B-flat major, 108 | D minor, 108 |

Every tempo landed. Three keys or modes differ: Darkside overworld, Ancients and Finale.
