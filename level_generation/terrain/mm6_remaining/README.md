# Remaining MM6 outdoor terrain

The missing assets catalogued below are now generated in [transitions/](transitions/index.html): corrected v3 masters,
60 material transitions, six extra roads, and a combined 134-file runtime pack. See the
[review and iteration policy](transitions/README.md) for checks and the separately recorded original map-layout mismatches.
The inventory below retains the original pre-generation baseline and its source hashes.

Scanned all 15 outdoor maps: **120 distinct static tile textures**, of which **49 are restored** and **71 remain**. The restored pack also contains the 14 water animation frames.

| Family | Missing | Maps |
| --- | ---: | --- |
| Sand | 13 | Paradise Valley, Hermit's Isle, Blackshire, Dragonsand, Free Haven |
| Snow | 13 | Sweet Water, Kriegspire, Frozen Highlands |
| Cracked ground | 13 | Sweet Water, Paradise Valley |
| Swamp | 13 | Mire of the Damned, Castle Ironfist |
| Tropical vegetation | 13 | Bootleg Bay |
| Additional cobbles on dirt | 6 | Sweet Water, Paradise Valley, Hermit's Isle, Kriegspire, Blackshire, Dragonsand, Frozen Highlands, Free Haven, Mire of the Damned, Silver Cove, Bootleg Bay, Castle Ironfist, Eel Infested Waters, Misty Islands |

Five new masters + 60 directional material→dirt transitions + six additional cobblestone-road tiles.

Each new material family uses the twelve suffixes `e,n,ne,nw,s,se,sw,w,xne,xnw,xse,xsw` (edges, corners and inward corners). These are opaque composites; the material masks still need extraction and connected-edge validation.

Additional roads: `6drsrcros`, `6drsrew_n`, `6drsrncap`, `6drsrns_e`, `6drsrns_w`, `6drsrscap`.

Existing dirt, grass, volcano, animated water and dirt shoreline assets can be reused. Swamp channels are baked into its opaque material, not a new water animation. Sand and snow do not introduce separate water-overlay families in the shipped maps.

[Visual catalogue](index.html) · [Exact per-map inventory and source hashes](inventory.json) · [71 missing filenames](missing_tiles.csv)

This inventory reads repository ODMs, retaining their source hashes; it does not modify maps, artwork or the enhanced playtest. The New Sorpigal test correction changes placements but adds no texture family.

Rebuild: `python3 level_generation/terrain/mm6_remaining/inventory.py`

Five v1 master candidates are now available: [comparison, tiles and prompts](masters/v1/index.html). These are not yet part of the accepted runtime pack counted above.

Master revision v2: [larger cracked/tropical segments and repaired sand ridges](masters/v2/index.html). Snow and swamp remain byte-identical to v1.
