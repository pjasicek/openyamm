#pragma once

#include <cstdint>
#include <limits>
#include <string>

namespace OpenYAMM::Game
{
// Named, reproducible random streams (devdocs/maw/RANDOMS.md §7.2). A stream is a key built from the save's root
// seed, a domain and stable ids (map, actor spawn id, chest and slot, house and refresh count); draw n is a mix of the
// key and n, so only a reused stream needs its counter saved. Combat and cosmetics stay on plain randomness.
// The values are stored in saves through the keys they produce; never renumber them.
enum class RandomDomain : uint16_t
{
    // 2-7, 13 and 14 were planned for chests, ground items, shops, rewards, item rolls and spawns, which keep the
    // engine's per-visit seeds, and 17 for MAW's randomizer, which is not ported; they stay unused.
    CorpseLoot = 1,
    CraftDrop = 8,
    CraftApply = 9,
    BossSelect = 10,
    BossStats = 11,
    BossAffix = 12,
    Dimension = 15,
    DimensionQuest = 16,
    DoomSpecialAttack = 18,
    // The dimension rolls that once shared Dimension's keys with others (audit ROB-2-9).
    DimensionCompletion = 19,
    DimensionBecomeBoss = 20,
    DimensionHigherTier = 21,
};

uint64_t randomStreamKey(uint64_t rootSeed, RandomDomain domain, uint64_t a = 0, uint64_t b = 0, uint64_t c = 0);
// A stable id for a name in stream keys (a map file name, ignoring case).
uint64_t randomNameKey(const std::string &name);
// A new root seed for a new game, from the system's entropy.
uint64_t freshRandomRootSeed();

// One stream: a key and a counter. Meets UniformRandomBitGenerator, so the standard distributions draw from it.
class RandomStream
{
public:
    using result_type = uint64_t;

    explicit RandomStream(uint64_t key, uint64_t counter = 0);

    static constexpr result_type min()
    {
        return 0;
    }

    static constexpr result_type max()
    {
        return std::numeric_limits<result_type>::max();
    }

    result_type operator()();
    // A whole number in [low, high].
    uint32_t uniform(uint32_t low, uint32_t high);
    uint64_t counter() const;

private:
    uint64_t m_key = 0;
    uint64_t m_counter = 0;
};
}
