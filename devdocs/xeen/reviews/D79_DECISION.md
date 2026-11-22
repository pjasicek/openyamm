# Clue texts on the guide's maps: decision (D-79)

Read: `devdocs/xeen/reviews/D76_DECISION.md`, `tools/xeen_site/README.md` ("Player text (D-76)"), `tools/xeen_site/build_site.py` (`clean_where`, `map_secrets`, `hide_answers`, `developer_wording`), `devdocs/xeen/lanes/G.md` (State), `tools/mm9_site/web/app.js` (lines 306, 429, 710, 1310), `tools/mm9_site/extra_pois.yml`, and the generated `output/xeen_site/data/guide.js` and `output/mm9_site/data/guide.js`.

Facts that shaped the decision:

- **Point details are seen without asking.** A point's detail shows in its hover tip, in the point panel and in the map's point filter. Site search also matches on it (`app.js` 306, 429, 710, 1310). Someone looking for a shop, or searching "dial", gets the clue text without opening any walkthrough.
- **The Xeen map pages show clues the game spreads out.** The game makes the player go and find each clue. The guide puts them all on view at once:
  - the obelisk words, 7 on the surface and 6 in the Darkside pyramids;
  - the four Dragon Rune books (x9 e46-e49);
  - the Book of Ascension (dd09 e6), which sits away from the dials it sets;
  - the Asp rule stone (x4 e98), plus its second half at xd25 e14;
  - "The Count wakes at nine" (x3 e50);
  - the dd12 statue ("Turn all dials up");
  - the Overseer's pad map (dd15 e51);
  - the dd15 number verses (e84, e85, e88, e89).

  Collecting those clues is the puzzle itself, so showing them together removes it.
- **The Dragon Rune books break D-76's own rule.** FI/IN/NI/TY spell "Infinity", the typed answer to x9's "What is the secret of the Dragon?" (`xeen_x9.lua:413`). Each piece is shorter than the five-letter threshold, so `hide_answers` and the build check let them through.
- **MM9's map points never quote an in-game clue.** MM9 has no `sign` point type, and its longest detail is 117 characters. Its notes and scrolls appear by name only, with empty details: Chess note, Coded scroll, Elixir instructions, Manuscript, Njam's letter. So option (a)'s "as MM9's signs are" does not hold: MM9 shows no sign text at all.
- **But three MM9 hand-kept points state solutions in the guide's own words** (`tools/mm9_site/extra_pois.yml`):
  - darkpassageway Gemstone: "mirrors to 330, 10, 340, 50";
  - darkpassageway Floor plates: "north-east, south-west, south-east, north-west";
  - the four Ta-Sar Academy tables, each naming its book (a borderline case, since each table has a sign).

  D-76's "0 answers in MM9 details" counted typed answers only. These are the exceptions.
- **The typed-answer cut leaves a broken fragment on the sundials.** x3 e51-e53 read "The sundial is set to ", because the script builds that message from the dial's live value. dd17's dials show the right form: "A sundial in its alcove; each turn moves it on one hour".

**DECISION:** (b). Cut clue texts that spell out a solution, the same way typed answers are cut. A point names the thing and may quote its clue up to the clause that gives the solution away. The solution lives in the walkthrough.

The principle for this and every future point: **a point says what a thing is, what it asks and what it does when used. It never says how to solve it.**

- **Allowed:** what a mechanism does ("each turn moves it on one hour", "Light all four, and the way is open"), lore and flavour, directions, bonus effects, and the prompt a point asks.
- **Not allowed:** the hidden knowledge a puzzle checks for. That means a setting or value, an order, a combination, a pairing, a route, a word, a recipe for working out a number, or pieces that add up to any of these.
- **It does not matter who says it.** A solution is cut whether it comes from the game's own clue text or from the guide's voice, and whether or not the answer is typed.
- **The test is whether a reader who has never been there could do the puzzle from the details alone.** If yes, cut it. A cryptic hint that still needs the player's thinking stays, for example the dd08 pillow note or fd04's "something to do with forever".
- **A cut detail ends cleanly.** Keep the lead-in, end it with a full stop, and leave no dangling colon or "set to", e.g. "Only a scrap of the original text remains legible." or "Carved into the obelisk, the first of seven words."
- **The thing's location stays on the map.** Marking a place is the map's job, as MM9 marks hidden doors. This covers x6's mound of sand.

**WHY:**

- D-76's rule was "a point names the thing and its prompt; the answer lives in the walkthrough". The typed-answer filter was only the tool that carried it out. From the player's side, a dial order or a colour sequence is as much an answer as a password. Splitting typed from non-typed is the generator's distinction, not the reader's.
- Option (a)'s argument, "it is what the player reads on the spot", fails because the guide shows the text away from the spot. The reader sees it before getting there, together with every other clue of the puzzle, through hover and search, without asking.
- The walkthrough already holds every solution in full behind its closed `<details>`, as D-76 decided. Cutting the map detail loses nothing for a reader who wants the answer: the point's quest link leads there.
- MM9's maps show no clue text at all. Xeen's maps keep more than MM9's (the lead-in, flavour signs, mechanism text) and stop at the same place.

**WHO ACTS:**

- **G:**
  - Sweep Xeen's sign and objective points with the test above. The clear cases are the ones listed under the facts; G settles the doubtful ones by the test, e.g. xd02 e33 (the Red Dwarves' tablet) and x8 e15.
  - Fix each point by hand in `tools/xeen_site/extra_pois.yml`, as a detail override or a cut-at clause.
  - Extend the build check so a rebuilt point cannot bring a declared solution back. Add a per-map list of solution phrases next to the typed answers that `map_secrets` already collects. Check two-letter pieces such as the rune syllables per point, not as map-wide words, because "IN" would match everywhere.
  - Fold the Dragon Rune books under D-76's typed rule: pieces that spell a typed answer count as that answer.
  - Replace the broken "The sundial is set to " details (x3 e51-e53) with the dd17 wording. dd09's empty dial details can get the same.
  - Add one sentence to README "Player text (D-76)" stating the principle (D-79).
  - Rebuild, check a few map routes with `output/xeen_site_work/shot.sh`, confirm the MM9 `data/guide.js` is unchanged, and redeploy.
- **Request to the MM9 guide owner, through the orchestrator:** move the Gemstone angles and the Floor plates order out of the point details in `tools/mm9_site/extra_pois.yml`; the walkthrough in `ch3_5.yml` already has both. Decide on the Academy tables by the same test. G leaves the MM9 output unchanged.

**REVERSIBLE:** Yes. The changes are hand overrides in `extra_pois.yml`, a per-map phrase list and one generator filter. A clue's full text can be restored by deleting its override or phrase.

## SUMMARY ROW

| D-79 | 2026-11-21 | Clue texts on the guide's maps | Points never state how to solve a puzzle, typed or not: no value, order, pairing, route or word, whether quoted from a clue or in the guide's words. Clues are quoted up to that clause; walkthroughs keep solutions. | G; MM9 guide owner (two points) |
