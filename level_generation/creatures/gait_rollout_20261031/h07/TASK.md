You are package `h07` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h07/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m222.glb (source assets_source/worlds/mm7/models/mm7_m222.glb; biped; authored walk 1.48 run 2.45; projects: mm7_m222_claude, mm7_m222_reduce_claude)
    Fighter Chain A: standard wander Walking x1.54 at 2.29
    Fighter Chain A: standard chase Running x1.87 at 4.58
    Fighter Chain A: maw chase Running x3.48 at 8.54
    Fighter Chain B: standard chase Running x2.04 at 5.0
    Fighter Chain B: maw chase Running x3.56 at 8.75
    Fighter Chain C: standard chase Running x2.20 at 5.42
    Fighter Chain C: maw chase Running x3.64 at 8.96
- mm7/mm7_m226.glb (source assets_source/worlds/mm7/models/mm7_m226.glb; biped; authored walk 1.64 run 2.45; projects: mm7_m226_claude, mm7_m226_reduce_claude)
    Fighter Leather A: standard chase Running x1.65 at 4.04
    Fighter Leather A: maw chase Running x3.30 at 8.08
    Fighter Leather B: standard chase Running x1.81 at 4.44
    Fighter Leather B: maw chase Running x3.38 at 8.28
    Fighter Leather C: standard chase Running x1.98 at 4.85
    Fighter Leather C: maw chase Running x3.46 at 8.48
- mm7/mm7_m230.glb (source assets_source/worlds/mm7/models/mm7_m230.glb; biped; authored walk 1.71 run 2.45; projects: mm7_m230_claude, mm7_m230_reduce_claude)
    Fighter Plate A: standard chase Running x1.94 at 4.77
    Fighter Plate A: maw chase Running x3.30 at 8.11
    Fighter Plate B: standard chase Running x2.34 at 5.73
    Fighter Plate B: maw chase Running x3.50 at 8.59
    Fighter Plate C: standard chase Running x2.72 at 6.68
    Fighter Plate C: maw chase Running x3.70 at 9.06
- mm7/mm7_m406.glb (source assets_source/worlds/mm7/models/mm7_m406.glb; biped; authored walk 1.72 run 2.45; projects: mm7_m406_claude, mm7_m406_reduce_claude)
    Swordsman A: standard chase Running x1.51 at 3.7
    Swordsman A: maw chase Running x2.80 at 6.89
    Swordsman B: standard chase Running x1.71 at 4.2
    Swordsman B: maw chase Running x2.92 at 7.14
    Swordsman C: standard chase Running x1.92 at 4.71
    Swordsman C: maw chase Running x3.02 at 7.39

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
