# Gait rollout package h05: MM6 PeasantF3, PeasantF4, PeasantM4, Nobleman, Merchant (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to five installed MM6 humanoids
(`assets_source/worlds/mm6/models/`, commit `d285bdd`; pre-gait copies and rollback in `work/mm6_<m>_pre_gait.glb`).
Every existing clip, mesh, skin and material is unchanged (`identity_check.py`: the input's binary chunk is a
byte-identical prefix, only animations are appended). No Meshy credits or other spending; sources are local library
loops (`work/sources/*.npz`, copied from h04/h07, library-derived, never commit). All five are installed
(`tools/install_model.py --world mm6`); bindings for the coordinator are in [bindings.yml](bindings.yml).

| Model | New clips (source, length, bound stride, authored speed u/s) | Binding |
|---|---|---|
| PeasantM4 A-C `mm6_natm` (spear, buckler) | `Walk2` Mixamo Walk 0.82 s 1.80 (2.20) · `Jog` humanoid set Unarmed-Run-Forward 0.66 s 2.90 (4.39) · `Sprint` Unarmed-Sprint 0.56 s 4.11 (7.34) | walking Walk2, stride_length 1.8, run Jog, run_stride_length 2.9, sprint Sprint, sprint_stride_length 4.11 |
| Merchant A-C `mm6_mer1` (robe, club) | `Jog` humanoid set Relax-Run-Forward 0.72 s 1.88 (2.61) | run Jog, run_stride_length 1.88 |
| PeasantF3 A-C `mm6_mfp` (wrap skirt, knife) | `Walk2` Mixamo Walk 0.84 s 1.60 (1.90) · `Jog` Unarmed-Run-Forward 0.63 s 2.41 (3.83) · `Sprint` Unarmed-Sprint 0.56 s 3.41 (6.09) | walking Walk2, stride_length 1.6, run Jog, run_stride_length 2.41, sprint Sprint, sprint_stride_length 3.41 |
| PeasantF4 A-C `mm6_natf` (skirt, forearm blade, leaf shield) | `Walk2` Mixamo Walk 0.83 s 1.80 (2.17) · `Jog` Unarmed-Run-Forward 0.66 s 2.85 (4.32) · `Sprint` Unarmed-Sprint 0.56 s 4.11 (7.34) | walking Walk2, stride_length 1.8, run Jog, run_stride_length 2.85, sprint Sprint, sprint_stride_length 4.11 |
| Nobleman A-C `mm6_nobl` (cape, tabards, sword) | `Walk2` Mixamo Walk 0.82 s 1.75 (2.13) · `Jog` Unarmed-Run-Forward 0.66 s 2.80 (4.24) · `Sprint` Unarmed-Sprint 0.56 s 4.10 (7.32) | walking Walk2, stride_length 1.75, run Jog, run_stride_length 2.8, sprint Sprint, sprint_stride_length 4.1 |

Why: these five are not Wimps; they wander at Spd and chase at twice that (Standard 3.7-5.3 u/s, MAW 7.4-8.4 except
the Merchant, whose speed MAW leaves at 2.69). Their walks (0.75-1.69 u/s authored) and short runs (1.6-2.5) played at
x1.66-2.0 (capped, sliding). Wandering B/C tiers also outran the walks (x1.4-1.7), so the four MAW-affected bodies got
a `Walk2` as well as a `Jog` and a `Sprint`; the Merchant only a slow jog. The installed `Walking`/`Running` stay in
the GLBs (no longer bound for locomotion, except the Merchant's `Walking`). Strides bound are the planted strides
(`stride_probe.py`, both sides within 0.5 %); the gate's trusted measurements agree within 1 %.

## Gate window sections (`review/<m>_gait_gate.txt`; all PASSED, stride trusted, floor ok on every descriptor)

```
natm  standard PeasantM4 A/B/C  wander Walk2 x0.95/1.08/1.21   chase Jog x0.95/1.08/1.21
      maw      PeasantM4 A/B/C  wander Jog x0.89/0.92/0.95     chase Sprint x1.06/1.10/1.14
mer1  standard+maw Merchant A-C wander Walking x1.28           chase Jog x1.03
mfp   standard PeasantF3 A/B/C  wander Walk2 x0.98/1.07/1.17   chase Jog x0.97/1.07/1.17
      maw      PeasantF3 A/B/C  wander Jog x0.97/1.00/1.02     chase Sprint x1.22/1.25/1.28
natf  standard PeasantF4 A/B/C  wander Walk2 x0.94/1.07/1.20   chase Jog x0.94/1.07/1.20
      maw      PeasantF4 A/B/C  wander Jog x0.88/0.91/0.94     chase Sprint x1.04/1.07/1.11
nobl  standard Nobleman A/B/C   wander Walk2 x0.94/1.07/1.19   chase Jog x0.94/1.07/1.20
      maw      Nobleman A/B/C   wander Jog x0.88/0.91/0.94     chase Sprint x1.02/1.06/1.09
```

## Other gates (`review/<m>_probes.txt`)

- `check_winding.py`: 0 inverted closed parts on all five exports.
- Phase (left foot forward-most): every new clip follows its walk: natm 0.16-0.17 (Walking 0.17), mer1 0.71 (0.71),
  mfp 0.00 (0.00), natf 0.74-0.75 (0.75), nobl 0.75-0.76 (0.76). Installed runs half a loop from their walks:
  natf `Running` 0.29, nobl `Running` 0.24 (new clips follow the walks).
- Foot heading, toe-out from +Z, planted L / R (swing range): every Jog and Sprint +4.9..+5.2 (swing -6.2..+8.4);
  Walk2 +2.9..+4.7 (swing +0.3..+15.9, the Mixamo walk's own roll). Installed: natm Running +8.8 / +26.4, nobl Running
  +22.7 / +9.2 (swing to +92), natf/mfp clips a rigid +17..+21 (Standing's), mer1 +4.6 / +10.4.
- Head bob (bob_audit's measure; uneven 0.00-0.23 on every new clip): natm Walk2 4.7 %, Jog 4.7, Sprint 5.6; mer1
  Jog 4.6 (its Running 0.5 %, a glide); mfp Walk2 4.2, Jog 4.9, Sprint 5.0; natf Walk2 4.2, Jog 5.1, Sprint 6.2;
  nobl Walk2 4.2, Jog 4.7, Sprint 6.4.
- Lowest skin: every new clip within 0.02 cm of the floor (none below -1 cm, skirt hems included).
- Arm and hand gate (contact_probe, 60 Hz): no forearm, hand or prop inside legs or trunk in any new clip of natm,
  mfp, natf, nobl. The Merchant's hands rest on his belly and his club hangs against his robe as in his accepted
  clips (arms 100 % 39 mm, club 100 % 16 mm in Running and Jog alike). Arm skin stretch about the base clips' (natm
  Sprint L max 2.87 vs Running 2.74; nobl Sprint L 8.94 vs Running 7.82: the cape/shoulder edge that already
  stretches 7.6-8.3 in the accepted clips; mer1, mfp, natf at or below their bases).
- Playback: `python3 tools/run_creature_review.py --project level_generation/creatures/mm6_<m>_gait_h05_claude
  check|playback` (viewers from `scripts/build_viewers.py`; all switches, no console errors), looked at; half-speed
  sheets `review/<m>_playback_sheet.png`, Blender filmstrips in `review/iter/` (`*_final_*`, `natm_a_*`, `mer1_d_Jog`).
- Actor regressions on the installed GLBs with the current (old) bindings, `scripts/regressions.sh`, all pass
  (`review/regression_*.log`): `mm6_peasant_m4_actor_model_tiers_share_the_native_height`,
  `mm6_merchant_actor_model_tiers_share_the_native_height`, `mm6_peasant_f3_actor_model_tiers_share_the_native_height`,
  `mm6_peasant_f4_actor_model_tiers_share_the_native_height`, `mm6_swordsman_actor_model_tiers_share_one_size`.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

h04's composer (h02 lineage: `elbow_forward_deg`, `arm_out_deg`, `skirt_follow`, `skirt_clear`, `prop_floor`) with
h01's `even_bob`, h16's `symmetric_drop`, h01's `swing_height` and h19's `track_out` ported in, and these additions:

- `thigh_swing` (natf): her skirt is skinned to swing-only thigh helpers (`B_<s>_ThighSwing`, the thigh rotation
  without its twist, as `../../mm6_natf_anim_claude/scripts/skirt_skin.py` bakes it); they are recomputed from the new
  thighs (verified exact on her accepted Walking/Standing).
- `ring_skirt` (mfp, `scripts/ring_skirt.py`): her wrap skirt is a five-ring cage of 60 pelvis-child points fitted to
  the legs (`../../mm6_mfp_codex/scripts/final_skirt.py`); ported to numpy (mean 1 cm from the accepted cage before its
  push-out) with a push-out (skirt vertices inside a leg move out along its normal), `hang` (a ring rises at most 5 cm
  above its pelvis-carried place: the sprint's high knees bagged the hem), `posed_band` (rings 1-2 hold the thigh and
  knee skin at their posed height), `knee_out` (knee skin in front of the cloth pushes it out) and `floor` (hem above
  1 cm). Skirt probe (legs through the cloth): Walk2 43 % max 15 mm, Jog 82 % 31 mm, Sprint 79 % 34 mm against the
  accepted Walking 68 % 26 mm and Running 82 % 23 mm.
- `cape_lift` (nobl): the cape's 18 chain roots turned back 6 deg (Jog) / 15 deg (Sprint) so it streams behind; with
  `skirt_clear` on prefix `Cloak_` (h05: an optional boot capsule, chains ordered round the shoulders m88..p88) the
  cape leaves the leg and boot capsules (Sprint 33 mm before, 0 after; Walk2 43 -> 11 mm). Front tabards follow the
  thighs (`skirt_follow` on `Tabard_`, gain 0.9).
- Arms: natm/natf walks and natf's sprint run without arm clearance and with 8-10 deg abduction (`arm_out_deg`): the
  clearance chased the skirt/loincloth skin and made contacts deeper (as h02 found). Nobleman Jog/Sprint and natm
  Sprint use `swing_height` 0.75-0.8 (the sword met the high left knee; the spear butt met the kicked heel).
- Mixamo runs (Running (2), Fast Run, Slow Jog) were rejected: with `lock_stance` their long contacts (0.4-0.75 of the
  loop) forced the hips 15-20 cm down; the humanoid set's runs (contacts 0.2-0.25) keep the hips at 0.80-0.85 m.
- Merchant: a short, low shuffle (`swing_height` 0.45, `track_out` 3.5 cm, `width` 0.5) like his accepted Running's
  wide track and 11 cm foot lift, so his boots stay under the robe (`skirt_clear` on his robe turned chains 130 deg and
  was dropped).

## Doubts

- mfp: in a few sprint/jog frames a small patch of knee still shows through the front panel near the wrap's slit
  (1-2 of 16 front samples, about a centimetre at game scale); the skirt widens visibly in the run (the cage holds the
  legs) and the legs come out of the slit, as in her accepted Running.
- mer1: the swing foot grazes the floor briefly mid-stance (phase probe: R lifts 0.44, lands 0.49), a heel-toe blip of
  the low shuffle; his hands and club keep their accepted contacts with the belly/robe.
- nobl: the cape flies 15 deg higher in the sprint than in the accepted Running; the sword still sweeps across the body
  as in his `Running`. The Walk2 carries the sword low behind as his accepted `Walking` does.
- natf: the large leaf shield passes beside the trailing leg in the sprint (no contact, but close in side view).
- Walk2 stance shares are 0.47-0.54 (Mixamo Walk), shorter double support than the accepted walks.
- Not run: in-game captures (bindings not applied yet). After `apply_bindings.py`, rerun `scripts/regressions.sh`.

## Rebuild

`scripts/rebuild.sh [model ...]` composes every export from `work/mm6_<m>_pre_gait.glb`, `jobs/` and
`work/sources/`, then runs `scripts/gates.sh` (gait gate with the bindings, winding, identity, probes); it reproduces
the installed exports byte for byte. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h05/export/mm6_<m>.glb --world mm6 --name mm6_<m>.glb`. Rollback:
install `work/mm6_<m>_pre_gait.glb` the same way and drop the bindings. Probes: `scripts/skirt_probe.py`,
`scripts/cloak_poke_probe.py` (counts leg skin not covered from behind, so a lifted cape reads worse; not a
penetration measure), `scripts/contact_probe.py`, `scripts/where_contact.py`; filmstrips `PROPS=... scripts/render_review.sh`
(views side, front, back, rquarter); viewers `scripts/build_viewers.py <m>`, `scripts/playback_sheet.py`. A far-LOD repair
or head-bob rerun of these models must re-graft these clips (copy the new source over the pre-gait copy and rebuild).
