# MM7 Monk (m290) — Claude 3D model (batch B, 2026-10-20)

Monk / Initiate / Master (monsters 304/305/306, descriptors `Monk A/B/C`, sprite palettes 291/292/293), unarmed
(melee punch). Same chain as the other [batch B](../mm7_batches/BATCH_B.md) casters (settings in `creature.json`).
**Not installed** (batch rule). Status: technically complete, agent-reviewed in the viewer; user artistic acceptance
pending. [Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m290_claude/review/viewer/).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m290.glb` | runtime: LODs 9,331 / 4,665 / 1,679 / 555, tiers `m290_a/b/c` (robe and hood green / slate-violet / red; the white rope, hood lining, skin and sandals unchanged), head set merged |
| `mm7_m290_lod0.glb`, `mm7_m290.blend` | portable LOD0, editable master |
| `actors_binding.yml` | scale 109.6 (189 px / 1.725 m, hood included), run → Walking, stride 1.534, punch impact 0.583 s, cast 0.683 s (right palm) |

Install later (not run): `tools/install_model.py export/mm7_m290.glb --world mm7`, then the binding and a tier/height
regression.

## Model

- **HD masters**: `00` = Codex v2 (A-pose with open hands; the native's folded arms are animated); 01–04 run 2; head
  turnaround run 3 with the hood removed (face and close-cropped hair; the hood is its own geometry).
- **Geometry**: Smart Topology with `pose_mode` empty; 15 clean parts (hood + cowl + top + sleeves, face, skirt, two
  hands, two rope ends, shins, sandals, eyes). Reduced to 9,331.
- **Rig/weights**: source-frame rig; sleeves split from the torso at z 1.16 (connectivity) and made arm-only below it;
  robe 14 × 4 chains; shins and sandals keep Meshy's leg weights; rope ends one chain mix each.

## Clips

| Clip | Source |
|---|---|
| Standing / Walking | set Relax Idle / Relax Walk Forward with the forearms crossed in front of the waist (`fold_arms.py`, native sa/wa), hands hidden in the sleeves (`hide_hands.py`) |
| Attack 1.067 s | set Unarmed Attack R2 (right forward strike), planted, faced front; impact 0.55 s |
| Cast 1.3 s | set Unarmed Cast R Buff 1, planted; release 0.683 s |
| Hit 0.5 s | set Unarmed Get Hit F1, planted |
| Death 2.0 s / Dead | set Relax Lay Down |
| Fidget 2.0 s | authored (`FIDGET=raise author_fidget.py`): arms unfold and rise out to the sides, palms up (native fa–fd) |

## Gates (`review/gates_v5.json`)

Arm stretch p99 ≤ 1.86 except Attack right 2.22 and Cast right 2.21 (the striking shoulder); Death 2.45 lying. Wrist
swing ≤ 58°. Robe p99 ≤ 1.43 except Death 3.57. Viewer check: 24 switches, no console errors.

## Textures (`scripts/compose_m290.py`)

Body 1K + head 1K. One tier region, the robe and hood (native green cloth indices), ramps from the indexed bitmaps; the
pale hood lining, rope and sandals kept out of the mask.

Meshy: **30 credits** (Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10).

## Known limits / for review

- Folded arms: the hands are shrunk into the sleeves (bone scale) rather than tucked into the opposite sleeve.
- In the corpse the bare shins and sandals show below the robe (Relax Lay Down; the native throws the arms up and
  falls back).
- The hood's tip is a little more pointed than the native's.

## Reproduce

`TOK=<lease> scripts/rebuild.sh all`; texture chain (`export_uploads.py`, `requests/`, `transfer_uv.py`,
`uv_raster.py` ×2, `bake_ao_natm.py`, `compose_m290.py`); `TOK=<lease> scripts/build_runtime.sh`; `viewer_tiers.py`,
`update_viewer_manifest.py`.

## Revision 2026-10-20 (user review)

- Attack / Cast: `face_forward.py` (after `plant.py`) turns the pelvis, spine, neck and head back toward the front
  per frame; the set's casts and punches turned the head 45–65° to the side. Head yaw is now 0°, and the arm gates
  held or improved.
- Standing / Walking: `hide_hands.py` keys the hand bones' scale (0.03 when the wrist is within 8 cm of its folded position, full beyond 22 cm), so the hands sit inside the sleeves while the arms are folded and grow back as they unfold in the other clips.
- Attack: Unarmed Attack R2 (a straight forward strike) replaces R1, a haymaker whose 100° chest twist swung the arm overhead once the trunk faced front; impact 0.55 s.

## Reduction (2026-10-20, awaiting review)

A reduced body (LOD0 9,331 -> 7,081, no retexture, clips and textures unchanged) is in
[`../mm7_m290_reduce_claude/`](../mm7_m290_reduce_claude/README.md): install its `export/mm7_m290.glb` instead of this
project's export if accepted.
- Feet: `flatten_feet.py` (from the Warlock; before `robe_sim.py`, every clip except Death/Dead) levels the grounded
  feet and lifts sunken ankles to rest height: the planted set clips left the shoes 3.5-10 cm under the floor. Soles
  now sit within 1 cm of it.
- Attack head zig-zag (user review): Unarmed Attack R2 bends the chest ~75 degrees forward and rolls it ~150 degrees
  within three frames (a diving lunge); after `face_forward.py` the head zig-zagged. Attack is now Unarmed Cast R
  Attack 1 (the right-palm push, as the native's glowing palm strike; impact 0.483 s). `smooth_bones.py` (Attack and
  Cast, after `caster_timing.py`) Gaussian-smooths the WORLD orientation of the spine, neck and head over 1.5 frames.
  Smoothing local rotations made it worse, because the head then followed the chest's swing. Worst frame-to-frame
  change: head 14.7 -> 0.8 deg, chest 15.9 -> 3.2 deg.

## Installed 2026-10-20

The reduction (`../mm7_m290_reduce_claude/export/`) is installed through `../mm7_batches/BATCH_B_stage/` (assets_source + runtime copy, bindings in `assets_dev/worlds/mm7/models/actors.yml`). Rollback: `tools/install_model.py level_generation/creatures/mm7_m290_claude/export/mm7_m290.glb --world mm7` (the production export, byte-identical to the reduction's `work/mm7_m290_source_pre_reduce.glb`).
