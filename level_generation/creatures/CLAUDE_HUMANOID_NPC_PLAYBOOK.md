# Humanoid NPC 3D playbook (Claude)

The accepted process for MM6–MM8 humanoids (two-armed characters, armed or not). Read it fully before starting.
Reference projects, newest first: `mm6_natm_claude/` (spear and shield; authored weapon attack over mocap, feet and
motion probes; best current template), `mm6_bar1_claude/` (sword, rig-first gates, `TEST_DRIVE.md`),
`mm6_gob2_claude/` (non-human proportions, curved blade, skirt strips). Older special cases are listed at the end.

## Default route: source-frame rig with gates

User verdicts: barbarian "very good results" (one review round), natm "very good" (one review round).
**Principle.** Professional clips are correct, so arm, wrist, hand and finger faults come from our mesh, joints, bone
frames, weights or props, and wrong-looking motion usually comes from choosing a clip for the wrong reason. Check each
layer on numbers before building the next, fix a fault where it starts, replay the whole chain after every change.
Viewer and game are confirmation, not discovery.

| Gate | What | How (scripts in `mm6_natm_claude/scripts/` unless noted) | Pass |
|---|---|---|---|
| G1 clips | choose clips BEFORE modelling, by motion and by the weapon's geometry | `spear_preview.py`/`rpg_preview.py` (the set's own mannequin with a prop stand-in), `spear_probe.py` (tip height, prop pitch/yaw per frame), candidates rendered on our body (`spear_sheet.py`) | the blow reaches the target with the prop pointing at it; front, side and three-quarter read right |
| G2 proportions | segment lengths vs the source | `proportions.py` | warning only |
| G3 joints | two independent estimates in one X-ray | Meshy auto-rig (`meshy_joints.py`, 5 cr) for shoulders, clavicles, spine, hips, knees **and elbows**; ring centres for wrists/ankles (`fit_joints.py`, skin shell only); `compose_joints.py`, `joint_xray.py` | symmetric, inside the limb; ring line-fits put natm's elbows at 68–76 % of the arm, Meshy's at 51 % was right |
| G3 frames | cloned source frames | `build_rig.py` (rest = minimal swing @ source frame; hands from the mesh knuckle line; fingers by connectivity, `fit_fingers.py`, `finger_joints.py`), `hand_frame_check.py`, `hand_xray.py` | frame error 0; fitted chains inside the fingers |
| G3 retarget | world-rotation copy | `retarget.py` (set), `retarget_mixamo.py` (Mixamo, `:plant`/`:turn`) | durations equal the source's |
| G4 weights | at the ROM extremes | `garments.py` + `weights_fix.py` (rules by garment), `twist_bones.py`, `g4_weights.py`, `stretch_heatmap.py` | arm p99 ≲ 2, forearm twist ramps |
| G5 fingers + grip | fist for our fingers, source grip direction | `finger_weights.py`, `reduce_rigged.py` (after weights), `grip_from_source.py`, `grip_solve.py`, `apply_grip.py`, `g5_hand_stretch.py` on every clip | hand edges ≤ ~4.5x, thumb over the handle |
| G6 contacts | prop and limbs vs body on the posed mesh, half frames | `g6_contacts.py`: **inside test on the closed skin only**, proximity for open shells (feather cards, panels, cloth); whole prop length sampled | nothing inside the skin |
| G6 feet + motion | soles on the floor, no jerks | `sole_probe.py` (lowest foot vertex per frame), `jerk_probe.py` (world rotation step and its change per 1/48 s for head, arms, feet) | grounded soles within ±2 cm; no step or second difference far above the source's own |
| G7 look | textured renders from the party's camera, viewer, game | `render_clip_glb.py` (front = party eye height, side, close-ups), `check_viewer.mjs`, in-game tours | only after the numbers pass |

`rebuild.sh` (STAGE=rig, then STAGE=anim) replays cleanup → rig → retarget → foot levelling → carry → authored
attack → prop clearance → twist → weights → fingers → reduction → grip → timing in about a minute and aborts on the
first failing step. `build_runtime.sh --install` syncs the clips into the textured master and builds the runtime.

**Rules that proved themselves (each was a wrong turn first):**
- Retarget = WORLD rotation copy onto cloned frames (a local copy differs up to 68°). Hand rest frames come from the
  mesh's fitted knuckle line and finger direction (PCA was 35° off). Fingers by connectivity, never by distance
  (thumb cut first; a finger = the earliest component that never splits again); grow pieces through edges past the
  knuckle; measured fingertips; one smooth subdivision of the prop-hand fingers if they facet.
- The source's finger curl leaves no room for a handle in our thicker fingers: solve the fist per finger around a
  fixed handle. Handle DIRECTION = the source grip axis; a blade also needs its ROLL gated (`blade_edge_gate.py`;
  a curved blade needs contacts on its real mesh and the convex edge leading).
- Twist: forearm twist bone (0.6 of the hand roll, ramp 15–85 %) and an upper-arm counter-twist ending above any
  rigid ring; a rigid bracer takes the twist rigidly and the ramp moves to the elbow band.
- Weights: label every loose part by garment first (`garments.py`: proximity groups named by position); accessories
  copy the skin under them only within the armour gap; small rings rigid on their dominant bone; feather/scale cards
  rigid per card (hip trim, leg guards) or skin-copied and smoothed per card (a mantle: legs moved to the pelvis, arm
  share ≤ 0.25); skirt/loincloth strips pelvis → thighs with ONE left/right mix per strip; upper-arm weight fades
  out medially; jaw/head skin carries no clavicle or upper-arm weight.
- Reduce the triangle budget AFTER weighting (`reduce_rigged.py`, per garment, head and hands protected).
- Trunk axial twist soft-limited to ~45° (`mm6_bar1_claude/scripts/clip_timing.py limit_spine_twist`); big head
  and pauldrons: `g6_head_clearance.py` + `head_fix` (gob2).
- Timing traps: Blender's glTF import maps seconds at the scene rate; keep the source's frames; quaternion keys
  sign-continuous.
- Imported `B_*` armatures use QUATERNION rotation and meaningless bone tails (use joint heads).

## Weapon attacks and held props (natm, 2026-10-14)

The Codex natm attack looked artificial because it was built on clips that cannot work with the weapon. What fixed it:
- **Measure the weapon against the clip before choosing.** The humanoid set holds every weapon like a hammer: the
  shaft crosses the palm with the tip out of the thumb side, perpendicular to the fingers. A spear then points along
  an extended forearm only with a 60–90° wrist bend, and an overhand thrust needs the reversed grip. The set's spear
  attacks therefore stab the ground (R3: tip 2 cm above the floor 2 m ahead, then an 8-frame frozen hold). With this
  grip the natural spear blow is an **underhand thrust**: arm near-straight swinging from behind the hip to ~50°
  forward, wrist cocked ~40°. A diagonal grip (tilted handle) broke the fist solve; keep the square grip.
- **No clip fits → mocap body + authored blow** (`author_attack.py`, all numbers in `attack_params.json`): a mocap
  of a similar action (Mixamo "Stabbing (2)") gives the trunk, head and the off-arm's counterbalance, time-remapped
  (monotone cubic); authored on top: pelvis path (sink and draw back, drive forward), hip yaw then chest yaw 50 ms
  later (kinetic chain), forward lean, clavicle reach (≤ 8°: 14° pinched the armpit), legs by IK to a foot plan (one
  lunge step with a sine lift, rear heel peeling about a floor-level pivot under the ball, toes kept flat), the
  pelvis lowered whenever a planted leg cannot reach, a mesh floor clamp, the arm as angles about the shoulder
  (flex/abduction/length: reachable by construction), the prop aimed at a target, a head stabiliser (smoothed gaze,
  yaw held toward the target). Blend from and back to Standing frame 0 inside the clip.
- **Aim from the party's view.** Target chest height (1.2 m at 2.1 m); a thrust aimed dead at the camera
  foreshortens to a dot, so offset it ~30 cm across the body (the native sprite draws the thrust across too).
  Impact = when the tip reaches 95 % of its forward travel, not peak speed.
- **Arm IK: minimal change + a global choice.** `armik.py`: start from the clip's own arm, swing upper arm and
  forearm the least, keep the elbow-plane roll; choose elbow plane and hand roll over the WHOLE clip (Viterbi,
  `arm_dp`: wrist swing + 0.6 × |forearm twist − 30°| + continuity), then smooth. Per-frame greedy solves flipped
  the hand 150°+ and snapped the running elbow.
- **Held prop in idle/locomotion** (`author_carry.py`, `carry.json`): wrist in the chest frame plus a share of the
  clip's own wrist motion (idle/walk 0.3, run 0.35), prop direction fixed in the pelvis frame, same global arm solve.
  Angle a long prop so its butt clears the hip (tip slightly out with the hand 4 cm further out and forward).
- **Long props through the body**: `spear_clear.py` turns the hand the least (≤ 36°, wrist only, smoothed) where
  the shaft enters the skin, on clips that keep their source arms. Run it before the twist bake.
- **Props from the HD prop references**: model the silhouette, texture by planar projection (`make_props.py`,
  `prop_textures.py`); give each prop its own material and region mask, keep it in the body GLB through
  `region_variants.py` so the split attachment inherits the tier variants.

## Feet and locomotion after any retarget (natm review 1)

Every Mixamo/set clip carries the source body's feet. Fix them in the chain, then measure (`sole_probe.py`):
- **Toes:** the source toe channels curled the toes 4–7 cm up in every clip (looked "warped"). Reset Toe0 to rest
  except where authored.
- **Foot pitch:** the Mixamo idle and walk pitched the feet ~20° toe-up. `foot_level.py` levels grounded feet
  (heel/toe reference vertices back to their rest relation, fading out above 8 cm); for walks only the clip's
  constant tilt (keeps heel strike and toe-off); for deaths only before the body goes down.
- **Height:** a floor pass per frame (lowest sole, or the whole body for a death) in `clip_timing.py`: the set's hit
  floated 17 cm after blending, the cast sank 6 cm, the corpse lay 28 cm under the floor.
- **Installed check:** after installing, run [`floor_audit.py --match '<descriptor>*'`](claude_shared/floor/README.md).
  It poses the installed GLB at every key of every bound clip and reports the standing height, a walk's all-feet-off
  lift, a death sinking through the floor and the corpse height, in world units. `floor_fix.py` repairs a hop, a
  corpse or skirt strips under the floor without re-exporting (the 2026-10-21 MM8 pass found a Dark Elf Warrior death
  11.7 units under the floor and Dark Elf Female skirt strips 7.4 under it).
- **Run:** keep the SOURCE's own ankle paths relative to its pelvis (heel kick, knee drive, toe-off), scale only
  the forward travel to the stride, raise the pelvis (~92 % of Standing + a 5 cm bob), knees in the source leg
  plane, a constant foot yaw (a per-frame yaw flipped 60–100° at toe-off), a mesh floor clamp (`run_fit.py`).
  Synthetic sine-lift foot paths read as "fast walking". Never RelaxRunForward or jogging; Mixamo Standard Run.
- **Walk:** pick a walk whose natural speed is near the monster's (stride by distance): measure stride = planted
  foot speed × cycle (`scripts/stride.py`); Mixamo "Walk" (1.69 m) for fast walkers, the set's armed walk (1.09 m) is
  slow. A long Mixamo death travels: halve its pelvis travel so the corpse lies near the actor.

## Quick start (exact commands)

Run from the repository root. `<P>` is the new project, e.g. `level_generation/creatures/mm6_<id>_claude`.

0. **HD masters first ([CLAUDE_HD_MASTER_REFERENCES.md](CLAUDE_HD_MASTER_REFERENCES.md)).** Five generated views
   from the ORIGINAL native bitmaps (`00_three_quarter`, `01_front`, `02_back`, `03_left`, `04_right`), gated.
   An earlier attempt's gated masters (and its Smart Topology of the same master) can be reused. Never send Meshy a
   native sprite or a restored frame.
1. **Inputs.** Native frames and restored x2 frames (`mm6_<name>/native`, `aligned_2x`, `native_variants`), item art
   for props (`assets_dev/engine/icons_x2/`), palettes `assets_dev/worlds/mm6/textures/pal*.act`. **Tier palettes:**
   read the palette id per tier from `assets_dev/worlds/mm6/_legacy/bin_tables/dsft.bin` (int16 at byte 50 of
   the record that starts with the sprite name), never from a restoration note (natm A is 795 grey, not the "base" 796).
2. **Claim the workspace:** `python3 tools/creature_workspace.py claim --project <P> --identity mm6:<id> --owner
   <session> --state creature_3d_progress.json --budget <credits>`; release with the token at the end.
3. **Meshy jobs** (requests in `<P>/requests/`, `@file:` paths relative to the project; templates in
   `mm6_natm_claude/requests/`): `./tools/run_creature_meshy.sh --project <P> --state creature_3d_progress.json
   --token <T> submit|poll|download ...`. Typical spend 25–30: Smart Topology 5, auto-rig 5, body retexture 10
   (`enable_original_uv: false`, copied back by `transfer_uv.py`), head retexture 10.
4. **Blender** headless: `/snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1
   --python <script> -- <args>`. Copy the closest reference project's `scripts/`, then adapt the creature-specific
   parts (`step1_clean.py`, `garments.py`, `weights_fix.py`, clip lists `set_clips.txt` / `mx_clips.txt`).
5. **Textures:** `export_uploads.py` (body + head faces with a level neck cut), retextures, `transfer_uv.py`,
   `uv_raster.py`, `bake_ao_natm.py`, a per-project compose (`compose_natm.py`), then `build_runtime.sh --install`
   (export → `prepare_actor_glb.py` → `build_actor_lods.py` → `shrink_shadow_lods.py` → `region_variants.py` →
   `split_attachment.py` per prop → `merge_head_material.py` → `tools/install_model.py`). Then rebuild LOD2/LOD3 and
   check every level per the [LOD playbook](LOD_PLAYBOOK.md); `build_actor_lods.py`'s 6 % LOD3 is not finished.
6. **Bind and regress:** `assets_dev/worlds/mm6/models/actors.yml` (scale = native stand height / model height,
   `yaw_offset: -1.570796327`, `stride_length`, `run_stride_length`, `events` impact/cast/launch socket, `look`,
   attachments by node), a regression case in `game/outdoor/HeadlessOutdoorDiagnostics.cpp`, then
   `OPENYAMM_REGRESSION_FILTER=mm6_ ./build/game/openyamm --world mm6 --headless-run-regression-suite actors`.
   Viewer: copy `mm6_natm_claude/review/viewer/` + `viewer_tiers.py` + `update_viewer_manifest.py`, serve the
   creatures folder over http, `node claude_shared/check_viewer.mjs <url>`. Do not commit unless asked.

## In-game test locations (all creatures, user-chosen 2026-10-08)

Use the same camera for 3D (`debug.actor_models=true`) and sprites (`false`).
- **Outdoor:** New Sorpigal `oute3.odm`, position (-3718.493, 3245.946, 1.0), yaw 3.359 rad, pitch -13.751°.
- **Indoor:** Agar's Laboratory `6d19.blv`, position (1672.832, -2938.578, -46.896), yaw 3.132 rad, pitch -14.868°.

```sh
./tools/run_game.sh --isolated check-out --world mm6 --map oute3.odm --position -3718.493 3245.946 1 \
  --yaw-radians 3.359 --pitch-degrees -13.751 --set debug.actor_models=true --set debug.immortal=true \
  --set debug.menu_input_tour_path=/abs/tour.yml --warmup 3 --seconds 20
```

In the tour, spawn the tiers about 450 units ahead (outdoor around (-4157, 3149, 1); indoor around
(1223, -2935, -47)) with `actor spawn <monster id> 1 <x> <y> <z>`: open the console once, send every spawn, close it
once (reopening between commands dropped spawns). Hostile spawns with an immortal party walk in and attack.
Water creatures need water maps (`outa3.odm`, `oute1.odm`). Never run two game processes at once.

## Clip timing (user decision, 2026-10-10)

- Keep professional and authored clips at their intended speed; gameplay timing never changes for a model.
- Attack and cast: mark the blow/release with `animation.events` `impact`; author the wind-up close to the native
  action (±20 % reads fine); keep the follow-through within the recovery; missiles and spells charge at the
  events' `glow` sockets and leave their `release` (placed in `timing_review/`).
- Death and fidget can be any length (the engine finishes them); hit is cut at the native length, keep it short.
- Measure the blow (contact for a thrust, fastest tip motion while pointing at the target for a cut), never guess.
- Ease every one-shot clip from and to Standing frame 0 (the engine crossfades only 0.06–0.12 s, not into deaths).
- The engine plays `run` above 2.4 × scale units/s; check each tier's speed before polishing a run.

## Arm and hand gate (goblin postmortem, 2026-10-07)

Every arm, wrist, hand and prop fault was measurable before the user saw it. Before any clip is shown:
1. **Rig before poses:** each finger chain in its own finger, curling toward the palm; no upper-arm weight on
   chest/back/neck; armour copies the skin under it. Fix the rig, never pose around it. Sleeves follow the
   arm: a sleeve left on the chest lets a raised arm slide out and shows an empty open sleeve (Lizard Archer draw,
   `mm6_lzd_reduce_claude/scripts/sleeve_weights.py`); the shared gate does not catch it, so look at raised-arm
   clips from behind.
2. **Prop in the fist, from the item art**, grip solved per finger; check the prop direction against the forearm
   for the weapon type (blade ~90°; a spear along the thrust needs the underhand carry above).
3. **Key poses from the native frames as intent**, not traced: they are drawn for a front camera.
4. **Targets in a body frame** (chest or shoulder heading), hands kept outside the body envelope.
5. **Numbers on every frame:** contacts (G6), wrist swing ≤ 60°, forearm twist continuous and ≲ 90°, upper-arm
   roll stable over cycles, hand/finger stretch (G5), soles and jerk (`sole_probe.py`, `jerk_probe.py`).
6. **Posture vs Standing:** imported clips carry the source body's slump, clavicles, arm spacing, foot pitch and toes.
7. **Look where the user looks:** textured renders from the party's eye height, the viewer at 48 fps with
   close-ups of both hands and both feet, then game. Inspect them yourself first.
8. **Fix causes, re-run everything** through `rebuild.sh`; never hand-patch.

## Budgets, textures and runtime facts

- LOD0 is a ceiling, not a target ([modelling guidelines](../GAME_ASSET_MODELLING_GUIDELINES.md)): reduce while the
  head, hands and silhouette survive (natm 9.3k body + props). Keep the head at full density.
- Textures per [CLAUDE_CREATURE_TEXTURES.md](CLAUDE_CREATURE_TEXTURES.md): one shared set, region mask + per-tier
  ramps measured from each tier's own native pixels, 1K head set from a head-only retexture. Repaint skin with one
  albedo × Meshy's fine shading (luminance over its masked blur): Meshy paints face-sized salmon/brown patches.
  ORM red = per-class specular mask with `openyamm_specular_mask`; metallic 0.
- Sharpness: measure every body and head set with `claude_shared/texture_quality.py` before install and meet the
  targets in [Sharp textures](CLAUDE_CREATURE_TEXTURES.md#sharp-textures-layout-paint-resolution-and-grading-default-since-2026-10-30)
  (atlas use, density spread, fragments); request 4K paints and downsample once; grade gently.
- Binding: `actors.yml` as in the quick start; material variants via `KHR_materials_variants` on every primitive;
  attachments inherit the carrier's variant by name; clips start at t = 0; the engine checks native clip lengths.
- Shadow LOD is chosen by size in shadow texels, apart from the colour LOD and usually coarser
  ([LOD playbook](LOD_PLAYBOOK.md) §1, §5).

## Special cases (rules; details in the projects)

- **Upright vs guard clips** (bar1, magyar): the set's one-handed idle/run/attack are a low guard (users read it as
  crouching). Upright sources: Mixamo Standard Idle, the set's Unarmed hit, Mixamo walks; plant Mixamo attacks
  (`:plant`) and blend ~20 % of their legs back with IK steps; check what an attack actually does with the weapon
  ("Sword And Shield Attack (2)" is a shield bash).
- **Cloaks** (`mm6_thf_claude/`, `mm6_dru1_claude/`): replace every Meshy cloak weight with dense bone chains on
  the cloak's mid-surface (~10–13° apart), mantle front on the chest, only the shoulder mantle on the upper arm;
  verlet sim baked per clip with one-sided collisions on bone midpoints and capsules (with radius floors), rigid
  straight chains, damping 0.94/substep, temporal smoothing; gate with `cloak_poke.py` and `cloak_stretch.py`
  (openings in cm). Hands over a cloak in the HD master get fused: ask for arms out ~40°.
- **Skirts and strips** (gob2): one left/right mixture per strip; `g4_skirt.py`, `g6_skirt_poke.py`.
- **Staffs and two-handed props** (`mm6_pmn2_claude/`, `mm6_cle_claude/`): Mixamo two-handed clips keep both hands
  on the handle, Meshy's do not; key snapshots, never solve with an action attached; upright staffs need the
  forearm level and ~90° of forearm roll budget.
- **Open hands / casters** (thief, druidess): keep ~25 % of the source finger curl, mitten finger chain + two-bone
  thumb when Smart Topology returns open hands; the cast's wrist eased straight; spell sockets on the palm surface.
- **Skeletons** (`mm6_ske_claude/`): Smart Topology returns separate bone pieces; skip Meshy's rig, label pieces,
  joints at the pieces' axis ends, each piece 100 % to one joint; skull-only Smart Topology for the head.
- **Stance and scale** (titan, werewolf, druidess): author Standing from the bind pose when library idles stoop;
  clamp clavicle elevation both ways; straighten a crouched source idle before deriving the scale; scale from the
  standing height; narrow a wide stance to the native's.
- **Heads**: graft or project-and-bake per [CLAUDE_CREATURE_TEXTURES.md](CLAUDE_CREATURE_TEXTURES.md); remove
  eyeballs only with lid caps; a jaw bone needs each tooth piece wholly on one bone.
- **Winged humanoids** (`mm6_flying_demon_3d/claude_v2/`, `mm6_wdm_claude/`): wings from the native outline or
  classified by connectivity from the membrane; wing bones non-deforming during the body heat-weight solve;
  procedural flap on the native cycle; never cut the membrane from the back.

## What did not work (avoid)

- MakeHuman/MPFB bodies or proxy rigs as the shipped body or rig (likeness lost, misplaced joints, nine review
  rounds on the goblin).
- Texturing before the mesh and rig are final; conformal or Smart UV unwraps of noisy Meshy meshes (use Meshy UVs).
- Choosing a weapon clip by its name; per-frame independent arm solves; synthetic foot paths for a run.
- Trusting retargeted feet, toes, clavicles or idles without measuring them.
- Inside tests against open shells (any point behind a feather card counts as "inside").
