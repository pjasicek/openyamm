#include "game/SoundCatalog.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
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
        else if (std::isspace(static_cast<unsigned char>(character)) != 0 || character == '/' || character == '-')
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

bool isSpeechSoundName(const std::string &name, uint32_t &voiceId, std::string &speechGroupKey)
{
    if (name.size() < 6 || name[0] != 'p' || name[1] != 'c'
        || !std::isdigit(static_cast<unsigned char>(name[2]))
        || !std::isdigit(static_cast<unsigned char>(name[3]))
        || !std::isdigit(static_cast<unsigned char>(name[4]))
        || !std::isdigit(static_cast<unsigned char>(name[5])))
    {
        return false;
    }

    const uint32_t voiceCode =
        static_cast<uint32_t>(name[2] - '0') * 10u + static_cast<uint32_t>(name[3] - '0');

    if (voiceCode < 50)
    {
        return false;
    }

    voiceId = voiceCode - 50u;
    speechGroupKey = name.substr(0, 6);
    return true;
}
}

bool SoundCatalog::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexById.clear();
    m_speechSoundIdsByVoiceId.clear();

    std::unordered_map<std::string, std::string> inheritedCommentBySpeechGroup;

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty() || row[0][0] == '/')
        {
            continue;
        }

        SoundCatalogEntry entry = {};
        entry.name = trimCopy(row[0]);
        entry.soundId = static_cast<uint32_t>(std::strtoul(row[1].c_str(), nullptr, 10));
        entry.positional = row.size() > 3 && normalizeComment(row[3]) == "3d";

        uint32_t speechVoiceId = 0;
        std::string speechGroupKey;
        std::string normalizedComment = row.size() > 4 ? normalizeComment(row[4]) : "";

        if (isSpeechSoundName(entry.name, speechVoiceId, speechGroupKey))
        {
            if (normalizedComment.empty())
            {
                const std::unordered_map<std::string, std::string>::const_iterator commentIt =
                    inheritedCommentBySpeechGroup.find(speechGroupKey);

                if (commentIt != inheritedCommentBySpeechGroup.end())
                {
                    normalizedComment = commentIt->second;
                }
            }
            else
            {
                inheritedCommentBySpeechGroup[speechGroupKey] = normalizedComment;
            }
        }

        entry.normalizedComment = normalizedComment;
        m_entryIndexById[entry.soundId] = m_entries.size();
        m_entries.push_back(entry);

        if (!normalizedComment.empty() && isSpeechSoundName(entry.name, speechVoiceId, speechGroupKey))
        {
            m_speechSoundIdsByVoiceId[speechVoiceId][normalizedComment].push_back(entry.soundId);
        }
    }

    return !m_entries.empty();
}

void SoundCatalog::initializeVirtualPathIndex(const Engine::AssetFileSystem &assetFileSystem)
{
    m_virtualPathByLowerName.clear();

    for (const std::string &entry : assetFileSystem.enumerate("Data/EnglishD"))
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

        const std::string resolvedPath = "Data/EnglishD/" + entry;
        m_virtualPathByLowerName[lowerEntry] = resolvedPath;
        m_virtualPathByLowerName[lowerEntry.substr(0, lowerEntry.size() - 4)] = resolvedPath;
    }
}

const SoundCatalogEntry *SoundCatalog::findById(uint32_t soundId) const
{
    const std::unordered_map<uint32_t, size_t>::const_iterator entryIt = m_entryIndexById.find(soundId);

    if (entryIt == m_entryIndexById.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}

std::optional<std::string> SoundCatalog::buildVirtualPath(uint32_t soundId) const
{
    const SoundCatalogEntry *pEntry = findById(soundId);

    if (pEntry == nullptr || pEntry->name.empty() || pEntry->name == "null")
    {
        return std::nullopt;
    }

    const std::string lowerName = toLowerCopy(pEntry->name);
    const std::unordered_map<std::string, std::string>::const_iterator resolvedPathIt =
        m_virtualPathByLowerName.find(lowerName);

    if (resolvedPathIt != m_virtualPathByLowerName.end())
    {
        return resolvedPathIt->second;
    }

    return "Data/EnglishD/" + pEntry->name + ".wav";
}

std::optional<uint32_t> SoundCatalog::pickSpeechSoundId(uint32_t voiceId, const std::string &commentKey, uint32_t seed) const
{
    const std::unordered_map<uint32_t, std::unordered_map<std::string, std::vector<uint32_t>>>::const_iterator voiceIt =
        m_speechSoundIdsByVoiceId.find(voiceId);

    if (voiceIt == m_speechSoundIdsByVoiceId.end())
    {
        return std::nullopt;
    }

    const std::unordered_map<std::string, std::vector<uint32_t>>::const_iterator speechIt =
        voiceIt->second.find(commentKey);

    if (speechIt == voiceIt->second.end() || speechIt->second.empty())
    {
        return std::nullopt;
    }

    return speechIt->second[seed % speechIt->second.size()];
}
}
