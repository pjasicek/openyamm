# MM6 Cleric (`cle`, Cleric A/B/C: Acolyte / Cleric / Priest of Baa) reduction (2026-10-14)

User: "3D tris count reduction playbook - do mm6_cle". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_cle.glb` (9,869 body tris, one merged body + head atlas material, three variants, four
influences; project `../mm6_cle_claude/`). Scripts copied from `../mm6_fgt_reduce_claude/` (per-region budgets),
with the piece-aware weights of `../mm6_djn_reduce_claude/`. No Meshy credits. Limits for the 1.578 m height:
p99 4.73 mm, max 23.7 mm. The staff attachment (`mm6_cle_staff.glb`, 552) is left as installed.

## Regions (`scripts/cle_regions.py`, `review/regions.png`)

Connected pieces and dominant bones: face skin with neck (1,513), hair (1,256), left fist (744), right fist (815),
cloak chains (1,701), belt tie (124), rest: tunic, sleeves, legs, mantle and collar (3,716).
`scripts/trim_faces.py` adds every cloak/mantle face that samples the region mask's G channel (the chest ankh and the
mantle and hem piping, 416 faces): the ankh bent at r72 and broke at r60 in the first ladder.

## Ladder rounds

| round | config | pick / result |
|---|---|---|
| g1 | face kept, tie kept, hair 60 %, fists 50 % | ankh distorted (`review/ladder_sheet.png`) |
| g2 | + trim faces kept | fine; p99 driven by tunic and cloak (`scripts/region_error.py`), hair/fists <= 2 mm |
| g3 | hair 50 %, fists 40 % | r66 (6,513) p99 4.58; dark notch at the back of the collar (r62 larger) |
| g4 | + whole collar kept (459) | worse: the cut moved onto the cloak, p99 5.6 at r66, new drift |
| g5 | g3 + one drift-lock round (`drift_lock.py`, min area 1 cm2) | notch gone; Walking cloak crossings up to 10 mm |
| **g6** | **g5 + source faces within 4.5 cm of the four new crossing spots kept** | **r68: 6,709, p99 4.48, no drift > 40** |

The max error (65-70 mm at Death:15 for every ratio) is a source defect: hip vertex 465 is weighted to RightArm /
RightForeArm / Hips / RightUpLeg and stretches into a spike in Death (edges 23-33 mm at rest, 68-113 mm posed); the
reduction removes it. Pass is judged on p99 and the close renders.

## Checks on g6r68

- **Cloak shells** (`scripts/shell_cross_cand.py`, the project's `shell_cross.py` on the ladder blend; side labels
  exported from `rig_v4.blend` by `scripts/cloak_side_labels.py`, candidate faces labelled by the source face under
  them): Walking 4 frames, 1 vertex, 4.2 mm; Hit 5 frames, 4.7 mm; Death 17.1 mm; all equal to the installed model.
- **Staff grip** (`scripts/grip_gate_posed.py`, staff at the posed `Staff` joint, every 2nd frame of seven clips):
  the fist closes up to 5.4 mm into the staff (installed 5.6 mm, by design); penetrating / contact vertices per frame
  27 / 77 against 72 / 183, in line with the fist's vertex count.
- **Texture drift** (`texture_drift.py`): no face above 40, p99 15.8.
- Renders: `review/close/sheet_g6r68.png` (whole front/back, face, collar back, chest, left fist; installed vs pick),
  `review/close/sheet_g5_head.png` and `sheet_g5_whole.png` (earlier rounds).
- Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_cle_reduce_claude/review/viewer/> (installed vs pick per
  tier); `check_viewer.mjs` 54 switches, no console errors (`review/viewer_check.json`).

## Round 1 result (superseded by round 2)

`export/mm6_cle.glb` (= `mm6_cle_g6r68.glb`): LODs 6,709 / 3,353 / 1,206 / 402 (installed 9,869 / 4,995 / 1,802 /
593), shadow LODs rebuilt and tucked (`../mm6_cle_claude/scripts/shrink_shadow_lods.py`), variants carried to every
primitive. LOD0 with the staff 10,421 -> 7,261 (-30 %).
Build: `scripts/build_pick.sh r68 g6` (export_cand -> swap_lod0 -> build_actor_lods -> shrink_shadow_lods ->
carry_variants -> viewer variants -> close renders). Ladder: `REA_PROTECT_FACES=work/prot_face.npy
REA_KEEP_FACES=work/keep_g6.npy REA_GROUPS=work/groups1.npy REA_GROUP_RATIOS=2:0.5,3:0.4 scripts/run_ladder.sh g6 0.70,0.68,0.66`.

Install after review: `tools/install_model.py level_generation/creatures/mm6_cle_reduce_claude/export/mm6_cle.glb
--world mm6`, then the `actors` suite (`mm6_cleric_actor_model_tiers_share_the_native_height`,
`mm6_cleric_actor_spell_charge_glows_at_staff_head`, `mm6_cleric_actor_air_attack_lights_the_staff_head`) and the
ledger. Rollback source: `work/mm6_cle_source_pre_reduce.glb` (and `work/mm6_cle_staff_source_pre_reduce.glb`).

## Round 2 (2026-10-14): new hands and library clips, reduced again

User on round 1: "I want the hands re-done - both look plain bad ... and then some best fitting library animations
for the cast and attack (he has the staff and one hand free)." The hands and clips are built in the creature's own
chain (`../mm6_cle_claude/README.md`, "User review 2026-10-14"); this project reduces its export
(`../mm6_cle_claude/export/mm6_cle.glb`: body 10,453 = 9,869 - 1,404 old hand faces + 2 x 994 MPFB hands).

- Clip previews and choice: `anim/retarget_cle.py` + `anim/render_cands.py` (`review/cands_*.png`, `review/lib_*.png`;
  the set's own mannequin previews `review/clips_front_*.png`). Final: `review/lib_final.png`.
- Same per-region route as round 1 (`work/keep_g8.npy`: the round-1 kept faces mapped by centroid, plus two cloak
  spots of the new Attack), hands as their own group at 60 %, hair 50 %, face kept: **h4r70, 7,315 tris**
  (p99 4.63 mm; max 26.8 mm in Running, after the master's weight-spike repair removed the 95 mm hip spike), no
  texture drift; cloak shells: none in Attack, Cast, Hit; Walking and Death as the unreduced build.
- `export/mm6_cle.glb` (= `mm6_cle_h4r70.glb`): LODs 7,315 / 3,656 / 1,316 / 437; staff `../mm6_cle_claude/export/
  mm6_cle_staff.glb` (552). With the staff 7,867 against the installed 10,421 (-25 %).
- Viewer (installed vs new per tier, each staff attached at its joint): <http://127.0.0.1:8901/level_generation/
  creatures/mm6_cle_reduce_claude/review/viewer/>; `check_viewer.mjs` 54 switches, no console errors.
- Install after review: see the creature README (install_model for body and staff, actors.yml events 0.54 s and
  `Socket_Palm_R`, regressions, ledger). Rollback: `work/mm6_cle_source_pre_reduce.glb`,
  `work/mm6_cle_staff_source_pre_reduce.glb`.

## Round 3 (2026-10-14): leg twist, exposed tunic, library Death

User on round 2: the Cast twists the right knee and ankle (frames 7-25), the stance looks knock-kneed, the Attack
exposes untextured tunic, and the Death should come from the library. Fixed in the creature's chain
(`../mm6_cle_claude/README.md`, "User review 2026-10-14 (2)"); the same reduction (h4r70) rebuilt on its new export
(`SRC=... scripts/build_pick.sh r70 h4`): LODs 7,315 / 3,656 / 1,316 / 437, Death 1.75 s.

- Surface error against the unreduced export, both directions, every 2nd frame (`review/round3/`, measured with a
  posed GLB pair): p99 / max mm Standing 3.7 / 12.8, Walking 4.5 / 22.2, Running 5.0 / 26.8, Attack 4.5 / 24.7,
  Cast 4.2 / 23.7, Hit 4.0 / 24.1, Fidget 3.7 / 12.5, Death 4.9 / 31.7 (mid-dive), Dead 5.5 / 15.6. The corpse's
  errors are scattered folds pressed together (thighs, spine, arms); source and reduced corpses render the same.
- Death candidates: `review/deaths_s1.png`, `deaths_s2.png` (12 side-on), `deaths_f.png` (four forward falls).
- Viewer shots: `review/round3/` (`sheet3.png`: Attack, Cast frame 7, Standing, Death, corpse).
- Viewer (installed vs new, staff attached): `check_viewer.mjs` 54 switches, no console errors.

## Round 4 (2026-10-14): robe shards

The creature's chain fixes the robe (`../mm6_cle_claude/README.md`, "User review 2026-10-14 (3)"). The candidate gets the
same treatment in `scripts/skirt_shell_cand.py` (run by `build_pick.sh` before `export_cand.py`): each candidate face
takes the label of the master surface under it (nearest triangle with agreeing normal, else a ray along its normal;
nearest face centres mislabelled a third of the reduced panel), the lining faces are replaced by the exact inner copy
of the outside. h4r70 is now **7,361 tris** (LODs 7,361 / 3,679 / 1,323 / 441; the inside copy 200 faces, the removed
lining 154). Viewer frames: `review/round4/sheet.png` (Walking 4-22, Standing, Attack 6-15, Cast).

## Floor fix — 2026-10-21

`--lift-joints Death Dead --lift-only 'Cloak*'` (the legs inside the cloak keep their dip during the fall). Before, in world units at tier A: corpse at -3.7; dying sinks to -14.4.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_cle.glb`), written to `export/mm6_cle_floor.glb` and installed as `mm6_cle.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.


## Gait rollout — 2026-10-31

Package [h03](../gait_rollout_20261031/h03/README.md) appended `Jog` to the installed `mm6_cle.glb` for the chase
(Cleric A-C: Standard and MAW chase at a run pace, Froude above 0.65, which played `Walking` at x2.12-2.66): humanoid set Unarmed-Run-Forward legs, arms and staff from `Walking`, the 13 cloak chains re-simulated (numpy port of `../mm6_cle_claude/scripts/cloak_sim.py`);
0.64 s, bound stride 2.1277 (3.28 u/s); phase-aligned to `Walking`, planted feet at 5 deg toe-out. Bound as `run` (the coordinator applies
`h03/bindings.yml`); `Walking` stays the wander clip. Every existing clip, mesh, skin and material is byte-identical.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h03/scripts/rebuild.sh cle` (from the pre-gait copy
`h03/work/mm6_cle_pre_gait.glb`). A far-LOD repair, floor-fix or any re-export of this model must re-graft `Jog`
(copy the new source over the pre-gait copy and rerun the rebuild, or graft it with `claude_shared/graft_clips.py`).
