# OpenYAMM Editor UI/UX final spec

## Goal
Polish the editor so it feels like a coherent desktop content-authoring tool:
- calm
- dense
- readable
- mode-safe
- efficient for keyboard and mouse users
- visually secondary to the map content

This spec is written so Codex can implement the UI with minimal ambiguity.

---

## 1. Core visual direction

### Keep
- compact desktop density
- dark theme
- warm retro/fantasy accent language
- text-first professional tooling feel

### Change
- reduce muddy brown-on-brown chrome
- increase hierarchy
- make active mode and active tool much more obvious
- make view toggles scan faster
- reduce the “everything looks equally important” problem

---

## 2. Design tokens

## Neutral surfaces
- `bg.app`: `#16181C`
- `bg.panel`: `#1D2127`
- `bg.panel_alt`: `#222730`
- `bg.toolbar`: `#181B20`
- `bg.viewport_frame`: `#111317`
- `bg.input`: `#14171C`

## Borders / separators
- `border.subtle`: `#2B313B`
- `border.default`: `#3A4350`
- `border.strong`: `#566274`

## Text
- `text.primary`: `#E6E8EB`
- `text.secondary`: `#B5BDC8`
- `text.muted`: `#8D96A3`
- `text.disabled`: `#616A76`

## Accent family
Use a restrained amber-gold, not saturated orange.
- `accent.base`: `#B9873D`
- `accent.hover`: `#D29A49`
- `accent.pressed`: `#8D652B`
- `accent.soft_bg`: `#3A2B18`
- `accent.soft_border`: `#6C4D20`

## Selection / focus family
Use cool blue only for focus and direct manipulation.
- `focus.base`: `#5E98E5`
- `focus.hover`: `#7EB0F0`
- `focus.soft_bg`: `#1B2A40`

## State colors
- `success`: `#5FA36A`
- `warning`: `#D0A44C`
- `error`: `#CC6666`
- `info`: `#72A7D8`

---

## 3. Control states

All interactive controls should have distinct visual states.

## Default
- background: `bg.panel_alt`
- border: `border.default`
- text/icon: `text.secondary`

## Hover
- background: slightly raised toward `#262D37`
- border: `border.strong`
- text/icon: `text.primary`

## Pressed
- background: `accent.pressed` for primary tools, otherwise `#15181D`
- border: darker version of current accent/border
- text/icon: `text.primary`
- apply 1px inset look if easy

## Active / toggled on
- background: `accent.soft_bg`
- border: `accent.base`
- text/icon: `#F2DEC2`

## Focused by keyboard
- 1px or 2px outer ring using `focus.base`
- do not rely only on color fill

## Disabled
- background: `#171A1F`
- border: `#262B33`
- text/icon: `text.disabled`
- reduce contrast, do not reduce opacity so much that text becomes unreadable

---

## 4. Icon color mapping

Because icons use `currentColor`, Codex should set icon color via the control state.

Recommended icon colors:
- default: `text.secondary`
- hover: `text.primary`
- active tool: `#F2DEC2`
- disabled: `text.disabled`
- destructive action hover: `error`
- warning item icon: `warning`
- validation error icon: `error`
- success/build-ready icon: `success`

---

## 5. Icon inventory and intended meanings

## Main editor modes
- `icon_select.svg` — generic selection mode
- `icon_terrain.svg` — terrain editing mode
- `icon_entity.svg` — generic entities mode
- `icon_spawn.svg` — spawn points
- `icon_actor.svg` — actors/NPC placement
- `icon_event.svg` — events/triggers

## Transform / coordinate space
- `icon_move.svg`
- `icon_rotate.svg`
- `icon_world.svg`
- `icon_local.svg`
- `icon_snap.svg`

## Terrain tools
- `icon_paint.svg`
- `icon_raise.svg`
- `icon_lower.svg`
- `icon_flatten.svg`
- `icon_smooth.svg`
- `icon_noise.svg`
- `icon_ramp.svg`

## View toggles
- `icon_grid.svg`
- `icon_wireframe.svg`
- `icon_textured.svg`

## Status / diagnostics
- `icon_warning.svg`
- `icon_validation.svg`
- `icon_build_ready.svg`
- `icon_dirty.svg`

---

## 6. Where icons should be used

## Use icon + text
For:
- top-level mode buttons
- view toggles
- inspector section headers if desired
- validation/build status pills
- actions like Apply / Reimport / Replace From OBJ if styled as toolbar-like actions

## Use icon-only
For:
- repeated transform tool buttons
- sculpt tool quick buttons if you later move them out of dropdowns
- visibility toggles only if accompanied by tooltip and already well learned

## Keep text-only
For:
- dense property forms
- long inspector actions
- raw data fields
- object/template dropdowns

---

## 7. Layout changes recommended from the supplied screenshots

The current editor already has a solid functional base. The major issue is not capability but scanability.

## A. Separate three horizontal bands
Current top area mixes everything together. Split into:

### Band 1 — menu + document status
- menu: File, Build, Edit, View
- document path/name and package/version
- saved/dirty, build state, validation count as pills

### Band 2 — editing context
- mode buttons: Select, Terrain, Face, Entity, Spawn, Actor
- transform tools
- terrain tool block only when terrain mode is active

### Band 3 — view filters
- terrain, grid, textured, preview, entities, spawns, actors, events
- convert checkboxes into toggle pills

## B. Make mode obvious
The user should know within 1 second if they are in:
- Select
- Terrain
- Face
- Placement mode

Use:
- stronger active background
- icon + text
- viewport mode badge in top-left

## C. Improve the inspector
The inspector in the supplied screenshots is powerful but visually flat.

Make sections:
- Selection Summary
- Identity
- Placement
- Behavior
- Visibility & Faction
- Overrides / Legacy
- OBJ Import / Asset Actions

Use collapsible headers with clearer spacing and slightly different section backgrounds.

## D. Scene tree improvements
Left scene panel should gain:
- search/filter field
- clearer type grouping
- count badges if easy
- stronger row hover/selected styling

## E. Viewport overlay cleanup
Current overlay is useful but boxy and noisy.

Use compact overlay chips:
- mode
- transform
- quick input hints
- camera position optionally reduced or collapsed

---

## 8. Per-mode UX recommendations from the screenshots

## Select mode
Prioritize:
- clear selected outline
- transform gizmo clarity
- object name and type in inspector header
- direct manipulation controls in inspector near top

## Terrain mode
Prioritize:
- current sculpt tool
- brush radius
- strength
- falloff
- target height controls only when Flatten is selected

Add a terrain mode viewport badge:
`Terrain · Sculpt · Noise · Radius 8 · Strength 25`

## Face mode
Face editing is information-heavy. Improve by:
- visually separating `Selection Actions`, `Clipboard`, `Visual`, `Scene Override`, `Texture Mapping`
- making destructive actions less visually similar to regular ones
- emphasizing currently selected texture preview

## Placement mode
For entity/actor/spawn placement:
- show active asset/template near viewport
- show “click to place” chip
- consider “align to ground” and random yaw options near placement tools

---

## 9. Typography and spacing

## Typography
- base UI font size: 12px or 13px
- dense labels: 11px acceptable
- headers: 12px semibold
- inspector section labels: slightly brighter than body labels

## Spacing rhythm
Use consistent internal spacing:
- 4px for tight control spacing
- 8px for related groups
- 12px between sections
- 16px between major regions if needed

Avoid many nearly-random small gaps.

---

## 10. Suggested component restyling

## Buttons
- height: 22–26px for dense desktop toolbar buttons
- min corner radius: 3px
- active buttons get amber border and warm fill
- inactive buttons remain neutral

## Checkboxes
For toolbar/view filters, replace with toggle pills.
Keep classic checkboxes only inside inspectors and forms.

## Inputs
- dark neutral field
- subtle inner contrast
- hover border increase
- focus ring with cool blue

## Dropdowns
- clearer chevron area
- slightly wider padding
- keep compact

## Status pills
Examples:
- `Source: saved` -> green pill
- `Source: dirty` -> amber pill
- `Build: stale` -> amber pill
- `Build: ready` -> green pill
- `Validation: 2` -> amber or red depending on severity

---

## 11. Mockup directions Codex should follow

## Mockup A — polished current layout
Keep the overall 3-panel layout:
- left scene tree
- center viewport + log
- right inspector

But improve:
- palette
- mode emphasis
- toolbar grouping
- toggle pills
- inspector section separation

## Mockup B — terrain-focused workspace
Use the same structure but in Terrain mode:
- terrain tool block visually dominant
- view filters compacted
- viewport larger and calmer
- contextual brush info chip overlay

## Mockup C — face/selection-heavy workspace
Emphasize:
- selected object/face summary at top of inspector
- texture preview treatment
- action grouping and spacing

---

## 12. Implementation instructions for Codex

1. Do not redesign the entire editor architecture.
2. Patch the existing layout first.
3. Introduce the icon pack from `icons/`.
4. Introduce a central theme/token file using the colors in this spec.
5. Convert the most repeated toolbar checkboxes into pill toggles.
6. Improve active/hover/pressed styling globally.
7. Group inspector sections with reusable section-header widgets.
8. Add search field to the scene panel if missing.
9. Keep existing shortcuts and workflows intact.
10. Do not make the UI oversized.

---

## 13. Priority order

## Priority 1
- theme token cleanup
- active/hover/pressed states
- icon integration
- toolbar grouping
- status pills
- inspector section polish

## Priority 2
- view toggle pill conversion
- viewport overlay cleanup
- scene search/filter
- per-mode contextual emphasis

## Priority 3
- workspace presets
- command palette
- docking/custom layouts

---

## 14. File list in this archive

- `icons/icon_select.svg`
- `icons/icon_move.svg`
- `icons/icon_rotate.svg`
- `icons/icon_world.svg`
- `icons/icon_local.svg`
- `icons/icon_snap.svg`
- `icons/icon_terrain.svg`
- `icons/icon_paint.svg`
- `icons/icon_raise.svg`
- `icons/icon_lower.svg`
- `icons/icon_flatten.svg`
- `icons/icon_smooth.svg`
- `icons/icon_noise.svg`
- `icons/icon_ramp.svg`
- `icons/icon_grid.svg`
- `icons/icon_wireframe.svg`
- `icons/icon_textured.svg`
- `icons/icon_entity.svg`
- `icons/icon_spawn.svg`
- `icons/icon_actor.svg`
- `icons/icon_event.svg`
- `icons/icon_warning.svg`
- `icons/icon_build_ready.svg`
- `icons/icon_dirty.svg`
- `icons/icon_validation.svg`

---

## 15. Notes on authenticity

This editor should feel like:
- a serious classic game content tool
- not a web dashboard
- not a modern oversized toy UI
- not visually louder than the map itself

The map content must remain the hero.
The UI should quietly make all actions faster and safer.