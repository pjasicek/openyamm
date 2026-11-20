#include "engine/AssetFileSystem.h"
#include "engine/Localization.h"
#include "engine/TextTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/SpellTable.h"

#include <doctest/doctest.h>
#include <filesystem>
#include <string>
#include <vector>

using namespace OpenYAMM;

namespace
{
struct LanguageReset
{
    const Engine::AssetFileSystem &assets;
    explicit LanguageReset(const Engine::AssetFileSystem &source) : assets(source) {}
    ~LanguageReset()
    {
        Engine::activateLanguage(assets, "en");
        Engine::setLocalizationWorld("");
    }
};
}

TEST_CASE("Russian PO packs retain playtested object captions and English fallback")
{
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "mm8"));
    LanguageReset reset(assets);
    REQUIRE(Engine::activateLanguage(assets, "ru"));
    CHECK_EQ(Engine::localize("Camp Fire"), "Костёр");
    CHECK_EQ(Engine::localize("Food Bowl"), "Миска с едой");
    CHECK_EQ(Engine::localize("Red Barrel"), "Красная бочка");
    CHECK_EQ(Engine::localize("Would you like to rest?"), "Хотите передохнуть?");
    CHECK_EQ(Engine::localizeKnown("custom untranslated caption"), "custom untranslated caption");
    REQUIRE(Engine::activateLanguage(assets, "en"));
    CHECK_EQ(Engine::localize("Camp Fire"), "Camp Fire");
}

TEST_CASE("MM6 Control Center terminals translate their exact runtime messages")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    LanguageReset reset(assets);
    REQUIRE(Engine::activateLanguage(assets, "ru"));
    Engine::setLocalizationWorld("mm6");

    CHECK_EQ(Engine::localize("Computer Terminal"), "Компьютерный терминал");
    CHECK_EQ(Engine::localize("Storage Container"), "Контейнер для хранения");
    CHECK_EQ(Engine::localize("It's a short circuit!"), "Это короткое замыкание!");

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
        const std::string translated = Engine::localize(message);
        CHECK_NE(translated, message);
        CHECK_EQ(translated.find("�"), std::string::npos);
    }
}

TEST_CASE("Russian display localization preserves canonical character inspection tables")
{
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    LanguageReset reset(assets);
    REQUIRE(Engine::activateLanguage(assets, "ru"));
    const auto rows = [&assets](const std::string &name)
    {
        const std::optional<std::string> text = assets.readTextFile("engine/data_tables/english/" + name);
        REQUIRE(text.has_value());
        const std::optional<Engine::TextTable> table = Engine::TextTable::parseTabSeparated(*text);
        REQUIRE(table.has_value());
        std::vector<std::vector<std::string>> result;
        for (size_t index = 0; index < table->getRowCount(); ++index)
        {
            result.push_back(table->getRow(index));
        }
        return result;
    };
    Game::CharacterInspectTable table;
    REQUIRE(table.loadStatRows(rows("stats.txt")));
    REQUIRE(table.loadSkillRows(rows("skill_des.txt")));
    REQUIRE(table.loadClassRows(rows("class.txt")));
    const Game::StatInspectEntry *pMight = table.getStat("Might");
    const Game::SkillInspectEntry *pStaff = table.getSkill("Staff");
    const Game::ClassInspectEntry *pKnight = table.getClass("Knight");
    REQUIRE(pMight != nullptr);
    REQUIRE(pStaff != nullptr);
    REQUIRE(pKnight != nullptr);
    CHECK_EQ(pMight->name, "Might");
    CHECK_EQ(pStaff->name, "Staff");
    CHECK_EQ(pKnight->name, "Knight");
    CHECK_NE(Engine::localize(pMight->description), pMight->description);
    CHECK_NE(Engine::localize(pStaff->description), pStaff->description);
    CHECK_NE(Engine::localize(pKnight->description), pKnight->description);
    CHECK_EQ(table.getStat("Might"), pMight);
    CHECK_EQ(table.getSkill("Staff"), pStaff);
    CHECK_EQ(table.getClass("Knight"), pKnight);
}

TEST_CASE("Russian spell display leaves canonical monster spell lookup unchanged")
{
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    LanguageReset reset(assets);
    REQUIRE(Engine::activateLanguage(assets, "ru"));
    Game::SpellTable table;
    REQUIRE(table.loadFromRows({
        {"2", "2", "Fire Bolt", "Fire", "Fire Bolt", "Fire damage"},
        {"18", "7", "Lightning Bolt", "Air", "Lightning", "Air damage"}}));
    const Game::SpellEntry *pLightning = table.findByName("lightning bolt");
    REQUIRE(pLightning != nullptr);
    CHECK_EQ(pLightning->id, 18);
    CHECK_EQ(pLightning->name, "Lightning Bolt");
    CHECK_EQ(Engine::localize(pLightning->name), "Молния");
    CHECK_EQ(table.findByName("LightningBolt"), pLightning);
    CHECK(table.findByName("Молния") == nullptr);
    REQUIRE(Engine::activateLanguage(assets, "en"));
    CHECK_EQ(Engine::localize(pLightning->name), "Lightning Bolt");
    CHECK_EQ(table.findByName("lightning bolt"), pLightning);
}
