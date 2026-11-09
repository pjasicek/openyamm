# Cloak approvals and three repairs — 2026-09-26

[Review the three repairs](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=latest&hide_accepted=1).
Refresh an existing tab with Ctrl+Shift+R. Both Latest feedback repairs and Remaining main equipment contain
these same three images; held-weapon armor, gloves and jewelry remain deferred.

## Preserved approvals and placements

The latest browser state was captured at **10:14:41 UTC / 12:14 local**, including decisions through 12:13:48.
Only paperdoll keys at `http://127.0.0.1:8899` were read from an isolated, stable copy of Chrome Local Storage.
The live browser profile was not modified. The exact strings remain in
[browser_state.original.json](browser_state.original.json), with importable records in
[review.original.json](review.original.json).

**All 72 cloak variants are accounted for: 60 explicitly approved/staged here, plus 12 existing ledger approvals.**
The 38 newest cloak images are copied to `staged-accepted/`. All **961 current approvals** have hash-verified
staged copies; historical approved images remain in earlier immutable snapshots. All **724 placement records**
are retained exactly, including inactive legacy records and all manual adjustments. No ledger acceptance or
runtime installation has occurred. The three flags and their exact notes remain preserved against the reviewed
images; the new replacements await the user's approval.

## Repairs

- **7item235v2a — Governor's Armor, female:** removed the rear cuff arc at the character's left sleeve.
- **7item236v2a — Yoruba, female:** removed the black interior/back rim at both sleeve ends.
- **6hat1v5 — Cloth Hat, dwarf:** recovered the complete hat and feather from retained sheet S002. The former
  crop was effectively empty (maximum alpha 1), which caused the invisible hat. The recovered art is fitted to
  its original bounds in the original 76×74 canvas. Genuine green cloth color is retained.

The sleeve masks were edited with the built-in imagegen tool. Only their alpha within three small opening
regions is applied to the previously reviewed armor. Every pixel outside those regions is identical, and
visible RGB is unchanged: the generated torso/material changes are discarded. The armor canvases remain
160×494 and 212×510. No placement is changed: the female armors retain **[+1, 0]** and **[-21, -8]**;
the dwarf hat retains its default **[0, 0]** adjustment.

Exact prompts and retained output masters:

- [Governor's Armor prompt](generated/7item235v2a-prompt.txt) and [master](generated/7item235v2a-raw.png).
- [Yoruba prompt](generated/7item236v2a-prompt.txt) and [master](generated/7item236v2a-raw.png).
- [Recovered hat master](generated/6hat1v5-recovered-master.png); no new hat generation was required.

## Validation and continuation

- [repairs.json](repairs.json): exact source/old/new hashes, edit regions, operations and compatible offset history.
- [stage_manifest.json](stage_manifest.json): all exact decisions and staged paths.
- [completion_audit.json](completion_audit.json): only three replacements pending outside the deferred groups.
- [placements.json](placements.json) and [placement_proposals.csv](placement_proposals.csv): all saved offsets.
- [validation.json](validation.json): 961 staged hashes verified, 724 placements retained, canonical ledger unchanged.
- [magenta_scan.json](magenta_scan.json): all three repaired images report no spill detected.
- [browser_validation.json](browser_validation.json): exact three-item queue, all 964 decisions and 724
  placements retained, and upgrade preserving newer local edits; verified in an isolated browser profile.
- `before/` and `after/`: each image equipped on its review doll at the saved offset. The rear sleeve contours
  are absent and the recovered hat is visible. Original comparison canvases are retained alongside them.

`repair_assets.py` rebuilds only these three candidates from retained generated masks/raw hat artwork.
`process.py` stages the frozen browser approvals and builds the active overlay, preserving old repair history.
No other artwork is regenerated or reapproved by this repair pass.
