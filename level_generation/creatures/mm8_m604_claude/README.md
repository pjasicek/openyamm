# MM8 Ether Knight — m604

> **Installed model reduced (2026-10-19):** the installed body and sword are now the reduction from [`../mm8_m604_reduce_claude/`](../mm8_m604_reduce_claude/README.md) (LOD0 11,114 + 1,260 -> 8,332 + 774), with the cloth mask spill fixed and the Attack retimed (quicker wind-up, calmer slash; impact time and length unchanged). This project's exports and master remain the unreduced production; rollback sources are in `../mm8_m604_reduce_claude/work/`.

Full Claude humanoid-playbook production, 2026-10-18. Ether Knight, Ether Champion and Ether Lord share
one fitted body and a separate right-hand sword. Technical/agent review is recorded separately from user art approval.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m604_claude/review/viewer/)
· [Native sources](references_native/source_inventory.json)
· [Current state and Meshy receipts](creature_3d_progress.json)
· [Runtime contract and hashes](review/runtime_contract.json)

![Finished creature](review/shots/final_ready.png)

## Deliverables

- [Editable, packed Blender master](export/mm8_m604.blend), 58 bones including four twist helpers,
  Sword and Socket_SwordTip. The selected working geometry is `work/ready_lined.blend`;
  `work/texture_master.blend` retains the fitted source actions.
- [Runtime body GLB](export/mm8_m604.glb), [separate sword GLB](export/mm8_m604_sword.glb),
  [portable assembled LOD0](export/mm8_m604_runtime_lod0.glb), and [texture sources](textures/).
- [Three actor bindings](actors_ether_knight_binding.yml), installed in
  `assets_dev/worlds/mm8/models/actors.yml`; descriptors **Ether Knight A/B/C**, table IDs **154/155/156**.
  Installed GLB sources are under `assets_source/worlds/mm8/models/`; cooked models and textures are under
  `assets_dev/worlds/mm8/models/`. Installation used `tools/install_model.py` for both files.
- Body triangle counts: **11,114 / 5,553 / 2,743 / 1,350**. Sword: **1,260 / 630 / 314 / 156**.
  Combined LOD0: **12,374**. Four normalized influences per skinned vertex; rigid gold pieces and a rigid sword.
- Merged 2080×1024 body/head atlas (two 1K sets plus gutter), 256×1024 sword maps. ORM R stores the engine's
  specular mask, G roughness, B zero; metallic factor is zero. AO is baked subtly into albedo. Runtime normal maps
  were converted to glTF +Y. Colour/shadow LODs and the shared shadow correction are included.
- Cloth-only palette masks preserve skin, gold, cuirass and belt. Native Pal605–607 provide green/purple/red
  outer cloth and red/purple/magenta lining. The 1.5-mm cloth shell has independent inner UVs.

## Motion and calibration

| Role | Source | Exported seconds |
|---|---|---:|
| Standing | Mixamo Standard Idle, fitted diagonal sword guard | 3.000 |
| Walking | Armed / ArmedWalk | 0.800 |
| Running | Mixamo Standard Run, fitted carry and closed seam | 0.733 |
| Attack, Attack2 | 1Hand / SwordAttackR6 | 1.733 |
| Hit | Unarmed / UnarmedGetHitF1, reduced torso/head recoil over guard | 0.800 |
| Death | Armed / ArmedDeath1, planted entry and blade-floor correction | 1.267 |
| Dead | Exact final Death pose | 1.000 hold |
| Fidget | Armed / ArmedIdleAlert1 head scan over guard | 2.600 |

The cut retains source speed; its added lead aligns impact/release to **0.9833 s**, near the native 1.0 s.
Hit remains shorter than the native 1.125 s. Both attack roles use the native elemental combat behavior;
charge and release follow `Socket_SwordTip`. No gameplay tables or simulation timing were changed.
Humanoid head look uses Neck/Head, with 45° yaw and 30° pitch limits.

Native standing height is 200 pixels at sprite scale 1.3999938965, giving 280 world units. The standing model
is 1.8719639 m high: binding scale **149.5748852**, yaw offset **−π/2**. Measured walking/running strides are
**1.557079 m / 4.109801 m**. Collision dimensions remain the native table values.

## Review evidence

- [Author gates](review/author_gates.log), [final death correction](review/death_correction.log),
  [export/death checks](review/final_export_checks.log), [export parity](review/export_parity.json).
  Cloned source frames have 0° error. Arm p99 stretch stays below 2× and hand edges below 2.4×.
  Half-frame skin/weapon contact checks pass; planted soles stay on the floor. Running retains its flight phase.
  The blade stays at least 8 mm above the floor during death. The final wrist correction preserves source rotation;
  it removes the rejected axis-only IK roll.
- GLB/master surface parity is within **0.062 mm** over sampled clips and dense strike samples.
  Running/Walking loops close below 0.001 mm; Standing's breathing seam is below 0.7 mm; Dead is exact.
  The source sword cut itself has a rapid rotation at impact; source comparison is retained in
  `work/source_attack_steps.json`.
- [Continuous playback](review/playback/playback.json): 16 WebM recordings, all eight roles at 1× and 0.5×,
  with advancing-time screenshots. Reviewed gait, guard transitions, strike/recovery, head recoil/scan,
  fall, held endpoint, fingers, armour and cloth. `review_*.jpg` sheets index the live captured frames.
  [Face](review/shots/final_head.png), [hands](review/shots/final_hands.png),
  [rear grip](review/shots/final_hands_back.png), [Champion](review/shots/champion.png),
  [Lord](review/shots/lord.png), [corpse](review/shots/final_dead.png).
- Final viewer check: **24 tier/clip combinations**, no failures or browser errors. The viewer bakes the same
  region ramps for Three.js; the installed engine GLB keeps the palette masks and variants.
- Ordinary development build passed. [MM8 actor regression](review/actors_mm8.log): **21 passed**.
  [MM6 goblin baseline](review/actors_mm6.log): **1 passed**. The new Ether Knight case covers all tiers,
  shared geometry, all roles, sword attachment/socket and unchanged HP/position/animation ticks.
- [Outdoor model](review/ingame/outdoor_3d/tiers.png) and
  [native sprites](review/ingame/outdoor_sprite/tiers.png): matching New Sorpigal camera.
  [Indoor model](review/ingame/indoor_lineup_3d/tiers.png) and
  [native sprites](review/ingame/indoor_lineup_sprite/tiers.png): matching Agar camera.
  Indoor dynamic summons require sprite preloading; [isolated fixture](review/ingame/indoor_fixture.json)
  adds distant preload actors only to a private asset copy. Production map hash is preserved.
  Earlier empty Agar sprites and unsuitable Escaton camera probes are retained as diagnostics, not accepted evidence.
- [Normal-speed combat](review/combat_sheet.jpg): approach, sword-tip charge/release, elemental projectile,
  melee swings, forced hit, death and the game's ordinary summoned-remains transition. Native captures used
  the desktop OpenGL renderer on NVIDIA (vendor 0x10de), Wayland, isolated settings/saves. These are visual checks,
  not performance measurements. Full run records/logs are in `review/ingame/run_records/`.
- [Original sprite/palette integrity](review/native_integrity.json): original files were preserved.

## Provenance and choices

**40 Meshy credits** total: body Smart Topology 5, diagnostic rig 5, two head geometry jobs 5 each,
body/head retextures 10 each. No paid animation jobs. Task IDs, requests and download hashes are retained in
`creature_3d_progress.json`; original returns remain in `meshy/`. Generated body/head/sword references and
prompts are in `references_hd/`. The first head was rejected for cracks; the selected second head was grafted,
reduced and closed with twelve small UV-matched cap triangles.

The retained animation library clips were retargeted locally. Meshy body retexture UVs were transferred by exact
face correspondence instead of replacing the rigged body. Invalid/degenerate upload caps were explicitly removed;
all returned triangles were accounted for. Rear chain strips and the short mantle follow the native silhouette.
The sword was built locally from the generated silhouette with a bevelled blade, cylindrical grip and solid hilt.
Its painted front/back share the intentionally mirrored artwork. Raw animation-library files are not runtime assets.

## Rebuild

Acquire a fresh `mm8:m604` lease with `tools/creature_workspace.py claim` and run:

```sh
python3 level_generation/creatures/mm8_m604_claude/scripts/rebuild.py --token YOUR_TOKEN
```

This rebuilds motion, prepared GLB, LODs, palette masks, attachment split, merged head atlas, viewer tiers and numeric
checks from the selected textured revision. Review playback after motion changes. For geometry/texture changes,
start from the retained texture/UV stages and regenerate `ready_lined.blend` with `line_cloth.py`; do not rerun
`swap_lining.py`, which records a one-time historical correction. Install both final GLBs with `tools/install_model.py
<file> --world mm8` under the creature workspace guard, then rerun affected checks. Release the lease afterward.

Android/Vulkan execution and hardware performance profiling were outside this creature-production check.
User artistic approval is **not recorded**. No unresolved asset defect is being accepted as approval.
