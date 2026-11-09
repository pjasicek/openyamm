# MM7 male elf peasant — complete staged restoration

Validated 84/84 native frames across descriptors 340–348: five standing views, 40 walk poses,
30 recoil poses, four fidget poses, four falling poses and one corpse. Five native `nf0..4`
poses are retained as unused frames; all 79 referenced frames are covered without adding playback entries.
All 13 base sheets were generated once through built-in imagegen. Exact prompts, references,
raw outputs, selected checkpoints and dimensions are recorded in `generation.json`.

The original brown leather vest, burgundy trousers, blonde ponytail, empty hands and sheathed
hip dagger are retained. Nine native appearances (59, 60, 61, 62, 333, 334, 339, 340, 341)
share one enhanced base and soft RGB8 masks: R trousers, G hair, B zero. Fixed native-index
RGB matrix fits preserve shading; palette 59 is an exact bypass. Skin, leather, brass and
boots remain protected. `variants.py` records component selection, soft boundary filtering
and explicit falling/prone hair corrections. Missing trouser-leg coverage and separated
ponytail coverage were corrected after reviewing all 756 frame/palette combinations.

Native 256×256 logical canvas, bottom pivot (128,256), scale 0.799988 and Center flags are
preserved at 2 physical pixels per logical pixel. Views 0–4 are stored; 5–7 use native mirrors.
Every native timing entry is 125 ms. Standing holds one pose; walk/attack/shoot share the
eight-step walk cycle. Hit uses five poses. Death reuses the first two hit poses followed
by four falling poses, then holds its final pose. Corpse holds. Fidget uses fa, fb, fc, fd, fc, fb.
Native action-specific view reuse and all descriptor/palette bindings are preserved.

The base and matching RGB8 mask page are 2048×3574. Decoded resident base plus mask and packing
is 51,236,864 bytes (48.86 MiB); pre-baked variant previews are offline review assets.
The offline `viewer.html` embeds native palettes and deterministic enhanced variants.
These are staged art and metadata; no original assets or gameplay installation were changed.

Review covered every native/restored pose, all 756 variants, every mask overlay, ordered
animation sequences and native timelines. Browser captures verify a mirrored white-trouser
walk and the white-hair falling pose. Foreground extraction was corrected to preserve burgundy
fabric interiors. Confirmed pink ear/finger/boot residue was repaired from nearby interior hues
before and after resizing without changing alpha. Final magnified light/dark edges show no
visible matte fringe. The numeric audit retains 40 cleaned and 2 atlas chroma candidates,
principally intentional burgundy contour colors; the score alone is not the acceptance criterion.
`validation.json` passes source hashes, full coverage, unclipped raws, exact reconstruction,
atlas extraction, mask weights, base bypass, variant alpha and native timing/flags.

Reproduction from saved checkpoints (repository root; run sequentially):

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m332 --tone .80
python3 level_generation/creatures/mm7_m332/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m332
python3 level_generation/creatures/mm7_m332/review_variants.py
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m332
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m332
```

Processing script hashes are recorded with settings. Reuse the accepted package; any regeneration
invalidates acceptance hashes and requires review of affected outputs. Generated fine details
are an interpretation of the native low-resolution art, not recovered original high-resolution pixels.
