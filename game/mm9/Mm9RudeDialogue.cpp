#include "game/mm9/Mm9RudeDialogue.h"

#include "engine/AssetFileSystem.h"
#include "game/events/EventRuntime.h"
#include "game/party/Party.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cctype>
#include <filesystem>

#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Game
{
namespace
{
struct CsvRecord
{
    size_t sourceLine = 0;
    std::vector<std::string> columns;
};

bool parseInt32(const std::string &text, int32_t &value)
{
    const char *pBegin = text.data();
    const char *pEnd = pBegin + text.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, value);
    return result.ec == std::errc() && result.ptr == pEnd;
}

bool parseUint32(const std::string &text, uint32_t &value)
{
    const char *pBegin = text.data();
    const char *pEnd = pBegin + text.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, value);
    return result.ec == std::errc() && result.ptr == pEnd;
}

std::vector<CsvRecord> parseCsvRecords(const std::string &text, std::string &error)
{
    std::vector<CsvRecord> records;
    CsvRecord record = {.sourceLine = 1};
    std::string field;
    bool quoted = false;
    size_t line = 1;

    for (size_t index = 0; index < text.size(); ++index)
    {
        const char character = text[index];

        if (quoted)
        {
            if (character == '"')
            {
                if (index + 1 < text.size() && text[index + 1] == '"')
                {
                    field.push_back('"');
                    ++index;
                }
                else
                {
                    quoted = false;
                }
            }
            else
            {
                field.push_back(character);
                line += character == '\n' ? 1 : 0;
            }
            continue;
        }

        if (character == '"' && field.empty())
        {
            quoted = true;
        }
        else if (character == ',')
        {
            record.columns.push_back(std::move(field));
            field.clear();
        }
        else if (character == '\r' || character == '\n')
        {
            record.columns.push_back(std::move(field));
            field.clear();

            if (!record.columns.empty()
                && !(record.columns.size() == 1 && record.columns.front().empty()))
            {
                records.push_back(std::move(record));
            }

            if (character == '\r' && index + 1 < text.size() && text[index + 1] == '\n')
            {
                ++index;
            }

            ++line;
            record = {.sourceLine = line};
        }
        else
        {
            field.push_back(character);
        }
    }

    if (quoted)
    {
        error = "unterminated quoted CSV field";
        return {};
    }

    if (!field.empty() || !record.columns.empty())
    {
        record.columns.push_back(std::move(field));
        records.push_back(std::move(record));
    }

    return records;
}

bool isNpcDialogueFileName(const std::string &fileName)
{
    const std::filesystem::path path(fileName);
    const std::string stem = path.stem().string();

    if (path.extension() != ".rude" || stem.size() <= 3 || stem.substr(0, 3) != "NPC")
    {
        return false;
    }

    return std::all_of(
        stem.begin() + 3,
        stem.end(),
        [](unsigned char character)
        {
            return std::isdigit(character) != 0;
        });
}

}

std::optional<uint32_t> mm9QBitForRawQuestKey(int32_t rawKeyId)
{
    if (rawKeyId <= 0 || rawKeyId > Mm9QuestKeyRawIdMaximum)
    {
        return std::nullopt;
    }

    return Mm9QuestKeyQBitBegin + static_cast<uint32_t>(rawKeyId);
}

std::optional<int32_t> mm9RawQuestKeyForQBit(uint32_t qbitId)
{
    if (qbitId <= Mm9QuestKeyQBitBegin || qbitId > Mm9QuestKeyQBitEnd)
    {
        return std::nullopt;
    }

    return static_cast<int32_t>(qbitId - Mm9QuestKeyQBitBegin);
}

std::optional<uint16_t> mm9RudeExitEventIdForSourceObject(uint32_t sourceObjectIndex)
{
    const uint32_t eventId = Mm9RudeExitEventIdBegin + sourceObjectIndex;
    if (eventId > Mm9RudeExitEventIdEnd)
    {
        return std::nullopt;
    }

    return static_cast<uint16_t>(eventId);
}

namespace
{
std::optional<uint16_t> mm9RudeObjectEventId(
    uint32_t sourceObjectIndex,
    uint32_t eventIdBegin,
    uint32_t eventIdEnd)
{
    const uint32_t eventId = eventIdBegin + sourceObjectIndex;
    if (eventId > eventIdEnd)
    {
        return std::nullopt;
    }

    return static_cast<uint16_t>(eventId);
}
}

std::optional<uint16_t> mm9RudeUseEventIdForSourceObject(uint32_t sourceObjectIndex)
{
    return mm9RudeObjectEventId(sourceObjectIndex, Mm9RudeUseEventIdBegin, Mm9RudeUseEventIdEnd);
}

std::optional<uint16_t> mm9RudeFoundPlayerEventIdForSourceObject(uint32_t sourceObjectIndex)
{
    return mm9RudeObjectEventId(
        sourceObjectIndex,
        Mm9RudeFoundPlayerEventIdBegin,
        Mm9RudeFoundPlayerEventIdEnd);
}

bool Mm9RudeDialogueTable::load(const Engine::AssetFileSystem &assetFileSystem, const std::string &packageRoot)
{
    clear();
    const std::string directory = packageRoot + "dialogue/rude";
    std::vector<std::string> entries = assetFileSystem.enumerate(directory);
    std::sort(entries.begin(), entries.end());

    for (const std::string &entry : entries)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(directory + "/" + entry);
        if (!text)
        {
            addError(entry, 0, "could not read file");
            continue;
        }

        if (entry == "NPCNAME.rude")
        {
            loadNpcNamesText(entry, *text);
        }
        else if (entry == "TOPBLURB.rude")
        {
            loadTopBlurbsText(entry, *text);
        }
        else if (isNpcDialogueFileName(entry))
        {
            loadDialogueText(entry, *text);
        }
    }

    const std::string promotionsPath = packageRoot + "dialogue/promotions.yml";
    if (const std::optional<std::string> promotions = assetFileSystem.readTextFile(promotionsPath))
    {
        loadPromotionsText(promotionsPath, *promotions);
    }

    const std::string lostItemsPath = packageRoot + "dialogue/lost_items.yml";
    if (const std::optional<std::string> lostItems = assetFileSystem.readTextFile(lostItemsPath))
    {
        loadLostItemsText(lostItemsPath, *lostItems);
    }

    const std::string racialTrainersPath = packageRoot + "dialogue/racial_trainers.yml";
    if (const std::optional<std::string> racialTrainers = assetFileSystem.readTextFile(racialTrainersPath))
    {
        loadRacialTrainersText(racialTrainersPath, *racialTrainers);
    }

    return !m_rowsByRudeId.empty() && m_errors.empty();
}

bool Mm9RudeDialogueTable::loadPromotionsText(const std::string &sourceName, const std::string &text)
{
    YAML::Node root;
    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        addError(sourceName, 0, exception.what());
        return false;
    }

    if (!root.IsMap() || root["format_version"].as<int>(0) != 1)
    {
        addError(sourceName, 0, "expected format_version 1");
        return false;
    }

    bool valid = true;
    const auto fail = [&](const YAML::Node &node, const std::string &message)
    {
        addError(sourceName, size_t(node.Mark().line + 1), message);
        valid = false;
    };

    for (const YAML::Node &node : root["promotions"])
    {
        Mm9PromotionService service = {};
        service.promotion = node["promotion"].as<std::string>("");
        service.rudeId = node["rude"].as<uint32_t>(0);
        service.doneRawKey = node["done_key"].as<int32_t>(0);
        if (service.promotion.empty() || !hasDialogue(service.rudeId) || !mm9QBitForRawQuestKey(service.doneRawKey))
        {
            fail(node, "a promotion needs a name, a RUDE id with dialogue and a done key in 1-9999");
        }
        else if (!m_promotionServices.emplace(service.rudeId, service).second)
        {
            fail(node, "RUDE " + std::to_string(service.rudeId) + " has two promotions");
        }
    }

    // Rows MM9's dialogue lacks, in its own CSV form, after the original rows (whose indices stay).
    for (const YAML::Node &node : root["added_rows"])
    {
        const std::string row = node.as<std::string>("");
        if (row.empty() || !loadDialogueText(sourceName, row + "\n"))
        {
            fail(node, "an added row must be one valid RUDE row");
        }
    }

    for (const YAML::Node &node : root["waived_required_keys"])
    {
        const uint32_t rudeId = node["rude"].as<uint32_t>(0);
        const int32_t rawKeyId = node["key"].as<int32_t>(0);
        size_t waived = 0;
        const auto iterator = m_rowsByRudeId.find(rudeId);
        if (iterator != m_rowsByRudeId.end())
        {
            for (Mm9RudeRow &row : iterator->second)
            {
                waived += std::erase(row.requiredRawKeys, rawKeyId);
            }
        }
        if (waived == 0)
        {
            fail(node, "RUDE " + std::to_string(rudeId) + " has no row that requires key " + std::to_string(rawKeyId));
        }
    }

    return valid;
}

bool Mm9RudeDialogueTable::loadLostItemsText(const std::string &sourceName, const std::string &text)
{
    YAML::Node root;
    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        addError(sourceName, 0, exception.what());
        return false;
    }

    if (!root.IsMap() || root["format_version"].as<int>(0) != 1)
    {
        addError(sourceName, 0, "expected format_version 1");
        return false;
    }

    bool valid = true;
    for (const YAML::Node &node : root["keepers"])
    {
        const uint32_t rudeId = node.as<uint32_t>(0);
        if (!hasDialogue(rudeId))
        {
            addError(sourceName, size_t(node.Mark().line + 1), "a keeper needs a RUDE id with dialogue");
            valid = false;
            continue;
        }
        m_lostItemKeepers.push_back(rudeId);
    }

    for (const YAML::Node &node : root["items"])
    {
        Mm9LostItem item = {};
        item.rawItemId = node["raw"].as<int32_t>(0);
        item.itemId = node["item_id"].as<uint32_t>(0);
        if (item.rawItemId <= 0 || item.itemId == 0)
        {
            addError(sourceName, size_t(node.Mark().line + 1), "an item needs its raw MM9 id and its item_id");
            valid = false;
            continue;
        }
        m_lostItems.push_back(item);
    }

    return valid;
}

bool Mm9RudeDialogueTable::loadRacialTrainersText(const std::string &sourceName, const std::string &text)
{
    YAML::Node root;
    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        addError(sourceName, 0, exception.what());
        return false;
    }

    if (!root.IsMap() || root["format_version"].as<int>(0) != 1)
    {
        addError(sourceName, 0, "expected format_version 1");
        return false;
    }

    bool valid = true;
    const auto fail = [&](const YAML::Node &node, const std::string &message)
    {
        addError(sourceName, size_t(node.Mark().line + 1), message);
        valid = false;
    };

    for (const YAML::Node &node : root["skills"])
    {
        const std::string skillName = node.as<std::string>("");
        if (canonicalSkillName(skillName) != skillName || !skillIdForSkillName(skillName)
            || std::find(m_racialAbilitySkills.begin(), m_racialAbilitySkills.end(), skillName)
                != m_racialAbilitySkills.end())
        {
            fail(node, "racial ability '" + skillName + "' must be a distinct canonical skill");
            continue;
        }
        m_racialAbilitySkills.push_back(skillName);
    }

    for (const YAML::Node &node : root["trainers"])
    {
        Mm9RacialTrainer trainer = {};
        trainer.rudeId = node["rude"].as<uint32_t>(0);
        const std::string mastery = node["mastery"].as<std::string>("");
        trainer.maxMastery = mastery == "Expert" ? SkillMastery::Expert
            : mastery == "Master" ? SkillMastery::Master
            : mastery == "Grandmaster" ? SkillMastery::Grandmaster
            : SkillMastery::None;
        if (!hasDialogue(trainer.rudeId) || trainer.maxMastery == SkillMastery::None)
        {
            fail(node, "a racial trainer needs a RUDE id with dialogue and a mastery of Expert, Master or Grandmaster");
        }
        else if (!m_racialTrainers.emplace(trainer.rudeId, trainer).second)
        {
            fail(node, "RUDE " + std::to_string(trainer.rudeId) + " is listed twice");
        }
    }

    if (!m_racialTrainers.empty() && m_racialAbilitySkills.empty())
    {
        addError(sourceName, 0, "racial trainers need the racial abilities they teach");
        valid = false;
    }

    return valid;
}

bool Mm9RudeDialogueTable::loadDialogueText(const std::string &sourceName, const std::string &text)
{
    std::string csvError;
    const std::vector<CsvRecord> records = parseCsvRecords(text, csvError);
    if (!csvError.empty())
    {
        addError(sourceName, 0, csvError);
        return false;
    }

    bool valid = true;
    constexpr std::array<size_t, 5> RequiredKeyColumns = {6, 8, 10, 12, 14};
    constexpr std::array<size_t, 5> GrantedKeyColumns = {15, 16, 17, 18, 19};
    constexpr std::array<size_t, 5> ForbiddenKeyColumns = {20, 21, 22, 23, 24};
    constexpr std::array<size_t, 5> RemovedKeyColumns = {25, 26, 27, 28, 29};

    for (const CsvRecord &record : records)
    {
        if (record.columns.size() < 30)
        {
            addError(sourceName, record.sourceLine, "expected at least 30 columns");
            valid = false;
            continue;
        }

        Mm9RudeRow row = {};
        if (!parseInt32(record.columns[0], row.rudeId)
            || !parseInt32(record.columns[1], row.nodeId)
            || !parseInt32(record.columns[2], row.choiceSlot)
            || !parseInt32(record.columns[5], row.next)
            || row.rudeId <= 0)
        {
            addError(sourceName, record.sourceLine, "invalid RUDE row identity or action");
            valid = false;
            continue;
        }

        row.sourceLine = record.sourceLine;
        row.prompt = record.columns[3];
        row.response = record.columns[4];
        row.rawColumns = record.columns;
        bool keysValid = true;

        const auto parseQuestKeyGroup = [&](const std::array<size_t, 5> &columns, std::vector<int32_t> &keys)
        {
            for (size_t column : columns)
            {
                int32_t rawKeyId = 0;
                if (!parseInt32(record.columns[column], rawKeyId))
                {
                    addError(sourceName, record.sourceLine, "invalid key in column " + std::to_string(column + 1));
                    keysValid = false;
                }
                else if (rawKeyId != 0)
                {
                    if (!mm9QBitForRawQuestKey(rawKeyId))
                    {
                        addError(
                            sourceName,
                            record.sourceLine,
                            "quest key in column " + std::to_string(column + 1)
                                + " is outside raw range 1-9999");
                        keysValid = false;
                    }
                    else
                    {
                        keys.push_back(rawKeyId);
                    }
                }
            }
        };

        const auto validateNumericGroup = [&](const std::array<size_t, 5> &columns)
        {
            for (size_t column : columns)
            {
                int32_t value = 0;
                if (!parseInt32(record.columns[column], value))
                {
                    addError(
                        sourceName,
                        record.sourceLine,
                        "invalid numeric value in column " + std::to_string(column + 1));
                    keysValid = false;
                }
            }
        };

        parseQuestKeyGroup(RequiredKeyColumns, row.requiredRawKeys);
        parseQuestKeyGroup(ForbiddenKeyColumns, row.forbiddenRawKeys);

        if (mm9RudeRowAppliesQuestKeys(row))
        {
            parseQuestKeyGroup(GrantedKeyColumns, row.grantedRawKeys);
            parseQuestKeyGroup(RemovedKeyColumns, row.removedRawKeys);
        }
        else
        {
            validateNumericGroup(GrantedKeyColumns);
            validateNumericGroup(RemovedKeyColumns);
        }

        if (!keysValid)
        {
            valid = false;
            continue;
        }

        std::vector<Mm9RudeRow> &dialogueRows = m_rowsByRudeId[static_cast<uint32_t>(row.rudeId)];
        row.rowIndex = dialogueRows.size();
        dialogueRows.push_back(std::move(row));
    }

    return valid;
}

bool Mm9RudeDialogueTable::loadNpcNamesText(const std::string &sourceName, const std::string &text)
{
    std::string csvError;
    const std::vector<CsvRecord> records = parseCsvRecords(text, csvError);
    if (!csvError.empty())
    {
        addError(sourceName, 0, csvError);
        return false;
    }

    bool valid = true;
    for (const CsvRecord &record : records)
    {
        uint32_t rudeId = 0;
        if (record.columns.size() < 2 || !parseUint32(record.columns[0], rudeId) || rudeId == 0)
        {
            addError(sourceName, record.sourceLine, "invalid NPC name row");
            valid = false;
            continue;
        }
        m_npcNames[rudeId] = record.columns[1];
    }
    return valid;
}

bool Mm9RudeDialogueTable::loadTopBlurbsText(const std::string &sourceName, const std::string &text)
{
    std::string csvError;
    const std::vector<CsvRecord> records = parseCsvRecords(text, csvError);
    if (!csvError.empty())
    {
        addError(sourceName, 0, csvError);
        return false;
    }

    bool valid = true;
    for (const CsvRecord &record : records)
    {
        uint32_t rudeId = 0;
        if (record.columns.size() < 3 || !parseUint32(record.columns[0], rudeId) || rudeId == 0)
        {
            addError(sourceName, record.sourceLine, "invalid top-blurb row");
            valid = false;
            continue;
        }
        m_topBlurbs[rudeId] = record.columns[2];
    }
    return valid;
}

void Mm9RudeDialogueTable::clear()
{
    m_rowsByRudeId.clear();
    m_npcNames.clear();
    m_topBlurbs.clear();
    m_promotionServices.clear();
    m_lostItemKeepers.clear();
    m_lostItems.clear();
    m_racialTrainers.clear();
    m_racialAbilitySkills.clear();
    m_rulesetRows.clear();
    m_errors.clear();
}

void Mm9RudeDialogueTable::clearRulesetRows()
{
    m_rulesetRows.clear();
}

bool Mm9RudeDialogueTable::loadRulesetRowsText(const std::string &sourceName, const std::string &text)
{
    m_rulesetRows.clear();
    YAML::Node root;
    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        addError(sourceName, 0, exception.what());
        return false;
    }

    if (!root.IsMap() || root["format_version"].as<int>(0) != 1)
    {
        addError(sourceName, 0, "expected format_version 1");
        return false;
    }

    bool valid = true;
    const auto addRow = [&](const YAML::Node &node, bool bounty)
    {
        Mm9RulesetRow row = {};
        row.rudeId = node["npc"].as<uint32_t>(0);
        if (bounty)
        {
            row.bountyMapFileName = node["map"].as<std::string>("");
        }
        else
        {
            row.eventId = node["event"].as<uint16_t>(0);
            row.label = node["label"].as<std::string>("");
        }

        if (!hasDialogue(row.rudeId) || (bounty ? row.bountyMapFileName.empty() : row.eventId == 0 || row.label.empty()))
        {
            addError(sourceName, size_t(node.Mark().line + 1),
                bounty ? "a bounty needs a RUDE id with dialogue and its map"
                       : "a topic needs a RUDE id with dialogue, its event and its label");
            valid = false;
            return;
        }

        m_rulesetRows.push_back(std::move(row));
    };

    for (const YAML::Node &node : root["topics"])
    {
        addRow(node, false);
    }

    for (const YAML::Node &node : root["bounties"])
    {
        addRow(node, true);
    }

    return valid;
}

std::vector<const Mm9RulesetRow *> Mm9RudeDialogueTable::rulesetRows(uint32_t rudeId) const
{
    std::vector<const Mm9RulesetRow *> rows;
    for (const Mm9RulesetRow &row : m_rulesetRows)
    {
        if (row.rudeId == rudeId)
        {
            rows.push_back(&row);
        }
    }
    return rows;
}

bool Mm9RudeDialogueTable::empty() const
{
    return m_rowsByRudeId.empty();
}

bool Mm9RudeDialogueTable::hasDialogue(uint32_t rudeId) const
{
    const auto iterator = m_rowsByRudeId.find(rudeId);
    if (iterator == m_rowsByRudeId.end())
    {
        return false;
    }

    return std::any_of(
        iterator->second.begin(),
        iterator->second.end(),
        [rudeId](const Mm9RudeRow &row)
        {
            return row.nodeId == static_cast<int32_t>(rudeId);
        });
}

std::string Mm9RudeDialogueTable::npcName(uint32_t rudeId) const
{
    const auto iterator = m_npcNames.find(rudeId);
    return iterator != m_npcNames.end() ? iterator->second : std::string();
}

std::string Mm9RudeDialogueTable::topBlurb(uint32_t rudeId) const
{
    const auto iterator = m_topBlurbs.find(rudeId);
    return iterator != m_topBlurbs.end() ? iterator->second : std::string();
}

std::vector<const Mm9RudeRow *> Mm9RudeDialogueTable::visibleRows(
    uint32_t rudeId,
    int32_t nodeId,
    const Party &party) const
{
    std::vector<const Mm9RudeRow *> rows;
    const auto iterator = m_rowsByRudeId.find(rudeId);
    if (iterator == m_rowsByRudeId.end())
    {
        return rows;
    }

    for (const Mm9RudeRow &row : iterator->second)
    {
        if (row.nodeId == nodeId
            && mm9RudeRowPassesQuestKeys(
                row,
                [&party](uint32_t qbitId)
                {
                    return party.hasQuestBit(qbitId);
                }))
        {
            rows.push_back(&row);
        }
    }

    std::sort(
        rows.begin(),
        rows.end(),
        [](const Mm9RudeRow *pLeft, const Mm9RudeRow *pRight)
        {
            if (pLeft->choiceSlot != pRight->choiceSlot)
            {
                return pLeft->choiceSlot < pRight->choiceSlot;
            }
            return pLeft->sourceLine < pRight->sourceLine;
        });
    return rows;
}

const std::vector<Mm9RudeRow> &Mm9RudeDialogueTable::rows(uint32_t rudeId) const
{
    static const std::vector<Mm9RudeRow> EmptyRows;
    const auto iterator = m_rowsByRudeId.find(rudeId);
    return iterator != m_rowsByRudeId.end() ? iterator->second : EmptyRows;
}

const Mm9RudeRow *Mm9RudeDialogueTable::rowByIndex(uint32_t rudeId, size_t rowIndex) const
{
    const auto iterator = m_rowsByRudeId.find(rudeId);
    return iterator != m_rowsByRudeId.end() && rowIndex < iterator->second.size()
        ? &iterator->second[rowIndex]
        : nullptr;
}

bool Mm9RudeDialogueTable::isLostItemKeeper(uint32_t rudeId) const
{
    return std::find(m_lostItemKeepers.begin(), m_lostItemKeepers.end(), rudeId) != m_lostItemKeepers.end();
}

const std::vector<Mm9LostItem> &Mm9RudeDialogueTable::lostItems() const
{
    return m_lostItems;
}

const Mm9RacialTrainer *Mm9RudeDialogueTable::racialTrainer(uint32_t rudeId) const
{
    const auto iterator = m_racialTrainers.find(rudeId);
    return iterator != m_racialTrainers.end() ? &iterator->second : nullptr;
}

const std::vector<std::string> &Mm9RudeDialogueTable::racialAbilitySkills() const
{
    return m_racialAbilitySkills;
}

const Mm9PromotionService *Mm9RudeDialogueTable::promotionService(uint32_t rudeId) const
{
    const auto iterator = m_promotionServices.find(rudeId);
    return iterator != m_promotionServices.end() ? &iterator->second : nullptr;
}

const std::vector<std::string> &Mm9RudeDialogueTable::errors() const
{
    return m_errors;
}

void Mm9RudeDialogueTable::addError(
    const std::string &sourceName,
    size_t sourceLine,
    const std::string &message)
{
    m_errors.push_back(sourceName + (sourceLine != 0 ? ":" + std::to_string(sourceLine) : std::string())
        + ": " + message);
}

Mm9RudeSelection selectMm9RudeRow(const Mm9RudeRow &row)
{
    Mm9RudeSelection selection = {};
    selection.next = row.next;
    selection.response = row.response == "blank" ? std::string() : row.response;

    if (row.next >= 0)
    {
        selection.kind = Mm9RudeSelectionKind::GotoNode;
    }
    else if (row.next == -1 || row.next == -14)
    {
        selection.kind = Mm9RudeSelectionKind::Close;
    }
    else if (row.next < -1)
    {
        selection.kind = Mm9RudeSelectionKind::Service;
        selection.serviceOpcode = row.next;
    }
    else
    {
        selection.kind = Mm9RudeSelectionKind::Unresolved;
    }

    return selection;
}

bool mm9RudeRowPassesQuestKeys(
    const Mm9RudeRow &row,
    const std::function<bool(uint32_t)> &hasQBit)
{
    for (int32_t rawKeyId : row.requiredRawKeys)
    {
        const std::optional<uint32_t> qbitId = mm9QBitForRawQuestKey(rawKeyId);
        if (!qbitId || !hasQBit(*qbitId))
        {
            return false;
        }
    }

    for (int32_t rawKeyId : row.forbiddenRawKeys)
    {
        const std::optional<uint32_t> qbitId = mm9QBitForRawQuestKey(rawKeyId);
        if (qbitId && hasQBit(*qbitId))
        {
            return false;
        }
    }

    return true;
}

bool mm9RudeRowAppliesQuestKeys(const Mm9RudeRow &row)
{
    return row.next >= -1 || row.next == -10 || row.next == -11;
}

void applyMm9RudeRowActions(
    const Mm9RudeRow &row,
    Party &party,
    EventRuntimeState *pEventRuntimeState)
{
    if (!mm9RudeRowAppliesQuestKeys(row))
    {
        return;
    }

    for (int32_t rawKeyId : row.grantedRawKeys)
    {
        const std::optional<uint32_t> qbitId = mm9QBitForRawQuestKey(rawKeyId);
        if (qbitId)
        {
            if (pEventRuntimeState != nullptr)
            {
                EventRuntime::setQuestBitValue(*pEventRuntimeState, party, *qbitId, true);
            }
            else
            {
                party.setQuestBit(*qbitId, true);
            }
        }
    }

    for (int32_t rawKeyId : row.removedRawKeys)
    {
        const std::optional<uint32_t> qbitId = mm9QBitForRawQuestKey(rawKeyId);
        if (qbitId)
        {
            if (pEventRuntimeState != nullptr)
            {
                EventRuntime::setQuestBitValue(*pEventRuntimeState, party, *qbitId, false);
            }
            else
            {
                party.setQuestBit(*qbitId, false);
            }
        }
    }
}

std::string mm9RudeServiceName(int32_t opcode)
{
    switch (opcode)
    {
        case -2: return "shop";
        case -3: return "training";
        case -4: return "skill training";
        case -5: return "travel";
        case -6: return "bank";
        case -7: return "inn";
        case -8: return "healer";
        case -10: return "hire";
        case -11: return "dismiss";
        case -13: return "item combine";
        case -14: return "quest handoff";
        case -15: return "hireling service";
        case -16: return "donation";
        default: return "unknown service";
    }
}
}
