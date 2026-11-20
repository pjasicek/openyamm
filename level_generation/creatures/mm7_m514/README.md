# MM7 ambient rat — staged native sprite restoration

Open [viewer.html](viewer.html) directly for native/restored animation, eight direction aliases, placement,
light/dark backgrounds and the native appearances. No engine assets or gameplay bindings were changed.

All **29 native unique frames** are restored: five standing views, four walking phases in each of five stored
views, three front collapse frames and one corpse. Descriptor IDs 472–474 all use palette 545, with identical
appearance. Attack/shoot reuse walking; hit/fidget reuse standing. Native 125 ms timings, mirror flags, group IDs,
action reuse, scale and bottom-center anchoring remain in [manifest.json](manifest.json) and [sources.json](sources.json).
There are no additional family-owned native BMPs beyond these 29 files.

The base was generated with built-in imagegen, using a native standing sheet first and that accepted identity for
action sheets. Seven accepted sheets came from eight requests. The first front walk was rejected for substituting
profile/rear views; a frontal-only identity reference corrected it. All versions and exact submitted prompts remain
under `raw/`, `prompts/submitted/`, and [generation.json](generation.json).

The native rat is dark olive-brown and gray, with small pale whiskers and a pink-gray bare tail. The same fixed
RGB multiplier of 0.82 restores its tonal weight across every generated pose. Magenta matting uses local foreground
estimation and RGB unmixing, then repairs demonstrated contour flecks and green whisker contamination while protecting
warm tail pixels. Both cleaned masters and atlas-extracted frames are scanned. Inspect
[all frames](review/all_comparison.png) and [magnified light/dark edges](review/edge_closeups.png).

Export uses two physical pixels per logical pixel, with the original 256×256 logical canvas and pivot (128,256).
Registration inverts the common source window and sheet scale, then translates each frame to its native alpha
baseline; it does not independently fit silhouettes. The selected raw standing sheet is 1677×938 and action sheets
are 2048×764. The 2× export downsamples their generated detail. Native pixels were enlarged only in reference sheets.

One 1024×956 RGBA8 base page and matching zero-valued R8 mask page occupy **4,894,720 bytes (4.67 MiB)** decoded,
including packing. Tight base-plus-mask crops occupy 3,688,745 bytes. There are no independently generated recolors:
all three actor entries share one native palette, so their variant operation is an exact base bypass. The zero mask
documents the absence of recolorable regions. Preview PNGs are excluded from runtime memory totals.

Source hashes, frame coverage, crop reconstruction, atlas extraction, matching mask rectangles, native timelines,
alpha preservation and base bypass pass [validation.json](validation.json). Visual review covers all pose cells,
the native/restored sequence order, mirrored placement in the offline viewer and final light/dark edge crops.

Reproduce without AI calls:

```sh
python3 level_generation/creatures/mm7_m514/prepare.py
python3 level_generation/creatures/mm7_m514/process.py
python3 level_generation/creatures/mm7_m514/package.py
python3 level_generation/creatures/mm7_m514/build_viewer.py
```

Limitations: new fur/face detail is an interpretation of native pixels. Whisker alpha is estimated from one matte,
and subpixel color/opacity cannot be recovered exactly. Limb and tail contours vary slightly from native art;
no extra poses or camera views were invented. Keep this package staged until installation is separately requested.
