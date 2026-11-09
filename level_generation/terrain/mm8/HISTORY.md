# MM8 terrain restoration — active work

Authorized by the active thread goal. Follow [shared terrain workflow](../TERRAIN_RESTORATION_HANDOFF.md)
and [MM7 road v5 lessons](../mm7/roads_v5/README.md). Do not modify the accepted MM6/MM7 packs.

## Current verified scope

### Latest resume checkpoint (supersedes historical live-session notes below)

All13 selected enhanced flat land views completed and were visually inspected. Their saved-camera,
stage, screenshot and metadata hashes are bound in
[`fixtures/land_v1/review/visual_review.json`](fixtures/land_v1/review/visual_review.json).
The central connected fringes retain shading/interleaving without visible new rectangular joins;
the repaired volcano variant has no erroneous dirt frame. Outer fixture pads deliberately end abruptly.
The small red-dirt fragment is a native-context placement, not an invented closed island.

All six extra-bank captures completed and passed temporal screening. Both original/enhanced grey-water
patches and the plains-lava patch were visually reviewed; see
[`fixtures/banks_extra_v1/review/visual_review.json`](fixtures/banks_extra_v1/review/visual_review.json).
The fixtures contain all21 remaining bank names; screenshots inspect representative visible regions, not
all cells simultaneously. Grey patch1 is mostly dry land, so its motion ROI was moved to the visible
southern shore (750,720,1200,960), identically for original/enhanced, excluding HUD. Thresholds unchanged.
All six periods are1.595–1.606s with recurrence ratios0.116–0.176. Together with earlier12 bank captures,
all five bank families now have original/enhanced flat sampled-animation evidence.

`assemble_pack.py` exports all239 source-verified256px PNGs and provenance to
`complete_runtime_x2/manifest.json`. This is complete candidate coverage, not final acceptance/installation.
The historical runtime_x2 remains a partial build input. Production assets are unchanged.

The exact complete export now passes **24,428 compatible edge checks** across all197 used static names
and all14 liquid phases, including compatible cross-family contacts. `check_complete_pack.py` and
`reports/complete_validation.json` bind the239-file manifest. `write_map_list.py` generates [MAPS.md](MAPS.md)
from effective inventory with all14 map names/files and terrain families.

Eight original/enhanced grounded stepping walks are collected and visually inspected. Similar opposite-direction
views prompted a camera audit. The initially reported shared-stage race was **disproved**: the capture helper
already creates unique working directories and scenario IDs per capture name. Source and headless-prepared
saves retain the correct opposite headings; `reports/stepping_camera_audit.json` records their values/hashes.
Additional per-direction stage directories are now used. Historical captures archived under the poorly named
`fixtures/roads_v1/rejected_shared_stage_captures` are not evidence of a proven race; its note corrects that claim.

Actual GUI quicksave heading confirmation **passed**: west(-13568,-6400,1,yaw0),
east(-12544,-6400,1,yaw3.14159), pitch-0.4 for both. Retained GUI quicksaves are under
`fixtures/roads_v1/stepping_walks/`; `reports/stepping_camera_audit.json` binds their hashes/values.
The helper supports `--inspect <save>`. The camera question is closed; no capture sessions remain live.
All eight movement samples and six-frame sheets are retained; `review_road_walks.py --stepping --require-complete`
passes metadata and movement checks. Visual results are in `fixtures/roads_v1/review/stepping_visual_review.json`.

Remaining: selected cobble loop/diagonal original/enhanced views, production
installation/preservation, launcher, review gallery, shareable ZIP and final goal completion audit. All bank and
complete-union check processes are finished. Production assets remain unchanged.

`audit_effective_inventory.py` is now the coverage authority. Its `effective_inventory.json`
and `effective_grids.json` apply full-scene and ordered overlay environment settings before
resolving all14 maps. Shadowspire's `out06_1.scene.yml` sets master_tile2, making `gdtyl`
a used base. The original `inventory.json`/`grids.json` are raw-ODM historical build inputs;
do not regenerate them in place and invalidate older reports.

`inventory.py` resolves all rendered 127×127 cells in all 14 raw MM8 ODM maps. It follows
`game/maps/TerrainTileData.cpp`: direct nonzero IDs below90 are remapped by masterTile
through bases0/450/630; four remaining lookup blocks use36 entries; masterTile>=3 falls
back to direct indices. Invalid/pending rendered IDs fail inventory. Plane of Water uses
masterTile1, so MM7's direct-ID rule must not be copied unchanged.

- 197 effective used static names; 42 additional frames (14 water, 14 lava, 14 tar).
- One dependency-only native master: `rdtyl`. The former `gdtyl` dependency is required at runtime.
- Runtime goal: 239 PNGs; native128→runtime256. Hardware liquid frames already256 stay256 for the terrain array.
- No exact RGB/size matches found against MM6/MM7 native texture directories. This rules out byte-identical
  static-art reuse; it does not rule out careful reuse of matching topology or independently reviewed materials.
- `inventory.json` includes source hashes, descriptors, per-map counts, raw→descriptor resolutions,
  family classification, source palette0 and sample cell coordinates. `grids.json` has rendered names.
- `index.html`, `sheets/*.png` are ORIGINAL inventory sheets, not accepted restored outputs.
- Native stage: `/tmp/openyamm-mm8-terrain-review`; `prepare_native.py` freezes an executable and creates
  an original x1 stage. `capture_native.py` captures the named poses in `reports/native_stage.json`.
- `reports/protected_baseline.json` freezes settings and existing MM6/MM7 terrain checkpoints/installation.

## Art/semantics requiring special handling

- Brown dirt, green grass, porous dark volcano, striated grey rock, red layered sandstone,
  orange cracked desert base, orange sand, fine grey dirt and large grey stone plates are distinct materials.
- `rdnw` is a used red-dirt transition even though its native `rdtyl` master is never placed by itself.
- `drsr*` (19) and `gdrd*` (17) are cobbles on different substrates. Maintain solid stone coverage and
  continuous border artwork at shared openings; inspect both orientations at ground level.
- `plrd*` (12) are INTENTIONAL separate orange stepping stones. Keep native gaps and stone arrangement.
  Do not force them into a connected cobble strip or classify native stones as accidental fragments.
- Keyed liquid overlays: `wtrdr*` brown dirt/water; `wa*` grey dirt/water; `lvdr*` brown dirt/lava;
  `lv*` orange desert/lava; `tr*` grey dirt/tar. Magenta is transparent, not painted material.
- `surface_materials.yml` supplies the three14-frame sequences, each15ticks/frame. Runtime resolves
  liquid transition material from descriptor/base, so prefixes alone do not determine animation behavior.
- Several unused table families exist. Restore used names plus necessary dependencies; don't count unused
  table entries as missing shipped terrain. Document original incompatible map placements separately.

## Remaining work / completion gates

1. Inspect all original native captures; establish master/road/liquid references and save imagegen prompts/raw outputs.
2. Restore and visually validate periodic512px authoring masters and256px derivatives, including variants.
3. Recover/AI-extract coverage plus edge treatment, verify original topology/substrate assignments, pilot hard corners.
4. Expand all transition families and roads; preserve source shading/interleaving, avoid join fade-back fragments.
5. Restore all three liquid animations and five overlay families together; verify full cycles and land stability.
6. Build flat native fixtures, every-compatible-join tests and real-map paired captures, with both road directions,
   multiple scales/angles and movement checks. Iterate visible failures even if numeric checks pass.
7. Package/install only after full coverage and review; preserve other enhanced content. Add enhanced/original
   launcher, representative-map list, runtime ZIP, gallery, installation audit and final RESTORATION_STATE.json.

No enhanced MM8 terrain is installed yet. The goal remains active; inventory/captures are preparation, not completion.

## Ground master checkpoint

`WORK_STATE.json` records the active checkpoint. All14 original native material captures finished.
Ten ground candidates (including two dependency-only substrates) are generated under `masters/v1/`;
15 built-in imagegen results include five local repair attempts. Exact prompts, raw images, source receipts
and SHA256 records are retained. No API/CLI fallback was used.

`prepare_masters.py <families...>` deterministically builds512px materials and256px runtime candidates.
All ten currently pass both numeric self-seam checks; these are CANDIDATES, not final native acceptance.
Inspect `masters/v1/reviews/all_comparison.png`, individual repeats/offsets and reports.

- Dirt/grass/volcano/red_dirt/grey_dirt/plains use the existing periodic donor quilting.
- Plains' artificial blocky centre was repaired with imagegen and locally inserted within
  authoring rectangle[165,160,365,300], with24px blend; original exterior retained.
- Sand and grey_stone use AI half-offset repair with the reviewed periodic Poisson insertion,
  retaining central352px of the normalized master. Sand repeat now looks continuous.
- Native-template correlation found rock/sandstone output contained1.5 source repeats. Their current
  recipe resizes raw to768 then takes top-left512, restoring source feature size. Smooth periodic-component
  removal fixes remaining border jumps without averaging strips. Earlier raw `rock_repair.png` and
  `sandstone_repair.png` are retained but SUPERSEDED: they target the wrong feature scale.
- Exact old half-offset AI inputs remain `inputs/rock_offset.png` and `sandstone_offset.png`;
  current correctly scaled inputs use `_offset_scale_v2.png`. Never overwrite AI inputs with repaired outputs.
- Recheck the orange clod and volcanic pore sizes in native scenes: candidate plates/pores may still look finer
  than original. Numerical seams alone do not establish style/fidelity acceptance.

The checkpoint below supersedes that next-step list. Python here is3.8; avoid str.removesuffix.

## Land screening and road pilot checkpoint

The partial runtime union now has145 PNGs: eight used base masters, eight variants,
72 directional land transitions and57 RGBA liquid overlays. Neither roads nor liquid
frames/fallbacks are included yet. The two dependency-only masters remain authoring dependencies.

- `build_transitions.py` builds78 land transitions/variants and57 keyed overlays. Source material
  coverage and shading are separate float fields under `transitions/fields`; matching edge profiles
  are in `transitions/edge_profiles.json`. Liquid filtering is premultiplied float RGB/alpha.
- Grey stone requires special recovery: nearly collinear grey materials made unconstrained RGB fitting
  speckled. Luminance fitting with exact native-material anchors improves the masks, but visual review
  of `reports/grey_transition_pilot.png` still finds that rounded native fringe stones look too chipped.
  Correct this before accepting the family. Zero seam failures do not resolve this appearance issue.
- `build_pebble_variants.py` registers two generated pebble variants and inserts them over protected
  master dirt. `variants/v1/comparison.png` was visually inspected: native pebble positions retained.
- `check_land.py` screens90 opaque candidates (88 used names plus two dependency masters):
  **1,042 compatible joins, zero numerical failures**. Report and worst crops are under `reports/`.
  This report explicitly excludes roads, alpha overlays, animation, native placements and final coverage.
- Eight enhanced native captures completed. `reports/native_pilot_{dirt,rock}.png` and
  `native_pilot_review.json` record the appearance review: master tone and feature scale look promising.
  Actors/weather/combat differ, so these are not controlled animation or movement evidence.
  They used the143-file stage before pebble candidates were added. The old capture script did not bind
  candidate hashes at capture time; the unchanged stage was checked retrospectively. Updated
  `capture_native.py` now verifies and snapshots staged candidate hashes before/after every new capture.

### Roads: uninstalled pilots, not accepted outputs

`roads/v1/` contains five built-in imagegen results and their exact prompts/receipts.
Together with15 master and2 pebble calls, current retained total is22.

1. Initial `drsrew.png`/`drsrns.png` have usable detail but narrowed/shifted road footprints.
2. `_geometry_v2.png` outputs follow enlarged native geometry but copy its nearest-neighbour pixel blocks.
   They are superseded visual attempts, not restored runtime art. Avoid nearest-neighbour guides as
   the principal appearance target for this task.
3. `drsrew_definition_v3.png` uses a smooth native geometry reference, initial result as detail reference,
   and solid coverage guide. It removes the block grid but still needs measured geometry registration.

Rebuild pilot guides with `roads/v1/prepare_pilots.py`, then `compose_pilot.py` and `review_pilots.py`.
The compositor aligns generated road widths to native measurements (about222/228 authoring pixels),
normalizes stone palette, and protects shared dirt outside a narrow contact insertion. Straight masks
fill dark joints that touch the border: those joints must not become slots of earth. This envelope
logic is only for straight pilots; do not apply it blindly to bends or separate stepping stones.

`roads/v1/pilot_comparison.png` and `pilot_repeats.png` were inspected. Both masks have one component
and zero interior holes, but **both longitudinal RGB joins fail**, with visible chopped stones at
the repeated boundary. They remain in `roads/v1/runtime_pilots/`, outside the runtime union/stage.
Next repair the finished donor road artwork across joins (half-offset artwork correction and continuous
finished borders, following MM7 v5), then recheck both orientations before expanding the48-road set.
Do not fix this by fading back to a conflicting base mask or loosening the seam metric.

No MM8 terrain is installed. `reports/protected_check.json` confirms121 baseline files unchanged.
All three liquid animations, overlay/phase checks, controlled fixtures, movement reviews, complete
package/install/launcher/gallery/ZIP and final handoff remain required. The goal stays active.

## Current checkpoint: complete cobble candidates and native pilot

This supersedes the road-pilot failure checkpoint above. The current cobble union is
[`roads/v3/`](roads/v3/README.md), covering all19 brown-dirt and17 grey-dirt road names.
The12 orange stepping-stone paths remain unfinished and must retain their native gaps.

- Two local imagegen half-offset repairs reconnect the straight donor joins.17 other
  native shapes received individual restorations; four diagonal shapes then received
  local outline corrections. The total retained built-in imagegen count is now45
  (15 master results,2 pebble results,7 v1 road results,17 v2 shape results,4 outline edits).
- The road compositor's contour-stretching attempt was rejected because it folded
  diagonal stones. Active v2 composition quilts complete finished artwork through a
  minimum-error overlap cut; v3 inserts the four local outline repairs on both substrates.
- Grey bank treatment uses scalar shade and substitutes the grey master where rounded
  border stones expose brown earth. This removed the observed cyan/brown fringes.
- Runtime exports extend directional road artwork into filter gutters while exposed
  earth wraps in master phase. The opposite side of a mixed tile is not its neighbour.
- `roads/v3/validation.json`:724 compatible cobble/substrate joins, zero failures;
  every mask has one component and no interior holes. These are offline family checks,
  not acceptance of all terrain, all native layouts, movement or animation.
- `include_roads.py` verifies build/check hashes and merges36 candidates into the partial
  runtime union. `stage_candidates.py` has staged181 PNGs under the isolated enhanced
  review root. Production MM8 assets remain untouched;121 protected baseline files
  were rechecked unchanged.
- Native `roads_dirt` and `roads_grey` x2 captures finished with the updated script.
  Their metadata binds the181-file candidate manifest before/after capture and the
  screenshot hashes. `reports/native_road_pilot.png` and `native_road_pilot_review.json`
  record the visual review: crisper roads with comparable original tone/scale in
  Ravenshore and Shadowspire, without the prior cyan fringe. These are populated
  native stills, not controlled diagonal/two-orientation/movement acceptance.

Next: fix the grey-stone material fringe; restore12 stepping-stone variants and the
three liquid families (42 frames plus3 fallbacks); then complete controlled fixtures,
full join/native-placement/animation/movement reviews and the final238-file deliverables.
No background captures or generation jobs remain running at this checkpoint.

## Grey-stone local-art checkpoint

Four built-in restorations and deterministic local composites are now reviewed in
[`transitions/grey_fringe_ai/`](transitions/grey_fringe_ai/README.md). The rounded
native stones are preserved more convincingly than the earlier scalar-mask result.
Raw AI earth is too coarse, so the pilot retains accepted master dirt outside stone
neighbourhoods and normalizes native broad tone. The existing first16 runtime border
pixels remain protected; their chipped forms still need shared finished-art correction.
These pilots are **not copied into the runtime union or stage**.

The pilot substitution check covers1042 compatible land joins with zero failures,
but is explicitly not visual acceptance of the remaining old borders. Four exact
prompt/reference/output receipts bring retained built-in outputs to49. All121
protected baseline files remain unchanged. See the linked README for reproduction
and the nine remaining grey-stone names. The181-file stage and other outstanding
work listed above remain unchanged. No background jobs are live.

## Latest checkpoint: full grey-stone family and effective scene coverage

The preceding four-pilot checkpoint is superseded by
[`transitions/grey_family_v1/`](transitions/grey_family_v1/README.md): all13 non-base
grey-stone shapes now have individual built-in source restorations and shared finished
edge strips. Master-phase pure edges/corners and minimum-error overlap cuts replace
the old protected chipped bands. Thirteen native/candidate comparisons plus assembled
island/hole layouts were reviewed;1042 compatible land joins pass. These checks do
not certify all native layouts, controlled flat runtime fixtures or movement.

The effective scene audit found the raw-ODM inventory missed `out06_1.scene.yml`.
Its master_tile2 setting makes `gdtyl` required in Shadowspire. The new authoritative
coverage supplement is `effective_inventory.json`, with `effective_grids.json` and
`audit_effective_inventory.py`; target coverage is **197 static +42 frames =239 PNGs**.
Keep the older raw inventory as build provenance. The addition needs no new generation:
the accepted grey-dirt master already exists. No other map changes descriptor settings
in the audited full-scene/ordered-overlay environment data.

`stage_candidates.py --grey-family` stages182 PNGs: the older181-file union with13
grey-family substitutions and the additional `gdtyl` master. Production is untouched.
The union directory itself remains the historical181-file baseline; final assembly must
include these explicit overrides. The total retained built-in imagegen count is58.

Native capture debugging found that `--pose` after loading a flying save teleports the
party and reinitializes movement. `capture_native.py` now loads an explicit review save
without a second pose command and binds its hash/pose in screenshot metadata. The
project-local MM8 save helper adds saved flying state and a real Fly buff; debug-only
flight was insufficient. Early `grey_fringe`, `grey_fringe_overhead`, `grey_fringe_fly`
captures are rejected framing/altitude attempts, not acceptance evidence. The stable
`grey_fringe_saved` view exposed the missing base; `grey_fringe_complete_x2` verifies
that adding `gdtyl` removes the sharp restored/native boundary at that location.

The final `grey_fringe_detail` x1/x2 comparison is reviewed and recorded in
`transitions/grey_family_v1/native_review.json` and `native_comparison.png`. It shows
sharper rounded stones/contact shadows and no old/new square boundary, in a similar
broad grey palette. This is one elevated native neighbourhood, not all family tiles
in-game or movement acceptance. The report binds the182-file stage, effective inventory,
build, saved pose and screenshots. All121 protected baseline files remain unchanged.
No capture or generation jobs remain live at this checkpoint.

Remaining: controlled native flat/movement review,12 intentionally disconnected stepping-stone
paths,42 liquid frames+3 fallbacks and57 overlay/phase checks, controlled flat/movement
reviews and native adjacency audit, final239-file union/install/launcher/gallery/ZIP.

## Latest checkpoint: all12 desert stepping paths

[`roads/stepping_v1/README.md`](roads/stepping_v1/README.md) records the completed
candidate artwork/mask family, [review gallery](roads/stepping_v1/index.html) and
reproduction commands. There are24 retained built-in imagegen outputs, bringing the
run total to82. Each tile uses native-colour-matched restored stone paint, an individual
AI silhouette mask and native-derived contact shade over the accepted plains master.
Preserve the deliberately disconnected stones and all earth gaps; these are not solid
cobble roads. Reviewed native component counts are8–12, with no holes inside faces.

Two diagonal border shadow cuts were corrected: faint mask antialiasing is not a
physical stone crossing. All338 shared-earth pairs pass, and all84 native neighbour
pairs touching these paths pass at666 placements in Alvar. All12 native/raw/composite/
mask rows and repeat layouts were viewed. Cap/turn self repeats only screen earth
continuity, not connected path design. Original stone placements are broadly retained,
with some slightly rounder/inset outlines; do not claim pixel-exact silhouettes.

`stage_candidates.py --grey-family --stepping-paths` now stages194 candidates. The
historical OUT union remains181; final assembly must include the13 grey substitutions,
`gdtyl` and12 stepping paths. Production remains untouched; all121 protected baseline
files were checked unchanged.

Native `stepping_ew` and `stepping_ns_south` x1/x2 captures were visually reviewed and
bound to the194-file stage in `roads/stepping_v1/native_review.json`. They show clearer
flat stone striations and earth, similar broad palette/scale, and retained gaps. The
central `stepping_ns` view was rejected because a Troll Warrior obscures the terrain.
The east-west view includes ordinary projectile effects; it is not a controlled empty
fixture. Both original and restored views show some terrain triangle boundaries; this
is not diagnosed by these asset checks. Initial default-size Xvfb captures remained at
the cropped menu. Use `-s '-screen 0 1600x1200x24'` for the fixed capture controls.
All capture/generation jobs are terminal at this checkpoint.

Next work:42 liquid frames and3 fallbacks across water/lava/tar;57 overlay/all-phase
checks; controlled flat and movement review of all families, all-terrain/native layout
audit, final239-file assembly/install/launcher/gallery/ZIP and full completion audit.

## Latest checkpoint: complete candidate coverage and liquid motion pilots

[`liquids/v1/README.md`](liquids/v1/README.md) and its
[review gallery](liquids/v1/index.html) record3 new built-in imagegen atlas edits,
bringing the retained generation total to85. The conservative native-frame workflow
now supplies all42 animated frames and3 static fallbacks. Hardware frames remain256px
(already native256); static128px fallbacks become256px, matching x2 land. Native broad
colour/shape/motion remain authoritative, with bounded motion-registered AI detail.
All42 individual repeat metrics pass, without a new seam-repair atlas.

All57 RGBA bank candidates were composited against all14 phases:581 compatible pairs,
including cross-family shared pure edges and matching dirt/plains/grey-dirt masters,
give8134 passing checks. Opaque bank pixels remain exactly stationary. Visual bank
acceptance is **not complete**: dirt-bank outlines retain some blocky native key
contours, and tar banks transfer a few purple contaminated native key pixels. See
`liquids/v1/bank_visual_issues.json`; fix those while preserving the native irregular
islands/holes and dark rim, then recheck phases and connected fixtures.

`stage_candidates.py --grey-family --stepping-paths --liquids` now stages **239/239**
effective runtime names, with no extras. Production remains untouched. The historical
OUT union is still181files; do not mistake it for the complete reviewed source union.
Final assembly must retain all explicit staged overrides. All121 protected baseline
files were checked unchanged.

Native motion review had meaningful rejected attempts. Initial ground poses died from
liquid hazards; final screenshots show a death movie, and the lava burst includes
interrupted frames. Flying avoided drowning, but the Plane of Fire view had enemy fire,
and the first tar view landed on a building roof. Neither is animation acceptance.
Final saved native poses are `liquid_water_flying`, `liquid_lava_alvar` (over12000 units
from authored spawns), and `liquid_tar_pool` (outside expanded bmodel vertex bounds).
Their original/enhanced captures each retain40frames at0.1s intervals, covering over2
native cycles. All6 temporal screens pass near the expected1.640625s cycle. Actual
image variation is required, preventing a static roof from passing.

The3 native original/restored still comparisons and enhanced sampled motion sheets
were visually reviewed; the three liquids retain native broad palette, feature scale
and progression. `liquids/v1/review.json` binds those images, the full-stage capture
hashes and `native_review/motion_measurements.json`. These are stationary flying
native pilots, not controlled empty flat fixtures or ordinary camera movement.
No generation, capture or build processes remain live at this checkpoint.

Next: bank contour/key cleanup; controlled flat fixtures and movement for all terrain
families/roads/liquid banks; complete native placement/mismatch audit; final union,
production installation, enhanced/original launcher, representative maps, gallery,
shareable ZIP and requirement-by-requirement completion audit. Keep the goal active.
# Cleaned-bank checkpoint

## Latest: context triage and eight road walks reviewed; land captures running

`review_native_contexts.py` generated24 pages covering every one of the286 metric-failing native pair types.
All pages were visually inspected against original3x3 layouts. `reports/native_contexts/visual_review.json`
records pre-existing placement discontinuities and no additional replacement defect requiring repair.
This closes the offline context triage; it does not replace native in-game or animation checks.

Road movement session9934 is terminal. `review_road_walks.py --require-complete` collected all eight routes,
and all eight six-frame sheets were inspected. Matching earth, continuous stone artwork and restrained outlines
hold in both directions along both axes; see `fixtures/roads_v1/review/visual_review.json`. Original fixture
comparisons, native diagonal pads and stepping-path flat/movement evidence remain outstanding.

`prepare_land_fixtures.py` compiles seven material families. The shared staging/capture scripts now accept
`--land`. Closed island/pool networks use only available used corner tiles. Sandstone lacks the island topology;
red_dirt lacks both closed networks, so native-context pads provide those cases. Every family also contains
master repeats and native variant pads. Masters are placed at row32 to avoid overlaps with variant pads.
`stage_bank_fixtures.py --land` creates206 available poses; this is a camera catalogue, not a requirement to
capture206 views. A13-view enhanced batch is running as **session42502**: grass/volcano/rock/plains_sand/grey_stone
island+hole, sandstone hole, red_dirt rdnw, and corrected voltylx native pad. Poll before restarting.

No production installation yet. All121 protected baseline files remain unchanged. Final coverage union,
remaining visual gates, installation, launcher/gallery/ZIP and final handoff audit still remain required.

## Latest: bank review complete for three families; road movement running

All12 bank fixture captures are complete and `review_bank_motion.py --require-complete` passes. Tar original/
enhanced pool and island comparisons plus both enhanced six-frame sample sheets were inspected. Matching grey
earth, dark fringe, stationary banks and absence of purple contamination are recorded in the visual review.
Scope is shore_dirt, lava_dirt and tar_grey; shore_grey and lava_plains are not covered by those three fixtures.

`prepare_road_fixtures.py` compiles three empty flat fixtures covering all48 used road names:19 dirt,17 grey,
12 separate stepping paths. Dirt includes capped cross and closed loop; grey uses loops because its actual used
set lacks the cross and some caps. Every tile also has a5x5 native-context pad. A tile at the native map edge
(`gdrdecap`) retains all available native neighbours, with outside-map space explicitly filled by plain substrate.

The existing staging/capture tools accept `--roads`; `stage_bank_fixtures.py --roads` prepares120 available
poses (not120 required captures). Camera helper now accepts `--grounded` and clears Fly for ordinary movement.
Two initial enhanced grounded views (dirt west, grey south) were inspected and show coherent stone outlines.
`capture_bank_fixtures.py --roads --walk` captures12 forward steps from each grounded pose, preserving distinct
`_walk` output names. Eight enhanced axis/direction routes are running as **session9934**. Poll before restarting.
These are sampled movement steps, not continuous video. Grounded helper is rebuilt and available under `/tmp`.

Contract triage of the286 remaining native metric failures found **zero failures between compatible edges**.
`reports/native_join_contract_triage.json` identifies66 ordered incompatible contract combinations for contextual
review. Do not silently classify all as acceptable merely because their edge types differ; inspect representative
native layouts and distinguish original placement discontinuities from replacement defects.

## Latest: volcano correction staged; water/lava flat review complete

The candidate union now includes `--volcano-variant`. Its shared volcanic edges pass all compatible checks and
the three native-layout comparisons remove the erroneous dirt frame while retaining native interior patches.
The placement audit after this repair reports 286 metric candidates, one newly failing: `volxse S voltyl`,
an existing partial dirt corner meeting solid volcanic ground (see `variants/volcano_v2/context_26_96.png`).
The other previously noted variant/corner mismatch is also visible in original layout. These observations do
not exempt the other 286 candidates from contextual triage.

Eight original/enhanced water/lava flat captures completed and pass `review_bank_motion.py` temporal checks.
Four enhanced island/pool sampled-frame sheets were visually inspected; see
`fixtures/banks_v2/review/visual_review.json`. No claim of ground-level movement acceptance yet.

Capture session4934 terminated on a disk-full error during the first tar view. Shortly afterward about30GB
became available and temporary test directories disappeared externally. Repository evidence remained intact.
The frozen executable was recovered from `build/game/openyamm`, whose hash still matches the original.
`stage_bank_fixtures.py --restore-snapshot` recreates temporary mounts from retained runtime hashes and camera
saves while preserving the original fixture manifest. It was used successfully; do not replace that manifest
with the newer volcano union or invalidate earlier bank captures. Only the four incomplete tar views were
restarted as **session61349**, last verified running after original tar pool completed. Poll that session first.
The old disk-full partial tar frames are superseded by the retry, not accepted evidence.

`review_bank_motion.py --require-complete` is the completion gate for all12 flat-bank temporal samples; inspect
tar visually after capture. The original/enhanced main stage was rebuilt with the current239-file union.
The camera-save helper under `/tmp` was removed by the external cleanup and needs rebuilding with
`build_pose_helper.py` before preparing new poses. Existing retained camera saves are valid.

## Flat fixture and native placement follow-up

`stage_bank_fixtures.py` mounts six isolated configurations and creates twelve empty-world camera saves.
`capture_bank_fixtures.py` captures explicitly named views with optional `--cycle`, binding fixture and terrain
hashes. `reports/bank_fixture_stage.json` lists names and paths. The first enhanced dirt/water pool view was
visually inspected: unobstructed bank, matching dirt, no visible rectangular tile joins. The eleven remaining
views were launched as one batch; last verified session **4934** was running after original water pool/island
captures. Poll the same handle or inspect live processes before restarting anything. Staged fixtures contain
their own texture copies, and retain the cleaned-bank union independently of later candidate revisions.

`audit_native_joins.py` screens all **1,897 unique pairs / 448,056 placements** in the fourteen effective grids.
It found 304 metric review candidates, ten newly failing against original art. Nine of those involve `voltylx`:
the old automatic corner classification incorrectly treated this volcano patch variant as directional terrain,
introducing dirt on volcanic borders. `repair_volcano_variant.py` reconstructs its native interior patches with
pure volcanic borders; `variants/volcano_v2` is visually screened but **not staged**. Eighteen of nineteen native
pair types touching it pass. The remaining `voltylx E volxsw` is one native mismatched placement in elemf, also
failing with original art. Inspect its native context and the other audit candidates; do not certify them from
their historical presence alone. Re-run the full placement screen after staging any repair.

The bank capture run does not yet constitute completed animation review. All-family flat/movement tests,
native placement triage, final union, production installation and deliverables remain required.

The current isolated 239-file stage includes `liquids/banks_v2` (57 overlays, 25 changed runtime files).
See [the cleaned-bank notes](liquids/banks_v2/README.md) and its hash-bound `review.json`.
All 8,134 phase joins pass, opaque banks remain stationary, island/hole counts are preserved, and the visible
purple-pixel diagnostic for `trn` is zero. Six connected island/pool comparisons were visually reviewed.
This is offline acceptance; final installation and full native acceptance remain pending.

`prepare_bank_fixtures.py` compiles three empty flat maps under `fixtures/banks_v2/`, described by
`reports/bank_fixtures.json`. Each has a central 5x5 land island and liquid pool from the reviewed layouts.
The surrounding liquid test pad has a deliberately abrupt outer boundary; review the central bank network,
not that fixture boundary. These fixtures still need isolated mounting and native capture/movement review.
Do not mount native out01 scene overlays on them. Keep production maps and settings unchanged.

The `_banks_v2` native pose aliases preserve previous capture evidence. The water pose is partly obscured by
a landing craft, and the Alvar lava pose shows liquid body rather than a bank; neither proves bank acceptance.
Use the compiled empty fixtures for the decisive bank review. All 121 protected baseline files were rechecked
unchanged after staging and fixture compilation. Goal remains active.
