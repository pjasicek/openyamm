#pragma once

#include "engine/AssetFileSystem.h"
#include "game/audio/SoundRef.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct SoundCatalogEntry
{
    SoundScope scope = SoundScope::Engine;
    uint32_t soundId = 0;
    std::string name;
    std::string normalizedComment;
    bool positional = false;
};

class SoundCatalog
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadFromScopedRows(
        const std::vector<std::vector<std::string>> &engineRows,
        const std::vector<std::vector<std::string>> &worldRows,
        std::string &errorMessage);
    void initializeVirtualPathIndex(const Engine::AssetFileSystem &assetFileSystem);
    const SoundCatalogEntry *findById(uint32_t soundId) const;
    const SoundCatalogEntry *findById(SoundRef sound) const;
    std::optional<std::string> buildVirtualPath(uint32_t soundId) const;
    std::optional<std::string> buildVirtualPath(SoundRef sound) const;
    std::optional<uint32_t> pickSpeechSoundId(uint32_t voiceId, const std::string &commentKey, uint32_t seed) const;

private:
    bool appendRows(
        const std::vector<std::vector<std::string>> &rows,
        SoundScope scope,
        bool indexSpeechSounds,
        std::unordered_map<std::string, std::string> &inheritedCommentBySpeechGroup,
        std::string *pErrorMessage);
    const std::unordered_map<uint32_t, size_t> &entryIndexByScope(SoundScope scope) const;
    std::unordered_map<uint32_t, size_t> &entryIndexByScope(SoundScope scope);
    const std::unordered_map<std::string, std::string> &virtualPathIndexByScope(SoundScope scope) const;

    std::vector<SoundCatalogEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_engineEntryIndexById;
    std::unordered_map<uint32_t, size_t> m_worldEntryIndexById;
    std::unordered_map<uint32_t, std::unordered_map<std::string, std::vector<uint32_t>>> m_speechSoundIdsByVoiceId;
    std::unordered_map<std::string, std::string> m_engineVirtualPathByLowerName;
    std::unordered_map<std::string, std::string> m_worldVirtualPathByLowerName;
    std::string m_activeWorldId = "mm8";
};
}
