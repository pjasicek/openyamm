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

bool hasUnclosedQuotedField(const std::string &contents)
{
    bool isInsideQuotes = false;

    for (size_t index = 0; index < contents.size(); ++index)
    {
        if (contents[index] != '"')
        {
            continue;
        }

        if (isInsideQuotes && index + 1 < contents.size() && contents[index + 1] == '"')
        {
            ++index;
            continue;
        }

        isInsideQuotes = !isInsideQuotes;
    }

    return isInsideQuotes;
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
            else
            {
                isInsideQuotes = !isInsideQuotes;
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

    if (hasUnclosedQuotedField(contents))
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
