# M34's Accuracy and the wells' guards: decisions (D-70)

Decider D-70, 2026-11-21. I read the following:
- D-59, D-68 and A2's stat-gate table (`output/xeen_a2_check/stat_gates_20261121.md`).
- `source/quests/m34.yml`, QUESTS Act V and the MAPS rows for X9, XD-12 and DD-18.
- The installed map Lua for every Xeen map, scanned for temporary effects and the guard each one uses. The D5 and X9 hooks in `xeen_quests.lua`, and `Xeen.usedToday` in `xeen_common.lua`.
- `EventRuntime.cpp`:
  - All event bonuses on one stat share a single field per member (`temporaryEventBonuses`), which a rest clears.
  - HP and SP additions are capped at the member's maximum.
  - With no `ForPlayer`, an event affects only the active member.
- The original Clouds events (`reference/mm4_5_world_of_xeen/unpacked/events/xeen_initial_state/maze0011.evt.json` with `text/xeen/aaze0011`), and the MM6/MM7 fountains in `reference/mmext-scripts/Decompiled_Scripts` (`mm6/OUTE3.lua` event 150, `mm7/OUT02.lua` event 218).

## Q1: M34's Accuracy 60

**DECISION: (b). X9 hands out a pair of Accuracy Boosts at Slick's shooting line, once per game. The gate stays at 60.**

- **Map and object:** X9, at the shooting line's counter (-4608, 1280). The object is a tonic crate, "Sure-Eye Tonic", under the counter.
- **What it gives:** the first click in the game gives **two Accuracy Boosts (item 245, power 10)**, the same way FD-02's embalming table and XD-15's vault give their Might Boosts (`evt.SetHeldItem` twice).
  - Each potion gives +30 Accuracy for 300 minutes. It is carried in the pack and drunk at the booth.
  - Later clicks give the else line and nothing else.
- **Text:** A3's, in Slick's voice, for example: "Slick: First round's on the house. Only the first." The else line could be: "Slick: The free round was the first one."
- **New counts:**
  - The best member has 48 + 30 = **78** with no D5 route at all, and 93 with D5's Shrine of Great Power.
  - A member at bare creation Accuracy (30) reaches exactly 60.
  - The gem budget does not change.
- **Rejected:**
  - (a) Under D-68's wording the gate does pass, at 63. But that rests on one daily buff carried through a five-hop route that no in-game text explains, at a main-quest gate.
  - (c) Lowering the number would make Accuracy the one booth held to a different standard.
  - XD-10's great skull is not a fix: it would leave the party short of gems for M34's fees.

**WHY:**
- **It matches the Might gate.** Might reaches 60 because events hand out Might Boosts (XD-08, XD-10, XD-15, FD-02). Accuracy had no such source. A pair of boosts at power 10 is the same tool at the same strength, and it adds no permanent Accuracy.
- **It works however the player got to X9.** A potion in the pack does not depend on the route, a rest or the time of day. The D5 route still helps, but the gate no longer needs it.
- **It sits right at the booth, so it cannot run out on the way.** It is in an Act V map, as A2 asked. It also follows the source's design: the Clouds carnival was meant to be passed with temporary help (MM4_CLOUDS_CONTENT §2e lists the +50 wells).
- **It removes a chain convention.** The tonic is on the main path, so segment 83 can play it honestly, and D-68's CONVENTION grant for Accuracy stops firing by itself.

**WHO ACTS:**
- **A3:**
  - In `m34.yml`, add the hook `m34.tonic`:
    - `once` on the next free bit of M34's block (111686 if it is free);
    - the two-potion gift as described above;
    - the text and the else text.
  - Optionally add one clause to the `carnival` autonote ("Slick keeps a free round of tonic under the shooting line").
  - Regenerate.
  - Segment 83: before the Accuracy game, click the crate and have the member who will shoot drink one potion. Rerun 83, then 83 with `--reload`.
- **A5:** On X9, add the `deco:tonic_crate` click at the shooting line's counter, calling `m34.tonic`. Playtest:
  - the first click gives two Accuracy Boosts;
  - a second click gives the else line only;
  - after drinking one, a member at 30–48 Accuracy wins the Accuracy game.
- **A2:**
  - Count X9's tonic as event-given temporary help in `balance.py --gates`. The `m34.accuracy_game` row becomes 78 with no shortfall, and the D5 shrine is listed as extra.
  - Add the ledger row "X9 Sure-Eye Tonic: 2 Accuracy Boosts, power 10, once per game (temporary)".

**REVERSIBLE:** Yes. It is one hook, one click and one table row.

## Q2: Temporary wells with no guard

**DECISION: Every event that grants a temporary effect is used once a day by the party, through `Xeen.usedToday` / `Xeen.markToday`, and the effect goes to every member present. Bonuses from different sources keep adding together.**

1. **The rule.** It covers every temporary stat, resistance, armour class or level bonus: anything that lasts until rest.
   - The guard is `Xeen.usedToday("<map>_<thing>")`, with `Xeen.markToday` on use. That is the D5 and X9 pattern (D-49, D-59). Sketches can write it as `condition: {not: {lua: ...}}` plus `lua:` effects.
   - The effect is preceded by `evt.ForPlayer(Players.All)`.
   - A second use the same day gives the source's refusal line and nothing else. Water says "The water is cool and refreshing." (aaze0011:17). Shrines and stones say "No one seems to be listening." (aaze0011:21) or the map's own line.
   - Gain texts say "until you rest". They do not say "until tomorrow" or "today".
2. **Bonuses still add up (D-59 stands).** Different sources add together. The same source does not repeat within a day.
   - Replacing instead (MM6's `Set`, or the original's rule of "only if this stat has no temporary bonus") does not suit this engine. Because each stat has one shared bonus field per member, the order of visits would matter: a +5 cairn would cancel a later shrine. It would also undo D-59's +10/+15/+20 ladder.
3. **A guard that never resets is wrong for a temporary effect.**
   - The MapVar = 1 guards and the PlayerBit guards on temporary effects become daily. They say "come back tomorrow" but never reset, so they are really once per game.
   - Once per game is rejected as the rule: it wastes a temporary source after one use, and it contradicts D-49 and D-59.
4. **HP and SP restorations are exempt.** They are capped at maximum, so they cannot build up (MM6's restoring fountains repeat in the same way). They may stay unguarded. A restoration whose text promises "tomorrow" uses the daily helper.
5. **Known leftover, accepted as in D-49 and D-59:** a party that waits past midnight without resting can drink again. The amounts are small and cost game days.
   - If a later decider wants this closed, the fix is one engine rest counter plus a change to `Xeen.usedToday`'s body. All sources go through that one helper, so one change covers them all.

**WHY (the source and MM6–8):**
- **The original did not stack.** The Clouds' Well of Personality at (0,0) in maze0011 reads as follows:
  - *Who will drink?*
  - If that member's temporary Personality is 0, they get +50 and the line "+ 50 personality".
  - Otherwise: "The water is cool and refreshing."
  - The Shrine of Magic at (15,0) uses the same pattern with "No one seems to be listening."
  - So each member could drink once until rest, and a well never added to an existing temporary bonus on that stat.
- **MM6 and MM7 do not stack either:**
  - MM6's New Sorpigal fountain checks `Cmp(MightBonus, 10)` → "Refreshing!", else `Set(MightBonus, 10)`.
  - MM7's Harmondale well uses a player bit, then `Add`.
- **The repeat-click stacking is our bug, not Xeen's.** The OpenEnroth behaviour cited in the question does not justify it.
- **Party-daily with all members** is the project's existing form, uses an existing helper, and is fair to the whole party without a "who will drink" prompt.

**WHO ACTS (each lane edits its maps' sketches and regenerates; key names `<map>_<thing id>`):**
- **A5:**
  - **X4** (unguarded):
    - Well of Might
    - Quintain
    - Herders' well (+5 Endurance)
    - Herders' well (`savannah_well`, +5 Might)
    - Wayfarers' well
    - Standing stone
    - Climbers' cairn
    - Wind stone
  - **D3** (unguarded):
    - Wayside shrine of the desert sun
    - Omid's deep well
    - The Wrath Spring
    - Fountain of Great Protection
    - The great oak
    - Pilgrims' cairn
    - The caravan well
  - **X3:**
    - Wayside shrine and Marsh Well (unguarded);
    - the Well, event 56: Personality +10 once qbit 112141 is set. Keep the qbit as the condition that opens the well and add the daily guard.
  - **X6** (PlayerBit, never resets; these become daily):
    - The Well of Accuracy: also correct its text to "until you rest";
    - The sun stones;
    - Caravan cairn.
  - **X7:** Shrine of Fire (PlayerBit) and The cairn of the unreturned (MapVar) become daily.
  - Playtest on X4: click the quintain twice and check the gain is +5 for every member, not +10. After a rest the bonus is back to 0. The next day it gives +5 again.
- **A6:**
  - **D1:** A wayside shrine of Mok, The prayer shrine and The old west well change from MapVar to daily.
  - **D2:** The Glimmer Pool (unguarded).
  - **D4:** Fountain of Great Resilience, Fountain of Great Magic and The coven's cauldron change from MapVar to daily (their texts say "tomorrow").
  - **D6:** Fountain of Super Resilience and The Well of Warding change from MapVar to daily.
  - **X5** (Hot spring, Waters of Great Magic) and the restorations in D2 (fairy ring, Dewdrop Spring) need nothing.
  - Playtest the D1 prayer shrine: once today, again tomorrow.
- **A7/A8:** Nothing. The only effects the scan finds in dungeons are restorations (DD-19's Font, FD-04's Fountain, XD-07's Well). Any new temporary bonus follows rule 1.
- **A2:**
  - `balance.py --gates` gains a guard check: any event or hook with `AddValue(*Bonus | ArmorClassBonus | *Resistance*Bonus | level)` and no `Xeen.usedToday` fails the check and is listed. Today's 25 cases are expected to clear once the A5 and A6 changes land.
  - Delete the "no guard" note from the table. The gate sums do not change, because each source was already counted once.
- **A3:** Nothing in the quest hooks; D5, X9 and P1–P4 already follow the rule. Segment 83 only uses D5 if it plays it.

**REVERSIBLE:** Yes. Each change is a guard around existing effects, and every source goes through one helper, so the rule can be changed in one place.

## SUMMARY ROW

| D-70 | 2026-11-21 | M34 Accuracy; temporary wells' guards | M34 stays 60; X9's shooting line gives two Accuracy Boosts (245, power 10) once per game (m34.tonic): 78 without D5. Every temporary source: once a day for the party (`Xeen.usedToday`), all members; sources stack, never repeat; capped HP/SP restores exempt; MapVar/PlayerBit "tomorrow" guards become daily. Detail: `reviews/D70_DECISION.md` | A3, A5, A6, A2 |

---

Notes for the caller:
- **D1's "come back tomorrow" guard is not daily.** D1's map script (`/home/pjasicek/github/OpenYAMM/assets_dev/worlds/xeen/events/maps/xeen_d1.lua`) sets `MapVar(n) = 1` and nothing ever resets it. D4 and D6 use the same pattern, and X6 and X7 use per-character PlayerBits that never reset. So those sources are once per game, although their texts promise "tomorrow". Only the hooks using `Xeen.usedToday` (D5, X9, P1–P4) are truly daily.
- **The scan found more unguarded sources than A2 listed:** D3's Wayside shrine (Fire resistance) and Fountain of Great Protection (AC +10), and X3's Wayside shrine, Marsh Well and Well (event 56). Restorations are capped at maximum, so I left them out.
- **The original Xeen reading comes from the raw opcodes, since no decompiler is kept.** The opcodes are WhoWill, If3 on the stat's temporary value, TakeOrGive, then the "refreshing" text otherwise. The gain and refusal texts confirm that reading.
