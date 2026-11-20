# Handoff: MM9 monster AI, spells and animation (2026-11-06)

For a session taking over the MM9 monster work. It summarises where things stand and links to the documents that hold
the detail. Nothing here is committed: all of it is unstaged work in the tree (the user reviews in VS Code and commits).

## Read first

| Document | What it holds |
| --- | --- |
| [MM9_MONSTER_AI.md](MM9_MONSTER_AI.md) | The approved design: native archetypes, data flags, Lua only for bosses |
| [MM9_MONSTER_AI_PLAN.md](MM9_MONSTER_AI_PLAN.md) | The plan, its rules, the **user's decisions** ("Decisions after the plan"), status and a section per phase (2, 3, 4a, 4b, 5, recovery, perception, repositioning) with quirks reproduced, limits and assumptions |
| [monster_ai/MM9_AI_NATIVE_RE.md](monster_ai/MM9_AI_NATIVE_RE.md) | MM9 binary RE (`mm9/game/data/object.lto`): §5 perception, §7.2.1 recovery, §7.2.2 spell choice and `concat`, §7.2.3 in-reach rule and Lobbers, open list §16 |
| [monster_ai/MM9_AI_DATA_AND_SCRIPTS.md](monster_ai/MM9_AI_DATA_AND_SCRIPTS.md) | `MONSTERS.txt` columns, script families, per-archetype behaviour with script citations |
| [monster_ai/PROFILE.md](monster_ai/PROFILE.md) | The generated AI profile and placement fields, the placement-script survey and which maps still need conversion |
| [monster_ai/MM9_AMBIENT_ANIMATION.md](monster_ai/MM9_AMBIENT_ANIMATION.md) | Idle, fidget, wander, talk, chat and taunt animation in MM9 versus ours, with fixes: 1, 3, 4, 5 done, 2 dropped, 6 surveyed |
| [monster_ai/OPENYAMM_AI_CURRENT.md](monster_ai/OPENYAMM_AI_CURRENT.md) | How the shared AI worked before this work (partly superseded) |
| [MM9_SPELL_MAPPING.md](MM9_SPELL_MAPPING.md) | MM9 spells onto MM6-MM8 spells: inventory, mapping applied (§6), traps |
| [MM9_ANIMATION_AUDIT.md](MM9_ANIMATION_AUDIT.md) | Animation blending audit and its "Follow-ups done" section |
| [MM9_ACTOR_ANIMATION_BLENDING_RE.md](MM9_ACTOR_ANIMATION_BLENDING_RE.md) | MM9's two animation tracks (`Top` weight set) |
| [../MONSTER_MODIFIERS.md](../MONSTER_MODIFIERS.md) | The per-world `modifiers.yml` fields, including `mm9_ai`, `spell_conditions`, `reposition` |
| [../../tests/scenarios/mm9/ai/README.md](../../tests/scenarios/mm9/ai/README.md) | The AI arenas: format, how to run them in the window and headless, the trace, every arena |

## User rules that govern this work

- **MM9 as MM9 plays it.** Reproduce MM9's behaviour, quirks included, and record each quirk in the plan. Deliberate
  deviations are the user's call and are recorded as decisions (Fear on fliers, corpses kept for loot, repositioning
  casters, turn-based mode).
- **No world branches.** No `if (mm9)` or world-id checks. A behaviour is one shared code path; worlds differ by data
  (`modifiers.yml` fields, the MM9 AI profile, bindings). MM6-MM8 rows that don't set a field behave as before.
- **MM6-MM8 must not regress.** Where a shared fix changes them (it has, several times), say so and verify.
- **Data is generated, never hand-edited**: tables from `tools/mm9_import_discovery/`, placements from the MM9 map
  converters. Boss Lua in `assets_dev/worlds/mm9/behaviors/` is hand-written content.
- **Map conversion belongs to another session** (the map generation session). Don't run reconversion queues; converter
  changes reach maps at that session's next conversion. Never run a `-j` build while any `convert.py` runs (OOM):
  check by exact pid and build without `-j` meanwhile.
- **Waits:** wait on exact pids (`kill -0`) or output files, never `pgrep -f` with text from your own command line
  (11 such loops hung overnight on 2026-11-04).
- No git staging, no `rm` with variables or wildcards, `assets_dev` files are hard links (temp file + rename), never
  `--set` before `--headless-run-scenario`.

## Current state (done)

All phases of the plan are implemented, plus the follow-ups below.

- **Harness (phase 0):** decision trace (`ActorAiTrace`), arenas (`game/debug/AiArena`, `debug.ai_arena_path`,
  console `arena load|reload|trace|overlay|dump|anim`), scenario steps `ai_arena`, `assert: ai_trace` (with
  `max_in_window`), `ai_trace_dump`; animation trace (`trace_animation`), screenshot bursts
  (`debug.screenshot_burst_count`, `debug.screenshot_burst_interval_ms`). Every arena has a party (invulnerable).
- **Profile (phase 1):** `mm9_ai` row modifier and per-placement `mm9_ai` (scene), `Mm9MonsterAi.{h,cpp}`.
- **Behaviour:** walkers (crawler, skirmisher, ranged holder), fliers, swimmers, turrets (Lobbers); patrols, leash,
  flee to hiding places, cower, alerts and help calls, resurrection, monster-opened doors; townsfolk, guards, MM9
  factions (`worlds/mm9/relations.yml`), dormant starts, spawn-ins; bosses in Lua (Dragon King, Njam, Ebora, Yanmir,
  summoners). Code: `game/gameplay/GameplayActorAiSystem.cpp` (MM9 loop), `Mm9ActorRules.{h,cpp}`,
  `ActorRepositionRules.h`, `ActorBehaviorRuntime`, both world runtimes.
- **Recovery:** MM9 `Recovery` is game seconds at 33 ms each (30 → 0.99 s), counted from the clip's end; a hit or
  release arms it; a wince before the hit leaves none; spells use their `SPELL.txt` recovery.
- **Spells:** MM9 spells mapped onto MM6-MM8 spells; debuff spells leave their condition (`spell_conditions`);
  spell choice follows MM9's two rolls (spell versus shot by Att%, which spell by SpellUse%1); in reach every MM9
  monster strikes (no MM9 monster holds a ranged weapon); `concat` and `Bonus` on-hit specials removed (MM9 never
  reads them). Shared fixes for every world: indoor monster spells roll their dice, Stone Skin gives AC, monster Sparks
  fires its volley by mastery.
- **Placement scripts win:** a placement's `ScriptName` overrides archetype, ranged add-on and hooks
  (`mm9_ai.profile`); 435 placements differ, survey in PROFILE.md. Sturmford's prison guard is `passive`.
- **Animation:** flicker fixes for every 3D monster, hits at the model's own clip key (`attack_timing: clip` in
  `worlds/mm9/models/actors.yml`; an authored `sprite_attack_timing.yml` frame still wins), whole-body attack layers
  for the MM9 fliers, no layer where MM9 has none, mummy wake clip, 0.1 s death blend, smoothed gait.
- **Perception:** indoor actors start at their placement yaw (every world; 35 MM7/MM8 actors changed), per-actor
  outdoor engagement and indoor activation from the actor's senses (cap 48 MM9 actors thinking, nearest first), MM9
  eye height, outdoor spawns keep `mm9_ai`.
- **Repositioning casters** (OpenYAMM addition): `reposition` modifier on Evil Apprentice/Sorcerer/Grand Sorcerer
  (rows 156-158); they search for a spot that sees where they last saw the target, and back off when rushed.
- **Ambient animation** (2026-11-05, the plan's "Ambient animation"): MM9's idle fidget (once 5-12 s after entering
  idle, a clip picked among the model's: `fidget_variants: true` in `worlds/mm9/models/actors.yml`), the talk turn
  (every world's NPC faces the party on talk, indoors too now; an MM9 one turns back at 180 degrees a second) and the
  head look (an MM9 actor looks only at its held target or the party talking to it; none for `head_turn: false`
  rows). Stand variants dropped (no model has several).
- **The 2026-11-06 batch** (the plan's sections of that date): timed conditions from MM9 spells (`spell_conditions`
  minutes from SPELL.txt, `Character::conditionExpireGameMinutes`, save 157); MM9 projectile blasts (`missile_blast`
  from PROJECTILE.txt's damageRadius, [MM9_PROJECTILES_RE.md](MM9_PROJECTILES_RE.md): no falloff, no homing in MM9);
  marker stops on paths (`path_stops` from the converter, facing, wait and clip; arena `marker_stops`; the maps get
  them at their next conversion); a backpedal without its clip plays the gait forwards; the Wolf's Trot
  (gait rollout package q5: `run: Trot`, `sprint: Running`).
- **Drawn size apart from the body** (2026-11-06, with the map session): scene actor `draw_scale` (the 3D model's scale
  against its binding's; MM9_MONSTER_COLLISION_RE.md "Placed actors"); the converters write it at the next conversion.
- **Townsfolk chats** (2026-11-06, the plan's "Townsfolk chats"): NPCBase.inc's socializing, indoors: a townsperson
  wandering aimlessly without a leash looks for the nearest one it sees every 5-15 s, walks over, they take turns at
  Conv clips for 10-30 s and part. `AI_Mm9Chat`, `IndoorWorldRuntime::answerMm9ChatSearch`, arena `townsfolk_chat`.
- **Saves:** versions 146 (chosen RUDE rows), 147 (placement profile fields), 148 (hiding places), 149 (placement
  profile overrides), 150 (outdoor spawn `mm9_ai`).

**Tests (last full run, 2026-11-06 after the batch: chats, timed conditions, blasts, marker stops, backpedal):** all 43
arena scenarios (with `townsfolk_chat`, `marker_stops`) and the MM8 actor scenarios pass, except
`mm8_right_click_portrait_item` (failing before this work). The reposition arenas hold the Arena's pen doors open
(`door: {id, hold: true}`): since the map session's 2026-11-05 rebuild they shut 5 s after opening (MM9's
`CloseWaitTime`). Unit suite: 2678 of 2681 pass; the three failures are other sessions' work (MM9 chest icons, the
MM9 RUDE equip positions of the Poor Sword, Hesper staged missiles). Builds: after a `/fast` make (which skips the
dependency step) or another session's header edit mid-build, objects go stale (crashes in `Party::seed`, heap
errors at a test's end): touch the changed headers, or clean `build/game` and `build/tests`, and rebuild. Other sessions rebuild `build/` while runs go on
(a run then aborts on exit or cannot start the binary): run long queues from a copy of the binaries. Run commands are in the
arena README (`mm8_melee_out01` without `--asset-root`; `jellyspore` with
`--asset-root output/mm9_rework/isleofashes_blv_root --world mm9`; the rest with
`--asset-root output/mm9_rework/assets_dev --world mm9`).

## Desired state (next work)

### Open questions for the user

- The Evil Apprentice's corrected strides need a look in the creature viewer.
- The Grey Wolf's chase still plays its Running at x1.78: a longer-stride gallop (about 16.9 model units/s) would fit.
- 14 Frosgard city path walkers run `NPC181`-`NPC199.scr` (only globals.inc and pledge.inc): in MM9 they may not wander
  at all, while the converted scene makes them walk (map session).
- Beethoven's `scenario_doors_exits` fails because a Bone Thrasher legitimately opens door 21/22 (MM9 monster door
  rule); the map project's `make_scenarios.py` should clear actors or check doors without AI (map session).
- Beethoven fails to convert: its `LobberPodB0` is `CacheOnly 1`, which `Content.monster_bases` now skips (map
  session's converter change).

### Later items (recorded in the plan)

- Turn-based mode stays MM6-MM8's; later, choose an MM9 monster's action the MM9 way inside the MM6-MM8 turn.
- A sleep tier for far actors.
- Map Lua should send the boss triggers (`evt.TriggerActor`: Lich Lab summoner, Ebora's mine sequence, Njam's chase)
  and spawn the Dragon King's mutants targeting him.
- Outdoors: script targets, wince-cut attacks and actor-versus-actor perception are indoor only.
- MM9 spell traps: a shared shooter object (design in the spell mapping doc) only if needed; the converters already
  emit `evt.FireMissile` for damaging shooters.
- The 11 outdoor MM9 maps (bootcamp, drangheim, guberland, isleofashes, lindisfarne, mountainpass, sturmford,
  thjorgard, yorwick and two authored variants) lack `mm9_ai` placement data until the map session reconverts them;
  29 maps still need conversion for the placement-script overrides (list in PROFILE.md "Conversion status").
- Isle of Ashes lighting (the user's "last step").
- Ambient animation limits (the plan's "Ambient animation"): an aimless walk resumes its heading at once after a talk
  (MM9 turns back while it walks); fliers and swimmers share the idle fidget timer (MM9's flyIdle/swimIdle not traced).
- Chats are indoor only (the outdoor runtime carries no MM9 requests); the plan's "Townsfolk chats" lists the rest.
- OnFoundPlayer greetings (2026-11-06): both runtimes fire a RUDE greeting when `mm9Perceives` the party (placement
  sight in front, hearing all round, a clear line), searched once a second; Bootcamp's Grandpa and the Afterworld's
  Skraelos checked (`mm9/found_player_bootcamp.yml`, which needs `advance_runtime: {present_dialogs: true}`: a
  headless run otherwise leaves a queued dialogue queued). Missing, for the map session: the voiced first-sight
  scenes, which need MM9's `voices/cinema` imported: Broccan's new-game talk (Guberland, `NPC150.scr`, key 5020),
  "Bob and Doug" (Frosgard City, `NPC214.scr`, key 111), Knut's speech (Thronheim City, `KnutSpeech.scr`, key 114),
  and Hrolf and Alfrigg's quarrel (Drangheim City, `NPC110.scr`: only key 5010 and Hrolf's move are carried).
  The map session took them (2026-11-06) into its cutscene work C11 (`MM9_CUTSCENES.md`), with the import of the 228
  cinema WAVs to `worlds/mm9/audio/voices/cinema`, for the final rebuild.
- Animals (the plan's "Animals"): the cat's and dog's hang-out with townsfolk, the dog chasing cats, the pig's and
  hen's special clips at their pauses are open.
- MM9's projectile bursts at the end of its lifetime and blast push-back are not reproduced (the plan's "Dragon King
  against fliers").
- `actors.yml` and `modifiers.yml` in `assets_dev` are hard-linked with the two review roots (one file each since
  2026-11-06; on 2026-11-05 `actors.yml` was briefly a separate copy). Check with `stat -c '%i %h'` before an edit,
  edit in place (no `sed -i`, which makes a new file), and never copy one link onto another (`cat a > b` on the same
  file empties it). `tools/install_model.py` replaces a model file and breaks its review-root links: relink it.

## Evidence and outputs

- Screenshots, traces, contact sheets: `output/mm9_rework/ai_phase3/`, `ai_phase4/`, `ai_phase5/`, `anim_audit/`,
  `anim_followups/`, `perception_fix/`, `reposition/`.
- Arena and scenario files: `tests/scenarios/mm9/ai/`.
- Tests: `tests/Mm9ActorRulesTests.cpp`, `tests/Mm9MonsterAiTests.cpp`, `tests/AiArenaTests.cpp`,
  `tests/ModelAnimationTests.cpp`, the generator tests in `tools/mm9_import_discovery/`.
