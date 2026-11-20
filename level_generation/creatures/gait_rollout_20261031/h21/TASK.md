You are package `h21` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h21/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_ratman.glb (source assets_source/worlds/mm8/models/mm8_ratman.glb; biped; authored walk 2.33 run 4.3; projects: mm8_m448_claude, mm8_ratman_reduce_claude)
    Wererat Ratman Form Male A: maw chase Running x1.96 at 8.44
    Wererat Ratman Form Male B: maw chase Running x2.00 at 8.64
    Wererat Ratman Form Male C: maw chase Running x2.04 at 8.73
- mm8/mm8_m444.glb (source assets_source/worlds/mm8/models/mm8_m444.glb; biped; authored walk 1.77 run 2.7; projects: mm8_m444_claude, mm8_m444_reduce_claude)
    Wererat Human Form Male A: standard chase Running x1.80 at 4.86
    Wererat Human Form Male A: maw chase Running x3.06 at 8.26
    Wererat Human Form Male B: standard chase Running x1.94 at 5.25
    Wererat Human Form Male B: maw chase Running x3.12 at 8.45
    Wererat Human Form Male C: standard chase Running x2.08 at 5.63
    Wererat Human Form Male C: maw chase Running x3.20 at 8.65
- mm8/mm8_m468.glb (source assets_source/worlds/mm8/models/mm8_m468.glb; biped; authored walk 1.27 run 3.85; projects: mm8_m468_claude, mm8_m468_reduce_claude)
    Vampire (monster) A: standard wander Walking x1.51 at 1.92
    Vampire (monster) A: maw chase Running x1.86 at 7.16
    Vampire (monster) B: standard wander Walking x1.65 at 2.1
    Vampire (monster) B: maw chase Running x1.91 at 7.34
    Vampire (monster) C: standard wander Walking x1.79 at 2.27
    Vampire (monster) C: maw chase Running x1.95 at 7.51
- mm8/mm8_m628.glb (source assets_source/worlds/mm8/models/mm8_m628.glb; biped; authored walk 2.81 run 2.81; projects: mm8_m628, mm8_m628_reduce_claude)
    Skeletons Archer A: standard wander Walking x0.35 at 0.99
    Skeletons Archer A: standard chase Walking x0.71 at 1.99
    Skeletons Archer A: maw chase Walking x0.71 at 1.99
    Skeletons Archer B: standard wander Walking x0.38 at 1.06
    Skeletons Archer C: standard wander Walking x0.49 at 1.36
- mm8/mm8_m632.glb (source assets_source/worlds/mm8/models/mm8_m632.glb; biped; authored walk 1.51 run 3.95; projects: mm8_m632_claude, mm8_m632_reduce_claude)
    Dark Dwarf A: maw chase Running x1.79 at 7.09
    Dark Dwarf B: maw chase Running x1.84 at 7.26
    Dark Dwarf C: standard wander Walking x1.57 at 2.36
    Dark Dwarf C: maw chase Running x1.88 at 7.42

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
