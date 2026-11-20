#pragma once

#include <array>
#include <cstdint>
#include <span>
#include <string>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
// The BLV face draws (devdocs/INDOOR_FACE_DRAW_GROUPS.md). A face batch holds one sector's faces of one texture; the
// batches with the same draw state (texture, lightmap page, liquid colour) form a draw group whose vertices and
// indices share one buffer, so the main view draws a group's visible batches with few draw calls. The sectors, which
// the dynamic lights' portal reach tests, and whether a face takes the scene daylight are per vertex. A translucent face is a group of its own: those draw
// one by one, back to front.
//
// The batches once drew one by one in batch order, and where two faces cover the same pixels at one depth (nearly
// parallel faces overlapping: a panel on a wall, coincident faces) the later one's pixels win. So the draws keep that
// order for every two drawn batches with such faces (conflicts, indoorFacesMeetAtOneDepth) and may reorder all
// others: the drawn batches go out in a topological order of those pairs, a group at a time (each time the group with
// the most batches ready), one draw per turn. Faces that share only an edge or meet at an angle tie at most along
// that line, a pixel wide, and need no order.
struct IndoorFaceDrawGroupKey
{
    std::string textureName;
    int32_t lightmapPage = -1;
    uint32_t waterColorAbgr = 0;
    // The face index of a translucent face, -1 for opaque faces.
    int32_t translucentFace = -1;
    // Terrain faces whose pixels read one ground layer only, drawn with the single-material programs.
    bool singleMaterialTerrain = false;

    bool operator==(const IndoorFaceDrawGroupKey &other) const = default;
};

struct IndoorFaceDrawGroupKeyHash
{
    size_t operator()(const IndoorFaceDrawGroupKey &key) const;
};

using IndoorFacePoint = std::array<float, 3>;

// A face polygon prepared for indoorFaceReachesInterior: its plane (Newell's normal, following the winding), how far
// its corners stray from it, and the inward planes of its edges (convex faces only).
struct IndoorFaceShape
{
    std::vector<std::array<double, 3>> points;
    std::array<double, 3> normal = {0.0, 0.0, 0.0};
    double distance = 0.0;
    double flatness = 0.0;
    // A degenerate or non-convex face counts its whole plane (conservative).
    bool wholePlane = true;
    // Inward unit normal and offset of each edge's plane: inside where dot(normal, x) >= offset.
    std::vector<std::array<double, 4>> edgePlanes;
};

IndoorFaceShape makeIndoorFaceShape(std::span<const IndoorFacePoint> polygon);

// Whether some of `other` lies within depthSlack of `face`'s plane and inside `face`'s polygon shrunk by edgeInset:
// where it does, the two can meet at one depth with `other` over `face`'s interior.
bool indoorFaceReachesInterior(const IndoorFaceShape &face, const IndoorFaceShape &other, float depthSlack,
    float edgeInset);

// Whether two faces cover the same pixels at one depth, so their draw order decides which shows: their planes within
// IndoorFaceDrawMaxAngleDegrees of each other (a degenerate face counts as any plane) and one reaching the other's
// interior. Faces at a larger angle (a wall standing on a floor, a cornice under a wall, faces crossing) tie only
// along the line where they meet, about a pixel wide, like faces sharing an edge.
constexpr float IndoorFaceDrawMaxAngleDegrees = 30.0f;
bool indoorFacesMeetAtOneDepth(const IndoorFaceShape &first, const IndoorFaceShape &second, float depthSlack,
    float edgeInset);

// A batch's indices within its group's index list.
struct IndoorFaceIndexRange
{
    uint32_t firstIndex = 0;
    uint32_t indexCount = 0;

    bool operator==(const IndoorFaceIndexRange &other) const = default;
};

// One draw of some of a group's batches: a range of the group's own index list, or of the merged list (the drawn
// batches' indices, draw after draw) when they are not one run of its list in order.
struct IndoorFaceGroupDraw
{
    uint32_t group = 0;
    bool merged = false;
    uint32_t firstIndex = 0;
    uint32_t indexCount = 0;

    bool operator==(const IndoorFaceGroupDraw &other) const = default;
};

// The groups' index lists, the touching batches and the main view's draws, re-planned only when the drawn batches or
// the conflicts change.
class IndoorFaceDrawPlan
{
public:
    void clear();
    // Appends batch's indices (local to the batch, whose vertices start at vertexOffset in its group's buffer) to the
    // group's list. Batches are added in batch order (their ids ascending); groups are small dense ids.
    void addBatch(uint32_t group, uint32_t batch, std::span<const uint32_t> localIndices, uint32_t vertexOffset);
    // Two batches whose faces touch keep their batch order. Returns true when the pair is new.
    bool addConflict(uint32_t batch, uint32_t otherBatch);
    bool hasConflict(uint32_t batch, uint32_t otherBatch) const;
    size_t groupCount() const { return m_groupIndices.size(); }
    const std::vector<uint32_t> &groupIndices(uint32_t group) const { return m_groupIndices[group]; }
    IndoorFaceIndexRange batchRange(uint32_t batch) const;
    // Plans the draws of the drawn batches (one flag per batch). Returns true when it planned again (the drawn
    // batches or the conflicts changed), so the merged list must be uploaded again.
    bool update(std::span<const uint8_t> drawn);
    const std::vector<IndoorFaceGroupDraw> &draws() const { return m_draws; }
    const std::vector<uint32_t> &mergedIndices() const { return m_mergedIndices; }

private:
    void appendDraw(uint32_t group, const std::vector<uint32_t> &batches);

    std::vector<uint32_t> m_batchGroups;
    std::vector<std::vector<uint32_t>> m_groupIndices;
    std::vector<IndoorFaceIndexRange> m_batchRanges;
    // Per batch, the later batches its faces touch.
    std::vector<std::vector<uint32_t>> m_laterConflicts;
    std::unordered_set<uint64_t> m_conflictPairs;
    bool m_planned = false;
    std::vector<uint8_t> m_drawn;
    std::vector<IndoorFaceGroupDraw> m_draws;
    std::vector<uint32_t> m_mergedIndices;
};
}
