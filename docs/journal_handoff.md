# Journal Handoff

Date: 2026-04-08

Scope:
- Fullscreen journal overlay for:
  - Map
  - Quests
  - Story
  - Notes
- Notes sub-pages:
  - Potion
  - Fountain
  - Obelisk
  - Seer
  - Misc
  - Trainer

Related planning doc:
- [map_quests_notes_implementation_plan.md](/home/pjasicek/github/OpenYAMM/docs/map_quests_notes_implementation_plan.md)

## Current State

Implemented:
- Journal can be opened and closed with `M`.
- Journal blocks gameplay interaction while open.
- One shared fullscreen YAML layout exists:
  - [journal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/Data/ui/gameplay/journal.yml)
- Top-level views are implemented:
  - Map
  - Quests
  - Story
  - Notes
- Notes categories are implemented.
- Right-side `IRA-*` main icons animate on hover.
- Map view renders a reveal-mask-based fullscreen map with zoom, pan, and party marker.
- Quest/story/notes paging is implemented.
- Data loaders exist for:
  - [JournalQuestTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/JournalQuestTable.cpp)
  - [JournalHistoryTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/JournalHistoryTable.cpp)
  - [JournalAutonoteTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/JournalAutonoteTable.cpp)
- Story placeholder formatting exists:
  - [StoryTextFormatter.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/StoryTextFormatter.cpp)
- History unlock timestamps were added to event runtime and save/load.

Important recent visual state:
- Journal body text font is now `AUTONOTE`.
- Journal title font is now `Book2`.
- Journal text area was moved `10` units left and widened by `85`.
- Current journal title/text block in YAML:
  - [journal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/Data/ui/gameplay/journal.yml#L241)

## Primary Files

Layout:
- [journal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/Data/ui/gameplay/journal.yml)

UI state and input:
- [GameplayUiController.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.h)
- [GameplayUiController.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.cpp)
- [OutdoorGameplayInputController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameplayInputController.cpp)
- [OutdoorGameView.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.h)
- [OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)

Renderer:
- [GameplayPartyOverlayRenderer.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.h)
- [GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)
- [GameplayHudRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayHudRenderer.cpp)
- [GameplayOverlayContext.h](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.h)
- [GameplayOverlayContext.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayOverlayContext.cpp)

Data loading:
- [GameDataLoader.h](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.h)
- [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [GameApplication.cpp](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)
- [CMakeLists.txt](/home/pjasicek/github/OpenYAMM/game/CMakeLists.txt)

Story/history persistence:
- [EventRuntime.h](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
- [EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- [SaveGame.cpp](/home/pjasicek/github/OpenYAMM/game/maps/SaveGame.cpp)

## Data Sources

- [quests.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/quests.txt)
- [history.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/history.txt)
- [Autonote.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/Autonote.txt)

Font assets in use:
- [AUTONOTE.FNT](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/AUTONOTE.FNT)
- [Book2.FNT](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/Book2.FNT)

## What Still Needs Work

### Visual polish

The journal is implemented, but still needs screenshot-driven polish.

Highest-priority areas:
- Right-side main icon placement against MM8 references.
- Notes-side category ribbon placement against MM8 references.
- Quest/story/notes text block height, line spacing, and divider spacing.
- Map viewport framing and button spacing.
- Title placement and scaling with `Book2`.
- Confirm body readability with `AUTONOTE`.

Reference screenshots already used in prior passes:
- [260_map.png](/home/pjasicek/github/OpenYAMM/test_img/260_map.png)
- [261_history.png](/home/pjasicek/github/OpenYAMM/test_img/261_history.png)
- [262_quests.png](/home/pjasicek/github/OpenYAMM/test_img/262_quests.png)
- [263_teachers.png](/home/pjasicek/github/OpenYAMM/test_img/263_teachers.png)
- [264.png](/home/pjasicek/github/OpenYAMM/test_img/264.png)
- [265.png](/home/pjasicek/github/OpenYAMM/test_img/265.png)

### Divider rendering

The user requested MM8-style entry separators using `DIVBAR.bmp`.

Current status:
- Divider rendering work was previously done in the overlay renderer for journal-style entries.
- Recheck current rendering in:
  - [GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)

If visuals still look wrong:
- verify exact divider width centering
- verify spacing between stacked entries
- verify clipping inside the text viewport

### Notes / story page formatting

Likely follow-up issues:
- How many wrapped lines fit per page with `AUTONOTE`
- Whether current pagination matches MM8 visually, not just logically
- Whether timestamps and story text substitutions match intended wording/spacing

### Diagnostics

There is no dedicated journal regression suite coverage comparable to the dialogue coverage.

Recommended next additions:
- Open/close journal with `M`
- Switch all 4 top-level tabs
- Switch all 6 notes categories
- Page forward/backward in quests/story/notes
- Confirm journal blocks gameplay clicks under it

Add these to:
- [HeadlessOutdoorDiagnostics.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/HeadlessOutdoorDiagnostics.cpp)

## Known Non-Journal Context

The worktree is dirty with unrelated changes.

Do not revert unrelated files.

At the time of this handoff, the most recent dialogue regression suite run reported:
- `passed=193 failed=2`

Remaining failures from that run were unrelated to the journal:
- `event_can_show_topic_actor_killed_uses_scene_context`
- `app_tavern_rent_room_closes_dialog_runs_rest_ui_and_wakes_at_6am`

## Suggested Next Session Order

1. Run the game and compare journal screens directly against the provided screenshots.
2. Adjust only [journal.yml](/home/pjasicek/github/OpenYAMM/assets_dev/Data/ui/gameplay/journal.yml) first until placement and typography are close.
3. If text flow still looks wrong, then refine page layout in [GameplayPartyOverlayRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp).
4. Add minimal journal diagnostics after layout is stable.

## Notes For The Next Session

- Use font names without `.FNT` in YAML.
  - `Book2` maps to `Book2.FNT`
  - `AUTONOTE` maps to `AUTONOTE.FNT`
- The current title/body font change is already applied in YAML.
- The current text viewport shift and width expansion are already applied in YAML.
- Treat the implementation plan as the original design intent and this file as the current-state continuation note.
