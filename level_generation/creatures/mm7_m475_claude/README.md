# MM7 Blaster Guy (m475): Tolberti / Robert the Wise / Blaster Guy C — Claude humanoid route, batch L

MM7 batch L model 3 ([BATCH_L.md](../mm7_batches/BATCH_L.md)). Monsters 457 Tolberti, 458 Robert the Wise, 459 Blaster
Guy C (descriptors `zBlasterGuy A/B/C`). **Installed 2026-10-21** (the user asked for it after the batch; the batch
itself stopped at exports): install commands and the `actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart
Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10). User artistic acceptance is not
recorded.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m475_claude/review/viewer/`) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png) ·
[clip candidates (G1)](review/g1_candidates.png) · [clay clips](review/clay_v5_three_quarter.png) ·
[gates](review/gates_v5.json) · blaster renders `review/blaster_*.png`

| File | What |
|---|---|
| `export/mm7_m475.glb` | body: one skinned mesh `M475` on one merged body+head material (2080×1024 atlases), LODs **6,722** / 3,359 / 1,202 / 406 tris (LOD0 halved on the textured master by `halve_lod0.py` (user, 2026-10-20: "reduce tris now"; collapse before the armature, UV-seam vertices weighted 0.8, small pieces kept whole, the front of the head blocked completely (user review: a partial protection merged the mouth, lips and brows away), the hair reduces; `clamp_uv.py` takes back the LOD builder's u = -0.00001 at the atlas edge before the head merge)) (incl. the 296-tri blaster before the split) + shadow LODs, 8 clips, bones `Blaster` (right hand) and `Socket_Muzzle` |
| `export/mm7_m475_blaster.glb` | blaster attachment on node `Blaster` (296 / 148 / 51 / 26 tris) |
| `export/mm7_m475_lod0.glb`, `export/mm7_m475.blend` | portable LOD0 (blaster included), editable master |
| `textures/` | body and head 1K sets, class maps, blaster maps (`m475_blaster_*`, from `textures/props/blaster.png`) |

## Identity and tiers

Native `m475*` (124 frames). A stern bearded man with shoulder-length brown hair: a black cape to the ankles with a tall
two-pointed stand-up collar, a black shirt with puffed sleeves, a purple vest with white V-bands and padded white
shoulders, a studded black belt, black trousers in knee boots with silver bands, a retro blaster pistol in his right
hand. **All three descriptors draw sprite group m476 in palette 527**, so Tolberti and Robert the Wise look the same
as Blaster Guy C natively (checked: one standing frame set, one palette, no tint): one look, **no colour variants** and
no region mask; the binding has no `skin`.

## Model, rig and weights

- HD masters (Codex): primary after one correction (arms ~30° instead of 40°, clear of the cape), side views,
  `blaster.png` (side view), head turnaround (profile kept a slight three-quarter bias).
- Smart Topology (`pose_mode` empty, keeps the fist): 28 pieces, 15.8k tris: one shell for the vest, cape, collar and
  left sleeve; head + hair; legs + boots; right sleeve; both hands (right a fist); belt, cuffs, buttons, studs, buckles, eyes.
- Chain of the batch-B Warlock (`mm7_m426_claude`, settings in `creature.json`): Meshy auto-rig joints, wrists at the
  cuffs, cloned source frames, hands continuing the forearm (`HAND_FROM_FOREARM`, a fist's PCA frame was 30–41° off),
  `weights_robe.py`: the shell below 0.92 m is cape only (the legs are their own piece) and rides **12 chains × 4 bones
  across the cape's own angular sector** (−92…+95° from the back; `cape_sector`, new); the cape behind the arms loses
  its arm weight, with per-side arm radii (the puffed left sleeve is fused into the shell: 12 cm; the right sleeve is its
  own piece: 6 cm, and never cape) — the first rule took the sleeve backs to the chest (arm stretch 10–18×).
  Reduced after weighting to 12,855 (head, hair and hands kept).
- Blaster (`make_blaster.py`, `blaster_texture.py`): a local hard-surface prop (296 tris) fitted to the reference
  silhouette (0.31 m, grip at the rear, raked 15°), textured by a planar side projection of `blaster.png`; seated in the
  right fist's grip tunnel (`grip_from_fist.py`, enclosure 1.0, 13.7 mm clearance) by `seat_blaster.py`: grip on the
  tunnel axis, barrel along the hand (20° off the forearm at rest: it hangs down along the leg as in the native).
  User review (2026-10-20): the fist held only the top of the grip and the raked grip stuck out below the fingers;
  `regrip_blaster.py` turns the gun 25° about its cross axis (the grip along the fingers) and raises it 5 mm.

## Clips

| Clip | Source |
|---|---|
| Standing 2.0 s / Walking 0.8 s | set Relax Idle / Relax Walk Forward, arms out 8°; the gun hangs down at his right side (native m475sa/w) |
| Attack 1.067 s | set 1Hand Pistol Attack R1, planted and faced forward; `aim_forward.py` (user review 2026-10-20: the set aimed up to 40° to his right) turns the right upper arm at the shoulder so the barrel points straight ahead while the arm is raised (≤ 6° off), caps the recoil kick at 30°, and (second review) eases the arm from the raise straight into the shot pose by 0.30 s and holds it until the shot (the set's raise overshot 21 cm and sank back: up-down-fire), and (third and fourth review) `ground_clips.py` pins both feet with leg IK and lets the pelvis sink but not rise (the set rose 4 cm onto the toes from 0.30 s and the feet slid 6.6 cm); fires (native m475aa–ah); impact **0.62 s** |
| Cast 1.3 s | set Unarmed Cast L Attack 1, planted, faced forward: the left hand thrusts out at **0.567 s** (Power Cure, Hour of Power; no native cast frames) |
| Hit 0.5 s | set Unarmed Get Hit F1, planted; `ground_clips.py` pins the feet (it hopped 5 cm and slid 11 cm) |
| Death 3.63 s / Dead | Mixamo Standing React Death Backward, travel halved: falls on his back (native m475da–dd), cape spread under him |
| Fidget 2.33 s | set 1Hand Pistol Reload R1, planted, eased from and back to Standing: both hands at the gun (native m475fa–fd) |

## Gates (`review/gates_v5.json`, final reduced mesh)

- Halved LOD0 (`halve_lod0.py`, 2026-10-20, face blocked), edge stretch p99 / max, whole mesh: Standing 1.15 / 1.98,
  Walking 1.25 / 3.65, Attack 1.57 / 4.76, Cast 1.56 / 10.6, Hit 1.74 / 7.6, Fidget 1.69 / 9.4 (the full master: p99
  1.64-1.81, peaks up to 16.0 in the cape). Head 3,311 of the 6,426 body triangles. Viewer, winding and textured face
  close-ups rechecked.

Arm stretch p99 ≤ 1.78 and max ≤ 2.84 in every clip (Attack right arm 1.75 / 2.26 after the aim, hold and foot fixes);
hands rigid (1.00); wrist swing ≤ 39° (Death 42°); hand in body ≤ 0.08 cm. Cape (robe chains) p99 ≤ 1.46 except
**Death 5.66** (the cape flattened under the lying body, max 10.6 at the fall). Robe floor: lowest point −2.8 cm in
Death. Viewer: 8 clips, no console errors. `check_winding.py`: 0 inverted closed parts (body and blaster). Textured
EEVEE frames of Standing and the Attack inspected (`work/r_glb/`). Not checked in game (optional for batch L).

## Installed (2026-10-21, user request after the batch)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m475_claude/export/mm7_m475.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m475_claude/export/mm7_m475_blaster.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `zBlasterGuy B` and `zBlasterGuy C`, identical):

```yaml
# MM7 Blaster Guy m475 (457 Tolberti, 458 Robert the Wise, 459): blaster pistol attachment, shot from the muzzle.
- descriptor: zBlasterGuy A
  model: worlds/mm7/models/mm7_m475.glb
  scale: 106.2
  yaw_offset: -1.570796327
  animation:
    cast: Cast
    run: Walking
    stride_length: 1.637
    run_stride_length: 1.637
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    sockets:
      muzzle: Socket_Muzzle
      palm_l: {node: B_L_Hand, offset: [0.0, 0.08, 0.0]}
    events:
      attack_melee: {impact: 0.62}
      attack_ranged: {impact: 0.62, release: muzzle}
      cast: {impact: 0.567, glow: [palm_l], release: palm_l}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  attachments:
  - model: worlds/mm7/models/mm7_m475_blaster.glb
    node: Blaster
```

Scale = native standing silhouette 194 px (collar tips to soles, frame scale 1.0) / 1.827 m Standing height. Speed 240
plays the walk at 1.1× its natural 2.05 m/s; the run threshold (255) is not reached.

## For the user to review

- The cape lying under the corpse is flattened by the robe simulation (stretch p99 5.7 in Death).
- The blaster is a local low-poly prop textured from the HD reference; its trigger guard and side detail are paint.
- Neck (user review 2026-10-20): Meshy painted the head atlas's bottom rows dark and the body atlas's neck paler than
  the face; `compose_m475.py` (`neck_match`) repaints the band with the head's neck skin and matches the body neck's
  tone. A stubble line at the lower edge of the beard is Meshy's beard paint and is kept.
- The cast (left-hand thrust) is an invention: the native has no cast frames.

## Replay

Claim the project, then `TOK=<lease> scripts/rebuild.sh rig` (with `regrip_blaster.py`) and `... anim` (rig_v5, with
`aim_forward.py`), texture chain once
(`export_uploads.py`, Meshy `requests/retexture_v1.json` and `head_retexture_v1.json`, `transfer_uv.py` (UVMap, then
HeadUV), `uv_raster.py` ×2, `bake_ao_natm.py`, `compose_m475.py`, `blaster_texture.py`), then
`TOK=<lease> scripts/build_runtime.sh` and `update_viewer_manifest.py` (viewer GLB = `export/mm7_m475_lod0.glb`).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: walking lifts every foot by +3.1.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m475.glb export/mm7_m475.glb --lift-joints Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Walking`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m475.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h12`](../gait_rollout_20261031/h12/README.md) appended Jog (Unarmed-Run-Forward legs, 0.72 s,
arms and blaster from Walking with a stronger swing and bent elbows) to the installed
`assets_source/worlds/mm7/models/mm7_m475.glb` and installed it (existing clips, meshes, skins and materials
byte-identical). The cape chains (`Robe_*`) are simulated on the jog with the numpy port of this project's
`robe_sim.py` (`h12/scripts/cloth_sim.py`, h08's, chains dumped from `export/mm7_m475.blend`). Bindings
(`h12/bindings.yml`): run: Jog, run_stride_length 3.2072 (the walk stays; the chase at 4.52 u/s is a run pace).
Rebuild: `level_generation/creatures/gait_rollout_20261031/h12/scripts/rebuild.sh m475` (from `h12/work/mm7_m475_pre_gait.glb`, the
rollback source). A far-LOD repair rerun, a floor fix or any re-export of this model must re-graft these clips: copy the
new source over `h12/work/mm7_m475_pre_gait.glb` and rerun the rebuild, then install with `tools/install_model.py`.
