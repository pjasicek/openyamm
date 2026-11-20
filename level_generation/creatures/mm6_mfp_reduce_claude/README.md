# MM6 Cutpurse (`mfp`, PeasantF3 A/B/C: Cutpurse / Bounty Hunter / Assassin): dagger stab + reduction (2026-10-14)

User: "3D tris count reduction playbook - do cutpurse", then "for the attack - pick some dagger attack animation
instead first". Review viewer: `review/viewer/` (installed, installed + new stab, reduced + new stab, per variant,
knife attached at its joint).

## Base model: the round-3 runtime, not `assets_source`

`assets_dev/worlds/mm6/models/mm6_mfp.glb` (what the game runs) is Codex's round-3 export
(`../mm6_mfp_codex/export/mm6_mfp.glb`, 10,183 tris, 2048x1628 atlas, Death 2.144 s, Attack 1.125 s); it was copied into
`assets_dev` directly. `assets_source/worlds/mm6/models/mm6_mfp.glb` is an older revision (10,180 tris, 2080x1024
atlas, Death 2.979 s) and its knife differs in file (same geometry and UVs). Both are untracked in git. Everything
below is built on the round-3 export (`work/mm6_mfp_r3_runtime_source.glb`, knife `work/mm6_mfp_knife_r3_runtime_source.glb`).
The first pass on the stale source is archived in `work/old_base/`, `export/old_base/`.

## New Attack: right-hand dagger stab

Candidates retargeted onto the round-3 rig (`anim/codex_lod0.blend` = `../mm6_mfp_codex/work/round3/lod0.blend`,
rest and clips identical to the runtime GLB within 0.02 mm; `retarget.py` / `retarget_mixamo.py` from natm, extra
bones hold Standing) and rendered on the body (`review/attack/C_*.png`, `scripts/cand_sheet.py`, `tip_probe.py`):

| clip | finding |
|---|---|
| installed (Codex: humanoid set Dagger R3, heavily damped) | overhead hack, reads as a hammer blow |
| set Dagger-Attack R1 / R2 / R3 | deep-guard crouch, lunge and a leap; not upright |
| Mixamo "Stabbing" | stabs with the left (lead) hand |
| Mixamo "Stabbing (2)" | swings the knife out to the side |
| **Mixamo "Stabbing (1)"** | **right hand draws back and thrusts forward at chest height (tip 0.77 m ahead, 1.34 m high)** |

`scripts/author_stab.py` on `C_Stab1P` (`:plant`: legs and pelvis hold Standing, chest yaw aligned): source frames
4-38 time-remapped to 1.30 s (wind-up, thrust f22-28, short hold, the second slash and source recovery dropped), every
bone blended from and back to Standing frame 0, the installed Attack's fist and visible knife (the knife stays hidden
in every other clip, as installed), hand turned -25 deg about Z over the thrust so the knife points ahead (yaw 14-19
deg at impact instead of 31-44), **wrist bend capped at 30 deg** with the excess moved to the forearm about the elbow
(the mocap bent it 64 deg, 88 with the aim, and the rigid bangles folded; installed attack ~22 deg), twist bones baked
as in the Codex rig. Gates: knife inside the body only where the handle sits in the fist (<= 7 mm, same as installed);
grip gate 0 penetrations; `review/attack/stab3_tex.png` (textured, party front, side, right hand).
Impact: frame 23 of 39 = **0.59** (the thrust covers 88 % of its reach by frame 22, then creeps; the 95 % rule gives
frame 26). `actors.yml` PeasantF3 A/B/C `events` (attack_melee, attack_ranged, cast) need 0.59 instead of 0.65625 at install.
Splice: `export_clip.py` (armature-only GLB, every frame, all 363 channels) -> `splice_clip.py` (replaces the Attack
animation by node name, compacts the buffer); `clip_match.py` 0.001 mm against the blend.

## Body reduction (round-3 base, new Attack)

Same recipe as the first pass (per-region budgets; `label_faces.py` with the round-3 head set at u > 0.795):
face, eyes, lips and all small pieces (jewellery, coins, beads, anklets; components <= 80 faces) kept exactly plus
two rings around the vertices a uniform cut moved most (waist, `err_verts.py`); hair 75 %, hands 45 %, braid 80 %,
skirt 85 % (its medallion print tears under a uniform cut), the rest takes the ladder.

| config | triangles | p99 / max mm | drift > 40 | |
|---|---:|---|---|---|
| uniform r70 | 7,127 | 2.8 / 17.3 | | passes (the round-3 mesh is cleaner than the old source) |
| **c6 r78** | **7,939** | 3.8 / 19.2 | 23.8 cm2 | **pick**: IoU 0.993, SSIM 0.998 |
| c6 r76 | 7,737 | 4.5 / 25.2 | | fails max |
| c8 (c6 + drift lock) r80 | 8,143 | 3.7 / 19.2 | 7.9 cm2 | same look as c6r78; r78 fails max |

Close-ups `review/close/sheet_{head,torso,skirt}_r3.png` (installed / c6r78 / c8r80).
Lesson for the playbook: a strongly patterned cloth piece tears under the texture-aware collapse long before its
geometry error shows; give it its own gentle ratio.

## Knife

Identical geometry and UVs in both revisions, so the first pass carries over: `k6` keeps the blade (50-65 % dented the
edge and smeared the shading) and the grip exactly, collar and pommel at 60 % (lower loses the pommel ring groove):
2,344 -> 1,895, LODs 1,895 / 1,289 / 543 / 303. `review/props/knife_close_r3.png`, `grip_sheet_r3.png`.

## Result (staged, not installed)

`export/mm6_mfp.glb` (= `mm6_mfp_c6r78.glb`, new Attack): LODs 7,939 / 3,941 / 1,339 / 384 (installed 10,183 / 5,513 /
2,278 / 1,235), shadow LODs rebuilt, variants carried. `export/mm6_mfp_knife.glb`. Unreduced round-3 + new Attack:
`work/mm6_mfp_r3_stab3.glb`. LOD0 with the knife 12,527 -> 9,834 (-21 %).

Install after review: `tools/install_model.py export/mm6_mfp.glb --world mm6` and the knife (this also refreshes the
stale `assets_source` copies), `actors.yml` impact 0.59, actor regression, ledger, playbook lesson.
Rollback: `work/mm6_mfp_r3_runtime_source.glb`, `work/mm6_mfp_knife_r3_runtime_source.glb`.
Lease `mm6:mfp` is held by `claude-mfp-reduce` until install.

## Installed (2026-10-15)

User picked "newest staged" after the model cook had rebuilt `assets_dev` from the stale `assets_source` copies.
`tools/install_model.py export/mm6_mfp.glb --world mm6` and `export/mm6_mfp_knife.glb` (sources now = this export);
`actors.yml` PeasantF3 A/B/C attack_melee, attack_ranged and cast impact 0.65625 -> 0.59. Previous sources (the stale
10-12 revision) are `work/mm6_mfp{,_knife}_source_pre_reduce.glb`; round 3 without the stab and reduction is
`work/mm6_mfp{,_knife}_r3_runtime_source.glb`. Unit suite: only the three known unrelated failures. Timing review data
rebuilt.

## Knife shadow LOD fix (2026-10-15)

The installed reduced knife failed to load ("model mesh LOD reference is invalid or duplicated"): `prop_swap_glb.py`
dropped the knife's four shadow meshes but kept `openyamm_shadow_lods: [4, 5, 6, 7]`. The list is removed (the knife
casts its colour LODs, like every other attachment; the old shadow meshes were copies of them) and reinstalled;
the faulty file is `export/mm6_mfp_knife_badshadow.glb`. Every copy of `prop_swap_glb.py` now drops the list too.
A scan of all 520 installed and source models finds no other invalid LOD reference.

## Gait rollout (2026-10-31, package h05)

New in-place locomotion clips appended to the installed `assets_source/worlds/mm6/models/mm6_mfp.glb` (every existing
clip, mesh, skin and material unchanged): Walk2 (Mixamo Walk, 0.84 s, 1.60), Jog (Unarmed-Run-Forward, 0.63 s, 2.41), Sprint (Unarmed-Sprint, 0.56 s, 3.41); the five-ring skirt cage is refitted to the new legs (a port of `mm6_mfp_codex/scripts/final_skirt.py`). Bindings for PeasantF3 A-C (applied by the rollout coordinator from
`../gait_rollout_20261031/h05/bindings.yml`): walking Walk2, stride_length 1.6, run Jog, run_stride_length 2.41, sprint Sprint, sprint_stride_length 3.41. Details, gates and doubts:
[package h05](../gait_rollout_20261031/h05/README.md). Rebuild: `../gait_rollout_20261031/h05/scripts/rebuild.sh mfp`
from the pre-gait copy `work/mm6_mfp_pre_gait.glb` there. A far-LOD repair (`lod_repair_claude`) or head-bob rerun on
this model must re-graft these clips (copy the repaired source over that pre-gait copy and rerun the rebuild).

## Anim fix (2026-11-11, MM6–MM8 audit)

Jog and Sprint recomposed with a low knee and shorter, quicker steps so the wrap skirt no longer balloons (cloth bad
47.6 -> 13.4 %, 59.6 -> 11.1 %); bindings `run_stride_length` 2.05, `sprint_stride_length` 2.6. Details and rebuild:
[mm6_mfp_animfix_claude](../mm6_mfp_animfix_claude/README.md).
