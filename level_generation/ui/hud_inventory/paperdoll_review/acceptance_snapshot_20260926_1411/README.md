# Accepted held armor and synchronized offsets — 2026-09-26

The user approved all held armor in the web UI and requested application of the additional offset notes.
The consistent browser capture at **12:11:20 UTC / 14:11:20 local** contains 1,225 approvals, zero flags, and
726 saved placement records. The four remaining held images already have matching canonical approvals.
All **270 held armor images** and **270 empty-hand armor images** are now accepted/staged.

The active browser overlay is `acceptance_snapshot_20260926_1411/review.js`.
[Open the review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=held&hide_accepted=1)
and refresh with **Ctrl+Shift+R**. The main-equipment, held-armor, and latest-repair queues are empty.
Eight glove images and 28 jewelry images remain unreviewed, outside this armor acceptance.
Final ledger acceptance and runtime installation remain deferred.

## Applied notes

Twelve held-armor approvals explicitly request the same corrected offset for the corresponding empty-hand
variant. The two poses already share one `complex:<item id>:<body type>` placement record. The latest values
were therefore retained exactly, and the twelve paired empty-hand approval snapshots were updated to confirm
the requested placement. Their image hashes, original notes, and all other approval fields remain unchanged.

| Body type | Held image | New delta from native table (x, y) | Proposed table point (x, y) |
| --- | --- | --- | --- |
| Female | item098v2 | -1, -2 | 47, 80 |
| Female | 7item069v2 | 0, 3 | 60, 96 |
| Female | 7item071v2 | 1, 2 | 61, 98 |
| Female | 7item073v2 | 2, 0 | 61, 97 |
| Female | 6chain2v2 | 1, 3 | 60, 100 |
| Female | 6chain3v2 | 1, 1 | 61, 98 |
| Female | 6chain4v2 | -1, 3 | 57, 94 |
| Female | 6plate1v2 | -4, -2 | 39, 89 |
| Minotaur | 6plate1v3 | -4, 0 | 27, 104 |
| Minotaur | 6plate2v3 | -4, 0 | 27, 104 |
| Troll | 6plate3v4 | -1, -1 | -1, 87 |
| Troll | 6plate4v4 | -1, -2 | -1, 86 |

These are **native game pixels**, not doubled display pixels. Each change also applies to the corresponding
`a` image. No cross-body-type adjustment or image regeneration was performed.

[offset_sync.json](offset_sync.json) retains each exact instruction, source approval timestamp, old/new deltas,
paired target, and final point. [armor_offset_updates.csv](armor_offset_updates.csv) provides the twelve changes.
[placement_proposals.csv](placement_proposals.csv) and [placements.json](placements.json) retain all 726 saved
records, including the two inactive legacy proposals; active runtime tables are unchanged.

## Preservation and evidence

- `browser_state.original.json`: exact captured review keys from an isolated copy of Chrome Local Storage.
  The user's live profile was not opened or changed by the capture/checks.
- `previous_review.js`: exact previous active overlay. Three earlier explicit chat approvals have newer timestamps
  than their browser copies, so these authoritative records were retained during the merge.
- `review.original.json`: merged input before the twelve authorized placement confirmations.
- `review.applied.json`: resulting review, including scoped `placement_sync` provenance on the twelve paired approvals.
- `stage_manifest.json`: all **1,225** approved image hashes and staged paths. **266 newly approved/reapproved held
  files** are copied to this snapshot's `staged-accepted/`; the other 959 continue using their existing staged files.
  Every one of the previous 964 staged files remains unchanged.
- `completion_audit.json`: resolver-based totals by equipment group, including 266 staged and four canonical held
  approvals, 270 staged empty-hand approvals, and the remaining gloves/jewelry.
- `validation.json`: exact image hashes, zero remaining main/held targets, preserved offsets, unchanged ledger.
- `browser_validation.json`: all twelve pairs verified in empty/one-hand/two-hand poses at the requested coordinates
  with valid approvals; all three review queues empty; newer local notes and offsets survive importing this snapshot.
- `browser.png`: the updated browser state after these checks.

The ledger hash remains `3bf9a7ca23de974440dcc24770532f9dbad4c097bd26699fb0f365c1849c7346`.
No candidate artwork, original asset, runtime table, or canonical acceptance changed.

To reproduce the snapshot from its frozen feedback and inspect the browser on port 8899:

```sh
python3 level_generation/ui/hud_inventory/paperdoll_review/acceptance_snapshot_20260926_1411/process.py
node level_generation/ui/hud_inventory/paperdoll_review/acceptance_snapshot_20260926_1411/test_browser.mjs
```

The staging script verifies its frozen input hashes and accepts no unreviewed image. Further artwork or placement
changes should produce a new review snapshot so this exact approval record remains available.
