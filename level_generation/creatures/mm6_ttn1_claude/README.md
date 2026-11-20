# MM6 Titan (ttn1) — 3D model, 2026-10-09

Titan / Noble Titan / Supreme Titan (descriptors BTitan A/B/C, 640–642; palettes 828/829/830), built with the
[humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md): Codex HD masters → Meshy Smart Topology → own cleanup and UVs →
Meshy API auto-rig + library clips → body retexture + head set → region tiers. Runtime:
`assets_dev/worlds/mm6/models/mm6_ttn.glb`, bound in `assets_dev/worlds/mm6/models/actors.yml` (opt-in via
`debug.actor_models=true`). Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_ttn1_claude/review/viewer/>
(checked with `claude_shared/check_viewer.mjs`).

| Item | Value |
|---|---|
| LOD0/1/2/3 | 10,176 / 5,087 / 1,831 / 602 (Smart Topology 15k; rivets and eyeballs removed, head and hands kept) |
| Textures | body set 1K (from Meshy 2K), head set 1K (helmet, crest, face), normal and ORM (R baked AO) 1K |
| Tiers | region mask + ramps: armour (lavender → black → black), trim (gold → gold → blue), crest (red → red → cyan); skin unchanged |
| Rig | Meshy auto-rig (no finger chains); hands, head and helmet rigid; every armour plate one averaged weight set |
| Clips (24 fps) | Standing 2.0 s, Walking 1.04 s, Running 0.625 s (Meshy rig), Attack 0.75 s (fist, melee), Ranged 0.75 s (Mixamo one-handed thrust), Cast 2.0 s (Mixamo two-handed push), Hit 0.75 s, Death 1.5 s, Dead, Fidget 0.625 s |
| Sockets | `Socket_Palm_Left` / `Socket_Palm_Right` on the palms (cast glow between the hands) |
| Scale | 331.8 (native stand frame 374 px × frame scale 1.4 = 524 units against the 1.578 m model; all tiers 1.4) |
| Meshy credits | 54 of 80: Smart Topology 5, rig 5, eight library clips 24, body retexture 10, head retexture 10 |

## Triangle reduction (installed 2026-10-14)

The installed model is the reduction from [mm6_ttn_reduce_claude](../mm6_ttn_reduce_claude/README.md): 10,176 -> 7,666
triangles (face, eyes, helmet, jewel and arm bands unchanged), same textures, tiers, clips and palm sockets. The LOD
row above describes the pre-reduction model (rollback source in that project).

## Pipeline (scripts/)

1. `references_hd/` (Codex, `CODEX_BRIEF.md`; side views swapped to the guard's convention, see the progress JSON),
   `references_head/` (head turnaround from the body masters).
2. `examine_parts.py` → `analyse_parts.py` (visibility) → `step1_ttn.py` (cleanup, `work/step1_v1.blend`) →
   `uv_ttn.py` (`work/step1_uv.blend`; gate `uv_check.py`, `uv_islands.py`, `draw_uv_layout.py`).
3. `export_clean.py` → Meshy rig (`requests/rig_v1.json`) and library clips (`requests/anim_*_v1.json`) →
   `build_rig_ttn.py -- meshy/anim_cast_v1/...:CastSrc ...` (`work/rig_v1.blend`) → `build_clips_ttn.py`
   (`work/rig_v2.blend`) → gate `pose_audit.py -- rig_v2.blend`.
4. `export_neutral.py` → body retexture; `cp rig_v2 rig_v3` + `claude_shared/head_texture_split.py` (parts 0 9 10 11 12,
   whole 9–12) → head retexture; `claude_shared/bake_creature_ao.py` on rig_v2 → `work/ao_body.png`.
5. `build_runtime.sh [--install]`: `native_pixels.py` → `prepare_textures.py` → `compose_head_set.py` →
   `dump_head_uv.py` → `head_tiers.py` → `export_runtime.py` → LODs → `shrink_shadow_lods.py` → region variants →
   `merge_head_material.py` → install → `viewer_tiers.py` → `update_viewer_manifest.py`.
6. Regression `mm6_titan_actor_model_tiers_share_the_native_height` (headless `actors` suite).

## Notes

- **Clips** from the Meshy library on our rig (retimed to the native lengths; the engine cuts attack and hit at the
  native 0.75 s): Attack = Mage Spell Cast 7 frames 10–46 (right hand draws back and thrusts forward, as the native
  lightning cast); Cast = the whole cast (spellcasters need a clip distinct from Attack); Hit = Standing → Head Hold in
  Pain frame 56 (both hands on the helmet, bent, as the native wince) → Standing; Death = Shot and Fall Forward; Fidget
  is procedural (arms lift, elbows bend, head turns; Meshy's Idle 0 turned the whole body round). Every authored clip
  is lifted per frame so no vertex goes below the floor (Meshy's clips sank the feet 2.5–4 cm).
- **Stance (user review 2026-10-09: Standing "curved weirdly", walk "slumped shoulders").** Meshy's Idle 1 stooped
  (curved spine, head forward, one forearm raised); Standing is now authored from the bind pose like the native stand:
  upright, upper arms aimed down beside the hips (10 deg out, 6 deg forward), elbows bent 12 deg, a slow breath.
  Attack, Cast, Hit, Fidget and Death start from it, and Attack/Cast keep only 30 % of the source's spine, neck and
  head rotation (the source body hunches). The walk dropped the clavicles by up to 16.6 deg: `build_rig_ttn.py` now
  holds them within 3 deg of rest both ways (it only stopped them rising). Key poses: `review/poses_v2.png`.
- **Second review (2026-10-09): death deformed the torso, fidget arms went into the body, melee should be a fist.**
  Death is now Meshy Dying Backwards (189: stagger, knees, fall back) with the spine twist about the bone axes at
  50 %; Shot and Fall Forward arched the chest back and bloated the cuirass even with the twist damped. The fidget's
  world turns had both signs wrong (arms swung inward and hands backward). Melee Attack = Meshy Right Upper Hook from
  Guard (195) frames 6–30, lunge halved, spine 60 %; the lightning thrust became Ranged (`attack_ranged`) and Cast
  stays the full spell. The uppercut (194) was ordered for comparison and not used. Chain: `scripts/rebuild_anim.sh`.
- **Chest weights (user review 106: the right pec stretched in the hook).** Meshy gave the chest up to 55 % upper-arm
  and 97 % clavicle weight up to the sternum; `build_rig_ttn.py` ramps them out toward the midline (arm 0 at
  |x| 0.12 m → full at 0.21, clavicle 0 at 0.05 → full at 0.17) into the spine bones (307 vertices). The stretch now
  sits at the armpit under the pauldron: `review/chest_fix_attack.png` (attack frames 5–7).
- **Native shading transfer (user request 2026-10-09).** `prepare_textures.py` (`NATIVE_SHADE`): the armour texels
  take the native armour brightness by height (5 % bins over all standing views: dark greaves, lighter skirt, darker
  waist, bright chest and shoulders) × Meshy's hammered detail at 0.7; the head set is not shaded. In game, tiers B/C
  then read as flat matt black (the absolute-luminance pitfall: the shaded armour is darker than most native pixels),
  so their armour ramps match by luminance rank (`rank_ramps`) and show the sprites' teal sheen; tier A keeps the
  luminance-matched ramp (by rank it read chalky white). Before/after: `review/native_shading_tiers.png`, in game
  `review/ingame/ns_compare.png` (3D left, sprites right). Pre-transfer maps: `textures_pre_native/`.
- **Planted casts (user review: Ranged moved his legs while he stood still).** Ranged and Cast take hips and legs from
  the Standing pose (`planted`), only the upper body from Meshy's cast. The Mixamo one-handed casts (Standing 1H Magic
  Attack 01–03, 1H Cast Spell 01, Magic Spell Casting) all step or lunge too, so the same planting would apply to any
  of them.
- **Mixamo casts (user: Ranged moved his legs; "mind the stance").** `mixamo/standing_1h_magic_attack_01.fbx` →
  Ranged (source 8–46 in 0.75 s: wind-up, right-hand thrust), `mixamo/two_hand_spell_casting.fbx` → Cast (source
  8–86 in 2.0 s: arms rise and gather, two-handed push, hold), retargeted by `retarget_fbx.py` (in
  `rebuild_anim.sh`). The wizard's crouched, turned stance is not kept: hips and legs planted, spine 30 %, the
  titan's own clavicles, and upper arm / forearm / hand aimed along the source segment directions from the rest pose
  with the smallest swing (`stance_kept`). Local arm rotations on the straightened chest spread the arms into a T;
  copying world arm orientations kept the source twist (130 deg upper-arm roll, collapsed shoulder). Wrist swing is
  capped at 45 deg; during the Cast blends the arms swing out so the left forearm does not cross the belly. Both
  palms carry sockets (`Socket_Palm_Left/Right`), so the cast glow forms between the hands.
- **Channel and release (user: "move his body a bit forward ... channel and release a spell").** `body_motion` in
  `build_clips_ttn.py` moves the hips (forward/down), leans the chest and steps the right foot, legs by two-bone IK
  with flat feet: Cast settles back while the arms gather (frames 6–18), steps 22 cm forward and drives hips and chest
  into the push (20–23), holds, steps back (40–46); Ranged shifts the weight into the thrust without a step.
  `review/cast_body_motion.png`.
- **Gate** (`pose_audit.py`): penetration 0 (one vertex in Hit), wrist ≤ 55°, forearm twist ≤ 34°; upper-arm roll
  under 41° except the hook (right arm 88° as it swings overhead, no visible wringing in close-ups) and Death (≤ 59°).
- **UVs**: Smart UV Project shattered the plates into 886 islands; seams on sharp edges + minimum-stretch unwrap, a
  Smart UV fallback for collapsed or stretched regions (hands, feet, dome, left leg back) and per-island density
  normalisation give 452 islands, 52 % coverage, 8 texels/cm (2K) on the body and 14 on the face. Meshy fused the
  left greave into the leg shell; it is found by mirroring the right greave.
- **Tier ramps** from the aligned native standing pixels (`native_pixels.py`, `review/native_regions.png`):
  armour ×1.35, trim ×1.0 (×1.3 read neon-yellow in game, `review/ingame/far_1.png`), crest ×1.2. Body and head share
  one ramp set (merge_head_material.py requires it); the crest ramp only acts on the head mask.
- Known limits: hands are rigid open hands (no finger chains), so the fidget cannot clench the fists as the native
  does; the death is a fall backwards, not the native shatter; the fist is the open rigid hand; the crest is a single open sheet (as Meshy built it);
  the 3D armour has no per-pixel specular sheen like the prerendered sprite (the sheen is in the ramps).

## Clip timing (2026-10-10)

`build_clips_ttn.py` now plays the actions at source speed ([audit](../CLIP_TIMING_AUDIT_20261010.md)): Attack =
0.35 s guard pause + hook 6..30 (1.33 s, was x1.33), Ranged = 0.2 s pause + 1H magic 8..46 (1.46 s, was x1.69),
Cast = two-hand casting from source frame 18 (the opening rise-and-drop 8..18 dropped; 2.25 s, was 2.0 s squeezed
into the 0.75 s cast, ~x3.5). The authored body-motion keys scale with the clips. Markers printed by the script:
blow 0.604, thrust 0.729 (from `Socket_Palm_Right`), push 0.771 -> actors.yml `events`. Pose audit as before
(cast end: 0.2 cm left-hand touch on 3 vertices). Previous build: `work/rig_v2_pre_clip_timing.blend`,
`rig_v3_pre_clip_timing.blend`; sheets `review/timing_{Attack,Ranged,Cast}_sheet.png` (old: `review/old_*`).
- Death at source speed (follow-up): the whole Dying Backwards clip, 2.21 s (was 1.49x in 1.5 s); pose audit as
  before. Backups `work/rig_v{2,3}_pre_death_timing.blend`.
