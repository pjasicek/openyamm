# MM9 Gezzampt body (mm9_gezzampt) — 3D actor, 2026-10-31

MM9 `GEZZAMPT.abc` (27 joints, 16 clips, 554 triangles): rows 171 Gezzamptling L15 (`MM9 Gezzampt A`, GEZZAMPT), 172 Gezzampt L20 (`B`, GEZZAMPT2), 173 Gezzampt Elder L28 (`C`, GEZZAMPT3).
**Humanoid route** (MM9 skeleton, MM9 clips, closed fists, head-only Meshy model): a biped with arms and a face, on `HorseLink` goat legs with hooves. Progress and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_gezzampt.glb` (`tools/install_model.py --world mm9`), variants `gezz_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Gezzampt A/B/C`, scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.4 / run 2.8 (planted foot), melee impact 0.389 s (`Rattack` in Hattack1/2), ranged impact 0.389 s released at `cast_hand` = `Bip01 R Hand` (MM9's RangeAttack socket, node 17), look `Bip01 Neck, Head`, upper body `Bip01 Spine2` |
| Triangles LOD0/1/2/3 | 10,152 / 5,076 / 1,826 / 605; LOD0: body and arms about 4,600, fists about 950 each, head with mane, ears and horns about 3,100, teeth 700, eyes 160 |
| Skeleton | 43 joints: MM9's 27, names and rest rotations unchanged, joints translated + 16 half-rotation helpers (`*_h`). `Finger0` keeps its clips and drives nothing (see Hands) |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2 `Hattack2`, Fidget2, Taunt, Aware `aware`, Hit2 `wince2`, Death2 `die2`. `Backpedal` and `BackpedalRun` not built: nothing in the binding plays them |
| Textures | one shared set: body 2K colour + 1K normal + 1K ORM + 1K mask, head 2K colour + 1K normal + flat ORM + 1K mask. **Cooked 11.6 MB for all three tiers**, 8 images, no per-tier image |
| Meshy credits | **20 / 40**: body Smart Topology 5, head-only Smart Topology 5, body retexture 10 (backup account, no retries) |

## Head fix, r12 (user review, 2026-10-31)
The user saw four eyes and double teeth (`review/user_feedback_head_20261031.png`). Cause: `project_head.py` fitted each paint to the clay by silhouette box, and Codex had run the beard below the clay in the front view (paint bottom 0.888 against clay 0.860 of the image). That scaled the front paint and moved every painted feature about 4 cm above the real eyes and teeth, which `eyes.py` then painted again.
Fix: one source per feature. The front view is now placed by measured landmarks, no scale, 1.65 % of the image up (irises and teeth agree), so painted lids, brows and lips land on the real eyes and mouth. 0 credits; mesh, UVs, rig, clips and gates' geometry are unchanged. Accepted from viewer shots read at full size: every tier's head, front, quarter and side (`review/sheet_head_r12.png`). `sheet_mouth_neck.png`, `sheet_closeups_*`, `sheet_strips_*` and `mm9_vs_ours_*` are r10-r11 and still show the old head paint.

## Tiers
MM9's three skins are one layout in three colours (the Elder's horns and nails are red, its hooves blue), so this body takes the plain rule: one shared set + region mask + ramps. Regions: hide, and horn (head) or hoof (body); eyes, teeth and tusks are in no region. `tier_ramps.py` takes each tier's colours from its own MM9 skin, by the same quantile of luminance, at 1.3 x MM9's baked values (Elder's hide 1.12, hoof 0.8).

## Route (`scripts/`)
0. **Sources**: `convert_abc_model.py --scale 0.0256` in raw ABC space, `mirror_glb.py` last (`source/true/`). `bone_length_audit.py` on the raw source: 2 of 12 over 10 %, both MM9's own: the thigh joints slide 2.8 cm against the pelvis (14 %). `roles_gezz.json` `no_translate` holds them: 0 on the GLB.
1. **Masters** (Codex): `references_hd/` five views of tier A from flat-lit MM9 renders, `references_head/00_geometry.png` a clay sculpt of the head with one solid mane.
2. **Meshy**: body Smart Topology gave a clean closed figure with good hooves and a poor fist. Head-only gave a very good face with layered, torn shells round the lips, nose and mane.
3. **`head_prep.py`**: tears filled, left half mirrored. **`fit_gezz.py`**: left half mirrored, each limb onto its MM9 bone. Knee and hock sit 70 % of the way from MM9's joints to ours: MM9's short flat calf squashed our thick leg into a shelf. Arms, hip, Foot joint and shoulders match MM9 within about 2 cm with no change.
4. **`graft_gezz.py` + `wrap_voxel.py` + `wrap_finish.py`**: the whole figure rasterised at 4 mm, closed, flooded from outside, eroded back, remeshed, each vertex projected back on the assembled surface. One closed skin, head and body joined, no torn shells; teeth and eyes stay separate pieces. Mouth and sockets are carved open against a dark plug behind them.
5. **`rig_gezz.py`** bone heat, then head rigid over a neck band, hooves on Foot, ears on `Ponytail1/2` (MM9's ear bones), **`step_b.sh`** posed MPFB fists, wrist zipped. **`weights_fix.py`**, **`helpers_gezz.py`**, **`reduce_gezz.py`**, **`quick.sh`**. Gates ran on this first rig.
6. **UVs** `uv_gezz.py`: two sets. Never re-run: the paint belongs to `work/uv_v1.blend`. `reweight.py` and `move_joints.py` (`pivots_final.json`) act on the frozen mesh.
7. **Paint**: one Meshy retexture at 4K. Head: `head_clay.py` renders our head, Codex paints seven views on it, `project_head.py` projects them (front view by landmarks since r12, the others by silhouette box). `eyes.py` paints eyes and teeth from their 3D position and puts fur grain in texels no view saw. `seam_fix.py` brings the head's neck band to the body's tone.
8. **Runtime** `textures_all.sh`, then `REV=<rev> scripts/rebuild.sh --install` (project folder; `work/token` holds the lease token, claim a new one first). `SKIP_EXPORT=1` skips the Blender export. `bind_actors.py` writes the binding under the flock.

## Checks (final GLB r12; regression on r12, floors from r11, the other gates on r9, same mesh, weights and arm keys)

| Gate | Result |
|---|---|
| Cloth | **Not applicable: the body has no cloth, skirt or strip.** Nothing was measured for Walking and Running |
| Arm and hand, skin (`NOCLOTH=1 arm_hand_gate.py --outer-only --exact`) | **0.0 cm, 0 frames over 1 cm, in all 15 clips.** First rig: Hit2 L 6.0 cm, Fidget R 3.7, Fidget2 L 3.6 with the larger fists. `arm_bump.py` Fidget R (3 deg) and Hit2 L (12 deg); Fidget2 L cleared with the pivots. Fist stretch max 1.50 |
| `jitter_gate.py` against the untouched clips | **0 fails** |
| `bone_length_audit.py` | 12 checked, **0 stretching** |
| Head and hoof orientation against MM9 (`orient_gate.py`) | Head mean under 3.1 deg, max 13.6 (Fidget2). Feet mean under 2.4 deg, max 10.1, except Running: mean 7.6, max 36.9. That one is a time offset: 0.35 s sampled into 11 frames is 0.333 s, about 5 % fast, on a very fast foot |
| Handedness | Raw ABC: bone named R on the anatomical left. Source and runtime: on the anatomical right. Lightning leaves the right hand in game |
| `detached_parts_audit.py` (24 fps) | 19 components, **0 detached** |
| `flat_shading_check.py` | 0.00 body, head |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` | body atlas 61.3 %, spread 1.18, fragments 0.0 %; head 60.0 %, spread 1.77 (face denser by design), fragments 0.0 % |
| `floor_audit.py --world mm9` | 3 ok: stand 0, walk 0, living -0.1, dead 0. r10 had the walk lifting every foot 3.7 units: Walking now `--ground-loop` |
| Regression `mm9_actor_models_build_every_binding` | PASS on r12: 140 descriptors on 57 models, 0 failed |
| `run_creature_review.py check` | 0 failed |
| In game (`bootcamp.odm`, review root, isolated) | `review/ingame_sheet.png` r11: three tiers walk and attack, Elder casts |

**Collapse, worst single frame per clip and region** (`review/gates/collapse.txt`, `collapse.json`, gate from `mm9_evilsorcerer_claude`, all LOD0 primitives, regions extended to hock, ear and our `_h` bones, 30 fps). Seen = faces any camera can see at the clip's worst frame.

| Clip | face-frames | knee L/R | hip L/R | hock L/R | ankle L/R | shoulder L/R | elbow L/R | wrist L/R | torso | head | ear | seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 66 | 0/0 | 1/0 | 0/0 | 0/0 | 0/0 | 0/0 | 1/0 | 0 | 0 | 0 | 2 |
| Walking | 353 | 2/4 | 1/0 | 0/1 | 6/5 | 0/2 | 2/0 | 3/1 | 0 | 8 | 5 | 22 |
| Running | 143 | 2/2 | 1/1 | 4/3 | 5/6 | 1/5 | 1/0 | 1/0 | 0 | 4 | 3 | 19 |
| Fidget | 989 | 0/0 | 1/0 | 0/0 | 0/0 | 5/12 | 10/6 | 2/0 | 0 | 18 | 4 | 23 |
| Fidget2 | 1503 | 0/0 | 2/0 | 0/0 | 0/0 | 21/14 | 3/0 | 1/0 | 2 | 34 | 6 | 31 |
| Taunt, Aware | 289 | 2/2 | 3/0 | 0/0 | 0/0 | 3/7 | 2/0 | 1/2 | 4 | 11 | 4 | 22 |
| AttackMelee | 417 | 2/0 | 1/0 | 0/0 | 0/0 | 18/9 | 0/0 | 1/0 | 5 | 32 | 6 | 21 |
| AttackMelee2, AttackRanged | 270 | 0/0 | 2/0 | 0/0 | 0/0 | 2/9 | 3/4 | 1/0 | 3 | 18 | 3 | 30 |
| Hit | 218 | 0/0 | 1/0 | 0/0 | 0/0 | 8/7 | 0/1 | 1/1 | 1 | 7 | 0 | 16 |
| Hit2 | 148 | 1/0 | 2/0 | 0/0 | 0/0 | 3/4 | 2/0 | 1/0 | 3 | 14 | 0 | 10 |
| Death | 320 | 1/3 | 1/1 | 3/0 | 5/1 | 5/7 | 1/1 | 2/1 | 5 | 6 | 0 | 26 |
| Death2 | 1682 | 2/2 | 2/0 | 1/4 | 3/7 | 18/14 | 2/0 | 3/0 | 11 | 93 | 6 | 32 |
| Dead | 93 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 1/0 | 1/0 | 0 | 1 | 0 | 3 |

First rig: Death2 2,081 face-frames, head 86, shoulder 25; Fidget2 3,335; Walking knee 10/8, hock 7/9; Death ankle 10; elbows 9 in every clip including Standing (a weight step at the wrist). Knee and fetlock pivots moved behind the bend took knees from 10 to 2-4 and Death ankle from 10 to 5.
**Not zero.** Head faces are the back of the neck under the mane, and the throat under the jaw when the head goes back or down. Moving the head and neck pivots back cut AttackMelee's head folds from 43 to 32 and the seen ones from 30 to 12, and raised Death2 (a script clip) from 59 to 93, with the seen ones down from 20 to 10. Shoulders are the creases at the clavicle: MM9 hangs the clavicles on the Neck bone, so a neck turn pulls the shoulders. The close-ups of these poses read clean; the cat lesson says that is not proof.

Sheets (viewer shots, `review/`): `mm9_vs_ours_tiers.png` (MM9 and ours, every tier, front, back, quarter; MM9 is a Blender render with flat light; our crops cut the head, faces are in the next sheet), `mm9_vs_ours_clips.png` (eight clip moments), `sheet_mouth_neck.png` (mouth and throat in five poses, three tiers, camera riding the head), `sheet_closeups_a.png`, `_b`, `_c` (knees, groin, armpits, elbow, neck in crouch `AttackMelee`, `Death`, `Dead`, framed on the joint), `sheet_strips_a_1.png`, `_2`, same for `b` and `c` (15 clips, six frames each), `ingame_sheet.png`. Playback `review/playback/`. Numbers `review/gates/`.

## Decisions and deviations
- **Hands**: MM9's hand is a closed mitten fist, its `Finger0` constant in every clip but one small move in Hit, and the clips never open it. So: real five-finger fists (posed MPFB, thumb solved across the fingers), rigid on `Bip01 Hand`, no finger bones. The 15 bones of the default route would carry no motion. Meshy's fist had a thumb like a sausage. Fists are 20 % longer than the first graft, to match MM9's size.
- **Wrap**: not in the reference route. Head and body are one closed skin, so the neck has no bridge or zipped ring. It softens the surface a little, and the mane is fused to the back of the neck.
- **Leg proportions**: thigh 0.456 m, calf 0.278, shank 0.302 (MM9 0.478, 0.257, 0.352). Pelvis lowered 3 cm in every clip (`root_lift`) to keep the soles on the floor.
- **Pivots** (`pivots_final.json`): knee and fetlock 3-3.5 cm back, head and neck 4-6 cm back, upper arm 3 cm down. Rest rotations stay MM9's.
- **Ears** ride `Ponytail1/2`: MM9's ears are small flaps on those bones, and they twitch in fidgets.
- **Mouth**: MM9 has no jaw bone, so it stays closed: teeth and tusks are separate pieces, 25 % larger and 6 mm forward of the wrap's gums, in front of a dark plug.
- **Tone**: lighter than MM9's dark skins, the user's accepted direction. MM9 tier A bright fur sRGB (112, 72, 28), ours about 1.3 x that. The Elder was far too bright at 1.3 and is 1.12.
- **Sizes**: all tiers at MM9's size, 256 units. Rows keep their sprite heights 300, 350, 450, so the health bar floats above B and C.
- **Death**: MM9's `Velocity` events in die1 and die2 move the actor in MM9. They are not carried over; the corpse stays near the actor.

## Open points
- Collapse is not zero, numbers above. Death2 head 93 is the worst; it is a script clip, not traced to any behaviour.
- Forearm near the wrist: the fur grain is finer than on the rest of the arm (UV density 1.5x for the fists), visible at about 40 cm in `sheet_closeups_a` `cade5`.
- Fists are smooth on the palm side, against the thigh most of the time; finger ends sink into the palm.
- Under the nose: a small flat patch and nostril slits, from below only.
- Horn paint is blotchy at close range on tier A.

## Not checked
- Maps that place Gezzampts: the in-game check was `bootcamp.odm`. Indoor light, fog and night not seen.
- Motion at normal speed by eye: `review/playback/` holds 30 clip recordings that I did not watch; I read strips, gates and six in-game frames.
- Melee contact moment and footsteps; sounds. The lightning release was seen in one frame only.
- `Aware`, `Fidget2`, `Taunt`, `Hit2`, `Death2`: which behaviour plays them (`baserange.scr` not traced).
- LOD1-3 and shadow meshes by eye.
- Jitter, collapse, arm and orientation gates not repeated on r11, whose clips differ only by the Walking floor pass and whose images differ only in tier C's ramps.
- The full `actors` suite (only the binding case ran). The in-game sheet is r11, before the head fix.
- Side views keep the silhouette fit: the mane and cheeks may sit a little off, which I did not measure.
- Loop seams beyond the jitter gate. Android cook (only on request).
- `references_hd` hashes are in `references_hd/generation_runs.json`, not in `creature_3d_progress.json`.


## Dropped MM9 clips restored (2026-10-31, run2-clips-groupB)
MM9's GEZZAMPT.abc has 16 clips; `Backpedal` and `BackpedalRun` were missing. Added (loops, half keys; floor --ground-loop / --raise with smoothing 0.06 / 0.05 s, which took the shoulder-skin jitter from 13.4 to 1.5 mm/f2), bound `backpedal`, `backpedal_run`. Built with this project's own clip route in `scripts/extra_clips.sh` (soft joint-offset line now in `clips_mm9.py`), floored, then grafted with `claude_shared/graft_clips.py`: meshes, LODs, variants and the accepted clips are byte for byte (checked: old buffer a prefix of the new, old JSON unchanged). Numbers in `review/gates_extra/`, strip `review/gates_extra/strip_new.png` (numpy raster, untextured). Status: `devdocs/mm9_rework/overnight/status/clips_groupB.md`.

User artistic acceptance: "gezzampt OK" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_gezzampt_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_gezzampt_reduce_claude/before/`.
