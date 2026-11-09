# Gait rollout package q1: MM6 and MM7 spiders, MM6 Cockatrice and Wyrm (2026-10-31)

Brief: [the rollout README](../README.md). Every new clip is procedural. Each was grafted onto the **installed** source
with `../../claude_shared/graft_clips.py`, and `graft_byte_check.py` confirmed that the old file is a byte prefix:
every old mesh, skin, material and clip is unchanged. All four models are installed. The coordinator applies
[bindings.yml](bindings.yml).

| model | body (by eye) | descriptors | new clips | binding |
|---|---|---|---|---|
| mm6_spi1 | eight-legged spider | BSpider A-C | Sprint | sprint Sprint 1.018 |
| mm7_m402 | eight-legged spider | Spider A-C | Sprint | sprint Sprint 2.2027 |
| mm6_wyrm | wingless four-legged dragon | DragonLand A-C | Walk2, Run2 | walking Walk2 0.111, run Run2 0.18 |
| mm6_ckt | **two-legged** bird with bat wings (the ledger's "multi-legged" is wrong) | Cockatrice A-C | Run2, Sprint | run Run2 0.665, sprint Sprint 0.945 |

## Scripts

- `scripts/sprint_spi1.py` and `scripts/sprint_m402.py`. These are copies of the projects' `gait2_*.py`, the
  2026-10-21 Walk2/Run2 scripts: the same alternating tetrapod, planned footholds, tarsus-tip contact, IK and body
  raise. Only a Sprint is left in each clip table. One addition: `bob_low`, the phase at which the body is lowest. The
  Sprint puts it at mid-stance, so the body is highest in flight; Walk2 and Run2 keep their formula.
  `sprint_m402.py` reads the hanging fringe cards from the installed source.
- `scripts/gait_wyrm.py`. Copies `anim_wyrm.py`'s functions: the paw IK, the body bob, the tail and its floor clamp,
  and the phases. That script keys every clip when run, so it is copied, not imported. It reads the current master,
  `mm6_drr1_claude/export/mm6_wyrm.blend`.
- `scripts/gait_ckt.py`. Executes `anim_ckt.py` unchanged up to its clip table, which gives the leg IK, the wings,
  head, tail and floor helpers. It then keys Run2 and Sprint at 48 fps.
- Probes, copied from q3: `quad_probe.py`, `low_probe.py`, `viewer_manifest.py`, `viewer_page.sh`, `viewer_clips.py`.
  `sheet.py` makes the contact sheets in `review/`.

## Per model

### MM6 Spider (mm6_spi1): Sprint

**Targets.** MAW chases at 4.21-6.92. Run2 (3.23) played A ×2.00 (held at the 2× ceiling, sliding) and B ×1.63. The
sprint fit is 4.62-5.61.

**Sprint.**
- 0.2 s (12 keys at 60 fps), stride 1.018, authored speed 5.09.
- Duty 0.32: each tetrapod is down 32 %, with two flights per loop.
- Sweep 0.33 m, like Run2's 0.31.
- Body 6 cm lower, front pitched down 3°, feet lifted 10 cm.
- Group L1 R2 L3 R4 is down at 0, as in Walk2 and Run2.

**Gate** (window section):

| tier | Standard wander | Standard chase | MAW chase |
|---|---|---|---|
| A | Walk2 ×1.43 | Sprint ×0.91 | Sprint ×1.36 |
| B | Walk2 ×1.04 | Run2 ×1.04 | Sprint ×1.03 |
| C | Walk2 ×0.79 | Run2 ×0.79 | Run2 ×1.30 |

Stride: measured 1.018, feet 0.874, not trusted. Walk2 and Run2 also disagree, and were bound at their authored
strides. The binding is the authored stride, because the planted tips move exactly at it. Floor: ok. PASSED.

**Probes.**
- Thorax bob: Sprint 5.4 %, Run2 5.9 %, Walk2 3.5 %.
- Tarsus headings while planted: within 1-3° of Run2's on every leg (for example L1 -31.6 against -31.0, R4 +114.4
  against +116.0).
- Touchdowns are at the same phases as Run2.
- Worst tip miss in the swing is 17.6 mm (L2 reaching forward-up). Run2's was 15 mm. Planted tips miss nothing.

### MM7 Spider (mm7_m402): Sprint

**Targets.** MAW chases at 8.57-8.96. Run2 (5.24) played them ×1.63-1.71. The sprint fit is 5.98-11.42.

**Sprint.**
- 0.2667 s (16 keys at 60 fps), stride 2.2027, authored speed 8.26.
- Duty 0.33; the front pair's is 0.26.
- Sweep 0.73 m (Run2's is 0.71). Feet lifted 26 cm.
- The body is raised automatically by +7.1 cm to clear the floor by 5 mm. Run2 was raised +5.3 cm.
- Planted feet are raised for the hanging fringe cards: R1 3.6 cm, R2 1.7 cm, L2 0.8 cm, as in Run2.

**Gate** (window section):

| tier | Standard wander | Standard chase | MAW chase |
|---|---|---|---|
| A | Walk2 ×1.14 | Run2 ×1.14 | Sprint ×1.09 |
| B | Walk2 ×1.06 | Run2 ×1.06 | Sprint ×1.06 |
| C | Walk2 ×0.99 | Run2 ×0.99 | Sprint ×1.04 |

Stride: measured 2.034, feet 1.797, trusted. The binding is the authored 2.2027, as Walk2 and Run2 were bound at
their authored strides (1.092 and 1.572 against measured 1.004 and 1.451). The floor-hanging cards dilute the vertex
median. Floor: ok. PASSED.

**Probes.**
- Thorax bob: Sprint 13.6 %, Run2 13.2 %, Walk2 8.1 %. The thorax is low, so the percentages are large.
- Tarsus headings while planted: within 1° of Run2's.
- Touchdowns are at the same phases. Tip miss: 0.

### MM6 Wyrm (mm6_wyrm): Walk2, Run2

**Targets.** It wanders at 0.11-0.19 and chases at 0.22-0.37; MAW leaves these unchanged. Before:
- Great Wyrm C wandered on Walking (0.12 m in 0.75 s, 0.16) at ×0.69.
- C's chase fell back on Walking at ×1.38, because Running (0.19 m in 0.625 s, 0.30) would play ×0.73.

The fits are walk 0.12-0.15 and run 0.25-0.30.

**New clips** (24 fps linear keys, as the project):

| clip | length | stride | authored speed | duty | gait |
|---|---|---|---|---|---|
| Walk2 | 0.7917 s (19 keys) | 0.111 | 0.140 | 0.70 | four-beat walk |
| Run2 | 0.6667 s (16 keys) | 0.18 | 0.27 | 0.58 | diagonal gait |

- Slower speeds take shorter strides at a slightly lower cadence (retiming the old clips would look identical in game).
- Everything else is `anim_wyrm.gait` unchanged: the same phases (front L down at 0; Run2 front L + hind R at 0, as
  Running), tail wave and clamp, and the Remains bone at scale 0.

**Gate** (Standard and MAW are the same):

| tier | wander | chase |
|---|---|---|
| A | Walk2 ×1.32 | Run2 ×1.37 |
| B | Walk2 ×1.02 | Run2 ×1.06 |
| C | Walk2 ×0.79 | Run2 ×0.82 |

Stride: measured and feet both 0.111 and 0.180, trusted. Floor: ok (lowest vertex -0.0001 mm). PASSED.

**Probes.**
- Head bob is 1.2 % in all four clips.
- Paw toe-out while planted: front +1.4, hind +14.9, identical to Walking and Running. The hind toe-out is the rest
  pose's.
- Touchdowns: Walk2 0 / .47 / .26 / .74 (Walking 0 / .50 / .23 / .72); Run2 equals Running.

### MM6 Cockatrice (mm6_ckt): Run2, Sprint

**Targets.** It wanders at 0.56-0.65. Standard chases at 1.12-1.31, MAW at 1.96-2.06. Its only gait was Walking (0.503
m in 0.75 s, 0.67): it chased at ×1.67-1.95 and was held at 2× under MAW. The fits are run 0.87-1.50 and sprint
1.37-2.62.

Note: `anim_ckt.py`'s `STRIDE` 0.30 is the stance sweep. The real stride is 0.30 / 0.6 = 0.50, the binding's 0.503.

**New clips** (48 fps):

| clip | length | stride | authored speed | duty |
|---|---|---|---|---|
| Run2 | 0.5833 s | 0.665 | 1.14 | 0.45 |
| Sprint | 0.50 s | 0.945 | 1.89 | 0.32 |

- **Run2:** a bird run with short flights. Body pitched 11°, neck stretched, one wing beat per step.
- **Sprint:** a wing-assisted bounding sprint. Body pitched 17°, head forward, full wing beats (downstroke through each
  stance), tail held out and steadier.
- Both keep Walking's 0.30 m stance sweep about the rest ankle (the legs' reach), so the extra stride is flight.
- Body lowest at mid-stance. Left foot down at 0, as Walking.
- Ankle IK misses: at most 3.3 mm late in stance (push-off), 5.8 mm at swing start.
- A first Sprint had the tail curled up like a scorpion's (per-bone lift summed down the chain). It is now held out
  level with Walking's.

**Gate** (window section):

| tier | Standard wander | Standard chase | MAW chase |
|---|---|---|---|
| A | Walking ×0.84 | Run2 ×0.98 | Sprint ×1.04 |
| B | Walking ×0.91 | Run2 ×1.07 | Sprint ×1.06 |
| C | Walking ×0.98 | Run2 ×1.15 | Sprint ×1.09 |

Stride (measured / feet, trusted):
- Run2 0.670 / 0.666
- Sprint 0.957 / 0.930

The bindings are the authored strides. Floor (a flier, Fly Y): ok, lowest vertex +0.03 cm. PASSED.

**Probes.**
- Head bob: Walking 11.9 %, Run2 6.5 %, Sprint 9.7 %.
- Foot toe-out while planted, L and R: Walking +3.5, Run2 +3.6, Sprint +3.5. Swing up to +6.9 in Sprint (Walking +4.0).

## Gates run on every export

- `gait_gate.py`: PASSED (above).
- `graft_byte_check.py`: OK.
- `check_winding.py`: 0 inverted.
- `quad_probe.py`: bob, heading, touchdown phases.
- `low_probe.py`: floor (cockatrice).
- Viewer: `tools/run_creature_review.py ... check`, no console errors (33, 33, 30, 30 switches). Side, front and quarter
  shots of every new clip were looked at; contact sheets are in `review/*_sheet.png`, the shots in each viewer
  project's `review/shots/q1_*`.

Viewer GLBs were made with `mm6_spi1_reduce_claude/scripts/viewer_variants.py`, unchanged; it bakes each variant's
region ramps generically. The outputs were moved into each viewer.

| viewer project | revision | previous manifest kept as |
|---|---|---|
| `mm6_spi1_reduce_claude` | `spider-sprint-1` | `manifest_gait-1.json` |
| `mm7_m402_reduce_claude` | `spider-sprint-1` | `manifest_gait-1.json` |
| `mm6_drr1_claude` | `wyrm-gait-1` | `manifest_v4-retopo.json` |
| `mm6_ckt_reduce_claude` | `ckt-gait-1` | `manifest_reduce-1.json` |

In the Cockatrice manifest, Cast's duration was corrected from 0.75 to 0.631 s, the reduced Cast.

**Regressions covering these models** (headless outdoor suite), run on the installed files with the current bindings,
all pass (`review/regression_*.log`):
- `mm6_wyrm_actor_model_tiers_and_clips`
- `mm6_drake_and_dragon_actor_model_burn_death` (it includes `mm6_wyrm.glb`)
- `mm6_mm7_mm8_actor_models_build_every_binding` (647 descriptors on 185 models, 0 failed)

There are no dedicated cases for the spiders or the Cockatrice.

## Doubts

- **Spider sprint gait.** Real spiders keep an alternating tetrapod at speed rather than gallop, so the Sprint is the
  same tetrapod with a short stance and flights, not a bound. MM6 BSpider A's Standard chase (4.62) now plays Sprint
  ×0.91 rather than Run2 ×1.43; the engine picks the smaller misfit.
- **Spider stride bindings** are the authored ones, against the gate's vertex suggestion for m402 (2.034, 8 % shorter):
  planted tips move at the authored stride, as for the accepted Walk2 and Run2.
- **Untested MAW wandering.**
  - The Cockatrice wanders on Walking ×1.46-1.53 under MAW (not gated). The engine prefers the walk when not hurrying;
    Run2 would be ×0.86-0.90.
  - The MM7 spider wanders on Walk2 ×1.63-1.71 under MAW, likewise.
- **Wyrm hind toe-out** is 14.9°, the rest pose's and every accepted clip's.
- **Cockatrice head bob** is 9.7 % in Sprint (Walking 11.9 %). The bob of a flying bird's walking clips in the air (the
  model keeps its walking clips while flying) was not looked at in game.

## Rebuild

From this directory:

```sh
blender -b --factory-startup -P scripts/sprint_spi1.py -- work/spi1_clips.glb
blender -b --factory-startup -P scripts/sprint_m402.py -- work/m402_clips.glb
blender -b --factory-startup -P scripts/gait_wyrm.py -- work/wyrm_clips.glb
blender -b --factory-startup ../../mm6_ckt_claude/work/anim_v1.blend -P scripts/gait_ckt.py -- work/ckt_clips.glb
G=../../claude_shared/graft_clips.py
python3 $G work/rollback/mm6_spi1.glb work/spi1_clips.glb export/mm6_spi1.glb --clip Sprint
python3 $G work/rollback/mm7_m402.glb work/m402_clips.glb export/mm7_m402.glb --clip Sprint
python3 $G work/rollback/mm6_wyrm.glb work/wyrm_clips.glb export/mm6_wyrm.glb --clip Walk2 --clip Run2
python3 $G work/rollback/mm6_ckt.glb work/ckt_clips.glb export/mm6_ckt.glb --clip Run2 --clip Sprint
python3 ../../../../tools/install_model.py export/<glb> --world <mm6|mm7> --name <glb>
```

A far-LOD repair rerun (`lod_repair_claude`) rebuilds the GLB and must re-graft these clips.

**Rollback.** The pre-change sources are in `work/rollback/`. Install one with
`tools/install_model.py work/rollback/<glb> --world <w> --name <glb>`, then revert the q1 entries of `actors.yml`.

## Problems found in tools

- **`viewer_manifest.py` (q3's copy) fails on stale manifests.** It refuses a manifest whose clip duration differs
  from the GLB. The Cockatrice viewer's Cast was 0.75 s; the reduce project had retimed it to 0.631 s. It also copies
  the old manifest before that check, so a failed run still writes `manifest_<old>.json`.
- **Viewers had no pages or GLBs left.** All four viewers held only a `manifest.json` pointing at missing GLBs, so
  `viewer_page.sh` added pages.
- **Shared tools.** None found broken. `gait_gate.py`'s vertex stride for the spiders is diluted by planted legs'
  long tarsi and hanging cards, as earlier gait passes already noted.
