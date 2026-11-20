# MM9 Giant body (mm9_giant) — 3D actor, 2026-10-31

MM9 `GIANT.abc` (39 nodes, 17 clips, 588 triangles, piece `mallet` rigid on `Xbase`/`Xhammer`, no child model): rows 204 Plain Giant L50 (`MM9 Giant A`, GIANT2 + GIANTMALLET), 205 Forest Giant L60 (`MM9 Giant B`, GIANT3 + YANMIRMALLET). Both run `titan.scr` (BaseCrawl melee + Range: LightningBolt).
**Humanoid route** (MM9 skeleton, MM9 clips, grafted five-finger MPFB hands, head-only Meshy model, separate head set). Progress and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_giant.glb` (`tools/install_model.py --world mm9`), variants `gi_a`, `gi_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Giant A/B`, **scale 333.333** (the GLB is built at 0.3 x MM9's size, see below), `yaw_offset` -1.570796327, stride walk 1.34 / run 3.13 (model metres, `stride.py`, planted feet), melee impact 0.472 s (`rattack` in Hattack1), ranged impact 0.6 s released at `cast_hand` = `Bip01 L Finger11` (MM9's RangeAttack node, left hand), look `Bip01 Neck, Bip01 Head`, upper body `Bip01 Spine2` |
| Size | 2.56 m in the GLB x 333.333 = 853 world units (MM9: 8.5 m, 333 LithTech units). Descriptor body by MM9's rule: height 845, radius 154 (`mm9_monster_body_overrides.tsv`, already there) |
| Triangles LOD0/1/2/3 | 12,404 / 6,201 / 2,230 / 751. LOD0: body set 8,192 (hands about 2,600), head set 3,972 (eyes 160), mallet 240 |
| Skeleton | MM9's 39 nodes (true-handed by `mirror_glb.py`), rest rotations MM9's, joints MM9's (the fit moves our mesh onto them) + 30 finger bones (MPFB) + 16 half-rotation helpers (`*_h`, incl. Neck) |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2 `HAttack2` (kick), AttackMelee3 `Hattack2Save` (swipe), Fidget2, Taunt, Aware, Hit2 `wince2`, Death2 `die2`. **Not carried:** `giantstatic` (the bind pose itself) and `rangeattack` (key for key identical to `Rattack1`) |
| Textures | body 2K colour + 1K normal + 1K ORM, one shared set + 4-channel region mask + ramps; head 1536 colour **per tier** + 1K normal per tier + flat ORM (deviation, below); mallet 1024 x 512 procedural colour/normal/ORM + 3-channel mask + ramps. 12 images in the runtime GLB |
| Meshy credits | **20 / 30**: body Smart Topology 5, head-only Smart Topology 5, body 4K retexture 10 (backup account, no retries) |

## Deviation: build scale
MM9's giant is 8.5 m (333 LithTech units). Every shared script here (voxel closure at 2-4 mm, cm gate caps, knee pivots, MPFB hand sizes) is tuned for 2.5 m bodies, so the sources are converted at `--scale 0.00768` (0.3 x the usual 0.0256) and the binding scales by 333.333. Gate numbers below are in model centimetres: multiply by 3.33 for world size.

## Deviations: tiers
- **Body: one shared set, region mask, ramps** (the rule). The shared Meshy paint is the **Forest Giant's** outfit (bare chest, bare thighs with garters, fur and leather shin wraps). The Plain Giant's leather vest, leggings and steel greaves are ramps of the same paint, histogram-matched to MM9's GIANT2 skin read at the same body position (`tier_ramps.py`): R torso skin (belt to collar, front and back), G thigh and knee skin, B shins, A nape hair (the shared paint's brown hair below the head set turns copper on A). Tier A therefore reads as leather over the same anatomy and garters; MM9's A has plain leggings where ours keeps the fur loincloth's flaps and claws (`review/sheet_mm9_vs_ours.png`).
- **Heads: per-tier images** (design difference: MM9 has two heads, copper braids and studded headband against loose dark hair, gold earrings and heavier brows). One mesh, one Codex paint set per tier on our clay (`references_head/a_*`, `b_*`), `project_head.py`, `seam_giant.py`; 1536 colour and 1K normal per tier, about 2 x 3.5 MB as PNG. `tier_head.py` gives `GiantHead_B` its images.
- **Mallet: one procedural set, mask, ramps** (`make_mallet_tex.py`, painted by 3D position over the UV layout): A dark oak head with iron bands, rivets and engraved bosses, B steel head (ramp of the wood), dark bands, silver bosses. Shaft, wrap and pommel shared. 768 px.
- **Mallet UVs by hand, not `uv_atlas.py`** (second pass): on this 260-triangle hard-surface mesh `uv_atlas.py` gave 18-31 charts with 23-70 % of the surface on charts under 8 triangles (merges reverted; `cut_closed` best: 23 %, use 49 %). `make_mallet.py` unrolls it isometrically instead: the head's sides as one strip with each end cap hinged onto it, the shaft as two strips cut at y 0.33 (below every grip: a vertex ring inside a fist reads as shaft in the palm), two end discs. 5 islands, 0 % fragments, stretch p90 1.02, 526 px per metre (body 589).

## Route (`scripts/`)
0. `convert_sources.sh` (both skins with their mallet skins), `mirror_glb.py` to `source/true/`. Bind exactly symmetric (0.00 cm L/R). `handedness.py`: raw `R Hand` on the anatomical left, true and runtime right; the mallet is in the true right hand.
1. Masters (Codex): `references_hd/` five views of the Forest Giant from MM9 renders (`make_refs.sh`, `ref_renders.py`), `references_head/00_geometry.png` clay sculpt, then seven painted views per tier on our own head clay (`head_clay.py`).
2. Meshy Smart Topology on the 3/4 master (body) and on the sculpt (head-only).
3. `fit_giant.py` (figure's right half mirrored, arm segments onto MM9's bones, legs sheared, height 2.555 m); `head_prep.py` (open hair and jaw sheets left open) + `head_wrap_giant.py` (voxel closure with a big radius only behind the hair's side rims, so the hair becomes one mass and the face keeps its creases) + `head_close.py`; `union_giant.py` (Boolean union, head-origin attribute).
4. `rig_giant.py` (bone heat, head rigid above the jaw, hanging hair locks rigid on the head), `step_b.sh` (MPFB hands, hand length 0.29 m, 15 finger bones per side), `quick.sh` (`weights_fix_giant.py`, `helpers_giant.py` incl. a Neck helper, `reduce_giant.py`), `sym_giant.py` (exact symmetry, non-manifold clean-up: skin closed).
5. `uv_giant.py` (**never re-run**: the paint belongs to `work/uv_v1.blend`), Meshy 4K retexture, `compose_giant.py`, gentle grade (saturation 0.9, contrast 1.04), `belly_tex.py` + `belly_geo.py` (Meshy modelled and painted a second belt boss on the belly: flattened and painted out on colour, normal and AO).
6. `fist_giant.py`: right fist (fixed curl tried on the skinned mesh, the fist's real hole found by an outside test and angular enclosure, 2.79 cm, shaft radius 2.7 cm), thumb over the fingers, a constant 16.7 deg wrist turn lines the knuckles up with MM9's shaft; the mallet stays MM9's (unrotated), shifted so its axis runs through the turned fist; `make_mallet.py` builds it from MM9's stations (hex head 0.5 m, shaft to 1.30 m: MM9 slides the shaft to 1.18 m in the fist when standing, its own shaft ends at 1.095) with its UV islands; the band walls facing the head's middle were wound inward before the second pass (rewound by the strip's UV orientation). Left fist: the same solve (`hand_poses.json` gripL, holeL).
7. `rebuild.sh`: export, `clips_mm9.py` (soft joint-offset line, ORBIT hips), `finger_keys_giant.py` (fist held, wrist turn on R Hand and taken back out of `Xbase`, left fingers flexed about their own knuckle line by MM9's curl amount: MM9's own axes bend our fingers sideways), `grip_lock.py` (shaft locked on the grip: MM9's wanders 2.1 cm off it in Fidget2/Taunt), `arm_fix.sh` (`arm_bump.py`, one windowed bump per contact; `mallet` mode moves the right arm until the mallet clears the body: AttackMelee 12 -> 0 cm, Death 4.5 -> 0), `left_ik.py` (two-handed grip: the left fist's hole on the shaft by two-bone IK in Standing, Walking, Running, Fidget, kept 17 cm from the right fist's hole, sliding along the shaft where the arm cannot reach; in AttackMelee, where MM9 lets go overhead and through the blow, the grip's correction at the first and last key fades out over 0.5 s as a constant offset; the fist closes only where its hole is within 2 cm of the shaft), `left_grip.py` (every other key: each left finger and the thumb take one pose per key from a grid, chosen for the whole clip at once by Viterbi, clear of the shaft at the keys and at the midpoints between keys), post-grip bumps (`shaft` mode for AttackRanged's end, the left hand off the right at the top of the swing), helpers' keys, prepare, LODs, shadow fix, `region_variants.py`, `tier_head.py`, floor, winding, install, viewer.
8. Binding `scripts/bind_actors.py 1.34 3.13` under the flock, then the table generator under the flock (rows 9204/9205 unchanged).

## Fourth pass (2026-11-01 evening, user: "his pinky is not like holding the hammer on neither of his hands"): r23 installed
0 credits. Lease claude-pinky-fix-20261101.
- **Cause:** the MPFB pinky rests curled, its middle joint 4.0 cm from the shaft axis (skin inside the 3.0 cm shaft). `solve_finger` searched
  closing angles only and stopped a joint at the first vertex of the next phalanx in reach (its base, at the joint); the one clear pose was a
  76 deg knuckle bend that threw the pinky past the shaft (tips 33 deg round it on the palm side, 1.45-1.72 cm off). `grip_gate.py` measured
  the nearest joint and the spread only, so it passed.
- **Fix:** `fist_giant.py solve_finger_pad` (env PADSOLVE, default on) for the final finger pose: 2D search across the shaft (the curl is about
  its axis), knuckle -40..100, middle -40..110, last -40..100 deg, every phalanx's pad end (distal_mask) on the surface + gap, penetration
  penalised, opening lightly penalised. The palm search keeps the old solve, so the shaft line, holeL and the wrist turn are byte-identical
  to r21. Pinky curls (2, -24, 28) R / (0, -22, 26) L.
- `grip_gate.py`: per finger and phalanx (2, 3) the nearest skin to the shaft surface ("worst pad gap").
- Untested r22 script edits by the stopped agent (16:59: arm_bump shaftbody, corpse_mallet, left_ik, tier_ramps, rebuild) are in r23.
  Kept: Fidget's shaftbody bump. Reverted: Fidget in `left_ik.py` CLIPS (its regrip snapped the left fingers shut through the shaft, 2.9 cm).
  Added: a Fidget-only second `left_grip.py` pass after the post-grip bumps (`LG_CLIPS`), since the bump moves the open hand after the
  fingers were cleared (1.2 cm -> 0).

| Gate | r21 | r23 |
|---|---|---|
| Worst pad gap, grip clips (Standing, Walking, Running, Fidget2, Taunt, AttackMelee2) | R 1.72 cm, L 1.45 cm (Pinky3) | R 0.28 cm, L 0.27 cm |
| Fingertips round the shaft from the palm contact, Standing 0 | pinky +33 deg (palm side) | 127-173 deg, all four, both hands |
| Fingers in the shaft (mallet_gate) | grip clips 0-0.23 | grip clips 0; Fidget L 0; Aware L 0.89 -> 1.27 |
| Fidget left hand into the body (arm_hand_skin) | 1.3 cm, 6 f | 0 |
| Jitter | 6 fails | 5 (Fidget passes) |
| Mallet in the corpse (Death/Dead) | 4.20 cm | 4.20 cm (corpse_mallet.py finds no contact: open) |
| Regression actors --world mm9 | PASS | binding PASS 158 on 65; suite 192/193, the fail is out05 "could not load gameplay data" (known, not ours) |

Sheet read: `review/sheet_grip_r23.png` (Standing 0 and 0.9, Walking 0.5, Aware 0.3; both hands, front, below, side). r21 gates kept in
`review/gates_r21/`, r21 export in `work/r21_export.glb`. Not done: strips, joint close-ups and in-game not reshot on r23; the windup left
fingers (AttackMelee 2.8 cm) and the corpse mallet remain.

## Third pass (2026-11-01, user review "otherwise fine": grip and mallet): r21 installed
Credits this pass 15 (Smart Topology 5, retexture 10; 35 of 45 overall). Lease re-claimed with a cumulative budget of 45.

### Grip (`fist_giant.py` solve2, `grip_gate.py`)
- Finding: this hand is about 8 cm thick at the knuckles (the MCP joints sit near the back of the hand) and its fingers rest 38 deg palm-ward of the
  palm. A closed fist leaves no room for the shaft (the curled fingers fold into the palm's volume), so the first-pass "hole in the fist" put the shaft
  through the fingers. The grip is now palm on shaft: the axis on the knuckle line, the shaft's surface on the palm (palm skin 3.2-3.3 cm from the
  axis, R 3.0), each finger solved on its own skin (rigid-segment FK of its vertices) so every phalanx rests on the shaft's surface, then checked on
  the posed mesh; the thumb closes on its own side of the shaft at the index end. Both hands the same solve; the left one is put there by `left_ik.py`.
- The diagnostics were wrong before: `fist_view.py` and the new `grip_check.py` now keep the mallet MM9's (the pipeline takes the wrist turn back out
  of Xbase); without that the renders showed the shaft 16.7 deg off the hand.
- Left grip (`left_ik.py`) in Standing, Walking, Running, Fidget2, Taunt, Aware, AttackMelee2 and AttackMelee's ends (MM9's mitten lies on the
  shaft in those). Not Fidget (the arm cannot reach the new shaft line for 40 % of its keys; the hand is moved off the shaft instead) nor
  AttackMelee3 / Hit (half the clip; the fades jerked 9-14 deg/f). Outside the grip, `shaft`-mode bumps keep the left hand off the shaft.
- The palm grip puts the shaft 9 cm lower in the hand than the first-pass hole: MM9 slides the right fist up to 0.6 m in the attacks, and the shaft's
  end then reached the chest. The shaft now ends at 1.24 m (`mallet_tip.py`) and `grip_lock.py` stops the slide at 0.85 m.

| `grip_gate.py` (30 fps; joints = finger 2nd/3rd bones and thumb) | r16 | r21 |
|---|---|---|
| Right hand, every clip | joints 4.85 cm from the axis, wrap 102 deg (fingers through the shaft in the user's screenshot) | joints 3.99 cm, 0 inside (0.28 cm Fidget2/Taunt), **wrap 185 deg** |
| Left hand, Standing / Walking / Running / Fidget2 / Taunt / AttackMelee2 | not holding (2nd joints over 9 cm from the axis) | joints 3.79 cm, 0.03 cm inside, **wrap 209 deg** |
| Left hand, Aware / AttackMelee | not holding | wrap 198-209 deg, 1.05 / 0.64 cm inside on the transition frames |
Lich King gate on its scale: joints 2.3 cm, 0 inside, wrap 154 deg (shaft 1.65 cm); ours with a 3.0 cm shaft and 1.7 cm fingers.

### Mallet (Meshy, true to MM9's GIANTMALLET)
`references_mallet/`: MM9's mallet rendered alone (`render_mallet.py`, both tiers), Codex HD master (`CODEX_BRIEF.md`; run 1 redone with a
proportion template: the first had a 2.9:1 shaft), five views; Meshy Smart Topology (3506 tris, hexagonal head, top spike, wrapped shaft, pointed
cap); `fit_mallet_meshy.py` (MM9's frame: head 0.505 m, shaft radius 3.0 cm on the grip run, `uv_atlas.py` 121 charts); Meshy 4K retexture on
those UVs with the four views, downsampled once to 1024 (`mallet_tex_meshy.py`, gentle grade) with the tier mask (head wood / iron by the
metallic map / engraved end plates). Tier B: steel ramp of the wood, darker iron, brighter plates. `texture_quality.py`: atlas 67.2 %, spread
1.05, fragments 2.7 %, stretch p90 1.16, 1254 px per unit of the mallet's extent (body 1509 on its own extent). Deviation: our end faces carry
MM9's B engraved plates on both tiers (one shared paint); A keeps oak planks round them.

### Other gates r21 (r16 in brackets)
- `mallet_gate.py` left fingers in the shaft: 0-0.23 cm in the grip clips, Aware 0.89, AttackMelee3 1.30, AttackRanged 0.63, Death 0.63, Death2 0.95,
  **AttackMelee 2.87** (the windup release, as r16 2.52). Mallet in body: AttackMelee 3.63 cm 2 f (3.19, 4 f), Fidget 1.81 cm 2 f, **Death 4.20 cm
  2 f and Dead 4.20 cm (the head on the left thigh of the corpse, 25 f)** (2.41 / 0.15).
- `arm_hand_gate.py`: **Fidget left hand 6.0 cm into the body, 58 frames** (the hand moved off the shaft; r16 0), Fidget2 2.7 / Taunt 2.3 /
  AttackMelee 2.7 cm (4-7 frames, the left fist meeting the body at the grip's fades).
- `jitter_gate.py`: **5 fails** (r16 3): Fidget2, Taunt, Aware, AttackMelee2 left forearm 3-5 deg/f over MM9 (the IK grip against MM9's mitten
  path), AttackMelee right upper arm 3.6. Same with `--rel 0.25`.
- 0 bone stretching, 0 inverted winding, floor 0 problems, regression PASS 158 descriptors on 65 models, viewer 32 switches 0 failed.

### Sheets (r21)
`review/sheet_grip_std.png` (Standing, Walking, Aware: right and left hand from the front, below and outside), `review/sheet_grip_attacks.png`
(AttackMelee start, AttackMelee2, AttackMelee3, AttackRanged), `review/sheet_mallet.png` / `sheet_mallet_a.png` (whole, head three-quarter,
end, top, grip), `review/sheet_mm9_vs_ours.png`, strips and close-ups rebuilt, `review/ingame_sheet3.png` (Guberland jetty, both tiers).

## Second pass (2026-10-31, coordinator's six items): r16 installed
Before = r10 (first pass, installed until now), after = r16 (installed). Credits this pass 0 (20 of 30 overall).

| Gate | r10 | r16 |
|---|---|---|
| Arm and hand in body (`arm_hand_gate.py --outer-only --exact`, 48 fps, mallet excluded) | AttackMelee **L 5.2 cm, 19 frames**; R 1.5 cm, 3 frames | AttackMelee **L 2.1 cm, 2 frames; R 4.6 cm, 3 frames** (0.33-0.37 s: the two fists meet at the top of the swing, where MM9's own mitten passes through the fist); every other clip under 1 cm (Fidget2/Taunt R forearm 1.1 cm, hand 0.7) |
| Mallet in body (`mallet_gate.py`, 24 fps) | **AttackMelee 8.0 cm, 7 frames**; **Death 4.5, 17**; Death2 2.5, 1 | AttackMelee 3.2 cm, 4 frames (the shaft's seam ring inside the left palm heel at the very start and end, 0.04 and 1.0 s); Death 2.4, 1 frame; Death2 1.5, 1 frame; all others 0 |
| Left fingers in the shaft | **1.3-2.6 cm in Taunt, Aware, AttackMelee, AttackMelee3, AttackRanged**; 0.15-0.73 in Hit, Hit2, Death, Fidget2 | **0 in every clip except AttackMelee 2.5 cm** (0.04-0.12 s: the shaft passes the proximal finger bones as the hand lets go for the windup; opening the fingers cannot clear a knuckle and a bump there broke the grip at frame 0) and AttackRanged 0.28 |
| Right fingers in the shaft | 1.05 cm (1.19 Fidget2/Taunt) | 0 (per-finger clearance in `fist_giant.py`) |
| Jitter (`jitter_gate.py`, strict, per frame vs MM9) | 1 fail: Death2 L forearm acc 1.1 | **3 fails**: AttackMelee L upper arm 2.55 deg/f (0.5 s, the left-hand bump off the right fist), AttackMelee R forearm 1.08 deg/f (0.88 s, mallet bump fade), AttackRanged L shoulder skin 2.21 mm/f2 (limit 2.0, the shaft bump at the end). Death2 passes (ramp 0.3) |
| Jitter `--rel 0.25` (as `mm9_bigfoot_claude`) | - | same 3 clips: AttackMelee L 2.55, R 1.08, AttackRanged L skin 2.21 |
| Mallet texture (`texture_quality.py`) | atlas 82.5 %, **stretch p90 23.7, fragments 17 %** | atlas 51.3 %, density p10/p90 833/840 (spread 1.01), **stretch 1.02, fragments 0 %**, 5 islands; 526 px/m against the body's 589 |
| Body / head texture | 55.1 % / 66.4 % | unchanged |
| `bone_length_audit.py`, `check_winding.py`, handedness | 0 / 0 / true right | 0 / 0 / true right |
| `detached_parts_audit.py` | mallet floats (rigid, by design) | same |
| `flat_shading_check.py` | mallet 0.58 | mallet 0.54 (hard-surface head, by design) |
| Collapse (`review/gates/collapse.txt`) | worst seen head 26 (AttackRanged) | unchanged pattern: head 26 (AttackRanged), 23 (AttackMelee3), neck creases under big head turns |
| `floor_audit.py --world mm9` | 0 problems | 0 problems (stand 0, walk -0.2..0, dead 0) |
| Regression `mm9_actor_models_build_every_binding` | PASS 150 / 60 | **PASS, 155 descriptors on 63 models, 0 failed** |
| `run_creature_review.py check` | 32 switches, 0 errors | 32 switches, 0 failed |

Other items: collar wedges: the nape hair region of tier A's ramp now stops at the collar (`tier_ramps.py`), the wedges no longer show in `sheet_mm9_vs_ours` or `sheet_closeups_b` at review size. Belly on B: grain raised on the painted-over patch (`belly_tex.py`), still smoother than the chest around it (`sheet_tex.png`, lower left). Region mask of the mallet was empty in r11 (PIL premultiplied the unused alpha): fixed, written per channel.

## Sheets (r16)
`review/sheet_strips_{a,b}_{1,2}.png` (all 16 clips, six frames), `review/sheet_closeups_{a,b}.png`, `review/sheet_hands2.png` (right fist and left hand two ways: Standing, Walking, AttackMelee 0 / 0.1 / 0.4 / 0.95 s, Aware 0.08, AttackRanged 1.0), `review/sheet_mm9_vs_ours.png`, `review/sheet_heads.png`, `review/sheet_tex.png`, `review/sheet_fists.png`, `review/ingame_sheet2.png`. Numbers `review/gates/`. Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_giant_claude/review/viewer/

## In game
r16 in the review root (`review_root.py`), isolated run started on `bootcamp.odm` and sent with `goto 9008 10604 4777 2000 512` to Guberland (`scripts/ingame_tour2.yml`; a `--map guberland.odm` launch fails its scenario save). Both rows spawn friendly and hostile 2500-3600 units ahead: **full-body frames** of both tiers walking with the two-handed grip, A's oak and B's steel mallet, and the Lightning cast (`review/ingame_sheet2.png`, frames `review/ingame2/`). The spot is a jetty: the giants stand on the water beside it (spawn point, not the model). First-pass bootcamp frames: `review/ingame_sheet.png`.

## Open points
- Third pass (r21): Fidget's left hand 6 cm into the body for 58 frames (off the moved shaft line); the corpse's mallet head 4.2 cm into its left thigh (Dead, Death's end); 5 jitter fails from the left grip's IK (3-5 deg/f); tier B's steel head reads light grey with wood-like grain (a ramp of the oak paint).
- AttackMelee: the fists meet at the top of the swing (R 4.6 cm, 3 frames), the left fingers pass the shaft for 3 frames as the hand lets go, and the three jitter fails above. Holding the grip through the swing (IK on every key) put the left fist into the head and gave 4-7 deg/f of jitter; MM9 itself swings one-handed.
- The fists' palm heels cut about 1.1-1.6 cm into the shaft at the fists' edges (seen once a shaft vertex ring lies there).
- Neck creases under big head turns (hair locks rigid on the head); left wrist crease at MM9's wrist bends.
- Belly on B still smoother than the chest.
- Velocity events in die1/die2, `smallEQ`/`bigEQ` screen shakes and the LightningBolt's launch point not checked in game.

## Not checked
Third pass: read at full size `sheet_grip_std`, `sheet_grip_attacks`, `sheet_mallet`, `sheet_mallet_a`, `sheet_mm9_vs_ours`, `ingame_sheet3`; the r21 strips and joint close-ups were rebuilt but not read. Below the first-pass notes:
Read at full size this pass: `sheet_strips_a_1`, `sheet_strips_a_2`, `sheet_closeups_b`, `sheet_hands2`, `sheet_mm9_vs_ours`, `sheet_tex`, `ingame_sheet2` and `ingame2/g07`. Rebuilt but not read this pass: `sheet_strips_b_1/_2`, `sheet_closeups_a`, `sheet_heads`, `sheet_fists`. `sheet_tex`'s mallet cell misses the mallet (the two-handed pose moved it out of frame); the mallet is seen in `sheet_mm9_vs_ours`, the strips and in game. Two close-ups (`cbdd6`, `h2_42`) put the camera inside the mallet head. Playback not re-captured. LOD1-3, shadow meshes, indoor light, night, sounds, Android cook, cooked size.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_giant_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_giant_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_giant_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_giant_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_giant_reduce_claude/before/`.
