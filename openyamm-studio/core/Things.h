#pragma once

#include "core/Coplanar.h"
#include "core/MapLoad.h"

#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Something the player uses in an indoor map (the user's walk through Gharik's Forge, 2026-11-13, found what no
// check had seen at the things he used): the faces one event is bound to, what kind of thing they are, what using it
// changes, and where a player stands to use it.
struct InteractiveThing
{
    int eventId = 0;
    std::string title;
    // "door" (its own faces are a door record it moves, larger than 96), "lever" or "button" (its own faces are a
    // small door record it moves, down or sideways), "switch" (moves other door records or changes textures), "chest",
    // "exit" (leaves the map), "teleport", "decoration" (a clicked decoration), "panel" (anything else clicked).
    std::string kind;
    std::vector<uint32_t> faces;
    // Textures of its faces and how many faces carry each.
    std::map<std::string, int> textures;
    int sector = 0;
    // Its faces' bounds and middle.
    std::array<double, 3> low = {};
    std::array<double, 3> high = {};
    std::array<double, 3> middle = {};
    // The door records its own faces belong to.
    std::vector<uint32_t> ownDoors;
    // What its handler does on its first path (the effects `oymap flow` reads), and the faces those effects move or
    // retexture: "door 4 close: 12 faces (lavatyl 8, BemH16a 4)".
    std::vector<std::string> effects;
    std::vector<std::string> changes;
    // Where a player stands to use it (the floor there), the way he looks (radians, 0 east, counter-clockwise) and
    // down or up at its middle (radians, up positive) from the party's eye (160 over the floor).
    std::array<double, 3> stand = {};
    double yaw = 0.0;
    double pitch = 0.0;
    // Whether running its event in a picture tour is harmless (it neither opens a chest's screen, asks, nor leaves
    // or teleports).
    bool safeToUse = false;
    // Faces in one plane over this thing's (z-fighting, core/Coplanar.h), and clicked faces that lie over more than
    // one face of the wall behind them (a plate half over a corner strip).
    std::vector<std::string> overlaps;
};

// Every interactive thing of an indoor map, by event number. `flowJson` is exploreEventHandlers' output (empty: no
// effects are said). `names` turns numbers into a project's ids in the texts.
std::vector<InteractiveThing> listInteractiveThings(
    const LoadedMap &map,
    const std::string &flowJson,
    const CoplanarNames &names);
}
