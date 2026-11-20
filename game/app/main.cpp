#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/LogFile.h"
#include "engine/UserDataPaths.h"
#include "engine/update/AppInstallation.h"
#if defined(__APPLE__)
#include "game/app/AppleBundlePaths.h"
#endif
#include "game/app/ContentSetup.h"
#include "game/app/GameApplication.h"
#include "game/app/GameSettings.h"
#include "game/app/GameUpdater.h"
#include "game/app/ProfilingControl.h"
#include "game/app/OpenYammMain.h"
#include "game/indoor/IndoorBakeSceneExport.h"
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
#include <optional>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// Written to the user data folder, next to settings.ini and the saves.
constexpr const char *LogFileName = "openyamm.log";

void setEnvironmentVariable(const char *pName, const char *pValue)
{
#if defined(_WIN32)
    _putenv_s(pName, pValue);
#else
    setenv(pName, pValue, 1);
#endif
}

void printUsage(std::ostream &stream, const char *pProgram)
{
    stream << "Usage: " << pProgram << " [options] [--headless-<command> <arguments>...]\n"
           << "Without a headless command the game starts.\n"
           << "\n"
           << "Options:\n"
           << "  -h, --help                       Show this help and exit\n"
           << "  --world <world-id>               Start world (mm6, mm7, mm8, ...)\n"
           << "  --map <map-file>                 Start on this map\n"
           << "  --ruleset <id>[:<option>...]     Ruleset of a new game, such as maw:hell:horizontal\n"
           << "  --asset-root <directory>         Content root\n"
           << "  --extra-mount <directory>        Development: read this folder's engine/ and worlds/<id>/ map files\n"
           << "                                   in front of a development content root\n"
           << "  --asset-scale <1|2|4|x1|x2|x4>   Asset scale tier\n"
           << "  --user-data <directory>          Folder of settings.ini, saves and the log\n"
           << "  --load-unique-actor <index>      Load only this actor of the map\n"
           << "  --gameplay-trace <trace-file>    Write a gameplay trace\n"
           << "  --gameplay-trace-append          Append to the gameplay trace\n"
           << "\n"
           << "Headless commands:\n"
           << "  --headless-run-scenario <scenario.yml> [--scenario-dry-run] [--scenario-quiet] "
              "[--scenario-no-color]\n"
           << "  --headless-validate-scenario <scenario.yml> [scenario flags]\n"
           << "  --headless-update [channel-url]\n"
           << "  --headless-open-event <map> <event-id> [advance-seconds]\n"
           << "  --headless-open-actor <map> <actor-index>\n"
           << "  --headless-run-dialog-sequence <map> <event-id> <action-index>...\n"
           << "  --headless-run-regression-suite <suite>\n"
           << "  --headless-validate-actor-models [--all-worlds]\n"
           << "  --headless-profile-map-load-full <map>\n"
           << "  --headless-dump-outdoor-navigation <map>\n"
           << "  --headless-check-indoor-reachability <map.blv> <pairs.yml> <output.yml>\n"
           << "  --headless-export-decoration-models <map> <output-directory>\n"
           << "  --headless-export-indoor-bake-scene <map.blv> <output.json>\n"
           << "  --headless-verify-outdoor-world-item-floor <map>\n"
           << "  --headless-verify-outdoor-save-roundtrip <map> <chest-event-id> <mechanism-event-id>\n"
           << "  --headless-verify-outdoor-mechanism-passage <map> <mechanism-id>\n"
           << "  --headless-verify-mm9-positioned-transition <map> <source-object-index>\n"
           << "  --headless-capture-projectile-fx <output>\n"
           << "  --headless-simulate-actor <map> <actor-index> <steps> <delta-seconds> [party-offset-x] "
              "[pre-event-id]\n"
           << "  --headless-trace-actor-ai <map> <actor-index> <steps> <delta-seconds> [party-offset-x]\n"
           << "  --headless-inspect-actor-preview <map> <actor-index>\n"
           << "  --headless-dump-actor-support <map> <actor-index>\n"
           << "  --headless-dump-actor-preview-texture <map> <actor-index> <output>\n";
}

bool parseCommonArguments(
    int argc,
    char **argv,
    OpenYAMM::Engine::ApplicationConfig &config,
    std::vector<std::string> &arguments,
    bool &worldArgumentProvided,
    bool &assetScaleArgumentProvided,
    bool &assetRootArgumentProvided,
    std::optional<std::filesystem::path> &userDataRoot)
{
    bool hasAssetScaleArgument = false;
    bool hasMapOverrideArgument = false;
    bool hasWorldArgument = false;
    bool hasLoadUniqueActorArgument = false;
    worldArgumentProvided = false;
    assetScaleArgumentProvided = false;
    assetRootArgumentProvided = false;
    userDataRoot.reset();

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

        if (argument == "--user-data")
        {
            if (userDataRoot || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --user-data <directory>\n";
                return false;
            }

            userDataRoot = std::filesystem::path(argv[argumentIndex + 1]);
            ++argumentIndex;
            continue;
        }

        if (argument == "--asset-root")
        {
            if (assetRootArgumentProvided || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --asset-root <directory>\n";
                return false;
            }

            config.assetRoot = argv[argumentIndex + 1];
            assetRootArgumentProvided = true;
            ++argumentIndex;
            continue;
        }

        if (argument == "--extra-mount")
        {
            if (!config.installedContent.extraMountRoot.empty() || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --extra-mount <directory>\n";
                return false;
            }

            std::error_code absoluteError;
            config.installedContent.extraMountRoot = std::filesystem::absolute(argv[argumentIndex + 1], absoluteError);
            ++argumentIndex;
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

        if (argument == "--ruleset")
        {
            if (!config.startupRuleset.empty() || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --ruleset <id>[:<option>...], such as maw:hell:horizontal\n";
                return false;
            }

            config.startupRuleset = argv[argumentIndex + 1];
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

std::filesystem::path executableDirectory()
{
    const char *pBasePath = SDL_GetBasePath();
    std::error_code error;
    return pBasePath != nullptr ? OpenYAMM::Engine::programDirectory(pBasePath) : std::filesystem::current_path(error);
}

// Makes the user data folder the working directory: a release installation keeps saves, settings.ini and screenshots
// in its own folder. Android's entry point chooses the folder before the game starts.
bool enterUserDataDirectory(
    const std::optional<std::filesystem::path> &userDataRoot,
    const std::filesystem::path &installRoot)
{
#if defined(__ANDROID__)
    if (!userDataRoot)
    {
        return true;
    }
#endif

    std::error_code error;
    const std::filesystem::path root =
        OpenYAMM::Engine::resolveUserDataRoot(userDataRoot, installRoot, std::filesystem::current_path(error));

    std::filesystem::create_directories(root, error);

    if (error)
    {
        std::cerr << "Failed to create the user data folder " << root.string() << ": " << error.message() << '\n';
        return false;
    }

    std::filesystem::current_path(root, error);

    if (error)
    {
        std::cerr << "Failed to enter the user data folder " << root.string() << ": " << error.message() << '\n';
        return false;
    }

    std::cout << "User data folder: " << root.string() << '\n';
    return true;
}

void applySettingsConfigOverridesIfConfigured(
    OpenYAMM::Engine::ApplicationConfig &config,
    bool worldArgumentProvided,
    bool assetScaleArgumentProvided,
    bool assetRootArgumentProvided)
{
    const std::filesystem::path settingsPath = "settings.ini";
    // Without a file, the defaults apply; release packages ship none.
    std::optional<OpenYAMM::Game::GameSettings> settings = OpenYAMM::Game::GameSettings::createDefault();

    if (std::filesystem::exists(settingsPath))
    {
        std::string error;
        settings = OpenYAMM::Game::loadGameSettings(settingsPath, error);

        if (!settings)
        {
            std::cerr << "Failed to read settings from " << settingsPath.string() << ": " << error << '\n';
            return;
        }
    }

    // GameApplication migrates and saves the file; here the migration only drops the asset roots that older release
    // packages wrote, before they are used.
    OpenYAMM::Game::migrateGameSettings(*settings);

    if (!worldArgumentProvided && !settings->startWorldId.empty())
    {
        config.activeWorldId = settings->startWorldId;
    }

    if (!assetRootArgumentProvided && !settings->assetRoot.empty())
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
    config.installedContent.acceptModifiedPacks = settings->keepModifiedPacks;
    config.installedContent.languageId = settings->language;
}

// settings.ini in the user data folder (the working directory by then), or the defaults.
OpenYAMM::Game::GameSettings savedSettings()
{
    std::string error;
    const std::optional<OpenYAMM::Game::GameSettings> settings = std::filesystem::exists("settings.ini")
        ? OpenYAMM::Game::loadGameSettings("settings.ini", error)
        : std::nullopt;
    return settings ? *settings : OpenYAMM::Game::GameSettings::createDefault();
}

std::string updateChannelUrl()
{
    return savedSettings().updateUrl;
}

int runGame(int argc, char **argv, OpenYAMM::Engine::LogFile &logFile)
{
    setGameplayProfilingEnabled(false);
    av_log_set_level(AV_LOG_ERROR);

    OpenYAMM::Engine::ApplicationConfig config = OpenYAMM::Engine::ApplicationConfig::createDefault();
    std::vector<std::string> arguments;
    bool worldArgumentProvided = false;
    bool assetScaleArgumentProvided = false;
    bool assetRootArgumentProvided = false;
    std::optional<std::filesystem::path> userDataRoot;

    if (!parseCommonArguments(
            argc,
            argv,
            config,
            arguments,
            worldArgumentProvided,
            assetScaleArgumentProvided,
            assetRootArgumentProvided,
            userDataRoot))
    {
        return 2;
    }

    for (const std::string &argument : arguments)
    {
        if (argument == "--help" || argument == "-h")
        {
            printUsage(std::cout, argv[0]);
            return 0;
        }
    }

    // Anything left that is not a headless command is a mistake; the game does not start with it.
    if (!arguments.empty() && arguments[0].rfind("--headless-", 0) != 0)
    {
        std::cerr << "Unknown argument: " << arguments[0] << '\n';
        printUsage(std::cerr, argv[0]);
        return 2;
    }

    const std::filesystem::path executableFolder = executableDirectory();
    const std::filesystem::path installRoot = OpenYAMM::Engine::installationRoot(executableFolder);

    if (assetRootArgumentProvided)
    {
        // Relative to the folder the game was started from, not the user data folder entered below.
        std::error_code error;
        config.assetRoot = std::filesystem::absolute(config.assetRoot, error).string();
    }
#if !defined(__ANDROID__)
    else if (OpenYAMM::Engine::isReleaseInstallation(installRoot))
    {
        config.assetRoot = OpenYAMM::Engine::installedAssetRoot(executableFolder).string();
    }
#endif

    if (!enterUserDataDirectory(userDataRoot, installRoot))
    {
        return 2;
    }

#if !defined(__ANDROID__)
    // Mounted only over a release's packs (packaging/MODDING.md).
    std::error_code currentPathError;
    config.installedContent.modsRoot = std::filesystem::current_path(currentPathError) / "mods";
    // The player's own language packs (devdocs/LOCALIZATION.md), on every asset root.
    config.installedContent.userLanguagesRoot = std::filesystem::current_path(currentPathError) / "languages";
#endif

    const bool headlessCommand = !arguments.empty() && arguments[0].rfind("--headless-", 0) == 0;

    // Headless commands are development tools that report on the console, and parallel runs would share one file.
    if (headlessCommand)
    {
        logFile.discard();
    }
    else if (!logFile.open(LogFileName))
    {
        std::cerr << "Failed to create the log file " << LogFileName << '\n';
    }

    applySettingsConfigOverridesIfConfigured(
        config,
        worldArgumentProvided,
        assetScaleArgumentProvided,
        assetRootArgumentProvided);

    if (headlessCommand)
    {
        config.saveSettings = false;
        setEnvironmentVariable("OPENYAMM_DISABLE_LOADING_OVERLAY", "1");
        // Monster path plans land in simulated time (ActorPathRuntime::setWorkerCount).
        setEnvironmentVariable("OPENYAMM_SYNCHRONOUS_PATH_PLANS", "1");
    }

    if (arguments.size() >= 2 && arguments[0] == "--headless-validate-scenario")
    {
        return OpenYAMM::Game::runScenarioHeadlessCommand(argv[0], config, arguments, true);
    }

    if (arguments.size() >= 2 && arguments[0] == "--headless-run-scenario")
    {
        const int result = OpenYAMM::Game::runScenarioHeadlessCommand(argv[0], config, arguments, false);

        // A version that plays scenarios works: the release checks run new versions this way.
        if (result == 0)
        {
            if (std::unique_ptr<OpenYAMM::Game::GameUpdater> updater =
                    OpenYAMM::Game::GameUpdater::create(updateChannelUrl()))
            {
                updater->markHealthy(std::cout);
            }
        }

        return result;
    }

    if ((arguments.size() == 1 || arguments.size() == 2) && arguments[0] == "--headless-update")
    {
        return OpenYAMM::Game::runHeadlessUpdate(arguments.size() == 2 ? arguments[1] : updateChannelUrl(),
                                                 savedSettings().keepModifiedPacks, std::cout);
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

    if ((arguments.size() == 1 || (arguments.size() == 2 && arguments[1] == "--all-worlds"))
        && arguments[0] == "--headless-validate-actor-models")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runValidateActorModels(argv[0], arguments.size() == 2);
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

    if (arguments.size() == 4 && arguments[0] == "--headless-check-indoor-reachability")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runCheckIndoorReachability(argv[0], arguments[1], arguments[2], arguments[3]);
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-export-decoration-models")
    {
        OpenYAMM::Game::HeadlessGameplayDiagnostics diagnostics(config);
        return diagnostics.runExportDecorationModels(argv[0], arguments[1], arguments[2]);
    }

    if (arguments.size() == 3 && arguments[0] == "--headless-export-indoor-bake-scene")
    {
        return OpenYAMM::Game::exportIndoorBakeScene(config, argv[0], arguments[1], arguments[2]);
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

    // A headless command none of the above takes (unknown, or the wrong number of arguments).
    if (!arguments.empty())
    {
        std::cerr << "Unknown headless command or wrong arguments: " << arguments[0] << '\n';
        printUsage(std::cerr, argv[0]);
        return 2;
    }

#if !defined(__ANDROID__)
    // The downloaded macOS app installs its whole release into the per-user folder and never plays itself.
    bool installRelease = false;
#if defined(__APPLE__)
    installRelease = OpenYAMM::Game::applePackageInstallation().has_value();
#endif
    const bool releaseContent = !assetRootArgumentProvided && OpenYAMM::Engine::isReleaseInstallation(installRoot);

    if (!assetRootArgumentProvided && installRelease)
    {
        OpenYAMM::Game::runContentSetup(updateChannelUrl(), config.assetRoot);
        return 0;
    }

    // Packs the player changed on purpose are neither checked nor restored, and no update replaces them.
    if (releaseContent && config.installedContent.acceptModifiedPacks)
    {
        std::cout << "Content: keep_modified_packs is on; the game neither checks, restores nor updates its packs\n";

        if (!OpenYAMM::Game::modifiedContentComplete(config.assetRoot))
        {
            return 1;
        }
    }
    // A fresh installation from the small download package carries no content yet.
    else if (releaseContent && OpenYAMM::Game::installedContentMissing(config.assetRoot))
    {
        if (OpenYAMM::Game::runContentSetup(updateChannelUrl(), config.assetRoot, config.installedContent.languageId)
            != OpenYAMM::Game::ContentSetupResult::Ready)
        {
            return 0;
        }
    }
    // The language chosen in Settings has voices, sounds or videos not downloaded yet (devdocs/LOCALIZATION.md):
    // the same window downloads them; if the player closes it, the game plays in English this time.
    else if (releaseContent
             && OpenYAMM::Game::languageContentMissing(config.assetRoot, config.installedContent.languageId))
    {
        const OpenYAMM::Game::ContentSetupResult result =
            OpenYAMM::Game::runContentSetup(updateChannelUrl(), config.assetRoot, config.installedContent.languageId);

        if (result == OpenYAMM::Game::ContentSetupResult::Restarted)
        {
            return 0;
        }
    }
#endif

    OpenYAMM::Game::GameApplication application(config);
    return application.run();
}
}

int runApplication(int argc, char **argv)
{
    // Lives across the whole run, so a fatal error below still reaches the file.
    OpenYAMM::Engine::LogFile logFile;

    try
    {
        return runGame(argc, argv, logFile);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
}

#ifndef OPENYAMM_NO_DESKTOP_MAIN
int main(int argc, char **argv)
{
    return OpenYAMM::Game::runApplication(argc, argv);
}
#endif
