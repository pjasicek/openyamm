#include "game/localization/LocalizationCatalog.h"

#include "engine/AssetFileSystem.h"

#include <doctest/doctest.h>

#include <filesystem>

namespace OpenYAMM
{
TEST_CASE("Russian localization catalog translates known UI text and preserves unknown text")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));

    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));
    CHECK_EQ(catalog.language(), "ru");
    CHECK_EQ(catalog.translate("New Game"), "Новая игра");
    CHECK_EQ(catalog.translate("OpenYAMM"), "OpenYAMM");
    CHECK_EQ(
        catalog.format("Voice {voice_number} — {race_name}", {{"voice_number", "3"}, {"race_name", "Человек"}}),
        "Голос 3 — Человек");
}

TEST_CASE("English localization catalog uses source text")
{
    Engine::AssetFileSystem assetFileSystem;
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.language(), "en");
    CHECK_EQ(catalog.translate("New Game"), "New Game");
}
}
