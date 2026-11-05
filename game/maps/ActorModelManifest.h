#pragma once

#include <yaml-cpp/yaml.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class MonsterTable;
struct ActorAttackTiming;
struct ActorFidgetClips;

// Actor model bindings (worlds/<world>/models/actors.yml): the monster descriptors drawn as 3D models. Descriptors are
// global, so every mounted world contributes its bindings to all worlds (an MM9 map spawning an MM6 monster shows the
// MM6 model). A world binds a descriptor once; the active world's binding replaces another world's, and two other
// worlds binding one descriptor is an error. Loading only indexes the entries: WorldFxSystem builds a binding (loads
// its model) when a map first needs it, and the map loader skips the sprites of every bound monster.
class ActorModelManifest
{
public:
    struct Entry
    {
        YAML::Node node;
        std::string manifestPath;
        // The manifest's `attack_timing: clip`: its models' clips are their monsters' native attack timing (an attack
        // lasts its clip and applies at the clip's impact key), not the rows' sprites (boundClips).
        bool clipsTimeAttacks = false;
        // The manifest's `fidget_variants: true`: a fidget picks among the binding's `fidget` clip and its script clips
        // fidget<n> and search<n>, as MM9 picks among a model's Fidget* and Search* clips (fidgetClips).
        bool fidgetVariants = false;
    };

    // Attack roles of a bound model, in the order of BoundClips' arrays.
    enum class AttackRole : uint8_t
    {
        Melee,
        Ranged,
        Cast,
    };

    // The clips of a bound monster's model that time its gameplay (its attacks, its fidgets): read from the binding
    // and the model file's clip lengths (Engine::readGltfClipDurations), never from a loaded or posed model, so the
    // game runs the same with models drawn or not (headless).
    struct BoundClips
    {
        // Per AttackRole: the clip's length (0 unknown) and its impact key (actors.yml animation.events.<role>.impact,
        // the cast's falling back to the ranged attack's when both play one clip; negative: none).
        std::array<float, 3> clipSeconds = {};
        std::array<float, 3> impactSeconds = {-1.0f, -1.0f, -1.0f};
        bool clipsTimeAttacks = false;
        // Entry::fidgetVariants: the fidgets in order, the binding's `fidget` first (an empty role: the Bored clip),
        // then its script clip roles, and their clips' lengths. Empty without fidget variants.
        std::vector<std::string> fidgetRoles;
        std::vector<float> fidgetSeconds;
    };

    // Reads the existing manifests among paths, then activePath (empty for none), whose bindings replace theirs.
    bool load(const Engine::AssetFileSystem &assets, const std::vector<std::string> &paths,
        const std::string &activePath, const MonsterTable &monsters, std::string &error);
    // Keyed by the monster table's internal name.
    const Entry *find(const std::string &descriptor) const;
    bool binds(const std::string &descriptor) const
    {
        return m_entries.contains(descriptor);
    }
    // The same by monster id (MonsterTable::findById), for per-frame checks.
    bool bindsMonster(int16_t monsterId) const
    {
        return monsterId >= 0 && size_t(monsterId) < m_boundMonsterIds.size() && m_boundMonsterIds[size_t(monsterId)];
    }
    const std::unordered_map<std::string, Entry> &entries() const
    {
        return m_entries;
    }
    // The timing clips of a bound monster (by monster id), read once on first use; nullptr for an unbound monster.
    const BoundClips *boundClips(int16_t monsterId) const;

private:
    BoundClips readBoundClips(const Entry &entry) const;

    std::unordered_map<std::string, Entry> m_entries;
    std::vector<bool> m_boundMonsterIds;
    // By monster id: its entry (null when unbound) and its attack clips, read on first use.
    std::vector<const Entry *> m_entryByMonsterId;
    const Engine::AssetFileSystem *m_pAssets = nullptr;
    mutable std::unique_ptr<std::once_flag[]> m_boundClipsRead;
    mutable std::vector<BoundClips> m_boundClips;
    // YAML nodes are not safe to read from two threads at once (anchors share them): one read at a time.
    mutable std::mutex m_boundClipsReadMutex;
};

// One attack role of a monster: the timing of its sprite (the native action's length and its contact frame, 0 without
// one) unless its 3D model's clip times it (resolveActorAttackTiming; pModels null: models off).
ActorAttackTiming actorAttackTiming(const ActorModelManifest *pModels, int16_t monsterId,
    ActorModelManifest::AttackRole role, float spriteSeconds, float spriteImpactSeconds);

// The fidget clips a monster picks from (ActorRuntimeFacts::fidgetClips): its model's variants, or none (pModels null,
// an unbound monster or a manifest without fidget variants: its one sprite or model fidget).
ActorFidgetClips actorFidgetClips(const ActorModelManifest *pModels, int16_t monsterId);

// The role of a fidget variant (ActorMm9State::fidgetVariant) for the presentation: a script clip role, or empty for
// the binding's own fidget (the Bored clip) and for anything it does not know.
std::string actorFidgetRole(const ActorModelManifest *pModels, int16_t monsterId, int8_t variant);
}
