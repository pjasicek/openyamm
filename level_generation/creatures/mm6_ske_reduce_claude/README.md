# MM6 Skeleton (`ske`, Skeleton A/B/C) reduction (installed 2026-10-14)

User: "afterward do mm6_ske". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed
`assets_source/worlds/mm6/models/mm6_ske.glb` (`../mm6_ske_claude/`: 78 separate rigid bone pieces, skull set, eyes;
9,536 tris in the `Skeleton` node; the cutlass is a separate attachment, untouched). Scripts from
`mm6_wel_reduce_claude/` (piece-aware weights keep every piece 100 % on its bone, `fix_uv_seams.py`). Atlas as the
djinn: body set u < 0.5, skull set u > 0.5 (2,932 faces from 1.39 m up).

## Choice

Distances stay small at every step (max 5-14 mm), but the silhouette IoU fails from the first step: thin ribs and
finger bones shrink the outline. Picked by close-ups instead:

| candidate | triangles | close-ups |
|---|---:|---|
| uniform 62 % / 55 %, skull at 70 % on its own | 5,912 / 5,244 | skull, teeth, eyes, ribs fine; finger bones boxy and thin |
| skull and hands (1,162 faces) at 80 % on their own, 60 % overall | 5,720 | fingers fine; ribs angular, neck vertebrae and hip-joint balls pointy |
| **same, 66 % overall** | **6,292** | **picked**: ribs, hands, skull as installed; hip-joint balls and neck vertebrae slightly more faceted |

`decimate_tex.py` with `REA_PROTECT_FACES=work/protect_head_hands.npy REA_PROTECT_RATIO=0.8`, `fix_uv_seams.py`
(`UV_HEAD_Z=1.39`, 105 faces), `scripts/build_cand.sh Cand_66 h66`: `export/mm6_ske.glb`, LODs 6,292 / 3,116 /
1,061 / 417 (installed 9,542 / 4,826 / 1,685 / 500). No Meshy. Review `review/close/sheet_h66.png` (ribs, pelvis and
legs, left hand: installed / 66 %), `sheet_hands.png` (installed / uniform 62 % / 60 % with protected hands),
`sheet_parts.png` (skull), `sheet_tiers.png`. Viewer installed vs 66 % per tier, 48 loads pass.

## Installed (2026-10-14)

User: "accepted". Previous source backed up to `work/mm6_ske_source_pre_reduce.glb` (rollback: install that file with
`tools/install_model.py --world mm6`); `export/mm6_ske.glb` installed with `tools/install_model.py`. Far LOD height
1.525 m (installed 1.515 m), so the native-height check measures the same. Regressions
`mm6_skeleton_actor_model_tiers_follow_the_native_frame_scales` and `mm6_skeleton_actor_fidget_clip_plays_past_the_native_fidget`
pass. Dev assets only; `mm6.zip` and Android not repacked.

## Floor fix — 2026-10-21

`--lift-joints Death Dead --ground-death Death Dead`: the neck bends at most 7 degrees to keep the skull on the floor. Before, in world units at tier A: corpse at -4.3; dying sinks to -4.3.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_ske.glb`), written to `export/mm6_ske_floor.glb` and installed as `mm6_ske.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31)

Package [h06 of the gait rollout](../gait_rollout_20261031/h06/README.md) appended new locomotion clips (Walk2, Jog, Sprint) to
the installed `assets_source/worlds/mm6/models/mm6_ske.glb` (existing clips, meshes, skins and materials unchanged)
and installed it; the bindings are in `../gait_rollout_20261031/h06/bindings.yml`. Rebuild from the pre-gait copy:
`level_generation/creatures/gait_rollout_20261031/h06/scripts/rebuild.sh ske`. A far-LOD repair, head-bob or
reduction rerun on this model must re-graft these clips: copy the new source over
`../gait_rollout_20261031/h06/work/mm6_ske_pre_gait.glb`, rerun that rebuild and install its export.
