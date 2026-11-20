# MM9 goat (mm9_goat) — 3D model, 2026-10-30

The MM9 goat (`mm9/extracted/MODELS/MODELS/GOAT.abc`, 38 joints, 395 tris, 12 clips) for the MM9 world: Goat (row 268,
9268, skin GOAT), `goat.scr`, Hostility 2. Same route and scripts as `../mm9_cow_claude/` (read its README first):
a new HD Meshy mesh on the original MM9 skeleton, the MM9 clips played with only the listed fixes. Progress, hashes and
receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_goat.glb` (cooked copy in `assets_dev`), one material, no tiers |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_goat_claude`: `MM9 268 Goat`, scale 100 (MONSTERS.txt `Scale` 1) |
| Descriptor | NPC row in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 268 -> Unicorn A (109), the closest legacy horned hoofed quadruped |
| Triangles LOD0/1/2/3 | 7,934 / 3,966 / 1,428 / 476 (LOD0 skin 6,544, cavity 862, eyes and beard 528; horns and ears keep many: curved thin shapes) |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `XbackA/B/C`, `Xback`, `Xneckbase`, `Xneckpiv`, `Xneck`, `Xheadpiv`, `Xhead`, `Xjawpiv`, `Xjaw`, ears `Xearpiv-Xear(01)`, `Xfrontleg`, legs as the cow, tail `Xtailpiv-Xtail`) |
| Clips (30 fps) | Standing 1.5 (Stand), Walking 1.0 (Walk), Running 0.3 (Run), Fidget 2.5 (Fidget1), AttackMelee 0.67 (HAttack1), Hit 0.8 (Wince1), Death 1.9 (Die1), Dead 1.0 |
| Events | the butt lands at 0.288 s (MM9 `Rattack` of HAttack1); `goat.scr` butts whoever uses it, cast and ranged repeat it |
| Gait | stride 0.51 (walk), 1.2 (run) model units per cycle, from the hooves' planted speed |
| Floor | ground rule with low-passed shifts (`scripts/floor_smooth.py`); `floor_audit.py --world mm9` Goat ok |
| Meshy credits | **15** (backup account): Smart Topology 5, 4K retexture 10, no retries |

## Route (differences from the cow)

- **Body clean:** same solid grid (`scripts/solid_grid.py`, `finish_solid.py`): Meshy's inner layer covered 10 % here.
- **Symmetry:** the beard came off-centre; `symmetrize.py` moves a piece without a mirror partner onto the mid plane.
- **Mouth** (`scripts/mouth.py`, `MOUTH_A=-0.645,0.67 MOUTH_B=-0.565,0.688`): cavity of 4 rings, 862 tris, skinned between
  `Xhead` and `Xjaw`. The beard follows the jaw as in MM9.
- **Jaw on the keys** (`clips_mm9.py fix_jaw`, `rigcfg.JAW_FIX`): MM9's bind jaw hangs open of its idle: Stand chews 33-17 deg
  closed of the bind (Xjawpiv + Xjaw twist), the HD mouth is closed in the bind. `a' = soft_max(0, (a + 26) x 0.6)`: Stand
  chews 0-5.6 deg, HAttack1 reaches 17, Run 12-27 (MM9 lets the jaw hang in the run). Done on MM9's keys, so the
  curves stay as smooth as MM9's.
- **UVs:** the first layout reached 48 %; `max_cost=1.2 merge_below=8 head_factor=1.5` gave 60.2 %
  (`texturing/goat_body_upload_b.glb`, the one Meshy painted). `work/uv_v1a_48pct.blend` is the rejected one.
- **Coat relief:** Meshy embossed the coat with a pebbled wave (8-14 px at 2K, in the colour and the normal map) that read as
  a scaly hide up close. `compose_goat.py` damps that luminance band to 45 % (hue kept) and the coat's normal to 35 %.
- **Eyes:** Meshy painted the whole eye on the skin just in front of the eye piece, and an iris on the piece as well: two eyes
  side by side. The painted skin eye sits where the master has it, so `compose_goat.py` paints the piece in the skin's
  colour and it reads as a brow bump.
- **No tiers:** one MM9 skin, no region mask, `scripts/set_material_extras.py` sets specular 0 and metallic 0.
- **Weights:** `rigcfg.REFINE`, `LIMB_FADE`, `BELLY`, `TAIL_TUBE`, as the cow.

## Rebuild

As `../mm9_cow_claude/README.md` with: `mm9_rig_source.py ... 0 0.5065`, `finish_solid.py ... 0.0025 8 1`,
`POSE_SIGMA=0.08 HEAD_DIFFUSE=900` for `fit_quad.py`, `reduce_mod.py ... 6500 0.2`, `uv_atlas_v1.py ... max_cost=1.2
merge_below=8 head_factor=1.5`, `HEAD_GROUPS=Xheadpiv,Xhead,Xjawpiv,Xjaw,Xearpiv,Xear,Xearpiv01,Xear01
JAW_GROUPS=Xjawpiv,Xjaw`, `bake_ao.py ... 0.05 2048`, `compose_goat.py` (no MM9 dump, no ramps), and the viewer
from the export: `python3 scripts/make_viewer_manifest.py r2_goat_20261030 "goat=Goat=export/mm9_goat.glb"`.

## Checks (2026-10-30)

Sheets are review-viewer shots (the MM9 row of the comparison is a Blender render of the MM9 reference):
`review/sheet_mm9_vs_ours.png`, `review/sheet_angles_goat.png`, `review/sheet_texture_goat.png`.

| Gate | Result |
|---|---|
| Symmetry | MM9 mirror distance mean 2 mm, mid plane x = 3.5 mm; ours exact about it |
| Orientation | `scripts/head_gate.py` (`review/head_gate.json`), full head orientation vs MM9, max per clip: Standing 1.0, Walking 1.6, Running 4.2, Fidget 4.9, AttackMelee 8.2, Hit 7.4, Death 12.2 deg. Hooves 0-0.4 deg in Standing, Fidget, Hit; 4-16 in Walking, Running, AttackMelee, Death (mid-swing) |
| Head shape | goat proportions: long face, blunt lips, V horns, side ears, beard |
| Attachment | `detached_parts_audit.py` 0 detached in every clip |
| Folds | `scripts/fold_measure.py`, outside the head: worst frame Standing 0, Fidget 5, Walking 5, Death 9, Hit 10, Running 29, AttackMelee 30 |
| Shading | `flat_shading_check.py` flat 0.02 |
| Textures | `texture_quality.py`: atlas 60.2 %, spread 1.52 (the denser head, x1.5; body density p10/p50 1580/1640), fragments 0.2 %, stretch p90 1.09, 2K from a 4K paint |
| Deformation | `scripts/gates.py`: loop seams 0; edge ratio p1/p99 per clip 0.64-0.89 / 1.08-1.81 |
| Floor | `floor_audit.py --world mm9`: Goat ok |
| Viewer | `tools/run_creature_review.py check`: 1 model, 8 clips, 0 console errors; playback in `review/playback/` |
| Winding, regression | `check_winding.py` 0 inverted; `mm9_actor_models_build_every_binding` 65 descriptors on 31 models, 0 failed |

## Deviations and open points

- Solid-grid body clean instead of the wolf's voxel clean (see the cow).
- The jaw is re-based and scaled by 0.6 (above); the run's jaw is still loose, as in MM9.
- The coat is paler than MM9's skin (HD master choice). The eye is paint on the skin, with no eyeball of its own; a thin yellow rim of the old paint stays round the brow bump.
- Hooves are one piece with a painted cleft.
- Unused MM9 clips: Fidget2, RunAttack, Wince2, Die2. MM9 `Velocity` events are not reproduced (clips stay in place).
- The generator gives this row `Stationary / Aggress`; a wander/flee behaviour is not part of this model work.
- No in-game run: viewer, floor audit and regression only.
- User artistic acceptance: not recorded.
