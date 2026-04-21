# Indoor/Outdoor Shared Gameplay Runtime Boundary Plan

This document is the single authoritative refactor target for indoor/outdoor
shared gameplay.

Do not treat older slice plans as authoritative. They are historical context
only. This document defines the state the codebase must reach.

## Goal

OpenYAMM should have one shared gameplay runtime that owns input semantics,
gameplay decisions, UI/screens, party actions, item flow, spell flow, combat
rules, and shared presentation. Indoor and outdoor should only provide the
active world representation.

The final frame should read structurally like this:

```cpp
void GameApplication::renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    m_gameInputSystem.updateFromEngineInput(width, height, mouseWheelDelta);

    m_gameSession.updateGameplay(m_gameInputSystem.frame(), deltaSeconds);

    if (IGameplayWorldRuntime *pWorld = m_gameSession.activeWorldRuntime())
    {
        pWorld->renderWorld(width, height, deltaSeconds);
    }

    m_gameSession.gameplayUiRuntime().render(width, height);
}
```

Names may change. Ownership must not.

## Non-Negotiable Ownership Rule

Shared gameplay owns what should happen.

The active world owns what exists in the current world representation and how
to apply world-specific effects to that representation.

`OutdoorGameView`, `IndoorGameView`, and world renderers must not own shared
gameplay semantics.

## Current Problem To Eliminate

The current code still contains transitional wiring:

- outdoor and indoor sample or pass raw input into shared gameplay;
- `OutdoorGameView::render` assembles large callback structures;
- shared gameplay receives callbacks for facts it should pull from
  `GameSession` directly;
- shared gameplay receives callbacks for world operations that should be direct
  calls through the active world seam;
- `IGameplayWorldRuntime` exists, but it is not yet the cohesive active-world
  interaction/render boundary.

This must be replaced, not hidden behind smaller adapter layers.

## Target Runtime Ownership

### `GameApplication`

Owns app shell responsibilities:

- SDL/window/frame bootstrap;
- renderer/audio bootstrap;
- selected active screen fallback;
- `GameInputSystem` update from engine/SDL input;
- high-level call order only.

`GameApplication` should not branch into separate indoor/outdoor gameplay
flows. It may select/bind the active world runtime.

### `GameInputSystem`

Owns input sampling once per frame:

- SDL keyboard state;
- SDL mouse buttons;
- SDL pointer position;
- SDL relative mouse motion;
- mouse wheel;
- keybind resolution;
- pressed/released/held edge state;
- shared repeat/cadence primitives where they are input-level facts.

It produces a semantic `GameplayInputFrame`.

Indoor/outdoor code must not call `SDL_GetKeyboardState`,
`SDL_GetMouseState`, or `SDL_GetRelativeMouseState` for shared gameplay
actions.

World-specific debug camera shortcuts may remain world-specific until the
debug path is cleaned separately, but they must not participate in gameplay
semantics.

### `GameplaySession`

Owns shared gameplay state:

- party state;
- active world pointer;
- `GameDataRepository`;
- gameplay screen/modal state;
- gameplay UI runtime/controller;
- overlay interaction state;
- held item cursor state;
- pending spell targeting state;
- quick-cast and attack-cast state;
- shared gameplay services/controllers;
- shared status text and inspect state.

`GameplaySession::updateGameplay(const GameplayInputFrame &, float)` is the
shared gameplay frame entry point.

### Shared Gameplay Controllers And Services

Shared gameplay owns decisions for:

- UI/modal input gating;
- mouse-look and cursor-mode policy;
- LMB/RMB gameplay semantics;
- Space/E/mouse activation ordering;
- quick cast;
- attack cast;
- pending targeted spell confirmation/cancel;
- held-LMB and quick-cast repeat cadence;
- party attack execution;
- combat speech/status;
- item cursor and inventory transfer rules;
- dialogue/chest/shop/rest/menu/journal/spellbook behavior;
- spell legality, failure text, and spell action orchestration;
- shared projectile/FX/decal request ownership;
- high-level monster AI and combat decision rules.

Shared gameplay may ask the active world for facts or command world-specific
application, but it must not ask `OutdoorGameView` or `IndoorGameView` to make
gameplay decisions.

### `IGameplayWorldRuntime`

This is the active world seam. It should be cohesive and world-meaningful.

The interface should converge toward this shape:

```cpp
class IGameplayWorldRuntime
{
public:
    virtual ~IGameplayWorldRuntime() = default;

    virtual SceneKind sceneKind() const = 0;
    virtual const std::string &mapName() const = 0;

    virtual GameplayWorldPose partyWorldPose() const = 0;
    virtual void updateWorldMovement(const GameplayInputFrame &input, float deltaSeconds) = 0;

    virtual GameplayWorldPickResult pickWorld(const GameplayWorldPickRequest &request) = 0;
    virtual GameplayPendingSpellTargetFacts pickPendingSpellTarget(
        const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickKeyboardInteractionTarget() = 0;

    virtual bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod method) const = 0;
    virtual bool activateWorldHit(const GameplayWorldHit &hit) = 0;

    virtual bool canUseHeldItemOnWorld(const GameplayWorldHit &hit) const = 0;
    virtual bool useHeldItemOnWorld(const GameplayWorldHit &hit) = 0;
    virtual bool dropHeldItemToWorld(const GameplayHeldItemDropRequest &request) = 0;

    virtual GameplayPartyAttackWorldFacts buildPartyAttackWorldFacts(
        const GameplayPartyAttackWorldQuery &query) = 0;
    virtual void applyPartyAttackWorldCommand(
        const GameplayPartyAttackWorldCommand &command) = 0;

    virtual void applyPendingSpellWorldEffects(const PartySpellCastResult &result) = 0;

    virtual bool tryGetGameplayMinimapState(GameplayMinimapState &state) const = 0;
    virtual void collectGameplayMinimapMarkers(
        std::vector<GameplayMinimapMarkerState> &markers) const = 0;

    virtual void updateWorld(float deltaSeconds) = 0;
    virtual void renderWorld(int width, int height, float deltaSeconds) = 0;
};
```

Exact type names may differ. The important part is that shared gameplay calls
the active world directly through cohesive world methods, not through a per-frame
bag of lambdas.

If this interface grows too large, split it by real world responsibility:

- `IGameplayWorldPicking`;
- `IGameplayWorldInteraction`;
- `IGameplayWorldCombat`;
- `IGameplayWorldMovement`;
- `IGameplayWorldRendering`.

Do not split it into callback bags owned by the views.

## What Shared Gameplay Must Pull Directly

Do not pass callbacks for data already owned by shared gameplay:

- party;
- game data tables;
- current UI/screen state;
- overlay interaction latches;
- held item cursor;
- pending spell state;
- quick-cast and attack-cast state;
- status text;
- inspect popup state;
- gameplay UI runtime;
- spell service;
- item service;
- combat/action controllers.

These belong in `GameplaySession` or shared controllers/services.

## What The Active World Must Provide

The active world provides only world facts and world application:

- cursor/crosshair ray construction for the current world representation;
- actor/deco/world item/event-face picking;
- keyboard interaction picking;
- terrain/floor/sector/bmodel/BLV hit facts;
- LOS and visibility checks;
- map event and mechanism activation;
- actor world positions and world actor application;
- world item placement/drop position;
- projectile collision against world geometry;
- decal placement onto terrain/faces;
- world rendering;
- minimap extraction from world data.

Outdoor and indoor may differ here. They must not differ in gameplay decision
flow.

## What Views Should Become

### `OutdoorGameView`

Final responsibility:

- outdoor bgfx resource ownership if still needed there;
- outdoor geometry/camera/render state;
- outdoor world-specific debug render state;
- a thin render-world implementation or owner of `OutdoorWorldRuntime` rendering.

It must not own:

- HUD rendering;
- UI input;
- keybind handling;
- mouse-look policy;
- quick/attack cast;
- party attack decisions;
- held-item semantics;
- pending spell flow;
- chest/dialogue/shop/menu/rest/spellbook behavior.

### `IndoorGameView`

Final responsibility:

- indoor bgfx resource ownership if still needed there;
- BLV render state;
- sector/portal/mechanism render state;
- indoor world-specific debug render state;
- a thin render-world implementation or owner of `IndoorWorldRuntime` rendering.

It must not own the shared systems listed for `OutdoorGameView`.

## Refactor Phases

These phases are the executable direction. Do not execute old plans linearly.

### Phase 1: Introduce `GameInputSystem`

Requirements:

- add a shared input frame type;
- sample SDL input once per frame outside indoor/outdoor views;
- resolve keybinds into semantic fields;
- preserve mouse pointer, relative mouse, wheel, pressed, released, and held
  state;
- route existing shared UI/gameplay input from this frame.

Acceptance:

- no shared gameplay action path samples SDL input from `OutdoorGameView`,
  `IndoorGameView`, or `OutdoorGameplayInputController`;
- indoor and outdoor receive the same semantic input frame.

### Phase 2: Add `GameplaySession::updateGameplay`

Requirements:

- create one shared per-frame gameplay update entry point;
- move shared input/UI/modal gating into it;
- move shared world interaction update into it;
- move shared quick-cast, attack-cast, attack cadence, and pending spell update
  into it.

Acceptance:

- `GameApplication::renderFrame` calls `GameInputSystem`, then
  `GameSession::updateGameplay`;
- views do not call `GameplayInputController::updateSharedGameplayInputFrame`.

### Phase 3: Replace `WorldInteractionFrameInput` Callback Bag

Requirements:

- remove the large per-frame callback input from
  `GameplayInteractionController`;
- shared gameplay gets session-owned state directly from `GameSession`;
- shared gameplay gets world facts/application through
  `GameSession::activeWorldRuntime()`;
- no callback should exist merely to retrieve party/UI/state already owned by
  gameplay.

Acceptance:

- `OutdoorGameView::render` no longer assembles interaction lambdas;
- `IndoorGameView::render` no longer assembles no-op interaction lambdas;
- shared interaction code calls active-world methods directly.

### Phase 4: Move Outdoor Callback Bodies Into The Active World

Requirements:

- convert outdoor ray/pick/activation/held-item/drop/party-attack world code
  into `OutdoorWorldRuntime` or cohesive outdoor world services;
- keep `OutdoorInteractionController` only if it is a world implementation
  helper, not a gameplay orchestration layer;
- preserve outdoor behavior.

Acceptance:

- outdoor world methods satisfy the active-world seam;
- no shared controller includes outdoor headers;
- `OutdoorGameView` does not compose gameplay behavior.

### Phase 5: Implement Indoor World Seam

Requirements:

- provide indoor pick/raycast facts;
- provide indoor keyboard interaction target selection;
- provide indoor activation application;
- provide indoor held-item world use/drop;
- provide indoor pending spell target facts and spell FX application;
- provide indoor party attack world facts/application.

Acceptance:

- indoor gameplay uses the same shared decisions as outdoor;
- indoor differences are limited to BLV geometry, sectors, mechanisms,
  collision, LOS, and rendering.

### Phase 6: Move World Rendering Behind Active World

Requirements:

- add `renderWorld` and `updateWorld` to the active-world boundary;
- make `GameApplication::renderFrame` call the active world directly;
- keep shared UI rendering after world rendering.

Acceptance:

- `GameApplication` no longer branches into `m_outdoorGameView.render` vs
  `m_indoorGameView.render` for gameplay flow;
- world rendering is selected by the active world.

### Phase 7: Continue Shared-System Extraction Under This Boundary

Once the frame/input/world boundary is in place, continue moving remaining
shared systems under `GameplaySession`:

- UI rendering and all `.yml` gameplay screens;
- inventory, identify, repair, enchant, scroll use;
- dialogue, shops, houses, chests, rest, journal, save/load screens;
- spell/projectile/particle ownership;
- actor high-level AI and combat rules;
- static data ownership in `GameDataRepository`.

Acceptance:

- shared systems are called by `GameplaySession`;
- active world only supplies facts/application;
- no new indoor/outdoor gameplay duplication is introduced.

## Immediate Audit Checklist

Before each implementation slice, check:

- Does this logic decide what gameplay should do? Put it in shared gameplay.
- Does this logic query or mutate ODM/BLV geometry/world representation? Put it
  behind active world.
- Is this just passing a lambda from a view to shared gameplay? Prefer a direct
  active-world method or direct `GameSession` state access.
- Is this data already owned by `GameSession`? Do not pass it through callbacks.
- Would indoor and outdoor need the same behavior? Then it must not live in
  either view.

## Validation

Run after each meaningful slice:

```bash
cmake --build build --target openyamm -j25
ctest --test-dir build --output-on-failure
```

Manual smoke tests to record when relevant:

- LMB attack cadence;
- quick cast with and without target;
- quick cast with no assigned spell falling back to attack;
- attack-cast substitution;
- pending targeted spells;
- Meteor Shower / Starburst ground targeting;
- chest open with Space does not pick an item;
- held item transfer to party portraits;
- dialogue/chest/shop overlay input;
- indoor/outdoor mouse-look and RMB cursor mode;
- indoor/outdoor world activation.

## Done Definition

This refactor is done only when:

- `GameApplication::renderFrame` follows the target frame shape;
- gameplay input is sampled outside indoor/outdoor;
- `GameplaySession::updateGameplay` is the shared gameplay update entry point;
- shared gameplay owns all shared decisions;
- active world owns all world facts/application;
- `OutdoorGameView` and `IndoorGameView` no longer wire gameplay behavior;
- no giant callback bag replaces view ownership;
- indoor and outdoor use the same shared gameplay flow;
- `PROGRESS.md` records validation and contains `## Done definition satisfied: YES`.
