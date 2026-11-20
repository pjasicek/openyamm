You are package `h04` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h04/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_pfem.glb (source assets_source/worlds/mm6/models/mm6_pfem.glb; biped; authored walk 1.46 run 1.46; projects: mm6_peasants_fix_claude, mm6_pfem_claude, mm6_pfem_codex, mm6_pfem_reduce_claude, mm6_pfem_v4_claude)
    PeasantF1 A: standard chase Walking x1.72 at 2.51
    PeasantF1 A: maw chase Walking x1.72 at 2.51
    PeasantF1 B: standard chase Walking x1.72 at 2.51
    PeasantF1 B: maw chase Walking x1.72 at 2.51
    Peasantf1 C: standard chase Walking x1.72 at 2.51
    Peasantf1 C: maw chase Walking x1.72 at 2.51
- mm6/mm6_pmn2.glb (source assets_source/worlds/mm6/models/mm6_pmn2.glb; biped; authored walk 1.31 run 4.51; projects: mm6_pmn2_claude, mm6_pmn2_reduce_claude)
    PeasantM2 A: standard chase Walking x2.02 at 2.65
    PeasantM2 A: maw chase Walking x2.02 at 2.65
    PeasantM2 B: standard chase Walking x2.02 at 2.65
    PeasantM2 B: maw chase Walking x2.02 at 2.65
    PeasantM2 C: standard chase Walking x2.02 at 2.65
    PeasantM2 C: maw chase Walking x2.02 at 2.65
- mm6/mm6_pman_v2.glb (source assets_source/worlds/mm6/models/mm6_pman_v2.glb; biped; authored walk 1.6 run 1.6; projects: mm6_peasants_fix_claude, mm6_pman_claude_20261013, mm6_pman_v2_reduce_claude, mm6_pman_v3_claude)
    PeasantM1 A: standard chase Walking x1.68 at 2.68
    PeasantM1 A: maw chase Walking x1.68 at 2.68
    PeasantM1 B: standard chase Walking x1.68 at 2.68
    PeasantM1 B: maw chase Walking x1.68 at 2.68
    PeasantM1 C: standard chase Walking x1.68 at 2.68
    PeasantM1 C: maw chase Walking x1.68 at 2.68
- mm6/mm6_mep.glb (source assets_source/worlds/mm6/models/mm6_mep.glb; biped; authored walk 0.77 run 1.6; projects: mm6_mep_codex, mm6_mep_reduce_claude)
    PeasantM3 A: standard wander Walking x1.76 at 1.36
    PeasantM3 A: standard chase Running x1.70 at 2.72
    PeasantM3 A: maw chase Running x1.70 at 2.72
    PeasantM3 B: standard chase Running x1.94 at 3.1
    PeasantM3 B: maw chase Running x4.62 at 7.37
    PeasantM3 C: standard chase Running x2.42 at 3.88
    PeasantM3 C: maw chase Running x4.86 at 7.76
- mm6/mm6_fmp.glb (source assets_source/worlds/mm6/models/mm6_fmp.glb; biped; authored walk 1.01 run 1.56; projects: mm6_fmp_codex, mm6_fmp_reduce_claude, mm6_hrp_claude, mm6_seas_reduce_claude)
    PeasantF2 A: standard chase Run x1.70 at 2.65
    PeasantF2 A: maw chase Run x1.70 at 2.65
    PeasantF2 B: standard chase Run x1.70 at 2.65
    PeasantF2 B: maw chase Run x1.70 at 2.65
    PeasantF2 C: standard chase Run x1.70 at 2.65
    PeasantF2 C: maw chase Run x1.70 at 2.65

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
