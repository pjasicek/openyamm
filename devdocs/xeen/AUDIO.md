# Xeen: audio

Owner: lane AU ([lanes/AU.md](lanes/AU.md)). The world's own sounds, generated with ElevenLabs sound effects through
`tools/run_elevenlabs.sh` ([tools/audio/README.md](../../tools/audio/README.md)), the way Hesper did
(`design/kreegan_world/AUDIO.md`). Music stays MM6–MM8 tracks by number ([MUSIC.md](MUSIC.md), ROADMAP Q9).

- Jobs, prompts, picks and the reasons: `level_generation/sounds/xeen_20261120/` (`jobs.yml`, `picks.yml`,
  `install.yml`, `ledger.json`). Listen on the local review page `level_generation/sounds/xeen_20261120/review/index.html`
  (open from disk); spectrogram sheets and per-take measurements in `review/sheets/` and `review/analysis.txt`.
- Installed by `level_generation/sounds/xeen_20261120/install.py`: the WAVs in `assets_dev/worlds/xeen/audio/xeen/`,
  the rows in `assets_dev/worlds/xeen/audio/sounds.txt` (not in `data_tables/`, which `build_world.py` empties of
  files it does not write).

## How a Xeen sound reaches the game

| Hook | How it plays | Who sets it |
| --- | --- | --- |
| Monster descriptor columns | `AttackSoundId`, `DeathSoundId`, `WinceSoundId`, `AwareSoundId` (played as the idle fidget) are sound ids from `sounds.txt`; a ranged monster's shot plays its attack sound | A2: monsters.yml names a family's (and a tier's) sound set from the table below; gen_monsters writes the columns |
| Map and world Lua | `evt.PlaySoundName("xeen_gong", x, y, z)` (positional; without coordinates non-positional) | the owner of the script: map lanes in their wiring, A3 in `xeen_common.lua` / quests |
| Placed ambient sounds | a BLV scene's `ambient_sounds` (`sound: xeen_amb_mine`, radius, volume, loop, wait; [AMBIENT_SOUNDS](../AMBIENT_SOUNDS.md)) | map lanes, in their briefs' `sounds:` list |
| Outdoor beds | an ODM scene's `ambient_sounds` (E9, merge point 20), from sketch.yml `sounds` (see "Outdoor beds" below for the lists) | map lanes paste AU's lists |

A sound is found by its file name anywhere in the merged audio tree (`game/audio/SoundCatalog.cpp`), so every Xeen
name starts with `xeen_` and is unique across all worlds (`install.py` refuses a clash).

### Sound ids: 62000–63999, not 70000–79999

ROADMAP §4 gave sounds 70000–79999, but a monster descriptor's sound columns are 16-bit
(`game/tables/MonsterTable.h`: `soundSampleIds`, `attackSoundId`; also `OutdoorWorldRuntime.h`'s audio request), so a
row id of 70000 would wrap to 4464, an engine sound. MM9 (50000–59999) and the Hesper stage (60000–60999) stay under
65536 for the same reason. Xeen's rows use **62000–63999** (free: the engine's ids end at 46801, MM9's at 58523).
The world.yml change is the orchestrator's (request below); `install.yml` holds the ids:

| Ids | What |
| --- | --- |
| 62000–62499 | monster sets: a family block of ten, attack, death, wince, fidget at +0..3 (the descriptor's column order), the pitched tier set at +4..7 |
| 62500–62799 | world and event sounds |
| 62800–62999 | ambience beds |
| 63000–63099 | voice lines (D-38), a block of ten per speaker |
| 63100–63999 | boss sets (a block of ten: the boss's set at +0..3, a second boss's pitched set at +4..7), later batches |

## Survey: what the shipped sounds do not cover

The families borrow a shipped descriptor's sounds (monsters.yml `sprites` / `stand_in`). Measured on the generated
`monster_descriptors.txt` (2026-11-20):

- **New creatures on unrelated sounds:** toads on the salamander man, witches on MM7's moon cleric (no fidget), sprites on
  the will-o'-wisp, swarms on the dragonfly with a bloodsucker fidget, Flying Feet / Guardian / Carnage Hand on a
  **human mercenary**, moles on the rat, sorceresses on the druidess.
- **Borrowed sounds that do not fit:** orcs on MM6's small goblin (no fidget), golems on the gog (no fidget), madmen on
  a peasant (no wince, no fidget), harpies on a mix (cockatrice, peasant woman, bat), the iguanasaurs on a crystal
  dragon, the sand worms on the behemoth.
- **Fine as they are** (kept): goblins, gremlins, dwarves, ogres, trolls, cyclops, minotaurs, barbarians, thieves, monks,
  archers, knights, wizards, clerics, skeletons, zombies, ghosts, liches, vampires, bats, spiders, oozes, rats, ratmen,
  wolves, werewolves, snakes, serpentmen, gargoyles, rocs, eyes, robots, elementals, demons, dragons, hydras, bone
  dragons.
- **Risk:** the pyramid mummies borrow MM9's sound ids (50546–50553), which exist only while the MM9 package is
  installed; a release without MM9 plays them silent. A Xeen mummy set is in batch 2.
- **Events:** every map uses shipped sounds by name or id today (XD-03's gong is MM6's `6gong`, 42682). Nothing exists
  for the mirror network, the travel pyramids, the sand-falls, the Sphinx, the coffin lid, a reservoir draining, lifts,
  winches, fortune tellers, the Lifeforce Spring, wells, obelisks, gates, burning forts or Kalindra's phase.
- **Ambience:** dungeons use the shipped drips, water loops, `whistling wind` and `humming`. Missing: a sewer bed, a mine
  bed, a wizard-tower bed, a sky bed under the gusts, and every outdoor bed (no ODM emitters yet).

## Batch 1 (2026-11-20)

Every sound below is **installed** (WAV and row); the hooks wired so far are listed under "Hooks checked in the game" and
the Requests. Credits: 14 718
charged by the API's reports (53 348 committed at the docs rate of 40 a second), 284 requests: monsters 2 427, events
3 579, beds 8 712 (the long loops cost most). The picks' reasons are in `picks.yml` (`listening`), drawn from
`listening.yml` by `merge_listening.py`.

### (a) Monster sets

One generated set per family (attack, wince, death, idle fidget); a bigger tier or boss is the same set pitched down
(tape: lower and slower), a `derived` job with no new generation. Loudness as Hesper's monster voices: attack, wince,
death to a loudest 100 ms of -9 dBFS (the heavy bodies -8 with a low shelf), fidgets -11, peaks -1 dBFS.

| Family (monster ids) | Set (attack, death, wince, fidget) | Ids | Tiers on the set | Tiers on the pitched set (ids +4..7) | Credits charged |
| --- | --- | --- | --- | --- | --: |
| Toads (11450-11452) | `xeen_toad_attack`, `_death`, `_wince`, `_fidget` | 62000-62003 | A Giant Toad, B Bog Toad | C Swamp Toad (-2) | 159 |
| Witches (11160-11163), coven (11170-11172) | `xeen_witch_attack`, `_death`, `_wince`, `_fidget` | 62010-62013 | A Wicked Witch, B Witch; coven A, B | C Elder Witch, Head Witch, Coven Mother (-1.5) | 189 |
| Sprites (11530-11538), dark sprites (11534-11536) | `xeen_sprite_attack`, `_death`, `_wince`, `_fidget` | 62020-62023 | Medusa, Killer, Gorgon and Elder Gorgon Sprites | Sprite Queen (both), Sharla (-2): `xeen_sprite_queen_*` || 144; F37 re-takes of attack, death, fidget 126 |
| Swarms (11340-11342) | `xeen_swarm_attack`, `_death`, `_wince`, `_fidget` | 62030-62033 | B Insect Swarm, C Stingers | A Doom Bug: its own generated set `xeen_doombug_*` (62034-62037, a giant cricket; F37, 2026-11-23: no longer the swarm set -3) | 162; F37 re-takes: swarm 162, Doom Bug 249 |
| Flying Feet (11600) | `xeen_feet_attack`, `_death`, `_wince`, `_fidget` | 62040-62043 | A | — | 153 |
| Guardian (11601) | `xeen_guardian_attack`, `_death`, `_wince`, `_fidget` | 62050-62053 | B (its lightning shot plays the attack) | — | 165 |
| Carnage Hand (11602) | `xeen_hand_attack`, `_death`, `_wince`, `_fidget` | 62060-62063 | C | — | 159 |
| Moles (11430-11432) | `xeen_mole_attack`, `_death`, `_wince`, `_fidget` | 62070-62073 | A Tiger Mole, B Rock Mole | C Tunnel Mole (-2) | 138 |
| Sorceresses (11180-11185) | `xeen_sorceress_attack`, `_death`, `_wince`, `_fidget` | 62080-62083 | A, B, D Apprentice, Head Sorceress | C Grand Sorceress, Morgana (-1) | 147 |
| Orcs (11030-11033), warband (11040-11043) | `xeen_orc_attack`, `_death`, `_wince`, `_fidget` | 62090-62093 | A Orc, B Orc Archer; Orc Elite, Snog, Orc Shaman | C Orc Guard, Drum-Master, Orc Captain, Shaalth (-1.5) | 144 |
| Golems (11580-11584), elemental golems (11590-11594) | `xeen_golem_attack`, `_death`, `_wince`, `_fidget` | 62100-62103 | Wood, Stone; all five elemental golems | Iron, Diamond, Onyx (-2) | 171 |
| Madmen (11230-11232) | `xeen_madman_attack`, `_death`, `_wince`, `_fidget` | 62110-62113 | all three | — | 168 |
| Harpies (11520-11522) | `xeen_harpy_attack`, `_death`, `_wince`, `_fidget` | 62120-62123 | A Harpy, B Harpy Hag | C Harpy Queen (-1.5) | 159 |
| Iguanasaurs (11510-11512) | `xeen_lizard_attack`, `_death`, `_wince`, `_fidget` | 62130-62133 | A, B | C Ancient Iguanasaurus (-2) | 165 |
| Sand burrowers (11440-11442) | `xeen_worm_attack`, `_death`, `_wince`, `_fidget` | 62140-62143 | A Sand Worm, B Armadillo (for now) | C Great Worm (-2) | 204 |

### (b) World and event sounds

| Sound (id) | Use | Pick and why | Credits charged |
| --- | --- | --- | --: |
| `xeen_gong` (62500) | the great gongs: XD-03 (now the shipped 6gong), DD-06, X5's ghost-wave gongs (Q-C6) | v1.wav: v1 over the score: one clean strike, clear partials and a smooth natural decay, unclipped and only 3 dB limited; v2 (the score's) has a notch and a restart in its tail and needed 10 dB of limiting, v3 and v4 beat (8-10 events), v5 clipped. | 330 |
| `xeen_gong_low` (62501) | the larger gong (the second of a pair, or a deeper hall), the gong three semitones down | v1.wav: derived: -3 semitones | 0 |
| `xeen_mirror_touch` (62502) | a town mirror touched (the mirror network: Xeen.useMirror, first touch and the 'Where to?' prompt) | v2.wav: Kept v2: a chime that wakes and rings away; v1 swells and stops dead. | 88 |
| `xeen_mirror_travel` (62503) | the party steps through a mirror (before the move) | v5.wav: Kept v5: a glassy rise into a rich band and a long fade, the most even of five. | 140 |
| `xeen_pyramid_travel` (62504) | an Ancient travel pyramid sends the party to the other face | v4.wav: v4 over the score: a rising hum that breaks into a burst at 40 % and fades, the asked shape; v2 (the score's) is a flat drone with no burst. v4 clipped 938 samples in the download (declipped): listen first. | 152 |
| `xeen_sandfall_loop` (62505) | a sand-fall over the rim (X6's five xeen_sandfall, D-31): placed, looping, positional | v1.wav: Kept v1: the evenest hiss (0.4 dB spread over 2 s windows), 75 % above 8 kHz like falling sand. | 396 |
| `xeen_sphinx_stir` (62506) | the Sphinx (X6, XD-15): the stone colossus stirs at the riddle and the door opens | v3.wav: Kept v3: grinding with separate stone knocks, the most power and least limited. | 176 |
| `xeen_coffin_lid` (62507) | Count Draco's coffin on Nightshadow's square (X3, the lid and stair into XD-24, D-11.3); crypt coffins | v2.wav: v2 over the score: the scrape, a short gap, then the lid's thud and a 2.4 s decay; v1 and v3 scrape and stop dead with no drop. | 99 |
| `xeen_reservoir_drain` (62508) | XD-10's plug pulled: the reservoir drains (before the bed is revealed) | v1.wav: Kept v1: gurgles, then the rushing drain swelling and fading (4 s decay), unclipped. | 264 |
| `xeen_lift` (62509) | lifts: Ellinger's tower lift (DD-02) and any chain lift or moving platform | v1.wav: Kept v1: chain rattle at an even level with the stop; all three close. | 132 |
| `xeen_winch` (62510) | winches: XD-26's hoist and drawn ladder (D-17), XD-21's plank bridge, XD-12's works gate | v3.wav: Kept v3: steady ratchet clicks and rope creak, nearly clean (4 clipped against 25 and 180). | 99 |
| `xeen_fortune` (62511) | fortune tellers and seers (the Darkside palm reader, the gypsies): a reading | v1.wav: Kept v1: a shimmering swell with chimes and a low hum under it. | 99 |
| `xeen_spring_drink` (62512) | the Lifeforce Spring (X3, +2 Endurance) and the other fountains and shrines that grant a lasting gift | v3.wav: v3 over the score: bubbling, then a rising glissando shimmer and bell partials, exactly the asked order; v2 (the score's) is bubbling and a hiss. | 112 |
| `xeen_well_drink` (62513) | wells: 'The water is cool and refreshing.' (every well's click) | v2.wav: Kept v2: bucket splash, pour and a gulp. | 66 |
| `xeen_obelisk` (62514) | the thirteen obelisks (A3's obelisks.<map>): an obelisk gives its word | v4.wav: Kept v4 of the second prompt: a swelling hum and a bell tone at 600-2 500 Hz (18 %), the clearest tone. The first prompt's four takes were sub-bass alone and are superseded. | 264 |
| `xeen_yard_gate` (62515) | the Warzone coach yard gate (X6, D-8.1); other heavy wooden yard and fort gates | v2.wav: Kept v2: creak, latch, several knocks and the thud; the least clipped (11). | 84 |
| `xeen_fire_ignite` (62516) | lairs and forts set alight (X1's orc outposts' drums, D2's burned ogre fort, the encampments): one-shot; the shipped 'raging fire loop' keeps burning | v2.wav: Kept v2: the whoosh, then a roar that holds; v1 clipped 1 659 samples. | 132 |
| `xeen_phase_shift` (62517) | Castle Kalindra out of phase (DD-03 stages, D1's castle hill): the castle flickers or a stage changes | v3.wav: v3 over the score: shimmering partials bending in pitch over a rise and fall, the only take with audible glassy tones (60 % at 600-2 500 Hz); v4 (the score's) is a flat low hum. | 275 |
| `xeen_phase_loop` (62518) | Castle Kalindra's phase shimmer, placed and looping where the castle stands out of phase | v1.wav: Kept v1: steady warbling partials; its level drifts slowly (14 dB spread over 2 s windows), v2 dips sharply. | 495 |
| `xeen_sky_gust` (62519) | the sky maps (X8, X9): a strong gust, placed with a wait over the shipped 'whistling wind' | v3.wav: Kept v3: a long rise and fall of wind, the fullest. | 176 |

### (c) Ambience beds

Loops, mono (placed, positional), levelled to -20 dBFS RMS with a crossfaded seam. The indoor and sky beds play as
placed ambient sounds; the outdoor beds' placements are under "Outdoor beds" below.

| Sound (id) | Use | Pick and why | Credits charged |
| --- | --- | --- | --: |
| `xeen_amb_sewer` (62800) | sewers (DD-01 Castleview Sewer, DD-18 Sandcaster Sewer) | v3.wav: Kept v3: trickles and drips, the evenest (2.2 dB) and brightest. | 792 |
| `xeen_amb_mine` (62801) | mines (XD-02, XD-03, DD-10 Gemstone Mines) | v2.wav: Kept v2 of the second prompt: drips and knocks in the mid band, 6.7 dB spread; the first prompt's three takes were sub-bass rumble alone and are superseded. | 1584 |
| `xeen_amb_tower` (62802) | wizards' towers (XD-11 Tower of High Magic, XD-12 Darzog's Tower, DD-02 Ellinger's Tower, the towers of Mok) | v1.wav: Kept v1 of the second prompt: chimes and sparkle with the evenest seam (v2 and v3 jump 0.09 at the wrap); bright, so place it quiet (volume 0.3-0.4). The first prompt's three takes were sub-bass alone. | 1584 |
| `xeen_amb_sky` (62803) | the sky maps (X8 Cloudreach, X9 Clouds of Xeen): the open-air bed under the gusts | v2.wav: v2 over the score: gusts rising and falling with a whistling band, as asked, and a clean wrap; v3 (the score's) is an even rush with no gusts and a 0.026 jump at the wrap. | 792 |
| `xeen_amb_meadow` (62804) | Cloudside meadows by day (X1, X2; X5's pocket, low): placed by "Outdoor beds" | v1.wav: Kept v1: breeze with birdsong at the top of the band; v2 is a steady insect band over sub rumble. | 660 |
| `xeen_amb_lagoon` (62805) | X3's wetlands, X1's Toad Marsh, X2's lake shore, D3's Venom Fen, D4's lake shores: placed by "Outdoor beds" | v1.wav: v1 over the score: frogs and a steady insect layer, the more even (7.7 against 10.1 dB); v2 is frog croaks alone. | 660 |
| `xeen_amb_tundra` (62806) | X5 Winterkill Tundra; X4's Gargoyle range, D4's snow uplands, D5's highlands and D6's passes (low): placed by "Outdoor beds" | v1.wav: v1 over the score: a howling wind band at 150-300 Hz that swells and falls; v2 is sub rumble and hiss. | 660 |
| `xeen_amb_savannah` (62807) | X4 Burlock Savannah's plains by day: placed by "Outdoor beds" | v1.wav: Kept v1: an even cicada drone with wind; v2 has a dropout at 60 %. | 660 |
| `xeen_amb_desert` (62808) | X6 Desert of the Sphinx, D3's desert edge and Sandcaster, D5's deserts, D6's ash wind (session 4): placed by "Outdoor beds" | v2.wav of the second prompt (session 3), high-passed at 150 Hz at install (`bed_highpass_hz`, install.py): both prompts' takes are 77-99 % below 150 Hz (wind rumble); after the high-pass and re-levelling v2 keeps the most sand hiss (23 % above 8 kHz) with a 10.5 dB gust spread. The first prompt's v1 is superseded. | 660 + session 3 |
| `xeen_amb_darkside` (62809) | Darkside's surface under the amber, failing sun (D1-D4): placed by "Outdoor beds" | v2.wav of the second prompt (session 3): a steady cricket chorus at 2.5-8 kHz over a breeze with one distant caw, the evenest (3.9 dB); the first prompt's takes had nothing above 600 Hz (a drone) and are superseded. | 660 + session 3 |

## Outdoor beds (E9; session 4: `pan: false`, ready to re-paste)

E9 is live since merge point 20: an outdoor map's sketch.yml `sounds` become its scene's `ambient_sounds`
(openyamm-studio/README.md "Outdoor sounds"). The lists below are the whole `sounds:` block of each map; the map lanes
own the sketches and paste them (X6's block replaces its one sand-fall line, which it keeps). Written by
`level_generation/sounds/xeen_20261120/beds.py` from `beds.yml` (the fields of each map: a bed over some of the
sketch's districts, a hex lattice of emitters, plus the map's point sounds as `extra`); the same blocks are the files
`level_generation/sounds/xeen_20261120/review/beds/<map>.yml`, `review/beds/<map>.png` draws the circles on the
minimap (on the districts for a map not installed yet), `review/beds/coverage.txt` the evenness. Sound names without
`.wav` resolve (the studio and the game look a name up with and without it).

**Session 4 (D-48, merge point 21):** every bed emitter carries `pan: false`; the point sounds (X6's sand-falls, D1's
`sound:kalindra_shimmer`, D5's Barrier hum, D6's lava and lava falls, Castle Alamar's hum) do not and keep panning. The
positions of X1-X6 and D1-D4 are unchanged from session 3 (the sketches' districts are the same; only `, pan: false`
was added), so a lane can re-paste the whole block. D5 and D6 are new (D-49, below D4).

**Layout.** The engine fades a placed sound linearly in amplitude from its inner to its outer radius
(`engine/AudioSystem.cpp`). Emitters stand on a hex lattice about one outer radius apart with the inner radius at about
0.4 of it (map-wide beds 24-28 cells apart, 12 000-15 000 / 4 800-6 000; zone beds 15-24 cells, 9 000-11 000 /
3 500-4 500), so a field's level stays within 3 dB of one emitter heard at full over 58-99 % of its cells (80 % or more
on all but D4's shore and Darkside fields and X4's range wind, whose fields are thin strips; power sum; the misses are
the field's edges, where the next bed takes over). Neighbouring beds overlap at their edges: a crossfade, not a seam.

**Levels.** The beds are levelled to -20 dBFS RMS where their peaks allow (the lagoon -27.6 and the Darkside -23.7:
frogs and crickets are peaks; the desert -21.3). Volumes 0.25-0.45 (lagoon 0.5-0.7) put a bed at about -28 to -33 dBFS,
MM9's own outdoor beds' range (its wind and waves at -24 to -35 dBFS after their scene volumes).
Since D-117 (2026-11-23, players found Vertigo's birds too loud) the three all-treble beds, meadow (birds), savannah
(cicadas) and night (crickets), are cut 6 dB at install (`jobs.yml` `gain_db`, `install.py` `apply_gain`) to about
-27.5 dBFS RMS (-23.9, -22.7, -22.7 LUFS): treble reads louder than its RMS, and two or more emitters overlap almost
everywhere, so heard in X1 the meadow sat about 8 dB under the music at the default sliders. Their scene volumes are
unchanged. A level change goes in `gain_db` and a reinstall, not in the maps.

**Day and night** (Xeen's day 06:00-20:00, world.yml has no `ambientSounds`): the meadow (birdsong) and savannah
(cicadas) beds are `day_only`. Since session 5 their fields carry a night twin on the same lattice:
`xeen_amb_night` (crickets, 62819), `night_only`, volume 0.3 (X5's pocket 0.22): the `bed_night_*` and
`bed_pocket_night_*` lines in X1, X2, X4 and X5's blocks below (the day lines are unchanged).

**Known limits** (since merge point 21, D-48):
- A bed emitter with `pan: false` is heard centred, by distance only (`rules.pan && source.pan` in
  `game/audio/WorldAmbientSounds.cpp`): no left or right, also not at a bed's edge. A point sound pans by direction
  (`positionalAudioPan`), full left or right when side-on, as before.
- A looping sound without a `wait` starts at a random frame of its clip, so the emitters of one bed that come into
  reach together no longer play in step (session 3's +6 dB build-up is gone). One-shots and sounds with a `wait` start
  at the beginning, as before.
- No occlusion: a bed or a lava fall is heard through a hill or a wall within its radius (as MM9).
- `day_only` beds hand over to their `night_only` twins (session 5) at the world's day hours (06:00-20:00).
- `OPENYAMM_AUDIO_TRACE` logs a start (`play source=assetInstance`, path, position) but not the pan or the start
  frame: a game check shows that the scene accepts the word and the sound starts, not the balance.

**Checked in the game:**
- 2026-11-20 (session 3, merge point 20): X6 built from a copy of its L4 with the desert block; standing at cell
  [32, 80], the three desert emitters within 15 000 and the sand-fall start; the one at [41, 49], 16 500 away, does not.
- 2026-11-21 (session 4, `build-xeen` of merge point 21, minimised desktop runs with `OPENYAMM_AUDIO_TRACE=1`, logs in
  `level_generation/sounds/xeen_20261120/work/au_s4_*_game.log`): the pasted (panned) X6 from assets_dev at cell
  [32, 80]: the same three desert emitters and the sand-fall start (`au_s4_x6_dev`). D1's installed scene with
  `pan: false` added to its twelve bed entries, read through `--extra-mount` in front of assets_dev (`au_s4_d1_pan`):
  the map loads, four Darkside emitters and Kalindra's shimmer start; the same file with a misspelt key refuses the
  map ("an ambient_sounds entry has an unknown key pann"), so the run read the edited file and the scene parser takes
  `pan`. The seven new sounds of session 4 placed in the same scene all start (`au_s4_new_names`).

### X1 (A5)

Meadow by day over the land; the Toad Marsh on the lagoon bed day and night; the dead forest kept silent (the menace of the brief).

```yaml
sounds:
  - {id: sound:bed_meadow_1, at: [27, 25], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_2, at: [55, 25], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_3, at: [83, 25], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_4, at: [41, 49], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_5, at: [69, 49], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_6, at: [97, 49], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_7, at: [27, 73.5], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_8, at: [55, 73.5], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_night_1, at: [27, 25], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_2, at: [55, 25], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_3, at: [83, 25], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_4, at: [41, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_5, at: [69, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_6, at: [97, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_7, at: [27, 73.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_8, at: [55, 73.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_marsh_1, at: [68, 70], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_marsh_2, at: [86, 70], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_marsh_3, at: [77, 85.5], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_marsh_4, at: [95, 85.5], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
```

### X2 (A5)

Meadow by day; Lake Darzog's shore and island on the lagoon bed; the gloomy Dark End kept silent.

```yaml
sounds:
  - {id: sound:bed_meadow_1, at: [27, 25], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_2, at: [55, 25], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_3, at: [83, 25], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_4, at: [69, 49], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_5, at: [97, 49], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_6, at: [55, 73.5], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_7, at: [83, 73.5], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_8, at: [41, 97.5], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_meadow_9, at: [97, 97.5], sound: xeen_amb_meadow, radius: 15000, inner_radius: 6000, volume: 0.35, day_only: true, pan: false}
  - {id: sound:bed_night_1, at: [27, 25], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_2, at: [55, 25], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_3, at: [83, 25], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_4, at: [69, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_5, at: [97, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_6, at: [55, 73.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_7, at: [83, 73.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_8, at: [41, 97.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_9, at: [97, 97.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_lake_1, at: [29, 45], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_lake_2, at: [47, 45], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_lake_3, at: [38, 60.5], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_lake_4, at: [29, 76], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
  - {id: sound:bed_lake_5, at: [47, 76], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.6, pan: false}
```

### X3 (A5)

The lagoon bed over the reedbeds, fens, drowned shore, bogwood, gloomwood, the tower islet and the west landing; Nightshadow, the crow hills and the east ridge kept quiet (the brief: "Nightshadow silent in its fog").

```yaml
sounds:
  - {id: sound:bed_lagoon_1, at: [25, 23], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_2, at: [38, 45.5], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_3, at: [64, 45.5], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_4, at: [25, 68], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_5, at: [51, 68], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_6, at: [38, 90.5], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_7, at: [64, 90.5], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
  - {id: sound:bed_lagoon_8, at: [90, 90.5], sound: xeen_amb_lagoon, radius: 14000, inner_radius: 5500, volume: 0.7, pan: false}
```

### X4 (A5)

Savannah cicadas by day over the plains; the Gargoyle range on the tundra wind, low.

```yaml
sounds:
  - {id: sound:bed_savannah_1, at: [27, 49], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_2, at: [55, 49], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_3, at: [83, 49], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_4, at: [41, 73], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_5, at: [69, 73], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_6, at: [97, 73], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_7, at: [27, 97.5], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_8, at: [55, 97.5], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_savannah_9, at: [83, 97.5], sound: xeen_amb_savannah, radius: 15000, inner_radius: 6000, volume: 0.3, day_only: true, pan: false}
  - {id: sound:bed_night_1, at: [27, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_2, at: [55, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_3, at: [83, 49], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_4, at: [41, 73], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_5, at: [69, 73], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_6, at: [97, 73], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_7, at: [27, 97.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_8, at: [55, 97.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_night_9, at: [83, 97.5], sound: xeen_amb_night, radius: 15000, inner_radius: 6000, volume: 0.3, night_only: true, pan: false}
  - {id: sound:bed_range_wind_1, at: [23, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_2, at: [47, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_3, at: [71, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_4, at: [95, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
```

### X5 (A6)

The tundra wind over the west (steppe, snowfields, giants, glacier, troll forest, Winterkill); the softer pocket east of the Frostspine on the meadow bed, low, by day.

```yaml
sounds:
  - {id: sound:bed_tundra_1, at: [25, 23], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_2, at: [53, 23], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_3, at: [81, 23], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_4, at: [39, 47], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_5, at: [67, 47], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_6, at: [25, 71.5], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_7, at: [53, 71.5], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_8, at: [81, 71.5], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_9, at: [39, 95.5], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_tundra_10, at: [67, 95.5], sound: xeen_amb_tundra, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_pocket_1, at: [96, 27], sound: xeen_amb_meadow, radius: 10000, inner_radius: 4000, volume: 0.25, day_only: true, pan: false}
  - {id: sound:bed_pocket_2, at: [107, 46], sound: xeen_amb_meadow, radius: 10000, inner_radius: 4000, volume: 0.25, day_only: true, pan: false}
  - {id: sound:bed_pocket_3, at: [96, 65], sound: xeen_amb_meadow, radius: 10000, inner_radius: 4000, volume: 0.25, day_only: true, pan: false}
  - {id: sound:bed_pocket_4, at: [107, 84], sound: xeen_amb_meadow, radius: 10000, inner_radius: 4000, volume: 0.25, day_only: true, pan: false}
  - {id: sound:bed_pocket_5, at: [96, 103], sound: xeen_amb_meadow, radius: 10000, inner_radius: 4000, volume: 0.25, day_only: true, pan: false}
  - {id: sound:bed_pocket_night_1, at: [96, 27], sound: xeen_amb_night, radius: 10000, inner_radius: 4000, volume: 0.22, night_only: true, pan: false}
  - {id: sound:bed_pocket_night_2, at: [107, 46], sound: xeen_amb_night, radius: 10000, inner_radius: 4000, volume: 0.22, night_only: true, pan: false}
  - {id: sound:bed_pocket_night_3, at: [96, 65], sound: xeen_amb_night, radius: 10000, inner_radius: 4000, volume: 0.22, night_only: true, pan: false}
  - {id: sound:bed_pocket_night_4, at: [107, 84], sound: xeen_amb_night, radius: 10000, inner_radius: 4000, volume: 0.22, night_only: true, pan: false}
  - {id: sound:bed_pocket_night_5, at: [96, 103], sound: xeen_amb_night, radius: 10000, inner_radius: 4000, volume: 0.22, night_only: true, pan: false}
```

### X6 (A5)

The desert bed everywhere but the oasis and Sphinx Wells; A5's sand-fall entry kept as it is (checked in the game, below).

```yaml
sounds:
  - {id: sound:bed_desert_1, at: [27, 25], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_2, at: [55, 25], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_3, at: [83, 25], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_4, at: [41, 49], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_5, at: [69, 49], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_6, at: [97, 49], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_7, at: [27, 73.5], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_8, at: [55, 73.5], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_9, at: [83, 73.5], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_10, at: [41, 97.5], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_11, at: [69, 97.5], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:bed_desert_12, at: [97, 97.5], sound: xeen_amb_desert, radius: 15000, inner_radius: 6000, volume: 0.4, pan: false}
  - {id: sound:sandfalls, at: [28.5, 84], sound: xeen_sandfall_loop, radius: 4500, inner_radius: 1800, volume: 0.6}
```

### X7 (A5, session 5)

New in session 5, from A5's installed sketch: the volcano bed (`xeen_amb_volcano`, new) over the hot north strip
(the volcano's mouth, the crater, the lava basin and island, the ash flats, the Fire Corner, the crags, Firestone);
the cold wind (`xeen_amb_tundra`, low) over the Red Dwarf range, the south slopes, the Gap, the watch, the orc
outpost and Sablewing's cave. The lava falls' point sound is A5's own line (kept). Day and night alike.

```yaml
sounds:
  - {id: sound:bed_volcano_1, at: [36, 42], sound: xeen_amb_volcano, radius: 11000, inner_radius: 4500, volume: 0.4, pan: false}
  - {id: sound:bed_volcano_2, at: [58, 42], sound: xeen_amb_volcano, radius: 11000, inner_radius: 4500, volume: 0.4, pan: false}
  - {id: sound:bed_volcano_3, at: [80, 42], sound: xeen_amb_volcano, radius: 11000, inner_radius: 4500, volume: 0.4, pan: false}
  - {id: sound:bed_volcano_4, at: [102, 42], sound: xeen_amb_volcano, radius: 11000, inner_radius: 4500, volume: 0.4, pan: false}
  - {id: sound:bed_range_wind_1, at: [23, 68.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_2, at: [47, 68.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_3, at: [71, 68.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_4, at: [95, 68.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_5, at: [35, 89.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_6, at: [59, 89.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_range_wind_7, at: [83, 89.5], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:lavafalls, at: [73.5, 29], sound: xeen_lavafall_loop, radius: 4500, inner_radius: 1800, volume: 0.6}
```

### D1 (A6)

The Darkside bed over the whole map; `sound:kalindra_shimmer` (`xeen_phase_loop`) at the castle hill [39, 70] (the cell of event 265's phase sound): A6 may make it `on: false` and switch it off (`AmbientSound<n>` 2) once the castle is wholly back in phase.

```yaml
sounds:
  - {id: sound:bed_darkside_1, at: [27, 25], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_2, at: [55, 25], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_3, at: [83, 25], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_4, at: [41, 49], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_5, at: [69, 49], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_6, at: [97, 49], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_7, at: [27, 73.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_8, at: [55, 73.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_9, at: [83, 73.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_10, at: [41, 97.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_11, at: [69, 97.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_12, at: [97, 97.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:kalindra_shimmer, at: [39, 70], sound: xeen_phase_loop, radius: 3500, inner_radius: 1200, volume: 0.35}
```

### D2 (A6)

The Darkside bed over the whole map.

```yaml
sounds:
  - {id: sound:bed_darkside_1, at: [27, 25], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_2, at: [55, 25], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_3, at: [41, 49], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_4, at: [69, 49], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_5, at: [97, 49], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_6, at: [27, 73.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_7, at: [55, 73.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_8, at: [83, 73.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_9, at: [41, 97.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_10, at: [69, 97.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_11, at: [97, 97.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
```

### D3 (A5)

The desert bed over the desert edge and Sandcaster; the lagoon bed on the Venom Fen; the Darkside bed elsewhere.

```yaml
sounds:
  - {id: sound:bed_desert_1, at: [67, 21], sound: xeen_amb_desert, radius: 11000, inner_radius: 4500, volume: 0.3, pan: false}
  - {id: sound:bed_desert_2, at: [55, 28], sound: xeen_amb_desert, radius: 11000, inner_radius: 4500, volume: 0.3, pan: false}
  - {id: sound:bed_desert_3, at: [36, 25], sound: xeen_amb_desert, radius: 11000, inner_radius: 4500, volume: 0.3, pan: false}
  - {id: sound:bed_fen_1, at: [63, 57.5], sound: xeen_amb_lagoon, radius: 10000, inner_radius: 4000, volume: 0.6, pan: false}
  - {id: sound:bed_fen_2, at: [73, 75], sound: xeen_amb_lagoon, radius: 10000, inner_radius: 4000, volume: 0.6, pan: false}
  - {id: sound:bed_fen_3, at: [93, 75], sound: xeen_amb_lagoon, radius: 10000, inner_radius: 4000, volume: 0.6, pan: false}
  - {id: sound:bed_fen_4, at: [63, 92.5], sound: xeen_amb_lagoon, radius: 10000, inner_radius: 4000, volume: 0.6, pan: false}
  - {id: sound:bed_fen_5, at: [83, 92.5], sound: xeen_amb_lagoon, radius: 10000, inner_radius: 4000, volume: 0.6, pan: false}
  - {id: sound:bed_fen_6, at: [103, 92.5], sound: xeen_amb_lagoon, radius: 10000, inner_radius: 4000, volume: 0.6, pan: false}
  - {id: sound:bed_darkside_1, at: [27, 39], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_2, at: [55, 39], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_3, at: [83, 39], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_4, at: [41, 63], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_5, at: [97, 63], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_6, at: [27, 87.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_7, at: [55, 87.5], sound: xeen_amb_darkside, radius: 15000, inner_radius: 6000, volume: 0.45, pan: false}
```

### D4 (A6)

The tundra wind on the snow uplands and Magic Mountain; the lagoon bed on the lake shores and the isle (reeds); the Darkside bed elsewhere.

```yaml
sounds:
  - {id: sound:bed_snow_1, at: [25, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.35, pan: false}
  - {id: sound:bed_snow_2, at: [49, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.35, pan: false}
  - {id: sound:bed_snow_3, at: [73, 27], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.35, pan: false}
  - {id: sound:bed_snow_4, at: [37, 48], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.35, pan: false}
  - {id: sound:bed_snow_5, at: [61, 48], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.35, pan: false}
  - {id: sound:bed_shore_1, at: [59, 54], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.5, pan: false}
  - {id: sound:bed_shore_2, at: [77, 54], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.5, pan: false}
  - {id: sound:bed_shore_3, at: [50, 70], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.5, pan: false}
  - {id: sound:bed_shore_4, at: [68, 70], sound: xeen_amb_lagoon, radius: 9000, inner_radius: 3500, volume: 0.5, pan: false}
  - {id: sound:bed_darkside_1, at: [90, 45.5], sound: xeen_amb_darkside, radius: 14000, inner_radius: 5500, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_2, at: [25, 68], sound: xeen_amb_darkside, radius: 14000, inner_radius: 5500, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_3, at: [103, 68], sound: xeen_amb_darkside, radius: 14000, inner_radius: 5500, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_4, at: [38, 90.5], sound: xeen_amb_darkside, radius: 14000, inner_radius: 5500, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_5, at: [64, 90.5], sound: xeen_amb_darkside, radius: 14000, inner_radius: 5500, volume: 0.45, pan: false}
  - {id: sound:bed_darkside_6, at: [90, 90.5], sound: xeen_amb_darkside, radius: 14000, inner_radius: 5500, volume: 0.45, pan: false}
```

### D5 (A6, D-49)

New in session 4, from A6's L4 sketch (not installed yet; `review/beds/d5.png` draws on the districts). The desert bed
over the Desert of Doom, the Perishing Sands, the pass, the east valley and the south hills; the aspens' tremble
(`xeen_amb_aspen`, new) over the Quivering Forest; the cold wind (`xeen_amb_tundra`, low) on the highlands; the
Parabolic Barrier's faint hum (the shipped `humming`, as XD-19's generators) as six panned point sounds at every third
frame of its curtain (radius 3 000: heard near the frames, not between every pair); the People's fire at Gurodel's hold
(`campfire`: its `dec24` has no sound of its own; the dwarves' `dec24x` is a burned-out fire).

```yaml
sounds:
  - {id: sound:bed_desert_1, at: [25, 64.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_2, at: [49, 64.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_3, at: [73, 64.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_4, at: [97, 64.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_5, at: [37, 85.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_6, at: [61, 85.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_7, at: [85, 85.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_8, at: [25, 106], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_9, at: [49, 106], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_10, at: [73, 106], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_desert_11, at: [97, 106], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.4, pan: false}
  - {id: sound:bed_aspen_1, at: [25, 27], sound: xeen_amb_aspen, radius: 9000, inner_radius: 3500, volume: 0.45, pan: false}
  - {id: sound:bed_aspen_2, at: [40, 27], sound: xeen_amb_aspen, radius: 9000, inner_radius: 3500, volume: 0.45, pan: false}
  - {id: sound:bed_aspen_3, at: [32.5, 40], sound: xeen_amb_aspen, radius: 9000, inner_radius: 3500, volume: 0.45, pan: false}
  - {id: sound:bed_aspen_4, at: [47.5, 40], sound: xeen_amb_aspen, radius: 9000, inner_radius: 3500, volume: 0.45, pan: false}
  - {id: sound:bed_aspen_5, at: [25, 53], sound: xeen_amb_aspen, radius: 9000, inner_radius: 3500, volume: 0.45, pan: false}
  - {id: sound:bed_highland_1, at: [49, 25], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_highland_2, at: [73, 25], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_highland_3, at: [97, 25], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_highland_4, at: [61, 46], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:bed_highland_5, at: [85, 46], sound: xeen_amb_tundra, radius: 11000, inner_radius: 4500, volume: 0.25, pan: false}
  - {id: sound:barrier_hum_1, at: [48.7, 26.05], sound: humming, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:barrier_hum_2, at: [57.7, 31.2], sound: humming, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:barrier_hum_3, at: [66.7, 33.7], sound: humming, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:barrier_hum_4, at: [75.7, 34.2], sound: humming, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:barrier_hum_5, at: [84.7, 32.2], sound: humming, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:barrier_hum_6, at: [93.7, 28.2], sound: humming, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:hold_fire, at: [86.5, 46.5], sound: campfire, radius: 1500, inner_radius: 300, volume: 0.5}
```

### D6 (A6, D-49)

New in session 4, from A6's L4 sketch. The ash wind is the desert bed at a lower volume (0.3): the generated ash bed
came out as a tonal whistle over sub-bass and is not installed (Session 4 below). The cold wind on the southern peaks
and the passes; the Necropolis's own hushed bed (`xeen_amb_necropolis`, new; one emitter over the walled town, the ash
bed fades into it at the walls); the two lava falls over the rim (`xeen_lavafall_loop`, new, at `thing:lavafall_1`
and `_2`); the shipped `lava loop` bubbling round the moat, the pod lake and the Slag Run (point sounds, panned); and
Castle Alamar's hum between its gate pylons (`humming`): **switch it off after `m33.done`** (the ruin), for example by
`on` tied to the castle's state or a load hook that sets its `AmbientSound<key>` to 2 (A3 and A6).

```yaml
sounds:
  - {id: sound:bed_ash_1, at: [31, 27], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_2, at: [55, 27], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_3, at: [79, 27], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_4, at: [103, 27], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_5, at: [43, 48], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_6, at: [67, 48], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_7, at: [91, 48], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_8, at: [31, 68.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_9, at: [55, 68.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_10, at: [79, 68.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_11, at: [103, 68.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_12, at: [43, 89.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_ash_13, at: [67, 89.5], sound: xeen_amb_desert, radius: 12000, inner_radius: 4800, volume: 0.3, pan: false}
  - {id: sound:bed_pass_1, at: [104, 80], sound: xeen_amb_tundra, radius: 10000, inner_radius: 4000, volume: 0.25, pan: false}
  - {id: sound:bed_pass_2, at: [27, 99], sound: xeen_amb_tundra, radius: 10000, inner_radius: 4000, volume: 0.25, pan: false}
  - {id: sound:bed_pass_3, at: [49, 99], sound: xeen_amb_tundra, radius: 10000, inner_radius: 4000, volume: 0.25, pan: false}
  - {id: sound:bed_pass_4, at: [71, 99], sound: xeen_amb_tundra, radius: 10000, inner_radius: 4000, volume: 0.25, pan: false}
  - {id: sound:bed_pass_5, at: [93, 99], sound: xeen_amb_tundra, radius: 10000, inner_radius: 4000, volume: 0.25, pan: false}
  - {id: sound:bed_necropolis, at: [91, 82], sound: xeen_amb_necropolis, radius: 6500, inner_radius: 3500, volume: 0.4, pan: false}
  - {id: sound:lavafall_north, at: [44, 25], sound: xeen_lavafall_loop, radius: 4500, inner_radius: 1500, volume: 0.6}
  - {id: sound:lavafall_west, at: [25, 51], sound: xeen_lavafall_loop, radius: 4500, inner_radius: 1500, volume: 0.6}
  - {id: sound:lava_moat_w, at: [37, 46], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_moat_nw, at: [44, 36], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_moat_ne, at: [58, 36], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_moat_e, at: [63, 46], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_moat_sw, at: [41, 55], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_moat_se, at: [61, 55], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_lake_n, at: [70, 60], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_lake_e, at: [77, 64], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_lake_s, at: [68, 70], sound: lava loop, radius: 3500, inner_radius: 1000, volume: 0.4}
  - {id: sound:lava_slag_run, at: [31, 50], sound: lava loop, radius: 3000, inner_radius: 800, volume: 0.35}
  - {id: sound:alamar_hum, at: [50.8, 58], sound: humming, radius: 2500, inner_radius: 600, volume: 0.35}
```

X7's beds are in its own block (session 5); `xeen_lavafall_loop` (session 4) is made for X7's lava falls
too (D-40's shared preset): radius 4 500, inner 1 500, volume 0.6 at the foot of each fall.

## Batch 2 (2026-11-20, session 2)

Every sound below is **installed** (WAV and row, ids in `install.yml`). The monster and boss sets wait for A2 to name
them in monsters.yml (Requests). Same loudness rules as batch 1; heavy bodies (Xeen's Guard, armadillo, octopods,
swamp things, Lord Xeen, the dragons) -8 with a 30 Hz high-pass and a low shelf. Boss sets: five takes of the attack
and the death. Picks and reasons in `picks.yml` (`listening`), measured by `analyze.py` (`review/analysis.txt`,
`review/sheets/`). Credits: 2 930 charged, 10 556 committed (168 requests).

### (a) Monster sets, batch 2

| Family (monster ids) | Set (attack, death, wince, fidget) | Ids | Tiers on the set | Pitched set (ids +4..7) |
| --- | --- | --- | --- | --- |
| Pyramid mummies (11270-11272) | `xeen_mummy` | 62150-62153 | A Tomb Mummy, B Pyramid Guard | `xeen_mummy_c` (-2): C Royal Mummy |
| Xeen's Guard (11603) | `xeen_xguard` | 62160-62163 | D Xeen's Guard | — |
| Floating mages (11200-11202) | `xeen_mage` | 62170-62173 | A Mystic Mage, B Magic Mage | `xeen_mage_c` (-1.5): C Mega Mage |
| Coven (11170-11172) | `xeen_coven` (a chorus of witches; replaces the witches' set) | 62180-62183 | A, B Coven Witch | `xeen_coven_c` (-1.5): C Coven Mother |
| Hornets (11350-11352) | `xeen_hornet` | 62190-62193 | A Hell Hornet, B Hornet Swarm | `xeen_hornet_c` (-2): C Hornet Queen |
| Sand burrowers' Armadillo (11441) | `xeen_armadillo` (replaces the worm set on tier B) | 62200-62203 | B Armadillo | — |
| Octopods (11470-11472) | `xeen_octopod` | 62210-62213 | A Octopod, B Great Octopod | `xeen_octopod_c` (-2): C Kraken |
| Swamp things (11460-11462) | `xeen_swamp` | 62220-62223 | A Swamp Thing, B Bog Thing | `xeen_swamp_c` (-2): C Marsh Horror |
| Snake men (11500-11502) | `xeen_snakeman` | 62230-62233 | A Snake Man, B Snake Warrior | `xeen_snakeman_c` (-1.5): C Snake Lord |

### (a) Boss sets

| Boss (monster id) | Set | Ids | Notes |
| --- | --- | --- | --- |
| Lord Xeen (11634, XD-19) | `xeen_lordxeen` | 63100-63103 | no laugh or words: his voiced lines (d) play from the hooks |
| The Dragon King (11645, XD-18) | `xeen_dragonking` | 63110-63113 | a fire dragon's roar and breath |
| Xeen's Pet (11644, XD-19) | `xeen_dragonpet` | 63114-63117 | the Dragon King's set 2 semitones up (smaller) |
| The Energy Dragon (11653) | `xeen_energydragon` | 63120-63123 | a roar with an electric layer |
| The Megadragon (11654, D7) | `xeen_megadragon` | 63124-63127 | the Energy Dragon's set 3 semitones down |

Not made: **Sheltem** has no monster row (Corak fights him in m33's scene), so a boss set would have no hook; it is
one block of ten (63130) and five takes if a row appears. The other named dragons (Frost Dragon, the Darkside
tiers) keep the shipped dragon sounds (batch 1's survey: fine as they are).

Re-prompted after the first takes: the hornets' wince and fidget (sub-bass thumps from "deep ... droning": the
second prompt asks for the wing whine; a big hornet's wingbeat still sits at 100-150 Hz) and the snake men's wince
and death (hiss alone, nothing under 600 Hz: the second prompt adds a voiced cry). Sub-bass-only takes were passed
over for the guard's, the Dragon King's and the Energy Dragon's fidgets.

## Session 3 (2026-11-20): XD-19 and DD-16 (D-47) and the bed revisit

D-47's relay (`mockups/act5_a7_decisions.md`, RELAYS → AU): shipped sounds first. Every sound below is installed (WAV
and row) and resolves in the game by name and by id (desktop run `au_s3_names`, `work/au_s3_names.log`,
`work/au_s3_ids.log`). Credits this session: **3 194 charged, 11 620 committed** (22 requests, the two beds included);
whole budget: **23 048 charged, 79 350 committed** of 100 000.

| Use (D-47) | Sound (id) | Source | Pick and why | Hook (who) |
| --- | --- | --- | --- | --- |
| XD-19's four generator hums | `humming` (202) | shipped (engine): a steady 1.4 s hum loop; MM6's `reactor` was the other candidate, but it is a 2.9 s swell (26 dB spread), not a hum | — | A7: four placed loops at the generators (objects.yml `sounds`, radius about 1 500, inner 400, volume 0.5), each switched off (`AmbientSound<n>` 2) when its generator falls |
| XD-19's machines | `xeen_machine_stamp_loop` (62523) | generated, 12 s loop | v1: the most regular stamping (22 even blows in 11.6 s, steam between), 2.2 dB spread; v2 drops out at a quarter, v3 breaks rhythm | A7: one or two placed loops per machine hall (radius 3 000-4 000, inner a room, volume 0.4-0.5) |
| XD-19's barrier | `xeen_barrier_loop` (62524) | generated, 10 s loop | v3: a dense crackle over a buzz, the evenest (0.8 dB), the most snaps; v1 a smooth hiss, v2 swells out of near-silence | A7: a placed loop at the barrier (radius about 2 000, inner 600, volume 0.5), off when the barrier falls (with `xeen_castle_groan` as the one-shot then, if wanted) |
| The mirror shatters (scepter cinematic, Q14) | `xeen_mirror_shatter` (62520) | generated, 4 s one-shot (shipped glass is a 0.3 s melee hit) | v4: crack, burst, decaying shower and a second fall of shards; v1/v3 a flat wash, v2 starts after almost a second of near-silence | A3/A7: the cinematic's first `sound` cue |
| Castle Xeen groans | `xeen_castle_groan` (62521) | generated, 5.5 s one-shot (shipped `rumble` is 2 s of rumble alone) | v3: a creaking groan breaking into cracks and a trickle, the asked shape at -8; v1 stops dead, v2 6 dB quieter and even | A3/A7: the cinematic after the shatter (with the shake) |
| Lord Xeen, first sight and death (D-38) | `xeen_vo_lord_xeen_sight` (63030), `xeen_vo_lord_xeen_death` (63031) | installed in session 2 | — | A7 (Q13's step plate, `evt.PlaySoundName`), A3 (`sound:` fields) |
| DD-16's stasis field (optional) | `humming` (202) | shipped (engine) | — | A7: a placed loop at the stasis chamber (radius about 1 500), off when Corak is woken |
| DD-16's power restored (optional) | `xeen_power_up` (62522) | generated, 3.5 s one-shot | v2: a whine rising over a hum, the clunk at 2.5 s, the ring-out; v1 and v3 hold one tone | A7: the blast door's power event, positional at the panel |

The bed revisit: `xeen_amb_desert` and `xeen_amb_darkside` regenerated (three takes each at 30 s), see table (c).
The desert's takes came out as wind rumble again; `install.py` high-passes the pick at 150 Hz (4th order, run over the
loop three times so the seam stays whole) and levels it again: a new job field `bed_highpass_hz`, read only by the lane's
installer, since the processing tool shapes one-shots only.

## Session 4 (2026-11-21): D-48 panning, D-49 (D5, D6) and D-50 (X9, XD-17)

D-48 (merge point 21): every outdoor bed line carries `pan: false` ("Outdoor beds" above); the indoor list is below.
D-49 and D-50's relays (RELAYS → AU): shipped sounds first. Credits this session: **3 960 charged, 14 400 committed**
(29 requests: eight jobs at three or four takes, and the high-striker's second prompt; seven installed); whole budget: **27 008
charged, 93 750 committed** of 100 000. Every new sound is installed (WAV and row) and starts in the game
(`au_s4_new_names`, "Outdoor beds", Checked in the game).

| Use | Sound (id) | Source | Pick and why | Where (who) |
| --- | --- | --- | --- | --- |
| D5 desert wind | `xeen_amb_desert` (62808) | installed (session 3) | — | D5 list (A6), `pan: false` |
| D5 the aspens' tremble | `xeen_amb_aspen` (62810) | generated, 19 s loop | v3: an even broadband leaf rustle (94 % above 600 Hz, no birds), the evenest (4.6 dB); v1 and v2 swell and dip | D5 list, Quivering Forest, `pan: false` |
| D5 the Parabolic Barrier's hum | `humming` (202) | shipped (engine), as XD-19's generators | — | D5 list: six point sounds along the curtain, panned |
| D5 highland wind, D6 the passes | `xeen_amb_tundra` (62806) | installed (batch 1) | — | D5, D6 lists, low (0.25), `pan: false` |
| D6 ash wind | `xeen_amb_desert` (62808) | installed; the generated `xeen_amb_ash` is **not installed**: its three takes are a sustained tonal whistle (a line at 470-670 Hz, voiced 66-97 %) over sub-bass (64-95 % below 150 Hz), nothing above 600 Hz | — | D6 list, volume 0.3, `pan: false` |
| D6 lava bubbling | `lava loop` | shipped (engine), 3.2 s | — | D6 list: moat, pod lake, Slag Run, panned |
| D6 the lava falls (and X7's) | `xeen_lavafall_loop` (62525) | generated, 11 s loop (the shipped `waterfall loop` reads as water, `raging fire loop` is 89 % below 150 Hz) | v1: a thick even roar with crackle across the band, the evenest (1.4 dB); v2 and v3 step up a quarter of the way in and down near the end | D6 list at both falls, panned; X7 when its falls get sounds (A5) |
| D6 Necropolis | `xeen_amb_necropolis` (62811) | generated, 19 s loop | v2: a faint breeze with clinks, creaks and skitters spread over the loop, 7.3 dB; v1 repeats one chain burst on a beat, v3 has long silences and loud bursts (16 dB) | D6 list, one emitter over the town, `pan: false` |
| D6 Castle Alamar's hum | `humming` (202) | shipped | — | D6 list, at the gate pylons; off after `m33.done` |
| X9 wind bed | `xeen_amb_sky` (62803) + `xeen_sky_gust` (62519) | installed (batch 1), as X8 | — | X9 list (A5): one bed `pan: false` over the whole map, two gusts with waits, panned |
| X9 roc cries | `roc_aware` | shipped (engine): the roc's own cry, 1.9 s | — | X9 list: the aviary and the two burnable nests, with waits |
| X9 the high-striker's DING | `xeen_striker_ding` (62527) | generated, 3 s one-shot | v1 of the second prompt: one strike and a clear bell ring (partials at 1.4 kHz) decaying over 2.4 s; the first prompt's four takes ("a fairground strength tester ...") were 3 s of dense noise with the bell buried at the end | A3: `evt.PlaySoundName("xeen_striker_ding", -1024, 1280, 960)` in `m34.might_game` on a win (the bell over the plaza floor of 448) |
| X9 the fairground | `xeen_amb_fair` (62812) | generated, 19 s loop (no shipped crowd: the engine's tavern and shop files are 1 s greetings) | v3: an even crowd with clacks and calls (6.3 dB), the cleanest seam; v1 opens on a swell, v2 swells mid-loop | X9 list: one emitter over the plaza, `pan: false` |
| XD-17 the fall | `waterfall loop1` | shipped (engine), 4.1 s | — | XD-17 list (A5): at the fall's foot, panned |
| XD-17 the stream | `rushing water loop` | shipped (engine), low (0.3) | — | XD-17 list: two points on the stream, panned |
| XD-17 the forge hammer | `xeen_forge_hammer` (62526) | generated, 4.3 s one-shot (the shipped metal hits are 0.3 s melee clangs) | v1 over the score: eleven blows at an even 0.38-0.44 s with the anvil's ring at 5.4 kHz; v3 (the score's) hammers twice as fast, v2 is irregular and ends on its loudest blow | XD-17 list: by the forge's chimney, wait 2-7 s, by day |
| XD-17 the tavern murmur | `xeen_amb_tavern` (62813) | generated, 14 s loop | v1: an even murmur of voices with clinks (3.4 dB); v2 and v3 have loud low thumps (10-11 dB) | XD-17 list: at Tavern Xanadu's door, panned (a place you walk past) |
| XD-17 day birds | `bird01`, `bird08`, `bird03`, `bird11`, `bird05` | shipped (engine) one-shots, 1-4 s | — | XD-17 list: five points over the valley with waits, `day_only` |

Picks and reasons: `picks.yml` (`listening`), measured by `analyze.py` (`review/analysis.txt`, `review/sheets/`) and
`work/onsets.py` (blows, the bell's ring). Picked without ears: confirm by ear on the review page.

### X9 (A5, D-50)

An open-air BLV, so objects.yml `sounds` in game units (rooms and points from the L1 plan; move a point with its thing
if L2/L3 moves it). File: `level_generation/sounds/xeen_20261120/review/beds/x9.yml`. The sky bed is one emitter at
the landing, full within 22 000 (every walkable cloud but the castle's far apron), so nothing stacks; the fair is full
over the plaza (inner 2 800 against its half-diagonal of 3 840) and gone at the landing. Optional: switch a nest's
cries off when its nest is burned (A3's nest hook, `AmbientSound<key>` 2).

```yaml
sounds:
  - {id: sound:sky_bed, room: room:landing, at: [0, -2816], height: 512, sound: xeen_amb_sky, radius: 28000, inner_radius: 22000, volume: 0.4, pan: false}
  - {id: sound:gust_east, room: room:east_ledge, at: [15232, -1792], height: 512, sound: xeen_sky_gust, radius: 9000, inner_radius: 3000, volume: 0.5, wait: [6, 14]}
  - {id: sound:gust_west, room: room:west_spine, at: [-16896, -2816], height: 512, sound: xeen_sky_gust, radius: 9000, inner_radius: 3000, volume: 0.5, wait: [6, 14]}
  - {id: sound:roc_cries_aviary, room: room:aviary, at: [13440, 13440], height: 768, sound: roc_aware, radius: 7000, inner_radius: 2000, volume: 0.5, wait: [8, 20]}
  - {id: sound:roc_cries_se, room: room:se_nest, at: [13312, -15616], height: 768, sound: roc_aware, radius: 6000, inner_radius: 1500, volume: 0.45, wait: [10, 24]}
  - {id: sound:roc_cries_sw, room: room:sw_nest, at: [-13312, -15616], height: 768, sound: roc_aware, radius: 6000, inner_radius: 1500, volume: 0.45, wait: [10, 24]}
  - {id: sound:fair, room: room:carnival, at: [-2560, 2560], height: 160, sound: xeen_amb_fair, radius: 5000, inner_radius: 2800, volume: 0.45, pan: false}
```

### XD-17 (A5, D-50)

File: `level_generation/sounds/xeen_20261120/review/beds/xd17.yml`. The fall's foot is placed at the east cliff by the
pool (`[6016, 2048]`); while the fall decoration waits behind its switch (S's `xeen_waterfall`), give the sound the
same switch. The stream points stand on the line the L1 plan describes (south along the cliff foot); move them onto the
drawn stream.

```yaml
sounds:
  - {id: sound:falls, room: room:valley, at: [6016, 2048], height: 256, sound: waterfall loop1, radius: 4500, inner_radius: 1200, volume: 0.6}
  - {id: sound:stream_north, room: room:valley, at: [5888, -768], height: 32, sound: rushing water loop, radius: 1800, inner_radius: 400, volume: 0.3}
  - {id: sound:stream_south, room: room:valley, at: [5888, -3072], height: 32, sound: rushing water loop, radius: 1800, inner_radius: 400, volume: 0.3}
  - {id: sound:forge, room: room:valley, at: [384, -3072], height: 128, sound: xeen_forge_hammer, radius: 2600, inner_radius: 500, volume: 0.5, wait: [2, 7], day_only: true}
  - {id: sound:tavern, room: room:valley, at: [-2112, -3072], height: 128, sound: xeen_amb_tavern, radius: 1800, inner_radius: 400, volume: 0.45}
  - {id: sound:birds_orchard, room: room:valley, at: [4352, -2304], height: 512, sound: bird01, radius: 3500, inner_radius: 800, volume: 0.6, wait: [5, 14], day_only: true}
  - {id: sound:birds_court, room: room:valley, at: [0, 512], height: 512, sound: bird08, radius: 3500, inner_radius: 800, volume: 0.6, wait: [7, 18], day_only: true}
  - {id: sound:birds_west, room: room:valley, at: [-3968, -256], height: 640, sound: bird03, radius: 3500, inner_radius: 800, volume: 0.6, wait: [6, 16], day_only: true}
  - {id: sound:birds_north_west, room: room:valley, at: [-3584, 2816], height: 512, sound: bird11, radius: 3500, inner_radius: 800, volume: 0.6, wait: [8, 20], day_only: true}
  - {id: sound:birds_terrace, room: room:valley, at: [0, 4032], height: 768, sound: bird05, radius: 3500, inner_radius: 800, volume: 0.6, wait: [6, 15], day_only: true}
```

### Indoor beds: `pan: false` (D-48)

The rule: a bed that fills its rooms gets `pan: false` in its objects.yml line; anything with a source you can see or
place keeps panning (fires, torches, drips, lava, cauldrons, water, chimes, drums, a machine or a ward that hums, wind
at an opening or a window). From the installed scenes (2026-11-21):

| Map (lane) | Add `pan: false` to | Keep panning |
| --- | --- | --- |
| XD-02 (A7) | `sound:sorting_mine`, `sound:stope_mine` | — |
| XD-03 (A7) | `sound:landing_mine`, `sound:warren_mine` | — |
| XD-15 (A7) | `sound:dungeon_hum_lib`, `sound:dungeon_hum_w` (the shipped `humming` as the dungeon's bed) | the torch, `sound:eyes_wind` |
| DD-07 (A7) | `sound:tower_bed` | — |
| XD-11 (A8) | `sound:tower_bed` | lava, sparks, cauldrons, drips, `sound:roof`, `sound:stairway` |
| XD-12 (A8) | `sound:tower_bed` | lava, sparks, cauldron, drip, the four roof winds |
| DD-01 (A8) | `sound:bed_east`, `sound:bed_south`, `sound:bed_west` | drips, water, `sound:outfall` |
| DD-02 (A8) | `sound:tower_bed` | cauldron, `sound:wards_hum`, `sound:loft_wind`, `sound:roost_wind` |
| DD-05 (A8) | `sound:tower_bed` | fires, water, `sound:hoist_wind` |
| DD-10A (A8) | `sound:bed_gallery`, `sound:bed_ruby` | drips, `sound:adit_wind` |
| DD-10B (A8) | `sound:bed_flooded`, `sound:bed_sapphire`, `sound:bed_upper` | water, drip, `sound:god_hum`, `sound:adit_wind` |
| DD-12 (A8) | `sound:bed_lower`, `sound:bed_maze`, `sound:bed_upper` | fires, water, `sound:entry_wind` |
| DD-14 (A8) | `sound:roost` (the tower bed as the roost's draughts), `sound:yard_wind` (the sky bed over the courtyard) | `sound:gust_landing`, the four walk winds, drips, water |
| DD-18 (A8) | `sound:bed_cistern`, `sound:bed_drains`, `sound:bed_nest`, `sound:bed_tunnel` | drips, water, `sound:desert_gate`, `sound:sand_drift` |
| X8 (A6) | `sound:sky_bed` | `sound:gust_east`, `sound:gust_west`, the four winds, `sound:bells` |

Kept panning on purpose: DD-03's seven `xeen_phase_loop` emitters (each a phase leaf or a shimmering patch at a place,
radius 800-1 300); XD-25's transformer hum (a machine); XD-19's generators and DD-16's stasis field. No other
installed indoor scene places a bed.

## Session 5 (2026-11-21): P5 (D-56), D7 and the planes (D-58), the dungeons' asks, X7, night beds

The user lifted the ElevenLabs cap ("use however much you need, if it makes sense"); the job file's `budget` is now
140 000. Shipped and installed sounds first; 27 jobs generated (87 requests) and three beds re-prompted (9 more):
**25 sounds installed** (ids 62528-62544, 62814-62821; 264 rows in all). Credits this session: **10 783 charged,
39 200 committed**; whole: **37 791 charged, 132 950 committed** of 140 000. Not installed: the four corner hums
(rumble or swells out of silence; the corners carry their plane's bed instead) and the Brew vat (sparkle with no
bubbling; the shipped cauldron stays). Picks and reasons: `listening.yml` / `picks.yml`, measured by `analyze.py` and
the session's `work/look.py` (bands, envelope, onsets, spectrograms) and `work/pitchtrack.py` (a melody or a pulse
train). **Picked without ears**: confirm by ear on the review page. All 25 start in the game (below).

| Use | Sound (id) | Source | Pick and why |
| --- | --- | --- | --- |
| P5: the four sleepers answer (D-56 shot 2) | `xeen_chime_1` … `_4` (62528-62531) | generated (`xeen_far_chime`, 4 takes), derived | three different far bells (v1, v2, v4) and v2 five semitones down: four bells, the last the deepest |
| P5: the wedding (shot 4) | `xeen_wedding_fanfare` (62532) | generated, 5 takes | v3: a rising C-E-G call, then a held F major chord ringing out; the score's v4 is one held note |
| D7: cloud dragons calling far off | `xeen_dragon_call` (62533) | generated | v4: a roar rising into a shrill cry at 1.2-1.5 kHz and fading |
| D7: the Megadragon asleep on Alamar's roof | `xeen_megadragon_sleep` (62534) | generated, 7.5 s loop | v2: slow growling breaths, two cycles, the evenest; its fights keep its batch 2 set (63124-63127) |
| D7: the Sky Bandits' toll whistle | `xeen_bandit_whistle` (62535) | generated | v1: two linked finger whistles, the second higher and falling away |
| D7's corners (D-58: "a hum in each corner's element") | the plane beds below, as point sounds at the tips | installed this session | the four corner jobs are not installed (`listening.yml`) |
| P1 lava | `xeen_amb_plane_fire` (62814) | generated, 19 s loop, high-passed at 150 Hz at install | v3: bubbling at 150-600 Hz, pops and hiss, 3 dB |
| P2 gale | `xeen_amb_plane_air` (62815) | generated | v2: a broad howling gale with gusts, 2.9 dB |
| P3 rumble | `xeen_amb_plane_earth` (62816) | generated (second prompt), high-passed at 80 Hz | v3: grinding at 80-150 Hz under clatter; quiet by nature (-29.5 dBFS RMS): volume 0.9 |
| P4 surf | `xeen_amb_plane_water` (62817) | generated (second prompt) | v3: full surf, almost no sub-bass |
| DD-17's trapdoors | `xeen_trapdoor` (62536) | generated | v1: one clang at once, ringing 0.6 s (the others click 1 s before the clang) |
| DD-17's self-destruct | `xeen_klaxon` (62537) | generated, 6 s | v3: a harsh 825 Hz horn in long blasts |
| DD-22's alarm (was `buzzer01`) | `xeen_pod_alarm` (62538) | generated, 3.8 s loop | v3: a two-tone beep (2 045/1 790 Hz) every 0.6 s. `buzzer01` is the menus' 0.3 s error buzz (764/840 Hz), read as "you can't" |
| DD-22's log (was `tone2`) | `xeen_log_chirp` (62539) | generated | v1: three rising steps and a click, 0.4 s. `tone2` is a 0.27 s flat 311 Hz menu beep |
| DD-15's four torches (was `xeen_fire_ignite`) | `xeen_torch_light` (62540) | generated | v2: a small whoomph and flicker; `xeen_fire_ignite` (4 s, 75 % below 150 Hz) is a lair going up and stays on the Brew's drink |
| DD-15's pads, vat | `Teleport`, `bubbling cauldron01` | shipped, kept | the game's own teleport cue; a bubbling vat at 150-600 Hz (the generated vat had no bubbling) |
| DD-25's forge bay (was `metal vs metal01l` with a wait) | `xeen_forge_hall_loop` (62820) | generated, 11.4 s loop | v3: several smiths, dense ringing blows, 1.9 dB |
| DD-21's heart in the jar | `xeen_heartbeat_loop` (62541) | generated, 5.7 s loop | v1: a regular double thump at 62 a minute; low by nature, so close (radius 900) |
| DD-26's tribbles | `xeen_tribble_purr` (62821) | generated, 7.5 s loop | v3: a rolling purr with coos at 150-600 Hz |
| FD-01's shaft | `xeen_shaft_grit` (62542) + the shipped `whistling wind` | generated, 7.5 s loop | v3: sand hiss with pebble ticks |
| FD-01's stasis coffin (was `humming`) | `xeen_stasis_hum` (62543) | generated, 9.4 s loop | v2: a glassy 829 Hz tone with a faint shimmer, 0.6 dB |
| FD-01's settling metal (optional) | `xeen_metal_groan` (62544) | generated | v1: the longest groan |
| X7's volcano bed | `xeen_amb_volcano` (62818) | generated, high-passed at 80 Hz | v2: rumble at 80-150 Hz under vent hiss and sizzle |
| Cloudside nights (X1, X2, X4, X5's pocket) | `xeen_amb_night` (62819) | generated (second prompt) | v2: a steady cricket chorus at 2.5-8 kHz, the Darkside crickets' band (the first prompt's were a 8-10 kHz whine) |
| D5's Barrier hum and the hold's fire | `humming`, `campfire` | shipped, already placed | D5 from assets_dev: the six hums sit on frames 2, 5, 8, 11, 14, 17 of the sketch's curtain and the fire on `thing:hold_fire`; standing at (1 382, 14 500) the third hum (1 000 away) and four highland emitters start, the second hum (5 100 away) does not |

**Checked in the game** (`build-xeen`, minimised, `OPENYAMM_AUDIO_TRACE=1`, logs `work/au_s5_*_game.log`): D1's
installed scene with the 25 new names added (radius 90 000, through `--extra-mount output/au_s5/mount`): every one
`result=started` from `audio/xeen/<name>.wav` (`au_s5_new_names`); D5 from assets_dev as in the table (`au_s5_d5`).

**The re-pasted beds** (`work/check_pan.py` over every installed Xeen scene, 2026-11-21 09:45): X1-X7, D1-D7, X8, X9,
P5 and the indoor maps A7 named carry `pan: false` on every bed and pan their point sounds. Still panned: the beds of
**DD-01, DD-02, DD-10A, DD-10B, DD-12, DD-18, XD-11, XD-12** (A8's, listed in session 4) and **DD-19**'s
`sound:court` (`xeen_amb_sky`), `sound:hall` and `sound:sanctum` (`xeen_amb_tower`), new on the list.

### The lines to paste

**P5 (A5)**, `briefs/p5/L4/wiring.yml`, `cinematic:unification` cues (shot 2 is 8-18 s, shot 4 from 24 s):

```yaml
      - {at: 9.5, sound: xeen_chime_1}
      - {at: 11.5, sound: xeen_chime_2}
      - {at: 13.5, sound: xeen_chime_3}
      - {at: 15.5, sound: xeen_chime_4}
      - {at: 24.5, sound: xeen_wedding_fanfare}
```

**D7 (A6)**, `briefs/d7/L4/objects.yml` `sounds` (the tips of the four corners, the roost, the three dragon groups):

```yaml
  - {id: sound:corner_fire, room: room:air, at: [-30464, 20480], height: 128, sound: xeen_amb_plane_fire, radius: 2500, inner_radius: 600, volume: 0.5, notes: "The Fire Corner's tip: P1's lava heard through the corner (D-58), panned."}
  - {id: sound:corner_air, room: room:air, at: [30464, 20480], height: 128, sound: xeen_amb_plane_air, radius: 2500, inner_radius: 600, volume: 0.5, notes: "The Air Corner's tip: P2's gale."}
  - {id: sound:corner_earth, room: room:air, at: [30464, -20480], height: 128, sound: xeen_amb_plane_earth, radius: 2500, inner_radius: 600, volume: 0.9, notes: "The Earth Corner's tip: P3's grinding."}
  - {id: sound:corner_water, room: room:air, at: [-30464, -20480], height: 128, sound: xeen_amb_plane_water, radius: 2500, inner_radius: 600, volume: 0.5, notes: "The Water Corner's tip: P4's surf."}
  - {id: sound:megadragon_sleep, room: room:air, at: [-19456, 9216], height: 128, sound: xeen_megadragon_sleep, radius: 3500, inner_radius: 900, volume: 0.6, notes: "The Megadragon asleep on the hatch (Q-D26): off on its kill and on every load after (A3, AmbientSound<key> 0)."}
  - {id: sound:dragon_call_cap, room: room:air, at: [4608, 4768], height: 1024, sound: xeen_dragon_call, radius: 9000, inner_radius: 2500, volume: 0.45, wait: [25, 60], notes: "Cloud dragons calling far off."}
  - {id: sound:dragon_call_cap_b, room: room:air, at: [13056, -1024], height: 1024, sound: xeen_dragon_call, radius: 9000, inner_radius: 2500, volume: 0.45, wait: [25, 60]}
  - {id: sound:dragon_call_east, room: room:air, at: [-20736, -4864], height: 1024, sound: xeen_dragon_call, radius: 9000, inner_radius: 2500, volume: 0.45, wait: [25, 60]}
```

**P1-P4 (A6)**, each plane's `objects.yml` `sounds`: one bed over the plane (the planes are about 13 000 across):

```yaml
  - {id: sound:plane_bed, room: room:crater, at: [-256, 0], height: 512, sound: xeen_amb_plane_fire, radius: 12000, inner_radius: 8000, volume: 0.4, pan: false}   # P1
  - {id: sound:plane_bed, room: room:air, at: [0, 0], height: 512, sound: xeen_amb_plane_air, radius: 16000, inner_radius: 11000, volume: 0.4, pan: false}       # P2 (floor -6000: as X8's sky bed)
  - {id: sound:plane_bed, room: room:bowl, at: [-128, 0], height: 512, sound: xeen_amb_plane_earth, radius: 12000, inner_radius: 8000, volume: 0.9, pan: false}  # P3
  - {id: sound:plane_bed, room: room:sea, at: [0, 0], height: 1100, sound: xeen_amb_plane_water, radius: 12000, inner_radius: 8000, volume: 0.45, pan: false}   # P4 (over the surface at -64)
```

**A3:** `Xeen.toll` plays `evt.PlaySoundName("xeen_bandit_whistle")` when a toll stops the party (not once it is
paid); the Megadragon's kill hook and D7's load event (kill qbit set) switch `sound:megadragon_sleep` off.

**A8's dungeons** (their `L4/objects.yml` and `wiring.yml`):

| Map | Change |
| --- | --- |
| DD-17 | each `evt:trap_t1`…`t6`: `lua: evt.PlaySoundName("xeen_trapdoor")` with the drop; `cinematic:self_destruct` cues `{at: 5, sound: xeen_klaxon}` and `{at: 11.5, sound: xeen_klaxon}` (the groan at 9.5 stays). Optional: the four Lava Heads' `humming` stand-ins become their element's plane bed at volume 0.35 (`hum_air` `xeen_amb_plane_air`, `hum_earth` `xeen_amb_plane_earth` at 0.7, `hum_fire` `xeen_amb_plane_fire`, `hum_water` `xeen_amb_plane_water`), still stopped by the Head |
| DD-15 | the four torch levers: `evt.PlaySoundName("xeen_torch_light")` for `"xeen_fire_ignite"` (the Brew's drink keeps `xeen_fire_ignite`); pads and vat unchanged |
| DD-22 | `sound:alarm`: `sound: xeen_pod_alarm`, no `wait` (a loop, still stopped by the release); the log: `evt.PlaySoundName("xeen_log_chirp", 896, 1088, 1056)` for `"tone2"` |
| DD-25 | `sound:anvil`: `sound: xeen_forge_hall_loop, radius: 2400, inner_radius: 500, volume: 0.35`, no `wait` |
| DD-21 | `- {id: sound:heart, room: room:heart_culvert, at: [-832, -4704], height: 144, sound: xeen_heartbeat_loop, radius: 900, inner_radius: 250, volume: 0.6, notes: "Sandro's heart in the jar: off once heart_found (113461) is set."}` |
| DD-26 | `- {id: sound:tribbles, room: room:den, at: [0, 1700], height: 160, sound: xeen_tribble_purr, radius: 1000, inner_radius: 300, volume: 0.45, notes: "The tribbles in the den's cages."}` |
| FD-01 | `sound:coffin_hum`: `sound: xeen_stasis_hum` (still off with the field); add `- {id: sound:shaft_grit, room: room:shaft, at: [-8392, 7168], sound: xeen_shaft_grit, radius: 1200, inner_radius: 300, volume: 0.45}` beside the wind; optional `- {id: sound:metal_groan, room: room:hub, at: [-3072, 3840], sound: xeen_metal_groan, radius: 4200, inner_radius: 1600, volume: 0.35, wait: [25, 60]}` |
| DD-01, DD-02, DD-10A, DD-10B, DD-12, DD-18, XD-11, XD-12 | `pan: false` on the beds (session 4's list, not yet in the installed scenes) |
| DD-19 | `pan: false` on `sound:court`, `sound:hall`, `sound:sanctum` |

**X1, X2, X4, X5 (A5, A6):** the night lines in the blocks above (`bed_night_*`, `bed_pocket_night_*`); the day lines
are unchanged. **X7 (A5):** the block above.

## Planned (later batches)

- Events: the rim fall, the ghost waves' arrival (X5), Newcastle's building stages, the arena gong, the Ancient logs'
  terminals (DD-22's `xeen_log_chirp` may serve them).
- D6's ash wind is the desert bed (session 4); a dedicated ash bed would need a prompt that does not come out as a
  tonal whistle.

## (d) Voice lines: the voiced sheet (D-38)

Status: **voiced and installed** (2026-11-20, session 2). Every line is a locked `voice:` line of the quest YAMLs; the
hooks are A3's (`xeen_quests.lua`, silent until now) and they call exactly these names. The text always shows.
Generated with designed voices (`tools/audio`, jobs `vd_*` and `xeen_vo_*` in `jobs.yml`), three takes a line read
with `eleven_v3` (stability 0.5), a light treatment, picked only among the takes both local Whisper models read
(`whisper_check.py`: faster-whisper small.en exact, base.en at most one word off; names lenient, and "a" heard as "ah").
**Picked without ears** by the measures of `voices.py` (length, pitch, spread, HNR) against the brief: confirm by ear
on the review page (group "Voices: lines"). To change a pick, write `choice: vN.wav` under the line's job in
`listening.yml`, run `merge_listening.py`, `process` and `install.py`.

| Speaker | Line (subtitle) | Sound (id) | Hook | Takes | Picked | Length |
| --- | --- | --- | --- | --- | --- | --: |
| King Burlock | Ah, more adventurers! I charge you with the quest of finding the Sixth Mirror. | `xeen_vo_burlock_charge` (63000) | m5, the Sixth Mirror topic (global event 40251), first audience | 3 | v3 | 6.3 s |
| King Burlock | NO MIRROR?!? Get out of my sight! | `xeen_vo_burlock_no_mirror` (63001) | m5, the same topic every later time | 3 | v2 (the sputter: a break after "No!") | 3.4 s |
| King Burlock | Thank you for rescuing Xeen from that foul spirit. It is a pity about the mirror, though. | `xeen_vo_burlock_thanks` (63002) | m35, after Lord Xeen falls (both topic states) | 3 | v2 | 7.1 s |
| Corak | Ah! A Soulbox! You have done well. | `xeen_vo_corak_soulbox` (63010) | m32, the Soul Box given (DD-16) | 12 (four prompts) | v1 of the fourth | 4.9 s |
| Corak, Sheltem, Corak | Sheltem. / Corak. You took your time. / The Cube! Take it and run! | `xeen_vo_sheltem_corak` (63011) | m33, the box thrown down (DD-17): the three lines joined, 0.6 s apart | 3 per line | v3, v2, v2 | 9.6 s |
| Sheltem | Chosen Ones. You have nothing I need to fear. | `xeen_vo_sheltem_refusal` (63020) | m33, DD-17's door refusal without the box, first time only | 3 | v2 | 5.0 s |
| Lord Xeen | (a slow, amused laugh) The King's little crusaders, all this way up. Kneel, and I may let you fall gently. | `xeen_vo_lord_xeen_sight` (63030) | m35 `lord_xeen_sight`, XD-19, once per save | 6 (two prompts) | v1 of the second (about 2 s of laughter, then the line) | 10.6 s |
| Lord Xeen | You have no idea what you have broken. | `xeen_vo_lord_xeen_death` (63031) | m35 `lord_xeen`, his death, once per save | 3 | v3 | 5.2 s |
| The Dragon Pharaoh | Let the two faces of Xeen be one world again. | `xeen_vo_pharaoh_unification` (63040) | M42, the unification (the ending) | 3 | v1 | 6.6 s |

**The voices** (Voice Design `eleven_ttv_v3`, one request of three previews per speaker, two for Corak and the
Pharaoh; the saved preview of each makes the set whose closest pair lies furthest apart by `voices.py`'s measure: the
log-mel timbre difference plus half the pitch difference in semitones):

| Speaker | Description sent (shortened; full text in jobs.yml) | Voice | Measured (preview) | Treatment |
| --- | --- | --- | --- | --- |
| King Burlock | blustering, pompous old king: plump, hearty, chesty, easily flustered, quick to splutter, comic | `tRHOdGZbt2VZzsIzwUVt` (vd_burlock p3) | f0 190-270 Hz, the widest pitch movement | formants -1 (a bigger man), a 0.35 s throne-room room |
| Lord Xeen | cold, amused usurper: very deep, smooth, dark bass, slow, quietly mocking, never raised | `oOrp7bZ4qg1Z5CS1ziP8` (vd_lord_xeen p2) | f0 69 Hz, the darkest and roughest (HNR 3.9 dB) | formants -2, a sub-octave at -16 dB, a dark 0.5 s room |
| Sheltem | ancient, dry, contemptuous: an old man's thin, papery, clipped voice with a flat mechanical edge | `hZOe383KWOKL4H5rkLCx` (vd_sheltem p1) | near-whispered (5 % voiced, HNR 1.5 dB): dry and papery | formants -1.5, ring 40 Hz at 0.12 (the machine edge), a 200-6 500 Hz band, a short room |
| Corak | warm, measured guardian: a clear, kind, mid-range baritone with a faint synthetic sheen | `whF5D6oEaYFpKDZUVZ5m` (vd_corak_2 p1) | f0 90 Hz, brighter than the first request's | the same machine band warmed: 160-6 500 Hz, +4 dB low shelf at 300 Hz, ring 40 Hz at 0.05, formants -1 |
| The Dragon Pharaoh | ancient dragon king, very old: frail, breathy, wheezing, warm and kindly, a long dry hiss on every s | `VwvG90kRuXE2gg0212hY` (vd_pharaoh_2 p1) | f0 60 Hz with an unsteady, creaking pitch; the hissiest (centroid 1 593 Hz) | formants -2.5 (a huge throat), a sub-octave at -14 dB, a 0.6 s shrine room |

Distances (the closest pairs): designs 6.9 (Corak-Pharaoh), installed lines 6.5 (Lord Xeen-Sheltem) and 6.7
(Sheltem-Pharaoh); the first-request set's closest pair was 5.4 (Lord Xeen-Pharaoh, both at 65-70 Hz), which is why
Corak and the Pharaoh got a second request. Burlock is 21-27 from everyone.

**What production found:**
- **"Ah! A Soulbox!"**: twelve takes over four prompts run "Ah" and "a" together; small.en hears "Ah, ah soulbox" or
  "Ah, our soul box". The pick reads exactly in base.en and with the article as "ah" in small.en (counted as read).
- **Lord Xeen's laugh**: the tag `[slow, amused laugh]` at stability 0.5 was skipped in all three takes (each opens on
  "The King's" within a second); `[laughs slowly] [amused]` at stability 0 ("Creative") laughs in all three.
- **The Pharaoh** v3 fails ("two faces I've seen"); "Xeen" is heard as "Zeen", "Zine" or "scene" throughout (a name).
- **Lord Xeen's death** v1 and v2 croak an octave and hold a -60 dBFS hiss for 1.5 s after the words; v3 is clean.
- Audio tags (`[indignant, sputtering]`, `[warmly]`, `[urgent, strained]`) are not spoken in any take.

**Credits** (cap 4 000 committed): 7 designs 931 (docs rate, no cost header), 45 takes 1 275 charged (2 895 committed):
**2 206 charged, 3 826 committed**.

**Checked in the game** (2026-11-20, `build-xeen`, minimised desktop runs with `OPENYAMM_AUDIO_TRACE=1`): the Sixth
Mirror topic (global event 40251) plays `audio/xeen/xeen_vo_burlock_charge.wav`; every other voice name resolves and
queues from `evt.PlaySoundName`, and ids 63000, 63011 and 63040 from `evt.PlaySound`.

## Hooks checked in the game (2026-11-20, session 2)

Minimised desktop runs on `build-xeen` with `OPENYAMM_AUDIO_TRACE=1` and a startup console file
(`level_generation/sounds/xeen_20261120/work/*.console`; headless scenarios do not play sounds, so the trace there is
empty). A console line runs as one event and the next line replaces its queued sounds in the same frame, so names are
checked on one line and a hooked event last.

| Kind | Checked | Result |
| --- | --- | --- |
| Quest hooks (A3) | the Sixth Mirror topic, global event 40251 | plays `xeen_vo_burlock_charge.wav` |
| Names from Lua | all nine voice names by `evt.PlaySoundName` | every one resolves to `audio/xeen/<name>.wav` |
| Rows by id | 19 ids from batch 2 and the voice block by `evt.PlaySound` (62150-62237, 63000-63127) | every one resolves |
| Monster columns (A2) | toads, a mummy, a hornet spawned on X3 for 15 s | not visible: the trace has no actor sound lines (outdoor monster sounds go through the world's audio events, which the trace does not log); the columns' ids resolve (above), the descriptor rows carry them (43 rows on 620xx) |
| Map event sounds | wired in X5 (gongs, events 147-149), XD-26 (winch, 13-18), D1 (phase shift, 265), `xeen_common.lua` (mirrors, pyramids), the obelisks and springs | names resolve (batch 1 check); not driven here |
| Placed beds | session 3: X6 built from a copy of its L4 with the desert block (scratch root `output/au_beds/root`), standing at cell [32, 80] | the three desert emitters within reach and the sand-fall start (`play source=assetInstance`, `work/au_beds_x6.log`); the installed maps place no bed until the map lanes paste the lists |
| House `enter_sound` (A4's field, four fortune tellers) | waits on A1 | — |

## Requests to other lanes

New in session 5 (the lines are in "Session 5", "The lines to paste"):

| To | What | Where |
| --- | --- | --- |
| A5 | P5: the four chime cues and the fanfare in `cinematic:unification`; X1, X2, X4: add the night lines; X7: paste its block (volcano and range wind; the lava falls' line stays) | `briefs/p5/L4/wiring.yml`, `review/beds/{x1,x2,x4,x7}.yml` |
| A6 | D7: corners, the Megadragon's sleep, the dragon calls; P1-P4: one bed each; X5: the pocket's night lines | `briefs/d7/L4/objects.yml`, `briefs/p1..p4/L4/objects.yml`, `review/beds/x5.yml` |
| A3 | `Xeen.toll`: the bandits' whistle; the Megadragon's kill and D7's load event switch `sound:megadragon_sleep` off | M38 / Q-D26, `xeen_common.lua` |
| A8 | DD-17 trapdoor and klaxon (and optionally the Heads' element beds), DD-15 torches, DD-22 alarm and log, DD-25 forge loop, DD-21 heartbeat, DD-26 purring, FD-01 grit, stasis hum and groan; `pan: false` still missing on eight installed scenes' beds and on DD-19's three | their `L4/objects.yml`, `wiring.yml` |

New in session 4 (the lists are the files `level_generation/sounds/xeen_20261120/review/beds/<map>.yml`, the same
blocks as in this document):

| To | What | Where |
| --- | --- | --- |
| A5 | Re-paste the `pan: false` lists of X1, X2, X3, X4, X6 and D3 (positions unchanged, only `, pan: false` added to each bed line; X6's sand-fall line stays panned) into `output/studio_cal/a5/beds/<map>.yml` and rerun `a5/beds/pipeline.sh` | `review/beds/{x1,x2,x3,x4,x6,d3}.yml` |
| A5 | X9 and XD-17 (D-50): their objects.yml `sounds` lists ("Session 4"); XD-17's fall sound follows the fall decoration's switch; X7's lava falls may take `xeen_lavafall_loop` | `review/beds/x9.yml`, `review/beds/xd17.yml` |
| A6 | Re-paste the `pan: false` lists of X5, D1 (Kalindra's shimmer stays panned), D2 and D4 into `output/studio_cal/a6/beds/<map>.yml` and rerun `a6/beds/install_beds.sh`; add D5 and D6's lists (D-49) to their generators; D6's `sound:alamar_hum` off after `m33.done`; X8's `sound:sky_bed` gets `pan: false` | `review/beds/{x5,d1,d2,d4,d5,d6}.yml`, `briefs/x8/L4/objects.yml` |
| A7 | `pan: false` on the beds of XD-02, XD-03, XD-15 and DD-07 ("Indoor beds") | those maps' `L4/objects.yml` |
| A8 | `pan: false` on the beds of XD-11, XD-12, DD-01, DD-02, DD-05, DD-10A, DD-10B, DD-12, DD-14 and DD-18 ("Indoor beds") | those maps' `L4/objects.yml` |
| A3 | X9's high-striker: `evt.PlaySoundName("xeen_striker_ding", -1024, 1280, 960)` (the bell at the pole's top, about 512 over the plaza's floor of 448) on a win in `m34.might_game`; optional: a burned nest's cries off (`AmbientSound<key>` 2) | M34 |
| A1 | Done at merge point 21 (session 3's request): `pan: false` and random loop starts | — |

New in session 3:

| To | What | Where |
| --- | --- | --- |
| A5 | Paste the `sounds:` lists of "Outdoor beds" into X1, X2, X3, X4, X6 (it keeps its sand-fall line; `xeen_sandfall_loop` is the right name, checked) and D3, rebuild and install | `briefs/<map>/L4/sketch.yml` |
| A6 | The same for X5, D1 (with `sound:kalindra_shimmer`, optionally `on: false` and switched off once the castle is back in phase), D2 and D4 | `briefs/<map>/L4/sketch.yml` |
| A1 | A looping placed sound starts at a random point of its clip (or one seeded by its key), so the emitters of one bed that come into reach together do not play in step (they add in amplitude, up to about +6 dB); and, if the decider says so, a per-sound `pan: false` (scene and studio word) for beds | `game/audio/WorldAmbientSounds.cpp`, studio |
| A7 | XD-19 and DD-16 (D-47): the table of "Session 3" (generators and stasis `humming`, `xeen_machine_stamp_loop`, `xeen_barrier_loop`, `xeen_power_up`; the Lord Xeen lines on Q13's plate and his death) | XD-19, DD-16 briefs |
| A3 | XD-19's cinematic cues `xeen_mirror_shatter` then `xeen_castle_groan`; D-38's `sound:` fields for Lord Xeen (63030, 63031) | M35 |

Batch 1's requests (sent 2026-11-20, session 1) stand where not yet done; new in session 2:

| To | What | Where |
| --- | --- | --- |
| A2 | Name the batch 2 sets in monsters.yml: pyramid mummies `sounds: xeen_mummy`, tier C `xeen_mummy_c` (off MM9's ids); Xeen's Guard (tier D) `xeen_xguard`; floating mages `xeen_mage`, C `xeen_mage_c`; coven `xeen_coven` (instead of `xeen_witch`), C `xeen_coven_c`; hornets `xeen_hornet`, C `xeen_hornet_c`; the Armadillo (sand burrowers' B) `xeen_armadillo`; octopods `xeen_octopod`, C `xeen_octopod_c`; swamp things `xeen_swamp`, C `xeen_swamp_c`; snake men `xeen_snakeman`, C `xeen_snakeman_c`; bosses: Lord Xeen `xeen_lordxeen`, the Dragon King `xeen_dragonking`, Xeen's Pet `xeen_dragonpet`, the Energy Dragon `xeen_energydragon`, the Megadragon `xeen_megadragon` | `source/monsters.yml` |
| A3 | The nine voice names are installed (ids 63000-63040); the hooks need no change | — |
| A1 | E9 (outdoor emitters) for the six outdoor beds and the sand-falls; the house `enter_sound` field (A4) for `xeen_fortune`. Optional: trace the world's monster audio events under `OPENYAMM_AUDIO_TRACE` so a lane can confirm a family's sounds play | engine |

Batch 1's table (session 1):

| To | What | Where |
| --- | --- | --- |
| A1 | E9 (outdoor emitters) is what the six outdoor beds and the sand-falls wait on (the `sounds` tableContributions entry is in) | engine |
| A2 | Name each family's set (and the pitched set per tier or boss) from table (a) in monsters.yml (done for batch 1: 43 descriptor rows carry 620xx ids) | `source/monsters.yml` |
| A3 | `Xeen.useMirror`: `xeen_mirror_touch`, `xeen_mirror_travel`; obelisks `xeen_obelisk`; the Lifeforce Spring and lasting-gift shrines `xeen_spring_drink`; the burned encampment `xeen_fire_ignite` (all wired) | `events/common/xeen_common.lua`, `xeen_quests.lua` |
| A4 | The travel pyramids `xeen_pyramid_travel` (wired); fortune tellers `xeen_fortune` (as `enter_sound:`, waits on A1) | transport and house events |
| A5 | X3: Draco's coffin `xeen_coffin_lid`, wells `xeen_well_drink`; X6: the coach yard gate `xeen_yard_gate`, the Sphinx `xeen_sphinx_stir`, the sand-falls `xeen_sandfall_loop` (after E9); X1: the orc drums burning `xeen_fire_ignite`; X9: `xeen_sky_gust`, `xeen_amb_sky` | X1, X3, X6, X9 briefs |
| A6 | X5's ghost-wave gongs (wired); X8: `xeen_amb_sky` bed and `xeen_sky_gust` (wait 6-14 s) beside the shipped wind; D2's burned fort `xeen_fire_ignite`; D1's castle hill `xeen_phase_shift` (wired) | X8, D2 briefs |
| A7 | XD-03's gong: `evt.PlaySound(42682, ...)` → `evt.PlaySoundName("xeen_gong", x, y, z)`; DD-06's gong; XD-26's hoist and ladder `xeen_winch` (wired); XD-15's Sphinx `xeen_sphinx_stir`; XD-02/XD-03 bed `xeen_amb_mine` | wiring and objects briefs |
| A8 | XD-10's plug `xeen_reservoir_drain`; DD-02's lift `xeen_lift`; XD-21's plank bridge and XD-12's works gate `xeen_winch`; DD-03 `xeen_phase_shift` and `xeen_phase_loop` placed; beds: DD-01/DD-18 `xeen_amb_sewer`, XD-11/XD-12/DD-02 `xeen_amb_tower` (volume 0.3-0.4), DD-10 `xeen_amb_mine` | wiring and objects briefs |

Placed beds: loop, inner radius about a room, outer radius 2-4 rooms, volume 0.4-0.6 (the beds are levelled to -20 dBFS
RMS, louder than the shipped drips): one or two per large room, not one per sector.
