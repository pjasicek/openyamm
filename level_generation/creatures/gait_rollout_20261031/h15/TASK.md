You are package `h15` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h15/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_7m452.glb (source assets_source/worlds/mm7/models/mm7_7m452.glb; biped; authored walk 1.68 run 1.68; projects: mm7_7m452_claude, mm7_7m452_reduce_claude)
    Peasant Goblin Male A A: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male A A: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male A B: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male A B: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male A C: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male A C: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male B A: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male B A: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male B B: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male B B: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male B C: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male B C: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male C A: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male C A: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male C B: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male C B: maw chase Walking x1.55 at 2.6
    Peasant Goblin Male C C: standard chase Walking x1.55 at 2.6
    Peasant Goblin Male C C: maw chase Walking x1.55 at 2.6
- mm7/mm7_m442.glb (source assets_source/worlds/mm7/models/mm7_m442.glb; biped; authored walk 1.35 run 1.35; projects: mm7_m442_claude, mm7_m442_reduce_claude)
    Peasant Goblin female A A: standard chase Walking x1.75 at 2.36
    Peasant Goblin female A A: maw chase Walking x1.75 at 2.36
    Peasant Goblin female A B: standard chase Walking x1.75 at 2.36
    Peasant Goblin female A B: maw chase Walking x1.75 at 2.36
    Peasant Goblin female A C: standard chase Walking x1.75 at 2.36
    Peasant Goblin female A C: maw chase Walking x1.75 at 2.36
    Peasant Goblin female B A: standard chase Walking x1.75 at 2.36
    Peasant Goblin female B A: maw chase Walking x1.75 at 2.36
    Peasant Goblin female B B: standard chase Walking x1.75 at 2.36
    Peasant Goblin female B B: maw chase Walking x1.75 at 2.36
    Peasant Goblin female B C: standard chase Walking x1.75 at 2.36
    Peasant Goblin female B C: maw chase Walking x1.75 at 2.36
    Peasant Goblin female C A: standard chase Walking x1.75 at 2.36
    Peasant Goblin female C A: maw chase Walking x1.75 at 2.36
    Peasant Goblin female C B: standard chase Walking x1.75 at 2.36
    Peasant Goblin female C B: maw chase Walking x1.75 at 2.36
    Peasant Goblin female C C: standard chase Walking x1.75 at 2.36
    Peasant Goblin female C C: maw chase Walking x1.75 at 2.36
- mm7/mm8_m504.glb (source assets_source/worlds/mm8/models/mm8_m504.glb; biped; authored walk 1.84 run 1.84; projects: mm8_m504_claude)
    Elemental Earth A: standard chase Walking x2.76 at 5.07
    Elemental Earth A: maw chase Walking x2.76 at 5.07
    Elemental Earth B: standard chase Walking x2.26 at 4.15
    Elemental Earth B: maw chase Walking x2.26 at 4.15
    Elemental Earth C: standard chase Walking x1.96 at 3.6
    Elemental Earth C: maw chase Walking x1.96 at 3.6
- mm7/mm8_m612.glb (source assets_source/worlds/mm8/models/mm8_m612.glb; biped; authored walk 2.29 run 2.29; projects: mm7_m250_claude, mm8_m612_claude, mm8_m612_reduce_claude)
    AGog A: standard chase Walking x2.08 at 4.77
    AGog A: maw chase Walking x2.08 at 4.77
    AGog B: standard chase Walking x2.26 at 5.16
    AGog B: maw chase Walking x2.26 at 5.16
    AGog C: standard wander Walking x0.62 at 1.43
- mm8/mm8_m612.glb (source assets_source/worlds/mm8/models/mm8_m612.glb; biped; authored walk 2.29 run 2.29; projects: mm7_m250_claude, mm8_m612_claude, mm8_m612_reduce_claude)
    Gog A: standard chase Walking x2.70 at 6.16
    Gog A: maw chase Walking x2.70 at 6.16
    Gog B: standard chase Walking x2.42 at 5.52
    Gog B: maw chase Walking x2.42 at 5.52
    Gog C: standard chase Walking x2.02 at 4.65
    Gog C: maw chase Walking x2.02 at 4.65
- mm8/mm8_m504.glb (source assets_source/worlds/mm8/models/mm8_m504.glb; biped; authored walk 1.84 run 1.84; projects: mm8_m504_claude)
    Earth Elemental A: standard wander Walking x0.41 at 0.76
    Earth Elemental B: standard wander Walking x0.49 at 0.9
    Earth Elemental C: standard chase Walking x1.51 at 2.77
    Earth Elemental C: maw chase Walking x3.02 at 5.53

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
