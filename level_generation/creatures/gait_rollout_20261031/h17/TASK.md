You are package `h17` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h17/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm8/mm8_m412.glb (source assets_source/worlds/mm8/models/mm8_m412.glb; biped; authored walk 1.43 run 1.71; projects: mm8_m412_claude, mm8_m412_reduce_claude)
    Pirate Warrior Male A: standard chase Walking x1.84 at 3.15
    Pirate Warrior Male A: maw chase Walking x3.44 at 5.86
    Pirate Warrior Male B: maw chase Jog x2.14 at 6.08
    Pirate Warrior Male C: maw chase Jog x2.22 at 6.29
    Wimpy Pirate Warrior Male A: maw chase Walking x3.16 at 5.39
    Wimpy Pirate Warrior Male B: maw chase Walking x3.24 at 5.53
    Wimpy Pirate Warrior Male C: standard chase Walking x1.63 at 2.79
    Wimpy Pirate Warrior Male C: maw chase Walking x3.32 at 5.68
- mm8/mm8_m656.glb (source assets_source/worlds/mm8/models/mm8_m656.glb; biped; authored walk 1.78 run 5.27; projects: mm8_m656_claude, mm8_m656_reduce_claude)
    Human Mercenary C: maw chase Running x1.52 at 8.02
- mm8/mm8_m420.glb (source assets_source/worlds/mm8/models/mm8_m420.glb; biped; authored walk 0.78 run 0.78; projects: mm8_m420_claude, mm8_m420_reduce_claude)
    Pirate Mage Male A: standard wander Walk2 x0.64 at 0.5
    Pirate Mage Male B: standard chase Walk2 x1.72 at 1.34
    Pirate Mage Male B: maw chase Walk2 x1.72 at 1.34
    Wimpy Pirate Mage Male C: standard wander Walk2 x1.61 at 1.26
- mm8/mm8_m416.glb (source assets_source/worlds/mm8/models/mm8_m416.glb; biped; authored walk 1.08 run 2.21; projects: mm8_m416_claude, mm8_m416_reduce_claude)
    Pirate Crossbowman (Female) A: maw chase Walking x2.70 at 5.99
    Pirate Crossbowman (Female) B: maw chase Walking x2.74 at 6.07
    Pirate Crossbowman (Female) C: maw chase Walking x2.78 at 6.15
    Wimpy Pirate Crossbowman (Female) A: standard chase Walk2 x1.61 at 1.73
    Wimpy Pirate Crossbowman (Female) A: maw chase Walk2 x1.61 at 1.73
    Wimpy Pirate Crossbowman (Female) C: maw chase Walking x2.70 at 5.99
- mm8/mm8_m620.glb (source assets_source/worlds/mm8/models/mm8_m620.glb; biped; authored walk 1.64 run 1.64; projects: mm8_m620_claude, mm8_m620_reduce_claude)
    Bedraggled Human (peasant) A: standard wander Walking x0.67 at 1.1
    Bedraggled Human (peasant) B: standard wander Walking x0.67 at 1.1
    Bedraggled Human (peasant) C: standard wander Walking x0.67 at 1.1

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
