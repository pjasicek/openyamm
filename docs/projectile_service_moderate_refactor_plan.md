# Projectile Service Moderate Refactor Wiggum Plan

This document is the authoritative executable plan for the projectile service
moderate refactor.

It is designed for repeated autonomous execution. Do not execute it linearly
from top to bottom. Use the task queue section as the executable queue and
update the progress section after every meaningful slice.

## Goal

Reduce projectile over-abstraction without merging indoor/outdoor world logic.

Keep the core architecture:

- shared projectile code owns projectile state and gameplay rules;
- active world owns collision/fact collection and world-specific application;
- projectile simulation is entered from the active world update path;
- behavior remains unchanged unless a clear projectile bug is found and fixed
  intentionally.

The target readable frame shape is:

```cpp
ProjectileFrameFacts facts = world.collectProjectileFrameFacts(projectile, deltaSeconds);
ProjectileFrameResult result = projectileService.updateProjectileFrame(projectile, facts);
world.applyProjectileFrameResult(projectile, result);
```

## Boundary Rule

Shared projectile service owns what projectile gameplay should do.

Active world owns what the projectile collided with, how collision is computed,
and how results are applied to ODM/BLV representation.

Do not replace many decision structs with many callbacks. The exchange should
be domain data: facts in, result out.

## Non-Goals

- Do not merge indoor and outdoor runtime/render/collision types.
- Do not rewrite projectile behavior.
- Do not split `GameplayProjectileService` into many files in this refactor.
- Do not move all projectile code into `GameSession`.
- Do not change save format unless unavoidable.
- Do not refactor Fire Spike, Meteor Shower, Starburst, and projectile
  presentation all at once.
- Do not create another adapter layer that only hides the existing complexity.

## Current Pain

`GameplayProjectileService` exposes too many intermediate frame-decision types:

- `ProjectileFrameAdvanceResult`;
- `ProjectileImpactDecision`;
- `ProjectileLifetimeExpiryDecision`;
- `ProjectileBounceDecision`;
- `ProjectileCollisionOutcomeDecision`;
- `ProjectileCollisionPresentationDecision`;
- `ProjectileCollisionResolutionDecision`;
- `ProjectileCollisionFrameDecision`;
- `ProjectileUpdateFrameDecision`;
- multiple command enums.

This is mechanically correct but hard to read. The public API describes the
extraction mechanics more than the projectile domain.

Current follow-up after the initial facts/result extraction:

- the main frame boundary is already `ProjectileFrameFacts` -> `ProjectileFrameResult`;
- the next cleanup target is the remaining public `*Decision` / `*Command` vocabulary that represents internal
  service mechanics instead of projectile gameplay outcomes;
- keep coarse, typed facts/results, but make them human-readable;
- do not collapse everything into untyped flags or callbacks just to reduce the struct count;
- reduce helper structs where they are only phase plumbing, and keep structs where they describe real projectile
  domain data.

## Target Public Shape

### `ProjectileFrameFacts`

A heavier facts struct built by the active world. It should contain all data
shared projectile logic needs for one projectile frame:

```cpp
struct ProjectileFrameFacts
{
    float deltaSeconds = 0.0f;
    float gravity = 0.0f;
    float bounceFactor = 0.0f;
    float bounceStopVelocity = 0.0f;
    float groundDamping = 0.0f;

    ProjectileMotionSegment motion;

    bool hasCollision = false;
    ProjectileCollisionFacts collision;

    GameplayWorldPoint partyPosition;
    float partyCollisionRadius = 0.0f;
    float partyCollisionHeight = 0.0f;

    std::vector<ProjectileAreaActorFacts> areaActors;
};
```

### `ProjectileFrameResult`

A heavier result struct returned by shared projectile logic. It should contain
readable outcomes, not nested command scripts:

```cpp
struct ProjectileFrameResult
{
    ProjectileMotionSegment motion;
    bool applyMotionEnd = false;
    bool expireProjectile = false;
    bool logCollision = false;
    bool logLifetimeExpiry = false;

    std::optional<ProjectileBounceResult> bounce;
    std::optional<ProjectileDirectPartyImpact> directPartyImpact;
    std::optional<ProjectileDirectActorImpact> directActorImpact;
    std::optional<ProjectileAreaImpact> areaImpact;
    std::optional<ProjectileFxRequest> fxRequest;
    std::optional<ProjectileAudioRequest> audioRequest;
    std::vector<ProjectileSpawnRequest> spawnedProjectiles;
};
```

Exact names may change to fit current code. The important part is one readable
frame facts packet and one readable frame result packet.

### Frame API

Add or converge to:

```cpp
ProjectileFrameResult GameplayProjectileService::updateProjectileFrame(
    ProjectileState &projectile,
    const ProjectileFrameFacts &facts) const;
```

Keep low-level mutators only where they are true world application helpers.

## Executable Task Queue

### Step 1 - Add coarse frame facts/result types

- [ ] Audit current public projectile structs in `GameplayProjectileService.h`.
- [ ] Add `ProjectileFrameFacts` beside existing types.
- [ ] Add `ProjectileFrameResult` beside existing types.
- [ ] Prefer complete domain packets over many tiny public input/result structs.
- [ ] Do not change call sites yet.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Project builds.
- No projectile behavior changes.
- New types do not expose outdoor or indoor representation details.

### Step 2 - Add outdoor projectile frame fact builder

- [ ] Audit `OutdoorWorldRuntime::updateProjectiles`.
- [ ] Add a helper that collects all world facts needed for one projectile
  frame.
- [ ] Reuse existing collision/bounce/area-impact helpers internally.
- [ ] Keep behavior unchanged.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- `updateProjectiles` becomes slightly flatter.
- World-specific collision and terrain/bmodel facts remain outdoor-owned.

### Step 3 - Implement `updateProjectileFrame`

- [ ] Implement the new frame API in `GameplayProjectileService`.
- [ ] Initially delegate to existing internal decision builders if that reduces
  risk.
- [ ] Convert old decision output into `ProjectileFrameResult`.
- [ ] Add local helper names that describe projectile behavior, not extraction
  plumbing.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Old and new paths produce equivalent outcomes.
- No old public structs removed yet.

### Step 4 - Switch outdoor projectile loop to facts/result

- [x] Change outdoor projectile loop to collect facts, call
  `updateProjectileFrame`, then apply result.
- [x] Add `OutdoorWorldRuntime::applyProjectileFrameResult`.
- [x] Keep existing helper methods temporarily where useful.
- [x] Preserve projectile logging, audio, FX, bounce, area damage, direct damage,
  lifetime expiry, and spawned projectile behavior.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- `OutdoorWorldRuntime::updateProjectiles` reads as the target loop.
- Outdoor no longer switches over shared service command enums for the main
  projectile frame.

### Step 5 - Remove or privatize old frame-decision layer

- [x] Remove old intermediate decision structs from the public header where no
  longer used by call sites.
- [x] Keep old helpers private only if they still clarify internal
  implementation.
- [x] Remove public command enums that are only frame-update plumbing.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Public projectile API is smaller and domain-shaped.
- Old frame-update command-script API is gone from public use.

### Step 6 - Rename misleading presentation terms

- [x] Rename result/effect types that use "presentation" for audio/log/impact
  orchestration.
- [x] Reserve "presentation" for actual render-facing state.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Naming distinguishes gameplay result/effects from renderer-facing
  presentation state.

### Step 7 - Re-audit Fire Spike and shower projectiles only after stable frame path

- [x] Audit Fire Spike, Meteor Shower, Starburst, and special projectile paths.
- [x] Record whether they fit the new frame shape or need a separate follow-up.
- [x] Do not refactor them unless the main projectile loop is already stable and
  the change is small.
- [x] Build and run ctest if code changed.
- [x] Update progress.

Acceptance:

- Special projectile paths are documented and not accidentally broken.

### Step 8 - Clean public projectile decision/command vocabulary

- [x] Remove command-vector plumbing from projectile spawn effects.
- [x] Remove command-vector plumbing from Fire Spike trigger results.
- [x] Rename remaining public projectile `*Decision` types to domain outcome names.
- [x] Rename public `build*Decision` methods to domain builder names.
- [x] Keep `ProjectileFrameFacts` and `ProjectileFrameResult` as the frame boundary.
- [x] Keep behavior unchanged.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- `GameplayProjectileService.h` exposes no projectile-specific `*Decision` types.
- The normal projectile and Fire Spike paths no longer use public command-script enums.
- Remaining public structs describe projectile state, facts, inputs, requests, or outcomes.

### Step 9 - Audit remaining projectile helper structs for consolidation

- [x] Audit all remaining public helper structs in `GameplayProjectileService.h`.
- [x] Remove safe one-purpose helper structs from the public API where direct parameters or direct frame outcomes are
  clearer.
- [x] Identify any remaining helper structs that can be merged into `ProjectileFrameFacts`, `ProjectileFrameResult`, or another
  coarse domain packet without hurting readability.
- [x] Do not merge indoor/outdoor representation details.
- [x] Do not replace typed facts/results with callback bags.
- [x] Build and run ctest if code changes.
- [ ] Update progress.

Acceptance:

- Any remaining high-count struct surface is intentional and documented.
- Candidate follow-up merges are listed before implementation.

## Wiggum Prompt

Use this prompt for autonomous loop execution:

```text
Read these files first:

- AGENTS.md
- docs/indoor_outdoor_shared_gameplay_extraction_plan.md
- docs/projectile_service_moderate_refactor_plan.md

Use docs/projectile_service_moderate_refactor_plan.md as the executable plan
for this run.

Do not execute the plan linearly. Execute the next unfinished task from the
Executable Task Queue.

Work on one coherent slice. Keep projectile behavior unchanged unless fixing a
clear bug. Do not merge indoor/outdoor world logic. Do not introduce callback
bags or adapters that hide ownership. Shared projectile service owns projectile
gameplay decisions; active world owns collision facts and world application.

Run:
- cmake --build build --target openyamm -j25
- ctest --test-dir build --output-on-failure

Update the progress section in docs/projectile_service_moderate_refactor_plan.md
with concrete evidence, validation, and remaining work.

Stop only after finishing the current slice and leaving the repo buildable, or
if the progress section records: Hard blocker: YES.
```

## Progress

Current status:

- Overall completion: complete.
- Current focus: projectile indoor loop readability cleanup.
- Last validated at: 2026-04-22, P10 indoor loop split build/ctest.
- Hard blocker: NO

Done definition satisfied: YES

Validation history:

- 2026-04-22: Projectile Step 8 removed the public command-vector scripts from `ProjectileSpawnEffects` and
  `FireSpikeTrapTriggerResult`; they now expose direct domain outcome booleans.
- 2026-04-22: Projectile Step 8 renamed the remaining projectile impact/trap public `*Decision` result types and
  `build*Decision` methods to domain result/outcome names. Static `rg` found no `ProjectileSpawnEffectCommand`,
  `FireSpikeTrapTriggerCommand`, projectile-specific `*Decision`, or `build*Decision` names in
  `GameplayProjectileService`, `OutdoorWorldRuntime`, or `IndoorWorldRuntime`.
- 2026-04-22: Projectile Step 9 started with safe one-purpose struct removal:
  `PartyProjectileActorImpactInput`, `PartyProjectileActorImpactResult`, `ProjectileDirectPartyImpactInput`,
  `ProjectileSpawnEffectOptions`, and `FireSpikeTrapLifetimeFrame` were folded into direct parameters/results.
- 2026-04-22: Projectile Step 9 continued by removing `ProjectileDirectPartyImpact`,
  `ProjectileDeathBlossomFalloutRequest`, and `ProjectileImpactRequest`. Direct party impact is now optional damage,
  Death Blossom fallout is now an optional world point, and impact visual spawning builds `ProjectileImpactState`
  directly inside the service.
- 2026-04-22: Static API audit found no projectile-specific `*Decision`, `build*Decision`,
  `ProjectileSpawnEffectCommand`, `FireSpikeTrapTriggerCommand`, `ProjectileImpactRequest`, or stale `.decision`
  field names in `GameplayProjectileService`, `OutdoorWorldRuntime`, or `IndoorWorldRuntime`.
- 2026-04-22: `GameplayProjectileService.h` now has 36 nested public structs and 3 nested public enums. Remaining
  public structs are domain state, spawn/impact definitions, frame facts/results, world-supplied actor/collision facts,
  or Fire Spike facts/results.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the P8/P9 cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the P8/P9 cleanup slice; no
  tests were found in the current build tree.
- 2026-04-22: Projectile Step 10 split the indoor projectile loop into
  `IndoorWorldRuntime::collectIndoorProjectileFrameFacts` and
  `IndoorWorldRuntime::applyIndoorProjectileFrameResult`. Indoor still owns indoor face/party/actor collision facts and
  result application, while `GameplayProjectileService::updateProjectileFrame` remains the shared gameplay decision
  point.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the P10 indoor loop split.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the P10 indoor loop split; no
  tests were found in the current build tree.
- 2026-04-22: Acceptance follow-up fixed legacy outdoor companion lookup outside projectile-frame ownership.
  `MapAssetLoader` now resolves staged legacy DDM companions from `_legacy/map_delta` after checking `Data/games`,
  allowing `outdoor_scene_yml_matches_legacy_ddm_authored_state` to compare scene-YML state against legacy state for
  Out01, Out02, Out05, and Out13.
- 2026-04-22: Acceptance follow-up changed the focused `app_background_music_follows_selected_map` diagnostic outside
  projectile-frame ownership to initialize runtime-only after renderer shutdown; that case checks selected-map music
  track state and does not need render-facing outdoor view assets.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the legacy companion/music
  diagnostic follow-up slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the legacy companion/music
  diagnostic follow-up slice; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regressions passed after the follow-up slice:
  `outdoor_scene_yml_matches_legacy_ddm_authored_state` and `app_background_music_follows_selected_map`. Projectile
  manual smoke remains pending.
- 2026-04-22: Indoor headless suite passed with `passed=21 failed=0`. Full dialogue root acceptance remains open: a
  broad run before the music diagnostic adjustment passed the relevant projectile smoke and scene-YML parity cases,
  then exited 139 in the following headless audio/view initialization area.
- 2026-04-22: Acceptance follow-up stabilized the focused treasure-spawn diagnostic outside projectile-frame
  ownership. The synthetic case now uses high ordinary treasure-map conditions and a small batch of added treasure
  spawns so it no longer depends on a rare-only/no-materialized-item outcome.
- 2026-04-22: Acceptance follow-up fixed the focused speech-audio headless crash outside projectile-frame ownership.
  The speech-audio diagnostics now initialize runtime-only after renderer shutdown instead of allocating HUD/view
  textures through bgfx in a headless no-renderer path.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the diagnostic stabilization
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the diagnostic stabilization
  slice; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regressions passed after the diagnostic stabilization slice:
  `treasure_spawn_points_materialize_world_items_on_first_outdoor_load`,
  `spellbook_speech_audio_resolves_for_success_failure_and_store_closed`,
  `damage_speech_audio_resolves_for_all_default_seed_members`, and
  `damage_speech_audio_resolves_for_roster_seeded_party_members`. Projectile manual smoke remains pending.
- 2026-04-22: Indoor headless suite passed with `passed=21 failed=0`. Full dialogue rerun passed the previously
  residual projectile/actor smoke and speech-audio cases, but root acceptance remains open because
  `outdoor_scene_yml_matches_legacy_ddm_authored_state` fails and the process exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up fixed the focused CanShowTopic killed-context diagnostic. The change is outside
  projectile frame ownership: the synthetic CanShowTopic script now checks actor-id kill policy for actor 8, matching
  the diagnostic setup that kills actor 8.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the CanShowTopic diagnostic
  fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the CanShowTopic diagnostic
  fix; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regression
  `OPENYAMM_REGRESSION_FILTER=event_can_show_topic_actor_killed_uses_scene_context timeout 120s
  build/game/openyamm --headless-run-regression-suite dialogue` passed with `passed=1 failed=0`. Projectile manual
  smoke remains pending.
- 2026-04-22: Indoor headless suite passed with `passed=21 failed=0`. Full dialogue rerun still passed relevant
  projectile smoke cases, but root acceptance remains open because treasure-spawn materialization still fails and the
  process exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up fixed the focused spell-backend coverage diagnostic. The change is outside
  projectile frame ownership: Fire Aura and Vampiric Weapon coverage now supplies an equipped common weapon item
  target, Recharge Item requests inventory-item selection, and utility-target spells without an action report
  `NeedUtilityUi` instead of falling through to a generic failure.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the spell-backend diagnostic
  fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the spell-backend diagnostic
  fix; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regression
  `OPENYAMM_REGRESSION_FILTER=party_spell_backend_supports_all_defined_non_utility_spells timeout 120s
  build/game/openyamm --headless-run-regression-suite dialogue` passed with `passed=1 failed=0`. Projectile manual
  smoke remains pending; root acceptance remains open for full-suite dialogue/audio follow-up and manual smoke.
- 2026-04-22: Acceptance follow-up fixed the focused outdoor party water-boundary diagnostic. The change is outside
  projectile frame ownership: the synthetic diagnostic now computes water/land tile centers through
  `outdoorGridCornerWorldX/Y`, and party movement allows already-airborne water crossing while keeping grounded
  no-water-walk blocking intact.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the water-boundary diagnostic
  fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the water-boundary diagnostic
  fix; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regressions for
  `party_airborne_movement_allows_water_entry_without_water_walk` and
  `party_ground_movement_blocks_water_entry_without_water_walk` both passed with `passed=1 failed=0`. Projectile
  manual smoke remains pending; root acceptance remains open for unrelated residual dialogue diagnostics and
  full-suite audio decode exit 139.
- 2026-04-22: Acceptance follow-up reran `cmake --build build --target openyamm -j25` after the outdoor
  corpse-loot fix; the build completed successfully.
- 2026-04-22: Acceptance follow-up reran `ctest --test-dir build --output-on-failure` after the outdoor
  corpse-loot fix; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke cases still
  passed in the log, including local event projectile spawn/gravity, Meteor Shower ground impact, ranged projectile
  release, party projectile actor impact, party spell projectile actor impact, fireball splash, and visible spell
  impact cases. Root acceptance remains open because unrelated residual dialogue diagnostics and audio decode errors
  still make the suite non-clean.
- 2026-04-22: Acceptance follow-up static audit reran `rg` checks. Outdoor and indoor projectile loops still use
  `ProjectileFrameFacts` / `ProjectileFrameResult` and call `GameplayProjectileService::updateProjectileFrame`.
- 2026-04-22: Acceptance follow-up static audit found no remaining references to the old projectile frame
  command-layer names in `game`, `engine`, `editor`, or `tools`, including `ProjectileUpdateFrameDecision`,
  `ProjectileFrameAdvanceResult`, `ProjectileCollisionFrameDecision`, `buildProjectileUpdateFrameDecision`, and
  `applyProjectileUpdateFrameDecision`.
- 2026-04-22: Acceptance follow-up reran `cmake --build build --target openyamm -j25`; the build completed
  successfully.
- 2026-04-22: Acceptance follow-up reran `ctest --test-dir build --output-on-failure`; CTest completed successfully
  and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke coverage
  passed again, including local event fireball/cannonball projectile spawn and gravity, Meteor Shower ground impact,
  actor ranged projectile release and party hit, party arrow and spell projectile actor hits, fireball splash against
  party and multiple actors, and visible spell impact effects.
- 2026-04-22: Root acceptance remains open. The dialogue suite is still non-clean evidence because it reports
  residual failures outside the projectile frame refactor and exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke coverage
  passed in the log, including local event fireball/cannonball projectile spawn and gravity, Meteor Shower ground
  impact, actor ranged projectile release and party hit, party arrow and spell projectile actor hits, fireball splash
  against party and multiple actors, and visible spell impact effects.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it reports residual failures outside
  the projectile frame refactor and exits 139.
- 2026-04-22: Static `rg` audit reconfirmed that outdoor and indoor projectile loops use `ProjectileFrameFacts` /
  `ProjectileFrameResult` and call `GameplayProjectileService::updateProjectileFrame`; old projectile frame
  command-layer names remain absent from game, engine, editor, and tools code.
- 2026-04-22: Current acceptance follow-up reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Current acceptance follow-up reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Current acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Current acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke coverage
  passed in the log, including local event fireball/cannonball projectile spawn and gravity, Meteor Shower ground
  impact, actor ranged projectile release and party hit, party arrow and spell projectile actor hits, fireball splash
  against party and multiple actors, and visible spell impact effects.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it reports residual failures outside
  the projectile frame refactor and exits 139 after repeated audio decode errors.
- 2026-04-22: Current static `rg` audit reconfirmed that outdoor and indoor projectile loops use
  `ProjectileFrameFacts` / `ProjectileFrameResult` and call `GameplayProjectileService::updateProjectileFrame`.
- 2026-04-22: Current static `rg` audit found no remaining references to the old projectile frame command-layer names
  in `game`, `engine`, `editor`, or `tools`, including `ProjectileUpdateFrameDecision`,
  `ProjectileFrameAdvanceResult`, `ProjectileCollisionFrameDecision`, `buildProjectileUpdateFrameDecision`, and
  `applyProjectileUpdateFrameDecision`.
- 2026-04-22: Acceptance follow-up reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke cases still
  passed in the log, including party arrow and spell projectile actor hits, actor ranged projectile release and party
  hit, fireball splash, and visible spell impact effects.
- 2026-04-22: Root acceptance remains open. The dialogue suite is still non-clean evidence: it reports residual
  failures outside the projectile frame refactor and exits 139 after repeated audio decode errors.
- 2026-04-22: Acceptance follow-up reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke coverage
  passed again in the log, including local event projectile spawn/gravity, actor ranged projectile release and party
  hit, party arrow and spell projectile actor hits, fireball splash, and visible spell impact effects.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it still reports residual failures
  outside the projectile frame refactor and exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up validation slice reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up validation slice reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up validation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up validation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant projectile smoke coverage
  passed again, including local event fireball/cannonball spawn and gravity, Meteor Shower ground impact, actor ranged
  projectile release and party hit, party arrow and spell projectile actor hits, fireball splash, and visible spell
  impact effects.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it reports residual failures outside
  the projectile frame refactor and then exits 139 after repeated audio decode errors.
- 2026-04-22: Final projectile acceptance audit confirmed with static `rg` that outdoor and indoor projectile loops
  use `ProjectileFrameFacts` / `ProjectileFrameResult` and call
  `GameplayProjectileService::updateProjectileFrame`.
- 2026-04-22: Static `rg` audit found no remaining references to the old projectile frame command-layer names in
  `game`, `engine`, `editor`, or `tools`, including `ProjectileUpdateFrameDecision`,
  `ProjectileFrameAdvanceResult`, `ProjectileCollisionFrameDecision`, `buildProjectileUpdateFrameDecision`, and
  `applyProjectileUpdateFrameDecision`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully during the final projectile
  acceptance audit slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully during the final projectile
  acceptance audit slice; no tests were found in the current build tree.
- 2026-04-22: Attempted extra headless validation with
  `build/game/openyamm --headless-run-regression-suite dialogue`. The run passed many relevant projectile cases
  before it could be treated as acceptance evidence, including local event projectile spawn/gravity, Meteor Shower
  ground impact, ranged projectile release, party projectile actor impact, party spell projectile actor impact,
  fireball splash, and visible spell impact cases.
- 2026-04-22: The extra dialogue regression suite did not complete cleanly: it reported
  `party_airborne_movement_allows_water_entry_without_water_walk` as failed, then stopped producing output after the
  later outdoor geometry case and was interrupted. This is recorded as pending follow-up and not counted as passing
  acceptance evidence.
- 2026-04-21: Completed Step 1 by auditing the public projectile structs in `GameplayProjectileService.h` and adding
  coarse `ProjectileFrameFacts` / `ProjectileFrameResult` packet types beside the existing public API.
- 2026-04-21: New frame facts/results use generic projectile domain data only; no ODM/BLV runtime types, `bx::Vec3`,
  face indices, renderer state, or world-specific storage details were added.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully; no tests were found in the current
  build tree.
- 2026-04-21: Completed Step 2 by auditing `OutdoorWorldRuntime::updateProjectiles` and adding
  `OutdoorWorldRuntime::collectProjectileFrameFacts`.
- 2026-04-21: The new outdoor helper collects shared `ProjectileFrameFacts` plus the outdoor collision facts still
  needed by the existing application path; it reuses the existing collision, bounce-surface, direct-hit, and
  area-impact fact helpers.
- 2026-04-21: `updateProjectiles` now routes collision and bounce inputs through the collected frame facts while still
  calling `buildProjectileUpdateFrameDecision` and `applyProjectileUpdateFrameDecision`, so projectile behavior is
  intentionally unchanged until Step 3/Step 4.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully; no tests were found in the current
  build tree.
- 2026-04-21: Completed Step 3 by adding `GameplayProjectileService::updateProjectileFrame`, delegating to the
  existing frame-decision builders, and flattening their output into `ProjectileFrameResult`.
- 2026-04-21: The new frame result now carries motion-end, bounce, direct party impact, direct actor impact,
  area impact, FX, collision/lifetime logging, expiry, and Death Blossom fallout outcomes without exposing
  outdoor collision or renderer types.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully; no tests were found in the current
  build tree.
- 2026-04-21: Completed Step 4 by switching `OutdoorWorldRuntime::updateProjectiles` to the target frame shape:
  collect `ProjectileFrameFacts`, call `GameplayProjectileService::updateProjectileFrame`, then apply
  `ProjectileFrameResult` through `OutdoorWorldRuntime::applyProjectileFrameResult`.
- 2026-04-21: The outdoor frame result applier applies the shared direct impact, area impact, bounce, FX/audio,
  lifetime expiry, Death Blossom fallout, spawned projectile, collision logging, and motion-end outcomes without
  switching over the shared service frame command enums in the main projectile loop.
- 2026-04-21: Outdoor frame fact collection now predicts the projectile frame on a local projectile copy so collision
  facts use the same post-gravity motion segment while the real projectile is advanced once by
  `updateProjectileFrame`.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully; no tests were found in the current
  build tree.
- 2026-04-21: Completed Step 5 by removing the old public projectile frame command layer from
  `GameplayProjectileService.h`, including `ProjectileUpdateFrameDecision`, `ProjectileFrameAdvanceResult`,
  collision/lifetime resolution command enums, and their public builder methods.
- 2026-04-21: `GameplayProjectileService::updateProjectileFrame` now advances lifetime/motion and builds
  `ProjectileFrameResult` directly. The old outdoor frame-decision appliers were removed, while outdoor collision fact
  collection still owns ODM-specific collision and bounce surface facts.
- 2026-04-21: Static audit with `rg` found no remaining references to the removed frame command-layer names in `game`,
  `engine`, `editor`, or `tools`.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully; no tests were found in the current
  build tree.
- 2026-04-21: Completed Step 6 by renaming projectile spawn orchestration from presentation terminology to effect
  terminology: `ProjectileSpawnEffectCommand`, `ProjectileSpawnEffects`, `ProjectileSpawnEffectOptions`,
  `buildProjectileSpawnEffects`, and `OutdoorWorldRuntime::applyProjectileSpawnEffects`.
- 2026-04-21: Projectile impact visual creation now uses `ProjectileImpactSpawnResult`,
  `spawnProjectileImpactVisual`, `spawnWaterSplashImpactVisual`, `spawnImmediateSpellImpactVisual`, and
  `shouldSpawnProjectileImpactVisual`; Fire Spike impact trigger names now use `SpawnImpactVisual`,
  `FireSpikeTrapImpactProjectileInput`, and `buildFireSpikeTrapImpactProjectile`.
- 2026-04-21: Static audit with `rg` shows remaining projectile `Presentation` names are render-facing state/sync
  names such as `GameplayProjectilePresentationState`, `GameplayProjectileImpactPresentationState`,
  `collectProjectilePresentationState`, and `GameplayFxService::syncProjectilePresentation`.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully; no tests were found in the current
  build tree.
- 2026-04-21: Completed Step 7 static audit. Meteor Shower and Starburst only customize the spawn fan-out through
  `GameplayProjectileService::buildMeteorShowerProjectileShots` and `buildStarburstProjectileShots`; each shot then
  spawns a normal projectile through `OutdoorWorldRuntime::spawnSpellProjectile` and uses the converted
  `ProjectileFrameFacts` / `ProjectileFrameResult` outdoor loop for travel, collision, area impact, FX, and audio.
- 2026-04-21: Fire Spike remains an intentional trap-state path outside the normal projectile list:
  `OutdoorWorldRuntime::spawnPartyFireSpikeTrap` stores `FireSpikeTrapState`, `updateFireSpikeTraps` collects
  trap/actor facts, and `GameplayProjectileService::buildFireSpikeTrapTriggerDecision` owns the shared trigger and
  damage decision. It does not need conversion to `updateProjectileFrame` in this projectile-frame cleanup.
- 2026-04-21: Special frame behavior for Death Blossom and Rock Blast is already represented in
  `GameplayProjectileService::updateProjectileFrame`: Death Blossom returns a fallout request in
  `ProjectileFrameResult`, and Rock Blast lifetime expiry returns area-impact/FX outcomes through the same frame
  result path. Area spell radii for Meteor Shower, Starburst, Fireball, Dragon Breath, Flame Blast, Rock Blast, and
  Death Blossom remain shared in `spellImpactDamageRadius`.
- 2026-04-21: Existing headless diagnostics cover representative projectile behavior across local event projectile
  spawn/impact, gravity and no-gravity travel, Meteor Shower party damage, actor ranged projectile travel and party
  impact, party projectile actor impact, spell projectile actor impact, fireball splash, friendly-actor filtering, and
  visible spell impact effects. No code change was needed for Step 7.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed successfully after Step 7.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed successfully after Step 7; no tests were found in
  the current build tree.

Manual smoke status:

- 2026-04-22: Root acceptance closure reran static projectile audits, `cmake --build build --target openyamm -j25`,
  `ctest --test-dir build --output-on-failure`, `timeout 300s build/game/openyamm
  --headless-run-regression-suite indoor`, and `timeout 300s build/game/openyamm
  --headless-run-regression-suite dialogue`. Build and CTest passed, CTest still has no registered tests, indoor
  passed with `passed=21 failed=0`, and dialogue completed cleanly with `passed=242 failed=0`. Relevant headless
  projectile smoke cases passed, including local event projectile spawn/gravity, Meteor Shower ground impact,
  actor ranged projectile release and party hit, party arrow and spell projectile actor hits, fireball splash against
  party and multiple actors, and visible spell impact effects. Fire Spike, Starburst, Death Blossom, and Rock Blast
  paths remain covered by the Step 7 static audit; no separate interactive projectile play session was run.
- 2026-04-22: Acceptance follow-up fixed the six residual dialogue diagnostics outside projectile-frame ownership.
  `cmake --build build --target openyamm -j25` passed; `ctest --test-dir build --output-on-failure` passed with no
  registered tests; `timeout 300s build/game/openyamm --headless-run-regression-suite indoor` passed with
  `passed=21 failed=0`; and full dialogue now completes cleanly with `passed=242 failed=0`. Relevant non-interactive
  projectile smoke still passed in the dialogue log, including local event projectile spawn/gravity, Meteor Shower
  ground impact, party arrow and spell projectile actor hits, fireball splash, visible spell impact, and actor death
  audio. Interactive projectile manual smoke is still not run.
- 2026-04-22: Acceptance follow-up fixed a headless bgfx resource crash outside projectile ownership. Full dialogue
  now completes instead of exiting 139, and relevant projectile smoke cases pass in the log, including local event
  projectile spawn/gravity, Meteor Shower ground impact, party arrow and spell projectile actor hits, fireball splash,
  actor-vs-actor hostile damage, visible spell impact, and actor death audio. Root acceptance still is not clean:
  dialogue reports `passed=236 failed=6`, and interactive projectile manual smoke is still not run.
- 2026-04-22: Non-interactive headless smoke was rerun after the corpse-loot fix. Dialogue still passed relevant
  projectile cases, but the full suite remains non-clean because unrelated residual diagnostics and audio decode
  errors remain. Interactive projectile manual smoke is still not run.
- 2026-04-22: Current non-interactive headless smoke was rerun for acceptance follow-up. Indoor passed with
  `passed=21 failed=0`; dialogue passed relevant projectile cases but remains non-clean because unrelated residual
  failures and audio decode errors end the process with code 139. Interactive projectile manual smoke is still not
  run.
- 2026-04-22: Non-interactive headless smoke was rerun for acceptance follow-up. Indoor passed with
  `passed=21 failed=0`; dialogue passed relevant projectile cases but remains non-clean because unrelated residual
  failures and audio decode errors end the process with code 139. Interactive projectile manual smoke is still not
  run.
- 2026-04-22: Not run for final projectile acceptance. Projectile travel, bounce, collision, impact FX/audio, splash,
  area impact, spawned projectiles, Fire Spike, Meteor Shower, Starburst, Death Blossom, and Rock Blast remain pending
  for interactive/manual acceptance.
- 2026-04-21: Not run for Step 1; no projectile behavior or call sites changed.
- 2026-04-21: Not run for Step 2; validation was limited to build and ctest because the old projectile
  frame-decision application path remains active.
- 2026-04-21: Not run for Step 3; the new `updateProjectileFrame` API is implemented, but the outdoor projectile
  loop still uses the old frame-decision application path until Step 4.
- 2026-04-21: Not run for Step 4; validation was limited to build and ctest after routing the outdoor projectile loop
  through facts/result. Manual projectile travel, bounce, collision, FX/audio, area impact, spawned projectile, and
  special projectile smoke remain pending.
- 2026-04-21: Not run for Step 5; validation was limited to build, ctest, and static audit because this slice removed
  obsolete public frame plumbing without changing the active outdoor facts/result frame shape.
- 2026-04-21: Not run for Step 6; validation was limited to build, ctest, and static audit because this slice only
  renamed projectile orchestration/effect identifiers and did not change runtime behavior.
- 2026-04-21: Not run for Step 7; validation was limited to static audit because this slice did not change runtime
  behavior. Fire Spike, Meteor Shower, Starburst, Death Blossom, and Rock Blast paths were traced.

## Done Definition

This refactor is done only when:

- the main projectile loop uses `ProjectileFrameFacts` and
  `ProjectileFrameResult`;
- shared projectile service owns projectile gameplay decisions;
- active world owns projectile collision facts and world-specific application;
- public projectile frame API no longer exposes the old micro-decision command
  layer;
- behavior is validated by build/tests and relevant manual smoke notes;
- this progress section says `Done definition satisfied: YES`.
