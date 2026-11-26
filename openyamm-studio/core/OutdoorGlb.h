#pragma once

#include <array>
#include <cstddef>
#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A Blender model (a binary or text glTF) read as the faces of outdoor BModels (DECISIONS.md H-44: landmarks and
// dungeon entrances built in Blender and textured with the world's face textures). How it is read:
//
// - Every node with a mesh is one BModel (its node's name, else its mesh's). Skinned nodes are left out.
// - Corners in map units: the file's units times `scale`, turned from the file's up axis to the map's (glTF's own
//   +Y up, as Blender's exporter writes by default: map x = x, map y = -z, map z = y; `up: z` takes the file's axes
//   as the map's, as the studio's own GLB writer has them), turned and moved into place, then rounded to whole units
//   as a BModel stores them.
// - Each triangle (or a triangle fan kept as one polygon) keeps its material's name and its corners' first UV set.
// - Faces of one material that lie in one plane, share an edge and carry one continuous picture (the UVs of one
//   affine map) are joined into one convex polygon of up to 20 corners, as the shipped maps' faces are: a quad of
//   two triangles, an n-gon of a fan. Nothing non-convex is made.
// - Refused, with the face named: a face under `minArea` square units, a corner sharper than `minAngle` degrees (a
//   sliver), a face that is not convex (a fan polygon), more than `faceBudget` faces in one mesh, more than 65 535
//   corners in one mesh. A face that rounds to nothing (all its corners in a line) is dropped and counted.
struct OutdoorGlbOptions
{
    double scale = 1.0;
    // false: the file's +Y is up (glTF, Blender's default export); true: its +Z is.
    bool zUp = false;
    // After the axes and the scale: turned `turnDegrees` clockwise seen from above about `pivot` (map x, y), then
    // moved by `move`; all before the corners are rounded.
    double turnDegrees = 0.0;
    std::array<double, 2> pivot = {0.0, 0.0};
    std::array<double, 3> move = {0.0, 0.0, 0.0};
    double minArea = 32.0;
    double minAngleDegrees = 2.0;
    size_t faceBudget = 1000;
};

struct OutdoorGlbFace
{
    // Map units, counter-clockwise seen from the face's front: whole units, as stored; and as read, before rounding
    // (what the picture is checked against when faces are joined).
    std::vector<std::array<double, 3>> points;
    std::vector<std::array<double, 3>> exact;
    // The first UV set per corner: u across the picture, v down it (glTF's origin is the picture's top left).
    std::vector<std::array<double, 2>> uvs;
    bool hasUvs = false;
    std::string material;
};

struct OutdoorGlbMesh
{
    std::string name;
    std::vector<OutdoorGlbFace> faces;
    // Triangles read and faces that rounded to nothing.
    size_t triangles = 0;
    size_t dropped = 0;
};

// Reads the meshes; false with `errors` (each a sentence naming the mesh and the face) when the file cannot be read
// or breaks a limit.
bool readOutdoorGlb(const std::filesystem::path &path, const OutdoorGlbOptions &options,
    std::vector<OutdoorGlbMesh> &meshes, std::vector<std::string> &errors);

// Joins faces of one material lying in one plane with one continuous picture into convex polygons (readOutdoorGlb
// does it; open for tests).
void joinOutdoorGlbFaces(std::vector<OutdoorGlbFace> &faces);
}
