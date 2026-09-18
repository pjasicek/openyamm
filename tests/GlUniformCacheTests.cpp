#include "engine/GlUniformCache.h"

#include <doctest/doctest.h>

#include <array>
#include <bit>
#include <cstring>

using OpenYAMM::GlUniformCache;

TEST_CASE("GL uniform cache retains values separately across program switches")
{
    GlUniformCache cache;
    int sampler = 2;
    cache.saveCurrentProgram(11);
    CHECK(cache.update(0, 1, &sampler, sizeof(sampler)));
    CHECK_FALSE(cache.update(0, 1, &sampler, sizeof(sampler)));
    cache.saveCurrentProgram(12);
    CHECK(cache.update(0, 1, &sampler, sizeof(sampler)));
    sampler = 3;
    CHECK(cache.update(0, 1, &sampler, sizeof(sampler)));
    cache.saveCurrentProgram(11);
    sampler = 2;
    CHECK_FALSE(cache.update(0, 1, &sampler, sizeof(sampler)));
    CHECK(cache.update(1, 1, &sampler, sizeof(sampler)));
}

TEST_CASE("GL uniform cache invalidates reused program names and context state")
{
    GlUniformCache cache;
    int sampler = 1;
    for (uint32_t program : {7, 8})
    {
        cache.saveCurrentProgram(program);
        CHECK(cache.update(4, 1, &sampler, sizeof(sampler)));
    }
    cache.invalidateProgram(7);
    CHECK_FALSE(cache.update(4, 1, &sampler, sizeof(sampler)));
    cache.saveCurrentProgram(7);
    CHECK(cache.update(4, 1, &sampler, sizeof(sampler)));
    cache.invalidateProgram(7); // Also remove the currently selected program safely.
    cache.saveCurrentProgram(7);
    CHECK(cache.update(4, 1, &sampler, sizeof(sampler)));
    cache.invalidateProgram(999);
    cache.clear();
    for (uint32_t program : {7, 8})
    {
        cache.saveCurrentProgram(program);
        CHECK(cache.update(4, 1, &sampler, sizeof(sampler)));
    }
}

TEST_CASE("GL uniform cache handles partial and overlapping sampler arrays")
{
    GlUniformCache cache;
    cache.saveCurrentProgram(1);
    std::array<int, 4> samplers = {0, 1, 2, 3};
    CHECK(cache.update(8, 4, samplers.data(), sizeof(int)));
    CHECK_FALSE(cache.update(9, 2, samplers.data() + 1, sizeof(int)));
    int replacement = 5;
    CHECK(cache.update(10, 1, &replacement, sizeof(int)));
    CHECK(cache.update(8, 4, samplers.data(), sizeof(int)));
    CHECK_FALSE(cache.update(8, 4, samplers.data(), sizeof(int)));
    samplers[3] = 6;
    CHECK_FALSE(cache.update(8, 3, samplers.data(), sizeof(int)));
    CHECK(cache.update(8, 4, samplers.data(), sizeof(int)));
}

TEST_CASE("GL uniform cache preserves vector and matrix array elements and transpose state")
{
    for (size_t elements : {4, 9, 16})
    {
        CAPTURE(elements);
        GlUniformCache cache;
        cache.saveCurrentProgram(3);
        std::array<float, 48> data = {};
        const size_t elementSize = elements * sizeof(float);
        CHECK(cache.update(20, 3, data.data(), elementSize));
        CHECK_FALSE(cache.update(20, 3, data.data(), elementSize));
        data[elements + elements - 1] = 3.0f;
        CHECK(cache.update(21, 1, data.data() + elements, elementSize));
        CHECK_FALSE(cache.update(20, 3, data.data(), elementSize));
        CHECK(cache.update(20, 3, data.data(), elementSize, true));
        CHECK_FALSE(cache.update(20, 3, data.data(), elementSize, true));
        CHECK(cache.update(20, 3, data.data(), elementSize, false));
    }
}

TEST_CASE("GL uniform cache compares exact bytes without alignment requirements")
{
    GlUniformCache cache;
    cache.saveCurrentProgram(1);
    std::array<float, 4> vector = {0.0f, 1.0f, std::bit_cast<float>(uint32_t{0x7fc00001}), 2.0f};
    std::array<std::byte, sizeof(vector) + 1> unaligned = {};
    std::memcpy(unaligned.data() + 1, vector.data(), sizeof(vector));
    CHECK(cache.update(2, 1, unaligned.data() + 1, sizeof(vector)));
    CHECK_FALSE(cache.update(2, 1, vector.data(), sizeof(vector)));
    vector[0] = -0.0f;
    CHECK(cache.update(2, 1, vector.data(), sizeof(vector)));
    vector[2] = std::bit_cast<float>(uint32_t{0x7fc00002});
    CHECK(cache.update(2, 1, vector.data(), sizeof(vector)));
}

TEST_CASE("GL uniform cache ignores inactive locations and empty uploads")
{
    GlUniformCache cache;
    cache.saveCurrentProgram(1);
    CHECK_FALSE(cache.update(UINT32_MAX, 1, nullptr, sizeof(int)));
    CHECK_FALSE(cache.update(0, 0, nullptr, sizeof(int)));
    int value = 0;
    CHECK(cache.update(0, 1, &value, sizeof(value)));
    CHECK_FALSE(cache.update(0, 1, &value, sizeof(value)));
    cache.saveCurrentProgram(0);
    CHECK(cache.update(0, 1, &value, sizeof(value)));
    cache.saveCurrentProgram(1);
    CHECK_FALSE(cache.update(0, 1, &value, sizeof(value)));
}

TEST_CASE("GL uniform cache keeps the selected program valid as program storage grows")
{
    GlUniformCache cache;
    int value = 7;
    for (uint32_t program = 1; program <= 512; ++program)
    {
        cache.saveCurrentProgram(program);
        CHECK(cache.update(1023, 1, &value, sizeof(value)));
        CHECK_FALSE(cache.update(1023, 1, &value, sizeof(value)));
    }
    for (uint32_t program = 1; program <= 512; ++program)
    {
        cache.saveCurrentProgram(program);
        CHECK_FALSE(cache.update(1023, 1, &value, sizeof(value)));
    }
}
