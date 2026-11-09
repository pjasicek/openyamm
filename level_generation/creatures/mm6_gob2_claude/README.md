# MM6 goblin, second attempt (gob2), 2026-10-10

A rebuild of BGoblin A/B/C (Goblin, Goblin Shaman, Goblin King; New Sorpigal) with the current default humanoid route:
[source-frame rig with gates](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) (barbarian test drive, `../mm6_bar1_claude/`).
**Installed and bound since 2026-10-10**, replacing the first goblin (`../mm6_gob_claude/`; its GLBs stay in that
project's `export/` and were removed from the runtime models folder).

![3D (left) and sprite (right), same camera](review/ingame/tiers_3d_vs_sprite.png)

| Item | Value |
|---|---|
| Runtime GLBs | `assets_dev/worlds/mm6/models/mm6_gob2.glb`, `mm6_gob2_sword.glb` |
| Binding | `actors.yml` BGoblin A/B/C (copy in [actors_gob2_binding.yml](actors_gob2_binding.yml)); regression `mm6_gob_actor_models_bind_sorpigal_goblins` checks gob2 |
| Triangles LOD0/1/2/3 | 11,670 incl. the 642-triangle scimitar and the subdivided sword-hand fingers / 5,832 / 2,061 / 652 |
| Skeleton | 52 `B_*` bones cloned from the humanoid set + forearm/upper-arm twist bones, Sword, Socket_Palm_Left |
| Clips (30 fps keys) | Standing (armed idle, legs straightened 60 %), Walking, Running, Attack (0.4 s ready pause + sword attack R6, a slash), Cast (0.4 s pause + left-hand cast attack 1 with an authored open hand), Hit (get-hit front 1), Death (death 1), Dead, Fidget (authored from native gobfi) |
| Events | `attack_melee` impact 0.683 s (wind-up stretch 1.10x); `cast` impact 0.650 s from `Socket_Palm_Left` |
| Scale / stride | 97.1 (256 px x 0.65 over the upright walk height 1.713 m); walk 1.30 m per 0.8 s cycle = 158 units/s at that scale (goblins move at 160), so the true walk is bound, no foot sliding |
| Textures | body 1K + head 1K (Meshy retextures), one skin region, ramps per tier from palettes 745/746/747 |
| Size | 7.5 MB (3 variants share every image) |
| Meshy credits | **30 of 200**: Smart Topology 5, auto-rig 5 (joint estimate + weights), body retexture 10, head retexture 10 |
| Checks | G4 arm stretch p99 1.2-1.7 (max 2.3); G6 body contacts <= 3 mm; curved-blade contacts 0 in every clip; trace vs source 0 flags; viewer 3 tiers x 9 clips clean; regression suite 28/28 (with gob2 bound only the first goblin's own skin-name case fails, as expected) |

Viewer: `http://127.0.0.1:8901/level_generation/creatures/mm6_gob2_claude/review/viewer/index.html`.

## Route (replay)

`scripts/rebuild.sh` (cleanup -> joints -> rig -> fingers -> retarget -> twist -> weights -> finger weights ->
reduction -> sword-hand subdivision -> fist -> G4/G6), then `clip_timing.py work/rig_v5.blend work/rig_v5t.blend`,
`carry_uv.py work/rig_v5t.blend work/rig_v6_review1.blend work/rig_v6.blend` (carries the Meshy UV layout and the head
split, first made by `export_uploads.py` + `transfer_uv.py`, onto the rebuilt rig; `sync_actions.py` when only clips
changed), `build_runtime.sh --install`, `viewer_tiers.py`, `update_viewer_manifest.py`.

## What the gates caught (goblin-specific; each fixed in the layer where it started)

- **HD masters**: the stage-1 Codex set (`mm6_goblin/stage1_20261006/submission`) was reused, as the playbook allows.
- **Joints (G3)**: the generic ring fit seeds from human proportions and put the left elbow at 22 % of the arm and a
  wrist in a finger. `arm_rings.py` seeds from Meshy's shoulder/hand, cuts the SKIN shell only (bracers/pauldrons are
  separate shells) and stops the wrist search before the fingers separate: wrists within 1-3 cm of Meshy's, elbows 4 cm,
  line-fit gaps 1-12 mm. Ankles: the foot shell is only the back of the lower leg (the greave is the front); the ankle
  strap's centre is used.
- **Hands (G5)**: Smart Topology gave the goblin a human hand (thumb + four fingers, not the native three). The finger
  split needed a split tree (the index separates long before the pinky), the thumb cut first, and skin-only cuts.
  Hand rest frames then came out symmetric (89.6 / 90.2 deg from the inherited forearm swing; first try 79 / 106).
  Finger weights use the measured claw tips (an extrapolated tip left claw tips on the hand bone: shards in the fist).
- **Fist (G5)**: the goblin's fingers are splayed 25-70 deg from the handle's normal plane, so curling about the handle
  swept them past it: each finger's spread is closed at the knuckle first; the thumb's base joint and a wider swing
  range let it close over the handle; one smooth subdivision of the sword-hand fingers removed folded shards.
- **Twist (G4)**: the iron bracer covers the forearm from ~10 % to past the wrist, so the forearm twist cannot ramp
  along it: the bracer rides rigidly on the twist bone, the transition sits in the elbow band (0-12 %), the hand roll is
  split evenly between that band and the wrist.
- **Weights (G4)**: goblin armour stands 1.6-2.5 cm off the skin (the barbarian's 1.5 cm rule kept Meshy's weights);
  straps and greaves sit on the foot shells; skirt strips blend from the pelvis at the belt to the thighs at the hem;
  the pouch is rigid on the pelvis; spikes and studs copy the plate they sit on.
- **Contacts (G6)**: the goblin's arms are 1.35x and its hips 1.26x the source's: the walking hands passed through the
  side skirt strips and the pouch. Fixes: the two side strips removed, the pouch tucked 2.5 cm, 7 deg arm abduction in
  walk/run only. The retarget's abduction had its sign inverted (it adducted; also fixed in `mm6_bar1_claude`).
- **Curved blade**: G6 tests a straight stand-in blade; the scimitar curves up to 23 cm off it and sat 19 cm inside the
  torso at the attack's cross-body coil. `g6_sword_mesh.py` tests the exported blade mesh; a roll sweep chose 225 deg
  (no contact in any clip, cutting edge first at the blow +0.20 and in the walk 0.89).
- **Textures**: `transfer_uv.py` fitted on the non-head faces only (196 mm mismatch when the scalp is in the head set;
  now 4 mm). Skin ramps: rank-matching native pixels copied the sprite's baked near-black shading (black cheeks,
  mottled skin); final ramps keep Meshy's skin colour per luminance (full shift to the native hue/saturation, contrast
  1.4x) for tier A and map it through the 745 -> 746/747 palette fits for B/C.
- **In game**: tier A read dull against the grass (fixed with the grade above); the source idle is a deep crouch
  (1.47 m posed against the 1.71 m walk), so the legs are straightened 60 % with the feet kept down (1.63 m); the
  head-look (`look: [B_Neck, B_Head]`) lifts the source's downward gaze toward the party.

## Review 1 (user, 2026-10-10) and fixes

1. **Fingers stretched/morphed in every clip (both hands).** No gate measured the hands; the new
   `g5_hand_stretch.py` found up to 41x (right) / 11x (left) edge stretch: claw tips and knuckle skin left on the hand
   bone next to finger-weighted vertices, because finger weights went by distance to the nearest chain. Now
   `fit_fingers.py` stores each finger's separated piece, `finger_weights.py` gives every piece vertex to its own
   finger, grows the pieces through mesh edges to connected vertices beyond the knuckle (claw tips) and smooths the
   knuckle/web band (3 passes). Max stretch 4.5x (sword-hand webs in the fist) / 3.3x, from 41x / 11x; close-ups
   `review/hc_R_sheet.png`, `review/hc_L_sheet.png`.
2. **Attack read as a thrust.** R4 is a lunging stab; replaced by R6 (raise over the right shoulder, wide diagonal
   slash, arm sweeping out like the native follow-through). Blow at 0.683 s after a 0.4 s ready pause; blade roll
   re-swept to 45 deg (no contact in any clip, cutting edge first at the blow +0.56, walk 0.91).
3. **Cast wrist and fingers.** Measured: the source itself bends the wrist 55 deg and keeps the fingers curled ~99 deg
   (a fist) through the thrust; on the goblin that read as a limp claw. The cast now eases the left wrist straight and
   opens the fingers to the goblin's open rest pose during the thrust (85 %), back to the source afterwards.
4. **Skirt stretch (cast frame 32).** The middle strips copied skin weights that split across their width (left half on
   the left thigh, right half on the right): 8.9x between the legs in the wide stance. Each strip now has one uniform
   left/right thigh mixture (by its centre x), pelvis at the belt to the thighs at the hem: max 1.4-2.0x in every
   clip (`g4_skirt.py`); thigh poke-through stays at the original level (`g6_skirt_poke.py`, 3-5 cm by its metric,
   not visible in the walk/run renders).
- Rebuild without a new retexture: `carry_uv.py` maps the textured master's UVs onto the rebuilt topology (one old
  triangle per new face at its centroid; corners mapped independently crossed UV seams and made giant UV triangles).

## Review 2 (user, 2026-10-10): right shoulder into the head in the attack (viewer frames 34-49)

- Measured with `g6_head_clearance.py` (head skin above the jaw line vs the pauldrons, the gorget's shoulder parts and
  shoulder skin, by REST position so weight changes do not move the sets): attack 5 cm (0.70-1.0 s, after the blow),
  cast 1.5 cm (raised casting arm), death on the ground.
- Two causes. Weights: Meshy gave the jaw underside 21-37 % clavicle/upper-arm weight, so a shrug dragged the jaw onto
  the shoulder - `weights_fix.py` rule 5 cleans skin above the jaw line (the side of the neck below still lifts with a
  shrug; cleaning the whole neck made the shoulder meet a static jaw 5 cm deep). Motion: R6's follow-through twists the
  chest and swings the raised arm under the chin while the head pitches down onto it (the head hits the deltoid more
  than the plate) - the goblin's big head and short neck. `clip_timing.py head_fix` adds per frame the cheapest of chin
  up (neck + head), clavicle down and head away until the jaw clears, held +-2 frames and smoothed. Lowering the upper
  arm was tried and dropped: it drove the forearm 5 cm and the blade 18 cm (then 2.8 cm at 15 deg) into the body.
- Result: attack <= 1.4 cm (5 frames, a touch), cast 1.0, death 0.7; max correction chin up 25, clavicle down 25, head
  away 10 deg. No body or blade contacts, blow still edge-first (+0.53), trace 0 flags, viewer clean.

## Review 3 (user, 2026-10-10): lines on the skin of the blue and red tiers

- The region mask stopped at the UV island edges, while the colour was padded into the gutters (and the cracks between
  carried UV faces): filtering at every seam mixed in unrecoloured tier-A olive, invisible on A, thin olive lines on
  B/C. `compose_gob2.py` now pads the mask from the nearest island texel (body and head) before the 0.7 px blur, and
  zeroes it on the sword swatches (the padding first gave the blade the ramp).
- The belly skin behind the belt buckle carried a sliver of the buckle's yellow (600 texels): kept out of the mask, so
  it no longer shows as a bright red/blue rim on B/C.
- Checked in the viewer (all tiers, head, arms, back, sword) and regression 28/28; GLBs reinstalled.

## Known faults (placeholder quality)

- Four fingers instead of the native three (Smart Topology); claw tips show outside the fist close up; the webs between
  the sword-hand knuckles stretch up to 4.5x in the fist.
- Idle and attack stances are the source's wide guard, not the native's upright, narrow stand (legs only partly
  straightened); feet drift ~7 cm per 2 s idle cycle after the straightening.
- A pale smear on the head texture's temple (side view), from the head retexture projection.
- Head/neck seam follows a jagged line under the gorget.
- Cast keeps the source's raised sword arm while the left hand casts.
- Centre front skirt strip can touch the forward thigh in the walk (3-5 cm by the poke metric).
