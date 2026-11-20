# SPL audit: spells, buff auras, crowd control

Auditor scope: zzMaw-Spells.lua, SpellsTweaks.lua, ExtraQuickSpells.lua, zzMaw-BookSwitches.lua,
zzMaw-TownPortalClickFix.lua, Spells2.txt, general-spell parts of zzClasses.lua / MawCore/Classes.lua, against
`game/rules/SpellRules.*`, `game/rules/maw/MawSpellRules.*`, `MawSpellFormulas.*`, `MawAuras.*`, the spells patches,
`PartySpellSystem.cpp`, `GameplayActorService.cpp`, `GameplayProjectileService.cpp`, `Party.cpp` buff code and the
world runtimes' spell paths. MAW paths are relative to `Maw-Mod-MMMerge/Scripts/` (SP = General/zzMaw-Spells.lua,
TW = General/SpellsTweaks.lua, ST = General/zzMaw-Stats.lua, IT = General/zzMaw-Items.lua,
DM = Modules/MawCore/Damage.lua, SK = General/zzMAW-Skills.lua, MON = General/zzMaw-Monsters.lua). Code was read only;
no build or test run.

---

### SPL-1: Mass Distortion deals Standard's 25 % + 2 %/point of current HP under MAW; MAW's share is computed and thrown away
Severity: P1
Confidence: confirmed (read both sides)
MAW: SP:1939-1942 — Mass Distortion's damage is `HP x (0.15 + 0.005 x skill)`; DM:356-389 (`stage_massDistortion`) then
divides it by `sqrt(bolster mult)` (1.4/1.8/3, Doom 3.33(1+L/75), x2(1+L/80) on bosses, x4 Austerity) and multiplies by
`max(1, (L/250)^2)`.
OpenYAMM: `PartySpellSystem.cpp:2617-2641` computes MAW's share through `CombatRules::spellDamageOnTarget`
(`MawCombatRules.cpp:1778-1796`, `massDistortionScale`) and passes it as `damage` to `applyPartySpellToActor`, but
`IndoorWorldRuntime.cpp:13420` / `OutdoorWorldRuntime.cpp:18031` call `GameplayActorService::resolveDirectSpellImpact`,
whose Mass Distortion branch (`GameplayActorService.cpp:229-236`) ignores `baseDamage` and returns
`actorCurrentHp x (0.25 + 0.02 x skillLevel)`. So every non-Assassin Mass Distortion under MAW takes Standard's share
(at skill 20: 65 % of current HP instead of 25 %, before MAW's bolster divisor, which is also lost). The unit tests
(`MawSpellTests.cpp:354`, `MawSpecExampleTests`) only test `spellDamageOnTarget` itself, not the world path.
Not covered by: GAPS L6.3 (Assassin Mass Distortion only), E.7 (tests the function); no DEVIATIONS row.
Suggested fix: in `resolveDirectSpellImpact` use `baseDamage` for Mass Distortion when the caller supplied a ruleset
share (or move Standard's 25 % + 2 % into `CombatRules::spellDamageOnTarget` so both rulesets come through one place).

### SPL-2: Resistance auras and Day of Protection use base 20; MAW's is 10
Severity: P2
Confidence: confirmed
MAW: SP:2670-2677 — `buffPower` for 3/14/25/36/58/69 is Base 10, Scaling 2 ("resistance buffs: halved base, and the
caster-level term is level/4"); SP:2689 Day of Protection Base 10. Applied at IT:3035-3058:
`(Base + level/4) x (1 + Scaling/100 x s)` (Day of Protection with `s/1.4`). Stone Skin (38) and Bless (46) keep 20.
The spec agrees (CLASSES_SPELLS_SPEC §3.3, `data/buff_auras.yml:78-93,155`: base 10).
OpenYAMM: `MawSpellRules.cpp:1159,1163` (party resistance slots), `MawSkillRules.cpp:43-47,55-64` (`auraFlat`,
`addPotionAuraFlats`), `MawSpellRules.cpp:325,329` (tooltip `aura_flat`/`dop_flat`), `MawItemRules.cpp:2359` (potion
popup) all call `mawAuraFlat(20, 2, ...)`; `MawCombatFormulas.cpp:23-40` lists 3/14/25/36/58/69/85 with base 20. At the
temple caster (s 7, L 40) a resistance aura gives 34 instead of 23 (+50 %); at s 50, L 200: 140 instead of 120.
Not covered by: no DEVIATIONS/GAPS row.
Suggested fix: base 10 for the six resistance auras and Day of Protection (one constant, used by the slot powers,
the potion copies, `BuffPowers` and the texts); Stone Skin and Bless stay 20.

### SPL-3: Protection from Magic aura holds one charge at the holder's mastery; MAW gives 50 charges at Grandmaster every 0.5 s
Severity: P2
Confidence: confirmed
MAW: SP:2904-2907 — while the aura is held: `Party.SpellBuffs[13].Power=50`, `.Skill=4`, re-set every 0.5 s, so it
blocks Death and Eradication (engine needs GM) whatever the holder's Body mastery, and effectively never runs out;
the MAW tooltip promises "Poison, Disease, Stone, Paralyze, Weak, Death and Eradicated". The Magic Protection potion
(SP:2985-2990) sets Power 4, Skill 10 (also past the GM check).
OpenYAMM: `MawSpellRules.cpp:1215` gives power 1, and `1295-1296` applies the slot with
`SkillMastery(pSource->mastery)` = the holder's Body mastery (Master for most holders, PfM needs Master; 3 for the
scroll/pedestal/temple source at `:1101`; Master for the potion, `MawRules::potionAura`). `Party.cpp:6724-6728` then
refuses Death/Eradication below GM, and `:6731-6736` clears the buff after one save, so further saves in the same frame
(several members hit by one attack/area) fail until the next `updateAuras`; `MawCombatRules.cpp:2620`'s Unconscious
block also lapses for that frame. Side effect: power 1 adds +1 to every resistance through Standard's PfM bonus
(`Party.cpp:7360-7372`).
Not covered by: DEVIATIONS 31 says the potion is "the same" as MAW since 2026-10-24 — it is not for Death/Eradication;
GAPS A7.15/D.13 cover Dispel only.
Suggested fix: apply the PfM slot (aura, fixed source and potion) at Grandmaster with a large power (MAW's 50), and
keep power out of the resistance bonus under MAW.

### SPL-4: Holding Haste leaves the whole party Weak after travel, training or prison
Severity: P2
Confidence: confirmed
MAW: SP:2900 — every held aura's engine buff is set to expire in one week and refreshed every 0.5 s, so the engine's
"Haste ends → Weak" never fires on travel (coach/boat days) or training.
OpenYAMM: auras are applied for `AuraSeconds = 3600` game seconds and refreshed only below half
(`MawSpellRules.cpp:42,1292-1296`); the Haste slot carries spell id 5 (`:1185-1191`). Long time skips call
`Party::advanceTimedStates` in one step (`TravelRuntime.cpp:25-31`, after `restAndHealAll`; `HouseInteraction.cpp:1977`
prison, `:2072` training, `:2217` travel), the buff runs out inside it, and `Party.cpp:6240-6252` applies Weak to every
member for an expiring spell-5 party buff. With MAW's Weak halving weapon damage (GAPS A1.4) the party arrives crippled.
(Hour of Power's Haste carries id 86 and is not affected.)
Not covered by: no row.
Suggested fix: apply auras with a duration longer than any time skip (MAW's week), or tag aura-driven buffs so their
expiry runs no Standard side effect, or re-run `updateAuras` around time skips.

### SPL-5: Fire Spike under MAW rolls Standard's dice
Severity: P2
Confidence: confirmed
MAW: SP:1895-1896, 1976-1995, 2004-2037 — Fire Spike rolls `spellPowers[7]` (1-10 per point, Ascension-scaled), x8/6 at
Master, x10/6 at GM, then Intellect/Personality, spell crit, and weapon enchant/Fire Aura damage /2.5 (area list).
OpenYAMM: the trap's damage is `rollFireSpikeDamage` (`GameplayProjectileService.cpp:400-430, 2379-2382`): 1-6/1-6/1-8/
1-10 per point by mastery, no Ascension, Intellect, crit or enchantment; `OutdoorWorldRuntime.cpp:6657-6686` only runs
the rules' resistance pipeline on it. The ruleset patch (Damage % 133/167, dice 1-10) is never read for traps.
Not covered by: no row.
Suggested fix: roll the trap through `CombatRules::rollSpellDamage` (the caster, skill and mastery stored on the trap).

### SPL-6: Armageddon under MAW deals a fixed 50 + skill
Severity: P2
Confidence: confirmed
MAW: SP:1926 — Armageddon is in `spellPowers` (50 + 1 per point, the 50 Ascension-scaled; at high Ascension the per-point
die also becomes 1-2), then Intellect, crit and enchant /2.5 like every damage spell.
OpenYAMM: `OutdoorWorldRuntime.cpp:21771` uses `50 + skillLevel` for every monster and member, bypassing
`rollSpellDamage` (at Ascension 30 the flat part alone should be about 1050).
Not covered by: no row.
Suggested fix: roll the monster damage through the combat rules at the stored skill/mastery/caster (the party's share
keeps whatever MAW's non-monster damage rule says, see COMBAT).

### SPL-7: Lifedrain heals Standard's third of the damage on top of MAW's leech
Severity: P2
Confidence: plausible (MAW side depends on the engine's Lifedrain heal living in the impact code)
MAW: SP:3781-3790 swaps the hit's spell (and object) 111 → 200 before the engine processes it ("LEECH FIX"), so the
engine's own Lifedrain heal no longer triggers; DM:1263-1266 gives a tenth of the bar share plus the normal spell leech.
OpenYAMM: `PartySpellSystem.cpp:2616, 2643-2657` heals the caster `drained / 3` for every ruleset, and MAW's
`MawCombatRules.cpp:2880-2899` adds the 10 % bar share and leech as well, so a MAW vampire gets both.
Not covered by: GAPS A1.15 (done) adds MAW's part but does not remove Standard's.
Suggested fix: skip the Standard third when the ruleset handles drain leech (a `CombatRules` query), after confirming in
MAW that the engine heal is gone.

### SPL-8: Summon Wisp's extra MAW wisps are missing
Severity: P2
Confidence: confirmed (absent)
MAW: SP:3435-3455 — when the engine's cap stops a cast, MAW spawns a permanent power-C wisp (monster 97 → id 99, ally
group 9999, speed 350) while fewer than `2m − 3` of its own live (Expert 1, Master 3, GM 5), i.e. up to 10 wisps at GM.
CLASSES_SPELLS_SPEC §1.5 lists it.
OpenYAMM: `PartySpellSystem.cpp:36, 2772-2788` refuses at 5 friendly wisps (Standard), with Standard durations.
Not covered by: no GAPS/DEVIATIONS row.
Suggested fix: a `SpellRules` hook for extra summons (count, monster, permanence) used by the Summon Wisp branch.

### SPL-9: Immolation: MAW's aura likely burns for the flat part only (MAW bug?); we roll the full dice
Severity: P2 (question)
Confidence: plausible
MAW: the aura cast is `t.Handled` (SP:2746-2758), so the engine never sets `Party.SpellBuffs[10].Power`; `mawBuffApply`
puts buff 10 in `mawPartyBuffIgnore` (SP:2648, 2869-2872) and only writes `.Caster` (SP:2946-2952). The engine's
Immolation tick passes that Power as the skill, so `CalcSpellDamage` loops zero dice (SP:1979) and deals only the
Ascension-scaled 10 (x Intellect, + enchant/2.5) on a fresh save.
OpenYAMM: `MawSpellRules.cpp:930-952` rolls 10 + 1-30 per point of the aura's skill (GAPS L5.5 "done").
Not covered by: GAPS L5.5 records the full-dice behaviour as MAW's.
Suggested fix: confirm in MAW (cast Immolation on a new MAW game, watch the numbers); if it is flat-only, either match
it or add a DEVIATIONS row (our version follows MAW's tooltip).

### SPL-10: Turn Undead and Control Undead record diminishing returns on monsters they cannot affect
Severity: P3
Confidence: confirmed
MAW: SP:1621-1623 (engine path) sets a living monster's Spirit/Dark resistance to 65000 so Turn Undead fails and nothing
is recorded (history is written only when the debuff's expiry changed, SP:1650-1652); scripted Control Undead only
targets undead (SP:1493-1496).
OpenYAMM: the world runtimes evaluate `partyCrowdControlSeconds` (which appends to the DR ledger,
`MawRules.cpp:59-98`) as an argument before `tryApplySharedSpellEffect` rejects non-undead
(`IndoorWorldRuntime.cpp:13499`, `OutdoorWorldRuntime.cpp:18069`; rejection at `GameplayActorService.cpp:417-423, 488`).
Turn Undead hits every hostile in range, so living monsters gain group-2 history and later Charm/Fear/Berserk/Enslave
on them are shortened or refused.
Not covered by: no row.
Suggested fix: compute the ruleset duration only after the effect's own eligibility checks (or pass the undead flag in
and return nullopt without recording).

### SPL-11: Crowd-control cast time: Elementalists read Learning; dimension affix 27 slows CC, Dragon Fear, DK and Assassin casts
Severity: P3
Confidence: confirmed
MAW: ST:176-187 — for CC spells too, an Elementalist's Ascension is the floored average of the four elements; ST:211-217
CC returns before the affix; Dragon Fear (ST:167) and Assassins (ST:163) return before it as well; affix 27 applies at
ST:240-242 only to the normal path.
OpenYAMM: `MawSpellRules.cpp:571-575` uses `MawAscensionUse::CrowdControl`, which `MawClassRules.cpp:770` maps to Learning
for Elementalists (so their Slow/Stun cast much faster: x1.015^(0 − Earth) instead of x1.015^(avg − Earth));
`recoveryTicks` (`MawSpellRules.cpp:534-539`) applies affix 27 to every result, CC, Dragon Fear and class casts included.
Not covered by: no row.
Suggested fix: a separate "CC cast time" Ascension use (Elementalist average floored) and apply the affix only on the
normal path.

### SPL-12: An Elementalist's Grandmaster Mass Distortion costs the stack formula instead of MAW's level formula
Severity: P3
Confidence: confirmed
MAW: SP:2270-2277 — the Mass Distortion GM override (`ceil(min(L,255)^1.4/12.5 x P)`) is applied after the Elementalist
branch, so it wins for Elementalists too.
OpenYAMM: `MawSpellRules.cpp:507-515` returns the Elementalist formula before the Mass Distortion check at `:517-520`
(44 is in `mawElementalistOffensiveSpell`).
Not covered by: no row.
Suggested fix: test Mass Distortion GM before the Elementalist branch.

### SPL-13: Spirit Lash's Master range (384) is not ported
Severity: P3
Confidence: confirmed (absent)
MAW: SP:1009-1014 — an asm hook sets the range to 0x180 = 384 at Master (GM keeps the engine's).
OpenYAMM: `PartySpellSystem.cpp:2829-2830` uses 768 at every mastery in both rulesets. CLASSES_SPELLS_SPEC §1.7 and
`data/spells.yml:1060` list the change.
Not covered by: no row.
Suggested fix: a ruleset area-radius hook (or a spells.txt column) for Spirit Lash at Master.

### SPL-14: Wall of Mist (7d11) invisibility on load is not ported
Severity: P3
Confidence: confirmed (absent)
MAW: SP:733-737 — after loading 7d11 with the party between x −4698 and 2906, Invisibility is set for 10 hours.
OpenYAMM: `rulesets/maw/events/maps/7d11_maw.lua` has only the pillar-door fix; no invisibility.
Not covered by: MAPS_CONTENT §3.2 lists 7d11's doors only; no row.
Suggested fix: an on-load handler in `7d11_maw.lua` that grants the party Invisibility (10 h) in that x range, or a
DEVIATIONS row if it is not wanted.

### SPL-15: Raise Dead lifts Eradication at every mastery; MAW only at Grandmaster
Severity: P3
Confidence: confirmed
MAW: SP:250-260 — only GM Raise Dead clears Eradicated (the engine's Raise Dead below GM leaves it).
OpenYAMM: `PartySpellSystem.cpp:1240-1241` calls `Party::reviveMember`, which clears Eradicated (and Petrified, Zombie)
unconditionally (`Party.cpp:6846-6855`), in both rulesets; the spellbook lets any member be targeted.
Not covered by: no row (a Standard behaviour that MAW changes only at GM).
Suggested fix: Raise Dead below GM should not revive an Eradicated member (Standard and MAW alike, or MAW-only if
Standard's leniency is intended).

### SPL-16: Town Portal near enemies in Nightmare/Doom: MAW's block is dead code (typo); we block it — question
Severity: P3 (question)
Confidence: confirmed
MAW: MON:2190-2203 — at bolster 300 or Mode 2, Lloyd's Beacon is refused near enemies (`t.Result=false`), but the Town
Portal handler sets `t.Can=false` (the event field is `CanCast`, TW:60-69), so a Grandmaster Town Portal still works
near enemies on Nightmare/Doom; only Beyond Madness refuses it (SP:3728-3735). Below GM it is refused near enemies
anyway (TW:60-69).
OpenYAMM: `MawMonsterRules.cpp:1794-1797` blocks both spells near enemies for Nightmare, Doom, Road to Insanity and
Beyond Madness (`PartySpellSystem.cpp:1741-1751`).
Not covered by: no row.
Suggested fix: keep (it is the evident intent) and add a DEVIATIONS row, or drop Town Portal from the Nightmare/Doom
block to match MAW's behaviour; also confirm Lloyd's Beacon in Road to Insanity (MAW checks bolster 300 / Mode 2 only).

### SPL-17: Negative potion-aura skills are converted to `uint32_t` (undefined behaviour)
Severity: P3
Confidence: confirmed
MAW: potions below power 67 cast at a negative skill (SP:3127-3131), which MAW keeps as a number.
OpenYAMM: `MawSpellRules.cpp:1295-1296` and `:1321-1322` pass `uint32_t(slot.pSource->skill)` to
`applyPartyBuff`/`applyCharacterBuff`; for the Magic Protection and Preservation potion sources (`:1225-1235`,
`:1305-1311`) `mawPotionAuraSkill` is negative below power 67 (`MawAuras.cpp:282-286`), and a negative double to
unsigned conversion is UB.
Not covered by: no row.
Suggested fix: clamp to 0 (or `std::lround` into int and then clamp) before the cast; the buff skill is display-only.

### SPL-18: Quick-cast crowd control picks the closest monster; MAW spreads it to the one whose debuff ends soonest
Severity: P3
Confidence: confirmed
MAW: SP:1486-1526 (`castCCSpell`) — Slow, both Charms, Berserk, Paralyze, Enslave, Dark Grasp and Control Undead take
the monster under the mouse, else the visible valid hostile within 4800 whose debuff expires soonest; no target →
"Spell Failed", recovery 30, no SP; selection moves to the next ready member.
OpenYAMM: `GameplaySpellService.cpp:259-265` — hovered actor, else the closest visible hostile; no target → "No valid
target exists!" without recovery.
Not covered by: no row.
Suggested fix: a ruleset target-preference hook for quick-cast CC (soonest-expiring debuff), or a DEVIATIONS row.

### Side note (not MAW-specific): Town Portal at Master fails at random in both rulesets
TW:60-69 (base MMMerge and MAW alike) makes Town Portal always succeed at any mastery when no hostile is near;
`PartySpellSystem.cpp:1765-1781` rolls `skill x 10 %` below GM in both rulesets. Out of MAW scope; a Standard fix to
consider.

---

## Checked and matching

- Mana cost curves: damage `ceil(base(1+0.125s)1.04^s(1−0.125m)P)` capped 65000, heal (rounded), CC (`(1+0.2s)1.03^s`),
  Personality factor with the party's total level, Dragon Fear 15/15/25/30, Flame Blast fixed, auras/utility auras 0,
  Elementalist stack cost `ceil(round((base+stacks)·curve·0.5)(1+0.075·stacks)P)`, Mass Distortion GM level formula
  (non-Elementalists), Ascension source per class (Elementalist/Shaman averages at GM for cost; Learning for damage,
  CC duration). Table deltas in `patches/spells.txt` and `content/spells_patch.txt` (Charm 5, Chain Lightning 20/30,
  Lifedrain 10/15, all Spells2 cost/delay rows I sampled: 19, 21, 31, 33, 35, 48, 56, 60, 62, 66, 81, 82, 91, 92, 94,
  96, 113, 122).
- Spell damage roll: dice/add scaling, Empower Magic on Haste's row, unscaled per-point for fixed spells, mastery
  multipliers (Fire Spike 133/167, Lifedrain 167/233 in the table), Int/Pers x(1+max/1000), crit, enchant + Fire Aura
  x1.015^asc /2.5 on the same 17 area spells.
- Cast time: speed/20, Haste/HoP divisor, spell-haste special x1.1, offhand-shield and body-armour impairment,
  Ascension only for damage/heal/CC spells, Elementalist x1.5/(1+0.05·stacks), Flame Blast 1.5x breath, Dragon Fear 120.
- Heals: heal table (normal and Insanity), Ascension rounding, Personality `P/min(1000+3L,4000)`, affix 31, Shaman
  `(1+Σ/400)` except Power Cure, Shared Life (`s/2`, −3s/−4s, healthiest-first pool, even redistribution, unconscious
  join), Resurrection on a living target, legendaries 34/35.
- Auras: the 25 buff and 3 utility auras and costs, reservation `cost/(SPFactor + Enlightenment m/2)` with Shaman
  1/1.5/2, DK/Thief line reserve nothing, utility `round(cost(1−m/10))`, legendary 32 HP reservation, base school skill
  capped 50/75, holder level, unconscious holder (off, reservation kept), toggle/move/release (no recovery on release),
  NotEnoughMana check against the unreserved pool, Hour of Power at s/1.5 for Haste/Shield/Stone Skin/Fate, Day of
  Protection at s/1.4 (max with own), Day of the Gods 1/7 stat %, resistance-aura stat %, Bless/Stone Skin base 20,
  Heroism/Hammerhands/Shield/Fate/Haste multipliers, potion-vs-aura `buffStrength`, Fate/Hammerhands/Empower without
  potions, Regeneration aura (Base 5 used as scaling) and Meditation aura formulas and their exclusions, Torch power
  m+1 and solo Torch 3, solo Wizard Eye (10, Expert), Shadow/Omnipotent boss blinding Wizard Eye, vampire night
  Preservation, fixed scroll/pedestal/temple aura at 7/Master/40 and its map-change expiry, R clears all.
- Crowd control: CCMAP base minutes and groups, mastery steps 0.5/0.65/0.8/1, Shrinking Ray flat, Dragon Fear fixed
  Novice (dev 19), `1.015^asc/(1+res/100)`, solo x2, DR window 20 s and thresholds, boss halving after DR on groups 2-3,
  group 1 exempt, Stun chance `30/(30+L/4)` with boss doubling and paralysis 1 game minute + s·m ticks, Shrinking Ray
  m−1 extra targets within 512 (unshrunk nearest first, then soonest expiry), CC cost and delay formulas (except SPL-11).
- Invisibility Master/GM durations and refusal near enemies, solo travel scrolls kept, solo Fly scroll 7 h, PfM
  Unconscious block, Chain Lightning hits/costs, Tab/R spellbook keys, sealed spellbooks (dev 133), BookSwitches
  overlays (7d12 face 1817 → 3, 7d37 face 896 → 10), SpellsTweaks diff vs base (Slow/Mass Distortion always land,
  philosopher-stone Enchant Item removed: OpenYAMM has neither), ExtraQuickSpells change (extra slots not ported,
  dev 26), TownPortalClickFix (engine UI bug, not applicable).

## Not checked here (other areas)

Class spells (DK, Assassin, Elementalist rotation, Shaman damage, Dragon breath/Flame Blast numbers), spell crits and
the monster damage recompute of monster spells cast at the party (COMBAT), potion effects and recipes (alchemy), item
specials feeding spells.
