#include "game/OutdoorGameView.h"

#include "game/GenericActorDialog.h"
#include "game/HouseInteraction.h"
#include "game/ItemTable.h"
#include "game/MasteryTeacherDialog.h"
#include "game/OutdoorGeometryUtils.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/SpawnPreview.h"
#include "game/SpriteTables.h"
#include "game/StringUtils.h"

#include <bx/math.h>

#include <bgfx/bgfx.h>
#include <SDL3/SDL.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
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
constexpr uint16_t MainViewId = 0;
constexpr uint16_t HudViewId = 1;
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

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

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

DialogueMenuId dialogueMenuIdForHouseAction(HouseActionId actionId)
{
    switch (actionId)
    {
        case HouseActionId::OpenLearnSkillsMenu:
            return DialogueMenuId::LearnSkills;

        case HouseActionId::OpenShopEquipmentMenu:
            return DialogueMenuId::ShopEquipment;

        case HouseActionId::OpenTavernArcomageMenu:
            return DialogueMenuId::TavernArcomage;

        default:
            return DialogueMenuId::None;
    }
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
constexpr uint32_t AdventurersInnHouseId = 185;
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

std::vector<OutdoorActorCollision> buildRuntimeActorColliders(const OutdoorWorldRuntime &worldRuntime)
{
    std::vector<OutdoorActorCollision> colliders;
    colliders.reserve(worldRuntime.mapActorCount());

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = worldRuntime.mapActorState(actorIndex);

        if (pActor == nullptr
            || pActor->isDead
            || pActor->currentHp <= 0
            || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Dying
            || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Dead
            || pActor->isInvisible
            || !pActor->hostileToParty
            || pActor->radius == 0
            || pActor->height == 0)
        {
            continue;
        }

        OutdoorActorCollision collider = {};
        collider.sourceIndex = actorIndex;
        collider.source = OutdoorActorCollisionSource::MapDelta;
        collider.radius = pActor->radius;
        collider.height = pActor->height;
        collider.worldX = pActor->x;
        collider.worldY = pActor->y;
        collider.worldZ = pActor->z;
        collider.group = pActor->group;
        collider.name = pActor->displayName;
        colliders.push_back(std::move(collider));
    }

    return colliders;
}

void notifyFriendlyActorContacts(
    OutdoorWorldRuntime &worldRuntime,
    const OutdoorMoveState &partyMoveState,
    const OutdoorMovementEvents &movementEvents)
{
    for (size_t actorIndex : movementEvents.contactedActorIndices)
    {
        worldRuntime.notifyPartyContactWithMapActor(actorIndex, partyMoveState.x, partyMoveState.y, partyMoveState.footZ);
    }
}

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
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

std::vector<uint32_t> collectSelectableResidentNpcIds(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
{
    std::vector<uint32_t> residentNpcIds;

    auto appendNpcId = [&](uint32_t npcId)
    {
        if (std::find(residentNpcIds.begin(), residentNpcIds.end(), npcId) != residentNpcIds.end())
        {
            return;
        }

        const NpcEntry *pResident = npcDialogTable.getNpc(npcId);

        if (pResident == nullptr || pResident->name.empty())
        {
            return;
        }

        if (eventRuntimeState.unavailableNpcIds.contains(npcId))
        {
            return;
        }

        const auto overrideIt = eventRuntimeState.npcHouseOverrides.find(npcId);

        if (overrideIt != eventRuntimeState.npcHouseOverrides.end() && overrideIt->second != houseEntry.id)
        {
            return;
        }

        residentNpcIds.push_back(npcId);
    };

    for (uint32_t npcId : houseEntry.residentNpcIds)
    {
        appendNpcId(npcId);
    }

    for (uint32_t npcId : npcDialogTable.getNpcIdsForHouse(houseEntry.id, &eventRuntimeState.npcHouseOverrides))
    {
        appendNpcId(npcId);
    }

    return residentNpcIds;
}

std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
{
    const std::vector<uint32_t> residentNpcIds =
        collectSelectableResidentNpcIds(houseEntry, npcDialogTable, eventRuntimeState);

    if (residentNpcIds.size() != 1)
    {
        return std::nullopt;
    }

    return residentNpcIds.front();
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
    , m_activateInspectLatch(false)
    , m_inspectMouseActivateLatch(false)
    , m_attackInspectLatch(false)
    , m_toggleRunningLatch(false)
    , m_toggleFlyingLatch(false)
    , m_toggleWaterWalkLatch(false)
    , m_toggleFeatherFallLatch(false)
    , m_closeOverlayLatch(false)
    , m_dialogueClickLatch(false)
    , m_dialoguePressedTargetType(DialoguePointerTargetType::None)
    , m_dialoguePressedTargetIndex(0)
    , m_lootChestItemLatch(false)
    , m_chestSelectUpLatch(false)
    , m_chestSelectDownLatch(false)
    , m_eventDialogSelectUpLatch(false)
    , m_eventDialogSelectDownLatch(false)
    , m_eventDialogAcceptLatch(false)
    , m_eventDialogPartySelectLatches({})
    , m_chestSelectionIndex(0)
    , m_eventDialogSelectionIndex(0)
    , m_statusBarEventText()
    , m_statusBarEventRemainingSeconds(0.0f)
    , m_activeEventDialog({})
    , m_pOutdoorPartyRuntime(nullptr)
    , m_pAssetFileSystem(nullptr)
    , m_pOutdoorWorldRuntime(nullptr)
    , m_pItemTable(nullptr)
    , m_pRosterTable(nullptr)
    , m_pObjectTable(nullptr)
    , m_pSpellTable(nullptr)
    , m_nextPendingSpriteFrameWarmupIndex(0)
    , m_runtimeActorBillboardTexturesQueuedCount(0)
{
    m_eventDialogPartySelectLatches.fill(false);
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
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    const std::optional<StrTable> &localStrTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram,
    const std::optional<EventIrProgram> &localEventIrProgram,
    const std::optional<EventIrProgram> &globalEventIrProgram,
    OutdoorPartyRuntime *pOutdoorPartyRuntime,
    OutdoorWorldRuntime *pOutdoorWorldRuntime
)
{
    shutdown();

    m_isInitialized = true;
    m_pAssetFileSystem = &assetFileSystem;
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
    m_pRosterTable = &rosterTable;
    m_pObjectTable = &objectTable;
    m_pSpellTable = &spellTable;
    m_pItemTable = &itemTable;
    m_localStrTable = localStrTable;
    m_localEvtProgram = localEvtProgram;
    m_globalEvtProgram = globalEvtProgram;
    m_localEventIrProgram = localEventIrProgram;
    m_globalEventIrProgram = globalEventIrProgram;
    m_pOutdoorPartyRuntime = pOutdoorPartyRuntime;
    m_pOutdoorWorldRuntime = pOutdoorWorldRuntime;
    buildDecorationBillboardSpatialIndex();

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
        m_pOutdoorPartyRuntime->initialize(m_cameraTargetX, m_cameraTargetY, initialFootZ);
        m_cameraTargetZ = m_pOutdoorPartyRuntime->movementState().footZ + m_cameraEyeHeight;
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

    TerrainVertex::init();
    TexturedTerrainVertex::init();

    const std::vector<TerrainVertex> vertices = buildVertices(outdoorMapData);
    const std::vector<uint16_t> indices = buildIndices();
    std::vector<TexturedTerrainVertex> texturedTerrainVertices;
    const std::vector<TerrainVertex> filledTerrainVertices = buildFilledTerrainVertices(outdoorMapData, outdoorTileColors);
    const std::vector<TerrainVertex> bmodelVertices = buildBModelWireframeVertices(outdoorMapData);
    const std::vector<TerrainVertex> bmodelCollisionVertices = buildBModelCollisionFaceVertices(outdoorMapData);
    const std::vector<TerrainVertex> entityMarkerVertices = buildEntityMarkerVertices(outdoorMapData);
    const std::vector<TerrainVertex> spawnMarkerVertices = buildSpawnMarkerVertices(outdoorMapData);

    if (outdoorTerrainTextureAtlas)
    {
        texturedTerrainVertices = buildTexturedTerrainVertices(outdoorMapData, *outdoorTerrainTextureAtlas);
    }

    if (vertices.empty() || indices.empty())
    {
        std::cerr << "OutdoorGameView received empty terrain mesh.\n";
        return false;
    }

    m_vertexBufferHandle = bgfx::createVertexBuffer(
        bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TerrainVertex))),
        TerrainVertex::ms_layout
    );

    m_indexBufferHandle = bgfx::createIndexBuffer(
        bgfx::copy(indices.data(), static_cast<uint32_t>(indices.size() * sizeof(uint16_t)))
    );

    if (!texturedTerrainVertices.empty())
    {
        m_texturedTerrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                texturedTerrainVertices.data(),
                static_cast<uint32_t>(texturedTerrainVertices.size() * sizeof(TexturedTerrainVertex))
            ),
            TexturedTerrainVertex::ms_layout
        );
    }

    if (!filledTerrainVertices.empty())
    {
        m_filledTerrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                filledTerrainVertices.data(),
                static_cast<uint32_t>(filledTerrainVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
    }

    if (!bmodelVertices.empty())
    {
        m_bmodelVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(bmodelVertices.data(), static_cast<uint32_t>(bmodelVertices.size() * sizeof(TerrainVertex))),
            TerrainVertex::ms_layout
        );
        m_bmodelLineVertexCount = static_cast<uint32_t>(bmodelVertices.size());
    }

    if (!bmodelCollisionVertices.empty())
    {
        m_bmodelCollisionVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelCollisionVertices.data(),
                static_cast<uint32_t>(bmodelCollisionVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
        m_bmodelCollisionVertexCount = static_cast<uint32_t>(bmodelCollisionVertices.size());
    }

    if (!entityMarkerVertices.empty())
    {
        m_entityMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                entityMarkerVertices.data(),
                static_cast<uint32_t>(entityMarkerVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
        m_entityMarkerVertexCount = static_cast<uint32_t>(entityMarkerVertices.size());
    }

    if (!spawnMarkerVertices.empty())
    {
        m_spawnMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                spawnMarkerVertices.data(),
                static_cast<uint32_t>(spawnMarkerVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
        m_spawnMarkerVertexCount = static_cast<uint32_t>(spawnMarkerVertices.size());
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        m_bmodelFaceCount += static_cast<uint32_t>(bmodel.faces.size());
    }

    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedTerrainProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");

    if (outdoorTerrainTextureAtlas && !outdoorTerrainTextureAtlas->pixels.empty())
    {
        m_terrainTextureAtlasHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->width),
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            bgfx::copy(
                outdoorTerrainTextureAtlas->pixels.data(),
                static_cast<uint32_t>(outdoorTerrainTextureAtlas->pixels.size())
            )
        );
    }

    if (outdoorBModelTextureSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorBModelTextureSet->textures)
        {
            const std::vector<TexturedTerrainVertex> texturedBModelVertices =
                buildTexturedBModelVertices(outdoorMapData, texture);

            if (texturedBModelVertices.empty())
            {
                continue;
            }

            TexturedBModelBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    texturedBModelVertices.data(),
                    static_cast<uint32_t>(texturedBModelVertices.size() * sizeof(TexturedTerrainVertex))
                ),
                TexturedTerrainVertex::ms_layout
            );
            batch.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );
            batch.vertexCount = static_cast<uint32_t>(texturedBModelVertices.size());

            if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle))
            {
                if (bgfx::isValid(batch.vertexBufferHandle))
                {
                    bgfx::destroy(batch.vertexBufferHandle);
                }

                if (bgfx::isValid(batch.textureHandle))
                {
                    bgfx::destroy(batch.textureHandle);
                }

                continue;
            }

            m_texturedBModelBatches.push_back(batch);
        }
    }

    if (outdoorDecorationBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorDecorationBillboardSet->textures)
        {
            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.paletteId = texture.paletteId;
            billboardTexture.width = texture.width;
            billboardTexture.height = texture.height;
            billboardTexture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_billboardTextureHandles.push_back(std::move(billboardTexture));
                m_billboardTextureIndexByPalette[texture.paletteId][m_billboardTextureHandles.back().textureName] =
                    m_billboardTextureHandles.size() - 1;
            }
        }
    }

    if (m_localEventIrProgram)
    {
        queueEventSpellBillboardTextureWarmup(*m_localEventIrProgram);
    }

    if (m_globalEventIrProgram)
    {
        queueEventSpellBillboardTextureWarmup(*m_globalEventIrProgram);
    }

    queueRuntimeActorBillboardTextureWarmup();
    preloadPendingSpriteFrameWarmupsParallel();

    if (outdoorSpriteObjectBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorSpriteObjectBillboardSet->textures)
        {
            if (findBillboardTexture(texture.textureName, texture.paletteId) != nullptr)
            {
                continue;
            }

            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.paletteId = texture.paletteId;
            billboardTexture.width = texture.width;
            billboardTexture.height = texture.height;
            billboardTexture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_billboardTextureHandles.push_back(std::move(billboardTexture));
                m_billboardTextureIndexByPalette[texture.paletteId][m_billboardTextureHandles.back().textureName] =
                    m_billboardTextureHandles.size() - 1;
            }
        }
    }

    if (!loadHudLayout(assetFileSystem))
    {
        std::cerr << "OutdoorGameView failed to load HUD layout data from Data/ui/*.yml\n";
    }
    else
    {
            for (const auto &[id, element] : m_hudLayoutElements)
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

    m_isRenderable = true;
    return true;
}

void OutdoorGameView::render(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    if (!m_isInitialized)
    {
        return;
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

    bgfx::setViewRect(MainViewId, 0, 0, viewWidth, viewHeight);

    if (!m_isRenderable)
    {
        bgfx::touch(MainViewId);
        bgfx::dbgTextClear();
        bgfx::dbgTextPrintf(0, 1, 0x0f, "bgfx noop renderer active");
        return;
    }

    updateStatusBarEvent(deltaSeconds);

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        updateCameraFromInput(deltaSeconds);
        cameraStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    queueRuntimeActorBillboardTextureWarmup();
    processPendingSpriteFrameWarmups(1);

    const bool hasActiveLootView =
        m_pOutdoorWorldRuntime != nullptr
        && (m_pOutdoorWorldRuntime->activeChestView() != nullptr || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);
    const bool isEventDialogActive = hasActiveEventDialog();

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
        200000.0f,
        bgfx::getCaps()->homogeneousDepth
    );

    bgfx::setViewTransform(MainViewId, wireframeViewMatrix, wireframeProjectionMatrix);
    bgfx::touch(MainViewId);

    InspectHit inspectHit = {};
    float mouseX = 0.0f;
    float mouseY = 0.0f;

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();

        if (m_inspectMode && m_outdoorMapData && !hasActiveLootView && !isEventDialogActive)
        {
        SDL_GetMouseState(&mouseX, &mouseY);
        const float normalizedMouseX =
            ((static_cast<float>(mouseX) / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY =
            1.0f - ((static_cast<float>(mouseY) / static_cast<float>(viewHeight)) * 2.0f);
        float viewProjectionMatrix[16] = {};
        float inverseViewProjectionMatrix[16] = {};
        bx::mtxMul(viewProjectionMatrix, wireframeViewMatrix, wireframeProjectionMatrix);
        bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
        const bx::Vec3 rayOrigin = bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayTarget = bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
        inspectHit = inspectBModelFace(*m_outdoorMapData, rayOrigin, rayDirection);

        const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
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

        if (isActivationPressed && !m_activateInspectLatch)
        {
            if (tryActivateInspectEvent(inspectHit))
            {
                inspectHit = inspectBModelFace(*m_outdoorMapData, rayOrigin, rayDirection);
            }

            m_activateInspectLatch = true;
        }
        else if (!isActivationPressed)
        {
            m_activateInspectLatch = false;
        }

        if (isLeftMousePressed)
        {
            if (!m_inspectMouseActivateLatch)
            {
                m_pressedInspectHit = inspectHit;
                m_inspectMouseActivateLatch = true;
            }
        }
        else if (m_inspectMouseActivateLatch)
        {
            if (isSameInspectActivationTarget(m_pressedInspectHit, inspectHit))
            {
                if (tryActivateInspectEvent(inspectHit))
                {
                    inspectHit = inspectBModelFace(*m_outdoorMapData, rayOrigin, rayDirection);
                }
            }

            m_inspectMouseActivateLatch = false;
            m_pressedInspectHit = {};
        }

        if (isAttackPressed && !m_attackInspectLatch)
        {
            if (inspectHit.kind == "actor" && m_pOutdoorWorldRuntime != nullptr && m_pOutdoorPartyRuntime != nullptr)
            {
                size_t runtimeActorIndex = inspectHit.bModelIndex;

                if (m_outdoorActorPreviewBillboardSet
                    && inspectHit.bModelIndex < m_outdoorActorPreviewBillboardSet->billboards.size())
                {
                    runtimeActorIndex =
                        m_outdoorActorPreviewBillboardSet->billboards[inspectHit.bModelIndex].runtimeActorIndex;
                }

                if (runtimeActorIndex != static_cast<size_t>(-1))
                {
                    const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();

                    if (m_pOutdoorWorldRuntime->applyPartyAttackToMapActor(
                            runtimeActorIndex,
                            5,
                            moveState.x,
                            moveState.y,
                            moveState.footZ))
                    {
                        inspectHit = inspectBModelFace(*m_outdoorMapData, rayOrigin, rayDirection);

                        if (EventRuntimeState *pEventRuntimeState = m_pOutdoorWorldRuntime->eventRuntimeState())
                        {
                            pEventRuntimeState->lastActivationResult =
                                "actor " + std::to_string(runtimeActorIndex) + " hit by party";
                        }

                        std::cout << "Party attack hit actor=" << runtimeActorIndex << '\n';
                    }
                }
            }

            m_attackInspectLatch = true;
        }
        else if (!isAttackPressed)
        {
            m_attackInspectLatch = false;
        }
        }
        else
        {
            m_activateInspectLatch = false;
            m_attackInspectLatch = false;
        }

        inspectStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        bgfx::setTransform(modelMatrix);

        if (m_showFilledTerrain && bgfx::isValid(m_filledTerrainVertexBufferHandle))
        {
            bgfx::setVertexBuffer(0, m_filledTerrainVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
            );
            bgfx::submit(MainViewId, m_programHandle);
        }

        if (m_showFilledTerrain
            && bgfx::isValid(m_texturedTerrainVertexBufferHandle)
            && bgfx::isValid(m_texturedTerrainProgramHandle)
            && bgfx::isValid(m_terrainTextureAtlasHandle)
            && bgfx::isValid(m_terrainTextureSamplerHandle))
        {
            bgfx::setVertexBuffer(0, m_texturedTerrainVertexBufferHandle);
            bgfx::setTexture(0, m_terrainTextureSamplerHandle, m_terrainTextureAtlasHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(MainViewId, m_texturedTerrainProgramHandle);
        }

        if (m_showTerrainWireframe)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, m_vertexBufferHandle);
            bgfx::setIndexBuffer(m_indexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, m_programHandle);
        }

        terrainStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();

        if (m_showBModels && bgfx::isValid(m_bmodelVertexBufferHandle) && m_bmodelLineVertexCount > 0)
        {
            if (bgfx::isValid(m_texturedTerrainProgramHandle) && bgfx::isValid(m_terrainTextureSamplerHandle))
            {
                for (const TexturedBModelBatch &batch : m_texturedBModelBatches)
                {
                    if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle)
                        || batch.vertexCount == 0)
                    {
                        continue;
                    }

                    bgfx::setTransform(modelMatrix);
                    bgfx::setVertexBuffer(0, batch.vertexBufferHandle, 0, batch.vertexCount);
                    bgfx::setTexture(0, m_terrainTextureSamplerHandle, batch.textureHandle);
                    bgfx::setState(
                        BGFX_STATE_WRITE_RGB
                        | BGFX_STATE_WRITE_A
                        | BGFX_STATE_WRITE_Z
                        | BGFX_STATE_DEPTH_TEST_LEQUAL
                        | BGFX_STATE_BLEND_ALPHA
                    );
                    bgfx::submit(MainViewId, m_texturedTerrainProgramHandle);
                }
            }

            if (m_showBModelWireframe)
            {
                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(0, m_bmodelVertexBufferHandle, 0, m_bmodelLineVertexCount);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_PT_LINES
                );
                bgfx::submit(MainViewId, m_programHandle);
            }
        }

        if (m_showBModelCollisionFaces
            && bgfx::isValid(m_bmodelCollisionVertexBufferHandle)
            && m_bmodelCollisionVertexCount > 0)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, m_bmodelCollisionVertexBufferHandle, 0, m_bmodelCollisionVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(MainViewId, m_programHandle);
        }

        bmodelStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    if (m_showEntities && bgfx::isValid(m_entityMarkerVertexBufferHandle) && m_entityMarkerVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_entityMarkerVertexBufferHandle, 0, m_entityMarkerVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    if (m_showActors || m_showDecorationBillboards)
    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        renderActorPreviewBillboards(MainViewId, wireframeViewMatrix, wireframeEye);

        if (m_showActors && m_showActorCollisionBoxes)
        {
            renderActorCollisionOverlays(MainViewId, wireframeEye);
        }

        const uint64_t stageNanoseconds = SDL_GetTicksNS() - stageStartTickCount;
        actorStageNanoseconds += stageNanoseconds;

        if (m_showDecorationBillboards)
        {
            decorationStageNanoseconds += stageNanoseconds;
        }
    }

    if (m_showSpriteObjects)
    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        renderRuntimeProjectiles(MainViewId, wireframeViewMatrix, wireframeEye);
        renderSpriteObjectBillboards(MainViewId, wireframeViewMatrix, wireframeEye);
        spriteStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();

        if (m_showSpawns && bgfx::isValid(m_spawnMarkerVertexBufferHandle) && m_spawnMarkerVertexCount > 0)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, m_spawnMarkerVertexBufferHandle, 0, m_spawnMarkerVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, m_programHandle);
        }

        spawnStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

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
            "Move: WASD Space jump Ctrl down Shift turbo  R run F fly T waterwalk G feather"
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
                    const OutdoorWorldRuntime::MapActorState *pActorState = runtimeActorStateForBillboard(actorBillboard);
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

        if (m_showGameplayHud)
        {
            renderChestPanel(width, height);
            renderEventDialogPanel(width, height, false);
            renderGameplayHudArt(width, height);
            renderGameplayHud(width, height);
            renderEventDialogPanel(width, height, true);
        }

        hudStageNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

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
    if (m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle)
        || !bgfx::isValid(m_programHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const HudLayoutElement *pBasebarLayout = findHudLayoutElement("OutdoorBasebar");
    const HudLayoutElement *pPartyStripLayout = findHudLayoutElement("OutdoorPartyStrip");
    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return;
    }

    const HudTextureHandle *pBasebar = ensureHudTextureLoaded(pBasebarLayout->primaryAsset);
    const HudTextureHandle *pFaceMask = ensureHudTextureLoaded(pPartyStripLayout->primaryAsset);
    const HudTextureHandle *pSelectionRing = ensureHudTextureLoaded(pPartyStripLayout->secondaryAsset);
    const HudTextureHandle *pManaFrame = ensureHudTextureLoaded(pPartyStripLayout->tertiaryAsset);
    const HudTextureHandle *pHealthBar = ensureHudTextureLoaded(pPartyStripLayout->quaternaryAsset);
    const HudTextureHandle *pManaBar = ensureHudTextureLoaded(pPartyStripLayout->quinaryAsset);
    const std::vector<Character> &members = m_pOutdoorPartyRuntime->party().members();

    if (pBasebar == nullptr || pFaceMask == nullptr || members.empty())
    {
        return;
    }

    const std::optional<ResolvedHudLayoutElement> resolvedBasebar = resolveHudLayoutElement(
        "OutdoorBasebar",
        width,
        height,
        static_cast<float>(pBasebar->width),
        static_cast<float>(pBasebar->height));
    const std::optional<ResolvedHudLayoutElement> resolvedPartyStrip = resolveHudLayoutElement(
        "OutdoorPartyStrip",
        width,
        height,
        static_cast<float>(pBasebar->width),
        static_cast<float>(pBasebar->height));

    if (!resolvedBasebar || !resolvedPartyStrip)
    {
        return;
    }

    const float uiScale = resolvedBasebar->scale;
    const float basebarWidth = resolvedBasebar->width;
    const float basebarHeight = resolvedBasebar->height;
    const float basebarX = resolvedBasebar->x;
    const float basebarY = resolvedBasebar->y;
    const float partyStripX = resolvedPartyStrip->x;
    const float partyStripY = resolvedPartyStrip->y;
    const float partyStripWidth = resolvedPartyStrip->width;
    const float partyStripHeight = resolvedPartyStrip->height;
    const float portraitWidth = pFaceMask->width * uiScale;
    const float portraitHeight = pFaceMask->height * uiScale;
    const float portraitStartX = partyStripX + partyStripWidth * (20.0f / 471.0f);
    const float portraitY = partyStripY + partyStripHeight * (23.0f / 92.0f);
    const float portraitDeltaX = partyStripWidth * (94.0f / 471.0f);
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

    auto submitTexturedQuad =
        [this](
            const HudTextureHandle &texture,
            float x,
            float y,
            float quadWidth,
            float quadHeight)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
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

    auto submitTexturedQuadUv =
        [this](
            const HudTextureHandle &texture,
            float x,
            float y,
            float quadWidth,
            float quadHeight,
            float u0,
            float v0,
            float u1,
            float v1)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
            TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, u0, v0};
            pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[3] = {x, y, 0.0f, u0, v0};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[5] = {x, y + quadHeight, 0.0f, u0, v1};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
        };

    auto submitTexturedQuadClipped =
        [this](
            const HudTextureHandle &texture,
            float x,
            float y,
            float quadWidth,
            float quadHeight,
            uint16_t scissorX,
            uint16_t scissorY,
            uint16_t scissorWidth,
            uint16_t scissorHeight)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
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
            bgfx::setScissor(scissorX, scissorY, scissorWidth, scissorHeight);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
        };

    auto submitColoredQuad =
        [this](
            float x,
            float y,
            float quadWidth,
            float quadHeight,
            uint32_t color)
        {
            if (bgfx::getAvailTransientVertexBuffer(6, TerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TerrainVertex::ms_layout);
            TerrainVertex *pVertices = reinterpret_cast<TerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, color};
            pVertices[1] = {x + quadWidth, y, 0.0f, color};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, color};
            pVertices[3] = {x, y, 0.0f, color};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, color};
            pVertices[5] = {x, y + quadHeight, 0.0f, color};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_programHandle);
        };

    struct MinimapOverlayState
    {
        bool valid = false;
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
        float scale = 1.0f;
        float u0 = 0.0f;
        float v0 = 0.0f;
        float uSpan = 1.0f;
        float vSpan = 1.0f;
    };

    MinimapOverlayState minimapOverlay = {};
    const HudScreenState hudScreenState = currentHudScreenState();

    const auto isGameplayElementVisibleInHudState =
        [this, hudScreenState](const HudLayoutElement &layout) -> bool
        {
            if (toLowerCopy(layout.screen) != "outdoorhud")
            {
                return false;
            }

            if (hudScreenState != HudScreenState::Dialogue)
            {
                return true;
            }

            const std::string normalizedId = toLowerCopy(layout.id);

            if (normalizedId == "outdoorbasebar"
                || normalizedId == "outdoorpartystrip"
                || normalizedId == "outdoorstatusbar"
                || normalizedId == "outdoortopbar"
                || normalizedId == "outdoorgoldfoodicon"
                || normalizedId.rfind("charshield_", 0) == 0)
            {
                return true;
            }

            if (normalizedId.rfind("outdoorminimap", 0) == 0)
            {
                return false;
            }

            const HudLayoutElement *pCurrent = &layout;

            while (pCurrent != nullptr && !pCurrent->parentId.empty())
            {
                if (toLowerCopy(pCurrent->parentId) == "outdoorbasebar")
                {
                    return true;
                }

                pCurrent = findHudLayoutElement(pCurrent->parentId);
            }

            return false;
        };

    submitTexturedQuad(*pBasebar, basebarX, basebarY, basebarWidth, basebarHeight);

    const size_t displayedMemberCount = members.size();

    for (size_t memberIndex = 0; memberIndex < displayedMemberCount; ++memberIndex)
    {
        const Character &member = members[memberIndex];
        const float portraitX = portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX;
        const float portraitInset = 2.0f * uiScale;
        const HudTextureHandle *pPortrait = ensureHudTextureLoaded(member.portraitTextureName);

        if (pPortrait != nullptr)
        {
            submitTexturedQuad(
                *pPortrait,
                portraitX + portraitInset,
                portraitY + portraitInset,
                portraitWidth - portraitInset * 2.0f,
                portraitHeight - portraitInset * 2.0f
            );
        }

        submitTexturedQuad(*pFaceMask, portraitX, portraitY, portraitWidth, portraitHeight);

        if (memberIndex == m_pOutdoorPartyRuntime->party().activeMemberIndex() && pSelectionRing != nullptr)
        {
            submitTexturedQuad(*pSelectionRing, portraitX - uiScale, portraitY, portraitWidth, portraitHeight);
        }

        if (pManaFrame != nullptr)
        {
            const float barFrameX = portraitX + partyStripWidth * (63.0f / 471.0f);
            const float barFrameWidth = pManaFrame->width * uiScale;
            const float barFrameHeight = pManaFrame->height * uiScale;
            const float barFrameY = basebarY + basebarHeight - barFrameHeight - partyStripHeight * (1.0f / 92.0f);
            submitTexturedQuad(*pManaFrame, barFrameX, barFrameY, barFrameWidth, barFrameHeight);

            const float fillHeight = 49.0f * uiScale;
            const float fillY = barFrameY + 1.0f * uiScale;
            const float leftFillX = barFrameX + 1.0f * uiScale;
            const float rightFillX = barFrameX + 5.0f * uiScale;
            const float fillWidth = 3.0f * uiScale;
            const float healthPercent = (member.maxHealth > 0)
                ? std::clamp(static_cast<float>(member.health) / static_cast<float>(member.maxHealth), 0.0f, 1.0f)
                : 0.0f;
            const float manaPercent = (member.maxSpellPoints > 0)
                ? std::clamp(static_cast<float>(member.spellPoints) / static_cast<float>(member.maxSpellPoints), 0.0f, 1.0f)
                : 0.0f;

            if (pHealthBar != nullptr && healthPercent > 0.0f)
            {
                submitTexturedQuadUv(
                    *pHealthBar,
                    leftFillX,
                    fillY + (1.0f - healthPercent) * fillHeight,
                    fillWidth,
                    healthPercent * fillHeight,
                    0.0f,
                    1.0f - healthPercent,
                    1.0f,
                    1.0f
                );
            }

            if (pManaBar != nullptr && manaPercent > 0.0f)
            {
                submitTexturedQuadUv(
                    *pManaBar,
                    rightFillX,
                    fillY + (1.0f - manaPercent) * fillHeight,
                    fillWidth,
                    manaPercent * fillHeight,
                    0.0f,
                    1.0f - manaPercent,
                    1.0f,
                    1.0f
                );
            }
        }
    }

    for (size_t memberIndex = displayedMemberCount; memberIndex < 5; ++memberIndex)
    {
        const std::string slotShieldId = "CharShield_" + std::to_string(memberIndex + 1);
        const HudLayoutElement *pShieldLayout = findHudLayoutElement(slotShieldId);

        if (pShieldLayout == nullptr || pShieldLayout->primaryAsset.empty())
        {
            continue;
        }

        const HudTextureHandle *pShieldTexture = ensureHudTextureLoaded(pShieldLayout->primaryAsset);

        if (pShieldTexture == nullptr)
        {
            continue;
        }

        const std::optional<ResolvedHudLayoutElement> resolvedShield = resolveHudLayoutElement(
            slotShieldId,
            width,
            height,
            pShieldLayout->width > 0.0f ? pShieldLayout->width : static_cast<float>(pShieldTexture->width),
            pShieldLayout->height > 0.0f ? pShieldLayout->height : static_cast<float>(pShieldTexture->height));

        if (!resolvedShield)
        {
            continue;
        }

        submitTexturedQuad(
            *pShieldTexture,
            resolvedShield->x,
            resolvedShield->y,
            resolvedShield->width,
            resolvedShield->height);
    }

    const auto renderOrderedSimpleHudElement =
        [&](const std::string &layoutId)
        {
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "outdoorbasebar"
                || normalizedLayoutId == "outdoorpartystrip"
                || normalizedLayoutId.rfind("charshield_", 0) == 0)
            {
                return;
            }

            const HudLayoutElement *pLayout = findHudLayoutElement(layoutId);

            if (pLayout == nullptr || !pLayout->visible)
            {
                return;
            }

            if (!isGameplayElementVisibleInHudState(*pLayout))
            {
                return;
            }

            if (normalizedLayoutId == "outdoorminimap")
            {
                if (!m_map
                    || m_pOutdoorPartyRuntime == nullptr
                    || pLayout->width <= 0.0f
                    || pLayout->height <= 0.0f)
                {
                    return;
                }

                const std::string mapTextureName =
                    toLowerCopy(std::filesystem::path(m_map->fileName).stem().string());
                const HudTextureHandle *pTexture = ensureHudTextureLoaded(mapTextureName);

                if (pTexture == nullptr)
                {
                    return;
                }

                const std::optional<ResolvedHudLayoutElement> resolved = resolveHudLayoutElement(
                    layoutId,
                    width,
                    height,
                    pLayout->width,
                    pLayout->height);

                if (!resolved)
                {
                    return;
                }

                const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();

                // Outdoor runtime still uses mirrored X, while minimap BMPs stay in original map orientation.
                const float partyU = std::clamp((-moveState.x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
                const float partyV = std::clamp((32768.0f - moveState.y) / 65536.0f, 0.0f, 1.0f);
                const float uSpan = std::min(1.0f, pLayout->width / OutdoorMinimapZoom);
                const float vSpan = std::min(1.0f, pLayout->height / OutdoorMinimapZoom);
                const float u0 = std::clamp(partyU - uSpan * 0.5f, 0.0f, 1.0f - uSpan);
                const float v0 = std::clamp(partyV - vSpan * 0.5f, 0.0f, 1.0f - vSpan);

                submitTexturedQuadUv(
                    *pTexture,
                    resolved->x,
                    resolved->y,
                    resolved->width,
                    resolved->height,
                    u0,
                    v0,
                    u0 + uSpan,
                    v0 + vSpan);
                minimapOverlay.valid = true;
                minimapOverlay.x = resolved->x;
                minimapOverlay.y = resolved->y;
                minimapOverlay.width = resolved->width;
                minimapOverlay.height = resolved->height;
                minimapOverlay.scale = resolved->scale;
                minimapOverlay.u0 = u0;
                minimapOverlay.v0 = v0;
                minimapOverlay.uSpan = uSpan;
                minimapOverlay.vSpan = vSpan;
                return;
            }

            if (pLayout->primaryAsset.empty())
            {
                return;
            }

            const HudTextureHandle *pTexture = ensureHudTextureLoaded(pLayout->primaryAsset);

            if (pTexture == nullptr)
            {
                return;
            }

            const std::optional<ResolvedHudLayoutElement> resolved = resolveHudLayoutElement(
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

    const std::vector<std::string> orderedGameplayLayoutIds = sortedHudLayoutIdsForScreen("OutdoorHud");

    for (const std::string &layoutId : orderedGameplayLayoutIds)
    {
        renderOrderedSimpleHudElement(layoutId);
    }

    if (hudScreenState == HudScreenState::Gameplay && minimapOverlay.valid && m_pOutdoorPartyRuntime != nullptr)
    {
        const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
        const float partyU = std::clamp((-moveState.x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
        const float partyV = std::clamp((32768.0f - moveState.y) / 65536.0f, 0.0f, 1.0f);
        const float minimapCenterX =
            minimapOverlay.x + ((partyU - minimapOverlay.u0) / minimapOverlay.uSpan) * minimapOverlay.width;
        const float minimapCenterY =
            minimapOverlay.y + ((partyV - minimapOverlay.v0) / minimapOverlay.vSpan) * minimapOverlay.height;
        const float markerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float markerHalfSize = markerSize * 0.5f;
        const float markerMargin = std::max(2.0f, 2.0f * minimapOverlay.scale);
        const float markerMinX = minimapOverlay.x + markerMargin + markerHalfSize;
        const float markerMaxX = minimapOverlay.x + minimapOverlay.width - markerMargin - markerHalfSize;
        const float markerMinY = minimapOverlay.y + markerMargin + markerHalfSize;
        const float markerMaxY = minimapOverlay.y + minimapOverlay.height - markerMargin - markerHalfSize;
        const uint16_t minimapScissorX = static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.x + markerMargin)));
        const uint16_t minimapScissorY = static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.y + markerMargin)));
        const uint16_t minimapScissorWidth = static_cast<uint16_t>(std::max(
            1.0f,
            std::ceil(minimapOverlay.width - markerMargin * 2.0f)));
        const uint16_t minimapScissorHeight = static_cast<uint16_t>(std::max(
            1.0f,
            std::ceil(minimapOverlay.height - markerMargin * 2.0f)));
        const HudTextureHandle *pFriendlyMarkerTexture =
            ensureSolidHudTextureLoaded("__minimap_marker_friendly__", 0xff00ff00u);
        const HudTextureHandle *pHostileMarkerTexture =
            ensureSolidHudTextureLoaded("__minimap_marker_hostile__", 0xffff0000u);
        const HudTextureHandle *pCorpseMarkerTexture =
            ensureSolidHudTextureLoaded("__minimap_marker_corpse__", 0xffffff00u);

        if (m_pOutdoorWorldRuntime != nullptr)
        {
            for (size_t actorIndex = 0; actorIndex < m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

                if (pActor == nullptr || pActor->isInvisible)
                {
                    continue;
                }

                const float actorU = (-static_cast<float>(pActor->x) + 32768.0f) / 65536.0f;
                const float actorV = (32768.0f - static_cast<float>(pActor->y)) / 65536.0f;
                const float markerCenterX =
                    minimapOverlay.x + ((actorU - minimapOverlay.u0) / minimapOverlay.uSpan) * minimapOverlay.width;
                const float markerCenterY =
                    minimapOverlay.y + ((actorV - minimapOverlay.v0) / minimapOverlay.vSpan) * minimapOverlay.height;

                if (markerCenterX < markerMinX || markerCenterX > markerMaxX
                    || markerCenterY < markerMinY || markerCenterY > markerMaxY)
                {
                    continue;
                }

                const HudTextureHandle *pMarkerTexture = pActor->isDead
                    ? pCorpseMarkerTexture
                    : pActor->hostileToParty ? pHostileMarkerTexture : pFriendlyMarkerTexture;

                if (pMarkerTexture == nullptr)
                {
                    continue;
                }

                submitTexturedQuadClipped(
                    *pMarkerTexture,
                    markerCenterX - markerHalfSize,
                    markerCenterY - markerHalfSize,
                    markerSize,
                    markerSize,
                    minimapScissorX,
                    minimapScissorY,
                    minimapScissorWidth,
                    minimapScissorHeight);
            }
        }

        float normalizedYaw = std::fmod(m_cameraYawRadians, Pi * 2.0f);

        if (normalizedYaw < 0.0f)
        {
            normalizedYaw += Pi * 2.0f;
        }

        const int octant = static_cast<int>(std::floor((normalizedYaw + Pi * 0.125f) / (Pi * 0.25f))) % 8;
        const int arrowIndex = (octant + 3) % 8;
        const std::string arrowTextureName = "MAPDIR" + std::to_string(arrowIndex + 1);
        const HudTextureHandle *pArrowTexture = ensureHudTextureLoaded(arrowTextureName);

        if (pArrowTexture != nullptr)
        {
            const float arrowWidth = static_cast<float>(pArrowTexture->width) * minimapOverlay.scale;
            const float arrowHeight = static_cast<float>(pArrowTexture->height) * minimapOverlay.scale;
            submitTexturedQuadClipped(
                *pArrowTexture,
                minimapCenterX - arrowWidth * 0.5f,
                minimapCenterY - arrowHeight * 0.5f,
                arrowWidth,
                arrowHeight,
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }
    }

}

void OutdoorGameView::renderGameplayHud(int width, int height) const
{
    if (m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const Party &party = m_pOutdoorPartyRuntime->party();
    const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
    const OutdoorPartyMovementState &partyMovementState = m_pOutdoorPartyRuntime->partyMovementState();
    const std::vector<Character> &members = party.members();
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
    const HudScreenState hudScreenState = currentHudScreenState();

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
    const auto resolveCounterLabel = [&replaceAll](const std::string &labelText, const std::string &value) -> std::string
    {
        if (labelText.empty())
        {
            return value;
        }

        const std::string replacedGold = replaceAll(labelText, "{gold}", value);
        const std::string replacedFood = replaceAll(replacedGold, "{food}", value);

        if (replacedFood == labelText)
        {
            return value;
        }

        return replacedFood;
    };
    const std::optional<ResolvedHudLayoutElement> resolvedStatusBar = resolveHudLayoutElement(
        "OutdoorStatusBar",
        width,
        height,
        360.0f,
        18.0f);

    if (!resolvedStatusBar)
    {
        return;
    }
    std::string statusBarLabel;

    if (m_statusBarEventRemainingSeconds > 0.0f && !m_statusBarEventText.empty())
    {
        statusBarLabel = m_statusBarEventText;
    }
    if (const HudLayoutElement *pStatusBarLayout = findHudLayoutElement("OutdoorStatusBar"))
    {
        renderLayoutLabel(*pStatusBarLayout, *resolvedStatusBar, statusBarLabel);
    }

    if (const HudLayoutElement *pTopBarLayout = findHudLayoutElement("OutdoorTopBar"))
    {
        if (const std::optional<ResolvedHudLayoutElement> topBar = resolveHudLayoutElement(
                "OutdoorTopBar",
                width,
                height,
                640.0f,
                29.0f))
        {
            if (!pTopBarLayout->labelText.empty())
            {
                const std::string label = replaceAll(
                    replaceAll(pTopBarLayout->labelText, "{gold}", std::to_string(party.gold())),
                    "{food}",
                    std::to_string(party.food()));
                renderLayoutLabel(*pTopBarLayout, *topBar, label);
            }
        }
    }

    if (const HudLayoutElement *pGoldLabelLayout = findHudLayoutElement("OutdoorGoldLabel"))
    {
        if (const std::optional<ResolvedHudLayoutElement> goldLabel = resolveHudLayoutElement(
                "OutdoorGoldLabel",
                width,
                height,
                28.0f,
                14.0f))
        {
            const std::string label = resolveCounterLabel(pGoldLabelLayout->labelText, std::to_string(party.gold()));
            renderLayoutLabel(*pGoldLabelLayout, *goldLabel, label);
        }
    }

    if (const HudLayoutElement *pFoodLabelLayout = findHudLayoutElement("OutdoorFoodLabel"))
    {
        if (const std::optional<ResolvedHudLayoutElement> foodLabel = resolveHudLayoutElement(
                "OutdoorFoodLabel",
                width,
                height,
                28.0f,
                14.0f))
        {
            const std::string label = resolveCounterLabel(pFoodLabelLayout->labelText, std::to_string(party.food()));
            renderLayoutLabel(*pFoodLabelLayout, *foodLabel, label);
        }
    }

    if (hudScreenState == HudScreenState::Dialogue)
    {
        return;
    }

    if (const HudLayoutElement *pBottomLeftButtonsLayout = findHudLayoutElement("OutdoorBottomLeftButtons"))
    {
        if (const std::optional<ResolvedHudLayoutElement> bottomLeftButtons = resolveHudLayoutElement(
                "OutdoorBottomLeftButtons",
                width,
                height,
                180.0f,
                32.0f))
        {
            renderLayoutLabel(*pBottomLeftButtonsLayout, *bottomLeftButtons, pBottomLeftButtonsLayout->labelText);
        }
    }

    if (const HudLayoutElement *pSkullPanelLayout = findHudLayoutElement("OutdoorBuffSkullPanel"))
    {
        if (const std::optional<ResolvedHudLayoutElement> skullPanel = resolveHudLayoutElement(
                "OutdoorBuffSkullPanel",
                width,
                height,
                96.0f,
                48.0f))
        {
            renderLayoutLabel(*pSkullPanelLayout, *skullPanel, pSkullPanelLayout->labelText);
        }
    }

    if (const HudLayoutElement *pBodyPanelLayout = findHudLayoutElement("OutdoorBuffBodyPanel"))
    {
        if (const std::optional<ResolvedHudLayoutElement> bodyPanel = resolveHudLayoutElement(
                "OutdoorBuffBodyPanel",
                width,
                height,
                96.0f,
                48.0f))
        {
            renderLayoutLabel(*pBodyPanelLayout, *bodyPanel, pBodyPanelLayout->labelText);
        }
    }
}

void OutdoorGameView::renderChestPanel(int width, int height) const
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
            openPendingEventDialog(pEventRuntimeState->messages.size(), true);
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

    for (BillboardTextureHandle &textureHandle : m_billboardTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_billboardTextureHandles.clear();
    m_billboardTextureIndexByPalette.clear();
    m_spriteLoadCache.directoryAssetPathsByPath.clear();
    m_spriteLoadCache.assetPathByKey.clear();
    m_spriteLoadCache.binaryFilesByPath.clear();
    m_spriteLoadCache.actPalettesById.clear();
    m_pendingSpriteFrameWarmups.clear();
    m_queuedSpriteFrameWarmups.clear();
    m_nextPendingSpriteFrameWarmupIndex = 0;
    m_runtimeActorBillboardTexturesQueuedCount = 0;

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
    m_hudLayoutElements.clear();

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

    m_isRenderable = false;
    m_isInitialized = false;
    m_map.reset();
    m_monsterTable.reset();
    m_outdoorMapData.reset();
    m_pOutdoorPartyRuntime = nullptr;
    m_pAssetFileSystem = nullptr;
    m_pOutdoorWorldRuntime = nullptr;
    m_pItemTable = nullptr;
    m_pRosterTable = nullptr;
    m_pObjectTable = nullptr;
    m_pSpellTable = nullptr;
    m_localEventIrProgram.reset();
    m_globalEventIrProgram.reset();
    m_outdoorDecorationBillboardSet.reset();
    m_outdoorActorPreviewBillboardSet.reset();
    m_outdoorSpriteObjectBillboardSet.reset();
    m_classSkillTable.reset();
    m_npcDialogTable.reset();
    m_elapsedTime = 0.0f;
    m_framesPerSecond = 0.0f;
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
    m_activateInspectLatch = false;
    m_inspectMouseActivateLatch = false;
    m_attackInspectLatch = false;
    m_closeOverlayLatch = false;
    m_dialogueClickLatch = false;
    m_dialoguePressedTargetType = DialoguePointerTargetType::None;
    m_dialoguePressedTargetIndex = 0;
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
}

void OutdoorGameView::executeActiveDialogAction()
{
    if (!m_activeEventDialog.isActive
        || m_eventDialogSelectionIndex >= m_activeEventDialog.actions.size())
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    const EventDialogAction &action = m_activeEventDialog.actions[m_eventDialogSelectionIndex];
    const size_t previousMessageCount = pEventRuntimeState->messages.size();

    if (!action.enabled)
    {
        if (action.kind == EventDialogActionKind::HouseService)
        {
            if (!action.disabledReason.empty())
            {
                setStatusBarEvent(action.disabledReason);
            }

            return;
        }

        if (!action.disabledReason.empty())
        {
            pEventRuntimeState->messages.push_back(action.disabledReason);
            openPendingEventDialog(previousMessageCount, true);
        }

        return;
    }

    if (action.kind == EventDialogActionKind::HouseService)
    {
        if (m_pOutdoorPartyRuntime == nullptr || !m_houseTable)
        {
            return;
        }

        const HouseEntry *pHouseEntry = m_houseTable->get(m_activeEventDialog.sourceId);

        if (pHouseEntry == nullptr)
        {
            return;
        }

        const DialogueMenuId menuId = dialogueMenuIdForHouseAction(static_cast<HouseActionId>(action.id));

        if (menuId != DialogueMenuId::None)
        {
            pEventRuntimeState->dialogueState.menuStack.push_back(menuId);
        }
        else
        {
            std::vector<std::string> messages;
            HouseActionOption option = {};
            option.id = static_cast<HouseActionId>(action.id);
            option.label = action.label;
            option.argument = action.argument;
            performHouseAction(
                option,
                *pHouseEntry,
                m_pOutdoorPartyRuntime->party(),
                m_classSkillTable ? &*m_classSkillTable : nullptr,
                m_pOutdoorWorldRuntime,
                messages
            );

            for (const std::string &message : messages)
            {
                setStatusBarEvent(message);
            }
        }

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::HouseService;
        context.sourceId = m_activeEventDialog.sourceId;
        context.hostHouseId = m_activeEventDialog.sourceId;
        pEventRuntimeState->dialogueState.hostHouseId = m_activeEventDialog.sourceId;
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(previousMessageCount, true);
        return;
    }

    if (action.kind == EventDialogActionKind::HouseResident)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = action.id;
        context.hostHouseId = m_activeEventDialog.sourceId;
        pEventRuntimeState->dialogueState.hostHouseId = m_activeEventDialog.sourceId;
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(previousMessageCount, true);
        return;
    }

    if (action.kind == EventDialogActionKind::RosterJoinOffer)
    {
        if (!m_npcDialogTable)
        {
            return;
        }

        const std::optional<NpcDialogTable::RosterJoinOffer> offer =
            m_npcDialogTable->getRosterJoinOfferForTopic(action.id);

        if (!offer)
        {
            pEventRuntimeState->messages.push_back("That companion is not ready to join yet.");
            openPendingEventDialog(previousMessageCount, true);
            return;
        }

        const std::optional<std::string> inviteText = m_npcDialogTable->getText(offer->inviteTextId);

        if (inviteText && !inviteText->empty())
        {
            pEventRuntimeState->messages.push_back(*inviteText);
        }

        EventRuntimeState::DialogueOfferState offerState = {};
        offerState.kind = DialogueOfferKind::RosterJoin;
        offerState.npcId = m_activeEventDialog.sourceId;
        offerState.topicId = action.id;
        offerState.messageTextId = offer->inviteTextId;
        offerState.rosterId = offer->rosterId;
        offerState.partyFullTextId = offer->partyFullTextId;
        pEventRuntimeState->dialogueState.currentOffer = std::move(offerState);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = m_activeEventDialog.sourceId;
        context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(previousMessageCount, true);
        return;
    }

    if (action.kind == EventDialogActionKind::RosterJoinAccept)
    {
        if (!pEventRuntimeState->dialogueState.currentOffer
            || pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::RosterJoin
            || m_pOutdoorPartyRuntime == nullptr
            || m_pRosterTable == nullptr)
        {
            return;
        }

        const EventRuntimeState::DialogueOfferState invite = *pEventRuntimeState->dialogueState.currentOffer;
        pEventRuntimeState->dialogueState.currentOffer.reset();

        if (m_pOutdoorPartyRuntime->party().isFull())
        {
            pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;

            if (m_npcDialogTable)
            {
                const std::optional<std::string> fullPartyText = m_npcDialogTable->getText(invite.partyFullTextId);

                if (fullPartyText && !fullPartyText->empty())
                {
                    pEventRuntimeState->messages.push_back(*fullPartyText);
                }
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = invite.npcId;
            context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
            pEventRuntimeState->pendingDialogueContext = std::move(context);
            openPendingEventDialog(previousMessageCount, false);
            return;
        }

        const RosterEntry *pRosterEntry = m_pRosterTable->get(invite.rosterId);

        if (pRosterEntry == nullptr || !m_pOutdoorPartyRuntime->party().recruitRosterMember(*pRosterEntry))
        {
            pEventRuntimeState->messages.push_back("Recruitment is not available for this companion yet.");

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = invite.npcId;
            context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
            pEventRuntimeState->pendingDialogueContext = std::move(context);
            openPendingEventDialog(previousMessageCount, true);
            return;
        }

        pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
        pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
        pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = invite.npcId;
        context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(previousMessageCount, false);
        return;
    }

    if (action.kind == EventDialogActionKind::RosterJoinDecline)
    {
        const uint32_t npcId =
            (pEventRuntimeState->dialogueState.currentOffer
             && pEventRuntimeState->dialogueState.currentOffer->kind == DialogueOfferKind::RosterJoin)
            ? pEventRuntimeState->dialogueState.currentOffer->npcId
            : m_activeEventDialog.sourceId;
        pEventRuntimeState->dialogueState.currentOffer.reset();

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = npcId;
        context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(previousMessageCount, true);
        return;
    }

    if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
    {
        EventRuntimeState::DialogueOfferState offer = {};
        offer.kind = DialogueOfferKind::MasteryTeacher;
        offer.npcId = m_activeEventDialog.sourceId;
        offer.topicId = action.id;
        pEventRuntimeState->dialogueState.currentOffer = std::move(offer);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = m_activeEventDialog.sourceId;
        context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(previousMessageCount, true);
        return;
    }

    if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
    {
        if (!pEventRuntimeState->dialogueState.currentOffer
            || pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::MasteryTeacher
            || m_pOutdoorPartyRuntime == nullptr
            || !m_classSkillTable
            || !m_npcDialogTable)
        {
            return;
        }

        std::string message;

        if (applyMasteryTeacherTopic(
                pEventRuntimeState->dialogueState.currentOffer->topicId,
                m_pOutdoorPartyRuntime->party(),
                *m_classSkillTable,
                *m_npcDialogTable,
                message))
        {
            if (!message.empty())
            {
                setStatusBarEvent(message);
            }

            pEventRuntimeState->dialogueState.currentOffer.reset();
            openPendingEventDialog(previousMessageCount, false);
        }
        else
        {
            const std::optional<MasteryTeacherEvaluation> evaluation = evaluateMasteryTeacherTopic(
                pEventRuntimeState->dialogueState.currentOffer->topicId,
                m_pOutdoorPartyRuntime->party(),
                *m_classSkillTable,
                *m_npcDialogTable
            );

            if (evaluation && !evaluation->displayText.empty())
            {
                setStatusBarEvent(evaluation->displayText);
            }

            openPendingEventDialog(previousMessageCount, true);
        }

        return;
    }

    if (action.kind == EventDialogActionKind::NpcTopic)
    {
        const uint32_t npcId = m_activeEventDialog.sourceId;
        bool executed = false;

        if (action.textOnly && m_npcDialogTable)
        {
            const std::optional<NpcDialogTable::ResolvedTopic> topic =
                m_npcDialogTable->getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

            if (topic && !topic->text.empty())
            {
                pEventRuntimeState->messages.push_back(topic->text);
                executed = true;
            }
        }
        else
        {
            executed = m_eventRuntime.executeEventById(
                std::nullopt,
                m_globalEventIrProgram,
                static_cast<uint16_t>(action.id),
                *pEventRuntimeState,
                m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->party() : nullptr,
                m_pOutdoorWorldRuntime
            );
        }

        if (executed)
        {
            if (m_pOutdoorWorldRuntime != nullptr)
            {
                m_pOutdoorWorldRuntime->applyEventRuntimeState();
            }

            if (m_pOutdoorPartyRuntime != nullptr)
            {
                m_pOutdoorPartyRuntime->applyEventRuntimeState(*pEventRuntimeState);
            }
        }
        else
        {
            pEventRuntimeState->messages.push_back("That topic does not have an event yet.");
        }

        if (!pEventRuntimeState->pendingDialogueContext)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = npcId;
            context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }

        openPendingEventDialog(previousMessageCount, true);
    }
}

void OutdoorGameView::openPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent)
{
    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    if (!pEventRuntimeState->pendingDialogueContext)
    {
        return;
    }

    const EventRuntimeState::PendingDialogueContext originalContext = *pEventRuntimeState->pendingDialogueContext;

    if (pEventRuntimeState->pendingDialogueContext->kind == DialogueContextKind::HouseService
        && m_houseTable
        && m_npcDialogTable)
    {
        const HouseEntry *pHouseEntry = m_houseTable->get(pEventRuntimeState->pendingDialogueContext->sourceId);

        if (pHouseEntry != nullptr)
        {
            const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
                *pHouseEntry,
                m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->party() : nullptr,
                m_classSkillTable ? &*m_classSkillTable : nullptr,
                m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->currentHour() : -1,
                pEventRuntimeState->dialogueState.menuStack.empty()
                    ? DialogueMenuId::None
                    : pEventRuntimeState->dialogueState.menuStack.back()
            );
            const std::optional<uint32_t> residentNpcId = singleSelectableResidentNpcId(
                *pHouseEntry,
                *m_npcDialogTable,
                *pEventRuntimeState
            );

            if (residentNpcId && houseActions.empty())
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcTalk;
                context.sourceId = *residentNpcId;
                context.hostHouseId = pHouseEntry->id;
                pEventRuntimeState->dialogueState.hostHouseId = pHouseEntry->id;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
            }
        }
    }

    m_activeEventDialog = buildEventDialogContent(
        *pEventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        &m_globalEventIrProgram,
        m_houseTable ? &*m_houseTable : nullptr,
        m_classSkillTable ? &*m_classSkillTable : nullptr,
        m_npcDialogTable ? &*m_npcDialogTable : nullptr,
        m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->party() : nullptr,
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->currentHour() : -1
    );

    if (!m_activeEventDialog.isActive)
    {
        pEventRuntimeState->pendingDialogueContext.reset();
        return;
    }

    if (originalContext.hostHouseId != 0)
    {
        pEventRuntimeState->dialogueState.hostHouseId = originalContext.hostHouseId;
    }
    else if (originalContext.kind == DialogueContextKind::HouseService)
    {
        pEventRuntimeState->dialogueState.hostHouseId = originalContext.sourceId;
    }

    m_eventDialogSelectionIndex = 0;
    m_eventDialogSelectUpLatch = false;
    m_eventDialogSelectDownLatch = false;
    m_eventDialogAcceptLatch = false;
    m_eventDialogPartySelectLatches.fill(false);

    std::cout << "Opened "
              << (m_activeEventDialog.isHouseDialog ? "house" : "npc")
              << " dialog for id=" << m_activeEventDialog.sourceId << '\n';
}

void OutdoorGameView::closeActiveEventDialog()
{
    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->pendingDialogueContext.reset();
        pEventRuntimeState->dialogueState = {};
    }

    m_activeEventDialog = {};
    m_eventDialogSelectionIndex = 0;
    m_eventDialogSelectUpLatch = false;
    m_eventDialogSelectDownLatch = false;
    m_eventDialogAcceptLatch = false;
    m_eventDialogPartySelectLatches.fill(false);
    m_dialogueClickLatch = false;
    m_dialoguePressedTargetType = DialoguePointerTargetType::None;
    m_dialoguePressedTargetIndex = 0;
}

bool OutdoorGameView::hasActiveEventDialog() const
{
    return m_activeEventDialog.isActive;
}

OutdoorGameView::HudScreenState OutdoorGameView::currentHudScreenState() const
{
    if (m_activeEventDialog.isActive)
    {
        return HudScreenState::Dialogue;
    }

    return HudScreenState::Gameplay;
}

void OutdoorGameView::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    if (text.empty())
    {
        return;
    }

    m_statusBarEventText = text;
    m_statusBarEventRemainingSeconds = std::max(0.0f, durationSeconds);
}

void OutdoorGameView::updateStatusBarEvent(float deltaSeconds)
{
    if (m_statusBarEventRemainingSeconds <= 0.0f)
    {
        return;
    }

    m_statusBarEventRemainingSeconds = std::max(0.0f, m_statusBarEventRemainingSeconds - deltaSeconds);

    if (m_statusBarEventRemainingSeconds <= 0.0f)
    {
        m_statusBarEventText.clear();
    }
}

void OutdoorGameView::handleDialogueCloseRequest()
{
    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr && !pEventRuntimeState->dialogueState.menuStack.empty())
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::HouseService;
        context.sourceId = currentDialogueHostHouseId(pEventRuntimeState) != 0
            ? currentDialogueHostHouseId(pEventRuntimeState)
            : m_activeEventDialog.sourceId;
        context.hostHouseId = context.sourceId;
        pEventRuntimeState->dialogueState.menuStack.pop_back();
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(pEventRuntimeState->messages.size(), true);
        return;
    }

    if (pEventRuntimeState != nullptr
        && pEventRuntimeState->dialogueState.currentOffer
        && pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::None)
    {
        const uint32_t npcId = pEventRuntimeState->dialogueState.currentOffer->npcId;
        pEventRuntimeState->dialogueState.currentOffer.reset();

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = npcId != 0 ? npcId : m_activeEventDialog.sourceId;
        context.hostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(pEventRuntimeState->messages.size(), true);
        return;
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
    const HouseEntry *pHostHouseEntry =
        (currentDialogueHostHouseId(pEventRuntimeState) != 0 && m_houseTable.has_value())
        ? m_houseTable->get(currentDialogueHostHouseId(pEventRuntimeState))
        : nullptr;
    const std::vector<uint32_t> hostResidentNpcIds =
        (pHostHouseEntry != nullptr && m_npcDialogTable.has_value() && pEventRuntimeState != nullptr)
        ? collectSelectableResidentNpcIds(*pHostHouseEntry, *m_npcDialogTable, *pEventRuntimeState)
        : std::vector<uint32_t>{};

    if (!m_activeEventDialog.isHouseDialog
        && !isResidentSelectionMode
        && pEventRuntimeState != nullptr
        && hostResidentNpcIds.size() > 1)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::HouseService;
        context.sourceId = currentDialogueHostHouseId(pEventRuntimeState);
        context.hostHouseId = context.sourceId;
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        openPendingEventDialog(pEventRuntimeState->messages.size(), true);
    }
    else
    {
        closeActiveEventDialog();
        m_activateInspectLatch = true;
    }
}

void OutdoorGameView::openDebugNpcDialogue(uint32_t npcId)
{
    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || npcId == 0)
    {
        return;
    }

    const size_t previousMessageCount = pEventRuntimeState->messages.size();
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcTalk;
    context.sourceId = npcId;
    pEventRuntimeState->dialogueState.hostHouseId = 0;
    pEventRuntimeState->pendingDialogueContext = std::move(context);
    pEventRuntimeState->lastActivationResult = "debug npc " + std::to_string(npcId) + " engaged";
    openPendingEventDialog(previousMessageCount, true);
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
    static constexpr uint32_t HoveredDialogueTopicTextColorAbgr = 0xff23cde1u;
    const UiViewportRect uiViewport = computeUiViewportRect(width, height);

    if (!renderAboveHud && uiViewport.x > 0.5f)
    {
        const HudTextureHandle *pBlackTexture = ensureSolidHudTextureLoaded("__dialogue_blackout__", 0xff000000u);

        if (pBlackTexture != nullptr)
        {
            const auto drawSolidRect =
                [this, pBlackTexture](float x, float y, float rectWidth, float rectHeight)
                {
                    if (rectWidth <= 0.0f || rectHeight <= 0.0f)
                    {
                        return;
                    }

                    bgfx::TransientVertexBuffer transientVertexBuffer;

                    if (bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
                    {
                        return;
                    }

                    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
                    TexturedTerrainVertex *pVertices =
                        reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
                    pVertices[0] = {x, y, 0.0f, 0.0f, 0.0f};
                    pVertices[1] = {x + rectWidth, y, 0.0f, 1.0f, 0.0f};
                    pVertices[2] = {x + rectWidth, y + rectHeight, 0.0f, 1.0f, 1.0f};
                    pVertices[3] = {x, y, 0.0f, 0.0f, 0.0f};
                    pVertices[4] = {x + rectWidth, y + rectHeight, 0.0f, 1.0f, 1.0f};
                    pVertices[5] = {x, y + rectHeight, 0.0f, 0.0f, 1.0f};

                    float modelMatrix[16] = {};
                    bx::mtxIdentity(modelMatrix);
                    bgfx::setTransform(modelMatrix);
                    bgfx::setVertexBuffer(0, &transientVertexBuffer);
                    bgfx::setTexture(0, m_terrainTextureSamplerHandle, pBlackTexture->textureHandle);
                    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                    bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
                };

            drawSolidRect(0.0f, 0.0f, uiViewport.x, static_cast<float>(height));
            drawSolidRect(
                uiViewport.x + uiViewport.width,
                0.0f,
                static_cast<float>(width) - (uiViewport.x + uiViewport.width),
                static_cast<float>(height));
        }
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
    const std::vector<uint32_t> hostResidentNpcIds =
        (pHostHouseEntry != nullptr && m_npcDialogTable.has_value() && pEventRuntimeState != nullptr)
        ? collectSelectableResidentNpcIds(*pHostHouseEntry, *m_npcDialogTable, *pEventRuntimeState)
        : std::vector<uint32_t>{};
    const bool showEventDialogPanel =
        isResidentSelectionMode || !m_activeEventDialog.actions.empty() || pHostHouseEntry != nullptr;
    const bool showDialogueTextFrame = !m_activeEventDialog.lines.empty();
    const int hudZThreshold = defaultHudLayoutZIndexForScreen("OutdoorHud");
    const auto shouldRenderInCurrentPass =
        [renderAboveHud, hudZThreshold](int zIndex) -> bool
        {
            return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
        };
    const auto isDialogueFrameSubtree =
        [this](const HudLayoutElement &layout) -> bool
        {
            std::string currentLayoutId = layout.id;

            while (!currentLayoutId.empty())
            {
                if (toLowerCopy(currentLayoutId) == "dialogueframe")
                {
                    return true;
                }

                const HudLayoutElement *pCurrentLayout = findHudLayoutElement(currentLayoutId);

                if (pCurrentLayout == nullptr || pCurrentLayout->parentId.empty())
                {
                    break;
                }

                currentLayoutId = pCurrentLayout->parentId;
            }

            return false;
        };
    const HudLayoutElement *pDialogueFrameLayout = findHudLayoutElement("DialogueFrame");
    const HudLayoutElement *pDialogueTextLayout = findHudLayoutElement("DialogueText");
    const HudLayoutElement *pBasebarLayout = findHudLayoutElement("OutdoorBasebar");

    if (showDialogueTextFrame
        && pDialogueFrameLayout != nullptr
        && pDialogueTextLayout != nullptr
        && pBasebarLayout != nullptr
        && toLowerCopy(pDialogueFrameLayout->screen) == "dialogue"
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue")
    {
        const HudFontHandle *pFont = findHudFont(pDialogueTextLayout->fontName);

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

            for (const std::string &line : m_activeEventDialog.lines)
            {
                const std::vector<std::string> wrappedLines = wrapHudTextToWidth(*pFont, line, textWrapWidth);
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

            static std::string lastLoggedAuthoritativeDialogueFrameKey;
            const std::string currentAuthoritativeDialogueFrameKey =
                std::to_string(static_cast<int>(std::round(authoritativeFrameHeight))) + "|"
                + std::to_string(static_cast<int>(std::round(rawComputedTextHeight))) + "|"
                + std::to_string(wrappedLineCount);

            if (lastLoggedAuthoritativeDialogueFrameKey != currentAuthoritativeDialogueFrameKey)
            {
                std::cout
                    << "DialogueFrame authoritative height debug: frame_height=" << authoritativeFrameHeight
                    << " basebar_height=" << pBasebarLayout->height
                    << " text_height_from_yml=" << pDialogueTextLayout->height
                    << " raw_computed_text_height=" << rawComputedTextHeight
                    << " effective_text_height=" << unscaledTextHeight
                    << " line_count=" << wrappedLineCount
                    << " line_height=" << lineHeight
                    << " text_pad_y=" << textPadY
                    << " top_inset=" << DialogueTextTopInset
                    << " bottom_inset=" << DialogueTextBottomInset
                    << '\n';
                lastLoggedAuthoritativeDialogueFrameKey = currentAuthoritativeDialogueFrameKey;
            }
        }
    }

    const std::optional<ResolvedHudLayoutElement> resolvedText =
        pDialogueTextLayout != nullptr
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue"
        ? resolveHudLayoutElement(
            "DialogueText",
            width,
            height,
            pDialogueTextLayout->width,
            pDialogueTextLayout->height)
        : std::nullopt;

    const auto renderDialogueTextureElement =
        [this,
         width,
         height,
         dialogMouseX,
         dialogMouseY,
         showDialogueTextFrame,
         showEventDialogPanel,
         &isDialogueFrameSubtree,
         &shouldRenderInCurrentPass](
            const std::string &layoutId)
        {
            const HudLayoutElement *pLayout = findHudLayoutElement(layoutId);

            if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->screen) != "dialogue")
            {
                return;
            }

            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "dialoguenpcportrait"
                || normalizedLayoutId == "dialoguetext")
            {
                return;
            }

            if (!showDialogueTextFrame && isDialogueFrameSubtree(*pLayout))
            {
                return;
            }

            if (normalizedLayoutId == "dialogueeventdialog" && !showEventDialogPanel)
            {
                return;
            }

            if (!shouldRenderInCurrentPass(pLayout->zIndex))
            {
                return;
            }

            const HudTextureHandle *pBaseTexture = nullptr;

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                pBaseTexture = ensureHudTextureLoaded(pLayout->primaryAsset);
            }

            const std::optional<ResolvedHudLayoutElement> resolved = resolveHudLayoutElement(
                layoutId,
                width,
                height,
                pLayout->width > 0.0f
                    ? pLayout->width
                    : (pBaseTexture != nullptr ? static_cast<float>(pBaseTexture->width) : 0.0f),
                pLayout->height > 0.0f
                    ? pLayout->height
                    : (pBaseTexture != nullptr ? static_cast<float>(pBaseTexture->height) : 0.0f));

            if (!resolved)
            {
                return;
            }

            const bool isHovered =
                pLayout->interactive
                && dialogMouseX >= resolved->x
                && dialogMouseX < resolved->x + resolved->width
                && dialogMouseY >= resolved->y
                && dialogMouseY < resolved->y + resolved->height;
            const bool isPressed =
                isHovered && (SDL_GetMouseState(nullptr, nullptr) & SDL_BUTTON_LMASK) != 0;
            const std::string *pAssetName = &pLayout->primaryAsset;

            if (isPressed && !pLayout->pressedAsset.empty())
            {
                pAssetName = &pLayout->pressedAsset;
            }
            else if (isHovered && !pLayout->hoverAsset.empty())
            {
                pAssetName = &pLayout->hoverAsset;
            }

            if (pAssetName->empty())
            {
                return;
            }

            const HudTextureHandle *pTexture = ensureHudTextureLoaded(*pAssetName);

            if (pTexture == nullptr)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;

            if (bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
            TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {resolved->x, resolved->y, 0.0f, 0.0f, 0.0f};
            pVertices[1] = {resolved->x + resolved->width, resolved->y, 0.0f, 1.0f, 0.0f};
            pVertices[2] = {resolved->x + resolved->width, resolved->y + resolved->height, 0.0f, 1.0f, 1.0f};
            pVertices[3] = {resolved->x, resolved->y, 0.0f, 0.0f, 0.0f};
            pVertices[4] = {resolved->x + resolved->width, resolved->y + resolved->height, 0.0f, 1.0f, 1.0f};
            pVertices[5] = {resolved->x, resolved->y + resolved->height, 0.0f, 0.0f, 1.0f};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, m_terrainTextureSamplerHandle, pTexture->textureHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
        };

    const std::vector<std::string> orderedDialogueLayoutIds = sortedHudLayoutIdsForScreen("Dialogue");

    for (const std::string &layoutId : orderedDialogueLayoutIds)
    {
        const HudLayoutElement *pLayout = findHudLayoutElement(layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != "dialogue")
        {
            continue;
        }

        renderDialogueTextureElement(layoutId);
    }

    const auto renderDialogueLabelById =
        [this, width, height, &shouldRenderInCurrentPass](const std::string &layoutId, const std::string &label)
        {
            const HudLayoutElement *pLayout = findHudLayoutElement(layoutId);

            if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->screen) != "dialogue")
            {
                return;
            }

            if (!shouldRenderInCurrentPass(pLayout->zIndex))
            {
                return;
            }

            const std::optional<ResolvedHudLayoutElement> resolved = resolveHudLayoutElement(
                layoutId,
                width,
                height,
                pLayout->width,
                pLayout->height);

            if (!resolved)
            {
                return;
            }

            renderLayoutLabel(*pLayout, *resolved, label);
        };

    renderDialogueLabelById(
        "DialogueGoodbyeButton",
        "Close");
    renderDialogueLabelById(
        "DialogueResponseHint",
        m_activeEventDialog.actions.empty()
            ? "Enter/Space/E/Esc close"
            : "Up/Down select  Enter/Space accept  E/Esc close");

    const HudLayoutElement *pEventDialogLayout = findHudLayoutElement("DialogueEventDialog");
    const HudLayoutElement *pNpcPortraitLayout = findHudLayoutElement("DialogueNpcPortrait");
    const HudLayoutElement *pHouseTitleLayout = findHudLayoutElement("DialogueHouseTitle");
    const HudLayoutElement *pNpcNameLayout = findHudLayoutElement("DialogueNpcName");
    const HudLayoutElement *pTopicRowLayout = findHudLayoutElement("DialogueTopicRow_1");

    if (showEventDialogPanel && pEventDialogLayout != nullptr)
    {
        const std::optional<ResolvedHudLayoutElement> resolvedEventDialog = resolveHudLayoutElement(
            "DialogueEventDialog",
            width,
            height,
            pEventDialogLayout->width,
            pEventDialogLayout->height);

        if (resolvedEventDialog && shouldRenderInCurrentPass(pEventDialogLayout->zIndex))
        {
            const float panelScale = resolvedEventDialog->scale;
            const float panelPaddingX = 10.0f * panelScale;
            const float panelPaddingY = 10.0f * panelScale;
            const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
            const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
            const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
            const float portraitInset = 4.0f * panelScale;
            const float sectionGap = 8.0f * panelScale;
            const float houseTitleToPortraitGap = 2.0f * panelScale;
            float contentY = panelInnerY;
            const std::optional<ResolvedHudLayoutElement> resolvedPortraitTemplate =
                pNpcPortraitLayout != nullptr
                ? resolveHudLayoutElement(
                    "DialogueNpcPortrait",
                    width,
                    height,
                    pNpcPortraitLayout->width,
                    pNpcPortraitLayout->height)
                : std::nullopt;
            const std::optional<ResolvedHudLayoutElement> resolvedNpcNameTemplate =
                pNpcNameLayout != nullptr
                ? resolveHudLayoutElement(
                    "DialogueNpcName",
                    width,
                    height,
                    pNpcNameLayout->width,
                    pNpcNameLayout->height)
                : std::nullopt;
            const std::optional<ResolvedHudLayoutElement> resolvedTopicRowTemplate =
                pTopicRowLayout != nullptr
                ? resolveHudLayoutElement(
                    "DialogueTopicRow_1",
                    width,
                    height,
                    pTopicRowLayout->width,
                    pTopicRowLayout->height)
                : std::nullopt;
            const HudLayoutElement *pEffectiveHouseTitleLayout = pHouseTitleLayout != nullptr ? pHouseTitleLayout : pNpcNameLayout;
            const std::optional<ResolvedHudLayoutElement> resolvedHouseTitleTemplate =
                pEffectiveHouseTitleLayout != nullptr
                ? resolveHudLayoutElement(
                    pEffectiveHouseTitleLayout->id,
                    width,
                    height,
                    pEffectiveHouseTitleLayout->width,
                    pEffectiveHouseTitleLayout->height)
                : std::nullopt;
            const float portraitAreaWidth = resolvedPortraitTemplate ? resolvedPortraitTemplate->width : 80.0f * panelScale;
            const float portraitAreaHeight = resolvedPortraitTemplate ? resolvedPortraitTemplate->height : 80.0f * panelScale;
            const float portraitBorderSize = std::min(portraitAreaWidth, portraitAreaHeight);
            const float portraitAreaX = resolvedPortraitTemplate
                ? resolvedPortraitTemplate->x
                : std::round(panelInnerX + (panelInnerWidth - portraitAreaWidth) * 0.5f);
            const float portraitBaseY = resolvedPortraitTemplate ? resolvedPortraitTemplate->y : panelInnerY;
            const float nameWidth = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->width : panelInnerWidth;
            const float nameHeight = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->height : 20.0f * panelScale;
            const float nameX = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->x : panelInnerX;
            const float nameScale = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->scale : panelScale;
            const float nameOffsetY = resolvedNpcNameTemplate && resolvedPortraitTemplate
                ? (resolvedNpcNameTemplate->y - resolvedPortraitTemplate->y)
                : portraitBorderSize + 2.0f * panelScale;

            if (pHostHouseEntry != nullptr && pEffectiveHouseTitleLayout != nullptr)
            {
                ResolvedHudLayoutElement resolvedHouseTitle = {};
                resolvedHouseTitle.x = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->x : panelInnerX;
                resolvedHouseTitle.y = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->y : contentY;
                resolvedHouseTitle.width = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->width : panelInnerWidth;
                resolvedHouseTitle.height = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->height : 20.0f * panelScale;
                resolvedHouseTitle.scale = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->scale : panelScale;

                if (shouldRenderInCurrentPass(pEffectiveHouseTitleLayout->zIndex))
                {
                    const std::string &houseTitle = !m_activeEventDialog.houseTitle.empty()
                        ? m_activeEventDialog.houseTitle
                        : pHostHouseEntry->name;
                    renderLayoutLabel(*pEffectiveHouseTitleLayout, resolvedHouseTitle, houseTitle);
                }

                contentY += resolvedHouseTitle.height + houseTitleToPortraitGap;
            }

            contentY = std::max(contentY, portraitBaseY);

            const auto renderEventNpcPortraitCard =
                [this, pNpcNameLayout, panelScale, portraitBorderSize, portraitInset, panelInnerWidth](
                    float portraitY,
                    const std::string &name,
                    uint32_t pictureId,
                    bool selected) -> float
                {
                    const float portraitX = std::round(
                        panelInnerWidth >= portraitBorderSize
                            ? (panelInnerWidth - portraitBorderSize) * 0.5f
                            : 0.0f);
                    const float absolutePortraitX =
                        std::round((panelInnerWidth >= portraitBorderSize ? portraitX : 0.0f) + 0.0f);
                    BX_UNUSED(absolutePortraitX);
                    return portraitY;
                };
            BX_UNUSED(renderEventNpcPortraitCard);

            auto drawEventNpcCard =
                [this,
                 pNpcNameLayout,
                 nameHeight,
                 nameOffsetY,
                 nameScale,
                 nameWidth,
                 nameX,
                 portraitAreaHeight,
                 portraitAreaWidth,
                 portraitAreaX,
                 portraitBorderSize,
                 portraitInset,
                 &shouldRenderInCurrentPass](
                    float startY,
                    const std::string &name,
                    uint32_t pictureId,
                    bool selected) -> float
                {
                    const float portraitY = std::round(startY);
                    const float portraitX = std::round(portraitAreaX + (portraitAreaWidth - portraitBorderSize) * 0.5f);
                    const float portraitBorderY =
                        std::round(portraitY + (portraitAreaHeight - portraitBorderSize) * 0.5f);
                    const HudTextureHandle *pPortraitBorder = ensureHudTextureLoaded("evtnpc");

                    if (pPortraitBorder != nullptr)
                    {
                        bgfx::TransientVertexBuffer transientVertexBuffer;

                        if (bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) >= 6)
                        {
                            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
                            TexturedTerrainVertex *pVertices =
                                reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
                            pVertices[0] = {portraitX, portraitBorderY, 0.0f, 0.0f, 0.0f};
                            pVertices[1] = {portraitX + portraitBorderSize, portraitBorderY, 0.0f, 1.0f, 0.0f};
                            pVertices[2] = {
                                portraitX + portraitBorderSize,
                                portraitBorderY + portraitBorderSize,
                                0.0f,
                                1.0f,
                                1.0f};
                            pVertices[3] = {portraitX, portraitBorderY, 0.0f, 0.0f, 0.0f};
                            pVertices[4] = {
                                portraitX + portraitBorderSize,
                                portraitBorderY + portraitBorderSize,
                                0.0f,
                                1.0f,
                                1.0f};
                            pVertices[5] = {portraitX, portraitBorderY + portraitBorderSize, 0.0f, 0.0f, 1.0f};
                            float modelMatrix[16] = {};
                            bx::mtxIdentity(modelMatrix);
                            bgfx::setTransform(modelMatrix);
                            bgfx::setVertexBuffer(0, &transientVertexBuffer);
                            bgfx::setTexture(0, m_terrainTextureSamplerHandle, pPortraitBorder->textureHandle);
                            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
                        }
                    }

                    if (pictureId > 0)
                    {
                        char textureName[16] = {};
                        std::snprintf(textureName, sizeof(textureName), "npc%04u", pictureId);
                        const HudTextureHandle *pPortraitTexture = ensureHudTextureLoaded(textureName);

                        if (pPortraitTexture != nullptr)
                        {
                            const float imageWidth = static_cast<float>(pPortraitTexture->width);
                            const float imageHeight = static_cast<float>(pPortraitTexture->height);
                            const float targetSize = portraitBorderSize - portraitInset * 2.0f;
                            const float portraitScale = std::max(
                                targetSize / std::max(1.0f, imageWidth),
                                targetSize / std::max(1.0f, imageHeight));
                            const float scaledWidth = imageWidth * portraitScale;
                            const float scaledHeight = imageHeight * portraitScale;
                            const float innerX = std::round(portraitX + portraitInset);
                            const float innerY = std::round(portraitBorderY + portraitInset);
                            const float drawWidth = std::round(targetSize);
                            const float drawHeight = std::round(targetSize);
                            float u0 = 0.0f;
                            float v0 = 0.0f;
                            float u1 = 1.0f;
                            float v1 = 1.0f;

                            if (scaledWidth > targetSize)
                            {
                                const float croppedFraction = (scaledWidth - targetSize) / scaledWidth;
                                u0 = croppedFraction * 0.5f;
                                u1 = 1.0f - croppedFraction * 0.5f;
                            }

                            if (scaledHeight > targetSize)
                            {
                                const float croppedFraction = (scaledHeight - targetSize) / scaledHeight;
                                v0 = croppedFraction * 0.5f;
                                v1 = 1.0f - croppedFraction * 0.5f;
                            }

                            bgfx::TransientVertexBuffer transientVertexBuffer;

                            if (bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) >= 6)
                            {
                                bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
                                TexturedTerrainVertex *pVertices =
                                    reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
                                pVertices[0] = {innerX, innerY, 0.0f, u0, v0};
                                pVertices[1] = {innerX + drawWidth, innerY, 0.0f, u1, v0};
                                pVertices[2] = {innerX + drawWidth, innerY + drawHeight, 0.0f, u1, v1};
                                pVertices[3] = {innerX, innerY, 0.0f, u0, v0};
                                pVertices[4] = {innerX + drawWidth, innerY + drawHeight, 0.0f, u1, v1};
                                pVertices[5] = {innerX, innerY + drawHeight, 0.0f, u0, v1};
                                float modelMatrix[16] = {};
                                bx::mtxIdentity(modelMatrix);
                                bgfx::setTransform(modelMatrix);
                                bgfx::setVertexBuffer(0, &transientVertexBuffer);
                                bgfx::setTexture(0, m_terrainTextureSamplerHandle, pPortraitTexture->textureHandle);
                                bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                                bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
                            }
                        }
                    }

                    if (selected)
                    {
                        const HudTextureHandle *pHighlight =
                            ensureSolidHudTextureLoaded("__dialogue_event_npc_highlight__", 0x40ffffaaU);

                        if (pHighlight != nullptr)
                        {
                            bgfx::TransientVertexBuffer transientVertexBuffer;

                            if (bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) >= 6)
                            {
                                bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
                                TexturedTerrainVertex *pVertices =
                                    reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
                                pVertices[0] = {portraitX, portraitBorderY, 0.0f, 0.0f, 0.0f};
                                pVertices[1] = {portraitX + portraitBorderSize, portraitBorderY, 0.0f, 1.0f, 0.0f};
                                pVertices[2] = {
                                    portraitX + portraitBorderSize,
                                    portraitBorderY + portraitBorderSize,
                                    0.0f,
                                    1.0f,
                                    1.0f};
                                pVertices[3] = {portraitX, portraitBorderY, 0.0f, 0.0f, 0.0f};
                                pVertices[4] = {
                                    portraitX + portraitBorderSize,
                                    portraitBorderY + portraitBorderSize,
                                    0.0f,
                                    1.0f,
                                    1.0f};
                                pVertices[5] = {portraitX, portraitBorderY + portraitBorderSize, 0.0f, 0.0f, 1.0f};
                                float modelMatrix[16] = {};
                                bx::mtxIdentity(modelMatrix);
                                bgfx::setTransform(modelMatrix);
                                bgfx::setVertexBuffer(0, &transientVertexBuffer);
                                bgfx::setTexture(0, m_terrainTextureSamplerHandle, pHighlight->textureHandle);
                                bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                                bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
                            }
                        }
                    }

                    float nextY = portraitY + portraitAreaHeight;

                    if (pNpcNameLayout != nullptr && shouldRenderInCurrentPass(pNpcNameLayout->zIndex))
                    {
                        ResolvedHudLayoutElement resolvedName = {};
                        resolvedName.x = nameX;
                        resolvedName.y = portraitY + nameOffsetY;
                        resolvedName.width = nameWidth;
                        resolvedName.height = nameHeight;
                        resolvedName.scale = nameScale;
                        renderLayoutLabel(*pNpcNameLayout, resolvedName, name);
                        nextY = resolvedName.y + resolvedName.height;
                    }

                    return nextY;
                };

            if (isResidentSelectionMode)
            {
                for (size_t actionIndex = 0; actionIndex < m_activeEventDialog.actions.size(); ++actionIndex)
                {
                    const EventDialogAction &action = m_activeEventDialog.actions[actionIndex];
                    const NpcEntry *pNpc = m_npcDialogTable ? m_npcDialogTable->getNpc(action.id) : nullptr;
                    const uint32_t pictureId = pNpc != nullptr ? pNpc->pictureId : 0;
                    contentY = drawEventNpcCard(
                        contentY,
                        action.label,
                        pictureId,
                        false);
                    contentY += sectionGap;
                }
            }
            else
            {
                uint32_t pictureId = m_activeEventDialog.participantPictureId;

                if (pictureId == 0)
                {
                    const NpcEntry *pNpc =
                        m_npcDialogTable ? m_npcDialogTable->getNpc(m_activeEventDialog.sourceId) : nullptr;
                    pictureId = pNpc != nullptr
                        ? pNpc->pictureId
                        : (pHostHouseEntry != nullptr ? pHostHouseEntry->proprietorPictureId : 0);
                }

                contentY = drawEventNpcCard(contentY, m_activeEventDialog.title, pictureId, false);
                contentY += sectionGap;

                if (pTopicRowLayout != nullptr && !m_activeEventDialog.actions.empty())
                {
                    const HudFontHandle *pTopicFont = findHudFont(pTopicRowLayout->fontName);
                    const float topicFontScale = snappedHudFontScale(
                        resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
                    const float topicLineHeight = pTopicFont != nullptr
                        ? static_cast<float>(pTopicFont->fontHeight) * topicFontScale
                        : 20.0f * panelScale;
                    const float topicWrapWidth = 140.0f * (resolvedTopicRowTemplate
                        ? resolvedTopicRowTemplate->scale
                        : panelScale);
                    const float topicTextWidthScaled = std::max(
                        0.0f,
                        std::min(
                            resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth,
                            topicWrapWidth)
                            - std::abs(pTopicRowLayout->textPadX * topicFontScale) * 2.0f
                            - 4.0f * topicFontScale);
                    const float topicTextWidth = std::max(0.0f, topicTextWidthScaled / std::max(1.0f, topicFontScale));
                    const float rowGap = 4.0f * panelScale;
                    const size_t visibleActionCount = std::min<size_t>(m_activeEventDialog.actions.size(), 5);
                    const float availableTop = contentY;
                    const float availableHeight =
                        resolvedEventDialog->y + resolvedEventDialog->height - panelPaddingY - availableTop;
                    std::vector<std::vector<std::string>> wrappedActionLabels;
                    std::vector<float> actionRowHeights;
                    std::vector<float> actionPressHeights;
                    wrappedActionLabels.reserve(visibleActionCount);
                    actionRowHeights.reserve(visibleActionCount);
                    actionPressHeights.reserve(visibleActionCount);

                    for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                    {
                        const EventDialogAction &action = m_activeEventDialog.actions[actionIndex];
                        std::string label = action.label;

                        if (!action.enabled && !action.disabledReason.empty())
                        {
                            label += " [disabled]";
                        }

                        std::vector<std::string> wrappedLines = pTopicFont != nullptr
                            ? wrapHudTextToWidth(*pTopicFont, label, topicTextWidth)
                            : std::vector<std::string>{label};

                        if (wrappedLines.empty())
                        {
                            wrappedLines.push_back(label);
                        }

                        const float minimumRowHeight = resolvedTopicRowTemplate
                            ? resolvedTopicRowTemplate->height
                            : pTopicRowLayout->height * panelScale;
                        const float wrappedRowHeight = static_cast<float>(wrappedLines.size()) * topicLineHeight;
                        wrappedActionLabels.push_back(std::move(wrappedLines));
                        actionRowHeights.push_back(std::max(minimumRowHeight, wrappedRowHeight));
                        actionPressHeights.push_back(wrappedRowHeight);
                    }

                    float totalHeight = 0.0f;

                    for (size_t actionIndex = 0; actionIndex < actionRowHeights.size(); ++actionIndex)
                    {
                        totalHeight += actionRowHeights[actionIndex];

                        if (actionIndex + 1 < actionRowHeights.size())
                        {
                            totalHeight += rowGap;
                        }
                    }

                    const float topicListCenterOffsetY = 8.0f * panelScale;
                    float rowY = availableTop + std::max(0.0f, (availableHeight - totalHeight) * 0.5f)
                        - topicListCenterOffsetY;

                    for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                    {
                        ResolvedHudLayoutElement resolvedRow = {};
                        resolvedRow.x = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->x : panelInnerX;
                        resolvedRow.y = rowY;
                        resolvedRow.width = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth;
                        resolvedRow.height = actionRowHeights[actionIndex];
                        resolvedRow.scale = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale;
                        if (shouldRenderInCurrentPass(pTopicRowLayout->zIndex))
                        {
                            const float pressAreaInsetY = 2.0f * panelScale;
                            const float pressAreaHeight =
                                std::min(
                                    resolvedRow.height,
                                    std::max(topicLineHeight, actionPressHeights[actionIndex]) + pressAreaInsetY * 2.0f);
                            const float pressAreaY = resolvedRow.y + (resolvedRow.height - pressAreaHeight) * 0.5f;
                            const bool isHovered =
                                dialogMouseX >= resolvedRow.x
                                && dialogMouseX < resolvedRow.x + resolvedRow.width
                                && dialogMouseY >= pressAreaY
                                && dialogMouseY < pressAreaY + pressAreaHeight;

                            if (pTopicFont != nullptr)
                            {
                                float lineY = pressAreaY;
                                HudLayoutElement hoveredTopicRowLayout = *pTopicRowLayout;

                                if (isHovered)
                                {
                                    hoveredTopicRowLayout.textColorAbgr = HoveredDialogueTopicTextColorAbgr;
                                }

                                for (const std::string &wrappedLine : wrappedActionLabels[actionIndex])
                                {
                                    ResolvedHudLayoutElement resolvedLine = resolvedRow;
                                    resolvedLine.y = lineY;
                                    resolvedLine.height = topicLineHeight;
                                    renderLayoutLabel(
                                        isHovered ? hoveredTopicRowLayout : *pTopicRowLayout,
                                        resolvedLine,
                                        wrappedLine);
                                    lineY += topicLineHeight;
                                }
                            }
                            else
                            {
                                HudLayoutElement hoveredTopicRowLayout = *pTopicRowLayout;

                                if (isHovered)
                                {
                                    hoveredTopicRowLayout.textColorAbgr = HoveredDialogueTopicTextColorAbgr;
                                }

                                renderLayoutLabel(
                                    isHovered ? hoveredTopicRowLayout : *pTopicRowLayout,
                                    resolvedRow,
                                    m_activeEventDialog.actions[actionIndex].label);
                            }
                        }

                        rowY += actionRowHeights[actionIndex] + rowGap;
                    }
                }
            }
        }
    }

    if (showDialogueTextFrame
        && pDialogueTextLayout != nullptr
        && resolvedText
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue"
        && shouldRenderInCurrentPass(pDialogueTextLayout->zIndex))
    {
        const HudFontHandle *pFont = findHudFont(pDialogueTextLayout->fontName);

        if (pFont != nullptr)
        {
            static constexpr float DialogueTextTopInset = 2.0f;
            static constexpr float DialogueTextRightInset = 6.0f;
            const float fontScale = snappedHudFontScale(resolvedText->scale);
            bgfx::TextureHandle coloredMainTextureHandle =
                ensureHudFontMainTextureColor(*pFont, pDialogueTextLayout->textColorAbgr);
            if (!bgfx::isValid(coloredMainTextureHandle))
            {
                coloredMainTextureHandle = pFont->mainTextureHandle;
            }
            const float lineHeight = static_cast<float>(pFont->fontHeight) * fontScale;
            float textX = resolvedText->x + pDialogueTextLayout->textPadX * fontScale;
            float textY = resolvedText->y + (pDialogueTextLayout->textPadY + DialogueTextTopInset) * fontScale;
            textX = std::round(textX);
            textY = std::round(textY);
            const float textWrapWidth = std::max(
                0.0f,
                (resolvedText->width
                    - std::abs(pDialogueTextLayout->textPadX * fontScale) * 2.0f
                    - DialogueTextRightInset * fontScale)
                    / std::max(1.0f, fontScale));
            const size_t maxVisibleLines = std::max<size_t>(
                1,
                static_cast<size_t>(resolvedText->height / std::max(1.0f, lineHeight)));
            size_t visibleLineIndex = 0;

            for (const std::string &sourceLine : m_activeEventDialog.lines)
            {
                const std::vector<std::string> wrappedLines = wrapHudTextToWidth(
                    *pFont,
                    sourceLine,
                    textWrapWidth);

                for (const std::string &wrappedLine : wrappedLines)
                {
                    if (visibleLineIndex >= maxVisibleLines)
                    {
                        break;
                    }

                    renderHudFontLayer(*pFont, pFont->shadowTextureHandle, wrappedLine, textX, textY, fontScale);
                    renderHudFontLayer(*pFont, coloredMainTextureHandle, wrappedLine, textX, textY, fontScale);
                    textY += lineHeight;
                    ++visibleLineIndex;
                }

                if (visibleLineIndex >= maxVisibleLines)
                {
                    break;
                }
            }
        }
    }

    if (false && isResidentSelectionMode)
    {
        const HudLayoutElement *pPortraitLayout = findHudLayoutElement("DialogueNpcPortrait");

        if (pPortraitLayout != nullptr)
        {
            const std::optional<ResolvedHudLayoutElement> resolvedPortrait = resolveHudLayoutElement(
                "DialogueNpcPortrait",
                width,
                height,
                pPortraitLayout->width,
                pPortraitLayout->height);

            if (resolvedPortrait)
            {
                const float portraitGap = 8.0f * resolvedPortrait->scale;
                const HudLayoutElement *pNameLayout = findHudLayoutElement("DialogueNpcName");

                for (size_t actionIndex = 0; actionIndex < m_activeEventDialog.actions.size(); ++actionIndex)
                {
                    const EventDialogAction &action = m_activeEventDialog.actions[actionIndex];
                    const NpcEntry *pNpc = m_npcDialogTable ? m_npcDialogTable->getNpc(action.id) : nullptr;
                    char textureName[16] = {};

                    if (pNpc != nullptr && pNpc->pictureId > 0)
                    {
                        std::snprintf(textureName, sizeof(textureName), "npc%04u", pNpc->pictureId);
                        const HudTextureHandle *pPortraitTexture = ensureHudTextureLoaded(textureName);

                        if (pPortraitTexture != nullptr)
                        {
                            bgfx::TransientVertexBuffer transientVertexBuffer;

                            if (bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) >= 6)
                            {
                                const float portraitX = resolvedPortrait->x;
                                const float portraitY =
                                    resolvedPortrait->y + static_cast<float>(actionIndex)
                                        * (resolvedPortrait->height + portraitGap);
                                bgfx::allocTransientVertexBuffer(
                                    &transientVertexBuffer,
                                    6,
                                    TexturedTerrainVertex::ms_layout);
                                TexturedTerrainVertex *pVertices =
                                    reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);

                                pVertices[0] = {portraitX, portraitY, 0.0f, 0.0f, 0.0f};
                                pVertices[1] = {portraitX + resolvedPortrait->width, portraitY, 0.0f, 1.0f, 0.0f};
                                pVertices[2] = {
                                    portraitX + resolvedPortrait->width,
                                    portraitY + resolvedPortrait->height,
                                    0.0f,
                                    1.0f,
                                    1.0f};
                                pVertices[3] = {portraitX, portraitY, 0.0f, 0.0f, 0.0f};
                                pVertices[4] = {
                                    portraitX + resolvedPortrait->width,
                                    portraitY + resolvedPortrait->height,
                                    0.0f,
                                    1.0f,
                                    1.0f};
                                pVertices[5] = {portraitX, portraitY + resolvedPortrait->height, 0.0f, 0.0f, 1.0f};

                                float modelMatrix[16] = {};
                                bx::mtxIdentity(modelMatrix);
                                bgfx::setTransform(modelMatrix);
                                bgfx::setVertexBuffer(0, &transientVertexBuffer);
                                bgfx::setTexture(0, m_terrainTextureSamplerHandle, pPortraitTexture->textureHandle);
                                bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                                bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);

                                if (actionIndex == m_eventDialogSelectionIndex)
                                {
                                    const HudTextureHandle *pHighlight =
                                        ensureSolidHudTextureLoaded("__dialogue_resident_highlight__", 0x60ffffaaU);

                                    if (pHighlight != nullptr
                                        && bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) >= 6)
                                    {
                                        bgfx::allocTransientVertexBuffer(
                                            &transientVertexBuffer,
                                            6,
                                            TexturedTerrainVertex::ms_layout);
                                        pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
                                        pVertices[0] = {portraitX, portraitY, 0.0f, 0.0f, 0.0f};
                                        pVertices[1] = {
                                            portraitX + resolvedPortrait->width,
                                            portraitY,
                                            0.0f,
                                            1.0f,
                                            0.0f};
                                        pVertices[2] = {
                                            portraitX + resolvedPortrait->width,
                                            portraitY + resolvedPortrait->height,
                                            0.0f,
                                            1.0f,
                                            1.0f};
                                        pVertices[3] = {portraitX, portraitY, 0.0f, 0.0f, 0.0f};
                                        pVertices[4] = {
                                            portraitX + resolvedPortrait->width,
                                            portraitY + resolvedPortrait->height,
                                            0.0f,
                                            1.0f,
                                            1.0f};
                                        pVertices[5] = {
                                            portraitX,
                                            portraitY + resolvedPortrait->height,
                                            0.0f,
                                            0.0f,
                                            1.0f};
                                        bx::mtxIdentity(modelMatrix);
                                        bgfx::setTransform(modelMatrix);
                                        bgfx::setVertexBuffer(0, &transientVertexBuffer);
                                        bgfx::setTexture(0, m_terrainTextureSamplerHandle, pHighlight->textureHandle);
                                        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                                        bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
                                    }
                                }

                                if (pNameLayout != nullptr)
                                {
                                    ResolvedHudLayoutElement resolvedName = {};
                                    resolvedName.x = portraitX;
                                    resolvedName.y = portraitY + resolvedPortrait->height + 2.0f * resolvedPortrait->scale;
                                    resolvedName.width = resolvedPortrait->width;
                                    resolvedName.height = 22.0f * resolvedPortrait->scale;
                                    resolvedName.scale = resolvedPortrait->scale;
                                    renderLayoutLabel(*pNameLayout, resolvedName, action.label);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    else if (false)
    {
        const HudLayoutElement *pTopicListLayout = findHudLayoutElement("DialogueTopicList");
        const HudLayoutElement *pTopicRowLayout = findHudLayoutElement("DialogueTopicRow_1");

        if (pTopicListLayout != nullptr
            && pTopicRowLayout != nullptr
            && toLowerCopy(pTopicListLayout->screen) == "dialogue"
            && toLowerCopy(pTopicRowLayout->screen) == "dialogue")
        {
            const std::optional<ResolvedHudLayoutElement> resolvedTopicList = resolveHudLayoutElement(
                "DialogueTopicList",
                width,
                height,
                pTopicListLayout->width,
                pTopicListLayout->height);

            if (resolvedTopicList)
            {
                const float rowHeight = pTopicRowLayout->height * resolvedTopicList->scale;
                const float rowGap = 4.0f * resolvedTopicList->scale;
                const size_t visibleActionCount = std::min<size_t>(m_activeEventDialog.actions.size(), 5);
                const float totalHeight = visibleActionCount > 0
                    ? static_cast<float>(visibleActionCount) * rowHeight
                        + static_cast<float>(visibleActionCount - 1) * rowGap
                    : 0.0f;
                float rowY = resolvedTopicList->y + (resolvedTopicList->height - totalHeight) * 0.5f;

                for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                {
                    const EventDialogAction &action = m_activeEventDialog.actions[actionIndex];
                    std::string label = action.label;

                    if (actionIndex == m_eventDialogSelectionIndex)
                    {
                        label = "> " + label;
                    }

                    if (!action.enabled)
                    {
                        label += " [disabled]";
                    }

                    ResolvedHudLayoutElement resolvedRow = {};
                    resolvedRow.x = resolvedTopicList->x;
                    resolvedRow.y = rowY;
                    resolvedRow.width = resolvedTopicList->width;
                    resolvedRow.height = rowHeight;
                    resolvedRow.scale = resolvedTopicList->scale;
                    if (shouldRenderInCurrentPass(pTopicRowLayout->zIndex))
                    {
                        renderLayoutLabel(*pTopicRowLayout, resolvedRow, label);
                    }

                    rowY += rowHeight + rowGap;
                }
            }
        }

        if (pDialogueTextLayout != nullptr
            && resolvedText
            && toLowerCopy(pDialogueTextLayout->screen) == "dialogue"
            && shouldRenderInCurrentPass(pDialogueTextLayout->zIndex))
        {
            const HudFontHandle *pFont = findHudFont(pDialogueTextLayout->fontName);

            if (pFont != nullptr)
            {
                const float fontScale = snappedHudFontScale(resolvedText->scale);
                bgfx::TextureHandle coloredMainTextureHandle =
                    ensureHudFontMainTextureColor(*pFont, pDialogueTextLayout->textColorAbgr);
                if (!bgfx::isValid(coloredMainTextureHandle))
                {
                    coloredMainTextureHandle = pFont->mainTextureHandle;
                }
                const float lineHeight = static_cast<float>(pFont->fontHeight) * fontScale;
                float textX = resolvedText->x + pDialogueTextLayout->textPadX * fontScale;
                float textY = resolvedText->y + pDialogueTextLayout->textPadY * fontScale;
                textX = std::round(textX);
                textY = std::round(textY);
                const size_t maxVisibleLines = std::max<size_t>(
                    1,
                    static_cast<size_t>(resolvedText->height / std::max(1.0f, lineHeight)));

                for (size_t lineIndex = 0;
                     lineIndex < m_activeEventDialog.lines.size() && lineIndex < maxVisibleLines;
                     ++lineIndex)
                {
                    const std::string clampedLine = clampHudTextToWidth(
                        *pFont,
                        m_activeEventDialog.lines[lineIndex],
                        std::max(0.0f, resolvedText->width - std::abs(pDialogueTextLayout->textPadX * fontScale) * 2.0f));
                    renderHudFontLayer(*pFont, pFont->shadowTextureHandle, clampedLine, textX, textY, fontScale);
                    renderHudFontLayer(*pFont, coloredMainTextureHandle, clampedLine, textX, textY, fontScale);
                    textY += lineHeight;
                }
            }
        }
    }

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

uint32_t OutdoorGameView::colorFromHeight(float normalizedHeight)
{
    BX_UNUSED(normalizedHeight);
    const uint8_t red = 160;
    const uint8_t green = 160;
    const uint8_t blue = 160;
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

uint32_t OutdoorGameView::colorFromBModel()
{
    const uint8_t red = 255;
    const uint8_t green = 255;
    const uint8_t blue = 255;
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

bgfx::ProgramHandle OutdoorGameView::loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

bgfx::ShaderHandle OutdoorGameView::loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr << "Failed to read shader: " << shaderPath << '\n';
        return BGFX_INVALID_HANDLE;
    }

    const bgfx::Memory *pShaderMemory = bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size()));
    return bgfx::createShader(pShaderMemory);
}

bool OutdoorGameView::loadHudLayout(const Engine::AssetFileSystem &assetFileSystem)
{
    m_hudLayoutElements.clear();
    m_hudLayoutOrder.clear();

    const std::array<std::string, 3> layoutFiles = {
        "Data/ui/gameplay.yml",
        "Data/ui/dialogue.yml",
        "Data/ui/character.yml"
    };

    bool loadedAnyLayout = false;

    for (const std::string &layoutFile : layoutFiles)
    {
        const std::optional<std::string> fileContents = assetFileSystem.readTextFile(layoutFile);

        if (!fileContents)
        {
            if (layoutFile == "Data/ui/gameplay.yml")
            {
                return false;
            }

            continue;
        }

        if (!loadHudLayoutFile(assetFileSystem, layoutFile))
        {
            return false;
        }

        loadedAnyLayout = true;
    }

    return loadedAnyLayout;
}

bool OutdoorGameView::loadHudLayoutFile(const Engine::AssetFileSystem &assetFileSystem, const std::string &path)
{
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(path);

    if (!fileContents)
    {
        return false;
    }

    const auto normalizeLayoutToken = [](const std::string &value) -> std::string
    {
        const std::string lowerValue = toLowerCopy(value);
        std::string normalizedValue;

        for (char character : lowerValue)
        {
            if (character != '_' && character != '-' && character != ' ')
            {
                normalizedValue.push_back(character);
            }
        }

        return normalizedValue;
    };

    const auto parseRootAnchor = [&normalizeLayoutToken](const std::string &value) -> std::optional<HudLayoutAnchor>
    {
        const std::string normalizedValue = normalizeLayoutToken(value);

        if (normalizedValue == "topleft")
        {
            return HudLayoutAnchor::TopLeft;
        }

        if (normalizedValue == "topcenter")
        {
            return HudLayoutAnchor::TopCenter;
        }

        if (normalizedValue == "topright")
        {
            return HudLayoutAnchor::TopRight;
        }

        if (normalizedValue == "left")
        {
            return HudLayoutAnchor::Left;
        }

        if (normalizedValue == "center")
        {
            return HudLayoutAnchor::Center;
        }

        if (normalizedValue == "right")
        {
            return HudLayoutAnchor::Right;
        }

        if (normalizedValue == "bottomleft")
        {
            return HudLayoutAnchor::BottomLeft;
        }

        if (normalizedValue == "bottomcenter")
        {
            return HudLayoutAnchor::BottomCenter;
        }

        if (normalizedValue == "bottomright")
        {
            return HudLayoutAnchor::BottomRight;
        }

        return std::nullopt;
    };

    const auto parseChildAnchor = [&normalizeLayoutToken](const std::string &value) -> std::optional<HudLayoutAttachMode>
    {
        const std::string normalizedValue = normalizeLayoutToken(value);

        if (normalizedValue.empty() || normalizedValue == "none")
        {
            return HudLayoutAttachMode::None;
        }

        if (normalizedValue == "rightof")
        {
            return HudLayoutAttachMode::RightOf;
        }

        if (normalizedValue == "leftof")
        {
            return HudLayoutAttachMode::LeftOf;
        }

        if (normalizedValue == "right" || normalizedValue == "insideright")
        {
            return HudLayoutAttachMode::InsideRight;
        }

        if (normalizedValue == "left" || normalizedValue == "insideleft")
        {
            return HudLayoutAttachMode::InsideLeft;
        }

        if (normalizedValue == "above")
        {
            return HudLayoutAttachMode::Above;
        }

        if (normalizedValue == "below")
        {
            return HudLayoutAttachMode::Below;
        }

        if (normalizedValue == "centerabove")
        {
            return HudLayoutAttachMode::CenterAbove;
        }

        if (normalizedValue == "centerbelow")
        {
            return HudLayoutAttachMode::CenterBelow;
        }

        if (normalizedValue == "topcenter" || normalizedValue == "insidetopcenter")
        {
            return HudLayoutAttachMode::InsideTopCenter;
        }

        if (normalizedValue == "topleft" || normalizedValue == "insidetopleft")
        {
            return HudLayoutAttachMode::InsideTopLeft;
        }

        if (normalizedValue == "topright" || normalizedValue == "insidetopright")
        {
            return HudLayoutAttachMode::InsideTopRight;
        }

        if (normalizedValue == "bottomleft" || normalizedValue == "insidebottomleft")
        {
            return HudLayoutAttachMode::InsideBottomLeft;
        }

        if (normalizedValue == "bottomcenter" || normalizedValue == "insidebottomcenter")
        {
            return HudLayoutAttachMode::InsideBottomCenter;
        }

        if (normalizedValue == "bottomright" || normalizedValue == "insidebottomright")
        {
            return HudLayoutAttachMode::InsideBottomRight;
        }

        if (normalizedValue == "center" || normalizedValue == "centerin")
        {
            return HudLayoutAttachMode::CenterIn;
        }

        return std::nullopt;
    };

    const auto parseTextAlignX = [&normalizeLayoutToken](const std::string &value) -> std::optional<HudTextAlignX>
    {
        const std::string normalizedValue = normalizeLayoutToken(value);

        if (normalizedValue.empty() || normalizedValue == "left")
        {
            return HudTextAlignX::Left;
        }

        if (normalizedValue == "center")
        {
            return HudTextAlignX::Center;
        }

        if (normalizedValue == "right")
        {
            return HudTextAlignX::Right;
        }

        return std::nullopt;
    };

    const auto parseTextAlignY = [&normalizeLayoutToken](const std::string &value) -> std::optional<HudTextAlignY>
    {
        const std::string normalizedValue = normalizeLayoutToken(value);

        if (normalizedValue.empty() || normalizedValue == "top")
        {
            return HudTextAlignY::Top;
        }

        if (normalizedValue == "middle" || normalizedValue == "center")
        {
            return HudTextAlignY::Middle;
        }

        if (normalizedValue == "bottom")
        {
            return HudTextAlignY::Bottom;
        }

        return std::nullopt;
    };

    const auto yamlBoolOrDefault = [](const YAML::Node &node, const char *key, bool defaultValue) -> bool
    {
        const YAML::Node child = node[key];
        return child ? child.as<bool>() : defaultValue;
    };

    const auto yamlFloatOrDefault = [](const YAML::Node &node, const char *key, float defaultValue) -> float
    {
        const YAML::Node child = node[key];
        return child ? child.as<float>() : defaultValue;
    };

    const auto yamlStringOrEmpty = [](const YAML::Node &node, const char *key) -> std::string
    {
        const YAML::Node child = node[key];
        return child ? child.as<std::string>() : "";
    };

    try
    {
        const YAML::Node root = YAML::Load(*fileContents);

        if (!root.IsMap())
        {
            return false;
        }

        const YAML::Node screenNode = root["screen"];
        const YAML::Node elementsNode = root["elements"];

        if (!screenNode || !screenNode.IsScalar() || !elementsNode || !elementsNode.IsSequence())
        {
            return false;
        }

        const std::string screen = screenNode.as<std::string>();
        std::function<bool(const YAML::Node &, const std::string &)> appendElement;

        appendElement =
            [&](const YAML::Node &node, const std::string &parentId) -> bool
            {
                if (!node.IsMap())
                {
                    return false;
                }

                const YAML::Node idNode = node["id"];
                const YAML::Node anchorNode = node["anchor"];

                if (!idNode || !idNode.IsScalar() || !anchorNode || !anchorNode.IsScalar())
                {
                    return false;
                }

                HudLayoutElement element = {};
                element.id = idNode.as<std::string>();
                element.screen = screen;
                element.parentId = parentId;
                element.zIndex = defaultHudLayoutZIndexForScreen(screen);

                if (parentId.empty())
                {
                    const std::optional<HudLayoutAnchor> anchor = parseRootAnchor(anchorNode.as<std::string>());

                    if (!anchor)
                    {
                        return false;
                    }

                    element.anchor = *anchor;
                    element.offsetX = yamlFloatOrDefault(node, "offset_x", 0.0f);
                    element.offsetY = yamlFloatOrDefault(node, "offset_y", 0.0f);
                }
                else
                {
                    const HudLayoutElement *pParent = findHudLayoutElement(parentId);

                    if (pParent != nullptr)
                    {
                        element.zIndex = pParent->zIndex;
                    }

                    const std::optional<HudLayoutAttachMode> attachTo = parseChildAnchor(anchorNode.as<std::string>());

                    if (!attachTo)
                    {
                        return false;
                    }

                    element.attachTo = *attachTo;
                    element.gapX = yamlFloatOrDefault(node, "offset_x", 0.0f);
                    element.gapY = yamlFloatOrDefault(node, "offset_y", 0.0f);
                }

                const YAML::Node zIndexNode = node["z_index"];

                if (zIndexNode && zIndexNode.IsScalar())
                {
                    element.zIndex = zIndexNode.as<int>();
                }

                element.width = yamlFloatOrDefault(node, "width", 0.0f);
                element.height = yamlFloatOrDefault(node, "height", 0.0f);
                element.bottomToId = yamlStringOrEmpty(node, "bottom_to");
                element.bottomGap = yamlFloatOrDefault(node, "bottom_gap", 0.0f);
                element.visible = yamlBoolOrDefault(node, "visible", true);
                element.interactive = yamlBoolOrDefault(node, "interactive", false);
                element.notes = yamlStringOrEmpty(node, "notes");

                const YAML::Node scaleNode = node["scale"];

                if (scaleNode && scaleNode.IsMap())
                {
                    element.hasExplicitScale = true;
                    element.minScale = yamlFloatOrDefault(scaleNode, "min", 1.0f);
                    element.maxScale = yamlFloatOrDefault(scaleNode, "max", element.minScale);
                }

                const YAML::Node assetNode = node["asset"];

                if (assetNode)
                {
                    if (assetNode.IsScalar())
                    {
                        element.primaryAsset = assetNode.as<std::string>();
                    }
                    else if (assetNode.IsMap())
                    {
                        element.primaryAsset = yamlStringOrEmpty(assetNode, "default");
                        element.hoverAsset = yamlStringOrEmpty(assetNode, "highlighted");

                        if (element.hoverAsset.empty())
                        {
                            element.hoverAsset = yamlStringOrEmpty(assetNode, "hover");
                        }

                        element.pressedAsset = yamlStringOrEmpty(assetNode, "pressed");
                        element.secondaryAsset = yamlStringOrEmpty(assetNode, "selected");

                        element.tertiaryAsset = yamlStringOrEmpty(assetNode, "frame");
                        element.quaternaryAsset = yamlStringOrEmpty(assetNode, "health_bar");
                        element.quinaryAsset = yamlStringOrEmpty(assetNode, "mana_bar");
                    }
                }

                const YAML::Node textNode = node["text"];

                if (textNode && textNode.IsMap())
                {
                    element.fontName = yamlStringOrEmpty(textNode, "font");
                    element.labelText = yamlStringOrEmpty(textNode, "value");
                    const std::string textColor = yamlStringOrEmpty(textNode, "color");

                    const std::optional<HudTextAlignX> textAlignX =
                        parseTextAlignX(yamlStringOrEmpty(textNode, "align_x"));
                    const std::optional<HudTextAlignY> textAlignY =
                        parseTextAlignY(yamlStringOrEmpty(textNode, "align_y"));

                    if (!textAlignX || !textAlignY)
                    {
                        return false;
                    }

                    element.textAlignX = *textAlignX;
                    element.textAlignY = *textAlignY;
                    element.textPadX = yamlFloatOrDefault(textNode, "pad_x", 0.0f);
                    element.textPadY = yamlFloatOrDefault(textNode, "pad_y", 0.0f);

                    if (!textColor.empty())
                    {
                        const std::string normalizedTextColor = normalizeLayoutToken(textColor);
                        std::string hexTextColor = toLowerCopy(textColor);

                        hexTextColor.erase(
                            std::remove_if(
                                hexTextColor.begin(),
                                hexTextColor.end(),
                                [](char character)
                                {
                                    return character == ' ' || character == '\t';
                                }),
                            hexTextColor.end());

                        if (normalizedTextColor == "white")
                        {
                            element.textColorAbgr = makeAbgrColor(255, 255, 255);
                        }
                        else if (normalizedTextColor == "easternblue")
                        {
                            element.textColorAbgr = makeAbgrColor(21, 153, 233);
                        }
                        else if (hexTextColor.size() == 6
                                 || (hexTextColor.size() == 7 && hexTextColor[0] == '#'))
                        {
                            std::string hex = hexTextColor;

                            if (!hex.empty() && hex[0] == '#')
                            {
                                hex.erase(hex.begin());
                            }

                            if (hex.size() == 6)
                            {
                                const uint32_t rgb = static_cast<uint32_t>(std::strtoul(hex.c_str(), nullptr, 16));
                                element.textColorAbgr = makeAbgrColor(
                                    static_cast<uint8_t>((rgb >> 16) & 0xff),
                                    static_cast<uint8_t>((rgb >> 8) & 0xff),
                                    static_cast<uint8_t>(rgb & 0xff));
                            }
                            else
                            {
                                return false;
                            }
                        }
                        else
                        {
                            return false;
                        }
                    }
                }

                m_hudLayoutOrder.push_back(element.id);
                m_hudLayoutElements[toLowerCopy(element.id)] = element;

                const YAML::Node childrenNode = node["children"];

                if (childrenNode)
                {
                    if (!childrenNode.IsSequence())
                    {
                        return false;
                    }

                    for (const YAML::Node &childNode : childrenNode)
                    {
                        if (!appendElement(childNode, element.id))
                        {
                            return false;
                        }
                    }
                }

                return true;
            };

        for (const YAML::Node &elementNode : elementsNode)
        {
            if (!appendElement(elementNode, ""))
            {
                std::cerr << "HUD layout YAML parse failed in " << path << '\n';
                return false;
            }
        }

        return true;
    }
    catch (const YAML::Exception &exception)
    {
        std::cerr << "HUD layout YAML exception in " << path << ": " << exception.what() << '\n';
        return false;
    }
}

const OutdoorGameView::HudLayoutElement *OutdoorGameView::findHudLayoutElement(const std::string &layoutId) const
{
    const auto iterator = m_hudLayoutElements.find(toLowerCopy(layoutId));

    if (iterator == m_hudLayoutElements.end())
    {
        return nullptr;
    }

    return &iterator->second;
}

std::vector<std::string> OutdoorGameView::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    std::vector<std::string> result;
    const std::string normalizedScreen = toLowerCopy(screen);

    for (const std::string &layoutId : m_hudLayoutOrder)
    {
        const HudLayoutElement *pLayout = findHudLayoutElement(layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != normalizedScreen)
        {
            continue;
        }

        result.push_back(layoutId);
    }

    std::stable_sort(
        result.begin(),
        result.end(),
        [this](const std::string &leftId, const std::string &rightId)
        {
            const HudLayoutElement *pLeft = findHudLayoutElement(leftId);
            const HudLayoutElement *pRight = findHudLayoutElement(rightId);

            if (pLeft == nullptr || pRight == nullptr)
            {
                return false;
            }

            return pLeft->zIndex < pRight->zIndex;
        });

    return result;
}

int OutdoorGameView::maxHudLayoutZIndexForScreen(const std::string &screen) const
{
    int maxZIndex = defaultHudLayoutZIndexForScreen(screen);
    const std::string normalizedScreen = toLowerCopy(screen);

    for (const auto &[id, element] : m_hudLayoutElements)
    {
        BX_UNUSED(id);

        if (toLowerCopy(element.screen) == normalizedScreen)
        {
            maxZIndex = std::max(maxZIndex, element.zIndex);
        }
    }

    return maxZIndex;
}

int OutdoorGameView::defaultHudLayoutZIndexForScreen(const std::string &screen)
{
    if (toLowerCopy(screen) == "outdoorhud")
    {
        return 100;
    }

    return 0;
}

const OutdoorGameView::HudFontHandle *OutdoorGameView::findHudFont(const std::string &fontName) const
{
    const std::string normalizedFontName = toLowerCopy(fontName);

    for (const HudFontHandle &fontHandle : m_hudFontHandles)
    {
        if (fontHandle.fontName == normalizedFontName)
        {
            return &fontHandle;
        }
    }

    return nullptr;
}

float OutdoorGameView::measureHudTextWidth(const HudFontHandle &font, const std::string &text) const
{
    float widthPixels = 0.0f;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character < font.firstChar || character > font.lastChar)
        {
            widthPixels += static_cast<float>(font.atlasCellWidth);
            continue;
        }

        const HudFontGlyphMetrics &glyphMetrics = font.glyphMetrics[character];
        widthPixels += static_cast<float>(
            glyphMetrics.leftSpacing
            + glyphMetrics.width
            + glyphMetrics.rightSpacing);
    }

    return std::max(0.0f, widthPixels);
}

std::string OutdoorGameView::clampHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    std::string clampedText = text;

    while (!clampedText.empty() && measureHudTextWidth(font, clampedText) > maxWidth)
    {
        clampedText.pop_back();
    }

    return clampedText;
}

std::vector<std::string> OutdoorGameView::wrapHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    if (text.empty())
    {
        return {""};
    }

    if (maxWidth <= 0.0f)
    {
        return {text};
    }

    std::vector<std::string> lines;
    std::string currentLine;
    std::string currentWord;

    const auto flushLine = [&]()
    {
        lines.push_back(currentLine);
        currentLine.clear();
    };

    const auto appendWord = [&](const std::string &word)
    {
        if (word.empty())
        {
            return;
        }

        if (currentLine.empty())
        {
            currentLine = word;
            return;
        }

        const std::string candidate = currentLine + " " + word;

        if (measureHudTextWidth(font, candidate) <= maxWidth)
        {
            currentLine = candidate;
        }
        else
        {
            flushLine();
            currentLine = word;
        }
    };

    for (char character : text)
    {
        if (character == '\r')
        {
            continue;
        }

        if (character == '\n')
        {
            appendWord(currentWord);
            currentWord.clear();
            flushLine();
            continue;
        }

        if (character == ' ')
        {
            appendWord(currentWord);
            currentWord.clear();
            continue;
        }

        currentWord.push_back(character);
    }

    appendWord(currentWord);

    if (!currentLine.empty() || lines.empty())
    {
        lines.push_back(currentLine);
    }

    return lines;
}

void OutdoorGameView::renderHudFontLayer(
    const HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    uint32_t glyphCount = 0;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character >= font.firstChar
            && character <= font.lastChar
            && font.glyphMetrics[character].width > 0)
        {
            ++glyphCount;
        }
    }

    if (glyphCount == 0)
    {
        return;
    }

    const uint32_t vertexCount = glyphCount * 6;

    if (bgfx::getAvailTransientVertexBuffer(vertexCount, TexturedTerrainVertex::ms_layout) < vertexCount)
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer;
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, vertexCount, TexturedTerrainVertex::ms_layout);
    TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);
    float penX = textX;
    uint32_t vertexIndex = 0;

    for (unsigned char character : text)
    {
        if (character == '\r' || character == '\n')
        {
            break;
        }

        if (character < font.firstChar || character > font.lastChar)
        {
            penX += static_cast<float>(font.atlasCellWidth) * fontScale;
            continue;
        }

        const HudFontGlyphMetrics &glyphMetrics = font.glyphMetrics[character];
        penX += static_cast<float>(glyphMetrics.leftSpacing) * fontScale;

        if (glyphMetrics.width > 0)
        {
            const int cellX = (character % 16) * font.atlasCellWidth;
            const int cellY = (character / 16) * font.fontHeight;
            const float u0 = static_cast<float>(cellX) / static_cast<float>(font.atlasWidth);
            const float v0 = static_cast<float>(cellY) / static_cast<float>(font.atlasHeight);
            const float u1 = static_cast<float>(cellX + glyphMetrics.width) / static_cast<float>(font.atlasWidth);
            const float v1 = static_cast<float>(cellY + font.fontHeight) / static_cast<float>(font.atlasHeight);
            const float glyphWidth = static_cast<float>(glyphMetrics.width) * fontScale;
            const float glyphHeight = static_cast<float>(font.fontHeight) * fontScale;

            pVertices[vertexIndex + 0] = {penX, textY, 0.0f, u0, v0};
            pVertices[vertexIndex + 1] = {penX + glyphWidth, textY, 0.0f, u1, v0};
            pVertices[vertexIndex + 2] = {penX + glyphWidth, textY + glyphHeight, 0.0f, u1, v1};
            pVertices[vertexIndex + 3] = {penX, textY, 0.0f, u0, v0};
            pVertices[vertexIndex + 4] = {penX + glyphWidth, textY + glyphHeight, 0.0f, u1, v1};
            pVertices[vertexIndex + 5] = {penX, textY + glyphHeight, 0.0f, u0, v1};
            vertexIndex += 6;
        }

        penX += static_cast<float>(glyphMetrics.width + glyphMetrics.rightSpacing) * fontScale;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer);
    bgfx::setTexture(0, m_terrainTextureSamplerHandle, textureHandle);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
}

bgfx::TextureHandle OutdoorGameView::ensureHudFontMainTextureColor(
    const HudFontHandle &font,
    uint32_t colorAbgr) const
{
    if (colorAbgr == 0xffffffffu)
    {
        return font.mainTextureHandle;
    }

    for (const HudFontColorTextureHandle &textureHandle : m_hudFontColorTextureHandles)
    {
        if (textureHandle.fontName == font.fontName && textureHandle.colorAbgr == colorAbgr)
        {
            return textureHandle.textureHandle;
        }
    }

    if (font.mainAtlasPixels.empty() || font.atlasWidth <= 0 || font.atlasHeight <= 0)
    {
        return BGFX_INVALID_HANDLE;
    }

    std::vector<uint8_t> tintedPixels = font.mainAtlasPixels;
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xff);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xff);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xff);

    for (size_t pixelIndex = 0; pixelIndex + 3 < tintedPixels.size(); pixelIndex += 4)
    {
        if (tintedPixels[pixelIndex + 3] == 0)
        {
            continue;
        }

        tintedPixels[pixelIndex + 0] = blue;
        tintedPixels[pixelIndex + 1] = green;
        tintedPixels[pixelIndex + 2] = red;
    }

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(font.atlasWidth),
        static_cast<uint16_t>(font.atlasHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(tintedPixels.data(), static_cast<uint32_t>(tintedPixels.size()))
    );

    if (!bgfx::isValid(textureHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    HudFontColorTextureHandle tintedTextureHandle = {};
    tintedTextureHandle.fontName = font.fontName;
    tintedTextureHandle.colorAbgr = colorAbgr;
    tintedTextureHandle.textureHandle = textureHandle;
    m_hudFontColorTextureHandles.push_back(std::move(tintedTextureHandle));
    return m_hudFontColorTextureHandles.back().textureHandle;
}

void OutdoorGameView::renderLayoutLabel(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    const std::string &label) const
{
    if (label.empty())
    {
        return;
    }

    const HudFontHandle *pFont = findHudFont(layout.fontName);

    if (pFont == nullptr)
    {
        static std::unordered_set<std::string> missingFontLogs;
        const std::string logKey = "missing-font:" + toLowerCopy(layout.id) + ":" + toLowerCopy(layout.fontName);

        if (!missingFontLogs.contains(logKey))
        {
            std::cout << "HUD label skipped: id=" << layout.id
                      << " font=\"" << layout.fontName
                      << "\" reason=missing-font label=\"" << label << "\"\n";
            missingFontLogs.insert(logKey);
        }
        return;
    }

    const float fontScale = snappedHudFontScale(resolved.scale);
    const float labelHeightPixels = static_cast<float>(pFont->fontHeight) * fontScale;
    const float maxLabelWidth = std::max(0.0f, resolved.width - std::abs(layout.textPadX * fontScale) * 2.0f);
    std::string clampedLabel = clampHudTextToWidth(
        *pFont,
        label,
        maxLabelWidth);

    if (clampedLabel.empty())
    {
        const HudFontHandle *pFallbackFont = findHudFont("Lucida");

        if (pFallbackFont != nullptr)
        {
            pFont = pFallbackFont;
            clampedLabel = clampHudTextToWidth(*pFont, label, maxLabelWidth);
        }

        static std::unordered_set<std::string> emptyClampLogs;
        const std::string logKey = "empty-clamp:" + toLowerCopy(layout.id) + ":" + label;

        if (!emptyClampLogs.contains(logKey))
        {
            std::cout << "HUD label clamp empty: id=" << layout.id
                      << " font=\"" << layout.fontName
                      << "\" fallback_font=\"" << (pFallbackFont != nullptr ? pFallbackFont->fontName : "")
                      << "\" label=\"" << label
                      << "\" width=" << resolved.width
                      << " max_width=" << maxLabelWidth
                      << " scale=" << resolved.scale << '\n';
            emptyClampLogs.insert(logKey);
        }
    }

    if (clampedLabel.empty())
    {
        clampedLabel = label;
    }

    const float labelWidthPixels = measureHudTextWidth(*pFont, clampedLabel) * fontScale;
    float textX = resolved.x + layout.textPadX * resolved.scale;
    float textY = resolved.y + layout.textPadY * resolved.scale;

    switch (layout.textAlignX)
    {
        case HudTextAlignX::Left:
            break;

        case HudTextAlignX::Center:
            textX = resolved.x + (resolved.width - labelWidthPixels) * 0.5f + layout.textPadX * resolved.scale;
            break;

        case HudTextAlignX::Right:
            textX = resolved.x + resolved.width - labelWidthPixels + layout.textPadX * resolved.scale;
            break;
    }

    switch (layout.textAlignY)
    {
        case HudTextAlignY::Top:
            break;

        case HudTextAlignY::Middle:
            textY = resolved.y + (resolved.height - labelHeightPixels) * 0.5f + layout.textPadY * resolved.scale;
            break;

        case HudTextAlignY::Bottom:
            textY = resolved.y + resolved.height - labelHeightPixels + layout.textPadY * resolved.scale;
            break;
    }

    textX = std::round(textX);
    textY = std::round(textY);

    bgfx::TextureHandle coloredMainTextureHandle = ensureHudFontMainTextureColor(*pFont, layout.textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pFont->mainTextureHandle;
    }

    renderHudFontLayer(*pFont, pFont->shadowTextureHandle, clampedLabel, textX, textY, fontScale);
    renderHudFontLayer(*pFont, coloredMainTextureHandle, clampedLabel, textX, textY, fontScale);
}

const OutdoorGameView::HudTextureHandle *OutdoorGameView::ensureHudTextureLoaded(const std::string &textureName)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const HudTextureHandle *pTexture = findHudTexture(textureName);

    if (pTexture != nullptr)
    {
        return pTexture;
    }

    if (m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }

    if (!loadHudTexture(*m_pAssetFileSystem, textureName))
    {
        return nullptr;
    }

    return findHudTexture(textureName);
}

const OutdoorGameView::HudTextureHandle *OutdoorGameView::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const HudTextureHandle *pTexture = findHudTexture(textureName);

    if (pTexture != nullptr)
    {
        return pTexture;
    }

    const std::array<uint8_t, 4> pixel = {
        static_cast<uint8_t>(abgrColor & 0xff),
        static_cast<uint8_t>((abgrColor >> 8) & 0xff),
        static_cast<uint8_t>((abgrColor >> 16) & 0xff),
        static_cast<uint8_t>((abgrColor >> 24) & 0xff)
    };

    HudTextureHandle textureHandle = {};
    textureHandle.textureName = toLowerCopy(textureName);
    textureHandle.width = 1;
    textureHandle.height = 1;
    textureHandle.textureHandle = bgfx::createTexture2D(
        1,
        1,
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixel.data(), static_cast<uint32_t>(pixel.size()))
    );

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return nullptr;
    }

    m_hudTextureHandles.push_back(std::move(textureHandle));
    return &m_hudTextureHandles.back();
}

bool OutdoorGameView::loadHudFont(const Engine::AssetFileSystem &assetFileSystem, const std::string &fontName)
{
    if (fontName.empty() || findHudFont(fontName) != nullptr)
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

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    std::unordered_set<std::string> visited;
    return resolveHudLayoutElementRecursive(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight, visited);
}

std::optional<OutdoorGameView::ResolvedHudLayoutElement> OutdoorGameView::resolveHudLayoutElementRecursive(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight,
    std::unordered_set<std::string> &visited) const
{
    const std::string normalizedLayoutId = toLowerCopy(layoutId);

    if (visited.contains(normalizedLayoutId))
    {
        std::cerr << "HUD layout cycle detected at element: " << layoutId << '\n';
        return std::nullopt;
    }

    visited.insert(normalizedLayoutId);
    const auto iterator = m_hudLayoutElements.find(toLowerCopy(layoutId));

    if (iterator == m_hudLayoutElements.end())
    {
        return std::nullopt;
    }

    const HudLayoutElement &element = iterator->second;
    const UiViewportRect uiViewport = computeUiViewportRect(screenWidth, screenHeight);
    const float baseScale = std::min(
        uiViewport.width / HudReferenceWidth,
        uiViewport.height / HudReferenceHeight);
    const auto runtimeHeightOverrideIterator = m_hudLayoutRuntimeHeightOverrides.find(normalizedLayoutId);
    const float effectiveHeight = runtimeHeightOverrideIterator != m_hudLayoutRuntimeHeightOverrides.end()
        ? runtimeHeightOverrideIterator->second
        : (element.height > 0.0f ? element.height : fallbackHeight);

    if (normalizedLayoutId == "dialogueframe")
    {
        static float lastLoggedResolvedDialogueFrameHeight = -1.0f;

        if (std::abs(lastLoggedResolvedDialogueFrameHeight - effectiveHeight) > 0.5f)
        {
            std::cout
                << "DialogueFrame resolved height debug: effective_height=" << effectiveHeight
                << " yml_height=" << element.height
                << " has_runtime_override=" << (runtimeHeightOverrideIterator != m_hudLayoutRuntimeHeightOverrides.end() ? 1 : 0)
                << " fallback_height=" << fallbackHeight
                << '\n';
            lastLoggedResolvedDialogueFrameHeight = effectiveHeight;
        }
    }

    ResolvedHudLayoutElement resolved = {};

    if (!element.parentId.empty() && element.attachTo != HudLayoutAttachMode::None)
    {
        const HudLayoutElement *pParent = findHudLayoutElement(element.parentId);

        if (pParent == nullptr)
        {
            return std::nullopt;
        }

        const std::optional<ResolvedHudLayoutElement> parent = resolveHudLayoutElementRecursive(
            element.parentId,
            screenWidth,
            screenHeight,
            pParent->width,
            pParent->height,
            visited);

        if (!parent)
        {
            return std::nullopt;
        }

        resolved.scale = element.hasExplicitScale
            ? std::clamp(baseScale, element.minScale, element.maxScale)
            : parent->scale;
        resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
        resolved.height = effectiveHeight * resolved.scale;

        switch (element.attachTo)
        {
            case HudLayoutAttachMode::None:
                break;

            case HudLayoutAttachMode::RightOf:
                resolved.x = parent->x + parent->width + element.gapX * resolved.scale;
                resolved.y = parent->y + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::LeftOf:
                resolved.x = parent->x - resolved.width + element.gapX * resolved.scale;
                resolved.y = parent->y + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::Above:
                resolved.x = parent->x + element.gapX * resolved.scale;
                resolved.y = parent->y - resolved.height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::Below:
                resolved.x = parent->x + element.gapX * resolved.scale;
                resolved.y = parent->y + parent->height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::CenterAbove:
                resolved.x = parent->x + (parent->width - resolved.width) * 0.5f + element.gapX * resolved.scale;
                resolved.y = parent->y - resolved.height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::CenterBelow:
                resolved.x = parent->x + (parent->width - resolved.width) * 0.5f + element.gapX * resolved.scale;
                resolved.y = parent->y + parent->height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideLeft:
                resolved.x = parent->x + element.gapX * resolved.scale;
                resolved.y = parent->y + (parent->height - resolved.height) * 0.5f + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideRight:
                resolved.x = parent->x + parent->width - resolved.width + element.gapX * resolved.scale;
                resolved.y = parent->y + (parent->height - resolved.height) * 0.5f + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideTopCenter:
                resolved.x = parent->x + (parent->width - resolved.width) * 0.5f + element.gapX * resolved.scale;
                resolved.y = parent->y + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideTopLeft:
                resolved.x = parent->x + element.gapX * resolved.scale;
                resolved.y = parent->y + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideTopRight:
                resolved.x = parent->x + parent->width - resolved.width + element.gapX * resolved.scale;
                resolved.y = parent->y + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideBottomLeft:
                resolved.x = parent->x + element.gapX * resolved.scale;
                resolved.y = parent->y + parent->height - resolved.height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideBottomCenter:
                resolved.x = parent->x + (parent->width - resolved.width) * 0.5f + element.gapX * resolved.scale;
                resolved.y = parent->y + parent->height - resolved.height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::InsideBottomRight:
                resolved.x = parent->x + parent->width - resolved.width + element.gapX * resolved.scale;
                resolved.y = parent->y + parent->height - resolved.height + element.gapY * resolved.scale;
                break;

            case HudLayoutAttachMode::CenterIn:
                resolved.x = parent->x + (parent->width - resolved.width) * 0.5f + element.gapX * resolved.scale;
                resolved.y = parent->y + (parent->height - resolved.height) * 0.5f + element.gapY * resolved.scale;
                break;
        }

        if (!element.bottomToId.empty())
        {
            const HudLayoutElement *pBottomTo = findHudLayoutElement(element.bottomToId);

            if (pBottomTo != nullptr)
            {
                const std::optional<ResolvedHudLayoutElement> bottomTo = resolveHudLayoutElementRecursive(
                    element.bottomToId,
                    screenWidth,
                    screenHeight,
                    pBottomTo->width,
                    pBottomTo->height,
                    visited);

                if (bottomTo)
                {
                    resolved.height = std::max(0.0f, bottomTo->y + element.bottomGap * resolved.scale - resolved.y);
                }
            }
        }

        visited.erase(normalizedLayoutId);
        return resolved;
    }

    resolved.scale = std::clamp(baseScale, element.minScale, element.maxScale);
    resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
    resolved.height = effectiveHeight * resolved.scale;

    switch (element.anchor)
    {
        case HudLayoutAnchor::TopLeft:
            resolved.x = uiViewport.x + element.offsetX * resolved.scale;
            resolved.y = uiViewport.y + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::TopCenter:
            resolved.x =
                uiViewport.x + uiViewport.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = uiViewport.y + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::TopRight:
            resolved.x = uiViewport.x + uiViewport.width - resolved.width + element.offsetX * resolved.scale;
            resolved.y = uiViewport.y + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::Left:
            resolved.x = uiViewport.x + element.offsetX * resolved.scale;
            resolved.y =
                uiViewport.y + uiViewport.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::Center:
            resolved.x =
                uiViewport.x + uiViewport.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y =
                uiViewport.y + uiViewport.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::Right:
            resolved.x = uiViewport.x + uiViewport.width - resolved.width + element.offsetX * resolved.scale;
            resolved.y =
                uiViewport.y + uiViewport.height * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::BottomLeft:
            resolved.x = uiViewport.x + element.offsetX * resolved.scale;
            resolved.y = uiViewport.y + uiViewport.height - resolved.height + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::BottomCenter:
            resolved.x =
                uiViewport.x + uiViewport.width * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = uiViewport.y + uiViewport.height - resolved.height + element.offsetY * resolved.scale;
            break;

        case HudLayoutAnchor::BottomRight:
            resolved.x = uiViewport.x + uiViewport.width - resolved.width + element.offsetX * resolved.scale;
            resolved.y = uiViewport.y + uiViewport.height - resolved.height + element.offsetY * resolved.scale;
            break;
    }

    if (!element.bottomToId.empty())
    {
        const HudLayoutElement *pBottomTo = findHudLayoutElement(element.bottomToId);

        if (pBottomTo != nullptr)
        {
            const std::optional<ResolvedHudLayoutElement> bottomTo = resolveHudLayoutElementRecursive(
                element.bottomToId,
                screenWidth,
                screenHeight,
                pBottomTo->width,
                pBottomTo->height,
                visited);

            if (bottomTo)
            {
                resolved.height = std::max(0.0f, bottomTo->y + element.bottomGap * resolved.scale - resolved.y);
            }
        }
    }

    visited.erase(normalizedLayoutId);
    return resolved;
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

const OutdoorGameView::BillboardTextureHandle *OutdoorGameView::ensureSpriteBillboardTexture(
    const std::string &textureName,
    int16_t paletteId)
{
    const BillboardTextureHandle *pExistingTexture = findBillboardTexture(textureName, paletteId);

    if (pExistingTexture != nullptr)
    {
        return pExistingTexture;
    }

    if (m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        loadSpriteBitmapPixelsBgraCached(textureName, paletteId, textureWidth, textureHeight);

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        return nullptr;
    }

    BillboardTextureHandle billboardTexture = {};
    billboardTexture.textureName = toLowerCopy(textureName);
    billboardTexture.paletteId = paletteId;
    billboardTexture.width = textureWidth;
    billboardTexture.height = textureHeight;
    billboardTexture.textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(textureWidth),
        static_cast<uint16_t>(textureHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size()))
    );

    if (!bgfx::isValid(billboardTexture.textureHandle))
    {
        return nullptr;
    }

    m_billboardTextureHandles.push_back(std::move(billboardTexture));
    m_billboardTextureIndexByPalette[paletteId][m_billboardTextureHandles.back().textureName] =
        m_billboardTextureHandles.size() - 1;
    return &m_billboardTextureHandles.back();
}

const OutdoorGameView::HudTextureHandle *OutdoorGameView::findHudTexture(const std::string &textureName) const
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const HudTextureHandle &textureHandle : m_hudTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName)
        {
            return &textureHandle;
        }
    }

    return nullptr;
}

bool OutdoorGameView::loadHudTexture(const Engine::AssetFileSystem &assetFileSystem, const std::string &textureName)
{
    if (findHudTexture(textureName) != nullptr)
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
    textureHandle.width = width;
    textureHandle.height = height;
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
    std::optional<std::string> iconPath = findCachedAssetPath("Data/icons", textureName + ".bmp");

    if (!iconPath)
    {
        iconPath = findCachedAssetPath("Data/EnglishD", textureName + ".bmp");
    }

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

            ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
        }

        if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
        {
            return;
        }

        ++frameIndex;
    }
}

void OutdoorGameView::preloadPendingSpriteFrameWarmupsParallel()
{
    if (m_pendingSpriteFrameWarmups.empty() || m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    std::vector<SpriteTexturePreloadRequest> preloadRequests;
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> requestIndexByPaletteAndName;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> paletteCache;
    const uint64_t preloadStartTickCount = SDL_GetTicksNS();

    auto queueTextureRequest = [&](const std::string &textureName, int16_t paletteId)
    {
        if (textureName.empty() || findBillboardTexture(textureName, paletteId) != nullptr)
        {
            return;
        }

        const std::string normalizedTextureName = toLowerCopy(textureName);

        if (requestIndexByPaletteAndName[paletteId].contains(normalizedTextureName))
        {
            return;
        }

        const std::optional<std::string> spritePath = findCachedAssetPath("Data/sprites", normalizedTextureName + ".bmp");

        if (!spritePath)
        {
            if (DebugSpritePreloadLogging)
            {
                std::cout << "Preload sprite skipped texture=\"" << normalizedTextureName
                          << "\" palette=" << paletteId
                          << " reason=missing_bitmap\n";
            }
            return;
        }

        const std::optional<std::vector<uint8_t>> bitmapBytes = readCachedBinaryFile(*spritePath);

        if (!bitmapBytes || bitmapBytes->empty())
        {
            if (DebugSpritePreloadLogging)
            {
                std::cout << "Preload sprite skipped texture=\"" << normalizedTextureName
                          << "\" palette=" << paletteId
                          << " reason=empty_bitmap\n";
            }
            return;
        }

        SpriteTexturePreloadRequest request = {};
        request.textureName = normalizedTextureName;
        request.paletteId = paletteId;
        request.bitmapBytes = *bitmapBytes;

        if (!paletteCache.contains(paletteId))
        {
            paletteCache[paletteId] = loadCachedActPalette(paletteId);
        }

        request.overridePalette = paletteCache[paletteId];
        requestIndexByPaletteAndName[paletteId][normalizedTextureName] = preloadRequests.size();
        preloadRequests.push_back(std::move(request));
    };

    for (uint16_t spriteFrameIndex : m_pendingSpriteFrameWarmups)
    {
        if (spriteFrameIndex == 0)
        {
            continue;
        }

        size_t frameIndex = spriteFrameIndex;

        while (frameIndex <= std::numeric_limits<uint16_t>::max())
        {
            const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(static_cast<uint16_t>(frameIndex), 0);

            if (pFrame == nullptr)
            {
                break;
            }

            for (int octant = 0; octant < 8; ++octant)
            {
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                queueTextureRequest(resolvedTexture.textureName, pFrame->paletteId);
            }

            if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
            {
                break;
            }

            ++frameIndex;
        }
    }

    if (preloadRequests.empty())
    {
        m_pendingSpriteFrameWarmups.clear();
        m_nextPendingSpriteFrameWarmupIndex = 0;
        return;
    }

    if (DebugSpritePreloadLogging)
    {
        std::cout << "Preloading sprite textures: requests=" << preloadRequests.size()
                  << " workers=" << std::min(PreloadDecodeWorkerCount, preloadRequests.size())
                  << '\n';
    }

    const size_t workerCount = std::min(PreloadDecodeWorkerCount, preloadRequests.size());
    std::vector<std::future<std::vector<DecodedSpriteTexture>>> futures;
    futures.reserve(workerCount);

    for (size_t workerIndex = 0; workerIndex < workerCount; ++workerIndex)
    {
        futures.push_back(std::async(
            std::launch::async,
            [workerIndex, workerCount, &preloadRequests]()
            {
                std::vector<DecodedSpriteTexture> decodedTextures;

                for (size_t requestIndex = workerIndex; requestIndex < preloadRequests.size(); requestIndex += workerCount)
                {
                    const SpriteTexturePreloadRequest &request = preloadRequests[requestIndex];
                    int textureWidth = 0;
                    int textureHeight = 0;
                    const std::optional<std::vector<uint8_t>> pixels = loadSpriteBitmapPixelsBgra(
                        request.bitmapBytes,
                        request.overridePalette,
                        textureWidth,
                        textureHeight
                    );

                    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
                    {
                        continue;
                    }

                    DecodedSpriteTexture decodedTexture = {};
                    decodedTexture.textureName = request.textureName;
                    decodedTexture.paletteId = request.paletteId;
                    decodedTexture.width = textureWidth;
                    decodedTexture.height = textureHeight;
                    decodedTexture.pixels = *pixels;
                    decodedTextures.push_back(std::move(decodedTexture));
                }

                return decodedTextures;
            }
        ));
    }

    std::vector<DecodedSpriteTexture> decodedTextures;

    for (std::future<std::vector<DecodedSpriteTexture>> &future : futures)
    {
        std::vector<DecodedSpriteTexture> workerTextures = future.get();
        decodedTextures.insert(
            decodedTextures.end(),
            std::make_move_iterator(workerTextures.begin()),
            std::make_move_iterator(workerTextures.end()));
    }

    size_t uploadedCount = 0;

    for (DecodedSpriteTexture &decodedTexture : decodedTextures)
    {
        if (findBillboardTexture(decodedTexture.textureName, decodedTexture.paletteId) != nullptr)
        {
            continue;
        }

        BillboardTextureHandle billboardTexture = {};
        billboardTexture.textureName = decodedTexture.textureName;
        billboardTexture.paletteId = decodedTexture.paletteId;
        billboardTexture.width = decodedTexture.width;
        billboardTexture.height = decodedTexture.height;
        billboardTexture.textureHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(decodedTexture.width),
            static_cast<uint16_t>(decodedTexture.height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            bgfx::copy(decodedTexture.pixels.data(), static_cast<uint32_t>(decodedTexture.pixels.size()))
        );

        if (!bgfx::isValid(billboardTexture.textureHandle))
        {
            if (DebugSpritePreloadLogging)
            {
                std::cout << "Preload sprite failed texture=\"" << decodedTexture.textureName
                          << "\" palette=" << decodedTexture.paletteId
                          << " reason=create_texture\n";
            }
            continue;
        }

        if (DebugSpritePreloadLogging)
        {
            std::cout << "Preloaded sprite texture=\"" << decodedTexture.textureName
                      << "\" palette=" << decodedTexture.paletteId
                      << " size=" << decodedTexture.width << "x" << decodedTexture.height
                      << '\n';
        }

        m_billboardTextureHandles.push_back(std::move(billboardTexture));
        m_billboardTextureIndexByPalette[decodedTexture.paletteId][m_billboardTextureHandles.back().textureName] =
            m_billboardTextureHandles.size() - 1;
        ++uploadedCount;
    }

    const uint64_t preloadElapsedNanoseconds = SDL_GetTicksNS() - preloadStartTickCount;
    if (DebugSpritePreloadLogging)
    {
        std::cout << "Sprite preload complete uploaded=" << uploadedCount
                  << " elapsed_ms=" << static_cast<double>(preloadElapsedNanoseconds) / 1000000.0
                  << '\n';
    }

    m_pendingSpriteFrameWarmups.clear();
    m_nextPendingSpriteFrameWarmupIndex = 0;
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

void OutdoorGameView::queueEventSpellBillboardTextureWarmup(const EventIrProgram &eventIrProgram)
{
    if (m_pSpellTable == nullptr || m_pObjectTable == nullptr)
    {
        return;
    }

    auto queueSpellObjectSpriteFrame = [&](int objectId)
    {
        if (objectId <= 0)
        {
            return;
        }

        const std::optional<uint16_t> descriptionId =
            m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(objectId));

        if (!descriptionId)
        {
            return;
        }

        const ObjectEntry *pObjectEntry = m_pObjectTable->get(*descriptionId);

        if (pObjectEntry == nullptr)
        {
            return;
        }

        if (pObjectEntry->spriteId != 0)
        {
            queueSpriteFrameWarmup(pObjectEntry->spriteId);
            return;
        }

        if (pObjectEntry->spriteName.empty())
        {
            return;
        }

        const SpriteFrameTable *pSpriteFrameTable = nullptr;

        if (m_outdoorSpriteObjectBillboardSet)
        {
            pSpriteFrameTable = &m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
        }
        else if (m_outdoorActorPreviewBillboardSet)
        {
            pSpriteFrameTable = &m_outdoorActorPreviewBillboardSet->spriteFrameTable;
        }

        if (pSpriteFrameTable == nullptr)
        {
            return;
        }

        const std::optional<uint16_t> spriteFrameIndex =
            pSpriteFrameTable->findFrameIndexBySpriteName(pObjectEntry->spriteName);

        if (spriteFrameIndex)
        {
            queueSpriteFrameWarmup(*spriteFrameIndex);
        }
    };

    for (const EventIrEvent &event : eventIrProgram.getEvents())
    {
        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation != EventIrOperation::CastSpell || instruction.arguments.empty())
            {
                continue;
            }

            const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(instruction.arguments[0]));

            if (pSpellEntry == nullptr)
            {
                continue;
            }

            queueSpellObjectSpriteFrame(pSpellEntry->displayObjectId);
            queueSpellObjectSpriteFrame(pSpellEntry->impactDisplayObjectId);
        }
    }
}

void OutdoorGameView::queueRuntimeActorBillboardTextureWarmup()
{
    if (m_pOutdoorWorldRuntime == nullptr || !m_outdoorActorPreviewBillboardSet)
    {
        return;
    }

    const size_t actorCount = m_pOutdoorWorldRuntime->mapActorCount();

    if (m_runtimeActorBillboardTexturesQueuedCount == 0 && actorCount > 0)
    {
        std::vector<size_t> actorIndices(actorCount);

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            actorIndices[actorIndex] = actorIndex;
        }

        std::sort(
            actorIndices.begin(),
            actorIndices.end(),
            [&](size_t left, size_t right)
            {
                const OutdoorWorldRuntime::MapActorState *pLeft = m_pOutdoorWorldRuntime->mapActorState(left);
                const OutdoorWorldRuntime::MapActorState *pRight = m_pOutdoorWorldRuntime->mapActorState(right);

                if (pLeft == nullptr || pRight == nullptr)
                {
                    return left < right;
                }

                const float leftDeltaX = static_cast<float>(pLeft->x) - m_cameraTargetX;
                const float leftDeltaY = static_cast<float>(pLeft->y) - m_cameraTargetY;
                const float leftDistanceSquared = leftDeltaX * leftDeltaX + leftDeltaY * leftDeltaY;
                const float rightDeltaX = static_cast<float>(pRight->x) - m_cameraTargetX;
                const float rightDeltaY = static_cast<float>(pRight->y) - m_cameraTargetY;
                const float rightDistanceSquared = rightDeltaX * rightDeltaX + rightDeltaY * rightDeltaY;
                return leftDistanceSquared < rightDistanceSquared;
            }
        );

        for (size_t actorIndex : actorIndices)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActorState == nullptr)
            {
                continue;
            }

            queueSpriteFrameWarmup(pActorState->spriteFrameIndex);

            for (uint16_t actionSpriteFrameIndex : pActorState->actionSpriteFrameIndices)
            {
                queueSpriteFrameWarmup(actionSpriteFrameIndex);
            }
        }

        m_runtimeActorBillboardTexturesQueuedCount = actorCount;
        return;
    }

    for (size_t actorIndex = m_runtimeActorBillboardTexturesQueuedCount; actorIndex < actorCount; ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActorState = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

        if (pActorState == nullptr)
        {
            continue;
        }

        queueSpriteFrameWarmup(pActorState->spriteFrameIndex);

        for (uint16_t actionSpriteFrameIndex : pActorState->actionSpriteFrameIndices)
        {
            queueSpriteFrameWarmup(actionSpriteFrameIndex);
        }
    }

    m_runtimeActorBillboardTexturesQueuedCount = actorCount;
}

void OutdoorGameView::processPendingSpriteFrameWarmups(size_t maxSpriteFrames)
{
    if (maxSpriteFrames == 0)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    size_t processedCount = 0;

    while (processedCount < maxSpriteFrames && m_nextPendingSpriteFrameWarmupIndex < m_pendingSpriteFrameWarmups.size())
    {
        preloadSpriteFrameTextures(
            *pSpriteFrameTable,
            m_pendingSpriteFrameWarmups[m_nextPendingSpriteFrameWarmupIndex]);
        ++m_nextPendingSpriteFrameWarmupIndex;
        ++processedCount;
    }

    if (m_nextPendingSpriteFrameWarmupIndex >= m_pendingSpriteFrameWarmups.size())
    {
        m_pendingSpriteFrameWarmups.clear();
        m_nextPendingSpriteFrameWarmupIndex = 0;
    }
}

const OutdoorWorldRuntime::MapActorState *OutdoorGameView::runtimeActorStateForBillboard(
    const ActorPreviewBillboard &billboard
) const
{
    if (m_pOutdoorWorldRuntime == nullptr || billboard.source != ActorPreviewSource::Companion)
    {
        return nullptr;
    }

    if (billboard.runtimeActorIndex == static_cast<size_t>(-1))
    {
        return nullptr;
    }

    return m_pOutdoorWorldRuntime->mapActorState(billboard.runtimeActorIndex);
}

void OutdoorGameView::buildDecorationBillboardSpatialIndex()
{
    m_decorationBillboardGridCells.clear();
    m_decorationBillboardGridMinX = 0.0f;
    m_decorationBillboardGridMinY = 0.0f;
    m_decorationBillboardGridWidth = 0;
    m_decorationBillboardGridHeight = 0;

    if (!m_outdoorDecorationBillboardSet || m_outdoorDecorationBillboardSet->billboards.empty())
    {
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();

    for (const DecorationBillboard &billboard : m_outdoorDecorationBillboardSet->billboards)
    {
        const float x = static_cast<float>(-billboard.x);
        const float y = static_cast<float>(billboard.y);
        minX = std::min(minX, x);
        minY = std::min(minY, y);
        maxX = std::max(maxX, x);
        maxY = std::max(maxY, y);
    }

    m_decorationBillboardGridMinX = minX;
    m_decorationBillboardGridMinY = minY;
    m_decorationBillboardGridWidth =
        static_cast<size_t>(std::floor((maxX - minX) / BillboardSpatialCellSize)) + 1;
    m_decorationBillboardGridHeight =
        static_cast<size_t>(std::floor((maxY - minY) / BillboardSpatialCellSize)) + 1;
    m_decorationBillboardGridCells.assign(m_decorationBillboardGridWidth * m_decorationBillboardGridHeight, {});

    for (size_t billboardIndex = 0; billboardIndex < m_outdoorDecorationBillboardSet->billboards.size(); ++billboardIndex)
    {
        const DecorationBillboard &billboard = m_outdoorDecorationBillboardSet->billboards[billboardIndex];
        const float x = static_cast<float>(-billboard.x);
        const float y = static_cast<float>(billboard.y);
        const size_t cellX = std::min(
            static_cast<size_t>(std::max(0.0f, std::floor((x - minX) / BillboardSpatialCellSize))),
            m_decorationBillboardGridWidth - 1);
        const size_t cellY = std::min(
            static_cast<size_t>(std::max(0.0f, std::floor((y - minY) / BillboardSpatialCellSize))),
            m_decorationBillboardGridHeight - 1);
        m_decorationBillboardGridCells[cellY * m_decorationBillboardGridWidth + cellX].push_back(billboardIndex);
    }
}

void OutdoorGameView::collectDecorationBillboardCandidates(
    float minX,
    float minY,
    float maxX,
    float maxY,
    std::vector<size_t> &indices) const
{
    indices.clear();

    if (m_decorationBillboardGridCells.empty() || m_decorationBillboardGridWidth == 0 || m_decorationBillboardGridHeight == 0)
    {
        return;
    }

    const int startCellX = std::clamp(
        static_cast<int>(std::floor((minX - m_decorationBillboardGridMinX) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(m_decorationBillboardGridWidth) - 1);
    const int endCellX = std::clamp(
        static_cast<int>(std::floor((maxX - m_decorationBillboardGridMinX) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(m_decorationBillboardGridWidth) - 1);
    const int startCellY = std::clamp(
        static_cast<int>(std::floor((minY - m_decorationBillboardGridMinY) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(m_decorationBillboardGridHeight) - 1);
    const int endCellY = std::clamp(
        static_cast<int>(std::floor((maxY - m_decorationBillboardGridMinY) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(m_decorationBillboardGridHeight) - 1);

    for (int cellY = startCellY; cellY <= endCellY; ++cellY)
    {
        for (int cellX = startCellX; cellX <= endCellX; ++cellX)
        {
            const std::vector<size_t> &cell =
                m_decorationBillboardGridCells[static_cast<size_t>(cellY) * m_decorationBillboardGridWidth
                    + static_cast<size_t>(cellX)];
            indices.insert(indices.end(), cell.begin(), cell.end());
        }
    }
}

void OutdoorGameView::renderActorCollisionOverlays(uint16_t viewId, const bx::Vec3 &cameraPosition) const
{
    if (!m_showActorCollisionBoxes || (!m_outdoorActorPreviewBillboardSet && m_pOutdoorWorldRuntime == nullptr))
    {
        return;
    }

    std::vector<TerrainVertex> vertices;
    const size_t billboardCount = m_outdoorActorPreviewBillboardSet ? m_outdoorActorPreviewBillboardSet->billboards.size() : 0;
    const size_t runtimeActorCount = m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->mapActorCount() : 0;
    vertices.reserve((billboardCount + runtimeActorCount) * 24);
    std::vector<bool> coveredRuntimeActors;

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    auto appendLine = [&vertices](const bx::Vec3 &start, const bx::Vec3 &end, uint32_t color)
    {
        vertices.push_back({start.x, start.y, start.z, color});
        vertices.push_back({end.x, end.y, end.z, color});
    };

    auto appendActorOverlay =
        [&appendLine](
            int actorX,
            int actorY,
            int actorZ,
            uint16_t actorRadius,
            uint16_t actorHeight,
            bool hostileToParty)
        {
            const uint32_t color = hostileToParty ? 0xff6060ffu : 0xff60ff60u;
            const uint32_t centerColor = 0xff40ffffu;
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actorRadius, 32));
            const float height = static_cast<float>(std::max<uint16_t>(actorHeight, 64));
            const float minX = static_cast<float>(actorX) - halfExtent;
            const float maxX = static_cast<float>(actorX) + halfExtent;
            const float minY = static_cast<float>(actorY) - halfExtent;
            const float maxY = static_cast<float>(actorY) + halfExtent;
            const float minZ = static_cast<float>(actorZ);
            const float maxZ = static_cast<float>(actorZ) + height;

            const bx::Vec3 bottom00 = {minX, minY, minZ};
            const bx::Vec3 bottom01 = {minX, maxY, minZ};
            const bx::Vec3 bottom10 = {maxX, minY, minZ};
            const bx::Vec3 bottom11 = {maxX, maxY, minZ};
            const bx::Vec3 top00 = {minX, minY, maxZ};
            const bx::Vec3 top01 = {minX, maxY, maxZ};
            const bx::Vec3 top10 = {maxX, minY, maxZ};
            const bx::Vec3 top11 = {maxX, maxY, maxZ};

            appendLine(bottom00, bottom01, color);
            appendLine(bottom01, bottom11, color);
            appendLine(bottom11, bottom10, color);
            appendLine(bottom10, bottom00, color);
            appendLine(top00, top01, color);
            appendLine(top01, top11, color);
            appendLine(top11, top10, color);
            appendLine(top10, top00, color);
            appendLine(bottom00, top00, color);
            appendLine(bottom01, top01, color);
            appendLine(bottom10, top10, color);
            appendLine(bottom11, top11, color);
            appendLine(
                {static_cast<float>(actorX), static_cast<float>(actorY), minZ},
                {static_cast<float>(actorX), static_cast<float>(actorY), maxZ},
                centerColor);
            appendLine(
                {minX, static_cast<float>(actorY), minZ},
                {maxX, static_cast<float>(actorY), minZ},
                centerColor);
            appendLine(
                {static_cast<float>(actorX), minY, minZ},
                {static_cast<float>(actorX), maxY, minZ},
                centerColor);
        };

    if (m_outdoorActorPreviewBillboardSet)
    {
        for (const ActorPreviewBillboard &billboard : m_outdoorActorPreviewBillboardSet->billboards)
        {
            if (billboard.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = runtimeActorStateForBillboard(billboard);

            if (pRuntimeActor != nullptr && billboard.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[billboard.runtimeActorIndex] = true;
            }

            if (pRuntimeActor != nullptr && pRuntimeActor->isInvisible)
            {
                continue;
            }

            const float overlayDeltaX = static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->x : -billboard.x)
                - cameraPosition.x;
            const float overlayDeltaY = static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y)
                - cameraPosition.y;
            const float overlayDeltaZ = static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z)
                - cameraPosition.z;
            const float overlayDistanceSquared =
                overlayDeltaX * overlayDeltaX + overlayDeltaY * overlayDeltaY + overlayDeltaZ * overlayDeltaZ;

            if (overlayDistanceSquared > ActorBillboardRenderDistanceSquared)
            {
                continue;
            }

            appendActorOverlay(
                pRuntimeActor != nullptr ? pRuntimeActor->x : -billboard.x,
                pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y,
                pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z,
                pRuntimeActor != nullptr ? pRuntimeActor->radius : billboard.radius,
                pRuntimeActor != nullptr ? pRuntimeActor->height : billboard.height,
                pRuntimeActor != nullptr ? pRuntimeActor->hostileToParty : !billboard.isFriendly);
        }
    }

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pRuntimeActor == nullptr || pRuntimeActor->isInvisible)
            {
                continue;
            }

            const float overlayDeltaX = static_cast<float>(pRuntimeActor->x) - cameraPosition.x;
            const float overlayDeltaY = static_cast<float>(pRuntimeActor->y) - cameraPosition.y;
            const float overlayDeltaZ = static_cast<float>(pRuntimeActor->z) - cameraPosition.z;
            const float overlayDistanceSquared =
                overlayDeltaX * overlayDeltaX + overlayDeltaY * overlayDeltaY + overlayDeltaZ * overlayDeltaZ;

            if (overlayDistanceSquared > ActorBillboardRenderDistanceSquared)
            {
                continue;
            }

            appendActorOverlay(
                pRuntimeActor->x,
                pRuntimeActor->y,
                pRuntimeActor->z,
                pRuntimeActor->radius,
                pRuntimeActor->height,
                pRuntimeActor->hostileToParty);
        }
    }

    if (vertices.empty())
    {
        return;
    }

    if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TerrainVertex::ms_layout)
        < vertices.size())
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &transientVertexBuffer,
        static_cast<uint32_t>(vertices.size()),
        TerrainVertex::ms_layout
    );
    std::memcpy(
        transientVertexBuffer.data,
        vertices.data(),
        static_cast<size_t>(vertices.size() * sizeof(TerrainVertex))
    );

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_PT_LINES
        | BGFX_STATE_LINEAA
    );
    bgfx::submit(viewId, m_programHandle);
}

void OutdoorGameView::renderDecorationBillboards(
    uint16_t viewId,
    uint16_t viewWidth,
    uint16_t viewHeight,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_outdoorDecorationBillboardSet
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(m_cameraYawRadians) * cosPitch,
        -std::sin(m_cameraYawRadians) * cosPitch,
        std::sin(m_cameraPitchRadians)
    };
    const uint32_t animationTimeTicks = currentAnimationTicks();
    const uint64_t actorRenderStartTickCount = SDL_GetTicksNS();
    uint64_t gatherStageNanoseconds = 0;
    uint64_t placeholderStageNanoseconds = 0;
    uint64_t sortStageNanoseconds = 0;
    uint64_t submitStageNanoseconds = 0;
    size_t textureGroupCount = 0;
    size_t ensuredTextureLoadCount = 0;
    struct BillboardDrawItem
    {
        const DecorationBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<size_t> candidateBillboardIndices;
    collectDecorationBillboardCandidates(
        cameraPosition.x - DecorationBillboardRenderDistance,
        cameraPosition.y - DecorationBillboardRenderDistance,
        cameraPosition.x + DecorationBillboardRenderDistance,
        cameraPosition.y + DecorationBillboardRenderDistance,
        candidateBillboardIndices);

    if (candidateBillboardIndices.empty())
    {
        return;
    }

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(candidateBillboardIndices.size());

    for (size_t billboardIndex : candidateBillboardIndices)
    {
        const DecorationBillboard &billboard = m_outdoorDecorationBillboardSet->billboards[billboardIndex];

        if (billboard.spriteId == 0)
        {
            continue;
        }

        const float baseX = static_cast<float>(-billboard.x);
        const float baseY = static_cast<float>(billboard.y);
        const float baseZ = static_cast<float>(billboard.z);
        const float deltaX = baseX - cameraPosition.x;
        const float deltaY = baseY - cameraPosition.y;
        const float deltaZ = baseZ - cameraPosition.z;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

        if (distanceSquared > DecorationBillboardRenderDistanceSquared)
        {
            continue;
        }

        if (deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z <= BillboardNearDepth)
        {
            continue;
        }

        const uint32_t animationOffsetTicks =
            animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
        const SpriteFrameEntry *pFrame =
            m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, animationOffsetTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
        const float angleToCamera = std::atan2(
            static_cast<float>(-billboard.x) - cameraPosition.x,
            static_cast<float>(billboard.y) - cameraPosition.y
        );
        const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || pTexture->width <= 0 || pTexture->height <= 0)
        {
            continue;
        }

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = distanceSquared;
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            const uint16_t leftTextureId = left.pTexture != nullptr ? left.pTexture->textureHandle.idx : 0;
            const uint16_t rightTextureId = right.pTexture != nullptr ? right.pTexture->textureHandle.idx : 0;

            if (leftTextureId != rightTextureId)
            {
                return leftTextureId < rightTextureId;
            }

            return left.distanceSquared > right.distanceSquared;
        }
    );

    size_t groupBegin = 0;

    while (groupBegin < drawItems.size())
    {
        const BillboardTextureHandle *pTexture = drawItems[groupBegin].pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            ++groupBegin;
            continue;
        }

        size_t groupEnd = groupBegin + 1;

        while (groupEnd < drawItems.size() && drawItems[groupEnd].pTexture == pTexture)
        {
            ++groupEnd;
        }

        const uint32_t vertexCount = static_cast<uint32_t>((groupEnd - groupBegin) * 6);

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, TexturedTerrainVertex::ms_layout) < vertexCount)
        {
            groupBegin = groupEnd;
            continue;
        }

        std::vector<TexturedTerrainVertex> vertices;
        vertices.reserve(static_cast<size_t>(vertexCount));

        for (size_t index = groupBegin; index < groupEnd; ++index)
        {
            const BillboardDrawItem &drawItem = drawItems[index];
            const DecorationBillboard &billboard = *drawItem.pBillboard;
            const SpriteFrameEntry &frame = *drawItem.pFrame;
            const float spriteScale = std::max(frame.scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = {
                static_cast<float>(-billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + worldHeight * 0.5f
            };
            const bx::Vec3 right = {
                cameraRight.x * halfWidth,
                cameraRight.y * halfWidth,
                cameraRight.z * halfWidth
            };
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back(
                {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back(
                {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f});
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            vertexCount,
            TexturedTerrainVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, pTexture->textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);

        groupBegin = groupEnd;
    }
}

void OutdoorGameView::renderActorPreviewBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_outdoorActorPreviewBillboardSet && !m_outdoorDecorationBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(m_cameraYawRadians) * cosPitch,
        -std::sin(m_cameraYawRadians) * cosPitch,
        std::sin(m_cameraPitchRadians)
    };
    const uint32_t animationTimeTicks = currentAnimationTicks();
    const uint64_t actorRenderStartTickCount = SDL_GetTicksNS();
    uint64_t gatherStageNanoseconds = 0;
    uint64_t placeholderStageNanoseconds = 0;
    uint64_t sortStageNanoseconds = 0;
    uint64_t submitStageNanoseconds = 0;
    size_t textureGroupCount = 0;
    size_t ensuredTextureLoadCount = 0;

    struct BillboardDrawItem
    {
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float heightScale = 1.0f;
        float distanceSquared = 0.0f;
        float cameraDepth = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    if (m_outdoorActorPreviewBillboardSet)
    {
        drawItems.reserve(m_outdoorActorPreviewBillboardSet->billboards.size());
    }
    else if (m_outdoorDecorationBillboardSet)
    {
        drawItems.reserve(m_outdoorDecorationBillboardSet->billboards.size());
    }

    std::vector<TerrainVertex> placeholderVertices;
    if (m_outdoorActorPreviewBillboardSet)
    {
        placeholderVertices.reserve(m_outdoorActorPreviewBillboardSet->billboards.size() * 6);
    }
    std::vector<bool> coveredRuntimeActors;

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    auto appendActorDrawItem =
        [&](const OutdoorWorldRuntime::MapActorState *pRuntimeActor,
            int actorX,
            int actorY,
            int actorZ,
            uint16_t actorRadius,
            uint16_t actorHeight,
            uint16_t sourceBillboardHeight,
            uint16_t spriteFrameIndex,
            const std::array<uint16_t, 8> &actionSpriteFrameIndices,
            bool useStaticFrame)
        {
            if (pRuntimeActor != nullptr && pRuntimeActor->isInvisible)
            {
                return;
            }

            const float deltaX = static_cast<float>(actorX) - cameraPosition.x;
            const float deltaY = static_cast<float>(actorY) - cameraPosition.y;
            const float deltaZ = static_cast<float>(actorZ) - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

            if (distanceSquared > ActorBillboardRenderDistanceSquared)
            {
                return;
            }

            if (deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z <= BillboardNearDepth)
            {
                return;
            }

            uint32_t frameTimeTicks = useStaticFrame ? 0U : animationTimeTicks;

            if (pRuntimeActor != nullptr)
            {
                const size_t animationIndex = static_cast<size_t>(pRuntimeActor->animation);

                if (animationIndex < actionSpriteFrameIndices.size() && actionSpriteFrameIndices[animationIndex] != 0)
                {
                    spriteFrameIndex = actionSpriteFrameIndices[animationIndex];
                }

                frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pRuntimeActor->animationTimeTicks));
            }

            const SpriteFrameEntry *pFrame =
                m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

            if (pFrame == nullptr)
            {
                const float markerHalfSize =
                    std::max(48.0f, static_cast<float>(std::max(actorRadius, static_cast<uint16_t>(48))));
                const float baseX = static_cast<float>(actorX);
                const float baseY = static_cast<float>(actorY);
                const float baseZ = static_cast<float>(actorZ) + 96.0f;
                const uint32_t markerColor = 0xff3030ff;

                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX, baseY - markerHalfSize, baseZ, markerColor});
                placeholderVertices.push_back({baseX, baseY + markerHalfSize, baseZ, markerColor});
                return;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(actorX) - cameraPosition.x,
                static_cast<float>(actorY) - cameraPosition.y);
            const float actorYaw = pRuntimeActor != nullptr ? ((Pi * 0.5f) - pRuntimeActor->yawRadians) : 0.0f;
            const float octantAngle = actorYaw - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const BillboardTextureHandle *pExistingTexture =
                findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
            const BillboardTextureHandle *pTexture =
                pExistingTexture != nullptr
                    ? pExistingTexture
                    : ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pExistingTexture == nullptr && pTexture != nullptr)
            {
                ++ensuredTextureLoadCount;
            }

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                const float markerHalfSize =
                    std::max(48.0f, static_cast<float>(std::max(actorRadius, static_cast<uint16_t>(48))));
                const float baseX = static_cast<float>(actorX);
                const float baseY = static_cast<float>(actorY);
                const float baseZ = static_cast<float>(actorZ) + 96.0f;
                const uint32_t markerColor = 0xff3030ff;

                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX, baseY - markerHalfSize, baseZ, markerColor});
                placeholderVertices.push_back({baseX, baseY + markerHalfSize, baseZ, markerColor});
                return;
            }

            BillboardDrawItem drawItem = {};
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.x = static_cast<float>(actorX);
            drawItem.y = static_cast<float>(actorY);
            drawItem.z = static_cast<float>(actorZ);
            drawItem.heightScale =
                pRuntimeActor != nullptr && sourceBillboardHeight > 0
                    ? static_cast<float>(actorHeight) / static_cast<float>(sourceBillboardHeight)
                    : 1.0f;
            drawItem.distanceSquared = distanceSquared;
            drawItem.cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;
            drawItems.push_back(drawItem);
        };

    if (m_showDecorationBillboards && m_outdoorDecorationBillboardSet)
    {
        for (const DecorationBillboard &billboard : m_outdoorDecorationBillboardSet->billboards)
        {
            const float deltaX = static_cast<float>(-billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            const float cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;

            if (distanceSquared > DecorationBillboardRenderDistanceSquared || cameraDepth <= BillboardNearDepth)
            {
                continue;
            }

            const uint32_t animationOffsetTicks =
                animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
            const SpriteFrameEntry *pFrame =
                m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, animationOffsetTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
            const float angleToCamera = std::atan2(
                static_cast<float>(-billboard.x) - cameraPosition.x,
                static_cast<float>(billboard.y) - cameraPosition.y
            );
            const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            BillboardDrawItem drawItem = {};
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.x = static_cast<float>(-billboard.x);
            drawItem.y = static_cast<float>(billboard.y);
            drawItem.z = static_cast<float>(billboard.z);
            drawItem.heightScale = 1.0f;
            drawItem.distanceSquared = distanceSquared;
            drawItem.cameraDepth = cameraDepth;
            drawItems.push_back(drawItem);
        }
    }

    if (m_showActors && m_outdoorActorPreviewBillboardSet)
    {
        for (size_t billboardIndex = 0; billboardIndex < m_outdoorActorPreviewBillboardSet->billboards.size(); ++billboardIndex)
        {
            const ActorPreviewBillboard &billboard = m_outdoorActorPreviewBillboardSet->billboards[billboardIndex];

            if (billboard.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = runtimeActorStateForBillboard(billboard);

            const int actorX = pRuntimeActor != nullptr ? pRuntimeActor->x : -billboard.x;
            const int actorY = pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y;
            const int actorZ = pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z;
            const uint16_t actorRadius = pRuntimeActor != nullptr ? pRuntimeActor->radius : billboard.radius;
            const uint16_t actorHeight = pRuntimeActor != nullptr ? pRuntimeActor->height : billboard.height;

            if (pRuntimeActor != nullptr && billboard.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[billboard.runtimeActorIndex] = true;
            }

            appendActorDrawItem(
                pRuntimeActor,
                actorX,
                actorY,
                actorZ,
                actorRadius,
                actorHeight,
                billboard.height,
                billboard.spriteFrameIndex,
                billboard.actionSpriteFrameIndices,
                billboard.useStaticFrame);
        }
    }

    if (m_showActors && m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pRuntimeActor == nullptr)
            {
                continue;
            }

            appendActorDrawItem(
                pRuntimeActor,
                pRuntimeActor->x,
                pRuntimeActor->y,
                pRuntimeActor->z,
                pRuntimeActor->radius,
                pRuntimeActor->height,
                pRuntimeActor->height,
                pRuntimeActor->spriteFrameIndex,
                pRuntimeActor->actionSpriteFrameIndices,
                pRuntimeActor->useStaticSpriteFrame);
        }
    }

    gatherStageNanoseconds += SDL_GetTicksNS() - actorRenderStartTickCount;

    if (!placeholderVertices.empty())
    {
        const uint64_t placeholderStageStartTickCount = SDL_GetTicksNS();

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(placeholderVertices.size()),
                TerrainVertex::ms_layout) >= placeholderVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(placeholderVertices.size()),
                TerrainVertex::ms_layout
            );
            std::memcpy(
                transientVertexBuffer.data,
                placeholderVertices.data(),
                static_cast<size_t>(placeholderVertices.size() * sizeof(TerrainVertex))
            );

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(placeholderVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_LINEAA
                | BGFX_STATE_DEPTH_TEST_LEQUAL
            );
            bgfx::submit(viewId, m_programHandle);
        }

        placeholderStageNanoseconds += SDL_GetTicksNS() - placeholderStageStartTickCount;
    }

    if (!bgfx::isValid(m_texturedTerrainProgramHandle) || !bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        const uint64_t totalActorRenderNanoseconds = SDL_GetTicksNS() - actorRenderStartTickCount;

        if (DebugActorRenderHitchLogging && totalActorRenderNanoseconds >= RenderHitchLogThresholdNanoseconds)
        {
            std::cout << "Actor render hitch: total_ms="
                      << static_cast<double>(totalActorRenderNanoseconds) / 1000000.0
                      << " gather_ms=" << static_cast<double>(gatherStageNanoseconds) / 1000000.0
                      << " placeholder_ms=" << static_cast<double>(placeholderStageNanoseconds) / 1000000.0
                      << " sort_ms=" << static_cast<double>(sortStageNanoseconds) / 1000000.0
                      << " submit_ms=" << static_cast<double>(submitStageNanoseconds) / 1000000.0
                      << " draw_items=" << drawItems.size()
                      << " placeholder_vertices=" << placeholderVertices.size()
                      << " texture_groups=" << textureGroupCount
                      << " ensured_loads=" << ensuredTextureLoadCount
                      << '\n';
        }

        return;
    }

    const uint64_t sortStageStartTickCount = SDL_GetTicksNS();
    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            if (left.cameraDepth != right.cameraDepth)
            {
                return left.cameraDepth > right.cameraDepth;
            }

            return left.distanceSquared > right.distanceSquared;
        }
    );
    sortStageNanoseconds += SDL_GetTicksNS() - sortStageStartTickCount;

    const uint32_t vertexCount = 6;

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const BillboardTextureHandle *pTexture = drawItem.pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, TexturedTerrainVertex::ms_layout) < vertexCount)
        {
            continue;
        }

        ++textureGroupCount;

        const uint64_t submitStageStartTickCount = SDL_GetTicksNS();
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const float spriteScale = std::max(frame.scale * drawItem.heightScale, 0.01f);
        const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
        const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            drawItem.x,
            drawItem.y,
            drawItem.z + worldHeight * 0.5f
        };
        const bx::Vec3 right = {
            cameraRight.x * halfWidth,
            cameraRight.y * halfWidth,
            cameraRight.z * halfWidth
        };
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        const std::array<TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(&transientVertexBuffer, vertexCount, TexturedTerrainVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, pTexture->textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);
        submitStageNanoseconds += SDL_GetTicksNS() - submitStageStartTickCount;
    }

    const uint64_t totalActorRenderNanoseconds = SDL_GetTicksNS() - actorRenderStartTickCount;

    if (DebugActorRenderHitchLogging && totalActorRenderNanoseconds >= RenderHitchLogThresholdNanoseconds)
    {
        std::cout << "Actor render hitch: total_ms="
                  << static_cast<double>(totalActorRenderNanoseconds) / 1000000.0
                  << " gather_ms=" << static_cast<double>(gatherStageNanoseconds) / 1000000.0
                  << " placeholder_ms=" << static_cast<double>(placeholderStageNanoseconds) / 1000000.0
                  << " sort_ms=" << static_cast<double>(sortStageNanoseconds) / 1000000.0
                  << " submit_ms=" << static_cast<double>(submitStageNanoseconds) / 1000000.0
                  << " draw_items=" << drawItems.size()
                  << " placeholder_vertices=" << placeholderVertices.size()
                  << " texture_groups=" << textureGroupCount
                  << " ensured_loads=" << ensuredTextureLoadCount
                  << '\n';
    }
}

void OutdoorGameView::renderRuntimeProjectiles(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }
    else if (m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};

    struct BillboardDrawItem
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_pOutdoorWorldRuntime->projectileCount() + m_pOutdoorWorldRuntime->projectileImpactCount());
    std::vector<TerrainVertex> trailVertices;
    trailVertices.reserve(m_pOutdoorWorldRuntime->projectileCount() * 2);

    auto appendRuntimeDrawItem =
        [&](uint32_t runtimeId,
            const char *kind,
            float x,
            float y,
            float z,
            uint16_t cachedSpriteFrameIndex,
            uint16_t spriteId,
            const std::string &spriteName,
            uint32_t timeTicks)
        {
            uint16_t spriteFrameIndex = cachedSpriteFrameIndex;
            const bool shouldLog = DebugProjectileDrawLogging && timeTicks <= 16;
            const char *pResolutionSource = cachedSpriteFrameIndex != 0 ? "cached" : "none";
            const float deltaX = x - cameraPosition.x;
            const float deltaY = y - cameraPosition.y;
            const float deltaZ = z - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

            if (distanceSquared > RuntimeProjectileRenderDistanceSquared)
            {
                return;
            }

            if (spriteFrameIndex == 0 && !spriteName.empty())
            {
                const std::optional<uint16_t> spriteFrameIndexByName =
                    pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

                if (spriteFrameIndexByName)
                {
                    spriteFrameIndex = *spriteFrameIndexByName;
                    pResolutionSource = "name";
                }
            }

            if (spriteFrameIndex == 0)
            {
                spriteFrameIndex = spriteId;
                pResolutionSource = "id";
            }

            if (spriteFrameIndex == 0)
            {
                if (shouldLog)
                {
                    std::cout
                        << "Projectile draw skipped kind=" << kind
                        << " id=" << runtimeId
                        << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                        << " spriteId=" << spriteId
                        << " reason=no_frame_index"
                        << '\n';
                }
                return;
            }

            const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, timeTicks);

            if (pFrame == nullptr)
            {
                if (shouldLog)
                {
                    std::cout
                        << "Projectile draw skipped kind=" << kind
                        << " id=" << runtimeId
                        << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                        << " spriteId=" << spriteId
                        << " frameIndex=" << spriteFrameIndex
                        << " source=" << pResolutionSource
                        << " reason=frame_missing"
                        << '\n';
                }
                return;
            }

            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                if (shouldLog)
                {
                    std::cout
                        << "Projectile draw skipped kind=" << kind
                        << " id=" << runtimeId
                        << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                        << " spriteId=" << spriteId
                        << " frameIndex=" << spriteFrameIndex
                        << " source=" << pResolutionSource
                        << " texture=\"" << resolvedTexture.textureName << "\""
                        << " palette=" << pFrame->paletteId
                        << " reason=texture_missing"
                        << '\n';
                }
                return;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;

            if (shouldLog)
            {
                std::cout
                    << "Projectile draw kind=" << kind
                    << " id=" << runtimeId
                    << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                    << " spriteId=" << spriteId
                    << " frameIndex=" << spriteFrameIndex
                    << " source=" << pResolutionSource
                    << " texture=\"" << resolvedTexture.textureName << "\""
                    << " palette=" << pFrame->paletteId
                    << " texSize=(" << pTexture->width << ", " << pTexture->height << ")"
                    << " scale=" << spriteScale
                    << " worldSize=(" << worldWidth << ", " << worldHeight << ")"
                    << " pos=(" << x << ", " << y << ", " << z << ")"
                    << " ageTicks=" << timeTicks
                    << '\n';
            }

            BillboardDrawItem drawItem = {};
            drawItem.x = x;
            drawItem.y = y;
            drawItem.z = z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = distanceSquared;
            drawItems.push_back(drawItem);
        };

    for (size_t projectileIndex = 0; projectileIndex < m_pOutdoorWorldRuntime->projectileCount(); ++projectileIndex)
    {
        const OutdoorWorldRuntime::ProjectileState *pProjectile =
            m_pOutdoorWorldRuntime->projectileState(projectileIndex);

        if (pProjectile == nullptr)
        {
            continue;
        }

        const float projectileDeltaX = pProjectile->x - cameraPosition.x;
        const float projectileDeltaY = pProjectile->y - cameraPosition.y;
        const float projectileDeltaZ = pProjectile->z - cameraPosition.z;
        const float projectileDistanceSquared =
            projectileDeltaX * projectileDeltaX
            + projectileDeltaY * projectileDeltaY
            + projectileDeltaZ * projectileDeltaZ;

        if (projectileDistanceSquared <= RuntimeProjectileRenderDistanceSquared)
        {
            const bx::Vec3 trailStart = {
                pProjectile->x,
                pProjectile->y,
                pProjectile->z
            };
            const bx::Vec3 trailEnd = {
                pProjectile->x - pProjectile->velocityX * DebugProjectileTrailSeconds,
                pProjectile->y - pProjectile->velocityY * DebugProjectileTrailSeconds,
                pProjectile->z - pProjectile->velocityZ * DebugProjectileTrailSeconds
            };
            trailVertices.push_back({trailStart.x, trailStart.y, trailStart.z, 0xff40ffffu});
            trailVertices.push_back({trailEnd.x, trailEnd.y, trailEnd.z, 0xff40ffffu});
        }

            appendRuntimeDrawItem(
                pProjectile->projectileId,
                "projectile",
                pProjectile->x,
                pProjectile->y,
                pProjectile->z,
                pProjectile->objectSpriteFrameIndex,
                pProjectile->objectSpriteId,
                pProjectile->objectSpriteName,
                pProjectile->timeSinceCreatedTicks);
    }

    for (size_t effectIndex = 0; effectIndex < m_pOutdoorWorldRuntime->projectileImpactCount(); ++effectIndex)
    {
        const OutdoorWorldRuntime::ProjectileImpactState *pEffect =
            m_pOutdoorWorldRuntime->projectileImpactState(effectIndex);

        if (pEffect == nullptr)
        {
            continue;
        }

            appendRuntimeDrawItem(
                pEffect->effectId,
                "impact",
                pEffect->x,
                pEffect->y,
                pEffect->z,
                pEffect->objectSpriteFrameIndex,
                pEffect->objectSpriteId,
                pEffect->objectSpriteName,
                pEffect->timeSinceCreatedTicks);
    }

    if (!trailVertices.empty())
    {
        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(trailVertices.size()), TerrainVertex::ms_layout)
            >= trailVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(trailVertices.size()),
                TerrainVertex::ms_layout
            );
            std::memcpy(
                transientVertexBuffer.data,
                trailVertices.data(),
                static_cast<size_t>(trailVertices.size() * sizeof(TerrainVertex))
            );

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(trailVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_LINEAA
            );
            bgfx::submit(viewId, m_programHandle);
        }
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            const uint16_t leftTextureId = left.pTexture != nullptr ? left.pTexture->textureHandle.idx : 0;
            const uint16_t rightTextureId = right.pTexture != nullptr ? right.pTexture->textureHandle.idx : 0;

            if (leftTextureId != rightTextureId)
            {
                return leftTextureId < rightTextureId;
            }

            return left.distanceSquared > right.distanceSquared;
        }
    );

    size_t groupBegin = 0;

    while (groupBegin < drawItems.size())
    {
        const BillboardTextureHandle *pTexture = drawItems[groupBegin].pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            ++groupBegin;
            continue;
        }

        size_t groupEnd = groupBegin + 1;

        while (groupEnd < drawItems.size() && drawItems[groupEnd].pTexture == pTexture)
        {
            ++groupEnd;
        }

        const uint32_t vertexCount = static_cast<uint32_t>((groupEnd - groupBegin) * 6);

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, TexturedTerrainVertex::ms_layout) < vertexCount)
        {
            groupBegin = groupEnd;
            continue;
        }

        std::vector<TexturedTerrainVertex> vertices;
        vertices.reserve(static_cast<size_t>(vertexCount));

        for (size_t index = groupBegin; index < groupEnd; ++index)
        {
            const BillboardDrawItem &drawItem = drawItems[index];
            const SpriteFrameEntry &frame = *drawItem.pFrame;
            const float spriteScale = std::max(frame.scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = {drawItem.x, drawItem.y, drawItem.z + worldHeight * 0.5f};
            const bx::Vec3 right = {
                cameraRight.x * halfWidth,
                cameraRight.y * halfWidth,
                cameraRight.z * halfWidth
            };
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back(
                {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back(
                {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f});
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedTerrainVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, pTexture->textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);

        groupBegin = groupEnd;
    }
}

void OutdoorGameView::renderSpriteObjectBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_outdoorSpriteObjectBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};

    struct BillboardDrawItem
    {
        const SpriteObjectBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_outdoorSpriteObjectBillboardSet->billboards.size());

    for (const SpriteObjectBillboard &billboard : m_outdoorSpriteObjectBillboardSet->billboards)
    {
        const SpriteFrameEntry *pFrame =
            m_outdoorSpriteObjectBillboardSet->spriteFrameTable.getFrame(
                billboard.objectSpriteId,
                billboard.timeSinceCreatedTicks
            );

        if (pFrame == nullptr)
        {
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = float(-billboard.x) - cameraPosition.x;
        const float deltaY = float(billboard.y) - cameraPosition.y;
        const float deltaZ = float(billboard.z) - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        }
    );

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteObjectBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = float(texture.width) * spriteScale;
        const float worldHeight = float(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            float(-billboard.x),
            float(billboard.y),
            float(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TexturedTerrainVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedTerrainVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);
    }
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorGameView::buildVertices(const OutdoorMapData &outdoorMapData)
{
    std::vector<TerrainVertex> vertices;
    vertices.reserve(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight);

    const float minHeight = static_cast<float>(outdoorMapData.minHeightSample);
    const float maxHeight = static_cast<float>(outdoorMapData.maxHeightSample);
    const float heightRange = std::max(maxHeight - minHeight, 1.0f);

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth; ++gridX)
        {
            const size_t sampleIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const float heightSample = static_cast<float>(outdoorMapData.heightMap[sampleIndex]);
            const float normalizedHeight = (heightSample - minHeight) / heightRange;
            TerrainVertex vertex = {};
            vertex.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            vertex.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            vertex.z = heightSample * static_cast<float>(OutdoorMapData::TerrainHeightScale);
            vertex.abgr = colorFromHeight(normalizedHeight);
            vertices.push_back(vertex);
        }
    }

    return vertices;
}

std::vector<uint16_t> OutdoorGameView::buildIndices()
{
    std::vector<uint16_t> indices;
    indices.reserve((OutdoorMapData::TerrainWidth - 1) * (OutdoorMapData::TerrainHeight - 1) * 8);

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const uint16_t topLeft =
                static_cast<uint16_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t topRight = static_cast<uint16_t>(topLeft + 1);
            const uint16_t bottomLeft =
                static_cast<uint16_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t bottomRight = static_cast<uint16_t>(bottomLeft + 1);

            indices.push_back(topLeft);
            indices.push_back(topRight);

            indices.push_back(topRight);
            indices.push_back(bottomRight);

            indices.push_back(bottomRight);
            indices.push_back(bottomLeft);

            indices.push_back(bottomLeft);
            indices.push_back(topLeft);
        }
    }

    return indices;
}

std::vector<OutdoorGameView::TexturedTerrainVertex> OutdoorGameView::buildTexturedTerrainVertices(
    const OutdoorMapData &outdoorMapData,
    const OutdoorTerrainTextureAtlas &outdoorTerrainTextureAtlas
)
{
    std::vector<TexturedTerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6
    );

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const OutdoorTerrainAtlasRegion &region =
                outdoorTerrainTextureAtlas.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.isValid)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;

            TexturedTerrainVertex topLeft = {};
            topLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            topLeft.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topLeft.z = static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.u = region.u0;
            topLeft.v = region.v0;

            TexturedTerrainVertex topRight = {};
            topRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            topRight.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topRight.z = static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.u = region.u1;
            topRight.v = region.v0;

            TexturedTerrainVertex bottomLeft = {};
            bottomLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            bottomLeft.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomLeft.z =
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.u = region.u0;
            bottomLeft.v = region.v1;

            TexturedTerrainVertex bottomRight = {};
            bottomRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.z =
                static_cast<float>(outdoorMapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.u = region.u1;
            bottomRight.v = region.v1;

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TexturedTerrainVertex> OutdoorGameView::buildTexturedBModelVertices(
    const OutdoorMapData &outdoorMapData,
    const OutdoorBitmapTexture &texture
)
{
    std::vector<TexturedTerrainVertex> vertices;
    const std::string normalizedTextureName = toLowerCopy(texture.textureName);

    if (texture.width <= 0 || texture.height <= 0)
    {
        return vertices;
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 3 || face.textureName.empty())
            {
                continue;
            }

            if (toLowerCopy(face.textureName) != normalizedTextureName)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
            {
                const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
                TexturedTerrainVertex triangleVertices[3] = {};
                bool isTriangleValid = true;

                for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
                {
                    const size_t localTriangleVertexIndex = triangleVertexIndices[triangleVertexSlot];
                    const uint16_t modelVertexIndex = face.vertexIndices[localTriangleVertexIndex];

                    if (modelVertexIndex >= bmodel.vertices.size()
                        || localTriangleVertexIndex >= face.textureUs.size()
                        || localTriangleVertexIndex >= face.textureVs.size())
                    {
                        isTriangleValid = false;
                        break;
                    }

                    const bx::Vec3 worldVertex = outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
                    const float normalizedU =
                        static_cast<float>(face.textureUs[localTriangleVertexIndex] + face.textureDeltaU)
                        / static_cast<float>(texture.width);
                    const float normalizedV =
                        static_cast<float>(face.textureVs[localTriangleVertexIndex] + face.textureDeltaV)
                        / static_cast<float>(texture.height);

                    TexturedTerrainVertex vertex = {};
                    vertex.x = worldVertex.x;
                    vertex.y = worldVertex.y;
                    vertex.z = worldVertex.z;
                    vertex.u = normalizedU;
                    vertex.v = normalizedV;
                    triangleVertices[triangleVertexSlot] = vertex;
                }

                if (!isTriangleValid)
                {
                    continue;
                }

                for (const TexturedTerrainVertex &vertex : triangleVertices)
                {
                    vertices.push_back(vertex);
                }
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorGameView::buildFilledTerrainVertices(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint32_t>> &outdoorTileColors
)
{
    std::vector<TerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6
    );

    const uint32_t fallbackColor = 0xff707070u;

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t topLeftIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const size_t tileColorIndex =
                static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX);
            const uint32_t tileColor =
                outdoorTileColors ? (*outdoorTileColors)[tileColorIndex] : fallbackColor;

            TerrainVertex topLeft = {};
            topLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            topLeft.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topLeft.z = static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.abgr = tileColor;

            TerrainVertex topRight = {};
            topRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            topRight.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topRight.z = static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.abgr = tileColor;

            TerrainVertex bottomLeft = {};
            bottomLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            bottomLeft.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomLeft.z =
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.abgr = tileColor;

            TerrainVertex bottomRight = {};
            bottomRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.z =
                static_cast<float>(outdoorMapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.abgr = tileColor;

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorGameView::buildBModelWireframeVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 2)
            {
                continue;
            }

            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t startIndex = face.vertexIndices[vertexIndex];
                const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

                if (startIndex >= bmodel.vertices.size() || endIndex >= bmodel.vertices.size())
                {
                    continue;
                }

                const bx::Vec3 startVertex = outdoorBModelVertexToWorld(bmodel.vertices[startIndex]);
                const bx::Vec3 endVertex = outdoorBModelVertexToWorld(bmodel.vertices[endIndex]);

                TerrainVertex lineStart = {};
                lineStart.x = startVertex.x;
                lineStart.y = startVertex.y;
                lineStart.z = startVertex.z;
                lineStart.abgr = colorFromBModel();
                vertices.push_back(lineStart);

                TerrainVertex lineEnd = {};
                lineEnd.x = endVertex.x;
                lineEnd.y = endVertex.y;
                lineEnd.z = endVertex.z;
                lineEnd.abgr = colorFromBModel();
                vertices.push_back(lineEnd);
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorGameView::buildBModelCollisionFaceVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t walkableColor = 0x6600ff00u;
    const uint32_t blockingColor = 0x66ff0000u;

    for (const OutdoorBModel &bModel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bModel.faces)
        {
            if (face.vertexIndices.size() < 3)
            {
                continue;
            }

            std::vector<bx::Vec3> polygonVertices;
            polygonVertices.reserve(face.vertexIndices.size());

            for (uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= bModel.vertices.size())
                {
                    polygonVertices.clear();
                    break;
                }

                polygonVertices.push_back(outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]));
            }

            if (polygonVertices.size() < 3)
            {
                continue;
            }

            const uint32_t color = isOutdoorWalkablePolygonType(face.polygonType) ? walkableColor : blockingColor;

            for (size_t triangleIndex = 1; triangleIndex + 1 < polygonVertices.size(); ++triangleIndex)
            {
                const bx::Vec3 &vertex0 = polygonVertices[0];
                const bx::Vec3 &vertex1 = polygonVertices[triangleIndex];
                const bx::Vec3 &vertex2 = polygonVertices[triangleIndex + 1];

                vertices.push_back({vertex0.x, vertex0.y, vertex0.z, color});
                vertices.push_back({vertex1.x, vertex1.y, vertex1.z, color});
                vertices.push_back({vertex2.x, vertex2.y, vertex2.z, color});
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorGameView::buildEntityMarkerVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t color = makeAbgr(255, 208, 64);
    const float halfExtent = 96.0f;
    const float height = 192.0f;
    vertices.reserve(outdoorMapData.entities.size() * 6);

    for (const OutdoorEntity &entity : outdoorMapData.entities)
    {
        const float centerX = static_cast<float>(-entity.x);
        const float centerY = static_cast<float>(entity.y);
        const float baseZ = static_cast<float>(entity.z);

        vertices.push_back({centerX - halfExtent, centerY, baseZ + height * 0.5f, color});
        vertices.push_back({centerX + halfExtent, centerY, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY - halfExtent, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY + halfExtent, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY, baseZ, color});
        vertices.push_back({centerX, centerY, baseZ + height, color});
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorGameView::buildSpawnMarkerVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t color = makeAbgr(96, 192, 255);
    vertices.reserve(outdoorMapData.spawns.size() * 6);

    for (const OutdoorSpawn &spawn : outdoorMapData.spawns)
    {
        const float centerX = static_cast<float>(-spawn.x);
        const float centerY = static_cast<float>(spawn.y);
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 64));
        const float groundHeight = sampleOutdoorTerrainHeight(
            outdoorMapData,
            static_cast<float>(-spawn.x),
            static_cast<float>(spawn.y)
        );
        const int groundedZ = std::max(spawn.z, static_cast<int>(std::lround(groundHeight)));
        const float centerZ = static_cast<float>(groundedZ) + halfExtent;

        vertices.push_back({centerX - halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX + halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX, centerY - halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY + halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY, centerZ - halfExtent, color});
        vertices.push_back({centerX, centerY, centerZ + halfExtent, color});
    }

    return vertices;
}

OutdoorGameView::InspectHit OutdoorGameView::inspectBModelFace(
    const OutdoorMapData &outdoorMapData,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection
)
{
    InspectHit bestHit = {};
    bestHit.distance = std::numeric_limits<float>::max();

    if (vecLength(rayDirection) <= InspectRayEpsilon)
    {
        return {};
    }

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bModel.faces[faceIndex];

            if (face.vertexIndices.size() < 3)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
            {
                const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
                bx::Vec3 triangleVertices[3] = {
                    bx::Vec3 {0.0f, 0.0f, 0.0f},
                    bx::Vec3 {0.0f, 0.0f, 0.0f},
                    bx::Vec3 {0.0f, 0.0f, 0.0f}
                };
                bool isTriangleValid = true;

                for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
                {
                    const uint16_t vertexIndex = face.vertexIndices[triangleVertexIndices[triangleVertexSlot]];

                    if (vertexIndex >= bModel.vertices.size())
                    {
                        isTriangleValid = false;
                        break;
                    }

                    triangleVertices[triangleVertexSlot] = outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]);
                }

                if (!isTriangleValid)
                {
                    continue;
                }

                float distance = 0.0f;

                if (!intersectRayTriangle(
                        rayOrigin,
                        rayDirection,
                        triangleVertices[0],
                        triangleVertices[1],
                        triangleVertices[2],
                        distance))
                {
                    continue;
                }

                if (!bestHit.hasHit || distance < bestHit.distance)
                {
                    bestHit.hasHit = true;
                    bestHit.kind = "face";
                    bestHit.bModelIndex = bModelIndex;
                    bestHit.faceIndex = faceIndex;
                    bestHit.textureName = face.textureName;
                    bestHit.distance = distance;
                    bestHit.attributes = face.attributes;
                    bestHit.bitmapIndex = face.bitmapIndex;
                    bestHit.cogNumber = face.cogNumber;
                    bestHit.cogTriggeredNumber = face.cogTriggeredNumber;
                    bestHit.cogTrigger = face.cogTrigger;
                    bestHit.polygonType = face.polygonType;
                    bestHit.shade = face.shade;
                    bestHit.visibility = face.visibility;
                }
            }
        }
    }

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OutdoorEntity &entity = outdoorMapData.entities[entityIndex];
        const float halfExtent = 96.0f;
        float distance = 0.0f;

        const bx::Vec3 minBounds = {
            static_cast<float>(-entity.x) - halfExtent,
            static_cast<float>(entity.y) - halfExtent,
            static_cast<float>(entity.z)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(-entity.x) + halfExtent,
            static_cast<float>(entity.y) + halfExtent,
            static_cast<float>(entity.z) + 192.0f
        };

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
            && (!bestHit.hasHit || distance < bestHit.distance))
        {
            bestHit.hasHit = true;
            bestHit.kind = "entity";
            bestHit.bModelIndex = entityIndex;
            bestHit.faceIndex = 0;
            bestHit.name = entity.name;
            bestHit.distance = distance;
            bestHit.decorationListId = entity.decorationListId;
            bestHit.eventIdPrimary = entity.eventIdPrimary;
            bestHit.eventIdSecondary = entity.eventIdSecondary;
            bestHit.variablePrimary = entity.variablePrimary;
            bestHit.variableSecondary = entity.variableSecondary;
            bestHit.specialTrigger = entity.specialTrigger;
        }
    }

    for (size_t spawnIndex = 0; spawnIndex < outdoorMapData.spawns.size(); ++spawnIndex)
    {
        const OutdoorSpawn &spawn = outdoorMapData.spawns[spawnIndex];
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 64));
        const float groundHeight = sampleOutdoorTerrainHeight(
            outdoorMapData,
            static_cast<float>(-spawn.x),
            static_cast<float>(spawn.y)
        );
        const int groundedZ = std::max(spawn.z, static_cast<int>(std::lround(groundHeight)));
        float distance = 0.0f;
        const bx::Vec3 minBounds = {
            static_cast<float>(-spawn.x) - halfExtent,
            static_cast<float>(spawn.y) - halfExtent,
            static_cast<float>(groundedZ)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(-spawn.x) + halfExtent,
            static_cast<float>(spawn.y) + halfExtent,
            static_cast<float>(groundedZ) + halfExtent * 2.0f
        };

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
            && (!bestHit.hasHit || distance < bestHit.distance))
        {
            bestHit.hasHit = true;
            bestHit.kind = "spawn";
            bestHit.bModelIndex = spawnIndex;
            bestHit.faceIndex = 0;
            bestHit.distance = distance;
            bestHit.spawnTypeId = spawn.typeId;

            if (m_map)
            {
                const SpawnPreview preview =
                    SpawnPreviewResolver::describe(
                        *m_map,
                        m_monsterTable ? &*m_monsterTable : nullptr,
                        spawn.typeId,
                        spawn.index,
                        spawn.attributes,
                        spawn.group
                    );
                bestHit.spawnSummary = preview.summary;
                bestHit.spawnDetail = preview.detail;
            }

            if (m_pOutdoorWorldRuntime != nullptr)
            {
                const OutdoorWorldRuntime::SpawnPointState *pSpawnState =
                    m_pOutdoorWorldRuntime->spawnPointState(spawnIndex);

                if (pSpawnState != nullptr)
                {
                    bestHit.isFriendly = !pSpawnState->hostileToParty;
                }
            }
        }
    }

    std::vector<bool> coveredRuntimeActors;

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    if (m_outdoorActorPreviewBillboardSet)
    {
        for (size_t actorIndex = 0; actorIndex < m_outdoorActorPreviewBillboardSet->billboards.size(); ++actorIndex)
        {
            const ActorPreviewBillboard &actor = m_outdoorActorPreviewBillboardSet->billboards[actorIndex];

            if (actor.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pActorState = runtimeActorStateForBillboard(actor);

            if (pActorState != nullptr && actor.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[actor.runtimeActorIndex] = true;
            }

            if (pActorState != nullptr && pActorState->isInvisible)
            {
                continue;
            }

            const int actorX = pActorState != nullptr ? pActorState->x : -actor.x;
            const int actorY = pActorState != nullptr ? pActorState->y : actor.y;
            const int actorZ = pActorState != nullptr ? pActorState->z : actor.z;
            const uint16_t actorRadius = pActorState != nullptr ? pActorState->radius : actor.radius;
            const uint16_t actorHeight = pActorState != nullptr ? pActorState->height : actor.height;
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actorRadius, 64));
            const float height = static_cast<float>(std::max<uint16_t>(actorHeight, 128));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                static_cast<float>(actorX) - halfExtent,
                static_cast<float>(actorY) - halfExtent,
                static_cast<float>(actorZ)
            };
            const bx::Vec3 maxBounds = {
                static_cast<float>(actorX) + halfExtent,
                static_cast<float>(actorY) + halfExtent,
                static_cast<float>(actorZ) + height
            };

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && (!bestHit.hasHit || distance < bestHit.distance))
            {
                bestHit.hasHit = true;
                bestHit.kind = "actor";
                bestHit.bModelIndex = actorIndex;
                bestHit.faceIndex = 0;
                bestHit.name = actor.actorName;
                bestHit.distance = distance;
                bestHit.isFriendly = actor.isFriendly;
                bestHit.npcId = actor.npcId;
                bestHit.actorGroup = actor.group;

                if (m_map)
                {
                    const SpawnPreview preview =
                        SpawnPreviewResolver::describe(
                            *m_map,
                            m_monsterTable ? &*m_monsterTable : nullptr,
                            actor.typeId,
                            actor.index,
                            actor.attributes,
                            actor.group
                        );
                    bestHit.spawnSummary = preview.summary;
                    bestHit.spawnDetail = preview.detail;
                }

                if (pActorState != nullptr)
                {
                    bestHit.isFriendly = !pActorState->hostileToParty;
                }
            }
        }
    }

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pActorState = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActorState == nullptr || pActorState->isInvisible)
            {
                continue;
            }

            const float halfExtent = static_cast<float>(std::max<uint16_t>(pActorState->radius, 64));
            const float height = static_cast<float>(std::max<uint16_t>(pActorState->height, 128));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                static_cast<float>(pActorState->x) - halfExtent,
                static_cast<float>(pActorState->y) - halfExtent,
                static_cast<float>(pActorState->z)
            };
            const bx::Vec3 maxBounds = {
                static_cast<float>(pActorState->x) + halfExtent,
                static_cast<float>(pActorState->y) + halfExtent,
                static_cast<float>(pActorState->z) + height
            };

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && (!bestHit.hasHit || distance < bestHit.distance))
            {
                bestHit.hasHit = true;
                bestHit.kind = "actor";
                bestHit.bModelIndex = actorIndex;
                bestHit.faceIndex = 0;
                bestHit.name = pActorState->displayName;
                bestHit.distance = distance;
                bestHit.isFriendly = !pActorState->hostileToParty;
                bestHit.npcId = 0;
                bestHit.actorGroup = pActorState->group;
                bestHit.spawnSummary.clear();
                bestHit.spawnDetail.clear();
            }
        }
    }

    if (m_outdoorSpriteObjectBillboardSet)
    {
        for (size_t objectIndex = 0; objectIndex < m_outdoorSpriteObjectBillboardSet->billboards.size(); ++objectIndex)
        {
            const SpriteObjectBillboard &object = m_outdoorSpriteObjectBillboardSet->billboards[objectIndex];
            const float halfExtent = std::max(32.0f, float(std::max(object.radius, int16_t(32))));
            const float height = std::max(64.0f, float(std::max(object.height, int16_t(64))));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                float(-object.x) - halfExtent,
                float(object.y) - halfExtent,
                float(object.z)
            };
            const bx::Vec3 maxBounds = {
                float(-object.x) + halfExtent,
                float(object.y) + halfExtent,
                float(object.z) + height
            };

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && (!bestHit.hasHit || distance < bestHit.distance))
            {
                bestHit.hasHit = true;
                bestHit.kind = "object";
                bestHit.bModelIndex = objectIndex;
                bestHit.name = object.objectName;
                bestHit.distance = distance;
                bestHit.objectDescriptionId = object.objectDescriptionId;
                bestHit.objectSpriteId = object.objectSpriteId;
                bestHit.attributes = object.attributes;
                bestHit.spellId = object.spellId;
            }
        }
    }

    return bestHit;
}

bool OutdoorGameView::tryActivateInspectEvent(const InspectHit &inspectHit)
{
    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        std::cout << "Outdoor inspect activation ignored: runtime not available\n";
        return false;
    }

    uint16_t eventId = 0;

    if (inspectHit.kind == "actor" && m_pOutdoorWorldRuntime != nullptr)
    {
        size_t runtimeActorIndex = inspectHit.bModelIndex;

        if (m_outdoorActorPreviewBillboardSet
            && inspectHit.bModelIndex < m_outdoorActorPreviewBillboardSet->billboards.size())
        {
            runtimeActorIndex = m_outdoorActorPreviewBillboardSet->billboards[inspectHit.bModelIndex].runtimeActorIndex;
        }

        if (runtimeActorIndex != static_cast<size_t>(-1))
        {
            const OutdoorWorldRuntime::MapActorState *pActorState =
                m_pOutdoorWorldRuntime->mapActorState(runtimeActorIndex);

            if (pActorState != nullptr && pActorState->isDead
                && m_pOutdoorWorldRuntime->openMapActorCorpseView(runtimeActorIndex))
            {
                pEventRuntimeState->lastActivationResult =
                    "corpse " + std::to_string(runtimeActorIndex) + " opened";
                std::cout << "Opening corpse loot for actor=" << runtimeActorIndex << '\n';
                return true;
            }
        }
    }

    auto faceTalkingActor =
        [this, &inspectHit]()
        {
            if (m_pOutdoorWorldRuntime == nullptr || m_pOutdoorPartyRuntime == nullptr)
            {
                return;
            }

            const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();

            if (inspectHit.kind != "actor")
            {
                return;
            }

            size_t runtimeActorIndex = inspectHit.bModelIndex;

            if (m_outdoorActorPreviewBillboardSet
                && inspectHit.bModelIndex < m_outdoorActorPreviewBillboardSet->billboards.size())
            {
                runtimeActorIndex =
                    m_outdoorActorPreviewBillboardSet->billboards[inspectHit.bModelIndex].runtimeActorIndex;
            }

            if (runtimeActorIndex != static_cast<size_t>(-1))
            {
                m_pOutdoorWorldRuntime->notifyPartyContactWithMapActor(
                    runtimeActorIndex,
                    moveState.x,
                    moveState.y,
                    moveState.footZ);
            }
        };

    if (inspectHit.kind == "actor" && inspectHit.npcId > 0)
    {
        faceTalkingActor();
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(inspectHit.npcId);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
        pEventRuntimeState->lastActivationResult = "npc " + std::to_string(inspectHit.npcId) + " engaged";
        openPendingEventDialog(pEventRuntimeState->messages.size(), true);
        std::cout << "Opening direct NPC dialog for npc=" << inspectHit.npcId << '\n';
        return true;
    }

    if (inspectHit.kind == "actor" && m_npcDialogTable)
    {
        const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
            m_map ? m_map->fileName : std::string(),
            inspectHit.name,
            inspectHit.actorGroup,
            *pEventRuntimeState,
            *m_npcDialogTable
        );

        if (resolution)
        {
            const std::optional<std::string> newsText = m_npcDialogTable->getNewsText(resolution->newsId);

            if (!newsText || newsText->empty())
            {
                return false;
            }

            faceTalkingActor();
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcNews;
            context.sourceId = resolution->npcId;
            context.newsId = resolution->newsId;
            context.titleOverride = inspectHit.name;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
            pEventRuntimeState->messages.push_back(*newsText);
            pEventRuntimeState->lastActivationResult =
                "npc news group " + std::to_string(inspectHit.actorGroup) + " engaged";
            openPendingEventDialog(pEventRuntimeState->messages.size() - 1, true);
            std::cout << "Opening generic NPC news for actor group=" << inspectHit.actorGroup
                      << " npc=" << resolution->npcId
                      << " news=" << resolution->newsId << '\n';
            return true;
        }
    }

    if (inspectHit.kind == "entity")
    {
        eventId = inspectHit.eventIdPrimary != 0 ? inspectHit.eventIdPrimary : inspectHit.eventIdSecondary;
    }
    else if (inspectHit.kind == "face")
    {
        eventId = inspectHit.cogTriggeredNumber;
    }
    else
    {
        pEventRuntimeState->lastActivationResult = "no activatable event on hovered target";
        std::cout << "Outdoor inspect activation ignored: unsupported target kind '"
                  << inspectHit.kind << "'\n";
        return false;
    }

    if (eventId == 0)
    {
        pEventRuntimeState->lastActivationResult = "no event on hovered target";
        std::cout << "Outdoor inspect activation ignored: target has no event id\n";
        return false;
    }

    std::cout << "Activating outdoor event " << eventId
              << " from " << inspectHit.kind
              << " index=" << inspectHit.bModelIndex << '\n';

    const size_t previousMessageCount = pEventRuntimeState->messages.size();

    const bool executed = m_eventRuntime.executeEventById(
        m_localEventIrProgram,
        m_globalEventIrProgram,
        eventId,
        *pEventRuntimeState,
        m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->party() : nullptr,
        m_pOutdoorWorldRuntime
    );

    if (!executed)
    {
        pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        std::cout << "Outdoor event " << eventId << " unresolved\n";
        return false;
    }

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        m_pOutdoorWorldRuntime->applyEventRuntimeState();
    }

    if (m_pOutdoorPartyRuntime)
    {
        m_pOutdoorPartyRuntime->applyEventRuntimeState(*pEventRuntimeState);
    }

    openPendingEventDialog(previousMessageCount, true);

    pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    std::cout << "Outdoor event " << eventId << " executed\n";
    return true;
}

bool OutdoorGameView::tryTriggerLocalEventById(uint16_t eventId)
{
    EventRuntimeState *pEventRuntimeState =
        m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    std::cout << "Triggering local outdoor event " << eventId << " from hotkey\n";

    const size_t previousMessageCount = pEventRuntimeState->messages.size();
    const bool executed = m_eventRuntime.executeEventById(
        m_localEventIrProgram,
        m_globalEventIrProgram,
        eventId,
        *pEventRuntimeState,
        m_pOutdoorPartyRuntime != nullptr ? &m_pOutdoorPartyRuntime->party() : nullptr,
        m_pOutdoorWorldRuntime
    );

    if (!executed)
    {
        pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        std::cout << "Outdoor hotkey event " << eventId << " unresolved\n";
        return false;
    }

    if (m_pOutdoorWorldRuntime != nullptr)
    {
        m_pOutdoorWorldRuntime->applyEventRuntimeState();
    }

    if (m_pOutdoorPartyRuntime != nullptr)
    {
        m_pOutdoorPartyRuntime->applyEventRuntimeState(*pEventRuntimeState);
    }

    openPendingEventDialog(previousMessageCount, true);
    pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    std::cout << "Outdoor hotkey event " << eventId << " executed\n";
    return true;
}

void OutdoorGameView::applyPendingCombatEvents()
{
    if (m_pOutdoorWorldRuntime == nullptr || m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    for (const OutdoorWorldRuntime::CombatEvent &event : m_pOutdoorWorldRuntime->pendingCombatEvents())
    {
        if (event.type != OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
            && event.type != OutdoorWorldRuntime::CombatEvent::Type::PartyProjectileImpact)
        {
            continue;
        }

        std::string sourceName = "monster";

        for (size_t actorIndex = 0; actorIndex < m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            const OutdoorWorldRuntime::MapActorState *pActor = m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActor != nullptr && pActor->actorId == event.sourceId)
            {
                sourceName = pActor->displayName;
                break;
            }
        }

        if (event.sourceId == std::numeric_limits<uint32_t>::max())
        {
            sourceName = event.spellId > 0 ? "event spell" : "event";
        }

        const std::string status = event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
            ? sourceName + " hit party for " + std::to_string(event.damage)
            : sourceName
                + (event.spellId > 0 ? " spell hit party for " : " projectile hit party for ")
                + std::to_string(event.damage);

        if (m_pOutdoorPartyRuntime->party().applyDamageToActiveMember(event.damage, status))
        {
            std::cout << "Party damaged source=" << sourceName
                      << " damage=" << event.damage
                      << " kind="
                      << (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
                              ? "melee"
                              : (event.spellId > 0 ? "spell" : "projectile"))
                      << '\n';
        }
    }

    m_pOutdoorWorldRuntime->clearPendingCombatEvents();
}

void OutdoorGameView::updateCameraFromInput(float deltaSeconds)
{
    const float displayDeltaSeconds = std::max(deltaSeconds, 0.000001f);
    const float instantaneousFramesPerSecond = 1.0f / displayDeltaSeconds;
    m_framesPerSecond = (m_framesPerSecond == 0.0f)
        ? instantaneousFramesPerSecond
        : (m_framesPerSecond * 0.9f + instantaneousFramesPerSecond * 0.1f);
    deltaSeconds = std::min(deltaSeconds, 0.05f);

    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);

    if (pKeyboardState == nullptr)
    {
        return;
    }

    const bool hasActiveLootView =
        m_pOutdoorWorldRuntime != nullptr
        && (m_pOutdoorWorldRuntime->activeChestView() != nullptr || m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);
    const bool isEventDialogActive = hasActiveEventDialog();
    const bool isResidentSelectionMode =
        isEventDialogActive
        && !m_activeEventDialog.actions.empty()
        && std::all_of(
            m_activeEventDialog.actions.begin(),
            m_activeEventDialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });

    if (isEventDialogActive)
    {
        if (m_pOutdoorPartyRuntime != nullptr)
        {
            static constexpr SDL_Scancode PartySelectScancodes[5] = {
                SDL_SCANCODE_1,
                SDL_SCANCODE_2,
                SDL_SCANCODE_3,
                SDL_SCANCODE_4,
                SDL_SCANCODE_5,
            };

            for (size_t memberIndex = 0; memberIndex < std::size(PartySelectScancodes); ++memberIndex)
            {
                if (pKeyboardState[PartySelectScancodes[memberIndex]])
                {
                    if (!m_eventDialogPartySelectLatches[memberIndex])
                    {
                        if (m_pOutdoorPartyRuntime->party().setActiveMemberIndex(memberIndex))
                        {
                            EventRuntimeState *pEventRuntimeState = m_pOutdoorWorldRuntime != nullptr
                                ? m_pOutdoorWorldRuntime->eventRuntimeState()
                                : nullptr;

                            if (pEventRuntimeState != nullptr)
                            {
                                openPendingEventDialog(pEventRuntimeState->messages.size(), true);
                            }
                        }

                        m_eventDialogPartySelectLatches[memberIndex] = true;
                    }
                }
                else
                {
                    m_eventDialogPartySelectLatches[memberIndex] = false;
                }
            }
        }
        else
        {
            m_eventDialogPartySelectLatches.fill(false);
        }

        if (!m_activeEventDialog.actions.empty() && !isResidentSelectionMode)
        {
            if (pKeyboardState[SDL_SCANCODE_UP])
            {
                if (!m_eventDialogSelectUpLatch)
                {
                    m_eventDialogSelectionIndex = m_eventDialogSelectionIndex == 0
                        ? (m_activeEventDialog.actions.size() - 1)
                        : (m_eventDialogSelectionIndex - 1);
                    m_eventDialogSelectUpLatch = true;
                }
            }
            else
            {
                m_eventDialogSelectUpLatch = false;
            }

            if (pKeyboardState[SDL_SCANCODE_DOWN])
            {
                if (!m_eventDialogSelectDownLatch)
                {
                    m_eventDialogSelectionIndex =
                        (m_eventDialogSelectionIndex + 1) % m_activeEventDialog.actions.size();
                    m_eventDialogSelectDownLatch = true;
                }
            }
            else
            {
                m_eventDialogSelectDownLatch = false;
            }
        }
        else
        {
            m_eventDialogSelectUpLatch = false;
            m_eventDialogSelectDownLatch = false;
        }

        const bool acceptPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_SPACE];

        if (acceptPressed && !isResidentSelectionMode)
        {
            if (!m_eventDialogAcceptLatch)
            {
                if (m_activeEventDialog.actions.empty())
                {
                    handleDialogueCloseRequest();
                }
                else
                {
                    executeActiveDialogAction();
                }

                m_eventDialogAcceptLatch = true;
            }
        }
        else
        {
            m_eventDialogAcceptLatch = false;
        }

        float dialogMouseX = 0.0f;
        float dialogMouseY = 0.0f;
        const SDL_MouseButtonFlags dialogMouseButtons = SDL_GetMouseState(&dialogMouseX, &dialogMouseY);
        const bool isLeftMousePressed = (dialogMouseButtons & SDL_BUTTON_LMASK) != 0;
        SDL_Window *pWindow = SDL_GetMouseFocus();

        if (pWindow == nullptr)
        {
            pWindow = SDL_GetKeyboardFocus();
        }

        int screenWidth = 0;
        int screenHeight = 0;

        if (pWindow != nullptr)
        {
            SDL_GetWindowSizeInPixels(pWindow, &screenWidth, &screenHeight);
        }

        const auto findDialoguePointerTarget =
            [this, isResidentSelectionMode, screenWidth, screenHeight](
                float mouseX,
                float mouseY) -> std::pair<DialoguePointerTargetType, size_t>
            {
                if (screenWidth <= 0 || screenHeight <= 0)
                {
                    return {DialoguePointerTargetType::None, 0};
                }

                const EventRuntimeState *pEventRuntimeState =
                    m_pOutdoorWorldRuntime != nullptr ? m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
                const HouseEntry *pHostHouseEntry =
                    (currentDialogueHostHouseId(pEventRuntimeState) != 0 && m_houseTable.has_value())
                    ? m_houseTable->get(currentDialogueHostHouseId(pEventRuntimeState))
                    : nullptr;
                const bool showEventDialogPanel =
                    isResidentSelectionMode || !m_activeEventDialog.actions.empty() || pHostHouseEntry != nullptr;

                if (isResidentSelectionMode)
                {
                    const HudLayoutElement *pEventDialogLayout = findHudLayoutElement("DialogueEventDialog");
                    const std::optional<ResolvedHudLayoutElement> resolvedEventDialog = showEventDialogPanel
                        && pEventDialogLayout != nullptr
                        ? resolveHudLayoutElement(
                            "DialogueEventDialog",
                            screenWidth,
                            screenHeight,
                            pEventDialogLayout->width,
                            pEventDialogLayout->height)
                        : std::nullopt;

                    if (resolvedEventDialog)
                    {
                        const float panelScale = resolvedEventDialog->scale;
                        const float panelPaddingX = 10.0f * panelScale;
                        const float panelPaddingY = 10.0f * panelScale;
                        const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
                        const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
                        const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
                        const float portraitBorderSize = 80.0f * panelScale;
                        const float sectionGap = 8.0f * panelScale;
                        float contentY = panelInnerY;

                        if (pHostHouseEntry != nullptr)
                        {
                            contentY += 20.0f * panelScale + sectionGap;
                        }

                        for (size_t actionIndex = 0; actionIndex < m_activeEventDialog.actions.size(); ++actionIndex)
                        {
                            const float portraitX =
                                std::round(panelInnerX + (panelInnerWidth - portraitBorderSize) * 0.5f);
                            const float portraitY = std::round(contentY);

                            if (mouseX >= portraitX
                                && mouseX < portraitX + portraitBorderSize
                                && mouseY >= portraitY
                                && mouseY < portraitY + portraitBorderSize)
                            {
                                return {DialoguePointerTargetType::Action, actionIndex};
                            }

                            contentY += portraitBorderSize + 20.0f * panelScale + sectionGap;
                        }
                    }
                }
                else
                {
                    const HudLayoutElement *pEventDialogLayout = findHudLayoutElement("DialogueEventDialog");
                    const HudLayoutElement *pTopicRowLayout = findHudLayoutElement("DialogueTopicRow_1");
                    const std::optional<ResolvedHudLayoutElement> resolvedTopicRowTemplate =
                        pTopicRowLayout != nullptr
                        ? resolveHudLayoutElement(
                            "DialogueTopicRow_1",
                            screenWidth,
                            screenHeight,
                            pTopicRowLayout->width,
                            pTopicRowLayout->height)
                        : std::nullopt;
                    const std::optional<ResolvedHudLayoutElement> resolvedEventDialog =
                        (showEventDialogPanel && pEventDialogLayout != nullptr && pTopicRowLayout != nullptr)
                        ? resolveHudLayoutElement(
                            "DialogueEventDialog",
                            screenWidth,
                            screenHeight,
                            pEventDialogLayout->width,
                            pEventDialogLayout->height)
                        : std::nullopt;

                    if (resolvedEventDialog && pTopicRowLayout != nullptr)
                    {
                        const float panelScale = resolvedEventDialog->scale;
                        const float panelPaddingX = 10.0f * panelScale;
                        const float panelPaddingY = 10.0f * panelScale;
                        const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
                        const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
                        const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
                        const float portraitBorderSize = 80.0f * panelScale;
                        const float sectionGap = 8.0f * panelScale;
                        const HudFontHandle *pTopicFont = findHudFont(pTopicRowLayout->fontName);
                        const float topicFontScale = snappedHudFontScale(
                            resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
                        const float topicLineHeight = pTopicFont != nullptr
                            ? static_cast<float>(pTopicFont->fontHeight) * topicFontScale
                            : 20.0f * panelScale;
                        const float topicWrapWidth = 140.0f * (resolvedTopicRowTemplate
                            ? resolvedTopicRowTemplate->scale
                            : panelScale);
                        const float topicTextWidthScaled = std::max(
                            0.0f,
                            std::min(
                                resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth,
                                topicWrapWidth)
                                - std::abs(pTopicRowLayout->textPadX * topicFontScale) * 2.0f
                                - 4.0f * topicFontScale);
                        const float topicTextWidth =
                            std::max(0.0f, topicTextWidthScaled / std::max(1.0f, topicFontScale));
                        const float rowGap = 4.0f * panelScale;
                        const size_t visibleActionCount = std::min<size_t>(m_activeEventDialog.actions.size(), 5);
                        float contentY = panelInnerY;
                        std::vector<float> actionRowHeights;
                        std::vector<float> actionPressHeights;

                        actionRowHeights.reserve(visibleActionCount);
                        actionPressHeights.reserve(visibleActionCount);

                        if (pHostHouseEntry != nullptr)
                        {
                            contentY += 20.0f * panelScale + sectionGap;
                        }

                        contentY += portraitBorderSize + 20.0f * panelScale + sectionGap;
                        const float availableHeight =
                            resolvedEventDialog->y + resolvedEventDialog->height - panelPaddingY - contentY;

                        for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                        {
                            std::string label = m_activeEventDialog.actions[actionIndex].label;

                            if (!m_activeEventDialog.actions[actionIndex].enabled
                                && !m_activeEventDialog.actions[actionIndex].disabledReason.empty())
                            {
                                label += " [disabled]";
                            }

                            std::vector<std::string> wrappedLines = pTopicFont != nullptr
                                ? wrapHudTextToWidth(*pTopicFont, label, topicTextWidth)
                                : std::vector<std::string>{label};

                            if (wrappedLines.empty())
                            {
                                wrappedLines.push_back(label);
                            }

                            const float minimumRowHeight = resolvedTopicRowTemplate
                                ? resolvedTopicRowTemplate->height
                                : pTopicRowLayout->height * panelScale;
                            const float wrappedRowHeight = static_cast<float>(wrappedLines.size()) * topicLineHeight;
                            actionRowHeights.push_back(std::max(minimumRowHeight, wrappedRowHeight));
                            actionPressHeights.push_back(std::max(topicLineHeight, wrappedRowHeight));
                        }

                        float totalHeight = 0.0f;

                        for (size_t actionIndex = 0; actionIndex < actionRowHeights.size(); ++actionIndex)
                        {
                            totalHeight += actionRowHeights[actionIndex];

                            if (actionIndex + 1 < actionRowHeights.size())
                            {
                                totalHeight += rowGap;
                            }
                        }

                        const float topicListCenterOffsetY = 8.0f * panelScale;
                        float rowY = contentY + std::max(0.0f, (availableHeight - totalHeight) * 0.5f)
                            - topicListCenterOffsetY;

                        for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                        {
                            const float rowX = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->x : panelInnerX;
                            const float rowWidth = resolvedTopicRowTemplate
                                ? resolvedTopicRowTemplate->width
                                : panelInnerWidth;
                            const float rowHeight = actionRowHeights[actionIndex];
                            const float pressAreaInsetY = 2.0f * panelScale;
                            const float pressAreaHeight = std::min(
                                rowHeight,
                                actionPressHeights[actionIndex] + pressAreaInsetY * 2.0f);
                            const float pressAreaY = rowY + (rowHeight - pressAreaHeight) * 0.5f;

                            if (mouseX >= rowX
                                && mouseX < rowX + rowWidth
                                && mouseY >= pressAreaY
                                && mouseY < pressAreaY + pressAreaHeight)
                            {
                                return {DialoguePointerTargetType::Action, actionIndex};
                            }

                            rowY += rowHeight + rowGap;
                        }
                    }
                }

                const HudLayoutElement *pGoodbyeLayout = findHudLayoutElement("DialogueGoodbyeButton");
                const std::optional<ResolvedHudLayoutElement> resolvedGoodbye = pGoodbyeLayout != nullptr
                    ? resolveHudLayoutElement(
                        "DialogueGoodbyeButton",
                        screenWidth,
                        screenHeight,
                        pGoodbyeLayout->width,
                        pGoodbyeLayout->height)
                    : std::nullopt;

                if (resolvedGoodbye
                    && mouseX >= resolvedGoodbye->x
                    && mouseX < resolvedGoodbye->x + resolvedGoodbye->width
                    && mouseY >= resolvedGoodbye->y
                    && mouseY < resolvedGoodbye->y + resolvedGoodbye->height)
                {
                    return {DialoguePointerTargetType::CloseButton, 0};
                }

                return {DialoguePointerTargetType::None, 0};
            };

        if (isLeftMousePressed)
        {
            if (!m_dialogueClickLatch)
            {
                const auto [targetType, targetIndex] = findDialoguePointerTarget(dialogMouseX, dialogMouseY);
                m_dialoguePressedTargetType = targetType;
                m_dialoguePressedTargetIndex = targetIndex;
                m_dialogueClickLatch = true;
            }
        }
        else if (m_dialogueClickLatch)
        {
            const auto [targetType, targetIndex] = findDialoguePointerTarget(dialogMouseX, dialogMouseY);

            if (targetType == m_dialoguePressedTargetType && targetIndex == m_dialoguePressedTargetIndex)
            {
                if (targetType == DialoguePointerTargetType::Action
                    && targetIndex < m_activeEventDialog.actions.size())
                {
                    m_eventDialogSelectionIndex = targetIndex;
                    executeActiveDialogAction();
                }
                else if (targetType == DialoguePointerTargetType::CloseButton)
                {
                    handleDialogueCloseRequest();
                }
            }

            m_dialogueClickLatch = false;
            m_dialoguePressedTargetType = DialoguePointerTargetType::None;
            m_dialoguePressedTargetIndex = 0;
        }
        else
        {
            m_dialoguePressedTargetType = DialoguePointerTargetType::None;
            m_dialoguePressedTargetIndex = 0;
        }

        const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E];

        if (closePressed)
        {
            if (!m_closeOverlayLatch)
            {
                handleDialogueCloseRequest();
                m_closeOverlayLatch = true;
            }
        }
        else
        {
            m_closeOverlayLatch = false;
        }

        return;
    }

    m_eventDialogSelectUpLatch = false;
    m_eventDialogSelectDownLatch = false;
    m_eventDialogAcceptLatch = false;
    m_eventDialogPartySelectLatches.fill(false);
    m_dialogueClickLatch = false;
    m_dialoguePressedTargetType = DialoguePointerTargetType::None;
    m_dialoguePressedTargetIndex = 0;

    if (hasActiveLootView)
    {
        const OutdoorWorldRuntime::ChestViewState *pChestView = m_pOutdoorWorldRuntime->activeChestView();
        const OutdoorWorldRuntime::CorpseViewState *pCorpseView = m_pOutdoorWorldRuntime->activeCorpseView();
        const size_t itemCount =
            pChestView != nullptr ? pChestView->items.size() : (pCorpseView != nullptr ? pCorpseView->items.size() : 0);

        if (itemCount == 0)
        {
            m_chestSelectionIndex = 0;
        }
        else if (m_chestSelectionIndex >= itemCount)
        {
            m_chestSelectionIndex = itemCount - 1;
        }

        if (pKeyboardState[SDL_SCANCODE_UP])
        {
            if (!m_chestSelectUpLatch && itemCount > 0)
            {
                m_chestSelectionIndex = (m_chestSelectionIndex == 0) ? (itemCount - 1) : (m_chestSelectionIndex - 1);
                m_chestSelectUpLatch = true;
            }
        }
        else
        {
            m_chestSelectUpLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_DOWN])
        {
            if (!m_chestSelectDownLatch && itemCount > 0)
            {
                m_chestSelectionIndex = (m_chestSelectionIndex + 1) % itemCount;
                m_chestSelectDownLatch = true;
            }
        }
        else
        {
            m_chestSelectDownLatch = false;
        }

        const bool lootPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_SPACE];

        if (lootPressed)
        {
            if (!m_lootChestItemLatch && itemCount > 0 && m_pOutdoorPartyRuntime != nullptr)
            {
                const OutdoorWorldRuntime::ChestViewState *pCurrentChestView = m_pOutdoorWorldRuntime->activeChestView();
                const OutdoorWorldRuntime::CorpseViewState *pCurrentCorpseView = m_pOutdoorWorldRuntime->activeCorpseView();

                const std::vector<OutdoorWorldRuntime::ChestItemState> *pItems = nullptr;

                if (pCurrentChestView != nullptr)
                {
                    pItems = &pCurrentChestView->items;
                }
                else if (pCurrentCorpseView != nullptr)
                {
                    pItems = &pCurrentCorpseView->items;
                }

                if (pItems != nullptr && m_chestSelectionIndex < pItems->size())
                {
                    const OutdoorWorldRuntime::ChestItemState item = (*pItems)[m_chestSelectionIndex];
                    bool canLoot = true;

                    if (!item.isGold)
                    {
                        canLoot = m_pOutdoorPartyRuntime->party().tryGrantItem(item.itemId, item.quantity);
                    }

                    if (canLoot)
                    {
                        OutdoorWorldRuntime::ChestItemState removedItem = {};
                        const bool removed = pCurrentChestView != nullptr
                            ? m_pOutdoorWorldRuntime->takeActiveChestItem(m_chestSelectionIndex, removedItem)
                            : m_pOutdoorWorldRuntime->takeActiveCorpseItem(m_chestSelectionIndex, removedItem);

                        if (removed)
                        {
                            if (removedItem.isGold)
                            {
                                m_pOutdoorPartyRuntime->party().addGold(static_cast<int>(removedItem.goldAmount));
                            }

                            const OutdoorWorldRuntime::ChestViewState *pUpdatedChestView =
                                m_pOutdoorWorldRuntime->activeChestView();
                            const OutdoorWorldRuntime::CorpseViewState *pUpdatedCorpseView =
                                m_pOutdoorWorldRuntime->activeCorpseView();
                            const std::vector<OutdoorWorldRuntime::ChestItemState> *pUpdatedItems = nullptr;

                            if (pUpdatedChestView != nullptr)
                            {
                                pUpdatedItems = &pUpdatedChestView->items;
                            }
                            else if (pUpdatedCorpseView != nullptr)
                            {
                                pUpdatedItems = &pUpdatedCorpseView->items;
                            }

                            if (pUpdatedItems != nullptr && !pUpdatedItems->empty()
                                && m_chestSelectionIndex >= pUpdatedItems->size())
                            {
                                m_chestSelectionIndex = pUpdatedItems->size() - 1;
                            }
                        }
                    }
                }

                m_lootChestItemLatch = true;
            }
        }
        else
        {
            m_lootChestItemLatch = false;
        }

        const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E];

        if (closePressed)
        {
            if (!m_closeOverlayLatch && m_pOutdoorWorldRuntime != nullptr)
            {
                m_pOutdoorWorldRuntime->closeActiveChestView();
                m_pOutdoorWorldRuntime->closeActiveCorpseView();
                m_closeOverlayLatch = true;
                m_activateInspectLatch = true;
                m_chestSelectionIndex = 0;
            }
        }
        else
        {
            m_closeOverlayLatch = false;
        }
    }
    else
    {
        m_closeOverlayLatch = false;
        m_lootChestItemLatch = false;
        m_chestSelectUpLatch = false;
        m_chestSelectDownLatch = false;
        m_chestSelectionIndex = 0;
    }

    const bool turboSpeed = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const float mouseRotateSpeed = 0.0045f;
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isRightMousePressed = (mouseButtons & SDL_BUTTON_RMASK) != 0;

    if (isRightMousePressed)
    {
        if (m_isRotatingCamera)
        {
            const float deltaMouseX = mouseX - m_lastMouseX;
            const float deltaMouseY = mouseY - m_lastMouseY;
            m_cameraYawRadians -= deltaMouseX * mouseRotateSpeed;
            m_cameraPitchRadians -= deltaMouseY * mouseRotateSpeed;
        }

        m_isRotatingCamera = true;
        m_lastMouseX = mouseX;
        m_lastMouseY = mouseY;
    }
    else
    {
        m_isRotatingCamera = false;
    }

    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 forward = {
        cosYaw,
        -sinYaw,
        0.0f
    };
    const bx::Vec3 right = {
        sinYaw,
        cosYaw,
        0.0f
    };

    if (m_outdoorMapData)
    {
        if (m_pOutdoorPartyRuntime)
        {
            if (m_pOutdoorWorldRuntime != nullptr)
            {
                m_pOutdoorPartyRuntime->setActorColliders(buildRuntimeActorColliders(*m_pOutdoorWorldRuntime));
            }

            const OutdoorMovementInput movementInput = {
                !hasActiveLootView && pKeyboardState[SDL_SCANCODE_W],
                !hasActiveLootView && pKeyboardState[SDL_SCANCODE_S],
                !hasActiveLootView && pKeyboardState[SDL_SCANCODE_A],
                !hasActiveLootView && pKeyboardState[SDL_SCANCODE_D],
                !hasActiveLootView && pKeyboardState[SDL_SCANCODE_SPACE],
                !hasActiveLootView && (pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL]),
                !hasActiveLootView && turboSpeed,
                m_cameraYawRadians
            };
            m_pOutdoorPartyRuntime->update(movementInput, deltaSeconds);

            size_t previousMessageCount = 0;

            if (m_pOutdoorWorldRuntime != nullptr && m_pOutdoorWorldRuntime->eventRuntimeState() != nullptr)
            {
                previousMessageCount = m_pOutdoorWorldRuntime->eventRuntimeState()->messages.size();
            }

            if (m_pOutdoorWorldRuntime != nullptr
                && m_pOutdoorWorldRuntime->updateTimers(
                    deltaSeconds,
                    m_eventRuntime,
                    m_localEventIrProgram,
                    m_globalEventIrProgram))
            {
                m_pOutdoorPartyRuntime->applyEventRuntimeState(*m_pOutdoorWorldRuntime->eventRuntimeState());
                openPendingEventDialog(previousMessageCount, true);
            }

            if (m_pOutdoorWorldRuntime != nullptr)
            {
                const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
                m_pOutdoorWorldRuntime->updateMapActors(deltaSeconds, moveState.x, moveState.y, moveState.footZ);
                applyPendingCombatEvents();
                notifyFriendlyActorContacts(
                    *m_pOutdoorWorldRuntime,
                    moveState,
                    m_pOutdoorPartyRuntime->movementEvents());
            }

            m_cameraTargetX = m_pOutdoorPartyRuntime->movementState().x;
            m_cameraTargetY = m_pOutdoorPartyRuntime->movementState().y;
            m_cameraTargetZ = m_pOutdoorPartyRuntime->movementState().footZ + m_cameraEyeHeight;
        }
    }
    else
    {
        float moveVelocityX = 0.0f;
        float moveVelocityY = 0.0f;
        const float freeMoveSpeed = turboSpeed ? 4000.0f : 576.0f;

        if (pKeyboardState[SDL_SCANCODE_A])
        {
            moveVelocityX -= right.x * freeMoveSpeed;
            moveVelocityY -= right.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_D])
        {
            moveVelocityX += right.x * freeMoveSpeed;
            moveVelocityY += right.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_W])
        {
            moveVelocityX += forward.x * freeMoveSpeed;
            moveVelocityY += forward.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_S])
        {
            moveVelocityX -= forward.x * freeMoveSpeed;
            moveVelocityY -= forward.y * freeMoveSpeed;
        }

        m_cameraTargetX += moveVelocityX * deltaSeconds;
        m_cameraTargetY += moveVelocityY * deltaSeconds;
    }

    if (pKeyboardState[SDL_SCANCODE_1])
    {
        if (!m_toggleFilledLatch)
        {
            m_showFilledTerrain = !m_showFilledTerrain;
            m_toggleFilledLatch = true;
        }
    }
    else
    {
        m_toggleFilledLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_2])
    {
        if (!m_toggleWireframeLatch)
        {
            m_showTerrainWireframe = !m_showTerrainWireframe;
            m_toggleWireframeLatch = true;
        }
    }
    else
    {
        m_toggleWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_3])
    {
        if (!m_toggleBModelsLatch)
        {
            m_showBModels = !m_showBModels;
            m_toggleBModelsLatch = true;
        }
    }
    else
    {
        m_toggleBModelsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_4])
    {
        if (!m_toggleBModelWireframeLatch)
        {
            m_showBModelWireframe = !m_showBModelWireframe;
            m_toggleBModelWireframeLatch = true;
        }
    }
    else
    {
        m_toggleBModelWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_5])
    {
        if (!m_toggleBModelCollisionFacesLatch)
        {
            m_showBModelCollisionFaces = !m_showBModelCollisionFaces;
            m_toggleBModelCollisionFacesLatch = true;
        }
    }
    else
    {
        m_toggleBModelCollisionFacesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_6])
    {
        if (!m_toggleActorCollisionBoxesLatch)
        {
            m_showActorCollisionBoxes = !m_showActorCollisionBoxes;
            m_toggleActorCollisionBoxesLatch = true;
        }
    }
    else
    {
        m_toggleActorCollisionBoxesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_7])
    {
        if (!m_toggleActorsLatch)
        {
            m_showActors = !m_showActors;
            m_toggleActorsLatch = true;
        }
    }
    else
    {
        m_toggleActorsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_8])
    {
        if (!m_toggleSpriteObjectsLatch)
        {
            m_showSpriteObjects = !m_showSpriteObjects;
            m_toggleSpriteObjectsLatch = true;
        }
    }
    else
    {
        m_toggleSpriteObjectsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_9])
    {
        if (!m_toggleEntitiesLatch)
        {
            m_showEntities = !m_showEntities;
            m_toggleEntitiesLatch = true;
        }
    }
    else
    {
        m_toggleEntitiesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_0])
    {
        if (!m_toggleSpawnsLatch)
        {
            m_showSpawns = !m_showSpawns;
            m_toggleSpawnsLatch = true;
        }
    }
    else
    {
        m_toggleSpawnsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F2])
    {
        if (!m_toggleDebugHudLatch)
        {
            m_showDebugHud = !m_showDebugHud;
            m_toggleDebugHudLatch = true;
        }
    }
    else
    {
        m_toggleDebugHudLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F3])
    {
        if (!m_toggleDecorationBillboardsLatch)
        {
            m_showDecorationBillboards = !m_showDecorationBillboards;
            m_toggleDecorationBillboardsLatch = true;
        }
    }
    else
    {
        m_toggleDecorationBillboardsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F4])
    {
        if (!m_toggleGameplayHudLatch)
        {
            m_showGameplayHud = !m_showGameplayHud;
            m_toggleGameplayHudLatch = true;
        }
    }
    else
    {
        m_toggleGameplayHudLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F5])
    {
        if (!m_debugDialogueLatch)
        {
            openDebugNpcDialogue(31);
            m_debugDialogueLatch = true;
        }
    }
    else
    {
        m_debugDialogueLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_MINUS])
    {
        if (!m_toggleInspectLatch)
        {
            m_inspectMode = !m_inspectMode;
            m_toggleInspectLatch = true;
        }
    }
    else
    {
        m_toggleInspectLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F1])
    {
        if (!m_triggerMeteorLatch)
        {
            const bool isDwiOutdoor =
                m_map.has_value()
                && m_map->id == DwiMapId
                && m_outdoorMapData.has_value()
                && m_localEventIrProgram.has_value();

            if (isDwiOutdoor)
            {
                tryTriggerLocalEventById(DwiMeteorShowerEventId);
            }

            m_triggerMeteorLatch = true;
        }
    }
    else
    {
        m_triggerMeteorLatch = false;
    }

    if (m_pOutdoorPartyRuntime)
    {
        if (pKeyboardState[SDL_SCANCODE_R])
        {
            if (!m_toggleRunningLatch)
            {
                m_pOutdoorPartyRuntime->toggleRunning();
                m_toggleRunningLatch = true;
            }
        }
        else
        {
            m_toggleRunningLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_F])
        {
            if (!m_toggleFlyingLatch)
            {
                m_pOutdoorPartyRuntime->toggleFlying();
                m_toggleFlyingLatch = true;
            }
        }
        else
        {
            m_toggleFlyingLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_T])
        {
            if (!m_toggleWaterWalkLatch)
            {
                m_pOutdoorPartyRuntime->toggleWaterWalk();
                m_toggleWaterWalkLatch = true;
            }
        }
        else
        {
            m_toggleWaterWalkLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_G])
        {
            if (!m_toggleFeatherFallLatch)
            {
                m_pOutdoorPartyRuntime->toggleFeatherFall();
                m_toggleFeatherFallLatch = true;
            }
        }
        else
        {
            m_toggleFeatherFallLatch = false;
        }
    }

    if (m_cameraYawRadians > Pi)
    {
        m_cameraYawRadians -= Pi * 2.0f;
    }
    else if (m_cameraYawRadians < -Pi)
    {
        m_cameraYawRadians += Pi * 2.0f;
    }

    m_cameraPitchRadians = std::clamp(m_cameraPitchRadians, -1.55f, 1.55f);
    m_cameraTargetZ = std::clamp(m_cameraTargetZ, -2000.0f, 30000.0f);
    m_cameraOrthoScale = std::clamp(m_cameraOrthoScale, 0.05f, 3.5f);
}

}
