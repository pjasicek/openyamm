# D-191, panelist A (round 1): the arrival message for a solo run

## D-191: what a solo player reads at Darzog's Tower, and how

**DECISION:** M21's arrival hook gets two states, picked by a new `solo_run` quest condition that reads a new
`soloRun` field of the existing `evt.RulesetInfo()`. A party run reads today's text unchanged. A solo run reads a text
that says what U-18 actually does (spells work, at half strength, both ways). The window stays a window. Steps:

1. **A1 (engine, one field).** `luaRulesetInfo` in `game/events/EventRuntime.cpp` pushes one more field,
   `soloRun` (boolean, `pParty != nullptr && pParty->soloRun()`), beside `dimensionRun` and `challengeMode`; the
   `lua_createtable` size goes 5 → 6 and the comment above the function lists the field. No new Lua function, no
   change in `event_support.lua`. Test: a doctest beside `"Event scripts see the challenge mode in
   evt.RulesetInfo (Q8)"` (`tests/MawChallengeModeTests.cpp`): a party with `setSoloRun(true)` reads
   `evt.RulesetInfo().soloRun == true`, a default party reads `false`. Add one clause to the solo README's
   "No-magic maps" bullet: "Map Lua reads the run as `evt.RulesetInfo().soloRun` (XD-12's arrival text, D-191)."
2. **A3 (quest generator).** `tools/xeen/gen_quests.py`: `solo_run` joins `CONDITION_KEYS`; `cond()` emits
   `evt.RulesetInfo().soloRun` for `{solo_run: true}` and `not evt.RulesetInfo().soloRun` for `{solo_run: false}`.
   QUESTS_FORMAT.md §7 (or the condition list) gets one line: "`solo_run: true|false`: the run is (not) a solo run
   (`evt.RulesetInfo().soloRun`); for text that must differ where a map's rules differ by run (XD-12's ward, D-191)."
3. **A3 (m21.yml).** `hooks.arrival` loses `text:` and gains `states:` (the solo state first; only the last may lack
   `when`):

   ```yaml
   states:
     - when: {solo_run: true}
       text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Darzog's ward lies on the stones, made to smother the spells of a whole company. Alone, you slip under it, but only half of each spell gets through. Every spell you cast here strikes at half its strength, and so does every spell cast at you. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
     - text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Every spell you reach for dies before it is shaped. Here you fight with steel. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
   ```

   The party state's words are exactly today's, so its `msgid` and the zh-CN translation carry over. Then
   `python3 tools/xeen/build_world.py`, `python3 tools/xeen/quests.py` (0 errors), and `tools/l10n.py extract` for the
   new msgid. `m21.darzog` ("His ward on your spells stays: it is in the stones.") and `m21.crodo` are true for both
   runs and stay. `xeen_xd12.lua` is untouched (it calls `XeenQuests.hook("m21.arrival")` as now).
4. **A8 (notes).** `devdocs/xeen/briefs/xd12/L4/NOTES.md` "The ward by run": replace "The arrival text still says
   spells die here; Lua cannot tell a solo run." with "The arrival text has a solo state (D-191,
   `evt.RulesetInfo().soloRun`)."
5. **G (guide site).** `tools/xeen_site/story/act4.yml` M21 line "No spell works anywhere in the tower: fight with
   steel, and bring potions for healing." gains: "In a solo run your spells work there at half damage, and so do the
   monsters'."

Accepted edge: a party of one that converts to a solo run after its first arrival saw the party text (the hook is
once, `arrived_once` 110503). The ward itself follows the flag, so nothing breaks; the text is not shown again.

**WHY:**
- The solo text must carry information the player cannot find elsewhere: the halving is invisible (the spellbook
  preview shows full damage, D-194), and the monsters casting again at a solo run is a surprise after a party-run
  rumour of "no magic". A sentence true for both runs cannot do that without becoming vague ("a ward smothers your
  spells") or telling a party about solo rules. The party, in turn, needs today's plain "Here you fight with steel":
  it is the warning that makes the map fair (D-89 spirit: no unexplained gate). So two texts, chosen at run time.
- The query belongs in `evt.RulesetInfo()`: it already reports per-run options to map Lua (`dimensionRun`,
  `challengeMode`, read by MAW's `d22_maw.lua` and `Global_maw.lua`), and the solo run is itself a ruleset option
  (`ruleset_solo`, `--ruleset maw:solo`). One field is the smallest engine change; a new `IsSoloRun()` function would
  be a second way to read the same kind of fact.
- The hook already supports `states:` with `when:` (gen_quests' `hook_lua`), so the generator needs only a condition
  key, not a new hook shape. A named key over `when: {lua: "evt.RulesetInfo().soloRun"}`: QUESTS_FORMAT documents it,
  `quests.py` can count it, and the next solo-aware hook does not copy a Lua string.
- D-90: the arrival is a long story text shown once, not a find, a touch effect or a death; it keeps its window,
  and both states show the same way (`show_lua(hook, ...)`). Localization: each state is one whole English sentence
  set passed as one literal through `NPCText`; `.po` files key by msgid, so the text-id shift inside block 21
  (darzog 41051 → 41052, crodo 41052/41053 → 41053/41054) changes nothing for translations.
- MM6–MM9: an additive field in a table only MAW scripts read (by other fields); no existing script, table or save
  changes.
- Rejected: `GetPartyMemberCount() == 1` (a party of one is not a solo run, and the ward reads the flag, not the
  size); an engine-side status line on arrival for any map whose rules differ by run (generic and `tr()`-able, but
  a second message on top of a window that would still say "fight with steel"; worth it only if more maps gain a
  solo lift); a map-Lua branch in `xeen_xd12.lua` (generated from the studio project; the text belongs to A3's hook,
  D-90's hook ownership); leaving the text and documenting the exception (the user's player report is exactly the
  solo mage, who would read the one wrong line).

**WHO ACTS:** A1 (one field, a comment, one doctest; under an hour, rides the next merge point); A3 (condition key,
m21.yml states, QUESTS_FORMAT line, build_world/quests/l10n runs; under an hour, after A1's field is in or in the
same merge point since the Lua only reads a field that is nil-safe as `false` before it lands); A8 and G one line
each; orchestrator records the D-191 row and amends U-18's "unchanged (Lua has no solo query)" by reference.

**REVERSIBLE:** yes (text and an additive field). Confidence 85 %.

**SUMMARY ROW:** `| D-191 | 2026-11-26 | The arrival message for a solo run at Darzog's Tower (panel) | M21 arrival gets two states: a solo run (new quest condition solo_run, reading a new soloRun field of evt.RulesetInfo()) reads "...Darzog's ward lies on the stones, made to smother the spells of a whole company. Alone, you slip under it, but only half of each spell gets through. Every spell you cast here strikes at half its strength, and so does every spell cast at you..."; a party keeps today's text word for word. Window kept (D-90); darzog/crodo lines unchanged; XD-12 notes and the guide's M21 line updated | A1 (field + test), A3 (gen_quests key, m21.yml, QUESTS_FORMAT), A8, G |`

## Round 2

Read b.md and c.md. All three agree on the shape: two hook states on `m21.arrival`, a solo state first, the party
text byte-identical, a window for both (D-90), `m21.darzog` and `m21.crodo` unchanged, and no head-count, one-text or
engine-line route. Where we differ:

- **Query: concede to `evt.IsSoloRun()`** (B, C). The solo flag is a `Party` fact, not part of the ruleset's
  `scriptInfo` that `RulesetInfo()` reports. A boolean function beside `evt.IsTurnBased()` is the closer precedent, and
  two of three proposals chose it. Take C's comment and B's doctest in `tests/EventScriptingTests.cpp` (solo, normal
  party, no party → false). The solo README line names `evt.IsSoloRun()`.
- **Condition form: concede to `when: {lua: "evt.IsSoloRun()"}`** (B, C). It has one use and `gen_quests.py` already
  emits it, so there is no generator change. A named `solo_run` key can come with a second use. Take B's
  QUESTS_FORMAT §4.2 example line in place of my condition-key line, and B's `quest_stub.py` stub
  (`function evt.IsSoloRun() return Stub.solo == true end`).
- **Solo text: merge.** Mine said "half" twice. C's "yours and the tower's alike" could be read to include traps and
  map events, which D-193 has not ruled on yet. The merged text says the reason once, then the rule once, with the
  monsters named:
  "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air.
  Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Darzog's ward was
  laid against a company of casters; one alone slips through it, but not whole. Every spell you cast here strikes at
  half its strength, and so does every spell the tower's monsters cast at you. The stairs climb the west and east halls
  in turn; the Baron keeps the top floor."
  If D-193 halves traps and event spells too, a later edit can widen the wording to "every spell cast at you". Add
  C's m21.yml comment tying the two texts to the scene's `runtime_restrictions` ("Change both together (D-191)").
- **Solo playtest: keep, using B's form** (`devdocs/xeen/briefs/xd12/L4/playtest_solo_arrival.yml`,
  `ruleset: "standard:solo"`, one level-33 Sorcerer). It asserts `text_contains: "strikes at half its strength"`,
  then casts a spell with `expect` not refused. This is the only end-to-end check that the run flag reaches the hook,
  and it costs one scenario run. The party playtests keep their "dies before it is shaped" assert.
- **Order: concede to C.** A1's release lands first, then A3 installs m21.yml. No `evt.IsSoloRun ~= nil` guard:
  without the binding the call raises an error, and a guard would be the fallback AGENTS.md forbids. This replaces my
  round-1 note about a "nil-safe field".
- **`l10n.py`: concede to B.** Refresh the `.pot` at release per AGENT_GUIDE §5.5. The party msgid is unchanged, and the
  solo msgid shows English until it is translated.
- **Guide site: keep** (B has it too, C left it out). `tools/xeen_site/story/act4.yml:124` gains "In a solo run your
  spells do work here, at half damage, and the tower's monsters cast back at half damage too." This is G's lane, or
  the orchestrator's.

Final SUMMARY ROW (A):
`| D-191 | 2026-11-26 | Darzog's Tower arrival message for a solo run (panel) | New generic Lua query evt.IsSoloRun() (Party::soloRun(), EventRuntime.cpp beside IsTurnBased, doctest); m21.yml arrival becomes two states, solo first via when: {lua: "evt.IsSoloRun()"}: "...Darzog's ward was laid against a company of casters; one alone slips through it, but not whole. Every spell you cast here strikes at half its strength, and so does every spell the tower's monsters cast at you. ..."; party text verbatim; window for both (D-90); darzog/crodo unchanged; quest_stub stub; solo playtest playtest_solo_arrival.yml; NOTES and guide act4.yml lines; A1 release first, no nil guard. 85 % | A1 (query, test), A3 (m21.yml, stub, QUESTS_FORMAT example), A8 (playtest, NOTES), G/orchestrator (site, row) |`
