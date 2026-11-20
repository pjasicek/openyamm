#pragma once

#include "core/IndoorLowering.h"
#include "core/Project.h"

#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// wiring.yml `cinematics` (devdocs/map_studio/S6_PLAN.md item C) as the game's `<stem>.cinematics.yml`
// (devdocs/mm9_rework/MM9_CUTSCENES.md section 3): shots with their camera places and aims resolved from the lowered
// map (an object's id: its place; a placed monster as an aim: the game follows the actor), cues with wiring events by
// their numbers and monsters by their actor index. Checked by the format's rules (one aim per key, keys from 0 in
// increasing time inside the shot, a field of view of 10 to 120, a subtitle's seconds), then read by the game's own
// parser (parseCinematicLibrary, game/gameplay/CinematicLibrary.h). Empty text when the project has no cinematics.
bool writeCinematicsText(
    const Project &project,
    const LoweredIndoorMap &lowered,
    std::string &text,
    std::vector<ProjectIssue> &issues);

// The cinematic's name in the game's file (the id without its kind): `cinematic:arrival` -> `arrival`.
std::string cinematicName(const std::string &id);
}
