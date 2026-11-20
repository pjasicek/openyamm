# MM8 Centaur (`mm8_centaur`, m532, Centaur A/B/C) reduction (2026-10-18)

User: "pick 5 more to do" (MM8 triangle-reduction batch 2, coordinated with sessions openyamm-f9, openyamm-b4 and
openyamm-f6). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: the
installed textures, palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_centaur.glb`, byte-identical to
`../mm8_m532_claude/export/mm8_centaur.glb` (not stale), copied to `work/mm8_centaur_source_pre_reduce.glb`
(rollback source). One merged body + head material (`Centaur_A`, 2208x1024 atlas), one `Body` node, 72 bones,
4 influences. The body mesh also carries the moving bowstring and the nocked arrow; `mm8_centaur_bow.glb` and
`mm8_centaur_quiver.glb` are separate installed attachments and are not changed. Scripts are copied from
`../mm8_m624_reduce_claude/scripts/` (fixed parenting order in `reduce_ladder.py`, `normal_weights.py`).

The m532 build had already cut the Meshy body once (14,180 -> 11,059, `../mm8_m532_claude/export/reduction.json`),
so the remaining body is lean: an even cut over the whole body failed the limits from 75 % down, and the saving is
modest.

## Keep sets and groups (`scripts/centaur_sets.py`, `patch_keep.py`)

Kept exactly (5,039 of 11,153 welded faces):
- small separate pieces (`REA_SMALL=80`: eyes, brows, short tail strips) and every tail strip piece up to 260 faces:
  at 75 % the strips thinned into 4-6 cm gaps (`scripts/rest_gap.py`);
- the fingers (finger weights > 0.5): bow grip and string-drawing hand; `scripts/grip_check.py` confirms all 884
  finger vertices and all 68 string/arrow vertices keep their bind positions (< 0.002 mm) and weights;
- the bowstring and nocked arrow (String*/Arrow weights); the string is two-sided at the nock (6 reversed face
  pairs that the weld merged: `find_doubles.py`, restored by `export_cand.py` with `REA_DOUBLES`);
- the hooves (rims and soles lose their edges first, 15 mm at 75 %);
- the face skin (head texture set on the main surface, facing forward): at 55-80 % the eyes squinted, the lips
  flattened and the beard edge smeared onto the cheek (`review/glbclose/sheet_p1p2_tex.png`);
- the body skin within 3 cm of the harness straps: it is painted strap green under the straps, and every cut moved
  that paint out as green slivers on the chest (`review/glbclose/sheet_src_f2_tex.png`, `s1` vs `s2` in
  `sheet_src_f2*` / the close-ups);
- 5 cm patches (both sides) at the inner hind thigh, crotch, croup and elbow crease: the worst points of every
  step in Running and Death (`scripts/probe_rest.py` prints their rest positions).

Groups decimated on their own: scalp, ears and hair shell 75 % (50 % failed: p99 18 mm on the hair), palms and
backs of the hands 60 %, harness strap pieces 85 %. New vertices take weights from a source surface facing the
same way (`REA_NORMAL_WEIGHTS=1`); it removed the 50 mm hind-leg error of nearest-face weights.

## Ladder

Weld 7,524 -> 1,753 open edges (unchanged by every step). Limits for the 2.60 m height: p99 7.80 mm, max 39.0 mm.

| config | step | tris | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| c2: small, hands, tail strips kept; head set 80 % | 75 % | 8,363 | 8.20 / 47.7 | 0.988 | 0.994 | fail |
| c3n: + normal-facing weights | 84 % | 9,367 | 4.97 / 38.9 | 0.994 | 0.997 | pass |
| p2: + hooves, palms 60 %, patches; head set 55 % | 75 % | 8,363 | 6.60 / 30.2 | 0.993 | 0.995 | pass; face smeared |
| f2: + face skin kept, scalp/hair 75 % | 80 % | 8,919 | 6.82 / 38.7 | 0.993 | 0.995 | pass; green slivers on the chest |
| **s2: + strap skin kept, straps 85 %** | **82 %** | **9,143** | 7.59 / 32.8 | 0.992 | 0.995 | **pick** |
| s2 | 80 % | 8,919 | 9.20 / 39.6 | 0.991 | 0.994 | fail |

Close-ups from the GLBs themselves (`scripts/glb_close.py`, the file's own normals): `review/glbclose/sheet_src_f2_tex.png`
and `_clay.png` (face, hair, torso, bow hand, draw hand, elbow, back, inner hind leg, hooves, tail, attack, side);
the picked step's torso/back/head against `f2`/`s1`: `review/glbclose/s2_*`. Face, fingers, string, arrow, tail
and hooves are unchanged; torso, harness and back match. Texture drift (`texture_drift.py r82`): 1 face over 40 (5.5 cm²).

## Build

`export_cand.py` (Cand_82, `REA_DOUBLES`) -> `swap_lod0.py` -> `build_lods.py` (the m532 ratios: build_actor_lods
defaults 0.5 / 0.18 / 0.06, 4 influences, body only) -> `shrink_shadow_lods.py` (shadow LOD1-3 pulled inside the
surface by 2 / 4 / 7 mm, capped at 15 mm, as `../mm8_m532_claude/scripts/postprocess_runtime.py`) ->
`carry_variants.py` (variants on all 7 LOD/shadow primitives) -> `check_winding.py` (0 inverted closed parts):
`export/mm8_centaur.glb`, 7.3 MB (installed 7.5 MB), 9 clips.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,159 | 5,553 | 1,967 | 629 |
| reduced | 9,149 | 4,547 | 1,605 | 508 |

`work/lod_check_{src,r82}.json`: every LOD keeps the installed bounds (LOD3 top 2.596 m vs 2.606 m installed) and
the installed floor contact in every clip (Running/Walking minima are the same as installed); one face stretches over
20x in LOD1 (installed LOD1: two). `review/lods/sheet.png`: installed / reduced, LOD0-3, standing, attack and head.

Viewer: `review/viewer/` (installed vs reduced for all three palettes, body only, plus the creature project's
review model with bow and quiver for reference); `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_centaur_reduce_claude check`: 63 switches, no console errors.

## Attack versus the native sprite

`review/attack_native/sheet.png` (native views 0 and 2 against the installed clip at the same times, reference
model with bow): the native attack rears the forequarters up on the hind legs while the bow rises and is drawn at
an upward angle (375-500 ms), levels and looses about 625 ms, then settles. The 3D Attack stays on all four hooves,
reaches to the quiver, draws level and looses at 1.0 s. Not changed here (geometry-only task); reported for the user.

**Attack v2 (2026-10-19, user review: "the whole attack anatomy is strange, he doesnt angle the body, he is stiff,
hand disappears, wrists bend").** `../mm8_m532_claude/scripts/animate_attack_v2.py` rebakes only Attack into
`../mm8_m532_claude/work/centaur_master_attack_v2.blend` (1.5 s, impact marker unchanged at 1.0 s, first and last
frames the Standing pose). Upper body after the stored humanoid bow shot (the MM6 Lizard Archer's 2HandBowAttack1):
torso side-on, bow arm straight on the aim line with the bow hand along its forearm, quiver reach, nock with the bow
in front of the belly, the hooked string held in the chest frame and drawn to the jaw while the bow arm pushes out,
draw elbow back along the arrow, release, the hand sliding back past the cheek. Horse body after `m532a*`: the
forequarters rear (hind legs replanted with the exact rest hock) while the bow rises to 34 deg, level to 4 deg before
the release. `attack_v2/scripts/transplant_attack.py` carries the clip into `export/mm8_centaur.glb`
(`attack_v2/scripts/diff_except.py`: everything but Attack identical to the previous export,
`attack_v2/work/mm8_centaur_reduced_attack_v1.glb`). Gate (`../mm8_m532_claude/scripts/attack_gate.py`,
`attack_v2/work/gate_v2.json`): bow-hand wrist 15 deg and draw-hand wrist 0 deg through the shot, forearm twist
<= 72 deg, no arm inside the torso, string on the fingers from the hook to the release. The wrist rule fails only on
frames 0-6 and 67-72, the blend from and to Standing, whose bow-carry hold bends the wrist 114.6 deg in every frame of
Standing (not changed here). `lod_check` (`work/lod_check_r82_attack_v2.json`): Attack minimum -1.6 mm at LOD0,
no stretched faces, other clips and bounds unchanged. Sheets: `review/attack_v2/sheet_native.png`,
`review/attack_v2/sheet_hands.png`. Viewer: the 82 % models carry Attack v2; `withbow_v2` is the bow/quiver review
model with Attack v2, `withbow_ref` the old one.

**Attack v2b (2026-10-19, user review: bow "rotated 90 deg", "the bowstring should always be near his chest").** With
the wrist straightened along the forearm, the fitted grip left the bow's plane across the shot (string beside the
stave; bow plane normal 150-160 deg from the shot line while drawn). `spin_bow()` now turns the bow about its own long
axis in the fist so the plane holds the line from the grip to the chest (nocking) and the jaw (aim), with a continuous
angle over the frames; it fades in and out with the wrist blend. Gate metrics `bow_normal_to_shot_deg` (90 = shot line
in the plane; to the drawn nock, else to the base of the neck) and `bow_string_side` (+1 = string toward the archer):
frames 10-63 within 12.3 deg of 90 (over 10 deg only on frames 19-20, the first draw frames) with the string on the
archer's side; frames 0-9 and 64-72 blend to Standing,
whose carry holds the bow upright in the body's side plane with the string toward the body (36 deg off the neck line
only because the bow hangs at the left hip). Previous export: `attack_v2/work/mm8_centaur_reduced_attack_v2a.glb`.
Rear three-quarter (the user's camera) and top views: `review/attack_v2/sheet_user_view.png`.

**Bow-carry fix (2026-10-19, user: "ok fix the wrist first").** Every clip derived the bow hand from a placed bow
through the fitted grip, bending the bow-hand wrist 114-168 deg. `../mm8_m532_claude/scripts/carry.py` keeps each
frame's bow pose (centre, limbs, string toward the body) and turns the fist about the stave; the arm is re-solved for
a straight wrist with the elbow hanging 20 cm out from the shoulder (closer, the upper arm pressed 6-28 mm into the
lat), and the bow turns back in the fist by the same angle. A dynamic-programming pass picks the cheapest continuous
sequence of holds per clip; clips that start or end in the Standing pose meet the Standing hold exactly (Attack,
Hit, Cast, Fidget, loop joins). In Death the bow may also tilt in the grip (here up to 45 deg) and come 12 % toward
the shoulder, bow and arm above the floor; Dead holds Death's last frame. `carry_fix.py` rebakes LArm, LForeArm,
LHand and Bow in every clip but Attack; `animate_attack_v2.py` starts and ends Attack in the same hold. Peak bow-hand
wrist bend in degrees (`attack_v2/work/carry/{before,after}_*.json`):

| Clip | Before | After |
|---|---:|---:|
| Standing | 114.6 | 30.1 |
| Walking | 121.1 | 28.8 |
| Running | 128.4 | 21.3 |
| Fidget | 114.6 | 33.4 |
| Hit | 114.7 | 29.8 |
| Cast | 114.6 | 29.6 |
| Death | 168.4 | 9.2 |
| Dead | 144.2 | 1.2 |
| Attack | 116.6 | 29.6 |

Forearm twist stays under 64 deg (Death; 17 deg or less elsewhere but the Attack's 37), no arm vertex inside the
torso, and the upper arm beyond the armpit is inside the body only where it already was: Attack 27 mm at frame 21
(unchanged) and the fallen body lying on its arm in Death/Dead (59 -> 45 mm). Floor contact, bounds and stretched
faces at every LOD match the original reduction except Attack's minimum (-1.6/-1.4 mm at LOD0/1, as in v2b) and Dead
LOD1 (8.0 -> 10.7 mm above the floor) (`work/lod_check_r82_carry.json`);
winding clean. All nine clips were carried into `export/mm8_centaur.glb` (everything else identical; previous export
`attack_v2/work/mm8_centaur_reduced_attack_v2b.glb`). Unchanged and outside this fix: the draw-hand wrist reaches 70 deg
in Cast and 104 deg in Death/Dead. Sheets: `review/attack_v2/sheet_bow_wrist.png` (Standing, Walking, Running, Death,
Attack start and end, before and after) and `review/attack_v2/sheet_bow_wrist_death.png` (the fall).

## Status

Installed 2026-10-19 after user review ("ok accepted": Attack v2b and the bow-carry fix) with
`tools/install_model.py --world mm8 level_generation/creatures/mm8_centaur_reduce_claude/export/mm8_centaur.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_centaur_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_centaur_actor_models_keep_native_roles` passes (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_centaur_source_pre_reduce.glb` with
`tools/install_model.py --world mm8`. Open: the draw-hand wrist still reaches 70 deg in Cast and 104 deg in Death/Dead.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source), `find_doubles.py` -> `REA_PROTECT=Head,Neck
dump_mesh.py`, `dump_groups.py` -> `REA_STRAP_SKIN=0.03 REA_STRAPS=group REA_PALMS_GROUP=1 REA_KEEP_HOOVES=1
centaur_sets.py` -> `REA_PATCH_R=0.05 patch_keep.py work/keep_c.npy work/keep_p.npy 0.19,0.83,0.73 0.09,0.72,0.88
0.18,0.87,1.22 0.63,-0.66,1.84 0.26,0.45,0.84` -> `REA_NORMAL_WEIGHTS=1 REA_KEEP_FACES=work/keep_p.npy
REA_GROUPS=work/groups_c.npy REA_GROUP_RATIOS=1:0.75,3:0.6,4:0.85 run_ladder.sh s2 0.82,0.80` -> build as above
-> `grip_check.py`, `lod_check.py`, `lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_manifest.py`.

## Gait rollout (2026-10-31, package q4)

**Walk2** (working trot as Walking, front L + hind R at 0; 1.776 m in 0.6458 s, authored 2.75) and **Run2** (left-lead canter, hind R at 0; 3.0656 m in 0.5625 s, authored 5.45) grafted onto the installed model by `../gait_rollout_20261031/q4/scripts/gait_centaur.py` on `../mm8_m532_claude/work/centaur_master_carry.blend`: a new horse body with `animate.py`'s leg(); the rider, bow, string, quiver and arrow keep the installed Walking/Running channels at the same phase (the carry-fixed bow hold), Spine taking back 70 % of the canter's rocking. Binding for Centaur A-C: `walking: Walk2`, `stride_length: 1.776`, `run: Run2`, `run_stride_length: 3.0656` (it wandered on Walking x1.78-1.85 and chased on Running x1.62-1.74). Gate window: wander x0.98-1.05, chase x0.98-1.06. Rider head bob 2.4 % / 4.6 %; hoof toe-out front 0, hind +4.8 as every clip. Viewer: `review/viewer/` revision `centaur-gait-1` (A with the bow and quiver merged for review, A-C bodies). The hind thigh creases at the stifle when a hind leg reaches far forward, as in the installed Running.

Rebuild: `../gait_rollout_20261031/q4/README.md` (Rebuild). A far-LOD repair rerun (`lod_repair_claude`) or any rebuild of the installed GLB must re-graft these clips from `../gait_rollout_20261031/q4/work/centaur_clips.glb` with `../claude_shared/graft_clips.py`. Rollback source: `../gait_rollout_20261031/q4/work/rollback/mm8_centaur.glb`.
