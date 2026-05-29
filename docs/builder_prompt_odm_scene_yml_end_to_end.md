Implement the outdoor `ODM + .scene.yml` migration end-to-end in OpenYAMM.

Context and constraints:
- Repo: `/home/pjasicek/github/OpenYAMM`
- Follow `/home/pjasicek/github/OpenYAMM/AGENTS.md` exactly.
- Never copy code from `reference/OpenEnroth-git/` or `reference/mm_mapview2-master/`. Use them only as behavioral references.
- Keep solutions simple and maintainable.
- Use `apply_patch` for edits.
- Prefer existing runtime systems and do not invent a parallel architecture unless necessary.

Primary docs to consume first:
- `/home/pjasicek/github/OpenYAMM/docs/odm_ddm_to_scene_yml_export_spec.md`
- `/home/pjasicek/github/OpenYAMM/docs/odm_ddm_to_scene_yml_converter_plan.md`
- `/home/pjasicek/github/OpenYAMM/docs/odm_scene_yml_acceptance_test_spec.md`
- `/home/pjasicek/github/OpenYAMM/docs/runtime_refactor_plan.md`
- `/home/pjasicek/github/OpenYAMM/docs/game-engine-architecture.md`

Existing implementation to reuse:
- `/home/pjasicek/github/OpenYAMM/tools/export_outdoor_scene_yml.py`

Goal:
Implement the outdoor migration seam so that OpenYAMM can load:
1. legacy path: `ODM + DDM`
2. migrated path: `ODM + scene.yml`
and produce the same effective authored outdoor runtime state.

Architectural rule:
- Keep `ODM` unchanged in this phase.
- `.scene.yml` becomes the preferred authored supplement.
- `DDM` remains compatibility fallback.
- Save data still overrides authored defaults after map load.
- This is a conservative first-phase replacement of the authored companion format, not a full runtime redesign.

Required implementation scope:
1. Add loader support for outdoor `.scene.yml`.
2. Integrate it into the outdoor map load flow with precedence:
   - save data
   - `.scene.yml`
   - `DDM`
   - duplicated legacy `ODM` authored fields
3. Populate the same effective authored/runtime structures the current `DDM` path feeds.
4. Keep current behavior for maps that do not have `.scene.yml`.
5. Do not break existing `DDM` loading.
6. Reuse the existing exporter script for generating test fixtures where useful.
7. Add or adapt headless acceptance coverage per the acceptance spec.
8. Validate against real outdoor maps.

Important data rules from the docs:
- `decorationPidList` / `decorationMap` are derived lookup structures and must not become `.scene.yml` authority.
- `attributeMap`: only known named semantics are `burn` and `water`; preserve raw legacy values where needed.
- `normalMap` / stored normals are not authored truth.
- `scene.yml` is allowed to contain more authored information than current runtime happens to use, but for this implementation you only need to correctly consume the defined schema and preserve legacy meaning where specified.

Implementation guidance:
- Keep the first-phase loader path narrow and explicit.
- Prefer adding a scene-YAML parse/build layer that feeds current outdoor runtime state, rather than pushing YAML awareness deep into unrelated systems.
- If a legacy-shaped runtime struct is awkward, add a clean adapter layer instead of spreading YAML parsing logic everywhere.
- Use deterministic parsing/validation and fail with actionable errors.

Suggested work order:
1. Inspect current outdoor load path in `game/maps/MapAssetLoader.*`, `game/maps/MapDeltaData.*`, `game/outdoor/*`, `game/scene/OutdoorSceneRuntime.*`.
2. Add YAML parse/model support for the schema defined in the export spec.
3. Integrate `.scene.yml` loading into outdoor map load.
4. Implement merge/precedence rules.
5. Add diagnostics/logging for which authored source was used.
6. Add acceptance tests / headless comparison harness.
7. Run against several real outdoor maps and fix mismatches.

Acceptance criteria:
- Real outdoor maps load through both paths.
- `ODM + scene.yml` matches `ODM + DDM` for the normalized authored state described in the acceptance spec.
- Existing maps without `.scene.yml` still work.
- Save override behavior remains correct.
- No destructive rewrites of existing assets are required for runtime loading.
- Code is clean, reviewable, and consistent with repo architecture.

Deliverables:
- code changes implementing `.scene.yml` load path
- tests / diagnostics / comparison tooling needed for confidence
- brief summary of changed files
- explicit note of anything still intentionally deferred

Out of scope for this task:
- full indoor `BLV + scene.yml` implementation
- editor UI work
- replacing the legacy geometry formats
- broad Lua event migration beyond what is necessary to keep current outdoor authored behavior intact

Before coding:
- inspect the current codebase carefully
- produce a short plan
- then implement end-to-end
- run verification before finishing
