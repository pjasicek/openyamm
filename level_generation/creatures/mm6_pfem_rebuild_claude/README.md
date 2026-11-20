# MM6 PeasantF1 (pfem) rebuild on the MM9 PeasantFemale skeleton — 2026-11-11 (stream `rebuild`, audit mm678 2026-11-11)

New Sorpigal woman, monsters 595/596/597 (`PeasantF1 A`, `PeasantF1 B`, `Peasantf1 C`). Replaces the installed v3
(`../mm6_pfem_claude/`: Mixamo rig, clasped hands, knife attack; user: "the body is good, face is terrible", "hands are terrible,
especially in standing"; the v4 rebuild was rejected for heavy hair and heavy far LODs; three arm-fix rounds were reverted).
Route: the approved MM9 humanoid "Yrsa route" (MM9 skeleton with names and rest rotations kept, joints translated, MM9 clips,
grafted MPFB five-finger hands, separate head set), with the numpy chain of `../mm9_peasantf1_claude/` (same skeleton and clip library)
and the helpers of the Guard pilot (`../mm6_gua_rebuild_claude/`).

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/mm6/models/mm6_pfem.glb` (sha256 a47c43988a09…, follow-up 4 of 2026-11-12 below; follow-up 3 was 3d4d8fb7a10d…; follow-up 2 was 99d45ee4acb5…; the 2026-11-11 rebuild was 08e60edc3e17…), `tools/install_model.py --world mm6` |
| Revert | `mkdir -p /tmp/pfem_revert && cp work/before_rebuild/mm6_pfem.glb /tmp/pfem_revert/ && python3 tools/install_model.py /tmp/pfem_revert/mm6_pfem.glb --world mm6`, then put the three PeasantF1 blocks of `work/before_rebuild/actors_pfem_entries.yml` back into `assets_dev/worlds/mm6/models/actors.yml` (whole file at claim: `work/before_rebuild/actors_full_at_claim.yml`) and revert the `mm6_pfem_actor_models_bind_town_peasants` hunk of `game/outdoor/HeadlessOutdoorDiagnostics.cpp` |
| Binding | `actors.yml` A/B/C: scale 103.46 (old 111.6 x 1.574 / 1.698 standing heights; old `z_offset` 0.07 dropped, floor audit ok), walking `Walk2` stride 1.24, run `Running` stride 1.554, look `FHP Neck, FHP Head`, upper body `FHP Spine1`, attack impact 0.48 s, skins `pfem_a/b/c`; the v3 palm sockets are gone (peasants do not cast) |
| Body | the v3 master (`../mm6_pfem_claude/work/final_v3_head_repaired.blend`, the same body as the installed reduced LOD0, at full density) scaled to MM9's height (x1.0727), made symmetric (right half mirrored; the head on its own midline, 5.4 mm off the torso's), mouth cavity and teeth removed and the lips closed, skull skin under the hair pruned |
| Arms and hands | the thin bare v3 arms and open Meshy hands cut at the short sleeve's hem; a posed, straightened MPFB female arm (`mpfb_arm.py`, macro weight 0.55 / muscle 0.45: radius 48 / 38 / 23 mm at hem / elbow / wrist, v4's target was 40 / 37 / 24) from inside the sleeve to five fingers with 15 finger bones per side; the sleeve turned onto MM9's bind arm (28 deg) |
| Triangles LOD0/1/2/3 | 9,417 / 4,702 / 1,691 / 562 (v3 installed 7,393 / 3,695 / 1,847 / 923; v4 13,878 / 7,852 / 4,105 / 2,948): far LODs lighter than v3's. LOD0: face skin 2,234, hair 758 + 474 back faces, braid 900, arms+hands 1,800 |
| Skeleton | MM9 PeasantFemale (73 joints; skirt chains, Ponytail chain on the braid) + 30 finger bones + 5 half-joint helpers = 108 |
| Clips (MM9 `peasantfemale` library) | Standing `stand1` 2.5 s, Walking `Walk` 0.9 s, Walk2 = `Walk` with leg swing x1.15 (the game walk), Running `run` 0.77 s, Fidget `Conv2` (a quiet talk gesture) 3.37 s, Attack `Conv1` 1.1-2.5 s x1.6 = 0.87 s (open-handed scolding gesture, hands raised away from the skirt), Hit `Wince1` 0.1-1.45 s x1.8 = 0.73 s (native hit 0.75), Death `Die1`, Dead. Wrists keep half of MM9's outward idle flare, fingers a relaxed curl (x1.6 of PF1's), left upper arm 5 deg / right 2 deg out in the standing-type clips (clear of our wider skirt) |
| Textures | body 2K colour + 1K normal/ORM + 1K region mask (atlas 55.7 %, fragments 0.2 %, stretch p90 1.05, median 1,275 px/m, v3 775; spread 3.4 by design: hands 1.4x, legs 0.7x, lining 0.3x); head set 1K (face, hair, braid, circlet; atlas 56.4 %, fragments 8.4 % (braid and hair cards), stretch 1.27). 4K Meshy paints downsampled once; tiers = region mask on the green bodice and skirt bands + the installed v3 ramps (palettes 786/787/788), range refitted |
| Meshy credits | 40 of 85 (body and head retexture 4K, twice: the first pair was painted on a layout whose mirror split the nose off-centre and left the open mouth; geometry fixed, relaid out and repainted) |

## Chain (`scripts/`)
1. `extract_v3.py` (Blender) master -> `work/v3.npz`; `mpfb_arm.py` (MACRO, REACH=2.2 UPPER=2 STRAIGHT=1, `BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions`) -> `work/hand.npz`.
2. `assemble.py` (Blender) -> `work/asm.npz` (parts head, hair, braid, band, dress, belt, buckle, skirt, lining, legs, hands; `co_up` = arms in the masters' pose for the upload), `prune_hidden.py` -> `work/asm2.npz`.
3. `uv.py` (uv_atlas, frozen: the paints belong to `work/uv.npz`), `make_upload.py` -> `texturing/`, Meshy `retexture_body_v2` / `retexture_head_v2` (`requests/`, masters `references_hd/`, head turnaround `references_head/` from `../mm6_pfem_claude/`), `texpass_bake_ao.py` + `pad_ao.py`.
4. `scripts/rebuild.sh <viewer rev> [--install]` = `compose.py` (maps, gentle grade on the body, no local-contrast grade on the head, face paint fixes by texel position: mouth, nostrils, circlet brass; flat skin normals 25 %; neck toned to the face; bodice rim tucked behind the belt; skirt specks and hand echoes removed; lining one dark cloth; legs cut 11 cm under the knee and capped; hair back faces) -> `rig.sh` (`fit_rig.py`, `weights.py`, `build_glb.py`, `clips.py` with `roles.json`, `wrist_relax.py`, `finger_rest.py`, `arm_out.py`, `half_keys.py`) -> `build_runtime.sh` (prepare, LODs, shadow shrink, tiers, winding, skirt lift + floor, mirror to true handedness) -> `viewer.py` + `viewer_manifest.py`.
5. `gates.sh`, `sheet_shots.sh`, `ingame.sh`; binding `bind_actors.py` (repo root).

## Checks (final build)
| Check | Result |
|---|---|
| Attack motion ratio vs MM9 biped median | 0.12 (v3 knife 0.19): a gesture by design (brief: restrained, hands clear of the skirt) |
| Worst region beyond Standing | Attack arm 10.5 % (left elbow helper at the gesture's peak, under the 12 % line); v3: Jog cloth 14.3 % |
| Hand inside the body | 0 % in every bound role (v3: Hit 46 %); `arm_hand_gate.py --outer-only --exact`: every clip <= 0.1 cm, wrists <= 42 deg, finger stretch <= 1.31, 17 chains per hand (`review/gates/arm_hand_final.txt`) |
| `robe_gate.py` (legs through the skirt) | 0 frames except Death 1/45 at 0.7 cm (Walking was 2.9 cm before the legs were cut under the knee) |
| `jitter_gate.py` vs the raw MM9 clips | 2 marginal fails: left shoulder skin 2.04 (Hit) and 2.19 (Death) mm/f2 against 2.0, from the constant 5 deg left-arm offset that keeps the hand off the skirt (kept: removing it from Hit/Death pops at the clip start) |
| gait_gate / floor_audit / winding | PASSED (wander Walk2 x0.98, chase Running x1.34) / 0 problems (stand -0.5, walk -0.1..+1.4, dead 0.0) / 0 inverted |
| Regression | `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models); `mm6_pfem_actor_models_bind_town_peasants` PASS after updating its node name and clip table to the rebuild (game code, `HeadlessOutdoorDiagnostics.cpp`); `mm6_pman_...` PASS |
| Viewer | `run_creature_review.py check`: 27 switches, 0 console errors (revision `final`) |
| Before/after | `review/sheet_before_after.png` (stand front/quarter/back, walk, attack, hit, dead; every tier) and `review/sheet_before_after_close.png` (face front and 3/4, hands front, left, right in Standing; the before model is 7 % shorter in model units, so its close-up cameras are scaled by 0.927 to frame the same parts) |
| In game | `review/ingame/frozen_sheet.png` (three tiers spawned and frozen facing the party: New Sorpigal test spot, Agar's Laboratory); `review/ingame/out_sheet.png`, `out_near_sheet.png`, `in_sheet.png` (spawned, fleeing at the run, one killed: death and corpse) |

## Deviations / open
- Body from the v3 master at full density, not the installed reduced LOD0 (same body; the face needed the master's density). Fit, weights and
  GLB build follow `mm9_peasantf1_claude`'s numpy chain (same skeleton and clips), not the Guard's Blender chain.
- The face geometry is v3's (a shrinkwrap onto the paid v4 Meshy head was tried: that head is coarser; `review/face_cmp.png`); a faint chart
  line remains on the forehead midline and the jaw silhouette is v3's low-poly edge.
- Head set fragments 8.4 % (the braid's lobes and hair-card charts) above the 3 % target.
- MM9's run is bound as the run (no separate Jog); MM9's walk swings the arms wide (as on MM9's own women).
- The two remaining jitter fails above (marginal).
- Not checked: motion at playback speed by eye beyond strips and stills; LOD1-3 by eye.

## Follow-up 2 (2026-11-12): the bodice's shelf at the hips, arms hanging away

The user, in the before/after viewer (Standing, front, tier A): "what is wrong with her torso?", arrows at both sides of the waist. The
green bodice was a wide box whose lower edge stuck out past the belt and the skirt top at both hips, with a step into the skirt; the arms
also hung away from the body.

**Cause.** Rest geometry, not skinning: `assemble.py`'s sleeve turn (onto MM9's bind arm, 28 deg about each shoulder) rotated every shell
vertex with |x| > 5 cm and a positive reach along the v3 arm. That reach includes the bodice's sides all the way down to the waist, so
the side of the bodice swung 5-7 cm outwards (half-width at the belt 0.158 m; v3 and the belt 0.10). `compose.py` then tucked only the rim
below the belt's top edge, which made the step. The waist vertices carry spine weights (the arm weights stop above them), and fit_rig only
reads the bodice's midline, so the joints were not affected.

**Fix (positions and arm keys only; face, hands, UVs and textures as installed).**
- `scripts/torso_unturn.py`: the turn is undone on the green bodice (the paint's region mask, by UV) and kept on the white sleeves and
  chemise, blended over 3 rings at the armhole -> `work/asm3.npz`, `work/uv3.npz`. 231 vertices, up to 69 mm. Bodice half-width at
  z 0.20 / 0.24 / 0.28: 0.158 / 0.157 / 0.163 -> 0.107 / 0.113 / 0.124 m (v3: 0.097 / 0.112 / 0.123). Edge stretch against the v3 shape
  p99 1.77 -> 1.39.
- Weights: `weights.py` on asm3, then `scripts/weights_merge.py` keeps the installed weights everywhere except the bodice below z 0.47
  (550 vertices). A plain re-run also changed 4 neck-base vertices and the skirt hem by up to 0.5 %, so those keep their installed weights.
  `rig.json` is kept (`KEEPFIT=1`).
- Arms (`scripts/arm_out.py`, Standing, Fidget, Attack, Hit, Death, Dead as before): upper arms L -5 / R -8 deg (was +5 / +2, out) and a
  20 deg forearm carrying angle at the elbow (`LF:20 RF:20`, frontal axis in the upper arm's MM9 rest frame) so the hands stay where
  they were: elbow to body in Standing 7.9 / 7.0 -> 4.2 / 3.3 cm, hand to skirt 2.9 / 0.0 -> 3.2 / 0.1 cm (`scripts/arm_clearance.py`).
  Rejected variants: a pose-based fade of the forearm offset (7 jitter fails), and the offset post-multiplied in the forearm's own frame
  (0 jitter fails, but with the elbow bent it pulled Attack's raised hands down to the belt). Walk and run are unchanged.
- Textures: `compose.py` (now `UVIN=`) recolours the bodice band by 3D height, so a re-run moved some body texels by up to 46 levels and
  the ramp range in the 5th decimal. `textures/pfem_body_final.png` and `pfem_ramps.json` were put back from `work/before_followup2/textures/`:
  every image in the GLB is byte-identical to the installed one.

Reproduce: `torso_unturn.py work/asm2.npz work/uv.npz textures/pfem_region_mask.png work/asm3.npz work/uv3.npz`;
`UVIN=work/uv3.npz compose.py`, then copy the two textures back as above; `ASM=work/asm3.npz KEEPFIT=1
WKEEP=work/before_followup2/weights.npz MESH=work/uv_tex.npz ARMOUT="L:-5 R:-8 LF:20 RF:20" scripts/rig.sh`; `scripts/build_runtime.sh --install`.

| Check | Result |
|---|---|
| glb_diff vs the claimed GLB | LOD0 head primitive identical; body: 276 bodice vertices moved, same triangles and UVs; weights changed on the bodice only; 7 images identical; LOD1-3 re-decimated (triangles 9,417 / 4,702 / 1,691 / 562 unchanged; LOD2/3 vertices -1 / -6); keys changed in the six clips listed above |
| arm_hand_gate (`--outer-only --exact`) | every clip 0.0 cm, wrists and finger stretch unchanged (max 42.4 deg Fidget, 1.31), 17 chains per hand |
| jitter_gate vs the raw MM9 clips | 4 fails (installed: 2): forearm world speed above MM9's by 1.0-2.7 deg/frame in Attack L, Hit L/R and Death R, where MM9's own arm moves at 20+ deg/frame. This is the carrying angle on a moving elbow, not jiggle: hand acceleration and angular speed stay at or below MM9's in every clip. The shoulder-skin fails of the install are gone |
| robe_gate / floor_audit / winding | Death 1/45 0.7 cm as before / 3 bindings ok (stand -0.5, walk -0.1..+1.4, dead 0.0, as before) / 0 inverted |
| motion_audit (`audit_before_followup2` -> `audit_after_followup2`) | ratio 0.12 -> 0.12; attack amp p90 0.0505 -> 0.0516; worst region still the Attack arm 10.5 -> 11.0 % (line 12 %) |
| Regression | `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 185 models); full actors suite: see the ledger row |
| Viewer | `run_creature_review.py check`: 27 switches, 0 console errors |
| Shots | `review/followup2/sheet_waist.png` (stand front/side, waist front/side/back, installed vs fixed), `sheet_shoulders.png`, `sheet_clips_front.png`, `sheet_clips_side.png` (walk, run, attack, hit, death, fidget), `sheet_gestures.png` (Attack and Hit close-ups); the user's viewer: `compare_viewer_front.png`, `compare_viewer_side.png` (before the fix: `before_front.png`, `before_side.png`) |

Revert: `mkdir -p /tmp/pfem_revert2 && cp work/before_followup2/mm6_pfem.glb /tmp/pfem_revert2/ && python3 tools/install_model.py
/tmp/pfem_revert2/mm6_pfem.glb --world mm6` (actors.yml unchanged; its state at claim is in `work/before_followup2/`).

## Follow-up 3 (2026-11-12): head and neck jutting forward in the walk

The user, in the before/after viewer (Walk2, side): "isnt her head like crouched too forward?" The head and neck stuck out ahead of the
shoulders, the upper back was rounded, and the arms swung far behind the body. The v3 walk on the left was upright.

**Cause.** MM9's PeasantFemale `Walk`, bound as Walking and Walk2, bends the upper back forward at Spine2 (+11 deg over Standing) and the
neck (+6 deg), then tips the head back (-22 deg) so the face stays level. On MM9's own body that is the same: head 6.3 cm ahead of the chest,
chest->head line 17.8 deg off vertical. The rounded back also carried the arms backward, so the right arm reached 52 deg behind.
MM9's `run` keeps the back upright but tips the chin up by 19 deg against Standing. The gestures (`Conv2` Fidget, `Conv1` Attack) lean in
at Spine3 by +5.6 deg. Measured with `scripts/head_posture.py` (glTF y up, +z forward, 30 fps).

**Fix (animation keys only).** `scripts/head_upright.py work/before_followup3/mm6_pfem.glb export/followup3/mm6_pfem.glb
work/followup3/params_final.json` edits the runtime GLB's rotation keys in place. Mesh, weights, skin, images, materials, LODs and
`actors.yml` are unchanged, and so is the follow-up 2 torso. glb_diff reports only sampler outputs, in Walking, Walk2, Running, Fidget and
Attack.
- Per joint, the method removes a fraction k of the forward excess of the sagittal angle over Standing's mean. Walking and Walk2
  (loops): k 0.85 on Spine2, Spine3 and Neck, one constant turn per clip (-9.6 / -2.5 / -5.4 deg), so each frame keeps its own motion.
  Fidget and Attack (gestures): k 0.6, on the positive excess only, low-passed (Hann window 0.4 s / 0.6 s) and faded out over the first and
  last 0.25 s / 0.3 s, so both clips still start and end on their own keys.
- Head: in the walks, one turn (+16 deg) brings the mean facing pitch to Standing's (1.3 deg, chin level). In Running, +14.2 deg takes the
  chin-up from -18 to -4 deg. In the gestures, the head keeps its original world facing.
- Braid: with the head over the chest again, the braid floated 3.5 cm behind the back. Turned back by the whole head correction, it sank
  into the back. Its root (`Ponytail1`) now turns by a solved fraction of the head's correction (Walk2 -6.9 deg, Running -5.4 deg), so its
  end keeps the clip's original distance behind the upper chest (P12 9.7 / 8.2 cm, Standing 9.4).
- Walk arm swing: the right upper arm's swing relative to the chest is scaled by 0.75 about its centre. The left arm is unchanged, because
  the upright chest already brings both arms 12 deg forward.
- Half-joint helpers (XhalfHead, XhalfUpperArm, XhalfForearm) are re-keyed on the changed clips by `half_keys.py`'s rule, now
  `scripts/half_keys_rule.py`. On the installed clips this rule reproduces the stored keys to within 2e-4.
- Hit (a flinch, more forward on v3: 27 deg), Death, Dead and Standing are unchanged.

| Clip | chest->head line, deg (mean, max) | head ahead of chest, cm | head ahead of shoulders, cm | head pitch, deg (+ chin down) |
|---|---|---|---|---|
| Standing | -1.4 -> -1.4 | -0.6 -> -0.6 | 0.3 -> 0.3 | 1.3 -> 1.3 |
| Walking / Walk2 | 19.6 (19.7) -> 4.2 (4.2) | 8.6 -> 1.9 | 8.0 -> 2.2 | 2.5 -> 1.0 |
| Running | -0.7 -> -0.7 | -0.3 -> -0.3 | 1.3 -> 1.3 | -18.2 -> -4.1 |
| Fidget | 8.8 (14.8) -> 3.7 (8.0) | 4.0 -> 1.7 | 3.4 -> 1.7 | 1.1 -> 0.9 |
| Attack | 6.5 (15.9) -> 2.7 (13.8) | 2.9 -> 1.2 | 3.2 -> 1.9 | -5.0 -> -5.2 |
| Hit | 19.2 (42.7), unchanged | 8.1 | 7.0 | 37.0 |
| v3 (before model): Standing / Walking / Jog / Fidget / Attack / Hit | 0.6 / 4.6 / 7.0 / 0.9 / 6.7 / 27.1 | 0.2 / 1.7 / 2.5 / 0.3 / 2.4 / 8.9 | | |
| MM9 on its body: stand1 / Walk / run / Conv2 / Conv1 / Wince1 | -2.3 / 17.8 / -1.7 / 7.9 / 6.2 / 16.7 | -0.8 / 6.3 / -0.6 / 2.8 / 2.2 / 5.5 | | |

Walk upper-arm swing (world, deg, - = behind): L -34.1..-3.0 -> -17.6..14.2, R -51.7..8.9 -> -29.0..20.0 (v3 Walking: -25..30, -23..28).
Numbers: `work/before_followup3/head_posture_{installed,v3,mm9lib}.json`, `review/followup3/head_posture_fixed.json`.

| Check | Result |
|---|---|
| glb_diff vs the claimed GLB | only animation sampler outputs differ (Walking 10, Walk2 10, Running 3, Fidget 6, Attack 6 channels); every other part is identical |
| arm_hand_gate (`--outer-only --exact`) | every clip 0.0 cm, wrists and finger stretch identical to the installed model (max 42.4 deg Fidget, 1.31), 17 chains per hand (`review/followup3/gates/arm_hand.txt`) |
| jitter_gate (runtime GLB vs `work/clips.glb`) | 5 fails before and after, in the same clips (Attack L, Hit L/R, Death L/R). Attack L forearm excess 1.06 -> 1.22 deg/f (the line is 1.0), upper arm 0.09 -> 0.72 (the low-passed chest correction). Walk2 shoulder skin 0.48 -> 1.62 mm/f2 (the line is 2.0). Hit and Death are unchanged (`review/followup3/gates/jitter*.txt`) |
| robe_gate / floor_audit / gait_audit / winding | Death 1/45 0.7 cm as before / 3 bindings ok (stand -0.5, walk -0.1..+1.4, dead 0.0, unchanged) / wander Walk2 x0.98, chase Running x1.34, 0 flagged / 0 inverted |
| motion_audit (`audit_after_followup2` -> `audit_after_followup3`) | ratio 0.12 -> 0.12; Walk2 bad triangles: head 0.9 -> 0.1 %, braid 6.3 -> 0.1 %, arm 0.6 -> 0.2 %; worst region still the Attack arm 11.0 % |
| Regression | `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 185 models); `mm6_pfem_actor_models_bind_town_peasants` PASS; full actors suite 191/193 (fails: MM9 maps without models, out05 event clearance; as in follow-up 2, not this model) |
| Viewer | `run_creature_review.py check`: 27 switches, 0 console errors |
| Shots | Installed vs fixed, project viewer, tier A: `review/followup3/sheet_walk_side.png`, `sheet_head_profile.png` (Standing, walk, run head profiles), `sheet_walk_quarter.png`, `sheet_run.png`, `sheet_gestures.png`. User's compare viewer: `review/followup3/compare_before/` (installed before the fix) and `compare_after/` (every role, side and three-quarter), with a crop pair in `compare_walk_installed_vs_fixed.png` (left: before the fix, right: fixed) |

Reproduce: `scripts/head_upright.py work/before_followup3/mm6_pfem.glb export/followup3/mm6_pfem.glb work/followup3/params_final.json`, then
`python3 tools/install_model.py export/followup3/mm6_pfem.glb --world mm6`. This step runs after `build_runtime.sh`. A full rebuild needs it
again, applied to the new runtime GLB. Shots: `scripts/followup3_viewer.sh <candidate glb>`, `scripts/followup3_shots.sh <out dir> <roles>`.

Revert: `mkdir -p /tmp/pfem_revert3 && cp work/before_followup3/mm6_pfem.glb /tmp/pfem_revert3/ && python3 tools/install_model.py
/tmp/pfem_revert3/mm6_pfem.glb --world mm6` (actors.yml unchanged; its state at claim is `work/before_followup3/actors_full_at_claim.yml`).

## Follow-up 4 (2026-11-12): hole in the cheek, forehead crack, nostril notch, hairline flaps, jaw facets

The user, in the compare viewer's head close-up (low three-quarter, her right side): a hole in the cheek in front of the ear, a dark
crack down the forehead, a dark notch at the side of the nostril, angular hair-shell flaps at the temple and faceting along the jaw.

**What each defect was** (measured on the LOD0 head primitive of the installed GLB; `scripts/seethrough.py`, `soft_render.py`,
`pose.py`, `compare_render.py`, `compare_posed.py`, `hole_sheet.py`; LOD0 has no split normals and no open boundary on the face
midline, so neither the crack nor the jaw was a normals seam):
- **Hole**: open geometry. `prune_hidden.py` (2026-11-11) deleted 99 v3 head faces as hidden under the hair, but it counted rays that
  hit the single-sided hair shell from inside as cover; with backface culling the hair does not cover them. In front of the right
  ear that left a quad open between the face rim and the hair's front edge (the background showed through the head). The same prune
  opened both nostrils (7 faces inside the nose wings: the "notch" showed the background) and the nape: seen from behind or the side
  under the bob, the gap between hair and neck looked through the head. No ear was involved (the v3 master has none: open loops at
  the ears, under the hair).
- **Forehead crack**: paint sampling, not a seam. The symmetry snap left needle faces along the midline (66 under 0.6 mm wide) and
  small mirror-seam charts; some needles were one-texel-wide charts inside hair-brown texels of the atlas, others had collapsed onto
  texel (0, 0) (dark brown). The 1 cm line down the forehead was one such needle (face 758); others drew the speck on the columella,
  the philtrum dot and a faint line between the brows.
- **Nostril notch**: the open nostrils above, plus a cancelling fold in the nose-wing crease lit as a pale facet.
- **Hairline flaps**: the hair shell's front edge hooks inward and stops 3-8 mm off the face; its zigzag rim and the hook's underside
  read as angular flaps.
- **Jaw facets**: shading of v3's coarse jaw and chin (20-30 deg steps between neighbouring vertex normals, a hard crease where the
  face rim meets the neck); the paint itself is smooth there.

**Fix** (`scripts/face_fix.py`, then `scripts/followup4_build.sh`: head LODs from `tools/build_actor_lods.py` on the fixed level zero,
`splice_head_lods.py` keeps the installed body LOD primitives and rebuilds the merged shadows, `shrink_shadow_lods.py`,
`fix_winding.py`). Only the head primitive and the three head images change.
- Holes: 39 of the pruned faces come back (13 that fill a hole in the software z-buffer from 156 directions, plus their one-ring;
  12 that would mostly sit over drawn skin are left out, and so are the hairline-notch faces above the forehead, which the decimated
  LOD1 fringe showed as a skin wedge). Their 33 new charts sit in free atlas space; each texel copies the nearest face-skin texel in
  3D (nostril interiors x0.55, the 22 nape faces x0.85), flat normal map. Fan caps of the ear openings were tried and dropped: a flat
  fan sticks out of the curved temple.
- Forehead crack and specks: 72 midline needles and small-chart faces take the UVs of the big face chart their corners belong to (105
  new vertex entries, so their neighbours keep their UVs; eyes and lips untouched).
- Normals: face skin area-weighted per position as `build_glb.py` (reproduces the installed normals), then a bilateral smoothing on
  the jaw, chin, lower cheeks, face sides and nose-wing creases (235 positions; sigma 32 deg under the chin, 20 deg elsewhere; eyes,
  brows, nose bridge and lips keep theirs). Neck positions shared with the body keep the body's normal. Normal change on the face
  skin: p50 0.0 deg, p99 16.3 deg. Hair, braid and band keep their installed normals (outer-hair normals on the tucked edge lit the
  hook's underside white from below in the viewer; reverted).
- Hairline: the hair shell's front edge from temple to jaw, below the circlet, is tucked onto the skin (+0.8 mm, at most 4 mm; 75 edge
  vertices, two rings following at 50 % / 20 %, back-face copies with them, three Laplacian passes along the edge). Above y 0.685 it
  is unchanged (the hair under the circlet carries the circlet's cream paint).

| Measure | Installed (3d4d8fb7a10d) | Follow-up 4 (a47c43988a09) |
|---|---|---|
| Triangles LOD0 / 1 / 2 / 3 (head part) | 9,417 / 4,702 / 1,691 / 562 (3,841 / 1,914 / 688 / 229) | 9,456 / 4,720 / 1,699 / 565 (3,880 / 1,932 / 696 / 232) |
| See-through pixels, bind pose, 120 directions, LOD0 / 1 / 2 / 3 (0.16 mm2 each; `review/followup4/gates/seethrough.txt`) | 59,925 / 62,835 / 102,980 / 553,257 | 11,901 / 12,914 / 42,965 / 416,854 |
| LOD0 see-through by view (az/el): front 0/0, her right 330/-20, below 0/-40, behind 180/0, 150/0 | 82, 318, 1,784, 764, 1,512 | 0, 0, 61, 0, 0 (the rest: shoulder and braid, not the head) |
| Faces sampling texel (0, 0) (dark brown) / zero-area faces | 34 / 8 | 14 (12 of them hair slivers, where that texel is hair-coloured) / 8 (degenerate, never drawn); 72 of 104 midline needle and small-chart faces remapped (the rest have no big chart holding their corners, or would stretch) |
| Head images changed | | base colour, ORM, normal: 23,878 / 23,639 / 23,198 texels (new charts, gutters); body images, region mask byte-identical |
| Flat-shading check | flat 0.00, 1.5 vertices per position | flat 0.00, 1.6 |
| Detached parts | 2 (the calves under the skirt, by design) | the same 2 |
| motion_audit (`audit_after_followup3` -> `audit_after_followup4`) | ratio 0.12; boundary edges 785 | ratio 0.12; boundary edges 802 (open edges of the restored patches under the hair); head bad triangles within +-0.6 % per clip |

| Check | Result |
|---|---|
| glb_diff / own diff | nodes, skins, inverse binds, every animation sampler, materials, variants and all body primitives (LOD0-3) identical; changed: the head primitive of LOD0-3, the four shadow meshes (rebuilt from the new LODs, tier material mapping kept), three head images (`review/followup4/gates/` and `work/followup4/diff_summary.txt`) |
| Winding | 0 inverted closed parts |
| floor_audit | PeasantF1 A/B/C ok, unchanged (stand -0.5, walk -0.1..+1.4, dead 0.0); clips untouched, so no gait or arm/hand gate change |
| Regression | `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 185 models); full actors suite: see the ledger row |
| Viewer | `run_creature_review.py check`: 27 switches, 0 console errors |
| Shots (review viewer, identical cameras, tiers A/B/C, left before / right after) | `review/followup4/sheet_face_tierA.png` (front, both low three-quarters, below, forehead, nose, jaw), `sheet_face_tiers.png`, `sheet_sides_back.png`, `sheet_walk.png`; single frames in `review/followup4/before/` and `after/`; the user's compare viewer: `review/followup4/compare_before/` and `compare_after/` (head close-up, three tiers); see-through sheets `review/followup4/gates/holes_before_lod0.png`, `holes_after_lod0.png` |

Left as is: a thin sliver of the nape gap (posed Standing, from behind) under the restored nape skin; the jaw and chin silhouette is
still v3's low-poly edge (normals now blend the steps; reshaping it would change the face); the hair hook's darker underside at the
right temple (its paint); LOD2/LOD3 faces are as rough as before (decimated again from the fixed level zero).

Reproduce: `scripts/followup4_build.sh` (from `work/before_followup4/mm6_pfem.glb`), then `python3 tools/install_model.py
level_generation/creatures/mm6_pfem_rebuild_claude/export/followup4/mm6_pfem.glb --world mm6` after copying
`work/followup4/cand_final.glb` there; shots `scripts/followup4_shots.sh`. A full rebuild (rebuild.sh) needs follow-up 3's
`head_upright.py` and then this step again.

Revert: `mkdir -p /tmp/pfem_revert4 && cp work/before_followup4/mm6_pfem.glb /tmp/pfem_revert4/ && python3 tools/install_model.py
/tmp/pfem_revert4/mm6_pfem.glb --world mm6` (actors.yml unchanged; its state at claim is `work/before_followup4/actors_full_at_claim.yml`).


## Far LODs repaired (2026-11-12, lod-step1)

LOD2/LOD3 and their shadows rebuilt by `lod_repair_claude/scripts/repair.py` from the installed GLB with `LOD_LINING_FIX=1` (dark hem from the lining fixed): ladder step
25/12 %, own 512/256 px far maps by UV correspondence; LOD0, LOD1, clips, materials and tiers unchanged
(`verify_far_only.py` OK), winding 0, every_binding PASS. Numbers and captures: `../lod_repair_claude/README.md`
("MM6 rebuilds' far LODs"). Revert: `tools/install_model.py level_generation/creatures/mm6_pfem_rebuild_claude/work/before_lodrepair/mm6_pfem.glb --world mm6`.
