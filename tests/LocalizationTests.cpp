#include "engine/Localization.h"
#include "engine/TextCatalog.h"

#include <doctest/doctest.h>

#include <string>
#include <vector>

using namespace OpenYAMM::Engine;

namespace
{
TextCatalog catalogOf(const std::string &poText, const std::string &defaultContext = {})
{
    std::string error;
    const std::optional<PoFile> file = parsePoFile(poText, error);
    REQUIRE_MESSAGE(file.has_value(), error);
    TextCatalog catalog;
    std::vector<std::string> warnings;
    catalog.add(*file, "test.po", defaultContext, warnings);
    return catalog;
}
}

TEST_CASE("Localization: a .po file reads contexts, plurals, escapes and flags")
{
    const std::string text = "# translator comment\n"
                             "msgid \"\"\n"
                             "msgstr \"\"\n"
                             "\"Content-Type: text/plain; charset=UTF-8\\n\"\n"
                             "\"Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && "
                             "(n%100<10 || n%100>=20) ? 1 : 2);\\n\"\n"
                             "\n"
                             "#: game/ui/Shop.cpp:10\n"
                             "msgid \"Not enough gold.\"\n"
                             "msgstr \"Недостаточно золота.\"\n"
                             "\n"
                             "msgctxt \"map:7out01\"\n"
                             "msgid \"Refreshing!\"\n"
                             "msgstr \"\"\n"
                             "\"Освежает!\"\n"
                             "\n"
                             "msgid \"{count} day\"\n"
                             "msgid_plural \"{count} days\"\n"
                             "msgstr[0] \"{count} день\"\n"
                             "msgstr[1] \"{count} дня\"\n"
                             "msgstr[2] \"{count} дней\"\n"
                             "\n"
                             "#, fuzzy\n"
                             "msgid \"Door\"\n"
                             "msgstr \"Дверь\"\n"
                             "\n"
                             "msgid \"Line\\none\\t\\\"quoted\\\" \\\\ \\f00000\"\n"
                             "msgstr \"x\"\n"
                             "\n"
                             "#~ msgid \"Gone\"\n"
                             "#~ msgstr \"Ушло\"\n";

    std::string error;
    const std::optional<PoFile> file = parsePoFile(text, error);
    REQUIRE_MESSAGE(file.has_value(), error);
    CHECK(file->pluralForms.starts_with("nplurals=3"));
    REQUIRE(file->entries.size() == 5);
    CHECK(file->entries[0].english == "Not enough gold.");
    CHECK(file->entries[0].translations.front() == "Недостаточно золота.");
    CHECK(file->entries[1].context == "map:7out01");
    CHECK(file->entries[1].translations.front() == "Освежает!");
    CHECK(file->entries[2].englishPlural == "{count} days");
    CHECK(file->entries[2].translations.size() == 3);
    CHECK(file->entries[3].fuzzy);
    CHECK(file->entries[4].english == "Line\none\t\"quoted\" \\ \f00000");
}

TEST_CASE("Localization: malformed .po text is refused with its line")
{
    std::string error;
    CHECK_FALSE(parsePoFile("msgid \"a\"\nmsgid \"b\"\nmsgstr \"c\"\n", error).has_value());
    CHECK(error.starts_with("line 2"));
    CHECK_FALSE(parsePoFile("msgid \"unterminated\nmsgstr \"x\"\n", error).has_value());
    CHECK_FALSE(parsePoFile("msgstr \"no msgid\"\n", error).has_value());
    CHECK_FALSE(parsePoFile("msgid \"a\"\nmsgstr[0] \"no plural\"\n", error).has_value());
    CHECK_FALSE(parsePoFile("msgid \"a\"\n", error).has_value());
}

TEST_CASE("Localization: plural rules follow the Plural-Forms formula")
{
    std::string error;
    const std::optional<PluralRule> russian = PluralRule::parse(
        "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
        error);
    REQUIRE_MESSAGE(russian.has_value(), error);
    CHECK(russian->formCount() == 3);
    CHECK(russian->form(1) == 0);
    CHECK(russian->form(21) == 0);
    CHECK(russian->form(11) == 2);
    CHECK(russian->form(3) == 1);
    CHECK(russian->form(14) == 2);
    CHECK(russian->form(25) == 2);

    const std::optional<PluralRule> chinese = PluralRule::parse("nplurals=1; plural=0;", error);
    REQUIRE(chinese.has_value());
    CHECK(chinese->form(5) == 0);

    const std::optional<PluralRule> french = PluralRule::parse("nplurals=2; plural=(n > 1);", error);
    REQUIRE(french.has_value());
    CHECK(french->form(0) == 0);
    CHECK(french->form(2) == 1);

    CHECK(PluralRule::english().form(1) == 0);
    CHECK(PluralRule::english().form(0) == 1);

    CHECK_FALSE(PluralRule::parse("nplurals=2; plural=n+;", error).has_value());
    CHECK_FALSE(PluralRule::parse("nplurals=2; plural=n;", error).has_value());
    CHECK_FALSE(PluralRule::parse("plural=0;", error).has_value());
}

TEST_CASE("Localization: a translation must keep its English's placeholders and codes")
{
    CHECK(translationMismatch("Sold {item} for {price} gold.", "За {price} золотых продано: {item}.").empty());
    CHECK_FALSE(translationMismatch("Sold {item} for {price} gold.", "Продано {item}.").empty());
    CHECK_FALSE(translationMismatch("Sold {item}.", "Продано {предмет}.").empty());
    CHECK(translationMismatch("%s hits %s for %d damage", "%s бьёт %s на %d урона").empty());
    CHECK_FALSE(translationMismatch("%s hits %s for %d damage", "%d урона: %s бьёт %s").empty());
    CHECK(translationMismatch("Welcome, %01!", "Добро пожаловать, %01!").empty());
    CHECK_FALSE(translationMismatch("Welcome, %01!", "Добро пожаловать!").empty());
    CHECK(translationMismatch("\f02016Gold\f00000", "\f02016Золото\f00000").empty());
    CHECK_FALSE(translationMismatch("\f02016Gold\f00000", "Золото").empty());
    // A percent sign before a word is not a printf value.
    CHECK(translationMismatch("50% chance", "шанс 50 %").empty());
    CHECK(translationMismatch("Damage {add*2} and {skill:1}", "Урон {add*2}, {skill:1}").empty());
}

TEST_CASE("Localization: a catalogue refuses entries that lose a placeholder and keeps the rest")
{
    std::string error;
    const std::optional<PoFile> file = parsePoFile("msgid \"Sold {item}.\"\n"
                                                   "msgstr \"Продано.\"\n"
                                                   "\n"
                                                   "msgid \"Door\"\n"
                                                   "msgstr \"Дверь\"\n",
                                                   error);
    REQUIRE(file.has_value());
    TextCatalog catalog;
    std::vector<std::string> warnings;
    catalog.add(*file, "ru.po", {}, warnings);
    CHECK(catalog.size() == 1);
    REQUIRE(warnings.size() == 1);
    CHECK(warnings.front().find("ru.po:1") != std::string::npos);
    CHECK(catalog.find({}, "Sold {item}.") == nullptr);
    REQUIRE(catalog.find({}, "Door") != nullptr);
}

TEST_CASE("Localization: contexts, world files and plurals in a catalogue")
{
    const TextCatalog catalog = catalogOf("msgid \"\"\n"
                                          "msgstr \"Plural-Forms: nplurals=1; plural=0;\\n\"\n"
                                          "\n"
                                          "msgid \"Celeste\"\n"
                                          "msgstr \"天界\"\n"
                                          "\n"
                                          "msgctxt \"map:7d25\"\n"
                                          "msgid \"Door\"\n"
                                          "msgstr \"大门\"\n"
                                          "\n"
                                          "msgid \"{count} day\"\n"
                                          "msgid_plural \"{count} days\"\n"
                                          "msgstr[0] \"{count} 天\"\n",
                                          "world:mm7");

    CHECK(catalog.find({}, "Celeste") == nullptr);
    REQUIRE(catalog.find("world:mm7", "Celeste") != nullptr);
    CHECK(*catalog.find("world:mm7", "Celeste") == "天界");
    REQUIRE(catalog.find("map:7d25", "Door") != nullptr);
    CHECK(catalog.find("world:mm7", "Door") == nullptr);
    REQUIRE(catalog.findPlural("world:mm7", "{count} day", 7) != nullptr);
    CHECK(*catalog.findPlural("world:mm7", "{count} day", 7) == "{count} 天");
    // A world's text shown in another world: found through its file, entries with their own context are not.
    REQUIRE(catalog.findInWorldFiles("Celeste") != nullptr);
    CHECK(*catalog.findInWorldFiles("Celeste") == "天界");
    CHECK(catalog.findInWorldFiles("Door") == nullptr);
}

TEST_CASE("Localization: placeholders are filled by name and unknown braces stay")
{
    const std::vector<TextArgument> arguments = {{"item", "Long Sword"}, {"price", 150}};
    CHECK(formatText("Sold {item} for {price} gold.", arguments) == "Sold Long Sword for 150 gold.");
    CHECK(formatText("{price} gold for {item}", arguments) == "150 gold for Long Sword");
    CHECK(formatText("Damage {add*2} for {item}", arguments) == "Damage {add*2} for Long Sword");
    CHECK(formatText("No braces", arguments) == "No braces");
    CHECK(formatText("{unclosed", arguments) == "{unclosed");
}

TEST_CASE("Localization: the pseudo-language marks, accents and lengthens but keeps codes")
{
    const std::string pseudo = pseudoLocalize("Settings");
    CHECK(pseudo.front() == '[');
    CHECK(pseudo.back() == ']');
    CHECK(pseudo.find("S\xc3\xa9tt\xc3\xadngs") == std::string::npos);
    CHECK(pseudo.find("S\xc3\xa9tt\xc3\xad\xc3\xb1gs") != std::string::npos);
    CHECK(pseudo.find("\xc2\xb7") != std::string::npos);

    const std::string coded = pseudoLocalize("Sold {item} for %d gold to %01\f02016");
    CHECK(coded.find("{item}") != std::string::npos);
    CHECK(coded.find("%d") != std::string::npos);
    CHECK(coded.find("%01") != std::string::npos);
    CHECK(coded.find("\f02016") != std::string::npos);
    CHECK(translationMismatch("Sold {item} for %d gold to %01\f02016", coded).empty());
    CHECK(pseudoLocalize("").empty());
}

TEST_CASE("Localization: with no language active every text stays English")
{
    REQUIRE(activeLanguageId() == EnglishLanguageId);
    CHECK(tr("Not enough gold.") == "Not enough gold.");
    CHECK(tr("Sold {item} for {price} gold.", {{"item", "Dagger"}, {"price", 5}}) == "Sold Dagger for 5 gold.");
    CHECK(trc("button", "Close") == "Close");
    CHECK(trn("{count} day", "{count} days", 1, {{"count", 1}}) == "1 day");
    CHECK(trn("{count} day", "{count} days", 3, {{"count", 3}}) == "3 days");
    CHECK(localize("Refreshing!", "map:oute3") == "Refreshing!");
    // The original tables' Windows-1252 bytes pass through unchanged.
    CHECK(localize("Caf\xe9") == "Caf\xe9");
    CHECK(validLanguageId("zh-cn"));
    CHECK_FALSE(validLanguageId("../en"));
    CHECK_FALSE(validLanguageId(""));
}
