#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"

#include <cstdint>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class MonsterModifierTable;

struct ActorBehaviorDefinition
{
    std::string id;
    std::string sourcePath;
    std::string source;
};

// Actor behaviour scripts and their default attachments. engine/behaviors/behaviors.yml declares the shared library
// and behaviours; the active world's worlds/<id>/behaviors.yml adds its own and attaches behaviours to monster ids.
// World entries replace engine entries with the same behaviour id or monster id.
// `tactics` (monster id -> options) are declarative combat tactics without a script (ActorTacticsFacts): a turret's
// traverse, a ranged band and a post. ActorBehaviorRuntime applies them to every actor of that monster.
class ActorBehaviorCatalog
{
public:
    bool load(const Engine::AssetFileSystem &assetFileSystem, const std::string &worldId, std::string &error);

    void clear();
    void setLibrary(const std::string &sourcePath, const std::string &source);
    void addBehavior(const std::string &id, const std::string &sourcePath, const std::string &source);
    void setMonsterDefault(int16_t monsterId, const std::string &behaviorId);
    void setMonsterTactics(int16_t monsterId, const ActorTacticsFacts &tactics);
    // The monster modifiers that are tactics (kites_party: the ranged band; skirmisher: the skirmish footwork;
    // reposition: a holder's moves to see its target and back-offs), and the
    // MM9 AI profiles (mm9_ai). False, with error, for a monster whose tactics already set a ranged band: one of the
    // two must go.
    bool applyMonsterModifiers(const MonsterModifierTable &modifiers, std::string &error);

    const std::string &worldId() const;
    const std::string &librarySourcePath() const;
    const std::string &librarySource() const;
    const ActorBehaviorDefinition *findBehavior(const std::string &id) const;
    const std::string *defaultBehaviorForMonster(int16_t monsterId) const;
    bool empty() const;
    bool hasMonsterDefaults() const;
    const ActorTacticsFacts *tacticsForMonster(int16_t monsterId) const;
    bool hasTactics() const;
    // The MM9 AI profile of a monster row (modifier mm9_ai), null for every other monster.
    const Mm9AiProfile *mm9AiProfileForMonster(int16_t monsterId) const;
    bool hasMm9AiProfiles() const;

private:
    bool loadDocument(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        bool required,
        std::string &error);

    std::string m_worldId;
    std::string m_librarySourcePath;
    std::string m_librarySource;
    std::unordered_map<std::string, ActorBehaviorDefinition> m_behaviors;
    std::unordered_map<int16_t, std::string> m_monsterDefaults;
    std::unordered_map<int16_t, ActorTacticsFacts> m_monsterTactics;
    std::unordered_map<int16_t, Mm9AiProfile> m_monsterMm9AiProfiles;
};
}
