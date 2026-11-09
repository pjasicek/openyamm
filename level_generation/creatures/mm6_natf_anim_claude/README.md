# MM6 female Cannibal (`natf`): library attack and cast candidates (2026-10-14, study only)

User: look in the libraries for a one-handed dagger-style attack (and optionally a one-handed cast) to replace the
custom-fitted Attack. Nothing installed; `../mm6_natf_codex/` is untouched (its `work/accepted_master.blend` was
copied to `work/master.blend`).

The current Attack started as humanoid-set Dagger Attack R2 and was re-posed in Codex rounds 3-5 into a diagonal
cross-body cut (1.83 s); the current Cast started as Armed Cast R Attack Hand 1.

## Method

- `scripts/retarget.py` / `retarget_mixamo.py` (copied from `mm6_natf_codex/scripts/`, limited to the bones with
  rig offsets so the prop, skirt and twist bones of the final rig stay at rest), every clip planted on Standing
  (`:plant`).
- `scripts/lock_left_arm.py`: the shield arm holds Standing frame 0's local pose (follows the chest).
- `scripts/clip_sheet.py` + `sheet_compose.py`: `review/attacks_a_q34.png` (current, Dagger R2/R1/R3),
  `review/attacks_b_q34.png` (Mixamo), `review/casts_q34.png`.
- `scripts/export_candidates.py` + `cand_manifest.py`: viewer `review/viewer/` (15 clips; accepted clips rescaled
  from their 60 Hz keys; `check_viewer.mjs` 15 switches, no errors).

Not fitted: start and end poses are not blended into Standing, the skirt and twist bones stay at rest, the blade
path is not aimed. Compare motion only.

## Candidates

| clip | length | reading |
|---|---:|---|
| Mixamo Sword And Shield Attack (2) | 1.0 s | compact: blade to the shoulder, overhead, diagonal cut down; closest to the native overhead-to-down sweep; shield clip, so the off hand already guards |
| Mixamo Stable Sword Inward Slash | 2.2 s | wide horizontal cut across the body at chest height; reads well, long (would need speeding up) |
| Mixamo Sword And Shield Slash (4) | 1.67 s | low backhand then a big outward overhead swing; more flourish |
| HS Dagger R2 (current base) | 1.0 s | overhead raise, forward-down stab |
| HS Dagger R1 / R3 | 1.0 s | strong chest twist (the held shield swings with it); R3 ends in a reach |
| Mixamo Stabbing / Stabbing (2) | 2.1-2.4 s | jabs close to the body; with the blade along the forearm the tip points sideways, weak |
| HS Armed Cast R Attack Hand 2 | 1.0 s | clear forward hand thrust (spell push) |
| HS Armed Cast R Buff 1 | 1.0 s | arm raised overhead (invocation) |
| HS Armed Cast R Attack 1 / Attack Hand 1 (current base) | 1.0 s | short forward push, similar to the current Cast |

## Round 2 (user picks: Attack = Sword And Shield Slash (4), Cast = HS Armed Cast R Attack Hand 1; fix head and skirt)

### Clips (`scripts/build_clips.py`, from `work/locked.blend` -> `work/clips.blend`)

- **Why the head turned:** Mixamo's sword-and-shield fighter stands side-on and turns his head to the target; the
  retarget plants her chest square to the target, so that turn made her look 30 deg left at the start and 50 deg right
  in the cut (`scripts/head_probe.py`). The cast looked 20 deg down. Gaze correction per frame: the head looks along
  Standing's head direction and follows only 30 % (Attack) / 15 % (Cast) of the chest's turn; the neck takes 40 % of
  the correction. The engine's own look-at (`actors.yml` look, B_Neck/B_Head) then aims at the victim.
- Resampled to 60 Hz; Attack 0.9 speed (1.85 s), Cast 0.7 speed with half the spine twist (1.43 s; its chest swung
  110 deg in 0.1 s); blend from/to Standing over 0.3 / 0.25 s; shield arm held in the Standing guard, 40 % anchored to
  the pelvis (the long shield swung into her hip with the chest); right elbow projected into its hinge plane; right
  wrist neutral (Codex mounted-wrist rule); upper body smoothed (binomial, 3 passes); right twist helpers baked with
  Codex `bake_twist.py`, left ones keep Standing's values.
- Impact: Attack 0.908 s (the shared gate's blow: fastest tip motion while pointing at the target); Cast release
  0.35 s (hand at full reach).

### Skirt (`scripts/skirt_skin.py`)

The 60-bone cage was simulated per clip (bell-shaped in Standing; a clip without a simulation left it at rest, and the
thighs cut through it). Replaced by skinning: cage-driven vertices go to B_Pelvis and two new swing-only helpers
(`B_L_ThighSwing`, `B_R_ThighSwing`: the thigh rotation without its twist, baked into every clip; with the twist,
Standing's 16 deg thigh twist sheared the cloth into creases). Thigh share 0 at z 0.98 to 1.0 at 0.62, left/right
blend over +-0.20 m, feathers and fringe by their centre (rigid). Rest shape: one smooth radial push field (angle x
height about the pelvis) gives 30 mm clearance over legs, hips and buttocks (the narrowed skirt dipped inside the hip
skin), applied to every skirt vertex alike. Normals recomputed for the moved cloth, merged across seams only where the
original normals agree (the cloth is double-sided). The retired cage keys and the HemOpening marker keys are stripped
(`strip_channels.py`; the gate's containment opening now rides with the pelvis). Light stair patches seen in Blender
renders are a preview artifact of imported custom normals (the untouched installed GLB shows them too).
Check (`scripts/skirt_check.py`): no leg/hip through the skirt in Standing, Walking, Attack, Cast, Fidget, Dead; the
back hem touches the calf in the Running heel kick and in the Death fall.

### Runtime and reduction

`scripts/build_runtime.sh` -> `export/mm6_natf_v2_unreduced.glb` (122 joints, LODs 11,641 / 5,808 / 2,017 / 617).
Reduction rerun on it (`../mm6_natf_reduce_claude/`, config v3: as g3 plus the shield hand kept exactly for its grip;
8 influences): **`../mm6_natf_reduce_claude/export/mm6_natf_v3.glb`, 8,613 / 4,287 / 1,469 / 435**; props
`mm6_natf_blade_v3.glb` (898, LOD2 dropped for the ratio) and `mm6_natf_shield_v3.glb` (1,272, same).

### Shared gates (`gates/gates.json`, report `gates/out_v5/gates.md`)

Installed model: 7,636 PASS, 4 FAIL (blow time). New: 7,371 PASS, 221 FAIL. Full detail (LOD0) passes everything
except `blade_signed_lead` in Attack: the fast backhand sweep of Slash (4) leads with the back of her single-edged,
forearm-strapped blade (-0.88; Codex's config puts the edge on the convex side). The other failures are far LODs only
(LOD1-3 rebuilt by `tools/build_actor_lods.py`; Codex had fitted palms and soles per LOD): shield grip gap 3.5-11 mm,
grip penetration 5-6 mm, foot yaw 13 deg, rest sole height up to 20 mm and running contact on LOD3.

Viewer: `review/final_viewer/` (tiers A/B/C with blade and shield; `check_viewer.mjs` 27 switches, no errors).
Sheet: `review/final_sheet.png`. Not installed; `actors.yml` needs attack impact 0.9083 and cast impact 0.35 for
PeasantF4 A/B/C when installed.

### Round 3 (user: "speed up the attack anim 2x")

`scripts/time_scale.py` resamples the built Attack at twice the speed (`work/clips_x1.blend` -> `work/clips.blend`,
`Attack:2`; 111 -> 56 frames, 0.933 s; blends, smoothing and twist bakes carried as built), then `build_runtime.sh`,
`build_pick.sh r74 v3` and `prune_materials.py` as before (the rest mesh is unchanged, so the ladder was not rerun).
Impact 0.458 s (gate blow 0.448 s, within one frame). Gates `gates/out_v6`: 7,179 PASS, 413 FAIL; the new failures are
the right arm's speed limits in Attack, as expected at this speed (step 35 deg per 60 Hz frame against 25, angular
acceleration 35,600 deg/s^2 against 20,000; about 1.4x would still pass). Blade lead -0.83 as before.
`actors.yml` on install: attack impact 0.4583, cast 0.35.

### Round 4 (user: "attack: some leg/hip movement also please")

The planted retarget held pelvis and legs at Standing. The source's own footwork is a 58 cm lunge step from a stance
17 cm lower (`work/slash4_free.blend`, `F_Slash4`: `retarget_mixamo.py :turn`), too much for an in-place attack, so
`build_clips.py` now takes it as an optional hip source (6th field) and applies a scaled hip drive with the feet
planted: the pelvis follows 25 % of the source's horizontal hip travel (max 14.7 cm toward the target), turns 40 % of
the chest's yaw change (max 11.8 deg; the spine counter-turns so the arm and blade path keep their world motion), drops
0.35 x the shift (5.1 cm, knees bend), and both legs are solved two-bone so the feet hold Standing's exact plant
(each leg's reach limit is at least Standing's own 0.98). Input `work/locked_hips.blend` (= locked.blend + F_Slash4):
`SMOOTH_PASSES=3 ANCHOR=0.4 BLEND_IN=0.3 blender -b -P scripts/build_clips.py -- work/locked_hips.blend
work/clips_x1h.blend C_MxSSSlash4:Attack:0.9:0.3:1.0:F_Slash4 K_RHand1:Cast:0.7:0.15:0.5`, then `time_scale.py
work/clips_x1h.blend work/clips.blend Attack:2` and the runtime/reduction chain as before. Gates `gates/out_v7`: same
counts as round 3 (no new failures: feet, cloth and grips unchanged); skirt check: Attack clean.
Sheet `review/attack_hips_sheet.png`; viewer updated (natf-v5, `check_viewer.mjs` 27 switches, no errors).

### Installed (2026-10-14, user: "accepted")

`tools/install_model.py --world mm6`: `../mm6_natf_reduce_claude/export/mm6_natf_v3.glb` as `mm6_natf.glb`,
`mm6_natf_blade_v3.glb` as `mm6_natf_blade.glb`, `mm6_natf_shield_v3.glb` as `mm6_natf_shield.glb`. `actors.yml`
PeasantF4 A/B/C: attack impact 0.4583, cast impact 0.35. Actors regression (`OPENYAMM_REGRESSION_FILTER=mm6_`):
`mm6_peasant_f4_actor_model_tiers_share_the_native_height` passes (the 3 failures are the guard, ooze and Free Haven
mage, unrelated). The blade's back-edge lead in the backhand sweep was accepted as is. Ledger rows in
`../REDUCTION_LEDGER.md`.
