# Terrain restoration handoff: MM6 results and the next MM7 run

Terrain decoration expansion: [installed MM6–MM8 map settings, artwork and validation](decoration_rollout/README.md)
records the inspected MM6/MM7/MM8 x2 packs, map-specific densities, reusable families, new-art needs and
implementation/validation steps. This is a proposal; active decoration content remains New Sorpigal only.

Development installation verified 2026-09-13: all accepted packs are now in
`assets_dev/worlds/{mm6,mm7,mm8}/terrain_x2/` (134, 116 and 239 PNGs respectively).
MM6's missing installation was added from its frozen accepted export; existing MM7 and MM8 files
match their current export manifests, including MM8 v13 roads. Normal repository-root launches use
these packs with `[video_quality] terrain=x2`. File hashes are recorded in
[DEVELOPMENT_INSTALLATION.json](DEVELOPMENT_INSTALLATION.json). Settings and maps were not changed.

Workspace cleanup: see [retained sources and removed diagnostics](CLEANUP.md). Current user-accepted MM8 roads are [v13](mm8/roads/v13/README.md), installed also as `assets_dev/worlds/mm8/textures_v2`; older MM8 revision descriptions below are historical.

MM8 lesson from1300/1301: never average unlike diagonal edge colours into accepted straight-road tiles. It creates repeating ghost stones despite passing boundary metrics. Current [v10 repair](mm8/roads/v10/README.md) restores clean non-diagonal assets and fits repainted diagonal endpoints to them. Review both repeated straight directions and native connections.

MM8 diagonal-road correction after1298: [v8 notes](mm8/roads/v8/README.md). Recover native footprints **and stone structure**; generated detail must not move the road or individual stones. Review repeated paths and the exact native camera, not just tile thumbnails. Native endpoints can still need colour harmonization: v8 uses native diagonal samples and a12px colour correction, with no coordinate warp or donor-strip graft. Both orientations, road entry/exit, walking views and Alvar were checked; v7 visual acceptance is superseded.

This is the starting document for a future terrain agent. Read it before following older project READMEs.
Last consolidated: 2026-09-09. Paths and links here are relative to `level_generation/terrain/` unless stated otherwise.
This handoff records completed MM6 work and a proposed MM7 workflow; it does not authorize starting MM7 generation.

## MM8 restored terrain pack

The reviewed239-texture MM8 pack is installed alongside originals. Current `mm8/roads/v7` repairs the
joined stone neighborhoods rejected in1297 and matches shared road endpoint colours. Four diagonal
images were reconstructed;32 other roads receive border-only colour correction. Their interiors and
shapes are retained. Review covers both supplied poses,13 walking samples, entry/exit and Alvar.
See `mm8/roads/v7/README.md` and its `visual_review.json`. Map names alone do not imply different road textures. See [`mm8/HANDOFF.md`](mm8/HANDOFF.md),
[launch instructions](mm8/README.md), [comparison gallery](mm8/review.html), [map guide](mm8/MAPS.md), and
[runtime ZIP](mm8/mm8_complete_terrain_x2.zip). Coverage is all14 outdoor maps:197 effective static names
and42 liquid-animation frames after scene-overlay audit. The raw ODM-only count of196 missed Shadowspire's
required grey-dirt base. The exact union passes24,428 compatible joins; original incompatible map placements
are preserved. `mm8/WORK_STATE.json` and `mm8/reports/completion_audit.json` record completed delivery verification. MM6/MM7 content remains unchanged.

## Completed MM7 restoration

The subsequently authorized MM7 restoration is documented in
[`mm7/HANDOFF.md`](mm7/HANDOFF.md), with its [comparison gallery](mm7/index.html),
[116-texture runtime pack](mm7/mm7_complete_terrain_x2.zip), and [launch instructions](mm7/README.md).
It covers all 13 MM7 outdoor maps. The MM6 sources and accepted pack described below remain unchanged.

## Current deliverable and evidence

The authoritative complete MM6 export is
[`mm6_remaining/transitions/runtime_x2/manifest.json`](mm6_remaining/transitions/runtime_x2/manifest.json),
iteration `mm6_complete_terrain_v1`. Its **134 PNGs** cover the **120 static texture names used by all 15 MM6
outdoor maps**, plus **14 water animation frames**. Runtime terrain is 2x: 128px native tiles become 256px.
Authoring materials/masks are normally 512px. Do not confuse this with the separate ESRGAN surface-texture packs.

- [Complete review gallery](mm6_remaining/transitions/index.html) and [runtime ZIP](mm6_remaining/transitions/mm6_complete_terrain_x2.zip).
- [Build/provenance](mm6_remaining/transitions/reports/build.json),
  [compatible-join validation](mm6_remaining/transitions/reports/validation.json),
  [native capture evidence](mm6_remaining/transitions/reports/review.json),
  [installation audit](mm6_remaining/transitions/reports/integration.json).
- [Frozen source/manifest hashes at this handoff](MM6_TERRAIN_HANDOFF_STATE.json).
- [Original all-map inventory](mm6_remaining/inventory.json). Its “71 missing” count is the historical baseline;
  those 71 files are now generated and included in the complete pack.

The complete pack contains the previous **63 accepted New Sorpigal files byte-for-byte**, plus five masters,
60 material-to-dirt transitions and six extra cobble roads. The older 63 files are 36 land tiles, 12 RGBA shoreline
overlays, a water fallback and 14 animated water frames. The five added families are sand, snow, cracked,
tropical and swamp. Swamp's teal channels are opaque painted material, not another animated-water family.

Historically, at the original consolidation, `./level_generation/creatures/mm6_peasants/play.sh enhanced` loaded the complete 134-file pack
from `/tmp/openyamm-sorpigal-peasants-playtest/enhanced`. The main repository
`assets_dev/worlds/mm6/terrain_x2/` had no terrain PNGs installed; this was resolved on 2026-09-13 as recorded above. Repository `textures_x2/` contains bmodel/indoor
surface upscales and is a different asset category. Always inspect the actual launcher, asset root and quality setting.

Installation added 71 PNGs, preserved the previous 63, and verified 4,002 other files/symlink entries unchanged.
The installer source is [prepare_playtest.py](../creatures/mm6_peasants/prepare_playtest.py).
`--terrain-only` now uses the complete pack. It preserves the reviewed New Sorpigal map correction and checks source,
validation, capture and executable hashes. Restart the game after changing assets.

### Acceptance boundaries

The complete pack has **1,526 compatible join checks with no failures**, master repeat/offset visual reviews,
flat island/hole layouts for all five added families, six road comparisons, and five native family captures.
The unchanged older pack retains its **332 corrected-map joins across all 14 water frames** and native animation evidence.
These are content checks, not proof that every map cell, viewing angle, mip level or GPU configuration was tested.

The native map scan found **184 distinct incompatible neighbour pairs at 375 placements**. See
[CSV](mm6_remaining/transitions/reports/native_layout_mismatches.csv) and the original/restored examples in the gallery.
Those placements are not repaired by this pack. Never claim that every original map layout is seamless merely
because compatible tile assets pass. A separate reviewed 12-cell New Sorpigal correction predates the complete pack;
do not generalize it to other maps or silently overwrite maps that have further changes.

## Which source versions to use

| Asset | Current authoring source | Notes |
| --- | --- | --- |
| Dirt, grass, volcano, cobbles | `mm6_new_sorpigal_dirt_fidelity/transitions/seam_repair/materials/{dirt,grass,volcano,cobbles}.png` | Accepted periodic material phase; cobbles is a foreground material, not an entire road tile. |
| Sand, snow, cracked, tropical, swamp | `mm6_remaining/masters/v3/materials/*.png` | Only tropical changed from v2; the other four v3 files are byte-identical to v2. |
| Original New Sorpigal land coverage | `mm6_new_sorpigal_dirt_fidelity/transitions/masks/connected_v4/*.png` | Preserve polarity, orientation, disconnected flecks and inward corners. |
| Original land edge appearance | `mm6_new_sorpigal_dirt_fidelity/transitions/edge_treatment/layers/v1/*.npz` | Accepted linear RGB deltas. A v1 layer name does not imply that current finished composites are v1. |
| Final old land exports | `mm6_new_sorpigal_dirt_fidelity/transitions/edge_treatment/runtime/v2/*.png` | 36 files, carried unchanged into the full pack. |
| Water art | `mm6_new_sorpigal_water/restoration_v3/` | Keep only its 15 water runtime PNGs when assembling a new pack; its combined directory also contains obsolete land/shore art. |
| Final shoreline overlays | `mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/` | Shorelines v2, including broad damp-bank detail; twelve RGBA exports. |
| Added 66 transition variants | `mm6_remaining/transitions/{masks,fields,shading,authoring}/` | NPZ fields are authoritative floating-point coverage/shading; shading PNG neutral value is 200, not 255. |
| Exact final runtime union | `mm6_remaining/transitions/runtime_x2/worlds/mm6/terrain_x2/*.png` | Prefer this union for installation, not a mix of historical “latest-looking” directories. |

The earlier dirt-fidelity [HANDOFF.md](mm6_new_sorpigal_dirt_fidelity/transitions/HANDOFF.md) and
[HANDOFF_ASSETS.json](mm6_new_sorpigal_dirt_fidelity/transitions/HANDOFF_ASSETS.json) remain useful provenance for
51 locked files, but their remaining-shoreline tasks are completed. Older `seam_repair/`, water-v1/v2,
master-study and dirt-v4 trials are historical comparisons. Do not run their installers to select current artwork.
Folder version numbers describe local iterations, not one global chronological sequence.

## Art direction learned from the user

The goal is the original game's appearance with more definition, not photorealism, stronger lighting or a redesign.
Preserve broad value, saturation, feature scale and painted treatment. Compare original and restored renders at the
same camera, lighting and settings; a pleasing isolated texture is not sufficient.

- Dirt needed to return to the original's darker, fuller character. A lighter or conspicuously stamped dirt master
  can dominate a whole map. Reuse the same accepted dirt in every dirt-bearing transition and shoreline.
- Grass was accepted relatively early. Do not replace an accepted family to “match” a later bad candidate.
- Volcano initially became darker than the original; monitor the original's lighter overall value.
- Cracked ground needs the original's larger plates/cracks; fine dense crack noise changes the material's scale.
- Tropical needed larger interleaved patches, then removal of artificial serrated outlines and bevel-like dark rims.
  The fix was varied, broken painted edges, not blurring all detail.
- Sand/snow share broad dune-like forms, but native references still govern their colour, relief and transitions.
  Sand's broad ridges require special care: quilting suitable for fine grass can visibly cut dunes apart.
- Water initially became too bright and had a different fine pattern. Final water follows the original palette,
  broad waves, order and timing; modern-looking bright water was not the desired result.
- Cobble masters supply stone material **on top of the underlying terrain via a road mask**. Preserve road width,
  corners, T-junctions, crossings, end caps and detached end stones. Never fill an entire road tile with cobbles.

Imagegen prompts should state these constraints positively and include native references plus the accepted related
materials. Inspect inputs first and follow the available imagegen skill. Retain exact prompts, raw returned images,
source hashes and selected derivatives in the project. Do not depend on conversation images or generated-image cache
paths remaining available. Use built-in generation unless the user explicitly authorizes another API route.

## Failure modes and fixes

| Symptom | Actual lesson | Working reference |
| --- | --- | --- |
| Blurry grid lines on grass, dirt and water despite equal outer pixels | Averaging/mirroring opposite strips erased detail and introduced an inner band. Adjacent wrap pixels should be consecutive samples, not forced equal. | `seam_repair/build.py`, historical README |
| Sand shows cut ridges inside a tile while border statistics pass | Periodic donor quilting is not universal. Half-offset the image to expose the bad cross; paint a connected guide, then use periodic Poisson insertion over a limited band. | `mm6_remaining/masters/v2/repair_sand.py`, `raw/sand_offset_input.png`, `raw/sand_repair.png` |
| Tropical looks like raised camouflage/puzzle pieces | The defect was painted into the raw image, not caused by tiling. Correct the art while retaining palette and segment scale. | `mm6_remaining/masters/v3/raw/tropical.png` and `prompts/tropical.txt` |
| New shore or grass edge looks cut out | Coverage alone does not reproduce native contact shadow, damp earth, interleaving and fringe. Keep coverage separate from edge appearance. | dirt-fidelity edge layers and `transitions/shorelines/bank_detail/` |
| Shore earth does not match inland dirt | Separately generated shore dirt had different grain/phase. Composite accepted periodic dirt beneath local edge treatment; protect inland pixels. | final shorelines v2 |
| Brown cracked material is classified as dirt, or vice versa | Similar-colour two-material fitting is ill-conditioned. Use native topology and spatial confidence, not colour projection alone. One MM6 NW corner needed an explicit verified correction. | `mm6_remaining/transitions/build.py`, `crkdrtnw` case |
| Grey road stones gain little dirt holes | Original road dirt/stones did not share the base images' sample phase. Use the distinct source chroma and hole filling for this family, with restored cobble material underneath. | same builder, roads branch |
| Thin water lines survive offline seam repair | Runtime clamp sampling can be wrong for a periodic water surface. Existing fix uses repeat for water and clamp for land/shore via two samplers of the same array. | water restoration v3; inspect current renderer/shaders before changing anything |
| Animation evidence flashes or camera falls | Monsters can cast spells into a test; flying movement state alone does not survive all save round trips. Use an empty fixture and a real Fly buff for elevated poses. | shoreline capture notes and camera helper |
| A fresh preparation undoes the good result | The installer still points to an older pack. Update the authoritative manifest/source and validation binding, not only the temporary runtime folder. | peasants `prepare_playtest.py`, complete `integrate.py` |

Useful screenshot history: 1263/1267 dirt fidelity; 1264 native edge bleed; 1269 blurred tile-border lines;
1273–1274 water fidelity; 1278 local water seams; 1280 missing shoreline bank shading; 1281 sand internal seams;
1283 restored dirt next to uninstalled original sand transitions. Screenshots now used by the user may be under
`test_img/`; follow an explicit supplied path and repository image-resolution instructions rather than guessing.

## Materials, masks and edge appearance are separate assets

1. Make a master genuinely periodic before fixing transitions. Use 3x3/5x5 repeats, a half-tile offset, original/new
   side-by-side views and multiple display scales. Distinguish a recognizable repeated motif from a broken boundary.
2. Keep one sampling phase for each accepted material across every dependent tile. Do not rotate or scale dirt
   independently to make a particular shore look nicer. Rotate topology only when native evidence supports it.
3. Record each side's material order and crossing profile. N/S read left-to-right; E/W read top-to-bottom,
   without automatic reversal. Outer and inward corners are different. Four-way corner endpoints must agree.
4. Share both coverage and edge appearance profiles between compatible sides. Matching masks with mismatched
   shaded RGB still gives seams. Repair fields near borders, not broad strips of finished RGB.
5. Composite colour in the appropriate colour space and keep local shading/fringe separate. The original MM6 land
   used imagegen-derived linear RGB deltas. The later 66 variants recovered scalar coverage and shading from originals.
   Those are two supported case-specific approaches, not a requirement to AI-generate every mask.

For source tiles that really are registered composites of two known native materials, the later builder fits
`original ≈ wd * native_dirt + wm * native_foreground`, with nonnegative weights. Coverage is `wm / (wd + wm)`;
brightness/contact shade is estimated separately. It transfers these fields onto the restored materials rather
than pasting original low-resolution grain over the new art. Exact source matches and spatial confidence suppress
spurious interior mixing. Snow keeps broad soft coverage; tropical/swamp preserve irregular shapes.

This is **not a general MM7 segmentation guarantee**. Differing material phase, similarly coloured bases, baked
additional materials, palette keys and unusual corners need inspection or targeted imagegen extraction. Do not
copy MM6 thresholds, the `crkdrtnw` exception or its road chroma threshold into a new world without evidence.
Keep original colour references alongside mask/shading previews and record unresolved cases.

MM6 border parameters are worked examples: fine-detail quilting changes the outer 64 authoring pixels and retains
central 384px; field profiles typically lock 8px with a narrow 24–32px approach. Sand's repair preserves central
352px. Existing road openings use horizontal interval `[145,371)` and vertical `[136,372)` at 512px. These numbers
must remain fixed when extending the MM6 set, but MM7 requires its own measured contract.

### Export and filtering

For MM6, common authoring is 512px and runtime is 256px. Material gutters wrap; directional coverage/shading fields
extend their compatible boundary profiles. Do not wrap a mixed tile's opposite material into its filter gutter.
The existing reduction pads 8 authoring pixels, resizes 528→264 with Lanczos, and crops 4 runtime pixels per side.
Recheck the exported result: authoring-size success does not certify the runtime image.

Use premultiplied-alpha filtering for shoreline RGBA and meaningful hidden RGB near transparent edges. Shore alpha
represents land coverage over separately animated water; do not flatten it against blue water. The wider shore-v2
bank treatment is local (up to 80 authoring/40 runtime pixels), with inland dirt and coverage preserved. Do not
replace it with a uniform black outline.

## Water needs its own identity and animation review

Study the original frame family and overlay semantics before generating. MM6 uses fourteen frames with original
15/128-second frame duration; that is evidence for MM6, not a number to assume for MM7.
The accepted path restored a native frame atlas, registered fine detail with optical flow, bounded broad colour
changes, and retained original motion. Water-v3 then used a connected periodic guide/Poisson repair over the outside
24 runtime pixels, protecting central 208px, with motion-aligned stabilization. Keep its source/raw/flow scripts.

Check repeats and all shore orientations at every phase, including last→first closure. Compare motion-compensated
changes, not just raw frame differences. Use the same water phase where feasible for still comparisons; otherwise
state the phase difference. Frame-averaged seam statistics can hide a bad local join: preserve individual phase
measurements even when the acceptance statistic is over the complete cycle.

The existing water sampler fix is shared renderer work. Do not duplicate the texture allocation or add geometry to
solve a filtering issue. If renderer changes are necessary, review affected MM6/MM7/MM8 paths and bind new captures
to the new executable hash. An obsolete expected binary hash is not permission to bypass the check; establish fresh
review evidence for the new build. Software-display captures are not hardware performance measurements.

## Repeatable verification and feedback policy

The [original iteration policy](mm6_new_sorpigal_transitions/ITERATION_POLICY.md) has the fuller review rationale.
Its early counts and “water out of scope” statements describe that older land-only stage. Apply the following to the
new complete-world run:

- Validate filename coverage against decoded maps and descriptors, runtime dimensions, alpha semantics, source hashes,
  mask polarity and directional topology. Keep lookup failures explicit.
- Test every compatible side profile and corner combination, plus actual map adjacencies. A directional transition
  should not generally tile against itself; use valid closed islands, inward holes and road networks instead.
- Current MM6 screening uses local **16px windows**, sampled along joins, and compares gradient ratios with nearby
  and interior distributions. Boundary p95 must be below 1.25× interior p95, and boundary max below 1.25× interior
  p99.9. See the final checkers, not older whole-edge/1.75 thresholds. Do not loosen the threshold to force a pass.
- Always inspect the worst crops, full layouts, shifted masters and fine/broad detail. A numerical pass cannot
  overrule visible ridges, blur bands, halos, chopped cobbles or internal painted outlines.
- Render an empty native flat bench, then representative real slopes/coastlines. Include close/mid/far views,
  oblique directions and camera motion for filtering/mip shimmer; record which were actually checked.
- Hold executable, assets, camera, settings, weather/light/time and viewport fixed for meaningful A/B evidence.
  Hash captures and their inputs. `review.py` generally assembles/verifies saved captures; it does not launch new ones.
- Log each failure with image/crop, side/corner, material-vs-mask-vs-shading-vs-filtering-vs-placement diagnosis,
  current hashes, proposed change and protected invariants. Change one cause at a time.
- After two unsuccessful targeted retries, investigate the cause/constraints rather than blindly generating again.
  Reuse good raw outputs and repair locally. Recheck all affected dependants when a shared material/profile changes.

Keep original-map mismatches visible in a separate report with original/restored comparisons and coordinates.
Never mark an incompatible placement as a successful asset seam, or fix it silently as part of an art export.

## Rebuilding the capture environment

Repository source, not `/tmp`, is authoritative. The helper source is
[`mm6_new_sorpigal_transitions/prepare_capture_save.cpp`](mm6_new_sorpigal_transitions/prepare_capture_save.cpp).
[`build_pose_helper.py`](mm6_new_sorpigal_transitions/build_pose_helper.py) rebuilds
`/tmp/sorpigal-transition-capture-save` against the checkout's existing game libraries and CMake flags.
It requires the `build/tools/CMakeFiles/openyamm_levelgen_inspect_save.dir` build metadata. Check prerequisites
rather than assuming another agent's temporary helper still exists.

The complete MM6 [prepare_review.py](mm6_remaining/transitions/prepare_review.py) builds `dry` and `green` native
fixtures, copies enhanced content to an isolated review stage, installs reviewed textures there, excludes actor
scene overlays from the empty map, and creates Fly-buffed camera saves. It does not alter the main playtest.
Its two fixtures accommodate the four legacy tileset slots; a single fixture cannot simply install five arbitrary
families into four slots. The native hole fixture also needs a compatible outer ring when placed in surrounding dirt.

Example capture command from repository root, after preparing the MM6 review stage:

```sh
xvfb-run -a -s '-screen 0 1600x1200x24' \
  python3 level_generation/projects/brackenford_greywatch/capture_gameplay.py mm6_tropical \
  --world mm6 --map oute3.odm \
  --stage /tmp/openyamm-mm6-complete-terrain-review/green \
  --binary /tmp/openyamm-mm6-complete-terrain-review/openyamm \
  --start-save "$PWD/level_generation/terrain/mm6_remaining/transitions/captures/tropical.oysav" \
  --diagnostic-flying \
  --review-directory "$PWD/level_generation/terrain/mm6_remaining/transitions/captures" \
  --warmup 1 --seconds 0
```

For animated shoreline evidence, use an empty pool and timed capture actions, not a combat-populated town. For MM7,
use a real MM7 save/map and rebuild the relevant setup; do not transplant New Sorpigal IDs/party state blindly.

Original user camera references (New Sorpigal; positions are world coordinates):

| Purpose | Position | Yaw degrees | Pitch degrees |
| --- | --- | ---: | ---: |
| Overview | -11825.771, -12076.673, 1733.715 | 41.270 | -28.963 |
| Cobbles | -9247.492, -10485.380, 161.000 | 1.822 | -19.423 |
| Grass/dirt | -9429.897, -11473.650, 161.000 | 272.871 | -12.977 |
| Volcano | -12919.706, 13123.153, 1069.940 | 88.466 | -21.918 |
| Water fidelity | 1717.875, -8219.900, 838.091 | 17.292 | -27.932 |

## Starting the whole MM7 terrain task

Create a separate `level_generation/terrain/mm7/` project when that task is authorized. Do not overwrite MM6's
masters, exports or accepted review evidence. Recommended order:

1. **Inventory all actual MM7 ODM maps first.** Adapt [the MM6 inventory](mm6_remaining/inventory.py) with the actual
   [runtime lookup](../../game/maps/TerrainTileData.cpp) as authority. MM7 uses `terrain_tile_data_2.txt`, MM6 uses
   `_3.txt`, and the default world uses the unsuffixed table. Current code enables direct-master remapping only for
   the default world, not MM7/MM6. Read map `masterTile` and lookup bases; account for the runtime fallback for an
   out-of-range master tile. Do not assume every world's raw `<90` behaviour or table layout is identical.
2. **Map the full content set.** Record source hashes, raw→descriptor→filename resolution, rendered cells, per-map
   use and representative contexts; include road additions, animation frames, coast alpha, special materials and
   table aliases. The MM6 storage was 128×128 with 127×127 rendered cells. Verify this against the runtime for MM7.
   Do not equate every texture directory file with a used terrain tile.
3. **Audit potential reuse.** Match native art, sampling phase, palette and intended style, not just filenames or the
   fact that both worlds have grass. MM7 may have related or identical material shapes, but do not recolour MM6's
   pack blindly. Preserve correct existing shared content; generate missing distinct art only.
4. **Establish a representative native scene and cameras.** Capture originals before replacement. Use MM7 material
   closeups and a real overview as imagegen references. Define the fidelity target and runtime tier from originals.
5. **Prepare masters and pilot transitions.** Do the hard material families early; validate periodic masters, then one
   straight, outer corner, inward corner and representative road cases. Extract/paint coverage and appearance using
   whichever source-faithful approach the evidence supports. Freeze common profiles before expanding the batch.
6. **Generate the complete transition set.** Maintain a dependency manifest linking tiles to masters, masks, shades,
   versioned prompts/raw outputs and runtime hashes. Rebuild deterministically from retained inputs after repairs.
7. **Restore water and shorelines together.** Inventory original motion/keying, retain the correct earth master,
   verify repeat sampling, complete-cycle motion and stationary land. Don't defer shading until after installation.
8. **Run the structural, flat, native and real-map reviews above.** Resolve actual asset failures, report native
   placement contradictions separately, and keep measured evidence limits explicit.
9. **Package and install the reviewed union.** Write lowercase `worlds/mm7/terrain_x2/*.png` plus a manifest. Update
   the target launcher's authoritative source only within the requested installation scope. Audit other world art,
   sprites, decorations, sky, bmodel textures, settings, saves, map overlays and binary before/after. Do not use a
   broad “update everything” command to install a terrain-only change.
10. **Update this index and the MM7 handoff.** Record the final source union, hashes, review commands, pending cases
    and install locations. Mark older superseded documentation so another agent does not reintroduce a rejected pack.

These are workflow instructions, not an estimate of MM7 tile counts or a statement that MM7 terrain has already
been inventoried/restored. The completed MM7 ESRGAN `textures_x2` surface pack is independent work.

Optional grass/stone ground cover already has a separate MM6 experiment in
[mm6_ground_cover](mm6_ground_cover/README.md). Its terrain-decoration setting and per-map configuration are separate
from tile fidelity. First fix material/transition continuity; extra geometry must not hide a bad tile seam or become
an implicit requirement for the new world's texture pack.
