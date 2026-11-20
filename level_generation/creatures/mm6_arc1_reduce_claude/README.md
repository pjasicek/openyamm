# MM6 Archer (`arc1`, BArcher A/B/C: Archer / Master Archer / Sniper) reduction (2026-10-14)

User: "do mm6 archer" (3D tris reduction playbook). No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the archer body (9,531 tris, one merged body + head atlas material, three variants) and its held bow (2,108). The
nocked arrow (92) is left as is. Per-region scripts copied from `../mm6_fgt_reduce_claude/`. No Meshy credits.
Limits for the 1.70 m height: p99 5.1 mm, max 25.5 mm.

## Input: the installed round-6 export, not `assets_source`

`assets_source/worlds/mm6/models/mm6_arc1*.glb` (2026-10-12 17:29) are stale: they are Codex's round-5
`work/round5/runtime_unpadded/` snapshot, before the texture repack (body maps 0.75x, bow 0.875x) and the round-6
Attack/Cast retime (1.733 -> 1.156 s). The game runs `assets_dev/worlds/mm6/models/mm6_arc1*.glb`, which are
byte-identical to `../mm6_arc1_codex/export/` (round 6, copied without `tools/install_model.py`). The input snapshot
is `work/latest/` (copies of that export); every script here reads it. Same geometry and face order as the stale
copy, different UVs. A first pass on the stale copy is kept in `stale_r5_source/` for reference only (wrong UVs for
the installed textures; do not install).

## Body: per-region budgets

Pieces (`scripts/pieces.py` -> `work/components.npy`, `scripts/region_faces.py` -> `work/regions.npy`): main body
4,028 (face/neck skin 913 of it), hair 1,199, eyes and mouth pieces 609, two five-finger hands 1,038 + 1,034, quiver
364, seven quiver arrows ~83 each, bracers 129 + 120, pauldrons 101 + 98, sleeve cuffs 100 + 96, the bowstring 24
(skinned to the Bow* bones; the thin line beside her in renders without the bow) and three tiny bits.

| config | step | triangles | p99 / max mm | IoU | finding |
|---|---|---:|---|---|---|
| source | | 9,531 | | | |
| head kept (auto route, stale pass) | r70 | 6,671 | 3.3 / 16.2 | 0.990 | pass; r55 fails |
| g1: face, eyes, mouth, arrows, string kept; hair 60 %, hands 45 %, shells 70 % | r60 | 5,717 | 4.5 / 17.6 | 0.988 | pass; centre lacing bends into a zigzag, bracer rims jagged |
| g2: g1 + lacing strip (94) and both bracers kept + one drift lock | r63 | 6,003 | 4.4 / 17.6 | 0.988 | pass; the left boot's painted top edge moves up and turns jagged |
| g3: g2 + trouser/boot colour edge and its one-ring kept (273) | r63 | 6,003 | 5.3 / 19.7 | 0.985 | fails p99 |
| **g3** | **r66** | **6,289** | 4.2 / 17.6 | 0.990 | **pick**: lacing, bracers and boot edges as installed |

Keep sets: `scripts/make_groups.py g1`, `scripts/keep_lacing.py` (lacing |x| < 3 cm on the bodice front, bracers),
`scripts/drift_lock.py work/keep_g2a.npy work/keep_g2.npy r60` after `texture_drift.py r60`,
`scripts/keep_boot_edge.py` (leg faces whose texture samples hold both trouser blue and boot brown, plus one-ring).
Run: `REA_KEEP_FACES=work/keep_g3.npy REA_GROUPS=work/groups_g3.npy REA_GROUP_RATIOS=1:0.6,2:0.45,3:0.7
scripts/run_ladder.sh g3 0.66,0.63`, then `scripts/build_pick.sh r66 g3`. Texture drift of the pick: one 0.1 cm2
face above 40, p99 13.7.

## Bow

Parts: two limbs (574 each), grip wrap 624 (the left fist is fitted to it), six string-loop rings 56 each.
`scripts/bow_ladder.py` keeps grip and rings exactly and decimates each limb on its own (two-way Hausdorff per limb,
prop limits 1.5 % / 0.15 % of the bow length): b45 1,476, b35 1,360 pass, b25 1,244 fails (and kinks the recurve
tips in the stale pass). **Pick b35 (1,360)**: tips round, grip unchanged (`review/props/bow_close.png`,
`scripts/bow_close.py`). Built with `prop_build.py bow:b35` and `prop_swap_glb.py`; installed LODs 1,150 / 420 / 193
kept.

Grip gate (`scripts/grip_gate_posed.py`, bow at the posed `Bow` joint, left hand, every 2nd frame of Attack, Cast,
Standing, Walking, Hit, Fidget): per frame, left-hand vertices inside the 11 mm grip 11 -> 2, in contact 95 -> 53
(scales with the hand's vertex count), nearest 8.6 -> 9.4 mm from the axis. `review/grip/grip_sheet.png` (rows
installed, pick; Standing and mid-Attack).

## Body retexture (user review of g3r66: neckline smears)

User: pale smears and torn dark flaps along the bodice's V-neck ("retexture body i think"). They are in the installed
texture too. The installed round-5 atlas is about 680 islands, many of them single triangles (24 % coverage), so
painting onto it was not an option; the playbook's fresh-UV route instead, keeping the accepted head texture.

1. `scripts/uv_fresh.py -- g3 Cand_66` (`REA_BODY_ANGLE=80 REA_HEAD_ANGLE=80`): head or body per face by where its
   installed UVs sit (`work/headchart_label.npy`, rasterised from the source head set: hair, eyes, mouth, face/neck skin
   above 1.41 m; 2,225 of 6,289 reduced faces), component by the nearest source face. Layers `OldUV`, `Upload` (body
   Smart UV at 80 deg packed into 94 % of the square, head islands in the 6 % corner so Meshy sees the whole figure),
   `UVMap` (runtime 2048 x 1024: body left square, head right square). Body 40 % coverage, 78 % of its area in 27
   islands. Writes `work/retex_g3.blend`, `texturing/arc1_body_upload_g3.glb`, `work/cand_export.glb`.
   `scripts/dump_retex_faces.py` re-dumps the per-corner data by layer name (a held UV-layer reference goes stale
   once new layers are added; the first dump read garbage old UVs and scrambled the head).
2. Meshy `body_retexture_g3r66` (`requests/`, the accepted v1 body request with `enable_original_uv: true` and the
   four HD views): **10 credits**. UV parity exact (Meshy only rescales positions).
3. AO: `../claude_shared/bake_creature_ao.py` on `work/retex_g3_ao.blend` (UVMap active) -> `work/ao_g3.png`.
4. `scripts/compose_retex.py g3 body_retexture_g3r66`: body texels from Meshy (x AO, boots darkened, Meshy normal at
   0.7 after the convention check, which flipped it: score -0.997), material classes (cloth: blue on every body piece
   but hands and arrows, which is also the tier region; skin; arrows; leather); head texels from the installed maps
   at the same surface point (normals re-expressed in the new face frames); neck skin moved by the body skin's
   change (gain 0.97 / 0.94 / 0.93 measured on points that are skin in both); tier ramps from the native palettes
   660/661/662 against the new cloth luminance.
5. `swap_lod0.py` + `build_actor_lods.py` + `carry_variants.py` on the new-UV candidate, then `scripts/patch_maps.py`
   (images by name, ramps per variant): `export/mm6_arc1_g3t.glb`.

Review: `review/faces/sheet_retex.png` + `_clay` (rows installed, retexture: face front, three-quarter, side, back,
whole), `review/faces/sheet_tiers.png` (rows B installed, B retexture, C installed, C retexture),
`review/faces/sheet_tier_a.png`. Known: a small dark speck Meshy painted on the right thigh above the boot.

User review of the retexture (bracers, forehead), both in `compose_retex.py`:
- Meshy painted the right bracer skin-coloured and the left one only half leather. The bracers (components 8, 15, kept
  exactly by the reduction) now take every map from the installed atlas like the head.
- The installed head set paints a red-orange fringe on the forehead skin between the hair mesh's locks (in the
  installed model too). Face texels above the eye centres (1.585 m) that are hair-coloured and not under the hair mesh
  (no hair triangle within 6 cm along the face normal) become skin: a smooth field from the surrounding forehead skin,
  flat normal, skin specular/roughness. Dark components of 120+ texels (brows, lashes) are kept.
Review: `review/faces/sheet_fix.png` (rows installed, fixed: face front, three-quarter, arms front, arms back),
`review/faces/sheet_fix_tiers.png` (B, C).

## Attack stance (user: "her completely still feet during attack")

Codex's round 5 pinned both ankles of Attack (and Cast, which shares its accessors) at the narrow idle spot (10 cm
apart, toes at the target) while the hips turn 44 deg and the chest ~90 deg: the knees twisted with the hips, the left
knee bent 12 cm inward and the right leg locked straight (178 deg, the pelvis reach limit). Still feet are right for a
shot; that stance was not. `scripts/attack_stance.py <in> <out>` rewrites only the pelvis translation and the
thigh/calf/foot rotations of the shared accessors: weight w = hip turn / peak (smoothstep), so the feet move with the
hips during the wind-up (0.04-0.2 s) and back during recovery (0.95-1.13 s). Right (rear) foot steps 21 cm from the
left along the turned hip line (about 11 cm back, 5 cm out), lifts 3 cm mid-step and pivots 0.9 x the turn; the left foot
advances 4 cm (the left hip moves forward over it), lifts 1.5 cm and pivots 0.55 x the turn. Two-bone IK with the knee pole
blended from the original knee to over the toes; pelvis drops (at most ~3 mm) where the rear knee would exceed 173 deg.
Hold: knees 142 / 173 deg (was 145 / 178); the left-hip drop is the source's pelvis roll and was left so that the
upper body, bow aim, arrow and timing are unchanged. First/last keys are unchanged (asserted). Lowest sole point during the
hold 2.0 / 0.4-0.5 mm (deformed LOD0), no floor penetration. Chain: `patch_maps.py` -> `work/g3t_maps.glb` ->
`attack_stance.py` -> `export/mm6_arc1_g3t.glb`. Review: `review/anim/attack_stance.png` (rows front, side, top;
installed then new; frames 0, 3, 5, 12, 23, 25 at 24 fps).

## Result (accepted, installed 2026-10-14)

- `export/mm6_arc1.glb` (= `mm6_arc1_g3t.glb`): g3r66 geometry, LODs 6,289 / 3,143 / 1,131 / 370 (installed 9,531 /
  5,223 / 1,904 / 620), new 2048 x 1024 atlas (base colour, specular/roughness, normal, region mask; same memory as
  the installed 1568 x 1376), variants and new ramps on every primitive; clips as round 6 except the Attack/Cast legs (archer stance above).
  `mm6_arc1_g3r66.glb` is the reduction with the installed texture.
- `export/mm6_arc1_bow.glb` (= `mm6_arc1_bow_b35.glb`): 1,360 / 1,150 / 420 / 193, installed bow textures.
- LOD0 body + bow + arrow 11,731 -> 7,741 (-34 %). Meshy 10 credits.
- Viewer `review/viewer/` (per tier: installed, reduced with the installed texture, reduced + retexture; every clip;
  `check_viewer.mjs` 72 switches, no console errors). Earlier review sheets: `review/faces/sheet*.png`,
  `review/props/bow_close.png`, `review/grip/grip_sheet.png` (geometry unchanged by the retexture). Other
  candidates are in `work/candidates/`.

Installed 2026-10-14 after user acceptance with `tools/install_model.py --world mm6`: `export/mm6_arc1.glb`,
`export/mm6_arc1_bow.glb` and the unchanged arrow (`../mm6_arc1_codex/export/mm6_arc1_arrow.glb`), which also replaced
the stale Oct 12 `assets_source` copies. Rollback (install these): `work/mm6_arc1_source_pre_reduce.glb`,
`work/mm6_arc1_bow_source_pre_reduce.glb`, `work/mm6_arc1_arrow_source_pre_reduce.glb` (the round-6 runtime files,
byte-identical to `assets_dev` before the install). `OPENYAMM_REGRESSION_FILTER=actor_model ./build/game/openyamm
--headless-run-regression-suite actors`: 53 pass, `mm6_archer_actor_model_tiers_share_the_native_height` included; the
3 failures (guard, mage, ooze) predate this change (`review/regression.log`). Meshy 10 credits.


## Gait rollout — 2026-10-31

Package [h03](../gait_rollout_20261031/h03/README.md) appended `Jog` to the installed `mm6_arc1.glb` for the chase
(BArcher A-C: Standard and MAW chase at a run pace, Froude above 0.65, which played `Walking` at x2.44-2.78): humanoid set 2Hand-Bow-Run-Forward legs, arms, bow and arrow from `Walking` (both arms turned out 8 deg: the bow met the left thigh, the right hand the right thigh);
0.74 s, bound stride 2.1358 (2.84 u/s); phase-aligned to `Walking`, planted feet at 5 deg toe-out. Bound as `run` (the coordinator applies
`h03/bindings.yml`); `Walking` stays the wander clip. Every existing clip, mesh, skin and material is byte-identical.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h03/scripts/rebuild.sh arc1` (from the pre-gait copy
`h03/work/mm6_arc1_pre_gait.glb`). A far-LOD repair, floor-fix or any re-export of this model must re-graft `Jog`
(copy the new source over the pre-gait copy and rerun the rebuild, or graft it with `claude_shared/graft_clips.py`).
