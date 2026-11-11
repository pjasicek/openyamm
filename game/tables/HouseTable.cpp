#include "game/tables/HouseTable.h"

#include "game/party/SkillData.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/ItemTable.h"
#include "game/items/ItemEnchantTables.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <iostream>
#include <optional>
#include <sstream>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MergedYawUnitsPerTurn = 2048;
constexpr int DegreesPerTurn = 360;

bool isNumericOnly(const std::string &value)
{
    return !value.empty()
        && std::all_of(
            value.begin(),
            value.end(),
            [](unsigned char character)
            {
                return std::isdigit(character) != 0;
            });
}

std::string normalizeVideoStem(const std::string &value)
{
    return isNumericOnly(value) ? "" : value;
}

std::unordered_map<uint32_t, std::string> movieStemsByAnimationIdFromRows(
    const std::vector<std::vector<std::string>> &rows)
{
    std::unordered_map<uint32_t, std::string> result;

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1 || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        const std::string normalizedVideoStem = normalizeVideoStem(row[1]);

        if (!normalizedVideoStem.empty())
        {
            result[static_cast<uint32_t>(parsedId)] = normalizedVideoStem;
        }
    }

    return result;
}

uint32_t parseUnsigned(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    return static_cast<uint32_t>(std::strtoul(value.c_str(), nullptr, 10));
}

int parseSigned(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    return std::atoi(value.c_str());
}

std::string vendorAliasKey(const std::string &packageId, uint32_t sourceVendorId)
{
    return packageId + ":" + std::to_string(sourceVendorId);
}

std::string serviceAliasKey(const std::string &packageId, uint32_t sourceServiceId)
{
    return packageId + ":" + std::to_string(sourceServiceId);
}

std::optional<size_t> standardEnchantSlotIndex(const std::string &equipStat)
{
    static const std::array<std::string, 9> EquipStats = {
        "Armor", "Shield", "Helm", "Belt", "Cloak", "Gauntlets", "Boots", "Ring", "Amulet"};
    const auto statIt = std::find(EquipStats.begin(), EquipStats.end(), equipStat);
    if (statIt == EquipStats.end())
    {
        return std::nullopt;
    }
    return static_cast<size_t>(std::distance(EquipStats.begin(), statIt));
}

std::optional<size_t> specialEnchantSlotIndex(const std::string &equipStat)
{
    static const std::array<std::string, 12> EquipStats = {
        "Weapon", "Weapon2", "Missile", "Armor", "Shield", "Helm",
        "Belt", "Cloak", "Gauntlets", "Boots", "Ring", "Amulet"};
    const std::string normalizedEquipStat = equipStat == "Weapon1or2" ? "Weapon" : equipStat;
    const auto statIt = std::find(EquipStats.begin(), EquipStats.end(), normalizedEquipStat);
    if (statIt == EquipStats.end())
    {
        return std::nullopt;
    }
    return static_cast<size_t>(std::distance(EquipStats.begin(), statIt));
}

// A ledger page's sanity limit: MM9 restocks with 15 rolls per range, and its biggest spellbook shop (Rober's Magic,
// Lindisfarne) stocks 74 books.
constexpr size_t MaxLedgerStockPageSlots = 128;

size_t expectedVendorStockSlotCount(VendorStockProfile profile)
{
    switch (profile)
    {
        case VendorStockProfile::Weapon:
            return 6;

        case VendorStockProfile::Armor:
        case VendorStockProfile::Mm9GeneralStore:
            return 8;

        case VendorStockProfile::Spellbook:
        case VendorStockProfile::Mm9Apothecary:
        case VendorStockProfile::Mm9Library:
            return 12;

        case VendorStockProfile::None:
            return 0;
    }
    return 0;
}

VendorStockProfile parseVendorStockProfile(const std::string &value)
{
    if (value == "Weapon")
    {
        return VendorStockProfile::Weapon;
    }
    if (value == "Armor")
    {
        return VendorStockProfile::Armor;
    }
    if (value == "Spellbook")
    {
        return VendorStockProfile::Spellbook;
    }
    if (value == "Mm9Apothecary")
    {
        return VendorStockProfile::Mm9Apothecary;
    }
    if (value == "Mm9GeneralStore")
    {
        return VendorStockProfile::Mm9GeneralStore;
    }
    if (value == "Mm9Library")
    {
        return VendorStockProfile::Mm9Library;
    }
    return VendorStockProfile::None;
}

bool parseBool(const std::string &value)
{
    return value == "1" || value == "true" || value == "True";
}

// A world venue's learn_skills cell: canonical OpenYAMM skill names separated by '|', each once; false on any other.
bool parseLearnSkills(const std::string &value, std::vector<std::string> &skills)
{
    skills.clear();
    std::stringstream stream(value);
    std::string token;

    while (std::getline(stream, token, '|'))
    {
        if (!skillIdForSkillName(token) || canonicalSkillName(token) != token
            || std::find(skills.begin(), skills.end(), token) != skills.end())
        {
            return false;
        }

        skills.push_back(token);
    }

    return true;
}

HouseEntry::DeterministicStockPage *findOrAddStockPage(
    std::vector<HouseEntry::DeterministicStockPage> &pages,
    uint32_t pageIndex)
{
    const std::vector<HouseEntry::DeterministicStockPage>::iterator pageIt = std::find_if(
        pages.begin(),
        pages.end(),
        [pageIndex](const HouseEntry::DeterministicStockPage &page)
        {
            return page.pageIndex == pageIndex;
        });
    if (pageIt != pages.end())
    {
        return &*pageIt;
    }

    pages.push_back({.pageIndex = pageIndex});
    return &pages.back();
}

// MM6's temple heal check (MM6.exe 0x49DAD0) restricts by house, not by table data: only Temple Stone in Free Haven
// cures eradication, Temple Baa cannot treat death, petrification or eradication, and every other MM6 temple
// treats everything except eradication. Tiers match templeConditionHealingTier; 0 means unrestricted.
float mm6TempleHealingTier(uint32_t houseId)
{
    constexpr uint32_t NewSorpigalTempleHouseId = 325;
    constexpr uint32_t TempleStoneHouseId = 326;
    constexpr uint32_t TempleBaaHouseId = 334;

    if (houseId == TempleStoneHouseId)
    {
        return 0.0f;
    }

    if (houseId == TempleBaaHouseId)
    {
        return 1.5f;
    }

    if (houseId >= NewSorpigalTempleHouseId && houseId < TempleBaaHouseId)
    {
        return 2.0f;
    }

    return 0.0f;
}

bool isTransportHouseTypeName(const std::string &houseType)
{
    return houseType == "Stables" || houseType == "Boats";
}

uint32_t houseRuleId(const HouseEntry &entry)
{
    return entry.typeIndex != 0 ? entry.typeIndex : entry.mapId;
}

std::optional<std::pair<std::string, std::string>> stockSectionNamesForHouseType(const std::string &houseType)
{
    if (houseType == "Weapon Shop")
    {
        return std::pair<std::string, std::string>{"Weapon shops Standart", "Weapon shops Special"};
    }

    if (houseType == "Armor Shop")
    {
        return std::pair<std::string, std::string>{"Armor shops Standart", "Armor shops Special"};
    }

    if (houseType == "Magic Shop")
    {
        return std::pair<std::string, std::string>{"Magic shops Standart", "Magic shops Special"};
    }

    if (houseType == "Alchemist")
    {
        return std::pair<std::string, std::string>{"Alchem shops Standart", "Alchem shops Special"};
    }

    return std::nullopt;
}

bool isSpellbookHouseType(const std::string &houseType)
{
    return houseType == "Elemental Guild"
        || houseType == "Light Guild"
        || houseType == "Dark Guild"
        || houseType == "Self Guild"
        || houseType == "Fire Guild"
        || houseType == "Air Guild"
        || houseType == "Water Guild"
        || houseType == "Earth Guild"
        || houseType == "Spirit Guild"
        || houseType == "Mind Guild"
        || houseType == "Body Guild"
        || houseType == "Spell Shop";
}

std::string stemFromMapFileName(const std::string &fileName)
{
    const size_t slashPosition = fileName.find_last_of("/\\");
    const size_t nameStart = slashPosition == std::string::npos ? 0 : slashPosition + 1;
    const size_t dotPosition = fileName.find_last_of('.');

    if (dotPosition == std::string::npos || dotPosition < nameStart)
    {
        return fileName.substr(nameStart);
    }

    return fileName.substr(nameStart, dotPosition - nameStart);
}

std::string normalizedMapFileName(const std::string &fileName)
{
    std::string result = fileName;
    std::transform(
        result.begin(),
        result.end(),
        result.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return result;
}

int directionDegreesFromMergedYawUnits(int32_t yawUnits)
{
    int32_t normalized = yawUnits % MergedYawUnitsPerTurn;

    if (normalized < 0)
    {
        normalized += MergedYawUnitsPerTurn;
    }

    return static_cast<int>((normalized * DegreesPerTurn) / MergedYawUnitsPerTurn);
}

const MergedHouseRuleSection *findHouseRuleSection(
    const MergedHouseRuleTable &houseRules,
    const std::string &sectionName)
{
    for (const MergedHouseRuleSection &section : houseRules.sections())
    {
        if (section.name == sectionName)
        {
            return &section;
        }
    }

    return nullptr;
}

const std::vector<int32_t> *findHouseRuleRow(const MergedHouseRuleSection &section, uint32_t ruleId)
{
    for (const std::vector<int32_t> &row : section.numericRows)
    {
        if (!row.empty() && row[0] == static_cast<int32_t>(ruleId))
        {
            return &row;
        }
    }

    return nullptr;
}

std::vector<uint32_t> itemTypesFromRuleRow(
    const std::vector<int32_t> &row,
    size_t beginColumn,
    size_t endColumn)
{
    std::vector<uint32_t> itemTypes;

    for (size_t columnIndex = beginColumn; columnIndex < endColumn && columnIndex < row.size(); ++columnIndex)
    {
        if (row[columnIndex] > 0)
        {
            itemTypes.push_back(static_cast<uint32_t>(row[columnIndex]));
        }
    }

    return itemTypes;
}

HouseEntry::StockRule stockRuleFromRow(const std::string &houseType, const std::vector<int32_t> &row)
{
    HouseEntry::StockRule rule = {};

    if (row.size() < 2)
    {
        return rule;
    }

    rule.quality = row[1];

    if (houseType == "Armor Shop")
    {
        rule.itemTypes = itemTypesFromRuleRow(row, 2, 6);

        if (row.size() > 6)
        {
            rule.secondaryQuality = row[6];
            rule.secondaryItemTypes = itemTypesFromRuleRow(row, 7, 11);
        }

        return rule;
    }

    rule.itemTypes = itemTypesFromRuleRow(row, 2, row.size());
    return rule;
}

bool applyStockRuleSection(
    HouseEntry &entry,
    const MergedHouseRuleTable &houseRules,
    const std::string &sectionName,
    HouseEntry::StockRule &targetRule)
{
    const MergedHouseRuleSection *pSection = findHouseRuleSection(houseRules, sectionName);

    if (pSection == nullptr)
    {
        std::cerr << "merged house rules are missing stock section: " << sectionName << '\n';
        return false;
    }

    const std::vector<int32_t> *pRow = findHouseRuleRow(*pSection, houseRuleId(entry));

    if (pRow == nullptr)
    {
        return true;
    }

    targetRule = stockRuleFromRow(entry.type, *pRow);
    return true;
}

bool applyShopStockRules(HouseEntry &entry, const MergedHouseRuleTable &houseRules)
{
    const std::optional<std::pair<std::string, std::string>> sectionNames =
        stockSectionNamesForHouseType(entry.type);

    if (!sectionNames.has_value())
    {
        return true;
    }

    if (!applyStockRuleSection(entry, houseRules, sectionNames->first, entry.standardStockRule)
        || !applyStockRuleSection(entry, houseRules, sectionNames->second, entry.specialStockRule))
    {
        return false;
    }

    entry.standardStockTier = entry.standardStockRule.quality;
    entry.specialStockTier = entry.specialStockRule.quality;
    return true;
}

std::optional<std::string> skillForStockItemType(uint32_t itemType)
{
    switch (itemType)
    {
        case 23: return "Sword";
        case 24: return "Dagger";
        case 25: return "Axe";
        case 26: return "Spear";
        case 27: return "Bow";
        case 28: return "Mace";
        case 30: return "Staff";
        case 31: return "LeatherArmor";
        case 32: return "ChainArmor";
        case 33: return "PlateArmor";
        case 34: return "Shield";
        default: return std::nullopt;
    }
}

void appendStockSkills(const std::vector<uint32_t> &itemTypes, std::vector<std::string> &skills)
{
    for (uint32_t itemType : itemTypes)
    {
        const std::optional<std::string> skill = skillForStockItemType(itemType);

        if (skill.has_value() && std::find(skills.begin(), skills.end(), *skill) == skills.end())
        {
            skills.push_back(*skill);
        }
    }
}

std::vector<std::string> deriveOfferedSkillsFromShopStock(const HouseEntry &entry)
{
    std::vector<std::string> skills;
    appendStockSkills(entry.standardStockRule.itemTypes, skills);
    appendStockSkills(entry.standardStockRule.secondaryItemTypes, skills);
    appendStockSkills(entry.specialStockRule.itemTypes, skills);
    appendStockSkills(entry.specialStockRule.secondaryItemTypes, skills);
    return skills;
}

bool applySpellbookRule(HouseEntry &entry, const MergedHouseRuleTable &houseRules)
{
    const MergedHouseRuleSection *pSection = findHouseRuleSection(houseRules, "Spellbook shops");

    if (pSection == nullptr)
    {
        std::cerr << "merged house rules are missing spellbook shop section\n";
        return false;
    }

    const std::vector<int32_t> *pRow = findHouseRuleRow(*pSection, houseRuleId(entry));

    if (pRow == nullptr || pRow->size() < 2)
    {
        return true;
    }

    entry.spellbookStockRule.quality = (*pRow)[1];
    return true;
}

bool applyTrainingRule(HouseEntry &entry, const MergedHouseRuleTable &houseRules)
{
    const MergedHouseRuleSection *pSection = findHouseRuleSection(houseRules, "Training halls");

    if (pSection == nullptr)
    {
        std::cerr << "merged house rules are missing training hall section\n";
        return false;
    }

    const std::vector<int32_t> *pRow = findHouseRuleRow(*pSection, houseRuleId(entry));

    if (pRow == nullptr || pRow->size() < 2)
    {
        return true;
    }

    entry.trainingMaxLevel = (*pRow)[1];
    return true;
}

bool applyArcomageRule(HouseEntry &entry, const MergedHouseRuleTable &houseRules)
{
    const MergedHouseRuleSection *pSection = findHouseRuleSection(houseRules, "Arcomage in taverns");

    if (pSection == nullptr)
    {
        std::cerr << "merged house rules are missing Arcomage tavern section\n";
        return false;
    }

    const std::vector<int32_t> *pRow = findHouseRuleRow(*pSection, houseRuleId(entry));

    if (pRow == nullptr || pRow->size() < 12)
    {
        entry.arcomageRule.reset();
        return true;
    }

    HouseEntry::ArcomageRule rule = {};
    rule.towerToWin = (*pRow)[1];
    rule.resourceToWin = (*pRow)[2];
    rule.towerAtStart = (*pRow)[3];
    rule.wallAtStart = (*pRow)[4];
    rule.quarry = (*pRow)[5];
    rule.magic = (*pRow)[6];
    rule.dungeon = (*pRow)[7];
    rule.bricks = (*pRow)[8];
    rule.gems = (*pRow)[9];
    rule.recruits = (*pRow)[10];
    rule.ai = (*pRow)[11];

    if (pRow->size() > 12 && (*pRow)[12] > 0)
    {
        rule.rulesTextId = static_cast<uint32_t>((*pRow)[12]);
    }

    entry.arcomageRule = rule;
    return true;
}

const MergedTransportLocationEntry *findTransportLocation(
    const MergedTransportLocationTable &transportLocations,
    int32_t locationId)
{
    if (locationId < 0)
    {
        return nullptr;
    }

    for (const MergedTransportLocationEntry &entry : transportLocations.entries())
    {
        if (entry.id == static_cast<uint32_t>(locationId))
        {
            return &entry;
        }
    }

    return nullptr;
}

std::string destinationNameForTransportLocation(
    const MergedTransportLocationEntry &location,
    const MapStats &mapStats)
{
    const MapStatsEntry *pMapStatsEntry = mapStats.findByFileName(location.mapName);

    if (pMapStatsEntry != nullptr && !pMapStatsEntry->name.empty())
    {
        return pMapStatsEntry->name;
    }

    return stemFromMapFileName(location.mapName);
}

std::vector<std::string> deriveOfferedSkillsForHouseType(const std::string &houseType)
{
    if (houseType == "Magic Shop")
    {
        return {"IdentifyItem", "RepairItem"};
    }

    if (houseType == "Alchemist")
    {
        return {"Alchemy", "IdentifyMonster"};
    }

    if (houseType == "Elemental Guild" || houseType == "Spell Shop")
    {
        return {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "Learning"};
    }

    if (houseType == "Fire Guild")
    {
        return {"FireMagic", "Learning"};
    }

    if (houseType == "Air Guild")
    {
        return {"AirMagic", "Learning"};
    }

    if (houseType == "Water Guild")
    {
        return {"WaterMagic", "Learning"};
    }

    if (houseType == "Earth Guild")
    {
        return {"EarthMagic", "Learning"};
    }

    if (houseType == "Self Guild")
    {
        return {"SpiritMagic", "MindMagic", "BodyMagic", "Meditation"};
    }

    if (houseType == "Spirit Guild")
    {
        return {"SpiritMagic", "Meditation"};
    }

    if (houseType == "Mind Guild")
    {
        return {"MindMagic", "Meditation"};
    }

    if (houseType == "Body Guild")
    {
        return {"BodyMagic", "Meditation"};
    }

    if (houseType == "Thieves guild" || houseType == "Thieves Guild")
    {
        return {"Dagger", "Merchant", "IdentifyItem", "Perception", "DisarmTraps"};
    }

    if (houseType == "Merc Guild")
    {
        return {"Unarmed", "Dodging", "Armsmaster", "DisarmTraps"};
    }

    if (houseType == "Light Guild")
    {
        return {"LightMagic"};
    }

    if (houseType == "Dark Guild")
    {
        return {"DarkMagic"};
    }

    if (houseType == "Temple")
    {
        return {"Unarmed", "Dodging", "Regeneration", "Merchant"};
    }

    if (houseType == "Tavern")
    {
        return {"Stealing", "DisarmTraps", "Perception"};
    }

    if (houseType == "Training")
    {
        return {"Armsmaster", "Bodybuilding"};
    }

    return {};
}
}

bool HouseTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_vendorAliases.clear();
    m_serviceAliases.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        const std::string &name = row[5];

        if (name.empty())
        {
            continue;
        }

        HouseEntry entry = {};
        entry.id = static_cast<uint32_t>(parsedId);
        entry.typeIndex = (row.size() > 1 && !row[1].empty()) ? std::strtoul(row[1].c_str(), nullptr, 10) : 0;
        entry.mapId = (row.size() > 3 && !row[3].empty()) ? std::strtoul(row[3].c_str(), nullptr, 10) : 0;
        entry.proprietorPictureId =
            (row.size() > 8 && !row[8].empty()) ? std::strtoul(row[8].c_str(), nullptr, 10) : 0;
        entry.type = row.size() > 2 ? row[2] : "";
        entry.name = name;
        entry.videoName = row.size() > 4 ? normalizeVideoStem(row[4]) : "";
        entry.proprietorName = row.size() > 6 ? row[6] : "";
        entry.proprietorTitle = row.size() > 7 ? row[7] : "";
        entry.priceMultiplier =
            (row.size() > 12 && !row[12].empty()) ? std::strtof(row[12].c_str(), nullptr) : 0.0f;
        entry.skillPriceMultiplier =
            (row.size() > 13 && !row[13].empty()) ? std::strtof(row[13].c_str(), nullptr) : 0.0f;
        entry.templeBehavior = (row.size() > 15 && !row[15].empty()) ? parseSigned(row[15]) : 0;
        if (entry.type == "Temple")
        {
            entry.templeHealingTier = mm6TempleHealingTier(entry.id);
        }
        entry.stockRefreshDays = (row.size() > 15 && !row[15].empty()) ? std::atoi(row[15].c_str()) : 0;
        entry.openHour = (row.size() > 18 && !row[18].empty()) ? std::atoi(row[18].c_str()) : 0;
        entry.closeHour = (row.size() > 19 && !row[19].empty()) ? std::atoi(row[19].c_str()) : 0;
        entry.rawExtraExitPictureIndex = row.size() > 20 ? parseUnsigned(row[20]) : 0;
        entry.rawExtraExitMapId = row.size() > 21 ? parseUnsigned(row[21]) : 0;
        entry.rawExtraExitRestriction = row.size() > 22 ? parseSigned(row[22]) : 0;
        entry.enterText = row.size() > 23 ? row[23] : "";

        if (row.size() > 24 && !row[24].empty())
        {
            std::istringstream stream(row[24]);
            std::string token;

            while (std::getline(stream, token, ','))
            {
                token.erase(
                    std::remove_if(
                        token.begin(),
                        token.end(),
                        [](unsigned char character)
                        {
                            return std::isspace(character) != 0;
                        }
                    ),
                    token.end()
                );

                if (token == "none")
                {
                    entry.teachesNothing = true;
                }
                else if (!token.empty())
                {
                    entry.offeredSkills.push_back(token);
                }
            }
        }

        if (row.size() > 25 && !row[25].empty())
        {
            const size_t colon = row[25].find(':');
            entry.priceQBit = colon != std::string::npos ? uint32_t(std::strtoul(row[25].c_str(), nullptr, 10)) : 0;
            entry.priceAfterQBit = colon != std::string::npos ? std::strtof(row[25].c_str() + colon + 1, nullptr) : 0.0f;

            if (entry.priceQBit == 0 || !(entry.priceAfterQBit > 0.0f))
            {
                return false;
            }
        }

        if (entry.offeredSkills.empty() && !entry.teachesNothing)
        {
            entry.offeredSkills = deriveOfferedSkillsForHouseType(entry.type);
        }

        m_entries[entry.id] = entry;
    }

    return !m_entries.empty();
}

bool HouseTable::appendVendorRows(
    const std::vector<std::vector<std::string>> &vendorRows,
    const std::vector<std::vector<std::string>> &aliasRows,
    const std::vector<std::vector<std::string>> &stockRows,
    std::string &errorMessage)
{
    errorMessage.clear();
    std::unordered_set<std::string> canonicalIds;
    std::unordered_set<std::string> sourceKeys;

    for (const std::vector<std::string> &row : vendorRows)
    {
        if (row.empty() || row[0].empty() || row[0] == "vendor_id")
        {
            continue;
        }
        if (row.size() < 25)
        {
            errorMessage = "malformed vendor row for id " + row[0];
            return false;
        }

        const uint32_t vendorId = parseUnsigned(row[0]);
        const VendorStockProfile profile = parseVendorStockProfile(row[8]);
        const std::string sourceKey = vendorAliasKey(row[1], parseUnsigned(row[2]));
        if (vendorId == 0
            || profile == VendorStockProfile::None
            || row[3].empty()
            || m_entries.contains(vendorId)
            || !canonicalIds.insert(row[3]).second
            || !sourceKeys.insert(sourceKey).second)
        {
            errorMessage = "invalid or duplicate vendor row for id " + row[0];
            return false;
        }

        HouseEntry entry = {};
        entry.id = vendorId;
        entry.packageId = row[1];
        entry.sourceVendorId = parseUnsigned(row[2]);
        entry.canonicalId = row[3];
        entry.name = row[4];
        entry.buildingName = row[5];
        entry.type = row[6] + " Shop";
        entry.proprietorName = entry.name;
        entry.priceMultiplier = std::strtof(row[11].c_str(), nullptr);
        entry.skillPriceMultiplier = entry.priceMultiplier;
        entry.standardStockTier = parseSigned(row[13]);
        entry.specialStockTier = parseSigned(row[16]);
        entry.stockRefreshDays = parseSigned(row[18]);
        entry.vendorCanSell = parseBool(row[19]);
        entry.vendorCanIdentify = parseBool(row[20]);
        entry.vendorCanRepair = parseBool(row[21]);
        entry.dialogueScenePolicy = row[22] == "LiveGameplay"
            ? DialogueScenePolicy::LiveGameplay
            : DialogueScenePolicy::HouseVideo;
        entry.vendorStockProfile = profile;
        // Optional open_hour and close_hour columns after the 31 standard ones (a world's shopkeepers' hours); equal
        // or absent: always open.
        entry.openHour = row.size() > 32 && !row[31].empty() ? parseSigned(row[31]) : 0;
        entry.closeHour = row.size() > 32 && !row[32].empty() ? parseSigned(row[32]) : 0;
        entry.resaleCapPercent = row.size() > 33 && !row[33].empty() ? std::clamp(parseSigned(row[33]), 1, 100) : 100;
        // Optional buy_view column: Ledger (MM9's scrolling list) or Shelf; absent or empty: Shelf.
        if (row.size() > 34 && !row[34].empty())
        {
            if (row[34] == "Ledger")
            {
                entry.shopBuyView = ShopBuyView::Ledger;
            }
            else if (row[34] != "Shelf")
            {
                errorMessage = "unknown buy_view '" + row[34] + "' for vendor " + row[0];
                return false;
            }
        }
        // Optional learn_skills column: the skills its "Learn Skills" menu teaches at Normal (MM9's shops).
        if (row.size() > 35 && !parseLearnSkills(row[35], entry.offeredSkills))
        {
            errorMessage = "invalid learn_skills '" + row[35] + "' for vendor " + row[0];
            return false;
        }
        m_entries.emplace(vendorId, std::move(entry));
    }

    for (const std::vector<std::string> &row : aliasRows)
    {
        if (row.empty() || row[0].empty() || row[0] == "vendor_id")
        {
            continue;
        }
        if (row.size() < 3)
        {
            errorMessage = "malformed vendor alias row for id " + row[0];
            return false;
        }

        const uint32_t vendorId = parseUnsigned(row[0]);
        const uint32_t sourceVendorId = parseUnsigned(row[2]);
        const HouseEntry *pVendor = get(vendorId);
        const std::string key = vendorAliasKey(row[1], sourceVendorId);
        if (pVendor == nullptr
            || sourceVendorId == 0
            || pVendor->packageId != row[1]
            || pVendor->sourceVendorId != sourceVendorId
            || !m_vendorAliases.emplace(key, vendorId).second)
        {
            errorMessage = "invalid or duplicate vendor alias '" + key + "'";
            return false;
        }
    }

    for (const std::vector<std::string> &row : stockRows)
    {
        if (row.empty() || row[0].empty() || row[0] == "vendor_id")
        {
            continue;
        }
        if (row.size() < 11)
        {
            errorMessage = "malformed vendor stock row for id " + row[0];
            return false;
        }

        const uint32_t vendorId = parseUnsigned(row[0]);
        const uint32_t pageIndex = parseUnsigned(row[2]);
        const uint32_t slotIndex = parseUnsigned(row[3]);
        const uint32_t itemId = parseUnsigned(row[4]);
        const uint32_t generationVersion = parseUnsigned(row[10]);
        const std::unordered_map<uint32_t, HouseEntry>::iterator entryIt = m_entries.find(vendorId);
        if (entryIt == m_entries.end()
            || itemId == 0
            || generationVersion == 0
            || (row[1] != "standard" && row[1] != "special"))
        {
            errorMessage = "invalid vendor stock row for vendor " + row[0];
            return false;
        }
        if (entryIt->second.deterministicStockGenerationVersion == 0)
        {
            entryIt->second.deterministicStockGenerationVersion = generationVersion;
        }
        else if (entryIt->second.deterministicStockGenerationVersion != generationVersion)
        {
            errorMessage = "mixed stock generation versions for vendor " + row[0];
            return false;
        }

        std::vector<HouseEntry::DeterministicStockPage> &pages = row[1] == "standard"
            ? entryIt->second.deterministicStandardStockPages
            : entryIt->second.deterministicSpecialStockPages;
        HouseEntry::DeterministicStockPage *pPage = findOrAddStockPage(pages, pageIndex);
        if (pPage->items.size() <= slotIndex)
        {
            pPage->items.resize(static_cast<size_t>(slotIndex) + 1);
        }
        if (pPage->items[slotIndex].itemId != 0)
        {
            errorMessage = "duplicate vendor stock slot for vendor " + row[0];
            return false;
        }

        pPage->items[slotIndex] = {
            .itemId = itemId,
            .quantity = std::max<uint32_t>(1, parseUnsigned(row[5])),
            .identified = parseBool(row[6]),
            .standardEnchantId = static_cast<uint16_t>(parseUnsigned(row[7])),
            .standardEnchantPower = static_cast<uint16_t>(parseUnsigned(row[8])),
            .specialEnchantId = static_cast<uint16_t>(parseUnsigned(row[9])),
            .minObjectives = static_cast<uint16_t>(row.size() > 11 ? parseUnsigned(row[11]) : 0),
        };
    }

    for (auto &[vendorId, entry] : m_entries)
    {
        if (entry.vendorStockProfile == VendorStockProfile::None)
        {
            continue;
        }
        // A Ledger shop may keep everything in one list (MM9's merchants have no Buy Special).
        if (entry.deterministicStandardStockPages.empty()
            || (entry.deterministicSpecialStockPages.empty() && entry.shopBuyView != ShopBuyView::Ledger))
        {
            errorMessage = "vendor " + std::to_string(vendorId) + " has incomplete deterministic stock";
            return false;
        }
        if (!m_vendorAliases.contains(vendorAliasKey(entry.packageId, entry.sourceVendorId)))
        {
            errorMessage = "vendor " + std::to_string(vendorId) + " has no source alias";
            return false;
        }
        const auto sortPages = [](std::vector<HouseEntry::DeterministicStockPage> &pages)
        {
            std::sort(
                pages.begin(),
                pages.end(),
                [](const HouseEntry::DeterministicStockPage &left, const HouseEntry::DeterministicStockPage &right)
                {
                    return left.pageIndex < right.pageIndex;
                });
        };
        sortPages(entry.deterministicStandardStockPages);
        sortPages(entry.deterministicSpecialStockPages);
        const auto validatePageLayout = [&](const std::vector<HouseEntry::DeterministicStockPage> &pages) -> bool
        {
            // A shelf holds a fixed number of slots; the ledger scrolls, so a page may hold any number of items
            // up to MaxLedgerStockPageSlots.
            const bool ledger = entry.shopBuyView == ShopBuyView::Ledger;
            const size_t expectedSlotCount = expectedVendorStockSlotCount(entry.vendorStockProfile);
            for (size_t pageOrdinal = 0; pageOrdinal < pages.size(); ++pageOrdinal)
            {
                const size_t slotCount = pages[pageOrdinal].items.size();
                const bool sizeValid = ledger
                    ? slotCount > 0 && slotCount <= MaxLedgerStockPageSlots
                    : slotCount == expectedSlotCount;
                if (pages[pageOrdinal].pageIndex != pageOrdinal || !sizeValid)
                {
                    errorMessage = "vendor " + std::to_string(vendorId)
                        + " has a non-contiguous or incorrectly sized stock page";
                    return false;
                }
            }
            return true;
        };
        if (!validatePageLayout(entry.deterministicStandardStockPages)
            || !validatePageLayout(entry.deterministicSpecialStockPages))
        {
            return false;
        }
    }

    return true;
}

bool HouseTable::appendServiceVenueRows(
    const std::vector<std::vector<std::string>> &venueRows,
    const std::vector<std::vector<std::string>> &aliasRows,
    std::string &errorMessage,
    const MapStats *pMapStats)
{
    errorMessage.clear();
    std::unordered_set<std::string> canonicalIds;
    std::unordered_set<std::string> sourceKeys;

    for (const std::vector<std::string> &row : venueRows)
    {
        if (row.empty() || row[0].empty() || row[0] == "service_id")
        {
            continue;
        }
        if (row.size() < 16)
        {
            errorMessage = "malformed service venue row for id " + row[0];
            return false;
        }

        const uint32_t serviceId = parseUnsigned(row[0]);
        const uint32_t sourceServiceId = parseUnsigned(row[2]);
        const std::string sourceKey = serviceAliasKey(row[1], sourceServiceId);
        const float priceMultiplier = std::strtof(row[7].c_str(), nullptr);
        const float templeHealingTier = std::strtof(row[8].c_str(), nullptr);
        const int trainingMaxLevel = parseSigned(row[9]);
        const bool templeCanHeal = parseBool(row[10]);
        const bool templeCanDonate = parseBool(row[11]);
        // MM9's service venues: temples, training halls, inns (taverns) and banks. A bank charges nothing.
        const bool isBank = row[6] == "Bank";
        const bool healsOrDonates = templeCanHeal || templeCanDonate;
        if (serviceId == 0
            || sourceServiceId == 0
            || (row[6] != "Temple" && row[6] != "Training" && row[6] != "Tavern" && !isBank)
            || (isBank ? priceMultiplier < 0.0f : priceMultiplier <= 0.0f)
            || templeHealingTier < 0.0f
            || trainingMaxLevel < 0
            || (row[6] != "Temple" && healsOrDonates)
            || (row[6] == "Temple" && !templeCanHeal && !templeCanDonate)
            || row[3].empty()
            || m_entries.contains(serviceId)
            || !canonicalIds.insert(row[3]).second
            || !sourceKeys.insert(sourceKey).second)
        {
            errorMessage = "invalid or duplicate service venue row for id " + row[0];
            return false;
        }

        HouseEntry entry = {};
        entry.id = serviceId;
        entry.packageId = row[1];
        entry.sourceServiceId = sourceServiceId;
        if (row.size() > 18 && !row[18].empty())
        {
            const MapStatsEntry *map = pMapStats != nullptr ? pMapStats->findByFileName(row[18]) : nullptr;
            if (map == nullptr)
            {
                errorMessage = "unknown service venue map: " + row[18];
                return false;
            }
            entry.mapId = map->id;
        }
        entry.canonicalId = row[3];
        entry.name = row[4];
        entry.buildingName = row[5];
        entry.type = row[6];
        entry.proprietorName = entry.name;
        entry.priceMultiplier = priceMultiplier;
        // Optional skill_price_multiplier column (an inn's skills keep MM9's merchant base; its price multiplier is the
        // MM6-MM8 tavern value of the food and room prices); empty or absent: the price multiplier.
        entry.skillPriceMultiplier = row.size() > 17 && !row[17].empty()
            ? std::strtof(row[17].c_str(), nullptr)
            : entry.priceMultiplier;
        entry.templeHealingTier = templeHealingTier;
        entry.trainingMaxLevel = trainingMaxLevel;
        entry.templeCanHeal = templeCanHeal;
        entry.templeCanDonate = templeCanDonate;
        entry.serviceCanLearnSkills = parseBool(row[12]);
        entry.dialogueScenePolicy = row[13] == "LiveGameplay"
            ? DialogueScenePolicy::LiveGameplay
            : DialogueScenePolicy::HouseVideo;
        entry.openHour = 0;
        entry.closeHour = 0;
        // Optional learn_skills column: what its "Learn Skills" menu teaches; required exactly when can_learn_skills.
        if (row.size() > 16 && !parseLearnSkills(row[16], entry.offeredSkills))
        {
            errorMessage = "invalid learn_skills '" + row[16] + "' for service venue " + row[0];
            return false;
        }
        if (entry.serviceCanLearnSkills == entry.offeredSkills.empty() || !(entry.skillPriceMultiplier >= 0.0f))
        {
            errorMessage = "can_learn_skills, learn_skills or skill_price_multiplier invalid for service venue " + row[0];
            return false;
        }
        // A tavern teaches by its list (the tavern menu offers "Learn Skills" unless it teaches nothing)
        entry.teachesNothing = entry.offeredSkills.empty();
        m_entries.emplace(serviceId, std::move(entry));
    }

    for (const std::vector<std::string> &row : aliasRows)
    {
        if (row.empty() || row[0].empty() || row[0] == "service_id")
        {
            continue;
        }
        if (row.size() < 3)
        {
            errorMessage = "malformed service venue alias row for id " + row[0];
            return false;
        }

        const uint32_t serviceId = parseUnsigned(row[0]);
        const uint32_t sourceServiceId = parseUnsigned(row[2]);
        const HouseEntry *pVenue = get(serviceId);
        const std::string key = serviceAliasKey(row[1], sourceServiceId);
        if (pVenue == nullptr
            || sourceServiceId == 0
            || pVenue->packageId != row[1]
            || pVenue->sourceServiceId != sourceServiceId
            || !m_serviceAliases.emplace(key, serviceId).second)
        {
            errorMessage = "invalid or duplicate service venue alias '" + key + "'";
            return false;
        }
    }

    for (const std::vector<std::string> &row : venueRows)
    {
        if (row.empty() || row[0].empty() || row[0] == "service_id")
        {
            continue;
        }
        const HouseEntry *pVenue = get(parseUnsigned(row[0]));
        if (pVenue == nullptr
            || !m_serviceAliases.contains(serviceAliasKey(pVenue->packageId, pVenue->sourceServiceId)))
        {
            errorMessage = "service venue " + row[0] + " has no source alias";
            return false;
        }
    }

    return true;
}

bool HouseTable::validateVendorStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    std::string &errorMessage) const
{
    errorMessage.clear();
    for (const auto &[vendorId, entry] : m_entries)
    {
        if (entry.vendorStockProfile == VendorStockProfile::None)
        {
            continue;
        }

        const auto validatePages = [&](const std::vector<HouseEntry::DeterministicStockPage> &pages) -> bool
        {
            for (const HouseEntry::DeterministicStockPage &page : pages)
            {
                for (const HouseEntry::DeterministicStockItem &stockItem : page.items)
                {
                    const ItemDefinition *pItem = itemTable.get(stockItem.itemId);
                    if (pItem == nullptr
                        || pItem->hasContentFlag("NoShop")
                        || pItem->rarity != ItemRarity::Common
                        || pItem->normalizedTier == 7
                        || !pItem->setId.empty())
                    {
                        errorMessage = "vendor " + std::to_string(vendorId)
                            + " references prohibited stock item " + std::to_string(stockItem.itemId);
                        return false;
                    }
                    if ((stockItem.standardEnchantId != 0
                            && standardItemEnchantTable.get(stockItem.standardEnchantId) == nullptr)
                        || (stockItem.specialEnchantId != 0
                            && specialItemEnchantTable.get(stockItem.specialEnchantId) == nullptr))
                    {
                        errorMessage = "vendor " + std::to_string(vendorId)
                            + " references unknown enchant for stock item " + std::to_string(stockItem.itemId);
                        return false;
                    }
                    if (stockItem.standardEnchantId != 0)
                    {
                        const std::optional<size_t> slotIndex = standardEnchantSlotIndex(pItem->equipStat);
                        const StandardItemEnchantEntry *pEnchant =
                            standardItemEnchantTable.get(stockItem.standardEnchantId);
                        if (!slotIndex || pEnchant == nullptr || pEnchant->slotValues[*slotIndex] <= 0)
                        {
                            errorMessage = "vendor " + std::to_string(vendorId)
                                + " uses an inapplicable standard enchant for stock item "
                                + std::to_string(stockItem.itemId);
                            return false;
                        }
                    }
                    if (stockItem.specialEnchantId != 0)
                    {
                        const std::optional<size_t> slotIndex = specialEnchantSlotIndex(pItem->equipStat);
                        const SpecialItemEnchantEntry *pEnchant =
                            specialItemEnchantTable.get(stockItem.specialEnchantId);
                        if (!slotIndex || pEnchant == nullptr || pEnchant->slotWeights[*slotIndex] <= 0)
                        {
                            errorMessage = "vendor " + std::to_string(vendorId)
                                + " uses an inapplicable special enchant for stock item "
                                + std::to_string(stockItem.itemId);
                            return false;
                        }
                    }
                }
            }
            return true;
        };
        if (!validatePages(entry.deterministicStandardStockPages)
            || !validatePages(entry.deterministicSpecialStockPages))
        {
            return false;
        }
    }
    return true;
}

size_t HouseTable::removeSpecialEnchantsTheRulesetDoesNotRoll(
    const ItemTable &itemTable,
    const SpecialItemEnchantTable &specialItemEnchantTable)
{
    size_t removed = 0;
    const auto removeFrom = [&](std::vector<HouseEntry::DeterministicStockPage> &pages)
    {
        for (HouseEntry::DeterministicStockPage &page : pages)
        {
            for (HouseEntry::DeterministicStockItem &stockItem : page.items)
            {
                const ItemDefinition *pItem = itemTable.get(stockItem.itemId);
                const SpecialItemEnchantEntry *pEnchant = stockItem.specialEnchantId != 0
                    ? specialItemEnchantTable.get(stockItem.specialEnchantId)
                    : nullptr;
                const std::optional<size_t> slotIndex =
                    pItem != nullptr ? specialEnchantSlotIndex(pItem->equipStat) : std::nullopt;

                if (pEnchant != nullptr && slotIndex && pEnchant->slotWeights[*slotIndex] <= 0)
                {
                    stockItem.specialEnchantId = 0;
                    ++removed;
                }
            }
        }
    };

    for (auto &[vendorId, entry] : m_entries)
    {
        removeFrom(entry.deterministicStandardStockPages);
        removeFrom(entry.deterministicSpecialStockPages);
    }

    return removed;
}

bool HouseTable::loadAnimationRows(const std::vector<std::vector<std::string>> &rows)
{
    const std::unordered_map<uint32_t, std::string> emptyMovieStems;
    return loadAnimationRows(rows, emptyMovieStems);
}

bool HouseTable::loadAnimationRows(
    const std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &movieRows)
{
    return loadAnimationRows(rows, movieStemsByAnimationIdFromRows(movieRows));
}

bool HouseTable::loadAnimationRows(
    const std::vector<std::vector<std::string>> &rows,
    const std::unordered_map<uint32_t, std::string> &movieStemsByAnimationId)
{
    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 3 || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        const uint32_t houseId = static_cast<uint32_t>(parsedId);
        HouseEntry &entry = m_entries[houseId];
        const uint32_t animationId = row.size() > 1 ? parseUnsigned(row[1]) : 0;
        entry.id = houseId;
        entry.buildingName = row[2];
        std::string normalizedVideoStem;

        if (row.size() > 4)
        {
            normalizedVideoStem = normalizeVideoStem(row[4]);
        }

        if (normalizedVideoStem.empty() && animationId != 0)
        {
            const std::unordered_map<uint32_t, std::string>::const_iterator movieIt =
                movieStemsByAnimationId.find(animationId);

            if (movieIt != movieStemsByAnimationId.end())
            {
                normalizedVideoStem = movieIt->second;
            }
        }

        if (!normalizedVideoStem.empty())
        {
            entry.videoName = normalizedVideoStem;
        }
        entry.roomSoundId = (row.size() > 6 && !row[6].empty()) ? std::strtoul(row[6].c_str(), nullptr, 10) : 0;
        entry.houseSoundBaseId = (row.size() > 7 && !row[7].empty()) ? std::strtoul(row[7].c_str(), nullptr, 10) : 0;
        if (row.size() > 8)
        {
            const uint32_t proprietorPictureId = parseUnsigned(row[8]);

            if (proprietorPictureId != 0)
            {
                entry.proprietorPictureId = proprietorPictureId;
            }
        }

        if (entry.type.empty() && row.size() > 9)
        {
            entry.type = row[9];
        }

        entry.residentNpcIds.clear();

        size_t startPosition = 0;

        while (startPosition <= row[3].size())
        {
            const size_t commaPosition = row[3].find(',', startPosition);
            const size_t tokenLength = (commaPosition == std::string::npos)
                ? (row[3].size() - startPosition)
                : (commaPosition - startPosition);
            const std::string token = row[3].substr(startPosition, tokenLength);

            if (!token.empty())
            {
                char *pTokenEnd = nullptr;
                const unsigned long parsedNpcId = std::strtoul(token.c_str(), &pTokenEnd, 10);

                if (pTokenEnd != token.c_str() && *pTokenEnd == '\0')
                {
                    entry.residentNpcIds.push_back(static_cast<uint32_t>(parsedNpcId));
                }
            }

            if (commaPosition == std::string::npos)
            {
                break;
            }

            startPosition = commaPosition + 1;
        }
    }

    return true;
}

bool HouseTable::applyHouseRules(
    const MergedHouseRuleTable &houseRules,
    const MergedTransportLocationTable &transportLocations,
    const MapStats &mapStats)
{
    for (auto &[houseId, entry] : m_entries)
    {
        (void)houseId;

        if (!applyShopStockRules(entry, houseRules))
        {
            return false;
        }

        if ((entry.type == "Weapon Shop" || entry.type == "Armor Shop") && entry.offeredSkills.empty()
            && !entry.teachesNothing)
        {
            entry.offeredSkills = deriveOfferedSkillsFromShopStock(entry);
        }

        if (entry.type == "Training" && !applyTrainingRule(entry, houseRules))
        {
            return false;
        }

        if (entry.type == "Tavern" && !applyArcomageRule(entry, houseRules))
        {
            return false;
        }

        if (isSpellbookHouseType(entry.type) && !applySpellbookRule(entry, houseRules))
        {
            return false;
        }

        if (!isTransportHouseTypeName(entry.type) || !entry.transportRoutes.empty())
        {
            continue;
        }

        const MergedHouseRuleSection *pSection = findHouseRuleSection(houseRules, entry.type);

        if (pSection == nullptr)
        {
            std::cerr << "merged house rules are missing transport section: " << entry.type << '\n';
            return false;
        }

        const uint32_t routeRuleId = houseRuleId(entry);
        const std::vector<int32_t> *pRouteLocationRow = findHouseRuleRow(*pSection, routeRuleId);

        if (pRouteLocationRow == nullptr)
        {
            continue;
        }

        std::vector<int32_t> addedLocationIds;

        for (size_t columnIndex = 1; columnIndex < pRouteLocationRow->size(); ++columnIndex)
        {
            const int32_t locationId = (*pRouteLocationRow)[columnIndex];

            if (locationId < 0)
            {
                continue;
            }

            if (std::find(addedLocationIds.begin(), addedLocationIds.end(), locationId) != addedLocationIds.end())
            {
                continue;
            }

            const MergedTransportLocationEntry *pLocation = findTransportLocation(transportLocations, locationId);

            if (pLocation == nullptr)
            {
                std::cerr << "merged house route references unknown transport location " << locationId
                          << " for house " << entry.id << '\n';
                return false;
            }

            HouseEntry::TransportRoute route = {};
            route.routeIndex = static_cast<uint32_t>(entry.transportRoutes.size() + 1);
            route.destinationName = destinationNameForTransportLocation(*pLocation, mapStats);
            route.mapFileName = pLocation->mapName;
            route.daysAvailable = pLocation->weekdays;
            route.travelDays = pLocation->daysCount;
            route.x = pLocation->x;
            route.y = pLocation->y;
            route.z = pLocation->z;
            route.directionDegrees = directionDegreesFromMergedYawUnits(pLocation->direction);
            route.requiredQBit = pLocation->qbit;
            route.useMapStartPosition = false;
            entry.transportRoutes.push_back(std::move(route));
            addedLocationIds.push_back(locationId);
        }
    }

    return true;
}

void HouseTable::applyMapWorlds(const MapStats &mapStats)
{
    for (auto &[houseId, entry] : m_entries)
    {
        (void)houseId;
        const MapStatsEntry *pMap = entry.mapId != 0 ? mapStats.findById(entry.mapId) : nullptr;
        entry.worldId = pMap != nullptr ? pMap->worldId : std::string();
    }
}

bool HouseTable::applyHouseExits(const MergedHouseExitTable &houseExits, const MapStats &mapStats)
{
    const MergedHouseExitTableData &exitData = houseExits.data();

    for (auto &[houseId, entry] : m_entries)
    {
        (void)houseId;
        entry.extraExit.reset();

        if (entry.rawExtraExitPictureIndex == 0 || entry.rawExtraExitMapId == 0)
        {
            continue;
        }

        const MapStatsEntry *pDestinationMap = mapStats.findById(entry.rawExtraExitMapId);

        if (pDestinationMap == nullptr)
        {
            std::cerr << "merged house exit references unknown map id " << entry.rawExtraExitMapId
                      << " for house " << entry.id << '\n';
            return false;
        }

        HouseEntry::ExtraExit extraExit = {};
        extraExit.destinationMapId = entry.rawExtraExitMapId;
        extraExit.destinationMapFileName = pDestinationMap->fileName;
        extraExit.destinationName = pDestinationMap->name;
        extraExit.label = !entry.enterText.empty() && entry.enterText != "0" ? entry.enterText : pDestinationMap->name;

        const size_t pictureIndex = static_cast<size_t>(entry.rawExtraExitPictureIndex - 1);

        if (pictureIndex >= exitData.npcPictureIds.size())
        {
            std::cerr << "merged house exit references unknown picture slot " << entry.rawExtraExitPictureIndex
                      << " for house " << entry.id << '\n';
            return false;
        }

        extraExit.pictureId = exitData.npcPictureIds[pictureIndex];

        if (entry.rawExtraExitRestriction > 0)
        {
            extraExit.requiredQuestBit = static_cast<uint32_t>(entry.rawExtraExitRestriction);
        }
        else if (entry.rawExtraExitRestriction < 0)
        {
            const size_t entranceIndex = static_cast<size_t>(-entry.rawExtraExitRestriction - 1);
            const std::string destinationFileName = normalizedMapFileName(pDestinationMap->fileName);
            const MergedHouseExitEntry *pEntranceEntry = nullptr;

            for (const MergedHouseExitEntry &candidate : exitData.exits)
            {
                if (normalizedMapFileName(candidate.mapName) == destinationFileName)
                {
                    pEntranceEntry = &candidate;
                    break;
                }
            }

            if (pEntranceEntry == nullptr || entranceIndex >= pEntranceEntry->positions.size())
            {
                std::cerr << "merged house exit references unknown entrance " << -entry.rawExtraExitRestriction
                          << " for map " << pDestinationMap->fileName << " and house " << entry.id << '\n';
                return false;
            }

            extraExit.x = pEntranceEntry->positions[entranceIndex].x;
            extraExit.y = pEntranceEntry->positions[entranceIndex].y;
            extraExit.z = pEntranceEntry->positions[entranceIndex].z;
            extraExit.useMapStartPosition = false;
        }

        entry.extraExit = std::move(extraExit);
    }

    return true;
}

std::optional<std::string> HouseTable::getName(uint32_t houseId) const
{
    const auto entryIt = m_entries.find(houseId);

    if (entryIt == m_entries.end())
    {
        return std::nullopt;
    }

    return entryIt->second.name;
}

const HouseEntry *HouseTable::get(uint32_t houseId) const
{
    const std::unordered_map<uint32_t, HouseEntry>::const_iterator entryIt = m_entries.find(houseId);

    if (entryIt == m_entries.end())
    {
        return nullptr;
    }

    const HouseEntry &entry = entryIt->second;

    if (entry.priceQBit == 0 || !m_questBitQuery || !m_questBitQuery(entry.priceQBit))
    {
        return &entry;
    }

    HouseEntry &switched = m_priceSwitchedEntries[houseId];
    switched = entry;
    switched.priceMultiplier = entry.priceAfterQBit;
    return &switched;
}

void HouseTable::setQuestBitQuery(std::function<bool(uint32_t)> query) const
{
    m_questBitQuery = std::move(query);
}

const HouseEntry *HouseTable::resolvePackageSourceVendorId(
    const std::string &packageId,
    uint32_t sourceVendorId) const
{
    const std::unordered_map<std::string, uint32_t>::const_iterator aliasIt =
        m_vendorAliases.find(vendorAliasKey(packageId, sourceVendorId));
    return aliasIt != m_vendorAliases.end() ? get(aliasIt->second) : nullptr;
}

const HouseEntry *HouseTable::resolvePackageSourceServiceId(
    const std::string &packageId,
    uint32_t sourceServiceId) const
{
    const std::unordered_map<std::string, uint32_t>::const_iterator aliasIt =
        m_serviceAliases.find(serviceAliasKey(packageId, sourceServiceId));
    return aliasIt != m_serviceAliases.end() ? get(aliasIt->second) : nullptr;
}

const std::unordered_map<uint32_t, HouseEntry> &HouseTable::entries() const
{
    return m_entries;
}
}
