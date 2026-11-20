# MM6 Swordsman / Expert / Master (`nobl`, Nobleman A/B/C) reduction (2026-10-14, not installed)

User: "then can we check the master swordsman" (after the Ghost). No-retexture route
([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed `assets_source/worlds/mm6/models/mm6_nobl.glb`
(9,493 body tris, four influences; the 256-tri sword is a separate attachment and unchanged), started with
`../reduce_installed.sh nobl Swordsman "MM6 Swordsman"`. Weld 8,475 -> 929 open edges; limits for the 1.69 m height
p99 5.06 mm, max 25.3 mm. Scripts copied from `../mm6_gst_reduce_claude/` (`REA_PROTECT_FACES`, `run_ladder.sh`,
`build_pick.sh`, `close_views.py` with `REA_CLIP`/`REA_FRAME` and a shoulder spot, `probe_max.py` with `REA_FRAMES`).

## Ladder

| config | step | tris | p99 / max mm | IoU | SSIM | visual |
|---|---|---:|---|---|---|---|
| source | | 9,493 | | | | |
| uniform | 70 % | 6,645 | 4.2 / 20.4 | 0.995 | 0.995 | auto-pick (only passing step) |
| uniform | 55 % | 5,221 | 6.5 / 51.4 | 0.990 | 0.990 | eyes and brows change |
| uniform | 45 % | 4,271 | 8.8 / 74.3 | 0.980 | 0.982 | face broken |
| head set kept | 55 % | 5,221 | 8.8 / 74.3 | 0.981 | 0.983 | head + hair (2,250) starve the body |
| face kept | 62 % | 5,885 | 6.5 / 51.4 | 0.989 | 0.990 | face exact; capelet shows the dark sleeves in Attack |
| face kept | 54 % | 5,125 | 8.9 / 74.3 | 0.980 | 0.982 | large capelet patches |
| face kept, cloak +4 mm | 62 % | 5,885 | | | | push does not hide them |
| **face + capelet top kept** | **62 %** | **5,885** | 6.9 / 74.3 | 0.987 | 0.989 | **pick** |

Face = head-set faces with skin colour plus one ring (`work/face_faces.npy`, 1,484); capelet top = cloak-mask faces
above z 1.25 m (464; `work/face_cape_faces.npy`, 1,948 together). The rest is cut to about 52 %. The worst errors
(probe) are inner thighs under the tunic skirt and the cloak in Death/Attack frames; the renders of those frames match
the installed model. The capelet patches are the shoulder sleeves passing through the capelet in the wide Attack
pose; the installed model already shows two small ones, and the pick shows the same two.

## First pick (superseded by the chest repair below)
`export/mm6_nobl.glb` (= `mm6_nobl_facecaper62.glb`): LODs 5,885 / 2,862 / 979 / 269 (installed 9,493 / 4,670 /
1,608 / 460), variants on all LOD/shadow primitives, Sword node kept. Close renders `review/close/sheet4_whole.png`
(rows installed/pick: standing, Death 15, Death 30, Attack 15), `sheet4_face_hand.png`,
`sheet4_Attack_shoulder.png`. Viewer `review/viewer/`: installed / pick / uniform 70 %; `check_viewer.mjs` 72 loads,
no errors. Known: one sharper facet on the orange collar.

## Chest repair and body retexture (2026-10-14, superseded as the export by the front detail set below)

User questions on the pick: what the capelet "rivets" are, the missing necklace, and the asymmetric clasp; repair on the
mesh first (animations intact), then retexture. The native sprite and HD masters show a twisted white/silver cord
along the capelet hem, a thin gold V chain from the clasp ends to a gem pendant, and a symmetric gold clasp bar. Meshy
had made them ~80 loose 6-vertex 'link' blobs (hem studs; necklace bits floating in front of the tunic), and the clasp
had a ball on one end and a green-painted curl on the other.
- `scripts/chest_repair.py` (on the pick): blobs removed; cord = 99 overlapping, alternately tilted lumps on the hem path
  the blobs traced (`work/beads.npy`), on the capelet surface with its weights (792 tris); necklace = alternating links
  lying on the tunic in a V plus a hex pendant with a gem, tunic weights, pendant rigid (206 tris); clasp: left knob and
  left half of the bar mirrored over the bar centre. Face attribute `chest_part` tags the new parts.
- `scripts/body_uv.py`: fresh body-set UVs (head set untouched), clasp 2x; cord, links, pendant, gem each on one flat
  colour square (2.92 texels/cm body, installed 3.17). Meshy `body_retexture_r62` (HD masters, 10 credits, UV parity
  exact). Lease `mm6:nobl-reduce` (budget 10) held for the install.
- After the job: `scripts/buckle_uv.py` replaces the lower belt buckle (crumpled by the reduction, painted dark by
  Meshy) with a clean gold frame and prong (60 tris), from `work/ladder_body_meshy.blend` (the painted layout).
- `scripts/bake_body_ao.py`, `scripts/compose_body.py`: Meshy's tunic buttons/seam filled from the surrounding cloth;
  classes from the new colours (cloak/tunic only on the installed cloak/tunic faces); gold/silver graded to the
  project targets; AO; cloak, tunic and rest luminance-matched to the installed classes (installed tier ramps kept);
  flat squares silver cord, gold chain/pendant/buckle, red gem. `scripts/body_atlas.py` pastes the body half; the head
  half and all materials/ramps are identical to the installed model.

`export/mm6_nobl.glb` (= `mm6_nobl_bodyr62.glb`): **6,603 tris** (LODs 6,603 / 3,179 / 1,065 / 269). Renders
`review/close/sheet5_chest.png` / `sheet6_chest.png` (installed vs final), `sheet6_tunic.png`, `sheet6_tiers.png`,
`sheet7_anim.png` (every clip), `chest_clay*.png` (shapes). Viewer: installed / final / earlier pick, 72 loads pass.

## Front detail set (2026-10-14)

User: the area around the capelet/shoulders and the collar is smeared, the black area below the neck too, and the
tabard (front); an extra 512/1024 texture is welcome if it adds clarity. Third 1K atlas section (body | head | detail,
3136 x 1024; the installed Fire Lizard's atlas is already 4128 wide), one primitive and material as before.
- `scripts/detail_faces.py`: collar/neck/undershirt V, capelet, chest (all tunic), tabard (tunic + front-most faces below
  the belt), belt/clasp pieces; backward-facing faces covered within 15 cm (tunic back under the cloak, cloak top under
  the capelet) stay in the body set. Installed cloak/tunic class per face read on `work/ladder_chest.blend` (installed
  UVs) and stored as face attribute `inst_region`. `review/detail_faces.png` shows the groups. 10,894 cm2.
- `scripts/detail_uv.py`: detail UVs (6.0 texels/cm, body 2.9); upload with the detail faces on 94 % of the square and the
  rest of the character in a corner. Meshy `detail_retexture_r62b` (10 credits). `detail_retexture_r62` (10 credits)
  was painted on a wrong selection (classes read through the new body UVs) and is unused; Meshy total 30 credits.
- `scripts/detail_groups.py`: group per detail triangle; the belt/clasp group reads the body texture again (cleaner).
- `scripts/compose_body.py` (REA_SET=detail; also the body set): Meshy's gold on the tunic removed (ghost of the modelled
  chain, doubled emblem; texels within 1.2 cm of the chain refilled), cord and clasp paint spilled onto the capelet and
  upper tunic refilled, cloth de-streaked (Meshy's soft shading kept by a blur within group and colour cluster, plus an
  even grain from 3D position), one analytic gold V emblem drawn in both sets where the installed one sits, red paint
  on the torso below the collar counted as tunic (it stayed red in every tier). `scripts/head_collar.py` de-streaks the
  collar band that lies in the head texture. `scripts/detail_atlas.py` widens the atlases. Chain: `scripts/texture_chain.sh`.

Blur fix (user: "why does it still look blurry?"): the blur was ours, not Meshy's (its raw return is crisp:
`review/close/sheet17_top.png` style render of `meshy/detail_retexture_r62b`). Removed: the de-streak blur and grain,
the original compose's cloth smoothing, the texture-space blur fills (they mixed unrelated UV islands into bands);
stray paint is now replaced by the nearest wanted texel in 3D. Luminance is matched by one median gain per region
(a full quantile match stretched Meshy's fabric noise over the old fold range), and fine luminance detail inside the
two ramped cloth regions is compressed (^0.4 around a sigma-1.5 local mean) because the tier ramps were rank-matched to
the old smoothed texture and turn fine grain into speckle. The detail section keeps Meshy's resolution: 2048 px
(`scripts/atlas_layout.py`: atlas 3104 x 2080, head (0,0), body (0,1056), detail 2048 at (1056,0);
`scripts/atlas_final.py` assembles it). The emblem sits on the tabard's front layer only; Meshy's dark emblem outline
is replaced by nearby cloth. Chain: `scripts/texture_chain.sh` (77 s).

`export/mm6_nobl.glb` (= `mm6_nobl_finalr62.glb`): 6,603 tris, materials and tier ramps identical to the installed
model. Renders `review/close/sheet16.png` (shoulders, collar, tunic), `sheet17_top.png` (high angle, all tiers),
`emblem_cmp2.png`. Viewer: installed / final / 1K-detail comparison, 72 loads pass. Known: the collar sides keep some of
Meshy's streak, light wool tufts beside the clasp (Meshy's trim paint, kept).

## Installed (2026-10-14)

User: "good enough accepted". Previous source backed up to `work/mm6_nobl_source_pre_reduce.glb` (rollback: install
that file); `tools/install_model.py export/mm6_nobl.glb --world mm6`; `mm6_swordsman_actor_model_tiers_share_one_size`
passes (`work/regression_swordsman.log`). Ledger row added; lease released. Meshy: 30 credits (10 of them on the
superseded `detail_retexture_r62`).

Original install plan: back up the installed source to `work/mm6_nobl_source_pre_reduce.glb`, then
`tools/install_model.py export/mm6_nobl.glb --world mm6`, `mm6_swordsman_actor_model_tiers_share_one_size` (actors suite), and the ledger row.

## Attack start retimed (2026-10-14)

User decision in the attack timing review (`level_generation/creatures/timing_review/`): the first 0.4 s of Attack
play 2x faster, easing back to its own speed over the last 0.1 s, so the Nobleman reaches his attack stance before the
swing. `timing_review/retime_clip.py export/mm6_nobl_unretimed.glb export/mm6_nobl.glb --clip Attack --end 0.4
--speed 2 --ramp 0.1` (Attack 1.2 -> 1.019 s; other clips unchanged), installed with `tools/install_model.py`. The
`attack_melee` impact moved with it, 0.78 -> 0.599 s, for Nobleman A/B/C in `actors.yml`. The billboard contact frame
(noblata frame 3, 0.375 s) and an attack sound delay of 0.15 s are in
`assets_dev/engine/rendering/sprite_attack_timing.yml`.
Rollback: install `export/mm6_nobl_unretimed.glb` as `mm6_nobl.glb` and restore the 0.78 s markers.

## Floor fix — 2026-10-21

`--lift-joints Attack`: cloak strips bend at most 14 degrees. Before, in world units at tier A: Attack sinks to -4.9.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_nobl.glb`), written to `export/mm6_nobl_floor.glb` and installed as `mm6_nobl.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31, package h05)

New in-place locomotion clips appended to the installed `assets_source/worlds/mm6/models/mm6_nobl.glb` (every existing
clip, mesh, skin and material unchanged): Walk2 (Mixamo Walk, 0.82 s, 1.75), Jog (Unarmed-Run-Forward, 0.66 s, 2.80), Sprint (Unarmed-Sprint, 0.56 s, 4.10); cape chains from the accepted clips, turned back 6 / 15 deg in Jog / Sprint and pushed out of the leg and boot capsules; front tabards follow the thighs. Bindings for Nobleman A-C (applied by the rollout coordinator from
`../gait_rollout_20261031/h05/bindings.yml`): walking Walk2, stride_length 1.75, run Jog, run_stride_length 2.8, sprint Sprint, sprint_stride_length 4.1. Details, gates and doubts:
[package h05](../gait_rollout_20261031/h05/README.md). Rebuild: `../gait_rollout_20261031/h05/scripts/rebuild.sh nobl`
from the pre-gait copy `work/mm6_nobl_pre_gait.glb` there. A far-LOD repair (`lod_repair_claude`) or head-bob rerun on
this model must re-graft these clips (copy the repaired source over that pre-gait copy and rerun the rebuild).
