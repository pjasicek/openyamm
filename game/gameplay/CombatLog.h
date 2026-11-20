#pragma once

#include <cstdint>
#include <deque>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct DamageStageRecord;

// One damage stage of a logged hit, as DamagePipeline ran it.
struct CombatLogStage
{
    std::string name;
    int before = 0;
    int after = 0;
};

enum class CombatLogKind : uint8_t
{
    // The party's hits on monsters.
    Dealt,
    // Monsters' hits on the party.
    Taken,
    // A drop the loot filter turned into gold ("Filtered: Uncommon Longsword -> 312 gold"): `target` is the item,
    // `rarity` and `rarityColor` its rarity, `amount` the gold.
    Loot,
};

// One logged hit, in the parts the panel words and colours (the study's "Gerrard shoots Goblin for 58 damage").
struct CombatLogEntry
{
    uint32_t id = 0;
    CombatLogKind kind = CombatLogKind::Dealt;
    // When it happened, in game minutes (CombatLog stamps it).
    float gameMinutes = 0;
    std::string attacker;
    // "hits", "shoots" or "casts"; a cast names its spell.
    std::string verb;
    std::string spell;
    // The struck one, or "3 monsters" for an area spell's line.
    std::string target;
    int amount = 0;
    bool critical = false;
    bool killed = false;
    // The stages the damage rules ran for this hit; empty when they are not known (an area spell's total).
    std::vector<CombatLogStage> stages;
    // A Loot line's rarity and its colour (ABGR; 0: the body colour).
    std::string rarity;
    uint32_t rarityColor = 0;
};

// The combat log (devdocs/maw/GAPS.md H.3): the last hits of play, for the docked log panel. It records only while the
// player has it on (the combat_log setting): the damage rules then hand it each hit's stages (CombatRules), and the
// places that resolve the hit add the entry, which takes the stages of the matching hit. Off, nothing is kept.
class CombatLog
{
public:
    static constexpr size_t MaxEntries = 200;

    bool recording() const;
    void setRecording(bool recording);

    // A hit's damage stages, from the damage rules: `onCharacter` for a hit on a party member.
    void recordStages(bool onCharacter, int finalAmount, const std::vector<DamageStageRecord> &records);
    // A hit (its id and time are set here). It takes the stages of the oldest recorded hit of its kind with the same
    // final amount; older ones of that kind, which no entry claimed, are dropped. `takeStages` false for a line that
    // sums several hits (an area spell): it takes none.
    void add(CombatLogEntry entry, bool takeStages = true);
    // The game time new entries are stamped with, from the session's update.
    void setGameMinutes(float gameMinutes);
    void clear();

    const std::deque<CombatLogEntry> &entries() const;
    // Changes whenever an entry is added or the log is cleared, so views rebuild only then.
    uint64_t revision() const;

private:
    struct PendingStages
    {
        bool onCharacter = false;
        int finalAmount = 0;
        std::vector<CombatLogStage> stages;
    };

    static constexpr size_t MaxPendingStages = 64;

    bool m_recording = false;
    float m_gameMinutes = 0;
    uint32_t m_nextId = 1;
    uint64_t m_revision = 0;
    std::deque<CombatLogEntry> m_entries;
    std::deque<PendingStages> m_pendingStages;
};

// The log the damage rules hand stages to; the gameplay screen binds its own. None while nothing is bound.
CombatLog *boundCombatLog();
void bindCombatLog(CombatLog *pLog);
}
