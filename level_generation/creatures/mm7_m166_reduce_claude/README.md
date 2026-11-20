# MM7 Beholder (`m166`, Floating Eye / Gazer / Evil Eye) reduction (2026-10-21)

User: "yes run the texture aware reduction" (Batch H follow-up). [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
default route, no-retexture branch, with the scripts of [mm7_m186_reduce_claude](../mm7_m186_reduce_claude/README.md)
(texture-aware MeshLab ladder, per-group ratios, floor-contact LOD lock, stretch/drift/dark-sliver checks). No Meshy
credits. Not installed (Batch H rule).

## Source

The [mm7_m166_claude](../mm7_m166_claude/README.md) export had been reduced with Blender's edit-mode decimate
(15,154 → 9,419), which the playbook rules out (it slides UVs across seams). This project starts again from the
unreduced UV master: `scripts/build_source.sh` exports `../mm7_m166_claude/work/uv_master.blend` with the beholder
project's own chain (material contract, prepare, LODs, shadow fix, tier ramps) to `work/mm7_m166_source.glb`
(15,154 triangles, sha256 `1611c500…`). Its five actions are key-for-key identical to those of the accepted export's
`uv_r1.blend` (checked per F-curve), so no re-keying was needed. Same textures, ramps, rig, sockets and clips.

`import_source.py` (REA_NODE=Beholder): weld 10,864 → 428 open edges (separate pieces: tentacles, stalks, tongue,
19 teeth), 15,148 triangles after the weld (6 duplicate faces), 46 coincident vertices with other weights kept apart.
Height 0.925 m: limits p99 2.78 mm, max 13.9 mm.

## Labels

`scripts/m166_groups.py` (connected pieces and dominant bones) and `scripts/drool_group.py`:
- **kept exactly** (`work/keep_iris.npy`, 532 faces): head faces within 7.5 cm of the painted iris (an eye texture tears
  under collapse, [mm6_bh_reduce_claude](../mm6_bh_reduce_claude/README.md));
- **stalk eyeballs** (`work/stalk_eyes.npy`, 1,614 faces: the split `StalkEye` piece and the end 6.5 cm of the other
  three stalks) decimated on their own at 60 %; the painted irises stay round (`review/close/sheet_k2.png`, stalk rows);
- **drool** (`work/groups_drool.npy`, 967 yellow faces on the head piece) at 65 %: under a uniform cut the drips
  shortened first (k2 r40/r35 in `review/close/sheet_k3.png` / `sheet_k4.png`);
- everything else (head flesh, tentacles, stalk shafts, teeth, tongue) takes the remaining ladder budget.

## Ladder

| config | step | triangles | p99 / max mm | IoU (min) | SSIM | |
|---|---|---:|---|---|---|---|
| k1: all eyes kept, rest uniform | r60 | 9,088 | 2.22 / 5.17 | 0.982 | 0.993 | pass (auto-pick) |
| | r50 / r45 / r40 / r35 | 7,574 / 6,816 / 6,058 / 5,300 | 3.27 … 5.66 / 6.8 … 14.0 | 0.975 … 0.953 | | fail |
| k2: iris kept, stalk eyes 60 % | r45 / r40 / r35 / r30 | 6,816 / 6,058 / 5,300 / 4,544 | 3.36 / 4.01 / 5.06 / 5.89 | 0.974 … 0.950 | | fail; drips shorten |
| **k3: k2 + drool 65 %** | **r45** | **6,814** | **3.79 / 8.49** | **0.970** | **0.987** | **visual pick** |
| | r40 / r35 | 6,058 / 5,300 | 4.82 / 5.62 | 0.963 / 0.953 | | light streak on the brow (r40) |
| k4: k3 + 60 % ring round the eye | r42 / r40 | 6,360 / 6,058 | 4.81 / 5.16 | 0.964 / 0.959 | | no visible gain |
| k5: k3 + drift lock (drift > 25, 43 faces, 2 cm) | r42 / r40 | 6,360 / 6,058 | 6.59 / 7.74 | 0.939 / 0.927 | | worse: 1,352 locked faces push the cut elsewhere |

**Pick: k3 r45, 6,814 triangles.** Only the k1 r60 step (9,088, barely below the accepted 9,419) meets the geometric
gates. `scripts/err_groups.py` (exact rest-pose error per group) shows why: the source's brain folds are a field of
lumps that every collapse flattens by 3–6 mm (source → candidate), and the 3–4 cm tentacles thin by a few millimetres;
the silhouette losses are one-pixel outline jitter along the eight thin tentacles (IoU difference maps, front/back
views worst). With the normal map the folds read the same (`review/glbclose/sheet.png`: source / accepted / r45,
textured and clay, straight from the GLBs), so the step is picked visually, as for the MM6 Flying Eye, goblin, hydra
and dragonfly reductions. r40 was rejected for a light streaked triangle on the brow at 25 cm framing
(`review/spots_brow/sheet.png`: source / k1 r60 / k1 r50 / k3 r45 / k3 r40); the remaining brain-texture streaks there
are already present at r60.

Close-up sheets (Eevee textured and clay, rows eye, head, top, back, mouth, both stalk eyes, tentacle tip, tentacle
chains, Attack, Dead): `review/close/sheet_k1.png`, `sheet_k2.png`, `sheet_k3.png` (source / r45 / r40 / r35),
`sheet_k4.png` (source / k3 r40 / k4 r40). Ladder sheets `review/ladder_sheet_k{1,2}.png`.

Checks on k3 r45:
- Stretch (`stretch_check.py`, every 2nd frame of every clip): 0 faces in source, r45 and r40.
- Texture drift (`texture_drift.py`): 9 faces over 40, 4.9 cm² in all, none over 3 cm² (the lock rule's size), so no
  drift lock round.
- Dark slivers (`dark_slivers.py`): 153 faces flagged (241 cm²), large faces over the dark brain crevices; the worst
  six spots (`review/spots/sheet_dark.png`, 12 cm framing, source / r45 / r40, outward and from above) show slightly
  streaked brain texture, no dark slivers. Visible only at close-up range.

## Result

`scripts/build_export.sh`: `export_cand.py` (Cand_45 of `work/ladder_k3.blend`) → `swap_lod0.py` (into the source GLB)
→ `floor_contacts.py` (Death/Dead, 41 vertices, 19 points) → `build_lods.py` (0.5 / 0.25 / 0.125, 4 influences,
contacts protected) → the beholder project's `shrink_shadow_lods.py` (≤ 1 mm) → `carry_variants.py` (7 primitives) →
`check_winding.py`.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| unreduced source | 15,154 | 7,574 | 3,786 | 1,890 | 8.3 MB |
| accepted export (Blender decimate) | 9,419 | 4,707 | 2,352 | 1,172 | 6.9 MB |
| **this reduction** | **6,814** | **3,406** | **1,699** | **848** | **6.6 MB** |

[`export/mm7_m166.glb`](export/mm7_m166.glb), sha256 `e8921b2ee9dd49edf4bfc30eca1710e32a1d76140f8af911e153007d34ca1c3c`;
variants `m166_a/b/c` on all colour and shadow primitives, materials `Beholder_A/B/C`, 4 images, clips Attack, Dead,
Death, Fly, Hit, `EyeSocket` kept. Winding: 0 inverted closed parts. `lod_check.py` (every frame of every clip, every
LOD, `work/lod_check_r45.json`): Death and Dead rest at +2.0 mm at all four LODs (as the source), no stretched faces at
any LOD, rest bounds kept (LOD3 tentacle tip 1 cm shorter at the bottom); Fly dips 3.7 cm below the origin (tentacle
tips) by design, as the source.

## Viewer

[review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m166_reduce_claude/review/viewer/): three tiers,
source vs r45 (ramps baked per tier by `viewer_variants.py`). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm7_m166_reduce_claude check`: 30 clip switches, no console errors.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m166_reduce_claude/export/mm7_m166.glb --world mm7
```

Binding unchanged (see the [beholder project README](../mm7_m166_claude/README.md)). Rollback / higher-detail sources:
`work/mm7_m166_source.glb` (unreduced) or `../mm7_m166_claude/export/mm7_m166.glb` (9,419).

## Rebuild

`scripts/build_source.sh` → `import_source.py` (REA_NODE=Beholder, REA_GLB=…/work/mm7_m166_source.glb) →
`dump_mesh.py` → `m166_groups.py` → `drool_group.py` → (split `keep_eyes.npy` into `keep_iris.npy` / `stalk_eyes.npy`)
→ `REA_KEEP_FACES=work/keep_iris.npy REA_PROTECT_FACES=work/stalk_eyes.npy REA_PROTECT_RATIO=0.6
REA_GROUPS=work/groups_drool.npy REA_GROUP_RATIOS=1:0.65 scripts/run_ladder.sh k3 0.45,0.4,0.35` →
`scripts/build_export.sh` → `viewer_variants.py` (source r100, export r45).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: living lowest at -10.4 (suggested hover 0.036502); living lowest at -10.8 (suggested hover 0.036502); living lowest at -11.1 (suggested hover 0.036502).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m166.glb export/mm7_m166.glb --hover 0.036502 Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m166.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
