# Hesper pickups in 3D (stat canisters, serum vats, supply satchels)

The four dungeon pickups of [PICKUPS.md](../../../design/kreegan_world/PICKUPS.md), each full and empty, as Hesper
decorations staged through `level_generation/projects/hesper_stage/decorations.yml`. The mechanic is the stage's
shared Lua ([`common/pickups.lua`](../../projects/hesper_stage/common/pickups.lua)); the test room is
[`hesper_pickups_test`](../../projects/hesper_pickups_test/README.md).

## Concept

[`concepts/CODEX_BRIEF_PICKUPS.md`](concepts/CODEX_BRIEF_PICKUPS.md) (the Hesper common image contract of
`concepts/monsters/CODEX_BRIEF_BROOD_MACHINES.md`): two candidates, one sheet each with the four props full and empty.
The user chose a mix on 2026-10-23: the canister of [candidate 1](concepts/pickups_candidate_1.png), the vat, satchel
and bundle of [candidate 2](concepts/pickups_candidate_2.png) (`concepts/generation_runs_pickups.json`).

## Route

The decoration route of `level_generation/props/hesper_decorations` (the ground-item playbook with a concept crop as
the design source); `scripts/deco3d.py` and `scripts/codex_texture.py` are its copies reading this folder's
[`designs.json`](designs.json) (concept paths repository-relative).

1. `python3 -I scripts/deco3d.py master <design>`, then `deco3d.py codex meshy/<design>/references_hd/CODEX_BRIEF.md`:
   the HD three-quarter master from the concept crop.
2. `deco3d.py st-request <design>`, then `tools/run_creature_meshy.sh --project level_generation/props/hesper_pickups_claude/meshy`
   submit / poll / download: Meshy Smart Topology, untextured, 5 credits each.
3. `blender --background --python scripts/codex_texture.py -- prep <design>`, `deco3d.py paint-briefs <design>`, the
   three Codex painting sessions, `codex_texture.py -- bake <design>`.
4. `blender --background --python scripts/finish.py`: [`finish.py`](scripts/finish.py) scales every design to its
   `height_m` and writes `work/export/<name>_export.glb` (the stage's source folder). The two containers become one
   model in material variants: the painted fluid (red in the canister's paintings, green in the vat's) is found by
   its hue in the baked base colour (the region mask, `review/masks/`), and each of the seven colours recolours it
   through a ramp of the painting's brightness and lights it with an emissive map of the same mask (bloom in game).
   The canister's empty variant turns the fluid into dark smoky glass without glow.
5. `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py`: 0 inverted closed parts on all 22 exports.
6. Restage (`hesper_stage/stage.py` under the exclusive stage lock).

No LODs: the pickups are 1 600-3 000 triangles (the guidelines' "skip LODs for assets that are already simple";
the loot satchels' LODs visibly changed their shape while walking up to them). No decoration lights: a storeroom of
fourteen vats would break the dungeons' four-lights-per-floor-point rule; the fluid glows by its emissive map.

## Models

| Decoration | From design | Triangles | Height | Notes |
|---|---|---|---|---|
| `hes_stim_canister_<colour>` (7), `hes_stim_canister_empty` | `hes_stim_canister` | 2 499 | 1.00 m | One mesh, eight material variants; radius 30 |
| `hes_serum_vat_<colour>` (7) | `hes_serum_vat` | 3 000 | 0.85 m | One mesh, seven variants; radius 55 |
| `hes_serum_vat_empty` | `hes_serum_vat_empty` | 3 000 | 0.85 m | Its own mesh: the torn membrane, dark hollow |
| `hes_colony_satchel`, `hes_colony_satchel_open` | the two satchel designs | 1 600 each | 0.30, 0.20 m | Radius 0 (walked over, as MM's floor loot) |
| `hes_scrap_bundle`, `hes_scrap_bundle_open` | the two bundle designs | 1 999, 1 599 | 0.32, 0.22 m | Radius 0 |

A map places `hes_stim_canister` or `hes_serum_vat` (the plain names, their hover hints; they show the empty model
until the load event swaps in the rolled colour) and `hes_colony_satchel` or `hes_scrap_bundle`. Colours: red Might,
yellow Accuracy, blue Personality, orange Intellect, green Endurance, purple Speed, white Luck.

Reviews: `review/baked_v1/` (the bakes), `review/variants_v1/sheet.jpg` (every colour and the masks),
`review/final_v1/sheet.jpg` (the eight states), in game `hesper_pickups_test/review/build02/sheet.jpg`.

Known limits: Smart Topology shells leave 40-58 % of each texture seen by no painting (filled outward, the inner
walls darkened); the opened satchel's inside reads dark and blotchy. The colour variants are fifteen near-identical
GLBs (about 1.8 MB each): an engine that chose a binding's material variant would make them one (engine queue, the
integrator's).

## Spending

Lease `engine:hesper-pickups`, cap 40 credits (FIX_PROMPTS), backup account; receipts in
`meshy/creature_3d_progress.json`.

| Date | Job | Credits |
|---|---|---|
| 2026-10-23 | `hes_stim_canister_st_v1`, `hes_serum_vat_st_v1`, `hes_serum_vat_empty_st_v1`, `hes_colony_satchel_st_v1`, `hes_colony_satchel_open_st_v1`, `hes_scrap_bundle_st_v1`, `hes_scrap_bundle_open_st_v1` (Smart Topology, untextured) | 35 |
