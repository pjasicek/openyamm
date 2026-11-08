#include "game/indoor/IndoorSectorFaceGrid.h"

#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/MapDeltaData.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
// About the PathMap's cell; a big sector is cut into at most MaxCellsPerAxis cells along each axis.
constexpr float GridCellSize = 256.0f;
constexpr int32_t MaxCellsPerAxis = 128;
// Sectors this small (all MM6-MM8 corridors) keep a single cell: the grid would save nothing.
constexpr size_t SingleCellFaceLimit = 32;
// Face bounds are widened by the point lookup's slack plus a margin for the rounding of cell indices.
constexpr float FacePadding = IndoorSectorFaceGrid::PointSlack + 2.0f;

struct FaceBounds
{
    bool placed = false;
    float minX = 0.0f;
    float maxX = 0.0f;
    float minY = 0.0f;
    float maxY = 0.0f;
};

// The x/y bounds every face can take, widened so that any point a query can accept lies inside them.
// A face whose vertices leave its plane is widened by that distance along its normal's dominant axis: a hit point
// on the plane inside the projected polygon can lie that far outside the vertices' bounds.
// A face a sliding door moves is placed by the bounds of its whole travel: each of its vertices runs on a straight line
// between the door's two end poses (distance 0 and the move length), so the bounds of both poses hold every pose
// between. A face a rotating or spinning mover moves (or without usable geometry) is not placed.
std::vector<FaceBounds> buildPlacedFaceBounds(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const MapDeltaData *pMapDeltaData)
{
    struct VertexTravel
    {
        // The doors that move the vertex: 0 none, 1 one sliding door (`doorIndex`), 2 several, 3 a rotating mover.
        uint8_t kind = 0;
        size_t doorIndex = 0;
        bx::Vec3 min = {0.0f, 0.0f, 0.0f};
        bx::Vec3 max = {0.0f, 0.0f, 0.0f};
    };

    std::vector<VertexTravel> vertexTravel(vertices.size());

    if (pMapDeltaData != nullptr)
    {
        for (size_t doorIndex = 0; doorIndex < pMapDeltaData->doors.size(); ++doorIndex)
        {
            const MapDeltaDoor &door = pMapDeltaData->doors[doorIndex];
            const IndoorMoverDefinition *pMover = findIndoorMoverDefinition(indoorMapData, door.doorId);
            const bool sliding = pMover == nullptr || (!pMover->rotation && !pMover->spin);
            const size_t offsetCount =
                std::min(door.xOffsets.size(), std::min(door.yOffsets.size(), door.zOffsets.size()));
            const float moveLength = static_cast<float>(door.moveLength);
            const bx::Vec3 travel = {
                fixedIndoorDoorDirectionComponentToFloat(door.directionX) * moveLength,
                fixedIndoorDoorDirectionComponentToFloat(door.directionY) * moveLength,
                fixedIndoorDoorDirectionComponentToFloat(door.directionZ) * moveLength};

            for (size_t index = 0; index < door.vertexIds.size(); ++index)
            {
                const uint16_t vertexId = door.vertexIds[index];

                if (vertexId >= vertexTravel.size())
                {
                    continue;
                }

                VertexTravel &entry = vertexTravel[vertexId];

                if (!sliding || index >= offsetCount)
                {
                    entry.kind = 3;
                    continue;
                }

                const bx::Vec3 closed = {static_cast<float>(door.xOffsets[index]),
                    static_cast<float>(door.yOffsets[index]), static_cast<float>(door.zOffsets[index])};
                const bx::Vec3 opened = {closed.x + travel.x, closed.y + travel.y, closed.z + travel.z};
                const bx::Vec3 low = {
                    std::min(closed.x, opened.x), std::min(closed.y, opened.y), std::min(closed.z, opened.z)};
                const bx::Vec3 high = {
                    std::max(closed.x, opened.x), std::max(closed.y, opened.y), std::max(closed.z, opened.z)};

                if (entry.kind == 0)
                {
                    entry.kind = 1;
                    entry.doorIndex = doorIndex;
                    entry.min = low;
                    entry.max = high;
                }
                else if (entry.kind != 3)
                {
                    entry.kind = entry.kind == 1 && entry.doorIndex == doorIndex ? uint8_t(1) : uint8_t(2);
                    entry.min = {std::min(entry.min.x, low.x), std::min(entry.min.y, low.y),
                        std::min(entry.min.z, low.z)};
                    entry.max = {std::max(entry.max.x, high.x), std::max(entry.max.y, high.y),
                        std::max(entry.max.z, high.z)};
                }
            }
        }
    }

    std::vector<FaceBounds> bounds(indoorMapData.faces.size());
    IndoorFaceGeometryData geometry = {};

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];
        // A face a door lists whose vertices all stay put keeps its place.
        bool moving = false;
        bool rotating = false;
        // Every vertex moved by the same sliding door: the face keeps its shape along the travel.
        bool rigid = !face.vertexIndices.empty();
        std::optional<size_t> rigidDoorIndex;
        bx::Vec3 travelMin = {std::numeric_limits<float>::max(), std::numeric_limits<float>::max(),
            std::numeric_limits<float>::max()};
        bx::Vec3 travelMax = {std::numeric_limits<float>::lowest(), std::numeric_limits<float>::lowest(),
            std::numeric_limits<float>::lowest()};

        for (uint16_t vertexId : face.vertexIndices)
        {
            if (vertexId >= vertexTravel.size())
            {
                rigid = false;
                continue;
            }

            const VertexTravel &entry = vertexTravel[vertexId];
            bx::Vec3 low = {static_cast<float>(vertices[vertexId].x), static_cast<float>(vertices[vertexId].y),
                static_cast<float>(vertices[vertexId].z)};
            bx::Vec3 high = low;
            moving = moving || entry.kind != 0;
            rotating = rotating || entry.kind == 3;

            if (entry.kind == 1 || entry.kind == 2)
            {
                low = entry.min;
                high = entry.max;
            }

            if (entry.kind != 1 || (rigidDoorIndex && *rigidDoorIndex != entry.doorIndex))
            {
                rigid = false;
            }

            rigidDoorIndex = entry.doorIndex;
            travelMin = {std::min(travelMin.x, low.x), std::min(travelMin.y, low.y), std::min(travelMin.z, low.z)};
            travelMax = {std::max(travelMax.x, high.x), std::max(travelMax.y, high.y), std::max(travelMax.z, high.z)};
        }

        const bool hasGeometry = buildIndoorFaceGeometry(indoorMapData, vertices, faceIndex, geometry);

        // A stretched face is placed by its vertices alone: it may have no usable geometry in the present pose only.
        if (rotating || (!hasGeometry && !(moving && !rigid)))
        {
            continue;
        }

        float planeDeviation = 0.0f;

        if (moving && !rigid)
        {
            // A face the door stretches changes its plane on the way. A point on any plane through one of its
            // vertices, inside the polygon projected along that plane's dominant axis, lies within the sum of the
            // other two extents of that vertex along the dominant axis.
            if (face.vertexIndices.empty() || travelMin.x > travelMax.x)
            {
                continue;
            }

            const float extentX = travelMax.x - travelMin.x;
            const float extentY = travelMax.y - travelMin.y;
            const float extentZ = travelMax.z - travelMin.z;
            planeDeviation = extentX + extentY + extentZ;
        }
        else
        {
            const float dominantNormal =
                std::max({std::fabs(geometry.normal.x), std::fabs(geometry.normal.y), std::fabs(geometry.normal.z)});

            if (geometry.hasPlane && dominantNormal > 0.0f)
            {
                const bx::Vec3 &origin = geometry.vertices.front();

                for (const bx::Vec3 &vertex : geometry.vertices)
                {
                    const float distance = (vertex.x - origin.x) * geometry.normal.x
                        + (vertex.y - origin.y) * geometry.normal.y
                        + (vertex.z - origin.z) * geometry.normal.z;
                    planeDeviation = std::max(planeDeviation, std::fabs(distance) / dominantNormal);
                }
            }
        }

        const float padding = FacePadding + planeDeviation;
        FaceBounds &faceBounds = bounds[faceIndex];
        faceBounds.placed = true;

        if (moving)
        {
            faceBounds.minX = travelMin.x - padding;
            faceBounds.maxX = travelMax.x + padding;
            faceBounds.minY = travelMin.y - padding;
            faceBounds.maxY = travelMax.y + padding;
        }
        else
        {
            faceBounds.minX = geometry.minX - padding;
            faceBounds.maxX = geometry.maxX + padding;
            faceBounds.minY = geometry.minY - padding;
            faceBounds.maxY = geometry.maxY + padding;
        }
    }

    return bounds;
}

int32_t clampedCell(float coordinate, float origin, float cellSize, int32_t cellCount)
{
    const float cell = std::floor((coordinate - origin) / cellSize);

    if (!(cell >= 0.0f))
    {
        return 0;
    }

    return cell >= static_cast<float>(cellCount - 1) ? cellCount - 1 : static_cast<int32_t>(cell);
}
}

void IndoorSectorFaceGrid::build(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const MapDeltaData *pMapDeltaData)
{
    m_sectors.clear();
    m_sectors.resize(indoorMapData.sectors.size());
    const std::vector<FaceBounds> faceBounds = buildPlacedFaceBounds(indoorMapData, vertices, pMapDeltaData);
    std::vector<size_t> sectorVisits(indoorMapData.faces.size(), std::numeric_limits<size_t>::max());

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorIndex];
        SectorGrid &grid = m_sectors[sectorIndex];

        // The sector's collision faces, each once, in list order.
        std::vector<uint16_t> collisionFaceIds;

        for (const std::vector<uint16_t> *pList :
            {&sector.floorFaceIds, &sector.wallFaceIds, &sector.ceilingFaceIds, &sector.cylinderFaceIds})
        {
            for (uint16_t faceId : *pList)
            {
                if (faceId < sectorVisits.size() && sectorVisits[faceId] != sectorIndex)
                {
                    sectorVisits[faceId] = sectorIndex;
                    collisionFaceIds.push_back(faceId);
                }
            }
        }

        float minX = std::numeric_limits<float>::max();
        float maxX = std::numeric_limits<float>::lowest();
        float minY = std::numeric_limits<float>::max();
        float maxY = std::numeric_limits<float>::lowest();

        const auto includeFaceBounds = [&](const std::vector<uint16_t> &faceIds)
        {
            for (uint16_t faceId : faceIds)
            {
                if (faceId < faceBounds.size() && faceBounds[faceId].placed)
                {
                    minX = std::min(minX, faceBounds[faceId].minX);
                    maxX = std::max(maxX, faceBounds[faceId].maxX);
                    minY = std::min(minY, faceBounds[faceId].minY);
                    maxY = std::max(maxY, faceBounds[faceId].maxY);
                }
            }
        };
        includeFaceBounds(collisionFaceIds);
        includeFaceBounds(sector.portalFaceIds);

        if (minX <= maxX && collisionFaceIds.size() + sector.portalFaceIds.size() > SingleCellFaceLimit)
        {
            const float extent = std::max(maxX - minX, maxY - minY);
            grid.cellSize = std::max(GridCellSize, extent / static_cast<float>(MaxCellsPerAxis));
            grid.originX = minX;
            grid.originY = minY;
            grid.cellsX = std::clamp(
                static_cast<int32_t>(std::ceil((maxX - minX) / grid.cellSize)), 1, MaxCellsPerAxis);
            grid.cellsY = std::clamp(
                static_cast<int32_t>(std::ceil((maxY - minY) / grid.cellSize)), 1, MaxCellsPerAxis);
        }

        const int32_t cellCount = grid.cellsX * grid.cellsY;

        // Two passes over a face list: count each cell's faces, then fill the cells in list order.
        const auto fillCells = [&](const std::vector<uint16_t> &faceIds, bool listMovingFaces, CellLists &lists)
        {
            std::vector<uint32_t> counts(static_cast<size_t>(cellCount) + 1, 0);

            for (int pass = 0; pass < 2; ++pass)
            {
                for (uint16_t faceId : faceIds)
                {
                    if (faceId >= faceBounds.size())
                    {
                        continue;
                    }

                    int32_t firstColumn = 0;
                    int32_t lastColumn = grid.cellsX - 1;
                    int32_t firstRow = 0;
                    int32_t lastRow = grid.cellsY - 1;
                    const FaceBounds &bounds = faceBounds[faceId];

                    if (bounds.placed)
                    {
                        firstColumn = clampedCell(bounds.minX, grid.originX, grid.cellSize, grid.cellsX);
                        lastColumn = clampedCell(bounds.maxX, grid.originX, grid.cellSize, grid.cellsX);
                        firstRow = clampedCell(bounds.minY, grid.originY, grid.cellSize, grid.cellsY);
                        lastRow = clampedCell(bounds.maxY, grid.originY, grid.cellSize, grid.cellsY);
                    }
                    else if (!listMovingFaces)
                    {
                        continue;
                    }

                    for (int32_t row = firstRow; row <= lastRow; ++row)
                    {
                        for (int32_t column = firstColumn; column <= lastColumn; ++column)
                        {
                            const size_t cell = static_cast<size_t>(row * grid.cellsX + column);

                            if (pass == 0)
                            {
                                ++counts[cell + 1];
                            }
                            else
                            {
                                lists.faceIds[counts[cell]++] = faceId;
                            }
                        }
                    }
                }

                if (pass == 0)
                {
                    for (size_t cell = 1; cell < counts.size(); ++cell)
                    {
                        counts[cell] += counts[cell - 1];
                    }

                    lists.cellStarts = counts;
                    lists.faceIds.resize(counts.back());
                }
            }
        };

        fillCells(collisionFaceIds, false, grid.collision);
        fillCells(sector.floorFaceIds, true, grid.floor);
        fillCells(sector.portalFaceIds, true, grid.portal);
        fillCells(sector.ceilingFaceIds, true, grid.ceiling);

        for (uint16_t faceId : collisionFaceIds)
        {
            if (faceId < faceBounds.size() && !faceBounds[faceId].placed)
            {
                grid.movingCollisionFaceIds.push_back(faceId);
            }
        }
    }
}

void IndoorSectorFaceGrid::clear()
{
    m_sectors.clear();
}

bool IndoorSectorFaceGrid::empty() const
{
    return m_sectors.empty();
}

size_t IndoorSectorFaceGrid::memoryBytes() const
{
    size_t bytes = m_sectors.capacity() * sizeof(SectorGrid);

    for (const SectorGrid &grid : m_sectors)
    {
        for (const CellLists *pLists : {&grid.collision, &grid.floor, &grid.portal, &grid.ceiling})
        {
            bytes += pLists->cellStarts.capacity() * sizeof(uint32_t) + pLists->faceIds.capacity() * sizeof(uint16_t);
        }

        bytes += grid.movingCollisionFaceIds.capacity() * sizeof(uint16_t);
    }

    return bytes;
}

void IndoorSectorFaceGrid::appendSegmentFaces(
    int16_t sectorId,
    const bx::Vec3 &start,
    const bx::Vec3 &end,
    float margin,
    IndoorFaceGeometryCache &geometryCache,
    std::vector<size_t> &faceIndices) const
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_sectors.size())
    {
        return;
    }

    const SectorGrid &grid = m_sectors[sectorId];
    const auto appendFace = [&geometryCache, &faceIndices](uint16_t faceId)
    {
        if (geometryCache.markFaceVisited(faceId))
        {
            faceIndices.push_back(faceId);
        }
    };

    for (uint16_t faceId : grid.movingCollisionFaceIds)
    {
        appendFace(faceId);
    }

    const float gridMaxX = grid.originX + grid.cellSize * static_cast<float>(grid.cellsX);
    const float gridMaxY = grid.originY + grid.cellSize * static_cast<float>(grid.cellsY);
    const float segmentMinY = std::min(start.y, end.y) - margin;
    const float segmentMaxY = std::max(start.y, end.y) + margin;

    if (grid.cellsX * grid.cellsY > 1
        && (std::max(start.x, end.x) + margin < grid.originX || std::min(start.x, end.x) - margin > gridMaxX
            || segmentMaxY < grid.originY || segmentMinY > gridMaxY))
    {
        return;
    }

    const int32_t firstRow = clampedCell(segmentMinY, grid.originY, grid.cellSize, grid.cellsY);
    const int32_t lastRow = clampedCell(segmentMaxY, grid.originY, grid.cellSize, grid.cellsY);
    const float deltaX = end.x - start.x;
    const float deltaY = end.y - start.y;

    for (int32_t row = firstRow; row <= lastRow; ++row)
    {
        // The part of the segment within `margin` of this row of cells, in x.
        float spanMinX = std::min(start.x, end.x);
        float spanMaxX = std::max(start.x, end.x);

        if (firstRow != lastRow && std::fabs(deltaY) > 0.0001f)
        {
            const float bandMinY = grid.originY + grid.cellSize * static_cast<float>(row) - margin;
            const float bandMaxY = bandMinY + grid.cellSize + 2.0f * margin;
            float enter = (bandMinY - start.y) / deltaY;
            float leave = (bandMaxY - start.y) / deltaY;

            if (enter > leave)
            {
                std::swap(enter, leave);
            }

            enter = std::max(enter, 0.0f);
            leave = std::min(leave, 1.0f);

            if (enter > leave)
            {
                continue;
            }

            const float enterX = start.x + deltaX * enter;
            const float leaveX = start.x + deltaX * leave;
            spanMinX = std::min(enterX, leaveX);
            spanMaxX = std::max(enterX, leaveX);
        }

        const int32_t firstColumn = clampedCell(spanMinX - margin, grid.originX, grid.cellSize, grid.cellsX);
        const int32_t lastColumn = clampedCell(spanMaxX + margin, grid.originX, grid.cellSize, grid.cellsX);

        for (int32_t column = firstColumn; column <= lastColumn; ++column)
        {
            for (uint16_t faceId : cellFaces(grid.collision, row * grid.cellsX + column))
            {
                appendFace(faceId);
            }
        }
    }
}

std::span<const uint16_t> IndoorSectorFaceGrid::floorFacesAt(int16_t sectorId, float x, float y) const
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_sectors.size())
    {
        return {};
    }

    const SectorGrid &grid = m_sectors[sectorId];
    return cellFaces(grid.floor, cellIndexAt(grid, x, y));
}

std::span<const uint16_t> IndoorSectorFaceGrid::portalFacesAt(int16_t sectorId, float x, float y) const
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_sectors.size())
    {
        return {};
    }

    const SectorGrid &grid = m_sectors[sectorId];
    return cellFaces(grid.portal, cellIndexAt(grid, x, y));
}

std::span<const uint16_t> IndoorSectorFaceGrid::ceilingFacesAt(int16_t sectorId, float x, float y) const
{
    if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_sectors.size())
    {
        return {};
    }

    const SectorGrid &grid = m_sectors[sectorId];
    return cellFaces(grid.ceiling, cellIndexAt(grid, x, y));
}

int32_t IndoorSectorFaceGrid::cellIndexAt(const SectorGrid &grid, float x, float y) const
{
    return clampedCell(y, grid.originY, grid.cellSize, grid.cellsY) * grid.cellsX
        + clampedCell(x, grid.originX, grid.cellSize, grid.cellsX);
}

std::span<const uint16_t> IndoorSectorFaceGrid::cellFaces(const CellLists &lists, int32_t cellIndex)
{
    if (cellIndex < 0 || static_cast<size_t>(cellIndex) + 1 >= lists.cellStarts.size())
    {
        return {};
    }

    const uint32_t begin = lists.cellStarts[cellIndex];
    const uint32_t end = lists.cellStarts[cellIndex + 1];
    return std::span<const uint16_t>(lists.faceIds.data() + begin, end - begin);
}

void collectIndoorSegmentFaceCandidates(
    const IndoorMapData &indoorMapData,
    IndoorFaceGeometryCache &geometryCache,
    const std::vector<int16_t> &sectorIds,
    const bx::Vec3 &start,
    const bx::Vec3 &end,
    float margin,
    std::vector<size_t> &faceIndices)
{
    faceIndices.clear();
    geometryCache.beginFaceVisit();
    const IndoorSectorFaceGrid *pGrid = geometryCache.sectorFaceGrid();
    // A segment with a non-finite end has no place in the grid; it is tested against every face, as without one.
    const bool useGrid = pGrid != nullptr && !pGrid->empty()
        && std::isfinite(start.x) && std::isfinite(start.y) && std::isfinite(end.x) && std::isfinite(end.y)
        && std::isfinite(margin);

    for (int16_t sectorId : sectorIds)
    {
        if (sectorId < 0 || static_cast<size_t>(sectorId) >= indoorMapData.sectors.size())
        {
            continue;
        }

        if (useGrid)
        {
            pGrid->appendSegmentFaces(sectorId, start, end, margin, geometryCache, faceIndices);
            continue;
        }

        const IndoorSector &sector = indoorMapData.sectors[sectorId];

        for (const std::vector<uint16_t> *pList :
            {&sector.floorFaceIds, &sector.wallFaceIds, &sector.ceilingFaceIds, &sector.cylinderFaceIds})
        {
            for (uint16_t faceId : *pList)
            {
                if (geometryCache.markFaceVisited(faceId))
                {
                    faceIndices.push_back(faceId);
                }
            }
        }
    }
}
}
