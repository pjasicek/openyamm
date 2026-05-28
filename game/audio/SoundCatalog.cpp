#include "game/audio/SoundCatalog.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *MergedAudioDirectory = "audio";

std::string toLowerCopy(const std::string &value)
{
    std::string lower = value;

    for (char &character : lower)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lower;
}

std::string trimCopy(const std::string &value)
{
    size_t start = 0;

    while (start < value.size() && std::isspace(static_cast<unsigned char>(value[start])) != 0)
    {
        ++start;
    }

    size_t end = value.size();

    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(start, end - start);
}

std::string normalizeComment(const std::string &value)
{
    std::string normalized;
    normalized.reserve(value.size());

    for (char character : trimCopy(value))
    {
        if (std::isalnum(static_cast<unsigned char>(character)) != 0)
        {
            normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
        else if (std::isspace(static_cast<unsigned char>(character)) != 0
            || character == '/'
            || character == '-'
            || character == '_')
        {
            if (!normalized.empty() && normalized.back() != '_')
            {
                normalized.push_back('_');
            }
        }
    }

    while (!normalized.empty() && normalized.back() == '_')
    {
        normalized.pop_back();
    }

    return normalized;
}

std::optional<uint32_t> parseSoundId(const std::string &value)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const unsigned long parsedValue = std::strtoul(trimmed.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(parsedValue);
}

std::string soundScopeName(SoundScope scope)
{
    switch (scope)
    {
    case SoundScope::Engine:
        return "engine";

    case SoundScope::World:
        return "world";
    }

    return "unknown";
}

void indexAudioDirectory(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &audioDirectory,
    std::unordered_map<std::string, std::string> &virtualPathByLowerName)
{
    for (const std::string &entry : assetFileSystem.enumerate(audioDirectory))
    {
        if (entry.empty())
        {
            continue;
        }

        const std::string lowerEntry = toLowerCopy(entry);

        if (lowerEntry.size() < 5 || lowerEntry.substr(lowerEntry.size() - 4) != ".wav")
        {
            continue;
        }

        const std::string resolvedPath = audioDirectory + "/" + entry;
        virtualPathByLowerName[lowerEntry] = resolvedPath;
        virtualPathByLowerName[lowerEntry.substr(0, lowerEntry.size() - 4)] = resolvedPath;
    }
}

std::string scopedAudioDirectory(SoundScope scope, const std::string &activeWorldId)
{
    (void)scope;
    (void)activeWorldId;
    return MergedAudioDirectory;
}
}

bool SoundCatalog::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_engineEntryIndexById.clear();
    m_worldEntryIndexById.clear();

    return appendRows(rows, SoundScope::Engine, nullptr) && !m_entries.empty();
}

bool SoundCatalog::loadFromScopedRows(
    const std::vector<std::vector<std::string>> &engineRows,
    const std::vector<std::vector<std::string>> &worldRows,
    std::string &errorMessage)
{
    errorMessage.clear();
    m_entries.clear();
    m_engineEntryIndexById.clear();
    m_worldEntryIndexById.clear();

    if (!appendRows(engineRows, SoundScope::Engine, &errorMessage)
        || !appendRows(worldRows, SoundScope::World, &errorMessage))
    {
        return false;
    }

    if (m_entries.empty())
    {
        errorMessage = "sound catalog has no entries";
        return false;
    }

    return true;
}

bool SoundCatalog::appendRows(
    const std::vector<std::vector<std::string>> &rows,
    SoundScope scope,
    std::string *pErrorMessage)
{
    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty() || row[0][0] == '/')
        {
            continue;
        }

        SoundCatalogEntry entry = {};
        const std::optional<uint32_t> soundId = parseSoundId(row[1]);
        if (!soundId.has_value())
        {
            continue;
        }

        entry.name = trimCopy(row[0]);
        entry.soundId = *soundId;
        entry.scope = scope;
        entry.positional = row.size() > 3 && normalizeComment(row[3]) == "3d";

        std::unordered_map<uint32_t, size_t> &entryIndex = entryIndexByScope(scope);

        if (entry.soundId != 0 && entryIndex.find(entry.soundId) != entryIndex.end())
        {
            if (pErrorMessage != nullptr)
            {
                *pErrorMessage =
                    "duplicate " + soundScopeName(scope) + " sound id " + std::to_string(entry.soundId);
            }

            return false;
        }

        entryIndex[entry.soundId] = m_entries.size();
        m_entries.push_back(entry);
    }

    return true;
}

void SoundCatalog::initializeVirtualPathIndex(const Engine::AssetFileSystem &assetFileSystem)
{
    m_engineVirtualPathByLowerName.clear();
    m_worldVirtualPathByLowerName.clear();
    m_activeWorldId = assetFileSystem.getActiveWorldId();

    indexAudioDirectory(
        assetFileSystem,
        MergedAudioDirectory,
        m_engineVirtualPathByLowerName);
    m_worldVirtualPathByLowerName = m_engineVirtualPathByLowerName;
}

const std::unordered_map<uint32_t, size_t> &SoundCatalog::entryIndexByScope(SoundScope scope) const
{
    switch (scope)
    {
    case SoundScope::Engine:
        return m_engineEntryIndexById;

    case SoundScope::World:
        return m_worldEntryIndexById;
    }

    return m_engineEntryIndexById;
}

std::unordered_map<uint32_t, size_t> &SoundCatalog::entryIndexByScope(SoundScope scope)
{
    switch (scope)
    {
    case SoundScope::Engine:
        return m_engineEntryIndexById;

    case SoundScope::World:
        return m_worldEntryIndexById;
    }

    return m_engineEntryIndexById;
}

const std::unordered_map<std::string, std::string> &SoundCatalog::virtualPathIndexByScope(SoundScope scope) const
{
    switch (scope)
    {
    case SoundScope::Engine:
        return m_engineVirtualPathByLowerName;

    case SoundScope::World:
        return m_worldVirtualPathByLowerName;
    }

    return m_engineVirtualPathByLowerName;
}

const SoundCatalogEntry *SoundCatalog::findById(uint32_t soundId) const
{
    return findById(engineSound(soundId));
}

const SoundCatalogEntry *SoundCatalog::findById(SoundRef sound) const
{
    const std::unordered_map<uint32_t, size_t> &entryIndex = entryIndexByScope(sound.scope);
    const std::unordered_map<uint32_t, size_t>::const_iterator entryIt = entryIndex.find(sound.id);

    if (entryIt == entryIndex.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}

std::optional<std::string> SoundCatalog::buildVirtualPath(uint32_t soundId) const
{
    return buildVirtualPath(engineSound(soundId));
}

std::optional<std::string> SoundCatalog::buildVirtualPath(SoundRef sound) const
{
    const SoundCatalogEntry *pEntry = findById(sound);

    if (pEntry == nullptr && sound.scope == SoundScope::World)
    {
        pEntry = findById(engineSound(sound.id));
    }

    if (pEntry == nullptr || pEntry->name.empty() || pEntry->name == "null")
    {
        return std::nullopt;
    }

    const std::string lowerName = toLowerCopy(pEntry->name);
    const auto findPathInScope = [this, &lowerName](SoundScope scope) -> std::optional<std::string>
    {
        const std::unordered_map<std::string, std::string> &virtualPathByLowerName =
            virtualPathIndexByScope(scope);
        const std::unordered_map<std::string, std::string>::const_iterator resolvedPathIt =
            virtualPathByLowerName.find(lowerName);

        if (resolvedPathIt != virtualPathByLowerName.end())
        {
            return resolvedPathIt->second;
        }

        return std::nullopt;
    };

    if (sound.scope == SoundScope::World)
    {
        if (const std::optional<std::string> worldPath = findPathInScope(SoundScope::World))
        {
            return *worldPath;
        }

        if (const std::optional<std::string> enginePath = findPathInScope(SoundScope::Engine))
        {
            return *enginePath;
        }

        return scopedAudioDirectory(SoundScope::World, m_activeWorldId) + "/" + pEntry->name + ".wav";
    }

    if (const std::optional<std::string> enginePath = findPathInScope(SoundScope::Engine))
    {
        return *enginePath;
    }

    if (const std::optional<std::string> worldPath = findPathInScope(SoundScope::World))
    {
        return *worldPath;
    }

    return scopedAudioDirectory(SoundScope::Engine, m_activeWorldId) + "/" + pEntry->name + ".wav";
}

std::optional<std::string> SoundCatalog::buildVirtualPathByName(SoundScope scope, const std::string &soundName) const
{
    const std::string lowerName = toLowerCopy(trimCopy(soundName));
    if (lowerName.empty())
    {
        return std::nullopt;
    }

    const auto findPathInScope = [this, &lowerName](SoundScope lookupScope) -> std::optional<std::string>
    {
        const std::unordered_map<std::string, std::string> &virtualPathByLowerName =
            virtualPathIndexByScope(lookupScope);
        const std::unordered_map<std::string, std::string>::const_iterator resolvedPathIt =
            virtualPathByLowerName.find(lowerName);

        if (resolvedPathIt != virtualPathByLowerName.end())
        {
            return resolvedPathIt->second;
        }

        return std::nullopt;
    };

    if (scope == SoundScope::World)
    {
        if (const std::optional<std::string> worldPath = findPathInScope(SoundScope::World))
        {
            return *worldPath;
        }

        if (const std::optional<std::string> enginePath = findPathInScope(SoundScope::Engine))
        {
            return *enginePath;
        }
    }
    else
    {
        if (const std::optional<std::string> enginePath = findPathInScope(SoundScope::Engine))
        {
            return *enginePath;
        }

        if (const std::optional<std::string> worldPath = findPathInScope(SoundScope::World))
        {
            return *worldPath;
        }
    }

    return std::nullopt;
}

}
