You are package `h12` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h12/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m214.glb (source assets_source/worlds/mm7/models/mm7_m214.glb; biped; authored walk 1.85 run 1.85; projects: mm7_m214_claude, mm7_m214_reduce_claude)
    Elf Archer A: standard wander Walking x0.72 at 1.34
- mm7/mm7_m218.glb (source assets_source/worlds/mm7/models/mm7_m218.glb; biped; authored walk 1.78 run 2.89; projects: mm7_m218_claude, mm7_m218_reduce_claude)
    Elf Spearman A: standard chase Running x1.64 at 4.73
    Elf Spearman A: maw chase Running x2.86 at 8.28
    Elf Spearman B: standard chase Running x1.77 at 5.12
    Elf Spearman B: maw chase Running x2.92 at 8.47
    Elf Spearman C: standard chase Running x1.91 at 5.52
    Elf Spearman C: maw chase Running x3.00 at 8.67
- mm7/mm7_m475.glb (source assets_source/worlds/mm7/models/mm7_m475.glb; biped; authored walk 2.05 run 2.05; projects: mm7_m475_claude)
    zBlasterGuy A: standard chase Walking x2.20 at 4.52
    zBlasterGuy A: maw chase Walking x2.20 at 4.52
    zBlasterGuy B: standard chase Walking x2.20 at 4.52
    zBlasterGuy B: maw chase Walking x2.20 at 4.52
    zBlasterGuy C: standard chase Walking x2.20 at 4.52
    zBlasterGuy C: maw chase Walking x2.20 at 4.52
- mm7/mm7_m178.glb (source assets_source/worlds/mm7/models/mm7_m178.glb; biped; authored walk 1.31 run 1.98; projects: mm7_m178_claude, mm7_m178_reduce_claude)
    Devil A: standard chase Running x1.87 at 3.71
    Devil A: maw chase Running x1.87 at 3.71
    Devil B: standard chase Running x2.34 at 4.63
    Devil B: maw chase Running x2.34 at 4.63
    Devil C: standard chase Running x2.80 at 5.56
    Devil C: maw chase Running x2.80 at 5.56
- mm7/mm7_m246.glb (source assets_source/worlds/mm7/models/mm7_m246.glb; biped; authored walk 1.75 run 2.45; projects: mm7_m246_claude, mm7_m246_reduce_claude)
    Goblin A: maw chase Running x2.82 at 6.91
    Goblin B: maw chase Running x2.86 at 7.0
    Goblin C: maw chase Running x2.88 at 7.09

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
