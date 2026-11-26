#pragma once

#include "core/MapLoad.h"
#include "core/Project.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
struct Image
{
    int width = 0;
    int height = 0;
    // RGB, row by row from the top.
    std::vector<uint8_t> pixels;
};

// A PNG file of the image (uncompressed inside: no dependency, the same bytes on every platform).
std::vector<uint8_t> encodePng(const Image &image);

enum class PreviewView
{
    Plan,
    Isometric,
};

struct PreviewOptions
{
    PreviewView view = PreviewView::Plan;
    // Longest side in pixels. 1568 is what an image-reading model sees without downscaling.
    int size = 1568;
    bool labels = true;
    // For an outdoor map, what each of its 128 x 128 cells holds as its tiles say (core/OutdoorGround's
    // outdoorCellKinds): 0 land, 1 shore, 2 open water, 3 road, 4 tar or lava. Empty: the tiles were not read, and
    // the land is drawn without water or roads.
    std::vector<uint8_t> cellKinds;
};

// A drawing of a map from its data, for people and agents to point at (PLAN.md section 2, `core/preview`): it shows
// structure, not materials. Indoor: every sector's floors in its own colour with its number, portals in green, door
// faces in red with their door number, the party start, spawn points. Outdoor: the terrain by height, water, shore
// and roads as the tiles have them, the buildings' footprints with their numbers, spawn points.
Image renderPreview(const LoadedMap &map, const PreviewOptions &options);

struct SketchPreviewOptions
{
    // Side of the square picture in pixels.
    int size = 1568;
    bool labels = true;
    // The part of the map to draw, [x, y, width, depth] in cells: the whole map, or a close view of a town.
    // Width or depth 0: the whole map (128 cells each way on a classic map, core/OutdoorGrid).
    std::array<double, 4> region = {0.0, 0.0, 0.0, 0.0};
};

// The plan picture of an outdoor project's sketch.yml on the 128 x 128 cell map, north up (the sketch's y runs
// south, so y = 0 is the top row): the land by height (the coarse grid as shading when there is one, else the height
// bands as tints), water, shores, cliffs with ticks on their low side, a dotted cell grid every 8 cells (every 2 in a
// close view), district
// outlines, roads by width class, plots as rectangles with the door side in red, encounter and keep-clear areas as
// dashed rings, views as arrows, points with short labels, the playable square and its exit spans. Reads the files
// as they are, so a sketch with issues still draws what can be read.
Image renderSketch(const Project &project, const SketchPreviewOptions &options);

// A point drawn over a plan: a stand point of a comparison, a finding.
struct PlanMark
{
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    std::array<uint8_t, 3> color = {255, 255, 255};
    // In pixels.
    int radius = 4;
    // A short number beside the mark; empty for none.
    std::string label;
};

// The plan of an indoor map in greys (floors by height, door faces in dull red) with marks over it, for pictures
// that show a value at many points of a map (`oymap compare`). Marks are drawn in order, labels last.
Image renderMarkedPlan(const LoadedMap &map, const std::vector<PlanMark> &marks, int size = 1568);
}
