# Quadruped / non-humanoid creature playbook (Claude)

The route that worked for the MM6 rat (`mm6_rat_claude/`, user verdict 2026-10-07: "this one is actually good").
Use it for four-legged and other non-humanoid creatures (rats, wolves, bears, spiders with adaptation, lizards).
For humanoids use [CLAUDE_HUMANOID_NPC_PLAYBOOK.md](CLAUDE_HUMANOID_NPC_PLAYBOOK.md). Elementals and other bodies made
of wind, flame or light skip Meshy: see "Elementals and other effect-bodied creatures" below.

Result: one session, 15 Meshy credits, no hand posing, first in-game result accepted.

## Why this route

- **Meshy gives the model, not the motion.** Meshy's auto-rig, animation library (all 678 clips biped; see the
  [animation catalogues](claude_shared/catalogues/ANIMATION_CATALOGUES.md), which also list Mixamo) and
  Text to Motion are humanoid-only. So the model comes from Meshy; rig and clips are ours.
- **Quadrupeds suit procedural animation.** No hands or held props (where humanoids broke); legs on IK footholds
  and a lagging tail look natural with a few parameters, and every frame can be checked automatically.
- **Compact bodies take Blender automatic (heat) weights well.** No proxy skeleton, no weight surgery.

## Steps (reference scripts in `mm6_rat_claude/scripts/`)

0. **HD masters first ([CLAUDE_HD_MASTER_REFERENCES.md](CLAUDE_HD_MASTER_REFERENCES.md)).** Before any Meshy job,
   have Codex image generation produce five masters from the ORIGINAL native bitmaps: `00_three_quarter`
   (Smart Topology input), `01_front`, `02_back`, `03_left`, `04_right` (retexture views). Gate them against the
   native frames. Never send Meshy a native sprite, a restored x2 frame or an enlargement of one.
1. **Inputs.** Restored 2x sprites in `level_generation/creatures/mm6_<name>/trimmed_2x/` (standing views
   `<x>sta0..4` = front, three-quarter front, side, three-quarter back, back), native action frames, per-palette
   previews in `native_variants/`, action timings in `manifest.json` (`animations.*.sequence_ms`).
   Descriptors/tier palettes: `assets_dev/engine/data_tables/monster_descriptors.txt`; sprite frame scales per
   tier: `assets_dev/engine/rendering/sprite_frame_data_common.yml` (`<x>sta` entries).
2. **Project + claim.** New `mm6_<name>_claude/` with `creature_3d_progress.json` (`meshy: {credit_limit, jobs}`),
   `python3 tools/creature_workspace.py claim --project <P> --identity mm6:<name> --owner <session>
   --state creature_3d_progress.json --budget 30`.
3. **Model (5 credits)** from `references_hd/00_three_quarter.png` (step 0), never from a sprite frame.
   `requests/smart_topology_v1.json`: `ai_model: meshy-t2`, `model_type: smart-topology`,
   `target_polycount: 8000`, `should_texture: false`, **no `pose_mode`** (A-pose is for humanoids).
   Submit/poll/download via `./tools/run_creature_meshy.sh` (poll `--wait-seconds` ≤ 45, loop in a Monitor).
4. **Joints from the mesh** (`grid_views.py`, plus slicing). Render side/top/front orthographic views with a
   labelled 5 cm grid, and slice the mesh: per-height centroids of vertices in each leg's box give the leg axis;
   per-y z-ranges near x=0 give the spine/tail midline. Read joints from numbers, not by eye.
5. **Rig** (`rig_rat.py`). Import, apply transforms, ground (min z = 0), forward −Y. Skeleton:
   `Spine1..3` (root = Spine1 at the hips), `Neck1`, `Head`, `Tail1..6` (parent Spine1),
   per side `UpperArm/ForeArm/FrontPaw` (parent Spine3) and `Thigh/Shin/HindPaw` (parent Spine1). No toes,
   no jaw unless needed. `parent_set(type='ARMATURE_AUTO')`; require 0 unweighted vertices.
6. **Stress check** (`stress.py`): rest with bones drawn, stride, rear up, tail curl + head turn, roll onto the
   back. Look for tearing/collapse before animating.
7. **Clips** (`anim_rat.py`, 24 fps). Each clip is a function of time:
   - legs: two-bone IK on footholds (`posing.two_bone_ik`), front pole behind (elbow back), hind pole in front
     (knee forward), paws keep their rest orientation plus a toe-down pitch in swing;
   - gait: trot with diagonal pairs (LF+RH, RF+LH), duty ~0.55, swing lift, body bob, spine sway; running =
     same with longer stride and lower duty; `stride_length` in the binding = body travel per cycle (m);
   - tail: per-segment yaw/pitch sine with a phase lag along the chain, amplitude growing to the tip;
   - actions: keyed parameter sets (hips offset/pitch/roll, spine, head, paw offsets, tail lift, or free FK legs)
     with smoothstep between keys, choreographed from the native action frames;
   - **floor rules every frame**: lift the root if body/head/upper legs sink; aim tail segments up when their end
     dips under the floor; swing an underside leg about its upper joint until its paw clears (lying poses).
   Dead = last Death pose held 1 s. Check with `clip_sheet.py` and a per-clip min-z report (target ≥ −1.5 cm).
8. **Texture (10 credits).** UVs from `claude_shared/uv_atlas.py` (not Smart UV Project; the older projects' `uv_export.py`
   layouts came out smudged), export an unrigged neutral GLB; follow
   [Sharp textures](CLAUDE_CREATURE_TEXTURES.md#sharp-textures-layout-paint-resolution-and-grading-default-since-2026-10-30).
   Retexture request: `meshy-7`, `enable_original_uv: true`, `enable_pbr: true`, `4k` (downsampled once to 2K), `multiview_image_urls` =
   the four HD masters `references_hd/01_front`, `03_left`, `02_back`, `04_right` (step 0), never restored frames.
   `compose_rat.py`: masks from rest-pose 3D position per texel (tail, lower legs/paws, head = skin; rest = fur;
   collar studs by colour; eyes as spheres located from the iris-coloured texels of the cleaner eye, mirrored and
   refined per side, painted whole: black pupil facing outward/forward, tier iris, dark rim — colour masks alone
   leave patchy sockets), roughness classes (fur 0.78, skin 0.62). **Tiers:** one shared texture set plus a
   region mask (skin, fur, eyes) and per-tier colour ramps from the native palettes, per
   [CLAUDE_CREATURE_TEXTURES.md](CLAUDE_CREATURE_TEXTURES.md); no per-tier base colours. Give the head UV island
   2–3× the body's texel density. Albedo ≈ native median × 1.45 (sprites carry baked shading). The rat pilot still
   bakes A/B/C base colours and is listed for migration there.
9. **Runtime** (`build_runtime.sh --install`): export → `tools/prepare_actor_glb.py` → `tools/build_actor_lods.py
   --mesh-node <Mesh>` → `shrink_shadow_lods.py` → `../claude_shared/region_variants.py <in> <out> textures/<x>_ramps.json` (A/B/C skins as KHR_materials_variants that
   share every image and differ only in ramps; the rat's own `add_variants.py` is the old baked route). Then the far
   LODs and their checks per the [LOD playbook](LOD_PLAYBOOK.md).
10. **Install** each accepted GLB with `tools/install_model.py <project>/export/<name>.glb` (source in
    `assets_source/worlds/mm6/models/`, runtime copy in `assets_dev`; see AGENTS.md), then the **binding** in
    `assets_dev/worlds/mm6/models/actors.yml` (copy the rat entries):
    - `scale` = standing sprite silhouette height (native px, alpha bbox of `native/<x>sta2.png`) × tier-A frame
      scale ÷ model rest height (m); rat: 76 × 0.8 / 0.26 ≈ 234. B/C: `scale_reference: <A descriptor>`.
    - `yaw_offset: -1.570796327` (model faces −Y).
    - an `animation:` block needs `cast`, `run`, `stride_length`, `upper_body_root` **and `sockets: {}`**
      (even empty; a missing key fails the whole file). Non-casters: `cast: Attack`.
11. **Checks.** `OPENYAMM_REGRESSION_FILTER=mm6_ ./build/game/openyamm --world mm6
    --headless-run-regression-suite actors`; then in-game captures with an input tour (console
    `actor spawn <id> <n> <x> <y> <z>`, `action: attack` steps, `capture:` steps), once with
    `debug.actor_models=true` and once `false` for a 3D-vs-sprite comparison at the same spawn and camera.
    The user judges that comparison; no frame-by-frame review.

## In-game test locations (all creatures, user-chosen 2026-10-08)

Quiet places for 3D-vs-sprite checks; use the same camera for both runs (`debug.actor_models=true`, then `false`).
- **Outdoor:** New Sorpigal `oute3.odm`, position (-3718.493, 3245.946, 1.0), yaw 3.359 rad, pitch -13.751°.
- **Indoor:** Agar's Laboratory `6d19.blv`, position (1672.832, -2938.578, -46.896), yaw 3.132 rad, pitch -14.868°.

```sh
./tools/run_game.sh --isolated check-out --world mm6 --map oute3.odm --position -3718.493 3245.946 1 \
  --yaw-radians 3.359 --pitch-degrees -13.751 --set debug.actor_models=true --set debug.immortal=true \
  --set debug.menu_input_tour_path=/abs/tour.yml --warmup 3 --seconds 20
./tools/run_game.sh --isolated check-in --world mm6 --map 6d19.blv --position 1672.832 -2938.578 -46.896 \
  --yaw-radians 3.132 --pitch-degrees -14.868 --set debug.actor_models=true --set debug.immortal=true \
  --set debug.menu_input_tour_path=/abs/tour.yml --warmup 3 --seconds 20
```

In the tour, spawn the tiers about 450 units ahead (outdoor around (-4157, 3149, 1); indoor around
(1223, -2935, -47)) with `actor spawn <id> 1 <x> <y> <z>`, one console open/close per command (typing a second
command into a closed console fails the tour: "text entry requires active SDL text input"). Hostile spawns with an
immortal party walk into view and attack, which also shows the attack clip; friendly spawns wander off camera.
Water creatures need water: use their own maps (sea serpent: `outa3.odm`, `oute1.odm`).

## Pitfalls hit on the rat

- Blender camera aiming: `direction.to_track_quat('-Z', 'Y')` (not `'Z'`), or renders come out rolled.
- World-axis rotation signs (forward −Y): +X rotation pitches the front down (rear up = negative); +Z turns the
  head toward +X (character left); a tail bone lifts up with a **positive** X rotation.
- Floor: tail tips and lowered heads are the usual offenders, then underside legs when lying on the side.
- `posing.two_bone_ik_hinge` could loop forever on ties (fixed: halve the step when not strictly improving).
- Do not `pkill -f <pattern>` in the same shell command whose text contains the pattern (kills that shell).
- Regression tests that count loaded models must count distinct models in `actors.yml`, not instanced ones.

## Flyers (MM6 bat, `mm6_bat_claude/`)

- Masters on a landscape canvas, wings spread as in the native front fly frame. The pilot fed Meshy the x2 spread
  front frame `batwae0` plus x2 frames `batwae1`/`batwad2`/`batwae4` for the retexture, and the texture came out
  blurry; redo it from HD masters. Wing joints as top-view (x, y) with z sampled from the membrane
  (`rig_bat.py`), so automatic weights follow the sheet. Export the membrane double-sided.
- One Fly loop serves standing/walking/fidget/run.
- **No extra hover lift; the lowest living point meets the floor** (user decision, 2026-10-21). Native fly frames
  float above the sprite anchor, but billboards lean toward the camera and a 3D model does not. Flyers rise until
  their small collision box (descriptor Height column, bat A = 56) meets the ceiling, so a lifted model goes through
  low ceilings. Start the model at the actor origin and bias the flap downward so the upstroke stays low. Fliers sit
  at floor height too (spawn, idle, matching the party's height): over every living clip the lowest point, wing tips
  included, must meet the floor, neither cutting it nor floating above it. Measure with
  [`floor_audit.py`](claude_shared/floor/README.md) and bake the printed amount with `floor_fix.py --hover`, which
  eases it out over the death clip so the corpse rests on the floor. Never use `z_offset` for this: it lifts the
  corpse too.
- **Scale by silhouette area** (front-view alpha area of the fly frames vs the model's Fly frames), not wingspan;
  Meshy bodies are heavier than the sprites' thin wings (wingspan scale came out ~1.3× too big).
- Dead pose: belly on the floor, head down, wings fitted flat. Ground on the **body** vertices, then rotate each
  wing segment (upper arm, then forearm) until it rests at belly height. Grounding the lowest vertex lets drooped
  wingtips prop the corpse up like a tent. Find the flattening body pitch by measurement, because the Meshy rest
  pose may already lean.

Second flyer, MM6 bloodsucker (`mm6_bld_claude/`, winged serpent):
- A **three-quarter** view worked as the Smart Topology input for a long body (body, tail and both wings in depth).
- **Separate mesh pieces** (spikes, tentacles, claws) get mixed heat weights and drift off. After automatic
  weights, rebind every non-main connected piece rigidly to the weights of its nearest main-body vertex
  (`rig_bld.py`).
- A wing raised in the rest pose stays edge-on if it is only lowered about the body axis. For a flat corpse, twist it
  about the upper-arm axis to the angle with the least height spread, then fit it down.
- Big mouth actions (native maw close-ups): do not scale the mesh's mouth tip (it balloons into a faceted, blurry
  bulb). Add a funnel **disc on its own bone** in the mouth opening, textured with the native attack-frame maw in a
  freed UV corner (`add_maw.py`), and key its **scale** (about ×5 at the lunge peak, 0.55 at rest). Keep the lunge
  short (under 0.1 m), because melee attackers sit at the camera. The engine plays glTF scale channels.
- **Re-run clip scripts on the UV-mapped blend** (`anim_v1.blend` after `uv_export.py`), never on the rig file:
  losing the UVs makes the engine reject the GLB ("material texture requires UV0"). Smart UV Project is
  deterministic, so rerunning `uv_export.py` on the same mesh recovers the identical layout.
- Tier colours: measure native colours per region with the restored `masks_2x` region channels (manifest `regions`)
  over `native_variants/<frame>_<palette>.png`; build the mask from hue classes of the Meshy texture and ramps per
  [CLAUDE_CREATURE_TEXTURES.md](CLAUDE_CREATURE_TEXTURES.md).

## Dragon and drake 3D creation (MM6 Flying Drake lessons)

Supplement to the base steps and flyer notes above, learned from
[MM6 Flying Drake v6](mm6_drg1_claude/README.md) (`drg1`, merged IDs 508–510, 2026-10-13).
The user accepted the repaired head/neck, hover/flight pose split, larger limbs and corrected tail junction.
The original-style burning death and its runtime timing remain unresolved; do not copy that part as a finished solution.
Use the following checks for later dragons, adapting anatomy and motion to their own native frames.

### References, proportions and poses

- Compare native front, quarter and side views before modelling: measure torso/neck length, forelimb versus hind-limb
  length and thickness, claw size, wing span and tail taper. Full-body references can hide undersized hands/feet and a
  weak head. Use dedicated HD close references for these regions when needed; native/restored frames are comparison
  evidence, never Meshy inputs (see [HD masters](CLAUDE_HD_MASTER_REFERENCES.md)).
- Establish **hover and travelling flight separately**. This Drake needed a chest-up Standing pose with hanging hind
  legs, but Walking/Running retained forward flight. A single global upright correction made locomotion wrong.
  Counterpose the neck and wing roots when pitching the trunk; inspect front and side silhouettes through a full flap.
- Try a local proportion edit before replacing a good body. Increasing leg length alone leaves spindly legs; enlarge
  thigh/forearm volume and clawed extremities as needed. Check for existing pose-scale shrink before editing geometry.
  The Drake's accepted fix broadened limbs around their fitted bone axes and removed a 0.75× forelimb pose scale.
  Its particular factors are recorded in the project; they are not defaults for other dragons. Preserve UVs when the
  edit supports it, then check texture stretch at the actual review distance before paying for a retexture.

### Head graft and texture continuity

- A separately generated head needs a **connected neck transition**. Cut away both obsolete neck stubs, fit their
  boundary cross-sections and bridge them with a weighted loft, following the multi-headed-creature notes below.
  Overlapping stubs produced an obvious collar/gap. Carry continuous neck UV coverage across the bridge, matching
  scale size, green skin and gold belly plates; inspect front, side, underside and bent-neck poses.
- Keep **body, head and wings in separate texture sets** when their detail needs justify it. The Drake uses three
  independent 2K PBR sets; dedicated 4K body/wing returns supplied detail for the final 2K maps. Separation preserves
  texel allocation but does not fix a stretched unwrap or mismatched reference detail by itself.
- Check the **embedded GLB images**, not only the requested Meshy resolution. An earlier composition/export reduced
  2K returns to 1K. Inspect the body, neck seam and both membrane sides close up, along with UV density, colour/roughness
  continuity and every palette variant. Reject generated details such as a false mouth painted on a cut neck.

### Skin weights at crowded junctions

- Bone proximity alone cannot distinguish belly/tail from nearby thighs, or shoulder skin from neck/wing roots.
  Define anatomical ownership first, then blend within and across those regions. Hard coordinate-box boundaries and
  nearest-bone assignments can look acceptable in forward flight but fold badly after an upright pose change.
- In the Drake, central belly/tail vertices followed hind-leg bones. Rotating and lengthening the legs pulled the gold
  underside into a sharp ridge between the thighs; weight-driven limb enlargement also deformed that same skin.
  Fix ownership **before** proportion edits: central/high tail-base skin follows the trunk/tail, with a smooth blend
  into the lateral/lower thigh. Reapply enlargement from the pre-edit checkpoint so the mistaken deformation is removed.
  See [repair_tailjoin.py](mm6_drg1_claude/scripts/repair_tailjoin.py); its bounds belong to this mesh only.
- Review the belly-to-tail join from front, quarter and rear in hover, forward flight, attack and hit poses. Check
  jaw/tooth ownership separately so opening the mouth does not stretch the upper muzzle. Inspect stray slivers and
  disconnected pieces at forelegs, chest and wing roots; remove confirmed artefacts and repair only their local holes.
  Protect intended horns, claws and membrane tips from broad cleanup operations.

### Reduction and delivery checks

- Reduce only after junction repairs and weighting. Try roughly **10% fewer triangles**, compare against the selected
  higher-detail checkpoint in textured closeups and deformed poses, accept only if quality holds, then repeat. Stop at
  the first visible or measured unacceptable loss and retain the previous passing step. Preserve thin wing membranes
  in lower LODs and inspect their backfaces; a static silhouette alone misses bending and seam failures.
- The Drake's earlier v2 pass retained 18,881 → 16,992 body triangles. After the accepted v6 anatomy/weight repairs,
  a fresh ladder retained **16,992 → 15,292**; the next trial reached 14,596 (13,764 requested) but tore wing membranes
  into strips, pinched the belly/tail and penetrated the floor during Attack/Cast. Protected-vertex surface error was
  still zero: that measurement alone does not establish intact membranes or good deformation. These are tested stopping
  points, not mathematical minima. Report requested and achieved counts, body, extra FX and runtime backface copies
  separately. Recheck reduction after later proportion/weight edits; see the project's v7 comparison evidence.
- Preserve revision checkpoints and verify unaffected geometry/weights, UVs and materials. Check animation at normal
  and slow speed, intermediate frames around deformation extremes, GLB reimport parity and the installed asset.
  Viewer tier/clip loading checks complement visual inspection; passing them does not prove anatomy is correct.
  Calibrate native size and check the actual habitat: an upright model can intersect a low ceiling even when its
  origin is grounded. The Drake's Agar ceiling intersection remains a known limitation, not a passed silhouette check.

### Burning death: model work versus engine work

- Study the **selected native playback sequence and timing**, not every frame file in alphabetical order. This Drake
  selects a/b/c/d/f for 0.9375 s before corpse h; other available art is not necessarily played. The original burns
  holes through a recognizable silhouette, then leaves flame edges, embers and charred remains.
- Skeletal shrinking and attached flame cards did not reproduce that surface erosion. Author recoil/curl/wing folding
  in the model; a convincing burnaway needs engine-supported surface removal, a glowing burn edge and flame/ember FX,
  with consistent colour/depth/shadow coverage and remains excluded from burning. This is a proposed engine feature,
  not an existing capability or automatic part of each new dragon's asset work.
- Verify the gameplay-to-visual death handoff. At this session's revision, `death_effect: disintegration` supplied a
  particle burst, not a mesh burn shader, and skipped longer death-clip continuation: a 1.5 s authored Death could jump
  to Dead after 0.9375 s. Recheck current engine behavior before reuse. Align the clip to the native clock or explicitly
  implement a visual continuation without changing AI/loot timing. Keep this issue visible in the progress record even
  when the model's appearance is accepted. See the project's [death assessment](mm6_drg1_claude/README.md#death-findings-and-recommendation).

## Floating heads (MM6 Flying Eye, `mm6_bh_claude/`)

- No legs and no ground contact. A small rig (Body hover root, Head, Jaw, EyeBall, Tendrils) is enough; pieces bind
  rigidly, and the jaw and tendrils blend on the main piece. Clips are hover bob/tilt, forward lean for flying, jaw
  gapes for attack and cast, and a drop-and-roll death under the engine's disintegration particles.
- **Spellcasting tiers need a `cast` clip distinct from Attack.** The engine rejects the whole `actors.yml`
  otherwise, and every actor regression fails.
- Find the eyeball by its painted iris, not by the first round piece: Meshy split the eye socket ring and the
  eyeball into separate pieces.
- Ivory teeth have a skin-like hue (below 40°). Classify them into the face/horn region as the sprite masks do, or a
  tier ramp turns them the skin colour.
- The sprite package's `masks_2x` region channels give per-region native colours for every palette directly
  (`tier_ramps.py`).

## Spiders and other segmented creatures (MM6 spider, `mm6_spi1_claude/`)

- **Masters for a new mesh:** ask for a neutral star pose with every leg separated by air gaps and all feet on one
  plane (in the sprite's colouring for tier A). Smart Topology from the three-quarter master then gives clean
  separate legs.
- **Rigid pieces mean an exoskeleton rig.** Meshy returned each leg as femur, tibia and tarsus pieces
  (`components.py` lists them). Place each joint at the closest-vertex junction of consecutive pieces and the hip at
  the femur's junction with the body. Bind each piece 100 % to its bone (`rig_spi1.py`). That is faster and cleaner
  than heat weights, and the joints rotate like real segments.
- **Clips.** Feet go by two-bone IK (femur + tibia) with the tarsus keeping its rest direction, and the knee pole
  above and outside. The gait is alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4). The death roll needs a final
  exact grounding pass so the corpse does not float.
- **Tiers straight from the native palettes:** sample the same body pixels in every palette sprite (exclusion mask
  built once on tier A), and map them to the shared base by luminance quantile (`tier_ramps.py`). This needs no
  per-tier compose.
- **Size check:** friendly actors walk up to the party, so moving captures exaggerate size. Compare a static
  `model spawn <glb> x y z <scale> <yaw>` beside a sprite actor at the same distance.

## Snakes (MM6 cobra, `mm6_cob_claude/`)

- Codex HD views in the native profile pose (ground body straight behind, front third raised, hood spread) and one
  Meshy multi-image job (30 credits) gave a clean single mesh; the straight body makes rigging trivial.
- Rig and clips from a curve: per frame, define the centreline (tail on the ground at body-radius height with a
  curvature profile, neck by pitch/yaw per segment, floor rule) and fit every bone to it; weights blend by arc
  position along the centreline (`rig_cob.py`, `anim_cob.py`). Coils are inward spirals whose radius drops by one
  body width per turn, so they cannot cross; print the self-contact margin per clip.
- Lock the tail frames to world up. Frames transported from an upright root roll a coiled tail onto its side.
- Reduce in a bent pose (`reduce_bent.py`). Rest-pose decimation removes the ring loops of a straight tube and the
  slivers fold into a flat blade in motion; this shows only in clip close-ups, not in static views.
- Tier ramps from dark-skewed native palettes: take only the COLOUR from the palette (band-averaged chroma by
  luminance percentile, 15th–95th) and keep the texel's own luminance scaled to the native mean × 1.35, then
  `region_variants.fit_ramps` (`mm6_seas_claude/scripts/compose_seas.py`). Full histogram matching copies the
  sprites' painted-shading range and turns fine Meshy texture into black/white speckles (sea serpent belly).

## Winged bipeds (MM6 cockatrice, `mm6_ckt_claude/`)

- **Heat weights fail on Meshy meshes with thin membranes and loose pieces** (even at 10× scale). Solve them on a
  watertight voxel-remeshed proxy (4 mm voxels keep the membranes) and copy them back with a Data Transfer
  (nearest face, interpolated); then give leftover vertices the nearest weighted vertex's weights (`rig_ckt.py`).
- **Bird legs by IK:** ankle on the foothold, tarsus keeps its rest direction (plus a pitch), hock = ankle − tarsus,
  Thigh + Shin two-bone IK to the hock with the knee pole in front; foot keeps its rest orientation plus toe pitch.
- **Tail floor rule without bending it up:** aim each segment so its end rests at its own radius above the floor;
  rotating segments up until clear arcs the whole tail upward.
- **Spellcasters need a Cast clip distinct from Attack** (engine check), and `attack_ranged` must not be the cast
  clip either. A head socket in the cast event's `glow` places the glow
  and the release.
- **LOD0 reduction:** a vertex-group Decimate modifier barely reduced this mesh; edit-mode `mesh.decimate` on the
  part's selected faces works.
- **Size:** match the native standing height (alpha bbox px × SFT frame scale) to the mean Standing-clip height: 245 × 0.8 / 0.458 m ≈ 428. Silhouette area (359) undersized this winged biped.

## Rigid hard-surface creatures (MM6 Patrol Unit, `mm6_rob1_claude/`)

Topology, normals, UV and material rules for hand-built hard-surface parts:
[game asset modelling guidelines](../GAME_ASSET_MODELLING_GUIDELINES.md).

- **Budget by complexity, not by the Smart Topology return.** The 15k request came back as 14.3k for a sphere with two
  rings and a small sensor, which the user rejected as far too many. Region-limited collapse decimation
  (`reduce_lod0.py`, UVs and weights kept) brought it to 4.7k with no visible loss; plan about 5k for simple rigid
  shapes.
- **Meshy symmetrises front and back.** Front-only features (the eye, V notches) came back on the back as well.
  Delete duplicated separate pieces; rebuild simple shells as surfaces of revolution from a section measured on the
  Meshy piece (`clean_rob1.py`). Moving vertices to close a notch left ragged edges.
- **One bone per part, parameters per frame.** Each clip frame turns a parameter set into one world transform per bone
  (`anim_rob1.py`); no IK or weights. Do not split one connected shell between bones that move apart (faces across
  the cut stretch).
- **Exploding deaths:** `death_effect: explosion` spawns the Fireball impact burst when dying starts; the Death clip
  throws the parts apart and shrinks them to 1 mm (native sprites with `SpriteDead null` leave no corpse).
- Eye glow: an empty `Socket_Eye` on the eye bone with `sockets: {eye_left: Socket_Eye}` and a tier `eye_color`.
- **Small hard-surface parts (sensor heads, guns, boxes) come out soft from Meshy** (open tubes, blobby boxes) and look
  sloppy up close. Rebuild them as clean boxes with flat procedural colours in a free UV strip (`sensor_rebuild.py`).
- **Lip and inner faces of shells** are painted light by Meshy; ramps turn that into white rim lines. Paint them a
  dark tone in compose (select by distance from the centre).
- **Tier ramps on shiny sprites:** read the native colour at most at the 90 % quantile; the top tenth is baked white
  highlight and makes the tiers too light (`tier_ramps.py`, `QMAX`).

## Hand-built machines (MM6 Reactor, `mm6_rea_claude/`)

- **Turned machines need no Meshy job.** Measure the radius per row from the restored front frame (1 native px =
  1 cm, binding scale = frame scale x 100) and build surfaces of revolution procedurally (`reactor_geometry.py`), with
  a profile section per hard edge. Codex HD masters still give the back and sides of front-only sprites.
- **Fullbright ("Lit") sprite frames:** in a dim room, lit PBR metal reads dull and dark next to them. Ship unlit
  materials with baked light: an analytic chrome response from each texel's true normal seen from the party's eye,
  scaled to the sprite's median metal level per part (`native_shade` in `paint_textures.py`). The actor faces the
  party, so baked front light stays consistent.
- **Animated surfaces on skinned actors** (screens, arcs, lamps, glow levels, liquid) are bone-switched geometry with
  STEP scale keys set after export (`fix_gltf.py`). Scale toggles shrink mid-cross-fade; for screens switch by depth
  (STEP translation behind an opaque window, offsets of 8 mm or more to clear depth precision at room distance).
- **Many small rigid parts: author LODs** by rebuilding with fewer segments (`build(lod=k)` + `author_lods.py`);
  collapse decimation smeared screens and shredded parts. Give each bone's vertices a distinct micro-offset so the
  LOD vertex weld never merges parts of different bones.
- Big stationary machines: put the ranged launch socket at the discharge point and move the discharge to the impact
  marker (`events.attack_ranged.impact`), so the bolt leaves at the flash.

## Water creatures (MM6 sea serpent, `mm6_seas_claude/`)

- Model only the part above the waterline (flat cut at z 0); Root at the waterline, centreline traced by marching
  slabs up the column (`rig_seas.py`).
- Foam/splash at the waterline: an alpha cut-out (MASK) ring mesh on an unparented bone, exported as its own mesh
  node so `build_actor_lods.py` (opaque merged shadows) skips it; spin/pulse it in every clip, shrink it on death.
- No corpse in the sprite: Death sinks the whole body (with the foam gone); Dead is held sunk.
- Spiky meshes: protect only very sharp edges (>90°) in the bent reduction, and unwrap with large islands (89°).
- Test on the creature's own water map (sea serpent: Hermit's Isle from the beach, `--position 2400 0 200
  --yaw-radians 3.1416`); spawn all tiers in ONE console session, because the console key does not reopen
  reliably once water monsters start attacking.

## Multi-headed creatures (MM6 hydra, `mm6_hyd_claude/`)

- Meshy may duplicate a limb that the side views disagree on (the hydra came back with two tails). Cut the extra one
  (`remove_tail.py`) and cap only the cut's own boundary loop. Meshy meshes have other small open holes (mouths, crest
  tips); filling and smoothing every boundary melted the horns. Keep the uncut mesh as the bake source and fill texels
  its rays miss (alpha 0) from a second bake of the capped mesh (`bake_reduced.py`).
- Rig: one body chain plus one chain per neck (`rig_hyd.py`). Split the surface first by geodesic distance from
  seeds (each neck piece above a split height, the body's rear); trace each neck up its piece and then down through
  its own region only (on a denser mesh a middle neck's downward trace wandered into a neighbour's run). Weight each
  vertex within its own chain; use the same ownership for tier regions (`compose_hyd.py`).
- Floor rule per joint: its radius, or its rest height where a neck already runs along the ground; segments lying on
  the ground do not bend in the clips.
- **Many heads: give each its own head model** (user review of v2: "head textures are smeared"). A full-body Meshy
  model spends ~3% of its mesh and ~150 reference pixels per head; no texture work fixes that shape. Per head: Codex
  head masters (five views; `references_heads/h<k>/`), Meshy Smart Topology at 15k (5 credits), unwrap it ourselves
  (smart projection at 66°; normal-binned charts stretched badly) and retexture it (10 credits), then graft it:
  `head_fit.py` traces the head's neck centreline; `graft_heads.py` cuts the head just behind the skull, scales it to
  ~1.3x our neck width, places it rigidly on the Head bone and joins it to our neck (cut a few cm further back) with a
  lofted tube (Hermite centreline, blended cross-sections, zipped to both rings); the high-res retextured head is
  placed the same way as the bake source. Do not bend the head model's own neck stub onto ours: it arched the other
  way, folded and tore at every joint (user review). Texture the loft by copying the neck surface just behind it
  (matched by angle round the neck and arc), not by baking it from the old full-body model. Meshy returns a retexture centred and
  scaled to a 2-unit box: undo that from the upload's own box.
- Texture sets: body 2048² plus a head set with one 512² tile per head (not five heads in one 512 tile). Bake each set
  from its own sources (`bake_hydra.py`); pad unbaked texels from the nearest baked one.
- Wide heads collide: gate every clip with `check_heads.py` (BVH overlap of each head against everything but its own
  neck, every frame); keep heads apart in the clip generator (neighbouring necks turn apart when two heads come
  closer than at rest), scale or squeeze the widest heads, and make inward head turns outward.
- Tube unwraps distort where several necks merge: give faces with an anisotropic tube map (connected clusters) an
  angle-based unwrap instead (`uv_atlas.py`).
- More than four tier regions (body, five necks, five skulls, five stubs, fins): several materials, each with its
  own mask and at most four regions (`Hydra`, `HydraB` on the body set; `HeadsA/B/C` on the head set). A grafted head
  meets its neck at a UV seam, so heads can be materials of their own; give the stubs their own neck-coloured
  regions, grow neck materials a few rings so feathered borders stay inside one material, and pad region labels
  past island borders. Give each material its own baked image in the three.js viewer GLBs.
- Do not remap base-colour luminance to separate classes inside one region: it made blotchy bellies. Give the classes
  their own regions instead (here: heads vs necks). A part excluded from every region keeps its raw base colour in
  every tier (the horns' purple roots): paint such parts in the shared base colour.
- Strike clips for snake necks: a deep wind-up (−1.1 rad) and a ~0.07 s lash whose bend travels from base to head
  (`anim_hyd.whip`); print the neck-to-neck clearance per clip.

## Elementals and other effect-bodied creatures (MM6 air elemental `mm6_aie1_claude/`, fire elemental `mm6_fie1_claude/`)

Bodies made of wind, flame or light have no surface for Meshy to model, so neither Meshy nor HD masters apply
(user-approved routes, 2026-10-13). Build the effect procedurally in Blender from the restored x2 frames (better than
the native ones), and add a simple MPFB figure only when the sprite shows a body inside the effect (fire elemental).
Spend nothing; the sprite package's `masks_2x`, `materials.py` and `recolor_vectors.json` supply the regions and
tier colours. `mm6_fie1_claude/scripts/rebuild.sh` replays the whole fire elemental build.

1. **Read the frames before proposing.** Contact sheets of every action and view of the restored frames, plus a
   measuring grid on key frames: silhouette per row, where an inner figure sits (head, hands, feet), lean in the side
   views (principal axis: fie1 flies with a 20° forward tilt; check which way view 2 faces against a humanoid
   sprite), how big the see-through share is (fie1: 11 % gaps, 17 % figure), and what attack and death actually show.
   Read `sources.json` for frame scales per tier (fie1: all 0.7), timing, the Glowing/Transparent flags and corpse.
2. **Inner figure (if any): MPFB, not Meshy** (`build_figure.py`). Keep only the `body` vertex group, smooth face,
   hands and feet into soft shapes, decimate to about 3k triangles, rename bones without the `mixamorig:` prefix,
   scale and lift onto the sprite figure's span. Pose the arms down and legs together and apply that as the rest pose
   when the MPFB A-pose would push hands through the effect.
3. **Clips from the library** (`retarget.py`): pick by contact sheet of several retargeted candidates (cheap: one
   Blender run). Spine, clavicles and legs copy the source's rotation change from its rest; arms copy absolute
   directions (A-pose to T-pose). Aligning the clavicles too shrugged them 35° up. Options worth keeping: trim
   (`start:end`), `turn` (Mixamo magic and reaction clips stand side-on; yaw the clip so the chest faces forward),
   `float` (legs hold the floating idle's pose for a creature that never stands) and `calm` (limbs keep only part of
   their turn from rest, so hands and feet stay inside the effect). Measure hand spread and chest yaw per frame to
   choose the attack window and impact (fie1: area attack 1.1–2.5 s, hands apart at 0.65 s, impact 0.75 s).
4. **Effect textures from the restored pixels** (`make_texture.py`). Unwrap several front/back frames as cylinders
   (row by row about each row's own centre and radius; narrow crossfades keep each slot's pattern crisp), over the
   cylindrical middle of the body. Fold a 1.25-tile band into a tile that repeats in v if it is to scroll. Make the
   inner figure's pixels (the package's core mask) transparent: the 3D figure shows through there.
   - **A revolved shell shows two layers** (far inside, near outside) where the sprite shows one composite. Copying
     the sprite's alpha closed every gap and hid the figure. Keep the pattern only under a smooth, tiling random mask
     (fie1: 92 % coverage, cell-sized features), so the gaps stay open where both layers are open; raise the alpha of
     thin edges if they wash out over bright ground.
   - Use one shell. Two nested shells made four layers: a solid yellow blob.
5. **Ragged outline: radial fins.** A smooth shell gives a smooth lens outline. Cut strips of the sprite's outer
   tongues (sampled along each row from 1.0 to 1.6 × the silhouette radius) and hang them on 6–12 radial fins: a fin
   faces the camera exactly where it forms the silhouette and is edge-on in front of the body. Strips that start inside
   the silhouette carry its dense band, which near-edge-on fins draw as vertical streaks across the body.
6. **Small effects on quads in an atlas**: hand bursts on three orthogonal quads per hand (leaf bones on the hands,
   held random twists for crackle), death star, sparks and embers on three vertical quads at 60° steps. Hide by
   scaling the bone to 0.001.
7. **Rig**: Root (moves, leans about mid-body, uniform scale) above the figure's Hips and a vertical chain for the
   effect. Width on leaf bones only (non-uniform scale on a bone with children shears the chain), height changes on
   the chain's first bone as uniform scale (a per-leaf Y stretch kinks the shell). To remove the effect, scale the
   whole chain away: zero width alone left a visible line of zero-width faces. Compose each clip from the figure's
   action plus procedural keys (`build_model.py compose`), and key every channel in every clip (a Hips scale keyed
   only in Dead leaked into every other clip and its export, hiding the figure).
8. **Materials and order**: the figure opaque and unlit with its shading baked (Cycles EMIT bake of the restored core
   colours, a soft key and AO), the effect layers alpha blended, single-sided and unlit, no specular, no edge
   darkening. The engine draws opaque primitives first and blended ones in authored order, keeping each blended
   primitive's triangle order: shell inside before outside, fins after the shell, fx last; give every LOD object the
   same material slot list before joining. Scrolling layers repeat in u and v (`openyamm_uv_scroll` [0, +v] makes
   flames rise; the engine adds the scroll to the UVs); fx atlases clamp.
9. **Tiers**: recolour exactly what the sprite package recolours. fie1 changes only the figure, so only the body
   material gets a region (all of it) and ramps fitted to the package's LUT recolour of the baked body; aie1 used the
   package hue rule on the wind atlas. The LUTs index sRGB luma and the ramps linear luminance, so expect a few levels
   of fit error.
10. **LODs**: rebuild shells and fins with fewer segments; decimating blended geometry breaks its face order.
11. **Review at the sprite's scale** (`compare_sprite.sh`: restored frames above unlit EEVEE renders at the same
    canvas, front/side/three-quarter/back), then in game. Hostile flyers climb over the party outdoors, so inspect
    placed models (`model spawn <glb> x y z scale yaw`, `model play`, `model pause`, `model scrub <seconds>`; there is no
    tier switch) and check the tiers, attack and death live indoors (`actor spawn`, then `actor kill 3000`).
    In game the effect looked thinner and the figure brighter than in Blender: raise the effect's density and
    darken the figure until the sprite's balance returns.

## Review viewer hand-off (all creatures)

Before sending the user a viewer link, load it for real:
`node claude_shared/check_viewer.mjs http://127.0.0.1:8901/level_generation/creatures/<project>/review/viewer/`.
It opens the page in headless Chrome, waits for the model, switches every tier and clip, and exits 0 only when all
load with no console error. A copied viewer also needs `feedback/user_feedback.json` (`{"findings": []}`), and each
clip's manifest duration must equal the GLB clip length (whole frames at 24 fps: 0.9375 s keys as 22 frames).

## Texture grade (all creatures)

Flat or washed out next to the sprite after grading? See [native shading transfer](NATIVE_SHADING_TRANSFER.md)
(Patrol Unit: global gains failed; transferring the sprite's shading by elevation and its palettes by brightness
worked).

Meshy textures are evenly lit, while the sprites carry painted crevice shading and saturated palettes. Without a grade
the models read bland and washed out indoors. After compose, bake AO and grade:
`blender --background <authoring.blend> --python ../claude_shared/bake_creature_ao.py -- <Mesh> textures/<x>_ao_2k.png
0.04`, then `python3 ../claude_shared/grade_basecolor.py --ao textures/<x>_ao_2k.png textures/<x>_{a,b,c}_basecolor.png`
(defaults: AO 0.7 smoothed by σ 2, finest detail below σ 1.5 kept at 50%, local contrast 0.6 at σ 16, contrast 1.12,
saturation 1.25; the goblin uses local 0.4 / contrast 1.08 / saturation 1.12 because its compose already grades).
Export reads the `_graded` file (one per model, shared by all tiers). Do not sharpen at pore scale: Meshy skin pores and grainy Cycles AO
read as dark speckles in game.

## Budget

HD masters cost no Meshy credits (Codex). Smart Topology 5 + retexture 10 = **15 credits** per creature; set the budget to 30 to allow one retry.
