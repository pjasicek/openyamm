#pragma once

#include "engine/TextCatalog.h"

#include <cstdint>
#include <initializer_list>
#include <string>
#include <string_view>
#include <vector>

// The interface language (devdocs/LOCALIZATION.md). English is the key and the default: with no language active, every
// function here returns its English unchanged. A language pack is languages/<id>/ in the mounted assets: language.yml,
// its translations in text/*.po, and optionally engine/ and worlds/<id>/ folders laid out like the game's whose fonts/,
// audio/ and videos/ mount over the English ones (AssetFileSystem::mountLanguagePack).
namespace OpenYAMM::Engine
{
class AssetFileSystem;

inline constexpr std::string_view EnglishLanguageId = "en";
// The built-in pseudo-language: every looked-up text marked, accented and longer, without files.
inline constexpr std::string_view PseudoLanguageId = "qps";

struct LanguagePack
{
    std::string id;
    // How the language names itself (Русский) and its English name (Russian).
    std::string name;
    std::string englishName;
};

// A language id fit for settings.ini and a folder name: 1-16 lower-case letters, digits, '-' or '_'.
bool validLanguageId(std::string_view id);

// The language packs the mounted assets hold, by id; English and the pseudo-language need none.
std::vector<LanguagePack> findLanguagePacks(const AssetFileSystem &assetFileSystem);

// Makes a language the interface language and loads its translations. English, or a language whose pack is missing,
// leaves the game in English (and returns false for the missing pack). Files that fail to read and entries that do not
// keep their English's placeholders and codes are logged and left out. Call it before anything localizes text, from
// the thread that draws: lookups do not lock.
bool activateLanguage(const AssetFileSystem &assetFileSystem, std::string_view languageId);
// The active language's id: EnglishLanguageId when none.
const std::string &activeLanguageId();
// The active world ("mm7"): its world file's translations ("world:mm7") come before the shared ones.
void setLocalizationWorld(std::string_view worldId);
// The context of a map's own texts, from its map or script file name: "oute3.odm" and "maps/oute3.lua" give
// "map:oute3". Empty for an empty name.
std::string mapTextContext(std::string_view fileName);

// Text of the game's data or scripts as the interface language shows it, its English when there is no translation.
// A context ("map:7out01") is tried first, then the active world's, then none. Windows-1252 bytes of the original
// tables are read as their characters.
std::string localize(std::string_view english, std::string_view context = {});
// The same for a display boundary that also receives text already in the interface language or built from parts
// (event messages): a text the catalogue lacks passes through without a missing-text log entry.
std::string localizeKnown(std::string_view text, std::string_view context = {});

// Text written in the code: tr("Not enough gold."),
// tr("Sold {item} for {price} gold.", {{"item", name}, {"price", 5}}).
std::string tr(std::string_view english);
std::string tr(std::string_view english, std::initializer_list<TextArgument> arguments);
// With an explicit context, for English that needs different translations in different places.
std::string trc(std::string_view context, std::string_view english, std::initializer_list<TextArgument> arguments = {});
// The form the number takes: trn("{count} day", "{count} days", days, {{"count", days}}).
std::string trn(std::string_view singular, std::string_view plural, uint64_t count,
                std::initializer_list<TextArgument> arguments = {});
// Marks English kept in a table of the code ({"Fire", "Air"}) for extraction; translate it where it is shown with
// tr(name) or localize(name).
constexpr std::string_view trNoop(std::string_view english)
{
    return english;
}
// The same for English that is translated with a context where it is shown: trc(context, name).
constexpr std::string_view trcNoop(std::string_view context, std::string_view english)
{
    static_cast<void>(context);
    return english;
}
}
