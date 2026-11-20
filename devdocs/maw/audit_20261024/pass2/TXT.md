# TXT — second pass: numbers the player is shown, and inventory/bag convenience

Read-only audit. MAW paths are relative to `/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/`, OpenYAMM paths to the
repository root. Part 1 covers the texts and tooltips (`texts.yml`, `MawSkillRules::skillTooltip/statTooltip`,
`MawSpellRules::spellTooltip`, `MawItemRules::inspectLines/itemDescription/enchantDescription`,
`MawCraftingRules::materialDescription`, `mawMonsterInspectNumbers`, `content/skill_des_*.txt`, the MAW event texts).
Part 2 covers the multibag, the sorter, the crafting bag and the book switches (ids `TXT-2-B*`). In part 2, I spot-checked
B3 and B4 by hand. The rest of part 2 was traced by a helper on both sides.

The rule applied: a shown number must match the formula our code applies. A MAW-faithful text is still a finding when
our code does something else.

## Part 1 — texts and tooltips

### TXT-2-1: Armsmaster's Expert, Master and Grandmaster lines are one rank ahead of the code
Severity: P3
Confidence: confirmed (read both sides)
MAW: `General/zzMAW-Skills.lua:149-152` `armsmasterSkill`: Damage `{0,1,1,1.5,2}` and Speed `{0,0,1,1,1}`, indexed by
mastery 1-5. That gives Novice 0 dmg / 0 %, Expert 1 dmg / 0 %, Master 1 dmg / 1 %, GM 1.5 dmg / 1 % and Supreme 2 dmg. The
texts are generated from the same table (`armsmasterDesc`, `:905-930`; Supreme line `:934-936`).
OpenYAMM: the code follows MAW: `MawCharacterSheet.cpp:37` `ArmsmasterDamage = {0,0,1,1,1.5,2}` and
`MawCombatRules.cpp:375` `ArmsmasterSpeedPerPoint = {0,0,0,1,1}`. The text does not: `texts.yml:824-826` says Expert
"1 damage, 1 attack, 1 % speed" (the code gives no speed at Expert), Master "1.5 damage" (code: 1) and Grandmaster
"2 damage" (code: 1.5). The Supreme description (`:819-822`) does not mention its 2 damage per point.
Not covered by: GAPS A5.7, which is about the Supreme line's ladder only. No DEVIATIONS row.
Suggested fix: Expert "1 damage, 1 attack", Master "1 damage, 1 attack, 1 % speed", Grandmaster "1.5 damage, 1 attack,
1 % speed", and add "2 damage per point" to the Supreme sentence.

### TXT-2-2: Grandmaster Bow says "Skill added to damage"; the code takes the skill back and shoots fire arrows, and no text says so
Severity: P3
Confidence: confirmed
MAW: `General/zzMAW-Skills.lua:883`: the GM line is "shoots fire arrows, dealing highest between fire and physical
damage". `zzMaw-Items.lua:3168-3171` removes the vanilla GM skill bonus from the bow's damage rows.
OpenYAMM: `texts.yml:752-758`, Bow grandmaster `"Attack +4, speed +2 % per point; {table}"`. `{table}` is the Standard
line from `engine/data_tables/english/skill_des.txt`: "Skill added to damage." The code does the opposite:
`MawCharacterSheet.cpp:314-318` subtracts the skill from the ranged rows at GM, and `MawCombatRules.cpp:1533` shoots
fire arrows (the better of Fire and Physical). No MAW text in `rulesets/maw` mentions the fire arrows (grep "fire arrow"
finds only the code comment). The append ("Each point adds 1 to the bow's damage") also gives no GM exception.
Not covered by: GAPS A1.9 is marked done "…; popup text", but the popup text is not there, so that done row is
incomplete.
Suggested fix: replace `{table}` in the Bow GM line with the fire-arrow sentence, and drop the "skill added to damage"
promise.

### TXT-2-3: Grandmaster Unarmed promises Standard's evade, which MAW switches off and our MAW rules do not roll
Severity: P3
Confidence: confirmed
MAW: MiscTweaks switches the GM Unarmed dodge off (first-pass note `audit_20261024/CNT.md:217`). MAW's Unarmed rows
are rebuilt from its attack, damage and speed tables (`zzMAW-Skills.lua:828-880`), with no evade.
OpenYAMM: `texts.yml:774-780`, Unarmed grandmaster `"Attack +3, speed +2 % per point; {table}"`. Here `{table}` is
Standard's "Chance to evade an incoming attack equal to skill". `MawCombatRules::characterEvades`
(`MawCombatRules.cpp:3401-3420`) rolls only GM Dodging and Speed. The Standard Unarmed evade
(`CombatRules.cpp:124-145`) is not called under MAW.
Not covered by: no related row.
Suggested fix: drop `{table}` from the Unarmed GM line.

### TXT-2-4: Item popup resistance lines add +10 to second enchantments and apply Legendary 16 before the +10 (MAW tooltip bug ported)
Severity: P3
Confidence: confirmed
MAW: the actual rule (`General/zzMaw-Items.lua:2743-2750`, `collectEnchant`) adds +10 to the first enchantment only and
halves for rings. Legendary 16's ×1.5 comes later, on the collected value. MAW's own tooltip (`Modules/MawCore/Tooltip.lua:263-293`)
adds +10 to both enchantments and multiplies by 1.5 before the +10. The comment at `Tooltip.lua:311` admits that "second
enchants grant the raw strength, no +10".
OpenYAMM: the code follows MAW's real rule: `MawItemRules.cpp:693-706` (`mawEnchantReadPower`: +10 when `first`) and
`:1424-1436` (×1.5 after reading). The popup follows MAW's tooltip: `MawItemRules.cpp:1802-1814` computes
`(power ×1.5 if L16) + 10`, halved on rings, for both enchantments. Examples: a ring's second Fire +40 shows 20.0 %
(the code gives 16.7 %). A first enchantment of 40 with Legendary 16 shows 41.2 % (the code gives 42.9 %).
Not covered by: GAPS A2.14 (done; says "resistances as a reduction %, viewer's Legendary 16 in it") and A1.1. This is a
MAW bug ported into the popup.
Suggested fix: build the line from `mawEnchantReadPower(type, power, first, …)` and then ×1.5 for Legendary 16, exactly as
`applyEnchant` does.

### TXT-2-5: The Learning (Ascension) popup reads the wrong ascension and mastery for Shamans, Elementalists, Death Knights and Assassins
Severity: P3
Confidence: confirmed
MAW: the tooltip (`Modules/MawCore/SkillTooltip.lua:166-185`) uses the Learning skill for every row. MAW's actual
ascension (`General/zzMaw-Spells.lua:2237-2259`) uses the school average at GM for Elementalists and the sum of 7
schools / 7 at GM for Shamans.
OpenYAMM: `MawSkillRules.cpp:471-479` computes every row (damage, healing, mana, cast) from
`mawAscension(character, MawAscensionUse::Damage)` and the Learning skill's own mastery. The code uses a different
ascension per use (`MawClassRules.cpp:748-786`):
- Shaman: healing and cost use sum/7 at Grandmaster, so the popup's healing and mana percents are wrong.
- Elementalist: costs use Grandmaster mastery, but the popup uses Learning's mastery, so the mana percent is wrong. The
  cast time uses `floor(sum)`.
- Death Knight and Assassin: no ascension at all, so a trained Learning shows "+0 %" rows, and "+-25 %" mana at Expert.
Not covered by: no related row.
Suggested fix: compute each row with its own `MawAscensionUse` (Heal, Cost, CastTime) and the mastery that use returns.
Hide the paragraph for classes whose ascension is always empty.

### TXT-2-6: The Meditation popup ignores the aura reservation and Legendary 20, which both MAW's tooltip and our regeneration apply
Severity: P3
Confidence: confirmed
MAW: `SkillTooltip.lua:158-164` → `getMeditationRegen` (`zzMaw-Spells.lua:3475-3487`) →
`Formulas.meditationRegenPerSec`, which uses the pool left after reservation, `ceil(fullSP·(1-reserved)^0.5)`, and
×(1+reserved) with Legendary 20.
OpenYAMM: `MawSkillRules.cpp:461-469` computes `med_now`/`med_next` from `Party::effectiveMaximumSpellPoints`, the full
pool. The real rate (`MawSkillRules.cpp:1029-1041`) uses `mawMeditationPool(full, reserved)` and Legendary 20. An aura
holder's popup overstates (for example √(1/0.5) ≈ 1.41× at half reserved) and never shows the Legendary 20 gain.
Not covered by: GAPS A5.3 (the ×2 timer text), L5.8.
Suggested fix: pass `mawMeditationPool(full, reservedSpellPoints(party, index))` and the Legendary 20 factor, as
`regenerationPerSecond` does.

### TXT-2-7: The Mace or Staff popup shows the other weapon's paralyse chance
Severity: P3
Confidence: confirmed
MAW: `SkillTooltip.lua:285-299`: the Mace GM part uses the Mace skill and mastery ("Stun" at Master, "Paralyze" at GM)
against the reference level.
OpenYAMM: `MawSkillRules.cpp:517-532`. `mawWeaponStunChance` returns the chance of the weapon in hand, Mace or Staff. The
line is added whenever the character has the skill being viewed (`pHeld = character.findSkill(canonicalSkill)`). A
member with Mace and Staff who holds a staff sees the staff's chance in the Mace popup, and the reverse. With any other
weapon in hand, neither popup shows a chance (MAW's Mace popup shows it from the skill).
Not covered by: GAPS L5.4 (done, "Mace and Staff paralyse chance").
Suggested fix: show the line only when the held weapon's skill equals `canonicalSkill`, or compute the chance for the
viewed skill as if that weapon were held.

### TXT-2-8: The Personality popup counts Personality's spell points once; the code counts it twice for Personality casters, and MAW twice for all (extends CLS-1)
Severity: P3
Confidence: confirmed
MAW: `General/zzMaw-Stats.lua:324`: "Increase the mana by 2 levels worth of mana per 5 personality".
OpenYAMM: `texts.yml:1060-1066` "Personality adds {personality_levels} levels' worth of spell points", with
`personality_levels = mawStatEffect(personality)` (`MawSkillRules.cpp:751`). `MawClassRules::baseMaxSpellPoints`
(`MawClassRules.cpp:198-219`) adds `mawStatEffect(personality)` on top of the class stat effect, so a Personality-mode
class gets 2× and an Intellect class 1×. The popup is right for Intellect classes and half for Personality and Mixed
classes.
Not covered by: extends CLS-1 / DAT-2 (the SP formula). The text has to move with that fix.
Suggested fix: once CLS-1 is settled, show the levels the formula actually adds, for example "2×" under MAW's rule.

### TXT-2-9: The Level popup says monsters grow with the levels banked in their world; they grow mainly with the levels banked elsewhere
Severity: P3
Confidence: confirmed
MAW: `General/zzMaw-Stats.lua:458-466` lists the levels gained per world and the "Bolster Level in MM6/7/8"
(`getPartyLevel(n) - 4`). `getPartyLevel` is the other worlds' levels plus half of the world's own.
OpenYAMM: `texts.yml:1092-1095` "…Monsters grow with the levels banked in their world." The code
(`MawRules.cpp:325-340`) uses `levelOutside(continent)` plus `min(own/2, 54)` (plus resets). The sentence inverts the
rule, and the per-world bolster levels MAW shows are missing.
Not covered by: no related row.
Suggested fix: say that monsters grow with the levels banked in the other worlds and half of their own (capped at 54).
Add the three bolster levels from the same formula `MawRules` uses.

### TXT-2-10: The SpellPoints popup says regeneration doubles 20 seconds "after the last hit taken"
Severity: P3
Confidence: confirmed
MAW: SP waits on its own timer, reset when SP drops (`zzMAW-Skills.lua:1432-1446`).
OpenYAMM: the code (`MawSkillRules.cpp:1183-1196`) uses `secondsSinceSpellLoss`. The Meditation skill text
(`texts.yml:838-842`) says it right ("20 seconds after spell points last dropped"). The SpellPoints stat append
(`texts.yml:1082-1085`) copies the HitPoints wording: "twice that 20 seconds after the last hit taken".
Not covered by: GAPS A5.3 (the skill text only).
Suggested fix: "…20 seconds after spell points last dropped…".

### TXT-2-11: Class school popups drop MAW's live numbers although the code has them
Severity: P3
Confidence: confirmed
MAW: `SkillTooltip.lua:351-373` (Shaman: Water's flat cut, Mind's SP per blow `s^1.25`, Body's HP per blow),
`:404-424` (Seraph: Spirit's flat cut, "Current heal from Body"), `:480-481` (Assassin Water mastery rows "You
regenerate 8/10/12/14 energy per second"). `General/zzMaw-Stats.lua:341-347` shows GM Dodging's dodge chance under
Speed.
OpenYAMM: `texts.yml:984-1006` (shaman Water, Mind and Body: no number), `:1009-1023` (seraph Spirit and Body: no
number), `:921-925` (assassin WaterMagic: description only, so the mastery rows fall back to the skill table's Water
Magic lines). No Speed or Dodging popup gives the GM dodge chance. The numbers exist in code:
`mawClassDefense().flatReduction` (`MawClassRules.cpp:663-675`), the on-hit heals (`MawCombatRules.cpp:3054-3115`),
the energy rate (`MawClassRules.cpp:462`) and `mawGrandmasterDodgeChance`.
Not covered by: GAPS L5.4 (lists other live numbers).
Suggested fix: add placeholders for them (`school_flat_cut`, `mind_sp`, `body_hp`, `seraph_heal`, the energy rows,
`dodge_chance`).

### TXT-2-12: Blood Leech's popup leaves out Body Magic skill bonuses that the heal uses
Severity: P3
Confidence: confirmed
MAW: `Formulas.bloodLeech(fullHP, s, m)` (`Modules/MawCore/Formulas.lua:248-250`). The MAW tooltip side was not
traced; this finding is about our two places disagreeing.
OpenYAMM: the popup (`MawSpellRules.cpp:345-351`) uses `pBlood->level`. The hit (`MawCombatRules.cpp:3017-3023,
3136-3141`) uses `level + skillBonus("BodyMagic")`. With a +Body item, the hit heals more than the popup says. The
heal reading the boosted skill is itself a candidate for CLS-2 (MAW reads the trained skill there).
Not covered by: CLS-2 (perks reading the effective skill) is related. Whichever way CLS-2 goes, the two places should
agree.
Suggested fix: compute both from the same skill reading.

### Note: texts that are MAW-correct but describe behaviour our code does not have yet (extends SPL-1, SPL-3/ALC-3, SPL-5, SPL-6)
These popups print MAW's rule while the code still runs Standard's or something else. They become right when the
listed finding is fixed, and need no text change:
- Spell 44 (`texts.yml` spell 44, `hp_share = 15 + 0.5 s`, `MawSpellRules.cpp:303-307`) while the damage dealt is
  Standard's 25 % + 2 %/pt (SPL-1).
- Spell 7's mastery dice (`mastery_dice`) while Fire Spike rolls Standard's dice (SPL-5).
- Spell 98's "{add} plus {dice} per point" while Armageddon deals 50 + skill (SPL-6).
- Spell 75 and potion 237 ("immune to … Death and Eradication", "from 50 power on…") while PfM holds one charge at the
  holder's mastery (SPL-3, ALC-3).

## Part 2 — inventory and convenience (multibag, sorter, crafting bag, book switches)

### TXT-2-B1: Shift+Sort for a party of one packs all 25 bags into one run; MAW's C (and a party-of-one G) sorts only the open tab's five
Severity: P3
Confidence: confirmed (read both sides)
MAW: `zzMaw-Item-Sorter.lua:202-405` `sortMultibag` opens bags 1-5 through `changeBag(pl, bag)`.
`zzMaw-MultiBag.lua:174-178` maps bag ≤ 5 to the current tab (`bag+(currentTab-1)*100`), so it sorts the open tab's
five bags. G for a party of one calls the same function (`:684-687`). The all-tabs `sortMultiBag`
(`zzMaw-MultiBag.lua:345`) is never called.
OpenYAMM: `GameplayPartyOverlayInputController.cpp:3302-3335` → `InventoryBags::sortPartyBags(…, allBags=shift,
bagCount=25)`. `bagItems(…, true)` (`InventoryBags.cpp:59`) takes every stored bag, and `packIntoBags`/`storeBags`
(`:104-160`) repack from tab 1, bag 1. Tabs a solo player keeps apart are merged into tab 1, and the open bag (say bag
12) is left empty.
Not covered by: DEVIATIONS 131 ("C all of a character's bags") misreads `changeBag`. GAPS H.1 is marked done.
Suggested fix: limit Shift and Ctrl+Shift sorts to the open tab's five bags when `bagCount > BagsPerTab`, or record a
deviation and correct row 131's MAW column.

### TXT-2-B2: A plain Sort under MAW without an alchemist uses Standard's grouped order, not MAW's
Severity: P3
Confidence: confirmed
MAW: `zzMaw-Item-Sorter.lua:39-45, 60-199`: R sorts the open bag by height (tallest first, 1.5 for a wide item one cell
tall), then skill, then item id. All sorts use that order.
OpenYAMM: `GameplayPartyOverlayInputController.cpp:3313` uses `sortPartyBags` (MAW's order) only with Shift, Ctrl or an
alchemist set. Otherwise `:3340` calls `Party::sortMemberInventory` (`Party.cpp:4829-4890`), Standard's sort by type,
then height, width and id. One MAW game therefore sorts in two orders.
Not covered by: DEVIATIONS 131/139, GAPS H.1/L7.2.
Suggested fix: when `bagCount > 1`, send a plain Sort through `sortPartyBags({member}, false, …)`.

### TXT-2-B3: The sort's skill tie-break compares skill-group names alphabetically; MAW compares skill numbers
Severity: P3 (cosmetic)
Confidence: confirmed (re-read)
MAW: `zzMaw-Item-Sorter.lua:155-167` compares `Game.ItemsTxt[n].Skill`, the numeric `const.Skills` id: Staff < Sword <
Dagger < Axe < Spear < Bow < Mace < Blaster < Shield < Leather < Chain < Plate, with Misc after equipment.
OpenYAMM: `InventoryBags.cpp:76-91` `sortByMawOrder` compares `ItemDefinition::skillGroup` strings. That puts Axe <
Blaster < Bow < Chain …, and misc items between Mace and Plate.
Not covered by: no related row.
Suggested fix: map `skillGroup` to the engine's skill order (Misc last) for the second key.

### TXT-2-B4: The Crafting Cube (1070) is neither gathered by the loot key nor routed to the alchemist
Severity: P3
Confidence: confirmed (re-read)
MAW: `zzzMaw_CraftingBag.lua:1-6` `isCraftingMaterial` covers 1041-1070. The K pull uses it (`zzMaw-Monsters.lua:4448`).
`alchemyItemsOrder` (`zzMaw-Item-Sorter.lua:751-757`) has 73 entries, with 1070 between 1063 and 1066.
OpenYAMM: `MawItemRules.cpp:2105-2110` `gathersItem` covers 1041-**1069** (the header comment `MawItemRules.h:141`
agrees). `MawItemRules.cpp:2185-2191` `AlchemyItemsOrder` has 72 entries without 1070, so the ranks after 1063 shift by
one. 1070 is the Crafting Cube (`items_patch.txt:350-361`, `crafting.yml:35`).
Not covered by: GAPS L7.2 is done ("30 crafting items"), so the implementation is incomplete here.
Suggested fix: use `<= 1070` in `gathersItem`, and insert 1070 after 1063 in `AlchemyItemsOrder` (73 entries).

### TXT-2-B5: After a party of one grows, a member left on tab 2 or later cannot use the bag buttons, and the compact view shows unusable bags
Severity: P3
Confidence: confirmed (read); a runtime check would confirm the visuals
MAW: `zzMaw-MultiBag.lua:166-178`: in a party the tab buttons are hidden, but `changeBag` still maps bags 1-5 into the
current tab. A member left on tab 3 keeps working with tab 3's five bags.
OpenYAMM: `MawItemRules.cpp:2095-2098`: `bagCount` drops from 25 to 5 when a second member joins, and nothing clamps
`rulesetState.currentBag`. A bag button computes `current/5*5 + button` (5-9 for `currentBag` 7;
`GameplayPartyOverlayInputController.cpp:3352-3357`), and `openBag` refuses bags from 5 up (`InventoryBags.cpp:143`).
The click silently does nothing. Shift+1-5 (`:1907`) parks the open bag 7 in `storedBags[7]`, out of reach until solo
again. The highlight uses `current % 5` (`GameplayPartyOverlayRenderer.cpp:9757-9760`). The compact view shows bags
5-9 (`:2276-2284`), which `placeInBag`/`takeFromBag` refuse (`InventoryBags.cpp:351`). A Shift+Sort pulls the hidden
tabs into bags 0-4 or fails with "Not enough room to sort."
Not covered by: GAPS H.1, H.1a, DEVIATIONS 141.
Suggested fix: work inside the open tab as MAW does (buttons, keys and `openBag` relative to the tab), or fold
`currentBag` into 0-4 when the party grows and say that the other tabs wait for solo play.

### TXT-2-B6: Adventurer's Inn characters cannot switch bags
Severity: P3
Confidence: confirmed
MAW: `zzMaw-MultiBag.lua:1-34, 76, 88` adds `innBagPlayer`/`bagOwner` so the bag buttons and keys work on a roster
character's inventory in the inn (screen 29), with an empty mouse.
OpenYAMM: the number keys return early in the inn (`GameplayPartyOverlayInputController.cpp:1884`). The bag buttons
and compact toggle are neither drawn nor hit-tested there (`GameplayPartyOverlayRenderer.cpp:9720, 9754`;
`GameplayHudOverlaySupport.cpp:1400`), and the alchemist key is blocked (`:2055`). An inn character's bags 2-5 can be
reached only after hiring.
Not covered by: DEVIATIONS 131/141, GAPS H.1.
Suggested fix: allow bag switching for an inn character (refuse while an item is held, as MAW does), or add a deviation
row.

### Note, extends ALC-7 (crafting bag not ported)
`zzzMaw_CraftingBag.lua` also draws a gold "C" marker on each flagged bag button (`:57-100`). It routes only items
1041-1070, to the picker's flagged bags first and then to other members' bags. A port should take its range from the
B4 fix, with 1070 included.

## Checked and matching

Part 1, enumerated:
- **Placeholders**, all filled by the code that reads each section; mawFillText prints an unknown one literally, and none
  is left over. Spells: 17 keys (`add`, `dice`, `mastery_*`, `cost`, `heal_*`, `cc_seconds`, `aura_*`, `dop_flat`,
  `dog_stat`, `hop_*`, `hp_share`, `level`, `skill`). Classes: `percent`, `blood_leech`. Skills: 26 keys, with the
  ladder present for all four self-taught skills in every mode. Class skills: 7. Stats: 27. Potions: 15. Gem: 10. No
  Standard text table (spells, skill_des, stats) contains braces, so filling Standard text through mawFillText is safe.
- **Skill popups:** Cover chance (10 % + 1 %/pt, cap 40 %, +15 % GM bonus), Mana Shield efficiency (1 + s^1.4/60, 5 at
  50) and absorb shares, Retaliation coefficients and damage (`round(P^0.25)·round(V^0.25)·skill·stacks`), its 10 s
  store, 25 % stun per stack (2 s, 1 s on bosses) and −30 % recovery per stack. Spear GM stack, ×1.5 halberd.
  Regeneration now/next and the 0.05/0.075/0.10/0.10 rates with their lines. Meditation rates and lines (apart from
  TXT-2-6). Ascension damage percents (`mawAscendedSpellDice`). The Learning mastery lines (−12.5 % per rank). Dragon
  bite leech (5 %·skill/expected skill). Dragon level cap 600/900.
- **Weapon and armour rows against the code:** attack per point (Spear 2-8, Unarmed 2/2/3/3), speed per point
  (Sword/Bow/Unarmed 0/1/1/2, Axe 0/1/1/1, Dagger GM 1), AC rows (Staff, Sword, Spear, Dodging 4/5/6/6), armour
  AC%/resistance% for Leather, Chain, Plate and Shield, the recovery penalties (Leather/Shield none from Expert, Chain
  halved then none, Plate halved then none at GM), Shield GM −15 %, Bodybuilding and Enlightenment 0.5-2 %, Dagger
  Master crit, Axe GM crit damage, Mace/Staff 2 s / 4 s paralysis, Assassin energy costs (50 − 5·mastery).
- **Class school popups:** Seraph Mind `round(s(m+1)/2)` and Light speed `s·m/2` (Seraph Mind/Body cap at Master, so
  their GM lines cannot be reached). Shaman Fire `s/10` %, Air and DK Body/Unholy `1−1/(1+s/100)`, Spirit `s` %, Earth
  `s·m/2`. DK Frost/Unholy flat 0.5/0.75/1. Vampiric Aura 5 % / 2.5 %.
- **Spell popups:** aura flats and stat percents (base 20 as coded, SPL-2), with the skill counted from the base level
  capped at 50/75 exactly as the live aura source. Empower Magic on Haste's row, as the damage code. Day of Protection
  ÷1.4 and Hour of Power ÷1.5, as `addPotionAuraFlats`/`auraSkill`. Heals with the Shaman 1 + sum/400 and Heal
  ascension. Crowd-control seconds = 2 × game minutes, the same conversion the cast uses. Mass Distortion's text formula
  equals `spellDamageOnTarget`. "Recovery time" uses the rules' `recoveryTicks`.
- **Stat popups:** Might `M/10` %, spell bonus `max(I,P)/10` % (as `MawCombatRules.cpp:1866`), healing
  `P/min(1000+3L,4000)`, cost cut (party total level, as the cast), Endurance `E/10` % (as `applyResourceBonuses`),
  attack haste and spell haste `floor(S/20)` (MAW's tooltip says /10 but its code /20; ours follows the code), avoid
  chance and hit chance from the same model and party size as the rolls, armour and resistance cuts, HP/SP regeneration
  from `regenerationPerSecond`, and the per-world level indices (continent 1 = MM8 … 3 = MM6).
- **Potion popups against `potion_effects.yml` and `InventoryItemUseRuntime`:** heal and mana pools (flat + share ×
  model pool at the capped power), haste, heroism and shield percents, stat and stat_light, protection, Meditation
  `ceil(√P/1.5)+1`, Transcendence `5s²+15s` and best step, black potion 20/50 and resistance 30/50 steps. MAW's 6-hour
  wording matches MAW.
- **Gem popup caps:** `gemCap` and the slot multipliers of `mawEnchantSlotMultiplier`.
- **Reagent "Power":** `floor`, as MAW's real mixing (`zzAlchemy.lua:613`), not MAW's `round` tooltip.
- **Monster inspect:** the two-roll 95 % range after the viewer's damage taken, disease → poison below level 20 as in
  `MawMonsterRules.cpp:470-485`, the Doom roll only on attacks with a special-attack level (D.20), the map damage affix.
- **Other texts:** Merchant (skill × mastery + bonus, GM or 45 = cost), Identify Monster's rule, Alchemy's reagent drop
  1 %/2 % and white/black mixing lines, teacher-speech rewriting, respec cost 1000 × level, Vampiric Aura and
  Retaliation `skill_des_new.txt` texts.

Part 2:
- **Bag counts:** 5 per character, 25 (5 tabs × 5) for a party of one. Standard returns 1, so no bag UI, keys, compact
  view, alchemist or gather runs there.
- **Keys:** Shift+1-5 switches bags in a party; for a party of one, 1-5 are bags and Shift+1-5 tabs.
- **Inventory passes see only the open bag:** pickup, evt and quest item checks, shop sell/identify/repair, Workbench
  and Alchemy inputs, as MAW's `changeBag`.
- **Bags belong to the character** (`Character::rulesetState`). They survive dismiss, re-hire, death and eradication,
  and are saved with the inn roster (`SaveGame.cpp:1267/1335`).
- **Save and load (SaveVersion 110/112):** `currentBag`, `storedBags` and each `InventoryItem` round-trip with
  `rulesetFields`. A character with bags only is still written. The alchemist member is saved in `MawGameState`.
- **Ruleset switch:** a MAW character never enters a Standard session, because loads replace the party and roster.
- **Alchemist pick:** a second press toggles it off; MAW's messages; an out-of-range slot counts as no alchemist.
- **Alchemy rank:** potions 220-299 first, highest id first, then MAW's list (apart from 1070, see B4). Alchemy items
  go to the alchemist. A party sort keeps each member's items with that member (DEVIATIONS 139).
- **Packing:** column by column, with no return to a full bag. A wide item one cell tall counts as 1.5 high.
- **Book switches:** `zzMaw-BookSwitches.lua` (7d12 face 1817 → event 3, 7d37 face 896 → event 10) is ported as the
  `7d12_zz_maw.scene.yml` and `7d37_zz_maw.scene.yml` overlays.
- **Gather counts:** 30 corpses and 30 items, dimension maps (290) included.
