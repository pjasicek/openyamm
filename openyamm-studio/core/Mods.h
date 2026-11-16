#pragma once

#include "core/Json.h"

#include <array>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Named mods and sharing (devdocs/map_studio/S6_PLAN.md item M), the studio's side. A mod is a folder:
//
//   <mod>/mod.yml        the manifest (schema/mod.schema.json): id, name, version, author, worlds, the maps it brings
//                        or overlays, the table rows it adds, the map numbers it uses
//   <mod>/engine/...     files as the game's packages hold them (none yet but tables the game reads whole)
//   <mod>/worlds/<w>/... maps, scenes, scripts, cinematics, overlays
//   <mod>/tables/<table>.override.txt, <table>.append.txt
//                        the rows of engine tables it changes (cells, the ruleset's override format) and adds
//
// The game today mounts one merged `<install>/mods` folder (AssetFileSystem::mountMods), where a table file replaces
// the whole table. `merged` installs write the mod's files there and compose each table from the asset root's and the
// installed mods' rows, so two mods that add map rows do not clash; a record of what is installed
// (`<mods>/studio_mods.yml`, with a copy of each mod in `<mods>/studio_mods/<id>/`) lets a mod be switched off and on
// again (its files taken out, the tables composed anew). `named` installs write `<mods>/<id>/` and `<mods>/enabled.yml`,
// the layout of the game's named mods (devdocs/NAMED_MODS.md): the game composes their table rows itself.

struct ModPackRequest
{
    std::vector<std::filesystem::path> projects;
    std::filesystem::path assetRoot;
    std::filesystem::path out;
    std::string id;
    std::string name;
    std::string version = "1.0";
    std::string author;
    std::string description;
    // The map numbers the mod declares as its own (mod.yml `idRanges.maps`): its new maps' map_stats ids lie in it,
    // and a new project of the mod takes the first free one (proposeMapNumber). None: no range declared.
    std::optional<std::array<int, 2>> mapRange;
    // Build each project first (oymap mod pack, mod.pack): else each must have been built.
    bool build = false;
};

struct PackedMap
{
    std::string file;
    std::string world;
    // new or overlay.
    std::string kind;
    std::string project;
    // A new map's map_stats number (0: an overlay).
    int number = 0;
};

struct ModPackResult
{
    std::filesystem::path folder;
    std::vector<std::string> files;
    std::vector<PackedMap> maps;
    // The engine tables whose rows it carries.
    std::vector<std::string> tables;
    std::vector<std::string> warnings;
};

// Packs the projects' builds (`<project>/build`, made first when `build`) into `<out>/<id>/`.
bool packMod(const ModPackRequest &request, ModPackResult &result, std::string &errorMessage);

struct ModInstallResult
{
    std::vector<std::string> files;
    std::vector<std::string> tables;
    std::vector<std::string> warnings;
};

// Installs a mod folder into `modsRoot`: `layout` merged (what the game mounts today) or named.
bool installMod(const std::filesystem::path &modFolder, const std::filesystem::path &modsRoot,
    const std::filesystem::path &assetRoot, const std::string &layout, ModInstallResult &result,
    std::string &errorMessage);

// Switches an installed mod off (its files leave the merged folder, the tables are composed without its rows) or on
// again; merged installs only.
bool setModEnabled(const std::string &id, bool enabled, const std::filesystem::path &modsRoot,
    const std::filesystem::path &assetRoot, ModInstallResult &result, std::string &errorMessage);

// The mods of a mods folder (merged and named), with their state, as JSON members.
void writeModList(const std::filesystem::path &modsRoot, JsonWriter &writer);

// A map number for a new project (S6_PLAN.md item M, S5_BROWSER_EDITOR.md 6.3: "a range table in S6's world and mod
// manifests lets the studio propose a free number"): the first number of a range that no map takes. The range is the
// mod's (`mod`: its mod.yml `idRanges.maps`, in `modsRoot`), else the world's (world.yml `idRanges.maps`), else the
// studio's own band. Taken: the asset root's map_stats rows, the map numbers of every mod in `modsRoot` (merged and
// named installs, and packed mods), and the projects' map cards.
struct MapNumberRequest
{
    std::filesystem::path assetRoot;
    std::string world;
    std::filesystem::path modsRoot;
    std::string mod;
    std::vector<std::filesystem::path> projects;
};

struct MapNumberProposal
{
    int number = 0;
    std::array<int, 2> range = {};
    // "mod:<id>", "world:<world>" or "studio".
    std::string from;
    // The numbers of the range already taken, ascending.
    std::vector<int> taken;
    // Declared ranges that overlap (two mods, or a mod and the world).
    std::vector<std::string> warnings;
};

// The studio's band when neither a mod nor the world declares a range (project.new's old default is its start).
constexpr std::array<int, 2> StudioMapNumbers = {9400, 9999};

// False with a reason when the mod is not in `modsRoot`, declares no map range, or the range is full.
bool proposeMapNumber(const MapNumberRequest &request, MapNumberProposal &proposal, std::string &errorMessage);

// A tab table's text with a mod's changed cells ("key<TAB>column<TAB>value", column `#<index>`) and added rows applied.
std::string applyTableRows(const std::string &baseText, const std::string &overrideText, const std::string &appendText);

// The rows `changedText` changes or adds against `baseText` (keyed by their first cell): the override and append
// texts of a mod's table.
void diffTableRows(const std::string &baseText, const std::string &changedText, std::string &overrideText,
    std::string &appendText);
}
