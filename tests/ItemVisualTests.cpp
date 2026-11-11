#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "engine/TextTable.h"
#include "game/party/CharacterState.h"
#include "game/tables/ItemTable.h"

#include <doctest/doctest.h>
#include <filesystem>

TEST_CASE("reviewed item visuals preserve body and slot scope and reject partial invalid imports")
{
    using namespace OpenYAMM;
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem fs;
    REQUIRE(fs.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1));
    Game::ItemTable table;
    REQUIRE(table.load(fs, {{"1", "item001", "Sword"}, {"2", "item150", "Medallion"}}, {}));
    const std::vector<std::vector<std::string>> rows = {
        {"placement", "1", "0", "MainHand", "-2", "3"},
        {"placement", "1", "1", "MainHand", "4", "-5"},
        {"placement", "1", "0", "OffHand", "6", "7"},
        {"inventory", "2", "", "", "", "", "1", "2", "7.5e-1", "1"}
    };
    std::string error;
    REQUIRE(table.loadVisualRows(rows, error));
    const Game::ItemDefinition *pSword = table.get(1);
    REQUIRE(pSword != nullptr);
    REQUIRE(pSword->equipmentPlacements.size() == 3);
    CHECK(pSword->equipmentPlacements[0].dollType == 0);
    CHECK(pSword->equipmentPlacements[0].slot == Game::EquipmentSlot::MainHand);
    CHECK(pSword->equipmentPlacements[0].x == -2);
    CHECK(pSword->equipmentPlacements[1].dollType == 1);
    CHECK(pSword->equipmentPlacements[2].slot == Game::EquipmentSlot::OffHand);
    CHECK(table.get(2)->inventoryWidth == 1);
    CHECK(table.get(2)->inventoryHeight == 2);
    CHECK(table.get(2)->inventoryDrawScale == doctest::Approx(0.75));
    CHECK(table.get(2)->jewelryDrawScale == doctest::Approx(1.0));
    for (const std::vector<std::string> &invalid : {
        std::vector<std::string>{"placement", "1", "0", "MainHand", "1", "1"},
        std::vector<std::string>{"placement", "1", "6", "MainHand", "1", "1"},
        std::vector<std::string>{"placement", "1", "0", "MainHand", "1bad", "1"},
        std::vector<std::string>{"inventory", "1", "", "", "", "", "1", "1", "nan", "1"},
        std::vector<std::string>{"inventory", "1", "", "", "", "", "0", "1", "1", "1"}})
    {
        std::vector<std::vector<std::string>> badRows = rows;
        badRows.push_back(invalid);
        CHECK_FALSE(table.loadVisualRows(badRows, error));
        CHECK_FALSE(error.empty());
        CHECK(table.get(1)->equipmentPlacements.size() == 3);
        CHECK(table.get(2)->inventoryDrawScale == doctest::Approx(0.75));
    }
    for (const std::string &invalidScale : {"", "bad", "0.75bad", "nan", "inf", "0", "-0.5", "1.01",
        "1e50", "1e-50"})
    {
        INFO(invalidScale);
        std::vector<std::vector<std::string>> badRows = rows;
        badRows[3][8] = invalidScale;
        CHECK_FALSE(table.loadVisualRows(badRows, error));
        CHECK_FALSE(error.empty());
        CHECK(table.get(1)->equipmentPlacements.size() == 3);
        CHECK(table.get(2)->inventoryDrawScale == doctest::Approx(0.75));
        CHECK(table.get(2)->jewelryDrawScale == doctest::Approx(1.0));
    }
}

TEST_CASE("installed icon packages preserve native logical dimensions across all world namespaces")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    AssetFileSystem fs;
    REQUIRE(fs.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    DirectoryAssetPathCache directories;
    AssetPathLookupCache paths;
    BinaryAssetCache binaries;
    for (const std::string &package : {"engine", "worlds/mm6", "worlds/mm7", "worlds/mm8"})
    {
        const std::filesystem::path folder = root / "assets_dev" / package / "icons_x2";
        REQUIRE(std::filesystem::is_directory(folder));
        size_t count = 0;
        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(folder))
        {
            if (!entry.is_regular_file())
            {
                continue;
            }
            const std::string name = entry.path().filename().string();
            const std::string extension = entry.path().extension().string();
            // Cooked HUD art (.oytex) and portrait set manifests sit beside the images (tools/cook_ui_textures.py).
            if (extension != ".png" && extension != ".bmp" && extension != ".pcx")
            {
                continue;
            }
            const std::optional<std::string> path = findImageAssetPath(fs, package + "/icons", name, directories, paths);
            INFO(package, "/", name);
            REQUIRE(path);
            const bool hasX4Override = package == "worlds/mm7"
                && std::filesystem::is_regular_file(folder.parent_path() / "icons_x4" / name);
            CHECK(assetScaleTierFromResolvedPath(*path) == (hasX4Override ? AssetScaleTier::X4 : AssetScaleTier::X2));
            ++count;
        }
        CHECK(count > 0);
    }
    const std::optional<ImagePixelsBgra> mask = loadImageAssetPixelsBgra(
        fs, "engine/icons", "7item344", directories, paths, binaries);
    REQUIRE(mask);
    CHECK(mask->width == 100);
    CHECK(mask->height == 110);
    CHECK(scalePhysicalPixelsToLogical(mask->width, mask->assetScaleTier) == 50);
    CHECK(scalePhysicalPixelsToLogical(mask->height, mask->assetScaleTier) == 55);
}
