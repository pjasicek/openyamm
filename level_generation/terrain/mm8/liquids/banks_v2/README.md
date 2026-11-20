# Cleaned MM8 liquid banks

This candidate supersedes the original bank overlays for further review. Production installation remains pending.
It contains all 57 RGBA overlays; 25 runtime files change (12 dirt/water, 12 dirt/lava, and `trn`).

`build.py` rounds the native pixel stair steps in dirt-bank coverage using a narrow signed-distance filter.
Local topology checks preserve every foreground island and background hole; blocked changes restore original
coverage. Matching dirt masters, phase, and native dark contact shading remain the source of bank colour.

`trn` contains purple palette contamination beyond the exact magenta key. The repair removes estimated key
contribution near transparency, and replaces purple chroma inside opaque land with matching native substrate
chroma at the same mean brightness. It corrects 37 native pixels without turning opaque land into holes.

Reproduce from the repository root:

```sh
python3 level_generation/terrain/mm8/liquids/banks_v2/build.py
python3 level_generation/terrain/mm8/liquids/banks_v2/contexts.py
python3 level_generation/terrain/mm8/liquids/v1/check.py --banks level_generation/terrain/mm8/liquids/banks_v2
python3 level_generation/terrain/mm8/stage_candidates.py --grey-family --stepping-paths --liquids --banks-v2
```

`validation.json` records 8,134 compatible joins over all 14 liquid phases with zero failures and zero opaque-bank
phase movement. `review.json` binds the six inspected connected island/pool comparisons and current build hashes.
The comparisons show the previous candidate on the left and this candidate on the right. These are offline
composites, not proof of in-game movement or full-map coverage. Native captures use separate `_banks_v2` pose names
to preserve earlier liquid-body evidence. Controlled flat fixtures and final native review are still required.
