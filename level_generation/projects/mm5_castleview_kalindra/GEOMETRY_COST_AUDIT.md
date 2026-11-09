# Castleview–Kalindra geometry cost audit

This records the pre-simplification baseline. See [implemented simplification](GEOMETRY_SIMPLIFICATION.md) for current counts and review evidence.

The best first candidates are the **Skyroad rope and four melon patches**: together they account for 6,284 triangles,
13.4% of the map's model triangles, with substantial geometry devoted to fine strands, stems and leaf details.
That is their current cost, not a promised saving. Preserve the large architectural silhouettes and settlement layout.
This is an audit of the accepted environment, not a simplification pass or a frame-rate certification.

## Evidence and scope

[Inventory JSON](review/geometry_simplification_v1/before/review/geometry_cost_audit/inventory.json) records every native model, its source OBJ hash,
semantic assembly, polygon/triangle counts, texture usage, bounds and geometric screening metrics.
[Model CSV](review/geometry_simplification_v1/before/review/geometry_cost_audit/models.csv) is sorted by triangle count.
The same census covers native Ravenshore and Garrote Gorge models. Reproduce it from the repository root:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/audit_geometry_cost.py
```

The accepted MM5 ODM SHA-256 is
`87c61c78629b56761ad46ff0280d35a5129238f6f34b3f576f5b49e107e57f24`.
No source geometry, native map, event, runtime setting or delivery package was changed by this audit.

| Measurement | MM5 map | Ravenshore | Garrote Gorge |
| --- | ---: | ---: | ---: |
| Stored model faces | 26,171 | 6,095 | 2,848 |
| Stored model triangles | 46,814 | 14,372 | 6,907 |
| Nonzero triangles with area below 64 native square units | 5,016 | 54 | 20 |
| Share below that area threshold | 10.71% | 0.38% | 0.29% |

All **326 source/native model pairs have identical face and triangle counts**. There is no count inflation from
export-time splitting. The MM5 census found **zero zero-area fan triangles**. It does not detect all possible overlap,
occlusion, winding or collision defects; equal counts are not proof that every polygon is useful.

Triangle counts follow the renderer's polygon fan, `vertex_count - 2`, in
[OutdoorRenderer.cpp](../../../game/outdoor/OutdoorRenderer.cpp). The small-area threshold is a screening heuristic;
it is not a screen-pixel measurement or an automatic defect. Close interaction props can legitimately need small faces.

The [whole-map comparison](review/geometry_comparison_ravenshore/README.md) includes the shared 32,258-triangle
terrain baseline: MM5 totals 79,072 stored terrain/model triangles versus Ravenshore's 46,630, or 1.70×.
The model-only ratio is 3.26×. Invisible model faces account for 530 MM5 triangles and remain in the stored totals here.
Billboards, actors, water overlays and additional render passes are outside these counts.

## Prioritized inspection

Counts below are complete semantic assemblies or repeated families, not arbitrarily selected native chunks.
Shares use the 46,814 stored model triangles. Priority reflects visual return and likely change risk, not just size.

| Priority | Family | Instances | Faces total | Triangles total | Model share | Inspect first |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Skyroad rope and brace | 1 | 1,158 | 2,348 | 5.02% | Helical strands, coils and lashings |
| 1 | Monga Melon patches | 4 | 2,448 | 3,936 | 8.41% | Box stems/stalks, leaf fans |
| 2 | Town chests | 5 | 550 | 1,150 | 2.46% | Closed boxes for straps, hinges and keyholes |
| 2 | Kramer's caravan yard | 1 | 709 | 1,432 | 3.06% | Wheel hardware and canopy joints |
| 2 | River/islet bridges | 2 | 1,348 | 2,688 | 5.74% | Repeated bay joints and concealed caps |
| 3 | Roofed source wells | 6 | 1,074 | 2,232 | 4.77% | Bucket and small hardware |
| 3 | Message bottles | 4 | 328 | 688 | 1.47% | Rolled-paper interior and lip steps |

**Correction to the previous comparison:** 612–622 faces described melon patches and the barbarian camp, not wells.
Each roofed source well has 179 faces / 372 triangles. The separate secret town well has 79 faces / 166 triangles.

### 1. Skyroad rope

[Authoring source](author_skyrope.py) constructs three helical strands with 36 segments and six sides, plus a
32-segment lower coil, a 24-segment upper wrap and another 24-segment trunk lashing. The hanging-rope model alone
has 994 faces / 2,008 triangles; its brace/lashing adds 164 / 340. Rope material accounts for 2,304 triangles.
Of the assembly's 2,348 triangles, **2,214 (94.3%)** fall below the area screening threshold.

In the [existing native view](review/gameplay/mm5_skyrope_front_v1.png), the hanging line, attachment and bottom coil
establish the object. Fine twist detail contributes much less at that distance. Prototype a simpler cord with fewer
length segments and texture-based twist, keeping readable coils and a credible attachment. Preserve the Skyroad
interaction identity, accessible contact and intended future arrival. A close view must still read as rope.

### 2. Melon patches

Each patch in [author_melon_patches.py](author_melon_patches.py) has six fruit, 18 leaves, six two-segment vines and
18 leaf stalks. The six fruit cost 480 triangles; 30 closed box stems/stalks cost 360; leaf fans cost 144.
Across four patches, 945 triangles are below the area threshold. The larger cost also comes from repeated construction.

The [existing native view](review/gameplay/mm5_melon_southwest_v1_context.png) supports retaining the striped fruit
and recognizable leaves. Simplify narrow stems/stalks first, then leaf fans; avoid removing fruit merely to meet a quota.
Keep all four original contact sites and their IDs, six fruit per patch, terrain contact and approach visibility.
A future alpha-cutout plant treatment needs its own art, picking and lighting review; it is not an automatic swap.

### 3. Chests and caravan

[Town chests](author_town_chests.py) use closed geometry for feet, seam, raised straps, strap ends, hasp, keyhole and
hinges. In the [existing chest view](review/gameplay/mm5_chest_mayor_v1.png), the arched lid and metal straps give useful
identity; a black keyhole does not obviously need a six-face box. Review flat hardware and concealed ends first.
Keep the curved silhouette, grounded feet and interaction surfaces.

Original MM8 chests in both reference maps have **19 faces / 38 triangles**, versus **110 / 230** here.
They are smaller: a reference chest is 96×64×80, while the authored body is 192×112 with a taller arched lid.
This is evidence of economical original construction, not a requirement to impose the original polygon count or copy it.

[Kramer's wagon](author_camps.py) uses four 12-segment wheels. Each wheel has rim surfaces, six boxed spokes and
a boxed hub: 90 faces / 180 triangles, or **720 triangles for four wheels**, about half the whole caravan assembly.
The [existing wagon view](review/gameplay/mm5_kramer_context_v1.png) shows that wheels and canvas curvature matter.
Inspect hidden spoke/hub ends and repeated canopy-hoop joints before reducing wheel silhouette. Contiguous closed
canopy slabs warrant an overlap check; this audit has not established that their caps are duplicate faces.

### 4. Bridges

[Bridge authoring](author_bridges.py) creates ten native chunks per crossing with repeated deck, rail, beam,
post and pile geometry, plus terrain-fitted landings. Each complete crossing has 674 faces / 1,344 triangles.
For comparison, each complete reference bridge comprises **two** chunks totaling 128 faces / 334 triangles:
Ravenshore model pairs 85+86 and 87+88, and Garrote Gorge 33+34.

The authored/reference bridges differ in span, supports and terrain fitting, so the roughly fourfold triangle ratio
does not imply a fourfold waste. Inspect bay interfaces, buried ends and repeated closed rail joints. These remain
source inspection candidates, not confirmed invisible-face savings. Preserve walking width, rails, collision,
landing diagonals and grades; repeat both directions of each bridge walk after any change. Do not flatten the ramps
or merge distinct functional faces merely to reduce counts. No new bridge visual capture was made for this audit.

### 5. Wells and bottles

[Roofed well authoring](author_source_wells.py) includes stonework, roof, posts, windlass, rope and an open bucket.
The bucket alone uses five wooden and seven metal boxes: 72 faces / 144 triangles. In the
[existing well view](review/gameplay/mm5_well_royal_v1.png), the rim hides much of that detail while the roof and
windlass remain important. Inspect bucket hardware before simplifying the whole well.
The original unroofed MM8 wells have 51 faces / 110 triangles, but are about 256 wide and 216 high versus the
roofed source wells' approximately 352-wide, 432-high form. These are different architectural objects.

[Message bottles](author_message_bottles.py) cost 82 faces / 172 triangles each. The paper roll accounts for
25 faces / 54 triangles; 96 triangles per bottle fall below the area threshold. The
[existing bottle view](review/gameplay/mm5_bottle_queen_v1_context.png) clearly reads through the green bottle outline
and protruding paper. Review interior paper surfaces and extra lip/profile steps while retaining those cues and
the open-rim appearance at close range. At 688 triangles for all four, this is a lower absolute priority.

## Geometry to preserve unless further evidence warrants change

Castle Kalindra has 4,266 triangles, Western Tower 1,520 and Ellinger's Tower 1,104. Their large scale, varied rooflines,
belts, parapets and landmark role give their geometry a stronger purpose than tiny prop hardware.
The town curtain totals 2,220 triangles across 62 chunks spread around the perimeter; that does not make it 62 buildings.
The barbarian camp's 622 faces / 876 triangles include cloth and supplies, and deserve a targeted view before any cut.

[Architecture authoring](author_architecture.py) subdivides walls at 128-unit horizontal and 256-unit vertical
intervals for materials, windows and corners. [Castle authoring](author_castle.py) also builds intentional projecting
belts and parapets. Only consider merging coplanar faces where material, UV continuity, events and face attributes
are compatible with the native format. The source currently disables coplanar merging; do not globally enable it
without checking regenerated native bindings and visual seams.

Keep the terrain grid, terrain transitions, water continuation and outside-travel buffers. They fulfill layout and
visibility requirements. Their cost should not be reduced by making the world edge visible. Do not reduce foliage
density on the basis of this model census: billboards were not measured by it.

The MM5 map uses 65 unique model texture names versus Ravenshore's 131. This census supplies no reason to remove
material variety across the city. Unique names do not measure decoded memory, animated frames, residency or filtering
cost; texture upscaling remains a separate evaluation.

## What still requires runtime measurement

No frame timings, draw calls, GPU memory, load-time or collision-time profiles were collected in this audit.
The renderer batches geometry by material/animation/translucency and, for lightmapped geometry, lightmap page.
**BModel counts and unique texture counts are not draw-call counts.** Fewer triangles may help, but the current totals
alone cannot identify a CPU/GPU bottleneck or establish whether a player will notice an improvement.

For a performance comparison, hold binary, settings, resolution, camera, time/weather and asset version constant.
Capture the market/fountain view, castle approach, wooded Skyroad view and river approach; include a traversal for
streaming/load or frame-time spikes. Record CPU/GPU frame time, submitted geometry/draw calls and memory where
instrumentation supports them, separating model geometry from billboard/overdraw cost. Use release behavior on
Android if that platform is assessed. Historical screenshots or software-renderer FPS are not a hardware benchmark.
Ravenshore also has live actors and gameplay absent from the placeholder MM5 environment, so full-scene performance
is not a controlled geometry-only comparison.

## Follow-up acceptance criteria

If simplification is requested, start with one rope variant and one melon-patch variant, then review before propagating
changes. Re-author project sources and regenerate through the established [rebuild workflow](REBUILD.md).
Do not edit generated Lua or substitute original MM8 BModels.

For each changed family, compare near, normal approach and distant native views under identical settings. Require
retained silhouette, original-asset atmosphere, terrain contact, UV scale and readable interaction cues. Check picking,
collision and the affected walk routes; preserve semantic IDs and all 121 status-placeholder handlers. Re-run the
relevant binding/grounding checks and this census, then record measured savings and any timing improvement separately.
Update delivery hashes only after the revised map passes its required reviews.

The images linked above were inspected from existing review captures; they are historical object-level evidence,
not new screenshots certifying every aspect of the current release. In particular, historical background/edge
rendering is outside this audit's visual findings. No optimization or new visual acceptance run was performed.
