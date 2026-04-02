#pragma once

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class StrTable
{
public:
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    const std::vector<std::string> &getEntries() const;
    std::optional<std::string> get(size_t index) const;

private:
    std::vector<std::string> m_entries;
};
}
