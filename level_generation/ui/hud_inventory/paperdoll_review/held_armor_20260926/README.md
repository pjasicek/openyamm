# Held armor derived from accepted empty-hand bases

Prepared on 2026-09-26, following the user's instruction to implement the accepted-base workflow.
**270 held-pose candidates are ready in the browser. No imagegen calls, ledger acceptance, or runtime installation.**

[Open held-weapon armor review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=held&hide_accepted=1&target=engine--icons--7item078v1.bmp).
Refresh with Ctrl+Shift+R. Choose **F6** for armor, **Space** for the next item, **Tab** for the next body type,
and **Shift+Space** to accept the displayed armor image. Switch Pose to compare empty/one-hand/two-hand.
The **Held-weapon armor to review** filter excludes accepted current images; the existing main-equipment queue
remains empty. Gloves and jewelry remain separate pending work.

## Result and approval scope

| Preparation | Images |
| --- | ---: |
| Exact file copy of the approved empty-hand base; native poses identical | 188 |
| Remove the now-hidden sleeve from the accepted base | 44 |
| Transfer only the raised arm, keeping the accepted body | 38 |
| Total | 270 |

There are **266 held images awaiting approval**: the previous 256 unreviewed images plus ten replacements of
previously approved held images. Four old held approvals still match the new candidate exactly. Two unreviewed
held images already matched their accepted empty-hand bases, so there are 264 changed files but 266 pending
approvals. The ten replacement identities are listed in [summary.json](summary.json). No acceptance is inherited
from another target/body/pose merely because its artwork was reused.

All **964 approval records, 964 exact staged files, 270 accepted empty-hand bases, and 724 placement records**
are preserved. Historical held versions remain available through the original catalog, staged files, and repair
history. The active overlay is `held_armor_20260926/review.js`; its one-time import retains newer local decisions,
notes, and offsets. Accepted-only artwork mode still uses the canonical ledger, so use candidate mode for this pass.

## Image preparation

Every source base is pinned to the approved file/hash in `acceptance_snapshot_20260926_1322`. Both poses use the
same native canvas and origin, and the same `complex:<item id>:<body type>` placement record. No item offset,
whole-image scaling, recentering, or doll artwork changed.

For changed poses, native alpha/material differences identify the right-arm area (viewer left). A solid local
mask covers the old sleeve, new sleeve, and attachment margin; it avoids the holes that caused wedges in the
earlier feasibility probes. The result starts as the accepted RGBA, with only this bounded patch replaced.
Opaque join colors are feathered inside the mask. Transparent geometry is replaced to avoid fading remnants of
the lowered sleeve. The final image copies the accepted RGBA back outside the mask, including soft alpha.

Most short sleeves simply disappear behind the torso in the native held pose. Those use alpha-only trimming
of the accepted artwork, with a smooth local native contour guide. Raised sleeves use complete retained raw-sheet
components where available, with local magenta/green decontamination. Special inspected adjustments:

- `item087v1/v2`: retain the existing held shoulder rims instead of trimming away their metal borders.
- `6chain4v1`: trim against the accepted blue yoke's attachment; a direct native cut damaged the wider restored yoke.
- `6plate1v4`: the retained held return repeated the lowered sleeve. Rotate that forearm 17 degrees at the elbow.
- `7item299v2`: restrict the transfer below the armpit, preserving the accepted shoulder/breast contour despite
  the donor torso's different proportions.

## Validation and review evidence

[validation.json](validation.json) verifies all 270 canvases and source hashes, exact outside-mask RGBA equality,
zero outside-mask alpha changes, unchanged source approvals/placements, and unchanged ledger hash. An additional
anatomical bound checks that actual edits stay on the weapon side, above the lower body, and under 20% of the
armor's visible area. All 188 unchanged-pose outputs are byte-identical copies of their approved base files.

[browser_validation.json](browser_validation.json) records an isolated-browser check of all 82 edited armor images
on their corresponding doll types, plus empty/one-hand/two-hand switching for Noble Plate on all five types.
Saved offsets apply, no image layer is missing, and pose switches retain the same armor position. The test also
checks the empty main queue, 266 held targets, exact imported decisions/placements, and preservation of newer notes.
The user's browser profile was not modified by these tests.

All 82 arm comparisons and all 82 equipped captures were inspected. The revised joins remove the obvious wedge
artifacts, detached sleeve remnants, and wrong troll forearm angle seen in the provisional splices. These remain
**review candidates**, not automatic visual approvals. Existing accepted features outside the arm region remain
exactly as approved, even where a different future restoration might improve them.

`contact/arms-01.png` through `arms-11.png` show accepted base / donor / result / original empty+held / edit mask.
`contact/equipped-01.png` through `equipped-07.png` show all edited candidates on dolls. Individual full-size
captures are in `equipped/`; [browser.png](browser.png) shows the interactive review.
The [magenta scan](magenta_scan.json) found zero suspected spill candidates; `item098v1` retains its legitimate
purple trim and is labeled as a purple-material check. No accepted material outside the arm region was recolored.

## Reproduce

From the repository root:

```sh
python3 level_generation/ui/hud_inventory/paperdoll_review/held_armor_20260926/prepare.py
python3 level_generation/ui/hud_inventory/paperdoll_review/held_armor_20260926/publish.py
python3 level_generation/ui/hud_inventory/paperdoll_review/held_armor_20260926/validate.py
```

The browser check requires the repository server on port 8899, Chrome, and a free CDP port 9246:

```sh
node level_generation/ui/hud_inventory/paperdoll_review/held_armor_20260926/test_browser.mjs
python3 level_generation/ui/hud_inventory/paperdoll_review/held_armor_20260926/validate.py
```

The second validation refreshes the equipped contact pages from the isolated browser captures. None of these
commands accept candidates or write runtime assets. `manifest.json` records exact inputs, donors, extraction,
methods, masks, output hashes, and per-image preservation checks for continuation.
