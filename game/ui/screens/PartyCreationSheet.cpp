#include "game/ui/screens/PartyCreationSheet.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/MergedBaseTables.h"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<std::string_view, 5> MasteryNames = {"", Engine::trNoop("Normal"), Engine::trNoop("Expert"),
    Engine::trNoop("Master"), Engine::trNoop("Grandmaster")};
// race_skills.yml exception codes: the rule skips warrior classes (-5) or casters (-4); a positive code is a class
// kind the rule skips.
constexpr int32_t WarriorClassesException = -5;
constexpr int32_t CasterClassesException = -4;

bool contains(const std::vector<std::string> &values, const std::string &value)
{
    return std::find(values.begin(), values.end(), value) != values.end();
}

std::string joined(const std::vector<std::string> &values)
{
    std::string text;

    for (const std::string &value : values)
    {
        text += (text.empty() ? "" : ", ") + value;
    }

    return text;
}

// A race skill rule's effect, as the race card states it: "at least Expert", "forbidden", "+1 mastery rank", with the
// classes it skips.
std::string raceSkillRuleEffect(const MergedRaceSkillOverride &rule, const ClassSkillTable &table)
{
    std::vector<std::string> parts;

    if (rule.minMastery > 0 && rule.minMastery < MasteryNames.size())
    {
        parts.push_back(Engine::tr("at least {mastery}", {{"mastery", Engine::tr(MasteryNames[rule.minMastery])}}));
    }

    if (rule.maxMastery)
    {
        parts.push_back(*rule.maxMastery == 0 || *rule.maxMastery >= MasteryNames.size()
                            ? Engine::tr("forbidden")
                            : Engine::tr("at most {mastery}",
                                         {{"mastery", Engine::tr(MasteryNames[*rule.maxMastery])}}));
    }

    if (rule.add != 0)
    {
        const std::string ranks = (rule.add > 0 ? "+" : "") + std::to_string(rule.add);
        parts.push_back(Engine::tr("{ranks} mastery rank", {{"ranks", ranks}}));
    }

    std::string effect = joined(parts);

    if (rule.exceptionCode == WarriorClassesException)
    {
        effect = Engine::tr("{effect} (warrior classes)", {{"effect", effect}});
    }
    else if (rule.exceptionCode == CasterClassesException)
    {
        effect = Engine::tr("{effect} (casters)", {{"effect", effect}});
    }
    else if (rule.exceptionCode > 0)
    {
        const std::vector<std::string> kind = table.classNamesOfKind(uint32_t(rule.exceptionCode), 0);

        if (!kind.empty())
        {
            effect = Engine::tr("{effect} (not {class} line)",
                                {{"effect", effect}, {"class", Engine::localize(displayClassName(kind.front()))}});
        }
    }

    return Engine::Utf8::capitalizedFirst(effect);
}
} // namespace

const std::array<const char *, CreationStatCount> &creationStatNames()
{
    // English: the names look up the stats' descriptions; the sheet translates them where it shows them.
    static const std::array<const char *, CreationStatCount> Names = {
        Engine::trNoop("Might").data(), Engine::trNoop("Intellect").data(), Engine::trNoop("Personality").data(),
        Engine::trNoop("Endurance").data(), Engine::trNoop("Accuracy").data(), Engine::trNoop("Speed").data(),
        Engine::trNoop("Luck").data(),
    };
    return Names;
}

const std::vector<CreationSkillGroup> &creationSkillGroups()
{
    static const std::vector<CreationSkillGroup> Groups = {
        {std::string(Engine::trNoop("Weapons")),
         {"Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Throwing", "Mace", "Blaster", "Unarmed"}},
        {std::string(Engine::trNoop("Armour")),
         {"Shield", "LeatherArmor", "ChainArmor", "PlateArmor", "Dodging", "Cover", "Retaliation", "ManaShield"}},
        {std::string(Engine::trNoop("Magic")),
         {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic", "LightMagic",
          "DarkMagic"}},
        {std::string(Engine::trNoop("Racial")), {"DarkElfAbility", "VampireAbility", "DragonAbility"}},
        {std::string(Engine::trNoop("Misc")),
         {"IdentifyItem", "Merchant", "RepairItem", "Bodybuilding", "Meditation", "Perception", "Regeneration",
          "DisarmTraps", "IdentifyMonster", "Armsmaster", "Stealing", "Alchemy", "Learning", "Enlightenment"}},
    };
    return Groups;
}

CreationSkillReach creationSkillReach(
    const ClassSkillTable &table, const std::string &className, uint32_t raceId, const std::string &skill)
{
    CreationSkillReach reach;
    reach.now = table.getEffectiveCap(className, raceId, skill);
    reach.best = std::max(reach.now, table.getHighestPromotionEffectiveCap(className, raceId, skill));
    return reach;
}

CreationSkillState creationSkillState(
    const std::vector<std::string> &fixedSkills,
    const std::vector<std::string> &optionalSkills,
    const std::vector<std::string> &chosenSkills,
    const CreationSkillReach &reach,
    const std::string &skill)
{
    if (contains(fixedSkills, skill))
    {
        return CreationSkillState::Fixed;
    }

    if (contains(optionalSkills, skill))
    {
        return contains(chosenSkills, skill) ? CreationSkillState::Chosen : CreationSkillState::Option;
    }

    return reach.best > SkillMastery::None ? CreationSkillState::Later : CreationSkillState::Never;
}

bool creationRaceChangesSkill(
    const ClassSkillTable &table, const std::string &className, uint32_t raceId, const std::string &skill)
{
    if (table.getEffectiveCap(className, raceId, skill) != table.getClassCap(className, skill))
    {
        return true;
    }

    for (const std::vector<std::string> &step : creationClassLine(table, className))
    {
        for (const std::string &promotion : step)
        {
            if (table.getEffectiveCap(promotion, raceId, skill) != table.getClassCap(promotion, skill))
            {
                return true;
            }
        }
    }

    return false;
}

int creationMasteryAvailability(
    const ClassSkillTable &table, const std::string &className, uint32_t raceId, const std::string &skill,
    SkillMastery mastery)
{
    if (table.getEffectiveCap(className, raceId, skill) >= mastery)
    {
        return 0;
    }

    return table.getHighestPromotionEffectiveCap(className, raceId, skill) >= mastery ? 1 : 2;
}

std::vector<std::vector<std::string>> creationClassLine(const ClassSkillTable &table, const std::string &className)
{
    std::vector<std::vector<std::string>> line = {{className}};
    const ClassMetadataEntry *pMetadata = table.classMetadata(className);

    if (pMetadata == nullptr)
    {
        return line;
    }

    for (uint32_t step = pMetadata->promotionStep + 1;; ++step)
    {
        std::vector<std::string> classes = table.classNamesOfKind(pMetadata->classKind, step);

        if (classes.empty())
        {
            break;
        }

        line.push_back(std::move(classes));
    }

    return line;
}

int raceStatTrend(const RaceStatLine &stat)
{
    if (stat.gainPerPoint > 1)
    {
        return 1;
    }

    return stat.pointsPerGain > 1 ? -1 : 0;
}

std::string raceStatTrendText(const RaceStatLine &stat)
{
    switch (raceStatTrend(stat))
    {
    case 1:
        return Engine::tr("+{gain} per point", {{"gain", stat.gainPerPoint}});
    case -1:
        return Engine::tr("{points} points per +1", {{"points", stat.pointsPerGain}});
    default:
        return Engine::tr("1 point per +1");
    }
}

std::vector<RaceCardLine> raceCardLines(
    const std::array<RaceStatLine, CreationStatCount> &stats,
    const std::array<const char *, CreationStatCount> &statNames,
    const std::vector<MergedRaceSkillOverride> &raceSkillRules,
    uint32_t raceId,
    const ClassSkillTable &table,
    const std::vector<std::string> &notes)
{
    std::vector<RaceCardLine> lines;

    // Attributes alike share a line: "Might, Endurance 14 · +2 per point · max 30".
    struct StatGroup
    {
        RaceStatLine stat;
        std::vector<std::string> names;
    };
    std::vector<StatGroup> groups;

    for (size_t index = 0; index < CreationStatCount; ++index)
    {
        const RaceStatLine &stat = stats[index];

        if (raceStatTrend(stat) == 0)
        {
            continue;
        }

        const auto same = std::find_if(groups.begin(), groups.end(),
            [&stat](const StatGroup &group)
            {
                return group.stat.base == stat.base && group.stat.maximum == stat.maximum
                    && group.stat.gainPerPoint == stat.gainPerPoint && group.stat.pointsPerGain == stat.pointsPerGain;
            });

        if (same != groups.end())
        {
            same->names.push_back(Engine::tr(statNames[index]));
        }
        else
        {
            groups.push_back({stat, {Engine::tr(statNames[index])}});
        }
    }

    if (groups.empty())
    {
        lines.push_back({RaceCardLine::Kind::Even,
            Engine::tr("Even attributes: {base} each, max {maximum}",
                {{"base", int64_t(stats[0].base)}, {"maximum", int64_t(stats[0].maximum)}})});
    }

    for (const StatGroup &group : groups)
    {
        lines.push_back({raceStatTrend(group.stat) > 0 ? RaceCardLine::Kind::Strong : RaceCardLine::Kind::Weak,
                         Engine::tr("{names} {base} · {trend} · max {maximum}", {{"names", joined(group.names)},
                             {"base", int64_t(group.stat.base)}, {"trend", raceStatTrendText(group.stat)},
                             {"maximum", int64_t(group.stat.maximum)}})});
    }

    // Skill rules with the same effect share a line: "+1 mastery rank: Learning".
    std::vector<std::pair<std::string, std::vector<std::string>>> effects;

    for (const MergedRaceSkillOverride &rule : raceSkillRules)
    {
        if (!rule.raceId || *rule.raceId != raceId || rule.skillName.empty())
        {
            continue;
        }

        const std::string effect = raceSkillRuleEffect(rule, table);

        if (effect.empty())
        {
            continue;
        }

        const auto same = std::find_if(effects.begin(), effects.end(),
            [&effect](const auto &entry)
            {
                return entry.first == effect;
            });
        const std::string skill = Engine::localize(displaySkillName(rule.skillName));

        if (same != effects.end())
        {
            if (!contains(same->second, skill))
            {
                same->second.push_back(skill);
            }
        }
        else
        {
            effects.push_back({effect, {skill}});
        }
    }

    for (const auto &[effect, skills] : effects)
    {
        lines.push_back({RaceCardLine::Kind::Skill,
            Engine::tr("{effect}: {skills}", {{"effect", effect}, {"skills", joined(skills)}})});
    }

    for (const std::string &note : notes)
    {
        lines.push_back({RaceCardLine::Kind::Note, note});
    }

    return lines;
}

CreationPartyCoverage creationPartyCoverage(const ClassSkillTable &table,
                                            const std::vector<CreationPartyMember> &members)
{
    CreationPartyCoverage coverage;

    for (const CreationSkillGroup &group : creationSkillGroups())
    {
        for (const std::string &skill : group.skills)
        {
            bool reachable = false;
            bool covered = false;
            SkillMastery coveredBest = SkillMastery::None;

            for (const CreationPartyMember &member : members)
            {
                const CreationSkillReach reach = creationSkillReach(table, member.className, member.raceId, skill);
                const CreationSkillState state =
                    creationSkillState(member.fixedSkills, member.optionalSkills, member.chosenSkills, reach, skill);
                reachable = reachable || reach.best > SkillMastery::None;

                if (state == CreationSkillState::Fixed || state == CreationSkillState::Chosen)
                {
                    covered = true;
                    coveredBest = std::max(coveredBest, reach.best);
                }
            }

            coverage.reachable += reachable ? 1 : 0;
            coverage.covered += covered ? 1 : 0;
            coverage.grandmaster += covered && coveredBest == SkillMastery::Grandmaster ? 1 : 0;
        }
    }

    return coverage;
}

std::string portraitTextureNameForEntry(const CharacterDollEntry &entry)
{
    if (!entry.facePicturesPrefix.empty())
    {
        return entry.facePicturesPrefix + "01";
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", entry.id);
    return buffer;
}

std::string classIconTextureName(const std::string &className)
{
    static const std::unordered_map<std::string, std::string> BorrowedIcons = {
        {"lich", "necromancer"},
    };
    std::string token;

    for (const unsigned char character : className)
    {
        if (std::isalnum(character) != 0)
        {
            token.push_back(char(std::tolower(character)));
        }
    }

    const auto borrowed = BorrowedIcons.find(token);
    return "hud_x2/menus/classes/" + (borrowed != BorrowedIcons.end() ? borrowed->second : token) + ".png";
}
} // namespace OpenYAMM::Game
