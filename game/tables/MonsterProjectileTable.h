#pragma once

#include "game/tables/MonsterShields.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct MonsterProjectileEntry
{
    std::string token;
    std::string normalizedToken;
    int objectId = 0;
    int impactObjectId = 0;
    // What a hit is to an energy shield; unset follows the attack's damage type (projectileShieldTier). Only a world's
    // missiles (monster_projectiles.yml) set it.
    std::optional<ShieldAttackTier> shieldTier;
    // The sound its impact plays (a sounds.txt id), 0: none, as MM's monster missiles.
    uint32_t impactSoundId = 0;
};

// A party gun's own missile (monster_projectiles.yml party: {<item id>: {missile: <token>, shot_sound_id: <id>}}).
struct PartyGunMissile
{
    const MonsterProjectileEntry *pMissile = nullptr;
    // The sound of its shot (a sounds.txt id), 0: the blaster's.
    uint32_t shotSoundId = 0;
};

class MonsterProjectileTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    // Appends a world's missiles: worlds/<world>/monster_projectiles.yml (schema openyamm.monsterProjectiles.v1),
    //   missiles: {<token>: {object: <id>, impact_object: <id or 0>, tier: <shield tier>, impact_sound_id: <id>}}
    //   party: {<item id>: {missile: <token>, shot_sound_id: <id>}}  (the party's guns: what each item fires)
    // Each object id must lie in the world's objects range [objectBegin, objectEnd]; a token may not repeat one the
    // table already has (MM's tokens stay as they are).
    bool loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t objectBegin,
        uint32_t objectEnd, std::string &error);
    const MonsterProjectileEntry *findByToken(const std::string &token) const;
    // The missile an equipped gun fires; nullopt for every gun the worlds do not list (MM's blaster bolt).
    std::optional<PartyGunMissile> findPartyGun(uint32_t itemId) const;
    const std::vector<MonsterProjectileEntry> &entries() const
    {
        return m_entries;
    }

private:
    std::vector<MonsterProjectileEntry> m_entries;
    std::unordered_map<std::string, size_t> m_entryIndexByNormalizedToken;
    struct PartyGun
    {
        size_t entryIndex = 0;
        uint32_t shotSoundId = 0;
    };
    std::unordered_map<uint32_t, PartyGun> m_partyGunByItemId;
};
}
