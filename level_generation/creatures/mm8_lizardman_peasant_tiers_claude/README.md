# MM8 Lizardman Peasant / Farmer / Villager colour tiers (2026-10-19)

User: "add the 2 missing color variants for lizardman villager". The installed `mm8_lizardman_peasant.glb`
(production `../mm8_m400/3d_20261006/claude_20261015/`, reduced in `../mm8_lizardman_peasant_reduce_claude/`) shipped
with only `m400_a`; only Lizardmen Male (Peasant) A was bound, so the Farmer (B) and Villager (C) drew sprites.

Same contract as every other tiered model ([creature textures](../CLAUDE_CREATURE_TEXTURES.md)): one shared texture
set, one region mask, and per tier only the ramps differ. `Lizardman_A/B/C` all point at the same base colour, normal,
MR and mask images; `KHR_materials_variants` maps `m400_a/b/c` on every colour and shadow LOD.

The native tiers are palettes 401 / 402 / 403 on the same sprites (`../mm8_m400/native_variants/`). Two regions change:
the garment (green -> tan -> crimson) and the warm trim, belt, collar, apron stripes and shin bands (orange -> purple ->
pale grey). Skin, teeth, the ivory fringe, claws and the gold arm bands stay. `scripts/tier_ramps.py`:

- **Mask.** Channel R (garment) is unchanged. Channel G is the trim: the production `compose.py` warm class, without
  the gold arm bands (rest height > 1.05 m, |x| > 0.17 m) and the ivory claws (below 0.2 m, or |x| > 0.3 m under 1.0 m;
  a first build tinted them lavender in B), padded into the gutters and blurred like R.
- **Ramps.** A's garment ramp is the installed one; A's trim ramp is a least-squares fit to the base (mean error 5.2 /
  255), so A looks as before. For B and C, every native pixel that changes between the palettes (402k pixels over all
  170 stored frames) is split into garment and trim by its 401 colour and sorted by 401 luminance; stop k takes the
  tier's mean colour at the luminance quantile of the region's texels at that stop, scaled to the luminance of A's stop.
  B and C keep A's brightness and take hue and pattern from their own palette. `textures/ramps.json` has the ramps and
  the report.

Review: `review/tiers_rest.png` (installed A / new A / B / C; front, back, three-quarter; shader recolour baked by
`scripts/bake_tiers.py`, rendered by `scripts/shots.py`), next to `../mm8_m400/native_variants/m400aa0_40{1,2,3}.png`.

## Install

Installed 2026-10-19: `export/mm8_lizardman_peasant.glb` (the installed file plus mask channel G, two ramps per tier and
the B/C materials; geometry, clips and other images unchanged; winding 0) with `python3 tools/install_model.py
level_generation/creatures/mm8_lizardman_peasant_tiers_claude/export/mm8_lizardman_peasant.glb --world mm8`.
`assets_dev/worlds/mm8/models/actors.yml` gains `Lizardmen Male (Peasant) B` and `C` (copies of A with skins `m400_b`,
`m400_c`; the native descriptors share height 160, so the scale is the same). The regression
`mm8_lizardman_peasant_actor_model_keeps_native_roles` now also spawns monsters 2 and 3 and checks that all three tiers
use one shared skin and mask with distinct garment and trim ramps:
`OPENYAMM_REGRESSION_FILTER=mm8_lizardman_peasant ./build/game/openyamm --headless-run-regression-suite actors`.
Rollback: install `work/mm8_lizardman_peasant_installed.glb` the same way and remove the B/C bindings.

Rebuild: `tier_ramps.py work/mm8_lizardman_peasant_installed.glb work/tiers.glb` ->
`../mm8_ratman_reduce_claude/scripts/compact_glb.py work/tiers.glb export/mm8_lizardman_peasant.glb`.

## Gait rollout (2026-10-31)

Package h16 of the [gait rollout](../gait_rollout_20261031/h16/README.md) appended two clips to the installed source
for Lizardmen Male (Peasant) A/B/C: `Run` (library Relax-Run-Forward with the arms of the library loop, 0.74 s) and
`Sprint` (Unarmed-Sprint, 0.60 s). Existing clips, meshes and skins are unchanged (binary prefix identical). Installed
2026-10-31 with `tools/install_model.py --world mm8`; bindings for the coordinator
(../gait_rollout_20261031/h16/bindings.yml): run: Run, run_stride_length: 2.7555, sprint: Sprint,
sprint_stride_length: 4.2454. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h16/review/lizardman_peasant_gait_gate.txt`). Rebuild:
`../gait_rollout_20261031/h16/scripts/rebuild.sh lizardman_peasant` (from the pre-gait copy
`../gait_rollout_20261031/h16/work/mm8_lizardman_peasant_pre_gait.glb`). It was the `lod_repair_claude` pilot: a
far-LOD repair rerun replaces the source without these clips: copy the new source over that pre-gait copy and rerun
the rebuild before installing. Rollback: install the pre-gait copy and drop the bindings.

## Rebuilt (2026-11-11)

The model was rebuilt on the MM9 lizard-orc skeleton and clips with a new 4K paint and new A/B/C ramps by the same method
([mm8_lizardman_peasant_rebuild_claude](../mm8_lizardman_peasant_rebuild_claude/README.md)); this project's export is
the previous state.
