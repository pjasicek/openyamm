# MM7 Dragonfly (`m186`) reduction — 2026-10-21

User: "all 3 are good, reduce tris". [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) default route,
no-retexture branch, with the scripts of [mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md) (parent-fixed
`reduce_ladder.py`, floor contacts, stretch, drift, dark-sliver and LOD checks). No Meshy credits. Not installed.

## Source

The accepted [mm7_m186_claude](../mm7_m186_claude/README.md) export was reduced inside Blender (edit-mode Decimate,
15,522 → 8,168), which the playbook forbids (it slides UVs across seams). The ladder therefore starts again from the
**unreduced** UV master: `mm7_m186_claude/work/uv_full.blend` (copy of `uv_master.blend`, clips re-keyed with the
current `anim_dfly.py` so Death/Dead keep the accepted head-lifted corpse) → `export_glb.py` → material contract →
`prepare_actor_glb.py` → `region_variants.py` = `work/mm7_m186_source.glb` (sha256 `f0c8651d…`; body 14,188 +
wings 1,334 = 15,522 triangles, the same textures, ramps and clips as the accepted export).

`import_source.py` (REA_NODE=Dragonfly): weld 14,514 → 134 open edges, 11 duplicate faces merged on the
double-sided body (14,177 triangles), no coincident vertices with other weights. Height 0.515 m: limits p99 1.55 mm,
max 7.7 mm.

## Body ladder

Pieces (`scripts/dfly_groups.py`): the main body (6,811 faces; 2,885 of them Head-dominated), the two compound eyes
(346 faces, **kept exactly**: painted eyes tear under collapse), and about 60 small separate pieces (crest spines,
bristles, mandibles, claw prongs: 7,020 faces, half the mesh). The small pieces set the floor: below about 55 % their
tips retract (p99 and max jump), so they get their own ratio (`REA_GROUPS`), the head its own (`REA_PROTECT_FACES`).

| config (small / head) | step | triangles | p99 / max mm | IoU | SSIM |
|---|---|---:|---|---|---|
| 0.45 / 0.7 | r60 / r55 / r50 | 8,505 / 7,795 / 7,087 | 1.52 / 1.55 / 1.64 (max ≤ 4.8) | 0.978–0.970 | 0.992–0.987 |
| 0.60 / 0.6 | r60 / r55 / r50 / r45 | 8,505 / 7,797 / 7,087 / 6,489 | 1.19 / 1.42 / 2.06 / 8.62 | 0.981–0.895 | |
| 0.55 / 0.6 | r55 / r50 / r45 | 7,795 / 7,087 / 6,377 | 1.35 / 1.73 / 3.48 | 0.977–0.952 | |
| **0.55 / 0.55** | r55 / r53 / **r51** | 7,793 / 7,509 / **7,227** | 1.33 / 1.42 / **1.52** (max 4.24) | 0.977 / 0.974 / **0.973** | **0.987** |
| 0.50 / 0.6 | r51 | 7,229 | 1.51 / 4.77 | 0.972 | 0.988 |
| 0.35 / 0.7 | r55 … r35 | 7,795 … 5,021 | 1.91 … 8.76 | fail | |
| 0.25 / 0.7 | r55 … r35 | 7,795 … 4,959 | 2.43 … 2.67 (max 6.33) | fail | |

**Pick: 0.55 / 0.55 at r51, 7,227 triangles** — the lowest step within the p99/max limits. The 0.98 silhouette-IoU
gate is not met (0.973): the 512-px silhouettes of this spiky creature differ only by one-pixel outline jitter along
the crest spines and bristles (`review/ladder_body`; even the 0.60/0.6 r60 step at p99 1.19 mm only reaches 0.981).
Close-ups (`review/close/sheet_s55h55.png`: head side/front, bristles, crest, claw, abdomen in the lunge, back,
corpse; source / r55 / r53 / r51) show no visible difference, so the step is accepted visually as for the goblin,
hydra and Flying Eye reductions.

Checks on r51: no face stretches over 20× in any clip (`stretch_check.py`); texture drift 4 faces over 40 (0.7 cm²,
no lock round needed); 136 dark-sliver faces flagged, all on the body under the stacked crest spines, and the four
worst spots render identically to the source from above and below (`review/spots/sheet_dark.png`).

## Wings

The alpha-blended wing node (`DragonflyWings`, four flat plates, no LODs) ran its own ladder (limits scaled to the
0.95 m span: p99 2.9 mm, max 14 mm):

| step | triangles | p99 / max mm | IoU | |
|---|---:|---|---|---|
| **r50** | **666** | 2.11 / 2.68 | 0.973 | **pick**: textured and clay views match the source |
| r35 | 466 | 2.80 / 4.55 | 0.942 | outline narrows in the top view |
| r25 | 332 | 4.49 / 9.27 | 0.890 | creased, twisted tips |

`review/close/sheet_wings.png` (source / r50 / r35 / r25).

## Build and result

`export_cand.py` (Cand_51) → `swap_lod0.py` → `floor_contacts.py` (Death/Dead, 41 vertices / 15 points) →
`build_lods.py` (0.5 / 0.25 / 0.125, 4 influences, contacts protected) → `mm7_m186_claude/scripts/shrink_shadow_lods.py`
(≤ 1 mm) → `carry_variants.py` (7 LOD/shadow primitives) → wings: `export_cand.py` (Cand_50) → `swap_lod0.py
… DragonflyWings`.

| | body LOD0 | LOD1 | LOD2 | LOD3 | wings |
|---|---:|---:|---:|---:|---:|
| unreduced source | 14,188 | | | | 1,334 |
| accepted export (Blender decimate) | 7,502 | 3,748 | 1,874 | 920 | 666 |
| **this reduction** | **7,227** | **3,612** | **1,805** | **889** | **666** |

[`export/mm7_m186.glb`](export/mm7_m186.glb): 6.1 MB, sha256 `b5a69ca9b5a28bbe63d289a54ba056b020ea8a86c86c98719f61179b2bb64659`;
3 variants on all 8 body primitives, the wing material unchanged, 4 images, 6 clips.

- `check_winding.py`: 0 inverted closed parts.
- `lod_check.py` (`work/lod_check_r51.json`): every LOD keeps the rest bounds (LOD3 top 0.7 mm lower); Death and
  Dead rest at 2.1 mm at every LOD; Fly dips at most 5.8 mm below the origin by design; no stretched faces.
- Viewer ([review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m186_reduce_claude/review/viewer/)):
  source and reduced per tier; `run_creature_review.py check`: 36 switches, no console errors. Tier shots
  `review/shots/tiers_sheet.png`: green / blue / red crests identical to the source.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m186_reduce_claude/export/mm7_m186.glb --world mm7
```

The binding in [mm7_m186_claude/README.md](../mm7_m186_claude/README.md) is unchanged (same clips, sockets and
variant names). Rollback / unreduced source: `work/mm7_m186_source.glb`.
