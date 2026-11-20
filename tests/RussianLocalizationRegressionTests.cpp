#include "engine/AssetFileSystem.h"
#include "engine/Localization.h"

#include <doctest/doctest.h>
#include <filesystem>
#include <string>

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
