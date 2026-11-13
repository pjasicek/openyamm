#pragma once

#include <yaml-cpp/yaml.h>

#include <array>
#include <atomic>
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
class SpriteFrameTable;
struct ActorAttackTiming;
struct ActorClipChoices;

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
        // The manifest's `gait: intent` (default `speed`): its models walk while their AI walks and run while it runs,
        // as MM9's do, unless that clip would play outside its rate window (actorModelIntendedGait); otherwise the
        // clip that suits the speed plays (actorModelGait).
        bool gaitFollowsIntent = false;
        // This descriptor's entry in actor_sounds.yml beside its actors.yml (null without): the timed sounds of its
        // model's clips (WorldFxSystem's ActorClipSounds).
        YAML::Node sounds;
    };

    // Attack roles of a bound model, in the order of BoundClips' arrays.
    enum class AttackRole : uint8_t
    {
        Melee,
        Ranged,
        Cast,
    };

    // The clips of a bound monster's model that time its gameplay (its attacks, its fidgets): read from the binding
    // and the model file's clip lengths (Engine::readGltfModelSummary), never from a loaded or posed model, so the
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
        // MM9's Conv clips (a townsperson's chat): its script clip role `conv` alone when it has one, else its
        // conv<n> roles, and their lengths. Read with the clips above (empty when neither is read).
        std::vector<std::string> convRoles;
        std::vector<float> convSeconds;
        // The model's bind pose (Engine::readGltfModelSummary's bindPoseHeightRange times the binding's `scale`; its
        // scale_reference and the actor's own scale apply later, actorTargetHeight): its lowest and highest point above
        // its origin, equal when unknown, and its `z_offset`, the origin's height above the actor's feet.
        float bodyBottom = 0.0f;
        float bodyTop = 0.0f;
        float zOffset = 0.0f;
        // The binding's scale_reference (empty without).
        std::string scaleReference;
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
    // What a bound monster's scale_reference multiplies its scale by, as WorldFxSystem applies it: its standing
    // sprite's scale over the reference's, from the map's sprite frames (which hold both for every bound monster
    // the map can show). Kept once found; 1 without a reference, 0 while the frames lack either sprite.
    float scaleReferenceRatio(int16_t monsterId, const MonsterTable &monsters,
        const SpriteFrameTable *pSpriteFrames) const;

private:
    BoundClips readBoundClips(const Entry &entry) const;

    std::unordered_map<std::string, Entry> m_entries;
    std::vector<bool> m_boundMonsterIds;
    // By monster id: its entry (null when unbound) and its attack clips, read on first use.
    std::vector<const Entry *> m_entryByMonsterId;
    const Engine::AssetFileSystem *m_pAssets = nullptr;
    mutable std::unique_ptr<std::once_flag[]> m_boundClipsRead;
    mutable std::vector<BoundClips> m_boundClips;
    // By monster id: scaleReferenceRatio once found (negative before; two threads may both find it).
    mutable std::unique_ptr<std::atomic<float>[]> m_scaleReferenceRatios;
    // YAML nodes are not safe to read from two threads at once (anchors share them): one read at a time.
    mutable std::mutex m_boundClipsReadMutex;
};

// The height above a monster's feet where the party aims at it: GameMechanics::actorTargetHeight of its height, or of
// its 3D model's bind pose when that is lower (a model shorter than its collision height, such as MM8's Bone Dragon).
// The model is scaled as WorldFxSystem draws it: bodyHeight over the descriptor's height (or drawScale when set) and
// visualScale (a shrink). It counts only while models are on (MonsterTable::actorModels), as the sprite is drawn
// otherwise; pSpriteFrames resolves a binding's scale_reference (the map's actor sprite frames).
float actorTargetHeight(const MonsterTable &monsters, const SpriteFrameTable *pSpriteFrames, int16_t monsterId,
    uint16_t height, uint16_t bodyHeight, float drawScale, float visualScale);

// One attack role of a monster: the timing of its sprite (the native action's length and its contact frame, 0 without
// one) unless its 3D model's clip times it (resolveActorAttackTiming; pModels null: models off).
ActorAttackTiming actorAttackTiming(const ActorModelManifest *pModels, int16_t monsterId,
    ActorModelManifest::AttackRole role, float spriteSeconds, float spriteImpactSeconds);

// The fidget clips a monster picks from (ActorRuntimeFacts::fidgetClips): its model's variants, or none (pModels null,
// an unbound monster or a manifest without fidget variants: its one sprite or model fidget).
ActorClipChoices actorFidgetClips(const ActorModelManifest *pModels, int16_t monsterId);

// The role of a fidget variant (ActorMm9State::fidgetVariant) for the presentation: a script clip role, or empty for
// the binding's own fidget (the Bored clip) and for anything it does not know.
std::string actorFidgetRole(const ActorModelManifest *pModels, int16_t monsterId, int8_t variant);

// The Conv clips a monster's chats pick from (ActorRuntimeFacts::convClips), and the role of one
// (ActorMm9State::chatClip; empty for anything it does not know).
ActorClipChoices actorConvClips(const ActorModelManifest *pModels, int16_t monsterId);
std::string actorConvRole(const ActorModelManifest *pModels, int16_t monsterId, int8_t variant);
}
