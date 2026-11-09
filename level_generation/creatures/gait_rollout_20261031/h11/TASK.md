You are package `h11` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h11/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m170.glb (source assets_source/worlds/mm7/models/mm7_m170.glb; biped; authored walk 1.71 run 1.71; projects: mm7_m170_claude, mm7_m170_reduce_claude)
    Cleric Moon A: standard wander Walking x0.74 at 1.27
    Cleric Moon B: standard chase Walking x1.67 at 2.86
    Cleric Moon B: maw chase Walking x1.67 at 2.86
    Cleric Moon C: standard chase Walking x1.86 at 3.18
    Cleric Moon C: maw chase Walking x1.86 at 3.18
- mm7/mm7_m174.glb (source assets_source/worlds/mm7/models/mm7_m174.glb; biped; authored walk 1.74 run 1.74; projects: mm7_m174_claude, mm7_m174_reduce_claude)
    Cleric Sun A: standard wander Walking x0.62 at 1.08
    Cleric Sun B: standard wander Walking x0.70 at 1.22
    Cleric Sun C: standard chase Walking x1.55 at 2.7
    Cleric Sun C: maw chase Walking x1.55 at 2.7
- mm7/mm7_m274.glb (source assets_source/worlds/mm7/models/mm7_m274.glb; biped; authored walk 1.86 run 1.86; projects: mm7_m274_claude, mm7_m274_reduce_claude)
    Mage A: standard chase Walking x1.98 at 3.68
    Mage A: maw chase Walking x1.98 at 3.68
    Mage B: standard chase Walking x2.18 at 4.05
    Mage B: maw chase Walking x2.18 at 4.05
    Mage C: standard chase Walking x2.38 at 4.42
    Mage C: maw chase Walking x2.38 at 4.42
- mm7/mm7_m426.glb (source assets_source/worlds/mm7/models/mm7_m426.glb; biped; authored walk 1.9 run 1.9; projects: mm7_m426_claude, mm7_m426_reduce_claude)
    Warlock A: standard chase Walking x1.93 at 3.67
    Warlock A: maw chase Walking x1.93 at 3.67
    Warlock B: standard chase Walking x2.12 at 4.04
    Warlock B: maw chase Walking x2.12 at 4.04
    Warlock C: standard chase Walking x2.32 at 4.4
    Warlock C: maw chase Walking x2.32 at 4.4
- mm7/mm7_m294.glb (source assets_source/worlds/mm7/models/mm7_m294.glb; biped; authored walk 1.79 run 1.79; projects: mm7_m294_claude, mm7_m294_reduce_claude)
    Necromancer A: standard chase Walking x1.86 at 3.33
    Necromancer A: maw chase Walking x1.86 at 3.33
    Necromancer B: standard chase Walking x2.04 at 3.67
    Necromancer B: maw chase Walking x2.04 at 3.67
    Necromancer C: standard chase Walking x2.24 at 4.0
    Necromancer C: maw chase Walking x2.24 at 4.0

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
