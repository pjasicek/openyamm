#include "game/rules/maw/MawMonsterLevels.h"

#include "game/rules/maw/MawExperienceCurve.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <exception>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string lowerCopy(std::string value)
{
    for (char &character : value)
    {
        character = char(std::tolower(static_cast<unsigned char>(character)));
    }

    return value;
}

// MAW's round: halves go up.
double mawRound(double value)
{
    return std::floor(value + 0.5);
}

constexpr double HorizontalMultiplier = 2.5;
}

bool MawMapLevels::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);

        for (const auto &entry : root["bands"])
        {
            const YAML::Node band = entry.second;

            if (!band.IsSequence() || band.size() != 3)
            {
                errorMessage = "band of " + entry.first.as<std::string>() + " must be [low, mid, high]";
                return false;
            }

            m_bands[lowerCopy(entry.first.as<std::string>())] = {
                band[0].as<double>(), band[1].as<double>(), band[2].as<double>()};
        }

        for (const YAML::Node &map : root["horizontal_starter_maps"])
        {
            m_horizontalStarterMaps.insert(lowerCopy(map.as<std::string>()));
        }

        for (const YAML::Node &map : root["madness"]["starting_maps"])
        {
            m_madnessStartingMaps.insert(lowerCopy(map.as<std::string>()));
        }

        for (const auto &entry : root["madness"]["levels"])
        {
            m_madnessLevels[lowerCopy(entry.first.as<std::string>())] = entry.second.as<int>();
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("map_levels.yml: ") + exception.what();
        return false;
    }

    if (m_bands.empty())
    {
        errorMessage = "map_levels.yml has no bands";
        return false;
    }

    return true;
}

bool MawMapLevels::loadWorldBalance(const std::string &text, std::string &errorMessage)
{
    const auto readBand = [](const YAML::Node &node, const std::string &mapFileName, std::array<double, 3> &band,
                              std::string &error)
    {
        if (!node.IsSequence() || node.size() != 3)
        {
            error = "band of " + mapFileName + " must be [low, mid, high]";
            return false;
        }

        band = {node[0].as<double>(), node[1].as<double>(), node[2].as<double>()};
        return true;
    };

    const auto readExclusions = [](const YAML::Node &node, std::unordered_set<int> &ids, std::vector<std::string> &names)
    {
        for (const YAML::Node &exclusion : node)
        {
            const std::string value = exclusion.as<std::string>();
            const bool numeric = !value.empty() && std::all_of(value.begin(), value.end(),
                [](char character) { return std::isdigit(static_cast<unsigned char>(character)) != 0; });

            if (numeric)
            {
                ids.insert(std::stoi(value));
            }
            else
            {
                names.push_back(value);
            }
        }
    };

    try
    {
        const YAML::Node root = YAML::Load(text);
        std::unordered_set<int> worldIds;
        std::vector<std::string> worldNames;
        readExclusions(root["completion_exclude"], worldIds, worldNames);
        DensityFactors fileDensity;

        if (const YAML::Node densityNode = root["density"])
        {
            for (const auto &entry : densityNode["difficulty"])
            {
                fileDensity.byDifficulty[entry.first.as<std::string>()] = entry.second.as<double>();
            }

            for (const auto &entry : densityNode["challenge"])
            {
                fileDensity.byChallengeMode[entry.first.as<std::string>()] = entry.second.as<double>();
            }
        }

        for (const auto &entry : root["maps"])
        {
            const std::string mapFileName = lowerCopy(entry.first.as<std::string>());
            const YAML::Node map = entry.second;
            DensityFactors &density = m_density[mapFileName];
            density = fileDensity;
            density.map = map["density"].as<double>(1.0);
            auto &[excludedIds, excludedNames] = m_completionExclusions[mapFileName];
            excludedIds = worldIds;
            excludedNames = worldNames;
            readExclusions(map["completion_exclude"], excludedIds, excludedNames);

            if (m_bands.contains(mapFileName))
            {
                errorMessage = mapFileName + " is listed twice";
                return false;
            }

            if (!readBand(map["band"], mapFileName, m_bands[mapFileName], errorMessage))
            {
                return false;
            }

            if (map["horizontal_starter"].as<bool>(false))
            {
                m_horizontalStarterMaps.insert(mapFileName);
            }

            if (map["madness_start"].as<bool>(false))
            {
                m_madnessStartingMaps.insert(mapFileName);
            }

            if (const int level = map["madness_level"].as<int>(0); level > 0)
            {
                m_madnessLevels[mapFileName] = level;
            }

            if (const YAML::Node nativesNode = map["natives"])
            {
                if (!nativesNode.IsSequence() || nativesNode.size() == 0 || nativesNode.size() > 3)
                {
                    errorMessage = "natives of " + mapFileName + " must list one to three families";
                    return false;
                }

                std::array<std::string, 3> &natives = m_natives[mapFileName];

                for (size_t index = 0; index < nativesNode.size(); ++index)
                {
                    natives[index] = nativesNode[index].as<std::string>();
                }
            }

            for (const YAML::Node &storyNode : map["story_bands"])
            {
                StoryBand storyBand;
                storyBand.qbit = storyNode["qbit"].as<uint32_t>();

                if (!readBand(storyNode["band"], mapFileName, storyBand.band, errorMessage))
                {
                    return false;
                }

                m_storyBands[mapFileName].push_back(storyBand);
            }
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("balance.yml: ") + exception.what();
        return false;
    }

    return true;
}

bool MawMapLevels::countsForCompletion(
    const std::string &mapFileName, const MonsterTable::MonsterStatsEntry &stats) const
{
    const auto exclusions = m_completionExclusions.find(lowerCopy(mapFileName));

    if (exclusions == m_completionExclusions.end())
    {
        return true;
    }

    const auto &[excludedIds, excludedNames] = exclusions->second;

    if (excludedIds.contains(stats.id))
    {
        return false;
    }

    for (const std::string &name : excludedNames)
    {
        const bool family = stats.pictureName.size() == name.size() + 2 && stats.pictureName.starts_with(name)
            && stats.pictureName[name.size()] == ' ';

        if (name == stats.name || name == stats.pictureName || family)
        {
            return false;
        }
    }

    return true;
}

const std::array<std::string, 3> *MawMapLevels::natives(const std::string &mapFileName) const
{
    const auto natives = m_natives.find(lowerCopy(mapFileName));
    return natives != m_natives.end() ? &natives->second : nullptr;
}

double MawMapLevels::densityFactor(
    const std::string &mapFileName, const std::string &difficulty, const std::string &challengeMode) const
{
    const auto density = m_density.find(lowerCopy(mapFileName));

    if (density == m_density.end())
    {
        return 1;
    }

    const DensityFactors &factors = density->second;
    const auto challenge = factors.byChallengeMode.find(challengeMode);
    const auto level = factors.byDifficulty.find(difficulty);
    const double modeFactor = challenge != factors.byChallengeMode.end() ? challenge->second
        : level != factors.byDifficulty.end()                         ? level->second
                                                                       : 1.0;
    return modeFactor * factors.map;
}

std::vector<uint32_t> MawMapLevels::storyBandQBits() const
{
    std::vector<uint32_t> qbits;

    for (const auto &[mapFileName, storyBands] : m_storyBands)
    {
        for (const StoryBand &storyBand : storyBands)
        {
            qbits.push_back(storyBand.qbit);
        }
    }

    return qbits;
}

bool MawMapLevels::setReachedStoryQBits(std::unordered_set<uint32_t> qbits)
{
    if (qbits == m_reachedStoryQBits)
    {
        return false;
    }

    m_reachedStoryQBits = std::move(qbits);
    return true;
}

std::array<double, 3> MawMapLevels::band(const std::string &mapFileName) const
{
    const std::string file = lowerCopy(mapFileName);

    if (const auto storyBands = m_storyBands.find(file); storyBands != m_storyBands.end())
    {
        for (auto storyBand = storyBands->second.rbegin(); storyBand != storyBands->second.rend(); ++storyBand)
        {
            if (m_reachedStoryQBits.contains(storyBand->qbit))
            {
                return storyBand->band;
            }
        }
    }

    const auto band = m_bands.find(file);
    return band != m_bands.end() ? band->second : std::array<double, 3>{1, 1, 1};
}

bool MawMapLevels::lists(const std::string &mapFileName) const
{
    return m_bands.contains(lowerCopy(mapFileName));
}

bool MawMapLevels::isHorizontalStarterMap(const std::string &mapFileName) const
{
    return m_horizontalStarterMaps.contains(lowerCopy(mapFileName));
}

bool MawMapLevels::isMadnessStartingMap(const std::string &mapFileName) const
{
    return m_madnessStartingMaps.contains(lowerCopy(mapFileName));
}

int MawMapLevels::madnessLevel(const std::string &mapFileName) const
{
    const auto level = m_madnessLevels.find(lowerCopy(mapFileName));
    return level != m_madnessLevels.end() ? level->second : 0;
}

bool mawLevelsMonster(int monsterId)
{
    return (monsterId >= 1 && monsterId <= MawMonsterRows) || monsterId >= MawWorldMonsterRows;
}

int MawMonsterFamily::row(int tierIndex) const
{
    const int row = tierIndex >= 1 && tierIndex <= 3 ? rows[size_t(tierIndex - 1)] : 0;
    return row != 0 ? row : rows[1] != 0 ? rows[1] : monsterId;
}

MawMonsterFamily mawMonsterFamily(const MonsterTable *pMonsterTable, int monsterId)
{
    MawMonsterFamily family;
    family.monsterId = monsterId;

    if (monsterId < MawWorldMonsterRows)
    {
        const int first = (monsterId - 1) / 3 * 3 + 1;
        family.tier = uint8_t(monsterId - first + 1);
        family.rows = {first, first + 1, first + 2};
        return family;
    }

    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(int16_t(monsterId)) : nullptr;
    const std::string picture = pStats != nullptr ? pStats->pictureName : std::string();
    const size_t suffix = picture.size() >= 2 && picture[picture.size() - 2] == ' '
            && picture.back() >= 'A' && picture.back() <= 'C'
        ? picture.size() - 2
        : std::string::npos;

    if (suffix == std::string::npos)
    {
        family.rows[1] = monsterId;
        return family;
    }

    family.tier = uint8_t(picture.back() - 'A' + 1);
    const std::string stem = picture.substr(0, suffix + 1);

    // The family's rows by picture, wherever they lie (MM9's Skeleton C is 9135, its A and B 9183 and 9184); some
    // families lack a tier.
    for (int tier = 1; tier <= 3; ++tier)
    {
        const std::string tierPicture = stem + char('A' + tier - 1);
        const MonsterTable::MonsterStatsEntry *pRow = pMonsterTable->findStatsByPictureName(tierPicture);

        if (pRow != nullptr && pRow->pictureName == tierPicture && pRow->id >= MawWorldMonsterRows)
        {
            family.rows[size_t(tier - 1)] = pRow->id;
        }
    }

    return family;
}

bool mawArenaMap(const std::string &mapFileName)
{
    const std::string file = lowerCopy(mapFileName);
    return file == "d42.blv" || file == "7d05.blv" || file == "zarena.blv" || file == "thearena.blv";
}

double mawMapBolster(const MawMapLevels &mapLevels, const MawMonsterLevelInputs &inputs)
{
    double bolster = std::max(inputs.partyLevel - 4, 0.0);

    if (inputs.austerity && inputs.partyLevel - 4 > 0)
    {
        bolster = std::pow(inputs.partyLevel - 4, 1.015);
    }

    const int madnessLevel = mapLevels.madnessLevel(inputs.mapFileName);

    if (inputs.madness && madnessLevel > 0 && !mapLevels.isMadnessStartingMap(inputs.mapFileName))
    {
        bolster = madnessLevel;
    }

    bolster += inputs.resetCount * 20.0;

    // A dimension map sets the bolster itself, and its monsters are not bolstered to the party.
    if (inputs.dimensionPower)
    {
        bolster = *inputs.dimensionPower * 10.0 + 20;
    }

    return bolster;
}

std::unordered_map<int, int> resolveMawMonsterLevels(
    const MonsterTable &monsterTable,
    const MawMapLevels &mapLevels,
    const MawMonsterLevelInputs &inputs)
{
    const auto baseLevel = [&monsterTable](int monsterId)
    {
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(monsterId));
        return pStats != nullptr ? pStats->level : 0;
    };

    double bolster = mawMapBolster(mapLevels, inputs);
    const double resetBonus = inputs.resetCount * 20.0;
    const int madnessLevel = mapLevels.madnessLevel(inputs.mapFileName);
    const bool fixedMadnessLevel =
        inputs.madness && madnessLevel > 0 && !mapLevels.isMadnessStartingMap(inputs.mapFileName);
    const bool partyBolster = !fixedMadnessLevel && !inputs.dimensionPower;
    const bool arenaMap = mawArenaMap(inputs.mapFileName);

    if (arenaMap)
    {
        bolster = 0;
    }

    // Native families: B rows whose picture is one of the map's encounter pictures, in monster-id order (a picture
    // listed twice counts twice), the first three sorted by base level.
    std::vector<int> natives;
    std::vector<int> monsterIds;

    for (const auto &[monsterId, stats] : monsterTable.statsEntries())
    {
        if (mawLevelsMonster(monsterId))
        {
            monsterIds.push_back(monsterId);
        }
    }

    std::sort(monsterIds.begin(), monsterIds.end());

    for (int monsterId : monsterIds)
    {
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(monsterId));

        for (const std::string &picture : inputs.encounterPictures)
        {
            if (pStats != nullptr && !picture.empty() && picture + " B" == pStats->pictureName)
            {
                natives.push_back(monsterId);
            }
        }
    }

    if (natives.size() >= 2)
    {
        const auto order = [&](size_t first, size_t second)
        {
            if (baseLevel(natives[first]) > baseLevel(natives[second]))
            {
                std::swap(natives[first], natives[second]);
            }
        };
        order(0, 1);

        if (natives.size() == 3)
        {
            order(1, 2);
            order(0, 1);
        }
    }

    const std::array<double, 3> band = mapLevels.band(inputs.mapFileName);
    const double low = band[0];
    const double mid = band[1];
    const double high = band[2];
    const double mean = (low + mid + high) / 3;
    const double adjustMult = inputs.madness ? 1 : 1.5;
    const bool starterMap = mapLevels.isHorizontalStarterMap(inputs.mapFileName);
    std::unordered_map<int, int> levels;

    for (int monsterId : monsterIds)
    {
        const MawMonsterFamily family = mawMonsterFamily(&monsterTable, monsterId);
        const double base = baseLevel(monsterId);
        const double familyLevel = baseLevel(family.row(2));
        double extraBolster = 0;

        if (familyLevel < low)
        {
            extraBolster = (low - familyLevel) / 2;
        }
        else if (familyLevel > high)
        {
            extraBolster = (high - familyLevel) / 2;
        }

        double adjust = 0;
        double nativeSlot = 0;

        for (size_t index = 0; index < natives.size(); ++index)
        {
            if (family.row(2) != natives[index])
            {
                continue;
            }

            const bool lowSlot = index == 0;
            const bool midSlot = index == 1 && natives.size() == 3;
            const bool highSlot = (index == 1 && natives.size() == 2) || index == 2;

            if (lowSlot || midSlot || highSlot)
            {
                nativeSlot = lowSlot ? low : midSlot ? mid : high;
                extraBolster = nativeSlot - familyLevel;
                adjust = (mean - nativeSlot) * adjustMult;
            }
        }

        if (arenaMap)
        {
            extraBolster = 0;
        }

        double level = partyBolster ? mawBolsteredLevel(bolster, base + extraBolster) : base + bolster + extraBolster;

        if ((inputs.horizontalProgression || inputs.madness) && !inputs.dimensionPower)
        {
            // MAW counts the reset bonus twice in this cap (BALANCE_MODEL.md §7.3).
            const double cap = partyBolster ? mawBolsteredLevel(bolster + resetBonus, base + extraBolster)
                                            : base + bolster + extraBolster + resetBonus;
            level = std::max(std::min((base + extraBolster) * HorizontalMultiplier, cap), 1.0);

            if (!starterMap)
            {
                // A map's monsters sit at about 2.5 times its band; the tier spread and the band's spread stay 1x.
                const double flattener = (base - familyLevel) * HorizontalMultiplier * 0.6;
                level = std::max(
                    base * HorizontalMultiplier + extraBolster * HorizontalMultiplier - 5 - flattener + adjust - 4
                        + resetBonus,
                    5.0);
            }
        }

        if (fixedMadnessLevel && !inputs.dimensionPower)
        {
            const double offset = (nativeSlot - mean) * 2 + (base - familyLevel) * 2;
            const double fixed = offset >= 0 ? mawBolsteredLevel(madnessLevel, offset)
                                             : 2.0 * madnessLevel - mawBolsteredLevel(madnessLevel, -offset);
            level = std::max(fixed, 5.0);
        }

        // The Arena (d42), where the Endless Arena brings every family: six times the base level, the tiers closer
        // together (zzMaw-Monsters.lua:577-589).
        if (inputs.mapFileName == "d42.blv")
        {
            level = std::max(base * 6 - (base - familyLevel) * 6 * 0.8 + adjust * 2, 5.0);
        }

        if (inputs.bountyLevel)
        {
            level = base + *inputs.bountyLevel;
        }

        levels[monsterId] = int(mawRound(std::max(level, 1.0)));
    }

    return levels;
}
}
