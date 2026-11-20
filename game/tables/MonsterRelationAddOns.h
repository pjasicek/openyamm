#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// Monster relations contributed by worlds and mods on top of the engine's relation table (hostile.txt), from each
// mounted world's relations.yml (schema openyamm.monsterRelations.v1): factions of monster ids and the relations of a
// faction toward the party, other factions or any monster, optionally switched by a QBit. A pair no rule covers keeps
// the engine table's relation, so monsters outside every faction are unchanged.
//
// Relations use the engine's levels: 0 friendly or neutral, 1-4 hostile with an engagement range of 1 024 (close),
// 2 560 (short), 5 120 (medium) or the long range.
class MonsterRelationAddOns
{
public:
    // Adds one world's file; its monster ids must lie in [idBegin, idEnd] (the world's monster id range).
    bool loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t idBegin, uint32_t idEnd,
        std::string &error);
    void clear();
    bool empty() const
    {
        return m_rules.empty() && m_factionByMonster.empty();
    }

    // The faction of a monster, -1 for none.
    int factionOf(int16_t monsterId) const;
    const std::string &factionName(int faction) const;
    // How the actor's monster treats the target monster, or the party; none when no active rule decides it.
    std::optional<int> relationBetween(int16_t actorMonsterId, int16_t targetMonsterId) const;
    std::optional<int> relationToParty(int16_t monsterId) const;
    // Whether both monsters belong to one faction or to kin factions (they rally together); none when neither has a
    // faction.
    std::optional<bool> sameFaction(int16_t leftMonsterId, int16_t rightMonsterId) const;

    // QBit-switched rules: their state is a cache of the party's QBits, refreshed by the world runtimes each actor
    // update. Returns true when a rule changed (revision() then advances).
    bool hasConditions() const
    {
        return m_hasConditions;
    }
    bool refreshConditions(const std::function<bool(uint32_t)> &isQBitSet) const;
    uint64_t revision() const
    {
        return m_revision;
    }
    // Whether a QBit-switched rule covers this monster's relation to the party.
    bool partyRelationIsConditional(int16_t monsterId) const;

private:
    enum class TargetKind : uint8_t
    {
        Party,
        Any,
        Factions,
    };

    struct Rule
    {
        std::vector<int> fromFactions;
        TargetKind target = TargetKind::Factions;
        std::vector<int> toFactions;
        int relation = 0;
        // Active while the QBit is clear (untilQBit) or once it is set (afterQBit); 0 for none.
        uint32_t untilQBit = 0;
        uint32_t afterQBit = 0;
    };

    void resolve() const;

    std::vector<std::string> m_factionNames;
    std::vector<std::vector<int>> m_kin;
    std::unordered_map<int16_t, int> m_factionByMonster;
    std::vector<Rule> m_rules;
    bool m_hasConditions = false;
    int16_t m_minimumMonsterId = INT16_MAX;
    int16_t m_maximumMonsterId = INT16_MIN;
    // Per rule: whether its condition holds (refreshConditions).
    mutable std::vector<uint8_t> m_ruleActive;
    // Resolved relations of the active rules: [from * (factions + 1) + to] with to = factions for "any", and per
    // faction toward the party; -1 where no rule decides.
    mutable std::vector<int8_t> m_pairRelations;
    mutable std::vector<int8_t> m_partyRelations;
    mutable uint64_t m_revision = 0;
};
}
