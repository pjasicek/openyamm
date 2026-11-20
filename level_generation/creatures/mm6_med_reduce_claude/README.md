# MM6 Medusa (`med`, BMedusa A/B/C) reduction (2026-10-14)

User: "Do medusa now". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed
`assets_source/worlds/mm6/models/mm6_med.glb` (14,900 tris, one merged material, three variants, four influences at
full detail; from `../mm6_med_claude/`). No attachments. Started with
`REA_PROTECT_HEAD=1 ../reduce_installed.sh med Body "MM6 Medusa"`; weld 14,218 -> 775 open edges; limits for the
2.245 m height: p99 6.74 mm, max 33.68 mm. No Meshy credits.

## Medusa-specific changes
- **Painted patterns kept.** The first auto-pick (r55, head kept) passed the limits, but the gold trim on the bodice
  straps turned into zigzags and the white belly-plate bands went wavy: thin painted lines run across long triangles,
  and any collapse bends them. Faces were classified from the runtime maps (16 samples per face):
  bodice = region mask red > 0.2 (783 faces), belly plates = region mask green > 0.2 (522), gold = base colour hue
  and saturation (1,377 outside head and bodice). Head (`B_Head` weights, 2,947), bodice and belly are kept exactly
  (`work/keep3.npy`, 4,252 faces, `REA_KEEP_FACES`); gold is reduced on its own at 70 % (`work/gold3.npy`,
  `REA_PROTECT_FACES`, `REA_PROTECT_RATIO=0.7`). Reducing the belly at 70 % still bent the bands.
- The hair snakes (`Crown_*` chains) are reduced with the body; they look the same at 65 % and get lumpier at 60 %.
- Scripts from the werewolf/chain fighter projects (`run_ladder.sh`, `build_pick.sh`, `face_views.py` with a
  full-body `whole` shot and the facing from `Socket_Gaze`, `texture_drift.py`, `probe_max.py`).

## Ladder

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 14,900 | | | |
| head kept | 55 % | 8,194 | 5.3 / 18.0 | 0.984 | auto pass; strap trim zigzag, belly bands wavy |
| head kept | 45 % | 6,704 | 8.5 / 26.6 | 0.976 | worse |
| head + bodice kept, gold + belly 70 % | 60 % | 8,940 | 6.6 / 23.8 | 0.985 | belly bands still wavy |
| **head + bodice + belly kept, gold 70 %** | **65 %** | **9,684** | 5.0 / 22.7 | 0.991 | **pick** (auto pass) |
| head + bodice + belly kept, gold 70 % | 60 % | 8,938 | 7.3 / 27.2 | 0.984 | hair snakes lumpier |

Texture drift of the pick: 6 faces over 40, 4.2 cm2 in total (invisible).

## Result
`export/mm6_med.glb` (= `mm6_med_trim3r65.glb`): LODs 9,684 / 4,839 / 1,734 / 572 (installed 14,900 / 7,449 /
2,672 / 883), variants carried to all 7 LOD/shadow primitives; sockets and clips unchanged.
Review: `review/sheet_head.png` (+ `_clay`; rows installed, head-kept r55, r45), `review/sheet_head2.png`,
`review/sheet_trim2.png`, `review/sheet_trim3.png` (installed, pick, r60), `review/sheet_clips.png` (installed vs pick
in Attack, Death and Walk). Viewer `review/viewer/` (installed / pick per variant, every clip; `check_viewer.mjs`
54 switches, no console errors).

## Installed (2026-10-14)

User: "accepted". Previous source backed up to `work/mm6_med_source_pre_reduce.glb` (rollback: install that file),
`tools/install_model.py export/mm6_med.glb --world mm6`; `mm6_medusa_actor_model_tiers_follow_sprite_scales` passes in
the `actors` suite (its other failures are guard, mage, ooze, water elemental and DWI cases). Lease released.
