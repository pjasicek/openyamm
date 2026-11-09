You are package `h16` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h16/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_lizardman_peasant.glb (source assets_source/worlds/mm8/models/mm8_lizardman_peasant.glb; biped; authored walk 1.38 run 1.38; projects: mm8_lizardman_peasant_reduce_claude, mm8_lizardman_peasant_tiers_claude)
    Lizardmen Male (Peasant) A: standard chase Walk x2.52 at 3.47
    Lizardmen Male (Peasant) A: maw chase Walk x5.02 at 6.93
    Lizardmen Male (Peasant) B: standard chase Walk x2.70 at 3.73
    Lizardmen Male (Peasant) B: maw chase Walk x5.10 at 7.06
    Lizardmen Male (Peasant) C: standard chase Walk x2.88 at 3.99
    Lizardmen Male (Peasant) C: maw chase Walk x5.20 at 7.19
- mm8/mm8_m456.glb (source assets_source/worlds/mm8/models/mm8_m456.glb; biped; authored walk 1.73 run 2.28; projects: mm8_m456_claude, mm8_m456_reduce_claude)
    Dragon Hunter A: standard chase Running x1.77 at 4.03
    Dragon Hunter A: maw chase Running x3.14 at 7.15
    Dragon Hunter B: standard chase Running x1.96 at 4.46
    Dragon Hunter B: maw chase Running x3.24 at 7.37
    Dragon Hunter C: standard chase Running x2.14 at 4.89
    Dragon Hunter C: maw chase Running x3.34 at 7.58
- mm8/mm8_m576.glb (source assets_source/worlds/mm8/models/mm8_m576.glb; biped; authored walk 1.49 run 2.37; projects: mm8_m576_claude, mm8_m576_reduce_claude)
    Triton A: standard chase Running x1.58 at 3.74
    Triton A: maw chase Running x2.68 at 6.36
    Triton B: standard chase Running x1.52 at 3.59
    Triton B: maw chase Running x2.50 at 5.94
    Triton C: standard chase Running x1.63 at 3.85
    Triton C: maw chase Running x2.44 at 5.77
- mm8/mm8_m404.glb (source assets_source/worlds/mm8/models/mm8_m404.glb; biped; authored walk 1.81 run 1.81; projects: mm8_m404_reduce_claude, mm8_m404_walk_claude)
    Lizardmen Warrior A: standard chase Walking x1.63 at 2.95
    Lizardmen Warrior A: maw chase Walking x3.96 at 7.17
    Lizardmen Warrior B: standard chase Walking x1.84 at 3.33
    Lizardmen Warrior B: maw chase Walking x4.06 at 7.36
    Lizardmen Warrior C: standard chase Walking x2.04 at 3.71
    Lizardmen Warrior C: maw chase Walking x4.16 at 7.55

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
