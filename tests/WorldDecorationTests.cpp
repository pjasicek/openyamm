#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/WorldDecorations.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/tables/SpriteTables.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace
{
using Rows = std::vector<std::vector<std::string>>;

std::vector<std::string> decorationRow(uint32_t number, const std::string &name, uint16_t spriteId)
{
    return {std::to_string(number), name, "null", "0", "16", "32", "0", "0", "0", "0", "0", "0",
        std::to_string(spriteId), "-"};
}

Rows engineRows()
{
    return {
        {"Decoration Data", "", "", "Descriptor"},
        {"#", "InternalName", "Hint", "Type", "Radius", "Height", "LightRadius", "LightRed", "LightGreen",
            "LightBlue", "SoundId", "Flags", "SpriteId", "Comments", "MapAliases"},
        decorationRow(1, "null", 0),
        decorationRow(2, "barrel", 10),
        decorationRow(3, "tree", 11),
    };
}

OpenYAMM::Game::WorldDecorationRows worldRows(const Rows &rows, uint32_t begin = 2001, uint32_t end = 2999)
{
    return {"custom", {"decorations", begin, end}, rows};
}

std::string tableText(const Rows &rows)
{
    std::string text;

    for (const std::vector<std::string> &row : rows)
    {
        for (size_t index = 0; index < row.size(); ++index)
        {
            text += (index == 0 ? "" : "\t") + row[index];
        }

        text += "\n";
    }

    return text;
}

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_world_decorations_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

const std::string WorldManifestWithDecorations =
    "id: custom\n"
    "idRanges:\n"
    "  decorations:\n"
    "    begin: 2001\n"
    "    end: 2999\n"
    "tableContributions:\n"
    "  - table: decorations\n"
    "    idDomain: decorations\n"
    "    mode: append\n"
    "    path: data_tables/decoration_data.txt\n";
}

TEST_CASE("world decoration rows follow the engine rows; the numbers between are no decoration")
{
    const Rows world = {{"#", "InternalName"}, decorationRow(2001, "custom_book", 24801),
        decorationRow(2003, "custom_well", 24802)};
    const OpenYAMM::Game::WorldDecorationRows contribution = worldRows(world);
    Rows composed;
    std::string error;
    REQUIRE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &contribution, composed, error));
    CHECK(error.empty());
    CHECK_EQ(composed.size(), engineRows().size() + 2);

    OpenYAMM::Game::DecorationTable table;
    REQUIRE(table.loadRows(composed));
    REQUIRE(table.get(1) != nullptr);
    CHECK_EQ(table.get(1)->internalName, "barrel");
    CHECK(table.get(3) == nullptr);
    CHECK(table.get(1999) == nullptr);
    REQUIRE(table.get(2000) != nullptr);
    CHECK_EQ(table.get(2000)->internalName, "custom_book");
    CHECK_EQ(table.get(2000)->spriteId, 24801);
    CHECK(table.get(2001) == nullptr);
    REQUIRE(table.get(2002) != nullptr);
    CHECK_EQ(table.get(2002)->internalName, "custom_well");
    CHECK(table.get(2003) == nullptr);
    CHECK_EQ(table.findIdByInternalName("custom_well"), std::optional<uint16_t>(2002));
    CHECK(table.findByInternalName("custom_missing") == nullptr);
}

TEST_CASE("decoration rows must increase")
{
    OpenYAMM::Game::DecorationTable table;
    Rows rows = engineRows();
    rows.push_back(decorationRow(3, "tree_again", 12));
    CHECK_FALSE(table.loadRows(rows));

    rows = engineRows();
    rows.push_back(decorationRow(2, "barrel_before", 12));
    CHECK_FALSE(table.loadRows(rows));

    rows = engineRows();
    rows.push_back(decorationRow(70000, "past_sixteen_bits", 12));
    CHECK_FALSE(table.loadRows(rows));
}

TEST_CASE("world decoration contributions reject bad ranges, rows and names")
{
    Rows composed;
    std::string error;

    SUBCASE("a range overlapping the engine rows")
    {
        const OpenYAMM::Game::WorldDecorationRows contribution = worldRows({decorationRow(3, "custom", 1)}, 3, 99);
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &contribution, composed, error));
        CHECK(error.find("must start past the engine's last decoration (3)") != std::string::npos);
    }

    SUBCASE("a range past the largest decoration id")
    {
        const OpenYAMM::Game::WorldDecorationRows contribution = worldRows({}, 2001, 70000);
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &contribution, composed, error));
    }

    SUBCASE("a row outside the world's range")
    {
        const OpenYAMM::Game::WorldDecorationRows contribution = worldRows({decorationRow(3001, "custom", 1)});
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &contribution, composed, error));
        CHECK(error.find("outside the world's range 2001-2999") != std::string::npos);
    }

    SUBCASE("rows repeating or going back")
    {
        const OpenYAMM::Game::WorldDecorationRows repeated =
            worldRows({decorationRow(2002, "custom_a", 1), decorationRow(2002, "custom_b", 2)});
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &repeated, composed, error));
        CHECK(error.find("increasing order") != std::string::npos);

        const OpenYAMM::Game::WorldDecorationRows backwards =
            worldRows({decorationRow(2005, "custom_a", 1), decorationRow(2002, "custom_b", 2)});
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &backwards, composed, error));
    }

    SUBCASE("a name the engine has, or the world repeats")
    {
        const OpenYAMM::Game::WorldDecorationRows engineName = worldRows({decorationRow(2001, "Barrel", 1)});
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &engineName, composed, error));
        CHECK(error.find("repeats a decoration name") != std::string::npos);

        const OpenYAMM::Game::WorldDecorationRows worldName =
            worldRows({decorationRow(2001, "custom", 1), decorationRow(2002, "custom", 2)});
        CHECK_FALSE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &worldName, composed, error));
    }
}

TEST_CASE("a world without a decoration contribution sees the engine rows unchanged")
{
    Rows composed;
    std::string error;
    REQUIRE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), nullptr, composed, error));
    CHECK_EQ(composed, engineRows());

    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "engine/data_tables/decoration_data.txt", tableText(engineRows()));
    writeTextFile(assetRoot / "worlds/plain/world.yml", "id: plain\n");
    writeTextFile(assetRoot / "worlds/custom/world.yml", WorldManifestWithDecorations);
    writeTextFile(assetRoot / "worlds/custom/data_tables/decoration_data.txt",
        tableText({{"#", "InternalName"}, decorationRow(2001, "custom_book", 24801)}));
    writeTextFile(assetRoot / "worlds/custom/rendering/sprite_frame_data_world_decorations.yml",
        "sprites:\n"
        "  - sprite_id: 24801\n"
        "    sprite_name: custom_book\n"
        "    frames:\n"
        "      - texture_name: pending\n"
        "        frame_length_raw: 0\n");

    for (const char *pWorld : {"plain", "custom"})
    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, OpenYAMM::Engine::AssetScaleTier::X1, pWorld));
        Rows rows;
        REQUIRE(OpenYAMM::Game::loadDecorationTableRows(assetFileSystem, rows, error));
        OpenYAMM::Game::SpriteFrameTable sprites;
        REQUIRE(sprites.loadFromYaml("sprites:\n  - sprite_id: 10\n    sprite_name: barrel\n    frames:\n"
            "      - texture_name: barrel\n        frame_length_raw: 0\n", error));
        REQUIRE(OpenYAMM::Game::appendWorldDecorationSpriteFrames(assetFileSystem, sprites, error));

        if (std::string(pWorld) == "plain")
        {
            CHECK_EQ(rows, engineRows());
            CHECK_FALSE(sprites.findFrameIndexBySpriteName("custom_book"));
        }
        else
        {
            REQUIRE_EQ(rows.size(), engineRows().size() + 1);
            CHECK_EQ(rows.back()[1], "custom_book");
            CHECK_EQ(sprites.findFrameIndexBySpriteName("custom_book"), std::optional<uint16_t>(24801));
        }
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("map entities placing a skipped or missing decoration are reported once per id")
{
    const OpenYAMM::Game::WorldDecorationRows contribution =
        worldRows({decorationRow(2001, "custom_book", 24801)});
    Rows composed;
    std::string error;
    REQUIRE(OpenYAMM::Game::composeDecorationTableRows(engineRows(), &contribution, composed, error));
    OpenYAMM::Game::DecorationTable table;
    REQUIRE(table.loadRows(composed));

    std::vector<OpenYAMM::Game::OutdoorEntity> entities(5);
    entities[0].name = "custom_book";
    entities[0].decorationListId = 1234;
    entities[1].name = "gone";
    entities[1].decorationListId = 1500;
    entities[2].name = "gone_too";
    entities[2].decorationListId = 1500;
    entities[3].name = "far";
    entities[3].decorationListId = 4000;
    entities[4].name = "barrel";
    entities[4].decorationListId = 1;

    const std::vector<OpenYAMM::Game::UnresolvedMapDecoration> unresolved =
        OpenYAMM::Game::unresolvedMapDecorations(table, entities);
    REQUIRE_EQ(unresolved.size(), 2);
    CHECK_EQ(unresolved[0].decorationId, 1500);
    CHECK_EQ(unresolved[0].firstEntityName, "gone");
    CHECK_EQ(unresolved[0].entityCount, 2);
    CHECK_EQ(unresolved[1].decorationId, 4000);
    CHECK_EQ(unresolved[1].entityCount, 1);
}

TEST_CASE("the shipped worlds load their decoration tables")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    std::string error;
    Rows engine;

    for (const char *pWorld : {"mm8", "mm9"})
    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, pWorld));
        Rows rows;
        REQUIRE_MESSAGE(OpenYAMM::Game::loadDecorationTableRows(assetFileSystem, rows, error), error);
        OpenYAMM::Game::DecorationTable table;
        REQUIRE(table.loadRows(rows));

        if (std::string(pWorld) == "mm8")
        {
            engine = rows;
        }
        else
        {
            // MM9's own decorations: rows 2001-2999 (worlds/mm9/data_tables/decoration_data.txt).
            REQUIRE_GT(rows.size(), engine.size());
            CHECK(std::equal(engine.begin(), engine.end(), rows.begin()));
            CHECK(table.get(1999) == nullptr);
            const std::optional<uint16_t> book = table.findIdByInternalName("mm9_book");
            REQUIRE(book);
            CHECK_GE(*book, 2000);

            OpenYAMM::Game::SpriteFrameTable sprites;
            REQUIRE(OpenYAMM::Game::appendWorldDecorationSpriteFrames(assetFileSystem, sprites, error));
            CHECK_EQ(sprites.findFrameIndexBySpriteName("mm9_book"),
                std::optional<uint16_t>(table.get(*book)->spriteId));
        }
    }
}
