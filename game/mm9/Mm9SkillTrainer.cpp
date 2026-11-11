#include "game/mm9/Mm9SkillTrainer.h"

#include "game/party/SkillData.h"
#include "game/tables/MapStats.h"
#include <algorithm>
#include <charconv>
#include <cctype>
#include <cmath>
#include <set>
#include <stdexcept>
#include <limits>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ExpectedColumnCount = 20;

std::string lowerCopy(const std::string &value)
{
    std::string result = value;
    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return result;
}

template<typename T>
bool parseUnsigned(const std::string &value, T &result)
{
    uint64_t parsed = 0;
    const char *pBegin = value.data();
    const char *pEnd = pBegin + value.size();
    const std::from_chars_result parseResult = std::from_chars(pBegin, pEnd, parsed);
    if (parseResult.ec != std::errc() || parseResult.ptr != pEnd
        || parsed > static_cast<uint64_t>(std::numeric_limits<T>::max()))
    {
        return false;
    }
    result = static_cast<T>(parsed);
    return true;
}

bool parseInt32(const std::string &value, int32_t &result)
{
    const char *pBegin = value.data();
    const char *pEnd = pBegin + value.size();
    const std::from_chars_result parseResult = std::from_chars(pBegin, pEnd, result);
    return parseResult.ec == std::errc() && parseResult.ptr == pEnd;
}

std::vector<std::string> split(const std::string &value)
{
    std::vector<std::string> result;
    size_t begin = 0;
    while (begin <= value.size())
    {
        const size_t end = value.find('|', begin);
        const std::string item = value.substr(begin, end == std::string::npos ? end : end - begin);
        if (!item.empty())
        {
            result.push_back(item);
        }
        if (end == std::string::npos)
        {
            break;
        }
        begin = end + 1;
    }
    return result;
}

bool parseIntList(const std::string &value, std::vector<int32_t> &result)
{
    for (const std::string &item : split(value))
    {
        int32_t parsed = 0;
        if (!parseInt32(item, parsed) || parsed <= 0)
        {
            return false;
        }
        result.push_back(parsed);
    }
    return true;
}

SkillMastery parseMastery(const std::string &value)
{
    if (value == "Expert")
    {
        return SkillMastery::Expert;
    }
    if (value == "Master")
    {
        return SkillMastery::Master;
    }
    if (value == "Grandmaster")
    {
        return SkillMastery::Grandmaster;
    }
    return SkillMastery::None;
}

uint32_t requiredRankForMastery(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert: return 4;
        case SkillMastery::Master: return 7;
        case SkillMastery::Grandmaster: return 10;
        default: return 0;
    }
}

// Each listed skill is its own training choice, so every one must be a distinct OpenYAMM skill.
bool validSeparateSkills(const std::vector<std::string> &skillNames)
{
    for (size_t index = 0; index < skillNames.size(); ++index)
    {
        if (!skillIdForSkillName(skillNames[index]) || canonicalSkillName(skillNames[index]) != skillNames[index]
            || std::find(skillNames.begin(), skillNames.begin() + index, skillNames[index])
                != skillNames.begin() + index)
        {
            return false;
        }
    }
    return !skillNames.empty();
}

uint64_t rudeRowKey(uint32_t rudeId, size_t rowIndex)
{
    return (static_cast<uint64_t>(rudeId) << 32) | static_cast<uint64_t>(rowIndex);
}
}

void Mm9SkillTrainerTable::clear()
{
    m_entries.clear();
    m_entryIndexByCanonicalId.clear();
    m_entryIndexByRudeRow.clear();
    m_errors.clear();
}

bool Mm9SkillTrainerTable::loadFromRows(
    const std::vector<std::vector<std::string>> &rows,
    const Mm9RudeDialogueTable &rudeDialogueTable)
{
    clear();
    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];
        if (row.empty() || row[0].empty() || row[0] == "CanonicalId")
        {
            continue;
        }
        const size_t rowNumber = rowIndex + 1;
        if (row.size() < ExpectedColumnCount)
        {
            addError(rowNumber, "expected 20 columns");
            continue;
        }

        Mm9SkillTrainerService entry = {};
        entry.canonicalId = row[0];
        entry.mm9Skill = row[6];
        entry.topic.skillNames = split(row[7]);
        entry.topic.targetMastery = parseMastery(row[8]);
        entry.expectedRegion = row[13];
        entry.sourceDisplayNames = split(row[14]);
        entry.npc998Hint = row[15];
        entry.actorOwnership = row[16];
        entry.actorSources = split(row[17]);
        entry.sourceRude = row[18];
        entry.provenance = row[19];

        if (!parseUnsigned(row[1], entry.rudeId)
            || !parseUnsigned(row[2], entry.rudeRowIndex)
            || !parseUnsigned(row[3], entry.sourceLine)
            || !parseInt32(row[4], entry.choiceSlot)
            || !parseInt32(row[5], entry.topic.rawTrainerId)
            || !parseUnsigned(row[9], entry.requiredSkillRank)
            || !parseUnsigned(row[10], entry.requiredGold)
            || !parseIntList(row[11], entry.requiredRawKeys)
            || !parseIntList(row[12], entry.forbiddenRawKeys))
        {
            addError(rowNumber, "invalid numeric field or quest-key list");
            continue;
        }
        entry.topic.requiredSkillRank = entry.requiredSkillRank;
        entry.topic.requiredGold = entry.requiredGold;
        entry.topic.displayName = entry.mm9Skill;
        if (!entry.canonicalId.starts_with("mm9:trainer/") || entry.mm9Skill.empty()
            || entry.topic.skillNames.empty() || entry.topic.targetMastery == SkillMastery::None
            || entry.requiredSkillRank != requiredRankForMastery(entry.topic.targetMastery)
            || entry.expectedRegion.empty() || entry.sourceDisplayNames.empty() || entry.npc998Hint.empty()
            || (entry.actorOwnership != "static" && entry.actorOwnership != "scheduled")
            || entry.actorSources.empty() || entry.sourceRude.empty() || entry.provenance.empty())
        {
            addError(rowNumber, "invalid trainer identity, operation, actor ownership, or provenance");
            continue;
        }
        if (!validSeparateSkills(entry.topic.skillNames))
        {
            addError(rowNumber, "trainer skills must be distinct canonical OpenYAMM skills");
            continue;
        }

        const Mm9RudeRow *pRudeRow = rudeDialogueTable.rowByIndex(entry.rudeId, entry.rudeRowIndex);
        if (pRudeRow == nullptr || pRudeRow->sourceLine != entry.sourceLine || pRudeRow->choiceSlot != entry.choiceSlot
            || pRudeRow->next != -4 || pRudeRow->rawColumns.size() <= 15
            || pRudeRow->rawColumns[15] != std::to_string(entry.topic.rawTrainerId)
            || pRudeRow->requiredRawKeys != entry.requiredRawKeys
            || pRudeRow->forbiddenRawKeys != entry.forbiddenRawKeys)
        {
            addError(rowNumber, "trainer service does not match its authoritative RUDE row");
            continue;
        }

        const std::string normalizedId = lowerCopy(entry.canonicalId);
        const uint64_t sourceKey = rudeRowKey(entry.rudeId, entry.rudeRowIndex);
        if (m_entryIndexByCanonicalId.contains(normalizedId))
        {
            addError(rowNumber, "duplicate canonical trainer id");
            continue;
        }
        if (m_entryIndexByRudeRow.contains(sourceKey))
        {
            addError(rowNumber, "duplicate RUDE row ownership");
            continue;
        }
        const size_t entryIndex = m_entries.size();
        m_entries.push_back(std::move(entry));
        m_entryIndexByCanonicalId[normalizedId] = entryIndex;
        m_entryIndexByRudeRow[sourceKey] = entryIndex;
    }
    return !m_entries.empty() && m_errors.empty();
}

const Mm9SkillTrainerService *Mm9SkillTrainerTable::find(uint32_t rudeId, size_t rudeRowIndex) const
{
    const auto iterator = m_entryIndexByRudeRow.find(rudeRowKey(rudeId, rudeRowIndex));
    return iterator != m_entryIndexByRudeRow.end() ? &m_entries[iterator->second] : nullptr;
}

const Mm9SkillTrainerService *Mm9SkillTrainerTable::findByCanonicalId(const std::string &canonicalId) const
{
    const auto iterator = m_entryIndexByCanonicalId.find(lowerCopy(canonicalId));
    return iterator != m_entryIndexByCanonicalId.end() ? &m_entries[iterator->second] : nullptr;
}

const std::vector<Mm9SkillTrainerService> &Mm9SkillTrainerTable::entries() const
{
    return m_entries;
}

const std::vector<std::string> &Mm9SkillTrainerTable::errors() const
{
    return m_errors;
}

void Mm9SkillTrainerTable::addError(size_t rowNumber, const std::string &message)
{
    m_errors.push_back("row " + std::to_string(rowNumber) + ": " + message);
}

bool buildMm9JournalTeachers(const std::vector<std::vector<std::string>> &places,
    const Mm9SkillTrainerTable &lessons, const Mm9RudeDialogueTable &dialogue, const MapStats &maps,
    const std::string &mapCatalog, std::vector<TrainerEntry> &entries, std::string &error)
{
    entries.clear();
    error.clear();
    std::unordered_map<std::string, MapPresentation> presentations;
    std::set<std::pair<uint32_t, std::string>> seen;
    try
    {
        for (const auto &row : places)
        {
            if (row.empty() || row[0] == "RudeId")
                continue;
            uint32_t rudeId = 0;
            if (row.size() != 6 || row[1].empty() || !parseUnsigned(row[0], rudeId) || !dialogue.hasDialogue(rudeId))
                throw std::runtime_error("invalid actor teacher identity");
            const MapStatsEntry *map = maps.findByFileName(row[2]);
            if (map == nullptr || map->mergedContinentId != 5 || !seen.emplace(rudeId, row[2]).second)
                throw std::runtime_error("invalid or duplicate actor teacher map");
            const auto coordinate = [](const std::string &value)
            {
                size_t used = 0;
                const float result = std::stof(value, &used);
                if (used != value.size() || !std::isfinite(result))
                    throw std::runtime_error("invalid actor teacher coordinate");
                return result;
            };
            TrainerEntry base;
            base.rudeId = rudeId;
            base.npcId = 90000 + rudeId;
            base.dialogueRowCount = dialogue.rows(rudeId).size();
            base.name = row[1];
            base.mapFileName = map->fileName;
            base.mapId = map->id;
            base.mapName = map->name;
            base.markerMapName = map->name;
            base.continent = 5;
            base.z = coordinate(row[5]);
            base.place = TrainerPlace{0, map->fileName, TrainerPlaceKind::Door, map->fileName,
                coordinate(row[3]), coordinate(row[4])};
            auto presentation = presentations.find(map->fileName);
            if (presentation == presentations.end())
            {
                const auto loaded = loadMapPresentationFromCatalog(mapCatalog, map->fileName, error);
                if (!loaded || !error.empty() || loaded->variants.empty())
                    throw std::runtime_error("missing painted map for " + map->fileName + ": " + error);
                presentation = presentations.emplace(map->fileName, *loaded).first;
            }
            base.mapPresentation = presentation->second;
            const auto add = [&](const std::string &skill, SkillMastery mastery, uint32_t rank, uint32_t gold)
            {
                TrainerEntry entry = base;
                entry.skill = canonicalSkillName(skill);
                const auto id = skillIdForSkillName(skill);
                if (!id)
                    throw std::runtime_error("unknown actor teacher skill " + skill);
                entry.skillId = *id;
                entry.mastery = mastery;
                entry.requiredSkill = rank;
                entry.requiredGold = gold;
                entries.push_back(std::move(entry));
            };
            for (const auto &lesson : lessons.entries())
                if (lesson.rudeId == rudeId)
                    for (const auto &skill : lesson.topic.skillNames)
                        add(skill, lesson.topic.targetMastery, lesson.requiredSkillRank, lesson.requiredGold);
            if (const auto *racial = dialogue.racialTrainer(rudeId))
                for (const auto &skill : dialogue.racialAbilitySkills())
                    for (int mastery = int(SkillMastery::Expert); mastery <= int(racial->maxMastery); ++mastery)
                        add(skill, SkillMastery(mastery), 0, 0);
        }
        for (const auto &lesson : lessons.entries())
            if (std::none_of(entries.begin(), entries.end(), [&](const auto &entry) { return entry.rudeId == lesson.rudeId; }))
                throw std::runtime_error("missing actor teacher " + std::to_string(lesson.rudeId));
    }
    catch (const std::exception &exception)
    {
        entries.clear();
        error = exception.what();
        return false;
    }
    return true;
}

}
