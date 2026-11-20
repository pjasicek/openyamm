# Approved menu staging bundle

**Carved Obsidian menus, revision 03 — approved by the user on 28 September 2026.**
This is the handoff for implementing the approved main menu, pause menu, save/load, continent selection,
full-screen party creation, Settings, keyboard configuration, credits and confirmations.

[Browse the graphics](index.html) · [Interactive approved design](../index.html) ·
[Approval receipt](approval.yml) · [Frozen screenshots](reference/) · [Validation](validation.json)

## Contents

| Location | Contents |
| --- | --- |
| `engine/ui/menu/` | Main menu, credits, reusable confirmation layout |
| `engine/ui/gameplay/` | Pause, save/load, continent/party creation, all five Settings sections |
| `engine/icons_x2/` | 47 blank PNG surfaces and 3 unchanged continent illustrations |
| `engine/fonts/truetype/` | Fondamento with its OFL licence; existing OpenYAMM Arrus/Lucida TTFs and descriptors |
| `contracts/theme.yml` | Typography, logical dimensions, surface states, padding, nine-slice and primitive drawing guidance |
| `contracts/screens.yml` | Screen/action mapping, dynamic data, scrolling, navigation and confirmation requirements |
| `contracts/settings.yml` | 30 player settings, INI owners, choices, dependencies and application behavior |
| `contracts/keyboard.yml` | All 26 implemented registered actions, categories, fixed shortcuts and capture behavior |
| `source/` | Measured geometry, CSS/JS snapshots, raw materials, editable seal SVG, provenance and previous browser validation |
| `reference/` | Revision 03 browser captures, including empty, conflict, overwrite and display-confirmation states |
| `manifest.json` | File hashes and candidate runtime destinations |

The `engine/` tree mirrors the intended global package under `assets_dev/engine/`. PNG names use the unique
`omenu_` prefix and the current `icons_x2` scope. The two existing native fonts are unchanged: reuse the installed
files when their hashes match. Do not copy the entire staging folder into the runtime asset mount.

The live game has not been switched to these menus. Layouts are **parser-compatible integration drafts**, not
a working replacement obtained by copying files. No game settings, saves, package manifests or runtime code were
changed for this staging task. “Staging” here is the integration bundle; it is not a Git index operation.

## Preserved design decisions

- Rough dark stone, worn brass and the approved generated dusk backdrop. Other background directions remain
  available in the parent study with artist/source credits; none was specifically selected to replace dusk.
- **Fondamento** for live actions, navigation, headings and the OpenYAMM wordmark. **OpenYAMM Arrus** for body,
  attributes, skills and save names. **OpenYAMM Lucida** for metadata, help, input labels and key names.
  No button label or title wordmark is baked into the supplied textures.
- **Settings** in both title and pause menus: Gameplay, Video, Audio, Mouse & Controls, Keyboard.
  Shared Apply/Revert state across sections; player settings only, as detailed in the existing audit.
- Simple save/load screens without search or world filters. Native thumbnails and real save metadata remain dynamic.
- **Choose Starting Continent**, then full-screen **Create Your Party**, then **Begin Adventure** directly.
  Cancel returns to the main menu. Preserve native portraits and paperdolls.
- The revision 03 stronger assigned-skill tiles and extra separation between Attributes and Starting skills.
  Optional skills use two columns. Do not reintroduce the earlier narrow inline assigned-skill summary.
- Credits for New World Computing, OpenEnroth, Rodril/MMMerge, pjasicek and the testers, plus the GitHub link.

## Runtime integration points

The current parser accepts all 13 drafts using its existing `screen`, `elements`, `children`, `asset`, `text`,
geometry and visibility fields. Contracts are deliberately separate YAML files: **do not pass `contracts/` to
`UiLayoutManager`**. It has no action binding, clipping, disabled-skin, range-control or nine-slice schema.
Braced text such as `{save_name}` identifies a controller-owned value, not an existing template language.

1. **Fit the complete canvas and input together.** Browser measurements are 1600×900; drafts use
   853⅓×480 logical units (8/15 of each browser pixel). Fit with
   `min(screenWidth / 853.333333, screenHeight / 480)` and center the result. Current menu resolvers still
   use 640×480 and ignore the declared reference dimensions. Honor the draft reference dimensions before use,
   including at 4:3; extend the backdrop on wider displays without stretching the content.
2. **Load live fonts.** `game/ui/MenuScreenBase.cpp` and `GameplayHudCommon.h` resolve legacy FNT names.
   `engine/FontAsset.cpp` currently loads a TTF replacement using an existing FNT's metrics. Fondamento needs
   a standalone TTF face/metrics path before `font: fondamento` is usable. Its proposed 32-unit cell in
   `contracts/theme.yml` is a sizing contract, not a supported engine descriptor. Preserve its own advances;
   do not shoehorn it into Arrus metrics. Existing Arrus/Lucida descriptors retain their native heights and baselines.
   The draft scales include the browser's 120% native-font adjustment. Calibrate baselines, wrapping and line
   height against the preserved captures. Draw arrows/checks as icons where the legacy text encoding needs it.
3. **Draw skins and live labels together.** Blank PNGs include measured padding for shadows. Button element
   rectangles describe content/hit areas; expand only the image destination by the documented padding and retain
   edge/corner sizes. Panel rectangles already include padding. Use native primitives for separators, focus rings,
   range tracks/thumbs and scrollbars. Apply hover, pressed, selected, disabled and focus states to both skin and
   live text. The title's metallic gradient remains a text treatment, with a solid fallback colour documented.
4. **Connect the existing controllers.** `MainMenuScreen.cpp` still draws four hard-coded image buttons and needs
   Continue/Settings plus live text. `LoadGameScreen.cpp`, `NewGameScreen.cpp`, `GameApplication.cpp` and the shared
   `GameplayUiController`, `GameplayUiOverlayOrchestrator`, `GameplayOverlayInputController` and
   `GameplayPartyOverlayRenderer` own the corresponding transitions and data. Reuse their gameplay behavior.
   Existing IDs are retained where the meaning matches; new IDs such as `MenuButtonSettings` and
   `CharacterCreationResetCharacterButton` require explicit wiring.
5. **Implement shared Settings state.** Read actual `GameSettings` values and binding presets on entry. Keep one
   draft across all five categories and preserve the entry origin. Apply/Revert and dirty-close prompts affect
   the entire draft; Restore Defaults is section-scoped. Enumerate display modes, disable resolution for borderless,
   pair terrain anisotropy with its filtering mode, and implement the 15-second display rollback. Deferred monster
   scaling on the next area entry is a new controller requirement. The browser's review defaults are not defaults
   to copy into the engine.
6. **Bind dynamic collections and clip input/rendering.** Scroll viewport IDs are enumerated in `screens.yml`.
   Their children use scroll-content coordinates, including rows below the initial viewport. Apply clipping to
   both draw calls and hit testing. Save rows are a reusable visible pool, not a maximum save count. Keyboard
   rows must reflow after search/category filtering; use registry IDs rather than browser event-code strings.
   Portraits, doll layers, available worlds/classes/races/voices, skill rules and attribute costs come from the
   engine and mounted content. The browser's simplified party rules are not a replacement for them.
7. **Use one modal controller.** The supplied confirmation layout measures the approved quit dialog. Its panel
   expands/reflows for longer text, a third action, key capture or a display countdown. Modal input takes priority;
   destructive actions run only after the appropriate confirmation. Preserve the existing save APIs and reserved slots.

## Graphics and provenance

Panels and control states are browser exports of the approved authored CSS/materials, with labels and unrelated
elements hidden. The stage exporter did not repaint the original artwork. `source/surfaces.json` records each
selector, image size and export operation; `source/copy_receipt.json` records unchanged source copies.
Raw materials and the original generated dusk image remain available for resolution-independent reconstruction.
The celestial seal is also supplied as editable SVG in `source/seal.svg`.

The three original continent illustrations retain the game's existing asset provenance. The native portraits,
paperdolls, game captures and legacy screenshots are not repackaged as menu textures. Online artist/fan background
comparisons stay outside the runtime payload; their provenance and reuse status are preserved in
`source/background_sources.json`. The generated dusk is the packaged default.

## Reproduce and verify

From the repository root:

```sh
node level_generation/ui/menu_study_20260928/stage_runtime.mjs
python3 level_generation/ui/menu_study_20260928/prepare_stage.py
python3 level_generation/ui/menu_study_20260928/validate_stage.py
```

Export uses a fresh local headless Chrome instance and `file://`; it does not need the study web server.
Preparation needs PyYAML. Validation needs Pillow, a C++20 compiler, and the existing build's yaml-cpp library.
It verifies assets, font/source hashes, all layout fields, IDs, references and scroll regions, and compiles a small
temporary checker against the repository's actual `UiLayoutManager.cpp`. It does not build the game or Vulkan.
`validation.json` records the result; `manifest.json` records the candidate payload and handoff file hashes.

Native visual acceptance follows implementation: title and pause entry paths; no-save and overwrite states;
all starting continents, party sizes, class/race layouts; long names; keyboard conflict/cancel; display timeout;
and 4:3, 16:9 and ultrawide fit. The existing browser study passed all 98 checks. Native rendering, persistence
and controller behavior have not been claimed as implemented by this bundle.
