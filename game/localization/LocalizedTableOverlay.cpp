#include "game/localization/LocalizedTableOverlay.h"

#include <yaml-cpp/yaml.h>

#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
bool applyLocalizedTableOverlay(
    std::string_view contents,
    std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage
)
{
    errorMessage.clear();

    YAML::Node root;
    try
    {
        root = YAML::Load(std::string(contents));
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    const YAML::Node translatedRows = root["rows"];
    if (!translatedRows || !translatedRows.IsMap())
    {
        errorMessage = "missing rows map";
        return false;
    }

    std::unordered_map<std::string, size_t> rowIndexByKey;
    std::unordered_set<std::string> duplicateKeys;
    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        if (rows[rowIndex].empty() || rows[rowIndex][0].empty())
        {
            continue;
        }

        const std::string &key = rows[rowIndex][0];
        if (!rowIndexByKey.emplace(key, rowIndex).second)
        {
            duplicateKeys.insert(key);
        }
    }

    try
    {
        for (const auto &translatedRow : translatedRows)
        {
            const std::string key = translatedRow.first.as<std::string>();
            if (duplicateKeys.contains(key))
            {
                errorMessage = "ambiguous row key '" + key + "'";
                return false;
            }

            const std::unordered_map<std::string, size_t>::const_iterator rowIterator = rowIndexByKey.find(key);
            if (rowIterator == rowIndexByKey.end())
            {
                errorMessage = "unknown row key '" + key + "'";
                return false;
            }
            if (!translatedRow.second.IsMap())
            {
                errorMessage = "columns for row '" + key + "' must be a map";
                return false;
            }

            std::vector<std::string> &row = rows[rowIterator->second];
            for (const auto &translatedColumn : translatedRow.second)
            {
                const size_t columnIndex = translatedColumn.first.as<size_t>();
                if (columnIndex >= row.size())
                {
                    errorMessage = "column out of range for row '" + key + "'";
                    return false;
                }
                row[columnIndex] = translatedColumn.second.as<std::string>();
            }
        }
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    return true;
}
}
