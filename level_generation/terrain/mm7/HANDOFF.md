# MM7 restoration handoff

Read [the shared terrain workflow](../TERRAIN_RESTORATION_HANDOFF.md) first. This directory implements the
MM7 run explicitly requested by the user; the older handoff's planning-only authorization note no longer
applies to this run. MM6 accepted artwork, packages and map fixes have not been changed.

Current roads: [roads_v5/README.md](roads_v5/README.md), correcting the repeating fragments in
`test_img/1288.png`. It extends the [v4 MM6-mask/imagegen workflow](roads_v4/README.md) with
paired finished-art border strips. Do not restore the v4 fade to base artwork at shared edges.
Both east–west and north–south native close-ups are required; solid masks and gradient tests
alone missed this defect. Older road sections below describe historical iterations.

## Authoritative outputs and dependencies

- `RESTORATION_STATE.json` freezes the final manifest, validation, native review, installation and ZIP hashes.
- `runtime_x2/manifest.json`, iteration `mm7_complete_terrain_v5_road_joins`, owns the 116 finished filenames.
- `inventory.json` records all 13 native ODMs, source hashes, descriptor table and actual 127×127 rendered cells.
  `grids.json` stores resolved names. MM7 uses `terrain_tile_data_2.txt`, master tile 1, direct ids below90
  without MM8's direct-tile remapping. The per-map four lookup bases determine the remaining ids.
- Seven authoring materials: `masters/v1/materials/{dirt,grass,sand,snow,swamp,waste,roads}.png`.
  `prepare_masters.py` selects `raw/roads_v2.png` for roads; the original `raw/roads.png` is superseded.
  Other masters use their matching `raw/<family>.png`. Exact prompts are under `masters/v1/prompts/`.
- Four variants: `masters/v1/variants/{7dirt1,7dirt2,7swtylv1,7swtylv2}.png`, using generated variant
  artwork registered to the originals, inserted into the shared master only where native variants differ.
- `transitions/fields/*.npz` stores 512px `coverage` and `shade`. Shore shade has three colour channels;
  other shade fields are scalar. `transitions/masks/` and `shading/` are visual exports (neutral shade200).
- `transitions/edge_profiles.json` records connected coverage/shade profiles by material, axis and topology.
- Water inputs: `water/native_atlas.png`, `restored_atlas_raw.png`, `offset_atlas.png`, `seam_repair_raw.png`;
  prompts and reports are adjacent. Four-by-four atlas cells0–13 are animation frames; cells14–15 repeat0–1.
- `reports/review_stage.json` binds staged assets, fixture maps and the frozen executable. Native capture JSONs
  bind executable/settings/native-map hashes; `reports/review.json` binds screenshot hashes. `package.py` checks these along with source and output hashes.

Python helpers import the existing reviewed gutter/colour conversion functions from `../seam_repair/build.py`
and native two-material recovery from the MM6 transition builder. They do not edit those implementations.
No MM6 master is reused merely because of a similar name. A few MM7 diagonal road originals also exist in
MM6's texture directory; they are not accepted MM6 restored terrain assets and were restored as MM7 roads.

## Iteration findings

1. Match global colour moments to the native material, then inspect runtime-scale comparisons. AI output alone
   tends to add contrast or brightness, particularly water. Do not accept raw AI colours automatically.
2. The first cobble candidate had too many small stones. `roads_v2` restores the chunkier original scale.
   The foreground remains masked over dirt; do not replace road shapes with a full cobble tile.
3. Native MM7 sand coverage/contact recovery left non-neutral values well inside the material. Abruptly setting
   shade to1 beyond a48px cleanup radius created a visible contour. Fade recovery influence continuously
   between24 and48px instead. The same continuous cleanup is used for other material families.
4. A48px protected variant border trimmed pebbles near the native tile edges. The final variant insertion
   protects16px and approaches full weight over the next16px, retaining original pebble placements and shared edges.
5. Land/shore edge topology is determined by its two endpoint materials. Do not use centre coverage to split
   a single mixed-edge topology into two classes. Roads additionally need their centre-opening bit.
6. Screenshot `test_img/1284.png` exposed dirt slots in roads: per-tile hole filling misses gaps
   connected to the tile border, and a noisy median edge profile stretches those gaps inward. The v2 road
   recovery closes narrow channels at native scale (3px disk with edge padding), keeps the main connected
   silhouette and fills holes. Each shared road opening is one continuous span; after connecting profiles,
   fill enclosed holes and make coverage fully opaque more than 4 authoring pixels inside the silhouette.
   Preserve outer contours, caps, corners and contact shade. Never average final material RGB into edge strips.
   `check_roads.py` gates solid interiors, single-piece roads, continuous openings and joined-mask holes.
   All 19 roads changed; the other 97 runtime images and every accepted master remain byte-identical to v1.
7. Water's initial periodic residual correction passed a gradient test but retained visible bands. Half-offset
   visual review caught this. A second built-in imagegen call repaired the cross in each frame; periodic Poisson
   insertion and motion-aligned temporal filtering affect only the outer24px at256 resolution, preserving208² interiors.
8. Water validation must animate both sides: a shoreline at frameN must be compared with open water at frameN,
   not a static `7wtrtyl` fallback at frame0. The first checker incorrectly reported156 failures from that mismatch.
9. Native animation screenshot hashes do not repeat exactly: the engine's `outdoor_textured_fog.sh` adds a small
   continuous UV distortion with6/8/10-second periods on top of the discrete14-frame animation. There is no frame
   interpolation. The native check clusters visually equivalent states and checks recurrence around14×15/128 seconds,
   while requiring an unchanged land ROI. Preserve source timing and the existing renderer; do not change gameplay
   rendering to make a diagnostic hash test pass.
10. Native camera selection must consider slope, not only transition variety. The first Nighon and Deyja
    poses intersected steep terrain and were unusable comparisons. Prefer locally flat cells and initialize
    height above the highest of the four cell corners before ordinary movement settles the party.
11. A generic party dies in Shoals under the normal wetsuit rule. `fixture/shoals_party.json` equips merged item1406
    on every member. Death-movie captures are invalid terrain evidence. Never disable that gameplay rule for this task.

## Native review and launch

`prepare_review.py` creates `/tmp/openyamm-mm7-terrain-review` with a frozen executable and two flat map layouts,
`green` and `dry`, each in x1/x2 versions. Real maps use `original` and `enhanced`. Asset mounts preserve other
content; only fixture stages substitute the Emerald Island map. Production ODMs are never replaced.
The camera helper uses a real MM7 Emerald Island seed and a Fly buff for the elevated diagnostic poses.

```sh
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm7/capture_review.py --quality x1
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm7/capture_review.py --quality x2
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm7/capture_maps.py --quality x1
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm7/capture_maps.py --quality x2
```

Water's native capture uses `capture_gameplay.py` with name `mm7_water_animation`, worldmm7, map7out01.odm,
stage`green_x2`, `captures/shore.oysav`, `--diagnostic-flying`, and `water/animation_actions.json`.
The60-image timed burst covers more than two frame cycles; subsequent movement/turn views check changing sampling.
Run `review_animation.py` afterwards. See capture JSONs for the actual settings and frozen binary hash.

Keep an original/reference view beside each new capture. Some original map transitions are misarranged;
report them separately, retaining exact map/row/column. A complete filename inventory is not proof that every
original map layout is seamless. Captures cover representative views, not every angle or graphics driver.

The runtime ZIP can be overlaid into a development asset root. `install.py` installs only the terrain category
alongside originals and checks existing-file conflicts. `play.sh enhanced` activates x2 terrain in the isolated
real-MM7 stage; original usesx1. Main repository settings and unrelated enhanced categories are preserved.

Installation updates may replace files owned by the previous installed manifest only when their existing
hashes still match that manifest. Unknown or locally modified conflicting textures remain protected.

## Road edge v3 (1285.png)

The user wanted MM6-inspired irregular edges, explicitly not a perfectly smooth outline.
`road_contour()` smooths signed distance with sigma4 at 512px authoring size, suppressing only
small native stair steps. A bounded 3px displacement favours stone shoulders over mortar in the
accepted master. Broad native bulges/notches remain. Keep the largest connected road silhouette
and remove detached fragments after connecting profiles; fill interior holes as in v2.
`road_contact()` provides narrow, local contact shading (6 authoring pixels falloff; 20% earth-side
and 10% stone-side maximum darkening), following the corrected contour. Shared edge shade profiles
are connected exactly like coverage. Neither RGB material is blurred or regenerated.

Reference comparison: `reports/road_edges_v3/comparison.png` (MM6 accepted / MM7 v2 / MM7 v3).
The new `road_close` native pose checks the straight arm from near ground level, alongside the
existing crossing/cap fixtures. V2 input manifest and straight road/mask are preserved under
`reports/road_edges_v3/before/`. Only the 19 MM7 roads change; the other 97 PNGs remain unchanged.

For pose-only review edits, `review_stage.json.assets_updated_ns` records the actual last texture
staging time. `package.py` uses it for capture freshness; replacing staged textures must refresh that
timestamp too. A full `prepare_review.py` rebuild omits it and uses the new stage report time.

## Current road v4: actual MM6 silhouettes and AI border detail

V3 was rejected in 1286/1287: smoothing small steps did not fix the larger sawtooth silhouette.
Follow [roads_v4/README.md](roads_v4/README.md) for the current road-only rebuild, exact imagegen prompts,
source masks, border-band extraction and shared edge appearance. It supersedes the road v3 algorithm
and pilot exports. All nonroad terrain, master materials, water and MM6 assets remain unchanged.

V4 validation additionally runs `roads_v4/review.py`: all 19 generated source/prompt/layer hashes are
recorded, all authoring pixels at least 40px from the road contour have zero AI residual, and the
outer 4px at every tile join have zero AI residual. The protected area includes road and dirt
interiors. Opposing masks and contact shading are still shared. Never average high-gain RGB ratios
from opposite AI edges: different stone/dirt placement can create bright streaks. A smooth fade of
the border residual to the unchanged base fields avoids that without blurring master textures.
