You are package `h14` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h14/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m352.glb (source assets_source/worlds/mm7/models/mm7_m352.glb; biped; authored walk 1.68 run 1.68; projects: mm7_m352_claude, mm7_m352_reduce_claude)
    Peasant Human1 MaleA A: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleA A: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleA B: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleA B: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleA C: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleA C: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleB A: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleB A: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleB B: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleB B: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleB C: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleB C: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleC A: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleC A: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleC B: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleC B: maw chase Walking x1.62 at 2.73
    Peasant Human1 MaleC C: standard chase Walking x1.62 at 2.73
    Peasant Human1 MaleC C: maw chase Walking x1.62 at 2.73
- mm7/mm7_m342.glb (source assets_source/worlds/mm7/models/mm7_m342.glb; biped; authored walk 2.09 run 2.09; projects: mm7_m342_claude, mm7_m342_reduce_claude)
    Peasant Human1 FemaleA A: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleA B: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleA C: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleB A: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleB B: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleB C: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleC A: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleC B: standard wander Walking x0.70 at 1.47
    Peasant Human1 FemaleC C: standard wander Walking x0.70 at 1.47
- mm7/mm7_m362.glb (source assets_source/worlds/mm7/models/mm7_m362.glb; biped; authored walk 1.62 run 1.62; projects: mm7_m362_claude, mm7_m362_reduce_claude)
    Peasant Human2 MaleA A: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleA A: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleA B: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleA B: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleA C: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleA C: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleB A: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleB A: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleB B: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleB B: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleB C: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleB C: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleC A: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleC A: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleC B: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleC B: maw chase Walking x1.89 at 3.07
    Peasant Human2 MaleC C: standard chase Walking x1.89 at 3.07
    Peasant Human2 MaleC C: maw chase Walking x1.89 at 3.07
- mm7/mm7_m372.glb (source assets_source/worlds/mm7/models/mm7_m372.glb; biped; authored walk 2.04 run 2.04; projects: mm7_m372_claude, mm7_m372_reduce_claude)
    Peasant Human2 FemaleA A: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleA B: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleA C: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleB A: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleB B: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleB C: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleC A: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleC B: standard wander Walking x0.68 at 1.4
    Peasant Human2 FemaleC C: standard wander Walking x0.68 at 1.4

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
