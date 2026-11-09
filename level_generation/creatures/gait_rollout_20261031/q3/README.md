# Gait rollout package q3: MM7 Manticore and Hydra, MM8 Gorgon and Thunder Lizard (2026-10-31)

Brief: [the rollout README](../README.md). Every new clip is procedural, grafted onto the **installed** source with
`../../claude_shared/graft_clips.py` (`graft_byte_check.py`: the old file is a byte prefix, every old mesh, skin,
material and clip unchanged). All four models are installed; the coordinator applies [bindings.yml](bindings.yml).

| model | body (by eye) | descriptors | new clips | binding |
|---|---|---|---|---|
| mm7_m278 | lion with scorpion tail, four legs | Manticore A-C | Walk2 | walking Walk2 1.6713 |
| mm7_m266 | sprawled five-necked lizard, four legs | Hydra A-C | Run2 | run Run2 1.62 |
| mm8_m564 | armoured bull, hooves with pasterns | Gorgon A-C | Walk2, Run2, Sprint | walking Walk2 0.512, run Run2 0.774, sprint Sprint 1.1247 |
| mm8_m516 | **two-legged** digitigrade dinosaur (the ledger's "multi-legged" is wrong) | Thunder Lizard A-C | Walk2, Run2, Sprint | walking Walk2 1.988, run Run2 3.414, sprint Sprint 4.8285 |

Only the Gorgon and the Thunder Lizard change speed under MAW, so only they get a sprint.

## Scripts

- `scripts/quad_gait.py` (Manticore, Hydra). This is a copy of `../q2/scripts/quad_gait.py`: toe planting, two-bone
  IK, heel lift at push-off, footholds planned against reach. It adds:
  - a `manticore` style: `anim_manticore.py`'s scorpion tail, rolled into the middle plane;
  - a `hydra` style: `anim_hydra.py`'s eight-segment tail, its five necks with the mesh-overlap head separation, its
    tail and neck floor clamps, its leg poles and symmetric footholds.

  It also fixes one thing in q2's copy. q2 averaged the paws' contact points along the body onto the paw itself. On a
  skewed rest pose that put the pivot behind the real toe: the Manticore's right forefoot stands 27 cm ahead, and its
  claws dipped 7 cm under the floor. Now the contact stays on the paw and only the foothold is averaged. With a wide
  `contact_band` (claw tips), the paw's lowest rest vertex sits at `toe_clear`.
- `scripts/gait_m564.py` (Gorgon). It copies `animate_gorgon.py`'s legs: the IK, the pastern inclined toward the
  shoulder or hip, flat hooves and footholds under the shoulder or hip. Additions:
  - back flex, harmonics for rocking, bob and head nod;
  - in the swing, the hoof is raised by its tip's drop.
- `scripts/gait_m516.py` (Thunder Lizard). It copies `animate_lizard.py`'s machinery:
  - hip-knee-hock IK, with soles planted 8 mm above the floor on their measured vertices;
  - the torso shifting over the support foot;
  - the head steadied, and the tail and arms.

  It adds a per-side foothold `skew`: the rest hips stand 14 cm apart along the body, and equal footholds overreached
  by up to 8.6 cm.
- Probes:
  - `scripts/quad_probe.py`: q2's, with `--head` and `--paws` added for the Hydra's `Head3` and for hooves and bird feet.
  - `scripts/low_probe.py`: the lowest vertex per key and its joint.
  - `scripts/viewer_clips.py`: copies every clip of the export into the viewer's tier GLBs.
  - `scripts/viewer_page.sh` and `scripts/viewer_manifest.py`: q2's.

**Strides.** Strides follow dynamic similarity: Alexander's relative stride is 2.3 Fr^0.3 of the leg. The stance sweep
then stays near each model's installed walk, and the extra speed comes from cadence and flights.

## Per model

### Manticore (mm7_m278): Walk2

**Targets.** The Manticore wanders at 2.16-2.49 and chases at 4.31-4.98; MAW leaves these unchanged. Walking (1.59)
played ×1.57 on A. Target walk speed: 2.18 (fits 1.66-2.87).

**Walk2.** A lateral-sequence walk with the installed phases (hind L 0, front R .25, hind R .5, front L .75):
- 0.7667 s (46 keys at 60 fps), stride 1.6713, authored speed 2.18;
- duty 0.58, sweep 0.97 m, heel lift 35°;
- the body is 2 cm lower, which brings the left fore within reach (1.02 of the chain; worst toe miss 7 mm at touchdown).

The installed Walking reaches 1.20 of the chain: the IK clamps it.

**Gate** (window section):

| tier | wander | chase |
|---|---|---|
| A | Walk2 ×1.14 | Running ×1.39 |
| B | Walk2 ×1.05 | Running ×1.28 |
| C | Walk2 ×0.99 | Running ×1.20 |

MAW is the same. Stride: Walk2 1.671 / feet 1.669, trusted. Floor: ok. PASSED.

**Head bob** 3.4 %. Walking's is 6.9 %, mostly from its floor-fix ground loop.

**Paw toe-out while planted:**

| front L | front R | hind L | hind R |
|---|---|---|---|
| +12.5 | +5.0 | +17.6 | +10.3 |

These are exactly Standing's and Walking's.

### Hydra (mm7_m266): Run2

**Targets.** The Hydra chases at 2.03-2.58; MAW leaves the speeds unchanged. Running (3.17) misfit B and C, which
chased on Walking ×1.57. Target run speed: 2.16 (fits 1.72-2.71).

**Run2.** A slower trot:
- 0.75 s (45 keys), stride 1.62, authored speed 2.16;
- duty 0.5, sweep 0.81 m;
- Running's bob (4 cm), spine and tail; the necks stretched forward 12°.

**Phase.** Run2 strikes hind L + front R at 0, as Walking strikes hind L at 0. The installed Running is half a loop off
from the walk (front L + hind R at 0); Run2 follows the walk.

**Gate** (window section; MAW is the same):

| tier | wander | chase |
|---|---|---|
| A | Walking ×0.99 | Run2 ×1.19 |
| B | Walking ×0.79 | Run2 ×0.95 |
| C | Walking ×0.78 | Run2 ×0.94 |

Stride: Run2 1.620 / feet 1.615. Floor: ok. PASSED.

The tail's lowest point is -0.84 cm, as in Running (-0.81). The tolerance is 1.47 cm at A.

**Head bob** (Head3) 3.0 %. Running's is 3.5 %, Walking's 2.5 %.

**Paw toe-out while planted:**

| front L | front R | hind L | hind R |
|---|---|---|---|
| -4.2 | -2.0 | +6.0 | +15.0 |

These are the same as the installed clips.

### Gorgon (mm8_m564): Walk2, Run2, Sprint

**Targets.** Standard wanders at 0.62-0.75 and chases at 1.25-1.49. MAW chases at 2.49-2.62. Walking (0.48) and
Running (0.80) played the chase ×1.56-1.87 and MAW ×3.1-3.3.

**New clips** (60 fps):

| clip | length | stride | duty | gait |
|---|---|---|---|---|
| Walk2 | 0.80 s | 0.512 | 0.60 | lateral walk, Walking's phases (hind L 0, front L .25) |
| Run2 | 0.60 s | 0.774 | 0.40 | flying trot, hind L + front R at 0 as Running |
| Sprint | 0.4667 s | 1.1247 | 0.26 | transverse gallop |

- Sweeps are 0.29-0.31 m, like Walking's 0.30. Planted hoof miss: 0 mm.
- The Sprint's footfalls are hind L 0, hind R .1, front L .45, front R .55. It has one gathered flight, flexes its back
  8°, rocks the body 3.5° and nods the head down as the fronts land.

**Gate** (window section):

| tier | Standard wander | Standard chase | MAW wander | MAW chase |
|---|---|---|---|---|
| A | Walk2 ×0.97 | Run2 ×0.97 | Run2 ×0.97 | Sprint ×1.03 |
| B | Walk2 ×1.07 | Run2 ×1.06 | Run2 ×0.99 | Sprint ×1.06 |
| C | Walk2 ×1.17 | Run2 ×1.16 | Run2 ×1.01 | Sprint ×1.09 |

Stride (measured / feet, all trusted):
- Walk2 0.512 / 0.512
- Run2 0.774 / 0.773
- Sprint 1.125 / 1.119

Floor: ok. PASSED.

**Head bob.** Walk2 3.6 %, Run2 5.7 %, Sprint 11.0 %. Walking and Running read 3.6 %.

**Hoof toe-out** while planted: front 0.0, hind +10.5, the rest pose's.

### Thunder Lizard (mm8_m516): Walk2, Run2, Sprint

**Targets.** Standard wanders at 2.77-3.28 and chases at 5.55-6.56. MAW chases at 10.34-10.85. The installed Walking
(1.0) never played: wandering took Running (2.4) at ×1.15-1.37, and chasing played it ×2.3-2.7, MAW ×4.3-4.5.

**New clips** (60 fps). The hip is 1.05 m high.

| clip | length | stride | duty | Froude | gait |
|---|---|---|---|---|---|
| Walk2 | 0.70 s | 1.988 | 0.52 | 0.8 | grounded run, no flight (the walk role's floor rule) |
| Run2 | 0.60 s | 3.414 | 0.33 | | run with short flights |
| Sprint | 0.4833 s | 4.8285 | 0.24 | | long bounding strides, body pitched 18°, tail out |

- The left foot is down at 0, as in Walking and Running.
- Sweeps are 1.03-1.16 m.
- Worst IK error is 4.3 mm and the contact error 1.4 mm.

**Gate** (window section):

| tier | Standard wander | Standard chase | MAW wander | MAW chase |
|---|---|---|---|---|
| A | Walk2 ×0.98 | Run2 ×0.98 | Run2 ×0.91 | Sprint ×1.04 |
| B | Walk2 ×1.07 | Run2 ×1.06 | Run2 ×0.93 | Sprint ×1.06 |
| C | Walk2 ×1.15 | Run2 ×1.15 | Run2 ×0.95 | Sprint ×1.09 |

Stride (measured / feet, all trusted):
- Walk2 1.988 / 1.983
- Run2 3.414 / 3.392
- Sprint 4.828 / 4.746

Floor: ok. PASSED.

**Head bob** (`bob_audit.measure` on the candidate): Walk2 3.5 %, Run2 4.5 %, Sprint 4.0 %. Walking reads 1.5 %,
Running 5.5 %.

**Foot heading** (`quad_probe.py --paws Foot_L,Foot_R`; `foot_heading_probe.py` needs humanoid joint names): planted
toe-out L +8.9, R +9.9. These equal Standing's and the installed clips'.

## Gates run on every export

- `gait_gate.py`: PASSED (above).
- `graft_byte_check.py`: OK.
- `check_winding.py`: 0 inverted.
- `quad_probe.py`: bob and heading.
- `low_probe.py`: floor.
- Viewer: `tools/run_creature_review.py ... check` loaded every tier and clip with no console errors (27, 27, 33 and
  33 switches). Side, front and quarter shots of every new clip were looked at; they are in each viewer project's
  `review/shots/`.

| viewer project | revision | tier GLBs made by (unchanged) |
|---|---|---|
| `mm7_m278_reduce_claude` | `manticore-walk2-1` | `viewer_tiers.py` |
| `mm7_m266_reduce_claude` | `hydra-run2-1` | `viewer_tiers.py r78h5` |
| `mm8_m564_reduce_claude` | `gorgon-gait-1` | `viewer_tiers.py r55 work/r55_lod0.glb` |
| `mm8_m516_claude` | `lizard-gait-1` | `viewer_tiers.py` |

Each viewer's previous manifest is kept as `manifest_<old revision>.json`. In each, `scripts/viewer_clips.py` replaced
every clip with the export's, and `scripts/viewer_page.sh` added a page where there was none.

## Doubts

- **Foot toe-out.**
  - The Manticore's paws toe out 5-18°, the Gorgon's hind hooves 10.5° and the Thunder Lizard's feet 9-10°. All are
    over the brief's 5°.
  - Each is the rest pose and the accepted Standing and walks. The engine switches clips instantly, so the new clips
    keep them (as q2).
- **Thunder Lizard Walk2 is a grounded run.** It has no flight, because the walking role's floor rule requires a foot
  down. At Froude 0.8 a walk would look wrong.
- **Hydra Run2's phase.** Run2 strikes half a loop from the installed Running, following the walk. Running is no longer
  bound.
- **Gorgon Sprint head bob.** It is 11 % (Walking 3.6 %). The body pitches 3.5° and nods in the gallop. It is lower than
  the first try (15.8 %); compare q2's wolf gallop at 11.7 %.
- **Manticore Walk2's head bob.** It is 3.4 %, against Walking's 6.9 %. Walking's figure includes its floor-fix ground
  loop.
- **Hydra tail.** The tail dips to -0.84 cm, as in the installed Running.
- **Gorgon and Thunder Lizard MAW wandering.** Both wander on Run2 at ×0.91-1.01 under MAW. This is not gated, but it
  is inside the window.

## Problems found in tools

- **q2's `quad_gait.py` contact averaging.** See Scripts above; fixed in this copy only.
- **`gait_gate.py` sprint stride.** On a first Gorgon Sprint, the gate took the vertex measurement (0.999) as the
  stride, against the authored and foot 1.12; both were "trusted" within `AGREE` 0.12.
  - Cause: swing hooves skimming inside the contact band.
  - Effect: binding the gate's suggestion would have slid the planted feet 12 %.
  - Fixed in the clip (the swing hoof raised by its tip's drop), not in the tool. Check the suggested strides against
    the authored ones.

## Rebuild

From this directory:

```sh
blender -b --factory-startup -P scripts/quad_gait.py -- m278 work/m278_clips.glb      # Manticore Walk2
blender -b --factory-startup -P scripts/quad_gait.py -- m266 work/m266_clips.glb      # Hydra Run2
blender -b --factory-startup -P scripts/gait_m564.py -- work/m564_clips.glb           # Gorgon Walk2, Run2, Sprint
blender -b --factory-startup -P scripts/gait_m516.py -- work/m516_clips.glb           # Thunder Lizard Walk2, Run2, Sprint
G=../../claude_shared/graft_clips.py; S=../../../../assets_source/worlds
python3 $G work/rollback/mm7_m278.glb work/m278_clips.glb export/mm7_m278.glb --clip Walk2
python3 $G work/rollback/mm7_m266.glb work/m266_clips.glb export/mm7_m266.glb --clip Run2
python3 $G work/rollback/mm8_m564.glb work/m564_clips.glb export/mm8_m564.glb --clip Walk2 --clip Run2 --clip Sprint
python3 $G work/rollback/mm8_m516.glb work/m516_clips.glb export/mm8_m516.glb --clip Walk2 --clip Run2 --clip Sprint
python3 ../../../../tools/install_model.py export/<glb> --world <mm7|mm8> --name <glb>
```

The scripts read the projects' blends read-only:
- `mm7_m278_claude/work/anim_v2u.blend`
- `mm7_m266_claude/work/anim_v2.blend` (with `work/rig.json`)
- `mm8_m564_claude/work/anim_v1.blend`
- `mm8_m516_claude/work/rig_v1.blend` (with `work/rig.json`)

They save `work/<model>_gaits.blend`.

A far-LOD repair rerun (`lod_repair_claude`) rebuilds the GLB and must re-graft these clips.

**Rollback.** The pre-change sources are in `work/rollback/`. Install one with
`tools/install_model.py work/rollback/<glb> --world <w> --name <glb>`, then revert the q3 entries of `actors.yml`.

**Regressions covering these models** (headless outdoor suite):
- `mm8_gorgon_actor_models_keep_native_tiers_and_simulation`
- `mm8_thunder_lizard_actor_models_keep_native_tiers_and_biped`

Both check the eight original clips, which are kept. There is no case for the MM7 Manticore or Hydra.
