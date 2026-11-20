#pragma once

#include "game/render/Mist.h"

#include <string>

namespace YAML
{
class Emitter;
class Node;
}

namespace OpenYAMM::Game
{
// Parses a scene's `mist` map (devdocs/MIST.md): an optional `layer` (or `layers`) and optional `volumes`, shared by indoor and
// outdoor scenes and their overlays. False with the reason for an unknown key or a value out of range.
bool parseSceneMistNode(const YAML::Node &node, MapMist &mist, std::string &errorMessage);
bool parseSceneMist(const std::string &yamlText, MapMist &mist, std::string &errorMessage);
// Writes the `mist` key and its map; nothing for a map without mist.
void emitSceneMist(YAML::Emitter &emitter, const MapMist &mist);
}
