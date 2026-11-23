#pragma once

#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapDeltaData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Two drawn faces of an indoor map in one plane, facing the same way, whose polygons overlap by more than a sliver:
// the renderer draws both and they flicker (z-fighting). Found by findCoplanarFaces.
struct CoplanarPair
{
    uint32_t firstFace = 0;
    uint32_t secondFace = 0;
    // The overlap's area in square units, and its middle.
    double area = 0.0;
    std::array<double, 3> at = {};
    // "start": as the map starts (the scene's door states); "moved": every moving part at the other end of its way;
    // "quarter", "half", "three_quarters": every moving part that far along its way from the start (a leaf passing a
    // face midway flickers too). Past the start only pairs with a face of a moving part that an earlier pose does
    // not have already; in the poses between the ends only a moving face against a face that does not move or that
    // moves with it (two parts that happen to move at once meet there by chance, not by design).
    std::string pose;
    // The common plane's normal (unit length).
    std::array<double, 3> normal = {};
    // The original has the same pair at the same place (markPairsAsOriginal).
    bool asOriginal = false;
};

// Every such pair of the map, in the start pose, the poses between and the moved pose. Faces that are portals or
// invisible are not drawn and not looked at. Two planes are one when their normals agree within about a twentieth of
// a degree and they lie within one unit of each other; an overlap counts when it is at least 8 square units and on
// average 1.5 units wide (twice its area over its perimeter), so faces that only touch along an edge do not.
std::vector<CoplanarPair> findCoplanarFaces(const Game::IndoorMapData &map, const Game::MapDeltaData *pState);

// The area two flat polygons share seen along `normal` (both projected onto the plane through the origin across
// it), in square units; for faces of nearly parallel planes.
double projectedOverlapArea(
    const std::vector<std::array<double, 3>> &first,
    const std::vector<std::array<double, 3>> &second,
    const std::array<double, 3> &normal);

// Where a pair of faces in one plane lies and of what it is, to be found again in another map: the two textures
// (lower case, in order), the plane's normal and the overlap's middle.
struct CoplanarPlace
{
    std::string firstTexture;
    std::string secondTexture;
    std::array<double, 3> normal = {};
    std::array<double, 3> at = {};
};

std::vector<CoplanarPlace> coplanarPlaces(const Game::IndoorMapData &map, const std::vector<CoplanarPair> &pairs);

// Marks each pair (of `map`) that the original has at the same place (`originalPlaces`, of the original map): the
// same two textures, the same plane (normals within about a degree, planes within 2 units) and the overlaps'
// middles within 128 units of each other (a rebuild cuts its faces otherwise than the original). Returns how many
// it marked.
size_t markPairsAsOriginal(
    const Game::IndoorMapData &map,
    std::vector<CoplanarPair> &pairs,
    const std::vector<CoplanarPlace> &originalPlaces);

// The door record (its door id) that moves each face, for messages.
std::map<uint32_t, uint32_t> doorOfFaces(const Game::MapDeltaData *pState);

// What a message calls sectors, door records and events by (a project's ids from ids.lock.yml); a number without a
// name is said as "sector 12", "door 3", "event 40".
struct CoplanarNames
{
    std::map<int, std::string> sectors;
    std::map<int, std::string> doors;
    std::map<int, std::string> events;
};

// One sentence naming both faces (texture, room, the moving part or the clicked thing they belong to), the overlap
// and where it is.
std::string describeCoplanarPair(
    const Game::IndoorMapData &map,
    const Game::MapDeltaData *pState,
    const CoplanarPair &pair,
    const CoplanarNames &names);

// Outdoors: two drawn faces of the map's models (any two, of one model or of two) in one plane facing the same way and
// overlapping, by the same rules as findCoplanarFaces (the models do not move). Faces are named by their model and
// their number in it.
struct OutdoorCoplanarPair
{
    size_t firstModel = 0;
    size_t firstFace = 0;
    size_t secondModel = 0;
    size_t secondFace = 0;
    double area = 0.0;
    std::array<double, 3> at = {};
    std::array<double, 3> normal = {};
    bool asOriginal = false;
};

std::vector<OutdoorCoplanarPair> findOutdoorCoplanarFaces(const std::vector<Game::OutdoorBModel> &models);

// Outdoors: two drawn faces in one plane facing opposite ways (back to back) whose polygons overlap, by the same rules
// (planes within a unit, at least 8 square units and 1.5 units wide). The game draws every face of an outdoor model
// from both sides (no culling), so such a pair is drawn at one depth from either side and flickers: a sheet laid both
// ways (P2 feedback F31, the studio's tent canvas). A pair shut inside solids on both sides (two solids touching) is
// hidden and left out: open space as tools/xeen/check_faces.py tells it (six rays from 2 units each side of the
// overlap's middle; one meeting a face's front first, or nothing, is open; four of six).
std::vector<OutdoorCoplanarPair> findOutdoorBackToBackFaces(const std::vector<Game::OutdoorBModel> &models);

std::vector<CoplanarPlace> outdoorCoplanarPlaces(
    const std::vector<Game::OutdoorBModel> &models,
    const std::vector<OutdoorCoplanarPair> &pairs);

// As markPairsAsOriginal, against the original's places (outdoorCoplanarPlaces of the original's models).
size_t markOutdoorPairsAsOriginal(
    const std::vector<Game::OutdoorBModel> &models,
    std::vector<OutdoorCoplanarPair> &pairs,
    const std::vector<CoplanarPlace> &originalPlaces);

// What an outdoor build reads of the shipped original it is measured against (the places where the original's own
// faces lie in one plane), kept by a service per asset root, world and map so that a build does not open the asset
// root and read the original again (S5_BROWSER_EDITOR.md 2.4.3).
struct OutdoorOriginals
{
    // By "<asset root>|<world>|<map file>".
    std::map<std::string, std::vector<CoplanarPlace>> coplanarPlaces;
};

// Per model, the part each face belongs to (empty: not known): "part:<id>" for a building's parts.
using OutdoorFaceParts = std::vector<std::vector<std::string>>;

// One sentence naming both faces (structure, part, texture), the overlap and where it is; `backToBack` for a pair of
// findOutdoorBackToBackFaces.
std::string describeOutdoorCoplanarPair(
    const std::vector<Game::OutdoorBModel> &models,
    const OutdoorCoplanarPair &pair,
    const OutdoorFaceParts &parts,
    bool backToBack = false);

// The pairs of one structure's two parts (or two structures' parts) said once: how many pairs, their area, and
// what it looks like: "identical" when every drawn face of each part has a partner in the other, else the parts
// "run through each other" along shared planes. One sentence per group, the groups in the order first met. With
// `backToBack` the pairs of findOutdoorBackToBackFaces, said as such.
std::vector<std::string> describeOutdoorCoplanarGroups(
    const std::vector<Game::OutdoorBModel> &models,
    const std::vector<OutdoorCoplanarPair> &pairs,
    const OutdoorFaceParts &parts,
    bool backToBack = false);
}
