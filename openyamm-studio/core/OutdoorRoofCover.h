#pragma once

#include "core/Polygon.h"

#include <optional>
#include <vector>

namespace OpenYAMM::Studio
{
// One roof over an outline that bends in (batch S4R): an L, a notched front, a box with a cut corner joined to
// another. The outline is covered by its largest convex pieces, which overlap where the outline's wings meet (an
// L's corner square lies in both wings). Each piece has the roof its own outline would have: a hip slopes from every
// side of the piece, a gable has two slopes from a ridge that runs out along its wing (or along one direction for
// all); a narrower gable ends at the ridge of the wider one it runs into. The roof over a point is the highest of the pieces' roofs there, so wings meet in valleys and the corners
// away from the join keep their hips or gables, as the shipped L-shaped houses do. Heights are runs: distances from
// the eaves line in the slope's own measure; the caller turns them into heights with one slope for every piece.

// h(p) = a x + b y + c.
struct RoofRun
{
    double a = 0.0;
    double b = 0.0;
    double c = 0.0;
};

struct RoofCoverFace
{
    // Counter-clockwise seen from above.
    std::vector<Point2> points;
    size_t piece = 0;
    size_t plane = 0;
};

// An upright face under the roof's edge (a gable end, the end of a stretch of eaves): [x, y, run] points.
using RoofProfileFace = std::vector<std::array<double, 3>>;

class RoofCover
{
public:
    // `walls`: the outline the slopes rise from (counter-clockwise, simple). `gable`: two slopes per piece, else a
    // hip. `ridge`: one ridge direction for every piece (a unit vector).
    // `hipRun`: a hip's ridge drawn in this far from each end (the slopes over the sides that look along the ridge
    // steeper, reaching the ridge's height after that run), as an outline part's `hip`; 0: every side alike.
    // `sameSlope`: every piece at one slope (a ridge as high as its piece is wide; a roof given by its pitch); else
    // every piece rises to the same height, the narrower steeper. A gable piece narrower than one it runs into ends at
    // that one's ridge. Left out, a gable piece's ridge runs away from where it meets the others (else along its
    // longest side).
    RoofCover(const std::vector<Point2> &walls, bool gable, const std::optional<Point2> &ridge, double hipRun = 0.0,
        bool sameSlope = false);

    const std::vector<std::vector<Point2>> &pieces() const
    {
        return m_pieces;
    }

    // The greatest run under the roof (where it is highest).
    double deepest() const
    {
        return m_deepest;
    }

    // The run over a point: the highest of the roofs of the pieces it lies in; 0 outside them all.
    double runAt(const Point2 &point) const;

    // The roof's slopes over `region` (the outline the roof covers, inside `walls`; empty: `walls`), each a convex
    // face on one plane.
    std::vector<RoofCoverFace> faces(const std::vector<Point2> &region) const;

    double runOf(const RoofCoverFace &face, const Point2 &point) const;

    // The upright faces between the region's outline and the roof over it where the roof stands higher than its
    // foot there (gable ends; the ends and sides of a stretch without eaves), each convex.
    std::vector<RoofProfileFace> profiles(const std::vector<Point2> &region) const;

private:
    std::vector<std::vector<Point2>> m_pieces;
    std::vector<std::vector<RoofRun>> m_runs;
    double m_deepest = 0.0;
};

// The outline's largest convex pieces (counter-clockwise), overlapping where wings meet; a convex outline is its own.
std::vector<std::vector<Point2>> roofCoverPieces(const std::vector<Point2> &outline);

// A simple counter-clockwise outline cut into convex pieces that do not overlap; a convex outline is its one piece
// as given.
std::vector<std::vector<Point2>> convexPartsOf(const std::vector<Point2> &outline);

// What lies in `outer` and not in `inner` (both simple, counter-clockwise), in convex pieces.
std::vector<std::vector<Point2>> areaBetween(const std::vector<Point2> &outer, const std::vector<Point2> &inner);

// Whether a counter-clockwise outline bends in anywhere.
bool outlineBendsIn(const std::vector<Point2> &outline);
}
