# MM9 Highwayman family (mm9_highwayman) — 3D actor, 2026-10-31

MM9's rogues, queue item 9: Cutpurse L8 (`MONSTERS.txt` 99, `MM9 Highwayman A`, HIGHWAYMAN1), Burglar L14 (100, `B`, HIGHWAYMAN2), Bandit L22 (101, `C`, HIGHWAYMAN3); body `HIGHWAYMAN.abc`, 32 nodes. Humanoid: built on the approved Yrsa route (MM9 skeleton, MM9 clips, grafted five-finger hands, a separate head set). Short sword in the true right fist, dagger in the true left. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_highwayman.glb` (`tools/install_model.py --world mm9`), variants `hw_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_highwayman_claude`: `scale: 100` (MONSTERS Scale 1), `yaw_offset: -1.570796327`, stride walk 1.6 / run 3.2, look `Bip01 Neck, Bip01 Head`, melee impact 0.444 s (Hattack1 `Rattack`), ranged impact 0.5 s, release socket `dagger` = `Ybasedagger` |
| Triangles LOD0/1/2/3 | 13,094 / 6,544 / 2,352 / 781. LOD0: limbs set 4,856 (hands 800 each), torso set 3,650 (skirt lining 556), head set 3,928, weapons 660 |
| Skeleton | HIGHWAYMAN.abc, 32 nodes, joints moved onto our mesh, rest frames = source frame turned by the least rotation onto our limb (`fit_hw.py`, `rerest.py`), + 15 finger bones per side + 8 hinges `Skirt_*` + 12 half-joint helpers `*_h` |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2 `Hattack2`, AttackMelee3 `Hattack3`, Fidget2, Hit2 `wince2`, Taunt, Cower, Backpedal, BackpedalRun, Death2 `die2`, LyingDown, JumpingDown |
| Textures | limbs 1792 + 1K normal + 1K ORM (A, B shared; C own), torso 2K + 1K normal per tier (normal shared A, B), head 1792 + 1K normal per tier, weapons 1024x512 procedural. 29.1 MB cooked, 21 images |
| Meshy credits | **40 / 40**: Smart Topology body 5, head 5, three 4K body paints 10 each (backup account) |

## Two findings in the source

- **The clips are split over two files.** `HIGHWAYMAN.abc` holds only 9 clips (stand, fidget2, the cower set, Hattack1, Hattack3, LyingDown, JumpingDown). Its ChildModels section names `fighterbase.abc`, which holds the other 12 (walk, run, die1, die2, wince, taunt, Rattack1...). The inventory's "9 clips" is the first file only. `merge_child.py` joins them. Same 32 nodes, same rest. The Half-Orc (`DOOKMILITIA.abc`) and `PHANTOM.abc` have the same child model.
- **MM9's bind is asymmetric:** one leg 15 cm forward, in a stride. Two consequences:
  - Bending the mesh into that stride with a transient skin would distort the hips, so our symmetric mesh stays as built and the rest frames turn to it. MM9's local rotations then give MM9's world rotations exactly.
  - `mirror_source.py` broke limb lengths on this bind (coordinator's `bone_length_audit.py`, Foot 0.29-0.53 m). See Handedness.

## Deviation: per-tier images

The rule is one shared set, region mask and colour ramps. The MM9 skins here differ in **design**: the Burglar has gold piping instead of a tan edge, buckled bracers instead of gold cuffs, and another head. The Bandit has riveted strip armour on the chest and back, a studded tunic with no quilting, tan trousers with a studded seam, red hair, a braid and an eye patch. No ramp makes those.

- **Per tier:** torso set (colour A, B, C; normal A shared with B, C own), head set (colour and normal A, B, C).
- **Shared:** limbs set by A and B; weapons by all. Bandit limbs have their own image for the trousers' studded seam (about 4.3 MB).
- **Forearms** are in the torso set so that the Burglar's bracers need no extra material.
- **Memory:** 29.1 MB cooked, against Guard 30.6 and Thrall's limbs-plus-ramps layout. Whether all variant images upload when one tier is on a map was not checked.
- **Runtime binds them per tier:** `actors.yml` skins `hw_a/b/c` select `KHR_materials_variants`; `review/ingame_sheet.png` shows the three tiers with their own costumes.

## Route (scripts/)

0. **Sources:** `convert_abc_model.py --scale 0.0256` (h1-3, fb), `merge_child.py`, then `mm9_imp_claude/scripts/mirror_glb.py` to `source/true/`. `ref_renders.py` for the masters' inputs.
1. **Masters** (Codex through `codex_slot.sh`): `references_hd/` five tier A views, `references_tiers/` four views each of B and C (same figure, repainted), `references_head/` clay sculpt `00_geometry` and seven painted views per tier on clay renders of our own head. Landscape 1536x1024: MM9's bind holds the arms 20 degrees below horizontal.
2. **Meshy:** Smart Topology 15k on the body and on the sculpt (`requests/`). Three 4K paints on one layout.
3. **Clean** (`clean_hw.py`): height scale, each central piece on its own mid-plane, figure's right half kept and mirrored, reduced per garment with the joints protected. Pieces came separate: tunic with sleeves and skirt, pants, boots, flares, yoke, belt, hands.
4. **Head** (`head_prep_hw.py`, `graft_head_hw.py`): scale 0.315, face and eyes mirrored symmetric. The hair is rebuilt as a polar grid over Meshy's shell: Meshy's hair decimated into lumps, ridges and pin holes, so the grid takes its radius per direction, low-passed, and runs under the skin at the face (the hairline is the intersection). The face is stitched to Meshy's own neck, which carries the bare V under the collar.
5. **Rest and weights:** `fit_hw.py`, `rig_hw.py` (structural bands, eight skirt hinges at the belt), `graft_hands.py` (MPFB), `helpers_hw.py`, `uv_hw.py` (never re-run), `rerest.py`, `reweight.py` (knee pivot 5 cm back, ankle helpers, relaxed bands).
6. **Paint:** `compose_hw.py` (Meshy normals flipped to glTF here, because the variants go in after `prepare_actor_glb.py`), gentle grade with saturation 0.92 and contrast 1.03 (the default 1.15 read far too orange against MM9), `project_head.py`, `finish_tex.py`.
7. **Finish** (`finish_hw.py`): fists, weapons, sleeve rims, linings (whole skirt, yoke and flare rims, sleeve ends) on a dark block in each image. `make_weapons.py` first.
8. **Clips** (`scripts/rebuild.sh`): `clips_mm9.py`, `finger_keys.py`, `arm_out.py`, `foot_clear.py`, `leg_lift.py`, `half_keys.py`, `skirt_keys.py`, `dagger_hide.py`.
9. **Runtime:** prepare, LODs, shadow fix, `tier_materials.py`, floor, winding, install, viewer. `scripts/retier.sh` from the tier step. Binding: `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <project>/scripts/bind_actors.py` from the repo root.

Rebuild after the paid steps: `scripts/rebuild.sh --install` (project folder), then `review_root.py`. `scripts/rebuild_mesh.sh` replays the mesh chain; never after the upload went to Meshy.

## Head paint fix (user, 2026-10-31)

User on tier A (`review/user_feedback_head_20261031.png`): double nose, double moustache and beard, patches on the neck. Causes and fixes in `project_head.py`, 0 credits, all three tiers:
- **Doubling:** the Codex fronts were fitted to the clay by silhouette box, but their faces sit lower and wider, so painted features missed the geometry by up to 4 cm (chin). The front view is now placed by measured landmarks per tier: eyes, nostrils, mouth, chin, eye spacing, jaw width.
- **One source per region:** all forward-facing skin, eyes, nose, mouth and beard come from the front view alone. Side and top views only fill the hair and the skin behind the cheek.
- **Neck:** one even tone from the paint's own chest, fine detail kept, faded under the jaw, so no beard or dark patch reaches it.
- **Skin flaps beside the neck:** the hair's lower lip carried neck paint. It now takes real strands from the back of the head, darkening toward the rim.

Sheet: `review/sheet_heads_fixed.png` (every tier, front, quarter, side, viewer). Left: cheeks are smoother than the front of the face (front view at grazing angles), and faint ripples show in the hair where the lip paint joins.

## Handedness

`convert_abc_model.py` leaves the figure mirrored. First attempt: `mirror_source.py`, as on the other bodies. The coordinator's audit found the legs stretching on this asymmetric bind, because that script applies the partner bone's world motion to this bone's rest. Now `mirror_glb.py` conjugates everything by S (S M S on every node and channel, names keep their meaning), and `rerest.py` puts the corrected frames on the frozen rig: mesh, weights, UVs and paints did not change.

`bone_length_audit.py`: **0 of 12 limb joints stretching** (was 4, Foot 0.29-0.53 m). `handedness.py`: raw `R Hand` x +0.691 anatomical left, source and runtime -0.69 anatomical right, sword there. The body is mirrored too, since the skins are asymmetric: patch on the left eye, braid on the left temple, as in MM9's own front view.

The fix also shrank the workarounds: run foot turn 57 -> 25 deg, walk ankle lift 13 -> 3.9 cm, knee folds in Running 21 -> 1, ankle folds 58 -> 0.

## Weapons

The outlines and stations are MM9's own vertices: sword blade 48 cm, guard 15.6 cm, grip 13 cm; dagger blade 30 cm, guard 17.5 cm, grip 13 cm. No Codex master was tried, as the brief's lesson on weapon prompts says. Procedural PBR, silver sword hilt, gold dagger hilt, as HIGHWAYMANSS and HIGHWAYMANDAGGER. In the body GLB as a fourth material, rigid on MM9's `Ybasesword` and `Ybasedagger`, so bone scale can hide the dagger. MM9 keeps them rigid to the hand in every clip (0 deg, 0 cm measured).

**Fist:** per finger on a grid round the grip, thumb over the fingers (`finish_hw.py`, from the Guard). A constant wrist turn of 12-13 deg lines the knuckles up with MM9's axis; the weapon is built turned back by it, so it points where MM9's does.

**Throw:** MM9's Rattack1 hides the dagger at 0.125 s and throws at 0.5 s. Here it hides only 0.07-0.23 s, while the fist is at the hip (the blade would run through the body), is in the raised hand until the release at 0.5 s, gone until 0.87 s. The left hand opens at the release. A deviation from MM9's event times, for a raised hand that holds something.

## Checks

Final build (viewer r13). Gate outputs: `review/gates/`. Clip gates ran on the build before the last floor smoothing change to Running (`retier.sh`), which touches only that clip's root height.

| Gate | Result |
|---|---|
| `bone_length_audit.py` | 0 stretching of 12 |
| Handedness | sword and `R Hand` anatomical right |
| `skirt_gate.py`, 48 fps, thigh vertices through the outer skirt, per clip | **Walking 0/53, Running 0/20, Backpedal 0/53, BackpedalRun 0/25**, Standing, Dead, LyingDown 0. One-shots 2-4 frames at 0.5 cm in their ease from Standing. **JumpingDown 8/44 at 13.0 cm** (script clip, no behaviour drives it) |
| `arm_hand_gate.py --outer-only --exact`, 48 fps, weapons excluded | every hand under 1 cm in every clip except Death L 1.0 cm, 1 frame. Finger stretch max 1.84 |
| `jitter_gate.py` against the untouched MM9 clips | **0 fails** |
| `grip_gate.py`, every clip, both hands | fingers inside the grip at most 0.3 cm; wrap per finger minimum 150, median 195 deg |
| `blade_gate.py`, skin only | sword: 0 over 1 cm except Fidget2 1.4 cm, 4 frames (a finger of the other hand as the blades clash). Dagger: same, Fidget2 1.4 cm, 3 frames. Death 0.8, Dead 0.8 |
| `detached_parts_audit.py` | **0 detached**, 36 components |
| `flat_shading_check.py` | 0.00 on all sets |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | limbs atlas 58.7 %, spread 1.13, stretch 1.16; torso 57.6 %, stretch 1.08; head 65.1 %, fragments 1.6 %, stretch 1.17. Torso spread is meaningless (lining on one texel) |
| `orient_gate.py`, head and feet against MM9 per frame | under 1.4 deg in the main clips at the mean; worst Death head 12.5, Death feet 9 (thinned keys and the floor pass) |
| `floor_audit.py --world mm9 --match 'MM9 Highwayman*'` | stand 0, walk -0.5..+0.8, dead 0. **Running sinks to -2.7 units, tolerance 2.5**, so the audit still flags all three bindings; tighter smoothing brings the pelvis bob back |
| `run_creature_review.py check` | 60 switches, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` | **No Highwayman failure.** PASS on 104 descriptors earlier; on the last run 113 descriptors, 1 failed, and that one is `MM9 Ghoul B` (another agent's binding: no cast clip), so the case reads FAIL |
| In game (`bootcamp.odm`, review root) | `review/ingame_sheet.png`: three tiers, hostile, fight, death, corpse |

Collapse gate, faces collapsed below 20 % of rest area or flipped, worst single frame per region, weapons excluded. `body` holds the fists' finger faces, which fold inside the curl by design. Exposed = faces any camera can see at the clip's worst frame.

| Clip | Knee | Groin | Elbow | Armpit | Ankle | Wrist | Neck/head | Body | Face-frames | Exposed |
|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 521 | 8 |
| Walking | 1 | 1 | 0 | 3 | 0 | 3 | 0 | 27 | 758 | 14 |
| Running | 1 | 1 | 0 | 4 | 0 | 0 | 3 | 17 | 236 | 15 |
| Fidget | 0 | 0 | 5 | 3 | 0 | 2 | 5 | 20 | 1805 | 16 |
| Fidget2 | 0 | 0 | 2 | 5 | 0 | 2 | 0 | 12 | 946 | 14 |
| Taunt | 0 | 0 | 9 | 3 | 0 | 3 | 4 | 14 | 626 | 18 |
| AttackMelee | 0 | 0 | 0 | 16 | 0 | 6 | 6 | 28 | 609 | 35 |
| AttackMelee2 | 0 | 0 | 6 | 10 | 0 | 8 | 22 | 19 | 489 | 15 |
| AttackMelee3 | 0 | 0 | 2 | 16 | 0 | 4 | 14 | 16 | 675 | 20 |
| AttackRanged | 0 | 0 | 12 | 25 | 0 | 5 | 3 | 16 | 622 | 13 |
| Hit | 0 | 0 | 5 | 22 | 0 | 0 | 2 | 19 | 524 | 12 |
| Hit2 | 0 | 1 | 0 | 10 | 0 | 1 | 14 | 31 | 878 | 27 |
| Cower | 1 | 0 | 9 | 13 | 0 | 1 | 14 | 39 | 3084 | 33 |
| Backpedal | 1 | 1 | 0 | 3 | 0 | 3 | 0 | 27 | 758 | 14 |
| BackpedalRun | 0 | 1 | 0 | 3 | 0 | 2 | 0 | 27 | 348 | 15 |
| LyingDown | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 521 | 8 |
| JumpingDown | 1 | 0 | 9 | 11 | 0 | 1 | 14 | 39 | 1909 | 34 |
| Death | 1 | 1 | 8 | 43 | 0 | 8 | 45 | 54 | 2807 | 24 |
| Death2 | 1 | 13 | 6 | 13 | 0 | 8 | 9 | 18 | 968 | 21 |
| Dead | 0 | 0 | 0 | 43 | 0 | 8 | 33 | 20 | 3348 | 20 |

These are real fold counts, not excused. Where the big ones are (`collapse_where.py`): Dead and Death neck/head are 1 cm² faces under the jaw with the head tipped forward, mostly hidden by the chin (1 exposed in Dead); armpit is the left upper arm's band with the arm thrown back; AttackRanged armpit is the raised throwing arm. First rig for comparison: knee 40, ankle 55, armpit 57, neck 60.

Sheets (viewer shots unless noted): `review/sheet_mm9_vs_ours.png` (MM9 is a Blender render, seven clip extremes, three tiers), `review/sheet_tiers.png`, `review/sheet_heads_fixed.png` (each tier's head after the paint fix; `sheet_heads.png` is older), `review/sheet_closeups_{a,b,c}.png` (knees, groin, armpits, elbow, neck, head in Cower, Death, Dead, Running; the last two columns of Death and Dead sit inside the body, so use the next sheet), `review/sheet_neck_mouth.png` (neck and mouth framed from above in Dead, Death, Cower, every tier), `review/sheet_hands.png` (both fists, Standing, AttackMelee, Death), `review/strips_{a,b,c}.png` (every clip, six times, two views), `review/ingame_sheet.png`.

## Deviations and open points

- **Per-tier images**: above.
- **Triangles**: 13,094 is high. 1,200 are dark linings. No reduction pass after the paint.
- **Rest pose**: not MM9's stride (see the source findings). Clip motion is unchanged by this, and `orient_gate.py` confirms it.
- **Corrections on MM9's clips**, all single smooth curves: `arm_out.py` AttackRanged L 14 deg, Cower L 14, JumpingDown L 14, Death L 9, moving the shoulder so the hand clears the hip; `foot_clear.py` Running, BackpedalRun, up to 25 deg (our foot is longer); `leg_lift.py` Walking, Backpedal, up to 3.9 cm.
- **Head**: painted by projection on our own clay, not Meshy. Neck behind the jaw is seen at grazing angles, so it has less detail than the face; unseen skin is filled from the nearest seen skin in 3D. Eye patch, headband and braid are paint, not geometry. Hair is a smooth shell with painted strands.
- **Skin relief**: the head normal comes from luminance and reads a little strong close up in the viewer's light.
- **Sleeve end**: a dark, slightly ragged edge where the wrist meets the cuff (`sheet_hands.png`), reduced by the rim relax, not gone.
- **Flare**: a thin corner of the boot flare stands off behind the knee in Dead and Running at close range.
- **Burglar's torso**: its diamond stitching reads brighter and more gold than MM9's (`sheet_tiers.png`); left as painted.
- **Bandit's trousers**: Meshy added a wavy embroidered line beside the studded seam, which MM9 does not have.
- **Viewer brightness**: the viewer's lights run brighter than the game, and tiers read lighter than MM9's dark skins.
- **Rattack1**: hide times differ from MM9 (see Weapons). Clip events `lunge`, `speakanimsound` and `playsoundFX` were not bound.
- **LyingDown** hangs in the air in the viewer: MM9 plays it on a ledge in a scripted ambush. Script clip.
- Not used: nothing of the 21 clips; all are in the GLB.
- **Not checked**: LOD1-3 and shadow meshes by eye; thrown dagger flight, its launch point and the dagger hide in game (viewer only); sounds; a map with these rows placed (the check ran in `bootcamp.odm`); the full `actors` regression suite (only the binding case); whether all variant images upload for one tier; normal-speed playback by eye; neck and mouth in Dead are partly blocked by the raised arm in `sheet_neck_mouth.png`, with no jaw to open; Android.


## Dropped MM9 clips restored (2026-10-31, run2-clips-groupB)
Nothing was dropped outright (21 source clips), but cowerstart, cower and cowerend existed only stitched in `Cower`. Added `CowerStart`, `CowerLoop` (the hold, a loop) and `CowerEnd`, bound `cower_start`, `cower_loop`, `cower_end`. Cower's arm_out (L -14 deg) is split over the phases (rises in CowerStart, held in CowerLoop, eases out in CowerEnd); `skirt_keys.py` treats CowerLoop as a loop and keeps the skirt up at the crouched ends. Joins between the phases: skirt 1.8 deg at most, body 0. Built with this project's own clip route in `scripts/extra_clips.sh` (soft joint-offset line now in `clips_mm9.py`), floored, then grafted with `claude_shared/graft_clips.py`: meshes, LODs, variants and the accepted clips are byte for byte (checked: old buffer a prefix of the new, old JSON unchanged). Numbers in `review/gates_extra/`, strip `review/gates_extra/strip_new.png` (numpy raster, untextured). Status: `devdocs/mm9_rework/overnight/status/clips_groupB.md`.

User artistic acceptance: "highwayman - good" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_highwayman_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_highwayman_reduce_claude/before/`.
