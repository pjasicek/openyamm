# MM8 Thunderbird restoration

Staged 2× restoration of all 125 native m552 files (120 referenced, five stored orphan poses),
including all native actions and stored camera directions. No gameplay installation or original edits.
Open `viewer.html` locally to compare native motion, restored art, palettes and coverage.

`manifest.json` records native logical 256×256 dimensions, per-step anchors/scales, exact durations,
mirrors, atlas crops and the expanded 576×576 work canvas at logical origin −32,−32 physical pixels.
`animations.json` preserves 192 descriptor/action/view tracks; unbound stored poses have no invented timing.
Four RGBA8 atlas pages have matching R8 mask pages. Decoded base plus mask memory is 59,919,360 bytes;
tight rectangles use 41,899,095 bytes and packing uses the remaining 18,020,265 bytes.
Pages use three pixels of hidden color/coverage bleed, four pixels crop padding and sixteen-pixel gutters;
no mipmaps are assumed. Runtime exports are 2× independently of imagegen sheet resolution.

Base artwork was generated with the built-in imagegen tool. `generation.json` stores selected raw,
exact prompt and ordered reference hashes. Raw sheets, rejected outputs, correction prompts and
accepted identity checkpoints remain under `raw/`, `prompts/` and `checkpoints/`.
The bad first view-1 attack prompt and incorrect rear-flight heads are explicitly documented there.
The three view-1 recovery poses were regenerated separately, keeping the accepted first four poses.

Processing: `process.py` unmixes the magenta matte, retains antialiased feather and claw alpha,
repairs demonstrated magenta/cyan contour RGB, and applies the frozen identity luminance multiplier.
Identity uses one common 0.9 sheet scale. `calibrate.py` applies one reviewed uniform similarity
transform per generated action/view batch against native torso landmarks over all its poses together.
The accepted transforms are frozen in `batches.json`; there is no independent per-pose centering,
rotation, equal-height normalization or native silhouette replacement. Raw and pre-registration masters
are retained for review. `tone.py` restores native coarse plumage color with generated fine detail,
while enhanced-art chroma masks protect gold talons and red beaks. Tone/edge repairs preserve alpha.

`materials.py` derives soft coverage from enhanced RGB pixels using eight nearest native palette
samples and frozen weights. Native palettes 553/554/555 share geometry and alpha; 553 is an exact
base bypass. The selective dark feather changes retain the native olive/brown tonal family, claws,
beaks and eyes. All preview variants are deterministic; variants were not separately generated.

Review includes every native pose in registration/final contacts, all 22 three-palette/mask contacts,
worst actual atlas contour patches on light and dark backgrounds, and the mirrored offline viewer.
The browser harness decodes all 375 preview variants and 125 stored poses, and checks 192 native
tracks at 1,200 timing boundaries. `validation.json` and the hash-sealed `review/acceptance.json`
are completion evidence; a draft manifest alone is not acceptance. Fine feather/barb shapes remain
an artistic restoration of low-resolution sources, not recovered original high-resolution assets.

To revise: run `python3 level_generation/creatures/mm8_m552/rebuild.py` from the repository root.
Rebuild reuses retained selected sheets and frozen registration, and never accepts changed artwork.
Inspect changed contacts and edges, run `browser_checks.py` through the approved offline wrapper,
renew `review/decision.json` with hashes of the evidence actually inspected, then run `finalize.py`
and `python3 level_generation/creatures/inventory_remaining.py`. Originals remain read-only.
