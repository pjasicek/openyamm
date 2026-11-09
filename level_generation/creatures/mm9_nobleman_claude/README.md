# MM9 Nobleman family (mm9_nobleman) — 3D actor, 2026-10-31

MM9's nobles, queue item 18: Baron L45 (`MONSTERS.txt` 153, `MM9 Nobleman A`, NOBLEMAN1), Viscount L55 (154, `B`, NOBLEMAN2), Count L65 (155, `C`, NOBLEMAN4); body `NOBLEMAN.abc`, 38 nodes, 15 clips. Humanoid by the ABC (`Bip01` biped, two finger chains per hand, six skirt bones): built on the approved Yrsa route (MM9 skeleton, MM9 clips, grafted five-finger hands, a separate head set). No held weapon: MM9's attacks are bare hands. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_nobleman.glb` (`tools/install_model.py --world mm9`), variants `nb_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_nobleman_claude`: `scale: 100` (MONSTERS Scale 1), `yaw_offset: -1.570796327`, stride walk 1.17 / run 3.6 (`stride.py`, planted foot), look `Bip01 Neck, Bip01 Head`, melee impact 0.533 s (hattack1 `Rattack`), second attack slot `attack_ranged: AttackMelee2` impact 0.8 s (hattack2 `Rattack`; both of the row's attacks are physical) |
| Triangles LOD0/1/2/3 | 10,727 / 5,361 / 1,926 / 659. LOD0: limbs set 2,869 (hands 760 each), torso set 4,106, head set 3,752 |
| Skeleton | NOBLEMAN.abc's 38 nodes, joints moved onto our mesh, rest frames = source frame turned by the least rotation onto our limb (`fit_nb.py`), + 15 finger bones per side + 12 half-joint helpers `*_h`. MM9's six skirt hinges `Bone06/14/18/02/10/22` carry the doublet skirt |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `hattack1`, AttackMelee2 `hattack2`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2, Taunt, Hit2 `wince2`, Cower `cowerstart + cower + cowerend`, Death2 `die2` |
| Textures | limbs 1792 + 1K normal + 1K ORM + 1K mask (one image, ramps), torso 2K + 1K normal per tier + shared 1K ORM, head 1792 + 1K normal per tier + flat ORM. **27.1 MB cooked, 18 images** |
| Meshy credits | **40 / 40**: Smart Topology body 5, head 5, three 4K body paints 10 each (backup account, no retries) |

## Findings in the source

- **No child model.** `ChildModels` in `NOBLEMAN.abc` lists only itself and the file holds no `.abc` name; all 15 clips are in the file. `merge_child.py` is not needed.
- **`fidget2` and `taunt` move alike** in every joint range measured: the same motion twice, as far as the numbers go.
- **MM9's bind is asymmetric** (one leg stepped forward, up to 20 deg against our symmetric rest), so `mirror_source.py` was never used: raw ABC, `mirror_glb.py`, then rest frames turned onto our limbs.
- **MM9's own thigh joints slide:** `bone_length_audit.py` on the raw conversion reads 2 of 12 stretching, thighs 10.4-11.7 and 11.7-12.9 cm. That is MM9's data, not ours. Our GLB reads 0 of 12 (`ORBIT` in `clips_mm9.py`).
- **The thighs hang from `Bip01 Spine`, and the Pelvis bone moves apart from it.** The Highwayman's rule put the leg tops on the Pelvis; here that opened an 8.6 cm gap in Death and left twice the folds in Walking. The leg tops, the thigh helpers and their keys follow the Spine (Walking face-frames 221 -> 113).
- **MM9's head steps in `die1`:** held, then a jump at 0.133 s. Our resampled curve is smooth, which is the large `orient_gate` maximum in Death (29.7 deg, mean 3.7): not a defect.

## Deviation: per-tier images

The rule is one shared set, region mask and colour ramps. Tried first, kept where it works; the MM9 skins here differ in **design**, three separate costumes: Baron burgundy brocade with a gold band and fur mantle; Viscount a blue-black fur coat, open over teal and burgundy, plain teal sleeves; Count gold brocade, an orange-red panel, tan fur edges, bosses, and a cap painted on the hair. Three men's heads as well.

- **Shared, with ramps:** limbs set (breeches, shoes, hands). Region R = the breeches. Each tier's ramp is fitted from that tier's own Meshy paint on the same layout (`tiers_nb.py`), so the tone sits with its torso.
- **Per tier:** torso set (colour and normal), head set (colour and normal). The shin bands differ per tier, so they live in the torso set, keeping the limbs set shared.
- **Memory:** 27.1 MB cooked for all tiers, against Highwayman 29.1 and Guard 30.6. Whether all variant images upload when one tier is on a map was not checked.
- Per-tier binding on LODs: every primitive of LOD0-3 goes through `KHR_materials_variants`. In game the three rows show their own costumes at distance, but LOD changes were not stepped through by eye.

## Route (scripts/)

0. **Sources:** `convert_abc_model.py --scale 0.0256` (run with `claude_shared/gltf_venv` on `PYTHONPATH`), `mm9_imp_claude/scripts/mirror_glb.py` to `source/true/`. Renders with `ref_renders.py`.
1. **Masters** (Codex through `codex_slot.sh`): `references_hd/` five tier A views, `references_tiers/` four views each of B and C (same figure, repainted), `references_head/` clay sculpt and seven painted views per tier on clay renders of our own head. Portrait 1024x1536: the arms hang 20 degrees from vertical.
2. **Meshy:** Smart Topology 15k on the body and on the sculpt (`requests/`). Three 4K paints on one layout.
3. **Clean** (`clean_nb.py`): height scale, each central piece on its own mid-plane, right half kept and mirrored, decimated by connected garment (doublet with skirt and belt as one, legs with shoes as one), and only then split into parts by geometry: splitting first left the belt a loose strip with flipped normals. The placket had holes, folds and pits under the dropped brooches, so the band is rebuilt as a constrained Delaunay patch on a fitted chest surface.
4. **Head** (`head_prep_nb.py`, `graft_nb.py`): scale 0.30. Meshy fused face and hair into one shell, so one skin part. Right half mirrored at full resolution, then Blender's symmetric decimate: decimating half and mirroring tore the seam. The closed neck base is stretched down and out under the collar.
5. **Rest and weights:** `fit_nb.py`, `rig_nb.py`, `graft_hands.py` (MPFB, `graft_nb.json`), `helpers_nb.py` (`step_b.sh` runs them). Pivots: knee 5 cm back, elbow 1.5 cm back, hip 2.5 cm forward. The body's standing collar is Meshy's own.
6. **UVs** `uv_nb.py`: **never re-run**, the paints belong to `work/uv_v1.blend`. The rig chain is deterministic, so `carry_uv.py` copies the UVs onto any re-rig after checking positions and loops match (max move 0.0, 0 loops differ). Rig changes after the paint are therefore free.
7. **Paint:** `scripts/textures.sh`: `compose_nb.py`, the gentle grade (saturation 0.92, contrast 1.03), `tone_nb.py`, `finish_tex.py`. Heads: `project_head.py` from the Codex views. `tiers_nb.py` for the ramps.
8. **Runtime:** `scripts/iter.sh [--install]` re-rigs, then `scripts/rebuild.sh`: `finish_nb.py`, `export_nb.py`, `clips_mm9.py`, `arm_const.py`, `half_keys.py`, `skirt_keys.py`, `arm_bump.py`, prepare, LODs, shadow fix, `region_variants.py`, `tier_images.py`, floor, winding, viewer. Binding: `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <project>/scripts/bind_actors.py` from the repo root.

## Handedness

`mirror_glb.py` on the raw conversion, nothing else. `handedness.py`: raw `R Hand` x +0.326 anatomical left; source -0.326 and runtime -0.375 anatomical right. No weapon to check.

## Cloth

MM9's six hinges stay, moved onto our ring, rest rotations kept. `skirt_keys.py` keeps MM9's cloth rotation and adds the least swing that clears the legs, measured in each hinge's own frame, on running-maximum plus Gaussian curves on the clip's keys, never per frame. Hinges stay rigid on the Spine, which carries the belt, in place of MM9's offsets for its nearer pivot. MM9's own skirt hangs still in `walk` and `fidget1`.

The legs' hidden top runs up inside the belt on the Spine (`finish_nb.py`): they only touched the skirt, which swings away, so the detached audit saw them part by 1.4 cm in Hit2.

## Checks

Final build r16. Gates ran on r11; later builds differ from it only in images (tier C torso colour, then the head colour and normal of every tier), so mesh, weights and clips are the same. Winding, validator and binding regression ran on r16, the viewer check on r13. Outputs: `review/gates/`.

| Gate | Result |
|---|---|
| `skirt_gate.py`, 48 fps, leg vertices through the outer skirt, per clip | **0 frames in all 14 clips**, Walking 0/66, Running 0/49. The gate is live: with my keys off, Walking reads 31/66 at 0.3 cm. The doublet flares clear of the thighs, so the margin is small work, not a large correction |
| `arm_hand_gate.py --outer-only --exact`, 48 fps | every clip 0 frames over 1 cm except **Hit2 R 3.7 cm, 21 frames, forearm 2.9** and Fidget R 1.6 cm, 13 frames (see below) |
| Finger stretch | p99 at most 1.58, max 3.52 on one 4.9 mm edge at the thumb root at full curl in Fidget |
| `jitter_gate.py` against the untouched MM9 clips | **3 flags**: AttackMelee2 R skin 3.8 mm/f2 (of 171), Death R skin 2.15 mm/f2 (of 190), Hit2 R upper arm 1.48 deg/f. See below |
| `bone_length_audit.py` | **0 stretching of 12** |
| `detached_parts_audit.py` (24 fps) | **0 detached**, 8 components |
| `flat_shading_check.py` | 0.00 on all sets |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | limbs atlas 57.0 %, spread 1.25, stretch 1.09; torso 56.4 %, spread 1.07, stretch 1.09; head 56.7 %, spread 1.1, fragments 0.1 %, stretch 1.12 |
| `orient_gate.py`, head and feet against MM9 | head mean under 2 deg except Death 3.7 (MM9's stepped head, above), feet up vector mean under 1 deg. Foot forward reads a constant 13.4 / 3.4 deg: that is the rest turn itself, not motion |
| `floor_audit.py --world mm9 --match 'MM9 Nobleman*'` | **ok, 0 problems**: stand 0, walk -1.1..+1.3, living -1.1, dead 0 (r11) |
| `--headless-validate-actor-models` | 131 descriptors on 54 models, 0 refused |
| Regression `mm9_actor_models_build_every_binding` | **PASS**, 131 descriptors, 0 failed |
| `run_creature_review.py check` | 42 switches, 0 failed (r5) |
| In game (`bootcamp.odm`, review root, r11, before the image-only change) | `review/ingame_sheet.png`: three tiers with row names, hostile attack, death |

Collapse gate, faces below 20 % of rest area or flipped, worst single frame per region, all LOD0 primitives (`scripts/collapse_gate.py`, from `mm9_evilsorcerer_claude`). Skirt = faces on MM9's hinge bones. Seen = faces any camera can see at the clip's worst frame.

| Clip | face-frames | knee L/R | hip L/R | groin | ankle L/R | elbow L/R | shoulder L/R | wrist L/R | torso | neck | head | skirt | finger | seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0/0 | 0/0 | 0 | 0/0 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Walking | 113 | 0/0 | 0/0 | 2 | 0/0 | 1/0 | 0/0 | 0/0 | 0 | 0 | 3 | 2 | 0 | 3 |
| Running | 411 | 0/0 | 0/0 | 6 | 0/0 | 3/0 | 1/1 | 1/0 | 0 | 0 | 0 | 14 | 0 | 16 |
| Fidget | 1185 | 0/0 | 0/0 | 0 | 0/0 | 5/1 | 11/20 | 5/3 | 6 | 0 | 0 | 0 | 3 | 29 |
| Fidget2 | 1855 | 0/0 | 0/0 | 6 | 0/0 | 11/12 | 1/1 | 0/3 | 1 | 0 | 0 | 6 | 0 | 19 |
| Taunt | 1855 | 0/0 | 0/0 | 6 | 0/0 | 11/12 | 1/1 | 0/3 | 1 | 0 | 0 | 6 | 0 | 19 |
| AttackMelee | 965 | 0/0 | 0/0 | 25 | 0/0 | 0/12 | 16/33 | 0/0 | 2 | 13 | 11 | 8 | 1 | 48 |
| AttackMelee2 | 1180 | 2/0 | 0/0 | 29 | 0/0 | 3/9 | 16/29 | 0/0 | 10 | 0 | 1 | 12 | 1 | 57 |
| Hit | 260 | 0/0 | 0/0 | 0 | 0/0 | 3/1 | 2/7 | 0/2 | 2 | 1 | 3 | 10 | 0 | 15 |
| Hit2 | 894 | 0/0 | 0/2 | 4 | 0/0 | 3/6 | 5/5 | 0/5 | 4 | 0 | 1 | 16 | 1 | 29 |
| Cower | 6643 | 0/0 | 0/0 | 27 | 0/0 | 9/9 | 38/23 | 5/0 | 16 | 0 | 5 | 8 | 1 | 106 |
| Death | 707 | 0/0 | 0/0 | 6 | 0/0 | 3/1 | 22/38 | 0/4 | 3 | 2 | 14 | 15 | 1 | 76 |
| Death2 | 4448 | 0/0 | 0/0 | 11 | 0/0 | 2/2 | 52/76 | 0/3 | 6 | 3 | 6 | 12 | 1 | 66 |
| Dead | 496 | 0/0 | 0/0 | 6 | 0/0 | 0/1 | 0/0 | 0/1 | 0 | 2 | 6 | 0 | 0 | 5 |

First rig for comparison: Standing 1,408 face-frames (hip 15, groin 15), Walking 1,874, Death2 9,520 with shoulders 127/125.

These are real counts, not excused. Knees at most 2, hips at most 2, ankles 0. **Shoulders are the open joint:** with the arm raised the flank and the sleeve cap fold where they meet (76 in Death2, 38 in Death, 33 in AttackMelee), most of them visible to some camera, and the brocade stretches under the arm in the raised poses. Cower's total is high because it holds its worst pose for 1.4 s. **Groin went up in the two attacks** when the leg tops moved to the Spine (15 -> 25, 13 -> 29), while Walking, Hit and Standing went down; those faces are under the skirt from most angles.

## Not zero, with why (second attempts done)

- **Fidget R 1.6 cm is not a body contact.** The wrists come together 11 cm apart in front of the chest, about 45 cm from the torso: MM9's hands-together gesture, and the gate counts the other arm as body. A bump on it made it worse (2.0 cm), so it was removed and MM9's motion restored.
- **Hit2 R 3.7 cm, 21 frames:** MM9's `wince2` brings the right hand in low against the body, 9.2 cm into our fuller doublet. `arm_bump.py` took it to 3.7 at its 27 deg limit and that bump carries the 1.48 deg/f jitter flag. A longer ramp hardly changed either (3.7 cm, 1.39 deg/f). A script clip: nothing here shows what plays it.
- **Jitter AttackMelee2 and Death, skin:** both come from the constant 3.5 deg shoulder offset (`arm_const.py`) that takes the right hand out of the skirt in Standing (2.2 cm, every frame, without it). A constant cannot jiggle: it scales the peak of a very fast swing by 1-2 %. At 2.5 deg, AttackMelee fails instead and AttackMelee2 still fails (2.96), because the bump grows. Kept at 3.5.

## Head fix, user feedback 2026-10-31 (r16, 0 credits)

The user: "count - double nose, also viscount, partly baron" (`review/user_feedback_nose_20261031.png`), with the beard running on below the jaw. Cause: `project_head.py` fitted each Codex view to the clay by silhouette box, and the paints keep neither the clay's proportions nor its features. The chin sat 23 / 70 / 50 px off in the front view (A, B, C; 0.4 mm per px), so the painted nose landed under the real one. The z-buffer does not help: this is paint against mesh, the same fault as the Gezzampt.

- **Front view placed by landmarks** measured on clay and paint (eyes, nose wings and base, mouth corners and centre, chin, jaw sides, neck): a thin-plate warp of the box error, zero at the hairline and in the hair. The Viscount's mouth corners sit wider on the clay, because his smile is wider than the closed mesh mouth.
- **One source per feature:** the whole face, out to the jaw, comes from the front view alone.
- **Beard ends at the jaw edge:** below it, plain neck skin from the paint's own neck, darker just under the jaw, inside the neck tube only.
- Side views keep the box fit; only hair and the area behind the jaw come from them.
- Head normals rebuilt from the new paint, so the old nostrils are gone from the relief too.

Accepted from viewer shots at full size, every tier, front, quarter, side, below: `review/sheet_heads_full.png`.

## Deviations and open points

- **Per-tier images**: above.
- **Tone:** texels match MM9's by region (Count's doublet 102/66/14 against MM9 89/60/16). The viewer's light runs brighter than the game, so tiers read lighter than MM9's Blender renders. The Baron's red stays more saturated than MM9's browner burgundy after `tone_nb.py`.
- **Fur and brocade:** Meshy returned hard flecks (the Viscount's coat read as black-and-white scales). `tone_nb.py` cuts local contrast on those regions and normals are scaled down. Fur still reads a little combed up close, MM9's is softer.
- **Mouths:** MM9 has no jaw bone and no clip opens the mouth. The hole left by Meshy's teeth is plugged dark; the Viscount's smile is paint on the clay's closed lips.
- **Count's cap:** paint on the same hair shell, as in MM9. No separate hat, so no layered projection: `project_head.py` is per-view with a z-buffer on the one head skin. Checked per the Guard lesson at full size, every tier, front, quarter, side and below (`review/sheet_heads_full.png`): no feature landed on the wrong surface. The collar and mantle are body paint, not projected.
- **Count's chest boss:** a small dark mark at its top, Meshy's paint where the dropped pendant was, and a faint seam where the rebuilt placket meets the old surface. Two repairs (closing, inpaint) did more harm than the mark and were removed, so it stays.
- **Hair edge:** a thin pale line where the hair shell meets the cheek, seen from the side.
- **Face, small marks:** a crease mark in the middle of the forehead (mesh) and a small dark nick at each jaw corner.
- **Hands:** MPFB, with MM9's curl through `finger_alias`. A pale net pattern reads on the back of the hands up close.
- **Mantle:** weights relaxed to move as one stiff cape, half its corners on the arm. It lifts with a high arm, so the arm does not cut it.
- **Rest pose:** not MM9's stride. Clip motion is unchanged, `orient_gate.py` confirms it.
- **Shoes** are longer and more pointed than MM9's.
- **Corrections on MM9's clips**, all single smooth curves: `arm_const.py` R 3.5 deg all clips; `arm_bump.py` Fidget2 L and Taunt L 9 deg, AttackMelee R 6 deg, Hit2 R 27 deg.
- **Second attack:** the engine requires an `attack_ranged` clip, so `hattack2` fills it. My first binding left it out and was refused, which briefly turned the shared regression red; fixed at 08:25.
- Events `lunge`, `speakanimsound`, `playsoundFX`, `playanimsound`: not bound. Sounds not wired.
- Rows at MM9's size. Health bar position against the row's sprite height: not measured.

## Sheets (viewer shots unless noted)

`review/sheet_mm9_vs_ours.png` (MM9 is a Blender render with its own light), `review/sheet_tiers.png`, `review/sheet_heads.png` (each tier from five sides), `review/sheet_heads_full.png` (r16, full size, front, quarter, side, below), `review/sheet_closeups_{a,b,c}.png` (knees, groin, armpits, elbow, neck, mouth in Cower, Death, Dead, Running, cameras fixed to the chest so a lying corpse is framed from the same side), `review/sheet_hands.png`, `review/strips_{a,b,c}.png` (every clip, six times, two views), `review/ingame_sheet.png`. Numbers: `review/gates/`, first rig `review/gates0/`.

## Not checked

LOD1-3 and shadow meshes by eye; a map with these rows placed (the check ran in `bootcamp.odm`); indoor light, fog, night; whether all variant images upload for one tier; motion at normal speed by eye (`review/playback/` holds 28 recordings of tier A, normal and half speed, not watched: I read strips and gates); the corpse in game is partly behind the portrait in the capture, and its Dead pose was checked in the viewer; melee contact timing and footsteps; sounds; Android cook.


## Dropped MM9 clips restored (2026-10-31, run2-clips-groupB)
Nothing was dropped outright (15 source clips), but cowerstart, cower and cowerend existed only stitched in `Cower`. Added `CowerStart`, `CowerLoop` (loop) and `CowerEnd`, bound `cower_start`, `cower_loop`, `cower_end`; arm_const, half keys, skirt keys (CowerLoop a loop, skirt kept at the crouched ends). Joins: skirt 0.8 deg at most, body 0. Built with this project's own clip route in `scripts/extra_clips.sh` (soft joint-offset line now in `clips_mm9.py`), floored, then grafted with `claude_shared/graft_clips.py`: meshes, LODs, variants and the accepted clips are byte for byte (checked: old buffer a prefix of the new, old JSON unchanged). Numbers in `review/gates_extra/`, strip `review/gates_extra/strip_new.png` (numpy raster, untextured). Status: `devdocs/mm9_rework/overnight/status/clips_groupB.md`.

User artistic acceptance: "nobleman - good" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_nobleman_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_nobleman_reduce_claude/before/`.
