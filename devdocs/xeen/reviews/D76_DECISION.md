# The guide's uncertainty and spoilers: decisions (D-76)

Read: `tools/mm9_site/README.md`, `tools/mm9_site/story/BRIEF.md`, `tools/xeen_site/README.md`, `tools/xeen_site/story/BRIEF.md`, `devdocs/xeen/lanes/G.md`, the Xeen and MM9 story files, `tools/mm9_site/web/app.js` (`questBlock`, lines 557-590), and the generated `output/xeen_site/data/guide.js` and `output/mm9_site/data/guide.js`.

Facts that shaped the decisions:

- **Walkthroughs are already behind a click.** Every walkthrough sits in a `<details class="walkthrough">` that is closed by default. It only opens if the reader ticks "Open every walkthrough", and that choice is remembered. A visitor to a quest sees its summary, giver, level, requirements and reward, and nothing more until they click.
- **Only one walkthrough line says "not confirmed".** It is the Q-D10 robbery-route tip, `side_darkside.yml:244`. Five more lines speak in the writers' voice ("The playthrough goes ..."): `act2.yml` (3), `act5.yml:98` and `act6.yml:43`. Most of the 44 questions don't change what a player does in the current build. The walkthroughs already describe the built world, as their brief requires.
- **The real leaks are on the Xeen map pages.**
  - Point details there are drawn from the quest hooks' `where` notes, which were written for the map lanes. `clean_where` in `tools/xeen_site/build_site.py` only partly cleans them.
  - About 30 details carry developer wording: "calls this hook", "answer_wrong", "crumbled_3", "the source's 'Begone, impudent fools!' is not used", "the map's prompt".
  - About 54 mention answers and print them openly: "'Sheltem' calls this hook", "answers open sesame", "There wolf or therewolf", "'Paladin' calls this hook".
  - The MM9 guide's map details have none of either (0 and 0). This is where the Xeen guide departs from MM9, not in the walkthroughs.
- **No `shortcut` boxes exist** in the Xeen story files. The MM9 shortcut box (ways past a quest's work that the rework added) is not involved.

## 1. Uncertainty shown to players

**DECISION:** Hide it. No markers, and don't wait for A3. The published guide describes the current build as plain fact.

- **Soften to what the playthrough proved.** Where a line goes past what a playthrough or scenario showed, keep only the proven part and drop the rest. For example, Q-D10 becomes "The village is hostile afterwards." with the clause about Sharla and Sheewana removed. Don't add an "unconfirmed" marker anywhere, on the site or in the data.
- **No sources in player text.** Walkthroughs must not mention the playthrough, scenarios, quest files, hooks, A3 or the questions.
  - The five "The playthrough goes/raises/opens ..." lines become route advice, such as "One good order: ..." or "To raise the gold, do ... first".
  - "The guide follows the map" style remarks go.
- **Correct misleading in-game text in one plain clause.** Where a line in the game misleads (Picard's "just north of Darkstone Tower", Ellinger's stage-4 key line, the arrival line about Gunther's drums), the step states the built behaviour and may add one clause, e.g. "(his workshop is far to the north-east)". That is a player tip, not uncertainty. Remove the clause when A3 fixes the line.
- **Map point details carry no developer wording.**
  - Show the hook's player text where it has one. Otherwise show only the cleaned first clause of `where`.
  - Add a build check that stops on developer wording in any `d`: hook, calls this, `answer_wrong` and other snake_case identifiers, "the source", "the map's", qbit, event numbers. MM9's details pass it today.
- **One honest line on the home page.** The Xeen home lead (`site_config.yml` `site`, world-scoped) says the world is Experimental and the guide follows the current build. This matches U-3's "Experimental" card.

**WHY:**

- The guide's reader wants to know what to do, and the playthroughs are the proof that it works. A visible uncertainty marker would mostly flag internal disagreements between sources that don't change what the player does.
- Markers tend to outlive the questions they flag. The guide rebuilds and deploys in minutes, so correcting a fact after A3 answers costs almost nothing. That is cheaper than tracking which lines carry a marker.
- The uncertainty that actually reaches players today is in the map point details' developer notes, not in the walkthroughs.

**WHO ACTS:**

- **G:**
  - edits `side_darkside.yml:244` and the five "playthrough" lines;
  - fixes the point details at their source: `clean_where` and hook-text first in `build_site.py`, or hand renames in an `extra_pois.yml`, as G's Next item 2 already plans;
  - adds the developer-wording check to the build;
  - adds the home-lead line;
  - rebuilds, redeploys, and checks that the MM9 guide's `data/guide.js` is unchanged.
  - When A3 answers, G folds in each answer that changes the built world (G's Next item 1), and drops the clauses that correct in-game text once A3 has fixed that text.
- **A3:** answers the 44 questions. Answers 10, 36, 38 and 43 (misleading in-game lines) and 17 (the robbery route's aftermath) are the ones the guide's text depends on.

**REVERSIBLE:** Yes. The changes are text and generator filters. A marker could be added later as a world-scoped `GUIDE.site` option if a real need appears.

## 2. Spoilers

**DECISION:** Keep every puzzle answer in full in the walkthroughs, as MM9 does and as the Xeen brief requires ("No riddle is left to the reader"). Add no per-answer click-to-reveal, and make no change to the shared `app.js` or `style.css`. The walkthrough's closed `<details>` already acts as the spoiler gate.

Do take answers out of the always-visible map point details. As on MM9, a point names the thing and its prompt (e.g. "asks 'What's the password?'"). The answer lives in the quest's walkthrough, where the point's quest link already leads. This covers the 54 answer-bearing details (Ali Baba chest, XD-14's door, DD-17's true-name gate, D5's seventh boulder and the rest). It is done in the same generator pass as decision 1.

**WHY:**

- A reader who opens a walkthrough has chosen to be told. Hiding the answer a second time adds clicks for that reader and protects no one.
- A per-answer reveal would need inline markup in the story YAML and a shared front-end change across both guides, all to repeat what the closed walkthrough already does.
- The answers that reach a player who didn't ask for them are on the map pages. Removing them there brings Xeen into line with MM9's maps (0 answers in details) with no front-end work.

**WHO ACTS:**

- **G:** strips answers from point details, checks a few map routes with `output/xeen_site_work/shot.sh`, and redeploys.
- **A3:** nothing.

**REVERSIBLE:** Yes. A world-scoped reveal (a `GUIDE.site` flag, which leaves MM9's output unchanged) can be added later if players ask. Point details can show answers again by changing one generator filter.

## SUMMARY ROW

| D-76 | 2026-11-21 | Guide uncertainty and spoilers | Guide states the built world as fact: no "not confirmed", no markers, no source talk; proven facts only. Answers stay in full in the walkthroughs (already closed by default); no reveal widget. Map point details lose developer wording and answers (as MM9); a build check enforces it. | G; A3 answers |
