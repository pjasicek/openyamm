#include "core/MapLoad.h"

#include "engine/AssetScaleTier.h"
#include "game/data/MapScriptSources.h"
#include "game/maps/SceneOverlayPaths.h"

#include <algorithm>

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerCopy(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}
}

namespace
{
std::filesystem::path &extraMount()
{
    static std::filesystem::path mountRoot;
    return mountRoot;
}
}

void AssetSession::setExtraMount(const std::filesystem::path &mountRoot)
{
    extraMount() = mountRoot;
}

bool AssetSession::open(const std::filesystem::path &assetRoot, const std::string &world, std::string &errorMessage)
{
    std::error_code error;

    if (!std::filesystem::is_directory(assetRoot / "worlds" / world, error))
    {
        errorMessage = assetRoot.string() + " has no world '" + world + "' (expected worlds/" + world + ")";
        return false;
    }

    // The development tree carries the desktop game's tier of face textures only (cooked x4); sizes are reported
    // in logical texels whatever the tier.
    Engine::AssetScaleProfile profile;
    profile.textures = Engine::AssetScaleTier::X4;

    Engine::InstalledContentOptions content;
    if (!extraMount().empty())
    {
        content.extraMountRoots.push_back(extraMount());
    }

    if (!m_files.initialize(assetRoot.parent_path(), assetRoot, Engine::AssetScaleTier::X1, profile, world, content))
    {
        errorMessage = "could not open the asset root " + assetRoot.string()
            + (extraMount().empty() ? std::string() : " with the mount " + extraMount().string());
        return false;
    }

    m_world = world;
    return true;
}

const Engine::AssetFileSystem &AssetSession::files() const
{
    return m_files;
}

const std::string &AssetSession::world() const
{
    return m_world;
}

std::string loadScriptSupport(const AssetSession &session)
{
    std::string supportPath;
    std::string worldCommonPath;
    const std::optional<std::string> support =
        Game::readFirstExistingText(session.files(), Game::buildLuaSupportPathCandidates(), supportPath);
    const std::optional<std::string> worldCommon = Game::readExistingTexts(
        session.files(), Game::buildLuaWorldCommonPathCandidates(session.files(), session.world()), worldCommonPath);
    return Game::prependLuaSupport(support, worldCommon, "");
}

bool loadMap(const AssetSession &session, const std::string &fileName, LoadedMap &map, std::string &errorMessage)
{
    map = {};
    map.world = session.world();
    map.fileName = lowerCopy(fileName);
    map.stem = Game::mapScriptBaseName(map.fileName);
    map.kind = mapKindFromPath(map.fileName);
    const Engine::AssetFileSystem &files = session.files();
    // "Data/games" is the engine's name for the mounted worlds' map folders, the active world's first.
    const std::optional<std::vector<uint8_t>> bytes = files.readBinaryFile("Data/games/" + map.fileName);

    if (!bytes)
    {
        errorMessage = "the world " + map.world + " has no map " + map.fileName;
        return false;
    }

    if (map.kind == MapKind::Indoor)
    {
        map.indoor = Game::IndoorMapDataLoader().loadFromBytes(*bytes);
    }
    else if (map.kind == MapKind::Outdoor)
    {
        map.outdoor = Game::OutdoorMapDataLoader().loadFromBytes(*bytes);
    }

    if (!map.indoor && !map.outdoor)
    {
        errorMessage = map.fileName + " is not a readable ODM or BLV map";
        return false;
    }

    // The scene and its overlays, in the game's order.
    const std::string sceneFileName = map.stem + ".scene.yml";
    map.scenePath = "Data/games/" + sceneFileName;
    const std::optional<std::string> sceneText = files.readTextFile(map.scenePath);

    if (!sceneText)
    {
        map.warnings.push_back("the map has no scene file (" + sceneFileName + ")");
    }
    else
    {
        std::vector<std::pair<std::string, std::string>> overlays;

        for (const std::string &overlayPath : Game::buildSceneOverlayPathCandidates(files, sceneFileName, ""))
        {
            const std::optional<std::string> overlayText = files.readTextFile(overlayPath);

            if (overlayText)
            {
                overlays.emplace_back(overlayPath, *overlayText);
                map.sceneOverlayPaths.push_back(overlayPath);
            }
        }

        std::string sceneError;
        Game::MapDeltaData state;

        if (map.indoor)
        {
            const Game::IndoorSceneYmlLoader loader;
            map.indoorScene = loader.loadFromText(*sceneText, sceneError);

            for (const std::pair<std::string, std::string> &overlay : overlays)
            {
                if (map.indoorScene && !loader.applyOverlayFromText(*map.indoorScene, overlay.second, sceneError))
                {
                    map.warnings.push_back("scene overlay " + overlay.first + " does not apply: " + sceneError);
                }
            }

            if (!map.indoorScene)
            {
                map.warnings.push_back("the scene file does not parse: " + sceneError);
            }
            else if (Game::buildIndoorMapStateFromScene(*map.indoorScene, *map.indoor, state, sceneError))
            {
                map.state = state;
            }
            else
            {
                map.warnings.push_back("the scene does not apply to the map: " + sceneError);
            }
        }
        else
        {
            const Game::OutdoorSceneYmlLoader loader;
            map.outdoorScene = loader.loadFromText(*sceneText, sceneError);

            for (const std::pair<std::string, std::string> &overlay : overlays)
            {
                if (map.outdoorScene && !loader.applyOverlayFromText(*map.outdoorScene, overlay.second, sceneError))
                {
                    map.warnings.push_back("scene overlay " + overlay.first + " does not apply: " + sceneError);
                }
            }

            if (!map.outdoorScene)
            {
                map.warnings.push_back("the scene file does not parse: " + sceneError);
            }
            else if (Game::buildOutdoorMapStateFromScene(*map.outdoorScene, *map.outdoor, state, sceneError))
            {
                map.state = state;
            }
            else
            {
                map.warnings.push_back("the scene does not apply to the map: " + sceneError);
            }
        }
    }

    // The map's own cinematics file, as written beside it (its overlays are not merged in).
    if (files.exists("Data/games/" + map.stem + ".cinematics.yml"))
    {
        map.cinematicsText = files.readTextFile("Data/games/" + map.stem + ".cinematics.yml");
    }

    // The event script: the map's own, its overlays appended, the support and world scripts in front.
    std::string scriptPath;
    const std::optional<std::string> script =
        Game::readFirstExistingText(files, Game::buildLuaScriptPathCandidates(map.stem, false), scriptPath);

    if (!script)
    {
        map.warnings.push_back("the map has no event script (events/maps/" + map.stem + ".lua)");
        return true;
    }

    std::string resolvedPath = scriptPath;
    map.scriptText = Game::appendLuaScriptOverlays(files, map.stem, "", *script, resolvedPath);
    map.scriptPaths.push_back(scriptPath);

    for (const std::string &overlayPath : Game::buildLuaScriptOverlayPathCandidates(files, map.stem, ""))
    {
        map.scriptPaths.push_back(overlayPath);
    }

    std::string supportPath;
    std::string worldCommonPath;
    const std::optional<std::string> support =
        Game::readFirstExistingText(files, Game::buildLuaSupportPathCandidates(), supportPath);
    // Every common script of the world that exists, joined, as the game does.
    const std::optional<std::string> worldCommon =
        Game::readExistingTexts(files, Game::buildLuaWorldCommonPathCandidates(files, map.world), worldCommonPath);
    const std::string source = Game::prependLuaSupport(support, worldCommon, map.scriptText);
    map.fullScriptSource = source;
    std::string scriptError;
    map.events = Game::ScriptedEventProgram::loadFromLuaText(
        source, "@" + resolvedPath, Game::ScriptedEventScope::Map, scriptError);

    if (!map.events)
    {
        map.warnings.push_back("the event script does not run: " + scriptError);
    }

    return true;
}
}
