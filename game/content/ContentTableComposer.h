#pragma once

#include "game/content/ContentManifest.h"

#include <cstddef>
#include <string>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
struct ItemTableContributionRows
{
    std::string packageId;
    ContentIdRangeDefinition idRange;
    size_t sourceIdColumn = 0;
    size_t canonicalIdColumn = 0;
    std::vector<std::vector<std::string>> rows;
};

struct KeyedTableContributionRows
{
    std::string packageId;
    ContentIdRangeDefinition idRange;
    size_t idColumn = 0;
    std::vector<std::vector<std::string>> rows;
};

// Rows a package adds to a table keyed by a map file name (outdoor_travels, map_navigation, house_exits).
struct MapKeyedTableContributionRows
{
    std::string packageId;
    // The package's own maps (lowercase file names): its rows may key only these.
    std::unordered_set<std::string> mapFileNames;
    std::vector<std::vector<std::string>> rows;
};

bool composeItemTableRows(
    const std::vector<std::vector<std::string>> &baseRows,
    const std::vector<ItemTableContributionRows> &contributions,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage
);

// A ruleset Override (RulesetDefinition.h): patchRows is a "key<TAB>column<TAB>value" table whose first row is the
// header. Each line sets one cell of the single base row whose keyColumn cell is the key; the column is a header
// name from the base table's headerRow or "#<index>". Fails on an unknown or repeated key or an ambiguous column.
// A keyColumn of RowNumberKeyColumn keys rows by their zero-based row number in the file instead of a cell; a patch
// key past the last row adds rows up to it.
inline constexpr size_t RowNumberKeyColumn = SIZE_MAX;

bool applyTableCellOverrides(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &patchRows,
    size_t keyColumn,
    size_t headerRow,
    std::string &errorMessage
);

// Adds whole rows at the end of a table. With a key column, an added key must be new.
bool appendTableRows(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &appendedRows,
    size_t keyColumn,
    size_t headerRow,
    std::string &errorMessage
);

// Adds columns at the right of a table. The first row of appendedColumns names them (its key cell is ignored); every
// other row fills them for the base row whose keyColumn cell is its key, and rows it does not list get empty cells.
// Fails on a name the header already has, an unknown or repeated key, or a row with more cells than names.
bool appendTableColumns(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &appendedColumns,
    size_t keyColumn,
    size_t headerRow,
    std::string &errorMessage
);

bool composeKeyedAppendTableRows(
    const std::vector<std::vector<std::string>> &baseRows,
    const std::vector<KeyedTableContributionRows> &contributions,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage,
    size_t baseIdColumn = 0
);

// Appends the contributions' rows to a table keyed by a map file name in keyColumn. A contributed row whose key names
// an .odm or .blv map must name one of its package's maps that no base or earlier row keys (compared without case);
// its other rows (headers, notes) are left out.
bool composeMapKeyedAppendTableRows(
    const std::vector<std::vector<std::string>> &baseRows,
    const std::vector<MapKeyedTableContributionRows> &contributions,
    size_t keyColumn,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage
);
}
