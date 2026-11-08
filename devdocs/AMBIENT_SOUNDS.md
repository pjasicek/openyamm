# Placed ambient sounds

Sounds placed in a map (2026-11-04, world rules and fires 2026-11-06; MM9's 1378 AmbientSound objects and its fires):
waves along a shore, wind in a canyon, a torch's crackle, a room's hum. Each is heard within its outer radius, at full
volume inside its inner radius.

## Scene data (BLV scenes)

```yaml
ambient_sounds:
  - key: 412                          # MM9: the DAT object index
    sound: ambient/water/waves02.wav  # a world sound name (worlds/<world>/audio/...)
    position: [1200, -340, 96]
    inner_radius: 640
    outer_radius: 3072
    volume: 0.8                       # 0-1 (default 1)
    loop: true                        # default true; false: once each time the party comes within reach
    wait: [2, 6]                      # a looping sound with a wait plays once, then waits a random min-max seconds
    day_only: true                    # the world's day hours, 06:00-20:00 by default (night_only: the rest)
    start_on: false                   # silent until a map script switches it on (AmbientSound<key>, or sprite)
    sprite: 310                       # on while the decoration of this cog is shown (evt.SetSprite): a fire's sound
```

`game/audio/WorldAmbientSounds.h` (`WorldAmbientSound`), parsed by `game/maps/IndoorSceneYml.cpp` into
`IndoorMapData::ambientSounds` (an overlay's list replaces the base scene's) and offered by
`IGameplayWorldRuntime::ambientSounds()`.

## World rules

`world.yml` `ambientSounds` (`WorldAmbientSoundDefinition`, passed to the runtime as `WorldAmbientSoundRules`):

```yaml
ambientSounds:
  dayHours: [5, 17]   # day_only / night_only window (default [6, 20])
  pan: false          # centred, heard by distance only (default true: panned by direction)
```

MM9 declares both (its own 05:00-17:00 window and its unpanned 2D samples; MM9_AMBIENT_AUDIO_RE.md section 1);
worlds that declare nothing keep 06:00-20:00 and panning. `pan: false` reaches the mixer as
`Engine::AudioSystem::PlaybackOptions::pan`: distance falloff stays, the left/right balance does not.

## Runtime

`WorldAmbientSoundRuntime` (`game/audio/WorldAmbientSounds.cpp`), run by `GameApplication::renderFrame` after the
frame's other audio with the active world's rules: the listener is the party (160 units over its feet). A sound is
switched by its map variable `AmbientSound<key>` (1 on, 2 off) if a script set it, else by its `sprite` decoration's
evt.SetSprite state if it has one and a script set that, else by `start_on` (`worldAmbientSoundEventSwitch`). A sound
comes in at its outer radius and stays until 1.1 x that (`AmbientSoundStopMargin`), then stops. Looping sounds without a wait play as one loop; with a
wait, each play is a one-shot followed by a random wait (a new arrival starts somewhere in the wait, so a shore's
waves do not start together). Positional playback uses the engine's own inner/outer radius falloff
(`GameAudioSystem::playAssetInstance`). A new map's list stops every sound of the old one; without a running map
nothing plays.

## MM9 maps (the converter)

`level_generation/projects/mm9r_common/dungeon/ambient.py`: MM9's file (by its path under `worlds/mm9/audio`, else by
its name anywhere there; 164 placements name files MM9 does not ship and are listed in the build report as
`ambient_sounds_missing_files`), radii x 2.56, Volume (MM9 0-100) / 127 x 2/3, Loop, LoopWaitMin/Max, DayOnly,
NightOnly (both: night only, as MM9's ReadProp), StartOn. The volume keeps MM9's level against the music under the default sliders: see
[MM9 ambient volume RE](mm9_rework/MM9_AMBIENT_VOLUME_RE.md). A sound with a LoopCount (1 on all 13 that have one, all switched) plays once
per switch-on (`loop: false`). The fire family (Fire, Brazier, WallTorch, Torch; about 670 objects) adds its SoundFile
within SoundRadius (`ambient.fire_sounds`; key: the object's DAT index; inner radius a quarter): on as MM9's `On`
says, following the decoration's evt.SetSprite (`sprite`) where the map's hooks placed the fire with a cog (Anskram's
gate fires, the Bathhouse furnace, Verhoffin's pentagram), and switched like an AmbientSound by a touch Trigger that
sends it On/Off/Toggle. The dungeons' plain touch Triggers that send On/Off/Toggle to an AmbientSound set the
map variable `AmbientSound<key>` (1 on, 2 off, saved with the map; `worldAmbientSoundSwitch`) from a shared 4 Hz poll (objects.py `ambient_triggers`, event 903); the cities' and
regions' scripts, and the maps' door, switch and destructible links, set it in their own Lua. The poll restarts
itself with `evt.StartTimer`, which only moves a registered map timer: since 2026-11-06 it is registered as one (it
ran once, on load, before; maps converted earlier keep that until reconverted).

## Scripted voices and scenes (MM9, 2026-11-06)

Not scene sounds but map Lua (`evt.PlaySoundName(name, x, y, z)` at a point, `MM9.playSound` without one), written by
the converters:

- **Greeting voices** (`dungeon/voices.py`, `objects.voice_lines`): a placed NPC whose script's `:OnUse` plays a voice
  (Shopkeeper.scr and Retainer.scr's ScriptParams wav, NPCnnn.scr's own) gets its click event (53000 + its DAT index,
  unless the map's Lua has one): the voice, then its RUDE dialogue.
- **Sturmford City's barks** (`mm9r_sturmfordcity/citylua.py`): Trigger1/2 (once each) at Tryggva's table and Ercc's
  seat: one of Tryygva01-04 (TryggvaSpeech.scr), Ercc's ercc01 and ercc02 with key 113 (ErccSpeech.scr).
- **The Guberland Players' show** (`mm9r_guberlandcity/citylua.py` `play_lines`): at 14:30 and 16:30 (Narrator.scr)
  the curtain opens and THEPLAY.scr's 29 lines play at their speakers' places, each after the last one's length;
  the curtain closes after the bow (map variables `PlayLine`, `PlayShows`).
- **The Temple of Honk ceremony** (`mm9r_templeofhonk/convert.py` `ceremony_lines`): the bell at 6:15 and 18:15, then
  until 6:45 and 18:45 the leader's thunder preaching and pacing between the platform markers (HonkLeader.scr).

## Not yet

- No occlusion: a sound is heard through walls within its radius, as in MM9.
- Outdoor (ODM) scenes have no `ambient_sounds`.
- MM9's `LoopCount` sounds play once per switch-on in or out of range and keep their waits running out of range; here
  `loop: false` plays once per arrival and an out-of-range sound stops (MM9_AMBIENT_AUDIO_RE.md G11).
- The world's music rules (repeat gap, battle music) are `world.yml` `music`: MM9_AMBIENT_AUDIO_RE.md section 4.
