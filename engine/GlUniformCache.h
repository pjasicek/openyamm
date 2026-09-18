#pragma once

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <unordered_map>

namespace OpenYAMM
{

// Render-thread-only shadow of uniform values stored in GL program objects.
class GlUniformCache
{
public:
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
        assert(pData != nullptr && elementSize > 0 && elementSize <= 16 * sizeof(float));
        if (m_pCurrentValues == nullptr)
        {
            return true;
        }

        bool changed = false;
        const std::byte* pBytes = static_cast<const std::byte*>(pData);
        for (int index = 0; index < count; ++index)
        {
            Value& value = (*m_pCurrentValues)[location + index];
            if (value.size != elementSize || value.transpose != transpose
                || std::memcmp(value.bytes.data(), pBytes, elementSize) != 0)
            {
                std::memcpy(value.bytes.data(), pBytes, elementSize);
                value.size = elementSize;
                value.transpose = transpose;
                changed = true;
            }
            pBytes += elementSize;
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
    struct Value
    {
        std::array<std::byte, 16 * sizeof(float)> bytes;
        size_t size = 0;
        bool transpose = false;
    };

    using ProgramValues = std::unordered_map<uint32_t, Value>;
    std::unordered_map<uint32_t, ProgramValues> m_programs;
    ProgramValues* m_pCurrentValues = nullptr;
};

}
