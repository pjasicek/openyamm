You are package `h10` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h10/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m162.glb (source assets_source/worlds/mm7/models/mm7_m162.glb; biped; authored walk 1.8 run 3.27; projects: mm7_m162_claude, mm7_m162_reduce_claude)
    Behemoth A: maw chase Running x2.16 at 7.08
    Behemoth B: maw chase Running x2.00 at 6.52
    Behemoth C: maw chase Running x1.84 at 6.0
- mm7/mm7_m190.glb (source assets_source/worlds/mm7/models/mm7_m190.glb; biped; authored walk 1.08 run 3.47; projects: mm7_m190_claude, mm7_m190_reduce_claude)
    Dwarf A: maw chase Running x2.10 at 7.26
    Dwarf B: standard wander Walking x1.52 at 1.64
    Dwarf B: maw chase Running x2.04 at 7.1
    Dwarf C: standard wander Walking x1.61 at 1.74
    Dwarf C: maw chase Running x2.00 at 6.95
- mm7/mm7_m254.glb (source assets_source/worlds/mm7/models/mm7_m254.glb; biped; authored walk 1.68 run 1.68; projects: mm7_m254_claude, mm7_m254_reduce_claude)
    Golem A: standard wander Walking x0.63 at 1.05
    Golem A: maw chase Walking x2.98 at 4.99
    Golem B: standard wander Walking x0.67 at 1.12
    Golem B: maw chase Walking x3.02 at 5.06
    Golem C: standard wander Walking x0.70 at 1.18
    Golem C: maw chase Walking x3.06 at 5.12
- mm7/mm7_m461.glb (source assets_source/worlds/mm7/models/mm7_m461.glb; biped; authored walk 1.87 run 1.87; projects: mm7_m461_claude)
    ATroll A: standard wander Walking x0.56 at 1.04
    ATroll A: maw chase Walking x2.22 at 4.15
    ATroll B: standard wander Walking x0.61 at 1.14
    ATroll B: maw chase Walking x2.28 at 4.25
    ATroll C: maw chase Walking x2.38 at 4.46
- mm7/mm7_m286.glb (source assets_source/worlds/mm7/models/mm7_m286.glb; biped; authored walk 1.67 run 2.89; projects: mm7_m286_claude)
    AMinotaur A: maw chase Running x1.95 at 5.64
    AMinotaur B: maw chase Running x1.70 at 4.89
    AMinotaur C: standard chase Walking x1.59 at 2.66
    AMinotaur C: maw chase Walking x2.38 at 3.98

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
