#include "engine/TextTable.h"

#include <cstddef>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
void finalizeCell(std::vector<std::string> &row, std::string &currentCell)
{
    row.push_back(currentCell);
    currentCell.clear();
}

void finalizeRow(
    std::vector<std::vector<std::string>> &rows,
    std::vector<std::string> &currentRow,
    std::string &currentCell,
    bool forceEmptyRow
)
{
    if (!currentCell.empty() || !currentRow.empty() || forceEmptyRow)
    {
        finalizeCell(currentRow, currentCell);
        rows.push_back(currentRow);
        currentRow.clear();
    }
}

// A leading quote opens a quoted cell only when its closing quote comes before the next tab. Quoted cells may span
// lines but never hold a tab, while truncated cells such as `"Journal Entry, 2nd Janua` in scroll.txt never close
// and would otherwise swallow the following records.
bool hasClosingQuoteBeforeTab(const std::string &contents, size_t begin)
{
    for (size_t index = begin; index < contents.size(); ++index)
    {
        if (contents[index] == '\t')
        {
            return false;
        }

        if (contents[index] == '"')
        {
            if (index + 1 < contents.size() && contents[index + 1] == '"')
            {
                ++index;
                continue;
            }

            return true;
        }
    }

    return false;
}
}

std::optional<TextTable> TextTable::parseTabSeparated(const std::string &contents)
{
    TextTable table;
    std::vector<std::string> currentRow;
    std::string currentCell;
    bool isInsideQuotes = false;

    for (size_t index = 0; index < contents.size(); ++index)
    {
        const char character = contents[index];

        if (character == '"')
        {
            if (isInsideQuotes && index + 1 < contents.size() && contents[index + 1] == '"')
            {
                currentCell.push_back('"');
                ++index;
            }
            else if (isInsideQuotes)
            {
                isInsideQuotes = false;
            }
            else if (currentCell.empty() && hasClosingQuoteBeforeTab(contents, index + 1))
            {
                isInsideQuotes = true;
            }
            else
            {
                currentCell.push_back(character);
            }

            continue;
        }

        if (character == '\r')
        {
            continue;
        }

        if (character == '\t' && !isInsideQuotes)
        {
            finalizeCell(currentRow, currentCell);
            continue;
        }

        if (character == '\n' && !isInsideQuotes)
        {
            finalizeRow(table.m_rows, currentRow, currentCell, true);
            continue;
        }

        currentCell.push_back(character);
    }

    if (isInsideQuotes)
    {
        return std::nullopt;
    }

    finalizeRow(table.m_rows, currentRow, currentCell, false);

    if (table.m_rows.empty())
    {
        return std::nullopt;
    }

    return table;
}

size_t TextTable::getRowCount() const
{
    return m_rows.size();
}

const std::vector<std::string> &TextTable::getRow(size_t index) const
{
    return m_rows.at(index);
}
}
