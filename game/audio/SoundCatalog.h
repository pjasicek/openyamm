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
    // A sound named by id alone (the voice table: MM6-MM8's voices are engine sounds, MM9's its world's): the engine's
    // sound of that id, else a world's. A world sound never takes an engine id (loadWorldSoundRows), so it is one.
    std::optional<std::string> buildVirtualPathAnyScope(uint32_t soundId) const;
    std::optional<std::string> buildVirtualPathByName(SoundScope scope, const std::string &soundName) const;

private:
    bool appendRows(
        const std::vector<std::vector<std::string>> &rows,
        SoundScope scope,
        std::string *pErrorMessage);
    const std::unordered_map<uint32_t, size_t> &entryIndexByScope(SoundScope scope) const;
    std::unordered_map<uint32_t, size_t> &entryIndexByScope(SoundScope scope);
    const std::unordered_map<std::string, std::string> &virtualPathIndexByScope(SoundScope scope) const;

    std::vector<SoundCatalogEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_engineEntryIndexById;
    std::unordered_map<uint32_t, size_t> m_worldEntryIndexById;
    std::unordered_map<std::string, std::string> m_engineVirtualPathByLowerName;
    std::unordered_map<std::string, std::string> m_worldVirtualPathByLowerName;
    std::string m_activeWorldId = "mm8";
};

// The sound table rows every mounted world contributes (world.yml `sounds` table contributions, read into the world
// sound scope): false when a manifest fails to load, a table is missing, or a row's id lies outside the world's
// declared id range or is one of the engine table's ids (a world sound never shadows an engine sound).
bool loadWorldSoundRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::vector<std::string>> &engineRows,
    std::vector<std::vector<std::string>> &worldRows,
    std::string &errorMessage);
}
