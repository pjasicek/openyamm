# MM9 dwarf boy (PeasantDboy1) — status (owner dboy-sigmund-agent)

- Project: `level_generation/creatures/mm9_peasantdboy_claude/`, lease `mm9:peasantdboy`.
- Rows: 67 Commoner Child (skin DWARFBOY1), 68 Townsfolk Child (skin DWARFBOY2): two tiers of one body.
- Mesh check (`mm9_meshcmp.py peasantdboy1:peasantboy1,peasantdm1,peasantchildboy`): skeleton 38 nodes (boy/childboy 30, DM1 41);
  after rigid shift 2-4 cm head, 4-7 cm torso/legs from both: a new body. PEASANTDBOY1.abc has NO child models and carries its
  own clips (stand, aware, fidget1/2, sitdown, sit-wait, sitfidget1/2, walk, run, Hattack1, wince1, die1): its own skeleton
  and clip set, not PEASANTCHILDBOY's or the dwarf library.
- Phase: **installed and bound** (2026-11-02 ~21:00). `assets_source/worlds/mm9/models/mm9_peasantdboy.glb` (sha256 ab3ec78feaac...),
  variants pdboy_a (67) / pdboy_b (68); `MM9 67 Commoner Child`, `MM9 68 Townsfolk Child` (actors.yml block mm9_peasantdboy_claude);
  rows 67 -> 313, 68 -> 322 in mm9_npc_actor_rows.tsv; tables regenerated; body overrides 97 / 26 (MM9 rule, sane for 1.01 m).
- Gates: arm/hand 0 frames > 1 cm all 9 clips; jitter 0; detached 0; winding 0; flat 0.00; bones 0; floor ok; LOD0 12,983;
  body atlas 57.2 %, head set 40.9 %; viewer 18 switches 0 errors; `mm9_actor_models_build_every_binding` PASS (240 on 105).
  See-through not 0: sleeves 15-23 px, torso 50 px on one Death fall frame (was 160 / 68 before linings).
- Credits: 35 / 50 (Smart Topology 5, body 4K 10, head a 10, head b 10); backup 2640 -> 2580 over these jobs (shared).
- Open: b keeps a's waist shirt band / checked trousers (pattern, not colour); low-camera mouths show a thin lip line; Fidget arms
  swing out ~26 deg to clear the flared tunic. Map placement left to the orchestrator.
