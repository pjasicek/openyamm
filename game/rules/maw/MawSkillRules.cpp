#include "game/rules/maw/MawSkillRules.h"
#include "engine/Localization.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/party/Party.h"
#include "game/party/SpellSchool.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawClassSpells.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMonsterInspect.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/rules/maw/MawTexts.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <sstream>
#include <tuple>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t RegenerationAura = 71;
constexpr uint32_t MeditationAura = 56;

bool noMeditationAura(const Character &member)
{
    static const std::array<const char *, 9> Classes = {
        "Dragon", "GreatWyrm", "Thief", "Rogue", "Assassin", "Spy", "DeathKnight", "DeathLord", "LichKing",
    };
    const std::string className = canonicalClassName(member.className);
    return std::find(Classes.begin(), Classes.end(), className) != Classes.end();
}

// A flat aura's value from one source: (20 + level / 4) x (1 + 2 % x skill), the skill divided for Day of Protection
// (1.4) or Hour of Power (1.5).
double auraFlat(const MawRules &rules, const std::optional<MawAuraSource> &source, double skillDivisor = 1)
{
    return source ? mawAuraFlat(20, 2, source->level, source->skill / skillDivisor, rules.buffScale()) : 0.0;
}

// The flat auras (resistances, Stone Skin, Bless attack) reach the party as buffs at the party's strength; a member's
// stronger potion copy adds only the difference, so the two never add up.
void addPotionAuraFlats(const MawRules &rules, Character &member)
{
    constexpr uint32_t DayOfProtection = 85;
    constexpr uint32_t HourOfPower = 86;
    const double partyDayOfProtection = auraFlat(rules, rules.activeAura(DayOfProtection), 1.4);
    const double potionDayOfProtection = auraFlat(rules, MawRules::potionAura(DayOfProtection, member), 1.4);
    static constexpr std::array<std::pair<uint32_t, int CharacterResistanceSet::*>, 6> Resistances = {{
        {3, &CharacterResistanceSet::fire}, {14, &CharacterResistanceSet::air}, {25, &CharacterResistanceSet::water},
        {36, &CharacterResistanceSet::earth}, {58, &CharacterResistanceSet::mind}, {69, &CharacterResistanceSet::body},
    }};

    for (const auto &[spellId, field] : Resistances)
    {
        const double party = std::max(auraFlat(rules, rules.activeAura(spellId)), partyDayOfProtection);
        const double potion = std::max(auraFlat(rules, MawRules::potionAura(spellId, member)), potionDayOfProtection);
        member.magicalBonuses.resistances.*field += int(mawRound(std::max(potion - party, 0.0)));
    }

    const double partyStoneskin =
        std::max(auraFlat(rules, rules.activeAura(38)), auraFlat(rules, rules.activeAura(HourOfPower), 1.5));
    member.magicalBonuses.armorClass +=
        int(mawRound(std::max(auraFlat(rules, MawRules::potionAura(38, member)) - partyStoneskin, 0.0)));
    const int blessAttack =
        int(mawRound(std::max(auraFlat(rules, MawRules::potionAura(46, member)) - auraFlat(rules, rules.activeAura(46)), 0.0)));
    member.magicalBonuses.meleeAttack += blessAttack;
    member.magicalBonuses.rangedAttack += blessAttack;
}
}

MawSkillRules::MawSkillRules(MawRules &rules)
    : m_rules(rules)
{
}

bool mawIsHybridClass(const std::string &className)
{
    static const std::array<const char *, 13> HybridClasses = {
        "Seraphim", "Angel", "Archangel", "DeathKnight", "DeathLord", "LichKing", "Shaman", "Sekhem", "Marabou",
        "Thief", "Rogue", "Assassin", "Spy",
    };
    const std::string canonical = canonicalClassName(className);
    return std::find(HybridClasses.begin(), HybridClasses.end(), canonical) != HybridClasses.end();
}

MawSkillMode MawSkillRules::skillMode() const
{
    const RulesetOptions &options = m_rules.options();

    switch (options.challengeMode)
    {
        case RulesetChallengeMode::BeyondMadness:
            return MawSkillMode::BeyondMadness;
        case RulesetChallengeMode::RoadToInsanity:
            return MawSkillMode::RoadToInsanity;
        case RulesetChallengeMode::Doom:
            return MawSkillMode::Horizontal;
        default:
            return options.progression == RulesetProgression::Horizontal ? MawSkillMode::Horizontal
                                                                        : MawSkillMode::Normal;
    }
}

MawPriceMode MawSkillRules::priceMode() const
{
    switch (m_rules.options().challengeMode)
    {
        case RulesetChallengeMode::BeyondMadness:
            return MawPriceMode::BeyondMadness;
        case RulesetChallengeMode::RoadToInsanity:
            return MawPriceMode::RoadToInsanity;
        case RulesetChallengeMode::Doom:
            return MawPriceMode::Doom;
        default:
            return MawPriceMode::Normal;
    }
}

std::string MawSkillRules::skillDisplayName(const Character &character, const std::string &canonicalSkill) const
{
    const char *pSchool = mawClassSchoolName(character, canonicalSkill);
    return pSchool != nullptr ? pSchool : displaySkillName(canonicalSkill);
}

uint32_t MawSkillRules::skillRaiseCost(const Character &character, const std::string &canonicalSkill) const
{
    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);
    const uint32_t newLevel = pSkill != nullptr ? pSkill->level + 1 : 1;
    const bool hybrid = mawIsHybridClass(character.className);

    if (!mawIsSharedCostSkill(canonicalSkill, hybrid))
    {
        return newLevel;
    }

    uint32_t sharers = 0;

    for (const auto &[name, skill] : character.skills)
    {
        if (skill.name != canonicalSkill && mawIsSharedCostSkill(canonicalSkillName(skill.name), hybrid)
            && skill.level >= newLevel)
        {
            ++sharers;
        }
    }

    return mawSharedRaiseCost(newLevel, sharers);
}

std::vector<std::pair<std::string, std::array<uint32_t, 3>>> MawSkillRules::teacherlessMasteryLadders() const
{
    std::vector<std::pair<std::string, std::array<uint32_t, 3>>> ladders;

    for (const char *pSkill : {"Cover", "ManaShield", "Enlightenment", "Retaliation"})
    {
        if (const std::optional<std::array<uint32_t, 3>> ladder = mawSkillMasteryLadder(pSkill, skillMode()))
        {
            ladders.emplace_back(pSkill, *ladder);
        }
    }

    return ladders;
}

std::optional<bool> MawSkillRules::skillSwitch(const Character &character, const std::string &canonicalSkill) const
{
    if (!character.hasSkill(canonicalSkill))
    {
        return std::nullopt;
    }

    if (canonicalSkill == "Cover")
    {
        return !character.rulesetState.coverDisabled;
    }

    if (canonicalSkill == "ManaShield")
    {
        return !character.rulesetState.manaShieldDisabled;
    }

    return std::nullopt;
}

std::optional<bool> MawSkillRules::toggleSkillSwitch(Character &character, const std::string &canonicalSkill) const
{
    const std::optional<bool> on = skillSwitch(character, canonicalSkill);

    if (!on)
    {
        return std::nullopt;
    }

    bool &disabled = canonicalSkill == "Cover" ? character.rulesetState.coverDisabled
                                               : character.rulesetState.manaShieldDisabled;
    disabled = *on;
    return !disabled;
}

std::vector<std::string> MawSkillRules::extraHouseSkills(const std::string &houseType) const
{
    if (houseType == "Training")
    {
        return {"Cover"};
    }

    if (houseType == "Magic Shop")
    {
        return {"ManaShield", "Enlightenment"};
    }

    return {};
}

std::optional<uint32_t> MawSkillRules::skillLevelCap(const std::string &canonicalSkill) const
{
    // MAW raises the engine's base limit to 500 (MaxSkillBase 0x1F4); a few skills stop lower (S:162-167).
    constexpr uint32_t BaseSkillLimit = 500;
    return mawSkillLevelCap(canonicalSkill).value_or(BaseSkillLimit);
}

std::string MawSkillRules::restoreRememberedMastery(
    Character &character,
    CharacterSkill &skill,
    const ClassSkillTable *pClassSkillTable) const
{
    const std::string canonicalSkill = canonicalSkillName(skill.name);
    const auto remembered = character.rulesetState.rememberedMasteries.find(canonicalSkill);

    if (remembered == character.rulesetState.rememberedMasteries.end() || skill.mastery >= remembered->second
        || skill.mastery >= SkillMastery::Grandmaster)
    {
        return {};
    }

    const SkillMastery next = SkillMastery(int(skill.mastery) + 1);

    if (skill.level < masteryRequiredLevel(canonicalSkill, next)
        || (pClassSkillTable != nullptr
            && pClassSkillTable->getEffectiveCap(character.className, character.raceId, canonicalSkill) < next))
    {
        return {};
    }

    skill.mastery = next;

    if (next >= remembered->second)
    {
        character.rulesetState.rememberedMasteries.erase(remembered);
    }

    return Engine::tr("{mastery} {skill} regained", {{"mastery", Engine::tr(masteryDisplayName(next))},
        {"skill", Engine::localize(displaySkillName(canonicalSkill), "skill")}});
}

std::string MawSkillRules::afterSkillRaised(
    Character &character,
    const std::string &canonicalSkill,
    const ClassSkillTable *pClassSkillTable) const
{
    CharacterSkill *pSkill = character.findSkill(canonicalSkill);

    if (pSkill == nullptr)
    {
        return {};
    }

    const std::string restored = restoreRememberedMastery(character, *pSkill, pClassSkillTable);
    const std::string granted = grantLadderMastery(character, canonicalSkill, pClassSkillTable);
    return !granted.empty() ? granted : restored;
}

void MawSkillRules::afterClassChanged(Character &character, const ClassSkillTable *pClassSkillTable) const
{
    // Cover first: reaching its cap may teach Retaliation, which then starts at 1 like a raise would.
    for (const char *pSkill : {"Cover", "ManaShield", "Enlightenment", "Retaliation"})
    {
        grantLadderMastery(character, pSkill, pClassSkillTable);
    }
}

std::string MawSkillRules::grantLadderMastery(
    Character &character,
    const std::string &canonicalSkill,
    const ClassSkillTable *pClassSkillTable) const
{
    CharacterSkill *pSkill = character.findSkill(canonicalSkill);

    if (pSkill == nullptr)
    {
        return {};
    }

    std::string status;
    const auto classCap = [&](const std::string &skillName)
    {
        return pClassSkillTable != nullptr
            ? pClassSkillTable->getEffectiveCap(character.className, character.raceId, skillName)
            : SkillMastery::Grandmaster;
    };

    if (canonicalSkill == "Cover" && pSkill->level >= mawSkillLevelCap("Cover").value_or(0)
        && !character.hasSkill("Retaliation") && classCap("Retaliation") != SkillMastery::None)
    {
        character.skills["Retaliation"] = {"Retaliation", 1, SkillMastery::Normal};
        status = Engine::tr("{skill} learned", {{"skill", Engine::localize(displaySkillName("Retaliation"), "skill")}});
    }

    const std::optional<std::array<uint32_t, 3>> ladder = mawSkillMasteryLadder(canonicalSkill, skillMode());

    if (ladder)
    {
        const SkillMastery reached = SkillMastery(
            int(SkillMastery::Normal) + int(std::count_if(
                ladder->begin(), ladder->end(), [&](uint32_t level) { return pSkill->level >= level; })));
        const SkillMastery granted = std::min(reached, classCap(canonicalSkill));

        if (granted > pSkill->mastery)
        {
            pSkill->mastery = granted;
            status = Engine::tr("{mastery} {skill} learned", {{"mastery", Engine::tr(masteryDisplayName(granted))},
                {"skill", Engine::localize(displaySkillName(canonicalSkill), "skill")}});
        }
    }

    return status;
}

std::optional<int> MawSkillRules::skillResetCost(const Character &character) const
{
    return int(character.level) * 1000;
}

bool MawSkillRules::resetSkills(Character &character) const
{
    const bool hybrid = mawIsHybridClass(character.className);
    std::vector<uint32_t> sharedLevels;
    uint32_t refund = 0;
    uint32_t alchemyCost = 0;

    // Austerity's free Identify Monster refunds nothing and leaves every member until the next map load.
    if (m_rules.options().challengeMode == RulesetChallengeMode::Austerity)
    {
        character.skills.erase("IdentifyMonster");
        m_rules.setAusterityIdentifyRespecced(true);
    }

    for (auto &[name, skill] : character.skills)
    {
        const std::string canonical = canonicalSkillName(skill.name);

        if (skill.level == 0 || isTechnologySkill(canonical))
        {
            continue;
        }

        if (canonical == "Alchemy")
        {
            alchemyCost = skill.level * (skill.level + 1) / 2 - 1;
            continue;
        }

        // MAW remembers the masteries of skills 0-38 only, not its four new skills (R:127-137).
        if (skill.mastery > SkillMastery::Normal && !mawIsAddedSkill(canonical))
        {
            SkillMastery &remembered = character.rulesetState.rememberedMasteries[canonical];
            remembered = std::max(remembered, skill.mastery);
        }

        if (mawIsSharedCostSkill(canonical, hybrid))
        {
            sharedLevels.push_back(skill.level);
        }
        else
        {
            refund += skill.level * (skill.level + 1) / 2 - 1;
        }

        skill.level = 1;
        skill.mastery = SkillMastery::Normal;
    }

    refund += mawSharedSetRefund(sharedLevels);
    const uint32_t earned = mawLevelUpPoints(character.level);
    character.skillPoints = std::max(character.skillPoints + refund, earned > alchemyCost ? earned - alchemyCost : 0);
    return true;
}

void MawSkillRules::applyStatBonuses(Character &member) const
{
    addPotionAuraFlats(m_rules, member);
    const std::optional<double> dayOfTheGods = m_rules.auraSkill(83, &member);
    const double dayPercent = dayOfTheGods ? mawAuraStatPercent(*dayOfTheGods, true) : 0;
    // The aura that raises each stat: Body Resistance Might, Fire Intellect, Mind Personality, Earth Endurance, Bless
    // Accuracy, Air Speed, Water Luck.
    const std::array<std::pair<uint32_t Character::*, int CharacterStatBonuses::*>, 7> stats = {{
        {&Character::might, &CharacterStatBonuses::might},
        {&Character::intellect, &CharacterStatBonuses::intellect},
        {&Character::personality, &CharacterStatBonuses::personality},
        {&Character::endurance, &CharacterStatBonuses::endurance},
        {&Character::accuracy, &CharacterStatBonuses::accuracy},
        {&Character::speed, &CharacterStatBonuses::speed},
        {&Character::luck, &CharacterStatBonuses::luck},
    }};
    static constexpr std::array<uint32_t, 7> StatAuras = {69, 3, 58, 36, 46, 14, 25};

    for (size_t index = 0; index < stats.size(); ++index)
    {
        const std::optional<double> aura = m_rules.auraSkill(StatAuras[index], &member);
        const double percent = std::max(aura ? mawAuraStatPercent(*aura, false) : 0.0, dayPercent);

        if (percent > 0)
        {
            const int total = int(member.*stats[index].first) + member.magicalBonuses.*stats[index].second;
            member.magicalBonuses.*stats[index].second += int(mawRound(std::max(total, 0) * percent / 100));
        }
    }

    // With its bonuses a skill reaches at most 1023 (MaxSkillVal 0x3FF), a capped one twice its cap (S:198-212);
    // the item bonuses give way first, then the followers'.
    constexpr int EffectiveSkillLimit = 1023;

    for (const auto &[name, skill] : member.skills)
    {
        const std::string canonical = canonicalSkillName(skill.name);
        const std::optional<uint32_t> cap = mawSkillLevelCap(canonical);
        const int limit = cap ? int(*cap) * 2 : EffectiveSkillLimit;
        int excess = int(skill.level) + member.skillBonus(canonical) - limit;

        for (auto &[bonusName, amount] : member.itemSkillBonuses)
        {
            if (excess > 0 && amount > 0 && canonicalSkillName(bonusName) == canonical)
            {
                const int cut = std::min(excess, amount);
                amount -= cut;
                excess -= cut;
            }
        }

        if (const auto follower = member.hiredNpcSkillBonuses.find(canonical);
            excess > 0 && follower != member.hiredNpcSkillBonuses.end())
        {
            follower->second = std::max(0, follower->second - excess);
        }
    }
}

void MawSkillRules::applyResourceBonuses(Character &member) const
{
    static constexpr std::array<double, 5> BodybuildingPercent = {0, 0.5, 1, 1.5, 2};
    static constexpr std::array<double, 5> EnlightenmentPercent = {0, 0.5, 1, 1.5, 2};
    const auto skill = [&member](const char *pName)
    {
        const CharacterSkill *pSkill = member.findSkill(pName);
        return std::pair<double, int>(
            (pSkill != nullptr ? double(pSkill->level) : 0.0) + member.skillBonus(pName),
            pSkill != nullptr ? std::min(int(pSkill->mastery), 4) : 0);
    };

    const int endurance = int(member.endurance) + member.magicalBonuses.endurance;
    const double fullHealth = member.maxHealth + member.permanentBonuses.maxHealth + member.magicalBonuses.maxHealth;
    const double enduranceBonus = fullHealth * std::max(endurance, 0) / 1000.0;
    const auto [bodybuilding, bodybuildingMastery] = skill("Bodybuilding");
    const double bodybuildingBonus =
        (fullHealth + enduranceBonus) * BodybuildingPercent[size_t(bodybuildingMastery)] * 0.01 * bodybuilding;
    member.magicalBonuses.maxHealth += int(enduranceBonus + bodybuildingBonus);

    // Enlightenment's base also counts Meditation, which adds no SP of its own (IT:3131-3146).
    const auto [enlightenment, enlightenmentMastery] = skill("Enlightenment");
    const double fullMana = member.maxSpellPoints + member.permanentBonuses.maxSpellPoints
        + member.magicalBonuses.maxSpellPoints + m_rules.classRules().enlightenmentMeditationMana(member);
    member.magicalBonuses.maxSpellPoints +=
        int(fullMana * EnlightenmentPercent[size_t(enlightenmentMastery)] * 0.01 * enlightenment);
}

std::optional<CharacterCombatRows> MawSkillRules::combatRows(
    const Character &character,
    const ItemTable *pItemTable,
    const CharacterStatValues &stats) const
{
    if (pItemTable == nullptr)
    {
        return std::nullopt;
    }

    return mawCombatRows(m_rules, character, *pItemTable, stats);
}

float MawSkillRules::regenerationHealthPerSecond(const Character &) const
{
    return 0.0f;
}

int MawSkillRules::meditationSpellPointsPerTick(const Character &) const
{
    return 0;
}

SkillTooltipText MawSkillRules::skillTooltip(
    const Party &party,
    const Character &character,
    const std::string &canonicalSkill,
    const SkillTooltipText &table) const
{
    const std::string line = mawClassLine(character.className);
    const std::optional<MawSkillTextEntry> entry = m_rules.textData().findSkill(line, canonicalSkill);

    const auto footer = [&]()
    {
        const std::string preview = raisePreviewText(party, character, canonicalSkill);
        const std::string hint = mawTrainerHintText(m_rules, party, character, canonicalSkill, skillMode());
        return preview + (!preview.empty() && !hint.empty() ? "\n\n" : "") + hint;
    };

    if (!entry)
    {
        SkillTooltipText text = table;
        text.footer = footer();
        return text;
    }

    const auto skillOf = [&character](const char *pSkill)
    {
        const CharacterSkill *pFound = character.findSkill(pSkill);
        return std::pair<double, SkillMastery>((pFound != nullptr ? double(pFound->level) : 0.0)
                + character.skillBonus(pSkill),
            pFound != nullptr ? pFound->mastery : SkillMastery::None);
    };
    const auto [level, mastery] = skillOf(canonicalSkill.c_str());
    MawBalanceModel &model = m_rules.model(int(std::max<size_t>(1, party.members().size())));
    std::unordered_map<std::string, double> values;
    values["level"] = level;

    // Regeneration and Meditation now and with one more point, before the out-of-combat multipliers. An unlearned
    // skill's next point is learning it at Normal.
    const SkillMastery nextMastery = std::max(mastery, SkillMastery::Normal);
    const double fullHealth = Party::effectiveMaximumHealth(character);
    const auto regeneration = [&](double skill, SkillMastery skillMastery)
    {
        return mawRegenerationHealthPerSecond(skillMastery, model.health(std::pow(skill, 1.4)), fullHealth,
            fullHealth);
    };
    // Meditation fills the pool the auras leave, and Legendary 20 adds 1 % for each 1 % they reserve, as the
    // regeneration does (TXT-2-6).
    const int fullSpellPoints = Party::effectiveMaximumSpellPoints(character);
    int reserved = 0;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        if (&party.members()[memberIndex] == &character)
        {
            reserved = m_rules.gameRules().spells.reservedSpellPoints(party, memberIndex);
        }
    }

    const double legendaryMeditation = fullSpellPoints > 0 && mawWearsLegendaryAffix(character, 20)
        ? 1 + std::clamp(double(reserved) / fullSpellPoints, 0.0, 1.0)
        : 1.0;
    const auto meditation = [&](double skill, SkillMastery skillMastery)
    {
        return mawMeditationSpellPerSecond(skillMastery, model.mana(std::pow(skill, 1.4) / 2),
                   mawMeditationPool(fullSpellPoints, reserved))
            * legendaryMeditation;
    };
    values["regen_now"] = regeneration(level, mastery);
    values["regen_next"] = regeneration(level + 1, nextMastery);
    values["med_now"] = meditation(level, mastery);
    values["med_next"] = meditation(level + 1, nextMastery);

    // Ascension's percents, each from the ascension its own use reads: a Shaman heals and pays by seven schools, an
    // Elementalist by the four elements at Grandmaster, Death Knights and Assassins have none (TXT-2-5).
    const double ascension = mawAscension(character, MawAscensionUse::Damage).skill;
    const double healAscension = mawAscension(character, MawAscensionUse::Heal).skill;
    const MawAscension costAscension = mawAscension(character, MawAscensionUse::Cost);
    const double castAscension = mawAscension(character, MawAscensionUse::CastTime).skill;
    // MAW's tooltip shows the Ascension growth alone, without the cut of every damage spell.
    values["asc_damage_scaling"] = std::round(100 * (mawSpellDiceScale(ascension) - 1));
    values["asc_damage_base"] = std::round(100 * (mawSpellAddScale(ascension) - 1));
    values["asc_heal_scaling"] = 100 * ((1 + 0.02 * healAscension) * std::pow(1.015, healAscension) - 1);
    values["asc_heal_base"] =
        100 * ((1 + 0.01 * healAscension * healAscension) * std::pow(1.015, healAscension) - 1);
    values["asc_mana"] =
        mawSpellManaCost(MawSpellCategory::Damage, 1000, costAscension.skill, costAscension.mastery, 1) / 10.0 - 100;
    values["asc_cc_mana"] =
        mawSpellManaCost(MawSpellCategory::CrowdControl, 1000, costAscension.skill, costAscension.mastery, 1) / 10.0
        - 100;
    values["asc_cast"] = 100 * (std::pow(1.015, castAscension) - 1);

    values["cover_chance"] = 100 * mawCoverChance(level, false);
    values["spear_stack"] = party.itemTable() != nullptr
        ? std::round(mawSpearStackPercent(m_rules, character, *party.itemTable()) * 10) / 10
        : 2 + 0.02 * level;
    values["mana_efficiency"] = mawManaShieldEfficiency(level);

    if (const std::optional<std::array<uint32_t, 3>> ladder = mawSkillMasteryLadder(canonicalSkill, skillMode()))
    {
        values["ladder_expert"] = (*ladder)[0];
        values["ladder_master"] = (*ladder)[1];
        values["ladder_grandmaster"] = (*ladder)[2];
    }

    // The class schools: a cut of 1 - 1 / (1 + s / 100), the Shaman's Fire share and Spirit percent, the Seraph's
    // Mind damage s (m + 1) / 2, an Elementalist's progress.
    values["school_cut"] = 100 * (1 - 1 / (1 + level / 100));
    values["school_share"] = level / 10;
    values["school_percent"] = level;
    values["school_damage"] = std::round(level * (int(mastery) + 1) / 2);
    // The class schools' live numbers: the Shaman's Water and the Seraph's Spirit flat cut, the Shaman's Mind and Body
    // returns, the Seraph's Body heal (SkillTooltip.lua:351-424, TXT-2-11).
    values["school_flat_cut"] =
        mawClassDefense(m_rules, character, int(std::max<size_t>(1, party.members().size()))).flatReduction;
    values["mind_sp"] = mawShamanMindSpellPoints(character);
    values["body_hp"] = mawShamanBodyHeal(character);
    values["seraph_heal"] = mawSeraphBodyHeal(m_rules, character, party);
    // Dragons' Fangs and Scales grow with the level up to 600, 900 in Beyond Madness.
    values["dragon_level_cap"] =
        m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness ? 900 : 600;
    // An Elementalist's casting progress in the school, named by the spell it reaches next (SkillTooltip.lua).
    static constexpr std::array<const char *, 4> ElementSchools = {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic"};
    std::string elementalProgress;

    for (size_t school = 0; school < ElementSchools.size(); ++school)
    {
        if (canonicalSkill != ElementSchools[school])
        {
            continue;
        }

        const double progress = character.rulesetState.elementalProgress[school];
        const std::optional<uint32_t> nextSpell = mawElementalistNextSpell(school, progress);
        const SpellEntry *pNext = nextSpell && m_rules.spellTable() != nullptr
            ? m_rules.spellTable()->findById(int(*nextSpell))
            : nullptr;

        if (pNext == nullptr)
        {
            elementalProgress =
                Engine::tr("Casting has taught every spell of this school; each still needs its mastery.");
            break;
        }

        std::ostringstream percent;
        percent << mawRound(mawElementalistNextSpellPercent(progress) * 10) / 10;
        elementalProgress = Engine::tr("Progress toward learning {spell}: <good>{percent} %</>",
            {{"spell", Engine::localize(m_rules.gameRules().spells.spellName(character, *pNext), "spell")},
                {"percent", percent.str()}});
    }

    // A Mace's or Staff's paralyse chance at the party's level, Retaliation's coefficients, Supreme's level
    // (SkillTooltip.lua:236-310).
    const int reference = std::max(1, int(mawRound(m_rules.state().totalLevel())));
    const int partyCount = int(std::max<size_t>(1, party.members().size()));
    std::string stunLine;
    values["retaliation_power"] = 0;
    values["retaliation_vitality"] = 0;
    values["retaliation_damage"] = 0;

    if (party.itemTable() != nullptr)
    {
        const double speed = mawCharacterAttackDelay(m_rules, character, *party.itemTable(), CharacterAttackMode::Melee,
            0).damageMultiplier;
        const double chance =
            mawWeaponStunChance(m_rules, character, *party.itemTable(), reference, partyCount, speed);
        // The chance is the weapon in hand's: only its own popup shows it (TXT-2-7).
        const ItemDefinition *pHeld = character.equipment.mainHand != 0
            ? party.itemTable()->get(character.equipment.mainHand)
            : nullptr;

        if (chance > 0 && pHeld != nullptr && canonicalSkillName(pHeld->skillGroup) == canonicalSkill)
        {
            std::ostringstream percent;
            percent << mawRound(chance * 10000) / 100;
            stunLine = Engine::tr("Chance to paralyse vs level {level}: {percent} %",
                {{"level", reference}, {"percent", percent.str()}});
        }

        const auto [power, vitality] = mawRetaliationCoefficients(m_rules, character, *party.itemTable(),
            party.standardItemEnchantTable(), party.specialItemEnchantTable(), partyCount);
        values["retaliation_power"] = power;
        values["retaliation_vitality"] = vitality;
        values["retaliation_damage"] = level * power * vitality;
    }

    // A dragon's Regeneration also leeches its bites: against a monster of its own level, and with one more point
    // (SkillTooltip.lua:148-154). Shown before the skill is learned too, so a new dragon sees what it would get.
    std::string dragonLeech;

    if (canonicalSkill == "Regeneration" && mawIsDragon(character))
    {
        const double perPoint = 5.0 / std::max(1.0, model.skill(std::max(1u, character.level)));
        std::ostringstream now;
        std::ostringstream next;
        now << mawRound(level * perPoint * 10) / 10;
        next << mawRound((level + 1) * perPoint * 10) / 10;
        dragonLeech = "\n\n"
            + Engine::tr("Melee life leech vs equal level: <bad>{now} %</> (<bad>{next} %</> with one more point), "
                         "lower against stronger monsters.",
                {{"now", now.str()}, {"next", next.str()}});
    }

    // The armour skills' popups: what the worn armour gives now (SkillTooltip.lua:208-224).
    std::string armorItems;
    const bool bodyArmorSkill =
        canonicalSkill == "LeatherArmor" || canonicalSkill == "ChainArmor" || canonicalSkill == "PlateArmor";

    if ((bodyArmorSkill || canonicalSkill == "Shield") && party.itemTable() != nullptr)
    {
        const MawArmorBreakdown armor = mawArmorBreakdown(m_rules, character, *party.itemTable());
        const auto number = [](auto value)
        {
            std::ostringstream text;
            text << value;
            return text.str();
        };

        if (bodyArmorSkill && armor.bodySkill == canonicalSkill)
        {
            armorItems = "\n\n"
                + Engine::tr("Current Armor Class from items: <value>{items}</>\nBonus Armor Class: <value>{armor}</>\n"
                             "Bonus resistances: <value>{resistances}</>",
                    {{"items", number(mawRound(armor.pieces))}, {"armor", number(armor.bodySkillArmor)},
                        {"resistances", number(armor.bodySkillResistance)}});
        }
        else if (canonicalSkill == "Shield" && armor.shield > 0)
        {
            armorItems = "\n\n"
                + Engine::tr("Bonus Armor Class: <value>{armor}</>\nBonus resistances: <value>{resistances}</>",
                    {{"armor", number(armor.shieldSkillArmor)}, {"resistances", number(armor.shieldSkillResistance)}});
        }
    }

    // Staff, Sword and Spear: what the weapons of the skill in hand give now, as the character sheet counts them.
    std::string guardLine;

    if ((canonicalSkill == "Staff" || canonicalSkill == "Sword" || canonicalSkill == "Spear")
        && party.itemTable() != nullptr)
    {
        int armorClass = 0;
        int resistance = 0;
        bool held = false;

        for (const auto &[itemId, pState] :
            {std::pair(character.equipment.mainHand, &character.equipmentRuntime.mainHand),
                std::pair(character.equipment.offHand, &character.equipmentRuntime.offHand)})
        {
            const ItemDefinition *pItem = itemId != 0 && !pState->broken ? party.itemTable()->get(itemId) : nullptr;
            const std::optional<MawWeaponGuard> guard = pItem != nullptr
                    && canonicalSkillName(pItem->skillGroup) == canonicalSkill
                ? mawWeaponGuard(m_rules, character, *pItem, pState->rulesetFields)
                : std::nullopt;

            if (guard)
            {
                held = true;
                armorClass += guard->armorClass;
                resistance += guard->resistance;
            }
        }

        if (held)
        {
            guardLine = "\n\n"
                + (canonicalSkill == "Staff"
                        ? Engine::tr("Armor Class from this skill now: <value>+{armor}</>\n"
                                     "Resistances it gives the party: <value>+{resistance}</>",
                              {{"armor", armorClass}, {"resistance", resistance}})
                        : Engine::tr("Armor Class from this skill now: <value>+{armor}</>", {{"armor", armorClass}}));
        }
    }

    const RulesetChallengeMode mode = m_rules.options().challengeMode;
    values["supreme_level"] = mode == RulesetChallengeMode::BeyondMadness ? 70
        : mode == RulesetChallengeMode::RoadToInsanity                    ? 50
                                                                           : 30;
    const auto state = [](bool off)
    {
        return Engine::tr(off ? "<bad>Currently disabled</>" : "<good>Currently enabled</>");
    };
    // A mana cost change, green when the mastery brings it below the base cost (SkillTooltip.lua manaStr).
    const auto costChange = [&values](const char *pName)
    {
        const double percent = std::round(values[pName]);
        std::ostringstream text;
        text << (percent < 0 ? "<good>" : "<bad>+") << percent << "</> %";
        return text.str();
    };
    const std::unordered_map<std::string, std::string> words = {
        {"rotation",
            Engine::tr(character.rulesetState.elementalRotationDisabled ? "<bad>disabled</>" : "<good>enabled</>")},
        {"asc_mana_change", costChange("asc_mana")},
        {"asc_cc_mana_change", costChange("asc_cc_mana")},
        {"stun_line", stunLine},
        {"dragon_leech", dragonLeech},
        {"elemental_progress_line", elementalProgress},
        {"armor_items", armorItems},
        {"guard_line", guardLine},
        {"cover_state", state(character.rulesetState.coverDisabled)},
        {"mana_shield_state", state(character.rulesetState.manaShieldDisabled)},
    };

    SkillTooltipText text = table;

    if (entry->description)
    {
        text.description = mawFillText(*entry->description, values, words);
    }

    if (entry->append)
    {
        text.description += (text.description.empty() ? "" : "\n\n") + mawFillText(*entry->append, values, words);
    }

    for (size_t index = 0; index < text.masteryLines.size(); ++index)
    {
        if (entry->masteryLines[index])
        {
            text.masteryLines[index] =
                mawFillText(*entry->masteryLines[index], values, {{"table", table.masteryLines[index]}});
        }
    }

    text.footer = footer();
    return text;
}

std::string MawSkillRules::raisePreviewText(
    const Party &party, const Character &character, const std::string &canonicalSkill) const
{
    std::optional<size_t> memberIndex;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        if (&party.members()[index] == &character)
        {
            memberIndex = index;
        }
    }

    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);

    if (!memberIndex || pSkill == nullptr || party.itemTable() == nullptr || !canRaiseSkill(character, canonicalSkill))
    {
        return {};
    }

    if (m_lastRaisePreview && m_lastRaisePreview->memberIndex == *memberIndex
        && m_lastRaisePreview->skill == canonicalSkill && m_lastRaisePreview->level == pSkill->level
        && m_lastRaisePreview->skillPoints == character.skillPoints
        && m_lastRaisePreview->spell == mawPowerSpellName(character)
        && m_lastRaisePreview->equipment == character.equipment
        && m_lastRaisePreview->equipmentRuntime == character.equipmentRuntime)
    {
        return m_lastRaisePreview->text;
    }

    m_lastRaisePreview = RaisePreview{*memberIndex, canonicalSkill, pSkill->level, character.skillPoints,
        mawPowerSpellName(character), character.equipment, character.equipmentRuntime, {}};

    // The party as it is and with the point bought as the skills page buys it (the masteries it grants included):
    // two copies, rebuilt alike (MawItemRules::comparisonLines).
    Party baseline = party;
    Party trial = party;

    if (!trial.setActiveMemberIndex(*memberIndex) || !trial.increaseActiveMemberSkillLevel(canonicalSkill))
    {
        return {};
    }

    baseline.refreshDerivedState();
    baseline.refreshMemberResources(*memberIndex);
    trial.refreshMemberResources(*memberIndex);
    const int partyCount = int(party.members().size());

    // A school's point is measured on the member's own spell when it is of the school, else on the school's strongest
    // known damage spell, named in the line (with no spell of its own a caster's Spell Power reads "-").
    const SpellEntry *pOwnSpell = m_rules.spellTable() != nullptr && !mawPowerSpellName(character).empty()
        ? m_rules.spellTable()->findByName(mawPowerSpellName(character))
        : nullptr;
    const bool ownSpellOfSchool =
        pOwnSpell != nullptr && resolveMagicSkillName(uint32_t(pOwnSpell->id)) == canonicalSkill;
    const std::optional<std::string> assumedSpell =
        ownSpellOfSchool ? std::nullopt : mawStrongestSchoolSpell(m_rules, character, canonicalSkill);
    const auto report = [&](const Party &source)
    {
        return mawPowerReport(m_rules, *source.member(*memberIndex), *source.itemTable(),
            source.standardItemEnchantTable(), source.specialItemEnchantTable(), partyCount,
            assumedSpell ? &*assumedSpell : nullptr);
    };
    const MawPowerReport before = report(baseline);
    const MawPowerReport after = report(trial);
    std::string lines;
    const auto addLine = [&lines](const std::string &name, double before, double after)
    {
        const double change = before > 0 ? mawRound((after / before - 1) * 10000) / 100 : 0;

        if (change == 0)
        {
            return;
        }

        std::ostringstream text;
        text << (change > 0 ? "<good>+" : "<bad>") << change << "%</>";
        lines += "\n" + Engine::tr("{name}: {change}", {{"name", name}, {"change", text.str()}});
    };
    addLine(Engine::tr("Melee Power"), before.melee, after.melee);
    addLine(Engine::tr("Ranged Power"), before.ranged, after.ranged);
    addLine(assumedSpell
            ? Engine::tr("Spell Power ({spell})", {{"spell", Engine::localize(*assumedSpell, "spell")}})
            : Engine::tr("Spell Power"),
        before.spell, after.spell);
    addLine(Engine::tr("Vitality"), before.vitality, after.vitality);

    if (!lines.empty())
    {
        // The colour tags become the game's colour codes, as in the popup's other texts.
        m_lastRaisePreview->text = mawFillText(Engine::tr("With one more point:") + lines, {}, {});
    }

    return m_lastRaisePreview->text;
}

std::string MawSkillRules::statTooltip(
    const Party &party,
    const Character &character,
    const std::string &statName,
    const std::string &table) const
{
    // The rows statRowText relabels or adds (Melee, Ranged and Spell Power, Vitality) explain their own numbers; MAW
    // leaves Condition's and Quick Spell's popups on them (zzMaw-Stats.lua:269-291, 425-456, 1189-1340).
    if ((statName == "Condition" || statName == "QuickSpell" || statName == "SpellPower" || statName == "Vitality")
        && party.itemTable() != nullptr)
    {
        const MawPowerReport report = mawPowerReport(m_rules, character, *party.itemTable(),
            party.standardItemEnchantTable(), party.specialItemEnchantTable(),
            int(std::max<size_t>(1, party.members().size())));
        const int level = std::max(1, int(mawRound(m_rules.state().totalLevel())));
        const MawLeech leech = mawLeech(m_rules, character, party.itemTable());
        // A negative leech (Hades) drains: red, not green.
        // {share} is left to mawFillText, which writes the number as MAW does.
        const auto leechLine = [](std::string_view name, double share)
        {
            return mawFillText(Engine::tr(share < 0 ? "{name}: <bad>{share}%</>" : "{name}: <good>{share}%</>",
                                   {{"name", Engine::tr(name)}}),
                {{"share", 100 * share}});
        };
        const std::string leechNotes = Engine::tr(
            "Leech counts health bars, not damage: take away 50% of a monster's health with 10% leech, and you heal 5% "
            "of your own. Every monster is measured with the bar of the middle variant of its family: weak variants "
            "leech for less, strong ones and bosses for more.");

        if (statName == "Condition")
        {
            std::string text = mawFillText(
                Engine::tr("Damage per second of weapon blows against monsters of level {level}: the average blow with "
                           "its critical hits, enchantments and Fire Aura, over the recovery between blows, times the "
                           "chance to hit.\n\nMelee Power: <bad>{melee}</>"),
                {{"level", level}, {"melee", report.melee}});

            if (leech.melee != 0)
            {
                text += "\n\n" + leechLine(Engine::trNoop("Physical Leech"), leech.melee) + "\n" + leechNotes;
            }

            return text;
        }

        if (statName == "SpellPower")
        {
            if (report.spell <= 0)
            {
                return Engine::tr("Damage per second of the attack or quick spell, with its critical hits, over its "
                                  "recovery. This character's attack and quick spell deal no damage.");
            }

            std::string text = mawFillText(
                Engine::tr("Damage per second of the attack or quick spell against monsters of level {level}, with its "
                           "critical hits, over its recovery.\n\nSpell Power: <mana>{spell}</>"),
                {{"level", level}, {"spell", report.spell}});

            if (leech.spell != 0)
            {
                text += "\n\n" + leechLine(Engine::trNoop("Magical Leech"), leech.spell) + "\n"
                    + Engine::tr("Magical Leech also includes damage done with weapon enchantments.") + "\n"
                    + leechNotes;
            }

            return text;
        }

        if (statName == "QuickSpell")
        {
            std::string text = mawFillText(
                Engine::tr("Damage per second of bow or blaster shots against monsters of level {level}: the average "
                           "shot with its critical hits and enchantments, over the recovery between shots, times the "
                           "chance to hit.\n\nRanged Power: <value>{ranged}</>"),
                {{"level", level}, {"ranged", report.ranged}});

            if (leech.ranged != 0)
            {
                text += "\n\n" + leechLine(Engine::trNoop("Physical Leech"), leech.ranged) + "\n"
                    + Engine::tr("Leech done with bow is halved.") + "\n" + leechNotes;
            }

            return text;
        }

        std::string text = mawFillText(
            Engine::tr("How much damage it takes to fell this character, against monsters of level {level}: maximum "
                       "Hit Points (with Mana Shield's mana and Grandmaster Dodging) over the share of an average hit "
                       "that gets through armour and resistances.\n\nVitality: <good>{vitality}</>"),
            {{"level", level}, {"vitality", report.vitality}});
        // MAW's popup of the Quick Spell row lists the legendary effects the character wears.
        text += "\n\n" + Engine::tr("Currently Active Legendary effects:");
        bool anyLegendary = false;

        for (int affix = MawFirstLegendaryAffix; affix < MawFirstLegendaryAffix + MawLegendaryAffixCount; ++affix)
        {
            const std::string &effect = m_rules.itemData().legendaryAffixText(affix);

            if (!effect.empty() && mawWearsLegendaryAffix(character, affix))
            {
                // Added after the description was filled, so the colour tags are converted here.
                text += mawFillText("\n - <value>" + Engine::localize(effect) + "</>", {});
                anyLegendary = true;
            }
        }

        return anyLegendary ? text : text + " " + Engine::tr("none");
    }

    const MawSkillTextEntry *pEntry = m_rules.textData().findStat(statName);
    const auto member = std::find_if(party.members().begin(), party.members().end(),
        [&character](const Character &candidate) { return &candidate == &character; });

    if (pEntry == nullptr || member == party.members().end())
    {
        return table;
    }

    const size_t index = size_t(member - party.members().begin());
    const CharacterSheetSummary sheet = GameMechanics::buildCharacterSheetSummary(character, party.itemTable(),
        party.standardItemEnchantTable(), party.specialItemEnchantTable());
    const int reference = std::max(1, int(mawRound(m_rules.state().totalLevel())));
    MawBalanceModel &model = m_rules.model(int(std::max<size_t>(1, party.members().size())));
    const double might = sheet.might.actual;
    const double intellect = sheet.intellect.actual;
    const double personality = sheet.personality.actual;
    const double speed = sheet.speed.actual;
    std::unordered_map<std::string, double> values;
    values["reference_level"] = reference;
    values["might_bonus"] = might / 10;
    values["spell_bonus"] = std::max(intellect, personality) / 10;
    values["heal_bonus"] = 100 * personality / std::min(1000.0 + 3 * character.level, 4000.0);
    values["cost_cut"] = 100 * (1 - mawPersonalityCostFactor(personality, m_rules.state().totalLevel()));
    values["endurance_bonus"] = sheet.endurance.actual / 10;
    values["endurance_levels"] = mawStatEffect(sheet.endurance.actual);
    // Personality counts twice in every caster's pool (MawClassRules::baseMaxSpellPoints, CLS-1).
    values["personality_levels"] = 2 * mawStatEffect(int(personality));

    MawCritInputs crit;
    crit.luck = sheet.luck.actual;
    crit.accuracy = sheet.accuracy.actual;
    crit.intellect = intellect;
    crit.referenceLevel = reference;
    crit.fateSkill = m_rules.auraSkill(47);
    crit.buffScale = m_rules.buffScale();
    crit.madness = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    const MawCrit weaponCrit = mawCrit(crit);
    crit.kind = MawCritKind::Spell;
    const MawCrit spellCrit = mawCrit(crit);
    values["crit_chance"] = 100 * weaponCrit.chance;
    values["crit_damage"] = 100 * (weaponCrit.multiplier - 1);
    values["spell_crit_damage"] = 100 * (spellCrit.multiplier - 1);

    values["attack_haste"] = mawSpeedRecoveryBonus(speed);
    values["spell_haste"] = std::floor(speed / 20);
    values["avoid_chance"] = 100 * (1 - mawChanceToBeHit(speed, reference, model));
    // Grandmaster Dodging's own dodge, which MAW lists under Speed (zzMaw-Stats.lua:341-347, TXT-2-11).
    const CharacterSkill *pDodging = character.findSkill("Dodging");
    values["dodge_chance"] = pDodging == nullptr || mawIsDragon(character)
        ? 0
        : 100 * mawGrandmasterDodgeChance(pDodging->level + character.skillBonus("Dodging"),
            pDodging->mastery >= SkillMastery::Grandmaster);

    if (party.itemTable() != nullptr)
    {
        const CharacterCombatRows rows = mawCombatRows(m_rules, character, *party.itemTable(),
            {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual});
        values["hit_chance"] =
            100 * mawPartyHitChance(rows.meleeAttack, reference, m_rules.blessHitSkill(character), model);
    }

    const double physicalTaken = mawDamageTakenPercent(m_rules, character, party.itemTable(),
        party.standardItemEnchantTable(), party.specialItemEnchantTable(), CombatDamageType::Physical, reference);
    values["physical_cut"] = 100 - physicalTaken;
    values["total_cut"] = 100 - physicalTaken * mawChanceToBeHit(speed, reference, model);

    const auto [healthPerSecond, spellPerSecond] = regenerationPerSecond(party, index);
    values["hp_regen"] = healthPerSecond;
    values["sp_regen"] = spellPerSecond;

    for (const auto &[key, type] : std::array<std::pair<const char *, CombatDamageType>, 6>{{
             {"fire_cut", CombatDamageType::Fire}, {"air_cut", CombatDamageType::Air},
             {"water_cut", CombatDamageType::Water}, {"earth_cut", CombatDamageType::Earth},
             {"mind_cut", CombatDamageType::Mind}, {"body_cut", CombatDamageType::Body}}})
    {
        values[key] = 100 - mawDamageTakenPercent(m_rules, character, party.itemTable(),
            party.standardItemEnchantTable(), party.specialItemEnchantTable(), type, reference);
    }

    const MawGameState &state = m_rules.state();
    values["levels_mm8"] = state.continentLevels[0];
    values["levels_mm7"] = state.continentLevels[1];
    values["levels_mm6"] = state.continentLevels[2];
    values["levels_mm9"] = state.continentLevels[3];
    values["levels_total"] = state.totalLevel();
    // Each world's bolster level, as MAW's popup shows it: the levels banked in the other worlds, less 4
    // (zzMaw-Stats.lua:458-466, TXT-2-9).
    values["bolster_mm8"] = std::max(state.levelOutside(1) - 4, 0.0);
    values["bolster_mm7"] = std::max(state.levelOutside(2) - 4, 0.0);
    values["bolster_mm6"] = std::max(state.levelOutside(3) - 4, 0.0);
    values["bolster_mm9"] = std::max(state.levelOutside(5) - 4, 0.0);

    std::string text = pEntry->description ? mawFillText(*pEntry->description, values) : table;

    if (pEntry->append)
    {
        text += (text.empty() ? "" : "\n\n") + mawFillText(*pEntry->append, values);
    }

    return text;
}

float MawSkillRules::trainingPriceMultiplier(const Character &trainee, float houseMultiplier) const
{
    if (!mawModelConfig(m_rules.options(), 5).insanityMode)
    {
        return houseMultiplier;
    }

    return float(m_rules.model(1).skill(double(trainee.level)) + 4);
}

std::optional<SkillRaiseCost> MawSkillRules::skillRaiseCostDetail(
    const Character &character,
    const std::string &canonicalSkill) const
{
    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);
    const std::optional<uint32_t> cap = skillLevelCap(canonicalSkill);

    if (pSkill == nullptr || (cap && pSkill->level >= *cap))
    {
        return std::nullopt;
    }

    SkillRaiseCost detail;
    detail.cost = skillRaiseCost(character, canonicalSkill);
    detail.fullCost = pSkill->level + 1;
    const bool hybrid = mawIsHybridClass(character.className);

    // The same sharers skillRaiseCost counts, while they lower the cost.
    if (detail.cost < detail.fullCost)
    {
        for (const auto &[name, skill] : character.skills)
        {
            const std::string other = canonicalSkillName(skill.name);

            if (other != canonicalSkill && mawIsSharedCostSkill(other, hybrid) && skill.level >= detail.fullCost)
            {
                detail.sharedWith.push_back(skillDisplayName(character, other));
            }
        }
    }

    return detail;
}

std::string MawSkillRules::teacherSpeech(
    const std::string &text,
    const std::string &canonicalSkill,
    SkillMastery mastery,
    uint32_t requiredLevel,
    int price) const
{
    // MAW rewrites the speeches of its horizontal skills only (S:1886-1889).
    if (!mawIsHorizontalSkill(canonicalSkill) || mawIsAddedSkill(canonicalSkill))
    {
        return text;
    }

    const int vanillaRequirement = mastery == SkillMastery::Expert ? 4 : mastery == SkillMastery::Master ? 7 : 10;
    struct Number
    {
        size_t start = 0;
        size_t length = 0;
        int value = 0;
    };
    std::vector<Number> numbers;

    for (size_t position = 0; position < text.size();)
    {
        if (!std::isdigit(static_cast<unsigned char>(text[position])))
        {
            ++position;
            continue;
        }

        Number number;
        number.start = position;

        // "5,000" counts as one number.
        while (position < text.size()
            && (std::isdigit(static_cast<unsigned char>(text[position]))
                || (text[position] == ',' && position + 1 < text.size()
                    && std::isdigit(static_cast<unsigned char>(text[position + 1])))))
        {
            if (text[position] != ',')
            {
                number.value = std::min(number.value * 10 + (text[position] - '0'), 100000000);
            }

            ++position;
        }

        number.length = position - number.start;
        numbers.push_back(number);
    }

    std::optional<size_t> requirement;

    for (size_t index = 0; index < numbers.size() && !requirement; ++index)
    {
        if (numbers[index].value == vanillaRequirement)
        {
            requirement = index;
        }
    }

    for (size_t index = 0; index < numbers.size() && !requirement; ++index)
    {
        if (numbers[index].value <= 12)
        {
            requirement = index;
        }
    }

    std::string result;
    size_t copied = 0;
    bool hasPrice = false;

    for (size_t index = 0; index < numbers.size(); ++index)
    {
        const Number &number = numbers[index];
        const bool isPrice = number.value >= 100;

        if (!isPrice && requirement != index)
        {
            continue;
        }

        result += text.substr(copied, number.start - copied);
        result += isPrice ? std::to_string(price) : std::to_string(requiredLevel);
        copied = number.start + number.length;
        hasPrice = hasPrice || isPrice;
    }

    result += text.substr(copied);

    if (!hasPrice || !requirement)
    {
        result += "\n\n"
            + Engine::tr("You need at least {level} skill and {price} gold.",
                {{"level", requiredLevel}, {"price", price}});
    }

    return result;
}

IdentifyMonsterReveal MawSkillRules::identifyMonsterReveal(const Party &party, int monsterLevel) const
{
    IdentifyMonsterReveal reveal;

    if (party.members().empty())
    {
        return reveal;
    }

    int levelSum = 0;
    int bestScore = 0;
    SkillMastery bestMastery = SkillMastery::None;

    // Every member counts, able or not; skill bonuses add to the level but a member needs the skill itself.
    for (const Character &member : party.members())
    {
        levelSum += int(member.level);
        const CharacterSkill *pSkill = member.findSkill("IdentifyMonster");

        if (pSkill == nullptr || pSkill->level == 0)
        {
            continue;
        }

        const int level = int(pSkill->level) + member.skillBonus("IdentifyMonster");
        bestScore = std::max(bestScore, level * int(pSkill->mastery));
        bestMastery = std::max(bestMastery, pSkill->mastery);
    }

    reveal.hasSkill = bestMastery != SkillMastery::None;
    // MAW compares the monster's level as the game stores it, at most 255.
    const double required = std::min(monsterLevel, 255) - double(levelSum) / double(party.members().size());

    if (!reveal.hasSkill || (bestScore < required && bestMastery != SkillMastery::Grandmaster))
    {
        return reveal;
    }

    reveal.hitPointsAndArmorClass = true;
    reveal.attackAndDamage = bestMastery >= SkillMastery::Expert;
    reveal.spellsAndEffects = bestMastery >= SkillMastery::Master;
    reveal.resistances = bestMastery == SkillMastery::Grandmaster;
    return reveal;
}

std::pair<double, double> MawSkillRules::regenerationPerSecond(const Party &party, size_t index) const
{
    const Character &member = party.members()[index];
    MawBalanceModel &model = m_rules.model(int(std::max<size_t>(1, party.members().size())));
    const auto effectiveSkill = [&member](const char *pSkill)
    {
        const CharacterSkill *pFound = member.findSkill(pSkill);
        return std::pair<double, SkillMastery>(
            (pFound != nullptr ? double(pFound->level) : 0.0) + member.skillBonus(pSkill),
            pFound != nullptr ? pFound->mastery : SkillMastery::None);
    };

    const int fullHealth = Party::effectiveMaximumHealth(member);
    const auto [regeneration, regenerationMastery] = effectiveSkill("Regeneration");
    double healthPerSecond = mawRegenerationHealthPerSecond(
        regenerationMastery, model.health(std::pow(regeneration, 1.4)), fullHealth, member.health);

    // The Regeneration aura or the member's Regeneration potion, whichever heals more (SK:1364-1376).
    const std::optional<MawAuraSource> aura = m_rules.activeAura(RegenerationAura);
    const int potionSkill = member.rulesetState.potionEffect(TimedPotionEffect::Kind::Regeneration, 0);
    healthPerSecond += std::max(
        aura ? mawRegenerationAuraHealthPerSecond(fullHealth, aura->level, aura->skill, m_rules.buffScale()) : 0.0,
        mawRegenerationPotionHealthPerSecond(fullHealth, potionSkill));
    // Regeneration specials and artifacts: 0.2 % of full HP a second each (S:1358-1362).
    const int healthItems = mawWornSpecialCount(member, {37, 44, 50, 54, 66})
        + mawWornRegenerationArtifacts(member, false);
    healthPerSecond += 0.002 * fullHealth * healthItems;

    const int fullSpellPoints = Party::effectiveMaximumSpellPoints(member);
    const int reserved = m_rules.gameRules().spells.reservedSpellPoints(party, index);
    const double pool = mawMeditationPool(fullSpellPoints, reserved);
    const auto [meditation, meditationMastery] = effectiveSkill("Meditation");
    double spellPerSecond =
        mawMeditationSpellPerSecond(meditationMastery, model.mana(std::pow(meditation, 1.4) / 2), pool);

    // Legendary 20: 1 % more for each 1 % of the mana the auras reserve (Formulas.meditationRegenPerSec).
    if (fullSpellPoints > 0 && mawWearsLegendaryAffix(member, 20))
    {
        spellPerSecond *= 1 + std::clamp(double(reserved) / fullSpellPoints, 0.0, 1.0);
    }
    // Only the mana artifacts restore SP as items do; the SP specials raise Meditation instead (S:1455-1459).
    spellPerSecond += 0.002 * pool * mawWornRegenerationArtifacts(member, true);

    // The Meditation aura gives nothing to dragons, the Thief line and Death Knights.
    if (const std::optional<MawAuraSource> meditationAura = m_rules.activeAura(MeditationAura);
        meditationAura && !noMeditationAura(member))
    {
        spellPerSecond += mawMeditationAuraSpellPerSecond(pool, model.skill(meditationAura->level),
            meditationAura->skill, m_rules.buffScale());
    }

    return {healthPerSecond, spellPerSecond};
}

void MawSkillRules::applyProgressionMasteries(Party &party) const
{
    static constexpr std::array<const char *, 24> SwitchedSkills = {
        "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace", "Blaster", "Shield", "LeatherArmor", "ChainArmor",
        "PlateArmor", "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic",
        "LightMagic", "DarkMagic", "DarkElfAbility", "VampireAbility", "DragonAbility",
    };
    const bool horizontal = skillMode() != MawSkillMode::Normal;
    const bool switched = m_horizontalApplied && *m_horizontalApplied != horizontal;
    m_horizontalApplied = horizontal;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        Character &member = *party.member(index);
        auto &stored = member.rulesetState.progressionStoredMasteries;

        if (!horizontal && !stored.empty())
        {
            for (const auto &[canonical, mastery] : stored)
            {
                if (CharacterSkill *pSkill = member.findSkillByCanonicalName(canonical))
                {
                    pSkill->mastery = std::max(pSkill->mastery, mastery);
                }
            }

            stored.clear();
            continue;
        }

        if (!horizontal || !switched)
        {
            continue;
        }

        for (const char *pName : SwitchedSkills)
        {
            CharacterSkill *pSkill = member.findSkillByCanonicalName(pName);

            while (pSkill != nullptr && pSkill->mastery > SkillMastery::Normal
                && pSkill->level < mawMasteryRequiredLevel(skillMode(), pSkill->mastery))
            {
                SkillMastery &kept = stored[pName];
                kept = std::max(kept, pSkill->mastery);
                pSkill->mastery = SkillMastery(int(pSkill->mastery) - 1);
            }
        }
    }
}

void MawSkillRules::applySoloMasteries(Party &party) const
{
    static constexpr std::array<uint32_t, 4> Thresholds = {1, 4, 7, 10};
    const bool solo = party.members().size() == 1;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        Character &member = *party.member(index);
        auto &stored = member.rulesetState.soloStoredMasteries;

        if (!solo)
        {
            for (const auto &[canonical, mastery] : stored)
            {
                if (CharacterSkill *pSkill = member.findSkillByCanonicalName(canonical))
                {
                    pSkill->mastery = mastery;
                }
            }

            stored.clear();
            continue;
        }

        for (const char *pName : MawSoloMasterySkills)
        {
            CharacterSkill *pSkill = member.findSkillByCanonicalName(pName);

            if (pSkill == nullptr || pSkill->level == 0)
            {
                continue;
            }

            const SkillMastery solved = SkillMastery(std::count_if(Thresholds.begin(), Thresholds.end(),
                [pSkill](uint32_t threshold) { return pSkill->level >= threshold; }));

            if (solved > pSkill->mastery)
            {
                SkillMastery &kept = stored[pName];
                kept = std::max(kept, pSkill->mastery);
            }

            pSkill->mastery = solved;
        }
    }
}

void MawSkillRules::updateRegeneration(Party &party, const IGameplayWorldRuntime &world, float deltaSeconds) const
{
    applyProgressionMasteries(party);
    applySoloMasteries(party);

    constexpr float RecentLossSeconds = 20.0f;
    // MAW regenerates on a 0.1 second timer (zzMaw-Timers.lua:87); the rates read every member's full HP, SP and
    // skill bonuses, too dear for every frame.
    constexpr float RegenerationTickSeconds = 0.1f;

    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    // Losses are seen every frame, so a hit healed within the same tick still restarts the wait.
    for (size_t index = 0; index < party.members().size(); ++index)
    {
        Character &member = *party.member(index);
        // HP and SP each wait 20 seconds after a loss of their own (S:1395-1446); kept with the character.
        CharacterRulesRuntime &track = member.rulesetState.runtime;

        if (track.lastHealth >= 0 && member.health < track.lastHealth)
        {
            track.secondsSinceHealthLoss = 0;
        }
        else
        {
            track.secondsSinceHealthLoss += deltaSeconds;
        }

        track.lastHealth = member.health;

        if (track.lastSpellPoints >= 0 && member.spellPoints < track.lastSpellPoints)
        {
            track.secondsSinceSpellLoss = 0;
        }
        else
        {
            track.secondsSinceSpellLoss += deltaSeconds;
        }

        track.lastSpellPoints = member.spellPoints;
    }

    m_regenerationSeconds += deltaSeconds;

    if (m_regenerationSeconds < RegenerationTickSeconds)
    {
        return;
    }

    const float elapsedSeconds = m_regenerationSeconds;
    m_regenerationSeconds = 0.0f;
    const bool enemiesNear = partyHasYellowAlert(world);
    // A dimension map's slower regeneration (zzMAW-Skills.lua:1388-1390).
    const double mapRegeneration = 1 - m_rules.mapAffix(MawMapAffix::PlayerRegeneration).value_or(0) / 100;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        Character &member = *party.member(index);
        CharacterRulesRuntime &track = member.rulesetState.runtime;

        if (member.conditions.test(size_t(CharacterCondition::Dead))
            || member.conditions.test(size_t(CharacterCondition::Petrified))
            || member.conditions.test(size_t(CharacterCondition::Eradicated)))
        {
            continue;
        }

        // HP and SP each double after 20 seconds without a loss of their own (S:1395-1446).
        const double multiplier = mawRegenerationMultiplier(track.secondsSinceHealthLoss < RecentLossSeconds,
            enemiesNear) * elapsedSeconds * mapRegeneration;
        const double spellMultiplier = mawRegenerationMultiplier(track.secondsSinceSpellLoss < RecentLossSeconds,
            enemiesNear) * elapsedSeconds * mapRegeneration;
        const auto [healthPerSecond, spellPerSecond] = regenerationPerSecond(party, index);

        track.healthCarry += healthPerSecond * multiplier;
        const int health = int(track.healthCarry);

        if (health > 0)
        {
            track.healthCarry -= health;
            party.healMember(index, health);
            track.lastHealth = member.health;
        }

        if (member.conditions.test(size_t(CharacterCondition::Insane)))
        {
            continue;
        }

        const int fullSpellPoints = Party::effectiveMaximumSpellPoints(member);
        const int reserved = m_rules.gameRules().spells.reservedSpellPoints(party, index);
        track.spellCarry += spellPerSecond * spellMultiplier;
        const int spellPoints = int(track.spellCarry);

        if (spellPoints > 0)
        {
            track.spellCarry -= spellPoints;
            member.spellPoints = std::min(std::max(fullSpellPoints - reserved, 0), member.spellPoints + spellPoints);
        }

        track.lastSpellPoints = member.spellPoints;
    }
}

uint32_t MawSkillRules::masteryRequiredLevel(const std::string &canonicalSkill, SkillMastery mastery) const
{
    if (!mawIsHorizontalSkill(canonicalSkill) || mastery < SkillMastery::Expert)
    {
        return SkillRules::masteryRequiredLevel(canonicalSkill, mastery);
    }

    return mawMasteryRequiredLevel(skillMode(), mastery);
}

int MawSkillRules::masteryTeacherCost(
    const Character &character,
    const std::string &canonicalSkill,
    SkillMastery mastery,
    int standardCost) const
{
    if (!mawIsHorizontalSkill(canonicalSkill) || mastery < SkillMastery::Expert)
    {
        return standardCost;
    }

    // Each horizontal skill of 0-38 already at the mastery, or remembered at it, makes the lesson dearer; the taught
    // skill's own remembered mastery counts too (S:1866-1871, DEVIATIONS.md 18).
    int held = 0;

    for (const auto &[name, skill] : character.skills)
    {
        const std::string canonical = canonicalSkillName(skill.name);

        if (skill.level == 0 || !mawIsHorizontalSkill(canonical) || mawIsAddedSkill(canonical))
        {
            continue;
        }

        const auto remembered = character.rulesetState.rememberedMasteries.find(canonical);
        const SkillMastery current = canonical == canonicalSkill ? SkillMastery::None : skill.mastery;
        const SkillMastery highest = remembered != character.rulesetState.rememberedMasteries.end()
            ? std::max(current, remembered->second)
            : current;
        held += highest >= mastery ? 1 : 0;
    }

    return mawTeacherBasePrice(priceMode(), mastery) * (1 + held);
}

bool MawSkillRules::followerSkillBonusesStack() const
{
    return false;
}

std::optional<uint32_t> MawSkillRules::statLabelRgb(const std::string &statName) const
{
    static constexpr std::array<std::pair<const char *, uint32_t>, 10> Colors = {{
        {"Might", 0xff0000},
        {"Intellect", 0xff8000},
        {"Personality", 0x007fff},
        {"Endurance", 0x00ff00},
        {"Accuracy", 0xffff00},
        {"Speed", 0x7f00ff},
        {"Luck", 0xffffff},
        {"HitPoints", 0x00ff00},
        {"SpellPoints", 0x0064ff},
        {"ArmorClass", 0xe6cc80},
    }};

    for (const auto &[pName, rgb] : Colors)
    {
        if (statName == pName)
        {
            return rgb;
        }
    }

    return std::nullopt;
}

int MawSkillRules::followerSkillBonus(uint32_t professionId, const std::string &canonicalSkill, int tableBonus) const
{
    if (canonicalSkill != "Learning")
    {
        return tableBonus;
    }

    switch (professionId)
    {
        case 4: return 2;
        case 13: return 4;
        case 14: return 6;
        default: return tableBonus;
    }
}

bool MawSkillRules::followerSkillBonusNeedsSkill(const std::string &canonicalSkill) const
{
    return canonicalSkill == "Learning";
}

namespace
{
// The resistance rows, Fire to Body, with their item enchantments and each label in its element's colour
// (zzMaw-Stats.lua:892-897).
struct MawResistanceRow
{
    const char *pName;
    CombatDamageType type;
    int CharacterResistanceSet::*pItemResistance;
    uint32_t labelRgb;
};

constexpr std::array<MawResistanceRow, 6> MawResistanceRows = {{
    {"FireResistance", CombatDamageType::Fire, &CharacterResistanceSet::fire, 0xff4646u},
    {"AirResistance", CombatDamageType::Air, &CharacterResistanceSet::air, 0xadd8e6u},
    {"WaterResistance", CombatDamageType::Water, &CharacterResistanceSet::water, 0x64b4ffu},
    {"EarthResistance", CombatDamageType::Earth, &CharacterResistanceSet::earth, 0x994c00u},
    {"MindResistance", CombatDamageType::Mind, &CharacterResistanceSet::mind, 0xc8c8ffu},
    {"BodyResistance", CombatDamageType::Body, &CharacterResistanceSet::body, 0xffc0cbu}}};
}

std::optional<CharacterResistanceCut> MawSkillRules::resistanceCut(
    const Party &party,
    const Character &character,
    const std::string &statName) const
{
    for (size_t index = 0; index < MawResistanceRows.size(); ++index)
    {
        if (statName == MawResistanceRows[index].pName)
        {
            return resistanceCuts(party, character)[index];
        }
    }

    return std::nullopt;
}

std::array<std::optional<CharacterResistanceCut>, 6> MawSkillRules::resistanceCuts(
    const Party &party,
    const Character &character) const
{
    std::vector<CombatDamageType> types;

    for (const MawResistanceRow &row : MawResistanceRows)
    {
        types.push_back(row.type);
    }

    const int reference = std::max(1, int(mawRound(m_rules.state().totalLevel())));
    const std::vector<double> taken = mawDamageTakenPercents(m_rules, character, party.itemTable(),
        party.standardItemEnchantTable(), party.specialItemEnchantTable(), types, reference);
    std::array<std::optional<CharacterResistanceCut>, 6> cuts;

    for (size_t index = 0; index < MawResistanceRows.size(); ++index)
    {
        CharacterResistanceCut cut;
        cut.percent = 100 - taken[index];
        cut.raisedByItem = character.itemResistanceEnchants.*MawResistanceRows[index].pItemResistance > 0;
        cut.labelRgb = MawResistanceRows[index].labelRgb;
        cuts[index] = cut;
    }

    return cuts;
}

std::optional<CharacterStatRowText> MawSkillRules::statRowText(
    const Party &party,
    const Character &character,
    const std::string &statName) const
{
    // With the Bow preference off, the Shoot rows say so, unless a wand or blaster still fires there.
    if ((statName == "Shoot" || statName == "RangedDamage") && m_rules.options().preferences.bowDisabled)
    {
        const CharacterAttackProfile profile =
            GameMechanics::buildCharacterAttackProfile(character, party.itemTable(), nullptr, {});

        if (profile.hasWand || profile.hasBlaster)
        {
            return std::nullopt;
        }

        return statName == "Shoot" ? CharacterStatRowText{Engine::tr("Shoot"), Engine::tr("Bow off"), {}}
                                   : CharacterStatRowText{Engine::tr("Damage"), "-", {}};
    }

    const std::array<const char *, 4> names = {"Condition", "QuickSpell", "SpellPower", "Vitality"};

    for (size_t index = 0; index < names.size(); ++index)
    {
        if (statName == names[index])
        {
            return statRows(party, character)[index];
        }
    }

    return std::nullopt;
}

std::array<std::optional<CharacterStatRowText>, 4> MawSkillRules::statRows(
    const Party &party,
    const Character &character) const
{
    // MAW's stats page shows the powers and Vitality where Condition and Quick Spell were ("M/R/S", zzMaw-Stats.lua:
    // 1478-1492); here each has a row: Melee Power, Ranged Power, Spell Power ("-" without a damage spell, where MAW
    // leaves S out) and Vitality, four tighter rows in the box (compactStatPowerRows).
    if (party.itemTable() == nullptr)
    {
        return {};
    }

    const MawPowerReport report = mawPowerReport(m_rules, character, *party.itemTable(),
        party.standardItemEnchantTable(), party.specialItemEnchantTable(),
        int(std::max<size_t>(1, party.members().size())));
    // The labels in the interface language; the popup titles stay English, translated where the popup shows them.
    const auto row = [](std::string_view label, const char *pColor, double value, std::string_view title)
    {
        return CharacterStatRowText{Engine::tr(label),
            mawFillText(std::string("<") + pColor + ">{value}</>", {}, {{"value", mawShortNumber(value, false)}}),
            std::string(title)};
    };

    constexpr std::string_view SpellPowerTitle = Engine::trNoop("Spell Power");
    return {row(Engine::trNoop("Melee Power:"), "bad", report.melee, Engine::trNoop("Melee Power")),
        row(Engine::trNoop("Ranged Power:"), "value", report.ranged, Engine::trNoop("Ranged Power")),
        report.spell > 0 ? row(Engine::trNoop("Spell Power:"), "mana", report.spell, SpellPowerTitle)
                         : CharacterStatRowText{Engine::tr("Spell Power:"), "-", std::string(SpellPowerTitle)},
        row(Engine::trNoop("Vitality:"), "good", report.vitality, Engine::trNoop("Vitality"))};
}

bool MawSkillRules::compactStatPowerRows() const
{
    return true;
}

std::string MawSkillRules::statValueText(const std::string &text) const
{
    std::string result;
    size_t index = 0;

    while (index < text.size())
    {
        if (std::isdigit(static_cast<unsigned char>(text[index])) == 0)
        {
            result.push_back(text[index++]);
            continue;
        }

        const size_t start = index;

        while (index < text.size() && std::isdigit(static_cast<unsigned char>(text[index])) != 0)
        {
            ++index;
        }

        const std::string digits = text.substr(start, index - start);
        const double value = std::stod(digits);
        result += value >= 10000 ? mawShortNumber(value, false) : digits;
    }

    return result;
}
}
