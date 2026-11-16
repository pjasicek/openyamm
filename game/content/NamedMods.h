#pragma once

#include "engine/AssetFileSystem.h"
#include "game/content/ContentManifest.h"

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Named mods (devdocs/NAMED_MODS.md): a mod is a folder <user data>/mods/<id>/ with its manifest mod.yml (the Map
// Studio's openyamm-studio/schema/mod.schema.json), its files under engine/ and worlds/<world>/ as the game's packages
// hold them, and the rows it changes in engine tables under tables/. mods/enabled.yml lists the mods that are on, in
// the order they mount; a mod it does not list is off. The game reads the folder once, at its start.
inline constexpr const char *NamedModManifestFileName = "mod.yml";
inline constexpr const char *EnabledModListFileName = "enabled.yml";
inline constexpr uint32_t NamedModManifestFormat = 1;

struct NamedModMap
{
    std::string file;
    std::string world;
    // "new" or "overlay".
    std::string kind;
};

// The rows a mod changes in one engine table, engine/data_tables/<table>: an override file in the rulesets' format (a
// "key<TAB>column<TAB>value" header, then one changed cell per line; the key is a row's first cell, the column
// "#<index>" or a name from the table's first row) and an append file of whole rows in the table's own layout, each
// with a key the table does not have. Both paths are inside the mod's folder; their texts are read with the manifest.
struct NamedModTable
{
    std::string table;
    std::string overridePath;
    std::string appendPath;
    std::string overrideText;
    std::string appendText;
};

struct NamedModManifest
{
    std::string id;
    std::string name;
    std::string version;
    std::string author;
    std::string description;
    std::vector<std::string> worlds;
    std::vector<NamedModMap> maps;
    std::vector<NamedModTable> tables;
    // The map_stats numbers its new maps take (`map_numbers`).
    std::vector<uint32_t> mapNumbers;
    // The ids it declares as its own by domain (`idRanges`, as world.yml and ruleset.yml declare theirs): `maps`, the
    // map_stats numbers of its new maps.
    std::vector<ContentIdRangeDefinition> idRanges;
};

// Lower case letters, digits and underscores, and not a name the mods folder uses itself (engine, worlds).
bool isValidNamedModId(const std::string &id);

// Parses mod.yml; `folderName` is the folder it was found in, which must be its id. The table texts are not read.
std::optional<NamedModManifest> parseNamedModManifest(
    const std::string &yamlText,
    const std::string &folderName,
    std::string &errorMessage);

// enabled.yml: `format: 1` and `enabled: [ids]` in mount order (the Map Studio's `oymap mod install --layout named`
// writes it). Repeated ids are kept once, at their first place.
std::optional<std::vector<std::string>> parseEnabledModList(const std::string &yamlText, std::string &errorMessage);
std::string formatEnabledModList(const std::vector<std::string> &ids);

enum class NamedModState
{
    // Installed, not in the enabled list.
    Off,
    // Mounted, its rows composed.
    On,
    // In the enabled list but not mounted: its manifest is invalid, or it clashes (`reason`).
    Refused,
};

struct NamedModEntry
{
    // The folder's name.
    std::string id;
    std::optional<NamedModManifest> manifest;
    NamedModState state = NamedModState::Off;
    std::string reason;
};

// A declarer of id ranges the mods must keep clear of: a world (world.yml) or a ruleset (ruleset.yml).
struct NamedModRangeOwner
{
    std::string name;
    std::vector<ContentIdRangeDefinition> ranges;
};

struct NamedModCatalog
{
    std::filesystem::path modsRoot;
    // The enabled list as read; empty when enabled.yml is missing or malformed (enabledListError).
    std::vector<std::string> enabledIds;
    std::string enabledListError;
    // Every installed mod (a folder with mod.yml), by id.
    std::vector<NamedModEntry> mods;
    // Ids the enabled list names that are not installed.
    std::vector<std::string> missingIds;
    // The mods that are on, in the enabled list's order: each one mounts in front of those before it, and its rows
    // apply after theirs.
    std::vector<std::string> mountOrder;

    const NamedModEntry *find(const std::string &id) const;
    // The manifests of mountOrder, in that order.
    std::vector<NamedModManifest> mountedManifests() const;
};

// Reads a mods folder: each folder with mod.yml (its manifest and table files; a manifest or a table file that cannot
// be read refuses the mod) and enabled.yml. The mods are all Off; resolveNamedMods decides. A missing folder reads as
// an empty catalog without touching the disk further.
NamedModCatalog readNamedModCatalog(const std::filesystem::path &modsRoot);

// Turns the enabled mods On in the list's order, unless one is refused: an invalid manifest; a map number outside its
// own `maps` range; an id range overlapping an owner's (a world, a ruleset) or an earlier mod's; a map number another
// mod already takes or declares. The earlier mod in the list keeps its place, the later one is refused.
void resolveNamedMods(NamedModCatalog &catalog, const std::vector<NamedModRangeOwner> &owners);

// Takes a mod that is On off its mount order, as Refused for `reason`.
void refuseNamedMod(NamedModCatalog &catalog, const std::string &id, const std::string &reason);

// Applies a mod's rows of one table: its overrides, then its appended rows (key column 0, header row 0). False with
// the reason, and the rows as they were, when a key is unknown or repeated or an added key exists already.
bool applyNamedModTable(
    std::vector<std::vector<std::string>> &rows,
    const NamedModTable &table,
    std::string &errorMessage);

// Every mod's rows of the table at `tableVirtualPath` (engine/data_tables/<table>) in the mods' order. A mod whose
// rows do not apply is left out of this table with a line in `errors` ("<id>: <reason>").
void applyNamedModTables(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<NamedModManifest> &mods,
    const std::string &tableVirtualPath,
    std::vector<std::string> &errors);

// At the game's start: reads the file system's mods folder (InstalledContentOptions::modsRoot), refuses the enabled
// mods that clash with the mounted worlds, the available rulesets or each other, mounts the others
// (AssetFileSystem::setNamedMods), then refuses any whose table rows do not apply to the tables as mounted and mounts
// again without it. Logs each decision. Without a mods folder or an enabled mod nothing is mounted again. False only
// when mounting fails.
bool mountNamedMods(Engine::AssetFileSystem &assetFileSystem, NamedModCatalog &catalog);

// Switches a mod on (appended to the end of enabled.yml) or off (taken out of it); the folder must hold it when it is
// switched on. False with the reason, and nothing written, when enabled.yml is malformed or the mod is not installed.
bool setNamedModEnabled(
    const std::filesystem::path &modsRoot,
    const std::string &id,
    bool enabled,
    std::string &errorMessage);
}
