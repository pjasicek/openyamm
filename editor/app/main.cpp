#include "editor/app/EditorApplication.h"
#include "editor/headless/EditorHeadlessDiagnostics.h"
#include "engine/ApplicationConfig.h"
#include "engine/AssetScaleTier.h"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

namespace
{
bool parseCommonArguments(
    int argc,
    char **argv,
    OpenYAMM::Engine::ApplicationConfig &config,
    std::vector<std::string> &arguments)
{
    bool hasAssetScaleArgument = false;

    for (int argumentIndex = 1; argumentIndex < argc; ++argumentIndex)
    {
        const std::string argument = argv[argumentIndex];

        if (argument != "--asset-scale")
        {
            arguments.push_back(argument);
            continue;
        }

        if (hasAssetScaleArgument || argumentIndex + 1 >= argc)
        {
            std::cerr << "Usage: --asset-scale <1|2|4|x1|x2|x4>\n";
            return false;
        }

        const std::optional<OpenYAMM::Engine::AssetScaleTier> assetScaleTier =
            OpenYAMM::Engine::parseAssetScaleTier(argv[argumentIndex + 1]);

        if (!assetScaleTier)
        {
            std::cerr << "Invalid asset scale: " << argv[argumentIndex + 1] << '\n';
            return false;
        }

        config.assetScaleTier = *assetScaleTier;
        hasAssetScaleArgument = true;
        ++argumentIndex;
    }

    return true;
}

int runApplication(int argc, char **argv)
{
    OpenYAMM::Engine::ApplicationConfig config = OpenYAMM::Engine::ApplicationConfig::createDefault();
    config.appName = "openyamm-editor";
    config.windowWidth = 1920;
    config.windowHeight = 1200;
    std::vector<std::string> arguments;

    if (!parseCommonArguments(argc, argv, config, arguments))
    {
        return 2;
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-run-regression-suite")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runRegressionSuite(argv[0], arguments[1]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-compare-outdoor-scene")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runCompareOutdoorScene(argv[0], arguments[1]);
    }

    OpenYAMM::Editor::EditorApplication editorApplication(config);
    return editorApplication.run();
}
}

int main(int argc, char **argv)
{
    try
    {
        return runApplication(argc, argv);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
