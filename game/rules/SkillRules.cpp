#include "game/rules/SkillRules.h"

#include "engine/Localization.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <cmath>
#include <iterator>
#include <string_view>

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
    // A monster effect's save adds Luck to the stat bonus or resistance against it. Each template is one whole line.
    const auto resistText = [&percentText, luckBonus](std::string_view lineTemplate, int bonus)
    {
        return "\n"
            + Engine::tr(lineTemplate,
                {{"chance", percentText(GameMechanics::monsterEffectResistChance(bonus + luckBonus))}});
    };
    std::string text = table.empty() ? std::string() : table + "\n";
    // The lines below start with a line break: none before the first without a table text.
    const auto finish = [](std::string body) { return !body.empty() && body.front() == '\n' ? body.substr(1) : body; };

    // A resistance row: the damage it takes off with Luck, and the monster effects it resists.
    struct ResistanceRow
    {
        const char *pRow;
        std::string_view immune;
        std::string_view taken;
        const CharacterSheetValue *pValue;
        std::string_view resist;
    };
    const ResistanceRow resistances[] = {
        {"FireResistance", Engine::trNoop("Immune to fire damage"),
            Engine::trNoop("Fire damage taken: {share} less on average (Luck included)"), &sheet.fireResistance, {}},
        {"AirResistance", Engine::trNoop("Immune to air damage"),
            Engine::trNoop("Air damage taken: {share} less on average (Luck included)"), &sheet.airResistance, {}},
        {"WaterResistance", Engine::trNoop("Immune to water damage"),
            Engine::trNoop("Water damage taken: {share} less on average (Luck included)"), &sheet.waterResistance, {}},
        {"EarthResistance", Engine::trNoop("Immune to earth damage and to petrification"),
            Engine::trNoop("Earth damage taken: {share} less on average (Luck included)"), &sheet.earthResistance,
            Engine::trNoop("Chance to resist petrification: {chance}")},
        {"MindResistance", Engine::trNoop("Immune to mind damage and to insanity, paralysis and fear"),
            Engine::trNoop("Mind damage taken: {share} less on average (Luck included)"), &sheet.mindResistance,
            Engine::trNoop("Chance to resist insanity, paralysis and fear: {chance}")},
        {"BodyResistance", Engine::trNoop("Immune to body damage and to poison and death"),
            Engine::trNoop("Body damage taken: {share} less on average (Luck included)"), &sheet.bodyResistance,
            Engine::trNoop("Chance to resist poison and death: {chance}")},
    };

    for (const ResistanceRow &row : resistances)
    {
        if (statName != row.pRow)
        {
            continue;
        }

        if (row.pValue->infinite)
        {
            return finish(text + "\n" + Engine::tr(row.immune));
        }

        text += "\n"
            + Engine::tr(row.taken,
                {{"share", percentText(GameMechanics::averageResistedDamageShare(row.pValue->actual + luckBonus))}});
        return finish(!row.resist.empty() ? text + resistText(row.resist, row.pValue->actual) : text);
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
        text += "\n" + Engine::tr("Melee damage: {bonus}", {{"bonus", signedText(bonus)}});
    }
    else if (statName == "Intellect" || statName == "Personality")
    {
        const std::optional<int> spellPoints = GameMechanics::primaryStatSpellPointBonus(character, statName, value);
        text += "\n"
            + (spellPoints ? Engine::tr("Spell points: {bonus}", {{"bonus", signedText(*spellPoints)}})
                           : Engine::tr("No effect on this class's spell points"));

        if (statName == "Personality")
        {
            text += resistText(Engine::trNoop("Chance to resist curses: {chance}"), bonus);
        }

        text += resistText(Engine::trNoop("Chance to resist mana drain: {chance}"), manaDrainBonus);
    }
    else if (statName == "Endurance")
    {
        text += "\n"
            + Engine::tr("Hit points: {bonus}",
                {{"bonus", signedText(GameMechanics::enduranceHealthBonus(character, value))}})
            + resistText(Engine::trNoop("Chance to resist disease, sleep, weakness and aging: {chance}"), bonus);
    }
    else if (statName == "Accuracy")
    {
        text += "\n" + Engine::tr("Attack and Shoot: {bonus}", {{"bonus", signedText(bonus)}});
    }
    else if (statName == "Speed")
    {
        text += "\n" + Engine::tr("Armor class: {bonus}", {{"bonus", signedText(bonus)}}) + "\n"
            + Engine::tr("Recovery time: {bonus}", {{"bonus", signedText(-bonus)}});
    }
    else
    {
        // Luck joins every resistance roll that may halve a hit, physical ones too, and every monster effect's save.
        text += "\n"
            + Engine::tr("Physical damage taken: {share} less on average",
                {{"share", percentText(GameMechanics::averageResistedDamageShare(bonus))}})
            + "\n"
            + Engine::tr("Also improves every resistance and every chance to resist curses, poison, disease and other "
                         "monster effects");
    }

    if (const std::optional<int> next = GameMechanics::nextPrimaryStatBonusValue(value))
    {
        text += "\n" + Engine::tr("Next bonus threshold: {value}", {{"value", *next}});
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
