You are package `h22` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h22/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_m596.glb (source assets_source/worlds/mm8/models/mm8_m596.glb; biped; authored walk 2.32 run 4.72; projects: mm8_crystal_material_claude, mm8_m596_claude, mm8_m596_v2_claude)
    Crystal Walker A: maw chase Run2 x1.83 at 8.65
- mm8/mm8_m592.glb (source assets_source/worlds/mm8/models/mm8_m592.glb; biped; authored walk 1.17 run 2.24; projects: mm8_m472_claude, mm8_m592_claude, mm8_m592_reduce_claude)
    Plane Guardian A: maw chase Running x2.30 at 5.15
    Plane Guardian B: maw chase Running x2.30 at 5.15
    Plane Guardian C: maw chase Running x2.30 at 5.15
    Wimpy Plane Guardian A: standard chase Running x1.92 at 4.29
    Wimpy Plane Guardian A: maw chase Running x3.84 at 8.58
    Wimpy Plane Guardian B: standard chase Running x1.92 at 4.29
    Wimpy Plane Guardian B: maw chase Running x3.84 at 8.58
    Wimpy Plane Guardian C: standard chase Running x1.92 at 4.29
    Wimpy Plane Guardian C: maw chase Running x3.84 at 8.58

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
