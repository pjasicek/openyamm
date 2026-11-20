You are package `q3` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/q3/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m278.glb (source assets_source/worlds/mm7/models/mm7_m278.glb; multi-legged; authored walk 1.59 run 3.58; projects: mm7_m278_claude, mm7_m278_reduce_claude)
    Manticore A: standard wander Walking x1.57 at 2.49
- mm7/mm7_m266.glb (source assets_source/worlds/mm7/models/mm7_m266.glb; multi-legged; authored walk 1.3 run 3.17; projects: mm7_m266_claude, mm7_m266_reduce_claude)
    Hydra B: standard chase Walking x1.57 at 2.05
    Hydra B: maw chase Walking x1.57 at 2.05
    Hydra C: standard chase Walking x1.56 at 2.03
    Hydra C: maw chase Walking x1.56 at 2.03
- mm8/mm8_m564.glb (source assets_source/worlds/mm8/models/mm8_m564.glb; multi-legged; authored walk 0.48 run 0.8; projects: mm8_m564_claude, mm8_m564_reduce_claude)
    Gorgon A: standard chase Running x1.56 at 1.25
    Gorgon A: maw chase Running x3.12 at 2.49
    Gorgon B: standard chase Running x1.71 at 1.37
    Gorgon B: maw chase Running x3.20 at 2.55
    Gorgon C: standard chase Running x1.87 at 1.49
    Gorgon C: maw chase Running x3.28 at 2.62
- mm8/mm8_m516.glb (source assets_source/worlds/mm8/models/mm8_m516.glb; multi-legged; authored walk 1.0 run 2.4; projects: mm8_m516_claude, mm8_m516_reduce_claude)
    Thunder Lizard A: standard chase Running x2.32 at 5.55
    Thunder Lizard A: maw chase Running x4.30 at 10.34
    Thunder Lizard B: standard chase Running x2.52 at 6.05
    Thunder Lizard B: maw chase Running x4.42 at 10.59
    Thunder Lizard C: standard chase Running x2.74 at 6.56
    Thunder Lizard C: maw chase Running x4.52 at 10.85

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
