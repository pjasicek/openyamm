#pragma once

#include "core/IndoorLowering.h"
#include "core/Json.h"

#include "game/indoor/IndoorMapData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What the studio's views draw (S5_BROWSER_EDITOR.md 2.9; the request list's view.layout and view.mesh): made from
// the lowering an indoor project's validation already ran (no compiler, BSP or GLB: compiled faces are lowered faces
// with whole-unit corners), and from an outdoor project's dry build. The client draws; the core decides where
// everything is.

// What an outdoor dry build leaves for the view (BuildOptions::pOutdoorView): the map as the game's loaders read it
// back, with its scene applied, and the texture of each tile number of the map.
struct OutdoorView
{
    std::string world;
    Game::OutdoorMapData map;
    // By the tile number a cell holds (OutdoorMapData::tileMap): the tile's texture in the world's tile table (empty:
    // unknown, as without an asset root) and whether the tile is water.
    std::array<std::string, 256> tileTextures;
    std::array<bool, 256> tileWater = {};
    // Where the party arrives (the plan's entrance), and its facing in the game's units (2048 a turn, 0 east).
    bool hasStart = false;
    std::array<double, 3> start = {};
    int startFacing = 0;
};

// Fills the tile textures of `view` from the world's tile table text (engine/data_tables/terrain_tile_data*.txt), as
// the game resolves a cell's tile number (game/maps/TerrainTileData.cpp).
void resolveOutdoorTileTextures(OutdoorView &view, const std::string &tileTableText);

// The binary mesh of view.mesh (view.rpc.json: positions, normals and texel coordinates per vertex, three indices a
// triangle grouped by texture, the face of each triangle, the owner of each face) and what its JSON answer says.
struct ViewMesh
{
    struct Section
    {
        size_t offset = 0;
        size_t count = 0;
    };

    struct Group
    {
        std::string texture;
        size_t first = 0;
        size_t count = 0;
        // Texture coordinates in texels (divide by the texture's size), or 0 to 1 across it (the outdoor land's tiles).
        bool unitUv = false;
        // surface, liquid, terrain, moving.
        std::string kind;
    };

    struct Owner
    {
        std::string id;
        std::string file;
    };

    std::vector<uint8_t> bytes;
    size_t vertices = 0;
    size_t triangles = 0;
    size_t faces = 0;
    Section positions;
    Section normals;
    Section uvs;
    Section indices;
    Section triangleFaces;
    Section faceOwners;
    std::vector<Group> groups;
    std::vector<Owner> owners;
    std::array<int64_t, 3> min = {0, 0, 0};
    std::array<int64_t, 3> max = {0, 0, 0};
};

// The indoor map's visible faces from its lowering: every face but the portals and the markers (decorations, lights,
// spawn points), and not those of invisible parts. Corners on whole units, as the compiler stores them. `liquids`
// says which textures the game draws as liquids.
ViewMesh indoorViewMesh(const LoweredIndoorMap &lowered, const LiquidTextures &liquids);

// A shipped indoor map's visible faces as the game stores them (the original a rebuild is compared with: Compare
// view): every face but portals and invisible ones, each owned by its sector (`sector:<n>`, no file), corners and
// texel coordinates as stored, moving parts where the map file has them.
ViewMesh shippedIndoorViewMesh(const Game::IndoorMapData &map, const LiquidTextures &liquids);

// The outdoor map's land (one quad a cell, by its tile's texture) and its models' visible faces.
ViewMesh outdoorViewMesh(const OutdoorView &view, const LiquidTextures &liquids);

// The result fields of view.layout after `revision`, `view_revision`, `stale`, `kind` and `world`.
void writeIndoorLayout(JsonWriter &writer, const LoweredIndoorMap &lowered);
void writeOutdoorLayout(JsonWriter &writer, const OutdoorView &view);
}
