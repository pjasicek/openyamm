# D-191: M21's arrival text in a solo run (panel of three, converged, 2026-11-26)

Panel: proposals and both later rounds in [D191_panel/](D191_panel/) (`a.md`, `b.md`, `c.md`, each with its "Round 2").
Brief: [DECIDER_BRIEF_20261126b.md](DECIDER_BRIEF_20261126b.md). Converged by the orchestrator from the panel's votes:
round 1 three proposals, round 2 each read the others and kept, conceded or merged, round 3 one vote on the open text.

| Point | Round 1 | Final | Votes |
| --- | --- | --- | --- |
| How Lua tells a solo run | A: a `soloRun` field on `evt.RulesetInfo()`; B, C: a new `evt.IsSoloRun()` | **`evt.RulesetInfo().soloRun`** (solo is a run option, read where map Lua already reads `dimensionRun`, `challengeMode`) | B, C (A conceded the other way) |
| Condition in `m21.yml` | A: a named `solo_run` key in gen_quests; B, C: `{lua: ...}` | **`when: {lua: "evt.RulesetInfo().soloRun"}`**; a named key waits for a second use | A, C |
| Solo text | three wordings | **B's** (below) | A, C (B voted C's) |
| Solo playtest | B | **kept** | all three |
| Party text | unchanged | **unchanged, word for word** (translations keyed by English) | all three |

## DECISION

1. **A1 (engine, small):** `evt.RulesetInfo()` (the table MAW scripts read) gains a boolean `soloRun` from
   `Party::soloRun()` (false with no party). Doctest beside the existing RulesetInfo test
   (`tests/MawChallengeModeTests.cpp`): solo run true, normal party false, no party false. MM6–MM9 scripts never read
   it. A missing field (an older binary) reads as nil, which is the party text: no guard.
2. **A3 (`assets_dev/worlds/xeen/source/quests/m21.yml`, then `tools/xeen/build_world.py --only gen_quests`):**
   `arrival:` becomes two states, solo first:
   ```yaml
   states:
     - when: {lua: "evt.RulesetInfo().soloRun"}
       text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Every spell you shape comes out at half its strength, and so does every spell cast at you. The ward was laid against a company; one alone slips half through it. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
     - text: "<today's text, unchanged>"
   ```
   A comment ties "half" to the scene's `solo_spell_damage_percent: 50` (U-18). `where:` adds "; a solo run reads the
   half-strength line (U-18)". Both stay a window (D-90: a long text read once on first entry). Darzog's and Crodo's
   hooks are true for both runs and stay. `quest_stub.py` gets an `evt.RulesetInfo` stub returning
   `{soloRun = Stub.solo == true}`; QUESTS_FORMAT.md §4.2 gets the example line.
3. **A8 (XD-12):** `devdocs/xeen/briefs/xd12/L4/playtest_solo_arrival.yml` (`new_game_flow`, `start_map:
   xeen_xd12.blv`, `ruleset: "standard:solo"`, one Sorcerer at level 33): the window contains "comes out at half its
   strength"; then a spell is cast and not refused. The party playtests keep their "dies before it is shaped" assert.
   NOTES.md: drop "Lua cannot tell a solo run".
4. **Orchestrator:** the walkthrough's M21 line (`tools/xeen_site/story/act4.yml`) gets one solo sentence; the
   translation template (`tools/l10n.py`) is refreshed at release.

Order: A1's release first, then A3 and A8 (same or a later merge point).

## WHY

The party text's "Here you fight with steel" is false for a solo run since U-18. One text for both runs either blurs
the party's warning or puts a solo rules note before every party player; an engine-side line would contradict the
window and put world text in the engine; `GetPartyMemberCount() == 1` mistakes a party of one for a solo run. B's text
won because D-193 halves event and trap spells too, so "every spell cast at you" is exactly true, and it names both
directions most plainly.

## WHO ACTS

A1 (the field and doctest, small), A3 (m21.yml, stub, QUESTS_FORMAT, small), A8 (playtest and NOTES, small),
orchestrator (walkthrough sentence, l10n at release).

## REVERSIBLE

Yes. 85 % (the remaining doubt is the wording).

## SUMMARY ROW

`| D-191 | 2026-11-26 | M21's arrival text in a solo run (panel of three) | evt.RulesetInfo() gains soloRun (Party::soloRun(), doctest); m21.yml arrival: two states, solo first via when: {lua: "evt.RulesetInfo().soloRun"} ("… Every spell you shape comes out at half its strength, and so does every spell cast at you. The ward was laid against a company; one alone slips half through it. …"), the party text word for word; both a window (D-90); quest_stub stub; playtest_solo_arrival.yml (standard:solo); walkthrough sentence. Detail: reviews/D191_DECISION.md, panel in reviews/D191_panel/. 85 % | A1, A3, A8, orchestrator |`
