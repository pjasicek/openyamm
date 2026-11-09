# New Sorpigal terrain border repair

**Historical repair iteration.** This directory is useful for its periodic-border method, but its combined artwork
and installation description are superseded. Start with [the current handoff](../TERRAIN_RESTORATION_HANDOFF.md)
and the complete MM6 pack; do not install this older union over the accepted new dirt and water.

This pack supersedes the blurred-border land v5 / water v1 exports for the enhanced playtest.
It contains 63 PNGs at 256×256. Accepted source masters, 33 connected-v4 land masks,
v5 dark transition artwork and the 12 reviewed shoreline alpha shapes are retained.
No new AI calls were needed. The earlier exports remain in their original project directories.

Open [review.html](review.html) for native before/after sliders, material repeats, all shore
contexts and animation. The runtime archive is [new_sorpigal_terrain_x2.zip](new_sorpigal_terrain_x2.zip).
The archive contains textures and a manifest; the existing corrected map is installed separately
by the playtest preparation script.

## Rebuild and install

```sh
python3 level_generation/terrain/seam_repair/build.py
python3 level_generation/terrain/seam_repair/validate.py
python3 level_generation/terrain/seam_repair/review.py
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --terrain-only
./level_generation/creatures/mm6_peasants/play.sh enhanced
```

`review.py` uses the retained native captures. After changing artwork, capture again before
accepting it; rebuilding the review does not run the game. Restart the game after installing.
The installer backs up existing tiles under `seed/terrain_before_periodic_borders`, preserves
saves and other enhanced assets, and installs the previously reviewed 12-cell map correction.
It refuses to overwrite a map with additional changes.

## Border method and acceptance

The former export averaged opposite strips, duplicating/mirroring the first eight authoring
pixels. This created soft stripes even though opposite edge pixels matched exactly.

The replacement borrows detailed patches from the same master. Cyclic minimum-error cuts
join those patches within the outer 64 authoring pixels, with only a one-pixel blend at the cut.
The central 384×384 source pixels remain unchanged. Across a tile wrap the samples are consecutive,
not duplicates. Material gutters wrap during downsampling; coverage and contact shading extend
their existing shared profiles. Mixed tiles are never blindly wrapped onto their opposite material.
Water uses a periodic deformation on a 512-sample domain, with no second border averaging pass.

Validation checks 332 distinct joins from the corrected map across all 14 water frames. Each
cross-border RMS gradient must stay below 1.75 times the neighbouring seven-pixel gradients
(measured worst: 1.227). Border-detail energy must be 0.8–1.3 times interior energy, and the
last-to-first animation change must be 0.8–1.2 times the average frame change.
These are screening checks, not proof of artistic seamlessness. Inspect repeated textures,
low-angle water and grass, the town overview, volcano slopes and shoreline animation before
installation. If broad bands, abrupt cuts, or a loop pop appear, revise the shared material or
composition and rerun the checks and affected native captures. Do not restore wide RGB averaging
just to make the first and last pixels equal.

Native captures use the same saved camera and executable for each before/after pair. Water
phase differs between separate runs. The 28 shoreline samples show moving water and stable land;
they are not full-frame-rate shimmer or GPU performance measurements. Thin terrain lines and
ordinary repeated motifs remain visible in places; this pass addresses broad baked blur bands.
