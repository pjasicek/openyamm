# ElevenLabs audio generation

`elevenlabs_gen.py` (entry point `tools/run_elevenlabs.sh`, mirroring `tools/run_creature_meshy.sh`) turns a YAML job
file into game-ready audio with ElevenLabs sound effects, music (Eleven Music) and TTS, with a credit ledger and resume. The first user is
Hesper: [`design/kreegan_world/audio/jobs.yml`](../../design/kreegan_world/audio/jobs.yml), its sound list
[`design/kreegan_world/AUDIO.md`](../../design/kreegan_world/AUDIO.md).

```sh
tools/run_elevenlabs.sh plan    design/kreegan_world/audio/jobs.yml          # jobs, done variants, credits
tools/run_elevenlabs.sh run     design/kreegan_world/audio/jobs.yml [ids]    # generate what is missing (paid)
tools/run_elevenlabs.sh run     design/kreegan_world/audio/jobs.yml --dry-run
tools/run_elevenlabs.sh process design/kreegan_world/audio/jobs.yml [ids]    # raw -> WAV variants, metrics, picks
tools/run_elevenlabs.sh review  design/kreegan_world/audio/jobs.yml          # review/index.html
tools/run_elevenlabs.sh create-voice design/kreegan_world/audio/jobs.yml <design id> pN   # save a design preview
```

## Access

The API key lives in `~/.config/openyamm/elvenlabs.key` (mode 600; another path with `ELEVENLABS_API_KEY_FILE`).
The tool reads it at run time and sends it only as the `xi-api-key` header; it is never printed, logged, written to
the repository or put on a command line. The key is restricted to Text to Speech, Sound Effects, Voice Generation and
Voices (write): without `user_read` the balance and the plan cannot be read (`/v1/user/subscription` answers 401), so
the ledger is the record of what was spent.

The key can list voices (`GET /v1/voices`, `/v1/shared-voices`) and add a library voice to the account (`POST /v1/voices/add/<owner>/<voice_id>`, free; the tool has no call for it). It can also design voices
(`POST /v1/text-to-voice/design`) and save them (`POST /v1/text-to-voice`): the tool's `voice_design` kind and
`create-voice` command (below), used for the boss casting of 2026-10-24. Hesper's boss lines use three library voices added that way on 2026-10-24 and one premade voice (design/kreegan_world/audio/BOSS_LINES.md).

## The job file

```yaml
schema: openyamm.elevenlabs.jobs.v1
budget: 50000                    # cap for the workspace's ledger, checked before every request
kind_budgets: {music: 25000}     # optional caps per kind
music: true                      # music jobs run only with this (the user's decision, below)
defaults: {kind: sfx, model: eleven_text_to_sound_v2, prompt_influence: 0.45, variants: 3,
           formats: [wav_48000, mp3_44100_192]}
jobs:
  - id: shield_hit_light         # also the default output name: the engine's sound name
    kind: sfx                    # sfx | music | tts (voice_id, voice_settings) | voice_design | derived (from: [ids or id/vN.wav])
    pitch: -2                    # derived one-shots only: semitones, as tape played slower (lower, longer): a tier's
                                 #   variant of a family sound without a new generation
    # derived one-shots also: each, undertone, saturation, lowpass_hz, loudness_db (matched): see Voice lines below
    prompt: "..."                # describe the sound; never name a game, film or artist
    duration: 0.7                # seconds (0.5-30); a duration is always given so the cost is known
    variants: 3                  # separate requests; the best is picked
    loop: false                  # true: the API's loop flag, then a crossfaded seam
    channels: 1                  # 1 for positional sounds (default), 2 for ambience beds
    output: shield_hit_light     # the installed WAV's name
    group, use, title            # for the review page and AUDIO.md
    # One-shot shaping and picking (processing only: they do not change the request or its hash)
    highpass_hz: 30              # 2nd-order high-pass: drops sub-sonic rumble that only eats headroom
    low_shelf: {hz: 120, db: 5}  # RBJ low shelf: more low end for heavy shots
    loudness_db: -7.7            # lift until the loudest 100 ms reaches this (dBFS), a look-ahead limiter holding
    max_boost_db: 10             #   the peak at peak_db (-1): louder in the mix, never clipped; the boost is capped
    score_bias: power            # pick toward takes loud and dense by nature and with the most low end
    hits: 2                      # the number of distinct shots the take must have (a twin shot)
    redone: {note: ..., before: before_feedback.wav}   # review page: "redone after feedback", the old take to compare
```

### Voice lines: TTS takes and the derived treatment (2026-10-24)

A spoken line is two jobs: a `tts` job that makes the takes (`voice_id`, `voice_settings` passed to the API as given,
`model` default `eleven_multilingual_v2`; `highpass_hz` / `low_shelf` shape each take when it is processed) and a
`derived` job that treats them and is the installed name. TTS costs about one credit per character by the docs; on
2026-10-24 the header reported about half that (18 for a 40-character line).

```yaml
  - id: vo_krav_sight_take        # three takes of the line
    kind: tts
    voice_id: cymHWdiF8WjUCg6vvFxx
    voice_settings: {stability: 0.4, similarity_boost: 0.8, style: 0.4, speed: 1.0}
    variants: 3
    highpass_hz: 70
    low_shelf: {hz: 140, db: 4}
    line: "Overseer Krav: The Yard eats colonists. Squad, feed it."   # the subtitle, shown on the review page
    prompt: "The Yard eats colonists. Squad, feed it."
  - id: vo_krav_sight             # the installed clip
    kind: derived
    each: true                    # one treated variant per take of the source (several sources number on: v4...)
    from: [vo_krav_sight_take]
    pitch: -1.5                   # tape-style: lower and about 8 % slower
    undertone: {semitones: -7, gain_db: -14, delay_ms: 15}   # a copy a fifth lower, its length kept, mixed under
    saturation: {drive_db: 6, mix: 0.4}                      # a tanh soft clip, blended with the clean signal
    loudness_db: -9               # matched: lifted (look-ahead limiter at peak_db) or turned down to the target
```

A derived one-shot runs, after the join: `pitch` (tape), `undertone` (ffmpeg's `rubberband` filter shifts the copy
with the length kept, so it stays on the words; the tail grows by the delay), `saturation`, the tone shaping
(`highpass_hz`, `lowpass_hz` (new, a 2nd-order low-pass; with a high `highpass_hz` a small-speaker band), `low_shelf`),
the peak normalisation and `loudness_db`. On a derived job `loudness_db` is matched rather than only lifted, so a set
of lines plays at one level. The family variants (`pitch` alone) are unchanged by this. With `each: true` the pick is
made on the derived job (`choice: vN.wav` in picks.yml), on what the game plays; the source job's own pick does not
matter. The tool's automatic score does not judge speech: pick voice lines by ear and write why under `listening`.

**Demonic treatment (2026-10-24, the boss casting round).** Four more derived stages, in this order with the others:
`shift` (first), `pitch`, `undertone`, `ring`, `saturation`, `room`, then the tone shaping and loudness.

```yaml
    shift: {pitch: -1, formant: -3, tempo: 1.0}   # pitch and formants apart, in semitones, the length kept (/ tempo)
    undertone: [{semitones: -12, gain_db: -10, delay_ms: 12}, {semitones: -7, gain_db: -14, delay_ms: 15}]
    ring: {hz: 50, mix: 0.12}                     # ring modulation by a low sine, blended with the dry voice
    saturation: {drive_db: 10, mix: 0.5}
    room: {seconds: 0.45, mix: 0.12, lowpass_hz: 2000, predelay_ms: 8}   # a short dark room
```

- `shift` moves the formants (the size of the throat) by tape, then ffmpeg's `rubberband` (`formant=preserved`,
  `pitchq=quality`) puts the pitch where asked and restores the length. A formant shift down makes a voice sound
  larger than a person; a pitch drop alone only sounds like a lower person. `tempo` below 1 slows the line.
- **Keep the pitch drop small on deep voices.** Lowering the pitch of a voice that is already deep (a designed brute
  or lord at 60-100 Hz) is what breaks intelligibility: Ghulkat, Mraal and the Hierarch failed Whisper at -3 to -5
  semitones even as plain tape, and read cleanly with the pitch kept and the formants at -2 to -3.5. Let the formants
  carry the size.
- `undertone` takes a list of layers: a sub-octave (-12) at -6 to -14 dB, a fifth, or a +0.2 detuned double for a
  chorus of throats.
- `ring` at 30-80 Hz and a mix of 0.08-0.22 adds a buzz no throat makes; above about 0.25 it starts to eat words.
- `room` is a synthetic impulse (decaying noise, fixed seed, low-passed): dark and short, 0.25-0.8 s.
- Check every treated take with a speech recogniser (two local Whisper models) before suggesting it.

### Voice Design: `voice_design` jobs and `create-voice` (2026-10-24)

```yaml
  - id: vd_krav_a
    kind: voice_design
    model: eleven_ttv_v3          # or eleven_multilingual_ttv_v2
    prompt: "A harsh, barking alien squad leader: ..."   # the voice description
    text: "The Yard eats colonists. ..."                 # the preview text, 100-1000 characters: the charge
    variants: 1                   # one request returns three previews
    voice_name: "Hesper Overseer Krav A"
    # optional: guidance_scale, loudness, seed, quality, enhance (should_enhance)
```

`run` sends one request per variant; the response's three previews are kept as `raw/<id>/<hash>_vN.pM.mp3` with a
`<hash>_vN.json` record of their `generated_voice_id`s. The design response has no cost header, so the ledger
records the docs rate (one credit per preview-text character, `credits_source: estimate`). `process` writes the
previews as `out/<id>/p1.wav...`. `create-voice <jobs> <id> pN` saves preview N as a voice of the account (free),
writes `voice_id` and `choice` under the job in picks.yml and a 0-credit `voice_create` entry in the ledger; TTS jobs
then name that `voice_id`. Read designed voices with `model: eleven_v3` (`voice_settings: {stability: 0.5}`,
"Natural"): in the pilot it kept the designed roughness better than eleven_multilingual_v2 at the same cost.

**Casting on the review page.** Jobs with `cast: {boss, candidate, current, design}` (and `untreated: true` on the
TTS takes) render as a casting section: per boss the candidates' voice descriptions, then per line the installed
clip (`current`), and candidate A and B side by side with their treatment, the `choice` marked as suggested; the
untreated reads and the design previews collapsed.

A music job (`kind: music`, `model: music_v2_5`, `formats: [pcm_48000]`) sends `prompt`, `music_length_ms` (from
`duration`, 3-600 s) and `force_instrumental` (`instrumental`, default true) to `POST /v1/music`. Its raw download
(interleaved stereo PCM) is kept as FLAC; the variants and the pick are FLAC masters (`master`), and the pick is also
encoded as `<output>.mp3` at 320 kbit/s, the engine's music format (`Music/<N>.mp3`, looped from the start). With
`loop: true` the last `crossfade` seconds are folded into the opening, so the wrap is seamless; a download that fades
out (a trailing run of at least 3 s of 1 s windows more than 6 dB below the median, at most a fifth of the track) is
cut where the fade starts before the fold, so the wrap joins music at the track's own level (`fade_cut_s` in picks).

## What the tool does

- **Ledger** (`ledger.json`): one entry per paid request: job, kind, variant, request hash, time, credits (the response's
  `character-cost` header, `credits_source: api`), the docs-rate `estimate`, format, bytes and the raw file. The budget
  is checked before each request against the larger of report and estimate per request (`committed`), so it cannot
  be overspent by a header that under-reports. On 2026-10-23 the header reported about 11 credits per second of sound;
  the docs say 40. Music responses carry no cost header (only `song-id`, recorded): music is ledgered at the pricing
  page's 900 credits per minute (`credits_source: estimate`), which cannot be checked without `user_read`.
- **Resume**: the raw download is `raw/<id>/<hash>_v<N>.<format>.<ext>`, the hash covering everything sent (prompt,
  duration, loop, model, influence). A variant whose file exists is never requested again; a changed prompt makes new
  variants and keeps the old files.
- **Processing** (`process`): decode to 48 kHz float (the engine mixes at 48 kHz, `engine/AudioSystem.cpp`), down-mix
  to mono unless `channels: 2`; one-shots are trimmed (lead below -50 dBFS with 4 ms pre-roll, tail below -55 dBFS with a
  30 ms fade) and peak-normalised to -1 dBFS; loops get an equal-power crossfade of the tail into the head (`crossfade`
  seconds), so the last sample runs straight into the first, and are levelled to `loop_rms_db` (default -20 dBFS RMS,
  peak at most -1 dBFS). Output: 16-bit PCM WAV, `out/<id>/v<N>.wav`, the pick copied as `out/<id>/<output>.wav`,
  the prompt and settings in `out/<id>/prompt.txt`.
- **Music picks** score a loopable background track: an even level (the 10th-90th percentile spread of 3 s windows,
  the loudest window over the median: swells and climaxes cost), no dead gaps (the longest stretch below -40 dBFS),
  clipping, the asked length, and an opening and ending at the track's own level (no fade-out or finale at the wrap).
  The note gives texture (onsets per minute: sparse, moving, busy), tone (spectral centroid), the level by quarter,
  the spread and the gaps. Listen before trusting it.
- **Picks** (`picks.yml`): each variant's metrics (length, peak, RMS, clipped samples in the download, near-silent
  share, spectral centroid, onset; for one-shots also `punch_db` (the loudest 100 ms), `low_share` (energy below
  200 Hz) and `hits` (distinct shots: rises after a dip of at least 8 dB lasting 40 ms, counted before limiting),
  with `loudness_db` the natural punch, the boost and the limiting; for loops the seam and the level spread over the
  loop) and an objective score; the best is installed. `score_bias: power` adds the natural punch and the low end and
  takes off for more than 6 dB of limiting; `hits` takes 30 off per shot too many or too few. A hand-written `choice: vN.wav` and `listening:` note under a job survive reprocessing.
- **Review** (`review`): `review/index.html`, an `<audio>` player per variant with its prompt, score and note, the
  installed one outlined. Open it from disk (`file://`); it references `../out/`.

## Plan and tier (2026-10-23)

The user confirmed the plan is **paid**. The key cannot read the subscription, but the output formats tell the tier:
`mp3_44100_192` (Creator or higher) and `pcm_44100` (Pro or higher, per the sound-generation API reference) were
accepted, so the plan is **Pro or higher** (the user reported about 131 000 credits). Probe requests are in the ledger.

## Licensing (checked 2026-10-23)

The repository is GPL and commits only assets we own or that are CC0/CC-BY. Checked on 2026-10-23 against the
documents' versions "Last updated: 09 October 2026":

### Sound effects and TTS: usable on a paid plan

- [Terms of Service](https://elevenlabs.io/terms-of-use), 4(c)(ii): "as between you and ElevenLabs, you retain all
  rights in and to your Output". 1(c)(ii): paid users "may use the Services for commercial purposes"; 1(c)(i): free
  users only non-commercially. 4(a): downloaded Output may be used outside the Services, subject to the Terms and the
  Prohibited Use Policy. The same terms apply to sound effects, TTS and voice design (no separate sound-effects terms;
  [Service-Specific Terms](https://elevenlabs.io/service-specific-terms) list none for them).
- ElevenLabs' sound-effects pages ([commercial](https://elevenlabs.io/sound-effects/commercial)): "Our paid plans do
  not require attribution and can be used in commercial projects"; the free plan requires attribution.
- Caveats to keep in mind:
  - ToS 4(d): ElevenLabs keeps a perpetual, sublicensable licence to all Content, Output included, to run and improve
    its services. It does not take our ownership away.
  - ToS 10: the service "may produce the same or similar Output for you and a third party", so a sound is ours but
    not guaranteed unique.
  - [Prohibited Use Policy](https://elevenlabs.io/use-policy), section 12, forbids "Making our Services or Output
    available to your own end users or other third parties on terms more permissive than those that apply to you"
    and putting Output in a dataset used to develop AI models. A GPL or CC licence gives third parties broad rights,
    so read literally this clause sits uneasily with releasing the WAVs under the repository's licence. The clause is
    aimed at reselling the service, and we own the Output (4(c)(ii)), but it is the user's call. The cautious options
    are to license the generated sounds separately ("generated with ElevenLabs; may not be used to train AI
    models") or to keep them out of the repository until decided. The user's decision is at the end.

### Music: the terms' Music Library clause (the user decided to proceed, below)

[Eleven Music Terms](https://elevenlabs.io/music-terms) (last updated 09 October 2026):

- 2.2: we keep the rights in Output "in accordance with your Underlying ElevenLabs Agreement".
- Exhibit A: Media Rights on every self-serve plan, Free to Business, cover "All online and offline commercial use
  permitted, except film, TV, radio, and Studio Games". Only Enterprise Music has no exclusions.
- 4.8(j): a Studio Game is "a video game or other interactive or playable experience made available to the public"
  that is monetised, Indie Games excluded. 4.8(c): an Indie Game has lifetime revenue under $500,000, from a
  developer with under $1,000,000 in game revenue in its last year. 4.7: a game that stops qualifying has 60 days
  to move to a plan that allows Studio Games. A free, non-monetised GPL game is not a Studio Game, so use in the
  game itself would be allowed on a paid plan.
- **The blocker**, 4.2: "You must not, directly or indirectly, use Output to compile, create, or contribute to a
  Music Library". 4.8(f) defines a Music Library as "any collection of Output, in whole or in part, made available to
  third parties for those third parties to use", paid or not. Committing tracks to a GPL repository, or shipping them
  under a licence that lets others reuse them, makes them available for third parties to use. The Prohibited Use
  Policy's "more permissive terms" clause applies as well.
- When checked, the key had no Music permission; the user enabled it afterwards.
- 2.1: prompts must not name artists, songs or record labels.

Read strictly, Eleven Music tracks cannot be released under the repository's licence. The user, told so, decided to
generate and commit Hesper's music with Eleven Music (below); the tool runs music jobs only when the job file says
`music: true`.

**Alternatives we could own outright** (kept for reference):

1. **ACE-Step 1.5** (open-weights music model, MIT licence; its model card says the generated music may be used
   commercially). It runs locally (8 GB GPU here), makes 2-3 minute tracks and can be steered toward instrumental
   ambient. It is the best fit; the model card's licence and training-data claims should be confirmed before use.
2. **Stable Audio Open 1.0** (Stability AI Community License: free under $1M revenue, outputs owned by the user).
   Clips are at most 47 s and suit textures better than full tracks; a loop could be built from several.
3. A human-made CC0/CC-BY score (OpenGameArt, Free Music Archive CC0), or the user's own composition.

Music would install as `worlds/hesper/music/<N>.mp3`, picked by the map_stats row's Redbook `Track` column
(`GameAudioSystem::loadBackgroundMusicTrack` reads `Music/<N>.mp3`). Watch the merged-root check: a world file with
the same logical name as an engine file but different content fails validation.

## The user's decision on committing (2026-10-23)

The user decided that the ElevenLabs sound effects and speech are used in Hesper and committed to the repository,
having read the Prohibited Use Policy note above.
On the same day, told of the music terms (section 4.2, "Music Library"), the user enabled Music Generation on the key
and decided to generate Hesper's music with ElevenLabs and commit it as well.
