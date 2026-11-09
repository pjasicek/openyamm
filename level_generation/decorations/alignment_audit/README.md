# Decoration ground-contact check

Run from the repository root:

```sh
python3 level_generation/decorations/alignment_audit/audit.py
```

This local, read-only comparison takes a few seconds and makes no image-generation calls. It compares the current
accepted restoration PNGs with their native PNGs in the same logical canvas. `report.json` has every measurement;
`measurements.csv` is a compact list; `ground_contact_review.csv` contains only accepted images whose recorded
anchor kind is `grounded` and whose base needs inspection. `index.html` and `base_closeups.png` show side-by-side
proofs. The script refreshes these reports but does not alter artwork or acceptance records.

The completed 113-appearance visual pass is recorded in [INSPECTION_2026-09-23.md](INSPECTION_2026-09-23.md)
and [inspection_2026-09-23.csv](inspection_2026-09-23.csv). Re-run the audit after changing artwork, then revisit
affected entries; the dated inspection is not regenerated automatically.
The accepted placement corrections are recorded in [CORRECTIONS_2026-09-23.md](CORRECTIONS_2026-09-23.md).

The grounded shortlist flags an upward shift greater than one native pixel only when both visible (alpha >=17) and
opaque (alpha >=128) bottoms move upward. It also flags a base-center shift greater than three native pixels. The
canvas size and accepted output hash are checked separately. A flag is a review request, not proof of floating:
foliage, loose branches and animation can change the measured lowest pixels while the actual support stays put.
For a flagged image, compare its original and restored base in the HTML view, especially the trunk, feet, pedestal
or other real support. The comparison cannot establish terrain contact at each map placement or judge whether the
art contains enlarged source pixels.
