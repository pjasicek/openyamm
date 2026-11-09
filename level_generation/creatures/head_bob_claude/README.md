# Head bob pass over MM6–MM8 bipeds (2026-10-22)

The head's vertical travel in walk and run clips, measured as peak-to-peak height in per cent of the standing head height
(Standing at 0 s). Across the 116 grounded biped walk/run bindings the walk median is 4.0 % (quartiles 3.1–5.4) and
the run median 5.5 % (3.7–8.0); people bob about 2.5–3 % walking and 4–6 % running. The head follows the pelvis
within a few per cent on almost every model, so the bob is the hips' travel.

The user asked for a check after the MM6 Ogre's run looked wrong: 10.3 % bob, played at x1.9–2.2 when chasing because
its run stride (1.59) is shorter than its walk (2.10). This pass changes the bob only; the Ogre still plays its run
fast (a longer-stride run clip would fix that, see the creature post-process gait step).

## Method

`claude_shared/postprocess/bob_fix.py` (see its docstring): per clip, the pelvis height over the loop is split into
its even part (both steps alike) and the uneven rest; the new height is the even part scaled about the mean, with the
gain fitted to a head-bob target and at least 0.2 of the authored bob. The root joints move, then each leg's thigh and
calf are solved again so the foot joint keeps its original world position and rotation (foot drift ~1e-7 model
units). A leg never stretches further than the clip already does. For clips whose own bob is too faint or out of
step to scale (PeasantM3 walk and run, PeasantF2 walk), a synthetic bob is timed by the legs: an inverted pendulum
for a walk, a grounded-run dip over the planted foot for a run.

Targets: 4.5 % for a damped walk, 6.5 % for a damped run, 3 % for a raised walk, 4.5 % for a raised run, and 0 (only
the limp removed) for uneven steps.

- `jobs.txt`: world, model, clip, target.
- `run_jobs.py`: `work/<world>/<model>.glb` (copy of the installed source, taken once) to `export/<world>/<model>.glb`.
- `check.py`: floor rules (`floor_audit.py`) and measured strides (`stride_audit.py`) of every binding, candidate
  against installed.
- `review/build_manifest.py`, `review/viewer/`: before/after viewer
  (`http://127.0.0.1:8912/level_generation/creatures/head_bob_claude/review/viewer/`), verdicts kept in the browser.
  `review/shots.mjs <out> <entry id>...` writes stills at four loop times.

## Results (installed 2026-10-22)

| Kind | Creature | Model | Clip | Bob before % | after % | Target |
| --- | --- | --- | --- | --- | --- | --- |
| Damped | MM6 Ogre | `mm6_ogr` | Running | 10.3 | 6.5 | 6.5 |
| Damped | MM8 Ogre Warrior | `mm8_m440` | Running | 13.2 | 6.4 | 6.5 |
| Damped | MM7 Troglodyte | `mm7_m418` | Running | 12.4 | 6.6 | 6.5 |
| Damped | MM8 Vampire (monster) | `mm8_m468` | Walking | 11.7 | 4.6 | 4.5 |
| Damped | MM8 Vampire (monster) | `mm8_m468` | Running | 14.8 | 7.0 | 6.5 |
| Damped | MM7 Behemoth | `mm7_m162` | Walking | 17.1 | 8.9 | 4.5 |
| Damped | MM7 Behemoth | `mm7_m162` | Running | 16.7 | 6.6 | 6.5 |
| Damped | MM6 Werewolf | `mm6_wwf` | Walking | 11.7 | 4.6 | 4.5 |
| Damped | MM6 Werewolf | `mm6_wwf` | Running | 13.8 | 6.5 | 6.5 |
| Damped | MM6 Goblin | `mm6_gob2` | Running | 16.4 | 6.4 | 6.5 |
| Damped | MM8 Human Mercenary | `mm8_m656` | Running | 11.2 | 6.6 | 6.5 |
| Damped | MM6 Earth Elemental | `mm6_ert` | Walking | 10.7 | 4.6 | 4.5 |
| Damped | MM7/MM8 Earth Elemental | `mm8_m504` | Walking | 10.2 | 4.5 | 4.5 |
| Damped | MM7 AMinotaur | `mm7_m286` | Walking | 12.3 | 5.8 | 4.5 |
| Damped | MM6 LizardArch | `mm6_lzd` | Walking | 10.1 | 4.7 | 4.5 |
| Damped | MM7 Devil | `mm7_m178` | Walking | 10.0 | 6.9 | 4.5 |
| Damped | MM7 Zombie | `mm7_m438` | Walking | 8.8 | 5.0 | 4.5 |
| Damped | MM8 Cyclops | `mm8_m520` | Walking | 9.8 | 5.7 | 4.5 |
| Damped | MM6 KnightPlate | `mm6_kni` | Running | 8.7 | 6.5 | 6.5 |
| Damped | MM6 PeasantF2 | `mm6_fmp` | Run | 8.0 | 6.5 | 6.5 |
| Damped | MM6 PeasantF4 | `mm6_natf` | Running | 7.9 | 6.5 | 6.5 |
| Damped | MM8 Troll | `mm8_m476` | Running | 14.1 | 7.2 | 6.5 |
| Damped | MM7 ATroll | `mm7_m461` | Running | 10.3 | 6.5 | 6.5 |
| Damped | MM8 Ogre Mage | `mm8_m540` | Running | 10.4 | 6.5 | 6.5 |
| Damped | MM8 Dark Elf Warrior | `mm8_m432` | Running | 11.5 | 7.5 | 6.5 |
| Damped | MM8 Dark Dwarf | `mm8_m632` | Running | 8.0 | 6.4 | 6.5 |
| Raised | MM6 PeasantM3 | `mm6_mep` | Walking | 0.4 | 2.9 | 3.0:walk |
| Raised | MM6 PeasantM3 | `mm6_mep` | Running | 0.7 | 4.4 | 4.5:run |
| Raised | MM6 Barbarian | `mm6_bar1` | Running | 2.2 | 4.4 | 4.5 |
| Raised | MM8 Dragon Hunter | `mm8_m456` | Running | 2.2 | 4.5 | 4.5 |
| Raised | MM6 PeasantF2 | `mm6_fmp` | Walking | 1.6 | 2.9 | 3.0:walk |
| Raised | MM6 Jackalman | `mm6_jak1` | Walking | 1.7 | 3.0 | 3.0 |
| Evened | MM8 Pirate Mage | `mm8_m420` | Walk2 | 2.1 | 1.6 | 0 |
| Evened | MM6 Skeleton | `mm6_ske` | Walking | 3.1 | 2.0 | 0 |
| Evened | MM8 Troll | `mm8_m476` | Walking | 2.4 | 2.0 | 0 |

Above target with the hips at the 0.2 minimum: the Behemoth and Devil walks, the AMinotaur and Cyclops walks and the
Dark Elf Warrior run. The rest of their head travel is the spine and neck nodding, which this pass leaves as authored.

Left out: the MM8 Necromancer's Run2 (evening its steps lowered the robe hem 4.6 units into the floor), the Cockatrice
(a bird: its head bobs on the neck, the hips only 6.6 %), the MM8 Ether Knight run (never chosen at its tiers' speeds)
and the Troglodyte walk (never chosen; it wanders with its run).

`check.py`: no new floor problem and every measured stride within 3 % on all 31 models, except the Earth Elemental's
vertex stride (0.754 to 0.797); that measurement was already untrusted on this rubble body, and its foot-joint stride,
the one that is trusted, moved 0.6 % (2.391 to 2.406).

## Status

The user reviewed the candidates in the viewer ("ok much better, install all") and all 29 models were installed on
2026-10-22 with `tools/install_model.py` (sources were checked unchanged since `work/` was copied; winding 0 inverted).
After the install, the floor and stride audits of every binding of these models are clean except the MM7 Behemoth's
Attack (sinks 16.6-20.8 units on tiers A-C), which the original model already did; `bob_audit.py` reads the
installed bobs back as in the table. Most sources had last been written by `lod_repair_claude`: its README and the
five MM8 project READMEs say to rerun `run_jobs.py` after a rebuild there.

## Install

For each accepted model (the user's verdicts may drop single clips: rerun the job without them first):

```sh
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py level_generation/creatures/head_bob_claude/export/<world>/<model>.glb
python3 tools/install_model.py level_generation/creatures/head_bob_claude/export/<world>/<model>.glb --world <world>
```

`mm8_m504` is installed once with `--world mm8` (MM7 binds the MM8 path). Then rerun `floor_audit.py` and
`stride_audit.py` for the three worlds, and add a dated "Head bob" note to each creature project's README.
