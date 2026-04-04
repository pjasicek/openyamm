#include "game/ui/GameplayPartyOverlayRenderer.h"

#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SkillData.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"
#include "game/ui/HudUiService.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cstdio>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <optional>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr uint32_t BrokenItemTintColorAbgr = 0x800000ffu;
constexpr uint32_t UnidentifiedItemTintColorAbgr = 0x80ff0000u;

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

enum class ItemTintContext
{
    None,
    Held,
    Equipped,
    ShopIdentify,
    ShopRepair,
};

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
    viewport.x = 0.0f;
    viewport.y = 0.0f;
    viewport.width = static_cast<float>(screenWidth);
    viewport.height = static_cast<float>(screenHeight);

    if (screenHeight > 0)
    {
        const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

        if (viewport.width > maxWidthForHeight)
        {
            viewport.width = maxWidthForHeight;
            viewport.x = (static_cast<float>(screenWidth) - viewport.width) * 0.5f;
        }
    }

    return viewport;
}

float snappedHudFontScale(float scale)
{
    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= HudFontIntegerSnapThreshold)
    {
        return std::max(1.0f, roundedScale);
    }

    return std::max(1.0f, scale);
}

uint32_t itemTintColorAbgr(
    const InventoryItem *pItemState,
    const ItemDefinition *pItemDefinition,
    ItemTintContext context)
{
    if (pItemState == nullptr || pItemDefinition == nullptr)
    {
        return 0xffffffffu;
    }

    const bool isBroken = pItemState->broken;
    const bool isUnidentified = !pItemState->identified && ItemRuntime::requiresIdentification(*pItemDefinition);

    switch (context)
    {
        case ItemTintContext::Held:
        case ItemTintContext::Equipped:
            if (isBroken)
            {
                return BrokenItemTintColorAbgr;
            }

            if (isUnidentified)
            {
                return UnidentifiedItemTintColorAbgr;
            }

            break;

        case ItemTintContext::ShopIdentify:
            if (isUnidentified)
            {
                return UnidentifiedItemTintColorAbgr;
            }

            break;

        case ItemTintContext::ShopRepair:
            if (isBroken)
            {
                return BrokenItemTintColorAbgr;
            }

            break;

        case ItemTintContext::None:
            break;
    }

    return 0xffffffffu;
}

uint32_t makeAbgrColor(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return static_cast<uint32_t>(red)
        | (static_cast<uint32_t>(green) << 8)
        | (static_cast<uint32_t>(blue) << 16)
        | 0xff000000u;
}

bool tryParseInteger(const std::string &value, int &parsedValue)
{
    if (value.empty())
    {
        return false;
    }

    size_t parsedCharacters = 0;

    try
    {
        parsedValue = std::stoi(value, &parsedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return parsedCharacters == value.size();
}

struct InventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
    float scale = 1.0f;
};

struct InventoryItemScreenRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

struct CharacterSkillUiRow
{
    std::string canonicalName;
    std::string label;
    std::string level;
    bool upgradeable = false;
};

struct CharacterSkillUiData
{
    std::vector<CharacterSkillUiRow> weaponRows;
    std::vector<CharacterSkillUiRow> magicRows;
    std::vector<CharacterSkillUiRow> armorRows;
    std::vector<CharacterSkillUiRow> miscRows;
};

constexpr size_t AdventurersInnVisibleRows = 4;
constexpr size_t AdventurersInnVisibleColumns = 2;
constexpr size_t AdventurersInnVisibleCount = AdventurersInnVisibleRows * AdventurersInnVisibleColumns;
constexpr float AdventurersInnPortraitX = 34.0f;
constexpr float AdventurersInnPortraitY = 47.0f;
constexpr float AdventurersInnPortraitWidth = 62.0f;
constexpr float AdventurersInnPortraitHeight = 72.0f;
constexpr float AdventurersInnPortraitGapX = 3.0f;
constexpr float AdventurersInnPortraitGapY = 3.0f;
constexpr float AdventurersInnColumn1X = 200.0f;
constexpr float AdventurersInnColumn1Y = 50.0f;
constexpr float AdventurersInnColumn2X = 330.0f;
constexpr float AdventurersInnColumn2Y = 82.0f;
constexpr float AdventurersInnBlurbX = 200.0f;
constexpr float AdventurersInnBlurbY = 210.0f;
constexpr float AdventurersInnBlurbWidth = 236.0f;
constexpr float AdventurersInnColumnLineStep = 16.0f;
constexpr uint32_t AdventurersInnSelectionColorAbgr = 0xff8ed9e9u;
constexpr uint32_t AdventurersInnTextColorAbgr = 0xffffffffu;
constexpr float AdventurersInnSelectionThickness = 2.0f;

bool shouldRenderCharacterLayoutInAdventurersInn(const std::string &normalizedLayoutId)
{
    return normalizedLayoutId.starts_with("adventurersinn")
        || normalizedLayoutId.starts_with("characterdoll")
        || normalizedLayoutId == "characterroot"
        || normalizedLayoutId == "charactertopbar"
        || normalizedLayoutId == "charactergoldfoodicon"
        || normalizedLayoutId == "charactergoldlabel"
        || normalizedLayoutId == "characterfoodlabel";
}

std::string npcPortraitTextureName(uint32_t pictureId)
{
    if (pictureId == 0)
    {
        return {};
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "npc%04u", pictureId);
    return buffer;
}

constexpr const char *WeaponSkillNames[] = {
    "Axe",
    "Bow",
    "Dagger",
    "Mace",
    "Spear",
    "Staff",
    "Sword",
    "Unarmed",
    "Blaster",
};

constexpr const char *MagicSkillNames[] = {
    "FireMagic",
    "AirMagic",
    "WaterMagic",
    "EarthMagic",
    "SpiritMagic",
    "MindMagic",
    "BodyMagic",
    "LightMagic",
    "DarkMagic",
};

constexpr const char *ArmorSkillNames[] = {
    "LeatherArmor",
    "ChainArmor",
    "PlateArmor",
    "Shield",
    "Dodging",
};

constexpr const char *MiscSkillNames[] = {
    "Alchemy",
    "Armsmaster",
    "Bodybuilding",
    "IdentifyItem",
    "IdentifyMonster",
    "Learning",
    "DisarmTraps",
    "Meditation",
    "Merchant",
    "Perception",
    "RepairItem",
    "Stealing",
};

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    float scale,
    int columns,
    int rows)
{
    InventoryGridMetrics metrics = {};
    metrics.x = x;
    metrics.y = y;
    metrics.cellWidth = width / static_cast<float>(std::max(1, columns));
    metrics.cellHeight = height / static_cast<float>(std::max(1, rows));
    metrics.scale = scale;
    return metrics;
}

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    float scale)
{
    return computeInventoryGridMetrics(
        x,
        y,
        width,
        height,
        scale,
        Character::InventoryWidth,
        Character::InventoryHeight);
}

InventoryItemScreenRect computeInventoryItemScreenRect(
    const InventoryGridMetrics &gridMetrics,
    const InventoryItem &item,
    float textureWidth,
    float textureHeight)
{
    const float slotSpanWidth = static_cast<float>(item.width) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(item.height) * gridMetrics.cellHeight;
    const float offsetX = (slotSpanWidth - textureWidth) * 0.5f;
    const float offsetY = (slotSpanHeight - textureHeight) * 0.5f;

    InventoryItemScreenRect rect = {};
    rect.x = std::round(
        gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth + offsetX);
    rect.y = std::round(
        gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;
        case EquipmentSlot::MainHand:
            return equipment.mainHand;
        case EquipmentSlot::Bow:
            return equipment.bow;
        case EquipmentSlot::Armor:
            return equipment.armor;
        case EquipmentSlot::Helm:
            return equipment.helm;
        case EquipmentSlot::Belt:
            return equipment.belt;
        case EquipmentSlot::Cloak:
            return equipment.cloak;
        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;
        case EquipmentSlot::Boots:
            return equipment.boots;
        case EquipmentSlot::Amulet:
            return equipment.amulet;
        case EquipmentSlot::Ring1:
            return equipment.ring1;
        case EquipmentSlot::Ring2:
            return equipment.ring2;
        case EquipmentSlot::Ring3:
            return equipment.ring3;
        case EquipmentSlot::Ring4:
            return equipment.ring4;
        case EquipmentSlot::Ring5:
            return equipment.ring5;
        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return 0;
}

std::optional<EquipmentSlot> characterEquipmentSlotForLayoutId(const std::string &layoutId)
{
    const std::string normalized = toLowerCopy(layoutId);

    if (normalized == "characterdollbowslot")
    {
        return EquipmentSlot::Bow;
    }

    if (normalized == "characterdollrighthandslot")
    {
        return EquipmentSlot::MainHand;
    }

    if (normalized == "characterdolllefthandslot")
    {
        return EquipmentSlot::OffHand;
    }

    if (normalized == "characterdollarmorslot")
    {
        return EquipmentSlot::Armor;
    }

    if (normalized == "characterdollhelmetslot")
    {
        return EquipmentSlot::Helm;
    }

    if (normalized == "characterdollbeltslot")
    {
        return EquipmentSlot::Belt;
    }

    if (normalized == "characterdollcloakslot")
    {
        return EquipmentSlot::Cloak;
    }

    if (normalized == "characterdollbootsslot")
    {
        return EquipmentSlot::Boots;
    }

    if (normalized == "characterdollamuletslot")
    {
        return EquipmentSlot::Amulet;
    }

    if (normalized == "characterdollgauntletsslot")
    {
        return EquipmentSlot::Gauntlets;
    }

    if (normalized == "characterdollring1slot")
    {
        return EquipmentSlot::Ring1;
    }

    if (normalized == "characterdollring2slot")
    {
        return EquipmentSlot::Ring2;
    }

    if (normalized == "characterdollring3slot")
    {
        return EquipmentSlot::Ring3;
    }

    if (normalized == "characterdollring4slot")
    {
        return EquipmentSlot::Ring4;
    }

    if (normalized == "characterdollring5slot")
    {
        return EquipmentSlot::Ring5;
    }

    if (normalized == "characterdollring6slot")
    {
        return EquipmentSlot::Ring6;
    }

    return std::nullopt;
}

const char *equipmentSlotName(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return "OffHand";
        case EquipmentSlot::MainHand:
            return "MainHand";
        case EquipmentSlot::Bow:
            return "Bow";
        case EquipmentSlot::Armor:
            return "Armor";
        case EquipmentSlot::Helm:
            return "Helm";
        case EquipmentSlot::Belt:
            return "Belt";
        case EquipmentSlot::Cloak:
            return "Cloak";
        case EquipmentSlot::Gauntlets:
            return "Gauntlets";
        case EquipmentSlot::Boots:
            return "Boots";
        case EquipmentSlot::Amulet:
            return "Amulet";
        case EquipmentSlot::Ring1:
            return "Ring1";
        case EquipmentSlot::Ring2:
            return "Ring2";
        case EquipmentSlot::Ring3:
            return "Ring3";
        case EquipmentSlot::Ring4:
            return "Ring4";
        case EquipmentSlot::Ring5:
            return "Ring5";
        case EquipmentSlot::Ring6:
            return "Ring6";
    }

    return "Unknown";
}

void logCharacterEquipmentRender(
    const std::string &renderKey,
    const std::string &parentId,
    const std::string &assetName,
    float x,
    float y,
    float width,
    float height,
    int zIndex,
    float logicalX,
    float logicalY,
    float logicalWidth,
    float logicalHeight)
{
    static_cast<void>(renderKey);
    static_cast<void>(parentId);
    static_cast<void>(assetName);
    static_cast<void>(x);
    static_cast<void>(y);
    static_cast<void>(width);
    static_cast<void>(height);
    static_cast<void>(zIndex);
    static_cast<void>(logicalX);
    static_cast<void>(logicalY);
    static_cast<void>(logicalWidth);
    static_cast<void>(logicalHeight);
}

std::optional<uint32_t> parseCharacterDataIdFromPortraitTextureName(const std::string &portraitTextureName)
{
    const std::string normalized = toLowerCopy(portraitTextureName);

    if (normalized.size() < 4 || !normalized.starts_with("pc"))
    {
        return std::nullopt;
    }

    std::string digits;

    for (size_t index = 2; index < normalized.size(); ++index)
    {
        const unsigned char character = static_cast<unsigned char>(normalized[index]);

        if (!std::isdigit(character))
        {
            break;
        }

        digits.push_back(normalized[index]);
    }

    if (digits.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(digits.c_str(), &pEnd, 10);

    if (pEnd == digits.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(parsed);
}

const CharacterDollEntry *resolveCharacterDollEntry(
    const CharacterDollTable *pCharacterDollTable,
    const Character *pCharacter)
{
    if (pCharacterDollTable == nullptr || pCharacter == nullptr)
    {
        return nullptr;
    }

    if (pCharacter->characterDataId != 0)
    {
        const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(pCharacter->characterDataId);

        if (pEntry != nullptr)
        {
            return pEntry;
        }
    }

    const std::optional<uint32_t> portraitCharacterDataId =
        parseCharacterDataIdFromPortraitTextureName(pCharacter->portraitTextureName);

    if (portraitCharacterDataId)
    {
        const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(*portraitCharacterDataId);

        if (pEntry != nullptr)
        {
            return pEntry;
        }
    }

    return pCharacterDollTable->getCharacter(1);
}

std::string skillPageMasteryDisplayName(SkillMastery mastery)
{
    const std::string displayName = masteryDisplayName(mastery);

    if (displayName == "Grandmaster")
    {
        return "Grand";
    }

    return displayName;
}

void appendCharacterSkillUiRows(
    const Character &character,
    std::vector<CharacterSkillUiRow> &rows,
    std::unordered_set<std::string> &shownSkillNames,
    const char *const *pSkillNames,
    size_t skillCount)
{
    for (size_t skillIndex = 0; skillIndex < skillCount; ++skillIndex)
    {
        const std::string canonicalName = canonicalSkillName(pSkillNames[skillIndex]);
        const CharacterSkill *pSkill = character.findSkill(canonicalName);

        if (pSkill == nullptr)
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = displaySkillName(pSkill->name);

        if (pSkill->mastery != SkillMastery::None && pSkill->mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(pSkill->mastery);
        }

        row.level = std::to_string(pSkill->level);
        row.upgradeable = character.skillPoints > pSkill->level;
        rows.push_back(std::move(row));
        shownSkillNames.insert(canonicalName);
    }
}

CharacterSkillUiData buildCharacterSkillUiData(const Character *pCharacter)
{
    CharacterSkillUiData data = {};

    if (pCharacter == nullptr)
    {
        return data;
    }

    std::unordered_set<std::string> shownSkillNames;
    appendCharacterSkillUiRows(
        *pCharacter,
        data.weaponRows,
        shownSkillNames,
        WeaponSkillNames,
        std::size(WeaponSkillNames));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.magicRows,
        shownSkillNames,
        MagicSkillNames,
        std::size(MagicSkillNames));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.armorRows,
        shownSkillNames,
        ArmorSkillNames,
        std::size(ArmorSkillNames));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.miscRows,
        shownSkillNames,
        MiscSkillNames,
        std::size(MiscSkillNames));

    std::vector<CharacterSkillUiRow> extraMiscRows;

    for (const auto &[ignoredSkillName, skill] : pCharacter->skills)
    {
        static_cast<void>(ignoredSkillName);
        const std::string canonicalName = canonicalSkillName(skill.name);

        if (shownSkillNames.contains(canonicalName))
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = displaySkillName(skill.name);

        if (skill.mastery != SkillMastery::None && skill.mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(skill.mastery);
        }

        row.level = std::to_string(skill.level);
        row.upgradeable = pCharacter->skillPoints > skill.level;
        extraMiscRows.push_back(std::move(row));
    }

    std::sort(
        extraMiscRows.begin(),
        extraMiscRows.end(),
        [](const CharacterSkillUiRow &left, const CharacterSkillUiRow &right)
        {
            return left.label < right.label;
        });

    data.miscRows.insert(data.miscRows.end(), extraMiscRows.begin(), extraMiscRows.end());
    return data;
}

bool isBodyEquipmentVisualSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
        case EquipmentSlot::MainHand:
        case EquipmentSlot::Bow:
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Gauntlets:
        case EquipmentSlot::Boots:
            return true;

        case EquipmentSlot::Amulet:
        case EquipmentSlot::Ring1:
        case EquipmentSlot::Ring2:
        case EquipmentSlot::Ring3:
        case EquipmentSlot::Ring4:
        case EquipmentSlot::Ring5:
        case EquipmentSlot::Ring6:
            return false;
    }

    return false;
}

bool isJewelryOverlayEquipmentSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::Gauntlets:
        case EquipmentSlot::Amulet:
        case EquipmentSlot::Ring1:
        case EquipmentSlot::Ring2:
        case EquipmentSlot::Ring3:
        case EquipmentSlot::Ring4:
        case EquipmentSlot::Ring5:
        case EquipmentSlot::Ring6:
            return true;

        case EquipmentSlot::OffHand:
        case EquipmentSlot::MainHand:
        case EquipmentSlot::Bow:
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Boots:
            return false;
    }

    return false;
}

bool isVisibleInCharacterDollOverlay(EquipmentSlot slot, bool jewelryOverlayOpen)
{
    return jewelryOverlayOpen ? isJewelryOverlayEquipmentSlot(slot) : !isJewelryOverlayEquipmentSlot(slot);
}

bool usesAlternateCloakBeltEquippedVariant(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Cloak || slot == EquipmentSlot::Belt;
}

void setCharacterSkillRegionHeight(
    std::unordered_map<std::string, float> &runtimeHeightOverrides,
    float skillRowHeight,
    const char *pLayoutId,
    size_t rowCount)
{
    runtimeHeightOverrides[toLowerCopy(pLayoutId)] =
        skillRowHeight * static_cast<float>(std::max<size_t>(1, rowCount));
}

std::string formatMonsterDamageText(const MonsterTable::MonsterStatsEntry::DamageProfile &damage)
{
    if (damage.diceRolls <= 0 || damage.diceSides <= 0)
    {
        return "-";
    }

    std::string text = std::to_string(damage.diceRolls) + "D" + std::to_string(damage.diceSides);

    if (damage.bonus > 0)
    {
        text += "+" + std::to_string(damage.bonus);
    }
    else if (damage.bonus < 0)
    {
        text += std::to_string(damage.bonus);
    }

    return text;
}

std::string joinNonEmptyTexts(const std::vector<std::string> &parts)
{
    std::string result;

    for (const std::string &part : parts)
    {
        if (part.empty() || part == "-" || part == "0")
        {
            continue;
        }

        if (!result.empty())
        {
            result += ", ";
        }

        result += part;
    }

    return result.empty() ? "-" : result;
}

std::string formatMonsterResistanceText(int value)
{
    return value >= 200 ? "Imm" : std::to_string(value);
}

std::string resolveItemInspectTypeText(const InventoryItem *pItemState, const ItemDefinition &itemDefinition)
{
    if (pItemState != nullptr && !pItemState->identified && ItemRuntime::requiresIdentification(itemDefinition))
    {
        return "Not identified";
    }

    if (!itemDefinition.skillGroup.empty()
        && itemDefinition.skillGroup != "0"
        && itemDefinition.skillGroup != "Misc")
    {
        return itemDefinition.skillGroup;
    }

    if (!itemDefinition.equipStat.empty()
        && itemDefinition.equipStat != "0"
        && itemDefinition.equipStat != "N / A")
    {
        return itemDefinition.equipStat;
    }

    return "Misc";
}

std::string formatItemInspectDamageText(const std::string &damageDice, int bonus)
{
    if (damageDice.empty() || damageDice == "0")
    {
        if (bonus <= 0)
        {
            return {};
        }

        return std::to_string(bonus);
    }

    if (bonus <= 0)
    {
        return damageDice;
    }

    return damageDice + "+" + std::to_string(bonus);
}

std::string resolveItemInspectDetailText(const InventoryItem *pItemState, const ItemDefinition &itemDefinition)
{
    const bool isBroken = pItemState != nullptr && pItemState->broken;
    const std::string &equipStat = itemDefinition.equipStat;
    int mod1Value = 0;
    int mod2Value = 0;
    const bool hasMod1Int = tryParseInteger(itemDefinition.mod1, mod1Value);
    const bool hasMod2Int = tryParseInteger(itemDefinition.mod2, mod2Value);

    if (equipStat == "Weapon" || equipStat == "Weapon2" || equipStat == "Weapon1or2")
    {
        const int attackBonus = hasMod2Int ? mod2Value : 0;
        const std::string damageText = formatItemInspectDamageText(itemDefinition.mod1, attackBonus);

        if (damageText.empty())
        {
            return isBroken ? "Broken" : std::string {};
        }

        const std::string detail = "Attack: +" + std::to_string(attackBonus) + "   Damage: " + damageText;
        return isBroken ? "Broken   " + detail : detail;
    }

    if (equipStat == "Missile")
    {
        const int shootBonus = hasMod2Int ? mod2Value : 0;
        const std::string damageText = formatItemInspectDamageText(itemDefinition.mod1, shootBonus);

        if (damageText.empty())
        {
            return isBroken ? "Broken" : std::string {};
        }

        const std::string detail = "Shoot: +" + std::to_string(shootBonus) + "   Damage: " + damageText;
        return isBroken ? "Broken   " + detail : detail;
    }

    if (equipStat == "WeaponW")
    {
        if (hasMod2Int && mod2Value > 0)
        {
            const std::string detail = "Charges: " + std::to_string(mod2Value);
            return isBroken ? "Broken   " + detail : detail;
        }

        return isBroken ? "Broken" : std::string {};
    }

    if (equipStat == "Armor"
        || equipStat == "Shield"
        || equipStat == "Helm"
        || equipStat == "Belt"
        || equipStat == "Cloak"
        || equipStat == "Gauntlets"
        || equipStat == "Boots"
        || equipStat == "Ring"
        || equipStat == "Amulet")
    {
        const int armorValue = (hasMod1Int ? mod1Value : 0) + (hasMod2Int ? mod2Value : 0);

        if (armorValue > 0)
        {
            const std::string detail = "Armor: +" + std::to_string(armorValue);
            return isBroken ? "Broken   " + detail : detail;
        }

        return isBroken ? "Broken" : std::string {};
    }

    return isBroken ? "Broken" : std::string {};
}

void setupHudProjection(int width, int height)
{
    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);
}

} // namespace

void GameplayPartyOverlayRenderer::renderSpellbookOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_spellbook.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "SpellbookRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedRoot = HudUiService::resolveHudLayoutElement(view, 
        "SpellbookRoot",
        width,
        height,
        pRootLayout->width,
        pRootLayout->height);

    if (!resolvedRoot)
    {
        return;
    }

    const auto loadHudTexture =
        [&view](const std::string &textureName) -> const OutdoorGameView::HudTextureHandle *
        {
            return HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), textureName);
        };

    setupHudProjection(width, height);

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto submitTexturedQuad =
        [&view](const OutdoorGameView::HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            view.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
        };

    const auto renderLayoutPrimaryAsset =
        [&view, width, height, &loadHudTexture, &submitTexturedQuad](const std::string &layoutId)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pTexture = loadHudTexture(pLayout->primaryAsset);

            if (pTexture == nullptr)
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                layoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pTexture->height));

            if (!resolved)
            {
                return;
            }

            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        };

    const SpellbookSchoolUiDefinition *pSchoolDefinition = findSpellbookSchoolUiDefinition(view.m_spellbook.school);

    if (pSchoolDefinition == nullptr || !view.activeMemberHasSpellbookSchool(view.m_spellbook.school))
    {
        return;
    }

    renderLayoutPrimaryAsset(pSchoolDefinition->pPageLayoutId);

    for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
    {
        if (!view.activeMemberHasSpellbookSchool(definition.school))
        {
            continue;
        }

        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, definition.pButtonLayoutId);

        if (pLayout == nullptr || pLayout->primaryAsset.empty())
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pDefaultTexture = loadHudTexture(pLayout->primaryAsset);

        if (pDefaultTexture == nullptr)
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
            definition.pButtonLayoutId,
            width,
            height,
            pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pDefaultTexture->width),
            pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pDefaultTexture->height));

        if (!resolved)
        {
            continue;
        }

        const bool isActive = definition.school == view.m_spellbook.school;
        const std::string *pInteractiveAssetName =
            HudUiService::resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);
        const std::string *pSelectedAssetName =
            !pLayout->pressedAsset.empty()
                ? &pLayout->pressedAsset
                : (!pLayout->hoverAsset.empty() ? &pLayout->hoverAsset : &pLayout->primaryAsset);
        const std::string *pAssetName = isActive ? pSelectedAssetName : pInteractiveAssetName;
        const OutdoorGameView::HudTextureHandle *pTexture =
            pAssetName != nullptr ? loadHudTexture(*pAssetName) : pDefaultTexture;

        if (pTexture != nullptr)
        {
            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }

    const auto renderInteractiveButton =
        [&view, width, height, mouseX, mouseY, isLeftMousePressed, &loadHudTexture, &submitTexturedQuad](
            const std::string &layoutId)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pDefaultTexture = loadHudTexture(pLayout->primaryAsset);

            if (pDefaultTexture == nullptr)
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                layoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pDefaultTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pDefaultTexture->height));

            if (!resolved)
            {
                return;
            }

            const std::string *pAssetName =
                HudUiService::resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);
            const OutdoorGameView::HudTextureHandle *pTexture =
                pAssetName != nullptr ? loadHudTexture(*pAssetName) : pDefaultTexture;

            if (pTexture != nullptr)
            {
                submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
            }
        };

    renderInteractiveButton("SpellbookCloseButton");
    renderInteractiveButton("SpellbookQuickCastButton");

    for (uint32_t spellOffset = 0; spellOffset < pSchoolDefinition->spellCount; ++spellOffset)
    {
        const uint32_t spellOrdinal = spellOffset + 1;
        const uint32_t spellId = pSchoolDefinition->firstSpellId + spellOffset;

        if (!view.activeMemberKnowsSpell(spellId))
        {
            continue;
        }

        const std::string layoutId = spellbookSpellLayoutId(view.m_spellbook.school, spellOrdinal);
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pDefaultTexture = loadHudTexture(pLayout->primaryAsset);

        if (pDefaultTexture == nullptr)
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
            layoutId,
            width,
            height,
            pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pDefaultTexture->width),
            pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pDefaultTexture->height));

        if (!resolved)
        {
            continue;
        }

        const bool isSelected = view.m_spellbook.selectedSpellId == spellId;
        const std::string *pInteractiveAssetName =
            HudUiService::resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);
        const std::string *pSelectedAssetName =
            !pLayout->pressedAsset.empty()
                ? &pLayout->pressedAsset
                : (!pLayout->hoverAsset.empty() ? &pLayout->hoverAsset : &pLayout->primaryAsset);
        const std::string *pAssetName = isSelected ? pSelectedAssetName : pInteractiveAssetName;
        const OutdoorGameView::HudTextureHandle *pTexture =
            pAssetName != nullptr ? loadHudTexture(*pAssetName) : pDefaultTexture;

        if (pTexture != nullptr)
        {
            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }
}

void GameplayPartyOverlayRenderer::renderHeldInventoryItem(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_heldInventoryItem.active
        || view.m_pItemTable == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = view.m_pItemTable->get(view.m_heldInventoryItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
    {
        return;
    }

    const OutdoorGameView::HudTextureHandle *pTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pItemDefinition->iconName);

    if (pTexture == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float scale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    SDL_GetMouseState(&mouseX, &mouseY);
    const float itemX = std::round(mouseX - view.m_heldInventoryItem.grabOffsetX);
    const float itemY = std::round(mouseY - view.m_heldInventoryItem.grabOffsetY);
    const float itemWidth = static_cast<float>(pTexture->width) * scale;
    const float itemHeight = static_cast<float>(pTexture->height) * scale;

    view.submitHudTexturedQuad(*pTexture, itemX, itemY, itemWidth, itemHeight);

    const bgfx::TextureHandle tintedTextureHandle =
        HudUiService::ensureHudTextureColor(view, 
            *pTexture,
            itemTintColorAbgr(&view.m_heldInventoryItem.item, pItemDefinition, ItemTintContext::Held));

    if (bgfx::isValid(tintedTextureHandle) && tintedTextureHandle.idx != pTexture->textureHandle.idx)
    {
        OutdoorGameView::HudTextureHandle tintedTexture = *pTexture;
        tintedTexture.textureHandle = tintedTextureHandle;
        view.submitHudTexturedQuad(tintedTexture, itemX, itemY, itemWidth, itemHeight);
    }
}

void GameplayPartyOverlayRenderer::renderItemInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_itemInspectOverlay.active
        || view.m_pItemTable == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_programHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = view.m_pItemTable->get(view.m_itemInspectOverlay.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "ItemInspectRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const InventoryItem *pItemState = view.m_itemInspectOverlay.hasItemState ? &view.m_itemInspectOverlay.itemState : nullptr;
    InventoryItem defaultItemState = {};
    defaultItemState.objectDescriptionId = view.m_itemInspectOverlay.objectDescriptionId;
    defaultItemState.identified = true;
    const InventoryItem &resolvedItemState = pItemState != nullptr ? *pItemState : defaultItemState;
    const bool showBrokenOnly = pItemState != nullptr && pItemState->broken;
    const bool showUnidentifiedOnly =
        !showBrokenOnly
        && pItemState != nullptr
        && !pItemState->identified
        && ItemRuntime::requiresIdentification(*pItemDefinition);
    const std::string itemName = ItemRuntime::displayName(
        resolvedItemState,
        *pItemDefinition,
        view.m_pStandardItemEnchantTable,
        view.m_pSpecialItemEnchantTable);
    const std::string itemType =
        showBrokenOnly || showUnidentifiedOnly ? std::string {} : resolveItemInspectTypeText(pItemState, *pItemDefinition);
    const std::string itemDetail =
        showBrokenOnly || showUnidentifiedOnly ? std::string {} : resolveItemInspectDetailText(pItemState, *pItemDefinition);
    const std::string enchantDescription = ItemEnchantRuntime::buildEnchantDescription(
        resolvedItemState,
        view.m_pStandardItemEnchantTable,
        view.m_pSpecialItemEnchantTable);
    const std::string itemSpecialDetail =
        showBrokenOnly || showUnidentifiedOnly || enchantDescription.empty() ? std::string {} : "Special: " + enchantDescription;
    const std::string itemDescription = showBrokenOnly ? "Broken item" : (showUnidentifiedOnly ? "Not identified" : pItemDefinition->notes);
    const int resolvedItemValue =
        view.m_itemInspectOverlay.hasValueOverride
            ? view.m_itemInspectOverlay.valueOverride
            : PriceCalculator::itemValue(
                resolvedItemState,
                *pItemDefinition,
                view.m_pStandardItemEnchantTable,
                view.m_pSpecialItemEnchantTable);
    const std::string itemValue = std::to_string(std::max(0, resolvedItemValue));
    const OutdoorGameView::HudTextureHandle *pItemTexture =
        !pItemDefinition->iconName.empty()
            ? HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pItemDefinition->iconName)
            : nullptr;
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;

    const OutdoorGameView::HudLayoutElement *pPreviewLayout = HudUiService::findHudLayoutElement(view, "ItemInspectPreviewImage");
    const OutdoorGameView::HudLayoutElement *pTypeLayout = HudUiService::findHudLayoutElement(view, "ItemInspectType");
    const OutdoorGameView::HudLayoutElement *pDetailRowLayout = HudUiService::findHudLayoutElement(view, "ItemInspectDetailRow");
    const OutdoorGameView::HudLayoutElement *pDetailValueLayout = HudUiService::findHudLayoutElement(view, "ItemInspectDetailValue");
    const OutdoorGameView::HudLayoutElement *pDescriptionLayout = HudUiService::findHudLayoutElement(view, "ItemInspectDescription");
    const OutdoorGameView::HudLayoutElement *pValueLayout = HudUiService::findHudLayoutElement(view, "ItemInspectValue");

    if (pPreviewLayout == nullptr
        || pTypeLayout == nullptr
        || pDetailRowLayout == nullptr
        || pDetailValueLayout == nullptr
        || pDescriptionLayout == nullptr
        || pValueLayout == nullptr)
    {
        return;
    }

    const float previewImageWidth =
        pItemTexture != nullptr ? static_cast<float>(pItemTexture->width) * popupScale : pPreviewLayout->width * popupScale;
    const float previewImageHeight =
        pItemTexture != nullptr ? static_cast<float>(pItemTexture->height) * popupScale : pPreviewLayout->height * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::ResolvedHudLayoutElement previewRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pPreviewLayout->attachTo,
        provisionalRoot,
        previewImageWidth,
        previewImageHeight,
        pPreviewLayout->gapX,
        pPreviewLayout->gapY,
        popupScale);
    const OutdoorGameView::ResolvedHudLayoutElement typeRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pTypeLayout->attachTo,
        provisionalRoot,
        pTypeLayout->width * popupScale,
        pTypeLayout->height * popupScale,
        pTypeLayout->gapX,
        pTypeLayout->gapY,
        popupScale);
    const OutdoorGameView::ResolvedHudLayoutElement descriptionRectForSizing =
        OutdoorGameView::resolveAttachedHudLayoutRect(
            pDescriptionLayout->attachTo,
            provisionalRoot,
            pDescriptionLayout->width * popupScale,
            pDescriptionLayout->height * popupScale,
            pDescriptionLayout->gapX,
            pDescriptionLayout->gapY,
            popupScale);
    const float descriptionWidthScaled =
        std::max(0.0f, descriptionRectForSizing.width - std::abs(pDescriptionLayout->textPadX * popupScale) * 2.0f);
    const float descriptionWidth = std::max(0.0f, descriptionWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> descriptionLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, itemDescription, descriptionWidth)
            : std::vector<std::string>{itemDescription};
    const bool showDetail = !itemDetail.empty();
    const bool showSpecialDetail = !itemSpecialDetail.empty();
    const float descriptionHeight =
        itemDescription.empty() || descriptionLines.empty() ? 0.0f : bodyLineHeight * static_cast<float>(descriptionLines.size());
    const float detailRowHeight = pDetailRowLayout->height * popupScale;
    const OutdoorGameView::HudFontHandle *pDetailFont = HudUiService::findHudFont(view, pDetailValueLayout->fontName);
    float detailFontScale = popupScale * std::max(0.1f, pDetailValueLayout->textScale);

    if (detailFontScale >= 1.0f)
    {
        detailFontScale = snappedHudFontScale(detailFontScale);
    }
    else
    {
        detailFontScale = std::max(0.5f, detailFontScale);
    }

    const float detailLineHeight =
        pDetailFont != nullptr ? static_cast<float>(pDetailFont->fontHeight) * detailFontScale : detailRowHeight;
    const float detailTextWidthScaled = std::max(
        0.0f,
        pDetailValueLayout->width * popupScale - std::abs(pDetailValueLayout->textPadX * popupScale) * 2.0f);
    const float detailTextWidth = std::max(0.0f, detailTextWidthScaled / std::max(0.1f, detailFontScale));
    const std::vector<std::string> specialDetailLines =
        showSpecialDetail && pDetailFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pDetailFont, itemSpecialDetail, detailTextWidth)
            : std::vector<std::string>{itemSpecialDetail};
    const float specialDetailHeight = showSpecialDetail
        ? std::max(detailRowHeight, detailLineHeight * static_cast<float>(std::max<size_t>(1, specialDetailLines.size())))
        : 0.0f;
    const int detailRowCount = (showDetail ? 1 : 0) + (showSpecialDetail ? 1 : 0);
    static constexpr float ItemInspectTypeToDetailGap = 3.0f;
    static constexpr float ItemInspectDetailToDescriptionGap = 8.0f;
    static constexpr float ItemInspectDescriptionToValueGap = 8.0f;
    static constexpr float ItemInspectBottomPadding = 8.0f;
    const float detailSectionHeight = detailRowCount > 0
        ? ItemInspectTypeToDetailGap * popupScale
            + (showDetail ? detailRowHeight : 0.0f)
            + (showSpecialDetail ? specialDetailHeight : 0.0f)
            + ItemInspectTypeToDetailGap * popupScale * static_cast<float>(detailRowCount - 1)
        : 0.0f;
    const float descriptionSectionHeight =
        descriptionHeight > 0.0f ? ItemInspectDetailToDescriptionGap * popupScale + descriptionHeight : 0.0f;
    const float previewContentHeight = previewImageHeight + 20.0f * popupScale;
    const float textContentHeight =
        typeRectForSizing.y
        + typeRectForSizing.height
        + detailSectionHeight
        + descriptionSectionHeight
        + ItemInspectDescriptionToValueGap * popupScale
        + pValueLayout->height * popupScale
        + ItemInspectBottomPadding * popupScale;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(previewContentHeight, textContentHeight);
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_itemInspectOverlay.sourceX + view.m_itemInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_itemInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_itemInspectOverlay.sourceY + (view.m_itemInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveItemInspectLayout =
        [&view,
         &rootRect,
         &resolveItemInspectLayout,
         previewImageWidth,
         previewImageHeight,
         popupScale](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            const std::string normalizedLayoutId = toLowerCopy(layoutId);
            const OutdoorGameView::HudTextureHandle *pBaseTexture = nullptr;

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                pBaseTexture = HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
            }

            float resolvedWidth =
                normalizedLayoutId == "iteminspectpreviewimage"
                    ? previewImageWidth
                    : (pLayout->width > 0.0f
                        ? pLayout->width * popupScale
                        : (pBaseTexture != nullptr ? static_cast<float>(pBaseTexture->width) * popupScale : 0.0f));
            float resolvedHeight =
                normalizedLayoutId == "iteminspectpreviewimage"
                    ? previewImageHeight
                    : (pLayout->height > 0.0f
                        ? pLayout->height * popupScale
                        : (pBaseTexture != nullptr ? static_cast<float>(pBaseTexture->height) * popupScale : 0.0f));

            if (normalizedLayoutId == "iteminspectcorner_topedge"
                || normalizedLayoutId == "iteminspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "iteminspectcorner_leftedge"
                || normalizedLayoutId == "iteminspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            if (pLayout->parentId.empty() || toLowerCopy(pLayout->parentId) == "iteminspectroot")
            {
                return OutdoorGameView::resolveAttachedHudLayoutRect(
                    pLayout->attachTo,
                    rootRect,
                    resolvedWidth,
                    resolvedHeight,
                    pLayout->gapX,
                    pLayout->gapY,
                    popupScale);
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> parentRect =
                resolveItemInspectLayout(pLayout->parentId);

            if (!parentRect)
            {
                return std::nullopt;
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                *parentRect,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const auto isItemInspectRootDescendant =
        [&view](const OutdoorGameView::HudLayoutElement &layout) -> bool
        {
            std::string currentLayoutId = layout.id;

            while (!currentLayoutId.empty())
            {
                if (toLowerCopy(currentLayoutId) == "iteminspectroot")
                {
                    return true;
                }

                const OutdoorGameView::HudLayoutElement *pCurrentLayout = HudUiService::findHudLayoutElement(view, currentLayoutId);

                if (pCurrentLayout == nullptr || pCurrentLayout->parentId.empty())
                {
                    break;
                }

                currentLayoutId = pCurrentLayout->parentId;
            }

            return false;
        };

    const std::vector<std::string> orderedItemInspectLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "ItemInspect");

    for (const std::string &layoutId : orderedItemInspectLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "iteminspectroot"
            || toLowerCopy(pLayout->id) == "iteminspectpreviewimage"
            || !isItemInspectRootDescendant(*pLayout))
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveItemInspectLayout(layoutId);

        if (pTexture == nullptr || !resolved || resolved->width <= 0.0f || resolved->height <= 0.0f)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderSingleLine =
        [&view, &resolveItemInspectLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveItemInspectLayout(pLayoutId);

            if (pLayout == nullptr || !resolved)
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    renderSingleLine("ItemInspectName", itemName);
    renderSingleLine("ItemInspectType", "Type: " + itemType);

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> previewRect =
        resolveItemInspectLayout("ItemInspectPreviewImage");

    if (previewRect && pItemTexture != nullptr && pItemTexture->width > 0 && pItemTexture->height > 0)
    {
        view.submitHudTexturedQuad(*pItemTexture, previewRect->x, previewRect->y, previewRect->width, previewRect->height);
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> typeRect = resolveItemInspectLayout("ItemInspectType");
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> detailRowBaseRect =
        resolveItemInspectLayout("ItemInspectDetailRow");
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> descriptionBaseRect =
        resolveItemInspectLayout("ItemInspectDescription");
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> valueBaseRect =
        resolveItemInspectLayout("ItemInspectValue");

    if (showDetail && typeRect && detailRowBaseRect)
    {
        OutdoorGameView::ResolvedHudLayoutElement detailRowRect = *detailRowBaseRect;
        detailRowRect.y = std::round(typeRect->y + typeRect->height + ItemInspectTypeToDetailGap * popupScale);
        const OutdoorGameView::ResolvedHudLayoutElement detailValueRect = OutdoorGameView::resolveAttachedHudLayoutRect(
            pDetailValueLayout->attachTo,
            detailRowRect,
            pDetailValueLayout->width * popupScale,
            pDetailValueLayout->height * popupScale,
            pDetailValueLayout->gapX,
            pDetailValueLayout->gapY,
            popupScale);
        HudUiService::renderLayoutLabel(view, *pDetailValueLayout, detailValueRect, itemDetail);
    }

    if (showSpecialDetail && typeRect && detailRowBaseRect)
    {
        OutdoorGameView::ResolvedHudLayoutElement specialRowRect = *detailRowBaseRect;
        specialRowRect.y = std::round(
            typeRect->y
            + typeRect->height
            + ItemInspectTypeToDetailGap * popupScale
            + (showDetail ? detailRowHeight + ItemInspectTypeToDetailGap * popupScale : 0.0f));
        specialRowRect.height = std::round(specialDetailHeight);
        const OutdoorGameView::ResolvedHudLayoutElement specialValueRect =
            OutdoorGameView::resolveAttachedHudLayoutRect(
                pDetailValueLayout->attachTo,
                specialRowRect,
                pDetailValueLayout->width * popupScale,
                specialRowRect.height,
                pDetailValueLayout->gapX,
                pDetailValueLayout->gapY,
                popupScale);

        if (pDetailFont != nullptr && !specialDetailLines.empty())
        {
            bgfx::TextureHandle coloredMainTextureHandle =
                HudUiService::ensureHudFontMainTextureColor(view, *pDetailFont, pDetailValueLayout->textColorAbgr);

            if (!bgfx::isValid(coloredMainTextureHandle))
            {
                coloredMainTextureHandle = pDetailFont->mainTextureHandle;
            }

            const float totalSpecialTextHeight =
                detailLineHeight * static_cast<float>(std::max<size_t>(1, specialDetailLines.size()));
            float textX = std::round(specialValueRect.x + pDetailValueLayout->textPadX * popupScale);
            float textY = specialValueRect.y + pDetailValueLayout->textPadY * popupScale;

            switch (pDetailValueLayout->textAlignY)
            {
                case OutdoorGameView::HudTextAlignY::Top:
                    break;

                case OutdoorGameView::HudTextAlignY::Middle:
                    textY =
                        specialValueRect.y
                        + (specialValueRect.height - totalSpecialTextHeight) * 0.5f
                        + pDetailValueLayout->textPadY * popupScale;
                    break;

                case OutdoorGameView::HudTextAlignY::Bottom:
                    textY =
                        specialValueRect.y
                        + specialValueRect.height
                        - totalSpecialTextHeight
                        + pDetailValueLayout->textPadY * popupScale;
                    break;
            }

            textY = std::round(textY);

            for (const std::string &wrappedLine : specialDetailLines)
            {
                HudUiService::renderHudFontLayer(view, *pDetailFont, pDetailFont->shadowTextureHandle, wrappedLine, textX, textY, detailFontScale);
                HudUiService::renderHudFontLayer(view, *pDetailFont, coloredMainTextureHandle, wrappedLine, textX, textY, detailFontScale);
                textY += detailLineHeight;
            }
        }
        else
        {
            HudUiService::renderLayoutLabel(view, *pDetailValueLayout, specialValueRect, itemSpecialDetail);
        }
    }

    const float dynamicDescriptionY = typeRect
        ? std::round(
            typeRect->y
            + typeRect->height
            + detailSectionHeight
            + (descriptionHeight > 0.0f ? ItemInspectDetailToDescriptionGap * popupScale : 0.0f))
        : 0.0f;
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedDescription =
        descriptionBaseRect
            ? std::optional<OutdoorGameView::ResolvedHudLayoutElement>(OutdoorGameView::ResolvedHudLayoutElement{
                descriptionBaseRect->x,
                dynamicDescriptionY,
                descriptionBaseRect->width,
                descriptionBaseRect->height,
                descriptionBaseRect->scale})
            : std::nullopt;

    if (!itemDescription.empty() && pBodyFont != nullptr && resolvedDescription)
    {
        bgfx::TextureHandle coloredMainTextureHandle =
            HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pDescriptionLayout->textColorAbgr);

        if (!bgfx::isValid(coloredMainTextureHandle))
        {
            coloredMainTextureHandle = pBodyFont->mainTextureHandle;
        }

        float textX = std::round(resolvedDescription->x + pDescriptionLayout->textPadX * popupScale);
        float textY = std::round(resolvedDescription->y + pDescriptionLayout->textPadY * popupScale);

        for (const std::string &line : descriptionLines)
        {
            HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
            HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
            textY += bodyLineHeight;
        }
    }

    if (valueBaseRect)
    {
        OutdoorGameView::ResolvedHudLayoutElement valueRect = *valueBaseRect;
        const float minimumValueY = dynamicDescriptionY + descriptionHeight + ItemInspectDescriptionToValueGap * popupScale;
        const float anchoredValueY =
            rootRect.y + rootRect.height - ItemInspectBottomPadding * popupScale - valueRect.height;
        valueRect.y = std::round(std::max(minimumValueY, anchoredValueY));
        HudUiService::renderLayoutLabel(view, *pValueLayout, valueRect, "Value: " + itemValue);
    }
}

void GameplayPartyOverlayRenderer::renderCharacterInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_characterInspectOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectBody");
    const OutdoorGameView::HudLayoutElement *pExpertLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectExpert");
    const OutdoorGameView::HudLayoutElement *pMasterLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectMaster");
    const OutdoorGameView::HudLayoutElement *pGrandmasterLayout =
        HudUiService::findHudLayoutElement(view, "CharacterInspectGrandmaster");

    if (pRootLayout == nullptr
        || pTitleLayout == nullptr
        || pBodyLayout == nullptr
        || pExpertLayout == nullptr
        || pMasterLayout == nullptr
        || pGrandmasterLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_characterInspectOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_characterInspectOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    const bool showExpert =
        view.m_characterInspectOverlay.expert.visible && !view.m_characterInspectOverlay.expert.text.empty();
    const bool showMaster =
        view.m_characterInspectOverlay.master.visible && !view.m_characterInspectOverlay.master.text.empty();
    const bool showGrandmaster =
        view.m_characterInspectOverlay.grandmaster.visible && !view.m_characterInspectOverlay.grandmaster.text.empty();
    static constexpr float CharacterInspectBodyToRowsGap = 10.0f;
    static constexpr float CharacterInspectRowGap = 2.0f;
    static constexpr float CharacterInspectBottomPadding = 15.0f;

    const auto resolveWrappedMasteryLines =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::string &text) -> std::vector<std::string>
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

            if (pFont == nullptr)
            {
                return {text};
            }

            const float maxWidthScaled =
                std::max(0.0f, layout.width * popupScale - std::abs(layout.textPadX * popupScale) * 2.0f);
            const float maxWidth = std::max(0.0f, maxWidthScaled / std::max(1.0f, popupScale));
            return HudUiService::wrapHudTextToWidth(view, *pFont, text, maxWidth);
        };

    const auto masteryRowHeight =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::vector<std::string> &lines) -> float
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);
            const float lineHeight =
                pFont != nullptr ? static_cast<float>(pFont->fontHeight) * popupScale : layout.height * popupScale;
            return std::max(lineHeight, lineHeight * static_cast<float>(std::max<size_t>(1, lines.size())));
        };

    const std::vector<std::string> expertLines =
        showExpert
            ? resolveWrappedMasteryLines(*pExpertLayout, view.m_characterInspectOverlay.expert.text)
            : std::vector<std::string>{};
    const std::vector<std::string> masterLines =
        showMaster
            ? resolveWrappedMasteryLines(*pMasterLayout, view.m_characterInspectOverlay.master.text)
            : std::vector<std::string>{};
    const std::vector<std::string> grandmasterLines =
        showGrandmaster
            ? resolveWrappedMasteryLines(*pGrandmasterLayout, view.m_characterInspectOverlay.grandmaster.text)
            : std::vector<std::string>{};
    float masteryHeight = 0.0f;
    bool hasAnyMasteryRows = false;

    for (const auto &[showRow, pLayout, pLines] : {
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showExpert, pExpertLayout, &expertLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showMaster, pMasterLayout, &masterLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showGrandmaster, pGrandmasterLayout, &grandmasterLines}})
    {
        if (!showRow)
        {
            continue;
        }

        if (hasAnyMasteryRows)
        {
            masteryHeight += CharacterInspectRowGap * popupScale;
        }

        masteryHeight += masteryRowHeight(*pLayout, *pLines);
        hasAnyMasteryRows = true;
    }

    const float rootWidth = provisionalRoot.width;
    const float rootHeight =
        bodyRectForSizing.y
        + bodyHeight
        + (hasAnyMasteryRows ? CharacterInspectBodyToRowsGap * popupScale + masteryHeight : 0.0f)
        + CharacterInspectBottomPadding * popupScale;
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_characterInspectOverlay.sourceX + view.m_characterInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_characterInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY =
        view.m_characterInspectOverlay.sourceY + (view.m_characterInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture =
                    HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "characterinspectcorner_topedge"
                || normalizedLayoutId == "characterinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "characterinspectcorner_leftedge"
                || normalizedLayoutId == "characterinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "characterinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent =
                    resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "CharacterInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "characterinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderSingleLine =
        [&view, &resolveLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(pLayoutId);

            if (pLayout == nullptr || !resolved || text.empty())
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    renderSingleLine("CharacterInspectTitle", view.m_characterInspectOverlay.title);

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("CharacterInspectBody");

    if (bodyBaseRect && pBodyFont != nullptr)
    {
        bgfx::TextureHandle coloredMainTextureHandle =
            HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

        if (!bgfx::isValid(coloredMainTextureHandle))
        {
            coloredMainTextureHandle = pBodyFont->mainTextureHandle;
        }

        float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
        float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

        for (const std::string &line : bodyLines)
        {
            HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
            HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
            textY += bodyLineHeight;
        }

        const auto masteryColorForAvailability =
            [](int availability) -> uint32_t
            {
                switch (availability)
                {
                    case 0:
                        return 0xffffffffu;

                    case 1:
                        return packHudColorAbgr(255, 255, 0);

                    case 2:
                        return packHudColorAbgr(255, 0, 0);

                    default:
                        return 0xffffffffu;
                }
            };

        float nextRowY = std::round(bodyBaseRect->y + bodyHeight + CharacterInspectBodyToRowsGap * popupScale);
        const auto renderMasteryRow =
            [&view, popupScale, &masteryColorForAvailability](
                const OutdoorGameView::HudLayoutElement &baseLayout,
                const OutdoorGameView::ResolvedHudLayoutElement &baseResolved,
                float rowY,
                const OutdoorGameView::CharacterInspectMasteryLine &line,
                const std::vector<std::string> &wrappedLines) -> float
            {
                if (!line.visible || line.text.empty())
                {
                    return rowY;
                }

                const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, baseLayout.fontName);

                if (pFont == nullptr)
                {
                    return rowY;
                }

                bgfx::TextureHandle coloredMainTextureHandle =
                    HudUiService::ensureHudFontMainTextureColor(view, 
                        *pFont,
                        masteryColorForAvailability(line.availability));

                if (!bgfx::isValid(coloredMainTextureHandle))
                {
                    coloredMainTextureHandle = pFont->mainTextureHandle;
                }

                const float lineHeight = static_cast<float>(pFont->fontHeight) * popupScale;
                float textX = std::round(baseResolved.x + baseLayout.textPadX * popupScale);
                float textY = std::round(rowY + baseLayout.textPadY * popupScale);

                for (const std::string &wrappedLine : wrappedLines)
                {
                    HudUiService::renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, wrappedLine, textX, textY, popupScale);
                    HudUiService::renderHudFontLayer(view, *pFont, coloredMainTextureHandle, wrappedLine, textX, textY, popupScale);
                    textY += lineHeight;
                }

                return rowY + lineHeight * static_cast<float>(std::max<size_t>(1, wrappedLines.size()));
            };

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> expertRect = resolveLayout("CharacterInspectExpert");
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> masterRect = resolveLayout("CharacterInspectMaster");
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> grandmasterRect =
            resolveLayout("CharacterInspectGrandmaster");

        if (expertRect)
        {
            nextRowY = renderMasteryRow(
                *pExpertLayout,
                *expertRect,
                nextRowY,
                view.m_characterInspectOverlay.expert,
                expertLines);

            if (showExpert)
            {
                nextRowY += CharacterInspectRowGap * popupScale;
            }
        }

        if (masterRect)
        {
            nextRowY = renderMasteryRow(
                *pMasterLayout,
                *masterRect,
                nextRowY,
                view.m_characterInspectOverlay.master,
                masterLines);

            if (showMaster)
            {
                nextRowY += CharacterInspectRowGap * popupScale;
            }
        }

        if (grandmasterRect)
        {
            renderMasteryRow(
                *pGrandmasterLayout,
                *grandmasterRect,
                nextRowY,
                view.m_characterInspectOverlay.grandmaster,
                grandmasterLines);
        }
    }
}

void GameplayPartyOverlayRenderer::renderSpellInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_spellInspectOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "SpellInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "SpellInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "SpellInspectBody");
    const OutdoorGameView::HudLayoutElement *pNormalLayout = HudUiService::findHudLayoutElement(view, "SpellInspectNormal");
    const OutdoorGameView::HudLayoutElement *pExpertLayout = HudUiService::findHudLayoutElement(view, "SpellInspectExpert");
    const OutdoorGameView::HudLayoutElement *pMasterLayout = HudUiService::findHudLayoutElement(view, "SpellInspectMaster");
    const OutdoorGameView::HudLayoutElement *pGrandmasterLayout = HudUiService::findHudLayoutElement(view, "SpellInspectGrandmaster");

    if (pRootLayout == nullptr
        || pTitleLayout == nullptr
        || pBodyLayout == nullptr
        || pNormalLayout == nullptr
        || pExpertLayout == nullptr
        || pMasterLayout == nullptr
        || pGrandmasterLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_spellInspectOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_spellInspectOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float SpellInspectBodyToRowsGap = 10.0f;
    static constexpr float SpellInspectRowGap = 2.0f;
    static constexpr float SpellInspectBottomPadding = 15.0f;

    const auto resolveWrappedLines =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::string &text) -> std::vector<std::string>
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

            if (pFont == nullptr)
            {
                return {text};
            }

            const float maxWidthScaled =
                std::max(0.0f, layout.width * popupScale - std::abs(layout.textPadX * popupScale) * 2.0f);
            const float maxWidth = std::max(0.0f, maxWidthScaled / std::max(1.0f, popupScale));
            return HudUiService::wrapHudTextToWidth(view, *pFont, text, maxWidth);
        };

    const auto rowHeight =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::vector<std::string> &lines) -> float
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);
            const float lineHeight =
                pFont != nullptr ? static_cast<float>(pFont->fontHeight) * popupScale : layout.height * popupScale;
            return std::max(lineHeight, lineHeight * static_cast<float>(std::max<size_t>(1, lines.size())));
        };

    const bool showNormal = !view.m_spellInspectOverlay.normal.empty();
    const bool showExpert = !view.m_spellInspectOverlay.expert.empty();
    const bool showMaster = !view.m_spellInspectOverlay.master.empty();
    const bool showGrandmaster = !view.m_spellInspectOverlay.grandmaster.empty();
    const std::vector<std::string> normalLines =
        showNormal ? resolveWrappedLines(*pNormalLayout, view.m_spellInspectOverlay.normal) : std::vector<std::string>{};
    const std::vector<std::string> expertLines =
        showExpert ? resolveWrappedLines(*pExpertLayout, view.m_spellInspectOverlay.expert) : std::vector<std::string>{};
    const std::vector<std::string> masterLines =
        showMaster ? resolveWrappedLines(*pMasterLayout, view.m_spellInspectOverlay.master) : std::vector<std::string>{};
    const std::vector<std::string> grandmasterLines =
        showGrandmaster
            ? resolveWrappedLines(*pGrandmasterLayout, view.m_spellInspectOverlay.grandmaster)
            : std::vector<std::string>{};
    float rowsHeight = 0.0f;
    bool hasRows = false;

    for (const auto &[showRow, pLayout, pLines] : {
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showNormal, pNormalLayout, &normalLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showExpert, pExpertLayout, &expertLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showMaster, pMasterLayout, &masterLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showGrandmaster, pGrandmasterLayout, &grandmasterLines}})
    {
        if (!showRow)
        {
            continue;
        }

        if (hasRows)
        {
            rowsHeight += SpellInspectRowGap * popupScale;
        }

        rowsHeight += rowHeight(*pLayout, *pLines);
        hasRows = true;
    }

    const float rootWidth = provisionalRoot.width;
    const float rootHeight =
        bodyRectForSizing.y
        + bodyHeight
        + (hasRows ? SpellInspectBodyToRowsGap * popupScale + rowsHeight : 0.0f)
        + SpellInspectBottomPadding * popupScale;
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_spellInspectOverlay.sourceX + view.m_spellInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_spellInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_spellInspectOverlay.sourceY + (view.m_spellInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture =
                    HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "spellinspectcorner_topedge"
                || normalizedLayoutId == "spellinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "spellinspectcorner_leftedge"
                || normalizedLayoutId == "spellinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "spellinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent =
                    resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "SpellInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "spellinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderSingleLine =
        [&view, &resolveLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(pLayoutId);

            if (pLayout == nullptr || !resolved || text.empty())
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    renderSingleLine("SpellInspectTitle", view.m_spellInspectOverlay.title);

    if (pBodyFont != nullptr)
    {
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("SpellInspectBody");

        if (bodyBaseRect)
        {
            bgfx::TextureHandle coloredMainTextureHandle =
                HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

            if (!bgfx::isValid(coloredMainTextureHandle))
            {
                coloredMainTextureHandle = pBodyFont->mainTextureHandle;
            }

            float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
            float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

            for (const std::string &line : bodyLines)
            {
                HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
                HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
                textY += bodyLineHeight;
            }

            const auto renderWrappedRow =
                [&view, popupScale](
                    const OutdoorGameView::HudLayoutElement &layout,
                    const OutdoorGameView::ResolvedHudLayoutElement &baseResolved,
                    float rowY,
                    const std::vector<std::string> &wrappedLines) -> float
                {
                    if (wrappedLines.empty())
                    {
                        return rowY;
                    }

                    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

                    if (pFont == nullptr)
                    {
                        return rowY;
                    }

                    bgfx::TextureHandle coloredMainTextureHandle =
                        HudUiService::ensureHudFontMainTextureColor(view, *pFont, layout.textColorAbgr);

                    if (!bgfx::isValid(coloredMainTextureHandle))
                    {
                        coloredMainTextureHandle = pFont->mainTextureHandle;
                    }

                    const float lineHeight = static_cast<float>(pFont->fontHeight) * popupScale;
                    float textX = std::round(baseResolved.x + layout.textPadX * popupScale);
                    float textY = std::round(rowY + layout.textPadY * popupScale);

                    for (const std::string &wrappedLine : wrappedLines)
                    {
                        HudUiService::renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, wrappedLine, textX, textY, popupScale);
                        HudUiService::renderHudFontLayer(view, *pFont, coloredMainTextureHandle, wrappedLine, textX, textY, popupScale);
                        textY += lineHeight;
                    }

                    return rowY + lineHeight * static_cast<float>(std::max<size_t>(1, wrappedLines.size()));
                };

            float nextRowY = std::round(bodyBaseRect->y + bodyHeight + SpellInspectBodyToRowsGap * popupScale);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> normalRect = resolveLayout("SpellInspectNormal");
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> expertRect = resolveLayout("SpellInspectExpert");
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> masterRect = resolveLayout("SpellInspectMaster");
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> grandmasterRect =
                resolveLayout("SpellInspectGrandmaster");

            if (normalRect)
            {
                nextRowY = renderWrappedRow(*pNormalLayout, *normalRect, nextRowY, normalLines);

                if (showNormal)
                {
                    nextRowY += SpellInspectRowGap * popupScale;
                }
            }

            if (expertRect)
            {
                nextRowY = renderWrappedRow(*pExpertLayout, *expertRect, nextRowY, expertLines);

                if (showExpert)
                {
                    nextRowY += SpellInspectRowGap * popupScale;
                }
            }

            if (masterRect)
            {
                nextRowY = renderWrappedRow(*pMasterLayout, *masterRect, nextRowY, masterLines);

                if (showMaster)
                {
                    nextRowY += SpellInspectRowGap * popupScale;
                }
            }

            if (grandmasterRect)
            {
                renderWrappedRow(*pGrandmasterLayout, *grandmasterRect, nextRowY, grandmasterLines);
            }
        }
    }
}

void GameplayPartyOverlayRenderer::renderReadableScrollOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_readableScrollOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "SpellInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "SpellInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "SpellInspectBody");

    if (pRootLayout == nullptr || pTitleLayout == nullptr || pBodyLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_readableScrollOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_readableScrollOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float ReadableScrollBottomPadding = 15.0f;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(
        provisionalRoot.height,
        bodyRectForSizing.y + bodyHeight + ReadableScrollBottomPadding * popupScale);
    const float rootX = std::round(uiViewport.x + (uiViewport.width - rootWidth) * 0.5f);
    const float rootY = std::round(uiViewport.y + (uiViewport.height - rootHeight) * 0.5f);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {rootX, rootY, rootWidth, rootHeight, popupScale};

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture =
                    HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "spellinspectcorner_topedge"
                || normalizedLayoutId == "spellinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "spellinspectcorner_leftedge"
                || normalizedLayoutId == "spellinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "spellinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent = resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "SpellInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "spellinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> titleRect = resolveLayout("SpellInspectTitle");

    if (titleRect)
    {
        HudUiService::renderLayoutLabel(view, *pTitleLayout, *titleRect, view.m_readableScrollOverlay.title);
    }

    if (pBodyFont == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("SpellInspectBody");

    if (!bodyBaseRect)
    {
        return;
    }

    bgfx::TextureHandle coloredMainTextureHandle =
        HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pBodyFont->mainTextureHandle;
    }

    float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
    float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

    for (const std::string &line : bodyLines)
    {
        HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
        HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
        textY += bodyLineHeight;
    }
}

void GameplayPartyOverlayRenderer::renderBuffInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_buffInspectOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "BuffInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "BuffInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "BuffInspectBody");

    if (pRootLayout == nullptr || pTitleLayout == nullptr || pBodyLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_buffInspectOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_buffInspectOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float BuffInspectBottomPadding = 14.0f;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(
        provisionalRoot.height,
        bodyRectForSizing.y + bodyHeight + BuffInspectBottomPadding * popupScale);
    const float popupGap = 10.0f * popupScale;
    float rootX = view.m_buffInspectOverlay.sourceX + view.m_buffInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_buffInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_buffInspectOverlay.sourceY + (view.m_buffInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "buffinspectcorner_topedge"
                || normalizedLayoutId == "buffinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "buffinspectcorner_leftedge"
                || normalizedLayoutId == "buffinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "buffinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent = resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "BuffInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "buffinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> titleRect = resolveLayout("BuffInspectTitle");

    if (titleRect)
    {
        HudUiService::renderLayoutLabel(view, *pTitleLayout, *titleRect, view.m_buffInspectOverlay.title);
    }

    if (pBodyFont == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("BuffInspectBody");

    if (!bodyBaseRect)
    {
        return;
    }

    bgfx::TextureHandle coloredMainTextureHandle =
        HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pBodyFont->mainTextureHandle;
    }

    float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
    float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

    for (const std::string &line : bodyLines)
    {
        HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
        HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
        textY += bodyLineHeight;
    }
}

void GameplayPartyOverlayRenderer::renderCharacterDetailOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_characterDetailOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "CharacterDetailRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "CharacterDetailTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "CharacterDetailBody");

    if (pRootLayout == nullptr || pTitleLayout == nullptr || pBodyLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_characterDetailOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_characterDetailOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float CharacterDetailBottomPadding = 15.0f;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(
        provisionalRoot.height,
        bodyRectForSizing.y + bodyHeight + CharacterDetailBottomPadding * popupScale);
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_characterDetailOverlay.sourceX + view.m_characterDetailOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_characterDetailOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_characterDetailOverlay.sourceY + (view.m_characterDetailOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "characterdetailcorner_topedge"
                || normalizedLayoutId == "characterdetailcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "characterdetailcorner_leftedge"
                || normalizedLayoutId == "characterdetailcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "characterdetailroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent = resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "CharacterDetail");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "characterdetailroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> titleRect = resolveLayout("CharacterDetailTitle");

    if (titleRect)
    {
        HudUiService::renderLayoutLabel(view, *pTitleLayout, *titleRect, view.m_characterDetailOverlay.title);
    }

    if (pBodyFont == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("CharacterDetailBody");

    if (!bodyBaseRect)
    {
        return;
    }

    bgfx::TextureHandle coloredMainTextureHandle =
        HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pBodyFont->mainTextureHandle;
    }

    float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
    float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

    for (const std::string &line : bodyLines)
    {
        HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
        HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
        textY += bodyLineHeight;
    }
}

void GameplayPartyOverlayRenderer::renderCharacterOverlay(
    const OutdoorGameView &view,
    int width,
    int height,
    bool renderAboveHud)
{
    if (view.currentHudScreenState() != OutdoorGameView::HudScreenState::Character
        || view.m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    OutdoorGameView &mutableView = const_cast<OutdoorGameView &>(view);
    setupHudProjection(width, height);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    float characterMouseX = 0.0f;
    float characterMouseY = 0.0f;
    const SDL_MouseButtonFlags characterMouseButtons = SDL_GetMouseState(&characterMouseX, &characterMouseY);
    const bool isLeftMousePressed = (characterMouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto replaceAll = [](std::string text, const std::string &from, const std::string &to) -> std::string
    {
        size_t position = 0;

        while ((position = text.find(from, position)) != std::string::npos)
        {
            text.replace(position, from.size(), to);
            position += to.size();
        }

        return text;
    };

    const auto hasVisibleCharacterAncestors =
        [&view](const OutdoorGameView::HudLayoutElement &layout) -> bool
        {
            const std::string activePageRootId =
                view.m_characterPage == OutdoorGameView::CharacterPage::Stats
                    ? "characterstatspage"
                    : (view.m_characterPage == OutdoorGameView::CharacterPage::Skills
                        ? "characterskillspage"
                        : (view.m_characterPage == OutdoorGameView::CharacterPage::Inventory
                            ? "characterinventorypage"
                            : "characterawardspage"));
            const OutdoorGameView::HudLayoutElement *pCurrent = &layout;

            while (pCurrent != nullptr)
            {
                const std::string normalizedId = toLowerCopy(pCurrent->id);

                if (!pCurrent->visible || toLowerCopy(pCurrent->screen) != "character")
                {
                    return false;
                }

                if ((normalizedId == "characterstatspage"
                        || normalizedId == "characterskillspage"
                        || normalizedId == "characterinventorypage"
                        || normalizedId == "characterawardspage")
                    && normalizedId != activePageRootId)
                {
                    return false;
                }

                if (pCurrent->parentId.empty())
                {
                    break;
                }

                pCurrent = HudUiService::findHudLayoutElement(view, pCurrent->parentId);
            }

            return true;
        };

    const Party &party = view.m_pOutdoorPartyRuntime->party();
    const bool isAdventurersInnActive = view.isAdventurersInnScreenActive();
    const Character *pCharacter = view.selectedCharacterScreenCharacter();
    const std::vector<std::string> orderedCharacterLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "Character");
    const int hudZThreshold = HudUiService::defaultHudLayoutZIndexForScreen("OutdoorHud");
    const auto shouldRenderInCurrentPass =
        [renderAboveHud, hudZThreshold](int zIndex) -> bool
        {
            return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
        };
    const size_t characterSourceIndex =
        view.isAdventurersInnCharacterSourceActive() ? view.m_characterScreenSourceIndex : party.activeMemberIndex();
    const auto formatPair = [](int actualValue, int baseValue) -> std::string
    {
        return std::to_string(actualValue) + " / " + std::to_string(baseValue);
    };
    const auto formatSheetValue = [&formatPair](const CharacterSheetValue &value) -> std::string
    {
        if (value.infinite)
        {
            return "INF";
        }

        return formatPair(value.actual, value.base);
    };

    std::string mightValue = "0 / 0";
    std::string intellectValue = "0 / 0";
    std::string personalityValue = "0 / 0";
    std::string enduranceValue = "0 / 0";
    std::string accuracyValue = "0 / 0";
    std::string speedValue = "0 / 0";
    std::string luckValue = "0 / 0";
    std::string hitPointsValue = "0 / 0";
    std::string spellPointsValue = "0 / 0";
    std::string armorClassValue = "0 / 0";
    std::string conditionValue = "-";
    std::string quickSpellValue = "-";
    std::string ageValue = "-";
    std::string levelValue = "0 / 0";
    std::string experienceValue = "-";
    std::string attackValue = "-";
    std::string meleeDamageValue = "-";
    std::string shootValue = "-";
    std::string rangedDamageValue = "-";
    std::string fireResistanceValue = "0 / 0";
    std::string airResistanceValue = "0 / 0";
    std::string waterResistanceValue = "0 / 0";
    std::string earthResistanceValue = "0 / 0";
    std::string mindResistanceValue = "0 / 0";
    std::string bodyResistanceValue = "0 / 0";
    std::string awards;
    std::string inventoryInfo;
    std::string adventurersInnBlurb;
    bool canTrainToNextLevel = false;
    const OutdoorGameView::HudFontHandle *pSkillRowFont = HudUiService::findHudFont(view, "Lucida");
    const float skillRowHeight =
        pSkillRowFont != nullptr ? static_cast<float>(std::max(1, pSkillRowFont->fontHeight - 3)) : 11.0f;
    const CharacterDollEntry *pCharacterDollEntry = resolveCharacterDollEntry(view.m_pCharacterDollTable, pCharacter);
    const CharacterDollTypeEntry *pCharacterDollType =
        pCharacterDollEntry != nullptr && view.m_pCharacterDollTable != nullptr
            ? view.m_pCharacterDollTable->getDollType(pCharacterDollEntry->dollTypeId)
            : nullptr;

    if (pCharacter != nullptr)
    {
        const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(*pCharacter, view.m_pItemTable);
        mightValue = formatSheetValue(summary.might);
        intellectValue = formatSheetValue(summary.intellect);
        personalityValue = formatSheetValue(summary.personality);
        enduranceValue = formatSheetValue(summary.endurance);
        accuracyValue = formatSheetValue(summary.accuracy);
        speedValue = formatSheetValue(summary.speed);
        luckValue = formatSheetValue(summary.luck);
        hitPointsValue =
            std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum);
        spellPointsValue =
            std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum);
        armorClassValue = formatSheetValue(summary.armorClass);
        conditionValue = summary.conditionText;
        quickSpellValue = summary.quickSpellText;
        ageValue = summary.ageText;
        levelValue = formatSheetValue(summary.level);
        experienceValue = summary.experienceText;
        canTrainToNextLevel = summary.canTrainToNextLevel;
        attackValue = std::to_string(summary.combat.attack);
        meleeDamageValue = summary.combat.meleeDamageText;
        shootValue = summary.combat.shoot ? std::to_string(*summary.combat.shoot) : "N/A";
        rangedDamageValue = summary.combat.rangedDamageText;
        fireResistanceValue = formatSheetValue(summary.fireResistance);
        airResistanceValue = formatSheetValue(summary.airResistance);
        waterResistanceValue = formatSheetValue(summary.waterResistance);
        earthResistanceValue = formatSheetValue(summary.earthResistance);
        mindResistanceValue = formatSheetValue(summary.mindResistance);
        bodyResistanceValue = formatSheetValue(summary.bodyResistance);
        awards = "Awards earned: " + std::to_string(pCharacter->awards.size());

        if (view.m_pRosterTable != nullptr && pCharacter->rosterId != 0)
        {
            const RosterEntry *pRosterEntry = view.m_pRosterTable->get(pCharacter->rosterId);
            adventurersInnBlurb = pRosterEntry != nullptr ? pRosterEntry->blurb : "";
        }
    }

    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pCharacter);
    mutableView.m_hudLayoutRuntimeHeightOverrides.clear();
    const uint32_t skillPointsValueColorAbgr =
        pCharacter != nullptr && pCharacter->skillPoints > 0 ? makeAbgrColor(0, 255, 0) : makeAbgrColor(255, 255, 255);
    const uint32_t experienceValueColorAbgr =
        pCharacter != nullptr && canTrainToNextLevel ? makeAbgrColor(0, 255, 0) : makeAbgrColor(255, 255, 255);

    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsWeaponsListRegion",
        skillUiData.weaponRows.size());
    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsMagicListRegion",
        skillUiData.magicRows.size());
    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsArmorListRegion",
        skillUiData.armorRows.size());
    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsMiscListRegion",
        skillUiData.miscRows.size());

    const auto submitCharacterDollLayer =
        [&view, &mutableView, uiViewport, baseScale](
            const OutdoorGameView::HudLayoutElement &layout,
            const OutdoorGameView::ResolvedHudLayoutElement &resolvedAnchor,
            const std::string &assetName,
            int offsetX,
            int offsetY,
            const char *pRenderKey = nullptr)
        {
            if (assetName.empty() || assetName == "none")
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, assetName);

            if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
            {
                return;
            }

            const float centerX = resolvedAnchor.x + resolvedAnchor.width * 0.5f;
            const float centerY = resolvedAnchor.y + resolvedAnchor.height * 0.5f;
            const float scale = resolvedAnchor.scale;
            const float layerWidth = static_cast<float>(pTexture->width) * scale;
            const float layerHeight = static_cast<float>(pTexture->height) * scale;
            float anchorX = centerX;
            float anchorY = centerY;
            const auto setAnchorPoint = [&](float normalizedX, float normalizedY)
            {
                anchorX = resolvedAnchor.x + resolvedAnchor.width * normalizedX;
                anchorY = resolvedAnchor.y + resolvedAnchor.height * normalizedY;
            };

            if (!layout.parentId.empty())
            {
                switch (layout.attachTo)
                {
                    case OutdoorGameView::HudLayoutAttachMode::None:
                    case OutdoorGameView::HudLayoutAttachMode::CenterIn:
                        setAnchorPoint(0.5f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::RightOf:
                    case OutdoorGameView::HudLayoutAttachMode::Below:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopLeft:
                        setAnchorPoint(0.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::LeftOf:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopRight:
                        setAnchorPoint(1.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::Above:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::CenterAbove:
                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomCenter:
                        setAnchorPoint(0.5f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::CenterBelow:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopCenter:
                        setAnchorPoint(0.5f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideLeft:
                        setAnchorPoint(0.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideRight:
                        setAnchorPoint(1.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomLeft:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomRight:
                        setAnchorPoint(1.0f, 1.0f);
                        break;
                }
            }
            else
            {
                switch (layout.anchor)
                {
                    case OutdoorGameView::HudLayoutAnchor::TopLeft:
                        setAnchorPoint(0.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::TopCenter:
                        setAnchorPoint(0.5f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::TopRight:
                        setAnchorPoint(1.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::Left:
                        setAnchorPoint(0.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::Center:
                        setAnchorPoint(0.5f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::Right:
                        setAnchorPoint(1.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::BottomLeft:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::BottomCenter:
                        setAnchorPoint(0.5f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::BottomRight:
                        setAnchorPoint(1.0f, 1.0f);
                        break;
                }
            }

            anchorX += static_cast<float>(offsetX) * scale;
            anchorY += static_cast<float>(offsetY) * scale;
            float layerX = std::round(anchorX - layerWidth * 0.5f);
            float layerY = std::round(anchorY - layerHeight * 0.5f);

            if (!layout.parentId.empty())
            {
                switch (layout.attachTo)
                {
                    case OutdoorGameView::HudLayoutAttachMode::RightOf:
                    case OutdoorGameView::HudLayoutAttachMode::Below:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::LeftOf:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::Above:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::CenterAbove:
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::CenterBelow:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopCenter:
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideLeft:
                        layerX = std::round(anchorX);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideRight:
                        layerX = std::round(anchorX - layerWidth);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomCenter:
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::None:
                    case OutdoorGameView::HudLayoutAttachMode::CenterIn:
                        break;
                }
            }
            else
            {
                switch (layout.anchor)
                {
                    case OutdoorGameView::HudLayoutAnchor::TopLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::TopCenter:
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::TopRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::Left:
                        layerX = std::round(anchorX);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::Center:
                        break;

                    case OutdoorGameView::HudLayoutAnchor::Right:
                        layerX = std::round(anchorX - layerWidth);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::BottomLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::BottomCenter:
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::BottomRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                }
            }

            if (pRenderKey != nullptr)
            {
                logCharacterEquipmentRender(
                    pRenderKey,
                    layout.parentId,
                    assetName,
                    layerX,
                    layerY,
                    layerWidth,
                    layerHeight,
                    layout.zIndex,
                    baseScale > 0.0f ? (layerX - uiViewport.x) / baseScale : layerX,
                    baseScale > 0.0f ? (layerY - uiViewport.y) / baseScale : layerY,
                    baseScale > 0.0f ? layerWidth / baseScale : layerWidth,
                    baseScale > 0.0f ? layerHeight / baseScale : layerHeight);
            }

            view.submitHudTexturedQuad(*pTexture, layerX, layerY, layerWidth, layerHeight);
        };

    const auto getEquippedItemDefinition =
        [&view, pCharacter](EquipmentSlot slot) -> const ItemDefinition *
        {
            if (pCharacter == nullptr || view.m_pItemTable == nullptr)
            {
                return nullptr;
            }

            const uint32_t itemId = equippedItemId(pCharacter->equipment, slot);
            return itemId != 0 ? view.m_pItemTable->get(itemId) : nullptr;
        };

    const ItemDefinition *pMainHandItem = getEquippedItemDefinition(EquipmentSlot::MainHand);
    const ItemDefinition *pOffHandItem = getEquippedItemDefinition(EquipmentSlot::OffHand);
    SkillMastery spearMastery = SkillMastery::None;

    if (pCharacter != nullptr)
    {
        const CharacterSkill *pSpearSkill = pCharacter->findSkill("Spear");

        if (pSpearSkill != nullptr)
        {
            spearMastery = pSpearSkill->mastery;
        }
    }

    const bool leftHandDisabled =
        pMainHandItem != nullptr
        && (pMainHandItem->equipStat == "Weapon2"
            || (canonicalSkillName(pMainHandItem->skillGroup) == "Spear" && spearMastery < SkillMastery::Master));

    for (const std::string &layoutId : orderedCharacterLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr || !hasVisibleCharacterAncestors(*pLayout) || !shouldRenderInCurrentPass(pLayout->zIndex))
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
            layoutId,
            width,
            height,
            pLayout->width,
            pLayout->height);

        if (!resolved)
        {
            continue;
        }

        const std::string normalizedLayoutId = toLowerCopy(layoutId);

        if (isAdventurersInnActive && !shouldRenderCharacterLayoutInAdventurersInn(normalizedLayoutId))
        {
            continue;
        }

        if (normalizedLayoutId.starts_with("adventurersinn"))
        {
            if (!isAdventurersInnActive)
            {
                continue;
            }

            if (normalizedLayoutId == "adventurersinnhirebutton" && party.isFull())
            {
                continue;
            }
        }

        if (normalizedLayoutId == "characterdismissbutton"
            && (view.isAdventurersInnCharacterSourceActive() || party.activeMemberIndex() == 0))
        {
            continue;
        }

        if (normalizedLayoutId == "characterdolljewelryoverlaypanel" && !view.m_characterDollJewelryOverlayOpen)
        {
            continue;
        }

        if (isAdventurersInnActive && normalizedLayoutId == "charactermagnifybutton")
        {
            continue;
        }

        if (normalizedLayoutId == "characterdollbackground")
        {
            std::string assetName = pLayout->primaryAsset;

            if (pCharacterDollEntry != nullptr
                && !pCharacterDollEntry->backgroundAsset.empty()
                && pCharacterDollEntry->backgroundAsset != "none")
            {
                const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
                    HudUiService::ensureHudTextureLoaded(mutableView, pCharacterDollEntry->backgroundAsset);

                if (pBackgroundTexture != nullptr)
                {
                    assetName = pCharacterDollEntry->backgroundAsset;
                }
            }

            if (!assetName.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, assetName);

                if (pTexture != nullptr)
                {
                    view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
                }
            }

            continue;
        }

        if (normalizedLayoutId == "characterdollbody" && pCharacterDollEntry != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                *resolved,
                pCharacterDollEntry->bodyAsset,
                pCharacterDollEntry->bodyOffsetX,
                pCharacterDollEntry->bodyOffsetY);
            continue;
        }

        if (normalizedLayoutId == "characterdollrighthand"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                *resolved,
                pMainHandItem != nullptr ? pCharacterDollEntry->rightHandHoldAsset : pCharacterDollEntry->rightHandOpenAsset,
                pMainHandItem != nullptr ? pCharacterDollType->rightHandClosedX : pCharacterDollType->rightHandOpenX,
                pMainHandItem != nullptr ? pCharacterDollType->rightHandClosedY : pCharacterDollType->rightHandOpenY);
            continue;
        }

        if (normalizedLayoutId == "characterdolllefthand"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr)
        {
            if (pOffHandItem != nullptr)
            {
                submitCharacterDollLayer(
                    *pLayout,
                    *resolved,
                    pCharacterDollEntry->leftHandHoldAsset,
                    pCharacterDollType->leftHandOpenX,
                    pCharacterDollType->leftHandOpenY);
            }
            else if (leftHandDisabled)
            {
                submitCharacterDollLayer(
                    *pLayout,
                    *resolved,
                    pCharacterDollEntry->leftHandClosedAsset,
                    pCharacterDollType->leftHandClosedX,
                    pCharacterDollType->leftHandClosedY);
            }
            else
            {
                submitCharacterDollLayer(
                    *pLayout,
                    *resolved,
                    pCharacterDollEntry->leftHandOpenAsset,
                    pCharacterDollType->leftHandFingersX,
                    pCharacterDollType->leftHandFingersY);
            }
            continue;
        }

        if (normalizedLayoutId == "characterdollrighthandfingers"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr
            && getEquippedItemDefinition(EquipmentSlot::MainHand) != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                *resolved,
                pCharacterDollEntry->rightHandFingersAsset,
                pCharacterDollType->rightHandFingersX,
                pCharacterDollType->rightHandFingersY);
            continue;
        }

        if (normalizedLayoutId == "characterpaperdollregion"
            && pCharacter != nullptr
            && !pCharacter->portraitTextureName.empty())
        {
            const std::string portraitTextureName = view.resolvePortraitTextureName(*pCharacter);
            const OutdoorGameView::HudTextureHandle *pPortraitTexture = HudUiService::ensureHudTextureLoaded(mutableView, portraitTextureName);

            if (pPortraitTexture != nullptr && pPortraitTexture->width > 0 && pPortraitTexture->height > 0)
            {
                const float scale = std::min(
                    resolved->width / static_cast<float>(pPortraitTexture->width),
                    resolved->height / static_cast<float>(pPortraitTexture->height));
                const float portraitWidth = static_cast<float>(pPortraitTexture->width) * scale;
                const float portraitHeight = static_cast<float>(pPortraitTexture->height) * scale;
                const float portraitX = resolved->x + (resolved->width - portraitWidth) * 0.5f;
                const float portraitY = resolved->y + (resolved->height - portraitHeight) * 0.5f;
                view.submitHudTexturedQuad(*pPortraitTexture, portraitX, portraitY, portraitWidth, portraitHeight);
            }
        }

        const std::string *pAssetName =
            HudUiService::resolveInteractiveAssetName(*pLayout, *resolved, characterMouseX, characterMouseY, isLeftMousePressed);

        if (!pAssetName->empty())
        {
            const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, *pAssetName);

            if (pTexture != nullptr)
            {
                view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
            }
        }

        const std::optional<EquipmentSlot> slot = characterEquipmentSlotForLayoutId(layoutId);

        if (slot && isVisibleInCharacterDollOverlay(*slot, view.m_characterDollJewelryOverlayOpen))
        {
            const ItemDefinition *pItemDefinition = getEquippedItemDefinition(*slot);

            if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
            {
                const bool hasRightHandWeapon = pCharacter != nullptr && pCharacter->equipment.mainHand != 0;
                const uint32_t dollTypeId = pCharacterDollType != nullptr ? pCharacterDollType->id : 0;
                const std::string textureName =
                    view.resolveEquippedItemHudTextureName(*pItemDefinition, dollTypeId, hasRightHandWeapon, *slot);
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, textureName);

                if (pTexture != nullptr)
                {
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> iconRect =
                        view.resolveCharacterEquipmentRenderRect(
                            *pLayout,
                            *pItemDefinition,
                            *pTexture,
                            pCharacterDollType,
                            *slot,
                            width,
                            height);

                    if (iconRect)
                    {
                        logCharacterEquipmentRender(
                            "slot." + std::string(equipmentSlotName(*slot)),
                            pLayout->parentId,
                            textureName,
                            iconRect->x,
                            iconRect->y,
                            iconRect->width,
                            iconRect->height,
                            pLayout->zIndex,
                            baseScale > 0.0f ? (iconRect->x - uiViewport.x) / baseScale : iconRect->x,
                            baseScale > 0.0f ? (iconRect->y - uiViewport.y) / baseScale : iconRect->y,
                            baseScale > 0.0f ? iconRect->width / baseScale : iconRect->width,
                            baseScale > 0.0f ? iconRect->height / baseScale : iconRect->height);
                        const std::optional<InventoryItem> equippedItemState =
                            !view.isAdventurersInnCharacterSourceActive() && view.m_pOutdoorPartyRuntime != nullptr
                                ? view.m_pOutdoorPartyRuntime->party().equippedItem(
                                    view.m_pOutdoorPartyRuntime->party().activeMemberIndex(),
                                    *slot)
                                : std::nullopt;
                        view.submitHudTexturedQuad(*pTexture, iconRect->x, iconRect->y, iconRect->width, iconRect->height);

                        const bgfx::TextureHandle tintedTextureHandle = HudUiService::ensureHudTextureColor(mutableView, 
                            *pTexture,
                            itemTintColorAbgr(
                                equippedItemState.has_value() ? &*equippedItemState : nullptr,
                                pItemDefinition,
                                ItemTintContext::Equipped));

                        if (bgfx::isValid(tintedTextureHandle) && tintedTextureHandle.idx != pTexture->textureHandle.idx)
                        {
                            OutdoorGameView::HudTextureHandle tintedTexture = *pTexture;
                            tintedTexture.textureHandle = tintedTextureHandle;
                            view.submitHudTexturedQuad(tintedTexture, iconRect->x, iconRect->y, iconRect->width, iconRect->height);
                        }

                        if (pItemDefinition->itemId != 0)
                        {
                            OutdoorGameView::RenderedInspectableHudItem inspectableItem = {};
                            inspectableItem.objectDescriptionId = pItemDefinition->itemId;

                            if (equippedItemState.has_value())
                            {
                                inspectableItem.hasItemState = true;
                                inspectableItem.itemState = *equippedItemState;
                            }

                            inspectableItem.sourceType =
                                view.isAdventurersInnCharacterSourceActive()
                                    ? OutdoorGameView::ItemInspectSourceType::None
                                    : OutdoorGameView::ItemInspectSourceType::Equipment;
                            inspectableItem.sourceMemberIndex = characterSourceIndex;
                            inspectableItem.equipmentSlot = *slot;
                            inspectableItem.textureName = textureName;
                            inspectableItem.x = iconRect->x;
                            inspectableItem.y = iconRect->y;
                            inspectableItem.width = iconRect->width;
                            inspectableItem.height = iconRect->height;
                            view.m_renderedInspectableHudItems.push_back(std::move(inspectableItem));
                        }
                    }
                }
            }
        }
    }

    if (!isAdventurersInnActive
        && view.m_characterPage == OutdoorGameView::CharacterPage::Inventory
        && pCharacter != nullptr)
    {
        const OutdoorGameView::HudLayoutElement *pInventoryGridLayout = HudUiService::findHudLayoutElement(view, "CharacterInventoryGrid");
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedInventoryGrid =
            pInventoryGridLayout != nullptr
                ? HudUiService::resolveHudLayoutElement(view, 
                    "CharacterInventoryGrid",
                    width,
                    height,
                    pInventoryGridLayout->width,
                    pInventoryGridLayout->height)
                : std::nullopt;

        if (resolvedInventoryGrid)
        {
            const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                resolvedInventoryGrid->x,
                resolvedInventoryGrid->y,
                resolvedInventoryGrid->width,
                resolvedInventoryGrid->height,
                resolvedInventoryGrid->scale);

            for (const InventoryItem &item : pCharacter->inventory)
            {
                const ItemDefinition *pItemDefinition =
                    view.m_pItemTable != nullptr ? view.m_pItemTable->get(item.objectDescriptionId) : nullptr;

                if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
                {
                    continue;
                }

                const OutdoorGameView::HudTextureHandle *pItemTexture =
                    HudUiService::ensureHudTextureLoaded(mutableView, pItemDefinition->iconName);

                if (pItemTexture == nullptr)
                {
                    continue;
                }

                const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
                const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
                const InventoryItemScreenRect itemRect =
                    computeInventoryItemScreenRect(gridMetrics, item, itemWidth, itemHeight);
                view.submitHudTexturedQuad(*pItemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

                if (pItemDefinition->itemId != 0)
                {
                    OutdoorGameView::RenderedInspectableHudItem inspectableItem = {};
                    inspectableItem.objectDescriptionId = pItemDefinition->itemId;
                    inspectableItem.hasItemState = true;
                    inspectableItem.itemState = item;
                    inspectableItem.sourceType =
                        view.isAdventurersInnCharacterSourceActive()
                            ? OutdoorGameView::ItemInspectSourceType::None
                            : OutdoorGameView::ItemInspectSourceType::Inventory;
                    inspectableItem.sourceMemberIndex = characterSourceIndex;
                    inspectableItem.sourceGridX = item.gridX;
                    inspectableItem.sourceGridY = item.gridY;
                    inspectableItem.textureName = pItemDefinition->iconName;
                    inspectableItem.x = itemRect.x;
                    inspectableItem.y = itemRect.y;
                    inspectableItem.width = itemRect.width;
                    inspectableItem.height = itemRect.height;
                    view.m_renderedInspectableHudItems.push_back(std::move(inspectableItem));
                }
            }
        }
    }

    for (const std::string &layoutId : orderedCharacterLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !hasVisibleCharacterAncestors(*pLayout)
            || !shouldRenderInCurrentPass(pLayout->zIndex)
            || pLayout->labelText.empty())
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
            layoutId,
            width,
            height,
            pLayout->width,
            pLayout->height);

        if (!resolved)
        {
            continue;
        }

        OutdoorGameView::HudLayoutElement layoutForRender = *pLayout;
        const std::string normalizedLayoutId = toLowerCopy(layoutId);

        if (isAdventurersInnActive && !shouldRenderCharacterLayoutInAdventurersInn(normalizedLayoutId))
        {
            continue;
        }

        if (normalizedLayoutId.starts_with("adventurersinn"))
        {
            if (!isAdventurersInnActive)
            {
                continue;
            }

            if (normalizedLayoutId == "adventurersinnhirebutton" && party.isFull())
            {
                continue;
            }
        }

        if (normalizedLayoutId == "characterstatsskillpointsvalue"
            || normalizedLayoutId == "characterskillsskillpointsvalue")
        {
            layoutForRender.textColorAbgr = skillPointsValueColorAbgr;
        }
        else if (normalizedLayoutId == "characterstatexperiencevalue")
        {
            layoutForRender.textColorAbgr = experienceValueColorAbgr;
        }

        std::string label = pLayout->labelText;
        label = replaceAll(label, "{gold}", std::to_string(party.gold()));
        label = replaceAll(label, "{food}", std::to_string(party.food()));
        label = replaceAll(label, "{character_name}", pCharacter != nullptr ? pCharacter->name : "");
        label = replaceAll(
            label,
            "{stats_skill_points}",
            pCharacter != nullptr ? "Skill Points: " + std::to_string(pCharacter->skillPoints) : "Skill Points: 0");
        label = replaceAll(
            label,
            "{stats_skill_points_value}",
            pCharacter != nullptr ? std::to_string(pCharacter->skillPoints) : "0");
        label = replaceAll(
            label,
            "{character_class_race}",
            pCharacter != nullptr ? (!pCharacter->className.empty() ? pCharacter->className : pCharacter->role) : "");
        label = replaceAll(
            label,
            "{quick_stats}",
            pCharacter != nullptr
                ? ("HP " + std::to_string(pCharacter->health) + "/" + std::to_string(pCharacter->maxHealth)
                    + "\nSP " + std::to_string(pCharacter->spellPoints) + "/" + std::to_string(pCharacter->maxSpellPoints))
                : "");
        label = replaceAll(label, "{might_value}", mightValue);
        label = replaceAll(label, "{intellect_value}", intellectValue);
        label = replaceAll(label, "{personality_value}", personalityValue);
        label = replaceAll(label, "{endurance_value}", enduranceValue);
        label = replaceAll(label, "{accuracy_value}", accuracyValue);
        label = replaceAll(label, "{speed_value}", speedValue);
        label = replaceAll(label, "{luck_value}", luckValue);
        label = replaceAll(label, "{hit_points_value}", hitPointsValue);
        label = replaceAll(label, "{spell_points_value}", spellPointsValue);
        label = replaceAll(label, "{armor_class_value}", armorClassValue);
        label = replaceAll(label, "{condition_value}", conditionValue);
        label = replaceAll(label, "{quick_spell_value}", quickSpellValue);
        label = replaceAll(label, "{age_value}", ageValue);
        label = replaceAll(label, "{level_value}", levelValue);
        label = replaceAll(label, "{experience_value}", experienceValue);
        label = replaceAll(label, "{attack_value}", attackValue);
        label = replaceAll(label, "{melee_damage_value}", meleeDamageValue);
        label = replaceAll(label, "{shoot_value}", shootValue);
        label = replaceAll(label, "{ranged_damage_value}", rangedDamageValue);
        label = replaceAll(label, "{fire_resistance_value}", fireResistanceValue);
        label = replaceAll(label, "{air_resistance_value}", airResistanceValue);
        label = replaceAll(label, "{water_resistance_value}", waterResistanceValue);
        label = replaceAll(label, "{earth_resistance_value}", earthResistanceValue);
        label = replaceAll(label, "{mind_resistance_value}", mindResistanceValue);
        label = replaceAll(label, "{body_resistance_value}", bodyResistanceValue);
        label = replaceAll(label, "{awards}", awards);
        label = replaceAll(label, "{award_detail}", "");
        label = replaceAll(label, "{inventory_info}", inventoryInfo);

        if (label.find('{') != std::string::npos)
        {
            label.clear();
        }

        HudUiService::renderLayoutLabel(view, layoutForRender, *resolved, label);
    }

    if (isAdventurersInnActive)
    {
        const std::vector<AdventurersInnMember> &innMembers = party.adventurersInnMembers();
        const size_t maximumScrollOffset =
            innMembers.size() > AdventurersInnVisibleCount ? innMembers.size() - AdventurersInnVisibleCount : 0;
        const size_t scrollOffset = std::min(view.m_adventurersInnScrollOffset, maximumScrollOffset);
        const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, "SMALLNUM");

        const auto renderInnLabel =
            [&view, baseScale](const std::string &text, float x, float y, float width, float height)
            {
                OutdoorGameView::HudLayoutElement layout = {};
                layout.fontName = "SMALLNUM";
                layout.textColorAbgr = AdventurersInnTextColorAbgr;
                layout.textAlignX = OutdoorGameView::HudTextAlignX::Left;
                layout.textAlignY = OutdoorGameView::HudTextAlignY::Top;
                OutdoorGameView::ResolvedHudLayoutElement resolved = {};
                resolved.x = std::round(x * baseScale);
                resolved.y = std::round(y * baseScale);
                resolved.width = width * baseScale;
                resolved.height = height * baseScale;
                resolved.scale = baseScale;
                HudUiService::renderLayoutLabel(view, layout, resolved, text);
            };

        for (size_t visibleIndex = 0; visibleIndex < AdventurersInnVisibleCount; ++visibleIndex)
        {
            const size_t innIndex = scrollOffset + visibleIndex;

            if (innIndex >= innMembers.size())
            {
                continue;
            }

            const size_t column = visibleIndex % AdventurersInnVisibleColumns;
            const size_t row = visibleIndex / AdventurersInnVisibleColumns;
            const float portraitX =
                uiViewport.x
                + (AdventurersInnPortraitX
                    + static_cast<float>(column) * (AdventurersInnPortraitWidth + AdventurersInnPortraitGapX)) * baseScale;
            const float portraitY =
                uiViewport.y
                + (AdventurersInnPortraitY
                    + static_cast<float>(row) * (AdventurersInnPortraitHeight + AdventurersInnPortraitGapY)) * baseScale;
            const float portraitWidth = AdventurersInnPortraitWidth * baseScale;
            const float portraitHeight = AdventurersInnPortraitHeight * baseScale;
            std::string textureName = npcPortraitTextureName(innMembers[innIndex].portraitPictureId);

            if (textureName.empty())
            {
                textureName = view.resolvePortraitTextureName(innMembers[innIndex].character);
            }

            const OutdoorGameView::HudTextureHandle *pPortraitTexture =
                HudUiService::ensureHudTextureLoaded(mutableView, textureName);

            if (pPortraitTexture != nullptr)
            {
                view.submitHudTexturedQuad(*pPortraitTexture, portraitX, portraitY, portraitWidth, portraitHeight);
            }

            if (innIndex == view.m_characterScreenSourceIndex)
            {
                const OutdoorGameView::HudTextureHandle *pSelectionTexture =
                    HudUiService::ensureSolidHudTextureLoaded(
                        mutableView,
                        "__adventurers_inn_selection__",
                        AdventurersInnSelectionColorAbgr);

                if (pSelectionTexture != nullptr)
                {
                    const float thickness = std::max(1.0f, AdventurersInnSelectionThickness * baseScale);
                    view.submitHudTexturedQuad(
                        *pSelectionTexture,
                        portraitX - thickness,
                        portraitY - thickness,
                        portraitWidth + thickness * 2.0f,
                        thickness);
                    view.submitHudTexturedQuad(
                        *pSelectionTexture,
                        portraitX - thickness,
                        portraitY + portraitHeight,
                        portraitWidth + thickness * 2.0f,
                        thickness);
                    view.submitHudTexturedQuad(*pSelectionTexture, portraitX - thickness, portraitY, thickness, portraitHeight);
                    view.submitHudTexturedQuad(*pSelectionTexture, portraitX + portraitWidth, portraitY, thickness, portraitHeight);
                }
            }
        }

        if (pCharacter != nullptr)
        {
            const auto formatSignedValue = [](const std::string &value) -> std::string
            {
                int parsedValue = 0;
                return tryParseInteger(value, parsedValue) && parsedValue > 0 ? "+" + value : value;
            };

            renderInnLabel(
                "Name: " + pCharacter->name,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Class: " + (!pCharacter->className.empty() ? pCharacter->className : pCharacter->role),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "HP: " + std::to_string(pCharacter->health),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 2.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "AC: " + armorClassValue,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 3.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Attack: " + formatSignedValue(attackValue),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 4.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Shoot: " + formatSignedValue(shootValue),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 5.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Skills: " + std::to_string(pCharacter->skills.size()),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 6.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Cond: " + conditionValue,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 7.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "QSpell: " + quickSpellValue,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 8.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);

            renderInnLabel(
                "Level: " + std::to_string(pCharacter->level),
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "SP: " + std::to_string(pCharacter->spellPoints),
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "Dmg: " + meleeDamageValue,
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep * 2.0f + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "Dmg: " + rangedDamageValue,
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep * 3.0f + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "Points: " + std::to_string(pCharacter->skillPoints),
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep * 4.0f + uiViewport.y / baseScale,
                130.0f,
                16.0f);

            if (pFont != nullptr && !adventurersInnBlurb.empty())
            {
                float fontScale = baseScale >= 1.0f ? snappedHudFontScale(baseScale) : std::max(0.5f, baseScale);
                const float lineHeight = std::max(1.0f, static_cast<float>(pFont->fontHeight - 2)) * fontScale;
                const float wrapWidth =
                    std::max(1.0f, (AdventurersInnBlurbWidth * baseScale) / std::max(0.5f, fontScale));
                const std::vector<std::string> wrappedLines =
                    HudUiService::wrapHudTextToWidth(view, *pFont, adventurersInnBlurb, wrapWidth);
                bgfx::TextureHandle coloredTextureHandle =
                    HudUiService::ensureHudFontMainTextureColor(view, *pFont, AdventurersInnTextColorAbgr);

                if (!bgfx::isValid(coloredTextureHandle))
                {
                    coloredTextureHandle = pFont->mainTextureHandle;
                }

                float blurbX = std::round(uiViewport.x + AdventurersInnBlurbX * baseScale);
                float blurbY = std::round(uiViewport.y + AdventurersInnBlurbY * baseScale);

                for (const std::string &line : wrappedLines)
                {
                    HudUiService::renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, line, blurbX, blurbY, fontScale);
                    HudUiService::renderHudFontLayer(view, *pFont, coloredTextureHandle, line, blurbX, blurbY, fontScale);
                    blurbY += lineHeight;
                }
            }
        }
    }

    const auto renderSkillGroup =
        [&view, width, height, &hasVisibleCharacterAncestors, &shouldRenderInCurrentPass, skillRowHeight](
            const char *pRegionId,
            const char *pLevelHeaderId,
            const std::vector<CharacterSkillUiRow> &rows)
        {
            const OutdoorGameView::HudLayoutElement *pRegionLayout = HudUiService::findHudLayoutElement(view, pRegionId);
            const OutdoorGameView::HudLayoutElement *pLevelLayout = HudUiService::findHudLayoutElement(view, pLevelHeaderId);

            if (pRegionLayout == nullptr
                || pLevelLayout == nullptr
                || !hasVisibleCharacterAncestors(*pRegionLayout)
                || !hasVisibleCharacterAncestors(*pLevelLayout)
                || !shouldRenderInCurrentPass(pRegionLayout->zIndex))
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedRegion = HudUiService::resolveHudLayoutElement(view, 
                pRegionId,
                width,
                height,
                pRegionLayout->width,
                pRegionLayout->height);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedLevelHeader =
                HudUiService::resolveHudLayoutElement(view, 
                    pLevelHeaderId,
                    width,
                    height,
                    pLevelLayout->width,
                    pLevelLayout->height);

            if (!resolvedRegion || !resolvedLevelHeader)
            {
                return;
            }

            const float rowHeightPixels = skillRowHeight * resolvedRegion->scale;
            const float nameWidth =
                std::max(0.0f, resolvedLevelHeader->x - resolvedRegion->x - 6.0f * resolvedRegion->scale);
            const std::vector<CharacterSkillUiRow> displayRows =
                rows.empty() ? std::vector<CharacterSkillUiRow>{{"", "None", "", false}} : rows;

            for (size_t rowIndex = 0; rowIndex < displayRows.size(); ++rowIndex)
            {
                const CharacterSkillUiRow &row = displayRows[rowIndex];
                const uint32_t textColorAbgr = row.upgradeable ? 0xffff784au : 0xffffffffu;

                OutdoorGameView::HudLayoutElement nameLayout = {};
                nameLayout.fontName = "Lucida";
                nameLayout.textColorAbgr = textColorAbgr;
                nameLayout.textAlignX = OutdoorGameView::HudTextAlignX::Left;
                nameLayout.textAlignY = OutdoorGameView::HudTextAlignY::Middle;
                OutdoorGameView::ResolvedHudLayoutElement nameResolved = {};
                nameResolved.x = resolvedRegion->x;
                nameResolved.y = resolvedRegion->y + static_cast<float>(rowIndex) * rowHeightPixels;
                nameResolved.width = nameWidth;
                nameResolved.height = rowHeightPixels;
                nameResolved.scale = resolvedRegion->scale;
                HudUiService::renderLayoutLabel(view, nameLayout, nameResolved, row.label);

                if (!row.level.empty())
                {
                    OutdoorGameView::HudLayoutElement levelLayout = {};
                    levelLayout.fontName = "Lucida";
                    levelLayout.textColorAbgr = textColorAbgr;
                    levelLayout.textAlignX = OutdoorGameView::HudTextAlignX::Right;
                    levelLayout.textAlignY = OutdoorGameView::HudTextAlignY::Middle;
                    OutdoorGameView::ResolvedHudLayoutElement levelResolved = {};
                    levelResolved.x = resolvedLevelHeader->x;
                    levelResolved.y = nameResolved.y;
                    levelResolved.width = resolvedLevelHeader->width;
                    levelResolved.height = rowHeightPixels;
                    levelResolved.scale = resolvedLevelHeader->scale;
                    HudUiService::renderLayoutLabel(view, levelLayout, levelResolved, row.level);
                }
            }
        };

    renderSkillGroup("CharacterSkillsWeaponsListRegion", "CharacterSkillsWeaponsLevelHeader", skillUiData.weaponRows);
    renderSkillGroup("CharacterSkillsMagicListRegion", "CharacterSkillsMagicLevelHeader", skillUiData.magicRows);
    renderSkillGroup("CharacterSkillsArmorListRegion", "CharacterSkillsArmorLevelHeader", skillUiData.armorRows);
    renderSkillGroup("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows);
}

void GameplayPartyOverlayRenderer::renderActorInspectOverlay(OutdoorGameView &view, int width, int height)
{
    if (!view.m_actorInspectOverlay.active
        || view.m_pOutdoorWorldRuntime == nullptr
        || !view.m_monsterTable.has_value()
        || !bgfx::isValid(view.m_programHandle)
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorWorldRuntime::MapActorState *pActorState =
        view.m_pOutdoorWorldRuntime->mapActorState(view.m_actorInspectOverlay.runtimeActorIndex);

    if (pActorState == nullptr)
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = view.m_monsterTable->findStatsById(pActorState->monsterId);

    if (pStats == nullptr)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "ActorInspectRoot");
    const OutdoorGameView::HudLayoutElement *pPreviewLayout = HudUiService::findHudLayoutElement(view, "ActorInspectPreviewFrame");
    const OutdoorGameView::HudLayoutElement *pHealthBarBackgroundLayout =
        HudUiService::findHudLayoutElement(view, "ActorInspectHealthBarBackground");
    const OutdoorGameView::HudLayoutElement *pHealthBarFillLayout =
        HudUiService::findHudLayoutElement(view, "ActorInspectHealthBarFill");

    if (pRootLayout == nullptr
        || pPreviewLayout == nullptr
        || pHealthBarBackgroundLayout == nullptr
        || pHealthBarFillLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const float rootWidth = pRootLayout->width * popupScale;
    const float rootHeight = pRootLayout->height * popupScale;
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_actorInspectOverlay.sourceX + view.m_actorInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_actorInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_actorInspectOverlay.sourceY + (view.m_actorInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const auto submitSolidQuad =
        [&view](float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const std::string textureName = "__actor_inspect_solid_" + std::to_string(abgr);
            const OutdoorGameView::HudTextureHandle *pSolidTexture =
                HudUiService::ensureSolidHudTextureLoaded(
                    const_cast<OutdoorGameView &>(view),
                    textureName,
                    abgr);

            if (pSolidTexture == nullptr)
            {
                return;
            }

            view.submitHudTexturedQuad(*pSolidTexture, x, y, quadWidth, quadHeight);
        };

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "actorinspectcorner_topedge"
                || normalizedLayoutId == "actorinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "actorinspectcorner_leftedge"
                || normalizedLayoutId == "actorinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "actorinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent =
                    resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> previewRect =
        resolveLayout("ActorInspectPreviewFrame");
    const float previewBorderThickness = std::max(1.0f, std::round(0.125f * popupScale));
    const float previewInnerInset = previewBorderThickness;
    const uint32_t previewBackgroundColor = makeAbgrColor(0, 0, 0, 255);
    const uint32_t previewBorderColor = makeAbgrColor(255, 255, 155, 255);
    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "ActorInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "actorinspectroot"
            || toLowerCopy(pLayout->id) == "actorinspectpreviewframe")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const float healthRatio = pActorState->maxHp > 0
        ? std::clamp(
            static_cast<float>(pActorState->currentHp) / static_cast<float>(pActorState->maxHp),
            0.0f,
            1.0f)
        : 0.0f;
    uint32_t healthBarColor = makeAbgrColor(0, 255, 0);

    if (healthRatio < 0.25f)
    {
        healthBarColor = makeAbgrColor(255, 0, 0);
    }
    else if (healthRatio < 0.5f)
    {
        healthBarColor = makeAbgrColor(255, 255, 0);
    }

    if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> healthBackgroundRect =
            resolveLayout("ActorInspectHealthBarBackground"))
    {
        submitSolidQuad(
            healthBackgroundRect->x,
            healthBackgroundRect->y,
            healthBackgroundRect->width,
            healthBackgroundRect->height,
            makeAbgrColor(32, 32, 32, 220));
    }

    if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> healthFillRect =
            resolveLayout("ActorInspectHealthBarFill"))
    {
        submitSolidQuad(
            healthFillRect->x,
            healthFillRect->y,
            healthFillRect->width * healthRatio,
            healthFillRect->height,
            healthBarColor);
    }

    if (previewRect)
    {
        submitSolidQuad(previewRect->x, previewRect->y, previewRect->width, previewRect->height, previewBorderColor);
        submitSolidQuad(
            previewRect->x + previewInnerInset,
            previewRect->y + previewInnerInset,
            std::max(1.0f, previewRect->width - previewInnerInset * 2.0f),
            std::max(1.0f, previewRect->height - previewInnerInset * 2.0f),
            previewBackgroundColor);
    }

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        uint16_t spriteFrameIndex = pActorState->spriteFrameIndex;
        const size_t walkingAnimationIndex = static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Walking);

        if (walkingAnimationIndex < pActorState->actionSpriteFrameIndices.size()
            && pActorState->actionSpriteFrameIndices[walkingAnimationIndex] != 0)
        {
            spriteFrameIndex = pActorState->actionSpriteFrameIndices[walkingAnimationIndex];
        }

        const SpriteFrameEntry *pFrame =
            view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, currentAnimationTicks());

        if (pFrame == nullptr)
        {
            pFrame = view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, 0);
        }

        if (pFrame != nullptr && previewRect)
        {
            static constexpr int PreviewFacingOctant = 0;
            const ResolvedSpriteTexture resolvedTexture =
                SpriteFrameTable::resolveTexture(*pFrame, PreviewFacingOctant);
            const OutdoorGameView::BillboardTextureHandle *pExistingTexture =
                view.findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                pExistingTexture != nullptr
                    ? pExistingTexture
                    : OutdoorBillboardRenderer::ensureSpriteBillboardTexture(
                        view,
                        resolvedTexture.textureName,
                        pFrame->paletteId);

            if (pTexture != nullptr && bgfx::isValid(pTexture->textureHandle))
            {
                const float previewPadding = std::round(4.0f * popupScale);
                const float baseAvailableWidth = std::max(1.0f, previewRect->width - previewPadding * 2.0f);
                const float baseAvailableHeight = std::max(1.0f, previewRect->height - previewPadding * 2.0f);
                const float expandedAvailableWidth = std::max(1.0f, previewRect->width * 1.4f);
                const float expandedAvailableHeight = std::max(1.0f, previewRect->height * 1.4f);
                const float fitScale = std::min(
                    baseAvailableWidth / static_cast<float>(std::max(1, pTexture->width)),
                    baseAvailableHeight / static_cast<float>(std::max(1, pTexture->height)));
                const float boostedScale = std::min(
                    fitScale * 1.4f,
                    std::min(
                        expandedAvailableWidth / static_cast<float>(std::max(1, pTexture->width)),
                        expandedAvailableHeight / static_cast<float>(std::max(1, pTexture->height))));
                const float portraitZoomScale = boostedScale * 1.45f;
                const float previewWidth = static_cast<float>(pTexture->width) * portraitZoomScale;
                const float previewHeight = static_cast<float>(pTexture->height) * portraitZoomScale;
                const float previewX = std::round(previewRect->x + (previewRect->width - previewWidth) * 0.5f);
                const uint16_t scissorX = static_cast<uint16_t>(
                    std::clamp(std::lround(previewRect->x + previewInnerInset), 0l, long(width)));
                const uint16_t scissorY = static_cast<uint16_t>(
                    std::clamp(std::lround(previewRect->y + previewInnerInset), 0l, long(height)));
                const uint16_t scissorWidth = static_cast<uint16_t>(
                    std::clamp(
                        std::lround(std::max(1.0f, previewRect->width - previewInnerInset * 2.0f)),
                        1l,
                        long(width)));
                const uint16_t scissorHeight = static_cast<uint16_t>(
                    std::clamp(
                        std::lround(std::max(1.0f, previewRect->height - previewInnerInset * 2.0f)),
                        1l,
                        long(height)));
                const float visibleCenterY =
                    static_cast<float>(scissorY) + static_cast<float>(scissorHeight) * 0.5f;
                const float previewY = std::round(visibleCenterY - previewHeight * 0.48f);

                if (bgfx::getAvailTransientVertexBuffer(6, OutdoorGameView::TexturedTerrainVertex::ms_layout) >= 6)
                {
                    bgfx::TransientVertexBuffer transientVertexBuffer = {};
                    bgfx::allocTransientVertexBuffer(
                        &transientVertexBuffer,
                        6,
                        OutdoorGameView::TexturedTerrainVertex::ms_layout);
                    OutdoorGameView::TexturedTerrainVertex *pVertices =
                        reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(transientVertexBuffer.data);
                    pVertices[0] = {previewX, previewY, 0.0f, 0.0f, 0.0f};
                    pVertices[1] = {previewX + previewWidth, previewY, 0.0f, 1.0f, 0.0f};
                    pVertices[2] = {previewX + previewWidth, previewY + previewHeight, 0.0f, 1.0f, 1.0f};
                    pVertices[3] = {previewX, previewY, 0.0f, 0.0f, 0.0f};
                    pVertices[4] = {previewX + previewWidth, previewY + previewHeight, 0.0f, 1.0f, 1.0f};
                    pVertices[5] = {previewX, previewY + previewHeight, 0.0f, 0.0f, 1.0f};
                    float modelMatrix[16] = {};
                    bx::mtxIdentity(modelMatrix);
                    bgfx::setTransform(modelMatrix);
                    bgfx::setVertexBuffer(0, &transientVertexBuffer);
                    bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, pTexture->textureHandle);
                    bgfx::setScissor(scissorX, scissorY, scissorWidth, scissorHeight);
                    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                    bgfx::submit(HudViewId, view.m_texturedTerrainProgramHandle);
                    bgfx::setScissor(0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
                }
            }
        }
    }

    if (previewRect)
    {
        submitSolidQuad(previewRect->x, previewRect->y, previewRect->width, previewBorderThickness, previewBorderColor);
        submitSolidQuad(
            previewRect->x,
            previewRect->y + previewRect->height - previewBorderThickness,
            previewRect->width,
            previewBorderThickness,
            previewBorderColor);
        submitSolidQuad(
            previewRect->x,
            previewRect->y,
            previewBorderThickness,
            previewRect->height,
            previewBorderColor);
        submitSolidQuad(
            previewRect->x + previewRect->width - previewBorderThickness,
            previewRect->y,
            previewBorderThickness,
            previewRect->height,
            previewBorderColor);
    }

    const std::string attackText = joinNonEmptyTexts({
        pStats->attack1Type,
        (pStats->attack2Chance > 0 || !pStats->attack2Type.empty()) ? pStats->attack2Type : std::string()});
    const std::string damageText = joinNonEmptyTexts({
        formatMonsterDamageText(pStats->attack1Damage),
        (pStats->attack2Chance > 0 || pStats->attack2Damage.diceRolls > 0)
            ? formatMonsterDamageText(pStats->attack2Damage)
            : std::string()});
    const std::string spellText = joinNonEmptyTexts({
        pStats->hasSpell1 ? pStats->spell1Name : std::string(),
        pStats->hasSpell2 ? pStats->spell2Name : std::string()});
    std::vector<std::string> activeEffects;

    if (pActorState->isDead)
    {
        activeEffects.push_back("Dead");
    }
    else
    {
        if (pActorState->stunRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Stunned");
        }

        if (pActorState->paralyzeRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Paralyzed");
        }

        if (pActorState->slowRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Slow");
        }

        if (pActorState->fearRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Afraid");
        }

        if (pActorState->shrinkRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Shrunk");
        }

        if (pActorState->darkGraspRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Dark Grasp");
        }

        switch (pActorState->controlMode)
        {
            case OutdoorWorldRuntime::ActorControlMode::Charm:
                activeEffects.push_back("Charmed");
                break;
            case OutdoorWorldRuntime::ActorControlMode::Berserk:
                activeEffects.push_back("Berserk");
                break;
            case OutdoorWorldRuntime::ActorControlMode::Enslaved:
                activeEffects.push_back("Enslaved");
                break;
            case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
                activeEffects.push_back("Controlled");
                break;
            case OutdoorWorldRuntime::ActorControlMode::Reanimated:
                activeEffects.push_back("Reanimated");
                break;
            case OutdoorWorldRuntime::ActorControlMode::None:
                break;
        }
    }

    const std::string effectsText = activeEffects.empty() ? "None" : joinNonEmptyTexts(activeEffects);
    const auto renderTextForLayout =
        [&view, &resolveLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(pLayoutId);

            if (pLayout == nullptr || !resolved || text.empty())
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    for (const char *pLabelId : {
             "ActorInspectHitPointsLabel",
             "ActorInspectArmorClassLabel",
             "ActorInspectAttackLabel",
             "ActorInspectDamageLabel",
             "ActorInspectSpellLabel",
             "ActorInspectEffectsHeader",
             "ActorInspectResistancesHeader",
             "ActorInspectResistanceFireLabel",
             "ActorInspectResistanceAirLabel",
             "ActorInspectResistanceWaterLabel",
             "ActorInspectResistanceEarthLabel",
             "ActorInspectResistanceMindLabel",
             "ActorInspectResistanceSpiritLabel",
             "ActorInspectResistanceBodyLabel",
             "ActorInspectResistanceLightLabel",
             "ActorInspectResistanceDarkLabel",
             "ActorInspectResistancePhysicalLabel"})
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLabelId);

        if (pLayout != nullptr)
        {
            renderTextForLayout(pLabelId, pLayout->labelText);
        }
    }

    renderTextForLayout("ActorInspectTitle", pActorState->displayName);
    renderTextForLayout(
        "ActorInspectHitPointsValue",
        std::to_string(std::max(0, pActorState->currentHp))
            + " / "
            + std::to_string(std::max(0, pActorState->maxHp)));
    renderTextForLayout(
        "ActorInspectArmorClassValue",
        std::to_string(view.m_pOutdoorWorldRuntime->effectiveMapActorArmorClass(view.m_actorInspectOverlay.runtimeActorIndex)));
    renderTextForLayout("ActorInspectAttackValue", attackText);
    renderTextForLayout("ActorInspectDamageValue", damageText);
    renderTextForLayout("ActorInspectSpellValue", spellText);
    renderTextForLayout("ActorInspectEffectsBody", effectsText);
    renderTextForLayout("ActorInspectResistanceFireValue", formatMonsterResistanceText(pStats->fireResistance));
    renderTextForLayout("ActorInspectResistanceAirValue", formatMonsterResistanceText(pStats->airResistance));
    renderTextForLayout("ActorInspectResistanceWaterValue", formatMonsterResistanceText(pStats->waterResistance));
    renderTextForLayout("ActorInspectResistanceEarthValue", formatMonsterResistanceText(pStats->earthResistance));
    renderTextForLayout("ActorInspectResistanceMindValue", formatMonsterResistanceText(pStats->mindResistance));
    renderTextForLayout("ActorInspectResistanceSpiritValue", formatMonsterResistanceText(pStats->spiritResistance));
    renderTextForLayout("ActorInspectResistanceBodyValue", formatMonsterResistanceText(pStats->bodyResistance));
    renderTextForLayout("ActorInspectResistanceLightValue", formatMonsterResistanceText(pStats->lightResistance));
    renderTextForLayout("ActorInspectResistanceDarkValue", formatMonsterResistanceText(pStats->darkResistance));
    renderTextForLayout("ActorInspectResistancePhysicalValue", formatMonsterResistanceText(pStats->physicalResistance));
}
} // namespace OpenYAMM::Game
