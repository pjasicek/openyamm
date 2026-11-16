#include "core/OutdoorBuild.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <map>
#include <sstream>

// How an outdoor map leads to its neighbours, as the game reads it (game/tables/MapStats.cpp): a row of
// engine/data_tables/outdoor_travels.txt for the map names, for each of its four sides (Up north, Down south,
// Left west, Right east), the map that lies there, the side of that map the party enters and the days the way takes.
// The arrival word is MMerge's: "up" enters by the north start and "down" by the south start, but "left" enters by the
// east start and "right" by the west start (parseMergedOutdoorTravelSide): a party that leaves west by the Left column
// arrives "left", on the other map's east side (S8g: the studio wrote "left" for a west arrival before). A map with a row has the game's fixed square to walk (23143 units from the
// middle on every side: 45.2 cells), and a party that walks past it is asked to travel. It arrives at the other
// map's decoration named "<side> start" (north start, south start, east start, west start), or at its party start.
//
// So a project's edge neighbours (project.yml `neighbours` with `kind: edge` and a `side`) become its row, and each
// neighbour's own row is pointed back at the project's map, unless the neighbour says `one_way: true`: a new map
// that lies north of a shipped one must be what that one's north side leads to.

namespace OpenYAMM::Studio
{
namespace
{
constexpr size_t ColumnKeyMap = 0;
constexpr size_t ColumnStraightTravel = 13;
constexpr size_t ColumnNotes = 14;
constexpr size_t ColumnCount = 19;



std::string lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

std::vector<std::string> splitTabs(const std::string &line)
{
    std::vector<std::string> columns;
    size_t begin = 0;

    while (true)
    {
        const size_t tab = line.find('\t', begin);
        columns.push_back(line.substr(begin, tab == std::string::npos ? tab : tab - begin));

        if (tab == std::string::npos)
        {
            break;
        }

        begin = tab + 1;
    }

    return columns;
}

// The first of a side's three columns (map, side, days), and the table's word for arriving on the side.
struct Side
{
    const char *pName;
    size_t column;
    const char *pArrivalWord;
    const char *pOpposite;
};

constexpr Side Sides[] = {
    {"north", 1, "up", "south"},
    {"south", 4, "down", "north"},
    {"west", 7, "right", "east"},
    {"east", 10, "left", "west"},
};

const Side *sideOf(const std::string &name)
{
    for (const Side &side : Sides)
    {
        if (name == side.pName)
        {
            return &side;
        }
    }

    return nullptr;
}
}

std::vector<OutdoorTravelEdge> outdoorTravelEdges(const Project &project)
{
    std::vector<OutdoorTravelEdge> edges;

    if (textOf(project.document("project.yml"), "kind") != "outdoor" || project.has("rooms.yml"))
    {
        return edges;
    }

    const YAML::Node neighbours = childOf(project.document("project.yml"), "neighbours");

    for (size_t index = 0; neighbours.IsDefined() && neighbours.IsSequence() && index < neighbours.size(); ++index)
    {
        const YAML::Node neighbour = neighbours[index];
        const Side *pSide = sideOf(textOf(neighbour, "side"));

        if (textOf(neighbour, "kind") != "edge" || pSide == nullptr || textOf(neighbour, "to").empty())
        {
            continue;
        }

        OutdoorTravelEdge edge;
        edge.id = textOf(neighbour, "id");
        edge.side = pSide->pName;
        edge.map = lower(textOf(neighbour, "to"));

        if (edge.map.find('.') == std::string::npos)
        {
            edge.map += ".odm";
        }

        const std::string arrival = textOf(neighbour, "arrival_side", pSide->pOpposite);
        edge.arrivalSide = sideOf(arrival) != nullptr ? arrival : std::string(pSide->pOpposite);
        edge.days = childOf(neighbour, "days").IsDefined() ? neighbour["days"].as<int>(0) : 0;
        edge.oneWay = textOf(neighbour, "one_way") == "true" || textOf(neighbour, "listed_only") == "true";
        edges.push_back(edge);
    }

    return edges;
}

bool upsertOutdoorTravelRows(
    const Project &project,
    const std::filesystem::path &tablePath,
    std::vector<std::string> &changes,
    std::string &errorMessage)
{
    const YAML::Node card = project.document("project.yml");
    const std::vector<OutdoorTravelEdge> edges = outdoorTravelEdges(project);

    if (textOf(card, "kind") != "outdoor" || edges.empty())
    {
        return true;
    }

    std::string text;

    if (!readTextFile(tablePath, text))
    {
        errorMessage = "could not read " + tablePath.string();
        return false;
    }

    const std::string lineEnding = text.find("\r\n") != std::string::npos ? "\r\n" : "\n";
    std::vector<std::vector<std::string>> rows;
    size_t begin = 0;

    while (begin < text.size())
    {
        const size_t end = text.find('\n', begin);
        std::string line = text.substr(begin, end == std::string::npos ? end : end - begin);

        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        rows.push_back(splitTabs(line));

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    const std::string mapFile = lower(textOf(card, "id")) + ".odm";
    const auto rowOf = [&rows](const std::string &file) -> std::vector<std::string> *
    {
        for (std::vector<std::string> &row : rows)
        {
            if (!row.empty() && lower(row[ColumnKeyMap]) == file)
            {
                return &row;
            }
        }

        return nullptr;
    };

    if (rowOf(mapFile) == nullptr)
    {
        std::vector<std::string> row(ColumnCount);
        row[ColumnKeyMap] = mapFile;
        rows.push_back(row);
    }

    std::vector<std::string> &own = *rowOf(mapFile);
    own.resize(std::max(own.size(), ColumnCount));
    own[ColumnNotes] = textOf(card, "name", textOf(card, "id"));
    own[ColumnStraightTravel].clear();

    for (const Side &side : Sides)
    {
        own[side.column].clear();
        own[side.column + 1].clear();
        own[side.column + 2].clear();
    }

    for (const OutdoorTravelEdge &edge : edges)
    {
        const Side &side = *sideOf(edge.side);
        const Side &arrival = *sideOf(edge.arrivalSide);
        own[side.column] = edge.map;
        own[side.column + 1] = arrival.pArrivalWord;
        own[side.column + 2] = std::to_string(edge.days);
        changes.push_back(mapFile + " " + edge.side + ": to " + edge.map + " (its " + edge.arrivalSide + " side, "
            + std::to_string(edge.days) + " days)");
    }

    // The way back: the neighbour's side that looks at this map leads to it, to the side the party left by.
    for (const OutdoorTravelEdge &edge : edges)
    {
        std::vector<std::string> *pRow = rowOf(edge.map);

        if (edge.oneWay || pRow == nullptr)
        {
            continue;
        }

        pRow->resize(std::max(pRow->size(), ColumnCount));
        // Batch O-H: the way back is the neighbour's side that leads to this map already, or to the original it
        // rebuilds (`reference`), when one does: the side the party arrives on is not always the one that leads
        // back (Erathia's east edge arrives on Harmondale's right; Harmondale's way to Erathia is its west edge).
        const Side *pTheirs = sideOf(edge.arrivalSide);
        const std::string reference = lower(textOf(childOf(card, "map_stats"), "reference"));

        for (const Side &side : Sides)
        {
            const std::string leadsTo = lower((*pRow)[side.column]);

            if (!leadsTo.empty() && (leadsTo == mapFile || (!reference.empty() && leadsTo == reference)))
            {
                pTheirs = &side;
                break;
            }
        }

        const Side &theirs = *pTheirs;
        const Side &ours = *sideOf(edge.side);
        (*pRow)[theirs.column] = mapFile;
        (*pRow)[theirs.column + 1] = ours.pArrivalWord;
        (*pRow)[theirs.column + 2] = std::to_string(edge.days);
        changes.push_back(edge.map + " " + theirs.pName + ": to " + mapFile + " (its " + edge.side + " side, "
            + std::to_string(edge.days) + " days)");
    }

    std::string written;

    for (const std::vector<std::string> &row : rows)
    {
        for (size_t column = 0; column < row.size(); ++column)
        {
            written += column == 0 ? "" : "\t";
            written += row[column];
        }

        written += lineEnding;
    }

    return writeTextFileAtomically(tablePath, written, errorMessage);
}

// The sky, the colours and the weather of an outdoor map, as the game reads them (game/data/GameDataLoader.cpp,
// applyMergedContinentSettingsToSelectedMap): engine/data_tables/bolster_maps.txt has a row for every map, keyed by
// the map's number in map_stats.txt. Its `Continent` column names a row of continent_settings.txt, which gives the
// map its skies from clear to storm (Jadame: plansky3, plansky1, sky06 ...; the paintings the sky's and the fog's
// colours are taken from), its colour grading and its journal's continent; `Weather`, `Rain` and `Snow` say whether
// rain and snow fall by the world's chances (engine/rendering/weather/weather.yml); `Custom sky` fixes one sky for
// every weather; `Bolster kind`, `Spells` and `Summons` say how the map's monsters are strengthened. A map without
// a row has no continent: the game then draws its fallback sky (a grey-blue haze where Ravenshore's is lavender
// and Harmondale's clear) and no rain or snow ever falls.
//
// So `oymap install` writes the row of an outdoor project's map: the row of the reference map (project.yml
// map_stats.reference) under the project's own number, else a plain row on the world's own continent without
// strengthened monsters; then what the project says itself: map_stats.continent, atmosphere.yml `weather` and `sky`.
namespace
{
constexpr size_t BolsterColumnId = 0;
constexpr size_t BolsterColumnNote = 1;
constexpr size_t BolsterColumnContinent = 2;
constexpr size_t BolsterColumnKind = 3;
constexpr size_t BolsterColumnSpells = 4;
constexpr size_t BolsterColumnSummons = 5;
constexpr size_t BolsterColumnWeather = 6;
constexpr size_t BolsterColumnExtra = 7;
constexpr size_t BolsterColumnCustomSky = 9;
constexpr size_t BolsterColumnRain = 10;
constexpr size_t BolsterColumnSnow = 11;
constexpr size_t BolsterColumnCount = 12;
constexpr size_t MapStatsColumnFile = 2;

// The continent of a world's own maps: its row of continent_settings.txt.
int continentOfWorld(const std::string &world)
{
    static const std::pair<const char *, int> Continents[] = {{"mm8", 1}, {"mm7", 2}, {"mm6", 3}, {"mm9", 5}};

    for (const std::pair<const char *, int> &entry : Continents)
    {
        if (world == entry.first)
        {
            return entry.second;
        }
    }

    return 0;
}

std::vector<std::vector<std::string>> tableRowsOf(const std::string &text)
{
    std::vector<std::vector<std::string>> rows;
    size_t begin = 0;

    while (begin < text.size())
    {
        const size_t end = text.find('\n', begin);
        std::string line = text.substr(begin, end == std::string::npos ? end : end - begin);

        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        rows.push_back(splitTabs(line));

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    return rows;
}
}

// map_stats.bolster in the table's words: the game's kinds (game/gameplay/GameplayBolsterRuntime.cpp: "0" none,
// OriginalStats, AllToEqual, and LowerToEqual, the shipped maps' kind); empty for a word that is none of them (the
// schema refuses it).
std::string bolsterWord(const std::string &word)
{
    const std::string lowered = lower(word);

    for (const char *pKind : {"LowerToEqual", "AllToEqual", "OriginalStats"})
    {
        if (lowered == lower(pKind))
        {
            return pKind;
        }
    }

    return lowered == "none" ? "0" : std::string();
}

OutdoorWeatherRow outdoorWeatherRow(const Project &project)
{
    OutdoorWeatherRow row;
    const YAML::Node card = project.document("project.yml");
    const YAML::Node stats = childOf(card, "map_stats");
    const bool outdoor = textOf(card, "kind") == "outdoor" && !project.has("rooms.yml");
    // An indoor map gets a row when it asks for a bolster kind (S8g); an outdoor map always.
    const bool indoorWithBolster = textOf(card, "kind") == "indoor" && !textOf(stats, "bolster").empty();

    if ((!outdoor && !indoorWithBolster) || childOf(card, "base").IsDefined() || !childOf(stats, "id").IsDefined())
    {
        return row;
    }

    row.written = true;
    row.id = textOf(stats, "id");
    row.note = textOf(card, "name", textOf(card, "id"));
    row.reference = lower(textOf(stats, "reference"));
    row.bolster = bolsterWord(textOf(stats, "bolster"));
    row.continent = childOf(stats, "continent").IsDefined() ? stats["continent"].as<int>(0)
        : continentOfWorld(textOf(card, "world"));
    row.continentGiven = childOf(stats, "continent").IsDefined();

    if (!outdoor)
    {
        return row;
    }

    const YAML::Node atmosphere = project.has("atmosphere.yml") ? project.document("atmosphere.yml")
        : YAML::Node(YAML::NodeType::Undefined);
    const YAML::Node weather = childOf(atmosphere, "weather");

    if (weather.IsDefined() && weather.IsMap())
    {
        row.weatherGiven = true;
        row.rain = textOf(weather, "rain") == "true";
        row.snow = textOf(weather, "snow") == "true";
    }

    row.sky = textOf(atmosphere, "sky");
    return row;
}

bool upsertOutdoorWeatherRow(
    const Project &project,
    const std::filesystem::path &tablesDirectory,
    std::vector<std::string> &changes,
    std::string &errorMessage)
{
    const OutdoorWeatherRow plan = outdoorWeatherRow(project);

    if (!plan.written)
    {
        return true;
    }

    const std::filesystem::path tablePath = tablesDirectory / "bolster_maps.txt";
    std::string text;
    std::string statsText;

    if (!readTextFile(tablePath, text) || !readTextFile(tablesDirectory / "map_stats.txt", statsText))
    {
        errorMessage = "could not read " + tablePath.string() + " and map_stats.txt beside it";
        return false;
    }

    const std::string lineEnding = text.find("\r\n") != std::string::npos ? "\r\n" : "\n";
    std::vector<std::vector<std::string>> rows = tableRowsOf(text);
    // The reference map's number, by its file in map_stats.txt.
    std::string referenceId;

    for (const std::vector<std::string> &statsRow : tableRowsOf(statsText))
    {
        if (!plan.reference.empty() && statsRow.size() > MapStatsColumnFile
            && lower(statsRow[MapStatsColumnFile]) == plan.reference)
        {
            referenceId = statsRow[BolsterColumnId];
        }
    }

    std::vector<std::string> row;
    std::vector<std::string> *pExisting = nullptr;

    for (std::vector<std::string> &other : rows)
    {
        if (other.empty())
        {
            continue;
        }

        if (!referenceId.empty() && other[BolsterColumnId] == referenceId)
        {
            row = other;
        }

        if (other[BolsterColumnId] == plan.id)
        {
            pExisting = &other;
        }
    }

    const bool fromReference = !row.empty();

    if (!fromReference)
    {
        // A plain row: the world's continent, monsters as the tables have them, no weather.
        row.assign(BolsterColumnCount, "");
        row[BolsterColumnKind] = "0";
        row[BolsterColumnSpells] = "-";
        row[BolsterColumnSummons] = "-";
        row[BolsterColumnWeather] = "-";
        row[BolsterColumnExtra] = "0";
    }

    row.resize(std::max(row.size(), BolsterColumnCount));
    row[BolsterColumnId] = plan.id;
    row[BolsterColumnNote] = plan.note;

    // map_stats.bolster (S8g): the kind; a plain row that strengthens its monsters lets them take new spells, as the
    // shipped dungeons' rows do (MM7's Temple of Baa: LowerToEqual, spells, no summons).
    if (!plan.bolster.empty())
    {
        row[BolsterColumnKind] = plan.bolster;

        if (!fromReference)
        {
            row[BolsterColumnSpells] = plan.bolster == "0" ? "-" : "x";
        }
    }

    if (!fromReference || plan.continentGiven)
    {
        row[BolsterColumnContinent] = std::to_string(plan.continent);
    }

    if (plan.weatherGiven)
    {
        // Rain falls unless its cell says "-"; snow only where its cell is marked.
        row[BolsterColumnWeather] = plan.rain || plan.snow ? "x" : "-";
        row[BolsterColumnRain] = plan.rain ? "" : "-";
        row[BolsterColumnSnow] = plan.snow ? "x" : "";
    }

    if (!plan.sky.empty())
    {
        row[BolsterColumnCustomSky] = plan.sky;
    }

    // The table's rows end with their last cell that says something, and have ten cells at least.
    while (row.size() > 10 && row.back().empty())
    {
        row.pop_back();
    }

    const bool weatherOn = row.size() > BolsterColumnWeather && row[BolsterColumnWeather] == "x";
    const bool rainOn = weatherOn && !(row.size() > BolsterColumnRain && row[BolsterColumnRain] == "-");
    const bool snowOn = weatherOn && row.size() > BolsterColumnSnow && row[BolsterColumnSnow] == "x";
    changes.push_back("bolster_maps.txt row " + plan.id + " (" + plan.note + "): continent "
        + row[BolsterColumnContinent] + (fromReference ? ", as " + plan.reference : std::string(", a plain row"))
        + (plan.bolster.empty() ? std::string() : ", bolster " + row[BolsterColumnKind])
        + ", " + (rainOn ? "rain" : "no rain") + ", " + (snowOn ? "snow" : "no snow")
        + (row.size() > BolsterColumnCustomSky && !row[BolsterColumnCustomSky].empty()
            ? ", the sky " + row[BolsterColumnCustomSky] : std::string()));

    if (pExisting != nullptr)
    {
        *pExisting = row;
    }
    else
    {
        rows.push_back(row);
    }

    std::string written;

    for (const std::vector<std::string> &line : rows)
    {
        for (size_t column = 0; column < line.size(); ++column)
        {
            written += column == 0 ? "" : "\t";
            written += line[column];
        }

        written += lineEnding;
    }

    return writeTextFileAtomically(tablePath, written, errorMessage);
}

std::string outdoorSkyTheme(const Project &project)
{
    if (!project.has("atmosphere.yml"))
    {
        return {};
    }

    return lower(textOf(project.document("atmosphere.yml"), "sky_theme"));
}

// The game reads sky.yml's `maps` as file name to theme (game/render/SkyPresets.cpp); the file keeps its comments,
// so the row is written as a line of text.
std::string withSkyTheme(const std::string &text, const std::string &mapFile, const std::string &theme)
{
    std::istringstream lines(text);
    std::string line;
    std::string written;
    bool inside = false;
    bool placed = false;
    const std::string row = "  " + mapFile + ": " + theme;

    while (std::getline(lines, line))
    {
        const bool top = !line.empty() && line[0] != ' ' && line[0] != '#';

        if (top)
        {
            if (inside && !placed)
            {
                written += row + "\n";
                placed = true;
            }

            inside = line.rfind("maps:", 0) == 0;
        }

        if (inside && !top)
        {
            // An older row of the same map goes; the new one is written at the block's end.
            const size_t colon = line.find(':');

            if (line.rfind("  ", 0) == 0 && colon != std::string::npos
                && lower(line.substr(2, colon - 2)) == lower(mapFile))
            {
                continue;
            }
        }

        written += line + "\n";
    }

    if (!placed)
    {
        written += inside ? row + "\n" : "maps:\n" + row + "\n";
    }

    return written;
}

bool upsertOutdoorSkyTheme(
    const Project &project,
    const std::filesystem::path &skyFile,
    std::vector<std::string> &changes,
    std::string &errorMessage)
{
    const std::string theme = outdoorSkyTheme(project);

    if (theme.empty())
    {
        return true;
    }

    std::string text;

    if (!readTextFile(skyFile, text))
    {
        errorMessage = "could not read " + skyFile.string();
        return false;
    }

    const std::string mapFile = lower(project.document("project.yml")["id"].Scalar()) + ".odm";
    changes.push_back("sky.yml maps: " + mapFile + " " + theme);
    return writeTextFileAtomically(skyFile, withSkyTheme(text, mapFile, theme), errorMessage);
}
}
