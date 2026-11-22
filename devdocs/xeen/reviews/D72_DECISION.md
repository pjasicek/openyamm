# Outdoor hatches into dungeons: decision (D-72)

Decider D-72, 2026-11-21. Read: D-24, D-50 change 3, D-65 B1, D-66 (DD-08 item 3, DD-17 items 5–6), A6's twenty-third session, D6's installed Lua (`xeen_d6.lua` events 33, 42, 44, 57, 70, 95), every installed ODM's moves into a BLV (D1–D6, X1–X9; X8 has none, D7 is a BLV), the return exits in `xeen_dd16|dd22|fd01.lua`, `devdocs/xeen/briefs/fd01/L4/playtest_in.yml`, the hooks `m29.pod_door`, `d6.sheltem_hatch`, `m39.depths_door` and `q-d15.lair_door`, `dark/aaze0005`, `aaze0006` and MM6's `oute3.lua`. Engine code read: `game/events/EventRuntime.cpp` `luaMoveToMap`, `moveToMapLeavesIndoorDungeon` and `luaAskQuestion`, and `EventDialogContent.cpp`'s transition window.

**DECISION**

1. **D6's three hatches stay as built.** They are FD-01's stair (event 70, `m39.depths_door`), Corak's pod (42, `m29.pod_door`) and Sheltem's pod (44, `d6.sheltem_hatch`). Each runs its hook and then moves at once, with no question. The game's window is not an option: the engine shows none on these moves.
2. **Rule for entering a dungeon from an outdoor map.**
   - The click moves at once, after its hook.
   - The map asks its own Yes/No only in two cases:
     - (a) a real choice: climb, fly, accept, destroy;
     - (b) a source question that a decision or an approved plan already kept for that door.
   - Lanes add no new questions to plain doors, hatches or mouths.
   - D-66's rule keeps its scope: exits **from a BLV into a BLV**, where neither side shows a window.
3. **Every outdoor question that stays must show its question on screen.**
   - No `evt.SetMessage` comes before it, unless that text itself ends on the request (D-65 B1).
   - It uses Yes/No buttons (`AskChoiceWithAnswerSteps`, as in D-66 item 6 and D7's `choice_lua`). The buttons follow at the map's next rebuild; this is not a reopen.

**WHY**

- **The engine shows no window on these moves.**
  - `luaMoveToMap` asks for confirmation only in two cases:
    - the move carries a transition text or picture id (arguments 7 and 8);
    - `moveToMapLeavesIndoorDungeon` is true. That needs the current scene to be indoors and the target to be an `.odm`.
  - D6's moves are `MoveToMap(..., 0, 0, 0, 0, "xeen_*.blv")` from an ODM, so they are queued as forced moves.
  - D-24's window ("Do you wish to leave {place}?") exists only on the way out of a BLV to an ODM.
  - MM6–MM8 confirm outdoor entrances only through a house text and picture, for example `oute3.lua:389` `MoveToMap(..., 417, 1, "6d01.blv")`. Xeen has no such rows, and adding them to about 60 doors would be new content with no source gain.
- **D-66's reason does not apply here.**
  - D-66 asks because a one-way roof between two BLVs gives no window and a misclick strands the party.
  - All three D6 hatches lead both ways. The way back is each map's exit preset to D6 (`xeen_fd01.lua:103`, `xeen_dd16.lua:129`, `xeen_dd22.lua:115`), and that exit does show the game's leave window. A misclick costs one click back.
- **The world already works this way.**
  - Of 72 installed doors from an ODM into a BLV, 61 enter at once. That includes doors whose source asked "Enter?":
    - Castle Kalindra (aaze0004:41)
    - the Great Pyramid (aaze0014:30)
    - the Troll Holes (aaze0016:2)
    - the Cave of Illusion (xeen/aaze0007:18)
    - Castle Xeen (aaze0027:40)
  - The pods' "Enter Strange Craft?" (dark/aaze0005:2, aaze0006:22) is the same case.
  - Adding three questions would make D6 the odd map out.
- **A question would clash with the hooks' texts.**
  - Each hook's text is the moment of entry ("The Cube of Power hums, and the mark goes out."; "The hatch slides aside with a sigh…"; "The hatch rolls aside…").
  - Under D-65 B1, a question after that message loses its own text, unless A3 rewrites three approved lines to end on a request.
- **Four outdoor questions break item 3 today.**
  - X6 80 and 83 and X7 38 and 40 call `SetMessage` and then `AskQuestion`. `luaAskQuestion` then shows only the pending message.
  - So the player sees only a description over an empty typed box, and the source question ("Enter the War Zone?", "Castle Basenji. Enter?", "Enter the Volcano Cave?", "The Dragon Cave smells pretty bad…") never appears.
  - D4 74 shows `q-d15.lair_door`'s line after Yes, as the party is leaving. Its hook's `where` says the line comes before "Enter?".

**WHO ACTS**

- **A8:** `devdocs/xeen/briefs/fd01/L4/playtest_in.yml`.
  - Drop the `answer_input: {text: 'Yes'}` step (step 14).
  - Drop "D6's Yes/No question (Yes)" and "Today D6 says 'Not yet open'" from the header, and "D6's question" from the note.
  - Make the change in the source that `tools/tests.py` reads, then regenerate. `four.sh` must pass 4/4 from assets_dev against D6 as installed (bake 08:39:16).
  - A6's working copy, `output/studio_cal/a6/s23/fd01_playtest_in_noq.yml`, is the reference.
  - No other playtest answers a question at D6's hatches: DD-16's and DD-22's in/exit tests already pass none.
- **A6** (D1, D2, D4–D7, X5, X8):
  - **D6:** no change to events 42, 44 or 70 (`d6/tools/gen.py` and the Lua stay). Close next step 1 in `lanes/A6.md`.
  - **Typed prompts to Yes/No buttons** at each map's next rebuild. Update the playtest steps that answer them.
    - D6 33 (Alamar's gate; its message already ends on "Enter?") and 95 (the adit, "Enter the Mine?", aaze0006:1).
    - D4 41 (the griffin), 50 (the sewer shaft, aaze0033:3) and 74 (the lair).
    - D1 117 and 121 (the ropes).
  - **D4 74:** no map message. Call `q-d15.lair_door` first, then show the buttons, and move on Yes. A3 ends the hook's text on the request.
  - **D2, D5, X5:** all enter at once, which matches the rule. No change.
- **A5** (X1–X4, X6, X7, X9, D3):
  - **Required at the next X6 and X7 rebuild, and before the world's next release:** X6 80 and 83, X7 38 and 40.
    - Each becomes one Yes/No button prompt whose own text is the description followed by the source question, for example "An iron-bound gate cut into the cliff. Beyond it a crowd roars, and something roars back. Enter the War Zone?". No `SetMessage` before it.
    - Their playtests assert that the dialog text contains the source question.
  - **X9 16 and 17 stay as built** (with the doll the gate enters at once). D-50 change 3's "the game's own leave window" does not exist outdoors, and the gate as built already meets this rule.
  - **X1–X4, X6 81 and 82, X7 39, 41 and 66, X9 42, D3 104 and 130:** these match the rule. No change.
- **A3:**
  - `q-d15.lair_door`'s text ends on the request (e.g. "… very still. Enter the cave?").
  - ORIGINAL_LINES:
    - "Enter Strange Craft?" (dark/aaze0005:2, aaze0006:22): not used, because the pod hooks' opening lines replace it (D-72).
    - Add a row for "Enter the Mine?" (aaze0006:1) on D6's adit.
    - Row "Enter Castle Xeen?" (aaze0027:40): "the meaning of X9's gate window" becomes "not shown; the gate enters at once (D-72)".
    - Record X6's and X7's joined prompts.
- **A1:** one sentence in the studio's `exit`/`into` docs: outdoors the move is immediate, and the leave window shows only when leaving a BLV for an ODM. No engine change.
- **Orchestrator:** the DECISIONS row. Add "(the window shows only when leaving a BLV for an ODM; D-72)" to D-24's and D-50's rows.

**REVERSIBLE:** Cheap. A question on any outdoor door is one `question:` field in its sketch plus one playtest step. The engine needs nothing either way.

**SUMMARY ROW** (≤ 50 words)

| D-72 | 2026-11-21 | Outdoor hatches into dungeons | D6's FD-01 stair (70) and both pods (42, 44) enter at once: entering a BLV from an ODM shows no window, and D-66 covers BLV→BLV exits only. A8 drops FD-01's answer step; A5 fixes X6 80/83, X7 38/40 (question text dropped). Detail: `reviews/D72_DECISION.md` | A8, A5, A6, A3, A1, orchestrator |
