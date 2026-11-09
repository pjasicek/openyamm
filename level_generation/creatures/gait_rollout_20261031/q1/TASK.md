You are package `q1` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/q1/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm6/mm6_spi1.glb (source assets_source/worlds/mm6/models/mm6_spi1.glb; multi-legged; authored walk 1.61 run 3.23; projects: mm6_spi1_claude, mm6_spi1_reduce_claude)
    BSpider A: maw chase Run2 x2.14 at 6.92
    BSpider B: maw chase Run2 x1.63 at 5.26
- mm6/mm6_ckt.glb (source assets_source/worlds/mm6/models/mm6_ckt.glb; multi-legged; authored walk 0.67 run 0.67; projects: mm6_ckt_claude, mm6_ckt_reduce_claude)
    Cockatrice A: standard chase Walking x1.67 at 1.12
    Cockatrice A: maw chase Walking x2.92 at 1.96
    Cockatrice B: standard chase Walking x1.81 at 1.21
    Cockatrice B: maw chase Walking x3.00 at 2.01
    Cockatrice C: standard chase Walking x1.95 at 1.31
    Cockatrice C: maw chase Walking x3.06 at 2.06
- mm6/mm6_wyrm.glb (source assets_source/worlds/mm6/models/mm6_wyrm.glb; multi-legged; authored walk 0.16 run 0.3; projects: mm6_drr1_claude)
    DragonLand C: standard wander Walking x0.69 at 0.11
- mm7/mm7_m402.glb (source assets_source/worlds/mm7/models/mm7_m402.glb; multi-legged; authored walk 2.62 run 5.24; projects: mm7_m402_claude, mm7_m402_reduce_claude)
    Spider A: maw chase Run2 x1.71 at 8.96
    Spider B: maw chase Run2 x1.67 at 8.76
    Spider C: maw chase Run2 x1.63 at 8.57

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
