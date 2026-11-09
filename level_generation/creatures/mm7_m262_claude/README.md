# MM7 Harpy (m262) — Claude project

Batch G, model 3 ([batch file](../mm7_batches/BATCH_G.md)), built in parallel with the other batch-G models (user
override of the one-at-a-time rule, 2026-10-20). Descriptors 283 Harpy (palette 263, green), 284 Harpy Hag (264,
violet), 285 Harpy Queen (56, magenta). **Exported, not installed** (batch rule). Technically complete, pending user
review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m262_claude/review/viewer/`) · [viewer shots](review/shots/) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/) · [G1 clip choice](review/g1/G1.md)

| Item | Value |
|---|---|
| Exports | `export/mm7_m262.glb` (body + wings + tail, LODs, shadow LODs, 3 tier variants, head merged), `export/mm7_m262_sword.glb` (curved knife attachment on node `Sword`); editable master `work/rig_v6.blend` |
| Triangles | LOD0/1/2/3 10,290 / 5,139 / 1,844 / 607 (incl. the 700-triangle knife before the split): body 7,691 after weighting (head and hands protected), wings 1,899, knife 700 |
| Mesh | Smart Topology 15k of the HD three-quarter master (v3, wings raised clear of the arms): body shell with feathered thighs, bare bird legs, hands with forearms, bracers, hair shells and strands, eyes, waist band; wings = two sheets + 70 feather cards; 17 tail feather cards. Nothing removed |
| Rig | 52 `B_*` bones cloned from the humanoid set + twist bones; Meshy's auto-rig for the trunk and arms (elbows and wrists from Meshy); **bird legs** on the leg chain from the mesh (`leg_joints.py`): Thigh = hip -> hidden knee, Calf = knee -> hock (the drumstick, end of the feathers), Foot = hock -> ball (the tarsus), Toe0 = the toes; `B_Tail` for the tail cards (`tail_rig.py`); wings `Wing_<s>_1..3` on B_Spine2 (`wings_rig.py`, wrist at 62 % of the leading edge) |
| Weights | Meshy + shoulder fade + jaw free; leg vertices re-weighted along the bird chain (nearest segment, 5 cm joint blends); hair, band and tuft copy the skin without arm weight; bracers copy the skin with the arm; tail rigid on `B_Tail`; wings by span position (B_Spine2 between the shoulder blades) |
| Clips (30 fps) | **Walking** = the flight loop (1.0 s, native wa..wh): authored over Standard Idle frame 0, trunk 15 deg forward, tucked bird legs with a small alternating kick, knife carried at the right side pointing up/forward, left arm forward, tail sway, wing beat (top at wa, bottom at wc..wf). **Attack** (1.83 s, blow 0.983 s): Mixamo Sword And Shield Slash (2) arms and trunk (planted), talon kick peaking at the blow, one big wing beat. **Hit** (0.5 s): set Unarmed get-hit F1 trunk and arms, legs flinch, wings flare. **Death** (2.2 s): Mixamo Falling Back Death, legs drawn up, tail folded, wings laid flat on both sides (searched corpse pose); **Dead** holds it. Every one-shot eases from and to the flight pose (`flight_blend.py`) |
| Textures | body 1K (Meshy retexture from the four HD views, UVs transferred) + head 1K (head retexture from the head turnaround); skin repainted, AO graded; ORM red = per-class specular mask. Two regions: R = the teal flight feathers, G = the teal metal of the bracers and bodice band; ramps by palette-index correspondence (tier-A luminance order) from palettes 263/264/56 |
| Meshy credits | **45 of 100**: Smart Topology 5, auto-rig 5, knife Smart Topology with texture 15, body retexture 10, head retexture 10 |

## Anatomy decisions

- **Arm gate applies.** The native harpy has two human arms with five-fingered hands (a curved knife in the right)
  in addition to the wings; the wings are separate chains on the back, so the arms are a human source-frame rig with
  the knife fist solved (`R_HANDLE=0.018`, the Meshy knife's measured grip radius).
- **Bird legs** reuse the humanoid leg chain with bird joints (above). She never stands (native standing, walking
  and fidget are all the flight loop), so no foot planting, run fit or foot levelling; the legs are authored in
  every clip (`hover.py`), hovering at the actor origin with the talons 2-8 cm above the floor (flyers: no extra lift).
- **Wings**: rest = the raised V of the HD master; flap -92..+18 deg about the root (mid -37), outer bones lag a
  quarter beat; collapse in the death onto the floor (corpse pose by search, floor rule per frame).
- **Tail**: its own bone; in the death it folds up until it clears the floor (pelvis-rigid it propped the corpse 0.47 m).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m262_claude/export/mm7_m262.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m262_claude/export/mm7_m262_sword.glb --world mm7
```

Then add [actors_m262_binding.yml](actors_m262_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml` (scale 107
from the flight silhouette; per-tier stride = speed x 1.0 s / scale so every tier beats at the native cycle; blow
0.983 s; head look; knife attachment).

## Replay

`TOKEN=<lease> STAGE=rig ELBOW_FROM=meshy WRIST_FROM=meshy scripts/rebuild.sh`, then `STAGE=anim DEATH_UNTIL=12
R_HANDLE=0.018 LEAD=0.3 LEFT_CURL=0.5 SPREAD_MAX=25 SMOOTH_PASSES=6 DEATH_MAX_TURN=75 scripts/rebuild.sh` (twice on a
fresh project), then `STAGE=wings scripts/rebuild.sh`; texture chain once (`export_uploads.py`, Meshy `retexture_v1`
and `head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`),
`import_knife.py`, then `scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`. Every step runs in a
memory-capped scope (`scripts/cap.sh`, `scripts/b.sh`).

## Gates (final export)

- G3: wrists/elbows from Meshy; bird-leg joints from the mesh (hip 0.87, knee 0.68, hock 0.50, ball 0.22 m).
- G4: arm stretch p99 <= 1.73, max 2.18 (attack). Forearm ring twist reaches ~90 deg in the lying death (left arm).
- G5: hand stretch <= 2.38x (right hand, every clip; left <= 1.69x); knife fist clearance 1.3-2.3 cm.
- G6 (closed skin inside test, knife sampled to its 0.31 m tip): Walking clean; Attack <= 0.5 cm; Hit <= 0.1 cm;
  Death: knife 0.6 cm, **right hand 3.4 cm into the feathered hip at the end of the fall** (the raised legs meet the
  arm; `arm_clear.py` resolved 6 of 16 frames).
- Jerk: the largest steps are the slash itself (right arm 0.85-0.88 s, just before the blow) and the source death's
  fall (head 0.79 s).
- Winding: 0 inverted closed parts (body and knife). UV transfer: 3 of 9,590 faces lost by Meshy, 2 faces > 5 mm.
- Viewer: `tools/run_creature_review.py ... check`: 3 tiers x 5 clips, no console errors. Not checked in game.

## Known limits / for user review

- The feathered thighs are bulky (as the HD master) and fold heavily in the tuck.
- Tier A's flight feathers follow palette 263, a pale green, lighter than Meshy's teal.
- The death keeps a 3.4 cm hand/hip contact while lying; the hit and death keep the source clips' fast head moves.
- The native's knife flash and blood are not modelled.
