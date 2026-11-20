# Magenta screening — 2026-09-25

Read-only scan of all **1,262 pending selected targets**, including the 332 shared inventory/equipment icons,
906 fitted variants, and 24 remaining doll background/head records. **1,319 candidate/alternative records** scanned.
Accepted artwork is excluded. Source and candidate hashes bind every finding to the inspected image.

- **70** selected candidates: suspected magenta spill (automatic flag).
- **14**: purple material check, kept separate because native art already contains purple.
- **1,178**: no spill detected by this screen; this is not a visual acceptance or a guarantee of clean edges.

[Review likely spill](../index.html?review=magenta) ·
[Review without detected spill](../index.html?review=clean) ·
[Purple material checks](../index.html?review=purple) · [Full report](report.json)

The GUI adds automatic badges and equipment-row/inspector warnings. “Flagged” includes automatic spill suspects;
“Auto: magenta spill” isolates them. Your manual decisions and placement proposals remain untouched. Export review
JSON includes the current automatic findings separately from your decisions. Changing a candidate attempt selects
its own hash-matched finding; changed/unscanned images are not presented as passing this check.

Method: inspect visible alpha >=24, red/blue-dominant pixels near the silhouette (within three output pixels),
and strongly matte-colored pixels anywhere. Ignore fully transparent RGB. Require at least five alpha-weighted
pixels and a coherent component or sufficient edge pixels. Compare native purple coverage to separate potentially
intentional material. This can still flag pink gems or highlights and can miss weak/isolated contamination.
The three contact sheets were visually inspected; obvious contamination is present on bowstrings, chains and
some fitted equipment edges. No pixels were repaired or removed, and no artwork was accepted/rejected.

Run after preparing/rebuilding candidates:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/scan_magenta.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/test_magenta.py
```

`report.js` is the file-friendly GUI data; `report.json` retains measurements and provenance. The contact JPGs
are diagnostics only, never replacement assets.
