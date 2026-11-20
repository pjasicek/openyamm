# MM6 Sea Serpent (`seas`, SeaSerpent A/B/C: Sea Serpent / Sea Monster / Sea Terror) reduction (2026-10-14)

User: "do sea serpent now" (triangle-reduction playbook). No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_seas.glb` (body `Seas` 8,000 tris, one texture set, three variants, 17-bone spine rig; foam
collar `Foam` 384 tris on its own node, left untouched; project `../mm6_seas_claude/`). Scripts copied from
`../mm6_ttn_reduce_claude/`. No Meshy credits. Limits for the 1.039 m height: p99 3.12 mm, max 15.6 mm.

The body was already reduced once, 20,886 -> 8,000, by the original bent-pose reduction + bake, so it has little
slack. It is one closed surface (13 open edges after welding): no separate pieces to keep.

| config | triangles | p99 / max mm | IoU | |
|---|---:|---|---|---|
| source | 8,000 | | | |
| uniform 70 % | 5,600 | 3.7 / 12.8 | 0.991 | fails p99 (also with the head at 70 % on its own) |
| uniform 80 % | 6,400 | 2.6 / 6.4 | 0.994 | pass |
| uniform 75 % | 6,000 | 3.2 / 6.7 | 0.993 | fails p99 |
| **head (Head-bone faces, 1,916) at 90 %, body 75 %** | **6,286** | 2.9 / 6.4 | 0.993 | **pick** |
| head 90 %, body 70 % | 5,982 | 3.5 / 7.1 | 0.992 | fails p99 |

Per-part weights (`REA_WEIGHTS=component`) and the nearest-face transfer give the same result on this one-piece body;
the pick uses the nearest-face transfer. Close-ups (`scripts/seas_views.py`: forward = Spine_14 -> Head):
`review/faces/c1.png` + `c1_clay.png` (head front, side, three-quarter, open mouth from below; rows installed,
uniform 80 %, pick) and `c2.png` (back spikes and belly segments, textured and clay): tusks, crest spikes, mouth teeth
and back spikes unchanged. Texture drift: one face above 40 (0.1 cm2), p99 12.5.

## New Attack (user request 2026-10-14)

"redo the attack animation a bit so that it isnt just symmetrical y axis smash, but like tilt a bit on windup and
release to the other side forward". `../mm6_seas_claude/scripts/anim_seas.py` `attack()` keeps its pitch and timing
and adds side lean and yaw: the windup coils back leaning and turning toward +X (head turned slightly against it),
the strike sweeps forward and down across to -X, then recovers. Floor rule holds (lowest joint 0.0 cm above its
radius), head reach 0.45 m (was 0.46). The master `../mm6_seas_claude/work/anim_v1.blend` was re-keyed and saved
(previous: `work/anim_v1_pre_attack2.blend` there).
Into the reduced GLB without rebuilding the chain: `scripts/attack_donor.py` re-keys the clip on the master and
exports the rig with export_glb.py's glTF settings; `scripts/transplant_clip.py` replaces the clip's channel data by
node name. Validation: the donor of the unchanged clip matched the installed Attack and Standing exactly (0.0); after
the transplant every other clip is byte-identical. Frames: `review/attack/compare_front.png` and `compare_top.png`
(rows old, new; frames 0, 5, 8, 10, 12, 14, 17, 21, 27).

## Result (installed 2026-10-14, user accepted)

`export/mm6_seas.glb` (= `mm6_seas_attack2.glb`: `mm6_seas_h90r78.glb` with the new Attack): body LODs 6,286 / 3,142 / 1,130 / 376 (installed 8,000 / 4,000 /
1,440 / 480), shadow LODs rebuilt, variants on every primitive, foam collar and the other six clips unchanged.
Viewer `review/viewer/` (installed vs pick per variant; `check_viewer.mjs` 42 switches, no console errors).
The uniform 80 % candidate and the old-Attack pick are in `work/candidates/`.

Installed with `tools/install_model.py export/mm6_seas.glb --world mm6`. The `actors` suite's
`mm6_seas_actor_model_tiers_follow_sprite_scales` passed in all three runs; the third run's only failures were the
guard, mage, ooze and DWI cases unrelated to this model. Two other runs were intermittent and did not reproduce:
`actor_crowding_outdoor_doorway` failed once (synthetic crowding map, does not load this model), and one run
segfaulted in `mm6_drake_and_dragon_actor_model_burn_death` on `oute3` (another session installed `mm6_fmp.glb` in
between). Rollback (install this; it has the old Attack): `work/mm6_seas_source_pre_reduce.glb`.
