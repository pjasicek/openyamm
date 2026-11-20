# MM8 Smuggler, human form (`m444`: Animalist, Shapeshifter, Lycanthrope) reduction (2026-10-19)

User: "OK do those 5" (third MM8 batch: Lizardman Warrior, Vampire, Smuggler, Gog, Cleric). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) with its MM8 batch lessons. No retexture and no Meshy credits;
two local texture fixes (cloth region mask, facial-hair colour after user review). Not installed; awaiting user review.

Sources: the installed `assets_source/worlds/mm8/models/mm8_m444.glb` and `mm8_m444_sword.glb`, byte-identical to
`mm8_m444_claude/export/`, copied to `work/mm8_m444_source_pre_reduce.glb` and
`work/mm8_m444_sword_source_pre_reduce.glb` (rollback sources). Body: node `Smuggler`, one shared texture set
(2080x1024 atlas, body left, head image from x = 1056) with three tier materials over `KHR_materials_variants`,
region mask channel R (cloth), 57 joints, up to 8 influences, nine clips, `Sword` joint.

Scripts come from `mm8_m620_reduce_claude/` (parent-transform fix, exact source weights, close-ups, viewer tiers),
with `reduce_ladder.py`, `uv_weights.py` and `dump_weights.py` from `mm8_m592_reduce_claude/` (UV-based weights),
`err_lock.py` and `spot_lock.py` from `mm8_m464_reduce_claude/`, and `mask_fix.py`/`swap_mask.py` after the Ether Knight.
New here: `make_groups.py` (material-class regions), `seam_keep.py`, `colour_slivers.py`, `merge_sword.py`,
`viewer_views.py`, `normal_audit.py`.

## Sword: not reduced

The sword is 144 triangles at LOD0 (LOD1-3: 50 / 14 / 6), already lean; a cut would save under 1 % of the
character and risk the fitted grip. It stays the installed file unchanged and is not part of the install.

## Regions (`make_groups.py`)

Weld 6,210 -> 444 open edges; no coincident vertices with other weights. 35 pieces: the head (3,402 faces: face,
bald scalp, beard, ears, neck), torso 1,000, two arms with hands (900 each), legs 750, boots (400 each), the two eye
pieces (163 / 162), two mouth pieces (86 / 40), cuffs, sheath, bandolier pouches and buckles. Material classes come
from the production class maps (`mm8_m444_claude/textures/*material_classes.png`).

| label | faces (not kept) | picked ratio |
|---|---:|---|
| 1 head piece | 2,879 | 42 % |
| 3 left hand, 4 right hand | 877 / 877 | kept exactly |
| 0 rest (tunic, trousers, boots, bandolier, sheath) | 3,971 | remaining budget |

Kept exactly (`work/keep_e.npy`, 3,226 faces):
- the eye and mouth pieces, and the head faces within 8 mm of them (lids, lips; 523);
- body faces with metal texels (buckles, studs; 181);
- pieces of up to 40 faces, and the soles (below 1.5 cm);
- the right (sword) hand and fingers: the fitted grip;
- the left hand: its texture already has thin orange lines along its many chart borders (649 of its 877 faces touch
  one), and every collapse there widened them into streaks (`review/close/sheet_upper.png`, lhand, ladders d/e);
- faces within 2 cm of 14 source vertices the r68 candidate missed by over 14 mm (`err_lock.py`: the upper back under
  the bandolier and collar in Hit/Attack/Cast, max 39 mm), and a 2.5 cm spot below the left collar where a
  bandolier-brown wedge appeared on the tunic (`spot_lock.py`).

## Ladder (limits for the 1.70 m height: p99 5.1 mm, max 25.5 mm; UV-based weights from b on)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: head 60, left hand 50, nearest-face weights | 72 % | 7,252 | 4.36 / 33.8 | 0.990 | 0.995 | fail (max: upper back) |
| b: as a, UV weights | 72 % | 7,252 | 4.11 / 33.1 | 0.991 | 0.996 | fail (max) |
| c: b + error lock | 72 / 68 % | 7,252 / 6,848 | 4.10 / 12.7, 5.12 / 19.6 | 0.991 / 0.988 | 0.996 / 0.993 | pass / fail (p99) |
| d: head 50, left hand 50 | 70 / 68 / 66 % | 7,050 / 6,848 / 6,646 | 3.93, 4.48, 4.88 / max 19.6 | 0.989-0.992 | 0.994-0.996 | pass; left-hand streaks, collar wedge |
| e: head 45, left hand 45 | 66 / 64 % | 6,646 / 6,444 | 4.54, 4.93 / 19.6 | 0.990 / 0.988 | 0.995 / 0.994 | pass; same faults, trouser fleck at 64 |
| f: hands kept, collar spot, head 50 | 72 / 70 / 68 % | 7,252 / 7,050 / 6,850 | 4.50, 4.90, 5.70 | 0.991-0.987 | 0.995-0.993 | 68 fails; 70 has white flecks on the shoulder and back |
| **g: hands kept, collar spot, head 42** | **70 %** | **7,050** | **4.52 / 12.9** | **0.991** | **0.995** | **picked** |
| g | 68 % | 6,848 | 4.91 / 19.6 | 0.989 | 0.994 | pass; orange fleck on the right trouser front |

- **The body sets the floor.** With both hands kept (1,754 faces), the tunic, trousers and boots take the cut;
  below 70 % they start showing flecks of a neighbouring chart (a trouser fleck at g68 and e64, white flecks at f70).
- **The head goes to 42 %** with eyes, lids, mouth and lips kept. The face reads the same in texture
  (`review/close/sheet_fg_head.png`). The beard loses some lock relief and the ear folds soften in clay, while the
  beard texture carries the detail.
- **Texture drift** (`texture_drift.py r70`): 32 of 7,050 faces over 40, on the boot laces and the scalp stubble;
  close-ups match (`review/close/sheet_g70_boots.png`, `sheet_fg_head.png`).
- **Close-ups** (source and candidates, tier A): `review/close/sheet_head.png`, `sheet_upper.png`, `sheet_body.png`
  (ladders d/e), `sheet_fg_head.png`, `sheet_fg_body.png` (f/g).

## Normals

`normal_audit.py` compares each GLB's own LOD0 normals with plain smooth ones: installed head 3.5 deg median (p90 14),
body 4.1 (p90 25), with 13 hard-split vertices on the soles; the reduction 4.6 / 4.3. Unlike the Bedraggled Human,
this head carries no sharper custom shading, so the reduction keeps plain smooth normals. Clay renders straight from
the GLBs match (`review/glbclose/sheet.png`: head front and side, sword hand, torso).

## Build

`export_cand.py` (Cand_70 of `work/ladder_g.blend`, REA_NODE=Smuggler, REA_INFLUENCES=8) -> `swap_lod0.py` ->
`REA_LOD_RATIOS=.5,.22,.085 build_lods.py` -> `carry_variants.py` -> `mask_fix.py` + `swap_mask.py` ->
`head_posmap.py`, `head_hair.py work/basecolor.png work/basecolor_hair.png` + `swap_basecolor.py`:
`export/mm8_m444.glb`, 7.8 MB (installed 8.3 MB).

Ratios: the installed build's 0.5 / 0.18 / 0.06 gave a 401-triangle LOD3 with a pointed skull and no boot laces from
the smaller LOD0; 0.22 / 0.085 keep LOD2/LOD3 close to the installed counts (`review/lods/sheet.png`, installed top).
Protected points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame and within 5 mm of each bounding
extreme (152 points).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,074 | 5,056 | 1,817 | 584 |
| reduced | **7,050** | 3,523 | 1,548 | 579 |
| sword (unchanged) | 144 | 50 | 14 | 6 |

Checks:
- **`lod_check.py`** (REA_NODE=Smuggler, `work/lod_check_final.json`): every LOD keeps the 1.70 m height and the
  1.05 m span. The lowest point of every clip at every LOD equals the source LOD0's (Death -1.5 mm, Walking -1.4 mm).
  The installed LOD2/LOD3 floated 7-16 mm in Attack/Cast/Fidget/Hit and dipped -5.3 mm in Death.
- **Stretched faces:** none at any LOD (the installed LOD2 has 3 in Cast).
- **`check_winding.py`:** 0 inverted closed parts.
- **Unchanged:** the nine clips, metal-rough and normal images, the three palette variants on all eight
  colour/shadow meshes, the `Sword` joint and the hand sockets. The base colour (head half) and the region mask
  change only as described below.

## Retexture check: two local fixes

- **Skin:** head and hands match (linear luminance median 0.310 face, 0.305 hands); no unify step.
- **Cloth mask spill (in the installed model too):** tiers B and C showed green-teal at the collar beside the
  bandolier and along the collar's lower edge. Surfaces painted cloth green under the cuffs, the belt and the trouser
  hems also lay outside the cloth channel. `mask_fix.py` adds the cloth-green texels to channel R. It covers the
  146 faces whose samples are over 20 % unmasked green (dilated 2 px), plus green texels within 4 px of the masked
  cloth: 9,845 texels. `swap_mask.py` replaces only that image. `review/glbclose/sheet_maskfix.png` (tiers A/B/C,
  installed vs fixed): the collar is blue/burgundy now, and tier A is unchanged.
- **Facial hair vs beard (user review: "his head facial hair color and beard dont agree"; in the installed model
  too, same texture):** the beard mesh is ginger brown (linear 0.165/0.065/0.014, luminance 0.08). The head texture
  painted the moustache, cheek/chin stubble, sideburns and the short side/back scalp hair as pale skin-tone strands
  (luminance 0.31), so they read as two people. `head_hair.py` recolours only the head half of the atlas:
  - hair texels come from their strand texture: local RMS of fine luminance detail, which is high in painted hair
    and low on smooth skin (bald crown, forehead, ears and cheeks stay skin);
  - rest positions per texel (`head_posmap.py`) add three zones. Skin within 1.2 cm of the beard mesh gets full
    weight, so the chin and jaw meet the beard without a seam. The moustache follows a soft drooping arc over the
    mouth. Hair fades out down the back of the neck below the nape. Pale patches painted on the beard itself also
    take the beard colour;
  - each hair texel moves 90 % towards the beard colour at its own strand detail (luminance over the local mean);
  - the mask is feathered 3 px into skin and kept off the eyes, mouth, cloth and the region mask. The ramps only
    recolour the collar, so tiers B and C follow tier A. Atlas gutters take their nearest chart texel's weight.
  - The eyebrows are a darker brown and are left as they are; they read as natural next to the ginger hair. The
    thin red marks at the cheek and the nose bridge are chart-border lines in the installed texture; they are not
    from this fix.
  - Only the base-colour buffer view changes (every other view and the GLB JSON are byte-identical).
  - Textured face close-ups (front, three-quarter, side, back) for every tier, installed vs fixed:
    `review/face/sheet_facial_hair.png`.
  - The optional head-ratio raise to 60 % was not needed: in those textured close-ups the beard and ears of the 42 %
    head match the installed ones.
- **Verdict:** no retexture for head or body. Earlier exports: `work/mm8_m444_r70_pre_maskfix.glb` (before both fixes),
  `work/mm8_m444_r70_pre_hair.glb` (mask fix only).

## Review

Viewer `review/viewer/` (installed vs reduced for each tier, the tiers baked by `viewer_variants.py`, the sword merged
on the `Sword` joint by `merge_sword.py`; `review/viewer_views/sheet.png` checks the grip at rest and at the attack
impact), opening on tier A reduced:
http://127.0.0.1:8912/level_generation/creatures/mm8_m444_reduce_claude/review/viewer/.
Its `review.js` (from `mm8_m444_claude`) picks native palettes by the first six id characters.
`tools/run_creature_review.py ... check` after the facial-hair fix: 54 clip switches, no console errors.

## Cast retime (user review, 2026-10-19)

User: "cast - first 45 frames do nothing, should be like imo blended the sequence and not have dead spots?"
The source Cast (2.0 s, keys at 30 Hz, upper body only) stands still for 0.93 s (viewer frame 45 at 48 fps). It then
gathers in 0.17 s, thrusts the left palm through the release (actors.yml `cast` impact 1.1167 s), holds with a slow
drift from 1.2 to 1.7 s, snaps back to guard in 0.23 s and stands still from 1.93 s.

`scripts/retime_cast.py` rewrites only the Cast output values at the existing key times, using a monotone time warp
(PCHIP, new -> source):

| new (s) | source (s) | |
|---|---|---|
| 0.00-0.10 | 0.00-0.93 | the still start, so the first pose is kept exactly |
| 0.10-1.1167 | 0.93-1.1167 | the gather at about 1/6 speed; the arms start moving by frame 10 |
| 1.1167-1.20 | same | the thrust through the release, at source speed |
| 1.20-1.45 | 1.20-1.68 | the hold drift, shortened |
| 1.45-2.00 | 1.68-2.00 | the return to guard at about half speed |

Slowed down, linear interpolation between keys shows every key as a speed jolt, so linear channels are sampled
through a modified-Akima spline over the source keys (as in `mm8_m604_reduce_claude`).

What it keeps:
- the release time and the clip length (`actors.yml` unchanged);
- the first and last poses (within 0.04 deg);
- every other clip, byte-identical.

Speeds:
- the gather runs at 20-170 deg/s per bone group from frame 5 on;
- the return peaks at 394 deg/s, against 739;
- the thrust is unchanged, peaking at 2,376 deg/s at 1.167 s.

`review/cast/strip_every6.png` shows every sixth viewer frame, before above retimed. The previous export is kept at
`work/mm8_m444_r70_pre_cast.glb`. The viewer adds a "Cast retimed" row per tier (`*_r70c.glb`, the r70 viewer files
through `retime_cast.py`) and opens on it in Cast. Check: 81 switches, no console errors. `check_winding.py`: 0
inverted closed parts.

## Status

Installed 2026-10-19 (user: "smuggler OK"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_smuggler_human ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_smuggler_human_actor_models_keep_tiers_roles_and_palm_cast` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m444_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Smuggler, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py`
-> `dump_weights.py` -> `make_groups.py` -> ladder c's Cand_68 for `REA_CAND=Cand_68 REA_ERR_MM=14 REA_LOCK_R=0.02
err_lock.py -- work/keep_base.npy work/keep_c.npy` -> keep_d = keep_c + label 3 -> `spot_lock.py work/keep_d.npy
work/keep_e.npy 0.025 0.118,-0.02,1.41` -> `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_e.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.42 run_ladder.sh g 0.70,0.68` -> close-ups (`close_human.py`, `CLOSE_TAG=g`), `texture_drift.py
r70`, `colour_slivers.py`, `dark_slivers.py` -> build as above -> `lod_check.py`, `lod_views.py`, `glb_close.py`,
`viewer_variants.py` (body and sword) + `merge_sword.py`, `viewer_views.py`, `face_views.py`.

## Surface detail (user review 2026-10-19)

User: "looks like he doesnt have any texture, its like solid color blobs ... liek no normals". Meshy's body retexture
was nearly flat at the source (colour detail 6.3, normal tilt 1.8 degrees), unlike the HD master's woven tunic,
embossed cloth and tooled leather. `scripts/bake_ao.py` bakes rest-pose AO (5 cm) of LOD0 into the atlas layout
(`work/ao_atlas.png`); `scripts/detail_pass.py work/mm8_m444_pre_detail.glb work/ao_atlas.png export/mm8_m444.glb`
then adds, on the body half only: the HD master's tunic, cloth and leather swatches (high-pass, seamless, sampled
triplanar by rest-pose position at the master's 835 px/m), the same pattern as normal-map relief, and the AO (lighter
on leather and skin). Classes: the production class map keeps skin and metal out; fabric and leather by colour. The
head set, UVs, geometry, mask and roughness are unchanged; the tier ramps recolour the patterned cloth from its
luminance, so B and C carry the detail (offline tier renders with `claude_shared/tier_textures.py`). Winding 0; the
Smuggler regression passes. Accepted by the user and installed (2026-10-19: "OK this is good") with the new sword (`../mm8_m444_claude/README.md`). Rollback: install
`work/mm8_m444_pre_detail.glb` with `--name mm8_m444.glb`. Known and unchanged: the region mask also covers the belt,
which takes the tier colour.


## Gait rollout (2026-10-31)

Package [h21](../gait_rollout_20261031/h21/README.md) appended new in-place locomotion clips to the installed source
`assets_source/worlds/mm8/models/mm8_m444.glb` (existing clips, meshes, skins and materials byte-identical): `Walk2` (Mixamo Walk, 0.86 s, stride 1.9284), `Jog` (Unarmed-Run-Forward, 0.70 s, 3.4034) and `Sprint` (Unarmed-Sprint, 0.58 s, 4.5328); bound as walking / run / sprint (the installed `Walking` and `Running` stay in the GLB, unbound for locomotion).
Bindings are in `../gait_rollout_20261031/h21/bindings.yml` (applied by the rollout coordinator). Rebuild:
`level_generation/creatures/gait_rollout_20261031/h21/scripts/rebuild.sh m444` (from `h21/work/mm8_m444_pre_gait.glb`,
the pre-gait source), then `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h21/export/mm8_m444.glb --world mm8 --name mm8_m444.glb`. A far-LOD repair,
head-bob or reduction rerun on this model must re-graft these clips: copy its new source over the pre-gait copy and
rerun the rebuild (or graft them with `claude_shared/graft_clips.py`).
