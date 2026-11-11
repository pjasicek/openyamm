# MM9 ambient animation: idle, fidget, wander and talk (reverse engineering)

How the original Might and Magic IX chooses the animations of townsfolk and monsters outside combat, what OpenYAMM
does today, and the gaps between the two. Decoded on 2026-11-05.

Status (2026-11-06): fixes 1, 3 and 4 of section 4 are implemented (the plan's
["Ambient animation"](../MM9_MONSTER_AI_PLAN.md#ambient-animation-2026-11-05)), and fix 5, the townsfolk chats (the
plan's ["Townsfolk chats"](../MM9_MONSTER_AI_PLAN.md#townsfolk-chats-2026-11-06)); fix 2 was dropped after a survey (no
MM9 monster or townsperson model has more than one `Stand*` clip); fix 6 is implemented in the converter and the engine
(the plan's ["Marker stops"](../MM9_MONSTER_AI_PLAN.md#marker-stops-2026-11-06)) and reaches the maps at their next
conversion. Section 3 describes the state before them.

- Binary: `mm9/game/data/object.lto`, SHA-256 prefix `b1271f37e5314281`, image base `0x10000000`. The disassembly
  used is `re_mm8/work/mm9_collision/object_lto.asm`.
- Scripts: `mm9/extracted/SCRIPTS/SCRIPTS/`. `NPCBASE.inc` (every townsperson), `BASEWANDER.inc`, `BASECRAWL.inc`,
  `BASEMELEE.inc`, `SHOPKEEPER.scr`.
- Related notes: [native AI](MM9_AI_NATIVE_RE.md) (states, think table §4.2, perception §5) and
  [animation blending](../MM9_ACTOR_ANIMATION_BLENDING_RE.md) (state table, SetState).

## 1. How an animation state becomes a clip

**Clip lists by name prefix.** At first use, the animator fills one list of up to 10 animations per state
(`0x1001d7f0`; per-model record at animator `+0xc`). For each prefix, `0x1001d6f0`:

- uses only the animation named exactly as the prefix, if the model has one;
- otherwise collects `<prefix>0` … `<prefix>9` (format `"%s%d"`, `0x1019b9f4`) that exist.

The prefixes come from the string table at `0x1019bff0`-`0x1019c0a4`.

| State (id) | Prefixes | Loops (`0x1001d0a0`, table `0x1001d0c8`) |
| --- | --- | --- |
| idle (0) | `Stand` | yes |
| fidget (1) | `Fidget`, then `Search`, into the same list | no |
| walk (2), run (3) | `Walk`, `Run` | yes |
| taunt (9), aware (0xa) | `Taunt`, `Aware` | no |
| speak (0x12) | `Speak` | yes (while its sound plays) |
| sleep (0x2f) | `Sleep` (else `STATIC_MODEL`) | yes |
| conversation (0x30) | `Conv` | **no** |
| flyIdle / flyFidget, swimIdle / swimFidget | `StandAir` / `FidgetAir`, `StandWater` / `FidgetWater` | yes / no |

**Which clip of the list plays.** `SetState(state, anim)` (`0x1001d110`, `0x1001d3fd`-`0x1001d433`) plays the named
index when one is given. With −1, the usual case, it picks one **uniformly at random** (`rand() % count`) at each
state entry. A looping state keeps that clip until the state changes. A one-shot state picks again on its next entry.

- Example, the PeasantMale library (`level_generation/creatures/mm9_greenman_claude/source/mm9_lib/pmale.glb`):
  - idle plays `stand1` (no `Stand`, so `Stand0`-`9` → `stand1`);
  - fidget picks among `fidget1`, `2`, `3`, `4`, `5` and `8`;
  - walk plays `walk3`;
  - `Converse` plays only `conv`, because the exact name `Conv` exists (`conv1`-`conv5` never play through
    `Converse -1`).
- PeasantFemale: `stand1`, fidgets `Fidget3` and `Fidget4`, conversation `Conv1`-`Conv3`. Her `Washfidget` and
  `wipefidget` only play when a script names them.

## 2. MM9's rules

### 2.1 Idle and fidget (monsters and townsfolk alike)

- **Idle** plays one random `Stand*` clip, looping, chosen when the actor enters idle.
- **Fidget timer.** Entering idle from any other state sets the next fidget time to now + 5 + rand × 7 s, so
  **5-12 s** (`AIBase::SetAnimState` `0x100168a0`, constants `0x100ee5c8` = 5, `0x100eef30` = 7,
  `0x100eeed0` = 1/32768; field `+0x72c`). Re-requesting idle while already idle keeps the old time.
- **The idle think** (`+0x5cc` → `0x10013060`) with no target:
  - fidget time reached (`+0x684` → `0x10016860`) → `+0x680` → `0x10013040`: clear the timer and `SetState(fidget,
    -1)`, which plays one random `Fidget*`/`Search*` clip once;
  - otherwise the target search runs (perception, MM9_AI_NATIVE_RE.md §5).
- When the fidget ends, the done dispatcher (`0x1001ea50`, state 1 → `0x1001ea8f`) sets idle again. That sets a
  fresh 5-12 s timer and picks a fresh `Stand*` clip.
- **So a standing actor fidgets once every 5-12 s plus the fidget's own length**, choosing uniformly among its fidget
  clips. There is no weighting and no fixed order.
- **Where fidgets happen.** Only idle runs the fidget timer. Walking, running, taunt, wince, strafe, the attack and
  speak states never fidget, and the fidget think (`+0x5d0` → `0x1001c7e0`) only tracks a target or searches.
- **A script's `LoopAnim` or `PlayAnim` stops the fidgets** (traced 2026-11-10). The command (`LoopAnim` vtable
  `0x10181f04`, run `0x100a7dd0`; `PlayAnim` `0x10181f14`, run `0x100a7c90`) calls actor slot `+0xbc`
  (`0x1000de70`: loop when the count is -1, stores the clip at `+0x424` and the count at `+0x428`) → `+0x248`
  (`0x10002300`) → animator slot 2 (`0x1001d560`, the blending animator's `0x1001f6b0` calls it first), which sets the
  animator state to **0x11** and plays the clip. The update's think dispatcher (`0x1001e870`, byte table `0x1001ea10`)
  sends state 0x11 to slot `+0x5d4`, the same `0x1001c7e0`: track or search, no fidget timer. So an actor looping a
  script clip never fidgets until its script sets another state (`Stop`, a walk); entering idle from 0x11 then arms
  a fresh 5-12 s timer (`0x100168a0`, the current state is not idle).
- **Per family:**
  - Fliers and swimmers use the `StandAir`/`FidgetAir` and `StandWater`/`FidgetWater` lists in their flyIdle and
    swimIdle states. The timer was not traced separately.
  - The Flying Icky's hanging fidget is scripted (`FlyingIcky.scr`, 2-10 s).
  - Lobbers scan by turning (`lobber.scr`).

### 2.2 Wandering and paths (`BASEWANDER.inc`)

- **Aimless:**
  - `Walk` (walk state, random `Walk*` clip) for 3-8 s (`MIN/MAX_WANDER_TIME`, lines 11-14), then `Stop`, which
    puts it in idle;
  - wait 3-8 s (`BaseWanderStart`, lines 525-550), turn a random 15-180° either way at 180°/s (15-90° after an
    obstacle; back toward the start beyond the leash; lines 352-385), walk again.
  - Leash check every 0.25 s.
- **Path markers:**
  - `WalkTo` the marker, then `OnWanderAtMarkerNext` (lines 58-110): `Stop`.
  - If the marker says `UseMarkerRotation`, face the marker's direction at 360°/s.
  - If the marker says `PlayAnim`, play its `AnimationName` once (`PlayAnim`), or loop it (`LoopAnim`).
  - Then wait the marker's `WanderWaitMin/Max` or the placement's 3-8 s, and walk to the next marker.
- **At stops** the actor is in idle, so the native fidget timer runs. With 3-8 s waits and a 5-12 s timer, a fidget
  at a stop is the exception. There is no scripted look-around: the only turn is the random re-heading. A marker's
  looped clip, or a script that loops its own clip while it waits (`MonkGuardBasic.scr`: `LoopAnim` of the pause or
  the chore), holds the script state 0x11 and does not fidget (§2.1).

### 2.3 Townsfolk chatting with each other (`NPCBASE.inc`)

A townsperson **without a path and without a leash** (`BaseWanderStartup`, lines 775-793) socialises:

1. Every 5-15 s (`MIN/MAX_SOCIALIZE_WAIT`) it looks for another NPC for 5-10 s (`OnFoundTarget`, the perception of
   MM9_AI_NATIVE_RE.md §5).
2. It greets the NPC it finds (`Hello`) and walks to it (`GoChat`, `WalkTo`, giving up after 4-10 s).
3. On arrival both stop, the partner turns to face it at 180°/s (`OnChatBegin`, `FaceObject g_hTarget, 180`,
   line 300), and they take turns with `Converse -1`.
   - `Converse` is the `conversation` state (native `0x1009b230` → `SetState(0x30, …)`): one random `Conv*` clip,
     not looping.
   - Each finished clip hands the turn over (`OnConverseDone` → `YourTurn`).
4. After 10-30 s (`CHAT_MIN/MAX`) each turns 180° ± 45° (`LeaveChat`, lines 346-366) and resumes wandering.

### 2.4 Talking with the party

**Native NPC "use"** (`NPC` class `+0x1e4` → `0x1003d0d0`). When the player uses an NPC:

1. If the placement has a `GreetingSound`, it plays as the NPC's voice (`+0xbb4` → `+0x298` → `0x10003140`).
2. If `DoRude` is set (`+0xbb8`):
   - the NPC saves its current animation state (`+0xbbc`);
   - **it goes to idle** (`SetState(0, -1)`: a random `Stand*`);
   - it stops moving (`+0xdc`);
   - **its whole body turns toward the player at 540°/s** (`+0x94`, `0x44070000`).
3. The RUDE dialogue opens on the client (message 0x1a with `RUDENPCId` `+0xbac`). The combat manager disables
   attacks (`0x100b3570(0)`).

**Script side** (`NPCBASE.inc` `OnUse`, lines 516-536, through the `Use` trigger):

- disable chat and wandering, `Stop`, `SetIdle`;
- store its facing (`GetFaceDir`);
- `Target <player>, FALSE`: the player becomes the target, without the body following it.

**Head.** `SetTarget` (`+0xa8` → `0x10011600`) sends the clients message 0x3a when the row's `HeadTurn` column
(record `+0x76`, getter `0x10016c20`; 204 rows 1, 66 rows 0) allows it:

- sub-message 0x3b with the new target and 90.0 (`0x42b40000`): **the client turns the head toward the target, up to
  90°**;
- sub-message 0x3c clears it.

So a townsperson the party talks to also follows the party with its head.

**No talk or gesture clip plays.**

- Nothing on the use path, in `NPCBASE.inc` or in the RUDE hand-over sets `conversation` or `speak`.
- The NPC stands in its `Stand*` loop for the whole dialogue.
- `Conv*` clips play only in NPC-to-NPC chats (§2.3) and in a few scripted scenes (`AKE.scr`, `KNUTSPEECH.scr`).
- `Speak` (state 0x12, `0x10015800`: loops until its sound ends) is only reached through the script command
  `Speak` (`GOBLINCIN1.scr`).
- Whether the idle fidget timer can fire during a long dialogue (the server keeps updating the NPC) was not traced.

**After the dialogue** (`NPC +0x710` → `0x1003d260`):

- the native code raises `OnRUDEExit` (event 0x18), **restores the saved animation state** (for example walk), and
  re-enables attacks.
- The script (`OnRUDEExit`, lines 538-552), without a marker: re-enable wandering and chat and **turn back to the
  facing stored at the use, at 180°/s** (`FaceDir g_dirX, g_dirY, g_dirZ, 180`).
- With a marker: `WalkTo` the marker again.
- A shopkeeper (`SHOPKEEPER.scr`) only plays its sound on use.

### 2.5 Taunts and other one-shots outside combat

- **Taunt clips are combat only** in the base scripts:
  - on noticing a target, 40 % (`BASECRAWL.inc` `OnFoundTarget`, lines 714-745, `AWARE_CHANCE`);
  - after a strafe attack's backpedal, 40 % (`BASEMELEE.inc` lines 191-211);
  - after a kill (`KilledTargetTaunt`).
- No wander or NPC script taunts. `Aware` plays for the Lobbers and a few special scripts.
- Townsfolk have no taunt. Their `Cower` is used by `BaseRun.inc` when they flee without a hiding place.

## 3. What OpenYAMM did (2026-11-05, before the fixes)

### 3.1 Clips available

- The converted MM9 models (`assets_dev/worlds/mm9/models/mm9_*.glb`, 125 models) keep **one** `Standing` and
  usually one `Fidget`. There are 79 extra numbered fidget clips (`Fidget2`-`Fidget4`) across the models, and 9
  models have `Search`.
- `Talk` (42 models) is one chosen `Conv*` clip. `Conv1`-`Conv5` appear on 37.
- `actors.yml` binds `standing` and `fidget` as AI clips. `fidget2`, `fidget3`, `talk`, `conv*`, `taunt` and the
  prop fidgets are `script_clips`, played only when a behaviour or modifier names them
  (`IndoorWorldRuntime.cpp:14884`; `ActorBehaviorRuntime.cpp:2408`).
- The converter dropped the other `stand*`, `fidget*` and `conv*` of the PeasantMale and PeasantFemale libraries
  (README of `mm9_annud_claude`, line 40).

### 3.2 Idle and fidget

- `AI_Mm9IdleStand` → `AI_StartIdleStand` → MM8's `idleStandBehavior` (`GameplayActorAiSystem.cpp:436`):
  - every decision is 1.5 s standing or, **50 %** (`actorChoosesBored`, `ActorVocalizationRules.h:19`), 2 s
    "bored";
  - the presentation plays the one `fidget` clip to its end (`WorldFxSystem.cpp:1626-1638`).
- So an MM9 actor fidgets about every 3-4 s, always with the same clip. MM9 does it once per 5-12 s with a random
  variant.

### 3.3 Wander

- The MM9 wander (`AI_Mm9Idle`, `:6849`) walks with `Walking` and waits `wander_wait`, with the idle above.
- Marker rotation, marker `PlayAnim` and `LoopAnim`, and the NPC-to-NPC chats with `Conv*` are not implemented. The
  converter keeps no marker animation data.

### 3.4 Talking with the party

- **Outdoor:** `faceTalkingActor` (`OutdoorInteractionController.cpp:4726`) → `faceMapActorTowardPoint`
  (`OutdoorWorldRuntime.cpp:19781`):
  - an **instant** turn to the party, for non-hostile actors only;
  - standing, held for 2 s;
  - while the dialogue is open the world is paused and only the speaker's model keeps animating
    (`GameApplication.cpp:8112`, `liveActorIndex`).
- **Indoor** (where most MM9 towns are now BLVs): **no turn at all**. Together with the indoor start-yaw bug
  (MM9_AI_NATIVE_RE.md §5.4, item 1), townsfolk face +X while talking.
- **Head:** the `look` binding (181 MM9 bindings; `WorldFxSystem.cpp:1281`) turns neck and head toward the party
  whenever it is within 2 048 and no scripted clip plays: max 60° yaw and 35° pitch, in and out of dialogue, for
  every model. MM9 does this only for its current target and only for `HeadTurn` rows, up to 90°.
- **No talk clip**, which matches MM9.
- The party's view stays where it was (the talk camera that eased it onto the speaker was removed on 2026-11-06); the
  talk ring shows the speaker's head instead.
- **After the dialogue:** nothing restores the facing or the previous state. The actor's AI continues from where it
  was.

### 3.5 Taunts

`taunt` plays for skirmishers in combat and `aware` on detection (`IndoorWorldRuntime.cpp:14891-14922`). There is
nothing out of combat, which matches MM9.

## 4. Gaps and proposed fixes

All the fixes below are data-driven, with no world branches.

1. **Fidget frequency and variety.**
   - OpenYAMM fidgets about every 3-4 s with one clip; MM9 fidgets once per 5-12 s after entering idle, choosing at
     random among all `Fidget*`/`Search*` clips.
   - **Fix:** give the MM9 profile's idle (or a world `actorIdle` setting read by the shared idle) a fidget timer
     (min 5, max 12 s, reset when the actor enters idle).
   - Let a binding list several fidget clips (`clips.fidget: [Fidget, Fidget2, Fidget3, Search]`), picked uniformly
     per fidget.
   - MM6-MM8 keep the current single clip and timing.
   - **Done:** `AI_Mm9IdleStand` (every MM9 loop actor) and the manifest's `fidget_variants: true`, which lists the
     binding's `fidget` and its `fidget<n>`/`search<n>` script clips (the converted models already carry MM9's
     numbered clips under those roles, of the right medium for fliers and swimmers), so no binding changed.
2. **Stand variants.**
   - Only one `Standing` exists. MM9 picks a random `Stand*` per idle entry; this only matters for models that have
     several.
   - **Fix:** let the converter keep every `stand<n>` of the source library, and allow a `standing` list in
     `actors.yml`, chosen at each entry into standing.
   - **Dropped:** a survey of the 99 animated MM9 models (`convert_abc_model.read_abc`) found more than one `Stand*`
     clip without an exact `Stand` only on the player models and the Rabbit. Every monster and townsperson has one.
3. **Talk turn, indoor.**
   - Indoor actors do not turn at all; outdoor ones snap.
   - **Fix:** one shared "face the speaker" request from both interaction controllers. It saves the actor's yaw and
     animation state, turns the body at a rate from data (MM9 profile 540°/s, MM6-MM8 instant), and sets standing.
   - On dialogue close, restore the saved state and turn back at 180°/s (NPCBase's `OnRUDEExit`), or resume the
     path.
   - First fix the indoor start yaw (MM9_AI_NATIVE_RE.md §5.4).
   - **Done:** `faceMapActorForTalk` in both runtimes, called by every dialogue path (MM9 RUDE, NPC, generated NPC,
     news). The AI yaw turns at once and the 3D model eases to it at 540 degrees a second, MM9's rate, for every world;
     MM6-MM8 sprites turn at once. An MM9 actor keeps its facing (`ActorMm9State::beginTalk`) and its idle turns back
     at 180 degrees a second; a walk (its path's next marker, an aimless walk) or a target cancels the turn back. The
     saved animation state is not restored: the MM9 loop resumes from its own state, which is where MM9's restored
     state would put it (a walk walks on). Deviation: an aimless walk resumes facing its way at once, where MM9 turns
     back at 180 degrees a second while it walks.
4. **Head look.**
   - Ours looks at the party within 2 048 for every bound model, at any time. MM9 looks only at the current target
     (the party when talking or fighting) and only for `HeadTurn` = 1 rows, up to 90°.
   - **Fix:** a binding or profile field `look.target: target` (look only at the AI's target or the dialogue
     partner), and the importer writes no `look` for `HeadTurn` 0 rows. Keep the party-in-range look for MM6-MM8
     bindings.
   - **Done:** the profile's `head_turn` (false for the 51 `HeadTurn` 0 rows, generator) and
     `GameplayRuntimeActorState::looksAtHeldTarget`: an MM9 loop actor's look follows only the target its AI holds
     (the party, or another actor's head) or the party while it is the dialogue partner, at any distance. The bindings
     are unchanged, so the turn stays within each model's `max_yaw_degrees` (60, or 50) where MM9 allows 90. MM6-MM8
     bindings keep the party-in-range look.
5. **NPC-to-NPC chats.**
   - Missing: wandering townsfolk without a path or leash meet every 5-15 s, walk together, face each other and
     alternate `Conv*` clips for 10-30 s.
   - **Fix:** a civilian `socialize` behaviour in the MM9 townsfolk loop, with the NPCBase timings in the profile and
     `conv` clip lists in `actors.yml`, picked uniformly per turn and played once.
   - **Done** (2026-11-06, indoors): `AI_Mm9Chat` with the world's search (`answerMm9ChatSearch`); the timings are
     NPCBase.inc's constants (no profile fields), the Conv clips the bindings' `conv`/`conv<n>` script clips. Limits in
     the plan's "Townsfolk chats".
6. **Marker rotation, wait and animations.**
   - MM9 path markers can set the facing, their own wait and a clip to play or loop at each stop. The converter drops
     all three.
   - **Survey** (2026-11-06, with the DAT object reader of `transcode_mm9_dat_to_odm.py`). Every marker is DAT class `Marker` (735 in all maps), with `AnimationName`,
     `LoopAnim`, `UseMarkerRotation`, `UseMarkerWaitTime`, `WanderWaitMin/Max` and `Rotation`. There is no `PlayAnim`
     property: the marker's stat getter (`0x10075f00`) answers 1 when `AnimationName` (`+0x478`) is set
     (`0x10075fe6`-`0x1007601b`); the same getter reads `UseMarkerWaitTime` `+0x47c`, the waits `+0x480`/`+0x484`,
     `UseMarkerRotation` `+0x488` and `LoopAnim` `+0x489`. `BASEWANDER.inc` lines 58-110 at a stop: Stop, the marker's
     own wait if it has one (64-77), with `UseMarkerRotation` a horizontal turn to its facing at 360°/s (79-83), the
     clip by name if the model has it, looped or once (85-98), then the ordinary wait (502); the next walk replaces the
     clip. 26 markers have a clip, 102 a facing, 86 their own wait; of the 78 path walkers, 62 pass a facing marker,
     63 a marker wait and only 8 a clip marker (2 ClanSoldier guards in Guberland city and 2 in Thronheim city, the
     Thjorgard cutpurses, Hatlati in Sturmford city, Yanmir). The clips are numbered fidgets, a taunt and one looped
     attack, **not** prop clips: `HoeFidget`, `sweepfidget` and `WashFidget` belong to `WORKINGMONK.scr`, which no
     placement or row uses. `mm9_peasantm2` lacks Hatlati's `fidget5`. 14 Frosgard city path walkers run
     `NPC181`-`NPC199.scr` (only `globals.inc` and `pledge.inc`), so in MM9 they may not wander at all: worth checking
     against the converted scene, which makes them walk.
   - **Fix:** path points become `{at, face, wait, clip, loop}` (converter: `mm9_ai_placement.py` and both marker
     caches, `content.py` and `transcode_mm9_dat_to_odm.py`; the map session reconverts 7 maps), parsed in
     `Mm9MonsterAi.cpp` (the old form still read); at the stop `AI_Mm9Idle` takes the marker wait, turns at 360°/s and
     keeps the clip until a walk or a target clears it, shown as a script clip (looping added; the role `fidget` falls
     back to the AI's fidget). The facing and wait are the main payoff (about 60 placements).
   - **Done** (2026-11-06): as above, `path_stops: [{point, face, wait, clip, loop}]`; the clip shows as a script clip
     that loops or releases at its end (`GameplayRuntimeActorState::ScriptedClipEnd`). Arena `marker_stops`.
7. **Talk clip.** None needed: MM9 plays none. Keep `talk` as a script clip for scripted scenes only.
8. **Script loops and chores** (2026-11-10). A looped script clip holds MM9's script state 0x11, which never fidgets
   (§2.1). Lindisfarne Monastery's monks showed the gap: all 27 stood and fidgeted, and `Fidget2` is the monk's
   "who's there?" voice, so it sounded throughout the monastery. In MM9, `MonkGuardBasic.scr` loops a clip whenever its
   monk stands, chosen by the type in its first script parameter: the prayer (0) loops `stand` while it waits between
   walks, the hoe (1) and broom (2) monks `hoe` and `sweep` at each stop, the hammer (3) and wash (4) monks their work.
   `ThjoradMonk.scr` loops its first parameter (`Pray`, `Hammer`) and, after the bells, `pray`. Only the chatting
   monks (-1) and the four named NPCs fidget. Their `Fidget` (MM9's `fidget1`) carries the `PrayMumble` key, so 4 times
   in 10 it mumbles a prayer (`MonkSounds.inc`). The `HoeFidget`/`SweepFidget`/`HammerFidget`/`WashFidget` clips are not
   only `WORKINGMONK.scr`'s (item 6): `MonkGuardBasic.scr` plays one once when a working monk is talked to.
   - **Done:** scene `mm9_ai.idle_clip` (`Mm9AiPlacement::idleClip`, saved from version 173; older saves take it
     from the scene on the map's next entry): `AI_Mm9IdleStand` stands without fidgets while it has one, or while a
     marker's looped clip holds, and the fidget is armed anew once the loop ends. The world runtimes show the clip,
     looped, while the actor stands without a target, its AI awake or not. A marker's clip played once still lets the
     timer run. Lindisfarne's converter sets the monks' clips; `generate_mm9_monster_sounds.py` reads the `PrayMumble`
     key (it looked for `pray`).
   - **Tools** (2026-11-10, item 10): the hoe, broom and wash monks hold MM9's tools (`held_items`). Not done: the
     working monks' fidget on a talk.
9. **Routines** (2026-11-10). MM9's scripted work and scenes beyond a looped clip (a miner's walk to the rock face
   and back, a drill, a ceremony) are a placement's `mm9_ai.routines`: named lists of steps the MM9 loop runs round
   and round while the actor holds no target, in place of its wander and chats (`AI_Mm9Routine`). `default` runs from
   the start; a map script switches with `evt.SetActorRoutine(actor, name)` (no name: none; runtime only, set again on
   load). Steps, written by the map converters:
   - `{walk: [x, y, z]}`, `{run: [x, y, z]}`: to the point by its own steering (given up after 40 s or if it may not
     move: a routine walker must not be `immobile`);
   - `{face: degrees}`: turns there (map frame, as `path_stops`) at 360 degrees a second;
   - `{clip: name, seconds: s}` or `{clips: [{clip, seconds}, ...]}` (one picked at random): stands and plays the
     clip, looping within its seconds (a clip's own length plays it once), without fidgets;
   - `{wait: [minimum, maximum]}`: stands idle (its idle clip or its fidgets);
   - `{chance: p, steps: [...]}`: the group with chance p, else skipped;
   - `{items: hide}`, `{items: show}`: puts its held items down and takes them up (DetachProp and AttachProp around a
     trip).
   Saved with the placement record from save version 174 (older saves take them from the scene on the map's next
   entry). Clip seconds come from the model's clip lengths (the converter reads them). Tests: `*MM9 routine runs its
   steps*`, `*parses its routines*`.
10. **Held items** (2026-11-10). MM9's `AttachProp` (a monk's hoe, a miner's axe, a Honk's pamphlet) and the pieces of
   MM9 prop models our bodies lack (Ercc's cup) are a placed actor's scene `held_items: [{model, node}]`
   (`MapDeltaActor::heldItems`, saved from version 174), drawn on its 3D model after its binding's attachments; map
   scripts change them with `evt.AttachActorItem(actor, model, node)` and `evt.DetachActorItem(actor[, node])`, and a
   routine's `items` steps hide them for a while. The items are MM9's own models
   (`level_generation/props/mm9_held_items_claude/`: `worlds/mm9/models/mm9_item_*.glb`); the nodes are MM9's sockets
   carried onto our creature models as `Socket_<name>` (the same project's `add_sockets.py`: monk `Socket_Hoe`,
   `Socket_Broom`, `Socket_Hammer`, `Socket_Cloth`; dwarf peasants and the dwarf `Socket_RHand1`; Honks
   `Socket_pamphlet`; the townsman `Socket_Cup` for Ercc's cup).
