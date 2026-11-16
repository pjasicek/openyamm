#pragma once

#include "core/Polygon.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A surface of flat triangles over part of the plan: heights at points, straight between them. The uneven floor or
// ceiling of a room (rooms.yml `floor_points`, `floor_plane`, `ceiling_points`, `ceiling_plane`): what the cave
// floors of the shipped maps are made of.
struct HeightMesh
{
    // x, y and height.
    std::vector<std::array<double, 3>> points;
    // Places in `points`, counter-clockwise seen from above.
    std::vector<std::array<size_t, 3>> triangles;

    bool empty() const
    {
        return triangles.empty();
    }
};

// Cuts a region of the plan into triangles that use the given points and no others, except where two of the given
// lines cross (a point is added there).
// `ring`: the region's rim, counter-clockwise; it may be a ring with holes tied in by bridges, as cutHole returns.
// `points`: further points; those outside the region are left out.
// `lines`: lines the triangles must keep as edges (each is cut at the points lying on it and where it leaves the
// region; what lies outside is dropped).
// The remaining edges are chosen shortest first among those that cross no edge already chosen, so the same input
// always gives the same triangles. `vertices` receives the points used; `triangles` places in it, counter-clockwise.
// False, with `error`, when the region cannot be cut.
bool triangulateRegion(
    const std::vector<Point2> &ring,
    const std::vector<Point2> &points,
    const std::vector<std::array<Point2, 2>> &lines,
    std::vector<Point2> &vertices,
    std::vector<std::array<size_t, 3>> &triangles,
    std::string &error);

// The surface's height at a point: on the triangle that holds it; for a point off the mesh, on the nearest
// triangle, held to its corners' range. Heights within a hair of a whole number come out whole.
double meshHeightAt(const HeightMesh &mesh, double x, double y);

double meshLowest(const HeightMesh &mesh);
double meshHighest(const HeightMesh &mesh);

// How steeply a triangle rises: its rise for each unit of run.
double meshTriangleGradient(const HeightMesh &mesh, size_t triangle);

// Where the mesh's edges meet a straight line from `from` to `to` that runs along the mesh's rim or through it:
// distances from `from` of the mesh's points lying on the line and of the places its edges cross it, in order,
// without the two ends. Between two neighbouring places the surface is straight along the line.
std::vector<double> meshBreaksAlong(const HeightMesh &mesh, const Point2 &from, const Point2 &to);

// Joins triangles that lie in one plane into convex faces of at most `maximumCorners` corners. `corners`: the
// points as the map stores them, on whole units. Triangles that have no area there are dropped. A face is a list of
// places in `corners`, counter-clockwise seen from above; points in a line along a face's edge are kept, so that
// faces still meet their neighbours corner to corner.
std::vector<std::vector<size_t>> mergeFlatTriangles(
    const std::vector<std::array<int64_t, 3>> &corners,
    const std::vector<std::array<size_t, 3>> &triangles,
    size_t maximumCorners);
}
