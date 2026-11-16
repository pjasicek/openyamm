#pragma once

#include "core/Json.h"
#include "core/MapLoad.h"

#include "game/events/EventRuntime.h"

#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
enum class SurfaceKind : uint8_t
{
    None = 0,
    Floor,
    Wall,
    Ceiling,
};

struct RayHit
{
    bool hit = false;
    // Along the ray; the cast's cap when nothing was hit.
    double distance = 0.0;
    // The number the face was added with; -1 when nothing was hit.
    int32_t sourceId = -1;
    SurfaceKind kind = SurfaceKind::None;
    // Lower case; empty when nothing was hit.
    std::string texture;
    // The texel of the face's texture at the point hit (the face's stored coordinates and delta, carried over its
    // plane), when the face was added with them.
    bool hasTexel = false;
    std::array<double, 2> texel = {};
};

// Flat polygons to cast rays against: a ray meets a face where it crosses the face's plane inside its outline (an
// even-odd test in the plane, so an outline need not be convex). A ray that runs into the seam of two or more faces
// (within half a unit of the edge of each, inside none: a shared edge, a mesh vertex) meets the one of them it
// looks at most squarely and does not slip between; past the free edge of a single face it goes on. A face is seen
// from the side its normal points to only, as the game draws it. Faces are kept in a grid over x and y.
class RayScene
{
public:
    // `points` in order round the face; `normal` its seen side (any length), or all zero to take it from the
    // order of the points (counter-clockwise seen from the front). A face without area is not added. `pTexels`: the
    // texture's coordinates at each point (in texels), carried over the face's plane to the point a ray hits.
    bool addFace(
        const std::vector<std::array<double, 3>> &points,
        const std::array<double, 3> &normal,
        int32_t sourceId,
        const std::string &texture,
        const std::vector<std::array<double, 2>> *pTexels = nullptr);
    // After the last face and before the first cast.
    void build(double cellSize = 384.0);
    // How near the edges of two faces a ray may pass, outside both, and still meet one (0.5 unless set; 0: the
    // even-odd test alone, through which a ray at a mesh vertex can slip).
    void setSeamTolerance(double tolerance);
    // `direction` of length one.
    RayHit cast(const std::array<double, 3> &origin, const std::array<double, 3> &direction, double cap) const;
    // The heights of the faces over one point of the plan (walls have none), with each face's number. A point on
    // the edge of a face is over it, as the game's walk has it: on a ledge's edge both the ledge and the floor below
    // are found.
    std::vector<std::pair<double, int32_t>> heightsAt(double x, double y, bool withEdges = true) const;
    size_t faceCount() const;

private:
    struct Face
    {
        std::array<double, 3> normal = {};
        double offset = 0.0;
        std::array<double, 3> low = {};
        std::array<double, 3> high = {};
        // The outline without the axis the normal is longest on.
        int dropAxis = 2;
        std::vector<std::array<double, 2>> flat;
        std::vector<std::array<double, 2>> plan;
        int32_t sourceId = -1;
        SurfaceKind kind = SurfaceKind::None;
        std::string texture;
        // The texel at `texelOrigin` and how it changes per unit along the face's plane.
        bool hasTexel = false;
        std::array<double, 3> texelOrigin = {};
        std::array<double, 2> originTexel = {};
        std::array<double, 3> gradientU = {};
        std::array<double, 3> gradientV = {};
    };

    // A face whose edge a ray passes within the seam tolerance of, outside its outline.
    struct EdgeHit
    {
        double distance = 0.0;
        double approach = 0.0;
        uint32_t face = 0;
    };

    void testCell(
        size_t cell,
        const std::array<double, 3> &origin,
        const std::array<double, 3> &direction,
        double &best,
        int32_t &bestFace,
        std::vector<EdgeHit> &edgeHits) const;

    std::vector<Face> m_faces;
    std::vector<std::vector<uint32_t>> m_cells;
    double m_cellSize = 384.0;
    double m_seamTolerance = 0.5;
    double m_lowX = 0.0;
    double m_lowY = 0.0;
    int m_columns = 0;
    int m_rows = 0;
};

struct CompareOptions
{
    // Distance between stand points; rounded to the walk grid of 32.
    double step = 256.0;
    // The reading before 2026-11-13, kept to tell what each change did to a score: stand points exactly on their
    // grid points, a floor's edge not part of it, a ray through a seam meeting nothing, and only thin moving blocks
    // left out.
    bool pointsOnGrid = false;
    bool exactFloorEdges = false;
    bool openSeams = false;
    bool thinBlocksOnly = false;
    // And the moving parts as the scene stores them, without what the map's load events do to them.
    bool storedPoses = false;
    // A ray on the same texture in both maps whose picture lies at another phase (more than OffsetTolerance texels
    // apart along u or v, whole repeats aside) counts whole in the score (`ignoreOffsets`, the default, so totals stay
    // comparable with every earlier figure and the bands); its share is reported apart as `offset_agreement`, and
    // `offsets` say what each rebuilt surface needs. With `ignoreOffsets` false (`--offsets`) such a ray counts half.
    // The texture sizes by lower-case name (in the units a face is drawn in): a texture without one is not judged for
    // its offset.
    bool ignoreOffsets = true;
    std::map<std::string, std::array<int, 2>> textureSizes;
};

// Texels two pictures of one texture may lie apart and count as one.
constexpr double OffsetTolerance = 8.0;

// The offset a rebuilt face's surface needs so that its picture lies as the original's at one point: the original's
// texel less the rebuilt one's, brought into (-size / 2, size / 2] for each axis; nothing where they agree within
// OffsetTolerance or the size is unknown.
std::optional<std::array<double, 2>> offsetNeeded(
    const std::array<double, 2> &original, const std::array<double, 2> &rebuilt, const std::array<int, 2> &size);

// What the rebuild's surfaces need, by texture and offset: rays on the same texture whose pictures lie apart.
struct CompareOffset
{
    std::string texture;
    SurfaceKind kind = SurfaceKind::None;
    std::array<double, 2> offset = {};
    size_t rays = 0;
};

struct ComparePoint
{
    // On the original's floor.
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    // The original's sector the floor belongs to.
    int sector = 0;
    // The rebuild has a floor under the point within 512 of the original's height.
    bool hasFloor = false;
    double rebuiltZ = 0.0;
    // Share of rays whose distances agree, the mean error of those that do not, share of rays on the same texture.
    double distanceShare = 0.0;
    double meanError = 0.0;
    double textureShare = 0.0;
    // Rebuild minus original, after the maps' vertical offset.
    double floorDelta = 0.0;
    bool hasCeilingDelta = false;
    double ceilingDelta = 0.0;
    // 0.7 of the distance share and 0.3 of the texture share: what the worst points are ranked by.
    double score = 0.0;
    // Where to look to see the most of what differs: radians, 0 east, counter-clockwise.
    double worstYaw = 0.0;
    // The four largest differences in one sentence, and every difference, largest first.
    std::string sentence;
    std::vector<std::string> differences;
    // No place within reach of the grid point stands clear of floor edges and walls (a narrow ledge, a stair, a
    // slit): the point stayed on its grid point and its reading is less sure.
    bool onEdge = false;
};

struct CompareSector
{
    int sector = 0;
    size_t points = 0;
    size_t missingFloor = 0;
    double distanceShare = 0.0;
    double meanError = 0.0;
    double textureShare = 0.0;
    double meanFloorDelta = 0.0;
    double meanCeilingDelta = 0.0;
    double score = 0.0;
};

struct CompareTexturePair
{
    std::string original;
    std::string rebuilt;
    SurfaceKind kind = SurfaceKind::None;
    size_t rays = 0;
};

struct CompareResult
{
    std::string originalName;
    std::string rebuiltName;
    double step = 256.0;
    // How much higher (negative: lower) the whole rebuild lies than the original; 0 when the maps share their
    // heights. Floors are matched, and floor and ceiling differences given, with it taken out.
    double verticalOffset = 0.0;
    size_t originalFaces = 0;
    size_t rebuiltFaces = 0;
    // Every stand point of the original, ordered by x, y, z.
    std::vector<ComparePoint> points;
    // Indices into `points`: where the rebuild has no floor, and the worst of the others (worst first).
    std::vector<size_t> missingFloor;
    std::vector<size_t> worst;
    // Stand points of the rebuild over which the original has no floor: x, y, z.
    std::vector<std::array<double, 3>> extraFloor;
    size_t rebuiltPoints = 0;
    // Stand points moved off their grid point to stand clear of a floor edge or a wall, and those left on one.
    size_t movedPoints = 0;
    size_t edgePoints = 0;
    std::vector<CompareSector> sectors;
    // Rays that agree in distance and differ in texture, by pair, most rays first.
    std::vector<CompareTexturePair> texturePairs;
    // Rays that agree in distance and texture and whose pictures lie apart, by texture and offset needed (rounded to
    // 8 texels), most rays first; and the share of rays on the same texture whose pictures lie alike.
    std::vector<CompareOffset> offsets;
    size_t sameTextureRays = 0;
    size_t offsetRays = 0;
    size_t rays = 0;
    double distanceShare = 0.0;
    double meanError = 0.0;
    double textureShare = 0.0;
    // Among the rays whose distances agree.
    double textureShareWhereSeen = 0.0;
    double meanFloorDelta = 0.0;
    double meanCeilingDelta = 0.0;
    double score = 0.0;
};

// How alike two indoor maps drawn in the same coordinate frame are, by what is seen from where the party can stand
// (the method is in `oymap compare`'s usage). No game is run. In both maps every moving part stands as the party
// first sees it: in the scene's starting state, then moved as the map's load events move it on a first visit (each
// test of a handler answered no). Stand points are taken with every door out of the way, and those inside a part
// that is shut at the start are left out.
bool compareMaps(
    const LoadedMap &original,
    const LoadedMap &rebuilt,
    const CompareOptions &options,
    CompareResult &result,
    std::string &errorMessage);

// The moving parts as the party first sees them: where the map's load events put them on a first visit, each test
// of a handler answered no (a quest bit not yet set, a map variable still nothing). Parts no load event moves are
// not in the result and stay in the scene's starting state. `eventFlowJson` is core/EventFlow's result.
Game::EventRuntimeState posesAfterLoadEvents(
    const Game::MapDeltaData &state, const std::string &eventFlowJson, const std::vector<uint16_t> &loadEvents);

// The report: totals, sectors, the 40 worst points, missing and extra floor.
void writeCompareJson(const CompareResult &result, JsonWriter &writer);

// Every point that differs, by sector (worst first in each), with all its differences, and every stand point of
// the rebuild the original has no floor under: what a rebuild is corrected from, where the report only ranks.
void writeComparePointsJson(const CompareResult &result, JsonWriter &writer);

// A shots file for calibration/ingame_compare.py: the 12 worst points at least 1024 apart, each looking toward
// what differs most.
std::string compareShotsYaml(const CompareResult &result);

// Indices into `result.points` of the shots above.
std::vector<size_t> compareShotPoints(const CompareResult &result);

const char *surfaceKindName(SurfaceKind kind);
}
