# Equipment feedback repair round 2 — 2026-09-26

[Open the latest 51 replacements](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=latest&hide_accepted=1).
Reload an existing tab with Ctrl+Shift+R. The server is on port **8899**.
Use **Review → Latest feedback repairs** for this round, or **All repairs to re-review** to include earlier
replacements still awaiting approval. **Hide accepted / staged** also filters item cycling and the item selectors.
Changed artwork remains visible until its new hash is approved.

The input is `/home/pjasicek/Downloads/openyamm-paperdoll-review (1).json`, exported at
**2026-09-26 07:54:45 UTC**. It contains **916 decisions: 838 approve and 78 flag**, and **714 placement records**.
The original bytes are retained in [review.original.json](review.original.json), with hashes in [baseline.json](baseline.json).
There are **38 new or revised flags** compared with the first pass. Forty earlier flags remain associated with
their previous repairs; those have not been silently accepted or regenerated again.

## Repairs

- Reconstructed 29 distinct weapon/wand designs from native references in four retained imagegen sheets.
  Replaced enlarged pixel edges with continuous blade edges and material shading, removed magenta/green backing,
  neutralized the unwanted purple blade tint, and made `item021` slimmer. Chips on cheap blades are irregular damage.
- Reused the same file for exact native-identical sprites. Each target still has its own review record.
- Recovered `sshield1`'s complete top from the original raw master, restored `7item074v1a`'s dark neckline V,
  and cleaned the green/magenta contour of `item110v1` and its identical dwarf variant.
- The note-free `7item026` flag referred to the old extraction. Its existing slimmer-handle/contour repair was
  inspected and retained as the replacement; no additional defect was invented from an empty note.
- The approval crop audit added ten replacements: `item022`, `item023`, `lshield2`, `item058`, `item059`,
  `item336`, `7item042`, `bow1`, `bow2`, and `bow3`. These recover complete pommels, the shield rim, and bowstrings.

This yields **51 target replacements**: the 38 new flags, three matching-sprite variants, and ten additional crop
repairs. All are review candidates. [repairs.json](repairs.json) records each source, operation, old/new hash and alias.
The combined browser overlay retains 453 earlier repairs and 38 superseded choices for comparison.

All final images retain the original canvas at exactly 2×. Generated masters have a measured subject sampling
of at least **3.081× native**. They are exported using premultiplied-alpha Lanczos without imposing a native pixel
staircase mask. On the fourth sheet the row split was moved into the actual empty band to include complete pommels.
These are fitted review candidates, not a guarantee of identical internal handle geometry; inspect their grip again.

Restored browser canvases and inspector previews now use smooth CSS scaling. The native comparison retains
nearest-neighbor scaling. This does not change any image pixels or source equipment coordinates.

## Decisions and offsets

All **838 exact approved files** are copied into `staged-accepted/`; [stage_manifest.json](stage_manifest.json)
retains their complete original decisions. Corrections do not overwrite these historical approvals.
Changed replacements need approval again. Twenty-five approvals from before round 1 still await their earlier
repairs; those remain pending rather than reverting to their old cutouts.

[placements.json](placements.json) and [placement_proposals.csv](placement_proposals.csv) preserve all 714 exported
records unchanged. Two legacy global records remain inactive. Existing user offsets carry through the recorded
candidate history, subject to the original source hash and placement-table checks.

The newer `wand4` adjustment on item **1752**, male main hand, is `[1, -1]`. Four previously inherited records for
items **1753–1756** still had `[2, -1]`; those now inherit `[1, -1]`. No manually authored record was changed.
See [inherited_placement_updates.json](inherited_placement_updates.json) for before/donor/after values.
The browser uses [placements.effective.json](placements.effective.json); the matching proposed table export is
[placement_proposals.effective.csv](placement_proposals.effective.csv).

The browser imports this round once, backs up existing storage first, and preserves newer local edits by timestamp.
Clear/Reset is not undone on subsequent reloads. Browser tests use an isolated profile and do not touch the user's tab.

## Checks and retained evidence

- [validation.json](validation.json): export and all staged hashes, 916 decisions, 714 original placements,
  explicit inherited changes, exact 2× dimensions, alpha, alias identity, and unchanged checkpoint hash.
- [magenta_scan.json](magenta_scan.json): all 51 replacement hashes report `no_spill_detected` under the existing
  visible-edge scan. This is an automated screen, not final visual acceptance.
- `after_contacts/`: native / reviewed / replacement comparisons, visually inspected for all distinct outputs.
- `staged_contacts/`: all 65 newly approved targets, visually inspected. `staged_crop_audit.json` also checks all
  838 staged records: 375 prior repairs, 308 complete raw subjects, 54 numerical boundary suspects, and 101 without
  a raw rectangle in the catalog. Of the 54 suspects, 13 already have earlier repairs, ten were corrected here,
  and 31 are small contour/margin differences retained for review; a numerical boundary test is not proof of truncation.
- [browser_validation.json](browser_validation.json): fresh import, upgrade from the previous round, newer local
  note/offset preservation, multi-round offset carryover, acceptance/hide/reload, and Clear persistence.
- `*_equipped.png`: inspected browser captures of the sword, neckline, helmet, shield and recovered bowstring.

The checkpoint/ledger, runtime tables, original BMPs, accepted dolls and previous review pass remain unchanged.
Nothing in this round authorizes final ledger acceptance or installation.

Rebuild local outputs without another generation call:

```sh
cd level_generation/ui/hud_inventory/paperdoll_review/review_pass_20260926_round2
python3 audit_staged.py
python3 finish_repairs.py
python3 refresh_inherited_placements.py
python3 build_overlay.py
python3 validate_pass.py
```

The raw generated masters and exact prompts already exist under `generated/weapons_01` through `weapons_04`.
Do not regenerate approved images merely to resume this slice.
