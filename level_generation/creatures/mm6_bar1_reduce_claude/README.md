# MM6 Magyar / Barbarian (`bar1`, Barbarian A/B/C) reduction (2026-10-14, installed)

User: "3D tris count reduction playbook - do barbarian". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the live barbarian (10,117 tris, one material over a body atlas plus a 1K head set, three variants, held
`mm6_bar1_sword.glb` unchanged at 348 tris; project `../mm6_bar1_claude/`). Scripts copied from
`../mm6_nobl_reduce_claude/` and `../mm6_fgt_reduce_claude/`. No Meshy credits. Limits for the 1.693 m height:
p99 5.08 mm, max 25.4 mm.

**Source:** the runtime copy `assets_dev/worlds/mm6/models/mm6_bar1.glb` equals `../mm6_bar1_claude/export/mm6_bar1.glb`
(2026-10-13, Mixamo Standard Run), while `assets_source/worlds/mm6/models/mm6_bar1.glb` still holds the 2026-10-11
export. The reduction starts from the live one (`work/mm6_bar1_source_pre_reduce.glb`); the older source is kept as
`work/mm6_bar1_assets_source_20261011.glb`. Installing this export also brings `assets_source` up to date.
Bindings (`actors.yml`) are not touched.

## Ladder

| config | step | tris | p99 / max mm | finding |
|---|---|---:|---|---|
| uniform | 55 % | 5,563 | 4.4 / 17.2 | auto-pick; mouth and chin smeared, eyes shift |
| face, studs kept; hair 60 %, gloves 45 % | 68 % | 6,877 | 6.5 / 32.9 | fails: gauntlet forearms, thighs, boots absorb the cut |
| g3: face kept, rest uniform | 64 % | 6,473 | 4.6 / 17.2 | face exact; studs turn into pyramids, belt ring hexagonal, dark streak on the right thigh |
| g5: face at 75 % | 57 % | 5,865 | 4.7 / 17.2 | mouth softer, grey streaks under the eyes |
| g7: g3 + drift lock + thigh lock + studs, pendant, belt ring kept | 70 % | 7,081 | 5.0 / 20.0 | parts round, streak gone; bra cups crease, loincloth scale pattern warps |
| g8: g7 + bra at 75 % | 70 % | 7,079 | 5.0 / 19.6 | bra clean; loincloth warp, slivers at its side flaps, gold wedge beside a belt stud |
| g9: g8 + loincloth kept + drift lock for this config | 72 % | 7,283 | 4.7 / 18.9 | loincloth matches; gold wedge remains |
| **g10: g9 + belt lock by the wedge** | **72 %** | **7,283** | 4.7 / 18.9 | **pick** |

Selections (`scripts/face_groups.py`, components of the welded mesh): face = the head texture set (atlas u > 0.505:
face, lips, circlet; 2,261; the hair lives on the body atlas), 32 studs (31-52 faces each, 1,213), collar pendant
(114), belt ring (159), loincloth (160), plus drift-locked faces. `scripts/viz_groups.py` renders them
(`review/groups_sheet.png`). Kept exactly: 3,868 faces (`work/keep_g10.npy`); bra (450) at 75 %
(`work/groups_bra.npy`); the rest (hair, skin, gauntlets, boots, shoulder pads, belt) at about 52 %.

New scripts:
- `pixel_lock.py`: the mean-colour drift check misses thin streaks along UV seams (the thigh) and small wedges; it
  ray-casts pixels of a close render onto the posed source and locks the source faces there.
- `sword_grip_gate.py`: sword at the `Sword` joint, every 2nd frame of the held clips; renders the gripping hand
  (`GRIP_RENDER`). Its numeric inside test flags most glove vertices on both models (not trustworthy here; the counts
  scale with the glove's vertex count, 0.50); the renders decide.
- `sheet.py`: contact sheets of close renders.

Texture drift of the pick: 2 faces above 40 (1.9 cm2), p99 14.3.

## Result

`export/mm6_bar1.glb` (= `mm6_bar1_g10r72.glb`): LODs 7,283 / 3,641 / 1,288 / 415 (installed 10,117 / 5,084 /
1,812 / 578), shadow LODs rebuilt, variants on every primitive, eight clips and the `Sword` joint unchanged.
LOD0 -28 %.

Review: `review/close/sheet_final.png` (rows installed / pick: tiers B and C, side, Attack 15, Death 12, Running 6,
face, chest), `sheet_g7.png` and `sheet_g8.png` (clay and textured), `sheet_face.png` (face configs),
`review/grip/grip_sheet.png` (rows installed, g8r70, pick: Standing 0, Attack 12, Attack 22), `sheet_uni.png`
(uniform 55 %). Viewer `review/viewer/`: installed / pick / uniform 55 % per variant; `check_viewer.mjs` 72 switches,
no console errors. Other candidates are in `work/candidates/` and `work/candidates_viewer/`.

## Face skin colour (user review 1)

User: the head skin does not match the body. The tier ramps only recolour clothing, so the skin is the baked base
colour, and the 1K head set's skin was darker and browner than the body's (texture Lab: face 40.8 / 16.3 / 27.4,
body skin of the chest, shoulders and arms 47.2 / 17.8 / 33.0). Normals, roughness and the normal map match; this
predates the reduction (the installed model has it too).
`scripts/skin_match.py`: head-set texels move to the body skin's Lab mean (contrast change capped at 1.15x),
weighted by skin likelihood (the head set also holds hair islands; eyes, brows, lips and the circlet keep their
colours), plus 6 L*: the vertical face under the hair gets less light than the upward-facing chest, so a plain
match still read darker in the viewer. `scripts/swap_basecolor.py` replaces the shared base colour atlas (body half
unchanged). No retexture. Review `review/skin/viewer_skin_sheet.png` (installed, fixed tier A, fixed tier B;
front and three-quarter), `review/skin/head_before_after.png` (head set before, after, skin weight).

`export/mm6_bar1.glb` is now `mm6_bar1_g10r72s.glb` (same geometry and LODs). Viewer: installed / pick / pick before
the skin match / uniform 55 %; `check_viewer.mjs` 96 switches, no console errors.

## Left hand spike (user review 2)

User: a stray polygon on the left hand. It is in the installed model too (Meshy source):
- **Broken hub** (`scripts/hub_caps.py`, `fold_probe.py`): vertex 1693 (ring finger) was the shared centre of twelve
  hole caps across the thumb tip, palm, index and middle fingers (40 faces, edges up to 10 cm), drawn as a long fin;
  some caps also doubled existing faces into zero-thickness fins. `scripts/fix_hub_holes.py` (on
  `work/source_pre_hubfix.blend`) deletes the hub and its faces, closes exactly the loops that opened (holes_fill;
  rims it skips are built from the ordered rim), copies UVs from adjacent faces and flattens the three rim vertices
  left as spike tips (thumb 15 mm, palm flap 30 mm, index 12 mm). 10,117 -> 10,092 source faces; no open edges remain
  there (two that were already open are closed too). Face map `work/face_map.npy`; keep masks remapped
  (`keep_g12.npy`, `groups_bra12.npy`, `regions.npy`; old regions in `regions_pre_hubfix.npy`).
- **Stray weights** (`scripts/weight_outliers.py`, REA_LIMIT 0.15): seven finger vertices (four left, three right)
  whose bone none of their neighbours shared, refilled from their neighbours (`work/source_pre_weightfix.blend`).
  `scripts/far_weights.py` found no finger vertex far from its bone.
- **Fused thumb**: the posed spike remained. `scripts/stretch_edges.py` (every 2nd frame of every clip): in the curled
  rest pose the Meshy thumb tip is fused to the ring and middle fingers; finger motion stretched those edges from
  about 1 cm to 11 cm (Hit 6) and tore shards in Attack. `scripts/freeze_fingers.py` removes the 360 animation channels
  of the 15 `B_L_Finger*` joints, so the left fingers hold their rest curl (a relaxed cupped hand) in every clip; the
  stretch check then finds no left-hand bridge (right-hand sword grip: up to 24 mm, unchanged and expected).
Renders: `review/hands/final_left_sheet.png` (rows installed / final: Standing, Attack 20, Hit 6, Running 6, front
and three-quarter), `review/hands/freeze_sheet.png` (clay), `review/hands/fix_sheet.png` (rest-pose repair, new faces
red), `review/grip/grip_sheet_final.png` (grip unchanged).

`export/mm6_bar1.glb` = `mm6_bar1_g13r72sf.glb`: ladder g13 (keep masks of g10, repaired source) r72 PASS (p99 4.69,
max 18.9 mm), skin-matched base colour, frozen left fingers. LODs **7,262 / 3,630 / 1,287 / 414**. Viewer: installed /
pick / previous pick; `check_viewer.mjs` 72 switches, no console errors.

## Install (2026-10-14)

User: "ok accepted". `tools/install_model.py export/mm6_bar1.glb --world mm6`: `assets_source` holds the export
(md5 07b07165...), the runtime copy culled 11,970 of 12,593 checked triangles (623 back copies). `actors` suite: 66
pass; failures in other models only (pmn2 mage and gua guard tier materials, ooz skin; DWI cases and the final
`bad_alloc` failed the same way on 2026-10-12), the suite has no barbarian case. Ledger row in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm6_bar1_source_pre_reduce.glb`.

## Floor fix — 2026-10-21

`--raise Hit --ground-death Death Dead` (limbs are not bent). Before, in world units at tier A: Hit sinks to -4.7; corpse at -3.1; dying sinks to -4.3.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_bar1.glb`), written to `export/mm6_bar1_floor.glb` and installed as `mm6_bar1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31)

Package h01 of the [gait rollout](../gait_rollout_20261031/README.md) appended `Jog` (humanoid set
Unarmed-Run-Forward, 0.68 s, stride 3.2856) and `Sprint` (Unarmed-Sprint, 0.56 s, 4.2974) to the installed
`mm6_bar1.glb` (arms and sword from `Running`, aligned to `Walking`). Existing clips untouched; bindings for the
coordinator in `../gait_rollout_20261031/h01/bindings.yml` (run `Jog`, sprint `Sprint`). Details, gates and doubts:
[h01 README](../gait_rollout_20261031/h01/README.md). Rebuild: `../gait_rollout_20261031/h01/scripts/rebuild.sh bar1`.
A far-LOD repair or head-bob rerun (or any other rebuild of this source) must re-graft these clips: copy the new
source over `h01/work/mm6_bar1_pre_gait.glb` and rerun that command, then install its export.
