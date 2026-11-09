# Gait rollout package h02: MM6 BDwarf, BMinotaur, Jackalman, Werewolf (2026-10-31)

Package `h02` of the [gait rollout](../README.md): new in-place locomotion clips appended to four installed MM6
humanoids so every tier walks, runs and (new) sprints inside the gait window 0.75–1.5x under Standard and MAW.
Existing clips, meshes, skins and materials are byte-identical (`scripts/identity_check.py`: the input's binary chunk
is a prefix of the export's, every other JSON key equal). No Meshy or other spending; sources are local library loops.
`actors.yml` is not edited here: the bindings are in [`bindings.yml`](bindings.yml) for the coordinator. All four are
installed (`tools/install_model.py export/mm6_<m>.glb --world mm6 --name mm6_<m>.glb`); until the bindings are
applied the game plays the old clips.

| Model | New clip: source, length, binding stride, authored speed (model units/s) |
|---|---|
| BDwarf A/B/C (`mm6_dwa1`) | Walk2: humanoid set Armed-Walk (the dwarf's own walk family), 0.76 s, 1.0824, 1.42 · Run2: humanoid set Unarmed-Run-Forward, 0.64 s, 2.1061, 3.29 · Sprint: humanoid set Unarmed-Sprint, 0.53 s, 3.0936, 5.84 |
| BMinotaur A/B/C (`mm6_min1`) | Run2: Unarmed-Run-Forward, 0.70 s, 3.0383, 4.34 · Sprint: Unarmed-Sprint, 0.58 s, 3.7452, 6.46 (walk unchanged) |
| Jackalman A/B/C (`mm6_jak1`) | Walk2: Armed-Walk (its own walk's source), 0.82 s, 1.7152, 2.09 · Run: Unarmed-Run-Forward, 0.74 s, 3.2027, 4.33 · Sprint: Unarmed-Sprint, 0.62 s, 4.366, 7.04 |
| Werewolf A/B/C (`mm6_wwf`) | Walk2: Mixamo Mutant Walking (its own walk's source), 0.90 s, 1.7988, 2.00 · Run2: Unarmed-Run-Forward, 0.69 s, 2.8999, 4.20 · Sprint: Unarmed-Sprint, 0.63 s, 3.6521, 5.80 |

Strides are the gate's own trusted measurement (vertices and foot joints agree within the stride audit's tolerance).
The installed `Running` (and the Jackalman's walk-as-run binding) is no longer bound for locomotion but stays in the GLB.

## Why these clips

Targets from `gait_gate.py` (without `--candidate`): the Dwarf runs 3.15–3.41 and MAW-chases 6.8–7.5 u/s on a 0.56 m
leg, the Minotaur 4.5–5.0 / 6.9–8.4 on 0.80 m, the Jackalman 4.0–5.1 / 7.5–8.1 on 0.83 m and the Werewolf 4.1–4.8 /
6.2–6.6 on 0.72 m. Strides and cadences follow dynamic similarity with the accepted MM6 Ogre (same Froude number, so the
short Dwarf takes a quicker 0.53 s sprint for the Ogre's 0.62 s). Walks: BDwarf C's wandering already failed on the
installed Walking (x1.53, not in the ledger's list), the Jackalman's walk ran x1.55 on tier C, the Werewolf's slow
Mutant walk x1.71–2.00; each got a Walk2 with a longer stride at a normal cadence. The Minotaur's Walking fits.
The Minotaur is heavy: a shorter, quicker sprint stride (3.7 at 0.58 s rather than the Ogre-like 4.2) after the first
version drove its knees to the belly. The Werewolf's Mutant Run has a natural stride of 2.03 m against the 2.9 needed
(the legs overreached and the pelvis dropped 31 cm), so Run2 uses the humanoid run on the Werewolf's hunched mean
posture (`lean: 1`), like the Sprint.

## Phase

All new clips are aligned on the left foot's forward-most point of the model's `Walking` (`align`). The Dwarf's
installed Walking and Running are half a loop apart (left foot forward at 0.72 vs 0.25), like the Ogre's were; its new
clips follow the walk (0.72). Minotaur and Werewolf Walking/Running already agree (0.23–0.27). Jackalman: 0.75.

## Method

`scripts/compose_gait.py` is the sprint pilot's composer (`../../mm6_sprint_humanoids_claude/`), copied, with four
additions used here (all applied after the body is solved, with the pilot's per-arm clearance switched off):

- `swing_lift`: scales the ankle's height above flat (the Dwarf's scaled library walk shuffled: stance share 0.85).
- `arms_raise_deg`: both arms turned forward and up as one rigid unit about the line through both shoulders, so a
  two-handed grip is kept exactly. The Minotaur carries its axe across the body with both hands; the sprint's and the
  run's knee drive put the haft 30–35 mm into the left thigh. Run2 10°, Sprint 14°.
- `arm_out_deg`: an upper arm turned out about the travel axis. The Jackalman's free hand beside its long wrap
  (10–12°, staff arm 20° in the sprint), the Werewolf's hanging claws beside its thighs (Walk2 10°, Run2/Sprint 14°
  plus a 12° raise).
- `elbow_forward_deg`: a forearm bent toward +Z in the plane of the upper arm. The Jackalman has no run, so its run
  arms are its Walking's; the pilot's `elbow_flex_deg` (hinge measured from the forearm's swing, here mostly a twist)
  swung the hand across the wrap. Free arm 50° (Run) / 60° (Sprint); the staff arm 14° (Walk2), 32° (Run), 40°
  (Sprint) so the staff foot stays above the floor (it went 10 / 18 cm under it).

Other per-model choices (jobs in `jobs/`): planted feet by `lock_stance` on runs and sprints, the integral plant on the
walks (`plant_iterations: 12`), `stance_foot: Standing` with `foot_toe_out_deg: 5`; the Minotaur's spine rotation
weights 0.4–0.5 (less armpit stretch); the Jackalman's sprint lean at 55 % of the pilot's (its staff tilts with the trunk);
the Werewolf's Walk2 `bob: 0.1` (the Mutant walk's head bob was 14 % at 0.8).

The Werewolf (Meshy auto-rig: `Hips`, `Spine01`, `neck`, `LeftUpLeg` ...) is composed on a copy with B_* joint names
(`scripts/rename_rig.py to_b`) and renamed back (`from_b`); only node names change, the probes read the B_* copy.

## Gates (outputs in `review/`)

`gait_gate.py` PASSED for all four (`review/<m>_gait_gate.txt`; stride trusted, floor ok on every descriptor).
Window section:

```
BDwarf      standard A  wander: Walk2 x1.11  chase: Run2 x0.96      maw A  chase: Sprint x1.28
            standard B  wander: Walk2 x1.15  chase: Run2 x1.00      maw B  chase: Sprint x1.22
            standard C  wander: Walk2 x1.20  chase: Run2 x1.04      maw C  chase: Sprint x1.17
BMinotaur   standard A  wander: Walking x1.18  chase: Run2 x1.14    maw A  chase: Sprint x1.30
            standard B  wander: Walking x1.07  chase: Run2 x1.04    maw B  chase: Sprint x1.15
            standard C  wander: Walking x1.10  chase: Run2 x1.07    maw C  chase: Sprint x1.07
Jackalman   standard A  wander: Walk2 x0.96  chase: Run x0.93       maw A  chase: Sprint x1.07
            standard B  wander: Walk2 x1.05  chase: Run x1.02       maw B  chase: Sprint x1.09
            standard C  wander: Walk2 x1.23  chase: Run x1.18       maw C  chase: Sprint x1.14
Werewolf    standard A  wander: Walk2 x1.03  chase: Run2 x0.98      maw A  chase: Sprint x1.07
            standard B  wander: Walk2 x1.10  chase: Run2 x1.05      maw B  chase: Sprint x1.09
            standard C  wander: Walk2 x1.21  chase: Run2 x1.15      maw C  chase: Sprint x1.13
```

MAW's wander rows (hostile speed, not judged by the gate) play at up to x1.55–1.79 on Walk2/Walking for BMinotaur B/C,
Jackalman A and all Werewolves.

Probes (`review/<m>_probes.txt`, `scripts/gates.sh`):

- `check_winding.py`: 0 inverted closed parts on all four exports.
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R): every new clip +4.3..+5.5 / +4.5..+5.3, swing
  within -6..+15 (Werewolf and Jackalman Walk2 swing up to +24 / +15 on one side, the source walk's toe-off roll).
  The joint line matches the boot/foot axis on these rigs (plan views `review/before/feet_plan.png`). The accepted
  walks plant very differently: Dwarf Walking/Running +26 / +39 (Standing's duck feet), Minotaur +26 / +29,
  Werewolf +14 / +22, Jackalman +5 / +5.
- Head bob (bob_audit's measure): Dwarf Walk2 3.6 %, Run2 4.7 %, Sprint 6.6 %; Minotaur Run2 4.7 %, Sprint 5.9 %;
  Jackalman Walk2 2.8 %, Run 4.9 %, Sprint 6.0 %; Werewolf Walk2 4.3 %, Run2 4.2 %, Sprint 6.1 %.
- Arm and hand gate (contact_probe, 60 Hz; forearm/hand/prop inside legs+trunk): 0 % in every new clip except Dwarf
  Walk2 11 % / 39 mm, the same forearm-twist spot at the hip as the accepted Walking (14 % / 39 mm). Werewolf Walk2 0 %
  where the accepted Walking reads 46 % / 40 mm. Props: axe and staff 0 %. Wrist maxima equal the base clips'.
- Lowest skin: 0.0 cm on every new clip (the sprint included, which `gait_gate.py` does not floor-check). Staff foot
  (`review/jak1_staff_floor.txt`): Walk2 +2.5 cm, Run +3.9, Sprint +1.3 (accepted Walking -2.3).
- Planted stride per side at 1 cm (`stride_probe.py`): within 1 % of the binding except Dwarf Walk2 R 1.124 vs 1.080
  (+4 %, slow convergence of the integral plant).
- Playback in the browser (`tools/run_creature_review.py`, normal and half speed, looked at): viewers in
  `../../mm6_<m>_gait_h02_claude/` (the wrapper needs a direct child of `creatures/` per viewer), sheets
  `review/<m>_playback_sheet.png`, close shots `review/<m>_shots.png`, Blender filmstrips in `review/iter/`.

## Doubtful / left open

- **Minotaur thigh weights.** 127 LOD0 vertices between 1.1 and 1.3 m (belly and shoulders, above the 0.96 m hip)
  carry up to 61 % thigh weight. The new clips' larger thigh swing stretches arm-region edges to 3.0–3.3x (Running
  1.93x; >1.5x edges 13–23 vs 4–11). Not visible in the renders at game size; a rig fault of the model (Codex round 3),
  not fixable here without touching the skin.
- **Kilt helper bones.** The Minotaur's `Skirt_*` bones only translate (a procedural push, up to 6 cm) in the base
  clips; the new clips carry the phase-aligned Running values, so the push does not grow with the larger knee drive.
  The front panel lifts with the knee in Run2/Sprint; no tear seen.
- **Pilot composer's arm clearance (`clear_arms`)** turned the Dwarf's left arm 14–18° *inward* in Walk2 (contact rose
  from 37 to 40 mm, the hand moved 7–12 cm toward the body), and on the Minotaur turned the two hands of its two-handed
  axe by different angles (2° and 8°), which loosens the grip. It pushes along the target skin's normal, which is not
  outward on a tunic or kilt shell. Off for every clip here.
- Dwarf, Minotaur and Jackalman Sprint read `uneven` 0.46–0.65 in the bob measure (the pilot's Ogre 0.43), the
  humanoid-set sprint's own left/right asymmetry; the Dwarf's and Minotaur's sprints also re-touch a toe briefly
  after lift-off (phase probe: R lift 0.44 / land 0.46 on the Dwarf).
- The Jackalman's run arms are its walk's arms with more swing, a forward elbow and abduction (it had no run).
- Walk-to-run switches change the foot heading on the Dwarf and Minotaur (duck-footed accepted walks against the new
  5° clips).
- Not run: in-game captures and the headless actor regressions (bindings are not applied yet).

## Rebuild

`scripts/rebuild.sh [--sources] [m ...]` composes the exports from `work/mm6_<m>_pre_gait.glb` and `jobs/`, then runs
`scripts/gates.sh` (gate, winding, identity, probes). It reproduces the installed sources byte for byte.
`--sources` re-extracts the library loops with Blender into `work/sources/` (library-derived, never commit).
Pre-gait sources (rollback: install these), SHA-256:
`mm6_dwa1` ee7a232d…df07, `mm6_min1` 390cc039…ed82, `mm6_jak1` c2982ff3…f9bd, `mm6_wwf` b2ef1c43…d47dd9.
Viewers: `scripts/build_viewers.py <m>`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm6_<m>_gait_h02_claude playback`, `scripts/playback_sheet.py`, `scripts/shots_sheet.py`.
A far-LOD repair rerun (`../../lod_repair_claude/`) on these models must re-graft the new clips.
