#include "game/indoor/IndoorGameView.h"

#include "engine/BgfxContext.h"
#include "game/arpg/ArpgModeLoot.h"
#include "game/app/GameSession.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/gameplay/MercenaryRecruitmentRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/audio/SoundIds.h"
#include "game/items/ItemRuntime.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/tables/MergedBaseTables.h"
#include "game/ui/GameplayDebugOverlayRenderer.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>
#include <bgfx/bgfx.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <functional>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
IndoorGameView::IndoorGameView(GameSession &gameSession)
    : m_gameSession(gameSession)
{
}

namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr float WalkingSoundMovementSpeedThreshold = 20.0f;
constexpr float WalkingMotionHoldSeconds = 0.125f;
constexpr uint16_t HudViewId = 2;
constexpr uint64_t GameplayMouseLookCursorSyncIntervalTicks = 100;
const std::filesystem::path AutosavePath = std::filesystem::path("saves") / "autosave.oysav";
using SpellbookPointerTargetType = IndoorSpellbookPointerTargetType;
using SpellbookPointerTarget = IndoorSpellbookPointerTarget;
using CharacterPointerTargetType = IndoorCharacterPointerTargetType;
using CharacterPointerTarget = IndoorCharacterPointerTarget;

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

uint32_t makeArpgModeHudColor(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

InventoryItem normalizedArpgModeCorpseInventoryItem(const GameplayChestItemState &item)
{
    InventoryItem inventoryItem = item.item;

    if (inventoryItem.objectDescriptionId == 0)
    {
        inventoryItem.objectDescriptionId = item.itemId;
    }

    if (inventoryItem.quantity == 0)
    {
        inventoryItem.quantity = item.quantity;
    }

    if (inventoryItem.width == 0)
    {
        inventoryItem.width = item.width;
    }

    if (inventoryItem.height == 0)
    {
        inventoryItem.height = item.height;
    }

    return inventoryItem;
}

std::string arpgModeCorpseLootLabel(
    const GameplayChestItemState &item,
    const ItemTable &itemTable,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    if (item.isGold)
    {
        return std::to_string(item.goldAmount) + " Gold";
    }

    const InventoryItem inventoryItem = normalizedArpgModeCorpseInventoryItem(item);
    const ItemDefinition *pItemDefinition = itemTable.get(inventoryItem.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return "Item";
    }

    std::string label =
        ItemRuntime::displayName(inventoryItem, *pItemDefinition, pStandardEnchantTable, pSpecialEnchantTable);

    if (inventoryItem.quantity > 1)
    {
        label = std::to_string(inventoryItem.quantity) + "x " + label;
    }

    return label.empty() ? "Item" : label;
}

ArpgModeLootFacts arpgModeCorpseLootFacts(const GameplayChestItemState &item, const ItemTable &itemTable)
{
    ArpgModeLootFacts facts = {};
    facts.isGold = item.isGold;
    facts.goldAmount = item.goldAmount;

    if (item.isGold)
    {
        return facts;
    }

    const InventoryItem inventoryItem = normalizedArpgModeCorpseInventoryItem(item);
    const ItemDefinition *pItemDefinition = itemTable.get(inventoryItem.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return facts;
    }

    facts.value = pItemDefinition->value;
    facts.highestTreasureLevel = arpgModeHighestTreasureLevel(*pItemDefinition);
    facts.reagentPower = arpgModeReagentPower(*pItemDefinition);
    facts.hasStandardEnchant = inventoryItem.standardEnchantId != 0;
    facts.hasSpecialEnchant = inventoryItem.specialEnchantId != 0;
    facts.hasArtifactOrRelicIdentity =
        inventoryItem.rarity == ItemRarity::Artifact
        || inventoryItem.rarity == ItemRarity::Relic
        || pItemDefinition->rarity == ItemRarity::Artifact
        || pItemDefinition->rarity == ItemRarity::Relic;
    facts.hasRareIdentity =
        pItemDefinition->rarity != ItemRarity::Common
        || inventoryItem.artifactId != 0
        || ItemRuntime::isRareItem(*pItemDefinition);
    return facts;
}

void drawArpgModeSolidHudRect(
    GameplayScreenRuntime &screenRuntime,
    const std::string &textureName,
    float x,
    float y,
    float width,
    float height,
    uint32_t colorAbgr)
{
    const std::optional<GameplayScreenRuntime::HudTextureHandle> texture =
        screenRuntime.gameplayUiRuntime().ensureSolidHudTextureLoaded(textureName, colorAbgr);

    if (!texture)
    {
        return;
    }

    screenRuntime.submitHudTexturedQuad(*texture, x, y, width, height);
}

bool windowHasInputFocus(SDL_Window *pWindow)
{
    return pWindow != nullptr && (SDL_GetWindowFlags(pWindow) & SDL_WINDOW_INPUT_FOCUS) != 0;
}

bool isAutosavePath(const std::filesystem::path &path)
{
    return toLowerCopy(path.stem().string()) == "autosave";
}

struct ParsedHudFontGlyphMetrics
{
    int leftSpacing = 0;
    int width = 0;
    int rightSpacing = 0;
};

struct ParsedHudBitmapFont
{
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    std::array<ParsedHudFontGlyphMetrics, 256> glyphMetrics = {{}};
    std::array<uint32_t, 256> glyphOffsets = {{}};
    std::vector<uint8_t> pixels;
};

struct CharacterInventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
    float scale = 1.0f;
};

struct CharacterInventoryItemRect
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

struct SplitCharacterStatValue
{
    std::string actualText = "0";
    std::string baseText = "0";
    uint32_t actualColorAbgr = 0xffffffffu;
    bool active = false;
};

CharacterInventoryGridMetrics computeCharacterInventoryGridMetrics(
    const GameplayResolvedHudLayoutElement &resolved)
{
    CharacterInventoryGridMetrics metrics = {};
    metrics.x = resolved.x;
    metrics.y = resolved.y;
    metrics.scale = resolved.scale;
    metrics.cellWidth = resolved.width / static_cast<float>(std::max(1, Character::InventoryWidth));
    metrics.cellHeight = resolved.height / static_cast<float>(std::max(1, Character::InventoryHeight));
    return metrics;
}

CharacterInventoryItemRect computeCharacterInventoryItemRect(
    const CharacterInventoryGridMetrics &gridMetrics,
    const InventoryItem &item,
    float textureWidth,
    float textureHeight)
{
    const float slotSpanWidth = static_cast<float>(item.width) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(item.height) * gridMetrics.cellHeight;
    const float offsetX = (slotSpanWidth - textureWidth) * 0.5f;
    const float offsetY = (slotSpanHeight - textureHeight) * 0.5f;

    CharacterInventoryItemRect rect = {};
    rect.x = std::round(gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth + offsetX);
    rect.y = std::round(gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
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
        const std::string canonicalName = pSkillNames[skillIndex];
        const CharacterSkill *pSkill = character.findSkillByCanonicalName(canonicalName);

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
    appendCharacterSkillUiRows(*pCharacter, data.weaponRows, shownSkillNames, WeaponSkillNames, std::size(WeaponSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.magicRows, shownSkillNames, MagicSkillNames, std::size(MagicSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.armorRows, shownSkillNames, ArmorSkillNames, std::size(ArmorSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.miscRows, shownSkillNames, MiscSkillNames, std::size(MiscSkillNames));

    std::vector<CharacterSkillUiRow> extraMiscRows;

    for (const auto &[canonicalName, skill] : pCharacter->skills)
    {
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

SplitCharacterStatValue makeSplitCharacterStatValue(const CharacterSheetValue &value)
{
    SplitCharacterStatValue result = {};
    result.active = true;
    result.baseText = std::to_string(value.base);
    result.actualText = value.infinite ? "INF" : std::to_string(value.actual);

    if (!value.infinite)
    {
        if (value.actual > value.base)
        {
            result.actualColorAbgr = 0xff00ff00u;
        }
        else if (value.actual < value.base)
        {
            result.actualColorAbgr = 0xff0000ffu;
        }
    }

    return result;
}

SplitCharacterStatValue makeSplitCharacterResourceValue(int currentValue, int maximumValue)
{
    SplitCharacterStatValue result = {};
    result.active = true;
    result.actualText = std::to_string(currentValue);
    result.baseText = std::to_string(maximumValue);

    if (currentValue <= 0)
    {
        result.actualColorAbgr = 0xff0000ffu;
    }
    else if (maximumValue > 0 && currentValue * 2 < maximumValue)
    {
        result.actualColorAbgr = 0xff00ffffu;
    }

    return result;
}

bool tryGetSplitCharacterStatValue(
    const std::string &normalizedLayoutId,
    const CharacterSheetSummary &summary,
    SplitCharacterStatValue &value)
{
    if (normalizedLayoutId == "characterstatmightvalue")
    {
        value = makeSplitCharacterStatValue(summary.might);
        return true;
    }

    if (normalizedLayoutId == "characterstatintellectvalue")
    {
        value = makeSplitCharacterStatValue(summary.intellect);
        return true;
    }

    if (normalizedLayoutId == "characterstatpersonalityvalue")
    {
        value = makeSplitCharacterStatValue(summary.personality);
        return true;
    }

    if (normalizedLayoutId == "characterstatendurancevalue")
    {
        value = makeSplitCharacterStatValue(summary.endurance);
        return true;
    }

    if (normalizedLayoutId == "characterstataccuracyvalue")
    {
        value = makeSplitCharacterStatValue(summary.accuracy);
        return true;
    }

    if (normalizedLayoutId == "characterstatspeedvalue")
    {
        value = makeSplitCharacterStatValue(summary.speed);
        return true;
    }

    if (normalizedLayoutId == "characterstatluckvalue")
    {
        value = makeSplitCharacterStatValue(summary.luck);
        return true;
    }

    if (normalizedLayoutId == "characterstathitpointsvalue")
    {
        value = makeSplitCharacterResourceValue(summary.health.current, summary.health.maximum);
        return true;
    }

    if (normalizedLayoutId == "characterstatlevelvalue")
    {
        value = makeSplitCharacterStatValue(summary.level);
        return true;
    }

    if (normalizedLayoutId == "characterstatfireresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.fireResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatairresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.airResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatwaterresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.waterResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatearthresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.earthResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatmindresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.mindResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatbodyresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.bodyResistance);
        return true;
    }

    return false;
}

bool isBodyEquipmentVisualSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Boots:
            return true;

        case EquipmentSlot::OffHand:
        case EquipmentSlot::MainHand:
        case EquipmentSlot::Bow:
        case EquipmentSlot::Gauntlets:
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
    return jewelryOverlayOpen
        ? isBodyEquipmentVisualSlot(slot) || isJewelryOverlayEquipmentSlot(slot)
        : !isJewelryOverlayEquipmentSlot(slot);
}

bool usesAlternateCloakBeltEquippedVariant(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Cloak || slot == EquipmentSlot::Belt;
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

void setCharacterSkillRegionHeight(
    std::unordered_map<std::string, float> &runtimeHeightOverrides,
    float skillRowHeight,
    const char *pLayoutId,
    size_t rowCount)
{
    runtimeHeightOverrides[toLowerCopy(pLayoutId)] =
        skillRowHeight * static_cast<float>(std::max<size_t>(1, rowCount));
}

const CharacterDollEntry *resolveCharacterDollEntry(
    const CharacterDollTable *pCharacterDollTable,
    const Character *pCharacter)
{
    if (pCharacterDollTable == nullptr || pCharacter == nullptr)
    {
        return nullptr;
    }

    const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(pCharacter->characterDataId);

    if (pEntry != nullptr)
    {
        return pEntry;
    }

    return pCharacterDollTable->getCharacter(1);
}

int32_t readInt32Le(const uint8_t *pBytes)
{
    return static_cast<int32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

uint32_t readUint32Le(const uint8_t *pBytes)
{
    return static_cast<uint32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

bool validateParsedHudBitmapFont(
    const ParsedHudBitmapFont &font,
    const std::vector<uint8_t> &pixels)
{
    if (font.firstChar < 0
        || font.firstChar > 255
        || font.lastChar < 0
        || font.lastChar > 255
        || font.firstChar > font.lastChar
        || font.fontHeight <= 0)
    {
        return false;
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const ParsedHudFontGlyphMetrics &metrics = font.glyphMetrics[glyphIndex];

        if (glyphIndex < font.firstChar || glyphIndex > font.lastChar)
        {
            continue;
        }

        if (metrics.width < 0 || metrics.width > 1024 || metrics.leftSpacing < -512 || metrics.leftSpacing > 512
            || metrics.rightSpacing < -512 || metrics.rightSpacing > 512)
        {
            return false;
        }

        const uint64_t glyphSize = static_cast<uint64_t>(font.fontHeight) * static_cast<uint64_t>(metrics.width);
        const uint64_t glyphEnd = static_cast<uint64_t>(font.glyphOffsets[glyphIndex]) + glyphSize;

        if (glyphEnd > pixels.size())
        {
            return false;
        }
    }

    return true;
}

std::optional<ParsedHudBitmapFont> parseHudBitmapFont(const std::vector<uint8_t> &bytes)
{
    constexpr size_t FontHeaderSize = 32;
    constexpr size_t Mm7AtlasSize = 4096;
    constexpr size_t MmxAtlasSize = 1280;

    if (bytes.size() < FontHeaderSize + MmxAtlasSize)
    {
        return std::nullopt;
    }

    const uint8_t *pBytes = bytes.data();

    if (pBytes[2] != 8 || pBytes[3] != 0 || pBytes[4] != 0 || pBytes[6] != 0 || pBytes[7] != 0)
    {
        return std::nullopt;
    }

    ParsedHudBitmapFont mm7Font = {};
    mm7Font.firstChar = pBytes[0];
    mm7Font.lastChar = pBytes[1];
    mm7Font.fontHeight = pBytes[5];

    if (bytes.size() >= FontHeaderSize + Mm7AtlasSize)
    {
        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t metricOffset = FontHeaderSize + static_cast<size_t>(glyphIndex) * 12;
            mm7Font.glyphMetrics[glyphIndex].leftSpacing = readInt32Le(&pBytes[metricOffset]);
            mm7Font.glyphMetrics[glyphIndex].width = readInt32Le(&pBytes[metricOffset + 4]);
            mm7Font.glyphMetrics[glyphIndex].rightSpacing = readInt32Le(&pBytes[metricOffset + 8]);
        }

        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t offsetPosition = FontHeaderSize + 256 * 12 + static_cast<size_t>(glyphIndex) * 4;
            mm7Font.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
        }

        mm7Font.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + Mm7AtlasSize), bytes.end());

        if (validateParsedHudBitmapFont(mm7Font, mm7Font.pixels))
        {
            return mm7Font;
        }
    }

    ParsedHudBitmapFont mmxFont = {};
    mmxFont.firstChar = pBytes[0];
    mmxFont.lastChar = pBytes[1];
    mmxFont.fontHeight = pBytes[5];

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        mmxFont.glyphMetrics[glyphIndex].width = pBytes[FontHeaderSize + glyphIndex];
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t offsetPosition = FontHeaderSize + 256 + static_cast<size_t>(glyphIndex) * 4;
        mmxFont.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
    }

    mmxFont.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + MmxAtlasSize), bytes.end());

    if (!validateParsedHudBitmapFont(mmxFont, mmxFont.pixels))
    {
        return std::nullopt;
    }

    return mmxFont;
}

bool usesBlackTransparencyKey(std::string_view textureName)
{
    const std::string normalizedName = toLowerCopy(std::string(textureName));
    return normalizedName.rfind("mapdir", 0) == 0 || normalizedName.rfind("micon", 0) == 0;
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

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
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

UiViewportRect computeAnchorRect(
    UiLayoutManager::LayoutAnchorSpace anchorSpace,
    int screenWidth,
    int screenHeight)
{
    if (anchorSpace == UiLayoutManager::LayoutAnchorSpace::Screen)
    {
        UiViewportRect rect = {};
        rect.width = static_cast<float>(screenWidth);
        rect.height = static_cast<float>(screenHeight);
        return rect;
    }

    return computeUiViewportRect(screenWidth, screenHeight);
}

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (static_cast<uint32_t>(blue) << 16) | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

bool isResidentSelectionMode(const EventDialogContent &dialog)
{
    return !dialog.actions.empty()
        && std::all_of(
            dialog.actions.begin(),
            dialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
}

uint32_t currentDialogueHostHouseId(const EventRuntimeState *pEventRuntimeState)
{
    return pEventRuntimeState != nullptr ? pEventRuntimeState->dialogueState.hostHouseId : 0;
}

bool indoorActorExplicitlyHostile(const MapDeltaActor &actor)
{
    return (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Aggressor)) != 0;
}

std::optional<GenericActorDialogResolution> resolveIndoorActorDialog(
    const GameSession &gameSession,
    const std::optional<MapStatsEntry> &map,
    const EventRuntimeState &eventRuntimeState,
    const MapDeltaActor &actor,
    const GameplayActorInspectState &inspectState,
    size_t actorIndex)
{
    return resolveGenericActorDialog(
        map ? map->fileName : std::string(),
        inspectState.displayName,
        actor.group,
        eventRuntimeState,
        gameSession.data().npcDialogTable(),
        &gameSession.data().mergedMonsterPortraitTable(),
        map ? &*map : nullptr,
        &gameSession.data().mergedNewsAreaTopicTable(),
        &gameSession.data().mergedNewsContinentTopicTable(),
        &gameSession.data().mergedNpcNameTable(),
        &gameSession.data().mergedNpcProfessionTable(),
        &gameSession.data().mergedBolsterMapTable(),
        &gameSession.data().mergedBolsterMonsterTable(),
        inspectState.monsterId > 0 ? static_cast<uint32_t>(inspectState.monsterId) : 0,
        actorIndex);
}

std::string generatedActorDisplayTitle(
    const GameSession &gameSession,
    const GenericActorDialogResolution &resolution)
{
    if (!resolution.generatedNpc || resolution.generatedName.empty())
    {
        return {};
    }

    const MergedNpcProfessionEntry *pProfession =
        gameSession.data().mergedNpcProfessionTable().get(resolution.generatedProfessionId);

    if (pProfession == nullptr || pProfession->profession.empty())
    {
        return resolution.generatedName;
    }

    return resolution.generatedName + " the " + pProfession->profession;
}
}

bool IndoorGameView::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    IndoorRenderer &indoorRenderer,
    IndoorSceneRuntime &sceneRuntime,
    GameAudioSystem *pGameAudioSystem)
{
    shutdown();
    const GameDataRepository &data = m_gameSession.data();

    m_pAssetFileSystem = &assetFileSystem;
    m_pIndoorRenderer = &indoorRenderer;
    m_pIndoorSceneRuntime = &sceneRuntime;
    m_pGameAudioSystem = pGameAudioSystem;
    m_map = map;
    m_pIndoorSceneRuntime->worldRuntime().bindGameplayView(this);
    m_gameSession.gameplayScreenRuntime().bindSceneAdapter(this);
    m_gameSession.gameplayScreenRuntime().bindAudioSystem(m_pGameAudioSystem);
    m_gameSession.gameplayScreenRuntime().bindSettings(&m_settings);
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    EventRuntimeState *pMutableEventRuntimeState = m_pIndoorSceneRuntime->worldRuntime().eventRuntimeState();

    if (pMutableEventRuntimeState != nullptr)
    {
        refreshMercenaryRecruitmentForCurrentMap(
            map,
            sceneRuntime.partyRuntime().party(),
            *pMutableEventRuntimeState,
            MercenaryRecruitmentTables{
                .pHouseTable = &data.houseTable(),
                .pNpcNameTable = &data.mergedNpcNameTable(),
                .pCharacterSelectionTable = &data.mergedCharacterSelectionTable(),
                .pCharacterDollTable = &data.characterDollTable(),
                .pClassSkillTable = &data.classSkillTable(),
                .pClassMultiplierTable = &data.classMultiplierTable(),
                .pRaceStartingStatsTable = &data.raceStartingStatsTable(),
                .pItemTable = &data.itemTable(),
                .pStandardItemEnchantTable = &data.standardItemEnchantTable(),
                .pSpecialItemEnchantTable = &data.specialItemEnchantTable(),
                .pSpellTable = &data.spellTable(),
            });
    }

    const EventRuntimeState *pEventRuntimeState = pMutableEventRuntimeState;
    screenRuntime.resetOverlayInteractionState(
        pEventRuntimeState != nullptr && !pEventRuntimeState->hiredNpcFollowers.empty());
    const GameplayScreenRuntime::SharedUiBootstrapResult sharedUiBootstrap =
        screenRuntime.initializeSharedUiRuntime(
            GameplayScreenRuntime::SharedUiBootstrapConfig{
                .pAssetFileSystem = &assetFileSystem,
                .portraitMemberCount = sceneRuntime.partyRuntime().party().members().size(),
                .preloadReferencedAssets = false,
            });

    if (!sharedUiBootstrap.layoutsLoaded)
    {
        return false;
    }

    return true;
}

void IndoorGameView::setSettingsSnapshot(const GameSettings &settings)
{
    m_settings = settings;

    IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime != nullptr)
    {
        Party &party = pRuntime->party();
        party.setDebugDamageImmune(settings.immortal);
        party.setDebugUnlimitedMana(settings.unlimitedMana);
    }
}

bool IndoorGameView::arpgModeFirstPersonUseMode() const
{
    return m_gameSession.gameplayScreenState().arpgModeFirstPersonUseMode();
}

void IndoorGameView::render(int width, int height, const GameplayInputFrame &input, float deltaSeconds)
{
    m_lastRenderWidth = width;
    m_lastRenderHeight = height;
    m_renderGameplayUiThisFrame = true;

    GameplayHudRenderBackend hudRenderBackend = {};
    bgfx::ProgramHandle invalidProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle invalidSamplerHandle = BGFX_INVALID_HANDLE;
    hudRenderBackend.texturedProgramHandle =
        m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->hudTexturedProgramHandle() : invalidProgramHandle;
    hudRenderBackend.textureSamplerHandle =
        m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->hudTextureSamplerHandle() : invalidSamplerHandle;
    hudRenderBackend.viewId = HudViewId;
    m_gameSession.gameplayScreenRuntime().bindHudRenderBackend(hudRenderBackend);

    presentPendingEventFeedback();

    SDL_Window *pWindow = SDL_GetMouseFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetKeyboardFocus();
    }

    GameplayScreenRuntime &overlayContext = m_gameSession.gameplayScreenRuntime();

    if (m_pendingSavePreviewCapture.active
        && m_pendingSavePreviewCapture.screenshotRequested
        && m_gameSession.canSaveGameToPath())
    {
        const std::optional<Engine::BgfxContext::ScreenshotCapture> screenshot =
            Engine::BgfxContext::consumeScreenshot(m_pendingSavePreviewCapture.requestId);

        if (screenshot)
        {
            const std::vector<uint8_t> previewPixels =
                SavePreviewImage::cropAndScaleBgraPreview(
                    screenshot->bgraPixels,
                    static_cast<int>(screenshot->width),
                    static_cast<int>(screenshot->height),
                    410,
                    253);
            const std::vector<uint8_t> previewBmp = SavePreviewImage::encodeBgraToBmp(410, 253, previewPixels);
            std::string error;

            if (!previewBmp.empty()
                && m_gameSession.saveGameToPath(
                    m_pendingSavePreviewCapture.savePath,
                    m_pendingSavePreviewCapture.saveName,
                    previewBmp,
                    error))
            {
                GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
                screenRuntime.refreshSaveGameOverlaySlots();

                if (m_pendingSavePreviewCapture.closeUiOnSuccess)
                {
                    screenRuntime.saveGameScreenState() = {};
                    screenRuntime.closeMenuOverlay();
                }
            }

            m_pendingSavePreviewCapture = {};
        }
        else if (SDL_GetTicks() - m_pendingSavePreviewCapture.startedTicks > 3000u)
        {
            m_pendingSavePreviewCapture = {};
        }
    }

    GameplayUiController::UtilitySpellOverlayState &utilityOverlay = overlayContext.utilitySpellOverlay();

    if (utilityOverlay.lloydSetPreviewCapturePending && utilityOverlay.lloydSetPreviewScreenshotRequested)
    {
        const std::optional<Engine::BgfxContext::ScreenshotCapture> screenshot =
            Engine::BgfxContext::consumeScreenshot(utilityOverlay.lloydSetPreviewRequestId);
        const bool timedOut = SDL_GetTicks() - utilityOverlay.lloydSetPreviewStartedTicks > 3000u;

        if (screenshot || timedOut)
        {
            PartySpellCastRequest request = utilityOverlay.lloydSetPreviewRequest;
            const std::string spellName = utilityOverlay.lloydSetPreviewSpellName;

            if (screenshot)
            {
                request.utilityPreviewPixelsBgra =
                    SavePreviewImage::cropAndScaleBgraPreview(
                        screenshot->bgraPixels,
                        static_cast<int>(screenshot->width),
                        static_cast<int>(screenshot->height),
                        92,
                        68);

                if (!request.utilityPreviewPixelsBgra.empty())
                {
                    request.utilityPreviewWidth = 92;
                    request.utilityPreviewHeight = 68;
                }
            }

            utilityOverlay.lloydSetPreviewCapturePending = false;
            utilityOverlay.lloydSetPreviewScreenshotRequested = false;
            utilityOverlay.lloydSetPreviewStartedTicks = 0;
            utilityOverlay.lloydSetPreviewRequestId.clear();
            utilityOverlay.lloydSetPreviewSpellName.clear();
            utilityOverlay.lloydSetPreviewRequest = {};
            overlayContext.tryCastSpellRequest(request, spellName);
        }
    }

    const bool captureSavePreviewThisFrame =
        m_pendingSavePreviewCapture.active && !m_pendingSavePreviewCapture.screenshotRequested;
    const bool captureLloydsBeaconPreviewThisFrame =
        !captureSavePreviewThisFrame
        && utilityOverlay.lloydSetPreviewCapturePending
        && !utilityOverlay.lloydSetPreviewScreenshotRequested;
    m_renderGameplayUiThisFrame = !captureSavePreviewThisFrame && !captureLloydsBeaconPreviewThisFrame;

    updateItemInspectOverlayState(width, height, input);

    const GameplaySharedInputFrameResult &sharedInputFrameResult = m_gameSession.sharedInputFrameResult();
    syncGameplayMouseLookMode(pWindow, sharedInputFrameResult.mouseLookPolicy.mouseLookActive);
    updateArpgModeLootAutoPickup(deltaSeconds);

    const bool lootLabelActivated =
        m_settings.arpgModeEnabled
        && !arpgModeFirstPersonUseMode()
        && input.leftMouseButton.pressed
        && tryActivateArpgModeLootLabelAt(input.pointerX, input.pointerY);

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->setGameplayMouseLookMode(
            sharedInputFrameResult.mouseLookPolicy.mouseLookActive,
            sharedInputFrameResult.mouseLookPolicy.cursorModeActive);
    }

    if (m_pIndoorRenderer != nullptr)
    {
        const bool pendingSpellTargetActive = m_gameSession.gameplayScreenState().pendingSpellTarget().active;
        const bool allowWorldInput =
            !sharedInputFrameResult.mouseLookPolicy.cursorModeActive
            && !sharedInputFrameResult.journalInputConsumed
            && !sharedInputFrameResult.worldInputBlocked
            && !pendingSpellTargetActive
            && !lootLabelActivated;
        m_pIndoorRenderer->render(
            width,
            height,
            m_gameSession,
            input,
            deltaSeconds,
            allowWorldInput);
        renderArpgModeLootOverlay(width, height, deltaSeconds);
    }

    if (captureSavePreviewThisFrame)
    {
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, m_pendingSavePreviewCapture.requestId.c_str());
        m_pendingSavePreviewCapture.screenshotRequested = true;
    }
    else if (captureLloydsBeaconPreviewThisFrame)
    {
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, utilityOverlay.lloydSetPreviewRequestId.c_str());
        utilityOverlay.lloydSetPreviewScreenshotRequested = true;
    }

    updateFootstepAudio(deltaSeconds);
    updateDialogueVideoPlayback(deltaSeconds);

    presentPendingEventFeedback();

    updateActorInspectOverlayState(width, height, input);
}

GameplayWorldUiRenderState IndoorGameView::gameplayUiRenderState(int width, int height) const
{
    return GameplayWorldUiRenderState{
        .canRenderHudOverlays =
            m_renderGameplayUiThisFrame
            &&
            m_pIndoorRenderer != nullptr
            && m_pIndoorRenderer->hasHudRenderResources()
            && width > 0
            && height > 0,
        .renderGameplayHud = m_renderGameplayUiThisFrame,
        .renderDebugFallbacks = true,
    };
}

void IndoorGameView::shutdown()
{
    syncGameplayMouseLookMode(SDL_GetMouseFocus(), false);

    if (m_pIndoorSceneRuntime != nullptr)
    {
        m_pIndoorSceneRuntime->worldRuntime().bindGameplayView(nullptr);
        m_pIndoorSceneRuntime->worldRuntime().bindRenderer(nullptr);
    }

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->setGameplayMouseLookMode(false, false);
    }

    if (m_pGameAudioSystem != nullptr)
    {
        m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
    }

    m_pAssetFileSystem = nullptr;
    m_pIndoorRenderer = nullptr;
    m_pIndoorSceneRuntime = nullptr;
    m_pGameAudioSystem = nullptr;
    m_gameSession.gameplayScreenRuntime().clearSceneAdapter(this);
    m_gameSession.gameplayScreenRuntime().bindAudioSystem(nullptr);
    m_map.reset();
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    screenRuntime.actorInspectOverlay() = {};
    screenRuntime.clearSharedUiRuntime();
    screenRuntime.clearUiControllerRuntimeState();
    screenRuntime.resetOverlayInteractionState();
    m_gameSession.gameplayScreenState().gameplayMouseLookState().clear();
    m_gameSession.previousKeyboardState().fill(0);
    m_gameSession.gameplayScreenRuntime().resetHudTransientState();
    m_hasLastFootstepPosition = false;
    m_walkingMotionHoldSeconds = 0.0f;
    m_activeWalkingSoundId = std::nullopt;
}

void IndoorGameView::updateArpgModeLootAutoPickup(float deltaSeconds)
{
    updateArpgModeCombatFeedback(deltaSeconds);

    for (ArpgModeLootFloatingText &floatingText : m_arpgModeLootFloatingTexts)
    {
        floatingText.remainingSeconds =
            std::max(0.0f, floatingText.remainingSeconds - std::max(0.0f, deltaSeconds));
    }

    m_arpgModeLootFloatingTexts.erase(
        std::remove_if(
            m_arpgModeLootFloatingTexts.begin(),
            m_arpgModeLootFloatingTexts.end(),
            [](const ArpgModeLootFloatingText &floatingText)
            {
                return floatingText.remainingSeconds <= 0.0f;
            }),
        m_arpgModeLootFloatingTexts.end());

    if (!m_settings.arpgModeEnabled || arpgModeFirstPersonUseMode() || m_pIndoorSceneRuntime == nullptr)
    {
        return;
    }

    IndoorWorldRuntime &worldRuntime = m_pIndoorSceneRuntime->worldRuntime();
    const std::vector<IndoorWorldRuntime::ArpgModeGoldPickup> pickups =
        worldRuntime.collectNearbyArpgModeCorpseGold(220.0f);
    uint32_t totalGold = 0;

    for (const IndoorWorldRuntime::ArpgModeGoldPickup &pickup : pickups)
    {
        totalGold += pickup.amount;
        m_arpgModeLootFloatingTexts.push_back(
            ArpgModeLootFloatingText{
                .text = "+" + std::to_string(pickup.amount) + " gold",
                .x = pickup.x,
                .y = pickup.y,
                .z = pickup.z + 48.0f,
                .remainingSeconds = 1.35f,
                .durationSeconds = 1.35f,
            });
    }

    if (totalGold > 0)
    {
        setStatusBarEvent("+" + std::to_string(totalGold) + " gold");
    }
}

void IndoorGameView::updateArpgModeCombatFeedback(float deltaSeconds)
{
    const float elapsedSeconds = std::max(0.0f, deltaSeconds);

    if (m_arpgModeCombatTargetState.active)
    {
        m_arpgModeCombatTargetState.remainingSeconds =
            std::max(0.0f, m_arpgModeCombatTargetState.remainingSeconds - elapsedSeconds);
        m_arpgModeCombatTargetState.active = m_arpgModeCombatTargetState.remainingSeconds > 0.0f;
    }

    for (ArpgModeCombatFloatingText &floatingText : m_arpgModeCombatFloatingTexts)
    {
        floatingText.remainingSeconds = std::max(0.0f, floatingText.remainingSeconds - elapsedSeconds);
    }

    m_arpgModeCombatFloatingTexts.erase(
        std::remove_if(
            m_arpgModeCombatFloatingTexts.begin(),
            m_arpgModeCombatFloatingTexts.end(),
            [](const ArpgModeCombatFloatingText &floatingText)
            {
                return floatingText.remainingSeconds <= 0.0f;
            }),
        m_arpgModeCombatFloatingTexts.end());

    if (m_pIndoorSceneRuntime == nullptr)
    {
        return;
    }

    const std::vector<GameplayArpgCombatFeedbackEvent> events =
        m_pIndoorSceneRuntime->worldRuntime().drainArpgModeCombatFeedbackEvents();

    if (!m_settings.arpgModeEnabled || arpgModeFirstPersonUseMode())
    {
        return;
    }

    for (const GameplayArpgCombatFeedbackEvent &event : events)
    {
        if (event.damage > 0)
        {
            m_arpgModeCombatTargetState.active = true;
            m_arpgModeCombatTargetState.actorIndex = event.actorIndex;
            m_arpgModeCombatTargetState.remainingSeconds = 2.5f;

            const auto existingText =
                std::find_if(
                    m_arpgModeCombatFloatingTexts.begin(),
                    m_arpgModeCombatFloatingTexts.end(),
                    [&](const ArpgModeCombatFloatingText &floatingText)
                    {
                        return !floatingText.experience && floatingText.actorIndex == event.actorIndex;
                    });
            ArpgModeCombatFloatingText *pFloatingText =
                existingText != m_arpgModeCombatFloatingTexts.end() ? &*existingText : nullptr;

            if (pFloatingText == nullptr)
            {
                m_arpgModeCombatFloatingTexts.push_back(
                    ArpgModeCombatFloatingText{
                        .actorIndex = event.actorIndex,
                    });
                pFloatingText = &m_arpgModeCombatFloatingTexts.back();
            }

            pFloatingText->amount += event.damage;
            pFloatingText->text = std::to_string(pFloatingText->amount);
            pFloatingText->x = event.x;
            pFloatingText->y = event.y;
            pFloatingText->z = event.z + std::max(48.0f, event.height * 0.75f);
            pFloatingText->remainingSeconds = 0.95f;
            pFloatingText->durationSeconds = 0.95f;
            pFloatingText->colorAbgr = pFloatingText->amount >= 100
                ? makeArpgModeHudColor(255, 225, 106, 255)
                : makeArpgModeHudColor(235, 232, 210, 255);
            pFloatingText->fontScale = pFloatingText->amount >= 500
                ? 1.45f
                : pFloatingText->amount >= 100 ? 1.25f : 1.1f;
            pFloatingText->experience = false;
        }

        if (event.experience > 0)
        {
            m_arpgModeCombatFloatingTexts.push_back(
                ArpgModeCombatFloatingText{
                    .actorIndex = event.actorIndex,
                    .amount = event.experience,
                    .text = "+" + std::to_string(event.experience) + " exp",
                    .x = event.x,
                    .y = event.y,
                    .z = event.z + std::max(72.0f, event.height + 42.0f),
                    .remainingSeconds = 1.35f,
                    .durationSeconds = 1.35f,
                    .colorAbgr = makeArpgModeHudColor(128, 232, 153, 255),
                    .fontScale = 0.9f,
                    .experience = true,
                });
        }
    }
}

void IndoorGameView::renderArpgModeLootOverlay(int width, int height, float deltaSeconds)
{
    m_arpgModeLootLabelHits.clear();

    if (!m_settings.arpgModeEnabled
        || arpgModeFirstPersonUseMode()
        || m_pIndoorSceneRuntime == nullptr
        || m_pIndoorRenderer == nullptr
        || width <= 0
        || height <= 0)
    {
        return;
    }

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    screenRuntime.prepareHudView(width, height);

    for (ArpgModeLootLineOfSightState &state : m_arpgModeLootLineOfSightStates)
    {
        state.seenThisFrame = false;
        state.refreshSeconds = std::max(0.0f, state.refreshSeconds - std::max(0.0f, deltaSeconds));
    }

    IndoorWorldRuntime &worldRuntime = m_pIndoorSceneRuntime->worldRuntime();
    const std::vector<IndoorWorldRuntime::ArpgModeCorpseLootItem> lootItems =
        worldRuntime.collectArpgModeCorpseLootItems();
    constexpr const char *FontName = "Create";
    constexpr float FontScale = 1.0f;
    constexpr float PaddingX = 7.0f;
    constexpr float PaddingY = 3.0f;
    constexpr float Border = 2.0f;
    const float fontHeight = static_cast<float>(std::max(12, screenRuntime.hudFontHeight(FontName)));
    const float labelHeight = std::max(18.0f, fontHeight * FontScale + PaddingY * 2.0f);
    const float lineGap = 4.0f;

    for (const IndoorWorldRuntime::ArpgModeCorpseLootItem &lootItem : lootItems)
    {
        const bx::Vec3 lootPoint = {lootItem.x, lootItem.y, lootItem.z};

        if (!arpgModeLootLabelHasLineOfSight(lootItem.actorIndex, lootPoint))
        {
            continue;
        }

        float projectedX = 0.0f;
        float projectedY = 0.0f;

        if (!m_pIndoorRenderer->projectArpgModeWorldPointToScreen(
                lootPoint,
                width,
                height,
                projectedX,
                projectedY))
        {
            continue;
        }

        if (projectedX < 0.0f
            || projectedX > static_cast<float>(width)
            || projectedY < 0.0f
            || projectedY > static_cast<float>(height))
        {
            continue;
        }

        const std::string baseLabel =
            arpgModeCorpseLootLabel(
                lootItem.item,
                m_gameSession.data().itemTable(),
                &m_gameSession.data().standardItemEnchantTable(),
                &m_gameSession.data().specialItemEnchantTable());
        const ArpgModeLootFacts facts =
            arpgModeCorpseLootFacts(lootItem.item, m_gameSession.data().itemTable());
        const ArpgModeLootImportance importance = classifyArpgModeLoot(facts);
        const ArpgModeLootStyle style = arpgModeLootStyle(importance, lootItem.item.isGold);
        const std::string label = style.showStar ? "* " + baseLabel : baseLabel;
        const float measuredWidth = screenRuntime.measureHudTextWidth(FontName, label) * FontScale;
        const float labelWidth = std::clamp(measuredWidth + PaddingX * 2.0f, 76.0f, 340.0f);
        const float labelX = projectedX - labelWidth * 0.5f;
        const float labelY =
            projectedY
            - labelHeight
            - 16.0f
            - static_cast<float>(lootItem.itemIndex) * (labelHeight + lineGap);

        if (labelX < 4.0f
            || labelY < 4.0f
            || labelX + labelWidth > static_cast<float>(width) - 4.0f
            || labelY + labelHeight > static_cast<float>(height) - 4.0f)
        {
            continue;
        }

        if (style.showBeam)
        {
            const float beamTop = std::min(labelY + labelHeight, projectedY - 2.0f);
            const float beamHeight = std::max(18.0f, projectedY - beamTop);
            drawArpgModeSolidHudRect(
                screenRuntime,
                "__arpg_loot_beam__",
                projectedX - 1.5f,
                beamTop,
                3.0f,
                beamHeight,
                style.beamColorAbgr);
        }

        drawArpgModeSolidHudRect(
            screenRuntime,
            "__arpg_loot_border__",
            labelX,
            labelY,
            labelWidth,
            labelHeight,
            style.borderColorAbgr);
        drawArpgModeSolidHudRect(
            screenRuntime,
            "__arpg_loot_background__",
            labelX + Border,
            labelY + Border,
            labelWidth - Border * 2.0f,
            labelHeight - Border * 2.0f,
            style.backgroundColorAbgr);

        const float textX = labelX + PaddingX;
        const float textY = labelY + std::max(1.0f, (labelHeight - fontHeight * FontScale) * 0.5f);
        screenRuntime.renderHudTextLine(FontName, style.textColorAbgr, label, textX, textY, FontScale);

        m_arpgModeLootLabelHits.push_back(
            ArpgModeLootLabelHit{
                .actorIndex = lootItem.actorIndex,
                .itemIndex = lootItem.itemIndex,
                .x = labelX,
                .y = labelY,
                .width = labelWidth,
                .height = labelHeight,
                .worldX = lootItem.x,
                .worldY = lootItem.y,
                .worldZ = lootItem.z,
            });
    }

    m_arpgModeLootLineOfSightStates.erase(
        std::remove_if(
            m_arpgModeLootLineOfSightStates.begin(),
            m_arpgModeLootLineOfSightStates.end(),
            [](const ArpgModeLootLineOfSightState &state)
            {
                return !state.seenThisFrame;
            }),
        m_arpgModeLootLineOfSightStates.end());

    constexpr float CombatFontScale = 1.1f;

    for (const ArpgModeCombatFloatingText &floatingText : m_arpgModeCombatFloatingTexts)
    {
        if (floatingText.remainingSeconds <= 0.0f || floatingText.durationSeconds <= 0.0f)
        {
            continue;
        }

        const float progress =
            1.0f - std::clamp(floatingText.remainingSeconds / floatingText.durationSeconds, 0.0f, 1.0f);
        float projectedX = 0.0f;
        float projectedY = 0.0f;

        if (!m_pIndoorRenderer->projectArpgModeWorldPointToScreen(
                bx::Vec3{floatingText.x, floatingText.y, floatingText.z + progress * 110.0f},
                width,
                height,
                projectedX,
                projectedY))
        {
            continue;
        }

        const float fadeStartSeconds = floatingText.experience ? 0.55f : 0.35f;
        const float alpha = std::clamp(floatingText.remainingSeconds / fadeStartSeconds, 0.0f, 1.0f);
        const uint8_t alphaByte = static_cast<uint8_t>(std::round(255.0f * alpha));
        const uint32_t textColor = (floatingText.colorAbgr & 0x00ffffffu)
            | (static_cast<uint32_t>(alphaByte) << 24);
        const float fontScale = CombatFontScale * std::max(0.5f, floatingText.fontScale);
        const float textWidth = screenRuntime.measureHudTextWidth(FontName, floatingText.text) * fontScale;
        screenRuntime.renderHudTextLine(
            FontName,
            textColor,
            floatingText.text,
            projectedX - textWidth * 0.5f,
            projectedY,
            fontScale);
    }

    if (m_arpgModeCombatTargetState.active)
    {
        GameplayActorInspectState inspectState = {};

        if (worldRuntime.actorInspectState(m_arpgModeCombatTargetState.actorIndex, 0, inspectState)
            && inspectState.maxHp > 0
            && !inspectState.isDead)
        {
            constexpr float PanelWidth = 260.0f;
            constexpr float PanelHeight = 36.0f;
            constexpr float BarHeight = 8.0f;
            constexpr float Border = 2.0f;
            constexpr float NameScale = 1.0f;
            constexpr float HpScale = 0.75f;
            const float panelX = (static_cast<float>(width) - PanelWidth) * 0.5f;
            const float panelY = 10.0f;
            const float nameWidth = screenRuntime.measureHudTextWidth(FontName, inspectState.displayName) * NameScale;
            const float nameX = panelX + (PanelWidth - nameWidth) * 0.5f;
            const float barX = panelX + 12.0f;
            const float barY = panelY + 21.0f;
            const float barWidth = PanelWidth - 24.0f;
            const float fillRatio =
                std::clamp(
                    static_cast<float>(inspectState.currentHp) / static_cast<float>(inspectState.maxHp),
                    0.0f,
                    1.0f);
            const std::string hpText =
                std::to_string(std::max(0, inspectState.currentHp)) + " / " + std::to_string(inspectState.maxHp);
            const float hpTextWidth = screenRuntime.measureHudTextWidth(FontName, hpText) * HpScale;

            drawArpgModeSolidHudRect(
                screenRuntime,
                "__arpg_target_panel_bg__",
                panelX,
                panelY,
                PanelWidth,
                PanelHeight,
                makeArpgModeHudColor(6, 8, 10, 160));
            screenRuntime.renderHudTextLine(
                FontName,
                makeArpgModeHudColor(255, 211, 132, 255),
                inspectState.displayName,
                nameX,
                panelY + 2.0f,
                NameScale);
            drawArpgModeSolidHudRect(
                screenRuntime,
                "__arpg_target_bar_frame__",
                barX,
                barY,
                barWidth,
                BarHeight,
                makeArpgModeHudColor(12, 12, 12, 230));
            drawArpgModeSolidHudRect(
                screenRuntime,
                "__arpg_target_bar_fill__",
                barX + Border,
                barY + Border,
                std::max(1.0f, (barWidth - Border * 2.0f) * fillRatio),
                BarHeight - Border * 2.0f,
                makeArpgModeHudColor(186, 28, 30, 245));
            screenRuntime.renderHudTextLine(
                FontName,
                makeArpgModeHudColor(238, 232, 210, 215),
                hpText,
                panelX + (PanelWidth - hpTextWidth) * 0.5f,
                barY + 7.0f,
                HpScale);
        }
    }

    for (const ArpgModeLootFloatingText &floatingText : m_arpgModeLootFloatingTexts)
    {
        if (floatingText.remainingSeconds <= 0.0f || floatingText.durationSeconds <= 0.0f)
        {
            continue;
        }

        const float progress =
            1.0f - std::clamp(floatingText.remainingSeconds / floatingText.durationSeconds, 0.0f, 1.0f);
        float projectedX = 0.0f;
        float projectedY = 0.0f;

        if (!m_pIndoorRenderer->projectArpgModeWorldPointToScreen(
                bx::Vec3{floatingText.x, floatingText.y, floatingText.z + progress * 96.0f},
                width,
                height,
                projectedX,
                projectedY))
        {
            continue;
        }

        const float alpha = std::clamp(floatingText.remainingSeconds / 0.45f, 0.0f, 1.0f);
        const uint8_t alphaByte = static_cast<uint8_t>(std::round(255.0f * alpha));
        const uint32_t textColor = makeArpgModeHudColor(255, 223, 102, alphaByte);
        const float textWidth = screenRuntime.measureHudTextWidth(FontName, floatingText.text) * FontScale;
        screenRuntime.renderHudTextLine(
            FontName,
            textColor,
            floatingText.text,
            projectedX - textWidth * 0.5f,
            projectedY,
            FontScale);
    }
}

bool IndoorGameView::arpgModeLootLabelHasLineOfSight(size_t actorIndex, const bx::Vec3 &point)
{
    for (ArpgModeLootLineOfSightState &state : m_arpgModeLootLineOfSightStates)
    {
        if (state.actorIndex != actorIndex)
        {
            continue;
        }

        state.seenThisFrame = true;

        if (state.refreshSeconds > 0.0f)
        {
            return state.hasLineOfSight;
        }

        GameplayWorldHit hit = {};
        hit.hasHit = true;
        hit.kind = GameplayWorldHitKind::Ground;
        hit.ground = GameplayGroundTargetHit{
            .worldPoint = point,
            .distance = 0.0f,
            .isValid = true,
        };
        state.hasLineOfSight =
            m_pIndoorRenderer != nullptr && m_pIndoorRenderer->arpgModeGameplayWorldHitHasLineOfSight(hit);
        state.refreshSeconds = 0.2f;
        return state.hasLineOfSight;
    }

    ArpgModeLootLineOfSightState state = {};
    state.actorIndex = actorIndex;
    state.seenThisFrame = true;
    state.refreshSeconds = 0.2f;

    GameplayWorldHit hit = {};
    hit.hasHit = true;
    hit.kind = GameplayWorldHitKind::Ground;
    hit.ground = GameplayGroundTargetHit{
        .worldPoint = point,
        .distance = 0.0f,
        .isValid = true,
    };
    state.hasLineOfSight =
        m_pIndoorRenderer != nullptr && m_pIndoorRenderer->arpgModeGameplayWorldHitHasLineOfSight(hit);

    const bool hasLineOfSight = state.hasLineOfSight;
    m_arpgModeLootLineOfSightStates.push_back(state);
    return hasLineOfSight;
}

bool IndoorGameView::tryActivateArpgModeLootLabelAt(float screenX, float screenY)
{
    if (!m_settings.arpgModeEnabled || m_pIndoorSceneRuntime == nullptr || partyRuntime() == nullptr)
    {
        return false;
    }

    for (auto iterator = m_arpgModeLootLabelHits.rbegin(); iterator != m_arpgModeLootLabelHits.rend(); ++iterator)
    {
        const ArpgModeLootLabelHit &hit = *iterator;

        if (screenX < hit.x
            || screenX > hit.x + hit.width
            || screenY < hit.y
            || screenY > hit.y + hit.height)
        {
            continue;
        }

        tryActivateArpgModeCorpseLootItem(hit.actorIndex, hit.itemIndex);
        return true;
    }

    return false;
}

bool IndoorGameView::tryActivateNearestArpgModeLootLabel()
{
    IndoorPartyRuntime *pPartyRuntime = partyRuntime();

    if (!m_settings.arpgModeEnabled
        || arpgModeFirstPersonUseMode()
        || m_pIndoorSceneRuntime == nullptr
        || pPartyRuntime == nullptr
        || m_arpgModeLootLabelHits.empty())
    {
        return false;
    }

    const IndoorMoveState &moveState = pPartyRuntime->movementState();
    std::vector<ArpgModeLootLabelHit> sortedHits = m_arpgModeLootLabelHits;

    std::stable_sort(
        sortedHits.begin(),
        sortedHits.end(),
        [&moveState](const ArpgModeLootLabelHit &lhs, const ArpgModeLootLabelHit &rhs)
        {
            const float lhsDeltaX = lhs.worldX - moveState.x;
            const float lhsDeltaY = lhs.worldY - moveState.y;
            const float lhsDeltaZ = lhs.worldZ - moveState.footZ;
            const float rhsDeltaX = rhs.worldX - moveState.x;
            const float rhsDeltaY = rhs.worldY - moveState.y;
            const float rhsDeltaZ = rhs.worldZ - moveState.footZ;
            const float lhsDistanceSquared =
                lhsDeltaX * lhsDeltaX + lhsDeltaY * lhsDeltaY + lhsDeltaZ * lhsDeltaZ;
            const float rhsDistanceSquared =
                rhsDeltaX * rhsDeltaX + rhsDeltaY * rhsDeltaY + rhsDeltaZ * rhsDeltaZ;

            return lhsDistanceSquared < rhsDistanceSquared;
        });

    for (const ArpgModeLootLabelHit &hit : sortedHits)
    {
        if (tryActivateArpgModeCorpseLootItem(hit.actorIndex, hit.itemIndex))
        {
            return true;
        }
    }

    return false;
}

bool IndoorGameView::tryActivateArpgModeCorpseLootItem(size_t actorIndex, size_t itemIndex)
{
    IndoorPartyRuntime *pPartyRuntime = partyRuntime();

    if (!m_settings.arpgModeEnabled || m_pIndoorSceneRuntime == nullptr || pPartyRuntime == nullptr)
    {
        return false;
    }

    IndoorWorldRuntime &worldRuntime = m_pIndoorSceneRuntime->worldRuntime();
    const std::optional<GameplayChestItemState> selectedItem = worldRuntime.mapActorCorpseItem(actorIndex, itemIndex);

    if (!selectedItem)
    {
        return false;
    }

    if (selectedItem->isGold)
    {
        GameplayChestItemState removedItem = {};

        if (!worldRuntime.takeMapActorCorpseItem(actorIndex, itemIndex, removedItem))
        {
            return true;
        }

        const EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();
        const uint32_t adjustedGold =
            pEventRuntimeState != nullptr
                ? hiredNpcGoldAfterBonusAndFees(removedItem.goldAmount, *pEventRuntimeState)
                : removedItem.goldAmount;
        pPartyRuntime->party().addGold(static_cast<int>(adjustedGold));
        pPartyRuntime->party().requestSound(SoundId::Gold);
        setStatusBarEvent("+" + std::to_string(adjustedGold) + " gold");
        m_arpgModeLootFloatingTexts.push_back(
            ArpgModeLootFloatingText{
                .text = "+" + std::to_string(adjustedGold) + " gold",
                .x = pPartyRuntime->movementState().x,
                .y = pPartyRuntime->movementState().y,
                .z = pPartyRuntime->movementState().footZ + 96.0f,
                .remainingSeconds = 1.35f,
                .durationSeconds = 1.35f,
            });
        return true;
    }

    GameplayChestItemState removedItem = {};

    if (!worldRuntime.takeMapActorCorpseItem(actorIndex, itemIndex, removedItem))
    {
        return true;
    }

    InventoryItem inventoryItem = normalizedArpgModeCorpseInventoryItem(removedItem);
    const ItemDefinition *pItemDefinition = m_gameSession.data().itemTable().get(inventoryItem.objectDescriptionId);
    const std::string itemName =
        pItemDefinition != nullptr
            ? ItemRuntime::displayName(
                inventoryItem,
                *pItemDefinition,
                &m_gameSession.data().standardItemEnchantTable(),
                &m_gameSession.data().specialItemEnchantTable())
            : "item";

    if (!pPartyRuntime->party().tryGrantInventoryItemStartingAt(
            pPartyRuntime->party().activeMemberIndex(),
            inventoryItem))
    {
        worldRuntime.tryPlaceMapActorCorpseItemAt(actorIndex, removedItem, itemIndex);
        setStatusBarEvent("Pack is Full!");
        return true;
    }

    pPartyRuntime->party().requestSound(SoundId::Gold);
    setStatusBarEvent("+" + itemName);
    m_arpgModeLootFloatingTexts.push_back(
        ArpgModeLootFloatingText{
            .text = "+" + itemName,
            .x = pPartyRuntime->movementState().x,
            .y = pPartyRuntime->movementState().y,
            .z = pPartyRuntime->movementState().footZ + 96.0f,
            .remainingSeconds = 1.55f,
            .durationSeconds = 1.55f,
        });
    return true;
}

bool IndoorGameView::tryActivateFirstArpgModeCorpseLootItem(size_t actorIndex)
{
    if (!m_settings.arpgModeEnabled || m_pIndoorSceneRuntime == nullptr)
    {
        return false;
    }

    IndoorWorldRuntime &worldRuntime = m_pIndoorSceneRuntime->worldRuntime();

    if (!worldRuntime.ensureMapActorCorpseView(actorIndex))
    {
        return false;
    }

    return tryActivateArpgModeCorpseLootItem(actorIndex, 0);
}

void IndoorGameView::reopenMenuScreen()
{
    m_gameSession.gameplayScreenRuntime().openMenuOverlay();
}

IndoorPartyRuntime *IndoorGameView::partyRuntime() const
{
    return m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->partyRuntime() : nullptr;
}

IGameplayWorldRuntime *IndoorGameView::worldRuntime() const
{
    return m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->worldRuntime() : nullptr;
}

GameAudioSystem *IndoorGameView::audioSystem() const
{
    return m_pGameAudioSystem;
}

float IndoorGameView::gameplayCameraYawRadians() const
{
    if (m_pIndoorRenderer == nullptr)
    {
        return 0.0f;
    }

    return arpgModeFirstPersonUseMode()
        ? m_pIndoorRenderer->cameraYawRadians()
        : m_pIndoorRenderer->arpgModeGameplayYawRadians();
}

bool IndoorGameView::activeMemberKnowsSpell(uint32_t spellId) const
{
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr)
    {
        return false;
    }

    const Character *pMember = pRuntime->party().activeMember();
    return pMember != nullptr && pMember->knowsSpell(spellId);
}

bool IndoorGameView::activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const
{
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr)
    {
        return false;
    }

    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(school);
    const Character *pMember = pRuntime->party().activeMember();

    if (pDefinition == nullptr || pMember == nullptr)
    {
        return false;
    }

    const std::optional<std::string> skillName = resolveMagicSkillName(pDefinition->firstSpellId);

    if (!skillName)
    {
        return false;
    }

    const CharacterSkill *pSkill = pMember->findSkill(*skillName);
    return pSkill != nullptr && pSkill->level > 0 && pSkill->mastery != SkillMastery::None;
}

GameplayUiController::HeldInventoryItemState &IndoorGameView::heldInventoryItem()
{
    return m_gameSession.gameplayScreenRuntime().heldInventoryItem();
}

const GameplayUiController::HeldInventoryItemState &IndoorGameView::heldInventoryItem() const
{
    return m_gameSession.gameplayScreenRuntime().heldInventoryItem();
}

bool IndoorGameView::canActivateMapActorDialogue(size_t actorIndex) const
{
    if (m_pIndoorSceneRuntime == nullptr)
    {
        return false;
    }

    const IndoorWorldRuntime &worldRuntime = m_pIndoorSceneRuntime->worldRuntime();
    const MapDeltaData *pMapDeltaData = worldRuntime.mapDeltaData();
    const EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (pMapDeltaData == nullptr || pEventRuntimeState == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const IndoorWorldRuntime::MapActorAiState *pAiState = worldRuntime.mapActorAiState(actorIndex);
    GameplayRuntimeActorState runtimeState = {};

    if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0
        || pAiState == nullptr
        || pAiState->motionState == ActorAiMotionState::Dying
        || !worldRuntime.actorRuntimeState(actorIndex, runtimeState)
        || runtimeState.isDead
        || runtimeState.isInvisible)
    {
        return false;
    }

    if (actor.npcId > 0)
    {
        return !runtimeState.hostileToParty;
    }

    GameplayActorInspectState inspectState = {};

    if (!worldRuntime.actorInspectState(actorIndex, 0, inspectState))
    {
        return false;
    }

    const std::optional<GenericActorDialogResolution> resolution =
        resolveIndoorActorDialog(m_gameSession, m_map, *pEventRuntimeState, actor, inspectState, actorIndex);

    if (resolution && resolution->generatedNpc && resolution->opensNpcTalk)
    {
        return !indoorActorExplicitlyHostile(actor);
    }

    if (runtimeState.hostileToParty)
    {
        return false;
    }

    return resolution.has_value();
}

bool IndoorGameView::activateMapActorDialogue(size_t actorIndex)
{
    if (m_pIndoorSceneRuntime == nullptr)
    {
        return false;
    }

    IndoorWorldRuntime &worldRuntime = m_pIndoorSceneRuntime->worldRuntime();
    MapDeltaData *pMapDeltaData = worldRuntime.mapDeltaData();
    EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (pMapDeltaData == nullptr || pEventRuntimeState == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    if (!canActivateMapActorDialogue(actorIndex))
    {
        GameplayRuntimeActorState runtimeState = {};

        if (worldRuntime.actorRuntimeState(actorIndex, runtimeState) && runtimeState.hostileToParty)
        {
            const Party *pParty = m_gameSession.gameplayScreenRuntime().partyReadOnly();

            if (pParty != nullptr)
            {
                m_gameSession.gameplayScreenRuntime().playSpeechReaction(
                    pParty->activeMemberIndex(),
                    SpeechId::Yell,
                    true);
            }
        }

        pEventRuntimeState->lastActivationResult = "actor " + std::to_string(actorIndex) + " dialogue blocked";
        return false;
    }

    auto presentPendingDialog =
        [this](const GameplayDialogController::Result &result, bool allowNpcFallbackContent)
        {
            if (!result.shouldOpenPendingEventDialog)
            {
                return;
            }

            m_gameSession.gameplayScreenRuntime().presentPendingEventDialog(
                result.previousMessageCount,
                allowNpcFallbackContent,
                [this](EventRuntimeState &eventRuntimeState)
                {
                    return buildDialogContext(eventRuntimeState);
                });
        };

    GameplayDialogController::Context context = buildDialogContext(*pEventRuntimeState);

    if (actor.npcId > 0)
    {
        const GameplayDialogController::Result result =
            m_gameSession.gameplayDialogController().openNpcDialogue(
                context,
                static_cast<uint32_t>(actor.npcId),
                0,
                static_cast<uint32_t>(actorIndex));
        pEventRuntimeState->lastActivationResult = "npc " + std::to_string(actor.npcId) + " engaged";
        presentPendingDialog(result, true);
        return true;
    }

    GameplayActorInspectState inspectState = {};

    if (!worldRuntime.actorInspectState(actorIndex, 0, inspectState))
    {
        return false;
    }

    const std::optional<GenericActorDialogResolution> resolution =
        resolveIndoorActorDialog(m_gameSession, m_map, *pEventRuntimeState, actor, inspectState, actorIndex);

    if (!resolution)
    {
        const Party *pParty = m_gameSession.gameplayScreenRuntime().partyReadOnly();

        if (pParty != nullptr)
        {
            m_gameSession.gameplayScreenRuntime().playSpeechReaction(
                pParty->activeMemberIndex(),
                SpeechId::NpcDontTalk,
                true);
        }

        pEventRuntimeState->lastActivationResult =
            "actor group " + std::to_string(actor.group) + " dialogue unresolved";
        return false;
    }

    if (resolution->opensNpcTalk)
    {
        applyGenericActorDialogResolution(*pEventRuntimeState, *resolution);
        const GameplayDialogController::Result result =
            m_gameSession.gameplayDialogController().openNpcDialogue(
                context,
                resolution->npcId,
                0,
                static_cast<uint32_t>(actorIndex));
        pEventRuntimeState->lastActivationResult =
            "generated npc " + std::to_string(resolution->npcId) + " engaged";
        presentPendingDialog(result, result.allowNpcFallbackContent);
        return true;
    }

    const std::optional<std::string> newsText =
        m_gameSession.data().npcDialogTable().getNewsDialogText(resolution->newsId);

    if (!newsText || newsText->empty())
    {
        pEventRuntimeState->lastActivationResult =
            "actor group " + std::to_string(actor.group) + " news text unresolved";
        return false;
    }

    const GameplayDialogController::Result result =
        m_gameSession.gameplayDialogController().openNpcNews(
            context,
            resolution->npcId,
            resolution->newsId,
            inspectState.displayName,
            *newsText,
            resolution->portraitPictureId);
    pEventRuntimeState->lastActivationResult =
        "npc news group " + std::to_string(actor.group) + " engaged";
    presentPendingDialog(result, result.allowNpcFallbackContent);
    return true;
}

void IndoorGameView::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_gameSession.gameplayScreenRuntime().setStatusBarEvent(text, durationSeconds);
}

void IndoorGameView::updateDialogueVideoPlayback(float deltaSeconds)
{
    const EventRuntimeState *pEventRuntimeState =
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr;
    const uint32_t hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
    const HouseEntry *pHostHouseEntry =
        hostHouseId != 0 ? m_gameSession.data().houseTable().get(hostHouseId) : nullptr;
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    const EventDialogContent &activeDialog = screenRuntime.activeEventDialog();

    if (!activeDialog.isActive
        || screenRuntime.currentHudScreenState() != GameplayHudScreenState::Dialogue)
    {
        screenRuntime.stopHouseVideoPlayback();
        return;
    }

    if (!activeDialog.videoName.empty())
    {
        if (activeDialog.videoDirectory.empty())
        {
            screenRuntime.playHouseVideo(activeDialog.videoName);
        }
        else
        {
            screenRuntime.playHouseVideo(activeDialog.videoName, activeDialog.videoDirectory);
        }

        screenRuntime.updateHouseVideoPlayback(deltaSeconds);
        return;
    }

    if (pHostHouseEntry == nullptr || pHostHouseEntry->videoName.empty())
    {
        screenRuntime.stopHouseVideoPlayback();
        return;
    }

    screenRuntime.playHouseVideo(pHostHouseEntry->videoName);
    screenRuntime.updateHouseVideoPlayback(deltaSeconds);
}

void IndoorGameView::presentPendingEventFeedback()
{
    EventRuntimeState *pEventRuntimeState =
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr)
    {
        for (const std::string &statusMessage : pEventRuntimeState->statusMessages)
        {
            setStatusBarEvent(statusMessage);
        }

        pEventRuntimeState->statusMessages.clear();

        GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
            m_gameSession.gameplayScreenRuntime(),
            *pEventRuntimeState,
            m_gameSession.data().itemTable());
    }

    m_gameSession.gameplayScreenRuntime().ensurePendingEventDialogPresented(
        true,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        });
}

void IndoorGameView::executeActiveDialogAction()
{
    m_gameSession.gameplayScreenRuntime().executeActiveDialogAction(
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        },
        [this](const GameplayDialogController::Result &)
        {
            EventRuntimeState *pEventRuntimeState =
                worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr;

            if (pEventRuntimeState == nullptr)
            {
                return;
            }

            GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
                m_gameSession.gameplayScreenRuntime(),
                *pEventRuntimeState,
                m_gameSession.data().itemTable());
        },
        {},
        {},
        [this](size_t previousMessageCount, bool allowNpcFallbackContent)
        {
            m_gameSession.gameplayScreenRuntime().presentPendingEventDialog(
                previousMessageCount,
                allowNpcFallbackContent,
                [this](EventRuntimeState &eventRuntimeState)
                {
                    return buildDialogContext(eventRuntimeState);
                });
        });
}

bool IndoorGameView::tryCastSpellRequest(
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    if (partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    PartySpellCastRequest resolvedRequest = request;

    if (m_pIndoorRenderer != nullptr)
    {
        const IndoorPartyRuntime *pRuntime = partyRuntime();
        const IndoorMoveState &moveState = pRuntime->movementState();
        resolvedRequest.hasViewTransform = true;
        resolvedRequest.viewX = moveState.x;
        resolvedRequest.viewY = moveState.y;
        resolvedRequest.viewZ = moveState.eyeZ();
        resolvedRequest.viewYawRadians = m_pIndoorRenderer->arpgModeGameplayYawRadians();
        resolvedRequest.viewPitchRadians = m_pIndoorRenderer->cameraPitchRadians();
        resolvedRequest.viewAspectRatio =
            static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(std::max(m_lastRenderHeight, 1));
    }

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    const GameplaySpellService::SpellRequestResolution resolution =
        m_gameSession.gameplaySpellService().resolveSpellRequest(screenRuntime, resolvedRequest, spellName);

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::CastSucceeded)
    {
        if (m_settings.arpgModeEnabled && m_pIndoorRenderer != nullptr)
        {
            m_pIndoorRenderer->playArpgModePartyActionAnimation(
                std::clamp(m_settings.arpgModeSpellAnimationSeconds, 0.05f, 10.0f),
                true);
        }

        worldRuntime()->applyPendingSpellCastWorldEffects(resolution.castResult);
        m_gameSession.gameplaySpellService().clearPendingTargetSelection(
            screenRuntime,
            "Cast " + spellName);
        return true;
    }

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::OpenedSelectionUi)
    {
        return true;
    }

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::NeedsTargetSelection)
    {
        m_gameSession.gameplaySpellService().armPendingTargetSelection(
            screenRuntime,
            resolvedRequest,
            resolution.castResult.targetKind,
            spellName);
        worldRuntime()->clearWorldHover();
        return true;
    }

    return false;
}

GameSettings &IndoorGameView::mutableSettings()
{
    return m_settings;
}

bool IndoorGameView::trySaveToSelectedGameSlot()
{
    return m_gameSession.gameplayScreenRuntime().trySaveToSelectedGameSlot(
        [this](const GameplayScreenRuntime::PreparedSaveGameRequest &request)
        {
            return beginSaveWithPreview(request.path, request.saveName, true);
        });
}

bool IndoorGameView::requestQuickSave()
{
    return beginSaveWithPreview(std::filesystem::path("saves") / "quicksave.oysav", "", false);
}

bool IndoorGameView::requestTravelAutosave()
{
    return beginSaveWithPreview(AutosavePath, "", false);
}

bool IndoorGameView::beginSaveWithPreview(
    const std::filesystem::path &path,
    const std::string &saveName,
    bool closeUiOnSuccess)
{
    if (!m_gameSession.canSaveGameToPath()
        || (m_map && !m_map->runtimeRestrictions.allowSaveGame && !isAutosavePath(path)))
    {
        return false;
    }

    m_pendingSavePreviewCapture = {};
    m_pendingSavePreviewCapture.active = true;
    m_pendingSavePreviewCapture.screenshotRequested = false;
    m_pendingSavePreviewCapture.savePath = path;
    m_pendingSavePreviewCapture.requestId =
        "save_preview_" + std::to_string(SDL_GetTicks()) + "_" + std::to_string(path.generic_string().size());
    m_pendingSavePreviewCapture.saveName = saveName;
    m_pendingSavePreviewCapture.closeUiOnSuccess = closeUiOnSuccess;
    m_pendingSavePreviewCapture.startedTicks = SDL_GetTicks();
    return true;
}

void IndoorGameView::updateFootstepAudio(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pGameAudioSystem == nullptr || m_pIndoorSceneRuntime == nullptr)
    {
        return;
    }

    if (resolveGameplayHudScreenState(
            m_gameSession.gameplayUiController(),
            m_gameSession.gameplayScreenRuntime().activeEventDialog(),
            worldRuntime())
        != GameplayHudScreenState::Gameplay)
    {
        m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        m_walkingMotionHoldSeconds = 0.0f;
        m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const IndoorMoveState &moveState = m_pIndoorSceneRuntime->partyRuntime().movementState();

    if (!m_hasLastFootstepPosition)
    {
        m_lastFootstepX = moveState.x;
        m_lastFootstepY = moveState.y;
        m_hasLastFootstepPosition = true;
        m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const float deltaX = moveState.x - m_lastFootstepX;
    const float deltaY = moveState.y - m_lastFootstepY;
    m_lastFootstepX = moveState.x;
    m_lastFootstepY = moveState.y;
    const float movedDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
    const float movementSpeed = movedDistance / std::max(deltaSeconds, 0.0001f);

    if (movementSpeed >= WalkingSoundMovementSpeedThreshold)
    {
        m_walkingMotionHoldSeconds = WalkingMotionHoldSeconds;
    }
    else
    {
        m_walkingMotionHoldSeconds = std::max(0.0f, m_walkingMotionHoldSeconds - deltaSeconds);
    }

    if (!moveState.grounded || m_walkingMotionHoldSeconds <= 0.0f)
    {
        m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const uint32_t desiredSoundId = static_cast<uint32_t>(SoundId::WalkStoneHall);

    if (m_activeWalkingSoundId == desiredSoundId)
    {
        return;
    }

    m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
    const bool played =
        m_pGameAudioSystem->playLoopingSound(desiredSoundId, GameAudioSystem::PlaybackGroup::Walking);
    m_activeWalkingSoundId = played ? std::optional<uint32_t>(desiredSoundId) : std::nullopt;
}

const GameSettings &IndoorGameView::settingsSnapshot() const
{
    return m_settings;
}

void IndoorGameView::syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled)
{
    const bool windowFocused = windowHasInputFocus(pWindow);
    const bool effectiveEnabled = enabled && windowFocused;

    if (pWindow != nullptr && SDL_GetWindowRelativeMouseMode(pWindow) != effectiveEnabled)
    {
        if (effectiveEnabled)
        {
            syncCursorToGameplayCrosshair(pWindow);
            m_lastGameplayMouseLookCursorSyncTicks = SDL_GetTicks();
        }
        else if (windowFocused)
        {
            int windowWidth = 0;
            int windowHeight = 0;
            SDL_GetWindowSizeInPixels(pWindow, &windowWidth, &windowHeight);

            if (windowWidth > 0 && windowHeight > 0)
            {
                SDL_WarpMouseInWindow(
                    pWindow,
                    static_cast<float>(windowWidth) * 0.5f,
                    static_cast<float>(windowHeight) * 0.5f);
            }

            m_lastGameplayMouseLookCursorSyncTicks = 0;
        }

        SDL_SetWindowRelativeMouseMode(pWindow, effectiveEnabled);
        m_gameSession.requestRelativeMouseMotionReset();
    }
    else if (effectiveEnabled)
    {
        const uint64_t nowTicks = SDL_GetTicks();

        if (m_lastGameplayMouseLookCursorSyncTicks == 0
            || nowTicks < m_lastGameplayMouseLookCursorSyncTicks
            || nowTicks - m_lastGameplayMouseLookCursorSyncTicks >= GameplayMouseLookCursorSyncIntervalTicks)
        {
            syncCursorToGameplayCrosshair(pWindow);
            m_lastGameplayMouseLookCursorSyncTicks = nowTicks;
        }
    }
    else
    {
        m_lastGameplayMouseLookCursorSyncTicks = 0;
    }

    if (effectiveEnabled)
    {
        SDL_HideCursor();
    }
    else
    {
        SDL_ShowCursor();
    }
}

void IndoorGameView::syncCursorToGameplayCrosshair(SDL_Window *pWindow)
{
    const GameplayScreenState::GameplayMouseLookState &mouseLookState =
        m_gameSession.gameplayScreenState().gameplayMouseLookState();

    if (!mouseLookState.mouseLookActive || mouseLookState.cursorModeActive)
    {
        return;
    }

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetMouseFocus();

        if (pWindow == nullptr)
        {
            pWindow = SDL_GetKeyboardFocus();
        }
    }

    if (pWindow == nullptr)
    {
        return;
    }

    if (!windowHasInputFocus(pWindow))
    {
        return;
    }

    int windowWidth = 0;
    int windowHeight = 0;
    SDL_GetWindowSizeInPixels(pWindow, &windowWidth, &windowHeight);

    if (windowWidth <= 0 || windowHeight <= 0)
    {
        const GameplayInputFrame *pInputFrame = m_gameSession.currentGameplayInputFrame();

        if (pInputFrame == nullptr || pInputFrame->screenWidth <= 0 || pInputFrame->screenHeight <= 0)
        {
            return;
        }

        windowWidth = pInputFrame->screenWidth;
        windowHeight = pInputFrame->screenHeight;
    }

    SDL_WarpMouseInWindow(
        pWindow,
        static_cast<float>(windowWidth) * 0.5f,
        static_cast<float>(windowHeight) * 0.5f);
    m_gameSession.requestRelativeMouseMotionReset();
}

void IndoorGameView::updateActorInspectOverlayState(int width, int height, const GameplayInputFrame &input)
{
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    GameplayUiController::ActorInspectOverlayState &actorInspectOverlay = screenRuntime.actorInspectOverlay();

    actorInspectOverlay = {};

    if (m_settings.arpgModeEnabled)
    {
        return;
    }

    const IndoorWorldRuntime *pWorldRuntime =
        m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->worldRuntime() : nullptr;
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr
            || pWorldRuntime->activeCorpseView() != nullptr);

    if (!GameplayScreenController::canUpdateStandardWorldInspectOverlayFromMouse(
            screenRuntime,
            GameplayStandardWorldInspectOverlayConfig{
                .width = width,
                .height = height,
                .worldReady = m_pIndoorRenderer != nullptr && pWorldRuntime != nullptr,
                .hasHeldItem = screenRuntime.heldInventoryItem().active,
                .hasPendingSpellTarget =
                    m_gameSession.gameplayScreenState().pendingSpellTarget().active,
                .hasActiveLootView = hasActiveLootView,
            }))
    {
        return;
    }

    if (!input.rightMouseButton.held || m_pIndoorRenderer == nullptr)
    {
        return;
    }

    const std::optional<IndoorRenderer::GameplayActorPick> pick =
        m_pIndoorRenderer->gameplayActorPickAtCursor(width, height, input.pointerX, input.pointerY);

    if (!pick.has_value())
    {
        return;
    }

    actorInspectOverlay.active = true;
    actorInspectOverlay.runtimeActorIndex = pick->runtimeActorIndex;
    actorInspectOverlay.sourceX = pick->sourceX;
    actorInspectOverlay.sourceY = pick->sourceY;
    actorInspectOverlay.sourceWidth = pick->sourceWidth;
    actorInspectOverlay.sourceHeight = pick->sourceHeight;

    const MapDeltaData *pMapDeltaData = pWorldRuntime->mapDeltaData();
    const EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

    if (pMapDeltaData == nullptr
        || pEventRuntimeState == nullptr
        || pick->runtimeActorIndex >= pMapDeltaData->actors.size())
    {
        return;
    }

    GameplayActorInspectState inspectState = {};

    if (!pWorldRuntime->actorInspectState(pick->runtimeActorIndex, 0, inspectState))
    {
        return;
    }

    if (input.rightMouseButton.pressed)
    {
        const IndoorMoveState *pMoveState =
            m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->partyRuntime().movementState() : nullptr;
        GameplayRuntimeActorState runtimeActorState = {};
        const bool hasRuntimeActorState =
            pWorldRuntime->actorRuntimeState(pick->runtimeActorIndex, runtimeActorState);
        GAMEPLAY_DEBUG_TRACE(
            "actor_inspect world=indoor map=\""
            + (m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->worldRuntime().mapName() : std::string())
            + "\" actor_index=" + std::to_string(pick->runtimeActorIndex)
            + " name=\"" + inspectState.displayName + "\""
            + " monster_id=" + std::to_string(inspectState.monsterId)
            + " current_hp=" + std::to_string(inspectState.currentHp)
            + " max_hp=" + std::to_string(inspectState.maxHp)
            + " dead=" + (inspectState.isDead ? "true" : "false")
            + (pMoveState != nullptr
                ? " party=(" + std::to_string(pMoveState->x)
                    + "," + std::to_string(pMoveState->y)
                    + "," + std::to_string(pMoveState->footZ) + ")"
                : "")
            + " yaw=" + std::to_string(m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->cameraYawRadians() : 0.0f)
            + " pitch=" + std::to_string(m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->cameraPitchRadians() : 0.0f)
            + (hasRuntimeActorState
                ? " actor_pos=(" + std::to_string(runtimeActorState.preciseX)
                    + "," + std::to_string(runtimeActorState.preciseY)
                    + "," + std::to_string(runtimeActorState.preciseZ) + ")"
                : ""));
    }

    if (input.rightMouseButton.pressed && !inspectState.isDead)
    {
        Party *pParty = screenRuntime.party();
        const std::optional<size_t> speakerMemberIndex =
            pParty != nullptr ? pParty->bestPartyWideUtilitySkillMemberIndex("IdentifyMonster") : std::nullopt;
        const Character *pMember = speakerMemberIndex ? pParty->member(*speakerMemberIndex) : nullptr;
        const MonsterTable::MonsterStatsEntry *pStats =
            m_gameSession.data().monsterTable().findStatsById(inspectState.monsterId);

        if (pParty != nullptr && pMember != nullptr && pStats != nullptr)
        {
            const SpeechId speechId = GameMechanics::resolveIdentifyMonsterSpeech(*pMember, pStats->level);

            if (speechId != SpeechId::None)
            {
                screenRuntime.playSpeechReaction(*speakerMemberIndex, speechId, true);
            }
        }
    }

    const std::optional<GenericActorDialogResolution> resolution =
        resolveIndoorActorDialog(
            m_gameSession,
            m_map,
            *pEventRuntimeState,
            pMapDeltaData->actors[pick->runtimeActorIndex],
            inspectState,
            pick->runtimeActorIndex);

    if (resolution)
    {
        actorInspectOverlay.displayNameOverride = generatedActorDisplayTitle(m_gameSession, *resolution);
    }
}

void IndoorGameView::updateItemInspectOverlayState(int width, int height, const GameplayInputFrame &input)
{
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    GameplayUiController::ItemInspectOverlayState &itemInspectOverlay = screenRuntime.itemInspectOverlay();
    itemInspectOverlay = {};

    const bool enabled =
        GameplayScreenController::canUpdateStandardHudItemInspectOverlayFromMouse(screenRuntime, width, height);

    if (!enabled || width <= 0 || height <= 0)
    {
        return;
    }

    if (!input.rightMouseButton.held)
    {
        screenRuntime.interactionState().itemInspectInteractionLatch = false;
        screenRuntime.interactionState().itemInspectInteractionKey = 0;
        return;
    }

    if (GameplayScreenController::updateRenderedHudItemInspectOverlay(screenRuntime, width, height, false))
    {
        GameplayScreenController::applySharedItemInspectSkillInteraction(screenRuntime);
        return;
    }

    if (m_settings.arpgModeEnabled)
    {
        return;
    }

    IndoorWorldRuntime *pWorldRuntime =
        m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->worldRuntime() : nullptr;

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    const GameplayWorldPickRequest pickRequest =
        pWorldRuntime->buildWorldPickRequest(
            GameplayWorldPickRequestInput{
                .screenX = input.pointerX,
                .screenY = input.pointerY,
                .screenWidth = width,
                .screenHeight = height,
                .includeRay = true,
            });
    const GameplayWorldHit worldHit = pWorldRuntime->pickMouseInteractionTarget(pickRequest);

    if (worldHit.kind != GameplayWorldHitKind::WorldItem || !worldHit.worldItem)
    {
        return;
    }

    GameplayWorldItemInspectState worldItemState = {};

    if (!pWorldRuntime->worldItemInspectState(worldHit.worldItem->worldItemIndex, worldItemState))
    {
        return;
    }

    itemInspectOverlay.active = true;
    itemInspectOverlay.objectDescriptionId = worldItemState.item.objectDescriptionId;
    itemInspectOverlay.hasItemState = !worldItemState.isGold;
    itemInspectOverlay.itemState = worldItemState.item;
    itemInspectOverlay.sourceType = GameplayUiController::ItemInspectSourceType::WorldItem;
    itemInspectOverlay.sourceWorldItemIndex = worldHit.worldItem->worldItemIndex;
    itemInspectOverlay.hasValueOverride = worldItemState.isGold;
    itemInspectOverlay.valueOverride = static_cast<int>(worldItemState.goldAmount);
    itemInspectOverlay.sourceX = input.pointerX;
    itemInspectOverlay.sourceY = input.pointerY;
    itemInspectOverlay.sourceWidth = 1.0f;
    itemInspectOverlay.sourceHeight = 1.0f;
    GameplayScreenController::applySharedItemInspectSkillInteraction(screenRuntime);
}

std::optional<std::string> IndoorGameView::findCachedAssetPath(
    const std::string &directoryPath,
    const std::string &fileName) const
{
    return GameplayHudCommon::findCachedAssetPath(
        m_pAssetFileSystem,
        m_gameSession.gameplayUiRuntime().assetLoadCache(),
        directoryPath,
        fileName);
}

std::optional<std::vector<uint8_t>> IndoorGameView::readCachedBinaryFile(const std::string &assetPath) const
{
    return GameplayHudCommon::readCachedBinaryFile(
        m_pAssetFileSystem,
        m_gameSession.gameplayUiRuntime().assetLoadCache(),
        assetPath);
}


GameplayDialogController::Context IndoorGameView::buildDialogContext(EventRuntimeState &eventRuntimeState)
{
    Party *pParty = partyRuntime() != nullptr ? &partyRuntime()->party() : nullptr;
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();

    return buildGameplayDialogContext(
        m_gameSession.gameplayUiController(),
        eventRuntimeState,
        screenRuntime.activeEventDialog(),
        screenRuntime.eventDialogSelectionIndex(),
        pParty,
        worldRuntime(),
        m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->globalEventProgram() : nullptr,
        &m_gameSession.data().houseTable(),
        &m_gameSession.data().classSkillTable(),
        &m_gameSession.data().npcDialogTable(),
        &m_gameSession.data().transitionTable(),
        m_map ? &*m_map : nullptr,
        &m_gameSession.data().mapEntries(),
        &m_gameSession.data().rosterTable(),
        &m_gameSession.data().arcomageLibrary(),
        screenRuntime.currentHudScreenState() == GameplayHudScreenState::Dialogue,
        &screenRuntime,
        &m_gameSession.data().mergedNpcProfessionTable(),
        &m_gameSession.data().mergedNewsProfessionTopicTable(),
        &m_gameSession.data().mergedNpcBtbTable(),
        &m_gameSession.data().mergedBolsterMapTable(),
        &m_gameSession.data().mergedContinentSettingTable(),
        &m_gameSession.data().mergedTeacherTopicTable(),
        &m_gameSession.data().mergedTeacherAutonoteTable(),
        &m_gameSession.data().spellTable());
}

} // namespace OpenYAMM::Game
