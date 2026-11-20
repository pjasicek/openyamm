# Four original Monga Melon patches

Status: all four patches have local native appearance, support and representative click/reload review.

Keep original source cells 4 (3,1), 4 (8,4), 4 (14,3) and 8 (1,4), using sprite 31's green fruit and purple foliage as
the visual reference. These are the four original quest-food pickup sites, separate from Nibbler's reserved future
growing ground. Food grants and the source Electrapede challenge remain deferred; no actors or encounter records.

`prepare_melon_patches.py` keeps every original center and gives each six irregularly arranged fruit, low vines and
eighteen leaves. Each rigid fruit fits the actual ground independently; low stems/leaves follow the quantized terrain.
The deterministic variations affect shape, angle and placement without making a symmetric planted grid.
`author_melon_patches.py` creates the source meshes. Native-sized `mm5melon.svg` and `mm5vine.svg` use muted rind/leaf
colors; narrow stems reuse the existing green bottle material. No native pickup/container descriptor is imported.

The [V2 study review](../review/melon_patch_study_v2/source_review.json) follows a correction to sparse V1 foliage:
the revised patches add leaf stalks and leaves along each vine. Three individual views and all eight views in the
contact sheet were inspected. Study meshes stay inside the reserved footprint.

The [integrated source review](../review/melon_patches_v1/source_review.json) confirms that all four OBJ files and
the two new bitmaps match the inspected study; all 281 preceding referenced models remain unchanged.
One existing decoration, `meadow_plants/024`, moved from (−2192, −19480, 477) to (−2133, −19504, 474), retaining
its identity. Its approach clearance improves from 96 to 155 units, above the required 128. All four approaches pass.
The refit retains 698 scenery records, all 55 orchard identities and fifteen total moves, with no unresolved records.
`review_melon_patches.py` checks native bindings, fruit contact and terrain edges during build. The completed native
checkpoint has 285 models, 116 handlers, 699 entities including start and zero actors/spawn records.
The [native review](../review/melon_patches_v1/native_review.json) records all four local game appearances and the
southwest patch's real named click/reload. Exposed saved health, food, gold and inventory remain unchanged.
Native fruit contact gaps are 0–0.875 units and foliage edges do not intersect the terrain. Broad country planting,
regional art/composition comparison and the black void rim remain unfinished; local prop review does not accept them.
