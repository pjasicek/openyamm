#pragma once

#include "core/Project.h"

#include <yaml-cpp/yaml.h>

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A cell of a table row as a whole number (digits with thousands separators, as the tables write hit points);
// nothing when it is not one.
std::optional<int> cellNumber(const std::vector<std::string> &row, size_t column);

// The row of a numbered table (first cell its number, rows as parseTableRows gives them) that a project value names:
// the number itself (or `cardNumber`, the number a table of project.yml gives the name, `pCardTable`), or a name
// found in one of `nameColumns` (first column that has it wins; upper and lower case are the same). A name that
// several rows of that column share is refused with the rows it could mean. Problems are issues of `file` at `path`.
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
    std::vector<ProjectIssue> &issues);
}
