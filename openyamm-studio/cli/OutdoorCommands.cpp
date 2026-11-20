#include "cli/OutdoorCommands.h"

#include "core/EventFlow.h"
#include "core/Json.h"
#include "core/OutdoorCompare.h"
#include "core/Project.h"

#include <cmath>
#include <iostream>

namespace OpenYAMM::Studio
{
namespace
{
OutdoorCompareSide sideOf(const AssetSession &session, const LoadedMap &map)
{
    OutdoorCompareSide side;
    side.name = map.fileName;
    side.pMap = &*map.outdoor;
    const std::optional<std::vector<Game::TerrainTileDescriptor>> tiles =
        Game::loadTerrainTileDescriptors(session.files(), *map.outdoor);

    if (tiles)
    {
        side.tiles = *tiles;
    }

    std::string flowJson;
    std::string errorMessage;

    if (map.events && exploreEventHandlers(map, flowJson, errorMessage))
    {
        side.eventTargets = outdoorEventTargets(flowJson);
        side.emptyEvents = outdoorEmptyEvents(flowJson);
        side.handledEvents = outdoorFlowEvents(flowJson);
        side.eventsRead = true;

        // The names the script gives events, also those without a handler (the program lists only events with
        // one, so every number is asked).
        for (uint32_t event = 1; event <= 0xffff; ++event)
        {
            const std::optional<std::string> name = map.events->getHint(static_cast<uint16_t>(event));

            if (name && !name->empty())
            {
                side.namedEvents.insert(static_cast<int>(event));
            }
        }
    }

    return side;
}
}

bool compareLoadedOutdoorMaps(
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const LoadedMap &original,
    const LoadedMap &rebuilt,
    OutdoorCompareResult &result,
    std::string &errorMessage,
    std::string &warning,
    bool rimByNodes)
{
    OutdoorCompareOptions options;
    options.rimBySkyline = !rimByNodes;
    // The tile tables belong to the engine, so one session of the world reads them for both maps.
    AssetSession session;

    if (!session.open(assetRoot, world, errorMessage))
    {
        return false;
    }

    const OutdoorCompareSide first = sideOf(session, original);
    const OutdoorCompareSide second = sideOf(session, rebuilt);

    if (first.tiles.empty() || second.tiles.empty())
    {
        warning = "the tile table of " + world + " could not be read; ground, water and roads are not compared";
    }

    return compareOutdoorMaps(first, second, result, errorMessage, options);
}

int runOutdoorCompare(
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const LoadedMap &original,
    const LoadedMap &rebuilt,
    const std::string &output,
    bool asJson,
    bool rimByNodes)
{
    std::string errorMessage;
    std::string warning;
    OutdoorCompareResult result;

    if (!compareLoadedOutdoorMaps(assetRoot, world, original, rebuilt, result, errorMessage, warning, rimByNodes))
    {
        if (!warning.empty())
        {
            std::cerr << "oymap compare: " << warning << "\n";
        }

        std::cerr << "oymap compare: " << errorMessage << "\n";
        return 1;
    }

    if (!warning.empty())
    {
        std::cerr << "oymap compare: " << warning << "\n";
    }

    JsonWriter writer(true);
    writeOutdoorCompareJson(result, writer);
    std::string report = writer.take();
    report.push_back('\n');

    if (!output.empty())
    {
        const std::filesystem::path folder = output;
        std::error_code error;
        std::filesystem::create_directories(folder, error);
        JsonWriter differencesWriter(true);
        writeOutdoorDifferencesJson(result, differencesWriter);
        std::string differences = differencesWriter.take();
        differences.push_back('\n');

        if (!writeTextFileAtomically(folder / "report.json", report, errorMessage)
            || !writeTextFileAtomically(folder / "differences.json", differences, errorMessage)
            || !writeTextFileAtomically(folder / "shots.yml", outdoorCompareShotsYaml(result), errorMessage))
        {
            std::cerr << "oymap compare: " << errorMessage << "\n";
            return 1;
        }

        for (const std::pair<std::string, Image> &picture : outdoorComparePictures(result))
        {
            if (!writeBinaryFileAtomically(folder / picture.first, encodePng(picture.second), errorMessage))
            {
                std::cerr << "oymap compare: " << errorMessage << "\n";
                return 1;
            }
        }
    }

    if (asJson || output.empty())
    {
        std::cout << report;
        return 0;
    }

    const auto percent = [](double share)
    {
        return formatNumber(std::round(share * 1000.0) / 10.0);
    };
    std::cout << "compared " << result.originalName << " with " << result.rebuiltName << ": score "
              << percent(result.score) << " %\n";

    for (const OutdoorComparePart &part : result.parts)
    {
        std::cout << "  " << part.id << " " << percent(part.score) << " % (" << percent(part.weight)
                  << " % of the score): " << part.detail << "\n";
    }

    std::cout << "worst regions (16 x 16 cells, A1 the north-west):\n";

    for (size_t index = 0; index < result.worstRegions.size() && index < 6; ++index)
    {
        const OutdoorCompareRegion &region = result.regions[result.worstRegions[index]];
        std::cout << "  " << region.name << " " << percent(region.score) << " %: " << region.sentence << "\n";
    }

    std::cout << "wrote report.json, differences.json, heights.png, ground.png, objects.png, regions.png and "
                 "shots.yml in " << output << "\n";
    return 0;
}
}
