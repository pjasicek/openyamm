# MM6 Lizard Archer (`lzd`, LizardArch A/B/C) reduction (2026-10-14)

User: "3D tris count reduction playbook - do mm6__lzd". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)).
Scripts copied from `../mm6_fgt_reduce_claude/`. No Meshy credits.

**Source: the accepted Codex round 6 export** (`../mm6_lzd_codex/export/mm6_lzd.glb` and `mm6_lzd_bow.glb`, accepted
2026-10-13), copied to `work/*_source_pre_reduce.glb`. The game runs these: the `assets_dev` runtime copies are
byte-identical to them. `assets_source/worlds/mm6/models/mm6_lzd*.glb` is still the older Oct 12 export: round 6
was copied into `assets_dev` without updating the source. The first pass of this project reduced that stale source
by mistake (user caught it). Its outputs are kept in `work/candidates/old_source/` and are not to be installed.

Round 6 model: 9,854 tris (body+head atlas material `Lizard_A` 9,634, skinned bowstring/arrow `LizardBow_A` 220;
three variants, eight influences, 66 joints), bow 1,788. Limits for the 1.699 m height: p99 5.1 mm, max 25.5 mm.

## Body: per-region budgets

The mesh is 63 connected pieces. `scripts/regions.py` labels them (`work/comp.npy`): head+neck 2,099,
legs/tail 1,470, arms 1,162 / 1,110, tunic 850, quiver, bracers, belt, pauldrons and small pieces (arrow shafts in the
quiver, buckles, rings). Kept exactly (`work/keep_a.npy`, 1,330 faces): the `LizardBow_A` faces (string and nocked
arrow, 208 after the weld) and every piece of up to 80 faces. Groups (`work/groups_b.npy`): 1 head+neck piece,
2 hands and fingers, 3 tunic; label 0 takes the rest of the ladder budget.

Configurations explored on the stale source (same piece structure). A uniform cut failed (p99 5.3 mm at r70: tunic,
legs and quiver lose depth). Head 65 % / hands 50 % / tunic 80 % passed at r75. Head 55 % / hands 45 % /
tunic 75 % ("d") passed at r70. Head 45 % / hands 40 % thinned the fingers.

On round 6, config d:

| config | r72 | r70 | r68 | finding |
|---|---|---|---|---|
| d6: d | 7,084, 3.84 / 30.1 | 6,886, 4.23 / 30.1 | 6,690, 4.63 / 30.8 | max at one crease of the tail root while lying (Death 36) |
| d7: + faces within 4 cm of the six source vertices over 18 mm there (`scripts/error_lock.py`) | 7,084, 3.83 / 25.7 | | 6,690, 4.73 / 25.7 | max at the back of the neck (Attack 6) |
| **d8: + same lock there (three vertices; 1,418 faces kept)** | 7,086, 3.92 / 15.1 | 6,888, 4.26 / 16.6 | **6,692, 4.75 / 20.7, IoU 0.992, SSIM 0.988** | **all pass; pick r68** |

Face, teeth, brow crest, claws and fingers match the installed model (`review/faces/s2.png`, `s2_clay.png`; rows
installed, d8r70, d8r68). Texture drift (`texture_drift.py r68`): no face above 40, p99 12.2; no lock round.

## Bow

Parts: grip wrap 772, limbs 608, riser 92, two nocks 86 and four nock rings 36. `scripts/bow_parts.py` decimates
each part on its own. Limbs below 50 % kink, and 45° hard normals facet them (stale-source tests).
Round 6 fitted the left hand tightly to the wrap: the source has no hand vertex inside the bow in any frame
(`scripts/grip_gate_bow.py`, bow at the posed `Bow` joint, every 2nd frame of every clip). Any cut of the wrap breaks
that:

| bow | tris | hand vertices inside (Standing) | deepest |
|---|---:|---:|---:|
| source | 1,788 | 0 | 0 |
| b4: wrap 40 % | 894 | 182 / 25 frames | 7.0 mm |
| b5: wrap 70 % | 1,126 | 124 | 4.5 mm |
| **b6: wrap kept, limbs 50 %, riser 60 %, nocks 50 %, rings kept** | **1,358** | **0** | **0** |

The reduced body with the source bow is also clean (0), so the cause is the wrap, not the hand.
Pick b6: LODs 1,358 / 964 / 388 / 110 (source LODs kept). `scripts/prop_swap_glb.py` also rebuilds and keeps shadow
LODs when a prop has them; round 6's bow has none. Renders: `review/props/bow_compare.png` (installed, b6),
`review/props/grip_sheet.png` (rows installed, reduced; Standing and Attack).

## Shared gate (round 6 bow-hold gate) and the final build

The installed model passes the shared Codex gate runner (`../claude_shared/gates/run_gates.sh`, configs
`work/gates_*.json`, flap vertex lists per LOD from `scripts/flap_regions.py`; 7,416 PASS). The d8r68 pick did not
(`review/gates_nofix`): LOD0 left-foot yaw 10.2-10.5 deg (installed 5.1; the 5 mm sole band and its heel/toe patches
were decimated), a left-wrist edge stretched 5.0x in Hit (installed 2.2), and LOD1-3 from `tools/build_actor_lods.py`
broke the fitted grips (gaps over 3 mm), soles, running contact and the loin flap.

- **d9** (`scripts/lock_d9.py`, `work/keep_d9.npy`, 1,888 faces kept): d8 plus every face with a vertex below
  6 cm (soles, toes, claws) and faces within 4 cm of the stretched wrist edge. r68 missed p99 (5.17 mm); **r70:
  6,888, p99 4.51 / max 20.7 mm, IoU 0.994, SSIM 0.989**.
- **LOD1-3 from the Codex LODs** (`scripts/codex_lods.py`): each accepted Codex level trimmed to a body target
  (3,600 / 1,650 / 650; string primitive kept) with hands, fingers, loin flap and soles locked, spliced into the
  reduced LOD0 file, shadow LODs rebuilt. Totals 3,707 / 1,671 / 683 (shared limits 55 / 25 / 10 % of LOD0).
  An unlocked flap went dark and crumpled at LOD2 (`review/lods/zoom.png`); locked, it matches (`zoom2.png`).
  Silhouette IoU against the installed level at its runtime size: 0.994-1.000 (`review/lods/lod_sheet.png`).
- **Bow LOD1 b6m**: the LOD1 wrap at 35 % left the index finger 3.7 mm off; wrap 50 %, limbs 20 %, rings and nocks
  35-50 % (`work/bow_lod0_l1b.glb`) passes. Bow LODs 1,358 / 664 / 304 / 110.
- Shared gate on the final pair (`review/gates_d9m`): **PASS, 7,416 checks, no FAIL** (same count as installed).

## Bow hand (not changed)

User: the left (bow) hand is turned outward. Confirmed: in the idle the left palm faces out with the thumb back.
`scripts/mirror_left_arm.py` (left arm takes the mirrored right arm, half-cycle shift in locomotion, 8 deg
abduction) fixes Standing/Fidget/Walking/Running/Hit and passes their gates (`review/gates_mirror_src`,
`review/pose/mirror_sheet.png`). Its blends into Attack/Cast/Death fail (bow 7 cm into the pelvis, elbow plane
27 deg), because round 6 authors the whole bow hold 180 deg rolled: in the draw the left palm faces the archer and
the bow mount compensates. A proper fix reworks the hand in the draw, the bow mount, grip, string/arrow alignment
and the blends; that is a separate animation round. The user left the call to Claude: the reduction was installed
with the original round 6 hand. Candidates: `work/candidates/mirror/`, `work/candidates/twist200/`.

## Installed 2026-10-14

`export/mm6_lzd.glb` (= `mm6_lzd_d9r70s.glb`: d9r70c plus the sleeve weights below): LODs 6,888 / 3,707 / 1,671 / 683 (round 6: 9,854 / 5,141 / 2,172 /
691). `export/mm6_lzd_bow.glb` (= `mm6_lzd_bow_b6m.glb`): 1,358 / 664 / 304 / 110 (1,788 / 964 / 388 / 110).
LOD0 with the bow 11,642 -> 8,246 (-29 %). Installed with `tools/install_model.py ... --world mm6` (this also
replaced the stale Oct 12 `assets_source` copies). Coarsest LOD height 1.695 m, as installed.
Viewer `review/viewer/` (installed vs d9r70s, bow attached; `check_viewer.mjs` 54 switches, no console errors).
`OPENYAMM_REGRESSION_FILTER=actor_model ./build/game/openyamm --headless-run-regression-suite actors`: 53 pass,
`mm6_lizard_archer_actor_model_tiers_follow_sprite_scales` included; the 3 failures (guard, mage, ooze) predate this
change (`review/regression.log`). Rollback (install these): `work/mm6_lzd_source_pre_reduce.glb`,
`work/mm6_lzd_bow_source_pre_reduce.glb`. Earlier picks: `export/mm6_lzd_d8r68*.glb`, `work/candidates/`.

## Sleeves follow the arms (installed and accepted by the user 2026-10-14)

User: from behind, Attack frame 15, the arm is disconnected from the body. Also in the installed round 6
(`review/back/attack_sheet.png`): both tunic sleeves are weighted to `B_Spine2` out to the cuff, and the arm skin is an
open tube that starts inside the sleeve (40 % / 50 % along the right / left upper arm). In the draw the right
upper arm swings out and back, leaves the sleeve and shows its empty open end (`review/back/iso_sheet.png`, arm
weights in red). Codex recorded it as a compressed elbow pending artistic review.
`scripts/sleeve_weights.py` blends the tunic sleeve off the chest across the shoulder into the weights of the arm
skin under it, falling off with distance from the arm, smoothed over the surface, on every colour and shadow LOD
(634 vertices at LOD0). Tried and rejected: blend only next to the tube (back of the sleeve a flat sheet,
`review/back/sleeve_zoom.png`), hard selection radius (short edges stretched 5-7x, shared gate FAIL), wider blend
(the chest strap dragged, `sleeve_zoom3.png` column 4). Result `review/back/sleeve_final.png` and
`sleeve_final_zoom.png`; the tunic's grey shoulder trim, hidden under the pauldron before, now shows along the raised
sleeve. Shared gate `review/gates_d9s`: PASS, 7,416 checks. Viewer check 54 switches, no errors; actor regression
53 pass (same 3 old failures). Pre-fix build: `export/mm6_lzd_d9r70c.glb`.

## Gait rollout (2026-10-31)

Package [h06 of the gait rollout](../gait_rollout_20261031/h06/README.md) appended new locomotion clips (Walk2, Jog) to
the installed `assets_source/worlds/mm6/models/mm6_lzd.glb` (existing clips, meshes, skins and materials unchanged)
and installed it; the bindings are in `../gait_rollout_20261031/h06/bindings.yml`. Rebuild from the pre-gait copy:
`level_generation/creatures/gait_rollout_20261031/h06/scripts/rebuild.sh lzd`. A far-LOD repair, head-bob or
reduction rerun on this model must re-graft these clips: copy the new source over
`../gait_rollout_20261031/h06/work/mm6_lzd_pre_gait.glb`, rerun that rebuild and install its export.
