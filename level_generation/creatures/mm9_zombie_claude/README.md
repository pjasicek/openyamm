# MM9 zombie body (mm9_zombie) — 3D actor, 2026-10-31, third pass (neck)

Rows 180 Rotter L9 (`MM9 Zombie A`, ZOMBIE1), 181 Dripper L13 (`B`, ZOMBIE2), 182 Zombie L17 (`C`, ZOMBIE3), `ZOMBIE.abc`, 32 joints, 18 clips. Needed by Beethoven and Chasm of the Dead.
Built on the approved MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)): MM9 skeleton and clips, Meshy bodies, sharp textures. Progress, hashes, Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_zombie.glb` (`tools/install_model.py --world mm9`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Zombie A/B/C`, skins `zombie_a/b/c`, `scale: 100`, `yaw_offset: -1.570796327`, stride 1.2 / 1.2, look `Bip01 Neck, Bip01 Head`, melee impact 0.618 s, ranged and cast 0.377 s released at `throw_hand` = `Bip01 L Finger11` (MM9's RangeAttack node) |
| Triangles LOD0/1/2/3 | 11,060 / 5,505 / 1,951 / 621; LOD0 body 3,628 (limbs, trousers), torso part 2,738 (with 519 tatter lining), head set 4,694 (face, hair, teeth, eyes, 80 skull plug) |
| Skeleton | MM9's 32 joints, names, rest rotations and positions unchanged (the mesh was fitted onto them), + 30 finger bones (`Bip01 L/R Thumb..Pinky1-3`), + 10 half-rotation helpers (`*_h`: hips, knees, elbows, shoulders, neck, head) |
| Clips | 30 fps: Standing `stand`, Walking `walk`, **Running is `walk` x1.5: MM9 has no run clip for this body**, Fidget `fidget1`, AttackMelee `Hattack2`, AttackRanged `rAttack2`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2 `Hattack1`, AttackRanged2 `rAttack1`, Hit2 `wince2`, Taunt, ResurrectSpell, Resurrect, Wakeup `coffin` |
| Textures | body 2K (repacked, see below) / 1K normal + ORM; head set 2K / 1K; torso part 1536 colour + 1K normal per tier, 1K ORM shared; region masks 1K |
| Meshy credits | **40 / 40**: body Smart Topology 5, head-only Smart Topology 5, body paint 10, head paint 10, Dripper torso paint 10 (backup account, no retries). Second pass: 0 |

## Third pass: the neck graft (2026-10-31, user's note, 0 credits, viewer r15)
User: "zombie graft - fix it. the issue likely is the different color scheme of the skin for the head and the body i think?" Confirmed, and more than colour.

Viewer light, front shot, same boxes, RGB neck / RGB chest (`scripts/neck_measure.py`, before shots in `review/neck_before/`, after in `review/neck/`):

| Tier | Before neck / chest | Ratio R G B | After neck / chest | Ratio R G B |
|---|---|---|---|---|
| A Rotter | 129 88 39 / 111 89 40 | 1.16 0.99 0.97 | 129 112 55 / 137 117 58 | 0.94 0.95 0.95 |
| B Dripper | 178 158 108 / 138 107 66 | 1.29 1.47 1.64 | 135 115 65 / 144 122 70 | 0.94 0.95 0.92 |
| C Zombie | 155 133 82 / 105 82 51 | 1.48 1.63 1.61 | 116 92 47 / 124 99 53 | 0.94 0.93 0.88 |

Grain was a second fault: sharp fine cracks on the head, soft pebbles on the torso. Local contrast (high-pass std, texture space, tier A) head band 0.073 against torso neck 0.081 after the fix; B 0.057 / 0.055, C 0.053 / 0.082 (the C head set shares A's grain through a darker ramp, so it stays lower than its torso).

The fix, `scripts/head_match.py` (in `compose_all.sh`, reruns from `zombie_head_basecolor_s1.png` and `zombie_torso_?_s1.png`; refresh those after a `torso_finish.py` change):
- Each tier's head skin ramp is rebuilt by luminance rank onto that tier's torso skin at the neck, so face, neck and chest read as one corpse (head shared, ramps per tier, no new image).
- A band on the head side, z 0.875 down to the rim, off the chin: the head's cracks give way to the torso's own detail, laid in neck coordinates (angle, height minus radius) at the torso's scale, gain 1.9 from the measured contrast. Colour in the band comes from a surface grid too, because the head's UVs stretch on the flare and split it.
- The torso's last 3 cm take the head's colour at the join; the old neck hole's dark paint line within 6 mm of the head's rim is lifted.
- `tier_ramps.py`: the head mask ran the hair over the cheeks and neck, which gave the paper panels and collar on Dripper. The hairline is now taken from a side projection of the paint; cheek, jaw and neck ahead of it are skin, the partings and tie behind it are hair.

Projection: the head was never fitted by silhouette. It is a Meshy retexture of the head-only mesh from four bust masters, so landmark placement as in `mm9_highwayman_claude/scripts/project_head.py` does not apply. One eye pair and one mouth seen on all three tiers (front shots).

Accepted from viewer shots read at full size: all twelve (`a,b,c` × front, quarter, side, back) on r13; the last rebuild, r15, changed only torso texels at the rim, so r15 was read as the three fronts at 3x plus Dripper quarter and Zombie back.

Left as is: a thin dark lip remains in short lengths of the ring where the head's rim sits proud of the torso (geometry, 0 credits and no rig change wanted); a 1.5 cm column at the front of the neck keeps the finer head cracks, visible only at 3x; the side flares of the neck are the mesh's own folds; one small brown speck on the left flare. The neck measures 5 to 6 % darker than the chest (blue on tier C 12 %); left, it reads as shade under the jaw.

## Second pass (2026-10-31, orchestrator's review, 0 credits)

| Item | Cause | Fix | Before | After |
|---|---|---|---|---|
| Hands in the thigh | our fingers are longer than MM9's, and `hand_rest.py` left it half done | `arm_bump.py` replaces `hand_rest.py`: one raised-cosine window per contact, two constant axes (upper arm, wrist), the hand moved straight out from the hip, least amplitude solved at 96 fps over the whole window. The window is back on MM9's pose before the clip's last key | AttackMelee R 5.9 cm 5f, L 3.4 cm 8f; AttackMelee2 L 3.1 cm 3f; AttackRanged L 1.3 cm 1f | **all 0 frames over 1 cm** (AttackMelee L 0.4 cm); wrist 21 deg added at most, upper arm 13 |
| Jitter | `thin_keys` moved motion between frames here with no gain (hand acceleration 12.49 against 12.43), per-key floor passes, `hand_rest.py` | `thin_keys` off, floor passes only on Death, Dead, Resurrect, Wakeup | 12 clips flagged, AttackMelee upper arm 6.6 deg/f | 5 flagged, see below; upper arm 1.9 deg/f |
| Tiger stripes, pale blobs | Codex's master banded the arms and bleached the knees | `soft_detail.py`, at 4K: a smoothed per-vertex colour field (no UV seams) pulled toward MM9's olive, the texel multiplied by target/field, so fine detail stays; wounds, wrist wraps and the shin bone left out; a faint olive mottle | | softer; see "Open" |
| Paper collar | the head's neck flared to the 16 cm body ring, and the hair mask made it white | ring narrowed to 11.7 cm with smooth falloffs, in `reweight_tatter.py` | | gone |
| Wig | white hair over the whole head | new crown region; hair, crown and face ramps from MM9's own skins, not the masters | | Dripper's crown is pale grey-tan; the silhouette is still the shared hair mass |
| Ragged hairline | mask followed the paint's noise | hair mask smoothed along the surface and cut softly | | clean |
| Stick on the chest | MM9 paints a small stitched gash on the right chest (it is in ZOMBIE1); Codex drew it as a long pale rod and Meshy painted it | painted out at 4K, at (-0.08, -0.04, 0.64), 6 cm long | | gone in all tiers that showed it (A) |
| Collapse | see table | armpit weights relaxed, wider head band, hair rigid on the head, rings welded | | see table |
| Body atlas 40.5 % | unused torso charts | limb charts repacked without new flattening (`repack.py`), every map resampled once from the 4K final (`repack_maps.py`, normals rotated per face) | 40.5 %, 1,713 px | **57.5 %**, 2,041 px (+19 %), spread 1.07 |

A pale unpainted-face refill also got the skin's own detail tiled back in (`soft_detail.py`), after a smooth refill read as flat patches in close-ups.

Collapse, worst frame, before -> after (exposed faces of the final frame in `review/gates/collapse.txt`; first pass in `review/gates_v1/`):

| Clip | neck/head | armpit | body | face-frames |
|---|---|---|---|---|
| Walking | 3 -> 4 | 2 -> 0 | 0 -> 0 | 137 -> 140 |
| Running | 3 -> 4 | 2 -> 0 | 0 -> 0 | 92 -> 93 |
| Fidget | 16 -> 11 | 7 -> 0 | 6 -> 14 | 2172 -> 1968 |
| Taunt | 11 -> 9 | 12 -> 2 | 3 -> 14 | 2665 -> 1912 |
| AttackMelee | 16 -> 19 | 11 -> 1 | 9 -> 20 | 917 -> 810 |
| Hit | 8 -> 8 | 8 -> 0 | 6 -> 11 | 374 -> 285 |
| Hit2 | 28 -> 20 | 11 -> 0 | 5 -> 13 | 750 -> 591 |
| Death | 19 -> 20 | 7 -> 1 | 3 -> 12 | 618 -> 585 |
| Dead | 6 -> 6 | 5 -> 0 | 3 -> 10 | 496 -> 496 |

**Still failing, with numbers and why (second serious attempt, stopped here):**
- Collapse is not zero: neck/head up to 20 (Death, all 20 exposed), body up to 20 (AttackMelee, 8 exposed). Armpits came down at the cost of the body count, because the relaxed weights moved faces into the region label. Thin neck faces around the welded ring; none reads in the close-ups, but the count stands.
- Jitter gate, 5 clips: AttackMelee and AttackRanged2 R upper arm 1.9 deg/f, over the 1.0 limit (the contact lasts to 1.32 s of 1.5, so the bump has 0.15 s to leave before the clip ends); Death, Resurrect, Wakeup shoulder skin 25.6, 3.5, 11.1 mm/f2: whole-body floor raises against the unfloored reference, with arm joints at 0 excess.
- Wakeup (script clip, no behaviour drives it): hand 5.8 cm, thigh through tatter 19.9 cm, groin 42 faces. Not corrected.
- Cloth 0.2 cm in AttackMelee and AttackRanged2, 7 frames.
- Against MM9 the arms still show bands and the knees stay the palest part: softer, but still more contrast than MM9. The body atlas reads olive (knee mean 124/110/63), the viewer's light lifts it; in Beethoven it reads dark.
- The Dripper still has a full hair silhouette where MM9's head is bald grey, because the geometry is shared. Crown colour only.
- A short seam shows at the edge of the refilled skin on the chest in extreme close-up.

## Tiers (deviation, orchestrator's note)
Colour-only differences are ramps on shared sets: arms, legs, feet, trousers, wraps (R skin, G cloth) and face, hair (R hair, G skin, B crown). The design difference is a part: the torso (upper body inside the arm cut at |x| 0.315, tatter, rope) is its own primitive with its own UVs, mapped per tier by `KHR_materials_variants` to its own material: bare chest (tier A, moved from the body paint), leather vest (Meshy torso-only paint on the Dripper masters), chain mail (Codex masters projected, procedural rings; no credits).
Why: MM9 paints a bare chest, a laced vest and a mail shirt on one mesh; no ramp can make those from one image.
Cost: three colour + three normal images. Cooked on disk: 6.4 MB of the model's 17.8 MB (about 1.1 MB colour + 1.0 MB normal each), so 4.3 MB for B and C over one torso.
Bound per tier: checked in the installed GLB (`ZombieTorso`, `_B`, `_C` on every LOD's torso primitive; shadow meshes carry no torso) and in game, `review/ingame_sheet.png`: all three spawned with their own torso.
Head: R hair, G skin, B crown. Lost in the ramp route: Dripper's pale torn trouser patches (the shared trousers keep Rotter's pattern, recoloured). The rope stays on B and C (recoloured in the torso image), where MM9 has a leather belt; the belt is painted, the knot remains.

## Route (`scripts/`)
0. **Sources**: `convert_abc_model.py` per skin; `mirror_glb.py` on the source (`source/z*/zombie*_true.glb`): true handedness from the start, so no later mirror. MM9's bone shin is on the anatomical right leg, as in `review/mm9_true/`.
1. **Masters** (Codex): `references_hd/` five views from MM9 renders in MM9's bind pose; `references_head/` five busts; `references_tiers/` four views each of Dripper and Zombie, repainted on the same figure. `clean_alpha.py` removes Codex's soft halo before anything goes to Meshy.
2. **Meshy**: body Smart Topology (clean, five fingers, tatter and rope as parts; bald head with a woman's face), then a head-only Smart Topology from the bust.
3. **`step_a.sh`** = `fit_pose.py` (each limb segment maps its own joints exactly onto MM9's, rotation + stretch: the 3/4 master gave a skewed stride with arms 12 cm short; torso Kabsch; upper body mirrored), `head_prep.py` (head scaled, back of the skull compressed 0.86, hair shells voxel-solidified), `graft_head.py` (traps lowered 18 mm for a neck, chest flattened, back and sternum seams smoothed, neck ring conformed and bridged).
4. **`quick.sh`** = `rig_zombie.py` (bone heat on the closed skin, rules by part, fingers by connectivity, helpers), `reduce_zombie.py`.
5. **UVs** `uv_zombie.py`, `uv_torso.py`. Never re-run: the paints belong to these layouts. `work/uv_v2.blend` holds them.
6. **Textures** `textures.sh`, `grade4k.py` + `grade_basecolor.py` on the 4K paint, then `compose_all.sh` (`soft_detail.py`, `torso_images.py`, `tier_ramps.py`, `torso_finish.py`, `repack_maps.py`).
7. **Runtime** `TOKEN=<lease> REV=<rev> scripts/rv.sh --install` (`rebuild.sh`): `reweight_tatter.py` (tatter on the trouser skin, head band, hair rigid, neck ring, armpit weights, repacked UVs), `export_zombie.py` (lining, ring weld, skull plug, shards), clips, `arm_bump.py`, prepare, LODs, shadow fix, ramps, `torso_variants.py`, floor, winding, viewer.
`PYGLTF` = `claude_shared/gltf_venv/bin/python`.

## Checks (geometry and rig unchanged since r10; r15 repeats only winding 0, LODs and the binding regression: PASS, 147 descriptors on 58 models, 0 failed)
| Gate | Result |
|---|---|
| Cloth gate `cloth_gate.py` (48 fps) | **Walking 0/53, Running 0/36**; bound clips 0 but AttackMelee 0.2 cm 7/73; script clips AttackRanged2 0.2 cm, Wakeup 19.9 cm |
| Collapse gate | table above; knees 0 (L 1 in Resurrect), elbows 0, groin 2, ankle 3 |
| `arm_hand_gate.py --outer-only --exact` | **0 frames over 1 cm in every bound clip**; Wakeup (not driven) 5.8 cm. Finger stretch at most 1.27 |
| `jitter_gate.py` | 5 flagged, above |
| `detached_parts_audit.py` (24 fps) | 57 components, **0 detached** |
| `flat_shading_check.py` | 0.00 body and head, 0.01 torso |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | body atlas 57.5 %, spread 1.07; head 60.0 %, spread 1.50, fragments 1.1 %; torso 63.4 %, spread 1.13 |
| `floor_audit.py` | 3 ok: stand -0.5, walk -2.0..+1.3, living -2.1, dead 0 |
| `mm9_actor_models_build_every_binding`, `--headless-validate-actor-models` | PASS, 95 descriptors on 42 models, 0 refused |
| `run_creature_review.py check` | 48 switches, 0 console errors |
| In game (review root, isolated) | `review/ingame_sheet.png` (`bootcamp.odm`, all tiers, attacks, hits); `review/ingame_bthv_sheet.png` (**Beethoven**: a placed Rotter, Dripper and Zombie spawned beside it, in the dark sewer) |
| `throw_hand` | `launch_check.py`: at the 0.377 s release the socket is 1.3 cm from the mesh, in the left fingers, 0.94 m ahead of the pelvis, 0.97 m high |

Sheets (viewer shots): `review/mm9_vs_ours.png`, `sheet_tiers.png`, `sheet_closeups.png` (tier A: knees, groin, armpits, elbow, neck, mouth in crouch, sit, death, attack), `sheet_closeups_b.png`, `sheet_closeups_c.png`, `sheet_mouth.png`, `strip_1.png`, `strip_2.png`, `strip_3.png` (tier A, every clip, eight frames), `strip_b.png`, `strip_c.png` (seven clips). Numbers: `review/gates/`, first pass `review/gates_v1/`.

## Decisions and deviations
- **Handedness**: fixed at the source. `Bip01 R Hand` at x -0.631 of the true GLB; no held weapon on this body. The torn leg stays on the anatomical right.
- **Hands**: Meshy's own five fingers by connectivity, not an MPFB graft; left hand mirrored over the right. 15 bones per side from MM9's mitten curl (`finger_alias`).
- **Head**: head-only Meshy model, colour 2K as Yrsa's approved route, not 1K. MM9 has no jaw bone, so the mouth never opens: rigid teeth, a skull plug behind them (back faces are culled, so the mouth looked through the head at the sky; found in viewer shots).
- **Hide**: Meshy gave pebbled lizard scales and a knit vest. `soft_detail.py` cuts the 1.2-9 px band, halves the normal maps, and tones the whole set toward MM9. Still lighter than MM9. Up close the skin stays a little pebbled.
- **Mail** is procedural rings where the projected master is grey; the throat V and sleeve edges come from the projection at about 770 px/m, softer than the rest.
- **Viewer**: `frustumCulled=false` and specular 0 on all materials in `review.js` / `viewer_tiers.py`; without them, parts vanish in close shots and the torso shines. Neither is the game's behaviour.
- Tatter rides the trouser skin exactly, so it follows the thigh instead of hanging. MM9 paints it.
- Skins are opaque (alpha 255). FX `greenyeldots` and `ResurrectFX` are not wired, as on the other bodies. `ZOMBIEARM.abc` and the separate `right arm` piece: nothing in the data I searched uses them.

## Not checked
Third pass: the neck in the game itself (viewer only), LOD1-3 at the neck, the neck in motion. Animation, cloth and collapse gates were not rerun: only textures, ramps and masks changed.
LOD1-3 and shadow meshes by eye; Chasm of the Dead (Beethoven only); Standing, Taunt and script clips on the second-pass strips of tiers B and C; the projectile's flight from `throw_hand` in game (position measured, and only the ranged attack's release time); B and C strips of the clips not listed (Running, Taunt, Hit2, script clips); B and C close-ups at Hit2, Wakeup and Death; bloom; fullbrite in the skins. Playback: `run_creature_review.py playback` recorded all 16 clips at normal and half speed (`review/playback/*.webm`, 32 runs) with no errors, and I looked at timed stills from three of them (`review/sheet_playback.png`). I cannot watch video, so smoothness in motion rests on the gates and frame strips.


## Dropped MM9 clips restored (2026-10-31, run2-clips-groupB)
MM9's ZOMBIE.abc has 17 clips; three were missing. Added script clips `Death2` (die2, floor-settled into its own corpse; no Dead2), `Wakeup2` (rises from the coffin pose), `Coffin2` (lying hold loop), bound as `death2`, `wakeup2`, `coffin_idle`. Both thumbs sat 4-6 cm in the thighs in the lying pose: `arm_bump.py` Coffin2:L/R, Wakeup2:L/R (6 deg, constant over Coffin2, eased out in Wakeup2), now 0 frames over 1 cm. Jitter gate flags shoulder skin in Death2 27.4 and Wakeup2 13.1 mm/f2 from the floor raise, as on Death and Wakeup. Built with this project's own clip route in `scripts/extra_clips.sh` (soft joint-offset line now in `clips_mm9.py`), floored, then grafted with `claude_shared/graft_clips.py`: meshes, LODs, variants and the accepted clips are byte for byte (checked: old buffer a prefix of the new, old JSON unchanged). Numbers in `review/gates_extra/`, strip `review/gates_extra/strip_new.png` (numpy raster, untextured). Status: `devdocs/mm9_rework/overnight/status/clips_groupB.md`.

User artistic acceptance: "zombie - ok" (2026-10-31).


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_zombie_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_zombie_reduce_claude/before/`.
