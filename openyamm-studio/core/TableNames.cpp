#include "core/TableNames.h"

#include "core/Json.h"

#include <algorithm>
#include <cctype>
#include <charconv>

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}
}

std::optional<int> cellNumber(const std::vector<std::string> &row, size_t column)
{
    if (column >= row.size() || row[column].empty())
    {
        return std::nullopt;
    }

    int number = 0;

    for (const char character : row[column])
    {
        if (character == ',')
        {
            continue;
        }

        if (character < '0' || character > '9' || number > 100000000)
        {
            return std::nullopt;
        }

        number = number * 10 + (character - '0');
    }

    return number;
}

const std::vector<std::string> *namedTableRow(
    const std::vector<std::vector<std::string>> &rows,
    const YAML::Node &value,
    const std::vector<size_t> &nameColumns,
    std::optional<int> cardNumber,
    const char *pCardTable,
    const std::string &what,
    const std::string &tableFile,
    const std::string &file,
    const std::string &path,
    std::vector<ProjectIssue> &issues)
{
    std::optional<int> wantedNumber = cardNumber;

    if (value && value.IsScalar() && classifyScalar(value) == ScalarKind::Integer)
    {
        const std::string &text = value.Scalar();
        double parsed = 0.0;
        const char *pBegin = text.data() + ((!text.empty() && text[0] == '+') ? 1 : 0);
        std::from_chars(pBegin, text.data() + text.size(), parsed);
        wantedNumber = static_cast<int>(parsed);
    }

    if (!value || !value.IsScalar())
    {
        issues.push_back({file, path, "name the " + what + " by its number or its name in " + tableFile, "schema"});
        return nullptr;
    }

    if (rows.empty())
    {
        issues.push_back({file, path, "a placed " + what + " needs the table " + tableFile + ": pass --assets <asset "
            "root> to the build", "reference"});
        return nullptr;
    }

    if (wantedNumber)
    {
        for (const std::vector<std::string> &row : rows)
        {
            if (cellNumber(row, 0) == wantedNumber && *wantedNumber > 0)
            {
                return &row;
            }
        }

        issues.push_back({file, path, "there is no " + what + " number " + std::to_string(*wantedNumber) + " in "
            + tableFile, "reference"});
        return nullptr;
    }

    const std::string wanted = lowerText(value.Scalar());

    for (const size_t column : nameColumns)
    {
        std::vector<const std::vector<std::string> *> found;

        for (const std::vector<std::string> &row : rows)
        {
            if (cellNumber(row, 0).value_or(0) > 0 && column < row.size() && lowerText(row[column]) == wanted)
            {
                found.push_back(&row);
            }
        }

        if (found.size() == 1)
        {
            return found.front();
        }

        if (found.size() > 1)
        {
            std::string listed;

            for (size_t index = 0; index < found.size() && index < 12; ++index)
            {
                const std::vector<std::string> &row = *found[index];
                listed += (listed.empty() ? "" : ", ") + row[0];

                // A second name column tells the rows apart (a monster's picture name).
                if (nameColumns.size() > 1 && nameColumns[1] < row.size() && nameColumns[1] != column)
                {
                    listed += " (" + row[nameColumns[1]] + ")";
                }
            }

            issues.push_back({file, path, std::to_string(found.size()) + " rows of " + tableFile + " are named '"
                + value.Scalar() + "': " + listed + (found.size() > 12 ? ", ..." : "") + ". Name the " + what
                + " by its number" + (nameColumns.size() > 1 ? " or by the name in brackets" : ""), "reference"});
            return nullptr;
        }
    }

    issues.push_back({file, path, "there is no " + what + " named '" + value.Scalar() + "' in " + tableFile
        + (pCardTable != nullptr ? std::string(" or in project.yml ") + pCardTable : std::string())
        + " (oymap assets does not list " + what + "s: look the name up in the table's Name column)", "reference"});
    return nullptr;
}
}
