You are package `h06` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h06/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_demon.glb (source assets_source/worlds/mm6/models/mm6_demon.glb; biped; authored walk 1.19 run 3.49; projects: hes_kreegan_claude, mm6_demon_reduce_claude)
    Demon A: standard wander Walking x1.60 at 1.91
    Demon A: maw chase Running x2.18 at 7.63
    Demon B: standard wander Walking x1.87 at 2.23
    Demon B: maw chase Running x2.16 at 7.57
    Demon C: standard wander Walking x2.10 at 2.5
    Demon C: maw chase Running x2.16 at 7.51
- mm6/mm6_gua.glb (source assets_source/worlds/mm6/models/mm6_gua.glb; biped; authored walk 1.27 run 4.44; projects: mm6_gua_claude, mm6_gua_reduce_claude)
    Guard A: standard chase Running x0.71 at 3.14
- mm6/mm6_gob2.glb (source assets_source/worlds/mm6/models/mm6_gob2.glb; biped; authored walk 1.87 run 3.59; projects: mm6_gob2_claude, mm6_gob2_reduce_claude)
    BGoblin A: maw chase Running x2.18 at 7.83
    BGoblin B: maw chase Running x2.04 at 7.36
    BGoblin C: maw chase Running x1.94 at 6.96
- mm6/mm6_ske.glb (source assets_source/worlds/mm6/models/mm6_ske.glb; biped; authored walk 0.71 run 2.25; projects: mm6_ske_claude, mm6_ske_reduce_claude)
    Skeleton A: standard chase Running x1.58 at 3.56
    Skeleton A: maw chase Running x2.94 at 6.63
    Skeleton B: standard chase Running x1.57 at 3.54
    Skeleton B: maw chase Running x2.68 at 6.02
    Skeleton C: standard chase Running x1.57 at 3.52
    Skeleton C: maw chase Running x2.46 at 5.54
- mm6/mm6_lzd.glb (source assets_source/worlds/mm6/models/mm6_lzd.glb; biped; authored walk 1.71 run 1.71; projects: mm6_lzd_reduce_claude)
    LizardArch A: standard chase Walking x1.55 at 2.65
    LizardArch A: maw chase Walking x1.55 at 2.65
- mm6/mm6_ert.glb (source assets_source/worlds/mm6/models/mm6_ert.glb; biped; authored walk 1.89 run 1.89; projects: mm6_ert_codex, mm8_m504_claude)
    ElemEarth A: standard chase Walking x2.84 at 5.35
    ElemEarth A: maw chase Walking x5.28 at 9.97
    ElemEarth B: standard wander Walking x1.55 at 2.92
    ElemEarth B: standard chase Walking x3.10 at 5.83
    ElemEarth B: maw chase Walking x5.42 at 10.21
    ElemEarth C: standard wander Walking x1.68 at 3.16
    ElemEarth C: standard chase Walking x3.36 at 6.32
    ElemEarth C: maw chase Walking x5.54 at 10.45

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
