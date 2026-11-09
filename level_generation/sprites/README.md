# Non-creature sprite upscale scope

Inventory snapshot: 2026-09-09. Restoration has since progressed; this document describes inventory scope.
For current verified completion use [restoration readiness](restoration_jobs/READINESS.md), not the original
pre-generation remainder below. For generation use [size-aware decoration batching](restoration_jobs/BATCHING.md).

For the complete prepared execution queue, start with the [Luna worker package](restoration_jobs/README.md)
and its [goal document](restoration_jobs/GOAL.md). It supplies exact prompts, paletted references, dependencies,
cleanup/review helpers and coverage for every inventoried file, including an explicit unresolved-source queue.
Its preparation makes no new AI images; the existing Sorpigal art and benchmark drafts keep their separate status.

MM9 sprites referenced by `CLIENTFX/CLIENTFX/SPELLS.fxf` have a separate, deliberately narrow
[future restoration guide](mm9_fxf_effects/README.md). Do not use it for other MM9 SPR files or merge those DTX-derived
RGBA effects into the MM6–MM8 paletted-BMP queue described here.

For reusable effect packs, authoring tools and current engine compatibility, see
[effect library research](effect_library_research/README.md). This is research, not an installation queue.

Count covers native MM6–MM8 BMPs in `assets_dev/engine/sprites/` and `assets_dev/worlds/mm7/sprites/`.
Creature exclusions include guards, peasants, animals and unused creature poses, not just hostile monsters.

## Scope

| Category | Existing individual BMPs |
| --- | ---: |
| Decorations / scenery | 1,235 |
| Spell FX, projectiles, weather and other shared sprites | 862 |
| Ground-item / pickup billboards | 403 |
| Interface / buff overlays | 71 |
| **Referenced non-creature total** | **2,571** |

Shared files are counted once, with scenery/item/overlay use taking precedence over effect use.
There are **152 additional unclassified files** outside the creature sets. These include unused scenery,
extra effect frames, utility images and possible filename mismatches. They are a review queue, not all confirmed runtime assets.
Examples: `6tree31`, `trotree01`, `nwtrch00`, `fire0001`, `no0se1`, `lightmap`. A missing frame-table reference
does not prove a file is unused: direct code/UI references and native import aliases need separate checking.

Broad planning range: **2,571 confirmed table-referenced images, up to 2,723 including that review queue**.
At initial preparation, the 19 New Sorpigal enhancements reduced the remainder to 2,552 images.
That is a historical planning count, not current progress or strict master-detail acceptance.
“Referenced” means present in the current frame tables, not proof that every map or active spell uses every entry.

## Animation / generation workload

Follow [multi-request scheduling](PARALLEL_IMAGEGEN.md). A [ten-request trial](concurrency_trial_10/README.md)
succeeded but behaved largely as a queue: 272 seconds total, compared with a 31-second standalone control.
Concurrent submission is available; a substantial service-level speedup has not been demonstrated.

- 1,285 named frame groups have at least some source art; **257 are animated**.
- 1,225 distinct image sequences remain after merging identical frame-name sequences while ignoring palettes.
- Group counts are not AI-call estimates: aliases, palette variants, paired states and short sequences should share work.
- Restore complete short animation sheets together, lock rigid geometry, and preserve native timing, view/mirror flags,
  logical canvas and anchor. Split long sequences with a shared identity reference; do not independently redraw every frame.
- Keep opaque decorations separate from additive/emissive/translucent spell FX. Do not apply a hard silhouette matte to glows.
- Interface/buff overlays need their UI placement/transparency preserved, rather than a scenery placement workflow.
- Reuse completed New Sorpigal art. Deduplicate only after checking palette/material identity; equal BMP bytes alone
  do not prove equal in-game colors. The referenced files contain 2,471 distinct complete-file hashes.
- Save progress per asset/sequence, allowing resumable batches. Do visual contact-sheet checks and quick metadata/edge checks.
  Engine installation, including effect blending and map/global scope, is a separate task from generation.

## Coverage and limitations

- 23,906 native BMP files audited: 23,018 engine files and 888 MM7 world files.
- 19,004 table-referenced creature files and 2,179 additional creature poses excluded.
- Case-insensitive matching matters: many MM6 names are uppercase. Numbered `mXXX` files alone are not a sufficient creature filter.
- Frame names resolve with the runtime Image1, view/mirror and trailing-zero rules. Monster family tables plus the
  monster descriptor action bindings identify creatures; explicit legacy orphan groups/stems cover unused MM6 poses.
- 390 distinct non-creature frame names have no matching source BMP in this scope, mostly historical MM7 FX entries.
  These are reported separately; do not generate invented replacements just to satisfy stale table names.
- 175 MM9 PNGs (world-item art and quest markers) are separately present and excluded from this native MM6–MM8 restoration estimate.
- Counts are before visual deduplication or a wider completed-art audit. Only the 19 known New Sorpigal exports are subtracted.

## Files

- [Per-file non-creature and review queue CSV](non_creature_files.csv)
- [Full machine-readable inventory, groups, palettes and missing references](inventory.json)

Recompute without modifying assets:

```sh
python3 level_generation/sprites/inventory.py
```
