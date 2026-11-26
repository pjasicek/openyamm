# D-193 and D-194: spell damage on a warded map in a solo run (decider, 2026-11-26)

Brief: [DECIDER_BRIEF_20261126b.md](DECIDER_BRIEF_20261126b.md), "Context: Darzog's Tower and U-18". Read-only
decision; no game runs. Code read (working tree, U-18 uncommitted): `game/maps/MapRuntimeRestrictions.h`,
`game/party/PartySpellSystem.cpp` (`casterSpellDamage`, the cast's `rollSpellDamage`, `damagePreview`,
`isSpellOutdoorOnly`), `game/gameplay/GameplayProjectileService.cpp/.h` (`resolveProjectilePartyImpactDamage`,
`resolveEventProjectileDamage`, `partyWorldSpellDamage`), `game/gameplay/ArmageddonSpell.cpp`
(`armageddonMonsterDamage`, `applyArmageddonToParty`), both worlds' `castEventSpell`, Fire Spike trap and Armageddon
detonation code, `game/ui/GameplayHudOverlaySupport.cpp` (`updateSpellInspectOverlay`, `spellInspectDamageLine`),
`game/gameplay/GameplayScreenRuntime.cpp` (`openSpellbookOverlay`), `tests/GameplayProjectileServiceTests.cpp`, XD-12's
scene and Lua, `world.yml openAirMaps`, the solo README's "No-magic maps", U-18's row in DECISIONS.md.

## D-193: spells from traps and map events in a solo run on a warded map

**DECISION:** In a solo run on a map with `solo_spell_damage_percent`, every spell's damage takes the map's share,
whoever or whatever casts it. Two code changes, nothing else:

1. **Map-event spells: halved.** `GameplayProjectileService::resolveProjectilePartyImpactDamage`, the `eventSource`
   branch: an event *spell* (`spellId != 0`) returns
   `MapRuntimeRestrictions::scaledSpellDamage(resolveEventProjectileDamage(spellId, skillLevel), input.spellDamagePercent)`.
   An event *missile* (`spellId == 0`: thrown rocks, arrows, anything that carries its own damage) keeps its full
   damage, as a monster's attacks do. Both worlds already set `spellDamagePercent` on that input
   (`IndoorWorldRuntime` ~8476, `OutdoorWorldRuntime::resolveProjectilePartyImpactDamage`), and the same number serves
   the party and every actor the spell hits, so this one branch covers `evt.CastSpell` everywhere with no world code.
   Event *buff* spells (`tryApplyEventSpellBuffs`) roll no damage and are untouched.
2. **Armageddon's strike on the party: halved like its strike on the monsters.** `applyArmageddonToParty(state, party,
   int mapSpellDamagePercent)`: each member takes `MapRuntimeRestrictions::scaledSpellDamage(50 + skill, percent)`.
   The four callers (indoor and outdoor `resolveArmageddonDetonation`, own party and guests) pass `spellDamagePercent()`,
   the value they already pass to `armageddonMonsterDamage`. Header comment in `ArmageddonSpell.h` says so.
3. **Trap spells the party set (Fire Spike): no change.** Both worlds' Fire Spike trap triggers already go through
   `partyWorldSpellDamage(..., spellDamagePercent())`.
4. **Not spells, not halved:** `evt.DamagePlayer`-style event damage, chest traps, falls, monster melee and bows (the
   README's "melee and bows unchanged").

Comments and docs to match, same commit: `MapRuntimeRestrictions.h` (`soloSpellDamagePercent`: "... the solo
character's (spells, scrolls, wands, Armageddon's strike on its own party), the monsters' and the map's event spells
alike"); `GameplayProjectileService.h` `spellDamagePercent` ("its attacks and an event's missiles keep theirs");
the solo README's "No-magic maps" (add "map events' spells in `resolveProjectilePartyImpactDamage`, Armageddon's own
strike in `applyArmageddonToParty`"); XD-12 `L4/NOTES.md` "The ward by run" one clause ("and every event spell").

Test (doctest, `tests/GameplayProjectileServiceTests.cpp`, the existing "a map's spell damage share ..." case, renamed
"... halves a monster's and an event's spells, not attacks, event missiles or the party's"): keep the existing
event-missile line (`eventSource`, `spellId` 0, carried 40 → 40); add an event spell (`sourceKind` Event,
`eventSource`, `spellId` Fire Bolt, `skillLevel` 10: 20 at 100 %, 10 at 50 %); add an `applyArmageddonToParty` case
(one member, skill 10, 50 %: loses 30; at 100 %: 60). Run with `--test-case='*share*'` and the Armageddon tests.

**WHY:**
- U-18 is the user's own wording: in a solo run on the tower "a solo run deals and takes half spell damage", and the
  brief's "same with monsters casting spells there". The ward is a property of the place, not of the caster; a fire
  bolt from a trap is as much a spell in Darzog's ward as a monster's. `MapRuntimeRestrictions.h` already describes the
  key as "every spell's damage on the map"; today the code makes two exceptions the comment does not name.
- Armageddon: the solo caster's strike on the monsters is already halved (`armageddonMonsterDamage`); leaving its strike
  on the caster full would make the spell twice as costly there as anywhere else, the opposite of U-18's intent (give a
  lone mage a fair tower). MM's Armageddon hits caster and monsters for the same 50 + skill; halving both keeps that
  equality. (On XD-12 itself it cannot be cast: the tower is a plain BLV, not in `world.yml openAirMaps`, and
  `isSpellOutdoorOnly` refuses Armageddon. The change is for the key's meaning on any future warded open-air or outdoor
  map, and costs one parameter.)
- Today's reach on XD-12: none of its events casts a spell (its `trap1`–`trap5` are drop hatches, chests are
  `trap_level: 0`); Xeen's only `evt.CastSpell` traps are DD-02 and DD-14, unwarded. So nothing on the tower changes
  for a player now; the rule keeps a later trap or a MAW overlay on the map honest without a second look.
- Risk to MM6–MM9: none. `spellDamagePercent()` is 100 on every map without the key and in every party run, and
  `scaledSpellDamage(d, 100)` returns `d` unchanged; only XD-12 has the key.
- Rejected: leave event spells at full (the code's current comment). It keeps a hidden exception to a rule the player
  is told in one line ("every spell at half"), with nothing gained. Rejected: halve event missiles too. They are not
  spells, and monsters' attacks are not halved either; the line between "spell" and "not" is `spellId`, as it already
  is in the same function. Rejected: block event spells in a party run (the ward "kills every spell"): not asked, and a
  map author's trap is the map's design, not the party reaching for magic.

**WHO ACTS:** A1 (engine), small: ~10 lines in `GameplayProjectileService.cpp` and `ArmageddonSpell.cpp/.h` plus four
call sites, three comments, two doc lines, three test checks; one game build and the unit tests. No map rebuild.

**REVERSIBLE:** yes. Confidence 80 %.

**SUMMARY ROW:** `| D-193 | 2026-11-26 | Spells from traps and map events in a solo run on a warded map (decider) | Every spell takes the map's share: event spells (resolveProjectilePartyImpactDamage's eventSource branch, spellId ≠ 0) and Armageddon's strike on its own party (applyArmageddonToParty gets spellDamagePercent(), as armageddonMonsterDamage has) are halved; event missiles (spellId 0), DamagePlayer, chest traps and falls stay full; Fire Spike already halved. Nothing on XD-12 changes today (no event spells; Armageddon refused in its BLV); 100 % everywhere else. Test in GameplayProjectileServiceTests. 80 % | A1 |`

## D-194: the spellbook's damage preview on a warded map in a solo run

**DECISION:** Show the numbers the cast will deal, plus one line saying why. The preview has access to the map: the
spell inspect overlay runs on `GameplayScreenRuntime`, whose `worldRuntime()` (the shared `IGameplayWorldRuntime`) the
spellbook already asks for `allowsSpellcasting()` in `openSpellbookOverlay`; both worlds implement
`spellDamagePercent()`. No indoor/outdoor code is touched.

1. `PartySpellSystem::damagePreview(party, caster, spellTable, spellId, int mapSpellDamagePercent)`: the new argument
   replaces the literal `100` in its three `casterSpellDamage(...)` calls (the same function and order the cast uses,
   so the shown range is the rolled one at the same share, minimum 1). Header comment: "... with the caster's
   spell-damage share and the map's (IGameplayWorldRuntime::spellDamagePercent)".
2. `GameplayHudOverlaySupport::updateSpellInspectOverlay`: `const int mapPercent = context.worldRuntime() != nullptr ?
   context.worldRuntime()->spellDamagePercent() : 100;` passed to `damagePreview` and to `spellInspectDamageLine`.
3. `spellInspectDamageLine(damage, mapPercent)`: when `mapPercent != 100`, after the damage line (and after the
   critical-hit line if any), a new line in the reset (ivory) colour, the number in the number colour as the crit
   line does: `Engine::tr("Spells deal {percent} % of their damage here.", {{"percent", ...}})`. Engine text, generic
   (no Xeen or Darzog name: any world can set the key); it reaches `engine.pot` at the release check's `l10n.py extract`
   (D-173's path) and zh-cn's todo list then.
4. Test (doctest, beside the existing spell preview tests in `tests/MawSpellClassTests.cpp` or a new case in
   `tests/SpellRegressionTests.cpp`): Standard rules, a sorcerer with Fire Magic, Fire Bolt's `damagePreview` at 100
   and at 50: each of minimum, average and maximum at 50 equals `scaledSpellDamage(value at 100, 50)`.

A party run (or any map without the key) gets 100 from `spellDamagePercent()`: the preview and its text are exactly as
today.

**WHY:**
- The preview's job (its header: "as a cast rolls it") is to tell the player what the spell will do. In the one place
  the share applies, full numbers are wrong by a factor of two, and a solo mage choosing between Fire Bolt and a sword
  is exactly the player who reads them. Halved numbers alone would look like a bug ("my Fire Bolt shrank"); the line
  names the cause in the same window, and costs one string.
- The brief's premise ("it has no access to the map") does not hold: the overlay's context is
  `GameplayScreenRuntime`, and `worldRuntime()` is already used next door for the spellbook's no-magic refusal. The map's
  share is read through the shared virtual, so there is no new indoor/outdoor divergence and no new plumbing.
- `damagePreview` already calls `casterSpellDamage` with a map-percent argument hard-wired to 100; making it a parameter
  is the smallest change and keeps preview and cast on one function.
- Rejected: leave it (wrong numbers in a place the user just retuned for solo players). Rejected: a note only, with full
  numbers (the player still has to halve in their head, and the crit line already sets the pattern of showing the
  dealt figure). Rejected: a Xeen-voiced line ("Darzog's ward ...") in engine C++: the key is generic; Xeen's voice
  belongs to the arrival text (D-191).
- Not in this decision, noted for A1: MAW's monster inspect (`MawMonsterInspect.cpp`, `numbers.spellDamage`) shows a
  monster's spell damage without the map's share; the same rule would apply if a player pins it (MAW is not on XD-12's
  usual path, so no change now).

**WHO ACTS:** A1 (engine), small: one signature, one caller, ~8 lines in the inspect line, one string, one test. Can go
in the same commit and build as D-193.

**REVERSIBLE:** yes. Confidence 85 %.

**SUMMARY ROW:** `| D-194 | 2026-11-26 | The spellbook's damage preview on a warded map in a solo run (decider) | Show the dealt numbers plus a line: PartySpellSystem::damagePreview takes the map's percent (replacing the hard-wired 100 in its casterSpellDamage calls), updateSpellInspectOverlay reads it from context.worldRuntime()->spellDamagePercent() (the shared interface the spellbook's refusal already uses; no world code), and below the damage line, when ≠ 100: "Spells deal {percent} % of their damage here." (engine tr()). Party runs unchanged. Doctest: Fire Bolt preview at 50 = scaled preview at 100. 85 % | A1 |`
