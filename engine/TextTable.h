#pragma once

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
class TextTable
{
public:
    static std::optional<TextTable> parseTabSeparated(const std::string &contents);

    size_t getRowCount() const;
    const std::vector<std::string> &getRow(size_t index) const;

private:
    std::vector<std::vector<std::string>> m_rows;
};
}
