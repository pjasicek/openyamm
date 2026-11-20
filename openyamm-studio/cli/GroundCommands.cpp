#include "cli/GroundCommands.h"

#include "cli/Commands.h"
#include "core/CanonicalYaml.h"
#include "core/GroundTerrain.h"
#include "core/Schema.h"

#include "game/indoor/IndoorMapData.h"

#include <yaml-cpp/yaml.h>

#include <iostream>
#include <sstream>

namespace OpenYAMM::Studio
{
// oymap ground <map.blv> --ground <ground.yml> --world <world> --assets <root> --out <folder> [--stem <stem>]
//     [--world-materials <world.yml>] [--exclude <faces file>]
// The ground block's weights and material file over the map's faces, and the scene's terrain block (terrain.yml).
// --world-materials: a world material file in place of the root's worlds/<world>/terrain_materials/world.yml;
// --exclude: face indices (whitespace or commas) drawn as faces, in place of the covered rule.
int runGround(const std::vector<std::string> &arguments)
{
    std::vector<std::string> rest = arguments;
    std::string groundPath;
    std::string world;
    std::string output;
    std::string stem;
    std::string worldMaterials;
    std::string excludePath;
    const std::filesystem::path assetRoot = takeAssetRoot(rest);
    takeOption(rest, "--ground", groundPath);
    takeOption(rest, "--world", world);
    takeOption(rest, "--out", output);
    takeOption(rest, "--stem", stem);
    takeOption(rest, "--world-materials", worldMaterials);
    takeOption(rest, "--exclude", excludePath);

    if (rest.size() != 1 || groundPath.empty() || world.empty() || output.empty() || assetRoot.empty())
    {
        std::cerr << "usage: oymap ground <map.blv> --ground <ground.yml> --world <world> --assets <root> --out "
                     "<folder> [--stem <stem>] [--world-materials <world.yml>] [--exclude <faces file>]\n";
        return 2;
    }

    const std::filesystem::path mapPath = rest.front();
    std::string bytes;

    if (!readTextFile(mapPath, bytes))
    {
        std::cerr << "oymap ground: cannot read " << mapPath.string() << "\n";
        return 1;
    }

    const std::optional<Game::IndoorMapData> map =
        Game::IndoorMapDataLoader().loadFromBytes(std::vector<uint8_t>(bytes.begin(), bytes.end()));

    if (!map)
    {
        std::cerr << "oymap ground: " << mapPath.string() << " is not a BLV the game reads\n";
        return 1;
    }

    std::string groundText;
    YAML::Node ground;

    try
    {
        if (!readTextFile(groundPath, groundText))
        {
            std::cerr << "oymap ground: cannot read " << groundPath << "\n";
            return 1;
        }

        ground = YAML::Load(groundText);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "oymap ground: " << groundPath << ": " << exception.what() << "\n";
        return 1;
    }

    const std::vector<SchemaIssue> schemaIssues =
        SchemaSet::builtIn().validateAt(ground, "atmosphere.schema.json#/properties/ground");

    for (const SchemaIssue &issue : schemaIssues)
    {
        std::cerr << groundPath << ": " << issue.path << ": " << issue.message << "\n";
    }

    if (!schemaIssues.empty())
    {
        return 1;
    }

    GroundAssets assets = readGroundAssets(assetRoot, world);

    if (!worldMaterials.empty() && !readTextFile(worldMaterials, assets.worldMaterialsText))
    {
        std::cerr << "oymap ground: cannot read " << worldMaterials << "\n";
        return 1;
    }

    GroundOptions options;
    options.writtenBy = "oymap ground";

    if (!excludePath.empty())
    {
        std::string text;

        if (!readTextFile(excludePath, text))
        {
            std::cerr << "oymap ground: cannot read " << excludePath << "\n";
            return 1;
        }

        for (char &letter : text)
        {
            letter = letter == ',' ? ' ' : letter;
        }

        std::istringstream stream(text);
        std::vector<uint32_t> faces;
        uint32_t face = 0;

        while (stream >> face)
        {
            faces.push_back(face);
        }

        options.excludedFaces = faces;
    }

    if (stem.empty())
    {
        stem = mapPath.stem().string();
    }

    GroundTerrain terrain;
    std::string errorMessage;

    if (!buildGroundTerrain(ground, *map, assets, stem, options, terrain, errorMessage))
    {
        std::cerr << "oymap ground: " << errorMessage << "\n";
        return 1;
    }

    const std::filesystem::path folder = output;
    std::filesystem::create_directories(folder);

    if (!writeTextFileAtomically(folder / terrain.materialsFile, terrain.materialsText, errorMessage)
        || !writeBinaryFileAtomically(folder / terrain.weightsFile, terrain.weightsPng, errorMessage)
        || !writeTextFileAtomically(folder / "terrain.yml", writeCanonicalYaml(terrain.sceneTerrain), errorMessage))
    {
        std::cerr << "oymap ground: " << errorMessage << "\n";
        return 1;
    }

    for (const std::string &warning : terrain.warnings)
    {
        std::cout << "warning: " << warning << "\n";
    }

    std::cout << "ground: " << terrain.groundFaces << " faces weighed, " << terrain.excludedFaces.size()
              << " drawn as faces; layers";

    for (const std::string &layer : terrain.layers)
    {
        std::cout << " " << layer;
    }

    std::cout << " (" << terrain.weightedLayers << " weighted); " << terrain.weightsPng.size() << " bytes of weights\n";
    return 0;
}
}
