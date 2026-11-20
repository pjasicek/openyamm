#pragma once

#include "core/MapLoad.h"
#include "core/Things.h"

#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The interactive things of an outdoor map (`oymap things` on an .odm or an outdoor project; round four of the outdoor
// rebuilds pictured them with a script of its own because the command refused outdoor maps): the faces of the
// map's models grouped by the event a click on them runs, and every decoration that runs an event. The fields are
// the indoor ones (core/Things.h) read for an outdoor map:
//   faces     model index * 65536 + face index;
//   sector    the model that holds most of the thing's faces (its index; `modelNames` names it), -1 for a
//             decoration;
//   ownDoors  empty (outdoor models have no door records);
//   kind      house (the click enters a house), chest, exit (another map), teleport, name (a thing that only says
//             its name: no handler, or one that does nothing), decoration (a clicked decoration), panel (anything
//             else);
//   stand     on the ground 256 in front of its largest upright face (along the summed outward normals of its
//             upright faces; south of a thing whose faces cancel out), the eye 160 over it looking at its middle.
// What overlaps it is not looked for outdoors.
std::vector<InteractiveThing> listOutdoorInteractiveThings(
    const LoadedMap &map,
    const std::string &flowJson,
    std::map<int, std::string> &modelNames);
}
