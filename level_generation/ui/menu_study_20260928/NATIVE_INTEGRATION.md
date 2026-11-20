# Native Carved Obsidian menus

The approved r03 menu design is installed in the normal game. Main menu, Pause, save/load, continent selection,
full-screen party creation, five Settings sections, keyboard configuration, credits and confirmations use the new
shared presentation. [Real-game captures](native_review/index.html) are separate from the
[frozen browser handoff](runtime_stage/README.md).

The [latest flow adjustments](native_review/flow_adjustments/index.html) show saving back to gameplay, direct
continent-card activation, location below Continue and the simplified main-menu footer at 1280×720.
The [earlier native refinements](native_review/refinements/index.html) address screenshots 2109–2115 and the
subsequent pause, save/load, typing and cursor feedback at 1280×720 and 1600×900.

## Installed assets and typography

- `assets_dev/engine/hud_x2/menus/`: 50 approved PNGs, including blank button states, panels, backgrounds,
  the seal and the three original continent illustrations. Filenames are lowercase, permissions are 0644, and
  pixel contents match the staged originals except for the [study backdrop](study_background_20261004/README.md), corrected
  [save-row/text-field exports](native_review/control_borders/README.md) and seven
  [tab/toggle/key/skill exports](native_review/widget_borders/validation.json), which restore clipped borders from
  the same approved CSS. The existing package builder includes this directory automatically.
- `assets_dev/engine/fonts/truetype/fondamento_regular.ttf` and `fondamento_ofl.txt`: Fondamento and its licence.
- `fondamento.yml`, `menu_arrus.yml`, `menu_lucida.yml` in the same font directory: standalone FreeType metrics
  for these menu faces. Existing Arrus/Lucida font files and legacy descriptors are retained.
- `assets_dev/engine/ui/menu/`: main menu, credits, shared confirmation layout and settings catalog.
- `assets_dev/engine/ui/gameplay/`: pause, save/load, continent/party creation and the five settings layouts.

**Fondamento** supplies headings, buttons and the live OpenYAMM wordmark. **OpenYAMM Arrus** supplies body text,
attributes, skills and save names. **OpenYAMM Lucida** supplies compact metadata and key names. Labels are rendered
text over blank graphics. These menu aliases always use their TTFs; the existing in-game font preferences retain
their existing behavior. Installed Arrus/Lucida outlines are newer than the copies frozen in the browser handoff,
so integration reuses the installed versions instead of overwriting them.

The 2026-10-04 [study background follow-up](study_background_20261004/README.md) restores the original candlelit
scholar scene, adapted with a shaded wall for the main menu on the right. The title and controls retain their live fonts,
sizes and behavior. A light charcoal veil softens the painting behind the live controls. The shared pre-game backdrop
uses this painting; Pause continues to dim the active game view.
The earlier dusk vista and online comparisons remain preserved in the browser study. Native portraits, voices and
paperdolls use their existing game assets.

[Asset receipt](native_assets.json) records installed paths, hashes and source relationships.

The 2026-10-01 control correction uses viewport capture in `stage_runtime.mjs`: beyond-viewport capture hides
scrollbars and shifts right-aligned controls outside their measured export rectangles. Fractional crop endpoints
retain the entire bottom/right border. Toggles now render their complete plate without the old cropped-image
workaround. Settings, keyboard bindings and ordinary/selected creation skills were inspected at 1600×900 and
1280×720; the [widget receipt](native_review/widget_borders/validation.json) records the edge checks and native runs.

## Runtime behavior

- **Main / Pause:** Continue finds the latest valid save and displays its location. Actual elapsed play time is not
  stored in saves. The continent list and small OpenYAMM footer labels are removed. Escape pauses and resumes.
  Pause keeps the scene visible
  with simulation stopped; input belongs to the menu. New Game, Main Menu and Quit protect the active adventure
  with a confirmation. The first action is **Resume**. Holding Escape while resuming cannot reopen Pause until
  the key is released. Pause contains no title branding or extra paused/Escape messages.
- **Save / Load:** native save files, real scene thumbnails, location, game date/time and file timestamps;
  identical compact rows with names on the left and locations on the right, no row numbers or helper copy.
  Eight full rows fit instead of five. Scrollbars support thumb dragging, track paging and the mouse wheel;
  keyboard selection scrolls into view. Double-click loads, manual saves accept typed names, and replacing an existing
  save requires confirmation. Successful creation or replacement resumes gameplay, matching the previous shared
  save flow. Cancelling Save returns to Pause; cancelling a replacement or encountering a save error keeps Save open.
  Automatic and quick saves remain available to load and are excluded from manual replacement.
- **New Game:** no continent is selected by default. Hover highlights a card; clicking it, or using Tab and Enter,
  opens that continent's party creation immediately. There is no separate Create Your Party button.
  Native class/race, stat,
  skill, appearance, voice and party-size rules are retained. Assigned skills have the stronger r03 panels;
  optional skills use two columns. Right-click retains class/stat/skill explanations. Cancel returns to Main Menu.
  The special Lich preset explicitly displays its granted skills and fixed attributes instead of empty skill tiles
  and a misleading allocation prompt.
- **Settings:** Gameplay, Video, Audio, Mouse & Controls, Keyboard. Thirty player-facing settings use the actual
  `GameSettings` fields, with one draft across sections, Apply/Revert, section defaults, dependencies and unsaved-change
  protection. Debug/developer settings remain in the INI. Display mode, resolution and VSync changes have a
  15-second Keep/Revert preview. Changing control preset requires confirmation because it resets its bindings.
  Subsection headings use their full size without subtitle copy. A vertical rule separates navigation; group labels
  and toggle controls are larger, with the On/Off text beside the checkbox.
- **Keyboard:** all 26 implemented registered actions, search and group filters, two-column scrollable list,
  capture/cancel/clear, named conflict and explicit swap. Fixed shortcuts are shown separately. The engine's
  single-key / single-mouse-button binding model is retained; modifier combinations are not invented by this UI.
- **Credits:** New World Computing, OpenEnroth, Rodril/MMMerge, pjasicek and testers; GitHub opens only when clicked.

Tab / Shift+Tab focus controls, Enter / Space activate them, arrow keys adjust focused sliders, and scrollable
settings reveal keyboard focus. Choice dialogs support arrows, Tab, Home/End and Page Up/Down across the full list.
The key that opens a confirmation cannot accept or dismiss that same confirmation.
Only keyboard navigation displays a focus border; mouse/touch presses clear it. The border follows the control's
visible bounds. SDL text-input sessions now follow the active field on desktop as well as Android.

## Shared implementation

`MenuDesignScreen` consumes the normal `UiLayoutManager` layouts, fits the 853⅓×480 canvas uniformly, and handles
blank skins, clipping, focus and dynamic confirmations. Backdrops and save previews preserve image proportions.
`MenuScreenBase` supplies GPU tinting, scissor clipping, primitives and standalone font atlases. Menu TTFs are
rasterized at their actual display pixel height with light hinting and pixel-aligned glyph placement; natural advances
retain fractional spacing. Each size is cached, and display changes release the previous size variants. The shadow
uses a single one-pixel offset. Text fitting selects a smaller whole-pixel size before truncating a tight label.
The legacy FNT metric path remains available for existing UI.

This corrects the fixed 4× atlas minification that made small letters jagged at 1280×720.
[Native before/after comparison](native_review/font_sizes/index.html) preserves the captures at their original size.

`MainMenuScreen`, `LoadGameScreen` and `NewGameScreen` own the native interactions. `GameApplication` connects
pause/resume, session loading/saving, settings persistence and live display changes. The shared HUD occlusion rule
keeps the world visible on the initial pause frame, so the save thumbnail captures a rendered scene.

Before rendering gameplay behind an active menu, the shared input result is cleared and world input is blocked.
This prevents the indoor renderer from reapplying a stale mouse-look policy while the menu releases capture every
frame, which caused repeated cursor hiding and relative-mode changes. Resuming restores the normal gameplay policy.

The separate Obsidian in-game HUD and inventory/dialogue studies are not activated by this menu integration.

## Validation and reproduction

Build and focused test commands:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*menu*,*font atlas*,*save location*,*game input*,*full-screen gameplay HUD*,*save preview*,screen switch requested*,screenshot launch directives*'
```

The focused suite passes **20 cases and 7,966 assertions**, including native font metrics, heading widths across five
display scales, binding/settings validation, HUD scale and occlusion, deferred screen switching, save previews and
nonpersistent capture directives. Save-location labels resolve legacy filenames and canonical map ids.

Native checks use the ordinary game on NVIDIA/OpenGL through Wayland, with private settings and saves. Captures
come from the engine's frame readback. [Validation receipt](native_review/validation.json) lists the completed runs
and inspected outcomes; these checks are not hardware performance benchmarks.

The checked-in [menu tours](native_review/tours/) reproduce the flows through real menu input. For example:

```sh
./tools/run_game.sh --isolated menu-visual --menu --world mm6 --warmup 1 --seconds 70 \
  --set video.window_mode=windowed --set video.resolution=1600x900 \
  --set debug.new_game_god_lich=false --set debug.allow_incomplete_character_creation=false \
  --set debug.menu_input_tour_path="$PWD/level_generation/ui/menu_study_20260928/native_review/tours/visual.yml"
```

Use `save-load.yml` with `--world mm6 --map oute3.odm`, `--world mm7 --map 7out01.odm`, or
`--world mm8 --map out01.odm` to exercise actual save/load/resume. An indoor check also uses `--world mm6 --map 6d01.blv`.
The merged MM7 map name is **7out01.odm**.
Each tour's relative output directory resolves against the tour file. Run the desktop tours sequentially.
See [Desktop game runs](../../../tools/RUN_GAME.md) for the input-tour format and isolated launcher behavior.

`refinement-layouts.yml` checks the latest layouts, keyboard search typing and Continue → indoor Pause at 1600×900;
run it with `--menu --world mm6 --map 6d01.blv` and the ordinary creation settings shown above.
`refinement-final.yml` checks the special preset, named saving, save/load scrolling, cursor state and held Escape at
1280×720; run it with the same menu/map arguments and both creation debug settings enabled. For the recorded
long-list check, sixteen copies of a private New Sorpigal scenario save were added to that isolated run's `saves/`
directory before the tour opened Save Game. The player's saves and settings were not modified.
The [refinement receipt](native_review/refinements/validation.json) records the runs and their limits.

`flow-adjustments.yml` checks neutral continent cards, mouse/keyboard activation for all three continents, Continue's
location, new-save/overwrite return to gameplay and the two cancellation paths. Run it with `--menu --world mm6
--map 6d01.blv`, 1280×720 and both creation debug settings disabled. Its 59 steps passed six runtime state assertions;
the [flow receipt](native_review/flow_adjustments/validation.json) records the inspected native captures.
Older tours have been adjusted to click a continent card and reopen Pause after saving; historical screenshots remain
attached to the earlier receipts.
