# MM6 Cleric (cle) — 3D model, 2026-10-09

Acolyte / Cleric / Priest of Baa (descriptors Cleric A/B/C, monsters 490/491/492; palettes 674 green-rust /
675 blue-grey / 676 tan-red), built with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md): Codex HD masters →
Meshy Smart Topology → own cleanup and UVs → Meshy API auto-rig + cloak chains (baked verlet) + the ankh staff modelled
from the native sprite → clips authored from the native keys (walk/run from Meshy's rig) → body retexture + head set →
three region tiers. Runtime: `assets_dev/worlds/mm6/models/mm6_cle.glb` and the staff attachment `mm6_cle_staff.glb`,
bound in `assets_dev/worlds/mm6/models/actors.yml` (opt-in via `debug.actor_models=true`).
Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_cle_claude/review/viewer/> (checked with
`claude_shared/check_viewer.mjs`: 3 tiers × 9 clips, no errors). Status: placeholder quality, awaiting user review.

| Item | Value |
|---|---|
| LOD0/1/2/3 | 10,421 / 5,210 / 1,875 / 623 incl. the staff (body 9,869 from Smart Topology 15.7k; eyeballs and the chest-emblem disc removed, the emblem is painted; face, hands and collar kept) |
| Textures | body set 1K (from Meshy 2K), head set 1K (face + hair), normal and ORM (R baked AO) 1K; 8.4 MB GLB |
| Tiers | three regions from the native palette-index groups (`../mm6_cle/materials.py`): R tunic and sleeves, G trousers and boots plus the mantle/hem piping and chest emblem, B collar, mantle and cloak; ramps from the native pixels of the original indexed bitmaps (`scripts/native_pixels.py`) |
| Rig | Meshy auto-rig (wrist joints moved onto the hands: left 32 mm, right 68 mm), 13 cloak chains × 4 bones (baked verlet), Staff bone in the left fist, socket `Socket_Staff_Head` (ring centre, cast focus) |
| Clips (24 fps) | Standing 4.0 s (breath every 2 s, weight shift and head drift over planted feet, staff upright beside the left foot), Walking 1.04 s (Meshy walk + staff carry), Running 0.63 s (Meshy run as a jog; not bound, see below), Attack 1.42 s (wind-up to his left, release forward with the staff level at the 0.75 s marker, follow-through), Cast (the Attack motion), Hit (body recoil), Fidget 0.75 s, Death 0.83 s and Dead (all authored from the native keys) |
| Scale | 110.0 (native stand 248 px × frame scale 0.7 = 173.6 units against the 1.578 m model; all tiers) |
| Meshy credits | 36 of 60: Smart Topology 5, rig 5, body retexture 10, head retexture 10, two library clips 6 (Shot and Fall Forward 184, Face Punch Reaction 174: not used, see Death) |

## Pipeline (scripts/)

1. `references_hd/` (Codex; `CODEX_BRIEF_v1_primary.md` for the primary, `CODEX_BRIEF.md` for views 01–04; gate
   `scripts/hd_gate.py` → `review/hd_gate.png`), `references_head/` (head turnaround, `CODEX_BRIEF.md`).
2. `examine_parts.py meshy/smart_topology_v1/model_urls_glb.glb v1` → `analyse_parts.py v1` → `step1_cle.py`
   (`work/step1_v1.blend`) → `uv_cle.py` (`work/step1_uv.blend`; gate `uv_check.py`, `draw_uv_layout.py`) →
   `export_clean.py step1_uv.blend cle_clean_v1.glb` → Meshy rig (`requests/rig_v1.json`).
3. `build_rig_cle.py -- meshy/anim_death_v1/result_animation_glb_url.glb:Death_src meshy/anim_hit_v1/...:Hit_src`
   (`work/rig_v1.blend`) → `cloak_rig.py` → `layer_weights.py` (tunic under the mantle copies the mantle's weights;
   tunic skirt blended toward the thighs) → `make_staff.py` → `seat_staff.py` (`work/rig_v2.blend`).
   Stress poses: `stress_pose.py`, `stress_parts.py` (coloured by part).
4. `rebuild_clips.sh`: `carry_staff.py` (walk/run staff carry, ring roll) → `author_clips.py` (Standing, Attack, Cast,
   Hit, Fidget) → `author_death.py` (Death, Dead) → `work/rig_v3.blend` → `cloak_sim.py` (`work/rig_v4.blend`) →
   `apply_head_split.py` → `pose_audit.py`. Shared solver `staff_rig.py`, helpers `author_lib.py`.
5. `export_neutral.py` → body retexture (`requests/retexture_v1.json`); `claude_shared/head_texture_split.py --mesh
   Cleric --rig Cleric_Rig --groups Head --parts 3 4 --whole-parts 3 4` → head retexture; `claude_shared/
   bake_creature_ao.py` on rig_v2 → `work/ao_body.png`; `dump_uv3d.py` on rig_v2.
6. `build_runtime.sh [--install]`: `native_pixels.py` → `prepare_textures.py` → `compose_head_set.py` →
   `export_runtime.py` → LODs → `shrink_shadow_lods.py` → region variants → `split_attachment.py` (staff) →
   `merge_head_material.py` → install → `viewer_tiers.py` → `update_viewer_manifest.py`.
7. Gates after the export: `trace_clip.py -- <clip> 48` + `trace_gate.py <clips>` (viewer timing; the staff grip and
   ring are compared with `work/<clip>_intent.json`), `cloak_poke.py` (env CLIP), `cloak_stretch.py`,
   `viewer_shots.mjs`. Regressions `mm6_cleric_actor_model_tiers_share_the_native_height` and
   `mm6_cleric_actor_spell_charge_glows_at_staff_head` (headless `actors` suite).
   In-game tours: `review/ingame/tour_*.yml` (New Sorpigal and Agar's Laboratory test spots).

## Decisions and lessons

- **Staff from the sprite, not Meshy:** the masters show empty fists (left fist with a front-to-back finger ring); the
  staff (1.60 m, ring finial 12 × 10 cm, two crossbars, collar knob, gripped 1.08 m above its foot) is built from the
  measured restored front frame and seated on the left fist's tunnel, searched only among directions perpendicular to
  the forearm and front-to-back (unrestricted, it ran past the fist).
- **Pose detached, then key** (`staff_rig.key_pose`): keying with the action attached let `view_layer.update()`
  re-evaluate the keyed pose over the solved arm, so the Standing staff stood 7–15 cm off its grip. The solver also uses
  the true elbow → wrist directions (`Side.uA`/`uF`), because the forearm bone axes sit 4–13° off after the wrist joints
  were moved.
- **Twist split:** the forearm takes 70 % of the hand's twist, capped at 85° (half-and-half left 46–78° at the wrist).
  Holding an upright staff with the arm out needs about 90° of forearm rotation from the palm-in rest; Cast now holds
  the staff at chest height with the forearm level instead of overhead.
- **Death authored** (Meshy 184 started from a raised-arm stance, whipped the staff overhead and sank 28 cm into the
  floor): sway, buckle to the knees, topple face down. The knees stay on the floor (shins behind them), ankles rise when
  the toes would dip, the staff tilts so its foot drags on the floor, and the lying staff takes the forward heading
  with the least wrist cost. The cloak and tunic skirt dip under the ground while he kneels (hidden by it); lifting the
  hips for them floated the body by up to 12 cm, so only the body counts for the floor.
- **Cloak collisions:** wider thigh/shin/hip capsules (15 / 10 / 13 cm) and 3.5 cm cloth clearance for the tunic skirt
  that follows the thighs: leg/skirt vertices through the cloak over the walk 168 → 20.
- **Trim tiers:** Meshy painted the piping and emblem near-black, the bottom of the legs ramp (black in every palette);
  repainted navy in the shared base, they read green / navy / white like the native A / B / C.
- **Run:** the monsters' speeds (160/180/200) stay below the run threshold (2.4 × 110 = 264), and Meshy's run, even as a
  jog, puts the back leg and the swinging elbow through the cloak, so `run` is bound to Walking. The Running clip stays
  in the GLB and the viewer.

## User review 2026-10-10

- Standing was too still: a 4 s loop with breathing (chest, clavicles), a slow weight shift and a small head drift.
- Attack: a wind-up (hips and centre of gravity to his left and back, staff drawn up) and a release forward (hips
  forward and down, chest leaning in) with the staff level with the ground at the strike, angled 40° across the body
  (straight forward bent the wrist 83°).
- Cast replays the Attack motion; the charge glows only at `Socket_Staff_Head`, as the New Sorpigal mage's (the palm
  socket and the right-fist thrust are gone).
- Hit has a body recoil (hips back and down, chest and head thrown back and turned away); Fidget a slight weight shift
  and turn toward the staff. All authored clips keep the feet planted with leg IK.
- Clip timing: Attack/Cast keep their own 1.42 s timing. `actors.yml` `animation.events` marks the release at 0.75 s:
  the engine fits the wind-up to the native 0.75 s action (when the bolt or spell leaves) and plays the rest during the
  recovery; bolts and spells leave from `Socket_Staff_Head` (engine `MODEL_RENDERING.md` "Action timing").
- The Air bolt's wind-up lights the staff ring (`ranged_hand_effects: {Air: openyamm:fx/creature_air_staff}` at
  `Socket_Staff_Head`: MM9 blurred blue star at 2.56 plus white-blue sparks) until the bolt leaves; regression
  `mm6_cleric_actor_air_attack_lights_the_staff_head`, captures `review/ingame/air_sheet.png` (`tour_air.yml`).

## User review 2026-10-10 (2)

- Mantle and collar spots (tier C): small dark specks in Meshy's mantle paint and the collar's inner shadow were
  classified as trim, which takes the legs ramp (white in tier C). `prepare_textures.py` now keeps only trim
  components of at least 1000 texels at 2K outside the collar (the piping and the emblem), paints the specks over
  with the surrounding cloth and replaces the cloak's isolated light/dark texels by their local median (9,325 speck
  and 774 outlier texels). The pale trousers and boots in tier C are native (the 676 palette's legs are near white).
- Cloak spots during animation: the inner cloak shell crossed the outer by 10-17 mm on the left side panel in every
  clip (cloak_rig.py weighted each surface by its own distance to the arm). `shell_weights.py` gives each inner vertex
  the weights of the outer point above it; `shell_cross.py` (in `rebuild_clips.sh`) reports no crossing in Standing,
  Fidget, Attack, Cast and Hit, 3 vertices at 3 mm on 7 of 26 Walking frames, and 7-11 mm where the cloak folds in
  Death and the lying corpse.
- Head look: `actors.yml` `look` turns the neck and head toward the party's eyes (engine `MODEL_RENDERING.md` "Head
  look"); captures `review/ingame/temple_*.png` (Superior Temple of Baa, priests on the stairs).
- Native shading transfer: by height the 3D cloth matched the sprites' medians within about 0.05 (only the hem is
  darker natively), so the height profile (`native_shading.shade`) is not used. The sprites differed in contrast: the
  cloak runs from black (its shadowed inside) to 0.75 luminance against 0.50-0.64 in 3D, the tunic 0.13-0.44 against
  0.19-0.34. Applied on user request (`prepare_textures.native_contrast`): the inner cloak and mantle at 0.5 of their
  luminance, and the outer cloth's broad shading stretched about its median (cloak x1.8, tunic x1.6, detail kept):
  cloak p10/50/90 0.26/0.56/0.65, tunic 0.12/0.31/0.35. The darker inside showed every shell crossing, so
  `shell_weights.py` also keeps the inner shell at least 15 mm inside the outer (it was 3-7 mm near the hem):
  no crossing in Standing, Fidget, Attack, Cast and Hit, one vertex at 2 mm on 5 Walking frames, up to 11 mm in
  Death and the corpse; legs through the cloak unchanged (20 over the walk). Edge padding: Meshy's light-grey fill
  between the islands sat under the soft region mask and drew light lines along the seams in game; each texel
  outside the islands now repeats its nearest island texel (after the ramps). Captures:
  `review/ingame/contrast/` (`before_*`, `after_*`, `sprite_*`, `zoom_b.png`: before / after / sprite).

## User review 2026-10-10 (3)

- Sharp dark triangles on the cloak after the inner shading: not shell crossings but wrong island labels.
  `uv_cle.py` put each cloak face in an outer or inner island by its own normal against the radial direction,
  unsmoothed, so 131 faces near the hem and the front edges had the other side's label: inner-labelled patches on
  the outer back and outer-labelled quads on the inside. The labels also chose which vertices `shell_weights.py`
  pushed inward, so outer-side vertices were dented in. `cloak_sides.py` (in `rebuild_clips.sh`, on the rest mesh)
  finds the physical sides: fold components (faces joined where normals agree within about 32 degrees; the rim turns
  the normal over in one or two faces) take their area-majority label, and the one mixed component (the mantle rim,
  114 faces) votes per face with half its label and half whether its normal faces the nearest body surface. Its
  `work/cloak_sides.json` drives the inner shading (`prepare_textures.raster_faces`, per face rather than per
  island; UVs and geometry unchanged), `shell_weights.py` and `shell_cross.py`. Crossings: none in Standing, Fidget,
  Attack and Cast; one vertex at 2 mm in Walking and 5 mm in Hit; Death 11 mm, the corpse 4.5 mm (was 9.6).
  A thicker inner offset (20-25 mm) crossed more. Review: `review/ingame/sides/` (`labels_vs_sides.png`: island
  labels on top, physical sides below, rest pose; `sides_standing_walking_running.png`; `viewer_tier_a.png`).
  An offset copy of the outer shell as the inside was tried and dropped: it kept the wrong labels.
- Running (unbound) still shows the inside at the back: the heel kicks into the cloak and the cloth creases sharply
  around it (`cloak_sim.py` leg collision), 9 mm whatever the shell thickness.

## User review 2026-10-14: hands, library Attack and Cast (not installed yet)

User: "I want the hands re-done - both look plain bad. The right hand not holding the staff can be a normal hand beside
the body ... and then some best fitting library animations for the cast and attack (he has the staff and one hand
free)." Built here; reduced and reviewed in `../mm6_cle_reduce_claude/` (README "Round 2").

- **Hands** (`hands_measure.py` -> `hands_mpfb.py` -> `fit_hands.py` -> `bake_hands.py` at the end of
  `rebuild_clips.sh`; `hand_texture_set.py` in `build_runtime.sh`): MPFB (MakeHuman, CC0) male hands posed with its
  finger rig: the left fist wrapped joint by joint around a cylinder of the staff's radius (index/middle closed, thumb
  along the shaft), the right hand relaxed (fingers drawn together and gently curled, thumb apart from the index: no
  ring). Each hand (994 tris, a 3.5 cm forearm stub hidden in the gold cuff) is a skinned object HandL/HandR in
  `rig_v4.blend`; the left fist's grip cylinder sits on the staff axis. Past the wrist 100 % on the hand bone, the stub
  copies the cuff's weights. `export_runtime.py` removes the old hand faces (`old_hand`: hand-weighted faces painted
  skin, so the cuff stays whole) and joins the new ones under the head material, so the master's face order (cloak
  sides, uv3d) is unchanged.
- **Hand texture**: the head texture set is resampled to 80 % into its lower-left corner (head UVs x0.8 at export, an
  exact resample) and each hand gets a 0.2 square of the freed top-right corner: the MakeHuman skin (nails, knuckles)
  baked through the hands' own MakeHuman UVs, graded to the face skin's median and spread, times a soft baked AO
  (fingers on the staff, cuff); flat normal; the old hands' roughness. No Meshy credits.
- **Clips** (`library_clips.py`, after `author_death.py`): Attack = Mixamo "Spell Cast": the staff arm thrusts, the
  forearm and hand turn so the staff ring points at the target 28 degrees up at the release (0.54 s; the shaft runs
  back past the hip, native cleatt b-c), then the staff returns upright. Cast = the same clip mirrored: the free right
  palm thrusts at the target, the staff arm keeps Standing's carry. Both 1.125 s, eased from and to Standing frame 0,
  feet on Standing's footprints (two-bone leg IK), 35 % of the source pelvis travel, wrist swing capped at 55 degrees,
  staff lifted (arm IK) where it would touch the floor. Retarget: world rotation change from the source rest onto our
  rig matched to the humanoid set's upright rest (the library's Mixamo files are retargeted to a hunched character;
  copying absolute directions crouched every clip). Tried and dropped for Cast: Standing 1H Cast Spell 01 (side-on
  throwing stance), Sword And Shield Casting (bows into a ground slam), Magic Heal (turns its back); the set's staff
  clips are martial-arts lunges. Gates: pose_audit wrist 55/55, no penetration, staff 0.6 cm above the floor;
  shell_cross Attack one vertex 7.4 mm (installed Hit 4.7), Cast none.
- **Weight spikes** (`spike_weights.py`, before `shell_weights.py`): five single vertices whose arm weight disagreed
  with their neighbours' (a tunic vertex at the right hip on RightArm/RightForeArm, shoulder mantle vertices) took
  their neighbours' mean weights; the hip vertex had stretched 95 mm in the new Cast (and 65 mm in the old Death).
- **Sockets**: `Socket_Palm_R` (right palm, 1.5 cm out) for the Cast launch and glow.
- Install (after the user's review): `tools/install_model.py ../mm6_cle_reduce_claude/export/mm6_cle.glb --world mm6`
  and `export/mm6_cle_staff.glb`; `actors.yml` for Cleric A/B/C: events impact 0.75 -> 0.54, `cast` launch_socket and
  `cast_focus_socket` -> `Socket_Palm_R`; regressions; ledger.
- Backups: `work/pre_libclips/` (rig_v3/rig_v4 before the library clips), `work/hands/rig_v4_pre_hands.blend`,
  `export/pre_hands/` (the exports before this round).

## User review 2026-10-14 (2): legs, exposed tunic, library Death (not installed yet)

User: "cast anim frame 3 (OK) -> frame 7 (twisted) - right ankle/leg/knee ... returns back on frame 25. in general the
stance is strange - like the feet placement vs legs? ... attack anim - exposes untextured back area? ... death anim -
pick some better from library i think."

- **Legs** (`library_clips.py`): the leg IK aimed the knees along the pelvis bone's axis (75 degrees inward, already
  at frame 0, so the crossfade from Standing snapped the knees in: the knock-kneed stance) and kept the source
  thigh's roll (up to 36 degrees off the shin: the twisted knee and ankle while Spell Cast turns the hips 50 degrees).
  Now each leg starts from Standing's frame-0 world rotations and swings minimally onto the footprint, the knee in
  Standing's bend plane; the pelvis takes PELVIS_TURN 35 % of the source rotation (the lowest spine bone the rest)
  and drops where a planted ankle would be farther from the hip than in Standing (the straightened legs lifted the
  heels 1.5 cm). Measured: thigh-to-shin roll 2-3 degrees, knees forward, feet on the floor, frame 0 = Standing.
  The stance width itself (the rest model's feet 8 cm outside the hips) is unchanged.
- **Exposed tunic** (`prepare_textures.py`): Meshy left the tunic grey or washed-out pale where none of its views saw
  it (under the arms, the flanks behind the cloak, the back of the torso); the tunic mask took only blue texels, so
  these stayed light grey in every tier. `fill_unpainted` repaints the tunic-region texels with saturation < 0.4
  (not gold or skin; 153k texels at 2K) with the tunic's median colour at the broad luminance of the painted tunic
  around them, keeping their folds. `relight_pouch_shadow` undoes the baked AO and lifts Meshy's painted shadow on
  the tunic behind the belt pouch (the Attack swings the pouch off it: dark shards).
- **Death** (`library_clips.py`): Mixamo "Dying (7)": staggers back, drops to a knee, falls face down, arms forward,
  the staff in the outstretched left hand (native cledyi: sways back, knees, face down). Its fall up to the settle is
  played in 1.75 s (source 4.5 s), eased in from Standing. Joints are kept their flesh radius above the floor (the
  pelvis lifted for trunk and legs, arm IK for elbows and hands: the retargeted kneel sank a knee 18 cm and the
  corpse's hand 13 cm, and cloak_sim's floor pass then floated the corpse 12 cm); once the hips are down the legs
  settle into the authored corpse's straight legs (author_death.py stays in the chain for that pose: the source kicks
  a leg up as it lands and the cloak caught on it); the staff is tipped toward level wherever it would reach under
  the floor. 'Dead' holds the last pose. Previewed and dropped: Dying (4), (5), (6), Standing Death Forward 01/02,
  Standing React Death Forward, Falling Forward Death, Sword And Shield Death (1), Death From Front Headshot, the
  set's Staff Death1 (`../mm6_cle_reduce_claude/review/deaths_*`).
- **Cloak in the death** (`cloak_sim.py`): lying, the one-sided collisions pushed cloth caught under or in the torso
  sideways (the standing yaw frame), so the fast dive left the cloak crumpled beside him; the push direction now
  blends into the chest's frame as the target already did (tilt over 25-70 degrees), and the cloak lies over his back.
- Gates: pose_audit Attack/Cast unchanged (wrists 55, no penetration, staff 0.6 cm up); Death wrists 42/45, no
  penetration, staff above the floor; upper-arm roll 71/78 degrees in the corpse (gate 40: both arms reach forward
  overhead; checked in renders); shell_cross Dead none (the old corpse 4.5 mm), Death 19 mm at the dive (old 11 mm).
- Fix along the way: `library_clips.py` saved rig_v3 at the FBX import's 30 fps; the clip rate is pinned to 24.
- Backups: `export/pre_r3/` (the exports of round 2).

## User review 2026-10-14 (3): shards on the robe (not installed yet)

User: "fix the texture artifacts on the bottom of the robe", then "walking frames 1-23 ... and attacking 6-17".

- **Texture** (`prepare_textures.py`): `smooth_skirt` removes Meshy's sharp-edged dark and light blotches on the skirt
  (luminance blurred at 24 texels inside the skirt islands, fine detail kept), which the tunic ramp and the 1.6x
  contrast turned into shards.
- **Geometry** (`skirt_shell.py`, in `rebuild_clips.sh` after `shell_weights.py`): Smart Topology made the skirt
  two-sided, an outside and an inward-facing lining 3-8 mm behind it (232 of 558 faces), weighted separately, so a
  stepping leg pushed the lining through the outside (17-18 mm in every clip), and the walk folds the panel's edges
  over (the source skinning, unreduced too), where the lining showed. Now: the lining faces are removed at export and
  replaced by an exact inner copy of the outside (`add_inside`: each vertex keeps its outer twin's weights, 4 mm in,
  faces flipped, on a flat dark tunic swatch `lining` in the atlas at 0.75 of the outside's median luminance), so the
  inside follows the outside exactly and shows only where the cloth curls (hem, slit). The outside's weights are
  smoothed a little; the waist under the skirt blends toward the outside's weights by depth (UNDER_FULL..UNDER_MAX)
  and sits 8 mm inside. Tried and dropped: pinning the lining 8-15 mm inside with the outside's weights and settling
  it against the clips (the reduced panel's large faces still let it through), local weight smoothing at the folds
  and moving the skirt's shin weights to the thighs (the folds stayed).
- The body is 11,099 tris unreduced (10,773 without the lining + 326 inside).

## Remaining faults (placeholder quality)

- Small leg specks through the back of the cloak on two walk frames and cloak openings of 5–12 cm between chains in
  Hit, Cast and Death (trace warnings).
- A few lighter speckles remain on the tunic in tier A (Meshy blotches; only the cloak is cleaned).
- The inner and outer cloak shells still cross up to 11 mm in Death and 4.5 mm in the corpse pose (see above); with
  the darker inside these can show as dark patches on the falling cloak.
- Running is not bound (see above).
- (2026-10-14: the right hand's ring and the crude left fist are replaced by the MPFB hands, see above.)
