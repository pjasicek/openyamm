You are package `h19` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h19/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_m440.glb (source assets_source/worlds/mm8/models/mm8_m440.glb; biped; authored walk 1.38 run 2.05; projects: mm8_m440_claude, mm8_m440_reduce_claude, mm8_m440_reduce_codex)
    Ogre Warrior A: standard chase Running x1.77 at 3.63
    Ogre Warrior A: maw chase Running x2.78 at 5.7
    Ogre Warrior B: standard chase Running x1.90 at 3.89
    Ogre Warrior B: maw chase Running x2.86 at 5.83
    Ogre Warrior C: standard chase Running x1.96 at 4.02
    Ogre Warrior C: maw chase Running x2.88 at 5.9
- mm8/mm8_m540.glb (source assets_source/worlds/mm8/models/mm8_m540.glb; biped; authored walk 1.99 run 1.99; projects: mm8_m540_claude, mm8_m540_reduce_claude)
    Ogre Mage A: standard wander Walking x0.66 at 1.32
    Ogre Mage A: maw chase Walking x2.64 at 5.27
    Ogre Mage B: standard wander Walking x0.73 at 1.45
    Ogre Mage B: maw chase Running x1.72 at 5.4
    Ogre Mage C: maw chase Running x1.76 at 5.54
- mm8/mm8_m520.glb (source assets_source/worlds/mm8/models/mm8_m520.glb; biped; authored walk 2.2 run 1.58; projects: mm8_m520_claude, mm8_m520_reduce_claude)
    Cyclops A: standard chase Walking x1.92 at 4.24
    Cyclops A: maw chase Walking x3.10 at 6.82
    Cyclops B: standard chase Walking x1.99 at 4.39
    Cyclops B: maw chase Walking x3.14 at 6.9
    Cyclops C: standard chase Walking x2.14 at 4.71
    Cyclops C: maw chase Walking x3.20 at 7.06
- mm8/mm8_m436.glb (source assets_source/worlds/mm8/models/mm8_m436.glb; biped; authored walk 1.41 run 1.41; projects: mm8_m436_claude, mm8_m436_reduce_claude)
    Ogre Pesant Male A: standard wander Walking x0.74 at 1.05
    Ogre Pesant Male B: standard wander Walking x0.74 at 1.05
    Ogre Pesant Male C: standard wander Walking x0.74 at 1.05

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
