You are package `h01` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h01/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_thf.glb (source assets_source/worlds/mm6/models/mm6_thf.glb; biped; authored walk 1.27 run 2.88; projects: mm6_thf_claude, mm6_thf_reduce_claude)
    BThief A: standard wander Walking x1.80 at 2.3
    BThief A: standard chase Running x1.60 at 4.6
    BThief A: maw chase Running x2.72 at 7.82
    BThief B: standard wander Walking x1.88 at 2.39
    BThief B: standard chase Running x1.66 at 4.78
    BThief B: maw chase Running x2.76 at 7.91
    BThief C: standard chase Running x1.73 at 4.97
    BThief C: maw chase Running x2.78 at 8.01
- mm6/mm6_bar1.glb (source assets_source/worlds/mm6/models/mm6_bar1.glb; biped; authored walk 2.06 run 2.18; projects: mm6_bar1_claude, mm6_bar1_reduce_claude)
    Barbarian A: standard chase Running x2.40 at 5.26
    Barbarian A: maw chase Running x3.98 at 8.7
    Barbarian B: standard chase Running x2.60 at 5.66
    Barbarian B: maw chase Running x4.08 at 8.9
    Barbarian C: standard chase Running x2.78 at 6.07
    Barbarian C: maw chase Running x4.18 at 9.1
- mm6/mm6_fgt.glb (source assets_source/worlds/mm6/models/mm6_fgt.glb; biped; authored walk 2.0 run 2.0; projects: mm6_fgt_claude, mm6_fgt_reduce_claude)
    FighterLeath A: standard chase Walking x1.63 at 3.26
    FighterLeath A: maw chase Walking x3.26 at 6.51
    FighterLeath B: standard chase Walking x1.79 at 3.58
    FighterLeath B: maw chase Walking x3.34 at 6.68
    FighterLeath C: standard chase Walking x1.95 at 3.91
    FighterLeath C: maw chase Walking x3.42 at 6.84
- mm6/mm6_figc.glb (source assets_source/worlds/mm6/models/mm6_figc.glb; biped; authored walk 2.23 run 2.23; projects: mm6_figc_codex, mm6_figc_reduce_claude)
    FighterChain A: standard chase Walking x1.57 at 3.49
    FighterChain A: maw chase Walking x2.92 at 6.51
    FighterChain B: standard chase Walking x1.71 at 3.81
    FighterChain B: maw chase Walking x3.00 at 6.67
    FighterChain C: standard chase Walking x1.85 at 4.13
    FighterChain C: maw chase Walking x3.06 at 6.82

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
