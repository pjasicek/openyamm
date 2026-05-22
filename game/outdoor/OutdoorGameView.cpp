#include "game/outdoor/OutdoorGameView.h"

#include "game/app/GameSession.h"
#include "engine/BgfxContext.h"
#include "game/arpg/ArpgModeLoot.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/FaceEnums.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/fx/ParticleRenderer.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/MercenaryRecruitmentRuntime.h"
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
#include "game/maps/MapIdentity.h"
#include "game/maps/SaveGame.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/SpawnPreview.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/party/SpellSchool.h"
#include "game/party/SpellIds.h"
#include "game/SpriteObjectDefs.h"
#include "game/tables/SpriteTables.h"
#include "game/StringUtils.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "engine/ImageAssetLoader.h"
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
bool isAutosavePath(const std::filesystem::path &path)
{
    return toLowerCopy(path.stem().string()) == "autosave";
}

double millisecondsFromNanoseconds(uint64_t nanoseconds)
{
    return static_cast<double>(nanoseconds) / 1000000.0;
}

bool mapLoadTimingEnabled()
{
    const char *pValue = std::getenv("OPENYAMM_MAP_LOAD_TIMING");
    return pValue != nullptr && std::string_view(pValue) != "0" && std::string_view(pValue) != "false";
}

bool windowHasInputFocus(SDL_Window *pWindow)
{
    return pWindow != nullptr && (SDL_GetWindowFlags(pWindow) & SDL_WINDOW_INPUT_FOCUS) != 0;
}

class OutdoorViewLoadTimingLogger
{
public:
    explicit OutdoorViewLoadTimingLogger(const std::string &mapFileName)
        : m_enabled(mapLoadTimingEnabled())
        , m_mapFileName(mapFileName)
        , m_startTickNanoseconds(SDL_GetTicksNS())
        , m_lastTickNanoseconds(m_startTickNanoseconds)
    {
        if (m_enabled)
        {
            std::cerr
                << "[MapLoadTiming] map=" << m_mapFileName
                << " begin=outdoor_view_initialize\n";
        }
    }

    void stage(const std::string &stageName)
    {
        if (!m_enabled)
        {
            return;
        }

        const uint64_t nowNanoseconds = SDL_GetTicksNS();
        const uint64_t stageNanoseconds = nowNanoseconds - m_lastTickNanoseconds;
        const uint64_t totalNanoseconds = nowNanoseconds - m_startTickNanoseconds;
        m_lastTickNanoseconds = nowNanoseconds;

        std::cerr
            << "[MapLoadTiming] map=" << m_mapFileName
            << " scope=outdoor_view_initialize"
            << " stage=\"" << stageName << "\""
            << " delta_ms=" << millisecondsFromNanoseconds(stageNanoseconds)
            << " total_ms=" << millisecondsFromNanoseconds(totalNanoseconds)
            << '\n';
    }

private:
    bool m_enabled = false;
    std::string m_mapFileName;
    uint64_t m_startTickNanoseconds = 0;
    uint64_t m_lastTickNanoseconds = 0;
};

std::string engineDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/" + std::string(fileName);
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
constexpr uint64_t GameplayMouseLookCursorSyncIntervalTicks = 100;
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
        || houseEntry.type.find(" Guild") != std::string::npos
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
constexpr float DefaultOutdoorFarClip = 18000.0f;
constexpr float RuntimeProjectileRenderDistance = 12288.0f;
constexpr float DecorationBillboardRenderDistance = 18000.0f;
constexpr float ActorBillboardRenderDistance = 18000.0f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovDegrees = 60.0f;
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
constexpr uint64_t BillboardAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;
constexpr bool DebugSpritePreloadLogging = false;
constexpr std::string_view PartyStartDecorationName = "party start";
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr uint64_t OutdoorFrameTimingWindowNanoseconds = 3ULL * 1000ULL * 1000ULL * 1000ULL;
constexpr uint64_t OutdoorFrameTimingLogThresholdNanoseconds = 8ULL * 1000ULL * 1000ULL;

std::string actPaletteCacheKey(int16_t paletteId, const std::string &worldId)
{
    const std::string normalizedWorldId = worldId.empty() ? std::string() : normalizeWorldId(worldId);
    return normalizedWorldId + "|" + std::to_string(static_cast<int>(paletteId));
}

std::vector<std::string> actPaletteCandidatePaths(int16_t paletteId, const std::string &worldId)
{
    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));

    std::vector<std::string> paths;

    if (!worldId.empty())
    {
        paths.push_back("worlds/" + normalizeWorldId(worldId) + "/textures/" + paletteFileName);
    }

    paths.push_back(std::string("Data/bitmaps/") + paletteFileName);
    return paths;
}
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
        assetFileSystem.readTextFile(engineDataTablePath("decoration_data.txt"));

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
    const std::string &virtualPath,
    const std::optional<std::array<uint8_t, 256 * 3>> &overridePalette,
    int &width,
    int &height
)
{
    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = overridePalette;
    decodeOptions.applyPaletteZeroTransparencyKey = true;

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(bitmapBytes, virtualPath, decodeOptions);

    if (!image)
    {
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    return image->pixels;
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

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    const std::filesystem::path configuredShaderRoot = OPENYAMM_BGFX_SHADER_DIR;
    std::string rendererDirectory;

    switch (rendererType)
    {
    case bgfx::RendererType::Direct3D11:
        rendererDirectory = "dxbc";
        break;

    case bgfx::RendererType::OpenGL:
        rendererDirectory = "glsl";
        break;

    case bgfx::RendererType::OpenGLES:
        rendererDirectory = "essl";
        break;

    default:
        return {};
    }

    const std::filesystem::path shaderName =
        std::filesystem::path(rendererDirectory) / (std::string(pShaderName) + ".bin");

    if (configuredShaderRoot.is_absolute())
    {
        return configuredShaderRoot / shaderName;
    }

    if (const char *pBasePath = SDL_GetBasePath())
    {
        const std::filesystem::path executableRoot = pBasePath;
        const std::filesystem::path packagedPath = executableRoot / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(packagedPath))
        {
            return packagedPath;
        }

        const std::filesystem::path buildTreePath = executableRoot / ".." / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(buildTreePath))
        {
            return buildTreePath;
        }

        return packagedPath;
    }

    return configuredShaderRoot / shaderName;
}

bool hasOutdoorCameraMotionInput(const GameplayInputFrame &input)
{
    return input.relativeMouseX != 0.0f
        || input.relativeMouseY != 0.0f
        || input.action(KeyboardAction::Forward).held
        || input.action(KeyboardAction::Backward).held
        || input.action(KeyboardAction::Left).held
        || input.action(KeyboardAction::Right).held
        || input.action(KeyboardAction::Jump).held
        || input.action(KeyboardAction::LookUp).held
        || input.action(KeyboardAction::LookDown).held
        || input.action(KeyboardAction::FlyUp).held
        || input.action(KeyboardAction::FlyDown).held;
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
    , m_outdoorFaceAlphaParamsUniformHandle(BGFX_INVALID_HANDLE)
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
    , m_isRotatingCamera(false)
    , m_lastMouseX(0.0f)
    , m_lastMouseY(0.0f)
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
    , m_renderableStartTickNanoseconds(0)
    , m_renderFrameIndex(0)
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
    OutdoorViewLoadTimingLogger timingLogger(map.fileName);
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
    m_arpgModeHasMoveDestination = false;
    m_arpgModeActionAnimationSeconds = 0.0f;
    m_arpgModeActionAnimationDurationSeconds = 0.0f;
    m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    m_arpgModeActionAnimationIsCast = false;
    m_arpgModeDelayedSpellActive = false;
    m_arpgModeReleasingDelayedSpell = false;
    m_arpgModeDelayedSpellRequest = {};
    m_arpgModeDelayedSpellName.clear();
    m_arpgModeDelayedSpellReleaseSeconds = 0.0f;
    refreshViewDistanceCache();
    m_gameSession.gameplayScreenRuntime().bindSceneAdapter(this);
    m_gameSession.gameplayScreenRuntime().bindAudioSystem(m_pGameAudioSystem);
    m_gameSession.gameplayScreenRuntime().bindSettings(&m_gameSettings);
    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    EventRuntimeState *pMutableEventRuntimeState = m_pOutdoorWorldRuntime->eventRuntimeState();
    timingLogger.stage("view state assigned");

    if (pMutableEventRuntimeState != nullptr && m_pOutdoorPartyRuntime != nullptr)
    {
        refreshMercenaryRecruitmentForCurrentMap(
            map,
            m_pOutdoorPartyRuntime->party(),
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
    timingLogger.stage("mercenary recruitment refreshed");

    const EventRuntimeState *pEventRuntimeState = pMutableEventRuntimeState;
    screenRuntime.resetOverlayInteractionState(
        pEventRuntimeState != nullptr && !pEventRuntimeState->hiredNpcFollowers.empty());
    const GameplayScreenRuntime::SharedUiBootstrapResult sharedUiBootstrap =
        screenRuntime.initializeSharedUiRuntime(
            GameplayScreenRuntime::SharedUiBootstrapConfig{
                .pAssetFileSystem = &assetFileSystem,
                .portraitMemberCount =
                    m_pOutdoorPartyRuntime != nullptr
                        ? m_pOutdoorPartyRuntime->party().members().size()
                        : 0,
                .initializeHouseVideoPlayer = true,
                .preloadReferencedAssets = false,
            });
    timingLogger.stage("shared ui runtime initialized");

    OutdoorInteractionController::rebuildInteractiveDecorationBindings(*this);
    timingLogger.stage("interactive decoration bindings rebuilt");
    OutdoorInteractionController::seedInteractiveDecorationRuntimeStateIfNeeded(*this);
    timingLogger.stage("interactive decoration runtime seeded");
    OutdoorInteractionController::buildDecorationBillboardSpatialIndex(*this);
    timingLogger.stage("decoration billboard spatial index built");

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
    m_arpgModeMinimapArrowYawRadians = m_cameraYawRadians;
    m_cameraPitchRadians = -0.15f;
    m_cameraDistance = 0.0f;
    m_cameraOrthoScale = 1.2f;
    timingLogger.stage("party start resolved");

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        timingLogger.stage("noop renderer view initialized");
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
    timingLogger.stage("world render resources initialized");

    OutdoorBillboardRenderer::initializeBillboardResources(*this);
    timingLogger.stage("billboard resources initialized");
    ParticleRenderer::initializeResources(m_worldFxRenderResources);
    timingLogger.stage("particle resources initialized");

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
    m_outdoorFaceAlphaParamsUniformHandle =
        bgfx::createUniform("u_outdoorFaceAlphaParams", bgfx::UniformType::Vec4);
    m_spellAreaPreviewParams0UniformHandle = bgfx::createUniform("u_spellAreaParams0", bgfx::UniformType::Vec4);
    m_spellAreaPreviewParams1UniformHandle = bgfx::createUniform("u_spellAreaParams1", bgfx::UniformType::Vec4);
    m_spellAreaPreviewColorAUniformHandle = bgfx::createUniform("u_spellAreaColorA", bgfx::UniformType::Vec4);
    m_spellAreaPreviewColorBUniformHandle = bgfx::createUniform("u_spellAreaColorB", bgfx::UniformType::Vec4);
    timingLogger.stage("outdoor uniforms created");

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
        || !bgfx::isValid(m_secretPulseParamsUniformHandle)
        || !bgfx::isValid(m_outdoorFaceAlphaParamsUniformHandle))
    {
        std::cerr << "OutdoorGameView failed to create bgfx resources.\n";
        shutdown();
        return false;
    }

    m_isRenderable = true;
    m_renderableStartTickNanoseconds = SDL_GetTicksNS();
    m_renderFrameIndex = 0;
    timingLogger.stage("outdoor view initialize complete");
    return true;
}

void OutdoorGameView::render(int width, int height, const GameplayInputFrame &input, float deltaSeconds)
{
    m_renderGameplayUiThisFrame = false;

    if (!m_isInitialized)
    {
        return;
    }

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
    const float farClipDistance = m_viewDistanceCache.farClipDistance;
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
    const uint64_t frameIndex = ++m_renderFrameIndex;
    const bool frameTimingEnabled =
        mapLoadTimingEnabled()
        && m_renderableStartTickNanoseconds != 0
        && SDL_GetTicksNS() - m_renderableStartTickNanoseconds <= OutdoorFrameTimingWindowNanoseconds;
    const uint64_t frameStartTickNanoseconds = frameTimingEnabled ? SDL_GetTicksNS() : 0;
    uint64_t stageStartTickNanoseconds = frameStartTickNanoseconds;
    uint64_t overlayStageNanoseconds = 0;
    uint64_t spriteWarmupStageNanoseconds = 0;
    uint64_t matrixStageNanoseconds = 0;
    uint64_t fxStageNanoseconds = 0;
    uint64_t worldRenderStageNanoseconds = 0;
    uint64_t audioStageNanoseconds = 0;
    const auto captureFrameTimingStage =
        [&](uint64_t &stageNanoseconds)
        {
            if (!frameTimingEnabled)
            {
                return;
            }

            const uint64_t nowNanoseconds = SDL_GetTicksNS();
            stageNanoseconds += nowNanoseconds - stageStartTickNanoseconds;
            stageStartTickNanoseconds = nowNanoseconds;
        };

    updateHouseVideoPlayback(deltaSeconds);
    updateItemInspectOverlayState(width, height, input);
    updateActorInspectOverlayState(width, height, input);
    captureFrameTimingStage(overlayStageNanoseconds);

    const bool cameraMotionInput = hasOutdoorCameraMotionInput(input);
    const size_t pendingSpriteWarmupsBefore =
        m_nextPendingSpriteFrameWarmupIndex < m_pendingSpriteFrameWarmups.size()
            ? m_pendingSpriteFrameWarmups.size() - m_nextPendingSpriteFrameWarmupIndex
            : 0;
    const size_t pendingActorTextureUploadsBefore =
        m_pendingActorPreviewTexturePreload
            && m_nextPendingActorPreviewTextureUploadIndex < m_pendingActorPreviewTexturePreload->size()
            ? m_pendingActorPreviewTexturePreload->size() - m_nextPendingActorPreviewTextureUploadIndex
            : 0;
    OutdoorBillboardRenderer::queueRuntimeActorBillboardTextureWarmup(*this);
    const bool processSpriteWarmupsThisFrame = !cameraMotionInput;
    OutdoorBillboardRenderer::processActorPreviewTexturePreload(*this, 1);

    if (processSpriteWarmupsThisFrame)
    {
        OutdoorBillboardRenderer::processActorPreviewTexturePreload(*this, 2);
        OutdoorBillboardRenderer::processPendingSpriteFrameWarmups(*this, 1);
    }

    const size_t pendingSpriteWarmupsAfter =
        m_nextPendingSpriteFrameWarmupIndex < m_pendingSpriteFrameWarmups.size()
            ? m_pendingSpriteFrameWarmups.size() - m_nextPendingSpriteFrameWarmupIndex
            : 0;
    const size_t pendingActorTextureUploadsAfter =
        m_pendingActorPreviewTexturePreload
            && m_nextPendingActorPreviewTextureUploadIndex < m_pendingActorPreviewTexturePreload->size()
            ? m_pendingActorPreviewTexturePreload->size() - m_nextPendingActorPreviewTextureUploadIndex
            : 0;
    captureFrameTimingStage(spriteWarmupStageNanoseconds);

    const float wireframeAspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const ArpgModeCameraFrame cameraFrame = buildCameraFrame(viewWidth, viewHeight, farClipDistance);

    bgfx::setViewTransform(SkyViewId, cameraFrame.viewMatrix.data(), cameraFrame.projectionMatrix.data());
    bgfx::touch(SkyViewId);
    bgfx::setViewTransform(MainViewId, cameraFrame.viewMatrix.data(), cameraFrame.projectionMatrix.data());
    bgfx::touch(MainViewId);
    captureFrameTimingStage(matrixStageNanoseconds);

    m_worldFxSystem.setShadowsEnabled(m_gameSettings.shadows);
    m_worldFxSystem.updateParticles(deltaSeconds, gameplayMouseLookState.cursorModeActive);

    if (!gameplayMouseLookState.cursorModeActive)
    {
        const bool refreshSpatialFx = m_outdoorSpatialFxRuntime.beginFrame(*this, deltaSeconds);
        m_worldFxSystem.syncProjectileFx(m_gameSession, deltaSeconds, refreshSpatialFx);
        m_outdoorSpatialFxRuntime.syncSpatialFx(*this, refreshSpatialFx);
    }
    captureFrameTimingStage(fxStageNanoseconds);

    OutdoorRenderer::renderWorldPasses(
        *this,
        viewWidth,
        viewHeight,
        wireframeAspectRatio,
        farClipDistance,
        pAtmosphereState,
        cameraFrame.eye,
        cameraFrame.forward,
        cameraFrame.right,
        cameraFrame.up,
        cameraFrame.viewMatrix.data());
    renderArpgModeLootOverlay(width, height, cameraFrame, deltaSeconds);
    captureFrameTimingStage(worldRenderStageNanoseconds);

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
    consumePendingWorldAudioEvents();
    captureFrameTimingStage(audioStageNanoseconds);

    if (frameTimingEnabled)
    {
        const uint64_t frameTotalNanoseconds = SDL_GetTicksNS() - frameStartTickNanoseconds;

        if (frameTotalNanoseconds >= OutdoorFrameTimingLogThresholdNanoseconds)
        {
            const std::string mapFileName = m_map.has_value() ? m_map->fileName : std::string();
            std::cerr
                << "[MapLoadTiming] map=" << mapFileName
                << " scope=outdoor_frame"
                << " frame=" << frameIndex
                << " since_renderable_ms="
                << millisecondsFromNanoseconds(frameStartTickNanoseconds - m_renderableStartTickNanoseconds)
                << " total_ms=" << millisecondsFromNanoseconds(frameTotalNanoseconds)
                << " overlay_ms=" << millisecondsFromNanoseconds(overlayStageNanoseconds)
                << " sprite_warmup_ms=" << millisecondsFromNanoseconds(spriteWarmupStageNanoseconds)
                << " matrix_ms=" << millisecondsFromNanoseconds(matrixStageNanoseconds)
                << " fx_ms=" << millisecondsFromNanoseconds(fxStageNanoseconds)
                << " world_render_ms=" << millisecondsFromNanoseconds(worldRenderStageNanoseconds)
                << " audio_ms=" << millisecondsFromNanoseconds(audioStageNanoseconds)
                << " camera_input=" << (cameraMotionInput ? 1 : 0)
                << " sprite_warmup_processed=" << (processSpriteWarmupsThisFrame ? 1 : 0)
                << " pending_warmups_before=" << pendingSpriteWarmupsBefore
                << " pending_warmups_after=" << pendingSpriteWarmupsAfter
                << " pending_actor_texture_uploads_before=" << pendingActorTextureUploadsBefore
                << " pending_actor_texture_uploads_after=" << pendingActorTextureUploadsAfter
                << '\n';
        }
    }

}

bool OutdoorGameView::executeEventHooks(EventRuntimeHookKind kind)
{
    return m_pOutdoorSceneRuntime != nullptr
        && m_pOutdoorSceneRuntime->executeEventHooks(kind);
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
        resetLightingStats(m_outdoorLightingStats);
        m_outdoorSpriteRenderDiagnostics = {};
        m_lastOutdoorLightingStatsLogElapsedTime = 0.0f;
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
        m_terrainTextureAtlasMipPixels.clear();
        m_terrainTextureAtlasWidth = 0;
        m_terrainTextureAtlasHeight = 0;
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
        m_outdoorFaceAlphaParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewParams0UniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewParams1UniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewColorAUniformHandle = BGFX_INVALID_HANDLE;
        m_spellAreaPreviewColorBUniformHandle = BGFX_INVALID_HANDLE;
        m_indexBufferHandle = BGFX_INVALID_HANDLE;
        m_filledTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_skyVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_texturedTerrainChunks.clear();
        m_bmodelVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bmodelCollisionVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_vertexBufferHandle = BGFX_INVALID_HANDLE;

        m_bmodelTextureAnimations.clear();
        m_resolvedBModelDrawGroups.clear();
        m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
        m_arpgModeResolvedBModelDrawGroups.clear();
        m_arpgModeResolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
        m_arpgModeResolvedBModelOcclusionHash = 0;

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
    m_terrainTextureAtlasMipPixels.clear();
    m_terrainTextureAtlasWidth = 0;
    m_terrainTextureAtlasHeight = 0;

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

    if (bgfx::isValid(m_outdoorFaceAlphaParamsUniformHandle))
    {
        bgfx::destroy(m_outdoorFaceAlphaParamsUniformHandle);
        m_outdoorFaceAlphaParamsUniformHandle = BGFX_INVALID_HANDLE;
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
    for (ResolvedBModelDrawGroup &group : m_arpgModeResolvedBModelDrawGroups)
    {
        if (bgfx::isValid(group.vertexBufferHandle))
        {
            bgfx::destroy(group.vertexBufferHandle);
            group.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        group.vertexCount = 0;
        group.animationIndex = static_cast<size_t>(-1);
    }
    m_arpgModeResolvedBModelDrawGroups.clear();
    m_arpgModeResolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
    m_arpgModeResolvedBModelOcclusionHash = 0;
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

    for (TexturedTerrainChunk &chunk : m_texturedTerrainChunks)
    {
        if (bgfx::isValid(chunk.vertexBufferHandle))
        {
            bgfx::destroy(chunk.vertexBufferHandle);
            chunk.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_texturedTerrainChunks.clear();

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
    resetLightingStats(m_outdoorLightingStats);
    m_outdoorSpriteRenderDiagnostics = {};
    m_lastOutdoorLightingStatsLogElapsedTime = 0.0f;
    m_cachedSkyVertices.clear();
    m_cachedSkyTextureName.clear();
    m_lastSkyUpdateElapsedTime = -1.0f;
    m_bmodelLineVertexCount = 0;
    m_bmodelCollisionVertexCount = 0;
    m_bmodelFaceCount = 0;
    m_entityMarkerVertexCount = 0;
    m_spawnMarkerVertexCount = 0;
    worldInteractionInputState.keyboardUseLatch = false;
    worldInteractionInputState.inspectKeyboardActivateLatch = false;
    worldInteractionInputState.keyboardUseNextRepeatTickNanoseconds = 0;
    worldInteractionInputState.inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
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

bool OutdoorGameView::arpgModeEnabled() const
{
    return m_gameSettings.arpgModeEnabled
        && !arpgModeFirstPersonUseMode()
        && m_pOutdoorPartyRuntime != nullptr;
}

bool OutdoorGameView::arpgModeFirstPersonUseMode() const
{
    return m_gameSession.gameplayScreenState().arpgModeFirstPersonUseMode();
}

ArpgModeCameraFrame OutdoorGameView::buildCameraFrame(
    uint16_t viewWidth,
    uint16_t viewHeight,
    float farClipDistance) const
{
    const float aspectRatio =
        static_cast<float>(std::max<uint16_t>(viewWidth, 1))
        / static_cast<float>(std::max<uint16_t>(viewHeight, 1));
    const bool homogeneousDepth = bgfx::getCaps()->homogeneousDepth;

    if (arpgModeEnabled())
    {
        return buildArpgModeCameraFrame(
            ArpgModeCameraInput{
                .target = {m_cameraTargetX, m_cameraTargetY, m_cameraTargetZ},
                .yawRadians = degreesToRadians(m_gameSettings.arpgModeCameraYawDegrees),
                .pitchRadians = degreesToRadians(m_gameSettings.arpgModeCameraPitchDegrees),
                .distance = m_gameSettings.arpgModeCameraDistance,
                .fovDegrees = m_gameSettings.arpgModeCameraFovDegrees,
                .aspectRatio = aspectRatio,
                .nearClip = 0.1f,
                .farClip = farClipDistance,
                .homogeneousDepth = homogeneousDepth,
            });
    }

    const float cameraYawRadians = effectiveCameraYawRadians();
    const float cameraPitchRadians = effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const bx::Vec3 eye = {m_cameraTargetX, m_cameraTargetY, m_cameraTargetZ};
    const bx::Vec3 at = {
        m_cameraTargetX + std::cos(cameraYawRadians) * cosPitch,
        m_cameraTargetY + std::sin(cameraYawRadians) * cosPitch,
        m_cameraTargetZ + std::sin(cameraPitchRadians),
    };
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};

    ArpgModeCameraFrame frame = {};
    frame.eye = eye;
    frame.at = at;
    frame.forward = vecNormalize(vecSubtract(at, eye));
    frame.right = vecNormalize(bx::cross(frame.forward, worldUp));
    frame.up = vecNormalize(bx::cross(frame.right, frame.forward));
    bx::mtxLookAt(frame.viewMatrix.data(), frame.eye, frame.at, worldUp, bx::Handedness::Right);
    bx::mtxProj(
        frame.projectionMatrix.data(),
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        farClipDistance,
        homogeneousDepth,
        bx::Handedness::Right);
    return frame;
}

void OutdoorGameView::syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled)
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

void OutdoorGameView::syncCursorToGameplayCrosshair(SDL_Window *pWindow)
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

void OutdoorGameView::playArpgModePartyActionAnimation(float animationSeconds, bool spellCast)
{
    if (!arpgModeEnabled())
    {
        return;
    }

    const float minimumDurationSeconds = 0.05f;
    const float durationSeconds = std::max(animationSeconds, minimumDurationSeconds);
    m_arpgModeActionAnimationSeconds = durationSeconds;
    m_arpgModeActionAnimationDurationSeconds = durationSeconds;
    m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    m_arpgModeActionAnimationIsCast = spellCast;
}

void OutdoorGameView::faceArpgModeTargetPoint(float targetX, float targetY)
{
    if (!arpgModeEnabled() || m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
    const float deltaX = targetX - moveState.x;
    const float deltaY = targetY - moveState.y;

    if (deltaX * deltaX + deltaY * deltaY <= 0.000001f)
    {
        return;
    }

    const float yawRadians = std::atan2(deltaY, deltaX);
    setCameraAngles(yawRadians, cameraPitchRadians());
    m_arpgModeMinimapArrowYawRadians = yawRadians;
}

void OutdoorGameView::updateArpgModeDelayedSpell(float deltaSeconds)
{
    if (!m_arpgModeDelayedSpellActive)
    {
        return;
    }

    m_arpgModeDelayedSpellReleaseSeconds =
        std::max(0.0f, m_arpgModeDelayedSpellReleaseSeconds - std::max(0.0f, deltaSeconds));

    if (m_arpgModeDelayedSpellReleaseSeconds > 0.0f)
    {
        return;
    }

    PartySpellCastRequest request = m_arpgModeDelayedSpellRequest;
    const std::string spellName = m_arpgModeDelayedSpellName;
    m_arpgModeDelayedSpellActive = false;
    m_arpgModeDelayedSpellRequest = {};
    m_arpgModeDelayedSpellName.clear();
    m_arpgModeReleasingDelayedSpell = true;
    tryCastSpellRequest(request, spellName);
    m_arpgModeReleasingDelayedSpell = false;
}

void OutdoorGameView::updateArpgModeLootAutoPickup(float deltaSeconds)
{
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

    if (!arpgModeEnabled() || m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const std::vector<OutdoorWorldRuntime::ArpgModeGoldPickup> pickups =
        m_pOutdoorWorldRuntime->collectNearbyArpgModeCorpseGold(220.0f);
    uint32_t totalGold = 0;

    for (const OutdoorWorldRuntime::ArpgModeGoldPickup &pickup : pickups)
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

void OutdoorGameView::renderArpgModeLootOverlay(
    int width,
    int height,
    const ArpgModeCameraFrame &cameraFrame,
    float)
{
    m_arpgModeLootLabelHits.clear();

    if (!arpgModeEnabled() || m_pOutdoorWorldRuntime == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    GameplayScreenRuntime &screenRuntime = m_gameSession.gameplayScreenRuntime();
    screenRuntime.prepareHudView(width, height);

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, cameraFrame.viewMatrix.data(), cameraFrame.projectionMatrix.data());

    const std::vector<OutdoorWorldRuntime::ArpgModeCorpseLootItem> lootItems =
        m_pOutdoorWorldRuntime->collectArpgModeCorpseLootItems();
    constexpr const char *FontName = "Create";
    constexpr float FontScale = 1.0f;
    constexpr float PaddingX = 7.0f;
    constexpr float PaddingY = 3.0f;
    constexpr float Border = 2.0f;
    const float fontHeight = static_cast<float>(std::max(12, screenRuntime.hudFontHeight(FontName)));
    const float labelHeight = std::max(18.0f, fontHeight * FontScale + PaddingY * 2.0f);
    const float lineGap = 4.0f;

    for (const OutdoorWorldRuntime::ArpgModeCorpseLootItem &lootItem : lootItems)
    {
        ProjectedPoint projected = {};

        if (!projectWorldPointToScreen(
                bx::Vec3{lootItem.x, lootItem.y, lootItem.z},
                width,
                height,
                viewProjectionMatrix,
                projected))
        {
            continue;
        }

        if (projected.x < 0.0f
            || projected.x > static_cast<float>(width)
            || projected.y < 0.0f
            || projected.y > static_cast<float>(height))
        {
            continue;
        }

        const std::string baseLabel =
            arpgModeCorpseLootLabel(
                lootItem.item,
                data().itemTable(),
                &data().standardItemEnchantTable(),
                &data().specialItemEnchantTable());
        const ArpgModeLootFacts facts = arpgModeCorpseLootFacts(lootItem.item, data().itemTable());
        const ArpgModeLootImportance importance = classifyArpgModeLoot(facts);
        const ArpgModeLootStyle style = arpgModeLootStyle(importance, lootItem.item.isGold);
        const std::string label = style.showStar ? "* " + baseLabel : baseLabel;
        const float measuredWidth = screenRuntime.measureHudTextWidth(FontName, label) * FontScale;
        const float labelWidth = std::clamp(measuredWidth + PaddingX * 2.0f, 76.0f, 340.0f);
        float labelX = projected.x - labelWidth * 0.5f;
        float labelY =
            projected.y
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
            const float beamTop = std::min(labelY + labelHeight, projected.y - 2.0f);
            const float beamHeight = std::max(18.0f, projected.y - beamTop);
            drawArpgModeSolidHudRect(
                screenRuntime,
                "__arpg_loot_beam__",
                projected.x - 1.5f,
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
            });
    }

    for (const ArpgModeLootFloatingText &floatingText : m_arpgModeLootFloatingTexts)
    {
        if (floatingText.remainingSeconds <= 0.0f || floatingText.durationSeconds <= 0.0f)
        {
            continue;
        }

        const float progress =
            1.0f - std::clamp(floatingText.remainingSeconds / floatingText.durationSeconds, 0.0f, 1.0f);
        ProjectedPoint projected = {};

        if (!projectWorldPointToScreen(
                bx::Vec3{floatingText.x, floatingText.y, floatingText.z + progress * 96.0f},
                width,
                height,
                viewProjectionMatrix,
                projected))
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
            projected.x - textWidth * 0.5f,
            projected.y,
            FontScale);
    }
}

bool OutdoorGameView::tryActivateArpgModeLootLabelAt(float screenX, float screenY)
{
    if (!arpgModeEnabled() || m_pOutdoorWorldRuntime == nullptr || m_pOutdoorPartyRuntime == nullptr)
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

bool OutdoorGameView::tryActivateArpgModeCorpseLootItem(size_t actorIndex, size_t itemIndex)
{
    if (!arpgModeEnabled() || m_pOutdoorWorldRuntime == nullptr || m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    const std::optional<GameplayChestItemState> selectedItem =
        m_pOutdoorWorldRuntime->mapActorCorpseItem(actorIndex, itemIndex);

    if (!selectedItem)
    {
        return false;
    }

    if (selectedItem->isGold)
    {
        GameplayChestItemState removedItem = {};

        if (!m_pOutdoorWorldRuntime->takeMapActorCorpseItem(actorIndex, itemIndex, removedItem))
        {
            return true;
        }

        const EventRuntimeState *pEventRuntimeState = m_pOutdoorWorldRuntime->eventRuntimeState();
        const uint32_t adjustedGold =
            pEventRuntimeState != nullptr
                ? hiredNpcGoldAfterBonusAndFees(removedItem.goldAmount, *pEventRuntimeState)
                : removedItem.goldAmount;
        m_pOutdoorPartyRuntime->party().addGold(static_cast<int>(adjustedGold));
        m_pOutdoorPartyRuntime->party().requestSound(SoundId::Gold);
        setStatusBarEvent("+" + std::to_string(adjustedGold) + " gold");
        m_arpgModeLootFloatingTexts.push_back(
            ArpgModeLootFloatingText{
                .text = "+" + std::to_string(adjustedGold) + " gold",
                .x = m_pOutdoorPartyRuntime->movementState().x,
                .y = m_pOutdoorPartyRuntime->movementState().y,
                .z = m_pOutdoorPartyRuntime->movementState().footZ + 96.0f,
                .remainingSeconds = 1.35f,
                .durationSeconds = 1.35f,
            });
        return true;
    }

    GameplayChestItemState removedItem = {};

    if (!m_pOutdoorWorldRuntime->takeMapActorCorpseItem(actorIndex, itemIndex, removedItem))
    {
        return true;
    }

    InventoryItem inventoryItem = normalizedArpgModeCorpseInventoryItem(removedItem);
    const ItemDefinition *pItemDefinition = data().itemTable().get(inventoryItem.objectDescriptionId);
    const std::string itemName =
        pItemDefinition != nullptr
            ? ItemRuntime::displayName(
                inventoryItem,
                *pItemDefinition,
                &data().standardItemEnchantTable(),
                &data().specialItemEnchantTable())
            : "item";

    if (!m_pOutdoorPartyRuntime->party().tryGrantInventoryItemStartingAt(
            m_pOutdoorPartyRuntime->party().activeMemberIndex(),
            inventoryItem))
    {
        m_pOutdoorWorldRuntime->tryPlaceMapActorCorpseItemAt(actorIndex, removedItem, itemIndex);
        setStatusBarEvent("Pack is Full!");
        return true;
    }

    m_pOutdoorPartyRuntime->party().requestSound(SoundId::Gold);
    setStatusBarEvent("+" + itemName);
    m_arpgModeLootFloatingTexts.push_back(
        ArpgModeLootFloatingText{
            .text = "+" + itemName,
            .x = m_pOutdoorPartyRuntime->movementState().x,
            .y = m_pOutdoorPartyRuntime->movementState().y,
            .z = m_pOutdoorPartyRuntime->movementState().footZ + 96.0f,
            .remainingSeconds = 1.55f,
            .durationSeconds = 1.55f,
        });
    return true;
}

bool OutdoorGameView::tryActivateFirstArpgModeCorpseLootItem(size_t actorIndex)
{
    if (m_pOutdoorWorldRuntime == nullptr || !m_pOutdoorWorldRuntime->ensureMapActorCorpseView(actorIndex))
    {
        return false;
    }

    return tryActivateArpgModeCorpseLootItem(actorIndex, 0);
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
                    worldSound(*greetingSoundId),
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

    const GameplayWorldPickRequest pickRequest =
        m_pOutdoorWorldRuntime->buildWorldPickRequest(
            GameplayWorldPickRequestInput{
                .screenX = input.pointerX,
                .screenY = input.pointerY,
                .screenWidth = width,
                .screenHeight = height,
                .includeRay = true,
            });
    const GameplayWorldHit worldHit = m_pOutdoorWorldRuntime->pickMouseInteractionTarget(pickRequest);

    if (worldHit.kind == GameplayWorldHitKind::WorldItem && worldHit.worldItem)
    {
        const OutdoorWorldRuntime::WorldItemState *pWorldItem =
            m_pOutdoorWorldRuntime->worldItemState(worldHit.worldItem->worldItemIndex);

        if (pWorldItem != nullptr)
        {
            itemInspectOverlay.active = true;
            itemInspectOverlay.objectDescriptionId = pWorldItem->item.objectDescriptionId;
            itemInspectOverlay.hasItemState = !pWorldItem->isGold;
            itemInspectOverlay.itemState = pWorldItem->item;
            itemInspectOverlay.sourceType = ItemInspectSourceType::WorldItem;
            itemInspectOverlay.sourceWorldItemIndex = worldHit.worldItem->worldItemIndex;
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

bool OutdoorGameView::requestTravelAutosave()
{
    return beginSaveWithPreview(m_autosavePath, "", false);
}

bool OutdoorGameView::beginSaveWithPreview(
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
    worldInteractionInputState.keyboardUseNextRepeatTickNanoseconds = 0;
    worldInteractionInputState.inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
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
    screenRuntime.clearStatusBarHoverText();
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

    if (arpgModeEnabled() && !m_arpgModeReleasingDelayedSpell)
    {
        if (m_arpgModeDelayedSpellActive)
        {
            return true;
        }

        m_arpgModeDelayedSpellActive = true;
        m_arpgModeDelayedSpellRequest = resolvedRequest;
        m_arpgModeDelayedSpellName = spellName;
        m_arpgModeDelayedSpellReleaseSeconds = std::clamp(m_gameSettings.arpgModeSpellReleaseSeconds, 0.0f, 10.0f);
        m_pOutdoorWorldRuntime->faceArpgModePartyActionTarget(resolvedRequest);
        playArpgModePartyActionAnimation(
            std::clamp(m_gameSettings.arpgModeSpellAnimationSeconds, 0.05f, 10.0f),
            true);
        return true;
    }

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
    refreshViewDistanceCache();

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        Party &party = m_pOutdoorPartyRuntime->party();
        party.setDebugDamageImmune(settings.immortal);
        party.setDebugUnlimitedMana(settings.unlimitedMana);
    }
}

void OutdoorGameView::refreshViewDistanceCache()
{
    if (m_viewDistanceCache.sourceValue == m_gameSettings.viewDistance)
    {
        return;
    }

    m_viewDistanceCache.sourceValue = m_gameSettings.viewDistance;
    m_viewDistanceCache.farClipDistance =
        resolveViewDistanceSetting(m_gameSettings.viewDistance, DefaultOutdoorFarClip);
    m_viewDistanceCache.runtimeProjectileDistance =
        resolveViewDistanceSetting(m_gameSettings.viewDistance, RuntimeProjectileRenderDistance);
    m_viewDistanceCache.runtimeProjectileDistanceSquared =
        m_viewDistanceCache.runtimeProjectileDistance * m_viewDistanceCache.runtimeProjectileDistance;
    m_viewDistanceCache.decorationBillboardDistance =
        resolveViewDistanceSetting(m_gameSettings.viewDistance, DecorationBillboardRenderDistance);
    m_viewDistanceCache.decorationBillboardDistanceSquared =
        m_viewDistanceCache.decorationBillboardDistance * m_viewDistanceCache.decorationBillboardDistance;
    m_viewDistanceCache.actorBillboardDistance =
        resolveViewDistanceSetting(m_gameSettings.viewDistance, ActorBillboardRenderDistance);
    m_viewDistanceCache.actorBillboardDistanceSquared =
        m_viewDistanceCache.actorBillboardDistance * m_viewDistanceCache.actorBillboardDistance;
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

float OutdoorGameView::gameplayMinimapArrowYawRadians() const
{
    return arpgModeEnabled() ? m_arpgModeMinimapArrowYawRadians : effectiveCameraYawRadians();
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

    if (arpgModeEnabled())
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

    if (!input.rightMouseButton.held)
    {
        return;
    }

    const GameplayWorldPickRequest pickRequest =
        m_pOutdoorWorldRuntime->buildWorldPickRequest(
            GameplayWorldPickRequestInput{
                .screenX = input.pointerX,
                .screenY = input.pointerY,
                .screenWidth = width,
                .screenHeight = height,
                .includeRay = true,
            });
    const GameplayWorldHit worldHit = m_pOutdoorWorldRuntime->pickMouseInteractionTarget(pickRequest);

    if (worldHit.kind != GameplayWorldHitKind::Actor || !worldHit.actor)
    {
        return;
    }

    const size_t runtimeActorIndex = worldHit.actor->actorIndex;

    if (runtimeActorIndex == GameplayInvalidWorldIndex)
    {
        return;
    }

    const OutdoorWorldRuntime::MapActorState *pActorState = m_pOutdoorWorldRuntime->mapActorState(runtimeActorIndex);

    if (pActorState == nullptr)
    {
        return;
    }

    const GameplayActorTargetHit &actorHit = *worldHit.actor;
    OutdoorGameView::InspectHit inspectHit = {};
    inspectHit.hasHit = true;
    inspectHit.kind = "actor";
    inspectHit.name = actorHit.displayName;
    inspectHit.isFriendly = actorHit.isFriendly;
    inspectHit.npcId = actorHit.npcId;
    inspectHit.actorGroup = actorHit.actorGroup;
    inspectHit.distance = actorHit.distance;
    inspectHit.runtimeActorIndex = runtimeActorIndex;
    inspectHit.bModelIndex = runtimeActorIndex;
    inspectHit.hitX = actorHit.hitPoint.x;
    inspectHit.hitY = actorHit.hitPoint.y;
    inspectHit.hitZ = actorHit.hitPoint.z;

    if (input.rightMouseButton.pressed)
    {
        GameplayActorInspectState inspectState = {};
        Party *pParty = m_gameSession.gameplayScreenRuntime().party();
        const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;

        if (m_pOutdoorWorldRuntime->actorInspectState(runtimeActorIndex, 0, inspectState))
        {
            const OutdoorMoveState *pMoveState =
                m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->movementState() : nullptr;
            GAMEPLAY_DEBUG_TRACE(
                "actor_inspect world=outdoor map=\"" + m_pOutdoorWorldRuntime->mapName() + "\""
                + " actor_index=" + std::to_string(runtimeActorIndex)
                + " name=\"" + inspectState.displayName + "\""
                + " monster_id=" + std::to_string(inspectState.monsterId)
                + " current_hp=" + std::to_string(inspectState.currentHp)
                + " max_hp=" + std::to_string(inspectState.maxHp)
                + " group=" + std::to_string(pActorState->group)
                + " dead=" + (inspectState.isDead ? "true" : "false")
                + (pMoveState != nullptr
                    ? " party=(" + std::to_string(pMoveState->x)
                        + "," + std::to_string(pMoveState->y)
                        + "," + std::to_string(pMoveState->footZ) + ")"
                    : "")
                + " yaw=" + std::to_string(m_cameraYawRadians)
                + " pitch=" + std::to_string(m_cameraPitchRadians)
                + " actor_pos=(" + std::to_string(pActorState->preciseX)
                + "," + std::to_string(pActorState->preciseY)
                + "," + std::to_string(pActorState->preciseZ) + ")");

            if (!pActorState->isDead)
            {
                const MonsterTable::MonsterStatsEntry *pStats =
                    m_gameSession.data().monsterTable().findStatsById(inspectState.monsterId);

                const std::optional<size_t> speakerMemberIndex =
                    pParty != nullptr ? pParty->bestPartyWideUtilitySkillMemberIndex("IdentifyMonster") : std::nullopt;
                const Character *pIdentifier = speakerMemberIndex ? pParty->member(*speakerMemberIndex) : nullptr;

                if (pParty != nullptr && pIdentifier != nullptr && pStats != nullptr)
                {
                    const SpeechId speechId = GameMechanics::resolveIdentifyMonsterSpeech(*pIdentifier, pStats->level);

                    if (speechId != SpeechId::None)
                    {
                        m_gameSession.gameplayScreenRuntime().playSpeechReaction(
                            *speakerMemberIndex,
                            speechId,
                            true);
                    }
                }
            }
        }
    }

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, pickRequest.viewMatrix.data(), pickRequest.projectionMatrix.data());

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
    actorInspectOverlay.runtimeActorIndex = runtimeActorIndex;
    actorInspectOverlay.displayNameOverride =
        OutdoorInteractionController::resolveActorInspectDisplayName(*this, inspectHit);
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

    const std::string worldId = m_map.has_value() ? m_map->worldId : std::string();
    const std::string cacheKey = actPaletteCacheKey(paletteId, worldId);
    const auto cachedPaletteIt = m_spriteLoadCache.actPalettesByKey.find(cacheKey);

    if (cachedPaletteIt != m_spriteLoadCache.actPalettesByKey.end())
    {
        return cachedPaletteIt->second;
    }

    for (const std::string &palettePath : actPaletteCandidatePaths(paletteId, worldId))
    {
        const std::optional<std::vector<uint8_t>> paletteBytes = readCachedBinaryFile(palettePath);

        if (!paletteBytes || paletteBytes->size() < 256 * 3)
        {
            continue;
        }

        std::array<uint8_t, 256 * 3> palette = {};
        std::memcpy(palette.data(), paletteBytes->data(), palette.size());
        m_spriteLoadCache.actPalettesByKey[cacheKey] = palette;
        return palette;
    }

    m_spriteLoadCache.actPalettesByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::vector<uint8_t>> OutdoorGameView::loadSpriteBitmapPixelsBgraCached(
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    const std::optional<std::string> spritePath =
        Engine::findImageAssetPath(
            *m_pAssetFileSystem,
            "Data/sprites",
            textureName,
            m_spriteLoadCache.directoryAssetPathsByPath,
            m_spriteLoadCache.assetPathByKey);

    if (!spritePath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = readCachedBinaryFile(*spritePath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    return loadSpriteBitmapPixelsBgra(*bitmapBytes, *spritePath, loadCachedActPalette(paletteId), width, height);
}

}
