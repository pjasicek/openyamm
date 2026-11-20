# Actor regression suite: diagnosis of 13 failures (2026-10-30)

The fixes are in [Resolved](#resolved-2026-10-30). Everything before that section is the diagnosis as written: it changed
no code, test or data. Line numbers are the working tree at about 13:15; the test file
is `game/outdoor/HeadlessOutdoorDiagnostics.cpp` (shortened to `HOD.cpp`) and is being edited by another session.

## Summary

- **All 13 fail the same way on a clean HEAD (`8226a3ece`), code and data.** None comes from the uncommitted work.
- **The "valid standing sprite" errors explain one case only, the demon case, and that case produces them itself.**
  They are not caused by archived MM6 sprites, and no gameplay case depends on them. The other 12 cases log no load
  errors.
- **Nothing here is a new regression to MM6–MM8 gameplay.** One real gameplay data bug is already shipped (case 9,
  since 2026-05-22), and two small visual losses are already shipped (far LODs since 10-22, ooze since 10-17).
- Eight of the 13 are stale tests or fixtures (2, 3, 4, 5, 10, 11, 12, 13). Case 9 is the real gameplay bug. Cases 1,
  6 and 8 are a real but cosmetic data regression. Case 7 is a stale helper plus an art decision.

## The 13 cases

| # | Case | Class | Root cause | Evidence |
| --- | --- | --- | --- | --- |
| 1 | `mm8_crystal_walker_…` | Real bug, cosmetic (at HEAD) | Far-LOD repair cut the top of LOD3; the test measures LOD3 | LOD0 190.71, LOD3 183.64 against 191 ± 3; `HOD.cpp:8740` |
| 2 | `mm8_lizardman_peasant_…` | Stale test | Helper counts LOD material copies: 9, not 3 | `HOD.cpp:103`, `:11485`; passes with the helper fixed |
| 3 | `mm6_demon_…variants…` | Stale test | Test re-configures one `fx` after a deliberate failure; frames stay null | `HOD.cpp:14403`; `WorldFxSystem.cpp:568`, `:584`; passes with a fresh `fx` |
| 4 | `mm6_pmn2_…` | Stale test | As 2: 12 materials, not 4 | `HOD.cpp:15450`; passes with the helper fixed |
| 5 | `mm6_gua_…` | Stale test | As 2: 9 materials, not 3 | `HOD.cpp:15550`; passes with the helper fixed |
| 6 | `mm6_gargoyle_…` | Real bug, cosmetic (at HEAD) | As 1 | LOD0 275.28, LOD3 258.25 (needs ≥ 260); `HOD.cpp:16198` |
| 7 | `mm6_ooz_…` | Stale test + art decision | As 2, and the 10-16 material pass replaced the tuned ooze specular | GLB specular 1.0, test 0.7; `HOD.cpp:16816`; still fails with the helper fixed |
| 8 | `mm6_dwarf_…` | Real bug, cosmetic (at HEAD) | As 1: helmet spike gone at LOD2 and LOD3 | LOD0 144.28, LOD2 137.06, LOD3 136.27 (needs ≥ 137); `HOD.cpp:18514` |
| 9 | `dwi_peasant_actor_5_…` | **Real bug, gameplay (at HEAD)** | Exporter stores a pointer byte as `hostility_type` | Scene value 59, raw `3b 95 2d 0b`; `export_outdoor_scene_yml.py:76` |
| 10 | `friendly_actor_3_preview_…` | Stale test | MM8 monster sprites archived 2026-10-19 | `samples=64 missing=64 textures=0`; `HOD.cpp:28125` |
| 11 | `hostile_actor_uses_long_…` | Stale fixture | Actor 53 now has its real `ally=1`; the fixture keeps it | `hostileToParty=0 ally=1`; `HOD.cpp:28798`; passes with `ally=0` |
| 12 | `mixed_actor_53_arrow_…` | Stale fixture | Party is placed 10 units underground; the arrow hits the slope | Ground 746, party 736; `HOD.cpp:30529`; passes with the party 16 higher |
| 13 | `out05_event_clearance_…` | Stale test | Targeted spell from (0,0,0) is past the range added on 10-26 | `index=1 mode=spell dist=13468`; `OutdoorWorldRuntime.cpp:18391`; passes when cast from the actor |

## Root causes by group

### A. Far-LOD repair, `8508f0269` (2026-10-22): cases 1, 2, 4, 5, 6, 7, 8

The repair rebuilt LOD2 and LOD3 of 156 creatures, see
[its README](../level_generation/creatures/lod_repair_claude/README.md). Two separate consequences:

**A1, material count (2, 4, 5, and part of 7).** Each tier gained `<name>_LOD2` and `<name>_LOD3` materials.
`recolouredTierMaterials` (`HOD.cpp:103`) dedupes by exact name, so it now returns three times as many: `mm6_gua` went
from 3 to 9 between `45480354c` and `8508f0269`. Base tier materials and ramps are intact: each LOD copy has the same
ramp hash as its tier, and base tiers share one image and mask.

**A2, height (1, 6, 8).** The cases read `actorModelBounds`, which is `pickingBounds`, which poses the coarsest LOD
(`ModelInstance.cpp` `pickingBounds`, `ModelAnimation.cpp:437`). LOD0 is unchanged and the repair's outline gate
allowed the loss. My offline measurement of the GLBs reproduces the failing runtime values exactly (136.27, 258.25).
Before the repair the same LODs were 142.54 (dwarf) and 190.71 (Walker). The dwarf is a regression of something
deliberate: the [ledger](../level_generation/creatures/REDUCTION_LEDGER.md) says its helmet spike was protected in
the LODs. The same coarsest-LOD height feeds picking boxes, aim points and `standingHeight`
(`WorldFxSystem.cpp:1151`), so these targets are slightly short up close too.

A rough audit of 184 installed models finds 14 whose LOD3 is at least 5 % shorter than LOD0 (worst about 12 %). It
excludes two false hits from separate parts (`mm8_m536`, `mm6_qfi`). Only the three models above were checked by hand.

### B. Test re-configures a used `fx`: case 3, and the source of the load errors

The case first calls `configureActorModels` with null frames to prove that this fails. Since `c66af06d9` (2026-10-15)
`m_actorModelsConfigured` is set before the eager build (`WorldFxSystem.cpp:568`). The second call, with real frames,
therefore returns at `:584` without storing them. Lazy builds then run with null frames, and every `scale_reference`
resident of New Sorpigal logs `actor model scale requires a valid standing sprite` (10 lines, this case only).

The sprite frame data for MM6 still exists in `engine/rendering/sprite_frames/monsters/`; only the images were
archived. The game path is safe: it stores the frames before that guard and uses the view's frame table
(`GameApplication.cpp` `syncActorModels`). With a separate `fx` for the negative check the case passes with 0 errors.

### C. Ooze material pass: case 7

Fixing A1 is not enough. The 2026-10-16 material pass (`assets_source` `2f206e9`) turned the ooze's tuned
`openyamm_specular` 0.7 with a per-texel crease mask (mean 0.71, max 1.0) and roughness 0.5 into specular 1.0 with a
flat mask of 0.30 and roughness 0.7. Its [README](../level_generation/creatures/mm6_ooz_claude/README.md) records 0.7
and the crease mask as user-reviewed choices; the pass was meant to keep deliberate sheen, but
[its summary](../level_generation/creatures/claude_shared/material_pass/batch/SUMMARY.md) lists no exception for the
ooze. In-game look not compared.

### D. Map re-export, `f766776a0` (2026-05-22): cases 9, 11

This commit corrected `ACTOR_ALLY_OFFSET` and re-exported the scenes from MMerge's DDMs, whose saved actors contain
live pointers.

- **Case 9, real bug.** `hostility_type` is read at `0x2C` (`export_outdoor_scene_yml.py:76`,
  `export_indoor_scene_yml.py:93`, `MapDeltaData.cpp:29`). That is the low byte of the `monsterInfo.name` pointer; the
  real field is `0x3D`. At least 789 of 1,710 scene actors hold a value above 4: MM6 60 of 377, MM7 414 of 826, MM8
  315 of 507. The engine treats 0 as friendly (`OutdoorWorldRuntime.cpp:2953`, `:4246`;
  `GameplayActorAiSystem.cpp:1398`, `:1990`), so these friendly actors skip the friendly-actor rules against other
  actors. This is from reading the code, not observed in game.
- **Reading `0x3D` alone will not fix it.** It holds the table's Hst value, 4 for this peasant, not 0. Friendly actors
  need 0 in the scene unless authored otherwise. The rest of the case (no fleeing) was not reached, so it is unverified.
- **Case 11, stale fixture.** The raw `ally` of actor 53 really is 1, which maps it to the lizardmen. The fixture swaps
  in monster 184 (relation 1) but keeps the ally, so `relationMonsterId` resolves to monster 1 (relation 0).

### E. Individual stale tests: cases 10, 12, 13

- **Case 10.** The MM8 sprites moved to `assets_legacy/sprites_mm8_monsters_20261019/`. The test still asserts billboard
  pixels for a monster that now draws a model.
- **Case 12.** Its message is wrong: the blocker plays no part. The trace is identical with the blocker 30,000 units
  away, and it takes no damage. Ground at the party's spot is 746 and the party is set to 736, so the arrow aimed at
  its feet hits the slope about 40 units short. A real party stands on the ground. The sibling
  `mixed_actor_53_arrow_hits_party_without_impact_effect` searches for a valid position and passes. I did not establish
  when this started.
- **Case 13.** `7ad4418fb` (2026-10-26) deliberately made targeted spells refuse monsters past 8192 units. The test
  passes the party as (0,0,0), and the second target is 13,468 away. The whole case passes when cast from the actor.

## Recommended fixes

| Group | Fix | Owner | Priority |
| --- | --- | --- | --- |
| D, case 9 | Stop exporting the pointer byte, write 0 for non-authored actors, regenerate MM6–MM8 scenes, then check actor-vs-actor behaviour on Dagger Wound. Also check `MapDeltaData.cpp:29` | Map/export owner | **High: real, but changes behaviour on many maps** |
| A2 | Decide per model: rerun the far LODs with the silhouette top protected (dwarf first), or accept the loss and relax the three cases | User decision, creature pipeline | Medium |
| C | Decide whether to restore the ooze's 0.7 and crease mask (`material_pass/revert.sh` exists), then align the test | User decision, creature pipeline | Low |
| A1 | Skip `_LOD<n>` names in `recolouredTierMaterials`; verified on cases 2, 4, 5 | Test owner | Low, one line |
| B | Use a separate `WorldFxSystem` for the negative check; verified | Test owner | Low |
| D, case 11 | Clear `ally` in the fixture; verified | Test owner | Low |
| E | Case 10: remove it or test a model instead. Case 12: put the party on the ground and aim as the game does; verified with +16. Case 13: cast from near the target; verified | Test owner | Low |

Test fixes should wait for, or be coordinated with, the session editing `HOD.cpp`.

## Shipping impact

- **Blocks nothing new.** All 13 are at HEAD, and every test-only item has no player effect.
- **Case 9 matters most.** It is live in shipped MM6–MM8 data, but has been since May, so it is a known-age bug and not
  a release regression. Fixing it changes monster behaviour, so it needs its own testing.
- **Far LODs and the ooze are visible only as polish:** distant silhouettes, slightly short pick boxes, a duller ooze.

## Method and limits

- Each case was reproduced alone with `OPENYAMM_REGRESSION_FILTER` on a working-tree snapshot (12:42): all 13 fail
  with `--world` mm6, mm7 and mm8, with identical messages in mm8, and with the same messages on HEAD.
- Full coverage on HEAD, one process per case under `--world mm8`: 174 pass and the failures are exactly these 13. This
  isolates cases from each other, so it cannot show order effects. The working tree has no complete run: a serial one
  timed out under load after 70 cases, with no failures beyond those explained here.
- HEAD baseline: a private `git archive` build with HEAD's assets, without MM9. It kept 330 unreferenced untracked MM6–MM8
  files (328 textures, 2 GLBs). "Passes with" results come from a private patched copy of it, not the repo.
- Moving target: at 12:50 another session reverted `mm6/models/actors.yml` to HEAD and rewrote `mm6_pfem.glb` and
  `mm6_pman_v2.glb`; at 13:04 the peasant test expectations were reverted too. `mm6_pfem`/`mm6_pman` failed only on my
  12:42 snapshot, for that reason. `git diff` of `game/tables/SpriteTables.*` touches decoration rows only.

## Separate hazard: headless runs rewrite `settings.ini`

A headless case that boots `GameApplication` saves settings with the active world (`GameApplication.cpp:7590`). So
`--world X` from the repository root overwrites the user's `start_world`, and later runs without `--world` use it. My
own matrix did this briefly and ended on `mm8`, the original value. Other sessions' `--world` runs still do:
`settings.ini` read `start_world=mm9` when this report was finished, and I left it alone. It should be set back to
`mm8` once those runs stop. Use `--user-data <private folder>` for these runs.

## Resolved (2026-10-30)

The user's decisions were applied the same day. Totals are in [Verification](#verification-2026-10-30).

### Case 9: `hostility_type` (data fix, behaviour change)

**What the field is.** In the original game `monsterInfo.hostilityType` (`0x3D`) is runtime state: a copy of the monster
table's Hst, dropped to 0 as soon as the actor has no target (`Actor.cpp:2566` in OpenEnroth), and raised when it fights.
The MMerge DDMs and DLVs only hold a snapshot of it: it matches the table, or the older table the map was saved with, or
0 for an actor that had already calmed down (`d07` Shapeshifters, table 2). No source authors it. The engine reads only
0 against non-zero, and outdoors gives actors hostile to the party their Hst when the value is 0
(`OutdoorWorldRuntime.cpp:2955`). Every one of the 1,710 scene values equalled the raw byte at `0x2C`, so nothing had
been authored in scenes since May.

**Fix.** The exporters write 0 for every actor and `MapDeltaData.cpp` no longer reads the field. The 811 non-zero values
were set to 0 in 32 scene files, written through a temporary file and a rename. `git diff` shows 811 changed lines, all
`hostility_type`, and a re-export of `out01` is byte-identical to the migrated scene.

| World | Actors | Hostile to party, before and after | Friendly to party, before and after | Scene value 0, before → after |
| --- | ---: | ---: | ---: | ---: |
| MM6 | 377 | 63 | 314 | 315 → 377 |
| MM7 | 826 | 173 | 653 | 412 → 826 |
| MM8 | 507 | 91 | 416 | 172 → 507 |

- **No actor changes between friendly and hostile to the party.** That flag does not read this field outside MM9
  civilians. Counted with the engine's rule against `hostile.txt`, not from a running game.
- **617 friendly actors** now start with the friendly-actor rules (MM6 50, MM7 316, MM8 251).
- **180 outdoor hostile actors** are unchanged: they get their Hst at load.
- **14 indoor hostile actors** go from non-zero to 0, like the 93 indoor hostile actors already at 0. It affects them
  against other actors only, and none has an enemy among the scene's placed actors: `6d08` Rogue, Genie; `6d12` Warlock;
  `6d19` Power Lich; `6t6` Priest of Baa; `6t7` two Priests of Baa; `cd2` Power Lich; `cd3` Minotaur King; `zdwj02` Devil
  Warrior; `znwc` Goblin King, Goblin Shaman; `d12` two Ogre Warleaders. Spawn points were not checked.

**Behaviour.** Case 9 passes end to end, including the no-fleeing part. `dwi_friendly_actors_stay_calm_until_enemies_come_close`
is new: on Dagger Wound no friendly placed actor leaves its calm state in 30 s, a peasant ignores an enemy at 3,500 units
and turns hostile at 400. In the same 30 s with the old byte, one friendly actor fled and one pursued.

**MM9** is not affected by the exporters: its scenes come from `transcode_mm9_dat_to_odm.py`. One value is the same bug:
`thjorgard_authored.scene.yml` has Kira Stonepath at 83, a copy of `out01` actor 0. Left for the user.

**Still open, not changed:**

- Friendly actors from spawn points still take the table's Hst (`OutdoorWorldRuntime.cpp:3929`,
  `IndoorWorldRuntime.cpp:18579`, `:20912`): 31 on Dagger Wound. They skip the friendly-actor rules, as the placed ones did.
- Saves keep the old byte for maps already visited. There is no save migration.
- `util/map_export.py` and `util/ddm_export.py` still dump `0x2C` under this name.

### Cases 1, 6, 8: far-LOD height accepted

The bounds pose the coarsest LOD, so each case now allows that LOD's height and says why: Crystal Walker 182 to 194,
gargoyle from 255, dwarf 94 % of native on all tiers. No LOD was rebuilt.

### Stale tests

| Case | Change |
| --- | --- |
| 2, 4, 5 | `recolouredTierMaterials` skips `<name>_LOD<n>` |
| 3 | The negative check uses its own `WorldFxSystem` |
| 10 | Renamed `friendly_actor_3_draws_an_animated_model`: tests a posed model and a sampled clip, not billboard pixels |
| 11 | Clears `ally` in the fixture |
| 12 | Party stands on the terrain |
| 13 | Spell cast from beside the target |

### Case 7: ooze gloss

Specular 0.7, the crease mask and roughness 0.5 are back, on the ooze only. `material_pass/revert.sh` was not used: its
backup predates the far-LOD repair and would have undone it. `mm6_ooz_claude/scripts/restore_gloss.py` keeps the installed
GLB and changes the factors and three maps; the far LODs' maps are re-derived with the repair's own transfer, which
reproduced the installed maps exactly. Winding check 0, installed with `tools/install_model.py`. Compared in viewer shots
(`mm6_ooz_claude/review/shots/cmp/compare.png`): sharper highlights and darker creases, and the ochre tier stays ochre. The
viewer shows the engine's specular through `KHR_materials_specular`; the look was not checked in game. The test now also
requires the specular mask.

### Settings hazard

`ApplicationConfig::saveSettings` is false for headless commands, and every settings save goes through
`GameApplication::saveSettings`. `headless_application_boot_leaves_settings_file_alone` covers it. A desktop run still
rewrites its `settings.ini`. `start_world` in the repository's `settings.ini` was set back to `mm8` last.

### Extra: the `dialogue` suite and scenarios

The `dialogue` suite is every outdoor case, so these 16 are not dialogue-specific. All 16 were old tests, mostly
written before the MMerge table merge.

| Case | Class | Evidence | Result |
| --- | --- | --- | --- |
| `app_startup_boots_seeded_out01_session` | Stale fixture | Default is now the main menu, seed is one member | Fixed |
| `app_adventurers_inn_house_opens_character_overlay` | Stale fixture | As above, and house 185 is now a guild; inn is 756 | Fixed |
| `app_tavern_rent_room_closes_dialog_runs_rest_ui_and_wakes_at_6am` | Stale fixture | House 107 is a shop; tavern is 229; residents are listed first | Fixed |
| `app_regular_house_entry_auto_opens_single_resident_dialog` | Stale fixture | Talimere's house is 866, not 237 | Fixed |
| `app_single_teacher_house_entry_unlocks_teacher_autonote` | Stale fixture | Helga Steeleye is NPC 185 in house 593; autonote 177 | Fixed |
| `app_quicksave_quickload_preserves_empty_house_after_departure` | Stale fixture | Resident is NPC 28; departed NPCs are party state | Fixed |
| `app_boundary_map_transition_confirm_preserves_world_direction_on_all_edges` | Stale test | Map names are lower case now | Fixed |
| `app_map_transition_confirm_applies_oe_travel_side_effects` | Stale test | As above | Fixed |
| `map_transition_dialog_uses_transition_presentation_and_oe_copy` | Stale test | Hard-coded 1 day; `outdoor_travels.txt` says 5 | Fixed |
| `mm6_oute3_west_boundary_travel_mirrors_arrival_and_keeps_heading` | Stale fixture | Spot is on a slope that keeps the party airborne; passes on level ground | Fixed |
| `local_event_457_cannonball_uses_gravity_but_fireball_does_not` | Stale test | Projectiles step at 1/60 s, the test ran one 1/128 s step | Fixed |
| `save_game_roundtrip_restores_party_world_and_movement_state` | Stale test | Saves omit splat vertices since `4ab07ed51`; restoring needs a splat on the ground | Fixed |
| `outdoor_scene_yml_matches_legacy_ddm_authored_state` | Stale test | Scenes come from the MMerge maps since May; the legacy companion differs | Renamed, checks scene preference |
| `indoor_scene_yml_matches_legacy_dlv_authored_state` | Stale test | As above | Renamed, checks scene preference |
| `lua_event_runtime_executes_scripted_map_handlers_without_errors` | Stale test, then real MM9 bugs | Ran MM7 and MM6 global events on an MM8 map, and hooks without context; both fixed | **Still fails** |
| `app_npc_granted_item_enters_held_cursor_slot` | **Probable real bug** | Stale NPC fixed. Subtracting gold queues the stat-down portrait effect (`EventRuntime.cpp`, gold branch of `subtractVariableValue`); OpenEnroth shows none | **Still fails** |

**For the coordinator's decision, not fixed:**

- Gold subtraction in events, above: cosmetic, and shared by all worlds.
- `drangheim.lua` events 50024 and 50114 call `routine_followplayer`, which nothing defines.
- `thronheimcity.lua` events 30953 and 30954 call `evt.UseMm9Barrel`, which nothing defines.
- `DefaultAdventurersInnHouseId = 185` in `GameplayDialogController.cpp` is now a guild. It is used only without a house
  table.
- On the slope at (-23106, 1000) of New Sorpigal the party stays airborne while walking into the edge, so travel is not
  offered there. Seen in one test position only.

**Scenarios (22 mentioning dialogue).** 11 pass, 11 fail. `smoke_faithful_potbello` was a stale fixture and now passes. The
other 11 are recorded May drafts, all stale fixtures:

| Scenario | Stops at | Past that |
| --- | --- | --- |
| `main_story_draft` | Loader: keys the runner never had (`until`, `levels`, `skill`) | Not run |
| `probe`, `probe_2`, `probe_3`, `probe_4`, `mm6_main_story_full_recorded_playthrough` | Recorded empty house name | With the name removed: a cancel step that was never recorded, later titles and destinations |
| `probe_4.2`, `probe_4.3_supremebaa`, `probe_4.5_darkmoor`, `probe_4.6_varn`, `probe_4_hive` | `load_game` of the user's `saves/saveN.oysav` | With a private copy: those saves now hold other maps |

They need re-recording or retiring, which is the user's call. Under `--user-data` their `saves/` path misses the
repository's folder, which only moves where they stop.

### Verification (2026-10-30)

One process per case under `--world mm8`, `--user-data` private, from the same build (comment and line-wrap edits came
after it; the 13 cases and the rewrapped cases were rerun on the rebuilt binary and pass).

| Check | Result |
| --- | --- |
| The 13 cases, by `OPENYAMM_REGRESSION_FILTER` | 13 pass |
| Actor regression, 198 case names | 189 pass, 0 fail in `actors`. The other 9 run only in the `indoor` or `outdoor` suite: 8 pass, 1 fails (below) |
| Every case in `dialogue`, 311 names | 275 pass, 2 fail (`app_npc_granted_item_enters_held_cursor_slot`, `lua_event_runtime_executes_scripted_map_handlers_without_errors`), 34 not in this suite |
| The 34 run in `indoor` or `outdoor` | 29 pass, 5 fail (below) |
| `mm9_actor_models_build_every_binding`, `--world mm9` | Pass: 69 descriptors on 33 models, 0 failed |
| `openyamm_unit_tests` | 2,384 pass, 0 fail |
| 22 dialogue scenarios | 11 pass, 11 fail (above) |
| Desktop run through `tools/run_game.sh --isolated` | `settings.ini` rewritten, so normal runs still save |

**Five `indoor` suite failures, outside the 13 and the 29. Compared with HEAD and fixed later the same day, see
[The five `indoor` failures](#the-five-indoor-failures-2026-10-30):**

- `party_spell_system_supports_indoor_shared_runtime_direct_actor_damage`: "Blades failed through indoor shared runtime".
  The test picks the first healthy actor of `d18.blv`, so the targeted-spell range of case 13 is the likely cause. Not
  confirmed.
- `indoor_movement_controller_snaps_to_floor_and_blocks_walls`: actor contacts not reported.
- `indoor_support_sampling_prefers_raised_open_door_surface_at_d18_seam`, `indoor_support_sampling_prefers_highest_floor_under_body_footprint`,
  `indoor_d18_naga_lintel_slide_preserves_tangential_progress`: movement geometry, in the area of the uncommitted
  `IndoorMovementController.cpp` work.

None of the five reads `hostility_type` as far as the code shows.

**Limits.** One process per case cannot show order effects: no complete single-process run was done.
`hostile_actor_uses_long_party_acquisition_despite_short_relation` and `long_hostile_actor_pair_engages_at_2048` both kept
actor 53's `ally`. The second passed only because of the old pointer byte: it is the one test the data fix broke, and
clearing `ally` in its fixture restored it. The ooze was checked in the viewer, not in game.

### The five `indoor` failures (2026-10-30)

**Result:** none of the five came from the uncommitted work, and all five were stale tests. The verification walk found a
different problem: two uncommitted movement hunks had changed MM6–MM8 movement. That is fixed, see
[below](#mm6mm8-movement-change-in-the-uncommitted-work).

Method: private `git archive` builds in `output/` without touching the working tree. "06-10" is `2c18879f0`, the last
indoor movement commit of June, built with its own assets. A probe linked only into the private builds stepped each case.

| Case | `8226a3ece`, `16e916f95` (true HEAD) | 06-10 | Cause | Fix (test only) |
| --- | --- | --- | --- | --- |
| `party_spell_system_supports_indoor_shared_runtime_direct_actor_damage` | Fails, same message | Fails | **Not the targeted-spell range**: `castSpell` has no range check. Blades is a projectile, and the short `IndoorWorldRuntime::initialize` overload leaves the spell table and projectile service null, so `castPartySpellProjectile` returns false | Casts Implosion, a direct-damage spell, which is what the case tests |
| `indoor_movement_controller_snaps_to_floor_and_blocks_walls` | Fails, same message | Fails | With `blockActorSlide`, `resolveMove` stops at the first sub-step blocked by an actor. Actor 22 is 8.5 units past actor 11, so only actor 11 is reported. Without that `break` the old test passes | Actors stand either side of the path and are met at the same distance |
| `indoor_support_sampling_prefers_raised_open_door_surface_at_d18_seam` | Fails, same numbers | Fails, same numbers | The test expects the body to stay on face 13 (z -144). The step-up on a floor's boundary (`369ae0a0c`, April) and the footprint probe both lift it to doorway floor 1364 (z -128) first. With both disabled the old test passes | Runs until the centre is over the raised floor and requires 1364 at z -128 |
| `indoor_support_sampling_prefers_highest_floor_under_body_footprint` | Fails, same message | **Passes** | The sweep change of `856f27d96` (10-04): spheres now hit face edges when moving along or away from a plane. At 0.1 s per step, gravity sinks the body into the open door's 36-wide floor slot and the lip stops it at y 979.6. HEAD with only the old `IndoorCollisionPrimitives.cpp` passes | Uses the party's 1/128 s step. On HEAD, at that step, all 72 crossings pass (speeds 60–768, six x positions, both directions), feet between -144 and -128 |
| `indoor_d18_naga_lintel_slide_preserves_tangential_progress` | Fails, same numbers | **Passes** | Same sweep change. The 270-wide body is wider than the 256-wide doorway. It slides around the right jamb edge and stops centred, held by both edges, which is correct. +10 in x was only reachable by ignoring the jamb edge | Requires 10 units of progress along the jamb and that neither jamb edge is penetrated |

The sweep change has its own unit tests in `IndoorCollisionPrimitivesTests.cpp` and is intended. Both 06-10 passes
depended on what it fixed.

### MM6–MM8 movement change in the uncommitted work

Compared with deterministic party walks, HEAD code against working-tree code, both on HEAD's assets: from the centre of
every floor face, 8 directions, 2 speeds (300, 768), 384 steps at 1/128 s, hashing position and support face every step.

| Map | Walks | Traces changed by the uncommitted work | After the fix |
| --- | ---: | ---: | ---: |
| `d06` | 11,440 | 6,110, up to 1,668 units apart at the end | 0 |
| `7d06` | 8,688 | 3,993, up to 1,836 units | 0 |
| `d18` | 4,960 | 2,682, up to 897 units | 0 |
| `6d08` | 4,592 | 630, up to 1,583 units | 0 |
| `7d26`, `d17`, `7d12`, `zdwj02` | 58,768 | Not measured | 0 |

- **Source:** only the two hunks of the Plane of Earth fix (`eleme.blv`, party dropping through cave slopes). With both
  restored, `d06`, `7d06` and `6d08` matched HEAD exactly, so the movers, ladders, `immobile` and floor-portal work change
  nothing on these maps.
- **Early step:** making it ignore every lower floor ahead caused almost all the changes, and could hold the party
  in place: on `d18` it stuck at a sloped lip's edge (z 840).
- **Embedded-floor check:** it also blocked moves in ordinary rooms (13 to 29 walks per map).

**Fix, in `resolveMoveSingleStep`:** the early step is HEAD's rule again. Both checks now act only when the floor is
another room's, more than `MaximumDrop` below, and a floor of the current sector stands above the body's step reach.
Both Plane of Earth runs stay in their rooms. New test: `the party walks off the low edge of a sloped lip`. It covers
the `d18` stuck walk; that walk ended at z 840 before the fix.

### Verification of these fixes (2026-10-30)

One frozen binary, `--user-data` private, `--world mm8`.

| Check | Result |
| --- | --- |
| The five cases, one process each | 5 pass |
| `indoor` suite, one process per case | 174 pass, 0 fail |
| `indoor` suite, one process | 174 pass, 0 fail, so no order effect in this suite |
| `tests/IndoorMoversTests.cpp` | 12 pass |
| `openyamm_unit_tests` | 2,387 pass, 0 fail |
| MM9 dungeon scenarios (`mm9r_*`) | 26 of 28 first time, 27 of 28 after a rerun, including `mm9r_beethoven/scenario_doors_exits` (doors, ladders), `mm9r_anskramkeep/scenario_rotating` and `mm9r_chasmofthedead/scenario_pivot` |
| Walks on eight MM6–MM8 maps, against HEAD code | 88,448 walks, 0 differ |
| Party runtime `movement_segment` on `d06` and `7d06`, HEAD against final | Same reported offset from a deliberately wrong target (one number per run) |

- **`mm9r_ruinedtemple/scenario_doors_exits` fails**, at step 10 (a map variable), with the same message on the binary
  from before the movement fix. Its map was being rebuilt at the time. Not investigated.
- **`mm9r_klusoshouse/scenario_scripted`** failed once in the parallel run, while its map was being rewritten (17:30),
  then passed alone on both binaries.

**Limits.** The walks are party walks on the maps' initial door states: no jumps, no actors, no flying, and eight maps
rather than all. The fix is tuned to two known Plane of Earth runs; other cave slopes in `eleme.blv` were not checked.
The two actor-free `movement_segment` runs each cover one path.
