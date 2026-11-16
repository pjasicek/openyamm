#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/NamedMods.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace
{
using namespace OpenYAMM::Game;

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_named_mods_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

std::string readTextFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}

// A manifest as `oymap mod pack` writes it.
std::string manifestText(const std::string &id, const std::string &extra = "")
{
    return "format: 1\nid: " + id + "\nname: \"Mod " + id + "\"\nversion: \"1.0\"\nauthor: Map Studio\n" + extra;
}

NamedModManifest manifest(
    const std::string &id,
    std::vector<uint32_t> mapNumbers = {},
    std::vector<ContentIdRangeDefinition> idRanges = {})
{
    NamedModManifest result;
    result.id = id;
    result.name = id;
    result.version = "1";
    result.mapNumbers = std::move(mapNumbers);
    result.idRanges = std::move(idRanges);
    return result;
}

NamedModCatalog catalogOf(const std::vector<NamedModManifest> &mods, const std::vector<std::string> &enabled)
{
    NamedModCatalog catalog;
    catalog.enabledIds = enabled;

    for (const NamedModManifest &mod : mods)
    {
        NamedModEntry entry;
        entry.id = mod.id;
        entry.manifest = mod;
        catalog.mods.push_back(entry);
    }

    return catalog;
}

using Rows = std::vector<std::vector<std::string>>;

// The shape of map_stats.txt: two title rows, a header row, data rows keyed by the first cell.
Rows mapStatsRows()
{
    return {
        {"", "Map Stats", ""},
        {"", "", "Reset"},
        {"#", "Name", "File name"},
        {"1", "Dagger Wound Island", "out01.odm"},
        {"2", "Ravenshore", "out02.odm"},
    };
}
}

TEST_CASE("named mods: a manifest as the Map Studio packs it parses")
{
    const std::string text = manifestText("s6_demo",
        "description: Two maps\n"
        "worlds: [mm6, mm9]\n"
        "maps:\n"
        "  - file: Studio06.blv\n    world: mm6\n    kind: new\n    project: studio06\n"
        "    source_revision: ed570eb6\n    files: [worlds/mm6/maps/studio06.blv]\n"
        "  - file: isleofashes.blv\n    world: mm9\n    kind: overlay\n"
        "tables:\n"
        "  - table: map_stats.txt\n    append: tables/map_stats.txt.append.txt\n"
        "map_numbers: [9306]\n"
        "idRanges:\n  maps: {begin: 9300, end: 9349}\n");
    std::string error;
    const std::optional<NamedModManifest> parsed = parseNamedModManifest(text, "s6_demo", error);
    REQUIRE_MESSAGE(parsed, error);
    CHECK(parsed->id == "s6_demo");
    CHECK(parsed->name == "Mod s6_demo");
    CHECK(parsed->version == "1.0");
    CHECK(parsed->author == "Map Studio");
    CHECK(parsed->worlds == std::vector<std::string>{"mm6", "mm9"});
    REQUIRE(parsed->maps.size() == 2);
    CHECK(parsed->maps[0].file == "studio06.blv");
    CHECK(parsed->maps[0].kind == "new");
    CHECK(parsed->maps[1].kind == "overlay");
    REQUIRE(parsed->tables.size() == 1);
    CHECK(parsed->tables[0].table == "map_stats.txt");
    CHECK(parsed->tables[0].appendPath == "tables/map_stats.txt.append.txt");
    CHECK(parsed->tables[0].overridePath.empty());
    CHECK(parsed->mapNumbers == std::vector<uint32_t>{9306});
    REQUIRE(parsed->idRanges.size() == 1);
    CHECK(parsed->idRanges[0].domain == "maps");
    CHECK(parsed->idRanges[0].begin == 9300);
    CHECK(parsed->idRanges[0].end == 9349);
}

TEST_CASE("named mods: invalid manifests are refused with a reason")
{
    std::string error;
    // The folder must be its id, and the id a plain name.
    CHECK_FALSE(parseNamedModManifest(manifestText("other"), "s6_demo", error));
    CHECK(error.find("folder") != std::string::npos);
    CHECK_FALSE(parseNamedModManifest(manifestText("Bad-Id"), "Bad-Id", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("engine"), "engine", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("worlds"), "worlds", error));
    // The format, a name and a version are required; keys the schema does not know are refused.
    CHECK_FALSE(parseNamedModManifest("format: 2\nid: a\nname: A\nversion: 1\n", "a", error));
    CHECK_FALSE(parseNamedModManifest("format: 1\nid: a\nversion: 1\n", "a", error));
    CHECK_FALSE(parseNamedModManifest("format: 1\nid: a\nname: A\n", "a", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("a", "requires: [b]\n"), "a", error));
    CHECK(error.find("requires") != std::string::npos);
    CHECK_FALSE(parseNamedModManifest("- not a map\n", "a", error));
    CHECK_FALSE(parseNamedModManifest("format: [1\n", "a", error));
    // Map kinds, table files inside the mod, map numbers.
    CHECK_FALSE(parseNamedModManifest(
        manifestText("a", "maps:\n  - {file: x.blv, world: mm6, kind: copy}\n"), "a", error));
    CHECK_FALSE(parseNamedModManifest(
        manifestText("a", "tables:\n  - {table: map_stats.txt, append: ../outside.txt}\n"), "a", error));
    CHECK_FALSE(parseNamedModManifest(
        manifestText("a", "tables:\n  - {table: ../map_stats.txt, append: tables/a.txt}\n"), "a", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("a", "tables:\n  - {table: map_stats.txt}\n"), "a", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("a", "map_numbers: [0]\n"), "a", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("a", "map_numbers: [5, 5]\n"), "a", error));
    CHECK_FALSE(parseNamedModManifest(manifestText("a", "idRanges:\n  maps: {begin: 10, end: 5}\n"), "a", error));
    CHECK(parseNamedModManifest(manifestText("a"), "a", error));
}

TEST_CASE("named mods: the enabled list reads in order, writes back and refuses a malformed file")
{
    std::string error;
    const std::optional<std::vector<std::string>> ids =
        parseEnabledModList("format: 1\nenabled: [b_mod, a_mod, b_mod]\n", error);
    REQUIRE(ids);
    CHECK(*ids == std::vector<std::string>{"b_mod", "a_mod"});
    // What the studio's named install writes (block style), and an empty file.
    CHECK(parseEnabledModList("format: 1\nenabled:\n  - s6_demo\n", error) == std::vector<std::string>{"s6_demo"});
    CHECK(parseEnabledModList("", error) == std::vector<std::string>{});
    CHECK(parseEnabledModList("format: 1\nenabled: []\n", error) == std::vector<std::string>{});
    CHECK(parseEnabledModList("format: 1\n", error) == std::vector<std::string>{});
    CHECK_FALSE(parseEnabledModList("enabled: [a]\n", error));
    CHECK_FALSE(parseEnabledModList("format: 1\nenabled: a\n", error));
    CHECK_FALSE(parseEnabledModList("format: 1\nenabled: [Bad-Id]\n", error));
    CHECK_FALSE(parseEnabledModList("format: 1\nenabled: [a\n", error));

    const std::string written = formatEnabledModList({"z_mod", "a_mod"});
    CHECK(parseEnabledModList(written, error) == std::vector<std::string>{"z_mod", "a_mod"});
    CHECK(parseEnabledModList(formatEnabledModList({}), error) == std::vector<std::string>{});
}

TEST_CASE("named mods: the enabled list decides which mods are on and their mount order")
{
    NamedModCatalog catalog = catalogOf({manifest("alpha"), manifest("beta"), manifest("gamma")}, {"gamma", "alpha",
        "missing"});
    NamedModEntry broken;
    broken.id = "broken";
    broken.reason = "mod.yml needs a name and a version";
    catalog.mods.push_back(broken);
    catalog.enabledIds.push_back("broken");
    resolveNamedMods(catalog, {});

    CHECK(catalog.mountOrder == std::vector<std::string>{"gamma", "alpha"});
    CHECK(catalog.find("alpha")->state == NamedModState::On);
    CHECK(catalog.find("gamma")->state == NamedModState::On);
    // Not listed: off. Listed but not installed: named, nothing mounted.
    CHECK(catalog.find("beta")->state == NamedModState::Off);
    CHECK(catalog.missingIds == std::vector<std::string>{"missing"});
    CHECK(catalog.find("broken")->state == NamedModState::Refused);
    CHECK(catalog.find("broken")->reason == "mod.yml needs a name and a version");

    const std::vector<NamedModManifest> mounted = catalog.mountedManifests();
    REQUIRE(mounted.size() == 2);
    CHECK(mounted[0].id == "gamma");
    CHECK(mounted[1].id == "alpha");

    refuseNamedMod(catalog, "gamma", "its rows of map_stats.txt");
    CHECK(catalog.mountOrder == std::vector<std::string>{"alpha"});
    CHECK(catalog.find("gamma")->state == NamedModState::Refused);

    // Nothing listed: nothing on.
    NamedModCatalog none = catalogOf({manifest("alpha")}, {});
    resolveNamedMods(none, {});
    CHECK(none.mountOrder.empty());
    CHECK(none.find("alpha")->state == NamedModState::Off);
}

TEST_CASE("named mods: id ranges and map numbers that clash refuse the later mod")
{
    const std::vector<NamedModRangeOwner> owners = {
        {"world mm9", {{"monsters", 9000, 9999}, {"maps", 9001, 9080}}},
        {"ruleset maw", {{"qbits", 10001, 10099}}},
    };

    // A world's or a ruleset's range.
    NamedModCatalog catalog = catalogOf({
        manifest("world_clash", {}, {{"monsters", 9500, 9510}}),
        manifest("ruleset_clash", {}, {{"qbits", 10050, 10060}}),
        manifest("map_in_world", {9050}),
        manifest("fine", {9306}, {{"maps", 9300, 9349}, {"qbits", 20000, 20010}}),
    }, {"world_clash", "ruleset_clash", "map_in_world", "fine"});
    resolveNamedMods(catalog, owners);
    CHECK(catalog.mountOrder == std::vector<std::string>{"fine"});
    CHECK(catalog.find("world_clash")->reason.find("world mm9") != std::string::npos);
    CHECK(catalog.find("ruleset_clash")->reason.find("ruleset maw") != std::string::npos);
    CHECK(catalog.find("map_in_world")->reason.find("9050") != std::string::npos);

    // Another mod's range or numbers: the earlier one in the list stays, whichever it is.
    NamedModCatalog mods = catalogOf({
        manifest("first", {9306}, {{"maps", 9300, 9349}}),
        manifest("overlapping_range", {9345}, {{"maps", 9340, 9360}}),
        manifest("same_number", {9306}),
        manifest("number_in_range", {9310}),
        manifest("range_holds_number", {}, {{"maps", 9200, 9400}}),
        manifest("outside_own_range", {9500}, {{"maps", 9400, 9449}}),
        manifest("second", {9450}, {{"maps", 9450, 9499}}),
    }, {"first", "overlapping_range", "same_number", "number_in_range", "range_holds_number", "outside_own_range",
        "second"});
    resolveNamedMods(mods, {});
    CHECK(mods.mountOrder == std::vector<std::string>{"first", "second"});
    CHECK(mods.find("overlapping_range")->reason.find("mod first") != std::string::npos);
    CHECK(mods.find("same_number")->reason.find("9306") != std::string::npos);
    CHECK(mods.find("number_in_range")->reason.find("mod first") != std::string::npos);
    CHECK(mods.find("range_holds_number")->reason.find("mod first") != std::string::npos);
    CHECK(mods.find("outside_own_range")->reason.find("its own maps range") != std::string::npos);

    // Listed the other way round, the other mod stays.
    NamedModCatalog reversed = catalogOf({manifest("first", {9306}), manifest("same_number", {9306})},
        {"same_number", "first"});
    resolveNamedMods(reversed, {});
    CHECK(reversed.mountOrder == std::vector<std::string>{"same_number"});
    CHECK(reversed.find("first")->state == NamedModState::Refused);

    // Two mods that bring the same new map.
    NamedModManifest left = manifest("left");
    left.maps.push_back({"studio06.blv", "mm6", "new"});
    NamedModManifest right = manifest("right");
    right.maps.push_back({"studio06.blv", "mm6", "new"});
    NamedModManifest overlay = manifest("overlay");
    overlay.maps.push_back({"studio06.blv", "mm6", "overlay"});
    NamedModCatalog sameMap = catalogOf({left, right, overlay}, {"left", "right", "overlay"});
    resolveNamedMods(sameMap, {});
    CHECK(sameMap.mountOrder == std::vector<std::string>{"left", "overlay"});
}

TEST_CASE("named mods: two mods' table rows compose in order, and a clash leaves the later mod's rows out")
{
    NamedModManifest first = manifest("first");
    first.tables.push_back({"map_stats.txt", "tables/map_stats.txt.override.txt", "tables/map_stats.txt.append.txt",
        "key\tcolumn\tvalue\n2\t#1\tRavenshore (first)\n", "9306\tThe Breakwater Store\tstudio06.blv\n\n"});
    NamedModManifest second = manifest("second");
    second.tables.push_back({"map_stats.txt", "tables/o.txt", "tables/a.txt",
        "key\tcolumn\tvalue\n2\t#1\tRavenshore (second)\n9306\t#2\tstudio06b.blv\n",
        "9307\tThe Loft\tstudio07.blv\r\n"});

    Rows rows = mapStatsRows();
    std::vector<std::string> errors;
    applyNamedModTables(rows, {first, second}, "engine/data_tables/map_stats.txt", errors);
    CHECK(errors.empty());
    REQUIRE(rows.size() == 7);
    // The later mod's cell wins; its override reaches the earlier mod's added row.
    CHECK(rows[4][1] == "Ravenshore (second)");
    CHECK(rows[5] == std::vector<std::string>{"9306", "The Breakwater Store", "studio06b.blv"});
    CHECK(rows[6][0] == "9307");
    CHECK(rows[6][2] == "studio07.blv");

    // Another table, or a path outside engine/data_tables: untouched.
    Rows other = mapStatsRows();
    applyNamedModTables(other, {first, second}, "engine/data_tables/house_data.txt", errors);
    applyNamedModTables(other, {first, second}, "worlds/mm9/data_tables/map_stats.txt", errors);
    CHECK(other == mapStatsRows());
    CHECK(errors.empty());

    // A second mod adding a row with a key the first added, or changing a row that is not there: its rows are left
    // out, the first mod's stay.
    NamedModManifest clash = manifest("clash");
    clash.tables.push_back({"map_stats.txt", "", "tables/a.txt", "", "9306\tAnother map\tother.blv\n"});
    NamedModManifest unknownKey = manifest("unknown_key");
    unknownKey.tables.push_back({"map_stats.txt", "tables/o.txt", "", "key\tcolumn\tvalue\n77\t#1\tNowhere\n", ""});
    Rows clashed = mapStatsRows();
    applyNamedModTables(clashed, {first, clash, unknownKey}, "engine/data_tables/map_stats.txt", errors);
    REQUIRE(errors.size() == 2);
    CHECK(errors[0].starts_with("clash: tables/a.txt"));
    CHECK(errors[0].find("9306") != std::string::npos);
    CHECK(errors[1].starts_with("unknown_key: tables/o.txt"));
    REQUIRE(clashed.size() == 6);
    CHECK(clashed[5][1] == "The Breakwater Store");

    // An added row whose key the shipped table has.
    NamedModTable shipped{"map_stats.txt", "", "a.txt", "", "1\tAnother island\tout99.odm\n"};
    Rows unchanged = mapStatsRows();
    std::string error;
    CHECK_FALSE(applyNamedModTable(unchanged, shipped, error));
    CHECK(unchanged == mapStatsRows());
}

TEST_CASE("named mods: a mods folder is read with its manifests, table files and enabled list")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path mods = root / "mods";

    // No folder: an empty catalog.
    const NamedModCatalog missing = readNamedModCatalog(mods);
    CHECK(missing.mods.empty());
    CHECK(missing.enabledIds.empty());
    CHECK(missing.enabledListError.empty());

    writeTextFile(mods / "b_mod" / "mod.yml", manifestText("b_mod",
        "tables:\n  - {table: map_stats.txt, append: tables/map_stats.txt.append.txt}\n"));
    writeTextFile(mods / "b_mod" / "tables" / "map_stats.txt.append.txt", "9306\tStore\tstudio06.blv\n");
    writeTextFile(mods / "a_mod" / "mod.yml", manifestText("a_mod"));
    writeTextFile(mods / "no_table" / "mod.yml", manifestText("no_table",
        "tables:\n  - {table: map_stats.txt, override: tables/missing.txt}\n"));
    writeTextFile(mods / "wrong_folder" / "mod.yml", manifestText("another_id"));
    // The loose layout and the studio's merged records are no named mods.
    writeTextFile(mods / "engine" / "data_tables" / "house_data.txt", "loose");
    writeTextFile(mods / "worlds" / "mm6" / "maps" / "x.blv", "loose");
    writeTextFile(mods / "studio_mods" / "s6_demo" / "mod.yml", manifestText("s6_demo"));
    writeTextFile(mods / "studio_mods.yml", "format: 1\n");
    writeTextFile(mods / "enabled.yml", "format: 1\nenabled: [b_mod, no_table, wrong_folder, a_mod]\n");

    NamedModCatalog catalog = readNamedModCatalog(mods);
    REQUIRE(catalog.mods.size() == 4);
    CHECK(catalog.mods[0].id == "a_mod");
    CHECK(catalog.mods[1].id == "b_mod");
    REQUIRE(catalog.mods[1].manifest);
    CHECK(catalog.mods[1].manifest->tables[0].appendText == "9306\tStore\tstudio06.blv\n");
    CHECK_FALSE(catalog.find("no_table")->manifest);
    CHECK(catalog.find("no_table")->reason.find("tables/missing.txt") != std::string::npos);
    CHECK_FALSE(catalog.find("wrong_folder")->manifest);
    CHECK(catalog.find("studio_mods") == nullptr);
    CHECK(catalog.enabledIds == std::vector<std::string>{"b_mod", "no_table", "wrong_folder", "a_mod"});

    resolveNamedMods(catalog, {});
    CHECK(catalog.mountOrder == std::vector<std::string>{"b_mod", "a_mod"});
    CHECK(catalog.find("no_table")->state == NamedModState::Refused);
    CHECK(catalog.find("wrong_folder")->state == NamedModState::Refused);

    // A malformed list enables nothing.
    writeTextFile(mods / "enabled.yml", "enabled: [b_mod]\n");
    NamedModCatalog malformed = readNamedModCatalog(mods);
    CHECK_FALSE(malformed.enabledListError.empty());
    resolveNamedMods(malformed, {});
    CHECK(malformed.mountOrder.empty());

    std::filesystem::remove_all(root);
}

TEST_CASE("named mods: switching a mod on and off edits enabled.yml and nothing else")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path mods = root / "mods";
    writeTextFile(mods / "a_mod" / "mod.yml", manifestText("a_mod"));
    writeTextFile(mods / "b_mod" / "mod.yml", manifestText("b_mod"));
    std::string error;

    // No list yet: switching on writes one; the order is the order switched on.
    REQUIRE(setNamedModEnabled(mods, "b_mod", true, error));
    REQUIRE(setNamedModEnabled(mods, "a_mod", true, error));
    REQUIRE(setNamedModEnabled(mods, "a_mod", true, error));
    CHECK(readNamedModCatalog(mods).enabledIds == std::vector<std::string>{"b_mod", "a_mod"});

    REQUIRE(setNamedModEnabled(mods, "b_mod", false, error));
    REQUIRE(setNamedModEnabled(mods, "b_mod", false, error));
    CHECK(readNamedModCatalog(mods).enabledIds == std::vector<std::string>{"a_mod"});
    CHECK(std::filesystem::exists(mods / "b_mod" / "mod.yml"));

    // A mod that is not installed cannot be switched on; a malformed list is not overwritten.
    CHECK_FALSE(setNamedModEnabled(mods, "c_mod", true, error));
    CHECK(error.find("c_mod") != std::string::npos);
    writeTextFile(mods / "enabled.yml", "enabled: [a_mod\n");
    CHECK_FALSE(setNamedModEnabled(mods, "b_mod", true, error));
    CHECK(readTextFile(mods / "enabled.yml") == "enabled: [a_mod\n");

    std::filesystem::remove_all(root);
}

TEST_CASE("named mods: a development root mounts the mods that are on, checked against the worlds and the tables")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path assetRoot = root / "assets_dev";
    const std::filesystem::path mods = root / "mods";
    writeTextFile(assetRoot / "engine" / "data_tables" / "map_stats.txt",
        "\tMap Stats\n\t\tReset\n#\tName\tFile name\n1\tDagger Wound Island\tout01.odm\n");
    writeTextFile(assetRoot / "engine" / "data_tables" / "spells.txt", "game-spells");
    writeTextFile(assetRoot / "worlds" / "mm6" / "world.yml",
        "id: mm6\nname: MM6\nidRanges:\n  monsters: {begin: 500, end: 599}\n");
    writeTextFile(assetRoot / "worlds" / "mm6" / "maps" / "d01.blv", "game-map");

    // On: a new map with its row, and its own copy of a game file. Its table row clashes with nothing.
    writeTextFile(mods / "store" / "mod.yml", manifestText("store",
        "maps:\n  - {file: studio06.blv, world: mm6, kind: new}\n"
        "tables:\n  - {table: map_stats.txt, append: tables/map_stats.txt.append.txt}\n"
        "map_numbers: [9306]\n"));
    writeTextFile(mods / "store" / "tables" / "map_stats.txt.append.txt", "9306\tThe Store\tstudio06.blv\n");
    writeTextFile(mods / "store" / "worlds" / "mm6" / "maps" / "studio06.blv", "store-map");
    writeTextFile(mods / "store" / "engine" / "data_tables" / "spells.txt", "store-spells");
    // Later in the list, so in front: its copy of the same file wins.
    writeTextFile(mods / "later" / "mod.yml", manifestText("later"));
    writeTextFile(mods / "later" / "engine" / "data_tables" / "spells.txt", "later-spells");
    writeTextFile(mods / "later" / "worlds" / "mm6" / "events" / "maps" / "d01_later.lua", "overlay-script");
    // Refused: its monsters overlap the world's, and its row has a key the table has.
    writeTextFile(mods / "monsters" / "mod.yml", manifestText("monsters", "idRanges:\n  monsters: {begin: 550, end: "
        "560}\n"));
    writeTextFile(mods / "monsters" / "engine" / "data_tables" / "spells.txt", "monster-spells");
    writeTextFile(mods / "same_row" / "mod.yml", manifestText("same_row",
        "tables:\n  - {table: map_stats.txt, append: tables/rows.txt}\n"));
    writeTextFile(mods / "same_row" / "tables" / "rows.txt", "1\tAnother island\tout99.odm\n");
    writeTextFile(mods / "same_row" / "worlds" / "mm6" / "maps" / "d01.blv", "same-row-map");
    writeTextFile(mods / "enabled.yml", "format: 1\nenabled: [store, monsters, same_row, later]\n");

    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    InstalledContentOptions options;
    options.modsRoot = mods;
    AssetFileSystem fs;
    REQUIRE(fs.initialize(root, assetRoot, AssetScaleTier::X1, profile, "mm6", options));
    const std::vector<std::string> gameOnly = fs.getSearchPaths();
    CHECK(fs.readTextFile("engine/data_tables/spells.txt") == std::optional<std::string>("game-spells"));

    NamedModCatalog catalog;
    REQUIRE(mountNamedMods(fs, catalog));
    CHECK(catalog.mountOrder == std::vector<std::string>{"store", "later"});
    CHECK(catalog.find("monsters")->state == NamedModState::Refused);
    CHECK(catalog.find("monsters")->reason.find("world mm6") != std::string::npos);
    CHECK(catalog.find("same_row")->state == NamedModState::Refused);
    CHECK(catalog.find("same_row")->reason.find("map_stats.txt") != std::string::npos);
    CHECK(fs.installedContentOptions().namedMods == std::vector<std::string>{"store", "later"});
    CHECK(fs.readTextFile("engine/data_tables/spells.txt") == std::optional<std::string>("later-spells"));
    CHECK(fs.readTextFile("worlds/mm6/maps/studio06.blv") == std::optional<std::string>("store-map"));
    CHECK(fs.readTextFile("Data/games/studio06.blv") == std::optional<std::string>("store-map"));
    CHECK(fs.readTextFile("Data/games/d01.blv") == std::optional<std::string>("game-map"));
    const std::vector<std::string> scripts = fs.enumerate("events/maps");
    CHECK(std::find(scripts.begin(), scripts.end(), "d01_later.lua") != scripts.end());

    // A world switch mounts the same mods again.
    REQUIRE(fs.switchActiveWorld("mm8"));
    CHECK(fs.readTextFile("engine/data_tables/spells.txt") == std::optional<std::string>("later-spells"));
    REQUIRE(fs.switchActiveWorld("mm6"));

    // None on: the mounts are the game's alone again.
    REQUIRE(fs.setNamedMods({}));
    CHECK(fs.getSearchPaths() == gameOnly);
    CHECK(fs.readTextFile("engine/data_tables/spells.txt") == std::optional<std::string>("game-spells"));
    CHECK_FALSE(fs.exists("worlds/mm6/maps/studio06.blv"));

    // No mods folder, and a folder whose mods are all off: nothing is mounted again.
    writeTextFile(mods / "enabled.yml", "format: 1\nenabled: []\n");
    NamedModCatalog off;
    REQUIRE(mountNamedMods(fs, off));
    CHECK(off.mountOrder.empty());
    CHECK(fs.getSearchPaths() == gameOnly);

    std::filesystem::remove_all(root);
}
