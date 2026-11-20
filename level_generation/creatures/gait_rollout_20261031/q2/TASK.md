You are package `q2` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/q2/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m382.glb (source assets_source/worlds/mm7/models/mm7_m382.glb; multi-legged; authored walk 4.48 run 8.96 sprint 13.2; projects: mm7_m382_claude, mm7_m382_reduce_claude)
    zrat a: standard wander Walk2 x0.63 at 2.8
    zrat b: standard wander Walk2 x0.63 at 2.8
    zrat c: standard wander Walk2 x0.63 at 2.8
- mm7/mm7_m509.glb (source assets_source/worlds/mm7/models/mm7_m509.glb; multi-legged; authored walk 1.12 run 1.12; projects: mm7_m509_claude)
    zdog a: standard chase Walking x2.12 at 2.36
    zdog a: maw chase Walking x2.12 at 2.36
    zdog b: standard chase Walking x2.12 at 2.36
    zdog b: maw chase Walking x2.12 at 2.36
    zdog c: standard chase Walking x2.12 at 2.36
    zdog c: maw chase Walking x2.12 at 2.36
- mm7/mm7_7m500.glb (source assets_source/worlds/mm7/models/mm7_7m500.glb; multi-legged; authored walk 0.7 run 0.7; projects: mm7_7m500_claude)
    zcat a: standard chase Walking x1.99 at 1.4
    zcat a: maw chase Walking x1.99 at 1.4
    zcat b: standard chase Walking x1.99 at 1.4
    zcat b: maw chase Walking x1.99 at 1.4
    zcat c: standard chase Walking x1.99 at 1.4
    zcat c: maw chase Walking x1.99 at 1.4
- mm8/mm8_wolf.glb (source assets_source/worlds/mm8/models/mm8_wolf.glb; multi-legged; authored walk 0.34 run 0.77; projects: mm8_m512_claude, mm8_wolf_reduce_claude)
    Dire Wolf A: standard wander Running x1.51 at 1.16
    Dire Wolf A: standard chase Running x3.02 at 2.32
    Dire Wolf A: maw chase Running x4.80 at 3.68
    Dire Wolf B: standard chase Running x2.82 at 2.16
    Dire Wolf B: maw chase Running x4.26 at 3.27
    Dire Wolf C: standard chase Running x2.56 at 1.97
    Dire Wolf C: maw chase Running x3.72 at 2.85

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
