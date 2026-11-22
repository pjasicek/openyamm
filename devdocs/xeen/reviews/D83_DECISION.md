# D-83: Q-C9, the Sphinx's door line (2026-11-21, fourth orchestrator's decider)

Question: X6 event 81 showed "The amulet grows warm..." and moved the party at once, so XD-15's arrival line replaced it
unseen. A5 (session 25) made the door two clicks; the alternative was one click and the line shown after arrival in XD-15.

DECISION: Keep A5's two-click door as installed in session 25. With the amulet, the first click on X6 event 81 shows
"The amulet grows warm, and the stone between the paws slides aside.", plays `xeen_sphinx_stir`, sets 112180 and keeps
the party on X6. Every later click goes straight into XD-15. The line is not shown after arrival in XD-15.

WHY:
- The line describes the door opening, not the party walking in; on X6 it reads as "the amulet unlocked the door" and
  the next click is plainly the way in. Inside XD-15 it would arrive after the fact.
- MM6–MM8 key doors: unlock with one action and visible feedback, enter with the next. The first click is not silent:
  a line and a sound, naming the amulet.
- D-72 holds: unlocking happens once and is not an entrance prompt; afterwards the entrance moves at once with no
  question. D-37 does not apply (A8's dungeon questions; the entrance name is unchanged).
- The alternative costs more: XD-15 already has a 6-second arrival line; combining lines or a one-time "just entered"
  flag would tie A7's map to X6's quest state and need an XD-15 change, while the current fix is installed and tested
  (X6 walk 385 passes).
- `ORIGINAL_LINES.md` has no original line for this door (the line is our own, q-c9.yml), so the source does not decide.

WHO ACTS:
- A5 (X6): nothing; optional: the hook's `else_text` ("The door between the paws stands open.") is now never shown;
  leave it (removing it touches NPCText 42951 and translations).
- A7 (XD-15): nothing.
- A3-side, scenario `tests/scenarios/xeen/side_quests/q-c8_q-c9_scroll_and_sphinx.yml` lines ~284–291: delete the
  `ISSUE (A5)` comment; replace the logging `play_lua` with one that does `click(81); wait(0.3)` and `error()`s if
  `status()` lacks "amulet grows warm", if the party is no longer on `xeen_x6.odm` or if `qbit(112180)` is not set;
  then add a second `play_lua: {source: "click(81)"}` before the existing `advance_runtime {follow_map_move: true}` and
  the `xeen_xd15.blv` and position asserts. Keep the later 112180 check.
- A3-side, `assets_dev/worlds/xeen/source/quests/q-c9.yml`: the `door` hook's `where` becomes: "the Sphinx's door
  between its paws on X6: the first click with the amulet runs this hook (a status line with `xeen_sphinx_stir`) and
  stays on X6; once `entered` is set, every click goes straight into XD-15's `entrance:x6_paws`. else_text is unused."
- G (guide): the walkthrough step: "With the Jewelled Amulet, click the door between the Sphinx's paws: the amulet grows
  warm and the stone slides aside. Click again to go in." Keep the line quoted; mark G.md question 6 / item 6 answered
  (D-83).

REVERSIBLE: Yes, cheaply: one event body in X6's Lua (`places.northern_sphinx`); the gen_walk `.pre_s25` backup holds
the old walk.
