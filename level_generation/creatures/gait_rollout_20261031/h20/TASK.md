You are package `h20` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h20/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_m476.glb (source assets_source/worlds/mm8/models/mm8_m476.glb; biped; authored walk 1.85 run 3.67; projects: mm8_m476_claude, mm8_m476_reduce_claude)
    Troll A: standard wander Walking x0.73 at 1.35
    Troll A: standard chase Running x0.74 at 2.7
    Troll B: maw chase Running x1.51 at 5.54
    Troll C: maw chase Running x1.58 at 5.81
- mm8/mm8_m484.glb (source assets_source/worlds/mm8/models/mm8_m484.glb; biped; authored walk 2.11 run 3.05; projects: mm8_m484_claude, mm8_m484_reduce_claude)
    Minotaur A: standard wander Walking x0.68 at 1.44
    Minotaur A: maw chase Running x1.61 at 4.91
    Minotaur B: standard wander Walking x0.71 at 1.5
    Minotaur B: maw chase Running x1.63 at 4.96
    Minotaur C: maw chase Running x1.70 at 5.19
- mm8/mm8_m480.glb (source assets_source/worlds/mm8/models/mm8_m480.glb; biped; authored walk 1.87 run 1.87; projects: mm7_m461_claude, mm8_m480_claude, mm8_m480_reduce_claude)
    Troll Pesant A: standard wander Walking x0.58 at 1.09
    Troll Pesant B: standard wander Walking x0.58 at 1.09
    Troll Pesant C: standard wander Walking x0.58 at 1.09
- mm8/mm8_m488.glb (source assets_source/worlds/mm8/models/mm8_m488.glb; biped; authored walk 2.15 run 2.72; projects: mm8_m488_claude, mm8_m488_reduce_claude)
    Minotaur Pesant A: standard chase Running x1.65 at 4.5
    Minotaur Pesant A: maw chase Running x3.08 at 8.38
    Minotaur Pesant B: standard chase Running x1.88 at 5.11
    Minotaur Pesant B: maw chase Running x3.20 at 8.69
    Minotaur Pesant C: standard chase Running x2.10 at 5.72
    Minotaur Pesant C: maw chase Running x3.30 at 8.99

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
