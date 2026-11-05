# Placed ambient sounds

Sounds placed in a map (2026-11-04; MM9's 1378 AmbientSound objects): waves along a shore, wind in a canyon, a torch's
crackle, a room's hum. Each is heard within its outer radius, at full volume inside its inner radius.

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
    day_only: true                    # 06:00-20:00 (night_only: the rest)
    start_on: false                   # never plays (MM9 starts these from triggers; none is scripted yet)
```

`game/audio/WorldAmbientSounds.h` (`WorldAmbientSound`), parsed by `game/maps/IndoorSceneYml.cpp` into
`IndoorMapData::ambientSounds` (an overlay's list replaces the base scene's) and offered by
`IGameplayWorldRuntime::ambientSounds()`.

## Runtime

`WorldAmbientSoundRuntime` (`game/audio/WorldAmbientSounds.cpp`), run by `GameApplication::renderFrame` after the
frame's other audio: the listener is the party (160 units over its feet). A sound comes in at its outer radius and
stays until 1.1 x that (`AmbientSoundStopMargin`), then stops. Looping sounds without a wait play as one loop; with a
wait, each play is a one-shot followed by a random wait (a new arrival starts somewhere in the wait, so a shore's
waves do not start together). Positional playback uses the engine's own inner/outer radius falloff
(`GameAudioSystem::playAssetInstance`). A new map's list stops every sound of the old one; without a running map
nothing plays.

## MM9 maps (the converter)

`level_generation/projects/mm9r_common/dungeon/ambient.py`: MM9's file (by its path under `worlds/mm9/audio`, else by
its name anywhere there; 164 placements name files MM9 does not ship and are listed in the build report as
`ambient_sounds_missing_files`), radii x 2.56, Volume (MM9 0-100) / 127 x 2/3, Loop, LoopWaitMin/Max, DayOnly,
NightOnly, StartOn. The volume keeps MM9's level against the music under the default sliders: see
[MM9 ambient volume RE](mm9_rework/MM9_AMBIENT_VOLUME_RE.md).

## Not yet

- Lua cannot switch a sound on or off (MM9's StartOn 0 sounds, 40 of them, stay silent).
- No occlusion: a sound is heard through walls within its radius, as in MM9.
- Outdoor (ODM) scenes have no `ambient_sounds`.
