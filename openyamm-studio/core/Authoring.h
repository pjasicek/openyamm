#pragma once

#include "core/Project.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What the browser's hand tools read from the core beyond the files (S5_BROWSER_EDITOR.md 3.8, 3.10, 3.12; S5b1
// part two): the map card as the game will read it, the fixes of the issues the core can fix by operations, and the
// source files as they stood at an entry of the history (History's "show as it was").

// One encounter slot of the map card (1 to 3) as the game reads it: project.yml map_stats.slots where the card
// writes it, else the row of its `reference` map in the asset root's engine/data_tables/map_stats.txt.
struct CardSlot
{
    int slot = 0;
    // The monster family's name and picture (the table's "Mon <n>" and "Mon<n> Pic" columns).
    std::string monster;
    std::string picture;
    // The table's difficulty ("Dif") and monsters per spawn point (" 3-5").
    std::string tier;
    std::string count;
    // The share of rest encounters, percent.
    std::string weight;
    // "written" (project.yml) or "reference" (the reference map's row).
    std::string source;
    std::string from;
};

// A column of the map card the game takes from the reference map's row because the card does not write it.
struct CardValue
{
    // The card's word for it (treasure_level, encounter_chance ...).
    std::string name;
    std::string value;
    std::string from;
};

struct MapCard
{
    std::vector<CardSlot> slots;
    std::vector<CardValue> fromReference;
    // Why the reference row could not be read (no asset root, no such map in the table); empty when it was.
    std::string referenceProblem;
};

MapCard resolveMapCard(const Project &project, const std::filesystem::path &assetRoot);

// A fix of an issue: what to do, as operations of edit.apply (a list of op objects).
struct IssueFix
{
    std::string label;
    YAML::Node ops;
};

// The fixes the core offers for an issue (none for most): a reference to an id the project lacks taken out of its
// list or dropped (or the object removed when it cannot stand without it), a word on the wrong kind dropped, an
// undeclared map variable declared, the party start set in the first room. S5b2: a missing id's obvious target named
// instead (the one id of its kind nearest in spelling within two letters, else the only one of its kind); an outline
// that runs clockwise reversed or its repeated points dropped, a path's repeated point and a height point given twice
// dropped (only when the change makes it stand); an opening wider than the shared wall narrowed or made `full`; a
// thing outside its room given the room it stands in or moved inside its own.
std::vector<IssueFix> issueFixes(const Project &project, const ProjectIssue &issue);

// The source files of a project as they stood after (`before` false) or before (`before` true) the history entry
// `sequence`: the current files, each taken back through the entries after it. A file that did not exist then is
// absent. False with a message when the history cannot be read.
bool sourceTextsAtEntry(
    const std::filesystem::path &projectRoot,
    const Project &current,
    int sequence,
    bool before,
    std::map<std::string, std::string> &texts,
    std::string &errorMessage);

// A project made from texts (file name to text), parsed as loadProject parses files. False when a text is not YAML.
bool projectFromTexts(
    const std::filesystem::path &root,
    const std::map<std::string, std::string> &texts,
    Project &project,
    std::string &errorMessage);
}
