#pragma once

#include "core/Project.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <functional>
#include <optional>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A map's own monster relations (objects.yml `relations` indoors, sketch.yml `relations` outdoors): rows the build
// sets by an event of its own on entering the map (evt.SetMonsterRelation, as the MMerge and MM9 maps' scripts do),
// and the check that tells an author where the monster table (engine/data_tables/hostile.txt) makes a map's monsters
// peaceful to the party or set on each other where the project has not said so.

// One side of a relation as the game's script takes it: a monster kind's number, an actor group, or the party (both
// 0).
struct MonsterRelationSide
{
    int monster = 0;
    int group = 0;

    bool party() const
    {
        return monster == 0 && group == 0;
    }
};

// One evt.SetMonsterRelation of the event: `of`'s relation toward `toward` (0 friendly to 4 hostile at any distance).
struct MonsterRelationRow
{
    MonsterRelationSide of;
    MonsterRelationSide toward;
    int relation = 0;
    // The entry of `relations` it comes from ("relations[2]").
    std::string path;
};

// Finds a monster kind's number from a scalar of the project (its number or name); nothing, with an issue, when the
// table has none.
using MonsterNumberLookup = std::function<std::optional<int>(const YAML::Node &value, const std::string &path)>;

// The rows of a `relations` list of `file`, in order (an entry with `both_ways` gives each kind's row and then the
// other side's toward it). Entries that are wrong are left out with an issue that says how to write them.
std::vector<MonsterRelationRow> readMonsterRelations(
    const YAML::Node &relations,
    const std::string &file,
    const MonsterNumberLookup &monsterNumber,
    std::vector<ProjectIssue> &issues);

// The event's lines: evt.SetMonsterRelation(<of>, <toward>, <relation>) for each row.
std::vector<std::string> monsterRelationLines(const std::vector<MonsterRelationRow> &rows);

// The monsters of a map as the hostility check sees them.
struct MapMonsters
{
    // The monster family (the picture's name without its tier letter) of encounter slots 1 to 3, "" for none:
    // project.yml map_stats.slots over the row map_stats.reference names (readMapSlots).
    std::array<std::string, 3> slots;
    // The families of the reference row's own slots: a project that rebuilds a shipped map keeps those as shipped.
    std::vector<std::string> shippedSlots;

    // A monster spawn point: the slot it spawns from, its fixed tier ('A' to 'C', or 0 for the slot's mix), its group.
    struct Spawn
    {
        std::string id;
        int slot = 1;
        char tier = '\0';
        int group = 0;
    };

    std::vector<Spawn> spawns;

    // A placed monster: its kind's number, group and `hostile` word (none when not given).
    struct Placed
    {
        std::string id;
        int monster = 0;
        int group = 0;
        std::optional<bool> hostile;
    };

    std::vector<Placed> placed;
    // Groups the project makes peaceful (`hostile: false`).
    std::set<int> peacefulGroups;
    std::vector<MonsterRelationRow> relations;
};

// Fills `monsters.slots` and `shippedSlots` from project.yml (`card`) and engine/data_tables/map_stats.txt's rows.
void readMapSlots(
    const YAML::Node &card,
    const std::vector<std::vector<std::string>> &mapStatsRows,
    MapMonsters &monsters);

// What the build warns of, with the fix in `file` (objects.yml or sketch.yml):
// - a slot whose kinds hostile.txt has friendly to the party (they leave the party alone) and that the project has
//   not set (`relations` toward the party); the reference row's own slots are left as shipped;
// - placed monsters of a kind hostile.txt has friendly to the party, without `hostile`, while other monsters of that
//   kind are hostile in the map;
// - two kinds of the map that are both hostile to the party and that hostile.txt sets on each other, with no
//   relation of the project between them (unless one is a shipped slot's kind);
// - a relation of a group toward the party, which the game does not use (it sets the party's foes by kind).
// Nothing without the monster and relation tables (`monsterRows`, `relationRows` as parseTableRows reads them).
std::vector<std::string> monsterHostilityWarnings(
    const MapMonsters &monsters,
    const std::vector<std::vector<std::string>> &monsterRows,
    const std::vector<std::vector<std::string>> &relationRows,
    const std::string &file);
}
