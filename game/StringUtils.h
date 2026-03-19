#pragma once

#include <cctype>
#include <string>

namespace OpenYAMM::Game
{
inline std::string toLowerCopy(const std::string &value)
{
    std::string lowered = value;

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}
}
