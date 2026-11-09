# MM8 Fire Elemental (`mm8_m496`, Lesser / Fire / Greater Fire Elemental) reduction (2026-10-19)

User: "Pick these for next reduction batch" (m556, m632, m488, m608, m496; session openyamm-f6). This follows the
default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: UVs are kept, so the
baked body map stays valid. No Meshy credits. The model is the Air Elemental's sibling (same MPFB effect-body route),
so the scripts are copied from [mm8_m508_reduce_claude](../mm8_m508_reduce_claude/README.md), with `reduce_ladder.py`
from [mm8_m624_reduce_claude](../mm8_m624_reduce_claude/README.md) (parent before transform; the m508 copy still sets
`matrix_world` first).

Source: the installed `assets_source/worlds/mm8/models/mm8_m496.glb`, byte-identical (sha256 `23a27b80…`) to
`../mm8_m496_claude/export/mm8_m496.glb` (steady-left-hand follow-up, the build's last revision; appearance approval is
still pending there). The `assets_dev` runtime copy was cooked from it at the same time (20:13). It is copied to
`work/mm8_m496_source_pre_reduce.glb` (rollback source). Five skinned mesh nodes on one rig:

| node | material | LOD0 | LOD1-3 | |
|---|---|---:|---|---|
| Body | `FireElemental_Body` (opaque, unlit, baked colour/AO, 1040x1024 atlas) | 6,496 | 3,246 / 1,624 / 516 | **reduced** |
| Flame | `FireElemental_Flame` (blended, unlit, UV scroll) | 2,688 | 1,344 / 672 / 448 | unchanged |
| Ash | `FireElemental_Ash` | 54 | 54 / 26 / 26 | unchanged |
| Burst | `FireElemental_Burst` | 12 | 8 / 8 / 8 | unchanged |
| Tongues | `FireElemental_Burst` | 54 | 36 / 36 / 36 | unchanged |

The effect meshes depend on face order for draw order and on UV repeats for scroll speed (openyamm-b4's m508 note), so
they keep their LOD chains byte for byte. `scripts/effects_identical.py` checks the export: Flame, Ash, Burst and
Tongues (all four LODs), materials, clip lengths and the node names are identical; only the body atlas image and the
four eased arm channels of Fidget and Hit change.

## Keep sets and ladder (body)

Weld 8,662 -> 0 open edges (one closed surface, 3,254 vertices), no coincident vertices with other weights. Limits for
the 1.84 m figure: p99 5.5 mm, max 27.7 mm.

- **Eyes** (96 faces, the two ellipsoids mapped to the 16-pixel swatch at the atlas's left edge, u < 16/1040): kept.
- **Face** (`face_faces.py`, 756 Head faces in front of the skull's centre, down through the jaw): decimated on its own
  at 75 %. The body is unlit, so the baked brow, socket and jaw shading turns into facets under a uniform cut (as on
  the Air Elemental).
- **Dark spots of the head and neck** (`dark_keep.py`, 650 faces with the eyes): faces whose baked colour is near-black
  over half their interior (mouth corners, ear folds, eye sockets, the throat notch), plus one ring. Every collapse that
  moved one of their corners spread the black over a larger triangle; the throat notch doubled at 55 %. Keeping all
  1,532 such faces (soles, palms, shoulders too) pushed the cut elsewhere and failed (p99 7.25 mm at 55 %).

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| uniform, eyes kept | 70 % | 4,546 | 2.71 / 13.85 | 0.995 | pass |
| uniform, eyes kept | 55 % | 3,572 | 3.54 / 15.88 | 0.991 | pass, face blocky |
| uniform, eyes kept | 45 % | 2,922 | 4.36 / 16.62 | 0.988 | pass, face and hips faceted |
| face 75 %, eyes kept | 55 % | 3,570 | 3.93 / 15.88 | 0.990 | pass, throat notch doubled |
| face 75 %, all dark spots kept | 55 % | 3,570 | 7.25 / 27.29 | 0.981 | fail |
| face 75 %, head/neck dark spots kept | 50 % | 3,246 | 4.57 / 16.62 | 0.986 | pass |
| **face 75 %, head/neck dark spots kept** | **55 %** | **3,570** | 4.08 / 16.62 | 0.989 | **visual pick** |

Close-ups: `review/close/sheet_face.png`, `sheet_body.png` (uniform vs face-protected), `sheet_dark.png` (throat notch).
Texture drift at 55 % (face 75 %): 0 faces over 40 (the thin notch is below what the per-face check sees).

## Texture fixes in the shared body atlas

The installed model already shows black triangles that read as holes: the throat notch below the chin, ear folds,
between the fingers and on the toes. They are 22 source faces the bake left black while their neighbours are bright
skin (`fix_dark_faces.py`): their dark texels (UV triangle dilated by 2 px) take the neighbours' mean skin colour.
Deep sockets and creases with dark neighbours stay as baked. `pad_body.py` then fills the black gutters between the
~1,100 skin charts with the nearest island colour (527k -> 67k dark texels; texels under the source UVs unchanged, the
eye swatch untouched), so a UV corner on a chart border no longer samples black. All three tiers share the atlas.

## Build

`scripts/build.sh`: `export_cand.py` (Cand_55 of `work/ladder_f75h.blend`) -> `swap_lod0.py ... Body` (other nodes keep
their LOD meshes) -> `build_lods.py` (`tools/build_actor_lods.py`, ratios 0.5 / 0.25 / 0.145, 4 influences, the eyes'
front outline protected: 32 points; without it LOD2-3 eyes collapsed to triangles) -> `shadow_chain.py` (body shadow =
colour LOD1-3, as installed) -> `compact_glb.py` -> `fix_dark_faces.py` -> `pad_body.py` -> `fix_arm_boundaries.py`
(below) -> `effects_identical.py`, `check_winding.py` (0 inverted closed parts): `export/mm8_m496.glb`, 3.2 MB
(installed 4.2 MB).

| | Body LOD0 | LOD1 | LOD2 | LOD3 | all meshes, LOD0 |
|---|---:|---:|---:|---:|---:|
| installed | 6,496 | 3,246 | 1,624 | 516 | 9,304 |
| reduced | 3,570 | 1,784 | 892 | 516 | 6,378 (-31 %) |

Checks:
- `work/lod_check_{src,r55}.json`: every body LOD keeps the rest height (top 1.950 / 1.949 / 1.944 / 1.938 m against
  installed 1.950 / 1.950 / 1.947 / 1.936), no face stretches over 20x in any frame of any clip, lowest body point per
  clip as installed (7.5-8.3 cm; the figure floats).
- The creature's own effect-body gates (`audit_effect_body.py`, a copy of `../mm8_m496_claude/scripts/audit_export.py`
  taking the GLB as an argument; run in Blender for `mathutils`): 674 checks, 0 FAIL, installed 674 / 0
  (`work/gates_{src,r55}.json`). Closest to a limit: combined LOD3 ratio 0.162 (limit 0.17, installed 0.111) and the
  Cast arm stretch p99 1.886 (limit 2.0, installed 1.837).
- `review/glbclose/sheet_src_r55.png` (GLB-direct renders, effect meshes hidden: face, three-quarter, chest, back, hand;
  textured and clay) and `sheet_src_r55_fx.png` (whole figure with the flames, Death).
- `review/lods/sheet.png` (installed / reduced, LOD0-3: three-quarter, head, Attack, Dead ash), `sheet_head.png`.
  The reduced LOD3 shows two small flame pieces at the collar where the coarser neck sits inside the unchanged Flame
  LOD3 (installed LOD3 shows one at the shoulder).

## Clip scan (`anim_scan.py`, body bones at 48 frames per second, viewer frame = time x 48)

Attack and Cast start moving in the first frame (no dead start); Walking and Running have no height jump (largest
head step 1.9 / 2.4 mm per frame, loops closed); Death drops the head up to 43 mm per frame while collapsing into ash
(intended). The scan found one fault in the source clips, fixed below.

### Arm pops at the Fidget and Hit boundaries (fixed)

Fidget frames 1-2 and 114-115 and Hit frames 1-2 and 35: the fingertips moved 45-56 mm per frame against a median of
4 / 12 mm. The finger channels are constant; the cause is the arms. In `../mm8_m496_claude`'s composed clips the first
and last keys of LeftArm and RightArm are the Standing pose, but from the second key (and up to the second-to-last)
both arms sit 5.2 deg (Fidget) or 6.2 / 5.3 deg (Hit) away from it, so the whole hand jumps in one 30 Hz key. Both
arms do it equally, so the steady-left-hand follow-up is not the cause.

`scripts/fix_arm_boundaries.py` changes only those four channels (in place, same keys and times): Fidget eases the arm
offset in and out over eight keys (slerp from Standing, smoothstep weights); Hit's fast reaction eases from Standing
to its key-7 pose over the first seven keys (where the swing peaks) and out over the last five. The boundary keys stay
the Standing pose, so the loop and the transition to and from Standing are unchanged, and the keys between the ramps
are untouched (identical fingertip motion there). Largest arm step per key: Fidget 5.16 -> 1.40 deg, Hit 6.18 ->
3.73 deg; fingertip speed: Fidget 45 -> 11 mm per frame, Hit 56 -> 36 mm per frame (a smooth swing; the source swing
itself runs at about 31). Plot: `review/fingertip_speed.png` (`fingertip_speed.py`, `plot_fingertips.py`).
`effects_identical.py` confirms that only these four channels differ from the installed file (570 bytes of quaternion
data; clip lengths, every other channel of all nine clips and the effect meshes identical). The gates' 48 Hz rotation
step for Fidget's arms drops from 3.22 to 0.96 deg.

**A re-export from `../mm8_m496_claude/` brings these pops back**: run `fix_arm_boundaries.py` on that export again
(it is part of `scripts/build.sh`), or fix the composed Fidget and Hit arm keys in that project's `build_model.py`.

## Viewer

`review/viewer/` (revision `reduce-2`, with the arm fix; installed vs reduced for each tier under the production `NativeTierScale`
roots 1 / 1.346 / 1.538, built by `scripts/viewer_tiers.py` from the m496 project's page; sha256 and `?v=` rewritten,
manifest loaded with `cache: 'no-store'`; flames, ash and plumes as in the production viewer):
<http://127.0.0.1:8912/level_generation/creatures/mm8_m496_reduce_claude/review/viewer/>.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m496_reduce_claude check`: 54 model/clip
switches, no console errors.

## Status

Installed 2026-10-19 after user review ("fire elemental ok"), with the body-atlas repair and arm-boundary fix, via `tools/install_model.py --world mm8`; effect meshes byte-identical; actor regression `mm8_fire_elemental_actor_models_keep_native_sizes_cast_and_ash` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install (from the repository root): `python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py
level_generation/creatures/mm8_m496_reduce_claude/export/mm8_m496.glb`, then `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m496_reduce_claude/export/mm8_m496.glb`, then
`OPENYAMM_REGRESSION_FILTER=mm8_fire_elemental_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_fire_elemental_actor_models_keep_native_sizes_cast_and_ash`), and add the ledger row. `actors.yml` needs no change.
Rollback: `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m496_reduce_claude/work/mm8_m496_source_pre_reduce.glb`.

Reproduce: `REA_NODE=Body REA_GLB=<abs path of the rollback source> blender -b -P scripts/import_source.py` ->
`REA_PROTECT=Head blender -b -P scripts/dump_mesh.py` -> eye faces (`work/eye_faces.npy`: faces with u < 16/1040) ->
`face_faces.py 0 0` -> `work/basecolor.png` (the GLB's m496_body image) -> `dark_keep.py work/keep_dark.npy` ->
`REA_HEIGHT_M=1.844 REA_KEEP_FACES=work/keep_dark.npy REA_PROTECT_FACES=work/face_faces.npy REA_PROTECT_RATIO=0.75
scripts/run_ladder.sh f75h 0.60,0.55,0.50` -> `close_ladder.py`, `close_sheet.py` -> `scripts/build.sh` ->
`lod_check.py`, `lod_views.py`, `audit_effect_body.py`, `glb_close.py` (`GLB_HIDE=Flame,Ash,Burst,Tongues`),
`anim_scan.py`, `fingertip_speed.py -- before=work/r55_pre_armfix.glb,after=export/mm8_m496.glb`, `plot_fingertips.py`,
`VIEWER_REVISION=reduce-2 viewer_tiers.py work/mm8_m496_source_pre_reduce.glb r100 export/mm8_m496.glb r55`.

## Floor fix — 2026-10-21

`--hover -0.056103 Death Dead`: the lowest living point was 0.056 m above the floor; every living clip is lowered so it meets it (Flying still rises as authored), eased out over Death without taking any key under the floor. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m496.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
