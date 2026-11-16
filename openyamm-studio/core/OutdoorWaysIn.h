#pragma once

#include "core/OutdoorModel.h"
#include "core/Project.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Ways in: dungeon entrances built into the land (`kind: cave_mouth`, `kind: hatch`) and the arched heads of
// openings. Measured on Shadowspire's Yaardrake's Cave (d49out_W, _W_1: 104 faces), Emerald Island's dragon cave
// (DragonCave_E*), Regna's d34entrance_N and d47out_W, Ironsand's Chain of Fire (CoFent_S, a wedge), Ravage
// Roaming's Balthazar Lair (d24entranceA, a pit) and the MM6 arched doors (outc3 DunEntC3, oute2 archesN); the
// method is told at the top of OutdoorWaysIn.cpp.

// The head of an arched opening `width` wide whose top stands `height` over its foot, from the left spring to the
// right spring as [across from the middle, height over the foot]: `round` a half ellipse (rising at most half the
// width), `pointed` two arcs meeting at the top (an equilateral arch, rising at most 0.87 of the width), `sides`
// segments; `segment` an arc of a circle flatter than a half circle (a segmental arch: the bridges of 7out04 and
// out09, flat sewer heads), rising `rise` over its springs (a quarter of the width when 0). Every head is convex.
std::vector<std::array<double, 2>> outdoorArchHead(double width, double height, const std::string &form, int sides,
    double rise = 0.0);

// A cave mouth or a hatch, as read from the sketch's `structures` and placed by the lowering.
struct OutdoorCavePlan
{
    std::string id;
    // structures[i], for messages.
    std::string path;
    // cave_mouth or hatch; a hatch's form: wedge or pit.
    std::string kind;
    std::string form;
    // The footprint's middle in world units and its turn (degrees clockwise; 0: the mouth looks south).
    double x = 0.0;
    double y = 0.0;
    double turn = 0.0;
    // The footprint: across the mouth and from the front to the back, map units.
    double width = 1024.0;
    double depth = 1024.0;
    // The top over the floor (a hatch's `height`).
    double crest = 736.0;
    bool floorGiven = false;
    // The floor's height (the land under the mouth); set by the lowering when not given.
    double floor = 0.0;
    double mouthWidth = 512.0;
    double mouthHeight = 384.0;
    double mouthDepth = 256.0;
    int mouthSides = 6;
    // arch (an open dark mouth) or door (a flat front with a door slab).
    std::string mouthForm = "arch";
    // How far the rim stands round the mouth, and how far back the mouth is from the rim's front.
    double rim = 72.0;
    double rimDepth = 72.0;
    // How far the mouth stands back behind the rim's front, the rim's faces a recess narrowing to it (the mouth set
    // back behind a ledge, as Emerald Island's dragon cave: its dark face about 620 behind the footprint's front, the
    // floor before it rising 72 to 128), and how high the ledge in the recess rises to the mouth's foot, over a ramp
    // in `ledgeTexture`.
    double setback = 0.0;
    double ledge = 0.0;
    std::string ledgeTexture;
    // The tunnel's far end against its mouth.
    double narrow = 0.85;
    // Where the land under the sides begins to rise to the crest, from the front.
    double shoulder = 512.0;
    double roughness = 0.5;
    uint32_t seed = 0;
    // A mound standing on level land, closed all round.
    bool free = false;
    // Rings of faces between the rim and the footprint's edge.
    int rings = 2;
    // A pit's rim thickness.
    double thickness = 32.0;
    // A pit's outer walls reach this far under its floor: as far as the land at its corners lies lower (0 on level
    // land, as Balthazar Lair's rim stands).
    double skirt = 0.0;
    std::string shellTexture;
    std::string doorTexture;
};

// The sketch's cave mouths and hatches, checked. Messages go to `issues`.
std::vector<OutdoorCavePlan> readOutdoorCaves(
    const Project &project,
    const std::string &world,
    std::vector<ProjectIssue> &issues);

// Sets the land under each: the floor under the mouth and the front, the back row to the crest, the nodes under the
// shell below it (a free mound and a hatch's pit: level at the floor). `ground` per node (index y * 128 + x), map
// units; `waterNode` the water's level, NaN where dry. Sets each plan's floor. Warns where the land behind a mouth
// lies lower than its crest.
void shapeOutdoorCaveLand(
    std::vector<OutdoorCavePlan> &caves,
    std::vector<double> &ground,
    const std::vector<double> &waterNode,
    std::vector<std::string> &warnings);

// The faces of one: the shell without floor or back, the tunnel and the dark face (the door), all carrying
// `event`. The door's faces are added to `doorFaces`.
void raiseOutdoorCave(
    const OutdoorCavePlan &cave,
    OutdoorModelBuilder &builder,
    uint16_t event,
    std::vector<int> &doorFaces);
}
