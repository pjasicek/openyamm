# Deterministic PC background removal investigation — 2026-09-27

## Current revision: stone faces, jewelry and full ovals

The port 9100 page now displays the revised masks in `review_v2_04/`, alongside the first pass.
It opens on `7pc01` frame 12. The **Stone frame 12** button works for every family; URL parameters
`?family=7pc05&frame=1` select a particular comparison. The same 672-frame sample is preserved.

- **Stone:** native stone colors can break the old silhouette estimate. Frame 12 now uses the union of that
  character's neutral and stone guides, with a separate interior-protection rule. The actual stone RGB decides
  which near-boundary pixels resemble backing; no face-color competition or shortest-boundary optimization remains.
- **Pale accessories:** only exterior green material trains the backing model. Nearby disconnected details can
  survive; they are not discarded simply because the head is the largest component. For `7pc05`, all 147 pale pixels
  lost in frame 01 and all 126 lost in frame 55 are retained above half alpha in the revision. The contact sheets
  show the earrings against both light and dark backgrounds. These counts describe that measured regression,
  not a universal visual-quality test.
- **Full ovals:** a family profile is frozen from the native neutral silhouette's convexity. Nearly convex heads
  get a solid protected interior and small outline-gap closing; only the outer edge receives soft alpha. Each
  pose keeps its own silhouette, including lowered and tilted heads. This is not an ellipse pasted over every frame.
- **`malea`:** the first-pass neutral and frame-55 exports did not discard pixels with all RGB channels above 100;
  the bright band was already largely retained, while the adjacent hair acquired notches. The rounded treatment
  improves that boundary. The dark preview helps distinguish white material from the pale comparison background.

The selection ring is an **overlay, not a stencil**. The new HUD composite follows `GameplayUiRenderer.cpp`:
a 60×80 logical face frame, portrait inset by 2 logical pixels, `FACEMASK` over the portrait, and `selring`
one logical pixel to the left. Its actual restored textures are used. This is a local compositing preview,
not a game capture; it does not change the renderer. The portrait still keeps its original 118×158 export.

[Stone comparison](review_v2_04/stone_comparison.png) ·
[Accessories and ovals](review_v2_04/accessories_comparison.png) ·
[Revision manifest](review_v2_04/manifest.json) · [Validation](review_v2_04/validation.json) ·
[Browser capture](review_v2_04/browser.png).

All 672 candidate RGB arrays and dimensions remain unchanged. Neutral and stone masks were each recomputed
for all 72 families: all 144 repeats matched. No pixels were lost from the measured protected interior.
The revised browser checks passed for image loading, navigation, the stone shortcut, both comparison backgrounds,
the earring regression, slideshow playback and the selection-ring toggle. The preview is served by the persistent
user service `openyamm-pc-alpha-9100.service`.
These are revised candidates, not global artwork acceptance. Complex green outlines, detached features and
backing remnants still need review; the diver's stone helmet is substantially recovered but retains an uneven rim.
The native guide is approximate: material more than eight physical pixels outside it may need a saved manual mask.

Reproduce this revision into a fresh directory:

```sh
python3 -B level_generation/ui/hud_inventory/pc_background_removal_20260927/build_v2.py \
  --output /tmp/openyamm-pc-alpha-v2-repeat
```

The original `build.py` and `review/` remain unchanged as hash-bound first-pass evidence. The unserved `review_v2`,
`review_v2_02` and `review_v2_03` directories retain intermediate trials. The remaining sections describe the first
investigation, not the active extraction method.

## First investigation

Background removal is practical as a local batch operation, with explicit mask repairs for exceptions.
The present prototype is useful review material, **not a production-ready universal extraction**.
It introduces no translation, scaling or regenerated artwork. Some similarly colored subjects and unusual
poses still need corrected masks before deployment.

[Interactive comparison on port 9100](http://127.0.0.1:9100/level_generation/ui/hud_inventory/pc_background_removal_20260927/index.html)
· [Examples](review/examples.png) · [All 72 neutral candidates](review/all_neutral_candidates.png)
· [Difficult poses](review/difficult_poses.png) · [Edge cases](review/edge_cases.png).

The page has character/frame selection, light/dark/checker backgrounds, masks, native pose references and
a numeric frame slideshow. All 56 frames are included for `pc01` and `pc23`; the other 70 families have
frames 01, 12, 35, 36, 38, 39, 55 and 56. These cover neutral, stone, lowered/partial, injury and expressive
poses. The slideshow is diagnostic, not the game's animation schedule.

## Where the accepted PC slice lives

The authoritative current selection is [accepted_icons.json](../accepted_icons.json). Read its per-target
`artifact` and `sha256`, because later spill repairs supersede some files in the original stage.

- Original accepted generation slices:
  `review/second_pass/portrait_opaque_regen_v1/<family>/restored/` (six families), and
  `review/second_pass/portrait_opaque_regen_remaining_v1/<family>/restored/` (66 families).
- Consolidated stage: `runtime_install_20260926/stage/engine/icons_x2/`.
- Some current PC revisions: `spill_acceptance_20260927/accepted/engine/icons_x2/`.
- Installed content: `assets_dev/engine/icons_x2/`.
- Native originals: `assets_legacy/icons_20260926/engine/icons/`, resolved through the explicit source archive.

There are **72 accepted families × 56 frames = 4,032 portraits**, including prefixes such as `malea`,
`girla`, `lmin`, `zmin` and `wets_`; a filename filter for only `pc*` would miss part of the slice.
The table references `pc30`, but its native frames are missing and the investigation does not invent them.
Every present native canvas is 59×79; every accepted restored canvas is 118×158.

Earlier `portrait_alpha_pilot_v1` / `portrait_transparent_v*` experiments used generated transparency and
are historical alternatives, not the current accepted inputs for this investigation.

## Method and measured result

1. Verify the current accepted image and archived native-source hashes.
2. Estimate the shared native textured backing from multiple characters and poses. Its color varies slightly
   with the original indexed palette. Mark low-support coordinates as unknown.
3. Derive a coarse native silhouette and map that guide onto the fixed x2 canvas. Protect its interior while
   refining a narrow boundary band using the actual accepted portrait colors and neighboring pixels.
4. Use deterministic color clustering and a binary graph cut, then apply a small alpha-only edge feather
   (`sigma=0.55` physical x2 pixels). The interior is opaque. No global green key is applied to the face.
5. Write a separate RGBA candidate and grayscale mask. Preserve **every RGB pixel**, even under alpha zero.

The 672-frame investigation took **83.12 seconds** on this machine, including input verification, native
backing estimation, PNG output, and 72 repeated segmentations. The complete 4,032-frame batch should take
minutes, but that duration has not been measured. The work remaining is edge quality and exception handling,
not the cost of batch execution.

All 672 reloaded output PNGs have identical RGB arrays and canvas dimensions to their accepted inputs.
One mask per family was computed twice: all 72 repeated masks matched exactly in the recorded environment.
NumPy/SciPy/Pillow versions, source/output hashes, mask statistics and source provenance are in
[review/manifest.json](review/manifest.json). A fixed clustering seed gives repeatability here; byte-identical
results across different numerical-library versions are not claimed.

The comparison page was tested in headless Chrome on port 9100: 72 families, image loading, full 56-frame
navigation for `pc01`, background switching, the lowered `pc23` pose and slideshow advancement passed.
No engine builds or runtime changes were needed for this asset investigation.

## What the images establish, and what they do not

- Ordinary human portraits and several green/dark faces have useful cutouts. The stone and lowered `pc01`
  examples also retain their pose and original pixel positions.
- A plain green cutoff failed badly on the green orcs and diver helmet. Similar-colored skin is not safely
  distinguishable from the backing by hue alone. The native guide substantially improves that behavior.
- `pc23` has unstable or ragged jaw remnants in several poses; `pc25` retains dark green material below its
  jaw; fine minotaur horns/hair need inspection. These are visible failures, not accepted output.
- `wets_` frame 12 loses a large part of the stone helmet; frame 35 damages a lens. `pc41` frame 35 has a
  notch in the head outline. The protected guide cannot compensate for every native/restored difference.
- Keeping only the main connected silhouette can discard detached intended details. Filling interior holes
  can retain real enclosed background holes. Those choices are prototype assumptions requiring local repair.
- Alpha-only feathering can retain a slight green edge tint where the accepted RGB already mixes subject and
  backing. A later edge-only color cleanup can correct that without moving any pixels, but it is not included here.
- Zero coordinate changes do not establish perfectly stable outlines: independently extracted masks can still
  flicker. They also cannot fix any movement already painted into the accepted expression frames.

The recommended production route is this fixed-canvas mask pipeline plus explicit per-family/pose mask
corrections, followed by sequence review over the basebar. Store those corrections with the input hashes so
the final batch remains repeatable. Do not reuse one neutral mask for every pose: partial, tilted and expressive
frames legitimately have different outlines. A fixed ellipse would also clip horns, ears and hair.

No acceptance percentage is claimed for the 672 candidates. The static contacts and representative sequences
were inspected; all candidates remain investigation outputs. Accepted/staged/runtime images, receipts and
the canonical ledger are unchanged.

## Reproduce without changing accepted artwork

Run from the repository root. Existing review manifests are protected against accidental overwrite.

```sh
# Repeat this 672-frame investigation into a fresh folder:
python3 -B level_generation/ui/hud_inventory/pc_background_removal_20260927/build.py \
  --full-family pc01 --full-family pc23 --output /tmp/openyamm-pc-alpha-repeat

# Optional full batch of review candidates (not acceptance or deployment):
python3 -B level_generation/ui/hud_inventory/pc_background_removal_20260927/build.py \
  --frames all --output /tmp/openyamm-pc-alpha-all

# Serve the checked-in comparison page:
python3 -m http.server 9100 --bind 127.0.0.1 --directory /home/pjasicek/github/OpenYAMM
```

`--families pc01,pc23` limits candidate output, while retaining the full native reference set for the backing
estimate. No model downloads, imagegen, OpenCV installation or paid service are used.
