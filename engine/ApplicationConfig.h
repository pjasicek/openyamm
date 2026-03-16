#pragma once

#include <string>

namespace OpenYAMM::Engine
{
struct ApplicationConfig
{
    std::string appName;
    std::string assetRoot;
    int windowWidth;
    int windowHeight;

    static ApplicationConfig createDefault();
};
}
