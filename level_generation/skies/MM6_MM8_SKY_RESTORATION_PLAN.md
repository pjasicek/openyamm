# MM6–MM8 sky restoration: inventory and execution plan

Updated 2026-09-09. **The user accepted MM6 `6plansky1` pilot v3_local after the seam repair; remaining native-sky jobs have not started.**
See the [current pilot gallery](mm6/6plansky1/review/v3/index.html) and [reproducible review/play instructions](mm6/6plansky1/README.md).
The pilot is isolated; it has not enabled or installed a complete production x2 tier.
Follow-up screenshot `1290.png` exposed an unresolved original-game sky/fog presentation mismatch in both x1 and x2.
The pilot uses the correct native image; x1/x2 consistency alone does not establish original-MM6 horizon fidelity.
See the [follow-up review](mm6/6plansky1/review/feedback.md).
Future jobs must apply the [pilot lessons and review requirements](#lessons-from-the-6plansky1-pilot).
The continent lists now explicitly use native MM6/MM7/MM8 assets. The user confirmed the correction works in-game:
“OK this works.” See [selection rationale](SKY_SELECTION.md). This confirms the source-selection fix, not acceptance
of any new restored artwork. Use the corrected native x1 rendering as the comparison baseline.

This document is the current execution handoff. The inventory, pipeline, per-image review/revision loop and install
rules below supersede the old 13-image merged-sky proposal. There are 19 current weather/custom images, one additional
scripted outdoor sky (`sky04`), and 64 distinct native sky images across the complete restoration backlog.

## Deliverables and scope

- [Visual inventory](audit/index.html): native previews for all inventoried textures.
- [Readable inventory and every map](audit/INVENTORY.md).
- [Full inventory](audit/inventory.json): source hashes, dimensions, exact pixel duplicates, references,
  installed x2 hashes, map coverage and a provisional restoration queue.
- [CSV](audit/inventory.csv) and [provisional installation paths](audit/install_plan.json).
- [Rebuild script](audit/build_inventory.py): Python 3.10+ and Pillow, reuses `util/map_export.py`.
  Run `python3 level_generation/skies/audit/build_inventory.py` with those dependencies available.
  It writes only the audit folder; it does not edit native assets, settings or maps.

| Coverage | MM6 | MM7 | MM8 | Total |
| --- | ---: | ---: | ---: | ---: |
| Native sky-art files | 27 | 26 | 12 | 65 |
| Outdoor maps parsed | 15 | 13 | 14 | 42 |
| Indoor maps parsed | 51 | 63 | 47 | 161 |
| Additional non-sky textures on sky-marked faces | 1 | 1 | 0 | 2 |

There are **64 distinct native sky images**, after removing one exact MM6 duplicate. Three additional files
under `worlds/mmmerge/textures` duplicate existing world images. Including those and the two ancillary surface
textures, the audit has 70 source-file records / 66 distinct RGB images. Pixel hashes include dimensions:
a 256px and 512px version of the same composition are not silently treated as interchangeable.

There are sky-art references on **21 indoor maps and 3 outdoor maps' bmodel surfaces**. Outdoor sky rendering
also applies to the 42 outdoor maps. All 203 native maps parsed without errors. All native ODM sky header strings
and scene YAML `sky_texture` fields were empty in this checkout; merged tables supply the current outdoor choices.
No saved games, DDM/DLV persistent-state overrides, user mods, packaged ZIPs or external original-game archives were
parsed. Generated Lua and the authored MM6 common event module were scanned for literal sky/texture changes.
This is a development-content inventory, not proof of every dynamic runtime state.

## Source selection: corrected and user-confirmed

The [original screenshot](../../test_img/1289.png) exposed a palette mismatch: the old Enroth list selected MM8's
pale `plansky1`, while original MM6 has a deep blue sky. The old restoration correctly retained its supplied source's
palette, but that source was inappropriate for authentic MM6 presentation.

The correction is in `assets_dev/engine/data_tables/continent_settings.txt`. The existing loader tries the explicit
name first; the corrected native names resolve without changing renderer or global alias precedence. Keep all seven
slots, including duplicate native counterparts, so the weather-state count and weighting remain unchanged.
Map/custom/event overrides were preserved. The user has confirmed the corrected selection works.

Start with MM6 `6plansky1` / identical `6sky01`, using the native 512px BMP and producing 1024px x2 art. The user's
confirmation does not establish the original game's entire weather algorithm or an exact cloud-scroll phase.
Do not treat local MMerge/OpenEnroth references as proof of every original MM6 state, and do not copy their code.

## What the previous New Sorpigal work actually completed

- Source: MM8 `PLANSKY1.bmp`, 256 × 256; `worlds/mmmerge/textures/plansky1.bmp` is identical.
- Supporting reference: MM6 `6plansky1.bmp`, 512 × 512, darker palette.
- Built-in imagegen edit: [exact prompt](mm6_new_sorpigal/prompt.txt), raw output 1254 × 1254.
- Export: Lanczos downsample to opaque RGB **512 × 512**, without sharpening or palette correction.
- Installed: `assets_dev/worlds/mm6/textures_x2/plansky1.png`.
- Accepted export SHA-256: `a6db629efaca1289b267cc806ce11c6a187d871dd11ecbe31d591baf8f9e65d1`.

I inspected the native source, export, repeat sheet and horizon capture. The result preserves the muted source's
cloud bands and openings, with softer cloud edges. It is useful accepted **MM8-palette artwork**; it must not be
counted as completion of an authentic MM6 deep-blue sky. Keep it and its provenance intact, and give the native-MM6
restoration its own key/project. Do not merely recolour this result without checking cloud shape and native detail.

The previous outdoor renderer fix already uses logical dimensions for projection, preserving sky scale between x1
and x2. Its original screenshot predates that fix, so fresh x1/x2 comparisons must use the same executable.
The recorded edge means (x2: LR 2.48, TB 4.57 on a 0–255 scale) are diagnostic evidence, not a universal seam threshold.

Main `settings.ini` currently has `[video_quality] sky=x1` and `texture=x1`.
The peasants' private playtest installer now exports the six unique native MM6 skies at nearest-neighbour x2
for seven weather slots under `/tmp`. Existing private stages are updated only when that installer is run. Those are placeholders, not reviewed AI restorations or production assets.

## Inventory groups and provisional restoration order

The complete native-art backlog remains 64 distinct images even if current runtime selections change.
MM8-palette `plansky1` and native MM6 `6plansky1` now have user-accepted artwork results.
**62 distinct native images still have no user-accepted sky-restoration result recorded by this workflow**.
MM6 acceptance covers the repaired pilot artwork; the renderer/fog issue and production rollout remain open.
Existing ESRGAN assets require review rather than being assumed unacceptable.
These are output-image counts, not a promise that each needs exactly one AI call; shared layouts may support reuse,
while repair retries may add calls.

| Stage | Images | Work |
| --- | ---: | --- |
| A0 | 1 | Native MM6 `6plansky1` v3_local artwork accepted; identical `6sky01` shares its output. Isolated pilot only. |
| A | 18 | Remaining current outdoor weather/custom images; includes the already restored MM8 `plansky1`. |
| B | 3 | Legacy outdoor fallback assets: `sky01`, `sky05`, `sky6pm` (MM8). |
| C | 9 | Eight additional indoor/surface images and Frozen Highlands' scripted `sky04`. Include that event asset when completing MM6 coverage. |
| D | 33 | Remaining unreferenced native images, including unused/test variants; complete the archive last. |

A0 + A cover the 19 current outdoor weather/custom images. “Unreferenced” means no reference in this static audit,
not a declaration that the original games never used it. Stages are priorities, not restrictions against pulling a
needed event/surface asset forward to complete one world.

### Current outdoor selection

| World / continent | Ordered weather list |
| --- | --- |
| MM6 / Enroth | `6plansky1`, `6plansky1`, `6sky06`, `6sky12`, `6sky03`, `6sky04`, `6sky19` |
| MM7 / Antagarich | `7plansky3`, `7sky01`, `sky12`, `7sky02`, `sky12`, `7sky04`, `sky19` |
| MM8 / Jadam | `plansky3`, `plansky1`, `sky06`, `sky02`, `sky03`, `stormclds`, `stormclds` |

Each list has six unique native images. Together with `sunsetclouds`, current weather/custom coverage is 19 images.
Do not deduplicate the ordered lists. Only generation jobs for identical source images may be deduplicated.

| Native source directory | Names in the current 19-image union | Native → x2 |
| --- | --- | --- |
| `worlds/mm6/textures/` | `6plansky1`, `6sky06`, `6sky12`, `6sky03`, `6sky04`, `6sky19` | 512 → 1024 |
| `worlds/mm7/textures/` | `7plansky3` | 512 → 1024 |
| `worlds/mm7/textures/` | `7sky01`, `sky12`, `7sky02`, `7sky04`, `sky19` | 256 → 512 |
| `worlds/mm8/textures/` | `plansky1`, `sky02` | 256 → 512 |
| `worlds/mm8/textures/` | `plansky3`, `sky06`, `sky03`, `stormclds`, `sunsetclouds` | 512 → 1024 |

Custom sky overrides:

| World | Map | Current custom sky |
| --- | --- | --- |
| MM7 | Bracada Desert (`7out06.odm`) | `7plansky3` |
| MM8 | Dagger Wound Island (`out01.odm`) | `sunsetclouds` (also explicitly selected in runtime) |
| MM8 | Ironsand Desert (`out04.odm`) | `plansky3` |
| MM8 | Shadowspire (`out06.odm`) | `stormclds` |
| MM8 | Plane of Air (`elema.odm`) | `plansky1` |
| MM8 | Plane of Fire (`elemf.odm`) | `sunsetclouds` |

Frozen Highlands' winter state explicitly selects `sky04` through `MM6.ApplyFrozenHighlandsWinterState`.
This explicit event override was preserved, so its x2 coverage must include MM8-source `sky04` in MM6's consuming
world. The install inventory records that destination. Do not silently change the event's sky identity, fog or snow
while restoring assets. Any future event-specific native-art correction is a separate presentation change.
Weather enable/disable controls precipitation separately from the existence of the sky profile: do not omit a map
from sky coverage merely because its weather flag is disabled.

### Indoor, surface and archival coverage

Stage C adds MM6 `sky_clo1`, `sky_nit1`, `sky_nit2`, `sky_sns1`; MM7 `7plansky1`, `plansky2`, `sgstars`, `sky13`;
and MM8-source `sky04` for the preserved MM6 winter event. MM7 `sky19` and MM8 `sky02` are now covered by Stage A,
but their indoor/surface usages still need review. Native sizes and every affected map are in the inventory.
Examples include MM6's Arena, Temple of the Sun, Supreme Temple of Baa and Control Center; MM7's Celeste,
Grand Temple of the Moon, Temple of the Light/Dark and Lincoln; and MM8's Castle of Air and Prison of the Lord of Earth.

Temple of the Sun changes `sky_nit1` / `sky_sns1` through events, so a static ceiling screenshot is insufficient.
MM6 `orair256` and MM7 `7solid01` are **ancillary surface assets**, not cloudy sky art. Keep their existing x2 results
and their surface-animation/material behaviour; do not image-generate a new sky into a solid black face or an animated
magic surface. `orair256` animation dependencies belong to the surface pipeline and are outside this sky-image count.

All 65 native sky-art filenames remain in the CSV, including MM6 `6sky01`–`6sky19`, `sky20`, `sky21`,
MM7 `testsky1`, `testsky2`, `skycity01` and the less frequently used colour variants.
Visually similar MM6/MM7 skies have different dimensions and sometimes palette/detail. Group them as references,
but only identical dimension-qualified RGB hashes automatically share a generated output.

Exact duplicates:

- MM6 `6plansky1` = MM6 `6sky01`.
- MM6 `sky_nit1` = MMerge `sky_nit1`.
- MM7 `sky16` = MMerge `sky16`.
- MM8 `plansky1` = MMerge `plansky1`.

## Existing x2 assets and preservation

Besides the accepted MM6-installed `plansky1` alias, the audit found:

| World | Existing x2 files | Provenance / handling |
| --- | --- | --- |
| MM6 | `orair256.png` | Surface upscale; preserve. |
| MM7 | `7solid01.png`, `sgstars.png` | Surface upscales; preserve black fill and review stars before replacement. |
| MM8 | `cloudsabove.png`, `stormclds.png`, `sunsetclouds.png` | Existing ESRGAN-derived surface-pack exports; compare against AI candidates before replacing. |

The cloud assets' hashes match `tools/upscaling/out_prod_bmodel_mm8_x2/manifest.json`, whose records identify
ESRGAN x4 sources. They are not previously accepted built-in-imagegen sky jobs. Current hashes are recorded in the
audit for conflict detection and rollback; existence alone is not an authenticity verdict.

## Authoring workflow

Follow the applicable [imagegen skill](/home/pjasicek/.codex/skills/.system/imagegen/SKILL.md), the
[terrain restoration handoff](../terrain/TERRAIN_RESTORATION_HANDOFF.md), and the existing
[New Sorpigal sky project](mm6_new_sorpigal/README.md). The sky-specific requirements below take priority over terrain
mask/transition procedures that do not apply to skies. This task does not start a Blender/map-generation workflow.

1. **Freeze the right reference.** Record world, native key, exact runtime lookup, original BMP and
   palette, source SHA-256, native dimensions, affected maps and sky/surface usages. Store a lossless source PNG.
   Include related world variants as labelled references only. For MM6 use the native MM6 palette demonstrated by
   the original screenshot; do not substitute the merged game's muted version.
2. **Inspect before prompting.** Classify cloud tile, storm tile, sunset tile, stars or special surface. Compare broad
   cloud layout, blue openings, colour, contrast and density. The inventory's square assets are not panoramic skyboxes.
   Star textures need restrained point detail, not invented galaxies or added nebulae.
3. **Generate one independently reviewable image per job.** Use built-in imagegen edits with local native references;
   retain exact prompts and raw returned images. Do not use a large contact-sheet generation as the runtime master:
   it reduces per-texture control and can mix palettes. Reuse an accepted output only when the source identity supports it.
4. **Export exact x2.** Measure the returned image rather than assuming the requested size was honoured. Deterministically
   downsample to twice the source width/height, opaque RGB PNG, lowercase runtime filename. Most outputs are 512² or
   1024²; `plansky2` is 256² and `sgstars` is 128². No default sharpening or global colour grading.
5. **Check wrap and fidelity.** Original/restored side-by-side at equal display size; 3×3 repeats; half-tile offset in both
   axes; native-sized downsample; sky/horizon views in-game. Preserve large-scale layout and original gentle/bold colour
   as appropriate. Do not flatten all skies into one lighting style.
6. **Repair only demonstrated defects.** A prompt saying “seamless” is insufficient. Use the half-offset image to expose
   a seam and request a targeted imagegen repair preserving the rest. Avoid forced identical edge strips, mirror seams,
   blanket blur and Poisson processing as default steps. These caused visible grids in terrain work. If two targeted
   retries fail, investigate the constraint/source rather than blindly iterating.
7. **Record the decision.** Keep accepted/rejected versions, source and export hashes, generation mechanism, exact export
   command/tool version, comparison images, notes and target mapping. Never overwrite the accepted source project to
   hide a change in palette or runtime meaning.

Suggested project layout:

```text
level_generation/skies/<world>/<native_key>/
  source/                 # native BMP snapshot/hash + lossless viewable reference
  prompts/v1.txt
  generated/v1.png         # unmodified imagegen return
  runtime_x2/<key>.png     # deterministic, exact-size export
  review/                 # native/restored, offset/repeat, game captures, timing report
  manifest.json
assets_dev/worlds/<world>/textures_x2/<key>.png
```

Cloud prompt template (customize every bracket, omit constraints inappropriate to stars/special surfaces):

> Faithfully restore the first input, the native [world/key] overhead cloud tile. Preserve its exact palette,
> large cloud bands, silhouettes, gaps, coverage, orientation and cloud scale. Improve pixel stepping and cloud wisps
> with restrained detail in the original game's style. The second image, if provided, is a layout reference only;
> do not transfer its palette. Return a flat full-bleed opaque square, continuous across both wrapping axes.
> Preserve the source's [specific blue/cloud colours and weather mood]. No horizon, landscape, sun, objects, text,
> frame, mirroring, edge fade or new large clouds. Requested runtime target: [2W × 2H].

## Pilot, visual checks and feedback loop

Start with **MM6 `6plansky1`: native 512² → restored 1024²**, using original BMP palette and the corrected New Sorpigal
rendering. `6sky01` is pixel-identical and shares the accepted output. Present the first complete comparison set before
propagating its detail/style choices to other skies. Independent source preparation can continue while feedback arrives.
Readiness discussion alone does not authorize generation; once a restoration run is requested, routine checks/retries
and preparation proceed within that request without requiring a separate approval for every image.

Each pilot/job review package must contain:

- Native and restored full tiles at the same display size, plus a native-sized downsample of the restored result.
- 3×3 repeats and both-axis half-offset views at useful display scales; numeric seam statistics are supporting evidence.
- Actual game x1/x2 captures with matched camera, time/weather, fog, viewport and executable. Include overhead and horizon
  views, plus brief motion/drift evidence. Texture mockups must be labelled and do not replace game captures.
- Exact source key/hash, output version/hash, map/save/camera, selected asset tier and capture limitations.
- A short verdict covering palette/value, cloud layout/coverage/scale, edge character, tiling, horizon and motion.
  Mark each check pass/revise/not checked. Do not mark an unchecked criterion passed because another view looks good.

Reuse the [existing native capture helper](../projects/brackenford_greywatch/capture_gameplay.py) and
[recorded sky capture procedure](mm6_new_sorpigal/README.md). Prepare fresh isolated x1/x2 settings/assets and saves for
this run. The old screenshots use different executable revisions and the old x2 settings lack corrected MM6 art;
they are historical evidence, not a ready-made new comparison. The helper supports explicit world, map, save, pose,
binary and review directory. Capture dependencies/settings and a smoke capture must be checked at execution start.

For feedback, keep a `review/feedback.md` log with asset/version, reported issue, requested invariant, revision taken,
and before/after evidence. Useful categories are: too bright/dark, wrong hue, clouds too dense/sparse, changed large
shapes, too sharp/soft, repeated pattern/seam, horizon mismatch, or motion/scale mismatch. Translate feedback into a
specific prompt or targeted repair while retaining accepted properties. Save the next version alongside the previous;
never replace raw generation evidence. Rerun the affected visual checks after each revision, including in-game checks
when colour, scale or boundaries changed. Two failed targeted repairs trigger diagnosis of the source/prompt/export
or rendering behaviour, not an endless blind retry loop.

Suggested per-job states: `pending → generated → checks passed → visual review → accepted → installed`; a failing
check or feedback sends the affected version to `revise`. Record who accepted it (agent assessment or explicit user
feedback) and the criteria/evidence. Do not attribute user approval when none was given. User feedback supersedes an
agent's prior visual verdict. Reopen other accepted skies only if feedback identifies a shared defect or the user asks.
Keep job-level acceptance separate from the complete-world installation gate.

Before enabling a whole world's x2 sky tier, include every configured/custom/event sky required there. A pilot can be
reviewed in an isolated stage with clearly labelled native x2 placeholders for the remaining states. Existing ESRGAN
candidates may be retained if they pass fidelity review; native nearest-neighbour placeholders are not restoration
completion. All-map lookup checks and representative captures remain execution work, not already-passed audit results.

## Lessons from the 6plansky1 pilot

The user accepted v3_local on 2026-09-09: “OK this is fine”. This follows the seam report in
[`1292.png`](../../test_img/1292.png), the targeted repair and the
[in-game comparisons](mm6/6plansky1/review/v3/index.html). Preserve that accepted artwork as a reference for subsequent
jobs, with each sky's own native palette and cloud structure. The acceptance does not close the separate renderer
fade reported in [`1290.png`](../../test_img/1290.png), or authorize a whole-world x2 installation.

### Review requirements for subsequent skies

1. **Verify identity before changing artwork.** Record the actual resolved file, tier and hash. A similar name or
   a plausible-looking screenshot is insufficient when worlds have different sky palettes. Compare native versus
   restored artwork, then compare game presentation with an original-game reference when available. x1 and x2 can
   agree while both contain the same renderer defect; do not recolour an asset to compensate for that defect.
2. **Expose the joins in the game.** A reduced 3×3 sheet and a short startup drift sample missed v2's seam. Inspect
   both wrapping axes at full texture resolution and in half-offset views, then place cloud-bearing joins in the
   visible sky at multiple scroll positions and camera pitches. Include a view where projection magnifies the join;
   a join hidden in empty blue sky or horizon fog is not sufficient evidence. Retain before/after frames and a short
   sequence showing the join moving. Mark any axis or condition not exercised as unchecked.
3. **Use measurements to find defects, not to approve them.** Record mean, p95 and maximum edge RGB differences,
   compare with the native source, and inspect the locations of large differences. Also inspect internal joins after
   an offset repair: a seam can move from the border into the tile. v2's modest edge averages still produced a visible
   line under projection. No universal numerical seam threshold follows from this pilot.
4. **Constrain an AI repair to the demonstrated defect.** Half-offset the tile, request continuity only at the central
   crossing, and keep palette, coverage, scale and surrounding clouds fixed. Inspect the entire returned image:
   v3 repaired that crossing but changed unrelated areas and introduced new outer-edge mismatches. Its whole-image
   export was rejected. A local selection retained the useful AI repair on v2, then the half-offset was undone.
   Retain the prompt, raw return, mask and exact export procedure. Feather the selection if needed, not the cloud
   image. Check for a visible cross, colour stripe or softened cloud band at the selection boundary afterward.
5. **Treat the successful mask as an example, not a preset.** This 1024px pilot used a 48px central cross and a
   sigma-12 feather on the selection mask. Choose the smallest repair region that fits the next demonstrated defect;
   do not apply these dimensions to every sky or add seam processing to already continuous assets. Avoid mirrored
   borders, forced identical edge strips, blanket blur and global colour changes. After two failed targeted AI
   retries, diagnose source, constraints, export or rendering before generating again.
6. **Make visual comparisons reproducible.** Explicitly load the retained review save; inherited startup settings
   previously started a fresh session. Match binary, camera, time/weather, fog, viewport and quality settings across
   each pair. Keep ordinary play preparation from overwriting historical review metadata. If a diagnostic timer
   adjustment is used to expose a later join, verify it took effect and label it; a failed adjustment is not evidence.
   The pilot's debugger helper is guarded for one frozen binary and must not be reused with stale memory offsets.
7. **Record acceptance at the right scope.** User feedback overrides an earlier agent pass. Keep rejected versions
   and update the current manifest, review log and gallery together. Track artwork, original-game renderer fidelity,
   performance and installation separately. Short Xvfb captures establish visual evidence, not target-GPU performance
   or a full weather-cycle guarantee.

### Pilot evidence to carry forward

| Finding | Before | Accepted repair / outcome |
| --- | --- | --- |
| Left/right mean edge RGB delta | v2 3.46; native 1.62 | v3_local 1.91 |
| Top/bottom mean edge RGB delta | v2 5.18; native 2.51 | v3_local 2.46 |
| Median RGB | v2 47/75/142 | v3_local 47/75/142 |
| In-game seam | User-visible straight line in 1292 | Targeted repair accepted by user |
| Broad grey sky fade | Present in both x1 and x2 | Still a separate unresolved renderer-fidelity issue |

The measurements use 0–255 channel values at each asset's own resolution; they are descriptive, not equivalent
spatial-gradient thresholds across resolutions. See the [feedback history](mm6/6plansky1/review/feedback.md),
[repair prompt](mm6/6plansky1/prompts/v3.txt), [export procedure](mm6/6plansky1/build_review.py),
[asset checks](mm6/6plansky1/review/v3/asset_checks.json) and [accepted artifact manifest](mm6/6plansky1/manifest.json).

## Installation and runtime correctness

The engine's virtual `sky_textures/` directory maps to physical **`textures_x2/`** when `[video_quality] sky=x2`.
Use `assets_dev/worlds/mm6/textures_x2/`, `mm7/textures_x2/`, and `mm8/textures_x2/`.
Do not invent `skies_x2`, `sky_x2` or put sky images in `terrain_x2`. Keep native BMPs unchanged.

Outdoor sky and surface textures share that physical folder but have independent quality settings:

```ini
[video_quality]
sky=x2
texture=x1
```

`sky=x2` changes outdoor skies. Indoor sky faces and sky art on ordinary surfaces use `texture=x2`.
Validate both combinations and also both at x2. Do not add a special indoor rendering path merely to change artwork.

**Current mounting concern:** `AssetFileSystem::mountMergedWorldMapRuntimeRoots` mounts other worlds'
`textures_x2` directories based on the **Textures** category, not the Sky category. The active world's full root
is mounted regardless. Thus a sky existing only in another world's x2 directory is not guaranteed to resolve with
`sky=x2, texture=x1`. Before rollout, either correct this shared mounting behaviour with focused coverage, or install
the exact required sky outputs in each consuming world's directory. The latter is an explicit content installation,
not a runtime fallback. Do not assume that a successful all-x2 test proves independent sky-tier loading.

The regenerated install inventory includes native-owner archive files and explicit consuming-world destinations
for weather, custom, event and legacy fallback names. It is provisional because the reviewed outputs and their hashes
do not exist yet. It includes MM6's event `sky04` alias; restoring only the continent list would miss that winter state.
Duplicate target copies share one reviewed master and do not imply extra generation jobs. No MMerge copies are needed
solely because that reference folder contains duplicates. Preserve explicit event/fallback identities during this run.

Installation procedure after review:

1. Check native/export hashes, dimensions, lowercase names and opaque pixels; detect case-insensitive collisions.
2. Build a staging pack and map each intended runtime name to an explicit reviewed source/output.
3. Verify every world's ordered sky list resolves to the same intended images at x1 and x2, including custom/event names.
   Missing files currently filter the resolved weather list; “the game still shows a sky” is not a sufficient test.
4. Install only manifest-listed PNGs into the existing folders. Preserve other surface upscales and native assets;
   record old hashes and an explicit backup for any replaced ESRGAN image. Preserve the accepted muted sky as its own asset.
5. Restart/reload and validate actual assets and quality settings in use. Only enable the main sky x2 setting once
   the intended complete runtime selection is available; package ZIP updates are a later packaging step.

## Visual and performance acceptance

The acceptance standard is **the original world's sky, with clearer detail**. Original-MM6 fidelity has priority over
matching the palette of an accidentally selected merged asset. A prettier isolated tile is insufficient.

- The user confirmed corrected native MM6 selection. Compare that native x1 to its own restored x2; retain `1289.png`
  as the original-game style reference.
  Record which source is selected, camera position/yaw/pitch, time/date, weather, fog, viewport, renderer and settings.
- Compare same executable, save/state and camera at x1/x2. Freeze or match scroll time where possible: clouds drift in
  wall time, so adjacent captures are not automatically pixel-aligned. Do not diagnose projection from unmatched crops.
- Review overhead, horizon, several yaw directions and a short motion capture. Look for repeating bands, seam crosses,
  cloud-scale changes, horizon discontinuities and visibly different drift speed.
- Preserve native colour, cloudy/clear coverage and weather contrast; verify dawn/day/dusk/night separately from texture
  identity. Do not bake runtime tint/fog into a neutral cloud asset. Preserve red sunset art when that is native artwork.
- Validate lookup coverage for all 42 outdoor maps. Capture representative skies for every distinct selected output,
  all custom sky maps, Frozen Highlands' winter override, and indoor ceiling/event/surface examples from Stage C.
  Flag underwater, elemental and enclosed special cases explicitly; do not assume a fair-weather outdoor recipe applies.
- The outdoor horizon colour currently averages the last eight **physical** rows. At x2 this samples half the native
  vertical extent; check for a gradient shift. If it causes a regression, fix logical sampling in shared rendering,
  with focused validation, instead of changing source colours to conceal it.

For performance, measure cold first sky use, subsequent weather switches, steady sky rendering and map reload with
matched settings. The current build preloads the initial sky during map loading; `ensureSkyTexture` caches by name.
A later uncached sky can still decode/upload during rendering; look at
`[AssetLoadWarning] kind=sky phase=render ... load_us=...`. Check frame-time spikes/p95/p99, not only averaged FPS.
Do not claim measured performance gains from this planning audit.

At x2, pixel storage is **4× native**. A 512² BGRA output is 1 MiB; 1024² is 4 MiB. Outdoor sky handles retain CPU BGRA
pixels as well as the GPU texture, so budget roughly twice that base storage, plus temporary decode/driver overhead.
One visible sky is not all 64 images resident at once, but successive sky changes can populate the cache. Verify cache
release on map/quality changes. If cold-load hitches are material, schedule only the selected map's small sky set during
loading and validate that shared change separately; do not preload the whole archive on every map.

## Completion gates

- Stage 0 complete: explicit native continent lists, passing lookup/map tests, and user-confirmed in-game correction.
- Art: all 64 distinct native images accounted for as accepted/reused/restored, with ancillary surface assets preserved.
- Coverage: every intended runtime name maps to a reviewed output; all current/custom/event/legacy choices accounted for;
  archive-only assets labelled honestly rather than claimed as game-visible tests.
- Integration: exact x2 sizes, physical paths and tier settings verified, independent sky/surface mounting validated,
  complete hashes/rollback manifest, no unrelated asset changes.
- Review: native/restored repeat sheets and representative actual game captures; performance results with their limits.

The continent-list correction is complete. The MM6 pilot has a retained review package; other jobs remain pending.
Pilot asset generation did not change production assets or main settings.
Per-job capture settings, prompts, raw outputs and final install hashes are produced during execution; the inventory
is not a fully automated generation or all-map capture runner.
