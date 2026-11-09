# Prepared weapon, bow, shield and wand candidates

Prepared 2026-09-24 from retained artwork; **no new generation or acceptance**.

[Browse all 332 icons](index.html) · [Try equipment on the accepted doll](../index.html?doll=1&art=candidate)

| Group | Exact-2× candidates | Total distinct icons |
| --- | ---: | ---: |
| Melee weapons | 244 | 244 |
| Bows / missile weapons | 35 | 35 |
| Shields | 38 | 38 |
| Wands | 15 | 15 |

66 candidates were already connected to the browser and are preserved. This pass adds 229 individual
extractions from 22 retained raw sheets and 37 exact-source donor copies. Donor sources, native dimensions,
source rectangles and compositing contracts are checked against each destination.

`manifest.json` records source/output/raw hashes, actual sampling, extraction rectangles, cleanup parameters,
registration findings, selected alternatives and donor provenance. Dense64 layouts are normalized in `layouts/`,
with hashes of the original manifests, layouts, references, receipts and submitted prompts. Canonical raw
attempts retain their original payload links. None of these inputs or the checkpoint is modified.

Each export is transparent RGBA at twice its original full canvas, with table offsets unchanged. The magenta
matte is estimated and unmixed before premultiplied resizing. Inventory extraction opts into thin-line seed
preservation so bowstrings and blade tips present in raw art survive spatial erosion. Low-magenta-chroma
foreground pixels supply those additional seeds; intentional purple interiors retain ordinary spatial seeds. A background-distance threshold of 0.08 removes near-magenta sheet noise.
This opt-in does not change previous dolls/equipment exports or accept their art.

Preparation is not visual approval. Of the 266 new candidates, 245 trigger the conservative registration guard
and 256 touch a measured extraction boundary; these findings are visible in the browser inspector. Some retained
art changes shape or extends beyond its native cell, so clipped tips/guards, fitting differences and residual
color artifacts still need review. These candidates are not claimed to be verified drop-in replacements.
No per-item repositioning or independent stretching to silhouette bounds was applied to hide those differences.

The main browser's **2× candidates, native fallback** mode now has candidates for all 332 scoped icons.
**Accepted 2× only** still shows native weapon/shield art because these candidates are unapproved.
The 466 accepted ESRGAN doll parts are unchanged. The main pending queue still contains the separate 930
paperdoll-background/head and fitted-equipment targets; these base inventory icons are reviewed via their
selectors, layer inspector, and this gallery. “Try on doll” equips the selected item at game-table coordinates.

Rebuild from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/prepare_inventory_candidates.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/build.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/verify.py
```

The preparer preserves existing external candidates and regenerates only its own unapproved previews.
Accepted checkpoint art takes precedence when the catalog is rebuilt. Runtime assets are not installed.

Validation passed: all 332 candidate images decoded at exact 2× size and were selected/drawn through the
actual equipment controls in headless Chrome. All 332 gallery cards and a “Try on doll” link were checked.
Accepted-only mode still uses native unapproved equipment; accepted ESRGAN doll parts remained selected.
[Browser checks](browser_checks.json) · [Unchanged tables/checkpoint verification](verification.json).
The matte tests cover intentional purple material, soft-edge unmixing, missing foreground, and thin bowstrings.
