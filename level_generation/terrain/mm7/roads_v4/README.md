# MM7 roads v4: MM6 masks and imagegen contact borders

Current join correction: [v5](../roads_v5/README.md). The compositor now uses paired finished-art
strips; descriptions below of fading back to base at shared edges are historical.

User references: `test_img/1286.png` (serrated MM7) and `test_img/1287.png` (accepted MM6).
The v3 distance smoothing retained too much of the MM7 silhouette. This iteration uses actual accepted
MM6 road masks for 15 matching shapes. The four MM7-only diagonal pieces retain their native routes,
with whole-stone-scale contour cleanup and the same MM6 opening profiles. The north cap adapts the
MM6 south cap by rotating its mask, avoiding loose stones. No master material is rotated or regenerated.

`prepare.py` records all mask source hashes in `mask_sources.json`, exports solid fields/masks and
composites the existing MM7 materials into registered imagegen inputs. Detached fragments are removed.
`raw/` contains 19 individual built-in imagegen edits; exact prompts are in `prompts/`. The accepted
straight-road generated border is the style reference for the other 18 calls. No API/CLI fallback is used.

`compose.py` imports only the generated boundary band (full weight within 24 authoring pixels,
fading to zero at 40). Bounded linear-light color ratios preserve the generated border appearance without negative RGB. The generated appearance residual fades to neutral within the outer 32 authoring pixels (zero in
the outer 4), using smoothstep. The underlying material, coverage and contact shade retain their
shared opening profiles. This avoids transferring a dirt-to-stone colour gain onto the wrong
underlying material, which produced bright streaks in an intermediate preview. Master RGB uses wrapped gutters; masks, shading and appearance fields use
edge-extended gutters. Authoring is 512px; runtime is 256px. Original masters and nonroad tiles stay unchanged.

Rebuild in order:

```sh
python3 level_generation/terrain/mm7/roads_v4/prepare.py
python3 level_generation/terrain/mm7/roads_v4/compose.py
python3 level_generation/terrain/mm7/build_land.py
python3 level_generation/terrain/mm7/roads_v4/review.py
python3 level_generation/terrain/mm7/check_roads.py
python3 level_generation/terrain/mm7/check.py
```

`pilot.py` and the initial `mm7_road_mm6mask_pilot` capture document the isolated straight-road experiment;
`compose.py` supersedes its prototype export. Final evidence is the main MM7 gallery, especially
`road_close`, `roads_green` and `roads_dry`. The previous installed manifest is `previous_manifest.json`.

Mask coverage must stay hole-free. Visual RGB borders intentionally contain local rounded stone ends
and earth contact; do not interpret the appearance layer as a replacement alpha mask. Preserve the
shared opening profiles and review near-ground repeats, not just distant overhead fixtures.

Generated earth hue/texture is not imported. Outside road coverage, the accepted dirt receives only
a smoothed achromatic darkening factor in [0.5,1]. RGB artwork may extend up to 12 authoring pixels
outside the mask only where the generated image contains a grey adjacent stone shoulder. This
removes the orange earth halo observed in an intermediate overhead capture.

The master-earth substitution also applies where the generated rounded outline retreats inward
inside the starting mask. Grey stone segmentation is hole-filled and reduced to its main component
before local appearance extraction. This keeps the earth colour/phase consistent on both sides of
the starting contour. The raw AI output is retained unchanged for provenance.

The generated-grey classification closes narrow gaps with a 6px disk, fills holes, keeps the main
road component and retains a 3px contact fringe before earth substitution. Raw chroma classification
alone removes dark mortar between edge stones and makes them appear detached; preserve those
connections. These are authoring-pixel values, applied to the appearance guide, not the original master.
