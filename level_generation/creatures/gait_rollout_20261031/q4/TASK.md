You are package `q4` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/q4/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_7m504.glb (source assets_source/worlds/mm7/models/mm7_7m504.glb; multi-legged; authored walk 0.92 run 0.92; projects: mm7_7m504_claude)
    zchicken a: standard chase Walking x2.12 at 1.95
    zchicken a: maw chase Walking x2.12 at 1.95
    zchicken b: standard chase Walking x2.12 at 1.95
    zchicken b: maw chase Walking x2.12 at 1.95
    zchicken c: standard chase Walking x2.12 at 1.95
    zchicken c: maw chase Walking x2.12 at 1.95
- mm8/mm8_centaur.glb (source assets_source/worlds/mm8/models/mm8_centaur.glb; multi-legged; authored walk 1.51 run 3.32; projects: mm8_centaur_reduce_claude, mm8_m532_claude)
    Centaur A: standard wander Walking x1.78 at 2.68
    Centaur A: standard chase Running x1.62 at 5.37
    Centaur A: maw chase Running x1.62 at 5.37
    Centaur B: standard wander Walking x1.85 at 2.78
    Centaur B: standard chase Running x1.68 at 5.56
    Centaur B: maw chase Running x1.68 at 5.56
    Centaur C: standard chase Running x1.74 at 5.76
    Centaur C: maw chase Running x1.74 at 5.76
- mm8/mm8_m548.glb (source assets_source/worlds/mm8/models/mm8_m548.glb; multi-legged; authored walk 0.32 run 0.57; projects: mm8_crystal_material_claude, mm8_m548_codex, mm8_m548_reduce_claude)
    Crystal Dragon A: standard chase Running x2.92 at 1.67
    Crystal Dragon A: maw chase Running x2.92 at 1.67
    Crystal Dragon B: standard chase Running x2.64 at 1.51
    Crystal Dragon B: maw chase Running x2.64 at 1.51
    Crystal Dragon C: standard chase Running x2.48 at 1.43
    Crystal Dragon C: maw chase Running x2.48 at 1.43
- mm8/mm8_m544.glb (source assets_source/worlds/mm8/models/mm8_m544.glb; multi-legged; authored walk 0.64 run 0.85; projects: mm8_m544_claude, mm8_m544_reduce_claude)
    Unicorn C: standard wander Walking x0.72 at 0.46

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
