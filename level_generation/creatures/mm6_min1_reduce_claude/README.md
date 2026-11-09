# MM6 Minotaur (`min1`, BMinotaur A/B/C) reduction (2026-10-14)

User: "do minotaur next". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed
`assets_source/worlds/mm6/models/mm6_min1.glb` (7,876 tris, one material, three variants, eight influences, kilt
bones; Codex batch `../mm6_min1_codex/`, already reduced once with face and fingers protected; hand-closed hips) and
its attachment `mm6_min1_axe.glb` (1,854). Limits for the 1.85 m height: p99 5.55 mm, max 27.75 mm. No Meshy credits.

## Body
- **Hands kept, head at 70 %.** `B_Head`, `Hand` and `Finger` weights cover 3,975 faces (half the model); keeping all
  of them failed even at 70 % (p99 11.5 mm). Hands and fingers (1,521 faces, `work/hands.npy`) are kept exactly so
  the axe grip does not change; the head (2,454, `work/head.npy`) is reduced on its own at 70 %
  (`REA_KEEP_FACES`, `REA_PROTECT_FACES`, `REA_PROTECT_RATIO=0.7`). Uniform and head+hands-at-80 % steps also pass
  but would reduce the gripping fingers.
- **Installed LODs kept.** The installed LOD1-3 (1,674 / 1,591 / 735) are hand-repaired (closed hips) and already
  leaner than a rebuild would be (about 3,150 / 1,100 / 360). `scripts/swap_lod0.py` with `REA_KEEP_LODS=1` replaces
  only LOD0 and the full-detail shadow mesh; `scripts/build_keep.sh` builds a step that way (no LOD rebuild).
- Open edges: 18 loops / 504 edges at every step, as in the source (the kilt hem/waist openings); no flipped faces;
  texture drift 3 cm2. No two-sided pairs.

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 7,876 | | | |
| head + hands kept | 70 % | 5,512 | 11.5 / 50.4 | 0.981 | fail |
| head + hands kept | 90 % | 7,088 | 3.3 / 24.1 | 0.997 | pass |
| head + hands at 80 % | 80 % | 6,298 | 3.5 / 24.1 | 0.996 | pass; fingers reduced |
| uniform | 75 % | 5,906 | 3.8 / 24.1 | 0.995 | pass; fingers reduced |
| **hands kept, head 70 %** | **80 %** | **6,298** | 3.7 / 24.1 | 0.996 | **pick** (auto pass) |
| hands kept, head 70 % | 75 % | 5,904 | 5.0 / 32.0 | 0.992 | max only (Dead) |

## Axe
`scripts/prop_*.py` (the chain fighter's copies of the decoration chain). The handle is 1,275 of the 1,840 welded
faces (wrap rings, spiral), so keeping all of it left nothing to cut. The grip was located by sampling the clips: the
right-hand finger joints sit at the same point in the axe's own space in every clip (glTF (-0.026, 0.713, 0.006)); the
handle within ±10 cm of it (233 faces, `work/axe_dec/grip.npy`) is kept exactly. Normals: transferred normals mottled
the thin blades, and angle normals on everything turned the kept wrap bands into hexagonal boxes
(`review/props/grip_compare.png`), so the kept grip keeps its transferred normals and the reduced faces take normals
by angle at 60 degrees (`prop_build.py` from `../mm6_natf_reduce_claude/`, `nkept` in the step file; 35 degrees left
facets on the reduced shaft). **g45: 828** (g35 = 644 rounds the top spike and head socket). Installed LOD1-3 kept
(389 / 343 / 127). The weld merged 14 duplicate faces (the material is double-sided, so the reversed copies were
redundant).

## Result
`export/mm6_min1.glb` (= `mm6_min1_h70r80.glb`): LODs 6,298 / 1,674 / 1,591 / 735 (installed 7,876 / 1,674 / 1,591 /
735); `export/mm6_min1_axe.glb` (= `mm6_min1_axe_g45h60.glb`): 828 / 389 / 343 / 127. LOD0 with the axe 9,730 -> 7,126.
Review: `review/sheet_a.png` (+ `_clay`; installed, r80, r75), `review/sheet_clips.png` (installed vs pick in Attack,
Death and Cast), `review/props/axe_compare.png` (installed, g45 all by angle, pick),
`review/props/grip_compare.png` (grip close-up: installed, 35 degrees, pick). Viewer `review/viewer/` (body, installed /
pick per variant, every clip, eight-influence skinning; `check_viewer.mjs` 54 switches, no console errors).

## Installed, Attack and Death 2x faster (2026-10-14)

User: "accepted, attack should be 2x faster, death should be 2x faster". `scripts/retime_glb.py` divides the key
times of Attack (1.958 -> 0.979 s) and Death (2.4 -> 1.2 s) in the export (pre-retime copy
`export/mm6_min1_h70r80_unretimed.glb`); the other clips are unchanged. `actors.yml`: `attack_melee` and
`attack_ranged` impact 0.947917 -> 0.473958 s for BMinotaur A/B/C (cast unchanged). Previous sources backed up to
`work/mm6_min1_source_pre_reduce.glb` and `work/mm6_min1_axe_source_pre_reduce.glb` (rollback: install them and
restore the impact times); `tools/install_model.py export/mm6_min1{,_axe}.glb --world mm6`. The viewer's comparison
models are the previous source retimed the same way. `mm6_minotaur_actor_model_tiers_follow_sprite_scales` passes.
The `actors` suite ends with `Fatal error: std::bad_alloc` after its last case (also on a run before these
installs; peak memory 1.4 GB) and two of five runs segfaulted in `mm6_drake_and_dragon_actor_model_burn_death`
(once before any Minotaur change); both are outside this work. Lease released.

## Cast = copy of Attack (2026-10-15)

User: "sync cast animation with attack animation (copy attack animation into cast animation)". `scripts/copy_clip.py`
replaces the Cast clip with its own copy of Attack's keys (0.979 s; the old 2.533 s Cast is dropped and the binary
compacted); meshes, skins, textures and the other clips are byte-identical. Pre-copy export:
`export/mm6_min1_pre_castcopy.glb` (rollback: install it and restore the cast impact 1.516667). `actors.yml`: cast
impact 1.516667 -> 0.473958 for BMinotaur A/B/C (= Attack), launch socket unchanged.
`mm6_minotaur_actor_model_tiers_follow_sprite_scales` passes.

## Superseded (2026-10-15)

Rebuilt on Codex round 3 (closed hips) in `../mm6_min1_r3_reduce_claude/`, which is now installed.

## Floor fix — 2026-10-21

`--ground-loop Walking`. Before, in world units at tier A: walking lifts every foot by +2.8.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_min1.glb`), written to `export/mm6_min1_floor.glb` and installed as `mm6_min1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
