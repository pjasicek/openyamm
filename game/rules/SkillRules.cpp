#include "game/rules/SkillRules.h"

#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <cmath>
#include <iterator>
#include <tuple>

namespace OpenYAMM::Game
{
uint32_t SkillRules::skillRaiseCost(const Character &character, const std::string &canonicalSkill) const
{
    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);
    return pSkill != nullptr ? pSkill->level + 1 : 1;
}

std::string SkillRules::skillDisplayName(const Character &, const std::string &canonicalSkill) const
{
    return displaySkillName(canonicalSkill);
}

std::vector<std::pair<std::string, std::array<uint32_t, 3>>> SkillRules::teacherlessMasteryLadders() const
{
    return {};
}

std::vector<std::string> SkillRules::extraHouseSkills(const std::string &) const
{
    return {};
}

std::optional<uint32_t> SkillRules::skillLevelCap(const std::string &) const
{
    return std::nullopt;
}

bool SkillRules::canRaiseSkill(const Character &character, const std::string &canonicalSkill) const
{
    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);

    if (pSkill == nullptr)
    {
        return false;
    }

    const std::optional<uint32_t> cap = skillLevelCap(canonicalSkill);
    return (!cap || pSkill->level < *cap)
        && character.pointsForRaisingSkill(canonicalSkill) >= skillRaiseCost(character, canonicalSkill);
}

std::string SkillRules::afterSkillRaised(Character &, const std::string &, const ClassSkillTable *) const
{
    return {};
}

uint32_t SkillRules::masteryRequiredLevel(const std::string &, SkillMastery mastery) const
{
    switch (mastery)
    {
        case SkillMastery::Expert:
            return 4;
        case SkillMastery::Master:
            return 7;
        case SkillMastery::Grandmaster:
            return 10;
        default:
            return 0;
    }
}

int SkillRules::masteryTeacherCost(const Character &, const std::string &, SkillMastery, int standardCost) const
{
    return standardCost;
}

std::optional<int> SkillRules::skillResetCost(const Character &) const
{
    return std::nullopt;
}

bool SkillRules::resetSkills(Character &) const
{
    return false;
}

void SkillRules::applyStatBonuses(Character &) const
{
}

void SkillRules::applyResourceBonuses(Character &) const
{
}

std::optional<CharacterCombatRows> SkillRules::combatRows(
    const Character &,
    const ItemTable *,
    const CharacterStatValues &) const
{
    return std::nullopt;
}

float SkillRules::regenerationHealthPerSecond(const Character &member) const
{
    constexpr float FiveGameMinuteTickRealSeconds = 10.0f;
    const CharacterSkill *pSkill = member.findSkill("Regeneration");
    return pSkill != nullptr ? float(pSkill->level * uint32_t(pSkill->mastery)) / FiveGameMinuteTickRealSeconds : 0.0f;
}

int SkillRules::meditationSpellPointsPerTick(const Character &member) const
{
    const CharacterSkill *pMeditation = member.findSkill("Meditation");

    if (pMeditation == nullptr || pMeditation->mastery == SkillMastery::None)
    {
        return 0;
    }

    const int skillLevel = std::max(0, int(pMeditation->level) + member.skillBonus("Meditation"));
    return int(pMeditation->mastery) + skillLevel / 10;
}

void SkillRules::updateRegeneration(Party &, const IGameplayWorldRuntime &, float) const
{
}

SkillTooltipText SkillRules::skillTooltip(
    const Party &,
    const Character &,
    const std::string &,
    const SkillTooltipText &table) const
{
    return table;
}

std::string SkillRules::statTooltip(
    const Party &party,
    const Character &character,
    const std::string &statName,
    const std::string &table) const
{
    const CharacterSheetSummary sheet = GameMechanics::buildCharacterSheetSummary(character, party.itemTable(),
        party.standardItemEnchantTable(), party.specialItemEnchantTable());
    const int luckBonus = GameMechanics::primaryStatBonus(sheet.luck.actual);
    const auto signedText = [](int number) { return (number >= 0 ? "+" : "") + std::to_string(number); };
    const auto percentText = [](float share) { return std::to_string(int(std::lround(100.0f * share))) + "%"; };
    // A monster effect's save adds Luck to the stat bonus or resistance against it.
    const auto resistText = [&percentText, luckBonus](const std::string &effects, int bonus)
    {
        return "\nChance to resist " + effects + ": "
            + percentText(GameMechanics::monsterEffectResistChance(bonus + luckBonus));
    };
    std::string text = table.empty() ? std::string() : table + "\n";
    // The lines below start with a line break: none before the first without a table text.
    const auto finish = [](std::string body) { return !body.empty() && body.front() == '\n' ? body.substr(1) : body; };

    // A resistance row: the damage it takes off with Luck, and the monster effects it resists.
    const std::tuple<const char *, const char *, const CharacterSheetValue *, const char *> resistances[] = {
        {"FireResistance", "Fire", &sheet.fireResistance, nullptr},
        {"AirResistance", "Air", &sheet.airResistance, nullptr},
        {"WaterResistance", "Water", &sheet.waterResistance, nullptr},
        {"EarthResistance", "Earth", &sheet.earthResistance, "petrification"},
        {"MindResistance", "Mind", &sheet.mindResistance, "insanity, paralysis and fear"},
        {"BodyResistance", "Body", &sheet.bodyResistance, "poison and death"},
    };

    for (const auto &[pRow, pDamage, pValue, pEffects] : resistances)
    {
        if (statName != pRow)
        {
            continue;
        }

        if (pValue->infinite)
        {
            return finish(text + "\nImmune to " + toLowerCopy(pDamage) + " damage"
                + (pEffects != nullptr ? std::string(" and to ") + pEffects : std::string()));
        }

        text += "\n" + std::string(pDamage) + " damage taken: "
            + percentText(GameMechanics::averageResistedDamageShare(pValue->actual + luckBonus))
            + " less on average (Luck included)";
        return finish(pEffects != nullptr ? text + resistText(pEffects, pValue->actual) : text);
    }

    const std::pair<const char *, int> stats[] = {
        {"Might", sheet.might.actual},
        {"Intellect", sheet.intellect.actual},
        {"Personality", sheet.personality.actual},
        {"Endurance", sheet.endurance.actual},
        {"Accuracy", sheet.accuracy.actual},
        {"Speed", sheet.speed.actual},
        {"Luck", sheet.luck.actual},
    };
    const auto stat = std::find_if(std::begin(stats), std::end(stats),
        [&statName](const std::pair<const char *, int> &entry) { return statName == entry.first; });

    if (stat == std::end(stats))
    {
        return table;
    }

    // What the value gives through MM's bonus table, and the value where the bonus next goes up.
    const int value = stat->second;
    const int bonus = GameMechanics::primaryStatBonus(value);
    const int manaDrainBonus = (GameMechanics::primaryStatBonus(sheet.intellect.actual)
        + GameMechanics::primaryStatBonus(sheet.personality.actual)) / 2;

    if (statName == "Might")
    {
        text += "\nMelee damage: " + signedText(bonus);
    }
    else if (statName == "Intellect" || statName == "Personality")
    {
        const std::optional<int> spellPoints = GameMechanics::primaryStatSpellPointBonus(character, statName, value);
        text += spellPoints ? "\nSpell points: " + signedText(*spellPoints)
                            : "\nNo effect on this class's spell points";

        if (statName == "Personality")
        {
            text += resistText("curses", bonus);
        }

        text += resistText("mana drain", manaDrainBonus);
    }
    else if (statName == "Endurance")
    {
        text += "\nHit points: " + signedText(GameMechanics::enduranceHealthBonus(character, value))
            + resistText("disease, sleep, weakness and aging", bonus);
    }
    else if (statName == "Accuracy")
    {
        text += "\nAttack and Shoot: " + signedText(bonus);
    }
    else if (statName == "Speed")
    {
        text += "\nArmor class: " + signedText(bonus) + "\nRecovery time: " + signedText(-bonus);
    }
    else
    {
        // Luck joins every resistance roll that may halve a hit, physical ones too, and every monster effect's save.
        text += "\nPhysical damage taken: " + percentText(GameMechanics::averageResistedDamageShare(bonus))
            + " less on average\nAlso improves every resistance and every chance to resist curses, poison, disease and "
              "other monster effects";
    }

    if (const std::optional<int> next = GameMechanics::nextPrimaryStatBonusValue(value))
    {
        text += "\nNext bonus threshold: " + std::to_string(*next);
    }

    return finish(text);
}

std::string SkillRules::teacherSpeech(
    const std::string &text,
    const std::string &,
    SkillMastery,
    uint32_t,
    int) const
{
    return text;
}

float SkillRules::trainingPriceMultiplier(const Character &, float houseMultiplier) const
{
    return houseMultiplier;
}

std::optional<SkillRaiseCost> SkillRules::skillRaiseCostDetail(const Character &, const std::string &) const
{
    return std::nullopt;
}

IdentifyMonsterReveal SkillRules::identifyMonsterReveal(const Party &party, int monsterLevel) const
{
    const Character *pIdentifier = party.bestPartyWideUtilitySkillMember("IdentifyMonster");
    return pIdentifier != nullptr ? GameMechanics::resolveIdentifyMonsterReveal(*pIdentifier, monsterLevel)
                                  : IdentifyMonsterReveal {};
}

const SkillRules &standardSkillRules()
{
    static const SkillRules Rules;
    return Rules;
}

bool SkillRules::followerSkillBonusesStack() const
{
    return true;
}

int SkillRules::followerSkillBonus(uint32_t, const std::string &, int tableBonus) const
{
    return tableBonus;
}

bool SkillRules::followerSkillBonusNeedsSkill(const std::string &) const
{
    return false;
}

std::optional<CharacterStatRowText> SkillRules::statRowText(const Party &, const Character &, const std::string &) const
{
    return std::nullopt;
}

std::array<std::optional<CharacterStatRowText>, 4> SkillRules::statRows(
    const Party &party,
    const Character &character) const
{
    return {statRowText(party, character, "Condition"), statRowText(party, character, "QuickSpell"),
        statRowText(party, character, "SpellPower"), statRowText(party, character, "Vitality")};
}

bool SkillRules::compactStatPowerRows() const
{
    return false;
}

std::optional<CharacterResistanceCut> SkillRules::resistanceCut(const Party &, const Character &,
    const std::string &) const
{
    return std::nullopt;
}

std::optional<uint32_t> SkillRules::statLabelRgb(const std::string &) const
{
    return std::nullopt;
}

std::array<std::optional<CharacterResistanceCut>, 6> SkillRules::resistanceCuts(
    const Party &party,
    const Character &character) const
{
    std::array<std::optional<CharacterResistanceCut>, 6> cuts;
    const std::array<const char *, 6> names = {
        "FireResistance", "AirResistance", "WaterResistance", "EarthResistance", "MindResistance", "BodyResistance"};

    for (size_t index = 0; index < names.size(); ++index)
    {
        cuts[index] = resistanceCut(party, character, names[index]);
    }

    return cuts;
}

std::string SkillRules::statValueText(const std::string &text) const
{
    return text;
}
}
