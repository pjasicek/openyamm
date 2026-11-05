#include "editor/import/IndoorDerivedGeometry.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <tuple>
#include <utility>

namespace OpenYAMM::Editor
{
namespace
{
// Faces whose normals differ by less than about 1.8 degrees meet as one surface for the outlines.
constexpr double NearlyCoplanarDot = 0.9995;

struct PartitionPlane
{
    double x = 0;
    double y = 0;
    double z = 0;
    double distance = 0;
};

// The face's plane from a Newell normal summed in double precision over its integer vertices. The shared float
// normal of the face geometry cache rounds its products once coordinates and edges are large (a long, thin triangle
// at x -3700, y 7900 is off its own float plane by 0.3), which would reject planar faces and skew partitions.
PartitionPlane facePlane(const Game::IndoorMapData &geometry, uint16_t faceId)
{
    const std::vector<uint16_t> &vertexIds = geometry.faces[faceId].vertexIndices;
    double normalX = 0;
    double normalY = 0;
    double normalZ = 0;
    for (size_t index = 0; index < vertexIds.size(); ++index)
    {
        const Game::IndoorVertex &current = geometry.vertices[vertexIds[index]];
        const Game::IndoorVertex &next = geometry.vertices[vertexIds[(index + 1) % vertexIds.size()]];
        normalX += (double(current.y) - next.y) * (double(current.z) + next.z);
        normalY += (double(current.z) - next.z) * (double(current.x) + next.x);
        normalZ += (double(current.x) - next.x) * (double(current.y) + next.y);
    }
    const double length = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);
    if (length <= 0)
    {
        return {};
    }
    const Game::IndoorVertex &point = geometry.vertices[vertexIds.front()];
    normalX /= length;
    normalY /= length;
    normalZ /= length;
    return {normalX, normalY, normalZ, -(normalX * point.x + normalY * point.y + normalZ * point.z)};
}

// 0 is coplanar, 1 front, 2 back, 3 crossing. Distances are in native map units.
int classifyFace(const Game::IndoorMapData &geometry, uint16_t faceId, const PartitionPlane &plane)
{
    int side = 0;
    for (uint16_t vertexId : geometry.faces[faceId].vertexIndices)
    {
        const Game::IndoorVertex &vertex = geometry.vertices[vertexId];
        const double distance = plane.x * vertex.x + plane.y * vertex.y + plane.z * vertex.z + plane.distance;
        side |= distance > 0.01 ? 1 : distance < -0.01 ? 2 : 0;
    }
    return side;
}

// Consecutive collinear outlines between the same two faces drawn as one line: an edge split at a vertex lying on it
// (a converter's T-junction repair inserts thousands) would otherwise cost one outline per piece of the 7 000.
void mergeCollinearOutlines(Game::IndoorMapData &geometry)
{
    std::map<std::pair<uint16_t, uint16_t>, std::vector<size_t>> groups;
    for (size_t index = 0; index < geometry.outlines.size(); ++index)
    {
        const Game::IndoorOutline &outline = geometry.outlines[index];
        groups[std::minmax(outline.face1Id, outline.face2Id)].push_back(index);
    }
    const auto collinearThrough = [&geometry](uint16_t middle, uint16_t a, uint16_t b)
    {
        const Game::IndoorVertex &m = geometry.vertices[middle];
        const Game::IndoorVertex &p = geometry.vertices[a];
        const Game::IndoorVertex &q = geometry.vertices[b];
        const double ax = double(p.x) - m.x, ay = double(p.y) - m.y, az = double(p.z) - m.z;
        const double bx = double(q.x) - m.x, by = double(q.y) - m.y, bz = double(q.z) - m.z;
        const double cx = ay * bz - az * by, cy = az * bx - ax * bz, cz = ax * by - ay * bx;
        const double lengths = std::sqrt((ax * ax + ay * ay + az * az) * (bx * bx + by * by + bz * bz));
        return lengths > 0 && ax * bx + ay * by + az * bz < 0
            && std::sqrt(cx * cx + cy * cy + cz * cz) <= 1e-3 * lengths;
    };
    std::vector<uint8_t> removed(geometry.outlines.size(), 0);
    for (const auto &[faces, members] : groups)
    {
        std::map<uint16_t, std::vector<size_t>> atVertex;
        for (size_t index : members)
        {
            atVertex[geometry.outlines[index].vertex1Id].push_back(index);
            atVertex[geometry.outlines[index].vertex2Id].push_back(index);
        }
        for (auto &[vertex, touching] : atVertex)
        {
            if (touching.size() != 2)
            {
                continue;
            }
            Game::IndoorOutline &kept = geometry.outlines[touching[0]];
            const Game::IndoorOutline &dropped = geometry.outlines[touching[1]];
            const uint16_t keptEnd = kept.vertex1Id == vertex ? kept.vertex2Id : kept.vertex1Id;
            const uint16_t droppedEnd = dropped.vertex1Id == vertex ? dropped.vertex2Id : dropped.vertex1Id;
            if (keptEnd == droppedEnd || !collinearThrough(vertex, keptEnd, droppedEnd))
            {
                continue;
            }
            // The kept outline now runs to the dropped one's far end, which takes it over in that vertex's list.
            (kept.vertex1Id == vertex ? kept.vertex1Id : kept.vertex2Id) = droppedEnd;
            kept.z = int16_t((geometry.vertices[kept.vertex1Id].z + geometry.vertices[kept.vertex2Id].z) / 2);
            removed[touching[1]] = 1;
            for (size_t &index : atVertex[droppedEnd])
            {
                if (index == touching[1])
                {
                    index = touching[0];
                }
            }
            touching.clear();
        }
    }
    std::vector<Game::IndoorOutline> outlines;
    outlines.reserve(geometry.outlines.size());
    for (size_t index = 0; index < geometry.outlines.size(); ++index)
    {
        if (removed[index] == 0)
        {
            outlines.push_back(geometry.outlines[index]);
        }
    }
    geometry.outlines = std::move(outlines);
}

struct PartitionWork
{
    std::vector<uint16_t> faces;
    int16_t parent = -1;
    bool front = false;
};

bool buildSectorBsp(
    Game::IndoorMapData &geometry,
    size_t sectorId,
    const std::vector<PartitionPlane> &planes,
    const std::vector<bool> &moving,
    std::string &errorMessage)
{
    Game::IndoorSector &sector = geometry.sectors[sectorId];
    const size_t firstGeneratedNode = geometry.bspNodes.size();
    std::vector<PartitionWork> pending(1);
    sector.nonBspFaceIds.clear();
    for (uint16_t faceId : sector.faceIds)
    {
        if (moving[faceId])
        {
            sector.nonBspFaceIds.push_back(faceId);
        }
        else
        {
            pending.front().faces.push_back(faceId);
        }
    }
    std::sort(pending.front().faces.begin(), pending.front().faces.end());
    sector.faceIds.clear();
    sector.firstBspNode = -1;
    sector.flags &= ~0x10;

    while (!pending.empty())
    {
        PartitionWork work = std::move(pending.back());
        pending.pop_back();
        if (work.faces.empty())
        {
            continue;
        }
        if (geometry.bspNodes.size() >= 32767 || sector.faceIds.size() + work.faces.size() > 32767)
        {
            errorMessage = "indoor BSP exceeds native signed 16-bit index limits";
            return false;
        }

        // Minimize unsplit crossing faces, then balance the remaining tree. Stable source order breaks ties.
        uint16_t partitionFace = work.faces.front();
        size_t bestScore = size_t(-1);
        for (uint16_t candidate : work.faces)
        {
            size_t front = 0;
            size_t back = 0;
            size_t crossing = 0;
            for (uint16_t faceId : work.faces)
            {
                const int side = classifyFace(geometry, faceId, planes[candidate]);
                front += side == 1;
                back += side == 2;
                crossing += side == 3;
            }
            const size_t score = crossing * (work.faces.size() + 1) + std::max(front, back);
            if (score < bestScore)
            {
                bestScore = score;
                partitionFace = candidate;
            }
        }

        PartitionPlane plane = planes[partitionFace];
        if (geometry.faces[partitionFace].isPortal && geometry.faces[partitionFace].roomNumber != sectorId)
        {
            plane = {-plane.x, -plane.y, -plane.z, -plane.distance};
        }
        const int16_t nodeId = int16_t(geometry.bspNodes.size());
        Game::IndoorBspNode node = {};
        node.front = -1;
        node.back = -1;
        node.faceIdOffset = int16_t(sector.faceIds.size());
        // The native reader takes the first face as the partition plane, including its orientation.
        sector.faceIds.push_back(partitionFace);
        node.faceCount = 1;
        PartitionWork front = {{}, nodeId, true};
        PartitionWork back = {{}, nodeId, false};
        for (uint16_t faceId : work.faces)
        {
            if (faceId == partitionFace)
            {
                continue;
            }
            const int side = classifyFace(geometry, faceId, plane);
            if (side == 0)
            {
                sector.faceIds.push_back(faceId);
                ++node.faceCount;
            }
            else if (side == 1)
            {
                front.faces.push_back(faceId);
            }
            else if (side == 2)
            {
                back.faces.push_back(faceId);
            }
            else
            {
                sector.nonBspFaceIds.push_back(faceId);
            }
        }
        geometry.bspNodes.push_back(node);
        if (work.parent == -1)
        {
            sector.firstBspNode = nodeId;
            sector.flags |= 0x10;
        }
        else if (work.front)
        {
            geometry.bspNodes[work.parent].front = nodeId;
        }
        else
        {
            geometry.bspNodes[work.parent].back = nodeId;
        }
        pending.push_back(std::move(back));
        pending.push_back(std::move(front));
    }
    if (sector.faceIds.size() + sector.nonBspFaceIds.size() > 32767)
    {
        errorMessage = "indoor sector face list exceeds native BSP offset limits";
        return false;
    }
    // Native sectors store non-BSP faces as a prefix of the same face list.
    std::sort(sector.nonBspFaceIds.begin(), sector.nonBspFaceIds.end());
    sector.faceIds.insert(sector.faceIds.begin(), sector.nonBspFaceIds.begin(), sector.nonBspFaceIds.end());
    for (size_t nodeId = firstGeneratedNode; nodeId < geometry.bspNodes.size(); ++nodeId)
    {
        geometry.bspNodes[nodeId].faceIdOffset += int16_t(sector.nonBspFaceIds.size());
    }
    sector.faceCount = uint16_t(sector.faceIds.size());
    sector.nonBspFaceCount = uint16_t(sector.nonBspFaceIds.size());
    return true;
}
}

bool generateIndoorDerivedGeometry(
    Game::IndoorMapData &geometry,
    const std::vector<uint16_t> &movingFaceIds,
    bool generateBsp,
    bool generateOutlines,
    std::string &errorMessage)
{
    if (!generateBsp && !generateOutlines)
    {
        return true;
    }
    std::vector<bool> moving(geometry.faces.size(), false);
    for (uint16_t faceId : movingFaceIds)
    {
        if (faceId >= moving.size())
        {
            errorMessage = "indoor moving face index is out of range";
            return false;
        }
        moving[faceId] = true;
    }
    Game::IndoorFaceGeometryCache cache(geometry.faces.size());
    std::vector<PartitionPlane> planes;
    planes.reserve(geometry.faces.size());
    for (size_t faceId = 0; faceId < geometry.faces.size(); ++faceId)
    {
        const Game::IndoorFaceGeometryData *pFace = cache.geometryForFace(geometry, geometry.vertices, faceId);
        if (pFace == nullptr || !pFace->hasPlane || pFace->vertices.empty())
        {
            errorMessage = "indoor derived geometry requires a non-degenerate face: " + std::to_string(faceId);
            return false;
        }
        planes.push_back(facePlane(geometry, uint16_t(faceId)));
        if (classifyFace(geometry, uint16_t(faceId), planes.back()) != 0)
        {
            errorMessage = "indoor native face is non-planar after coordinate quantization: " + std::to_string(faceId);
            return false;
        }
    }
    if (generateBsp)
    {
        geometry.bspNodes.clear();
        for (size_t sectorId = 0; sectorId < geometry.sectors.size(); ++sectorId)
        {
            if (!buildSectorBsp(geometry, sectorId, planes, moving, errorMessage))
            {
                return false;
            }
        }
    }
    if (generateOutlines)
    {
        geometry.outlines.clear();
        std::map<std::pair<uint16_t, uint16_t>, std::vector<uint16_t>> edges;
        std::map<std::tuple<int, int, int>, uint16_t> outlineVertices;
        for (size_t faceId = 0; faceId < geometry.faces.size(); ++faceId)
        {
            // An invisible face draws no outline, so its corners split no visible edge either (MM9's monster
            // barriers stand on floor edges; invisible walls and steps likewise).
            if (moving[faceId]
                || Game::hasFaceAttribute(geometry.faces[faceId].attributes, Game::FaceAttribute::Invisible))
            {
                continue;
            }
            for (uint16_t vertexId : geometry.faces[faceId].vertexIndices)
            {
                const Game::IndoorVertex &vertex = geometry.vertices[vertexId];
                outlineVertices.try_emplace({vertex.x, vertex.y, vertex.z}, vertexId);
            }
        }
        for (size_t faceId = 0; faceId < geometry.faces.size(); ++faceId)
        {
            const Game::IndoorFace &face = geometry.faces[faceId];
            if (face.isPortal || moving[faceId] || face.facetType == 5 || face.facetType == 6
                || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible))
            {
                continue;
            }
            for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
            {
                const uint16_t a = face.vertexIndices[corner];
                const uint16_t b = face.vertexIndices[(corner + 1) % face.vertexIndices.size()];
                if (geometry.vertices[a].x != geometry.vertices[b].x
                    || geometry.vertices[a].y != geometry.vertices[b].y)
                {
                    // A floor can have one long edge beside several wall segments and a doorway.
                    // Split outline edges at collinear vertices so these T-junctions share adjacency.
                    const Game::IndoorVertex &start = geometry.vertices[a];
                    const Game::IndoorVertex &end = geometry.vertices[b];
                    const double dx = end.x - start.x;
                    const double dy = end.y - start.y;
                    const double dz = end.z - start.z;
                    const double lengthSquared = dx * dx + dy * dy + dz * dz;
                    std::vector<std::pair<double, uint16_t>> points;
                    for (const auto &[coordinate, vertexId] : outlineVertices)
                    {
                        const Game::IndoorVertex &vertex = geometry.vertices[vertexId];
                        const double t = ((vertex.x - start.x) * dx + (vertex.y - start.y) * dy
                            + (vertex.z - start.z) * dz) / lengthSquared;
                        if (t >= 0 && t <= 1
                            && std::abs(start.x + t * dx - vertex.x) < 0.01
                            && std::abs(start.y + t * dy - vertex.y) < 0.01
                            && std::abs(start.z + t * dz - vertex.z) < 0.01)
                        {
                            points.emplace_back(t, vertexId);
                        }
                    }
                    std::sort(points.begin(), points.end());
                    for (size_t index = 1; index < points.size(); ++index)
                    {
                        edges[std::minmax(points[index - 1].second, points[index].second)].push_back(uint16_t(faceId));
                    }
                }
            }
        }
        for (const auto &[edge, faces] : edges)
        {
            const bool bordersFloor = std::any_of(faces.begin(), faces.end(), [&geometry](uint16_t faceId)
            {
                return geometry.faces[faceId].facetType == 3 || geometry.faces[faceId].facetType == 4;
            });
            if (!bordersFloor)
            {
                continue;
            }
            const uint16_t first = faces.front();
            uint16_t second = first;
            for (uint16_t faceId : faces)
            {
                if (classifyFace(geometry, faceId, planes[first]) != 0)
                {
                    second = faceId;
                    break;
                }
            }
            if (faces.size() > 1 && first == second)
            {
                continue; // Remove triangulation seams and coplanar surface joins.
            }
            // A face cut into triangles because rounding left it off its plane (a converter's T-junction repair)
            // bends by well under a degree at its seams: still one surface, no outline.
            const auto nearlyCoplanar = [&planes, first](uint16_t faceId)
            {
                const double dot = planes[first].x * planes[faceId].x + planes[first].y * planes[faceId].y
                    + planes[first].z * planes[faceId].z;
                return dot >= NearlyCoplanarDot;
            };
            if (faces.size() > 1 && std::all_of(faces.begin(), faces.end(), nearlyCoplanar))
            {
                continue;
            }
            Game::IndoorOutline outline = {};
            outline.vertex1Id = edge.first;
            outline.vertex2Id = edge.second;
            outline.face1Id = first;
            outline.face2Id = second;
            outline.z = int16_t((geometry.vertices[edge.first].z + geometry.vertices[edge.second].z) / 2);
            geometry.outlines.push_back(outline);
        }
        mergeCollinearOutlines(geometry);
        if (geometry.outlines.size() > 7000)
        {
            errorMessage = "indoor outlines exceed the native 875-byte visibility bitset: "
                + std::to_string(geometry.outlines.size()) + " of at most 7000";
            return false;
        }
    }
    return true;
}
}
