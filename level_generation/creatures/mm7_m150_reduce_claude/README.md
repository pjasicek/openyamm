# MM7 Angel (`m150`, Angel / Angel Lord / Archangel) triangle reduction (2026-10-21)

User request after the batch G review rounds: "reduce tris count for all 5". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the textures,
region mask, tier ramps, clips and attachments stay as exported. **No Meshy credits.** Template:
`mm7_m162_reduce_claude/` (ladder, UV weights, LODs, LOD check, variants). Batch G rules apply: nothing installed,
nothing in `assets_dev/` or `assets_source/`, `mm7_m150_claude/` untouched (read only: its v7 exports and, for the
labels and gates, its master `work/rig_v6.blend`).

Source: `../mm7_m150_claude/export/mm7_m150.glb` (v7, after seven review rounds), copied to
`work/mm7_m150_source_pre_reduce.glb` (rollback source): one node `M150`, material `M150_A` (body + head merged into a
2080×1024 atlas) with the tier variants `M150_B` / `M150_C` (one region: the skirt), 52 `B_*` + twist + 6 wing bones,
4 influences, smooth-shaded. The welded source has 9,914 triangles (two coincident duplicate faces in the export;
the runtime cook adds the back faces of open sheets anyway).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| v7 body + wings | 9,916 | 4,947 | 1,748 | 556 |
| **reduced** (`export/mm7_m150.glb`) | **7,828** (−21 %) | 3,894 | 1,686 | 591 |

Attachments unchanged (tried and rejected, see below): helmet 2,000, sword 1,000, shield 900. LOD0 with props
13,816 -> 11,728.

## Labels and budgets

The export carries no piece labels; `master_labels.py` + `match_labels.py` take piece, garment and head-set per face
from the accepted master (centroid match 0.0 mm). `make_groups.py`:

- **Kept exactly** (user-reviewed): eyes, leather tabs, shoulder straps, the belt band of the torso shell and the
  buckle, the painted gold trims (faces sampling saturated gold in the atlas), and every small piece under 60 faces
  (hair locks, sandal straps, soles, feather cards).
- **Own ratios** (ladder `h`): 5 face (front, below the brow) 0.6 · 1 scalp / back hair / neck under the helmet 0.45 ·
  2 wing shells 0.75 · 3 bracers 0.75 · 4 skirt 0.9 · 6 palms 0.7 · 7 sandals 0.85 · 8 studs and belt rings 0.75 ·
  9 feather cards 1.0 · 10 fingers 0.65 · 0 torso, arms, legs and greaves take the rest.
- One drift/dark-sliver lock round (`texture_drift.py`, `dark_slivers.py`, `drift_lock.py`, 2 cm): 1,723 -> 1,888
  kept faces; drifted area 90 -> 43 cm² (13 faces), dark slivers 47 -> 32 (none visible in the close-ups).

## Ladder (limits at 1.9 m: p99 5.7 mm, max 28.5 mm)

| step | config | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| a | head 0.45-0.8, shells 0.5, cards/hands kept | 7,926 | 8.93 / 42.1 | 0.987 | fail (cut fell on the 984-face torso skin) |
| c | + small pieces kept | 8,522 | 6.83 / 30.9 | 0.993 | fail |
| d | cards at 0.8 | 8,038 | 5.94 / 17.8 | 0.993 | fail (cards p99 9.6 mm: each card is ~15 triangles) |
| g | cards kept, face 0.6, fingers 0.65 | 7,828 | 5.12 / 24.1 | 0.996 | pass |
| **h** | g + drift lock | **7,828** | **5.47 / 24.1** | **0.995** | **picked** |
| h | | 7,628 | 6.74 / 30.9 | 0.994 | fail |

Isolated cuts (`iso*`): the torso skin fails on its own at 0.7 (Death thigh 42 mm) and the feather cards cannot be
cut, so the body was already lean where it deforms; the saving comes from the face, scalp, wing shells, fingers,
bracers, studs and sandals. `group_error.py` reports the error per group.

Close-ups (`close_m150.py`, `review/close/sheet_h79_tex.png`, `sheet_r79_tex_[ab].png`, `sheet_r79_clay_a.png`): face
front and three-quarter, back of the head, both hands, belt, skirt in the attack, chest, shoulders from behind, wings
front, back and in the flap, feet, Attack, Death — no visible change.

## Props (unchanged)

`prop_reduce.py` (MeshLab texture-aware collapse on the attachment's LOD0): helmet 2,000 -> 1,600 tore the brow band
texture and dented the rim; shield 900 -> 700 bent the heater outline (`review/props_compare.png`). Both kept as
exported; the sword's 1,000 already protects its edges. A lighter helmet would need a new Meshy model at a lower
target (not done).

## Build

`scripts/build_export.sh` (Cand_79 of `work/ladder.blend` = `ladder_h`): `export_cand.py` -> `swap_lod0.py` (into the
rollback source: materials, variants, ramps, clips unchanged) -> `build_lods.py` (0.5 / 0.22 / 0.08; protected: the
bounding extremes and one Death/Dead floor-contact point per 6 cm cell — all ~840 floor points kept LOD3 at 1k) ->
`shrink_shadow_lods.py` -> `carry_variants.py`.

## Gates (reduced vs source, gate copies by `gate_prep.py`)

- `lod_check.py`: bounds kept at every LOD; lowest point per clip equal to the source at every LOD (the source LOD3
  floated up to 1.4 cm, the reduced does not); one stretched face (>20x area) in LOD0 Attack and Death.
- `g6_skirt_poke.py`: identical (attack 1.5 cm vs 1.4, death 5.0 vs 5.0).
- `waist_stretch.py`: p99 1.26-1.65 vs 1.43-2.08; max 4.85 vs 5.06.
- `shield_gate.py`: 0.0 cm vs 1.2 cm.
- `g6_contacts.py`: skin contacts <= 0.3 cm (source 0.5).
- Winding: 0 inverted closed parts. Viewer: `tools/run_creature_review.py ... check`, 6 models x 7 clips, no errors.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m150_reduce_claude/review/viewer/`: v7 body (r100) and the
reduced body (r79), each for tiers A, B and C (body + wings only; the viewer of `mm7_m150_claude` shows the props).

## Install (installed 2026-10-21)

Replaces only the body of `mm7_m150_claude/` (same node, materials, variants, clips and binding):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m150_reduce_claude/export/mm7_m150.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150_sword.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150_shield.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m150_claude/export/mm7_m150_helmet.glb --world mm7
```

Binding: `../mm7_m150_claude/export/actors_binding.yml` unchanged. Rollback: `work/mm7_m150_source_pre_reduce.glb`.
Note: rebuilding `mm7_m150_claude` (its `build_runtime.sh`) overwrites its own export only; repeat this reduction
after any later change there.

## Reproduce

Every step memory-capped (`scripts/cap.sh`; `scripts/bl.sh` for Blender).
1. `REA_NODE=M150 REA_GLB=level_generation/creatures/mm7_m150_reduce_claude/work/mm7_m150_source_pre_reduce.glb scripts/bl.sh import_source.py`;
2. `REA_PROTECT=B_Head scripts/bl.sh dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `master_labels.py`;
   `python3 scripts/match_labels.py`, `make_groups.py`;
3. ladder `g`, drift/dark locks on r79, then `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_d2.npy REA_GROUPS=work/groups.npy
   REA_GROUP_RATIOS=1:0.45,2:0.75,3:0.75,4:0.9,5:0.6,6:0.7,7:0.85,8:0.75,9:1,10:0.65 scripts/run_ladder.sh h 0.81,0.79`;
4. `cp work/ladder_h.blend work/ladder.blend; scripts/build_export.sh`;
5. `lod_check.py`, `gate_prep.py` (source and reduced), the gates above, `close_m150.py`, `pair_sheet.py`;
6. `viewer_tiers.py <glb> r100|r79`, `viewer_manifest.py`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: corpse at -4.2; dying sinks to -42.3; living lowest at -3.2 (suggested hover 0.023967).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m150.glb export/mm7_m150.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --hover 0.023967 Death Dead --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m150.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
