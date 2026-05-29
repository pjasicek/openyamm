# Map, Quests, Story, And Findings Implementation Plan

Date: 2026-04-08

Scope:
- Add the fullscreen journal overlay opened and closed with `M`.
- Implement the four top-level views:
  - World Map
  - Current Quests
  - Story
  - Findings
- Implement the Findings sub-pages:
  - Potion Notes
  - Fountain Notes
  - Obelisk Notes
  - Seer Notes
  - Misc Notes
  - Trainer Notes
- Use one gameplay YAML layout and switch visible subsections from code.
- Match OE behavior where it is applicable, without copying OE code.

Primary references:
- Screenshots and target layout:
  - [test_img/dwi_missing/map_quests_notes/x_map.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_map.png)
  - [test_img/dwi_missing/map_quests_notes/x_current_quests.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_current_quests.png)
  - [test_img/dwi_missing/map_quests_notes/x_story.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_story.png)
  - [test_img/dwi_missing/map_quests_notes/x_y_potion.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_y_potion.png)
  - [test_img/dwi_missing/map_quests_notes/x_y_fountains.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_y_fountains.png)
  - [test_img/dwi_missing/map_quests_notes/x_y_obelisks.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_y_obelisks.png)
  - [test_img/dwi_missing/map_quests_notes/x_y_seer.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_y_seer.png)
  - [test_img/dwi_missing/map_quests_notes/x_y_misc.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_y_misc.png)
  - [test_img/dwi_missing/map_quests_notes/x_y_teacher_loc.png](/home/pjasicek/github/OpenYAMM/test_img/dwi_missing/map_quests_notes/x_y_teacher_loc.png)
- Source data:
  - [assets_dev/Data/EnglishT/quests.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/quests.txt)
  - [assets_dev/Data/EnglishT/history.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/history.txt)
  - [assets_dev/Data/EnglishT/Autonote.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/Autonote.txt)
- Existing runtime/UI seams:
  - [game/data/GameDataLoader.h](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.h)
  - [game/data/GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
  - [game/ui/GameplayUiController.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.h)
  - [game/ui/GameplayUiController.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.cpp)
  - [game/ui/GameplayOverlayContext.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.h)
  - [game/ui/GameplayOverlayContext.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.cpp)
  - [game/ui/GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)
  - [game/outdoor/OutdoorGameplayInputController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameplayInputController.cpp)
  - [game/outdoor/OutdoorGameView.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.h)
  - [game/outdoor/OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)
  - [game/maps/MapDeltaData.h](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.h)
  - [game/maps/SaveGame.cpp](/home/pjasicek/github/OpenYAMM/game/maps/SaveGame.cpp)
  - [game/events/EventRuntime.h](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
  - [game/events/EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- OE behavior reference only:
  - [reference/OpenEnroth-git/src/GUI/UI/Books/MapBook.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Books/MapBook.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Books/QuestBook.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Books/QuestBook.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Books/AutonotesBook.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Books/AutonotesBook.cpp)
  - [reference/OpenEnroth-git/src/GUI/UI/Books/JournalBook.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/GUI/UI/Books/JournalBook.cpp)
  - [reference/OpenEnroth-git/src/Engine/Tables/HistoryTable.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Tables/HistoryTable.cpp)

## 1. Current OpenYAMM Baseline

Implemented now:
- Gameplay HUD, character screen, spellbook, rest screen, dialogue, chest, inspect overlays.
- `M` is not currently used as a gameplay overlay toggle.
- `MapDeltaData` already contains outdoor reveal masks:
  - `fullyRevealedCells`
  - `partiallyRevealedCells`
- `MapDeltaData` is already serialized in save files.
- `EventRuntimeState.variables` is already the authoritative storage used for:
  - QBits
  - autonotes
- The event system already raises portrait FX for newly unlocked autonotes.

Missing now:
- No journal/map/quests/story/findings overlay state.
- No journal YAML.
- No quest/history/autonote table loaders.
- No history runtime support.
- No story text formatter for MM8 history placeholders.
- No fullscreen journal input blocking.
- No reuse of outdoor reveal masks in a book-style fullscreen map renderer.

## 2. Authoritative Data Decisions

Use these files as authoritative:
- Quests: [quests.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/quests.txt)
- Story/history: [history.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/history.txt)
- Findings/autonotes: [Autonote.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/Autonote.txt)

Do not use:
- [Quest.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/Quest.txt)

Reason:
- `quests.txt` contains the MM8 quest-note data that matches the expected journal behavior.
- `Quest.txt` appears legacy/incomplete and would produce the wrong content set.

## 3. UX And Parity Goals

Required behavior:
1. `M` toggles the journal overlay open and closed.
2. While the journal is open, mouse and keyboard input must not propagate to gameplay.
3. The journal uses one fullscreen background and switches subsections from code.
4. The four right-side top-level icons switch the active journal view.
5. Hovering a right-side top-level icon loops its `IRA-*` animation frames.
6. Non-hovered right-side top-level icons show frame `*_01`.
7. Top-left art changes with the active top-level view:
   - map: `IRB-1`
   - quests: `IRB-2`
   - story: `IRB-3`
   - findings: `IRB-4`
8. Findings subcategory buttons switch content, but are not latched visually after release.
9. The close button matches the existing dialogue/house close button behavior.
10. Page transitions and view/category switches use the existing UI sound vocabulary.

## 4. UI Asset Plan

Add one new gameplay layout:
- [assets_dev/Data/ui/gameplay/journal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/Data/ui/gameplay/journal.yml)

Background and major art:
- `IRBgrnd.bmp` as the fullscreen background, anchored top-left at `0,0`.
- All element widths and heights come from the source BMP dimensions.

Shared always-present elements:
- `JournalBackground`
- `JournalMainViewMap`
- `JournalMainViewQuests`
- `JournalMainViewStory`
- `JournalMainViewNotes`
- `JournalCloseButton`

Map-only elements:
- `JournalMapTopLeftArt`
- `JournalMapViewport`
- `JournalMapZoomInButton`
- `JournalMapZoomOutButton`
- `JournalMapScrollNorthButton`
- `JournalMapScrollSouthButton`
- `JournalMapScrollEastButton`
- `JournalMapScrollWestButton`
- `JournalMapCoordinatesText`

Quest-only elements:
- `JournalQuestsTopLeftArt`
- `JournalQuestsPrevPageButton`
- `JournalQuestsNextPageButton`
- `JournalQuestsTitleText`
- `JournalQuestsTextViewport`

Story-only elements:
- `JournalStoryTopLeftArt`
- `JournalStoryPrevPageButton`
- `JournalStoryNextPageButton`
- `JournalStoryPageTitleText`
- `JournalStoryTextViewport`

Findings-only elements:
- `JournalNotesTopLeftArt`
- `JournalNotesPrevPageButton`
- `JournalNotesNextPageButton`
- `JournalNotesPotionButton`
- `JournalNotesFountainButton`
- `JournalNotesObeliskButton`
- `JournalNotesSeerButton`
- `JournalNotesMiscButton`
- `JournalNotesTrainerButton`
- `JournalNotesTitleText`
- `JournalNotesTextViewport`

Layout positioning rule:
- Use the screenshots as the visual target.
- Use the BMP dimensions directly.
- First scaffold places the elements in their screenshot-aligned logical regions.
- Final pixel nudging happens in the implementation pass after first render verification.

Known asset note:
- `IRT076r.bmp` exists next to `IRT07r.bmp`. Treat `IRT07*` as the intended misc-notes button set unless runtime loading proves otherwise.

## 5. Runtime State Model

Add a new journal state to [GameplayUiController.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.h):

- `enum class JournalView`
  - `Map`
  - `Quests`
  - `Story`
  - `Notes`
- `enum class JournalNotesCategory`
  - `Potion`
  - `Fountain`
  - `Obelisk`
  - `Seer`
  - `Misc`
  - `Trainer`
- `struct JournalScreenState`
  - `bool active`
  - `JournalView view`
  - `JournalNotesCategory notesCategory`
  - `size_t questPage`
  - `size_t storyPage`
  - `size_t notesPage`
  - `float mapCenterX`
  - `float mapCenterY`
  - `int mapZoomStep`
  - `float hoverAnimationElapsedSeconds`

State rules:
- Opening the journal initializes map center from the party position.
- Opening the journal preserves the last active top-level tab only within the current open session.
- Closing resets pressed/hovered input latches.
- View changes reset only the page index for the destination view.
- Notes category changes reset only the notes page index.

## 6. HUD Screen Integration

Add a new HUD screen state:
- `Journal`

Files to update:
- [game/ui/GameplayOverlayContext.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.h)
- [game/ui/GameplayOverlayContext.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.cpp)
- [game/outdoor/OutdoorGameView.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.h)
- [game/outdoor/OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)

Priority:
1. Dialogue
2. Journal
3. Rest
4. Character
5. Spellbook
6. Chest
7. Gameplay

Reason:
- The journal is a fullscreen overlay like rest/spellbook and must intercept input before gameplay.
- Dialogue remains higher priority so event conversations continue to behave deterministically.

## 7. Input Plan

Primary entry:
- [game/outdoor/OutdoorGameplayInputController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameplayInputController.cpp)

Required behavior:
- `M` opens journal if the current screen is plain gameplay.
- `M` closes journal if the journal is open.
- `Esc` also closes journal.
- Clicking the close button closes journal.
- Clicking the right-side view icons switches view.
- Clicking quest/story page buttons pages backward and forward.
- Clicking findings page buttons pages backward and forward.
- Clicking findings category buttons switches category.
- Clicking map zoom buttons changes zoom.
- Clicking map direction buttons pans the map.

Input blocking:
- Mirror the rest-screen fix pattern.
- If the frame starts or ends with the journal active, world interaction for that frame is suppressed.
- This includes NPCs, houses, attack clicks, movement clicks, and inspect clicks.

## 8. Journal Data Tables

Add three new table loaders under [game/tables](/home/pjasicek/github/OpenYAMM/game/tables):
- `JournalQuestTable.h/.cpp`
- `JournalHistoryTable.h/.cpp`
- `JournalAutonoteTable.h/.cpp`

Load them in:
- [game/data/GameDataLoader.h](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.h)
- [game/data/GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)

Expose them to gameplay:
- thread the new table references into [OutdoorGameView.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.h)
- thread the new table references into [OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)

### 8.1 Quest table rules

Parse:
- qbit id
- quest text
- notes
- owner

Display rules:
- show an entry only if:
  - the row has non-empty quest note text
  - the corresponding qbit is set in runtime state
- rows with empty quest note text are bookkeeping rows and are not displayed
- sorting is ascending qbit id

### 8.2 History table rules

Parse:
- history id
- body text
- time token
- page title

Display rules:
- an entry is visible only if its history id is unlocked in runtime state
- the page title comes from the row
- a single history entry may span multiple rendered pages
- page order is the unlock order sorted by history id, with multi-page entries expanded in place

### 8.3 Autonote table rules

Parse:
- note bit
- note text
- category

Normalize category names case-insensitively:
- `Potion` or `potion` -> potion notes
- `Stat` -> fountain notes
- `Obelisk` -> obelisk notes
- `seer` or `Seer` -> seer notes
- `Teacher` or `teacher` -> trainer notes
- everything else, including `Misc` and `Arbiter` -> misc notes

Display rules:
- show an entry only if:
  - the note text is non-empty
  - the autonote bit is unlocked in runtime state
- sorting is ascending note bit

## 9. History Runtime Support

This is the main missing gameplay foundation.

Add support for `History[n]` variables in:
- [game/events/EventRuntime.h](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
- [game/events/EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)

Required behavior:
- setting a history variable unlocks the corresponding story entry
- unlocking records the current game-minute timestamp
- unlocking an already-unlocked history entry does not overwrite the first timestamp

Recommended data shape in `EventRuntimeState`:
- `std::unordered_map<uint32_t, int32_t> historyEventTimes`

Persistence:
- serialize `historyEventTimes` in [game/maps/SaveGame.cpp](/home/pjasicek/github/OpenYAMM/game/maps/SaveGame.cpp)

Reason:
- OE story pages use more than a bool. They keep the unlock time and pass it into text formatting.
- Without timestamps, MM8 story entries cannot be rendered with full parity.

## 10. Story Text Formatting

Add a small formatter for history text before paging/rendering.

Recommended new helper:
- `game/gameplay/StoryTextFormatter.h/.cpp`

Responsibilities:
- resolve the subset of MM8 story placeholders used in `history.txt`
- accept:
  - source text
  - party
  - unlock time
- return already-expanded display text

Minimum parity target:
- support the `%31`, `%32`, `%33`, `%34` style party placeholders that appear in MM8 history text
- support any date/time substitutions needed by the `Time` column if the data requires them

Do not bury this logic in the renderer.

## 11. Rendering Plan

Primary file:
- [game/ui/GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)

Add a shared journal render entry:
- `renderJournalOverlay(...)`

### 11.1 Right-side main icon hover animation

Do not use `dift.bin` for these icons.

Reason:
- the `IRA-*` journal icon animations do not appear to be present in the existing icon-frame table.

Implementation rule:
- build a small explicit frame list per icon prefix:
  - `IRA-1_01` through existing last frame
  - `IRA-2_01` through existing last frame
  - `IRA-3_01` through existing last frame
  - `IRA-4_01` through existing last frame
- when not hovered, draw frame `*_01`
- when hovered, loop all frames at a fixed cadence

Recommended cadence:
- start with `10 fps`
- verify visually against the screenshots and OE feel

### 11.2 Quest and findings pagination

Implement a reusable paginator for stacked note entries with dividers:
- layout text into the viewport width
- add an entry
- measure its height
- stop when the next entry would overflow
- insert a divider between visible entries

Recommendation:
- build a pure data pagination helper so headless diagnostics can validate page boundaries without needing pixel snapshots

### 11.3 Story pagination

Match OE behavior:
- a single story entry may expand into multiple render pages
- store a flattened page list:
  - `entryIndex`
  - `pageIndexWithinEntry`
- render only the selected page of the selected story entry
- show the page title on the first page of the entry

## 12. Fullscreen Map Plan

Map view must reuse existing discovery data.

Outdoor behavior:
- Use the current outdoor map bitmap already used for minimap rendering.
- Apply the reveal mask from:
  - `fullyRevealedCells`
  - `partiallyRevealedCells`
- Unrevealed cells draw black.
- Partially revealed cells draw the OE-style dither/checker blend.
- Revealed cells draw the map normally.
- Draw the party arrow at the party world position and orientation.

Map view state:
- `mapCenterX`
- `mapCenterY`
- `mapZoomStep`

Zoom parity target:
- follow OE book zoom steps equivalent to `384` through `1536`
- store them as a small integer step list in OpenYAMM rather than raw OE constants if that is simpler

Pan parity target:
- support north/south/east/west directional buttons
- clamp panning to the map extents
- initialize center on the party when opening the journal

Coordinate text:
- draw the current party coordinates in the map view footer area

Implementation note:
- the current gameplay minimap logic in [game/ui/GameplayHudRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayHudRenderer.cpp) should be reused conceptually, but the journal renderer needs its own viewport, zoom, panning, and reveal-mask composition.

## 13. OpenYAMM File Touch List

Expected files to add:
- [assets_dev/Data/ui/gameplay/journal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/Data/ui/gameplay/journal.yml)
- [game/tables/JournalQuestTable.h](/home/pjasicek/github/OpenYAMM/game/tables/JournalQuestTable.h)
- [game/tables/JournalQuestTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/JournalQuestTable.cpp)
- [game/tables/JournalHistoryTable.h](/home/pjasicek/github/OpenYAMM/game/tables/JournalHistoryTable.h)
- [game/tables/JournalHistoryTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/JournalHistoryTable.cpp)
- [game/tables/JournalAutonoteTable.h](/home/pjasicek/github/OpenYAMM/game/tables/JournalAutonoteTable.h)
- [game/tables/JournalAutonoteTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/JournalAutonoteTable.cpp)
- [game/gameplay/StoryTextFormatter.h](/home/pjasicek/github/OpenYAMM/game/gameplay/StoryTextFormatter.h)
- [game/gameplay/StoryTextFormatter.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/StoryTextFormatter.cpp)

Expected files to update:
- [game/data/GameDataLoader.h](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.h)
- [game/data/GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [game/ui/GameplayUiController.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.h)
- [game/ui/GameplayUiController.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.cpp)
- [game/ui/GameplayOverlayContext.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.h)
- [game/ui/GameplayOverlayContext.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.cpp)
- [game/ui/GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)
- [game/outdoor/OutdoorGameplayInputController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameplayInputController.cpp)
- [game/outdoor/OutdoorGameView.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.h)
- [game/outdoor/OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)
- [game/events/EventRuntime.h](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
- [game/events/EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- [game/maps/SaveGame.cpp](/home/pjasicek/github/OpenYAMM/game/maps/SaveGame.cpp)
- [game/outdoor/HeadlessOutdoorDiagnostics.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/HeadlessOutdoorDiagnostics.cpp)

## 14. Implementation Sequence

### Phase 1. Data foundation

1. Add the three journal table loaders.
2. Load them in `GameDataLoader`.
3. Thread them into `OutdoorGameView`.
4. Add the story text formatter helper.

### Phase 2. Runtime support

1. Add `History` variable support in `EventRuntime`.
2. Add `historyEventTimes` storage.
3. Serialize `historyEventTimes` in save files.

### Phase 3. UI state and layout

1. Add `JournalScreenState` to `GameplayUiController`.
2. Add `Journal` HUD screen state.
3. Add `journal.yml` to the gameplay UI load list.
4. Add `openJournal()` and `closeJournal()` helpers to `OutdoorGameView`.

### Phase 4. Input

1. Bind `M` for toggle.
2. Add journal pointer target resolution.
3. Add click handling for all journal buttons.
4. Add full input-consumption gating so gameplay does not receive clicks while the journal is active.

### Phase 5. Rendering

1. Render shared background and close button.
2. Render right-side main icons and hover animation.
3. Render quest pages.
4. Render story pages.
5. Render findings pages and category switching.
6. Render fullscreen map with discovery mask, panning, zooming, and party arrow.

### Phase 6. Verification and polish

1. Add headless diagnostics for data loading and page-model building.
2. Add interaction diagnostics for `M` toggle and input blocking.
3. Manually compare the rendered layout against the provided screenshots and adjust `journal.yml`.

## 15. Diagnostics Plan

Add coverage in [HeadlessOutdoorDiagnostics.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/HeadlessOutdoorDiagnostics.cpp) for:

- `journal_hotkey_opens_and_closes_overlay`
- `journal_overlay_blocks_world_clicks`
- `journal_quest_table_uses_quests_txt_rows`
- `journal_autonote_category_mapping_normalizes_mm8_categories`
- `history_event_unlock_records_first_timestamp`
- `quest_journal_pages_visible_unlocked_entries_only`
- `story_journal_flattens_multi_page_history_entries`
- `findings_journal_filters_by_selected_category`
- `map_journal_uses_reveal_masks_for_visibility`

Recommendation:
- put most of the page-building logic into pure helpers so diagnostics can assert page contents directly without image comparison.

## 16. Open Decisions Resolved By This Plan

Resolved:
- One YAML file is sufficient.
- Main view switching is code-driven, not YAML-driven.
- Hover animation for `IRA-*` uses explicit numbered bitmap frames.
- `quests.txt` is the quest data source.
- `Stat` maps to Fountain Notes.
- `Teacher` maps to Trainer Notes.
- Unknown autonote categories fall back to Misc Notes.
- `M` is the open/close hotkey.

## 17. Risk Notes

1. Story text formatting is the highest hidden-risk area.
   - The data contains MM-style placeholder tokens that are not currently handled locally.
2. History needs timestamp storage, not only unlocked bits.
3. Full map parity depends on the reveal-mask renderer, not only on drawing the base bitmap.
4. Layout values will require at least one screenshot-driven adjustment pass after first implementation.

## 18. Definition Of Done

This feature is done when:
- `M` opens and closes the fullscreen journal.
- The overlay blocks gameplay interaction while visible.
- All four top-level views render.
- All six findings sub-pages render.
- Hovering the right-side view icons animates them.
- Quest, story, and findings pages paginate correctly.
- Story pages use unlocked history data with timestamps.
- The map view uses discovery masks, zoom, and panning.
- The close button works.
- Headless diagnostics cover the core journal model and interaction behavior.
