# MM9 monster and NPC sounds

How Might and Magic IX gives a creature its sounds, and how the OpenYAMM MM9 world plays the same files on its 3D
monsters and townsfolk. Tool: `tools/mm9_import_discovery/generate_mm9_monster_sounds.py`.

## 1. MM9's rule

MM9 has no per-monster sound table. Every creature sound is keyed to an animation of its model (`MODELS/*.abc`): a
keyframe string names a command, and the client builds the file from the row's `MONSTERS.txt` columns and the
animation's own name.

| Key (frame string) | File | Evidence |
|---|---|---|
| `PlayAnimSound` | `sounds\animSounds\<BaseName>\<animation>.wav` | `cshell.dll` dispatch `0x1005b040` -> `0x1005c970`, path builder `0x10046230` (`sounds\animSounds\%s\%s.wav`); `object.lto` `0x10044830` builds the same string for precaching |
| `SpeakAnimSound` | the same file, as the creature's voice (a new line replaces the previous one) | `cshell.dll` `0x1005ced0`: the same builder, after stopping the speaker's current sound |
| `PlaySoundFX`, `PlayAnimFX` | `sounds\animSounds\<BaseName>\FX_<animation>.wav` (the weapon's swish) | both keys go to `cshell.dll` `0x1005cc20`; format `sounds\animSounds\%s\FX_%s.wav` |
| `PlayDeathSound` | `sounds\DeathSounds\<BaseName>\<animation>.wav` (the body hitting the floor) | `cshell.dll` `0x1005d190`; `object.lto` precache `0x10008184` for animations named `DIE*`/`FALLDOWN*` |
| `Flap` | `sounds\animSounds\<BaseName>\Flap.wav` | `cshell.dll` `0x1005b250` (builder called with the name `Flap`) |
| `Footstep` | `sounds\animsounds\footsteps\<FootSound><n>.wav`, n cycling 1..count | `cshell.dll` `0x1005b3f0`: index `[+0x184]` advances modulo the found count `[+0x188]`; builder `0x10046580` (`%s%s%d.wav`); `object.lto` precaches n = 0..4 (`0x10008221`) |

- `BaseName` (column 66) names the folder: Nobleman, Guard, PeasantFemale, Banshee... `FootSound` (54) is the step
  prefix (`dirt` -> `DIRT1-4`, `GuardStep` -> `GUARDSTEP1-4`; `0` or empty: no steps), `FootRadius` (55) and
  `Voice Radius` (79) the audible radii.
- So the attack sound is whatever the attack animation keys (Hattack1: a `SpeakAnimSound` grunt and a `PlaySoundFX`
  swish), the hit sound the wince animation's key, the death the die animation's `PlayAnimSound` scream and later its
  `PlayDeathSound` fall, aware/taunt/fidget/fly/resurrect the keys of those animations, and the steps the walk and run
  keys. An animation without a key is silent, and a key whose file MM9 does not ship plays nothing (LithTech skips a
  missing file).
- Script idle sounds: two include files play sounds on model keys that are not client commands. `GuardSounds.inc`
  (`GuardBase`, `GuardHelp`, `GuardRude`, `Jeff`): `OnStand` (the `Stand` key of stand and walk) plays one of
  `Stand1-7` with chance 7/20 and waits 1.2 s, else waits 50 s; `OnSleep` plays one of `Sleep1-4`, then waits 5 s.
  `MonkSounds.inc` (`MonkBase`, `MonkGuardBasic`, `ThjoradMonk`, `WorkingMonk`): `OnPray` (key `PrayMumble`, on
  `MONK.abc`'s `pray` and `fidget1`; read as `pray` until 2026-11-10, so no prayer played) 4/10 `Pray1-4` then 2.2 s,
  else 20 s; `OnSweep` `Sweep` then 1 s; `OnWash` `Wash` at volume 10 and 1/10 `WashFidget` then 5 s.
- Camera shakes (2026-11-11): three keys shake the view instead of playing a sound, `BigEQ`, `SmallEQ` and
  `SmallerEQ` (`cshell.dll` dispatch `0x1005b16d` -> `0x1005d260`/`0x1005d2d0`/`0x1005d340` -> `0x100ab070`). Each
  passes MM9 constants: radius 6000 / 1200 / 900, amplitude at the radius 1 / 1 / 0.5 and at the model 6 / 4 / 2
  (linear between, nothing beyond the radius; the distance is the camera's to the model), full for 1.3 / 0.4 / 0.25 s,
  then decaying by 10 / 20 / 30 per second (the EarthQuake client shake, MM9_CUTSCENES.md section 1). Only three
  models key them: `DRAGON.abc` (`land` at touchdown, `die1`), `GIANT.abc` (`walk`, `run`, `Hattack1`: Small;
  `die1`, `die2`: Big) and `YANMIR.abc` (`walk`, `run`, `HAttack1`, `KickDoor`, `StepOn`, `rAttack2`). MM9's
  projectile table shakes too (`EQ` columns: lightning and the red and yellow beams within 35 units of the impact,
  the player's EQ hammer and grenade within 360); those are not carried.
- Not row sounds: map scripts' own `PlaySound` lines (Yanmir's patrol, the jukeboxes, cutscene `Voice*`/`Speak*` keys)
  belong to their maps' Lua; spells' sounds are the spell system's. `Foostep` (a typo in three models) matches no
  command and is silent in MM9 too.

## 2. OpenYAMM

- **Files:** `import_mm9_world_audio.py` imports `SOUNDS/ANIMSOUNDS` and `SOUNDS/DEATHSOUNDS` whole (WAV, lowercase
  paths) into `assets_dev/worlds/mm9/audio/animsounds` and `.../deathsounds`.
- **Sound ids:** `worlds/mm9/data_tables/sounds.txt` registers every one of those files in the world's `sounds` id
  range (50000-59999, `world.yml`), clear of the engine's ids (at most 46801). The engine reads each mounted world's
  `sounds` table contribution into the world sound scope (`GameAudioSystem::initializeSoundCatalog`) and refuses an id
  outside the range or one the engine table already uses.
- **Animations:** a model plays its own animations and those of the models its ABC `ChildModels` section names
  (RAM.abc plays `sheep.ABC`'s, a townsman `PeasantMale.abc`'s and `Peasantwork.abc`'s); the generator reads both.
- **Clip events:** `worlds/mm9/models/actor_sounds.yml` lists, per descriptor, the timed sound events of its 3D model's
  clips. The generator finds which MM9 animation each of our clips plays by pose signature: per bone (named without
  its skeleton prefix), the angle from the clip's first pose at nine points of the clip, which the creature projects'
  bone-basis changes and mirroring leave unchanged; the median over bones decides (projects re-pose a few arms and
  robes), a duplicate animation (Taunt = Aware) goes to the clip's own name, a static pose (Dead) matches by name
  only, and a clip reworked past the tolerance still takes the animation of its name and length. Key times are scaled
  to the clip's length. A clip the projects stitched from several animations (a flyer's Death: DieAir1, then its
  FallDown) is matched piece by piece, each piece's keys at their own times. Clips made for OpenYAMM (the Green Man's
  attack, hit and death: MM9's model has none) have no events.
- **Playback** (`game/fx/ActorClipSounds.*`, `WorldFxSystem::presentActorClipSounds`): an event plays when its clip
  passes its time, for the full-body clip and an upper-body attack layer, every cycle of a loop; a clip entered
  mid-way plays only that frame's events. `voice` events replace the actor's previous voice line; footsteps take the
  row's step files in turn; script events roll their chance and hold their gates (events of one sound set share a
  gate, as MM9's per-script wait). Sounds are positional within the row's Voice Radius (FootRadius for steps) x 2.56,
  full within a quarter of it (the script sounds: their own radii); none starts beyond its radius.
- **Shakes:** the EQ keys become `shake: {near, edge, seconds, radius}` events on the same clips: intensity amplitude
  / 12 (the client's clamp, as the converters' EarthQuakes), seconds full + amplitude / decay, radius x 2.56. The
  actor's clip events hand them to `WorldFxSystem::takeActorCameraShakes`, scaled by the party's distance as MM9's,
  and the session's `CameraShake` plays them (indoors and outdoors, without audio too).
- **Descriptor slots:** `monster_descriptors.txt` columns AttackSoundId, DeathSoundId, WinceSoundId and AwareSoundId of
  MM9 rows hold the first voice of the bound attack_melee, dying (else its death fall), hit and fidget clips
  (`mm9_monster_sound_slots.tsv`, read by `generate_mm9_monster_tables.py`); 0 where that clip has no MM9 sound.
  They play only when the actor is not drawn by a model with clip sounds (`GameAudioSystem::playActorSound` asks
  `WorldFxSystem::actorPlaysClipSounds`), so a 3D MM9 actor never doubles a sound.
- **Projectile launches** (2026-11-08): MM9 plays a projectile's own `Launch Sound` (`DATA/PROJECTILE.txt`) as it
  leaves the monster; its ranged animations mostly key no sound, so the Bandit's knives, the Gezzampt's lightning and
  every other thrown or shot missile were silent. The generator adds, for each ranged attack of a row (its
  Projectile1/2/3 from `MONSTERS.txt`; `Spell` rows sound as their spell), the projectile's `weapons/<launch>` file to
  that attack's clip (`attack_ranged`, `attack_ranged2`, `attack_ranged3`) at its release (`actors.yml` events
  `<role>: impact`). `weapons/` is registered in the sound table after `animsounds`/`deathsounds`, so their ids did not
  move. Not carried yet: MM9's `In-flight sound` (a loop on the projectile) and `Explosion Sound` (at the impact,
  played where the projectile lands: an engine change keyed to the MM9 row, since MM9's projectiles share MM8's
  missile tokens). MM9 spells keep MM8's spell release sound; MM9's own `CastWav`/`ImpactWav` (`SPELL.txt`) are not
  used.
- MM6-MM8 monsters keep their sounds.txt ids and play exactly as before: they have no clip sounds.

## 3. Silent cells and verification

- All 252 rows are bound; 249 descriptors carry clip sounds (3266 events, 215 with footsteps). No row falls back to an
  MM6-MM8 sound: where MM9 has none the cell is empty. The silent ones are MM9's own silences: the Fish (227, FISH.abc
  has no keys) and both mice (299, 300: no keys and no MOUSE folder); the male townsfolk's wince and death
  (PeasantMale.abc keys only hattack1, and our townsmen attack with hattack2); the Birds (93-95: empty BaseName, so
  `animSounds\\Flap.wav` does not exist); keys whose file MM9 does not ship (`?` cells: the Dagrell's rattack1, the
  townswomen-dwarves' die1, the Eye's fidgetair1). Descriptor slots left 0: attack 71 rows, death 58, wince 56, fidget
  191 (MM9 keys few fidgets).
- `u` cells that matter: the Sea Monsters', Yanmir's and Kira's deaths are reworked past the tolerance, but their MM9
  die animations have no sound keys either; the Green Man's attack, hit and death are OpenYAMM clips.
- Verified 2026-11-07: generator tests (`test_generate_mm9_monster_sounds.py`, `test_generate_mm9_monster_tables.py`,
  `test_import_mm9_world_audio.py`), unit tests `*actor clip*` and `*monster sounds load*` (every world id resolves
  to an existing file; engine id 2900 still resolves to `112noblemana_attack`), and a desktop arena on `thearena.blv`
  (Count 9155 vs Guard Captain 9113, Basilisk 9150 vs Fright 9162, `OPENYAMM_AUDIO_TRACE=1`): the trace played only
  MM9 files (`animsounds/nobleman/hattack1` + `fx_hattack1`, `guard/hattack1` + `fx_hattack1`, `guard/taunt`,
  `nobleman/taunt`, `banshee/fly` and `hattackair1`, `basilisk/hattack1`, `guard/die1` + `deathsounds/guard/die1`,
  `basilisk/die1` + `deathsounds/basilisk/die1`, `footsteps/dirt1-4` and `guardstep1-4` in turn) and no descriptor
  sound. No wince played in that run (the engine staggered nobody).

## 4. Coverage

Every MM9 row (monsters and the NPC rows placed as actors) and the sounds its bound clips play. Cell legend: file names
(the row's folder implied; `death:` a DeathSounds file; `?` a file MM9 names and does not ship, silent in MM9 too);
`k`: the MM9 animation has no sound key (MM9 is silent there too); `n`: the model has no such clip (MM9's model has no
such animation either); `u`: our clip has no single MM9 source animation (stitched or made for OpenYAMM). Steps:
the step prefix and how many files cycle. Other: clips beyond the columns that play sounds, and MM9 animations with
sound keys that no clip of ours plays (`dropped`).

<!-- coverage:begin (generated by generate_mm9_monster_sounds.py) -->

| Row | Name | Sound folder | Attack | Attack 2 | Cast | Hit | Death | Aware | Taunt | Fidget | Steps | Other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Commoner | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 2 | Commoner | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 3 | Town | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 4 | Town | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 5 | Shopkeeper | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 6 | Shopkeeper | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 7 | Prisoner | peasantdf | hattack | hattack | n | wince | death:die1 die1? | n | n | k, k | dirt x4 | - |
| 8 | Commoner | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | Hammer: hammer |
| 9 | Commoner | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | Hammer: hammer |
| 10 | Town | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | dropped: hammer |
| 11 | Town | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | dropped: hammer |
| 12 | Shopkeeper | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | dropped: hammer |
| 13 | Shopkeeper | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | Hammer: hammer |
| 14 | Shopkeeper | peasantdm | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k, k | dirt x4 | Hammer: hammer |
| 15 | Commoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 16 | Commoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 17 | Town | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 18 | Town | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 19 | Shopkeeper | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 20 | Shopkeeper | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 21 | Prisoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 22 | Commoner | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 23 | Commoner | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k | dirt x4 | - |
| 24 | Town | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 25 | Town | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 26 | Shopkeeper | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 27 | Shopkeeper | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 28 | Prisoner | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 29 | Commoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 30 | Commoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 31 | Town | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 32 | Town | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 33 | Shopkeeper | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 34 | Shopkeeper | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 35 | Prisoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 36 | Commoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 37 | Commoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 38 | Town | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 39 | Town | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 40 | Shopkeeper | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 41 | Shopkeeper | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 42 | Prisoner | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 43 | Commoner | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 44 | Commoner | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 45 | Town | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 46 | Town | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 47 | Shopkeeper | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 48 | Shopkeeper | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 49 | Prisoner | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 50 | Commoner | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 51 | Commoner | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 52 | Town | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 53 | Town | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 54 | Shopkeeper | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 55 | Shopkeeper | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 56 | Prisoner | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 57 | Commoner | peasanthom | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k | dirt x4 | - |
| 58 | Town | peasanthom | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k | dirt x4 | - |
| 59 | Shopkeeper | peasanthom | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k | dirt x4 | - |
| 60 | Prisoner | peasanthom | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k | dirt x4 | - |
| 61 | Commoner | peasantfemale | k | k | n | k | k | n | n | k, k, k | dirt x4 | - |
| 62 | Town | peasantfemale | k | k | n | k | k | n | n | k, k, k | dirt x4 | - |
| 63 | Shopkeeper | peasantfemale | k | k | n | k | k | n | n | k, k, k | dirt x4 | - |
| 64 | Prisoner | peasantfemale | k | k | n | k | k | n | n | k, k, k | dirt x4 | - |
| 67 | Commoner Child | peasantboy | hattack1 | hattack1 | n | wince1? | die1 death:die1 | n | n | k, k, k | dirt x4 | - |
| 68 | Townsfolk Child | peasantboy | hattack1 | hattack1 | n | wince1? | die1 death:die1 | n | n | k, k, k | dirt x4 | - |
| 69 | Commoner Child | peasantboy | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k | dirt x4 | - |
| 70 | Townsfolk Child | peasantboy | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k | dirt x4 | - |
| 71 | Commoner Child | peasantgirl | k | k | n | wince | die1 death:die1 | n | n | k, k | dirt x4 | dropped: hattack1 |
| 72 | Townsfolk Child | peasantgirl | k | k | n | wince | die1 death:die1 | n | n | k, k | dirt x4 | dropped: hattack1 |
| 73 | Commoner Child | peasantboy | hattack1 | hattack1 | n | wince | die1 death:die1 | n | n | k, k | dirt x4 | - |
| 74 | Townsfolk Child | peasantgirl | k | k | n | wince | die1 death:die1 | n | n | k, k | dirt x4 | dropped: hattack1 |
| 75 | Dragonfly Mite | dragonfly | hattackair1 flap | rattack1 flap weapons/fireboltlaunch, hattackair2 flap | rattack1 flap weapons/fireboltlaunch | winceair1 flap, flap winceair2 | dieair1, dieair2 | awareair flap | tauntair flap | flap, flap | - | Standing: flap; Walking: flap; Search: flap |
| 76 | Dragonfly | dragonfly | hattackair1 flap | rattack1 flap weapons/yellowthingylaunch, hattackair2 flap | rattack1 flap weapons/yellowthingylaunch | winceair1 flap, flap winceair2 | dieair1, dieair2 | awareair flap | tauntair flap | flap, flap | - | Standing: flap; Walking: flap; Search: flap |
| 77 | Fire Dragonfly | dragonfly | hattackair1 flap | rattack1 flap weapons/redthingylaunch, hattackair2 flap | rattack1 flap weapons/redthingylaunch | winceair1 flap, flap winceair2 | dieair1, dieair2 | awareair flap | tauntair flap | flap, flap | - | Standing: flap; Walking: flap; Search: flap |
| 78 | Imply | imp | hattack2 | weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, fidget2 | impstep x2 | dropped: Hattack1 |
| 79 | Imp | imp | hattack2 | weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, fidget2 | impstep x2 | dropped: Hattack1 |
| 80 | Imp Elder | imp | hattack2 | weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, fidget2 | impstep x2 | dropped: Hattack1 |
| 81 | Nagate Hatchling | nagate | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1 | taunt | taunt | k, fidget2 | spiderstep x2 | dropped: Hattack2 |
| 82 | Nagate | nagate | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1 | taunt | taunt | k, fidget2 | spiderstep x2 | dropped: Hattack2 |
| 83 | Nagate Elder | nagate | hattack1 | rattack1 weapons/redlinelaunch | rattack1 weapons/redlinelaunch | wince1, wince2 | die1 death:die1 | taunt | taunt | k, fidget2 | spiderstep x2 | dropped: Hattack2 |
| 84 | Lobber Pod | lobberpod | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 | n | taunt | fidget | spiderstep x2 | Walking: walk; Projectile: projectile; Land: land |
| 85 | Lobber Pod | lobberpod | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 | n | taunt | fidget | spiderstep x2 | Walking: walk; Projectile: projectile; Land: land |
| 86 | Lobber | lobber | rattack1 weapons/greenyellowthingylaunch | rattack1 weapons/greenyellowthingylaunch | launchpod | winceair2, winceair1 | dieair1 | awareair | n | fidgetair1, fidgetair2 | - | dropped: falldown1 |
| 87 | Airborne Icky | flyingicky | hattackair1 | flap startattackair2 | taunt flap | winceair1 flap, winceair2 flap | dieair1 falldown1, falldown2 | n | n | taunt flap | - | Running: flap; Standing: flap; Walking: flap; HangFidget: hangfidget; Launch: launch flap; dropped: Flap fidgetair1 |
| 88 | Flying Icky | flyingicky | hattackair1 | flap startattackair2 | taunt flap | winceair1 flap, winceair2 flap | dieair1 falldown1, falldown2 | n | n | taunt flap | - | Running: flap; Standing: flap; Walking: flap; HangFidget: hangfidget; Launch: launch flap; dropped: Flap fidgetair1 |
| 89 | Astral Icky | flyingicky | hattackair1 | flap startattackair2 | taunt flap | winceair1 flap, winceair2 flap | dieair1 falldown1, falldown2 | n | n | taunt flap | - | Running: flap; Standing: flap; Walking: flap; HangFidget: hangfidget; Launch: launch flap; dropped: Flap fidgetair1 |
| 90 | Field Thrall | thrall | k | weapons/knifelaunch, k, k | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 91 | Thrall | thrall | k | weapons/knifelaunch, k, k | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 92 | Thrall Master | thrall | k | weapons/knifelaunch, k, k | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 93 | Bird | - | flap? | flap? | flap? | flap?, flap? | k, k | n | n | k | - | - |
| 94 | Bird | - | flap? | flap? | flap? | flap?, flap? | k, k | n | n | k | - | - |
| 95 | Bird | - | flap? | flap? | flap? | flap?, flap? | k, k | n | n | k | - | - |
| 96 | Troglodyte | troglodyte | hattack1 | rattack1 weapons/greenthingylaunch, hattack2 | rattack1 weapons/greenthingylaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | troglodytestep x2 | - |
| 97 | Troglodyte Wren | troglodyte | hattack1 | rattack1 weapons/greenthingylaunch, hattack2 | rattack1 weapons/greenthingylaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | troglodytestep x2 | - |
| 98 | Troglodyte Gnoll | troglodyte | hattack1 | rattack1 weapons/greenthingylaunch, hattack2 | rattack1 weapons/greenthingylaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | troglodytestep x2 | - |
| 99 | Cutpurse | highwayman | hattack1 fx_hattack1 | weapons/knifelaunch, hattack2 fx_hattack2, hattack3 fx_hattack3 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt | k, k | dirt x4 | - |
| 100 | Burglar | highwayman | hattack1 fx_hattack1 | weapons/knifelaunch, hattack2 fx_hattack2, hattack3 fx_hattack3 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt | k, k | dirt x4 | - |
| 101 | Bandit | highwayman | hattack1 fx_hattack1 | weapons/knifelaunch, hattack2 fx_hattack2, hattack3 fx_hattack3 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt | k, k | dirt x4 | - |
| 102 | Half Orc Recruit | dookmilitia | hattack1 fx_hattack1 | weapons/knifelaunch, hattack2 fx_hattack2, hattack3 fx_hattack3 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt? | k, k | dirt x4 | Hit3: wince3 |
| 103 | Half Orc Soldier | dookmilitia | hattack1 fx_hattack1 | weapons/knifelaunch, hattack2 fx_hattack2, hattack3 fx_hattack3 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt? | k, k | dirt x4 | Hit3: wince3 |
| 104 | Half Orc Captain | dookmilitia | hattack1 fx_hattack1 | weapons/knifelaunch, hattack2 fx_hattack2, hattack3 fx_hattack3 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt? | k, k | guardchainstep x2 | Hit3: wince3 |
| 105 | Ice Lobbercicle | lobberpod | hattack1 | rattack1 weapons/fireboltlaunch | rattack1 weapons/fireboltlaunch | wince1, wince2 | die1 | n | taunt | fidget | spiderstep x2 | Walking: walk; Projectile: projectile; Land: land |
| 106 | Ice Lobber | lobber | rattack1 weapons/bluethingy2launch | rattack1 weapons/bluethingy2launch | launchpod | winceair2, winceair1 | dieair1 | awareair | n | fidgetair1, fidgetair2 | - | dropped: falldown1 |
| 107 | Town Guard | guard | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | dirt x4 | - |
| 108 | Town Guard | guard | hattack1 fx_hattack1 | k, hattack2 fx_hattack2, hattack3? fx_hattack3? | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt? | k, k | dirt x4 | - |
| 109 | Town Guard | guard | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | guardstep x4 | - |
| 110 | Town Guard | guard | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | soldierstep x2 | - |
| 111 | Guard | guard | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | dirt x4 | Standing: stand1; Walking: stand1; Sleep: sleep1 |
| 112 | Guard Segeant | guard | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | guardchainstep x2 | Standing: stand1; Walking: stand1; Sleep: sleep1 |
| 113 | Guard Captain | guard | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | guardstep x4 | Standing: stand1; Walking: stand1; Sleep: sleep1 |
| 114 | Grey Wolf | wolf | hattack1 | hattack2 | hattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | k | taunt | k, k | dirt x4 | Trot: hattack2 |
| 115 | Red Wolf | wolf | hattack1 | hattack2 | hattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | k | taunt | k, k | dirt x4 | Trot: hattack2 |
| 116 | Black Wolf | wolf | hattack1 | hattack2 | hattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | k | taunt | k, k | dirt x4 | Trot: hattack2 |
| 120 | Dwarven Guard | dwarf | rattack1 | rattack1 weapons/axelaunch, wattack2, k | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | dwarfstep x2 | dropped: WAttack1 HAttack1 |
| 121 | Dwarven Soldier | dwarf | rattack1 | rattack1 weapons/axelaunch, wattack2, k | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | dwarfstep x2 | dropped: WAttack1 HAttack1 |
| 122 | Dwarven Commander | dwarf | rattack1 | rattack1 weapons/axelaunch, wattack2, k | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | dwarfstep x2 | dropped: WAttack1 HAttack1 |
| 123 | Initiate | monk | hattack1 fx_hattack1 | k | k | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | pray1, fidget2 | monkstep x2 | Pray: pray1; CowerStart: cowerstart; Hoe: hoe; Sweep: sweep; SweepFidget: sweepfidget; Hammer: hammer; HammerFidget: hammerfidget; Wash: wash washfidget; WashFidget: washfidget |
| 124 | Monk | monk | hattack1 fx_hattack1 | k | k | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | pray1, fidget2 | monkstep x2 | Pray: pray1; CowerStart: cowerstart; Hoe: hoe; Sweep: sweep; SweepFidget: sweepfidget; Hammer: hammer; HammerFidget: hammerfidget; Wash: wash washfidget; WashFidget: washfidget |
| 125 | Reverend Monk | monk | hattack1 fx_hattack1 | k | k | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | pray1, fidget2 | monkstep x2 | Pray: pray1; CowerStart: cowerstart; Hoe: hoe; Sweep: sweep; SweepFidget: sweepfidget; Hammer: hammer; HammerFidget: hammerfidget; Wash: wash washfidget; WashFidget: washfidget |
| 129 | Horde Grunt | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | dirt x4 | Block: block; Cower: block |
| 130 | Horde Warrior | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | soldierstep x2 | Block: block; Cower: block |
| 131 | Horde Leader | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | soldierstep x2 | Block: block; Cower: block |
| 132 | Clan Soldier | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | guardchainstep x2 | Block: block; Cower: block |
| 133 | Clan Corporal | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | guardchainstep x2 | Block: block; Cower: block |
| 134 | Clan Sergeant | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 weapons/axelaunch | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | soldierstep x2 | Block: block; Cower: block |
| 135 | Skeleton | skeleton | hattack1 | rattack1 weapons/axelaunch, hattack2 | n | wince1, wince3 | die1 | n | taunt | fidget1, fidget2 | skeletonstep x2 | Fidget3: fidget3; Resurrect: resurrect |
| 136 | Skeleton Warrior | skeletonwarrior | hattack1 | rattack1 weapons/knifelaunch, hattack2 | n | wince1, wince2 | die1, die2 | n | taunt | k, resurrectspell | skeletonstep x2 | Resurrect: resurrect |
| 137 | Skeleton Master | skeletonwarrior | hattack1 | rattack1 weapons/axelaunch, hattack2 | n | wince1, wince2 | die1, die2 | n | taunt | k, resurrectspell | skeletonstep x2 | Resurrect: resurrect |
| 138 | Shadow | ghost | hattackair1 | rattack1, hattackair2 | rattack1 | winceair1, winceair2 | winceair2 | awareair | awareair | fidgetair1, fidgetair2 | - | Standing: standair; Walking: flap; dropped: tauntair |
| 139 | Apparition | ghost | hattackair1 | rattack1, hattackair2 | rattack1 | winceair1, winceair2 | winceair2 | awareair | awareair | fidgetair1, fidgetair2 | - | Standing: standair; Walking: flap; dropped: tauntair |
| 140 | Specter | ghost | hattackair1 | rattack1, hattackair2 | rattack1 | winceair1, winceair2 | winceair2 | awareair | awareair | fidgetair1, fidgetair2 | - | Standing: standair; Walking: flap; dropped: tauntair |
| 144 | Canopic Mummy | mummy | hattack1 | k, hattack2 | k | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1?, fidget2 | dirt x4 | ResurrectSpell: resurrectspell |
| 145 | Embalmed Mummy | mummy | hattack1 | k, hattack2 | k | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1?, fidget2 | dirt x4 | ResurrectSpell: resurrectspell |
| 146 | Petrified Mummy | mummy | hattack1 | k, hattack2 | k | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1?, fidget2 | dirt x4 | ResurrectSpell: resurrectspell |
| 147 | Dagrell | dagrell | hattack1 | rattack1?, hattack2 | rattack1? | wince1, wince2 | wince2 | n | rattack1? | fidget1 | dagrellstep x2 | dropped: Taunt |
| 148 | Venomous Dagrell | dagrell | hattack1 | rattack1?, hattack2 | rattack1? | wince1, wince2 | wince2 | n | rattack1? | fidget1 | dagrellstep x2 | dropped: Taunt |
| 149 | Spectre Dagrell | dagrell | hattack1 | rattack1?, hattack2 | rattack1? | wince1, wince2 | wince2 | n | rattack1? | fidget1 | dagrellstep x2 | dropped: Taunt |
| 150 | Basilisk | basilisk | hattack1 | rattack1 weapons/greenyellowthingylaunch | rattack1 weapons/greenyellowthingylaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | basiliskstep x2 | - |
| 151 | Fibrase Basilisk | basilisk | hattack1 | rattack1 weapons/greenyellowthingylaunch | rattack1 weapons/greenyellowthingylaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | basiliskstep x2 | - |
| 152 | King Basilisk | basilisk | hattack1 | rattack1 weapons/greenyellowthingylaunch | rattack1 weapons/greenyellowthingylaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | k, k | basiliskstep x2 | - |
| 153 | Baron | nobleman | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 154 | Viscount | nobleman | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 155 | Count | nobleman | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 156 | Evil Apprentice | evilsorcerer | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | k | k, k | dirt x4 | - |
| 157 | Evil Sorcerer | evilsorcerer | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | k | k, k | dirt x4 | - |
| 158 | Evil Grand Sorcerer | evilsorcerer | hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | k | k, k | dirt x4 | - |
| 159 | Winged Oddity | wingedmutant | hattackair1 flap | flap rattack1, flap hattackair2 | flap rattack1 | winceair1, winceair2 flap | dieair1 death:falldown1, dieair2 death:falldown2 | n | tauntair flap | flap | - | Running: flap; Standing: flap; Walking: flap |
| 160 | Winged Mutant | wingedmutant | hattackair1 flap | flap rattack1, flap hattackair2 | flap rattack1 | winceair1, winceair2 flap | dieair1 death:falldown1, dieair2 death:falldown2 | n | tauntair flap | flap | - | Running: flap; Standing: flap; Walking: flap |
| 161 | Winged Aberration | wingedmutant | hattackair1 flap | flap rattack1, flap hattackair2 | flap rattack1 | winceair1, winceair2 flap | dieair1 death:falldown1, dieair2 death:falldown2 | n | tauntair flap | flap | - | Running: flap; Standing: flap; Walking: flap |
| 162 | Fright | banshee | hattackair1 | rattackair1 | rattackair2 fx_rattackair2 | winceair1, winceair2 | dieair1 death:falldown1 | n | k | k, k | - | Walking: fly; Transition: transition; Resurrect: rattackair2 fx_rattackair2; dropped: ResurrectSpell |
| 163 | Dread | banshee | hattackair1 | rattackair1 | rattackair2 fx_rattackair2 | winceair1, winceair2 | dieair1 death:falldown1 | n | k | k, k | - | Walking: fly; Transition: transition; Resurrect: rattackair2 fx_rattackair2; dropped: ResurrectSpell |
| 164 | Terror | banshee | hattackair1 | rattackair1 | rattackair2 fx_rattackair2 | winceair1, winceair2 | dieair1 death:falldown1 | n | k | k, k | - | Walking: fly; Transition: transition; Resurrect: rattackair2 fx_rattackair2; dropped: ResurrectSpell |
| 165 | Trellborg | trellborg | hattack1 | weapons/fireboltlaunch, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, k | dirt x4 | - |
| 166 | Kin Trellborg | trellborg | hattack1 | weapons/fireboltlaunch, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, k | dirt x4 | - |
| 167 | Ancient Trellborg | trellborg | hattack1 | weapons/fireboltlaunch, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, k | dirt x4 | - |
| 168 | Jellyspore | jellyspore | hattackwater1 | hattackwater2 | n | wincewater1 | wincewater2 | n | n | fidgetwater | - | Running: swim; Walking: swim |
| 169 | Gelatinous Spore | jellyspore | hattackwater1 | hattackwater2 | n | wincewater1 | wincewater2 | n | n | fidgetwater | - | Running: swim; Walking: swim |
| 170 | Nettle Spore | jellyspore | hattackwater1 | hattackwater2 | n | wincewater1 | wincewater2 | n | n | fidgetwater | - | Running: swim; Walking: swim |
| 171 | Gezzamptling | gezzampt | hattack1 fx_hattack1 | weapons/chainlight01, hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, fidget2 | dirt x4 | - |
| 172 | Gezzampt | gezzampt | hattack1 fx_hattack1 | weapons/chainlight01, hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, fidget2 | dirt x4 | - |
| 173 | Gezzampt Elder | gezzampt | hattack1 fx_hattack1 | weapons/chainlight01, hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware | taunt | fidget1, fidget2 | dirt x4 | - |
| 174 | Ghast | ghoul | hattack1 fx_hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, death:die2 | n | taunt | fidget1, fidget2 | wightstep x2 | ResurrectSpell: resurrectspell |
| 175 | Ghoul | ghoul | hattack1 fx_hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, death:die2 | n | taunt | fidget1, fidget2 | wightstep x2 | ResurrectSpell: resurrectspell |
| 176 | Revenant | ghoul | hattack1 fx_hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, death:die2 | n | taunt | fidget1, fidget2 | wightstep x2 | ResurrectSpell: resurrectspell |
| 177 | Sea Monster Male | seamonster | hattackwater1 | hattackwater2 | n | wincewater1, wincewater2 | u, u | n | n | fidgetwater1, fidgetwater2 | - | Standing: standwater; Walking: swim; Jump: jump |
| 178 | Sea Monster Female | seamonster | hattackwater1 | hattackwater2 | n | wincewater1, wincewater2 | u, u | n | n | fidgetwater1, fidgetwater2 | - | Standing: standwater; Walking: swim; Jump: jump |
| 180 | Rotter | zombie | hattack2 | weapons/redthingylaunch rattack2?, hattack1 | weapons/redthingylaunch rattack2? | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1 | zombiestep x2 | ResurrectSpell: resurrectspell; Wakeup2: wakeup2 fx_wakeup2 |
| 181 | Dripper | zombie | hattack2 | weapons/redthingylaunch rattack2?, hattack1 | weapons/redthingylaunch rattack2? | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1 | zombiestep x2 | ResurrectSpell: resurrectspell; Wakeup2: wakeup2 fx_wakeup2 |
| 182 | Zombie | zombie | hattack2 | rattack2?, hattack1 | rattack2? | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1 | zombiestep x2 | ResurrectSpell: resurrectspell; Wakeup2: wakeup2 fx_wakeup2 |
| 183 | Skeletoid | skeleton | hattack1 | rattack1, hattack2 | n | wince1, wince3 | die1 | n | taunt | fidget1, fidget2 | skeletonstep x2 | Fidget3: fidget3; Resurrect: resurrect |
| 184 | Bone Thrasher | skeleton | hattack1 | rattack1, hattack2 | n | wince1, wince3 | die1 | n | taunt | fidget1, fidget2 | skeletonstep x2 | Fidget3: fidget3; Resurrect: resurrect |
| 185 | Skull Thrower | skeleton | hattack1 | rattack1 weapons/swordswing03, hattack2 | n | wince1, wince3 | die1 | n | taunt | fidget1, fidget2 | skeletonstep x2 | Fidget3: fidget3; Resurrect: resurrect |
| 186 | Honk | honk worshipper | hattack2? | weapons/swordswing03 rattack1? | hattack1? | wince1?, wince2? | die1? death:die1?, die2? death:die2? | n | n | k, k | dirt x4 | - |
| 187 | Elder Honk | honk worshipper | hattack1? | weapons/swordswing03 | hattack2? | wince1?, wince2? | die1? death:die1?, die2? death:die2? | n | n | k, k | dirt x4 | - |
| 188 | Honk Seer | honk worshipper | hattack1? | weapons/swordswing03 | hattack2? | wince1?, wince2? | die1? death:die1?, die2? death:die2? | n | n | k, k | dirt x4 | - |
| 189 | Lizard-Orc | lizardorc | hattack1 | rattack1 weapons/fireball01, hattack2 | rattack1 weapons/fireball01 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, fidget2 | lizardorcstep x2 | - |
| 190 | Lizard-Orc Warrior | lizardorc | hattack1 | rattack1 weapons/dragonfireboltlaunch, hattack2 | rattack1 weapons/dragonfireboltlaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, fidget2 | lizardorcstep x2 | - |
| 191 | Lizard-Orc Mage | lizardorc | hattack1 | rattack1 weapons/dragonfireboltlaunch, hattack2 | rattack1 weapons/dragonfireboltlaunch | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, fidget2 | lizardorcstep x2 | - |
| 192 | Skeleton | skeleton | hattack1 | rattack1 weapons/swordswing03, hattack2 | n | wince1, wince3 | die1 | n | taunt | fidget1, fidget2 | skeletonstep x2 | Fidget3: fidget3; Resurrect: resurrect |
| 195 | Bloodsucker | nosferatu | hattack1 fx_hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | ResurrectSpell: resurrectspell; Resurrect: resurrect |
| 196 | Annelid | nosferatu | hattack1 fx_hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | ResurrectSpell: resurrectspell; Resurrect: resurrect |
| 197 | Vampir | nosferatu | hattack1 fx_hattack1 | rattack1 | rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | ResurrectSpell: resurrectspell; Resurrect: resurrect |
| 198 | Bigfoot | bigfoot | hattack1 | rattack1 weapons/fireball01, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt | fidget1?, k | dirt x4 | WalkFidget: walkfidget |
| 199 | Sasquatch | bigfoot | hattack1 | rattack1 weapons/fireball01, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt | fidget1?, k | dirt x4 | WalkFidget: walkfidget |
| 200 | Yeti | bigfoot | hattack1 | rattack1 weapons/fireball01, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt fx_taunt | fidget1?, k | dirt x4 | WalkFidget: walkfidget |
| 204 | Plain Giant | giant | hattack1 | rattack1 weapons/electricalpop01, hattack2, hattack2save? | n | wince1, wince2 | die1, die2 | aware | taunt | k, k | yanmirstep x2 | - |
| 205 | Forest Giant | giant | hattack1 | rattack1 weapons/electricalpop01, hattack2, hattack2save? | n | wince1, wince2 | die1, die2 | aware | taunt | k, k | yanmirstep x2 | - |
| 206 | Yanmir | yanmir | hattack1 fx_hattack1 | fx_rattack1 weapons/iceblastlaunch rattack1?, hattack2 fx_hattack2, stepon | n | wince1, wince2 | u, u | n | taunt | fidget1, k | yanmirstep x2 | Wipe: wipe; AttackRanged2: rattack2; KickDoor: kickdoor fx_kickdoor |
| 207 | Lich | lich | hattack2 | rattack1 fx_rattack1, k | rattack1 fx_rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | skeletonstep x2 | ResurrectSpell: resurrectspell; Resurrect: resurrect; dropped: Hattack1 |
| 208 | Power Lich | lich | hattack2 | rattack1 fx_rattack1, k | rattack1 fx_rattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | skeletonstep x2 | ResurrectSpell: resurrectspell; Resurrect: resurrect; dropped: Hattack1 |
| 209 | Lich King | lichking | hattack1 | rattack1 fx_rattack1 | rattack1 fx_rattack1 | wince1, wince2 | die1 death:die1, death:die2 die2? | aware | taunt fx_taunt | fidget1, k | skeletonstep x2 | ResurrectSpell: resurrectspell; Resurrect: resurrect |
| 212 | Dragon King | dragon | wingattack | rattack1 weapons/dragonfireboltlaunch | rattack3 | wince1, wince2 | die1 | n | taunt | fidget1, fidget2 | dragonstep? | Land: flap; Running: fly; Walking: fly; SpitAcross: spitacross; Breath2: rattack2 |
| 216 | Honk | honk worshipper | hattack1? | weapons/swordswing03 | hattack2? | wince1?, wince2? | die1? death:die1?, die2? death:die2? | n | n | k, k | dirt x4 | - |
| 217 | Elder Honk | honk worshipper | hattack2? | weapons/swordswing03 rattack1? | hattack1? | wince1?, wince2? | die1? death:die1?, die2? death:die2? | n | n | k, k | dirt x4 | - |
| 227 | Fish | fish | k | k | n | k | k | n | n | k | - | - |
| 228 | Eye | beholder | hattackair1 | weapons/purplethingylaunch rattack1?, hattackair2 | weapons/purplethingylaunch rattack1? | winceair1, winceair2 | dieair1, dieair2 | n | tauntair | fidgetair1? | - | Running: flap; Walking: flap; Search: searchair |
| 229 | Orbus | beholder | hattackair1 | weapons/bluelinelaunch rattack1?, hattackair2 | weapons/bluelinelaunch rattack1? | winceair1, winceair2 | dieair1, dieair2 | n | tauntair | fidgetair1? | - | Running: flap; Walking: flap; Search: searchair |
| 230 | Oculus | beholder | hattackair1 | weapons/bluelinelaunch rattack1?, hattackair2 | weapons/bluelinelaunch rattack1? | winceair1, winceair2 | dieair1, dieair2 | n | tauntair | fidgetair1? | - | Running: flap; Walking: flap; Search: searchair |
| 234 | Colloidal Soldier | colloidal | hattack1 | rattack1 weapons/redthingylaunch, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | colloidalwarriorstep x2 | - |
| 235 | Colloidal Warrior | colloidal | hattack1 | rattack1 weapons/redthingylaunch, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | colloidalwarriorstep x2 | - |
| 236 | Colloidal Guardian | colloidal | hattack1 | rattack1 weapons/redthingylaunch, hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | colloidalwarriorstep x2 | - |
| 237 | Amphibious Terror | terror | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 238 | Desert Terror | terror | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 239 | Reptilian Terror | terror | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | k, k | dirt x4 | - |
| 241 | Lesser Demon | stage1demon | hattack1 | rattack1 weapons/fireboltlaunch, hattack2 | n | wince1, wince2 | die1 death:die1 | n | taunt | fidget1, fidget2 | dirt x4 | Block: block; DodgeLeft: dodgeleft; DodgeRight: dodgeright |
| 242 | Greater Demon | stage2demon | hattack1 | rattack1 weapons/fireboltlaunch flap?, hattack2 flap? | rattack1 weapons/fireboltlaunch flap? | wince1, wince2 | die1 death:die1 | n | taunt | fidget1, fidget2 | dirt x4 | Spawn: spawn; Block: block; DodgeLeft: dodgeleft; DodgeRight: dodgeright |
| 244 | MagreebBaby | magreeb | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | - |
| 245 | Old Hag | peasantfemale | k | k | n | k | k | n | n | k | dirt x4 | - |
| 246 | Bjarni Thorvaldssen | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 247 | Sigmund the Stressed | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | - |
| 248 | Markel the Great | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 249 | Sven Svenssen | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k, k | dirt x4 | - |
| 250 | Tryggva Ravenlocks | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | dropped: hattack1 |
| 251 | Kira the Cold | kira | wattack1 | wattack1 | n | wince1 | u | n | n | k, k | dirt x4 | dropped: wattack2 wattack3 block dodgeleft dodgeright dodgeback wince2 |
| 252 | Forad Darre | peasantmale | hattack1 | hattack1 | n | k | k | n | n | k | dirt x4 | - |
| 254 | Yrsa the Troll | peasantfemale | k | k | n | k | k | n | n | k | dirt x4 | - |
| 255 | Krohn | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | - |
| 256 | Fre | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 257 | Skraelos | peasantmale | k | k | n | k | k | n | n | k, k | dirt x4 | - |
| 258 | Bori | peasantmale | hattack1 | hattack1, k | hattack1 | wince1, wince2 | die1 death:die1, death:die2 die2? | n | n | k, fidget2? | dirt x4 | - |
| 259 | Ratatosk | peasantmale | hattack1 | hattack1, k | hattack1 | wince1, wince2 | die1 death:die1, death:die2 die2? | n | n | k, fidget2? | dirt x4 | - |
| 260 | Hanndl | peasantmale | k | k | n | k | k | n | n | k | dirt x4 | dropped: hattack1 |
| 261 | Njam the Meddler | peasantmale | k | weapons/fireboltlaunch, k | k | k, k | k | n | n | k, k | dirt x4 | PeasantAttack: hattack1 |
| 262 | The Great Honk | goose | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k, fidget1 | henstep x2 | - |
| 263 | Wyrde of the Known (Igrid) | peasantfemale | k | k | n | k | k | n | n | k, k | dirt x4 | - |
| 264 | Wyrde of the Knowing (Verdandi) | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 265 | Wyrde of the Unknown (Morgan) | peasantfemale | k | k | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Yawn Wince2 Die2 |
| 266 | Green Man | peasantmale | u | u | n | u | u | n | n | k, k, k | dirt x4 | - |
| 267 | Cow | cow | fidget1 | fidget1 | fidget1 | wince1, k | die1 death:die1, die2? death:die2? | n | n | fidget1, k | cowstep x4 | Tipover: tipover1; Tipover2: tipover2 |
| 268 | Goat | goat | hattack1 | hattack1 | hattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | n | k, fidget2 | goatstep x4 | - |
| 269 | Hen | hen | hattack1 | hattack1 | hattack1 | wince1, wince2 | die1, die2 | n | n | fidget1?, fidget2? | henstep x2 | - |
| 270 | Rooster | rooster | hattack1 | hattack1 | hattack1 | wince1, wince2 | die1, die2 | n | n | fidget1, k | henstep x2 | - |
| 271 | Pig | pig | fidget2 | fidget2 | n | wince1, wince2 | die1, k | n | n | fidget2, fidget1 | pigstep x4 | LieDown: standdown; Roll: roll; Rest: rest; StandUp: standup |
| 272 | Ewe | sheep | hattack1 | hattack1, k | hattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | n | k, fidget2 | goatstep x4 | - |
| 273 | Ram | sheep | hattack1 | hattack1, k | hattack1 | wince1, wince2 | die1 death:die1, die2 death:die2 | n | n | k, fidget2 | goatstep x4 | - |
| 274 | Scholar | scholar | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Hattack2 wince2 die2 |
| 275 | Master Scholar | scholar | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k, k | dirt x4 | dropped: Hattack2 wince2 die2 |
| 276 | Magreeb Spawn | magreeb | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | - |
| 277 | Magreeb | magreeb | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | - |
| 278 | Armored Magreeb | magreeb | hattack1 | hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | n | taunt | fidget1, fidget2 | dirt x4 | - |
| 292 | Tamur Leng | soldier | hattack1 fx_hattack1 | hattack2 fx_hattack2 | n | wince1, wince2 | die1 death:die1, die2 death:die2 | aware, k | n | k, k | dirt x4 | Block: block; Cower: block |
| 293 | Goose | goose | hattack1 | hattack1 | n | wince1 | die1 death:die1 | n | n | k, fidget1 | henstep x2 | - |
| 294 | cat | cat | standdown? | standdown? | standdown? | standdown? | k | n | n | fidget1, k | pigstep x4 | - |
| 295 | dog | dog | bark | bark | bark | k | k | n | n | k | pigstep x4 | WalkBark: walkbark |
| 296 | RailTest | - | hattack1? | hattack1? | n | k | k | n | n | k, k | dirt x4 | - |
| 297 | Brown Cow | cow | fidget1 | fidget1 | fidget1 | wince1, k | die1 death:die1, die2? death:die2? | n | n | fidget1, k | cowstep x4 | Tipover: tipover1; Tipover2: tipover2 |
| 299 | mouse | mouse | k | k | n | k | k | n | n | k | - | - |
| 300 | evil mouse | mouse | k | k | n | k | k | n | n | k | - | - |
| 301 | Ebora | peasantfemale | hattack1? | castspell? | castspell? | wince1, wince2 | die2 | n | k | k, k | dirt x4 | - |
| 302 | Concubine | peasantfemale | hattack1? | castspell? | castspell? | wince1, wince2 | die2 | n | k | k, k | dirt x4 | - |
| 303 | Phantom Fighter | phantom | hattack1 fx_hattack1? | k, hattack2? fx_hattack2?, hattack3 fx_hattack3? | n | wince1?, wince2? | die1? death:die1?, die2? death:die2? | n | taunt? fx_taunt? | k, k | dirt x4 | - |

<!-- coverage:end -->
