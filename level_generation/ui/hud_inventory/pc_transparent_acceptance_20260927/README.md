# Accepted transparent PC portraits — 2026-09-27

All **4,032 portraits across 72 active PC families** are accepted and installed under the user's explicit
instruction to replace the accepted solution and deploy it. Every runtime PNG is an exact copy of the aligned
118×158 RGBA export approved in the browser. Publication applies no extra scaling, cropping, alpha edits or offset.

[Open the accepted preview on port 9100](http://127.0.0.1:9100/level_generation/ui/hud_inventory/pc_transparent_regen_20260927/index.html).
Selection rings, center guides, height/contact measurements and global preview offsets remain available.
The installed exports use the default global offset `[0, 0]`; subsequent slider changes affect previews/downloads.

## Accepted revision and runtime files

- [accepted.json](accepted.json) records all 4,032 approved hashes, prior revisions, reviewed exports and destinations.
- `accepted/engine/icons_x2/` contains the immutable accepted PNGs. Their runtime destination is
  `assets_dev/engine/icons_x2/`, the repository's authoritative spelling of the requested x2 icon folder.
- [authority.json](authority.json) records the exact user approval, approved browser-manifest hash and generation evidence.
- `receipts/` contains per-portrait records, including family, frame and accepted identity-seed hash.
- [../accepted_icons.json](../accepted_icons.json) and `../checkpoint/state.json` select these as the current PC solution.
- [installed.json](installed.json) records deployment against the full 9,920-icon accepted index.
- [validation.json](validation.json) verifies runtime equality, transparency, canvas sizes, preserved prior artwork
  and unchanged unrelated index/ledger entries.
- `review_before/`, `previous_accepted_index.json` and `checkpoint.before.json` preserve the approval and earlier state.

All filenames are lowercase and installed PNG permissions are 0644. Old accepted exports and archived native
originals are preserved. The 5,888 unrelated accepted icons retain their prior records and pixels. Release ZIP
packaging is separate from this development-asset installation.

The accepted set includes the user-requested lighter injury states for `7pc02`, `girld` and `maled`.
The reserved `pc30` has no source portraits; four `archived_unused` families remain outside the active slice,
as recorded in the [scope receipt](review_before/scope_audit.json).

## Provenance and validation

The [generation workspace](../pc_transparent_regen_20260927/README.md) retains every imagegen master, exact prompt,
reference sheet, per-frame extraction report and comparison. Imagegen supplies the final alpha; deterministic
placement matches native head height and lower contact before downsampling to the native canvas at 2× resolution.
The accepted PNGs preserve those reviewed pixels byte for byte.

The [native HUD capture](runtime.png) confirms the installed portrait fits the selection ring over the basebar.
[Runtime check](runtime_check.json) records successful isolated MM6 launches using the normal OpenGL build and
the NVIDIA GeForce RTX 3060 Ti. This visual check covers the displayed portrait; the full asset audit covers
all 4,032 installed files. The accepted preview's browser checks also pass for all 72 family galleries.

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/pc_transparent_acceptance_20260927/validate.py
python3 -B level_generation/ui/hud_inventory/pc_transparent_regen_20260927/audit.py
```

For redeployment, use `deploy_icons.py --install`, which always follows the current accepted index.
`publish.py --apply` records this specific, hash-pinned approval; it does not regenerate portraits or replay
superseded art over a newer revision.
