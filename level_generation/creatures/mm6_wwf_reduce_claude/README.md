# MM6 Werewolf (`wwf`, Werewolf A/B/C) reduction (2026-10-14)

User: "do the playbook 3D tris reduction method on wolfman". No-retexture route
([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed `assets_source/worlds/mm6/models/mm6_wwf.glb`
(10,821 tris, one merged material: body set left, head set right of the 2080x1024 atlas; three variants; from
`../mm6_wfigt1_claude/`). Started with `REA_PROTECT_HEAD=1 ../reduce_installed.sh wwf Werewolf "MM6 Werewolf"`.
Weld 8,713 -> 1,161 open edges; limits scaled to the 1.514 m height (p99 4.54 mm, max 22.71 mm). No Meshy credits.

## Werewolf-specific changes
- **Head set at 60 %, not kept.** Head/Jaw weights cover 4,367 faces (40 %): the head shell plus 128 mane-card,
  tooth and tongue pieces. Keeping them all forced the body below 50 % and failed. `work/headset.npy` (faces in the
  head half of the atlas, 4,322) is protected and decimated on its own at 60 % (`REA_PROTECT_FACES`,
  `REA_PROTECT_RATIO=0.6`, as for the Ghost). Face, teeth and eyes are unchanged in the renders.
- **Necklace kept exactly.** The gold chain tube and pendant (`work/necklace.npy`, 528 faces) broke into gaps at
  55 %. `decimate_tex.py` takes a new `REA_KEEP_FACES` set that is always copied unchanged.
- **Texture drift locks.** At 55-60 % the texture-aware collapse moved UVs on a few large faces (a dark blotch on the
  front of the shorts, toe claws). `texture_drift.py` compares each reduced face's base colour with the source's
  colour at the same rest-pose points; `drift_lock.py` adds source faces within 3 cm of drifted faces (difference
  > 40, over 3 cm2) to the keep set (`work/lock1.npy`, 939 faces). A second lock round only moved the drift
  elsewhere and raised the error, so one round is used.
- `scripts/run_ladder.sh <label> <ratios>` reruns a ladder configuration, `scripts/build_pick.sh <tag> <label>`
  builds one step, `scripts/face_views.py` renders face/mane/torso/claw views (textured and clay; facing from the
  Jaw bone, `REA_CLIP=<clip>:<frame>`), `scripts/face_sheet.py` makes the sheets, `probe_max.py` locates the worst
  errors (thin torso and limb fur cards in Death, mane cards in Standing).

## Ladder

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 10,821 | | | |
| head set kept | 70 % | 7,573 | 7.7 / 38.5 | 0.982 | body cut too deep |
| uniform | 70 % | 7,573 | 4.4 / 25.5 | 0.992 | max only; gold smear on the neck |
| uniform | 55 % | 5,951 | 7.6 / 36.3 | 0.985 | necklace gaps, shorts blotch |
| head 60 % + necklace | 60 % | 6,491 | 7.3 / 32.3 | 0.984 | shorts blotches |
| **head 60 % + necklace + lock1** | **60 %** | **6,489** | 8.4 / 36.5 | 0.983 | **pick** |
| head 60 % + necklace + lock1 | 55 % | 5,949 | 10.7 / 42.8 | 0.978 | new shorts blotch |
| head 60 % + necklace + lock2 | 60 % | 6,489 | 11.0 / 46.6 | 0.978 | drift moves elsewhere |

No step passes the automatic limits (the fur cards collapse first), so the pick is visual, as for the goblin and
cannibal.

## Result
`export/mm6_wwf.glb` (= `mm6_wwf_lock1r60.glb`): LODs 6,489 / 3,108 / 1,020 / 240 (installed 10,821 / 5,354 /
1,797 / 498), variants carried to all 7 LOD/shadow primitives. Review sheets (rows installed, uniform 55 %,
head 60 % + necklace, pick): `review/sheet_head.png`, `review/sheet_body.png`; `review/sheet_clips.png` (installed vs
pick in Attack, Death and Running). Viewer `review/viewer/` (installed / pick per variant, every clip;
`check_viewer.mjs` 48 switches, no console errors).

## Installed (2026-10-14)

User: "approved". Previous source backed up to `work/mm6_wwf_source_pre_reduce.glb` (rollback: install that file),
`tools/install_model.py export/mm6_wwf.glb --world mm6`; `mm6_werewolf_actor_model_tiers_share_the_native_height`
passes in the `actors` suite (the suite's other failures are guard, mage, ooze and DWI cases that do not involve
this model). Lease released.

## Gait rollout — 2026-10-31

The [gait rollout package h02](../gait_rollout_20261031/h02/README.md) appended Walk2 (0.90 s, stride 1.7988), Run2 (0.69 s, 2.8999) and Sprint (0.63 s, 3.6521) to the installed
`assets_source/worlds/mm6/models/mm6_wwf.glb` (existing clips, meshes, skins and materials byte-identical; installed
with `tools/install_model.py`). Bindings for Werewolf A/B/C, applied by the rollout coordinator from
`../gait_rollout_20261031/h02/bindings.yml`: walking: Walk2, run: Run2, sprint: Sprint (the slow Mutant walk wandered at x1.7-2.0; MAW chase played Running at x2.0-2.2). Every tier passes `gait_gate.py` under Standard and MAW.
Rebuild: `../gait_rollout_20261031/h02/scripts/rebuild.sh wwf` (from the pre-gait source kept in
`../gait_rollout_20261031/h02/work/`). Any later re-export of this model, including a far-LOD repair rerun
(`../lod_repair_claude/`) or a floor fix, starts from a source without these clips unless it starts from the installed
one: re-graft them (rerun the rebuild on the new source) and keep the bindings.

## Rebuilt (2026-11-11)

Replaced by a full rebuild on the MM9 bigfoot skeleton and clips with new lean masters
([mm6_wwf_rebuild_claude](../mm6_wwf_rebuild_claude/README.md)); this project's export is the previous state.
