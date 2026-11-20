# MM6 Titan (`ttn1`, BTitan A/B/C: Titan / Noble Titan / Supreme Titan) reduction (2026-10-14)

User: "do titan now" (triangle-reduction playbook). No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_ttn.glb` (10,176 tris, one merged body+head atlas material, three variants, Meshy rig without
finger bones, palm sockets; project `../mm6_ttn1_claude/`). Scripts copied from `../mm6_fgt_reduce_claude/`.
No Meshy credits. Limits for the 1.577 m height: p99 4.73 mm, max 23.66 mm.

## Parts

Connected components of the welded mesh: main shell 4,117 (body skin, armour, face/neck 1,648 on the head set, hands
762 / 765), legs 1,906, helmet 710 + cheek guards 332, crest 362, eyes 51 / 45, pauldrons 258 / 256, bracers 140,
arm bands 122, belt 165, jewel 81, buckle ring 50, 28 skirt plates (21-50 each). Gold trims are painted (region mask
channel 1) and touch 3,102 faces (30 %).

## Ladder

| config | triangles | p99 / max mm | finding |
|---|---:|---|---|
| t1: trims as their own group at 70 % | 7,378 | 7.8 / 22.7 | fails; trim group alone at 70 % already p99 6.4 (thin strips with fixed borders) |
| t2: trims in the main cut | 7,378 | 4.5 / 42.8 | 43-49 mm at the back in Death: plates took the body's weights |
| t3: + per-part weights (`REA_WEIGHTS=component`), crest 70 % | 7,450 / 7,000 | 3.7 / 17.9, 4.5 / 28.5 | weights fixed; jewel blob, helmet cheek lump and gold smear at 60 % |
| t6: + jewel and arm bands kept, helmet 75 % | 7,520 | 3.8 / 17.9 | 28.5 mm armpit point returns at any lower step |
| t9: + one drift lock (9 faces > 40), helmet 85 %, 4 cm patch at the armpit point (both sides) | 7,512 | 4.4 / 18.5 | helmet side still more gold than the source |
| **t10: t9 with the helmet kept** | **7,666** | 4.4 / 18.5, IoU 0.990, SSIM 0.989 | **pick** |

Pick `t10r75` (`work/keep_t10.npy`, `work/groups_t2.npy`, ratios hands 0.45 / crest 0.7, shells 0.6): face/neck,
eyes, helmet, cheek guards, jewel, buckle ring, arm bands, small plates, drift-lock and armpit patches kept exactly.
Texture drift after the lock: 5 faces above 40 (back of the left calf, a bracer), p99 14.6; no second round (playbook).

## Result (installed 2026-10-14, user accepted)

`export/mm6_ttn.glb` (= `mm6_ttn_t10r75.glb`): LODs 7,666 / 3,832 / 1,379 / 450 (installed 10,176 / 5,087 / 1,831 /
602), shadow LODs rebuilt, variants on every primitive, palm sockets and all ten clips unchanged.
Review: `review/faces/t10.png` (rows installed, t9r73, pick: face, three-quarter, side, back, belt),
`review/faces/t10_clay.png` (installed, pick), `review/faces/t6*.png` and `t9.png` (earlier steps), `review/ladder_sheet.png`.
Viewer `review/viewer/` (installed vs pick per variant; `check_viewer.mjs` 60 switches, no console errors).
Other candidates are in `work/candidates/`.

Installed with `tools/install_model.py export/mm6_ttn.glb --world mm6`. The `actors` suite's
`mm6_titan_actor_model_tiers_share_the_native_height` passes; the other failures are the guard, mage, ooze and DWI
cases unrelated to this model. Rollback (install this): `work/mm6_ttn_source_pre_reduce.glb`.

## Floor fix — 2026-10-21

`--ground-loop Walking`. Before, in world units at tier A: walking lifts every foot by +12.4.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_ttn.glb`), written to `export/mm6_ttn_floor.glb` and installed as `mm6_ttn.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Heavy walk — 2026-10-21

User: walk rework ("i guess only walk"). The Titan wanders at 0.60 and chases at 1.21 model units/s
(`claude_shared/postprocess/gait_gate.py`), but its only walk covers 1.255 per 1.04 s loop (1.20 u/s), so wandering
played it at 0.50x (slow motion). New clip **`WalkHeavy`** (1.50 s, stride 0.902, authored 0.60 u/s), derived from
the installed `Walking` without Blender or Meshy by `scripts/derive_walk.py` (settings `scripts/gait_ttn.json`):
ankle paths' forward travel x0.72 about each foot's mean (as `run_fit.py` scales a run), the cycle stretched
uniformly to 1.5 s (a giant's slower leg swing), legs re-solved by two-bone IK (knee in the source knee's direction,
carried onto the new hip-ankle line), feet 3 cm wider each, swing lift x0.9, heel-strike/toe-off pitch x0.75, pelvis
sway x1.4, a 1 cm settle after each heel strike, 4 deg forward lean taken back at neck and head, arm swing x0.6 and
the upper arms 4 deg out (the hands clear the swaying hips). Each foot's lowest vertex is put back at the source's
height (planted on the floor), then `floor_fix.py --ground-loop WalkHeavy` (6 keys, at most 4.6 mm). Every other clip
is unchanged; the old `Walking` becomes the run (it fits the chase at 1.0x).

- Gate: `gait_gate.py --world mm6 --model mm6_ttn.glb --candidate export/mm6_ttn_gait.glb --set walking=WalkHeavy
  --set run=Walking --set stride_length=0.902 --set run_stride_length=1.255`: strides trusted (0.902 / feet 0.906,
  1.255 / 1.260), wander WalkHeavy x1.00 and chase Walking x1.00 on all three tiers, floor ok. PASSED.
- `scripts/gait_probe.py`: knee flexion 22-79 deg (never backward), loop seam 0, joints slower than the source walk.
  `scripts/gait_arms.py` (arm and hand gate): wrist <= 14 deg, forearm/hand >= 3.5 cm from torso, pelvis and thighs
  (old walk 1.1 cm). `check_winding.py` 0 inverted.
- Review: `review/gait/v5.png` (clay sheet, `scripts/gait_sheet.py`: old vs heavy, side/three-quarter/front),
  `review/playback/` (viewer recordings of WalkHeavy and Walking at 1x and 0.5x, `tools/run_creature_review.py
  playback`), `review/gait/playback_sheet.png`. The viewer manifest now shows the gait export (`mm6_ttn_*_gait.glb`);
  the reduction review's manifest is kept as `review/viewer/manifest_reduce.json`.
- Installed: `tools/install_model.py export/mm6_ttn_gait.glb --world mm6 --name mm6_ttn.glb`. The `actors.yml`
  binding (walking WalkHeavy, run Walking, strides 0.902 / 1.255) is left to the coordinating agent; until then the
  game plays the unchanged Walking/Running. Rollback: install `export/mm6_ttn_floor.glb` the same way.
- Rebuild: `derive_walk.py export/mm6_ttn_floor.glb work/gait/mm6_ttn_gait_v6.glb scripts/gait_ttn.json`, then
  `floor_fix.py work/gait/mm6_ttn_gait_v6.glb export/mm6_ttn_gait.glb --ground-loop WalkHeavy`.

## Melee plays Cast (user review 2026-10-21)

User: "for the mm6 titan use cast animation for both attack and cast (remove his current attack anim)". The hook
`Attack` clip was removed from the installed export with `../claude_shared/drop_clips.py export/mm6_ttn_gait.glb
export/mm6_ttn_noattack.glb --clip Attack` (also dropping two orphan accessors; every other clip is unchanged), which
was installed with `--name mm6_ttn.glb`. `actors.yml` binds `attack_melee: Cast` for BTitan A/B/C with its impact at
the push (0.87 s, the cast's), without the cast's palm glow. Rollback: `export/mm6_ttn_gait.glb`.

## Five-finger hands and the Cast recovery (2026-11-11)

Rebuild stream of the MM6-MM8 audit: grafted MPFB hands with 15 finger bones per side, finger keys in every clip
(fists, the open casting hands on the push), and Cast's arms eased to Standing from 1.55 s (the left hand no longer
crosses the belly). Installed from [mm6_ttn_rebuild_claude](../mm6_ttn_rebuild_claude/README.md); the export here is
now the previous state (rollback: that project's `work/before_rebuild/mm6_ttn.glb`).
