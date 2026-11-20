# MM9 Ebora body (mm9_ebora) — 3D actor, 2026-10-31

MM9 `EBORA.abc` (68 nodes, 21 clips + bind), rows 301 **Ebora** L99 (`MM9 301 Ebora`, skin EBORA.dtx) and 302 **Concubine**
L60 (`MM9 302 Concubine`, skin SIREN1.dtx). The Concubine row uses the **same model** (`ebora.abc`), so both are tiers of this
body. `EBORACONCUBINE.scr` picks SIREN1-4 at random (`SetModelFilenames "models\ebora.abc", "skins\SirenN.dtx"`); SIREN2-4 are
carried as extra variants for that script, unbound. EBORA2.dtx is on no row and no script.
Decided from the ABC: a two-armed Biped (`Bip01`, five two-bone fingers per hand) with two bat wings on their own chains
(`Bone48`-`Bone69` and `Bone13`-`Bone46`, children of Spine2). Humanoid route for the body (MM9 skeleton, MM9 clips, never
Mixamo); the wings follow the animal brief's rule of keeping MM9's own chain and motion.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_ebora.glb` (`tools/install_model.py --world mm9`), sha256 `5a8a356830dd...` = `export/mm9_ebora.glb` (s2 throat tint, ear sweep 2026-11-02; previous install `work/installed_preear.glb`, ad8aff4fc94e, Concubine face and hair fix; before it `work/installed_hf3.glb`, f141099bc209), variants `eb`, `s1`, `s2`, `s3`, `s4` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` (`scripts/bind_actors.py 1.14 4.0` under the flock), scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.14 / run 4.0, `cast: AttackRanged`, sockets `palm_left` = `LHand1`, `palm_right` = `RHand1`. Ebora skin `eb`, Concubine `s1`. Table generator run under the flock: tables unchanged (both rows already had descriptors) |
| Triangles LOD0/1/2/3 | 15,299 / 7,649 / 2,751 / 906 (Concubine fix: 733 hair back faces; head fixes 2 removed the fringe stub). LOD0: torso + arms 5,126, head set 6,177 (5,444 before + 733 hair backs, flat_shading_check counts) (face subdivided once), legs 1,692, wings 2,304 |
| Skeleton | 86 deforming joints of 112 nodes: MM9's 68 + 30 finger bones (15 per side, from the mesh) + 9 half-joint helpers + 6 wing pleat helpers (`XPleat{A,B}{1,2,3}`) |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged/cast `Castspell`, Hit `wince1`, Death `die2`, Dead; script clips Fidget2 `fidget2`, Taunt `taunt`, Hit2 `wince2`, Backpedal, BackpedalRun, Fly `fly`, Flap `flap`, Launch `launch`, Land `land`, HitAir `WinceAir1`, DeathAir `DieAir1`, Fall `fall1`, FallDown `FallDown1`. All 21 MM9 clips carried |
| Events (MM9's) | `attack_melee` impact 0.407 s (`rattack`); `attack_ranged`/`cast` impact 0.6 s: MM9 has no range event on Castspell (only `speakanimsound` 0.588); both palms thrust forward at 0.6-0.7 s, release `palm_right`. MM9 has no sockets on this model: `LHand1`/`RHand1` are ours (palm centres) |
| Textures | eb: torso 2048x1024, head 2048 (head pass), legs 1024 colour + normal (1024x512 / 1024 / 512); s1: the same three colour + normal images (siren paint); wing 2048x1024 colour, 1024x512 normal; ORM shared; region masks for s2-s4 (body) and s1-s4 (wing). 22 images |
| GPU memory | about 24 MB for all tiers (BC7/BC5 estimate with mips): colour 13, normals 5, ORM 3, masks 2 |
| Meshy credits | **25 / 25**: body Smart Topology 5, retexture Ebora 10, retexture Concubine (siren1) 10 (backup account; backup balance 3,900 -> 3,875, gate 3,785 never reached) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_ebora_claude/review/viewer/ revision `cf10-20261102`, tiers `eb`, `s1`-`s4` |

## Route (`scripts/`)

0. **Sources:** `convert_abc_model.py --scale 0.0256` with each skin (`source/ebora`, `ebora2`, `siren1-4`). Raw ABC space
   throughout (L at -x), `mirror_glb.py` last: the bind is asymmetric in the feet and wings, never `mirror_source.py`.
1. **Masters** (`references_hd/`, Codex, `scripts/codex_masters.sh`): Ebora without wings (the wings are built on MM9's chain),
   from renders of the MM9 model with its wings hidden.
2. **Meshy Smart Topology** on `00_three_quarter_clean.png`: 22 clean parts, five separate clawed fingers per hand.
3. `step1_clean.py` (raw MM9 space, exact mirror of the figure's left half, symmetric decimate to 10.4k), `assemble.py`
   (labels; hair cut at the shoulder blades as MM9's and capped, so the wing roots clear it; two back studs dropped).
4. `fit_rig.py` (spine heights MM9's, legs and arms by sections, wrist at the narrowest ring, fingers by geodesic merge
   levels), `heat_weights.py`, `weights.py` (knee/elbow tight blends, rigid head above the jaw line, hair hanging from the
   skull, belt/emblem on the body under them, half joints).
5. `bind.py`: each bone's bind frame is MM9's rest frame turned onto our bone (MM9's local rotations give MM9's poses);
   fingers take MM9's Finger0-4 frames so its curl applies (`finger_alias`, 1.0/0.7/0.4 per joint); wing bones keep MM9's
   local transform under our Spine2, the wing roots moved 5 cm back so they stand as far behind our back as MM9's (7 cm).
6. **Wings** (`build_wings.py`): MM9's wing is rigid per vertex (every outline point at a bone head). Ours: spar tubes on the
   same bone heads (arm root buried 7 cm in the back with the body's weights, then Bone48 -> Bone49 -> wrist; three fingers;
   a thumb claw), three Coons membrane fans between the spars with scalloped trailing edges, harmonic weights between the
   spar and edge weights, solidified to a 7 mm shell. The web along the back follows Bone48 as MM9's does (tied to the body
   it stretched into a sail when the clips swing the wing arm up 70 deg). Wing UVs: front projection of the membrane, both
   wings and both layers share it; the spars take the UVs of their own centre lines, so one painted image carries both.
7. **UVs** (`uv_eb.py`, frozen in `work/uv_frozen.npz`, never re-run): one 4K Meshy upload holding three runtime sets
   (torso+arms bottom half, head set top-left quarter, legs top-right quarter).
8. **Paint:** Codex paints on our exact clay (`references_paint/`, Ebora and siren1; the safety filter refused Ebora's right
   view, so it is the mirrored left view: the figure is symmetric), then a Meshy 4K retexture each (`compose_eb.py`,
   downsampled once). Wing: a Codex paint on the UV template (`codex_wing.sh`), warped onto the template by 13 matched
   points (`compose_wing.py`). `finish_eb.py` (AO, gentle grade), `tone_eb.py` (skin towards MM9: Ebora median sRGB
   248,102,51 -> 212,52,20 against MM9's 204,39,13; siren lighter; orange paint on hair charts repainted; Meshy's dark slash
   marks in the skin inpainted).
9. `subdiv_face.py`: one subdivision level on the face front (UVs and weights interpolated, paint unchanged): the decimated
   face read faceted at full size. Then `face_shape.py` (head fixes 3): mouth and nose reshaped, vertex moves only.
10. `rebuild.sh [--install]`: weights -> bind -> wings -> merge -> face subdivision -> face reshape -> GLB -> clips (`clips_mm9.py`, soft
    joint-offset line, Running lowered 0.794 m: MM9's `run` clip floats, model lifted so the floor is y 0) -> arm
    corrections (`arm_groups.txt`) -> wing pleat keys -> half joints -> LODs -> shadow fix -> tiers (`tier_glb.py`) ->
    winding fix -> floor -> sockets -> `mirror_glb.py` -> winding and bone-length checks -> install.
    `viewer_update.sh` (tiers baked for three.js), `gates.sh`, `closeups.sh`, `strips.py` + `vs.sh` review it.

## Tiers

| Tier | Row | Paint | Notes |
|---|---|---|---|
| `eb` | 301 Ebora (bound) | own Meshy paint | red skin, black corset with skull cups, studded legs, red wings |
| `s1` | 302 Concubine (bound) | own Meshy paint (siren1 look) | copper hair, peach skin, burgundy brocade catsuit, orange wings (wing ramp) |
| `s2` | script skin SIREN2 | s1 + region mask + ramps | white-blond hair, orange brocade, orange wings |
| `s3` | script skin SIREN3 | s1 + region mask + ramps | black hair, pale skin, dark purple suit, orange wings |
| `s4` | script skin SIREN4 | s1 + region mask + ramps | black hair, pale skin, dark blue suit, blue wings |

Body regions (s2-s4): hair, skin, suit, black; each region's target is MM9's median colour of that region in that skin (texels
classified on SIREN1, read at the same texels of SIREN2-4: the four skins share one layout) times our own relative
luminance, so our detail stays. Wing regions: membrane (MM9's wing strip per skin), bone (own grey).
**Deviation from one shared set:** Ebora and the Concubine are different designs on the same MM9 mesh (armoured demoness
with red skin vs. human-skinned woman in a catsuit; different faces), so each has its own colour and normal images (torso,
head, legs: 4 MB colour + 1.75 MB normal extra). SIREN2-4 use ramps on the Concubine's set as the rule asks.

## Checks (installed GLB)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only` (48 fps) | Hands 0 in every ground clip but AttackRanged R 1.4 cm (2 frames over 1 cm); script clips Land L 1.6 cm (4 frames), Launch 0.4. Forearms: Death L 4.7 cm / R 5.9 cm and the corpse's L forearm 4.7 cm lie **in the wing membrane she falls on** (sheet_joints_2 jcdd3, jcde5); Launch R 1.9, Land R 1.3. Finger stretch max 1.88 (Taunt), 3.92 in the script clip FallDown. Five chains per hand |
| `jitter_gate.py` against the same clips without arm corrections | **0 fails** (Land and Death were 3.02 and 2.57 mm/f2 shoulder skin with larger corrections; now 1.28 and 1.25) |
| `detached_parts_audit.py` | **0 detached** in every pose (29 components; the wing membranes ride on the buried spar roots) |
| `bone_length_audit.py` | 20 limb joints checked, **0 stretching** (every build) |
| `check_winding.py` | **0** inverted closed parts |
| `flat_shading_check.py` | torso 0.00, head 0.01, legs 0.00, wing 0.00 after the bent normals (pass 2; was 0.21) |
| `floor_audit.py` | 2 bindings ok: stand 0, walk -0.5..+0.4, living -0.5, dead 0 |
| `texture_quality.py` | torso 2048: atlas 57.1 %, spread 1.1, fragments 0.2 %, stretch 1.06; head 1024: 60.6 %, spread 1.64 (face 1.9x by design), stretch 1.16; legs 1024: 56.5 %, 1.09, 1.07. Wing (own projection, not uv_atlas): 36.9 %, stretch p90 2.41 (the membrane's slant out of the front plane and the spar strips; deviation) |
| Regression `--world mm9 --headless-run-regression-suite actors` | `mm9_actor_models_build_every_binding` **PASS**, 158 descriptors on 65 models, 0 failed (final install). The same suite run also printed `[FAIL] out05_event_clearance_completes_from_monster_killed_hook - could not load gameplay data` (an MM8 map test: "world.yml id 'mm8' does not match active world 'mm9'"), not touched by this body |
| Viewer `run_creature_review.py check` | 110 switches, 0 failed, 0 console errors |

### Collapse (`scripts/collapse_gate.py` from the Evil Sorcerer, all LOD0 primitives, 30 fps, worst single frame per region; wings A/B = each wing's bones and pleat helpers)

| Clip | knee L/R | hip L/R | groin | shoulder L/R | elbow L/R | neck | head | torso | finger | wing A/B (exposed) | exposed hip L/R/groin |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 0/0 | 4/1 | 1 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 156/148 (75/45) | 4/1/1 |
| Walking | 0/0 | 3/3 | 2 | 0/0 | 0/0 | 0 | 0 | 1 | 0 | 156/148 (68/44) | 1/3/1 |
| Running | 10/9 | 18/15 | 17 | 0/0 | 7/1 | 0 | 0 | 1 | 0 | 156/148 (70/45) | 14/1/14 |
| Backpedal | 0/0 | 5/4 | 2 | 0/0 | 0/0 | 0 | 0 | 1 | 0 | 156/148 (72/42) | 4/3/2 |
| BackpedalRun | 0/0 | 5/4 | 2 | 0/0 | 0/0 | 0 | 0 | 1 | 0 | 156/148 (71/41) | 4/3/2 |
| Fidget | 0/0 | 5/1 | 2 | 0/0 | 0/5 | 0 | 0 | 1 | 0 | 156/148 (72/43) | 4/1/2 |
| Fidget2 | 0/0 | 4/2 | 2 | 0/0 | 0/0 | 1 | 2 | 1 | 0 | 156/148 (69/42) | 4/1/2 |
| Taunt | 0/0 | 5/1 | 5 | 0/0 | 0/5 | 0 | 0 | 0 | 2 | 156/148 (71/47) | 5/1/3 |
| AttackMelee | 0/0 | 7/2 | 11 | 0/4 | 0/0 | 2 | 2 | 0 | 1 | 167/156 (71/43) | 6/2/7 |
| AttackRanged | 0/0 | 5/5 | 5 | 4/3 | 1/0 | 5 | 2 | 4 | 4 | 156/148 (75/45) | 4/1/0 |
| Hit | 0/0 | 4/3 | 5 | 3/1 | 1/0 | 2 | 0 | 2 | 0 | 156/148 (71/40) | 3/1/3 |
| Hit2 | 1/4 | 4/6 | 16 | 0/0 | 3/0 | 5 | 2 | 0 | 0 | 156/148 (75/45) | 4/1/0 |
| Death | 2/12 | 5/17 | 6 | 7/1 | 0/1 | 22 | 1 | 6 | 0 | 167/172 (74/47) | 1/9/0 |
| Fly | 0/0 | 3/1 | 2 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0/0 (0/0) | 3/1/2 |
| Flap | 0/0 | 3/1 | 2 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0/0 (0/0) | 3/1/2 |
| Launch | 6/10 | 10/4 | 17 | 12/11 | 0/0 | 0 | 1 | 1 | 0 | 156/148 (75/45) | 4/1/0 |
| Land | 6/10 | 10/4 | 17 | 11/10 | 0/0 | 0 | 1 | 1 | 0 | 156/148 (75/45) | 4/1/0 |
| HitAir | 1/0 | 4/4 | 20 | 0/0 | 0/0 | 2 | 1 | 4 | 0 | 0/0 (0/0) | 3/4/17 |
| DeathAir | 1/0 | 4/4 | 20 | 0/0 | 0/0 | 2 | 1 | 4 | 0 | 0/0 (0/0) | 3/4/17 |
| Fall | 0/0 | 3/12 | 23 | 0/1 | 0/0 | 0 | 0 | 2 | 0 | 1/0 (0/0) | 3/11/10 |
| FallDown | 1/3 | 3/13 | 21 | 0/2 | 0/1 | 2 | 2 | 2 | 10 | 1/0 (0/0) | 1/12/10 |
| Dead | 0/0 | 1/6 | 1 | 7/0 | 0/0 | 0 | 0 | 2 | 0 | 156/172 (73/90) | 1/6/1 |

Body regions are in the range of the accepted bodies (Evil Sorcerer hips 7-13, armpits up to 30): the worst exposed are
Running hip L 14 and groin 14, the air reactions' groin 17 (script clips), Death hip R 9. Neck 22 in Death has 1 exposed.
**Wings fail by count:** about 150 faces per wing (of 1,152) whenever the wings fold (every ground clip), 40-75 exposed per
wing. MM9's clips close the fan at the wrist (arm to third finger 46.8 -> 6.5 deg, fingers 21 -> 7 deg), and MM9's own wing
flattens the same way. Attempt: pleat helpers that turn each panel's mid-line out of plane. A full pleat cut squashed faces
(area under 20 %) in Standing from 99 to 23 but stood out like a sail; half still did; kept 0.6/0.6/0.2 (63 squashed). Most of
the remaining count is the gate's flip test on faces inside the closed fan. Seen in `sheet_wing_pleat*.png`, `sheet_wing_web.png`.

## Deviations

- **Wings are not Meshy:** built on MM9's chain (MM9's own motion), with our membrane and a Codex-painted texture.
- **Handedness:** `mirror_glb.py` last; figure true-handed (`L Hand` +x facing +Z), inferred from coordinates and names.
- **Limb lengths:** ours from the mesh; only Pelvis (absolute) and Scene Root translate; others take only offsets beyond
  4 mm on the soft line.
- **Proportions:** our figure is fuller than MM9's (waist depth 20 cm against 15) and stands wider.
- **Arm corrections** (`arm_groups.txt`, `arm_clear.py` + `arm_soft.py`, solved on keys, faded at the ends): AttackRanged, Taunt,
  Fidget 20 deg / 0.10 s; Launch 16 / 0.18; Land 10 / 0.25; Death 20 / 0.25. Larger caps on Land and Death cleared more but failed
  the jitter gate; the remaining forearm contacts in Death and Dead are with the wing she lies on.
- **Hair:** shorter than the masters (cut at the shoulder blades, as MM9's) so the wing roots clear it.
- **Wing fold:** MM9's clips close the fan at the wrist (Standing: arm to third finger 46.8 -> 6.5 deg). A full pleat that keeps
  each half's rest opening cut squashed membrane faces in Standing from 99 to 23 but stood out like a sail; kept per panel
  0.6 / 0.6 / 0.2 (63 faces under 20 % of their area).
- **Run stride** from MM9's velocities (300/60 x 0.7 s x walk stride): the run has almost no planted phase to measure.
- **s2 lips** orange (MM9's dark red): the lip paint shares the suit region on that tier.
- **Concubine skin** lighter than MM9's siren1 (tone moved only part of the way); s3/s4 faces read stark white, as MM9's pale
  skins, with less face detail than s1.

## Sheets (viewer shots unless noted, all read by me)

`review/sheet_mm9_vs_ours.png` (8 clip poses, MM9 Blender render beside ours), `sheet_tiers.png` (MM9 skin per tier beside
our five tiers: quarter, rear, face, flight), `sheet_joints_1.png` (crouch of the take-off, running, arms raised: armpits,
elbows, knees, groin), `sheet_joints_2.png` (the fall at 0.96 s and the corpse: knees, groin, neck, forearm on the wing),
`sheet_joints_3.png` (head front, quarter, side, back; hands; wing roots; flight), `strips_eb_1.png`, `strips_eb_2.png` (all 22
clips, 7 frames), `sheet_wing_pleat.png`, `sheet_wing_pleat_half.png`, `sheet_wing_pleat_final.png`, `sheet_wing_web.png` (the
fold attempts), in game `sheet_ingame.png` (+ `review/ingame/`). Gate numbers: `review/gates/`.

## What was not checked

- **Playback at normal speed** by eye (agents cannot watch video); motion judged from strips and the jitter gate.
- The bathhouse itself (Ebora's map): the in-game check is spawned actors on map 9021 (over water, the `goto` landed there),
  full-body frame, idle, death and a hostile cast. Ebora's camera cut, letterbox and the concubines' scripted launch are
  engine and script work (below).
- **Build of each sheet:** strips, tier sheet and siren faces are from the final build (r10-r12); the in-game run is the r8
  install (sha f72ad1550201: same mesh and wings, before the Death/Land arm settings and the s2-s4 lip fix); the joint close-ups
  and the MM9-vs-ours sheet are from r3-r4 (before the pleat and the wing web change; body and clips the same).
- LOD1-3 and the shadow meshes close up; Android; saves; sounds and footsteps.
- s2-s4 in game (nothing binds them); their faces only in the viewer at full size from the front.
- Charge glow timing and the spells' visuals against MM9's (Column of Fire, Souldrinker, Sparks, Elemental Bolt).

## Second pass, 2026-10-31 (coordinator's review, 0 credits)

| Point | Cause | Fix | Result |
|---|---|---|---|
| Spread wings lost the tier colour from the front (dark maroon, siren4 near black) | Not the mask or ramps (folded wings were right): the membrane is a closed 7 mm shell with its own outward normals, single-sided like every other material. Raised for flight, the wing's front layer faces down and away from the top light, so the engine's ambient term `0.65 + 0.35 * max(normal.z, 0)` and the sun left it dark. The Winged Mutant solves membranes the same way (offset copy, no `doubleSided`); the engine's `doubleSided` flips the normal toward the camera, which would give the same dark underside | `build_glb.py`: both membrane layers get a bent normal, tilted along the wing's in-plane up axis (x1.6), carried by the wing bones, so the underside of a raised wing is lit like the top. No geometry, UV or texture change; kept on LOD1-3 | Fly front shows red / orange / orange / orange / blue on eb / s1-s4 (`sheet_tiers.png`), and orange in game (`review/ingame2/h06_crop.png`). Wing flat-shading 0.21 -> 0.00 |
| Death and Dead forearms 4.7-5.9 cm in the wing | MM9's die2 lays the left forearm over the raised left wing fan: 98-107 arm edges through the membrane in the fall, 60-73 in the corpse (`scripts/arm_wing_cross.py`) | Tried: turning the wing fan in the floor plane (+/-25 deg: 112-149, worse), the pleat avoiding the arms (no change). Kept: `scripts/arm_lay.py`, the left upper arm lifted 18 deg about an axis across the arm, eased over the whole Death clip and held in Dead (replaces the old Death `arm_clear` group). 22-30 deg cleared the fall completely but failed jitter (upper arm +1.2-3.1 deg/f over MM9) | Corpse 0 crossings, arm gate Dead L 0; fall 24 crossings at 0.92 s for a moment, arm gate Death L 1.3 cm (was 4.7). Jitter 0 fails. Death R 6.0 cm is the gate's cone test against the folded wing under the arm: 0 crossings, lying on top (seen, close-up `review/shots/rf0.png`, `rf1.png`) |
| Concubine skin lighter than MM9's SIREN1 | Tone moved part way and its mask missed the pale highlights | `scripts/tone_sr.sh`: wider mask, target 216,146,104 | Median skin 230,160-169,118-126 -> 219,150-159,107-114 (MM9 222,152,109) |
| siren2 lips orange | Lip paint fell in the suit and hair regions | `tiers_eb.py`: lips (face charts, crimson hue) and eyes kept out of every region, so all tiers keep the siren1 paint there (all four MM9 sirens have dark red lips) | Dark red lips on s2-s4 (`sheet_tiers.png` face column) |

Reshot on the pass-2 build and read: `sheet_mm9_vs_ours.png`, `sheet_tiers.png`, `sheet_joints_1/2/3.png`, in game
`sheet_ingame_p2.png` (+ `review/ingame2/`, Ebora and Concubine idle, death, a hostile Concubine flying and casting lightning).
Seen and left: small dark marks in the skin of the upper chest and shoulder close up (Meshy paint the inpainting missed,
`sheet_joints_2.png` jcde3-5, `sheet_joints_1.png` jcar0-1).

## Head pass, 2026-11-01 (user: "imo needs better head texture"; 0 Meshy credits)

The Meshy head was flat orange with smeared white eyes, soft features, a dark fringe tip on the forehead and noisy hair.
Route of `mm9_njam_claude` r14:
1. `scripts/head_clay.py`: clay renders of our own head set (true-handed), eight ortho views incl. a close face view `08_face`.
2. Codex (`scripts/codex_head.sh ebora|siren`, briefs `references_head/CODEX_BRIEF_HEAD*.md`): Ebora and siren1 painted on
   that clay, all eight views, the close face first; MM9's head renders and skin as look authority.
3. `scripts/fringe_lift.py` (in `rebuild.sh`, vertex moves only): the fringe's centre tip folded up from z 0.931 to 0.965, off the
   forehead (it was the dark strand the user saw).
4. `scripts/dump_head.py work/mesh_sub.npz work/head_faces.npz` and `scripts/dump_head.py work/mesh_shp.npz work/head_faces_shp.npz` (after a rebuild; head fixes 3) + `scripts/project_head.py a eb` / `s sr` (2048), then `tone_eb.py`, `tone_sr.sh`, `tiers_eb.py`, `rebuild.sh`: `08_face` is the face's ONLY source inside the face
   frame, placed by 15 measured landmarks (eyes, corners, nose base and wings, mouth corners at the lip bulge, chin, jaw;
   `references_head/landmarks.json`, thin-plate warp, max offset 60-63 px); the other views paint outside it only; z-buffer over
   every head layer (skin, hair, fringe, horns, ears); hair texels refuse skin-coloured paint, skin texels refuse hair-coloured
   paint outside the face frame (inside it the rule deleted the brows, lash lines and dark lips: removed there); gentle
   luminance normal (0.45; 1.6 read as orange peel).
5. `tone_eb.py`: the projected head replaces Meshy's; Ebora's skin takes the body's tone at the neck seam (`scripts/seam_gain.py`,
   22 shared edges: head 180,61,35 -> body 218,55,21); the siren's needs none (206,135,98 against MM9's 222,152,109; a seam gain
   lightened it to cream).
6. `tiers_eb.py`: the head's tier regions now come from the mesh parts (hair/fringe, skin, horns), not a colour test (the painted
   shading dropped skin into the suit and black regions: orange and black patches on siren2-4); lips and eyes keep the siren1
   paint, limited to the mouth area (the hairline's copper matched the lip test); the hair ramp has a luminance floor (sRGB ~40)
   so siren3/4's dark hair keeps its strand sheen (it read flat black).

Read at full size, five views per tier (`review/sheet_head_full.png`) and `review/sheet_tiers.png`: crisp white eyes with lash
lines, defined brows, nose and plum lips on Ebora; green eyes, red lips, copper locks on siren1; clean faces on siren2-4.
Left: the mouth is still small (Meshy's narrow pursed mouth shape; the paint is fitted to it); the nose bridge carries a bright
streak along the mesh's thin ridge; siren3/4 hair reads navy where MM9's is blue-black; a faint brown tint at siren2's
hairline; the central fringe ends in a short dark point at the hairline (a widow's peak, off the face). Head image 1024 -> 2048
(+4.5 MB colour for eb and s1, BC7 estimate).

Head fixes 2 (coordinator, 2026-11-01, 0 credits):
- **Hairline block:** paint, not geometry. Codex drew the clay's old notch as a dark column down the forehead centre (|x| < 6 mm,
  z 0.93-0.98). Fixed in three parts: `fringe_lift.py` drops the folded fringe stub (18 faces) and the hair shell's tongue under
  the arch (16 faces); `dump_head.py` labels the scalp strip the tongue covered as hair (62 faces), so projection, fill and tier
  mask treat it as hair; `project_head.py` repaints the notch column from the clean forehead below it, blending to hair at the
  scalp. Reads as a plain widow's peak on every tier. (A knob recolour tried on the way striped the arch: removed.)
- **Nose bridge streak:** `build_glb.py` smooths the normals of the ridge vertices with the face beside them (202 vertices) and
  `project_head.py` pulls the ridge's paint 70 % towards the local skin mean. Now gentle shading.
- **Ears:** `project_head.py` darkens them towards the back edge and the root (up to 28 %). Reads as form on eb, s1, s2; on
  s3/s4 the pale-skin ramp flattens it and they still read as pale cards (left).

Head fixes 3 (user review 2026-11-01: "mouth too thin, nose too tall and thin, consult the master"; "I can see the ear painted
also on the hair"; 0 credits, Codex not used):
- **Causes.** Mouth and nose were the **geometry**: Meshy's pursed mouth was 1.7 cm wide (0.36 of the eye spacing; HD master
  and MM9 about 0.7) and the nose a 1 cm knife ridge (0.2; master and MM9 0.4-0.5). The Codex face paint was painted on that
  clay, so it copied both. The midline section puts the lip junction at z 0.832, the nose base at 0.847 and the tip at 0.855.
  The "ear on the hair" was two things: the `ears` part (7) is a pair of 14 cm leaves from the temple to behind the jaw, floating
  1-3 cm off the skin in front of the hair edge (Meshy's side locks: the master and MM9 show hair there, and Codex painted them
  as hair in the right view and as a small ear plus hair in the others). Labelled skin, they refused the hair paint and took skin
  fill: a big skin flap over the hair. On top of that, Ebora's dark red ear shading from the left view landed on the hair
  behind the ear, because dark red sits nearer the blue-black hair than the bright skin in RGB.
- `scripts/face_shape.py` (in `rebuild.sh` after `subdiv_face.py`; vertex moves only, UVs and weights kept): the mouth corners
  go from 8.6 to ~17 mm under a horizontal displacement that rises across the lips and gives back over the cheek by 5.5 cm (zero
  net: the face outline is unchanged). Points follow the face's measured front surface backwards, with the slide capped on the
  steep jaw sides. Lips are taller (upper 1.6x, lower 1.35x, nothing at the junction itself) and the lower lip is a little fuller. The pucker's radial folds are
  Taubin-smoothed (they read as a dark zigzag once widened). Nose: wings 5 -> ~8.5 mm, the bridge widened less, base and tip
  lifted 4 mm. 0 front flips; the moved faces keep 0.33-4x their area, except two inner-crevice faces under the upper lip.
- Projection through the reshape (`project_head.py`): texels sit on the reshaped head (`work/head_faces_shp.npz`, dumped from
  `work/mesh_shp.npz`) and sample the paint at the field's smooth inverse (damped fixed point, residual < 0.001 mm). Letting the
  paint simply ride on the moved vertices kinked painted lines at triangle edges. The inner faces of the lip junction, now
  in view, take a deep lip tone (they were unpainted and filled as skin, which left a pale slit). The nose-ridge tone now comes
  from the skin beside the nose at the same height (the old 9 mm mean kept a pale highlight that the widening spread into a stripe).
- Side locks: `dump_head.py` relabels part 7 as hair (104 faces), so projection, tone and the tier masks treat them as hair.
  `project_head.py` (Ebora only) counts any clearly red paint (R - max(G, B) > 0.08) as skin for the hair texels' refusal test.
  The old ear shading went with the part.
- `tone_eb.py`: Ebora's neck-seam gain (R x1.31 in linear) clipped the light mid-face at 255. A soft shoulder above 0.72
  linear keeps the highlight gradient.
- Checks on the install (sha f141099bc209), identical to the 17:12 install (d0abf59d2ff8, `review/gates_base/`): jitter 0
  fails, detached 0, bones 0 stretching, winding 0, flat head 0.01, texture head stretch p90 1.19, arm/hand and collapse
  tables unchanged line by line (`review/gates_hf3/`). Regression `mm9_actor_models_build_every_binding` PASS (158 on 65,
  0 failed) before and after. Viewer `h16-20261101`: check 110 switches, 0 errors.
- Sheets (read at full size): `review/sheet_face_compare.png` (HD master, MM9 Ebora and SIREN1 front and three-quarter;
  ours per tier eb, s1-s4 close up; Ebora before at 0.42 m), `review/sheet_head_sides.png` (both three-quarters and sides,
  eb and s1, plus s2-s4), `review/sheet_head_clips.png` (Taunt 1.0 s, AttackMelee 0.4 s, eb and s1: the head is rigid, with no
  jaw bone in MM9's rig, so the mouth never opens).
- Left: the upper lip is still thinner than the master's (its painted vermilion is thin; the geometry is taller now). There
  is no visible ear any more (as in the master and MM9). The nose bridge keeps a soft highlight (paint, plus head fixes 2's ridge normal
  smoothing). Small dark speckles on the siren hair paint (s1, s3, s4) and siren3/4's grey brows are older and untouched.
  Rollback copy of the previous install: `work/installed_hf2.glb`.

## Concubine face and hair (user note 2026-11-01 evening; 0 Meshy credits, 1 Codex image run)

User: "ebora - accepted, ebora - has ugly face + there are some spaces in the hair? like holes?" (screenshots of the s1
Concubine: `review/user_notes/s1_hair_holes_front.png`, `s1_hair_holes_side.png`). Ebora's look is accepted and was kept.

| Point | Cause | Fix |
|---|---|---|
| Holes in the hair at the temple, a strand floating by the cheek, dark slivers by the far eye | The hair shell (part 1), the fringe (4) and the side locks (7, the old "ear" cards) are single-sided open sheets. Past the face's profile the camera sees their inside, which every renderer culls: grey background between the strands, the far side lock reduced to its edge | `scripts/hair_backs.py` (in `rebuild.sh` after `face_shape.py`): every hair face whose inner side is ever the nearest surface from ~100 directions round the head (torso occluding) gets a reversed copy 0.5 mm inward with the same UVs, weights and part, so the inside shows the hair paint. Copied groups smaller than 8 faces on one UV island grow by edge-neighbour rings to 8 (lone copies counted as UV fragments: 3.0 % of the head), 733 faces in all (shell 541, fringe 88, side locks 104); nothing existing moves. Shared mesh, so Ebora gets them too (her face pixels unchanged, below) |
| Sullen, crooked face | The siren brief asked for "a fierce ... cold slight smile": Codex painted knitted brows with frown lines, a pursed mouth and heavy jaw shading; the face paint was painted on the unshaped clay and stretched through the reshape inverse | New Codex paint `references_head/s2_08_face_clean.png` (brief `CODEX_BRIEF_HEAD_SIREN_CALM.md`, attempt 1 of 2) painted on the **reshaped** head's clay (`references_head/clay_shp_08_face.png`, `head_clay.py` with `work/head_faces_shp.npz`): calm, symmetric, relaxed arched brows, dark red lips. `project_head.py`: a tier whose landmarks carry `face_clay: shp` projects 08_face from the reshaped texel positions with the clay landmarks `clay_face_shp` (24 points: the 15 of before re-measured on the new clay, three hairline anchors, six brow points that lift the inner brows 18 px against the outer ones; without them the eye shift steepened the brows into a frown). Ridge softening stops below the eyes for this face (at eye height the "skin beside the nose" is the eye corners: a dark band between the eyes) |
| Muddy chin from below | The underside of the chin and jaw is seen by no view (fill from the jaw-line shading) and gets no top light | `project_head.py` (siren only): those texels' 1 cm mean is moved additively to the neck front's skin, up to 18 % lighter where they face down, the limit following the jaw line (off the lower lip). A per-channel gain first tried saturated a blush spot to orange |
| Jagged pale seam at the neck base | Torso paint lighter and yellower than the head at the 22 zigzag seam edges (219,159,111 against 210,129,94), and Meshy's dark island padding on the torso side of 9 of 22 edges (luminance 0-35): a thin dark "W" | `project_head.py` (siren only): per seam point a linear gain torso/head spread over the head skin and faded out 4 cm above the seam; `scripts/seam_rim.py sr` (after `tone_sr.sh`, before `tiers_eb.py`) replaces the texels of the torso faces within 1.5 cm of the seam darker than 0.85 x skin, plus 6 px of padding around them off the island, with the nearest good skin texel (7,833 texels): the neck faces' UVs touch a dark brown blob of Meshy paint beyond the island, which the texture filter pulled in as a dotted brown band along the zigzag. The zigzag still showed: the shared ORM images carry near-black AO (13-16 of 255) on the thin seam faces of both sides. `scripts/seam_rim.py orm` repairs the AO channel of `eb_head_orm.png` (head skin faces only, 7,295 texels) and `eb_torso_orm.png` (1,901 texels) inside the seam zone the same way. Shared with Ebora: her neck base loses the same dark zigzag; nothing above the neck changes |

Checks on the install (sha ad8aff4fc94e; geometry, UVs, weights and normals byte-identical to the gated candidate
`work/cf7_candidate.glb`, `review/gates_cf/`), against the previous install (`review/gates_hf3/`):

| Gate | Before (f141099bc209) | After (ad8aff4fc94e) |
|---|---|---|
| `check_winding.py` | 0 | 0 |
| `bone_length_audit.py` | 0 stretching | 0 stretching |
| `detached_parts_audit.py` | 0 detached, 29 components | 0 detached, 38 components (the hair back copies; they ride on the same weights) |
| `flat_shading_check.py` | head 0.01 (5,444 faces) | head 0.01 (6,177 faces); torso/legs/wing unchanged |
| `jitter_gate.py` | 0 fails | identical output, 0 fails |
| `arm_hand_gate.py` | (table above) | identical output |
| `collapse_gate.py` | (table above) | identical except neck worst 22 -> 23 (Death) and 2 -> 3 (HitAir, DeathAir): copies of the same squashed nape hair faces; exposed counts unchanged |
| `texture_quality.py` head | atlas 60.3 %, spread 1.64, fragments 0.1 %, stretch 1.19, 58 islands | atlas 60.3 %, spread 1.63, fragments 0.1 %, stretch 1.20, 87 islands, uv sum 71.5 % (copies reuse existing texels) |
| `floor_audit.py` | 2 bindings ok | 2 bindings ok, same numbers |
| Regression `mm9_actor_models_build_every_binding` | PASS 158 on 65 | PASS 182 on 75 (other bodies installed since); known `out05_event_clearance...` world-mismatch FAIL only |
| Viewer `run_creature_review.py check` | 110 / 0 | 110 switches, 0 failed, 0 console errors (revision cf9-20261102) |

Sheets (read at full size): `review/sheet_cf_s1_before_after.png` (the user's two angles, front, 3/4, below; before and
after), `review/sheet_cf_sirens.png` (s1-s4: front, both 3/4, low side, below), `review/sheet_cf_hair_sides.png` (both sides,
back, low front, low side; s1 before/after, Ebora after), `review/sheet_cf_ebora_face.png` (Ebora before/after with a pixel
diff: only hair pixels change, 0 face-skin pixels in five views and 854 in the front view, a sliver at the temple hair edge
where the hair back now covers what was a hole), `review/sheet_cf_neck.png`.

Left: from below the chin underside still reads as a shaded wedge (the mesh's V-shaped jaw lit only by ambient; the dark
brown "goatee" paint is gone). A faint thin zigzag line pattern remains at the neck seam on s1 (and as a tone step on Ebora):
not the colour, AO, padding or normal-map texels (all repaired or checked: no visible change), not z-fighting (no coplanar
overlap); cause not found. s2's skin ramp turns the jaw shading olive (older, tier ramp). The new paint's nose keeps a soft
bridge highlight, and the face reads paler than MM9's SIREN1 (Codex's skin, 226,164,123 at the neck vs the torso 219,159,111).

Chain for the siren head now: `scripts/project_head.py s sr` -> `scripts/tone_sr.sh` -> `scripts/seam_rim.py sr` (once: `seam_rim.py orm`) ->
`scripts/tiers_eb.py` -> `scripts/rebuild.sh`. Ebora's textures were not regenerated (`eb_*` files untouched); re-running
`project_head.py a eb` reproduces them byte for byte (the new blocks are siren-only and the old landmark pairing is kept
for her). `tiers_eb.py` changed only the s2-s4 head ramps and 2,205 head-mask texels (lips/eyes from the new paint).

## Throat check (ear sweep, 2026-11-02; 0 credits)

Sweep notes (`claude_shared/mm9_overview/ear_sweep_20261102.png`): (a) s2 a pale olive tint on the throat; (b) in the views
from below the jaw (rneck/lneck) of every tier a heart-shaped patch in the tier's wing colour between chin and chest.
- **(b) is not a hole: harmless.** `review/throat_wings_check.png`: the same cameras with every wing face deleted and a magenta
  background show the patch turning magenta, i.e. it is the wings (seen past the neck's silhouette, behind the head) and the
  background, not geometry seen through the throat; with the wings deleted the chin, neck and chest are closed skin. The
  boundary loops of the LOD0 mesh near the neck and chest (`holes.py`-style scan) are the known wing roots and suit edges at
  the back (z < -0.04), none on the throat. Nothing changed for it.
- **(a) Cause**: the s2 head skin ramp. `tiers_eb.py`'s target is MM9 siren2's skin colour times our relative luminance; the
  brightest head-skin texels (the chin underside that `project_head.py` lightens for the siren, up to 2.9 x the median) passed
  1 in red, and per-channel clipping turned the ramp's top stops yellow (1, 0.69-0.75, 0.34-0.38): olive under a low light.
  **Fix** (`tiers_eb.py`, `target_image(..., shoulder=True)` for the head skin of s2 only): an over-range target colour is
  scaled back to max 1 (hue and saturation kept), so the top stops stay peach (1, 0.43, 0.22). Tried: lifting it toward
  white to its own luminance (a pale grey-white patch). Only the s2 head skin ramp changed (`textures/eb_tiers.json`; every
  mask and every other ramp byte-identical, previous files in `work/preear_tiers/`); s3/s4 kept (their skin goes to white,
  as MM9's pale sirens). Rebuilt (`rebuild.sh`, then the tail from `tier_glb.py` after the s2-only change): `glb_diff.py` vs the
  previous install: every image the same, 0.000 mm in every clip. Viewer GLBs eb, s1, s3, s4 byte-identical to before (Ebora's
  face pixel-identical); viewer cf10-20261102 check 110 switches, 0 failed. Sheet `review/sheet_ear_before_after.png` (s2
  before/after: ear-side close-ups, profiles, 3/4 backs, under-jaw, party view from 22 deg); the s3/s4 try with the white lift
  is superseded. Winding 0.
Regression after the last ear-sweep install (2026-11-02, `review/regression_actors_earsweep.log`): `--world mm9 actors` passed 192,
failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data");
`mm9_actor_models_build_every_binding` **PASS**.

## Map events for later (engine and script work, `devdocs/mm9_rework/overnight/dungeons_ledger.md`, bathhouse)

- `EboraBath.scr`: when three concubines die, `EscapeTheTub`: camera cut (`EboraCam1.scr` faces the camera to Ebora) and
  letterbox, rollover text 11, `PlayAnim launch` (script clip `launch`, events Launch 0.495 / launch 0.517 s), then `RunTo
  FlyToBlatt` in flight (`fly` / `flap` loops) and `PlayAnim land` (`land`). `Fatc MoveIt/EboraArrive` unmatched.
- `EboraConcubine.scr`: on finding the player each concubine plays `launch` then goes aggressive; on death it triggers
  `DeadConcubine` on Ebora; at init it picks SIREN1-4 at random (variants `s1`-`s4`).
- `EboraMines.scr` (Thjorad mine): `fidget2`, `Taunt`, `Rattack1` (not in EBORA.abc), column of fire, vanish.
- Air reactions `WinceAir1`, `DieAir1`, `fall1`, `FallDown1` are carried for a flying state the engine does not drive yet.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_ebora_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_ebora_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_ebora_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_ebora_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_ebora_reduce_claude/before/`.
