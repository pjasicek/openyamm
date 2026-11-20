# MM6 Cannibal (`natm`) — reduction + Meshy retexture (2026-10-14, staged, not installed)

Source: the installed `mm6_natm.glb` from `mm6_natm_claude/` (9,230 body triangles; spear and buckler are separate
attachments and unchanged).

## Round 1: texture-aware reduction ladder

`reduce_installed.sh natm Natm "MM6 Cannibal"` (RETOPOLOGY_PLAYBOOK.md default route, step 1). No step passed the
automatic limits (p99 5.1 mm), so the pick was visual, as for the goblin:

| step | triangles | p99 / max mm | IoU min | |
|---|---:|---|---|---|
| r70 | 6,460 | 8.0 / 26.7 | 0.989 | |
| **r55** | **5,076** | 11.3 / 45.1 | 0.978 | **picked** |
| r45 | 4,152 | 14.2 / 50.3 | 0.968 | forearm/wrist blocky |
| r30 and below | | | | broken |

Spear fist (`review/hand_cmp.png`) stays curled with the shaft opening at r55 and r45.

## Round 2: r55 + Meshy retexture (body and head)

The old textures on the r55 head gave a smeared, frowning mouth (`review/retex_face_cmp.png`, middle row), so the
picked mesh was put back into the cannibal's own master and retextured with its own chain:

1. `scripts/swap_body.py -- r55`: the r55 mesh into `../mm6_natm_claude/work/rig_v5.blend` (rig and final clips).
   Per connected piece the source piece by majority vote; weights and `orig_co` by barycentric interpolation on the
   nearest source triangle of that piece (fallback to the nearest surface beyond 5 mm: the welded source joins
   touching cards; 167 vertices); labels from the nearest corner. Vertex group names live on the mesh in Blender 5,
   so they are recreated on the new mesh. Max surface distance 8.3 mm.
2. `scripts/export_uploads.py` (copied unchanged): body upload 5,076 faces, head 632 faces (HeadUV 61 % coverage).
3. Meshy `body_retexture_r55` / `head_retexture_r55` (`requests/`, the accepted v1 requests and references):
   **20 credits**, both back in about 2 minutes.
4. `scripts/r55_texture_chain.sh`: UV transfer (head exact; body 4 faces > 2 mm), raster, AO, `compose_natm.py`
   (pointed at the r55 jobs), `build_runtime.sh` (no install). LODs 5,076 / 2,298 / 661 / 347.

Fix found on the way (`bake_ao_natm.py`): head faces keep stray coordinates in the body `UVMap` layer (it is created
from `HeadUV`), so the body AO bake also drew the enclosed eye shells (black AO) over forearm and hip islands: dark
triangles on the forearms and lower belly. The bake now parks head faces in a corner of the body layout as it already
did for body faces in the head layout. The installed model's bake has the same latent issue (932 skin texels with
AO < 0.1 against 488 here).

Review: `review/retex_final.png` (installed tier A vs r55t tiers A/B/C; faces; spear hand), `review/retex_face_cmp.png`
(rows installed, r55 old textures, r55 retextured), viewer `review/viewer/` (r100 / r55 / r55t per tier,
`check_viewer.mjs` 81/81, no console errors).

## Round 3: installed head + reduced body (h65, current pick)

User (2026-10-14), comparing the r55t face with the installed one: the r55 head looked worse. Cause: the uniform
ladder halved the head (1,377 -> 632 head triangles), and the new head texture followed the flatter forms (pouting
lips, broader nose, longer jaw).

- `decimate_tex.py` with `REA_PROTECT_HEAD=1 REA_PROTECT_ZMIN=1.43 REA_TAG=h`: every face above 1.43 m (the whole
  head set, the collar tops) kept as installed (2,085 faces), the rest decimated with its cut edge preserved and
  welded back. Open edges 1,714 as in the source (no crack). **h65: 5,998 triangles** (the rest at r55's density).
- `copy_head_uv.py`: the head faces are the installed ones, so the installed `HeadUV` is copied by corner position
  (1,377 of 1,377; quads in the master, triangles here; matched by distance, glTF float noise 0.2 µm) and compose
  uses the installed `head_retexture_v1` job: the head texture set is the accepted one, unchanged.
- Meshy `body_retexture_h65`: 10 credits. `scripts/h65_texture_chain.sh` (body UV transfer, raster, AO, compose,
  runtime). LODs 5,998 / 2,761 / 827 / 391.
- Review `review/h65_cmp.png` (tiers installed vs h65; face front and three-quarter; spear hand). Viewer models
  `*_h65` (default) beside `*_r100` and `*_r55t`; `check_viewer.mjs` 81/81.

Meshy in this project: 30 credits (r55 body + head 20, h65 body 10). `export/mm6_natm.glb` is h65;
`export/mm6_natm_r55t.glb` keeps round 2.

Lesson: on a humanoid, the texture-aware ladder must protect the head (`REA_PROTECT_HEAD`, plus a height cut that
covers the head texture set); keeping the head also keeps the accepted head texture, so only the body needs Meshy.

## Round 4: body texture artifacts (user review of h65)

User: pale strips on the chest under the necklace, a lighter patch at the shoulder/mantle edge, a patch on the belly.
Meshy's raw body paint was clean there (`work` diagnostics: raw base colour, AO, class map rendered on the rest mesh);
the compose labels were wrong:

1. **Pendants classed as skin.** The Smart Topology mesh fused the necklace and hip-trim pendants to the skin piece,
   so `garments.py` labels them skin and the skin repaint turned Meshy's ivory bone into pale skin strips. The
   installed model has the same defect (peach pendant tails, lighter chest polygons). `compose_natm.py`: skin texels
   Meshy painted ivory (sat < 0.3, val > 0.55, components >= 6) are bead below z 1.30 and in a narrow box over the
   chest pendants (33,453 texels); ivory paint at the mantle edge stays skin.
2. **Per-component labels after the swap.** The reduction's source is welded, which joins touching cards to the
   skin; `swap_body.py` now labels per face (nearest source triangle within 12 mm with an agreeing normal) and
   stores `fgarment`/`fpiece` face attributes, which `uv_raster.py` uses (a shared vertex has one label). 438 of
   439 source pieces matched (was 406). Same geometry, so the Meshy body job stayed valid (no new credits).

Review `review/h65_chest_fix.png` (installed vs h65 at the user's camera). Viewer `*_h65` rebuilt, 81/81.

## Round 5: "two stray triangles on his pecs" = a hole in the chest

The two triangles under the middle pendant were the inside of his back, seen through a 5 x 3.6 cm hole in the chest
under the necklace (face ids rendered per pixel; rays through those pixels missed the chest). The Codex Smart Topology
mesh never had skin there; the fused pendants hid it, and **the installed model has the same hole**.

- `scripts/hole_probe.py`: ray grids from 16 cameras; a ray whose first hit is the back of a skin face looks into the
  body. Installed 278 such hits, h65 279 (chest, plus armpit and upper-back folds that exist in both and are not
  holes in the boundary sense).
- `scripts/fill_holes.py` (in `h65_texture_chain.sh` after the UV transfer): closed skin-only boundary loops of 5+ edges
  get a fan from a new centre vertex (average weights of the loop), every triangle facing away from the body axis,
  with the UV triangle of a plain chest neighbour. A plain fill folded one triangle backwards (the loop is not
  planar) and a single-texel UV came out darker than the chest; both were replaced. After: 1 backface hit.
- Body 6,003 triangles. Review `review/h65_hole_fix.png`; viewer 81/81.

## Installed (2026-10-14, user accepted round 5)

`tools/install_model.py export/mm6_natm.glb --world mm6` (body only; spear and buckler exports are byte-identical to
the installed attachments). Previous source: `work/mm6_natm_source_pre_reduce.glb`. LODs 6,003 / 2,765 / 828 / 391.
Regression (`actors`, filter peasant): `mm6_peasant_m4_actor_model_tiers_share_the_native_height` and the other
peasant model cases pass; `dwi_peasant_actor_5_does_not_flee_on_start` fails ("actor 5 missing", an MM8 event case,
not a model binding). In game (oute3, three tiers, before/after): `review/ingame/ingame_cmp.jpg`.

## Clip speed (2026-10-14, user: attack 50 % faster, death 2x faster)

`scripts/retime_clips.py -- work/rig_v5.blend Attack:1.5 Death:2` compresses the key times (rounded to whole frames:
Attack 45 -> 30 frames, 1.0 s, x1.5; Death 109 -> 54 frames, 1.8 s, x2.02, so `Dead` holds the true last pose).
It marks retimed actions and skips them on a second run; `swap_body.py` rebuilds `work/rig_v5.blend` from the master,
so rerun it after a swap. Then `build_runtime.sh` and install. `actors.yml` PeasantM4 A/B/C: attack impact
0.628 -> 0.419 s. Frames: `review/fast_clips.png` (attack: full reach at 0.419 s; death: down by 1.0 s, still to 1.8 s).

## Gait rollout (2026-10-31, package h05)

New in-place locomotion clips appended to the installed `assets_source/worlds/mm6/models/mm6_natm.glb` (every existing
clip, mesh, skin and material unchanged): Walk2 (Mixamo Walk, 0.82 s, stride 1.80), Jog (humanoid set Unarmed-Run-Forward, 0.66 s, 2.90), Sprint (Unarmed-Sprint, 0.56 s, 4.11). Bindings for PeasantM4 A-C (applied by the rollout coordinator from
`../gait_rollout_20261031/h05/bindings.yml`): walking Walk2, stride_length 1.8, run Jog, run_stride_length 2.9, sprint Sprint, sprint_stride_length 4.11. Details, gates and doubts:
[package h05](../gait_rollout_20261031/h05/README.md). Rebuild: `../gait_rollout_20261031/h05/scripts/rebuild.sh natm`
from the pre-gait copy `work/mm6_natm_pre_gait.glb` there. A far-LOD repair (`lod_repair_claude`) or head-bob rerun on
this model must re-graft these clips (copy the repaired source over that pre-gait copy and rerun the rebuild).
