# MM6 Werewolf (wfigt1) — 3D model, 2026-10-09

Wolfman / Werewolf / Greater Werewolf (descriptors Werewolf A/B/C, 643/644/645; palettes 831/832/833), built with the
[humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md): Codex HD masters → Meshy Smart Topology → own cleanup and UVs →
Meshy API auto-rig + jaw bone → Mixamo Mutant clips → body retexture + head set → region tiers. Runtime:
`assets_dev/worlds/mm6/models/mm6_wwf.glb`, bound in `assets_dev/worlds/mm6/models/actors.yml` (opt-in via
`debug.actor_models=true`). Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_wfigt1_claude/review/viewer/>
(checked with `claude_shared/check_viewer.mjs`). Status: placeholder quality, awaiting user review.

| Item | Value |
|---|---|
| LOD0/1/2/3 | 10,821 / 5,354 / 1,797 / 498 (Smart Topology 14.4k; tail, eyeballs and bead necklace removed, head and hands kept) |
| Textures | body set 1K (from Meshy 2K), head set 1K (head, jaw, teeth, crown mane), normal and ORM (R baked AO) 1K |
| Tiers | region mask + ramps: shorts (rust → navy → red, by luminance rank), pendant gem (cyan → red → blue); fur, claws and gold unchanged (measured) |
| Rig | Meshy auto-rig (no finger chains) + `Jaw` bone; hands, head, teeth rigid; every mane/fur card and the pendant one averaged weight set |
| Clips (24 fps) | Standing 4.04 s, Walking 1.42 s, Running 0.875 s, Attack (claw rake) 0.5 s, Hit 0.75 s, Death 1.5 s, Dead, Fidget 1.0 s |
| Scale | 145.1 (native stand 246 px × 0.9 = 221 units against the 1.526 m posed Standing height); stride 1.71 m |
| Meshy credits | 30 of 100: Smart Topology 5, rig 5, body retexture 10, head retexture 10 (clips from Mixamo, free) |

## Pipeline (scripts/)

1. `references_hd/` (Codex, `CODEX_BRIEF.md`; side views came back mirrored to the guard convention, symmetric figure,
   noted in the progress JSON), `references_head/` (head turnaround; `references_head/meshy/` copies with the brown
   mane shifted to charcoal, used for the head retexture).
2. `examine_parts.py` → `analyse_parts.py` → `step1_wfigt1.py` (`work/step1_v1.blend`: tail cut + seat patch fitted to the
   buttock surface, 21 beads → one chain tube, eyeballs deleted, region decimation) → `uv_wfigt1.py`
   (`work/step1_uv.blend`; gates `uv_check.py`, `uv_islands.py`, `draw_uv_layout.py`).
3. `export_clean.py` → Meshy rig (`requests/rig_v1.json`) → `rebuild_anim.sh` (`build_rig_wfigt1.py`, `retarget_fbx.py`
   on the Mixamo FBX in `mixamo/`, `build_clips_wfigt1.py`, `pose_audit.py`, head split).
4. `export_neutral.py` → body retexture; head split → head retexture; `dump_uv3d.py` and
   `claude_shared/bake_creature_ao.py` on rig_v2.
5. `build_runtime.sh [--install]`: `native_pixels.py` → `prepare_textures.py` → `compose_head_set.py` (seam gain 0.8) →
   `export_runtime.py` → LODs → `shrink_shadow_lods.py` → region variants → `merge_head_material.py` → install →
   `viewer_tiers.py` → `update_viewer_manifest.py`.
6. Regression `mm6_werewolf_actor_model_tiers_share_the_native_height` (headless `actors` suite).

## Notes

- **Clips** (Mixamo Mutant set, downloaded by the user): Standing = Mutant Breathing Idle (spine/head breathing) with
  authored hanging arms; Walking/Running = Mutant Walking/Run with the root travel removed (stride = drift per cycle)
  and the stand's hanging arms swung with the source timing (±22° / ±32° with 60° elbows; user review 3: the Mutant
  flung them 21–58° out); Attack = an authored two-handed claw (user reviews: the roar lunge was weak, the swipe's
  arms flailed, the one-arm rake dislocated at the wind-up and sank into the shoulder): hips and chest settle back
  6 cm / 10° while both arms rise with the claws beside the head, elbows near shoulder height (frames 4–5; user
  review 5: higher upper arms stretched the armpit and lats into a sheet), both claws rake
  forward and down together as the hips drive 12 cm forward on planted feet (leg IK) and the chest leans in 18°,
  jaw wide (7), follow-through to waist height (9), back to the stand (12); largest per-frame arm step 42°; Hit = Zombie Reaction Hit
  4–44; Death = Mutant Dying 0–86 blended in from the stand over 7 frames (user review 3: it started in the old
  crouch), sits back and falls onto its back like the native death; Fidget = authored from the stand (claws lift,
  head turns, snarl). Meshy's own walk/run (rig job) are not used.
- **Arms (user review 2: shoulders too far forward and down, arms "flexing for a bodybuilding competition")**: the
  Mutant idle protracted the clavicles 18 cm and bent the elbows 55–68° with the claws on the hips. `hang_arms`
  puts the clavicles at the bind pose and aims the upper arms 17° out and 5° forward, elbows 28°, claws forward at
  the shorts' hem like the native stand. Attack, Hit and Fidget start and end on that stand; their arms are aimed
  along the source segment directions from it with the smallest swing (`aimed_arms`, titan stance_kept), so no source
  roll is copied (the swipe's slam rolled the upper arm ~100° and stretched the shoulder blade).
- **Stance** (in-game review against the sprites): the Mutant crouch read squat and bulky, so Standing, Attack, Hit
  and Fidget take a bone-space correction toward the bind pose (hips/spine keep 50 % of the crouch, legs 35 %), feet
  pinned to the floor, head turned 6° down so the snout is level. The walk/run keep the Mutant posture (forward lean,
  bent knees, like the native walk).
- **Shoulder weights (user review 5, stretch at the wind-up)**: Meshy's arm-to-torso transition on this broad
  torso is narrow, so the lat panel follows the upper arm. `build_rig_wfigt1.py` smooths the weights of the body skin
  between the shorts' top and the neck (20 Laplacian passes; neck/head weights untouched so the head split, and with
  it the head retexture's UVs, stay identical). Cutting arm weight off the lats instead only moved the tear onto the
  triceps (`review/heat_v3.png`); a clavicle shrug made it worse. Diagnosis: `scripts/stretch_audit.py` (edges
  stretched over 1.35× in the shoulder region) and `scripts/stretch_heatmap.py` (`review/heat_v4.png`).
- **Upper-arm skin (user review 6: biceps thinned/twisted with the claws raised)**: Meshy weighted the upper arm
  20–30 % to the clavicle and up to 15 % to the spine down to the elbow; that share stayed behind when the arm rose and
  one side of the arm collapsed to 34 % of its thickness (`scripts/arm_volume.py`). Along the shoulder→elbow segment
  the torso-bone weight now fades out from 12 % to 35 % of the way down into the upper-arm bone (lat skin excluded);
  minimum thickness through the attack 70 %, hit 74 %, walk 84 %, run 67 %.
  User review 7 (fins at the shoulder top): per-vertex cut-offs left armpit-junction vertices 100 % on the arm next to
  torso-weighted neighbours (they jumped 7 cm, `scripts/spike_audit.py`). The pass now builds a smooth "armness"
  field (geometric arm test, 12 Laplacian passes over the mesh) and runs after the shoulder smoothing; the smoothing
  fixes only the rigid hand/head vertices. Spikes ≤ 2.2 cm in every clip. Limb fur tufts take the weights of the
  nearest skin that Meshy gave the same dominant bone (mane and pendant keep their own mean so the head split stays
  identical). `review/viewer_shots/v8_shoulders.png`.
- **Jaw**: teeth were split between Head and Jaw weights and stretched into spikes; each tooth/tongue piece now goes
  wholly to one bone (`review/gate_jaw.png`).
- **Texture repairs**: Meshy projected shorts and chain colour onto neighbouring islands (hands, fur cards, chest);
  repaired by nearest clean texel per UV region. Fur ×0.7 toward the sprites' charcoal, except the ash-grey chest,
  shoulders and upper back. Shorts ramps by luminance rank (nearest-luminance kept Meshy's bright tan).
- **Gate** (`pose_audit.py`): penetration 0 in every clip; wrist ≤ 45° and forearm twist ≤ 12° outside the death;
  upper-arm roll ≤ 24° except the attack wind-up (≤ 44°, claws by the head, no visible wringing;
  `review/viewer_shots/v4_attack.png` at 48 fps) and the Mixamo death
  (≤ 70° in the fall). Viewer: `review/viewer_shots/v3_sheet.png`; in game `review/ingame/host3d_v5.png`.
  Close-ups: `review/gate_attack.png`; viewer: `review/viewer_shots/v2_sheet.png` (native front first).
- In game: `review/ingame/host_compare_v4.png` (3D left, sprites right, hostile spawns at the New Sorpigal spot).
- Known limits: hands are rigid open claws (no finger chains); the chain is a plain gold tube (no links); the body is
  bulkier than the sprite (Meshy bodybuilder proportions); the mane is ~300 cards (2k triangles); the walk is the
  Mutant brutal walk, heavier than the native; tier A gem reads green-teal.

## Death at source speed (2026-10-10)

`build_clips_wfigt1.py` plays Mutant Dying 0..86 at source speed (2.88 s, 69 frames; was 1.91x in 1.5 s), jaw keys
scaled with it ([clip timing audit](../CLIP_TIMING_AUDIT_20261010.md)). Pose audit maxima as before. Backups
`work/rig_v{2,3}_pre_death_timing.blend`.
