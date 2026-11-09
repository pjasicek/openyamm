# MM8 Wererat, rat form (`m452`, Wererat Rat Form Male A/B/C) reduction (2026-10-19)

User pick for the next reduction batch. Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md),
no-retexture branch: no part needed rebuilding, so the installed textures stay valid. No Meshy credits. Scripts are
copied from `mm8_m468_reduce_claude/` and `mm8_m592_reduce_claude/` (parent fix, exact source weights, UV-based
weights, error lock); `close_rat.py`, `glb_close.py`, `build_lods.py` and `make_groups.py` are adapted to the rat.

Source: the installed `assets_source/worlds/mm8/models/mm8_m452.glb`, byte-identical to `../mm8_m452_claude/export/`,
copied to `work/mm8_m452_source_pre_reduce.glb` (rollback source). One material (`Rat_Palette452`, base colour,
normal and ORM maps), one `Rat` node, 24 bones, 4 influences. The three tiers share the texture and differ only in
scale (1 / 1.25 / 1.5): there are no colour variants or region ramps.

Pieces: one body with head, paws and tail (6,424 faces), the two eyes (58, 48), a detached paw piece (18), four
incisors (12 each) and six single-triangle whiskers.

## Ladder

Weld 5,236 -> 152 open edges (unchanged by every step). Limits are scaled to the 0.69 m body length without the
tail (nose to rump; with the tail the bound is 1.0 m): p99 2.07 mm, max 10.35 mm.

Region budgets (`make_groups.py`, dominant bone):
- **Kept exactly:** every piece other than the body (eyes, incisors, whiskers, the paw piece).
- **Head and jaw:** 70 %.
- **Front and hind paws:** 55 %.
- **Tail:** 80 %.
- **Body:** fills the rest.

| step | weights | locks | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| g2 | UV | pieces | 4,620 (70 %) | 3.77 / 32.6 | 0.982 | 0.993 | fail |
| g3 | UV | pieces | 5,938 (90 %) | 1.06 / 17.1 | 0.996 | 0.998 | fail (max) |
| e1 | UV | + error lock | 4,620 (70 %) | 2.51 / 10.8 | 0.990 | 0.996 | fail |
| e2 | UV | + 2nd error lock | 4,752 (72 %) | 2.61 / 16.5 | 0.990 | 0.995 | fail |
| **s2** | UV | e1 + snout spot | **4,950 (75 %)** | **1.96 / 9.16** | **0.991** | **0.996** | **picked** |

- **Weights:** a nearest-face transfer (first run) failed even at 70 % (p99 4.8, max 20.7 mm). UV weights
  (`uv_weights.py`, `REA_WEIGHTS=component`) helped little on their own.
- **Error lock:** the large errors came from source vertices with odd weights: Head-weighted vertices in the
  shoulder hump, and flank vertices with Spine3/Thigh weights that move away from their neighbours in Walking, Attack
  and Death. Even the 90 % step missed them by 17 mm. `err_lock.py` (Cand_80, over 6 mm, 12 mm radius) keeps 544
  faces around 78 such vertices.
- **Second lock round:** as the playbook warns, it moved the error elsewhere (e2 is worse), and so did a ten-spot
  sliver lock (s1: 75 % at p99 2.34). One round plus a single snout spot (s2) is the pick. 73 % fails (p99 2.10).
- **Worst point:** at 75 %, the 9.2 mm maximum is a cheek vertex on the right side of the head in Running frame 0
  (`probe_err.py`). It is not visible in the close-ups.

Close-ups of `work/ladder_s2.blend`, source vs 75 %:
- `review/close/sheet_r75_tex.png` and `sheet_r75_clay.png`: face front, three-quarter and both sides, ears from
  above, the Attack bite, all four paws, tail root and tip, back, flank, belly, Death, Running and Walking;
- `review/close/sheet_r75_mouth.png`: muzzle side and front, open mouth from both sides, soles.

The welded `source.blend` showed a light, faceted patch on the snout bridge between the eyes in the candidate. It
stayed even with those faces kept exactly, and it is not in the GLB renders. It is the weld's custom-normal artefact
the playbook describes, so it does not need a fix.

Texture checks:
- **Drift (`texture_drift.py`):** two faces over 40 (0.4 cm² in all).
- **Slivers (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`):** 10 dark and 7 light hits. They are under 0.6 cm²
  each, at the lip line and on the toe soles. Close-ups and GLB renders show no change there.

## Build

`export_cand.py` (Cand_75 of `work/ladder_s2.blend`, REA_NODE=Rat) -> `swap_lod0.py ... Rat` -> `build_lods.py` ->
`shrink_shadow_lods.py` (the installed model's own step, from `mm8_m452_claude/scripts/`): `export/mm8_m452.glb`,
10.3 MB (installed 10.5 MB). Textures, material, clips and node structure are unchanged.

`build_lods.py` settings:
- **Ratios:** 0.5 / 0.24 / 0.08 of LOD0 (`REA_LOD_RATIOS`). The creature's own 0.5 / 0.18 / 0.06 gave a 292-triangle
  LOD3 with a wedge at the tail root and a flattened hump (`review/lods/`). These ratios match the installed far LOD
  counts.
- **Protected points:** 121 points, the bounding extremes (top, both sides, nose and tail tip, 5 mm) and LOD0
  vertices within 4 mm of the floor in any Death/Dead frame. 1 cm caught the whole belly of the belly-down corpse.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 6,602 | 3,301 | 1,182 | 391 |
| reduced | **4,950** | 2,475 | 1,184 | 390 |

`lod_check.py` (REA_NODE=Rat) on every LOD:
- the bounds of LOD0 are kept: 1.0 m long, 0.26 m wide, 0.328 m high;
- no face stretches in any clip;
- the lowest point is the same at every LOD: Walking -4.7 mm (as installed), every other clip +0.2 mm. The installed
  LOD2 and LOD3 floated 2.3 and 4.1 mm.

`review/lods/sheet.png` compares all LODs at rest and in the Attack lunge. LOD3 is as blocky as the installed LOD3,
with a slightly flatter hump.

Regression `mm8_wererat_animal_actor_models_keep_native_sizes_and_motion` requires three colour LODs; the export
keeps them.

## Normals and texture

Straight from the GLBs (`glb_close.py`, `review/glbclose/sheet_tex.png`, `sheet_clay.png`), the installed model and
the reduction shade the same: plain smooth, with no sharper head shading. The head, muzzle, ears, bite, back, flank,
paws and tail root match.

**No retexture or local fix needed.** The single texture serves all three tiers, so there is no ramp to check.

Faults that are already in the installed model:
- small dark flakes on top of the head between the ears (geometry folds in the source, visible in clay too);
- the dark mottling of the fur, which is painted.

## Animation (unchanged)

`../mm8_m604_reduce_claude/scripts/bone_velocity.py` on Attack, which is also the bound Cast clip: 1.0 s, keys at
24 Hz, contact at 0.65 s.
- **Start:** no dead start. The body moves from the first key (95 deg/s at 0.04 s, 225 at 0.08 s).
- **Push-off jolt:** the hind legs snap at the leap. The shins rise 456 -> 915 deg/s at 0.458 s, then stop within
  one key at 0.50 s.
- **Re-plant:** the hind legs pick up again from 110 to 623 deg/s at 0.708 s.

At 24 Hz these are one-key changes. Left as is, since the clip was out of scope.

## Viewer

`review/viewer/`: installed / reduced for tiers A, B and C (scale 1 / 1.25 / 1.5), opening on the reduced tier A in
Attack. Native reference frames come from `mm8_packed_outline_collection_20261002/`. `run_creature_review.py check`:
48 switches, no console errors. `check_winding.py`: 0 inverted closed parts.

## Status

Installed 2026-10-19 (user: "wererat - ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_wererat_animal ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_wererat_animal_actor_models_keep_native_sizes_and_motion` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m452_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce:
1. `REA_NODE=Rat REA_GLB=<rollback source> import_source.py`;
2. `dump_mesh.py`, `dump_faces.py`, `make_groups.py`, `dump_weights.py`;
3. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.85,2:0.7,3:0.7,4:0.9 run_ladder.sh g3 0.9,0.8`;
4. `REA_CAND=Cand_80 REA_ERR_MM=6 REA_LOCK_R=0.012 err_lock.py -- work/keep_base.npy work/keep_e1.npy`;
5. `spot_lock.py work/keep_e1.npy work/keep_s2.npy 0.012 0.004,-0.422,0.216`;
6. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_s2.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.55,3:0.55,4:0.8 run_ladder.sh s2 0.76,0.75`
   (`run_ladder.sh` defaults to `REA_HEIGHT_M=0.69`);
7. `close_rat.py`, `pair_sheet.py`, `texture_drift.py r75`, `dark_slivers.py r75`;
8. build as above;
9. `lod_check.py`, `LOD_SCALE=1.15 LOD_CZ=.16 LOD_ATTACK_F=16 lod_views.py`, `glb_close.py`.

## Gait pass: Walk2 and Run2 (2026-10-21)

The game plays a gait one loop per stride of travel. The installed Walking (0.30 m per 1 s) and Running (0.43 m per
0.625 s) played 1.5-2.0x wandering and 2.9-4.0x chasing, because m452 wanders at 1.00-1.38 and chases at 1.99-2.76
model units/s (`gait_gate.py --world mm8 --model mm8_m452.glb`: walk target 1.17, run 2.34). The rat's legs are short
(front chain 0.147 m, shoulder 0.165 m up), so the stride grows only as far as the planted feet reach. The rest of the
speed comes from cadence and a gait change. Two new clips are keyed at 48 fps on the master
(`../mm8_m452_claude/scripts/anim_gait2.py`):

| clip | length | stride | speed | gait |
|---|---:|---:|---:|---|
| Walk2 | 0.3125 s (15 f) | 0.365 m | 1.168 | quick trot: diagonal pairs, hind foot 0.05 of a cycle behind its front foot, duty 0.52 (always a foot down), shoulders 2.5 cm lower and front footholds forward for reach, body bob, tail streaming |
| Run2 | 0.3333 s (16 f) | 0.78 m | 2.34 | half-bound: hind feet land almost together (0 / 0.06, duty 0.30), extended flight, staggered front feet (0.44 / 0.52, duty 0.25), gathered flight; the spine arches at hind touchdown and stretches in the extended flight, the hips slide back through hind stance |

Planted feet stay within 0.97 of each leg's chain length (`work/gait2_report.json`, in the master project); lowest
point -4.4 mm (Walk2) and -2.8 mm (Run2). The existing clips are unchanged.

Build: `anim_gait2.py` (writes `../mm8_m452_claude/work/rat_gait2.blend` and the donor export `work/gait2_donor.glb`;
its Walking, Running and Attack keys match the installed ones exactly) → `../mm8_m452_claude/scripts/add_clips.py
work/mm8_m452_pre_gait2.glb <donor> export/mm8_m452.glb --clips Walk2 Run2` (the pre-pass export, byte-identical to
the installed source, is the rollback). Gate:

```
gait_gate.py --world mm8 --model mm8_m452.glb --candidate export/mm8_m452.glb --set walking=Walk2 --set run=Run2 \
  --set stride_length=0.365 --set run_stride_length=0.78
  Walk2  measured 0.363 feet 0.365 trusted     Run2  measured 0.766 feet 0.774 trusted
  A wander Walk2 x1.18 chase Run2 x1.18 · B x0.99 / x0.99 · C x0.85 / x0.85 · floor ok · PASSED
```

`check_winding.py`: 0 inverted. The focused regression passes. Viewer (`review/viewer/`, the reduce-1 manifest kept as
`manifest_reduce1.json`) shows the new export for the three tiers with old and new clips; recordings at 1x and 0.5x
are in `review/playback/` (`Walking`/`Running` against `Walk2`/`Run2`). Blender side and three-quarter frames:
`../mm8_m452_claude/review/gait2/`. Installed 2026-10-21 (source sha256 `5d2c528b…`). The binding change
(`walking: Walk2`, `run: Run2`, `stride_length: 0.365`, `run_stride_length: 0.78`) is left to the coordinator.

Open point: at the gathered pose of Run2 the arched back shows a shallow fold over the Spine1/Spine2 joint. It is
visible in close side views, not at game distance.

## Sprint (2026-10-31)

The engine now takes an optional third locomotion clip (`animation.sprint` with `sprint_stride_length`), chosen by the
same misfit logic as walk and run. MAW makes m452 chase at 2.83-4.14 model units/s (Standard: 1.99-2.76), so Run2
would play up to 1.77x. `gait_gate.py --world mm8 --model mm8_m452.glb` gives a sprint target of 3.23 (fits 2.76-3.77).
One new clip, `Sprint`, keyed on the master by `../mm8_m452_claude/scripts/anim_sprint.py` (anim_gait2.py unchanged):

| clip | length | stride | speed | gait |
|---|---:|---:|---:|---|
| Sprint | 0.3542 s (34 keys at 96 fps) | 1.17 m (1.5x Run2) | 3.30 | full bound: Run2's footfall phases (HL 0, HR 0.06, FL 0.44, FR 0.52), so a walk/run/sprint switch on the shared gait phase does not jump; lower duty (hind 0.22, front 0.19), extended flight 0.28-0.44 and gathered flight 0.71-1.0; spine -16 to +28 deg (stretched to arched, more in the chest than over the hips), hips and chest slide back over the planted feet in both stances and surge forward in both flights (the body lifts 3 cm in the gathered flight), front paws kick back and tuck then reach forward, hind paws trail then swing under the belly |

Cadence is 0.94x Run2's: with the 3.23 target, a 1.5x stride leaves no room for a higher cadence. The extra stride comes
from the body sliding over the planted feet (the front chain is 0.147 m). Planted reach is at most 0.964 of each
leg's chain. Swinging paws curl their toes down only as far as their lift clears (`floor_pitch`). It is keyed at
96 fps because at 48 fps the planted legs' linear in-between rotations dipped the paws 6 mm under the floor. Lowest
point: keys +0.2 mm, quarter-key samples -1.7 mm (Run2: -2.6 / -3.6 mm). Up to 7.8 mm off the floor in the flights,
which is intended.

Build: `anim_sprint.py` (writes `../mm8_m452_claude/work/rat_sprint.blend`, saved at 96 fps, and the donor
`work/sprint_donor.glb`) → `add_clips.py work/mm8_m452_pre_sprint.glb <donor> export/mm8_m452.glb --clips Sprint`.
The pre-pass GLB is the installed far-LOD repair (`../lod_repair_claude/export/mm8_m452.glb`, sha256 `1f02043f…`) and
is the rollback. Every existing clip, node, mesh, skin and material is unchanged (compared accessor by accessor).
Gate:

```
gait_gate.py --world mm8 --model mm8_m452.glb --candidate export/mm8_m452.glb --set sprint=Sprint \
  --set sprint_stride_length=1.17
  Sprint  measured 1.162 feet 1.163 trusted  binding 1.170
  standard A wander Walk2 x1.18 chase Run2 x1.18 · B x0.99 / x0.99 · C x0.85 / x0.85
  maw      A chase Sprint x1.25 · B chase Sprint x1.02 · C chase Run2 x1.21
  floor ok · PASSED
```

`check_winding.py`: 0 inverted. The focused regression passes. Viewer `review/viewer/` (sprint manifest; the gait-2
one kept as `manifest_gait2.json`): `run_creature_review.py check` passes, 11 clips, no console errors. Recordings at 1x and
0.5x in `review/playback/` (the gait-2 record moved to `playback/gait2_20261021/`), side shots of Sprint against Run2 in
`review/shots/`, Blender frames in `../mm8_m452_claude/review/sprint/`. Installed 2026-10-31 (source sha256
`bc3bdf20…`). The binding (`sprint: Sprint`, `sprint_stride_length: 1.17`) is left to the coordinator.

Open points: in-place playback shows Sprint as a clearly bigger bound than Run2, but not a dramatically different one.
The extra travel in the flights only shows in game. The gathered pose keeps Run2's fold behind the shoulder hump
(here no deeper than Run2's) and the small fin on the back.
