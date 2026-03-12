#pragma once

#include <string>

namespace OpenYAMM::Engine
{
struct ApplicationConfig
{
    std::string appName;
    std::string assetRoot;

    [[nodiscard]] static ApplicationConfig createDefault();
};
}
