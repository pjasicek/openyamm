#include "game/outdoor/OutdoorBillboardRenderer.h"

#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/StringUtils.h"
#include "game/scene/OutdoorSceneRuntime.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <future>
#include <iostream>
#include <iterator>
#include <limits>
#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float RuntimeProjectileRenderDistance = 12288.0f;
constexpr float RuntimeProjectileRenderDistanceSquared =
    RuntimeProjectileRenderDistance * RuntimeProjectileRenderDistance;
constexpr float DecorationBillboardRenderDistance = 16384.0f;
constexpr float DecorationBillboardRenderDistanceSquared =
    DecorationBillboardRenderDistance * DecorationBillboardRenderDistance;
constexpr float ActorBillboardRenderDistance = 16384.0f;
constexpr float ActorBillboardRenderDistanceSquared =
    ActorBillboardRenderDistance * ActorBillboardRenderDistance;
constexpr uint64_t RenderHitchLogThresholdNanoseconds = 16 * 1000 * 1000;
constexpr float BillboardNearDepth = 0.1f;
constexpr bool DebugProjectileDrawLogging = false;
constexpr float DebugProjectileTrailSeconds = 0.05f;
constexpr uint64_t BillboardAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;
constexpr bool DebugActorRenderHitchLogging = false;
constexpr size_t PreloadDecodeWorkerCount = 4;
constexpr bool DebugSpritePreloadLogging = false;

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

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgra(
    const std::vector<uint8_t> &bitmapBytes,
    const std::optional<std::array<uint8_t, 256 * 3>> &overridePalette,
    int &width,
    int &height)
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
                    paletteIndex < pBasePalette->ncolors
                        ? pBasePalette->colors[paletteIndex]
                        : SDL_Color{0, 0, 0, 255};
                const bool isMagentaKey =
                    sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
                const bool isTealKey =
                    sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
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

} // namespace

void OutdoorBillboardRenderer::initializeBillboardResources(OutdoorGameView &view)
{
    if (view.m_outdoorDecorationBillboardSet)
    {
        view.m_decorationBitmapTextureIndexByName.clear();

        for (const OutdoorBitmapTexture &texture : view.m_outdoorDecorationBillboardSet->textures)
        {
            OutdoorGameView::BillboardTextureHandle billboardTexture = {};
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
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size())));

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
                view.m_billboardTextureIndexByPalette[texture.paletteId][view.m_billboardTextureHandles.back().textureName] =
                    view.m_billboardTextureHandles.size() - 1;
                view.m_decorationBitmapTextureIndexByName[toLowerCopy(texture.textureName)] =
                    &texture - view.m_outdoorDecorationBillboardSet->textures.data();
            }
        }
    }

    if (view.m_pOutdoorSceneRuntime != nullptr && view.m_pOutdoorSceneRuntime->localEventIrProgram())
    {
        queueEventSpellBillboardTextureWarmup(view, *view.m_pOutdoorSceneRuntime->localEventIrProgram());
    }

    if (view.m_pOutdoorSceneRuntime != nullptr && view.m_pOutdoorSceneRuntime->globalEventIrProgram())
    {
        queueEventSpellBillboardTextureWarmup(view, *view.m_pOutdoorSceneRuntime->globalEventIrProgram());
    }

    queueRuntimeActorBillboardTextureWarmup(view);
    preloadPendingSpriteFrameWarmupsParallel(view);

    if (!view.m_outdoorSpriteObjectBillboardSet)
    {
        return;
    }

    for (const OutdoorBitmapTexture &texture : view.m_outdoorSpriteObjectBillboardSet->textures)
    {
        if (view.findBillboardTexture(texture.textureName, texture.paletteId) != nullptr)
        {
            continue;
        }

        OutdoorGameView::BillboardTextureHandle billboardTexture = {};
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
            bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size())));

        if (bgfx::isValid(billboardTexture.textureHandle))
        {
            view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
            view.m_billboardTextureIndexByPalette[texture.paletteId][view.m_billboardTextureHandles.back().textureName] =
                view.m_billboardTextureHandles.size() - 1;
        }
    }
}

void OutdoorBillboardRenderer::queueEventSpellBillboardTextureWarmup(
    OutdoorGameView &view,
    const EventIrProgram &eventIrProgram)
{
    if (view.m_pSpellTable == nullptr || view.m_pObjectTable == nullptr)
    {
        return;
    }

    auto queueSpellObjectSpriteFrame =
        [&view](int objectId)
        {
            if (objectId <= 0)
            {
                return;
            }

            const std::optional<uint16_t> descriptionId =
                view.m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(objectId));

            if (!descriptionId)
            {
                return;
            }

            const ObjectEntry *pObjectEntry = view.m_pObjectTable->get(*descriptionId);

            if (pObjectEntry == nullptr)
            {
                return;
            }

            if (pObjectEntry->spriteId != 0)
            {
                view.queueSpriteFrameWarmup(pObjectEntry->spriteId);
                return;
            }

            if (pObjectEntry->spriteName.empty())
            {
                return;
            }

            const SpriteFrameTable *pSpriteFrameTable = nullptr;

            if (view.m_outdoorSpriteObjectBillboardSet)
            {
                pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
            }
            else if (view.m_outdoorActorPreviewBillboardSet)
            {
                pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
            }

            if (pSpriteFrameTable == nullptr)
            {
                return;
            }

            const std::optional<uint16_t> spriteFrameIndex =
                pSpriteFrameTable->findFrameIndexBySpriteName(pObjectEntry->spriteName);

            if (spriteFrameIndex)
            {
                view.queueSpriteFrameWarmup(*spriteFrameIndex);
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

            const SpellEntry *pSpellEntry = view.m_pSpellTable->findById(static_cast<int>(instruction.arguments[0]));

            if (pSpellEntry == nullptr)
            {
                continue;
            }

            queueSpellObjectSpriteFrame(pSpellEntry->displayObjectId);
            queueSpellObjectSpriteFrame(pSpellEntry->impactDisplayObjectId);
        }
    }
}

void OutdoorBillboardRenderer::queueRuntimeActorBillboardTextureWarmup(OutdoorGameView &view)
{
    if (view.m_pOutdoorWorldRuntime == nullptr || !view.m_outdoorActorPreviewBillboardSet)
    {
        return;
    }

    const size_t actorCount = view.m_pOutdoorWorldRuntime->mapActorCount();

    if (view.m_runtimeActorBillboardTexturesQueuedCount == 0 && actorCount > 0)
    {
        std::vector<size_t> actorIndices(actorCount);

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            actorIndices[actorIndex] = actorIndex;
        }

        std::sort(
            actorIndices.begin(),
            actorIndices.end(),
            [&view](size_t left, size_t right)
            {
                const OutdoorWorldRuntime::MapActorState *pLeft = view.m_pOutdoorWorldRuntime->mapActorState(left);
                const OutdoorWorldRuntime::MapActorState *pRight = view.m_pOutdoorWorldRuntime->mapActorState(right);

                if (pLeft == nullptr || pRight == nullptr)
                {
                    return left < right;
                }

                const float leftDeltaX = static_cast<float>(pLeft->x) - view.m_cameraTargetX;
                const float leftDeltaY = static_cast<float>(pLeft->y) - view.m_cameraTargetY;
                const float leftDistanceSquared = leftDeltaX * leftDeltaX + leftDeltaY * leftDeltaY;
                const float rightDeltaX = static_cast<float>(pRight->x) - view.m_cameraTargetX;
                const float rightDeltaY = static_cast<float>(pRight->y) - view.m_cameraTargetY;
                const float rightDistanceSquared = rightDeltaX * rightDeltaX + rightDeltaY * rightDeltaY;
                return leftDistanceSquared < rightDistanceSquared;
            });

        for (size_t actorIndex : actorIndices)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActorState == nullptr)
            {
                continue;
            }

            view.queueSpriteFrameWarmup(pActorState->spriteFrameIndex);

            for (uint16_t actionSpriteFrameIndex : pActorState->actionSpriteFrameIndices)
            {
                view.queueSpriteFrameWarmup(actionSpriteFrameIndex);
            }
        }

        view.m_runtimeActorBillboardTexturesQueuedCount = actorCount;
        return;
    }

    for (size_t actorIndex = view.m_runtimeActorBillboardTexturesQueuedCount; actorIndex < actorCount; ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActorState = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

        if (pActorState == nullptr)
        {
            continue;
        }

        view.queueSpriteFrameWarmup(pActorState->spriteFrameIndex);

        for (uint16_t actionSpriteFrameIndex : pActorState->actionSpriteFrameIndices)
        {
            view.queueSpriteFrameWarmup(actionSpriteFrameIndex);
        }
    }

    view.m_runtimeActorBillboardTexturesQueuedCount = actorCount;
}

void OutdoorBillboardRenderer::preloadPendingSpriteFrameWarmupsParallel(OutdoorGameView &view)
{
    if (view.m_pendingSpriteFrameWarmups.empty() || view.m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    std::vector<SpriteTexturePreloadRequest> preloadRequests;
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> requestIndexByPaletteAndName;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> paletteCache;
    const uint64_t preloadStartTickCount = SDL_GetTicksNS();

    auto queueTextureRequest =
        [&view, &preloadRequests, &requestIndexByPaletteAndName, &paletteCache](
            const std::string &textureName,
            int16_t paletteId)
        {
            if (textureName.empty() || view.findBillboardTexture(textureName, paletteId) != nullptr)
            {
                return;
            }

            const std::string normalizedTextureName = toLowerCopy(textureName);

            if (requestIndexByPaletteAndName[paletteId].contains(normalizedTextureName))
            {
                return;
            }

            const std::optional<std::string> spritePath =
                view.findCachedAssetPath("Data/sprites", normalizedTextureName + ".bmp");

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

            const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*spritePath);

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
                paletteCache[paletteId] = view.loadCachedActPalette(paletteId);
            }

            request.overridePalette = paletteCache[paletteId];
            requestIndexByPaletteAndName[paletteId][normalizedTextureName] = preloadRequests.size();
            preloadRequests.push_back(std::move(request));
        };

    for (uint16_t spriteFrameIndex : view.m_pendingSpriteFrameWarmups)
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
        view.m_pendingSpriteFrameWarmups.clear();
        view.m_nextPendingSpriteFrameWarmupIndex = 0;
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
                        textureHeight);

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
            }));
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
        if (view.findBillboardTexture(decodedTexture.textureName, decodedTexture.paletteId) != nullptr)
        {
            continue;
        }

        OutdoorGameView::BillboardTextureHandle billboardTexture = {};
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
            bgfx::copy(decodedTexture.pixels.data(), static_cast<uint32_t>(decodedTexture.pixels.size())));

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

        view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
        view.m_billboardTextureIndexByPalette[decodedTexture.paletteId][view.m_billboardTextureHandles.back().textureName] =
            view.m_billboardTextureHandles.size() - 1;
        ++uploadedCount;
    }

    const uint64_t preloadElapsedNanoseconds = SDL_GetTicksNS() - preloadStartTickCount;

    if (DebugSpritePreloadLogging)
    {
        std::cout << "Sprite preload complete uploaded=" << uploadedCount
                  << " elapsed_ms=" << static_cast<double>(preloadElapsedNanoseconds) / 1000000.0
                  << '\n';
    }

    view.m_pendingSpriteFrameWarmups.clear();
    view.m_nextPendingSpriteFrameWarmupIndex = 0;
}

void OutdoorBillboardRenderer::processPendingSpriteFrameWarmups(OutdoorGameView &view, size_t maxSpriteFrames)
{
    if (maxSpriteFrames == 0)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    size_t processedCount = 0;

    while (processedCount < maxSpriteFrames
        && view.m_nextPendingSpriteFrameWarmupIndex < view.m_pendingSpriteFrameWarmups.size())
    {
        view.preloadSpriteFrameTextures(
            *pSpriteFrameTable,
            view.m_pendingSpriteFrameWarmups[view.m_nextPendingSpriteFrameWarmupIndex]);
        ++view.m_nextPendingSpriteFrameWarmupIndex;
        ++processedCount;
    }

    if (view.m_nextPendingSpriteFrameWarmupIndex >= view.m_pendingSpriteFrameWarmups.size())
    {
        view.m_pendingSpriteFrameWarmups.clear();
        view.m_nextPendingSpriteFrameWarmupIndex = 0;
    }
}

const OutdoorGameView::BillboardTextureHandle *OutdoorBillboardRenderer::ensureSpriteBillboardTexture(
    OutdoorGameView &view,
    const std::string &textureName,
    int16_t paletteId)
{
    const OutdoorGameView::BillboardTextureHandle *pExistingTexture = view.findBillboardTexture(textureName, paletteId);

    if (pExistingTexture != nullptr)
    {
        return pExistingTexture;
    }

    if (view.m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        view.loadSpriteBitmapPixelsBgraCached(textureName, paletteId, textureWidth, textureHeight);

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        return nullptr;
    }

    OutdoorGameView::BillboardTextureHandle billboardTexture = {};
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
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size())));

    if (!bgfx::isValid(billboardTexture.textureHandle))
    {
        return nullptr;
    }

    view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
    view.m_billboardTextureIndexByPalette[paletteId][view.m_billboardTextureHandles.back().textureName] =
        view.m_billboardTextureHandles.size() - 1;
    return &view.m_billboardTextureHandles.back();
}

void OutdoorBillboardRenderer::invalidateRenderAssets(OutdoorGameView &view)
{
    for (OutdoorGameView::BillboardTextureHandle &textureHandle : view.m_billboardTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    view.m_billboardTextureHandles.clear();
    view.m_billboardTextureIndexByPalette.clear();
    view.m_spriteLoadCache.directoryAssetPathsByPath.clear();
    view.m_spriteLoadCache.assetPathByKey.clear();
    view.m_spriteLoadCache.binaryFilesByPath.clear();
    view.m_spriteLoadCache.actPalettesById.clear();
    view.m_pendingSpriteFrameWarmups.clear();
    view.m_queuedSpriteFrameWarmups.clear();
    view.m_nextPendingSpriteFrameWarmupIndex = 0;
    view.m_runtimeActorBillboardTexturesQueuedCount = 0;
}

void OutdoorBillboardRenderer::destroyRenderAssets(OutdoorGameView &view)
{
    for (OutdoorGameView::BillboardTextureHandle &textureHandle : view.m_billboardTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    invalidateRenderAssets(view);
}

void OutdoorBillboardRenderer::renderDecorationBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    uint16_t viewWidth,
    uint16_t viewHeight,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    (void)viewWidth;
    (void)viewHeight;

    if (!view.m_outdoorDecorationBillboardSet
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle))
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(view.m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(view.m_cameraYawRadians) * cosPitch,
        -std::sin(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraPitchRadians)
    };
    const uint32_t animationTimeTicks = currentAnimationTicks();

    struct BillboardDrawItem
    {
        const DecorationBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<size_t> candidateBillboardIndices;
    OutdoorInteractionController::collectDecorationBillboardCandidates(view, 
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
        const DecorationBillboard &billboard = view.m_outdoorDecorationBillboardSet->billboards[billboardIndex];

        if (OutdoorInteractionController::isInteractiveDecorationHidden(view, billboard.entityIndex)
            || billboard.spriteId == 0)
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
            view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, animationOffsetTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
        const float angleToCamera = std::atan2(
            static_cast<float>(-billboard.x) - cameraPosition.x,
            static_cast<float>(billboard.y) - cameraPosition.y);
        const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const OutdoorGameView::BillboardTextureHandle *pTexture = view.findBillboardTexture(resolvedTexture.textureName);

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
        });

    size_t groupBegin = 0;

    while (groupBegin < drawItems.size())
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture = drawItems[groupBegin].pTexture;

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

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertexCount)
        {
            groupBegin = groupEnd;
            continue;
        }

        std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
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
            const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

            vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back({center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f});
            vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back({center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f});
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            vertexCount,
            OutdoorGameView::TexturedTerrainVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
        bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, pTexture->textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_texturedTerrainProgramHandle);

        groupBegin = groupEnd;
    }
}

void OutdoorBillboardRenderer::renderActorPreviewBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (!view.m_outdoorActorPreviewBillboardSet && !view.m_outdoorDecorationBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(view.m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(view.m_cameraYawRadians) * cosPitch,
        -std::sin(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraPitchRadians)
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
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float heightScale = 1.0f;
        float distanceSquared = 0.0f;
        float cameraDepth = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        drawItems.reserve(view.m_outdoorActorPreviewBillboardSet->billboards.size());
    }
    else if (view.m_outdoorDecorationBillboardSet)
    {
        drawItems.reserve(view.m_outdoorDecorationBillboardSet->billboards.size());
    }

    std::vector<OutdoorGameView::TerrainVertex> placeholderVertices;

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        placeholderVertices.reserve(view.m_outdoorActorPreviewBillboardSet->billboards.size() * 6);
    }

    std::vector<bool> coveredRuntimeActors;

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(view.m_pOutdoorWorldRuntime->mapActorCount(), false);
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
                view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

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
            const OutdoorGameView::BillboardTextureHandle *pExistingTexture =
                view.findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                pExistingTexture != nullptr
                    ? pExistingTexture
                    : ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

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

    if (view.m_showDecorationBillboards && view.m_outdoorDecorationBillboardSet)
    {
        for (const DecorationBillboard &billboard : view.m_outdoorDecorationBillboardSet->billboards)
        {
            if (OutdoorInteractionController::isInteractiveDecorationHidden(view, billboard.entityIndex))
            {
                continue;
            }

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
                view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, animationOffsetTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
            const float angleToCamera = std::atan2(
                static_cast<float>(-billboard.x) - cameraPosition.x,
                static_cast<float>(billboard.y) - cameraPosition.y);
            const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const OutdoorGameView::BillboardTextureHandle *pTexture = view.findBillboardTexture(resolvedTexture.textureName);

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

    if (view.m_showActors && view.m_outdoorActorPreviewBillboardSet)
    {
        for (size_t billboardIndex = 0; billboardIndex < view.m_outdoorActorPreviewBillboardSet->billboards.size(); ++billboardIndex)
        {
            const ActorPreviewBillboard &billboard = view.m_outdoorActorPreviewBillboardSet->billboards[billboardIndex];

            if (billboard.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = OutdoorInteractionController::runtimeActorStateForBillboard(view, billboard);
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

    if (view.m_showActors && view.m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

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
                OutdoorGameView::TerrainVertex::ms_layout) >= placeholderVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(placeholderVertices.size()),
                OutdoorGameView::TerrainVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                placeholderVertices.data(),
                static_cast<size_t>(placeholderVertices.size() * sizeof(OutdoorGameView::TerrainVertex)));

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(placeholderVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_LINEAA
                | BGFX_STATE_DEPTH_TEST_LEQUAL);
            bgfx::submit(viewId, view.m_programHandle);
        }

        placeholderStageNanoseconds += SDL_GetTicksNS() - placeholderStageStartTickCount;
    }

    if (!bgfx::isValid(view.m_texturedTerrainProgramHandle) || !bgfx::isValid(view.m_terrainTextureSamplerHandle))
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
        });
    sortStageNanoseconds += SDL_GetTicksNS() - sortStageStartTickCount;

    const uint32_t vertexCount = 6;

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture = drawItem.pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertexCount)
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
        const bx::Vec3 center = {drawItem.x, drawItem.y, drawItem.z + worldHeight * 0.5f};
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        const std::array<OutdoorGameView::TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(&transientVertexBuffer, vertexCount, OutdoorGameView::TexturedTerrainVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
        bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, pTexture->textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_texturedTerrainProgramHandle);
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

void OutdoorBillboardRenderer::renderRuntimeWorldItems(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};

    struct BillboardDrawItem
    {
        const OutdoorWorldRuntime::WorldItemState *pWorldItem = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(view.m_pOutdoorWorldRuntime->worldItemCount());

    for (size_t worldItemIndex = 0; worldItemIndex < view.m_pOutdoorWorldRuntime->worldItemCount(); ++worldItemIndex)
    {
        const OutdoorWorldRuntime::WorldItemState *pWorldItem = view.m_pOutdoorWorldRuntime->worldItemState(worldItemIndex);

        if (pWorldItem == nullptr)
        {
            continue;
        }

        uint16_t spriteFrameIndex = pWorldItem->objectSpriteFrameIndex;

        if (spriteFrameIndex == 0 && !pWorldItem->objectSpriteName.empty())
        {
            const std::optional<uint16_t> spriteFrameIndexByName =
                pSpriteFrameTable->findFrameIndexBySpriteName(pWorldItem->objectSpriteName);

            if (spriteFrameIndexByName)
            {
                spriteFrameIndex = *spriteFrameIndexByName;
            }
        }

        if (spriteFrameIndex == 0)
        {
            spriteFrameIndex = pWorldItem->objectSpriteId;
        }

        if (spriteFrameIndex == 0)
        {
            continue;
        }

        const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, pWorldItem->timeSinceCreatedTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const OutdoorGameView::BillboardTextureHandle *pTexture =
            ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = pWorldItem->x - cameraPosition.x;
        const float deltaY = pWorldItem->y - cameraPosition.y;
        const float deltaZ = pWorldItem->z - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pWorldItem = pWorldItem;
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
        });

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const OutdoorWorldRuntime::WorldItemState &worldItem = *drawItem.pWorldItem;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const OutdoorGameView::BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {worldItem.x, worldItem.y, worldItem.z + worldHeight * 0.5f};
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        const std::array<OutdoorGameView::TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(vertices.size()),
                OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            OutdoorGameView::TexturedTerrainVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, texture.textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_texturedTerrainProgramHandle);
    }
}

void OutdoorBillboardRenderer::renderRuntimeProjectiles(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
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
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(view.m_pOutdoorWorldRuntime->projectileCount() + view.m_pOutdoorWorldRuntime->projectileImpactCount());
    std::vector<OutdoorGameView::TerrainVertex> trailVertices;
    trailVertices.reserve(view.m_pOutdoorWorldRuntime->projectileCount() * 2);

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
                    std::cout << "Projectile draw skipped kind=" << kind
                              << " id=" << runtimeId
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " reason=no_frame_index\n";
                }
                return;
            }

            const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, timeTicks);

            if (pFrame == nullptr)
            {
                if (shouldLog)
                {
                    std::cout << "Projectile draw skipped kind=" << kind
                              << " id=" << runtimeId
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " reason=frame_missing\n";
                }
                return;
            }

            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                if (shouldLog)
                {
                    std::cout << "Projectile draw skipped kind=" << kind
                              << " id=" << runtimeId
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " texture=\"" << resolvedTexture.textureName << "\""
                              << " palette=" << pFrame->paletteId
                              << " reason=texture_missing\n";
                }
                return;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;

            if (shouldLog)
            {
                std::cout << "Projectile draw kind=" << kind
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

    for (size_t projectileIndex = 0; projectileIndex < view.m_pOutdoorWorldRuntime->projectileCount(); ++projectileIndex)
    {
        const OutdoorWorldRuntime::ProjectileState *pProjectile = view.m_pOutdoorWorldRuntime->projectileState(projectileIndex);

        if (pProjectile == nullptr)
        {
            continue;
        }

        const float projectileDeltaX = pProjectile->x - cameraPosition.x;
        const float projectileDeltaY = pProjectile->y - cameraPosition.y;
        const float projectileDeltaZ = pProjectile->z - cameraPosition.z;
        const float projectileDistanceSquared =
            projectileDeltaX * projectileDeltaX + projectileDeltaY * projectileDeltaY + projectileDeltaZ * projectileDeltaZ;

        if (projectileDistanceSquared <= RuntimeProjectileRenderDistanceSquared)
        {
            const bx::Vec3 trailStart = {pProjectile->x, pProjectile->y, pProjectile->z};
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

    for (size_t effectIndex = 0; effectIndex < view.m_pOutdoorWorldRuntime->projectileImpactCount(); ++effectIndex)
    {
        const OutdoorWorldRuntime::ProjectileImpactState *pEffect = view.m_pOutdoorWorldRuntime->projectileImpactState(effectIndex);

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
        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(trailVertices.size()),
                OutdoorGameView::TerrainVertex::ms_layout) >= trailVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(trailVertices.size()),
                OutdoorGameView::TerrainVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                trailVertices.data(),
                static_cast<size_t>(trailVertices.size() * sizeof(OutdoorGameView::TerrainVertex)));

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
                | BGFX_STATE_LINEAA);
            bgfx::submit(viewId, view.m_programHandle);
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
        });

    size_t groupBegin = 0;

    while (groupBegin < drawItems.size())
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture = drawItems[groupBegin].pTexture;

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

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertexCount)
        {
            groupBegin = groupEnd;
            continue;
        }

        std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
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
            const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

            vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back({center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f});
            vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f});
            vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f});
            vertices.push_back({center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f});
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            OutdoorGameView::TexturedTerrainVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, pTexture->textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_texturedTerrainProgramHandle);

        groupBegin = groupEnd;
    }
}

void OutdoorBillboardRenderer::renderSpriteObjectBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (!view.m_outdoorSpriteObjectBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};

    struct BillboardDrawItem
    {
        const SpriteObjectBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(view.m_outdoorSpriteObjectBillboardSet->billboards.size());

    for (const SpriteObjectBillboard &billboard : view.m_outdoorSpriteObjectBillboardSet->billboards)
    {
        const SpriteFrameEntry *pFrame =
            view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable.getFrame(
                billboard.objectSpriteId,
                billboard.timeSinceCreatedTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const OutdoorGameView::BillboardTextureHandle *pTexture = view.findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = static_cast<float>(-billboard.x) - cameraPosition.x;
        const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
        const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

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
        });

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteObjectBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const OutdoorGameView::BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            static_cast<float>(-billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        const std::array<OutdoorGameView::TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(vertices.size()),
                OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            OutdoorGameView::TexturedTerrainVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, texture.textureHandle);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_texturedTerrainProgramHandle);
    }
}

} // namespace OpenYAMM::Game
