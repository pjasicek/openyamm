# MM6 cobra (cob) — 3D model, 2026-10-08

Cobra / King Cobra / Queen Cobra (descriptors 493–495, Cobra A/B/C; Abandoned Temple `6d02.blv`), installed as
`assets_dev/worlds/mm6/models/mm6_cob.glb`, bound in `assets_dev/worlds/mm6/models/actors.yml` (opt-in via
`debug.actor_models=true`). Review viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_cob_claude/review/viewer/>.

| Item | Value |
|---|---|
| References | Codex HD views `references_hd/` (front, back, left, right, three-quarter; 1536×1024), native profile pose: ground body straight behind, front third raised, hood spread |
| Model | Meshy `multi-image-to-3d` (meshy-7.1, four views, textured, 2k, remesh 20k): 20,812 tris, one closed mesh |
| LOD0/1/2/3 | 6,000 / 2,996 / 1,073 / 353 triangles |
| Rig | 27 bones: Root at the bend, Tail_01–20 along the ground, Spine_01–05 up the neck, Head |
| Clips | Standing 3.0 s loop, Walk 0.75 s loop, Attack 0.75 s, Hit 0.9375 s, Death 0.75 s, Dead, Fidget 0.75 s |
| Tiers | shared skin; region mask R body (incl. belly plates and bands), G hood-front scales, B spectacle; ramps from palettes 677/678/679 |
| Scale | 130 (A); B/C via `scale_reference` (frame scales 0.60/0.70); origin at the neck base |
| Meshy credits | 30 of 100 |

## Pipeline (scripts/)

1. `prepare_cob.py` — import, weld, drop specks, rig frame (1 m raised height, ground z 0, head −Y, neck base at the
   origin) → `work/hd_base.blend`.
2. `rig_cob.py` on `hd_base` → `work/rig_20k.blend` (only for the next step), then `reduce_bent.py` → bent-pose
   reduction to 6k (see below), `bake_reduced.py` → fresh unwrap (smart project 45°: 29% coverage, no overlap) and
   base colour / roughness / normal baked from the 20k mesh (cage 8 mm, rays 4 cm) → `work/hd_reduced.blend`.
3. `rig_cob.py` on `hd_reduced` → `work/rig_v1.blend` + `work/rig.json` (centreline joints, body radius per joint).
4. `anim_cob.py` → `work/anim_v1.blend`; checks: printed self-contact margin and floor, `check_stretch.py`,
   `clip_sheet.py`.
5. `dump_uv3d.py`, `bake_creature_ao.py` (→ `cob_ao_2k.png`), `grade_basecolor.py --ao` on `cob_basecolor.png`,
   `compose_cob.py` (masks, classes, MR with AO in R, normal, ramps), `build_runtime.sh --install`,
   `viewer_tiers.py`, `update_viewer_manifest.py`.

## What was specific to a snake

- **Rig and clips from a curve.** Each frame defines the centreline (tail branch on the ground at body-radius height
  with a curvature profile; neck branch by pitch/yaw per segment, floor rule) and every bone is fitted to it.
  Weights blend by arc position along the centreline (no heat weights). The coil is an inward spiral whose radius
  drops by one body width per turn, so it cannot cross itself.
- **Tail frames are locked to world up.** Transporting frames from the upright root rolled the coiled tail onto its
  side (belly scutes on top).
- **Reduce in a bent pose.** Rest-pose collapse decimation removed the ring loops of the straight body and tail,
  leaving slivers that folded into a flat blade when the body bent (seen only in motion). `reduce_bent.py` decimates
  the mesh posed in a tight wave + coil, carrying each vertex's rest position as an interpolated attribute.
- **Ramps by histogram matching.** The native palette is dark-skewed and the Meshy texture is not, so a linear
  luminance-to-palette ramp needed absurd gains. Each tier's target texture maps a texel's luminance percentile in its
  region to the native colour at that percentile (×1.35 albedo); `region_variants.fit_ramps` fits the 16 stops
  (mean error 6–9 levels of 255 on body/hood, 17–19 on the small spectacle region).

## Triangle budget

The first install (10k) kept everything above 0.74 m at full density, which also caught the hood: 5.4k of the 10k
triangles sat in the hood and upper neck, 2.3k in the whole body and tail. `reduce_bent.py` now protects only the
head itself (snout, fangs, eyes) and sharp edges; the hood's scales live in the baked texture and normal map.
Same-camera head, hood-back and full views plus tail close-ups in the slither and coil: 7k and 6k match 10k;
5.5k shows a slight crease mid-tail in motion; 4.5k breaks the bake (holes on the belly) and facets the hood outline.

## Known limits

- LOD1–3 come from `build_actor_lods.py` (rest-pose decimation), so the distant LODs may show the tail blade
  while slithering.
- A small bump at the bend when the neck lies flat (Dead).
- Eyes are not a separate class (they stay in the body region); the material class map has skin, tooth, mouth only.
