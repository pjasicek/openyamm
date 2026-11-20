# Hesper Landfall Guard (`hes_guard`, ranks guard_a/b/c) reduction (2026-10-22)

User: "the villager, female male + guard are ok, you can run the tris reduction playbook on them". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the textures, region mask, rank ramps, rig,
clips, sockets and the rifle attachments stay as exported. No Meshy credits. **Exported 2026-10-22, not installed**
(Hesper is integrated by the Hesper stage; nothing in `assets_dev/` or `assets_source/`, `hes_guard_claude/`
untouched). Scripts copied from `mm7_m178_reduce_claude/` (ladder, UV weights, LODs, LOD check, close-ups, viewer,
`find_doubles.py`, `drift_lock.py`); the gates `gates.py`, `armik.py`, `cfg.py`, `rifle_up_check.py`,
`shrink_shadow_lods.py` from `../hes_guard_claude/scripts/`; `lodrep/` = the `lod_repair_claude/scripts/` far-LOD route
(unchanged copies) with `repair_glb.py` taking an explicit GLB.

Source: `../hes_guard_claude/export/hes_guard.glb` (sha256 `795e22be…`), copied to
`work/hes_guard_source_pre_reduce.glb` (rollback source); rifle and glow copied to `work/*_source_pre_reduce.glb`.
One node `HGD`, one material `HGD_A` (body + head sets merged, 2080x1024 atlas; body set u < 0.5) with variants
`HGD_B` / `HGD_C` (regions R coat, G tabard, B gold). The source LOD0 was already cut once by Blender Decimate
(`halve_lod0.py`, 10.7k -> 8,559) and its body atlas is very fragmented (transferred Meshy islands).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| approved export | 8,559 | 4,278 | 1,540 | 510 |
| **reduced** (`export/hes_guard.glb`) | **7,189** (-16 %) | 3,594 | 1,790 | 898 |
| rifle / glow attachments | 758 / 48 (unchanged) | | | |

LOD2/LOD3 and their shadows come from the `lod_repair_claude` route (own UVs and 512/256 px far textures, LOD2/3 at
25/12 % of LOD0, first ladder step passing: LOD2 outline 2.5 % / colour 13.5, LOD3 4.3 % / 13.5; the default-ratio
LOD3 of this build scored 6.6 % / 20.6). The rifle (a hand-built 758-triangle reference silhouette whose pistol grip and
handguard are fitted to both fists) is left unchanged: little to gain, and its fit is the user-reviewed part.

## Pieces and budgets (`make_groups.py`, masks `review/masks/`)

- **Kept exactly** (`work/keep_k.npy`, 4,277 faces): small pieces up to 90 faces (eyes, rivets, buckle, stud, tubes),
  the soles, the face front (951 head-set faces: brows, eyes, nose, mouth, chin, neck front), both rigid fists (the
  rifle's grip and handguard fits), the helmet, the rest of the head set (the scalp under the helmet poked through it
  at 45 %), the **coat skirt and tabard below the waist** (547: its gold hem and the white panel edges tore into
  zigzags even at 88 %), the **tabard front above the belt** (208: the gold glyph stem went wavy at 80 %) and 2.5 cm
  around six posed misses (`err_lock.py`).
- **Own ratios:** feet and boots 80 %, shoulder and knee plates 80 % (at 55 % their rims lost the crisp lower edge),
  pouches and holster 60 %, the rest of the torso shell (back, sides, chest plate) 80 %.
- **Rest (arms, legs):** the remaining budget (about 60 %).

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm)

| config | change | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| a | head 60, feet 65, helmet/plates 60, pouches 75 % | r80 | 6,845 | 4.56 / 26.2 | 0.993 | 0.991 | fail |
| d | + error lock, head 45, helmet 50, plates 55 % | r76 | 6,501 | 4.81 / 20.7 | 0.993 | 0.992 | pass; helmet rim and plate edges lost |
| e | helmet and plates 80 % | r78 | 6,675 | 4.77 / 23.9 | 0.994 | 0.992 | pass; skirt hem torn |
| h | head + helmet kept, skirt 88 %, upper torso 80 % | r84 | 7,185 | 4.58 / 23.9 | 0.994 | 0.992 | pass; hem still torn, glyph wavy |
| j | skirt + tabard front kept | r84 | 7,187 | 4.74 / 30.3 | 0.994 | 0.993 | fail (one thigh point in Death) |
| **k** | **j + error lock** | **r84** | **7,189** | **4.90 / 19.2** | **0.994** | **0.992** | **picked** |
| k | | r83 | 7,103 | 5.37 / 19.2 | 0.993 | 0.992 | fail |

Texture drift (`texture_drift.py r84`): 17 faces over 40, mostly thigh surfaces under the coat; nothing visible in the
flat textured close-ups. Close-ups: `review/flat/sheet_k_r84.png` (source | r84, flat textured: the reliable texture
check, see below), `review/glbclose/sheet_r84_a_tex.png`, `sheet_r84_a_clay.png`, `sheet_r84_bc_tex.png` (straight
from the viewer GLBs with the rifle; ranks B and C), rejected configs in `review/close/sheet_{d,e,f,h}*.png`,
`review/flat/sheet_i*.png`, LODs `review/lods/lod_sheet.png`.

**Eevee close-ups of `work/*.blend` show false colour bands** on parts kept exactly (the helmet's back): the welded
source's custom normals are cleared there and it shades differently. `flat_close.py` (workbench FLAT + texture)
compares the texture alone and showed the helmet identical; use it, or the GLB close-ups, for texture decisions.

Shading: the source GLB is split at every UV seam (faceted patches in clay views on this fragmented atlas); the
reduced mesh is welded and shades smooth (as the reduced MM7 models). Textured it reads the same.

## Build

`scripts/build_export.sh Cand_84` (with `work/ladder.blend` = `work/ladder_k.blend`): `export_cand.py` ->
`swap_lod0.py` (into the rollback source) -> `build_lods.py` (LOD1 at 50 %, 4 influences) -> `shrink_shadow_lods.py`
-> `carry_variants.py` -> `lodrep/repair_glb.py` (LOD2/LOD3 + shadows, `work/lodrep/result.json`) -> the corpse floor
fix below (pre-fix export `work/floor_fix_base/hes_guard.glb`). The rifle GLBs are
copied unchanged to `export/`.

## Gates (GLB gate copies of source and reduced, 30 fps import, the master's garment/piece labels: `scripts/gates.sh`)

| gate | source | reduced |
|---|---|---|
| arm stretch p99 (all clips) | <= 1.91 (Death L) | <= 2.20 (Death L, frame 48) |
| arm stretch max | 4.61 (Death L) | 4.61 (the same edges) |
| hands (rigid) / hand in body | 1.00 / 0 (Death free left hand 4 cm) | the same |
| robe (skirt chains) p99 / max | <= 1.66 / 1.89 | identical, except Death 1.71 / 2.05 after the floor fix (strips bent onto the floor; source 1.48 / 1.81) |
| rifle up axis (`rifle_up_check.py`) | aim 10°, carry <= 30°, roll 0°: PASS | the same (rig and clips unchanged) |
| soles Standing / Walking / Hit | -0.1 / -1.9..0.7 / -1.3 cm | -0.1 / -1.9..0.7 / -1.2 cm |
| LOD check: stretched faces, bounds | 0, 1.07 x 0.42 x 1.70 m | 0, the same at every LOD |
| winding (body, rifle, glow) | 0 | 0 |

The Death left-arm p99 rise is the same 9 edges over 2x in both meshes (one lying frame, flagged in the source
README); the reduced arm has fewer edges, so they are a larger share of them.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/hes_guard_reduce_claude/review/viewer/`: approved export (r100) and
the reduction (r84, default) for ranks A, B and C with the rifle joined for review (`add_rifle.py`).
`run_creature_review.py check`: 48 switches, no console errors.

## For the user to review

- 16 % off LOD0 (8,559 -> 7,189): this mesh was already cut once, and the painted gold trims on the fragmented atlas
  tear long before the geometry error shows, so the coat skirt, tabard, head, helmet and fists are exact.
- The corpse floated 35 cm above the floor in the approved export; fixed in both exports (section below).

## Install (not run)

Same file names, nodes, materials, variants, sockets and attachments as the source project, so
`integration/actors.yml` (= the source draft) applies unchanged. When the Hesper stage takes it:
`tools/install_model.py` on `export/hes_guard.glb`, `export/hes_guard_rifle.glb`, `export/hes_guard_rifle_glow.glb`
with the Hesper target (after `check_winding.py`). Rollback: `work/hes_guard_source_pre_reduce.glb`.

Reproduce: `find_doubles.py` (0), `import_source.py` (REA_GLB, REA_NODE=HGD), `dump_mesh.py`, `dump_faces.py`,
`dump_weights.py`, `SMALL=90 make_groups.py`, keep masks (`keep_err.npy` from `err_lock.py` on config b, + helmet,
head, skirt, `tabard_front.npy`, + `err_lock.py` on j -> `keep_k.npy`), `REA_WEIGHTS=component
REA_KEEP_FACES=work/keep_k.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=3:0.8,5:0.8,6:0.6,9:0.8 scripts/run_ladder.sh
k 0.86,0.85,0.84,0.83`, `flat_close.py`, `close_hes_guard.py`, `texture_drift.py`, `build_export.sh Cand_84`,
`gates.sh`, `lod_check.py` + `lod_views.py`, `viewer_tiers.py` + `add_rifle.py`, `viewer_manifest.py`, `glb_close.py`.

## Corpse floor fix (2026-10-22, coordinator follow-up)

**Cause.** In the engine's evaluation (`claude_shared/floor/glb_pose.py`) the approved export's Death ended, and Dead
held, the corpse with its lowest point at +0.349 m; the body itself lay 0.54 m up. The source project's
`death_floor.py` counted the rifle as a floor contact: it stays rigid in the right fist and points straight down at
the end of Mixamo "Death From The Front", so its tip stood on the floor and held the body up (`rig_v2t4` -> `rig_v2t5`
raised the corpse 33 cm). `floor_fix.py --ground-death` alone is not enough: it counts the coat skirt, whose Robe_*
chains hang straight down under the lying body and still held it 19 cm up.

**Fix (clips only; meshes, LODs, materials and variants unchanged):**
1. `scripts/ground_body.py`: root joint (B_Pelvis) moved as `--ground-death` does, measuring the body without the
   skirt (Robe_* weight <= 0.5): Dead -0.536 m, Death lowered toward it while above the floor and raised where it goes
   under, on a 1/120 s grid (root keys only at the clip keys dipped 3.5 cm at the kneeling impact, frame 42.5).
2. `claude_shared/floor/floor_fix.py --lift-joints Death Dead --lift-only 'Robe_*' --ground-death Death Dead`: the
   skirt strips bent onto the floor (15 strip joints); the strips left under it lift the corpse 2.8 cm (it lies on the
   coat).
3. `scripts/death_rifle_floor.py`: the Rifle joint eased from the fist onto the floor, lying on its side with the
   barrel level (from 1.05 s, as the held rifle reaches the floor while he kneels, over 0.4 s); RifleGlow and
   Socket_Muzzle follow it.

Result (glb_pose at 240 Hz and the Blender gate copy): Death lowest -0.4 cm, Dead 0.0 cm (body 2.8 cm up on the coat),
rifle +0.2 cm above the floor; every LOD's Dead lowest point 0.0 to +0.3 cm (`lod_check.py`). Gates rerun
(`work/gates_floor_run.log`): rifle up/roll PASS (Death is not judged), arm/hand/soles as before, Death body floor
-0.05 cm, robe Death p99 1.71 / max 2.05. Viewer check 48 switches, no console errors; `check_winding.py` 0.
Before/after: `review/floor/before_after.png` (`floor_view.py`, `floor_sheet.py`).
The same three steps were applied to `../hes_guard_claude/export/hes_guard.glb` (pre-fix copy in its
`work/floor_fix_base/`); the two exports' clips agree to 7 mm on the body joints (each mesh's own lowest point) and
5 cm on skirt strip tips (strips bent against each mesh's own skirt). The rollback source
`work/hes_guard_source_pre_reduce.glb` stays the approved, pre-fix file.

## Key-time gate and far-LOD mask fix (2026-10-22, follow-ups)

- **Key times.** The first floor-fixed export had two Death keys at 2.1 s on B_Pelvis translation (`ground_body.py`
  merged a 1/120 s grid time with a stored key that differed only below float32 precision), and the engine rejected
  the model ("keyframe times are not finite and strictly increasing"). `ground_body.py` now drops grid times within
  0.1 ms of a key, and `scripts/check_key_times.py <glb...>` (every sampler input finite and strictly increasing, as
  stored) runs at the end of `build_export.sh`: PASS on every export of the three reduce projects and of
  `hes_guard_claude/export/`.
- **Far-LOD region mask.** In game the villagers' LOD2/LOD3 were one hair-coloured figure (user report, Landfall):
  `lodrep/transfer_textures.py` (copied from `lod_repair_claude`) loaded and wrote the region mask as RGB, so the
  fourth region (hair, mask alpha) covered every far-LOD texel. It now keeps RGBA (fixed in `lod_repair_claude` too);
  the villager exports were rebuilt. The guard's ramps use two channels and were not affected.
- In-game check (Hesper stage, `hes_out1`, forced `debug.model_lod` 0-3, all nine skins):
  `review/ingame/lod_before_after.png` (and `guard_a_lod0123.png` in the guard project); the guard loads.
