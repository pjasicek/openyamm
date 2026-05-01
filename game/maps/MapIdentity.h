#pragma once

#include <string>

namespace OpenYAMM::Game
{
constexpr const char *DefaultWorldId = "mm8";

std::string normalizeWorldId(const std::string &worldId);
std::string normalizeMapFileStem(const std::string &fileName);
std::string buildCanonicalMapId(const std::string &worldId, const std::string &fileName);
}

