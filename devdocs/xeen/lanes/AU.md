# AU: audio (ElevenLabs)

Started 2026-11-20 by the second orchestrator at the user's word: "use elevenlabs for the stuff as well if you want, if
it warrants even multiple variants to select the best one."

## Owns

- `devdocs/xeen/AUDIO.md`: the world's sound list (what each sound is for, where it plays, its engine name and id).
- `level_generation/sounds/xeen_20261120/` (`jobs.yml`, `picks.yml`, `ledger.json`, raw takes, review page): the job
  file for `tools/run_elevenlabs.sh` (`tools/audio/README.md`).
- Sound rows of the world (ids 62000–63999; ROADMAP §4 said 70000–79999, see AUDIO.md) and the installed WAVs under `assets_dev/worlds/xeen/` (the
  world's sound table contribution; ask A1 for a `tableContributions` entry if one is missing).

Never touches: monster rows (A2 sets a family's sound ids from this lane's list), map projects (map lanes place
ambient sounds and event sounds by name), music by number (MUSIC.md, A6) unless a decider changes Q9.

## Read first

`tools/audio/README.md` (the tool, the ledger, variants, picking, voice treatment), Hesper's `design/kreegan_world/AUDIO.md`
and `design/kreegan_world/audio/jobs.yml` (the model), `level_generation/sounds/solo_archetypes_20261118/jobs.yml`,
`devdocs/AMBIENT_SOUNDS.md`, `devdocs/xeen/ROADMAP.md` §0, §5.8, `devdocs/xeen/MUSIC.md`, `devdocs/xeen/WORLD_DESIGN.md`
§1 (voice), `assets_dev/worlds/xeen/source/monsters.yml` (families and their current stand-in sounds).

## Rules

- Budget: the user lifted the cap on 2026-11-21 ("use however much you need, if it makes sense"): raise the job
  file's `budget` as needed (140 000 since session 5), shipped sounds first, no needless re-takes (measure before a
  re-prompt). `music: false` (music stays MM6–MM8 tracks by number, Q9, unless a decider says otherwise). Report
  credits charged and committed in every report.
- Three variants per sound by default (more where the sound carries a lot: boss cries, signature ambience); pick by the
  tool's metrics and by listening analysis, write why under `listening` in picks.yml; voice lines checked with Whisper.
- Prompts never name a game, film or artist.

## State (2026-11-21, end of session 5)

**Installed: 264 sounds** (ids 62000-62237, 62500-62544, 62800-62821, 63000-63040, 63100-63127) as
`assets_dev/worlds/xeen/audio/xeen/*.wav` and the rows of `assets_dev/worlds/xeen/audio/sounds.txt` (the world's
`sounds` table contribution), by `level_generation/sounds/xeen_20261120/install.py`. The list, ids, picks and hooks:
[AUDIO.md](../AUDIO.md); this session's is "Session 5", with every line the map lanes paste ("The lines to paste").

- **Session 5's queue is done** (the sounds; the pasting is the map lanes'): P5's four chimes and fanfare (D-56); D7's
  corners (the plane beds as point sounds; the four corner jobs not installed), the Megadragon asleep, the cloud
  dragons' calls, the bandits' whistle (D-58); one bed per plane P1-P4; DD-17 trapdoor and klaxon; DD-15 torch (pads
  `Teleport` and the vat's shipped cauldron kept); DD-22's `buzzer01`/`tone2` replaced (menu buzz and beep); DD-25's
  forge loop; DD-21's heartbeat; DD-26's purring; FD-01's grit, stasis hum and groan; X7's volcano bed and range wind;
  night beds (`xeen_amb_night`, `night_only` twins of X1, X2, X4 and X5's day beds). D5's Barrier hums and hold fire
  were already placed: checked from assets_dev in the game.
- Not installed (measured, `listening.yml`): `xeen_corner_*` (rumble or swells out of silence), `xeen_brew_vat` (no
  bubbling). Re-prompted once: P3's earth, P4's water, the night bed.
- **`pan: false` from assets_dev** (`work/check_pan.py`): every outdoor map and A7's indoor maps right; A8's DD-01,
  DD-02, DD-10A, DD-10B, DD-12, DD-18, XD-11, XD-12 still panned, and DD-19's three beds (new on the list).
- All 25 new sounds start in the game (D1's scene with them added through an extra mount); D5 from assets_dev.
- Credits: budget raised to 140 000; **charged 37 791, committed 132 950** (session 5: 10 783 charged, 39 200
  committed, 96 requests).

Tools of the lane (in the job folder): `analyze.py`, `listening.yml` + `merge_listening.py`, `install.yml` +
`install.py` (`bed_highpass_hz`), `voices.py`, `whisper_check.py`, `beds.py` + `beds.yml` (`pan: false` on beds,
`night_only` twins, a district drawing for maps without a minimap); `work/look.py` (session 5: any file through ffmpeg:
bands, tonal peaks, envelope, onsets, `--png DIR` spectrograms and a sheet), `work/pitchtrack.py` (dominant pitch per
step: a fanfare's melody, a whistle's shape, an alarm's tones), `work/check_pan.py` (the installed scenes against
D-48), `work/bands.py`, `work/onsets.py`. Their venv is `work/venv` (git-ignored; faster-whisper, parselmouth, scipy,
pyyaml); `analyze.py`, `beds.py`, `look.py` run on the system python3 (numpy, scipy, PIL). Note: `analyze.py <ids>`
rewrites `review/analysis.txt` and the group sheets with those jobs only; run it without ids at the end (done in
session 5).

Next: check the pasted session 5 lines from assets_dev once the lanes install them (P5's cinematic cues, D7, P1-P4,
X7, the night beds at night, A8's dungeons); A8's missing `pan: false`; confirm A2's batch 2 names; `xeen_fortune` as a
house `enter_sound` once A1 has the field.

## Log

- 2026-11-20 session 1: survey and plan (AUDIO.md); jobs.yml (89 generated jobs, 45 derived); 284 requests; picks by
  measurement and spectrogram reading (18 overrides of the automatic score, each with its reason); mine, tower and
  obelisk re-prompted after their first takes came out sub-bass alone; installed; validated in game (scratch root,
  deleted after).
- 2026-11-20 session 2: D-38 voices: seven designs (two more for Corak and the Pharaoh to pull them apart from Lord
  Xeen), 45 takes, nine sounds installed at 63000-63040 (3 826 committed of the 4 000 cap); "Ah! A Soulbox!" took four
  prompts and Lord Xeen's laugh a second prompt at stability 0. Batch 2: 156 requests plus 12 re-prompted (hornets,
  snake men), 84 sounds installed. Desktop checks with the audio trace.
- 2026-11-20 session 3: outdoor beds laid out for X1-X6 and D1-D4 by `beds.py` (hex lattice per bed field from the
  sketches' districts; 130 emitters), the lists in AUDIO.md for A5 and A6; checked on a scratch X6 in the game. Desert
  and Darkside beds regenerated (6 takes), the desert high-passed at install. D-47: five sounds generated (16 takes) and
  installed at 62520-62524, the generators and stasis field on the shipped `humming`. 22 requests, 3 194 charged.
- 2026-11-21 session 4: D-48: `pan: false` on every bed line beds.py writes; X1-X6, D1-D4 regenerated (positions
  unchanged); indoor bed list for A6/A7/A8; checked in the game (X6 from assets_dev, D1 with the word through an extra
  mount, a misspelt key as the control). D-49/D-50: shipped sounds first; eight jobs generated (29 requests, the
  high-striker re-prompted), seven installed at 62525-62527 and 62810-62813, the ash bed rejected; lists for D5, D6
  (A6) and X9, XD-17 (A5). 3 960 charged, 14 400 committed.
- 2026-11-21 session 5: budget lifted by the user (job file 140 000). D-56, D-58 and the dungeon asks: 27 jobs (87
  requests) and three beds re-prompted (9); 25 sounds installed at 62528-62544 and 62814-62821, the corners and the
  Brew vat rejected by measurement; DD-22's buzzer and beep replaced. Night beds and X7's beds in beds.yml. Installed
  scenes checked for D-48 (`check_pan.py`); every new name starts in the game; D5's hums from assets_dev. Lines for
  A3, A5, A6, A8 in AUDIO.md. 10 783 charged, 39 200 committed.
- 2026-11-22 lane P (packaging, session 1) for AU: `install.py` now writes the installed copies as IMA ADPCM WAVs
  (`compact_wav`: ffmpeg `adpcm_ima_wav`, 512-byte blocks, bit-exact; SDL_LoadWAV decodes them, no engine change).
  Loops (`loop: true` jobs) are first resampled (periodic FFT) to a whole number of blocks, at most 1,016 frames
  longer (under 4 cents), because SDL pads the last block and ignores the fact chunk, which would put up to 21 ms of
  silence into every repeat. The picks in `out/` stay 16-bit PCM. 264 WAVs 92 -> 24 MB on disk, 77.8 -> 18.9 MiB
  zipped; one-shot SNR median 33.8 dB (min 16.0, hiss beds); seams continuous; decoded in game (`xeen_amb_meadow`,
  `xeen_amb_plane_fire`: frame counts as expected). `install.py --check` 0. Analysis tools that read installed WAVs
  with scipy must read the picks in `out/` instead (none does today). PCM copies of the 264 before the change:
  `output/xeen_p/wav/pcm_before/` (lane P scratch, deleted when P closes).
