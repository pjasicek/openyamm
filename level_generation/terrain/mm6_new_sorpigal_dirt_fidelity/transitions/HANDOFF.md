# Handoff: accepted new dirt, land transitions, and remaining shoreline work

**Historical task handoff.** Its shoreline work is completed and its 63-file pack is now included unchanged in the
complete 134-file MM6 pack. For current source selection, installation, lessons and MM7 planning, start with
[the consolidated terrain handoff](../../TERRAIN_RESTORATION_HANDOFF.md). Do not treat the remaining-work or
old installer-state sections below as current instructions.

The user accepted the new fuller dirt master, all 33 land transitions, the v2 seam repair, and
native_water_v3 in the separate trial. Their next requested task is to adapt the dirt→water
shorelines to this dirt and integrate the resulting terrain into
`./level_generation/creatures/mm6_peasants/play.sh enhanced`, preserving its other enhanced assets.
Completed 2026-09-09: the twelve shoreline overlays and combined 63-tile pack are in
[shorelines](shorelines/README.md), with [visual review](shorelines/review.html) and
[preservation audit](shorelines/integration.json). Peasants enhanced now installs this pack through its authoritative
terrain-only installer. Shorelines v2 now adds the broader shaded damp-earth bank requested after screenshot 1280, using a separate AI detail layer. All 51 accepted hashes below remain unchanged. The remaining-work sections below document
the original handoff requirements and sources.

All paths below are relative to the repository root. Files are saved in the shared workspace;
the dirt-fidelity project is currently untracked in Git, so another checkout will need an explicit transfer.
Use the repository files as sources, not the disposable `/tmp` trial.

## Accepted sources

Let `D = level_generation/terrain/mm6_new_sorpigal_dirt_fidelity` and `T = D/transitions`.

| Purpose | Source |
| --- | --- |
| User-selected 512px dirt artwork | `D/generated/dirt_v2_512.png` |
| **Current 512px repeating dirt material for new shoreline compositions** | **`T/seam_repair/materials/dirt.png`** |
| **Current 36 runtime land PNGs, 256×256** | **`T/edge_treatment/runtime/v2/*.png`** |
| Current 512px land composites | `T/composites/v2/*.png` |
| Current grass, rock and cobbles materials | `T/seam_repair/materials/{grass,volcano,cobbles}.png` |
| Accepted AI transition appearance deltas | `T/edge_treatment/layers/v1/*.npz` |
| Original directional land masks | `T/masks/connected_v4/*.png` |
| Native land references and imagegen prompts | `T/references`, `T/edge_treatment/prompts/v1` |
| Land build and seam checks | `T/seam_repair/{build.py,check.py,build.json,local_joins.json,review.json}` |
| Visual comparisons and game captures | `T/review/index.html` |

The v1 name on AI delta layers is intentional: v2 reuses the accepted natural turf fringe, gravel bleed
and cobble contact shading. The current *finished exports* are v2.
The periodic dirt derivative retains the selected master's central 384×384 pixels exactly.
Preserve its texture phase and palette in the shoreline overlays; do not rotate, mirror, rescale or independently
regenerate their dirt regions.

Keep the **15 accepted water PNGs** from
`level_generation/terrain/mm6_new_sorpigal_water/restoration_v3/runtime_x2/worlds/mm6/terrain_x2`:
`6hdwtr000.png` through `6hdwtr013.png`, plus `6wtrtyl.png`.
That directory is a combined 63-file pack containing **older dirt/land/shore art**. Importing all of it would
overwrite the accepted new dirt. Use only its 15 water files in the new combined pack.

[HANDOFF_ASSETS.json](HANDOFF_ASSETS.json) records repository-relative source paths and SHA-256 hashes for
all **51 accepted runtime PNGs** (36 land + 15 water), the two dirt master references, and the 12 missing shore names.
These hashes were checked against the files when this handoff was written.

## Remaining terrain art: twelve shoreline overlays

Rebuild `6wtrdr{e,n,ne,nw,s,se,sw,w,xne,xnw,xse,xsw}.png` using the current repeating dirt material above.
They are RGBA land overlays rendered over animated water, not flattened blue-water-and-dirt images.
The separate trial still has older shoreline dirt; these twelve overlays were not adapted by the land work.

Useful existing sources:

- Original shore references, context tiles and alpha paths:
  `level_generation/terrain/mm6_new_sorpigal/catalogue.json`, family `shoreline`;
  native alpha under `level_generation/terrain/mm6_new_sorpigal/alpha/shore_visible`.
- Latest retained 512px shore overlays and coverage:
  `level_generation/terrain/mm6_new_sorpigal_water/restoration_v3/authoring/6wtrdr*.png`.
  Their RGB uses the old dirt; use them as alpha/contact-shading references, not the new dirt source.
- Historical construction logic: `level_generation/terrain/mm6_new_sorpigal_water/build_water.py`.
  Do not rerun its old water generation or old mirrored border locking into the accepted pack.
- Current material quilting/export convention:
  `level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/seam_repair/build.py`
  and shared `level_generation/terrain/seam_repair/build.py`.

Use the imagegen skill for any newly painted shore fringe/contact treatment. Retain native NE/SW and inward-corner
orientation and compatible shoreline coverage. The user's preference is irregular material bleed and subtle shading,
with the accepted dirt material preserved away from the boundary. Keep transparent-water coverage and review the
overlay on multiple actual water frames. Export at 256×256 with proper premultiplied-alpha filtering.

Avoid the previous seam mistake: averaged/mirrored border strips produced visible smooth grid bands while
opposite-pixel equality checks passed. Use continuous material samples with wrapped gutters during reduction;
coverage and shading use the appropriate neighbour extension. Matching consecutive pixels is not the criterion.
Check shifted joins, local worst 16px windows, border detail, and complete multi-tile shoreline contexts.

## Integrating with peasants enhanced

Create a distinct combined terrain pack/manifest containing:

- 36 accepted land exports, byte-identical to the handoff hashes;
- 15 accepted native_water_v3 water exports, byte-identical to the handoff hashes;
- 12 newly adapted shoreline RGBA exports.

Total: **63 runtime PNGs**. Validate the combined land/shore joins across all 14 water frames and inspect coastline,
island, inward corners, low-angle water and the supplied dirt viewpoint. Existing native map contradictions are a
separate layout issue; retain the enhanced session's reviewed map correction.

`level_generation/creatures/mm6_peasants/prepare_playtest.py` currently points `TERRAIN` at the old combined
native_water_v3 pack. Its `install_terrain()` checks that pack's iteration, 63-file manifest, validation and animation
hashes. Update the authoritative source and validation records for the new combined pack. Simply copying new dirt
into `/tmp/.../enhanced` is insufficient: the existing installer would replace it with old dirt on preparation.
Keep meaningful manifest/hash/visual checks; do not relabel stale validation as covering the new files.

Preserve existing enhanced creatures, decorations, sky, buildings, saves and other content. The water requires the
renderer change that repeats water sampling while clamping land/shore overlays. The verified executable used by
both the newer water session and this trial has SHA-256:
`56791c4f9342da2dbf664e8ed545b464749f4830338df457d81e0490e9c1e491`.
A later build containing that fix is fine after checking the affected views; do not restore the older dirt trial binary.

## Existing separate trial

```sh
./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh transitions
```

Load **Terrain camera reference** (not a menu entry named Dirt_View).
Camera: map New Sorpigal, position `(-9728, -11319, 161)`, yaw `89.227°`, pitch `-9.626°`.
The trial now owns `/tmp/openyamm-sorpigal-dirt-fidelity/transitions/openyamm` and includes new land + water v3.
Its installer and hashes are `T/prepare_playtest.py` and `T/reports/playtest.json`.

Do not use `D/runtime/6dirttyl.png`, the original `candidate` trial, `T/materials/dirt.png`,
or `T/edge_treatment/runtime/v1` as final land sources: they predate the accepted v2 seam repair.
