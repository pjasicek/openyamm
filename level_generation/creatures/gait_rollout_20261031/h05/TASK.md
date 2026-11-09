You are package `h05` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h05/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_nobl.glb (source assets_source/worlds/mm6/models/mm6_nobl.glb; biped; authored walk 1.5 run 2.23; projects: mm6_nobl_codex, mm6_nobl_reduce_claude)
    Nobleman A: standard chase Running x1.79 at 4.0
    Nobleman A: maw chase Running x3.34 at 7.46
    Nobleman B: standard chase Running x2.04 at 4.55
    Nobleman B: maw chase Running x3.46 at 7.74
    Nobleman C: standard chase Running x2.28 at 5.1
    Nobleman C: maw chase Running x3.58 at 8.01
- mm6/mm6_natf.glb (source assets_source/worlds/mm6/models/mm6_natf.glb; biped; authored walk 1.5 run 2.32; projects: mm6_natf_anim_claude, mm6_natf_reduce_claude)
    PeasantF4 A: standard chase Running x1.76 at 4.08
    PeasantF4 A: maw chase Running x3.28 at 7.6
    PeasantF4 B: standard chase Running x1.99 at 4.63
    PeasantF4 B: maw chase Running x3.40 at 7.88
    PeasantF4 C: standard chase Running x2.24 at 5.19
    PeasantF4 C: maw chase Running x3.52 at 8.16
- mm6/mm6_mfp.glb (source assets_source/worlds/mm6/models/mm6_mfp.glb; biped; authored walk 0.75 run 1.74; projects: mm6_mfp_codex, mm6_mfp_reduce_claude)
    PeasantF3 A: standard chase Running x2.14 at 3.72
    PeasantF3 A: maw chase Running x4.26 at 7.44
    PeasantF3 B: standard chase Running x2.34 at 4.09
    PeasantF3 B: maw chase Running x4.38 at 7.63
    PeasantF3 C: standard chase Running x2.56 at 4.47
    PeasantF3 C: maw chase Running x4.48 at 7.81
- mm6/mm6_mer1.glb (source assets_source/worlds/mm6/models/mm6_mer1.glb; biped; authored walk 1.05 run 1.63; projects: mm6_mer1_reduce_claude)
    Merchant A: standard chase Running x1.66 at 2.69
    Merchant A: maw chase Running x1.66 at 2.69
    Merchant B: standard chase Running x1.66 at 2.69
    Merchant B: maw chase Running x1.66 at 2.69
    Merchant C: standard chase Running x1.66 at 2.69
    Merchant C: maw chase Running x1.66 at 2.69
- mm6/mm6_natm.glb (source assets_source/worlds/mm6/models/mm6_natm.glb; biped; authored walk 1.69 run 2.45; projects: mm6_natm_claude, mm6_natm_reduce_claude)
    PeasantM4 A: standard chase Running x1.70 at 4.18
    PeasantM4 A: maw chase Running x3.18 at 7.79
    PeasantM4 B: standard chase Running x1.94 at 4.75
    PeasantM4 B: maw chase Running x3.30 at 8.08
    PeasantM4 C: standard chase Running x2.16 at 5.32
    PeasantM4 C: maw chase Running x3.40 at 8.37

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
