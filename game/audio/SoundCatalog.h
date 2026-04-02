#pragma once

#include "engine/AssetFileSystem.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct SoundCatalogEntry
{
    uint32_t soundId = 0;
    std::string name;
    std::string normalizedComment;
    bool positional = false;
};

class SoundCatalog
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    void initializeVirtualPathIndex(const Engine::AssetFileSystem &assetFileSystem);
    const SoundCatalogEntry *findById(uint32_t soundId) const;
    std::optional<std::string> buildVirtualPath(uint32_t soundId) const;
    std::optional<uint32_t> pickSpeechSoundId(uint32_t voiceId, const std::string &commentKey, uint32_t seed) const;

private:
    std::vector<SoundCatalogEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndexById;
    std::unordered_map<uint32_t, std::unordered_map<std::string, std::vector<uint32_t>>> m_speechSoundIdsByVoiceId;
    std::unordered_map<std::string, std::string> m_virtualPathByLowerName;
};
}
