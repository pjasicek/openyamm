# MM6 Dwarf (`dwa1`, BDwarf A/B/C: Dwarf / Dwarf Warrior / Dwarf Lord) reduction and arm repair (2026-10-14, installed)

User: "3D tris count reduction playbook - do dwarf". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_dwa1.glb` (11,563 tris, one merged body+head atlas material, three variants, eight influences;
Codex project `../mm6_dwa1_codex/`) and its held `mm6_dwa1_axe.glb` (2,119). Scripts copied from
`../mm6_fgt_reduce_claude/` with `REA_INFLUENCES=8` and the 1.41 m height (limits p99 4.23 mm, max 21.15 mm).
No Meshy credits.

## Body

The Codex pipeline already reduced the body with head and hands protected, so the cloth is thin and the head
(helmet, beard, hair, face, eyes: 4,497 faces, 39 %) is the dense part. Region labels: `scripts/dwarf_regions.py`
(bones, head atlas half, components), `scripts/dwarf_classes.py` (Codex material class maps: skin, hair, eyes, cloth,
metal), `scripts/hem_faces.py` (open-boundary bands, narrowed to the tunic and sleeve hems). `scripts/region_error.py`
prints rest-pose error per region and, with `REA_WHERE`, where it sits.

| config | tris | p99 / max mm | finding |
|---|---:|---|---|
| uniform 70 % | 8,093 | 3.2 / 10.5 | only passing step |
| uniform 60 % / 55 % | 6,937 / 6,359 | 4.4 / 12.2, 5.2 / 20.1 | yoke and sleeve studs and the eye domes melt |
| g1-g3: face/eyes/studs kept, hair, helmet, hands, boots each on its own ratio | 7,860-6,930 | 4.9-8.5 | worse: each group cut alone loses more than the shared collapse; the cloth (boot cuffs, trousers) takes the error |
| k1: eyes + small pieces (<= 80 faces: studs, rivets) kept, rest uniform 60 % | 6,937 | 5.3 / 20.1 | textured fine; clay face softer, tunic hem tabs blur |
| k2: + face skin and colour-detected trims kept (3,670 faces) | 7,631 | 7.0 / 30.0 | starves the cloth |
| k5: k1 + buckle + tunic/sleeve hems kept, rest 64 % | 7,399 | 5.0 / 20.1 | hems kept; beard widens a little at the mouth (alternative) |
| **k4: k5 + face skin decimated alone at 75 %, rest 66 %** | **7,629** | 6.1 / 20.9 | first pick (superseded in review round 1): moustache/beard edge and brow closest to the installed model |

`texture_drift.py r66`: no face above 40, p99 13; no lock round. Attack 27 and Fidget 6 (worst frames) render like
the installed model (`review/faces/s5_anim.png`); bracer rims are slightly more angular.
MeshLab's texture-aware collapse has no per-vertex quality weighting, so face protection is a separate decimation.

## Axe

Parts: grip wrap 857 (a geometric leather spiral), blade 242, socket 156, three collars ~120 each, two end caps
105/132, shaft 123, rivets 53/55, rear spike 32. Cutting the blade chipped its crescent edge and transferred normals
smeared it; the wrap at 50 % (609; its open strip edges stop the collapse) turned ragged under the fist (a1-a3).
**Pick `a4` (1,677)**: blade, wrap, shaft, spike and rivets exact; socket 50 %, collars and caps 40 %; normals by angle
(35 degrees). LODs 1,677 / 1,248 / 470 / 149. Grip gate (`scripts/grip_gate_posed.py`, radius 15.84 mm, every 2nd frame
of six clips): installed 8 hand vertices per frame inside the handle (nearest 4.5 mm from the axis), reduced 2
(nearest 12.1 mm); `review/props/grip_sheet.png` shows the same grip.

## Review round 1: detached sleeve, jagged fingers (sleeve repair superseded in round 2)

User (viewer, Attack wind-up): the right arm looks detached at the sleeve; the right fingers, mainly the thumb, are
jagged with black triangles. Reproduced at Attack 14 (`review/arm/sheet_a14.png`, installed above, first pick below).
- **Sleeve: already in the installed model.** The Codex shirt keeps 20-80 % Spine/Spine1/Pelvis weight down to the
  sleeve hem (the inner half, facing the chest, is mostly torso), and the separate elbow skin piece (z 0.67-0.90 m,
  112/115 vertices) is rigid on UpperArm/Forearm while the pieces covering its rims use the twist bones. Raising the
  arm leaves the sleeve behind and pulls the elbow piece's rim out of it.
  `scripts/rim_gate.py` pins each rim vertex to its cover face at rest and measures the drift over every 2nd frame
  of every clip: installed p95 108-117 mm (top rims), 21-42 mm (bottom rims), max 244 mm.
  `scripts/fix_arm_weights.py` repairs `work/source.blend` (original `work/source_orig.blend`): sleeve weights fade
  to their arm part (Clavicle/UpperArm/UpperArmTwist) by geodesic distance from the hem (full within 6 cm, original
  by 14 cm; hem seeds are the shirt vertices over the elbow piece's top rim, since the right hem is not an open loop
  after the weld); studs copy their nearest sleeve vertex; the elbow piece's rims copy their covers (sleeve above,
  forearm piece below), fading into its own elbow weights 1-5 cm from each rim. 676 vertices changed. A weight
  threshold or an arm-axis rule caught the torso side under the armpit (22-29 cm errors); the geodesic rule does not.
  Result: rim drift p95 0.3-1.9 mm, max 9.3 mm (`work/rim_gate_k9r72.json`); `review/arm/sheet_fix.png`.
- **Fingers: from the first pick.** The hands were in the shared cut. Keeping both whole hands starved the cloth
  (p99 8.8 mm at 8,093), so only finger-weighted faces (907) and the bracers (462, whose top rims went jagged) are kept.
- `reduce_ladder.py` now has the Genie's piece-aware weights (`REA_PIECE_WEIGHTS`); `scripts/weight_mix.py` found 19
  mixed vertices in the first pick, one on the elbow piece.
- One drift-lock round (`drift_lock.py`, 3 faces above 40 on the elbow piece and the helmet top) -> `keep_k9`;
  1 face left (0.8 cm2).

## Review round 2: torn triceps and armpit

User (viewer, Attack from frame 12): the upper arm tears or twists and drags part of the lats with it
(`review/arm/sheet_user_view.png`, middle row). Both came from the round 1 repair, not from the decimation:
- the hem seeds (shirt vertices within 2 cm of the elbow piece's top rim) included the torso side, which lies
  against the inner sleeve in the rest pose, so torso vertices went fully onto the arm;
- the elbow piece's top rim took the sleeve's UpperArmTwist weights while its middle stayed on UpperArm, so the
  twist roll pinched a band across the triceps.
The original weights run as a continuum from the outer sleeve (about 80 % arm) to the torso under the armpit
(`work/radial.py`: no radial or weight gap), so any hard sleeve/torso split tears. Bone heat on the mesh fails
(separate shells); on a voxel proxy it leaks across the hanging arm (thigh weight in the armpit).
`scripts/fix_arm_weights.py` (v2; v1 kept as `work/fix_arm_weights_v1.py`):
- blend factor (0 = original, 1 = arm part only) as a harmonic field (Jacobi iterations of the graph Laplacian)
  over the shirt, fixed at 1 on the outer half of the sleeve below s = 0.45 and at 0 on the torso (|x| < 0.13 m or
  s < 0.1);
- the elbow piece's UpperArm weight moves to UpperArmTwist (it rolls with the sleeve); its bottom rim copies the
  forearm piece as before; its top rim no longer copies the shirt;
- studs only when their host surface is the shirt (a yoke stud with shirt weights split in Death), one rigid
  weight set per stud;
- writes `work/arm_blend.npy`.
Rim drift on the repaired source: top p95 12-15 mm (the inner rim stretches with the armpit), bottom 1.9 mm.
The decimated shirt turned the smooth blend into coarse steps again (armpit tears in clay, `k10`), so the repaired
area (every shirt face with blend > 0.01), both elbow skin pieces and the yoke are kept exactly (`keep_k12`); the
split yoke stud in Death 10 was a decimation artifact already in the first pick.
Checks: `review/arm/sheet_k13.png` (rows installed, repaired source, final; Attack 16/24 and Death 10, textured and
clay), `review/arm/sheet_user_view.png` (your view, Attack 12-16: installed, round 1, final).

## Result (installed 2026-10-14, user accepted)

`export/mm6_dwa1.glb` (= `mm6_dwa1_k13r76.glb`): built from the round 2 source; arms, shoulders and armpit (repaired
area), yoke, eyes, studs, buckle, hems, fingers and bracers kept exactly, face skin 75 %, the rest 76 %. LODs 8,785 /
4,392 / 1,551 / 498 (installed 11,563 / 5,938 / 2,091 / 629), shadow LODs rebuilt, variants on all 8 primitives,
WEIGHTS_0+1 sums within 1.2e-7, 57 joints and inverse binds identical, eight clips. Ladder p99 6.1 mm / max 27.3 mm
(the boot tops inside the fur cuffs and the sole edges); texture drift one face above 40 (0.8 cm2). Rim gate equals
the repaired source. `export/mm6_dwa1_axe.glb` (= `mm6_dwa1_axe_a4.glb`, unchanged). LOD0 with the axe
13,682 -> 10,462 (-24 %). Grip gate: 4 hand vertices per frame inside the handle radius (installed 8).
Review: `review/arm/sheet_k13.png`, `sheet_user_view.png`, `sheet_final_arm.png`, `review/faces/s8_tex.png`,
`s8_anim.png`, `review/props/axe_compare.png`. Viewer `review/viewer/` (installed vs pick per variant;
`check_viewer.mjs` 48 switches, no console errors). Superseded picks are in `work/candidates/` and `export/`.

Installed with `tools/install_model.py export/mm6_dwa1.glb --world mm6` and the same for the axe. The first install
failed `mm6_dwarf_actor_model_tiers_follow_sprite_scales` (tiers 134.6 / 145.0 / 155.4 units, 7 % short; the
installed model passes): picking bounds use the coarsest LOD, and the default LOD2/LOD3 collapsed the 8 cm helmet
spike (top 1.40 -> 1.32 m). Higher LOD ratios do not keep it (LOD3 1,113 still 1.327 m).
`scripts/build_lods_keep_spike.py` (now in `build_pick.sh`) runs `tools/build_actor_lods.py` with an inverted vertex
group on the spike and its collar in each decimate modifier: same triangle counts, every LOD 1.401 m. Reinstalled,
`OPENYAMM_REGRESSION_FILTER=actor_model ... actors`: 53 pass, the dwarf case included; the 3 failures are the
guard, mage and ooze cases unrelated to this model. The spikeless-LOD build is `work/candidates/
mm6_dwa1_k13r76_spikeless_lods.glb`. Rollback (install these): `work/mm6_dwa1_source_pre_reduce.glb`,
`work/mm6_dwa1_axe_source_pre_reduce.glb`.

## Gait rollout — 2026-10-31

The [gait rollout package h02](../gait_rollout_20261031/h02/README.md) appended Walk2 (0.76 s, stride 1.0824), Run2 (0.64 s, 2.1061) and Sprint (0.53 s, 3.0936) to the installed
`assets_source/worlds/mm6/models/mm6_dwa1.glb` (existing clips, meshes, skins and materials byte-identical; installed
with `tools/install_model.py`). Bindings for BDwarf A/B/C, applied by the rollout coordinator from
`../gait_rollout_20261031/h02/bindings.yml`: walking: Walk2, run: Run2, sprint: Sprint (BDwarf C wandered at x1.53 on Walking; Standard chase played Running at x1.8-2.0, MAW at x4). Every tier passes `gait_gate.py` under Standard and MAW.
Rebuild: `../gait_rollout_20261031/h02/scripts/rebuild.sh dwa1` (from the pre-gait source kept in
`../gait_rollout_20261031/h02/work/`). Any later re-export of this model, including a far-LOD repair rerun
(`../lod_repair_claude/`) or a floor fix, starts from a source without these clips unless it starts from the installed
one: re-graft them (rerun the rebuild on the new source) and keep the bindings.
