#include "engine/Localization.h"

#include "engine/AssetFileSystem.h"
#include "engine/Utf8Text.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <mutex>
#include <optional>
#include <span>
#include <unordered_set>

namespace OpenYAMM::Engine
{
namespace
{
constexpr std::string_view LanguagesDirectory = "languages";
// The translations of a world's own texts are text/<world>.po; text/engine*.po are shared by every world.
constexpr std::string_view SharedTextFilePrefix = "engine";
// Enough to show what kind of entries a pack refuses without flooding the log.
constexpr size_t LoggedWarningCount = 20;

struct ActiveLanguage
{
    std::string id = std::string(EnglishLanguageId);
    bool pseudo = false;
    TextCatalog catalog;
    std::string worldContext;
};

ActiveLanguage &activeLanguage()
{
    static ActiveLanguage language;
    return language;
}

// OPENYAMM_UNTRANSLATED_TEXT_LOG=<file>: each text the active language lacks, once, for translators.
class UntranslatedTextLog
{
public:
    void record(std::string_view context, std::string_view english)
    {
        std::lock_guard<std::mutex> lock(m_mutex);

        if (!m_opened)
        {
            m_opened = true;
            const char *pPath = std::getenv("OPENYAMM_UNTRANSLATED_TEXT_LOG");

            if (pPath != nullptr && pPath[0] != '\0')
            {
                m_file.open(pPath, std::ios::app);
            }
        }

        if (!m_file.is_open())
        {
            return;
        }

        std::string line;
        line.reserve(context.size() + english.size() + 1);
        line += context;
        line += '\t';

        for (const char character : english)
        {
            if (character == '\n')
            {
                line += "\\n";
            }
            else if (character == '\t')
            {
                line += "\\t";
            }
            else
            {
                line += character;
            }
        }

        if (m_logged.insert(line).second)
        {
            m_file << line << '\n';
            m_file.flush();
        }
    }

private:
    std::mutex m_mutex;
    bool m_opened = false;
    std::ofstream m_file;
    std::unordered_set<std::string> m_logged;
};

UntranslatedTextLog &untranslatedTextLog()
{
    static UntranslatedTextLog log;
    return log;
}

bool hasNonAsciiByte(std::string_view text)
{
    return std::any_of(text.begin(), text.end(), [](char character) { return (unsigned char)character >= 0x80; });
}

// The translation of English in the most specific context that has one: the caller's, the world's, then none; last,
// what another world's file gives its own text (the party carries items between worlds, MAW puts MM9's in every world).
const std::string *findTranslation(const ActiveLanguage &language, std::string_view english, std::string_view context)
{
    if (!context.empty())
    {
        if (const std::string *pTranslation = language.catalog.find(context, english))
        {
            return pTranslation;
        }
    }

    if (!language.worldContext.empty() && language.worldContext != context)
    {
        if (const std::string *pTranslation = language.catalog.find(language.worldContext, english))
        {
            return pTranslation;
        }
    }

    if (const std::string *pTranslation = language.catalog.find({}, english))
    {
        return pTranslation;
    }

    return language.catalog.findInWorldFiles(english);
}

// A table cell keeps the spaces and line breaks around its text ("Elvis ", a topic ending in an empty line); the
// catalogs hold the text without them. The translation gets the same surroundings back.
std::optional<std::string> findTrimmedTranslation(const ActiveLanguage &language, std::string_view english,
                                                  std::string_view context)
{
    constexpr std::string_view Whitespace = " \t\r\n";
    const size_t begin = english.find_first_not_of(Whitespace);

    if (begin == std::string_view::npos)
    {
        return std::nullopt;
    }

    const size_t end = english.find_last_not_of(Whitespace) + 1;

    if (begin == 0 && end == english.size())
    {
        return std::nullopt;
    }

    const std::string *pTranslation = findTranslation(language, english.substr(begin, end - begin), context);

    if (pTranslation == nullptr)
    {
        return std::nullopt;
    }

    return std::string(english.substr(0, begin)) + *pTranslation + std::string(english.substr(end));
}

const std::string *findPluralTranslation(const ActiveLanguage &language, std::string_view english,
                                         std::string_view context, uint64_t count)
{
    if (!context.empty())
    {
        if (const std::string *pTranslation = language.catalog.findPlural(context, english, count))
        {
            return pTranslation;
        }
    }

    if (!language.worldContext.empty() && language.worldContext != context)
    {
        if (const std::string *pTranslation = language.catalog.findPlural(language.worldContext, english, count))
        {
            return pTranslation;
        }
    }

    return language.catalog.findPlural({}, english, count);
}

std::string textFileContext(std::string_view fileName)
{
    const std::string_view stem = fileName.substr(0, fileName.size() - 3);
    return stem.starts_with(SharedTextFilePrefix) ? std::string() : "world:" + std::string(stem);
}

std::string localizePlural(std::string_view context, std::string_view singular, std::string_view plural,
                           uint64_t count)
{
    const ActiveLanguage &language = activeLanguage();
    const std::string_view english = count == 1 ? singular : plural;

    if (language.pseudo)
    {
        return pseudoLocalize(english);
    }

    if (language.catalog.empty() || singular.empty())
    {
        return std::string(english);
    }

    if (const std::string *pTranslation = findPluralTranslation(language, singular, context, count))
    {
        return *pTranslation;
    }

    untranslatedTextLog().record(context, singular);
    return std::string(english);
}
}

bool validLanguageId(std::string_view id)
{
    return !id.empty() && id.size() <= 16
        && std::all_of(id.begin(), id.end(), [](char character)
                       {
                           return (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9')
                               || character == '-' || character == '_';
                       });
}

std::vector<LanguagePack> findLanguagePacks(const AssetFileSystem &assetFileSystem)
{
    std::vector<LanguagePack> packs;

    for (const std::string &id : assetFileSystem.enumerate(std::string(LanguagesDirectory)))
    {
        if (!validLanguageId(id) || id == EnglishLanguageId || id == PseudoLanguageId)
        {
            continue;
        }

        const std::optional<std::string> description =
            assetFileSystem.readTextFile(std::string(LanguagesDirectory) + "/" + id + "/language.yml");

        if (!description)
        {
            continue;
        }

        try
        {
            const YAML::Node node = YAML::Load(*description);
            LanguagePack pack;
            pack.id = id;
            pack.name = node["name"].as<std::string>(id);
            pack.englishName = node["english_name"].as<std::string>(pack.name);
            packs.push_back(std::move(pack));
        }
        catch (const YAML::Exception &exception)
        {
            std::cout << "Language: languages/" << id << "/language.yml is not valid: " << exception.what() << '\n';
        }
    }

    std::sort(packs.begin(), packs.end(), [](const LanguagePack &left, const LanguagePack &right)
              {
                  return left.id < right.id;
              });
    return packs;
}

bool activateLanguage(const AssetFileSystem &assetFileSystem, std::string_view languageId)
{
    ActiveLanguage &language = activeLanguage();
    const std::string worldContext = language.worldContext;
    language = ActiveLanguage();
    language.worldContext = worldContext;

    if (languageId.empty() || languageId == EnglishLanguageId)
    {
        return true;
    }

    if (languageId == PseudoLanguageId)
    {
        language.id = std::string(PseudoLanguageId);
        language.pseudo = true;
        std::cout << "Language: pseudo-language qps\n";
        return true;
    }

    const std::string root = std::string(LanguagesDirectory) + "/" + std::string(languageId);

    if (!validLanguageId(languageId) || !assetFileSystem.exists(root + "/language.yml"))
    {
        std::cout << "Language: no language pack " << languageId << "; the game stays in English\n";
        return false;
    }

    std::vector<std::string> warnings;
    size_t fileCount = 0;

    for (const std::string &fileName : assetFileSystem.enumerate(root + "/text"))
    {
        if (fileName.size() <= 3 || !fileName.ends_with(".po"))
        {
            continue;
        }

        const std::string path = root + "/text/" + fileName;
        const std::optional<std::string> text = assetFileSystem.readTextFile(path);
        std::string error;
        const std::optional<PoFile> file = text ? parsePoFile(*text, error) : std::nullopt;

        if (!file)
        {
            std::cout << "Language: " << path << " left out: " << (text ? error : "cannot be read") << '\n';
            continue;
        }

        language.catalog.add(*file, path, textFileContext(fileName), warnings);
        ++fileCount;
    }

    for (const std::string &entry : assetFileSystem.enumerate(root))
    {
        if (entry != "language.yml" && entry != "text" && entry != "engine" && entry != "worlds")
        {
            std::cout << "Language: " << root << "/" << entry << " ignored: a pack holds language.yml, text/, engine/"
                      << " and worlds/\n";
        }
    }

    for (size_t index = 0; index < warnings.size() && index < LoggedWarningCount; ++index)
    {
        std::cout << "Language: " << warnings[index] << '\n';
    }

    if (warnings.size() > LoggedWarningCount)
    {
        std::cout << "Language: and " << warnings.size() - LoggedWarningCount << " more refused entries\n";
    }

    language.id = std::string(languageId);
    std::cout << "Language: " << language.id << ", " << language.catalog.size() << " translations from " << fileCount
              << (fileCount == 1 ? " file\n" : " files\n");
    return true;
}

const std::string &activeLanguageId()
{
    return activeLanguage().id;
}

void setLocalizationWorld(std::string_view worldId)
{
    activeLanguage().worldContext = worldId.empty() ? std::string() : "world:" + std::string(worldId);
}

std::string mapTextContext(std::string_view fileName)
{
    const size_t separator = fileName.find_last_of("/\\");

    if (separator != std::string_view::npos)
    {
        fileName.remove_prefix(separator + 1);
    }

    fileName = fileName.substr(0, fileName.find('.'));

    if (fileName.empty())
    {
        return {};
    }

    std::string context = "map:";

    for (const char character : fileName)
    {
        context += char(std::tolower(static_cast<unsigned char>(character)));
    }

    return context;
}

std::string localize(std::string_view english, std::string_view context)
{
    const ActiveLanguage &language = activeLanguage();

    if (english.empty() || (!language.pseudo && language.catalog.empty()))
    {
        return std::string(english);
    }

    if (language.pseudo)
    {
        return pseudoLocalize(english);
    }

    // The original tables hold Windows-1252 bytes; translation files are UTF-8.
    const std::string normalized = hasNonAsciiByte(english) ? Utf8::normalized(english) : std::string();
    const std::string_view key = normalized.empty() ? english : std::string_view(normalized);

    if (const std::string *pTranslation = findTranslation(language, key, context))
    {
        return *pTranslation;
    }

    if (std::optional<std::string> translation = findTrimmedTranslation(language, key, context))
    {
        return *translation;
    }

    untranslatedTextLog().record(context, key);
    return std::string(english);
}

std::string localizeKnown(std::string_view text, std::string_view context)
{
    const ActiveLanguage &language = activeLanguage();

    if (language.pseudo)
    {
        // Already marked by an earlier lookup (a script's message): not marked twice.
        const bool marked = text.size() >= 2 && text.front() == '[' && text.back() == ']';
        return marked ? std::string(text) : pseudoLocalize(text);
    }

    if (text.empty() || language.catalog.empty())
    {
        return std::string(text);
    }

    const std::string normalized = hasNonAsciiByte(text) ? Utf8::normalized(text) : std::string();
    const std::string_view key = normalized.empty() ? text : std::string_view(normalized);

    if (const std::string *pTranslation = findTranslation(language, key, context))
    {
        return *pTranslation;
    }

    return findTrimmedTranslation(language, key, context).value_or(std::string(text));
}

std::string tr(std::string_view english)
{
    return localize(english);
}

std::string tr(std::string_view english, std::initializer_list<TextArgument> arguments)
{
    return formatText(localize(english), std::span<const TextArgument>(arguments.begin(), arguments.size()));
}

std::string trc(std::string_view context, std::string_view english, std::initializer_list<TextArgument> arguments)
{
    return formatText(localize(english, context), std::span<const TextArgument>(arguments.begin(), arguments.size()));
}

std::string trn(std::string_view singular, std::string_view plural, uint64_t count,
                std::initializer_list<TextArgument> arguments)
{
    return formatText(localizePlural({}, singular, plural, count),
                      std::span<const TextArgument>(arguments.begin(), arguments.size()));
}
}
