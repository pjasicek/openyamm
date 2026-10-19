#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
bool applyLocalizedTableOverlay(
    std::string_view contents,
    std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage
);
}
