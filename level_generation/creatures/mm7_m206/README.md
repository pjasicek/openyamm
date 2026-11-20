# MM7 light elemental — validated staged restoration

All 56 native frames are restored: 19 movement, 20 attack and 17 disintegration poses.
The 33 descriptor-referenced images and 23 additional native poses are included. Additional poses are retained
without changing native playback. Descriptors 241–243 share palette 528 and frame art, with native scales
1.5, 1.799988 and 2.099991. Their Image1 frames reuse one stored camera for all eight directions without mirrors.
Standing/walk/fidget use 10 frames, attack/shoot 12, hit 6 and death 9, each at 62.5 ms per frame.
Death holds its last frame; the native `null` corpse action remains empty. Original Lit/Center flags are retained.

The base preserves the dark blue-gray oval, pale center, flickering ivory sparks, bright attack flare,
cool late-attack sparks and progressively fading warm gray-brown disintegration motes. Eleven accepted sheets
come from fourteen preserved outputs. Death-sheet v1 outputs invented intact orbs and were rejected;
d_1 v2 and d_2 v3 correct them. d_2 v2 was superseded because its wide sheet compressed particle spacing.
The interrupted d_2 v3 output was recovered on resume. Exact prompts, raw images and selection reviews are
in generation.json. Accepted raw sizes are 1536×1024, 1568×1003 and 2172×724; export size is not a claim
of separately generated detail at every output pixel.

The 2× export keeps the native 128×128 logical canvas and bottom-center pivot (64,128), with explicit
crop origins. Atlas base_0.png and its matching zero R8 mask are 1024×2091. Only one native palette exists,
so the variant is an exact bypass. Decoded shared base, mask and packing total 10,705,920 bytes (10.21 MiB).
Open viewer.html locally for native/restored playback, all descriptors, views, mask overlay and backgrounds.

Processing uses the common source window and uniform sheet scale, native baseline translation, estimated
magenta alpha, local contour unmixing, premultiplied Lanczos resizing and a consistent ivory-light grade.
The grade restores over-orange enhanced sparks while preserving dim motes and cool blue sparks; its exact
thresholds are in processing_settings.json. No per-frame histogram matching is used.

All 56 native/base poses were visually reviewed in comparison_0.png through comparison_2.png, including
the corrected final spark spacing. Ordered poses and native animation metadata were checked; browser captures
cover the attack flare, final death spark in view 7 and the empty corpse action. Cleaned and atlas edges
were reviewed on light/dark backgrounds. validation.json passes source hashes, complete coverage, unclipped
raw cells, exact crop reconstruction/extraction, mask weights, base bypass, alpha and native timing/flags;
the residual contour audit has zero candidates above 32. review/acceptance.json freezes these artifacts.

Reproduction from the repository root:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m206 --tone 1.0
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m206
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m206
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m206
```

Staged only; no gameplay installation or original asset changes. Fine sparkle shape and estimated edge opacity
remain an artistic interpretation of low-resolution native pixels. Review affected outputs again after any change.
