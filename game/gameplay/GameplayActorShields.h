#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/tables/MonsterShields.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct EventRuntimeState;
class MonsterTable;

// The attack tier of a hit known only by its damage type (monster attacks, projectiles without an explicit tier):
// Physical is physical, Energy (and, from the party, Irresistible: the blasters) is energy, everything else magic.
ShieldAttackTier shieldAttackTierForDamageType(CombatDamageType damageType, bool fromParty);

// Where a hit from `source` meets the shell of an actor standing at `foot` (its collision radius and height): on the
// side facing the source, at the source's height within the body.
std::array<float, 3> actorShieldImpactPoint(const std::array<float, 3> &foot, float radius, float height,
    const std::array<float, 3> &source);

// Presentation of an actor's energy shield (GameplayRuntimeActorState::shield). Never saved.
struct GameplayActorShieldView
{
    static constexpr size_t MaxHits = 4;

    // The actor's monster has a shield pool.
    bool present = false;
    bool raised = false;
    // Current over full pool.
    float fraction = 0.0f;
    // Grade colour (linear RGB) and strength.
    std::array<float, 3> color = {};
    float intensity = 1.0f;
    // Strength while raised and untouched (the grade's rest_intensity); negative: the intensity.
    float restIntensity = -1.0f;
    // Seconds since the shield broke or came back up, -1 when it has not this map visit (or long ago).
    float secondsSinceBreak = -1.0f;
    float secondsSinceRaise = -1.0f;
    // Recent hits on the raised shield: world impact point and age in seconds (age < 0: unused).
    std::array<std::array<float, 4>, MaxHits> hits = {};
    // Counters of hits, breaks and raises, so presentation can react to each once.
    uint32_t hitSerial = 0;
    uint32_t breakSerial = 0;
    uint32_t raiseSerial = 0;
};

// What one hit did to an actor's shield.
struct GameplayActorShieldHit
{
    // Damage left for the body (exposed multiplier applied); equals the input for an actor without a profile.
    int bodyDamage = 0;
    // Points the raised shield lost to the hit.
    float shieldDamage = 0.0f;
    // A raised shield took the hit: no hit reaction.
    bool absorbed = false;
    bool broke = false;
};

// A shield sound the world runtime hands to its event runtime state (EventRuntimeState::pendingSounds).
struct GameplayActorShieldSound
{
    std::string name;
    std::string fallback;
    std::array<float, 3> position = {};
};

// Energy shields of one world runtime's actors (MonsterTable::shields), indexed by its actor indices. Only actors
// whose monster has a shield profile get an entry; without profiles every call returns at once. Runtime state:
// shields start full on every map load, like the original game's regenerating stats.
class GameplayActorShields
{
public:
    struct ActorFacts
    {
        int16_t monsterId = 0;
        bool alive = false;
        // Body centre, for sounds and link distances.
        std::array<float, 3> center = {};
        // Shield links join allies: actors on the same side of the party whose monsters are not hostile.
        bool hostileToParty = false;
    };

    // pRelations (optional) decides which actors a shield link joins (MonsterTable::getRelationBetweenMonsters).
    void bind(const MonsterShieldTable *pTable, const MonsterTable *pRelations = nullptr);
    const MonsterShieldTable *table() const
    {
        return m_pTable;
    }
    void clear();
    bool active() const
    {
        return m_pTable != nullptr && !m_pTable->empty();
    }
    // Per actor step: creates entries for newly seen shielded actors, regenerates, ages the presentation.
    void update(float deltaSeconds, size_t actorCount, const std::function<ActorFacts(size_t)> &actorFacts);
    // One hit through the shield rules; pImpactPoint (world) places the ripple, defaulting to the shield's last
    // known centre.
    GameplayActorShieldHit applyHit(size_t actorIndex, int16_t monsterId, int damage, ShieldAttackTier tier,
        const std::array<float, 3> *pImpactPoint = nullptr, const ShieldHitModifiers &modifiers = {});
    // Cuts a raised shield to remainingFraction of what is left (Overload, the EMP grenade) with a ripple; false when
    // the actor has no raised shield.
    bool cutRaisedShield(size_t actorIndex, float remainingFraction,
        const std::array<float, 3> *pImpactPoint = nullptr);
    // An actor script's self:suspendShield: the shield drops (a break, if it was up) and does not regenerate for the
    // seconds (negative: until restore). False without a shield.
    bool suspend(size_t actorIndex, int16_t monsterId, float seconds);
    bool restore(size_t actorIndex);
    // Seconds since the shield broke while it is still down; -1 while it is up, without a shield, or long ago.
    float secondsDownSinceBreak(size_t actorIndex) const;
    // The actor's shield profile (null without one).
    const MonsterShieldProfile *profile(size_t actorIndex) const;
    void view(size_t actorIndex, GameplayActorShieldView &view) const;
    // Current shield points (0 without an entry), and a debug/test setter that keeps the pool's bounds.
    float shieldPoints(size_t actorIndex) const;
    bool setShieldPoints(size_t actorIndex, float points);
    std::vector<GameplayActorShieldSound> drainSounds();
    // Hands the queued shield sounds to the world's event runtime state (played by name, with their fallbacks).
    void queueSounds(EventRuntimeState &eventRuntimeState);

private:
    struct Entry
    {
        bool used = false;
        bool alive = false;
        bool hostileToParty = false;
        int16_t monsterId = 0;
        const MonsterShieldProfile *pProfile = nullptr;
        float current = 0.0f;
        float secondsSinceDamage = 0.0f;
        float secondsSinceBreak = -1.0f;
        float secondsSinceRaise = -1.0f;
        std::array<float, 3> center = {};
        std::array<std::array<float, 4>, GameplayActorShieldView::MaxHits> hits = {};
        uint32_t hitSerial = 0;
        uint32_t breakSerial = 0;
        uint32_t raiseSerial = 0;
        // Regeneration held by a script (suspend): seconds left, negative until restored, 0 not held.
        float suspendedSeconds = 0.0f;
    };

    Entry *ensure(size_t actorIndex, int16_t monsterId);
    void queueSound(const std::string &name, const std::array<float, 3> &position);
    void addRipple(Entry &entry, const std::array<float, 3> &impact);
    void breakShield(Entry &entry, const std::array<float, 3> &impact);
    bool allied(const Entry &linker, const Entry &other) const;
    // Regeneration multipliers of living links and the breaks of a dead linker's allies (MonsterShieldProfile::link*).
    void updateLinks();

    const MonsterShieldTable *m_pTable = nullptr;
    const MonsterTable *m_pRelations = nullptr;
    // Per entry, rebuilt each update while some monster links (1 without a link in reach).
    std::vector<float> m_regenMultipliers;
    // Linkers (linkDropsOnDeath) that died this update.
    std::vector<size_t> m_deadLinkers;
    std::vector<Entry> m_entries;
    std::vector<GameplayActorShieldSound> m_sounds;
};
}
