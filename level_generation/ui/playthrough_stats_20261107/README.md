# Playthrough statistics: mockups

7 November 2026 · implemented in the game the same day (`game/ui/GameplayStatisticsScreen.cpp`). Engine plan: [devdocs/PLAYTHROUGH_STATISTICS_PLAN.md](../../../devdocs/PLAYTHROUGH_STATISTICS_PLAN.md).

The mockups are in [index.html](index.html). Open the file directly or serve the repository root. On the live Overview,
hold the right mouse button on a line and a breakdown opens; release it and the breakdown closes.

All numbers belong to one consistent sample playthrough: the per-member columns add up to the totals.

**Art used.** Everything is the game's own approved art, copied into `assets/`:
- the reading surface;
- the quick-reference Exit button states;
- the inspect frame pieces and the value divider;
- the top-bar plate and command icons;
- the native party basebar from the overlay-arc capture, with its Dismiss button painted out;
- the faithful Lucida, Arrus, Create and Smallnum fonts, and Fondamento.

**Contents:**

| # | Screen | Point |
| --- | --- | --- |
| 1 | Top bar | Fifth icon between Party and Rest. The bar is 268 → 298 logical wide. Default key F1. |
| 2 | Overview | Seven groups, 26 lines. Gold marks rates and records, red marks losses. The basebar's right panel shows this session. |
| 3 | Party | Per member, in the Quick Reference layout, with a damage share bar. The top value in each row is gold. Former members and allies are on one line underneath. |
| 4–8 | Breakdowns | Experience, Monsters killed, Damage dealt (by school, with bars), Deaths, Time played. They open below the row, above it, or beside its column, and never cover the row. |
| 9 | Older save | Statistics start when the save is first loaded, and the header says so. |

**Icon.** Codex made three candidates from [icon/CODEX_BRIEF.md](icon/CODEX_BRIEF.md), using the four existing
command icons as the style reference:
- A: tally scroll;
- B: bronze dial;
- C: goblet with a sword and quill.

Raw generations are in `icon/raw/` and cleaned 1024 px masters are in `icon/masters/`. The page uses A. To see the
others, add `?icon=candidate_b` or `?icon=candidate_c` to the page address.

`artifact.html` is the same page in the form needed for publishing it as a claude.ai artifact.
