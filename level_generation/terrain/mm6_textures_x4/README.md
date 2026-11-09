# Complete MM6 x4+ master production

Active objective: prepare fresh, faithful x4-or-better master artwork for the complete MM6 texture inventory using
[the texture playbook](../TEXTURE_RESTORATION_PLAYBOOK.md). Do not count an enlarged ESRGAN image, a layout guide,
an undersized source crop, a generated-but-rejected candidate or an unchanged water carrier as new master artwork.

The queue retains all 1507 indoor/ODM building face names and the separately recorded 120 terrain names. Five names
are shared, giving 1622 distinct entries. Event-switched texture states are included. The static workflow applies to
BLV and BModel materials; terrain transitions and complete animated materials require their respective existing
workflows. Water, sky, special signs and unresolved native sources remain visible work, not completion exceptions.

`python3 level_generation/terrain/mm6_textures_x4/prepare.py` rebuilds the native catalogue and inventory, verifies
the preserved Temple master/prompt/export hashes and copies its 62 reviewed x4 exports into this isolated study.
It also verifies new selections in `selections.json`, including actual source/crop budgets and frozen runtime-review
hashes. The original archive under `reference/mmerge_data_forus/Data/mm6.bitmaps.lod/` supplies native layouts. Current x2
art is recorded separately for brightness comparison, never accepted as new x4 detail. Missing native originals
stay unresolved; do not infer their historical composition from a filename or silently treat an upscale as native.

Keep exact built-in imagegen prompts in `prompts/`, unaltered returns in `generated/`, comparisons and repeat proofs
in `review/`, and selected x4 exports in `exports_x4/`. `decisions.json` records family decisions and candidate
rejections. Each new selection needs real source/crop budgets, native fidelity, correct alpha, shared-background
ownership, required continuity and calibrated finish/brightness before isolated runtime checks. Shared material
families must retain the native period; finite artwork is not forced to tile. Native screenshots must use matching
normal/Torch Light or outdoor sun/shade camera states and honest tier/path receipts.

The imported Temple artwork has recorded Temple runtime comparisons; the inventory explicitly retains the limit
that other maps sharing its texture names have not all been inspected. Importing its verified artwork is progress,
not proof that every map appearance is accepted. Preparing references and recording a queue is not generation.

No renderer changes, production installation, release bundles or 3D assets are part of this authoring workspace.

Current selections: **82 prepared of 1622 names; 1540 remain**. The [second Goblinwatch comparison](review/second_batch/index.html)
adds faithful four-plank timber and a cave material that is an exact native/ESRGAN duplicate of the verified Temple
master. Its 24 native screenshots compare close, angled and medium views in normal light and Torch Light. Two
other candidate families remain unselected. This count describes prepared artwork, not installation or complete
visual approval of every map that shares it.

The [third stone-material comparison](review/third_batch/index.html) adds six names from three new constructions:
the slate/rose diamond floor (`oflr`, `oflr1`, `orflr1`), finite beveled granite panels (`t1c2`, `t1c3`) and warm marble
(`orceil`). Native and current ESRGAN hashes prove the exact aliases. Its 18 material pairs use matching normal and
Torch Light states in Goblinwatch and a visible ceiling in `6t1.blv`. The full receipt includes 48 native screenshots;
12 Goblinwatch niche-context views are excluded from material approval because a front panel occludes the marble.
Sampled brightness differs by about +1.1% for the floor, −2.0% to −2.3% for granite and −0.3% to +0.4% for marble.
`python3 level_generation/terrain/mm6_textures_x4/review/third_batch/verify_review.py` rechecks its frozen sources,
mounts, saves, captures, settings and 173 unchanged comparison carriers. Those ESRGAN carriers are not prepared art.

The [fourth granite-panel sampler](review/fourth_batch/index.html) adds four distinct 32-square materials:
`oflrd32`, `oflrl32`, `oflr1l32` and `orflr32b`, each exported at 128-square pixels. Registered fresh body cuts retain
the thin bevel and are assembled inside a four-pixel joint using the dominant native joint colour. The darker
earth redraw replaces an overly bright first crop; the excessively dark alternate brick-red crop remains unused.
Its 26 matched normal/Torch Light pairs include close tabletop views, with 52 native PNGs and frozen source,
mount, save, tier and capture receipts. The four temporary sampler bindings are explicitly labelled; original
niche/strip views were occluded and the canonical room assignments remain unchecked. Preparing this art does not
approve those original placements. `python3 level_generation/terrain/mm6_textures_x4/review/fourth_batch/verify_review.py`
checks the exact constructions and 94 unchanged ESRGAN context carriers. No sampler aliases are installed.

The [fifth granite-variant sampler](review/fifth_batch/index.html) adds three fresh masters and six exact native
duplicate names: `oflr1d32`/`orflrd32`, `oflr1l64`/`orflr1l64` and `oflrd48`/`orflr64c`. The first pair is native
32-square with 128-square exports; the other two are native 64-square with 256-square exports. Native and ESRGAN
hashes independently establish each duplicate pair. Its 18 normal/Torch Light pairs contain 36 native PNGs from
four matched runs. All selected body crops have sufficient actual pixels and retained finite joints; 95 unchanged
context carriers are excluded from prepared artwork. The pale material differs by about −1.9% in sampled native
brightness, and the two dark materials by about −8% to −9%. Wrong-palette, silver-bevel and excessive-brightness
returns remain unselected. Original narrow-strip placements and shared-map appearances are still pending; these
labelled samplers approve material appearance and native period only.

The [sixth original-map cave comparison](review/sixth_batch/index.html) adds `d6wlactr` (128×256 → 512×1024)
and `d6flora` (128-square → 512-square). Four matched runs provide 12 normal/Torch Light pairs and 24 native PNGs
in their actual `6d13.blv` assignments, without sampler bindings or geometry/UV changes. Exact selected centre-cross
repair strips retain each subdued fresh body; full repair returns are unused. Raw boundaries, source budgets and
x4 repeats were checked. Sampled wall brightness differs by about +5.2% to +6.5%, and floor views by −5.5% to +4.3%.
The 34 unchanged context carriers are excluded from prepared art; three terrain-only ESRGAN assets are explicitly
mirrored into both private BLV tiers at the same native period. Other shared maps and joins with unfinished grille
and root composites remain unchecked. No production installation is implied.

The [seventh grating study](review/seventh_batch/index.html) remains **unselected** and does not change the count.
Its separate fresh recess and plant layers have adequate source pixels and real alpha over the exact selected
plain-wall base. Seven original-map pairs contain 14 native PNGs. Recess samples remain about 16.5% brighter than
current ESRGAN, with whole-face samples about 33% brighter; native recess/plant appearance also needs correction.
Some alpha-1 stray pixels reach the otherwise empty tile bands. Bright-rim, sparse-plant and charcoal palette
drift returns are retained as rejected evidence. Exact prompts, sources, construction and matched-run receipts are
recorded. The two unfinished composite families remain candidates, not prepared exports.
