# MM9 cutscenes: in-engine cinematics and camera shake (2026-11-06)

The user (2026-11-06): in-engine cutscenes for the MM9 world, done now, in a modern data format ("we don't want legacy
format here"). This document is the research (MM9's system from its data, scripts and binaries), the per-map
inventory, the OpenYAMM format and runtime (shared, world-agnostic: MM6-MM8 can use it), and the pilot. The other
cutscenes are converter work items: [FINAL_REBUILD_WORK.md](FINAL_REBUILD_WORK.md) item C11.

Before this the engine had only video cutscenes (`game/ui/screens/CutsceneVideoScreen`); the converted maps ran their
cutscenes' gameplay steps on timers and logged the cameras as `[MM9Unsupported]` (FINAL_REBUILD_GAPS.md section 4).

## 1. MM9's system

### Objects (the DATs, `assets_editor_dev/worlds/mm9/maps/<stem>.raw_objects.yml`)

| Class | Count | Maps | Properties | What the game reads |
| --- | --: | --: | --- | --- |
| `Camera` | 71 | 13 | Name, Pos, Rotation (pitch, yaw, roll), ScriptName/Params, ActiveTime -1, OneTime 0, StartActive 0, FOV 90 | ActiveTime, OneTime, StartActive only (object.lto Camera ReadProp `0x1005a4c0`); **FOV is never read** |
| `CameraMarker` | 16 | 6 | Name, Pos, Rotation, wander fields, FOV | a position the camera scripts move to (`MoveToPos`) |
| `EarthQuake` | 29 | 7 | InnerRadius, OuterRadius, QuakeDuration, ShakeAmount, InnerDamage, DecayRate, StartOn | see "Camera shake" |

Maps with cameras: thronheimcity 12, 1000terrors 11, hallofthegods 11, afterworld 9, yorwick 7, arslegardcity 5,
frosgardcity 4, greatgate 4 (no rebuilt map: its lose sequence is the `MM9LoseGame` movie, E6), isleofashes 4,
bathhouse, thjoradmine, wizardslab, yanmirsfort 1 each. There is no KeyFramer, key path or CinemaCamera class: camera
motion is all script (`MoveToPos` to a marker, `FaceObject`). Several placed cameras are never used (Afterworld's
Camera0-8 and 10, a copy of Yorwick's set; Frosgard City's Camera3).

### Script commands (`mm9/extracted/SCRIPTS/SCRIPTS/*.scr|*.inc`)

A director script (an object's script: `ARGUMENT.scr` on Argueman, `ISLEASHESBOOK.scr` on the Book, `FATEMAN.scr`,
`WINMAN.scr` ...) runs the cutscene as a chain of labels joined by `Wait <channel> <seconds> <label>` (a new wait on
a channel replaces the old one) and by callbacks:

- `Trigger <camera> On` / `Off`: the view switches to that camera and back. Nothing restores the player's view
  explicitly; `Off` does. Camera scripts (`BATTLECAM1`, `ARGUECAM1`, `LOSECAM1-3`, `ICECAM1`, `IA_CAMERA2`,
  `AFTERWORLDCAM1`, `WG_*`) add triggers such as `Play`, `Pan`, `Move` that start a motion and tell the director
  when it arrives (`trigger <director> Done`, `Cam3`, `Crane`).
- `MoveToPos x y z speed callback`: a straight line at speed LT units per second, no easing; it stops when it would
  pass the target and raises the callback (`0x100bff70`, ticks every 0.01 s); speed below 1 teleports.
  `IA_CAMERA2.scr:35` passes `xpos Xpos Zpos` (y = x): MM9's crane shot also sinks.
- `FaceObject obj rate callback` / `FaceDir x y z rate cb`: a turn at rate degrees per second, 0 a snap
  (`0x100a62c0`, `0x100bfb70`).
- `Target obj`: stores a handle and raises an event; there is **no per-frame look-at** in the Camera or ObjectBase
  update (`0x10099aa0`), so a cutscene camera looks along its DAT rotation and its FaceObject turns.
- `LetterBox TRUE/FALSE`: the 3D view becomes the hard-coded rect 0, 100, 800 x 400 (a 2:1 picture, a sixth of an
  800 x 600 screen black at the top and bottom; cshell `0x10091e00`, `0x10090bc0`), instantly (a 4 px/frame slide
  exists, `0x100920a0`, but nothing enables it). LetterBox also turns **input off** (`SetInputState(false)`,
  `ClearInput`), pauses both music managers and blocks Escape (`0x100a51a5`): no menu and no save.
- `ScreenFadeOut n` / `ScreenFadeIn n`: the server sends message 0x84 {seconds, in/out}; neither the client's
  OnMessage switch (`0x100a58f0`) nor the game handler (`0x100aabb0`) handles 0x84: **in the shipped game the fades
  do nothing** (medium-high confidence). The scripts' intent (fade over n seconds, 0 instant, non-blocking) is kept.
- The client draws from the first camera effect object with the "live" flag (cshell `0x10091650`) and skips the
  player's eye position (`0x100ac35c`); the server moves the client's view position there too (visibility, sound).
  The field of view stays the client's: 90 degrees across, vertical = horizontal x height / width (`0x10090e00`).
- No input lock or skip besides LetterBox: while a camera is live, Use or AttackUse raise `OnPlayerInterrupt` on it
  (`0x100c4020`), which only test scripts (`FOLLOWPATH.inc`) handle. Shipped cutscenes cannot be skipped.
- `IsTurnBased`: TELP 1.3's guard in `ARGUMENT`, `EBORAMINES`, `EBORABATH`, `TAUNTMAN`: fade out, RollOverText 18,
  retry every second until the party leaves turn-based mode.
- Timing comes from fixed waits, camera arrivals, animation key events (`AddModelKey tag label` on the `.abc` keys:
  `Voice1`, `CameraSwitch`, `Done`) and sound ends (`PlaySound ..., callback`). The speech-driven cutscenes (the
  council, the gate, the epilogue) time each line by its wav and animation.
- Actors during a cutscene: `PlayAnim anim callback`, `MoveToPos`/path walks, `RemoveNPC`, `appear` (show), teleport
  effects, `RollOverText id` (floating text; the strings are not in the extracted data), voice wavs
  (`VOICES/CINEMA/<scene>/NN.wav`). Monsters near the scene are often removed first (`GetObjects AIBase` + `RemoveObject`).

### Camera shake (EarthQuake, object.lto `0x101A4660`)

Messages On/Off (StartOn the default) and Trigger (`0x10076e50`). On Trigger every object within OuterRadius gets
{amplitude, duration, damage, decay} with no falloff (InnerRadius must be above 0 for it to fire at all); the player
forwards it to the client (`0x10090ef0`), which offsets the view by an independent random ±amplitude per axis each
frame (clamped to 12 units), at full amplitude for QuakeDuration seconds, then down by DecayRate units per second.
InnerDamage is applied once to each object in range. **Bug**: ReadProp (`0x10076de0`) reads `ShakeAmt`, the DATs and
`SetPropNumber` say `ShakeAmount`, so the amplitude stays at the constructor's 0.5 units: shipped quakes barely move.

## 2. Inventory (every cutscene and shake)

Ids are the cinematic ids the converters should give them. "Speech" means timing driven by voice wavs and animation
keys (their durations come from the wav files and the `.abc` keys, read by the converter).

| Map | Cinematic | Director, trigger | Cameras (in order) | Length, timing | What happens; purpose |
| --- | --- | --- | --- | --- | --- |
| isleofashes | `book_sinking` (**pilot, done**) | ISLEASHESBOOK.scr (Book) OnUse with key 29, not 28 | Camera0, Camera1, Camera2, Camera2 Pan (IA_CAMERA2: MoveToPos to Camera3's x,x,z at 100, FaceObject Boat at 20), Camera3 | 17 s, fixed waits | Fort walls destroyed, shooters fire, the islet sinks, the boat leaves; key 28, 5 200 xp, ExitTrigger1 to Sturmford |
| thronheimcity | `council_argument` | ARGUMENT.scr (Argueman) Start from KiraDoor2; keys 90 and 91, not 40; TB guard | Camera0 (to CameraMarker0 at 40, ARGUECAM1), then 1, 11, 2, 3, 4, 1, 2, 4, 5, 6, 5, 4, 7, 4, 5, 4, 5, 4, 7, 8, 9, 10, 0, 10 (fixed) | ~165 s, speech: 24 `Done` callbacks (camera arrivals, animation keys, wav ends) | The Jarls' war council: lines 01-20.wav (VOICES/CINEMA/THEARGUMENT), Sc2_* animations, applause, Kira kills Markel; `:War` mid-scene (keys 184, 40, 85, 93, 26 500 xp, item 401); Yrsa appears at the end |
| yorwick | `battlefield_sven` | SVENSPEECH.scr (Sven) on load with key 95, not 97 | Camera0 (to CameraMarker0 at 70), Camera1 (to Camera2 at 40), Camera3 (to Camera4 at 10), Camera5, cuts to 6/7/8 on animation keys | ~68 s: 3 moves then the 43.7 s Sven_scene06 animation | Sven's battle speech (sven01-04.wav); key 97, 114 000 xp at sven04; ambient sounds off/on; ~30 tableau props shown/hidden |
| afterworld | `afterworld_guilt` | NPC336.scr + SIXFIRES.inc :Guilt (Skraelos0) on dialogue exit with key 380, not 381 | Camera9 (to AfterMarker0 at 100) | ~16 s, fixed | Key 381, quest sound, fade out 2 s, then dialogue |
| frosgardcity | `break_ice` | BREAKICE.scr (BreakIce) after the powder barrel dies (Shooter0 sends start) | Camera0 (ICECAM1), Camera1 (to IceMarker2 at 150), Camera2 | ~16 s, waits + one arrival | Shooter1-4 fire, ice floes break in waves, iceimpact.wav; keys 72 and 174, 8 000 xp each |
| arslegardcity | `gate_fate` | FATEMAN.scr (Fateman) on load without key 98 | Losecam4 (to CameraMarker0 at 100), Losecam2 (to CameraMarker2 at 150), Losecam3 | ~45 s, speech | Hanndl09-15.wav with the party's lines (getPCVoice, 18 voice sets; line 05 never plays: a script bug), the peephole door; 46 000 xp, ExitTrigger2 to the Dark Passageway |
| arslegardcity | `gate_writ` | WRITMAN.scr (Writman) on load with key 100, not 9515 | Losecam1, Losecam2, Losecam3, Losecam5 (to Losecam6 at 100) | ~30 s, speech | Hanndl16, the party's line 01, Hanndl17b; 170 000 xp, Hanndl removed, the gate opens |
| 1000terrors | `njam_freeze_win` | WINMAN.scr (WinMan lever) OnUse with key 108, party at z >= -3680 | NjamCam (path NjamCamMk1/2), WG_Shot2Cam, Shot3, Shot4, Shot5 (to Shot5Mk), Shot6 0.6 s, Shot5 3 s, Shot5CamB, Shot7 (path Shot7Mk0-3 at 75) | ~40 s, mixed: arrivals, njam_wingame keys, waits | Njam frozen (skins Njam1-7), earthquake, lightning; key 109, 234 000 xp; ExitTrigger1 to the Hall of the Gods |
| 1000terrors | `njam_taunt` | TAUNTMAN.scr, Trigger19 touch with key 108, not 497; TB guard | TauntCam, TauntCamB, TauntCam | ~20 s, waits + a walk | Njam walks out, two RollOverTexts, vanishes; key 497 |
| 1000terrors | `chess_capture` | CHESSCAMERA.scr, `Look` from a chess piece | ChessCam at the party's eye, pan to the piece at 360 | until the piece lands | The party is pushed down through the floor (the chess puzzle) |
| hallofthegods | `gods_epilogue` | WINMAN.scr Part2 on load with key 109, no item 394 | WG_Scene7Cam1 (to Scene7MK1 at 150), Cam2 3.5 s, Cam3-Cam11 cut by HanndlN/KrohnN | ~95 s, mostly waits, voice keys | Hanndl01-06 and Krohn01-07.wav; item 394 (Writ of Fate), then the high-score/ending (D3) |
| wizardslab | `summoning` | WIZARDLABCAMERA.scr + CUTSCENE.inc (CameraSummon), DestinationPurple touch | MarkerLocation0-3 facing MarkerTarget0-3 | ~23 s, trigger delays 8, 5, 0 | Apprentices' beams (M10), a Greater Demon summoned |
| bathhouse | `ebora_escape` | EBORABATH.scr after the third concubine dies | EboraCam1 (snap to Ebora) | ~4 s | Ebora casts and escapes (RollOverText 11, fire column); key 349 + 80 000 xp or key 350 |
| thjoradmine | `ebora_free` | EBORAMINES.scr, FreeAtLast | EboraCam (snap to Ebora) | ~13 s, fixed | Taunt, attack, fire column, she is removed |
| yanmirsfort | `yanmir_death` | YANMIRBASE :OnTimeToDie, six supports broken | YanmirCamera (on Yanmir; ends 3 s after his link breaks) | ~8-10 s, events | Cave-in dust, his fall; key 69 or 173, 8 000 xp |

Never placed: CINEMAMGR, ALTCINEMAMGR, E3DUNGEON*, DIRECTOR1, GOBLINCIN1, LICHLABCAMERA, CAMERATEST, ARGUECAM2.
greatgate's `lose_game` (LOSEMAN.scr) is the `MM9LoseGame` movie already (E6).

Camera shake (EarthQuake objects and scripts):

| Map | Objects (inner/outer radius, duration s, ShakeAmount, decay) | Trigger |
| --- | --- | --- |
| ruinedtemple | DBQuakeObject0 (400/400, 1, 100, 2), DBQuakeObject1/2 (500/700, 0.7, 100, 2), QuakeObject0/2 (500/700, 2, 100, 3); QuakeObject1 unused | DBEffectsTrigger0-2 touches (with dust); TriggerCaveIn0/1 with the cave-in |
| thjoradmine | DBQuakeObject0/1/4/5 (100/300, 0.2, 2, 1), DBQuakeObject2 (100/200, 0.1, 1, 0.5), DBQuakeObject3 (300/700, 0.5, 3, 2), TunnelQuake2 (1/500, 3, 2, 0.5, StartOn 0) | DBEffectsTrigger0-5 touches; FallingBoard0; the Stalagtite door sends TunnelQuake2 on |
| thjoradmine | QuakeObject (THJORADQUAKE.scr) | ambient: every 300-600 s, 3-8 s at amount 2-5, radius 1000, at the party |
| bathhouse | EffectsMgr (EFFECTSMGR.scr) | GasRelease0 opens: 12 s at 6, eqhammer sound x4 |
| 1000terrors | Earthquake (100/400, 500, 1, 2) | Njam's Panic (NJAMFREEZE:49) on, OnLightningOff off: part of `njam_freeze_win` |
| isleofashes | Earthquake, Earthquake1 | never fired (ISLEASHESBOOK:177-178 commented out) |
| wizardslab, yanmirsfort | QuakeSummon; DoorQuake0-9 | never fired (no sender; YANMIRPATROL.scr runs nowhere) |

Model keys shake the view as well: the Dragon's landing and death, a Giant's and Yanmir's steps and blows (`BigEQ`,
`SmallEQ`, `SmallerEQ`); they are clip events of those actors, see
[MM9_MONSTER_SOUNDS.md](MM9_MONSTER_SOUNDS.md) section 1.

## 3. The OpenYAMM format

A map's cinematics live beside it: `worlds/<world>/maps/<stem>.cinematics.yml`, loaded with the map
(`GameApplication::loadMapCinematics`, before its load events run); no file costs nothing. The parser
(`game/gameplay/CinematicRuntime.cpp`, `parseCinematicLibrary`) rejects unknown keys, missing fields and out-of-range
values with the cinematic, shot or cue named; an invalid file is logged and the map has no cinematics.

```yaml
format_version: 1
kind: openyamm_cinematics
source: "free text"                 # optional, ignored (every map, shot and cue may carry note: too)
cinematics:
  book_sinking:                      # the id evt.PlayCinematic takes
    skippable: true                  # default true: Escape, Space or Return ends it (section 4)
    letterbox: true                  # default true: bars in over letterbox_seconds at the start, out before the end
    letterbox_seconds: 0.5           # default 0.5 (0: instant, as MM9)
    shots:                           # consecutive; after the last the party's own view returns
      - {duration: 2.2, position: [92, 6625, 655], direction: [-0.49, -0.78, -0.40], fov: 73.7}
      - {duration: 3, position: [0, 0, 300], look_at_actor: 12}        # follows the actor (3/4 up its body)
      - {duration: 2, party: true}                                     # the party's view inside the cinematic
      - duration: 3.5
        easing: linear               # linear | smooth (default: smoothstep between keys) | spline (one curve
                                     # through all keys, continuous speed, at rest at the ends and at repeated keys)
        keys:                        # a moving camera: the first key at 0, times increasing, within the shot
          - {at: 0, position: [8659, 9624, 1037], direction: [0.91, 0.41, 0]}
          - {at: 3.5, position: [8414, 8768, 940], look_at: [9554, 5253, 0]}
    cues:                            # at: seconds from the start; exactly one kind per cue
      - {at: 0, fade: in, seconds: 1}          # in: from black; out: to black (default 1 s)
      - {at: 0, letterbox: true, seconds: 0.5} # explicit bars (then none are added implicitly)
      - {at: 1, event: 31011}                  # runs a map event: the gameplay steps (also on a skip)
      - {at: 3.2, sound: "sounds\\spells\\ebolt01.wav"}   # as evt.PlaySoundName takes it
      - {at: 4, subtitle: "Text shown under the picture", seconds: 3}
      - {at: 0, actor: 5, action: hide}        # show | hide | place (to:) | move (to:, seconds:)
      - {at: 1, actor: 5, action: move, to: [100, 200, 0], seconds: 2}   # feet, a straight line
      - {at: 2, actor: 5, action: face, look_at_actor: 6, seconds: 0.5}  # or look_at: [x, y, z] / look_at_party: true
      - {at: 2, actor: 5, action: clip, clip: ArgumentSpeak2, loop: false}  # a model clip or script_clips role
      - {at: 4.5, decoration: 493, offset: [4557, 4342, 0], seconds: 24.6}  # a decoration model glides (by its cog)
      - {at: 4.5, shake: 0.6, seconds: 2}      # camera shake, intensity 1 strong
```

Actor `face` turns the actor's model (presentation; its AI keeps its own heading) and `clip` plays a clip by the
model's GLB clip name (the MM9 NPC models carry their cutscene clips: `mm9_bjarni.glb` has `Sit`, `Agree`, `Applause`,
`ArgumentShot1A` ...) or an actors.yml `script_clips` role, once (then its own animation) or looping; both end when
the cinematic ends. A model without the clip plays its own animation. A clip with actors.yml animation events plays
them as in a fight (2026-11-10): its socket effects (MM9's `DoFX` hand effects) at their clip times, and an action
role's clip (`AttackRanged` of the summoners in `wizardslab` `summoning`) charges that role's glow until its impact
marker ([creature guidelines](../../level_generation/creatures/CREATURE_3D_GUIDELINES.md) section 7). `decoration` moves a decoration's model (by
its cog, as `evt.SetSprite`) to an offset from its map position; the glide goes on past the cinematic's end and is
runtime only (a map restores it on load). Faces of the map (BLV world models: a sinking islet) move as the engine's
doors and movers do, started by an `event` cue (`evt.SetDoorState`); the converters make such a model a mover
(dungeon/movers.py motions, `dat` for MM9's own linear Door).

Camera keys: `position` (the eye, world units) and exactly one aim: `look_at: [x, y, z]`, `look_at_actor: <map actor
index>`, `look_at_party: true`, `direction: [x, y, z]`, or `yaw:` with `pitch:` (degrees). `fov` is the vertical field
of view in degrees (10-120); without it the gameplay view's (60). Between keys the eye moves along the line (eased) and
the aim's directions blend, so a key pair with two directions is a pan. A cinematic lasts until its last shot or cue
ends (fades, letterbox, subtitles, moves and shakes last their seconds).

The format is world-agnostic: actor indices, positions and event ids are the map's own; nothing names MM9. MM6-MM8
maps can carry the same file.

## 4. Runtime behaviour

Shared gameplay code, indoors and outdoors (`game/gameplay/CinematicRuntime.{h,cpp}`, run by `GameSession`):

- **Lua**: `evt.PlayCinematic(id[, doneEventId])` starts it from the next frame; `doneEventId` runs when it ends,
  played out or skipped. A map without that cinematic logs it and runs the done event at once, so a script never
  stalls on a missing file. `evt.SkipCinematic()` ends the playing one as a skip (also an unskippable one).
  `evt.CameraShake(intensity, seconds[, x, y, z, innerRadius, outerRadius])` shakes the view (section 5).
  Also for scripts outside cinematics (runtime only, never saved): `evt.MoveDecoration(cog, dx, dy, dz[, seconds])`,
  `evt.PlayActorClip(actor, clip[, loop])`, `evt.FaceActorTo(actor, x, y[, seconds])`,
  `evt.ClearActorPresentation(actor)` (EventRuntimeState `decorationAims` offsets and `actorPresentations`, applied by
  the worlds' `actorRuntimeState` through `applyActorPresentation` and by the decoration model pose), and
  `evt.PlayDecorationClip(cog, clip[, "once" | "loop" | "end"])`: a decoration's moving part (a binding's `part`
  model in indoor_decorations.yml / decorations.yml, authored in the decoration's asset space with clips on one mesh
  node, `DecorationModelSet::poseParts`) plays the clip once and holds its last frame, loops, or stands at its end
  at once (a map shows a part left open again on load); an empty clip returns it to rest (EventRuntimeState
  `decorationClips`). Beethoven's coffin lids are the first (2026-11-10).
- **While it plays** the frame is drawn from its camera (the renderers swap the cinematic's eye, angles and field of
  view in for the render: `IndoorRenderer::render`, `OutdoorGameView::render`; portal visibility, culling and the
  open sky follow it), the party gets an input frame with nothing held (no movement, look, attack, hotkeys, menu),
  and the gameplay HUD is replaced by the letterbox, fade and subtitle overlay (`GameSession::renderCinematicOverlay`).
  The world keeps running (actors, timers, doors, projectiles), as in MM9.
- **Pace**: cues are timed against real-time audio (voice lines, sound ends), so fast mode (Double Speed) and the
  turn-based speeds do not apply while a cinematic takes the view: the whole frame runs at 1x
  (`GameApplication::gameplaySpeed`). An ambient one runs its own timeline at real pace while the party around it
  keeps fast mode (`GameSession::setGameSpeed`); at 2x its voice lines would start over one another.
- **Letterbox**: at full the bars leave MM9's 2:1 picture (a sixth of a 4:3 screen each; none on a screen wider
  than 2:1); they slide in over `letterbox_seconds`.
- **Skip**: Escape, Space, Return or Enter, for a skippable cinematic. The remaining `event` cues run at once in order,
  actors take their last places (`place`, the ends of `move`s, `show`/`hide`), and the presentation cues (sounds,
  subtitles, fades, shakes) are dropped; the next frame the done event runs. MM9 had no skip; ours exists because
  every gameplay step is an event cue (converters must put none in presentation cues). The Escape that skips does not
  open the menu.
- **End**: the update after the one that reached its end (or a skip) finishes it and runs the done event, so the last
  frame still draws the cinematic and a map move its last event asks for happens first, with no party-view frame
  between; a map change ends a cinematic without its done event (an event's start would clear the pending move).
- **Saves**: a cinematic is never saved half played. Saving (quick save, the save screen, autosaves) is refused while
  one plays ("Cannot save during a cutscene"; `GameApplication::quickSaveToPath`); the menu cannot open. A map change or
  a load ends it without running anything (`GameSession::stopCinematics`). Scripts keep progress in their event
  cues and map variables, so a cinematic that ended either way leaves a consistent map.
- **Debug console**: `cinematic list | play <id> [doneEventId] | skip | shake <intensity> <seconds>`.

## 5. Camera shake

`evt.CameraShake(intensity, seconds)`: a smooth tremor of the view's yaw and pitch (two sines each), about one degree at
intensity 1, fading out quadratically over the seconds; shakes add up. With a point, the party feels it fully within
`innerRadius`, fading to nothing at `outerRadius` (pass `outerRadius` for both: MM9's all-or-nothing range). It adds to
the indoor and outdoor views like the melee camera kick, and to a cinematic's camera (its `shake` cue). Transient,
never saved.

Converter rule for EarthQuake (the shipped amplitude is the ShakeAmt bug's 0.5 units, too small to see; we follow the
DATs' ShakeAmount, the designers' intent): `intensity = min(ShakeAmount, 12) / 12` (MM9 clamps at 12 units),
`seconds = QuakeDuration + min(ShakeAmount, 12) / DecayRate`, the point the object's position, both radii its
OuterRadius; InnerDamage, where non-zero, as an `evt.DamagePlayer` in the same handler.

## 6. Converting a cutscene (rules for the converters)

The shared emitter is `level_generation/projects/mm9r_common/cinematics.py` (`Cinematic` builder, `to_yaml`, `check`,
`move_to_pos`, `face_toward`, `vertical_fov`, `lt_direction`); each map's converter builds its cutscenes from the DAT
and the director script and installs `worlds/mm9/maps/<stem>.cinematics.yml` with its other files.

1. **Cameras**: a shot per `Trigger <camera> On` until the next switch, at the camera's DAT position and rotation
   (the map's LT transform; `direction()`/`lt_direction()`), `fov: 73.7` (MM9's 90 across at 4:3). `Target` adds
   nothing (MM9 never aims by it).
2. **Motion**: `MoveToPos marker speed` becomes keys along the line at speed x scale per second (`move_to_pos`),
   stopping where the script cuts away or the camera arrives; `FaceObject obj rate` a direction key where the turn
   ends (`face_toward`); both `easing: linear`. Keep the scripts' bugs that change the picture (IA_CAMERA2's y = x).
3. **Timing**: seconds from the start by following the waits; a callback (arrival, animation key, sound end) at its
   computed time: arrival = distance / speed, animation keys from the `.abc` key times, sound ends from the wav length.
4. **Gameplay steps** (keys, experience, items, doors, monsters removed or shown, exits, dialogue) stay in the map Lua
   as map events the cinematic's `event` cues run, each guarded to run once, and the done event runs any not yet run
   (so a missing file or an old save loses nothing). Sounds the script plays become `sound` cues; voice lines with a
   subtitle (`subtitle` cue, the line's text from the dialogue tables where it exists).
5. **Fades and letterbox**: keep the scripts' `ScreenFadeOut/In` as `fade` cues (MM9's own did nothing, the intent is
   clear); `LetterBox` is the cinematic's default.
6. **Actors**: `show`/`hide`/`place`/`move` cues where the script moves or reveals them; MM9's `IsTurnBased` guard is
   not needed (the cinematic plays in turn-based mode too: the world steps on).

## 7. Implementation (2026-11-06)

- `game/gameplay/CinematicRuntime.{h,cpp}`: the format's parser and validation, `CinematicRuntime` (shots, keys,
  aims, easing, cues, skip, end), `CameraShake`, the `ICinematicWorld` seam (tests fake it).
- `game/app/GameSession`: owns the map's library and the runtime; `updateCinematics` (requests, skip keys, the locked
  input frame), `renderCinematicOverlay`, `playCinematic`, `stopCinematics`; the world adapter runs map events,
  queues sounds, hides actors (the Invisible bit, as `evt.SetMonsterBit`) and places them
  (`ISceneEventContext::setMapActorPosition`, reached through the new `IGameplayWorldRuntime::sceneEventContext()`).
- `game/events/EventRuntime`: `evt.PlayCinematic`, `evt.SkipCinematic`, `evt.CameraShake` (transient requests on the
  event state, never saved).
- `game/app/GameApplication`: `loadMapCinematics`, the save refusal, the `cinematic` console command.
- Renderers: `IndoorRenderer` (camera swap, field of view in the projection, portal visibility and open sky; shake in
  `viewYawRadians`/`viewPitchRadians`), `OutdoorGameView`/`OutdoorRenderer` (the same; the grass and bmodel-world
  culling take the field of view).
- Tests: `tests/CinematicRuntimeTests.cpp` (`--test-case='*inematic*'`, `'*shake*'`): parsing and its errors, camera
  motion and blending, cue timing, the end and done event, skip, actor cues and look-at, shake decay.

Added 2026-11-06 (second pass): actor `face` and `clip` cues, `decoration` cues and the four Lua functions above
(`game/events/EventRuntime` decoration offsets and actor presentations, `game/maps/DecorationModelSet::pose` offset,
the worlds' `actorRuntimeState`, `WorldFxSystem`'s clip lookup by name). Tests: `Cinematic actors face*`, `Actor
presentations*`. Not yet: voice lines positioned at a speaker, the outdoor classic sky's field of view (the enhanced
sky follows the projection), sprite-only decorations do not glide (models do), skin swaps (Njam's freeze).

## 8. Pilot: Isle of Ashes, `book_sinking`

Converter: `level_generation/projects/mm9r_isleofashes/story.py` (`Story.cinematics`, used by
`mm9r_isleofashes_blv/convert.py`, which installs `isleofashes.cinematics.yml`), `story.lua` (the six gameplay steps
as map events 31010-31015, the done event 31019, `evt.PlayCinematic` from the book's Use; the old tick-driven
`cinema` table and the `[MM9Unsupported]` camera stubs are gone). Map conversions are on hold, so the test ran the
emitter alone against the installed map: a hard-linked scratch root `output/mm9_rework/cinematics_pilot_root` with the
generated `isleofashes.cinematics.yml` and the installed `isleofashes.lua` with the new story part.

The emitter's output (17 s, five shots: Camera0, Camera1, Camera2, the 3.5 s pan that sinks toward Camera3's x, x, z
at 100 LT/s while turning 70 degrees toward the boat at 20 degrees a second, Camera3; a fade in from black, six event
cues, five sound cues, the fade out at 16 s) is checked by the engine's parser on load (`GameApplication: 1
cinematics from ...`).

Checks (2026-11-06, `output/mm9_rework/cinematics_pilot_run/`):

- Headless, `mm9r_isleofashes_blv/cinematic_play.yml`: the lectern's Use starts it (`cinematic list` reports it
  playing), a save during it is refused, key 28 is set at 4.5 s and not before, the party arrives in sturmford.blv
  after 17 s. `cinematic_skip.yml`: skipped at 1 s, key 28 and the arrival in Sturmford still happen. Both pass
  (run from `output/mm9_rework/cinematics_pilot_run`, whose settings.ini points at the scratch root:
  `build/game/openyamm --world mm9 --headless-run-scenario <yml>`). `advance_runtime` now carries out a map move an
  event of the step asked for, as the game's frame does (ScenarioRuntimeDriver::advanceRuntime).
- Desktop, engine-native captures through a menu input tour (`tour.yml`: `qbit set 90029`, `event 30496`, captures at
  the shots' times): `captures/00-before.png` (the party at the lectern, HUD), `01-camera0` (the bunker's fort wall,
  letterboxed, no HUD), `02-camera1` (the islet), `03-camera2` (the islet's fort), `04-camera2-pan` (turned toward the
  boat), `05-camera3`, `06/07` (the party arrived in Sturmford with its HUD); `captures/sheet.jpg` is all eight.
  First pass: the islet did not sink and the boat did not sail. Second pass (2026-11-06): the boat sails
  (IS_Boat.scr's MoveToPos to BoatMarker's x and z at 100 LT/s, 24.6 s: `evt.MoveDecoration` in story.lua's `Boat
  move`; `captures_isle2/sheet.jpg` shows it under way in the pan and in Camera3), and the islet is MM9's own Door
  as a mover (`overrides.yml` `Terrain3: {group: Terrain3, motion: dat}`, 1000 LT down at 50 LT/s; story.lua's
  `Terrain3 open` opens it, the load keeps it sunk after key 28). The islet needs the map's conversion (a mover is
  BLV geometry), so until the rebuild the scratch root logs `[MM9Unsupported] Terrain3 open: this build of the map
  has no islet mover`.
- Unit tests: `*inematic*` and `*shake*` (6 cases) pass; the whole suite has only the known failures plus one MM6
  faction-relations case another session is working on. The MM6-MM8 `tests/scenarios/*.yml` pass (11 of 11).

## 9. Camera gate (2026-11-06)

The user found cameras outside the maps or facing walls. The transform was checked end to end first: the cameras use
the converters' own frame (`Project.native`: LT x, z, y times 2.56 less the map's overrides.yml `offset`; the Isle's
`to_map` with its sea level is the same formula), and MM9's Rotation (pitch, yaw: forward = (sin yaw cos pitch,
cos yaw cos pitch, -sin pitch)) points the council's static cameras at their speakers within 4-18 degrees (Camera1
Bjarni 14, Camera2 Sigmund 7, Camera6 Forad 6, Camera9 KiraMarker1 4). The failures are placements: MM9 had no
camera collision, its cutscene stages were sometimes built elsewhere (the council's hall under the city, moved into
the real hall by the Thronheim converter), and the remade geometry differs (Frosgard's pier).

`level_generation/projects/mm9r_common/camera_gate.py` checks every shot, and every quarter second of a moving shot,
against the compiled BLV (drawn faces only): the eye inside the map (14 rays meet faces from the front; rays upward
may escape into open sky), at least 16 units from any face, a look target inside the 90-degree view and in clear
sight, a direction not into a face within 96 units. A failing camera is moved minimally (along its view, then the
nearest clear point; a moving shot's whole path up or along its view) and the move is written into the shot's note.
It runs in `cutscenes.pilot()` (reporting), in `dungeon/build.py` after the map is installed (`gate_cinematics`,
strict: an unresolved camera fails the conversion unless overrides.yml `cinematics_gate` names it with a reason) and
in the Isle converter; `python3 camera_gate.py <stems> [--write]` checks the files in the scratch root.

Results on the scratch root: isleofashes 5 shots, yorwick 8, afterworld 3, hallofthegods 21, wizardslab 3,
bathhouse, thjoradmine, yanmirsfort 1 each: all pass. arslegardcity: Losecam3 (both gate scenes) 48 back along its
view; thronheimcity: council shot 2 (Camera0's move) 16 back. frosgardcity: Camera1's dive under the pier (MM9's
"Under" shot through ice we model as solid) moved 400 units west by the converter (`CAMERA1_SHIFT`), Camera2 at the
map's edge an override (its view reads inward). 1000terrors: the chess cameras (from the party's eye) moved up to
576 units and three hidden targets resolved by the converter (section 8, the agent's notes). The Isle's pan
(captures_isle3) shows the islet's peak beside the boat: that is Terrain3, which MM9 sinks during the shot; with
the converted map's islet mover it is 700-960 units lower by then. The pan now aims where the sailing boat is at its
end (FaceObject follows it).

## 10. All cutscenes (C11, 2026-11-06)

Every cutscene of section 2 is converted in its map's converter (`MM9Cinematic.start("<id>")` from MM9's trigger,
`<stem>.cinematics.yml` installed by the conversion, gameplay steps as guarded map events from 36000, a play and a
skip scenario per scene in the project, captures in output/mm9_rework/cinematics_pilot_run/captures_<id>/), tested
without conversion in the scratch root. MM9's 228 cinema voices are imported
(`tools/mm9_import_discovery/import_mm9_world_audio.py`: worlds/mm9/audio/voices/cinema/<folder>/<file>.wav).
First-sight voiced scenes are `ambient: true` cinematics (no camera, no lock, the HUD stays): Guberland's
`newgame_talk`, Drangheim City's `dwarves_and_humans`, Frosgard City's `bob_and_doug`; Thronheim City's Knut rant is
plain map Lua (a proximity timer). The camera shakes (ruinedtemple, thjoradmine, bathhouse, 1000terrors) are
`evt.CameraShake` in the handlers of what breaks; thjoradmine's ambient quake a map timer. See each project's
README "Cinematics" and FINAL_REBUILD_WORK.md C11 for the list. Engine additions of this pass: actor face/clip
cues, decoration glides, ambient cinematics, the portal walk from the cinematic camera's sector, no health bars or
combat text over a cinematic, the completion certificate waiting for a playing cinematic, scenario
`advance_runtime: {follow_map_move: true}`.

## 11. Shows that are not cutscenes (2026-11-06)

MM9's clock-scheduled shows move no camera: the Guberland Players' play (Narrator.scr at 14:30 and 16:30) and the
Temple of Honk ceremony (HonkLeader.scr at 6:15 and 18:15). They are map Lua with positional sounds, not
`.cinematics.yml` scenes, so the party keeps playing through them ([Ambient sounds](../AMBIENT_SOUNDS.md), "Scripted
voices and scenes").

