# Control Schemes Settings Implementation Plan

## Goal

Add two gameplay control schemes without new UI art:

- `modern`: current OpenYAMM mouse-look style.
- `classic`: OE-like cursor style.

The first implementation is settings-driven through `settings.ini` and uses the existing keyboard configuration
screen with minimal text/layout changes. It does not add new UI screens or image assets.

## User-Facing Behavior

### Modern Scheme

Modern is the current OpenYAMM-style scheme:

- Mouse look is active during normal gameplay.
- Crosshair is rendered while mouse look is active.
- Cursor is hidden during normal gameplay.
- RMB temporarily enters cursor mode / pointer interaction mode, as it works now.
- LMB attacks from the crosshair target.
- `E` activates the current mouse/crosshair world target.
- `Space` remains the separate keyboard trigger path.
- `W/S` move forward/back.
- `A/D` strafe left/right.

Default input bindings:

```ini
[controls]
control_scheme=modern

[input]
forward=W
backward=S
left=A
right=D
attack=MouseLeft
use=E
trigger=Space
```

### Classic Scheme

Classic is the OE-like scheme:

- Mouse look is disabled during normal gameplay.
- Crosshair is not rendered.
- Cursor remains visible and movable.
- RMB is OE-style inspect/info popup behavior, not cursor-mode switching.
- LMB activates the clicked world target.
- `A` attacks.
- `Space` remains the separate keyboard trigger path.
- `Up/Down` move forward/back.
- `Left/Right` turn left/right.
- Optional strafe keys can remain hidden or be added later; OE default strafe is `[` / `]`.

Default input bindings:

```ini
[controls]
control_scheme=classic

[input]
forward=Up
backward=Down
left=Left
right=Right
attack=A
use=MouseLeft
trigger=Space
```

## Input Concepts

Keep `Trigger` and `Use` distinct:

- `Trigger` is the current keyboard interaction path and uses `pickKeyboardInteractionTarget(...)`.
- `Use` is the mouse/current-target activation path and uses `pickMouseInteractionTarget(...)`.

This distinction matters because `Space` and LMB/E do not currently do exactly the same thing.

## Keyboard Screen Changes

No new UI images are required.

- Replace the visible `Auto Notes` binding with `Use`.
- Put `Use` on page 1 near movement, `Attack`, and `Trigger`.
- Keep `Trigger` visible and named `Trigger` for now, because it is behaviorally distinct from `Use`.
- `AutoNotes` can either:
  - remain as an internal action with its old INI key but hidden from the keyboard screen, or
  - be removed from the visible binding definitions and left unbound until a later UI pass.

Recommended first pass:

- Rename `KeyboardAction::AutoNotes` to `KeyboardAction::Use` only if migration impact is small.
- Otherwise keep enum stability by replacing the definition entry currently using `AutoNotes` with label `Use`,
  ini key `use`, and behavior mapped to the new use action. This avoids enum-order churn.
- Move `Use` to `KeyboardBindingPage::Page1`, `KeyboardBindingColumn::Right`, near `Attack` and `Trigger`.
- Move lower-priority page 1 rows only as needed to avoid overlap.

## Settings Model

Add:

```cpp
enum class ControlScheme
{
    Modern,
    Classic
};
```

Store it in `GameSettings`:

```cpp
ControlScheme controlScheme = ControlScheme::Modern;
```

Persist in `settings.ini`:

```ini
[controls]
control_scheme=modern
```

Accepted values:

- `modern`
- `classic`

Invalid or missing value falls back to `modern`.

## Binding Model

The existing binding model only stores `SDL_Scancode`. To support `MouseLeft`, introduce a small input binding type:

```cpp
enum class InputBindingKind : uint8_t
{
    None,
    Keyboard,
    MouseButton
};

struct InputBinding
{
    InputBindingKind kind = InputBindingKind::None;
    SDL_Scancode scancode = SDL_SCANCODE_UNKNOWN;
    uint8_t mouseButton = 0;
};
```

Supported serialized names for this pass:

- Existing keyboard names such as `A`, `Space`, `Left`, `Right`.
- `MouseLeft`.
- Optionally parse `LMB` as an alias, but write `MouseLeft`.

Scope for mouse bindings:

- `Attack` accepts `MouseLeft`.
- `Use` accepts `MouseLeft`.
- Other actions may remain keyboard-only initially unless the parser generalization makes support trivial.

To reduce INI churn, either:

- Keep the section name `[keyboard]` for compatibility and allow mouse names there, or
- Add `[input]` and read both `[input]` and `[keyboard]`, with `[input]` taking precedence.

Recommended first pass:

- Read `[input]` first, then fall back to `[keyboard]`.
- Continue writing `[input]`.
- Optionally also keep writing `[keyboard]` only if older tools depend on it.

## Runtime Behavior Changes

### Mouse Look Policy

Current behavior is effectively modern. Add scheme gating:

- `modern`: existing `updateGameplayMouseLookPolicy(...)` behavior.
- `classic`: force `mouseLookActive=false`, `cursorModeActive=true` or equivalent cursor-visible state, and do not render
  the crosshair.

Implementation locations:

- `game/gameplay/GameplayInputController.cpp`
- `game/app/GameSession.cpp`
- `game/outdoor/OutdoorGameView.cpp`
- `game/indoor/IndoorRenderer.cpp`

### RMB Semantics

Modern:

- Keep current RMB cursor-mode behavior.

Classic:

- RMB should not toggle cursor mode because the cursor is already active.
- RMB should run OE-like inspect/info behavior while held.
- Reuse existing right-click inspect overlay paths where possible.
- Keep right-click from triggering `Use` or `Attack`.

Implementation locations:

- `GameplayInputController::updateGameplayMouseLookPolicy(...)`
- `GameplayScreenController` / `GameplayInteractionController` inspect handling
- UI overlay inspect rendering paths in `game/ui/GameplayHudOverlaySupport.cpp`

### LMB Semantics

Modern:

- `MouseLeft` bound to `Attack` by default.
- While mouse look is active and RMB is not held, LMB attacks from the center/crosshair target.

Classic:

- `MouseLeft` bound to `Use` by default.
- LMB activates the clicked world target using the mouse interaction path.

Implementation locations:

- `game/app/GameInputSystem.cpp`: map mouse button state into action state for bindings.
- `game/gameplay/GameplayInteractionController.cpp`: consume `Use` action through the current mouse activation path.
- Preserve HUD/menu overlay priority so UI clicks are not treated as world actions.

### Left/Right Movement Semantics

Short-term, keep the existing `Left` and `Right` actions but resolve them based on scheme:

- `modern`: `Left` / `Right` are strafe left/right.
- `classic`: `Left` / `Right` are turn left/right.

Long-term, split this into explicit actions:

- `TurnLeft`
- `TurnRight`
- `StrafeLeft`
- `StrafeRight`

Do not do the split in the first pass unless the implementation is already touching enough movement code to justify it.

Implementation locations:

- `game/outdoor/OutdoorGameplayInputController.cpp`
- `game/indoor/IndoorRenderer.cpp`

Indoor currently has hardcoded `W/A/S/D` movement checks. Convert it to action checks as part of this work so settings
affect indoor and outdoor consistently.

## File-Level Work Plan

1. `game/app/GameSettings.h`
   - Add `ControlScheme`.
   - Add `controlScheme` setting.
   - Change keyboard binding storage to input binding storage or add input binding alongside keyboard binding.

2. `game/app/GameSettings.cpp`
   - Parse and write `control_scheme`.
   - Parse and write `MouseLeft`.
   - Read `[input]` with fallback to `[keyboard]`.
   - Apply scheme defaults when no explicit binding exists.

3. `game/app/KeyboardBindings.h/.cpp`
   - Replace visible `Auto Notes` row with `Use`.
   - Put `Use` on page 1 near `Attack` and `Trigger`.
   - Add display text for `MouseLeft`.
   - Keep existing key display names stable.

4. `game/app/GameInputSystem.cpp`
   - Populate action state from keyboard bindings and mouse button bindings.
   - Make `MouseLeft` action state use `leftMouseButton`.
   - Preserve raw `leftMouseButton` and `rightMouseButton` for UI and overlays.

5. `game/gameplay/GameplayInputController.cpp`
   - Gate mouse-look policy by `settings.controlScheme`.
   - Classic: no mouse-look/crosshair mode.
   - Modern: current policy.

6. `game/gameplay/GameplayInteractionController.cpp`
   - Add `Use` action handling.
   - Route `Use` to the current mouse activation path, not the keyboard trigger path.
   - Keep `Trigger` routed through `pickKeyboardInteractionTarget(...)`.
   - Ensure `Attack=MouseLeft` and `Use=MouseLeft` are mutually sane by scheme defaults and do not both fire unless the
     user explicitly creates a conflicting custom binding.

7. `game/outdoor/OutdoorGameplayInputController.cpp`
   - Interpret `Left`/`Right` as strafe in modern and turn in classic.
   - Ensure classic cursor mode does not block movement.

8. `game/indoor/IndoorRenderer.cpp`
   - Replace hardcoded `SDL_SCANCODE_W/A/S/D/X` movement checks with action checks where appropriate.
   - Apply the same left/right semantic split as outdoor.

9. `game/app/GameSession.cpp`
   - Use control scheme for crosshair render decision.
   - Ensure classic does not render gameplay mouse-look overlay.

10. Tests / verification
    - Add unit tests for input binding parsing and display names.
    - Add settings load/save tests for `control_scheme` and `MouseLeft`.
    - Add focused runtime tests or scenario-driver checks:
      - modern default: LMB attacks, E uses, RMB enters cursor mode.
      - classic default: LMB uses clicked target, A attacks, RMB inspects, arrows move/turn.
      - indoor and outdoor both honor scheme movement semantics.

## Compatibility Notes

- Existing settings without `control_scheme` should behave like `modern`.
- Existing `[keyboard]` bindings should keep loading.
- If the user has an old `auto_notes=N` entry, it should not break parsing. It can be ignored or mapped only if Auto Notes
  returns in a later UI pass.
- Conflicting custom binds, such as `attack=MouseLeft` and `use=MouseLeft`, should be allowed but deterministic. Prefer
  documenting that the scheme defaults avoid conflicts, while custom conflicts follow action processing order.

## Non-Goals For First Pass

- No new UI art.
- No new controls screen layout.
- No fully general multi-bind-per-action support.
- No gamepad scheme work.
- No removal of the underlying `Trigger` behavior.
- No direct copy from OpenEnroth; OE remains a behavior reference only.
