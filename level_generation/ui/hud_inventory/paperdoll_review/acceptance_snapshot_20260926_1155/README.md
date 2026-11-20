# Acceptance snapshot — 2026-09-26, 11:55 local

[Open remaining main equipment](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=main&hide_accepted=1).
Refresh an existing tab with Ctrl+Shift+R. Newer browser decisions are preserved by the one-time import.

The latest Downloads export was still from 11:20. This snapshot instead captures the newer persisted browser
state at **09:55:39 UTC / 11:55 local**, including decisions through **11:52:55 local**. A stable copy of Chrome's
Local Storage was opened in an isolated temporary browser; only the paperdoll keys for `http://127.0.0.1:8899`
were read. The live profile was not changed. Exact strings are retained in
[browser_state.original.json](browser_state.original.json), and the importable records are in
[review.original.json](review.original.json).

**926 decisions: 923 approvals and 3 flags. All 724 placement records are preserved exactly.**
Since the 11:20 snapshot, 69 images have new explicit approvals and three flags have been updated.
The 69 exact approved images are copied to `staged-accepted/`; other approvals retain their immutable previous
staged paths. All 923 staged hashes are verified in [validation.json](validation.json).
Thirteen placement records are new or changed; all original records and notes remain in the earlier snapshot.
No ledger acceptance or runtime installation has occurred.

## Remaining outside held-weapon armor, gloves and jewelry

| Group | Accepted/staged current images | Remaining | Total |
| --- | ---: | ---: | ---: |
| Melee weapons | 244 | 0 | 244 |
| Bows | 35 | 0 | 35 |
| Shields | 38 | 0 | 38 |
| Wands | 15 | 0 | 15 |
| Armor, empty hands | 268 | 2 | 270 |
| Helmets | 159 | 1 | 160 |
| Boots | 76 | 0 | 76 |
| Belts | 90 | 0 | 90 |
| Cloaks | 34 | 38 | 72 |

**41 images remain:** 38 female/dwarf cloak variants with no saved decision, and these three current flags:

- `7item235v2a`: visible cuff on the character's left sleeve.
- `7item236v2a`: black contours still visible at both sleeve openings; otherwise good.
- `6hat1v5`: hat is not visible.

All 26 formerly staged originals with changed replacement art now have explicit approvals for their replacements.
The latest 51-image repair batch is fully approved. There are no stale approvals among current main equipment.
The deliberately excluded categories still contain 256 unreviewed held-weapon armor variants, 8 gloves and
28 jewelry images. Existing accepted images in those categories remain accepted.

## Retained evidence

- [stage_manifest.json](stage_manifest.json): exact reviewed decisions and immutable staged image paths/hashes.
- [completion_audit.json](completion_audit.json): per-image status and equipment/body-type associations.
- [remaining_main_equipment.csv](remaining_main_equipment.csv): all 41 targets with direct browser links.
- [placements.json](placements.json) and [placement_proposals.csv](placement_proposals.csv): all 724 records,
  including the two preserved inactive legacy keys.
- [validation.json](validation.json): source/staged hashes and unchanged canonical checkpoint hash.
- [browser_validation.json](browser_validation.json): exact 41-target queue, 926 decisions, 724 placements,
  and upgrade from the previous snapshot preserving newer local edits; checked in an isolated browser profile.

`process.py` reconstructs staging and the review overlay from frozen inputs. It does not alter artwork or the ledger.
