#include "game/outdoor/OutdoorGameView.h"

#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/outdoor/OutdoorGameplayInputController.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorPresentationController.h"
#include "game/outdoor/OutdoorRenderer.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/SpawnPreview.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/party/SpellSchool.h"
#include "game/party/SpellIds.h"
#include "game/SpriteObjectDefs.h"
#include "game/tables/SpriteTables.h"
#include "game/StringUtils.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudRenderer.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"
#include "game/ui/HudUiService.h"
#include "engine/TextTable.h"

#include <bx/math.h>

#include <bgfx/bgfx.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <future>
#include <iostream>
#include <iterator>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using SpellbookSchool = OutdoorGameView::SpellbookSchool;
using SpellbookPointerTargetType = OutdoorGameView::SpellbookPointerTargetType;

enum class HouseShopVerticalAlign
{
    Center,
    Top,
    Bottom,
    Baseline
};

struct HouseShopSlotLayout
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float baselineY = 0.0f;
    HouseShopVerticalAlign verticalAlign = HouseShopVerticalAlign::Center;
};

struct HouseShopVisualLayout
{
    std::string backgroundAsset;
    std::vector<HouseShopSlotLayout> slots;
};

struct HouseShopItemDrawRect
{
    size_t slotIndex = std::numeric_limits<size_t>::max();
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

HouseShopVisualLayout buildHouseShopVisualLayout(const HouseEntry &houseEntry, bool spellbookMode)
{
    HouseShopVisualLayout layout = {};

    if (spellbookMode)
    {
        layout.backgroundAsset = "MAGSHELF";

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            topRowSlot.y = 56.0f;
            topRowSlot.width = 74.0f;
            topRowSlot.height = 132.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Bottom;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            bottomRowSlot.y = 199.0f;
            bottomRowSlot.width = 74.0f;
            bottomRowSlot.height = 128.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Bottom;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Weapon Shop"))
    {
        layout.backgroundAsset = "WEPNTABL";
        constexpr std::array<float, 6> weaponTopOffsets = {88.0f, 34.0f, 112.0f, 58.0f, 128.0f, 46.0f};

        for (size_t index = 0; index < weaponTopOffsets.size(); ++index)
        {
            HouseShopSlotLayout slot = {};
            slot.x = 25.0f + static_cast<float>(index) * 70.0f;
            slot.y = weaponTopOffsets[index];
            slot.width = 70.0f;
            slot.height = 334.0f - weaponTopOffsets[index];
            slot.verticalAlign = HouseShopVerticalAlign::Top;
            layout.slots.push_back(slot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        layout.backgroundAsset = "ARMORY";

        for (size_t index = 0; index < 4; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 34.0f + static_cast<float>(index) * 105.0f;
            topRowSlot.y = 8.0f;
            topRowSlot.width = 105.0f;
            topRowSlot.height = 90.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Bottom;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 4; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 34.0f + static_cast<float>(index) * 105.0f;
            bottomRowSlot.y = 126.0f;
            bottomRowSlot.width = 105.0f;
            bottomRowSlot.height = 190.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Top;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Magic Shop"))
    {
        layout.backgroundAsset = "GENSHELF";

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            topRowSlot.y = 63.0f;
            topRowSlot.width = 74.0f;
            topRowSlot.height = 132.0f;
            topRowSlot.baselineY = 201.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            bottomRowSlot.y = 192.0f;
            bottomRowSlot.width = 74.0f;
            bottomRowSlot.height = 128.0f;
            bottomRowSlot.baselineY = 324.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        layout.backgroundAsset = "GENSHELF";

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            topRowSlot.y = 63.0f;
            topRowSlot.width = 74.0f;
            topRowSlot.height = 132.0f;
            topRowSlot.baselineY = 201.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            bottomRowSlot.y = 192.0f;
            bottomRowSlot.width = 74.0f;
            bottomRowSlot.height = 128.0f;
            bottomRowSlot.baselineY = 324.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Elemental Guild")
        || isHouseType(houseEntry, "Self Guild")
        || isHouseType(houseEntry, "Light Guild")
        || isHouseType(houseEntry, "Dark Guild")
        || isHouseType(houseEntry, "Spell Shop"))
    {
        layout.backgroundAsset = "MAGSHELF";

        for (size_t row = 0; row < 2; ++row)
        {
            for (size_t column = 0; column < 8; ++column)
            {
                HouseShopSlotLayout slot = {};
                slot.x = 14.0f + static_cast<float>(column) * 54.0f;
                slot.y = row == 0 ? 74.0f : 214.0f;
                slot.width = 48.0f;
                slot.height = 92.0f;
                slot.verticalAlign = HouseShopVerticalAlign::Top;
                layout.slots.push_back(slot);
            }
        }

        return layout;
    }

    return layout;
}

HouseShopItemDrawRect resolveHouseShopItemDrawRect(
    float frameX,
    float frameY,
    float frameWidth,
    float frameHeight,
    float frameScale,
    const HouseShopSlotLayout &slot,
    size_t slotIndex,
    int textureWidth,
    int textureHeight,
    int opaqueMinY,
    int opaqueMaxY)
{
    HouseShopItemDrawRect result = {};
    result.slotIndex = slotIndex;

    if (textureWidth <= 0 || textureHeight <= 0)
    {
        return result;
    }

    const float scaleX = frameWidth / 460.0f;
    const float scaleY = frameHeight / 344.0f;
    const float slotX = frameX + slot.x * scaleX;
    const float slotY = frameY + slot.y * scaleY;
    const float slotWidth = slot.width * scaleX;
    const float slotHeight = slot.height * scaleY;
    const float fitScale = std::min(
        slotWidth / static_cast<float>(textureWidth),
        slotHeight / static_cast<float>(textureHeight));
    const float itemScale = std::min(frameScale, fitScale);
    const float itemWidth = static_cast<float>(textureWidth) * itemScale;
    const float itemHeight = static_cast<float>(textureHeight) * itemScale;
    const float opaqueTop = static_cast<float>(std::max(0, opaqueMinY)) * itemScale;
    const float opaqueBottom = static_cast<float>(std::max(0, opaqueMaxY + 1)) * itemScale;

    result.width = itemWidth;
    result.height = itemHeight;
    result.x = std::round(slotX + (slotWidth - itemWidth) * 0.5f);

    switch (slot.verticalAlign)
    {
        case HouseShopVerticalAlign::Top:
            result.y = std::round(slotY - opaqueTop);
            break;

        case HouseShopVerticalAlign::Bottom:
            result.y = std::round(slotY + slotHeight - opaqueBottom);
            break;

        case HouseShopVerticalAlign::Baseline:
            result.y = std::round(frameY + slot.baselineY * scaleY - opaqueBottom);
            break;

        case HouseShopVerticalAlign::Center:
        default:
            result.y = std::round(slotY + (slotHeight - itemHeight) * 0.5f);
            break;
    }

    return result;
}

bool tryParseScrollSpellId(const InventoryItem &item, const ItemTable *pItemTable, uint32_t &spellId)
{
    if (pItemTable == nullptr)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(item.objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->equipStat != "Sscroll")
    {
        return false;
    }

    const std::string &token = pItemDefinition->mod1;

    if (token.size() < 2 || (token[0] != 'S' && token[0] != 's'))
    {
        return false;
    }

    for (size_t index = 1; index < token.size(); ++index)
    {
        if (!std::isdigit(static_cast<unsigned char>(token[index])))
        {
            return false;
        }
    }

    try
    {
        spellId = static_cast<uint32_t>(std::stoul(token.substr(1)));
    }
    catch (...)
    {
        return false;
    }

    return spellId > 0;
}

bool shouldSkipSpriteObjectInspectTarget(const SpriteObjectBillboard &object, const ObjectEntry *pObjectEntry)
{
    if (pObjectEntry == nullptr || object.objectDescriptionId == 0)
    {
        return true;
    }

    if ((object.attributes & (SpriteAttrTemporary | SpriteAttrMissile | SpriteAttrRemoved)) != 0)
    {
        return true;
    }

    if ((pObjectEntry->flags & (ObjectDescNoSprite
                                | ObjectDescNoCollision
                                | ObjectDescTemporary
                                | ObjectDescUnpickable
                                | ObjectDescTrailParticle
                                | ObjectDescTrailFire
                                | ObjectDescTrailLine)) != 0)
    {
        return true;
    }

    if (object.spellId != 0)
    {
        return true;
    }

    return false;
}

constexpr uint16_t SkyViewId = 0;
constexpr uint16_t MainViewId = 1;
constexpr uint16_t HudViewId = 2;
constexpr float DefaultOutdoorFarClip = 200000.0f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float RuntimeProjectileRenderDistance = 12288.0f;
constexpr float RuntimeProjectileRenderDistanceSquared =
    RuntimeProjectileRenderDistance * RuntimeProjectileRenderDistance;
constexpr float DecorationBillboardRenderDistance = 16384.0f;
constexpr float DecorationBillboardRenderDistanceSquared =
    DecorationBillboardRenderDistance * DecorationBillboardRenderDistance;
constexpr float ActorBillboardRenderDistance = 16384.0f;
constexpr float ActorBillboardRenderDistanceSquared =
    ActorBillboardRenderDistance * ActorBillboardRenderDistance;
constexpr float BillboardSpatialCellSize = 2048.0f;
constexpr uint64_t RenderHitchLogThresholdNanoseconds = 16 * 1000 * 1000;
constexpr float CameraVerticalFovRadians = CameraVerticalFovDegrees * (Pi / 180.0f);
constexpr int DebugTextCellWidthPixels = 8;
constexpr int DebugTextCellHeightPixels = 16;
constexpr float BillboardNearDepth = 0.1f;
constexpr bool DebugProjectileDrawLogging = false;
constexpr float DebugProjectileTrailSeconds = 0.05f;
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float OeMouseInteractionDistance = 512.0f;
constexpr float OeCharacterMeleeAttackDistance = 407.2f;
constexpr float OeMeleeAlertDistance = 307.2f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr float OeNearHoverDistance = 512.0f;
constexpr float OeActorHoverDistance = 8192.0f;
constexpr uint32_t OeArrowProjectileObjectId = 545;
constexpr uint32_t OeBlasterProjectileObjectId = 555;
constexpr float OutdoorWalkableNormalZ = 0.70710678f;
constexpr float OutdoorMaxStepHeight = 128.0f;
constexpr size_t PreloadDecodeWorkerCount = 4;
constexpr uint64_t BillboardAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;
constexpr bool DebugSpritePreloadLogging = false;
constexpr bool DebugRenderHitchLogging = false;
constexpr bool DebugActorRenderHitchLogging = false;
constexpr std::string_view PartyStartDecorationName = "party start";
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr uint32_t SkyDomeHorizontalSegmentCount = 24;
constexpr uint32_t SkyDomeVerticalSegmentCount = 8;
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;
constexpr uint64_t HoverInspectRefreshNanoseconds = 20 * 1000 * 1000;
constexpr uint32_t SpeechReactionCooldownMs = 900;
constexpr uint32_t CombatSpeechReactionCooldownMs = 2500;
constexpr uint32_t KillSpeechChancePercent = 20;
constexpr float WalkingSoundMovementSpeedThreshold = 20.0f;
constexpr float WalkingMotionHoldSeconds = 0.125f;
constexpr uint32_t BrokenItemTintColorAbgr = 0x800000ffu;
constexpr uint32_t UnidentifiedItemTintColorAbgr = 0x80ff0000u;

enum class ItemTintContext
{
    None,
    Held,
    Equipped,
    ShopIdentify,
    ShopRepair,
};

bool bypassSpeechCooldown(SpeechId speechId)
{
    switch (speechId)
    {
        case SpeechId::IdentifyWeakItem:
        case SpeechId::IdentifyGreatItem:
        case SpeechId::IdentifyFailItem:
        case SpeechId::RepairSuccess:
        case SpeechId::RepairFail:
        case SpeechId::CantLearnSpell:
        case SpeechId::LearnSpell:
            return true;

        default:
            return false;
    }
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

void appendPopupBodyLine(std::string &body, const std::string &line)
{
    if (line.empty())
    {
        return;
    }

    if (!body.empty())
    {
        body.push_back('\n');
    }

    body += line;
}

std::string formatRemainingDuration(float remainingSeconds)
{
    const int totalSeconds = std::max(0, static_cast<int>(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;

    if (hours > 0)
    {
        if (minutes > 0)
        {
            return std::to_string(hours) + "h " + std::to_string(minutes) + "m";
        }

        return std::to_string(hours) + "h";
    }

    if (minutes > 0)
    {
        if (seconds > 0 && minutes < 5)
        {
            return std::to_string(minutes) + "m " + std::to_string(seconds) + "s";
        }

        return std::to_string(minutes) + "m";
    }

    return std::to_string(seconds) + "s";
}

struct GoldHeapVisual
{
    const char *pTextureName = "item204";
    uint8_t width = 1;
    uint8_t height = 1;
    uint32_t objectDescriptionId = 187;
};

GoldHeapVisual classifyGoldHeapVisual(uint32_t goldAmount)
{
    // OE stores small/medium/large gold piles as distinct items at generation time.
    // We infer the same visual tier from the generated amount ranges.
    if (goldAmount <= 200)
    {
        return {"item204", 1, 1, 187};
    }

    if (goldAmount <= 1000)
    {
        return {"item205", 2, 1, 188};
    }

    return {"item206", 2, 1, 189};
}

enum class PortraitAggroIndicator
{
    Hidden,
    Black,
    Green,
    Yellow,
    Red,
};

PortraitAggroIndicator classifyPortraitAggroIndicator(
    const Character &member,
    const OutdoorPartyRuntime *pPartyRuntime,
    const OutdoorWorldRuntime *pWorldRuntime)
{
    if (!GameMechanics::canAct(member))
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (member.recoverySecondsRemaining > 0.0f)
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (pPartyRuntime == nullptr || pWorldRuntime == nullptr)
    {
        return PortraitAggroIndicator::Hidden;
    }

    const OutdoorMoveState &partyMoveState = pPartyRuntime->movementState();
    float nearestHostileDistance = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = pWorldRuntime->mapActorState(actorIndex);

        if (pActor == nullptr || pActor->isDead || pActor->isInvisible || !pActor->hostileToParty)
        {
            continue;
        }

        const float actorX = pActor->preciseX != 0.0f ? pActor->preciseX : static_cast<float>(pActor->x);
        const float actorY = pActor->preciseY != 0.0f ? pActor->preciseY : static_cast<float>(pActor->y);
        const float actorZ = pActor->movementStateInitialized
            ? pActor->movementState.footZ
            : (pActor->preciseZ != 0.0f ? pActor->preciseZ : static_cast<float>(pActor->z));
        const float deltaX = actorX - partyMoveState.x;
        const float deltaY = actorY - partyMoveState.y;
        const float deltaZ = actorZ - partyMoveState.footZ;
        const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, centerDistance - static_cast<float>(pActor->radius));
        nearestHostileDistance = std::min(nearestHostileDistance, edgeDistance);
    }

    if (nearestHostileDistance < OeMeleeAlertDistance)
    {
        return PortraitAggroIndicator::Red;
    }

    if (nearestHostileDistance < OeYellowAlertDistance)
    {
        return PortraitAggroIndicator::Yellow;
    }

    return PortraitAggroIndicator::Green;
}

std::string normalizeDecorationKey(const std::string &value)
{
    const std::string lowered = toLowerCopy(value);
    size_t begin = 0;

    while (begin < lowered.size() && std::isspace(static_cast<unsigned char>(lowered[begin])) != 0)
    {
        ++begin;
    }

    size_t end = lowered.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(lowered[end - 1])) != 0)
    {
        --end;
    }

    return lowered.substr(begin, end - begin);
}

std::string formatPartyAttackStatusText(
    const std::string &attackerName,
    const std::string &targetName,
    const CharacterAttackResult &attack,
    bool killed)
{
    if (!attack.canAttack)
    {
        return "Target is out of range";
    }

    if (attack.resolvesOnImpact)
    {
        if (!targetName.empty())
        {
            return attackerName + " shoots " + targetName;
        }

        return attack.mode == CharacterAttackMode::Melee ? attackerName + " swings" : attackerName + " shoots";
    }

    if (targetName.empty())
    {
        return attackerName + " swings";
    }

    if (!attack.hit)
    {
        return attackerName + " misses " + targetName;
    }

    if (killed)
    {
        return attackerName + " inflicts " + std::to_string(attack.damage) + " points killing " + targetName;
    }

    if (attack.mode == CharacterAttackMode::Bow
        || attack.mode == CharacterAttackMode::Wand
        || attack.mode == CharacterAttackMode::Blaster)
    {
        return attackerName + " shoots " + targetName + " for " + std::to_string(attack.damage) + " points";
    }

    return attackerName + " hits " + targetName + " for " + std::to_string(attack.damage) + " damage";
}

bool decorationMatchesAnyKey(
    const std::vector<std::string> &keys,
    std::initializer_list<std::string_view> candidates)
{
    for (const std::string &key : keys)
    {
        for (std::string_view candidate : candidates)
        {
            if (key == candidate)
            {
                return true;
            }
        }
    }

    return false;
}

std::optional<OutdoorGameView::InteractiveDecorationFamily> classifyInteractiveDecorationFamily(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    std::vector<std::string> keys;
    keys.reserve(3);

    const std::string hint = normalizeDecorationKey(decoration.hint);
    const std::string internalName = normalizeDecorationKey(decoration.internalName);
    const std::string normalizedInstanceName = normalizeDecorationKey(instanceName);

    if (!hint.empty())
    {
        keys.push_back(hint);
    }

    if (!internalName.empty() && std::find(keys.begin(), keys.end(), internalName) == keys.end())
    {
        keys.push_back(internalName);
    }

    if (!normalizedInstanceName.empty()
        && std::find(keys.begin(), keys.end(), normalizedInstanceName) == keys.end())
    {
        keys.push_back(normalizedInstanceName);
    }

    if (decorationMatchesAnyKey(keys, {"barrel", "dec03", "dec32"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::Barrel;
    }

    if (decorationMatchesAnyKey(keys, {"cauldron", "dec26"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::Cauldron;
    }

    if (decorationMatchesAnyKey(keys, {"trash heap", "trash pile", "dec01", "dec10", "dec23"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::TrashHeap;
    }

    if (decorationMatchesAnyKey(keys, {"campfire", "camp fire", "dec24", "dec25"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::CampFire;
    }

    if (decorationMatchesAnyKey(keys, {"keg", "cask", "dec21"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::Cask;
    }

    return std::nullopt;
}

float resolveActorAabbBaseZ(
    const OutdoorMapData &outdoorMapData,
    const OutdoorWorldRuntime::MapActorState *pActorState,
    int actorX,
    int actorY,
    int actorZ,
    bool clampDeadActorToGround)
{
    if (!clampDeadActorToGround)
    {
        return static_cast<float>(actorZ);
    }

    if (pActorState != nullptr && pActorState->movementStateInitialized)
    {
        const OutdoorMoveState &movementState = pActorState->movementState;

        if (movementState.supportKind == OutdoorSupportKind::Terrain
            || movementState.supportKind == OutdoorSupportKind::BModelFace)
        {
            return movementState.footZ - 1.0f;
        }
    }

    return sampleOutdoorSupportFloorHeight(
        outdoorMapData,
        static_cast<float>(actorX),
        static_cast<float>(actorY),
        static_cast<float>(actorZ));
}

uint16_t interactiveDecorationBaseEventId(OutdoorGameView::InteractiveDecorationFamily family)
{
    switch (family)
    {
        case OutdoorGameView::InteractiveDecorationFamily::Barrel:
            return 268;

        case OutdoorGameView::InteractiveDecorationFamily::Cauldron:
            return 276;

        case OutdoorGameView::InteractiveDecorationFamily::TrashHeap:
            return 281;

        case OutdoorGameView::InteractiveDecorationFamily::CampFire:
            return 285;

        case OutdoorGameView::InteractiveDecorationFamily::Cask:
            return 288;

        case OutdoorGameView::InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

uint8_t interactiveDecorationEventCount(OutdoorGameView::InteractiveDecorationFamily family)
{
    switch (family)
    {
        case OutdoorGameView::InteractiveDecorationFamily::Barrel:
            return 8;

        case OutdoorGameView::InteractiveDecorationFamily::Cauldron:
            return 5;

        case OutdoorGameView::InteractiveDecorationFamily::TrashHeap:
            return 4;

        case OutdoorGameView::InteractiveDecorationFamily::CampFire:
            return 2;

        case OutdoorGameView::InteractiveDecorationFamily::Cask:
            return 2;

        case OutdoorGameView::InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

bool interactiveDecorationHidesWhenCleared(OutdoorGameView::InteractiveDecorationFamily family)
{
    return family == OutdoorGameView::InteractiveDecorationFamily::CampFire;
}

uint32_t makeInteractiveDecorationSeed(const OutdoorEntity &entity, size_t entityIndex)
{
    uint32_t seed = static_cast<uint32_t>((entityIndex + 1u) * 2654435761u);
    seed ^= static_cast<uint32_t>(entity.decorationListId + 1u) * 2246822519u;
    seed ^= static_cast<uint32_t>(entity.x) * 3266489917u;
    seed ^= static_cast<uint32_t>(entity.y) * 668265263u;
    seed ^= static_cast<uint32_t>(entity.z + 1) * 374761393u;
    return seed;
}

uint8_t initialInteractiveDecorationState(
    OutdoorGameView::InteractiveDecorationFamily family,
    uint32_t seed)
{
    switch (family)
    {
        case OutdoorGameView::InteractiveDecorationFamily::Barrel:
            return static_cast<uint8_t>(1u + seed % 7u);

        case OutdoorGameView::InteractiveDecorationFamily::Cauldron:
            return static_cast<uint8_t>(1u + seed % 4u);

        case OutdoorGameView::InteractiveDecorationFamily::Cask:
            return 1;

        case OutdoorGameView::InteractiveDecorationFamily::TrashHeap:
        case OutdoorGameView::InteractiveDecorationFamily::CampFire:
        case OutdoorGameView::InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
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

struct CharacterStatRowDefinition
{
    const char *pStatName;
    const char *pLabelId;
    const char *pValueId;
};

constexpr std::array<CharacterStatRowDefinition, 26> CharacterStatRows = {{
    {"SkillPoints", "CharacterStatsSkillPointsTextLabel", "CharacterStatsSkillPointsValue"},
    {"Might", "CharacterStatMightLabel", "CharacterStatMightValue"},
    {"Intellect", "CharacterStatIntellectLabel", "CharacterStatIntellectValue"},
    {"Personality", "CharacterStatPersonalityLabel", "CharacterStatPersonalityValue"},
    {"Endurance", "CharacterStatEnduranceLabel", "CharacterStatEnduranceValue"},
    {"Accuracy", "CharacterStatAccuracyLabel", "CharacterStatAccuracyValue"},
    {"Speed", "CharacterStatSpeedLabel", "CharacterStatSpeedValue"},
    {"Luck", "CharacterStatLuckLabel", "CharacterStatLuckValue"},
    {"HitPoints", "CharacterStatHitPointsLabel", "CharacterStatHitPointsValue"},
    {"SpellPoints", "CharacterStatSpellPointsLabel", "CharacterStatSpellPointsValue"},
    {"ArmorClass", "CharacterStatArmorClassLabel", "CharacterStatArmorClassValue"},
    {"Condition", "CharacterStatConditionLabel", "CharacterStatConditionValue"},
    {"QuickSpell", "CharacterStatQuickSpellLabel", "CharacterStatQuickSpellValue"},
    {"Age", "CharacterStatAgeLabel", "CharacterStatAgeValue"},
    {"Level", "CharacterStatLevelLabel", "CharacterStatLevelValue"},
    {"Experience", "CharacterStatExperienceLabel", "CharacterStatExperienceValue"},
    {"Attack", "CharacterStatAttackLabel", "CharacterStatAttackValue"},
    {"MeleeDamage", "CharacterStatMeleeDamageLabel", "CharacterStatMeleeDamageValue"},
    {"Shoot", "CharacterStatShootLabel", "CharacterStatShootValue"},
    {"RangedDamage", "CharacterStatRangedDamageLabel", "CharacterStatRangedDamageValue"},
    {"FireResistance", "CharacterStatFireResistanceLabel", "CharacterStatFireResistanceValue"},
    {"AirResistance", "CharacterStatAirResistanceLabel", "CharacterStatAirResistanceValue"},
    {"WaterResistance", "CharacterStatWaterResistanceLabel", "CharacterStatWaterResistanceValue"},
    {"EarthResistance", "CharacterStatEarthResistanceLabel", "CharacterStatEarthResistanceValue"},
    {"MindResistance", "CharacterStatMindResistanceLabel", "CharacterStatMindResistanceValue"},
    {"BodyResistance", "CharacterStatBodyResistanceLabel", "CharacterStatBodyResistanceValue"},
}};

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
    return jewelryOverlayOpen ? isJewelryOverlayEquipmentSlot(slot) : !isJewelryOverlayEquipmentSlot(slot);
}

bool usesAlternateCloakBeltEquippedVariant(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Cloak || slot == EquipmentSlot::Belt;
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

std::string formatFoundItemStatusText(int goldAmount, const std::string &itemName)
{
    const std::string resolvedItemName = itemName.empty() ? "item" : itemName;

    if (goldAmount > 0)
    {
        return "You found " + std::to_string(goldAmount) + " gold and an item (" + resolvedItemName + ")!";
    }

    return "You found an item (" + resolvedItemName + ")!";
}

std::string formatFoundGoldStatusText(int goldAmount)
{
    return "You found " + std::to_string(std::max(0, goldAmount)) + " gold!";
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
    return computeInventoryGridMetrics(x, y, width, height, scale, Character::InventoryWidth, Character::InventoryHeight);
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
        gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth
        + offsetX);
    rect.y = std::round(
        gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight
        + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

std::optional<std::pair<int, int>> computeHeldInventoryPlacement(
    const InventoryGridMetrics &gridMetrics,
    uint8_t itemWidthCells,
    uint8_t itemHeightCells,
    float textureWidth,
    float textureHeight,
    float drawX,
    float drawY)
{
    if (gridMetrics.cellWidth <= 0.0f || gridMetrics.cellHeight <= 0.0f)
    {
        return std::nullopt;
    }

    const float slotSpanWidth = static_cast<float>(itemWidthCells) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(itemHeightCells) * gridMetrics.cellHeight;
    const float itemCenterX = drawX + textureWidth * 0.5f;
    const float itemCenterY = drawY + textureHeight * 0.5f;
    const int gridX = static_cast<int>(std::floor(
        (itemCenterX - gridMetrics.x - slotSpanWidth * 0.5f + gridMetrics.cellWidth * 0.5f)
        / gridMetrics.cellWidth));
    const int gridY = static_cast<int>(std::floor(
        (itemCenterY - gridMetrics.y - slotSpanHeight * 0.5f + gridMetrics.cellHeight * 0.5f)
        / gridMetrics.cellHeight));
    return std::pair<int, int>(gridX, gridY);
}

InventoryItemScreenRect computeCenteredItemRect(
    float layoutX,
    float layoutY,
    float layoutWidth,
    float layoutHeight,
    float textureWidth,
    float textureHeight)
{
    InventoryItemScreenRect rect = {};
    rect.x = std::round(layoutX + (layoutWidth - textureWidth) * 0.5f);
    rect.y = std::round(layoutY + (layoutHeight - textureHeight) * 0.5f);
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
    static std::unordered_map<std::string, std::string> s_lastPayloadByKey;

    std::ostringstream payloadStream;
    payloadStream << "sprite=\"" << assetName
                  << "\" parent=\"" << parentId << "\""
                  << " x=" << x
                  << " y=" << y
                  << " z=" << zIndex
                  << " width=" << width
                  << " height=" << height
                  << " logical_x=" << logicalX
                  << " logical_y=" << logicalY
                  << " logical_width=" << logicalWidth
                  << " logical_height=" << logicalHeight;
    const std::string payload = payloadStream.str();

    const std::unordered_map<std::string, std::string>::const_iterator it = s_lastPayloadByKey.find(renderKey);

    if (it != s_lastPayloadByKey.end() && it->second == payload)
    {
        return;
    }

    s_lastPayloadByKey[renderKey] = payload;
    std::cout << "Character equipment render " << renderKey << ": " << payload << '\n';
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
    appendCharacterSkillUiRows(*pCharacter, data.weaponRows, shownSkillNames, WeaponSkillNames, std::size(WeaponSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.magicRows, shownSkillNames, MagicSkillNames, std::size(MagicSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.armorRows, shownSkillNames, ArmorSkillNames, std::size(ArmorSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.miscRows, shownSkillNames, MiscSkillNames, std::size(MiscSkillNames));

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
        }
    );

    data.miscRows.insert(data.miscRows.end(), extraMiscRows.begin(), extraMiscRows.end());
    return data;
}

int skillMasteryAvailability(
    const ClassSkillTable *pClassSkillTable,
    const Character *pCharacter,
    const std::string &skillName,
    SkillMastery mastery)
{
    if (pClassSkillTable == nullptr || pCharacter == nullptr)
    {
        return 0;
    }

    if (pClassSkillTable->getClassCap(pCharacter->className, skillName) >= mastery)
    {
        return 0;
    }

    if (pClassSkillTable->getHighestPromotionCap(pCharacter->className, skillName) >= mastery)
    {
        return 1;
    }

    return 2;
}

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return static_cast<uint32_t>(red)
        | (static_cast<uint32_t>(green) << 8)
        | (static_cast<uint32_t>(blue) << 16)
        | 0xff000000u;
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

template <typename Target, typename ResolveTargetFn, typename ActivateTargetFn>
void handlePointerClickRelease(
    const HudPointerState &pointerState,
    bool &clickLatch,
    Target &pressedTarget,
    const Target &noneTarget,
    ResolveTargetFn resolveTargetFn,
    ActivateTargetFn activateTargetFn)
{
    if (pointerState.leftButtonPressed)
    {
        if (!clickLatch)
        {
            pressedTarget = resolveTargetFn(pointerState.x, pointerState.y);
            clickLatch = true;
        }
    }
    else if (clickLatch)
    {
        const Target currentTarget = resolveTargetFn(pointerState.x, pointerState.y);

        if (currentTarget == pressedTarget)
        {
            activateTargetFn(currentTarget);
        }

        clickLatch = false;
        pressedTarget = noneTarget;
    }
    else
    {
        pressedTarget = noneTarget;
    }
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

uint32_t currentDialogueHostHouseId(const EventRuntimeState *pEventRuntimeState)
{
    return pEventRuntimeState != nullptr ? pEventRuntimeState->dialogueState.hostHouseId : 0;
}

const EventIrEvent *findEventById(const EventIrProgram &program, uint16_t eventId)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        if (event.eventId == eventId)
        {
            return &event;
        }
    }

    return nullptr;
}

const EventIrEvent *findCurrentMapEventById(
    const std::optional<EventIrProgram> &localProgram,
    const std::optional<EventIrProgram> &globalProgram,
    uint16_t eventId)
{
    if (eventId == 0)
    {
        return nullptr;
    }

    if (localProgram)
    {
        const EventIrEvent *pLocalEvent = findEventById(*localProgram, eventId);

        if (pLocalEvent != nullptr)
        {
            return pLocalEvent;
        }
    }

    if (globalProgram)
    {
        return findEventById(*globalProgram, eventId);
    }

    return nullptr;
}

std::vector<std::string> collectRelevantHouseVideoStemsForMap(
    const OutdoorMapData &outdoorMapData,
    const std::optional<EventIrProgram> &localProgram,
    const std::optional<EventIrProgram> &globalProgram,
    const HouseTable &houseTable)
{
    std::unordered_set<uint16_t> rootEventIds;

    for (const OutdoorEntity &entity : outdoorMapData.entities)
    {
        if (entity.eventIdPrimary != 0)
        {
            rootEventIds.insert(entity.eventIdPrimary);
        }

        if (entity.eventIdSecondary != 0)
        {
            rootEventIds.insert(entity.eventIdSecondary);
        }
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.cogTriggeredNumber != 0)
            {
                rootEventIds.insert(face.cogTriggeredNumber);
            }
        }
    }

    std::unordered_set<uint16_t> visitedEventIds;
    std::vector<uint16_t> pendingEventIds(rootEventIds.begin(), rootEventIds.end());
    std::unordered_set<std::string> seenVideoStems;
    std::vector<std::string> videoStems;

    while (!pendingEventIds.empty())
    {
        const uint16_t eventId = pendingEventIds.back();
        pendingEventIds.pop_back();

        if (!visitedEventIds.insert(eventId).second)
        {
            continue;
        }

        const EventIrEvent *pEvent = findCurrentMapEventById(localProgram, globalProgram, eventId);

        if (pEvent == nullptr)
        {
            continue;
        }

        for (const EventIrInstruction &instruction : pEvent->instructions)
        {
            if (instruction.operation == EventIrOperation::SpeakInHouse
                && !instruction.arguments.empty())
            {
                const HouseEntry *pHouseEntry = houseTable.get(instruction.arguments[0]);

                if (pHouseEntry != nullptr
                    && !pHouseEntry->videoName.empty()
                    && seenVideoStems.insert(pHouseEntry->videoName).second)
                {
                    videoStems.push_back(pHouseEntry->videoName);
                }
            }
            else if (instruction.operation == EventIrOperation::ChangeEvent
                && !instruction.arguments.empty())
            {
                pendingEventIds.push_back(static_cast<uint16_t>(instruction.arguments[0]));
            }
            else if (instruction.operation == EventIrOperation::RandomJump)
            {
                for (uint32_t targetEventId : instruction.arguments)
                {
                    if (targetEventId != 0)
                    {
                        pendingEventIds.push_back(static_cast<uint16_t>(targetEventId));
                    }
                }
            }
        }
    }

    std::sort(videoStems.begin(), videoStems.end());
    return videoStems;
}

uint32_t makeAbgrColor(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

constexpr float OutdoorMinimapZoom = 512.0f;

struct SpriteTexturePreloadRequest
{
    std::string textureName;
    int16_t paletteId = 0;
    std::vector<uint8_t> bitmapBytes;
    std::optional<std::array<uint8_t, 256 * 3>> overridePalette;
};

struct DecodedSpriteTexture
{
    std::string textureName;
    int16_t paletteId = 0;
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};
constexpr uint8_t OutdoorPolygonFloor = 0x3;
constexpr uint8_t OutdoorPolygonInBetweenFloorAndWall = 0x4;
constexpr int DwiMapId = 1;
constexpr uint16_t DwiMeteorShowerEventId = 456;

struct OutdoorPartyStartPoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
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
    if (font.firstChar < 0 || font.firstChar > 255 || font.lastChar < 0 || font.lastChar > 255
        || font.firstChar > font.lastChar || font.fontHeight <= 0)
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
    constexpr size_t fontHeaderSize = 32;
    constexpr size_t mm7AtlasSize = 4096;
    constexpr size_t mmxAtlasSize = 1280;

    if (bytes.size() < fontHeaderSize + mmxAtlasSize)
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

    if (bytes.size() >= fontHeaderSize + mm7AtlasSize)
    {
        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t metricOffset = fontHeaderSize + static_cast<size_t>(glyphIndex) * 12;
            mm7Font.glyphMetrics[glyphIndex].leftSpacing = readInt32Le(&pBytes[metricOffset]);
            mm7Font.glyphMetrics[glyphIndex].width = readInt32Le(&pBytes[metricOffset + 4]);
            mm7Font.glyphMetrics[glyphIndex].rightSpacing = readInt32Le(&pBytes[metricOffset + 8]);
        }

        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t offsetPosition = fontHeaderSize + 256 * 12 + static_cast<size_t>(glyphIndex) * 4;
            mm7Font.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
        }

        mm7Font.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(fontHeaderSize + mm7AtlasSize), bytes.end());

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
        mmxFont.glyphMetrics[glyphIndex].leftSpacing = 0;
        mmxFont.glyphMetrics[glyphIndex].width = pBytes[fontHeaderSize + glyphIndex];
        mmxFont.glyphMetrics[glyphIndex].rightSpacing = 0;
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t offsetPosition = fontHeaderSize + 256 + static_cast<size_t>(glyphIndex) * 4;
        mmxFont.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
    }

    mmxFont.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(fontHeaderSize + mmxAtlasSize), bytes.end());

    if (!validateParsedHudBitmapFont(mmxFont, mmxFont.pixels))
    {
        return std::nullopt;
    }

    return mmxFont;
}

std::optional<float> parseHudLayoutFloat(const std::string &value)
{
    char *pEnd = nullptr;
    const float result = std::strtof(value.c_str(), &pEnd);

    if (pEnd == value.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return result;
}

std::optional<bool> parseHudLayoutBool(const std::string &value)
{
    const std::string lowerValue = toLowerCopy(value);

    if (lowerValue == "1" || lowerValue == "true" || lowerValue == "yes")
    {
        return true;
    }

    if (lowerValue == "0" || lowerValue == "false" || lowerValue == "no")
    {
        return false;
    }

    return std::nullopt;
}

std::optional<OutdoorPartyStartPoint> resolveOutdoorPartyStartPoint(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData)
{
    const std::optional<std::vector<uint8_t>> decorationTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/ddeclist.bin");

    if (!decorationTableBytes)
    {
        return std::nullopt;
    }

    DecorationTable decorationTable;

    if (!decorationTable.loadFromBytes(*decorationTableBytes))
    {
        return std::nullopt;
    }

    for (const OutdoorEntity &entity : outdoorMapData.entities)
    {
        std::string decorationName = toLowerCopy(entity.name);

        if (decorationName.empty())
        {
            if (const DecorationEntry *pDecoration = decorationTable.get(entity.decorationListId))
            {
                decorationName = pDecoration->internalName;
            }
        }

        if (decorationName != PartyStartDecorationName)
        {
            continue;
        }

        OutdoorPartyStartPoint startPoint = {};
        startPoint.x = static_cast<float>(-entity.x);
        startPoint.y = static_cast<float>(entity.y);
        startPoint.z = static_cast<float>(entity.z);
        return startPoint;
    }

    return std::nullopt;
}

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

uint32_t secondsToAnimationTicks(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return 0;
    }

    return static_cast<uint32_t>(std::max(0.0f, std::round(deltaSeconds * 128.0f)));
}

std::string portraitTextureNameForPictureFrame(uint32_t pictureId, uint16_t frameIndex)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-%02u", pictureId + 1, std::max<uint16_t>(1, frameIndex));
    return buffer;
}

uint32_t mixPortraitSequenceValue(uint32_t value)
{
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return value;
}

PortraitId pickIdlePortrait(uint32_t sequenceValue)
{
    const uint32_t randomValue = sequenceValue % 100u;

    if (randomValue < 25u)
    {
        return PortraitId::Blink;
    }

    if (randomValue < 31u)
    {
        return PortraitId::Wink;
    }

    if (randomValue < 37u)
    {
        return PortraitId::MouthOpenRandom;
    }

    if (randomValue < 43u)
    {
        return PortraitId::PurseLipsRandom;
    }

    if (randomValue < 46u)
    {
        return PortraitId::LookUp;
    }

    if (randomValue < 52u)
    {
        return PortraitId::LookRight;
    }

    if (randomValue < 58u)
    {
        return PortraitId::LookLeft;
    }

    if (randomValue < 64u)
    {
        return PortraitId::LookDown;
    }

    if (randomValue < 70u)
    {
        return PortraitId::Portrait54;
    }

    if (randomValue < 76u)
    {
        return PortraitId::Portrait55;
    }

    if (randomValue < 82u)
    {
        return PortraitId::Portrait56;
    }

    if (randomValue < 88u)
    {
        return PortraitId::Portrait57;
    }

    if (randomValue < 94u)
    {
        return PortraitId::PurseLips1;
    }

    return PortraitId::PurseLips2;
}

uint32_t pickNormalPortraitDurationTicks(uint32_t sequenceValue)
{
    return 32u + (sequenceValue % 257u);
}

bool portraitExpressionAllowedForCondition(
    const std::optional<CharacterCondition> &displayedCondition,
    PortraitId newPortrait)
{
    if (!displayedCondition)
    {
        return true;
    }

    const std::optional<PortraitId> currentPortrait = portraitIdForCondition(*displayedCondition);

    if (!currentPortrait)
    {
        return true;
    }

    if (*currentPortrait == PortraitId::Dead || *currentPortrait == PortraitId::Eradicated)
    {
        return false;
    }

    if (*currentPortrait == PortraitId::Petrified)
    {
        return newPortrait == PortraitId::WakeUp;
    }

    if (*currentPortrait == PortraitId::Sleep && newPortrait == PortraitId::WakeUp)
    {
        return true;
    }

    if ((*currentPortrait >= PortraitId::Cursed && *currentPortrait <= PortraitId::Unconscious)
        && *currentPortrait != PortraitId::Poisoned)
    {
        return isDamagePortrait(newPortrait);
    }

    return true;
}

using OutdoorFaceGeometry = OutdoorFaceGeometryData;

const char *outdoorSupportKindName(OutdoorSupportKind supportKind)
{
    switch (supportKind)
    {
        case OutdoorSupportKind::Terrain:
            return "terrain";
        case OutdoorSupportKind::BModelFace:
            return "bmodel";
        case OutdoorSupportKind::None:
        default:
            return "none";
    }
}

std::vector<std::string> wrapDebugText(const std::string &text, size_t width)
{
    std::vector<std::string> lines;

    if (text.empty())
    {
        lines.push_back({});
        return lines;
    }

    if (width == 0)
    {
        lines.push_back(text);
        return lines;
    }

    size_t lineStart = 0;

    while (lineStart < text.size())
    {
        while (lineStart < text.size() && (text[lineStart] == '\r' || text[lineStart] == '\n'))
        {
            ++lineStart;
        }

        if (lineStart >= text.size())
        {
            break;
        }

        const size_t remaining = text.size() - lineStart;

        if (remaining <= width)
        {
            lines.push_back(text.substr(lineStart));
            break;
        }

        size_t breakPosition = text.rfind(' ', lineStart + width);

        if (breakPosition == std::string::npos || breakPosition < lineStart)
        {
            breakPosition = lineStart + width;
        }

        lines.push_back(text.substr(lineStart, breakPosition - lineStart));
        lineStart = breakPosition;

        while (lineStart < text.size() && text[lineStart] == ' ')
        {
            ++lineStart;
        }
    }

    if (lines.empty())
    {
        lines.push_back(text);
    }

    return lines;
}

std::string buildGameplayHudCharacterLine(const Character &character, bool isLeader)
{
    std::ostringstream stream;
    stream << (isLeader ? "*" : " ")
           << character.name
           << " Lv"
           << character.level
           << " "
           << character.role;
    return stream.str();
}

bool isOutdoorFaceSlopeTooSteep(const OutdoorFaceGeometry &geometry)
{
    if (!geometry.hasPlane)
    {
        return false;
    }

    const float normalZ = std::fabs(geometry.normal.z);

    if (normalZ <= InspectRayEpsilon || normalZ >= OutdoorWalkableNormalZ)
    {
        return false;
    }

    return (geometry.maxZ - geometry.minZ) >= OutdoorMaxStepHeight;
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &vector, float scalar)
{
    return {vector.x * scalar, vector.y * scalar, vector.z * scalar};
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float vecLength(const bx::Vec3 &vector)
{
    return std::sqrt(vecDot(vector, vector));
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

bx::Vec3 vecNormalize(const bx::Vec3 &vector)
{
    const float vectorLength = vecLength(vector);

    if (vectorLength <= InspectRayEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {vector.x / vectorLength, vector.y / vectorLength, vector.z / vectorLength};
}

std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgra(
    const std::vector<uint8_t> &bitmapBytes,
    const std::optional<std::array<uint8_t, 256 * 3>> &overridePalette,
    int &width,
    int &height
)
{
    if (bitmapBytes.empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes.data(), bitmapBytes.size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Palette *pBasePalette = SDL_GetSurfacePalette(pLoadedSurface);
    const bool canApplyPalette =
        overridePalette.has_value()
        && pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8
        && pBasePalette != nullptr;

    if (canApplyPalette)
    {
        width = pLoadedSurface->w;
        height = pLoadedSurface->h;
        std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

        for (int row = 0; row < height; ++row)
        {
            const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels)
                + static_cast<ptrdiff_t>(row * pLoadedSurface->pitch);

            for (int column = 0; column < width; ++column)
            {
                const uint8_t paletteIndex = pSourceRow[column];
                const SDL_Color sourceColor =
                    paletteIndex < pBasePalette->ncolors ? pBasePalette->colors[paletteIndex] : SDL_Color{0, 0, 0, 255};
                const bool isMagentaKey = sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
                const bool isTealKey = sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
                const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                const size_t pixelOffset =
                    (static_cast<size_t>(row) * static_cast<size_t>(width) + static_cast<size_t>(column)) * 4;

                pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
                pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
                pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
                pixels[pixelOffset + 3] = (isMagentaKey || isTealKey) ? 0 : 255;
            }
        }

        SDL_DestroySurface(pLoadedSurface);
        return pixels;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pConvertedSurface->pixels)
            + static_cast<ptrdiff_t>(row * pConvertedSurface->pitch);
        uint8_t *pTargetRow = pixels.data() + static_cast<size_t>(row) * static_cast<size_t>(width) * 4;
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(width) * 4);
    }

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];
        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}
float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY
);

float cross2d(float ax, float ay, float bx, float by)
{
    return ax * by - ay * bx;
}

bool rangesOverlap(float a0, float a1, float b0, float b1)
{
    const float minA = std::min(a0, a1);
    const float maxA = std::max(a0, a1);
    const float minB = std::min(b0, b1);
    const float maxB = std::max(b0, b1);
    return maxA + InspectRayEpsilon >= minB && maxB + InspectRayEpsilon >= minA;
}

bool segmentsIntersect2d(
    float ax,
    float ay,
    float bx,
    float by,
    float cx,
    float cy,
    float dx,
    float dy
)
{
    if (!rangesOverlap(ax, bx, cx, dx) || !rangesOverlap(ay, by, cy, dy))
    {
        return false;
    }

    const float abx = bx - ax;
    const float aby = by - ay;
    const float acx = cx - ax;
    const float acy = cy - ay;
    const float adx = dx - ax;
    const float ady = dy - ay;
    const float cdx = dx - cx;
    const float cdy = dy - cy;
    const float cax = ax - cx;
    const float cay = ay - cy;
    const float cbx = bx - cx;
    const float cby = by - cy;
    const float cross1 = cross2d(abx, aby, acx, acy);
    const float cross2 = cross2d(abx, aby, adx, ady);
    const float cross3 = cross2d(cdx, cdy, cax, cay);
    const float cross4 = cross2d(cdx, cdy, cbx, cby);

    if (((cross1 > InspectRayEpsilon && cross2 < -InspectRayEpsilon)
            || (cross1 < -InspectRayEpsilon && cross2 > InspectRayEpsilon))
        && ((cross3 > InspectRayEpsilon && cross4 < -InspectRayEpsilon)
            || (cross3 < -InspectRayEpsilon && cross4 > InspectRayEpsilon)))
    {
        return true;
    }

    return std::fabs(cross1) <= InspectRayEpsilon
        || std::fabs(cross2) <= InspectRayEpsilon
        || std::fabs(cross3) <= InspectRayEpsilon
        || std::fabs(cross4) <= InspectRayEpsilon;
}

float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY
)
{
    const float segmentX = segmentEndX - segmentStartX;
    const float segmentY = segmentEndY - segmentStartY;
    const float segmentLengthSquared = segmentX * segmentX + segmentY * segmentY;

    if (segmentLengthSquared <= InspectRayEpsilon)
    {
        const float dx = pointX - segmentStartX;
        const float dy = pointY - segmentStartY;
        return dx * dx + dy * dy;
    }

    const float pointProjection =
        ((pointX - segmentStartX) * segmentX + (pointY - segmentStartY) * segmentY) / segmentLengthSquared;
    const float clampedProjection = std::clamp(pointProjection, 0.0f, 1.0f);
    const float closestX = segmentStartX + segmentX * clampedProjection;
    const float closestY = segmentStartY + segmentY * clampedProjection;
    const float dx = pointX - closestX;
    const float dy = pointY - closestY;
    return dx * dx + dy * dy;
}

std::string summarizeLinkedEvent(
    uint16_t eventId,
    const std::optional<HouseTable> &houseTable,
    const std::optional<StrTable> &localStrTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    if (eventId == 0)
    {
        return "-";
    }

    const HouseTable emptyHouseTable = {};
    const HouseTable &resolvedHouseTable = houseTable ? *houseTable : emptyHouseTable;
    const StrTable emptyStrTable = {};
    const StrTable &strTable = localStrTable ? *localStrTable : emptyStrTable;

    if (localEvtProgram)
    {
        const std::optional<std::string> summary = localEvtProgram->summarizeEvent(eventId, strTable, resolvedHouseTable);

        if (summary)
        {
            return "L:" + *summary;
        }
    }

    if (globalEvtProgram)
    {
        const std::optional<std::string> summary = globalEvtProgram->summarizeEvent(eventId, emptyStrTable, resolvedHouseTable);

        if (summary)
        {
            return "G:" + *summary;
        }
    }

    return std::to_string(eventId) + ":unresolved";
}

size_t countChestItemSlots(const MapDeltaChest &chest)
{
    size_t occupiedSlots = 0;

    for (int16_t itemIndex : chest.inventoryMatrix)
    {
        if (itemIndex > 0)
        {
            ++occupiedSlots;
        }
    }

    return occupiedSlots;
}

std::string summarizeLinkedChests(
    uint16_t eventId,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::optional<ChestTable> &chestTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    if (eventId == 0 || !mapDeltaData || !chestTable)
    {
        return {};
    }

    std::vector<uint32_t> chestIds;

    if (localEvtProgram && localEvtProgram->hasEvent(eventId))
    {
        chestIds = localEvtProgram->getOpenedChestIds(eventId);
    }
    else if (globalEvtProgram && globalEvtProgram->hasEvent(eventId))
    {
        chestIds = globalEvtProgram->getOpenedChestIds(eventId);
    }

    if (chestIds.empty())
    {
        return {};
    }

    std::string summary = "Chest:";
    const size_t chestCount = std::min<size_t>(chestIds.size(), 2);

    for (size_t chestIndex = 0; chestIndex < chestCount; ++chestIndex)
    {
        const uint32_t chestId = chestIds[chestIndex];
        summary += " #" + std::to_string(chestId);

        if (chestId >= mapDeltaData->chests.size())
        {
            summary += ":out";
            continue;
        }

        const MapDeltaChest &chest = mapDeltaData->chests[chestId];
        const ChestEntry *pEntry = chestTable->get(chest.chestTypeId);
        summary += ":" + std::to_string(chest.chestTypeId);

        if (pEntry != nullptr && !pEntry->name.empty())
        {
            summary += ":" + pEntry->name;
        }

        std::ostringstream flagsStream;
        flagsStream << std::hex << chest.flags;
        summary += " f=0x" + flagsStream.str();
        summary += " s=" + std::to_string(countChestItemSlots(chest));
    }

    if (chestIds.size() > chestCount)
    {
        summary += " ...";
    }

    return summary;
}

bool intersectRayTriangle(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &vertex0,
    const bx::Vec3 &vertex1,
    const bx::Vec3 &vertex2,
    float &distance
)
{
    const bx::Vec3 edge1 = vecSubtract(vertex1, vertex0);
    const bx::Vec3 edge2 = vecSubtract(vertex2, vertex0);
    const bx::Vec3 pVector = vecCross(rayDirection, edge2);
    const float determinant = vecDot(edge1, pVector);

    if (std::fabs(determinant) <= InspectRayEpsilon)
    {
        return false;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const bx::Vec3 tVector = vecSubtract(rayOrigin, vertex0);
    const float barycentricU = vecDot(tVector, pVector) * inverseDeterminant;

    if (barycentricU < 0.0f || barycentricU > 1.0f)
    {
        return false;
    }

    const bx::Vec3 qVector = vecCross(tVector, edge1);
    const float barycentricV = vecDot(rayDirection, qVector) * inverseDeterminant;

    if (barycentricV < 0.0f || barycentricU + barycentricV > 1.0f)
    {
        return false;
    }

    distance = vecDot(edge2, qVector) * inverseDeterminant;
    return distance > InspectRayEpsilon;
}

bool intersectRayAabb(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &minBounds,
    const bx::Vec3 &maxBounds,
    float &distance
)
{
    float tMin = 0.0f;
    float tMax = std::numeric_limits<float>::max();

    const float rayOriginValues[3] = {rayOrigin.x, rayOrigin.y, rayOrigin.z};
    const float rayDirectionValues[3] = {rayDirection.x, rayDirection.y, rayDirection.z};
    const float minValues[3] = {minBounds.x, minBounds.y, minBounds.z};
    const float maxValues[3] = {maxBounds.x, maxBounds.y, maxBounds.z};

    for (int axis = 0; axis < 3; ++axis)
    {
        if (std::fabs(rayDirectionValues[axis]) <= InspectRayEpsilon)
        {
            if (rayOriginValues[axis] < minValues[axis] || rayOriginValues[axis] > maxValues[axis])
            {
                return false;
            }

            continue;
        }

        const float inverseDirection = 1.0f / rayDirectionValues[axis];
        float t1 = (minValues[axis] - rayOriginValues[axis]) * inverseDirection;
        float t2 = (maxValues[axis] - rayOriginValues[axis]) * inverseDirection;

        if (t1 > t2)
        {
            std::swap(t1, t2);
        }

        tMin = std::max(tMin, t1);
        tMax = std::min(tMax, t2);

        if (tMin > tMax)
        {
            return false;
        }
    }

    distance = tMin;
    return true;
}

std::optional<float> intersectOutdoorTerrainRay(
    const OutdoorMapData &outdoorMapData,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection)
{
    float closestDistance = std::numeric_limits<float>::max();
    bool hasIntersection = false;

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight - 1; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth - 1; ++gridX)
        {
            const size_t topLeftIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + (gridX + 1));
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex =
                static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + (gridX + 1));

            const bx::Vec3 topLeft = {
                static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize),
                static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize),
                static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 topRight = {
                static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize),
                static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize),
                static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 bottomLeft = {
                static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize),
                static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize),
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 bottomRight = {
                static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize),
                static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize),
                static_cast<float>(outdoorMapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale)
            };

            float distance = 0.0f;

            if (intersectRayTriangle(rayOrigin, rayDirection, topLeft, bottomLeft, topRight, distance)
                && distance < closestDistance)
            {
                closestDistance = distance;
                hasIntersection = true;
            }

            if (intersectRayTriangle(rayOrigin, rayDirection, topRight, bottomLeft, bottomRight, distance)
                && distance < closestDistance)
            {
                closestDistance = distance;
                hasIntersection = true;
            }
        }
    }

    if (!hasIntersection)
    {
        return std::nullopt;
    }

    return closestDistance;
}

struct ProjectedPoint
{
    float x = 0.0f;
    float y = 0.0f;
};

bool projectWorldPointToScreen(
    const bx::Vec3 &point,
    int viewWidth,
    int viewHeight,
    const float *pViewProjectionMatrix,
    ProjectedPoint &projectedPoint)
{
    const float x = point.x;
    const float y = point.y;
    const float z = point.z;
    const float clipX =
        x * pViewProjectionMatrix[0] + y * pViewProjectionMatrix[4] + z * pViewProjectionMatrix[8]
        + pViewProjectionMatrix[12];
    const float clipY =
        x * pViewProjectionMatrix[1] + y * pViewProjectionMatrix[5] + z * pViewProjectionMatrix[9]
        + pViewProjectionMatrix[13];
    const float clipW =
        x * pViewProjectionMatrix[3] + y * pViewProjectionMatrix[7] + z * pViewProjectionMatrix[11]
        + pViewProjectionMatrix[15];

    if (std::fabs(clipW) <= InspectRayEpsilon)
    {
        return false;
    }

    const float inverseW = 1.0f / clipW;
    const float ndcX = clipX * inverseW;
    const float ndcY = clipY * inverseW;

    projectedPoint.x = ((ndcX + 1.0f) * 0.5f) * static_cast<float>(viewWidth);
    projectedPoint.y = ((1.0f - ndcY) * 0.5f) * static_cast<float>(viewHeight);
    return true;
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    std::filesystem::path shaderRoot = OPENYAMM_BGFX_SHADER_DIR;

    if (rendererType == bgfx::RendererType::OpenGL)
    {
        return shaderRoot / "glsl" / (std::string(pShaderName) + ".bin");
    }

    if (rendererType == bgfx::RendererType::Noop)
    {
        return {};
    }

    return {};
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream inputStream(path, std::ios::binary);

    if (!inputStream)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(inputStream), std::istreambuf_iterator<char>());
}

}

bgfx::VertexLayout OutdoorGameView::TerrainVertex::ms_layout;
bgfx::VertexLayout OutdoorGameView::TexturedTerrainVertex::ms_layout;

OutdoorGameView::OutdoorGameView()
    : m_isInitialized(false)
    , m_isRenderable(false)
    , m_outdoorMapData(std::nullopt)
    , m_vertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_indexBufferHandle(BGFX_INVALID_HANDLE)
    , m_skyVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_texturedTerrainVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_filledTerrainVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bmodelVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bmodelCollisionVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_entityMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_spawnMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_programHandle(BGFX_INVALID_HANDLE)
    , m_texturedTerrainProgramHandle(BGFX_INVALID_HANDLE)
    , m_terrainTextureAtlasHandle(BGFX_INVALID_HANDLE)
    , m_terrainTextureSamplerHandle(BGFX_INVALID_HANDLE)
    , m_elapsedTime(0.0f)
    , m_framesPerSecond(0.0f)
    , m_bmodelLineVertexCount(0)
    , m_bmodelCollisionVertexCount(0)
    , m_bmodelFaceCount(0)
    , m_entityMarkerVertexCount(0)
    , m_spawnMarkerVertexCount(0)
    , m_cameraTargetX(-80000.0f)
    , m_cameraTargetY(0.0f)
    , m_cameraTargetZ(28000.0f)
    , m_cameraYawRadians(0.0f)
    , m_cameraPitchRadians(0.30f)
    , m_cameraEyeHeight(176.0f)
    , m_cameraDistance(0.0f)
    , m_cameraOrthoScale(1.2f)
    , m_showFilledTerrain(true)
    , m_showTerrainWireframe(false)
    , m_showBModels(true)
    , m_showBModelWireframe(true)
    , m_showBModelCollisionFaces(false)
    , m_showActorCollisionBoxes(false)
    , m_showDecorationBillboards(true)
    , m_showActors(true)
    , m_showSpriteObjects(true)
    , m_showEntities(true)
    , m_showSpawns(false)
    , m_showGameplayHud(true)
    , m_showDebugHud(false)
    , m_inspectMode(true)
    , m_isRotatingCamera(false)
    , m_lastMouseX(0.0f)
    , m_lastMouseY(0.0f)
    , m_toggleFilledLatch(false)
    , m_toggleWireframeLatch(false)
    , m_toggleBModelsLatch(false)
    , m_toggleBModelWireframeLatch(false)
    , m_toggleBModelCollisionFacesLatch(false)
    , m_toggleActorCollisionBoxesLatch(false)
    , m_toggleDecorationBillboardsLatch(false)
    , m_toggleActorsLatch(false)
    , m_toggleSpriteObjectsLatch(false)
    , m_toggleEntitiesLatch(false)
    , m_toggleSpawnsLatch(false)
    , m_toggleGameplayHudLatch(false)
    , m_toggleDebugHudLatch(false)
    , m_toggleInspectLatch(false)
    , m_triggerMeteorLatch(false)
    , m_debugDialogueLatch(false)
    , m_keyboardUseLatch(false)
    , m_activateInspectLatch(false)
    , m_inspectMouseActivateLatch(false)
    , m_attackInspectLatch(false)
    , m_toggleRunningLatch(false)
    , m_toggleFlyingLatch(false)
    , m_toggleWaterWalkLatch(false)
    , m_toggleFeatherFallLatch(false)
    , m_quickSpellCastLatch(false)
    , m_spellbookToggleLatch(false)
    , m_spellbookClickLatch(false)
    , m_pendingSpellTargetClickLatch(false)
    , m_inventoryScreenToggleLatch(false)
    , m_adventurersInnToggleLatch(false)
    , m_gameplayUiController()
    , m_characterScreenOpen(m_gameplayUiController.characterScreen().open)
    , m_characterDollJewelryOverlayOpen(m_gameplayUiController.characterScreen().dollJewelryOverlayOpen)
    , m_adventurersInnRosterOverlayOpen(m_gameplayUiController.characterScreen().adventurersInnRosterOverlayOpen)
    , m_characterPage(m_gameplayUiController.characterScreen().page)
    , m_characterScreenSource(m_gameplayUiController.characterScreen().source)
    , m_characterScreenSourceIndex(m_gameplayUiController.characterScreen().sourceIndex)
    , m_adventurersInnScrollOffset(m_gameplayUiController.characterScreen().adventurersInnScrollOffset)
    , m_characterClickLatch(false)
    , m_characterMemberCycleLatch(false)
    , m_characterPressedTarget({})
    , m_partyPortraitClickLatch(false)
    , m_partyPortraitPressedIndex(std::nullopt)
    , m_lastPartyPortraitClickTicks(0)
    , m_lastPartyPortraitClickedIndex(std::nullopt)
    , m_lastAdventurersInnPortraitClickTicks(0)
    , m_lastAdventurersInnPortraitClickedIndex(std::nullopt)
    , m_pendingCharacterDismissMemberIndex(std::nullopt)
    , m_pendingCharacterDismissExpiresTicks(0)
    , m_heldInventoryItem(m_gameplayUiController.heldInventoryItem())
    , m_itemInspectOverlay(m_gameplayUiController.itemInspectOverlay())
    , m_itemInspectInteractionLatch(false)
    , m_itemInspectInteractionKey(0)
    , m_characterInspectOverlay(m_gameplayUiController.characterInspectOverlay())
    , m_buffInspectOverlay(m_gameplayUiController.buffInspectOverlay())
    , m_characterDetailOverlay(m_gameplayUiController.characterDetailOverlay())
    , m_actorInspectOverlay(m_gameplayUiController.actorInspectOverlay())
    , m_spellInspectOverlay(m_gameplayUiController.spellInspectOverlay())
    , m_readableScrollOverlay(m_gameplayUiController.readableScrollOverlay())
    , m_spellbook(m_gameplayUiController.spellbook())
    , m_inventoryNestedOverlay(m_gameplayUiController.inventoryNestedOverlay())
    , m_houseShopOverlay(m_gameplayUiController.houseShopOverlay())
    , m_houseBankState(m_gameplayUiController.houseBankState())
    , m_spellbookPressedTarget({})
    , m_lastSpellbookSpellClickTicks(0)
    , m_lastSpellbookClickedSpellId(0)
    , m_pendingSpellCast({})
    , m_heldInventoryDropLatch(false)
    , m_closeOverlayLatch(false)
    , m_dialogueClickLatch(false)
    , m_houseShopClickLatch(false)
    , m_houseShopPressedSlotIndex(std::numeric_limits<size_t>::max())
    , m_chestItemClickLatch(false)
    , m_dialoguePressedTarget({})
    , m_chestClickLatch(false)
    , m_chestPressedTarget({})
    , m_inventoryNestedOverlayClickLatch(false)
    , m_inventoryNestedOverlayItemClickLatch(false)
    , m_inventoryNestedOverlayPressedTarget({})
    , m_houseBankDigitLatches({})
    , m_houseBankBackspaceLatch(false)
    , m_houseBankConfirmLatch(false)
    , m_lootChestItemLatch(false)
    , m_chestSelectUpLatch(false)
    , m_chestSelectDownLatch(false)
    , m_eventDialogSelectUpLatch(false)
    , m_eventDialogSelectDownLatch(false)
    , m_eventDialogAcceptLatch(false)
    , m_eventDialogPartySelectLatches({})
    , m_chestSelectionIndex(0)
    , m_eventDialogSelectionIndex(m_gameplayUiController.eventDialog().selectionIndex)
    , m_statusBarHoverText(m_gameplayUiController.statusBar().hoverText)
    , m_statusBarEventText(m_gameplayUiController.statusBar().eventText)
    , m_statusBarEventRemainingSeconds(m_gameplayUiController.statusBar().eventRemainingSeconds)
    , m_cachedHoverInspectHitValid(false)
    , m_lastHoverInspectUpdateNanoseconds(0)
    , m_cachedHoverInspectHit({})
    , m_activeEventDialog(m_gameplayUiController.eventDialog().content)
    , m_pOutdoorPartyRuntime(nullptr)
    , m_pAssetFileSystem(nullptr)
    , m_pOutdoorSceneRuntime(nullptr)
    , m_pOutdoorWorldRuntime(nullptr)
    , m_pItemTable(nullptr)
    , m_pStandardItemEnchantTable(nullptr)
    , m_pSpecialItemEnchantTable(nullptr)
    , m_pItemEquipPosTable(nullptr)
    , m_pRosterTable(nullptr)
    , m_pArcomageLibrary(nullptr)
    , m_pCharacterDollTable(nullptr)
    , m_pObjectTable(nullptr)
    , m_pSpellTable(nullptr)
    , m_pReadableScrollTable(nullptr)
    , m_pGameAudioSystem(nullptr)
    , m_nextPendingSpriteFrameWarmupIndex(0)
    , m_runtimeActorBillboardTexturesQueuedCount(0)
    , m_lastFootstepX(0.0f)
    , m_lastFootstepY(0.0f)
    , m_hasLastFootstepPosition(false)
    , m_walkingMotionHoldSeconds(0.0f)
    , m_activeWalkingSoundId(std::nullopt)
    , m_activeHouseAudioHostId(0)
{
    m_eventDialogPartySelectLatches.fill(false);
    m_houseBankDigitLatches.fill(false);
}

OutdoorGameView::~OutdoorGameView()
{
    shutdown();
}

bool OutdoorGameView::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<std::vector<uint32_t>> &outdoorTileColors,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet,
    const std::optional<DecorationBillboardSet> &outdoorDecorationBillboardSet,
    const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
    const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const ChestTable &chestTable,
    const HouseTable &houseTable,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    const RosterTable &rosterTable,
    const ArcomageLibrary &arcomageLibrary,
    const CharacterDollTable &characterDollTable,
    const CharacterInspectTable &characterInspectTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    const ReadableScrollTable &readableScrollTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const ItemEquipPosTable &itemEquipPosTable,
    const std::optional<StrTable> &localStrTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram,
    GameAudioSystem *pGameAudioSystem,
    OutdoorSceneRuntime &sceneRuntime
)
{
    shutdown();

    m_isInitialized = true;
    m_pAssetFileSystem = &assetFileSystem;
    m_houseVideoPlayer.initialize();
    m_map = map;
    m_monsterTable = monsterTable;
    m_outdoorMapData = outdoorMapData;
    m_outdoorDecorationBillboardSet = outdoorDecorationBillboardSet;
    m_outdoorActorPreviewBillboardSet = outdoorActorPreviewBillboardSet;
    m_outdoorSpriteObjectBillboardSet = outdoorSpriteObjectBillboardSet;
    m_outdoorMapDeltaData = outdoorMapDeltaData;
    m_chestTable = chestTable;
    m_houseTable = houseTable;
    m_classSkillTable = classSkillTable;
    m_npcDialogTable = npcDialogTable;
    m_characterInspectTable = characterInspectTable;
    m_pRosterTable = &rosterTable;
    m_pArcomageLibrary = &arcomageLibrary;
    m_pCharacterDollTable = &characterDollTable;
    m_pObjectTable = &objectTable;
    m_pSpellTable = &spellTable;
    m_pReadableScrollTable = &readableScrollTable;
    m_pGameAudioSystem = pGameAudioSystem;
    m_pItemTable = &itemTable;
    m_pStandardItemEnchantTable = &standardItemEnchantTable;
    m_pSpecialItemEnchantTable = &specialItemEnchantTable;
    m_pItemEquipPosTable = &itemEquipPosTable;
    m_localStrTable = localStrTable;
    m_localEvtProgram = localEvtProgram;
    m_globalEvtProgram = globalEvtProgram;
    m_pOutdoorSceneRuntime = &sceneRuntime;
    m_pOutdoorPartyRuntime = &sceneRuntime.partyRuntime();
    m_pOutdoorWorldRuntime = &sceneRuntime.worldRuntime();
    m_portraitSpellFxStates.assign(5, {});

    if (!loadPortraitAnimationData(assetFileSystem))
    {
        std::cout << "HUD portrait animation load failed\n";
    }

    if (!loadPortraitFxData(assetFileSystem))
    {
        std::cout << "HUD portrait FX load failed\n";
    }

    OutdoorInteractionController::rebuildInteractiveDecorationBindings(*this);
    OutdoorInteractionController::seedInteractiveDecorationRuntimeStateIfNeeded(*this);
    OutdoorInteractionController::buildDecorationBillboardSpatialIndex(*this);

    const int centerGridX = OutdoorMapData::TerrainWidth / 2;
    const int centerGridY = OutdoorMapData::TerrainHeight / 2;
    const size_t centerSampleIndex =
        static_cast<size_t>(centerGridY * OutdoorMapData::TerrainWidth + centerGridX);
    const float centerHeightWorld =
        static_cast<float>(outdoorMapData.heightMap[centerSampleIndex] * OutdoorMapData::TerrainHeightScale);
    float initialX = 0.0f;
    float initialY = 0.0f;
    float initialFootZ = centerHeightWorld;

    if (const std::optional<OutdoorPartyStartPoint> startPoint =
            resolveOutdoorPartyStartPoint(assetFileSystem, outdoorMapData))
    {
        initialX = startPoint->x;
        initialY = startPoint->y;
        initialFootZ = startPoint->z;
    }

    m_cameraTargetX = initialX;
    m_cameraTargetY = initialY;
    if (m_pOutdoorPartyRuntime)
    {
        m_pOutdoorPartyRuntime->initialize(m_cameraTargetX, m_cameraTargetY, initialFootZ, false);
        m_cameraTargetZ = m_pOutdoorPartyRuntime->movementState().footZ + m_cameraEyeHeight;
        m_lastFootstepX = m_pOutdoorPartyRuntime->movementState().x;
        m_lastFootstepY = m_pOutdoorPartyRuntime->movementState().y;
        m_hasLastFootstepPosition = true;
    }
    else
    {
        m_cameraTargetZ = initialFootZ + m_cameraEyeHeight;
    }
    m_cameraYawRadians = -Pi * 0.5f;
    m_cameraPitchRadians = -0.15f;
    m_cameraDistance = 0.0f;
    m_cameraOrthoScale = 1.2f;

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    if (!OutdoorRenderer::initializeWorldRenderResources(
            *this,
            outdoorMapData,
            outdoorTileColors,
            outdoorTerrainTextureAtlas,
            outdoorBModelTextureSet))
    {
        return false;
    }

    OutdoorBillboardRenderer::initializeBillboardResources(*this);

    if (!HudUiService::loadHudLayout(*this, assetFileSystem))
    {
        std::cerr << "OutdoorGameView failed to load HUD layout data from Data/ui/gameplay/*.yml\n";
    }
    else
    {
            for (const auto &[id, element] : m_uiLayoutManager.elements())
            {
                BX_UNUSED(id);
                for (const std::string *pAssetName : {
                     &element.primaryAsset,
                     &element.hoverAsset,
                     &element.pressedAsset,
                     &element.secondaryAsset,
                     &element.tertiaryAsset,
                     &element.quaternaryAsset,
                     &element.quinaryAsset})
            {
                if (!pAssetName->empty())
                {
                    loadHudTexture(assetFileSystem, *pAssetName);
                }
            }

            if (!element.fontName.empty())
            {
                if (!loadHudFont(assetFileSystem, element.fontName))
                {
                    std::cout << "HUD font preload failed: font=\"" << element.fontName
                              << "\" element=\"" << element.id << "\"\n";
                }
            }
        }
    }

    m_terrainTextureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);

    if (!bgfx::isValid(m_vertexBufferHandle) || !bgfx::isValid(m_indexBufferHandle) || !bgfx::isValid(m_programHandle))
    {
        std::cerr << "OutdoorGameView failed to create bgfx resources.\n";
        shutdown();
        return false;
    }

    if (m_houseTable.has_value())
    {
        const std::vector<std::string> relevantHouseVideoStems = collectRelevantHouseVideoStemsForMap(
            outdoorMapData,
            m_pOutdoorSceneRuntime != nullptr
                ? m_pOutdoorSceneRuntime->localEventIrProgram()
                : std::nullopt,
            m_pOutdoorSceneRuntime != nullptr
                ? m_pOutdoorSceneRuntime->globalEventIrProgram()
                : std::nullopt,
            *m_houseTable);

        for (const std::string &videoStem : relevantHouseVideoStems)
        {
            m_houseVideoPlayer.queueBackgroundPreload(videoStem);
        }
    }

    m_isRenderable = true;
    return true;
}

void OutdoorGameView::render(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    if (!m_isInitialized)
    {
        return;
    }

    if (deltaSeconds > 0.0f)
    {
        m_elapsedTime += deltaSeconds;
    }

    const uint64_t renderStartTickCount = SDL_GetTicksNS();
    uint64_t cameraStageNanoseconds = 0;
    uint64_t inspectStageNanoseconds = 0;
    uint64_t terrainStageNanoseconds = 0;
    uint64_t bmodelStageNanoseconds = 0;
    uint64_t decorationStageNanoseconds = 0;
    uint64_t actorStageNanoseconds = 0;
    uint64_t spriteStageNanoseconds = 0;
    uint64_t spawnStageNanoseconds = 0;
    uint64_t debugTextStageNanoseconds = 0;
    uint64_t hudStageNanoseconds = 0;

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState =
        m_pOutdoorWorldRuntime != nullptr ? &m_pOutdoorWorldRuntime->atmosphereState() : nullptr;
    const uint32_t clearColorAbgr = pAtmosphereState != nullptr ? pAtmosphereState->clearColorAbgr : 0x000000ffu;
    const float farClipDistance = pAtmosphereState != nullptr
        ? std::clamp(pAtmosphereState->visibilityDistance, 4096.0f, DefaultOutdoorFarClip)
        : DefaultOutdoorFarClip;

    bgfx::setViewRect(SkyViewId, 0, 0, viewWidth, viewHeight);
    bgfx::setViewClear(SkyViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, clearColorAbgr, 1.0f, 0);
    bgfx::setViewRect(MainViewId, 0, 0, viewWidth, viewHeight);
    bgfx::setViewClear(MainViewId, BGFX_CLEAR_DEPTH, 0, 1.0f, 0);

    if (!m_isRenderable)
    {
        bgfx::touch(SkyViewId);
        bgfx::touch(MainViewId);
        bgfx::dbgTextClear();
        bgfx::dbgTextPrintf(0, 1, 0x0f, "bgfx noop renderer active");
        return;
    }

    updateStatusBarEvent(deltaSeconds);
    updatePartyPortraitAnimations(deltaSeconds);

    if (m_pAssetFileSystem != nullptr)
    {
        m_houseVideoPlayer.updateBackgroundPreloads(*m_pAssetFileSystem);
    }

    updateHouseVideoPlayback(deltaSeconds);
    updateItemInspectOverlayState(width, height);
    updateCharacterInspectOverlayState(width, height);
    updateBuffInspectOverlayState(width, height);
    updateCharacterDetailOverlayState(width, height);
    updateActorInspectOverlayState(width, height);
    updateSpellInspectOverlayState(width, height);
    m_renderedInspectableHudItems.clear();
    m_renderedInspectableHudState = currentHudScreenState();

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        updateCameraFromInput(deltaSeconds);
        cameraStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    OutdoorBillboardRenderer::queueRuntimeActorBillboardTextureWarmup(*this);
    OutdoorBillboardRenderer::processPendingSpriteFrameWarmups(*this, 1);

    const bool hasActiveLootView =
        m_pOutdoorWorldRuntime != nullptr
        && (m_pOutdoorWorldRuntime->activeChestView() != nullptr || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);
    const bool isEventDialogActive = hasActiveEventDialog();
    const bool isCharacterScreenActive = m_characterScreenOpen;
    const bool isSpellbookActive = m_spellbook.active;

    const float wireframeAspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);

    float wireframeViewMatrix[16] = {};
    float wireframeProjectionMatrix[16] = {};

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 wireframeEye = {
        m_cameraTargetX,
        m_cameraTargetY,
        m_cameraTargetZ
    };
    const bx::Vec3 wireframeAt = {
        m_cameraTargetX + cosYaw * cosPitch,
        m_cameraTargetY - sinYaw * cosPitch,
        m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 wireframeUp = {0.0f, 0.0f, 1.0f};
    bx::mtxLookAt(wireframeViewMatrix, wireframeEye, wireframeAt, wireframeUp);
    bx::mtxProj(
        wireframeProjectionMatrix,
        CameraVerticalFovDegrees,
        wireframeAspectRatio,
        0.1f,
        farClipDistance,
        bgfx::getCaps()->homogeneousDepth
    );

    const bx::Vec3 cameraForward = vecNormalize(vecSubtract(wireframeAt, wireframeEye));
    const bx::Vec3 cameraRight = vecNormalize(bx::cross(cameraForward, wireframeUp));
    const bx::Vec3 cameraUp = vecNormalize(bx::cross(cameraRight, cameraForward));

    bgfx::setViewTransform(SkyViewId, wireframeViewMatrix, wireframeProjectionMatrix);
    bgfx::touch(SkyViewId);
    bgfx::setViewTransform(MainViewId, wireframeViewMatrix, wireframeProjectionMatrix);
    bgfx::touch(MainViewId);

    InspectHit inspectHit = {};
    float mouseX = 0.0f;
    float mouseY = 0.0f;

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
        const auto buildInspectRayForScreenPoint =
            [&](float screenX, float screenY, bx::Vec3 &rayOrigin, bx::Vec3 &rayDirection) -> bool
            {
                if (viewWidth <= 0 || viewHeight <= 0)
                {
                    return false;
                }

                const float normalizedX =
                    ((screenX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
                const float normalizedY =
                    1.0f - ((screenY / static_cast<float>(viewHeight)) * 2.0f);
                float viewProjectionMatrix[16] = {};
                float inverseViewProjectionMatrix[16] = {};
                bx::mtxMul(viewProjectionMatrix, wireframeViewMatrix, wireframeProjectionMatrix);
                bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
                rayOrigin = bx::mulH({normalizedX, normalizedY, 0.0f}, inverseViewProjectionMatrix);
                const bx::Vec3 rayTarget = bx::mulH({normalizedX, normalizedY, 1.0f}, inverseViewProjectionMatrix);
                rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
                return vecLength(rayDirection) > InspectRayEpsilon;
            };

        if (!hasActiveLootView && !isEventDialogActive && !isCharacterScreenActive && !isSpellbookActive)
        {
            if (m_pendingSpellCast.active)
            {
                const bool closePressed =
                    pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

                if (closePressed)
                {
                    if (!m_closeOverlayLatch)
                    {
                        clearPendingSpellCast("Spell canceled");
                        m_closeOverlayLatch = true;
                    }
                }
                else
                {
                    m_closeOverlayLatch = false;
                }

                SDL_GetMouseState(&mouseX, &mouseY);
                const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(nullptr, nullptr);
                const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

                if (isLeftMousePressed)
                {
                    if (!m_pendingSpellTargetClickLatch)
                    {
                        m_pendingSpellTargetClickLatch = true;
                    }
                }
                else if (m_pendingSpellTargetClickLatch)
                {
                    const bool isPointerOverPartyPortrait =
                        resolvePartyPortraitIndexAtPoint(width, height, mouseX, mouseY).has_value();
                    InspectHit pendingInspectHit = {};

                    if (!isPointerOverPartyPortrait && m_outdoorMapData.has_value())
                    {
                        bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
                        bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

                        if (buildInspectRayForScreenPoint(mouseX, mouseY, rayOrigin, rayDirection))
                        {
                            pendingInspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
                                *m_outdoorMapData,
                                rayOrigin,
                                rayDirection,
                                mouseX,
                                mouseY,
                                width,
                                height,
                                wireframeViewMatrix,
                                wireframeProjectionMatrix,
                                OutdoorGameView::DecorationPickMode::Interaction);
                        }
                    }

                    if (!isPointerOverPartyPortrait && tryResolvePendingSpellCast(pendingInspectHit, std::nullopt))
                    {
                        m_cachedHoverInspectHitValid = false;
                        m_cachedHoverInspectHit = {};
                    }

                    m_pendingSpellTargetClickLatch = false;
                }

                m_keyboardUseLatch = false;
                m_heldInventoryDropLatch = false;
                m_activateInspectLatch = false;
                m_inspectMouseActivateLatch = false;
                m_attackInspectLatch = false;
                m_pressedInspectHit = {};
            }
            else
            {
                const bool isKeyboardUsePressed =
                    pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_SPACE];

                if (isKeyboardUsePressed)
                {
                    if (!m_keyboardUseLatch && m_outdoorMapData.has_value())
                    {
                        const float centerX = static_cast<float>(width) * 0.5f;
                        const float centerY = static_cast<float>(height) * 0.5f;
                        bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
                        bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

                        if (buildInspectRayForScreenPoint(centerX, centerY, rayOrigin, rayDirection))
                        {
                            const InspectHit keyboardUseInspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
                                *m_outdoorMapData,
                                rayOrigin,
                                rayDirection,
                                centerX,
                                centerY,
                                width,
                                height,
                                wireframeViewMatrix,
                                wireframeProjectionMatrix,
                                OutdoorGameView::DecorationPickMode::Interaction);

                            const bool canActivate = OutdoorInteractionController::canActivateInspectEvent(*this, keyboardUseInspectHit);
                            std::cout << "Keyboard use target: hit="
                                      << (keyboardUseInspectHit.hasHit ? "yes" : "no")
                                      << " kind=" << (keyboardUseInspectHit.hasHit ? keyboardUseInspectHit.kind : "-")
                                      << " name=" << (keyboardUseInspectHit.hasHit ? keyboardUseInspectHit.name : "-")
                                      << " dist=" << (keyboardUseInspectHit.hasHit ? keyboardUseInspectHit.distance : -1.0f)
                                      << " activatable=" << (canActivate ? "yes" : "no") << '\n';

                            bool activated = false;

                            if (canActivate)
                            {
                                activated = OutdoorInteractionController::tryActivateInspectEvent(*this, keyboardUseInspectHit);
                            }

                            std::cout << "Keyboard use result: activated=" << (activated ? "yes" : "no") << '\n';

                            if (activated)
                            {
                                m_cachedHoverInspectHitValid = false;
                                m_cachedHoverInspectHit = {};
                            }
                        }

                        m_keyboardUseLatch = true;
                    }
                }
                else
                {
                    m_keyboardUseLatch = false;
                }
            }
        }
        else
        {
            m_keyboardUseLatch = false;
            m_pendingSpellTargetClickLatch = false;
        }

        if (!m_pendingSpellCast.active
            && m_heldInventoryItem.active
            && !hasActiveLootView
            && !isEventDialogActive
            && !isCharacterScreenActive
            && !isSpellbookActive)
        {
            const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
            const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

            if (isLeftMousePressed)
            {
                if (!m_heldInventoryDropLatch)
                {
                    m_heldInventoryDropLatch = true;
                }
            }
            else if (m_heldInventoryDropLatch)
            {
                const bool isPointerOverPartyPortrait =
                    resolvePartyPortraitIndexAtPoint(width, height, mouseX, mouseY).has_value();
                bool handledInteraction = isPointerOverPartyPortrait;

                if (!handledInteraction && m_outdoorMapData.has_value())
                {
                    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
                    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

                    if (buildInspectRayForScreenPoint(mouseX, mouseY, rayOrigin, rayDirection))
                    {
                        const InspectHit heldItemInspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
                            *m_outdoorMapData,
                            rayOrigin,
                            rayDirection,
                            mouseX,
                            mouseY,
                            width,
                            height,
                            wireframeViewMatrix,
                            wireframeProjectionMatrix,
                            OutdoorGameView::DecorationPickMode::Interaction);

                        if (OutdoorInteractionController::canActivateInspectEvent(*this, heldItemInspectHit)
                            && OutdoorInteractionController::isMouseInteractionInspectHitInRange(*this, heldItemInspectHit))
                        {
                            OutdoorInteractionController::tryActivateInspectEvent(*this, heldItemInspectHit);
                            handledInteraction = true;
                        }
                    }
                }

                if (!handledInteraction)
                {
                    const ItemDefinition *pItemDefinition =
                        m_pItemTable != nullptr ? m_pItemTable->get(m_heldInventoryItem.item.objectDescriptionId) : nullptr;
                    const std::string itemName =
                        pItemDefinition != nullptr && !pItemDefinition->name.empty()
                        ? pItemDefinition->name
                        : "item";

                    if (m_pOutdoorWorldRuntime != nullptr && m_pOutdoorPartyRuntime != nullptr)
                    {
                        const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();

                        if (m_pOutdoorWorldRuntime->spawnWorldItem(
                                m_heldInventoryItem.item,
                                moveState.x,
                                moveState.y,
                                moveState.footZ + m_cameraEyeHeight,
                                m_cameraYawRadians))
                        {
                            setStatusBarEvent("Dropped " + itemName);
                            m_heldInventoryItem = {};
                        }
                        else
                        {
                            setStatusBarEvent("Can't drop " + itemName);
                        }
                    }
                    else
                    {
                        setStatusBarEvent("Can't drop " + itemName);
                    }
                }

                m_heldInventoryDropLatch = false;
            }
        }
        else if (!m_pendingSpellCast.active
                 && m_inspectMode
                 && m_outdoorMapData
                 && !hasActiveLootView
                 && !isEventDialogActive
                 && !isCharacterScreenActive
                 && !isSpellbookActive)
        {
            SDL_GetMouseState(&mouseX, &mouseY);
            bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
            bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

            if (!buildInspectRayForScreenPoint(mouseX, mouseY, rayOrigin, rayDirection))
            {
                rayOrigin = {0.0f, 0.0f, 0.0f};
                rayDirection = {0.0f, 0.0f, 0.0f};
            }
            const auto refreshHoverInspectHit =
                [&]()
                {
                    inspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
                        *m_outdoorMapData,
                        rayOrigin,
                        rayDirection,
                        mouseX,
                        mouseY,
                        width,
                        height,
                        wireframeViewMatrix,
                        wireframeProjectionMatrix,
                        OutdoorGameView::DecorationPickMode::HoverInfo);
                    m_cachedHoverInspectHit = inspectHit;
                    m_cachedHoverInspectHitValid = true;
                    m_lastHoverInspectUpdateNanoseconds = renderStartTickCount;
                };
            const bool shouldRefreshHoverInspect =
                !m_cachedHoverInspectHitValid
                || renderStartTickCount < m_lastHoverInspectUpdateNanoseconds
                || renderStartTickCount - m_lastHoverInspectUpdateNanoseconds >= HoverInspectRefreshNanoseconds;

            if (shouldRefreshHoverInspect)
            {
                refreshHoverInspectHit();
            }
            else
            {
                inspectHit = m_cachedHoverInspectHit;
            }

            const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(nullptr, nullptr);
            const bool isActivationPressed =
                pKeyboardState != nullptr
                && pKeyboardState[SDL_SCANCODE_E]
                && (mouseButtons & SDL_BUTTON_RMASK) == 0;
            const bool isAttackPressed =
                pKeyboardState != nullptr
                && pKeyboardState[SDL_SCANCODE_H]
                && (mouseButtons & SDL_BUTTON_RMASK) == 0;
            const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
            const bool isPointerOverPartyPortrait =
                resolvePartyPortraitIndexAtPoint(width, height, mouseX, mouseY).has_value();
            const bool needsInteractionInspectHit =
                isActivationPressed
                || isAttackPressed
                || isLeftMousePressed
                || m_inspectMouseActivateLatch;
            InspectHit interactionInspectHit = {};
            bool hasInteractionInspectHit = false;
            const auto refreshInteractionInspectHit =
                [&]()
                {
                    interactionInspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
                        *m_outdoorMapData,
                        rayOrigin,
                        rayDirection,
                        mouseX,
                        mouseY,
                        width,
                        height,
                        wireframeViewMatrix,
                        wireframeProjectionMatrix,
                        OutdoorGameView::DecorationPickMode::Interaction);
                    hasInteractionInspectHit = true;
                };
            const auto isSameInspectActivationTarget =
                [](const InspectHit &lhs, const InspectHit &rhs) -> bool
                {
                    return lhs.hasHit
                        && rhs.hasHit
                        && lhs.kind == rhs.kind
                        && lhs.bModelIndex == rhs.bModelIndex
                        && lhs.faceIndex == rhs.faceIndex
                        && lhs.npcId == rhs.npcId
                        && lhs.eventIdPrimary == rhs.eventIdPrimary
                        && lhs.eventIdSecondary == rhs.eventIdSecondary
                        && lhs.specialTrigger == rhs.specialTrigger;
                };

            if (needsInteractionInspectHit)
            {
                refreshInteractionInspectHit();
            }

            if (isActivationPressed && !m_activateInspectLatch)
            {
                if (OutdoorInteractionController::tryActivateInspectEvent(*this, interactionInspectHit))
                {
                    refreshInteractionInspectHit();
                    refreshHoverInspectHit();
                }

                m_activateInspectLatch = true;
            }
            else if (!isActivationPressed)
            {
                m_activateInspectLatch = false;
            }

            if (isLeftMousePressed && !isPointerOverPartyPortrait)
            {
                if (!m_inspectMouseActivateLatch)
                {
                    if (!hasInteractionInspectHit)
                    {
                        refreshInteractionInspectHit();
                    }

                    m_pressedInspectHit = interactionInspectHit;
                    m_inspectMouseActivateLatch = true;
                }
            }
            else if (m_inspectMouseActivateLatch)
            {
                if (!hasInteractionInspectHit)
                {
                    refreshInteractionInspectHit();
                }

                if (!isPointerOverPartyPortrait
                    && isSameInspectActivationTarget(m_pressedInspectHit, interactionInspectHit))
                {
                    if (OutdoorInteractionController::isMouseInteractionInspectHitInRange(*this, interactionInspectHit)
                        && OutdoorInteractionController::tryActivateInspectEvent(*this, interactionInspectHit))
                    {
                        refreshInteractionInspectHit();
                        refreshHoverInspectHit();
                    }
                }

                m_inspectMouseActivateLatch = false;
                m_pressedInspectHit = {};
            }

            if (isAttackPressed && !m_attackInspectLatch)
            {
                if (!hasInteractionInspectHit)
                {
                    refreshInteractionInspectHit();
                }

                if (m_pOutdoorWorldRuntime != nullptr && m_pOutdoorPartyRuntime != nullptr)
                {
                    Party &party = m_pOutdoorPartyRuntime->party();
                    Character *pAttacker = party.activeMember();

                    if (pAttacker == nullptr || !GameMechanics::canSelectInGameplay(*pAttacker))
                    {
                        setStatusBarEvent("Nobody is in condition");
                    }
                    else
                    {
                        const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
                        auto resolveFallbackRangedActorTarget =
                            [&]() -> std::optional<size_t>
                            {
                                if (m_pOutdoorWorldRuntime == nullptr)
                                {
                                    return std::nullopt;
                                }

                                float viewProjectionMatrix[16] = {};
                                bx::mtxMul(viewProjectionMatrix, wireframeViewMatrix, wireframeProjectionMatrix);
                                float bestDistance = std::numeric_limits<float>::max();
                                std::optional<size_t> bestActorIndex;

                                for (size_t actorIndex = 0; actorIndex < m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
                                {
                                    const OutdoorWorldRuntime::MapActorState *pActor =
                                        m_pOutdoorWorldRuntime->mapActorState(actorIndex);

                                    if (pActor == nullptr || pActor->isDead || pActor->isInvisible || !pActor->hostileToParty)
                                    {
                                        continue;
                                    }

                                    const float deltaX = pActor->preciseX - moveState.x;
                                    const float deltaY = pActor->preciseY - moveState.y;
                                    const float deltaZ = pActor->preciseZ - moveState.footZ;
                                    const float distance = std::max(
                                        0.0f,
                                        std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ)
                                            - static_cast<float>(pActor->radius));

                                    if (distance > 5120.0f)
                                    {
                                        continue;
                                    }

                                    const bx::Vec3 projected = bx::mulH(
                                        {
                                            pActor->preciseX,
                                            pActor->preciseY,
                                            pActor->preciseZ + std::max(48.0f, static_cast<float>(pActor->height) * 0.6f)
                                        },
                                        viewProjectionMatrix);

                                    if (projected.z < 0.0f || projected.z > 1.0f
                                        || projected.x < -1.0f || projected.x > 1.0f
                                        || projected.y < -1.0f || projected.y > 1.0f)
                                    {
                                        continue;
                                    }

                                    if (distance < bestDistance)
                                    {
                                        bestDistance = distance;
                                        bestActorIndex = actorIndex;
                                    }
                                }

                                return bestActorIndex;
                            };
                        const bool hasDirectActorHoverTarget = interactionInspectHit.kind == "actor";
                        std::optional<size_t> runtimeActorIndex =
                            hasDirectActorHoverTarget
                                ? resolveRuntimeActorIndexForInspectHit(interactionInspectHit)
                                : std::nullopt;
                        const OutdoorWorldRuntime::MapActorState *pTargetActor =
                            runtimeActorIndex ? m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex) : nullptr;

                        if (pTargetActor != nullptr && (pTargetActor->isDead || pTargetActor->isInvisible))
                        {
                            runtimeActorIndex.reset();
                            pTargetActor = nullptr;
                        }

                        if (!runtimeActorIndex)
                        {
                            runtimeActorIndex = resolveFallbackRangedActorTarget();
                            pTargetActor =
                                runtimeActorIndex ? m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex) : nullptr;
                        }
                        float targetDistance = 0.0f;
                        int targetArmorClass = 0;
                        bool targetInMeleeRange = false;

                        if (pTargetActor != nullptr)
                        {
                            const float deltaX = pTargetActor->preciseX - moveState.x;
                            const float deltaY = pTargetActor->preciseY - moveState.y;
                            const float deltaZ = pTargetActor->preciseZ - moveState.footZ;
                            targetDistance = std::max(
                                0.0f,
                                std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ)
                                    - static_cast<float>(pTargetActor->radius));
                            targetInMeleeRange = targetDistance <= OeCharacterMeleeAttackDistance;
                            targetArmorClass = m_pOutdoorWorldRuntime->effectiveMapActorArmorClass(*runtimeActorIndex);
                        }

                        std::mt19937 rng(
                            static_cast<uint32_t>(SDL_GetTicks())
                            ^ static_cast<uint32_t>((runtimeActorIndex.value_or(0) + 1) * 2654435761u)
                            ^ static_cast<uint32_t>(party.activeMemberIndex() * 40503u));
                        const CharacterAttackProfile attackProfile =
                            GameMechanics::buildCharacterAttackProfile(*pAttacker, m_pItemTable, m_pSpellTable);
                        CharacterAttackResult attack = {};

                        if (attackProfile.hasBlaster && attackProfile.rangedAttackBonus.has_value())
                        {
                            attack.mode = CharacterAttackMode::Blaster;
                        }
                        else if (attackProfile.hasWand && attackProfile.rangedAttackBonus.has_value())
                        {
                            attack.mode = CharacterAttackMode::Wand;
                        }
                        else if (targetInMeleeRange)
                        {
                            attack.mode = CharacterAttackMode::Melee;
                        }
                        else if (attackProfile.hasBow && attackProfile.rangedAttackBonus.has_value())
                        {
                            attack.mode = CharacterAttackMode::Bow;
                        }
                        else
                        {
                            attack.mode = CharacterAttackMode::Melee;
                        }

                        if (attack.mode == CharacterAttackMode::Melee && pTargetActor != nullptr && targetInMeleeRange)
                        {
                            attack = GameMechanics::resolveCharacterAttackAgainstArmorClass(
                                *pAttacker,
                                m_pItemTable,
                                m_pSpellTable,
                                targetArmorClass,
                                targetDistance,
                                rng);
                        }
                        else if (attack.mode == CharacterAttackMode::Melee)
                        {
                            attack.canAttack = true;
                            attack.hit = false;
                            attack.attackBonus = attackProfile.meleeAttackBonus;
                            attack.recoverySeconds = attackProfile.meleeRecoverySeconds;
                            attack.attackSoundHook = "melee_swing";
                            attack.voiceHook = "attack";
                        }
                        else
                        {
                            attack.canAttack = attackProfile.rangedAttackBonus.has_value();
                            attack.hit = false;
                            attack.resolvesOnImpact = true;
                            attack.attackBonus = attackProfile.rangedAttackBonus.value_or(attackProfile.meleeAttackBonus);
                            attack.recoverySeconds = attackProfile.rangedRecoverySeconds;
                            attack.skillLevel = attackProfile.rangedSkillLevel;
                            attack.skillMastery = attackProfile.rangedSkillMastery;
                            attack.spellId = attackProfile.wandSpellId;
                            attack.attackSoundHook =
                                attack.mode == CharacterAttackMode::Bow
                                    ? "bow_shot"
                                    : (attack.mode == CharacterAttackMode::Blaster ? "blaster_shot" : "wand_cast");
                            attack.voiceHook = "attack";

                            if (attack.canAttack)
                            {
                                const int minimumDamage = attackProfile.rangedMinDamage;
                                const int maximumDamage = std::max(attackProfile.rangedMinDamage, attackProfile.rangedMaxDamage);
                                attack.damage =
                                    std::uniform_int_distribution<int>(minimumDamage, maximumDamage)(rng);
                            }
                        }

                        bool actionPerformed = false;
                        bool attacked = false;
                        bool killed = false;
                        const bool hadMeleeTarget =
                            runtimeActorIndex.has_value() && pTargetActor != nullptr && targetInMeleeRange;

                        if (attack.mode == CharacterAttackMode::Melee)
                        {
                            actionPerformed = attack.canAttack;

                            if (runtimeActorIndex && pTargetActor != nullptr && targetInMeleeRange
                                && attack.hit && attack.damage > 0)
                            {
                                int appliedDamage = attack.damage;

                                if (m_monsterTable.has_value() && m_pItemTable != nullptr)
                                {
                                    const MonsterTable::MonsterStatsEntry *pStats =
                                        m_monsterTable->findStatsById(pTargetActor->monsterId);

                                    if (pStats != nullptr)
                                    {
                                        const int multiplier =
                                            ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
                                                *pAttacker,
                                                CharacterAttackMode::Melee,
                                                m_pItemTable,
                                                m_pSpecialItemEnchantTable,
                                                pStats->name,
                                                pStats->pictureName);
                                        appliedDamage *= multiplier;
                                    }
                                }

                                const int beforeHp = pTargetActor->currentHp;
                                attacked = m_pOutdoorWorldRuntime->applyPartyAttackToMapActor(
                                    *runtimeActorIndex,
                                    appliedDamage,
                                    moveState.x,
                                    moveState.y,
                                    moveState.footZ);

                                if (attacked)
                                {
                                    const OutdoorWorldRuntime::MapActorState *pAfterActor =
                                        m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex);
                                    killed = pAfterActor != nullptr && beforeHp > 0 && pAfterActor->currentHp <= 0;

                                    if (pAttacker->vampiricHealFraction > 0.0f && appliedDamage > 0)
                                    {
                                        party.healMember(
                                            party.activeMemberIndex(),
                                            std::max(1, static_cast<int>(std::round(
                                                static_cast<float>(appliedDamage) * pAttacker->vampiricHealFraction))));
                                    }

                                    refreshInteractionInspectHit();
                                    refreshHoverInspectHit();
                                }
                            }
                        }
                        else if (attack.canAttack)
                        {
                            const float sourceX = moveState.x;
                            const float sourceY = moveState.y;
                            const float sourceZ = moveState.footZ + 96.0f;
                            bx::Vec3 rangedTarget = {
                                sourceX + std::cos(m_cameraYawRadians) * 5120.0f,
                                sourceY - std::sin(m_cameraYawRadians) * 5120.0f,
                                sourceZ + std::sin(m_cameraPitchRadians) * 5120.0f
                            };

                            if (pTargetActor != nullptr)
                            {
                                rangedTarget = {
                                    pTargetActor->preciseX,
                                    pTargetActor->preciseY,
                                    pTargetActor->preciseZ + std::max(48.0f, static_cast<float>(pTargetActor->height) * 0.6f)
                                };
                            }
                            else if (vecLength(rayDirection) > InspectRayEpsilon)
                            {
                                rangedTarget = {
                                    rayOrigin.x + rayDirection.x * 5120.0f,
                                    rayOrigin.y + rayDirection.y * 5120.0f,
                                    rayOrigin.z + rayDirection.z * 5120.0f
                                };
                            }

                            if (attack.mode == CharacterAttackMode::Wand && attack.spellId > 0)
                            {
                                OutdoorWorldRuntime::SpellCastRequest request = {};
                                request.sourceKind = OutdoorWorldRuntime::RuntimeSpellSourceKind::Party;
                                request.sourceId = static_cast<uint32_t>(party.activeMemberIndex() + 1);
                                request.sourcePartyMemberIndex = static_cast<uint32_t>(party.activeMemberIndex());
                                request.ability = OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
                                request.spellId = static_cast<uint32_t>(attack.spellId);
                                request.skillLevel = attack.skillLevel;
                                request.skillMastery = attack.skillMastery;
                                request.damage = attack.damage;
                                request.attackBonus = attack.attackBonus;
                                request.useActorHitChance = true;
                                request.sourceX = sourceX;
                                request.sourceY = sourceY;
                                request.sourceZ = sourceZ;
                                request.targetX = rangedTarget.x;
                                request.targetY = rangedTarget.y;
                                request.targetZ = rangedTarget.z;
                                attacked = m_pOutdoorWorldRuntime->castPartySpell(request);
                            }
                            else
                            {
                                OutdoorWorldRuntime::PartyProjectileRequest request = {};
                                request.sourcePartyMemberIndex = static_cast<uint32_t>(party.activeMemberIndex());
                                request.objectId =
                                    attack.mode == CharacterAttackMode::Blaster
                                        ? OeBlasterProjectileObjectId
                                        : OeArrowProjectileObjectId;
                                request.damage = attack.damage;
                                request.attackBonus = attack.attackBonus;
                                request.useActorHitChance = true;
                                request.sourceX = sourceX;
                                request.sourceY = sourceY;
                                request.sourceZ = sourceZ;
                                request.targetX = rangedTarget.x;
                                request.targetY = rangedTarget.y;
                                request.targetZ = rangedTarget.z;
                                attacked = m_pOutdoorWorldRuntime->spawnPartyProjectile(request);
                            }

                            actionPerformed = attacked;
                        }

                        if (actionPerformed)
                        {
                            if (m_pGameAudioSystem != nullptr)
                            {
                                if (attack.attackSoundHook == "bow_shot")
                                {
                                    m_pGameAudioSystem->playCommonSound(
                                        SoundId::ShootBow,
                                        GameAudioSystem::PlaybackGroup::World,
                                        GameAudioSystem::WorldPosition{moveState.x, moveState.y, moveState.footZ + 96.0f});
                                }
                                else if (attack.attackSoundHook == "blaster_shot")
                                {
                                    m_pGameAudioSystem->playCommonSound(
                                        SoundId::ShootBlaster,
                                        GameAudioSystem::PlaybackGroup::World,
                                        GameAudioSystem::WorldPosition{moveState.x, moveState.y, moveState.footZ + 96.0f});
                                }
                                else if (attack.attackSoundHook == "wand_cast" && attack.spellId > 0)
                                {
                                    // Spell casts route their own release/impact audio through the spell runtime.
                                }
                                else
                                {
                                    m_pGameAudioSystem->playCommonSound(
                                        SoundId::SwingSword01,
                                        GameAudioSystem::PlaybackGroup::World,
                                        GameAudioSystem::WorldPosition{moveState.x, moveState.y, moveState.footZ + 96.0f});
                                }
                            }

                            party.applyRecoveryToActiveMember(attack.recoverySeconds);

                            if (attack.mode == CharacterAttackMode::Melee)
                            {
                                if (hadMeleeTarget)
                                {
                                    SpeechId speechId = attacked && attack.hit ? SpeechId::AttackHit : SpeechId::AttackMiss;

                                    if (killed)
                                    {
                                        speechId = pTargetActor != nullptr && pTargetActor->maxHp >= 100
                                            ? SpeechId::KillStrongEnemy
                                            : SpeechId::KillWeakEnemy;
                                    }

                                    triggerPortraitFaceAnimation(
                                        party.activeMemberIndex(),
                                        attacked && attack.hit ? FaceAnimationId::AttackHit : FaceAnimationId::AttackMiss);
                                    playSpeechReaction(
                                        party.activeMemberIndex(),
                                        speechId,
                                        false);
                                }
                            }
                            else
                            {
                                triggerPortraitFaceAnimation(party.activeMemberIndex(), FaceAnimationId::Shoot);
                                playSpeechReaction(party.activeMemberIndex(), SpeechId::Shoot, false);
                            }

                            party.switchToNextReadyMember();
                        }

                        const std::string attackTargetName =
                            attack.mode == CharacterAttackMode::Melee && !targetInMeleeRange
                                ? std::string()
                                : (pTargetActor != nullptr ? interactionInspectHit.name : std::string());
                        setStatusBarEvent(
                            formatPartyAttackStatusText(
                                pAttacker->name,
                                attackTargetName,
                                attack,
                                killed));

                        if (EventRuntimeState *pEventRuntimeState = m_pOutdoorWorldRuntime->eventRuntimeState())
                        {
                            if (runtimeActorIndex)
                            {
                                pEventRuntimeState->lastActivationResult =
                                    attacked
                                        ? "actor " + std::to_string(*runtimeActorIndex) + " hit by party"
                                        : "actor " + std::to_string(*runtimeActorIndex) + " attacked by party";
                            }
                            else
                            {
                                pEventRuntimeState->lastActivationResult =
                                    actionPerformed ? "party attack released" : "party attack failed";
                            }
                        }

                        std::cout << "Party attack actor="
                                  << (runtimeActorIndex ? std::to_string(*runtimeActorIndex) : std::string("-"))
                                  << " attacker=" << pAttacker->name
                                  << " mode=" << static_cast<int>(attack.mode)
                                  << " can_attack=" << (attack.canAttack ? "yes" : "no")
                                  << " hit=" << (attack.hit ? "yes" : "no")
                                  << " projectile=" << (attack.resolvesOnImpact ? "yes" : "no")
                                  << " damage=" << attack.damage
                                  << " recovery=" << attack.recoverySeconds
                                  << " released=" << (actionPerformed ? "yes" : "no")
                                  << '\n';
                    }
                }

                m_attackInspectLatch = true;
            }
            else if (!isAttackPressed)
            {
                m_attackInspectLatch = false;
            }

            m_statusBarHoverText = OutdoorInteractionController::resolveHoverStatusBarText(*this, inspectHit).value_or("");
        }
        else
        {
            m_heldInventoryDropLatch = false;
            m_activateInspectLatch = false;
            m_inspectMouseActivateLatch = false;
            m_pressedInspectHit = {};
            m_attackInspectLatch = false;
            m_cachedHoverInspectHitValid = false;
            m_lastHoverInspectUpdateNanoseconds = 0;
            m_cachedHoverInspectHit = {};
            m_statusBarHoverText.clear();
        }

        inspectStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    const OutdoorRenderer::WorldPassTimings worldPassTimings =
        OutdoorRenderer::renderWorldPasses(
            *this,
            viewWidth,
            viewHeight,
            wireframeAspectRatio,
            farClipDistance,
            pAtmosphereState,
            wireframeEye,
            cameraForward,
            cameraRight,
            cameraUp,
            wireframeViewMatrix);
    terrainStageNanoseconds += worldPassTimings.terrainNanoseconds;
    bmodelStageNanoseconds += worldPassTimings.bmodelNanoseconds;
    decorationStageNanoseconds += worldPassTimings.decorationNanoseconds;
    actorStageNanoseconds += worldPassTimings.actorNanoseconds;
    spriteStageNanoseconds += worldPassTimings.spriteNanoseconds;
    spawnStageNanoseconds += worldPassTimings.spawnNanoseconds;

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        bgfx::dbgTextClear();

        int nextHudLine = 1;

        if (m_showDebugHud)
        {
        bgfx::dbgTextPrintf(0, 1, 0x0f, "Terrain debug renderer");
        bgfx::dbgTextPrintf(0, 2, 0x0f, "FPS: %.1f", m_framesPerSecond);
        bgfx::dbgTextPrintf(
            0,
            3,
            0x0f,
            "Terrain vertices: %d",
            OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight
        );
        bgfx::dbgTextPrintf(0, 4, 0x0f, "BModels: %u", m_bmodelFaceCount);
        bgfx::dbgTextPrintf(
            0,
            5,
            0x0f,
            "Modes: 1 filled=%s  2 wire=%s  3 bmodels=%s  4 bmwire=%s  5 coll=%s  6 actorcoll=%s  7 actors=%s  8 objs=%s  9 ents=%s  0 spawns=%s  -=inspect=%s  F2 debug=%s  F3 decor=%s  F4 hud=%s  F5 ston  textured=%s/%s",
            m_showFilledTerrain ? "on" : "off",
            m_showTerrainWireframe ? "on" : "off",
            m_showBModels ? "on" : "off",
            m_showBModelWireframe ? "on" : "off",
            m_showBModelCollisionFaces ? "on" : "off",
            m_showActorCollisionBoxes ? "on" : "off",
            m_showActors ? "on" : "off",
            m_showSpriteObjects ? "on" : "off",
            m_showEntities ? "on" : "off",
            m_showSpawns ? "on" : "off",
            m_inspectMode ? "on" : "off",
            m_showDebugHud ? "on" : "off",
            m_showDecorationBillboards ? "on" : "off",
            m_showGameplayHud ? "on" : "off",
            bgfx::isValid(m_terrainTextureAtlasHandle) ? "yes" : "no",
            m_texturedBModelBatches.empty() ? "no" : "yes"
        );
        bgfx::dbgTextPrintf(
            0,
            6,
            0x0f,
            "Move: WASD  Space use  X jump  Ctrl down  Shift turbo  R run F fly T waterwalk G feather"
        );

        nextHudLine = 7;

        if (m_pOutdoorPartyRuntime)
        {
        const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
        const OutdoorMovementEvents &moveEvents = m_pOutdoorPartyRuntime->movementEvents();
        const OutdoorMovementConsequences &moveConsequences = m_pOutdoorPartyRuntime->movementConsequences();
        const OutdoorPartyMovementState &partyMovementState = m_pOutdoorPartyRuntime->partyMovementState();
        const Party &party = m_pOutdoorPartyRuntime->party();
        const EventRuntimeState *pEventRuntimeState =
            m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
        const size_t openedChestCount =
            m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->openedChestCount() : 0;
        const size_t totalChestCount =
            m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->chestCount() : 0;
        std::string leaderSummary = "-";

        if (!party.members().empty())
        {
            const Character &leader = party.members().front();
            leaderSummary = leader.name + "/" + leader.role + " lv" + std::to_string(leader.level);
        }

        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Pos: %.0f %.0f %.0f  support=%s  water=%s  burn=%s  air=%s  land=%s  fall=%.0f",
            m_cameraTargetX,
            m_cameraTargetY,
            m_cameraTargetZ,
            outdoorSupportKindName(moveState.supportKind),
            moveState.supportOnWater ? "on" : "off",
            moveState.supportOnBurning ? "on" : "off",
            moveState.airborne ? "on" : "off",
            moveState.landedThisFrame ? "yes" : "no",
            moveState.fallDistance
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Mods: run=%s fly=%s waterwalk=%s feather=%s",
            partyMovementState.running ? "on" : "off",
            partyMovementState.flying ? "on" : "off",
            partyMovementState.waterWalk ? "on" : "off",
            partyMovementState.featherFall ? "on" : "off"
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Events: fall=%s land=%s hard=%s water=%s/%s burn=%s/%s",
            moveEvents.startedFalling ? "yes" : "no",
            moveEvents.landed ? "yes" : "no",
            moveEvents.hardLanding ? "yes" : "no",
            moveEvents.enteredWater ? "in" : "-",
            moveEvents.leftWater ? "out" : "-",
            moveEvents.enteredBurning ? "in" : "-",
            moveEvents.leftBurning ? "out" : "-"
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Fx: waterDmg=%s burnDmg=%s fallDmg=%s splash=%s land=%s hard=%s",
            moveConsequences.applyWaterDamage ? "yes" : "no",
            moveConsequences.applyBurningDamage ? "yes" : "no",
            moveConsequences.applyFallDamage ? "yes" : "no",
            moveConsequences.playSplashSound ? "yes" : "no",
            moveConsequences.playLandingSound ? "yes" : "no",
            moveConsequences.playHardLandingSound ? "yes" : "no"
        );

        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Party: members=%u hp=%d/%d gold=%d food=%d items=%u inv=%u/%u lead=%s",
            static_cast<unsigned>(party.members().size()),
            party.totalHealth(),
            party.totalMaxHealth(),
            party.gold(),
            party.food(),
            static_cast<unsigned>(party.inventoryItemCount()),
            static_cast<unsigned>(party.usedInventoryCells()),
            static_cast<unsigned>(party.inventoryCapacity()),
            leaderSummary.c_str()
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "PartyFx: waterTicks=%u burnTicks=%u fall=%.0f chests=%u/%u status=%s",
            party.waterDamageTicks(),
            party.burningDamageTicks(),
            party.lastFallDamageDistance(),
            static_cast<unsigned>(openedChestCount),
            static_cast<unsigned>(totalChestCount),
            party.lastStatus().c_str()
        );

        if (pEventRuntimeState != nullptr && pEventRuntimeState->lastActivationResult)
        {
            bgfx::dbgTextPrintf(
                0,
                nextHudLine++,
                0x0f,
                "Activate: %s",
                pEventRuntimeState->lastActivationResult->c_str()
            );
        }

        if (pEventRuntimeState != nullptr)
        {
            std::string runtimeSummary;

            if (pEventRuntimeState->pendingDialogueContext)
            {
                const EventRuntimeState::PendingDialogueContext &context = *pEventRuntimeState->pendingDialogueContext;

                if (context.kind == DialogueContextKind::HouseService)
                {
                    runtimeSummary += " house=" + std::to_string(context.sourceId);
                }
                else if (context.kind == DialogueContextKind::NpcTalk)
                {
                    runtimeSummary += " npc=" + std::to_string(context.sourceId);
                }
                else if (context.kind == DialogueContextKind::NpcNews)
                {
                    runtimeSummary += " news=" + std::to_string(context.newsId);
                }
            }

            if (pEventRuntimeState->pendingMapMove)
            {
                runtimeSummary += " map=("
                    + std::to_string(pEventRuntimeState->pendingMapMove->x)
                    + ","
                    + std::to_string(pEventRuntimeState->pendingMapMove->y)
                    + ","
                    + std::to_string(pEventRuntimeState->pendingMapMove->z)
                    + ")";

                if (pEventRuntimeState->pendingMapMove->mapName
                    && !pEventRuntimeState->pendingMapMove->mapName->empty())
                {
                    runtimeSummary += ":" + *pEventRuntimeState->pendingMapMove->mapName;
                }
            }

            if (!pEventRuntimeState->openedChestIds.empty())
            {
                runtimeSummary += " chest=" + std::to_string(pEventRuntimeState->openedChestIds.back());
            }

            if (!pEventRuntimeState->grantedItemIds.empty())
            {
                runtimeSummary += " give=" + std::to_string(pEventRuntimeState->grantedItemIds.back());
            }

            if (!runtimeSummary.empty())
            {
                bgfx::dbgTextPrintf(0, nextHudLine++, 0x0f, "Event:%s", runtimeSummary.c_str());
            }
        }
        }
        else
        {
            bgfx::dbgTextPrintf(
                0,
                nextHudLine++,
                0x0f,
                "Pos: %.0f %.0f %.0f",
                m_cameraTargetX,
                m_cameraTargetY,
                m_cameraTargetZ
            );
        }
    }

        if (m_inspectMode)
        {
        const int inspectBaseLine = nextHudLine + 1;

        if (inspectHit.hasHit)
        {
            if (inspectHit.kind == "entity")
            {
                const std::string primaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdPrimary,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string secondaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdSecondary,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string primaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdPrimary,
                    m_outdoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string secondaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdSecondary,
                    m_outdoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: entity=%u dist=%.0f name=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "Entity: dec=%u evt=%u/%u var=%u/%u trig=%u",
                    inspectHit.decorationListId,
                    inspectHit.eventIdPrimary,
                    inspectHit.eventIdSecondary,
                    inspectHit.variablePrimary,
                    inspectHit.variableSecondary,
                    inspectHit.specialTrigger
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 2,
                    0x0f,
                    "Script: P %s | S %s",
                    primaryEventSummary.c_str(),
                    secondaryEventSummary.c_str()
                );
                if (!primaryChestSummary.empty() || !secondaryChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(
                        0,
                        inspectBaseLine + 3,
                        0x0f,
                        "Chest: P %s | S %s",
                        primaryChestSummary.empty() ? "-" : primaryChestSummary.c_str(),
                        secondaryChestSummary.empty() ? "-" : secondaryChestSummary.c_str()
                    );
                }
            }
            else if (inspectHit.kind == "actor")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: actor=%u dist=%.0f name=%s %s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str(),
                    inspectHit.isFriendly ? "[friendly]" : "[hostile]"
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "npc=%d  %s",
                    inspectHit.npcId,
                    inspectHit.spawnSummary.empty() ? "-" : inspectHit.spawnSummary.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 2,
                    0x0f,
                    "%s",
                    inspectHit.spawnDetail.empty() ? "-" : inspectHit.spawnDetail.c_str()
                );

                if (m_outdoorActorPreviewBillboardSet
                    && inspectHit.bModelIndex < m_outdoorActorPreviewBillboardSet->billboards.size())
                {
                    const ActorPreviewBillboard &actorBillboard =
                        m_outdoorActorPreviewBillboardSet->billboards[inspectHit.bModelIndex];
                    const OutdoorWorldRuntime::MapActorState *pActorState = OutdoorInteractionController::runtimeActorStateForBillboard(*this, actorBillboard);
                    uint16_t spriteFrameIndex = actorBillboard.spriteFrameIndex;
                    uint32_t frameTimeTicks = actorBillboard.useStaticFrame ? 0U : currentAnimationTicks();
                    int octant = 0;

                    if (pActorState != nullptr)
                    {
                        const size_t animationIndex = static_cast<size_t>(pActorState->animation);

                        if (animationIndex < actorBillboard.actionSpriteFrameIndices.size()
                            && actorBillboard.actionSpriteFrameIndices[animationIndex] != 0)
                        {
                            spriteFrameIndex = actorBillboard.actionSpriteFrameIndices[animationIndex];
                        }

                        frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pActorState->animationTimeTicks));
                        const float angleToCamera = std::atan2(
                            static_cast<float>(pActorState->x) - wireframeEye.x,
                            static_cast<float>(pActorState->y) - wireframeEye.y
                        );
                        const float actorYaw = (Pi * 0.5f) - pActorState->yawRadians;
                        const float octantAngle = actorYaw - angleToCamera + Pi + (Pi / 8.0f);
                        octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;

                        bgfx::dbgTextPrintf(
                            0,
                            inspectBaseLine + 3,
                            0x0f,
                            "AI: state=%d anim=%d yaw=%.2f pos=%d,%d,%d",
                            static_cast<int>(pActorState->aiState),
                            static_cast<int>(pActorState->animation),
                            pActorState->yawRadians,
                            pActorState->x,
                            pActorState->y,
                            pActorState->z
                        );
                        bgfx::dbgTextPrintf(
                            0,
                            inspectBaseLine + 4,
                            0x0f,
                            "Runtime: idx=%u move=%u action=%.2f idle=%.2f vel=%.1f,%.1f",
                            static_cast<unsigned>(actorBillboard.runtimeActorIndex),
                            static_cast<unsigned>(pActorState->moveSpeed),
                            pActorState->actionSeconds,
                            pActorState->idleDecisionSeconds,
                            pActorState->velocityX,
                            pActorState->velocityY
                        );
                        const float deltaHomeX = pActorState->homePreciseX - pActorState->preciseX;
                        const float deltaHomeY = pActorState->homePreciseY - pActorState->preciseY;
                        const float distanceToHome = std::sqrt(deltaHomeX * deltaHomeX + deltaHomeY * deltaHomeY);
                        bgfx::dbgTextPrintf(
                            0,
                            inspectBaseLine + 5,
                            0x0f,
                            "Home: dist=%.1f decisions=%u",
                            distanceToHome,
                            static_cast<unsigned>(pActorState->idleDecisionCount)
                        );
                    }

                    const SpriteFrameEntry *pFrame =
                        m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

                    if (pFrame != nullptr)
                    {
                        const ResolvedSpriteTexture resolvedTexture =
                            SpriteFrameTable::resolveTexture(*pFrame, octant);
                        bgfx::dbgTextPrintf(
                            0,
                            inspectBaseLine + 6,
                            0x0f,
                            "Draw: frame=%u sprite=%s tex=%s pal=%d oct=%d",
                            static_cast<unsigned>(spriteFrameIndex),
                            pFrame->spriteName.c_str(),
                            resolvedTexture.textureName.c_str(),
                            pFrame->paletteId,
                            octant
                        );
                    }

                    bgfx::dbgTextPrintf(0, inspectBaseLine + 7, 0x0f, "Keys: E=talk/use  H=hit actor");
                }
            }
            else if (inspectHit.kind == "spawn")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: spawn=%u dist=%.0f type=%u %s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.spawnTypeId,
                    inspectHit.spawnSummary.empty() ? "-" : inspectHit.spawnSummary.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "%s",
                    inspectHit.spawnDetail.empty() ? "-" : inspectHit.spawnDetail.c_str()
                );
                bgfx::dbgTextPrintf(0, inspectBaseLine + 2, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }
            else if (inspectHit.kind == "decoration")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: decoration=%u dist=%.0f name=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "decorationId=%u",
                    inspectHit.decorationId
                );
            }
            else if (inspectHit.kind == "object")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: object=%u dist=%.0f name=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "Object: desc=%u sprite=%u attr=0x%04x spell=%d",
                    inspectHit.objectDescriptionId,
                    inspectHit.objectSpriteId,
                    inspectHit.attributes,
                    inspectHit.spellId
                );
                bgfx::dbgTextPrintf(0, inspectBaseLine + 2, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }
            else if (inspectHit.kind == "world_item")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: world_item=%u dist=%.0f name=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "World item: desc=%u sprite=%u attr=0x%04x",
                    inspectHit.objectDescriptionId,
                    inspectHit.objectSpriteId,
                    inspectHit.attributes
                );
                bgfx::dbgTextPrintf(0, inspectBaseLine + 2, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }
            else
            {
                const std::string faceEventSummary = summarizeLinkedEvent(
                    inspectHit.cogTriggeredNumber,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string faceChestSummary = summarizeLinkedChests(
                    inspectHit.cogTriggeredNumber,
                    m_outdoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: bmodel=%u face=%u distance=%.0f tex=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    static_cast<unsigned>(inspectHit.faceIndex),
                    inspectHit.distance,
                    inspectHit.textureName.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "Face: attr=0x%08x bmp=%d cog=%u evt=%u trig=%u",
                    inspectHit.attributes,
                    inspectHit.bitmapIndex,
                    inspectHit.cogNumber,
                    inspectHit.cogTriggeredNumber,
                    inspectHit.cogTrigger
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 2,
                    0x0f,
                    "Type: poly=%u shade=%u vis=%u  Script: %s",
                    static_cast<unsigned>(inspectHit.polygonType),
                    static_cast<unsigned>(inspectHit.shade),
                    static_cast<unsigned>(inspectHit.visibility),
                    faceEventSummary.c_str()
                );
                if (!faceChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(0, inspectBaseLine + 3, 0x0f, "%s", faceChestSummary.c_str());
                }
            }
        }
        else
        {
            bgfx::dbgTextPrintf(0, inspectBaseLine, 0x0f, "Inspect: no outdoor object under cursor");
            bgfx::dbgTextPrintf(0, inspectBaseLine + 1, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
        }
        }

        debugTextStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        const bool deferDialogueInventoryServiceOverlay =
            m_inventoryNestedOverlay.active
            && (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopSell
                || m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopIdentify
                || m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopRepair)
            && currentHudScreenState() == HudScreenState::Dialogue;

        if (m_showGameplayHud)
        {
            renderChestPanel(width, height, false);
            if (!deferDialogueInventoryServiceOverlay)
            {
                renderInventoryNestedOverlay(width, height, false);
            }
            renderEventDialogPanel(width, height, false);
            renderCharacterOverlay(width, height, false);
            renderGameplayHudArt(width, height);
            renderGameplayHud(width, height);
            renderChestPanel(width, height, true);
            renderCharacterOverlay(width, height, true);
            renderEventDialogPanel(width, height, true);
            if (deferDialogueInventoryServiceOverlay)
            {
                renderInventoryNestedOverlay(width, height, false);
            }
            renderSpellbookOverlay(width, height);
            renderHeldInventoryItem(width, height);
            renderItemInspectOverlay(width, height);
            renderCharacterInspectOverlay(width, height);
            renderBuffInspectOverlay(width, height);
            renderCharacterDetailOverlay(width, height);
            renderActorInspectOverlay(width, height);
            renderSpellInspectOverlay(width, height);
            renderReadableScrollOverlay(width, height);
            renderPendingSpellTargetingOverlay(width, height);
        }

        hudStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    updateFootstepAudio(deltaSeconds);
    consumePendingPartyAudioRequests();
    consumePendingWorldAudioEvents();

    const uint64_t renderElapsedNanoseconds = SDL_GetTicksNS() - renderStartTickCount;

    if (DebugRenderHitchLogging && renderElapsedNanoseconds > RenderHitchLogThresholdNanoseconds)
    {
        std::cout << "Render hitch: total_ms=" << (static_cast<float>(renderElapsedNanoseconds) / 1000000.0f)
                  << " camera_ms=" << (static_cast<float>(cameraStageNanoseconds) / 1000000.0f)
                  << " inspect_ms=" << (static_cast<float>(inspectStageNanoseconds) / 1000000.0f)
                  << " terrain_ms=" << (static_cast<float>(terrainStageNanoseconds) / 1000000.0f)
                  << " bmodels_ms=" << (static_cast<float>(bmodelStageNanoseconds) / 1000000.0f)
                  << " decorations_ms=" << (static_cast<float>(decorationStageNanoseconds) / 1000000.0f)
                  << " actors_ms=" << (static_cast<float>(actorStageNanoseconds) / 1000000.0f)
                  << " sprites_ms=" << (static_cast<float>(spriteStageNanoseconds) / 1000000.0f)
                  << " spawns_ms=" << (static_cast<float>(spawnStageNanoseconds) / 1000000.0f)
                  << " dbgtext_ms=" << (static_cast<float>(debugTextStageNanoseconds) / 1000000.0f)
                  << " hud_ms=" << (static_cast<float>(hudStageNanoseconds) / 1000000.0f)
                  << '\n';
    }
}

void OutdoorGameView::renderGameplayHudArt(int width, int height)
{
    GameplayHudRenderer::renderGameplayHudArt(*this, width, height);
}

void OutdoorGameView::renderGameplayHud(int width, int height) const
{
    GameplayHudRenderer::renderGameplayHud(*this, width, height);
}

void OutdoorGameView::renderChestPanel(int width, int height, bool renderAboveHud) const
{
    if (m_pOutdoorWorldRuntime == nullptr || m_chestTable == std::nullopt || width <= 0 || height <= 0)
    {
        return;
    }

    const OutdoorWorldRuntime::ChestViewState *pChestView = m_pOutdoorWorldRuntime->activeChestView();
    const OutdoorWorldRuntime::CorpseViewState *pCorpseView = m_pOutdoorWorldRuntime->activeCorpseView();

    if (pChestView == nullptr && pCorpseView == nullptr)
    {
        return;
    }

    if (currentHudScreenState() != HudScreenState::Chest)
    {
        return;
    }

    if (pChestView != nullptr)
    {
        GameplayOverlayContext overlayContext(*const_cast<OutdoorGameView *>(this));
        GameplayHudOverlayRenderer::renderChestPanel(overlayContext, width, height, renderAboveHud);
        return;
    }

    if (!renderAboveHud)
    {
        return;
    }

    const int textColumns = std::max(80, width / DebugTextCellWidthPixels);
    const int textRows = std::max(25, height / DebugTextCellHeightPixels);
    int row = std::max(8, textRows / 4);

    std::string title;

    if (pChestView != nullptr)
    {
        const ChestEntry *pChestEntry = m_chestTable->get(pChestView->chestTypeId);
        std::ostringstream titleStream;
        titleStream << "Chest #" << pChestView->chestId;

        if (pChestEntry != nullptr && !pChestEntry->name.empty())
        {
            titleStream << " - " << pChestEntry->name;
        }

        title = titleStream.str();
    }
    else
    {
        title = pCorpseView->title.empty() ? "Corpse" : pCorpseView->title;
    }

    const int titleColumn = std::max(0, (textColumns - static_cast<int>(title.size())) / 2);
    bgfx::dbgTextPrintf(static_cast<uint16_t>(titleColumn), static_cast<uint16_t>(row++), 0x1f, "%s", title.c_str());

    const std::string closeHint = "Up/Down select  Enter/Space loot  E/Esc close";
    const int hintColumn = std::max(0, (textColumns - static_cast<int>(closeHint.size())) / 2);
    bgfx::dbgTextPrintf(
        static_cast<uint16_t>(hintColumn),
        static_cast<uint16_t>(row++),
        0x0f,
        "%s",
        closeHint.c_str()
    );
    row += 1;

    const std::vector<OutdoorWorldRuntime::ChestItemState> &items =
        pChestView != nullptr ? pChestView->items : pCorpseView->items;

    if (items.empty())
    {
        const std::string emptyLine = "Empty";
        const int emptyColumn = std::max(0, (textColumns - static_cast<int>(emptyLine.size())) / 2);
        bgfx::dbgTextPrintf(
            static_cast<uint16_t>(emptyColumn),
            static_cast<uint16_t>(row),
            0x0f,
            "%s",
            emptyLine.c_str()
        );
        return;
    }

    constexpr size_t MaxVisibleItems = 14;
    const size_t visibleCount = std::min(items.size(), MaxVisibleItems);

    for (size_t itemIndex = 0; itemIndex < visibleCount; ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = items[itemIndex];
        std::string itemName;

        if (item.isGold)
        {
            itemName = std::to_string(item.goldAmount) + " gold";

            if (item.goldRollCount > 1)
            {
                itemName += " (" + std::to_string(item.goldRollCount) + " rolls)";
            }
        }
        else
        {
            itemName = "item #" + std::to_string(item.itemId);
        }

        if (!item.isGold && m_pItemTable != nullptr)
        {
            const ItemDefinition *pItemDefinition = m_pItemTable->get(item.itemId);

            if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
            {
                itemName = pItemDefinition->name;
            }
        }

        if (!item.isGold && item.quantity > 1)
        {
            itemName += " x" + std::to_string(item.quantity);
        }

        const std::string line = std::to_string(itemIndex + 1) + ". " + itemName;
        const uint8_t color = itemIndex == m_chestSelectionIndex ? 0x0e : 0x0f;
        const int column = std::max(4, (textColumns / 2) - 20);
        bgfx::dbgTextPrintf(
            static_cast<uint16_t>(column),
            static_cast<uint16_t>(row++),
            color,
            "%s",
            line.c_str()
        );
    }

    if (items.size() > visibleCount)
    {
        const std::string moreLine = "...";
        const int moreColumn = std::max(0, (textColumns - static_cast<int>(moreLine.size())) / 2);
        bgfx::dbgTextPrintf(
            static_cast<uint16_t>(moreColumn),
            static_cast<uint16_t>(row),
            0x0f,
            "%s",
            moreLine.c_str()
        );
    }
}

void OutdoorGameView::renderInventoryNestedOverlay(int width, int height, bool renderAboveHud) const
{
    GameplayOverlayContext overlayContext(*const_cast<OutdoorGameView *>(this));
    GameplayHudOverlayRenderer::renderInventoryNestedOverlay(
        overlayContext,
        width,
        height,
        renderAboveHud);
}

void OutdoorGameView::renderEventDialogPanel(int width, int height, bool renderAboveHud)
{
    if (width <= 0 || height <= 0)
    {
        return;
    }

    if (!m_activeEventDialog.isActive)
    {
        EventRuntimeState *pEventRuntimeState =
            m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

        if (pEventRuntimeState != nullptr
            && pEventRuntimeState->pendingDialogueContext
            && pEventRuntimeState->pendingDialogueContext->kind != DialogueContextKind::None)
        {
            OutdoorInteractionController::presentPendingEventDialog(*this, pEventRuntimeState->messages.size(), true);
        }
    }

    if (!m_activeEventDialog.isActive)
    {
        return;
    }

    if (currentHudScreenState() == HudScreenState::Dialogue)
    {
        renderDialogueOverlay(width, height, renderAboveHud);
        return;
    }

    if (!renderAboveHud)
    {
        return;
    }

    const int textColumns = std::max(80, width / DebugTextCellWidthPixels);
    const int textRows = std::max(25, height / DebugTextCellHeightPixels);
    int row = std::max(8, textRows / 4);

    const int titleColumn = std::max(0, (textColumns - static_cast<int>(m_activeEventDialog.title.size())) / 2);
    bgfx::dbgTextPrintf(
        static_cast<uint16_t>(titleColumn),
        static_cast<uint16_t>(row++),
        0x1f,
        "%s",
        m_activeEventDialog.title.c_str()
    );

    const bool hasActions = !m_activeEventDialog.actions.empty();
    const std::string closeHint = hasActions
        ? "Up/Down select  Enter/Space accept  E/Esc close"
        : "Enter/Space/E/Esc close";
    const int hintColumn = std::max(0, (textColumns - static_cast<int>(closeHint.size())) / 2);
    bgfx::dbgTextPrintf(
        static_cast<uint16_t>(hintColumn),
        static_cast<uint16_t>(row++),
        0x0f,
        "%s",
        closeHint.c_str()
    );
    row += 1;

    const size_t maxVisibleLines = hasActions ? 8u : 12u;
    const size_t visibleCount = std::min(m_activeEventDialog.lines.size(), maxVisibleLines);

    for (size_t lineIndex = 0; lineIndex < visibleCount; ++lineIndex)
    {
        const std::string &line = m_activeEventDialog.lines[lineIndex];
        const int lineColumn = std::max(0, (textColumns - static_cast<int>(line.size())) / 2);
        bgfx::dbgTextPrintf(
            static_cast<uint16_t>(lineColumn),
            static_cast<uint16_t>(row++),
            0x0f,
            "%s",
            line.c_str()
        );
    }

    if (!hasActions)
    {
        return;
    }

    row += 1;

    for (size_t actionIndex = 0; actionIndex < m_activeEventDialog.actions.size(); ++actionIndex)
    {
        const EventDialogAction &action = m_activeEventDialog.actions[actionIndex];
        const bool isSelected = actionIndex == m_eventDialogSelectionIndex;
        std::string actionLine = isSelected ? "> " : "  ";
        actionLine += action.label;

        if (!action.enabled)
        {
            actionLine += " [unavailable]";
        }

        const int actionColumn = std::max(0, (textColumns - static_cast<int>(actionLine.size())) / 2);
        const uint8_t color = !action.enabled ? 0x08 : (isSelected ? 0x2f : 0x0f);
        bgfx::dbgTextPrintf(
            static_cast<uint16_t>(actionColumn),
            static_cast<uint16_t>(row++),
            color,
            "%s",
            actionLine.c_str()
        );
    }
}

void OutdoorGameView::shutdown()
{
    if (!m_isInitialized)
    {
        return;
    }

    auto resetRuntimeState = [this]()
    {
        m_isRenderable = false;
        m_isInitialized = false;
        m_map.reset();
        m_monsterTable.reset();
        m_outdoorMapData.reset();
        m_pOutdoorPartyRuntime = nullptr;
        m_pAssetFileSystem = nullptr;
        m_pOutdoorSceneRuntime = nullptr;
        m_pOutdoorWorldRuntime = nullptr;
        m_pItemTable = nullptr;
        m_pStandardItemEnchantTable = nullptr;
        m_pSpecialItemEnchantTable = nullptr;
        m_pItemEquipPosTable = nullptr;
        m_pRosterTable = nullptr;
        m_pArcomageLibrary = nullptr;
        m_pCharacterDollTable = nullptr;
    };

    m_gameplayUiController.clearRuntimeState();
    m_houseVideoPlayer.shutdown();

    if (bgfx::getInternalData() == nullptr)
    {
        m_programHandle = BGFX_INVALID_HANDLE;
        m_texturedTerrainProgramHandle = BGFX_INVALID_HANDLE;
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
        m_terrainTextureSamplerHandle = BGFX_INVALID_HANDLE;
        m_indexBufferHandle = BGFX_INVALID_HANDLE;
        m_filledTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_skyVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bmodelVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bmodelCollisionVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_vertexBufferHandle = BGFX_INVALID_HANDLE;

        for (TexturedBModelBatch &batch : m_texturedBModelBatches)
        {
            batch.vertexBufferHandle = BGFX_INVALID_HANDLE;
            batch.textureHandle = BGFX_INVALID_HANDLE;
        }

        for (HudTextureHandle &textureHandle : m_hudTextureHandles)
        {
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }

        for (HudFontHandle &fontHandle : m_hudFontHandles)
        {
            fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
            fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
        }

        for (HudFontColorTextureHandle &textureHandle : m_hudFontColorTextureHandles)
        {
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }

        for (HudTextureColorTextureHandle &textureHandle : m_hudTextureColorTextureHandles)
        {
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }

        m_texturedBModelBatches.clear();
        OutdoorBillboardRenderer::invalidateRenderAssets(*this);
        OutdoorRenderer::invalidateSkyResources(*this);
        m_hudTextureHandles.clear();
        m_hudFontHandles.clear();
        m_hudFontColorTextureHandles.clear();
        m_hudTextureColorTextureHandles.clear();
        m_uiLayoutManager.clear();
        m_interactiveDecorationBindings.clear();
        resetRuntimeState();
        return;
    }

    if (bgfx::isValid(m_programHandle))
    {
        bgfx::destroy(m_programHandle);
        m_programHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedTerrainProgramHandle))
    {
        bgfx::destroy(m_texturedTerrainProgramHandle);
        m_texturedTerrainProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureAtlasHandle))
    {
        bgfx::destroy(m_terrainTextureAtlasHandle);
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        bgfx::destroy(m_terrainTextureSamplerHandle);
        m_terrainTextureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indexBufferHandle))
    {
        bgfx::destroy(m_indexBufferHandle);
        m_indexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_filledTerrainVertexBufferHandle))
    {
        bgfx::destroy(m_filledTerrainVertexBufferHandle);
        m_filledTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    for (TexturedBModelBatch &batch : m_texturedBModelBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
            batch.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        if (bgfx::isValid(batch.textureHandle))
        {
            bgfx::destroy(batch.textureHandle);
            batch.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_texturedBModelBatches.clear();
    OutdoorBillboardRenderer::destroyRenderAssets(*this);
    OutdoorRenderer::destroySkyResources(*this);

    for (HudTextureHandle &textureHandle : m_hudTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudTextureHandles.clear();
    for (HudFontHandle &fontHandle : m_hudFontHandles)
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
            fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
            fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudFontHandles.clear();
    for (HudFontColorTextureHandle &textureHandle : m_hudFontColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudFontColorTextureHandles.clear();

    for (HudTextureColorTextureHandle &textureHandle : m_hudTextureColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudTextureColorTextureHandles.clear();
    m_uiLayoutManager.clear();
    m_interactiveDecorationBindings.clear();

    if (bgfx::isValid(m_skyVertexBufferHandle))
    {
        bgfx::destroy(m_skyVertexBufferHandle);
        m_skyVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedTerrainVertexBufferHandle))
    {
        bgfx::destroy(m_texturedTerrainVertexBufferHandle);
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bmodelVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelVertexBufferHandle);
        m_bmodelVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bmodelCollisionVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelCollisionVertexBufferHandle);
        m_bmodelCollisionVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_entityMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_entityMarkerVertexBufferHandle);
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spawnMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_spawnMarkerVertexBufferHandle);
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_vertexBufferHandle))
    {
        bgfx::destroy(m_vertexBufferHandle);
        m_vertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    resetRuntimeState();
    m_pObjectTable = nullptr;
    m_pSpellTable = nullptr;
    m_pReadableScrollTable = nullptr;
    m_pGameAudioSystem = nullptr;
    m_faceAnimationTable = {};
    m_iconFrameTable = {};
    m_portraitFrameTable = {};
    m_spellFxTable = {};
    m_lastPortraitAnimationUpdateTicks = 0;
    m_outdoorDecorationBillboardSet.reset();
    m_outdoorActorPreviewBillboardSet.reset();
    m_outdoorSpriteObjectBillboardSet.reset();
    m_classSkillTable.reset();
    m_npcDialogTable.reset();
    m_characterInspectTable.reset();
    m_elapsedTime = 0.0f;
    m_framesPerSecond = 0.0f;
    m_cachedSkyVertices.clear();
    m_cachedSkyTextureName.clear();
    m_lastSkyUpdateElapsedTime = -1.0f;
    m_bmodelLineVertexCount = 0;
    m_bmodelCollisionVertexCount = 0;
    m_bmodelFaceCount = 0;
    m_entityMarkerVertexCount = 0;
    m_spawnMarkerVertexCount = 0;
    m_toggleFilledLatch = false;
    m_toggleWireframeLatch = false;
    m_toggleBModelsLatch = false;
    m_toggleBModelWireframeLatch = false;
    m_toggleBModelCollisionFacesLatch = false;
    m_toggleActorCollisionBoxesLatch = false;
    m_toggleDecorationBillboardsLatch = false;
    m_toggleActorsLatch = false;
    m_toggleSpriteObjectsLatch = false;
    m_toggleEntitiesLatch = false;
    m_toggleSpawnsLatch = false;
    m_inspectMode = true;
    m_toggleInspectLatch = false;
    m_triggerMeteorLatch = false;
    m_keyboardUseLatch = false;
    m_activateInspectLatch = false;
    m_inspectMouseActivateLatch = false;
    m_attackInspectLatch = false;
    m_quickSpellCastLatch = false;
    m_spellbookToggleLatch = false;
    m_spellbookClickLatch = false;
    m_pendingSpellTargetClickLatch = false;
    m_inventoryScreenToggleLatch = false;
    m_adventurersInnToggleLatch = false;
    m_characterScreenOpen = false;
    m_characterDollJewelryOverlayOpen = false;
    m_adventurersInnRosterOverlayOpen = false;
    m_characterPage = CharacterPage::Inventory;
    m_characterScreenSource = CharacterScreenSource::Party;
    m_characterScreenSourceIndex = 0;
    m_adventurersInnScrollOffset = 0;
    m_characterClickLatch = false;
    m_characterMemberCycleLatch = false;
    m_characterPressedTarget = {};
    m_partyPortraitClickLatch = false;
    m_partyPortraitPressedIndex = std::nullopt;
    m_lastPartyPortraitClickTicks = 0;
    m_lastPartyPortraitClickedIndex = std::nullopt;
    m_lastAdventurersInnPortraitClickTicks = 0;
    m_lastAdventurersInnPortraitClickedIndex = std::nullopt;
    m_pendingCharacterDismissMemberIndex = std::nullopt;
    m_pendingCharacterDismissExpiresTicks = 0;
    m_heldInventoryItem = {};
    m_actorInspectOverlay = {};
    m_spellInspectOverlay = {};
    m_readableScrollOverlay = {};
    m_spellbook = {};
    m_spellbookPressedTarget = {};
    m_lastSpellbookSpellClickTicks = 0;
    m_lastSpellbookClickedSpellId = 0;
    m_pendingSpellCast = {};
    m_heldInventoryDropLatch = false;
    m_cachedHoverInspectHitValid = false;
    m_lastHoverInspectUpdateNanoseconds = 0;
    m_cachedHoverInspectHit = {};
    m_closeOverlayLatch = false;
    m_dialogueClickLatch = false;
    m_dialoguePressedTarget = {};
    m_lootChestItemLatch = false;
    m_chestSelectUpLatch = false;
    m_chestSelectDownLatch = false;
    m_eventDialogSelectUpLatch = false;
    m_eventDialogSelectDownLatch = false;
    m_eventDialogAcceptLatch = false;
    m_eventDialogPartySelectLatches.fill(false);
    m_chestSelectionIndex = 0;
    m_eventDialogSelectionIndex = 0;
    m_activeEventDialog = {};
    m_isRotatingCamera = false;
    m_lastMouseX = 0.0f;
    m_lastMouseY = 0.0f;
    m_pressedInspectHit = {};
    m_portraitSpellFxStates.clear();
    m_lastFootstepX = 0.0f;
    m_lastFootstepY = 0.0f;
    m_hasLastFootstepPosition = false;
    m_walkingMotionHoldSeconds = 0.0f;
    m_activeWalkingSoundId = std::nullopt;
    m_memberSpeechCooldownUntilTicks.clear();
    m_memberCombatSpeechCooldownUntilTicks.clear();
    m_activeHouseAudioHostId = 0;
}

float OutdoorGameView::cameraYawRadians() const
{
    return m_cameraYawRadians;
}

float OutdoorGameView::cameraPitchRadians() const
{
    return m_cameraPitchRadians;
}

void OutdoorGameView::setCameraAngles(float yawRadians, float pitchRadians)
{
    m_cameraYawRadians = yawRadians;
    m_cameraPitchRadians = pitchRadians;

    if (m_cameraYawRadians > Pi)
    {
        m_cameraYawRadians -= Pi * 2.0f;
    }
    else if (m_cameraYawRadians < -Pi)
    {
        m_cameraYawRadians += Pi * 2.0f;
    }

    m_cameraPitchRadians = std::clamp(m_cameraPitchRadians, -1.55f, 1.55f);
}

void OutdoorGameView::updateHouseVideoPlayback(float deltaSeconds)
{
    const EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const uint32_t hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
    const HouseEntry *pHostHouseEntry =
        (hostHouseId != 0 && m_houseTable.has_value()) ? m_houseTable->get(hostHouseId) : nullptr;

    if (currentHudScreenState() != HudScreenState::Dialogue
        || !m_activeEventDialog.isActive
        || pHostHouseEntry == nullptr
        || pHostHouseEntry->videoName.empty()
        || m_pAssetFileSystem == nullptr)
    {
        if (m_activeHouseAudioHostId != 0 && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::WoodDoorClosing, GameAudioSystem::PlaybackGroup::HouseDoor);
        }

        m_activeHouseAudioHostId = 0;
        m_houseVideoPlayer.stop();
        return;
    }

    if (m_activeHouseAudioHostId != pHostHouseEntry->id)
    {
        m_activeHouseAudioHostId = pHostHouseEntry->id;

        if (m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Enter, GameAudioSystem::PlaybackGroup::HouseDoor);
            const std::optional<uint32_t> greetingSoundId =
                deriveHouseSoundId(*pHostHouseEntry, HouseSoundType::GeneralGreeting);

            if (greetingSoundId.has_value())
            {
                m_pGameAudioSystem->playSound(
                    *greetingSoundId,
                    GameAudioSystem::PlaybackGroup::HouseSpeech);
            }
        }
    }

    m_houseVideoPlayer.play(*m_pAssetFileSystem, pHostHouseEntry->videoName);

    if (!m_houseShopOverlay.active)
    {
        m_houseVideoPlayer.update(deltaSeconds);
    }
}

bool OutdoorGameView::hasActiveEventDialog() const
{
    return m_activeEventDialog.isActive;
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolvePartyPortraitRect(
    int width,
    int height,
    size_t memberIndex)
{
    if (m_pOutdoorPartyRuntime == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const HudLayoutElement *pBasebarLayout = HudUiService::findHudLayoutElement(*this, "OutdoorBasebar");
    const HudLayoutElement *pPartyStripLayout = HudUiService::findHudLayoutElement(*this, "OutdoorPartyStrip");

    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return std::nullopt;
    }

    const HudTextureHandle *pBasebar = HudUiService::ensureHudTextureLoaded(*this, pBasebarLayout->primaryAsset);
    const HudTextureHandle *pFaceMask = HudUiService::ensureHudTextureLoaded(*this, pPartyStripLayout->primaryAsset);

    if (pBasebar == nullptr || pFaceMask == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<ResolvedHudLayoutElement> resolvedBasebar = HudUiService::resolveHudLayoutElement(*this, 
        "OutdoorBasebar",
        width,
        height,
        static_cast<float>(pBasebar->width),
        static_cast<float>(pBasebar->height));
    const std::optional<ResolvedHudLayoutElement> resolvedPartyStrip = HudUiService::resolveHudLayoutElement(*this, 
        "OutdoorPartyStrip",
        width,
        height,
        static_cast<float>(pBasebar->width),
        static_cast<float>(pBasebar->height));

    if (!resolvedBasebar || !resolvedPartyStrip)
    {
        return std::nullopt;
    }

    const std::vector<Character> &members = m_pOutdoorPartyRuntime->party().members();

    if (memberIndex >= members.size())
    {
        return std::nullopt;
    }

    const float portraitWidth = static_cast<float>(pFaceMask->width) * resolvedBasebar->scale;
    const float portraitHeight = static_cast<float>(pFaceMask->height) * resolvedBasebar->scale;
    const float portraitStartX = resolvedPartyStrip->x + resolvedPartyStrip->width * (20.0f / 471.0f);
    const float portraitY = resolvedPartyStrip->y + resolvedPartyStrip->height * (23.0f / 92.0f);
    const float portraitDeltaX = resolvedPartyStrip->width * (94.0f / 471.0f);

    return ResolvedHudLayoutElement{
        portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX,
        portraitY,
        portraitWidth,
        portraitHeight,
        resolvedBasebar->scale
    };
}

std::optional<size_t> OutdoorGameView::resolvePartyPortraitIndexAtPoint(
    int width,
    int height,
    float x,
    float y)
{
    if (m_pOutdoorPartyRuntime == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const std::vector<Character> &members = m_pOutdoorPartyRuntime->party().members();

    if (members.empty())
    {
        return std::nullopt;
    }

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        const std::optional<ResolvedHudLayoutElement> portraitRect =
            resolvePartyPortraitRect(width, height, memberIndex);

        if (portraitRect
            && x >= portraitRect->x
            && x < portraitRect->x + portraitRect->width
            && y >= portraitRect->y
            && y < portraitRect->y + portraitRect->height)
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

bool OutdoorGameView::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    if (m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    Party &party = m_pOutdoorPartyRuntime->party();

    if (requireGameplayReady && !party.canSelectMemberInGameplay(memberIndex))
    {
        return false;
    }

    if (!party.setActiveMemberIndex(memberIndex))
    {
        return false;
    }

    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr && hasActiveEventDialog())
    {
        OutdoorInteractionController::presentPendingEventDialog(*this, pEventRuntimeState->messages.size(), true);
    }

    return true;
}

bool OutdoorGameView::tryAutoPlaceHeldItemOnPartyMember(size_t memberIndex, bool showFailureStatus)
{
    if (m_pOutdoorPartyRuntime == nullptr || !m_heldInventoryItem.active)
    {
        return false;
    }

    Party &party = m_pOutdoorPartyRuntime->party();

    if (!party.tryAutoPlaceItemInMemberInventory(memberIndex, m_heldInventoryItem.item))
    {
        if (showFailureStatus)
        {
            setStatusBarEvent(party.lastStatus().empty() ? "Inventory full" : party.lastStatus());
        }

        return false;
    }

    m_heldInventoryItem = {};
    return true;
}

void OutdoorGameView::updateItemInspectOverlayState(int width, int height)
{
    m_itemInspectOverlay = {};

    if (width <= 0 || height <= 0 || m_pItemTable == nullptr || m_pendingSpellCast.active || m_spellbook.active)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        m_itemInspectInteractionLatch = false;
        m_itemInspectInteractionKey = 0;
        return;
    }

    if (currentHudScreenState() == m_renderedInspectableHudState)
    {
        for (auto it = m_renderedInspectableHudItems.rbegin(); it != m_renderedInspectableHudItems.rend(); ++it)
        {
            if (mouseX < it->x
                || mouseX >= it->x + it->width
                || mouseY < it->y
                || mouseY >= it->y + it->height)
            {
                continue;
            }

            if (!isOpaqueHudPixelAtPoint(*it, mouseX, mouseY))
            {
                continue;
            }

            m_itemInspectOverlay.active = true;
            m_itemInspectOverlay.objectDescriptionId = it->objectDescriptionId;
            m_itemInspectOverlay.hasItemState = it->hasItemState;
            m_itemInspectOverlay.itemState = it->itemState;
            m_itemInspectOverlay.sourceType = it->sourceType;
            m_itemInspectOverlay.sourceMemberIndex = it->sourceMemberIndex;
            m_itemInspectOverlay.sourceGridX = it->sourceGridX;
            m_itemInspectOverlay.sourceGridY = it->sourceGridY;
            m_itemInspectOverlay.sourceEquipmentSlot = it->equipmentSlot;
            m_itemInspectOverlay.sourceLootItemIndex = it->sourceLootItemIndex;
            m_itemInspectOverlay.hasValueOverride = it->hasValueOverride;
            m_itemInspectOverlay.valueOverride = it->valueOverride;
            m_itemInspectOverlay.sourceX = it->x;
            m_itemInspectOverlay.sourceY = it->y;
            m_itemInspectOverlay.sourceWidth = it->width;
            m_itemInspectOverlay.sourceHeight = it->height;
            tryApplyItemInspectSkillInteraction();
            return;
        }
    }

    if (!m_characterScreenOpen
        && !hasActiveEventDialog()
        && m_pOutdoorWorldRuntime != nullptr
        && m_outdoorMapData.has_value()
        && !m_heldInventoryItem.active)
    {
        const bool hasActiveLootView =
            m_pOutdoorWorldRuntime->activeChestView() != nullptr || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr;

        if (!hasActiveLootView)
        {
            InspectHit inspectHit = {};
            bool hasInspectHit = false;

            if (m_cachedHoverInspectHitValid)
            {
                inspectHit = m_cachedHoverInspectHit;
                hasInspectHit = true;
            }
            else if (!m_inspectMode)
            {
                const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
                const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));
                const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
                float viewMatrix[16] = {};
                float projectionMatrix[16] = {};
                const float cosPitch = std::cos(m_cameraPitchRadians);
                const float sinPitch = std::sin(m_cameraPitchRadians);
                const float cosYaw = std::cos(m_cameraYawRadians);
                const float sinYaw = std::sin(m_cameraYawRadians);
                const bx::Vec3 eye = {
                    m_cameraTargetX,
                    m_cameraTargetY,
                    m_cameraTargetZ
                };
                const bx::Vec3 at = {
                    m_cameraTargetX + cosYaw * cosPitch,
                    m_cameraTargetY - sinYaw * cosPitch,
                    m_cameraTargetZ + sinPitch
                };
                const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
                bx::mtxLookAt(viewMatrix, eye, at, up);
                bx::mtxProj(
                    projectionMatrix,
                    CameraVerticalFovDegrees,
                    aspectRatio,
                    0.1f,
                    200000.0f,
                    bgfx::getCaps()->homogeneousDepth
                );

                const float normalizedMouseX = ((mouseX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
                const float normalizedMouseY = 1.0f - ((mouseY / static_cast<float>(viewHeight)) * 2.0f);
                float viewProjectionMatrix[16] = {};
                float inverseViewProjectionMatrix[16] = {};
                bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);
                bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
                const bx::Vec3 rayOrigin =
                    bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
                const bx::Vec3 rayTarget =
                    bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
                const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
                inspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
                    *m_outdoorMapData,
                    rayOrigin,
                    rayDirection,
                    mouseX,
                    mouseY,
                    width,
                    height,
                    viewMatrix,
                    projectionMatrix,
                    OutdoorGameView::DecorationPickMode::HoverInfo);
                hasInspectHit = true;
            }

            if (hasInspectHit && inspectHit.kind == "world_item")
            {
                const OutdoorWorldRuntime::WorldItemState *pWorldItem =
                    m_pOutdoorWorldRuntime->worldItemState(inspectHit.bModelIndex);

                if (pWorldItem != nullptr)
                {
                    m_itemInspectOverlay.active = true;
                    m_itemInspectOverlay.objectDescriptionId = pWorldItem->item.objectDescriptionId;
                    m_itemInspectOverlay.hasItemState = !pWorldItem->isGold;
                    m_itemInspectOverlay.itemState = pWorldItem->item;
                    m_itemInspectOverlay.sourceType = ItemInspectSourceType::WorldItem;
                    m_itemInspectOverlay.sourceWorldItemIndex = inspectHit.bModelIndex;
                    m_itemInspectOverlay.hasValueOverride = pWorldItem->isGold;
                    m_itemInspectOverlay.valueOverride = static_cast<int>(pWorldItem->goldAmount);
                    m_itemInspectOverlay.sourceX = mouseX;
                    m_itemInspectOverlay.sourceY = mouseY;
                    m_itemInspectOverlay.sourceWidth = 1.0f;
                    m_itemInspectOverlay.sourceHeight = 1.0f;
                    tryApplyItemInspectSkillInteraction();
                    return;
                }
            }
        }
    }

    if (!m_characterScreenOpen
        || m_characterPage != CharacterPage::Inventory
        || m_pOutdoorPartyRuntime == nullptr
        || isAdventurersInnScreenActive())
    {
        return;
    }

    const Character *pCharacter = selectedCharacterScreenCharacter();
    const HudLayoutElement *pInventoryGridLayout = HudUiService::findHudLayoutElement(*this, "CharacterInventoryGrid");

    if (pCharacter == nullptr || pInventoryGridLayout == nullptr)
    {
        return;
    }

    const std::optional<ResolvedHudLayoutElement> resolvedInventoryGrid = HudUiService::resolveHudLayoutElement(*this, 
        "CharacterInventoryGrid",
        width,
        height,
        pInventoryGridLayout->width,
        pInventoryGridLayout->height);

    if (!resolvedInventoryGrid
        || mouseX < resolvedInventoryGrid->x
        || mouseX >= resolvedInventoryGrid->x + resolvedInventoryGrid->width
        || mouseY < resolvedInventoryGrid->y
        || mouseY >= resolvedInventoryGrid->y + resolvedInventoryGrid->height)
    {
        return;
    }

    const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
        resolvedInventoryGrid->x,
        resolvedInventoryGrid->y,
        resolvedInventoryGrid->width,
        resolvedInventoryGrid->height,
        resolvedInventoryGrid->scale);
    const uint8_t gridX = static_cast<uint8_t>(std::clamp(
        static_cast<int>((mouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
        0,
        Character::InventoryWidth - 1));
    const uint8_t gridY = static_cast<uint8_t>(std::clamp(
        static_cast<int>((mouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
        0,
        Character::InventoryHeight - 1));
    const InventoryItem *pHoveredItem = pCharacter->inventoryItemAt(gridX, gridY);

    if (pHoveredItem == nullptr)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pHoveredItem->objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
    {
        return;
    }

    const HudTextureHandle *pItemTexture = HudUiService::ensureHudTextureLoaded(*this, pItemDefinition->iconName);

    if (pItemTexture == nullptr)
    {
        return;
    }

    const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
    const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
    const InventoryItemScreenRect itemRect =
        computeInventoryItemScreenRect(gridMetrics, *pHoveredItem, itemWidth, itemHeight);

    m_itemInspectOverlay.active = true;
    m_itemInspectOverlay.objectDescriptionId = pHoveredItem->objectDescriptionId;
    m_itemInspectOverlay.hasItemState = true;
    m_itemInspectOverlay.itemState = *pHoveredItem;
    m_itemInspectOverlay.sourceType =
        isAdventurersInnCharacterSourceActive() ? ItemInspectSourceType::None : ItemInspectSourceType::Inventory;
    m_itemInspectOverlay.sourceMemberIndex =
        isAdventurersInnCharacterSourceActive() ? m_characterScreenSourceIndex : m_pOutdoorPartyRuntime->party().activeMemberIndex();
    m_itemInspectOverlay.sourceGridX = gridX;
    m_itemInspectOverlay.sourceGridY = gridY;
    m_itemInspectOverlay.sourceX = itemRect.x;
    m_itemInspectOverlay.sourceY = itemRect.y;
    m_itemInspectOverlay.sourceWidth = itemRect.width;
    m_itemInspectOverlay.sourceHeight = itemRect.height;
    tryApplyItemInspectSkillInteraction();
}

void OutdoorGameView::tryApplyItemInspectSkillInteraction()
{
    if (!m_itemInspectOverlay.active
        || !m_itemInspectOverlay.hasItemState
        || m_pOutdoorPartyRuntime == nullptr
        || m_pItemTable == nullptr
        || m_itemInspectOverlay.sourceType == ItemInspectSourceType::None)
    {
        return;
    }

    uint64_t interactionKey = static_cast<uint64_t>(m_itemInspectOverlay.objectDescriptionId);
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceMemberIndex + 1) << 16;
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceGridX) << 24;
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceGridY) << 32;
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceEquipmentSlot) << 40;
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceWorldItemIndex) << 44;
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceLootItemIndex) << 48;
    interactionKey ^= static_cast<uint64_t>(m_itemInspectOverlay.sourceType) << 56;

    if (m_itemInspectInteractionLatch && m_itemInspectInteractionKey == interactionKey)
    {
        return;
    }

    m_itemInspectInteractionLatch = true;
    m_itemInspectInteractionKey = interactionKey;

    Party &party = m_pOutdoorPartyRuntime->party();
    const Character *pActiveMember = party.activeMember();
    const ItemDefinition *pItemDefinition = m_pItemTable->get(m_itemInspectOverlay.objectDescriptionId);

    if (pActiveMember == nullptr || pItemDefinition == nullptr)
    {
        return;
    }

    const size_t activeMemberIndex = party.activeMemberIndex();
    bool reactionPlayed = false;
    const auto playSingleReaction =
        [this, activeMemberIndex, &reactionPlayed](SpeechId speechId)
        {
            if (reactionPlayed)
            {
                return;
            }

            playSpeechReaction(activeMemberIndex, speechId, true);
            reactionPlayed = true;
        };

    const auto refreshOverlayItemState =
        [this, &party]()
        {
            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Inventory)
            {
                const Character *pSourceMember = party.member(m_itemInspectOverlay.sourceMemberIndex);

                if (pSourceMember == nullptr)
                {
                    return;
                }

                const InventoryItem *pItem =
                    pSourceMember->inventoryItemAt(m_itemInspectOverlay.sourceGridX, m_itemInspectOverlay.sourceGridY);

                if (pItem != nullptr)
                {
                    m_itemInspectOverlay.itemState = *pItem;
                }
            }
            else if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Equipment)
            {
                const std::optional<InventoryItem> item =
                    party.equippedItem(m_itemInspectOverlay.sourceMemberIndex, m_itemInspectOverlay.sourceEquipmentSlot);

                if (item.has_value())
                {
                    m_itemInspectOverlay.itemState = *item;
                }
            }
            else if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::WorldItem
                && m_pOutdoorWorldRuntime != nullptr)
            {
                const OutdoorWorldRuntime::WorldItemState *pWorldItem =
                    m_pOutdoorWorldRuntime->worldItemState(m_itemInspectOverlay.sourceWorldItemIndex);

                if (pWorldItem != nullptr && !pWorldItem->isGold)
                {
                    m_itemInspectOverlay.itemState = pWorldItem->item;
                }
            }
            else if (m_pOutdoorWorldRuntime != nullptr
                && m_itemInspectOverlay.sourceType == ItemInspectSourceType::Chest)
            {
                const OutdoorWorldRuntime::ChestViewState *pChestView = m_pOutdoorWorldRuntime->activeChestView();

                if (pChestView != nullptr && m_itemInspectOverlay.sourceLootItemIndex < pChestView->items.size())
                {
                    m_itemInspectOverlay.itemState = pChestView->items[m_itemInspectOverlay.sourceLootItemIndex].item;
                }
            }
            else if (m_pOutdoorWorldRuntime != nullptr
                && m_itemInspectOverlay.sourceType == ItemInspectSourceType::Corpse)
            {
                const OutdoorWorldRuntime::CorpseViewState *pCorpseView = m_pOutdoorWorldRuntime->activeCorpseView();

                if (pCorpseView != nullptr && m_itemInspectOverlay.sourceLootItemIndex < pCorpseView->items.size())
                {
                    m_itemInspectOverlay.itemState = pCorpseView->items[m_itemInspectOverlay.sourceLootItemIndex].item;
                }
            }
        };

    const auto forceIdentifyWithoutReaction =
        [this, &party](std::string &statusText) -> bool
        {
            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Inventory)
            {
                return party.identifyMemberInventoryItem(
                    m_itemInspectOverlay.sourceMemberIndex,
                    m_itemInspectOverlay.sourceGridX,
                    m_itemInspectOverlay.sourceGridY,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Equipment)
            {
                return party.identifyEquippedItem(
                    m_itemInspectOverlay.sourceMemberIndex,
                    m_itemInspectOverlay.sourceEquipmentSlot,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::WorldItem
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->identifyWorldItem(
                    m_itemInspectOverlay.sourceWorldItemIndex,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Chest
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->identifyActiveChestItem(
                    m_itemInspectOverlay.sourceLootItemIndex,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Corpse
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->identifyActiveCorpseItem(
                    m_itemInspectOverlay.sourceLootItemIndex,
                    statusText);
            }

            return false;
        };

    const auto tryIdentifyWithSkill =
        [this, &party, activeMemberIndex, pActiveMember](std::string &statusText) -> bool
        {
            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Inventory)
            {
                return party.tryIdentifyMemberInventoryItem(
                    m_itemInspectOverlay.sourceMemberIndex,
                    m_itemInspectOverlay.sourceGridX,
                    m_itemInspectOverlay.sourceGridY,
                    activeMemberIndex,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Equipment)
            {
                return party.tryIdentifyEquippedItem(
                    m_itemInspectOverlay.sourceMemberIndex,
                    m_itemInspectOverlay.sourceEquipmentSlot,
                    activeMemberIndex,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::WorldItem
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->tryIdentifyWorldItem(
                    m_itemInspectOverlay.sourceWorldItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Chest
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->tryIdentifyActiveChestItem(
                    m_itemInspectOverlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Corpse
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->tryIdentifyActiveCorpseItem(
                    m_itemInspectOverlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            return false;
        };

    const auto tryRepairWithSkill =
        [this, &party, activeMemberIndex, pActiveMember](std::string &statusText) -> bool
        {
            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Inventory)
            {
                return party.tryRepairMemberInventoryItem(
                    m_itemInspectOverlay.sourceMemberIndex,
                    m_itemInspectOverlay.sourceGridX,
                    m_itemInspectOverlay.sourceGridY,
                    activeMemberIndex,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Equipment)
            {
                return party.tryRepairEquippedItem(
                    m_itemInspectOverlay.sourceMemberIndex,
                    m_itemInspectOverlay.sourceEquipmentSlot,
                    activeMemberIndex,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::WorldItem
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->tryRepairWorldItem(
                    m_itemInspectOverlay.sourceWorldItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Chest
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->tryRepairActiveChestItem(
                    m_itemInspectOverlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (m_itemInspectOverlay.sourceType == ItemInspectSourceType::Corpse
                && m_pOutdoorWorldRuntime != nullptr)
            {
                return m_pOutdoorWorldRuntime->tryRepairActiveCorpseItem(
                    m_itemInspectOverlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            return false;
        };

    if (!m_itemInspectOverlay.itemState.identified)
    {
        std::string statusText;

        if (!ItemRuntime::requiresIdentification(*pItemDefinition))
        {
            if (forceIdentifyWithoutReaction(statusText))
            {
                refreshOverlayItemState();
            }
        }
        else if (tryIdentifyWithSkill(statusText))
        {
            refreshOverlayItemState();
            const SpeechId speechId =
                pItemDefinition->value < 100 * (static_cast<int>(pActiveMember->level) + 5)
                    ? SpeechId::IdentifyWeakItem
                    : SpeechId::IdentifyGreatItem;
            playSingleReaction(speechId);
        }
        else if (statusText == "Not skilled enough.")
        {
            setStatusBarEvent("Identify failed.");
            playSingleReaction(SpeechId::IdentifyFailItem);
        }
    }

    if (m_itemInspectOverlay.itemState.broken)
    {
        std::string statusText;

        if (tryRepairWithSkill(statusText))
        {
            refreshOverlayItemState();
            playSingleReaction(SpeechId::RepairSuccess);
        }
        else if (statusText == "Not skilled enough.")
        {
            setStatusBarEvent("Repair failed.");
            playSingleReaction(SpeechId::RepairFail);
        }
    }
}

void OutdoorGameView::updateCharacterInspectOverlayState(int width, int height)
{
    m_characterInspectOverlay = {};
    const auto combineResolvedRects =
        [](const ResolvedHudLayoutElement &left, const ResolvedHudLayoutElement &right) -> ResolvedHudLayoutElement
        {
            const float minX = std::min(left.x, right.x);
            const float minY = std::min(left.y, right.y);
            const float maxX = std::max(left.x + left.width, right.x + right.width);
            const float maxY = std::max(left.y + left.height, right.y + right.height);

            return {
                minX,
                minY,
                maxX - minX,
                maxY - minY,
                left.scale
            };
        };
    const auto inflateResolvedRect =
        [](const ResolvedHudLayoutElement &rect, float horizontalPadding, float verticalPadding)
            -> ResolvedHudLayoutElement
        {
            return {
                rect.x - horizontalPadding,
                rect.y - verticalPadding,
                rect.width + horizontalPadding * 2.0f,
                rect.height + verticalPadding * 2.0f,
                rect.scale
            };
        };

    if (width <= 0
        || height <= 0
        || !m_characterScreenOpen
        || m_pOutdoorPartyRuntime == nullptr
        || isAdventurersInnScreenActive()
        || !m_characterInspectTable)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return;
    }

    const Character *pCharacter = selectedCharacterScreenCharacter();

    if (pCharacter == nullptr)
    {
        return;
    }

    if (m_characterPage == CharacterPage::Stats)
    {
        for (const CharacterStatRowDefinition &row : CharacterStatRows)
        {
            const HudLayoutElement *pLabelLayout = HudUiService::findHudLayoutElement(*this, row.pLabelId);
            const HudLayoutElement *pValueLayout = HudUiService::findHudLayoutElement(*this, row.pValueId);

            if (pLabelLayout == nullptr || pValueLayout == nullptr)
            {
                continue;
            }

            const std::optional<ResolvedHudLayoutElement> resolvedLabel = HudUiService::resolveHudLayoutElement(*this, 
                row.pLabelId,
                width,
                height,
                pLabelLayout->width,
                pLabelLayout->height);
            const std::optional<ResolvedHudLayoutElement> resolvedValue = HudUiService::resolveHudLayoutElement(*this, 
                row.pValueId,
                width,
                height,
                pValueLayout->width,
                pValueLayout->height);

            if (!resolvedLabel || !resolvedValue)
            {
                continue;
            }

            const ResolvedHudLayoutElement rowRect =
                inflateResolvedRect(combineResolvedRects(*resolvedLabel, *resolvedValue), 6.0f, 3.0f);

            if (!HudUiService::isPointerInsideResolvedElement(rowRect, mouseX, mouseY))
            {
                continue;
            }

            const StatInspectEntry *pEntry = m_characterInspectTable->getStat(row.pStatName);

            if (pEntry == nullptr || pEntry->description.empty())
            {
                return;
            }

            m_characterInspectOverlay.active = true;
            m_characterInspectOverlay.title = pEntry->name;
            m_characterInspectOverlay.body = pEntry->description;

            if (std::string_view(row.pStatName) == "Experience")
            {
                const std::string supplement = GameMechanics::buildExperienceInspectSupplement(*pCharacter);

                if (!supplement.empty())
                {
                    m_characterInspectOverlay.body += "\n" + supplement;
                }
            }

            m_characterInspectOverlay.sourceX = rowRect.x;
            m_characterInspectOverlay.sourceY = rowRect.y;
            m_characterInspectOverlay.sourceWidth = rowRect.width;
            m_characterInspectOverlay.sourceHeight = rowRect.height;
            return;
        }

        return;
    }

    if (m_characterPage != CharacterPage::Skills)
    {
        return;
    }

    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pCharacter);
    const HudFontHandle *pSkillRowFont = HudUiService::findHudFont(*this, "Lucida");
    const float skillRowHeight = pSkillRowFont != nullptr
        ? static_cast<float>(std::max(1, pSkillRowFont->fontHeight - 3))
        : 11.0f;

    const auto tryShowSkillPopup =
        [this, width, height, mouseX, mouseY, pCharacter, skillRowHeight](
            const char *pRegionId,
            const char *pLevelHeaderId,
            const std::vector<CharacterSkillUiRow> &rows) -> bool
        {
            if (rows.empty())
            {
                return false;
            }

            const HudLayoutElement *pRegionLayout = HudUiService::findHudLayoutElement(*this, pRegionId);
            const HudLayoutElement *pLevelLayout = HudUiService::findHudLayoutElement(*this, pLevelHeaderId);

            if (pRegionLayout == nullptr || pLevelLayout == nullptr)
            {
                return false;
            }

            const std::optional<ResolvedHudLayoutElement> resolvedRegion = HudUiService::resolveHudLayoutElement(*this, 
                pRegionId,
                width,
                height,
                pRegionLayout->width,
                pRegionLayout->height);
            const std::optional<ResolvedHudLayoutElement> resolvedLevelHeader = HudUiService::resolveHudLayoutElement(*this, 
                pLevelHeaderId,
                width,
                height,
                pLevelLayout->width,
                pLevelLayout->height);

            if (!resolvedRegion || !resolvedLevelHeader)
            {
                return false;
            }

            const float rowHeightPixels = skillRowHeight * resolvedRegion->scale;
            const float rowWidth = resolvedLevelHeader->x + resolvedLevelHeader->width - resolvedRegion->x;

            for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
            {
                const CharacterSkillUiRow &row = rows[rowIndex];
                const float rowY = resolvedRegion->y + static_cast<float>(rowIndex) * rowHeightPixels;
                const ResolvedHudLayoutElement rowRect = {
                    resolvedRegion->x,
                    rowY,
                    rowWidth,
                    rowHeightPixels,
                    resolvedRegion->scale
                };

                if (!HudUiService::isPointerInsideResolvedElement(rowRect, mouseX, mouseY))
                {
                    continue;
                }

                const SkillInspectEntry *pEntry =
                    m_characterInspectTable ? m_characterInspectTable->getSkill(row.canonicalName) : nullptr;

                if (pEntry == nullptr || pEntry->description.empty())
                {
                    return false;
                }

                m_characterInspectOverlay.active = true;
                m_characterInspectOverlay.title = pEntry->name;
                m_characterInspectOverlay.body = pEntry->description;
                m_characterInspectOverlay.expert.text = "Expert: " + pEntry->expertDescription;
                m_characterInspectOverlay.expert.availability = skillMasteryAvailability(
                    m_classSkillTable ? &*m_classSkillTable : nullptr,
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Expert);
                m_characterInspectOverlay.expert.visible = !pEntry->expertDescription.empty();
                m_characterInspectOverlay.master.text = "Master: " + pEntry->masterDescription;
                m_characterInspectOverlay.master.availability = skillMasteryAvailability(
                    m_classSkillTable ? &*m_classSkillTable : nullptr,
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Master);
                m_characterInspectOverlay.master.visible = !pEntry->masterDescription.empty();
                m_characterInspectOverlay.grandmaster.text = "Grandmaster: " + pEntry->grandmasterDescription;
                m_characterInspectOverlay.grandmaster.availability = skillMasteryAvailability(
                    m_classSkillTable ? &*m_classSkillTable : nullptr,
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Grandmaster);
                m_characterInspectOverlay.grandmaster.visible = !pEntry->grandmasterDescription.empty();
                m_characterInspectOverlay.sourceX = rowRect.x;
                m_characterInspectOverlay.sourceY = rowRect.y;
                m_characterInspectOverlay.sourceWidth = rowRect.width;
                m_characterInspectOverlay.sourceHeight = rowRect.height;
                return true;
            }

            return false;
        };

    if (tryShowSkillPopup("CharacterSkillsWeaponsListRegion", "CharacterSkillsWeaponsLevelHeader", skillUiData.weaponRows))
    {
        return;
    }

    if (tryShowSkillPopup("CharacterSkillsMagicListRegion", "CharacterSkillsMagicLevelHeader", skillUiData.magicRows))
    {
        return;
    }

    if (tryShowSkillPopup("CharacterSkillsArmorListRegion", "CharacterSkillsArmorLevelHeader", skillUiData.armorRows))
    {
        return;
    }

    tryShowSkillPopup("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows);
}

void OutdoorGameView::updateBuffInspectOverlayState(int width, int height)
{
    m_buffInspectOverlay = {};

    if (width <= 0
        || height <= 0
        || m_pOutdoorPartyRuntime == nullptr
        || !m_showGameplayHud
        || currentHudScreenState() != HudScreenState::Gameplay
        || m_characterScreenOpen
        || hasActiveEventDialog()
        || m_spellbook.active)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & (SDL_BUTTON_RMASK | SDL_BUTTON_LMASK)) == 0 || m_itemInspectOverlay.active)
    {
        return;
    }

    const Party &party = m_pOutdoorPartyRuntime->party();

    struct PartyBuffInspectTarget
    {
        const char *pLayoutId;
        const char *pLabel;
        PartyBuffId buffId;
        bool skullPanel;
    };

    static constexpr PartyBuffInspectTarget BuffTargets[] = {
        {"OutdoorBuffSkull_Torchlight", "Torch Light", PartyBuffId::TorchLight, true},
        {"OutdoorBuffSkull_WizardEye", "Wizard Eye", PartyBuffId::WizardEye, true},
        {"OutdoorBuffSkull_Featherfall", "Feather Fall", PartyBuffId::FeatherFall, true},
        {"OutdoorBuffSkull_Stoneskin", "Stoneskin", PartyBuffId::Stoneskin, true},
        {"OutdoorBuffSkull_DayOfGods", "Day of the Gods", PartyBuffId::DayOfGods, true},
        {"OutdoorBuffSkull_ProtectionFromGods", "Protection from Magic", PartyBuffId::ProtectionFromMagic, true},
        {"OutdoorBuffBody_FireResistance", "Fire Resistance", PartyBuffId::FireResistance, false},
        {"OutdoorBuffBody_WaterResistance", "Water Resistance", PartyBuffId::WaterResistance, false},
        {"OutdoorBuffBody_AirResistance", "Air Resistance", PartyBuffId::AirResistance, false},
        {"OutdoorBuffBody_EarthResistance", "Earth Resistance", PartyBuffId::EarthResistance, false},
        {"OutdoorBuffBody_MindResistance", "Mind Resistance", PartyBuffId::MindResistance, false},
        {"OutdoorBuffBody_BodyResistance", "Body Resistance", PartyBuffId::BodyResistance, false},
        {"OutdoorBuffBody_Shield", "Shield", PartyBuffId::Shield, false},
        {"OutdoorBuffBody_Heroism", "Heroism", PartyBuffId::Heroism, false},
        {"OutdoorBuffBody_Haste", "Haste", PartyBuffId::Haste, false},
        {"OutdoorBuffBody_Immolation", "Immolation", PartyBuffId::Immolation, false},
    };

    const auto populateBuffPanelOverlay =
        [this, &party](bool skullPanel, const ResolvedHudLayoutElement &rect)
        {
            std::string body;

            for (const PartyBuffInspectTarget &target : BuffTargets)
            {
                if (target.skullPanel != skullPanel)
                {
                    continue;
                }

                const PartyBuffState *pBuff = party.partyBuff(target.buffId);

                if (pBuff == nullptr)
                {
                    continue;
                }

                appendPopupBodyLine(
                    body,
                    std::string(target.pLabel) + " - " + formatRemainingDuration(pBuff->remainingSeconds));
            }

            if (body.empty())
            {
                body = "No active buffs";
            }

            m_buffInspectOverlay.active = true;
            m_buffInspectOverlay.title = "Active Buffs";
            m_buffInspectOverlay.body = body;
            m_buffInspectOverlay.sourceX = rect.x;
            m_buffInspectOverlay.sourceY = rect.y;
            m_buffInspectOverlay.sourceWidth = rect.width;
            m_buffInspectOverlay.sourceHeight = rect.height;
        };

    for (const PartyBuffInspectTarget &target : BuffTargets)
    {
        const PartyBuffState *pBuff = party.partyBuff(target.buffId);

        if (pBuff == nullptr)
        {
            continue;
        }

        const HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(*this, target.pLayoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const std::optional<ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(*this, 
            target.pLayoutId,
            width,
            height,
            pLayout->width,
            pLayout->height);

        if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, mouseX, mouseY))
        {
            continue;
        }

        populateBuffPanelOverlay(target.skullPanel, *resolved);
        return;
    }

    struct BuffPanelTarget
    {
        const char *pLayoutId;
        const char *pTitle;
        bool skullPanel;
    };

    static constexpr BuffPanelTarget PanelTargets[] = {
        {"OutdoorBuffSkullPanel", "Skull Buffs", true},
        {"OutdoorBuffBodyPanel", "Body Buffs", false},
    };

    for (const BuffPanelTarget &panelTarget : PanelTargets)
    {
        const HudLayoutElement *pPanelLayout = HudUiService::findHudLayoutElement(*this, panelTarget.pLayoutId);

        if (pPanelLayout == nullptr)
        {
            continue;
        }

        const std::optional<ResolvedHudLayoutElement> resolvedPanel = HudUiService::resolveHudLayoutElement(*this, 
            panelTarget.pLayoutId,
            width,
            height,
            pPanelLayout->width,
            pPanelLayout->height);

        if (!resolvedPanel || !HudUiService::isPointerInsideResolvedElement(*resolvedPanel, mouseX, mouseY))
        {
            continue;
        }

        populateBuffPanelOverlay(panelTarget.skullPanel, *resolvedPanel);
        return;
    }
}

void OutdoorGameView::updateCharacterDetailOverlayState(int width, int height)
{
    m_characterDetailOverlay = {};

    if (width <= 0 || height <= 0 || m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0
        || m_itemInspectOverlay.active
        || m_characterInspectOverlay.active
        || m_buffInspectOverlay.active
        || m_spellInspectOverlay.active
        || hasActiveEventDialog()
        || m_spellbook.active)
    {
        return;
    }

    const Party &party = m_pOutdoorPartyRuntime->party();
    const Character *pCharacter = nullptr;
    std::optional<ResolvedHudLayoutElement> sourceRect;

    if (m_characterScreenOpen)
    {
        pCharacter = party.activeMember();
        const HudLayoutElement *pDollLayout = HudUiService::findHudLayoutElement(*this, "CharacterDollPanel");

        if (pCharacter != nullptr && pDollLayout != nullptr)
        {
            sourceRect = HudUiService::resolveHudLayoutElement(*this, 
                "CharacterDollPanel",
                width,
                height,
                pDollLayout->width,
                pDollLayout->height);
        }
    }
    else if (currentHudScreenState() == HudScreenState::Gameplay)
    {
        const std::optional<size_t> memberIndex = resolvePartyPortraitIndexAtPoint(width, height, mouseX, mouseY);

        if (memberIndex)
        {
            pCharacter = party.member(*memberIndex);
            sourceRect = resolvePartyPortraitRect(width, height, *memberIndex);
        }
    }

    if (pCharacter == nullptr || !sourceRect || !HudUiService::isPointerInsideResolvedElement(*sourceRect, mouseX, mouseY))
    {
        return;
    }

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(*pCharacter, m_pItemTable);
    std::string body;

    appendPopupBodyLine(body, "Condition: " + summary.conditionText);
    appendPopupBodyLine(
        body,
        "HP " + std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum)
            + "   SP " + std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum));
    appendPopupBodyLine(
        body,
        "AC " + std::to_string(summary.armorClass.actual)
            + "   Level " + std::to_string(summary.level.actual)
            + "   Exp " + summary.experienceText);
    appendPopupBodyLine(
        body,
        "Resists: F" + (summary.fireResistance.infinite ? std::string("Imm") : std::to_string(summary.fireResistance.actual))
            + " A" + (summary.airResistance.infinite ? std::string("Imm") : std::to_string(summary.airResistance.actual))
            + " W" + (summary.waterResistance.infinite ? std::string("Imm") : std::to_string(summary.waterResistance.actual))
            + " E" + (summary.earthResistance.infinite ? std::string("Imm") : std::to_string(summary.earthResistance.actual))
            + " M" + (summary.mindResistance.infinite ? std::string("Imm") : std::to_string(summary.mindResistance.actual))
            + " B" + (summary.bodyResistance.infinite ? std::string("Imm") : std::to_string(summary.bodyResistance.actual)));

    std::string buffsLine;

    struct CharacterBuffInspectLine
    {
        const char *pLabel;
        CharacterBuffId buffId;
    };

    static constexpr CharacterBuffInspectLine CharacterBuffLines[] = {
        {"Bless", CharacterBuffId::Bless},
        {"Fate", CharacterBuffId::Fate},
        {"Preservation", CharacterBuffId::Preservation},
        {"Regeneration", CharacterBuffId::Regeneration},
        {"Hammerhands", CharacterBuffId::Hammerhands},
        {"Pain Reflection", CharacterBuffId::PainReflection},
        {"Fire Aura", CharacterBuffId::FireAura},
        {"Vampiric Weapon", CharacterBuffId::VampiricWeapon},
        {"Mistform", CharacterBuffId::Mistform},
        {"Glamour", CharacterBuffId::Glamour},
    };

    const size_t memberIndex = static_cast<size_t>(pCharacter - party.members().data());

    for (const CharacterBuffInspectLine &buffLine : CharacterBuffLines)
    {
        const CharacterBuffState *pBuff = party.characterBuff(memberIndex, buffLine.buffId);

        if (pBuff == nullptr)
        {
            continue;
        }

        if (!buffsLine.empty())
        {
            buffsLine += ", ";
        }

        buffsLine += std::string(buffLine.pLabel) + " " + formatRemainingDuration(pBuff->remainingSeconds);
    }

    appendPopupBodyLine(body, "Buffs: " + (buffsLine.empty() ? std::string("None") : buffsLine));
    appendPopupBodyLine(
        body,
        "Attack " + std::to_string(summary.combat.attack)
            + "   Shoot " + (summary.combat.shoot ? std::to_string(*summary.combat.shoot) : std::string("N/A")));

    m_characterDetailOverlay.active = true;
    m_characterDetailOverlay.title = pCharacter->name.empty()
        ? ("Member " + std::to_string(memberIndex + 1))
        : pCharacter->name;
    m_characterDetailOverlay.body = body;
    m_characterDetailOverlay.sourceX = sourceRect->x;
    m_characterDetailOverlay.sourceY = sourceRect->y;
    m_characterDetailOverlay.sourceWidth = sourceRect->width;
    m_characterDetailOverlay.sourceHeight = sourceRect->height;
}

bool OutdoorGameView::isOpaqueHudPixelAtPoint(const RenderedInspectableHudItem &item, float x, float y) const
{
    if (item.textureName.empty()
        || item.width <= 0.0f
        || item.height <= 0.0f
        || x < item.x
        || x >= item.x + item.width
        || y < item.y
        || y >= item.y + item.height)
    {
        return false;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        const_cast<OutdoorGameView *>(this)->loadHudBitmapPixelsBgraCached(item.textureName, textureWidth, textureHeight);

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        return true;
    }

    const float normalizedX = std::clamp((x - item.x) / item.width, 0.0f, 0.999999f);
    const float normalizedY = std::clamp((y - item.y) / item.height, 0.0f, 0.999999f);
    const int pixelX = std::clamp(static_cast<int>(normalizedX * textureWidth), 0, textureWidth - 1);
    const int pixelY = std::clamp(static_cast<int>(normalizedY * textureHeight), 0, textureHeight - 1);
    const size_t pixelOffset =
        (static_cast<size_t>(pixelY) * static_cast<size_t>(textureWidth) + static_cast<size_t>(pixelX)) * 4;

    if (pixelOffset + 3 >= pixels->size())
    {
        return false;
    }

    return (*pixels)[pixelOffset + 3] > 0;
}

std::string OutdoorGameView::resolveEquippedItemHudTextureName(
    const ItemDefinition &itemDefinition,
    uint32_t dollTypeId,
    bool hasRightHandWeapon,
    EquipmentSlot slot) const
{
    if (!isBodyEquipmentVisualSlot(slot))
    {
        return itemDefinition.iconName;
    }

    std::vector<std::string> candidateSuffixes;

    switch (dollTypeId)
    {
        case 0:
            candidateSuffixes = hasRightHandWeapon
                ? std::vector<std::string>{"v1", "v1a"}
                : std::vector<std::string>{"v1a", "v1"};
            break;

        case 1:
            candidateSuffixes = hasRightHandWeapon
                ? std::vector<std::string>{"v2", "v2a"}
                : std::vector<std::string>{"v2a", "v2"};
            break;

        case 2:
            candidateSuffixes = {usesAlternateCloakBeltEquippedVariant(slot) ? "v1" : "v3"};
            break;

        case 3:
            candidateSuffixes = {usesAlternateCloakBeltEquippedVariant(slot) ? "v1" : "v4"};
            break;

        default:
            break;
    }

    for (const std::string &suffix : candidateSuffixes)
    {
        const std::string candidateName = itemDefinition.iconName + suffix;
        const std::optional<std::string> candidatePath =
            const_cast<OutdoorGameView *>(this)->findCachedAssetPath("Data/icons", candidateName + ".bmp");

        if (candidatePath)
        {
            return candidateName;
        }
    }

    return itemDefinition.iconName;
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolveCharacterEquipmentRenderRect(
    const OutdoorGameView::HudLayoutElement &layout,
    const ItemDefinition &itemDefinition,
    const OutdoorGameView::HudTextureHandle &texture,
    const CharacterDollTypeEntry *pCharacterDollType,
    EquipmentSlot slot,
    int screenWidth,
    int screenHeight) const
{
    const float fallbackWidth = layout.width > 0.0f ? layout.width : static_cast<float>(texture.width);
    const float fallbackHeight = layout.height > 0.0f ? layout.height : static_cast<float>(texture.height);
    const std::optional<ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(*this, 
        layout.id,
        screenWidth,
        screenHeight,
        fallbackWidth,
        fallbackHeight);

    if (!resolved)
    {
        return std::nullopt;
    }

    const float iconWidth = static_cast<float>(texture.width) * resolved->scale;
    const float iconHeight = static_cast<float>(texture.height) * resolved->scale;

    if (isBodyEquipmentVisualSlot(slot))
    {
        const ItemEquipPosEntry *pEntry =
            m_pItemEquipPosTable != nullptr ? m_pItemEquipPosTable->get(itemDefinition.itemId) : nullptr;
        const uint32_t dollTypeId = pCharacterDollType != nullptr ? pCharacterDollType->id : 0;
        int offsetX = 0;
        int offsetY = 0;

        if (pEntry != nullptr && dollTypeId < pEntry->xByDollType.size())
        {
            offsetX = pEntry->xByDollType[dollTypeId];
            offsetY = pEntry->yByDollType[dollTypeId];
        }

        ResolvedHudLayoutElement rect = {};
        rect.x = std::round(resolved->x + static_cast<float>(offsetX) * resolved->scale);
        rect.y = std::round(resolved->y + static_cast<float>(offsetY) * resolved->scale);
        rect.width = iconWidth;
        rect.height = iconHeight;
        rect.scale = resolved->scale;
        return rect;
    }

    if (slot == EquipmentSlot::Bow)
    {
        ResolvedHudLayoutElement rect = {};
        rect.x = std::round(
            resolved->x + static_cast<float>(pCharacterDollType != nullptr ? pCharacterDollType->bowOffsetX : 0)
            * resolved->scale - iconWidth * 0.5f);
        rect.y = std::round(
            resolved->y + static_cast<float>(pCharacterDollType != nullptr ? pCharacterDollType->bowOffsetY : 0)
            * resolved->scale - iconHeight * 0.5f);
        rect.width = iconWidth;
        rect.height = iconHeight;
        rect.scale = resolved->scale;
        return rect;
    }

    if (slot == EquipmentSlot::MainHand || slot == EquipmentSlot::OffHand)
    {
        int offsetX = 0;
        int offsetY = 0;

        if (pCharacterDollType != nullptr)
        {
            if (slot == EquipmentSlot::MainHand)
            {
                offsetX = pCharacterDollType->rightHandFingersX + pCharacterDollType->mainHandOffsetX - itemDefinition.equipX;
                offsetY = pCharacterDollType->rightHandFingersY + pCharacterDollType->mainHandOffsetY - itemDefinition.equipY;
            }
            else if (itemDefinition.equipStat == "Shield")
            {
                offsetX += pCharacterDollType->leftHandClosedX + pCharacterDollType->shieldX - itemDefinition.equipX;
                offsetY += pCharacterDollType->leftHandClosedY + pCharacterDollType->shieldY - itemDefinition.equipY;
            }
            else
            {
                offsetX = pCharacterDollType->rightHandFingersX + pCharacterDollType->offHandOffsetX - itemDefinition.equipX;
                offsetY = pCharacterDollType->rightHandFingersY + pCharacterDollType->offHandOffsetY - itemDefinition.equipY;
            }
        }

        ResolvedHudLayoutElement rect = {};
        rect.x = std::round(resolved->x + static_cast<float>(offsetX) * resolved->scale);
        rect.y = std::round(resolved->y + static_cast<float>(offsetY) * resolved->scale);
        rect.width = iconWidth;
        rect.height = iconHeight;
        rect.scale = resolved->scale;
        return rect;
    }

    const InventoryItemScreenRect centeredRect = computeCenteredItemRect(
        resolved->x,
        resolved->y,
        resolved->width,
        resolved->height,
        iconWidth,
        iconHeight);
    ResolvedHudLayoutElement rect = {};
    rect.x = centeredRect.x;
    rect.y = centeredRect.y;
    rect.width = centeredRect.width;
    rect.height = centeredRect.height;
    rect.scale = resolved->scale;
    return rect;
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolveChestGridArea(int width, int height) const
{
    if (m_pOutdoorWorldRuntime == nullptr || m_chestTable == std::nullopt || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const OutdoorWorldRuntime::ChestViewState *pChestView = m_pOutdoorWorldRuntime->activeChestView();

    if (pChestView == nullptr)
    {
        return std::nullopt;
    }

    const ChestEntry *pChestEntry = m_chestTable->get(pChestView->chestTypeId);
    const HudLayoutElement *pChestBackgroundLayout = HudUiService::findHudLayoutElement(*this, "ChestBackground");

    if (pChestEntry == nullptr || pChestBackgroundLayout == nullptr || pChestView->gridWidth == 0 || pChestView->gridHeight == 0)
    {
        return std::nullopt;
    }

    const std::optional<ResolvedHudLayoutElement> resolvedBackground = HudUiService::resolveHudLayoutElement(*this, 
        "ChestBackground",
        width,
        height,
        pChestBackgroundLayout->width,
        pChestBackgroundLayout->height);

    if (!resolvedBackground)
    {
        return std::nullopt;
    }

    ResolvedHudLayoutElement resolved = {};
    resolved.x = std::round(resolvedBackground->x + static_cast<float>(pChestEntry->gridOffsetX) * resolvedBackground->scale);
    resolved.y = std::round(resolvedBackground->y + static_cast<float>(pChestEntry->gridOffsetY) * resolvedBackground->scale);
    resolved.width = 32.0f * static_cast<float>(pChestView->gridWidth) * resolvedBackground->scale;
    resolved.height = 32.0f * static_cast<float>(pChestView->gridHeight) * resolvedBackground->scale;
    resolved.scale = resolvedBackground->scale;
    return resolved;
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolveInventoryNestedOverlayGridArea(
    int width,
    int height) const
{
    if (!m_inventoryNestedOverlay.active || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const HudLayoutElement *pGridLayout = HudUiService::findHudLayoutElement(*this, "ChestNestedInventoryGrid");

    if (pGridLayout == nullptr)
    {
        return std::nullopt;
    }

    return HudUiService::resolveHudLayoutElement(*this, 
        "ChestNestedInventoryGrid",
        width,
        height,
        pGridLayout->width,
        pGridLayout->height);
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolveHouseShopOverlayFrame(
    int width,
    int height) const
{
    if (!m_houseShopOverlay.active || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const HudLayoutElement *pFrameLayout = HudUiService::findHudLayoutElement(*this, "DialogueShopOverlayFrame");

    if (pFrameLayout == nullptr)
    {
        return std::nullopt;
    }

    return HudUiService::resolveHudLayoutElement(*this, 
        "DialogueShopOverlayFrame",
        width,
        height,
        pFrameLayout->width,
        pFrameLayout->height);
}

OutdoorGameView::HudScreenState OutdoorGameView::currentHudScreenState() const
{
    if (m_activeEventDialog.isActive)
    {
        return HudScreenState::Dialogue;
    }

    if (m_characterScreenOpen)
    {
        return HudScreenState::Character;
    }

    if (m_spellbook.active)
    {
        return HudScreenState::Spellbook;
    }

    if (m_pOutdoorWorldRuntime != nullptr
        && (m_pOutdoorWorldRuntime->activeChestView() != nullptr || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr))
    {
        return HudScreenState::Chest;
    }

    return HudScreenState::Gameplay;
}

void OutdoorGameView::openSpellbook()
{
    m_gameplayUiController.openSpellbook();
    m_spellbookToggleLatch = false;
    m_spellbookClickLatch = false;
    m_spellbookPressedTarget = {};
    m_lastSpellbookSpellClickTicks = 0;
    m_lastSpellbookClickedSpellId = 0;

    if (m_pGameAudioSystem != nullptr)
    {
        m_pGameAudioSystem->playCommonSound(SoundId::OpenBook, GameAudioSystem::PlaybackGroup::Ui);
    }

    for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
    {
        if (activeMemberHasSpellbookSchool(definition.school))
        {
            m_spellbook.school = definition.school;
            break;
        }
    }

    if (m_pOutdoorPartyRuntime == nullptr || m_pSpellTable == nullptr)
    {
        return;
    }

    const Character *pCaster = m_pOutdoorPartyRuntime->party().activeMember();

    if (pCaster == nullptr || pCaster->quickSpellName.empty())
    {
        return;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findByName(pCaster->quickSpellName);

    if (pSpellEntry == nullptr)
    {
        return;
    }

    const SpellbookSchoolUiDefinition *pDefinition =
        findSpellbookSchoolUiDefinitionForSpellId(static_cast<uint32_t>(pSpellEntry->id));

    if (pDefinition == nullptr)
    {
        return;
    }

    if (activeMemberHasSpellbookSchool(pDefinition->school))
    {
        m_spellbook.school = pDefinition->school;
    }

    m_spellbook.selectedSpellId = 0;
}

void OutdoorGameView::closeSpellbook(const std::string &statusText)
{
    const bool wasActive = m_spellbook.active;
    m_gameplayUiController.closeSpellbook();
    m_spellbookToggleLatch = false;
    m_spellbookClickLatch = false;
    m_spellbookPressedTarget = {};
    m_lastSpellbookSpellClickTicks = 0;
    m_lastSpellbookClickedSpellId = 0;

    if (wasActive && m_pGameAudioSystem != nullptr)
    {
        m_pGameAudioSystem->playCommonSound(SoundId::CloseBook, GameAudioSystem::PlaybackGroup::Ui);
    }

    if (!statusText.empty())
    {
        setStatusBarEvent(statusText);
    }
}

void OutdoorGameView::closeReadableScrollOverlay()
{
    m_gameplayUiController.closeReadableScrollOverlay();
}

void OutdoorGameView::openHouseShopOverlay(uint32_t houseId, HouseShopMode mode)
{
    if (mode == HouseShopMode::None || houseId == 0)
    {
        closeHouseShopOverlay();
        return;
    }

    closeInventoryNestedOverlay();
    m_gameplayUiController.openHouseShopOverlay(houseId, mode);
    m_houseShopClickLatch = false;
    m_houseShopPressedSlotIndex = std::numeric_limits<size_t>::max();
}

void OutdoorGameView::closeHouseShopOverlay()
{
    m_gameplayUiController.closeHouseShopOverlay();
    m_houseShopClickLatch = false;
    m_houseShopPressedSlotIndex = std::numeric_limits<size_t>::max();
}

void OutdoorGameView::beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode)
{
    if (houseId == 0 || mode == HouseBankInputMode::None)
    {
        OutdoorInteractionController::returnToHouseBankMainDialog(*this);
        return;
    }

    closeHouseShopOverlay();
    closeInventoryNestedOverlay();
    m_gameplayUiController.beginHouseBankInput(houseId, mode);
    m_houseBankDigitLatches.fill(false);
    m_houseBankBackspaceLatch = false;
    m_houseBankConfirmLatch = false;
    OutdoorInteractionController::refreshHouseBankInputDialog(*this);
}

void OutdoorGameView::clearHouseBankState()
{
    m_gameplayUiController.clearHouseBankState();
    m_houseBankDigitLatches.fill(false);
    m_houseBankBackspaceLatch = false;
    m_houseBankConfirmLatch = false;
}

void OutdoorGameView::openInventoryNestedOverlay(InventoryNestedOverlayMode mode, uint32_t houseId)
{
    if (mode == InventoryNestedOverlayMode::None)
    {
        closeInventoryNestedOverlay();
        return;
    }

    closeHouseShopOverlay();
    m_gameplayUiController.openInventoryNestedOverlay(mode, houseId);
    m_inventoryNestedOverlayClickLatch = false;
    m_inventoryNestedOverlayItemClickLatch = false;
    m_inventoryNestedOverlayPressedTarget = {};
}

void OutdoorGameView::closeInventoryNestedOverlay()
{
    m_gameplayUiController.closeInventoryNestedOverlay();
    m_inventoryNestedOverlayClickLatch = false;
    m_inventoryNestedOverlayItemClickLatch = false;
    m_inventoryNestedOverlayPressedTarget = {};
}

bool OutdoorGameView::tryBeginQuickSpellCast()
{
    if (m_pOutdoorPartyRuntime == nullptr || m_pOutdoorWorldRuntime == nullptr || m_pSpellTable == nullptr)
    {
        return false;
    }

    if (m_pendingSpellCast.active)
    {
        setStatusBarEvent("Select target for " + m_pendingSpellCast.spellName, 4.0f);
        return false;
    }

    if (m_heldInventoryItem.active || m_characterScreenOpen || m_spellbook.active || hasActiveEventDialog()
        || m_pOutdoorWorldRuntime->activeChestView() != nullptr
        || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr)
    {
        setStatusBarEvent("Finish current action");
        return false;
    }

    Party &party = m_pOutdoorPartyRuntime->party();
    Character *pCaster = party.activeMember();

    if (pCaster == nullptr || !GameMechanics::canSelectInGameplay(*pCaster))
    {
        setStatusBarEvent("Nobody is in condition");
        return false;
    }

    if (pCaster->quickSpellName.empty())
    {
        setStatusBarEvent("No quick spell");
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findByName(pCaster->quickSpellName);

    if (pSpellEntry == nullptr)
    {
        setStatusBarEvent("Unknown quick spell");
        return false;
    }

    return tryCastSpellFromMember(
        party.activeMemberIndex(),
        static_cast<uint32_t>(pSpellEntry->id),
        pSpellEntry->name);
}

bool OutdoorGameView::activeMemberKnowsSpell(uint32_t spellId) const
{
    if (m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    const Character *pMember = m_pOutdoorPartyRuntime->party().activeMember();
    return pMember != nullptr && pMember->knowsSpell(spellId);
}

bool OutdoorGameView::activeMemberHasSpellbookSchool(SpellbookSchool school) const
{
    if (m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(school);
    const Character *pMember = m_pOutdoorPartyRuntime->party().activeMember();

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

void OutdoorGameView::updateReadableScrollOverlayForHeldItem(
    size_t memberIndex,
    const CharacterPointerTarget &pointerTarget,
    bool isLeftMousePressed)
{
    m_readableScrollOverlay = {};

    if (!isLeftMousePressed
        || !m_heldInventoryItem.active
        || m_pItemTable == nullptr
        || m_pOutdoorPartyRuntime == nullptr
        || (pointerTarget.type != CharacterPointerTargetType::EquipmentSlot
            && pointerTarget.type != CharacterPointerTargetType::DollPanel))
    {
        return;
    }

    const InventoryItemUseAction useAction =
        InventoryItemUseRuntime::classifyItemUse(m_heldInventoryItem.item, *m_pItemTable);

    if (useAction != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    Party &party = m_pOutdoorPartyRuntime->party();
    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            party,
            memberIndex,
            m_heldInventoryItem.item,
            *m_pItemTable,
            m_pReadableScrollTable);

    if (!useResult.handled || useResult.action != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    m_readableScrollOverlay.active = true;
    m_readableScrollOverlay.title = useResult.readableTitle;
    m_readableScrollOverlay.body = useResult.readableBody;
}

void OutdoorGameView::triggerPortraitEventFxWithoutSpeech(size_t memberIndex, PortraitFxEventKind kind)
{
    const PortraitFxEventEntry *pEntry = m_portraitFxEventTable.findByKind(kind);

    if (pEntry == nullptr)
    {
        return;
    }

    triggerPortraitFxAnimation(pEntry->animationName, {memberIndex});

    if (pEntry->faceAnimationId.has_value())
    {
        triggerPortraitFaceAnimation(memberIndex, *pEntry->faceAnimationId);
    }

    if (m_pGameAudioSystem == nullptr)
    {
        return;
    }

    switch (kind)
    {
        case PortraitFxEventKind::AwardGain:
            m_pGameAudioSystem->playCommonSound(SoundId::Chimes, GameAudioSystem::PlaybackGroup::Ui);
            break;

        case PortraitFxEventKind::QuestComplete:
        case PortraitFxEventKind::StatIncrease:
            m_pGameAudioSystem->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
            break;

        case PortraitFxEventKind::StatDecrease:
        case PortraitFxEventKind::Disease:
        case PortraitFxEventKind::None:
            break;
    }
}

bool OutdoorGameView::tryCastSpellFromMember(size_t casterMemberIndex, uint32_t spellId, const std::string &spellName)
{
    if (m_pOutdoorPartyRuntime != nullptr)
    {
        const Character *pCaster = m_pOutdoorPartyRuntime->party().member(casterMemberIndex);

        if (pCaster == nullptr || !pCaster->knowsSpell(spellId))
        {
            setStatusBarEvent("Spell not learned");
            return false;
        }
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = casterMemberIndex;
    request.spellId = spellId;
    return tryCastSpellRequest(request, spellName);
}

bool OutdoorGameView::loadPortraitAnimationData(const Engine::AssetFileSystem &assetFileSystem)
{
    m_faceAnimationTable = {};
    m_portraitFrameTable = {};

    const std::optional<std::vector<uint8_t>> portraitFrameBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dpft.bin");

    if (!portraitFrameBytes || !m_portraitFrameTable.loadFromBytes(*portraitFrameBytes))
    {
        return false;
    }

    const std::optional<std::string> faceAnimationText = assetFileSystem.readTextFile("Data/FACE_ANIMATIONS.txt");

    if (!faceAnimationText)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*faceAnimationText);

    if (!parsedTable)
    {
        return false;
    }

    std::vector<std::vector<std::string>> rows;
    rows.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return m_faceAnimationTable.loadFromRows(rows);
}

void OutdoorGameView::updatePartyPortraitAnimations(float deltaSeconds)
{
    OutdoorPresentationController::updatePartyPortraitAnimations(*this, deltaSeconds);
}

void OutdoorGameView::updatePortraitAnimation(Character &member, size_t memberIndex, uint32_t deltaTicks)
{
    OutdoorPresentationController::updatePortraitAnimation(*this, member, memberIndex, deltaTicks);
}

void OutdoorGameView::playPortraitExpression(
    size_t memberIndex,
    PortraitId portraitId,
    std::optional<uint32_t> durationTicks)
{
    OutdoorPresentationController::playPortraitExpression(*this, memberIndex, portraitId, durationTicks);
}

void OutdoorGameView::triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId)
{
    OutdoorPresentationController::triggerPortraitFaceAnimation(*this, memberIndex, animationId);
}

void OutdoorGameView::triggerPortraitFaceAnimationForAllLivingMembers(FaceAnimationId animationId)
{
    OutdoorPresentationController::triggerPortraitFaceAnimationForAllLivingMembers(*this, animationId);
}

uint32_t OutdoorGameView::defaultPortraitAnimationLengthTicks(PortraitId portraitId) const
{
    const int32_t animationLengthTicks = m_portraitFrameTable.animationLengthTicks(portraitId);

    if (animationLengthTicks > 0)
    {
        return static_cast<uint32_t>(animationLengthTicks);
    }

    return 48u;
}

bool OutdoorGameView::isAdventurersInnCharacterSourceActive() const
{
    return m_characterScreenOpen && m_characterScreenSource == CharacterScreenSource::AdventurersInn;
}

bool OutdoorGameView::isAdventurersInnScreenActive() const
{
    return isAdventurersInnCharacterSourceActive() && m_adventurersInnRosterOverlayOpen;
}

bool OutdoorGameView::isReadOnlyAdventurersInnCharacterViewActive() const
{
    return isAdventurersInnCharacterSourceActive() && !m_adventurersInnRosterOverlayOpen;
}

const Character *OutdoorGameView::selectedCharacterScreenCharacter() const
{
    if (m_pOutdoorPartyRuntime == nullptr)
    {
        return nullptr;
    }

    const Party &party = m_pOutdoorPartyRuntime->party();

    if (m_characterScreenSource == CharacterScreenSource::AdventurersInn)
    {
        return party.adventurersInnCharacter(m_characterScreenSourceIndex);
    }

    return party.activeMember();
}

Character *OutdoorGameView::selectedCharacterScreenCharacter()
{
    if (m_pOutdoorPartyRuntime == nullptr)
    {
        return nullptr;
    }

    Party &party = m_pOutdoorPartyRuntime->party();

    if (m_characterScreenSource == CharacterScreenSource::AdventurersInn)
    {
        return party.adventurersInnCharacter(m_characterScreenSourceIndex);
    }

    return party.activeMember();
}

const AdventurersInnMember *OutdoorGameView::selectedAdventurersInnMember() const
{
    if (m_pOutdoorPartyRuntime == nullptr || m_characterScreenSource != CharacterScreenSource::AdventurersInn)
    {
        return nullptr;
    }

    return m_pOutdoorPartyRuntime->party().adventurersInnMember(m_characterScreenSourceIndex);
}

AdventurersInnMember *OutdoorGameView::selectedAdventurersInnMember()
{
    if (m_pOutdoorPartyRuntime == nullptr || m_characterScreenSource != CharacterScreenSource::AdventurersInn)
    {
        return nullptr;
    }

    return m_pOutdoorPartyRuntime->party().adventurersInnMember(m_characterScreenSourceIndex);
}

std::string OutdoorGameView::resolvePortraitTextureName(const Character &character) const
{
    if (character.portraitState == PortraitId::Eradicated)
    {
        return "ERADCATE";
    }

    if (character.portraitState == PortraitId::Dead)
    {
        return "DEAD";
    }

    if (character.portraitState == PortraitId::Normal)
    {
        const std::string basePortraitTextureName = portraitTextureNameForPictureFrame(character.portraitPictureId, 1);

        if (!basePortraitTextureName.empty())
        {
            return basePortraitTextureName;
        }

        return character.portraitTextureName;
    }

    const PortraitFrameEntry *pFrame = m_portraitFrameTable.getFrame(character.portraitState, character.portraitElapsedTicks);

    if (pFrame != nullptr && pFrame->textureIndex > 0)
    {
        return portraitTextureNameForPictureFrame(character.portraitPictureId, pFrame->textureIndex);
    }

    return character.portraitTextureName;
}

bool OutdoorGameView::loadPortraitFxData(const Engine::AssetFileSystem &assetFileSystem)
{
    m_iconFrameTable = {};
    m_spellFxTable = {};
    m_portraitFxEventTable = {};

    const std::optional<std::vector<uint8_t>> iconFrameBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dift.bin");

    if (!iconFrameBytes || !m_iconFrameTable.loadFromBytes(*iconFrameBytes))
    {
        return false;
    }

    const std::optional<std::string> spellFxText = assetFileSystem.readTextFile("Data/SPELL_FX.txt");
    const std::optional<std::string> portraitFxEventText =
        assetFileSystem.readTextFile("Data/PORTRAIT_FX_EVENTS.txt");

    if (!spellFxText || !portraitFxEventText)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedSpellFxTable = Engine::TextTable::parseTabSeparated(*spellFxText);
    const std::optional<Engine::TextTable> parsedPortraitFxEventTable =
        Engine::TextTable::parseTabSeparated(*portraitFxEventText);

    if (!parsedSpellFxTable || !parsedPortraitFxEventTable)
    {
        return false;
    }

    std::vector<std::vector<std::string>> spellFxRows;
    spellFxRows.reserve(parsedSpellFxTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedSpellFxTable->getRowCount(); ++rowIndex)
    {
        spellFxRows.push_back(parsedSpellFxTable->getRow(rowIndex));
    }

    std::vector<std::vector<std::string>> portraitFxEventRows;
    portraitFxEventRows.reserve(parsedPortraitFxEventTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedPortraitFxEventTable->getRowCount(); ++rowIndex)
    {
        portraitFxEventRows.push_back(parsedPortraitFxEventTable->getRow(rowIndex));
    }

    return m_spellFxTable.loadFromRows(spellFxRows)
        && m_portraitFxEventTable.loadFromRows(portraitFxEventRows);
}

bool OutdoorGameView::triggerPortraitFxAnimation(
    const std::string &animationName,
    const std::vector<size_t> &memberIndices)
{
    return OutdoorPresentationController::triggerPortraitFxAnimation(*this, animationName, memberIndices);
}

void OutdoorGameView::triggerPortraitSpellFx(const PartySpellCastResult &result)
{
    OutdoorPresentationController::triggerPortraitSpellFx(*this, result);
}

void OutdoorGameView::triggerPortraitEventFx(const EventRuntimeState::PortraitFxRequest &request)
{
    OutdoorPresentationController::triggerPortraitEventFx(*this, request);
}

void OutdoorGameView::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    OutdoorPresentationController::playSpeechReaction(*this, memberIndex, speechId, triggerFaceAnimation);
}

bool OutdoorGameView::canPlaySpeechReaction(size_t memberIndex, SpeechId speechId, uint32_t nowTicks)
{
    return OutdoorPresentationController::canPlaySpeechReaction(*this, memberIndex, speechId, nowTicks);
}

void OutdoorGameView::consumePendingPartyAudioRequests()
{
    OutdoorPresentationController::consumePendingPartyAudioRequests(*this);
}

void OutdoorGameView::consumePendingWorldAudioEvents()
{
    OutdoorPresentationController::consumePendingWorldAudioEvents(*this);
}

void OutdoorGameView::updateFootstepAudio(float deltaSeconds)
{
    OutdoorPresentationController::updateFootstepAudio(*this, deltaSeconds);
}

void OutdoorGameView::consumePendingPortraitEventFxRequests()
{
    OutdoorPresentationController::consumePendingPortraitEventFxRequests(*this);
}

void OutdoorGameView::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    OutdoorPresentationController::renderPortraitFx(*this, memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
}

void OutdoorGameView::submitHudTexturedQuad(
    const HudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight) const
{
    if (!bgfx::isValid(texture.textureHandle)
        || quadWidth <= 0.0f
        || quadHeight <= 0.0f
        || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
    TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
    pVertices[0] = {x, y, 0.0f, 0.0f, 0.0f};
    pVertices[1] = {x + quadWidth, y, 0.0f, 1.0f, 0.0f};
    pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
    pVertices[3] = {x, y, 0.0f, 0.0f, 0.0f};
    pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
    pVertices[5] = {x, y + quadHeight, 0.0f, 0.0f, 1.0f};

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer);
    bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
}

bool OutdoorGameView::tryCastSpellRequest(const PartySpellCastRequest &request, const std::string &spellName)
{
    if (m_pOutdoorPartyRuntime == nullptr || m_pOutdoorWorldRuntime == nullptr || m_pSpellTable == nullptr)
    {
        return false;
    }

    Party &party = m_pOutdoorPartyRuntime->party();
    Character *pCaster = party.member(request.casterMemberIndex);

    if (pCaster == nullptr || !GameMechanics::canSelectInGameplay(*pCaster))
    {
        setStatusBarEvent("Nobody is in condition");
        return false;
    }

    const PartySpellCastResult result =
        PartySpellSystem::castSpell(party, *m_pOutdoorPartyRuntime, *m_pOutdoorWorldRuntime, *m_pSpellTable, request);

    if (result.succeeded())
    {
        triggerPortraitFaceAnimation(request.casterMemberIndex, FaceAnimationId::CastSpell);
        playSpeechReaction(request.casterMemberIndex, SpeechId::CastSpell, false);
        triggerPortraitSpellFx(result);

        if (m_pGameAudioSystem != nullptr)
        {
            const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(request.spellId));

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

        clearPendingSpellCast("Cast " + spellName);
        return true;
    }

    if (result.status == PartySpellCastStatus::NeedActorTarget
        || result.status == PartySpellCastStatus::NeedCharacterTarget
        || result.status == PartySpellCastStatus::NeedActorOrCharacterTarget
        || result.status == PartySpellCastStatus::NeedGroundPoint)
    {
        m_pendingSpellCast.active = true;
        m_pendingSpellCast.casterMemberIndex = request.casterMemberIndex;
        m_pendingSpellCast.spellId = request.spellId;
        m_pendingSpellCast.skillLevelOverride = request.skillLevelOverride;
        m_pendingSpellCast.skillMasteryOverride = request.skillMasteryOverride;
        m_pendingSpellCast.spendMana = request.spendMana;
        m_pendingSpellCast.applyRecovery = request.applyRecovery;
        m_pendingSpellCast.targetKind = result.targetKind;
        m_pendingSpellCast.spellName = spellName;
        m_pendingSpellTargetClickLatch = false;
        m_cachedHoverInspectHitValid = false;
        setStatusBarEvent("Select target for " + spellName, 4.0f);
        return true;
    }

    triggerPortraitFaceAnimation(request.casterMemberIndex, FaceAnimationId::SpellFailed);
    if (m_pGameAudioSystem != nullptr)
    {
        m_pGameAudioSystem->playCommonSound(SoundId::SpellFail, GameAudioSystem::PlaybackGroup::Ui);
    }
    setStatusBarEvent(result.statusText.empty() ? "Spell failed" : result.statusText);
    return false;
}

bool OutdoorGameView::tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen)
{
    if (!m_heldInventoryItem.active || m_pItemTable == nullptr || m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    Party &party = m_pOutdoorPartyRuntime->party();
    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            party,
            memberIndex,
            m_heldInventoryItem.item,
            *m_pItemTable,
            m_pReadableScrollTable);

    if (!useResult.handled)
    {
        return false;
    }

    if (useResult.action == InventoryItemUseAction::CastScroll)
    {
        if (m_pSpellTable == nullptr)
        {
            return false;
        }

        const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(useResult.spellId));

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

        if (!tryCastSpellRequest(request, pSpellEntry->name))
        {
            return true;
        }

        if (useResult.consumed)
        {
            m_heldInventoryItem = {};
        }
    }
    else if (useResult.action == InventoryItemUseAction::ReadMessageScroll)
    {
        m_readableScrollOverlay.active = true;
        m_readableScrollOverlay.title = useResult.readableTitle;
        m_readableScrollOverlay.body = useResult.readableBody;
    }
    else
    {
        if (useResult.consumed)
        {
            m_heldInventoryItem = {};
        }

        if (useResult.action == InventoryItemUseAction::ConsumePotion
            && useResult.consumed
            && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Drink, GameAudioSystem::PlaybackGroup::Ui);
            triggerPortraitFaceAnimation(memberIndex, FaceAnimationId::DrinkPotion);
        }

        if (useResult.action == InventoryItemUseAction::UseHorseshoe && useResult.consumed)
        {
            triggerPortraitEventFxWithoutSpeech(memberIndex, PortraitFxEventKind::QuestComplete);
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

    if (!keepCharacterScreenOpen)
    {
        m_characterScreenOpen = false;
        m_characterDollJewelryOverlayOpen = false;
    }

    return true;
}

void OutdoorGameView::clearPendingSpellCast(const std::string &statusText)
{
    m_pendingSpellCast = {};
    m_pendingSpellTargetClickLatch = false;

    if (!statusText.empty())
    {
        setStatusBarEvent(statusText);
    }
}

bool OutdoorGameView::tryResolvePendingSpellCast(
    const InspectHit &actorInspectHit,
    const std::optional<size_t> &portraitMemberIndex)
{
    if (!m_pendingSpellCast.active || m_pOutdoorPartyRuntime == nullptr || m_pOutdoorWorldRuntime == nullptr
        || m_pSpellTable == nullptr)
    {
        return false;
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = m_pendingSpellCast.casterMemberIndex;
    request.spellId = m_pendingSpellCast.spellId;
    request.skillLevelOverride = m_pendingSpellCast.skillLevelOverride;
    request.skillMasteryOverride = m_pendingSpellCast.skillMasteryOverride;
    request.spendMana = m_pendingSpellCast.spendMana;
    request.applyRecovery = m_pendingSpellCast.applyRecovery;
    const bool actorTargetAllowed =
        m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Actor
        || m_pendingSpellCast.targetKind == PartySpellCastTargetKind::ActorOrCharacter;
    const bool characterTargetAllowed =
        m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Character
        || m_pendingSpellCast.targetKind == PartySpellCastTargetKind::ActorOrCharacter;
    const std::optional<size_t> runtimeActorIndex =
        actorTargetAllowed && actorInspectHit.kind == "actor"
            ? resolveRuntimeActorIndexForInspectHit(actorInspectHit)
            : std::nullopt;

    if (runtimeActorIndex)
    {
        request.targetActorIndex = runtimeActorIndex;
    }

    if (characterTargetAllowed && portraitMemberIndex)
    {
        request.targetCharacterIndex = *portraitMemberIndex;
    }

    if (m_pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint)
    {
        const std::optional<bx::Vec3> groundTargetPoint = resolvePendingSpellGroundTargetPoint(actorInspectHit);

        if (groundTargetPoint)
        {
            request.hasTargetPoint = true;
            request.targetX = groundTargetPoint->x;
            request.targetY = groundTargetPoint->y;
            request.targetZ = groundTargetPoint->z;
        }
    }

    const auto setPendingTargetPrompt =
        [this]()
        {
            const std::string prompt =
                m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Actor
                    ? "Select actor for "
                    : m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Character
                    ? "Select character for "
                    : m_pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint
                    ? "Select ground point for "
                    : "Select target for ";
            setStatusBarEvent(prompt + m_pendingSpellCast.spellName, 4.0f);
        };

    if (m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Actor && !request.targetActorIndex)
    {
        setPendingTargetPrompt();
        return false;
    }

    if (m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Character && !request.targetCharacterIndex)
    {
        setPendingTargetPrompt();
        return false;
    }

    if (m_pendingSpellCast.targetKind == PartySpellCastTargetKind::ActorOrCharacter
        && !request.targetActorIndex
        && !request.targetCharacterIndex)
    {
        setPendingTargetPrompt();
        return false;
    }

    if (m_pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint && !request.hasTargetPoint)
    {
        setPendingTargetPrompt();
        return false;
    }

    const PartySpellCastResult result = PartySpellSystem::castSpell(
        m_pOutdoorPartyRuntime->party(),
        *m_pOutdoorPartyRuntime,
        *m_pOutdoorWorldRuntime,
        *m_pSpellTable,
        request);

    if (!result.succeeded())
    {
        if (result.status == PartySpellCastStatus::NeedActorTarget
            || result.status == PartySpellCastStatus::NeedCharacterTarget
            || result.status == PartySpellCastStatus::NeedActorOrCharacterTarget)
        {
            setPendingTargetPrompt();
        }
        else
        {
            triggerPortraitFaceAnimation(request.casterMemberIndex, FaceAnimationId::SpellFailed);
            if (m_pGameAudioSystem != nullptr)
            {
                m_pGameAudioSystem->playCommonSound(SoundId::SpellFail, GameAudioSystem::PlaybackGroup::Ui);
            }
            setStatusBarEvent(result.statusText.empty() ? "Spell failed" : result.statusText);
        }

        return false;
    }

    triggerPortraitFaceAnimation(request.casterMemberIndex, FaceAnimationId::CastSpell);
    playSpeechReaction(request.casterMemberIndex, SpeechId::CastSpell, false);
    triggerPortraitSpellFx(result);

    if (m_pGameAudioSystem != nullptr)
    {
        const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(request.spellId));

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

    clearPendingSpellCast("Cast " + m_pendingSpellCast.spellName);
    return true;
}

std::optional<bx::Vec3> OutdoorGameView::resolvePendingSpellGroundTargetPoint(const InspectHit &inspectHit) const
{
    if (inspectHit.hasHit)
    {
        if (inspectHit.kind == "actor")
        {
            const std::optional<size_t> runtimeActorIndex = resolveRuntimeActorIndexForInspectHit(inspectHit);
            const OutdoorWorldRuntime::MapActorState *pActor =
                runtimeActorIndex && m_pOutdoorWorldRuntime != nullptr
                    ? m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex)
                    : nullptr;

            if (pActor != nullptr)
            {
                return bx::Vec3 {
                    pActor->preciseX,
                    pActor->preciseY,
                    pActor->preciseZ + std::max(48.0f, static_cast<float>(pActor->height) * 0.6f)
                };
            }
        }

        return bx::Vec3 {inspectHit.hitX, inspectHit.hitY, inspectHit.hitZ};
    }

    if (m_outdoorMapData.has_value())
    {
        const bx::Vec3 rayOrigin = {
            m_cameraTargetX,
            m_cameraTargetY,
            m_cameraTargetZ
        };
        const float cosPitch = std::cos(m_cameraPitchRadians);
        const bx::Vec3 rayDirection = {
            std::cos(m_cameraYawRadians) * cosPitch,
            -std::sin(m_cameraYawRadians) * cosPitch,
            std::sin(m_cameraPitchRadians)
        };
        const std::optional<float> terrainDistance =
            intersectOutdoorTerrainRay(*m_outdoorMapData, rayOrigin, rayDirection);

        if (terrainDistance)
        {
            return bx::Vec3 {
                rayOrigin.x + rayDirection.x * *terrainDistance,
                rayOrigin.y + rayDirection.y * *terrainDistance,
                rayOrigin.z + rayDirection.z * *terrainDistance
            };
        }
    }

    return std::nullopt;
}

void OutdoorGameView::renderPendingSpellTargetingOverlay(int width, int height) const
{
    if (!m_pendingSpellCast.active
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

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
        bgfx::getCaps()->homogeneousDepth
    );
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    SDL_GetMouseState(&mouseX, &mouseY);
    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
    const float armLength = std::round(10.0f * overlayScale);
    const float armGap = std::round(4.0f * overlayScale);
    const float stroke = std::max(1.0f, std::round(2.0f * overlayScale));
    const uint32_t crosshairColor = packHudColorAbgr(255, 255, 155);
    const uint32_t shadowColor = 0xc0000000u;

    const HudTextureHandle *pCrosshairTexture = HudUiService::ensureSolidHudTextureLoaded(
        const_cast<OutdoorGameView &>(*this),
        "__spell_target_crosshair__",
        crosshairColor);
    const HudTextureHandle *pShadowTexture = HudUiService::ensureSolidHudTextureLoaded(
        const_cast<OutdoorGameView &>(*this),
        "__spell_target_shadow__",
        shadowColor);

    if (pCrosshairTexture == nullptr || pShadowTexture == nullptr)
    {
        return;
    }

    const auto submitTexturedQuad =
        [this](const HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || quadWidth <= 0.0f
                || quadHeight <= 0.0f
                || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
            TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
            pVertices[0] = {x, y, 0.0f, 0.0f, 0.0f};
            pVertices[1] = {x + quadWidth, y, 0.0f, 1.0f, 0.0f};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
            pVertices[3] = {x, y, 0.0f, 0.0f, 0.0f};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
            pVertices[5] = {x, y + quadHeight, 0.0f, 0.0f, 1.0f};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
        };

    const auto submitCrosshairLine =
        [&](float x, float y, float quadWidth, float quadHeight)
        {
            submitTexturedQuad(*pShadowTexture, x + 1.0f, y + 1.0f, quadWidth, quadHeight);
            submitTexturedQuad(*pCrosshairTexture, x, y, quadWidth, quadHeight);
        };

    submitCrosshairLine(mouseX - armGap - armLength, mouseY - stroke * 0.5f, armLength, stroke);
    submitCrosshairLine(mouseX + armGap, mouseY - stroke * 0.5f, armLength, stroke);
    submitCrosshairLine(mouseX - stroke * 0.5f, mouseY - armGap - armLength, stroke, armLength);
    submitCrosshairLine(mouseX - stroke * 0.5f, mouseY + armGap, stroke, armLength);

    const std::string prompt =
        m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Actor
            ? "Select actor for " + m_pendingSpellCast.spellName + "  LMB cast  Esc cancel"
            : m_pendingSpellCast.targetKind == PartySpellCastTargetKind::Character
            ? "Select character for " + m_pendingSpellCast.spellName + "  LMB cast  Esc cancel"
            : m_pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint
            ? "Select ground point for " + m_pendingSpellCast.spellName + "  LMB cast  Esc cancel"
            : "Select target for " + m_pendingSpellCast.spellName + "  LMB cast  Esc cancel";
    HudLayoutElement promptLayout = {};
    promptLayout.fontName = "arrus";
    promptLayout.textColorAbgr = crosshairColor;
    promptLayout.textAlignX = HudTextAlignX::Center;
    promptLayout.textAlignY = HudTextAlignY::Top;
    ResolvedHudLayoutElement promptRect = {};
    promptRect.x = uiViewport.x;
    promptRect.y = uiViewport.y + std::round(18.0f * overlayScale);
    promptRect.width = uiViewport.width;
    promptRect.height = std::round(24.0f * overlayScale);
    promptRect.scale = overlayScale;
    HudUiService::renderLayoutLabel(*this, promptLayout, promptRect, prompt);
}

void OutdoorGameView::renderSpellbookOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderSpellbookOverlay(*this, width, height);
}

void OutdoorGameView::showStatusBarEvent(const std::string &text, float durationSeconds)
{
    setStatusBarEvent(text, durationSeconds);
}

void OutdoorGameView::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_gameplayUiController.setStatusBarEvent(text, durationSeconds);
}

void OutdoorGameView::updateStatusBarEvent(float deltaSeconds)
{
    m_gameplayUiController.updateStatusBarEvent(deltaSeconds);
}

void OutdoorGameView::renderCharacterOverlay(int width, int height, bool renderAboveHud) const
{
    GameplayPartyOverlayRenderer::renderCharacterOverlay(*this, width, height, renderAboveHud);
}

std::optional<size_t> OutdoorGameView::resolveRuntimeActorIndexForInspectHit(const InspectHit &inspectHit) const
{
    if (inspectHit.kind != "actor" || m_pOutdoorWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    if (m_outdoorActorPreviewBillboardSet
        && inspectHit.bModelIndex < m_outdoorActorPreviewBillboardSet->billboards.size())
    {
        const ActorPreviewBillboard &billboard =
            m_outdoorActorPreviewBillboardSet->billboards[inspectHit.bModelIndex];

        if (billboard.runtimeActorIndex != static_cast<size_t>(-1))
        {
            return billboard.runtimeActorIndex;
        }
    }

    return inspectHit.bModelIndex < m_pOutdoorWorldRuntime->mapActorCount()
        ? std::optional<size_t>(inspectHit.bModelIndex)
        : std::nullopt;
}

void OutdoorGameView::updateActorInspectOverlayState(int width, int height)
{
    m_actorInspectOverlay = {};

    if (width <= 0
        || height <= 0
        || m_pOutdoorWorldRuntime == nullptr
        || !m_outdoorMapData.has_value()
        || m_heldInventoryItem.active
        || m_pendingSpellCast.active
        || m_spellbook.active
        || m_characterScreenOpen
        || hasActiveEventDialog())
    {
        return;
    }

    const bool hasActiveLootView =
        m_pOutdoorWorldRuntime->activeChestView() != nullptr || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr;

    if (hasActiveLootView)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return;
    }

    InspectHit inspectHit = {};
    bool hasInspectHit = false;

    if (m_cachedHoverInspectHitValid)
    {
        inspectHit = m_cachedHoverInspectHit;
        hasInspectHit = true;
    }
    else if (!m_inspectMode)
    {
        const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
        const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));
        const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
        float viewMatrix[16] = {};
        float projectionMatrix[16] = {};
        const float cosPitch = std::cos(m_cameraPitchRadians);
        const float sinPitch = std::sin(m_cameraPitchRadians);
        const float cosYaw = std::cos(m_cameraYawRadians);
        const float sinYaw = std::sin(m_cameraYawRadians);
        const bx::Vec3 eye = {
            m_cameraTargetX,
            m_cameraTargetY,
            m_cameraTargetZ
        };
        const bx::Vec3 at = {
            m_cameraTargetX + cosYaw * cosPitch,
            m_cameraTargetY - sinYaw * cosPitch,
            m_cameraTargetZ + sinPitch
        };
        const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
        bx::mtxLookAt(viewMatrix, eye, at, up);
        bx::mtxProj(
            projectionMatrix,
            CameraVerticalFovDegrees,
            aspectRatio,
            0.1f,
            200000.0f,
            bgfx::getCaps()->homogeneousDepth
        );

        const float normalizedMouseX = ((mouseX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY = 1.0f - ((mouseY / static_cast<float>(viewHeight)) * 2.0f);
        float viewProjectionMatrix[16] = {};
        float inverseViewProjectionMatrix[16] = {};
        bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);
        bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
        const bx::Vec3 rayOrigin = bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayTarget = bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
        inspectHit = OutdoorInteractionController::inspectBModelFace(*this, 
            *m_outdoorMapData,
            rayOrigin,
            rayDirection,
            mouseX,
            mouseY,
            width,
            height,
            viewMatrix,
            projectionMatrix,
            OutdoorGameView::DecorationPickMode::HoverInfo);
        hasInspectHit = true;
    }

    if (!hasInspectHit || inspectHit.kind != "actor")
    {
        return;
    }

    const std::optional<size_t> runtimeActorIndex = resolveRuntimeActorIndexForInspectHit(inspectHit);

    if (!runtimeActorIndex)
    {
        return;
    }

    const OutdoorWorldRuntime::MapActorState *pActorState = m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex);

    if (pActorState == nullptr)
    {
        return;
    }

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));
    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 eye = {
        m_cameraTargetX,
        m_cameraTargetY,
        m_cameraTargetZ
    };
    const bx::Vec3 at = {
        m_cameraTargetX + cosYaw * cosPitch,
        m_cameraTargetY - sinYaw * cosPitch,
        m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    bx::mtxLookAt(viewMatrix, eye, at, up);
    bx::mtxProj(
        projectionMatrix,
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        200000.0f,
        bgfx::getCaps()->homogeneousDepth
    );
    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);

    const float halfExtent = static_cast<float>(std::max<uint16_t>(pActorState->radius, 64));
    const float actorHeight = static_cast<float>(std::max<uint16_t>(pActorState->height, 128));
    const float minX = static_cast<float>(pActorState->x) - halfExtent;
    const float maxX = static_cast<float>(pActorState->x) + halfExtent;
    const float minY = static_cast<float>(pActorState->y) - halfExtent;
    const float maxY = static_cast<float>(pActorState->y) + halfExtent;
    const float minZ = static_cast<float>(pActorState->z);
    const float maxZ = static_cast<float>(pActorState->z) + actorHeight;
    const std::array<bx::Vec3, 8> corners = {{
        {minX, minY, minZ},
        {maxX, minY, minZ},
        {minX, maxY, minZ},
        {maxX, maxY, minZ},
        {minX, minY, maxZ},
        {maxX, minY, maxZ},
        {minX, maxY, maxZ},
        {maxX, maxY, maxZ},
    }};

    bool hasProjectedPoint = false;
    float rectMinX = 0.0f;
    float rectMinY = 0.0f;
    float rectMaxX = 0.0f;
    float rectMaxY = 0.0f;

    for (const bx::Vec3 &corner : corners)
    {
        ProjectedPoint projected = {};

        if (!projectWorldPointToScreen(corner, width, height, viewProjectionMatrix, projected))
        {
            continue;
        }

        if (!hasProjectedPoint)
        {
            rectMinX = projected.x;
            rectMinY = projected.y;
            rectMaxX = projected.x;
            rectMaxY = projected.y;
            hasProjectedPoint = true;
            continue;
        }

        rectMinX = std::min(rectMinX, projected.x);
        rectMinY = std::min(rectMinY, projected.y);
        rectMaxX = std::max(rectMaxX, projected.x);
        rectMaxY = std::max(rectMaxY, projected.y);
    }

    if (!hasProjectedPoint)
    {
        return;
    }

    m_actorInspectOverlay.active = true;
    m_actorInspectOverlay.runtimeActorIndex = *runtimeActorIndex;
    m_actorInspectOverlay.sourceX = rectMinX;
    m_actorInspectOverlay.sourceY = rectMinY;
    m_actorInspectOverlay.sourceWidth = std::max(1.0f, rectMaxX - rectMinX);
    m_actorInspectOverlay.sourceHeight = std::max(1.0f, rectMaxY - rectMinY);
}

void OutdoorGameView::updateSpellInspectOverlayState(int width, int height)
{
    m_spellInspectOverlay = {};

    if (width <= 0 || height <= 0 || !m_spellbook.active || m_pSpellTable == nullptr)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return;
    }

    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(m_spellbook.school);

    if (pDefinition == nullptr || !activeMemberHasSpellbookSchool(m_spellbook.school))
    {
        return;
    }

    for (uint32_t spellOffset = 0; spellOffset < pDefinition->spellCount; ++spellOffset)
    {
        const uint32_t spellId = pDefinition->firstSpellId + spellOffset;

        if (!activeMemberKnowsSpell(spellId))
        {
            continue;
        }

        const uint32_t spellOrdinal = spellOffset + 1;
        const std::string layoutId = spellbookSpellLayoutId(m_spellbook.school, spellOrdinal);
        const HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(*this, layoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const std::optional<ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(*this, 
            layoutId,
            width,
            height,
            pLayout->width,
            pLayout->height);

        if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, mouseX, mouseY))
        {
            continue;
        }

        const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

        if (pSpellEntry == nullptr)
        {
            return;
        }

        m_spellInspectOverlay.active = true;
        m_spellInspectOverlay.spellId = spellId;
        m_spellInspectOverlay.title = pSpellEntry->name;
        m_spellInspectOverlay.body = pSpellEntry->description;
        m_spellInspectOverlay.normal =
            pSpellEntry->normalText.empty() ? "" : "Normal: " + pSpellEntry->normalText;
        m_spellInspectOverlay.expert =
            pSpellEntry->expertText.empty() ? "" : "Expert: " + pSpellEntry->expertText;
        m_spellInspectOverlay.master =
            pSpellEntry->masterText.empty() ? "" : "Master: " + pSpellEntry->masterText;
        m_spellInspectOverlay.grandmaster =
            pSpellEntry->grandmasterText.empty() ? "" : "Grand Master: " + pSpellEntry->grandmasterText;
        m_spellInspectOverlay.sourceX = resolved->x;
        m_spellInspectOverlay.sourceY = resolved->y;
        m_spellInspectOverlay.sourceWidth = std::max(1.0f, resolved->width);
        m_spellInspectOverlay.sourceHeight = std::max(1.0f, resolved->height);
        return;
    }
}

void OutdoorGameView::renderHeldInventoryItem(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderHeldInventoryItem(*this, width, height);
}

void OutdoorGameView::renderItemInspectOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderItemInspectOverlay(*this, width, height);
}

void OutdoorGameView::renderCharacterInspectOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderCharacterInspectOverlay(*this, width, height);
}

void OutdoorGameView::renderSpellInspectOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderSpellInspectOverlay(*this, width, height);
}

void OutdoorGameView::renderReadableScrollOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderReadableScrollOverlay(*this, width, height);
}

void OutdoorGameView::renderBuffInspectOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderBuffInspectOverlay(*this, width, height);
}

void OutdoorGameView::renderCharacterDetailOverlay(int width, int height) const
{
    GameplayPartyOverlayRenderer::renderCharacterDetailOverlay(*this, width, height);
}

void OutdoorGameView::renderActorInspectOverlay(int width, int height)
{
    GameplayPartyOverlayRenderer::renderActorInspectOverlay(*this, width, height);
}

void OutdoorGameView::renderDialogueOverlay(int width, int height, bool renderAboveHud)
{
    if (currentHudScreenState() != HudScreenState::Dialogue
        || !m_activeEventDialog.isActive
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    m_hudLayoutRuntimeHeightOverrides.clear();
    float dialogMouseX = 0.0f;
    float dialogMouseY = 0.0f;
    SDL_GetMouseState(&dialogMouseX, &dialogMouseY);
    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    GameplayOverlayContext overlayContext(*this);

    if (!renderAboveHud && uiViewport.x > 0.5f)
    {
        GameplayDialogueRenderer::renderBlackoutBackdrop(overlayContext, width, height, uiViewport.x, uiViewport.width);
    }

    const bool isResidentSelectionMode =
        !m_activeEventDialog.actions.empty()
        && std::all_of(
            m_activeEventDialog.actions.begin(),
            m_activeEventDialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
    const EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const HouseEntry *pHostHouseEntry =
        (currentDialogueHostHouseId(pEventRuntimeState) != 0 && m_houseTable.has_value())
        ? m_houseTable->get(currentDialogueHostHouseId(pEventRuntimeState))
        : nullptr;
    const bool showDialogueVideoArea = pHostHouseEntry != nullptr;
    const bool hasDialogueParticipantIdentity =
        !m_activeEventDialog.title.empty()
        || m_activeEventDialog.participantPictureId != 0
        || m_activeEventDialog.sourceId != 0;
    const bool showEventDialogPanel =
        isResidentSelectionMode
        || !m_activeEventDialog.actions.empty()
        || pHostHouseEntry != nullptr
        || hasDialogueParticipantIdentity;
    const std::vector<std::string> &dialogueBodyLines = m_activeEventDialog.lines;
    const bool showDialogueTextFrame = !dialogueBodyLines.empty();
    std::optional<std::string> hoveredHouseServiceTopicText;
    const bool suppressServiceTopicsForShopOverlay =
        (m_houseShopOverlay.active
         && (m_houseShopOverlay.mode == HouseShopMode::BuyStandard
             || m_houseShopOverlay.mode == HouseShopMode::BuySpecial
             || m_houseShopOverlay.mode == HouseShopMode::BuySpellbooks))
        || (m_inventoryNestedOverlay.active
            && (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopSell
                || m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopIdentify
                || m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopRepair));
    const Party *pParty = m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->party() : nullptr;
    GameplayDialogueRenderer::updateHouseShopHoverTopicText(
        overlayContext,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        hoveredHouseServiceTopicText);

    const HudLayoutElement *pDialogueFrameLayout = HudUiService::findHudLayoutElement(*this, "DialogueFrame");
    const HudLayoutElement *pDialogueTextLayout = HudUiService::findHudLayoutElement(*this, "DialogueText");
    const HudLayoutElement *pBasebarLayout = HudUiService::findHudLayoutElement(*this, "OutdoorBasebar");

    if (showDialogueTextFrame
        && pDialogueFrameLayout != nullptr
        && pDialogueTextLayout != nullptr
        && pBasebarLayout != nullptr
        && toLowerCopy(pDialogueFrameLayout->screen) == "dialogue"
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue")
    {
        const HudFontHandle *pFont = HudUiService::findHudFont(*this, pDialogueTextLayout->fontName);

        if (pFont != nullptr)
        {
            static constexpr float DialogueTextTopInset = 2.0f;
            static constexpr float DialogueTextBottomInset = 5.0f;
            static constexpr float DialogueTextRightInset = 6.0f;
            const float lineHeight = static_cast<float>(pFont->fontHeight);
            const float textPadY = std::abs(pDialogueTextLayout->textPadY);
            const float textWrapWidth = std::max(
                0.0f,
                pDialogueTextLayout->width
                    - std::abs(pDialogueTextLayout->textPadX) * 2.0f
                    - DialogueTextRightInset);
            size_t wrappedLineCount = 0;

            for (const std::string &line : dialogueBodyLines)
            {
                const std::vector<std::string> wrappedLines = HudUiService::wrapHudTextToWidth(*this, *pFont, line, textWrapWidth);
                wrappedLineCount += std::max<size_t>(1, wrappedLines.size());
            }

            const float rawComputedTextHeight =
                static_cast<float>(wrappedLineCount) * lineHeight
                + textPadY * 2.0f
                + DialogueTextTopInset
                + DialogueTextBottomInset;
            const float unscaledTextHeight = rawComputedTextHeight;
            const float authoritativeFrameHeight = pBasebarLayout->height + unscaledTextHeight;
            m_hudLayoutRuntimeHeightOverrides[toLowerCopy("DialogueFrame")] = authoritativeFrameHeight;
            m_hudLayoutRuntimeHeightOverrides[toLowerCopy("DialogueText")] = unscaledTextHeight;

        }
    }

    std::string dialogueResponseHintText =
        m_activeEventDialog.actions.empty()
            ? "Enter/Space/E/Esc close"
            : "Up/Down select  Enter/Space accept  E/Esc close";

    if (m_houseBankState.inputActive())
    {
        dialogueResponseHintText = "Type amount  Enter accept  E/Esc cancel";
    }

    if (m_statusBarEventRemainingSeconds > 0.0f && !m_statusBarEventText.empty())
    {
        dialogueResponseHintText = m_statusBarEventText;
    }

    if (m_inventoryNestedOverlay.active
        && (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopSell
            || m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopIdentify
            || m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopRepair))
    {
        if (m_statusBarEventRemainingSeconds <= 0.0f || m_statusBarEventText.empty())
        {
            if (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopSell)
            {
                dialogueResponseHintText = "Select the Item to Sell";
            }
            else if (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopIdentify)
            {
                dialogueResponseHintText = "Select the Item to Identify";
            }
            else if (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopRepair)
            {
                dialogueResponseHintText = "Select the Item to Repair";
            }
        }

        if (pHostHouseEntry != nullptr && m_pOutdoorPartyRuntime != nullptr && m_pItemTable != nullptr)
        {
            const Character *pActiveCharacter = m_pOutdoorPartyRuntime->party().activeMember();
            const std::optional<ResolvedHudLayoutElement> resolvedInventoryGrid =
                resolveInventoryNestedOverlayGridArea(width, height);

            if (pActiveCharacter != nullptr && resolvedInventoryGrid)
            {
                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    resolvedInventoryGrid->scale);

                if (dialogMouseX >= resolvedInventoryGrid->x
                    && dialogMouseX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
                    && dialogMouseY >= resolvedInventoryGrid->y
                    && dialogMouseY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
                {
                    const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((dialogMouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                        0,
                        Character::InventoryWidth - 1));
                    const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((dialogMouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                        0,
                        Character::InventoryHeight - 1));
                    const InventoryItem *pItem = pActiveCharacter->inventoryItemAt(gridX, gridY);

                    if (pItem != nullptr)
                    {
                        if (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopSell)
                        {
                            hoveredHouseServiceTopicText = HouseServiceRuntime::buildSellHoverText(
                                m_pOutdoorPartyRuntime->party(),
                                *m_pItemTable,
                                *m_pStandardItemEnchantTable,
                                *m_pSpecialItemEnchantTable,
                                *pHostHouseEntry,
                                *pItem);
                        }
                        else if (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopIdentify)
                        {
                            hoveredHouseServiceTopicText = HouseServiceRuntime::buildIdentifyHoverText(
                                m_pOutdoorPartyRuntime->party(),
                                *m_pItemTable,
                                *m_pStandardItemEnchantTable,
                                *m_pSpecialItemEnchantTable,
                                *pHostHouseEntry,
                                *pItem);
                        }
                        else if (m_inventoryNestedOverlay.mode == InventoryNestedOverlayMode::ShopRepair)
                        {
                            const std::string hoverText = HouseServiceRuntime::buildRepairHoverText(
                                m_pOutdoorPartyRuntime->party(),
                                *m_pItemTable,
                                *m_pStandardItemEnchantTable,
                                *m_pSpecialItemEnchantTable,
                                *pHostHouseEntry,
                                *pItem);

                            if (!hoverText.empty())
                            {
                                hoveredHouseServiceTopicText = hoverText;
                            }
                        }
                    }
                }
            }
        }
    }

    const std::vector<std::string> orderedDialogueLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(*this, "Dialogue");

    for (const std::string &layoutId : orderedDialogueLayoutIds)
    {
        const HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(*this, layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != "dialogue")
        {
            continue;
        }

        GameplayDialogueRenderer::renderDialogueTextureElement(
            overlayContext,
            layoutId,
            width,
            height,
            dialogMouseX,
            dialogMouseY,
            showDialogueTextFrame,
            showDialogueVideoArea,
            showEventDialogPanel,
            renderAboveHud);
    }

    GameplayDialogueRenderer::renderHouseShopOverlay(
        overlayContext,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        dialogueResponseHintText,
        renderAboveHud);

    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueGoodbyeButton",
        "Close",
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueGoldLabel",
        pParty != nullptr ? std::to_string(pParty->gold()) : "",
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueFoodLabel",
        pParty != nullptr ? std::to_string(pParty->food()) : "",
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueResponseHint",
        dialogueResponseHintText,
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueEventPanel(
        overlayContext,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        renderAboveHud,
        showEventDialogPanel,
        isResidentSelectionMode,
        pHostHouseEntry,
        hoveredHouseServiceTopicText,
        suppressServiceTopicsForShopOverlay);
    GameplayDialogueRenderer::renderDialogueBodyText(
        overlayContext,
        width,
        height,
        renderAboveHud,
        dialogueBodyLines);

    m_hudLayoutRuntimeHeightOverrides.clear();
}

void OutdoorGameView::TerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void OutdoorGameView::TexturedTerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

OutdoorGameView::ResolvedHudLayoutElement OutdoorGameView::resolveAttachedHudLayoutRect(
    HudLayoutAttachMode attachTo,
    const ResolvedHudLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    ResolvedHudLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
        case HudLayoutAttachMode::None:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case HudLayoutAttachMode::RightOf:
            resolved.x = parent.x + parent.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case HudLayoutAttachMode::LeftOf:
            resolved.x = parent.x - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case HudLayoutAttachMode::Above:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case HudLayoutAttachMode::Below:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case HudLayoutAttachMode::CenterAbove:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case HudLayoutAttachMode::CenterBelow:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideTopCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideTopLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideTopRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideBottomLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideBottomCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case HudLayoutAttachMode::InsideBottomRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case HudLayoutAttachMode::CenterIn:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;
    }

    return resolved;
}


















bool OutdoorGameView::loadHudFont(const Engine::AssetFileSystem &assetFileSystem, const std::string &fontName)
{
    if (fontName.empty() || HudUiService::findHudFont(*this, fontName) != nullptr)
    {
        return true;
    }

    std::optional<std::string> fontPath = findCachedAssetPath("Data/icons", fontName + ".fnt");

    if (!fontPath)
    {
        fontPath = findCachedAssetPath("Data/EnglishT", fontName + ".fnt");
    }

    if (!fontPath)
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" reason=path-not-found\n";
        return false;
    }

    const std::optional<std::vector<uint8_t>> fontBytes = readCachedBinaryFile(*fontPath);

    if (!fontBytes || fontBytes->empty())
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" reason=read-failed\n";
        return false;
    }

    const std::optional<ParsedHudBitmapFont> parsedFont = parseHudBitmapFont(*fontBytes);

    if (!parsedFont)
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" bytes=" << fontBytes->size() << " reason=parse-failed\n";
        return false;
    }

    int atlasCellWidth = 1;

    for (const ParsedHudFontGlyphMetrics &metrics : parsedFont->glyphMetrics)
    {
        atlasCellWidth = std::max(atlasCellWidth, metrics.width);
    }

    const int atlasWidth = atlasCellWidth * 16;
    const int atlasHeight = parsedFont->fontHeight * 16;

    if (atlasWidth <= 0 || atlasHeight <= 0)
    {
        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" atlas=" << atlasWidth << "x" << atlasHeight << " reason=invalid-atlas\n";
        return false;
    }

    std::vector<uint8_t> mainPixels(static_cast<size_t>(atlasWidth) * atlasHeight * 4, 0);
    std::vector<uint8_t> shadowPixels(static_cast<size_t>(atlasWidth) * atlasHeight * 4, 0);

    for (int glyphIndex = parsedFont->firstChar; glyphIndex <= parsedFont->lastChar; ++glyphIndex)
    {
        const ParsedHudFontGlyphMetrics &metrics = parsedFont->glyphMetrics[glyphIndex];

        if (metrics.width <= 0)
        {
            continue;
        }

        const int cellX = (glyphIndex % 16) * atlasCellWidth;
        const int cellY = (glyphIndex / 16) * parsedFont->fontHeight;
        const size_t glyphOffset = parsedFont->glyphOffsets[glyphIndex];

        for (int y = 0; y < parsedFont->fontHeight; ++y)
        {
            for (int x = 0; x < metrics.width; ++x)
            {
                const uint8_t pixelValue =
                    parsedFont->pixels[glyphOffset + static_cast<size_t>(y) * metrics.width + x];

                if (pixelValue == 0)
                {
                    continue;
                }

                const size_t atlasPixelIndex =
                    (static_cast<size_t>(cellY + y) * atlasWidth + static_cast<size_t>(cellX + x)) * 4;
                std::vector<uint8_t> &targetPixels = (pixelValue == 1) ? shadowPixels : mainPixels;
                targetPixels[atlasPixelIndex + 0] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 1] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 2] = (pixelValue == 1) ? 0 : 255;
                targetPixels[atlasPixelIndex + 3] = 255;
            }
        }
    }

    HudFontHandle fontHandle = {};
    fontHandle.fontName = toLowerCopy(fontName);
    fontHandle.firstChar = parsedFont->firstChar;
    fontHandle.lastChar = parsedFont->lastChar;
    fontHandle.fontHeight = parsedFont->fontHeight;
    fontHandle.atlasCellWidth = atlasCellWidth;
    fontHandle.atlasWidth = atlasWidth;
    fontHandle.atlasHeight = atlasHeight;
    fontHandle.mainAtlasPixels = mainPixels;

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        fontHandle.glyphMetrics[glyphIndex].leftSpacing = parsedFont->glyphMetrics[glyphIndex].leftSpacing;
        fontHandle.glyphMetrics[glyphIndex].width = parsedFont->glyphMetrics[glyphIndex].width;
        fontHandle.glyphMetrics[glyphIndex].rightSpacing = parsedFont->glyphMetrics[glyphIndex].rightSpacing;
    }

    fontHandle.mainTextureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(atlasWidth),
        static_cast<uint16_t>(atlasHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(mainPixels.data(), static_cast<uint32_t>(mainPixels.size()))
    );
    fontHandle.shadowTextureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(atlasWidth),
        static_cast<uint16_t>(atlasHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(shadowPixels.data(), static_cast<uint32_t>(shadowPixels.size()))
    );

    if (!bgfx::isValid(fontHandle.mainTextureHandle) || !bgfx::isValid(fontHandle.shadowTextureHandle))
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
        }

        std::cout << "HUD font load failed: font=\"" << fontName << "\" path=\"" << *fontPath
                  << "\" atlas=" << atlasWidth << "x" << atlasHeight << " reason=texture-create-failed\n";
        return false;
    }

    std::cout << "HUD font loaded: font=\"" << fontName << "\" path=\"" << *fontPath
              << "\" atlas=" << atlasWidth << "x" << atlasHeight
              << " range=" << parsedFont->firstChar << "-" << parsedFont->lastChar << '\n';
    m_hudFontHandles.push_back(std::move(fontHandle));
    return true;
}




const OutdoorGameView::BillboardTextureHandle *OutdoorGameView::findBillboardTexture(
    const std::string &textureName,
    int16_t paletteId
) const
{
    const auto paletteIterator = m_billboardTextureIndexByPalette.find(paletteId);

    if (paletteIterator == m_billboardTextureIndexByPalette.end())
    {
        return nullptr;
    }

    const auto exactIterator = paletteIterator->second.find(textureName);

    if (exactIterator != paletteIterator->second.end())
    {
        if (exactIterator->second >= m_billboardTextureHandles.size())
        {
            return nullptr;
        }

        return &m_billboardTextureHandles[exactIterator->second];
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);
    const auto normalizedIterator = paletteIterator->second.find(normalizedTextureName);

    if (normalizedIterator == paletteIterator->second.end())
    {
        return nullptr;
    }

    if (normalizedIterator->second >= m_billboardTextureHandles.size())
    {
        return nullptr;
    }

    return &m_billboardTextureHandles[normalizedIterator->second];
}

bool OutdoorGameView::loadHudTexture(const Engine::AssetFileSystem &assetFileSystem, const std::string &textureName)
{
    if (HudUiService::findHudTexture(*this, textureName) != nullptr)
    {
        return true;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        loadHudBitmapPixelsBgraCached(textureName, width, height);

    if (!pixels || width <= 0 || height <= 0)
    {
        return false;
    }

    HudTextureHandle textureHandle = {};
    textureHandle.textureName = toLowerCopy(textureName);
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(width, assetFileSystem.getAssetScaleTier());
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(height, assetFileSystem.getAssetScaleTier());
    textureHandle.physicalWidth = width;
    textureHandle.physicalHeight = height;
    textureHandle.bgraPixels = *pixels;
    textureHandle.textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size()))
    );

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return false;
    }

    m_hudTextureHandles.push_back(std::move(textureHandle));
    return true;
}

std::optional<std::vector<uint8_t>> OutdoorGameView::loadHudBitmapPixelsBgraCached(
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::optional<std::string> iconPath = findCachedAssetPath("Data/icons", textureName + ".bmp");

    if (!iconPath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = readCachedBinaryFile(*iconPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];
        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}


void OutdoorGameView::preloadSpriteFrameTextures(const SpriteFrameTable &spriteFrameTable, uint16_t spriteFrameIndex)
{
    if (spriteFrameIndex == 0)
    {
        return;
    }

    size_t frameIndex = spriteFrameIndex;

    while (frameIndex <= std::numeric_limits<uint16_t>::max())
    {
        const SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(static_cast<uint16_t>(frameIndex), 0);

        if (pFrame == nullptr)
        {
            return;
        }

        for (int octant = 0; octant < 8; ++octant)
        {
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);

            if (resolvedTexture.textureName.empty())
            {
                continue;
            }

            OutdoorBillboardRenderer::ensureSpriteBillboardTexture(*this, resolvedTexture.textureName, pFrame->paletteId);
        }

        if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
        {
            return;
        }

        ++frameIndex;
    }
}

void OutdoorGameView::queueSpriteFrameWarmup(uint16_t spriteFrameIndex)
{
    if (spriteFrameIndex == 0)
    {
        return;
    }

    if (m_queuedSpriteFrameWarmups.empty())
    {
        m_queuedSpriteFrameWarmups.resize(static_cast<size_t>(std::numeric_limits<uint16_t>::max()) + 1, false);
    }

    if (m_queuedSpriteFrameWarmups[spriteFrameIndex])
    {
        return;
    }

    m_queuedSpriteFrameWarmups[spriteFrameIndex] = true;
    m_pendingSpriteFrameWarmups.push_back(spriteFrameIndex);
}

std::optional<std::string> OutdoorGameView::findCachedAssetPath(
    const std::string &directoryPath,
    const std::string &fileName)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    const std::string cacheKey = directoryPath + "|" + toLowerCopy(fileName);
    const auto cachedPathIt = m_spriteLoadCache.assetPathByKey.find(cacheKey);

    if (cachedPathIt != m_spriteLoadCache.assetPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto assetPathsIt = m_spriteLoadCache.directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (assetPathsIt != m_spriteLoadCache.directoryAssetPathsByPath.end())
    {
        pAssetPaths = &assetPathsIt->second;
    }
    else
    {
        std::unordered_map<std::string, std::string> assetPaths;
        std::vector<std::string> entries = m_pAssetFileSystem->enumerate(directoryPath);

        for (const std::string &entry : entries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths =
            &m_spriteLoadCache.directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedFileName = toLowerCopy(fileName);
    const auto resolvedPathIt = pAssetPaths->find(normalizedFileName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        m_spriteLoadCache.assetPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    m_spriteLoadCache.assetPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::vector<uint8_t>> OutdoorGameView::readCachedBinaryFile(const std::string &assetPath)
{
    if (m_pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    const auto cachedFileIt = m_spriteLoadCache.binaryFilesByPath.find(assetPath);

    if (cachedFileIt != m_spriteLoadCache.binaryFilesByPath.end())
    {
        return cachedFileIt->second;
    }

    const std::optional<std::vector<uint8_t>> bytes = m_pAssetFileSystem->readBinaryFile(assetPath);
    m_spriteLoadCache.binaryFilesByPath[assetPath] = bytes;
    return bytes;
}

std::optional<std::array<uint8_t, 256 * 3>> OutdoorGameView::loadCachedActPalette(int16_t paletteId)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const auto cachedPaletteIt = m_spriteLoadCache.actPalettesById.find(paletteId);

    if (cachedPaletteIt != m_spriteLoadCache.actPalettesById.end())
    {
        return cachedPaletteIt->second;
    }

    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath = findCachedAssetPath("Data/bitmaps", paletteFileName);

    if (!palettePath)
    {
        m_spriteLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> paletteBytes = readCachedBinaryFile(*palettePath);

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        m_spriteLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    m_spriteLoadCache.actPalettesById[paletteId] = palette;
    return palette;
}

std::optional<std::vector<uint8_t>> OutdoorGameView::loadSpriteBitmapPixelsBgraCached(
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    const std::optional<std::string> spritePath = findCachedAssetPath("Data/sprites", textureName + ".bmp");

    if (!spritePath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = readCachedBinaryFile(*spritePath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    return loadSpriteBitmapPixelsBgra(*bitmapBytes, loadCachedActPalette(paletteId), width, height);
}

void OutdoorGameView::updateCameraFromInput(float deltaSeconds)
{
    OutdoorGameplayInputController::updateCameraFromInput(*this, deltaSeconds);
}

}
