# MM8 School of Fish

Staged restoration of all 130 unique native images, including 44 stored poses absent from native playback.
The three actor descriptors retain all eight actions, eight logical views, native timing, mirrors and anchor flags.
Logical dimensions remain 256×256; physical export is 2×. Nothing is installed into gameplay.

Open `viewer.html` directly for native/restored/mask comparisons, palette selection, native animation playback and
manual access to every stored pose. `manifest.json`, `animations.json` and `variants.json` describe placement,
timing and deterministic recoloring. Nine RGBA8 base pages and matching R8 masks are in `atlas/`.
Decoded base plus masks and packing total 154,425,600 bytes (147.27 MiB), including 28,160,020 bytes of packing overhead.

The built-in imagegen tool produced the base artwork. Exact prompts are in `prompts/`, selected and rejected raw
outputs in `raw/`, and prior accepted processing in `checkpoints/`. Actual generation was 1536×1024 or 1774×887,
with per-cell dimensions and physical registration recorded in `generation.json` and `registration.json`.
The 2× export size is separate from the generated detail resolution.

Palette 637 is the exact base bypass. Enhanced RGB pixels define one soft R8 coverage mask using native color
samples; fixed palette deltas derive 638 green and 636 orange. Native unchanged gray fins and pale highlights
are protected. No native spatial mask is resized onto changed anatomy. The offline palette operation is documented
in `material_settings.json`; engine loading and shader integration remain separate work.

Visual review covers all 21 native/final sequence contacts and 21 complete palette/mask contacts. Confirmed harsh
markings and green/cyan fin-tip fringes were corrected from retained raw art. Final magnified contour patches were
checked on light and dark backgrounds. Browser validation covers 390 variant decodes, 192 animation tracks,
2,472 duration-boundary samples and all 130 stored pose selections. Exact crop reconstruction and color/mask atlas
extraction pass for every frame. Fine markings remain an AI interpretation of the source.

To rebuild offline, run `python3 level_generation/creatures/mm8_m636/rebuild.py` from the repository root.
Review changed contacts and renew the evidence hashes in `review/decision.json`; acceptance is deliberately not
automatic. Run `browser_checks.py`, then `finalize.py` in this folder, and finally
`python3 level_generation/creatures/inventory_remaining.py`. The retained decision and acceptance hashes detect stale
outputs. The saved Chrome wrapper can run browser checks when desktop sockets are blocked by the ordinary sandbox.
