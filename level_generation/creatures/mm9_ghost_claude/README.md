# MM9 Ghost (mm9_ghost) — 3D actor, 2026-10-30

## Second pass (2026-10-31, coordinator review, 0 credits) - current

Clips, robe, hands and body paint are unchanged, except that the jacket's collar is rebuilt.

- **Jaw scrap: not paint.** Texel maps of the head (`head_map.py`) showed no dark scrap in any painting. Ray tests from the viewer's angle (`head_order_probe.py`) found it: a concave fold under the jaw and pieces of the mouth's inside lie further from the head's centre than the cheek, so the order by distance drew them over it. `finish_blend.py` now draws dark pockets first, then interior faces (a face with more head further out along its radial line) and grazing faces, then the shell. 119 of 20078 rays stay in the wrong order at that angle (0.6 %, around the lips and the jaw); the scrap is gone from the sheets but for a short thin line in close-up.
- **Collar**: Meshy's neck cone is cut on one plane (bisect keeps UVs), giving a clean rim, 8 inner flaps are deleted, and a dark bowl goes in under the rim on its own patch in free atlas space, drawn first in the body so it cannot interleave with the ruff. `collar_head_fix.py`. All tiers show the same dark opening (the mask leaves the patch alone). A few thin pale flap edges remain just inside the rim in close-up.
- **Heads against MM9: MM9 has hair**, on all three skins (`scripts/mm9_head_stats.py`, `work/mm9_hair.json`). On the texels of the back of `head1`: Shadow pale blue-white, RGB 0.72/0.77/0.77, faint strands (contrast 0.038); Apparition silver-green, 0.64/0.70/0.65, the clearest strands (0.088); Specter grey-blue, 0.49/0.58/0.58 (0.063). The low-poly render reads as bald because 256 texels blur it. So hair stays, and `head_tone.py` sets each tier's hair to the skin's mean colour and strand contrast: Shadow was much too white (0.86/0.90/0.91), Apparition's and Specter's strands too strong (gain 0.47, 0.40). MM9's back profile, measured, is close to ours (within 1 cm over most of the height), so `collar_head_fix.py` only trims the widest part to MM9's width; ours is still a fuller, rounder mass than MM9's faceted egg. MM9's skin keeps the crown paler than the sides on Apparition, ours less so.
- **Detached audit: confused, not real.** Hands and cuffs are not detached. Measured on the final build: hand to sleeve within 5.0 mm in every frame (`wrist_gate.py`), jacket to robe within 2.4 mm in every living clip. On a copy with one sliver triangle joining jacket and robe and nothing else changed (`audit_weld_test.py`, `review/gates/detached_welded.txt`) the audit flags only the head. The flags came from the unwelded waist breaking its chain to the body. Left unwelded: a weld would add a double layer at the belt or need a retopology of the jacket hem.

Monster rows Shadow L33 (`MONSTERS.txt` 138, descriptor `MM9 Ghost A`, GHOST1), Apparition L44 (139, `MM9 Ghost B`, GHOST2), Specter L55 (140, `MM9 Ghost C`, GHOST3), `GHOST.abc`, 58 joints, 12 clips, no death clip.
See-through by user decision (`devdocs/mm9_rework/PLAN.md`). Built on the approved MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)): MM9 skeleton and clips, never Mixamo. Progress and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_ghost.glb` (`tools/install_model.py --world mm9`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_ghost_claude`: `scale: 180` (100 x MONSTERS Scale 1.8), `yaw_offset: -1.570796327`, look `Xhead`, `upper_body_root: Xspine1`, stride 2.0, `run: Walking`, skins `ghost_a/b/c`, sockets `palm_left: ZfingA`, `palm_right: ZfingA01` |
| Triangles | LOD0 about 11,200 with the lining: robe 3,160, jacket and sleeves 3,245 including the bowl, hands 620 each, head 3,228 |
| Primitives | Four blended, single-sided materials on one mesh: `Ghost` (torso, robe), `GhostArmL`, `GhostArmR` (sleeve, cuff, hand), `GhostHead`. No dedicated shadow LODs (the engine refuses them on blended geometry) |
| Skeleton | 58 MM9 joints, rest rotations unchanged, translated; + 15 finger bones per side (`Finger L/R Thumb1..Pinky3`) |
| Clips (30 fps) | Standing `standair`, Walking `Flap`, Fidget `fidgetair1`, Fidget2 `fidgetair2`, Aware `awareair`, Taunt `tauntair`, AttackMelee `HattackAir1`, AttackMelee2 `HattackAir2`, AttackRanged `RAttack1`, Hit `winceAir1`, Hit2 `winceAir2`, Death (authored), Dead |
| Events | `Rattack` 0.400 s; `RangeAttack` 0.292 s, glow and release on `palm_right` (the right hand leads RAttack1, measured 7.8 m/s against 2.8) |
| Textures | body colour 2K RGBA (alpha is the see-through), normal and ORM 1K; head colour 1K per identity RGBA, normal and ORM 1K shared; region mask 1K; eye glow mask 1K |
| Meshy credits | **40 of 40** (body Smart Topology 5, head Smart Topology 5, body retexture 10, head retexture Apparition 10, head retexture Specter 10; backup account), no retries |

## Route (`scripts/`)

0. **HD masters** (Codex through `codex_slot.sh`, `references_hd/`, `references_head/{a,b,c}`), from renders of the MM9 model and the three skins. The body masters show Apparition, the richest skin. Pose = MM9's bind pose. One head shape, three paintings of it.
1. **Meshy** Smart Topology, body and head alone.
2. **Jacket** (`step1_upper.py`): scaled 1.5, cut at the belt, interior faces removed by rays (Meshy's shoulder discs and inner layers would show through), x > 0 half mirrored, lace cuffs kept.
3. **Robe** (`robe_loft.py`): Meshy's robe was two overlapping sheets. Rays from a curved axis to the outermost sheet give r(theta, s), which becomes one regular tube, 40 columns by 20 rows, rings following the hem, and a mask of where cloth exists. The tatters are alpha from that mask, not geometry.
4. **Rig** (`fit_ghost.py`, `rig_fix.py`): bones translated. Arm stretched 1.04 to MM9's shoulder-to-wrist length, so hands reach where MM9's do. Robe weights are MM9's rigid rings at higher resolution: hat functions along each of the 8 chains and between chains.
5. **Hands** (`graft_ghost.py`, `graft_ghost.json`): five-finger MPFB old-male hands, 15 bones per side. Each finger bone takes the rest frame of the MM9 mitten joint it follows: `ZfingA` / `B` / `C` by `finger_alias` (`roles_ghost.json`), palm on `Zfingbase`.
6. **Head** (`head_step.py`, `head_repair.py`): interior removed, 3,000 triangles, scaled onto MM9's head piece, rigid on `Xhead`.
7. **UVs** (`uv_ghost.py`, `uv_atlas.py`, hands 1.45x), **4K retextures**, `compose_ghost.py`, gentle grade with no AO.
8. **Repairs on the UV master** (safe, the layout stays): `sleeve_repair.py`, `head_repair.py`, `rig_fix.py`. Chain `work/uv_v1.blend` -> `sleeve_repair` `uv_v1b` -> `head_repair` `uv_v1c` -> `collar_head_fix` `uv_v1d` -> `rig_fix` `uv_v2`.
9. **Alpha** (`alpha_map.py`): torso 0.66, hands 0.78, robe 0.60 fading to 0.30, head 0.90, with the torn hem. **Tiers** (`tier_ramps.py`, `ghost_variants.py`, `head_a.py`).
10. **Runtime** (`build_runtime.sh [--install]`): export -> clips -> `ghost_death.py` -> prepare -> LODs -> variants -> eye glow -> floor -> `mirror_glb.py` -> `finish_blend.py` -> winding -> install. Viewer `viewer_update.sh <rev>`, gates `gates.sh`, sheets `sheets.sh`.

Rebuild: `TOKEN=<lease> MASTER=work/uv_v2.blend scripts/build_runtime.sh --install` from the repo root. Never re-run `uv_ghost.py`: the paid paints belong to that layout.

## How the see-through works

- **What the renderer gives** (`game/` and `engine/` untouched): a blended creature primitive writes no depth, keeps its authored triangle order, and is drawn back to front by the centre of its rest-pose bounds, after everything opaque. There is no depth prepass for it.
- **Primitive order is the trick.** The robe trails backward, so the body's rest centre lies behind the arms and head: from the front arms and head draw over the body, from behind under it, from the side the near arm last. That comes free from four primitives.
- **Triangle order** (`finish_blend.py`, on every LOD, since decimation shuffles them): robe lining, robe, jacket; hand before sleeve; on the head dark pockets, then inner faces, then the shell.
- **Robe lining**: the robe's faces again, inside-out, flipped normals, drawn first. Seen from outside the far wall's inside lies behind the near wall's outside. Seen from below only the lining faces you.
- **No hidden geometry is allowed**: under this material every internal seam shows. So: one robe tube, no inner layer; no shoulder discs; collar closed by a shallow dish; throat closed by a dark pocket; the wrist stub really is a wrist inside a sleeve.

### Limits of the renderer, recorded

- **A limb stays in its rest layer.** A limb that swings across keeps its layer (`order_gate.py`). Arms: 6-12 % of overlapping screen cells are in the wrong layer per clip, worst 42 % (Walking left arm from straight behind). Head: 50-100 % of the overlap when it flies low over the body, in Fidget2, Aware, Taunt, AttackMelee, Hit, Hit2, Death (that overlap is small and brief). It is a colour-order error between two translucent layers, not a hole: nothing vanishes. Fixing it needs per-frame primitive centres or a depth prepass for blended creatures, which is engine work.
- **Fingers against fingers** have one fixed order. Not measured.
- **No shadow.** Blended creatures cast none, and dedicated shadow LODs are refused.
- **Alpha cannot animate.** The material has no per-clip alpha, which is why Death shrinks instead of fading.
- **Mips**: at normal range the belt's knotwork averages to grey, and the see-through hides it further.

## Decisions and deviations

- **Death**: MM9's `GHOST.abc` has none, and a search of `GHOST.scr` for die, death and fade finds nothing. Ours (`ghost_death.py`, 1.75 s): the first 0.42 s of `winceAir2`, whose head and arms already fly apart, then the source slows to rest while the Scene Root turns 300 degrees, rises 34 cm and scales to 0.2 %. Dead is that speck on the floor, as the air elemental's empty corpse. In game it plays, and the loot bag drops indoors.
- **The head flies.** It is NOT a detached-parts defect: `Xhead` hangs on the scene root, and MM9's clips move it up to 49 cm off the shoulders and turn it 180 degrees; Fidget2 holds it in the hands. So no neck was built. `detached_parts_audit.py` flags it, correctly, in 443 of 465 poses.
- **Arm translations frozen** (`freeze_translation: ["Z"]`): MM9's arm joints slide up to 5.5 cm along the limb in its clips, which its rigid pieces hide and a continuous sleeve tears. Hands land up to about 5 cm from MM9's. Robe chains keep theirs.
- **Tip bones carry no skin**: MM9 turns the chain tips freely and neighbouring vertices swung round them.
- **Sleeve and cuff stay on the forearm**: MM9 turns the wrist up to 113 deg; a ring shared with the hand folds. The hand turns inside the cuff.
- **Head colour per tier breaks the shared-skin rule on purpose**: a ghost's plaster mask, an old man's face and a skull are different paintings, which a ramp cannot be; MM9 has three skins too. Body stays shared: Apparition keeps the paint with no mask, Shadow and Specter recolour four regions (cloth, ornament, linen, skin); the flat ramps of Shadow drop the brocade's contrast. Ramps are hand-set from colours read off GHOST1 and GHOST3, not fitted texel by texel.
- **Shadow's face costs no credits** (`head_a.py`): derived from the Apparition paint, wrinkles and colour flattened, sockets and mouth painted black by 3D position. It is plainer than the Codex master in `references_head/a/`, and the budget was spent.
- **Eyes glow** green and blue (gain over MM9, `emission.py`, strength 1.2, gentle pulse). Shadow has none.
- **Sleeve ends** copy paint from the forearm above, at about 570 texels/m instead of 950, with flat normals. Meshy's sleeve end was ragged and open underneath.
- **Handedness**: `mirror_glb.py` as the last geometry step. `Zhand01` (MM9's right, its `RHand1` socket) ends at x -0.16 with the actor facing +z, its true right. `review/sheet_mm9_vs_ours.png` flips MM9's renders to match.
- **Skeleton names**: the arm and jitter gates need `Bip01` names, so they read an alias copy (`gate_alias.py`). The GLB keeps MM9's names.
- **Size**: as the row says, it fills a dungeon corridor. Indoors in Verhoffin Ruins its head left the top of the frame at close range, and in those shots its side sat in the corridor wall.

## Checks (all rerun on the final build of the second pass; `review/gates/`)

| Gate | Result |
|---|---|
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.00 on arms and head; body 0.07, the planar robe grid, not flat shading |
| `texture_quality.py` body | atlas **54.4 %, 0.6 under the 55 target** (the bowl took a little of the jacket), spread 1.04, fragments 0.0 %, stretch p90 1.06 |
| `texture_quality.py` head | atlas 66.8 %, spread 1.15, fragments 2.4 % |
| `arm_hand_gate.py --exact --outer-only`, 48 fps, robe without lining, no head | **0 frames over 1 cm** in every clip. Worst: AttackRanged left hand 1.0 cm; Death forearm 2.3 cm, 1 frame while shrinking. Finger stretch p99 1.21, max 1.8. Wrist max 113 deg (MM9's Fidget2) |
| same, with the head | Fidget2 25 / 21 frames, AttackMelee 7 / 6: hands inside the floating head. MM9's gesture (it holds its head); kept, and visible |
| `jitter_gate.py` | **0 fails**, 11 clips; arm joints 0 excess over the MM9 clip |
| `wrist_gate.py`, 24 fps | hand to sleeve within 5.0 mm in every frame of every clip |
| `floor_audit.py --world mm9` | 3/3 ok, flier: hover 0.175 m, living lowest +1.6 units, dead 0 |
| `detached_parts_audit.py --fps 24` | Flags the head (by design), and both hands (65 and 55 poses): a false alarm, measured above. With jacket and robe joined only the head is flagged |
| `order_gate.py` | `review/gates/order.txt`, see the limits above |
| `mm9_actor_models_build_every_binding` | PASS, 95 descriptors on 42 models, 0 failed; `--headless-validate-actor-models` 0 refused |
| `run_creature_review.py check` | 13 clips, 3 tiers, 39 switches, 0 errors, revision `r23_20261031` |
| `run_creature_review.py playback` | every clip at 1x and 0.5x, `review/playback/*.webm`; six frames per clip at 1x sampled in `review/sheet_playback.png`. One-shots reach their end time and hold, loops wrap. The videos themselves were not watched: an agent reads frames, not motion |
| In game | `review/sheet_ingame.png`, final build: three tiers against sky, castle and hill, hostile attacks, death with loot, Verhoffin Ruins indoors. No load errors |

### Collapse gate (`scripts/collapse_gate.py`, 30 fps, faces collapsed under 20 % or flipped, all LOD0 primitives, lining counted)

| Clip | Face-frames | Worst frame by region |
|---|---|---|
| Standing | 168 of 40 frames | robe_front 20 |
| Walking | 238 of 34 | upperarm_L 5, elbow_L 2 |
| Fidget | 1,530 of 166 | robe_front 20, upperarm 6 / 5, elbow 2 / 2 |
| Fidget2 | 929 of 73 | shoulder 9 / 13, upperarm 5 / 6, elbow 5 / 5, wrist_L 1 |
| Aware, Taunt | 267 of 40 | robe_front 20, upperarm 8 / 5, shoulder_R 3, elbow 1 / 1 |
| AttackMelee | 176 of 25 | shoulder 14 / 5, upperarm_L 2, elbow 1 / 2 |
| AttackMelee2 | 80 of 28 | shoulder_L 5, fingers_L 3, upperarm 2 / 2, elbow_R 2 |
| AttackRanged | 9 of 25 | upperarm_L 3, elbow 1 / 1 |
| Hit | 2 of 31 | elbow_R 1 |
| Hit2, Death | 14 of 31 / 53 | robe_front 6, upperarm_R 2 |
| Dead | 0 | |

Not zero, and see-through hides nothing, so these are not excused. `robe_front`: 10 faces (doubled by the lining) in the last ring at the front centre tip, where neighbouring chains pinch the narrow tip; the texels of the tip's faces read alpha 0.0, so they do not draw. `shoulder`: the front armpit crease with the arm across the chest or lifted over the head. Before the weight work the waist alone was 36 and shoulders 19. Close-ups show no visible pinch (`review/sheet_closeups.png`). Full table `review/gates/collapse.txt`.

## Open points

- **Not checked**: LOD1-3 by eye up close (in-game shots at range only; `finish_blend.py` orders them); Specter's Dark Grasp and the charge glow in game; fingers overlapping in close-ups beyond the sheets; a Ghost in front of water fog or another blended effect; Android; any save with Ghosts in it.
- From the side at close range the mouth cavity shows through the cheek as a grey shape, most on Shadow (alpha 0.72). That is the see-through working, and it reads a little mottled near the upper lip.
- Dark notches on the backs of the hands in close-ups (`review/sheet_hip_speck.png`, left): dark texels in Meshy's paint, not holes. Left as painted.
- Pale lens-shaped patches beside the chest trim where the slits were filled; read as shirt.
- The arm gate must read the build without lining: on the final GLB the lining's flipped normals read every point near the robe as 6 cm inside. `hand_rest.py` chased that once and was removed.
- Monster row flags are untouched: `Transparent 1` needs no support, the material does it.
- User artistic acceptance: "if thats intended then OK" (2026-10-31): the flying head is MM9's own behaviour


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_ghost_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_ghost_reduce_claude/before/`.
