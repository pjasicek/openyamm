#include "game/outdoor/OutdoorRenderer.h"

#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
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
constexpr uint16_t SkyViewId = 0;
constexpr uint16_t MainViewId = 1;
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float ActorBillboardRenderDistance = 16384.0f;
constexpr float ActorBillboardRenderDistanceSquared =
    ActorBillboardRenderDistance * ActorBillboardRenderDistance;
constexpr uint32_t SkyDomeHorizontalSegmentCount = 24;
constexpr uint32_t SkyDomeVerticalSegmentCount = 8;

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
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
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
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

} // namespace

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildTerrainVertices(const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    vertices.reserve(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight);

    const float minHeight = static_cast<float>(mapData.minHeightSample);
    const float maxHeight = static_cast<float>(mapData.maxHeightSample);
    const float heightRange = std::max(maxHeight - minHeight, 1.0f);

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth; ++gridX)
        {
            const size_t sampleIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const float heightSample = static_cast<float>(mapData.heightMap[sampleIndex]);
            const float normalizedHeight = (heightSample - minHeight) / heightRange;
            OutdoorGameView::TerrainVertex vertex = {};
            vertex.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            vertex.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            vertex.z = heightSample * static_cast<float>(OutdoorMapData::TerrainHeightScale);
            vertex.abgr = makeAbgr(
                static_cast<uint8_t>(32.0f + normalizedHeight * 96.0f),
                static_cast<uint8_t>(96.0f + normalizedHeight * 159.0f),
                static_cast<uint8_t>(32.0f + (1.0f - normalizedHeight) * 48.0f));
            vertices.push_back(vertex);
        }
    }

    return vertices;
}

std::vector<uint16_t> OutdoorRenderer::buildTerrainIndices()
{
    std::vector<uint16_t> indices;
    indices.reserve((OutdoorMapData::TerrainWidth - 1) * (OutdoorMapData::TerrainHeight - 1) * 8);

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const uint16_t topLeft = static_cast<uint16_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t topRight = static_cast<uint16_t>(topLeft + 1);
            const uint16_t bottomLeft = static_cast<uint16_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
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

std::vector<OutdoorGameView::TexturedTerrainVertex> OutdoorRenderer::buildTexturedTerrainVertices(
    const OutdoorMapData &mapData,
    const OutdoorTerrainTextureAtlas &textureAtlas)
{
    std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6);

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = mapData.tileMap[tileMapIndex];
            const OutdoorTerrainAtlasRegion &region = textureAtlas.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.isValid)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;

            OutdoorGameView::TexturedTerrainVertex topLeft = {};
            topLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            topLeft.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topLeft.z = static_cast<float>(mapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.u = region.u0;
            topLeft.v = region.v0;

            OutdoorGameView::TexturedTerrainVertex topRight = {};
            topRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            topRight.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topRight.z = static_cast<float>(mapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.u = region.u1;
            topRight.v = region.v0;

            OutdoorGameView::TexturedTerrainVertex bottomLeft = {};
            bottomLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            bottomLeft.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomLeft.z = static_cast<float>(mapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.u = region.u0;
            bottomLeft.v = region.v1;

            OutdoorGameView::TexturedTerrainVertex bottomRight = {};
            bottomRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.z = static_cast<float>(mapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
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

std::vector<OutdoorGameView::TexturedTerrainVertex> OutdoorRenderer::buildTexturedBModelVertices(
    const OutdoorMapData &mapData,
    const OutdoorBitmapTexture &texture)
{
    std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
    const std::string normalizedTextureName = toLowerCopy(texture.textureName);

    if (texture.width <= 0 || texture.height <= 0)
    {
        return vertices;
    }

    for (const OutdoorBModel &bmodel : mapData.bmodels)
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
                OutdoorGameView::TexturedTerrainVertex triangleVertices[3] = {};
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

                    OutdoorGameView::TexturedTerrainVertex vertex = {};
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

                for (const OutdoorGameView::TexturedTerrainVertex &vertex : triangleVertices)
                {
                    vertices.push_back(vertex);
                }
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildFilledTerrainVertices(
    const OutdoorMapData &mapData,
    const std::optional<std::vector<uint32_t>> &tileColors)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6);

    const uint32_t fallbackColor = 0xff707070u;

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t topLeftIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const size_t tileColorIndex = static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX);
            const uint32_t tileColor = tileColors ? (*tileColors)[tileColorIndex] : fallbackColor;

            OutdoorGameView::TerrainVertex topLeft = {};
            topLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            topLeft.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topLeft.z = static_cast<float>(mapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.abgr = tileColor;

            OutdoorGameView::TerrainVertex topRight = {};
            topRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            topRight.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topRight.z = static_cast<float>(mapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.abgr = tileColor;

            OutdoorGameView::TerrainVertex bottomLeft = {};
            bottomLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            bottomLeft.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomLeft.z =
                static_cast<float>(mapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.abgr = tileColor;

            OutdoorGameView::TerrainVertex bottomRight = {};
            bottomRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.z =
                static_cast<float>(mapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
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

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildBModelWireframeVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t lineColor = makeAbgr(255, 192, 96);

    for (const OutdoorBModel &bmodel : mapData.bmodels)
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

                OutdoorGameView::TerrainVertex lineStart = {};
                lineStart.x = startVertex.x;
                lineStart.y = startVertex.y;
                lineStart.z = startVertex.z;
                lineStart.abgr = lineColor;
                vertices.push_back(lineStart);

                OutdoorGameView::TerrainVertex lineEnd = {};
                lineEnd.x = endVertex.x;
                lineEnd.y = endVertex.y;
                lineEnd.z = endVertex.z;
                lineEnd.abgr = lineColor;
                vertices.push_back(lineEnd);
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildBModelCollisionFaceVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t walkableColor = 0x6600ff00u;
    const uint32_t blockingColor = 0x66ff0000u;

    for (const OutdoorBModel &bModel : mapData.bmodels)
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

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildEntityMarkerVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t color = makeAbgr(255, 208, 64);
    const float halfExtent = 96.0f;
    const float height = 192.0f;
    vertices.reserve(mapData.entities.size() * 6);

    for (const OutdoorEntity &entity : mapData.entities)
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

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildSpawnMarkerVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t color = makeAbgr(96, 192, 255);
    vertices.reserve(mapData.spawns.size() * 6);

    for (const OutdoorSpawn &spawn : mapData.spawns)
    {
        const float centerX = static_cast<float>(-spawn.x);
        const float centerY = static_cast<float>(spawn.y);
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 64));
        const float groundHeight = sampleOutdoorTerrainHeight(
            mapData,
            static_cast<float>(-spawn.x),
            static_cast<float>(spawn.y));
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

bgfx::ShaderHandle OutdoorRenderer::loadShaderHandle(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return bgfx::ShaderHandle{bgfx::kInvalidHandle};
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr << "Failed to read shader: " << shaderPath << '\n';
        return bgfx::ShaderHandle{bgfx::kInvalidHandle};
    }

    const bgfx::Memory *pShaderMemory = bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size()));
    return bgfx::createShader(pShaderMemory);
}

bgfx::ProgramHandle OutdoorRenderer::loadProgramHandle(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShaderHandle(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShaderHandle(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return bgfx::ProgramHandle{bgfx::kInvalidHandle};
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

void OutdoorRenderer::createBModelTextureBatches(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet)
{
    if (!outdoorBModelTextureSet)
    {
        return;
    }

    for (const OutdoorBitmapTexture &texture : outdoorBModelTextureSet->textures)
    {
        const std::vector<OutdoorGameView::TexturedTerrainVertex> texturedBModelVertices =
            buildTexturedBModelVertices(outdoorMapData, texture);

        if (texturedBModelVertices.empty())
        {
            continue;
        }

        OutdoorGameView::TexturedBModelBatch batch = {};
        batch.vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                texturedBModelVertices.data(),
                static_cast<uint32_t>(
                    texturedBModelVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))),
            OutdoorGameView::TexturedTerrainVertex::ms_layout);
        batch.textureHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(texture.width),
            static_cast<uint16_t>(texture.height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size())));
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

        view.m_texturedBModelBatches.push_back(batch);
    }
}

bool OutdoorRenderer::initializeWorldRenderResources(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint32_t>> &outdoorTileColors,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet)
{
    OutdoorGameView::TerrainVertex::init();
    OutdoorGameView::TexturedTerrainVertex::init();
    const std::vector<OutdoorGameView::TerrainVertex> vertices = buildTerrainVertices(outdoorMapData);
    const std::vector<uint16_t> indices = buildTerrainIndices();
    std::vector<OutdoorGameView::TexturedTerrainVertex> texturedTerrainVertices;
    const std::vector<OutdoorGameView::TerrainVertex> filledTerrainVertices = buildFilledTerrainVertices(
        outdoorMapData,
        outdoorTileColors);
    const std::vector<OutdoorGameView::TerrainVertex> bmodelVertices = buildBModelWireframeVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> bmodelCollisionVertices = buildBModelCollisionFaceVertices(
        outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> entityMarkerVertices =
        buildEntityMarkerVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> spawnMarkerVertices =
        buildSpawnMarkerVertices(outdoorMapData);

    if (outdoorTerrainTextureAtlas)
    {
        texturedTerrainVertices = buildTexturedTerrainVertices(outdoorMapData, *outdoorTerrainTextureAtlas);
    }

    view.m_baseTexturedTerrainVertices = texturedTerrainVertices;
    view.m_animatedTexturedTerrainVertices = texturedTerrainVertices;

    if (vertices.empty() || indices.empty())
    {
        std::cerr << "OutdoorGameView received empty terrain mesh.\n";
        return false;
    }

    view.m_vertexBufferHandle = bgfx::createVertexBuffer(
        bgfx::copy(
            vertices.data(),
            static_cast<uint32_t>(vertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
        OutdoorGameView::TerrainVertex::ms_layout);

    view.m_indexBufferHandle = bgfx::createIndexBuffer(
        bgfx::copy(indices.data(), static_cast<uint32_t>(indices.size() * sizeof(uint16_t))));

    if (!texturedTerrainVertices.empty())
    {
        view.m_texturedTerrainVertexBufferHandle = bgfx::createDynamicVertexBuffer(
            bgfx::copy(
                texturedTerrainVertices.data(),
                static_cast<uint32_t>(
                    texturedTerrainVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))),
            OutdoorGameView::TexturedTerrainVertex::ms_layout,
            BGFX_BUFFER_NONE);
    }

    if (!filledTerrainVertices.empty())
    {
        view.m_filledTerrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                filledTerrainVertices.data(),
                static_cast<uint32_t>(
                    filledTerrainVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
    }

    if (!bmodelVertices.empty())
    {
        view.m_bmodelVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelVertices.data(),
                static_cast<uint32_t>(bmodelVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_bmodelLineVertexCount = static_cast<uint32_t>(bmodelVertices.size());
    }

    if (!bmodelCollisionVertices.empty())
    {
        view.m_bmodelCollisionVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelCollisionVertices.data(),
                static_cast<uint32_t>(
                    bmodelCollisionVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_bmodelCollisionVertexCount = static_cast<uint32_t>(bmodelCollisionVertices.size());
    }

    if (!entityMarkerVertices.empty())
    {
        view.m_entityMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                entityMarkerVertices.data(),
                static_cast<uint32_t>(
                    entityMarkerVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_entityMarkerVertexCount = static_cast<uint32_t>(entityMarkerVertices.size());
    }

    if (!spawnMarkerVertices.empty())
    {
        view.m_spawnMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                spawnMarkerVertices.data(),
                static_cast<uint32_t>(
                    spawnMarkerVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_spawnMarkerVertexCount = static_cast<uint32_t>(spawnMarkerVertices.size());
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        view.m_bmodelFaceCount += static_cast<uint32_t>(bmodel.faces.size());
    }

    view.m_programHandle = loadProgramHandle("vs_cubes", "fs_cubes");
    view.m_texturedTerrainProgramHandle = loadProgramHandle("vs_shadowmaps_texture", "fs_shadowmaps_texture");

    if (outdoorTerrainTextureAtlas && !outdoorTerrainTextureAtlas->pixels.empty())
    {
        view.m_terrainTextureAtlasHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->width),
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            bgfx::copy(
                outdoorTerrainTextureAtlas->pixels.data(),
                static_cast<uint32_t>(outdoorTerrainTextureAtlas->pixels.size())));
    }

    createBModelTextureBatches(view, outdoorMapData, outdoorBModelTextureSet);

    return true;
}

const OutdoorGameView::SkyTextureHandle *OutdoorRenderer::ensureSkyTexture(
    OutdoorGameView &view,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);
    const auto cachedTextureIt = view.m_skyTextureIndexByName.find(normalizedTextureName);

    if (cachedTextureIt != view.m_skyTextureIndexByName.end() && cachedTextureIt->second < view.m_skyTextureHandles.size())
    {
        return &view.m_skyTextureHandles[cachedTextureIt->second];
    }

    const std::optional<std::string> bitmapPath = view.findCachedAssetPath("Data/bitmaps", textureName + ".bmp");

    if (!bitmapPath)
    {
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return nullptr;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return nullptr;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return nullptr;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return nullptr;
    }

    const int textureWidth = pConvertedSurface->w;
    const int textureHeight = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(textureWidth) * static_cast<size_t>(textureHeight) * 4;
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);

    OutdoorGameView::SkyTextureHandle textureHandle = {};
    textureHandle.textureName = normalizedTextureName;
    textureHandle.width = textureWidth;
    textureHandle.height = textureHeight;
    textureHandle.textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(textureHandle.width),
        static_cast<uint16_t>(textureHandle.height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_MIRROR | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixels.data(), static_cast<uint32_t>(pixels.size())));

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return nullptr;
    }

    view.m_skyTextureHandles.push_back(std::move(textureHandle));
    view.m_skyTextureIndexByName[view.m_skyTextureHandles.back().textureName] = view.m_skyTextureHandles.size() - 1;
    return &view.m_skyTextureHandles.back();
}

void OutdoorRenderer::invalidateSkyResources(OutdoorGameView &view)
{
    for (OutdoorGameView::SkyTextureHandle &textureHandle : view.m_skyTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    view.m_skyTextureHandles.clear();
    view.m_skyTextureIndexByName.clear();
}

void OutdoorRenderer::destroySkyResources(OutdoorGameView &view)
{
    for (OutdoorGameView::SkyTextureHandle &textureHandle : view.m_skyTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    invalidateSkyResources(view);
}

OutdoorRenderer::WorldPassTimings OutdoorRenderer::renderWorldPasses(
    OutdoorGameView &view,
    uint16_t viewWidth,
    uint16_t viewHeight,
    float aspectRatio,
    float farClipDistance,
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    const float *pViewMatrix)
{
    WorldPassTimings timings = {};
    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);

    if (pAtmosphereState != nullptr)
    {
        renderOutdoorSky(
            view,
            SkyViewId,
            viewWidth,
            viewHeight,
            cameraPosition,
            cameraForward,
            cameraRight,
            cameraUp,
            farClipDistance);
    }

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        bgfx::setTransform(modelMatrix);

        if (view.m_showFilledTerrain && bgfx::isValid(view.m_filledTerrainVertexBufferHandle))
        {
            bgfx::setVertexBuffer(0, view.m_filledTerrainVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }

        if (view.m_showFilledTerrain
            && bgfx::isValid(view.m_texturedTerrainVertexBufferHandle)
            && bgfx::isValid(view.m_texturedTerrainProgramHandle)
            && bgfx::isValid(view.m_terrainTextureAtlasHandle)
            && bgfx::isValid(view.m_terrainTextureSamplerHandle))
        {
            if (!view.m_baseTexturedTerrainVertices.empty()
                && view.m_baseTexturedTerrainVertices.size() == view.m_animatedTexturedTerrainVertices.size())
            {
                view.m_animatedTexturedTerrainVertices = view.m_baseTexturedTerrainVertices;

                bgfx::update(
                    view.m_texturedTerrainVertexBufferHandle,
                    0,
                    bgfx::copy(
                        view.m_animatedTexturedTerrainVertices.data(),
                        static_cast<uint32_t>(
                            view.m_animatedTexturedTerrainVertices.size()
                            * sizeof(OutdoorGameView::TexturedTerrainVertex))
                    )
                );
            }

            bgfx::setVertexBuffer(0, view.m_texturedTerrainVertexBufferHandle);
            bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, view.m_terrainTextureAtlasHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
            );
            bgfx::submit(MainViewId, view.m_texturedTerrainProgramHandle);
        }

        if (view.m_showTerrainWireframe)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, view.m_vertexBufferHandle);
            bgfx::setIndexBuffer(view.m_indexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }

        timings.terrainNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();

        if (view.m_showBModels
            && bgfx::isValid(view.m_bmodelVertexBufferHandle)
            && view.m_bmodelLineVertexCount > 0)
        {
            if (bgfx::isValid(view.m_texturedTerrainProgramHandle)
                && bgfx::isValid(view.m_terrainTextureSamplerHandle))
            {
                for (const OutdoorGameView::TexturedBModelBatch &batch : view.m_texturedBModelBatches)
                {
                    if (!bgfx::isValid(batch.vertexBufferHandle)
                        || !bgfx::isValid(batch.textureHandle)
                        || batch.vertexCount == 0)
                    {
                        continue;
                    }

                    bgfx::setTransform(modelMatrix);
                    bgfx::setVertexBuffer(0, batch.vertexBufferHandle, 0, batch.vertexCount);
                    bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, batch.textureHandle);
                    bgfx::setState(
                        BGFX_STATE_WRITE_RGB
                        | BGFX_STATE_WRITE_A
                        | BGFX_STATE_WRITE_Z
                        | BGFX_STATE_DEPTH_TEST_LEQUAL
                        | BGFX_STATE_BLEND_ALPHA
                    );
                    bgfx::submit(MainViewId, view.m_texturedTerrainProgramHandle);
                }
            }

            if (view.m_showBModelWireframe)
            {
                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(0, view.m_bmodelVertexBufferHandle, 0, view.m_bmodelLineVertexCount);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_PT_LINES
                );
                bgfx::submit(MainViewId, view.m_programHandle);
            }
        }

        if (view.m_showBModelCollisionFaces
            && bgfx::isValid(view.m_bmodelCollisionVertexBufferHandle)
            && view.m_bmodelCollisionVertexCount > 0)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(
                0,
                view.m_bmodelCollisionVertexBufferHandle,
                0,
                view.m_bmodelCollisionVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }

        timings.bmodelNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    if (view.m_showEntities
        && bgfx::isValid(view.m_entityMarkerVertexBufferHandle)
        && view.m_entityMarkerVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, view.m_entityMarkerVertexBufferHandle, 0, view.m_entityMarkerVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, view.m_programHandle);
    }

    if (view.m_showActors || view.m_showDecorationBillboards)
    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        OutdoorBillboardRenderer::renderActorPreviewBillboards(view, MainViewId, pViewMatrix, cameraPosition);

        if (view.m_showActors && view.m_showActorCollisionBoxes)
        {
            renderActorCollisionOverlays(view, MainViewId, cameraPosition);
        }

        const uint64_t stageNanoseconds = SDL_GetTicksNS() - stageStartTickCount;
        timings.actorNanoseconds += stageNanoseconds;

        if (view.m_showDecorationBillboards)
        {
            timings.decorationNanoseconds += stageNanoseconds;
        }
    }

    if (view.m_showSpriteObjects)
    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();
        OutdoorBillboardRenderer::renderRuntimeWorldItems(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderRuntimeProjectiles(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderSpriteObjectBillboards(view, MainViewId, pViewMatrix, cameraPosition);
        timings.spriteNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    {
        const uint64_t stageStartTickCount = SDL_GetTicksNS();

        if (view.m_showSpawns
            && bgfx::isValid(view.m_spawnMarkerVertexBufferHandle)
            && view.m_spawnMarkerVertexCount > 0)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, view.m_spawnMarkerVertexBufferHandle, 0, view.m_spawnMarkerVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }

        timings.spawnNanoseconds += SDL_GetTicksNS() - stageStartTickCount;
    }

    if (pAtmosphereState != nullptr && pAtmosphereState->darknessOverlayAlpha > 0.001f)
    {
        renderOutdoorDarknessOverlay(
            view,
            MainViewId,
            cameraPosition,
            cameraForward,
            cameraRight,
            cameraUp,
            aspectRatio,
            pAtmosphereState->darknessOverlayAlpha,
            pAtmosphereState->darknessOverlayColorAbgr);
    }

    return timings;
}

void OutdoorRenderer::renderOutdoorSky(
    OutdoorGameView &view,
    uint16_t viewId,
    uint16_t viewWidth,
    uint16_t viewHeight,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    float renderDistance)
{
    (void)cameraForward;
    (void)cameraRight;
    (void)cameraUp;

    if (!bgfx::isValid(view.m_texturedTerrainProgramHandle) || !bgfx::isValid(view.m_terrainTextureSamplerHandle))
    {
        return;
    }

    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState =
        view.m_pOutdoorWorldRuntime != nullptr ? &view.m_pOutdoorWorldRuntime->atmosphereState() : nullptr;

    if (pAtmosphereState == nullptr)
    {
        return;
    }

    const OutdoorGameView::SkyTextureHandle *pTexture = ensureSkyTexture(view, pAtmosphereState->skyTextureName);

    if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || viewWidth == 0 || viewHeight == 0)
    {
        return;
    }

    const float domeRadius = std::max(renderDistance * 0.85f, 8192.0f);
    const float domeCenterZ = cameraPosition.z - domeRadius * 0.15f;
    const float skyUpdateElapsedTime = std::floor(view.m_elapsedTime * 30.0f) / 30.0f;
    const float horizontalDrift = skyUpdateElapsedTime * 0.0015f;
    const float verticalDrift = skyUpdateElapsedTime * 0.0002f;
    const uint32_t vertexCount = SkyDomeHorizontalSegmentCount * SkyDomeVerticalSegmentCount * 6;

    if (!bgfx::isValid(view.m_skyVertexBufferHandle))
    {
        view.m_skyVertexBufferHandle = bgfx::createDynamicVertexBuffer(
            vertexCount,
            OutdoorGameView::TexturedTerrainVertex::ms_layout,
            BGFX_BUFFER_NONE
        );
    }

    if (!bgfx::isValid(view.m_skyVertexBufferHandle))
    {
        return;
    }

    if (view.m_cachedSkyVertices.size() != vertexCount)
    {
        view.m_cachedSkyVertices.resize(vertexCount);
    }

    if (view.m_lastSkyUpdateElapsedTime != skyUpdateElapsedTime || view.m_cachedSkyTextureName != pTexture->textureName)
    {
        uint32_t vertexIndex = 0;

        for (uint32_t verticalIndex = 0; verticalIndex < SkyDomeVerticalSegmentCount; ++verticalIndex)
        {
            const float phi0 =
                (static_cast<float>(verticalIndex) / static_cast<float>(SkyDomeVerticalSegmentCount))
                * (Pi * 0.5f);
            const float phi1 =
                (static_cast<float>(verticalIndex + 1) / static_cast<float>(SkyDomeVerticalSegmentCount))
                * (Pi * 0.5f);
            const float sinPhi0 = std::sin(phi0);
            const float sinPhi1 = std::sin(phi1);
            const float cosPhi0 = std::cos(phi0);
            const float cosPhi1 = std::cos(phi1);
            const float ringRadius0 = domeRadius * sinPhi0;
            const float ringRadius1 = domeRadius * sinPhi1;
            const float z0 = domeCenterZ + domeRadius * cosPhi0;
            const float z1 = domeCenterZ + domeRadius * cosPhi1;
            const float v0 = (phi0 / (Pi * 0.5f)) * 0.92f + verticalDrift;
            const float v1 = (phi1 / (Pi * 0.5f)) * 0.92f + verticalDrift;

            for (uint32_t horizontalIndex = 0; horizontalIndex < SkyDomeHorizontalSegmentCount; ++horizontalIndex)
            {
                const float theta0 =
                    (static_cast<float>(horizontalIndex) / static_cast<float>(SkyDomeHorizontalSegmentCount))
                    * (Pi * 2.0f);
                const float theta1 =
                    (static_cast<float>(horizontalIndex + 1) / static_cast<float>(SkyDomeHorizontalSegmentCount))
                    * (Pi * 2.0f);
                const float cosTheta0 = std::cos(theta0);
                const float sinTheta0 = std::sin(theta0);
                const float cosTheta1 = std::cos(theta1);
                const float sinTheta1 = std::sin(theta1);
                const float x00 = cameraPosition.x + ringRadius0 * cosTheta0;
                const float y00 = cameraPosition.y + ringRadius0 * sinTheta0;
                const float x01 = cameraPosition.x + ringRadius0 * cosTheta1;
                const float y01 = cameraPosition.y + ringRadius0 * sinTheta1;
                const float x10 = cameraPosition.x + ringRadius1 * cosTheta0;
                const float y10 = cameraPosition.y + ringRadius1 * sinTheta0;
                const float x11 = cameraPosition.x + ringRadius1 * cosTheta1;
                const float y11 = cameraPosition.y + ringRadius1 * sinTheta1;
                const float u0 =
                    static_cast<float>(horizontalIndex) / static_cast<float>(SkyDomeHorizontalSegmentCount)
                    + horizontalDrift;
                const float u1 =
                    static_cast<float>(horizontalIndex + 1) / static_cast<float>(SkyDomeHorizontalSegmentCount)
                    + horizontalDrift;

                view.m_cachedSkyVertices[vertexIndex++] = {x00, y00, z0, u0, v0};
                view.m_cachedSkyVertices[vertexIndex++] = {x10, y10, z1, u0, v1};
                view.m_cachedSkyVertices[vertexIndex++] = {x11, y11, z1, u1, v1};
                view.m_cachedSkyVertices[vertexIndex++] = {x00, y00, z0, u0, v0};
                view.m_cachedSkyVertices[vertexIndex++] = {x11, y11, z1, u1, v1};
                view.m_cachedSkyVertices[vertexIndex++] = {x01, y01, z0, u1, v0};
            }
        }

        bgfx::update(
            view.m_skyVertexBufferHandle,
            0,
            bgfx::copy(
                view.m_cachedSkyVertices.data(),
                static_cast<uint32_t>(
                    view.m_cachedSkyVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))
            )
        );
        view.m_lastSkyUpdateElapsedTime = skyUpdateElapsedTime;
        view.m_cachedSkyTextureName = pTexture->textureName;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, view.m_skyVertexBufferHandle, 0, vertexCount);
    bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, pTexture->textureHandle);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_texturedTerrainProgramHandle);
}

void OutdoorRenderer::renderOutdoorDarknessOverlay(
    OutdoorGameView &view,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    float aspectRatio,
    float overlayAlpha,
    uint32_t overlayColorAbgr)
{
    if (!bgfx::isValid(view.m_programHandle) || overlayAlpha <= 0.0f)
    {
        return;
    }

    const float planeDistance = 1.0f;
    const float planeHalfHeight = std::tan(bx::toRad(CameraVerticalFovDegrees * 0.5f)) * planeDistance;
    const float planeHalfWidth = planeHalfHeight * std::max(aspectRatio, 0.1f);
    const bx::Vec3 overlayCenter = {
        cameraPosition.x + cameraForward.x * planeDistance,
        cameraPosition.y + cameraForward.y * planeDistance,
        cameraPosition.z + cameraForward.z * planeDistance
    };
    const bx::Vec3 planeRight = {
        cameraRight.x * planeHalfWidth,
        cameraRight.y * planeHalfWidth,
        cameraRight.z * planeHalfWidth
    };
    const bx::Vec3 planeUp = {
        cameraUp.x * planeHalfHeight,
        cameraUp.y * planeHalfHeight,
        cameraUp.z * planeHalfHeight
    };
    const uint8_t alpha = static_cast<uint8_t>(std::clamp(std::lround(overlayAlpha * 255.0f), 0l, 255l));
    const uint32_t abgr = (overlayColorAbgr & 0x00ffffffu) | (static_cast<uint32_t>(alpha) << 24);
    const std::array<OutdoorGameView::TerrainVertex, 6> vertices = {{
        {overlayCenter.x - planeRight.x + planeUp.x, overlayCenter.y - planeRight.y + planeUp.y, overlayCenter.z - planeRight.z + planeUp.z, abgr},
        {overlayCenter.x - planeRight.x - planeUp.x, overlayCenter.y - planeRight.y - planeUp.y, overlayCenter.z - planeRight.z - planeUp.z, abgr},
        {overlayCenter.x + planeRight.x - planeUp.x, overlayCenter.y + planeRight.y - planeUp.y, overlayCenter.z + planeRight.z - planeUp.z, abgr},
        {overlayCenter.x - planeRight.x + planeUp.x, overlayCenter.y - planeRight.y + planeUp.y, overlayCenter.z - planeRight.z + planeUp.z, abgr},
        {overlayCenter.x + planeRight.x - planeUp.x, overlayCenter.y + planeRight.y - planeUp.y, overlayCenter.z + planeRight.z - planeUp.z, abgr},
        {overlayCenter.x + planeRight.x + planeUp.x, overlayCenter.y + planeRight.y + planeUp.y, overlayCenter.z + planeRight.z + planeUp.z, abgr}
    }};

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, OutdoorGameView::TerrainVertex::ms_layout);
    std::memcpy(transientVertexBuffer.data, vertices.data(), sizeof(vertices));

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, 6);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_programHandle);
}

void OutdoorRenderer::renderActorCollisionOverlays(
    OutdoorGameView &view,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition)
{
    if (!view.m_showActorCollisionBoxes
        || (!view.m_outdoorActorPreviewBillboardSet && view.m_pOutdoorWorldRuntime == nullptr))
    {
        return;
    }

    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const size_t billboardCount =
        view.m_outdoorActorPreviewBillboardSet ? view.m_outdoorActorPreviewBillboardSet->billboards.size() : 0;
    const size_t runtimeActorCount =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapActorCount() : 0;
    vertices.reserve((billboardCount + runtimeActorCount) * 24);
    std::vector<bool> coveredRuntimeActors;

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(view.m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    const auto appendLine =
        [&vertices](const bx::Vec3 &start, const bx::Vec3 &end, uint32_t color)
        {
            vertices.push_back({start.x, start.y, start.z, color});
            vertices.push_back({end.x, end.y, end.z, color});
        };

    const auto appendActorOverlay =
        [&view, &appendLine](
            int actorX,
            int actorY,
            int actorZ,
            uint16_t actorRadius,
            uint16_t actorHeight,
            bool isDead,
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
            const float minZ = view.m_outdoorMapData.has_value()
                ? resolveActorAabbBaseZ(
                    *view.m_outdoorMapData,
                    nullptr,
                    actorX,
                    actorY,
                    actorZ,
                    isDead)
                : static_cast<float>(actorZ);
            const float maxZ = minZ + height;

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

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        for (const ActorPreviewBillboard &billboard : view.m_outdoorActorPreviewBillboardSet->billboards)
        {
            if (billboard.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = OutdoorInteractionController::runtimeActorStateForBillboard(view, billboard);

            if (pRuntimeActor != nullptr && billboard.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[billboard.runtimeActorIndex] = true;
            }

            if (pRuntimeActor != nullptr && pRuntimeActor->isInvisible)
            {
                continue;
            }

            const float overlayDeltaX =
                static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->x : -billboard.x) - cameraPosition.x;
            const float overlayDeltaY =
                static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y) - cameraPosition.y;
            const float overlayDeltaZ =
                static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z) - cameraPosition.z;
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
                pRuntimeActor != nullptr ? pRuntimeActor->isDead : false,
                pRuntimeActor != nullptr ? pRuntimeActor->hostileToParty : !billboard.isFriendly);
        }
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

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
                pRuntimeActor->isDead,
                pRuntimeActor->hostileToParty);
        }
    }

    if (vertices.empty())
    {
        return;
    }

    if (bgfx::getAvailTransientVertexBuffer(
            static_cast<uint32_t>(vertices.size()),
            OutdoorGameView::TerrainVertex::ms_layout) < vertices.size())
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &transientVertexBuffer,
        static_cast<uint32_t>(vertices.size()),
        OutdoorGameView::TerrainVertex::ms_layout
    );
    std::memcpy(
        transientVertexBuffer.data,
        vertices.data(),
        static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TerrainVertex))
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
    bgfx::submit(viewId, view.m_programHandle);
}

} // namespace OpenYAMM::Game
