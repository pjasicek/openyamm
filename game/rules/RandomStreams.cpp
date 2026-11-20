#include "game/rules/RandomStreams.h"

#include <cctype>
#include <chrono>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
// SplitMix64's finaliser: a bijective mix with good avalanche, enough for counter-based streams.
uint64_t mix64(uint64_t value)
{
    value += 0x9e3779b97f4a7c15ull;
    value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ull;
    value = (value ^ (value >> 27)) * 0x94d049bb133111ebull;
    return value ^ (value >> 31);
}
}

uint64_t randomStreamKey(uint64_t rootSeed, RandomDomain domain, uint64_t a, uint64_t b, uint64_t c)
{
    uint64_t key = mix64(rootSeed ^ mix64(static_cast<uint64_t>(domain)));
    key = mix64(key ^ a);
    key = mix64(key ^ mix64(b));
    return mix64(key ^ mix64(mix64(c)));
}

uint64_t randomNameKey(const std::string &name)
{
    // FNV-1a over the lowercase name.
    uint64_t hash = 14695981039346656037ull;

    for (char character : name)
    {
        hash ^= uint8_t(std::tolower(static_cast<unsigned char>(character)));
        hash *= 1099511628211ull;
    }

    return hash;
}

uint64_t freshRandomRootSeed()
{
    std::random_device device;
    const uint64_t entropy = (static_cast<uint64_t>(device()) << 32) ^ device();
    const uint64_t time = static_cast<uint64_t>(std::chrono::steady_clock::now().time_since_epoch().count());
    return mix64(entropy ^ mix64(time));
}

RandomStream::RandomStream(uint64_t key, uint64_t counter)
    : m_key(key), m_counter(counter)
{
}

RandomStream::result_type RandomStream::operator()()
{
    return mix64(m_key ^ mix64(m_counter++));
}

uint32_t RandomStream::uniform(uint32_t low, uint32_t high)
{
    if (high <= low)
    {
        return low;
    }

    // Rejection sampling keeps every value equally likely.
    const uint64_t span = static_cast<uint64_t>(high) - low + 1;
    const uint64_t limit = max() - max() % span;
    uint64_t value = 0;

    do
    {
        value = (*this)();
    }
    while (value >= limit);

    return low + static_cast<uint32_t>(value % span);
}

uint64_t RandomStream::counter() const
{
    return m_counter;
}
}
