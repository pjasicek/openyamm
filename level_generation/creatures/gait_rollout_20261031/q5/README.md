# Gait rollout package q5: the MM9 wolf's Trot (2026-11-06)

Brief: [TASK.md](TASK.md), [the rollout README](../README.md). One model: `mm9_wolf.glb` (Grey Wolf 9114 = MM9 Wolf A,
scale 40; Red Wolf 9115 = B and Black Wolf 9116 = C, scale 50; project `../../mm9_wolf_claude/`). A procedural
`Trot`, grafted onto the **installed** source with `../../claude_shared/graft_clips.py` (`graft_byte_check.py` OK: the
old file is a byte prefix, every old mesh, skin, material, LOD, variant and clip unchanged), installed and bound.

| clip | gait | length | stride | authored speed | duty front / hind | sweep front / hind | lowest vertex |
|---|---|---|---|---|---|---|---|
| Trot | flying trot, front R + hind L at 0 | 0.3667 s (22 keys at 60 fps) | 3.04 model units | 8.29 units/s | 0.33 / 0.42 | 1.00 / 1.28 | +0.2 cm (no flight below floor) |

Binding (all three descriptors): `run: Trot`, `run_stride_length: 3.04`, `sprint: Running`, `sprint_stride_length:
4.18`; the walk stays `Walking` 1.96 ([bindings.yml](bindings.yml), applied by this package).

## The speeds (measured, not the MM6-MM8 table)

`gait_gate.py` reads monster_data.txt Spd, where the MM9 rows come out "stationary", so `scripts/wolf_gate.py`
takes MM9's profile speeds (`assets_dev/worlds/mm9/modifiers.yml` `mm9_ai`): Grey Wolf walk 358, run 742; Red and
Black Wolf 384, 768 world units/s. The AI wanders at walk_speed (`GameplayActorAiSystem.cpp`, "A wander walks at
MM9's walking speed") and chases at run_speed; the arenas confirm it: before the change every wolf `anim` line
moved at 358 (wander) or 742 (chase), slower only for single hindered steps (37-52) and the moving bite (683-729).
In model units/s: A wanders 8.95, chases 18.55; B and C 7.68 and 15.36. The trot's 8.29 is their geometric middle.

## Why run = Trot, sprint = Running

The engine (`actorModelGait`): misfit = log of the playback rate, doubled below 1; walk is preferred by log 1.25
when calm, run and sprint when hurrying. Clip speeds: Walking 2.18, Trot 8.29, Running 10.45 model units/s.

| tier, state | Walking | Trot | Running | plays |
|---|---|---|---|---|
| A wander 358 | 1.19 (x4.1, capped 2: slides) | **0.08** (x1.08) | 0.31 (x0.86) | Trot x1.08 (was Running x0.86) |
| B/C wander 384 | 1.04 (x3.5) | **0.15** (x0.93) | 0.62 (x0.73) | Trot x0.93 (was Running x0.73, outside 0.75-1.5) |
| A chase 742 | 2.14 (x8.5) | 0.58 (x2.24) | **0.35** (x1.78) | Running x1.78 (unchanged) |
| B/C chase 768 | 1.95 (x7.0) | 0.39 (x1.85) | **0.16** (x1.47) | Running x1.47 (unchanged) |

(Hurrying rows include the run/sprint preference.) Trot as `walking` instead would lose MM9's Walking for slow and
hindered steps (it would play the trot at x0.3-0.6 below 200 units/s); as `run` with Running as `sprint` the walk
keeps everything up to about 200 units/s (A) or 250 (B/C), the trot 200-400 / 250-480, Running above. The sweep in
`wolf_gate.py` prints the choice and rate every 50 units/s: the band where Walking was capped at 2 or Running crawled
at 0.57-0.72 (A 200-350, B/C 250-450) is now the trot at 0.6-1.1.

## Method (`scripts/wolf_trot.py`)

q3's `quad_gait.py` machinery mapped to the MM9 skeleton (its joints are points: every bone points up, so limbs are
solved by aiming each joint at its child's head):
- **Limbs.** Shoulder Bone11 / elbow Bone12 / wrist Bone13 / paw Bone19 (front L; Bone16-17-18-05 right), hip Bone01 /
  hock Bone02 / Bone03 / paw Bone09 (hind L; Bone06-07-08-42). Two-joint IK to the wrist / Bone03 with the elbow and
  hock behind; the two lower joints are a rigid foot carrying Standing's rotations, pitched about the side axis (heel
  lift 30 deg over the last 40 % of the stance, tuck 55 deg front / -10 deg hind in the swing).
- **Planting.** Each paw rolls over its claw tips (front-most vertex within 6 cm of its lowest one in Standing), so a
  heel lift sinks nothing. Footholds are Standing's, planned per limb so wrist/hock stay within 0.97 of the chain
  (worst 0.969). The fronts plant their lowest vertex at 0.2 cm, the hinds at 1.5 cm (Standing's hind paws stand 5 cm
  up; the body is 3.5 cm lower than Standing so the hind legs keep their Standing extension).
- **Carriage.** Every key starts from Standing's first key; hips Bone33 3.5 cm lower with a 6 cm bob twice a loop (low
  mid-stance), rocking 1.5 deg, back flex 2 deg, spine/chest yaw 2.5 deg, skull Bone27 steadied (head hold 0.5, 2 deg
  down), tail Bone34-24 lifted back 12 deg and swaying 7 deg. Skull mean height 1.900 (Walking 1.913), skull bob 3.7 %
  of its Standing height (Walking 2.5 %, Running 11.8 %).
- **Front duty shorter than hind** (0.33 / 0.42): at equal duties the hind paw brushed the front paw on its side as
  the front lifted off (hind-foot vertices inside the front paw's hull: 88; 0.3-0.8 cm skin clearance), and no wider
  or later hind foothold cured it. With the fronts up earlier the clearance is 10.4 / 11.7 cm, 0 vertices inside
  (`scripts/paw_clash.py`; the installed Running has 55 inside, 0.9 cm). It also shortened the front sweep, which
  brought the front reach from 0.986 to 0.969 of the chain.
- **Floor pass.** As the wolf's `build_runtime.sh` and `extra_clips.sh` floor their clips (`scripts/finish.sh`): the
  tail chain lifted first (`--lift-joints Trot --lift-only Bone34,...,Bone24`), then `--raise Trot`; neither changed a
  key (`compare_clips.py`: 0.0000 deg, 0 cm).

## Gates (all on `export/mm9_wolf.glb`)

- **Phase** (`scripts/wolf_probe.py`): Walking strikes front R at 0.97 and hind L at 0.00, front L 0.45 and hind R
  0.55 (a diagonal-sequence walk); Trot front R 0.97-0.98 and hind L 0.00, front L 0.47-0.48 and hind R 0.50. Running
  (now the sprint) leads with front L at 0, as before: that mismatch with Walking is MM9's own and unchanged.
- **Paw heading** relative to Standing while planted: Trot 0.0 on every paw (the foot keeps Standing's rotation);
  Walking -1.7..+0.7 mean (-4.6..+4.4). Front view: paws point along travel, no splay.
- **Stride:** binding 3.04; floor vertices 3.040 (`stride_audit.py`, contact 73 %); paw joints 2.75 (the joints move
  forward as the heel lifts, as on every rollout trot). Walking 1.96 and Running 4.18 unchanged.
- **Loop seam** 0.0000 (`scripts/trot_gates.py`), edge ratio p1/p99 0.60/2.19, max 4.54 (Running 0.57/2.41, 4.65).
- **Floor:** `floor_audit.py --world mm9` Wolf A/B/C ok (installed binding, sprint included); lowest +0.2 cm.
- **Winding:** `check_winding.py` 0 inverted closed parts. Regression `mm9_actor_models_build_every_binding`: 252
  descriptors on 114 models, 0 failed.
- **Window** (`scripts/wolf_gate.py`): wander A x1.08, B/C x0.93; chase B/C Running x1.47. **A's chase stays at
  Running x1.78**, outside 1.5 as before: the trot does not touch it (see Open).

## Viewer and arenas

- Viewer `../../mm9_wolf_claude/review/viewer/` (revision `q5_trot_20261106b`; the previous manifest and GLBs are in
  `work/viewer_backup/`): `run_creature_review.py check` 30 switches, 0 console errors. Shots, looked at:
  `review/viewer_trot_left.png` (8 phases, side), `review/viewer_trot_front_quarter.png` (front, paw close-ups),
  `review/viewer_trot_black_wolf.png`; Blender strips `review/strip_Trot_v1.png` (first version) and
  `review/strip_Walking_v1.png`. Paws planted and pointing forward, elbows and hocks behind, no inversion, tail above
  the floor, the folded fore-paw clears the hind paw.
- Arenas (`tests/scenarios/mm9/ai/` patrol, crawler, alarm, flee, factions, give_up, retarget, copies with
  `trace_animation`; plus a scratch arena with 9115 and 9116): all pass before and after. Wolf gait lines before:
  `Running speed=358` (wander, x0.86), `Running speed=742`; after: `Trot speed=358` / `Trot speed=384` while
  wandering, `Running speed=742` / `768` while chasing (the 0.3 s gait hold shows one Trot line at 768 before the
  switch, as it showed Walking before).

## Install

- `tools/install_model.py export/mm9_wolf.glb --world mm9`; the runtime copy is a new inode, so the review roots'
  links (`output/mm9_rework/assets_dev/...`, `output/mm9_rework/isleofashes_blv_root/...`) were relinked to it (only
  this file; `review_root.py` refresh was not run, it would also relink actors.yml).
- actors.yml edited in place under `flock -x ../../claude_shared/locks/mm9_actors_yml.lock`. On 2026-11-06
  `assets_dev/worlds/mm9/models/actors.yml` and both review-root copies were one inode (3 links), so the edit reached
  them; the brief's `cat assets_dev/... > output/...` step was skipped, because on the same inode it would have
  truncated the file.

## Open

- **Grey Wolf chase x1.78.** Running (4.18) is the longest stride on the model; A's chase (742 at scale 40) needs a
  clip of about 16.9 model units/s (a gallop of stride about 6.8 at 0.4 s, or a sprint with longer flights) to play
  inside 1.5. B/C chase at x1.47.
- Running leads with the other diagonal than Walking and the Trot (MM9's data). Switches happen at the shared phase
  with the 0.12 s blend, as they did between Walking and Running.
- The rollout's composite viewer (`../viewer/`) and `ledger.py` do not read MM9 speeds; not rebuilt.

## Rebuild

From this directory (lease: `tools/creature_workspace.py claim --project level_generation/creatures/gait_rollout_20261031
--identity mm9:wolf_trot --state q5/creature_3d_progress.json`, released after this run):

```sh
# from the repository root:
tools/run_creature_blender.sh --token <token> level_generation/creatures/gait_rollout_20261031/q5/scripts/wolf_trot.py \
  $PWD/level_generation/creatures/gait_rollout_20261031/q5/work/wolf_clips.glb       # reads mm9_wolf_claude/work/anim_v3.blend
# then from this directory:
scripts/finish.sh                       # floor pass, graft onto work/rollback/mm9_wolf.glb (SRC=... for another base)
python3 scripts/wolf_gate.py export/mm9_wolf.glb --set run=Trot --set run_stride_length=3.04 \
  --set sprint=Running --set sprint_stride_length=4.18
python3 scripts/wolf_probe.py export/mm9_wolf.glb Walking,Trot; python3 scripts/paw_clash.py export/mm9_wolf.glb Trot
python3 scripts/trot_gates.py export/mm9_wolf.glb Trot
python3 scripts/viewer_trot.py export/mm9_wolf.glb <revision>
(cd ../../../.. && python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/q5/export/mm9_wolf.glb --world mm9)
```

`QG_SET="Trot:key=value,..."` overrides clip parameters for trials. **A rebuild of the wolf** (its `build_runtime.sh`,
`extra_clips.sh` or a far-LOD repair) rewrites the GLB from the project blend and drops the Trot: run `scripts/finish.sh`
with `SRC=<the new export>` and reinstall; its `bind_actors.py` block would also drop the run/sprint binding above.

**Rollback:** `tools/install_model.py work/rollback/mm9_wolf.glb --world mm9` (sha256 5711a0a1...), relink the review
roots, and restore `run: Running`, `run_stride_length: 4.18` without `sprint` in the three wolf bindings.
