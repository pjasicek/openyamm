# Outdoor bed panning (D-48)

## DECISION

**(b): a per-sound `pan: false`.** Beds that are meant to surround the party get `pan: false`. Point sounds (the sand-falls, Castle Kalindra's shimmer, torches, fires, drips) keep panning. Xeen's `world.yml` gets no `ambientSounds` block, so (a) is rejected. Leaving panning as it is (c) is also rejected.

**The random start point is approved.** It applies in every world to looping placed sounds that have no `wait`. Each one starts at a uniformly random frame of its clip. It does not need to be seeded by key.

## WHY

1. Option (a) costs too much. Xeen already ships placed sounds in 39 indoor scenes, and most are point sounds whose direction matters: `whistling wind` ×10, `drip01/02` ×8, `torch loop`, `raging fire loop`, campfires, `lava loop`, `bubbling cauldron01`, `xeen_sandfall_loop`. The switch is world-wide (`rules.pan` in `game/audio/WorldAmbientSounds.cpp`), so all of them would lose direction. MM9 uses it only because all of MM9's ambient sounds are unpanned 2D samples.
2. Option (b) is the small, general engine word that D-41 and D-44 prefer. The work is:
   - a `bool pan = true` in `WorldAmbientSound`;
   - one more accepted key in `parseAmbientSoundsNode`'s key list (`game/maps/IndoorSceneYml.cpp`), which outdoor scenes share through `parseSceneAmbientSoundsNode`;
   - passing `rules.pan && source.pan` to the `pan` argument that `playAssetInstance` already takes, which reaches the mixer as `PlaybackOptions::pan`.
3. The random start is just as small. The mixer's `frameOffset` (`engine/AudioSystem.cpp`) already holds each sound's play position and currently always starts at 0. The runtime already has an `m_rng`, which it uses to randomise waits for the same reason ("so a shore's waves do not all start together"). A seamless loop has no meaningful first sample, so starting it elsewhere changes nothing a player can hear except the in-step build-up of about +6 dB. Seeding by key is unnecessary because headless runs play no placed sounds.
4. No option affects MM6–MM8. No `assets_dev/worlds/mm6|mm7|mm8` or engine scene has `ambient_sounds`.
5. MM9's sounds stay centred under (b), because its world rule `pan: false` is combined with the new field by AND. Its looping sounds without a wait only gain the random start.

## WHO ACTS

**A1 (engine and studio, at the next merge point)**
- **Engine field:**
  - Add `pan` (default true) to `WorldAmbientSound`.
  - Parse `pan` in scene `ambient_sounds`.
  - Play with `rules.pan && source.pan`.
- **Studio word:**
  - Accept `pan: false` in sketch.yml `sounds` (`openyamm-studio/core/OutdoorThings.cpp`) and write it in `OutdoorBuild.cpp`.
  - Do the same for objects.yml `sounds` indoors (`IndoorLowering.cpp`, `IndoorBuild.cpp`) and for overlay sounds (`SceneOverlay.cpp`).
- **Random start:**
  - Add a start position to `playAssetInstance` / `PlaybackOptions`: a fraction of the clip, or a start frame that gets wrapped.
  - Set it from `m_rng` uniformly over the clip, only when the sound has `loop: true` and no `wait`.
  - One-shot sounds and sounds with a wait are unchanged.
- **Tests:** one unit test for each of these:
  - the parser accepts `pan`;
  - the world rule and the field combine as AND;
  - the start position stays inside the clip.
- **Docs:** document all of this in `devdocs/AMBIENT_SOUNDS.md` and in the studio README ("Outdoor sounds", "sounds").

**AU (audio lane)**
- After A1's merge point names the word, add `pan: false` to every bed line that `beds.py` writes (`xeen_amb_meadow`, `lagoon`, `tundra`, `savannah`, `desert`, `darkside`). Leave the sand-falls and `sound:kalindra_shimmer` without it.
- Indoors, apply the same rule:
  - room-filling beds such as `xeen_amb_sewer`, `xeen_amb_mine` and `xeen_amb_tower` get `pan: false`;
  - anything with a source you can see or locate (fires, drips, lava, the cauldron, wind at an opening) keeps panning.
- In AUDIO.md, rewrite "Known limits" and record the session's request to A1 as done.

**A5 and A6 (map lanes)**
- Paste the current bed lists now; they work, just panned.
- Re-paste AU's regenerated lists, with `pan: false`, once A1's merge point carries the word. Then rebuild and install as already requested.

**Orchestrator:** nothing to change in `world.yml`.

## REVERSIBLE

Yes, and cheaply:
- Dropping `pan: false` from a line brings back panning for that sound.
- The world switch (a) is still available if Xeen ever wants every sound unpanned.
- The random start is only the position a sound starts playing from; it touches no data or saves.

## SUMMARY ROW

| D-48 | 2026-11-21 | Outdoor bed panning | (b): per-sound `pan: false` (scene field, studio word; `rules.pan && source.pan`) for beds that surround the party; point sounds keep panning; no world-wide switch (it would unpan 39 Xeen indoor scenes' point sounds). Looping placed sounds without a wait start at a random frame, all worlds. MM6–MM8 unaffected | A1 (field, word, random start), AU (bed lines), A5/A6 (re-paste) |
