# Latest acceptance snapshot — 2026-09-26, 11:20 local

[Open remaining main equipment](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=main&hide_accepted=1).
Refresh an existing tab with Ctrl+Shift+R. This queue excludes armor with a weapon held, gloves and jewelry.

Source: `/home/pjasicek/Downloads/openyamm-paperdoll-review (2).json`, exported **09:20:37.965 UTC / 11:20 local**.
The browser has no debugging port available, so this audit uses the newest exported snapshot, not an unobserved
live tab. The import preserves any newer local records. Automated browser checks use a separate temporary profile.

The export contains **921 decisions: 880 approvals and 41 flags**, plus **721 placement records**.
All records, notes and placements are preserved exactly in [review.original.json](review.original.json).
There are 54 changed approval records since the preceding snapshot. Their 54 exact images are copied into
`staged-accepted/`; the other approved images reference existing immutable staged copies.
[stage_manifest.json](stage_manifest.json) verifies all **880** approved files by hash.
The checkpoint/ledger and runtime files are unchanged. This is staging, not final acceptance into the ledger.

## Completion outside the requested exclusions

| Group | Accepted/staged current images | Remaining | Total |
| --- | ---: | ---: | ---: |
| Melee weapons | 244 | 0 | 244 |
| Bows | 35 | 0 | 35 |
| Shields | 38 | 0 | 38 |
| Wands | 15 | 0 | 15 |
| Armor, empty hands | 224 | 46 | 270 |
| Helmets | 143 | 17 | 160 |
| Boots | 69 | 7 | 76 |
| Belts | 88 | 2 | 90 |
| Cloaks | 34 | 38 | 72 |

**110** images remain outside the exclusions: **67 repaired replacements awaiting approval**, and **43 without
a review decision for that target**. The 38 cloak gaps are female/dwarf variants. Approval of one body variant
does not approve another. Identical source BMPs alone do not establish approval of different generated returns.

The audit checks the selected candidate hash, source hash, saved placement and any earlier repair history.
An old approval/flag remains archived but does not approve its replacement. The 41 flags all refer to earlier
images with replacement candidates available. Twenty-six older approvals similarly await their changed repairs.
There are no additional approvals invalidated solely by a changed placement in this export.

The scope follows the five equipment body types and their slot restrictions. It also includes the legacy lowercase
`armor`/`cloak` table rows as manual previews, since these items are already part of the user's review slice.
Four of the 46 empty-hand armor gaps belong to those legacy manual-preview items. Unsupported body-type slots
and unused orphan variants are outside this completion count. Gloves/jewelry and held-weapon armor are reported
separately in the audit, but intentionally excluded from the remaining-main-equipment queue.

The **Latest feedback repairs** filter is only the most recent repair batch, now **2 remaining**:
`7item074v1a` and `item110v5`. It is not the full completion queue.

## Evidence and continuation

- [completion_audit.json](completion_audit.json): groups, per-image status, body types, item associations and notes.
- [remaining_main_equipment.csv](remaining_main_equipment.csv): all 110 remaining targets with direct browser links.
- [placements.json](placements.json) and [placement_proposals.csv](placement_proposals.csv): all 721 exported records;
  two earlier global records remain inactive. No placement record was rewritten by this snapshot.
- [validation.json](validation.json): all staged hashes, immutable export hash and unchanged checkpoint hash.
- [browser_validation.json](browser_validation.json): fresh-load counts, exact 110-target queue, old-profile import,
  preserved newer local note and exact placement records.

`process.py` rebuilds this snapshot from its frozen input and `previous_review.js`; it does not regenerate images,
approve pending candidates or modify the ledger. The active page loads this snapshot's `review.js`.
