# Terrain restoration

Terrain catalogues, source references, masks, and preparation for image generation live here.

For **static BLV and outdoor BModel surface textures**, use the
[2×/4× texture restoration playbook](TEXTURE_RESTORATION_PLAYBOOK.md). It records the Abandoned Temple quality
feedback and the shared-background/true-alpha-overlay workflow; terrain transition work below remains separate.

## Materials terrain style

- **[Materials terrain (New Sorpigal pilot)](materials/README.md)** — blended CC0 ground materials, smoothed mesh,
  per-map weights; engine path shared by every map that gets a material file.

## Start here: current terrain handoff

- **[Space cleanup and retained material](CLEANUP.md)** — raw diagnostic sequences and obsolete trial stages were removed; accepted assets and authoring sources are preserved.

- **[MM6 results, lessons learned, and the next MM7 workflow](TERRAIN_RESTORATION_HANDOFF.md)** — authoritative entry point.
- **[MM7 restoration: all 13 maps, review gallery and 116-texture pack](mm7/README.md)**.
- [MM7 continuation handoff](mm7/HANDOFF.md).
- [Complete MM6 review and 134-texture pack](mm6_remaining/transitions/index.html).
- [Current source/manifest hash snapshot](MM6_TERRAIN_HANDOFF_STATE.json).

The complete MM6 terrain is installed in the peasants enhanced playtest. The links below document earlier
New Sorpigal studies; their local version names and installation instructions are historical, not the final pack selection.

## New Sorpigal (MM6)

- [Visual catalogue](mm6_new_sorpigal/index.html)
- [Catalogue documentation](mm6_new_sorpigal/README.md)
- [Portable archive](mm6_new_sorpigal.zip)
- [Prepared imagegen jobs](mm6_new_sorpigal/imagegen_briefs/jobs.json)
- [Generated master study: in-game before/after](mm6_new_sorpigal_master_study/index.html)
- [Master study notes and prompts](mm6_new_sorpigal_master_study/README.md)
- [Land transition masks and iteration policy](mm6_new_sorpigal_transitions/README.md)
- [Flat land-transition review bench](mm6_new_sorpigal_transitions/index.html)

Rebuild from the repository root:

```sh
python3 level_generation/terrain/build_new_sorpigal_catalogue.py
```

The builder reads the existing runtime sources and writes only this catalogue and its archive.
