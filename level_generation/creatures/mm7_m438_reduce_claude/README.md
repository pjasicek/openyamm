# MM7 Zombie (`m438`, Rotted Corpse / Walking Dead / Zombie) reduction (2026-10-21)

User request (batch F): "handle batch F ... check if they had their tris reduced". The Zombie had not (LOD0 11,343
with the forearm). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part
needed rebuilding, so the textures, region mask, tier ramps, rig, clips and the `Sword` attachment joint stay as
exported. No Meshy credits. **Not installed**; nothing written to `assets_dev/`, `assets_source/` or
`../mm7_m438_claude/`. Scripts copied from [mm7_m262_reduce_claude](../mm7_m262_reduce_claude/README.md) (ladder,
UV weights, LODs, LOD check, viewer), `mm6_wwf_reduce_claude` (`drift_lock.py`), `mm7_m166_reduce_claude`
(`spot_blend.py`), `mm6_natf_reduce_claude` (`prop_ladder_io.py`), `mm7_m442_reduce_claude` (`viewer_sickle.py` ->
`viewer_forearm.py`); the gates `g4_weights.py`, `g5_hand_stretch.py`, `g6_prop.py`, `sole_probe.py`,
`shrink_shadow_lods.py` and `clamp_lod_uv.py` are copies from `../mm7_m438_claude/scripts/`. Every Blender/Python step
runs memory-capped (`scripts/cap.sh`).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m438_reduce_claude/review/viewer/) (batch F export
r100 vs reduced r78, tiers A/B/C, eight clips, the forearm shown under the `Sword` joint) ·
GLB close-ups [front textured](review/glbclose/sheet_front_tex.png), [front clay](review/glbclose/sheet_front_clay.png),
[back textured](review/glbclose/sheet_back_tex.png), [back clay](review/glbclose/sheet_back_clay.png) ·
[forearm ladder textured](review/prop/sheet_tex.png), [clay](review/prop/sheet_clay.png) ·
[LOD views](review/lods/sheet.png) · [viewer shots](review/shots/sheet.png) ·
gates [source](review/gates_source.txt), [reduced](review/gates_reduced.txt)

## Source

`../mm7_m438_claude/export/mm7_m438.glb` and `mm7_m438_forearm.glb` (the final batch F export of 2026-10-20 14:00,
built after the stump-bone and wound-end review; `export_info.json` describes the portable `mm7_m438_lod0.glb` of the
same build), copied byte for byte to `work/mm7_m438_source_pre_reduce.glb` (sha256 `aec055df75f6…`) and
`work/mm7_m438_forearm_source_pre_reduce.glb` (`521132ff0837…`): the rollback sources. Body node `Zombie`, one merged
body + head atlas material per tier (`Zombie_A/B/C`, 2080x1024, region mask R = trousers and headband), variants
`m438_a/b/c`, 57 joints incl. `Sword`, shadow LODs, clips Attack, Dead, Death, Fidget, Hit, Running, Standing,
Walking. Forearm node `Sword`, three identical `Forearm_A` variant materials, own 512 texture set, LOD1-3.

Weld (identical weights only, `import_source.py`): 5,317 -> 163 open edges, 4,837 vertices (the master's count), 7
coincident vertices with other weights kept apart, 9,499 triangles in and out. Labels come from the production master
`../mm7_m438_claude/work/rig_v7.blend` (read only; `master_pieces.py`, `source_world.py`, `face_labels.py`: nearest
rest vertex, max 0.001 mm): piece, garment, finger, plus per face the head set (u > 0.5), wound share (crimson texels)
and the region share. Bind height 1.75 m (ladder limits p99 5.25 mm, max 26.25 mm).

## Where the triangles are

| part | faces | treatment |
|---|---:|---|
| left fingers (the fist round the forearm) | 1,019 | kept exactly |
| face front (head-set skin within 7.5 cm of the face centre) | 1,087 | kept exactly |
| headband (region R in the head set) + one ring | 382 | kept exactly |
| rope belt and ends (thin tubes) | 498 | kept exactly |
| soles (faces below 6 cm) | 499 | kept exactly |
| stump bone shafts, shin rods, lathe right shin | 392 | kept exactly |
| right-arm stump (B_R_Forearm skin) | 156 | kept exactly |
| eyes, teeth | 191 | kept exactly |
| trouser/skin faces within 3 cm of the rope | ~250 | kept exactly (cr74 pushed trouser-top wedges out over the rope) |
| drift / error locks (one round each, below) | ~240 | kept exactly |
| trousers (holes and bloody cuff included) | ~1,700 | own group 55 % |
| rest of the head set (scalp, back of head, ears, neck) | ~970 | own group 55 % |
| feet above the soles | ~380 | own group 50 % |
| left hand back/palm | ~375 | own group 60 % |
| torso and arms | ~1,430 | the remaining ladder budget |

About 4,640 of the 9,499 faces (49 %) are kept exactly. The original build had already reduced everything but head
and hands (16.2k -> 9.8k), so the torso has little left to give: its error (the nape and upper back in Fidget and
Death, `region_error.py`, `probe_err.py`) sets the floor of every configuration.

## Ladder (REA_HEIGHT_M 1.75: p99 <= 5.25 mm, max <= 26.25 mm, IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| a: keep set, trousers 60 %, head 55 %, feet 65 %, hand 60 % | r78 | 7,409 | 3.56 / 20.4 | 0.994 | pass (r76 fails max 26.6) |
| b: trousers 50 %, head 50 % | r74 | 7,025 | 4.47 / 27.8 | 0.992 | fail (left knee in the run) |
| c: trousers 55 %, head 50 %, feet/hand 55 % | r74 | 7,025 | 4.55 / 24.1 | 0.992 | pass, **but** trouser-top wedges over the rope (back, sides), a dark sliver in a trouser hole, an orange sliver at the navel |
| e: c + error lock (41 vertices > 15 mm, 2.5 cm) | r74 | 7,025 | 5.52 / 27.8 | 0.989 | fail: the lock pushed the cut onto the torso |
| g: rope ring kept, trouser holes 65 %, rest 45 % | r76 | 7,213 | 7.17 / 25.4 | 0.984 | fail (trousers too low) |
| i: one shared collapse (Dwarf lesson) | r78 | 7,409 | 4.91 / 28.5 | 0.991 | fail: worse than per-group |
| k: rope ring kept, head 40 %, hand 45 %, feet 50 % | r74 | 7,025 | 4.77 / 27.8 | 0.991 | fail (run knee) |
| m: k + 4 cm knee patch + drift/dark lock (R 1.5 cm) | r76 | 7,217 | 5.11 / 22.1 | 0.991 | pass; clay shows scalp dents (head 40 %) and a crease on the back of the hand (45 %) |
| n: m with head 55 %, hand 60 % | r78 | 7,407 | 4.97 / 23.3 | 0.992 | pass, clean |
| p: n + 4 cm nape patches | r76 | 7,217 | 6.49 / 27.3 | 0.989 | fail: locks push the cut |
| **q: n + 2 cm lock round the navel sliver** | **r78** | **7,407** | **4.97 / 23.3** | **0.992** | **picked** (SSIM 0.995) |

Close-up sheets (`close_m438.py`, ladder blends, textured and clay, 24 spots front and back): `review/close/sheet_m_*`
(source / m r76 / m r75), `sheet_n_*` (source / m r76 / n r78 / n r77); flagged spots `review/spots_c/`,
`review/spots_n/sheet.png`, `review/spots_q/sheet.png` (the navel sliver gone in q r78).

Checks on q r78: texture drift (`texture_drift.py`) 0 faces over 40 (p99 16.8); dark slivers (`dark_slivers.py`) and
red slivers (`red_slivers.py`, wound texels pulled onto skin or cloth) mostly at the bloody right shin, where the
wound edges already run across the faces; two on the left trouser holes, whose outlines shift by a few millimetres
but keep their shape (`review/spots_q2/sheet.png`); one 9.9 cm² face on the right upper back that renders like the
source (`review/spots_n/sheet.png` p0). Stretch: 0 stretched faces in every clip at every LOD (`lod_check.py`).

## Forearm prop (`prop_reduce.py`)

1,844 triangles: the severed hand beyond the fist is 1,284 of them (the left hand's dense fingers, mirrored), the
forearm only ~190. The fist zone and forearm (y >= -0.10 m in prop space), the ragged wound cap and both bone shafts
(560 faces) are kept exactly; only the hand is decimated (MeshLab texture-aware, boundary kept; source vertices keep
their normals, new ones get smooth normals). LOD1-3 (922 / 330 / 108) stay as exported.

| step | triangles | two-way max / mean mm | |
|---|---:|---|---|
| **r70** | **1,458** | **1.85 / 0.06** | **picked**: textured and clay match the source |
| r60 | 1,330 | 2.88 / 0.10 | fingertips a little sharper in clay, one extra dark crease on a finger at 7 cm framing |
| r50 | 1,202 | 3.38 / 0.14 | jagged fingertips |
| r40 | 1,072 | 3.51 / 0.18 | jagged fingers |

## Result

`TOKEN=<lease> scripts/build_export.sh ladder_q.blend Cand_78 r70`: `export_cand.py` -> `swap_lod0.py` (into the
rollback source) -> `build_lods.py` (0.5 / 0.25 / 0.08, 8 influences like the batch F LODs, bounding extremes
protected) -> the m438 project's `shrink_shadow_lods.py` -> `carry_variants.py` -> `clamp_lod_uv.py` (nothing to
clamp); the forearm is `work/forearm_r70.glb`.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch F export, body | 9,499 | 4,748 | 1,708 | 562 |
| **reduced body** | **7,407** | 3,702 | 1,851 | 586 |
| batch F forearm | 1,844 | 922 | 330 | 108 |
| **reduced forearm** | **1,458** | 922 | 330 | 108 |
| combined, batch F | 11,343 | 5,670 | 2,038 | 670 |
| **combined, reduced** | **8,865** | 4,624 | 2,181 | 694 |

Body -22.0 %, forearm -20.9 %, combined LOD0 -21.8 %: short of the 25-35 % aim, see "For the user to review".
LOD2/3 stay at the batch F counts on purpose (the ratios 0.25 / 0.08 instead of the tool's 0.18 / 0.06).

- [`export/mm7_m438.glb`](export/mm7_m438.glb), 7.8 MB, sha256 `60a11e17cc4fc979de5c9c094f7c6e31bacf7155d47fc7d7ff2414ce684db285`.
- [`export/mm7_m438_forearm.glb`](export/mm7_m438_forearm.glb), 0.5 MB, sha256 `a6316f0fee127bcf156d407250cbe49ec71f9fd33d25a59a5acdfca8ebace47f`.
- `compare_glb.py` against the rollback sources: nodes and transforms, skin joints, inverse bind matrices,
  materials (incl. region ramps and specular extras), variant mappings on every primitive, mesh names and LOD/shadow
  extras, attributes, animations (sampler data byte for byte), images, textures: **identical**; only geometry differs.
- `check_winding.py`: 0 inverted closed parts in both GLBs (source body 0 as well).

### LOD check (`lod_check.py`, every frame of every clip, `lod_table.py`)

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---|---|---|---|
| source: lowest point Dead / Death (cm) | -0.0 / -1.9 | +0.1 / -1.8 | -0.2 / -2.1 | -0.1 / -2.1 |
| reduced: lowest point Dead / Death (cm) | +0.1 / -1.8 | +0.1 / -1.8 | -0.2 / -1.7 | -0.3 / -1.5 |
| stretched faces (> 20x), all clips | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| rest height (m), source / reduced | 1.7504 / 1.7510 | 1.7501 / 1.7507 | 1.7502 / 1.7514 | 1.7452 / 1.7502 |

The playbook's floor-contact lock (`REA_FLOOR_M` 3 cm, then 1 cm) broke LOD3 here: the corpse's contact points held
most of the lower body and the 586-1,034-triangle budget collapsed the head and arms into a wedge
(`review/lods/sheet.png`, bottom row). Without it (`REA_FLOOR_M=-1`, the build default now) every LOD matches the
batch F look and the corpse stays within 2 mm of the source's floor contact.

## Gates (gate copies of both GLBs: `gate_import.py` at 30 fps, `gate_attrs.py` labels from the master by connected
piece, `gate_prop.py` adds the forearm GLB on the `Sword` joint; `run_gates.sh`, `gate_summary.py`)

| gate | source | reduced |
|---|---|---|
| G4 arm stretch p99 / max, right (stump) | 2.18 / 3.44 | 1.72 / 3.33 |
| G4 arm stretch p99 / max, left (carrying arm) | 1.83 / 2.80 | 1.53 / 2.74 |
| G5 hand stretch max right / left | 1.20 / 1.83 | 1.04 / 1.71 |
| G6 prop, forearms and hands inside the skin/trousers | 0 cm except L forearm 0.1 cm (Running) | the same |
| G6 lowest prop point (Death) | 1.4 cm | 1.4 cm |
| soles: lowest foot range Standing / Walking / Attack / Hit / Fidget (cm) | -0.7..-0.3 / -1.3..2.0 / -0.8..1.9 / -0.9..1.2 / -0.2..0.2 | identical |

The source copy reproduces the production gates (G6 0.1 cm run, soles); its G4 figures are higher than the
production `gates_final.txt` because the welded GLB copy samples the arm edges differently. The rig, clips, grip and
stride are unchanged, so the jerk, stride and height gates of the batch F run still apply.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m438_reduce_claude/review/viewer/`: batch F export (r100) and
reduced (r78, default) for tiers A, B and C (`viewer_tiers.py` bakes the ramps; `viewer_forearm.py` adds each
version's forearm under the `Sword` joint, review only). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm7_m438_reduce_claude check`: 48 switches, 8 clips, no console errors; shots in
`review/shots/`.

## For the user to review

- **22 % off, short of the 25-35 % aim.** Half of the body is kept exactly (face front, the fist's fingers, headband,
  rope, soles, stump and shin bones, rope junction), and the rest was already cut once by the production build. Every
  cheaper configuration either failed the error gates at the nape/upper back (Fidget, Death) or showed damage: c r74
  (7,025, -26 % body) passed the numbers but pushed trouser wedges out over the rope at the back and sides, left a
  dark sliver in a trouser hole and an orange sliver at the navel; m r76 (7,217) dented the scalp and creased the back
  of the hand in clay. If a lower count matters more than those close-up spots, c r74 is in `work/ladder_c.blend`.
- The abdominal muscle ridges are softer in clay renders (`review/glbclose/sheet_front_clay.png`, chest and rope
  rows); with the textures (painted shading and normal map) the abs read as before.
- A small dent on the top of the scalp in clay (front view), invisible under the scalp texture.
- The head top is 0.6 mm higher at rest (1.7510 m vs 1.7504 m); the binding's scale (1.726 m Standing) is unaffected.
- Forearm: r70 is the clean step; r60 (1,330) is available in `work/forearm_r60.glb` if the extra 128 triangles matter.

## Install (not run)

Replaces the batch F export of `mm7_m438_claude/` (same nodes, materials, variants, clips and `Sword` joint):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m438_reduce_claude/export/mm7_m438.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m438_reduce_claude/export/mm7_m438_forearm.glb --world mm7
```

The actors.yml binding is unchanged: add [`../mm7_m438_claude/actors_m438_binding.yml`](../mm7_m438_claude/actors_m438_binding.yml)
to `assets_dev/worlds/mm7/models/actors.yml` (Zombie A/B/C, scale 125.1, skins `m438_a/b/c`, forearm attachment on node
`Sword`). Rollback: `work/mm7_m438_source_pre_reduce.glb` and `work/mm7_m438_forearm_source_pre_reduce.glb` (or the
batch F files in `../mm7_m438_claude/export/`). Record the install in `REDUCTION_LEDGER.md` when it happens.

## Reproduce

Claim the project (`tools/creature_workspace.py claim --identity mm7:m438-reduce`), then with `TOKEN=<lease>`:
`import_source.py` (REA_GLB, REA_NODE=Zombie), `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `master_pieces.py`,
`source_world.py`, `face_labels.py`, `make_groups.py`, `make_groups_g.py` (rope ring), `spot_keep.py work/keep_k.npy
work/keep_m0.npy 0.04 2481`, `drift_lock.py` on the k r73 flags (R 1.5 cm) -> `keep_m.npy`, `spot_keep.py
work/keep_m.npy work/keep_q.npy 0.02 177`, `REA_HEIGHT_M=1.75 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_q.npy
REA_GROUPS=work/groups_q.npy REA_GROUP_RATIOS=1:0.55,2:0.55,3:0.5,4:0.6 scripts/run_ladder.sh q 0.79,0.78,0.77`,
`close_m438.py`, `flag_spots.py`, `spot_blend.py`, `red_slivers.py`; forearm `prop_reduce.py 0.7,0.6,0.5,0.4`,
`prop_views.py`, `prop_spots.py`; `build_export.sh ladder_q.blend Cand_78 r70`, `compare_glb.py`, `lod_check.py`,
`lod_views.py`, gates (`gate_import.py`, `gate_attrs.py`, `gate_prop.py`, `run_gates.sh`), `glb_close.py`,
`viewer_tiers.py`, `viewer_forearm.py`, `viewer_manifest.py`. `run_ladder.sh` calls a pymeshlab venv by absolute
path (another session's scratchpad); recreate it if it is gone.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.4.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m438.glb export/mm7_m438.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m438.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h09)

New clips appended to the installed source (this reduction's export as installed): `Walk2` (Mixamo Orc Walk, 1.20 s, stride 1.6091) bound as `walking`, `Jog` (Unarmed-Run-Forward leaned, 0.80 s, 2.2022) as `run`, `Sprint` (Unarmed-Sprint, 0.60 s, 3.5625) as `sprint`; the stump and carried forearm come from the model's own Walking / Running. `Walking` (the drunk stagger) and `Running` stay, unbound.

Rebuild: `level_generation/creatures/gait_rollout_20261031/h09/scripts/rebuild.sh m438` (composes from the pre-gait copy
`h09/work/mm7_m438_pre_gait.glb` and `h09/jobs/`, runs `gait_gate.py` and `check_winding.py`), then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h09/export/mm7_m438.glb --world mm7 --name
mm7_m438.glb`. Bindings: `h09/bindings.yml` (applied by the rollout coordinator). A far-LOD repair, head-bob, floor or
reduction rerun on this model must re-graft these clips: copy the new installed source over the pre-gait copy and
rebuild. Details, gates and doubts: [h09 README](../gait_rollout_20261031/h09/README.md).
