#pragma once

#include <array>
#include <cstddef>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Plane geometry for room outlines (PLAN.md section 12, S3): outlines may bend inward and carry points in a line.
using Point2 = std::array<double, 2>;

// Twice the area, positive when the points run counter-clockwise.
double polygonDoubleArea(const std::vector<Point2> &points);

// Whether no two edges cross or touch except neighbours at their shared corner.
bool polygonIsSimple(const std::vector<Point2> &points);

// Whether the point lies inside, at least `margin` away from every edge.
bool pointInPolygon(const std::vector<Point2> &points, const Point2 &point, double margin);

// Whether the point lies inside or on an edge or corner.
bool pointInOrOnPolygon(const std::vector<Point2> &points, const Point2 &point);

// Cuts a simple counter-clockwise polygon into convex pieces that use only its own points (so edges of the pieces
// meet corner to corner, also where the polygon has points in a line), each with at most `maximumCorners` corners.
// A piece is a list of indices into `points`, counter-clockwise. Empty when the polygon cannot be cut (not simple).
std::vector<std::vector<size_t>> convexPieces(const std::vector<Point2> &points, size_t maximumCorners);

// Whether two simple counter-clockwise polygons share area (touching along edges or at corners is not sharing).
bool polygonsOverlap(const std::vector<Point2> &first, const std::vector<Point2> &second);

// A point well inside: the centre of the polygon's largest convex piece.
Point2 polygonInteriorPoint(const std::vector<Point2> &points);

// Cuts a hole into a polygon: the result is one ring that runs round the outer polygon, crosses to the hole along a
// bridge, runs round the hole the other way and crosses back (so the bridge's two ends appear twice).
// convexPieces accepts such a ring. `hole` is counter-clockwise and lies inside `outer`. Empty when no bridge can be
// drawn without crossing an edge. `keepClear`: holes that will be cut after this one; the bridge keeps off them when
// it can, so that they can still be cut (a bridge through a later hole's place leaves no ring for it).
std::vector<Point2> cutHole(
    const std::vector<Point2> &outer,
    const std::vector<Point2> &hole,
    const std::vector<std::vector<Point2>> &keepClear = {});

// The outline of a corridor: the path's centre line widened by half the width to each side, with mitred corners and
// square ends, counter-clockwise, on whole units. Empty with `error` set when the path cannot be widened (a bend too
// sharp for its width, points too close).
std::vector<Point2> pathOutline(const std::vector<Point2> &path, double width, std::string &error);

// Two counter-clockwise polygons that touch along a stretch of edge (two plates side by side) as one: the outline
// round both. Empty when they share no stretch of edge, overlap, or the outline round them would not be simple.
std::vector<Point2> unionTouching(const std::vector<Point2> &first, const std::vector<Point2> &second);

// The part of a convex counter-clockwise polygon on the inner side of a line (the side `normal` points away from):
// points p with dot(p, normal) <= offset.
std::vector<Point2> clipConvex(const std::vector<Point2> &points, const Point2 &normal, double offset);
}
