# Decider brief, 2026-11-26 (b): Darzog's Tower follow-ups and the pin round's leftovers (D-191 to D-199)

The user asked for these to go through deciders: an open-ended question goes to a panel of three that propose
independently and then converge; a narrow question goes to one decider.

## Rules for every decider

- Read [AGENT_GUIDE.md](../AGENT_GUIDE.md) §6 (lanes, who owns what) and the "Design questions" bullets, and
  [DECISIONS.md](../DECISIONS.md) (precedents; the last rows: D-180 to D-190, U-16 to U-18).
- **Read-only.** Edit nothing except the output file your prompt names. No builds, installs, bakes or `git` writes.
  You may run read-only checks and tools; any heavy job goes through `tools/heavy.sh <cap>` (a game run or scenario 6,
  an oymap build 8, a Python tool 4). Pictures: read them at full size.
- Answer each question in this shape:
  - **DECISION:** what is done, concrete enough for the lane to act without asking back (files, values, words).
  - **WHY:** the reasons, the precedents, the options you rejected and why.
  - **WHO ACTS:** the lane (A1 engine and builds, A2 world tables, A3 quests and text, A5/A6 outdoor maps, A7/A8
    dungeons, or "orchestrator") and roughly how big the job is.
  - **REVERSIBLE:** yes/no, and your confidence in per cent.
  - **SUMMARY ROW:** `| D-n | 2026-11-26 | <question> (decider) | <decision> | <who acts> |`
- Player-visible text: whole sentences, English, through `tr()` in C++ or whole sentences to `evt` in Lua
  ([LOCALIZATION.md](../../LOCALIZATION.md)); Xeen's voice per [STORY_AND_ATMOSPHERE.md](STORY_AND_ATMOSPHERE.md).
- Engine work must stay shared and generic (AGENTS.md "Architecture"); no hack fixes that mask broken data.

## Context: Darzog's Tower and U-18 (D-191, D-193, D-194)

XD-12, Darzog's Tower, is a required main-quest map (M21, [QUESTS.md](../QUESTS.md)) where magic fails. U-18 (the
user, 2026-11-26, after a Discord player said "Solo Magic user will have a hard time"): the scene's
`runtime_restrictions` now hold `allow_spellcasting: false`, `allow_monster_spellcasting: false`,
`allow_spellcasting_solo: true`, `solo_spell_damage_percent: 50`. A party run: nobody casts, the monsters included. A
solo run (`Party::soloRun()`, [solo README](../../solo_action/README.md) "No-magic maps"): everyone casts, every spell
at half damage. Code: `game/maps/MapRuntimeRestrictions.h`; monster spell choice blocked in
`GameplayActorAiSystem::updateActors`; party damage scaled in `PartySpellSystem.cpp` `casterSpellDamage` and
`GameplayProjectileService::partyWorldSpellDamage`; monster spell damage in `resolveProjectilePartyImpactDamage`.
Not covered so far: Armageddon's damage to the caster's own party, spells cast by map events and traps (full damage),
the spellbook's damage preview (shows full damage; it has no access to the map), a debug console command that forces a
monster's spell. Map notes: `devdocs/xeen/briefs/xd12/L4/NOTES.md` ("No magic", "The ward by run").

## Context: the pin round's leftovers (D-192, D-195 to D-199)

[PLAYER_FEEDBACK_20261126.md](PLAYER_FEEDBACK_20261126.md): the families table (F70–F77), the "Round summary" (its
"Open after the round" list) and every agent's Results section. The decider file of the same round:
[D185_D188_DECISION.md](D185_D188_DECISION.md) and [D180_D184_DECISION.md](D180_D184_DECISION.md).

## The questions

- **D-191 (panel of three): the arrival message for a solo run.** M21's arrival hook
  (`assets_dev/worlds/xeen/source/quests/m21.yml`, `arrival:`, its window text; built by `tools/xeen/quests.py` into
  `xeen_quests.lua`, called from `assets_dev/worlds/xeen/events/maps/xeen_xd12.lua`'s `evt:arrive`) ends "Every spell you
  reach for dies before it is shaped. Here you fight with steel." That is false for a solo run since U-18. Map Lua has
  no way to tell a solo run (no `IsSoloRun`-style query in `assets_dev/engine/scripts/common/` or the Lua bindings).
  What should a solo player read, and by what mechanism (a new Lua query, one text true for both runs, an engine-side
  line, something else)? Mind D-90 (when a hook keeps a window), QUESTS_FORMAT.md, localization, MM6–MM9 unaffected.
- **D-192 (panel of three): X6 p14, worms stuck at the Sphinx cove.** The R5 section of PLAYER_FEEDBACK_20261126.md
  ("R5, outdoor pursuit at X6's cove" and its REQUESTS): engine2 fixed the planner over void cells; a worm can still hold
  at the seam of `hull_092`/`hull_093` (cell 32, 84), where `hull_093`'s west end cap rises 16–32 over the land with no
  top behind it (an invisible fin). Two requests stand: A5 sinks the caps or levels the run's tops (data), A1 lets a
  walker step over a tread-less fin lower than its step height (engine, `OutdoorMovementController`). Repro
  `output/xeen_fb/p5_engine2/r5/x6_cove_worms_pursue.yml` (and `x6_worm_probe3.yml`). Decide the fix: data, engine,
  both, in which order, and the test that closes the pin (where the repro scenario goes). Weigh MM6–MM8 outdoor
  movement risk and the hull pieces of every Xeen map (the rim kit `tools/xeen/common/rim.py` and the incident in the
  round: kerbed hull pieces sunk so the party could step into the void).
- **D-193 (single): spells from traps and map events in a solo run on a warded map.** Should they be halved like the
  rest (U-18 said "same with monsters casting spells there")? Which, if any: map-event spells (`evt.CastSpell`-style),
  trap spells (e.g. Fire Spike traps already go through `partyWorldSpellDamage`), Armageddon's self-damage.
- **D-194 (single): the spellbook's damage preview on a warded map in a solo run.** Show the halved numbers, a note,
  or leave it? If changed, how the preview gets the map's percent without new indoor/outdoor divergence.
- **D-195 (single): XD-05's three campfires.** In its L4, not installed. Its stage fails `check_drops` (pocket at
  -2398, 5374, -480) and its playtests land on X1 below `z_min` 1300; both faults are on the installed map too (Round
  summary). Install now with the faults recorded, fix the faults first (whose job, how), or drop the campfires? And
  `common/campfires.py --check` joining `regressions.sh`.
- **D-196 (single): Darkside's 192-wide tower doors tile MM7 door pictures** (a narrow second leaf shows). See the
  outdoor3 section ("D-180/D-190 (all 8 Darkside sites ...)", `common/classic_kit.yml keep_doors` += `hkm1d`,
  `hkm3dr`, audit `doors.tiled`). What picture and fit should those doors use?
- **D-197 (single): X7's `xd05_gate` picture 416 deep.** Does D-189's "leaf ≤ 128 behind the frame" apply to doors
  built before D-189? If yes, what changes for this gate.
- **D-198 (single): D-186's pair placed differently from the decision.** dungeon2 put group 25 in FD-04's nest N and
  SE of the egg bowl, not in the nest's "free south-west quarter" (which already held three of six dragons); its D-186
  section gives the reasons and captures. Accept or move?
- **D-199 (single): X7's Dragon Tower plinth**, 215 over its slope, kept by the X-maps agent (`houses.plinth`,
  `tools/xeen/town_fit_kept.yml`, D1 p3's rule in the families' Results). Accept the kept line or change the building?
