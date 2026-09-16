#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/app/GameApplication.h"
#include "game/app/GameSettings.h"
#include "game/app/ProfilingControl.h"
#include "game/app/OpenYammMain.h"
#include "game/outdoor/HeadlessOutdoorDiagnostics.h"
#include "game/scenario/ScenarioHeadlessCommand.h"

#include <SDL3/SDL.h>

extern "C"
{
#include <libavutil/log.h>
}

#include <cctype>
#include <cstdlib>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
void setEnvironmentVariable(const char *pName, const char *pValue)
{
#if defined(_WIN32)
    _putenv_s(pName, pValue);
#else
    setenv(pName, pValue, 1);
#endif
}

bool parseCommonArguments(
    int argc,
    char **argv,
    OpenYAMM::Engine::ApplicationConfig &config,
    std::vector<std::string> &arguments,
    bool &worldArgumentProvided,
    bool &assetScaleArgumentProvided)
{
    bool hasAssetScaleArgument = false;
    bool hasMapOverrideArgument = false;
    bool hasWorldArgument = false;
    bool hasLoadUniqueActorArgument = false;
    worldArgumentProvided = false;
    assetScaleArgumentProvided = false;

    for (int argumentIndex = 1; argumentIndex < argc; ++argumentIndex)
    {
        const std::string argument = argv[argumentIndex];

        if (argument == "--gameplay-trace")
        {
            if (argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --gameplay-trace <trace-file>\n";
                return false;
            }

            setEnvironmentVariable("OPENYAMM_GAMEPLAY_TRACE", "1");
            setEnvironmentVariable("OPENYAMM_GAMEPLAY_TRACE_FILE", argv[argumentIndex + 1]);
            ++argumentIndex;
            continue;
        }

        if (argument == "--gameplay-trace-append")
        {
            setEnvironmentVariable("OPENYAMM_GAMEPLAY_TRACE_APPEND", "1");
            continue;
        }

        if (argument == "--map")
        {
            if (hasMapOverrideArgument || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --map <map-file>\n";
                return false;
            }

            config.startupMapFileOverride = argv[argumentIndex + 1];
            hasMapOverrideArgument = true;
            ++argumentIndex;
            continue;
        }

        if (argument == "--world")
        {
            if (hasWorldArgument || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --world <world-id>\n";
                return false;
            }

            config.activeWorldId = argv[argumentIndex + 1];
            hasWorldArgument = true;
            worldArgumentProvided = true;
            ++argumentIndex;
            continue;
        }

        if (argument == "--load-unique-actor")
        {
            if (hasLoadUniqueActorArgument || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --load-unique-actor <actor-index>\n";
                return false;
            }

            const std::string value = argv[argumentIndex + 1];
            if (value.empty())
            {
                std::cerr << "Invalid --load-unique-actor value: " << value << '\n';
                return false;
            }

            for (char ch : value)
            {
                if (!std::isdigit(static_cast<unsigned char>(ch)))
                {
                    std::cerr << "Invalid --load-unique-actor value: " << value << '\n';
                    return false;
                }
            }

            size_t parsedCharacters = 0;
            unsigned long long parsedActorIndex = 0;

            try
            {
                parsedActorIndex = std::stoull(value, &parsedCharacters, 10);
            }
            catch (const std::exception &)
            {
                std::cerr << "Invalid --load-unique-actor value: " << value << '\n';
                return false;
            }

            if (parsedCharacters != value.size()
                || parsedActorIndex > static_cast<unsigned long long>(std::numeric_limits<size_t>::max()))
            {
                std::cerr << "Invalid --load-unique-actor value: " << value << '\n';
                return false;
            }

            config.loadUniqueActorIndex = static_cast<size_t>(parsedActorIndex);
            hasLoadUniqueActorArgument = true;
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
        assetScaleArgumentProvided = true;
        ++argumentIndex;
    }

    return true;
}

void applySettingsConfigOverridesIfConfigured(
    OpenYAMM::Engine::ApplicationConfig &config,
    bool worldArgumentProvided,
    bool assetScaleArgumentProvided)
{
    const std::filesystem::path settingsPath = "settings.ini";

    if (!std::filesystem::exists(settingsPath))
    {
        return;
    }

    std::string error;
    const std::optional<OpenYAMM::Game::GameSettings> settings =
        OpenYAMM::Game::loadGameSettings(settingsPath, error);

    if (!settings)
    {
        std::cerr << "Failed to read settings from " << settingsPath.string() << ": " << error << '\n';
        return;
    }

    if (!worldArgumentProvided && !settings->startWorldId.empty())
    {
        config.activeWorldId = settings->startWorldId;
    }

    if (!settings->assetRoot.empty())
    {
        config.assetRoot = settings->assetRoot;
    }

    if (!assetScaleArgumentProvided)
    {
        config.assetScaleProfile = settings->assetScaleProfile;
    }

    config.fpsTrace = settings->fpsTrace;
    config.performanceTrace = settings->performanceTrace;
    config.hitchTrace = settings->hitchTrace;
    config.hitchThresholdMilliseconds = settings->hitchThresholdMilliseconds;
    config.verticalSync = settings->verticalSync;
}
}

int runApplication(int argc, char **argv)
{
    setGameplayProfilingEnabled(false);
    av_log_set_level(AV_LOG_ERROR);

    OpenYAMM::Engine::ApplicationConfig config = OpenYAMM::Engine::ApplicationConfig::createDefault();
    std::vector<std::string> arguments;
    bool worldArgumentProvided = false;
    bool assetScaleArgumentProvided = false;

    if (!parseCommonArguments(argc, argv, config, arguments, worldArgumentProvided, assetScaleArgumentProvided))
    {
        return 2;
    }

    applySettingsConfigOverridesIfConfigured(config, worldArgumentProvided, assetScaleArgumentProvided);

    if (!arguments.empty() && arguments[0].rfind("--headless-", 0) == 0)
    {
        setEnvironmentVariable("OPENYAMM_DISABLE_LOADING_OVERLAY", "1");
    }

    if (arguments.size() >= 2 && arguments[0] == "--headless-validate-scenario")
    {
        return OpenYAMM::Game::runScenarioHeadlessCommand(argv[0], config, arguments, true);
    }

    if (arguments.size() >= 2 && arguments[0] == "--headless-run-scenario")
    {
        return OpenYAMM::Game::runScenarioHeadlessCommand(argv[0], config, arguments, false);
    }

    if ((arguments.size() == 3 || arguments.size() == 4) && arguments[0] == "--headless-open-event")
    {
        const std::string mapFileName = arguments[1];
        const int parsedEventId = std::stoi(arguments[2]);

        if (parsedEventId < 0 || parsedEventId > 65535)
        {
            return 2;
        }

        float advanceSeconds = 0.0f;

        if (arguments.size() == 4)
        {
            advanceSeconds = std::stof(arguments[3]);

            if (advanceSeconds < 0.0f)
            {
                return 2;
            }
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runOpenEvent(
            argv[0],
            mapFileName,
            static_cast<uint16_t>(parsedEventId),
            advanceSeconds);
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-open-actor")
    {
        const std::string mapFileName = arguments[1];
        const int parsedActorIndex = std::stoi(arguments[2]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runOpenActor(argv[0], mapFileName, static_cast<size_t>(parsedActorIndex));
    }

    if (arguments.size() >= 4 && arguments[0] == "--headless-run-dialog-sequence")
    {
        const std::string mapFileName = arguments[1];
        const int parsedEventId = std::stoi(arguments[2]);

        if (parsedEventId < 0 || parsedEventId > 65535)
        {
            return 2;
        }

        std::vector<size_t> actionIndices;

        for (size_t argumentIndex = 3; argumentIndex < arguments.size(); ++argumentIndex)
        {
            const int parsedActionIndex = std::stoi(arguments[argumentIndex]);

            if (parsedActionIndex < 0)
            {
                return 2;
            }

            actionIndices.push_back(static_cast<size_t>(parsedActionIndex));
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runDialogSequence(argv[0], mapFileName, static_cast<uint16_t>(parsedEventId), actionIndices);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-run-regression-suite")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runRegressionSuite(argv[0], arguments[1]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-profile-map-load-full")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runProfileFullMapLoad(argv[0], arguments[1]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-dump-outdoor-navigation")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runDumpOutdoorNavigation(argv[0], arguments[1]);
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-verify-outdoor-world-item-floor")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runVerifyOutdoorWorldItemFloor(argv[0], arguments[1]);
    }

    if (arguments.size() == 4 && arguments[0] == "--headless-verify-outdoor-save-roundtrip")
    {
        const int parsedChestEventId = std::stoi(arguments[2]);
        const int parsedMechanismEventId = std::stoi(arguments[3]);

        if (parsedChestEventId < 0 || parsedChestEventId > 65535
            || parsedMechanismEventId < 0 || parsedMechanismEventId > 65535)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runVerifyOutdoorSaveRoundtrip(
            argv[0],
            arguments[1],
            static_cast<uint16_t>(parsedChestEventId),
            static_cast<uint16_t>(parsedMechanismEventId));
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-verify-outdoor-mechanism-passage")
    {
        const unsigned long parsedMechanismId = std::stoul(arguments[2]);

        if (parsedMechanismId == 0 || parsedMechanismId > UINT32_MAX)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runVerifyOutdoorMechanismPassage(
            argv[0],
            arguments[1],
            static_cast<uint32_t>(parsedMechanismId));
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-verify-mm9-positioned-transition")
    {
        const unsigned long parsedSourceObjectIndex = std::stoul(arguments[2]);

        if (parsedSourceObjectIndex > UINT32_MAX)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runVerifyMm9PositionedTransition(
            argv[0],
            arguments[1],
            static_cast<uint32_t>(parsedSourceObjectIndex));
    }

    if (arguments.size() == 2 && arguments[0] == "--headless-capture-projectile-fx")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runCaptureProjectileFx(argv[0], arguments[1]);
    }

    if ((arguments.size() == 5 || arguments.size() == 6 || arguments.size() == 7)
        && arguments[0] == "--headless-simulate-actor")
    {
        const std::string mapFileName = arguments[1];
        const int parsedActorIndex = std::stoi(arguments[2]);
        const int parsedStepCount = std::stoi(arguments[3]);
        const float deltaSeconds = std::stof(arguments[4]);
        const float partyOffsetX = arguments.size() >= 6 ? std::stof(arguments[5]) : 6000.0f;
        const int parsedPreEventId = arguments.size() == 7 ? std::stoi(arguments[6]) : 0;

        if (parsedActorIndex < 0 || parsedStepCount <= 0 || deltaSeconds <= 0.0f
            || parsedPreEventId < 0 || parsedPreEventId > 65535)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runSimulateActor(
            argv[0],
            mapFileName,
            static_cast<size_t>(parsedActorIndex),
            parsedStepCount,
            deltaSeconds,
            partyOffsetX,
            static_cast<uint16_t>(parsedPreEventId));
    }

    if ((arguments.size() == 5 || arguments.size() == 6)
        && arguments[0] == "--headless-trace-actor-ai")
    {
        const std::string mapFileName = arguments[1];
        const int parsedActorIndex = std::stoi(arguments[2]);
        const int parsedStepCount = std::stoi(arguments[3]);
        const float deltaSeconds = std::stof(arguments[4]);
        const float partyOffsetX = arguments.size() == 6 ? std::stof(arguments[5]) : 6000.0f;

        if (parsedActorIndex < 0 || parsedStepCount <= 0 || deltaSeconds <= 0.0f)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runTraceActorAi(
            argv[0],
            mapFileName,
            static_cast<size_t>(parsedActorIndex),
            parsedStepCount,
            deltaSeconds,
            partyOffsetX);
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-inspect-actor-preview")
    {
        const std::string mapFileName = arguments[1];
        const int parsedActorIndex = std::stoi(arguments[2]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runInspectActorPreview(argv[0], mapFileName, static_cast<size_t>(parsedActorIndex));
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-dump-actor-support")
    {
        const std::string mapFileName = arguments[1];
        const int parsedActorIndex = std::stoi(arguments[2]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runDumpActorSupport(argv[0], mapFileName, static_cast<size_t>(parsedActorIndex));
    }

    if (arguments.size() == 4 && arguments[0] == "--headless-dump-actor-preview-texture")
    {
        const std::string mapFileName = arguments[1];
        const int parsedActorIndex = std::stoi(arguments[2]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runDumpActorPreviewTexture(
            argv[0],
            mapFileName,
            static_cast<size_t>(parsedActorIndex),
            arguments[3]);
    }

    OpenYAMM::Game::GameApplication application(config);
    return application.run();
}
}

#ifndef OPENYAMM_NO_DESKTOP_MAIN
int main(int argc, char **argv)
{
    try
    {
        return OpenYAMM::Game::runApplication(argc, argv);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
#endif
