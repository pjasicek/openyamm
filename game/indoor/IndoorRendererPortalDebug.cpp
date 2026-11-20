// The indoor portal and visibility debug view (console `portals`, tools/RUN_GAME.md "Indoor portal view"): portal
// faces, the drawn sectors, and the per-frame counts and timings of the visibility and the passes. Every function here
// runs only while the view is on.
#include "game/indoor/IndoorRenderer.h"

#include "game/render/CinematicGrading.h"
#include "game/render/ViewFrustum.h"
#include "game/render/WaterMath.h"

#include <SDL3/SDL_timer.h>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <sstream>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
// Translucent cyan, as the editor draws portals: the traversed ones brighter.
constexpr uint32_t PortalFaceAbgr = 0x30ffff00u;
constexpr uint32_t TraversedPortalFaceAbgr = 0x70ffff00u;
constexpr uint32_t TraversedPortalEdgeAbgr = 0xffffff00u;
// Overlay lines are pulled this share of the way to the eye so they win the depth test over their own faces.
constexpr float OverlayEyePull = 0.004f;
// A face's bounding sphere grows by this much in the frustum tests, as the billboards' (BillboardFrustumSlack).
constexpr float FrustumSlack = 8.0f;

struct Bounds
{
    bx::Vec3 min = {0.0f, 0.0f, 0.0f};
    bx::Vec3 max = {0.0f, 0.0f, 0.0f};
    bool valid = false;

    void include(const bx::Vec3 &point)
    {
        if (!valid)
        {
            min = point;
            max = point;
            valid = true;
            return;
        }
        min = {std::min(min.x, point.x), std::min(min.y, point.y), std::min(min.z, point.z)};
        max = {std::max(max.x, point.x), std::max(max.y, point.y), std::max(max.z, point.z)};
    }

    void include(const Bounds &other)
    {
        if (other.valid)
        {
            include(other.min);
            include(other.max);
        }
    }
};

bool boundsInFrustums(const Bounds &bounds, const std::vector<IndoorVisibilityFrustum> &frustums)
{
    const bx::Vec3 center = {(bounds.min.x + bounds.max.x) * 0.5f, (bounds.min.y + bounds.max.y) * 0.5f,
        (bounds.min.z + bounds.max.z) * 0.5f};
    const bx::Vec3 half = {bounds.max.x - center.x, bounds.max.y - center.y, bounds.max.z - center.z};
    const float radius = std::sqrt(half.x * half.x + half.y * half.y + half.z * half.z) + FrustumSlack;
    for (const IndoorVisibilityFrustum &frustum : frustums)
    {
        bool inside = true;
        for (const IndoorVisibilityPlane &plane : frustum)
        {
            const float distance = plane.normal.x * center.x + plane.normal.y * center.y
                + plane.normal.z * center.z + plane.distance;
            if (distance < -radius)
            {
                inside = false;
                break;
            }
        }
        if (inside)
        {
            return true;
        }
    }
    return false;
}

bool sectorVisible(const std::vector<uint8_t> &mask, int16_t sectorId)
{
    return sectorId >= 0 && size_t(sectorId) < mask.size() && mask[size_t(sectorId)] != 0;
}

const std::vector<IndoorVisibilityFrustum> &sectorFrustums(
    const std::vector<std::vector<IndoorVisibilityFrustum>> &frustums, int16_t sectorId)
{
    static const std::vector<IndoorVisibilityFrustum> none;
    return sectorId >= 0 && size_t(sectorId) < frustums.size() ? frustums[size_t(sectorId)] : none;
}
}

void IndoorRenderer::setPortalDebugSettings(const IndoorPortalDebugSettings &settings)
{
    if (settings.cullingOff != m_portalDebug.cullingOff)
    {
        clearPortalVisibilityCaches();
    }
    m_portalDebug = settings;
    if (!m_portalDebug.active())
    {
        m_portalDebugStats = {};
        std::vector<std::vector<uint32_t>>().swap(m_portalDebugBatchFaces);
        m_portalDebugBatchFacesRevision = std::numeric_limits<uint64_t>::max();
        m_renderPortalVisibilityCache.acceptedPortals.clear();
        m_renderPortalVisibilityCache.nodeSectorIds.clear();
    }
    else
    {
        // The next frame rebuilds the visibility, so the traversed portals and nodes are recorded at once.
        m_renderPortalVisibilityCache.valid = false;
    }
}

uint16_t IndoorRenderer::portalDebugPassView(IndoorDebugPass pass, uint16_t normalView) const
{
    return m_portalDebug.gpuPasses ? uint16_t(FirstIndoorDebugPassView + uint16_t(pass)) : normalView;
}

void IndoorRenderer::preparePortalDebugPassViews(
    int width, int height, const float *pViewMatrix, const float *pProjectionMatrix)
{
    if (!m_portalDebug.gpuPasses)
    {
        if (m_portalDebugPassViewsBound)
        {
            for (uint16_t view = FirstIndoorDebugPassView; view < FirstIndoorDebugPassView + IndoorDebugPassViews;
                ++view)
            {
                bgfx::setViewFrameBuffer(view, BGFX_INVALID_HANDLE);
            }
            m_portalDebugPassViewsBound = false;
        }
        return;
    }
    // Each pass view draws into the world target after view 0, with its transform and no clear: the same picture.
    const bgfx::FrameBufferHandle target = m_pPostProcessing != nullptr
        ? m_pPostProcessing->worldFrameBuffer() : bgfx::FrameBufferHandle(BGFX_INVALID_HANDLE);
    for (uint16_t pass = 0; pass < uint16_t(IndoorDebugPass::Count); ++pass)
    {
        const uint16_t view = uint16_t(FirstIndoorDebugPassView + pass);
        bgfx::setViewName(view, indoorDebugPassName(IndoorDebugPass(pass)));
        bgfx::setViewFrameBuffer(view, target);
        bgfx::setViewRect(view, 0, 0, uint16_t(std::max(width, 1)), uint16_t(std::max(height, 1)));
        bgfx::setViewMode(view, bgfx::ViewMode::Sequential);
        bgfx::setViewClear(view, BGFX_CLEAR_NONE);
        bgfx::setViewTransform(view, pViewMatrix, pProjectionMatrix);
        bgfx::touch(view);
    }
    m_portalDebugPassViewsBound = true;
}

void IndoorRenderer::collectPortalDebugStats(const std::vector<uint8_t> &visibleSectorMask, const float *pViewMatrix,
    const float *pProjectionMatrix, const bx::Vec3 &eye)
{
    IndoorPortalDebugStats &stats = m_portalDebugStats;
    const PortalVisibilityCache &cache = m_renderPortalVisibilityCache;
    stats.valid = m_pIndoorMapData != nullptr;
    if (!stats.valid)
    {
        return;
    }
    const IndoorMapData &mapData = *m_pIndoorMapData;
    const size_t sectorCount = mapData.sectors.size();
    stats.eyeSectorId = cache.valid ? cache.sectorId : int16_t(-1);
    stats.eye = {eye.x, eye.y, eye.z};
    stats.yawRadians = m_cameraYawRadians;
    stats.pitchRadians = m_cameraPitchRadians;
    stats.sectorsDrawn = uint32_t(std::count_if(visibleSectorMask.begin(), visibleSectorMask.end(),
        [](uint8_t visible) { return visible != 0; }));
    stats.visibilityNodes = uint32_t(cache.nodeSectorIds.size());
    stats.portalsTested = cache.portalCandidateCount;
    stats.portalsTraversed = cache.acceptedPortalCount;
    stats.portalsRejectedFacing = cache.directionRejectedPortalCount;
    stats.portalsRejectedClipped = cache.clippedPortalRejectedCount;
    stats.portalsRejectedOther = cache.rejectedPortalCount >= cache.directionRejectedPortalCount
            + cache.clippedPortalRejectedCount
        ? cache.rejectedPortalCount - cache.directionRejectedPortalCount - cache.clippedPortalRejectedCount : 0;
    stats.visibilityBuildNanoseconds = cache.buildNanoseconds;

    // Each batch's faces, once per rebuild of the batches.
    if (m_portalDebugBatchFacesRevision != m_texturedBatchGeometryRevision
        || m_portalDebugBatchFacesBatchCount != m_texturedBatches.size())
    {
        m_portalDebugBatchFaces.assign(m_texturedBatches.size(), {});
        for (size_t faceIndex = 0; faceIndex < m_faceBatchIndices.size(); ++faceIndex)
        {
            const int32_t batchIndex = m_faceBatchIndices[faceIndex];
            if (batchIndex >= 0 && size_t(batchIndex) < m_portalDebugBatchFaces.size())
            {
                m_portalDebugBatchFaces[size_t(batchIndex)].push_back(uint32_t(faceIndex));
            }
        }
        m_portalDebugBatchFacesRevision = m_texturedBatchGeometryRevision;
        m_portalDebugBatchFacesBatchCount = m_texturedBatches.size();
    }

    std::vector<IndoorPortalDebugSector> sectors(sectorCount);
    for (size_t sectorId = 0; sectorId < sectorCount; ++sectorId)
    {
        sectors[sectorId].sectorId = int16_t(sectorId);
        if (m_indoorPortalGraph && sectorId < m_indoorPortalGraph->sectors.size())
        {
            sectors[sectorId].portalLinks = uint32_t(m_indoorPortalGraph->sectors[sectorId].portalLinkIds.size());
        }
    }
    for (int16_t sectorId : cache.nodeSectorIds)
    {
        if (sectorId >= 0 && size_t(sectorId) < sectorCount)
        {
            ++sectors[size_t(sectorId)].nodes;
            sectors[size_t(sectorId)].portalsTested += sectors[size_t(sectorId)].portalLinks;
        }
    }

    const ViewFrustum viewFrustum(pViewMatrix, pProjectionMatrix, bgfx::getCaps()->homogeneousDepth);
    const bool enhancedWater = m_waterRenderer.isReady();
    const float tileSize = std::max(m_portalDebug.tileSize, 64.0f);
    stats.batchesSubmitted = 0;
    stats.facesSubmitted = 0;
    stats.trianglesSubmitted = 0;
    stats.facesInView = 0;
    stats.facesInPortals = 0;
    stats.trianglesInPortals = 0;
    stats.tileDraws = 0;
    stats.tileTriangles = 0;
    struct Tile
    {
        Bounds bounds;
        float triangles = 0.0f;
    };
    std::unordered_map<uint64_t, Tile> tiles;
    std::unordered_set<std::string> textures;

    for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
    {
        const TexturedBatch &batch = m_texturedBatches[batchIndex];
        if (batch.translucent || (enhancedWater && batch.waterColorAbgr != 0) || batch.vertexCount == 0)
        {
            continue;
        }
        if (batchIndex >= m_portalDebugBatchFaces.size())
        {
            break;
        }
        const std::vector<uint32_t> &faces = m_portalDebugBatchFaces[batchIndex];
        if (batch.sectorId >= 0 && size_t(batch.sectorId) < sectorCount)
        {
            sectors[size_t(batch.sectorId)].totalFaces += uint32_t(faces.size());
        }
        if (!indoorGeometrySectorsVisible(visibleSectorMask, batch.sectorId, batch.backSectorId))
        {
            continue;
        }
        // Counted for the visible one of its two sectors (the front when both are).
        const int16_t sectorId =
            sectorVisible(visibleSectorMask, batch.sectorId) ? batch.sectorId : batch.backSectorId;
        IndoorPortalDebugSector *pSector =
            sectorId >= 0 && size_t(sectorId) < sectorCount ? &sectors[size_t(sectorId)] : nullptr;
        const uint32_t batchTriangles = batch.indexCount / 3;
        ++stats.batchesSubmitted;
        stats.trianglesSubmitted += batchTriangles;
        textures.insert(batch.textureName + "#" + std::to_string(batch.lightmapPage));
        if (pSector != nullptr)
        {
            ++pSector->batches;
            pSector->triangles += batchTriangles;
        }
        const std::vector<IndoorVisibilityFrustum> &frontFrustums =
            sectorFrustums(cache.visibleSectorFrustums, batch.sectorId);
        const std::vector<IndoorVisibilityFrustum> &backFrustums =
            sectorFrustums(cache.visibleSectorFrustums, batch.backSectorId);
        tiles.clear();
        for (uint32_t faceIndex : faces)
        {
            const uint32_t offset = faceIndex < m_faceVertexOffsets.size() ? m_faceVertexOffsets[faceIndex] : 0;
            const uint32_t count = faceIndex < m_faceVertexCounts.size() ? m_faceVertexCounts[faceIndex] : 0;
            Bounds bounds;
            for (uint32_t vertex = offset; vertex < offset + count && vertex < batch.vertices.size(); ++vertex)
            {
                bounds.include({batch.vertices[vertex].x, batch.vertices[vertex].y, batch.vertices[vertex].z});
            }
            if (!bounds.valid)
            {
                continue;
            }
            // The face's share of its batch's triangles, by its vertices.
            const float faceTriangles =
                float(batchTriangles) * float(count) / float(std::max(batch.vertexCount, 1u));
            ++stats.facesSubmitted;
            const bool inView = viewFrustum.intersectsBounds(bounds.min, bounds.max);
            const bool inPortals = (sectorVisible(visibleSectorMask, batch.sectorId)
                    && boundsInFrustums(bounds, frontFrustums))
                || (sectorVisible(visibleSectorMask, batch.backSectorId) && boundsInFrustums(bounds, backFrustums));
            stats.facesInView += inView ? 1 : 0;
            stats.facesInPortals += inPortals ? 1 : 0;
            stats.trianglesInPortals += inPortals ? uint32_t(std::lround(faceTriangles)) : 0;
            if (pSector != nullptr)
            {
                ++pSector->faces;
                pSector->facesInView += inView ? 1 : 0;
                pSector->facesInPortals += inPortals ? 1 : 0;
                pSector->trianglesInPortals += inPortals ? uint32_t(std::lround(faceTriangles)) : 0;
            }
            const int32_t cellX = int32_t(std::floor((bounds.min.x + bounds.max.x) * 0.5f / tileSize));
            const int32_t cellY = int32_t(std::floor((bounds.min.y + bounds.max.y) * 0.5f / tileSize));
            Tile &tile = tiles[(uint64_t(uint32_t(cellX)) << 32) | uint32_t(cellY)];
            tile.bounds.include(bounds);
            tile.triangles += faceTriangles;
        }
        for (const auto &[key, tile] : tiles)
        {
            const bool inPortals = (sectorVisible(visibleSectorMask, batch.sectorId)
                    && boundsInFrustums(tile.bounds, frontFrustums))
                || (sectorVisible(visibleSectorMask, batch.backSectorId)
                    && boundsInFrustums(tile.bounds, backFrustums));
            if (!inPortals)
            {
                continue;
            }
            ++stats.tileDraws;
            stats.tileTriangles += uint32_t(std::lround(tile.triangles));
            if (pSector != nullptr)
            {
                ++pSector->tileDraws;
                pSector->tileTriangles += uint32_t(std::lround(tile.triangles));
            }
        }
    }

    stats.batchTextures = uint32_t(textures.size());
    // The batches drawn merged by group (IndoorFaceDrawGroups.h): this frame's world face draw calls.
    stats.faceDraws = uint32_t(m_faceDrawPlan.draws().size());
    stats.sectors.clear();
    for (const IndoorPortalDebugSector &sector : sectors)
    {
        if (sectorVisible(visibleSectorMask, sector.sectorId))
        {
            stats.sectors.push_back(sector);
        }
    }
    std::sort(stats.sectors.begin(), stats.sectors.end(),
        [](const IndoorPortalDebugSector &left, const IndoorPortalDebugSector &right)
        {
            return left.faces != right.faces ? left.faces > right.faces : left.sectorId < right.sectorId;
        });

    stats.labels.clear();
    for (const IndoorAcceptedPortalVisibility &portal : cache.acceptedPortals)
    {
        if (portal.faceId >= mapData.faces.size())
        {
            continue;
        }
        const IndoorFace &face = mapData.faces[portal.faceId];
        bx::Vec3 sum = {0.0f, 0.0f, 0.0f};
        size_t count = 0;
        for (uint16_t vertexId : face.vertexIndices)
        {
            if (vertexId < m_renderVertices.size())
            {
                sum.x += float(m_renderVertices[vertexId].x);
                sum.y += float(m_renderVertices[vertexId].y);
                sum.z += float(m_renderVertices[vertexId].z);
                ++count;
            }
        }
        if (count > 0)
        {
            stats.labels.push_back({{sum.x / float(count), sum.y / float(count), sum.z / float(count)},
                portal.targetSectorId});
        }
    }
}

void IndoorRenderer::renderPortalDebugOverlay(uint16_t viewId, const std::vector<uint8_t> &visibleSectorMask)
{
    if (m_pIndoorMapData == nullptr || !bgfx::isValid(m_programHandle))
    {
        return;
    }
    const IndoorMapData &mapData = *m_pIndoorMapData;
    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    const auto vertexAt = [&](uint16_t vertexId, uint32_t abgr) -> TerrainVertex
    {
        const IndoorVertex &vertex = m_renderVertices[vertexId];
        const float x = float(vertex.x);
        const float y = float(vertex.y);
        const float z = float(vertex.z);
        return {x + (eye.x - x) * OverlayEyePull, y + (eye.y - y) * OverlayEyePull, z + (eye.z - z) * OverlayEyePull,
            abgr};
    };
    const auto faceUsable = [&](size_t faceId)
    {
        if (faceId >= mapData.faces.size() || mapData.faces[faceId].vertexIndices.size() < 2)
        {
            return false;
        }
        for (uint16_t vertexId : mapData.faces[faceId].vertexIndices)
        {
            if (vertexId >= m_renderVertices.size())
            {
                return false;
            }
        }
        return true;
    };
    const auto submit = [&](std::vector<TerrainVertex> &vertices, uint64_t primitiveState, uint64_t blendState)
    {
        uint32_t count = uint32_t(vertices.size());
        const uint32_t step = (primitiveState & BGFX_STATE_PT_LINES) != 0 ? 2 : 3;
        count = std::min(count, bgfx::getAvailTransientVertexBuffer(count, TerrainVertex::ms_layout));
        count -= count % step;
        if (count == 0)
        {
            return;
        }
        bgfx::TransientVertexBuffer buffer = {};
        bgfx::allocTransientVertexBuffer(&buffer, count, TerrainVertex::ms_layout);
        std::memcpy(buffer.data, vertices.data(), count * sizeof(TerrainVertex));
        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &buffer, 0, count);
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_DEPTH_TEST_LEQUAL | primitiveState | blendState);
        bgfx::submit(viewId, m_programHandle);
    };

    if (m_portalDebug.sectors)
    {
        // The drawn sectors' faces, outlined in each sector's colour.
        std::vector<TerrainVertex> lines;
        const size_t batchCount = std::min(m_texturedBatches.size(), m_portalDebugBatchFaces.size());
        for (size_t batchIndex = 0; batchIndex < batchCount; ++batchIndex)
        {
            const TexturedBatch &batch = m_texturedBatches[batchIndex];
            if (!indoorGeometrySectorsVisible(visibleSectorMask, batch.sectorId, batch.backSectorId))
            {
                continue;
            }
            const int16_t sectorId =
                sectorVisible(visibleSectorMask, batch.sectorId) ? batch.sectorId : batch.backSectorId;
            const uint32_t color = indoorPortalDebugSectorColor(sectorId);
            for (uint32_t faceId : m_portalDebugBatchFaces[batchIndex])
            {
                if (!faceUsable(faceId))
                {
                    continue;
                }
                const std::vector<uint16_t> &indices = mapData.faces[faceId].vertexIndices;
                for (size_t index = 0; index < indices.size(); ++index)
                {
                    lines.push_back(vertexAt(indices[index], color));
                    lines.push_back(vertexAt(indices[(index + 1) % indices.size()], color));
                }
            }
        }
        submit(lines, BGFX_STATE_PT_LINES, 0);
    }

    if (m_portalDebug.faces != IndoorPortalDebugFaces::Off)
    {
        std::vector<uint8_t> traversed(mapData.faces.size(), 0);
        for (const IndoorAcceptedPortalVisibility &portal : m_renderPortalVisibilityCache.acceptedPortals)
        {
            if (portal.faceId < traversed.size())
            {
                traversed[portal.faceId] = 1;
            }
        }
        std::vector<TerrainVertex> triangles;
        std::vector<TerrainVertex> edges;
        for (size_t faceId = 0; faceId < mapData.faces.size(); ++faceId)
        {
            const bool isTraversed = traversed[faceId] != 0;
            if (!mapData.faces[faceId].isPortal
                || (m_portalDebug.faces == IndoorPortalDebugFaces::Traversed && !isTraversed) || !faceUsable(faceId))
            {
                continue;
            }
            const std::vector<uint16_t> &indices = mapData.faces[faceId].vertexIndices;
            const uint32_t color = isTraversed ? TraversedPortalFaceAbgr : PortalFaceAbgr;
            for (size_t index = 1; index + 1 < indices.size(); ++index)
            {
                triangles.push_back(vertexAt(indices[0], color));
                triangles.push_back(vertexAt(indices[index], color));
                triangles.push_back(vertexAt(indices[index + 1], color));
            }
            if (isTraversed)
            {
                for (size_t index = 0; index < indices.size(); ++index)
                {
                    edges.push_back(vertexAt(indices[index], TraversedPortalEdgeAbgr));
                    edges.push_back(vertexAt(indices[(index + 1) % indices.size()], TraversedPortalEdgeAbgr));
                }
            }
        }
        submit(triangles, 0, BGFX_STATE_BLEND_ALPHA);
        submit(edges, BGFX_STATE_PT_LINES, 0);
    }
}

std::vector<std::string> IndoorRenderer::portalDebugSectorSummary() const
{
    std::vector<std::string> lines;
    if (m_pIndoorMapData == nullptr)
    {
        return lines;
    }
    const IndoorMapData &mapData = *m_pIndoorMapData;
    std::vector<uint32_t> drawnFaces(mapData.sectors.size(), 0);
    for (size_t faceIndex = 0; faceIndex < m_faceBatchIndices.size() && faceIndex < mapData.faces.size(); ++faceIndex)
    {
        const int32_t batchIndex = m_faceBatchIndices[faceIndex];
        const uint16_t sectorId = mapData.faces[faceIndex].roomNumber;
        if (batchIndex >= 0 && size_t(batchIndex) < m_texturedBatches.size()
            && !m_texturedBatches[size_t(batchIndex)].translucent && sectorId < drawnFaces.size())
        {
            ++drawnFaces[sectorId];
        }
    }
    for (size_t sectorId = 0; sectorId < mapData.sectors.size(); ++sectorId)
    {
        const IndoorSector &sector = mapData.sectors[sectorId];
        const size_t links = m_indoorPortalGraph && sectorId < m_indoorPortalGraph->sectors.size()
            ? m_indoorPortalGraph->sectors[sectorId].portalLinkIds.size() : 0;
        std::ostringstream line;
        line << "sector=" << sectorId << " faces=" << sector.faceIds.size() << " drawn_faces=" << drawnFaces[sectorId]
             << " portal_faces=" << sector.portalFaceIds.size() << " portal_links=" << links
             << " open_sky=" << (indoorDaylightSector(m_daylight, int(sectorId)) ? 1 : 0)
             << " bounds=" << sector.minX << ',' << sector.minY << ',' << sector.minZ << ".." << sector.maxX << ','
             << sector.maxY << ',' << sector.maxZ;
        lines.push_back(line.str());
    }
    return lines;
}
}
