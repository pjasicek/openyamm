# Test drive: rig-first gates on the MM6 Barbarian (started 2026-10-10)

Purpose (user, 2026-10-10): with professional source clips (the RPG humanoid set in `anim_library/rpg_humanoid/`,
`B_*` rig), arm, shoulder, wrist and finger faults come from our model, joints, bone frames or weights, not from the
animation. Test whether catching them layer by layer, early and on numbers, avoids the usual 10–20 stacked fix-ups.
This file is the running log. When the barbarian is accepted, review it and move what proved itself into the
humanoid playbook. Hypotheses are untested until the evidence column says otherwise.

## Hypotheses

| # | Hypothesis | Gate | Status | Evidence |
|---|---|---|---|---|
| H1 | Choosing the clips before modelling and extracting each joint's range of motion (ROM) from them gives the right stress poses for later gates | G1 | **supported** | predicted the wrist/upper-arm roll problem before any modelling; ROM frames were the G4 poses |
| H2 | Comparing segment proportions (shoulder width, arm segments, chest depth, hip height) with the source skeleton predicts hand/body collisions before any clip plays | G2 | **not confirmed** | predicted contacts did not occur; keep as a cheap warning, G6 decides |
| H3 | Joints placed at cross-section ring centroids, hinge axes from the mesh's own crease, fix elbow/wrist/shoulder faults at the source | G3 | **partly** | rings right for wrists/ankles only; shoulders/knees/hips/spine from Meshy's auto-rig; elbow from two line fits; judged in the X-ray |
| H4 | Cloning the source armature's bone frames (local axes/rolls) and fitting only joint positions makes the retarget a plain local-rotation copy, removing per-bone twist offsets (the bicep "wringing" and hand flips) | G3/G6 | **supported (corrected)** | the exact rule is a WORLD-rotation copy (local copy wrong by up to 68 deg); hand rest frames must be measured from the mesh |
| H5 | Weight faults (shoulder collapse, elbow volume loss, candy-wrapper forearm, arm bleed into the chest) are measurable on the clip ROM extremes posed one joint at a time, before animation | G4 | **supported** | all old faults found as located numbers; fixes verified on all gate poses in seconds |
| H6 | Fingers are robust when driven by a few verified poses (relaxed, grip, open) instead of the raw source finger channels; the grip axis can be derived from the source's curled fingers | G5 | **supported (direction only)** | source grip axis sets the blade direction; the fist itself must be solved for our finger thickness; blade roll needs its own gate |
| H7 | Per-frame comparison with the source (bone directions, palm normals, elbow off-hinge, twist, contacts) catches what remains, so viewer review becomes confirmation rather than discovery | G6 | **supported** | trace vs source + contacts caught timing and blade faults; the user found one fault (blade roll) no gate covered |
| H8 | One replay script that re-runs every later gate after any change prevents fixes from breaking earlier work | all | **supported** | caught the leggings, armlet and decimation regressions at once; must abort on the first failing step |

## Outcome (2026-10-10)

User verdict: "it DID produce very good results". Distilled into the humanoid playbook section "Default route:
source-frame rig with gates". 30 Meshy credits; one user review round (blade roll).

## Gates (planned)

- G1 clips + ROM: pick the clips, preview them on a stick mannequin, extract per-joint extremes.
- G2 proportions: after Smart Topology, segment lengths versus the source skeleton.
- G3 joints and frames: ring-centroid joints, crease hinge axes, source bone frames; X-ray sheet.
- G4 weights at ROM extremes: stretch, elbow area, forearm twist progression, deltoid drop, arm-torso penetration.
- G5 fingers: chains in real fingers, curl direction, fist around the derived grip, no phalanx overlap.
- G6 source match per frame on the exported GLB at 48 fps: direction, palm, hinge, twist, contacts.
- G7 look: viewer + in-game, only after the numbers pass.

## Log

(newest last; each entry: what was tried, numbers, what it means for the hypotheses)

### 2026-10-10 setup
- Project `mm6_bar1_claude/`, workspace claimed (60 credits). Native: `mm6_bar1/native` (sta/wa/at/wi/fi/de),
  palettes 663 (A gold/bronze armour), 664 (B blue steel), 665 (C copper with green bracers/boots).
- Source set: Armed (one-handed weapon right hand: idle, walk, run, get-hit, death) and 1Hand (sword attacks).
  The source rig has 53 `B_*` bones, three-joint finger chains, no twist bones and no weapon/prop bone.

### G1 clips and range of motion (2026-10-10)
- Previewing clips needs the set's own character mesh (each set GLB carries a skinned blocky mannequin, ~2.58 m
  including the box head); a self-built stick mannequin was unreadable.
- Traps found on the way (each would have cost a debugging round later):
  - the imported armature uses QUATERNION rotation, so an Euler 180° turn is silently ignored; the first preview
    showed the character from behind with the sword "in the left hand";
  - imported `B_*` bones have meaningless tails (tens of metres); every axis must come from joint HEADS;
  - the library folder was renamed twice during the session; scripts find it by content (`scripts/libpath.sh`).
- H6 (grip from the source fingers): a circle through each finger's three joint heads (index..pinky) gives four
  centres that are collinear within 0.3–0.5 cm, curl radius ~3.6 cm, handle axis almost the hand bone's local X.
  The finger pose is IDENTICAL in idle, walk, run, hit, death and attack R4 (only attack R1 tightens slightly):
  the source holds one fixed grip. A stand-in sword on that axis reads correctly in every previewed clip.
  → H6 grip derivation supported; "fixed finger poses" matches how the source itself animates fingers.
- Clips chosen (front + side + three-quarter previews with the derived sword): Standing = armed idle, Walking =
  armed walk, Running = armed run forward, Attack = one-handed sword attack R1 (raise behind the right shoulder,
  overhead pass, diagonal cut to the low left, recovery: closest to the native bar1at), Hit = front get-hit 1,
  Death = armed death 1 (falls forward like native bar1de), Fidget = armed boost 1.
- ROM (`scripts/rom_extract.py`, `work/rom.json`, swing/twist of rest-relative local rotations about the
  joint-head segment axis):
  - the source FOREARM IS A PURE HINGE: twist 0.0 in every clip. All forearm roll is carried by the HAND bone:
    right hand twist up to 107.7° (attack), 72.8° (fidget), 53.9° (death); left hand up to 58°.
  - upper arm twist (humeral rotation) up to 107° right (attack), -99° left (fidget).
  - elbow flexion up to 121° (fidget), wrist bend up to 101° (death, hand on the floor), 61° (attack).
  - clavicle swing up to 42° (attack), 39° (death); clavicle twist ~0.
  → Predicted before any modelling: with a rigid hand and no twist distribution, the attack's 108° hand roll
    twists the wrist skin (the old "wrist rotating unnaturally" fault) and the 107° humeral roll wrings the upper
    arm. Plan: forearm twist bones sharing the hand's roll, an upper-arm counter-twist near the shoulder. H1 gives
    concrete, quantified requirements: supported so far (to be confirmed at G4).
- Source proportions (`scripts/proportions.py`, normalised by height): shoulder width 0.252, clavicle 0.106, upper
  arm 0.138, forearm 0.138, hand 0.068, hip width 0.090, thigh 0.230, shin 0.231, shoulder height 0.767, hip height
  0.518. Broad-shouldered, narrow-hipped mannequin; compare at G2.

### G3 tooling dry run on the male peasant mesh (2026-10-10, before the barbarian mesh existed)
- `scripts/fit_joints.py` (ring centres from perpendicular slices) + `scripts/joint_xray.py` (ghost mesh, joint
  spheres, segment rods; front/left). The X-ray was decisive: every mistake was obvious at a glance, numbers alone
  would not have shown which joint was wrong.
- Arm tip seed: "lowest vertex beyond the shoulder line" hit the thigh on close-hanging arms; "most lateral vertex
  at hand height, then the lowest point of that hand" works.
- WRIST = narrowest ring in the distal third: correct. ELBOW = the A-pose bend's largest deviation from the
  shoulder-wrist line (bend 22–37 mm on pman): plausible; gives the mesh's own hinge axis.
- SHOULDER (glenohumeral centre): three geometric rules failed in the X-ray - a ray up the upper-arm axis stops at
  the skin under the separate sleeve shell (joint too low/outside); torso half-width from a slice picked an inner
  shell, then the outer shell still measured narrow (joint too far in, at the collar); scaling by the source's
  joint/torso ratio is meaningless because the blocky source mannequin's shoulder joints sit 2.1x its torso
  half-width out. → H3 holds for wrist/elbow/ankle, NOT for the shoulder on garment-shelled Meshy meshes. Plan:
  shoulder, clavicle, spine and hips from Meshy's auto-rig (independent estimate, 5 credits), refined and gated in
  the X-ray; rings for wrist/elbow/knee/ankle; compare Meshy's wrist with the ring wrist (thief: Meshy 5 cm off).

### HD masters, Smart Topology, cleanup (2026-10-10)
- Codex image generation refused the front view once and the BACK view twice ("sexual" safety classification of the
  bikini-armour design), even with neutral armour wording and an added leather underlayer. Retexture will use front,
  left and right (01/03/04). Front/right carry a thin leather underlayer (the brief's allowed fallback).
- Smart Topology (5 cr): 15.2k tris, 50 loose parts; one closed skin body, separate armour/hair/boots/belt shells.
  Faults: a thin strand from the left hand down to the boot (fused into the boot shell), an eye blob over one eye
  only. `scripts/step1_clean.py` removes both (strand = boot vertices outside the mirrored boot extent).

### G3 joints (2026-10-10)
- Meshy auto-rig (5 cr) as the independent estimate; ring centres (`fit_joints.py`) as the other; overlaid in the
  X-ray (`joint_xray.py ... <second set>`).
- Ring geometry is fooled by garment bulges: knee at the boot top (12-15 cm too low), elbow at the gold armlet,
  shoulder at the collar. Meshy's auto-rig was right for shoulders, knees, hips, spine; its wrists sit 2-3 cm up the
  forearm, so wrists and ankles come from rings. ELBOW: intersect two line fits (upper-arm ring centres, forearm ring
  centres) - symmetric (t 0.556 / 0.575 of shoulder->wrist, line gap 2-5 mm, bends 12.5 / 9.6 deg), where a single
  max-deviation point gave 0.58 / 0.33. → H3 refined: "combine two independent estimates, judge in the X-ray, use
  line fits not single extremes on garmented limbs".
- G2 proportions vs the source (height-normalised): shoulders 0.81, clavicle 0.80, upper arm 1.12, forearm 0.90,
  hip width 1.40, legs ~1. Prediction: hands pass 3-4 cm closer to the hips than in the source (walk/idle) → check
  contacts at G6.

### G3 bone frames and the retarget rule (H4) - two wrong turns, both caught on the first comparison render
- Bone frames cloned from the source (`build_rig.py`): our rest frame = minimal swing q (source T-pose segment ->
  our segment) @ source frame. Exact (frame error 0.0 deg).
- WRONG 1: hands inherited the forearm's swing. Our mesh's rest hand is bent ~36 deg and rolled ~26 deg relative to
  the forearm (the source T-pose hand is straight), so idle hands came out palm-up. Fix: the hand's rest swing is
  measured from the MESH hand (PCA finger direction + thumb side vs the source hand's index->pinky axis): 46-47 deg
  away from the inherited swing, symmetric. Self-check that proved it: the source finger joints, carried by that
  swing and scaled by the measured hand length (14-15 cm; the forearm ratio overestimated it), land inside our mesh
  fingers, thumb forward and on the palm side (`hand_xray.py`).
- WRONG 2: the retarget used R = S R_src^-1 q R_src (the old Mixamo-retarget form), which applies the T-pose -> pose
  rotation to an A-pose mesh. With cloned frames the exact rule is simply R_ours(t) = S(t): copy WORLD rotations.
  A LOCAL rotation copy is still wrong (differs up to 68 deg on the upper arms) because parent and child rest swings
  differ. → H4 holds in this form: cloned frames make the retarget a plain world-rotation copy with no per-bone
  offsets; the remaining degree of freedom is each bone's rest swing, which must be measured from the mesh.
- `compare_source.py` (source mannequin and our mesh side by side at the same clip time, both with the derived
  stand-in sword) is the tool that exposed both errors in one render each. After the fixes the idle pose and sword
  direction match the source.

### G4 weights at the clip extremes (2026-10-10) - H5 supported
- `g4_weights.py` (per side: arm edge stretch p99/max with the dominant bone, forearm twist profile from 6 vertex
  rings, elbow area, upper-arm ring twist) at the ROM frames from `rom.json`, mapped to our 24 fps frames.
  `stretch_heatmap.py` locates hotspots (threshold the colour at 1.6x: plain edge ratios light up shear everywhere).
- Meshy auto-rig weights, measured BEFORE looking at any clip: armlets 9x, chest armour 6.6x, shoulder skin 5x in the
  attack; forearm rings all rotate as one block and the whole hand roll jumps at the wrist (+20..35 deg in the last
  15 % of the forearm; the hand rolls 52 deg relative to the forearm already in idle, 108 in the attack). Exactly the
  old "wrist rotating unnaturally" and "chest/shoulder" faults, found as numbers.
- Rules (`weights_fix.py`): armour copies the weights of the skin directly under it; torso armour drops arm weight;
  small limb rings rigid on their dominant bone; upper-arm weight fades out medially over 7 cm past the shoulder.
  First version made walk/idle WORSE (edges > 2x: 10 -> 117): the leggings shell IS the legs' surface (no skin under
  it, median gap 26 cm) and the copy pulled hip/opposite-thigh weights across the crotch. The full gate re-run caught
  it immediately; rule refined (copy only when the skin gap < 1.5 cm). Result: armlets 1.0x, top 5.8 -> 2.2x,
  walk back to its baseline.
- Twist (`twist_bones.py`): forearm twist bone at 60 % taking 0.6 x the hand's roll (ramp 15-85 %), upper-arm twist
  bone at 25 % taking -0.5 x the humeral roll (ramp 0-60 %), baked per frame. Forearm rings now ramp smoothly
  (idle 19 -> 21 -> 30 -> 50 -> 65 deg instead of a jump at the wrist); attack arm-edge p99 1.46-1.52 (Meshy weights
  2.4-3.0). Remaining: a narrow 3.5x band at mid upper arm where the rigid armlet meets the counter-twisting skin.
- Third round, from the numbers: copying skin weights onto the armlet (to follow the twist) made the metal ring
  itself shear 2.5-2.9x. The real constraint: a twist transition must not pass under a rigid accessory. The upper-arm
  twist ramp now ends at 30 % (the armlet spans 32-51 %, measured), the skin under the armlet is pure upper arm, and
  small rings go rigid when one bone holds >= 80 % of the skin under them. Result (attack extremes): armlets 1.0x,
  arm-edge p99 1.55-1.93, walk/idle unchanged. Heatmap: only small spots left (armpit of the raised arm, near the
  pauldron, hair) - deferred to the source-match gate.
- Pattern so far: each fix was proposed from a located measurement, tried, and re-measured on ALL gate poses in a
  few seconds; two of three first attempts broke something else and were caught at once, before any viewer or game
  check. This is the "fix it at its inception" loop the test drive was meant to check.

### G5 fingers and grip (2026-10-10) - H6 holds only for the DIRECTION
- Fingers from the mesh: slicing perpendicular to the hand and tracking loops mislabelled fingers (index 3 cm,
  ring 8 cm). What works on this hand: CONNECTIVITY - cut the hand at increasing depth along the finger direction; the
  first depth with >= 5 pieces separates the four fingers, and the first depth with 2 pieces separates the thumb
  (it leaves the palm much earlier). Centrelines from each piece; joints at the source's phalanx proportions.
  Finger lengths now consistent L/R (index 8.0, middle 8.8-8.9, ring 6.6-6.9, pinky 5.4-6.1 cm).
- Finger weights: nearest finger segment within 1.4 cm beyond the knuckle; palm/back stay on the hand. With the
  carried source fingers only ~80 of 550 hand vertices were assigned (index none); with fitted fingers 50-80 per finger.
- Using the source's finger curl directly: no room for a handle (source mannequin fingers are thin; ours are
  1.0-1.5 cm thick). Scaling the source curl: wrong (scales other rotation components too, handle drifts).
  What works: a FIXED handle against the palm and a per-finger grid search (3 angles about one flex axis, tip joint
  <= middle joint) so each phalanx sits at handle radius + its measured half-thickness + 2 mm. All fingers flex about
  the handle axis (per-finger planes from the fitted centrelines were 85 deg off on two fingers).
- The handle DIRECTION must be the source's own grip axis: our hand bone rotates exactly like the source hand, so that
  axis puts the blade where the animator's sword was. An axis from our own fingers was 29 deg off and the blade went
  into the legs in walk/hit/fidget (max clear blade 0.18-0.42 m); with the source axis no clip has any blade contact
  up to 0.85 m.
- The 29 deg came from the hand's REST ROLL: the PCA width axis of the hand was 35-37 deg off (mirrored L/R). Using the
  fitted knuckle line (index -> pinky) for the hand frame: knuckle mismatch 0 deg, a clean fist with the thumb over
  the handle, and the hand's roll relative to the forearm dropped (idle 52 -> 15 deg, attack peak 108 -> 83 deg):
  part of G1's "huge wrist roll" was our own rest-roll error, not the source.
  → Rule: measure the hand frame from fitted finger knuckles, not from a PCA of the hand blob.
- Remaining G6 contact: forearms pass 5 cm into the loincloth's back flap in the walk (the flap hangs 4 cm off the
  body). Mesh-layer fix next.

### G6 contacts (2026-10-10) - H2's prediction NOT confirmed; the metric needed care
- `g6_contacts.py`: per frame, forearm / hand / sword-blade samples against the rest of the posed body (closest
  point + face normal). First version: forearms "5 cm into" piece 6 in the walk, blade into the legs in walk/hit/
  fidget. The blade contacts were real (wrong handle direction, fixed in G5). The forearm "contact" was a false
  positive: the forearm sat 2.7 cm BESIDE the belt, below the plane of the belt's top edge (closest face = the top,
  normal up). A flap-swing mesh edit made for it changed nothing - wasted round; now off by default. Fix in the
  metric: inside only if behind the closest face within a 45 deg cone of its normal. Result: no contact > 2 mm in any
  clip (idle, walk, run, attack, hit, fidget, death).
- H2 (proportions predict hand/body collisions): the prediction (hands 3-4 cm closer to the hips) did not show up as
  contacts; the 19 % narrower shoulders / 40 % wider hips stay within the clips' clearances for this source.
  → Keep G2 as a cheap warning, but only G6 decides; and always LOCATE a reported contact (which piece, which face,
  render it) before fixing anything.

### G6 trace and G7 clay look (2026-10-10)
- Trace on the EXPORTED GLB (`trace_export.py`, played like the viewer at 1/48 s, linear keys) compared per bone
  group with the SOURCE clip sampled the same way. A fixed limit (25 deg per half-frame) flagged 15 groups - but the
  source's own attack turns the hand ~120 deg per half-frame (an authored whip). Gate = "match the source" instead.
- Two timing bugs found by this gate and the viewer, both invisible in still renders:
  - resampling 30 -> 24 fps keys put ~185 deg between two keys at the whip (interpolates the wrong way): keys are now
    at the source's own frames;
  - Blender's glTF import maps the source's seconds to frames at the SCENE rate (24), not 30: every clip played 25 %
    fast (attack 0.63 s instead of 0.80 s); the viewer manifest's clip durations exposed it. Retarget reads the scene
    rate after import. Durations now equal the source's (idle 2.0, walk/run/attack 0.8, hit 0.5, death 1.067, fidget
    1.0 s) and the trace equals the source per group (world copy is exact): 0 flags.
- G7 clay viewer (`export_review.py`, `update_viewer_manifest.py`, check_viewer: 8 clips, no errors) and full clip
  sheets (front / side / three-quarter, 8 frames per clip, sword on the solved handle): motion reads as the source,
  sword stays in the fist through the attack, fidget (sword raised overhead) and death. No visible arm, wrist or
  finger fault in the sheets.
- Process so far: every arm/hand fault (palm-up hands, hand roll, candy-wrapper wrist, armlet/chest tearing, finger
  placement, fist, blade direction, timing) was found by a gate number or a gate render BEFORE a viewer or game check.
  Wrong turns: 9 (each caught within one gate run); none required the user.

### Triangle budget (2026-10-10) - H8 tested for real
- Reducing 15.0k -> 10.0k in the mesh cleanup (before the rig) and replaying the chain: G4 caught a regression at
  once (attack arm stretch p99 1.9 -> 2.6, max 4.3 -> 9.7). Cause: Meshy's weights are transferred by nearest vertex
  and the decimated vertices sat up to 23 mm from the originals. Fix: reduce AFTER the weights (`reduce_rigged.py`,
  collapse interpolates the vertex groups; head and hands protected by their weights). Result 10,117 tris, attack
  p99 1.17-1.44, max ~1.9 (the decimation also removed sliver edges that inflated the ratio), G6 clean.
  → Rule: topology reduction belongs after weighting when weights come from a transfer.
- H8 failure mode found: a crashing step left a stale file and every later gate ran on it, printing plausible but
  meaningless numbers. The replay runner now aborts on the first Python error.

### Textures and tiers (2026-10-10)
- Body retexture (10 cr) with `enable_original_uv: false` and Meshy's own layout copied back face by face
  (`transfer_uv.py`: 10,117 faces matched, worst centroid 1.7 mm); views front, left, right, three-quarter (no back).
- Classes per texel from the UV raster (`uv_raster.py`: piece id + rest position) plus colour; graded per class to
  the native tier-A medians. The gold rim of the cups is not separable by colour from the pale metal (known fault).
- Tier ramps: first build (16 linear quantiles of the native pixels) left the leather BLACK in every tier and tier-A
  armour too dark: most leather texels sit at the dark end of the luminance range, and the native set included many
  pure-black outline pixels. Fix: drop near-black native pixels and RANK-MATCH (each stop takes the native colour at
  the quantile its luminance has among the region's texels), gain 1.3. Tiers now read like the sprites (A bronze /
  brown, B blue / burgundy, C copper / green).
  → Rule for ramps: quantile-match the region's texel luminance distribution, never map t linearly to native rank.

### Runtime, install, in-game (2026-10-10)
- Head retexture (10 cr). Our head render looked scrambled; a UV transfer from Meshy's return showed 0.0 mm mismatch,
  so the UVs were right: Blender Workbench samples every material through the ACTIVE UV layer (the UV Map node is
  ignored). Preview tools now merge the head UVs into one layer as the runtime export does. Then my head grade turned
  the skin grey-green: Meshy painted hair onto the scalp under the hair shell and the "skin" class included it;
  restricting the class to skin tones fixed it. (Two false alarms of my own tooling, neither in the asset.)
- Sword export: every sword face had zero area - its cross-section vector came from the hand bone axis that runs
  along the handle. Picked the least-parallel axis and assert non-degenerate faces.
- Scale from the upright walk height (the source idle is a crouched guard; werewolf lesson): 98.9.
- Installed (`build_runtime.sh --install`): LODs 10,465 / 5,228 / 1,860 / 601, 8.6 MB, tiers A/B/C, sword attachment,
  head merged into one material. In game (New Sorpigal, hostile, immortal party): all three tiers attack with the
  sword in hand; tier colours match the sprites. Regression `mm6_barbarian_actor_model_tiers_share_one_size` added;
  suite 23/23. Viewer: 3 tiers x 8 clips, no errors. Meshy credits: 30 of 60 (Smart Topology 5, rig 5, body 10, head 10).
- Known faults (placeholder): gold reads lemon-yellow next to the sprite's bronze-gold; the cups' thin gold rim follows
  the armour tier colour; her idle is the source's low guard (the native stand is upright); slight neck seam in
  brightness; no back reference (image tool refusal).

### User review: blade roll (2026-10-10)
- User: the sword shows its flat to the front while walking; the edge should point at the ground.
- Not covered by any gate: G6 checked the blade's DIRECTION (grip axis from the source) but not its ROLL about that
  axis. The roll came from an arbitrary hand-bone axis. New gate `blade_edge_gate.py`: over the fastest 20 % of tip
  motion per clip, the share of tip velocity along the edge vs the flat (1 = edge leads). A roll sweep found the
  optimum at 45 deg from the knuckle line (attack 0.78, walk 0.99, fidget 0.83, death 0.89, hit 0.83, idle 0.92); the
  first export sat near 135 deg (walk 0.15). Remaining: the run's fastest frames are flat-leading (0.24) - a
  compromise in favour of walk and attack.
  → Rule: a held blade has two degrees of freedom to gate - direction (source grip axis) AND roll (edge leads the
  motion in the clips).

### Clip timing for the engine's action events (2026-10-10)
- The engine now plays a marked attack's wind-up [0, impact] over the native action and the rest as follow-through;
  fidget and hit are still cut at the native length. `clip_timing.py` (rig_v6 -> rig_v6t, run by `build_runtime.sh`):
  - Attack: 0.4 s ready pause (ease Standing -> attack's first pose, chest coiled 6 deg) + the source attack at its
    own speed. Blow = peak sword-tip speed at 0.683 s, so the 0.75 s native wind-up plays it at 1.10x. actors.yml
    `events: attack_melee: {impact: 0.683}` on all three tiers. A first try without the pause had the blow at 0.617 s
    (1.22x); the pause brings the stretch inside the agreed +-20 %.
  - Fidget: the 1.0 s sword raise was cut mid-move at the native 0.625 s. New 0.6 s fidget = Standing with the set's
    RelaxNo head shake layered on the neck/head (40 % on the upper chest).
- Checks: trace gate 0 flags, blade-edge gate attack 0.72, viewer 3 tiers x 8 clips clean, regression suite 25/25.
- Follow-up (same day): the engine now plays a fidget longer than the native one to its end while the actor stands
  (presentation only), so `clip_timing.py` no longer replaces Fidget: the set's Armed boost 1 (1.0 s, sword raised)
  is back at source speed. The interim head shake is gone.

### User review: attack follow-through too flexible; head look (2026-10-10)
- User: the end phase of the attack looks far too flexible, with a huge range of motion. Measured on the built clip:
  the source slash (SwordAttackR1) turns B_Spine..B_Spine2 by 89 deg about the spine against the pelvis (shoulder line
  110 deg against the hip line with the clavicles; pelvis another 39 deg over the feet), while the neck turns back
  -52 deg to keep the head forward. A real trunk rotates ~40-45 deg. No gate measured trunk axial rotation.
- `clip_timing.py` now limits the summed spine twist per frame (unchanged to 25 deg, soft limit 45 deg, each bone
  keeps its share and its swing) and gives the removed turn to the neck, so the head keeps its world direction.
  Peak 89 -> 45 deg; the arm keeps its pose relative to the chest, and the cut ends low across her front instead of
  swinging out behind her left side. Blow time unchanged (0.683 s); g6_contacts clean; blade-edge share 0.72 -> 0.86;
  trace gate no Attack flag.
- actors.yml: `look` on B_Neck/B_Head (60 deg yaw, 35 deg pitch; head height from the rest pose) for all three
  tiers. In game the faces stay on the party through the attacks.
  → Rule: measure the trunk's axial twist (spine bones about their segment axes) on every imported attack; soft-limit
  it to ~45 deg and hand the excess to the neck.

### User review: clay skin (2026-10-10)
- User: the skin looks like clay. Measured: the graded skin albedo is nearly uniform (texel luminance quartiles
  169-189 vs the sprite's 103-170, which includes its baked lighting), and the material had specular off
  (`openyamm_specular=0`), so skin was pure Lambert with no sheen and no crease darkening.
- Changes (`compose_bar1.py`, `build_runtime.sh`, new `bake_ao.py`): rest-pose AO (3 cm reach, UVMap) multiplied into
  the body base colour (strength 0.5, floor 0.3); ORM red = per-class specular mask with `openyamm_specular_mask`
  (skin 0.45, hair 0.3, leather 0.35, armour 0.8, gold 1.0, fur 0.1), green = per-class roughness around Meshy's detail
  (skin 0.5, armour 0.35, gold 0.3, fur 0.9); metallic stays 0. The head set gets the same skin/gold values. The sword
  swatches keep their own surface values.
- Not yet seen in game (another session had the game running); pending the user's look.

### User review: upright clips (2026-10-11)
- User: the crouched animations look bad, the attack and above all the run. Measured (posture of the source clips,
  pelvis height over leg length / knee bend / trunk lean): every one-handed clip of the humanoid set is a low guard -
  Armed idle 0.65 / 76 deg / 16 deg, Armed run lean 40 deg, all 1Hand sword attacks 0.66-0.79 with 60-90 deg knees.
  Upright options: the set's Relax run (lean 6 deg) and Mixamo (library index `anim_library/index.json`).
- Mixamo files in the library are retargeted to Warrok (the user's preview character): hunched rest, knees bent ~40
  deg, neck tilted. `retarget_mixamo.py` copies each bone's WORLD rotation change from Warrok's rest pose,
  D(t) = M(t) M_rest^-1, onto the set's rest frame (S = D R_src), so retarget.py's world rule and the mesh-measured hands
  stay valid; absolute directions would copy Warrok's build. Pelvis height from foot contact (lowest ankle/toe lift
  matches the source's, scaled by the leg ratio).
- G4 caught at once: Mixamo rolls the forearm bone itself (90-125 deg in the attack and battle cry); the set's forearm is
  a pure hinge and twist_bones.py expects the hand to carry the roll - the whole forearm turned as one block. The
  retarget now keeps only the forearm's hinge swing (the hand, set in world space next, takes the roll): forearm rings
  ramp to the wrist again (attack 3 -> 87 deg with the hand at 108).
- Candidates rendered on our rig (side and three-quarter sheets): runs - set Armed/Relax/Unarmed, Mixamo axe-pack,
  Running 2/5, Run Forward 2, Slow Jog, Unarmed Run Forward, Medium Run; attacks - 1Hand R1/R5/R7, Mixamo axe downward/
  horizontal, sword-and-shield attack 2 / slash 3; idles - set Armed/Relax/Unarmed/2H axe, Mixamo axe idle, sword-and-
  shield idle, Ready Idle, Standard Idle. The Mixamo axe pack (Pro Melee Axe) is no better: wide sideways stance,
  short-stride combat jog.
- Chosen: Standing = Mixamo Standard Idle; Walking = Armed walk (unchanged, already upright); Running = Relax run;
  Attack = Mixamo Sword And Shield Attack (2) (raise over the right shoulder, chop down - the native bar1at); Hit =
  Unarmed get-hit F1; Death = Armed death 1 (unchanged); Fidget = Mixamo Standing Taunt Battlecry. GripRef (Armed idle)
  is retargeted only so grip_solve keeps the source's sword grip; the export drops it.
- The sword-and-shield attack and the battle cry step into a lunge (pelvis 23-27 cm lower in the side view, upright
  only from the front): stance plant on Standing (`:plant`, druidess rule) - pelvis and legs hold Standing, the upper
  body keeps its world motion with a yaw correction. Native attack stands in place, as now.
- `clip_timing.py` stance blends: Hit eases in/out over 0.2 s, Death in over 0.25 s (the engine does not crossfade into
  the death), Fidget 0.3 s both ends, Attack out over 0.25 s (its ready pause is the ease-in). Blow still at 0.683 s.
- `sync_actions.py` copies the gated clips from rig_v5 into the textured master rig_v6 (rebuild.sh last step), so clip
  changes no longer need the texture chain. Previous masters: `work/pre_upright_20261011/`.
- Checks: G4 p99 <= 1.44 (max 1.99, as accepted before); G6 contacts <= 0.9 cm except the battle cry's left forearm
  2.0 cm for one frame; blade edge attack 0.74, run 0.94, hit 0.95; trace: the battle cry's arm fling and fist clench
  are fast (<= 53 deg per half-frame) but continuous; viewer 3 tiers x 8 clips clean; regression pass; in game
  (`review/ingame/upright_sheet.png`, `upright_crops.png`): upright run, stand and attack in all tiers.
  Sheets: `review/upright_clips_three_quarter.png`, `upright_clips_side.png`, `upright_attack_fidget.png`.
- Follow-up (user, same day): at the blow the attack looked like a pommel strike - blade up, fist coming down. Our grip
  was not the cause (the Mixamo handle axis from Warrok's curled fingers, mapped into our hand frame, is within 12 deg
  of our solved sword axis): "Sword And Shield Attack (2)" never cuts - the sword sweeps forward, goes back over the
  shoulder and stays up while the shield fist punches; it is a shield bash. Replaced by Mixamo "Sword And Shield
  Slash" (planted): raise over the right shoulder, slice across the front to the low left. Twelve planted candidates
  compared (set R1/R4/R5, Mixamo sword-and-shield slashes 0-4, axe downward/horizontal, stable inward/outward slash).
- The old blow rule (peak sword-tip speed) picks the overhead pass, with the blade still pointing backwards, in most
  slashes. `clip_timing.py` now takes the fastest tip motion while the blade points at the target (forward > 0.5): the
  slice at 0.75 s with a 0.15 s ready pause = the native wind-up, no stretch. actors.yml `attack_melee: {impact: 0.75}`.
  Edge-leading share 0.76; G6 attack <= 1.5 cm (recovery); G4 attack p99 <= 1.46 (hand max 2.19 just after the cut);
  viewer clean; regression pass; in game `review/ingame/slash_crops.png`, blow frames `review/slash_blow.png`.
- Follow-up (user): "some leg movement?" - the fully planted slash froze the legs. The chain now also retargets the
  attack and battle cry unplanted but yaw-aligned (`retarget_mixamo.py :turn`, AttackFull/FidgetFull, dropped at
  export); `clip_timing.py` blends LEG_KEEP = 0.2 of their pelvis and leg motion into the planted clips, keeps B_Spine's
  planted world orientation, re-floors the feet, and keeps 0.4 of the slash's trunk lean (the source leans 31-40 deg
  forward throughout, a fencing hunch -> max 16; walk/run 3-6). First try 0.35 legs with the trunk following the
  pelvis: wide straddle and the forward hunch back. Result: weight shift, right foot steps back, knees flex; pelvis
  range 3.5 cm. Blow still 0.75 s; edge share 0.74; G6 attack <= 0.6 cm; viewer clean; regression pass; in game
  `review/ingame/legs_crops.png`, sheet `review/legs_attack.png`.
- Follow-up (user): the right foot jiggles between viewer frames 8 and 11. Trace (48 fps): the blended right ankle
  jumped ~10 cm sideways for two source frames - the Mixamo slash's own foot pop where its step starts - and the feet
  glided several cm while on the floor. `clip_timing.py` now drives the planted clips' legs by two-bone IK to foot
  targets: median (5 frames) + Gaussian (1.5) filtered, turned into discrete steps - home = the Standing foot, one
  foot in the air at a time (6 frames, 3 cm sine lift), hold = the mean target around the widest moment (capped at
  15 cm), feet flat at the home height and rotation, steps back home in reverse order at the end. Attack: left out
  15 cm, right 10.5 cm, both before the slice; battle cry 7-8 cm. Intermediate tries: home = the clip's frame 0 (the
  foot still glided 13 cm through the lead-in), both feet stepping at once (a hop), hold = the extreme (29 cm).
  Ankles now move <= 3.1 cm per 1/48 s and only in the lifted steps; no joint below Standing's floor level; blow 0.75 s;
  edge share 0.74; G6 attack <= 0.6 cm; viewer clean; regression pass.
- Follow-up (user): the thigh jiggles the same way, viewer frames 7-10. The leg IK took its knee bend plane from the
  blended knee, which carried the source pop (right thigh 7.0 and 8.5 deg in single 1/48 s steps, knee 3 cm out and
  back). The bend plane now comes from each foot's forward (ankle -> toe at the constant home rotation): knees over
  the toes. Frames 7-11: knee < 0.3 cm per step, thigh <= 0.9 deg; whole attack thighs <= 4.3 deg per 1/48 s (in the
  return step; walk 7.4).

### Running clip swap 2026-10-13

**Historical: Jogging rejected by the user on 2026-10-13; superseded by Standard Run below.**

User scope: replace only Running; RelaxRunForward is banned. The previously installed creature remains
user-accepted. No installation, game launch/build or commit was performed. Workspace lease owner:
`codex-run-swap-bar1`. Original masters and all export GLBs are preserved under
`work/pre_runswap_20261013/` with `sha256.json`.

- Source: `anim_library/mixamo/Jogging.fbx`, index `mx/jogging_478abf`, retargeted through
  `retarget_mixamo.py` and the existing twist calibration. Source receipt: `work/runswap_source.json`.
  Keep its central cycle (source frames 26–52), fit contact/stride with `scripts/swap_running.py`, and
  copy the first pose to the last. Output: 27 keys / 26 intervals at 30 fps (0.866667 s).
- Retained source torso/arm swing; maximum torso lean **12.39°**. Fitted feet use forward-facing soles,
  alternating stance and a low brief flight. The run stride is **1.86 m**, from the unchanged binding's
  1.2 m × the engine's 1.55 run multiplier (`WorldFxSystem.cpp`). Measured stance travel is
  1.859975–1.860053 m/cycle. At scale 98.9 and table speeds 260/280/300 the distance-driven cycle is
  0.707515/0.656979/0.613180 s; gameplay speed and bindings are unchanged.
- The unarmed source wrist pointed the blade into the head; retain the calibrated carrying direction and
  solved right-hand finger rotations (maximum quaternion-component difference **0**). Open the left
  fingers to their fitted rest pose to avoid the foreign curl tearing the web. Resolve elbows in their
  hinge planes while retaining hand world orientation. Arm abduction is 9° for clearance.
- Project gates on Running: G4 arm stretch **p99 ≤1.38×, max 1.96×** over all 27 frames;
  G5 hand stretch **R 2.91× / L 1.85×**; G6 forearm/hand/blade-axis contacts **0**.
  `g5_grip.py` was also run; its legacy re-derived circle diagnostic is in `work/runswap_grip.log`.
  The accepted solved grip itself is preserved, as checked by `work/runswap_motion.json`.
- Shared exported-mesh gate, full detail: arm/body and actual sword/body penetration **0 mm**;
  floor penetration **0 mm**; foot contact **97.596%**; maximum flight **12.424 mm**;
  foot yaw **L 3.543° / R 1.439°**; elbow-plane error **L 0.076° / R 0.029°**.
  **The complete shared gate verdict remains FAIL (exit 2)**: inherited palm/grip geometry and coarse-LOD
  foot measurements remain, and Sword LOD2 has no complete handle surface for its grip selector.
  No new failure category occurs against the accepted baseline. All **5,619 non-Running rows are
  exactly unchanged**. Reports: `review/runswap_20261013/gates/`, `gates_baseline/`, and
  `work/runswap_gate_comparison.json`. The full-detail inherited palm/handle angle is 64.399° (limit 60°).
- Staged `integration/actors.yml` contains the exact three installed Barbarian entries. `check_bindings.py`
  exits **0**, prints **no BAD**, and reports zero skin-weight-sum error for body and sword.
  `check_viewer.mjs`: **24/24 tier/clip switches**, zero errors. Agent inspected all eight cycle positions
  from front/side/three-quarter and arm close-ups: `review/runswap_20261013/running_review.png`
  and `viewer_final/`. New artistic acceptance is not yet recorded.
- `sync_actions.py ... Running` transfers only Running into `rig_v5.blend` and `rig_v6.blend`.
  `export_running.py` exports animation channels; `replace_running_glb.py` appends only those channels
  to the existing final GLB, LOD0 export and three viewer GLBs. No geometry/LOD/texture rebuild was used.
  All seven other exported clips have byte-identical keys; every original payload byte and all mesh,
  texture, material, skin and node records are retained. The sword GLB is byte-identical.
  Master meshes/weights/UVs/bind skeletons/images and all other action keys compare identical too.
  Receipts: `work/runswap_glb_comparison.json`, `runswap_review_comparison.json`,
  `runswap_master_comparison.json`. All 168 Running samplers have exactly equal first/last outputs.
- New `export/mm6_bar1.glb` SHA-256: **`aeb96ef8b33ad883112f56b81946417f4b752c5a1cd17a8a519f4d66c77068f5`**.
  Installed body/sword and all three Barbarian bindings remain unchanged. Other sessions edited unrelated
  `actors.yml` entries during the work; verification is recorded in `work/runswap_installed_verification.json`.
  Older intermediate `runtime_lod0`/`lods`/`shadowfix` exports were not rebuilt; use the final GLB above.

Replay: the full `rebuild.sh` now selects Jogging and fits only its Running action after grip application.
For this narrow operation, retain the source retarget/twist outputs in `work/run_raw.blend` and
`work/run_twist.blend`, run `swap_running.py`, sync only Running to each master, then run
`export_running.py` and `replace_running_glb.py` against the immutable backup. Every Blender call
uses background mode with `--threads 4`. Installation remains outside this task.

### Running clip: Standard Run — review round 1 (2026-10-13)

**Superseded by Review round 2 below: user rejected the low pelvis/crouched stance in image #95.**

The user rejected Jogging: “please no jogging, do running ... like we have in the other sheets,
jogging doesnt fit.” Running now uses **`anim_library/mixamo/Standard Run.fbx`**, the requested
Cannibal source, index `mx/standard_run_f8c60f`. Source SHA-256: `64d7e112a4ce95b2543cccfea18a4a654f00bde8fddd0612b40bb43261fdd6bb`.
No credits spent. Backup before edits: `work/pre_runswap2_20261013/` (masters, exports, viewer,
staged bindings and prior run-fit scripts; `sha256.json`). Lease owner: `codex-run-swap-bar1`.

- Retargeted with `retarget_mixamo.py` from `rig_v1.blend`, then the existing twist calibration on a
  temporary donor. `swap_running.py` keeps the Standard Run upper-body motion, resolves elbow hinges,
  adds 9° arm clearance and 70° right forearm supination so the sword swings beside the body.
  The wrist and solved right fingers retain their accepted local grip; maximum finger quaternion
  component difference **0**. No mesh, weight, skeleton, sword or attachment edit.
- **23 keys / 22 intervals at 30 fps (0.733333 s)**. All **168 exported Running samplers** have
  byte-identical first/last outputs. Legs use matched stance travel and smooth returning feet,
  toe-down recovery, low flight and a smooth two-bob pelvis path. The stance measurement is
  **2.014972–2.015037 m/cycle**, matching **2.015 m = 1.3 × 1.55**.
- Only the three staged `animation.stride_length` values change **1.2 → 1.3**. Scale remains 98.9;
  table speeds remain 260/280/300. Run cycles at those speeds are **0.766475 / 0.711727 / 0.664278 s**.
  The engine shares this stride setting with Walking, so its distance-driven cadence also changes;
  Walking animation keys remain identical. Installed bindings remain untouched.
- Shared full-detail measurements: **88.636% contact**, **11.364% above the 10 mm contact band**
  (about 83 ms total per authored cycle, split between two brief flights); maximum lower-foot
  elevation **13.836 mm**. Floor penetration **0.256 mm**, toe yaw **L 4.688° / R 2.146°**,
  trunk lean **19.832°**. Arm/body, sword/body and head penetration **0 mm**.
- G4 over all 23 frames: arm stretch **p99 ≤1.35× / max 2.04×**. G5 hand stretch:
  **R 2.91× / L 1.61×**. `g5_grip.py` diagnostic rendered at frame 6; its re-derived circle is
  diagnostic only, while the accepted solved grip is verified unchanged. G6 reports no
  forearm/hand/blade-axis contacts. Logs: `work/runswap2_g4.log`, `runswap2_g5.log`,
  `runswap2_g5_hand.log`, `runswap2_g6.log`; grip renders in `review/runswap2_20261013/g5_*`.
- Pelvis/head jitter: shared angular-step and angular-acceleration gates **PASS**. Maximum rotation
  steps **4.547° / 1.883°**; angular acceleration **5515.6 / 2363.0 deg/s²**. Additional explicit
  project position checks pass: vertical bob ranges **43.392 / 44.854 mm**; max steps at ~48 Hz
  **7.763 / 8.566 mm**, max vertical acceleration **9.077 / 10.228 m/s²**. Pelvis half-cycle
  symmetry error **0.000119 mm**, head **1.667 mm**. See `review/runswap2_20261013/jitter.json`.
- Shared runner focused on Running: **790 PASS, 16 FAIL, 9 UNVERIFIED, 28 INFO, 8 N/A**, exit **2**.
  This is **not an all-pass result**. Remaining failures are the inherited **64.399° palm/handle
  angle** (limit 60°) and coarse-LOD foot yaw/contact measurements. Grip-surface selection remains
  UNVERIFIED (the existing coarse sword handle is incomplete). No new failing/unverified category
  against the preceding export; see `gate_comparison.json`. Thresholds were not relaxed.
  The runner uses `work/run2_gate.glb`, retaining the final geometry and all LODs with only the
  Running animation entry. `work/run2_candidate.glb` is byte-identical to the final export.
- Binding checker: **exit 0, no BAD**, body/sword weight-sum error 0. Viewer checker: **24/24**
  model/clip switches, zero errors. Receipts: `review/runswap2_20261013/bindings.txt`,
  `viewer_check.txt`, `gates/gates.json`. Agent inspected the textured front/side/three-quarter
  [running sheet](review/runswap2_20261013/running_review.png); new user acceptance is pending.
- `sync_actions.py ... Running` updates only Running in both masters. `export_running.py` exports
  those channels; `replace_running_glb.py` transplants them into the backed-up final GLB, LOD0 and
  three viewer GLBs, preserving every original binary payload byte and all non-animation records.
  All seven other exported clips have identical hashes. Master action keys, mesh/weights/UVs,
  materials, bind skeletons and packed images compare identical. Evidence:
  `work/runswap2_glb_comparison.json`, `runswap2_master_comparison.json`, `runswap2_motion.json`.
- Final body SHA-256: **`4810e5fad20a9ed11885ee1a46ccc7ece438139a47abdb5f02ad723a44ed8abe`**. Full file hashes and unchanged triangle counts are in
  `review/runswap2_20261013/artifact_receipt.json`. Installed body/sword and `actors.yml` hashes
  were checked unchanged. No installation, game launch/build or commit.

Replay the narrow swap from this project's directory, using background Blender with `--threads 4`:
retarget Standard Run into `work/run2_raw.blend`; run the twist script into `work/run2_twist.blend`;
run `swap_running.py`; sync only Running into v5 then v6; export Running channels and transplant
against `work/pre_runswap2_20261013/`. `rebuild.sh` now selects Standard Run for a future full rebuild.
`build_runtime.sh` was inspected but deliberately not run: it recomputes other clip timing, geometry,
LODs and textures. Existing intermediate runtime/LOD/shadowfix files remain historical; the deliverable
is `export/mm6_bar1.glb`. The staged stride update must travel with this export at later installation.

### Review round 2 — high-pelvis Running (2026-10-13)

User rejected the crouched run in image #95. The previous fit forced the pelvis 19 cm below its
rest position while extending the feet into a 2.015 m gait. Removed that offset and refitted only
Running. Backup: `work/pre_runswap3_20261013/`; owner `codex-run-swap-bar1`. No paid work.

**Posture and source:** Standard Run remains the source, through the retained Mixamo-retarget/twist
donor `work/run2_twist.blend`. `swap_running.py` now reads the original FBX hip profile before the
retargeter's floor correction, averages its two half-cycles, smooths adjacent samples, scales its
vertical excursion to 45% after the measured leg-length ratio, and anchors the minimum to 92.1%
of Standing frame 0. This preserves the source's bob timing/shape while fitting its amplitude to
this body. Standing pelvis: **0.987648 m**. Running minimum **0.909624 m (92.100%)**, mean
**0.924118 m (93.568%)**; bob **30.664 mm**. No framewise floor correction or low hip offset.
Source trunk sway and arm/sword swing are retained; sagittal trunk target is 16° (was 17°), and the
full-detail shared trunk measurement peaks at **19.353°**. Grip component difference is below
**1.1e-7**, with the sword attachment/export unchanged.

**Gait:** stride **1.600 m**, source duration **0.733333 s**. Each foot has a 35% exactly fitted
stance and a smooth recovery; stance phases are aligned with the source hip profile. Full-detail
480 Hz skin measurements give contact **38.352% L / 38.068% R**, either-foot contact **76.420%**,
flight **23.580%**, peak lower-sole flight height **42.798 mm** (limit 60 mm). No floor penetration.
The original 30 fps export allowed ~3 mm of interpolation drift; quarter-frame leg/root fitting
and a **120 Hz export (89 samples)** reduce full-stance ankle drift to **0.207 mm L / 0.212 mm R**
after applying the runtime forward displacement. Other upper-body keys retain the original rate.
All 168 exported Running samplers have exact first/last values. Stance knee flexion is
**L 23.66–54.22° / R 19.11–49.50°**; recovery peaks **116.47° / 114.38°**, rather than a sustained
wide low lunge. Runtime cycles at speeds 260/280/300 and scale 98.9:
**0.608615 / 0.565143 / 0.527467 s**.

Only the three staged stride fields change **1.3 → 1.032258064516129**; multiplying by the engine's
1.55 run factor gives 1.600 m. Walking's keys are identical, but the shared binding also changes its
distance-driven cadence. Installed bindings and models were verified unchanged.

**Checks on the final export:**

- `running_gait.py`: pelvis, 35–45% per-foot contact, flight <=60 mm and <2 mm stance drift all pass;
  measurements above are from `review/runswap3_20261013/gait.json` at 480 Hz.
- Shared runner focused on Running: **789 PASS, 17 FAIL, 9 UNVERIFIED, 28 INFO, 8 N/A**, exit **2**.
  At its 48 Hz sample grid: contact **74.432%**, flight peak **40.258 mm**, toe yaw
  **4.371° L / 1.778° R**; arm/body, sword/body, head and floor penetration all **0 mm**.
  Per the user's revised rule, this project's Running-only thresholds are contact >=70% (two 35%
  stances), airborne <=60 mm, pelvis >=92% of Standing. Other thresholds remain unchanged.
  The report is **not all-pass**: the inherited palm/handle angle is **64.399°** (limit 60°), grip
  surface selection remains UNVERIFIED, and the immutable coarse meshes retain foot yaw/contact
  findings. **Shadow LOD2 contact (56.818%) is newly flagged in this pose**; colour LOD3 and shadow
  LOD3 also fail contact. No mesh edits were made to address coarse-LOD sole geometry.
- G4: all 23 original frame positions, arm stretch **p99 <=1.35× / max 2.04×**.
  G5 hands **R 2.91× / L 1.61×**; solved grip verified against the preceding GLB. G6 no
  forearm/hand/blade-axis contacts. Shared export checks also sample between original frames.
- Pelvis/head angular jitter passes: step **4.620° / 2.127°**, acceleration
  **5444.1 / 5464.9 deg/s²**. Vertical step at ~48 Hz **6.147 / 6.625 mm**; vertical acceleration
  **7.344 / 8.930 m/s²**. Pelvis half-cycle symmetry error **0.000124 mm**; head **1.926 mm**.
- Bindings: **exit 0, no BAD**, body/sword weight-sum error zero. Viewer: **24/24** switches,
  zero errors. Agent inspected the new textured [front/side/three-quarter sheet](review/runswap3_20261013/running_review.png).
  User artistic acceptance remains pending.

**Preservation:** `sync_actions.py ... Running` updates only Running in v5 and v6. `export_running.py`
now honours the action's subframe sampling in memory (time remains unchanged), then
`replace_running_glb.py` replaces only Running in the immutable backed-up runtime/LOD0/viewer GLBs.
All seven other exported clip hashes match. Master non-Running action keys, meshes, weights, UVs,
materials, bind skeletons and images match. Every original GLB payload byte and non-animation
record remains intact. Sword export and all triangle counts remain identical.

Final `export/mm6_bar1.glb`: **`9003969a9f845f90acba05a20255dfb5f3ec810e65f922c97d76e9a87e9b2681`**.
Receipts: `review/runswap3_20261013/artifact_receipt.json`, `gate_input_receipt.json`,
`gate_comparison.json`, `gates/`, `gait.json`, `jitter.json`, `bindings.txt`, `viewer_check.txt`;
master/key comparison in `work/runswap3_master_comparison.json` and `runswap3_glb_comparison.json`.
The shared gate input retains the final geometry, LODs and payload, with only Running in the
animation list; the complete candidate is byte-identical to the final export.

Replay: `swap_running.py` defaults to backup3 plus the retained Standard Run donor; sync only
Running to both masters; run `export_running.py` and transplant against backup3. The dense leg
keys require this channel-only export path. `build_runtime.sh` remains unrun because it also
retimes other clips and rebuilds geometry/textures. Historical intermediate exports remain
unchanged. No installation, game launch/build or commit. Blender ran serially with `--threads 4`.

Final concurrent-work check: the global installed actors.yml hash changed outside this session;
all three installed Barbarian blocks still exactly match the pre-round snapshot, as do both
installed model hashes. The artifact receipt records the descriptor-level verification.
