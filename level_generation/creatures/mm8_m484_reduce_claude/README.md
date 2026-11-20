# MM8 Minotaur (`m484`, Guard / Warrior / Battleleader) reduction (2026-10-19)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) including its MM8 batch lessons. Scripts are
copied from `mm8_m404_reduce_claude/`, which has the m604 parent-transform fix, exact weights, coincident-vertex
handling, lod_check, fleck_check and the prop chain. No Meshy credits. Not installed.

Sources: the installed `assets_source/worlds/mm8/models/mm8_m484.glb` and `mm8_m484_axe.glb`, byte-identical to
`../mm8_m484_claude/export/`. The rollback copies are `work/mm8_m484_source_pre_reduce.glb` and
`work/mm8_m484_axe_source_pre_reduce.glb`. The Minotaur Peasant reduction (`mm8_m488_reduce_claude/`, another session)
was read as precedent only.

**Animation:** after two user reviews, the only attack is the reworked original one-handed attack
(see "One-handed attack" below). `Attack` and its `Cast` alias share it. The two-handed Attack and the `AttackOneHand`
name are gone. The other 7 clips are byte-identical to the installed GLB. Shading is judged from GLBs imported directly (`viewer_views.py`, `axe_views.py`). The welded `source.blend`
close-ups use `CLOSE_SMOOTH_SRC=1` and compare geometry only. The body keeps plain smooth normals, like the installed
body.

## Body

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,253 | 4,616 | 1,647 | 533 |
| reduced | **6,751** | 3,357 | 1,189 | 480 |

- **Weld:** 6,477 -> 887 open edges; no coincident vertices with different weights.
- **Limits:** for the 1.80 m figure (`REA_HEIGHT_M=1.80`), p99 5.4 mm and max 27 mm. Four influences, as installed.
- **Where the triangles are:** the head has 57 % of the faces (5,252 B_Head faces). The rest (torso, arms, thighs, legs:
  about 1,500 faces) was already lean. Below about 71 % of the total its error grows quickly: the thighs reach 36 mm in
  Death.

Regions (`scripts/face_bones.py`, `make_groups.py`):
- **Kept exactly:**
  - small pieces of up to 80 faces (`small_pieces.py`): the eyes (two separate 124/128-face pieces), the silver nose
    ring, harness buckles and 70 mane locks (1,073 faces);
  - the faces straddling the mail region-mask edge, plus one ring;
  - the soles;
  - the silver bracer faces of hands and forearm twists, plus one ring. Their fur border flecked at the wrists
    (`REA_SILVER=1`).
- **Own budgets:**
  - face 65 %: head faces in front of y -0.08 between 1.40 and 1.75 m (eyes, brow, muzzle);
  - nose pad 80 % (in front of y -0.26);
  - back of the head 35 %;
  - horns (ivory) 50 %;
  - palms 60 %;
  - fingers 70 %: both hands grip the handle. The grip renders unchanged with the axe in the hand (`review/tiers`, `grip`);
  - feet and hooves 85 %;
  - mail kilt kept.

| run | head / face / nose / horns / palm / fingers / feet | step | triangles | p99 / max mm | |
|---|---|---|---:|---|---|
| g1 | 50 / - / - / 50 / 60 / kept / 60, kilt 80 | 75 % | 6,799 | 4.11 / 45.6 | fail: hoof clefts and kilt edge |
| g2 | 50 / - / - / 50 / 60 / kept / 85, kilt kept | 72 % | 6,659 | 3.68 / 17.4 | pass |
| g3 | 45 / - / - / 50 / 60 / 70 / 85 | 68 % | 6,289 | 3.63 / 17.4 | pass; muzzle and eye sockets soft |
| g4 | back 40 / 62 / - / 50 / 60 / 70 / 85 | 70 % | 6,475 | 4.28 / 17.2 | pass; 12 flecks (nose, wrists) |
| g5 | g4 + one fleck lock round | 71 % | 6,567 | 4.78 / 19.8 | pass, flecks moved elsewhere; dropped |
| g6 | back 40 / 55 / 80 / 50 / 60 / 70 / 85 + bracers | 71 % | 6,565 | 4.57 / 17.2 | pass; eye socket softer than g4 |
| **g7** | **back 40 / 65 / 80 / 50 / 60 / 70 / 85 + bracers** | **73 %** | **6,751** | **4.48 / 17.2** | **picked** (IoU 0.9965, SSIM 0.9954) |
| g8 | back 35 / 65 / 80 / 40 / 60 / 70 / 85 | 72 % | 6,657 | 5.59 / 17.2 | fail (p99) |

The 72 % step of g7 fails on the thighs in Death (35.7 mm). The g7 max sits in AttackOneHand frame 15, as in every
run.

Colour checks on the pick:
- `texture_drift.py r73`: no face over 40.
- `fleck_check.py r73` flags 7 faces, all within 7 cm of the nose tip next to the kept nose ring. The textured
  nose close-ups match the source (`review/close/sheet_g6_nose.png`), so these are samples matched onto the ring, not
  flecks. The wrist flecks of g4 are gone.

Sheets in `review/close/`:
- `sheet_g3_head.png`, `sheet_g3_body.png`: source / g2 72 % / g3 68 % / g3 65 %;
- `sheet_g4_head.png`, `sheet_g6_head.png`: face and muzzle clay;
- `sheet_g6_body.png`: hands, hooves, kilt, legs, strike, corpse.

## Build

`export_cand.py` (Cand_73) -> `swap_lod0.py` -> `floor_contacts.py` (34 Death/Dead contact points) ->
`build_lods.py` -> `../mm8_m484_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py`. The build uses ratios
0.5 / 0.18 / 0.075 and 4 influences.

- **LOD3 ratio:** the installed ratios are 0.5 / 0.18 / 0.06. At 0.06 (378 triangles) LOD3 lost the horns and thinned
  the arms; at 0.075 (480) it matches the installed LOD3 (533).
- **Protected points:** the bounding-extreme vertices, the floor contacts and the top vertex of each red horn tip.
  Without the horn tips LOD3 was 4 cm short.
- **`lod_check.py`** (`work/lod_check_r73c.json`; the installed model in `lod_check_src.json`):
  - every LOD keeps the full 1.90 m height and the arm span within 1.5 cm. The installed LOD3 was 2.4 cm short and
    floated 15 mm above the floor in every standing clip;
  - every clip's minimum is within 1.1 mm of the floor at every LOD, except Death at LOD3: -18.1 mm, exactly as the
    installed LOD3;
  - stretched faces (over 20 times their rest area, summed over all clips): LOD0 13 and LOD1 6, the same as the
    installed LODs (inherent to the source); LOD2 3 and LOD3 2, against the installed 1 and 0 (one face each in
    Death, Dead or Running).
- `review/lods/sheet.png` compares all LODs at rest, at the attack impact and as a corpse.

## Axe

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 1,772 | 886 | 318 | 100 |
| reduced | **1,130** | 886 | 318 | 100 |

Parts (connected components, `work/axe_comp.npy`):

| part | faces | treatment |
|---|---:|---|
| two blades | 376 each | 50 % |
| shaft | 140 | kept: the fitted grip |
| six grip bands and the head collar | 92 each | 60 % |
| top cap | 118 | kept |
| pommel sphere | 118 | kept |

- **Command:** `prop_parts.py axe c50_60k 0:0.5,1:0.5,3:0.6,...,9:0.6`; max deviation 0.33 % of the 1.25 m length
  (4 mm, a blade tip).
- **Cap and pommel:** reduced to 60 %, they faceted visibly (`review/axe/sheet.png`).
- **Normals:** by angle at 60 degrees (`PROP_NORMALS_ANGLE=60`); the kept parts keep transferred normals. At 20 degrees
  the bands, cap and pommel turned faceted. At 55 % blades, 60 degrees smeared a dark streak across a blade, which
  the 50 % blades do not show (`review/axe/sheet_n60.png`).
- `review/axe/sheet_pick.png` compares source and pick. LOD1-3 are kept.

## Retexture check

- **Texture set:** one material per tier (`M484_A/B/C`) over a shared 2080x1024 atlas (body half, head half). The
  region mask's R channel is the mail, with one ramp per tier (brass / silver / yellow gold). The reduction keeps the
  UVs; base colour, normal, metal-roughness and mask are byte-identical.
- **Tiers rendered with their ramps baked** (`viewer_build.py`, `viewer_views.py`; `review/tiers/sheet_tiers_a.png`,
  `sheet_tiers_b.png`, installed and reduced per tier): the mail takes its tier colour only inside the kilt. There is
  no spill onto fur, harness or hands, and the ramp leaves no near-black streaks. Face, eyes, nose ring, horns and
  bracers match in every tier.
- **No fault found** in the head or body texture, and no retexture is needed.

## Two-handed attack rework (superseded, not shipped)

User: "would it be possible to make the attack anim slash like in front of him? like where the arrows point. and dont
look to the side ideally?" The screenshot is front-on, with arrows at the chest centre and the front of the mail kilt.

The old chop came down left of centre:
- impact head 14 cm to his left;
- follow-through at his left knee;
- head turned 13 deg to the side and tilted through the downswing.

Two jolts are removed (see the animation check below): the `Axe` joint stopping dead at 0.60 s, and the right forearm
going from 0 to 1,874 deg/s within two keys.

**Source:** the installed fitted chop itself (`mm8_m484_claude`, local `2HandAxeAttack1` refit), with its gated
two-hand grip, wrists and contacts. No library clip was needed.

**First attempt, rejected:** a fresh IK-authored diagonal slash. The 0.56 m arms only reach the axe with large wrist
bends, up to 150 deg against the old 49 deg.

`scripts/front_chop.py` rewrites only the Attack output values at the existing 60 Hz keys. Cast shares every
sampler with Attack, so the alias stays identical. Length (1.667 s), the `actors.yml` impact (0.8167 s) and the
first and last poses are kept (within 0.0002 deg), so `actors.yml` and the idle blend are unchanged. Pelvis and legs
are not animated in this clip.

- **Re-aim:** a spine twist about the vertical (30/35/35 %) that grows through the cut: +6 deg (to his left) in the
  chamber, -12 deg at the impact and -24 deg in the follow-through, then back to 0. The cut becomes a diagonal across
  the front: chamber high on his left, the front centre line at the impact (head 4 cm right of centre, 1.16 m high,
  1.17 m forward), follow-through low in front of his right knee.
- **Head forward:** neck and head keep the idle head's world orientation through the whole clip (yaw 0), nodding up
  to 8 deg into the follow-through.
- **Jolts:** every upper-body channel (arms, hands, fingers, axe, clavicles) is low-passed over 0-0.95 s (Gaussian
  sigma 0.045 s, tapered at both ends).
- **Grip:** the left arm is then solved again (two-bone IK) so the left hand sits exactly where the old clip had it on
  the handle, sliding included. The difference is 5.0 mm at most between keys and 0.25 deg; the old clip already
  drifted 5.2 mm between keys. The right hand's `Axe` joint is the old one, filtered.

| | old | new |
|---|---|---|
| peak bone speed | 1,874 deg/s (right forearm) | 707 deg/s (right hand) |
| largest speed change per viewer frame | 1,439 deg/s (0.633 s) | 379 deg/s (left hand, 0.817 s) |
| `Axe` joint | 225 deg/s, then 0 within one key at 0.60 s | eases from 219 to 0 deg/s over 0.52-0.73 s |
| still stretches | none | none |
| axe-head peak speed | 12.8 m/s | 11.2 m/s |
| head yaw | down to -13 deg | 0 deg |

Checks (`scripts/attack_gates.py`, tier A viewer GLB, 60 Hz):
- no axe head, handle, hand or forearm inside the body, horns or legs;
- hand stretch L 3.088 / R 3.087, the same as the old clip;
- body never below the floor; the axe stays at least 0.33 m above it;
- end pose equal to Standing frame 0.

`lod_check.py`: Attack and Cast stay on the floor at every LOD, and the stretched-face counts match the old clip.
`check_winding.py`: 0 inverted closed parts. The other 8 clips and the whole non-animation glTF are unchanged.

Evidence:
- `review/attack/strip_front.png`: front view every 4 viewer frames, old above new;
- `review/attack/tip_path.png`: axe-head path from above and from the front, plus speed, old (blue) against new
  (orange), impact dotted.

Superseded by the user's second review: "did you adjust the 'original' 1H attack? that should be the one to use.
you can delete the 2H one". The result is kept as a backup in `work/attack2h_rework/`: the export, the viewer files,
its strip and its tip path. The export without any attack change is `work/mm8_m484_r73_pre_attack.glb`.

## One-handed attack (user review, 2026-10-19)

User: "did you adjust the 'original' 1H attack? that should be the one to use. you can delete the 2H one". Same goals
as the first review: cut directly in front of the body centre, head forward, smooth, no dead start or jolts, grip
fitted, no contacts, feet on the floor.

**Source:** `AttackOneHand` from the installed GLB: the original fitted one-handed attack (`mm8_m484_claude`
`work/gated_master_onehand_v1.blend`, local 1Hand `MaceAttackR2`, 0.867 s, 60 Hz keys). It was unbound, so neither the
project nor `actors.yml` records an impact time. The source motion (`scripts/oh_path.py`, `jolt_report.py`):
- still for 0.07 s;
- a backswing round behind his right side in 0.12 s (axe head up to 34 m/s);
- a strike from behind-right to his right front in two keys (76 m/s), ending 0.83 m right of centre;
- a dead stop and a 0.23 s hold, then a 0.2 s recovery with the free left arm whipping at up to 3,000 deg/s;
- head turned up to 29 deg;
- largest speed change per viewer frame 2,572 deg/s.

`scripts/front_onehand.py` (-> npz) and `scripts/ship_onehand.py` (-> GLB):
- **Length:** 0.867 -> 1.1 s (66 keys at 60 Hz). The source fits its backswing, strike and recovery into 0.87 s;
  1.1 s removes the frantic backswing and recovery without slowing the cut itself much.
- **Retime:** a monotone time warp (new -> source, PCHIP) with velocity-continuous (modified Akima) sampling of the
  source keys:

  | new (s) | source (s) | phase |
  |---|---|---|
  | 0-0.06 | 0-0.075 | the still start passes |
  | 0.06-0.46 | 0.075-0.30 | backswing |
  | 0.46-0.54 | 0.30-0.37 | chamber |
  | 0.54-0.66 | 0.37-0.433 | strike; the warp slows towards its end, a follow-through instead of a dead stop |
  | 0.66-0.82 | 0.433-0.62 | the hold, shortened and slowed in and out |
  | 0.82-1.10 | 0.62-0.867 | recovery |

- **Re-aim:** a spine twist about the vertical (30/35/35 %) coils him -8 deg (to his right) in the backswing, then
  turns him +44 deg (to his left) through the strike and eases back. The idle chest faces 37 deg to his right, so this
  squares him to the target as he cuts. The axe comes down from over his right shoulder and crosses the centre line
  at 0.66 s: 1.24 m high (chest to belt), 1.5 m in front, at 14 m/s while still cutting. It decelerates low on his
  left, so the hit lands in front of the body centre, not at his right side.
- **Head forward:** neck and head keep Standing's head world orientation (world yaw within 0.1 deg the whole clip),
  with a small nod into the cut.
- **Smoothing:** spine, arms, hands, fingers, axe and clavicles are low-passed over the whole clip (Gaussian sigma
  0.04 s, tapered to the ends so the first and last poses stay). Legs and pelvis use the source's own planted stance,
  retimed.
- **Pose continuity:** the source's first pose is exactly Standing frame 0. Its last pose matches too, except for the
  kilt bones (up to 3.4 cm). Those are blended into Standing's values over the last 0.2 s. The new clip's first and
  last poses equal Standing frame 0 (0.0 mm, 0.0 deg), so idle -> attack -> idle does not pop.
- **Ship:** a new `Attack` animation with the AttackOneHand channel layout (unchanged constant channels keep their
  accessors). `Cast` shares every Attack accessor. The two-handed Attack/Cast and `AttackOneHand` are removed and the
  buffer is compacted (9 clips, 6.1 MB).

**Impact: 0.6667 s** (key 40). That is when the blade crosses the front centre line at chest-to-belt height while
still cutting (x 0.03 m, 1.15 m high, 1.51 m in front). The source has no recorded impact. Its own strike ends at his
right side, so the timing comes from the reworked path.

| | source AttackOneHand | new Attack |
|---|---|---|
| length | 0.867 s | 1.1 s |
| peak bone speed | 2,998 deg/s (right hand) | 1,141 deg/s (a left finger; arm bones below 1,000) |
| largest speed change per viewer frame | 2,572 deg/s | 549 deg/s (left forearm, recovery at 0.917 s) |
| axe-head peak | 76 m/s | 34 m/s (0.60 s, high over his right shoulder) |
| still stretches | 0.07 s at the start, then a 0.23 s hold | none (motion from the first key) |
| head yaw | up to 29 deg | 0 deg |

Checks:
- `attack_gates.py` (tier A viewer GLB, 60 Hz): no axe head, handle, hand or forearm inside the body, horns or legs,
  including the backswing over his head;
- hand stretch L 3.088 / R 3.088, the source's values;
- lowest body point -0.2 mm; the axe stays at least 0.53 m above the floor;
- the grip is the source's own: the right hand holds the `Axe` joint, filtered like every arm channel; the left hand
  is free in this attack.
- `lod_check.py` (`work/lod_check_oh.json`): Attack and Cast stay within 0.1 mm of the floor at every LOD. The most
  stretched face is the narrow kilt-front seam face (Skirt_F, 42 mm2 at rest), 30x at most in both the source and the
  new clip. At LOD0 and LOD1 one more face crosses the 20x mark than in the source.
- `check_winding.py`: 0 inverted closed parts. Dead, Death, Fidget, Hit, Running, Standing and Walking are
  byte-identical.

Evidence:
- `review/attack/strip_front.png`: front view, installed 2H attack above the new 1H attack, every 4 viewer frames;
  `*` marks the impacts;
- `review/attack/tip_path.png`: axe-head path from above and from the front, plus speed; installed 2H (blue) against
  new 1H (orange), impacts dotted.

Viewer: per tier, the installed model and the new model, opening on Attack. The viewer needs every clip in every model
with one duration (`scripts/viewer_clips.py`):
- the installed rows carry their two-handed attack as `Attack2H`, plus the new Attack/Cast for comparison;
- the new rows carry `Attack2H` too.

Check: 60 switches, no console errors.

### Bindings to apply at install (not applied)

`assets_dev/worlds/mm8/models/actors.yml`, the same change for Minotaur A (lines 1806-1808), B (1837-1839) and C
(1868-1870); clip names stay Attack and Cast:

```diff
     events:
-      attack_melee: {impact: 0.816666667}
-      attack_ranged: {impact: 0.816666667}
-      cast: {impact: 0.816666667}
+      attack_melee: {impact: 0.666666667}
+      attack_ranged: {impact: 0.666666667}
+      cast: {impact: 0.666666667}
```

`game/outdoor/HeadlessOutdoorDiagnostics.cpp`, case `mm8_minotaur_actor_models_keep_native_roles` (lines 10852-10853).
It asserts the 9 clip names and durations; AttackOneHand is not checked, and the GLB still has 9 clips:

```diff
         const std::array<std::pair<const char *, float>, 9> clips = {{{"Standing", 2.0f},
-            {"Walking", 0.8f}, {"Running", 22.0f / 30.0f}, {"Attack", 50.0f / 30.0f},
-            {"Cast", 50.0f / 30.0f}, {"Hit", 0.5f}, {"Death", 74.0f / 30.0f}, {"Dead", 1.0f}, {"Fidget", 1.2f}}};
+            {"Walking", 0.8f}, {"Running", 22.0f / 30.0f}, {"Attack", 33.0f / 30.0f},
+            {"Cast", 33.0f / 30.0f}, {"Hit", 0.5f}, {"Death", 74.0f / 30.0f}, {"Dead", 1.0f}, {"Fidget", 1.2f}}};
```

Line 10742 (`{"Cast", 50.0f / 30.0f}`) belongs to another case and is unrelated. After install, also update
`../mm8_m484_claude/README.md` and `motion_selection.json`: Attack and Cast become the reworked one-handed attack,
and AttackOneHand and the two-handed default are removed.

## Animation check (before the rework)

`../mm8_m604_reduce_claude/scripts/bone_velocity.py` on Attack, which Cast aliases (1.667 s, impact 0.8167 s):
- **Dead start:** none. The body moves from the first key.
- **The Axe joint turns while the rest holds:** between 0.43 and 0.60 s the chamber is held, and only the `Axe` joint
  turns at a constant 225 deg/s. At 0.60 s it stops dead.
- **Jolt at the downswing start:** the right forearm goes from 0 to 1,874 deg/s within two 60 Hz keys at 0.62-0.65 s.
  That is the largest change from one viewer frame to the next (1,439 deg/s at 0.633 s).

Both are removed by the rework above.

## Viewer

`review/viewer/`: per tier, the installed model (`*_r100.glb`) and the reduced model with the one-handed attack
(`*_r73oh.glb`), axe included, opening on Attack. Both carry the installed two-handed attack as `Attack2H` for
comparison (see above). The tier ramps are baked as in `../mm8_m484_claude/scripts/viewer_tiers.py`, and the native
references point at `../mm8_m484_claude/native/`. `*_r73.glb` (reduced, original clips) stay as build inputs.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m484_reduce_claude check`: 60
switches, no console errors.

## Status

Installed 2026-10-19 (user: "ok this is good, accepted."). `check_winding.py`: 0 inverted closed parts (body and axe).
Installed both with `tools/install_model.py ... --world mm8` (the rollback sources matched the installed GLBs byte for
byte first). Applied with the install:
- `assets_dev/worlds/mm8/models/actors.yml`: Minotaur A/B/C `attack_melee`, `attack_ranged` and `cast` impact
  0.816666667 -> 0.666666667;
- `game/outdoor/HeadlessOutdoorDiagnostics.cpp`, `mm8_minotaur_actor_models_keep_native_roles`: Attack and Cast
  durations 50/30 -> 33/30 s.

Regression: `OPENYAMM_REGRESSION_FILTER=mm8_minotaur ./build/game/openyamm --world mm8
--headless-run-regression-suite actors`: `mm8_minotaur_actor_models_keep_native_roles` and
`mm8_minotaur_peasant_actor_models_keep_native_roles` pass (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m484_source_pre_reduce.glb` and
`work/mm8_m484_axe_source_pre_reduce.glb` with `tools/install_model.py --world mm8`, and revert the two edits above.

Reproduce (body):
1. `REA_NODE=M484 REA_GLB=<rollback source> import_source.py`;
2. `dump_mesh.py`, `face_bones.py`, `small_pieces.py`; extract `work/basecolor.png` and `work/region_mask.png`
   from the GLB;
3. `REA_FINGERS=group REA_FACE_Y=-0.08 REA_NOSE_Y=-0.26 REA_SILVER=1 make_groups.py`, which writes
   `work/keep_pick.npy` and `work/groups_pick.npy`;
4. `REA_HEIGHT_M=1.80 REA_KEEP_FACES=work/keep_pick.npy REA_GROUPS=work/groups_pick.npy
   REA_GROUP_RATIOS=1:0.4,2:0.6,3:0.85,4:0.5,5:1.0,6:0.7,7:0.65,8:0.8 run_ladder.sh g7 0.73,0.72`;
5. `texture_drift.py r73`, `fleck_check.py r73`, `close_ladder.py`;
6. build as above (`REA_TAG=r73 build_lods.py`).

Reproduce (attack):
1. `scripts/oh_build.sh <tag>` runs `front_onehand.py` + `ship_onehand.py` on `work/mm8_m484_r73_pre_attack.glb`
   and on the three `review/viewer/mm8_m484_<tier>_r73.glb`;
2. copy `work/oh_export_<tag>.glb` -> `export/mm8_m484.glb`;
3. `viewer_clips.py` -> `review/viewer/*_r100.glb` and `*_r73oh.glb`;
4. check with `attack_gates.py`, `jolt_report.py`, `oh_path.py`, `tip_path.py <installed> <new> 0.8166667 0.6666667`
   and `strip_frames.py`.

The superseded two-handed rework is `front_chop.py`.

Reproduce (axe):
1. `prop_dump.py -- axe`, then connected components -> `work/axe_comp.npy`;
2. `prop_parts.py axe c50_60k 0:0.5,1:0.5,3:0.6,4:0.6,5:0.6,6:0.6,7:0.6,8:0.6,9:0.6`;
3. `PROP_NORMALS_ANGLE=60 prop_build.py -- axe:c50_60k`;
4. `prop_swap_glb.py`.

## Gait rollout (2026-10-31)

New locomotion clips: `Walk2` (Armed-Walk, 0.92 s, 1.361), `Jog` (Unarmed-Run-Forward, 0.76 s, 2.2942; replaces
`Running`, which was half a loop off `Walking`) and `Sprint` (Unarmed-Sprint, 0.64 s, 3.062); arms and axe from
`Running` with a rigid 8 / 12 deg two-handed raise; the twelve `Skirt_*` kilt controls are re-solved on each new clip
(`h20/scripts/kilt_solve.py`, a numpy version of `../mm8_m484_claude/scripts/solve_cloth.py`). Package
[h20](../gait_rollout_20261031/h20/README.md) appended them to the installed source
(`assets_source/worlds/mm8/models/mm8_m484.glb`; existing clips, meshes, skins and materials byte-identical; pre-gait
copy `../gait_rollout_20261031/h20/work/mm8_m484_pre_gait.glb`) and installed it; the bindings are in
`../gait_rollout_20261031/h20/bindings.yml` for the rollout coordinator. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h20/scripts/rebuild.sh m484`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).

## Anim fix (2026-11-11, MM6–MM8 audit)

Jog and Sprint recomposed with a lower knee and a coupled kilt solve (panels move as one piece): cloth bad 43.4 ->
17.1 % and 42.4 -> 19.7 %, kilt no longer inside the body. Details: [mm8_m484_animfix_claude](../mm8_m484_animfix_claude/README.md).
