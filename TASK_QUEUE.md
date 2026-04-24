# Task Queue

## Execution Rules

- Use this file as the executable queue.
- Use `implementation_plan.md` as the authoritative detailed source.
- Do not execute the detailed plan linearly.
- Work one coherent task or tightly related micro-batch at a time.
- Prefer unit tests for pure logic and headless tests for runtime/map behavior.
- Keep shared gameplay shared. Do not duplicate outdoor logic into indoor.
- Consult local OpenEnroth only for behavior when needed. Do not copy code.
- Keep the repository buildable after each meaningful slice.
- Update `PROGRESS.md` after each meaningful slice.
- Update this file when task status changes.

## Current Migration Order

1. BUG1 - Stabilize active indoor combat regressions and validate hit reactions.
2. BUG2 - Stabilize indoor corpse/world-item interaction parity.
3. BUG3 - Fix indoor event/status/dialogue activation gaps.
4. FEATURE1 - Implement shared wand attack behavior.
5. FEATURE2 - Implement Recharge Item and inventory item mixing.
6. FEATURE3 - Implement Lloyd's Beacon screen, state, and save data.
7. FEATURE4 - Implement remaining spell gaps: Summon Wisp, Prismatic Light, Soul Drinker, indoor-only spell gates.
8. FEATURE5 - Implement monster relation overrides and unique actor guaranteed drops.
9. FEATURE6 - Implement save screenshot preview and dungeon transition dialogue.
10. SAVE1 - Implement indoor save/load parity for spawned/placed actors, corpses, mechanisms, and NPC animation state.
11. FINAL - Cleanup, validation, and progress closeout.

Reason:

- active regressions should be fixed before adding feature surface area;
- item/spell features should be shared before more indoor-specific parity work;
- save/load parity is large and should happen after core runtime state is stable enough to serialize confidently.

## Ready

### BUG1 - Stabilize Indoor Combat Hit Reactions

- [ ] Verify current behavior for indoor non-lethal damage from:
  - party melee;
  - party ranged/projectile spell;
  - actor projectile;
  - actor melee;
  - area/collateral damage.
- [ ] Identify whether hit reactions are missing because shared combat does not request them, indoor world hook drops
  them, actor AI overwrites them, or animation selection/rendering ignores them.
- [ ] Fix the smallest structural owner:
  - shared combat if the reaction rule is shared;
  - indoor world hook only if indoor actor animation state is not being translated correctly.
- [ ] Preserve dying/dead animations and do not interrupt active attacks unless OpenEnroth behavior indicates that it
  should.
- [ ] Add doctest coverage for any pure hit-reaction rule.
- [ ] Add or update focused headless coverage if runtime actor state is observable.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### BUG2 - Stabilize Indoor Corpse And World-Item Interaction Parity

- [ ] Verify corpse looting, corpse disappearance, corpse outline, corpse inspect, and Space/E target selection.
- [ ] Verify world item pickup, inspect, identify/repair service use, outline, and billboard ray picking.
- [ ] Ensure item/corpse gameplay actions use shared item/interaction services where possible.
- [ ] Keep indoor-specific code limited to world hit facts, billboard picking, corpse/world-item lookup, and removal from
  BLV runtime state.
- [ ] Add unit tests for shared item/interaction decision logic if changed.
- [ ] Add focused headless coverage if corpse/world-item runtime state is observable.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### BUG3 - Fix Indoor Event, Status Text, And Dialogue Activation Gaps

- [ ] Audit indoor hover-only faces and Lua status text routing.
- [ ] Ensure status text reaches the shared status bar path.
- [ ] Audit indoor face/decor/door dialogue activation.
- [ ] Reuse the shared dialogue/house/NPC UI path; do not create an indoor dialogue renderer.
- [ ] Include pressure plates, event-spawned spell handling, and missing indoor event opcodes if they are directly tied
  to activation flow.
- [ ] Add headless coverage for event/status/dialogue cases where feasible.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FEATURE1 - Implement Shared Wand Attack Behavior

- [ ] Inspect data tables and local OpenEnroth behavior for wand item type, charges, spell mapping, mastery/skill, and
  empty-charge behavior.
- [ ] Implement wand equip/use as shared item/combat/spell action behavior.
- [ ] Route wand firing through the shared attack/spell projectile path, not an outdoor-only branch.
- [ ] Consume one charge per successful wand fire.
- [ ] Handle zero charges consistently with broken/empty behavior.
- [ ] Add doctest coverage for wand selection, charge consumption, and empty-charge behavior.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FEATURE2 - Implement Recharge Item And Inventory Item Mixing

- [ ] Implement Recharge Item as shared spell/item targeting for wand items.
- [ ] Restore charges according to spell skill/mastery behavior from data/reference behavior.
- [ ] Implement inventory mixing as shared inventory held-item-over-target behavior.
- [ ] Use `data_tables/english/potion.txt` or loaded repository data for valid potion/reagent combinations.
- [ ] Handle invalid combinations and character reactions.
- [ ] Add doctest coverage for valid recharge, invalid recharge target, valid mix, invalid mix, and consumed/created
  item state.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FEATURE3 - Implement Lloyd's Beacon

- [ ] Add `lloyds_beacon.yml` with the requested full-screen layout, Recall, Set, Close, and five beacon slot buttons.
- [ ] Implement shared Lloyd's Beacon UI state:
  - recall mode;
  - set mode;
  - five saved beacon slots;
  - location name;
  - remaining duration;
  - screenshot preview.
- [ ] Implement set-beacon duration based on Water skill/mastery.
- [ ] Implement recall teleport and exit back to gameplay.
- [ ] Persist beacon data in save files.
- [ ] Add doctest coverage for duration/state calculations and save data round-trip if feasible.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FEATURE4 - Implement Remaining Spell Gaps

- [ ] Fix Summon Wisp to summon one wisp per cast while respecting the limit.
- [ ] Add indoor/outdoor spell availability gates for spells such as Meteor Shower and Starburst through shared spell
  rules.
- [ ] Implement Prismatic Light with correct damage/victim collection and shared FX.
- [ ] Enable/fix Soul Drinker indoors using shared spell logic and indoor victim collection.
- [ ] Add doctest coverage for spell availability and pure spell outcomes.
- [ ] Add focused headless coverage for summon and indoor spell effects if feasible.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FEATURE5 - Monster Relations And Unique Drops

- [ ] Inspect authored actor override data and local OpenEnroth behavior for monster relation overrides.
- [ ] Fix relation/faction resolution for special authored actors such as out05 Dragon Hunter Pet.
- [ ] Inspect authored actor special drop data and local OpenEnroth behavior.
- [ ] Fix guaranteed drops for special authored actors such as Jeric Whistlebone.
- [ ] Add unit/headless coverage for relation override and guaranteed-drop cases where feasible.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FEATURE6 - Save Screenshot Preview And Dungeon Transition Dialogue

- [ ] Fix save-game screen preview display for existing saves using the same screenshot data path as load game.
- [ ] Implement dungeon transition dialogue from Lua `MoveToMap` data using the shared dialogue screen.
- [ ] Reuse transition videos from `assets_dev/Videos/Transitions/`.
- [ ] Resolve transition text from `trans.txt`.
- [ ] Use a small mapping table only if no authored data maps dungeons to transition videos/images.
- [ ] Add tests for non-render logic where feasible.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### SAVE1 - Indoor Save/Load Parity

- [ ] Audit current indoor save/load gaps:
  - spawned actors;
  - placed actors;
  - corpse and loot exhaustion state;
  - NPC animation state;
  - mechanisms/doors;
  - map event state needed after reload.
- [ ] Inspect local OpenEnroth for which BLV/DLV runtime fields are persisted.
- [ ] Persist only real runtime state, not renderer-derived state.
- [ ] Add headless save/load coverage for representative indoor actors, corpses, and mechanisms.
- [ ] Build and run relevant validation.
- [ ] Update `PROGRESS.md`.

### FINAL - Cleanup And Validation Closeout

- [ ] Static-audit for stale diagnostics and temporary logs.
- [ ] Static-audit for new indoor/outdoor duplication in shared gameplay areas.
- [ ] Run default validation.
- [ ] Run relevant focused headless suites.
- [ ] Update `ACCEPTANCE.md`.
- [ ] Set `PROGRESS.md` done definition to YES only if acceptance is satisfied.
