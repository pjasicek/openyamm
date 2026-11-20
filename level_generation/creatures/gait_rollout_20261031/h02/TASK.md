You are package `h02` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h02/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_wwf.glb (source assets_source/worlds/mm6/models/mm6_wwf.glb; biped; authored walk 1.21 run 3.03; projects: mm6_wfigt1_claude, mm6_wwf_reduce_claude)
    Werewolf A: standard wander Walking x1.71 at 2.07
    Werewolf A: maw chase Running x2.04 at 6.2
    Werewolf B: standard wander Walking x1.83 at 2.21
    Werewolf B: maw chase Running x2.10 at 6.34
    Werewolf C: standard wander Walking x2.00 at 2.41
    Werewolf C: standard chase Running x1.59 at 4.82
    Werewolf C: maw chase Running x2.16 at 6.55
- mm6/mm6_dwa1.glb (source assets_source/worlds/mm6/models/mm6_dwa1.glb; biped; authored walk 1.11 run 1.72; projects: mm6_dwa1_codex, mm6_dwa1_reduce_claude)
    BDwarf A: standard chase Running x1.82 at 3.15
    BDwarf A: maw chase Running x4.34 at 7.48
    BDwarf B: standard chase Running x1.91 at 3.29
    BDwarf B: maw chase Running x4.14 at 7.12
    BDwarf C: standard chase Running x1.98 at 3.41
    BDwarf C: maw chase Running x3.96 at 6.82
- mm6/mm6_jak1.glb (source assets_source/worlds/mm6/models/mm6_jak1.glb; biped; authored walk 1.66 run 1.66; projects: mm6_jak1_codex)
    Jackalman A: standard chase Walking x2.42 at 4.03
    Jackalman A: maw chase Walking x4.52 at 7.51
    Jackalman B: standard chase Walking x2.64 at 4.39
    Jackalman B: maw chase Walking x4.64 at 7.69
    Jackalman C: standard wander Walking x1.55 at 2.56
    Jackalman C: standard chase Walking x3.10 at 5.13
    Jackalman C: maw chase Walking x4.86 at 8.06
- mm6/mm6_min1.glb (source assets_source/worlds/mm6/models/mm6_min1.glb; biped; authored walk 2.1 run 2.65; projects: mm6_min1_r3_reduce_claude, mm6_min1_reduce_claude)
    BMinotaur A: standard chase Running x1.87 at 4.95
    BMinotaur A: maw chase Running x3.18 at 8.42
    BMinotaur B: standard chase Running x1.70 at 4.51
    BMinotaur B: maw chase Running x2.82 at 7.46
    BMinotaur C: standard chase Running x1.74 at 4.62
    BMinotaur C: maw chase Running x2.62 at 6.94

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
