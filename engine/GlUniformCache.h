#pragma once

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <unordered_map>
#include <vector>

namespace OpenYAMM
{

// Render-thread-only shadow of uniform values stored in GL program objects.
// bgfx re-commits every uniform of a program on each draw that sets any, so this check runs for every array element
// of every draw: values are kept in a table indexed by location, never in a hash map per element.
class GlUniformCache
{
public:
    // Locations past this are not shadowed and always upload. Drivers number locations densely from zero.
    static constexpr size_t MaxShadowedLocations = 4096;

    GlUniformCache() = default;
    GlUniformCache(const GlUniformCache&) = delete;
    GlUniformCache& operator=(const GlUniformCache&) = delete;

    void saveCurrentProgram(uint32_t program)
    {
        m_pCurrentValues = program == 0 ? nullptr : &m_programs[program];
    }

    // Array elements occupy consecutive uniform locations, including matrix arrays.
    // Track elements separately so shorter and overlapping uploads remain correct.
    bool update(uint32_t location, int count, const void* pData, size_t elementSize, bool transpose = false)
    {
        if (location == UINT32_MAX || count <= 0)
        {
            return false;
        }
        assert(pData != nullptr && elementSize > 0 && elementSize <= MaxElementSize);
        if (m_pCurrentValues == nullptr)
        {
            return true;
        }

        const size_t end = size_t(location) + size_t(count);
        if (end > MaxShadowedLocations)
        {
            return true;
        }
        if (m_pCurrentValues->size() < end)
        {
            m_pCurrentValues->resize(end);
        }

        bool changed = false;
        const std::byte* pBytes = static_cast<const std::byte*>(pData);
        Value* pValue = m_pCurrentValues->data() + location;
        const uint8_t state = uint8_t(elementSize | (transpose ? TransposeBit : 0));
        for (int index = 0; index < count; ++index, ++pValue, pBytes += elementSize)
        {
            if (pValue->state != state || std::memcmp(pValue->bytes.data(), pBytes, elementSize) != 0)
            {
                std::memcpy(pValue->bytes.data(), pBytes, elementSize);
                pValue->state = state;
                changed = true;
            }
        }
        return changed;
    }

    void invalidateProgram(uint32_t program)
    {
        const auto it = m_programs.find(program);
        if (it == m_programs.end())
        {
            return;
        }
        if (m_pCurrentValues == &it->second)
        {
            m_pCurrentValues = nullptr;
        }
        m_programs.erase(it);
    }

    void clear()
    {
        m_pCurrentValues = nullptr;
        m_programs.clear();
    }

private:
    static constexpr size_t MaxElementSize = 16 * sizeof(float);
    static constexpr uint8_t TransposeBit = 0x80;

    struct Value
    {
        std::array<std::byte, MaxElementSize> bytes;
        // Element size in bytes, with TransposeBit for a transposed matrix; zero: nothing uploaded yet.
        uint8_t state = 0;
    };

    // Indexed by uniform location. The map keeps each program's table at one address while others are added.
    using ProgramValues = std::vector<Value>;
    std::unordered_map<uint32_t, ProgramValues> m_programs;
    ProgramValues* m_pCurrentValues = nullptr;
};

}
