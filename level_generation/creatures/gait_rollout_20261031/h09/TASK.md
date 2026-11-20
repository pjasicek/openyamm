You are package `h09` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h09/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m398.glb (source assets_source/worlds/mm7/models/mm7_m398.glb; biped; authored walk 1.66 run 2.45; projects: mm7_m398_claude)
    Skeleton Warrior A: maw chase Running x2.80 at 6.86
    Skeleton Warrior B: standard chase Running x1.57 at 3.86
    Skeleton Warrior B: maw chase Running x2.68 at 6.57
    Skeleton Warrior C: standard chase Running x1.64 at 4.02
    Skeleton Warrior C: maw chase Running x2.58 at 6.31
- mm7/mm7_m430.glb (source assets_source/worlds/mm7/models/mm7_m430.glb; biped; authored walk 1.37 run 2.45; projects: mm7_m430_claude)
    Wight A: maw chase Running x2.86 at 7.01
    Wight B: maw chase Running x2.92 at 7.19
    Wight C: standard chase Running x1.61 at 3.95
    Wight C: maw chase Running x3.00 at 7.37
- mm7/mm7_m270.glb (source assets_source/worlds/mm7/models/mm7_m270.glb; biped; authored walk 2.12 run 2.45; projects: mm7_m270_claude)
    Lich A: standard wander Walking x0.73 at 1.54
    Lich C: standard chase Running x1.53 at 3.76
    Lich C: maw chase Running x1.53 at 3.76
- mm7/mm7_m470.glb (source assets_source/worlds/mm7/models/mm7_m470.glb; biped; authored walk 1.74 run 2.45; projects: mm7_m470_claude)
    Ghoul A: maw chase Running x2.70 at 6.64
    Ghoul B: maw chase Running x2.78 at 6.81
    Ghoul C: maw chase Running x2.84 at 6.99
- mm7/mm7_m438.glb (source assets_source/worlds/mm7/models/mm7_m438.glb; biped; authored walk 0.82 run 1.95; projects: mm7_m438_claude, mm7_m438_reduce_claude)
    Zombie A: standard wander Walking x1.56 at 1.28
    Zombie A: maw chase Running x3.12 at 6.08
    Zombie B: standard wander Walking x1.76 at 1.44
    Zombie B: maw chase Running x3.20 at 6.24
    Zombie C: standard wander Walking x1.95 at 1.6
    Zombie C: standard chase Running x1.64 at 3.2
    Zombie C: maw chase Running x3.28 at 6.39

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
