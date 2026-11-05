#include <doctest/doctest.h>

#include "game/indoor/IndoorCollisionPrimitives.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorSectorFaceGrid.h"
#include "game/maps/MapDeltaData.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <set>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
std::optional<IndoorMapData> loadBlv(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);

    if (!stream.good())
    {
        return std::nullopt;
    }

    const std::vector<uint8_t> bytes = {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
    return IndoorMapDataLoader().loadFromBytes(bytes);
}

void addFace(IndoorMapData &map, std::initializer_list<IndoorVertex> vertices, uint8_t type, uint16_t sectorId)
{
    IndoorFace face = {};
    face.facetType = type;
    face.roomNumber = sectorId;

    for (const IndoorVertex &vertex : vertices)
    {
        face.vertexIndices.push_back(uint16_t(map.vertices.size()));
        map.vertices.push_back(vertex);
    }

    const uint16_t faceId = uint16_t(map.faces.size());
    map.faces.push_back(face);
    IndoorSector &sector = map.sectors[sectorId];
    sector.faceIds.push_back(faceId);
    std::vector<uint16_t> &list =
        type == 3 ? sector.floorFaceIds : type == 5 ? sector.ceilingFaceIds : sector.wallFaceIds;
    list.push_back(faceId);
}

// One 2000 x 2000 hall: a floor of 20 x 20 tiles, a ceiling, four walls and 40 square pillars.
IndoorMapData pillarHall()
{
    IndoorMapData map = {};
    map.sectors.resize(2);
    IndoorSector &hall = map.sectors[1];
    hall.minX = hall.minY = -1000;
    hall.maxX = hall.maxY = 1000;
    hall.minZ = 0;
    hall.maxZ = 400;

    for (int16_t row = 0; row < 20; ++row)
    {
        for (int16_t column = 0; column < 20; ++column)
        {
            const int16_t x = int16_t(-1000 + column * 100);
            const int16_t y = int16_t(-1000 + row * 100);
            addFace(map, {{x, y, 0}, {int16_t(x + 100), y, 0}, {int16_t(x + 100), int16_t(y + 100), 0},
                {x, int16_t(y + 100), 0}}, 3, 1);
        }
    }

    addFace(map, {{-1000, 1000, 400}, {1000, 1000, 400}, {1000, -1000, 400}, {-1000, -1000, 400}}, 5, 1);
    addFace(map, {{-1000, -1000, 0}, {1000, -1000, 0}, {1000, -1000, 400}, {-1000, -1000, 400}}, 1, 1);
    addFace(map, {{1000, 1000, 0}, {-1000, 1000, 0}, {-1000, 1000, 400}, {1000, 1000, 400}}, 1, 1);
    addFace(map, {{-1000, 1000, 0}, {-1000, -1000, 0}, {-1000, -1000, 400}, {-1000, 1000, 400}}, 1, 1);
    addFace(map, {{1000, -1000, 0}, {1000, 1000, 0}, {1000, 1000, 400}, {1000, -1000, 400}}, 1, 1);

    for (int16_t pillar = 0; pillar < 40; ++pillar)
    {
        const int16_t x0 = int16_t(-900 + (pillar % 8) * 230);
        const int16_t y0 = int16_t(-900 + (pillar / 8) * 370);
        const int16_t x1 = int16_t(x0 + 40);
        const int16_t y1 = int16_t(y0 + 40);
        addFace(map, {{x0, y0, 0}, {x1, y0, 0}, {x1, y0, 300}, {x0, y0, 300}}, 1, 1);
        addFace(map, {{x1, y0, 0}, {x1, y1, 0}, {x1, y1, 300}, {x1, y0, 300}}, 1, 1);
        addFace(map, {{x1, y1, 0}, {x0, y1, 0}, {x0, y1, 300}, {x1, y1, 300}}, 1, 1);
        addFace(map, {{x0, y1, 0}, {x0, y0, 0}, {x0, y0, 300}, {x0, y1, 300}}, 1, 1);
    }

    return map;
}

bool segmentCrossesFace(const IndoorFaceGeometryData &geometry, const bx::Vec3 &start, const bx::Vec3 &end)
{
    if (!geometry.hasPlane || geometry.vertices.empty())
    {
        return false;
    }

    const bx::Vec3 segment = {end.x - start.x, end.y - start.y, end.z - start.z};
    const bx::Vec3 &normal = geometry.normal;
    const float denominator = segment.x * normal.x + segment.y * normal.y + segment.z * normal.z;

    if (std::fabs(denominator) <= 0.0001f)
    {
        return false;
    }

    const bx::Vec3 &origin = geometry.vertices.front();
    const float progress =
        ((origin.x - start.x) * normal.x + (origin.y - start.y) * normal.y + (origin.z - start.z) * normal.z)
        / denominator;

    if (progress < 0.0f || progress > 1.0f)
    {
        return false;
    }

    const bx::Vec3 point = {start.x + segment.x * progress, start.y + segment.y * progress,
        start.z + segment.z * progress};
    return isPointInsideIndoorPolygonProjected(point, geometry.vertices, normal);
}

std::set<size_t> sortedSectorFaces(const IndoorMapData &map, const std::vector<int16_t> &sectorIds)
{
    std::set<size_t> faces;

    for (int16_t sectorId : sectorIds)
    {
        const IndoorSector &sector = map.sectors[sectorId];

        for (const std::vector<uint16_t> *pList :
            {&sector.floorFaceIds, &sector.wallFaceIds, &sector.ceilingFaceIds, &sector.cylinderFaceIds})
        {
            faces.insert(pList->begin(), pList->end());
        }
    }

    return faces;
}

// Compares the grid with the full sector lists on random segments and points. A door moves some faces after the
// grid is built, so faces the grid cannot place must still be found.
void checkGridAgainstSectorLists(const IndoorMapData &map, uint32_t seed, size_t segmentCount, size_t sweepCount)
{
    MapDeltaData mapDelta = {};
    MapDeltaDoor door = {};
    door.doorId = 1;

    for (size_t faceIndex = 7; faceIndex < map.faces.size(); faceIndex += 61)
    {
        door.faceIds.push_back(uint16_t(faceIndex));
        door.vertexIds.insert(
            door.vertexIds.end(), map.faces[faceIndex].vertexIndices.begin(), map.faces[faceIndex].vertexIndices.end());
    }

    mapDelta.doors.push_back(door);
    IndoorSectorFaceGrid grid;
    grid.build(map, map.vertices, &mapDelta);
    REQUIRE_FALSE(grid.empty());
    std::vector<IndoorVertex> vertices = map.vertices;
    std::sort(door.vertexIds.begin(), door.vertexIds.end());
    door.vertexIds.erase(std::unique(door.vertexIds.begin(), door.vertexIds.end()), door.vertexIds.end());

    for (uint16_t vertexId : door.vertexIds)
    {
        vertices[vertexId].x = int16_t(vertices[vertexId].x + 40);
        vertices[vertexId].y = int16_t(vertices[vertexId].y - 30);
        vertices[vertexId].z = int16_t(vertices[vertexId].z + 12);
    }

    IndoorFaceGeometryCache fullCache(map.faces.size());
    IndoorFaceGeometryCache gridCache(map.faces.size());
    gridCache.setSectorFaceGrid(&grid);
    std::vector<int16_t> sectors;
    size_t largestSector = 0;
    size_t largestFaceCount = 0;

    for (size_t sectorIndex = 1; sectorIndex < map.sectors.size(); ++sectorIndex)
    {
        const size_t faceCount = sortedSectorFaces(map, {int16_t(sectorIndex)}).size();

        if (faceCount > 0)
        {
            sectors.push_back(int16_t(sectorIndex));
        }

        if (faceCount > largestFaceCount)
        {
            largestFaceCount = faceCount;
            largestSector = sectorIndex;
        }
    }

    REQUIRE_FALSE(sectors.empty());
    std::mt19937 random(seed);
    std::uniform_real_distribution<float> unit(0.0f, 1.0f);
    const auto pickSector = [&]() -> int16_t
    {
        return unit(random) < 0.5f ? int16_t(largestSector) : sectors[random() % sectors.size()];
    };
    const auto pointInSector = [&](int16_t sectorId) -> bx::Vec3
    {
        const IndoorSector &sector = map.sectors[sectorId];
        return {sector.minX - 64.0f + unit(random) * (sector.maxX - sector.minX + 128.0f),
            sector.minY - 64.0f + unit(random) * (sector.maxY - sector.minY + 128.0f),
            sector.minZ - 16.0f + unit(random) * (sector.maxZ - sector.minZ + 32.0f)};
    };
    std::vector<size_t> fullCandidates;
    std::vector<size_t> gridCandidates;

    for (size_t segmentIndex = 0; segmentIndex < segmentCount; ++segmentIndex)
    {
        std::vector<int16_t> sectorIds = {pickSector()};

        if (unit(random) < 0.4f)
        {
            sectorIds.push_back(sectors[random() % sectors.size()]);
        }

        const bx::Vec3 start = pointInSector(sectorIds.front());
        bx::Vec3 end = pointInSector(sectorIds.back());
        const float shape = unit(random);

        if (shape < 0.1f)
        {
            end = {start.x, start.y, end.z};
        }
        else if (shape < 0.2f)
        {
            end = {end.x, start.y, start.z};
        }
        else if (shape < 0.4f)
        {
            end = {start.x + (end.x - start.x) * 0.1f, start.y + (end.y - start.y) * 0.1f, end.z};
        }

        // Without the grid: every face of the lists once, the same set the sorted, de-duplicated list held.
        collectIndoorSegmentFaceCandidates(map, fullCache, sectorIds, start, end, 1.0f, fullCandidates);
        const std::set<size_t> fullSet(fullCandidates.begin(), fullCandidates.end());
        REQUIRE_EQ(fullSet.size(), fullCandidates.size());
        REQUIRE(fullSet == sortedSectorFaces(map, sectorIds));

        // With the grid: every face the segment crosses, which is every face line of sight or a projectile can hit.
        for (float margin : {0.0f, 1.0f, 24.0f})
        {
            collectIndoorSegmentFaceCandidates(map, gridCache, sectorIds, start, end, margin, gridCandidates);
            const std::set<size_t> gridSet(gridCandidates.begin(), gridCandidates.end());
            REQUIRE_EQ(gridSet.size(), gridCandidates.size());

            for (size_t faceIndex : fullCandidates)
            {
                const IndoorFaceGeometryData *pGeometry = fullCache.geometryForFace(map, vertices, faceIndex);

                if (pGeometry != nullptr && segmentCrossesFace(*pGeometry, start, end))
                {
                    INFO("segment " << segmentIndex << " face " << faceIndex << " margin " << margin);
                    REQUIRE(gridSet.count(faceIndex) == 1);
                }
            }
        }

        // An item's sphere chain: every face a sphere meets, with the margin the item sweep passes.
        if (segmentIndex < sweepCount)
        {
            const float radius = 16.0f;
            const std::array<bx::Vec3, 3> offsets = {{{0.0f, 0.0f, 0.0f}, {24.0f, 0.0f, 0.0f}, {0.0f, -24.0f, 30.0f}}};
            const float reach = 24.0f + radius;
            collectIndoorSegmentFaceCandidates(map, gridCache, sectorIds, start, end, reach + 8.0f, gridCandidates);
            const std::set<size_t> gridSet(gridCandidates.begin(), gridCandidates.end());
            const bx::Vec3 move = {end.x - start.x, end.y - start.y, end.z - start.z};
            const float distance = std::sqrt(move.x * move.x + move.y * move.y + move.z * move.z);

            if (distance > 0.001f)
            {
                const bx::Vec3 direction = {move.x / distance, move.y / distance, move.z / distance};

                for (size_t faceIndex : fullCandidates)
                {
                    const IndoorFaceGeometryData *pGeometry = fullCache.geometryForFace(map, vertices, faceIndex);

                    if (pGeometry == nullptr || !pGeometry->hasPlane)
                    {
                        continue;
                    }

                    for (const bx::Vec3 &offset : offsets)
                    {
                        IndoorSweptSphere sphere = {};
                        sphere.center = {start.x + offset.x, start.y + offset.y, start.z + offset.z};
                        sphere.radius = radius;
                        const std::optional<IndoorSweptFaceHit> hit =
                            sweepIndoorSphereAgainstFace(sphere, direction, distance, *pGeometry);

                        if (hit && hit->hit)
                        {
                            INFO("sweep " << segmentIndex << " face " << faceIndex);
                            REQUIRE(gridSet.count(faceIndex) == 1);
                        }
                    }
                }
            }
        }
    }

    // The sector lookup returns the same sector with and without the grid.
    for (size_t pointIndex = 0; pointIndex < segmentCount * 2; ++pointIndex)
    {
        const bx::Vec3 point = pointInSector(pickSector());

        for (bool allowBoundingSectorFallback : {true, false})
        {
            const std::optional<int16_t> full =
                findIndoorSectorForPoint(map, vertices, point, &fullCache, allowBoundingSectorFallback);
            const std::optional<int16_t> gridded =
                findIndoorSectorForPoint(map, vertices, point, &gridCache, allowBoundingSectorFallback);
            INFO("point " << point.x << " " << point.y << " " << point.z);
            REQUIRE(full == gridded);
        }
    }
}
}

TEST_CASE("indoor sector face grid finds every face a segment can hit in a pillar hall")
{
    checkGridAgainstSectorLists(pillarHall(), 11u, 3000, 600);
}

TEST_CASE("indoor segment face candidates list each face of overlapping sectors once")
{
    IndoorMapData map = pillarHall();
    // A face listed by both sectors and twice by one: the candidates hold it once.
    map.sectors.push_back(map.sectors[1]);
    map.sectors[2].wallFaceIds.push_back(map.sectors[2].floorFaceIds.front());
    IndoorFaceGeometryCache cache(map.faces.size());
    std::vector<size_t> candidates;
    collectIndoorSegmentFaceCandidates(map, cache, {1, 2, 2}, {0.0f, 0.0f, 50.0f}, {500.0f, 0.0f, 50.0f}, 1.0f,
        candidates);
    CHECK_EQ(candidates.size(), sortedSectorFaces(map, {1}).size());
    CHECK_EQ(std::set<size_t>(candidates.begin(), candidates.end()).size(), candidates.size());
}

// The shipped MM6-MM8 dungeons and, where present, the rebuilt MM9 dungeons of the review root
// (devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md): the biggest sectors of both.
TEST_CASE("indoor sector face grid matches the full sector lists on real maps")
{
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    const std::vector<std::filesystem::path> maps = {
        root / "assets_dev/worlds/mm8/maps/d13.blv",
        root / "assets_dev/worlds/mm8/maps/d19.blv",
        root / "assets_dev/worlds/mm7/maps/7d35.blv",
        root / "assets_dev/worlds/mm6/maps/6d17.blv",
        root / "output/mm9_rework/assets_dev/worlds/mm9/maps/1000terrors.blv",
        root / "output/mm9_rework/assets_dev/worlds/mm9/maps/lindisfarnemonastery.blv",
        root / "output/mm9_rework/assets_dev/worlds/mm9/maps/traininghall.blv",
        root / "output/mm9_rework/assets_dev/worlds/mm9/maps/hallofthegods.blv",
    };
    uint32_t seed = 101;

    for (const std::filesystem::path &path : maps)
    {
        const std::optional<IndoorMapData> map = loadBlv(path);

        if (!map)
        {
            REQUIRE(path.string().find("output/mm9_rework") != std::string::npos);
            continue;
        }

        INFO(path.filename().string());
        checkGridAgainstSectorLists(*map, seed++, 800, 100);
    }
}

TEST_CASE("indoor sector lookup sees every floor over and under a point, past five")
{
    // A tall open sector (a city's street air) with six floors high over the point, and a staircase room inside its
    // bounds whose floor is just under it: MM8's lookup kept the first five floors and so missed the room's.
    IndoorMapData map = {};
    map.sectors.resize(3);
    IndoorSector &air = map.sectors[1];
    air.minX = air.minY = -1000;
    air.maxX = air.maxY = 1000;
    air.minZ = 0;
    air.maxZ = 5000;
    IndoorSector &stairs = map.sectors[2];
    stairs.minX = stairs.minY = -200;
    stairs.maxX = stairs.maxY = 200;
    stairs.minZ = 900;
    stairs.maxZ = 1400;
    for (int16_t floor = 0; floor < 6; ++floor)
    {
        const int16_t z = int16_t(3000 + floor * 200);
        addFace(map, {{-1000, -1000, z}, {1000, -1000, z}, {1000, 1000, z}, {-1000, 1000, z}}, 3, 1);
    }
    addFace(map, {{-200, -200, 1000}, {200, -200, 1000}, {200, 200, 1000}, {-200, 200, 1000}}, 3, 2);
    const std::vector<IndoorVertex> &vertices = map.vertices;

    CHECK(findIndoorSectorForPoint(map, vertices, {0.0f, 0.0f, 1100.0f}, nullptr, true) == std::optional<int16_t>(2));
    // Over the air's floors the point is the air's.
    CHECK(findIndoorSectorForPoint(map, vertices, {0.0f, 0.0f, 4500.0f}, nullptr, true) == std::optional<int16_t>(1));
}
