# D-191, panelist C (round 1): the arrival message for a solo run

Read: DECIDER_BRIEF_20261126b.md, AGENT_GUIDE §6 and "Design questions", DECISIONS D-90, D-180 to D-190, U-16 to U-18,
QUESTS_FORMAT.md §4.2 and §7, `source/quests/m21.yml`, `events/maps/xeen_xd12.lua`, `briefs/xd12/L4/NOTES.md`
("How M21 plays", "No magic", "The ward by run"), `solo_action/README.md` ("No-magic maps"),
`game/maps/MapRuntimeRestrictions.h`, `game/events/EventRuntime.cpp` (the Lua registrations), `tools/xeen/gen_quests.py`
(hook states, text ids), `languages/zh-cn/text/xeen.po` (the arrival's msgid). No game runs.

## DECISION

Two texts, chosen at run time by a new generic run-mode query; the window stays.

1. **A1: one Lua query, `evt.IsSoloRun()`.** In `game/events/EventRuntime.cpp`, beside `luaIsTurnBased` (same shape,
   same `evt.` table): `luaIsSoloRun` pushes `readableParty(pLuaState) != nullptr && pParty->soloRun()`, registered as
   `registerLuaFunction(pLuaState, "IsSoloRun", luaIsSoloRun)` with a one-line comment
   (`// evt.IsSoloRun(): true in a solo run (Party::soloRun), the run mode a map's runtime_restrictions read.`).
   Unit test in `tests/EventScriptingTests.cpp`, beside the IsTurnBased case: "evt.IsSoloRun is true only in a solo
   run" (a party with `setSoloRun(false)` then `true`; status lines `party`, `solo`). One sentence in
   `devdocs/solo_action/README.md` "No-magic maps": "Map Lua can tell a solo run with `evt.IsSoloRun()` (Darzog's
   Tower's arrival text)." No scene key, no save field, no change to any MM6–MM9 script.
2. **A3: M21's `arrival` hook gets two states** in `assets_dev/worlds/xeen/source/quests/m21.yml` (the top-level
   `text:` moves into the last state; `map`, `where` unchanged; no `status:`, it stays a window):

   ```yaml
   arrival:
     map: XD-12
     where: "the first arrival (built: evt:arrive, a one-shot timer); replaces the map's message"
     # The two texts follow the scene's runtime_restrictions (U-18): a party casts nothing here, a solo run casts at
     # solo_spell_damage_percent 50, the monsters too. Change both together (D-191).
     states:
       - when: {lua: "evt.IsSoloRun()"}
         text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Darzog's ward was spun to catch a company of casters, and one alone slips through it, but not whole. Every spell here strikes at half its strength, yours and the tower's alike. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
       - text: "Darzog's Tower. The Skeleton Key turns, and the door that has been sealed since Crodo vanished swings in on cold air. Artemus was right about the Baron: somewhere above, Crodo still lives. And the air itself is wrong. Every spell you reach for dies before it is shaped. Here you fight with steel. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
   ```

   The party text is byte-identical to today's (its msgid, playtests and the NOTES quote keep matching). Then the
   usual build (`gen_quests` through `build_world.py`, `quests.py` clean), `tools/l10n.py` to refresh `xeen.pot`
   (one new msgid; zh-cn shows English until translated). Check the diff: `xeen_quests.lua`'s `m21.arrival` gains
   `if evt.IsSoloRun() then ... return end`; M21's later text ids shift by one (ids are per-file counters; the .po keys
   on the English text, so nothing is lost; A3 confirms no other file's ids moved).
3. **Nothing else changes.** `xeen_xd12.lua` still calls `XeenQuests.hook("m21.arrival")` (no map rebuild). The
   other XD-12 lines stay, being true for both runs: Darzog's death ("His ward on your spells stays: it is in the
   stones."), Crodo ("Darzog's ward still holds him, but it is fading..."), the journal (Darzog's own boast "no spell
   leaves this tower, and no spell enters it but mine"). NOTES.md "How M21 plays" 1 and the last sentence of "The ward
   by run" ("The arrival text still says spells die here; Lua cannot tell a solo run.") are rewritten to name the two
   texts and `evt.IsSoloRun()`.
4. **Order.** A1's merge point releases the binary first; A3 installs the m21.yml change after it (a build without
   the binding would raise a Lua error at the tower's first arrival). No `evt.IsSoloRun ~= nil` guard: that is the
   compatibility fallback AGENTS.md forbids.

## WHY

- **The text must be true for the player who reads it.** U-18 split the tower's rule by run; the arrival is the one
  place the game explains that rule in the world's voice (the engine's refusal still says "underwater", NOTES "No
  magic"). A solo mage told "Here you fight with steel" is told the opposite of what the map does, on a required
  main-quest map, right after a player complained about exactly this map.
- **The query belongs to the engine, once and generically.** `Party::soloRun()` is the state every U-18 rule reads
  (`allowsSpellcasting(soloRun)`, `spellDamagePercent(soloRun)`); exposing it read-only to Lua is a few lines, of the
  same kind as `evt.IsTurnBased()`, adds no cost to MM6–MM9 (registered, never called there), no save change, and keeps
  presentation in content, where QUESTS_FORMAT already has the machinery: hook `states:` with `{lua: "..."}`
  conditions (m24, m33 use them; `gen_quests.py` emits them, `quests.py`'s window and touch checks read states).
- **Whole sentences, two literals.** Each state is one full `NPCText(id, english)` literal (LOCALIZATION.md: no joined
  pieces); the solo text repeats the shared sentences rather than splicing a middle sentence in.
- **D-90 holds.** The arrival is no find, touch site or death; it is a once-per-game long text read on first entry, and
  both runs keep it a window of the same length. A status line could not hold either text (6 s at most).
- **Voice.** Short, deadpan, played straight (STORY_AND_ATMOSPHERE "Tone"); the solo text explains the rule in the
  world: the ward is made for a company, a lone caster slips through it weakened, and "yours and the tower's alike"
  warns that the monsters cast at a solo run (they do not at a party: `allow_monster_spellcasting` lifts with the solo
  lift). "Half" is the scene's 50; the m21.yml comment ties the two together.

Rejected:

- **One text true for both runs** (e.g. "Darzog's ward stills a company's spells and thins a lone caster's"): a party
  reads a rule about lone casters it can never use, and loses the plain "fight with steel" warning that matters most to
  it; a vaguer line ("your spells falter here") is true for neither run's exact rule.
- **`GetPartyMemberCount() == 1`** (exists, no engine work): a normal party can have one member (`Party::isFull` is
  `MaxMembers` only outside a solo run), and the ward follows `soloRun()`, not the head count; the text would lie to a
  one-member party run.
- **An engine-side line** (a scene key such as `solo_arrival_text`, or a generic status line on entering a map whose
  restrictions differ by run): moves world text into engine/scene data for one map, needs a new key in the scene
  schema and Map Studio, and duplicates the hook's lore window. Worth having only if more maps take
  `allow_spellcasting_solo`; today only XD-12 does.
- **A map-rule query instead of a run-mode query** (`evt.CanCastSpellsHere()`, `evt.MapSpellDamagePercent()`): would
  make the text follow the scene's values automatically, but the solo text states three facts (casting allowed, half
  damage, monsters cast), so it needs two or three queries for one line; `evt.IsSoloRun()` is one generic fact with a
  plain comment tying the text to the scene. Acceptable as an alternative if the other panelists prefer it.
- **Leave it** (U-18's interim note): the user's own ruling exists because of solo players; a false arrival text
  undercuts it.

## WHO ACTS

- **A1**: `evt.IsSoloRun()` + unit test + the README sentence, next merge point (about 20 lines, small).
- **A3**: m21.yml states, rebuild, `quests.py`, `l10n.py`, after A1's release (small, under an hour).
- **A8 (or the orchestrator, who wrote U-18's note)**: the two NOTES.md sentences. Orchestrator: the D-191 row
  (U-18's "unchanged (Lua has no solo query)" is superseded by it).

## REVERSIBLE

Yes: a Lua binding nobody else calls and one hook's states; reverting is deleting both. Confidence 85 %.

## SUMMARY ROW

| D-191 | 2026-11-26 | Darzog's Tower arrival message for a solo run (panel) | New generic Lua query `evt.IsSoloRun()` (`EventRuntime.cpp`, beside `evt.IsTurnBased`; unit test; MM6–MM9 untouched); m21.yml `arrival` becomes two states: `when: {lua: "evt.IsSoloRun()"}` "...And the air itself is wrong. Darzog's ward was spun to catch a company of casters, and one alone slips through it, but not whole. Every spell here strikes at half its strength, yours and the tower's alike. ..." and the party text unchanged; both a window (D-90: a long first-arrival text); A1's release first, no nil guard; other XD-12 lines stay (true for both) | A1 (binding, test), A3 (m21.yml, l10n), A8/orchestrator (NOTES) |

## Round 2

Read a.md and b.md. All three agree on the shape: two hook states, the party text word for word, the window kept
(D-90), no engine-side line, `GetPartyMemberCount() == 1` rejected, darzog/crodo/journal lines unchanged. Where we
differ:

| Point | A | B | C (round 1) | Final position |
| --- | --- | --- | --- | --- |
| The query | `soloRun` field on `evt.RulesetInfo()` | `evt.IsSoloRun()` | `evt.IsSoloRun()` | **Concede to A.** `evt.RulesetInfo()` (`EventRuntime.cpp` `luaRulesetInfo`) already reports the run's options to map Lua (`dimensionRun`, `challengeMode`, read by MAW's `d22_maw.lua`, `Global_maw.lua`), and a solo run is a ruleset option (`standard:solo`, `maw:solo`); one more field (table size 5 → 6, the comment lists it) avoids a second way to read the same kind of fact. Bonus: a missing field reads `nil`, so the yml can land in the same merge point without a Lua error, which removes my "A1 first" ordering constraint without any guard. |
| Condition form | new `{solo_run: true}` key in `gen_quests.py` `CONDITION_KEYS` | `{lua: ...}` | `{lua: ...}` | **Keep `{lua: "evt.RulesetInfo().soloRun"}`** (merge with B's doc line): one use today, and `{lua}` already covers it with no generator, audit or format change; QUESTS_FORMAT §4.2's `{lua}` row gets the example ("`evt.RulesetInfo().soloRun` for a line that differs in a solo run, M21's arrival, D-191"). A named key can come with a second user. |
| Solo text | three sentences, repeats "half" twice | "Every spell you shape comes out at half its strength, and so does every spell cast at you. The ward was laid against a company; one alone slips half through it." | "...spun to catch a company..., but not whole. Every spell here strikes at half its strength, yours and the tower's alike." | **Concede to B's wording, verbatim.** It states the rule first and plainly ("every spell cast at you" is clearer than my "the tower's"), gives the in-world reason in one short line, and is the shortest of the three (Xeen's short, deadpan voice). Keep my m21.yml comment tying "half" to the scene's `solo_spell_damage_percent: 50`. |
| Solo playtest | none | A8 `briefs/xd12/L4/playtest_solo_arrival.yml`, `new_game_flow: {start_map: xeen_xd12.blv, ruleset: "standard:solo"}`, assert "comes out at half its strength", cast once if U-18's test doesn't | unit test only | **Concede to B (merge).** The doctest proves the field, not that the built hook picks the solo state on the real map; the scenario form exists (`tests/scenarios/README.md`, `standard:solo`), and it also covers U-18's solo lift on XD-12 in a game run. Party playtests keep their "Every spell you reach for dies" assert. |
| Stub | — | `evt.IsSoloRun` stub in `tools/xeen/quest_stub.py` | — | **Merge:** `quest_stub.py` has no `evt.RulesetInfo`; add `function evt.RulesetInfo() return {soloRun = Stub.solo == true} end` so the stub run can call the condition. |
| Unit test | doctest beside "Event scripts see the challenge mode in evt.RulesetInfo (Q8)" (`tests/MawChallengeModeTests.cpp`) | doctest in `EventScriptingTests.cpp` | same as B | **Concede to A:** the test sits with the other `RulesetInfo` field test; it checks `setSoloRun(true)` → `true`, a default party → `false`. |
| Guide site | `tools/xeen_site/story/act4.yml` M21 line gains a solo sentence (G) | same (orchestrator) | not raised | **Concede:** the walkthrough says "No spell works anywhere in the tower" and would be the next false line; use B's sentence "In a solo run your spells do work here, at half damage, and the tower's monsters cast back at half damage too." |
| `l10n.py` | run `extract` now | leave for the release (AGENT_GUIDE §5.5) | run now | **Concede to B:** the guide's release step owns it; the new msgid is picked up then. |

Final converged decision (my vote): A1 adds `soloRun` (`pParty != nullptr && pParty->soloRun()`) to
`evt.RulesetInfo()`, doctest beside the Q8 RulesetInfo test, a solo README line; A3 turns m21.yml `arrival` into two
states, `when: {lua: "evt.RulesetInfo().soloRun"}` with B's solo text first and today's text last, the stub line, the
QUESTS_FORMAT example, `build_world.py`/`quests.py`/`quest_stub.py`; A8 the solo playtest and NOTES "The ward by run"
sentence; orchestrator the act4.yml sentence and the D-191 row. Reversible, 85 %.
