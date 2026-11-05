#include "game/rules/maw/MawSpellRules.h"

#include "game/gameplay/GameMechanics.h"
#include "game/party/SpellSchool.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawClassSpells.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
// Road to Insanity and Beyond Madness heal from their own table.
bool insanityHeals(const MawRules &rules)
{
    return mawModelConfig(rules.options(), 5).insanityMode;
}

constexpr uint32_t MassDistortion = 44;
constexpr uint32_t DragonFear = 122;
constexpr uint32_t FlameBlast = 123;
// Special 40 ("Lichs'") in a weapon slot speeds casting by 10 %.
constexpr uint16_t SpellSpeedSpecial = 40;

// Auras are re-applied with a long duration and refreshed before half of it has run out: a week of game time, so
// no travel, training or prison time skip lets a held aura's buff run out and take its expiry's side effect (Haste's
// Weak) (SP:2900, SPL-4).
constexpr float AuraSeconds = 7.0f * 24.0f * 3600.0f;

// The skill an aura's buff shows: a weak potion's aura skill is negative (MAW keeps it as a number), so it shows 0
// (SPL-17).
uint32_t auraBuffSkill(const MawAuraSource &source)
{
    return uint32_t(std::max(0.0, source.skill));
}
constexpr uint32_t HourOfPower = 86;
constexpr uint32_t DayOfProtection = 85;
constexpr uint32_t Preservation = 50;
constexpr uint32_t ProtectionFromMagic = 75;
// MAW holds Protection from Magic at 50 charges and Grandmaster, re-set every half second, so it blocks Death and
// Eradication whatever the holder's mastery and never runs out (SP:2904-2907, SPL-3).
constexpr int ProtectionFromMagicCharges = 50;

// The Elementalist's rotation kinds (Classes.lua:55-61): single target, shotgun and area, the area spells by where
// they can be cast. A spell of several kinds counts as the first.
enum ElementalistSpellKind
{
    NoRotation = 0,
    SingleTarget,
    Shotgun,
    Area,
};

constexpr std::array<uint32_t, 7> SingleTargetSpells = {2, 11, 20, 26, 29, 37, 39};
constexpr std::array<uint32_t, 4> ShotgunSpells = {2, 15, 24, 37};
constexpr std::array<uint32_t, 5> IndoorAreaSpells = {6, 10, 18, 32, 41};
constexpr std::array<uint32_t, 7> OutdoorAreaSpells = {6, 9, 18, 22, 32, 41, 43};

template <size_t Count>
bool listed(const std::array<uint32_t, Count> &spells, uint32_t spellId)
{
    return std::find(spells.begin(), spells.end(), spellId) != spells.end();
}

int elementalistSpellKind(uint32_t spellId)
{
    if (listed(SingleTargetSpells, spellId))
    {
        return SingleTarget;
    }

    if (listed(ShotgunSpells, spellId))
    {
        return Shotgun;
    }

    return listed(IndoorAreaSpells, spellId) || listed(OutdoorAreaSpells, spellId) ? Area : NoRotation;
}

// A random spell of the kind the member knows (elementalistRandomizer); nothing when they know none.
std::optional<uint32_t> randomElementalistSpell(const Character &member, int kind, bool indoor)
{
    static thread_local std::mt19937 rng(std::random_device{}());
    std::vector<uint32_t> known;
    const auto collect = [&](const auto &spells)
    {
        for (const uint32_t spellId : spells)
        {
            if (member.knowsSpell(spellId))
            {
                known.push_back(spellId);
            }
        }
    };

    if (kind == SingleTarget)
    {
        collect(SingleTargetSpells);
    }
    else if (kind == Shotgun)
    {
        collect(ShotgunSpells);
    }
    else if (kind == Area && indoor)
    {
        collect(IndoorAreaSpells);
    }
    else if (kind == Area)
    {
        collect(OutdoorAreaSpells);
    }

    if (known.empty())
    {
        return std::nullopt;
    }

    return known[std::uniform_int_distribution<size_t>(0, known.size() - 1)(rng)];
}

void rotateElementalistSpells(
    Character &member,
    MawClassRuntime &runtime,
    uint32_t spellId,
    const SpellTable &spellTable,
    bool indoor)
{
    const SpellEntry *pCast = spellTable.findById(int(spellId));
    std::array<std::string *, 2> slots = {&member.quickSpellName, &member.attackSpellName};

    for (size_t slot = 0; slot < slots.size(); ++slot)
    {
        std::string &bound = *slots[slot];

        if (pCast == nullptr || bound != pCast->name)
        {
            continue;
        }

        // A spell the rotation did not put there was bound by the player and names the slot's kind.
        if (bound != runtime.rotationSpells[slot])
        {
            runtime.rotationKinds[slot] = elementalistSpellKind(spellId);
        }

        const std::optional<uint32_t> next = randomElementalistSpell(member, runtime.rotationKinds[slot], indoor);
        const SpellEntry *pNext = next ? spellTable.findById(int(*next)) : nullptr;

        if (pNext != nullptr)
        {
            bound = pNext->name;
            runtime.rotationSpells[slot] = bound;
        }
    }
}

bool memberConscious(const Character &member)
{
    return !member.conditions.test(size_t(CharacterCondition::Dead))
        && !member.conditions.test(size_t(CharacterCondition::Unconscious))
        && !member.conditions.test(size_t(CharacterCondition::Petrified))
        && !member.conditions.test(size_t(CharacterCondition::Eradicated));
}

// Death Knights and the Thief line hold auras without reserving mana (SP:3055-3058).
bool reservesNothing(const Character &member)
{
    static const std::array<const char *, 7> Classes = {
        "DeathKnight", "DeathLord", "LichKing", "Thief", "Rogue", "Assassin", "Spy",
    };
    const std::string className = canonicalClassName(member.className);
    return std::find(Classes.begin(), Classes.end(), className) != Classes.end();
}

// The class's SP per level (Class HP SP.txt), as MAW snapshots it, with its overrides for the Shaman line.
double classSpellFactor(const Party &party, const Character &member)
{
    const std::string className = canonicalClassName(member.className);

    if (className == "Shaman" || className == "Sekhem" || className == "Marabou")
    {
        return className == "Shaman" ? 1 : className == "Sekhem" ? 1.5 : 2;
    }

    const ClassMultiplierEntry *pEntry =
        party.classMultiplierTable() != nullptr ? party.classMultiplierTable()->get(className) : nullptr;
    return pEntry != nullptr ? pEntry->manaPerLevel : 0;
}

// The class's HP per level, the divisor of a legendary 32 wearer's reservations (hpScalings, SP:2581-2584).
double classHealthFactor(const Party &party, const Character &member)
{
    const ClassMultiplierEntry *pEntry = party.classMultiplierTable() != nullptr
        ? party.classMultiplierTable()->get(canonicalClassName(member.className))
        : nullptr;
    return pEntry != nullptr ? pEntry->healthPerLevel : 0;
}

// Legendary 32: auras reserve hit points instead of mana, by the class's HP factor (SP:2762-2790).
bool reservesHealth(const Character &member)
{
    return mawWearsLegendaryAffix(member, 32);
}

int skillMasteryValue(const Character &member, const std::string &skill)
{
    const CharacterSkill *pSkill = member.findSkill(skill);
    return pSkill != nullptr ? int(pSkill->mastery) : 0;
}

CharacterSheetSummary sheetOf(const CharacterSpellCast &cast)
{
    return GameMechanics::buildCharacterSheetSummary(
        *cast.pCaster, cast.pItemTable, cast.pStandardItemEnchantTable, cast.pSpecialItemEnchantTable);
}
}

MawSpellRules::MawSpellRules(MawRules &rules)
    : m_rules(rules)
{
}

std::string MawSpellRules::spellName(const Character &caster, const SpellEntry &spell) const
{
    if (const MawClassSpell *pClassSpell = mawClassSpell(caster.className, uint32_t(spell.id)))
    {
        return pClassSpell->pName;
    }

    // MAW's renames (Chain Lightning, Vampiric Aura...); saves keep the table's name.
    const std::optional<MawSpellTextEntry> text = m_rules.textData().find({}, uint32_t(spell.id));
    return text && text->name ? *text->name : spell.name;
}

SpellTooltipText MawSpellRules::spellTooltip(const Party &party, const Character &caster, const SpellEntry &spell) const
{
    SpellTooltipText text = SpellRules::spellTooltip(party, caster, spell);
    const uint32_t spellId = uint32_t(spell.id);
    const std::string line = mawClassLine(caster.className);

    if (const std::optional<MawSpellTextEntry> entry = m_rules.textData().find(line, spellId))
    {
        text.description = entry->description.value_or(text.description);

        for (size_t mastery = 0; mastery < text.masteryLines.size(); ++mastery)
        {
            text.masteryLines[mastery] = entry->masteryLines[mastery].value_or(text.masteryLines[mastery]);
        }
    }

    const std::optional<std::string> schoolSkill = resolveMagicSkillName(spellId);
    const CharacterSkill *pSchool = schoolSkill ? caster.findSkill(*schoolSkill) : nullptr;
    const SkillMastery casterMastery =
        pSchool != nullptr ? std::max(pSchool->mastery, SkillMastery::Normal) : SkillMastery::Normal;
    const uint32_t schoolLevel = pSchool != nullptr ? pSchool->level + caster.skillBonus(*schoolSkill) : 0;
    const MawClassSpell *pClassSpell = mawClassSpell(caster.className, spellId);
    const MawAura *pAura = mawAura(spellId);
    const auto castAt = [&](SkillMastery mastery)
    {
        CharacterSpellCast cast;
        cast.pCaster = &caster;
        cast.pItemTable = party.itemTable();
        cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
        cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
        cast.pSpell = &spell;
        cast.mastery = mastery;
        cast.skillLevel = schoolLevel;
        cast.partyCount = int(std::max<size_t>(1, party.members().size()));
        return cast;
    };

    // The numbers a text may name, at one mastery: the description reads the caster's own.
    const auto valuesAt = [&](SkillMastery mastery)
    {
        std::unordered_map<std::string, double> values;
        const size_t masteryIndex = size_t(mastery) - 1;
        values["level"] = caster.level;
        values["skill"] = schoolLevel;
        values["cost"] = manaCost(castAt(mastery), spellNumbersAtMastery(spell, mastery).manaCost);

        if (const std::optional<MawSpellDice> dice = mawCasterSpellDice(m_rules, caster, spell))
        {
            const double percent = spell.damagePercents[masteryIndex] / 100.0;
            values["add"] = dice->add;
            values["dice"] = dice->diceMax;
            values["mastery_add"] = dice->add * percent;
            values["mastery_dice"] = dice->diceMax * percent;
        }

        // Mass Distortion's share of the target's hit points (MawCombatRules::spellDamageOnTarget).
        if (spellId == MassDistortion)
        {
            values["hp_share"] = 15 + 0.5 * schoolLevel;
        }

        if (std::optional<MawHealSpell> heal = mawHealSpell(spellId, mastery, insanityHeals(m_rules)))
        {
            // A Shaman's every school strengthens the heals but Power Cure (SP:2370-2384).
            if (spellId != 77)
            {
                const double shaman = 1 + mawShamanSchoolSum(caster) / 400;
                heal->base *= shaman;
                heal->perPoint *= shaman;
            }

            const double ascension = mawAscension(caster, MawAscensionUse::Heal).skill;
            const double base = mawHealAmount(*heal, 0, ascension, 0, caster.level);
            values["heal_base"] = base;
            values["heal_per"] = mawHealAmount(*heal, 1, ascension, 0, caster.level) - base;
        }

        if (const MawCrowdControlSpell *pControl = mawCrowdControlSpell(spellId))
        {
            values["cc_seconds"] = 2 * mawCrowdControlMinutes(*pControl, mastery,
                mawAscension(caster, MawAscensionUse::CrowdControl).skill, 0, party.members().size() <= 1);
        }

        if (pAura != nullptr)
        {
            const double skill = std::min(pSchool != nullptr ? double(pSchool->level) : 0.0, pAura->skillCap);
            const double buffScale = m_rules.buffScale();
            values["aura_flat"] = mawAuraFlat(20, 2, caster.level, skill, buffScale);
            values["aura_stat"] = mawAuraStatPercent(skill, false);
            // Empower Magic reads Haste's numbers (CLASSES_SPELLS_SPEC.md §3.3).
            values["aura_percent"] = 100 * mawBuffMultiplier(spellId == 28 ? 5 : int(spellId), skill, buffScale);
            values["dop_flat"] = mawAuraFlat(20, 2, caster.level, skill / 1.4, buffScale);
            values["dog_stat"] = mawAuraStatPercent(skill, true);
            values["hop_haste"] = 100 * mawBuffMultiplier(5, skill / 1.5, buffScale);
            values["hop_shield"] = 100 * mawBuffMultiplier(17, skill / 1.5, buffScale);
            values["hop_armor"] = mawAuraFlat(20, 2, caster.level, skill / 1.5, buffScale);
            values["hop_fate"] = 100 * mawBuffMultiplier(47, skill / 1.5, buffScale);
        }

        if (pClassSpell != nullptr)
        {
            values["percent"] = 100 * pClassSpell->damage[masteryIndex];
            values["combo"] = pClassSpell->comboCost;
            values["class_cost"] = pClassSpell->cost;
        }

        // A Death Knight's Blood Leech heals max(FullHP^0.5 s^1.5 / 70 (1 + m/4), 2s) a hit (DM:743-768).
        if (const CharacterSkill *pBlood = caster.findSkill("BodyMagic"))
        {
            const double blood = pBlood->level;
            const double full = caster.maxHealth + caster.permanentBonuses.maxHealth + caster.magicalBonuses.maxHealth;
            values["blood_leech"] =
                std::max(std::sqrt(full) * std::pow(blood, 1.5) / 70 * (1 + int(mastery) / 4.0), 2 * blood);
        }

        return values;
    };

    text.description = mawFillText(text.description, valuesAt(casterMastery));

    for (size_t mastery = 0; mastery < text.masteryLines.size(); ++mastery)
    {
        text.masteryLines[mastery] = mawFillText(text.masteryLines[mastery], valuesAt(SkillMastery(mastery + 1)));
    }

    if (pClassSpell != nullptr && pClassSpell->comboCost > 0)
    {
        text.description += "\n\nNeeds " + std::to_string(pClassSpell->comboCost) + " combo points.";
    }

    if (pAura != nullptr)
    {
        const int enlightenment = skillMasteryValue(caster, "Enlightenment");
        std::string reserve;

        if (reservesNothing(caster))
        {
            reserve = "Holding it reserves no spell points.";
        }
        else if (pAura->utility)
        {
            // A legendary 32 wearer holds back hit points instead (SP:2461-2480).
            const double points = mawUtilityAuraReservation(pAura->cost, enlightenment);
            reserve = "Holding it reserves "
                + mawFillText(reservesHealth(caster) ? "<good>{n} hit points</>." : "<mana>{n} spell points</>.",
                    {{"n", points}});
        }
        else
        {
            const bool health = reservesHealth(caster);
            const double factor = health ? classHealthFactor(party, caster) : classSpellFactor(party, caster);
            const double percent = mawAuraReservedPercent(pAura->cost, factor, enlightenment);
            reserve = "Holding it reserves "
                + mawFillText(
                    health ? "<good>{p:1} %</> of maximum hit points." : "<mana>{p:1} %</> of maximum spell points.",
                    {{"p", percent}});
        }

        const std::optional<std::string> holder = heldBuffText(party, spellId);
        text.description += "\n\n" + reserve + "\n"
            + mawFillText(
                holder ? "<good>" + *holder + ".</>" : "<bad>Not held:</> cast it to hold it, again to let it go.", {});
    }

    // An Elementalist's cast time follows its stacks, which the rules move on each cast.
    if (line != "elementalist")
    {
        const int ticks =
            recoveryTicks(castAt(casterMastery), spellNumbersAtMastery(spell, casterMastery).recoveryTicks);
        text.description += "\n\nRecovery time: " + std::to_string(ticks);
    }

    return text;
}

std::optional<bool> MawSpellRules::toggleSpellRotation(Character &member) const
{
    if (mawClassLine(member.className) != "elementalist")
    {
        return std::nullopt;
    }

    bool &disabled = member.rulesetState.elementalRotationDisabled;
    disabled = !disabled;
    return !disabled;
}

std::optional<SkillMastery> MawSpellRules::classSpellMastery(const Character &caster, uint32_t spellId) const
{
    if (const MawClassSpell *pSpell = mawClassSpell(caster.className, spellId))
    {
        return SkillMastery(pSpell->mastery);
    }

    if (mawClassLine(caster.className) == "elementalist" && spellId >= 1 && spellId <= 44
        && caster.knownSpellIds.contains(spellId))
    {
        return SkillMastery::None;
    }

    return std::nullopt;
}

std::optional<std::string> MawSpellRules::castRefusal(const Party &party, size_t casterIndex, uint32_t spellId) const
{
    const Character *pCaster = party.member(casterIndex);
    const MawClassSpell *pClassSpell = pCaster != nullptr ? mawClassSpell(pCaster->className, spellId) : nullptr;

    if (pClassSpell == nullptr || pClassSpell->comboCost <= 0
        || m_rules.classRuntime(*pCaster).comboPoints >= pClassSpell->comboCost)
    {
        return std::nullopt;
    }

    return "Not enough combo points";
}

void MawSpellRules::afterCast(
    Party &party,
    size_t casterIndex,
    uint32_t spellId,
    const SpellTable &spellTable,
    bool indoor,
    bool fromSpellbook) const
{
    Character *pCaster = party.member(casterIndex);

    // Each offensive cast of an Elementalist builds a stack and turns the quick or attack spell it was to another
    // known spell of the kind bound there; switching the rotation off stops both (MCC:509-537).
    if (pCaster != nullptr && mawClassLine(pCaster->className) == "elementalist"
        && mawElementalistOffensiveSpell(spellId) && !pCaster->rulesetState.elementalRotationDisabled)
    {
        MawClassRuntime &runtime = m_rules.classRuntime(*pCaster);
        // The idle window the stacks then wait out comes from this cast's delay, read before its stack: other casts,
        // the stats page and the leech floor leave it alone (Classes.lua:533, FCOR-2-20).
        runtime.elementalLastDelayTicks = castRecoveryTicks(party, *pCaster, spellId, spellTable);
        runtime.elementalStacks = fromSpellbook ? 1 : runtime.elementalStacks + 1;
        runtime.elementalIdleSeconds = 0;
        runtime.elementalDecaySeconds = 0;
        rotateElementalistSpells(*pCaster, runtime, spellId, spellTable, indoor);
    }

    const MawClassSpell *pClassSpell = pCaster != nullptr ? mawClassSpell(pCaster->className, spellId) : nullptr;

    if (pClassSpell != nullptr && pClassSpell->comboCost > 0)
    {
        MawClassRuntime &runtime = m_rules.classRuntime(*pCaster);
        runtime.comboPoints = std::max(0.0, runtime.comboPoints - pClassSpell->comboCost);
    }
}

int MawSpellRules::manaCost(const CharacterSpellCast &cast, int tableCost) const
{
    const uint32_t spellId = uint32_t(cast.pSpell->id);
    const MawSpellCategory category = mawSpellCategory(spellId);

    // Death Knights and Assassins pay fixed costs; switches cost nothing to throw.
    if (const MawClassSpell *pClassSpell = mawClassSpell(cast.pCaster->className, spellId))
    {
        return pClassSpell->toggle ? 0 : pClassSpell->cost;
    }

    // Auras reserve mana instead of costing it.
    if (mawAura(spellId) != nullptr)
    {
        return 0;
    }

    if (category == MawSpellCategory::Other)
    {
        return tableCost;
    }

    if (spellId == DragonFear)
    {
        static constexpr std::array<int, 4> DragonFearCosts = {15, 15, 25, 30};
        return DragonFearCosts[size_t(std::clamp(int(cast.mastery), 1, 4)) - 1];
    }

    if (spellId == FlameBlast)
    {
        static constexpr std::array<int, 4> FlameBlastCosts = {25, 40, 50, 60};
        return FlameBlastCosts[size_t(std::clamp(int(cast.mastery), 1, 4)) - 1];
    }

    const Character &caster = *cast.pCaster;
    const double personality = mawPersonalityCostFactor(sheetOf(cast).personality.actual, m_rules.state().totalLevel());

    // Grandmaster Mass Distortion costs by level, for Elementalists too: MAW applies it after their branch
    // (SP:2270-2277, SPL-12).
    if (spellId == MassDistortion && cast.mastery >= SkillMastery::Grandmaster)
    {
        return int(std::ceil(std::pow(std::min(double(caster.level), 255.0), 1.4) / 12.5 * personality));
    }

    // An Elementalist's stacks raise the base and then the whole cost (SP:2270-2272).
    if (mawClassLine(caster.className) == "elementalist" && mawElementalistOffensiveSpell(spellId))
    {
        const MawAscension ascension = mawAscension(caster, MawAscensionUse::Cost);
        const int stacks = m_rules.classRuntime(caster).elementalStacks;
        const double ascended = mawRound(
            (tableCost + stacks) * (1 + 0.125 * ascension.skill) * std::pow(1.04, ascension.skill) * 0.5);
        return int(std::min(std::ceil(ascended * (1 + 0.075 * stacks) * personality), double(MawMaximumManaCost)));
    }

    int baseCost = tableCost;

    if (category == MawSpellCategory::Heal)
    {
        const std::optional<MawHealSpell> heal = mawHealSpell(spellId, cast.mastery, insanityHeals(m_rules));
        baseCost = heal ? heal->cost : tableCost;
    }

    const MawAscension ascension = mawAscension(caster, MawAscensionUse::Cost);
    return mawSpellManaCost(category, baseCost, ascension.skill, ascension.mastery, personality);
}

int MawSpellRules::recoveryTicks(const CharacterSpellCast &cast, int tableTicks) const
{
    const int ticks = baseRecoveryTicks(cast, tableTicks);
    // A dimension map's slower casting applies on the normal path only: crowd control, Dragon Fear and the Death
    // Knight's and Assassin's casts return before it (ST:163-217, 240-242; SPL-11).
    const uint32_t spellId = uint32_t(cast.pSpell->id);
    const std::string line = mawClassLine(cast.pCaster->className);
    const bool normalPath = line != "death_knight" && line != "assassin" && spellId != DragonFear
        && mawSpellCategory(spellId) != MawSpellCategory::CrowdControl;
    const std::optional<double> slower = m_rules.mapAffix(MawMapAffix::PlayerSpellRecovery);
    return slower && normalPath ? int(mawRound(ticks / (1 - *slower / 100))) : ticks;
}

int MawSpellRules::baseRecoveryTicks(const CharacterSpellCast &cast, int tableTicks) const
{
    const uint32_t spellId = uint32_t(cast.pSpell->id);
    const MawSpellCategory category = mawSpellCategory(spellId);
    const Character &caster = *cast.pCaster;

    // A Death Knight casts at their weapon's pace, an Assassin at half of it (MCC:877-886, 448-450).
    const std::string line = mawClassLine(caster.className);

    if ((line == "death_knight" || line == "assassin") && cast.pItemTable != nullptr)
    {
        const MawAttackDelay delay = mawCharacterAttackDelay(
            m_rules, caster, *cast.pItemTable, CharacterAttackMode::Melee, sheetOf(cast).speed.actual,
            m_rules.auraSkill(5, &caster));
        return line == "assassin" ? 2 * delay.delay : delay.delay;
    }

    if (spellId == DragonFear)
    {
        return 120;
    }

    // Flame Blast takes half again the breath's delay (zzMaw-Stats.lua:237-239).
    if (spellId == FlameBlast && cast.pItemTable != nullptr)
    {
        const MawAttackDelay breath = mawCharacterAttackDelay(m_rules, caster, *cast.pItemTable,
            CharacterAttackMode::DragonBreath, sheetOf(cast).speed.actual, m_rules.auraSkill(5, &caster));
        return int(mawRound(breath.delay * 1.5));
    }

    if (category == MawSpellCategory::CrowdControl)
    {
        return mawCrowdControlDelay(
            tableTicks, mawAscension(caster, MawAscensionUse::CrowdControlCastTime).skill, cast.skillLevel);
    }

    MawSpellDelayInputs inputs;
    inputs.tableDelay = tableTicks;
    inputs.speed = sheetOf(cast).speed.actual;
    inputs.ascensionSkill =
        category == MawSpellCategory::Other ? 0 : mawAscension(caster, MawAscensionUse::CastTime).skill;
    inputs.armorImpairmentPercent =
        cast.pItemTable != nullptr ? mawCharacterArmorImpairment(caster, *cast.pItemTable) : 0;
    inputs.hasteSkill = m_rules.auraSkill(5, &caster);
    inputs.buffScale = m_rules.buffScale();
    // A broken weapon's enchantment does not count (HasSpellHasteEnchant reads the active items; FITM-2-7).
    const auto spellSpeed = [](const EquippedItemRuntimeState &slot)
    {
        return slot.specialEnchantId == SpellSpeedSpecial && !slot.broken;
    };
    inputs.spellSpeedEnchantment = spellSpeed(caster.equipmentRuntime.offHand)
        || spellSpeed(caster.equipmentRuntime.mainHand) || spellSpeed(caster.equipmentRuntime.bow);
    const int delay = mawSpellDelay(inputs);

    // Elementalists cast half again as slowly, faster with their stacks (ST:228-236).
    if (mawClassLine(caster.className) == "elementalist")
    {
        return int(mawRound(delay * 1.5 / (1 + 0.05 * m_rules.classRuntime(caster).elementalStacks)));
    }

    return delay;
}

int MawSpellRules::castRecoveryTicks(
    const Party &party, const Character &caster, uint32_t spellId, const SpellTable &spellTable) const
{
    const SpellEntry *pSpell = spellTable.findById(int(spellId));
    const std::optional<std::string> school = resolveMagicSkillName(spellId);

    if (pSpell == nullptr || !school)
    {
        return 0;
    }

    const CharacterSkill *pSkill = caster.findSkill(*school);
    CharacterSpellCast cast;
    cast.pCaster = &caster;
    cast.pItemTable = party.itemTable();
    cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
    cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
    cast.pSpell = pSpell;
    cast.mastery = pSkill != nullptr ? pSkill->mastery : SkillMastery::Normal;
    cast.skillLevel = pSkill != nullptr ? pSkill->level : 0;
    cast.partyCount = int(party.members().size());
    return baseRecoveryTicks(cast, spellNumbersAtMastery(*pSpell, cast.mastery).recoveryTicks);
}

std::optional<int> MawSpellRules::healAmount(const CharacterSpellCast &cast) const
{
    const uint32_t spellId = uint32_t(cast.pSpell->id);
    const std::optional<MawHealSpell> heal = mawHealSpell(spellId, cast.mastery, insanityHeals(m_rules));

    if (!heal)
    {
        return std::nullopt;
    }

    // Shared Life counts half of its school skill.
    const double points = spellId == 54 ? cast.skillLevel / 2.0 : double(cast.skillLevel);
    // Shared Life gives back 3 per skill point at Master, 4 at Grandmaster (SP:850-855).
    const double sharedLifeCut = spellId == 54 && cast.mastery >= SkillMastery::Master
        ? (cast.mastery >= SkillMastery::Grandmaster ? 4.0 : 3.0) * cast.skillLevel
        : 0.0;

    // A scroll heals as the engine does; only Shared Life keeps MAW's table, at the scroll's skill with nothing of
    // the reader's and no map affix (SP:144-149, 836-849; FSPS-2-3).
    if (cast.fromScroll)
    {
        return spellId == 54
            ? std::optional<int>(int(mawRound(std::max(heal->base + heal->perPoint * points - sharedLifeCut, 0.0))))
            : std::nullopt;
    }

    const Character &caster = *cast.pCaster;
    MawHealSpell scaled = *heal;

    // A Shaman's every school strengthens the heals but Power Cure (SP:2370-2384).
    if (spellId != 77)
    {
        const double shaman = 1 + mawShamanSchoolSum(caster) / 400;
        scaled.base *= shaman;
        scaled.perPoint *= shaman;
    }

    const double healing = 1 - m_rules.mapAffix(MawMapAffix::Healing).value_or(0) / 100;
    const double amount = mawHealAmount(scaled, points, mawAscension(caster, MawAscensionUse::Heal).skill,
        sheetOf(cast).personality.actual, caster.level) * healing;

    return int(mawRound(std::max(amount - sharedLifeCut, 0.0)));
}

int MawSpellRules::reservedSpellPoints(const Party &party, size_t memberIndex) const
{
    const Character *pMember = party.member(memberIndex);
    return pMember != nullptr && !reservesHealth(*pMember) ? reservedPoints(party, memberIndex, false) : 0;
}

void MawSpellRules::afterHeal(
    Party &party, size_t casterIndex, int healed, int overheal, int manaCost, float &recoverySeconds) const
{
    Character *pCaster = party.member(casterIndex);

    if (pCaster == nullptr || healed <= 0 || overheal <= 0)
    {
        return;
    }

    const double share = double(overheal) / healed;

    if (mawWearsLegendaryAffix(*pCaster, 34))
    {
        pCaster->spellPoints += int(std::floor(manaCost * share));
    }

    if (mawWearsLegendaryAffix(*pCaster, 35))
    {
        recoverySeconds *= float(1 - share / 2);
    }
}

bool MawSpellRules::shareLife(Party &party, int heal) const
{
    struct Share
    {
        size_t memberIndex = 0;
        int64_t health = 0;
        int64_t maximum = 0;
    };

    // The dead, eradicated and petrified stay out; the unconscious join with their negative hit points.
    std::vector<Share> shares;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character &member = party.members()[memberIndex];

        if (!member.conditions.test(size_t(CharacterCondition::Dead))
            && !member.conditions.test(size_t(CharacterCondition::Eradicated))
            && !member.conditions.test(size_t(CharacterCondition::Petrified)))
        {
            shares.push_back({memberIndex, member.health, Party::effectiveMaximumHealth(member)});
        }
    }

    std::stable_sort(shares.begin(), shares.end(),
        [](const Share &left, const Share &right)
        {
            return left.health > right.health;
        });

    // Members join from the healthiest down while the pool stays at or above zero, so nobody is dragged down.
    int64_t remaining = std::max(heal, 0);
    size_t sharing = 0;

    while (sharing < shares.size() && remaining + shares[sharing].health >= 0)
    {
        remaining += shares[sharing].health;
        shares[sharing].health = 0;
        ++sharing;
    }

    shares.resize(sharing);

    // Even portions to everyone below their maximum, the overflow of the full going round again.
    while (remaining > 0)
    {
        int64_t wanting = 0;
        int64_t smallestDeficit = 0;

        for (const Share &share : shares)
        {
            const int64_t deficit = share.maximum - share.health;

            if (deficit > 0)
            {
                smallestDeficit = wanting == 0 ? deficit : std::min(smallestDeficit, deficit);
                ++wanting;
            }
        }

        if (wanting == 0)
        {
            break;
        }

        const int64_t portion = std::max<int64_t>(1, std::min(smallestDeficit, remaining / wanting));
        int64_t given = 0;

        for (Share &share : shares)
        {
            const int64_t amount = std::min({portion, share.maximum - share.health, remaining - given});

            if (amount > 0)
            {
                share.health += amount;
                given += amount;
            }
        }

        remaining -= given;

        if (given == 0)
        {
            break;
        }
    }

    for (const Share &share : shares)
    {
        party.member(share.memberIndex)->health = int(share.health);

        if (share.health > 0)
        {
            party.clearMemberCondition(share.memberIndex, CharacterCondition::Unconscious);
        }
    }

    return true;
}

void MawSpellRules::memberLeaving(const Party &party, size_t memberIndex) const
{
    // The alchemist's slot moves with the members too (ROB-2-3).
    int32_t &alchemist = m_rules.state().alchemistMember;

    if (alchemist == int32_t(memberIndex))
    {
        alchemist = -1;
    }
    else if (alchemist > int32_t(memberIndex))
    {
        --alchemist;
    }

    std::unordered_map<uint32_t, uint32_t> &holders = m_rules.state().auraHolders;

    for (auto it = holders.begin(); it != holders.end();)
    {
        if (it->second == memberIndex)
        {
            it = holders.erase(it);
            continue;
        }

        if (it->second > memberIndex && it->second != MawGameState::FixedAuraHolder)
        {
            --it->second;
        }

        ++it;
    }
}

int MawSpellRules::reservedHitPoints(const Party &party, size_t memberIndex) const
{
    const Character *pMember = party.member(memberIndex);
    return pMember != nullptr && reservesHealth(*pMember) ? reservedPoints(party, memberIndex, true) : 0;
}

int MawSpellRules::reservedPoints(const Party &party, size_t memberIndex, bool health) const
{
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || reservesNothing(*pMember))
    {
        return 0;
    }

    const int maximum =
        health ? Party::effectiveMaximumHealth(*pMember) : Party::effectiveMaximumSpellPoints(*pMember);
    const double factor = health ? classHealthFactor(party, *pMember) : classSpellFactor(party, *pMember);
    const int enlightenment = skillMasteryValue(*pMember, "Enlightenment");
    double percent = 0;
    int flat = 0;

    for (const auto &[spellId, holder] : m_rules.state().auraHolders)
    {
        const MawAura *pAura = mawAura(spellId);

        if (holder != memberIndex || pAura == nullptr)
        {
            continue;
        }

        if (pAura->utility)
        {
            flat += mawUtilityAuraReservation(pAura->cost, enlightenment);
        }
        else
        {
            percent += mawAuraReservedPercent(pAura->cost, factor, enlightenment);
        }
    }

    return std::min(maximum, int(std::ceil(maximum * percent / 100)) + flat);
}

AuraReservationCost MawSpellRules::auraCost(const Party &party, size_t memberIndex, uint32_t spellId) const
{
    AuraReservationCost cost;
    const Character *pMember = party.member(memberIndex);
    const MawAura *pAura = mawAura(spellId);

    if (pMember == nullptr || pAura == nullptr)
    {
        return cost;
    }

    cost.flat = pAura->utility;
    cost.health = reservesHealth(*pMember);
    cost.free = reservesNothing(*pMember);

    if (cost.free)
    {
        return cost;
    }

    const int maximum =
        cost.health ? Party::effectiveMaximumHealth(*pMember) : Party::effectiveMaximumSpellPoints(*pMember);
    const int enlightenment = skillMasteryValue(*pMember, "Enlightenment");

    if (pAura->utility)
    {
        cost.points = mawUtilityAuraReservation(pAura->cost, enlightenment);
        return cost;
    }

    const double factor = cost.health ? classHealthFactor(party, *pMember) : classSpellFactor(party, *pMember);
    cost.percent = mawAuraReservedPercent(pAura->cost, factor, enlightenment);
    cost.points = int(std::ceil(maximum * cost.percent / 100));
    return cost;
}

std::vector<uint32_t> MawSpellRules::heldAurasWithoutBuffSlot(const Party &) const
{
    // Empower Magic and Meditation drive no engine buff slot.
    std::vector<uint32_t> auras;

    for (const uint32_t spellId : {28u, 56u})
    {
        if (m_rules.state().auraHolders.contains(spellId))
        {
            auras.push_back(spellId);
        }
    }

    return auras;
}

std::optional<std::string> MawSpellRules::heldBuffText(const Party &party, uint32_t spellId) const
{
    const auto held = m_rules.state().auraHolders.find(spellId);

    if (held != m_rules.state().auraHolders.end() && held->second == MawGameState::FixedAuraHolder)
    {
        const auto fixed = m_rules.state().fixedAuraMaps.find(spellId);
        return fixed != m_rules.state().fixedAuraMaps.end() && fixed->second.empty() ? "Temple blessing"
                                                                                     : "Blessing of this place";
    }

    const Character *pHolder = held != m_rules.state().auraHolders.end() ? party.member(held->second) : nullptr;

    if (pHolder == nullptr)
    {
        return std::nullopt;
    }

    return "Held by " + pHolder->name;
}

SpellSplash MawSpellRules::spellSplash(uint32_t spellId, SkillMastery mastery) const
{
    constexpr uint32_t ShrinkingRay = 92;

    if (spellId != ShrinkingRay)
    {
        return {};
    }

    return {size_t(std::max(int(mastery), 1) - 1), 512.0f};
}

bool MawSpellRules::ignoresCrowdControl(const ActorRulesetFacts &target) const
{
    return mawIgnoresCrowdControl(target);
}

bool MawSpellRules::castSourceBuff(Party &party, uint32_t spellId, BuffSource source) const
{
    if (mawAura(spellId) == nullptr)
    {
        return false;
    }

    if (source == BuffSource::Hireling)
    {
        return true;
    }

    MawGameState &state = m_rules.state();
    const auto held = state.auraHolders.find(spellId);

    if (held != state.auraHolders.end() && held->second != MawGameState::FixedAuraHolder)
    {
        return true;
    }

    // A temple's blessing comes through its map event too; it stays the temple's.
    const auto fixed = state.fixedAuraMaps.find(spellId);

    if (source == BuffSource::MapEvent && held != state.auraHolders.end() && fixed != state.fixedAuraMaps.end()
        && fixed->second.empty())
    {
        return true;
    }

    state.auraHolders[spellId] = MawGameState::FixedAuraHolder;
    state.fixedAuraMaps[spellId] = source == BuffSource::Temple ? std::string() : m_rules.currentMap();
    updateAuras(party, 0.0f);
    return true;
}

std::optional<int> MawSpellRules::auraDamage(const Party &party, uint32_t spellId) const
{
    const std::optional<MawAuraSource> source = m_rules.activeAura(spellId);
    const SpellEntry *pSpell = m_rules.spellTable() != nullptr ? m_rules.spellTable()->findById(int(spellId)) : nullptr;
    // A scroll's or temple's aura burns as the first member's, as MAW names member 1 its caster.
    const Character *pHolder = source ? party.member(source->holder) : nullptr;

    if (pHolder == nullptr || pSpell == nullptr)
    {
        return std::nullopt;
    }

    CharacterSpellCast cast;
    cast.pCaster = pHolder;
    cast.pItemTable = party.itemTable();
    cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
    cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
    cast.pSpell = pSpell;
    cast.mastery = SkillMastery(std::clamp(source->mastery, 1, 4));
    cast.skillLevel = uint32_t(std::max(1.0, source->skill));
    cast.partyCount = int(std::max<size_t>(1, party.members().size()));
    return m_rules.gameRules().combat.rollSpellDamage(cast);
}

std::optional<float> MawSpellRules::partyBuffSeconds(
    const Party &party,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery mastery,
    bool fromScroll) const
{
    constexpr uint32_t Invisibility = 19;
    constexpr uint32_t Fly = 21;

    if (spellId == Fly && fromScroll && party.members().size() == 1)
    {
        return 7.0f * 3600.0f;
    }

    if (spellId != Invisibility || mastery < SkillMastery::Master)
    {
        return std::nullopt;
    }

    const float steps = float(int(mastery) - 2);
    return (15.0f * steps + steps * float(skillLevel)) * 1.5f * 60.0f;
}

bool MawSpellRules::keepsScroll(const Party &party, uint32_t spellId) const
{
    constexpr std::array<uint32_t, 5> TravelScrolls = {16, 21, 27, 31, 33};
    return party.members().size() == 1 && listed(TravelScrolls, spellId);
}

bool MawSpellRules::castsAsAura(const Party &party, size_t casterIndex, uint32_t spellId) const
{
    const Character *pMember = party.member(casterIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    const MawClassSpell *pClassSpell = mawClassSpell(pMember->className, spellId);
    return (pClassSpell != nullptr && pClassSpell->toggle) || mawAura(spellId) != nullptr;
}

std::optional<AuraCastResult> MawSpellRules::castAura(Party &party, size_t casterIndex, uint32_t spellId) const
{
    // A Death Knight's Blood Leech, Superior Blood Leech and Death Grasp are switches, one on at a time
    // (MCC:843-872).
    if (Character *pMember = party.member(casterIndex))
    {
        const MawClassSpell *pClassSpell = mawClassSpell(pMember->className, spellId);

        if (pClassSpell != nullptr && pClassSpell->toggle)
        {
            std::vector<uint32_t> &toggles = pMember->rulesetState.classToggles;
            const auto on = std::find(toggles.begin(), toggles.end(), spellId);

            if (on != toggles.end())
            {
                toggles.erase(on);
                return AuraCastResult::Released;
            }

            toggles.assign(1, spellId);
            return AuraCastResult::Held;
        }
    }

    const MawAura *pAura = mawAura(spellId);
    const Character *pCaster = party.member(casterIndex);

    if (pAura == nullptr || pCaster == nullptr)
    {
        return std::nullopt;
    }

    std::unordered_map<uint32_t, uint32_t> &holders = m_rules.state().auraHolders;
    const auto held = holders.find(spellId);

    if (held != holders.end() && held->second == casterIndex)
    {
        holders.erase(held);
        return AuraCastResult::Released;
    }

    if (!reservesNothing(*pCaster))
    {
        // The new reservation has to fit in what the caster's other auras leave of the pool (HP for a legendary 32
        // wearer). A utility aura has to find its full cost free, before Enlightenment's discount (SP:2779-2794).
        const bool health = reservesHealth(*pCaster);
        const int maximum =
            health ? Party::effectiveMaximumHealth(*pCaster) : Party::effectiveMaximumSpellPoints(*pCaster);
        const double factor = health ? classHealthFactor(party, *pCaster) : classSpellFactor(party, *pCaster);
        const int enlightenment = skillMasteryValue(*pCaster, "Enlightenment");
        const int needed = pAura->utility
            ? int(mawRound(pAura->cost))
            : int(std::ceil(maximum * mawAuraReservedPercent(pAura->cost, factor, enlightenment) / 100));

        if (reservedPoints(party, casterIndex, health) + needed > maximum)
        {
            return AuraCastResult::NotEnoughMana;
        }
    }

    // A member takes over a scroll's, pedestal's or temple's aura.
    holders[spellId] = uint32_t(casterIndex);
    m_rules.state().fixedAuraMaps.erase(spellId);
    return AuraCastResult::Held;
}

void MawSpellRules::updateAuras(Party &party, float deltaSeconds) const
{
    // MAW applies its auras on a half-second timer (mawBuffApply, zzMaw-Timers.lua:95); a zero step (a cast, a toggle,
    // a pedestal) applies them at once.
    constexpr float AuraTickSeconds = 0.5f;

    if (deltaSeconds > 0.0f)
    {
        m_auraSeconds += deltaSeconds;

        if (m_auraSeconds < AuraTickSeconds)
        {
            return;
        }
    }

    m_auraSeconds = 0.0f;
    std::unordered_map<uint32_t, uint32_t> &holders = m_rules.state().auraHolders;
    std::unordered_map<uint32_t, std::string> &fixedMaps = m_rules.state().fixedAuraMaps;
    std::unordered_map<uint32_t, MawAuraSource> sources;

    // A new map ends the temple's auras, and an outdoor one the scroll and pedestal auras of other maps (SP:2693-2730).
    if (m_rules.currentMap() != m_auraMap)
    {
        const bool firstUpdate = m_auraMap.empty();
        const std::string &map = m_rules.currentMap();
        const bool outdoor = map.size() > 4 && map.compare(map.size() - 4, 4, ".odm") == 0;
        m_auraMap = map;

        for (auto it = fixedMaps.begin(); it != fixedMaps.end() && !firstUpdate;)
        {
            if (it->second.empty() || (outdoor && it->second != map))
            {
                holders.erase(it->first);
                it = fixedMaps.erase(it);
                continue;
            }

            ++it;
        }
    }

    for (auto it = holders.begin(); it != holders.end();)
    {
        // A scroll, pedestal or temple holds its aura at skill 7, Master, level 40 (getSpecialBuffSkill).
        if (it->second == MawGameState::FixedAuraHolder)
        {
            if (!fixedMaps.contains(it->first))
            {
                it = holders.erase(it);
                continue;
            }

            sources[it->first] = MawAuraSource{7, 3, 40, 0};
            ++it;
            continue;
        }

        // A holder who left the party takes the aura along.
        if (it->second >= party.members().size())
        {
            it = holders.erase(it);
            continue;
        }

        const Character &holder = *party.member(it->second);
        const MawAura *pAura = mawAura(it->first);

        // An unconscious holder's aura is off but keeps its reservation.
        if (pAura != nullptr && memberConscious(holder))
        {
            const std::string school = mawSpellSchoolSkill(it->first);
            const CharacterSkill *pSkill = holder.findSkill(school);
            MawAuraSource source;
            source.skill = std::min(pSkill != nullptr ? double(pSkill->level) : 0.0, pAura->skillCap);
            source.mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
            source.level = holder.level;
            source.holder = it->second;
            sources[it->first] = source;
        }

        ++it;
    }

    // The rules know the held auras before any buff below is applied: applying one rebuilds the members' stats, and
    // Day of the Gods and the stat auras read the sources there (MawSkillRules::applyStatBonuses).
    m_rules.setActiveAuras(sources);

    const auto source = [&sources](uint32_t spellId) -> const MawAuraSource *
    {
        const auto it = sources.find(spellId);
        return it != sources.end() ? &it->second : nullptr;
    };

    struct Slot
    {
        int power = 0;
        uint32_t spellId = 0;
        const MawAuraSource *pSource = nullptr;
    };

    std::map<PartyBuffId, Slot> partySlots;
    std::map<CharacterBuffId, Slot> characterSlots;
    const MawAuraSource *pHourOfPower = source(HourOfPower);
    const MawAuraSource *pDayOfProtection = source(DayOfProtection);

    // Resistances: each aura's own, or Day of Protection's at skill / 1.4, whichever is stronger.
    static constexpr std::array<std::pair<uint32_t, PartyBuffId>, 6> ResistanceAuras = {{
        {3, PartyBuffId::FireResistance}, {14, PartyBuffId::AirResistance}, {25, PartyBuffId::WaterResistance},
        {36, PartyBuffId::EarthResistance}, {58, PartyBuffId::MindResistance}, {69, PartyBuffId::BodyResistance},
    }};

    // Dimension affix 33 weakens every aura of the map.
    const double buffScale = m_rules.buffScale();

    for (const auto &[spellId, buffId] : ResistanceAuras)
    {
        const MawAuraSource *pOwn = source(spellId);
        double strength = pOwn != nullptr ? mawAuraFlat(20, 2, pOwn->level, pOwn->skill, buffScale) : 0;

        if (pDayOfProtection != nullptr)
        {
            strength = std::max(strength,
                mawAuraFlat(20, 2, pDayOfProtection->level, pDayOfProtection->skill / 1.4, buffScale));
        }

        if (pOwn != nullptr || pDayOfProtection != nullptr)
        {
            partySlots[buffId] = {int(mawRound(strength)), pOwn != nullptr ? spellId : DayOfProtection,
                pOwn != nullptr ? pOwn : pDayOfProtection};
        }
    }

    // Stone Skin, Haste and Shield, or Hour of Power at skill / 1.5.
    const MawAuraSource *pStoneskin = source(38);

    if (pStoneskin != nullptr || pHourOfPower != nullptr)
    {
        const double own =
            pStoneskin != nullptr ? mawAuraFlat(20, 2, pStoneskin->level, pStoneskin->skill, buffScale) : 0;
        const double hour = pHourOfPower != nullptr
            ? mawAuraFlat(20, 2, pHourOfPower->level, pHourOfPower->skill / 1.5, buffScale)
            : 0;
        partySlots[PartyBuffId::Stoneskin] = {int(mawRound(std::max(own, hour))),
            own >= hour ? 38u : HourOfPower, own >= hour ? pStoneskin : pHourOfPower};
    }

    for (const auto &[spellId, buffId] : std::array<std::pair<uint32_t, PartyBuffId>, 2>{{
             {5, PartyBuffId::Haste}, {17, PartyBuffId::Shield}}})
    {
        if (const MawAuraSource *pOwn = source(spellId))
        {
            partySlots[buffId] = {0, spellId, pOwn};
        }
        else if (pHourOfPower != nullptr)
        {
            partySlots[buffId] = {0, HourOfPower, pHourOfPower};
        }
    }

    // Engine flags: the effects themselves are MAW's (combat and sheet rules read the auras).
    static constexpr std::array<std::pair<uint32_t, PartyBuffId>, 6> FlagAuras = {{
        {51, PartyBuffId::Heroism}, {83, PartyBuffId::DayOfGods}, {8, PartyBuffId::Immolation},
        {75, PartyBuffId::ProtectionFromMagic}, {12, PartyBuffId::WizardEye}, {27, PartyBuffId::WaterWalk},
    }};

    for (const auto &[spellId, buffId] : FlagAuras)
    {
        // A Shadow boss near the party blinds the Wizard Eye aura too (zzMaw-Spells.lua:2993-3005).
        if (buffId == PartyBuffId::WizardEye && m_rules.shadowBossNearby())
        {
            continue;
        }

        if (const MawAuraSource *pOwn = source(spellId))
        {
            // Immolation burns by the holder's skill; Protection from Magic keeps its charges, given back each update.
            const int power = spellId == 8 ? int(pOwn->skill) : spellId == 75 ? ProtectionFromMagicCharges : 0;
            partySlots[buffId] = {power, spellId, pOwn};
        }
    }

    // A Magic Protection potion shields the whole party like the aura while it lasts (SP:2985-2990).
    std::optional<MawAuraSource> protectionPotion;

    for (size_t memberIndex = 0; memberIndex < party.members().size() && !protectionPotion; ++memberIndex)
    {
        protectionPotion = MawRules::potionAura(ProtectionFromMagic, *party.member(memberIndex));

        if (protectionPotion)
        {
            protectionPotion->holder = uint32_t(memberIndex);
        }
    }

    if (protectionPotion && source(ProtectionFromMagic) == nullptr)
    {
        partySlots[PartyBuffId::ProtectionFromMagic] = {
            ProtectionFromMagicCharges, ProtectionFromMagic, &*protectionPotion};
    }

    // A party of one always sees by Wizard Eye (skill 10, Expert) and Torch Light (radius 3) (SP:1089-1096, 2968-2975).
    static const MawAuraSource SoloWizardEye{10, 2, 0, 0};
    static const MawAuraSource SoloTorch{1, 1, 0, 0};
    const bool solo = party.members().size() == 1;

    if (solo && !partySlots.contains(PartyBuffId::WizardEye) && !m_rules.shadowBossNearby())
    {
        partySlots[PartyBuffId::WizardEye] = {0, 12, &SoloWizardEye};
    }

    if (const MawAuraSource *pTorch = source(1))
    {
        partySlots[PartyBuffId::TorchLight] = {std::max(pTorch->mastery + 1, solo ? 3 : 0), 1, pTorch};
    }
    else if (solo)
    {
        partySlots[PartyBuffId::TorchLight] = {3, 1, &SoloTorch};
    }

    if (const MawAuraSource *pBless = source(46))
    {
        characterSlots[CharacterBuffId::Bless] = {
            int(mawRound(mawAuraFlat(20, 2, pBless->level, pBless->skill, buffScale))), 46, pBless};
    }

    if (const MawAuraSource *pFate = source(47))
    {
        characterSlots[CharacterBuffId::Fate] = {0, 47, pFate};
    }
    else if (pHourOfPower != nullptr)
    {
        characterSlots[CharacterBuffId::Fate] = {0, HourOfPower, pHourOfPower};
    }

    // Regeneration heals by MAW's regeneration, not by the engine's periodic tick (spell id 0). Fire Aura and Vampiric
    // Aura only show: their effects are MAW's.
    static constexpr std::array<std::pair<uint32_t, CharacterBuffId>, 6> CharacterFlagAuras = {{
        {50, CharacterBuffId::Preservation}, {71, CharacterBuffId::Regeneration}, {73, CharacterBuffId::Hammerhands},
        {95, CharacterBuffId::PainReflection}, {4, CharacterBuffId::FireAura}, {91, CharacterBuffId::VampiricWeapon},
    }};

    for (const auto &[spellId, buffId] : CharacterFlagAuras)
    {
        if (const MawAuraSource *pOwn = source(spellId))
        {
            characterSlots[buffId] = {0, spellId == 71 ? 0 : spellId, pOwn};
        }
    }

    // Apply what changed, refresh what runs low, and clear the slots no aura sets any more.
    for (const auto &[buffId, slot] : partySlots)
    {
        const PartyBuffState *pBuff = party.partyBuff(buffId);

        if (pBuff == nullptr || pBuff->power != slot.power || pBuff->spellId != slot.spellId
            || pBuff->remainingSeconds < AuraSeconds / 2)
        {
            const SkillMastery mastery = buffId == PartyBuffId::ProtectionFromMagic
                ? SkillMastery::Grandmaster
                : SkillMastery(slot.pSource->mastery);
            party.applyPartyBuff(buffId, AuraSeconds, slot.power, slot.spellId, auraBuffSkill(*slot.pSource),
                mastery, slot.pSource->holder);
        }
    }

    // A member's Preservation potion (Protection, Paladin's) acts as the aura for its drinker alone.
    std::vector<std::optional<MawAuraSource>> preservationPotions(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        preservationPotions[memberIndex] = MawRules::potionAura(Preservation, *party.member(memberIndex));
        std::map<CharacterBuffId, Slot> memberSlots = characterSlots;

        if (preservationPotions[memberIndex] && source(Preservation) == nullptr)
        {
            preservationPotions[memberIndex]->holder = uint32_t(memberIndex);
            memberSlots[CharacterBuffId::Preservation] = {0, Preservation, &*preservationPotions[memberIndex]};
        }

        for (const auto &[buffId, slot] : memberSlots)
        {
            const CharacterBuffState *pBuff = party.characterBuff(memberIndex, buffId);

            if (pBuff == nullptr || pBuff->power != slot.power || pBuff->spellId != slot.spellId
                || pBuff->remainingSeconds < AuraSeconds / 2)
            {
                party.applyCharacterBuff(memberIndex, buffId, AuraSeconds, slot.power, slot.spellId,
                    auraBuffSkill(*slot.pSource), SkillMastery(slot.pSource->mastery), slot.pSource->holder);
            }
        }
    }

    std::vector<uint32_t> appliedPartyBuffs;
    std::vector<uint32_t> appliedCharacterBuffs;

    for (const auto &[buffId, slot] : partySlots)
    {
        appliedPartyBuffs.push_back(uint32_t(buffId));
    }

    for (const auto &[buffId, slot] : characterSlots)
    {
        appliedCharacterBuffs.push_back(uint32_t(buffId));
    }

    const bool preservationPotion = std::any_of(preservationPotions.begin(), preservationPotions.end(),
        [](const std::optional<MawAuraSource> &potion)
        {
            return potion.has_value();
        });

    const bool preservationAura = characterSlots.contains(CharacterBuffId::Preservation);

    if (preservationPotion && !preservationAura)
    {
        appliedCharacterBuffs.push_back(uint32_t(CharacterBuffId::Preservation));

        // A released aura ends at once for every member that no potion of their own keeps (SP:2877-2888, FSPS-2-7).
        if (m_preservationAuraApplied)
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                if (!preservationPotions[memberIndex])
                {
                    party.clearCharacterBuff(memberIndex, CharacterBuffId::Preservation);
                }
            }
        }
    }

    m_preservationAuraApplied = preservationAura;

    for (uint32_t buffId : m_appliedPartyBuffs)
    {
        if (std::find(appliedPartyBuffs.begin(), appliedPartyBuffs.end(), buffId) == appliedPartyBuffs.end())
        {
            party.clearPartyBuff(PartyBuffId(buffId));
        }
    }

    for (uint32_t buffId : m_appliedCharacterBuffs)
    {
        if (std::find(appliedCharacterBuffs.begin(), appliedCharacterBuffs.end(), buffId)
            == appliedCharacterBuffs.end())
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.clearCharacterBuff(memberIndex, CharacterBuffId(buffId));
            }
        }
    }

    m_appliedPartyBuffs = std::move(appliedPartyBuffs);
    m_appliedCharacterBuffs = std::move(appliedCharacterBuffs);

    // Each member's staff resists for the whole party (zzMaw-Items.lua:3294-3316).
    int staffResistance = 0;

    for (const Character &member : party.members())
    {
        staffResistance += party.itemTable() != nullptr
            ? mawStaffPartyResistance(m_rules, member, *party.itemTable())
            : 0;
    }

    m_rules.setPartyStaffResistance(staffResistance);

    // Mana (or HP) stays below each holder's unreserved pool.
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character &member = *party.member(memberIndex);
        const int pool = Party::effectiveMaximumSpellPoints(member) - reservedSpellPoints(party, memberIndex);
        member.spellPoints = std::min(member.spellPoints, std::max(pool, 0));
        // A legendary 32 wearer's auras hold back hit points instead.
        const int healthPool = Party::effectiveMaximumHealth(member) - reservedHitPoints(party, memberIndex);
        member.health = std::min(member.health, std::max(healthPool, 1));
    }
}

std::optional<float> MawSpellRules::crowdControlSeconds(const CrowdControlCast &cast) const
{
    constexpr uint32_t Stun = 34;
    static thread_local std::mt19937 rng(std::random_device{}());

    // A dimension map's control resistance: the control sometimes fails outright (MAW lowers only Stun's chance;
    // DEVIATIONS.md).
    const std::optional<double> controlResistance = m_rules.mapAffix(MawMapAffix::ControlResistance);
    const auto resisted = [&controlResistance]()
    {
        return controlResistance && std::uniform_real_distribution<double>(0.0, 1.0)(rng) < *controlResistance / 100;
    };

    // An Unstoppable boss shrugs off every crowd control (checkDebuffDuration and calcDebuffDuration return 0,
    // stage_stunSpellPrime fails the Stun, SP:1817-1841, DM:347).
    if ((cast.spellId == Stun || mawCrowdControlSpell(cast.spellId) != nullptr) && cast.pTargetFacts != nullptr
        && mawIgnoresCrowdControl(*cast.pTargetFacts))
    {
        return 0.0f;
    }

    // Stun keeps a success roll; it paralyses one game minute plus skill x mastery ticks (TW:50-58).
    if (cast.spellId == Stun)
    {
        if (resisted())
        {
            return 0.0f;
        }

        const double chance = mawStunChance(cast.targetLevel, cast.resistance, cast.skillLevel, cast.boss);
        return std::uniform_real_distribution<double>(0.0, 1.0)(rng) < chance
            ? 2.0f + float(cast.skillLevel) * float(std::max(1, int(cast.mastery))) / 128.0f
            : 0.0f;
    }

    const MawCrowdControlSpell *pSpell = mawCrowdControlSpell(cast.spellId);

    if (pSpell == nullptr || cast.pCaster == nullptr)
    {
        return std::nullopt;
    }

    if (resisted())
    {
        return 0.0f;
    }

    const double minutes = mawCrowdControlMinutes(
        *pSpell,
        cast.mastery,
        mawAscension(*cast.pCaster, MawAscensionUse::CrowdControl).skill,
        cast.resistance,
        cast.partySize <= 1);
    return float(m_rules.diminishedCrowdControlSeconds(
        cast.targetKey, pSpell->group, cast.nowSeconds, minutes * 2, cast.boss));
}

std::optional<std::string> MawSpellRules::removeAllBuffs(Party &) const
{
    m_rules.state().auraHolders.clear();
    m_rules.state().fixedAuraMaps.clear();
    return "All buffs have been removed";
}

bool MawSpellRules::tabCyclesSpellbookSchools() const
{
    return true;
}

bool MawSpellRules::protectionFromMagicRaisesResistances() const
{
    return false;
}

size_t MawSpellRules::extraPermanentWisps(SkillMastery mastery) const
{
    return size_t(std::max(0, 2 * int(mastery) - 3));
}

bool MawSpellRules::raiseDeadLiftsEradication(SkillMastery mastery) const
{
    return mastery >= SkillMastery::Grandmaster;
}

float MawSpellRules::spiritLashRadius(SkillMastery mastery) const
{
    return mastery == SkillMastery::Master ? 384.0f : 768.0f;
}

bool MawSpellRules::sunrayWorksIndoors() const
{
    // MAW removes the engine's outdoor-only refusal for Sunray (SP:1006, FSPS-2-1).
    return true;
}

bool MawSpellRules::quickCastSpreadsDebuff(uint32_t spellId) const
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Slow:
        case SpellId::Charm:
        case SpellId::VampireCharm:
        case SpellId::Berserk:
        case SpellId::Paralyze:
        case SpellId::Enslave:
        case SpellId::DarkGrasp:
        case SpellId::ControlUndead:
            return true;
        default:
            return false;
    }
}
}
