#pragma once

#include "core/IndoorLowering.h"
#include "core/Project.h"

#include "game/outdoor/OutdoorMapData.h"

#include <filesystem>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What an event of an outdoor sketch tests and does, in the words an indoor project's wiring has for the same
// (schema/wiring.schema.json): `condition` (the lock: common.schema.json `condition`), `locked_text` and
// `else_effects` (when it does not hold), `effects`, `once` and `lua`. A plot's door, a door of `doors`, a part of
// a building, a structure and an entry of the sketch's `events` all say what they do with these words, and this
// class writes their Lua. What the shipped handlers do that the words are measured against is told at the top of
// OutdoorEvents.cpp.

// The node of a document at a path as issues write them ("districts[0].plots[3].doors[1]"); undefined when the
// path leads nowhere. Plans keep such paths, not nodes: a yaml-cpp node copied by assignment rewrites its tree.
YAML::Node sketchNodeAt(const YAML::Node &root, const std::string &path);

// A thing of the sketch that events change, by its id.
struct OutdoorEventTarget
{
    // decoration: a single decoration of `structures` (its picture is changed and hidden by `evt.SetSprite`).
    // model: the model of a structure or of a plot's building (its faces are hidden by facet bits, its textures
    // changed by `evt.SetTexture`).
    bool decoration = false;
    // It starts hidden (`hidden: true`).
    bool hidden = false;
    // `switch`: the structure whose show and hide this one follows (its faces carry that one's number); empty for
    // none.
    std::string follows;
    // An event shows or hides it.
    bool toggled = false;
    // Model: the textures events change, lower case; the faces of each carry a number of their own.
    std::set<std::string> swapped;
    // Where the sketch draws it, for messages.
    std::string path;
    // A scatter entry's `group`: the number its decorations carry and events change them by (the shipped maps'
    // decoration groups: Harmondale's 5, 6, 7 and 10 for the seasons); 0 for one the build numbers itself.
    int group = 0;
};

class OutdoorEventWords
{
public:
    // `assetRoot` (empty for none) is where the names an effect gives are looked up (decoration pictures).
    OutdoorEventWords(
        const Project &project,
        const std::filesystem::path &assetRoot,
        IdsLock &ids,
        std::vector<ProjectIssue> &issues);

    // Whether the node says anything a click runs beside a house, a map or a chest: effects or Lua.
    static bool hasActions(const YAML::Node &node);

    // A `condition` as one Lua expression that is true when it holds.
    std::string condition(const YAML::Node &condition, const std::string &path);

    // The steps of an `effects` list as lines of Lua.
    void effects(const YAML::Node &effects, const std::string &path, const std::string &indent,
        std::vector<std::string> &body);

    // The beginning of a handler: `once` (a map variable of its own, kept under `onceId`), then the lock: unless
    // `condition` holds, `else_effects`, `locked_text` and no more; then the item a condition consumes is taken; then
    // the lines of `lua_before` (what runs before the house, the map or the chest).
    void lock(const YAML::Node &node, const std::string &path, const std::string &onceId,
        std::vector<std::string> &body);

    // The end of a handler: `effects`, then the lines of `lua`.
    void actions(const YAML::Node &node, const std::string &path, std::vector<std::string> &body);

    // The things events change, by id; filled as conditions and effects are written, and with what starts hidden.
    const std::map<std::string, OutdoorEventTarget> &targets() const;

    // The number a decoration carries for `evt.SetSprite`; 0 for one no event names and that does not start
    // hidden.
    int decorationNumber(const std::string &id);

    // Gives a model's faces the numbers events change them by, and the bits of one that starts hidden. Call once
    // for every model of the map, after every handler is written.
    void applyToModel(const std::string &id, Game::OutdoorBModel &model);

    // The textures effects name as the new look of a face (`set_texture.to`), with the path that names each.
    const std::map<std::string, std::string> &namedTextures() const;

    // Actor groups an event shows or hides, and those the sketch starts hidden.
    const std::set<int> &shownGroups() const;

    // What the words leave to say once all is written: a thing that starts hidden and that nothing shows.
    void finish(std::vector<std::string> &warnings) const;

private:
    void add(const std::string &path, const std::string &message, const char *pCode = "event");
    void collectSwaps(const YAML::Node &node);
    int namedNumber(const YAML::Node &value, const char *pTable, const std::string &path);
    int mapVariable(const YAML::Node &value, const std::string &path);
    std::string selector(const YAML::Node &node, const std::string &path);
    OutdoorEventTarget *target(const YAML::Node &value, const std::string &path, const std::string &effect);
    std::vector<std::string> targetIds(const YAML::Node &value) const;
    void visibility(const YAML::Node &value, const std::string &path, const std::string &key, bool show,
        const std::string &indent, std::vector<std::string> &body);
    bool knownDecoration(const std::string &name);

    const Project &m_project;
    const std::filesystem::path m_assetRoot;
    IdsLock &m_ids;
    std::vector<ProjectIssue> &m_issues;
    std::map<std::string, OutdoorEventTarget> m_targets;
    std::map<std::string, std::string> m_namedTextures;
    std::set<int> m_actorGroups;
    std::set<int> m_shownGroups;
    std::set<int> m_hiddenGroups;
    bool m_decorationsLoaded = false;
    std::set<std::string> m_decorationNames;
};
}
