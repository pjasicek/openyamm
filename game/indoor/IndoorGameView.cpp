#include "game/indoor/IndoorGameView.h"

#include "engine/BgfxContext.h"
#include "game/app/GameSession.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/audio/SoundIds.h"
#include "game/items/ItemRuntime.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/scene/IndoorSceneRuntime.h"
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
    const GameplayScreenRuntime::SharedUiBootstrapResult sharedUiBootstrap =
        screenRuntime.initializeSharedUiRuntime(
            GameplayScreenRuntime::SharedUiBootstrapConfig{
                .pAssetFileSystem = &assetFileSystem,
                .portraitMemberCount = sceneRuntime.partyRuntime().party().members().size(),
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
            && !pendingSpellTargetActive;
        m_pIndoorRenderer->render(
            width,
            height,
            m_gameSession,
            input,
            deltaSeconds,
            allowWorldInput);
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
    return m_pIndoorRenderer != nullptr ? m_pIndoorRenderer->cameraYawRadians() : 0.0f;
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
        resolvedRequest.viewYawRadians = m_pIndoorRenderer->cameraYawRadians();
        resolvedRequest.viewPitchRadians = m_pIndoorRenderer->cameraPitchRadians();
        resolvedRequest.viewAspectRatio =
            static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(std::max(m_lastRenderHeight, 1));
    }

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    const GameplaySpellService::SpellRequestResolution resolution =
        m_gameSession.gameplaySpellService().resolveSpellRequest(screenRuntime, resolvedRequest, spellName);

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::CastSucceeded)
    {
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

bool IndoorGameView::beginSaveWithPreview(
    const std::filesystem::path &path,
    const std::string &saveName,
    bool closeUiOnSuccess)
{
    if (!m_gameSession.canSaveGameToPath())
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
        m_gameSession.requestRelativeMouseMotionReset();
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

void IndoorGameView::updateActorInspectOverlayState(int width, int height, const GameplayInputFrame &input)
{
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    GameplayUiController::ActorInspectOverlayState &actorInspectOverlay = screenRuntime.actorInspectOverlay();

    actorInspectOverlay = {};

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
        &screenRuntime);
}

} // namespace OpenYAMM::Game
