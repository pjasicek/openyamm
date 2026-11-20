# Hesper Landfall villager, male (`hes_hvm`, outfits vm_a/b/c) reduction (2026-10-22)

User: "the villager, female male + guard are ok, you can run the tris reduction playbook on them". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: textures, region mask, outfit ramps, rig and
clips stay as exported. No Meshy credits. **Exported 2026-10-22, not installed** (Hesper is integrated by the Hesper
stage; nothing in `assets_dev/` or `assets_source/`, `hes_villager_m_claude/` untouched). Scripts as in
[`../hes_guard_reduce_claude/`](../hes_guard_reduce_claude/README.md) (m178 ladder chain, `flat_close.py`,
`gate_labels.py`, `lodrep/`); `export_cand.py` restores two-sided faces (`REA_DOUBLES`, from `mm6_hrp_reduce_claude`);
the gates `g4_weights.py`, `g5_hand_stretch.py`, `g6_contacts.py`, `sole_probe.py` are copies from
`../hes_villager_m_claude/scripts/`.

Source: `../hes_villager_m_claude/export/hes_hvm.glb` (sha256 `4912a205…`), copied to
`work/hes_hvm_source_pre_reduce.glb` (rollback source). One node `HVM`, material `HVM_A` (body + head sets in a
2080x1024 atlas) with variants `HVM_B` / `HVM_C` (regions coat, panel, collar, hair). Two two-sided hair-card faces
(`find_doubles.py`), restored on export. Its UVs are Meshy's own on the already reduced mesh, so texture drift stays low.

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| approved export | 9,452 | 4,721 | 1,687 | 553 |
| **reduced** (`export/hes_hvm.glb`) | **7,064** (-25 %) | 3,526 | 1,758 | 866 |

LOD2/LOD3 + shadows by the `lod_repair_claude` route at 25/12 % (LOD2 outline 3.3 % / colour 14.3, LOD3 4.9 % /
11.5; the default-ratio LOD3 scored 8.2 % / 21.6).

## Pieces and budgets (`make_groups.py` with FRONT_Y=0.0 FRONT_ZMIN=1.47, masks `review/masks/`)

- **Kept exactly** (`work/keep_d.npy`, 2,164 faces): the eyes, pin, clasps and buttons (body-set pieces up to 90 faces)
  and the coat within 1.5 cm of them (`keep_near.py`), the soles, the face front (936 faces: cheeks to chin) and
  2.5 cm around 14 posed misses (`err_lock.py`).
- **Own ratios:** head outside the face (scalp under the hair, ears, neck) 60 %, hands 55 %, shoes 70 %, hair cards
  75 %, pouch 70 %, trousers 60 %.
- **Rest (the coat):** the remaining budget (about 72 %).

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm)

| config | change | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| a | coat and trousers share the remainder | r76 | 7,346 | 3.58 / 22.3 | 0.995 | 0.995 | pass |
| a | | r72 | 6,968 | 4.47 / 26.9 | 0.992 | 0.991 | fail |
| b | coat 80 %, clasp surroundings kept | r77 | 7,440 | 3.36 / 20.5 | 0.996 | 0.995 | trousers took the whole cut |
| c | coat takes the remainder, trousers 60 % | r73 | 7,062 | 4.69 / 28.9 | 0.992 | 0.993 | fail (calf in Death) |
| **d** | **c + error lock** | **r73** | **7,062** | **4.98 / 20.3** | **0.992** | **0.992** | **picked** |
| d | | r71 | 6,872 | 5.47 / 20.0 | 0.991 | 0.990 | fail |

Texture drift (`texture_drift.py r73`): 7 faces over 40 (93.5 cm²), not visible. Close-ups: `review/flat/sheet_d.png`
and `sheet_d_pin.png` (flat textured, rest pose: pin, clasps, cuff, collar), `review/close/sheet_d_clay.png`,
`review/glbclose/sheet_r73_a_tex.png`, `sheet_r73_a_clay.png`, `sheet_r73_bc_tex.png` (outfits B and C), LODs
`review/lods/lod_sheet.png`. No feature changed; the fingers are slightly simpler in clay views.

## Build

`scripts/build_export.sh Cand_73` (with `work/ladder.blend` = `work/ladder_d.blend`): `export_cand.py` (2 reversed
faces restored) -> `swap_lod0.py` -> `build_lods.py` (LOD1 50 %) -> `shrink_shadow_lods.py` (the source project's
margins) -> `carry_variants.py` -> `lodrep/repair_glb.py`.

## Gates (GLB gate copies of source and reduced, 30 fps import, the master's labels: `scripts/gates.sh` -> `work/gates_final.txt`)

| gate | source | reduced |
|---|---|---|
| G4 arm stretch p99 (worst clip) | <= 2.05 (Hit R), Standing/Walking <= 1.37 | <= 2.05 (Hit R), Standing/Walking <= 1.31 |
| G5 hand stretch max L / R | 3.79x / 2.52x (Death) | 2.62x / 2.39x |
| G6 hands into coat at rest | L 1.9 / R 1.4 cm | L 1.9 / R 1.3 cm |
| G6 lying (Death) right hand / forearm | 6.0 / 3.0 cm | 6.0 / 6.0 cm |
| soles Standing / Walking / Hit | -1.4..-1.3 / -2.0..2.0 / 0..0.4 cm | the same (Hit 0..0.5) |
| LOD check: stretched faces, Dead lowest point | 0, 0.0 cm at every LOD | 0, 0.0 cm at every LOD |
| winding | 0 | 0 |

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/hes_villager_m_reduce_claude/review/viewer/`: approved export
(r100) and reduction (r73, default) for outfits A, B and C. `run_creature_review.py check`: 36 switches, no console errors.

## For the user to review

- 25 % off LOD0 (9,452 -> 7,064); face, eyes, pin, clasps and soles exact.
- While lying in Death the right forearm goes 6 cm into the coat instead of 3 cm (the source's right hand already
  goes 6 cm in there, from the motion).

## Install (not run)

Same file name, node, materials, variants and clips as the source project: `integration/actors.yml` (= the source draft)
applies unchanged. Through the Hesper stage: `tools/install_model.py` on `export/hes_hvm.glb` with the Hesper target
(after `check_winding.py`). Rollback: `work/hes_hvm_source_pre_reduce.glb`.

Reproduce: `find_doubles.py` (2), `import_source.py` (REA_NODE=HVM), dumps, `FRONT_Y=0.0 FRONT_ZMIN=1.47
make_groups.py`, `keep_near.py work/keep_front.npy work/small_body.npy work/keep_b.npy`, `groups_c.npy` (trousers
label 8), `err_lock.py` on c r73 -> `keep_d.npy`, `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_d.npy
REA_GROUPS=work/groups_c.npy REA_GROUP_RATIOS=1:0.6,2:0.55,3:0.7,4:0.75,6:0.7,8:0.6 scripts/run_ladder.sh d
0.77,0.75,0.73,0.71`, `build_export.sh Cand_73`, `gates.sh`, `lod_check.py`, `lod_views.py` + `lod_sheet.py`,
`viewer_tiers.py`, `viewer_manifest.py`, `glb_close.py`.

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
