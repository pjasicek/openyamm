# D-191, panelist B (round 1): the arrival message for a solo run

Question: M21's arrival window on XD-12 says "Every spell you reach for dies before it is shaped. Here you fight with
steel." Since U-18 a solo run casts there at half damage, and the monsters cast back at half. Map Lua cannot tell a
solo run. What does a solo player read, and how does it get there?

## DECISION

One generic engine query, and the arrival hook gets two states. The party text stays word for word. No engine-side
text, nothing specific to a world.

1. **A1: a new Lua query `evt.IsSoloRun()`** in `game/events/EventRuntime.cpp`, beside `luaGetPartyMemberCount`
   (the same pattern: `readableParty(pLuaState)`, then push `pParty != nullptr && pParty->soloRun()`), registered in
   `registerEventBindings` as `"IsSoloRun"`. It needs a one-line comment: "true in a solo run (`Party::soloRun()`,
   devdocs/solo_action/README.md), the flag `MapRuntimeRestrictions` reads; not the same as a party of one". Add a
   doctest in `tests/EventScriptingTests.cpp` next to "evt.IsTurnBased ...": "evt.IsSoloRun is true only in a solo
   run". It checks a party seeded with `setSoloRun(true)`, a normal party, and no party at all (false). Add one line to
   the solo README's "No-magic maps" bullet: "Map Lua reads it with `evt.IsSoloRun()` (M21's arrival text)." No MM6–MM9
   script calls the query, so they are unaffected and pay nothing for it.
2. **A3: `assets_dev/worlds/xeen/source/quests/m21.yml`, hook `arrival:`.** Replace `text:` with `states:`. The solo
   state comes first, because only the last state may go without a `when`:
   ```yaml
   states:
     - when: {lua: "evt.IsSoloRun()"}
       text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Every spell you shape comes out at half its strength, and so does every spell cast at you. The ward was laid against a company; one alone slips half through it. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
     - text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Every spell you reach for dies before it is shaped. Here you fight with steel. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
   ```
   Add to `where:`: "; a solo run reads the half-strength line (U-18)". Keep the message box for both runs. Like
   before, this is a long text read once on entry, not a find, a touch or a death (D-90 and QUESTS_FORMAT.md need no
   `window:` for it, and the generator already shows a hook state the way it shows the hook). Leave `darzog` ("His ward
   on your spells stays: it is in the stones.") and `crodo` ("Darzog's ward still holds him ...") alone: both stay true
   in a solo run, where the ward still halves every spell.
   - In `tools/xeen/quest_stub.py`, add the stub `function evt.IsSoloRun() return Stub.solo == true end` (false
     unless a segment sets it), so the stub run can call the condition.
   - Then follow AGENT_GUIDE §5.3/§5.4: `build_world.py --check`, `build_world.py --only gen_quests`, `quests.py` (0
     errors), `quest_stub.py`, and `--check` at 0 differ. The map needs no rebuild: XD-12 calls the hook by name.
   - The text ids of m21's later hooks move up by one (41050 becomes the solo state, the party text 41051, and so on).
     That only touches generated files. Translations are keyed by msgid, so the party line keeps its translations and
     the solo line is one new msgid. Leave `l10n.py` for the release (§5.5).
   - Add one example to QUESTS_FORMAT.md §4.2's `{lua: ...}` row: "`evt.IsSoloRun()` for a line that differs in a solo
     run (M21's arrival, D-191)".
3. **A8 (XD-12): a solo playtest** `devdocs/xeen/briefs/xd12/L4/playtest_solo_arrival.yml`.
   - Use `new_game_flow` with `start_map: xeen_xd12.blv`, `ruleset: "standard:solo"` and one Sorcerer at level 33.
   - Advance 3 s with `present_dialogs: true`, then assert `text_contains: "comes out at half its strength"`.
   - Close the window. If U-18's own playtest does not already cast, also cast a spell and check that it is not
     refused.
   - The party playtests (`playtest.yml`, `playtest_way_in.yml`) keep their "Every spell you reach for dies before it is
     shaped" assert unchanged.
   - In NOTES.md "The ward by run", the last sentence ("The arrival text still says spells die here; Lua cannot tell a
     solo run.") becomes "A solo run's arrival window says spells come out at half strength (D-191, `evt.IsSoloRun()`)."
4. **Orchestrator:**
   - In the walkthrough, `tools/xeen_site/story/act4.yml:124` ("No spell works anywhere in the tower: fight with steel,
     and bring potions for healing.") gets the whole sentence: "In a solo run your spells do work here, at half damage,
     and the tower's monsters cast back at half damage too."
   - Add the DECISIONS row and `reviews/D191_DECISION.md`.

## WHY

- **The text has to change for the solo player.** "Here you fight with steel" tells a lone mage to put the spellbook
  away. That is the exact worry the Discord player raised ("Solo Magic user will have a hard time"), on the very map U-18
  changed for them. The window is also the only place in the game that tells a solo player the monsters cast here too.
  A party never sees them cast.
- **A query is the honest mechanism, and the smallest one.** The engine already exposes run-wide facts to Lua the same
  way (`evt.IsTurnBased`, `evt.GetPartyMemberCount`). `IsSoloRun` is world-neutral and about six lines with a test. The
  quest generator already supports hook states with `when: {lua: ...}` (q-d14's potions, q-d23), so A3 changes only
  data. The condition is exactly the flag `MapRuntimeRestrictions::allowsSpellcasting(soloRun)` reads, so the text and
  the rules cannot drift apart.
- **Rejected: one text true for both runs.** A neutral line such as "magic falters here" undersells the party's case,
  where nothing casts at all and the playtests assert that. A line that explains both cases ("a company's spells die;
  one alone ...") puts a rules note about solo play in front of every party player, who are most players, and it reads
  like a manual, not like Xeen's short deadpan lines. I keep a half of that idea in the solo text only: "The ward was
  laid against a company; one alone slips half through it." It gives the solo player an in-world reason for the
  difference.
- **Rejected: an engine-side line** (for example a status line on entering a map whose solo percent is not 100). The
  arrival window would still say "fight with steel" and contradict it, unless the window changed anyway. It would also
  put world prose into the engine, or add a new per-map text key to the scene format for a single map. The real
  engine-side gap is different: the refusal line "You can't do that while underwater" in a dry tower (NOTES.md "No
  magic"). That is its own question and should not be mixed into this one.
- **Rejected: `GetPartyMemberCount() == 1`.** A party of one under normal rules is not a solo run, and the ward keys off
  `Party::soloRun()`. That party would read the solo text and still be refused every spell.
- **Rejected: an `Xeen.soloRun()` wrapper in xeen_common.lua, or a new `{solo: true}` condition form in quests.py.**
  The first is a forwarding layer that only hides the binding (AGENTS.md). The second adds generator work for a single
  use when `{lua: ...}` already covers it. A second user can justify the form later.
- **Edge cases, accepted as they are:**
  - A party of one that converts to a solo run after its first arrival has already seen the party text. The window
    shows once (`arrived_once`), and the spellbook works anyway.
  - The other way round (solo back to a party) cannot happen: the conversion is one-way.
- **Precedents.**
  - U-18 asked for the solo lift and left this line open only because Lua had no query.
  - D-90: the window is kept because this is a long text to read at a story entrance, not a find, a touch or a death.
  - D-188: a hook's line rewritten so it says what is true at that moment, with the matched sentences kept for the
    tests.
  - LOCALIZATION.md: whole sentences, and no sentence assembled from pieces at runtime. That is why there are two full
    texts rather than one shared opening with a swapped tail.

## WHO ACTS

- A1: the binding, its doctest and the solo README line. Small, under an hour plus a build.
- A3: m21.yml, the stub line, the regeneration and the QUESTS_FORMAT example. Small.
- A8: the solo playtest and the NOTES line. Small, one scenario run.
- Orchestrator: the walkthrough sentence, the DECISIONS row and the D191 file.

Order: A1 first, because A3's `quest_stub.py` and the playtest need the query. A3 can land the yml change at the same
time, since the stub covers it.

## REVERSIBLE

Yes. Everything is a data and text change plus one read-only Lua query; removing the state brings back the old window.
Confidence 85 %. The remaining doubt is wording: whether the solo text should also mention that monsters do not cast
at a party (I leave that out, because a solo player has no use for it).

## SUMMARY ROW

`| D-191 | 2026-11-26 | M21's arrival text in a solo run (panel) | New generic Lua query evt.IsSoloRun() (Party::soloRun(), EventRuntime.cpp, doctest); m21.yml arrival: becomes two states, solo first ("... Every spell you shape comes out at half its strength, and so does every spell cast at you. The ward was laid against a company; one alone slips half through it. ..."), party text verbatim; same message box (D-90); darzog/crodo lines unchanged; quest_stub stub, solo playtest_solo_arrival.yml (standard:solo), walkthrough act4.yml sentence. 85 % | A1 (query), A3 (m21, stub), A8 (playtest, NOTES), orchestrator (site) |`

## Round 2

I have read a.md and c.md. All three of us agree on the frame: two states on `m21.arrival`, the solo state first and
the party text unchanged word for word, a window in both runs (D-90), `darzog` and `crodo` unchanged, the NOTES.md
sentence and the guide's M21 line updated, and `GetPartyMemberCount()` and an engine-side line rejected. My final
position on each point where we differ:

- **Query: concede to A, a `soloRun` field on `evt.RulesetInfo()`, not a new `evt.IsSoloRun()`.** The solo run is a
  ruleset option (`RulesetOptions::soloRun`, `ruleset solo`, `standard:solo`). `evt.RulesetInfo()` is already where map
  Lua reads per-run options (`dimensionRun`, `challengeMode`, read by MAW's `d22_maw.lua` and `Global_maw.lua`). One
  more field avoids a second way to read the same kind of fact.
  - A1: in `luaRulesetInfo` (`game/events/EventRuntime.cpp`), add `soloRun` as
    `pParty != nullptr && pParty->soloRun()`, raise `lua_createtable` 5 → 6 and add the field to the comment.
  - A1: a doctest beside "Event scripts see the challenge mode in evt.RulesetInfo (Q8)"
    (`tests/MawChallengeModeTests.cpp`), plus the solo README clause.
- **Condition form: concede to A, the named key `{solo_run: true}` in `gen_quests.py`'s `CONDITION_KEYS`, emitting
  `evt.RulesetInfo().soloRun`.** That costs a few lines. QUESTS_FORMAT can document the key, `quests.py` can see it, and
  quest data never spells out an engine field. I withdraw my "wait for a second user": with RulesetInfo, a `{lua: ...}`
  string is longer and more fragile than a key.
- **Solo text: concede to C's wording.** Of the three it is the shortest. It gives the in-world reason before the fact,
  and "yours and the tower's alike" says in four words that the monsters cast at a solo run. A's text says the halving
  twice; mine split the reason from the fact. The final solo state reads: "Darzog's Tower. The Skeleton Key turns, and
  the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron:
  somewhere above, Crodo still lives. And the air itself is wrong. Darzog's ward was spun to catch a company of
  casters, and one alone slips through it, but not whole. Every spell here strikes at half its strength, yours and the
  tower's alike. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
- **Solo playtest: keep (A8, `devdocs/xeen/briefs/xd12/L4/playtest_solo_arrival.yml`).** Both existing playtests run a
  party, so they only exercise the default state. One cheap scenario catches a missing field or an inverted condition
  in the built game, which neither the doctest nor `quests.py` reaches.
  - The run: `new_game_flow` with `start_map: xeen_xd12.blv`, `ruleset: "standard:solo"`, one level-33 Sorcerer.
  - The check: advance 3 s with `present_dialogs: true`, then assert `text_contains: "yours and the tower's alike"`.
- **Also keep: the `tools/xeen/quest_stub.py` stub.** The stub today defines neither `evt.RulesetInfo` nor any solo
  flag. Add `function evt.RulesetInfo() return {soloRun = Stub.solo == true} end` so the stub run of the new condition
  does not raise (one line, A3).
- **Order: merge A and C.** A1's field lands first, A3's m21.yml in the same or a later merge point. No guard: before
  the field exists, `evt.RulesetInfo().soloRun` is nil and reads as a party run, which is the right fallback.

**Final SUMMARY ROW:** `| D-191 | 2026-11-26 | The arrival message for a solo run at Darzog's Tower (panel) | evt.RulesetInfo() gains soloRun (Party::soloRun(); doctest beside Q8); gen_quests condition {solo_run: true}; m21.yml arrival becomes two states, solo first: "...Darzog's ward was spun to catch a company of casters, and one alone slips through it, but not whole. Every spell here strikes at half its strength, yours and the tower's alike...", party text word for word; window kept (D-90); darzog/crodo unchanged; quest_stub stub; solo playtest playtest_solo_arrival.yml (standard:solo); XD-12 NOTES and the guide's M21 line updated. 85 % | A1 (field, test), A3 (gen_quests key, m21.yml, stub, QUESTS_FORMAT), A8 (playtest, NOTES), orchestrator (guide line, row) |`
