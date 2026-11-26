# Playthrough checks: when to run them

Moved from the root `AGENTS.md` on 2026-11-24, unchanged.

- **Story and quest playthroughs are long checks, not routine tests.** The MM9 main story from a new game to its
  ending is `tests/playthrough/mm9/` (about 60 segments chained by checkpoint saves); its side quests are
  `tests/scenarios/mm9/side_quests/` (standalone, each from a new game); its promotion quests and their class table are
  `tests/playthrough/mm9/promotions/` (a chain that starts from the main run's checkpoints, which are git-ignored: run
  the main run first, then `promotions/run.py --start`). Each has its own `run.py` (and a
  `--reload` mode that saves and loads back after every step). They take minutes to tens of minutes, so they are not
  in CI (CI plays only `tests/scenarios/release/scenarios.txt`: never add them there) and are not run for ordinary
  changes. Run them when the user asks, before a release, or after a change that can break a story (a story map's
  converter or rebuild, event, dialogue, item or map-transition code, save format, the scenario runner), and then
  only the affected segments or quests (`run.py NN`). A change that deliberately alters a story path (an item made a
  world item, an event renumbered) updates the segments it breaks in the same change. How they are built, extended
  and debugged: the [Playthrough playbook](../../tests/playthrough/PLAYBOOK.md).
