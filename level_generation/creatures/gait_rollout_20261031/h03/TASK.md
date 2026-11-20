You are package `h03` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h03/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_cle.glb (source assets_source/worlds/mm6/models/mm6_cle.glb; biped; authored walk 1.37 run 1.37; projects: mm6_cle_claude, mm6_cle_reduce_claude)
    Cleric A: standard chase Walking x2.12 at 2.91
    Cleric A: maw chase Walking x2.12 at 2.91
    Cleric B: standard chase Walking x2.38 at 3.27
    Cleric B: maw chase Walking x2.38 at 3.27
    Cleric C: standard chase Walking x2.66 at 3.64
    Cleric C: maw chase Walking x2.66 at 3.64
- mm6/mm6_dru1.glb (source assets_source/worlds/mm6/models/mm6_dru1.glb; biped; authored walk 1.77 run 1.77; projects: mm6_dru1_claude, mm6_dru1_reduce_claude)
    Druidess A: standard chase Walking x1.63 at 2.9
    Druidess A: maw chase Walking x1.63 at 2.9
    Druidess B: standard chase Walking x1.84 at 3.26
    Druidess B: maw chase Walking x1.84 at 3.26
    Druidess C: standard chase Walking x2.04 at 3.62
    Druidess C: maw chase Walking x2.04 at 3.62
- mm6/mm6_lch.glb (source assets_source/worlds/mm6/models/mm6_lch.glb; biped; authored walk 1.98 run 1.98; projects: none)
    BLich A: standard chase Walking x1.63 at 3.23
    BLich A: maw chase Walking x1.63 at 3.23
    BLich B: standard chase Walking x1.81 at 3.58
    BLich B: maw chase Walking x1.81 at 3.58
    BLich C: standard chase Walking x1.99 at 3.94
    BLich C: maw chase Walking x1.99 at 3.94
- mm6/mm6_sor1.glb (source assets_source/worlds/mm6/models/mm6_sor1.glb; biped; authored walk 1.78 run 1.78; projects: mm6_sor1_codex)
    Sorcerer A: standard chase Walking x2.12 at 3.77
    Sorcerer A: maw chase Walking x2.12 at 3.77
    Sorcerer B: standard chase Walking x2.32 at 4.15
    Sorcerer B: maw chase Walking x2.32 at 4.15
    Sorcerer C: standard chase Walking x2.54 at 4.52
    Sorcerer C: maw chase Walking x2.54 at 4.52
- mm6/mm6_arc1.glb (source assets_source/worlds/mm6/models/mm6_arc1.glb; biped; authored walk 1.08 run 1.08; projects: mm6_arc1_reduce_claude)
    BArcher A: standard chase Walking x2.44 at 2.63
    BArcher A: maw chase Walking x2.44 at 2.63
    BArcher B: standard chase Walking x2.60 at 2.82
    BArcher B: maw chase Walking x2.60 at 2.82
    BArcher C: standard chase Walking x2.78 at 3.01
    BArcher C: maw chase Walking x2.78 at 3.01

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
