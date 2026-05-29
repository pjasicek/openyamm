# ARPG Mode Interaction Backport Candidates

This document tracks ARPG-mode changes that may be worth backporting to main after the ARPG work is moved to a branch.
The goal is to keep main focused on modern first-person/MAW-style interaction while selectively retaining fixes that
improve shared indoor/outdoor popup interaction.

## Backport Goal

Extract reusable interaction behavior without carrying ARPG camera, click-to-move, loot labels, player-monster rendering,
or mode-specific gameplay branches into main.

Preferred shape:

- rename ARPG-specific helpers to neutral context-action names;
- keep the behavior behind existing `contextActionPopup` / first-person interaction settings;
- avoid adding `arpgMode` checks to shared gameplay paths;
- use one shared target selection policy for hover, popup display, and activation.

## Refined Main Backport Scope

The current target for main is first-person/crosshair context interaction, not ARPG proximity interaction.

Backport the pieces that make the popup and `E` activation agree with the thing the player is facing:

- exact crosshair/precision target first;
- forward-facing fallback second;
- optional visible-popup activation before recomputing a new target;
- indoor/outdoor line-of-sight validation for fallback popup candidates;
- indoor event-face filtering and geometry highlight fixes so only real activatable event faces are shown.

Do not backport the ARPG 360-degree nearby target bubble as-is. If a fallback is needed, it should be constrained by the
current first-person/crosshair direction and `keyboardInteractionDepth`, not by "anything near the party".

## High-Value Candidates

### 1. Forward/Precision Context Action Picking

Current ARPG work adds generic target APIs:

- `IGameplayWorldRuntime::pickNearbyInteractionTarget(float radius)`
- `IGameplayWorldRuntime::pickForwardInteractionTarget(float depth)`
- indoor implementation via `IndoorRenderer::pickNearbyGameplayWorldHit`
- outdoor implementation via `OutdoorInteractionController::pickNearbyInteractionTarget`

Why keep it:

- popup interaction should not require pixel-perfect hits when the crosshair is clearly aimed at an interactable face;
- first-person context actions should prefer the exact crosshair target, then fall back only along the facing direction;
- this helps both indoor and outdoor maps without importing ARPG proximity behavior.

Backport notes:

- rename from ARPG framing to neutral context-action naming;
- keep distance clamping based on `keyboardInteractionDepth`;
- prefer `pickMouseInteractionTarget` / exact crosshair hit first;
- use `pickForwardInteractionTarget` as the fallback;
- do not use the ARPG `pickNearbyInteractionTarget` 360-degree scan as the main popup source;
- validate activatability through `canActivateWorldHit`;
- add line-of-sight validation before accepting fallback candidates.

### 2. Activate The Visible Context Action First

ARPG interaction activation uses the currently visible popup action before recomputing a new target.

Why keep it:

- prevents "popup says one thing, key activates another thing";
- makes keyboard/use activation predictable;
- works for first-person interaction as well as ARPG.

Backport notes:

- when context action state has a valid primary action, activate its stored `worldHit`;
- only fall back to precision/forward/nearby picking when no visible action exists;
- keep existing latches so holding the use key does not repeatedly activate.

### 3. Precision Target Takes Precedence

ARPG work adds a helper that tries exact mouse/crosshair picking first, validates activation, then falls back to keyboard
interaction picking.

Why keep it:

- important for mobile and crosshair interaction: if the player points directly at an interactable face, the popup and
  `E` should use that face;
- reduces dead input around tiny event faces without making unrelated nearby objects steal interaction.

Backport notes:

- rename `pickArpgModePrecisionInteractionTarget` to a neutral helper;
- make it choose between current mouse/crosshair hit and forward-facing fallback;
- keep `canActivateWorldHit(..., GameplayInteractionMethod::Keyboard)` as the validator.

### 4. Indoor Event Face Filtering

ARPG work added better indoor checks around event faces and mechanisms:

- detect whether a face's event id actually exists in local/global scripts;
- ignore hint-only events for context actions;
- use context-action metadata and opened chest ids for labels/icons;
- suppress bad popup/highlight targets such as ceilings, floors, open/opening door mechanisms, and non-relevant door
  faces.

Why keep it:

- first-person popup highlighting is also vulnerable to fake/irrelevant event faces;
- prevents context action popups on ceiling/floor surfaces or inactive mechanism parts;
- improves indoor chest/door/button labeling without being ARPG-specific.

Backport notes:

- rename helpers such as `indoorFaceSuppressedForArpgContextAction` and
  `indoorDoorMechanismSuppressesArpgContextAction`;
- audit the suppression rules before applying globally, especially the chest exception;
- use the same filters in both context action picking and geometry highlight rendering.

### 5. Line-Of-Sight And Range Validation

ARPG work applies stronger validation before keyboard/context activation:

- indoor fallback hits can be checked with indoor world-hit line of sight;
- outdoor fallback hits can be checked with `hasClearOutdoorLineOfSight`;
- ARPG-specific distance checks should become regular context-action distance checks.

Why keep it:

- prevents popup/key activation through walls or closed geometry;
- makes forward fallback safer for first-person mode.

Backport notes:

- make LOS validation a neutral context-action validator;
- apply it to forward/fallback popup targets, not necessarily to exact mouse hover if that path already intersects the
  visible surface;
- be careful with doors/mechanisms, where the clickable face may be part of the occluding geometry.

## Medium-Value Candidates

### 6. Context Action Metadata Resolution

Indoor and outdoor code now resolves `ScriptedEventProgram::ContextActionMetadata` into gameplay context action metadata.

Why keep it:

- better labels/icons for enter house, open chest, open door, press button, use lever, and generic events;
- useful for main regardless of camera mode.

Backport notes:

- keep metadata resolution in world-specific interaction code;
- preserve fallback labels when metadata is missing;
- avoid coupling metadata to ARPG naming.

### 7. Popup Geometry Highlight Improvements

Indoor rendering now highlights selected context action world hits across event faces, doors, entities, actors, and items.
Outdoor rendering already has related context action geometry highlight support.

Why keep it:

- improves "what will Use activate?" clarity;
- useful for first-person context action popup.

Backport notes:

- keep highlight rendering optional under `contextActionPopup`;
- reuse the same filtered target used by activation;
- avoid importing ARPG transparent-ceiling/occlusion rendering.

## Do Not Backport As Mainline Interaction Fixes

These are ARPG-specific and should stay on the branch unless explicitly promoted later:

- isometric/ARPG camera frames and camera settings;
- click-to-move world movement;
- ARPG first-person toggle on `Y`;
- ARPG delayed spell release timing;
- ARPG action animation/recovery overrides;
- player monster sprite rendering;
- ARPG loot labels, beams, floating text, and auto-pickup;
- ARPG indoor sector visibility and ceiling/BModel transparency;
- minimap arrow override for ARPG facing;
- shared gameplay branches that change party member cycling, direct target selection, ranged target behavior, or attack
  recovery based on `arpgMode`.

## Suggested Backport Order

1. Add neutral context target helpers:
   `pickPrecisionContextActionTarget` and `pickForwardContextActionTarget`.
2. Port indoor event-face filters and geometry-highlight filtering first, with ARPG names removed.
3. Port indoor forward/crosshair popup target wiring.
4. Port outdoor forward target picking and LOS validation.
5. Change popup display to prefer exact hover/crosshair, then forward fallback.
6. Change use-key activation to activate the visible popup action first.
7. Add focused tests or scenario coverage for:
   - indoor door/button/chest context action selection;
   - indoor fake/ceiling/floor event faces not showing popup;
   - outdoor forward item/NPC/event target fallback;
   - key activation matching the visible popup target.

## Files To Inspect On The ARPG Branch

- `game/gameplay/GameplayInteractionController.cpp`
- `game/gameplay/GameplayRuntimeInterfaces.h`
- `game/indoor/IndoorRenderer.cpp`
- `game/indoor/IndoorWorldRuntime.cpp`
- `game/outdoor/OutdoorInteractionController.cpp`
- `game/outdoor/OutdoorWorldRuntime.cpp`
- `game/ui/GameplayHudRenderer.cpp`
- `game/ui/GameplayUiRenderer.cpp`
