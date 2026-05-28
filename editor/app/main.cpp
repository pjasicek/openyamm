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
    bool hasWorldArgument = false;

    for (int argumentIndex = 1; argumentIndex < argc; ++argumentIndex)
    {
        const std::string argument = argv[argumentIndex];

        if (argument == "--world")
        {
            if (hasWorldArgument || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --world <world-id>\n";
                return false;
            }

            config.activeWorldId = argv[argumentIndex + 1];
            hasWorldArgument = true;
            ++argumentIndex;
            continue;
        }

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
        config.assetScaleProfile = OpenYAMM::Engine::createUniformAssetScaleProfile(*assetScaleTier);
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

    if (arguments.size() == 2 && arguments[0] == "--headless-verify-model-instances")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyModelInstances(argv[0], arguments[1]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-verify-mm9-dat-level")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9DatLevel(argv[0], arguments[1]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-verify-mm9-dat-filters")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9DatFilters(argv[0], arguments[1]);
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-verify-mm9-event-provenance")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9EventProvenance(argv[0], arguments[1], arguments[2]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-verify-mm9-events")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9Events(argv[0], arguments[1]);
    }

    if (arguments.size() == 1 && arguments[0] == "--headless-verify-mm9-source-manifest")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9SourceManifest(argv[0]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-verify-mm9-inspector-search")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9InspectorSearch(argv[0], arguments[1]);
    }

    if (arguments.size() == 1 && arguments[0] == "--headless-verify-document-dispatch")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyDocumentDispatch(argv[0]);
    }

    if (arguments.size() == 1 && arguments[0] == "--headless-verify-all-mm9-dat-levels")
    {
        OpenYAMM::Editor::EditorHeadlessDiagnostics diagnostics(config);
        return diagnostics.runVerifyAllMm9DatLevels(argv[0]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-level")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-models")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::ModelInstancesOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-physics")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::PhysicsOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-sky")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::SkyOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-water")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::WaterOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-visibility")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::VisibilityOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-invisible")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::InvisibleOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-helper")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::HelperOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-render-mm9-dat-trigger")
    {
        OpenYAMM::Editor::EditorRenderSmokeConfig renderSmokeConfig = {};
        renderSmokeConfig.enabled = true;
        renderSmokeConfig.mapPath = arguments[1];
        renderSmokeConfig.mode = OpenYAMM::Editor::EditorRenderSmokeMode::TriggerOnly;
        OpenYAMM::Editor::EditorApplication editorApplication(config, renderSmokeConfig);
        const int result = editorApplication.run();
        std::exit(result);
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
