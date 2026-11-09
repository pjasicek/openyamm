# New dirt master — directional transitions

[Handoff for shoreline generation and peasants enhanced integration](HANDOFF.md)
includes the accepted source paths and a hash manifest for the 51 completed land/water PNGs.

[Open the catalogue](review/index.html). It compares each native tile, the clean new-master composition,
and its finished AI boundary treatment, with directional suffixes, masks, prompts, assembled layouts and game captures.
The default catalogue and separate trial now use **v2**, which repairs the softened tile-border bands reported after v1.

The pack contains **33 transitions plus 3 pure materials**, exported as opaque RGB **256×256** runtime tiles
(2× the native 128px tiles). The runtime files are in [edge_treatment/runtime/v2](edge_treatment/runtime/v2).
The 512px authoring composites are in [composites/v2](composites/v2).

## Art and orientation

The user-selected [new dirt master](../generated/dirt_v2_512.png) supplies every dirt region.
A versioned [wrapping derivative](seam_repair/materials/dirt.png) quilts existing interior detail into continuous
border strips using the shared [terrain seam repair](../../seam_repair/build.py) implementation.
The central 384×384 master pixels remain exact. The accepted source file remains intact.
Grass, volcano and cobbles receive the same treatment from their accepted source masters.
Material sampling wraps through a gutter during the 512→256 export; masks and AI contact-shading fields extend.

All 33 original references were reviewed, including NE/NW/SE/SW corners and inward corners.
The existing `connected_v4` masks are copied without rotation, mirroring or geometry changes.
Suffixes follow the native tile names; the catalogue shows the actual image orientation rather than inferring
which material occupies a quadrant from the suffix alone. Existing grass, volcano and cobble material samples are retained.

Built-in imagegen edited each clean composition with its matching native reference: irregular olive/brown turf fringe
for grass, restrained gravel mixing for rock, and contact shadows plus worn stone endings for cobbles.
Nine pilots covered straight edges, corners/insets and road turn/cap before the other 24 were generated.
The bake retains only a narrow AI colour delta around each mask boundary. Equivalent tile edges share the same
appearance profile; interior material pixels are protected. V2 reuses these accepted AI deltas unchanged.
V1's mirrored material strips passed pixel-equality checks but created visible softened bands. Those strips are superseded.

Exact prompts and references are indexed by [generation.json](generation.json); raw imagegen edits are retained under
`edge_treatment/raw/v1`. The [bake report](edge_treatment/bake_v1.json) records all 33 protected-interior checks and hashes.

## Separate playtest

```sh
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/prepare_playtest.py
./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh transitions
```

Choose **Load Game → Terrain camera reference**. The save uses the supplied position
`(-9728, -11319, 161)`, yaw `89.227°`, pitch `-9.626°`.
The stage is `/tmp/openyamm-sorpigal-dirt-fidelity/transitions`. It now includes the newer
[native_water_v3](../../mm6_new_sorpigal_water/restoration_v3/README.md) animation: 14 frames plus its static fallback.
Only these 15 water textures are imported from that combined pack, preserving this trial's 36 repaired land tiles.
The mode owns a separate executable with the required water repeat-sampler fix, copied from `build/game/openyamm`
by default (`prepare_playtest.py --binary PATH` selects another build with that fix).
Re-running preparation refreshes the land, water and executable while preserving saves. The initial `candidate`, `current`
and `original` modes retain their previous executable and remain available for comparison.
Restart the game after preparation to reload the assets. [Installation hashes](reports/playtest.json) identify both packs.

No new dirt assets are installed into the peasants enhanced playtest or development terrain mounts by these scripts.
During this work, its executable/manifest and water files changed concurrently; the 36 corresponding terrain files
still match the initial protected hashes. See [snapshot check](reports/protected_snapshot_check.json).

## Rebuild and checks

Run from the repository root using the retained accepted master art and v1 AI delta layers:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/seam_repair/build.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/seam_repair/check.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/prepare_playtest.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/build_catalogue.py
```

- [Mask checks](reports/mask_check.json): 398 compatible edge checks, zero failures.
- [V2 local checks](seam_repair/local_joins.json): 211 unique compatible joins, covering 8,524 placements.
  Checks use 16px local windows and border detail; both gates pass. Opposite pixel equality is no longer appropriate.
- Reviewed shifted/repeated materials, the 32 highest-gradient join windows, all 211 joins, six legal layouts
  and eight fresh game captures. See [v2 review](seam_repair/review.json).
- Known native map-layout conflicts remain marked in the corner sheets. The trial uses its original map;
  the `corrected_*` camera names identify historical diagnostic locations, not newly patched map cells.
- The [v1 visual review](reports/visual_review.json) is historical. Its successful pixel-equality checks did not catch
  softened border bands; retain that limitation when using this report as a reference.

Capture preparation uses the existing `fixture/` layout matching the saved poses, not `fixture_v2/`.
Actor-placement overlays are disabled only in the private flat stage. A sustained Fly buff in diagnostic saves
prevents the faithful headless save round-trip from clearing flight and dropping the elevated camera.
This is an explicit camera fixture change; no renderer or gameplay system was changed.

```sh
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/prepare_captures.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/capture.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/build_catalogue.py
```

The art is a separate review candidate. Numeric edge checks establish continuity only for compatible placements;
they do not establish visual equivalence to the native art or eliminate deliberate material repetition.
