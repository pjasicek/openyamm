#include "engine/AssetFileSystem.h"
#include "engine/TextCatalogue.h"

#include <doctest/doctest.h>

#include <chrono>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

namespace
{
using namespace OpenYAMM;
using Engine::encodeCodePageText;
using Engine::formatDisplayText;
using Engine::localizeDisplayText;

std::string cyrillic(const std::string &utf8)
{
    return encodeCodePageText(utf8, "windows-1251");
}

// A game folder with a Russian language (engine/localization/ru) whose catalogue the tests write.
struct CatalogueFixture
{
    std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("openyamm_catalogue_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    Engine::AssetFileSystem assets;

    explicit CatalogueFixture(const std::string &world = "mm8")
    {
        std::filesystem::create_directories(root / "engine/localization/ru");
        std::filesystem::create_directories(root / "worlds" / world);
        std::ofstream(root / "engine/localization/ru/language.yml") << "name: Russian\nencoding: windows-1251\n";
        REQUIRE(assets.initialize(root, root, Engine::AssetScaleTier::X1, world));
    }

    ~CatalogueFixture()
    {
        Engine::loadTextCatalogue(assets, Engine::EnglishLanguageId);
        assets.shutdown();
        std::filesystem::remove_all(root);
    }

    void write(const std::string &text, const std::filesystem::path &path = "engine/localization/ru/strings.tsv")
    {
        std::filesystem::create_directories((root / path).parent_path());
        std::ofstream(root / path, std::ios::binary) << text;
        assets.refreshLookupCache();
    }

    void load(const std::string &language = "ru")
    {
        Engine::loadTextCatalogue(assets, language);
    }
};
}

TEST_CASE("text catalogue draws Cyrillic and Yo in their windows-1251 bytes")
{
    CatalogueFixture fixture;
    fixture.write("Name\tИмя\nYo\tЁё\n");
    fixture.load();
    CHECK(Engine::hasTextCatalogue());
    CHECK(Engine::interfaceLanguageId() == "ru");
    CHECK(Engine::interfaceTextEncoding() == "windows-1251");
    CHECK(localizeDisplayText("Name") == std::string("\xc8\xec\xff"));
    CHECK(localizeDisplayText("Yo") == std::string("\xa8\xb8"));
    CHECK(localizeDisplayText("out01.odm") == "out01.odm");
}

TEST_CASE("a language's catalogue files load in name order, a later file's entry winning")
{
    CatalogueFixture fixture;
    fixture.write("Name\tИмя\nTree\tДерево\n");
    fixture.write("Tree\tДрево\nWell\tКолодец\n", "engine/localization/ru/zz_game_text.tsv");
    fixture.write("Well\tИсточник\n", "engine/localization/ru/notes.txt");
    fixture.load();
    CHECK(localizeDisplayText("Name") == cyrillic("Имя"));
    CHECK(localizeDisplayText("Tree") == cyrillic("Древо"));
    CHECK(localizeDisplayText("Well") == cyrillic("Колодец"));
}

TEST_CASE("text catalogue keeps quoted multiline entries whole")
{
    CatalogueFixture fixture;
    fixture.write("\"Hello\ntraveller\"\t\"Привет\nпутник\"\n");
    fixture.load();
    CHECK(localizeDisplayText("Hello\ntraveller") == cyrillic("Привет\nпутник"));
}

TEST_CASE("a malformed text catalogue throws and keeps the loaded one")
{
    CatalogueFixture fixture;
    fixture.write("Name\tИмя\n");
    fixture.load();
    fixture.write("Name\t\xe0\x90\x90\n");
    CHECK_THROWS_AS(fixture.load(), std::runtime_error);
    CHECK(localizeDisplayText("Name") == std::string("\xc8\xec\xff"));
    // A character windows-1251 lacks, and a UTF-16 surrogate.
    fixture.write("Name\t\xef\xbf\xbf\n");
    CHECK_THROWS_AS(fixture.load(), std::runtime_error);
    fixture.write("Name\t\xed\xa0\x80\n");
    CHECK_THROWS_AS(fixture.load(), std::runtime_error);
}

TEST_CASE("English and missing languages leave the text as it is")
{
    CatalogueFixture fixture;
    fixture.write("New Game\tНовая игра\n");
    fixture.load(Engine::EnglishLanguageId);
    CHECK_FALSE(Engine::hasTextCatalogue());
    CHECK(Engine::interfaceTextEncoding() == "windows-1252");
    CHECK(localizeDisplayText("New Game") == "New Game");
    fixture.load("de");
    CHECK(Engine::interfaceLanguageId() == Engine::EnglishLanguageId);
    CHECK(localizeDisplayText("New Game") == "New Game");
}

TEST_CASE("the installed interface languages follow English")
{
    CatalogueFixture fixture;
    const std::vector<Engine::InterfaceLanguage> languages = Engine::availableInterfaceLanguages(fixture.assets);
    REQUIRE(languages.size() == 2);
    CHECK(languages[0].id == "en");
    CHECK(languages[1].id == "ru");
    CHECK(languages[1].name == "Russian");
    CHECK(languages[1].encoding == "windows-1251");
}

TEST_CASE("text catalogue keys match the windows-1252 punctuation of game tables")
{
    CatalogueFixture fixture;
    fixture.write("Wait…\tПодожди…\n");
    fixture.load();
    CHECK(localizeDisplayText(std::string("Wait\x85")) == cyrillic("Подожди…"));
}

TEST_CASE("the active world's catalogue wins over shared entries for that world only")
{
    {
        CatalogueFixture fixture("mm6");
        fixture.write("New Sorpigal\tНовый Сорпигал\nTree\tДерево\n");
        fixture.write("New Sorpigal\tНью-Сорпигаль\nWell\tКолодец\n", "worlds/mm6/localization/ru/world_strings.tsv");
        fixture.load();
        CHECK(localizeDisplayText("New Sorpigal") == cyrillic("Нью-Сорпигаль"));
        CHECK(localizeDisplayText("Well") == cyrillic("Колодец"));
        CHECK(localizeDisplayText("Tree") == cyrillic("Дерево"));
    }
    CatalogueFixture fixture("mm8");
    fixture.write("New Sorpigal\tНовый Сорпигал\n");
    fixture.write("New Sorpigal\tНью-Сорпигаль\n", "worlds/mm6/localization/ru/world_strings.tsv");
    fixture.load();
    CHECK(localizeDisplayText("New Sorpigal") == cyrillic("Новый Сорпигал"));
}

TEST_CASE("a language's own copy of an asset replaces the shared one")
{
    CatalogueFixture fixture;
    fixture.write("x\tх\n", "engine/localization/ru/fonts/truetype/arrus.yml");
    fixture.write("x\n", "engine/fonts/truetype/lucida.yml");
    fixture.load();
    CHECK(Engine::localizedAssetPath(fixture.assets, "fonts/truetype/arrus.yml")
        == "localization/ru/fonts/truetype/arrus.yml");
    CHECK(Engine::localizedAssetPath(fixture.assets, "fonts/truetype/lucida.yml") == "fonts/truetype/lucida.yml");
    fixture.load(Engine::EnglishLanguageId);
    CHECK(Engine::localizedAssetPath(fixture.assets, "fonts/truetype/arrus.yml") == "fonts/truetype/arrus.yml");
}

TEST_CASE("text catalogue translates formatted text through its printf entries")
{
    CatalogueFixture fixture;
    fixture.write("%s hits %s for %lu damage\t%s нанес(ла) врагу \"%s\" урон в %lu ед.\n"
                  "Goblin\tГоблин\n"
                  "%d points left\tОсталось очков: %d\n"
                  "\"%s\nPress a key or mouse button.\"\t\"%s\nНажмите клавишу или кнопку мыши.\"\n"
                  "Forward\tВперёд\n"
                  "%d%% done\tГотово на %d%%\n"
                  "%s %s\t%s и %s\n"
                  "%d apples\t%s яблок\n"
                  "Reverting in %d seconds.\tВозврат через %d с.\n");
    fixture.load();
    CHECK(localizeDisplayText("Ariel hits Goblin for 12 damage")
        == cyrillic("Ariel нанес(ла) врагу \"Гоблин\" урон в 12 ед."));
    CHECK(localizeDisplayText("15 points left") == cyrillic("Осталось очков: 15"));
    CHECK(localizeDisplayText("-3 points left") == cyrillic("Осталось очков: -3"));
    CHECK(localizeDisplayText("Forward\nPress a key or mouse button.")
        == cyrillic("Вперёд\nНажмите клавишу или кнопку мыши."));
    CHECK(localizeDisplayText("50% done") == cyrillic("Готово на 50%"));
    CHECK(localizeDisplayText("Reverting in 9 seconds.") == cyrillic("Возврат через 9 с."));
    // The same text again, from the per-thread match cache.
    CHECK(localizeDisplayText("Reverting in 9 seconds.") == cyrillic("Возврат через 9 с."));
    // Values must have the declared kind, and the literal text must match around them.
    CHECK(localizeDisplayText("many points left") == "many points left");
    CHECK(localizeDisplayText("15 points left over") == "15 points left over");
    CHECK(localizeDisplayText(" hits Goblin for 12 damage") == " hits Goblin for 12 damage");
    // Entries without enough literal text, or whose values change kind, are no patterns.
    CHECK(localizeDisplayText("Ariel Goblin") == "Ariel Goblin");
    CHECK(localizeDisplayText("3 apples") == "3 apples");
}

TEST_CASE("short catalogue patterns apply only to names the catalogue translates")
{
    CatalogueFixture fixture;
    fixture.write("the %s\t%s\nKnight\tРыцарь\n"
                  "%s, %s\t%s, %s\n%s GM%d\t%s ВМ%d\nKervin\tКервин\nBlacksmith\tОружейник\nFire Bolt\tОгн.Стр\n");
    fixture.load();
    CHECK(localizeDisplayText("the Knight") == cyrillic("Рыцарь"));
    CHECK(localizeDisplayText("the end of the road") == "the end of the road");
    CHECK(localizeDisplayText("Kervin, Blacksmith") == cyrillic("Кервин, Оружейник"));
    CHECK(localizeDisplayText("Fire Bolt GM10") == cyrillic("Огн.Стр ВМ10"));
    CHECK(localizeDisplayText("Kervin, my friend") == "Kervin, my friend");
    CHECK(localizeDisplayText("Yes, Blacksmith") == "Yes, Blacksmith");
}

TEST_CASE("catalogue patterns translate assembled values and let a value span the next literal")
{
    CatalogueFixture fixture;
    fixture.write("Identified %s.\tОпознано: %s.\n%s of Might\t%s (Мощи)\nLongsword\tБольшой меч\n"
                  "%s %d Gold\t%s %d з.м.\nBribe the guard\tПодкупить стражу\n");
    fixture.load();
    CHECK(localizeDisplayText("Identified Longsword of Might.") == cyrillic("Опознано: Большой меч (Мощи)."));
    CHECK(localizeDisplayText("Identified Longsword.") == cyrillic("Опознано: Большой меч."));
    CHECK(localizeDisplayText("Identified Spear.") == cyrillic("Опознано: Spear."));
    CHECK(localizeDisplayText("Bribe the guard 100 Gold") == cyrillic("Подкупить стражу 100 з.м."));
    CHECK(localizeDisplayText("Bribe the guard many Gold") == "Bribe the guard many Gold");
}

TEST_CASE("formatted display text translates the template and each name it is given")
{
    CatalogueFixture fixture;
    fixture.load(Engine::EnglishLanguageId);
    CHECK(formatDisplayText("%s the %s", {"Zoltan", "Knight"}) == "Zoltan the Knight");
    fixture.write("%s the %s\t%s, %s\nKnight\tРыцарь\n%dh\t%d ч\n");
    fixture.load();
    CHECK(formatDisplayText("%s the %s", {"Zoltan", "Knight"}) == cyrillic("Zoltan, Рыцарь"));
    CHECK(formatDisplayText("%s has %d gold", {"Zoltan", "12"}) == "Zoltan has 12 gold");
    CHECK(formatDisplayText("%dh", {"5"}) == cyrillic("5 ч"));
}

TEST_CASE("catalogue patterns follow catalogue reloads")
{
    CatalogueFixture fixture;
    fixture.write("%d points left\tОсталось очков: %d\n");
    fixture.load();
    CHECK(localizeDisplayText("7 points left") == cyrillic("Осталось очков: 7"));
    fixture.write("%d points left\tОчков осталось: %d\n");
    fixture.load();
    CHECK(localizeDisplayText("7 points left") == cyrillic("Очков осталось: 7"));
    fixture.load(Engine::EnglishLanguageId);
    CHECK(localizeDisplayText("7 points left") == "7 points left");
}

TEST_CASE("code page text: windows-1251 Cyrillic, windows-1252 Latin and the characters each lacks")
{
    CHECK(Engine::codePageCharacter("windows-1251", 0xc0) == 0x0410);
    CHECK(Engine::codePageCharacter("windows-1251", 0xff) == 0x044f);
    CHECK(Engine::codePageCharacter("windows-1251", 0xa8) == 0x0401);
    CHECK(Engine::codePageCharacter("windows-1252", 0xe9) == 0x00e9);
    CHECK(Engine::codePageCharacter("windows-1252", 0x85) == 0x2026);
    CHECK(Engine::codePageCharacter("windows-1252", 0x81) == 0);
    CHECK(Engine::codePageCharacter("windows-1251", 0x0a) == 0);
    CHECK(encodeCodePageText("Caf\xc3\xa9 \xe2\x80\x93 1", "windows-1252") == "Caf\xe9 \x96 1");
    CHECK(cyrillic("Ёж — да") == "\xa8\xe6 \x97 \xe4\xe0");
    CHECK_THROWS_AS(encodeCodePageText("\xd0\x98", "windows-1252"), std::runtime_error);
    CHECK_THROWS_AS(encodeCodePageText("Caf\xc3\xa9", "windows-1251"), std::runtime_error);
    CHECK_THROWS_AS(encodeCodePageText("x", "koi8-r"), std::runtime_error);
}
