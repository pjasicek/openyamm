# MM6 Skeleton (ske) — 3D model, 2026-10-09

Skeleton / Skeleton Knight / Skeleton Lord (descriptors Skeleton A/B/C, 628/629/630; palettes 816 ivory / 817 yellow /
818 dark red), built with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md). Runtime:
`assets_dev/worlds/mm6/models/mm6_ske.glb` + `mm6_ske_sword.glb` (attachment on `Sword`), bound in
`assets_dev/worlds/mm6/models/actors.yml` (opt-in via `debug.actor_models=true`). Viewer:
<http://127.0.0.1:8901/level_generation/creatures/mm6_ske_claude/review/viewer/> (checked with
`claude_shared/check_viewer.mjs`: 3 tiers × 8 clips, no console errors). Status: placeholder quality, accepted by the user 2026-10-09 (after the attack body-motion follow-up).

| Item | Value |
|---|---|
| LOD0/1/2/3 | 9,822 / 4,908 / 1,711 / 504 (incl. 280-triangle cutlass and 160-triangle eyes) |
| Mesh | body Smart Topology (78 separate bone pieces, 16.2k) + skull-only Smart Topology (cranium, jaw, separate teeth, 16.3k), reduced per piece |
| Rig | own: 53 mixamorig joints placed at the bone pieces' principal-axis ends, `Jaw` at the mandible condyles, `Sword` under RightHand; every piece 100 % on one joint (no skin stretch) |
| Clips (24 fps) | Standing 2.5 s, Walking 1.083 s, Running 0.708 s, Attack 1.5 s (impact 0.771 s), Hit 0.75 s, Death 2.83 s (source speed + skull roll, 2026-10-10), Dead, Fidget 1.21 s (source speed) |
| Textures | body set 1K (Meshy 2K), head set 1K (skull retexture), normal and ORM (R baked AO) 1K; eyes = red swatch in the head set; one material per tier after the head merge |
| Tiers | one region (all bone, teeth included); ramps from the native bone pixels (tier A saturation < 0.3) of skesta0..4 per palette, gain 0.95, AO 0.8; cutlass and eyes keep their colours |
| Scale / stride | 123.6 / 141.26 / 158.91 for tiers A/B/C (native stand 273 px × 0.7 = 191 units over the 1.546 m Standing pose; B and C follow their SFT frame scales 0.8 and 0.9, corrected 2026-10-21); stride 1.028 m from the processed feet; run threshold 297 > all tier speeds |
| Meshy credits | 30 of 60: body Smart Topology 5, skull Smart Topology 5, body retexture 10, skull retexture 10 (no rig job; Mixamo clips free) |

## Pipeline (scripts/)

1. `references_hd/` (Codex: `CODEX_BRIEF_v1_primary.md` primary, `CODEX_BRIEF.md` views 01–04; 00 is raw v1 by
   orchestrator override) and `references_head/` (skull turnaround, `CODEX_BRIEF.md`).
2. `examine_parts.py` on both Smart Topology returns → `work/st_v1_parts.blend`, `work/skull_v1_parts.blend`;
   piece labels in `parts_map.py` (`hand_chains.py` found the finger chains).
3. `rebuild.sh`: `build_rig.py` → `add_skull.py` (neck stub cut, skull placed on the atlas) → `reduce.py` →
   `uv_ske.py` (body and head layouts) → `add_eyes.py` (sockets by ray casting) → `fist_sword.py` (grip solve +
   cutlass from skesta2 proportions) → `retarget_fbx.py` (Mixamo Sword and Shield pack, `mixamo/clip_map.json`) →
   `build_clips.py`. Deterministic: the retexture uploads re-export byte-identical.
4. `export_neutral.py` → `requests/retexture_v1.json`, `requests/head_retexture_v1.json`.
5. `build_runtime.sh [--install]`: `bake_ao.py` (body, head) → `compose_ske.py` → `export_runtime.py` →
   prepare → LODs → `shrink_shadow_lods.py` (margins 1.5–4 mm for thin bones) → region variants → sword split →
   head merge; then `viewer_tiers.py`, `update_viewer_manifest.py`.
6. Regression `mm6_skeleton_actor_model_tiers_follow_the_native_frame_scales` (headless `actors` suite, 20/20 pass).

## Clip notes

- Mixamo's sword-and-shield idle/hit/fidget/attack stand sideways in a deep fencing crouch. Turning the whole body to
  face forward splayed the legs, so those clips are "stance" clips: hips and legs planted in the skeleton's own stance
  (bind pose + 12/24/12° knee bend, native stoop at Spine2/Neck), spine 30–80 % of the source, arms from the source.
- Standing and Fidget use an authored right arm from the native stand (cutlass low, forward and out).
- Hit uses the head-impact variant (head back, sword up, as the native hit). Attack: downward slash, 0.05–1.35 s at
  source speed after a 0.2 s ready pause (2026-10-10, engine action events: blow at 0.771 s, actors.yml
  `events: attack_melee: {impact: 0.771}`, so the native 0.75 s wind-up plays at 0.97x; it was 1.7x before), plus body motion (user request): wind-up = weight back 4.5 cm, hips turned 16° sword-shoulder back, torso
  leaning back 12°; swing = hips forward 8.5 cm and down 3.5 cm, turned 14° through, torso 16° into the cut, left foot
  steps 15 cm forward with a 4.5 cm lift; recovery back toward the stance. Timed from the grip's path (wind-up peak
  = highest grip, strike end = lowest after it); feet by two-bone IK in each leg's bend plane, kept flat.
- Walk/run legs and spine are 40/50 % straightened toward the bind pose (the Mixamo walk read as a crouch in game);
  the stride is re-measured from the processed feet.

## Known faults (placeholder)

- Bone colour reads lighter and flatter than the sprites, which have hard dark crevices and a 1-px outline; native
  shading transfer was not applied.
- The right thumb hooks over the grip rather than wrapping it; the left hand keeps Mixamo's shield-arm pose.
- The full trace/pose-audit gate (thief tools) was not run; checks were clip sheets, viewer load, in-game captures.
- The cutlass keeps tier A colours (the native palettes shift it slightly per tier).
- Death drifts the corpse about 0.5 m back from the actor position (half the Mixamo travel).
