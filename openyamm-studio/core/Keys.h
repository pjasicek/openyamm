#pragma once

#include "core/Schema.h"

#include <yaml-cpp/yaml.h>

#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Keys of sub-objects (S5_BROWSER_EDITOR.md 2.6 item 2, format 1 of rooms.yml and objects.yml). A list of things a
// person selects or pins on their own (a room's pillars, platforms, levels; a mover's parts) is marked in the schema
// with `x-key: <field>` and `x-key-prefix: <kind>`; each item's key is unique within its list. Keys are optional in
// files: an item without one reads as the key the core gives it (the prefix and the item's place in the list,
// counted from 1: `pillar2`), and the core writes it on its next write of the file. Top-level lists carry
// `x-key: id`: their items are addressed by their ids, as before.

// What the schema says of a list: the field its items are keyed by and the prefix of a derived key (empty: the list
// is not keyed; "id" with no prefix: a list of objects with ids).
struct ListKey
{
    std::string field;
    std::string prefix;

    // `x-key: '#'` (rows by their place: a timeline's shots and cues) and `x-key: false` (rows not selectable) key
    // nothing.
    bool keyed() const
    {
        return !field.empty() && field != "#" && field != "false";
    }
};

// The list key of an array schema (resolved), or none.
ListKey listKeyOf(const YAML::Node &arraySchema);

// The key of each item of a keyed list, in order: the item's own (`field`) where it has one, otherwise the derived
// key (`prefix` and the place from 1; the next free number where that one is taken by an item's own key).
std::vector<std::string> itemKeys(const YAML::Node &list, const ListKey &key);

// Where `key` is in the list (its position), or -1.
long findKeyed(const YAML::Node &list, const ListKey &key, const std::string &wanted);

// A schema walk alongside a document: the schema node of a map's property and of a list's items, $refs followed.
// `fileName` follows the references across files.
YAML::Node propertySchema(const SchemaSet &schemas, const YAML::Node &mapSchema, const std::string &property,
    std::string &fileName);
YAML::Node itemsSchema(const SchemaSet &schemas, const YAML::Node &arraySchema, std::string &fileName);

// Writes the missing keys of every keyed sub-object list of a document of `schemaFile` ("rooms.schema.json"): each
// gets the key it reads as. Returns how many were written. Lists keyed by `id` (the top-level collections) are left
// alone: an id is the author's to give. `pFilled` collects "rooms[3].pillars[0]: pillar1".
size_t fillMissingKeys(YAML::Node &document, const std::string &schemaFile, std::vector<std::string> *pFilled = nullptr);

// Whether a file's schema has keyed sub-object lists (rooms.yml, objects.yml): the core writes `format: 1` into it.
bool fileHasKeyedLists(const std::string &schemaFile);

// The keys of every keyed sub-object list of a document, as full addresses (`room:hall/pillars/pillar2`, or
// `rooms.yml#room:entry/...` is the caller's to add): for pins, provenance and the inspector.
std::vector<std::string> subObjectAddresses(const YAML::Node &document, const std::string &schemaFile);
// Only the sub-objects whose key is written in the file (not derived).
std::vector<std::string> writtenKeyAddresses(const YAML::Node &document, const std::string &schemaFile);
}
