# Hesper Landfall villager, female (`hes_villager_f`, outfits vf_a/b/c) reduction (2026-10-22)

User: "the villager, female male + guard are ok, you can run the tris reduction playbook on them". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: textures, region mask, outfit ramps, rig
(114 bones, robe chains), clips and the leg/hand fixes of this week stay as exported. No Meshy credits. **Exported
2026-10-22, not installed** (Hesper is integrated by the Hesper stage; nothing in `assets_dev/` or `assets_source/`,
`hes_villager_f_claude/` untouched; its `build_runtime.sh` was not run, so its rebuild trap does not apply). Scripts as
in [`../hes_villager_m_reduce_claude/`](../hes_villager_m_reduce_claude/README.md); the gates `gates.py`,
`g6_leg_leak.py`, `g6_hand_proximity.py`, `sole_probe.py` (+ `cfg.py`, `armik.py`, the source `creature.json` as
`work/source_creature.json`) are copies from `../hes_villager_f_claude/`.

Source: `../hes_villager_f_claude/export/hes_villager_f.glb` (sha256 `5831a932…`), copied to
`work/hes_villager_f_source_pre_reduce.glb` (rollback source). One node `HVF`, material `HVF_A` (body + head sets in a
2080x1024 atlas) with variants `HVF_B` / `HVF_C` (regions coat, off-white, sash, hair). The source's own reduction had
kept the head and hands whole, so the head + neck piece alone was 3,519 triangles (a third of the mesh).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| approved export | 10,468 | 5,234 | 1,877 | 619 |
| **reduced** (`export/hes_villager_f.glb`) | **7,114** (-32 %) | 3,557 | 1,774 | 887 |

LOD2/LOD3 + shadows by the `lod_repair_claude` route at 25/12 % (LOD2 outline 2.8 % / colour 12.7, LOD3 5.0 % /
10.8; the default-ratio LOD3 scored 7.3 % / 21.1).

## Pieces and budgets (`FRONT_Y=0.0 FRONT_ZMIN=1.49 FRONT_ZMAX=1.66 make_groups.py`, masks `review/masks/`)

- **Kept exactly** (`work/keep_front.npy`, 2,608 faces): the face front (1,927: brows, eyes, nose, lips, chin, the
  fringe roots), eyes, earrings, buttons and clips (pieces up to 100 faces) and the soles.
- **Own ratios:** head outside the face (scalp under the bun, ears, neck) 55 %, hands 60 %, boots 75 %, bun 70 %,
  bag, strap and sash tail 75 %.
- **Rest (coat-dress, trousers):** the remaining budget (about 66 %).

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a | r80 | 8,370 | 2.97 / 15.1 | 0.995 | 0.996 | pass |
| a | r76 | 7,952 | 3.44 / 15.4 | 0.992 | 0.996 | pass |
| a | r72 | 7,532 | 4.00 / 20.4 | 0.988 | 0.993 | pass |
| **a** | **r68** | **7,114** | **4.85 / 20.8** | **0.982** | **0.990** | **picked** (lowest step tried; the leg and hand gates pass) |
| b | a + one drift/dark-sliver lock round (1,470 faces) | r70 | 7,322 | 22.5 / 108 | 0.963 | fail: the lock pushed the cut onto the coat |

Texture drift (`texture_drift.py r68`): 10 faces over 40 (111 cm²). Close-ups: `review/flat/sheet_a.png` (flat
textured), `review/close/sheet_a_clay.png`, `review/glbclose/sheet_r68_a_tex.png`, `sheet_r68_a_clay.png`,
`sheet_r68_bc_tex.png` (outfits B, C), LODs `review/lods/lod_sheet.png`.

## Build

`scripts/build_export.sh Cand_68` (with `work/ladder.blend` = `work/ladder_a.blend`): `export_cand.py` ->
`swap_lod0.py` -> `build_lods.py` (LOD1 50 %) -> `shrink_shadow_lods.py` (source margins) -> `carry_variants.py` ->
`lodrep/repair_glb.py`.

## Gates (GLB gate copies, 30 fps import, the master's garment/piece labels from `work/rig_v5.blend`: `scripts/gates.sh` -> `work/gates_final_reduced.txt`)

| gate | source | reduced |
|---|---|---|
| **G6 legs** (`g6_leg_leak.py`, leg vertices beyond 5 mm in front of the coat panels) | 0 in every frame of every clip | **0 in every frame of every clip** |
| **G6 hands** (`g6_hand_proximity.py`, contact < 10 mm, every frame) | 0 contact frames; nearest 10.8 mm (L, Death) / 11.9 mm (R, bag) | **0 contact frames**; nearest 11.0 mm / 12.2 mm |
| arm stretch p99 (Standing/Walking/Hit/Death/Fidget) | 1.20 / 1.25 / 1.97 / 2.22 / 1.57 | 1.24 / 1.22 / 2.00 / 2.12 / 1.51 |
| hand stretch max / hand in body | 1.56 / 0 | 1.38 / 0 |
| robe p99 / max (Walking, Death) | 1.87 / 2.69, 2.36 / 2.88 | 1.67 / 2.30, 2.13 / 2.84 |
| soles Standing / Walking / Hit | -0.7..-0.6 / -2.0..0.5 / 0..0.4 cm | identical |
| LOD check: stretched faces, Dead lowest point | 0, -0.0..-0.8 cm | 0, -0.0..0.2 cm |
| winding | 0 | 0 |

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/hes_villager_f_reduce_claude/review/viewer/`: approved export
(r100) and reduction (r68, default) for outfits A, B and C. `run_creature_review.py check`: 36 switches, no console errors.

## For the user to review

- 32 % off LOD0 (10,468 -> 7,114), the largest cut of the three: the source head was very dense; face, eyes,
  earrings, buttons and soles exact. The coat's gold piping is slightly less straight in flat close-ups.
- A few small dark texels on the right sleeve above the cuff at close range (dark-sliver check); a lock round made the
  coat much worse, so it was not used.
- The rebuilt LOD2 face looks blotchier than the old LOD2 up close (its own small far texture), but scores better at
  the switch size, as in the global far-LOD repair.

## Install (not run)

Same file name, node, materials, variants and clips: `integration/actors.yml` (= the source draft) applies unchanged.
Through the Hesper stage: `tools/install_model.py` on `export/hes_villager_f.glb` with the Hesper target (after
`check_winding.py`). Rollback: `work/hes_villager_f_source_pre_reduce.glb`.

Reproduce: `find_doubles.py` (0), `import_source.py` (REA_NODE=HVF), dumps, `make_groups.py` (env above),
`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_front.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.55,2:0.6,3:0.75,4:0.7,6:0.75 scripts/run_ladder.sh a 0.80,0.76,0.72,0.68`, `build_export.sh
Cand_68`, `gates.sh`, `lod_check.py`, `lod_views.py` + `lod_sheet.py`, `viewer_tiers.py`, `viewer_manifest.py`,
`glb_close.py`.

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
