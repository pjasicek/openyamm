You are package `h13` of the 2026-10-31 gait rollout in the OpenYAMM repository (/home/pjasicek/github/OpenYAMM).
Read `level_generation/creatures/gait_rollout_20261031/README.md` fully first: it is your brief (why, target gates,
methods for humanoids and multi-legged bodies, phase and feet rules, the user's standing decisions, install and the
`bindings.yml` hand-off). Also read the repository's AGENTS.md and CLAUDE.md. Your working directory is
`level_generation/creatures/gait_rollout_20261031/h13/` (create it). Three other package agents work at the same time
on other models: touch only your models, your package directory and your models' project READMEs; never edit
actors.yml, STATUS.md, shared tools, the pilot projects or engine code.

Your models (world/glb, body type from rig joint names — check it by eye, the ledger only guesses; authored speeds in
model units/s; then every tier problem the gate reports now: tier, ruleset + state, clip, playback rate, speed):
- mm7/mm7_m302.glb (source assets_source/worlds/mm7/models/mm7_m302.glb; biped; authored walk 1.18 run 1.18; projects: mm7_m302_claude, mm7_m302_reduce_claude)
    Peasant Dwarf MaleA A: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleA A: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleA B: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleA B: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleA C: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleA C: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleB A: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleB A: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleB B: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleB B: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleB C: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleB C: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleC A: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleC A: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleC B: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleC B: maw chase Walking x2.64 at 3.13
    Peasant Dwarf MaleC C: standard chase Walking x2.64 at 3.13
    Peasant Dwarf MaleC C: maw chase Walking x2.64 at 3.13
- mm7/mm7_m312.glb (source assets_source/worlds/mm7/models/mm7_m312.glb; biped; authored walk 2.0 run 2.0; projects: mm7_m312_claude, mm7_m312_reduce_claude)
    Peasant Dwarf FemaleA A: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleA A: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleA B: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleA B: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleA C: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleA C: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleB A: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleB A: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleB B: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleB B: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleB C: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleB C: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleC A: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleC A: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleC B: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleC B: maw chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleC C: standard chase Walking x1.91 at 3.82
    Peasant Dwarf FemaleC C: maw chase Walking x1.91 at 3.82
- mm7/mm7_m332.glb (source assets_source/worlds/mm7/models/mm7_m332.glb; biped; authored walk 1.7 run 1.7; projects: mm7_m332_claude, mm7_m332_reduce_claude)
    Peasant Elf MaleA A: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleA A: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleA B: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleA B: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleA C: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleA C: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleB A: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleB A: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleB B: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleB B: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleB C: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleB C: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleC A: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleC A: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleC B: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleC B: maw chase Walking x1.92 at 3.28
    Peasant Elf MaleC C: standard chase Walking x1.92 at 3.28
    Peasant Elf MaleC C: maw chase Walking x1.92 at 3.28
- mm7/mm7_m322.glb (source assets_source/worlds/mm7/models/mm7_m322.glb; biped; authored walk 1.78 run 1.78; projects: mm7_m322_claude, mm7_m322_reduce_claude)
    Peasant Elf FemaleA A: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleA A: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleA B: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleA B: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleA C: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleA C: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleB A: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleB A: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleB B: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleB B: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleB C: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleB C: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleC A: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleC A: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleC B: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleC B: maw chase Walking x1.81 at 3.21
    Peasant Elf FemaleC C: standard chase Walking x1.81 at 3.21
    Peasant Elf FemaleC C: maw chase Walking x1.81 at 3.21

Run `gait_gate.py` without --candidate on each model first for its targets. Work model by model and install each
model as soon as its gates pass (so a later blocker does not lose earlier work), appending to `bindings.yml` as you go.

Final report (concise): per model the clips added, the binding values, the gate's window section, the foot heading
numbers, and doubts; the path of bindings.yml; any model you could not finish and why; any problem found in shared
tools.
