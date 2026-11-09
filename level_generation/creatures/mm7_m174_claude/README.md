# MM7 Cleric of the Sun (m174) — Claude 3D model (batch B, 2026-10-20)

Acolyte / Cleric / Priest of the Sun (monsters 217/218/219, descriptors `Cleric Sun A/B/C`, sprite palettes 40/41/42).
Same route as the [Moon Cleric](../mm7_m170_claude/README.md) (humanoid playbook default route, the MM8 Cleric's robe
chains) with the scripts generalised to `creature.json` (garment numbering in `scripts/cfg.py`). **Not installed**
(batch rule). Status: technically complete, agent-reviewed in the viewer; user artistic acceptance pending.
[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m174_claude/review/viewer/).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m174.glb` | runtime GLB: LODs 8,761 / 4,379 / 1,576 / 514 triangles + shadow LODs, tiers `m174_a/b/c` (stole teal / violet / black), head set merged (2080×1024 atlas) |
| `mm7_m174_lod0.glb`, `mm7_m174.blend` | portable LOD0, editable master (textures packed) |
| `actors_binding.yml` | `actors.yml` entries to add later: scale 148.0 (207 px × frame scale 1.2 / 1.678 m posed, rays included), run → Walking, stride 1.395, release 0.483 s (right palm) / cast 0.8 s |

Install later (not run): `python3 tools/install_model.py level_generation/creatures/mm7_m174_claude/export/mm7_m174.glb --world mm7`,
then add `export/actors_binding.yml` to `assets_dev/worlds/mm7/models/actors.yml` and a tier/height regression.

## Model

- **HD masters**: primary `00_three_quarter` = run v3 (the orchestrator's choice; Codex rejected it, but v1/v2 were
  near-frontal with the hands against the robe — a Smart Topology fusion risk); views 01–04 from run 2; head
  turnaround in `references_head/` (gold mask, wavy rays, grey cap).
- **Geometry**: Smart Topology (15.7k, 19 parts; Meshy returned a clean A-pose with the arms at ~45°). The skin piece
  includes the legs under the skirt: they are removed after the auto-rig upload (`strip_legs.py`, 768 vertices) so
  nothing pokes through the robe; the leg bones stay for the robe's leg capsules. Reduced to 8,761.
- **Rig**: source-frame rig; wrists at the gold wrist bands (`creature.json` `wrist_bands`), elbows from Meshy on the
  arm ring centreline (bare arms; no sleeve correction). Rigid open hands (fingers unweighted).
- **Weights**: mantle (garment 13): pelvis/leg weight → B_Spine, arm share ≤ 0.35, then 20 smoothing passes inside the
  mantle shell (Meshy's mixed pelvis/clavicle/arm weights tore its lower edge 4.6× in the attack); mask, rays and
  head band rigid on the head; wrist bands rigid on the forearms; stole and buckle on one robe-chain mix.
- **Robe**: 14 × 4 chains (`robe_sim.py`), DROP_FLAT so the supine corpse's robe lies on the floor instead of
  standing up as a funnel.

## Clips

| Clip | Source |
|---|---|
| Standing / Walking | set Relax Idle / Relax Walk Forward, arms abducted 6° (claws cleared the robe sides) |
| Attack 1.267 s | set Unarmed Cast R Attack 1 (right-hand push as native m174a), planted; release 0.483 s |
| Cast 1.3 s | set Unarmed Cast Dual Attack 2, planted, faced front, wrists ≤ 58°; release 0.8 s (1.10 s before face_forward) |
| Hit 0.5 s | set Unarmed Get Hit F1, planted |
| Death 3.63 s / Dead | Mixamo Standing React Death Backward (staggers, sits, falls onto the back as native m174d), travel halved, floor pass. "Falling Back Death" was tried first: its legs kick up and the robe chains flipped into a funnel |
| Fidget 2.0 s | authored (`FIDGET=raise author_fidget.py`): both arms lift out to the sides, palms up, head tilts back (native fa–fd) |

## Gates (`review/gates_v5.json`)

Arm stretch p99 ≤ 1.98 in every clip (Attack 1.54/1.73, Cast 1.51/1.61); wrist swing ≤ 58°; robe p99 ≤ 1.27 except
Death 3.47 (sitting and falling back); a claw dips 7 cm into the robe/mantle at one Walking frame and one Death frame
(not visible in renders); body ≥ 0 cm in the corpse. Viewer check: 24 switches, no console errors.

## Textures (`scripts/compose_m174.py`)

Body 1K + head 1K. Skin tan (bare forearms); the robe's vertical stripes (lost in Meshy's paint) re-painted by the
angle round the body axis (34 per turn, orange-red on deep red) × Meshy's fine shading; gold graded richer. One tier
region: the stole's front panel (native indices 228–238), ramps from the indexed bitmaps in palettes 40/41/42. The
stole's back stays gold (Meshy painted it so).

Meshy: **30 credits** (Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10).

## Known limits / for review

- The robe's front shows a narrow split at the hem (Smart Topology fold), the inner red visible.
- The rays are smooth tapered spikes, not wavy as in the native.
- Rigid open hands; not checked in game.

## Reproduce

`TOK=<lease> scripts/rebuild.sh all`, texture chain (`export_uploads.py`, `requests/`, `transfer_uv.py`,
`uv_raster.py` UVMap/HeadUV, `bake_ao_natm.py`, `compose_m174.py`), `TOK=<lease> scripts/build_runtime.sh`,
`viewer_tiers.py`, `update_viewer_manifest.py`.

## Revision 2026-10-20 (user review)

- Attack / Cast: `face_forward.py` (after `plant.py`) turns the pelvis, spine, neck and head back toward the front
  per frame; the set's casts and punches turned the head 45–65° to the side. Head yaw is now 0°, and the arm gates
  held or improved.

> **Reduction (2026-10-20, not installed):** [`../mm7_m174_reduce_claude/`](../mm7_m174_reduce_claude/README.md) cuts
> LOD0 8,761 -> 6,305 (LODs 3,152 / 1,134 / 492) with UVs, textures, tiers and clips unchanged; this export stays the
> rollback source.

## Installed 2026-10-20

The reduction (`../mm7_m174_reduce_claude/export/`) is installed through `../mm7_batches/BATCH_B_stage/` (assets_source + runtime copy, bindings in `assets_dev/worlds/mm7/models/actors.yml`). Rollback: `tools/install_model.py level_generation/creatures/mm7_m174_claude/export/mm7_m174.glb --world mm7` (the production export, byte-identical to the reduction's `work/mm7_m174_source_pre_reduce.glb`).
