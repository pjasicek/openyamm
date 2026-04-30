#include "game/outdoor/OutdoorGameView.h"

#include "game/app/GameSession.h"
#include "engine/BgfxContext.h"
#include "game/FaceEnums.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/fx/ParticleRenderer.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/outdoor/OutdoorSpatialFxRuntime.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorPresentationController.h"
#include "game/outdoor/OutdoorRenderer.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/maps/SaveGame.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/SpawnPreview.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/party/SpellSchool.h"
#include "game/party/SpellIds.h"
#include "game/render/TextureFiltering.h"
#include "game/SpriteObjectDefs.h"
#include "game/tables/SpriteTables.h"
#include "game/StringUtils.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/gameplay/GameplayScreenRuntime.h"
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
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string dataTablePath(std::string_view fileName)
{
    return "Data/data_tables/" + std::string(fileName);
}

bool usesBlackTransparencyKey(std::string_view textureName)
{
    const std::string normalizedName = toLowerCopy(std::string(textureName));

    return normalizedName.rfind("mapdir", 0) == 0 || normalizedName.rfind("micon", 0) == 0;
}

bool outdoorActorIsPartyControlled(OutdoorWorldRuntime::ActorControlMode mode)
{
    switch (mode)
    {
        case OutdoorWorldRuntime::ActorControlMode::Charm:
        case OutdoorWorldRuntime::ActorControlMode::Enslaved:
        case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
        case OutdoorWorldRuntime::ActorControlMode::Reanimated:
            return true;

        default:
            return false;
    }
}

using SpellbookSchool = OutdoorGameView::SpellbookSchool;
using SpellbookPointerTargetType = OutdoorGameView::SpellbookPointerTargetType;
constexpr int MinutesPerDay = 24 * 60;
constexpr int InnRestDawnHour = 5;
constexpr uint32_t DeyjaTavernHouseId = 111;
constexpr uint32_t PitTavernHouseId = 114;
constexpr uint32_t MountNighonTavernHouseId = 116;
constexpr std::array<int, 3> JournalMapZoomLevels = {384, 768, 1536};
constexpr int JournalRevealWidth = 88;
constexpr int JournalRevealHeight = 88;
constexpr int JournalRevealBytesPerRow = 11;
constexpr float JournalMapWorldHalfExtent = 32768.0f;
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

bool decodeBmpBytesToBgra(
    const std::vector<uint8_t> &bmpBytes,
    int &width,
    int &height,
    std::vector<uint8_t> &pixels)
{
    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bmpBytes.data(), bmpBytes.size());

    if (pIoStream == nullptr)
    {
        return false;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return false;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return false;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    pixels.resize(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);
    return true;
}

void clampJournalMapState(GameplayUiController::JournalScreenState &journalScreen)
{
    journalScreen.mapZoomStep = std::clamp(
        journalScreen.mapZoomStep,
        0,
        static_cast<int>(JournalMapZoomLevels.size()) - 1);

    const int zoom = JournalMapZoomLevels[journalScreen.mapZoomStep];
    const float zoomFactor = static_cast<float>(zoom) / 384.0f;
    const float visibleWorldHalfExtent = JournalMapWorldHalfExtent / zoomFactor;
    const float maxOffset = std::max(0.0f, JournalMapWorldHalfExtent - visibleWorldHalfExtent);
    journalScreen.mapCenterX = std::clamp(
        journalScreen.mapCenterX,
        -maxOffset,
        maxOffset);
    journalScreen.mapCenterY = std::clamp(
        journalScreen.mapCenterY,
        -maxOffset,
        maxOffset);
}

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
constexpr float DefaultOutdoorFarClip = 16192.0f;
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
constexpr float CameraVerticalFovRadians = CameraVerticalFovDegrees * (Pi / 180.0f);
constexpr int DebugTextCellWidthPixels = 8;
constexpr int DebugTextCellHeightPixels = 16;
constexpr float BillboardNearDepth = 0.1f;
constexpr bool DebugProjectileDrawLogging = false;
constexpr float DebugProjectileTrailSeconds = 0.05f;
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float OeMeleeAlertDistance = 307.2f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr float OutdoorWalkableNormalZ = 0.70710678f;
constexpr float OutdoorMaxStepHeight = 128.0f;
constexpr size_t PreloadDecodeWorkerCount = 4;
constexpr uint64_t BillboardAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;
constexpr bool DebugSpritePreloadLogging = false;
constexpr bool DebugActorRenderHitchLogging = false;
constexpr std::string_view PartyStartDecorationName = "party start";
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr uint32_t SkyDomeHorizontalSegmentCount = 24;
constexpr uint32_t SkyDomeVerticalSegmentCount = 8;
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;
constexpr uint32_t SpeechReactionCooldownMs = 900;
constexpr uint32_t CombatSpeechReactionCooldownMs = 2500;
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

        if (pActor == nullptr
            || pActor->isDead
            || pActor->isInvisible
            || !pActor->hostileToParty
            || outdoorActorIsPartyControlled(pActor->controlMode))
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
    return jewelryOverlayOpen
        ? isBodyEquipmentVisualSlot(slot) || isJewelryOverlayEquipmentSlot(slot)
        : !isJewelryOverlayEquipmentSlot(slot);
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

std::vector<std::string> collectRelevantHouseVideoStemsForMap(
    const OutdoorMapData &outdoorMapData,
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    const HouseTable &houseTable)
{
    static_cast<void>(outdoorMapData);
    static_cast<void>(localProgram);
    static_cast<void>(globalProgram);

    std::unordered_set<std::string> seenVideoStems;
    std::vector<std::string> videoStems;

    for (const auto &[houseId, houseEntry] : houseTable.entries())
    {
        (void)houseId;

        if (houseEntry.videoName.empty())
        {
            continue;
        }

        if (!seenVideoStems.insert(houseEntry.videoName).second)
        {
            continue;
        }

        videoStems.push_back(houseEntry.videoName);
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
    std::optional<float> yawRadians;
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
    const std::optional<std::string> decorationTableText =
        assetFileSystem.readTextFile(dataTablePath("decoration_data.txt"));

    if (!decorationTableText)
    {
        return std::nullopt;
    }

    const std::optional<Engine::TextTable> parsedDecorationTable =
        Engine::TextTable::parseTabSeparated(*decorationTableText);

    if (!parsedDecorationTable)
    {
        return std::nullopt;
    }

    std::vector<std::vector<std::string>> decorationRows;
    decorationRows.reserve(parsedDecorationTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedDecorationTable->getRowCount(); ++rowIndex)
    {
        decorationRows.push_back(parsedDecorationTable->getRow(rowIndex));
    }

    DecorationTable decorationTable;

    if (!decorationTable.loadRows(decorationRows))
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
        startPoint.x = static_cast<float>(entity.x);
        startPoint.y = static_cast<float>(entity.y);
        startPoint.z = static_cast<float>(entity.z);
        startPoint.yawRadians = static_cast<float>(entity.facing) * Pi / 180.0f;
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
                const bool isZeroIndexKey = paletteIndex == 0;
                const bool isMagentaKey = sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
                const bool isTealKey = sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
                const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                const size_t pixelOffset =
                    (static_cast<size_t>(row) * static_cast<size_t>(width) + static_cast<size_t>(column)) * 4;

                pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
                pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
                pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
                pixels[pixelOffset + 3] = (isZeroIndexKey || isMagentaKey || isTealKey) ? 0 : 255;
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
    const HouseTable *pHouseTable,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    static_cast<void>(pHouseTable);

    if (eventId == 0)
    {
        return "-";
    }

    if (localEventProgram)
    {
        const std::optional<std::string> summary = localEventProgram->summarizeEvent(eventId);

        if (summary)
        {
            return "L:" + *summary;
        }
    }

    if (globalEventProgram)
    {
        const std::optional<std::string> summary = globalEventProgram->summarizeEvent(eventId);

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
    const ChestTable *pChestTable,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    if (eventId == 0 || !mapDeltaData || pChestTable == nullptr)
    {
        return {};
    }

    std::vector<uint32_t> chestIds;

    if (localEventProgram && localEventProgram->hasEvent(eventId))
    {
        chestIds = localEventProgram->getOpenedChestIds(eventId);
    }
    else if (globalEventProgram && globalEventProgram->hasEvent(eventId))
    {
        chestIds = globalEventProgram->getOpenedChestIds(eventId);
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
        const ChestEntry *pEntry = pChestTable->get(chest.chestTypeId);
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
                outdoorGridCornerWorldX(gridX),
                outdoorGridCornerWorldY(gridY),
                static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 topRight = {
                outdoorGridCornerWorldX(gridX + 1),
                outdoorGridCornerWorldY(gridY),
                static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 bottomLeft = {
                outdoorGridCornerWorldX(gridX),
                outdoorGridCornerWorldY(gridY + 1),
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 bottomRight = {
                outdoorGridCornerWorldX(gridX + 1),
                outdoorGridCornerWorldY(gridY + 1),
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

    if (clipW <= InspectRayEpsilon)
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
bgfx::VertexLayout OutdoorGameView::LitBillboardVertex::ms_layout;
bgfx::VertexLayout OutdoorGameView::ForcePerspectiveVertex::ms_layout;

void OutdoorGameView::dumpDebugBModelRenderStateToConsole(uint32_t cogNumber) const
{
    const MapDeltaData *pMapDeltaData =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
    const EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const uint32_t invisibleBit = faceAttributeBit(FaceAttribute::Invisible);

    size_t matchedBatchCount = 0;
    size_t hiddenBatchCount = 0;
    size_t visibleBatchCount = 0;
    size_t missingAnimationCount = 0;
    size_t matchedVertexCount = 0;
    size_t visibleVertexCount = 0;
    bool hasVisibleBounds = false;
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    std::vector<const TexturedBModelBatch *> samples;
    samples.reserve(8);

    for (const TexturedBModelBatch &batch : m_texturedBModelBatches)
    {
        if (batch.cogNumber != cogNumber)
        {
            continue;
        }

        ++matchedBatchCount;
        matchedVertexCount += batch.vertices.size();

        if (batch.defaultAnimationIndex >= m_bmodelTextureAnimations.size())
        {
            ++missingAnimationCount;
        }

        uint32_t attributes = batch.baseAttributes;

        if (pMapDeltaData != nullptr && batch.faceId < pMapDeltaData->faceAttributes.size())
        {
            attributes = pMapDeltaData->faceAttributes[batch.faceId];
        }
        else if (pEventRuntimeState != nullptr)
        {
            const auto setIt = pEventRuntimeState->facetSetMasks.find(batch.faceId);

            if (setIt != pEventRuntimeState->facetSetMasks.end())
            {
                attributes |= setIt->second;
            }

            const auto clearIt = pEventRuntimeState->facetClearMasks.find(batch.faceId);

            if (clearIt != pEventRuntimeState->facetClearMasks.end())
            {
                attributes &= ~clearIt->second;
            }
        }

        if ((attributes & invisibleBit) != 0)
        {
            ++hiddenBatchCount;
        }
        else
        {
            ++visibleBatchCount;
            visibleVertexCount += batch.vertices.size();

            for (const TexturedTerrainVertex &vertex : batch.vertices)
            {
                minX = std::min(minX, vertex.x);
                minY = std::min(minY, vertex.y);
                minZ = std::min(minZ, vertex.z);
                maxX = std::max(maxX, vertex.x);
                maxY = std::max(maxY, vertex.y);
                maxZ = std::max(maxZ, vertex.z);
            }

            hasVisibleBounds = true;
        }

        if (samples.size() < 8)
        {
            samples.push_back(&batch);
        }
    }

    size_t resolvedVertexCount = 0;

    for (const ResolvedBModelDrawGroup &drawGroup : m_resolvedBModelDrawGroups)
    {
        resolvedVertexCount += drawGroup.vertexCount;
    }

    std::cout
        << "F5 Outdoor bmodel render cog=" << cogNumber
        << " showBModels=" << (m_showBModels ? 1 : 0)
        << " batches.total=" << m_texturedBModelBatches.size()
        << " matched=" << matchedBatchCount
        << " hidden=" << hiddenBatchCount
        << " visible=" << visibleBatchCount
        << " missingAnimation=" << missingAnimationCount
        << " matched.vertices=" << matchedVertexCount
        << " visible.vertices=" << visibleVertexCount
        << " animations=" << m_bmodelTextureAnimations.size()
        << " resolved.groups=" << m_resolvedBModelDrawGroups.size()
        << " resolved.vertices=" << resolvedVertexCount
        << " resolved.revision=" << m_resolvedBModelDrawGroupRevision
        << '\n';

    if (hasVisibleBounds)
    {
        std::cout
            << "  visible.bounds min=(" << minX << "," << minY << "," << minZ << ")"
            << " max=(" << maxX << "," << maxY << "," << maxZ << ")"
            << '\n';
    }

    for (const TexturedBModelBatch *pBatch : samples)
    {
        uint32_t currentAttributes = pBatch->baseAttributes;

        if (pMapDeltaData != nullptr && pBatch->faceId < pMapDeltaData->faceAttributes.size())
        {
            currentAttributes = pMapDeltaData->faceAttributes[pBatch->faceId];
        }

        std::cout
            << "  batch faceId=" << pBatch->faceId
            << " bmodel=" << pBatch->bModelIndex
            << " face=" << pBatch->faceIndex
            << " texture=\"" << pBatch->textureName << "\""
            << " vertices=" << pBatch->vertices.size()
            << " animation=" << pBatch->defaultAnimationIndex
            << " base=0x" << std::hex << pBatch->baseAttributes
            << " current=0x" << currentAttributes << std::dec
            << '\n';
    }
}

OutdoorGameView::OutdoorGameView(GameSession &gameSession)
    : m_isInitialized(false)
    , m_isRenderable(false)
    , m_outdoorMapData(std::nullopt)
    , m_vertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_indexBufferHandle(BGFX_INVALID_HANDLE)
    , m_skyVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_texturedTerrainVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bloodSplatVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_filledTerrainVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bmodelVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bmodelCollisionVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_entityMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_spawnMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_programHandle(BGFX_INVALID_HANDLE)
    , m_texturedTerrainProgramHandle(BGFX_INVALID_HANDLE)
    , m_spellAreaPreviewProgramHandle(BGFX_INVALID_HANDLE)
    , m_outdoorLitBillboardProgramHandle(BGFX_INVALID_HANDLE)
    , m_outdoorTexturedFogProgramHandle(BGFX_INVALID_HANDLE)
    , m_outdoorForcePerspectiveProgramHandle(BGFX_INVALID_HANDLE)
    , m_terrainTextureAtlasHandle(BGFX_INVALID_HANDLE)
    , m_bloodSplatTextureHandle(BGFX_INVALID_HANDLE)
    , m_forcePerspectiveSolidTextureHandle(BGFX_INVALID_HANDLE)
    , m_terrainTextureSamplerHandle(BGFX_INVALID_HANDLE)
    , m_outdoorBillboardAmbientUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorBillboardOverrideColorUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorBillboardOutlineParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorFxLightPositionsUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorFxLightColorsUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorFxLightParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorFogColorUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorFogDensitiesUniformHandle(BGFX_INVALID_HANDLE)
    , m_outdoorFogDistancesUniformHandle(BGFX_INVALID_HANDLE)
    , m_secretPulseParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_spellAreaPreviewParams0UniformHandle(BGFX_INVALID_HANDLE)
    , m_spellAreaPreviewParams1UniformHandle(BGFX_INVALID_HANDLE)
    , m_spellAreaPreviewColorAUniformHandle(BGFX_INVALID_HANDLE)
    , m_spellAreaPreviewColorBUniformHandle(BGFX_INVALID_HANDLE)
    , m_elapsedTime(0.0f)
    , m_framesPerSecond(0.0f)
    , m_bmodelLineVertexCount(0)
    , m_bloodSplatVertexCount(0)
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
    , m_showBModelWireframe(false)
    , m_showBModelCollisionFaces(false)
    , m_showActorCollisionBoxes(false)
    , m_showDecorationBillboards(true)
    , m_showActors(true)
    , m_showSpriteObjects(true)
    , m_showEntities(false)
    , m_showSpawns(false)
    , m_showGameplayHud(true)
    , m_renderGameplayUiThisFrame(false)
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
    , m_toggleTextureFilteringLatch(false)
    , m_toggleInspectLatch(false)
    , m_triggerMeteorLatch(false)
    , m_dumpGameplayStateLatch(false)
    , m_toggleFlyingLatch(false)
    , m_toggleWaterWalkLatch(false)
    , m_toggleFeatherFallLatch(false)
    , m_gameSession(gameSession)
    , m_lastAdventurersInnPortraitClickTicks(0)
    , m_lastAdventurersInnPortraitClickedIndex(std::nullopt)
    , m_spellAreaPreviewCache({})
    , m_cachedHoverInspectHitValid(false)
    , m_lastHoverInspectUpdateNanoseconds(0)
    , m_cachedHoverInspectHit({})
    , m_pOutdoorPartyRuntime(nullptr)
    , m_pAssetFileSystem(nullptr)
    , m_pOutdoorSceneRuntime(nullptr)
    , m_pOutdoorWorldRuntime(nullptr)
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
    GameplayOverlayInteractionState &overlayInteractionState = m_gameSession.overlayInteractionState();
    overlayInteractionState.eventDialogPartySelectLatches.fill(false);
    overlayInteractionState.houseBankDigitLatches.fill(false);
}

OutdoorGameView::~OutdoorGameView()
{
    shutdown();
}

bool OutdoorGameView::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
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
        GameAudioSystem *pGameAudioSystem,
        OutdoorSceneRuntime &sceneRuntime,
        const GameSettings &settings)
{
    shutdown();
    const GameDataRepository &data = m_gameSession.data();

    m_isInitialized = true;
    m_pAssetFileSystem = &assetFileSystem;
    m_map = map;
    m_outdoorMapData = outdoorMapData;
    m_outdoorDecorationBillboardSet = outdoorDecorationBillboardSet;
    m_outdoorActorPreviewBillboardSet = outdoorActorPreviewBillboardSet;
    m_outdoorSpriteObjectBillboardSet = outdoorSpriteObjectBillboardSet;
    m_outdoorMapDeltaData = outdoorMapDeltaData;
    m_pGameAudioSystem = pGameAudioSystem;
    m_pOutdoorSceneRuntime = &sceneRuntime;
    m_pOutdoorPartyRuntime = &sceneRuntime.partyRuntime();
    m_pOutdoorWorldRuntime = &sceneRuntime.worldRuntime();
    m_pOutdoorWorldRuntime->bindInteractionView(this);
    m_pOutdoorWorldRuntime->bindGlobalEventProgram(&sceneRuntime.globalEventProgram());
    m_pOutdoorWorldRuntime->setWorldFxSystem(&m_worldFxSystem);
    m_gameSettings = settings;
    m_gameSession.gameplayScreenRuntime().bindSceneAdapter(this);
    m_gameSession.gameplayScreenRuntime().bindAudioSystem(m_pGameAudioSystem);
    m_gameSession.gameplayScreenRuntime().bindSettings(&m_gameSettings);
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    const GameplayScreenRuntime::SharedUiBootstrapResult sharedUiBootstrap =
        screenRuntime.initializeSharedUiRuntime(
            GameplayScreenRuntime::SharedUiBootstrapConfig{
                .pAssetFileSystem = &assetFileSystem,
                .portraitMemberCount =
                    m_pOutdoorPartyRuntime != nullptr
                        ? m_pOutdoorPartyRuntime->party().members().size()
                        : 0,
                .initializeHouseVideoPlayer = true,
            });

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
    std::optional<float> initialYawRadians;

    if (const std::optional<OutdoorPartyStartPoint> startPoint =
            resolveOutdoorPartyStartPoint(assetFileSystem, outdoorMapData))
    {
        initialX = startPoint->x;
        initialY = startPoint->y;
        initialFootZ = startPoint->z;
        initialYawRadians = startPoint->yawRadians;
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
    m_cameraYawRadians = initialYawRadians.value_or(-Pi * 0.5f);
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
    ParticleRenderer::initializeResources(m_worldFxRenderResources);

    if (!sharedUiBootstrap.layoutsLoaded)
    {
        std::cerr << "OutdoorGameView failed to load HUD layout data from Data/ui/gameplay/*.yml\n";
    }

    m_terrainTextureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_outdoorBillboardAmbientUniformHandle = bgfx::createUniform("u_billboardAmbient", bgfx::UniformType::Vec4);
    m_outdoorBillboardOverrideColorUniformHandle =
        bgfx::createUniform("u_billboardOverrideColor", bgfx::UniformType::Vec4);
    m_outdoorBillboardOutlineParamsUniformHandle =
        bgfx::createUniform("u_billboardOutlineParams", bgfx::UniformType::Vec4);
    m_outdoorFxLightPositionsUniformHandle = bgfx::createUniform("u_fxLightPositions", bgfx::UniformType::Vec4, 8);
    m_outdoorFxLightColorsUniformHandle = bgfx::createUniform("u_fxLightColors", bgfx::UniformType::Vec4, 8);
    m_outdoorFxLightParamsUniformHandle = bgfx::createUniform("u_fxLightParams", bgfx::UniformType::Vec4);
    m_outdoorFogColorUniformHandle = bgfx::createUniform("u_fogColor", bgfx::UniformType::Vec4);
    m_outdoorFogDensitiesUniformHandle = bgfx::createUniform("u_fogDensities", bgfx::UniformType::Vec4);
    m_outdoorFogDistancesUniformHandle = bgfx::createUniform("u_fogDistances", bgfx::UniformType::Vec4);
    m_secretPulseParamsUniformHandle = bgfx::createUniform("u_secretPulseParams", bgfx::UniformType::Vec4);
    m_spellAreaPreviewParams0UniformHandle = bgfx::createUniform("u_spellAreaParams0", bgfx::UniformType::Vec4);
    m_spellAreaPreviewParams1UniformHandle = bgfx::createUniform("u_spellAreaParams1", bgfx::UniformType::Vec4);
    m_spellAreaPreviewColorAUniformHandle = bgfx::createUniform("u_spellAreaColorA", bgfx::UniformType::Vec4);
    m_spellAreaPreviewColorBUniformHandle = bgfx::createUniform("u_spellAreaColorB", bgfx::UniformType::Vec4);

    if (!bgfx::isValid(m_vertexBufferHandle)
        || !bgfx::isValid(m_indexBufferHandle)
        || !bgfx::isValid(m_programHandle)
        || !bgfx::isValid(m_outdoorLitBillboardProgramHandle)
        || !m_worldFxRenderResources.isReady()
        || !bgfx::isValid(m_outdoorTexturedFogProgramHandle)
        || !bgfx::isValid(m_outdoorForcePerspectiveProgramHandle)
        || !bgfx::isValid(m_outdoorBillboardAmbientUniformHandle)
        || !bgfx::isValid(m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(m_outdoorBillboardOutlineParamsUniformHandle)
        || !bgfx::isValid(m_outdoorFxLightPositionsUniformHandle)
        || !bgfx::isValid(m_outdoorFxLightColorsUniformHandle)
        || !bgfx::isValid(m_outdoorFxLightParamsUniformHandle)
        || !bgfx::isValid(m_outdoorFogColorUniformHandle)
        || !bgfx::isValid(m_outdoorFogDensitiesUniformHandle)
        || !bgfx::isValid(m_outdoorFogDistancesUniformHandle)
        || !bgfx::isValid(m_secretPulseParamsUniformHandle))
    {
        std::cerr << "OutdoorGameView failed to create bgfx resources.\n";
        shutdown();
        return false;
    }

    const std::vector<std::string> relevantHouseVideoStems = collectRelevantHouseVideoStemsForMap(
        outdoorMapData,
        m_pOutdoorSceneRuntime != nullptr
            ? m_pOutdoorSceneRuntime->localEventProgram()
            : std::nullopt,
        m_pOutdoorSceneRuntime != nullptr
            ? m_pOutdoorSceneRuntime->globalEventProgram()
            : std::nullopt,
        m_gameSession.data().houseTable());

    for (const std::string &videoStem : relevantHouseVideoStems)
    {
        screenRuntime.queueBackgroundHouseVideoPreload(videoStem);
    }

    m_isRenderable = true;
    return true;
}

void OutdoorGameView::render(int width, int height, const GameplayInputFrame &input, float deltaSeconds)
{
    m_renderGameplayUiThisFrame = false;

    if (!m_isInitialized)
    {
        return;
    }

    const GameDataRepository &data = m_gameSession.data();
    const HouseTable &houseTable = data.houseTable();
    const ChestTable &chestTable = data.chestTable();
    GameplayScreenState &gameplayScreenState = m_gameSession.gameplayScreenState();
    GameplayMouseLookState &gameplayMouseLookState = gameplayScreenState.gameplayMouseLookState();

    GameplayHudRenderBackend hudRenderBackend = {};
    hudRenderBackend.texturedProgramHandle = m_texturedTerrainProgramHandle;
    hudRenderBackend.textureSamplerHandle = m_terrainTextureSamplerHandle;
    hudRenderBackend.viewId = HudViewId;
    m_gameSession.gameplayScreenRuntime().bindHudRenderBackend(hudRenderBackend);

    if (deltaSeconds > 0.0f)
    {
        m_elapsedTime += deltaSeconds;
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
                    m_gameSession.gameplayScreenRuntime().closeMenuOverlay();
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

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));
    m_lastRenderWidth = width;
    m_lastRenderHeight = height;
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState =
        m_pOutdoorWorldRuntime != nullptr ? &m_pOutdoorWorldRuntime->atmosphereState() : nullptr;
    const uint32_t clearColorAbgr = pAtmosphereState != nullptr ? pAtmosphereState->clearColorAbgr : 0x000000ffu;
    const float farClipDistance = DefaultOutdoorFarClip;
    const bool captureSavePreviewThisFrame =
        m_pendingSavePreviewCapture.active && !m_pendingSavePreviewCapture.screenshotRequested;
    const bool captureLloydsBeaconPreviewThisFrame =
        !captureSavePreviewThisFrame
        && utilityOverlay.lloydSetPreviewCapturePending
        && !utilityOverlay.lloydSetPreviewScreenshotRequested;
    m_renderGameplayUiThisFrame = !captureSavePreviewThisFrame && !captureLloydsBeaconPreviewThisFrame;

    bgfx::setViewRect(SkyViewId, 0, 0, viewWidth, viewHeight);
    bgfx::setViewClear(SkyViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, clearColorAbgr, 1.0f, 0);
    bgfx::setViewRect(MainViewId, 0, 0, viewWidth, viewHeight);
    bgfx::setViewClear(MainViewId, BGFX_CLEAR_DEPTH, 0, 1.0f, 0);
    bgfx::setViewMode(MainViewId, bgfx::ViewMode::Sequential);

    if (!m_isRenderable)
    {
        if (captureLloydsBeaconPreviewThisFrame)
        {
            PartySpellCastRequest request = utilityOverlay.lloydSetPreviewRequest;
            const std::string spellName = utilityOverlay.lloydSetPreviewSpellName;
            utilityOverlay.lloydSetPreviewCapturePending = false;
            utilityOverlay.lloydSetPreviewScreenshotRequested = false;
            utilityOverlay.lloydSetPreviewStartedTicks = 0;
            utilityOverlay.lloydSetPreviewRequestId.clear();
            utilityOverlay.lloydSetPreviewSpellName.clear();
            utilityOverlay.lloydSetPreviewRequest = {};
            overlayContext.tryCastSpellRequest(request, spellName);
        }

        m_renderGameplayUiThisFrame = false;
        bgfx::touch(SkyViewId);
        bgfx::touch(MainViewId);
        bgfx::dbgTextClear();
        bgfx::dbgTextPrintf(0, 1, 0x0f, "bgfx noop renderer active");
        return;
    }

    const GameplayUiController::SaveGameScreenState &saveGameScreen = overlayContext.saveGameScreenState();
    const GameplayUiController::LoadGameScreenState &loadGameScreen = overlayContext.loadGameScreenState();

    updateHouseVideoPlayback(deltaSeconds);
    updateItemInspectOverlayState(width, height, input);
    updateActorInspectOverlayState(width, height, input);

    OutdoorBillboardRenderer::queueRuntimeActorBillboardTextureWarmup(*this);
    OutdoorBillboardRenderer::processPendingSpriteFrameWarmups(*this, 1);

    const float wireframeAspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);

    float wireframeViewMatrix[16] = {};
    float wireframeProjectionMatrix[16] = {};

    const float cameraYawRadians = effectiveCameraYawRadians();
    const float cameraPitchRadians = effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const float sinPitch = std::sin(cameraPitchRadians);
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const bx::Vec3 wireframeEye = {
        m_cameraTargetX,
        m_cameraTargetY,
        m_cameraTargetZ
    };
    const bx::Vec3 wireframeAt = {
        m_cameraTargetX + cosYaw * cosPitch,
        m_cameraTargetY + sinYaw * cosPitch,
        m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 wireframeUp = {0.0f, 0.0f, 1.0f};
    bx::mtxLookAt(
        wireframeViewMatrix,
        wireframeEye,
        wireframeAt,
        wireframeUp,
        bx::Handedness::Right);
    bx::mtxProj(
        wireframeProjectionMatrix,
        CameraVerticalFovDegrees,
        wireframeAspectRatio,
        0.1f,
        farClipDistance,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    const bx::Vec3 cameraForward = vecNormalize(vecSubtract(wireframeAt, wireframeEye));
    const bx::Vec3 cameraRight = vecNormalize(bx::cross(cameraForward, wireframeUp));
    const bx::Vec3 cameraUp = vecNormalize(bx::cross(cameraRight, cameraForward));

    bgfx::setViewTransform(SkyViewId, wireframeViewMatrix, wireframeProjectionMatrix);
    bgfx::touch(SkyViewId);
    bgfx::setViewTransform(MainViewId, wireframeViewMatrix, wireframeProjectionMatrix);
    bgfx::touch(MainViewId);

    InspectHit inspectHit = {};
    const float mouseX = input.pointerX;
    const float mouseY = input.pointerY;
    if (m_cachedHoverInspectHitValid)
    {
        inspectHit = m_cachedHoverInspectHit;
    }

    m_worldFxSystem.setShadowsEnabled(m_gameSettings.shadows);
    m_worldFxSystem.updateParticles(deltaSeconds, gameplayMouseLookState.cursorModeActive);

    if (!gameplayMouseLookState.cursorModeActive)
    {
        const bool refreshSpatialFx = m_outdoorSpatialFxRuntime.beginFrame(*this, deltaSeconds);
        m_worldFxSystem.syncProjectileFx(m_gameSession, deltaSeconds, refreshSpatialFx);
        m_outdoorSpatialFxRuntime.syncSpatialFx(*this, refreshSpatialFx);
    }

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

    if (!captureSavePreviewThisFrame && !captureLloydsBeaconPreviewThisFrame)
    {
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
            "Modes: 1 filled=%s  2 wire=%s  3 bmodels=%s  4 bmwire=%s  5 coll=%s  "
            "6 actorcoll=%s  7 actors=%s  8 objs=%s  9 ents=%s  0 spawns=%s  "
            "-=inspect=%s  F2 debug=%s  F3 decor=%s  F4 hud=%s  F5 dump  F7 filter=%s  textured=%s/%s",
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
            textureFilteringEnabled() ? "on" : "off",
            bgfx::isValid(m_terrainTextureAtlasHandle) ? "yes" : "no",
            m_texturedBModelBatches.empty() ? "no" : "yes"
        );
        bgfx::dbgTextPrintf(
            0,
            6,
            0x0f,
            "Move: WASD  Space use  X jump  Shift walk/run  Ctrl turbo  F fly T waterwalk G feather"
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

            if (!pEventRuntimeState->grantedItems.empty())
            {
                runtimeSummary += " give=" + std::to_string(pEventRuntimeState->grantedItems.back().objectDescriptionId);
            }
            else if (!pEventRuntimeState->grantedItemIds.empty())
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
            const std::optional<ScriptedEventProgram> &localEventProgram =
                m_pOutdoorSceneRuntime != nullptr ? m_pOutdoorSceneRuntime->localEventProgram() : std::optional<ScriptedEventProgram>{};
            const std::optional<ScriptedEventProgram> &globalEventProgram =
                m_pOutdoorSceneRuntime != nullptr ? m_pOutdoorSceneRuntime->globalEventProgram() : std::optional<ScriptedEventProgram>{};

            if (inspectHit.kind == "entity")
            {
                const std::string primaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdPrimary,
                    &houseTable,
                    localEventProgram,
                    globalEventProgram
                );
                const std::string secondaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdSecondary,
                    &houseTable,
                    localEventProgram,
                    globalEventProgram
                );
                const std::string primaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdPrimary,
                    m_outdoorMapDeltaData,
                    &chestTable,
                    localEventProgram,
                    globalEventProgram
                );
                const std::string secondaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdSecondary,
                    m_outdoorMapDeltaData,
                    &chestTable,
                    localEventProgram,
                    globalEventProgram
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
                            static_cast<float>(pActorState->y) - wireframeEye.y,
                            static_cast<float>(pActorState->x) - wireframeEye.x
                        );
                        const float actorYaw = pActorState->yawRadians;
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
                    &houseTable,
                    localEventProgram,
                    globalEventProgram
                );
                const std::string faceChestSummary = summarizeLinkedChests(
                    inspectHit.cogTriggeredNumber,
                    m_outdoorMapDeltaData,
                    &chestTable,
                    localEventProgram,
                    globalEventProgram
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

    }

    updateFootstepAudio(deltaSeconds);
    consumePendingWorldAudioEvents();

}

GameplayWorldUiRenderState OutdoorGameView::gameplayUiRenderState(int width, int height) const
{
    return GameplayWorldUiRenderState{
        .canRenderHudOverlays = m_renderGameplayUiThisFrame && width > 0 && height > 0,
        .renderGameplayHud = m_renderGameplayUiThisFrame && m_showGameplayHud,
    };
}

void OutdoorGameView::shutdown()
{
    syncGameplayMouseLookMode(SDL_GetMouseFocus(), false);
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    GameplayScreenState &gameplayScreenState = m_gameSession.gameplayScreenState();
    PendingSpellCastState &pendingSpellCast = gameplayScreenState.pendingSpellTarget();
    QuickSpellState &quickSpellState = gameplayScreenState.quickSpellState();
    AttackActionState &attackActionState = gameplayScreenState.attackActionState();
    WorldInteractionInputState &worldInteractionInputState = gameplayScreenState.worldInteractionInputState();
    GameplayMouseLookState &gameplayMouseLookState = gameplayScreenState.gameplayMouseLookState();
    screenRuntime.clearHudRenderBackend();
    screenRuntime.clearSceneAdapter(this);
    screenRuntime.bindAudioSystem(nullptr);

    if (!m_isInitialized)
    {
        return;
    }

    auto resetRuntimeState = [this]()
    {
        m_isRenderable = false;
        m_isInitialized = false;
        m_map.reset();
        m_outdoorMapData.reset();
        m_pOutdoorPartyRuntime = nullptr;
        m_pAssetFileSystem = nullptr;
        m_pOutdoorSceneRuntime = nullptr;
        if (m_pOutdoorWorldRuntime != nullptr)
        {
            m_pOutdoorWorldRuntime->bindInteractionView(nullptr);
            m_pOutdoorWorldRuntime->bindGlobalEventProgram(nullptr);
            m_pOutdoorWorldRuntime->setWorldFxSystem(nullptr);
        }
        m_pOutdoorWorldRuntime = nullptr;
    };

    screenRuntime.clearUiControllerRuntimeState();
    screenRuntime.shutdownHouseVideoPlayer();
    m_outdoorSpatialFxRuntime.reset();
    m_worldFxSystem.reset();

    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        m_programHandle = BGFX_INVALID_HANDLE;
        m_texturedTerrainProgramHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewProgramHandle = BGFX_INVALID_HANDLE;
        m_outdoorLitBillboardProgramHandle = BGFX_INVALID_HANDLE;
        m_worldFxRenderResources.reset();
        m_outdoorTexturedFogProgramHandle = BGFX_INVALID_HANDLE;
        m_outdoorForcePerspectiveProgramHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatTextureHandle = BGFX_INVALID_HANDLE;
        m_forcePerspectiveSolidTextureHandle = BGFX_INVALID_HANDLE;
        m_terrainTextureSamplerHandle = BGFX_INVALID_HANDLE;
        m_outdoorBillboardAmbientUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorBillboardOverrideColorUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorBillboardOutlineParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorFxLightPositionsUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorFxLightColorsUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorFxLightParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatVertexCount = 0;
        m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();
        m_outdoorFogColorUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorFogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
        m_outdoorFogDistancesUniformHandle = BGFX_INVALID_HANDLE;
        m_secretPulseParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewParams0UniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewParams1UniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewColorAUniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewColorBUniformHandle = BGFX_INVALID_HANDLE;
        m_indexBufferHandle = BGFX_INVALID_HANDLE;
        m_filledTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_skyVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bmodelVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bmodelCollisionVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_vertexBufferHandle = BGFX_INVALID_HANDLE;

        m_bmodelTextureAnimations.clear();
        m_resolvedBModelDrawGroups.clear();
        m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();

        m_texturedBModelBatches.clear();
        OutdoorBillboardRenderer::invalidateRenderAssets(*this);
        OutdoorRenderer::invalidateSkyResources(*this);
        screenRuntime.releaseHudGpuResources(false);
        m_interactiveDecorationBindings.clear();
        screenRuntime.clearSharedUiRuntime();
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

    if (bgfx::isValid(m_spellAreaPreviewProgramHandle))
    {
        bgfx::destroy(m_spellAreaPreviewProgramHandle);
        m_spellAreaPreviewProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorLitBillboardProgramHandle))
    {
        bgfx::destroy(m_outdoorLitBillboardProgramHandle);
        m_outdoorLitBillboardProgramHandle = BGFX_INVALID_HANDLE;
    }

    ParticleRenderer::shutdownResources(m_worldFxRenderResources);

    if (bgfx::isValid(m_outdoorTexturedFogProgramHandle))
    {
        bgfx::destroy(m_outdoorTexturedFogProgramHandle);
        m_outdoorTexturedFogProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorForcePerspectiveProgramHandle))
    {
        bgfx::destroy(m_outdoorForcePerspectiveProgramHandle);
        m_outdoorForcePerspectiveProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureAtlasHandle))
    {
        bgfx::destroy(m_terrainTextureAtlasHandle);
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bloodSplatTextureHandle))
    {
        bgfx::destroy(m_bloodSplatTextureHandle);
        m_bloodSplatTextureHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_forcePerspectiveSolidTextureHandle))
    {
        bgfx::destroy(m_forcePerspectiveSolidTextureHandle);
        m_forcePerspectiveSolidTextureHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        bgfx::destroy(m_terrainTextureSamplerHandle);
        m_terrainTextureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorBillboardAmbientUniformHandle))
    {
        bgfx::destroy(m_outdoorBillboardAmbientUniformHandle);
        m_outdoorBillboardAmbientUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorBillboardOverrideColorUniformHandle))
    {
        bgfx::destroy(m_outdoorBillboardOverrideColorUniformHandle);
        m_outdoorBillboardOverrideColorUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorBillboardOutlineParamsUniformHandle))
    {
        bgfx::destroy(m_outdoorBillboardOutlineParamsUniformHandle);
        m_outdoorBillboardOutlineParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorFxLightPositionsUniformHandle))
    {
        bgfx::destroy(m_outdoorFxLightPositionsUniformHandle);
        m_outdoorFxLightPositionsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorFxLightColorsUniformHandle))
    {
        bgfx::destroy(m_outdoorFxLightColorsUniformHandle);
        m_outdoorFxLightColorsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorFxLightParamsUniformHandle))
    {
        bgfx::destroy(m_outdoorFxLightParamsUniformHandle);
        m_outdoorFxLightParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorFogColorUniformHandle))
    {
        bgfx::destroy(m_outdoorFogColorUniformHandle);
        m_outdoorFogColorUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorFogDensitiesUniformHandle))
    {
        bgfx::destroy(m_outdoorFogDensitiesUniformHandle);
        m_outdoorFogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_outdoorFogDistancesUniformHandle))
    {
        bgfx::destroy(m_outdoorFogDistancesUniformHandle);
        m_outdoorFogDistancesUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_secretPulseParamsUniformHandle))
    {
        bgfx::destroy(m_secretPulseParamsUniformHandle);
        m_secretPulseParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spellAreaPreviewParams0UniformHandle))
    {
        bgfx::destroy(m_spellAreaPreviewParams0UniformHandle);
        m_spellAreaPreviewParams0UniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spellAreaPreviewParams1UniformHandle))
    {
        bgfx::destroy(m_spellAreaPreviewParams1UniformHandle);
        m_spellAreaPreviewParams1UniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spellAreaPreviewColorAUniformHandle))
    {
        bgfx::destroy(m_spellAreaPreviewColorAUniformHandle);
        m_spellAreaPreviewColorAUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spellAreaPreviewColorBUniformHandle))
    {
        bgfx::destroy(m_spellAreaPreviewColorBUniformHandle);
        m_spellAreaPreviewColorBUniformHandle = BGFX_INVALID_HANDLE;
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

    for (BModelTextureAnimationHandle &animation : m_bmodelTextureAnimations)
    {
        for (bgfx::TextureHandle textureHandle : animation.frameTextureHandles)
        {
            if (bgfx::isValid(textureHandle))
            {
                bgfx::destroy(textureHandle);
            }
        }

        animation.frameTextureHandles.clear();
        animation.frameLengthTicks.clear();
        animation.animationLengthTicks = 0;
    }

    m_texturedBModelBatches.clear();
    m_bmodelTextureAnimations.clear();
    for (ResolvedBModelDrawGroup &group : m_resolvedBModelDrawGroups)
    {
        if (bgfx::isValid(group.vertexBufferHandle))
        {
            bgfx::destroy(group.vertexBufferHandle);
            group.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        group.vertexCount = 0;
        group.animationIndex = static_cast<size_t>(-1);
    }
    m_resolvedBModelDrawGroups.clear();
    m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
    OutdoorBillboardRenderer::destroyRenderAssets(*this);
    OutdoorRenderer::destroySkyResources(*this);

    screenRuntime.releaseHudGpuResources(true);
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

    if (bgfx::isValid(m_bloodSplatVertexBufferHandle))
    {
        bgfx::destroy(m_bloodSplatVertexBufferHandle);
        m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
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
    m_pGameAudioSystem = nullptr;
    m_outdoorDecorationBillboardSet.reset();
    m_outdoorActorPreviewBillboardSet.reset();
    m_outdoorSpriteObjectBillboardSet.reset();
    m_elapsedTime = 0.0f;
    m_framesPerSecond = 0.0f;
    m_lastOutdoorFxLightUniformUpdateElapsedTime = -1.0f;
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
    m_toggleTextureFilteringLatch = false;
    m_inspectMode = true;
    m_toggleInspectLatch = false;
    m_triggerMeteorLatch = false;
    worldInteractionInputState.keyboardUseLatch = false;
    worldInteractionInputState.inspectKeyboardActivateLatch = false;
    screenRuntime.resetOverlayInteractionState();
    worldInteractionInputState.inspectMouseActivateLatch = false;
    attackActionState.clear();
    pendingSpellCast.clickLatch = false;
    GameplayUiController::CharacterScreenState &characterScreen = screenRuntime.characterScreen();
    characterScreen.open = false;
    characterScreen.dollJewelryOverlayOpen = false;
    characterScreen.adventurersInnRosterOverlayOpen = false;
    characterScreen.page = CharacterPage::Inventory;
    screenRuntime.clearSharedUiRuntime();
    characterScreen.source = CharacterScreenSource::Party;
    characterScreen.sourceIndex = 0;
    characterScreen.adventurersInnScrollOffset = 0;
    m_lastAdventurersInnPortraitClickTicks = 0;
    m_lastAdventurersInnPortraitClickedIndex = std::nullopt;
    GameplayHeldItemController::clearHeldInventoryItem(heldInventoryItem());
    screenRuntime.actorInspectOverlay() = {};
    screenRuntime.spellInspectOverlay() = {};
    screenRuntime.readableScrollOverlay() = {};
    screenRuntime.spellbook() = {};
    utilitySpellOverlay() = {};
    pendingSpellCast = {};
    quickSpellState.clear();
    m_spellAreaPreviewCache = {};
    worldInteractionInputState.heldInventoryDropLatch = false;
    worldInteractionInputState.pressedWorldHit = {};
    m_cachedHoverInspectHitValid = false;
    m_lastHoverInspectUpdateNanoseconds = 0;
    m_cachedHoverInspectHit = {};
    screenRuntime.eventDialogSelectionIndex() = 0;
    screenRuntime.activeEventDialog() = {};
    gameplayMouseLookState.clear();
    m_isRotatingCamera = false;
    m_lastMouseX = 0.0f;
    m_lastMouseY = 0.0f;
    m_lastFootstepX = 0.0f;
    m_lastFootstepY = 0.0f;
    m_hasLastFootstepPosition = false;
    m_walkingMotionHoldSeconds = 0.0f;
    m_activeWalkingSoundId = std::nullopt;
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

void OutdoorGameView::syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled)
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

void OutdoorGameView::syncCursorToGameplayCrosshair()
{
    const GameplayScreenState::GameplayMouseLookState &mouseLookState =
        m_gameSession.gameplayScreenState().gameplayMouseLookState();

    if (!mouseLookState.mouseLookActive || mouseLookState.cursorModeActive)
    {
        return;
    }

    SDL_Window *pWindow = SDL_GetMouseFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetKeyboardFocus();
    }

    if (pWindow == nullptr)
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

    const float cursorX = static_cast<float>(windowWidth) * 0.5f;
    const float cursorY = static_cast<float>(windowHeight) * 0.5f;
    SDL_WarpMouseInWindow(pWindow, cursorX, cursorY);
    m_lastMouseX = cursorX;
    m_lastMouseY = cursorY;
    m_gameSession.requestRelativeMouseMotionReset();
}

float OutdoorGameView::effectiveCameraYawRadians() const
{
    if (m_pOutdoorWorldRuntime == nullptr)
    {
        return m_cameraYawRadians;
    }

    return m_cameraYawRadians + m_pOutdoorWorldRuntime->armageddonCameraShakeYawRadians();
}

float OutdoorGameView::effectiveCameraPitchRadians() const
{
    if (m_pOutdoorWorldRuntime == nullptr)
    {
        return m_cameraPitchRadians;
    }

    return m_cameraPitchRadians + m_pOutdoorWorldRuntime->armageddonCameraShakePitchRadians();
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

void OutdoorGameView::reopenMenuScreen()
{
    m_gameSession.gameplayScreenRuntime().openMenuOverlay();
}

void OutdoorGameView::updateHouseVideoPlayback(float deltaSeconds)
{
    const EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const uint32_t hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
    const HouseEntry *pHostHouseEntry =
        hostHouseId != 0 ? m_gameSession.data().houseTable().get(hostHouseId) : nullptr;
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    const EventDialogContent &activeDialog = screenRuntime.activeEventDialog();

    if (resolveGameplayHudScreenState(
            m_gameSession.gameplayUiController(),
            activeDialog,
            m_pOutdoorWorldRuntime)
            != GameplayHudScreenState::Dialogue
        || !activeDialog.isActive
        || m_pAssetFileSystem == nullptr)
    {
        if (m_activeHouseAudioHostId != 0 && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::WoodDoorClosing, GameAudioSystem::PlaybackGroup::HouseDoor);
            m_pGameAudioSystem->resumeBackgroundMusic();
        }

        m_activeHouseAudioHostId = 0;
        m_gameSession.gameplayScreenRuntime().stopHouseVideoPlayback();
        return;
    }

    if (!activeDialog.videoName.empty())
    {
        if (m_activeHouseAudioHostId != 0 && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->resumeBackgroundMusic();
        }

        m_activeHouseAudioHostId = 0;
        m_gameSession.gameplayScreenRuntime().playHouseVideo(activeDialog.videoName, activeDialog.videoDirectory);
        m_gameSession.gameplayScreenRuntime().updateHouseVideoPlayback(deltaSeconds);
        return;
    }

    if (pHostHouseEntry == nullptr || pHostHouseEntry->videoName.empty())
    {
        if (m_activeHouseAudioHostId != 0 && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::WoodDoorClosing, GameAudioSystem::PlaybackGroup::HouseDoor);
            m_pGameAudioSystem->resumeBackgroundMusic();
        }

        m_activeHouseAudioHostId = 0;
        m_gameSession.gameplayScreenRuntime().stopHouseVideoPlayback();
        return;
    }

    if (m_activeHouseAudioHostId != pHostHouseEntry->id)
    {
        m_activeHouseAudioHostId = pHostHouseEntry->id;

        if (m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->pauseBackgroundMusic();
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

    m_gameSession.gameplayScreenRuntime().playHouseVideo(pHostHouseEntry->videoName);

    if (!houseShopOverlay().active)
    {
        m_gameSession.gameplayScreenRuntime().updateHouseVideoPlayback(deltaSeconds);
    }
}

bool OutdoorGameView::hasActiveEventDialog() const
{
    return m_gameSession.gameplayScreenRuntime().activeEventDialog().isActive;
}

void OutdoorGameView::updateItemInspectOverlayState(int width, int height, const GameplayInputFrame &input)
{
    GameplayScreenRuntime &overlayContext = m_gameSession.gameplayScreenRuntime();
    GameplayUiController::ItemInspectOverlayState &itemInspectOverlay = overlayContext.itemInspectOverlay();

    itemInspectOverlay = {};

    if (!GameplayScreenController::canUpdateStandardHudItemInspectOverlayFromMouse(
            overlayContext,
            width,
            height,
            m_gameSession.gameplayScreenState().pendingSpellTarget().active))
    {
        return;
    }

    GameplayScreenController::updateStandardHudItemInspectOverlayFromMouse(
        overlayContext,
        input,
        width,
        height,
        true,
        true);

    if (overlayContext.itemInspectOverlayReadOnly().active)
    {
        return;
    }

    const float mouseX = input.pointerX;
    const float mouseY = input.pointerY;

    if (!input.rightMouseButton.held)
    {
        return;
    }

    const bool hasActiveLootView =
        m_pOutdoorWorldRuntime != nullptr
        && (m_pOutdoorWorldRuntime->activeChestView() != nullptr
            || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);

    if (!GameplayScreenController::canUpdateStandardWorldInspectOverlayFromMouse(
            overlayContext,
            GameplayStandardWorldInspectOverlayConfig{
                .width = width,
                .height = height,
                .worldReady = m_pOutdoorWorldRuntime != nullptr && m_outdoorMapData.has_value(),
                .hasHeldItem = heldInventoryItem().active,
                .hasPendingSpellTarget = m_gameSession.gameplayScreenState().pendingSpellTarget().active,
                .hasActiveLootView = hasActiveLootView,
            }))
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
        const float cameraYawRadians = effectiveCameraYawRadians();
        const float cameraPitchRadians = effectiveCameraPitchRadians();
        const float cosPitch = std::cos(cameraPitchRadians);
        const float sinPitch = std::sin(cameraPitchRadians);
        const float cosYaw = std::cos(cameraYawRadians);
        const float sinYaw = std::sin(cameraYawRadians);
        const bx::Vec3 eye = {
            m_cameraTargetX,
            m_cameraTargetY,
            m_cameraTargetZ
        };
        const bx::Vec3 at = {
            m_cameraTargetX + cosYaw * cosPitch,
            m_cameraTargetY + sinYaw * cosPitch,
            m_cameraTargetZ + sinPitch
        };
        const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
        bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
        bx::mtxProj(
            projectionMatrix,
            CameraVerticalFovDegrees,
            aspectRatio,
            0.1f,
            200000.0f,
            bgfx::getCaps()->homogeneousDepth,
            bx::Handedness::Right
        );

        const float normalizedMouseX = ((input.pointerX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY = 1.0f - ((input.pointerY / static_cast<float>(viewHeight)) * 2.0f);
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
            itemInspectOverlay.active = true;
            itemInspectOverlay.objectDescriptionId = pWorldItem->item.objectDescriptionId;
            itemInspectOverlay.hasItemState = !pWorldItem->isGold;
            itemInspectOverlay.itemState = pWorldItem->item;
            itemInspectOverlay.sourceType = ItemInspectSourceType::WorldItem;
            itemInspectOverlay.sourceWorldItemIndex = inspectHit.bModelIndex;
            itemInspectOverlay.hasValueOverride = pWorldItem->isGold;
            itemInspectOverlay.valueOverride = static_cast<int>(pWorldItem->goldAmount);
            itemInspectOverlay.sourceX = mouseX;
            itemInspectOverlay.sourceY = mouseY;
            itemInspectOverlay.sourceWidth = 1.0f;
            itemInspectOverlay.sourceHeight = 1.0f;
            GameplayScreenController::applySharedItemInspectSkillInteraction(overlayContext);
            return;
        }
    }
}

bool OutdoorGameView::trySaveToSelectedGameSlot()
{
    return m_gameSession.gameplayScreenRuntime().trySaveToSelectedGameSlot(
        [this](const GameplayScreenRuntime::PreparedSaveGameRequest &request)
        {
            return beginSaveWithPreview(request.path, request.saveName, true);
        });
}

bool OutdoorGameView::requestQuickSave()
{
    return beginSaveWithPreview(std::filesystem::path("saves") / "quicksave.oysav", "", false);
}

bool OutdoorGameView::beginSaveWithPreview(
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

void OutdoorGameView::clearWorldInteractionInputLatches()
{
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    GameplayScreenState &gameplayScreenState = m_gameSession.gameplayScreenState();
    PendingSpellCastState &pendingSpellCast = gameplayScreenState.pendingSpellTarget();
    QuickSpellState &quickSpellState = gameplayScreenState.quickSpellState();
    AttackActionState &attackActionState = gameplayScreenState.attackActionState();
    WorldInteractionInputState &worldInteractionInputState = gameplayScreenState.worldInteractionInputState();

    worldInteractionInputState.keyboardUseLatch = false;
    worldInteractionInputState.inspectKeyboardActivateLatch = false;
    pendingSpellCast.clickLatch = false;
    worldInteractionInputState.heldInventoryDropLatch = false;
    m_gameSession.overlayInteractionState().activateInspectLatch = false;
    worldInteractionInputState.inspectMouseActivateLatch = false;
    worldInteractionInputState.pressedWorldHit = {};
    attackActionState.clear();
    quickSpellState.clear();
    m_cachedHoverInspectHitValid = false;
    m_lastHoverInspectUpdateNanoseconds = 0;
    m_cachedHoverInspectHit = {};
    screenRuntime.mutableStatusBarHoverText().clear();
}

float OutdoorGameView::innRestDurationMinutes(uint32_t houseId) const
{
    if (m_pOutdoorWorldRuntime == nullptr)
    {
        return 8.0f * 60.0f;
    }

    int currentMinuteOfDay = static_cast<int>(std::floor(m_pOutdoorWorldRuntime->gameMinutes()));
    currentMinuteOfDay %= MinutesPerDay;

    if (currentMinuteOfDay < 0)
    {
        currentMinuteOfDay += MinutesPerDay;
    }

    int minutesUntilDawn = InnRestDawnHour * 60 - currentMinuteOfDay;

    if (minutesUntilDawn <= 0)
    {
        minutesUntilDawn += MinutesPerDay;
    }

    float durationMinutes = static_cast<float>(minutesUntilDawn) + 60.0f;

    if (houseId == DeyjaTavernHouseId
        || houseId == PitTavernHouseId
        || houseId == MountNighonTavernHouseId)
    {
        durationMinutes += 12.0f * 60.0f;
    }

    return durationMinutes;
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

const AdventurersInnMember *OutdoorGameView::selectedAdventurersInnMember() const
{
    const GameplayUiController::CharacterScreenState &characterScreen =
        m_gameSession.gameplayScreenRuntime().characterScreenReadOnly();

    if (m_pOutdoorPartyRuntime == nullptr || characterScreen.source != CharacterScreenSource::AdventurersInn)
    {
        return nullptr;
    }

    return m_pOutdoorPartyRuntime->party().adventurersInnMember(characterScreen.sourceIndex);
}

AdventurersInnMember *OutdoorGameView::selectedAdventurersInnMember()
{
    const GameplayUiController::CharacterScreenState &characterScreen =
        m_gameSession.gameplayScreenRuntime().characterScreenReadOnly();

    if (m_pOutdoorPartyRuntime == nullptr || characterScreen.source != CharacterScreenSource::AdventurersInn)
    {
        return nullptr;
    }

    return m_pOutdoorPartyRuntime->party().adventurersInnMember(characterScreen.sourceIndex);
}

void OutdoorGameView::consumePendingWorldAudioEvents()
{
    OutdoorPresentationController::consumePendingWorldAudioEvents(*this);
}

void OutdoorGameView::updateFootstepAudio(float deltaSeconds)
{
    OutdoorPresentationController::updateFootstepAudio(*this, deltaSeconds);
}

bool OutdoorGameView::tryCastSpellRequest(const PartySpellCastRequest &request, const std::string &spellName)
{
    if (m_pOutdoorPartyRuntime == nullptr || m_pOutdoorWorldRuntime == nullptr)
    {
        return false;
    }

    PartySpellCastRequest resolvedRequest = request;
    resolvedRequest.hasViewTransform = true;
    resolvedRequest.viewX = m_cameraTargetX;
    resolvedRequest.viewY = m_cameraTargetY;
    resolvedRequest.viewZ = m_cameraTargetZ;
    resolvedRequest.viewYawRadians = effectiveCameraYawRadians();
    resolvedRequest.viewPitchRadians = effectiveCameraPitchRadians();
    resolvedRequest.viewAspectRatio =
        static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(std::max(m_lastRenderHeight, 1));

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    const GameplaySpellService::SpellRequestResolution resolution =
        m_gameSession.gameplaySpellService().resolveSpellRequest(screenRuntime, resolvedRequest, spellName);

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::CastSucceeded)
    {
        m_worldFxSystem.triggerPartySpellFx(resolution.castResult);
        m_gameSession.gameplaySpellService().clearPendingTargetSelection(
            screenRuntime,
            "Cast " + spellName);
        return true;
    }

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::NeedsTargetSelection)
    {
        m_gameSession.gameplaySpellService().armPendingTargetSelection(
            screenRuntime,
            request,
            resolution.castResult.targetKind,
            spellName);
        m_cachedHoverInspectHitValid = false;
        return true;
    }

    if (resolution.disposition == GameplaySpellService::SpellRequestDisposition::OpenedSelectionUi)
    {
        return true;
    }

    return false;
}

OutdoorGameView::HeldInventoryItemState &OutdoorGameView::heldInventoryItem()
{
    return m_gameSession.gameplayScreenRuntime().heldInventoryItem();
}

const OutdoorGameView::HeldInventoryItemState &OutdoorGameView::heldInventoryItem() const
{
    return m_gameSession.gameplayScreenRuntime().heldInventoryItem();
}

OutdoorGameView::UtilitySpellOverlayState &OutdoorGameView::utilitySpellOverlay()
{
    return m_gameSession.gameplayScreenRuntime().utilitySpellOverlay();
}

const OutdoorGameView::UtilitySpellOverlayState &OutdoorGameView::utilitySpellOverlay() const
{
    return m_gameSession.gameplayScreenRuntime().utilitySpellOverlayReadOnly();
}

GameplayUiController::HouseShopOverlayState &OutdoorGameView::houseShopOverlay()
{
    return m_gameSession.gameplayScreenRuntime().houseShopOverlay();
}

const GameplayUiController::HouseShopOverlayState &OutdoorGameView::houseShopOverlay() const
{
    return m_gameSession.gameplayScreenRuntime().houseShopOverlay();
}

void OutdoorGameView::showStatusBarEvent(const std::string &text, float durationSeconds)
{
    setStatusBarEvent(text, durationSeconds);
}

void OutdoorGameView::setSettingsSnapshot(const GameSettings &settings)
{
    m_gameSettings = settings;

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        Party &party = m_pOutdoorPartyRuntime->party();
        party.setDebugDamageImmune(settings.immortal);
        party.setDebugUnlimitedMana(settings.unlimitedMana);
    }
}

const GameSettings &OutdoorGameView::settingsSnapshot() const
{
    return m_gameSettings;
}

void OutdoorGameView::showCombatStatusBarEvent(const std::string &text, float durationSeconds)
{
    if (!m_showHitStatusMessages)
    {
        return;
    }

    setStatusBarEvent(text, durationSeconds);
}

void OutdoorGameView::setMouseRotateSpeed(float speed)
{
    m_mouseRotateSpeed = std::clamp(speed, 0.0005f, 0.05f);
}

void OutdoorGameView::setWalkSoundEnabled(bool active)
{
    m_walkSoundEnabled = active;
}

void OutdoorGameView::setShowHitStatusMessages(bool active)
{
    m_showHitStatusMessages = active;
}

void OutdoorGameView::setFlipOnExitEnabled(bool active)
{
    m_flipOnExitEnabled = active;
}

OutdoorPartyRuntime *OutdoorGameView::partyRuntime() const
{
    return m_pOutdoorPartyRuntime;
}

IGameplayWorldRuntime *OutdoorGameView::worldRuntime() const
{
    return m_pOutdoorWorldRuntime;
}

GameAudioSystem *OutdoorGameView::audioSystem() const
{
    return m_pGameAudioSystem;
}

const GameDataRepository &OutdoorGameView::data() const
{
    return m_gameSession.data();
}

float OutdoorGameView::gameplayCameraYawRadians() const
{
    return effectiveCameraYawRadians();
}

void OutdoorGameView::executeActiveDialogAction()
{
    if (m_pOutdoorWorldRuntime != nullptr)
    {
        m_pOutdoorWorldRuntime->executeActiveDialogAction();
    }
}

GameSettings &OutdoorGameView::mutableSettings()
{
    return m_gameSettings;
}

std::array<uint8_t, SDL_SCANCODE_COUNT> &OutdoorGameView::previousKeyboardState()
{
    return m_gameSession.previousKeyboardState();
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &OutdoorGameView::previousKeyboardState() const
{
    return m_gameSession.previousKeyboardState();
}

void OutdoorGameView::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_gameSession.gameplayScreenRuntime().setStatusBarEvent(text, durationSeconds);
}

void OutdoorGameView::updateActorInspectOverlayState(int width, int height, const GameplayInputFrame &input)
{
    GameplayScreenRuntime &overlayContext = m_gameSession.gameplayScreenRuntime();
    GameplayUiController::ActorInspectOverlayState &actorInspectOverlay = overlayContext.actorInspectOverlay();

    actorInspectOverlay = {};

    const bool hasActiveLootView =
        m_pOutdoorWorldRuntime != nullptr
        && (m_pOutdoorWorldRuntime->activeChestView() != nullptr
            || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);

    if (!GameplayScreenController::canUpdateStandardWorldInspectOverlayFromMouse(
            overlayContext,
            GameplayStandardWorldInspectOverlayConfig{
                .width = width,
                .height = height,
                .worldReady = m_pOutdoorWorldRuntime != nullptr && m_outdoorMapData.has_value(),
                .hasHeldItem = heldInventoryItem().active,
                .hasPendingSpellTarget = m_gameSession.gameplayScreenState().pendingSpellTarget().active,
                .hasActiveLootView = hasActiveLootView,
            }))
    {
        return;
    }

    if (!input.rightMouseButton.held)
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
        const float cameraYawRadians = effectiveCameraYawRadians();
        const float cameraPitchRadians = effectiveCameraPitchRadians();
        const float cosPitch = std::cos(cameraPitchRadians);
        const float sinPitch = std::sin(cameraPitchRadians);
        const float cosYaw = std::cos(cameraYawRadians);
        const float sinYaw = std::sin(cameraYawRadians);
        const bx::Vec3 eye = {
            m_cameraTargetX,
            m_cameraTargetY,
            m_cameraTargetZ
        };
        const bx::Vec3 at = {
            m_cameraTargetX + cosYaw * cosPitch,
            m_cameraTargetY + sinYaw * cosPitch,
            m_cameraTargetZ + sinPitch
        };
        const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
        bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
        bx::mtxProj(
            projectionMatrix,
            CameraVerticalFovDegrees,
            aspectRatio,
            0.1f,
            200000.0f,
            bgfx::getCaps()->homogeneousDepth,
            bx::Handedness::Right
        );

        const float normalizedMouseX = ((input.pointerX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY = 1.0f - ((input.pointerY / static_cast<float>(viewHeight)) * 2.0f);
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
                input.pointerX,
                input.pointerY,
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

    const std::optional<size_t> runtimeActorIndex =
        OutdoorInteractionController::resolveRuntimeActorIndexForInspectHit(*this, inspectHit);

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
    const float cameraYawRadians = effectiveCameraYawRadians();
    const float cameraPitchRadians = effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const float sinPitch = std::sin(cameraPitchRadians);
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const bx::Vec3 eye = {
        m_cameraTargetX,
        m_cameraTargetY,
        m_cameraTargetZ
    };
    const bx::Vec3 at = {
        m_cameraTargetX + cosYaw * cosPitch,
        m_cameraTargetY + sinYaw * cosPitch,
        m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        200000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
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

    actorInspectOverlay.active = true;
    actorInspectOverlay.runtimeActorIndex = *runtimeActorIndex;
    actorInspectOverlay.sourceX = rectMinX;
    actorInspectOverlay.sourceY = rectMinY;
    actorInspectOverlay.sourceWidth = std::max(1.0f, rectMaxX - rectMinX);
    actorInspectOverlay.sourceHeight = std::max(1.0f, rectMaxY - rectMinY);
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
        .add(bgfx::Attrib::TexCoord1, 1, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord3, 4, bgfx::AttribType::Float)
        .end();
}

void OutdoorGameView::LitBillboardVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void OutdoorGameView::ForcePerspectiveVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord1, 4, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord2, 1, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
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
    return GameplayHudCommon::findCachedAssetPath(
        m_pAssetFileSystem,
        m_spriteLoadCache,
        directoryPath,
        fileName);
}

std::optional<std::vector<uint8_t>> OutdoorGameView::readCachedBinaryFile(const std::string &assetPath)
{
    return GameplayHudCommon::readCachedBinaryFile(
        m_pAssetFileSystem,
        m_spriteLoadCache,
        assetPath);
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

}
