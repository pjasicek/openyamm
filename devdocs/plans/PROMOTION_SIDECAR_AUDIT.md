# MM6/MM7/MM8 promotion audit

Status: sidecar repairs implemented. The audit findings below describe the pre-fix behavior.
Generated `assets_dev/engine/events/Global.lua` and the shared class-comparison API remain unchanged.

## Confirmed reproduction

The user promoted Nathaniel Roberts through Vetrinus, recruited another Necromancer using `player add necromancer`,
gave the new recruit a Lich Jar, and attempted Lathean's repeat promotion. It failed with Nathaniel in the active
party and succeeded after removing him. The console resolves Necromancer to the correct merged class (44).
This confirms that the already-promoted Lich is the blocking candidate, rather than the console-created recruit.

Event 738 emits its introductory message before validating jars. The sidecar now validates first and emits one
outcome message, identifying the eligible character's party slot when a jar is missing.

## Root cause

Generated promotion handlers use `IsAtLeast(ClassId, sourceClass)` before changing the class.
`EventRuntime::classIdMatchesPromotionFamily` delegates to `ClassSkillTable::classIdIsAtLeast`, which accepts
the same class kind at any equal or higher promotion step. It is not an exact class comparison.

Consequently, existing promoted characters can be selected for promotion again. In MM8, an existing Lich
is selected by the Necromancer check, and event 738 demands another jar from that character. The jar held
by the new Necromancer cannot satisfy that per-character check.

The local OpenEnroth `Character::CompareVariable` implementation compares `VAR_Class` by equality.
MMMerge's `Scripts/Global/PromotionTopics.lua` also uses exact source classes or explicit source-class lists.
Our existing Lua `PlayerClassMatches` and `PromotePlayers` helpers already implement exact matching.

## MM8

All eight generated promotion families use the broad check in both initial and repeat handlers:

| Promotion | Initial event | Repeat event | Consequence |
| --- | --- | --- | --- |
| Dark Elf → Patriarch | 25 | 733 | Existing Patriarch selected again |
| Troll → War Troll | 36 | 734 | Existing War Troll selected again |
| Knight → Champion | 58 | 735 | Existing Champions selected; Black Knights can be changed to Champions |
| Dragon → Great Wyrm | 62 | 736 | Existing Great Wyrm selected again |
| Minotaur → Minotaur Lord | 71 | 740 | Existing Minotaur Lord selected again |
| Cleric → Priest of Light | 81 | 737 | Existing promoted clerics selected; dark/high priests can change class |
| Necromancer → Lich | 89 | 738 | Existing Liches demand and consume new jars |
| Vampire → Nosferatu | 90 | 739 | Existing Nosferatu selected again |

Selection alone is often invisible when setting a class to itself. These other handlers do not all have
the Lich's jar refusal, so this is not eight identical promotion blockers. The class changes across
MM6/MM7 branches are the more serious additional consequence.

Existing tests cover initial promotion and inclusion of party member zero in repeat promotions. They do
not cover a mixed party containing existing promoted classes and newly eligible recruits.

### First-character honorary completion gates

Events 733, 737, 738, 739 and 740 select Member0 before checking their honorary award fallback (20, 31, 35, 33 and 29).
The user confirmed that Member0 is the permanent main character and cannot be dismissed. Under that invariant,
this is valid completion proof, including quests completed before recruiting a member of the promoted class.
The repair preserves these gates. No new completion flags or save migration are introduced.

## MM7

The active `Global_mm7_mmmerge.lua` sidecar replaces all 27 generated class-changing promotion handlers
(events 795 through 853). Ordinary promotions call `MM7.CompletePromotion` and then `PromotePlayers` with
exact source classes. Completion QBits distinguish initial party rewards from rewards for later recruits.

The Lich handler (847) separately accepts exact classes 43, 44 and 47, processes each character's jar,
and calls `ApplyLichTransformation`. Existing Liches are not promotion candidates. An extra MM7 jar on
another class can be exchanged for the honorary reward; that is present in the MMerge reference too.

No instance of the MM8 promoted-class matching bug was found in the active MM7 promotion handlers.
The generated MM7 handlers still contain broad checks, but the sidecar supersedes them.

## MM6

The cleric sidecar handlers (1349 and 1351) already use exact class matching and select the merged
High Priest class (50). The other ten class-changing handlers remain generated:

| Family | First event | Second event | Additional consequence |
| --- | --- | --- | --- |
| Paladin | 1327 | 1329 | A Hero/Villain can be downgraded to Crusader; Villain can become Hero |
| Sorcerer | 1371 | 1373 | Advanced sorcerers can be downgraded to Wizard |
| Knight | 1382 | 1384 | Champion/Black Knight can be downgraded to Cavalier |
| Archer | 1405 | 1413 | Master Archer/Sniper can be downgraded to Warrior Mage |
| Druid | 1678 | 1679 | Arch Druid/Warlock can be downgraded to Great Druid |

The second steps also admit existing final classes, including opposite branches. This is particularly
relevant to a merged party that arrives in Enroth after promotions elsewhere.

There is a separate data/behavior mismatch in event 1373: its text promises Master Wizard, but it assigns
Arch Mage (46). The merged class registry and MMerge promotion reference specify Master Wizard (51).

MM6 repeat promotion handling also lacks the MMerge completion-QBit branches and repeat-topic routing.
For example, a consumed unique promotion item can still be required by the generated second-stage handler.
Exact class matching alone will not implement repeat promotions for new recruits after the original quest.
The ordinary NPC route also switches to dialogue-only finished topics, such as event 1330 after Hero promotion
and event 1352 after High Priest promotion. Repairing the class-changing handler alone does not make later
promotions reachable: the first-stage and finished-topic routes must also offer the appropriate completed promotion.

## Implemented sidecar repair

1. Added `assets_dev/worlds/mm8/events/Global_mm8_promotions.lua` with explicit replacements for all 16
   initial/repeat handlers. Initial quest items are consumed once from the party. Completed first handlers also
   avoid replaying the quest reward or demanding already-returned items.
2. Eligibility uses `PartyMembers` and `PlayerClassMatches`. Knight/Cavalier and Cleric/Priest are explicit source
   lists; existing final and opposite-branch classes are excluded. The class mutation still uses `SetValue(ClassId, ...)`
   to retain the existing resource refresh, Lich transformation, portrait effect and sound behavior.
3. MM8 Lich handlers validate a jar on every exact eligible Necromancer before changing any character or consuming
   any item. The refusal identifies the missing jar's party slot. One outcome message is emitted after validation.
4. Replaced the twelve MM6 class-changing handlers in `Global_mm6_mmmerge.lua`, using exact eligibility and
   Master Wizard (51) as the second Sorcerer promotion. Existing completion bits bypass consumed-item requirements
   for later recruits. Only newly promoted recruits receive repeat XP; party rewards and reputation effects run once.
5. An MM6 NPC-enter hook makes the completed first promotion available in unused topic slot 5 and keeps the second
   promotion in slot 1. It derives availability from persisted completion bits, so old saves need no reset or migration.
   Council quests and Anthony Stone's Ankh topic are preserved. Druid ceremonies remain required on the first pass;
   after completion, later recruits can receive their promotions from Loretta without repeating the calendar condition.
6. MM7's existing promotion sidecars, MM8's permanent first-character honorary gates, and MM8's zero-XP repeat
   promotion policy are unchanged. No generated event Lua was edited or regenerated.

## Validation

- Both `openyamm` and `openyamm_unit_tests` built successfully.
- Eleven focused promotion tests passed (633 assertions), including all eight MM8 initial/repeat families,
  the Nathaniel/Lathean NPC dialogue reproduction, atomic missing-jar refusal, the permanent main character's
  honorary completion gate, all six MM6 promotion families after restoring persisted party state, MM7 Lich and
  repeat Priest promotion, and the existing class/promotion baselines.
- The existing MM6 global supplement test passed (208 assertions), including all twelve promotion handlers.
- Runtime event-loader coverage passed (17 assertions), confirming automatic discovery of the new MM8 sidecar.
- Both Garrote Gorge headless event regressions passed with the updated global sidecars mounted.

No manual in-game playthrough was performed for this repair. No generated event Lua or shared class comparator
was changed. Existing saves retain their completion bits and honorary awards; no quest reset is required.
