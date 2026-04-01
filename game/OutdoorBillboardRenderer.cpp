#include "game/OutdoorBillboardRenderer.h"

#include "game/OutdoorGameView.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>
#include <optional>
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

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

} // namespace

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
    view.collectDecorationBillboardCandidates(
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

        if (view.isInteractiveDecorationHidden(billboard.entityIndex) || billboard.spriteId == 0)
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
                    : view.ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

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
            if (view.isInteractiveDecorationHidden(billboard.entityIndex))
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

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = view.runtimeActorStateForBillboard(billboard);
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
            view.ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

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
                view.ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

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
