#include "game/indoor/IndoorGameView.h"

#include "game/app/GameSession.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayHudInputController.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/gameplay/GameplayDialogUiFlow.h"
#include "game/gameplay/GameplayScreenHotkeyController.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/indoor/IndoorDebugRenderer.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/ui/GameplayDebugOverlayRenderer.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudRenderer.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/ui/HudUiService.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"
#include "game/ui/GameplayUiOverlayOrchestrator.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
IndoorGameView::IndoorGameView(GameSession &gameSession)
    : m_gameSession(gameSession)
    , m_gameplayUiRuntime(gameSession.gameplayUiRuntime())
    , m_gameplayUiController(gameSession.gameplayUiController())
    , m_gameplayDialogController(gameSession.gameplayDialogController())
    , m_overlayInteractionState(gameSession.overlayInteractionState())
{
}

namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr uint16_t HudViewId = 2;
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

GameplayResolvedHudLayoutElement resolveAttachedHudLayoutRect(
    UiLayoutManager::LayoutAttachMode attachTo,
    const GameplayResolvedHudLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    GameplayResolvedHudLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
    case UiLayoutManager::LayoutAttachMode::None:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::RightOf:
        resolved.x = parent.x + parent.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::LeftOf:
        resolved.x = parent.x - resolved.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::Above:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::Below:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + parent.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterAbove:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterBelow:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + parent.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterIn:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;
    }

    return resolved;
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
}

bool IndoorGameView::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    IndoorDebugRenderer &indoorRenderer,
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
    m_gameplayUiRuntime.bindAssetFileSystem(&assetFileSystem);
    m_gameplayUiController.clearRuntimeState();

    if (!m_gameplayUiRuntime.ensureGameplayLayoutsLoaded(m_gameplayUiController))
    {
        return false;
    }

    m_gameplayUiRuntime.preloadReferencedAssets();
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

void IndoorGameView::render(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    GameplayHudRenderBackend hudRenderBackend = {};
    bgfx::ProgramHandle invalidProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle invalidSamplerHandle = BGFX_INVALID_HANDLE;
    hudRenderBackend.texturedProgramHandle =
        m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->hudTexturedProgramHandle() : invalidProgramHandle;
    hudRenderBackend.textureSamplerHandle =
        m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->hudTextureSamplerHandle() : invalidSamplerHandle;
    hudRenderBackend.viewId = HudViewId;
    m_gameplayUiRuntime.bindHudRenderBackend(hudRenderBackend);

    EventRuntimeState *pEventRuntimeState =
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr;

    if (!activeEventDialog().isActive
        && pEventRuntimeState != nullptr
        && pEventRuntimeState->pendingDialogueContext.has_value()
        && pEventRuntimeState->pendingDialogueContext->kind != DialogueContextKind::None)
    {
        presentPendingEventDialog(pEventRuntimeState->messages.size(), true);
    }

    SDL_Window *pWindow = SDL_GetMouseFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetKeyboardFocus();
    }

    float gameplayMouseX = 0.0f;
    float gameplayMouseY = 0.0f;
    const SDL_MouseButtonFlags gameplayMouseButtons = SDL_GetMouseState(&gameplayMouseX, &gameplayMouseY);
    const bool gameplayMouseLookAllowed = shouldEnableGameplayMouseLook();
    const bool gameplayCursorModeActive =
        gameplayMouseLookAllowed && (gameplayMouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool gameplayMouseLookActive = gameplayMouseLookAllowed && !gameplayCursorModeActive;

    m_gameplayCursorModeActive = gameplayCursorModeActive;
    m_gameplayMouseLookActive = gameplayMouseLookActive;
    syncGameplayMouseLookMode(pWindow, gameplayMouseLookActive);

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->setGameplayMouseLookMode(gameplayMouseLookActive, gameplayCursorModeActive);
    }

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->render(width, height, mouseWheelDelta, deltaSeconds);
    }

    if (!activeEventDialog().isActive
        && pEventRuntimeState != nullptr
        && pEventRuntimeState->pendingDialogueContext.has_value()
        && pEventRuntimeState->pendingDialogueContext->kind != DialogueContextKind::None)
    {
        presentPendingEventDialog(pEventRuntimeState->messages.size(), true);
    }

    m_gameplayUiController.updateStatusBarEvent(deltaSeconds);
    updateItemInspectOverlayState(width, height);

    GameplayUiController::RestScreenState &restScreen = m_gameplayUiController.restScreen();

    if (restScreen.active)
    {
        const float safeDeltaSeconds = std::max(0.0f, deltaSeconds);
        restScreen.hourglassElapsedSeconds += safeDeltaSeconds;

        if (restScreen.mode != GameplayUiController::RestMode::None && worldRuntime() != nullptr)
        {
            constexpr float ShortestRestAnimationSeconds = 0.25f;
            constexpr float LongestRestAnimationSeconds = 2.0f;
            constexpr float RestMinutesPerAnimationSecond = 360.0f;
            const float animationDurationSeconds = std::clamp(
                restScreen.totalMinutes / RestMinutesPerAnimationSecond,
                ShortestRestAnimationSeconds,
                LongestRestAnimationSeconds);
            const float gameMinutesPerSecond = animationDurationSeconds > 0.0f
                ? restScreen.totalMinutes / animationDurationSeconds
                : restScreen.totalMinutes;
            const float advancedMinutes =
                std::min(restScreen.remainingMinutes, gameMinutesPerSecond * safeDeltaSeconds);

            if (advancedMinutes > 0.0f)
            {
                worldRuntime()->advanceGameMinutes(advancedMinutes);
                restScreen.remainingMinutes = std::max(0.0f, restScreen.remainingMinutes - advancedMinutes);
            }

            if (restScreen.remainingMinutes <= 0.0f)
            {
                if (partyRuntime() != nullptr && restScreen.mode == GameplayUiController::RestMode::Heal)
                {
                    partyRuntime()->party().restAndHealAll();
                }

                const bool closeRestScreenAfterCompletion = restScreen.mode == GameplayUiController::RestMode::Heal;
                restScreen.mode = GameplayUiController::RestMode::None;
                restScreen.totalMinutes = 0.0f;
                restScreen.remainingMinutes = 0.0f;

                if (closeRestScreenAfterCompletion)
                {
                    createGameplayOverlayContext().closeRestOverlay();
                }
            }
        }
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
    struct KeyboardStateSnapshotUpdater
    {
        std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState;
        const bool *pKeyboardState = nullptr;

        ~KeyboardStateSnapshotUpdater()
        {
            if (pKeyboardState == nullptr)
            {
                previousKeyboardState.fill(0);
                return;
            }

            for (size_t scancode = 0; scancode < SDL_SCANCODE_COUNT; ++scancode)
            {
                previousKeyboardState[scancode] = pKeyboardState[scancode] ? 1u : 0u;
            }
        }
    } keyboardStateSnapshotUpdater = {m_gameSession.previousKeyboardState(), pKeyboardState};
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    bool hasSharedScreenOverlay =
        m_gameplayUiController.restScreen().active
        || m_gameplayUiController.menuScreen().active
        || m_gameplayUiController.controlsScreen().active
        || m_gameplayUiController.keyboardScreen().active
        || m_gameplayUiController.videoOptionsScreen().active
        || m_gameplayUiController.saveGameScreen().active
        || m_gameplayUiController.loadGameScreen().active
        || m_gameplayUiController.journalScreen().active;

    const bool canOpenMenu =
        !activeEventDialog().isActive
        && !hasActiveLootView
        && !hasSharedScreenOverlay
        && !m_gameplayUiController.inventoryNestedOverlay().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();
    const bool allowGameplayPointerInput = !gameplayMouseLookAllowed || gameplayCursorModeActive;

    const bool escapePressed = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (canOpenMenu)
    {
        if (escapePressed && m_gameSession.previousKeyboardState()[SDL_SCANCODE_ESCAPE] == 0)
        {
            createGameplayOverlayContext().openMenuOverlay();
            m_overlayInteractionState.menuToggleLatch = true;
            hasSharedScreenOverlay = true;
        }
        else if (!escapePressed)
        {
            m_overlayInteractionState.menuToggleLatch = false;
        }
    }

    const bool gameplayReadyForPortraitClicks =
        allowGameplayPointerInput
        && width > 0
        && height > 0
        && !activeEventDialog().isActive
        && !m_gameplayUiController.spellbook().active
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    if (gameplayReadyForPortraitClicks)
    {
        const bool requireGameplayReady = !hasActiveLootView;
        GameplayHudInputController::handlePartyPortraitInput(
            overlayContext,
            GameplayPartyPortraitInputConfig{
                .screenWidth = width,
                .screenHeight = height,
                .pointerX = gameplayMouseX,
                .pointerY = gameplayMouseY,
                .leftButtonPressed = (gameplayMouseButtons & SDL_BUTTON_LMASK) != 0,
                .allowInput = true,
                .requireGameplayReady = requireGameplayReady,
                .hasActiveLootView = hasActiveLootView,
            });
    }
    else
    {
        GameplayHudInputController::handlePartyPortraitInput(
            overlayContext,
            GameplayPartyPortraitInputConfig{});
    }

    const bool canToggleGameplaySpellbook =
        !activeEventDialog().isActive
        && !m_gameplayUiController.characterScreen().open
        && !hasActiveLootView
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    const bool canToggleInventory =
        !activeEventDialog().isActive
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active;

    const bool canCyclePartyMember =
        !activeEventDialog().isActive
        && !hasActiveLootView
        && !m_gameplayUiController.spellbook().active
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    GameplayScreenHotkeyController::handleGameplayScreenHotkeys(
        overlayContext,
        pKeyboardState,
        GameplayScreenHotkeyConfig{
            .canToggleMenu = canOpenMenu,
            .canOpenRest = false,
            .canToggleSpellbook = canToggleGameplaySpellbook,
            .canToggleInventory = canToggleInventory,
            .canCyclePartyMember = canCyclePartyMember,
            .hasActiveLootView = hasActiveLootView,
        });

    const bool canClickGameplayHudButtons =
        allowGameplayPointerInput
        && width > 0
        && height > 0
        && !activeEventDialog().isActive
        && !m_gameplayUiController.characterScreen().open
        && !m_gameplayUiController.spellbook().active
        && !hasActiveLootView
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    GameplayHudInputController::handleGameplayHudButtonInput(
        overlayContext,
        GameplayHudButtonInputConfig{
            .screenWidth = width,
            .screenHeight = height,
            .pointerX = gameplayMouseX,
            .pointerY = gameplayMouseY,
            .leftButtonPressed = (gameplayMouseButtons & SDL_BUTTON_LMASK) != 0,
            .allowInput = canClickGameplayHudButtons
        });

    const bool canToggleJournal =
        !activeEventDialog().isActive
        && !hasActiveLootView
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.inventoryNestedOverlay().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    const GameplayUiOverlayInputResult inputResult = GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height,
        GameplayUiOverlayInputConfig{
            .hasActiveLootView = hasActiveLootView,
            .canToggleJournal = canToggleJournal,
            .mapShortcutPressed =
                pKeyboardState != nullptr
                && (pKeyboardState[SDL_SCANCODE_M]
                    || m_settings.keyboard.isPressed(KeyboardAction::MapBook, pKeyboardState)),
            .storyShortcutPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::History, pKeyboardState),
            .notesShortcutPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::AutoNotes, pKeyboardState),
            .zoomInPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::ZoomIn, pKeyboardState),
            .zoomOutPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::ZoomOut, pKeyboardState),
            .mouseWheelDelta = mouseWheelDelta,
            .activeEventDialog = activeEventDialog().isActive,
            .residentSelectionMode = isResidentSelectionMode(activeEventDialog()),
            .restActive = m_gameplayUiController.restScreen().active,
            .menuActive = m_gameplayUiController.menuScreen().active,
            .controlsActive = m_gameplayUiController.controlsScreen().active,
            .keyboardActive = m_gameplayUiController.keyboardScreen().active,
            .videoOptionsActive = m_gameplayUiController.videoOptionsScreen().active,
            .saveGameActive = m_gameplayUiController.saveGameScreen().active,
            .spellbookActive = m_gameplayUiController.spellbook().active,
            .characterScreenOpen = m_gameplayUiController.characterScreen().open,
        },
        GameplayUiOverlayInputCallbacks{
            .resetDialogueInteractionState =
                [this]()
                {
                    m_overlayInteractionState.eventDialogSelectUpLatch = false;
                    m_overlayInteractionState.eventDialogSelectDownLatch = false;
                    m_overlayInteractionState.eventDialogAcceptLatch = false;
                    m_overlayInteractionState.eventDialogPartySelectLatches.fill(false);
                    m_overlayInteractionState.dialogueClickLatch = false;
                    m_overlayInteractionState.dialoguePressedTarget = {};
                },
            .handleSpellbookOverlayInput =
                [this](const bool *pState, int screenWidth, int screenHeight)
                {
                    handleSpellbookOverlayInput(pState, screenWidth, screenHeight);
                },
            .handleCharacterOverlayInput =
                [this](const bool *pState, int screenWidth, int screenHeight)
                {
                    handleCharacterOverlayInput(pState, screenWidth, screenHeight);
                }});

    if (inputResult.journalInputConsumed && !activeEventDialog().isActive)
    {
        m_overlayInteractionState.eventDialogSelectUpLatch = false;
        m_overlayInteractionState.eventDialogSelectDownLatch = false;
        m_overlayInteractionState.eventDialogAcceptLatch = false;
        m_overlayInteractionState.eventDialogPartySelectLatches.fill(false);
    }

    const bool canRenderHudOverlays =
        m_pIndoorRenderer != nullptr
        && m_pIndoorRenderer->hasHudRenderResources()
        && width > 0
        && height > 0;

    const bool renderChestUi =
        hasActiveLootView && pWorldRuntime != nullptr && pWorldRuntime->activeChestView() != nullptr;
    GameplayUiOverlayOrchestrator::renderStandardOverlays(
        overlayContext,
        width,
        height,
        GameplayUiOverlayRenderConfig{
            .canRenderHudOverlays = canRenderHudOverlays,
            .hasActiveLootView = hasActiveLootView,
            .activeEventDialog = activeEventDialog().isActive,
            .renderGameplayMouseLookOverlay = m_gameplayMouseLookActive && !m_gameplayCursorModeActive,
            .renderChestBelowHud = renderChestUi,
            .renderChestAboveHud = renderChestUi,
            .renderInventoryBelowHud = renderChestUi,
            .renderInventoryAboveHud = renderChestUi,
            .renderDialogueAboveHud = true,
            .renderCharacterBelowHud = true,
            .renderCharacterAboveHud = true,
            .renderDebugLootFallback = hasActiveLootView,
            .renderDebugDialogueFallback = true,
        });
}

void IndoorGameView::handleSpellbookOverlayInput(const bool *pKeyboardState, int width, int height)
{
    if (!m_gameplayUiController.spellbook().active || width <= 0 || height <= 0)
    {
        m_overlayInteractionState.spellbookClickLatch = false;
        return;
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    GameplayPartyOverlayInputController::handleSpellbookOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height);
}

void IndoorGameView::handleCharacterOverlayInput(const bool *pKeyboardState, int width, int height)
{
    if (!m_gameplayUiController.characterScreen().open || width <= 0 || height <= 0)
    {
        m_overlayInteractionState.characterClickLatch = false;
        return;
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    GameplayPartyOverlayInputController::handleCharacterOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height);
}

void IndoorGameView::shutdown()
{
    syncGameplayMouseLookMode(SDL_GetMouseFocus(), false);

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->setGameplayMouseLookMode(false, false);
    }

    m_pAssetFileSystem = nullptr;
    m_pIndoorRenderer = nullptr;
    m_pIndoorSceneRuntime = nullptr;
    m_pGameAudioSystem = nullptr;
    m_map.reset();
    m_gameplayUiRuntime.clear();
    m_gameplayUiController.clearRuntimeState();
    m_overlayInteractionState.closeOverlayLatch = false;
    m_overlayInteractionState.restClickLatch = false;
    m_overlayInteractionState.restPressedTarget = {};
    m_overlayInteractionState.menuToggleLatch = false;
    m_overlayInteractionState.menuClickLatch = false;
    m_overlayInteractionState.menuPressedTarget = {};
    m_overlayInteractionState.controlsToggleLatch = false;
    m_overlayInteractionState.controlsClickLatch = false;
    m_overlayInteractionState.controlsPressedTarget = {};
    m_overlayInteractionState.controlsSliderDragActive = false;
    m_overlayInteractionState.controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    m_overlayInteractionState.keyboardToggleLatch = false;
    m_overlayInteractionState.keyboardClickLatch = false;
    m_overlayInteractionState.keyboardPressedTarget = {};
    m_overlayInteractionState.videoOptionsToggleLatch = false;
    m_overlayInteractionState.videoOptionsClickLatch = false;
    m_overlayInteractionState.videoOptionsPressedTarget = {};
    m_overlayInteractionState.saveGameToggleLatch = false;
    m_overlayInteractionState.saveGameClickLatch = false;
    m_overlayInteractionState.saveGamePressedTarget = {};
    m_overlayInteractionState.saveGameEditKeyLatches.fill(false);
    m_overlayInteractionState.saveGameEditBackspaceLatch = false;
    m_overlayInteractionState.lastSaveGameSlotClickTicks = 0;
    m_overlayInteractionState.lastSaveGameClickedSlotIndex.reset();
    m_overlayInteractionState.journalToggleLatch = false;
    m_overlayInteractionState.journalClickLatch = false;
    m_overlayInteractionState.journalPressedTarget = {};
    m_overlayInteractionState.journalMapKeyZoomLatch = false;
    m_overlayInteractionState.dialogueClickLatch = false;
    m_overlayInteractionState.dialoguePressedTarget = {};
    m_overlayInteractionState.houseShopClickLatch = false;
    m_overlayInteractionState.houseShopPressedSlotIndex = 0;
    m_overlayInteractionState.chestClickLatch = false;
    m_overlayInteractionState.chestItemClickLatch = false;
    m_overlayInteractionState.chestPressedTarget = {};
    m_overlayInteractionState.inventoryNestedOverlayItemClickLatch = false;
    m_overlayInteractionState.houseBankDigitLatches.fill(false);
    m_overlayInteractionState.houseBankBackspaceLatch = false;
    m_overlayInteractionState.houseBankConfirmLatch = false;
    m_overlayInteractionState.lootChestItemLatch = false;
    m_overlayInteractionState.chestSelectUpLatch = false;
    m_overlayInteractionState.chestSelectDownLatch = false;
    m_overlayInteractionState.eventDialogSelectUpLatch = false;
    m_overlayInteractionState.eventDialogSelectDownLatch = false;
    m_overlayInteractionState.eventDialogAcceptLatch = false;
    m_overlayInteractionState.eventDialogPartySelectLatches.fill(false);
    m_overlayInteractionState.activateInspectLatch = false;
    m_overlayInteractionState.chestSelectionIndex = 0;
    m_overlayInteractionState.spellbookClickLatch = false;
    m_overlayInteractionState.spellbookPressedTarget = {};
    m_overlayInteractionState.partyPortraitClickLatch = false;
    m_overlayInteractionState.partyPortraitPressedIndex = std::nullopt;
    m_overlayInteractionState.lastPartyPortraitClickTicks = 0;
    m_overlayInteractionState.lastPartyPortraitClickedIndex = std::nullopt;
    m_overlayInteractionState.pendingCharacterDismissMemberIndex = std::nullopt;
    m_overlayInteractionState.pendingCharacterDismissExpiresTicks = 0;
    m_overlayInteractionState.characterClickLatch = false;
    m_overlayInteractionState.characterPressedTarget = {};
    m_overlayInteractionState.gameplayHudClickLatch = false;
    m_overlayInteractionState.gameplayHudPressedTarget = {};
    m_gameplayMouseLookActive = false;
    m_gameplayCursorModeActive = false;
    m_gameSession.previousKeyboardState().fill(0);
    m_gameplayUiRuntime.renderedInspectableHudItems().clear();
    m_gameplayUiRuntime.hudLayoutRuntimeHeightOverrides().clear();
}

void IndoorGameView::reopenMenuScreen()
{
    createGameplayOverlayContext().openMenuOverlay();
}

IndoorPartyRuntime *IndoorGameView::partyRuntime() const
{
    return m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->partyRuntime() : nullptr;
}

GameplayOverlayContext IndoorGameView::createGameplayOverlayContext()
{
    return GameplayOverlayContext(m_gameSession, m_pGameAudioSystem, &m_settings, *this);
}

GameplayOverlayContext IndoorGameView::createGameplayOverlayContext() const
{
    return GameplayOverlayContext(
        const_cast<GameSession &>(m_gameSession),
        m_pGameAudioSystem,
        const_cast<GameSettings *>(&m_settings),
        const_cast<IndoorGameView &>(*this));
}

IGameplayWorldRuntime *IndoorGameView::worldRuntime() const
{
    return m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->worldRuntime() : nullptr;
}

GameAudioSystem *IndoorGameView::audioSystem() const
{
    return m_pGameAudioSystem;
}

const ItemTable *IndoorGameView::itemTable() const
{
    return &m_gameSession.data().itemTable();
}

const StandardItemEnchantTable *IndoorGameView::standardItemEnchantTable() const
{
    return &m_gameSession.data().standardItemEnchantTable();
}

const SpecialItemEnchantTable *IndoorGameView::specialItemEnchantTable() const
{
    return &m_gameSession.data().specialItemEnchantTable();
}

const ClassSkillTable *IndoorGameView::classSkillTable() const
{
    return &m_gameSession.data().classSkillTable();
}

const CharacterDollTable *IndoorGameView::characterDollTable() const
{
    return &m_gameSession.data().characterDollTable();
}

const CharacterInspectTable *IndoorGameView::characterInspectTable() const
{
    return &m_gameSession.data().characterInspectTable();
}

const RosterTable *IndoorGameView::rosterTable() const
{
    return &m_gameSession.data().rosterTable();
}

const ReadableScrollTable *IndoorGameView::readableScrollTable() const
{
    return &m_gameSession.data().readableScrollTable();
}

const ItemEquipPosTable *IndoorGameView::itemEquipPosTable() const
{
    return &m_gameSession.data().itemEquipPosTable();
}

const SpellTable *IndoorGameView::spellTable() const
{
    return &m_gameSession.data().spellTable();
}

const HouseTable *IndoorGameView::houseTable() const
{
    return &m_gameSession.data().houseTable();
}

const ChestTable *IndoorGameView::chestTable() const
{
    return &m_gameSession.data().chestTable();
}

const NpcDialogTable *IndoorGameView::npcDialogTable() const
{
    return &m_gameSession.data().npcDialogTable();
}

const JournalQuestTable *IndoorGameView::journalQuestTable() const
{
    return &m_gameSession.data().journalQuestTable();
}

const JournalHistoryTable *IndoorGameView::journalHistoryTable() const
{
    return &m_gameSession.data().journalHistoryTable();
}

const JournalAutonoteTable *IndoorGameView::journalAutonoteTable() const
{
    return &m_gameSession.data().journalAutonoteTable();
}

const std::string &IndoorGameView::currentMapFileName() const
{
    static const std::string kEmptyMapFileName;
    return m_map ? m_map->fileName : kEmptyMapFileName;
}

float IndoorGameView::gameplayCameraYawRadians() const
{
    return 0.0f;
}

const std::vector<uint8_t> *IndoorGameView::journalMapFullyRevealedCells() const
{
    return nullptr;
}

const std::vector<uint8_t> *IndoorGameView::journalMapPartiallyRevealedCells() const
{
    return nullptr;
}

bool IndoorGameView::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    (void)requireGameplayReady;
    IndoorPartyRuntime *pRuntime = partyRuntime();
    return pRuntime != nullptr && pRuntime->party().setActiveMemberIndex(memberIndex);
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

void IndoorGameView::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_gameplayUiController.setStatusBarEvent(text, durationSeconds);
}

void IndoorGameView::executeActiveDialogAction()
{
    EventRuntimeState *pEventRuntimeState =
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    GameplayDialogController::Context context = buildDialogContext(*pEventRuntimeState);
    const GameplayDialogController::Result result = m_gameplayDialogController.executeActiveDialogAction(context);

    if (result.shouldCloseActiveDialog)
    {
        closeActiveEventDialog();
    }

    if (result.shouldOpenPendingEventDialog)
    {
        presentPendingEventDialog(result.previousMessageCount, result.allowNpcFallbackContent);
    }
}


void IndoorGameView::closeInventoryNestedOverlay()
{
    m_gameplayUiController.closeInventoryNestedOverlay();
}

bool IndoorGameView::tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen)
{
    GameplayUiController::HeldInventoryItemState &heldItem = m_gameplayUiController.heldInventoryItem();

    if (!heldItem.active || itemTable() == nullptr || partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    Party &party = partyRuntime()->party();
    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            party,
            memberIndex,
            heldItem.item,
            *itemTable(),
            readableScrollTable());

    if (!useResult.handled)
    {
        return false;
    }

    if (useResult.action == InventoryItemUseAction::CastScroll)
    {
        if (spellTable() == nullptr)
        {
            return false;
        }

        const SpellEntry *pSpellEntry = spellTable()->findById(static_cast<int>(useResult.spellId));

        if (pSpellEntry == nullptr)
        {
            setStatusBarEvent("Unknown scroll spell");
            return true;
        }

        PartySpellCastRequest request = {};
        request.casterMemberIndex = memberIndex;
        request.spellId = useResult.spellId;
        request.skillLevelOverride = useResult.spellSkillLevelOverride;
        request.skillMasteryOverride = useResult.spellSkillMasteryOverride;
        request.spendMana = false;
        request.applyRecovery = true;
        const PartySpellCastResult result =
            PartySpellSystem::castSpell(party, *worldRuntime(), *spellTable(), request);

        if (!result.succeeded())
        {
            setStatusBarEvent(result.statusText.empty() ? "Spell failed" : result.statusText);
            return true;
        }

        if (useResult.consumed)
        {
            heldItem = {};
        }
    }
    else if (useResult.action == InventoryItemUseAction::ReadMessageScroll)
    {
        GameplayUiController::ReadableScrollOverlayState &overlay = m_gameplayUiController.readableScrollOverlay();
        overlay.active = true;
        overlay.title = useResult.readableTitle;
        overlay.body = useResult.readableBody;
    }
    else
    {
        if (useResult.consumed)
        {
            heldItem = {};
        }

        if (useResult.action == InventoryItemUseAction::ConsumePotion
            && useResult.consumed
            && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Drink, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (useResult.action == InventoryItemUseAction::LearnSpell
                 && !useResult.consumed
                 && useResult.alreadyKnown
                 && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Error, GameAudioSystem::PlaybackGroup::Ui);
        }

        if (useResult.speechId.has_value())
        {
            playSpeechReaction(memberIndex, *useResult.speechId, true);
        }
    }

    if (!useResult.statusText.empty())
    {
        setStatusBarEvent(useResult.statusText);
    }

    const bool closeCharacterScreen = !keepCharacterScreenOpen || useResult.action == InventoryItemUseAction::CastScroll;

    if (closeCharacterScreen)
    {
        GameplayUiController::CharacterScreenState &screen = m_gameplayUiController.characterScreen();
        screen.open = false;
        screen.dollJewelryOverlayOpen = false;
    }

    return true;
}

void IndoorGameView::updateReadableScrollOverlayForHeldItem(
    size_t memberIndex,
    const GameplayCharacterPointerTarget &pointerTarget,
    bool isLeftMousePressed)
{
    GameplayUiController::ReadableScrollOverlayState &overlay = m_gameplayUiController.readableScrollOverlay();
    overlay = {};

    if (!isLeftMousePressed
        || !m_gameplayUiController.heldInventoryItem().active
        || itemTable() == nullptr
        || partyRuntime() == nullptr
        || (pointerTarget.type != GameplayCharacterPointerTargetType::EquipmentSlot
            && pointerTarget.type != GameplayCharacterPointerTargetType::DollPanel))
    {
        return;
    }

    const InventoryItemUseAction useAction =
        InventoryItemUseRuntime::classifyItemUse(m_gameplayUiController.heldInventoryItem().item, *itemTable());

    if (useAction != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    Party &party = partyRuntime()->party();
    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            party,
            memberIndex,
            m_gameplayUiController.heldInventoryItem().item,
            *itemTable(),
            readableScrollTable());

    if (!useResult.handled || useResult.action != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    overlay.active = true;
    overlay.title = useResult.readableTitle;
    overlay.body = useResult.readableBody;
}

void IndoorGameView::closeReadableScrollOverlay()
{
    m_gameplayUiController.closeReadableScrollOverlay();
}

void IndoorGameView::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    (void)memberIndex;
    (void)speechId;
    (void)triggerFaceAnimation;
}

void IndoorGameView::triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId)
{
    (void)memberIndex;
    (void)animationId;
}

bool IndoorGameView::tryCastSpellFromMember(
    size_t casterMemberIndex,
    uint32_t spellId,
    const std::string &spellName)
{
    if (spellTable() == nullptr || partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = casterMemberIndex;
    request.spellId = spellId;

    Party &party = partyRuntime()->party();
    const PartySpellCastResult result =
        PartySpellSystem::castSpell(party, *worldRuntime(), *spellTable(), request);

    if (!result.succeeded())
    {
        if (result.status == PartySpellCastStatus::NeedActorTarget
            || result.status == PartySpellCastStatus::NeedCharacterTarget
            || result.status == PartySpellCastStatus::NeedActorOrCharacterTarget
            || result.status == PartySpellCastStatus::NeedGroundPoint
            || result.status == PartySpellCastStatus::NeedInventoryItemTarget
            || result.status == PartySpellCastStatus::NeedUtilityUi)
        {
            setStatusBarEvent("Spell targeting is not wired indoors yet");
            return false;
        }

        if (!result.statusText.empty())
        {
            setStatusBarEvent(result.statusText);
        }

        return false;
    }

    if (m_pGameAudioSystem != nullptr)
    {
        const SpellEntry *pSpellEntry = spellTable()->findById(static_cast<int>(spellId));

        if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
            || result.effectKind == PartySpellCastEffectKind::PartyRestore)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Heal, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (pSpellEntry != nullptr
            && pSpellEntry->effectSoundId > 0
            && result.effectKind != PartySpellCastEffectKind::Projectile
            && result.effectKind != PartySpellCastEffectKind::MultiProjectile)
        {
            m_pGameAudioSystem->playSound(
                static_cast<uint32_t>(pSpellEntry->effectSoundId),
                GameAudioSystem::PlaybackGroup::Ui);
        }
    }

    setStatusBarEvent("Cast " + spellName);
    return true;
}

bool IndoorGameView::tryCastSpellRequest(
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    if (spellTable() == nullptr || partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    Party &party = partyRuntime()->party();
    const PartySpellCastResult result =
        PartySpellSystem::castSpell(party, *worldRuntime(), *spellTable(), request);

    if (!result.succeeded())
    {
        if (!result.statusText.empty())
        {
            setStatusBarEvent(result.statusText);
        }

        return false;
    }

    if (m_pGameAudioSystem != nullptr)
    {
        const SpellEntry *pSpellEntry = spellTable()->findById(static_cast<int>(request.spellId));

        if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
            || result.effectKind == PartySpellCastEffectKind::PartyRestore)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Heal, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (pSpellEntry != nullptr
            && pSpellEntry->effectSoundId > 0
            && result.effectKind != PartySpellCastEffectKind::Projectile
            && result.effectKind != PartySpellCastEffectKind::MultiProjectile)
        {
            m_pGameAudioSystem->playSound(
                static_cast<uint32_t>(pSpellEntry->effectSoundId),
                GameAudioSystem::PlaybackGroup::Ui);
        }
    }

    if (!spellName.empty())
    {
        setStatusBarEvent("Cast " + spellName);
    }

    return true;
}

GameSettings &IndoorGameView::mutableSettings()
{
    return m_settings;
}

std::array<uint8_t, SDL_SCANCODE_COUNT> &IndoorGameView::previousKeyboardState()
{
    return m_gameSession.previousKeyboardState();
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &IndoorGameView::previousKeyboardState() const
{
    return m_gameSession.previousKeyboardState();
}

bool IndoorGameView::trySaveToSelectedGameSlot()
{
    GameplayUiController::SaveGameScreenState &saveGameScreen = m_gameplayUiController.saveGameScreen();

    if (!saveGameScreen.active
        || saveGameScreen.slots.empty()
        || saveGameScreen.selectedIndex >= saveGameScreen.slots.size()
        || !m_gameSession.canSaveGameToPath())
    {
        return false;
    }

    std::string saveName;

    if (saveGameScreen.editActive)
    {
        saveName = saveGameScreen.editBuffer;
    }
    else
    {
        const GameplayUiController::SaveSlotSummary &slot = saveGameScreen.slots[saveGameScreen.selectedIndex];
        saveName = slot.fileLabel == "Empty" ? std::string() : slot.fileLabel;
    }

    if (saveName.empty())
    {
        saveName = m_map.has_value() ? m_map->name : "Save Game";
    }

    std::string error;
    const bool saved = m_gameSession.saveGameToPath(
        saveGameScreen.slots[saveGameScreen.selectedIndex].path,
        saveName,
        {},
        error);

    if (saved)
    {
        createGameplayOverlayContext().closeSaveGameOverlay();
    }

    return saved;
}

int IndoorGameView::restFoodRequired() const
{
    int foodRequired = 2;
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr)
    {
        return foodRequired;
    }

    constexpr uint32_t DragonRaceId = 5;
    const Party &party = pRuntime->party();

    for (const Character &member : party.members())
    {
        if (member.raceId == DragonRaceId)
        {
            ++foodRequired;
            break;
        }
    }

    return std::max(1, foodRequired);
}

const GameSettings &IndoorGameView::settingsSnapshot() const
{
    return m_settings;
}

bool IndoorGameView::shouldEnableGameplayMouseLook() const
{
    return createGameplayOverlayContext().currentHudScreenState() == GameplayHudScreenState::Gameplay;
}

void IndoorGameView::syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled)
{
    if (pWindow != nullptr && SDL_GetWindowRelativeMouseMode(pWindow) != enabled)
    {
        if (!enabled)
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
        }

        SDL_SetWindowRelativeMouseMode(pWindow, enabled);
        SDL_GetRelativeMouseState(nullptr, nullptr);
    }

    if (enabled)
    {
        SDL_HideCursor();
    }
    else
    {
        SDL_ShowCursor();
    }
}

void IndoorGameView::updateItemInspectOverlayState(int width, int height)
{
    GameplayUiController::ItemInspectOverlayState &overlay = m_gameplayUiController.itemInspectOverlay();
    overlay = {};

    if (width <= 0
        || height <= 0
        || itemTable() == nullptr
        || m_gameplayUiController.spellbook().active
        || m_gameplayUiController.controlsScreen().active
        || m_gameplayUiController.keyboardScreen().active
        || m_gameplayUiController.menuScreen().active
        || m_gameplayUiController.saveGameScreen().active
        || m_gameplayUiController.loadGameScreen().active)
    {
        return;
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    (void)GameplayHudOverlaySupport::tryPopulateItemInspectOverlayFromRenderedHudItems(
        overlayContext,
        width,
        height,
        false);
}

std::optional<std::string> IndoorGameView::findCachedAssetPath(
    const std::string &directoryPath,
    const std::string &fileName) const
{
    return GameplayHudCommon::findCachedAssetPath(
        m_pAssetFileSystem,
        m_gameplayUiRuntime.assetLoadCache(),
        directoryPath,
        fileName);
}

std::optional<std::vector<uint8_t>> IndoorGameView::readCachedBinaryFile(const std::string &assetPath) const
{
    return GameplayHudCommon::readCachedBinaryFile(
        m_pAssetFileSystem,
        m_gameplayUiRuntime.assetLoadCache(),
        assetPath);
}

std::optional<std::vector<uint8_t>> IndoorGameView::loadHudBitmapPixelsBgraCached(
    const std::string &textureName,
    int &width,
    int &height) const
{
    return GameplayHudCommon::loadHudBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_gameplayUiRuntime.assetLoadCache(),
        textureName,
        width,
        height);
}

bool IndoorGameView::loadHudTexture(const std::string &textureName)
{
    return GameplayHudCommon::loadHudTexture(
        m_pAssetFileSystem,
        m_gameplayUiRuntime.assetLoadCache(),
        textureName,
        m_gameplayUiRuntime.hudTextureHandles(),
        m_gameplayUiRuntime.hudTextureIndexByName());
}

bool IndoorGameView::loadHudFont(const std::string &fontName)
{
    return GameplayHudCommon::loadHudFont(
        m_pAssetFileSystem,
        m_gameplayUiRuntime.assetLoadCache(),
        fontName,
        m_gameplayUiRuntime.hudFontHandles());
}

GameplayDialogController::Context IndoorGameView::buildDialogContext(EventRuntimeState &eventRuntimeState)
{
    GameplayDialogController::Callbacks callbacks = {};
    callbacks.playSpeechReaction =
        [this](size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
        {
            playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
        };
    callbacks.playHouseSound =
        [this](uint32_t soundId)
        {
            if (m_pGameAudioSystem != nullptr)
            {
                m_pGameAudioSystem->playSound(soundId, GameAudioSystem::PlaybackGroup::HouseSpeech);
            }
        };
    callbacks.playCommonSound =
        [this](SoundId soundId)
        {
            if (m_pGameAudioSystem != nullptr)
            {
                m_pGameAudioSystem->playCommonSound(soundId, GameAudioSystem::PlaybackGroup::Ui);
            }
        };

    Party *pParty = partyRuntime() != nullptr ? &partyRuntime()->party() : nullptr;

    return buildGameplayDialogContext(
        m_gameplayUiController,
        eventRuntimeState,
        activeEventDialog(),
        eventDialogSelectionIndex(),
        pParty,
        worldRuntime(),
        m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->globalEventProgram() : nullptr,
        houseTable(),
        classSkillTable(),
        npcDialogTable(),
        m_map ? &*m_map : nullptr,
        &m_gameSession.data().mapEntries(),
        rosterTable(),
        &m_gameSession.data().arcomageLibrary(),
        createGameplayOverlayContext().currentHudScreenState() == GameplayHudScreenState::Dialogue,
        std::move(callbacks));
}

void IndoorGameView::presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent)
{
    GameplayDialogUiFlowState state = {
        m_gameplayUiController,
        m_overlayInteractionState,
        m_gameplayDialogController,
        eventDialogSelectionIndex()
    };
    ::OpenYAMM::Game::presentPendingEventDialog(
        state,
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        },
        previousMessageCount,
        allowNpcFallbackContent);
}

void IndoorGameView::closeActiveEventDialog()
{
    GameplayDialogUiFlowState state = {
        m_gameplayUiController,
        m_overlayInteractionState,
        m_gameplayDialogController,
        eventDialogSelectionIndex()
    };
    ::OpenYAMM::Game::closeActiveEventDialog(
        state,
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr);
}
} // namespace OpenYAMM::Game
