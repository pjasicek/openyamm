# Gait rollout package q2: MM7 zrat, dog, cat and MM8 Dire Wolf (2026-10-31)

Brief: [the rollout README](../README.md). Four quadrupeds, all on the rat-route rig (Spine1-3, Neck1, Head, Tail1-6,
UpperArm/ForeArm/FrontPaw, Thigh/Shin/HindPaw; the wolf adds Jaw). Every new clip is procedural, made by
`scripts/quad_gait.py` and grafted onto the **installed** source with `../../claude_shared/graft_clips.py`
(`graft_byte_check.py`: the old file is a byte prefix, every old mesh, skin, material and clip unchanged). All four are
installed; the coordinator applies [bindings.yml](bindings.yml).

| model | descriptors | new clips | binding |
|---|---|---|---|
| mm7_m382 | zrat a-c (Rat A-C unchanged) | Walk3 | walking Walk3 0.7733, run Walk2 1.0453 |
| mm7_m509 | zdog a-c | Trot | run Trot 0.9663 |
| mm7_7m500 | zcat a-c | Trot | run Trot 0.484 |
| mm8_wolf | Dire Wolf A-C | Walk2, Run2, Sprint | walking Walk2 0.4545, run Run2 0.7035, sprint Sprint 1.275 |

## Method

`scripts/quad_gait.py` copies the machinery of `../../mm7_m382_claude/scripts/sprint_rat7.py` (left unchanged):
- **Planting.** Each paw is planted by its contact point (the front-most of its lowest vertices at rest). The wrist or
  ankle follows through two-bone IK, and the heel lifts over the last 40 % of the stance.
- **Footholds.** Footholds are planned per limb against the posed body, keeping the wrist or ankle within 0.97 of the
  chain.
- **Swing.** In the swing the paw tucks; fronts reach ahead of the foothold and hinds trail for flights.
- **Floor.** Tail ends are kept above the floor.

Per model it keeps the installed walk's carriage: the rat's tail wave, the dog's and cat's tail, and the wolf's
front-down 7° body pitch with the head raised 4° and the tail lowered.

Added for this package:
- **Bob, rocking and flex harmonics.** Twice a loop for trots, once for lopes and gallops.
- **Head hold** (`head_hold`). Neck1 pitches so the Head joint moves back toward its mean height by that share, and
  Head turns back by the same angle. Running animals steady the head this way.
- **Tuning.** `QG_SET` overrides clip parameters for trial runs.

**Phase.** Every new clip strikes the foot that the model's walk strikes at 0. Check this with the furthest-forward
phase of each paw joint (`scripts/quad_probe.py`):

| model | walk at phase 0 | new clips |
|---|---|---|
| rat | Walk2 lope: hind L at 0, hind R .12, front R .40, front L .52 | Walk3 uses the same phases |
| dog, wolf | trot: front L and hind R at 0 | Trot, Walk2 and Run2: front L and hind R at 0; the wolf's Sprint: rotary gallop, hind R at 0, hind L .07, front L .42, front R .51 |
| cat | walk: hind L at 0, front R .25, hind R .50, front L .75 | Trot: hind L and front R at 0 |

**Paw heading.** Heading is measured from each paw's lateral axis (`quad_probe.py`, as
`../../mm6_sprint_humanoids_claude/scripts/foot_heading_probe.py`). The paws only pitch about the travel's side axis,
so a planted paw keeps its rest heading, the same as in the model's Standing and installed walk (± 1.5° planted).

## Per model

| model | clip | gait | length | stride | authored speed | duty | sweep | head bob | lowest vertex |
|---|---|---|---|---|---|---|---|---|---|
| m382 | Walk3 | rotary lope, no suspension | 0.2667 s (16 keys at 60 fps) | 0.7733 m | 2.90 | 0.52 | 0.40 m | 9.2 % (Walk2 44.8 %) | -2.2 cm (scale 50: -1.1 wu) |
| m509 | Trot | trot, short suspensions | 0.4333 s (26) | 0.9663 m | 2.23 | 0.40 | 0.39 m | 5.2 % (Walking 3.7 %) | +0.3 cm |
| 7m500 | Trot | trot | 0.3667 s (22) | 0.484 m | 1.32 | 0.42 | 0.20 m | 6.3 % (Walking 5.6 %) | +0.04 cm |
| wolf | Walk2 | trot, stances overlapping | 0.45 s (27) | 0.4545 m | 1.01 | 0.56 | 0.25 m | 3.4 % (Walking 10.9 %) | -0.43 cm |
| wolf | Run2 | flying trot | 0.35 s (21) | 0.7035 m | 2.01 | 0.38 | 0.27 m | 6.0 % | -0.65 cm |
| wolf | Sprint | rotary gallop, two flights | 0.4167 s (25) | 1.275 m | 3.06 | 0.22 | 0.28 m | 11.7 % (the rat's Sprint: 65 %) | -0.53 cm |

The head bob is the Head joint's peak-to-peak height in % of its Standing height. `bob_audit.py` only reads bipeds.

**Paw headings.** Toe-out while planted, front L / front R / hind L / hind R:

| model | front L | front R | hind L | hind R |
|---|---|---|---|---|
| rat | +12.6 | +8.6 | -8.1 | -4.8 |
| dog | +2.6 | +4.1 | +7.2 | +4.0 |
| cat | +11.4 | +12.6 | +4.9 | +4.2 |
| wolf | +16.0 | +13.1 | +21.5 | +21.8 |

Every new clip matches its model's Standing and installed walk.

### zrat (mm7_m382)

**Targets.** zrat a-c wander at 2.80 and chase at 5.60 model units/s, the same under MAW (Spd 140). Walk2 (4.48)
played ×0.63 when wandering. Walk3 is a slower lope with Walk2's phases, longer stances and a 3.75 Hz cadence. Rocking
and flex are cut to 1° and 2.5°, and the hips take back half the flex: 3° and 5° gave a 36 % head bob, the current
values 9 %.

**Why Walk2 becomes zrat's run.** With Walk3 as the walk, the engine would chase on Walk3 at ×1.93: Run2 at ×0.63
misfits more. So zrat's run is Walk2, which chases at ×1.25.

**Gate.** `scripts/gate_only.py --only "zrat a,zrat b,zrat c"`: the shared gate applies `--set` to every descriptor of
the model, and Rat A-C keep theirs.
- stride: Walk3 0.773 / feet 0.763, trusted
- window: Standard wander Walk3 ×0.97, chase Walk2 ×1.25; MAW the same
- floor: ok
- PASSED

Rat A-C rerun on the candidate without changes: Walk2 ×1.06, Run2 ×1.06; MAW Run2 ×0.90 and Sprint ×1.22. PASSED.

### zdog (mm7_m509)

**Targets.** Wander 1.18, chase 2.36; MAW unchanged, so no sprint. The installed `run: Walking` played ×2.12.

**Trot.** Front L and hind R strike at 0, as in the walk. The body is 3 cm lower, and the front footholds are planned
13 cm further back (under the shoulder): the dog's rest front leg is almost straight, so reach is at 0.97.

**Gate.**
- stride: Trot 0.966 / 0.962, trusted
- window: Standard and MAW wander Walking ×1.06, chase Trot ×1.06
- floor: ok
- PASSED

### zcat (mm7_7m500)

**Targets.** Wander 0.70, chase 1.40; MAW unchanged. The installed `run: Walking` played ×1.99.

**Trot.** Hind L and front R strike at 0. The body is 2.5 cm lower, and the cadence is 2.7 Hz. A 0.40 s loop put the
fronts at the limit of reach (1.00 of the chain); 0.367 s keeps every limb at 0.97.

**Gate.**
- stride: Trot 0.484 / 0.481, trusted
- window: wander Walking ×1.00, chase Trot ×1.06
- floor: ok
- PASSED

### Dire Wolf (mm8_wolf)

**Targets.** Standard wander 0.98-1.16 and chase 1.97-2.32; MAW chase 2.85-3.68 (Spd / 2 + 300). The installed walk
(0.34) and run (0.77) played the Running clip ×1.51 wandering and ×3.02 chasing (A).

**Reach limits.** The wolf's legs are short: shoulder 0.32 m, chain 0.28 m. Its sweep stays within about 0.28 m, so
the speed comes from cadence and, in the gallop, from flights:
- Walk2: a trot at 2.2 Hz with overlapping stances (no suspension, as the floor rule for walks requires).
- Run2: a flying trot at 2.9 Hz.
- Sprint: a rotary gallop at 2.4 Hz. Its back flexes ±16°, and the hips take back 55 %. It has two flights and rises
  2.5 cm.

**Gate.** In `gait_gate.py` the window section is:

| ruleset | tier | wander | chase |
|---|---|---|---|
| Standard | A | Walk2 ×1.15 | Run2 ×1.15 |
| Standard | B | Walk2 ×1.07 | Run2 ×1.08 |
| Standard | C | Walk2 ×0.97 | Run2 ×0.98 |
| MAW | A | Run2 ×0.92 | Sprint ×1.20 |
| MAW | B | Walk2 ×1.62 | Sprint ×1.07 |
| MAW | C | Walk2 ×1.41 | Sprint ×0.93 |

MAW's hostile wandering of B is outside the window. The gate does not hold it (its calm wandering keeps Spd).

Also:
- stride: Walk2 0.454 / 0.453, Run2 0.704 / 0.699, Sprint 1.275 / 1.255, all trusted
- floor: ok. The lowest vertex is -0.65 cm (Run2's hind paw at push-off); the tolerance is 0.78 cm at tier C
  (2.5 world units / 320).
- PASSED

## Gates run on every export

- `gait_gate.py`: see each model above.
- `graft_byte_check.py`: OK.
- `check_winding.py`: 0 inverted.
- `quad_probe.py`: head bob and paw heading.
- Viewer: `tools/run_creature_review.py ... check` (no console errors), shots, and playback at 1× and 0.5×, looked at.

Viewer revisions:

| project | revision | previous manifest kept as |
|---|---|---|
| `mm7_m382_reduce_claude` | `zrat-walk3-1` | `manifest_sprint-1.json` |
| `mm7_m509_claude` | `zdog-trot-1` | `manifest_mm7_m509_claude_v1.json` |
| `mm7_7m500_claude` | `zcat-trot-1` | `manifest_mm7_7m500_claude_v1.json` |
| `mm8_wolf_reduce_claude` | `wolf-gait-1` | `manifest_reduce-1-attack-v3.json` |

The dog, cat and wolf viewers had no page. `scripts/viewer_page.sh` copied the rat viewer's, as the rat sprint pilot
did from `mm9_bigfoot_claude`. The wolf viewer GLBs were made by that project's `viewer_tiers.py`, unchanged.

## Doubts

- **Paw toe-out.** The rat's and cat's front paws toe out 9-13°, and the wolf's 13-16° (front) and 22° (hind), over
  the brief's 5°. That is the rest pose and the accepted Standing and walks. The engine switches clips instantly on
  the shared phase, so turning only the new clips' paws would twist them at every switch. Straightening them means
  re-posing the rest paws and every clip.
- **Head bob.** The quadruped figures are not comparable to the biped bands. The rat's lope (9 %) and the wolf's
  gallop (12 %) are above 4-7 %; the rat's accepted Walk2, Run2 and Sprint read 45-79 %.
- **Dog stride.** The dog's Trot stride (0.97 m) equals its walk's (0.97 m bound, 1.0 measured). The walk overreaches
  (its 0.53 m sweep is beyond the straight front leg), so the trot gets its speed from cadence.
- **Cat stride.** The cat's Trot stride (0.48 m) is shorter than its walk's (0.60 m), for the same reason.
- **Wolf MAW wandering.** Under MAW, hostile Dire Wolf B and C wander on Walk2 at ×1.62 and ×1.41. Not gated.

## Rebuild

From this directory:

```sh
blender -b --factory-startup -P scripts/quad_gait.py -- <m382|m509|7m500|wolf> work/<model>_clips.glb
python3 ../../claude_shared/graft_clips.py ../../../../assets_source/worlds/mm7/models/mm7_m382.glb \
  work/m382_clips.glb export/mm7_m382.glb --clip Walk3                                   # rat
python3 ../../claude_shared/graft_clips.py <source mm7_m509.glb> work/m509_clips.glb export/mm7_m509.glb --clip Trot
python3 ../../claude_shared/graft_clips.py <source mm7_7m500.glb> work/7m500_clips.glb export/mm7_7m500.glb --clip Trot
python3 ../../claude_shared/graft_clips.py <source mm8_wolf.glb> work/wolf_clips.glb export/mm8_wolf.glb \
  --clip Walk2 --clip Run2 --clip Sprint
python3 scripts/quad_probe.py export/<glb> <clips>                       # head bob, paw heading, footfall
```

Graft onto the pre-change sources in `work/rollback/`, or onto the current source after any later change. A far-LOD
repair rerun (`lod_repair_claude`) rebuilds the GLB and must re-graft these clips. The scripts read the projects'
blends read-only:
- `mm7_m382_claude/work/anim_v2u.blend`
- `mm7_m509_claude/work/anim_v2u.blend`
- `mm7_7m500_claude/work/anim_v2u.blend`
- `mm8_m512_claude/work/anim_v1.blend`

They save `work/<model>_gaits.blend`.

**Rollback.** The pre-change sources are in `work/rollback/`. Install one with `tools/install_model.py
work/rollback/<glb> --world <w> --name <glb>`, then revert the q2 entries of `actors.yml`.
