# Minimap rendering technique research

Research date: 2026-09-27. This records findings and the proposed next experiment.
Follow-up completed: [process reproduction, settings, renders and validation](VINEVI_PROCESS.md).

## What is established, and what is not

The archived New Sorpigal map is a 512×512 indexed-color bitmap. The local behavioral reference in
`reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.cpp` loads a map-named image, and
`src/GUI/UI/UIGame.cpp` samples that image for the outdoor minimap. This establishes a precomputed image at
runtime, not the original studio's image-authoring process. No original New World Computing production recipe
was found. A claim that they used a particular renderer or filter would be speculation.

There is a directly relevant first-hand reconstruction guide by vinevi, dated August 11, 2020:
[Making minimaps for Might and Magic](https://www.moddb.com/mods/minimaps-for-might-magic/tutorials/making-minimaps-for-might-and-magic).
The author used orthographic Blender/Cycles renders, a warm sun and cool fill, disabled cast shadows, and separate
terrain/object layers. Terrain received Random Pick; buildings received levels adjustments; final grading adjusted
contrast, saturation and sharpness. This describes the modder's workflow, not verified 1998 production history.
The [mod page](https://www.moddb.com/mods/minimaps-for-might-magic) also links an editable Krita project; it was not downloaded.

[Krita's manual](https://docs.krita.org/en/reference_manual/filters/other.html) describes Random Pick as a pixel-fringe
effect. It is not simply a large Gaussian blur. Applying a displacement-like filter to our complete composite
would conflict with landmark fidelity; use a bounded terrain-only treatment, if needed.

Cartographic hillshade is a relevant established alternative to full physical lighting: derive brightness from
slope/aspect, choose illumination direction, and optionally exaggerate relief or combine several directions.
Cast-shadow calculation is separable from local slope shading.
[Esri hillshade documentation](https://doc.arcgis.com/en/allsource/1.2/analysis/geoprocessing-tools/spatial-analyst/hillshade.htm),
[multidirectional hillshade](https://doc.arcgis.com/en/allsource/1.2/analysis/raster-functions/hillshade-function.htm).

## Measurements from our files

All images were compared at 512×512. The fixed native-image grass mask selected normalized RGB pixels with
G > 1.18R, G > 1.5B and G > 0.25. Luma is 0.2126R + 0.7152G + 0.0722B on encoded RGB, scaled to 0–255;
these are descriptive image statistics, not physical luminance. Saturation is HSV saturation. Texture and shading
both contribute to the luma spread; this measurement does not isolate lighting alone.

| Image | Grass luma 10th / median / 90th percentile | Median saturation |
| --- | --- | --- |
| Original | 62 / 74 / 120 | 67.3% |
| Raw Blender | 67 / 76 / 79 | 51.7% |
| Smooth/brighter Blender | 87 / 95 / 99 | 50.0% |
| Filtered + relief Blender | 69 / 107 / 134 | 45.7% |

The raw capture has far less grass tonal variation. The styled capture is already brighter overall than the
original while remaining less saturated. A global brightness increase alone will not reproduce the original.
Our original geometry test used generic Cycles materials, ambient fill and cast shadows, then filtered the
combined image. That couples terrain styling to small building details and makes selective correction difficult.

## Proposed next candidate

1. Keep the verified camera, world bounds and every landmark coordinate fixed.
2. Render terrain color, terrain relief and buildings as separate layers. Preserve shore/road masks as controls.
3. Create broad, smooth slope shading from native heights. Sweep lighting elevation, azimuth and shading-only
   vertical exaggeration against the original. Disable cast shadows for this stylistic trial.
4. Grade terrain by material: recover saturated yellow-green grass, warm earth and restrained blue water.
   Match broad tonal ranges before introducing fine texture. Smooth terrain texture/relief, not the building layer.
5. Raise building visibility with an independent levels curve and small-scale sharpening, without moving or
   enlarging footprints. Composite buildings after terrain processing.
6. If straight tile boundaries still dominate, test very small terrain-only edge breakup under protected landmark
   masks. Retain an untouched version alongside it; do not use unconstrained image warping.
7. Compare full map, town and islands with the existing geometry overlay. Treat camera registration and visual
   similarity as separate checks. Keep the sharper building layer separate through final downsampling.

Any numerical lighting/smoothing settings in that experiment would be new trial parameters, not recovered
original-game settings. Palette reduction/dithering can be offered as a separate retro-style comparison; the
current OpenYAMM PNG pipeline does not need the legacy indexed-color constraint.
