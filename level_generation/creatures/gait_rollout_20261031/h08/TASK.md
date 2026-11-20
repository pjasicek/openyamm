You are package `h08` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h08/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m418.glb (source assets_source/worlds/mm7/models/mm7_m418.glb; biped; authored walk 1.66 run 2.77; projects: mm7_m418_claude)
    Troglodyte A: standard chase Running x2.02 at 5.6
    Troglodyte A: maw chase Running x3.76 at 10.43
    Troglodyte B: standard chase Running x2.20 at 6.11
    Troglodyte B: maw chase Running x3.86 at 10.69
    Troglodyte C: standard chase Running x2.38 at 6.62
    Troglodyte C: maw chase Running x3.96 at 10.94
- mm7/mm7_m410.glb (source assets_source/worlds/mm7/models/mm7_m410.glb; biped; authored walk 1.86 run 2.75; projects: mm7_m410_claude, mm7_m410_reduce_claude)
    Thief A: standard chase Running x1.62 at 4.45
    Thief A: maw chase Running x2.76 at 7.57
    Thief B: standard chase Running x1.68 at 4.63
    Thief B: maw chase Running x2.78 at 7.66
    Thief C: standard chase Running x1.75 at 4.81
    Thief C: maw chase Running x2.82 at 7.75
- mm7/mm7_m290.glb (source assets_source/worlds/mm7/models/mm7_m290.glb; biped; authored walk 1.86 run 1.86; projects: mm7_m290_claude, mm7_m290_reduce_claude)
    Monk A: standard chase Walking x1.96 at 3.65
    Monk A: maw chase Walking x3.92 at 7.3
    Monk B: standard chase Walking x2.16 at 4.01
    Monk B: maw chase Walking x4.02 at 7.48
    Monk C: standard chase Walking x2.36 at 4.38
    Monk C: maw chase Walking x4.12 at 7.66
- mm7/mm7_m422.glb (source assets_source/worlds/mm7/models/mm7_m422.glb; biped; authored walk 1.85 run 1.85; projects: mm7_m422_claude, mm7_m422_reduce_claude)
    Vampire A: standard chase Walking x1.99 at 3.69
    Vampire A: maw chase Walking x3.72 at 6.87
    Vampire B: standard chase Walking x2.18 at 4.02
    Vampire B: maw chase Walking x3.80 at 7.04
    Vampire C: standard chase Walking x2.36 at 4.36
    Vampire C: maw chase Walking x3.90 at 7.21

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
