# MAW crafting items as 3D ground items — 2026-10-24

The 30 items the MAW ruleset adds on top of MMMerge (ids 1041–1070 in `assets_dev/rulesets/maw/content/items_patch.txt`:
20 crafting gems, Eye of Void, Creator's Hourglass, Pandora's Cube, Archibald's Mirror, Emerald of Power, Pearl of
Memory, Orb of Creation, Celestial Orb, Endless Potion, Crafting Cube) had no ground model and drew the placeholder.
All 30 are now installed under `engine/world_items/` (WIP, excluded from releases like the rest) and bound by icon
in the MAW block at the end of `assets_dev/engine/world_items/items.yml`.

MAW's nine sealed spell books (items 971–979, icons `sbfireu`…`sbdarku`) are not covered: the ruleset does not
implement them yet and their icons do not exist in OpenYAMM.

## Route

The [ground item playbook](../items_claude/GROUND_ITEM_3D_PLAYBOOK.md) route with the workers' later improvements
(paint + material mask atlas, registration warp, per-class PBR from
[items_wip_equipment_geometry_finish](../items_wip_equipment_geometry_finish/README.md)):

1. `designs.json`: identity, materials, material classes, triangle budget, binding length per design.
2. Codex HD three-quarter master from the x2 icon (`scripts/maw3d.py master` + `codex`), reviewed beside the icon
   (`review/masters_*.png`).
3. Geometry:
   - **Meshy Smart Topology, untextured, 5 credits** for 20 designs (Lunar Shard, Amethyst Chunk, the ten set
     stones, the eight sculptural items). Clay checks: `review/plain_*.png`, `review/pilot_plain.png`.
   - **Blender cuts** (`scripts/build_cut.py`) for the 10 regular shapes Smart Topology rounds away: round
     brilliants (gems 05, 06, 07, 10), oval and cushion cuts (02, 09), the teardrop cabochon (04), hexagonal prisms
     (08, Emerald of Power) and the pearl. The pilot's Meshy brilliant (`maw_gem05_st_v1`) came back a smooth cone
     and was not used.
4. `scripts/codex_texture.py prep`: weld, rest pose (`rest: pca_front` for the three set stones Meshy stood on edge),
   ground, reduce to budget, Smart UV, five orthographic guides.
5. One Codex session paints the 3x2 view atlas (single-material gems) or 3x4 paint + mask atlas (gold settings,
   sculptures: red metal, black gem/glass, yellow matte stone/sand) over the guides (`scripts/maw3d.py paint-brief`).
6. `scripts/register_views.py` (all 30 passed: IoU ≥ 0.95, p95 displacement ≤ 4 %), then `codex_texture.py bake`:
   512 px base colour, metallic-roughness and normal maps, `work/codex_tex/<design>_export.glb`.
   `scripts/process_ready.sh` runs register, bake and review renders for every painted design.
7. `scripts/install_maw.py`: winding check (0 inverted closed parts on all 30), `tools/install_model.py --world-items
   --name item_<icon>.glb`, the MAW binding block, `tools/item_model_shapes.py` for bounds. Receipts:
   `work/install.json`.

Ascended Amber Droplet, Ascended Solarstone and Ascended Queen's Diamond were re-mastered lying flat
(`master_note`, `meshy_version: v2`): their first Meshy models wrapped the setting around only part of the rim.
The v1 masters are kept in `meshy/<design>/references_hd/superseded_v1/`.

## Cost

Meshy: **120 credits** (24 Smart Topology jobs, all succeeded; backup account 1,655 → 1,535), receipts in
`meshy/creature_3d_progress.json`, claim `engine:ground-items-maw` released. 5 of them unused (the Meshy brilliant)
and 15 superseded (the three v1 set stones). Codex: 33 master sessions (30 + 3 re-masters) and 30 paint sessions,
at most four at a time, medium reasoning.

## Review

- PBR renders beside icon and master: `review/final_1.png` (loose stones, pearl), `review/final_2.png` (set stones,
  Emerald of Power), `review/final_3.png` (sculptures); pilot `review/pilot_final.png`.
- Native check (NVIDIA/OpenGL, isolated MAW new game, MM7 `out10.odm`, all 30 dropped by `item drop`):
  `review/native/maw_items_out10_near.png`, zoom `maw_items_out10_near_zoom.png`; tour `review/native/tour.yml`.
  No missing-model or placeholder errors in the log. Not checked indoors.
- `./build/tests/openyamm_unit_tests --test-case='*Item model*'`: passed (956 assertions).

Known small flaws: a painted sparkle on one front facet of some cut stones; thin dark slits in an unseen crevice of
Ascended Amethyst Chunk and Ascended Erudite Crystal; Ascended Queen's Diamond is the weakest (muddy facets). Gold
reads darker under outdoor light, as on the other WIP items (metallic 1).

## Caveat for the coordinator

`items_claude/scripts/install_family.py` rewrites `items.yml` from its family manifests and would drop the MAW
block; rerun `python3 level_generation/props/items_wip_maw/scripts/install_maw.py` after it (it only rewrites the
block and bounds). Lengths (world units of the longest horizontal side) are in `designs.json`: loose stones 20–24,
set stones 22–26, sculptures 18–50.
