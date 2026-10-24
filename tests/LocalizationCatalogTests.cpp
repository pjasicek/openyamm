#include "game/localization/LocalizationCatalog.h"
#include "game/party/SkillData.h"
#include "game/ui/GameplayUiController.h"

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
    CHECK_EQ(catalog.translate("The Door is Locked"), "Дверь заперта");
    CHECK_EQ(catalog.translate("Spell not learned"), "Заклинание не изучено");
    CHECK_EQ(catalog.translate("OpenYAMM"), "OpenYAMM");
    CHECK_EQ(catalog.translateText("Quick spell set to Fire Bolt"), "Быстрое заклинание: Fire Bolt");
    CHECK_EQ(catalog.translateText("Brewed 3 x Cure Wounds"), "Сварено: 3 × Cure Wounds");
    CHECK_EQ(
        catalog.translateText("You found 25 gold and an item (Iron Sword)!"),
        "Найдено золота: 25; найден предмет: Iron Sword!");
    CHECK_EQ(catalog.translateText("Untranslated runtime text"), "Untranslated runtime text");
    CHECK_EQ(
        catalog.format("Voice {voice_number} — {race_name}", {{"voice_number", "3"}, {"race_name", "Человек"}}),
        "Голос 3 — Человек");
}

TEST_CASE("Russian localization covers every displayed character skill name")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));

    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));
    for (const std::string &skill : Game::allCanonicalSkillNames())
    {
        const std::string displayName = Game::displaySkillName(skill);
        INFO(displayName);
        CHECK_NE(catalog.translate(displayName), displayName);
    }
    CHECK_EQ(catalog.translate(Game::displaySkillName("LeatherArmor")), "Кожаные доспехи");
    CHECK_EQ(catalog.translate(Game::displaySkillName("ChainArmor")), "Кольчуга");
    CHECK_EQ(catalog.translate(Game::displaySkillName("RepairItem")), "Ремонт");
    CHECK_EQ(catalog.translate(Game::displaySkillName("Bodybuilding")), "Бодибилдинг");
}

TEST_CASE("English localization catalog uses source text")
{
    Engine::AssetFileSystem assetFileSystem;
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.language(), "en");
    CHECK_EQ(catalog.translate("New Game"), "New Game");
}

TEST_CASE("Gameplay UI localizes status and event dialog text")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));

    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));

    Game::GameplayUiController controller;
    controller.bindLocalizationCatalog(&catalog);
    controller.setStatusBarEvent("Quick spell set to Fire Bolt");
    CHECK_EQ(controller.statusBar().eventText, "Быстрое заклинание: Fire Bolt");

    Game::EventDialogContent content;
    content.title = "The Door is Locked";
    content.lines.push_back("Empty sack");
    controller.setEventDialogContent(content);
    CHECK_EQ(controller.eventDialog().content.title, "Дверь заперта");
    REQUIRE_EQ(controller.eventDialog().content.lines.size(), 1);
    CHECK_EQ(controller.eventDialog().content.lines.front(), "Пустой мешок");
}
}
