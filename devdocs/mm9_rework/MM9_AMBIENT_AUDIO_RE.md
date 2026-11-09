# MM9 ambient sound and music (reverse engineering)

How Might and Magic IX plays ambient sounds, music and interior acoustics, and what the OpenYAMM MM9 rework does
today. Research date 2026-11-06. Companion to [MM9 ambient volume RE](MM9_AMBIENT_VOLUME_RE.md) (the volume chain,
not repeated here) and the engine's [placed ambient sounds](../AMBIENT_SOUNDS.md).

Sources:

- DAT objects: all 45 `assets_editor_dev/worlds/mm9/maps/<stem>.raw_objects.yml` (parsed in full; every property name
  containing Sound, Music, Ambient, Volume, Radius, Loop, Range, Pan, Fade, Reverb, EAX or Track checked).
- Scripts: the 804 `mm9/extracted/SCRIPTS/SCRIPTS/*.scr|*.inc`; data `mm9/extracted/DATA/DATA/MAPSTATS.txt`;
  `mm9/game/music/MM9-Song01..17.mp3`; `mm9/game/EAL/*.eal`; `mm9/game/autoexec.cfg`.
- Binaries, Rizin 0.10 + rz-ghidra (projects in the ignored `re_mm8/work/mm9_audio/`), same hashes as the volume RE:
  `data/cshell.dll` 678700ff…, `data/object.lto` b1271f37…, `lithtech.exe` 4e9ddd2b…. Addresses below are virtual
  addresses in these files. The shipped `cshell.dll` is the GOG/patched one (MP3 soundtrack, main-menu music).

## 1. Ambient sounds

### What emits them

| Source | Count | Positional | Notes |
| --- | --- | --- | --- |
| DAT class `AmbientSound` | 1378 in 41 maps | object position, distance falloff, **no pan** | the main source; properties below |
| DAT `Fire`, `Brazier`, `WallTorch`, `Torch` (`SoundFile`, `SoundRadius`) | 170 / 260 / 246 / 76; 668 with a file and radius (Fire 98, Brazier 248, WallTorch 246, Torch 76) | at the fire | nearly all `Sounds\ambient\torchlight.wav` at 200 LT (8 `inferno.wav` at 400). `object.lto` Fire ReadProp `0x1006b920` reads `SoundRadius` (default 200, `0x1006be58`) and `SoundFile` into the fire effect sent to the client. The four classes have the same property set; that the torch classes share Fire's sound path is inferred, not traced. |
| Scripts: `PlaySound file, label, inner, outer, loop, volume` | many (event one-shots, voices) | at the script's object | ambience-like: `DungeonJukebox.scr` (Anskram Keep: a random creak/owl/thunder/taunt every 2-8 minutes, placed 1 unit behind the player, radius 1/500), `Spook.scr` (Inventa Storca, the same idea plus 5 triggers), `Bell.scr`/`DingTheBell.scr`/`BellWeight.scr` (Guberland, Thjorgard), `LindisfarneBell*.scr` (monastery), `DrainWater.scr` (fountain loops) |
| DAT `Trigger` `ActivationSound` + `SoundRadius` | 7 (Thjorgard 1, Training Hall 6) | at the trigger | one-shot when the trigger fires |
| `WeatherMan.AmbientSound` | 12 objects, all empty | - | WeatherMan can switch a named AmbientSound with the weather (`object.lto` `0x100876e0` on, `0x10087720` off); no map uses it |
| `WorldProperties` music/ambient lists | none | - | `object.lto` still knows Lithtech's DirectMusic world properties (`MusicDirectory`, `InstrumentFiles`, `AmbientList`, `CruisingList`, `HarddrivingList`, `CDTrack`, `0x101aa9cc`…), but no MM9 WorldProperties carries them |

No DAT object has a music, reverb or EAX property, and no script has a music or reverb command (`grep` of all 804
scripts: no `Music`, `CDTrack`, `PlayTrack` or `SoundTrack` command).

### AmbientSound properties (all 1378 objects)

| Property | `object.lto` member | Values (count) |
| --- | --- | --- |
| `Filename` | `+0x474` | 188 files; `waves02` 181, `Canyon_wind02` 158, `torchlight` 96, `INT_AMB01` 70, `waterlap03` 61 |
| `InnerRadius` / `OuterRadius` (LT) | `+0x484` / `+0x488` | inner 250 (338), 150, 100, 400 …; outer 500 (200), 1200 (183), 1500 (120), 450, 2000 … up to 20000 |
| `Volume` (0-100, float bits) | `+0x494` | 100 (498), 80 (179), 40 (161), 65 (116), 90 (70) … 10 (32) |
| `Loop` | `+0x471` | 1 (1354), 0 (24) |
| `LoopCount` | `+0x478` | 0 (1343), 1.0 (35) |
| `LoopWaitMin` / `LoopWaitMax` (s) | `+0x47c` / `+0x480` | 0/0 on 1093; else 2-60 typical, up to 120 |
| `DayOnly` / `NightOnly` | `+0x498` / `+0x499` | 78 / 49; both set on 2 (Guberland City) |
| `StartOn` | `+0x470` | 1 (1337), 0 (41) |

ReadProp is `0x10077500`; it clears `DayOnly` when `NightOnly` is also set (`0x100775ed`), so both means night only.

### Falloff, panning, distance

From the volume RE (`lithtech.exe` `0x4622c5`, `0x462f15`-`0x462fb4`): a plain 2D Miles sample, centred (no pan, no
3D provider), volume updated every frame as `Volume * scale` with `scale` 1 inside the inner radius, 0 beyond the
outer radius and linear between. The sample keeps running at zero volume out of range, so loops and waits continue
while the party is away. No occlusion: walls do not matter.

### Looping, one-shots and waits (`object.lto`)

- **TurnOn** `0x10077410` (an `On` trigger, or WeatherMan): if the sound is off, mark it on, reset its play count and
  play it. When `Loop` is set, `LoopCount` is 0 and both waits are 0 it is started as a real Miles loop and the object
  stops updating; otherwise it is a one-shot and the object updates every 0.5 s. `TurnOff` `0x100774c0` kills the sample.
- **Play** `0x10077750`: only while on; checks day/night (below); then `0x100d7b20(pos, file, inner, outer, …, loop,
  volume)`.
- **Tick** `0x10077600` (from the server's ambient list, `0x1000a060`): when the sample has finished, count it; if
  `LoopCount` > 0 and `LoopCount >= count`, turn the sound off (so any `LoopCount` plays exactly once per switch-on);
  if a wait is set, draw `min + rand() / 32767 * (max - min)` seconds once and wait it out; then play again as a one-shot.
  StartOn sounds start here: the initial update (`0x100771c5`) calls TurnOn, which is a no-op because ReadProp already
  set the on flag, so the first tick finds no sample and starts it.
- `Loop 0`: played once when turned on (24 sounds: The Arena's 20 cheers, two Sturmford and two Thjorgard one-offs).

### Day and night

`0x10077930` reads the clock's 12-hour form (`0x10055d80`, `0x10056160`: hour 0 is 12 AM, 12 is 12 PM) and calls it
night when `PM && hour12 > 4` or `AM && hour12 < 5`. The intent is night 17:00-05:00; the 12-hour test also makes
the 12:00-12:59 hour night and the 00:00-00:59 hour day. The check runs at every (re)start; a time-of-day handler
(`0x10077850`, called from `0x100098e0`) stops a DayOnly sound at night (and a NightOnly one by day) and restarts the
matching ones.

### Start and stop

- Start: map load (`StartOn 1`), an `On`/`Toggle` trigger message from a DAT `Trigger`, a door/switch link or a script
  (`trigger <handle> on|off`, for example `SvenSpeech.scr` turns `AmbientSound0-7` off), or WeatherMan (unused).
- Stop: `Off`/`Toggle`, `LoopCount` reached, the day/night handler, map exit.
- No volume or zone gates them: there is no "inside a house" or "inside a room" condition. Only the radius matters.

## 2. Music

### What picks the track

The live music manager is `cshell.dll`'s CD/MP3 class (constructor `0x100a98f0`, global `0x1017361c`, per-frame update
`0x100a9a40` from `0x1009d637`). The older Redbook `MusicMan.cpp` class (`0x10025570`) is still in the file, but its
creation call at `0x1009c522` sits after an unconditional `jmp` and never runs.

- **Per map, from MAPSTATS column D "Music Track".** The loader `0x100466c0` reads columns by spreadsheet letter (`A`,
  `B`, `C`, `AG`, `D` -> record `+0x14`, `E` -> `+0x18`, `L`, `M`, `N`, `O`, `P`, `S`, `V`, `AH`). The columns
  "Redbook Track" (AB) and "EAX Environments" (AC) are never read. `0x100a9f50` looks up the current world name and,
  for a track `N >= 2`, stores index `N - 2`; `0x100a9ba0` plays `songs[index]` from the table at `0x100d87d8`
  (`Music\MM9-Song01.mp3` at index 0, through Song17 at index 16) through the client call `+0x384` (`lithtech.exe`
  `0x466240`: `AIL_open_stream`, volume, `AIL_start_stream`, no loop count). **Music Track N plays MM9-Song(N-1)**: the
  column counts CD tracks, and track 1 of the CD was data.
- A track below 2 (blank: Temple of Honk) changes nothing, so the previous map's song is played again from the start.
  A map with no MAPSTATS row gets no music.
- **Combat:** when the party's danger state (`0x1001d8a0`: `[[0x100d9f70]+0x284]+0x68`; 2 is the state that also
  refuses saving with "There are monsters nearby!") becomes 2, `0x100a9f10` remembers the map song's position
  (`+0x3a4`), stops it and plays the battle song, index 2 = **MM9-Song03** (hard-coded in the constructor; MAPSTATS
  "Battle Track" is ignored). The battle song repeats while the state stays 2. When the state drops to 0 or 1 it fades
  out (`0x100a9ff0`, `0x100aa030`: 30 MusicVolume units per second, about 2.5 s from the default 75), then the map song
  resumes **at the remembered position** (`0x100a9cb0`, `+0x3a8`) and fades in at the same rate (`0x100aa0e0`).
- **Repeat:** the map song is played once; when it ends, the manager waits **10 s** (`+0x2c` = 10000 ms) and starts
  it again (`0x100a9b40`). On entering a map the old song stops and the new one starts at once (`0x100a4abc`,
  `0x100a4ac7`): no crossfade.
- **Main menu:** index 13 = MM9-Song14 (`+0x10` = 13; the patch note "Added music to the main menu" in `Update.txt`).
- **Pauses:** the pause menu (`0x10037819`), losing the window (`0x1009dbdb`) and two unidentified UI paths pause and
  resume the music (`+0x388`/`+0x38c`). No dialogue, shop or house path was found.
- Not used: zones, triggers, scripts, day/night, houses. The dormant `0x100a96c0` switches Lithtech's DirectMusic
  intensity lists (`SilenceList`, `AmbientList`, `CruisingList`, `HarddrivingList`, `*.sec` segments); no map feeds it.
- **Volume:** `MusicVolume` (shipped 75) through `+0x398`; the old CD line is in the volume RE. The unused
  `Sounds\Battle Music\battleintro/loop/outro.wav` belong to the dead `MusicMan.cpp` class.

### Songs and where they play

| Song | Music Track | Maps |
| --- | --- | --- |
| Song01 | 2 | Ruined Temple |
| Song02 | 3 | Anskram Keep, Lindisfarne Monastery |
| Song03 | 4 | The Arena; also the battle song everywhere |
| Song04 | 5 | Chasm of the Dead, The Afterworld, The Bathhouse |
| Song05 | 6 | Lindisfarne, Yorwick |
| Song06 | 7 | Sturmford City, Sturmford, Guberland City, Guberland, Ravensford (and Temple of Honk, inherited from Guberland) |
| Song07 | 8 | Thjorgard City, Thjorgard, Arslegard City, Hall of the Gods |
| Song08 | 9 | Frosgard City, Frosgard, Yanmir's Fort |
| Song09 | 10 | Verhoffin Ruins, Beet Hoven, Dook's Castle |
| Song10 | 11 | Lich Lab, Wizard's Lab, Dragon's Lair |
| Song11 | 12 | Drangheim City, Drangheim |
| Song12 | 13 | Isle of Ashes, Kluso's House, Dungeon of Secrets |
| Song13 | 14 | Thronheim City, Thronheim, Inventa Storca |
| Song14 | 15 | Training Hall, Ta'Sar Academy; the main menu |
| Song15 | 16 | Connecting Tunnels, Mountain Pass, Drangheim Prison |
| Song16 | 17 | Thjorad Mine, Dark Passageway |
| Song17 | 18 | Thousand Terrors |

## 3. Houses and interiors

MM9's houses and shops are rooms of the same world, and nothing changes when the party walks in:

- **Music:** unchanged (per map only; section 2).
- **Ambience:** unchanged except by distance. Sounds placed inside houses (Guberland City's `snore_loop1` x4,
  Kluso's House's `fireplaceloop02`, the INT_AMB beds) are heard through the walls within their radius.
- **Reverb:** each map has a Creative EAGLE file `mm9/game/EAL/<Map>.eal` (RIFF `eal `: environment names, geometry,
  materials) loaded by `lithtech.exe`'s EAX manager (`EaxMan.dll`, `.eal`, `CSoundMgr::SetReverbProperties`).
  Interiors have their own environments: Guberland City `Small Building`/`Large Buildings`/`World`, Sturmford City
  `LargeBuildings`/`Tent`/`ChurchNCastle`, Thjorgard City `LargeBuildings`/`SmallBuildings`, Drangheim `House`, Frosgard
  City and Yorwick `SmallRoom`/`LargeRoom`; Dark Passageway has 31 and Ta'Sar Academy 13. It needs EAX hardware and
  `EaxEnable 1`; the shipped `autoexec.cfg` has `"EaxEnable" "0.000000"`, and current Windows has no hardware EAX,
  so by default MM9 plays no reverb anywhere.

## 4. The rework

### What the converter and engine do

State after the gap fixes of 2026-11-06 (the list below says which).

- **AmbientSound -> scene `ambient_sounds`** (`level_generation/projects/mm9r_common/dungeon/ambient.py`
  `ambient_sounds`): file by path or name under `worlds/mm9/audio`, radii x 2.56, volume `Volume / 127 * 2/3`,
  `loop` off for `Loop 0` or `LoopCount >= 1`, `wait`, `day_only` / `night_only` (both set: `night_only`, as MM9),
  `start_on: false`. 1378 DAT sounds -> 1326 in the 44 installed scenes; the 52 dropped name files MM9 does not ship
  either (`bird01-17`, `rodents/batflap*`, `invisibiltiy/loop`, `canyonwindloop`).
- **Fires:** `ambient.fire_sounds` carries every Fire, Brazier, WallTorch and Torch with a `SoundFile` and
  `SoundRadius` (inner a quarter, full volume, key the DAT index): on as its `On` says; one the map's hooks placed as
  a decoration with a cog follows that decoration's `evt.SetSprite` (scene `sprite`); a touch Trigger that sends it
  On/Off/Toggle switches it as an AmbientSound (`objects.ambient_triggers`): all 668 in the 44 scenes (48 before),
  15 of them by `sprite`. The engine still does not play the
  decoration table's `SoundId` column (0 on the MM9 torch rows anyway).
- **Switching:** `objects.py` `ambient_triggers` (event 903, a 4 Hz poll) and the per-map Lua set the map variable
  `AmbientSound<key>`; the engine reads it, then the `sprite` decoration's state
  (`game/audio/WorldAmbientSounds.cpp` `worldAmbientSoundEventSwitch`).
- **Engine playback** (`WorldAmbientSoundRuntime::update`): positional through `GameAudioSystem::playAssetInstance`
  with inner/outer linear falloff; started at the outer radius, stopped beyond 1.1 x outer, waits re-drawn on arrival;
  `loop: false` plays once per arrival. The world's rules (`world.yml` `ambientSounds`, devdocs/AMBIENT_SOUNDS.md):
  MM9 has day 05:00-17:00 and no panning (`pan: false`: `Engine::AudioSystem::PlaybackOptions::pan`); worlds without
  the block keep 06:00-20:00 and panning.
- **Scripted ambience:** Spook (Inventa Storca), the bells (Guberland, Lindisfarne Monastery), Anskram Keep's
  DungeonJukebox (a random sound of its list every 2-8 minutes, `mm9r_anskramkeep/convert.py` `script_jukebox`) and
  the event one-shots are in the map Lua (`evt.PlaySoundName`). Training Hall's chandelier plays all six of its
  triggers' ActivationSounds at MM9's SendDelays; Thjorgard's JumperWarningTrigger0 plays `rubble.wav` once
  (`mm9r_thjorgard_blv/regionlua.py`).
- **Music:** `tools/mm9_import_discovery/import_mm9_world_music.py` copies `MM9-SongNN.mp3` to
  `worlds/mm9/music/900NN.mp3`, and the MM9 rows of `engine/data_tables/map_stats.txt` (9001-9080, column "Redbook
  Track") hold `90000 + Music Track - 1` (`generate_mm9_map_stats_encounters.py`, which also writes the converters'
  frozen `original_tables/map_stats.txt`). `GameApplication` (`setBackgroundMusicTrack(map.redbookTrack, gap)`) plays
  it on load; `GameAudioSystem` fades in 1.25 s and out 0.6 s on a change and stops for track 0. `world.yml` `music`
  (MM9's): `repeatGapSeconds: 10` (`MusicStream` writes the silence after each pass), `battleTrack: 90003` and
  `battleFadeSeconds: 2.5` (`GameAudioSystem::setBattleMusic`: under the party's yellow alert, a hostile monster that
  has seen the party within 5120, the map's track is paused and the battle song plays; after the alert it fades out
  over 2.5 s and the map's track resumes where it stopped, fading in as fast; a map track asked for meanwhile starts
  after it). `musicAreas` and `ambience` exist but MM9 uses neither. A house with a video pauses the music (and the
  battle music); MM9's venues are walk-in and have no house video.
- **Reverb:** none in the engine.

### Gaps

| # | MM9 | Rework | Status |
| --- | --- | --- | --- |
| G1 | Music Track N plays Song(N-1) | map_stats holds `90000 + N - 1`; Thousand Terrors plays `90017` (Song17) | **fixed** 2026-11-06 (generator; every MM9 row checked against the table below) |
| G2 | blank Music Track (Temple of Honk) keeps the previous map's song | Temple of Honk has Guberland's song, `90006` (Song06): its only entrance is Guberland's, so it is what MM9 plays, and it also plays after loading a save there | **fixed** (data, `MAPSTATS_MUSIC_FROM`) |
| G3 | battle song (Song03) while monsters are near, fade out, map song resumes where it left off | `world.yml` `music.battleTrack` under the yellow alert; 2.5 s fade out, map song resumed at its position and faded in | **fixed** (MM9 only; the signal is the engine's yellow alert: what sets MM9's danger state 2 was not traced) |
| G4 | song once, then 10 s silence, then again | `music.repeatGapSeconds: 10` | **fixed** (MM9 only) |
| G5 | map change: hard cut | 0.6 s fade out, 1.25 s fade in | accepted |
| G6 | ambient sounds centred, no pan | `ambientSounds.pan: false` | **fixed** (MM9 only) |
| G7 | night 17:00-05:00 (with the 12:00 and 00:00 hour quirk) | `ambientSounds.dayHours: [5, 17]`, without the quirk | **fixed** (MM9 only) |
| G8 | `DayOnly` + `NightOnly` = night only (2 sounds) | `night_only` | **fixed** (converter; Guberland City) |
| G9 | Brazier/WallTorch/Torch torchlight within 200 LT (570 placements) and the 50 switched, scripted or placed Fires | all carried (`ambient.fire_sounds`); scripted ones follow their decoration's cog or a touch Trigger, else their `On` | **fixed** (converter); a scripted fire with no cog-placed decoration that its map's own Lua lights (1000 Terrors' CastingSmoke, Thjorad Mine's PressuredWater, the Afterworld's six fires) keeps its `On` state until that Lua sets `AmbientSound<key>` |
| G10 | 6 ambient placements whose files MM9 ships outside `ambient/` | imported (`import_mm9_world_audio.py`, which since 2026-11-08 imports every MM9 sound) | **fixed** |
| G11 | `Loop 0` and `LoopCount` sounds play once per switch-on, in or out of range; sounds and waits run out of range | `loop: false` plays once per arrival; out-of-range sounds stop and restart | open (accepted for now) |
| G12 | Anskram Keep DungeonJukebox (random sound every 2-8 min behind the player) | map Lua timer + `evt.PlaySoundName` (its 8 shipped sounds) | **fixed** |
| G13 | Trigger ActivationSound (Thjorgard 1, Training Hall 4 of 6 missing) | all 7 played | **fixed** |
| G14 | EAX reverb zones per interior, off by default | none | open (low priority) |
| G15 | houses change nothing | nothing changes (no house screen for MM9 venues) | - |
| G16 | interiors inconsistent: 2 of 9 taverns, 3 of 8 smithies, 5 of 8 temples, 1 of 9 magic shops have a fitting sound | carried as MM9 has it | findings only: [MM9 ambient consistency](MM9_AMBIENT_CONSISTENCY.md) |

## 5. Per-map table

"Kind" is MAPSTATS `InTown` (1 town, 2 dungeon, 0 other). "Fire-family sounds" counts Fire/Brazier/WallTorch/Torch
objects with a `SoundFile` and `SoundRadius`; "carried" is how many the converter carries now (`fire_sounds` in the
map's build report). "Rework plays" and "Scene sounds" are after the 2026-11-06 fixes: the map_stats track, and the
review roots' scene `ambient_sounds` (`output/mm9_rework/assets_dev`, the regions' `isleofashes_blv_root`;
AmbientSounds plus fires; not yet promoted). Radii are MM9 units (x 2.56 for native).

| Map | Kind | Music Track: MM9 plays | Rework plays | Ambient | Off at start | Day / night | Waits | Fire-family sounds (carried) | Scene sounds | Outer radius median / max (LT) | Main sounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Thousand Terrors | dungeon | 18: Song17 | 90017 (Song17) | 28 | 1 | 0 / 0 | 9 | 50 (50) | 78 | 800 / 20000 | torchlight x8, campfireloop x7, int_amb04 x3 |
| The Afterworld | other | 5: Song04 | 90004 (Song04) | 10 | 0 | 0 / 0 | 7 | 7 (7) | 10 | 15000 / 15000 | errie_wind x3, thunder distant01, thunder distant02 |
| Anskram Keep | dungeon | 3: Song02 | 90002 (Song02) | 6 | 0 | 0 / 0 | 4 | 109 (109) | 115 | 1000 / 1000 | rats03 x4, dungeon x2 |
| Arslegard City | town | 8: Song07 | 90007 (Song07) | 20 | 0 | 0 / 0 | 9 | 2 (2) | 20 | 1000 / 2000 | windlarge x5, birds01 x3, birds02 x2 |
| The Bathhouse | other | 5: Song04 | 90004 (Song04) | 18 | 1 | 0 / 0 | 0 | 10 (10) | 28 | 500 / 1000 | steamhissloop x6, waterlap02 x6, waterdrop x2 |
| Beet Hoven | dungeon | 10: Song09 | 90009 (Song09) | 193 | 0 | 0 / 0 | 7 | 21 (21) | 214 | 500 / 2000 | int_amb01 x70, waterlap03 x61, waterflow01 x21 |
| Ravensford | blank | 7: Song06 | 90006 (Song06) | 20 | 0 | 9 / 6 | 15 | 1 (1) | 14 | 2400 / 4500 | single_cricket x6, waves02 x2, waves-ocean02 x2 |
| Chasm of the Dead | dungeon | 5: Song04 | 90004 (Song04) | 18 | 0 | 0 / 0 | 9 | 0 (0) | 18 | 1500 / 5000 | rockscrumblingloop x9, int_amb_spooky01 x6, wind-canyonloop x3 |
| Connecting Tunnel | dungeon | 16: Song15 | 90015 (Song15) | 73 | 0 | 6 / 3 | 7 | 0 (0) | 72 | 500 / 2200 | torchlight x44, int_amb_spooky01 x11, int_amb04 x4 |
| Dark Passageway | dungeon | 17: Song16 | 90016 (Song16) | 115 | 1 | 0 / 0 | 0 | 0 (0) | 115 | 450 / 3000 | canyon_wind02 x112, rushing_river, waterfall01 |
| Dook's Castle | other | 10: Song09 | 90009 (Song09) | 25 | 0 | 0 / 0 | 25 | 30 (30) | 47 | 800 / 800 | woodcreak2 x6, woodcreek x6, batflap06 x4 |
| Dragon's Lair | dungeon | 11: Song10 | 90010 (Song10) | 5 | 0 | 0 / 0 | 2 | 0 (0) | 5 | 2000 / 2000 | canyon_wind02 x3, rat squeek 01, rat squeek 03 |
| Drangheim | other | 12: Song11 | 90011 (Song11) | 0 | 0 | 0 / 0 | 0 | 5 (5) | 5 | - | - |
| Drangheim City | town | 12: Song11 | 90011 (Song11) | 7 | 0 | 0 / 0 | 7 | 6 (6) | 10 | 1200 / 3000 | bird08 x2, single_cricket x2, bell |
| Drangheim Prison | dungeon | 16: Song15 | 90015 (Song15) | 0 | 0 | 0 / 0 | 0 | 77 (77) | 77 | - | - |
| Dungeon of Secrets | dungeon | 13: Song12 | 90012 (Song12) | 31 | 4 | 0 / 0 | 4 | 20 (20) | 51 | 600 / 8000 | steamhissloop x10, machinery ambience x10, rat squeek 01 x3 |
| Frosgard | other | 9: Song08 | 90008 (Song08) | 1 | 0 | 0 / 0 | 0 | 0 (0) | 0 | 1000 / 1000 | loop |
| Frosgard City | town | 9: Song08 | 90008 (Song08) | 10 | 0 | 0 / 0 | 1 | 0 (0) | 10 | 10000 / 10000 | errie_wind x3, monks chanting x2, whistling_wind x2 |
| greatgate | blank | no MAPSTATS row: silent | not converted | 0 | 0 | 0 / 0 | 0 | 0 (0) | - | - | - |
| Guberland | other | 7: Song06 | 90006 (Song06) | 59 | 0 | 16 / 3 | 29 | 0 (0) | 46 | 1500 / 2500 | waves02 x22, crowdnoise-ambience loop 02 x7, goose honk x6 |
| Guberland City | town | 7: Song06 | 90006 (Song06) | 24 | 1 | 9 / 8 | 17 | 0 (0) | 24 | 1500 / 10000 | waves02 x5, single_cricket x4, snore_loop1 x4 |
| Hall of the Gods | other | 8: Song07 | 90007 (Song07) | 23 | 0 | 0 / 0 | 0 | 22 (22) | 44 | 4000 / 4000 | whistling_wind x21, loop, wind01 |
| Inventa Storca | dungeon | 14: Song13 | 90013 (Song13) | 51 | 0 | 0 / 0 | 4 | 65 (65) | 116 | 500 / 2000 | torchlight x44, rockscrumblingloop x4, wind02 x3 |
| Isle of Ashes | other | 13: Song12 | 90012 (Song12) | 176 | 0 | 3 / 0 | 3 | 2 (2) | 176 | 1200 / 2800 | waves02 x134, canyon_wind02 x32, seagulls 02b x7 |
| Kluso's House | other | 13: Song12 | 90012 (Song12) | 5 | 0 | 1 / 0 | 1 | 3 (3) | 8 | 320 / 320 | fireplaceloop02 x3, crowdnoise-ambience loop 02, birds14 |
| Lich Lab | dungeon | 11: Song10 | 90010 (Song10) | 45 | 2 | 0 / 0 | 0 | 1 (1) | 46 | 1200 / 3000 | int_amb02 x21, purplethingy2launch x6, eqhammerpostimpactloop x5 |
| Lindisfarne | other | 6: Song05 | 90005 (Song05) | 44 | 0 | 15 / 7 | 22 | 3 (3) | 47 | 2000 / 6600 | waves02 x16, waterlap02 x6, owl02 x6 |
| Lindisfarne Monastery | other | 3: Song02 | 90002 (Song02) | 7 | 0 | 0 / 0 | 3 | 22 (22) | 27 | 1000 / 2000 | monks chanting x3, fountain05, bird01 |
| Mountain Pass | other | 16: Song15 | 90015 (Song15) | 9 | 0 | 0 / 0 | 0 | 1 (1) | 10 | 20000 / 20000 | wind-canyonloop2 x9 |
| Ruined Temple | dungeon | 2: Song01 | 90001 (Song01) | 5 | 0 | 0 / 0 | 0 | 0 (0) | 5 | 10000 / 10000 | int_amb02 x5 |
| Sturmford | other | 7: Song06 | 90006 (Song06) | 44 | 2 | 3 / 7 | 22 | 4 (4) | 32 | 2500 / 7000 | waves-ocean01 x21, wolf howl (distance) x4, owl01 x3 |
| Sturmford City | town | 7: Song06 | 90006 (Song06) | 6 | 0 | 0 / 0 | 3 | 25 (25) | 29 | 900 / 1000 | monks chanting x2, bird02, bird06 |
| Ta'Sar Academy | dungeon | 15: Song14 | 90014 (Song14) | 9 | 0 | 0 / 0 | 1 | 50 (50) | 59 | 650 / 5000 | wind_trees x8, churchbellring |
| Temple of Honk | other | none: previous map's song continues | 90006 (Song06) | 4 | 0 | 0 / 0 | 0 | 60 (60) | 64 | 400 / 400 | waterlap02 x4 |
| The Arena | town | 4: Song03 | 90003 (Song03) | 30 | 20 | 0 / 0 | 0 | 14 (14) | 44 | 1200 / 1200 | crowdnoise-cheer01 x20, crowdnoise-ambience loop 01 x10 |
| Thjorad Mine | other | 17: Song16 | 90016 (Song16) | 26 | 0 | 0 / 0 | 25 | 4 (4) | 30 | 2500 / 2500 | eqhammerpostimpactloop x9, rat squeek 01 x4, rat squeek 02 loop x3 |
| Thjorgard | other | 8: Song07 | 90007 (Song07) | 61 | 0 | 6 / 2 | 18 | 3 (3) | 46 | 1300 / 5000 | waves-ocean02 x35, crowdnoise-ambience loop 02 x4, thunder distant02 x3 |
| Thjorgard City | town | 8: Song07 | 90007 (Song07) | 11 | 0 | 0 / 0 | 2 | 6 (6) | 17 | 1200 / 1200 | canyon_wind02 x6, crow02 x2, waves02 x2 |
| Thronheim | other | 14: Song13 | 90013 (Song13) | 0 | 0 | 0 / 0 | 0 | 2 (2) | 2 | - | - |
| Thronheim City | town | 14: Song13 | 90013 (Song13) | 15 | 0 | 0 / 5 | 11 | 4 (4) | 19 | 500 / 1000 | dog13 x3, cricket x3, hammer hitting anvil x2 |
| Training Hall | dungeon | 15: Song14 | 90014 (Song14) | 19 | 4 | 2 / 2 | 2 | 30 (30) | 49 | 350 / 3000 | steamhissloop02 x10, birdsloop x2, owl x2 |
| Verhoffin Ruins | dungeon | 10: Song09 | 90009 (Song09) | 26 | 1 | 0 / 0 | 3 | 7 (7) | 33 | 750 / 2500 | gusty_wind x10, waves-ocean02 x7, waterdrop x3 |
| Wizard's Lab | dungeon | 11: Song10 | 90010 (Song10) | 34 | 4 | 0 / 0 | 0 | 0 (0) | 34 | 1000 / 1500 | magic-loop x14, magnetpostimpactloop x13, doorslammetal01 x2 |
| Yanmir's Fort | dungeon | 9: Song08 | 90008 (Song08) | 21 | 0 | 0 / 0 | 0 | 0 (0) | 19 | 4000 / 4000 | dungeon x17, loop x2, wind-whistling x2 |
| Yorwick | other | 6: Song05 | 90005 (Song05) | 44 | 0 | 6 / 6 | 12 | 2 (2) | 46 | 2000 / 6000 | gusty_wind x12, waves-ocean02 x8, canyon_wind02 x8 |

Examples by map type:

- **Town** (Guberland City): 24 sounds, half of them timed (crickets, owls and a snoring house at night, birds by
  day), waves on the shore with 1500 LT outer radii, one 10000 LT bed; Song06.
- **Dungeon** (Beet Hoven): 193 small beds (`INT_AMB01` x70, `waterlap03` x61, `waterflow01` x21) at 500 LT, almost
  all continuous; Song09. Dungeons with fire-family objects (Anskram Keep 109, Drangheim Prison 77) get most of their
  ambience from torch crackle, which the rework does not carry (G9).
- **Region** (Isle of Ashes): 176, mostly `waves02` along the coast (134) and `canyon_wind02` (32), 1200-2800 LT;
  Song12.
