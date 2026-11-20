#pragma once

#include "game/events/MechanismAudioProfile.h"

#include <yaml-cpp/yaml.h>

#include <string>

namespace OpenYAMM::Game
{
// A scene mechanism's or door's `sounds` block: open, close, open_start, open_busy, open_stop, close_start,
// close_busy, close_stop, jiggle (world sound names) and an optional position {x, y, z} (the sounds come from there).
bool parseMechanismAudioProfile(const YAML::Node &node, MechanismAudioProfile &profile, std::string &errorMessage);
// Writes the block's set fields as the value of the emitter's current key.
void emitMechanismAudioProfile(YAML::Emitter &emitter, const MechanismAudioProfile &profile);
}
