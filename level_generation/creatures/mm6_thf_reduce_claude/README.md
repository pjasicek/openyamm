# MM6 Thief (`thf`, BThief A/B/C) reduction, retexture, new daggers and clips (installed 2026-10-14)

User: "after that do thief". RETOPOLOGY_PLAYBOOK.md default route, no-rebuild branch, no Meshy. Source: the installed
`assets_source/worlds/mm6/models/mm6_thf.glb` (9,506 tris, one texture set, cloak chains, two daggers in the skinned
mesh shown only in the attack).

## Ladder

A uniform ladder fails every step (`../reduce_installed.sh thf Thief "MM6 Thief"`; max error 42+ mm already at r70).
`scripts/decimate_tex.py` carries the Merchant's `REA_HEAD_RATIO` (head faces, `Head`-dominated, 2,439, decimated
separately). Picked visually: **head 70 %, rest 45 %: 4,886 tris** (head 1,707).

Checked and rejected on the way (`work/viewer_trials/`):
- head kept, rest at the same body budget (5,608) and head + neck + headfront kept (5,892): the pale cheek/jaw patches
  in the face close-ups did not go away. They are painted in the source texture and Blender's EEVEE renders the same
  file with them faint or bright from run to run (`review/face/sheet_noise.png`: two renders of the installed model and
  of one candidate), so they were never a reduction fault.
- the source's custom normals transferred onto the candidate: no change to the patches, dark faults on the hood; reverted.

Daggers: hidden in Standing and present in Attack at every step (weights transfer kept them on DaggerL/DaggerR).

## Result

`export/mm6_thf.glb`: LODs **4,886 / 2,441 / 873 / 283** (installed 9,506 / 4,750 / 1,704 / 563). Texture, variants
(carried to every LOD/shadow primitive), clips and sockets unchanged; no collapsed meshes. Review:
`review/face/sheet.png` (faces), `review/pose/sheet_pick.png` (Standing, Attack, Walking, Death, Hit; installed vs
pick), viewer `review/viewer/` (installed vs pick, A/B/C, all clips): `check_viewer.mjs` 48 loads, no errors.

## Animation changes (user 2026-10-14)

"attack anim should use the body/legs at least a bit, not be totally stationary; hit - use better anim; death - speed
up 2x". Made in the authoring project (`../mm6_thf_claude/`, scripts and work blends; the previous ones are in
`work/pre_anim_20261014/` there), then the accepted reduced LOD0 (`work/cand_export.glb`) swapped into the rebuilt
export: `export/mm6_thf_anim.glb` (LODs 4,886 / 2,441 / 873 / 283, shadow LODs tucked in by `shrink_shadow_lods.py`,
variants carried).
- Attack (`attack_thf.py`): a lunge. The right foot steps 20 cm forward on the first thrust and back at the end (leg
  IK, flat feet), the hips drive forward and down into each thrust (up to 15 / 7 cm), the chest leans further (13 deg);
  the wrist targets ride the hip travel, so the dagger grip and aim are solved as before. Trace gate passes.
- Hit (`build_clips_thf.py` + new `retarget_hit.py`): Mixamo Medium Hit To Head, retargeted relative to its first frame
  onto Standing (world rotation change per bone, hips travel by the leg ratio), resampled into 0.75 s, settled into
  Standing over the last 5 frames. Chosen from four Mixamo and four stored Meshy hits (strips on the thief). Trace gate
  passes.
- Death: twice the source speed (2.2 s -> 1.125 s); Dead unchanged.
- Cloak re-simulated for every clip (`cloak_sim.py`); the head split restored (`apply_head_split.py`).
Review: `review/clips/sheet_{Attack,Hit,Death}.png` (installed vs new, side and front). The viewer now takes per-model
clip durations (`review.js` `dur()`, manifest `models[].durations`): 48 loads, no errors.

## Retexture (user 2026-10-14: "retexture the body; split one texture cloak (+ hood), another the rest")

`scripts/build_master_tex.py` (reduced Cand_45 in the rig_v3 master with the new clips; face labels from the nearest
source face), `compose_tex.py`, `export_tex.py`, `build_tex_runtime.sh` -> `export/mm6_thf_tex.glb`. Three materials:
- **ThiefCloak_A** (cloak, mantle, hood and insides, 1,588 faces): fresh UVs cut along the source's uv_region borders,
  Meshy `cloak_texture` (10 credits, UV parity exact), 1K maps; luminance matched to the installed cloak cloth so the
  installed ramps recolour it per tier.
- **Thief_A** (body): three Meshy body retextures (`body_texture` body-only upload; `body_texture_v2` with a weighted
  layout: part weights + visibility, crushed closed shells re-unwrapped; `body_texture_v3` with the whole thief in the
  upload) all smeared the belt and the lower jerkin (pouch/sheath occlusion) and painted the shirt olive (30 credits;
  results in `meshy/`, `meshy_v1/`). User choice: keep the installed body texture and UVs (`BODY_UVS`/`BODY_SOURCE =
  'installed'`). Its tier mask is extended (hue 60-200 shirt texels, the sleeve regions whole, padded into the
  gutters): the installed mask left jade crease zigzags on the sleeves in tiers B/C (`review/tex/sleeve_cmp.png`).
- **ThiefHead_A** (face and hair): the installed head set, cropped from the installed atlas (`head_from_atlas.py`).
Three draws per thief (the cloak is a third material; merge_head_material.py handles one head only). Meshy 40 credits.
Review: `review/tex/final_sheet.png` (A/B/C now vs new: front, three-quarter, back, torso, chest, legs). Viewer
`review/viewer/` (installed vs final, all clips): `check_viewer.mjs` 48 loads, no errors.

## Review fixes (user 2026-10-14: "knives - why are they green, body armor - why are there holes?"; "the daggers could
## look more sharp and overall better, with the tris count in mind")

- **Green daggers:** the extended cloth mask had been padded into the gutters, over the dagger swatches, so the tier
  ramps recoloured the blades. The rebuilt daggers have their own column, with the mask zeroed there.
- **Daggers rebuilt** (`scripts/dagger_mesh.py`, on the same seat and bones): blade with an eight-sided section
  (cutting edge, bevel, flat, central ridge), a slight leaf profile and a needle point, flat-shaded; quillons that
  thin and curve; a swelling hexagonal grip; a faceted pommel. 126 triangles each (the reduced originals had 82). A
  painted column at the right of the body image (`compose_tex.paint_daggers`): brushed steel with a bright edge and
  ridge, wrapped leather grip, dark iron guard. The body image is squeezed into u < 0.92 for it (`installed_col`).
- **Holes in the jerkin** had two causes:
  1. The 45 % cut made big triangles straddle the leather/shirt border. The body is now taken from a gentler ladder
     that protects Spine/Hips (`REA_PROTECT='Head,neck,Spine,Hips'`, head 70 %, rest 45 %). The cloak keeps the
     reduction its Meshy texture belongs to (`CLOAK_FROM = work/ladder_r45_h70.blend`; its UVs are taken exactly from
     the upload, parity 0).
  2. Inner layers poked through after the reduction, and the double-sided material showed their backs. Never-seen
     inner faces (source visibility >= 0.95, 212) are removed, plus torso/skirt faces whose back is seen unobstructed
     from a viewpoint around the creature, level to 55 deg above (73; sleeves excluded: they are single shells).
  Tried and dropped: re-taking the body UVs per face from the full-detail mesh (stretched corners) and baking the
  installed maps onto a fresh layout (`bake_body.py`: the layered jerkin/shirt skirt and the radial skirt chart
  blurred the lower jerkin).
- Result: LODs **4,991 / 2,495 / 894 / 288**. Review: `review/tex/final_sheet.png` (A/B/C), `daggers_sheet.png`,
  `jerkin_cmp.png`, `sleeve_close.png`, `review/clips/sheet_*.png`. Viewer: 48 loads, no errors.

## Installed

User accepted (2026-10-14). `export/mm6_thf_tex.glb` installed as `mm6_thf.glb` with `tools/install_model.py` (runtime
back-face pass: 907 back copies); previous source in `work/mm6_thf_source_pre_reduce.glb`.
`mm6_thief_actor_model_tiers_share_the_native_height` passes. Three materials (body, cloak, head): three draws per
thief. Ledger row added.

## Gait rollout (2026-10-31)

Package h01 of the [gait rollout](../gait_rollout_20261031/README.md) appended `Walk2` (Mixamo Walk, 0.78 s, stride
1.5152), `Jog` (humanoid set Unarmed-Run-Forward, 0.64 s, 2.8184) and `Sprint` (Unarmed-Sprint, 0.52 s, 3.4402) to the
installed `mm6_thf.glb`, with the 17 cloak chains simulated over each (`h01/scripts/cloak.py`, a numpy port of
`../mm6_thf_claude/scripts/cloak_sim.py`). Existing clips untouched; bindings for the coordinator in
`../gait_rollout_20261031/h01/bindings.yml` (walking `Walk2`, run `Jog`, sprint `Sprint`). Details, gates and doubts:
[h01 README](../gait_rollout_20261031/h01/README.md). Rebuild: `../gait_rollout_20261031/h01/scripts/rebuild.sh thf`.
Any later rebuild of this source (far-LOD repair rerun, re-export) must re-graft these clips: copy the new source over
`h01/work/mm6_thf_pre_gait.glb` and rerun that command, then install its export.
