# Levitate and floor traps

Investigated 2026-09-11 in response to the report that MMMerge Levitate avoids MM8 floor traps but fails in
MM6/MM7 maps. This is a static executable, asset, and source investigation, not a live MMMerge reproduction.
The initial investigation changed no gameplay implementation; the subsequent repair is recorded below.

## Finding

The report has a concrete explanation in the original MM8 executable and the local imported maps. Indoor
Levitate protection depends on a face flag that the MM6/MM7 trap faces examined do not have. It is not a
continent-name check, and the evidence does not establish that literally every MM8 trap is protected.

OpenYAMM also has an implementation gap: it applies a Levitate party buff but never consults that buff in
either indoor or outdoor pressure-plate dispatch. Consequently, MM8's native protection is missing here too.

## Original MM8 evidence

Target: `mm8_orig/MM8-Rel.exe`, verified SHA-256
`5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b`.
Analysis used Rizin 0.10.0 following [the Rizin guide](RIZIN_GUIDE.md), with no executable writes.
These addresses describe disk code in this executable, not GrayFace/MMMerge runtime patches.

The local MMExtension structures identify character spell buffs at offset `0x1a34`, each 16 bytes, with
Levitate at index 25. This gives offset `0x1bc4`.

- `0x43f49f` iterates the active party members through `0x402741`, checks the signed 64-bit expiration field
  at character offset `0x1bc4`, and returns true if any member has a positive expiration value.
- The spell-casting path at `0x42d76d` addresses that same buff slot.
- Indoor movement at `0x473272` tests bit `0x08` of face byte `+0x2f`, equivalent to flag `0x08000000`
  in the attributes at `+0x2c`. If set, it calls `0x43f49f` at `0x47327e` and skips the step event when true.
  Otherwise, `0x473298` tests `0x04000000` and obtains the face event from its face-data record.
- Another indoor collision path at `0x473cea` / `0x473cf6` performs the same conditional Levitate check.
- Outdoor movement also has flag-gated checks at `0x47436a` / `0x474376`. A later outdoor collision path
  calls the Levitate helper unconditionally at `0x47542f` before its event checks. Do not assume every
  outdoor branch has identical flag requirements based only on the indoor finding.

Useful reproduction commands, from the repository root:

```sh
sha256sum re_mm8/mm8_orig/MM8-Rel.exe
rizin -N -q -e scr.color=0 -c 'pd 35 @ 0x43f49f;pd 38 @ 0x473255;pd 24 @ 0x473cdb' re_mm8/mm8_orig/MM8-Rel.exe
rizin -N -q -e scr.color=0 -c 'aaa;axt @ 0x43f49f' re_mm8/mm8_orig/MM8-Rel.exe
```

`reference/mmmerge/Scripts/Core/ConstAndBits.lua` explicitly assigns different meanings to this bit:
`TriggerByMonster` in MM6/MM7 and `DisableEventByCtrlClick` in MM8. The MM8 name does not describe its
additional use by Levitate, which is established by the executable instructions above.

## Local map evidence

Scanned the raw `assets_dev/worlds/mm*/maps/*.blv` files using the layout detection in
`tools/export_indoor_scene_yml.py`. Counted faces with both a nonzero event id and `0x04000000` set.
These are raw BLV counts, before scene overrides, saved face attributes, or event-driven changes; they are
not counts of traps, because step events also serve other purposes.

| World | BLV maps | Faces with step events | Also have `0x08000000` |
| --- | ---: | ---: | ---: |
| MM6 | 51 | 689 | 0 |
| MM7 | 63 | 977 | 0 |
| MM8 | 47 | 539 | 106 |

Concrete checks against the readable original event references:

- MM8 `d26.blv` (Crypt of Korbu): event 101 has 18 pressure faces, all with attributes `0x8c000102`.
  `reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/D26.txt` shows event 101 casting ten Sparks spells.
  Its faces have the native Levitate-sensitive bit.
- MM7 `7d10.blv` (Breeding Zone): event 451 has attributes `0x84000102`, and event 452 has `0x84000100`.
  `reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/D10.txt` identifies Blades and Fireball traps,
  respectively. Neither face has the Levitate-sensitive bit.
- MM6 `6d03.blv`: events 21 and 22 both have attributes `0x84000100`.
  `reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/D03.txt` shows event 21 conditionally casting
  Fireball, while event 22 recruits Sharry Carnegie and updates a quest bit. This demonstrates why
  suppressing every step event would also suppress non-trap gameplay.

## OpenYAMM implementation and repair scope

- `game/party/PartySpellSystem.cpp`, Levitate case: applies Levitate, WaterWalk, and FeatherFall party buffs.
  `game/party/EventSpellBuffs.cpp` does the same for event-applied spells.
- `game/scene/IndoorSceneRuntime.cpp`, `updatePartyFaceTriggers`: determines floor transitions and dispatches
  pressure events without a Levitate check.
- `game/indoor/IndoorWorldRuntime.cpp`, `executeFaceTriggeredEvent`: likewise has no Levitate guard.
- `game/scene/OutdoorSceneRuntime.cpp`: dispatches pressure events without a Levitate check.
- `game/FaceEnums.h` names `0x08000000` only as `TriggerByMonster`, and
  `game/indoor/IndoorMapData.cpp` preserves the raw face attributes.

A complete repair should represent the native MM8 meaning correctly, supply explicit equivalent metadata
for audited MM6/MM7 physical floor traps, and consult that metadata plus Levitate in shared trigger policy
used by the world-specific dispatch paths. Do not redefine MM6/MM7 monster triggers globally, suppress all
step events, infer trap status solely from a spell-casting opcode, or edit generated event Lua directly.

Validation should cover the three trap examples above with Levitate active and inactive, an ordinary
quest/door step event while levitating, buff expiration and re-entry, and affected indoor/outdoor dispatch.
Chest traps, timed traps, and immunity to already-fired projectiles are separate mechanics and are not
established by this investigation.

## Follow-up: can MM6/MM7 trap status be derived?

Yes for a substantial, well-defined subset, using the floor binding together with the event's behavior.
There is no reliable discriminator in the examined face fields alone. Prefer conservative classification
during event export over a manually maintained list of every ordinary trap.

### What a pressure plate actually represents

The local OpenEnroth MM7 reference checks ground contact, a change of supporting face, the step-trigger bit,
and the bound event id. It does not have a separate trap-plate object or consult the event's damage behavior
when deciding whether to trigger it. Both indoor and outdoor movement use this general event mechanism.
This is reference-source evidence, not a separate binary verification of original MM6/MM7 movement.

Joining the imported indoor face bindings to their generated Lua gives 244 distinct map/event bindings in
MM6 and 134 in MM7. Fifteen and nine, respectively, have no registered body; the corresponding original
readable reference scripts also contain no matching event. Initial scene face-attribute overrides were
included in this follow-up scan. It does not simulate saved overrides or later script mutations.

The apparent alternative discriminators do not solve classification:

- `cogTriggerType` is zero on all 689 MM6 and 977 MM7 step-event faces examined.
- No MM6 step-event face has the `IsSecret` bit. In MM7, that bit covers 12 of the 14 identified spell-trap
  events, misses two, and also appears on `7d17` event 7, which opens a door and updates a map variable.
- Textures and ordinary face flags overlap. MM6 `6d03` events 21 and 22 have identical step attributes,
  despite representing a Fireball trap and an NPC/quest encounter.
- Merely having the step bit does not even establish that a face is a walkable floor. MM6 `6d01` event 64
  is attached to wall faces, also supports clicking, and casts Wizard Eye. It must not become a floor trap
  because a classifier sees `CastSpell`.

### Script-derived candidates

Restricted to events bound to floor or floor/wall polygons (native polygon types 3 and 4), the scan found:

| World | Hostile-spell floor events | Only spell effects, optional conditions/messages | Mixed with other state changes |
| --- | ---: | ---: | ---: |
| MM6 | 33 | 28 | 5 |
| MM7 | 14 | 14 | 0 |

All 47 event bodies were also checked against their original per-world readable EVT references. The simple
42 contain only `CastSpell`, optional `Cmp`, `Exit`, `GoTo`, `StatusText`, and `ForPlayer` operations. The five
mixed cases contain additional `Set` or `SetLight` operations. Counts describe the local imported indoor
corpus; they are not a claim that every possible floor hazard is a spell trap.

MM7 candidates: `7d10` 451/452, `7d12` 452, `7d14` 454, `7d20` 451, `7d31` 455,
`d01` 457/458/459, `t02` 454/455/456/457, and `t03` 451.

MM6 simple candidates: `6d08` 34/35/36/39/40/41/42, `6t7` 61 through 70,
and `cd2` 2/3/19/20/21/22/23/24/25/27/46.

The five MM6 mixed spell cases illustrate why a broad rule needs limits:

- `6d03` event 21: checks the Guild Key and a map variable; the safe branch updates the variable.
- `6d08` events 22 and 23: fire spells and record which puzzle plates have been pressed. A later floor
  event checks these puzzle variables before opening a magic gate. Suppressing only the spell would
  still count a levitating party as pressing the puzzle plates.
- `6d08` event 25: fires Sparks and resets puzzle progress.
- `sci-fi` event 47: turns off a set of lights and fires Sparks.

Direct-damage scripts need separate care. There are simple spike, lava, and damage-floor events, but other
step events describe falling debris or swamp gas, summon ambushes, or combine damage with forced movement.
The opcode `DamagePlayer` does not by itself establish a pressure-operated ground trap. Spell selection
must likewise include hostile status spells such as Stun and exclude beneficial spells.

The raw outdoor ODM scan found 12 distinct step-event bindings on 34 faces across 15 MM6 maps, and 44
bindings on 67 faces across 13 MM7 maps. All have matching generated event bodies. These mostly implement
teleports, NPC interactions, and encounters. The two spell-bearing events are mixed, not additional simple
spell-plate candidates: MM6 `outd3` 210 combines spells with dialogue, payment, movement, and summoning;
MM7 `7out02` 236 sets the hill-fort quest bit, casts Fire Bolts, and summons goblins. The latter is a concrete
example of a floor-triggered hostile-spell event that should not automatically be classified as a physical
trap plate. This outdoor scan used raw geometry attributes, without applying scene or saved overrides.

### Revised implementation recommendation

Derive metadata for the simple cases during legacy event export by examining reachable control flow and
spell effects. A conservative rule is:

1. The event has a reachable hostile spell effect.
2. Its other reachable operations are limited to reads/conditions, control flow, player selection, and
   optional trap feedback. It has no quest, inventory, mechanism, teleport, summon, or persistent-state
   effects that would be silently lost by suppressing the event.
3. At runtime, apply the derived property only to party step activation on a supporting floor, using the
   shared Levitate policy. The same event id activated by clicking, a timer, or another source must not
   inherit blanket immunity from having a floor binding somewhere else.

Generate this property from the exporter instruction model, not runtime Lua-text scanning. The exploratory
Lua scan above was cross-checked against the original readable instructions; it is not a proposed runtime
classifier. Unrecognized instructions or indirect calls require explicit handling rather than optimistic
classification.

Review the five mixed spell cases and non-spell hazards individually, with explicit overlays/metadata only
where the behavior cannot be established by the conservative rule. For a physical plate that serves both
a trap and a puzzle, bypassing the plate should suppress both effects until the party actually steps on it.
Do not globally make event damage or event spell casting inert whenever Levitate is active.

This replaces the earlier suggestion to hand-mark all MM6/MM7 traps: the ordinary spell cases can be
derived, while ambiguous cases remain a small, reviewable extension.

## Implemented repair and validation

Implemented the shared policy in `ScriptedEventProgram::isLevitateSensitivePressurePlate`, consulted only
by indoor/outdoor party pressure-plate dispatch when Levitate is active. It does not suppress direct event
execution, timers, spell damage, or clicking. Indoor floor-entry tracking still advances while a trap is
bypassed, so expiration does not retroactively activate an occupied plate; leaving and re-entering does.

The legacy Lua exporter now emits:

- MM8 map metadata `levitateTrapFaceMask = 0x08000000`, preserving the native flag requirement.
- MM6/MM7 `levitateTrapEvents`, inferred from reachable normalized instructions and a conservative set of
  hostile trap spells. Beneficial casts, unknown effects, and mixed state changes are excluded.
- Explicit MM6 entries for the five reviewed mixed spell events, Shadow Guild spike event 32, Supreme
  Temple of Baa lava event 34, Superior Temple of Baa lava event 76, and Temple of the Snake damage
  events 16 through 20. Puzzle plates bypass the complete event, including their puzzle-state changes.

This event metadata is necessary because the imported MM6/MM7 BLVs also use MM8 binary layout version 8;
the geometry layout alone cannot select the original flag semantics. Monster-trigger flags in MM6/MM7
are not reinterpreted as native MM8 Levitate flags.

Ran `tools/regenerate_lua_events.sh`. The resulting map-script change is one metadata line in each of 94
files. Unrelated shared-global topic-title churn from regeneration was reverted. All 33 audited MM6 and
14 MM7 hostile-spell floor events are covered. No adjacent map overlay overrides these classified events.

Validation completed:

- `cmake --build build --target openyamm -j25`: passed.
- `cmake --build build --target openyamm_unit_tests -j25`: passed.
- `./build/tests/openyamm_unit_tests --test-case='*levitate*'`: 3 tests, 64 assertions passed.
- Related exporter, pressure-plate, and generated-script tests: 25 tests, 315 assertions passed. These
  overlap the focused selection and are not additional unique counts.
- `OPENYAMM_REGRESSION_FILTER=pressure_plate SDL_AUDIODRIVER=dummy ./build/game/openyamm
  --headless-run-regression-suite indoor`: 9 cases passed, including existing monster-trigger and tiled
  plate re-entry regressions.

The seven new headless map cases use actual imported geometry and loaded scripts: MM8 `d26` and `d05`,
MM7 `7d10` and `7d12`, and MM6 `6d03`, `6d08`, and `6t8`. Each casts Levitate through the spell system,
checks that floor entry creates no trap projectile/damage/state change, expires the buff, and verifies
that re-entry activates the trap even with Water Walk and Feather Fall. Cases with ordinary floor events
also verify those events still activate while levitating. These are deterministic scene-runtime checks;
the fixture restores movement snapshots and preserves the separately owned session party state.

The outdoor hook uses the same policy. The map-entry regression cases above exercise indoor traps; direct
script execution with Levitate is independently checked in all three worlds to prevent blanket spell
immunity. Mixed outdoor encounters, gas/debris events, and chest traps were not reclassified.

## Follow-up: lava (2026-10-26)

The spell text promises that Levitate avoids "damage from drowning or lava". In `MM8-Rel.exe`, the per-tick
environment damage routine `0x494007` tests the party water-damage flag (`0x04` at `0xb7c988`) and the burning
flag (`0x200`), and calls the Levitate helper `0x43f49f` before each damage (`0x494416`, `0x49451b`); either
damage is skipped while any member levitates. The indoor movement code sets the burning flag at `0x473f52` from
face flag `0x40000000` without a Levitate test, so the protection is at damage time and does not depend on the
world. The other movement-path calls (`0x473e66`, `0x4755d2`) only gate footstep sounds.

OpenYAMM burned a levitating party on every lava floor. `IndoorPartyRuntime` and `OutdoorMovementDriver` now skip
burning damage (and outdoor water damage) while Levitate is active.

MM6 and MM7 also scripted some lava floors through step events, which Levitate never covered in MMMerge either.
A scan of the imported BLVs for lava textures and the `0x40000000` flag found:

| Map | Lava floors | Old behaviour |
| --- | --- | --- |
| MM6 `6d18` Gharik's Forge | 31 `orfyrlga` | event 51 sets a map variable; timer event 54 deals 25 magic damage per minute |
| MM6 `6t6` Supreme Temple of Baa | 8 `lavatyl` | event 34: 1000 magic damage per step |
| MM6 `6t7` Superior Temple of Baa | 2 `vlcceila` ("Lava pool") | event 76: 30 magic damage per step |
| MM7 `7d07` Thunderfist Mountain | 7 of 14 `lava` | event 451 kills the party; the other 7 already had the flag |
| MM7 `7d26` The Pit, `d03` Castle Gloaming | flagged native lava | events on two Pit faces are teleports, kept |

Scene overlays (`<map>_1.scene.yml`) now make these floors native lava, as in MM8: they add `0x40000000` and drop the
step trigger `0x04000000`. The events stay bound, so a save that already holds one of these maps keeps its saved
face flags, and the scripted lava, until the map resets. Castle Darkmoor's `lavatyl` faces are walls and puzzle
texture swaps, not floors, and are unchanged.

Validation: the unit tests `indoor lava support applies recurring burning damage` and `outdoor Levitate keeps the
party off lava and water damage`, and the headless cases `indoor_levitate_lava_floor_*` (`6d18`, `6t6`, `6t7`,
`7d07`, MM8 `d38`): each loads the map, checks the overlay flags, stands a levitating party on the lava (no burn,
no step event), then removes the buff (burns, no step event).
