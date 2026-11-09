# MM9 Banshee (mm9_banshee) — 3D actor, 2026-10-31

## Head graft polish (2026-10-31, user feedback `review/user_feedback_head_graft_20261031.png`, 0 credits) - current

- Mouth bag: conformed to 90 % of the shell from its centre and skinned as the nearest shell vertex (`rig_fix.py`), so it travels with the jaw. `bag_gate.py` shoots all 112 bag vertices toward the throat at 8 Hz in all 14 clips: 0 miss the shell with the jaw shut, at most 4 with it wide open (Taunt, attacks, Hit2, Transition, Resurrect). I did not trace those 4 vertices individually. At those worst times the raster shows 0 bag pixels from three angles (profile both sides and from below) and the viewer shots show none (`review/zoom_bag.png`). The dark red piece below the chin is gone in every sheet.
- Neck join, shape: the grey band at the neck's base was a real crack. The loft's last row sat up to 11 mm off the torso ring and rays saw the neck's far wall from inside (`raster_ids.py`, a triangle-id raster with back faces marked). The row is now snapped to the ring and tucked 4 mm under it, last in `rig_fix.py`, rows straight between. `neck_gap_gate.py`: largest pair distance 8.3 mm over all clips, against 7 mm at rest including the tuck.
- Neck join, colour (`head_b.py`): one even colour read from the skin under the jaw, faded per texel by 3D height so no triangle edge shows. The stump around the head's ring is all neck, Meshy's crease and fringe included; hair is a whole-mass mask with a smooth edge. Tier b's stains and rust stop at the join. An interim all-round version bleached the back of the head; do not widen the fade above the ring by faces.
- Jaw fold, opening, cloak, body paint and tier ramps unchanged.
- Accepted from viewer shots read at full size: `review/sheet_graft_banshee_{a,b,c}.png` (profile and from below, Standing, AttackRanged, Taunt). AttackRanged profile is az -70: at az 90 her forearm covers the neck.
- Left: two or three dark slivers at the jaw crease, side of the jaw, seen only at a 0.28 camera distance (`review/zoom_a.png`). They are not the bag (0 bag pixels in the profile raster) and not dark paint on the head primitive; probably shading on the fold. Not chased.
- Not rerun on this build: the gates in `gates.sh` other than the two above, the frame strips, in-game captures. Only neck, stump paint and the bag changed.

## Second pass (2026-10-31, coordinator review, 0 credits)

Silhouette, cloak, hair and motion are unchanged. The first pass read well in game and was unfinished close up.

- **The head is opaque now, hair and neck stay blended.** A blended head has no depth, so its fixed triangle order drew the wrong face in concave places (`head_order_probe.py`: 0.5 % of rays in Standing az90, 3.1 % in Hit 0.2). The dark slashes on the cheek in profile and the pale shard across the cheek in Hit were this, **not paint as I had said**: the same textures with depth show neither. Opaque also fixes teeth against lips, the mouth's inner walls, and hands before the face. Cost: the head is no longer 8-19 % see-through. Hair and everything else stay blended and depth test against it.
- **Mouth** (`clips_mm9.py` `jaw_fold`, `rig_fix.py`): MM9's opening now saturates at 24 deg, A tanh(open / B) with B 45 deg, on the bind's opening of about 10, instead of 36 % of 94 = 34 deg. The cheek band widened to 48 deg and made linear, so stretch spreads over the cheek, and weights near the mouth corners narrowed in x so the lips part cleanly.
- **Neck join** (`head_b.py`, `rig_fix.py`, `build_export.py`): the saw-teeth were not colour. The strip stitching head to neck came out of the unwrap with degenerate UVs (half its triangles at UV 0,0), so tangents were undefined and the stretched strip shaded in stripes. It now maps onto a real neck face. The neck is an eleventh primitive, blended, one flat colour per tier, flat normals, alpha 1 at the head falling to 0.72 at the ring, and its colour fades into the torso's at the ring. Neck weights fade smoothly toward the jaw and skull: the old zone had a hard edge, which caused the 29 x stretch.
- **Sleeves** (`soften.py`): local contrast to a third, colour 60 % toward MM9's gold-brown on sleeves and gauntlets, half that on the bodice bands. No repaint. The belt and the last 4 cm of the cuff keep the print.
- **Hands** (`arm_bump.py`): `arm_clear.py`'s per-key correction failed the jitter gate (13 deg/frame). Fidget2 now has one smooth 5.4 deg rotation of the upper arm, eased over 0.45 s: 3.9 -> 2.9 cm, still 47 frames. It clears less than asked, and more rotation lifts the arm off MM9's gesture. Taunt 5.9 cm is **not into the body**: her right hand passes her left hand for 2 frames in MM9's gesture, 19 cm clear of the torso, so not corrected.
- **Spikes** narrower at the root, widest halfway; opaque showed their blunt ends at the cap.

Numbers before -> after, on the same gate:

| Gate | First pass | Second pass |
|---|---|---|
| Jaw opening, max | 34 deg over bind | 23.6 deg over bind |
| Jaw-blend edges of the whole head (`cheek_gate.py --all`), AttackMelee p95 / p99 worst frame / max | 5.65 / 18.9 / 29.0 | 1.77 / 3.44 / 7.15 |
| same, outer cheek only (default) | not measured | 2.05 / 5.96 / 7.15 |
| all edges, AttackRanged | 2.30 / 4.84 / 7.31 | 1.56 / 2.41 / 2.94 |
| all edges, Taunt | 2.11 / 6.71 / 9.9 | 1.49 / 2.39 / 3.87 |
| MM9's own jaw-to-head edges, for scale | HattackAir1 p95 1.66, max 1.83 (20 long edges on a black flap) | |
| Head faces drawn wrongly | 0.5-3.1 % of rays | 0, depth |
| Hair/Head, Head/Arm, Head/Torso wrong layer | 17-20 %, up to 100 % of a few cells, up to 62 % | 0, depth |
| Hand gate, Fidget2 | 3.9 cm, 44 frames | 2.9 cm, 47 frames |
| Jitter | 0 fails | 0 fails |
| Collapse, Hit neck / AttackMelee head | 36 / 32 | 36 / 28 |

**The worst cheek edge in AttackMelee is not at the mouth**: it is 1.1 cm of skin at the jaw angle stretched 7 x, where MM9 throws the head back 60 deg over a 6 cm neck. MM9 hides this with a black flap. Over the cheek itself the median is 1.17 and p95 2.05, which still exceeds MM9's 1.66-1.83, on real skin. It fails no written limit, but it is the measurable stretch that remains.

Monster rows Fright L35 (`MONSTERS.txt` 162, descriptor `MM9 Banshee A`), Dread L55 (163, `MM9 Banshee B`), Terror L65 (164, `MM9 Banshee C`), `BANSHEE.abc`, 135 joints, 13 clips, on the original MM9 skeleton with MM9's own clips.
See-through by user decision (`devdocs/mm9_rework/PLAN.md`), on the route of the translucent Ghost (`../mm9_ghost_claude/`): blended, single-sided, draw order authored per primitive.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_banshee.glb` (`tools/install_model.py --world mm9`; cooked copy in `assets_dev`), variants `banshee_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_banshee_claude`, `scripts/bind_actor.py` under the shared flock |
| Triangles | LOD0 about 15,000 with lining (12,450 before; 15k ceiling), LODs 6210 / 2224 / 743 before lining |
| Primitives | eleven, because the engine sorts a blended creature primitive by its rest centre: Banshee (torso), Skirt, ArmL, ArmR, Cape, WingL, WingR, HairL, HairR, Neck, all blended, and Head, opaque |
| Textures | Body 2K RGBA (shared by torso, arms, dress), normal and ORM 1K; Head 1K RGBA per identity (three), normal and ORM 1K shared; Cloak 1K RGBA + normal 512; Hair 512 RGBA |
| Credits | 35 of 40: body ST 5, head ST 5 + 5, body retexture 10, head retexture 10 |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_banshee_claude/review/viewer/ |

## Route

1. **Masters.** Codex HD body views (`references_hd/`) from MM9 renders with the cloak and hair spikes left out, so Meshy gets a clean figure; head busts (`references_head2/`), the second round after the first head came out with a huge cranium and a dislocated jaw from the wide scream (`references_head/`, 5 credits lost, below).
2. **Torso, sleeves** (`step1_body.py`): Meshy Smart Topology at 1.6 x, which puts hem, belt and crown on MM9's. Cut at the waist, at a neck plane leaning forward, at the wrist. Interior faces and pin holes removed, +x half mirrored. Arms re-posed 9 deg onto MM9's bind direction and length, so MM9's clips reach where they do in MM9.
3. **Dress and cloak** (`lattice.py`, `assemble.py`): MM9's dress is a 50-vertex tube and its cloth a 43-vertex envelope, every vertex rigid on a chain joint, so the joints are a lattice. Each surface is a cubic through the lattice (44 x 19, 41 x 13), folds rippled in, classic skinning on the chains (a bone owns the segment to its child; the tip bone carries nothing). The tatters are alpha (`tears.py`). The cloak uses a Codex swatch from the MM9 patch, mirrored, on its grid.
4. **Hands** (`assemble.py`): the design has three long fingers, a thumb and claws. Meshy returned five digits, so the hands are built on MM9's four chains: lofted tubes and palm joined by a voxel remesh, reduced to 516 triangles, weights along each chain by connectivity; claws are separate rigid pieces on the last moving bone. No MPFB.
5. **Head** (`step3_head.py`, `rig_fix.py`): Meshy head with separate teeth, eyes and tongue. Shell mirrored, cap drawn in to MM9's narrower skull, a strap of skin from ear to jaw and the notch under the chin smoothed. Neck lofted to the torso ring and stitched by a strip (`zip_loops`: bmesh's bridge twisted the loops into a membrane across waist and neck, which the UV layout showed before any paid job). A mouth bag (dark inner shell, upper half on Xhead, lower on Xjaw) closes the mouth, because Meshy's mouth is a hole into the hollow head.
6. **Jaw** (`clips_mm9.py`, `jaw_fold`): MM9 opens the jaw up to 94 deg with two hinges at the throat, behind a black flap. Ours has real cheeks, so Xjawpiv + Xjaw fold into one hinge at the TMJ, opening saturating at 24 deg, closing limited to 8 deg where the teeth meet. Cheeks take the stretch over a 48 deg band.
7. **Hair**: MM9's 19 spikes (8 a side, 3 on top) lofted on the centrelines read from its meshes, on its hair chains. Own swatch + ramps per tier, tips burnt as MM9's. Rooted in the cap, narrow at the root.
8. **Runtime** (`build_runtime.sh [--install]`): rig_fix -> export -> clips -> prepare -> LODs -> variants -> eye glow -> floor -> `mirror_glb.py` -> `finish_blend.py` -> winding -> install. Textures `textures.sh`, viewer `viewer_update.sh <rev>`, gates `gates.sh`, sheets `sheets.sh`. Joint-framed close-ups: `jshot.py` targets the joint's world position at that clip time.

## Rebuild (repo root)

```sh
T=<lease token>
TOKEN=$T level_generation/creatures/mm9_banshee_claude/scripts/uvjob.sh        # geometry + UVs: NEVER after the paints, they belong to work/uv_v1.blend
(cd level_generation/creatures/mm9_banshee_claude && bash scripts/textures.sh)
TOKEN=$T level_generation/creatures/mm9_banshee_claude/scripts/build_runtime.sh --install
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 level_generation/creatures/mm9_banshee_claude/scripts/bind_actor.py
python3 level_generation/projects/mm9r_common/review_root.py
```

## Deviations and decisions

- **Tiers and per-tier images.** Body, dress and sleeves are one paint (skin E's, ribs showing) with a mask + ramps: the Fright's ramp is nearly flat on the side and back panels, which is how her ribs vanish; the Dread's is warmer and duller; the Terror has no mask. Hair is a swatch with ramps. The cloak has no ramps: MM9's skins share it. **The head is the deviation: one 1K image per tier**, because a woman, a rotting skull and a clean skull are different paintings. Cost: two extra 1K RGBA images, about 2.8 MB of BC7 with mips, on one body. All three bind per descriptor (`skin: banshee_a/b/c`): regression 98 descriptors, 0 refused; `--headless-validate-actor-models` 0 refused; the three faces seen in game.
- **Skin choice.** MM9's rows all name `bansheeA.dtx`; skins B-E are a 6 fps `.spr` sequence for her undead phase. Ours has no runtime skin switch, so the decay becomes the tiers: Fright A, Dread C, Terror E. **The decay on melee is not carried over** (needs gap 3 of `MM9_VISUAL_PROPERTIES.md`, an engine addition).
- **Skull paint, free**: Codex repainted exact orthographic renders of our own head (`head_views.py`, outline IoU 0.99), projected back with known cameras (`head_project.py`). The Dread's head is derived from it (`head_b.py`): brown stain and the woman's skin in patches by 3D noise, eyes rust. Eyeballs are repainted procedurally on the skulls: black, a green iris, a pupil.
- **Eye glow** on Dread (rust) and Terror (green), `emission.py`, gentle pulse. A gain over MM9.
- **No `canFly`.** The rows have `N` in `monster_data.txt` though `Banshee.scr` includes `FlyRange.inc`, so the AI keeps her on the ground and she cannot fly over water. She hovers 18 cm in every clip. Added to `HOVERERS` in `claude_shared/floor/floor_audit.py`. Flagged for whoever owns the table.
- **Ranged attacks leave from her left hand**: MM9's `RangeAttack` socket is on `Zhand`. Melee events keep the first `Lattack` 0.269 s; MM9's `DoFX` / `redyeldots` hand sparkles are not bound.
- **Handedness**: built in raw ABC space, `mirror_glb.py` last: `Zhand01` (MM9's `RHand1`) ends at x -0.6 with the actor facing +z, her true right.
- **Death**: MM9's own, DieAir1 + Fall1 + FallDown1. Unlike the Ghost she falls to the floor and stays.
- **The head is large and sits low**, as MM9's: chin below the top of the chest, neck short and leaning forward.

## Checks (final build, `review/gates/`; first-pass output kept in `review/gates1/`)

| Gate | Result |
|---|---|
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.00 on torso, arms, head, hair; dress 0.02; cloak 0.10-0.16, the planar parts of its grid |
| `texture_quality.py` | Body atlas 57.5 %, spread 1.27, fragments 0.0 %, stretch p90 1.05. Head atlas 69.1 %, fragments 2.4 %; density p10 reads 0 because the mouth bag sits on a strip of dark texels |
| `arm_hand_gate.py --exact --outer-only`, 48 fps, whole body | Over 1 cm: **Fidget2 left 2.9 cm for 47 frames** (in her hair), **Taunt right 5.9 cm for 2 frames** (her other hand, MM9's gesture), AttackRanged 2.4 / 3.2 cm for 3 / 4 frames (head), Death 1.5 / 1.7 cm for 1 / 2 frames. Not fixed; each would cost jitter or leave the gesture |
| `jitter_gate.py` | **0 fails** on 10 clips |
| `cheek_gate.py` | Worst: AttackMelee p95 2.05, max 7.15; Death max 4.67; Taunt 3.87; Fidget 3.33; all others under 3. MM9's edges: max 1.83 |
| `floor_audit.py --world mm9 --match 'MM9 Banshee*'` | 3/3 ok, hoverer: stand +11.8..+15.0, walk +26.4..+30.6, living +1.0, dead 0 |
| `detached_parts_audit.py --fps 24` | 74 components, **0 visibly detached**, 3 only just attached (hands in the cuff by design) |
| `order_gate.py` (`review/gates/order.txt`) | Wrong layer, all clips: Torso/Arm 0.8 %, Cape/Arm 2.5 %, Wing/Torso 2-3 %, Cape/Torso 7.8 %, Skirt/Arm 9-18 %, Wing/Arm 17-20 %, Hair/Arm up to 83 % of a few cells in Fidget. Death is worst: Skirt/ArmR 82 %, Wing/Arm 36-55 %, Neck/Torso 55 %: she turns over and rest centres cannot follow. Anything against the head: 0, depth |
| `fold_gate.py` | True creases past 110 deg: WingL 21 of 456 edges (Fidget2), Skirt 21 of 2332 (Dead), Cape 4 of 445 |
| `mm9_actor_models_build_every_binding` | PASS, 107 descriptors on 46 models, 0 failed; `--headless-validate-actor-models` 0 refused |
| `run_creature_review.py check` | 42 model switches, 0 failed, no console errors |
| In game | `review/sheet_ingame.png`, `review/ingame6/`: three tiers hostile on Isle of Ashes, attack, death, final build. Outdoors only |

### Collapse gate (`scripts/collapse_gate.py`, 30 fps, faces collapsed under 20 % or flipped, all LOD0 primitives, lining counted, so cloak numbers are double)

| Clip | Face-frames | Worst frame by region |
|---|---|---|
| Standing | 1,720 of 70 | neck 11, jaw 7, head 4, fingers 3 |
| Walking | 4,263 of 28 | wing 150 / 160, upperarm_L 11, torso 8 |
| Fidget | 2,503 of 91 | neck 21, jaw 9, head 6, fingers 6 |
| Fidget2 | 7,860 of 82 | wing_L 240, neck 13, cape 10, fingers 10, torso 8 |
| Taunt | 1,279 of 34 | wing 52 / 50, neck 21, head 16, cape 12 |
| AttackMelee | 1,479 of 42 | head 28, neck 24, wing_L 18, jaw 7 |
| AttackRanged | 1,037 of 46 | wing_R 60, neck 19, head 15, jaw 8 |
| AttackRanged2 | 1,308 of 31 | wing 102 / 108, neck 19, head 7 |
| Hit | 535 of 28 | neck 36, head 13, jaw 7 |
| Hit2 | 744 of 34 | neck 11, jaw 7, cape 2 |
| Death | 10,482 of 76 | wing, cape 100, dress_left 24, hair 20, head 17 |
| Dead | 5,177 of 31 | wing_L 130, cape 18, hair 10 |

Not zero, and see-through hides nothing, so these are not excused. **Wing and cape**: the flip test compares a face with a blend of two chains' rotations, and a cloak that turns over reads as flipped; `fold_gate.py` measures real creases, 21 edges at worst, and the strips show a sheet turning, not a tear. **Neck**: the short throat compresses when MM9 throws the head back. On the opaque head a flipped face would be a hole; none was seen in the close-ups, but faces under 20 % of their area do remain at the jaw line. Arms, elbows (MM9 bends them 115 deg) and fingers stay at 1-10 faces.

## Sheets

`review/sheet_mm9_vs_ours.png` (the MM9 Death panel is a frame off: motion measured within 1 deg of MM9), `review/sheet_tier_banshee_{a,b,c}.png`, `review/sheet_head_banshee_{a,b,c}.png` (faces, mouths in attack, hit, taunt), `review/sheet_closeups_arms.png` (elbows, armpits, hands), `review/sheet_closeups_neck.png`, `review/sheet_closeups_drape.png` (dress, cloak and limbs from several angles), `review/sheet_clips_banshee_{a,b,c}_az35.png` and `review/sheet_clips_banshee_c_az160.png` (six frames of all 14 clips), `review/sheet_ingame.png`. All from viewer shots of the final build (r26). Read by the builder: MM9 vs ours, heads, neck, arms, strips of Dread; the other strips were generated on the same build and read in the first pass only.

## Unsure, and not checked

- **Still fails**: cheek and jaw-angle stretch above MM9's (max 7.15 against 1.83), hand gate items listed above, Skirt/Arm and Wing/Arm blend order 17-20 %, 82 % at worst in Death.
- The neck is plain: the skull's cracks stop at the jaw line on Dread and Terror. A choice, because any variation there stretches into stripes.
- Black curves beside the neck in head-back poses are the burnt tips of her lowest hair spikes, by shape and by `sheet_closeups_neck.png`, not measured by ray.
- The opaque head now casts a shadow while the rest of her does not. Not seen in the game shots; **not checked** under a low sun.
- **Not checked**: indoors, fog and night, LOD1-3 up close, the point-blank in-game camera, the corpse from above in game (HUD), Android, loot drop.

User artistic acceptance: "Banshee - OK" (2026-10-31), with a note that the head graft may need more polish later (`review/user_feedback_head_graft_20261031.png`: a dark red piece of the mouth shows under the jaw in profile)

## Dropped-clip pass, 2026-10-31 (run 2, 0 credits)

MM9's `Fly` has exactly `WalkAir`'s keys and length, so it is bound as `fly: Walking` (no new data). `DieAir1`, `Fall1`, `FallDown1` are already stitched into Death: every MM9 clip is carried. Numbers, strips: `review/clips_restore/`; summary `devdocs/mm9_rework/overnight/status/clips_groupA.md`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_banshee_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_banshee_reduce_claude/before/`.
