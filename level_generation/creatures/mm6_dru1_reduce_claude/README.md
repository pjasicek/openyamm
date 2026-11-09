# MM6 Druid / Great Druid / Grand Druid (`dru1`, Druidess A/B/C) reduction (installed 2026-10-14)

User: "3D tris count reduction playbook - do mm6_dru1". No-retexture route
([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed `assets_source/worlds/mm6/models/mm6_dru1.glb`
(one `Druidess` primitive, 9,781 tris, body + head atlas 2080x1024, four influences, 118 joints incl. 60 cloak-chain
bones). Weld 6,839 -> 431 open edges; limits for the 1.694 m height p99 5.08 mm, max 25.4 mm. Scripts: ladder from
`../mm6_djn_reduce_claude/` (piece-aware weights), `decimate_tex.py` from `../mm6_fgt_reduce_claude/` (protect, keep,
groups), `texture_drift.py` / `drift_lock.py` from fgt, close views and probe from `../mm6_nobl_reduce_claude/`.
No Meshy, no texture change.

## What had to be kept

- **Face** (`scripts/face_faces.py`, 1,685 faces): head-atlas faces with skin colour above the choker, plus one ring;
  the face is the review-3/4 Meshy graft, so it stays exact. Check: `work/face_mask_check.png`.
- **Small separate pieces** (`scripts/small_pieces.py`, 728 faces): belt, belt medallion, front panel, wrist cuffs.
  At 70 % the medallion grew a gold shard and the panel studs smeared.
- **Colour boundaries across faces** (`scripts/edge_faces.py`, 310 faces): the bodice neckline/armholes (skin against
  dark leather; zigzagged at every step) and the gold bracer/armband rims on the arms (a notch at 66 %). Studs are
  excluded by hue and by |x| > 0.2 m for the gold rule.
- **One drift-lock round** (`drift_lock.py` from the 70/66/62 drift; `work/lock_e3.npy`, 1,199 faces with the rims).
  A second round moved the drift elsewhere (66 %: 11 faces, 66 cm2), as the playbook says.

## Weights

`reduce_ladder.py` `REA_PIECE_MAX=150`: per-piece nearest-vertex weights only for small pieces (belt and medallion stay
rigid pelvis/spine, review 3); big pieces keep the nearest-face interpolated transfer. Per-piece weights everywhere put
a mis-voted torso split on the wrong piece (29 mm at the chest in Hit 3); nearest-vertex weights on big pieces gave
52 mm in Walking. `export_cand.py` transfers the source's custom normals per corner (the hair shell's outward normals
from review 5) instead of recomputing smooth ones.

## Ladder (every config keeps the face; `work/selection_<label>.json`)

| config | step | tris | p99 / max mm | IoU | drift > 40 | visual |
|---|---|---:|---|---|---|---|
| uniform (no protection) | 70 % | 6,845 | 3.6 / 23.4 | 0.997 | | face changes (not used) |
| face kept | 70 % | 6,845 | 4.6 / 22.9 | 0.994 | | medallion shard, panel smear, neckline zigzag |
| face + hair 60 % + hands 50 % | 70 % | 6,845 | 5.1 / 29.4 | 0.992 | | worse everywhere |
| face + hands 50 % + cloak 80 % | 66 % | 6,455 | 8.3 / 29.0 | 0.983 | 14 | legs/torso take the cut |
| face + pieces + drift lock | 66 % | 6,455 | 6.3 / 23.0 | 0.987 | 6 | neckline still jagged |
| face + pieces + neckline + lock | 66 % | 6,455 | 6.4 / 22.7 | 0.987 | 3 | bracer rim notch |
| **face + pieces + neckline + rims + lock** | **66 %** | **6,455** | 6.5 / 25.0 | 0.986 | **1 (0.7 cm2)** | **pick: matches the installed model** |
| same | 62 % | 6,063 | 7.8 / 28.4 | 0.983 | 1 | lumpier left neckline, faint inner-thigh creases |

The p99 is above the scaled limit in every face-kept config: keeping 3,000+ faces exact pushes the cut onto the cloak
and legs. `scripts/region_error.py` (per region, every 4th frame): cloak p99 ~9 mm whatever its own ratio, legs 7-10
mm, hands 3 mm. The renders of the worst frames (Hit 3, Cast 15, Death 40, Walking 6) match the installed model.

## Pick

`export/mm6_dru1.glb` (= `mm6_dru1_fel3r66.glb`): LODs **6,455 / 3,226 / 1,161 / 387** (installed 9,781 / 4,935 /
1,775 / 592), shadow LODs by `../mm6_dru1_claude/scripts/shrink_shadow_lods.py`, variants on all LOD/shadow primitives
(`carry_variants.py`), textures, ramps, sockets and clips byte-identical. Build: `scripts/build_cand.sh fel3 r66`
(needs `work/ladder_fel3.blend`; config: `REA_PIECE_MAX=150 REA_PROTECT_FACES=work/face_faces.npy
REA_KEEP_FACES=work/lock_e3.npy scripts/run_ladder.sh fel3 0.70,0.66,0.62`).

Review renders (rows installed / pick [/ 62 %]):
- `review/close/sheet_fel3.png`: chest, bracers, hands, front panel.
- `review/close/sheet_fel.png`: chest, panel, side, head (the same lock without the rims).
- `review/close/sheet_anim.png`: Walking 6, Cast 15, Death 40, Hit 3 (whole body, chest, face).
- `review/close/sheet_hand66.png`: Cast hand and face close-ups.

Viewer: `http://127.0.0.1:8901/level_generation/creatures/mm6_dru1_reduce_claude/review/viewer/index.html`
(installed / 66 % pick / 62 % per tier); `check_viewer.mjs` 72 loads, no errors (`review/viewer/check.json`).

## Install after review

Back up the installed source to `work/mm6_dru1_source_pre_reduce.glb`, set the Attack impact to 0.65 s (round 3), then
`tools/install_model.py level_generation/creatures/mm6_dru1_reduce_claude/export/mm6_dru1.glb --world mm6`, the
regression `mm6_druidess_actor_model_tiers_share_one_size`, and the ledger row in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm6:dru1-reduce` held until then.

## Round 2 (user, 2026-10-14): head retexture, black band under the hood, library punch

User: retexture the head with a good texture budget for face and hair (hood may go elsewhere), find the black area
above the hair under the hood, and replace Attack with a library punch (Cast stays). The punch is in
`../mm6_dru1_anim_claude/` (separate README).

**Black band:** not paint (hood lining ~0.45, hair crown ~0.2 luminance in the viewer GLB, `scripts/crown_probe.py`)
and not visible in Blender: the installed head-set normal map shaded the hood lining and hair crown black in the
three.js viewer (tangent mismatch, as the review-4 face cracks). A/B with the normal map removed
(`review/head/viewer/nonormal_front.png` vs `pick_front.png`) shows the band and the light-green edge line gone.
The new head set has flat normals.

**Why the old head texture was poor:** the earlier head upload was a 66-degree Smart UV Project (hundreds of islands)
where the hood took most of the square; the face was scattered fragments (`../mm6_dru1_claude/meshy/head_retexture_v1`).

**New head layout** (`scripts/head_parts.py` -> `head_uv.py`, `review/head/headuv_layout.png`): head-set faces of the
r66 pick split into face/neck/scalp (the big piece), hair shell and hood (their own pieces). Face front = geodesic
disc of 0.10 m around the nose, one angle-based island; scalp/neck/ears one island cut down the back; hood outer and
lining one sheet each (the hood is a closed shell); hair Smart UV at 80 degrees. Own skyline packer (Blender's packer
does nothing in background mode). Texels/cm at 1024: face 26.7 (installed 18.7), hair 11.4 (installed 6.3), neck 6.7,
hood 3.4 (body cloak 2.9). Same 1K head half of the 2080x1024 atlas, so no memory change.

**Meshy** `head_retexture_r66` (10 credits; head-only upload `texturing/dru1_head_upload_r66.glb`, the four HD head
references): clean face; most hair strips and occluded neck/scalp painted hood-green (the hair hangs inside the hood in
every reference view). `scripts/head_raster.py` + `compose_head.py`: face from Meshy, skin matched to the installed
head skin; green neck texels to skin, hidden back scalp to dark hair; the hair is a strand texture (line-integral
convolution along each lock's hanging direction, wave bands by height, palette from the references' hair pixels,
median brightness matched to the installed hair, darker at the roots); hairline/temple hair re-hued; hood luminance
rank-matched to the cloak and the finest speckle damped (review-6 rule); choker gold by height; per-part spec/rough as
installed; flat normals; empty texels filled from the nearest island. `scripts/build_head.sh r66` ->
`export/mm6_dru1_headr66.glb` (geometry and LODs as the r66 pick). Viewer captures: `review/head/sheet_h66*.png`,
tiers `review/head/sheet_tiers.png`.

**Round 2 result:** `export/mm6_dru1.glb` (= `mm6_dru1_r2.glb`): the r66 mesh with the new head set
(`build_head.sh r66`) and the library punch Attack spliced in
(`../mm6_dru1_anim_claude/scripts/splice_attack.py export/mm6_dru1_headr66.glb ../mm6_dru1_anim_claude/work/clips.glb
export/mm6_dru1_r2.glb`). Viewer: round 2 only, three tiers (the viewer rejects models whose clip lengths differ, so
the old-Attack models are compared in `review/head/sheet_h66*.png`); `check_viewer.mjs` 24 loads, no errors.
Install then also needs the Druidess `attack_melee`/`attack_ranged` impact in `assets_dev/worlds/mm6/models/actors.yml`
moved from 0.817 s to 0.367 s (the punch's full reach).

## Round 3 (user, 2026-10-14): Death 2x faster, panel in the walk, a magic Attack

User: "death - 2x faster, walking: [the front panel] gets embedded into skin when walking, attack animation - try to
find something suiting ... her punch looks weak, like it is druidess, she is magic user".

**Front panel:** the installed panel splits every vertex evenly between both thighs (pelvis 0.6, each thigh 0.2; 0.41
each at the tip), so a thigh swinging forward pushed through that side; in Standing the thigh skin already covered the
panel's sides (the narrow V seen before was skin over the leather). `scripts/panel_weights.py` (on
`work/ladder_head.blend` -> `work/ladder_head_panel.blend`): each panel vertex takes the weights of the skin behind it
(ray +Y onto the torso / leg-shell islands, nearest point otherwise; no cloak bones), blended back to the installed even
split in the centre (smoothstep |x| 0.015-0.07 m, 4 smoothing passes; full skin weights crumpled the tip between the
legs). `REA_LADDER=ladder_head_panel.blend scripts/build_head.sh r66 r66p` -> `export/mm6_dru1_headr66p.glb`. The panel
now shows its modelled width (wider over the hips) and no thigh comes through it in Walking, Hit, Cast or the kneel.

**Death:** `scripts/clip_speed.py <in> Death 2 <out>` divides the key times (2.0 -> 1.0 s); the other clips unchanged.

**Attack:** in MM6 her Attack 1 is an elemental missile (Druid Fire, Great Druid Water, Grand Druid Earth,
`monster_data.txt`), so a spell gesture replaces the punch: Mixamo Standing 2H Magic Attack 01 (arms swept overhead,
then a leaning two-palm thrust), see `../mm6_dru1_anim_claude/` README round 3. Impact **0.65 s** (clip 1.33 s).

**Result:** `export/mm6_dru1.glb` (= `mm6_dru1_r3.glb`): headr66p + `splice_attack.py ... work/clips_blast.glb` +
Death x2. Viewer: round 3 only, three tiers (`check_viewer.mjs` 24 loads, no errors). `scripts/vtest.py` now takes clip
lengths from the first GLB, so models with other clip lengths load in the scratch viewer.

**Installed 2026-10-14** (user: "ok accepted"): installed source backed up to `work/mm6_dru1_source_pre_reduce.glb`;
`tools/install_model.py export/mm6_dru1.glb --world mm6` (source byte-identical to the export, runtime copy 508 back
copies); Druidess A/B/C `attack_melee`/`attack_ranged` impact 0.817 -> 0.65 s in `actors.yml`; regression
`mm6_druidess_actor_model_tiers_share_one_size` PASS; ledger row added; lease released.

## Floor fix — 2026-10-21

`--ground-loop Walking --lift-joints Death Dead --lift-only 'Cloak*'` (the left leg's source sink under the cloak is kept, as before). Before, in world units at tier A: walking lifts every foot by +5.5; corpse at -15.3; dying sinks to -15.3.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_dru1.glb`), written to `export/mm6_dru1_floor.glb` and installed as `mm6_dru1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.


## Gait rollout — 2026-10-31

Package [h03](../gait_rollout_20261031/h03/README.md) appended `Jog` to the installed `mm6_dru1.glb` for the chase
(Druidess A-C: Standard and MAW chase at a run pace, Froude above 0.65, which played `Walking` at x1.63-2.04): humanoid set Unarmed-Run-Forward legs, arms from `Walking`, the 15 cloak chains re-simulated (numpy port of `../mm6_dru1_claude/scripts/cloak_sim.py`);
0.70 s, bound stride 2.2475 (3.29 u/s); phase-aligned to `Walking`, planted feet at 5 deg toe-out. Bound as `run` (the coordinator applies
`h03/bindings.yml`); `Walking` stays the wander clip. Every existing clip, mesh, skin and material is byte-identical.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h03/scripts/rebuild.sh dru1` (from the pre-gait copy
`h03/work/mm6_dru1_pre_gait.glb`). A far-LOD repair, floor-fix or any re-export of this model must re-graft `Jog`
(copy the new source over the pre-gait copy and rerun the rebuild, or graft it with `claude_shared/graft_clips.py`).
