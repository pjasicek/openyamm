You are package `h18` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h18/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_m424.glb (source assets_source/worlds/mm8/models/mm8_m424.glb; biped; authored walk 1.78 run 2.75; projects: mm8_m424_claude, mm8_m424_reduce_claude)
    Dark Elf Pesant Male A: standard wander Walking x0.68 at 1.22
    Dark Elf Pesant Male B: standard wander Walking x0.68 at 1.22
    Dark Elf Pesant Male C: standard wander Walking x0.68 at 1.22
- mm8/mm8_m428.glb (source assets_source/worlds/mm8/models/mm8_m428.glb; biped; authored walk 1.95 run 1.95; projects: mm8_m428_claude, mm8_m428_reduce_claude)
    Dark Elf Pesant Female A: standard wander Walking x0.61 at 1.18
    Dark Elf Pesant Female B: standard wander Walking x0.61 at 1.18
    Dark Elf Pesant Female C: standard wander Walking x0.61 at 1.18
- mm8/mm8_m432.glb (source assets_source/worlds/mm8/models/mm8_m432.glb; biped; authored walk 1.53 run 5.85; projects: mm8_m432_claude, mm8_m432_reduce_claude)
    Dark Elf Warrior A: standard chase Running x0.68 at 3.99
    Dark Elf Warrior B: standard chase Running x0.74 at 4.32
    Dark Elf Warrior C: standard wander Walking x1.52 at 2.33
- mm8/mm8_m604.glb (source assets_source/worlds/mm8/models/mm8_m604.glb; biped; authored walk 2.24 run 5.6; projects: mm8_m604_claude, mm8_m604_reduce_claude)
    Ether Knight A: standard wander Walking x0.66 at 1.47
    Ether Knight B: standard wander Walking x0.72 at 1.6
    Ether Knight C: standard chase Running x0.67 at 3.74
- mm8/mm8_m460.glb (source assets_source/worlds/mm8/models/mm8_m460.glb; biped; authored walk 1.9 run 1.9; projects: mm8_m460_claude, mm8_m460_reduce_claude)
    Cleric (human male) A: standard chase Walking x1.52 at 2.89
    Cleric (human male) A: maw chase Walking x1.52 at 2.89
    Cleric (human male) B: standard chase Walking x1.71 at 3.25
    Cleric (human male) B: maw chase Walking x1.71 at 3.25
    Cleric (human male) C: standard chase Walking x1.90 at 3.62
    Cleric (human male) C: maw chase Walking x1.90 at 3.62

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
