# Carved Obsidian menus — revision 03, 28 September 2026

Interactive browser implementation of the main menu, pause menu, save/load library, new-game flow, Settings,
keyboard configuration, credits, and their confirmation states. **Revision 03 was approved by the user on
28 September 2026 and integrated into the native game.** The browser study remains the preserved design reference.
See [native integration and validation](NATIVE_INTEGRATION.md) and the
[real-game screenshot gallery](native_review/index.html) for the installed implementation.

The [2026-10-04 native background follow-up](study_background_20261004/README.md) restores the original candlelit
scholar study, moves the title/menu to the right and adds light charcoal shading for the Obsidian scheme.
The browser study and frozen handoff below preserve their earlier dusk backdrop.

Open [the study](http://127.0.0.1:8899/level_generation/ui/menu_study_20260928/) or [index.html](index.html) directly.
The screen selector reaches every design. **Compare original** shows the matching supplied screenshot.
Background comparison, button lettering and an empty save library are available outside the game composition.
`export=1` hides those tools. Backgrounds can also be shared with `background=dusk|fortress|atlas|sketch`.

The pause and title menus both use **Settings**, as requested. Its subsections are **Gameplay**, **Video**,
**Audio**, **Mouse & Controls**, and **Keyboard**. The in-game Controls hub has been replaced by this hierarchy.

## Approved runtime staging

The [integration bundle](runtime_stage/README.md) preserves the approved r03 screenshots and source hashes,
13 parser-compatible UI YAML drafts, 47 blank graphics, three continent illustrations, all three approved fonts,
and the settings/keybinding/navigation contracts. [Browse the staged graphics](runtime_stage/index.html).
The dusk background remains the default; the online comparison directions are retained in this study.

The frozen bundle records the handoff before integration; its manifests and README intentionally retain that historical
status. The native implementation installs the graphics under `assets_dev/engine/hud_x2/menus/`, adds standalone
TrueType metrics, and connects the layouts to the real screen controllers. Its receipt is separate from the frozen bundle.
The [staging validation receipt](runtime_stage/validation.json) includes the actual C++ `UiLayoutManager` parser check.

## Revision 03: party skill emphasis

The marked party-creation reference is `test_img/2089.png` (the requested `20889.png` was not present).
Assigned class skills now appear as separate brass-edged, noninteractive tiles in 23px OpenYAMM Arrus,
replacing the small inline Lucida summary. The Attributes column retains its original usable width;
an additional 48px provides space and a subtle divider before Starting skills. Optional skills remain in
two columns without scrolling. No character-creation rules or font assets changed.

## Revision 02: requested refinements

- Preserve the liked title-menu composition; add four selectable background directions and a credited comparison gallery.
- Remove the title identity and redundant paused/Escape messages from Pause. Keep location, date and actions.
- Remove save/load eyebrow copy, search/world-filter row and footer prose. Keep the complete list and selected save details.
- Use **Choose Starting Continent**, remove the three flavour descriptions, and retain each starting location.
- Expand party creation to a 1560×860 frame within the 1600×900 stage. Increase the portrait from 89×119 to 152×202,
  enlarge the native paperdoll, and show every class's nine optional skills in two columns without scrolling.
  Remove the class boilerplate and separate review screen. **Begin Adventure** starts directly once the party is ready;
  **Cancel** and Escape return to the main menu, including when creation was entered from Pause.
- Use the project's recreated **OpenYAMM Arrus** and **OpenYAMM Lucida** TTFs throughout menu body text and values,
  with Fondamento actions/headings. Keep the same roles in party, continent, save/load and Settings.
- Remove the Settings welcome line and category-persistence note.
- Replace Credits with New World Computing, OpenEnroth, Rodril and the MMMerge contributors, and OpenYAMM
  (pjasicek and testers), with a link to the project's GitHub repository.

Revision 01 images and its validation receipt remain in `previews/r01-*` and `browser_validation_r01.json`.
Revision 02 captures and its validation receipt are also preserved. The current captures use `r03-*`.

## Visual language

- Continue [Carved Obsidian revision 06](../hud_overlay_study_20260927/README.md): rough dark stone, worn brass,
  carved corners, and restrained relief. Retain the actual generated sidebar surround as a reusable nine-slice frame.
  Larger panels use the existing finer stone texture behind text, avoiding enlarged grain and repeated decorative edges.
- Use **Fondamento** for buttons, navigation, headings, and the live **OpenYAMM** wordmark. All new button labels
  are text over blank surfaces; none is an image of a word. This follows the related
  [button typography study](../hud_overlay_study_20260927/BUTTON_TYPOGRAPHY.md) and the concurrent overlay work's
  accepted Fondamento direction. Almendra remains a review-only button comparison.
- **Universe of Might and Magic** is the second line of the identity. A small vector celestial/compass seal connects
  the title to the original diamond ornament vocabulary. The compact identity appears above the ordinary menu frames; Pause and the expanded party screen omit it.
- OpenYAMM Arrus carries descriptions and values; OpenYAMM Lucida carries compact help, keys and metadata.
  Both are unchanged copies of the existing faithful TTFs. CSS `size-adjust: 120%` compensates for their smaller
  visible glyphs relative to the former Source fonts; this is presentation sizing, not edited font geometry.
  Source Serif/Sans remain on the outer review page. Their OFL licences and Fondamento’s are bundled. Visible pressed, hover, selected, disabled, and keyboard-focus states
  keep label metrics stable. Reduced-motion preference disables transitions.
- A new text-free fantasy vista gives the title its own atmosphere. The pause screen dims the approved gameplay
  capture. Busy menus use a wider common workspace: unlike the house-dialogue screen, they contain no fixed movie
  viewport that requires the original 4:3 composition. The 1600×900 study scales uniformly; fullscreen centres it.

## Screens and interactions

| Screen | Implemented in this browser study |
| --- | --- |
| Main menu | Continue with location, New Game, Load Game, Settings, Credits, Quit; Continue/Load disabled with no saves |
| Pause menu | Resume first, then Save, Load, Settings, New Game, Main Menu and explicit Quit to Desktop; Escape resumes |
| Load | Complete save list, manual/auto/quick identities, selected preview, location, game date/time, saved timestamp, double-click load and empty state |
| Save | New-save row, name field, manual saves only for replacement, overwrite confirmation, reserved automatic/quick names; sample saves update in memory |
| New game | Starting continent → full-screen party creation → Begin Adventure; Enroth, Antagarich and Jadame |
| Party creation | One to five members, enlarged portrait and native paperdoll, name, voice, world-appropriate Human classes, attributes, fixed skills, two-column optional skills, reset/remove, readiness validation, Cancel to main |
| Settings | Five persistent categories, 30 settings, Apply/Revert, scoped restore defaults, dirty-state protection, remembered title/pause return destination |
| Keyboard | All 26 implemented registered actions, search, six groups, two-column list, capture/cancel/clear, named conflict and swap, reserved shortcuts, preset/reset confirmation |
| Confirmations | Overwrite, load from an active adventure, start anew, return to title, quit, discard settings, restore defaults, binding conflict, display keep/revert with a real 15-second countdown |
| Credits | NWC, OpenEnroth, Rodril/MMMerge, pjasicek and OpenYAMM testers, plus the GitHub project link |

The **native paperdoll is retained**: existing body and open-hand assets are layered over their existing backgrounds.
Positions are imported from `character_data.txt` and `doll_types.txt`, with the same Y sign conversion used by
`CharacterDollTable.cpp` and layer order used by `NewGameScreen::buildCreationPreviewDollPixels`.
No character, portrait, world-selection illustration, or source screenshot was redrawn.

## Settings audit: what was missing

The audit compared [GameSettings.h](../../../game/app/GameSettings.h), its
[INI parser/writer](../../../game/app/GameSettings.cpp), [the current Controls layout](../../../assets_dev/engine/ui/gameplay/controls.yml),
[Video Options](../../../assets_dev/engine/ui/gameplay/video_options.yml), and the actual overlay input handlers.
[settings_audit.json](settings_audit.json) records every control and its exact INI owner.

**13 existing menu settings are retained; 17 existing INI settings receive a player-facing entry.** The original
Controls hub mixed sound, movement, and links to other screens. The original video panel exposed cinematic colour
and three effects, while retaining a stale “Gamma Preview” heading in the supplied screenshot. The new hierarchy
separates these concerns and does not claim to implement a gamma control.

| Category | Retained from existing menus | Newly exposed existing settings |
| --- | --- | --- |
| Gameplay | Hit messages | Monster scaling, quest markers, floating combat text, enemy health bars, target information, context action menu, event-cutscene skipping |
| Video | Cinematic colour/strength, coloured lights, tinting, blood splats | Window mode, resolution, VSync, view distance, texture smoothing, terrain anisotropy, terrain details, melee blood effects |
| Audio | Effects, music and voices at the existing 0–9 scale; footsteps | None required |
| Mouse & Controls | Turn rate, always run, face away on house exit | Modern/Classic preset, mouse sensitivity at its actual 0–100 range |

The on-screen values are **review defaults**, not this machine's configuration. Runtime display modes must be
enumerated from the monitor. Borderless disables the resolution control. Cinematic strength follows its toggle.
The anisotropy control assumes anisotropic terrain filtering; runtime adoption must apply the corresponding
filtering mode as well as the level. Extended view distance is an example explicit distance; performance and labels
need calibration per supported world. “Unlimited” retains the existing parser's bounded interpretation.

Monster scaling uses the existing bolster feature; the proposed menu applies that change on entering an area.
That timing is a design requirement for later integration, not evidence that a new deferred-application path exists.

Deliberately omitted from ordinary player settings:

- Debug/god mode, unlimited mana, seeded test parties, trace logs, asset paths, screenshot capture and launch overrides.
- AI pathfinding switches, raw interaction distances, blaster formula tuning, billboard depth slicing and baked-light
  calibration. These are implementation/data controls, not useful player choices merely because they exist in the INI.
- Per-package texture tiers and font/filter overrides. A future verified artwork-quality preset could replace that
  technical detail; this study does not claim that arbitrary restored tiers are installed or available.
- Shadows, sprite outlines, lightmaps and loading-detail switches pending a separate parity/performance decision.
  The presence of a stored flag alone does not justify promising consistent indoor/outdoor behaviour.
- FOV, UI scale, subtitles, gamepad remapping and secondary bindings: potentially useful future features, but not
  represented as working settings without an authoritative implementation. The selected HUD is treated as the new
  visual baseline rather than exposing the old Standard/Widescreen implementation selector here.

## Keyboard audit

[binding_audit.json](binding_audit.json) is an extraction of all **29** definitions in
[KeyboardBindings.cpp](../../../game/app/KeyboardBindings.cpp), including page, row, key and implementation flag.
**26** are marked implemented. Yell, Combat and Pass are marked unimplemented; the first two occupy visible legacy
rows, while Pass is hidden. They are recorded in the audit rather than offered as working actions.

Double Speed is implemented and bound to F2, but hidden from both old pages. It is now discoverable under System.
Movement, Combat, Interaction, Party & books, Camera and System replace page numbers as meaningful filters.
The two-column list scrolls without a fixed page capacity, and search includes assigned key names.

Fixed shortcuts are displayed separately: **F9 Quicksave, F10 Quickload, 1–5 party selection, Escape menu**.
These are the actual current shortcuts, not conventional F5/F9 guesses. They remain reserved during capture; the
debug-console backquote is also reserved. Modifier combinations are not offered as though the current binding model
supported them. The current model has one input per action, so this design does not invent a second binding slot.
The browser accepts keyboard and mouse-button samples; current menu capture only exposes keyboard and left mouse,
so adopting additional mouse-button capture is an explicit runtime input follow-up.

## Supplied screen references

Unchanged copies of the user's `test_img/2070.png`–`2077.png` are included and hashed in
[asset_sources.json](asset_sources.json).

| Image | Current screen |
| --- | --- |
| 2070 | Pause/menu: New, Save, Load, Controls, Quit, Return |
| 2071 | Save: named slots, location, preview, calendar, Save/Cancel |
| 2072 | Load: autosave/quicksave/manual slots, preview and calendar |
| 2073 | Controls: volumes, turn rate, movement toggles, keyboard/video links |
| 2074 | Keyboard page 1, with fixed 14-row arrangement and page navigation |
| 2075 | Video: colour grading, effects, old Gamma Preview plaque |
| 2076 | Character creation: name, class, portrait, voice, 15-point pool, skills, paperdoll |
| 2077 | Title: painted background, baked title and four baked-label buttons |

The approved HUD image is used as the paused scene and a clearly documented sample save thumbnail.
Goblinwatch and Harmondale preview areas are CSS crops of the supplied images' scenery, above their baked calendar text.
Sample save metadata is illustrative,
not a scan of the user's save directory. A missing screenshot has a deliberate no-preview state.

## Preserved browser scope

The browser page implements the design and its illustrative interaction model. Apply saves to this page's memory;
refresh resets the example. Audio/voice choices do not play samples, display confirmation does not change the actual
monitor, Begin/Load/Resume lead to a static gameplay handoff, and Quit leaves the preview open with an explicit notice.
The review toolbar and bottom caption make that scope visible outside the proposed game UI.

Party creation uses five existing Human examples and imported class starting-skill lists. The 15-point Human demo
uses simple one-for-one increments and does not simulate the complete race-stat rules, every portrait/voice, or
the full character-selection registry. Native adoption must keep the authoritative candidate, race, class, voice,
stat-cost, skill-cap and world-mount rules. Do not port the browser's illustrative state into the game as gameplay logic.
The supplied God Lich screenshot is a debug example, not a default new-game choice.

The [native integration](NATIVE_INTEGRATION.md) retains `MainMenuScreen`, `LoadGameScreen`, `NewGameScreen`,
`GameSettings`, the binding registry and existing save services as the owners. It implements standalone TTF metrics,
shared title/pause Settings, real display rollback, and native save/party behavior. Its screenshots and validation
receipt supply the runtime evidence; the frozen browser captures remain the visual reference.

## Background comparison

The current **Dusk vista** remains the default. Use the toolbar selector or the gallery under the stage to compare
all four behind the same title layout. The alternatives are title-only; Pause retains the gameplay capture.

| Choice | Source | Design assessment |
| --- | --- | --- |
| Dusk vista | Original generated artwork from revision 01 | Strongest quiet composition and most neutral invitation to the combined worlds. |
| Sepia fortress | [Flavio Greco Paglia, Might & Magic Heroes concept art](https://www.behance.net/gallery/41550721/Might-Magic-Heroes-Concept-Art-Illustration) | Strong alternative for a drawn, older-fantasy atmosphere. Made for a Ubisoft trailer, not an NWC-era sketch. |
| World of Enroth | [MarkonPhoenix, Superior World of Enroth](https://www.deviantart.com/markonphoenix/art/Superior-World-of-Enroth-667443279) | Makes the combined-world premise explicit. Busier than a vista; the geography is the artist's fan interpretation. |
| NWC sketchbook | [George Almond's MM8 sketches, archived at Jaskinia Behemota](https://mm8.heroes.net.pl/galeria) | Closest to original MM8 pencil art. A necromancer is less representative of all the game's worlds and classes. |

The three external images are unchanged downloads for **local design comparison**, not accepted game assets.
No redistribution licence has been established for them. The original signatures remain in the images; the gallery
and selected-background line link the artists/sources. CSS contains each complete image and provides the menu shade
or parchment colour. [background_sources.json](background_sources.json) records sources, hashes and review status;
[backgrounds.js](backgrounds.js) is its browser-readable data copy. Nothing is installed into runtime mounts.

## Artwork and verification

[asset_sources.json](asset_sources.json) records unchanged local copies and their hashes. The new background is
[assets/generated/universe-dusk-v1.png](assets/generated/universe-dusk-v1.png), created with the **built-in imagegen
tool** using the [imagegen skill](/home/pjasicek/.codex/skills/.system/imagegen/SKILL.md). Its exact final prompt and returned
source path are in [generated_art.json](generated_art.json). No CLI generation was used. The vector seal and all
interface layout/state effects are authored in code.

**Revision 03 verification: all 98 existing browser checks passed**, including every class’s two-column
skill layout, with no JavaScript errors or missing assets.
[browser_validation.json](browser_validation.json) records the executable interaction checks and
[previews/](previews/) contains each screen plus important modal/empty states. Checks include local font/assets,
title/pause navigation, pending changes, real display timeout, conditional controls, preset changes, conflicts,
reserved keys, reset/clear, save creation/overwrite, empty libraries, one-to-five party capacity, completion gating,
native paperdoll layers, keyboard focus and 1280×720 fit. Revision 02 also checks the simplified text, direct
party start, Cancel destination, all class skill layouts, full-screen portrait/doll bounds, native fonts, requested
credits and every selectable background. Captures are browser screenshots, not game captures.

```sh
node --check level_generation/ui/menu_study_20260928/app.js
node --check level_generation/ui/menu_study_20260928/data.js
node level_generation/ui/menu_study_20260928/test_browser.mjs
```

The last command expects the repository served at `http://127.0.0.1:8899/` and launches its own isolated headless Chrome.
No C++ build or runtime test is needed for this browser-only change; none was run.
