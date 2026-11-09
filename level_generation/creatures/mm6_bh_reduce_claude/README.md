# MM6 Flying Eye (`bh`, BBeholder A/B/C) reduction, teeth and texture repair (installed 2026-10-14)

User: "3D tris count reduction playbook - do flying eye". [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) default
route, no-rebuild branch, on the installed `assets_source/worlds/mm6/models/mm6_bh.glb` (mesh node `Eye`, one texture
set). No Meshy. The source had already been trimmed once in its own build (`mm6_bh_claude/scripts/reduce_lod0.py`:
Smart Topology 15,823 -> 10,722, horns 40 %, back skin 50 %), so less is left to take.

Started with `../reduce_installed.sh bh Eye "MM6 Flying Eye"` (a copy with the eye's bones as close-up aliases:
`EyeBall`, `Jaw`, `Tendrils`); `scripts/run_ladder.sh <ratios>` reruns decimate -> ladder -> compare with the current
`REA_*` environment. Weld 8,504 -> 810 open edges (separate pieces), unchanged at every step. Limits for the 1.0 m
model: p99 3.0 mm, max 15 mm.

## Ladder rounds

| round | step | triangles | p99 / max mm | SSIM | drift > 40 (cm²) | |
|---|---|---:|---|---|---:|---|
| uniform | r80 | 8,576 | 2.3 / 9.0 | 0.994 | | pass |
| uniform | r75 | 8,040 | 2.7 / 14.7 | 0.994 | | pass, auto-pick; pupil already jagged |
| uniform | r65 | 6,968 | 4.2 / 14.7 | 0.990 | | pupil torn |
| uniform | r55 | 5,896 | 5.7 / 14.9 | 0.976 | | pupil torn |
| all pieces kept | r70 | 7,504 | 5.1 / 14.9 | 0.982 | | worse: the main head takes the whole cut |
| eyeball kept | r65 | 6,968 | 4.4 / 14.4 | 0.988 | 201 | |
| **eyeball + drift lock** | **r65** | **6,968** | 4.9 / 12.1 | 0.986 | **17** | **pick** |
| eyeball + drift lock | r60 | 6,432 | 6.0 / 12.3 | 0.979 | 190 | option |
| eyeball + lock + all pieces | r65 | 6,968 | 7.5 / 36.1 | 0.972 | 466 | worse |

- The **eyeball** (pieces 3 and 4, 608 faces: the painted iris and pupil) tore at every uniform cut: the collapse moved
  UVs across the pupil. It is kept exactly (`work/keep_eyeball.npy`).
- One **drift lock** round (`texture_drift.py` + `drift_lock.py` on r60 and r55; 1,188 faces kept, `work/lock1.npy`).
- The geometric metric fails from r70 down because the Meshy back skin is a field of small lumps: every collapse
  moves the surface 3-5 mm. The lumps, horns and fangs still read the same in the close-ups, so the step is picked
  visually (as for the goblin and hydra). Per-region budgets (`groups_bh.npy`: skin / face / horns / pieces) and
  keeping the lips, gum and teeth only moved the cut onto the skin.
- `scripts/regions_bh.py` (pieces and region mask per face), `scripts/err_regions.py` (rest-pose error per region and
  worst spots: the horns and the back lumps), `scripts/groups_bh.py`.

## Round 1 result (k65, superseded by round 2)

`work/round1/mm6_bh.glb`: LODs **6,968 / 3,483 / 1,248 / 409** (installed 10,722 / 5,361 / 1,928 / 635). Built
export_cand -> swap_lod0 -> `tools/build_actor_lods.py` -> `mm6_bh_claude/scripts/shrink_shadow_lods.py` (as the
installed build) -> carry_variants. Textures, region ramps, variants `bh_a/b/c`, clips and the binding are unchanged.

Close-ups (Standing frame 0; rows installed / k65 / k60): `review/close/sheet_k_whole.png`, `sheet_k_head.png`
(eye and brow), `sheet_k_hand.png` (mouth and fangs). Remaining differences: a few small dark slivers on the upper
lip and cheek (more at k60). Earlier rounds: `sheet4_*.png` (installed / r75 / r65 / r55 uniform).

Viewer `review/viewer/` (installed, k65 and k60 per tier, all clips): `check_viewer.mjs` 81 loads, no errors.

## Round 2: teeth, black shards (2026-10-14)

User: "fix all the teeth", "check the black spots or triangles why its wrong and either fix it before retexture or if
retexture helps then retexture or uv". No Meshy.

**Why the black shards.** Two causes, both in the installed model:
1. The original build cut the horns (40 %) and back skin (50 %) with Blender's collapse decimate *after* texturing
   (`mm6_bh_claude/scripts/reduce_lod0.py`); it slid UVs across seams. The pre-cut mesh still exists with the UVs the
   texture was composed on (`mm6_bh_claude/work/anim_v1_full.blend`, 15,823 tris; `scripts/export_full.py` ->
   `work/mm6_bh_full_source.glb`), so round 2 reduces from it with the UV-safe MeshLab ladder.
2. Meshy left texturing gaps on surfaces no HD view saw (horn undersides and inner curls, hidden face surfaces): wide
   near-black blobs inside the islands (the HD references have uniform grey horns). Any cut makes them sharp triangles.
   `scripts/repair_horns.py` fills them in all four shared maps from the nearest clean texel of the same horn / face in
   rest-pose 3D: rule `dark` (tier A ramped luminance < 45, opening radius 4 so the thin ring stripes stay) on the horns
   and the face, then rule `neutral` (grey camouflage mottles: luminance < 90, red - green < 12) on the horns. The ring
   stripes continue across the filled areas. `scripts/pad_textures.py` then pads every unused texel from the nearest
   island (the Meshy gutters were dark). Texels under the source UVs stay identical apart from the repaired blobs.
   Not used: UV re-projection per face (`scripts/reuv.py`, more drift), drift locks and per-region budgets (the rest of
   the head took the cut; errors doubled).

**Teeth** (`scripts/teeth_select.py`, `scripts/fix_teeth.py`, `scripts/ivory_cell.py`):
- The six separate tooth pieces (4 upper, 2 lower; brown roots, ragged) are fitted cones: 8 sides, shoulder ring at
  0.55, root sunk 15 % into the gum, rigid on the piece's bone (upper Head, lower Jaw), 30 tris each (750 -> 180).
- The two big fangs (part of the main head) and the four gum spikes keep their geometry; their dark lower band and brown
  paint are replaced by UVs in a painted ivory cell (free 2K square, root-to-tip gradient from the fangs' clean ivory,
  the fangs' own face-region mask value so every tier colours them as before, flat normal).
- Teeth and eyeball are kept exactly in the ladder (`work/keep_eye_teeth.npy`). Attack frame 9 checked: cones follow
  Head and Jaw (`review/mouth/sheet_attack.png`).

| step (pre-cut 15,823) | before teeth | after teeth | p99 / max mm | drift > 40 | |
|---|---:|---:|---|---:|---|
| r55 | 8,701 | | 4.7 / 16.9 | 20 | |
| **r50** | 7,911 | **7,341** | 5.4 / 17.3 | 30 | **pick**: face clean, horn stripes intact |
| r45 | 7,119 | 6,549 | 6.5 / 17.3 | 38 | horn stripes break up, more drift spots |

## Result (t50)

`export/mm6_bh.glb`: LODs **7,341 / 3,670 / 1,315 / 430** (installed 10,722 / 5,361 / 1,928 / 635), shadow LODs
shrunk as in the eye build, variants carried. Textures replaced by the repaired + padded set (same four images, same
names). Clips, binding and tiers unchanged; tier C teeth take the lime face ramp exactly like the installed fangs
(`review/mouth/sheet_tiers.png`).

Reviews: `review/mouth/sheet_t.png` (rows installed / pre-cut repaired / t50 / t45), `review/close/sheet_t_whole.png`,
`review/close/horn_repair2.png` (horn repair steps). Viewer `review/viewer/` (installed, t50, pre-cut repaired
reference per tier): `check_viewer.mjs` 81 loads, no errors. Remaining: faint grey mottling at the horn roots seen
from behind (also on the repaired pre-cut mesh); the mouth corners stretch a little more than the source at the widest
Attack gape.

Rebuild: `export_full.py` -> `repair_horns.py` (horns dark, horns neutral, face dark) -> `ivory_cell.py` ->
`pad_textures.py` -> `import_source.py` + `dump_mesh.py` -> `REA_KEEP_FACES=work/keep_eye_teeth.npy run_ladder.sh 0.50`
-> `build_teeth_cand.sh 50` -> `build_actor_lods.py` -> `shrink_shadow_lods.py` -> `carry_variants.py`.

## Installed

User accepted t50 (2026-10-14: "good accepted"). Previous source backed up to `work/mm6_bh_source_pre_reduce.glb`;
installed with `tools/install_model.py export/mm6_bh.glb --world mm6` (runtime back-face pass: 253 back copies).
`OPENYAMM_REGRESSION_FILTER=actor_model ./build/game/openyamm --headless-run-regression-suite actors`: 53 pass; the 3
failures (guard, mage, ooze) predate this change.

## Floor fix — 2026-10-21

`--hover 0.116799 Death Dead` (flier rule). Before, in world units at tier A: living lowest at -14.1 (suggested hover 0.116799).
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_bh.glb`), written to `export/mm6_bh_floor.glb` and installed as `mm6_bh.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
