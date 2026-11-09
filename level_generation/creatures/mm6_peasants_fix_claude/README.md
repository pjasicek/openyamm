# MM6 New Sorpigal peasants: fixes to the installed models — Claude project

The user rejected the rebuilt v4 female and v3 male (`mm6_pfem_v4_claude/`, `mm6_pman_v3_claude/`: heavy hair,
heavy far LODs) on 2026-10-30. They asked for this instead: "take the original male and FIX his shoulders. and the
original female and FIX her arms (can have the different idle pose). and leave it at that".

**Outcome (2026-10-30): only the male fix is installed.** After three review rounds on the female's arms, the user
had the original female reinstalled ("revert the female to original one, keep only the male changed").
`mm6_pfem.glb` and its regression durations equal HEAD again. Her work below stays as a record, with
`scripts/build_pfem.sh` as its replay; it is not installed.

The models were edited at the GLB level with numpy (`scripts/gltf_rig.py`). Mesh, LODs, textures, material variants
and the untouched clips stay byte-identical. There is no Blender re-export and no Meshy spend. The male is installed
under his old name (`mm6_pman_v2.glb`); `actors.yml` is unchanged from HEAD. The originals as installed before this
work are in `work/orig_*.glb`.

In game (New Sorpigal test spot, six tiers spawned): [far](review/ingame/peasants_far.png),
[near](review/ingame/peasants_near.png), [arm angle](review/ingame/peasants_arms.png),
[sleeves, close](review/ingame/peasants_close_crop.png); tour
`review/ingame/tour.yml`.

Rebuild the installed male with `scripts/build_pman.sh`; `scripts/build_pfem.sh` replays the uninstalled female work.
Both read the originals in `work/`, never the installed source (the male's already carries his fix).

## Male (`scripts/build_pman.sh`)

The rig's rest clavicles are level and symmetric. The clips dropped them: Standing L 4–11° and R 12–18° (lopsided),
Walking both 17–20°. They also rolled the clavicles 26–35° forward. `scripts/shoulder_fix.py` holds each clavicle
vector (clavicle head to upper-arm head) in an elevation band of rest −3…+6° and a forward band of rest ±8°. It
shifts the clip's mean into the band and keeps the motion, and clamps extremes 2° beyond the band. The upper arm keeps
its world rotation. Standing, Walking and Fidget are fixed. After the fix, Standing is −5…+0.5° elevation and −7…−5°
forward; Walking is −5…−1.5° elevation.

## Female (`scripts/build_pfem.sh`, not installed)

- **Standing**: Mixamo Standard Idle replaces the clasped-hands pose (`scripts/retarget_idle.py` from a
  `scripts/dump_fbx_clip.py` dump). Limb bones swing onto the source's segment directions. Spine, neck and head take
  the motion only, because the source rest leans. Hips and legs keep frame 0 of the old clip (skirt chains), and so
  do the skirt, braid and knife bones.
- **Fidget**: Mixamo Weight Shift (9.43 s). **Hit**: Standing React Large From Front (1.0 s). The old Fidget and Hit
  started from the clasped pose and would have popped.
- `shoulder_fix.py` on Standing, Fidget and Hit.
- **Arm angle** (`scripts/arm_pose.py`, Standing and Fidget): each arm hangs as one straight line, about 10° out
  from vertical in the front view.
  - Upper arm, forearm and hand are each set to 10°, 10° and 9°; the elbow bends 8° forward, the wrist is straight.
  - The clip's own motion is kept about these means.
  - The shoulders sit 15–16 cm from the centre line and the skirt is 18–21 cm wide at wrist height, so about 10°
    is what a straight arm needs to clear it.
  - Rejected first: the whole arm swung 8° out, which gave a stiff A-pose with the forearm and hand angled back in.
  - Rejected second: per-segment offsets (upper arm 5°, forearm 10°), which put the elbow in and the hand out.
    Both are in user reviews of 2026-10-30; the before-and-after sheet is `review/arms3/sheet.png`.
  - Clearance from the skinned final mesh: hand to skirt at least 8 mm in Standing and 3 mm in Fidget, with no
    vertex inside; upper arm to torso at least 9 mm. Measured with `work/gaps.py` and `work/skin_pose.py`.
- **Sleeves follow the arms** (`scripts/sleeve_weights.py`; review 2 on 2026-10-30, the user circled both arms).
  - The cause: the bind pose holds the arms 37° out and 18° back, and the shoulder vertices were split about half and
    half between the upper arm and the clavicle and spine.
  - So a hanging arm turned the puff sleeve only halfway: the arm slid out of the sleeve's inner edge, and the upper
    arm pinched under it.
  - The fix: the white sleeve and the arm skin below it move their torso-side weight onto the upper-arm bone, blended
    in from 10 cm above the arm head.
  - The armhole seam (within 3 cm of the bodice) and the chest skin keep their weights. Moving them pushed the sleeve
    top out through the bodice and notched the neckline.
  - LODs copy the nearest LOD0 vertex. LOD1 has eight influences, so a copied vertex clears its second set; the
    engine requires the weights to sum to one.
  - Every clip benefits: in Attack the old sleeve stayed flat at the shoulder while the raised arm came out of the
    bodice. Before and after: `review/arms2/clips_sheet.png`.
- **Thicker arms** (`scripts/arm_thicken.py`): skin vertices weighted to the arm are pushed along their normals.
  - Skin is detected by sampling the base-colour texture.
  - The push tapers: 14 mm below the sleeve hem, 6 mm at the elbow, 2 mm at mid forearm, 0 at the wrist.
  - The first version (11 / 6 / 9 / 9 mm) made the forearm as thick as the upper arm.
  - LOD and shadow meshes copy the nearest LOD0 displacement.
- Attack (knife), Walking, Death and Dead keep their animation.

## Checks

- `check_winding.py`: 0 inverted parts on both models.
- Regression: `mm6_pfem_actor_models_bind_town_peasants` (original female) and
  `mm6_pman_actor_models_bind_town_peasants` (fixed male) pass.
- `scripts/render_glb.py` gives EEVEE review renders of any clip frame.

## Gait rollout (2026-10-31)

The installed male (`mm6_pman_v2.glb`, with his shoulder fix) and the original female (`mm6_pfem.glb`) each gained a
`Jog` (Mixamo Running (5) legs, arms from their Walking with a bent elbow; the female's skirt chains follow her thighs
and are kept outside her legs), so their fleeing chase (2.5-2.7 units/s) no longer plays the walk at x1.7. Bindings
for the coordinator: `run: Jog`, `run_stride_length` 2.03 (male) / 1.54 (female). Details, gates and rebuild:
[package h04](../gait_rollout_20261031/h04/README.md) (`scripts/rebuild.sh pman_v2 pfem`, from the pre-gait copies in
its `work/`). A rebuild of either model here (or a far-LOD repair rerun) must re-graft these clips: rerun the h04
rebuild on the new source.
