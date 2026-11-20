# MM7 Cleric of the Moon (m170) — Claude 3D model (batch B, 2026-10-20)

Acolyte / Cleric / Priest of the Moon (monsters 214/215/216, descriptors `Cleric Moon A/B/C`, sprite palettes
37 green / 38 blue / 39 red). Built with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) default route
(source-frame rig, humanoid-set clips, numeric gates) and the robe solution of the accepted MM8 Cleric
([`mm8_m460_claude`](../mm8_m460_claude/README.md): verlet robe chains with leg capsules), carried through
[batch B](../mm7_batches/BATCH_B.md). **Not installed** (batch rule): everything stays in this project.

Status: technically complete and agent-reviewed in the viewer; user artistic acceptance pending.
[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m170_claude/review/viewer/) (all three tiers, eight
clips, native frames beside each clip).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m170.glb` | runtime GLB: LODs 9,883 / 4,930 / 1,757 / 570 triangles, shadow LODs, three tier variants `m170_a/b/c` (`KHR_materials_variants`, region mask + ramps), head set merged into one 2080×1024 atlas material |
| `mm7_m170_lod0.glb` | portable animated LOD0 (separate body and head materials) |
| `mm7_m170.blend` | editable master (rig, all clips, textures packed) |
| `actors_binding.yml` | the `actors.yml` entries to add later |

Install later (not run):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m170_claude/export/mm7_m170.glb --world mm7
```

then add `export/actors_binding.yml` to `assets_dev/worlds/mm7/models/actors.yml` (scale 125.8, run → Walking, palm
sockets, events) and an actor regression like `mm6_cleric_actor_model_tiers_share_the_native_height`.

## Model

- **HD masters** (`references_hd/`, Codex, two runs; gate passed): primary `00_three_quarter` = run v1 (front-left
  three-quarter, chosen over Codex's own pick v2 which was nearly frontal), views 01–04 from run 2. Head turnaround in
  `references_head/`.
- **Geometry**: Meshy Smart Topology (15.3k triangles, 57 loose parts) kept as returned; parts labelled into garments
  (`scripts/prepare_rig.py`): skin, robe top + sleeves, skirt, helmet + hair, eyes, cheek plates, collar, chest chain,
  rope ends, crescent, banners, back rods + beads. Reduced after weighting to 9,883 (`reduce_rigged.py`: face skin
  and small pieces protected).
- **Rig** (126 bones): humanoid-set source frames (`build_rig.py`); joints from Meshy's auto-rig (person-only upload,
  no crescent/banners) with two corrections (`joints_fix.py`): the wrist at the end of the slender wrist tube of each
  hand shell (the shells carry an 8 cm forearm stub into the sleeve), the elbow on the shoulder→wrist line at 0.54
  (inside the bell sleeves Meshy's elbow and the sleeve centreline gave a 65° rest bend). Hands are rigid open claws
  (the native never curls them; Smart Topology fused the fingers). Forearm/upper-arm twist bones.
- **Robe**: 14 chains × 4 bones from the waist (`weights_robe.py`), simulated per clip (`robe_sim.py`, m460 verlet:
  yaw-only rest bell, leg capsules — shrunk for this legless robe, which bulged at the hips with m460's radii —
  neighbour spacing, floor). **Banners**: 2 × 2 chains × 3 bones from the rods (`banner_rig.py`), same simulation
  rooted on the chest; they sway and, in the death, drop off the rods onto the floor (rigid, they stood up in the air).
  Crescent, rods, beads and chest chain are rigid on the chest; helmet/eyes rigid on the head; hair blends head →
  neck → chest.
- **Weights**: Meshy's transfer plus rules: the robe torso below the armpit (connectivity: below z 1.065 the robe top
  splits into torso + two sleeves 1 cm apart) loses its arm weight (it tore 8× when the arm rose); rope ends take one
  chain mix per cord.

## Clips (30 fps keys; chosen before modelling, `review/g1_sheet.png`, `review/g1b_sheet.png`)

| Clip | Source | Notes |
|---|---|---|
| Standing 2.0 s | set Relax Idle | upright, arms relaxed |
| Walking 0.8 s | set Relax Walk Forward | stride 1.371 m (natural 1.71 m/s; tiers play 0.75–0.93×) |
| Attack 1.267 s | set Unarmed Cast L Attack 3 | left-hand throw (native m170a: left hand up, flung forward), legs planted on Standing (`plant.py`), 0.27 s ready ease; release 0.483 s at peak palm speed |
| Cast 1.3 s | set Unarmed Cast Dual Attack 2 | two-handed push, planted, faced front; release 0.8 s at full reach (1.10 s before face_forward). Mixamo "Standing 2H Magic Attack 01" (the MM8 Cleric's cast) was tried first: its overhead gather tore the sleeve armpits (p99 2.9, wrist 84°) and the native never raises the arms overhead |
| Hit 0.5 s | set Unarmed Get Hit F1 | planted |
| Death 2.0 s / Dead | set Relax Lay Down | kneels, lies down (native: sinks and collapses); travel halved, floor pass |
| Fidget 2.0 s | authored on Standing (`author_fidget.py`) | both claws meet in front of the chest, head bows (native fa–fd) |

All one-shots ease from/to Standing frame 0 (`caster_timing.py`); wrist swing soft-limited to 58° (`wrist_limit.py`).

## Gates (`review/gates_v5.json`, every half frame of the final rig)

| | arm stretch p99 (L/R) | wrist swing | robe p99 | other |
|---|---|---|---|---|
| Standing / Walking / Fidget | ≤ 1.78 | ≤ 38° | ≤ 1.38 | claws in body ≤ 1 cm (fidget, hands meeting) |
| Attack | 2.27 / 1.85 | 49° | 1.38 | |
| Cast | 1.92 / 1.87 | 58° | 1.33 | the claws brush the banners at the wind-up (cloth pushed aside, no penetration) |
| Hit | 1.98 / 1.83 | 27° | 1.25 | |
| Death | 2.80 / 1.91 | 57° | 3.88 | kneeling folds the robe (robe max 5.5×), left claw 8 cm into the robe while kneeling on it; body ≥ −5 mm |

Viewer: `tools/run_creature_review.py check` — 24 tier/clip switches, no console errors; playback in
`review/playback/`, close-ups in `review/shots/` (`stand_q{a,b,c}`, `back_{a,b,c}`, death `d1`–`d4`).

## Textures (`scripts/compose_m170.py`)

One shared 1K body set + 1K head set (Meshy body retexture with Meshy UVs transferred back, head retexture on our own
head UVs), AO graded in, ORM red = specular class mask, metallic 0. Skin repainted to one ashen grey albedo × Meshy's
fine shading; gold re-graded richer (Meshy's read pale cream). Region mask R = robe (all non-gold texels of the robe
garments), G = banners; ramps per tier from the ORIGINAL indexed bitmaps in palettes 37/38/39 (index ranges from
`../mm7_m170/variants.json`), gain 1.35. Material classes in `textures/m170_material_classes.png`.

## Reproduce

`TOK=<lease> scripts/rebuild.sh all` (prepare → joints → rig → weights → banners → clips → wrist limit → timing →
twist → robe and banner sims → reduction → gates), texture chain once (`export_uploads.py`, Meshy jobs in
`requests/`, `transfer_uv.py`, `uv_raster.py` ×2, `bake_ao_natm.py`, `compose_m170.py`), then
`TOK=<lease> scripts/build_runtime.sh` and `viewer_tiers.py` + `update_viewer_manifest.py`.

Meshy: **30 credits** (Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10); no paid animation.

## Known limits / for review

- Hands are rigid open claws (no finger motion).
- The corpse lies on its side (Relax Lay Down), one rod of the back frame points up; the native corpse is a flat heap.
- The Attack's wind-up turns the chest ~45° and bows the head (the set's lunge throw, legs planted).
- Not checked in game (optional for the batch; no install).

## Revision 2026-10-20 (user review)

- Attack / Cast: `face_forward.py` (after `plant.py`) turns the pelvis, spine, neck and head back toward the front
  per frame; the set's casts and punches turned the head 45–65° to the side. Head yaw is now 0°, and the arm gates
  held or improved.

## Reduction (2026-10-20)

A reduced version (LOD0 9,883 -> 7,179, no retexture) is in [`../mm7_m170_reduce_claude/`](../mm7_m170_reduce_claude/README.md),
not installed and awaiting review; this project's export stays its rollback source.

## Installed 2026-10-20

The reduction (`../mm7_m170_reduce_claude/export/`) is installed through `../mm7_batches/BATCH_B_stage/` (assets_source + runtime copy, bindings in `assets_dev/worlds/mm7/models/actors.yml`). Rollback: `tools/install_model.py level_generation/creatures/mm7_m170_claude/export/mm7_m170.glb --world mm7` (the production export, byte-identical to the reduction's `work/mm7_m170_source_pre_reduce.glb`).
