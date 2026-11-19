#include "game/localization/LocalizationCatalog.h"
#include "game/events/EventDialogContent.h"
#include "game/tables/MergedBaseTables.h"
#include "game/party/SkillData.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameMechanics.h"
#include "game/ui/GameplayUiController.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"
#include "game/localization/LocalizedTableOverlay.h"
#include "game/tables/NpcDialogTable.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/MonsterSpellSupport.h"

#include <doctest/doctest.h>

#include <filesystem>

namespace OpenYAMM
{
TEST_CASE("MM7 Emerald Island sign cart food and dragon topic use Russian translations")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm7"));
    Game::GameDataLoader data;
    data.setLanguage("ru");
    REQUIRE(data.loadCommonForGameplay(assets));
    const Game::LocalizationCatalog &catalog = data.getLocalizationCatalog();

    CHECK_EQ(catalog.translateText("Welcome to Emerald Isle"), "Добро пожаловать на Изумрудный остров");
    CHECK_EQ(catalog.translateText("Cart"), "Повозка");
    CHECK_EQ(catalog.translateText("Enter The Temple of the Moon"), "Вход: Храм Луны");
    CHECK_EQ(catalog.translateText("Enter the Dragon's Cave"), "Вход: Пещера дракона");

    Game::GameplayUiController controller;
    controller.bindLocalizationCatalog(&catalog);
    controller.setStatusBarEvent("You find 5 food");
    CHECK_EQ(controller.statusBar().eventText, "Найдено еды: 5");

    // Global event 789 embeds this whole message, rather than requesting NPC text 988.
    const std::string dragonMessage =
        "The Dragon of Emerald Island lives in a cave in the northeast.\n"
        "I wouldn't go there, though, he doesn't like visitors.\n"
        "He spares our town so that we may pay him tribute, and in return he keeps pirates and undesirables out.";
    const std::optional<std::string> localizedDragon = data.getNpcDialogTable().getText(988);
    REQUIRE(localizedDragon.has_value());
    CHECK_NE(*localizedDragon, dragonMessage);
    CHECK_EQ(catalog.translateText(dragonMessage), *localizedDragon);

    Game::LocalizationCatalog english;
    REQUIRE(english.load(assets, "en"));
    CHECK_EQ(english.translateText("Welcome to Emerald Isle"), "Welcome to Emerald Isle");
    CHECK_EQ(english.translateText("Cart"), "Cart");
    CHECK_EQ(english.translateText("Enter The Temple of the Moon"), "Enter The Temple of the Moon");
    CHECK_EQ(english.translateText("Enter the Dragon's Cave"), "Enter the Dragon's Cave");
    CHECK_EQ(english.translateText("You find 5 food"), "You find 5 food");
    CHECK_EQ(english.translateText(dragonMessage), dragonMessage);
}

TEST_CASE("Dungeon object captions survive Russian NPC table registration across MM6 MM7 MM8")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm8"));
    Game::GameDataLoader data;
    data.setLanguage("ru");
    REQUIRE(data.loadCommonForGameplay(assets));
    const Game::LocalizationCatalog &catalog = data.getLocalizationCatalog();

    // Check the final catalog, after NPC tables have registered overlapping object and effect captions.
    CHECK_EQ(catalog.translateText("Camp Fire"), "Костёр");
    CHECK_EQ(catalog.translateText("Food Bowl"), "Миска с едой");
    CHECK_EQ(catalog.translateText("Red Barrel"), "Красная бочка");
    CHECK_EQ(catalog.translateText("Steaming Cauldron"), "Дымящийся котёл");
    CHECK_EQ(catalog.translateText("Empty bag"), "Пустой мешок");
    CHECK_EQ(catalog.translateText("Diseased!"), "Болезнь!");
    CHECK_EQ(catalog.translateText("+2 Air Resistance permanent"), "+2 к сопротивлению воздуху (постоянный эффект)");
    CHECK_EQ(catalog.translateText("Oracle Memory Crystal"), "Кристалл памяти Оракула");
    CHECK_EQ(catalog.translateText("Shard filled caskets."), "Бочки, наполненные осколками кристаллов.");
    CHECK_EQ(catalog.translateText("Ore Vein"), "Рудная жила");
    CHECK_EQ(catalog.translateText("Mine Car"), "Вагонетка");
    CHECK_EQ(catalog.translateText("Key Hole"), "Замочная скважина");
    CHECK_EQ(catalog.translateText("Submarine"), "Подводная лодка");

    for (const std::string &source : {"Stone Face", "Lord of Fire", "Glowing dinosaur bones", "Gold vein",
        "Gems", "Pool", "Wall", "Tile", "Chandelier", "Flickering Torch", "Full sack", "Cell", "Cylinder",
        "Baa Head One", "Baa Head Two", "Baa Head Three", "Baa Head Four", "Almighty Head of Baa.", "Lava pool",
        "Torch", "Sewer Grate", "Stew filled bowl.", "Crates filled with wood chips.", "Mead filled barrel.",
        "Water filled barrel.", "Mine", "Boulders.", "Small glittering pool.", "Switch.", "Sacks.", "Crystal.",
        "Table with implements atop.", "Carved mural.", "Old bones.", "Wall with missing bricks.", "Iron Maiden",
        "Long dead adventurer.", "Skeleton in a cage.", "Shelves", "Potions for sale", "Pantry", "Counter",
        "Pillar", "Vault", "Portrait", "Lift", "Leave the Arena", "Enter the Throne Room",
        "Leave the Dwarven Barrow", "Leave the Red Dwarf Mines", "Enter Castle Gloaming", "Enter the Submarine",
        "Leave the Prison of the Lord of Earth", "Talk to the Arena Master", "Gate out of the Plane of Earth"})
    {
        CAPTURE(source);
        CHECK_NE(catalog.translateText(source), source);
    }

    Game::LocalizationCatalog english;
    REQUIRE(english.load(assets, "en"));
    CHECK_EQ(english.translateText("Stone Face"), "Stone Face");
    CHECK_EQ(english.translateText("Submarine"), "Submarine");
    CHECK_EQ(english.translateText("Leave the Arena"), "Leave the Arena");
}

TEST_CASE("MM6 Hive objects messages and map transition names use Russian translations")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::GameDataLoader data;
    data.setLanguage("ru");
    REQUIRE(data.loadCommonForGameplay(assets));
    const Game::LocalizationCatalog &catalog = data.getLocalizationCatalog();

    CHECK_EQ(catalog.translate("Keg"), "Бочка");
    CHECK_EQ(catalog.translate("Protected"), "Защищено");
    for (const std::string &text : {"Door", "Switch", "Chest", "Exit", "The door is locked",
        "The Door Won't Budge", " +20 Hit Points", "Flush system deactivated", "Flush system activated.",
        "Flush sequence complete.", "Flush sequence in progress.", "Warning!  Flush system activated!"})
    {
        CAPTURE(text);
        CHECK_NE(catalog.translateText(text), text);
    }

    // The exit hint uses the map name from Lua rather than the localized map table entry.
    const Game::MapStatsEntry *pDestination = data.getMapStats().findByFileName("outa1.odm");
    REQUIRE(pDestination != nullptr);
    CHECK_EQ(catalog.translate("Sweet Water"), pDestination->name);
    CHECK_NE(catalog.translate("Sweet Water"), "Sweet Water");
    CHECK_EQ(catalog.translate("The Hive"), "«Улей»");

    Game::LocalizationCatalog english;
    REQUIRE(english.load(assets, "en"));
    CHECK_EQ(english.translate("Keg"), "Keg");
    CHECK_EQ(english.translate("Protected"), "Protected");
    CHECK_EQ(english.translate("Sweet Water"), "Sweet Water");
}

TEST_CASE("MM6 Control Center terminals translate their exact runtime messages")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assets, "ru"));

    CHECK_EQ(catalog.translateText("Computer Terminal"), "Компьютерный терминал");
    CHECK_EQ(catalog.translateText("Storage Container"), "Контейнер для хранения");
    CHECK_EQ(catalog.translateText("It's a short circuit!"), "Это короткое замыкание!");

    const std::optional<std::string> generated = assets.readTextFile("events/maps/sci-fi.lua");
    const std::optional<std::string> supplement = assets.readTextFile("events/maps/sci-fi_mmmerge.lua");
    REQUIRE(generated.has_value());
    REQUIRE(supplement.has_value());
    for (uint32_t eventId = 53; eventId <= 61; ++eventId)
    {
        CAPTURE(eventId);
        const bool hasOverride = eventId == 55 || eventId == 56 || eventId == 60 || eventId == 61;
        const std::string &script = hasOverride ? *supplement : *generated;
        const std::string handler = (hasOverride ? "ReplaceMapEvent(" : "RegisterEvent(")
            + std::to_string(eventId) + ",";
        const size_t handlerStart = script.find(handler);
        REQUIRE_NE(handlerStart, std::string::npos);
        const size_t handlerEnd = script.find("end, \"Computer Terminal\")", handlerStart);
        REQUIRE_NE(handlerEnd, std::string::npos);
        const std::string prefix = eventId == 61 ? "evt.SimpleMessage(" : "evt.SetMessage(";
        const size_t messageStart = script.find(prefix, handlerStart);
        REQUIRE_LT(messageStart, handlerEnd);
        const size_t messageEnd = script.find(")", messageStart + prefix.size());
        REQUIRE_LT(messageEnd, handlerEnd);
        // Decode the quoted Lua fragments, including the concatenated training message.
        std::string message;
        bool inString = false;
        for (size_t offset = messageStart + prefix.size(); offset < messageEnd; ++offset)
        {
            const char character = script[offset];
            if (inString && character == '\\')
            {
                REQUIRE_LT(offset + 1, messageEnd);
                message += script[++offset];
            }
            else if (character == '"')
            {
                inString = !inString;
            }
            else if (inString)
            {
                message += character;
            }
        }
        REQUIRE_FALSE(message.empty());
        CHECK_FALSE(inString);
        const std::string translated = catalog.translateText(message);
        CHECK_NE(translated, message);
        CHECK_EQ(translated.find("�"), std::string::npos);
    }
}

TEST_CASE("Russian blaster inspection covers every rank and the scaling damage explanation")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::GameDataLoader data;
    data.setLanguage("ru");
    REQUIRE(data.loadCommonForGameplay(assets));
    const Game::SkillInspectEntry *pBlaster = data.getCharacterInspectTable().getSkill("Blaster");
    REQUIRE(pBlaster != nullptr);
    CHECK_NE(pBlaster->description.find("Бластеры"), std::string::npos);
    CHECK_EQ(pBlaster->normalDescription, "Навык прибавляется к атаке");
    CHECK_EQ(pBlaster->expertDescription, "Двойная прибавка навыка к атаке");
    CHECK_EQ(pBlaster->masterDescription, "Тройная прибавка навыка к атаке");
    CHECK_EQ(pBlaster->grandmasterDescription, "Пятикратная прибавка навыка к атаке");

    const Game::LocalizationCatalog &catalog = data.getLocalizationCatalog();
    const std::string scalingDescription =
        "Blaster weapons provide an accurate ranged attack. With scaling damage enabled, only "
        "Grandmaster rank adds damage per skill point.";
    const std::string translated = catalog.translateText(scalingDescription);
    CHECK_NE(translated, scalingDescription);
    CHECK_NE(translated.find("Великий мастер"), std::string::npos);
    CHECK_EQ(catalog.translateText("+1 damage per skill point"), "+1 к урону за каждый пункт навыка");
    CHECK_EQ(catalog.translateText("Normal"), "Новичок");
    CHECK_EQ(catalog.translateText("Expert"), "Эксперт");
    CHECK_EQ(catalog.translateText("Master"), "Мастер");
    CHECK_EQ(catalog.translateText("Grandmaster"), "Великий мастер");

    Game::LocalizationCatalog english;
    REQUIRE(english.load(assets, "en"));
    CHECK_EQ(english.translateText(scalingDescription), scalingDescription);
    CHECK_EQ(english.translateText("+1 damage per skill point"), "+1 damage per skill point");
}

TEST_CASE("Event input accepts original and Russian answers without changing answer branches")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assets, "ru"));

    for (const std::string &input : {"Да", "да", "ДА", " дА \t", "Yes", "YES", " yes "})
    {
        CAPTURE(input);
        CHECK(catalog.matchesAnswer("Yes", input));
        CHECK_FALSE(catalog.matchesAnswer("Y", input));
    }
    for (const std::string &input : {"Д", "д", "Y", "y"})
    {
        CAPTURE(input);
        CHECK(catalog.matchesAnswer("Y", input));
    }
    for (const std::string &input : {"Нет", "НЕТ", "Н", "No", "", " \t", "Да нет", "Yes!"})
    {
        CAPTURE(input);
        CHECK_FALSE(catalog.matchesAnswer("Yes", input));
        CHECK_FALSE(catalog.matchesAnswer("Y", input));
    }
    CHECK(catalog.matchesAnswer("No", "НЕТ"));
    CHECK(catalog.matchesAnswer("N", "н"));
    CHECK_FALSE(catalog.matchesAnswer("", ""));
    catalog.addExactTranslation("fir tree", "ёлка");
    CHECK(catalog.matchesAnswer("fir tree", "ЁЛКА"));
    CHECK_FALSE(catalog.matchesAnswer("fir tree", "елка"));

    CHECK_EQ(catalog.translate("Guardian of Kriegspire"), "Хранитель Кригспайра");
    CHECK_EQ(catalog.translate("Curator of Kriegspire"), "Куратор Кригспайра");
    CHECK_EQ(catalog.translate("Accept (Yes/No)?"), "Согласны (Да/Нет)?");
    CHECK_EQ(catalog.translateText("Answer: _"), "Ответ: _");
    CHECK_EQ(catalog.format("Answer: {answer}_", {{"answer", "Да"}}), "Ответ: Да_");
    CHECK_EQ(catalog.format("Answer: {answer}_", {{"answer", "Yes"}}), "Ответ: Yes_");

    REQUIRE(catalog.load(assets, "en"));
    CHECK(catalog.matchesAnswer("Yes", " YES "));
    CHECK_FALSE(catalog.matchesAnswer("Yes", "Да"));
    CHECK_EQ(catalog.format("Answer: {answer}_", {{"answer", "Yes"}}), "Answer: Yes_");
}

TEST_CASE("NPC time of day substitution follows the dialogue language at hour boundaries")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assets, "ru"));
    const Game::NpcEntry npc = {};
    const Game::MergedNpcProfessionEntry profession = {};

    for (const std::pair<float, std::string> &sample : {
        std::pair<float, std::string>{0.0f, "утро"}, {8.0f, "утро"},
        {9.0f, "день"}, {16.0f, "день"}, {17.0f, "вечер"}, {23.0f, "вечер"}, {24.0f, "утро"}})
    {
        CAPTURE(sample.first);
        CHECK_EQ(Game::formatNpcProfessionText(
            "%05", npc, profession, nullptr, 0, std::nullopt, sample.first * 60.0f, &catalog), sample.second);
    }

    REQUIRE(catalog.load(assets, "en"));
    for (const std::pair<float, std::string> &sample : {
        std::pair<float, std::string>{8.0f, "morning"}, {16.0f, "afternoon"}, {23.0f, "evening"}})
    {
        CAPTURE(sample.first);
        CHECK_EQ(Game::formatNpcProfessionText(
            "%05", npc, profession, nullptr, 0, std::nullopt, sample.first * 60.0f, &catalog), sample.second);
        CHECK_EQ(Game::formatNpcProfessionText(
            "%05", npc, profession, nullptr, 0, std::nullopt, sample.first * 60.0f), sample.second);
    }
}

TEST_CASE("MM6 promotion dialogue translates complete replies for all six class families")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::GameDataLoader data;
    data.setLanguage("ru");
    REQUIRE(data.loadCommonForGameplay(assets));

    // Compare against complete authored translations, including legacy unquoted continuation rows.
    const std::optional<std::string> overlay = assets.readTextFile("data_tables/ru/npc_topic_text.txt.overlay.yml");
    const std::optional<std::string> source = assets.readTextFile("data_tables/npc_topic_text.txt");
    REQUIRE(overlay.has_value());
    REQUIRE(source.has_value());
    const std::optional<Engine::TextTable> parsed = Engine::TextTable::parseTabSeparated(*source);
    REQUIRE(parsed.has_value());
    std::vector<std::vector<std::string>> expectedRows;
    for (size_t index = 0; index < parsed->getRowCount(); ++index)
    {
        expectedRows.push_back(parsed->getRow(index));
    }
    expectedRows = Game::NpcDialogTable::normalizeTextRows(expectedRows);
    std::string errorMessage;
    REQUIRE(Game::applyLocalizedTableOverlay(*overlay, expectedRows, errorMessage));
    Game::NpcDialogTable expected;
    REQUIRE(expected.loadTextsFromRows(expectedRows));
    for (const std::pair<uint32_t, uint32_t> range : {
        std::pair<uint32_t, uint32_t>{1711, 1716}, {1738, 1744}, {1759, 1765},
        {1773, 1779}, {1790, 1795}, {1801, 1807}})
    {
        for (uint32_t id = range.first; id <= range.second; ++id)
        {
            CAPTURE(id);
            const std::optional<std::string> translation = expected.getText(id);
            REQUIRE(translation.has_value());
            REQUIRE_FALSE(translation->empty());
            const std::optional<std::string> actual = data.getNpcDialogTable().getText(id);
            REQUIRE(actual.has_value());
            CHECK_EQ(*actual, *translation);
        }
    }

    const Game::LocalizationCatalog &catalog = data.getLocalizationCatalog();
    CHECK_EQ(catalog.translate("Sorcerer"), "Колдун");
    CHECK_EQ(catalog.translate("Wizard"), "Волшебник");
    CHECK_EQ(catalog.translate("Master Wizard"), "Архимаг");
    CHECK_EQ(catalog.translate("Arch Mage"), "Архимаг Света");
    CHECK_EQ(catalog.translate("Dark ArchMage"), "Архимаг Тьмы");
    const std::string repeatPrefix =
        "Your party has already completed this quest. Eligible companions are promoted to ";
    for (const std::string &className : {"Crusader", "Hero", "Wizard", "Master Wizard", "Cavalier", "Champion",
        "Priest", "High Priest", "Great Druid", "Arch Druid", "Warrior Mage", "Master Archer"})
    {
        CAPTURE(className);
        CHECK_EQ(catalog.translateText(repeatPrefix + className + "."),
            "Ваша группа уже выполнила это задание. "
            "Соответствующие требованиям спутники получают повышение. Новый класс: "
                + catalog.translate(className) + ".");
    }
}

TEST_CASE("MM6 cobra egg replies translate legacy Lua text with and without an egg")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::GameDataLoader data;
    data.setLanguage("ru");
    REQUIRE(data.loadCommonForGameplay(assets));

    // Read the generated handler so the check includes its original legacy punctuation bytes.
    const std::optional<std::string> globalLua = assets.readTextFile("events/Global.lua");
    REQUIRE(globalLua.has_value());
    const size_t handlerStart = globalLua->find("RegisterGlobalEvent(1625,");
    REQUIRE_NE(handlerStart, std::string::npos);
    const size_t handlerEnd = globalLua->find("RegisterGlobalEvent(", handlerStart + 1);
    REQUIRE_NE(handlerEnd, std::string::npos);
    size_t offset = handlerStart;
    for (uint32_t textId : {2020u, 2019u})
    {
        const std::string prefix = "evt.SetMessage(\"";
        const size_t messageStart = globalLua->find(prefix, offset);
        REQUIRE_LT(messageStart, handlerEnd);
        const size_t textStart = messageStart + prefix.size();
        const size_t textEnd = globalLua->find("\")", textStart);
        REQUIRE_LT(textEnd, handlerEnd);
        std::string message = globalLua->substr(textStart, textEnd - textStart);
        size_t newline = 0;
        while ((newline = message.find("\\n", newline)) != std::string::npos)
        {
            message.replace(newline, 2, "\n");
            ++newline;
        }
        CAPTURE(textId);
        const std::optional<std::string> expected = data.getNpcDialogTable().getText(textId);
        REQUIRE(expected.has_value());
        CHECK_NE(*expected, message);
        CHECK_NE(expected->find("кобр"), std::string::npos);
        CHECK_EQ(data.getLocalizationCatalog().translateText(message), *expected);
        offset = textEnd + 2;
    }
}

TEST_CASE("Russian and English game tables resolve all implemented monster spells")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));

    for (const std::string language : {"ru", "en"})
    {
        CAPTURE(language);
        Game::GameDataLoader data;
        data.setLanguage(language);
        REQUIRE(data.loadCommonForGameplay(assets));
        const Game::SpellTable &spells = data.getSpellTable();

        for (const auto &[id, monster] : data.getMonsterTable().statsEntries())
        {
            CAPTURE(id);
            for (const std::string &name : {monster.spell1Name, monster.spell2Name})
            {
                if (name.empty() || Game::isKnownUnsupportedMonsterSpellName(name))
                {
                    continue;
                }
                CAPTURE(name);
                const Game::SpellEntry *pSpell = spells.findByName(name);
                REQUIRE(pSpell != nullptr);
                CHECK_FALSE(pSpell->normalizedName.empty());
            }
        }

        const Game::SpellEntry *pLightning = spells.findByName("lightning bolt");
        const Game::SpellEntry *pFireBolt = spells.findByName("fire bolt");
        REQUIRE(pLightning != nullptr);
        REQUIRE(pFireBolt != nullptr);
        CHECK_EQ(pLightning->normalizedName, "lightning bolt");
        CHECK_EQ(pFireBolt->normalizedName, "fire bolt");
        CHECK_EQ(pLightning->displayObjectId, 2060);
        CHECK_EQ(pFireBolt->displayObjectId, 1010);
        CHECK_EQ(pLightning->name, language == "ru" ? "Молния" : "Lightning Bolt");
        CHECK_EQ(pFireBolt->name, language == "ru" ? "Огненная стрела" : "Fire Bolt");
    }
}

TEST_CASE("Saved teacher map notes translate every skill and mastery in the selected language")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));

    for (const std::string &skill : Game::allCanonicalSkillNames())
    {
        const std::string skillLabel = Game::displaySkillName(skill);
        REQUIRE(catalog.translate(skillLabel) != skillLabel);
        for (const std::string &mastery : {"Expert", "Master", "Grandmaster"})
        {
            const std::string savedNote = skillLabel + " - " + mastery;
            CHECK_EQ(catalog.translateText(savedNote),
                catalog.translate(skillLabel) + " — " + catalog.translate(mastery));
        }
    }

    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.translateText("Sword - Expert"), "Sword - Expert");
    CHECK_EQ(catalog.translateText("Fire Magic - Grandmaster"), "Fire Magic - Grandmaster");
}

TEST_CASE("Russian character experience inspection translates shortfall and available training")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));

    Game::Character character = {};
    character.name = "Ариэль";
    character.level = 4;
    character.experience = 9500;
    const std::string shortfall = Game::GameMechanics::buildExperienceInspectSupplement(character);
    CHECK_EQ(catalog.translateText(shortfall), "Ариэль: до уровня 5 не хватает опыта: 500.");

    character.experience = 21000;
    const std::string availableTraining = Game::GameMechanics::buildExperienceInspectSupplement(character);
    CHECK_EQ(catalog.translateText(availableTraining), "Ариэль: обучение доступно до уровня 7.");

    character.name.clear();
    CHECK_EQ(catalog.translateText(Game::GameMechanics::buildExperienceInspectSupplement(character)),
        "Этот персонаж: обучение доступно до уровня 7.");

    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.translateText(shortfall), shortfall);
    CHECK_EQ(catalog.translateText(availableTraining), availableTraining);
}

TEST_CASE("Mastery teacher localization replaces whole multiline replies and translates training actions")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    const std::optional<std::string> source = assetFileSystem.readTextFile("data_tables/npc_topic_text.txt");
    const std::optional<std::string> overlay =
        assetFileSystem.readTextFile("data_tables/ru/npc_topic_text.txt.overlay.yml");
    REQUIRE(source.has_value());
    REQUIRE(overlay.has_value());
    const std::optional<Engine::TextTable> parsed = Engine::TextTable::parseTabSeparated(*source);
    REQUIRE(parsed.has_value());
    std::vector<std::vector<std::string>> rows;
    for (size_t index = 0; index < parsed->getRowCount(); ++index)
    {
        rows.push_back(parsed->getRow(index));
    }
    Game::NpcDialogTable english;
    REQUIRE(english.loadTextsFromRows(rows));
    rows = Game::NpcDialogTable::normalizeTextRows(rows);
    Game::NpcDialogTable normalizedEnglish;
    REQUIRE(normalizedEnglish.loadTextsFromRows(rows));
    for (const std::vector<std::string> &row : rows)
    {
        const uint32_t id = std::stoul(row[0]);
        CHECK_EQ(normalizedEnglish.getText(id), english.getText(id));
    }
    std::string errorMessage;
    REQUIRE(Game::applyLocalizedTableOverlay(*overlay, rows, errorMessage));
    Game::NpcDialogTable russian;
    REQUIRE(russian.loadTextsFromRows(rows));
    const std::optional<std::string> swordText = russian.getText(1894);
    REQUIRE(swordText.has_value());
    CHECK_EQ(*swordText,
        "Мои уроки помогут вам улучшить технику владения мечом.\n"
        "Чтобы мои советы принесли вам пользу, вы должны уже обладать навыками среднего уровня (4-й ранг).\n"
        "Я беру 2000 золотых с каждого ученика.");
    const std::optional<std::string> staffText = russian.getText(1892);
    REQUIRE(staffText.has_value());
    CHECK_EQ(staffText->find("All you need"), std::string::npos);
    CHECK_EQ(staffText->find("2000"), staffText->rfind("2000"));

    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));
    Game::GameplayUiController controller;
    controller.bindLocalizationCatalog(&catalog);
    Game::EventDialogContent content;
    for (const std::string &mastery : {"Expert", "Master", "Grandmaster"})
    {
        Game::EventDialogAction action;
        action.label = "Become " + mastery + " in Sword for 2000 gold";
        content.actions.push_back(action);
    }
    controller.setEventDialogContent(content);
    CHECK_EQ(controller.eventDialog().content.actions[0].label, "Обучение: Меч — Эксперт (2000 золота)");
    CHECK_EQ(controller.eventDialog().content.actions[1].label, "Обучение: Меч — Мастер (2000 золота)");
    CHECK_EQ(controller.eventDialog().content.actions[2].label, "Обучение: Меч — Великий мастер (2000 золота)");
    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.translateText(content.actions[0].label), content.actions[0].label);
}

TEST_CASE("Mastery teacher requirements localize promotion alternatives and class restrictions")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assets, "ru"));

    const std::string prefix = "You have to be promoted to ";
    const std::string suffix = " to learn this skill.";
    const std::string russianPrefix =
        "Чтобы освоить этот навык, вам необходимо получить повышение. Требуемый класс: ";
    CHECK_EQ(catalog.translateText(prefix + "Wizard" + suffix), russianPrefix + "Волшебник.");
    CHECK_EQ(catalog.translateText(prefix + "Arch Mage or Lich" + suffix), russianPrefix + "Архимаг Света или Лич.");
    CHECK_EQ(catalog.translateText(prefix + "Arch Mage, Dark ArchMage or Master Wizard" + suffix),
        russianPrefix + "Архимаг Света, Архимаг Тьмы или Архимаг.");
    CHECK_EQ(catalog.translateText(prefix + "High Priest or Priest of the Light" + suffix),
        russianPrefix + catalog.translate("High Priest") + " или " + catalog.translate("Priest of the Light") + ".");
    CHECK_EQ(catalog.translateText(prefix + "Wizard, Arch Mage, Lich or Master Wizard" + suffix),
        russianPrefix + "Волшебник, Архимаг Света, Лич или Архимаг.");
    CHECK_EQ(catalog.translateText("This skill level can not be learned by the Wizard class."),
        "Этот уровень навыка недоступен для класса «Волшебник».");
    for (const std::string &message : {
        "You must have at least 50 base Intellect to learn Master Learning.",
        "You must have at least 50 base Personality to learn Master Merchant.",
        "You must have at least 50 base Endurance to learn Master Bodybuilding.",
        "The requirements for this training are unmet.",
        "This character does not know that skill.",
        "This character already knows that mastery."})
    {
        CAPTURE(message);
        CHECK_NE(catalog.translateText(message), message);
    }

    REQUIRE(catalog.load(assets, "en"));
    CHECK_EQ(catalog.translateText(prefix + "Wizard" + suffix), prefix + "Wizard" + suffix);
    CHECK_EQ(catalog.translateText(prefix + "Arch Mage or Lich" + suffix), prefix + "Arch Mage or Lich" + suffix);
}

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

TEST_CASE("Russian localization translates combat status messages in the gameplay UI")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));
    Game::GameplayUiController controller;
    controller.bindLocalizationCatalog(&catalog);

    Game::CharacterAttackResult attack = {};
    attack.mode = Game::CharacterAttackMode::Melee;
    attack.canAttack = true;
    attack.hit = true;
    attack.damage = 48;
    const std::string attacker = "Ариэль";
    const std::string target = "Гоблин";
    const auto checkStatus = [&](bool killed, const std::string &expected)
    {
        controller.setStatusBarEvent(Game::GameplayCombatController::formatPartyAttackStatusText(
            attacker, target, attack, killed, 12));
        CHECK_EQ(controller.statusBar().eventText, expected);
    };
    checkStatus(false, "Ариэль: нанесённый урон: 12; цель: Гоблин");
    checkStatus(true, "Ариэль: цель «Гоблин» уничтожена, урон: 12");
    attack.mode = Game::CharacterAttackMode::Bow;
    checkStatus(false, "Ариэль: выстрел по цели «Гоблин», урон: 12");
    attack.paralyzeTarget = true;
    checkStatus(false, "Ариэль: цель «Гоблин» парализована");
    attack.paralyzeTarget = false;
    attack.stunTarget = true;
    checkStatus(false, "Ариэль: цель «Гоблин» оглушена");

    controller.setStatusBarEvent("Ариэль shoots Гоблин for 1 points");
    CHECK_EQ(controller.statusBar().eventText, "Ариэль: выстрел по цели «Гоблин», урон: 1");
    controller.setStatusBarEvent("Ариэль inflicts 0 points killing Гоблин");
    CHECK_EQ(controller.statusBar().eventText, "Ариэль: цель «Гоблин» уничтожена, урон: 0");
    controller.setStatusBarEvent("Ариэль evades damage");
    CHECK_EQ(controller.statusBar().eventText, "Ариэль уклоняется от урона");
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
        for (const std::string &mastery : {"Expert", "Master", "Grandmaster"})
        {
            CHECK_EQ(catalog.translateText(mastery + ": " + displayName),
                catalog.translate(mastery) + ": " + catalog.translate(displayName));
        }
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

TEST_CASE("Russian guild shop purchase phrases preserve book names and prices")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));

    const std::string itemName = "Исцеление ран";
    const std::vector<std::string> phrases = {
        "An excellent choice! This " + itemName
            + " is of the finest quality. I am willing to virtually give it away for 123 gold.",
        "I try to sell things like this " + itemName
            + " for 456 gold. But we both know it's really worth 123. So that's my price.",
        "Ordinarily I sell things like this " + itemName
            + " for 456 gold. But you drive a hard bargain-- I'll sell it to you for 123."
    };
    for (const std::string &phrase : phrases)
    {
        const std::string localized = catalog.translateText(phrase);
        CHECK_NE(localized, phrase);
        CHECK_NE(localized.find(itemName), std::string::npos);
        CHECK_NE(localized.find("123"), std::string::npos);
        CHECK_EQ(localized.find('{'), std::string::npos);
    }
    CHECK_EQ(catalog.translateText(phrases.front()),
        "Отличный выбор! Предмет «Исцеление ран» отличается высочайшим качеством. "
        "Я готов практически отдать его за 123 золота.");

    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.translateText(phrases.front()), phrases.front());
}

TEST_CASE("Russian item overlay translates every MM6 spellbook description")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    const std::optional<std::string> source = assetFileSystem.readTextFile("data_tables/items.txt");
    const std::optional<std::string> overlay =
        assetFileSystem.readTextFile("data_tables/ru/items.txt.overlay.yml");
    REQUIRE(source.has_value());
    REQUIRE(overlay.has_value());
    const std::optional<Engine::TextTable> table = Engine::TextTable::parseTabSeparated(*source);
    REQUIRE(table.has_value());
    std::vector<std::vector<std::string>> rows;
    for (size_t index = 0; index < table->getRowCount(); ++index)
    {
        rows.push_back(table->getRow(index));
    }
    std::string errorMessage;
    REQUIRE(Game::applyLocalizedTableOverlay(*overlay, rows, errorMessage));
    size_t bookCount = 0;
    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() > 20 && row[4] == "Book" && row[20] == "World:mm6")
        {
            INFO(row[0]);
            CHECK_EQ(row[10], "Книга заклинаний");
            CHECK(row[16].starts_with("Книга заклинаний."));
            ++bookCount;
        }
    }
    CHECK_EQ(bookCount, 117);
}

TEST_CASE("House service dialogs localize menus and priced skill lessons")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));

    Game::GameplayUiController controller;
    controller.bindLocalizationCatalog(&catalog);
    Game::EventDialogContent content;
    content.isHouseDialog = true;
    content.title = "Equipment";
    content.lines = {"Balance: 1234"};
    for (const std::string &label : {"Buy Standard", "Buy Special", "Display Equipment", "Learn Skills",
             "Buy Spellbooks", "Sell", "Identify", "Repair", "Deposit", "Withdraw", "Rules", "Victory Conditions",
             "Play", "Play Arcomage", "Pay Fine", "Bounty Hunt", "Rent room for 17 gold",
             "Fill packs to 14 days for 42 gold", "Train to level 5 for 100 gold",
             "2 days to Дейя for 55 gold"})
    {
        Game::EventDialogAction action;
        action.label = label;
        content.actions.push_back(action);
    }
    Game::EventDialogAction lesson;
    lesson.label = "Learn Leather Armor for 500 gold";
    lesson.argument = "LeatherArmor";
    lesson.disabledReason = "You must be a member of this guild to study here.";
    content.actions.push_back(lesson);
    controller.setEventDialogContent(content);
    const Game::EventDialogContent &localized = controller.eventDialog().content;
    CHECK_EQ(localized.title, "Снаряжение");
    CHECK_EQ(localized.lines.front(), "Остаток на счёте: 1234");
    REQUIRE_EQ(localized.actions.size(), content.actions.size());
    for (size_t index = 0; index < content.actions.size(); ++index)
    {
        INFO(content.actions[index].label);
        CHECK_NE(localized.actions[index].label, content.actions[index].label);
    }
    CHECK_EQ(localized.actions.back().label, "Освоить Кожаные доспехи за 500 золота");
    CHECK_EQ(localized.actions.back().argument, "LeatherArmor");
    CHECK_NE(localized.actions.back().disabledReason, lesson.disabledReason);
    CHECK_EQ(localized.actions[localized.actions.size() - 2].label, "Дейя — 2 дн. за 55 золота");
    CHECK_EQ(catalog.translateText("1 day to Дейя for 55 gold"), "Дейя — 1 дн. за 55 золота");
    CHECK_EQ(catalog.translateText("Learn Unknown Skill for 501 gold"), "Освоить Unknown Skill за 501 золота");
    CHECK_EQ(catalog.translateText("Train to level 7 for 235 gold"), "Обучиться до уровня 7 за 235 золота");
}

TEST_CASE("Alchemy bench localizes dynamic recipes previews and brewing results")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::LocalizationCatalog catalog;
    REQUIRE(catalog.load(assetFileSystem, "ru"));

    CHECK_EQ(catalog.translateText("BOTTLE + REAGENT"), "БУТЫЛКА + РЕАГЕНТ");
    CHECK_EQ(catalog.translateText("GRANDMASTER"), "ВЕЛИКИЙ МАСТЕР");
    CHECK_EQ(catalog.translateText("??? (17 undiscovered)"), "??? (не открыто: 17)");
    CHECK_EQ(catalog.translateText("12 / 40 known"), "Известно: 12 / 40");
    CHECK_EQ(catalog.translateText("Alchemist: Алиса - Grandmaster 10 (best in party)"),
        "Алхимик: Алиса — Великий мастер 10 (лучший в отряде)");
    CHECK_EQ(catalog.translateText("Needs Master Alchemy; Алиса has Expert."),
        "Требуется алхимия: Мастер; у персонажа Алиса: Эксперт.");
    CHECK_EQ(catalog.translateText("power ~25"), "сила ~25");
    CHECK_EQ(catalog.translateText("needs Grandmaster"), "требуется: Великий мастер");
    CHECK_EQ(catalog.translateText("Brewed x3"), "Сварено x3");
    CHECK_EQ(catalog.translateText("Uses: 2 Красное зелье."), "Расходуется: 2 Красное зелье.");
    CHECK_EQ(catalog.translateText("Brews first: 1 Синее зелье."), "Сначала сварить: 1 Синее зелье.");
    CHECK_EQ(catalog.translateText("Brewed Красное зелье (power 20, 3 steps)"),
        "Сварено: Красное зелье (сила 20, шагов: 3)");
    CHECK_EQ(catalog.translateText("Brewed 2 x Красное зелье (1 step)"),
        "Сварено: 2 × Красное зелье (шагов: 1)");

    Game::GameplayUiController controller;
    controller.bindLocalizationCatalog(&catalog);
    controller.setStatusBarEvent("Discovered: Красное зелье!");
    CHECK_EQ(controller.statusBar().eventText, "Открыт рецепт: Красное зелье!");

    REQUIRE(catalog.load(assetFileSystem, "en"));
    CHECK_EQ(catalog.translateText("Brewed Красное зелье (power 20, 3 steps)"),
        "Brewed Красное зелье (power 20, 3 steps)");
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
