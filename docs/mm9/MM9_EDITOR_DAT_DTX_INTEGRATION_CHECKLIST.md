# MM9 DAT + DTX Editor Integration Checklist

This document defines the editor-side implementation plan for native MM9 DAT/DTX support. It extends
`MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md`; that document remains the authority for source layout, DAT/DTX parsing,
runtime wiring, generated sidecars, and lossless requirements.

The goal is a complete native MM9 editor path where every official source reference is visible, validated, and wired:
world DATs, DTX textures, skins, model assets, sprites, sounds, voices, scripts, RUDE/data records, object properties,
events, mechanisms, portals, visibility, collision, and actor/monster variants.

## Scope Split

This checklist has three scopes. Keep them separate when choosing work, judging completion, or deciding whether a
diagnostic should block the current gate.

### Active Two-Map Editor Gate

This is the current implementation gate and the day-to-day acceptance target. Keep slow editor/rendering/inspection
work focused on:

- `assets_dev/worlds/mm9/maps/thjorgard.level.yml`
- `assets_dev/worlds/mm9/maps/thjorgardcity.level.yml`

These two maps are the required editor-confidence slice for native DAT/DTX world geometry, source-DTX material
rendering, object/event/mechanism inspection, picking, and validation. Do not expand slow editor, rendering, object,
actor, mechanism, or asset resolution work beyond these two maps while this gate still has active failures.

The active gate is evaluated from focused commands and concrete counters, not by opening every local MM9 map. The
preferred one-command gate is:

- `tools/mm9_import_discovery/run_mm9_active_gate.sh`

That wrapper runs these focused checks:

- focused generator/idempotency checks for `thjorgard` and `thjorgardcity` in both `assets_dev` and
  `assets_editor_dev`;
- `ctest --test-dir build -R mm9_active_gate_tests --output-on-failure`;
- named MM9 DAT editor/import unit tests for parsing, render mesh source ids, picking, material assignment, filters,
  mechanism preview, level metadata, document paths, generated sidecars, and active-slice entrypoints;
- `./build/editor/openyamm-editor --world mm9 --headless-verify-document-dispatch`;
- `./build/editor/openyamm-editor --world mm6 --headless-run-regression-suite editor-world-outdoor-terrain-load`;
- `./build/editor/openyamm-editor --world mm9 --headless-verify-mm9-dat-filters thjorgard.level.yml`
- `./build/editor/openyamm-editor --world mm9 --headless-verify-mm9-dat-filters thjorgardcity.level.yml`
- `./build/editor/openyamm-editor --world mm9 --headless-verify-mm9-dat-level thjorgard.level.yml`
- `./build/editor/openyamm-editor --world mm9 --headless-verify-mm9-dat-level thjorgardcity.level.yml`
- `./build/editor/openyamm-editor --world mm9 --headless-verify-mm9-inspector-search thjorgard.level.yml`
- `./build/editor/openyamm-editor --world mm9 --headless-verify-mm9-inspector-search thjorgardcity.level.yml`
- `python3 tools/mm9_import_discovery/check_mm9_active_gate.py`.

Current active-gate pass/fail counters live in
`assets_dev/worlds/mm9/import/validation/active_slice.validation_summary.yml`. The gate is not green unless the summary
has at least these properties:

| Counter | Required active-gate state |
| --- | --- |
| `clean` | `true` |
| `report_count` | `2` |
| `dirty_reports` | `0` |
| `level_load_diagnostics` | `0` |
| `source_mutation_snapshot_verified_reports` | equals `report_count` |
| `source_mutation_snapshot_files` | nonzero |
| `source_dat_hash_diagnostics` | `0` |
| `source_dat_hash_verified_reports` | equals `report_count` |
| `source_manifest_diagnostics` | `0` |
| `source_manifest_expected_files` | equals `source_manifest_actual_files` |
| `source_manifest_count_drift_families` | `0` |
| `source_manifest_missing_directories` | `0` |
| `document_paths_missing` | `0` |
| `document_paths_missing_required` | `0` |
| `readonly_source_paths` | at least 2 per report |
| `generated_paths` / `authored_paths` / `authored_override_paths` / `compatibility_paths` | nonzero |
| `dat_world_reference_issues` | `0` |
| `asset_graph_total` | nonzero and equals resolved + unresolved + ambiguous |
| `asset_graph_resolved` | equals `asset_graph_total` in the active slice |
| `asset_graph_unresolved` / `asset_graph_ambiguous` / `asset_graph_stale` | `0` |
| `asset_graph_required_total + asset_graph_optional_total` | equals `asset_graph_total` |
| `asset_graph_required_resolved + asset_graph_required_unresolved + asset_graph_required_ambiguous` | equals `asset_graph_required_total` |
| `asset_graph_optional_resolved + asset_graph_optional_unresolved + asset_graph_optional_ambiguous` | equals `asset_graph_optional_total` |
| `asset_graph_required_unresolved` | `0` |
| `asset_graph_required_ambiguous` | `0` |
| `asset_graph_optional_unresolved` | `0` |
| `asset_graph_optional_ambiguous` | `0` |
| `raw_object_asset_refs` | equals `required_raw_object_asset_refs + optional_raw_object_asset_refs` |
| `unresolved_required_raw_object_asset_refs` | `0` |
| `unresolved_optional_raw_object_asset_refs` | `0` |
| `stale_caches` | `0` |
| `viewport_native_missing_material_triangles` | `0` |
| `viewport_native_placeholder_material_triangles` | `0` |
| `viewport_native_unresolved_material_triangles` | `0` |
| `native_filter_visual` / `native_filter_helper` / `native_filter_physics` / `native_filter_visibility` / `native_filter_rail` | nonzero |
| `native_filter_visible_water + native_filter_water_volume` | equals `native_filter_water` |
| `native_filter_helper` | covers physics, visibility, rail, and water-volume helper subsets |
| `native_filter_portals` | nonzero for the active slice |
| `ambiguous_dtx` | `0` |
| `material_textures` | equals `resolved_dtx + resolved_sprite_materials + default_helper_materials` |
| `source_dtx_paths` | equals `resolved_dtx` |
| `placeholder_missing_source_materials` | at least `default_helper_materials` |
| `dtx_headers` | equals `resolved_dtx` |
| `dtx_user_flag_records` | equals `dtx_headers` |
| `dtx_extra_byte_records` | at least `dtx_headers` |
| `dtx_decoded_preview_mips` | equals `dtx_mip_payloads` |
| `decoded_cache_mismatches` | `0` |
| `decoded_cache_*` source/image/match counters | equal `decoded_cache_determinism_checked` |
| `unresolved_sprite_frame_textures` / `ambiguous_sprite_frame_textures` | `0` |
| `resolved_sprite_materials` / `resolved_sprite_frame_textures` | equal corresponding source counters |
| `unresolved_required_sound_references` | `0` |
| `resolved_sound_references` | equals `sound_references` |
| `missing_model_instance_assets` | `0` |
| `missing_drawable_model_instance_geometry` | `0` |
| `actor_variant_unresolved` | `0` |
| `actor_variant_gameplay_identity_rows` | equals `actor_variant_candidates` when candidates are nonzero |
| `actor_variant_unresolved_foot_sounds` | `0` |
| `actor_variant_resolved_foot_sounds` | equals `actor_variant_foot_sound_fields` |
| `actor_variant_unresolved_source_sound_references` | `0` |
| `actor_variant_resolved_source_sound_references` | equals `actor_variant_source_sound_references` |
| `actor_variant_unresolved_source_voice_references` | `0` |
| `actor_variant_resolved_source_voice_references` | equals `actor_variant_source_voice_references` |
| `missing_scripted_object_collision_visuals` | `0` |
| `mechanism_unresolved_required_targets` | `0` |
| `mechanism_incomplete_linear_motion` / `mechanism_incomplete_rotation_motion` | `0` |
| `mechanism_unresolved_trigger_outputs` | `0` |
| `mechanism_authored_sound_references + mechanism_empty_sound_references` | equals `mechanism_sound_slots` |
| `mechanism_activation_start_open_fields` | nonzero, with locked/push/touch/reopen counts matching |
| `mechanism_timing_move_delay_fields` / `mechanism_timing_open_wait_fields` | equal `mechanism_activation_start_open_fields` |
| `mechanism_rotation_open_away_fields` | nonzero and no greater than `mechanism_activation_start_open_fields` |
| `mechanism_world_model_targets_missing_model` | `0` |
| `mechanism_world_model_targets_missing_polygon_group` | `0` |
| `mechanism_world_model_targets_mismatched_polygon_group` | `0` |
| `script_includes` / `script_labels` | nonzero |
| `script_unresolved_includes` / `script_ambiguous_includes` | `0` |
| `script_resolved_includes` | equals `script_include_references`, which equals `script_includes` |
| `mechanism_inert_preview_entries` | equals `mechanism_inert_mechanisms` |
| `mechanism_preview_changed_bounds` | equals `mechanism_preview_candidates` when candidates are nonzero |
| overlay/picking counters | nonzero when the corresponding source-backed data exists |

The `check_mm9_active_gate.py` command validates the table above from the current active summary and prints a compact
pass/fail line. Current evidence: it reports `MM9 active gate passed` with 2 reports, 82,815 native renderable
triangles, 1,022 model instances, 165 mechanism preview candidates, 189 inert preview entries, and 33 non-blocking
warnings. Focused unit coverage for the checker is in `tests/mm9_active_gate_tests.py`; it verifies the passing summary
shape and failures for wrong active maps, unresolved required counters, missing source immutability proof,
source-manifest count drift, missing required document paths, missing inert-preview detail, missing preview bounds
changes, missing overlay pick evidence, unresolved required sound references, unresolved sound-reference counts, and
missing actor-variant gameplay identity rows. Actor-variant foot-sound and object-authored actor sound/voice reference
drift are also active-gate failures. Mechanism diagnostics are also covered: incomplete authored motion, unresolved
trigger outputs, sound-slot partition drift, missing typed activation/timing evidence, and invalid `open_away` rotation
evidence are active-gate failures. Source script provenance now also has active-gate counters for nonzero
`script_includes` and `script_labels`, and required include-file resolution counters for zero unresolved/ambiguous
includes; current focused evidence is 60/60 resolved includes and 275 labels across the two active reports. Native DAT
filter evidence is now
part of the final summary check, so visual/helper/physics/visibility/rail/water/portal classifier drift cannot pass only
because the standalone filter verifier was skipped. Asset-graph total/resolved/required/optional partitions are also
checked, including optional unresolved and optional ambiguous counters.
CMake registers this Python test as `mm9_active_gate_tests`, so the CTest command above runs it after the build
directory is configured. Current one-command evidence: `tools/mm9_import_discovery/run_mm9_active_gate.sh` passes end to
end, including `--headless-verify-document-dispatch` with 8 cases: 2 active MM9 DAT documents, 3 legacy outdoor
documents, 3 legacy indoor documents, the focused MM6 outdoor editor terrain smoke for `oute3.odm`, and both active
DAT filter verifiers. The wrapper intentionally no longer runs the broad `MM9 DAT*` doctest bucket, because that also
contains playable/runtime acceptance checks such as `guberland`/`guberlandcity`; those remain outside the active
two-map editor gate.

Diagnostics block the active gate only for required source loss, required unresolved or ambiguous references, invalid
source indexes, missing required generated sidecars, stale generated data used by the active maps, or render/pick/inspect
paths that silently drop required active-map data. Optional, inert, helper-only, source-only, future-runtime-only, or
all-map-only findings should be warnings/info with source provenance unless an active-map required reference is lost.

This does not mean MM9 DAT/DTX code should be editor-only. Low-level, non-UI services should still live in reusable
engine/game/shared modules when they represent source truth or runtime-neutral logic:

- DAT binary parsing, source-index-preserving world-model data, BSP/leaf/portal records, render mesh extraction, bounds,
  and ray picking;
- DTX binary/header parsing and texture decoding;
- material alias resolution from DAT texture names to original DTX files;
- raw object parsing and source-property preservation;
- model/skin/sprite/sound/script/data reference resolution;
- mechanism/event target binding as source-index-preserving data.

The editor is the first consumer and validation surface for those services. The game runtime should later consume the
same proven services and sidecars, but it should not receive separate MM9 gameplay/rendering shortcuts before the editor
proves the source data is complete and correctly wired.

The active two-map editor gate is green only after:

- `thjorgard.level.yml` and `thjorgardcity.level.yml` open through `maps/<map>.level.yml`;
- the editor renders DAT world geometry from source DAT and source DTX, not from compatibility ODM/BLV or mandatory
  `.bitmaps/*` caches;
- model instances, actors/monsters, props, pickups, sounds, lights, triggers, doors/mechanisms, portals/leaves,
  physics, and visibility helpers are inspectable and either rendered/visualized or explicitly hidden by a checked
  display filter;
- every official source reference has a resolved target or a blocking diagnostic;
- source indexes round-trip from viewport selection to inspector rows and sidecar records;
- MM6-MM8 editor and game loading are proven unaffected.

### Future All-Map Regression

All 45 local MM9 maps are a later regression/milestone scope. Cheap parser, source-manifest, and sidecar idempotency
checks may still run across all maps when they are fast and relevant, but slow editor/rendering/inspection gates should
not be expanded past `thjorgard` and `thjorgardcity` until the active two-map editor gate is green.

When the active gate is green, widen the same validators and inspectors to the remaining local MM9 maps as a separate
milestone. Do not treat all-map failures as day-to-day active-gate blockers unless they reveal a defect that also affects
the two active maps or shared source-preserving services.

### Playable Runtime Milestone

Playable MM9 game-world integration is explicitly blocked until the active two-map editor gate is green. Runtime work may
continue only for reusable low-level services that the editor is actively proving, such as DAT parsing, DTX decoding,
source-index models, material resolution, model/skin/sprite/sound/script reference resolution, and event/mechanism
binding data. Do not add gameplay shortcuts or separate runtime interpretations before the editor path proves the source
data and diagnostics.

## Non-Negotiable Outcomes

Unless a bullet is explicitly tagged `[future-regression]` or `[runtime-blocked]`, these outcomes are active two-map
editor-gate requirements. In this section, "every" means every required source-backed reference in `thjorgard` and
`thjorgardcity`; future all-map widening must reuse the same checks but is not the current day-to-day gate.

- [x] MM9 editor loading uses `maps/<map>.level.yml` as the entrypoint and resolves original assets from
  `source/*`.
  Active evidence: both `thjorgard.level.yml` and `thjorgardcity.level.yml` validate as `kind: mm9_level`,
  `runtime.world_backend: dat_world`, declare their source DAT paths under `../source/worlds`, declare the active-slice
  authored source-asset-alias sidecar, and pass `validateMm9DatLevelMetadataFiles` with zero path/hash/kind issues. The
  focused DAT-level headless verifier also opens both maps through their `maps/*.level.yml` entrypoints, reports
  `readonly_source_paths=2`, validates source DAT hashes and source manifest counts, and never treats compatibility
  ODM/BLV as the entrypoint.
- [x] `source/*` remains immutable. Editor saves never modify DAT, DTX, ABC/LTB, SCR/INC, RUDE, sounds, sprites, or
  original data files in place.
  MM9 DAT documents reject the editor's generic `save`, `saveSource`, `saveAs`, `saveSourceAs`, `buildRuntime`, and
  `buildRuntimeAs` mutation/build entrypoints. The active DAT-level verifier now checks these guards for both
  `thjorgard.level.yml` and `thjorgardcity.level.yml` and also asserts the rejected save-as sentinel is not created.
- [x] Native MM9 maps do not load through `OutdoorView` or `IndoorView`. They use a new DAT document/view path while
  sharing reusable renderer, asset, picking, and diagnostics services where appropriate.
- [x] Existing MM6-MM8 ODM/BLV editor behavior remains unchanged unless a document explicitly has `kind: mm9_level`.
  Active evidence: `--headless-verify-document-dispatch` opens the active MM9 `thjorgard.level.yml` and
  `thjorgardcity.level.yml` entrypoints as `EditorDocument::Kind::Mm9Dat`, then opens representative legacy
  MM6/MM7/MM8 map paths through the same physical-map loader and verifies they still dispatch as outdoor or indoor
  documents instead of touching MM9 sidecars. The current dispatch set covers 8 cases: 2 MM9 DAT documents, 3 legacy
  outdoor ODM documents, and 3 legacy indoor BLV documents, without requiring an SDL video backend.
- [x] Every active-map DAT texture reference resolves to an original DTX source file, a source-backed SPR/built-in
  helper classification, or a decoded preview/cache asset.
  Active two-map evidence now has zero renderable native DAT missing, placeholder, or unresolved material triangles.
  `thjorgard` resolves 59 source DTX material rows plus 3 SPR-backed material rows with 59/59 frame DTX files;
  `thjorgardcity` resolves 135 source DTX material rows plus 3 SPR-backed material rows with 50/50 frame DTX files.
  LithTech `Default` material rows used only by hidden helper/volume/visibility models are classified as built-in
  helper material evidence instead of missing source DTX. Optional `WorldProperties` sky/environment texture strings are
  now resolved as LithTech world-property sky-controller metadata instead of DAT surface material inputs. The active
  summary now enforces the complete material row partition: `material_textures=202` equals `resolved_dtx=194` plus
  `resolved_sprite_materials=6` plus `default_helper_materials=2`, with `ambiguous_dtx=0`,
  `unresolved_sprite_frame_textures=0`, `ambiguous_sprite_frame_textures=0`, and zero renderable placeholder or
  unresolved native DAT triangles.
- [x] Every DTX source file used by the active maps has preserved header metadata, user flags, mip information,
  command string, extra fields, and source path.
  Active evidence: `thjorgard` reports 59/59 source DTX paths and loaded headers, 59 user-flag records, 708 extra-byte
  records, 236/236 decoded preview mips, 12 command strings, and 55/55 deterministic decoded cache matches.
  `thjorgardcity` reports 135/135 source DTX paths and loaded headers, 135 user-flag records, 1,620 extra-byte records,
  539/539 decoded preview mips, 5 command strings, and 132/132 deterministic decoded cache matches. The active summary
  enforces these as `source_dtx_paths=194`, `dtx_headers=194`, `dtx_user_flag_records=194`,
  `dtx_extra_byte_records=2328`, `dtx_decoded_preview_mips=775`, and `decoded_cache_mismatches=0`.
- [ ] Every active-map DAT object reference that names or points at a model, skin, sprite, sound, voice, script, class,
  command, event target, or world-model target is either resolved or reported as a blocking validation error.
- [ ] Every actor and monster variant used by the active maps resolves through official MM9 data to its model or billboard,
  animation source, skin/texture set, sound/voice set, and gameplay identity.
  Active-slice validation now makes official gameplay identity completeness a blocking active-gate invariant:
  `actor_variant_gameplay_identity_rows=113` must equal `actor_variant_candidates=113`, with per-map evidence
  `53/53` for `thjorgard` and `60/60` for `thjorgardcity`. This item remains open until animation/source sound/voice
  identity is centralized under the same actor/monster resolver instead of only proving model/skin/gameplay rows.
- [x] Every active-map generated sidecar preserves source indexes so editor selection can round-trip to DAT world model,
  polygon, surface, leaf, node, user portal, object, and property indexes.
  Active-slice reports now promote the source-index proof into the blocking summary: `raw_objects=2475`,
  `object_source_transforms=2475`, `raw_object_sidecar_issues=0`, `dat_world_reference_issues=0`, and zero invalid
  leaf, surface texture, polygon surface, polygon plane, polygon vertex, node polygon, and root-node references.
  Per-map evidence is `704/704` object source transforms for `thjorgard` and `1771/1771` for `thjorgardcity`, with
  user-portal sidecar metadata preserved for the city map's 35 portals.
- [x] The editor can open `thjorgard` and `thjorgardcity` with zero unresolved required asset references and zero
  invalid source-index references.
  `tools/mm9_import_discovery/run_mm9_active_gate.sh` now treats those conditions as active completion criteria through
  the two DAT-level headless validations, inspector-search runs, and `check_mm9_active_gate.py`.
- [x] The editor has headless tests proving `thjorgard` and `thjorgardcity` open, render, pick, inspect, and validate.
  The active wrapper runs both `--headless-verify-mm9-dat-level` maps for native DAT open/render/pick/validate evidence
  and both `--headless-verify-mm9-inspector-search` maps for source-backed inspector coverage. Current inspector-search
  evidence indexes 4,771 rows for `thjorgard` and 12,795 rows for `thjorgardcity`, covering world models, textures,
  raw objects, scripts, sounds/voices, lights, sound objects, spawns, model instances, actor variants, diagnostics, and
  known mechanism binding targets.
- [ ] `[future-regression]` All 45 local MM9 DAT maps remain a later milestone/regression target for the same checks.
- [ ] `[runtime-blocked]` Playable MM9 game-world integration remains blocked until the active two-map editor gate is
  complete.

## Editor Architecture

### New Document Type

- [x] Add `EditorDocument::Kind::Mm9Dat` or an equivalent non-ODM/BLV document kind.
- [ ] Add a native MM9 document model, tentatively `EditorMm9DatDocumentData`, containing:
  - [ ] loaded `*.level.yml`;
  - [ ] source DAT path and content hash;
  - [x] parsed DAT world model/BSP render data;
  - [ ] parsed DAT object data;
  - [ ] generated `*.dat_world.yml` inspection metadata;
  - [ ] `*.raw_objects.yml`;
  - [ ] `*.material_aliases.yml`;
  - [ ] `*.events.yml`;
  - [ ] generated script IR and Lua status;
  - [ ] asset dependency graph;
  - [ ] validation diagnostics.
- [x] Add `EditorDocument::loadMm9DatLevelPackage(...)` or equivalent, selected only when the opened file is
  `kind: mm9_level`.
- [x] Keep `loadOutdoorMapPackage`, `loadIndoorMapPackage`, and physical ODM/BLV scene loading untouched for MM6-MM8.
  The MM9 branch is limited to `*.level.yml` physical paths, while ODM and BLV physical paths continue to resolve their
  adjacent legacy scene/package supplements. `--headless-verify-document-dispatch` now checks this directly for
  representative MM6/MM7/MM8 outdoor and indoor maps.
- [x] Make save/build semantics explicit for the inspector/validator editor path:
  - [x] `source/*` is read-only.
  - [x] generated sidecars can be regenerated.
  - [x] authored overrides live outside `source/*`, likely under `maps/`, `events/`, or `import/overrides/`.
    The editor now builds a typed MM9 document path inventory from the level YAML, source manifest, generated sidecars,
    generated Lua/script IR, compatibility artifacts, and generated material caches. MM9 `save`/`save as`/`build`
    operations no longer fall through to ODM/BLV document behavior and report DAT/DTX-specific messages instead. The
    active MM9 editor milestone is an inspector/validator milestone, not a DAT authoring milestone: creating or
    recompiling DAT levels is left to external/source-world tools or future dedicated tooling.

### New Viewport

- [x] Add a native DAT viewport, tentatively `EditorDatLevelViewport`.
  Implemented as the MM9 DAT branch of the editor viewport rather than a separate class: `kind: mm9_level` documents
  render from the parsed DAT render mesh, DAT model roles, MM9 object layers, and MM9 sidecars without entering the
  ODM/BLV terrain or room pipelines.
- [x] Render DAT world models directly from parsed DAT geometry.
  Active evidence: `thjorgard` reports 37,772 native mesh triangles and 31,418 default renderable native DAT triangles;
  `thjorgardcity` reports 76,414 native mesh triangles and 51,397 default renderable native DAT triangles. Both active
  maps preserve source model/polygon/surface/texture ids through render mesh construction, selection, and inspection.
- [x] Render sky-capable DAT maps without requiring ODM outdoor terrain.
  DAT sky/helper surfaces are classified from DAT model roles and surface flags; active filter evidence reports sky
  triangles in both active maps while the MM9 document path remains independent of ODM outdoor terrain.
- [x] Render portalized/city/dungeon DAT maps without converting them to BLV rooms.
  `thjorgardcity.level.yml` now opens and validates as `classification=dat_bsp_portal_like`,
  `visibility=dat_bsp_portal`, with 4,700 DAT leaves, 35 user portals, portal overlays, and zero DAT world reference
  issues. This is native DAT portal metadata, not BLV room conversion.
- [x] Render DAT world textures directly from source DTX data. Generated `.bitmaps/*` files may be used as temporary
  previews or diagnostics only; native DAT rendering must not require them as authoritative texture inputs.
  The DAT viewport decodes source DTX via the shared `game/mm9` loader and uploads decoded pixels directly to bgfx
  texture handles for native world geometry. Active evidence: both active maps report zero renderable native DAT
  missing, placeholder, or unresolved material triangles, with `viewport_native_textured_triangles=31418` for
  `thjorgard` and `viewport_native_textured_triangles=51397` for `thjorgardcity`.
- [ ] Render DAT document model instances, actors/monsters, props, boats, trees, pickups, lights, sounds, and other
  object-driven assets from raw object and sidecar source references.
  Active visual evidence in `test_img/923.png` shows Thjorgard currently renders native terrain/world geometry but does
  not yet visually prove model instances, actors, props, boat/tree content, moat/water, or wall/building presentation
  assets. Earlier placeholder-style material output must be interpreted through the material inspector rather than by
  screenshot labels: `RAIL` itself resolves to source DTX and is authored into the source DAT, while SPR-backed
  water/effect materials and true placeholder/default materials need explicit preview handling. `RAIL` is not a missing
  texture and should not be treated as normal visual art: active Thjorgard evidence shows the texture belongs to
  `AITrk*` DAT world models, raw objects expose `UsesRails`, `FlyerUsesRails`, `RailDist`, `RailCheckInterval`,
  `MaxRailPath`, and scripts reference `AIRail`, `GetContainer`, and `GetContainerCount`. Treat `AITrk*`/`AIRail`/
  `rail.dtx` surfaces as lossless rail/container/navigation helper geometry that is hidden from normal textured
  rendering by default, inspectable through an explicit rail/helper overlay, and still available to picking,
  validation, event binding, and future runtime movement/container logic. The screenshot also shows why the editor must
  make model-instance visibility and DAT helper-role filtering obvious: a disabled model-instance toggle or hidden
  helper role can look like missing source data unless the inspector and validation surface the exact reason. The MM9
  editor status strip now reports submitted DAT vertices and submitted model-instance vertices for the current frame so
  this class of visual report can be separated quickly into "not submitted", "submitted but occluded/framed wrong", or
  "submitted but rendered incorrectly". Treat this screenshot as an active two-map visual regression target, not as
  acceptable final editor behavior.
  MM9 DAT documents now load the generated object-presentation scene sidecar as read-only object placement data, without
  using its ODM/BLV geometry as source truth. Active validators assert `thjorgard` has 232 loaded model instances and
  `thjorgardcity` has 790, matching the generated sidecar counts. Those active model instances now also resolve
  generated GLB/model-sidecar candidates, import drawable generated model geometry, and decode source DTX skin textures
  in headless validation. The native DAT viewport buffer path now continues past DAT world mesh construction into the
  shared object-derived model-instance renderer instead of returning after terrain/world geometry. The default native
  DAT display filter now renders non-invisible `PhysicsBSP` triangles because the active MM9 city/outdoor maps store
  real wall, roof, floor, and building-shell textures there; `AITrk*`/`rail.dtx`, `VisBSP`, trigger/volume geometry,
  water-volume markers, and invisible surfaces remain hidden by default but available through explicit helper filters.
  Actual complete rendering is still open until
  screenshot/headless visual smoke proves those resolved instances, actors, props, trees, boats, city walls/building
  presentation assets, and any billboard-only visuals are visible with correct filtering and picking. Active viewport
  preflight now proves `thjorgard` has 31,418 source-DTX-textured renderable native DAT triangles, including 8,984
  renderable PhysicsBSP triangles, plus 232 drawable model-instance geometries. `thjorgardcity` has 51,397
  source-DTX-textured renderable native DAT triangles, including 47,895 renderable PhysicsBSP triangles, plus 790
  drawable model-instance geometries. The default filter now excludes rail helpers and water volume/marker helper
  brushes while keeping visible water/effect surfaces: current filter evidence reports `thjorgard` with
  `native_filter_rail=2460`, `native_filter_visible_water=13`, and `native_filter_water_volume=86`, and
  `thjorgardcity` with `native_filter_rail=5704`, `native_filter_visible_water=0`, and
  `native_filter_water_volume=48`. Each active map now reports zero renderable native DAT missing, placeholder, or
  unresolved material triangles after the scoped `MTNDOWN`
  (`TEXTURES\ENVIRONMENTMAPS\MountainSky\MTN_Down.dtx`) source-asset alias resolves to the snow-mountain skybox DTX.
  `Default` DAT material references are preserved as LithTech helper/default material evidence when they are only used
  by hidden helper/volume/visibility models instead of being reported as missing source DTX. The active validation
  reports now also expose SPR-backed DAT
  materials explicitly: `thjorgard` resolves 3/3 sprite materials and 59/59 referenced sprite-frame DTX files;
  `thjorgardcity` resolves 3/3 sprite materials and 50/50 referenced sprite-frame DTX files, with zero unresolved or
  ambiguous sprite-frame textures. The focused DAT-level verifier now also checks the default native DAT camera frame
  against object-derived model-instance centers: `thjorgard` has 232/232 model instances in front, in depth range, and
  inside the frame; `thjorgardcity` has 790/790. This rules out the common "assets are resolved but the default editor
  camera cannot see them" failure mode, while the screenshot-level visual-completeness item remains open because this is
  render-input and framing validation, not a pixel/readback proof.
- [ ] Provide an explicit display filter for hiding/showing helper geometry instead of hard-dropping potentially
  important visible world models based on a single surface flag.
  Interim rule: render non-invisible `PhysicsBSP` by default for MM9 DAT editor documents because active-map evidence
  shows it contains visible city/building/wall surfaces, while `VisBSP`, trigger/volume geometry, and invisible surfaces
  are still hidden in the default view. `AITrk*`/`AIRail` rail geometry textured with `rail.dtx` must be classified as
  helper/navigation/container geometry rather than `visible_geometry`; it should not appear in the normal textured view
  unless the user enables a dedicated rail/helper overlay. The toolbar now exposes explicit DAT subset filters for sky,
  PhysicsBSP, water, VisBSP, invisible, helper, and trigger/volume triangles so those hidden roles can be inspected
  intentionally. Current classifier evidence now gives `AITrk*`/`rail.dtx` its own `Mm9DatRenderFilterRail` bit, keeps it
  out of the default view, and includes it in the generic helper subset; active-map validation reports
  `native_filter_rail=2460` for `thjorgard` and `native_filter_rail=5704` for `thjorgardcity`. Add a rail-specific
  toolbar filter or make the generic helper filter surface rail role/name/texture evidence clearly enough that `RAIL`
  screenshots are not mistaken for unresolved textures.
- [ ] Support editor overlays for:
  - [ ] world model bounds and names;
    DAT world-model bounds now have a source-index-preserving viewport overlay toggle. The overlay draws sidecar-backed
    bounds boxes from `*.dat_world.yml`, colors visible/helper/movable model roles distinctly, and picking a bounds box
    selects the matching `Mm9WorldModel` inspector row with source model index/name preserved. Focused validation proves
    `thjorgard` has 7,608 world-model overlay vertices and 317 pick candidates; `thjorgardcity` has 18,912 vertices and
    788 pick candidates. On-canvas text labels remain open; names are currently available through the selected inspector
    and scene tree.
  - [ ] selected polygon/surface;
    Native DAT polygon selections now draw source-index-backed overlays directly from `Mm9DatRenderMesh`: a broad
    selected source-surface fill and a stronger selected source-polygon fill/edge overlay. The selected triangle still
    points back to the DAT source model, polygon, surface, texture, and material rows in the inspector. Focused
    validation proves the synthetic native pick produces non-empty selected overlays: `thjorgard` has 9 selected
    polygon overlay vertices and 3 selected surface overlay vertices; `thjorgardcity` has 18 and 6.
  - [ ] leaves, nodes, and user portals;
    User portals now have a source-index-preserving MM9 DAT overlay toggle. The viewport builds line boxes from
    `*.dat_world.yml` user portal center/dimensions and keeps the leaf/node part open until their spatial semantics are
    decoded enough to draw source-backed volumes or graph overlays.
  - [ ] physics BSP and visibility BSP helper geometry;
  - [ ] trigger volumes and object bounds;
    MM9 raw objects are now projected into the shared `Mm9ObjectLayer` with source object index, class/name, position,
    rotation, scale, `Dims`, `Radius`, `Visible`, `Solid`, and `Trigger` evidence. This gives the editor a typed source
    layer for object bounds and trigger-volume inspection. The native DAT viewport now builds a toggleable object-bounds
    overlay from that layer, using source `Dims`, `Radius`, and `Trigger` evidence without mutating the DAT/ODV/BLV
    source. Focused validation reports prove `thjorgard` has 704 positioned object sources, 273 object sources with
    bounds evidence, 12 trigger volumes, and 984 object overlay vertices; `thjorgardcity` has 1771 / 796 / 3 and 144
    object overlay vertices. Object-bound overlay picking now maps visible source-bound candidates back to lossless
    raw-object inspector rows by source object index; focused validation proves 41 pick candidates for `thjorgard` and
    6 for `thjorgardcity`, matching the currently visualized object-bound rows.
  - [x] movable world models and mechanism target groups;
    The MM9 DAT viewport now projects generated `*.events.yml` mechanism bindings into the source-inspection overlay
    behind the existing `Events` toggle. Each generated `odm_bmodel` target gets a DAT-world-model bounds box and,
    when the source mechanism object has a decoded position, a source-to-target link line and source marker. Picking the
    target overlay selects the generated `Mm9Mechanism` inspector row, preserving the path from source raw object to
    event binding to target DAT world model. Focused validation proves `thjorgard` has 124 mechanism target marker
    groups / 124 pick candidates / 3,968 marker vertices / 124 source links, and `thjorgardcity` has
    405 / 405 / 12,960 / 405.
  - [x] unresolved or missing asset markers.
    MM9 DAT documents now expose a dedicated `Issues` viewport toggle for unresolved or ambiguous raw-object asset
    references. The overlay only places markers for source objects with decoded source-backed positions from object,
    light, sound, spawn, or model-instance data; unpositioned issues remain inspector/report rows instead of invented
    coordinates. Clicking an issue marker selects the matching lossless raw-object sidecar row by source object index.
    Focused validation currently reports one optional positioned asset issue marker for `thjorgard` and one for
    `thjorgardcity`, with zero required issue markers and zero unpositioned required issue markers in the active slice.
- [ ] Support display filters:
  - [x] visual world geometry;
  - [x] invisible surfaces;
  - [x] sky surfaces;
  - [x] water/special material surfaces;
  - [x] physics blockers;
  - [x] visibility blockers;
  - [ ] portals/leaves;
    User portals are now exposed as an independent overlay toggle; leaf filters remain open because the decoded leaf
    records are not yet a renderable volume or graph overlay.
  - [ ] objects;
    Raw object rows remain lossless, and the typed object-source transform layer is now searchable and selectable from
    the scene tree. The MM9 toolbar now also exposes a `Bounds` overlay toggle for object bounds and trigger-volume
    wireframes, and the MM9 status strip includes submitted overlay vertices so screenshots like `test_img/923.png` can
    distinguish missing source-object rendering from hidden overlays. Current focused inspector-search evidence reports
    `object_sources=704` for `thjorgard` and `object_sources=1771` for `thjorgardcity`, matching the raw object counts.
  - [ ] actors/monsters;
  - [ ] sounds/lights/spawns;
    MM9 light raw objects are now projected into the shared `Mm9LightLayer` from source-preserved raw object properties
    and DAT `WorldInfo` lighting fields. The editor summary and search index expose typed light rows, and focused
    validation reports prove `thjorgard` has 30 light objects / 30 static render lights / 0 light diagnostics while
    `thjorgardcity` has 165 / 165 / 0. MM9 sound/voice raw-object asset references are also projected into the shared
    `Mm9SoundLayer` with source object index, class/name, property name, position, sound position, sound radius, and
    resolved source path evidence. Focused validation reports prove `thjorgard` has 69 sound objects with 73/73 resolved
    sound references and 0 unresolved required sound references, while `thjorgardcity` has 202 sound objects with 358/358
    resolved and 0 unresolved required. Spawn-bearing raw objects are now projected into the shared `Mm9SpawnLayer` with
    source object index, class/name, position, rotation, `SpawnLevel`, `SpawnObject`, `SpawnObjectVel`, `NPCProps`, and
    `NPCNbr` evidence. Focused validation reports prove `thjorgard` has 61 spawn source objects / 16 NPC numbers and
    `thjorgardcity` has 72 / 60. The native DAT viewport now exposes light and sound source markers through the
    existing `Entities` toggle and spawn source markers through the existing `Spawns` toggle; marker picking selects the
    matching lossless raw object row by source object index. Current active-slice overlay evidence is
    `light_overlay_vertices=7020`, `sound_overlay_vertices=6336`, and `spawn_overlay_vertices=798`
    (`thjorgard`: 1080 / 564 / 366; `thjorgardcity`: 5940 / 5772 / 432). Final in-world static-light rendering,
    positional audio playback, and spawn/actor visualization are still open.
  - [x] mechanisms/events.
    The existing `Events` display filter now covers MM9 DAT mechanism target overlays as well as generated event/raw
    object markers. Current active-slice summary evidence reports `mechanism_target_marker_groups=529`,
    `mechanism_target_marker_candidates=529`, `mechanism_target_marker_vertices=16928`, and
    `mechanism_target_marker_source_links=529`; the same reports now separately prove selectable mechanism gizmos with
    previewable mechanisms drawn green and inert assigned mechanisms drawn yellow-green:
    `mechanism_gizmo_candidates=801`, `mechanism_circle_gizmo_candidates=272`,
    `mechanism_target_gizmo_candidates=529`, `mechanism_motion_path_markers=165`,
    `mechanism_los_checked_candidates=529`, and
    `mechanism_los_blocked_candidates=94`.

### Shared Runtime Services

- [ ] Factor DAT parsing and DTX loading into reusable engine/game services, not editor-only code.
  Native DAT world/BSP parsing and source-index-preserving render mesh extraction now live under `game/mm9` and are
  shared by the editor document/headless validation path. DTX v2 header parsing, base-image decoding, mip payload
  enumeration, and section metadata parsing now live under `game/mm9`; editor metadata wraps those shared records for
  inspection. This item is still open until material/model/skin/source resolution and event binding are all shared
  instead of editor-local.
- [ ] Editor and game use the same DAT source-index model, material resolver, texture resolver, model resolver, and
  event binding resolver.
- [ ] Editor-specific UI code only presents and edits metadata; it must not duplicate gameplay event interpretation.
- [x] DAT world loading is gated by `kind: mm9_level` so regular ODM/BLV loading remains the default path.
  Current headless dispatch evidence proves that only `*.level.yml` MM9 entrypoints load native DAT sidecars/world
  state; representative legacy ODM/BLV paths load outdoor/indoor documents and do not report loaded MM9 sidecars.
- [ ] `[runtime-blocked]` Do not add playable MM9 game-world behavior until the active two-map editor gate proves source
  reference resolution and lossless sidecar binding for the active maps.

## Required Inspectors

### Level Inspector

- [x] Display `kind`, map id, display name, classification, source DAT path, original DAT path, DAT hash, compatibility
  artifacts, and sidecar paths.
- [x] Show whether runtime backend is `dat_world`.
- [x] Show whether compatibility ODM/BLV files exist and mark them as derived only.
- [x] Show the document path inventory split into read-only source, generated sidecars/scripts/caches, authored
  entrypoints, and derived compatibility artifacts.
  Active validation reports now serialize the same split under `document_paths`, including explicit
  `source_read_only_files`, `authored_files`, `authored_overrides`, `generated_files`, and
  `compatibility_derived_files` entries. Current evidence: `thjorgard` reports 77 total document paths with 2
  read-only source paths, 74 generated paths, 2 authored paths, 1 authored override path, 4 compatibility-derived paths,
  and 0 missing paths;
  `thjorgardcity` reports 153 total paths with 2 read-only source paths, 150 generated paths, 2 authored paths,
  1 authored override path, 4 compatibility-derived paths, and 0 missing paths.
- [x] Provide one-click validation for all referenced sidecars and assets.
  The MM9 DAT summary inspector now has a `Validate Referenced Sidecars And Assets` action backed by the current
  document path inventory, source manifest diagnostics, asset dependency summary, material DTX/cache status, raw-object
  required asset refs, and document validation messages. The action reports success only when blocking counts are zero;
  otherwise it reports the blocking issue count in editor chrome.

### Source Manifest Inspector

- [x] Show `source/manifest.yml` counts and extracted REZ family mappings.
- [x] Verify that required source families exist: worlds, textures, skins, models, scripts, rude, data, sounds, voices,
  sprites, sprite textures, art, localart, clientfx.
- [x] Show source tree drift from the expected mirrored extraction.
  `--headless-verify-mm9-source-manifest` validates the active MM9 source manifest without opening maps. Current
  evidence: `assets_dev/worlds/mm9/source/manifest.yml` declares 14 required families and 12,646 source files, and the
  mirrored `source/*` tree currently has exactly 12,646 files.
- [x] Report accidental edits under `source/*` when hashes/manifests are available.
  Level entrypoints already store SHA-256 hashes for the source DAT file and `validateMm9DatLevelMetadataFiles` rejects
  stale source DAT hashes. The active DAT-level validation report now exposes `source_integrity` with source DAT hash
  verification, level-load diagnostics, source manifest diagnostics, declared/required family counts, expected/actual
  source file totals, count-drift family counts, missing source directory counts, and a before/after source-integrity
  snapshot around the active DAT-level open/validation/save-rejection/build-rejection flow, plus before/after content
  digests for resolved source files referenced by material, sprite-frame, and raw-object asset inspection. Current
  focused evidence: `thjorgard.level.yml` reports `source_mutation_snapshot_verified: true` across 243 referenced
  source files, and `thjorgardcity.level.yml` reports `source_mutation_snapshot_verified: true` across 443 referenced
  source files. Both maps also report `source_dat_hash_verified: true`, `source_dat_hash_diagnostics: 0`,
  `source_manifest_diagnostics: 0`, `source_manifest_expected_files: 12646`, `source_manifest_actual_files: 12646`,
  `source_manifest_count_drift_families: 0`, and `source_manifest_missing_directories: 0`.

### DAT World Inspector

- [x] Tree view of DAT world models with source indexes, names, roles, flags, bounds, and counts.
- [x] Per-world-model sections for:
  - [x] points;
  - [x] planes;
  - [x] surfaces;
  - [x] polygons;
  - [x] nodes;
  - [x] leaves;
  - [x] user portals;
  - [x] PBlock/root/section metadata.
    `*.dat_world.yml` now preserves each model's root node index, section count, raw BSP count fields, unknown header
    values, and decoded PBlock dimensions/bounds/record count while leaving PBlock record payloads in source DAT.
- [x] Preserve and display unknown fields instead of hiding them.
  DAT world-model unknown header values, DAT surface unknown fields, polygon unknown flags/lists, DTX header unknowns,
  and user portal raw unknown fields are parsed into typed inspector state and displayed rather than discarded. Current
  active verifier evidence: `thjorgard.level.yml` reports `dat_world_models_with_unknown_values=316` and
  `dat_world_user_portals_with_raw_unknowns=0`; `thjorgardcity.level.yml` reports
  `dat_world_models_with_unknown_values=787` and `dat_world_user_portals_with_raw_unknowns=35`.
- [x] Show helper roles such as `PhysicsBSP`, `VisBSP`, sky, water, invisible helper, movable world model, and trigger
  geometry.
- [x] Validate leaf polygon references, portal references, surface texture indexes, vertex ranges, and source-index
  bounds.
  Generated DAT world sidecars now include blocking aggregate checks for leaf polygon refs, user portal model refs,
  surface texture refs, polygon surface/plane/vertex refs, node polygon refs, root node refs, and source model/texture
  row indexes. `WorldNode.leaf_index` is intentionally not treated as a direct leaf-array index until its MM9 semantics
  are verified.

### Surface And Material Inspector

- [x] Selecting a polygon shows its source model index, polygon index, surface index, texture index, DAT surface flags,
  DTX user flags, DTX surface flag, effect name/parameter, UV vectors, plane, vertices, and bounds.
  The editor now uses a native DAT render-triangle selection payload that walks back to parsed DAT world model,
  polygon, surface, plane, point, material-alias, and DTX-header records instead of inventing ODM/BLV face ids.
  The polygon inspector also displays the shared DAT render-filter classifier entry for the selected triangle, including
  filter flags, default-render participation, pick-mesh participation, visual/invisible/helper status, PhysicsBSP,
  VisBSP, trigger/volume, sky, water, terrain, and movable flags. These values come from the same
  `classifyMm9DatRenderMeshFilters` path used by headless validation and viewport subset rendering.
- [x] Show distinct DAT surface flags and DTX user flags; never collapse them into one field.
- [x] Show resolved material alias from `*.material_aliases.yml`.
  DAT world-model texture rows now show the resolved map-local material alias, source-DTX resolution state, ambiguity
  state, resolved source path, and allow jumping to the matching DTX material inspector row.
- [x] Show original DTX path from `*.material_aliases.yml` when inspecting a material texture row.
- [x] Show missing/ambiguous texture references as blocking diagnostics.

### DTX Texture Inspector

- [x] List every DTX used by the opened map, including source path and map-local alias.
- [x] Display DTX v2 header fields: version, dimensions, mip count, section count, flags, user flags, extra fields,
  command string, format/BPP, texture group, detail scale, and detail angle.
  The inspector names LithTech `m_UserFlags` explicitly and keeps the older `surface flag` alias visible because the
  generated sidecar currently stores that value as `dtx_surface_flag`.
- [x] Display DTX mip payload offsets/sizes/dimensions and LithTech section headers when present.
- [x] Preview decoded base image and mips when available.
  The material texture inspector now decodes supported source DTX mip payloads through shared `game/mm9` code, uploads
  them to editor bgfx preview textures, and renders them inline without relying on generated `.bitmaps/*` caches.
  SPR-backed DAT surface materials preserve their source `.spr` identity for inspection and validation, and the editor
  now records resolved sprite-frame DTX paths so the viewport can use the first resolved frame as a static source-DTX
  preview. Animated SPR material playback remains a separate rendering task.
- [x] Show generated cache path and freshness relative to DTX hash.
  Current editor metadata computes the resolved source DTX SHA-256, generated cache SHA-256, file sizes, and
  timestamp staleness. Deterministic cache regeneration is still tracked separately below.
- [x] Validate that every DAT texture reference resolves case-insensitively to exactly one source DTX.
- [x] Validate that every decoded cache can be regenerated deterministically.
  Material texture inspection now decodes non-placeholder source-DTX cache modes through shared C++ DTX loading,
  decodes the generated BMP cache through the engine image loader, and requires matching dimensions and BGRA pixels.
  Cache drift is a blocking material validation issue, a report-clean blocker, and a normalized diagnostics row.
  Focused unit coverage accepts the generated MM9 material aliases and rejects a deliberately drifted decoded cache.

### Object And Property Inspector

- [x] List every DAT object with source object index, class/type, name, transform, dimensions, flags, and property
  count.
- [x] Show each decoded property with raw property code, decoded value, raw bytes, consumed length, declared length, and
  trailing bytes.
- [ ] Highlight unresolved object references:
  - [x] model file;
  - [x] skin file;
  - [x] sprite/texture;
  - [x] sound/voice;
  - [x] script file;
    Raw object string properties are now classified into source families and resolved case-insensitively against
    `source/models`, `source/skins`, `source/textures`, `source/sprite_textures`, `source/sprites`, `source/sounds`,
    `source/voices`, and `source/scripts`. The object inspector shows resolved path, unresolved state, and ambiguity.
    Embedded official `ScriptParams` references such as `268 models\Props\Maypole.ABC skins\Props\Maypole.dtx` and
    `\voices\npc\NPC_125.wav 455` are split into individual source-file references. Remaining official unresolved refs
    are tracked as diagnostics counters until the full asset graph adds alias/remap rules for LithTech resource aliases
    and absent/moved source assets. If an exact family-relative path does not exist, the resolver falls back to a
    basename match only when that basename is unique in the source family; multiple matches remain ambiguous.
    `WorldProperties` sky/environment texture names are preserved as visible optional references and resolved as
    LithTech world-property sky-controller metadata when the official source tree has no matching DTX; placed object
    model, skin, sound, sprite, script, and voice references remain required. The active two-map slice now resolves the
    official-but-absent Thjorgard `Barrel02` model/skin refs and
    Thjorgard City `Sounds\GIBS\GLASS\EXPLODE_2.WAV` refs through an explicit authored
    `import/overrides/mm9_active_slice.source_asset_aliases.yml` sidecar. Those aliases are scoped by map, source object
    index, and property, and preserve the original raw DAT property values in `*.raw_objects.yml`. The raw object
    inspector now also shows per-object required issue, optional issue, and ambiguity counts, an explicit issue label for
    every source-asset reference, and the candidate paths that made a reference ambiguous. Active validation reports keep
    the corresponding unresolved required/optional reference lists under `raw_object_asset_references`.
  - [ ] script function/message;
  - [ ] target object;
  - [ ] target world model;
  - [ ] event command;
  - [ ] AI/actor template;
  - [ ] dialogue or data-table row.
  Generated `*.events.yml` unresolved rows are now preserved as typed event-sidecar entries instead of only an aggregate
  count. The MM9 document summary shows kind, severity, source object index/name/class, nearest movable DAT world-model
  evidence counts, and a jump back to the raw object. DAT-level validation reports count unresolved event warnings,
  errors, and candidate evidence. Current focused evidence: `thjorgard` has 4 unresolved event warnings, 0 errors, and
  20 nearest-position movable DAT candidates; `thjorgardcity` has 1 unresolved event warning, 0 errors, and 5
  nearest-position candidates. These are still non-blocking `ScriptObject` binding warnings until script/event command
  semantics decide whether an explicit override is required.
- [x] Allow object selection to jump to matching event, script IR, world model, or asset dependency.
  MM9 raw-object, event-object, and mechanism inspectors now expose explicit selection jumps to linked raw objects,
  generated event objects, generated mechanisms, and generated target DAT world models. Source-asset and generated
  script/IR rows are covered by the adjacent copy/open-path controls, so the inspector graph can be followed without
  manually searching ids.

### Event And Script Inspector

- [x] Display `*.events.yml`, `*.raw_objects.yml`, generated Lua, and source SCR/INC provenance.
  The MM9 event generator now emits the split `events/<map>.script_ir.yml` files declared by the level YAML. The active
  two-map slice has generated IR sidecars for `thjorgard` and `thjorgardcity`, and their event sidecars record the
  matching `generated.script_ir` path next to generated Lua.
- [x] Show object bindings and the source raw-property evidence used to infer each event object.
- [x] Show unresolved object names, source object indexes, binding targets, and missing source scripts as blocking
  diagnostics.
- [x] Support opening generated Lua read-only when generated from source.
  Selecting an MM9 script now exposes read-only previews for the generated Lua and generated script-IR files declared by
  the level/events sidecars. The preview records the physical path, existence, loaded state, byte size, truncation
  status, and read-only status, and displays file contents without providing an editor path for mutating generated
  files. Headless event provenance now reads the generated Lua and script-IR text, checks expected generated markers,
  and reports byte counts. Active evidence: `thjorgard.lua` is readable at 7,172 bytes and `thjorgardcity.lua` is
  readable at 4,273 bytes through `--headless-verify-mm9-event-provenance`.
- [x] Support authored override files separately from generated Lua and generated event YAML.
  The event script provenance inspector now shows generated Lua and generated script IR as generated files, and shows
  the optional source-asset-alias sidecar separately as `Authored Source Asset Aliases` with role `authored_override`.
  This matches the document path inventory, asset graph `authored_overrides` family, active validation report
  `document_paths.authored_overrides` bucket, and focused unit/headless assertions that source-asset aliases are
  authored override data rather than generated event output.
- [x] Provide a per-map event validation action that matches the headless validator.
  `--headless-verify-mm9-events <level.yml>` now opens the MM9 DAT document through `EditorSession`, requires
  `EditorDocument::Kind::Mm9Dat`, cross-checks the level-declared event sidecar, generated Lua, and generated
  script-IR paths, verifies generated file markers and byte counts, validates raw-object provenance, source SCR
  existence, binding object references, DAT world-model target indexes, and mechanism/source-object links, and reports
  unresolved binding targets without hiding them. Active evidence: `thjorgard.level.yml` passes with 704 event objects,
  22 source scripts, 66 mechanisms, 556 bindings, 871 binding targets, and 4 unresolved non-required targets;
  `thjorgardcity.level.yml` passes with 1,771 event objects, 18 source scripts, 206 mechanisms, 1,578 bindings,
  2,364 binding targets, and 1 unresolved non-required target. Required mechanism targets are enforced by the
  DAT-level validation report rather than guessed in this map-wide structural check.
  The editor-side event script model now also loads generated script `includes` and labels into the inspector and
  active reports. Current active DAT-level evidence records `script_includes=38` and `script_labels=167` for
  `thjorgard`, `script_includes=22` and `script_labels=108` for `thjorgardcity`, active-slice totals of 60 includes
  and 275 labels, and 60/60 source include files resolved with zero unresolved or ambiguous includes.

### Mechanism Inspector

- [x] List generated mechanisms from `*.events.yml` with MM9 source object identity.
- [x] Display mechanism source evidence from DAT raw object properties, generated events, and generated binding targets.
  The interactive mechanism inspector now also shows the nearest movable DAT world models by rotation point for
  rotating mechanisms. This mirrors the headless unresolved-target evidence and makes cases such as
  `thjorgardcity` object 1095 `BembStudy3` inspectable without manually searching the YAML sidecars.
  The MM9 event generator now also writes nearest movable DAT world-model candidate evidence into unresolved binding
  targets and unresolved diagnostics in the generated `*.events.yml` sidecars. This keeps the unresolved-target
  investigation source-sidecar backed instead of leaving it only in editor-local validation reports. The C++ events YAML
  loader now preserves both `nearest_movable_world_models_by_rotation_point` and
  `nearest_movable_world_models_by_position`, including exact-binding claims that explain when a nearby candidate is
  already owned by another source object, and the inspector displays that generated sidecar evidence alongside the
  editor-recomputed nearest-candidate view. The generator also has a source-backed shared-rotation-point rule for
  rotating doors whose named object has no separate DAT model: `BembStudy3` now binds to DAT bmodel 122 `BembStudy2`
  with confidence `shared_rotation_point_exact_source_object_position`, because its `RotationPoint` exactly matches
  source object 131 `BembStudy2`'s authored position.
- [x] Show source world model indexes for generated binding targets and keep ODM/BLV face ids out of primary
  mechanism identity.
- [x] Detect movable world models directly from DAT flags plus object/script evidence.
  DAT world-model `roles.movable` is loaded from the generated DAT-world sidecar, which derives it from the DAT
  `world_info_flags` movable bit. Mechanism validation now cross-checks every generated world-model mechanism target
  against those DAT roles and reports `world_model_targets_with_movable_role`,
  `world_model_targets_without_movable_role`, and `world_model_targets_missing_model`. The mechanism inspector also
  shows the selected target DAT model roles next to the generated object/script binding confidence. Current active-slice
  evidence: `thjorgard` has 314 movable DAT world models and 124/124 mechanism world-model targets with the movable
  role; `thjorgardcity` has 785 movable DAT world models and 405/405 mechanism world-model targets with the movable
  role.
- [x] Show source face/polygon groups for mechanism targets when the sidecar generator emits them.
  Generated `*.events.yml` binding targets now include a `source_polygon_group` block for DAT world-model targets. The
  block preserves the DAT source model index/name, source polygon count, source surface count, bounds, and role bits
  from `*.dat_world.yml`. The C++ event sidecar loader preserves this evidence, the mechanism inspector displays the
  group next to each generated target, and headless validation rejects missing or mismatched polygon groups for
  mechanism world-model targets.
- [ ] Show trigger bindings, toggle state, open/closed/default state, movement vector/rotation, speed, timing, sound,
  blockers, and script callbacks when known.
  Partial trigger-output coverage now exists: generated mechanism `trigger_outputs` are loaded from `*.events.yml`,
  preserved as typed event-sidecar data, counted by headless DAT validation, and displayed in the mechanism inspector
  with phase, slot, target object name, message name, and resolution. Current focused evidence: `thjorgard` has 6
  mechanism trigger outputs and 0 unresolved trigger outputs; `thjorgardcity` has 0 mechanism trigger outputs.
  Generated script `registered_triggers` and `trigger_edges` are also loaded as typed event-sidecar data and displayed in
  the event script inspector with source line, callback/message expression, and raw argument text. DAT-level validation
  now counts them: `thjorgard` reports 44 registered script triggers and 29 trigger edges, while `thjorgardcity` reports
  20 registered script triggers and 1 trigger edge. Generated script `movement_commands` and `unknown_commands` are also
  loaded as typed rows and displayed with source line, command name, and raw argument text. Current focused evidence:
  `thjorgard` reports 11 movement commands and 465 unknown commands; `thjorgardcity` reports 5 movement commands and
  372 unknown commands. The generated per-script `command_count` is preserved and reported as well, currently 1,417
  total script commands for `thjorgard` and 1,140 for `thjorgardcity`. Generated mechanism sound slots are now loaded
  from `*.events.yml`, preserved as typed sidecar data, counted by DAT validation, and shown in the mechanism inspector
  with phase/property/sound/authored evidence. Current active-slice evidence records `mechanism_sound_slots=1064`,
  `mechanism_authored_sound_references=304`, and `mechanism_empty_sound_references=760`. Known generated activation,
  rotation, and timing fields are also now loaded as typed event-sidecar data, displayed in the mechanism inspector, and
  counted by DAT validation. Current active-slice evidence records
  `mechanism_activation_start_open_fields=152`, `mechanism_activation_locked_fields=152`,
  `mechanism_activation_push_open_fields=152`, `mechanism_activation_touch_to_open_fields=152`,
  `mechanism_activation_lock_on_close_fields=0`, `mechanism_activation_reopen_on_contact_fields=152`,
  `mechanism_rotation_open_away_fields=80`, `mechanism_timing_move_delay_fields=152`, and
  `mechanism_timing_open_wait_fields=152`. This item remains open until blockers and complete script callbacks are
  represented and diagnosed.
- [x] Preview mechanism movement in the DAT viewport without modifying source DAT geometry.
  The DAT viewport applies generated linear/rotation mechanism motion as per-world-model render transforms, so
  `Closed`, `Half`, `Open`, and `Clear` preview controls no longer rebuild or mutate the source render mesh. Mechanism
  target groups also expose selectable projected handles on each bound DAT world-model target, so one mechanism driving
  multiple door leaves presents one selectable handle per moving leaf. Previewable mechanisms use brighter green source
  and target circle handles, while assigned mechanisms that are inert in the preview system use yellow-green handles.
  Projected MM9 DAT editor handles now share the MM6-MM8-style distance scale/fade behavior and lower their alpha when
  native DAT world-model bounds block line of sight, avoiding per-frame scans over every DAT render triangle. The
  viewport now also caches each loaded document's mechanism source marker, target world-model bounds, previewability,
  and open-motion transform data, so `Closed`/`Half`/`Open`/`Clear` update only preview progress instead of
  rediscovering bindings and movement data in the preview frame. The MM9 viewport also caches the scripted-billboard
  visual set per active MM9 world, so scripted object collision markers do not reload billboard YAML during interactive
  overlay/preview frames. Headless active-slice validation now proves 83 previewable mechanisms and 189 inert
  mechanisms; all 272 mechanisms have
  selectable circle gizmos, all 529 target groups have selectable target gizmos, all 165 previewable mechanism targets
  have motion-path markers, and all 529 target gizmos pass the bounds-based line-of-sight fade check, with 94 currently
  reported as occluded/faded.
- [ ] Report incomplete mechanism data as blocking until it is represented in generated sidecars or explicit overrides.
  Current headless validation now writes a `mechanisms` section into the active-slice asset reports and includes
  unresolved required mechanism targets in the report `clean` decision. `thjorgard` currently reports 66 mechanisms,
  4 unresolved non-required `ScriptObject` targets, and 0 unresolved required mechanism targets. `thjorgardcity`
  currently reports 206 mechanisms, 1 unresolved non-required `ScriptObject` target, and 0 unresolved required
  mechanism targets. The report now includes shared-rotation-point binding evidence for source object 1095
  `RotatingDoor` / `BembStudy3`: the generated sidecar binds it to DAT bmodel 122 `BembStudy2`, records the shared
  source object index 131, and preserves the exact rotation point that proves the intended shared target. This removes
  the previous required mechanism blocker without inventing an ODM/BLV face-list identity.

### Portal, Visibility, And Collision Inspector

- [ ] Show DAT leaves, nodes, user portals, visibility blockers, physics blockers, not-a-step surfaces, and helper BSPs.
- [ ] Classify and inspect DAT rail/helper containers separately from visible world art.
  Active Thjorgard evidence identifies `TEXTURES\LevelTextures\Misc\rail.dtx`, DAT world models named `AITrk*`, raw
  object rail properties, and scripts that query `AIRail` containers. Preserve this geometry losslessly, but hide it in
  the default textured view. The inspector should expose source model index/name, `rail.dtx` material, surface flags,
  object/script references, and whether the rail participates in container/path/navigation semantics. The active
  classifier now identifies `AITrk*` and `rail.dtx` triangles as `Mm9DatRenderFilterRail`, prevents them from counting
  as normal visual art even when a sidecar marks the source model visible, keeps them inspectable through the helper
  subset, and shows `Rail Or AIRail Helper` in the selected DAT surface inspector. Focused validation reports
  `thjorgard` with `rail=2460` and `thjorgardcity` with `rail=5704`, and fails if rail triangles are missing the helper
  filter.
- [ ] Classify visible water surfaces separately from water volumes and markers.
  Active Thjorgard evidence shows multiple water heights: visible `Ocean` geometry uses `Sprites\Water\Ocean4.spr`
  around LithTech `Y=314`, while `BlueWater*` models use `Invisible.dtx` or `WaterMarker.dtx` as volume/marker/helper
  surfaces at other vertical ranges. The default textured view should render visible water/effect surfaces, but should
  not draw water volumes or marker/invisible water brushes as opaque normal geometry. Water volumes remain source-backed
  helper overlays and validation/runtime collision/container inputs. The active classifier now splits water into
  `Mm9DatRenderFilterVisibleWater` and `Mm9DatRenderFilterWaterVolume`, hides the volume/marker filter from the default
  editor view, keeps it in the helper subset, and exposes both booleans in the selected DAT surface inspector. Focused
  validation reports `thjorgard` with `visible_water=13` and `water_volume=86`, and `thjorgardcity` with
  `visible_water=0` and `water_volume=48`; it also fails if water-volume triangles are missing the helper filter.
- [x] Allow toggling between visual, physics, and visibility worlds.
  The MM9 DAT viewport toolbar now exposes source-backed DAT world subset modes for normal/default DAT rendering,
  sky geometry, PhysicsBSP geometry, water/effect-role geometry, visibility-helper geometry, invisible surfaces,
  helper surfaces, and trigger/volume geometry, plus separate model-instance and user-portal overlay toggles. This
  closes the coarse viewport switch needed for inspection; leaf/node overlays and full per-surface collision semantics
  remain separate open tasks.
- [x] Show collision material classification from DAT flags and DTX user flags.
  The DAT polygon inspector now has a `Collision And Material` section that keeps DAT `Surface.flags` and DTX
  `m_UserFlags` separate while naming the locally verified LithTech bits: `SURF_SOLID`, `SURF_NONEXISTENT`,
  `SURF_INVISIBLE`, `SURF_TRANSPARENT`, `SURF_SKY`, `SURF_PORTAL`, `SURF_PHYSICSBLOCKER`, `SURF_VISBLOCKER`, and
  `SURF_NOTASTEP`. It reports solid candidate, physics blocker, visibility blocker, not-a-step, portal, invisible,
  sky, and the material contact metadata source without treating DTX user flags as a replacement for DAT surface flags.
- [x] Show whether a selected surface participates in render, physics, visibility, picking, or script interaction.
  The DAT polygon inspector includes a `Surface Participation` block with default-render participation, pick-mesh
  participation, visual/invisible/helper roles, physics and visibility blockers, trigger/volume classification, sky,
  water, terrain, and movable flags derived from the same render-filter classifier used by the viewport.
  Partial active-slice coverage now exists in the DAT polygon inspector: selected render triangles show default render
  participation, pick-mesh participation, PhysicsBSP, VisBSP, and trigger/volume participation from source DAT flags
  plus generated DAT world-model roles. This remains open until collision material semantics and general script/event
  face interaction are fully represented, rather than only the DAT trigger/volume role.
- [x] Validate that physics BSP and visibility BSP helper world models are preserved and not accidentally rendered as
  normal art.
  Unit coverage classifies real Thjorgard helper geometry with nonzero helper, physics, and visibility triangle counts
  and zero unclassified triangles. The active DAT-level verifier now also fails if declared `PhysicsBSP` models produce
  no physics-filter triangles, declared `VisBSP` models produce no visibility-filter triangles, or helper BSP triangles
  are not included in the helper filter. Current focused evidence: `thjorgard.level.yml` reports
  `physics_bsp_models=1`, `vis_bsp_models=1`, `native_filter_helper=15338`, `native_filter_physics=10850`, and
  `native_filter_visibility=644`; `thjorgardcity.level.yml` reports `physics_bsp_models=1`, `vis_bsp_models=1`,
  `native_filter_helper=72912`, `native_filter_physics=48297`, and `native_filter_visibility=15147`.

### Asset Dependency Graph Inspector

- [ ] Build a per-map graph from level YAML, DAT world, DTX aliases, raw objects, events, source scripts, data/RUDE
  tables, model registries, generated caches, and authored overrides.
  Current editor document state now builds a typed partial asset dependency summary from level DAT/source sidecars,
  source data/RUDE family roots, material DTX/cache inspection, generated Lua/script IR paths, raw-object source-file
  references, the source-manifest inventory, and the active authored source-asset alias override file. Model
  registries, actor/monster variants, and any future authored override families still need to be folded into the same
  graph before this item is complete.
- [ ] Group references by source family:
  - [x] worlds/DAT;
  - [x] textures/DTX;
  - [x] skins/DTX;
  - [x] models/ABC/LTB source files;
  - [x] sprites/sprite textures;
  - [x] sounds;
  - [x] voices;
  - [x] scripts/SCR/INC and generated Lua/script IR;
  - [x] RUDE/data tables;
  - [x] generated events/Lua;
  - [x] generated caches.
  Generated event Lua/script-IR files, source data/RUDE table roots, and generated material caches now have explicit
  asset graph families (`generated_events`, `data`, `rude`, and `generated_caches`) with required
  resolved/unresolved/stale counters. Unit coverage asserts these families directly, and active validation reports
  include the same per-family graph rows. Current active-slice reports are clean with `data` and `rude` resolved for
  both maps, `asset_graph_total=821` / `asset_graph_resolved=821` for `thjorgard`, and
  `asset_graph_total=2229` / `asset_graph_resolved=2229` for `thjorgardcity`.
- [x] Provide global counters: resolved, unresolved, ambiguous, stale cache, unused source, and source-only.
  Asset graph summaries now expose total, resolved, unresolved, ambiguous, stale, source-only, and unused-source
  counters globally and by family. `source_only` is sourced from the declared source-manifest file inventory, while
  `unused_source` is the per-family source inventory minus the current per-map graph references. The reports also
  separate required and optional resolved/unresolved/ambiguous counters so optional source evidence remains visible
  without blocking the active slice. Current active reports are clean with `source_only=12646`,
  `unused_source=11895` for `thjorgard`, and `unused_source=10563` for `thjorgardcity`; the active-slice summary
  reports `asset_graph_source_only=25292` and `asset_graph_unused_source=22458`.
- [x] Block "validated" status unless unresolved and ambiguous counts are zero.
  The MM9 document summary validation action now reports success only when required document paths, source manifest
  checks, required asset-graph unresolved/ambiguous counters, material/source-DTX or sprite-frame checks, required raw
  object asset refs, and document validation diagnostics are clean. Its material blocker logic matches the headless
  active-slice clean gate, so optional `WorldProperties` sky/environment-map entries remain visible as built-in
  sky-controller metadata instead of validating as required source-file data loss.

### Actor And Monster Variant Inspector

- [ ] Resolve every actor/monster object to the official MM9 data chain that defines its visual and gameplay identity.
- [ ] Show variant id/name, model or billboard source, animation source, skin/texture source, sound/voice set, spawn
  settings, faction/team/alignment where available, and map object source index.
  Current partial coverage: selecting a DAT-backed MM9 model instance or scripted object now works in the inspector for
  `kind: mm9_level` documents and shows the source object ref, class, object name, source model, source skin, generated
  model asset, resolved actor-table variant id when one is inferred, resolved model/skin, resolved generated asset, and
  source position. The resolver now also preserves the official actor-table evidence row for inferred variants, including
  source table, row, number, monster name, type picture, and base name. The model-instance inspector displays those fields,
  and DAT-level validation reports `actor_variant_actor_rows`; current focused evidence is 53/53 actor variants with
  actor-row evidence for `thjorgard` and 60/60 for `thjorgardcity`. The resolver now also enriches those rows from the
  official MM9 `source/data/ACTOR.txt` and `source/data/MONSTERS.txt` tables, preserving gameplay identity fields such
  as level, HP, AC, EXP, speed, script name, foot sound, monster flag, hostility group, and voice radius in the
  inspector/search/report path. The actor resolver now also resolves official `FootSound` tokens against
  `source/sounds/ANIMSOUNDS/FOOTSTEPS`; current active-slice evidence reports
  `actor_variant_gameplay_identity_rows=53/53` and `actor_variant_resolved_foot_sounds=43/43` for `thjorgard`,
  `60/60` and `60/60` for `thjorgardcity`, and `113/113` gameplay rows plus `103/103` foot-sound resolutions in the
  active-slice summary. Object-authored actor voice references are also folded into the actor-variant report path:
  `thjorgard` resolves `1/1`, `thjorgardcity` resolves `28/28`, and the active summary resolves `29/29` with
  `actor_variant_unresolved_source_voice_references=0`. The selected-object actor variant inspector now also makes
  the faction/alignment boundary explicit: MM9 actor tables provide a source `Hostility Group`, the generated event
  sidecar can match the actor script and count hostility-related includes, registered triggers, and trigger edges, and
  there are no explicit `ACTOR.txt`/`MONSTERS.txt` team or alignment columns. Spawn source settings are currently
  exposed through the MM9 raw-object/spawn source layer rather than centralized in the actor variant section.
- [ ] Support both 3D model rendering and generated billboard rendering as presentation choices; the source asset
  identity must remain the same.
- [ ] Validate all actor/monster model, skin, animation, sprite, sound, and voice references.
- [x] Provide a missing-variant report for any map object that cannot be resolved to a complete visual/gameplay variant.
  Active validation reports now include a dedicated `actor_variants` section with variant counters and
  `missing_variants` entries keyed by source object index/ref/class/name/model/skin when the actor resolver cannot bind
  a map object. Current active-slice evidence is clean: `thjorgard` reports 53 candidates, 53 resolved, 0 unresolved,
  and `missing_variants: []`; `thjorgardcity` reports 60 candidates, 60 resolved, 0 unresolved, and
  `missing_variants: []`.

### Diagnostics Panel

- [x] Centralize diagnostics from all inspectors.
  The MM9 DAT document summary now has a centralized `Diagnostics` section sourced from document validation, document
  path inventory, source manifest validation, material/DTX resolution, raw-object source-asset resolution, and
  mechanism target binding. It also emits actor/monster variant diagnostics for unresolved actor-source variants,
  unresolved official foot-sound aliases, and unresolved or ambiguous object-authored actor sound/voice references. The
  table shows severity, source, source index path, sidecar, resolver, suggested owner, and message in one editor surface
  instead of forcing the user to inspect each subsystem panel separately.
- [x] Each diagnostic includes severity, source file, source index/path, sidecar path, resolver name, and suggested
  owner: parser, sidecar generator, authored override, or source asset mirror.
  Active per-map validation reports now include a normalized `diagnostics` stream with `severity`, `source_file`,
  `source_index_path`, `sidecar_path`, `resolver`, `suggested_owner`, and `message` on every entry. The active-slice
  summary report aggregates these as `diagnostic_errors`, `diagnostic_warnings`, and `diagnostic_info`. Current evidence:
  `thjorgard` reports 0 errors and 18 warnings; `thjorgardcity` reports 0 errors and 15 warnings. The active-slice
  summary reports 0 diagnostic errors and 33 diagnostic warnings.
- [x] Severity rules:
  - [x] `error`: parse failure, invalid source index, unresolved required asset, ambiguous required asset, generated
    sidecar data loss, stale hash mismatch, source mutation.
  - [x] `warning`: unused source asset, optional preview cache missing, unsupported preview-only metadata.
  - [x] `info`: derived compatibility artifact missing, cache regenerated, optional override absent.
  The shared MM9 metadata layer now exposes `mm9DiagnosticSeverityRules()` so the editor UI, headless report, and unit
  tests use the same policy. The active validation report serializes this under `diagnostics.severity_policy`, and the
  editor `Diagnostics` panel displays the same rows before the diagnostic table. Optional placeholder preview material
  remains a warning class, while LithTech `Default` helper material is now classified separately when it is only used by
  hidden helper geometry. Unused source-family inventory is surfaced as non-blocking warnings. Current active-slice
  reports list `thjorgard` at 0 errors and 18 warnings, and `thjorgardcity` at 0 errors and 15 warnings.

## Sidecar And Data Requirements

- [x] `*.level.yml` contains every path needed to open the map without guessing.
  Level metadata now declares `source.manifest` alongside `source.dat`, and the document loader, source-integrity
  snapshot, document path inventory, source-manifest validation, and asset graph use the declared manifest path instead
  of deriving it from the map directory. The native sidecar generator emits this field, and all 45 `assets_dev` plus
  all 45 `assets_editor_dev` MM9 level entrypoints now include `manifest: ../source/manifest.yml`. Focused metadata
  tests assert the active maps parse this path, and active headless validation for `thjorgard` and `thjorgardcity`
  passes with `source_manifest_diagnostics=0`.
- [ ] `*.dat_world.yml` contains enough source-index metadata for editor inspection and validation but does not replace
  the source DAT as geometry truth.
- [x] `*.material_aliases.yml` maps DAT texture names to original DTX source paths and decoded cache paths.
  Material alias parsing now preserves whether the required `alias`, `source_texture`, `emitted_bitmap`, and
  `emitted_bitmap_mode` fields were actually present, and material validation reports missing/empty fields as generated
  sidecar data loss through `mm9_material_alias_sidecar_validator`. Active headless validation for `thjorgard.level.yml`
  and `thjorgardcity.level.yml` still reports `material_textures.invalid_or_unresolved: []`; the active-slice summary
  remains clean with 0 diagnostic errors and the existing 35 unused-source inventory warnings.
- [x] `*.raw_objects.yml` preserves every DAT object/property and raw payload boundary.
  Raw object validation now checks object count, source object indexes, property count, unknown-property count, property
  names, raw hex byte integrity, trailing hex integrity, raw hex length against consumed property bytes, and that
  decoded/trailing payload bytes stay within the enclosing object `data_length` boundary. The headless clean gate now
  treats raw-object sidecar validation issues as generated sidecar data loss through
  `mm9_raw_object_sidecar_validator`. Current active reports for `thjorgard.level.yml` and
  `thjorgardcity.level.yml` both show `raw_object_sidecar_issues: 0`, and the all-generated-map raw sidecar unit sweep
  accepts all 45 `assets_dev/worlds/mm9/maps/*.raw_objects.yml` files.
- [ ] `*.events.yml` describes OpenYAMM event bindings derived from source objects/scripts.
- [ ] `*.script_ir.yml` preserves script control-flow evidence for generated Lua.
  Active-slice split IR sidecars now preserve source script ids, source paths, includes, labels, registered triggers,
  trigger edges, movement/state/presentation command summaries, unknown commands, and command counts for `thjorgard`
  and `thjorgardcity`. The editor loader now carries includes and labels through `Mm9EventScript`; selecting an MM9
  event script shows include and label rows, and the active report/gate records nonzero include/label totals plus
  resolved source include counts.
- [x] Optional authored overrides are explicit and separate from generated files.
  The active two-map slice uses `import/overrides/mm9_active_slice.source_asset_aliases.yml` for missing official source
  asset aliases. Level entrypoints reference it through `sidecars.source_asset_aliases`; the resolver treats it as
  authored override data, not generated source truth. The editor document path inventory and active validation reports
  now list this under `document_paths.authored_overrides` while generated sidecars, generated Lua/script IR, material
  caches, and compatibility artifacts remain in separate generated or derived groups. The headless clean gate also
  requires zero missing document paths for the active DAT level report.
- [ ] Regenerating sidecars from unchanged `source/*` produces byte-stable YAML or intentionally normalized YAML.
  Partial active-slice coverage now exists for generated MM9 event sidecars: `generate_mm9_events.py
  --check-idempotent` rebuilds the in-memory `*.events.yml`, generated Lua, and `*.script_ir.yml` outputs and compares
  them byte-for-byte against existing files without writing. This has been verified for `thjorgard` and
  `thjorgardcity` in both `assets_dev/worlds/mm9` and `assets_editor_dev/worlds/mm9`. This item remains open until the
  same idempotency/losslessness check covers DAT world, raw object, material alias, model/actor, and other generated
  MM9 sidecars.

## Implementation Checklist

### Phase 1: Native Document Skeleton

- [x] Add `Mm9Dat` document kind and load dispatch from `kind: mm9_level`.
- [x] Load `*.level.yml` and resolve all declared sidecar paths.
- [x] Load source DAT path and verify hash from level YAML.
- [x] Load `*.dat_world.yml`, `*.material_aliases.yml`, `*.raw_objects.yml`, and `*.events.yml`.
- [x] Load `source/manifest.yml` into typed read-only document state and expose source-family diagnostics.
- [x] Add read-only document state for source assets and writable state for generated/authored OpenYAMM files.
  Implemented as `EditorMm9DocumentPathStatus` inventory exposed by the MM9 level inspector. Validation rejects
  read-only source paths outside `source/*` and writable/generated paths inside `source/*`.
- [x] Add editor UI routing so MM9 DAT documents open in the native DAT viewport path.
  Implemented as the MM9 DAT branch of the shared editor scene viewport for now: the document opens as
  `EditorDocument::Kind::Mm9Dat`, uses the source DAT render mesh, and does not use compatibility ODM/BLV geometry as
  the world source. A later class split to `EditorDatLevelViewport` remains optional and should only happen if it
  reduces coupling.

Tests:

- [x] Headless: `kind: mm9_level` dispatches to MM9 DAT document, not outdoor/indoor document.
  `--headless-verify-document-dispatch` checks `thjorgard.level.yml` and `thjorgardcity.level.yml` through
  `EditorDocument::loadMapPhysicalPath` and requires loaded MM9 sidecars, loaded source DAT world data, and a nonempty
  native DAT render mesh.
- [x] Headless: regular ODM/BLV map paths still dispatch exactly as before.
  The same verifier checks representative MM8, MM7, and MM6 ODM files as `Outdoor`, and representative MM8, MM7, and
  MM6 BLV files as `Indoor`, while asserting that those legacy documents do not load MM9 sidecars.
- [x] Unit: missing source DAT, hash mismatch, missing sidecar, and wrong document kind produce clear diagnostics.
- [x] Unit: MM9 level YAML parsing, wrong-kind rejection, missing required source/sidecar diagnostics, and generated
  Thjorgard entrypoint validation.
- [x] Unit: required sidecars are opened and rejected when their `kind` does not match the expected MM9 sidecar kind.
- [x] Unit: MM9 DAT world, material aliases, raw objects, and event sidecars load into typed editor-side state.
- [x] Unit: MM9 raw objects project into source-preserving light, sound, and spawn layers without changing legacy
  ODM/BLV spawn data.
- [x] Unit: MM9 raw objects project into source-preserving object transform/bounds/trigger-volume evidence without
  changing legacy ODM/BLV object or spawn data.
- [x] Unit: source manifest parsing, required-family validation, count drift diagnostics, and mirrored source-tree
  validation.
- [x] Unit: MM9 document path inventory classifies source DAT and source manifest as read-only, sidecars/scripts/caches
  as generated, compatibility files as derived, and rejects generated paths under `source/*`.
  The same focused unit now covers declared `source_asset_aliases` files as authored overrides, with explicit assertions
  that they are not classified as generated files.
- [x] Unit: cheap parser invariant coverage confirms generated `*.dat_world.yml` files preserve source model indexes,
  texture indexes, totals, portal bounds, and leaf-reference summaries accepted by the editor validator. This is
  regression coverage, not a requirement to run slow editor validation across all maps during the active two-map slice.
- [x] Headless editor: open `thjorgard.level.yml`, report document kind `Mm9Dat`, assert the MM9 document path role
  inventory is populated, and assert all generic save/build entrypoints reject source mutation and ODM/BLV-style build
  actions.
  The active DAT-level verifier also now requires read-only source paths, generated paths, authored paths, and
  compatibility-derived paths to be present. If the level declares `sidecars.source_asset_aliases`, it must appear as an
  authored override, keeping active override data visibly separate from generated source-derived outputs.
- [x] Headless editor: regression coverage exists for MM9 DAT level path roles and MM9-specific save/build rejection.
  The current active slice runs the focused `thjorgard` and `thjorgardcity` checks.
- [x] Headless editor: `thjorgard.level.yml` and `thjorgardcity.level.yml` dispatch through the physical map-path loader
  to `EditorDocument::Kind::Mm9Dat`; the focused verifier rejects any outdoor/indoor document kind for these native DAT
  entrypoints.
- [x] Headless/editor regression: regular MM6-MM8 ODM/BLV map paths still dispatch through the existing outdoor/indoor
  document paths after the native MM9 level branch.
  `--headless-verify-document-dispatch` provides the non-SDL proof for document dispatch, independent of viewport
  rendering. SDL/bgfx render smoke remains separate coverage.

### Phase 2: DAT World Rendering And Picking

- [x] Build render mesh buffers directly from DAT world model polygons.
  Source DAT polygons are now parsed into a reusable `Mm9DatRenderMesh` with OpenYAMM-space vertices, UVs, source
  model/polygon/surface/texture ids, source texture names, DAT flags, and degenerate/skipped polygon counters. GPU/editor
  viewport buffers are wired through the MM9 DAT viewport path. The native DAT viewport path now builds textured
  geometry from source DTX files through shared `game/mm9` DTX decoding rather than requiring generated `.bitmaps/*`
  preview caches. Visible/helper filtering and source-index-preserving interactive picking are covered separately below;
  object-driven model/actor/billboard visual completeness remains a separate open item.
- [x] Preserve source model/polygon/surface ids in editor pick payloads.
  `pickMm9DatRenderMesh` now performs native mesh ray picking and returns triangle index, source model/polygon/surface/
  texture ids, source model/texture names, hit distance, barycentric coordinates, and hit position. It is shared under
  `game/mm9`; the editor viewport now converts mouse rays to DAT pick rays and selects `Mm9DatPolygon` by render
  triangle index for source-preserving inspection.
- [ ] Apply source-DTX-derived materials through material aliases.
  Native DAT render triangles are now assigned to map-local material aliases with `assignMm9DatRenderMeshMaterials`,
  preserving triangle/source ids and carrying alias, source DTX path, and decoded preview cache path when available. The
  native DAT world-geometry viewport path now decodes and uploads source DTX pixels directly. Deterministic preview-cache
  regeneration remains a diagnostic/editor-cache concern, not the authoritative native DAT render source. This item is
  still open until the same source-DTX material path is used for model instances, actors, props, pickups, and billboard
  skins. DAT material rows that reference LithTech `*.spr` files now resolve the source SPR and its listed
  `SpriteTextures/**/*.dtx` frame textures so animated water/perception-style surface materials are source-backed
  instead of reported as missing DTX aliases; the viewport can use the first resolved frame DTX as a static preview
  source until animated material playback is implemented. DTX material references also use a conservative
  unique-basename fallback after exact path lookup fails, which resolves known source layout aliases such as
  `TEXTURES\LevelTextures\Invisible.dtx` to the single mirrored source file
  `source/textures/LEVELTEXTURES/MISC/INVISIBLE.dtx` without guessing when duplicate basenames exist.
- [ ] Add filters for visual, invisible, sky, helper, physics, visibility, and portal geometry.
  `classifyMm9DatRenderMeshFilters` now produces source-index-preserving triangle filter entries and aggregate counts
  from DAT surface flags plus generated DAT world-model roles. It covers visual, invisible, sky, water, helper,
  physics BSP, visibility BSP, trigger/volume, terrain, movable, and portal overlay counts. The interactive viewport
  now consumes the same filter entries for DAT/default, sky, PhysicsBSP, water/effect, VisBSP, invisible, helper, and
  trigger/volume world subset modes, and the selected polygon inspector exposes the exact classifier entry used for each
  source triangle. Matching headless render-smoke modes are wired for those same subset names, and user portals are
  exposed as a separate overlay toggle. This item remains open until leaf filters are exposed with their own overlay UI
  and inspector counts.
  Non-rendering filter verification now exists through `--headless-verify-mm9-dat-filters`: `thjorgard` reports
  total/default/sky/physics/water/visibility/invisible/helper/trigger counts of
  37,772/33,920/48/10,850/99/644/2,926/12,836/1,195, and `thjorgardcity` reports
  76,414/57,109/48/48,297/48/15,147/6,066/67,200/1,222, with 35 portal overlays preserved for the city map as 840
  generated line vertices. The same verifier now reports source DAT collision flag counts:
  `thjorgard` has `dat_solid=36419`, `dat_visibility_blocker=6`, `dat_not_a_step=7500`, and
  `thjorgardcity` has `dat_solid=71223`, `dat_portal_surface=295`.
- [x] Add basic camera framing from DAT world bounds.
  `computeMm9DatRenderBounds` and `frameMm9DatRenderMeshCamera` now produce native OpenYAMM-space bounds and a
  deterministic editor/runtime camera frame from parsed DAT render mesh geometry. Active verification is focused on
  `thjorgard` and `thjorgardcity`; previous all-map camera-frame coverage remains regression context.

Tests:

- [x] Unit: DAT polygon-to-render-mesh conversion preserves source ids.
- [x] Unit: DAT render mesh ray picking returns a source-index-preserving pick payload.
- [x] Unit: material assignment uses map-local aliases and rejects unresolved aliases.
- [x] Headless editor: MM9 DAT documents attach a nonempty native render mesh and compare parsed source model/polygon
  totals against generated sidecars for focused active targets `thjorgard.level.yml` and
  `thjorgardcity.level.yml`; all-map verification is reserved for milestone checks because it is slow.
- [x] Headless editor: every native DAT render triangle has a unique material alias assignment.
  Focused active-slice checks cover `thjorgard` and `thjorgardcity`. Previous all-map verifier counters remain
  regression context; full preview-cache completeness is still tracked by the DTX preview/cache items.
- [x] Headless editor: every native DAT render triangle has a display-filter classification.
  Focused active-slice checks cover `thjorgard` and `thjorgardcity`. Previous all-map display-filter counters remain
  regression context.
- [x] Headless editor: render one frame for `thjorgard` and one frame for `thjorgardcity` with nonzero submitted
  geometry.
  `openyamm-editor --world mm9 --headless-render-mm9-dat-level <map>.level.yml` opens the MM9 DAT level, drives the
  normal `EditorOutdoorViewport` renderer directly, presents the offscreen viewport texture to the backbuffer, requests
  a bgfx screenshot, and fails unless the frame reports nonzero source-DTX DAT world submissions, nonzero model-instance
  submissions, and nonblank screenshot pixels with color variance. Verified under an OpenGL bgfx context for the active
  slice: `thjorgard` submitted 101,760 DAT-world vertices across 55 textured DAT batches plus 183,870 model-instance
  vertices across 328 textured model-instance batches, with 2,287,250 visible screenshot pixels and 51 coarse color
  buckets; `thjorgardcity` submitted 171,327 DAT-world vertices across 132 textured DAT batches plus 500,934
  model-instance vertices across 794 textured model-instance batches, with 2,287,634 visible screenshot pixels and 61
  coarse color buckets. Pixel-backed render smokes require a real bgfx backend; the smoke now fails explicitly when the
  SDL dummy path selects bgfx `Noop`, because `Noop` cannot prove viewport submissions or screenshots. Current focused
  model-only smoke evidence was verified with `OPENYAMM_BGFX_RENDERER=opengl SDL_VIDEODRIVER=x11`.
- [x] Headless editor: active-slice viewport preflight reports nonzero renderable native DAT geometry with source-DTX
  material inputs and nonzero drawable model-instance geometry, complementing the bgfx screenshot/readback smoke.
  Current focused counts are: `thjorgard.level.yml` has 31,418 renderable native DAT triangles, 8,984 renderable
  PhysicsBSP triangles, 31,418 source-DTX textured native triangles, 0 placeholder material triangles,
  0 unresolved material triangles, and 232 drawable model-instance geometries. `thjorgardcity.level.yml` has 51,397
  renderable native DAT triangles, 47,895 renderable PhysicsBSP triangles, 51,397 source-DTX textured native triangles,
  0 placeholder material triangles, 0 unresolved material triangles, and 790 drawable model-instance
  geometries. This is render-input coverage, not a substitute for the open one-frame screenshot/readback test above.
- [x] Headless editor: visual smoke for the `test_img/923.png` class of gaps proves the rendered frame contains visible
  model-instance pixels, source sprite-water/effect material pixels instead of placeholder checker output, and
  wall/building/physics-BSP surfaces under the intended default display filters.
  The active render smoke now proves a nonblank screenshot with model-instance submissions and source-DTX DAT world
  submissions for both focused maps, and category-specific smokes now isolate the previously missing classes.
  `--headless-render-mm9-dat-models` hides DAT world geometry and requires zero DAT-world vertices, nonzero
  model-instance submissions, and nonblank screenshot readback: `thjorgard` reports 183,870 model-instance vertices,
  328 textured model-instance submissions, 0 placeholder/missing model-instance submissions, 0 DAT-world vertices,
  2,303,924 visible screenshot pixels, and 118 color buckets; `thjorgardcity` reports 500,934 model-instance vertices,
  794 textured model-instance submissions, 0 placeholder/missing model-instance submissions, 0 DAT-world vertices,
  2,303,942 visible screenshot pixels, and 388 color buckets.
  `--headless-render-mm9-dat-water` filters to DAT water-role world geometry with model instances hidden:
  `thjorgard` reports 297 DAT-world vertices, 0 model-instance vertices, 2,303,955 visible screenshot pixels, and 42
  color buckets; `thjorgardcity` reports 144 DAT-world vertices, 0 model-instance vertices, 2,304,000 visible
  screenshot pixels, and 41 color buckets. This water smoke currently proves the role can be isolated and rendered; it
  is regression context from before the visible-water/water-volume split, not final pixel proof for the current water
  subsets. Current source-backed validation now proves `Ocean`/`Ocean4.spr` remains a visible water surface while
  `BlueWater*` records backed by `Invisible.dtx` or `WaterMarker.dtx` are hidden by default and remain available through
  the water-volume/helper filter: `thjorgard` reports `visible_water=13` and `water_volume=86`; `thjorgardcity` reports
  `visible_water=0` and `water_volume=48`.
  `--headless-render-mm9-dat-physics` filters to PhysicsBSP world geometry
  with model instances hidden: `thjorgard` reports 32,550 DAT-world vertices, 0 model-instance vertices, 2,287,250
  visible screenshot pixels, and 18 color buckets; `thjorgardcity` reports 144,891 DAT-world vertices, 0
  model-instance vertices, 2,287,634 visible screenshot pixels, and 61 color buckets.
  `--headless-render-mm9-dat-visibility` filters to visibility-helper world geometry with model instances hidden:
  `thjorgard` reports 1,932 DAT-world vertices, 0 model-instance vertices, 2,287,250 visible screenshot pixels, and 17
  color buckets; `thjorgardcity` reports 45,441 DAT-world vertices, 0 model-instance vertices, 2,287,634 visible
  screenshot pixels, and 61 color buckets. These category smokes are regression coverage for the `test_img/923.png`
  class of missing geometry: they prove the active viewport can isolate and render model instances, water/effect
  surfaces, physics hull surfaces, and visibility-helper surfaces from source-derived MM9 data. They do not close the
  remaining actor/monster billboard, mechanism preview, or interactive inspector tasks.
- [x] Headless editor: synthetic pick returns the expected DAT source model/polygon/surface ids.
  Focused active-slice checks cover `thjorgard` and `thjorgardcity`. Previous all-map synthetic-pick coverage remains
  regression context.

### Phase 3: DTX Resolver And Texture Inspector

- [x] Implement source DTX discovery under `source/textures/`, `source/skins/`, and sprite texture folders.
- [x] Implement deterministic case-insensitive path/name resolution with ambiguity detection.
- [x] Decode DTX preview images and mip metadata through shared runtime/editor code.
  `game/mm9/Mm9DtxTexture` now provides shared DTX v2 header parsing and base-level pixel decode for raw BGRA, DXT1,
  DXT3, and DXT5 textures, selectable mip-level decode to BGRA, plus mip payload enumeration and LithTech section
  metadata parsing. The material texture inspector renders decoded source mip images inline and now shows
  source-backed SPR material provenance plus frame-texture resolution counts for sprite-driven DAT surface materials.
  Model-instance skins now use the same source-DTX loader path rather than generated PNG previews, resolving
  `skins/...`/`textures/...` references against the immutable MM9 `source/` tree with case-insensitive physical lookup.
  Current active verifier evidence: `thjorgard.level.yml` reports `dtx_headers=59`, `dtx_mip_payloads=236`,
  `dtx_decoded_preview_mips=236`, `dtx_command_strings=12`, 55 deterministic decoded-cache checks, and 325 decoded
  model-instance skin textures; `thjorgardcity.level.yml` reports `dtx_headers=135`, `dtx_mip_payloads=539`,
  `dtx_decoded_preview_mips=539`, `dtx_command_strings=5`, 132 deterministic decoded-cache checks, and 794 decoded
  model-instance skin textures.
- [ ] Upload DTX-decoded pixels directly to editor renderer texture handles for DAT world geometry and model/actor/prop
  skins.
  Implemented for native DAT world geometry and the editor model-instance preview path. Model instance sidecars now
  prefer `runtime_texture` DTX bindings over generated preview PNGs, and source actor skin refs such as
  `skins/peasantm6a.dtx` are decoded through the shared MM9 DTX loader instead of requiring `skins/*.png` previews.
  Full actor/monster variant inspection, billboard presentation, and blocking model/skin diagnostics remain open.
- [x] Keep generated `.bitmaps/*` as optional debug/cache output only. The editor must validate and render correctly
  when source DTX exists even if generated bitmap caches are absent.
  Native DAT world geometry no longer requires `.bitmaps/*` in the viewport. Inspector cache freshness and generated
  preview diagnostics still reference those files, but `generated_caches` are now optional asset-graph dependencies,
  missing cache document paths are warning-level diagnostics instead of clean-blocking errors, and the headless reports
  split `document_paths.missing_required` from total missing paths. Current active-slice reports still have all caches
  present, but the clean gate no longer depends on them. Native DAT world geometry and model-instance skins upload
  decoded source-DTX pixels directly to bgfx texture handles.
- [x] Populate texture inspector from actual DTX headers, not only from generated aliases.
- [x] Add cache freshness checks against source DTX hashes.

Tests:

- [x] Unit: cheap parser/material invariant coverage confirms generated DAT texture references resolve to source DTX
  files. This remains regression coverage; active editor acceptance is the two-map slice.
- [x] Unit: ambiguous case-folded DTX names are rejected with both candidate paths.
- [x] Unit: DTX header parser preserves flags, surface flags, command string, dimensions, detail fields, BPP, texture
  group, and mip count for material alias validation.
- [x] Unit: shared DTX decoder preserves raw BGRA32 pixels and expands DXT1 blocks to BGRA pixels.
- [x] Unit: shared DTX layout parser preserves mip payload offsets/sizes/dimensions and DTX section metadata.
- [x] Unit: shared DTX decoder can decode a selected mip level with source dimensions and mip identity preserved.
- [x] Headless editor: texture inspector for `thjorgard` reports zero unresolved and displays at least one decoded
  preview.
- [x] Headless editor: focused source-DTX native DAT material path passes for `thjorgard.level.yml` and
  `thjorgardcity.level.yml`; active-slice validation reports now show `material_textures.invalid_or_unresolved: []`
  for both maps after resolving SPR-backed material aliases through source SPR plus frame DTX files, with the first
  resolved frame available as the static editor preview source.

### Phase 4: Object, Event, And Script Inspection

- [x] Load and cross-link raw objects, event YAML, generated Lua, and source SCR/INC files.
- [x] Add object inspector with raw/decoded property display.
- [x] Add event/script inspector with binding provenance.
- [x] Add jump navigation between object, event, script, target world model, and source asset.
  The active MM9 inspectors link raw objects, generated event objects, mechanisms, and generated world-model targets
  through editor selection buttons. Script/source-asset jumps use the read-only open-path actions from the same
  inspector sections.
- [x] Make unresolved object/script references blocking validation errors.

Tests:

- [x] Unit: cheap raw-object invariant coverage confirms generated `*.raw_objects.yml` files preserve object/property
  source indexes, raw lengths, hex payload integrity, and object data-length boundaries. This remains regression
  coverage; active editor acceptance is the two-map slice.
- [x] Unit: raw object source file references resolve model, skin-list, script, voice, and sprite properties against
  source-family indexes and report unresolved required references deterministically.
  Coverage includes embedded multi-asset `ScriptParams` strings with numeric arguments, unique basename fallback, and
  ambiguous basename fallback diagnostics.
- [x] Unit: event bindings reference valid source object ids, object names, world model ids, or explicit external
  targets.
- [x] Unit: generated Lua paths in level YAML resolve and generated event sidecars cannot drift to an authored
  override path.
- [x] Unit: cheap event invariant coverage confirms generated `*.events.yml` files cross-link to raw objects, generated
  Lua, source SCR/INC scripts, bindings, mechanisms, and DAT world targets accepted by the editor validator. This
  remains regression coverage; active editor acceptance is the two-map slice.
- [x] Headless editor: open `thjorgard`, select a mechanism/event object, and resolve its event/script provenance.
  `--headless-verify-mm9-event-provenance <level.yml> <source_object_index>` now opens the map through
  `EditorSession`, selects the generated `Mm9EventObject`, selects `Mm9Mechanism` when present, checks raw-object
  provenance, validates generated Lua/script-IR paths, verifies source SCR existence through the development-root
  source fallback, and checks resolved mechanism DAT world-model target identity. The editor-dev active slice
  `thjorgard.events.yml` and `thjorgardcity.events.yml` sidecars were regenerated so they now preserve
  `generated.script_ir` alongside the generated Lua path. Verified on `thjorgard.level.yml` with source object 105
  `BlueWater0` as a mechanism/DAT-world-model provenance case and source object 117 `HalfOrcCaptain0` as a scripted
  event-object/source-SCR provenance case. The full `cmake --build ...` path currently trips an unrelated CMake
  regenerate failure in `tools/CMakeLists.txt`, but `openyamm-editor/fast` and `openyamm_unit_tests/fast` built the
  touched editor/test targets for this check.
- [x] Headless editor: active-slice maps have map-wide event sidecar validation.
  `--headless-verify-mm9-events thjorgard.level.yml` and
  `--headless-verify-mm9-events thjorgardcity.level.yml` validate the same loaded DAT document path, generated
  `*.events.yml`, generated Lua, generated script IR, source SCR paths, raw-object provenance, bindings, mechanisms,
  and DAT world-model target indexes without opening every local MM9 map. The command intentionally reports unresolved
  target counts as diagnostics so source-evidence questions stay visible.

### Phase 5: Mechanisms

- [x] List generated mechanisms from event sidecars with MM9 source object identity and source evidence.
- [x] Detect movable world models directly from DAT flags and object/script evidence.
  The active-slice DAT-level verifier now validates mechanism targets against DAT `roles.movable` and emits blocking
  diagnostics for missing target source models plus warnings for target models lacking the movable role. Current focused
  reports have `mechanism_world_model_targets_without_movable_role=0` and
  `mechanism_world_model_targets_missing_model=0`.
- [x] Bind mechanisms by DAT source world model/polygon groups and object/event targets.
  Mechanism targets are generated from raw-object/source-script evidence into `*.events.yml` bindings and now carry both
  the DAT source world-model target and its source polygon-group evidence. The focused reports prove all active
  mechanism world-model targets are grouped consistently: `thjorgard` has 124/124 targets with source polygon groups
  and 0 mismatches; `thjorgardcity` has 405/405 targets with source polygon groups and 0 mismatches.
- [x] Add mechanism preview transforms in editor.
  The editor mechanism inspector exposes progress/state controls for previewable MM9 DAT mechanisms, and the viewport
  applies those controls by generating a preview render mesh from the original DAT render mesh plus selected mechanism
  transforms. The source DAT/render mesh remains immutable; only transient editor geometry buffers are rebuilt.
- [ ] Add mechanism diagnostics for missing movement parameters, missing trigger bindings, missing target world models,
  missing sounds, and ambiguous source evidence.
  Partial coverage exists in the active-slice validation reports for missing mechanism target bindings and incomplete
  authored movement parameter sets. The report now emits `incomplete_linear_motion`, `incomplete_rotation_motion`, and
  per-mechanism `incomplete_motion` entries, plus normalized `mm9_mechanism_motion_resolver` warnings when any required
  motion field is absent. Current focused evidence is clean for authored motion completeness:
  `thjorgard` and `thjorgardcity` both report `mechanism_incomplete_linear_motion=0` and
  `mechanism_incomplete_rotation_motion=0`, and those counters are now active-gate failures if nonzero. The reports
  also count `mechanism_trigger_outputs` and
  `mechanism_unresolved_trigger_outputs`; current focused evidence is `thjorgard` 6/0 and `thjorgardcity` 0/0. The
  reports now also count typed sound evidence (`mechanism_sound_slots=1064`,
  `mechanism_authored_sound_references=304`, `mechanism_empty_sound_references=760`) and previewability
  (`mechanism_previewable_mechanisms=83`, `mechanism_inert_mechanisms=189`,
  `mechanism_inert_preview_entries=189`, `mechanism_without_preview_motion=189`,
  `mechanism_without_preview_target=7`). Each inert preview entry is listed in the per-map report with source object
  index/class/name, mechanism id, reason, binding presence, required-target status, preview-motion availability, and
  preview world-model target availability; the clean gate now requires the detailed inert-entry count to match the
  aggregate inert mechanism count. The active gate now requires unresolved trigger outputs to stay at zero and requires
  authored plus empty sound references to equal total sound slots, so sound-sidecar drift cannot pass silently. The
  reports also count typed activation/timing state preservation:
  `mechanism_activation_start_open_fields=152`, `mechanism_activation_locked_fields=152`,
  `mechanism_activation_push_open_fields=152`, `mechanism_activation_touch_to_open_fields=152`,
  `mechanism_activation_lock_on_close_fields=0`, `mechanism_activation_reopen_on_contact_fields=152`,
  `mechanism_rotation_open_away_fields=80`, `mechanism_timing_move_delay_fields=152`, and
  `mechanism_timing_open_wait_fields=152`; the active gate requires the present activation/timing counts to stay
  internally consistent. The normalized diagnostics section includes an
  `mm9_mechanism_preview_state_resolver` info entry for the inert-preview inventory. This is still not complete because
  missing trigger bindings, ambiguous evidence, and complete script-callback semantics are not all checked as blocking
  diagnostics. The reports also expose typed script-side callback/edge preservation counters, currently
  `script_registered_triggers=44` and `script_trigger_edges=29` for `thjorgard`, and
  `script_registered_triggers=20` and `script_trigger_edges=1` for `thjorgardcity`.
- [ ] Keep compatibility ODM/BLV face lists secondary and derived.

Tests:

- [x] Unit: mechanism bindings never use ODM/BLV face ids as primary identity.
- [x] Unit: generated MM9 event bindings preserve nearest movable DAT world-model candidate evidence from
  `*.events.yml`.
- [x] Unit: generated MM9 event bindings preserve DAT source polygon-group evidence for world-model targets.
  `Mm9EventsYmlTests` loads `source_polygon_group` fields through `Mm9EventsYmlLoader`, and
  `tests/mm9_events_generator_tests.py` verifies regenerated shared-rotation bindings retain source model, polygon
  count, surface count, bounds, and movable role evidence from `*.dat_world.yml`.
- [x] Unit: generated MM9 mechanism trigger outputs are preserved by the event sidecar loader.
  `Mm9EventsYmlTests` loads generated `trigger_outputs` with phase, slot, target name, message name, and resolution.
- [x] Unit: generated MM9 script trigger callbacks and trigger edges are preserved by the event sidecar loader.
  `Mm9EventsYmlTests` loads generated `registered_triggers` and `trigger_edges` with source lines, callback/message
  expressions, and raw argument text.
- [x] Unit: generated MM9 script movement and unknown command rows are preserved by the event sidecar loader.
  `Mm9EventsYmlTests` loads generated `movement_commands` and `unknown_commands` with source line, command name, and raw
  argument text, and also preserves the generated per-script `command_count`.
- [x] Unit: generated MM9 unresolved event rows are preserved by the event sidecar loader.
  `Mm9EventsYmlTests` loads unresolved event kind, source object identity, severity, and nearest movable world-model
  candidate evidence from `*.events.yml`.
- [x] Unit: moving-world-model transform preview preserves original source geometry and produces transformed preview
  geometry only.
  `MM9 DAT mechanism preview transforms target model without mutating source mesh` verifies that only the selected DAT
  source model is transformed, source model/polygon ids are preserved, unrelated triangles are unchanged, and the input
  mesh is not mutated.
- [x] Headless editor: open maps with known doors/mechanisms and validate zero unresolved required mechanism targets.
  Current evidence: `--headless-verify-mm9-dat-level thjorgard.level.yml` and
  `--headless-verify-mm9-dat-level thjorgardcity.level.yml` both pass with
  `mechanism_unresolved_required_targets=0`. Optional unresolved `ScriptObject` targets remain visible in the event
  reports and are not treated as required mechanism blockers.
- [x] Headless editor: mechanism movement parameter diagnostics are represented in validation reports.
  `--headless-verify-mm9-dat-level thjorgard.level.yml` and
  `--headless-verify-mm9-dat-level thjorgardcity.level.yml` now write `incomplete_motion` entries when generated
  mechanisms have partial linear or rotation movement data. The active two-map summary currently reports
  `mechanism_incomplete_linear_motion=0` and `mechanism_incomplete_rotation_motion=0`.
- [x] Headless editor: mechanism world-model targets are checked against DAT movable roles.
  `--headless-verify-mm9-dat-level thjorgard.level.yml` reports 124/124 world-model targets with movable roles,
  0 targets without the movable role, and 0 missing target models. `thjorgardcity.level.yml` reports 405/405
  world-model targets with movable roles, 0 targets without the movable role, and 0 missing target models.
- [x] Headless editor: mechanism world-model targets include matching DAT source polygon groups.
  `--headless-verify-mm9-dat-level thjorgard.level.yml` reports 124/124 world-model targets with source polygon
  groups, 0 missing groups, and 0 mismatches. `thjorgardcity.level.yml` reports 405/405 world-model targets with source
  polygon groups, 0 missing groups, and 0 mismatches. The active two-map event sidecars also pass
  `generate_mm9_events.py --check-idempotent` after regeneration.
- [x] Headless editor: mechanism preview changes selected world model bounds while source DAT hash remains unchanged.
  `--headless-verify-mm9-dat-level thjorgard.level.yml` reports 12 mechanism preview candidates, 12 target bounds
  changes, and 470 transformed preview triangles while preserving referenced source-file hashes.
  `--headless-verify-mm9-dat-level thjorgardcity.level.yml` reports 153 candidates, 153 target bounds changes, and
  1,884 transformed preview triangles while preserving referenced source-file hashes.

### Phase 6: Portals, Visibility, And Collision Inspection

- [ ] Visualize DAT leaves, nodes, user portals, physics BSPs, visibility BSPs, and blocker surfaces.
  Partial coverage: MM9 DAT user portals now render as optional viewport line-box overlays derived from sidecar
  center/dimensions. PhysicsBSP, VisBSP, invisible, helper, and trigger/volume geometry can be viewed through DAT
  subset filters. Leaves and nodes are still metadata/inspector-only until their spatial graph semantics are decoded
  enough for a source-backed overlay.
- [x] Add per-surface participation flags for render, physics, visibility, picking, and scripts.
  Selected DAT polygons report render/pick participation and physics, visibility, trigger/volume, helper, movable,
  sky, water, and terrain classifier bits in the inspector. The active-slice DAT-level verifier also reports aggregate
  filter counts for the same classifier categories.
- [x] Add collision material display from DAT surface flags plus DTX user flags.
  Implemented in the selected DAT polygon inspector with named LithTech DAT surface flags, named DTX user/material
  flags, and derived booleans for solid, physics blocker, visibility blocker, not-a-step, portal, invisible, and sky
  participation. This is display/inspection coverage; runtime collision response remains governed by the separate
  MM9 DAT physics checklist.
- [x] Add validation for invalid leaf, portal, node, surface, point, and polygon references.
  The DAT world sidecar validator now rejects invalid leaf polygon references, user portal source-model/range references,
  surface texture references, polygon surface/plane/vertex point references, node polygon references, root node
  references, source model indexes, texture indexes, and aggregate source counts. The active DAT-level verifier gates on
  the same validation and writes `dat_world_reference_validation` into each active-slice asset report. Current focused
  evidence: `thjorgard.level.yml` and `thjorgardcity.level.yml` both report `dat_world_reference_issues=0`,
  `dat_world_invalid_leaf_references=0`, `dat_world_invalid_surface_texture_refs=0`,
  `dat_world_invalid_poly_surface_refs=0`, `dat_world_invalid_poly_plane_refs=0`,
  `dat_world_invalid_poly_vertex_refs=0`, `dat_world_invalid_node_poly_refs=0`, and
  `dat_world_invalid_root_node_refs=0`.

Tests:

- [x] Unit: cheap DAT parser invariant coverage confirms decoded leaf polygon references are valid. This remains
  regression coverage; active editor acceptance is the two-map slice.
- [x] Unit: helper world models are classified consistently with `*.dat_world.yml`.
- [x] Headless editor: portalized city map opens with nonzero leaves and portals visible in inspector.
- [x] Headless editor: physics/visibility filter toggles change overlay counts without changing source geometry.
  `--headless-render-mm9-dat-physics` and `--headless-render-mm9-dat-visibility` run against the same loaded DAT
  document as the normal render smoke, hide model-instance rendering, and require nonzero submitted DAT vertices plus
  nonblank screenshot readback. The focused validators still pass afterward with unchanged source counts and hashes for
  `thjorgard.level.yml` and `thjorgardcity.level.yml`. This is headless viewport coverage; the interactive overlay UI
  and inspector toggles remain tracked by the unchecked Phase 6 visualization tasks above.

### Phase 7: Model, Actor, Monster, And Billboard Resolution

- [ ] Implement official MM9 model/actor/monster resolver from source DAT objects, source data/RUDE tables, source model
  files, skins, sprites, sounds, and generated registries.
  Converted OpenYAMM model and skin cache layout should mirror original MM9 resource layout, not invent an `actors/`
  folder. Actor ABCs that are top-level under `MODELS/MODELS/*.abc` should convert to
  `assets_dev/worlds/mm9/models/<name>.glb` plus `<name>.model.yml`; source subfolders such as `MODELPROPS`,
  `WEAPONS`, `PROPS/PLANTSANDTREES`, `PLAYER`, `SPELLS`, `PROJECTILES`, `GIBS`, and `PICKUPITEMS` should mirror under
  lowercase `models/` subfolders. DTX skins should mirror `SKINS/SKINS` under `assets_dev/worlds/mm9/skins/`.
  Actor/monster table resolution must bind the official variant skin/texture to the base GLB/model animation holder,
  while keeping original ABC/DTX source identity and generated presentation caches separate.
- [ ] Resolve static object models, pickup models, projectile models, actor models, monster variants, and optional
  billboard presentations through the same dependency graph.
  Native MM9 DAT documents now keep the object-derived `model_instances` from the generated scene sidecar in document
  state, so the existing editor model-instance renderer and selection markers can see the same source object indexes as
  the DAT/event inspectors. The scene sidecar remains generated presentation data, not geometry truth; missing
  `model_asset` fields are allowed so incomplete generated presentation caches do not drop otherwise lossless source
  object records. The renderer now accepts source DTX skins and model sidecar `runtime_texture` DTX paths directly;
  generated PNG skin previews are optional fallback/cache data. The focused DAT validator now derives generated
  presentation-asset candidates from source model references and scoped source-asset aliases, so missing sidecar
  `model_asset` fields do not hide whether an official object can resolve to a concrete generated model asset. The
  native DAT viewport now consumes the same raw-object asset reference statuses for model and skin aliases, so the
  active-slice Thjorgard `Barrel02` source references resolve through the authored source-asset alias to the generated
  `Barrel` model/skin instead of drawing a placeholder.
- [ ] Add actor/monster variant inspector.
  Active selector-level inspection now exists for MM9 DAT model instances and scripted objects: the inspector branch
  applies to `EditorDocument::Kind::Mm9Dat`, not just legacy outdoor scene documents, and the MM9 actor-source resolver
  carries the inferred variant id through to the UI. The selected-object inspector now has an `Actor/Monster Variant`
  section with official actor-row evidence, actor number, monster name, type picture, base name, resolved model, resolved
  skin, generated variant asset path, source object index, and jump actions to the raw object, generated event object, and
  bound mechanism when those links exist. The same section now exposes parsed official gameplay/combat/movement row
  fields including level, HP, AC, EXP, speed, treasure type/level, quest, fly/move flags, walk/run/fly/lunge velocity,
  attack reach/range, recovery, target preference, bonus, alert radius, accuracy, foot sound/radius, resolved foot-sound
  source count and paths, transparency, head-turn, special, scale, evade chance, strafe-attack percent, monster flag,
  hostility group, script, and voice radius. A collapsed `Variant Source Assets` table also lists the source model and
  skin, sound, and voice references that produced the selected variant. The inspector also has a collapsed
  `Billboard Presentation` section backed by the generated scripted-billboard visual set; it shows whether the selected
  object has generated billboard metadata or is using a generated 3D model asset, plus visual id, source model/GLB/skins,
  variant/model ids, angle/clip/frame counts, collision metadata, used-by count, and first idle-frame texture/path/angle
  when a billboard visual resolves. Missing variant diagnostics are now visible directly on the selected object as
  candidate, severity, resolver, and message rows for unresolved variants, missing official actor-row evidence, missing
  gameplay identity, and unresolved official foot-sound aliases. The same section now exposes source-backed
  faction/hostility semantics: hostility group source, generated-script match/source, source script include paths,
  hostility-related include, registered-trigger, and trigger-edge counts, and an explicit note that the MM9 actor tables
  do not carry separate team/alignment columns.
- [ ] Report missing model, skin, animation, sprite, sound, voice, or gameplay identity as blocking errors.
  Raw object asset inspection now counts unresolved source file references but does not block map open yet, because 976
  historical official references across the full local map set require explicit alias/remap semantics or source-inventory
  decisions before they can be classified as true data loss. The current active slice has zero unresolved required
  raw-object asset references after applying scoped source-asset aliases. The active-slice validation report now also
  separates official actor-variant resolution from generated billboard presentation caches: `thjorgard` reports 53
  actor variant candidates, 53 resolved, 53 gameplay identity rows, and 0 unresolved; `thjorgardcity` reports 60
  candidates, 60 resolved, 60 gameplay identity rows, and 0 unresolved. Active actor foot-sound references are now
  clean-blocking too: `thjorgard` resolves 43/43 `FootSound` fields, `thjorgardcity` resolves 60/60, and
  `actor_variant_unresolved_foot_sounds=0` in the active summary. Object-authored actor voice references are also
  clean-blocking: active evidence is `actor_variant_resolved_source_voice_references=29/29` and
  `actor_variant_unresolved_source_voice_references=0`. Unresolved actor variants, missing active gameplay identity
  rows, unresolved active foot-sound refs, and unresolved active object-authored actor sound/voice refs are
  clean-blocking errors. Scripted/model-backed objects are now separated
  from billboard-dependent presentation caches: `thjorgard` reports 62 scripted objects with model collision volumes and
  0 requiring billboard collision visuals; `thjorgardcity` reports 207 with model collision volumes and 0 requiring
  billboard collision visuals. The active slice now reports `missing_scripted_object_collision_visuals=0`.
- [ ] Keep GLB and billboard outputs as generated presentation caches, not source truth.

Tests:

- [ ] Unit: every map object with a model-like property resolves to exactly one source model or explicit non-rendered
  class.
- [ ] Unit: every actor/monster object resolves to a complete variant or emits a blocking diagnostic.
  Partial unit coverage now verifies that actor variant resolution preserves the official actor row evidence used to infer
  a variant from source object class/name: variant id, source model/skin, ACTOR row, number, monster name, type picture,
  and base name. The selected-object inspector now exposes that same resolver evidence for MM9 DAT model-instance and
  scripted-object selections.
- [ ] Unit: generated billboard metadata references source model/animation/skin identity and generated image frames.
- [x] Headless editor: active MM9 DAT documents load object-derived model-instance placement from sidecars without
  routing map geometry through ODM/BLV. `thjorgard.level.yml` reports 232 loaded instances and
  `thjorgardcity.level.yml` reports 790, matching the generated sidecar counts.
- [x] Headless editor: active MM9 DAT documents resolve every loaded object-derived model instance to a generated
  model asset, import drawable generated model geometry, and decode its source skin textures through the MM9 DTX loader.
  The headless resolver now treats model-instance skin paths as source-family references, resolving `skins/...` and
  `textures/...` against `assets_dev/worlds/mm9/source/` case-insensitively before decoding source DTX pixels.
  Current focused counts are: `thjorgard.level.yml` has 232/232 resolved model assets, 232/232 drawable model geometries,
  0 missing model assets, 0 missing drawable geometries, 325 decoded skin textures, and 53/53 actor variants resolved;
  `thjorgardcity.level.yml` has
  790/790 resolved model assets, 790/790 drawable model geometries, 0 missing model assets, 0 missing drawable
  geometries, 794 decoded skin textures, and 60/60 actor variants resolved. This validates asset/skin/geometry and
  actor-variant wiring for the active slice; generated billboard collision visuals, complete gameplay/sound/voice
  identity, and screenshot-proven viewport draw completeness are still tracked by the open items above. Focused
  DAT-level metadata and validator unit coverage now runs as named editor/import doctest cases through
  `tools/mm9_import_discovery/run_mm9_active_gate.sh`; the broad `MM9 DAT*` doctest bucket is not part of the active
  gate because it includes playable/runtime acceptance tests.
- [x] Headless editor: actor/monster inspector reports zero unresolved variants for the active city and outdoor-like
  maps.
  Active-slice evidence covers one outdoor-like map and one city map through DAT-level validation: `thjorgard` and
  `thjorgardcity` both report `actor_variant_unresolved=0`.
- [ ] `[future-regression]` Headless editor: actor/monster inspector reports zero unresolved variants for at least one
  representative dungeon and then all remaining local MM9 maps.
  This remains outside the active two-map gate until the same inspector path includes the remaining sound/voice/gameplay
  identity fields and the all-map milestone begins.

### Phase 8: Full Asset Graph Validation

- [ ] Implement `mm9 asset graph validate` logic usable by editor UI, unit tests, and headless tests.
- [ ] Validate `thjorgard` and `thjorgardcity` against source manifest, source assets, generated sidecars, generated
  caches, and authored overrides.
  The headless `--headless-verify-mm9-dat-level` path now emits deterministic active-slice reports for these maps under
  `assets_dev/worlds/mm9/import/validation/*.asset_validation.yml`. Required raw-object asset references are now clean
  for both active maps after scoped authored aliases resolve the absent official `Barrel02` and glass explosion
  resources. Optional `WorldProperties` sky/environment texture names are now resolved as built-in sky-controller
  metadata rather than source DTX targets. Material aliases and generated Lua/script
  IR paths validate cleanly for the two active maps, including loaded script include and label provenance. Current
  active-slice report counts are
  `asset_graph_required_unresolved=0`, `asset_graph_required_ambiguous=0`, and `asset_graph_optional_unresolved=0` for
  both `thjorgard` and `thjorgardcity`, `script_includes=60`, `script_resolved_includes=60`,
  `script_unresolved_includes=0`, `script_ambiguous_includes=0`, `script_labels=275`, and no stale caches.
  The reports also include object-derived presentation counters: `thjorgard` has
  `resolved_model_instance_assets=232`, `missing_model_instance_assets=0`, `drawable_model_instance_geometry=232`,
  `missing_drawable_model_instance_geometry=0`, `viewport_native_textured_triangles=31418`,
  `viewport_native_missing_material_triangles=0`, `decoded_model_instance_skin_textures=325`,
  `decoded_cache_determinism_checked=55`, and `decoded_cache_mismatches=0`; `thjorgardcity` has
  `resolved_model_instance_assets=790`, `missing_model_instance_assets=0`, `drawable_model_instance_geometry=790`,
  `missing_drawable_model_instance_geometry=0`, `viewport_native_textured_triangles=51397`,
  `viewport_native_missing_material_triangles=0`, `decoded_model_instance_skin_textures=794`,
  `decoded_cache_determinism_checked=132`, and `decoded_cache_mismatches=0`. Required asset-graph
  references and active model-instance asset/skin/drawable-geometry resolution are clean for both maps, but the report
  `clean` state now also includes required mechanism target resolution. Both current active-slice reports are
  `clean: true`; source object 1095 `RotatingDoor` / `BembStudy3` is resolved through the generated
  shared-rotation-point binding to DAT bmodel 122 `BembStudy2`.
  The viewport material split is now explicit: both active reports have
  `viewport_native_missing_material_triangles=0`, `viewport_native_placeholder_material_triangles=0`, and
  `viewport_native_unresolved_material_triangles=0`; future viewport material loss is blocking.
  The reports also expose the default PhysicsBSP display contribution:
  `viewport_native_renderable_physics_triangles=8984` for `thjorgard` and `47895` for `thjorgardcity`.
  DAT world reference validation is now part of the same report and clean gate: both active maps currently report
  `dat_world_reference_issues=0` and zero invalid leaf, surface texture, polygon surface, polygon plane, polygon vertex,
  node polygon, and root-node references.
- [ ] `[future-regression]` Add all-map validation as a later milestone/regression action after the two-map editor path
  is complete.
- [x] Add per-map and global reports under `assets_dev/worlds/mm9/import/validation/`.
  Focused DAT-level validation now writes per-map reports for the active slice and regenerates
  `active_slice.validation_summary.yml` from the current per-map reports. Current summary evidence: 2 reports,
  `clean_reports=2`, `dirty_reports=0`, `dat_world_reference_issues=0`,
  `asset_graph_required_unresolved=0`, `asset_graph_required_ambiguous=0`,
  `asset_graph_total=3050`, `asset_graph_resolved=3050`, `asset_graph_unresolved=0`,
  `asset_graph_ambiguous=0`, `asset_graph_stale=0`, `asset_graph_required_total=2831`,
  `asset_graph_required_resolved=2831`, `asset_graph_optional_total=219`,
  `asset_graph_optional_resolved=219`, `asset_graph_optional_unresolved=0`,
  `asset_graph_optional_ambiguous=0`,
  `raw_object_asset_refs=2628`, `required_raw_object_asset_refs=2622`, `optional_raw_object_asset_refs=6`,
  `unresolved_required_raw_object_asset_refs=0`, `unresolved_optional_raw_object_asset_refs=0`, `stale_caches=0`,
  `dat_world_invalid_leaf_references=0`, `dat_world_invalid_surface_texture_refs=0`,
  `dat_world_invalid_poly_surface_refs=0`, `dat_world_invalid_poly_plane_refs=0`,
  `dat_world_invalid_poly_vertex_refs=0`, `dat_world_invalid_node_poly_refs=0`,
  `dat_world_invalid_root_node_refs=0`, `raw_objects=2475`, `raw_object_sidecar_issues=0`,
  `object_source_transforms=2475`,
  `native_filter_visual=28533`, `native_filter_invisible=8992`, `native_filter_water=147`,
  `native_filter_visible_water=13`, `native_filter_water_volume=134`, `native_filter_rail=8164`,
  `native_filter_helper=88250`, `native_filter_physics=59147`, `native_filter_visibility=15791`, and
  `native_filter_portals=35`,
  `viewport_native_unresolved_material_triangles=0`, `missing_model_instance_assets=0`, and
  `mechanism_unresolved_required_targets=0`, with `actor_variant_candidates=113`, `actor_variant_unresolved=0`,
  `scripted_objects_with_model_collision_volumes=269`,
  `scripted_objects_requiring_billboard_collision_visuals=0`, and
  `missing_scripted_object_collision_visuals=0`. The same summary now records `mechanism_sound_slots=1064`,
  `mechanism_authored_sound_references=304`, `mechanism_empty_sound_references=760`,
  `mechanism_previewable_mechanisms=83`, `mechanism_inert_mechanisms=189`,
  `mechanism_inert_preview_entries=189`, `mechanism_without_preview_motion=189`, and
  `mechanism_without_preview_target=7`. It also records `mechanism_activation_start_open_fields=152`,
  `mechanism_activation_locked_fields=152`, `mechanism_activation_push_open_fields=152`,
  `mechanism_activation_touch_to_open_fields=152`, `mechanism_activation_lock_on_close_fields=0`,
  `mechanism_activation_reopen_on_contact_fields=152`, `mechanism_rotation_open_away_fields=80`,
  `mechanism_timing_move_delay_fields=152`, and `mechanism_timing_open_wait_fields=152`. It also records
  `mechanism_preview_candidates=165` and
  `mechanism_preview_changed_bounds=165`, proving every active-slice previewable world-model mechanism changes target
  bounds without source mutation. It also records DAT source-inspection overlay evidence:
  `world_model_overlay_vertices=26520`, `world_model_overlay_pick_candidates=1105`,
  `selected_polygon_overlay_vertices=27`, `selected_surface_overlay_vertices=9`, `object_overlay_vertices=1128`,
  `object_overlay_pick_candidates=47`, `asset_issue_marker_candidates=0`,
  `asset_issue_marker_required_candidates=0`, `asset_issue_marker_required_unpositioned=0`,
  `mechanism_target_marker_groups=529`, `mechanism_target_marker_candidates=529`,
  `mechanism_target_marker_vertices=16928`, `mechanism_target_marker_source_links=529`,
  `mechanism_gizmo_candidates=801`, `mechanism_circle_gizmo_candidates=272`,
  `mechanism_target_gizmo_candidates=529`, `mechanism_motion_path_markers=165`,
  `mechanism_los_checked_candidates=529`,
  `mechanism_los_blocked_candidates=94`,
  `light_overlay_vertices=7020`, `sound_overlay_vertices=6336`, and `spawn_overlay_vertices=798`.
  Active-slice per-map reports exist for `thjorgard`
  and `thjorgardcity`; the
  full-map/global report remains a later
  milestone so the current loop stays fast.
- [x] Block "clean" status on unresolved required references.
  Active-slice reports now use DAT world reference validation, required asset-graph unresolved/ambiguous counters, and
  required mechanism target counters for `clean`, while preserving optional-reference buckets in the report. Current
  active-slice evidence has `asset_graph_optional_unresolved=0`.
- [ ] Allow unused source assets as warnings only when not referenced by any loaded map or official table.
  Partial coverage now exists in the active reports: source-manifest family inventory that is not referenced by the
  loaded map's asset graph is emitted as normalized `warning` diagnostics from
  `mm9_asset_graph_source_inventory`, while `clean` remains true because these are non-blocking. Current active
  evidence includes `asset_graph_unused_source=11895` for `thjorgard` and `10563` for `thjorgardcity`, represented as
  per-family warnings. This remains open until the graph records individual unused source files and excludes assets
  referenced by any loaded map or official table, not just the current per-map graph.

Tests:

- [x] Unit/headless: `thjorgard` and `thjorgardcity` validate with asset-graph `unresolved_required=0` and
  `ambiguous_required=0`.
- [x] Unit/headless: `thjorgard` and `thjorgardcity` validate with zero unresolved required mechanism targets.
  Current state: both active maps pass DAT-level validation with `mechanism_unresolved_required_targets=0`. The event
  generator unit suite covers the shared-rotation-point binding rule that resolves `BembStudy3` without broadly binding
  arbitrary nearest movable models.
- [x] Unit/headless: active-slice validators run without opening or resolving every local MM9 map.
  Current focused event generation validation and idempotency checks run only for `thjorgard` and `thjorgardcity`
  against `assets_dev/worlds/mm9/maps` and `assets_editor_dev/worlds/mm9/maps`, using
  `assets_dev/worlds/mm9/source/scripts` as the source-script root. The editor-side event validator also opens only the
  named active-slice level and its declared sidecars/scripts.
- [ ] `[future-regression]` Milestone/regression: all 45 local MM9 maps validate with `unresolved_required=0` and
  `ambiguous_required=0`.
- [x] Unit/headless: intentionally missing DTX, missing model, missing script, missing sound, and ambiguous name
  fixtures each produce deterministic blocking diagnostics.
  Unit coverage now includes deterministic fixtures for missing required source DTX paths, missing raw-object model refs,
  missing raw-object script refs, missing raw-object sound refs, and ambiguous case-folded/basename candidates. The
  tests assert both unresolved/ambiguous resolver state and stable diagnostic substrings/candidate paths.
- [x] Unit: partial asset dependency summary groups level DAT, sidecars, generated script files, material DTX/cache rows,
  and raw-object source refs into resolved/unresolved/ambiguous/stale counters by family.
- [x] Unit/headless: source manifest counts match mirrored `source/*`.
  Unit coverage: `MM9 source asset manifest validation accepts mirrored source tree` parses the live
  `assets_dev/worlds/mm9/source/manifest.yml` and validates it against the mirrored source tree. Headless coverage:
  `--headless-verify-mm9-source-manifest --world mm9` reports 14 declared/required families and
  `expected_files=12646 actual_files=12646`.
- [ ] Unit/headless: regenerating sidecars from unchanged source produces no data-loss diffs.
  Partial coverage: `tests/mm9_events_generator_tests.py` now asserts that generated event/Lua/script-IR outputs pass
  `--check-idempotent` and that a stale generated Lua file is reported. Active two-map checks pass for generated event
  outputs in both the source and editor-dev world roots. This remains open for the other generated MM9 sidecar families.

### Phase 9: Editor Usability And Regression Gates

- [x] Add a map-open browser that distinguishes native MM9 DAT maps from compatibility ODM/BLV artifacts.
  The open-map browser labels native `*.level.yml` entries under `worlds/mm9` as `MM9 DAT` and MM9-derived `.odm` or
  `.blv` files as compatibility artifacts. The filter searches those labels too, which makes it harder to accidentally
  validate/render a derived file while investigating source DAT behavior.
- [x] Show validation status in the editor chrome.
  The editor status strip displays a `Validation · <count>` pill for the active document and exposes validation
  messages in a hover tooltip. MM9 DAT documents also show submitted DAT/model-instance vertex counts in the same
  chrome, which helps separate validation failures from viewport-submission gaps while investigating screenshots such
  as `test_img/923.png`.
- [x] Add search across world models, objects, textures, scripts, sounds, lights, actor variants, and diagnostics.
  The MM9 scene outliner search now filters source-backed groups for DAT world models, raw objects, material/DTX rows,
  event objects, mechanisms, scripts, source asset references including sounds/voices, typed light objects,
  object-derived model instances, actor variant resolver output, and diagnostics. Search hits on selectable rows jump to
  the corresponding inspector
  row. `--headless-verify-mm9-inspector-search <level.yml>` covers the same source-backed categories and keeps the
  active-slice acceptance deterministic.
- [x] Add "copy source id/path" actions for every inspector row.
  MM9 DAT inspector rows now expose one-click copy controls for source ids, source object/model names, DAT/DTX/source
  paths, generated sidecar/script paths, material aliases, raw object refs, asset-reference paths, binding targets, and
  candidate evidence. The helper is MM9-only so the existing MM6-MM8 inspector rows keep their current presentation.
- [x] Add "open generated sidecar" and "open source asset path" actions.
  MM9 DAT inspectors now pair copy controls with explicit local-file open buttons for level/source DATs, generated
  sidecars, generated Lua/script IR, compatibility outputs, source-manifest families, DTX/SPR source candidates, raw
  object asset references, material caches, and document path rows. Buttons are disabled for missing or placeholder
  paths, so unresolved rows remain inspectable without silently inventing fallback locations.
- [x] Cache source DTX indexes and content hashes per editor document/session so lossless validation remains available
  without making normal inspector refreshes pay full-dataset hashing cost.
  `EditorDocument` now owns an MM9 material inspection cache that reuses source DTX discovery, DTX headers, and
  source/cache SHA-256 reads while invalidating cached file entries when size or write time changes.
- [x] Add screenshot/headless visual smoke coverage for editor viewport states.
  The focused native DAT render smoke presents the editor viewport texture to the backbuffer and validates nonblank
  screenshot readback for `thjorgard` and `thjorgardcity`. The companion model-instance-only smoke hides native DAT
  world geometry and validates that object-derived model-instance batches are visible on their own. Additional DAT
  world subset smokes isolate water-role geometry and PhysicsBSP geometry with model instances hidden.

Tests:

- [x] Headless editor: regression coverage exists for repeated MM9 map open/close without leaks or stale document state.
  The current active slice remains `thjorgard` and `thjorgardcity`.
- [x] Headless editor: inspector search finds known texture, object, script, and model names.
  `--headless-verify-mm9-inspector-search thjorgard.level.yml` indexes 4,771 rows across world models, textures,
  raw objects, scripts, sounds/voices, typed lights, typed sound objects, model instances, actor variants, and
  diagnostics, and verifies known terms such as `RAIL`, `BlueWater0`, `HalfOrcCaptain0`, `PROPANIM.scr`, `Barrel`,
  `peasant`, `Light`, and `Sound`.
  `--headless-verify-mm9-inspector-search thjorgardcity.level.yml` indexes 12,795 rows across the same families and also
  verifies `BembStudy3` is findable as object evidence and as a resolved shared-rotation-point mechanism binding target.
- [ ] Regression: MM6-MM8 outdoor and indoor editor smoke tests still pass.
  Partial current evidence: the active gate wrapper now runs
  `--headless-run-regression-suite editor-world-outdoor-terrain-load --world mm6`, which passes for `oute3.odm`, and
  `--headless-verify-document-dispatch` passes with 3 outdoor and 3 indoor MM6-MM8 legacy cases plus 2 MM9 DAT cases.
  The paired `indoor-map-package-load` editor suite is not currently green in this checkout because it reports
  `unexpected indoor source geometry`; `editor-world-map-script-load` is also not currently green because it resolves
  `Data/scripts/maps/oute3.lua` under `assets_dev/worlds/mm6/events/...` while the suite expects the
  `assets_editor_dev/worlds/mm6/events/...` path. Those are tracked here as pre-existing regressions to recheck rather
  than fixed inside the MM9 DAT inspector changes.
- [ ] Regression: regular game/runtime MM6-MM8 map loading does not see or require MM9 sidecars.

## Active Gate Definition Of Done

This definition applies to the active two-map editor gate only. Future all-map regression and playable/runtime work are
tracked below as separate milestones and must not keep the active gate open unless they expose a failure in
`thjorgard`, `thjorgardcity`, or shared source-preserving services used by those maps.

- [ ] The editor uses native DAT geometry, source DTX materials, object/model/actor source references, and
  source-index-preserving sidecars for the active maps.
- [ ] No active-map required texture, model, skin, sprite, sound, voice, script, object target, event target, mechanism
  target, actor variant, or monster variant reference is unresolved.
- [x] All compatibility ODM/BLV outputs are clearly labeled as derived migration artifacts.
  MM9 level metadata requires `compatibility.generated_odm_blv_are_derived: true`, the document path inventory classifies
  compatibility paths as generated `derived_compatibility_artifact` entries, the summary inspector labels the
  compatibility section with `ODM/BLV Derived`, the map-open browser labels MM9-derived `.odm`/`.blv` files as
  compatibility artifacts, and the active reports serialize those paths under
  `document_paths.compatibility_derived_files`. Unit coverage now also asserts the BLV compatibility path is generated,
  compatibility-derived, and has the `derived_compatibility_artifact` role.
- [x] Source files under `source/*` remain unchanged during editor open, validation, preview, save, and build actions.
  MM9 DAT documents reject save/build paths that would mutate source truth, verify the source DAT hash from each level
  entrypoint, report source manifest family counts, compare a before/after source-integrity snapshot around
  open/validation/save/build rejection, and compare content digests for resolved source files referenced by material,
  sprite-frame, and raw-object asset inspection. Active focused evidence: `thjorgard.level.yml` validates 243
  referenced source-file digests and `thjorgardcity.level.yml` validates 443, with `source_mutation_snapshot_verified`
  true for both.
- [ ] Unit and headless tests cover document dispatch, DAT parsing, DTX resolution, material assignment, object/event
  binding, mechanism preview, portal/visibility inspection, actor/monster variant resolution, full asset graph
  validation, and MM6-MM8 non-regression for the active two-map gate.
- [ ] The same resolver/validator code paths are usable by editor and game runtime, preventing editor-only correctness.

## Future All-Map Regression Definition Of Done

- [x] All 45 MM9 DAT maps open in the editor through `maps/<map>.level.yml`.
- [ ] `[future-regression]` All 45 local MM9 maps validate with the same required-reference, source-index, sidecar
  idempotency, renderability, and inspection invariants proven by the active two-map gate.
- [ ] `[future-regression]` All-map failures are triaged as either active-gate defects, future-regression defects, or
  source-data policy decisions, instead of being mixed into the active gate by default.

## Playable Runtime Milestone Definition Of Done

- [ ] `[runtime-blocked]` Playable MM9 game-world integration has not started unless the active two-map editor gate above
  is complete or this goal document has been explicitly revised with a narrower exception.
- [ ] `[runtime-blocked]` Runtime MM9 work reuses the editor-proven DAT, DTX, source-index, material, model, script,
  event, and mechanism services instead of adding separate shortcuts.
