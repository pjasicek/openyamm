#pragma once

#include "engine/AssetFileSystem.h"

#include <cstddef>
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace YAML
{
class Node;
}

namespace OpenYAMM::Game
{
struct WorldStartDefinition
{
    std::string mapFileName;
    std::string introMovie;
};

struct WorldQBitDefinition
{
    uint32_t begin = 0;
    uint32_t end = 0;
    std::string mapping;
    bool declared = false;
};

struct WorldPartyMovementDefinition
{
    float eyeHeight = 0.0f;
    float collisionRadius = 0.0f;
    float collisionHeight = 0.0f;
    float maxStepHeight = 128.0f;
    bool declared = false;
};

struct WorldActorAwarenessDefinition
{
    float partyEngagementRange = 0.0f;
    bool declared = false;
};

// world.yml hum (Hesper's Hum, COMBAT "The Hum"): the party's damage spells deal percents[n]% of their damage, n the
// number of qbits set (the Lattice nodes down), unless the map has its own share in maps (0: a null field, no casting).
// Undeclared: full damage everywhere.
struct WorldHumDefinition
{
    bool declared = false;
    std::vector<uint32_t> qbits;
    std::vector<int> percents;
    std::unordered_map<std::string, int> mapPercents;
};

// world.yml floorBurn: the damage type of the world's burning floors (fire, energy, poison, ...; a map may have its own in
// maps) and whether resistances cut it. Undeclared: MM's unresisted Fire.
struct WorldFloorBurnDefinition
{
    std::string type = "Fire";
    bool resisted = false;
    std::unordered_map<std::string, std::string> mapTypes;
};

// world.yml actorCombat. meleeVerticalReach: a monster's melee reaches the party only across a height difference of
// at most this share of the lower one's body height (a party on a ledge above half a monster's height is out of its
// reach, so it must find the way up); 0 (the default, MM6-MM8) ignores height.
struct WorldActorCombatDefinition
{
    float meleeVerticalReach = 0.0f;
};

// world.yml actorMovement. levelRadiusLimit: a monster wider than this meets the level indoors (walls, doorways,
// stairs) and plans its routes at this radius; its own radius still sets its reach and the other bodies' distance from
// it. MM6-MM8 declare it: their engine tested a body's sphere against a face only where the sphere's contact point lay
// inside the face, never against its edges, so a monster passed any doorway or corridor its centre fitted through.
// 0 (undeclared) keeps the full radius.
struct WorldActorMovementDefinition
{
    float levelRadiusLimit = 0.0f;
};

enum class TableContributionMode
{
    Append,
    Override,
    Distribution,
    // Whole-table replacement; ruleset packages only.
    Replace,
};

struct ContentIdRangeDefinition
{
    std::string domain;
    uint32_t begin = 0;
    uint32_t end = 0;
};

// Parses a manifest's idRanges map (domain: {begin, end}) into ranges; `owner` names the file in errors.
bool parseContentIdRanges(
    const YAML::Node &node,
    const std::string &owner,
    std::vector<ContentIdRangeDefinition> &ranges,
    std::string &errorMessage);
// The first domain whose ranges in the two lists overlap, if any.
std::optional<std::string> overlappingContentIdRange(
    const std::vector<ContentIdRangeDefinition> &left,
    const std::vector<ContentIdRangeDefinition> &right);

struct TableContributionDefinition
{
    std::string table;
    std::string idDomain;
    TableContributionMode mode = TableContributionMode::Append;
    std::string path;
    size_t sourceIdColumn = 0;
    size_t canonicalIdColumn = 0;
};

// world.yml completion: the certificate the party receives the first time it finishes the world's story (the qbit is
// set). A variant whose qbit is set at that moment replaces the headline and ending text (MM7's path of the Dark).
// With a layout the art is an original game's certificate background (an icon, 640 x 480): the text is centred in
// layout.text and the OpenYAMM mark drawn at layout.mark; without one it is OpenYAMM's 1536 x 1024 design.
struct WorldCompletionDefinition
{
    struct Layout
    {
        bool declared = false;
        // left, top, right, bottom
        std::array<float, 4> text = {};
        // centre x, centre y, height
        std::array<float, 3> mark = {};
    };

    struct Variant
    {
        uint32_t qbit = 0;
        std::string headline;
        std::string text;
    };

    bool declared = false;
    uint32_t qbit = 0;
    std::string continent;
    // The certificate's background, a hud_x2 path (1536 x 1024; WinGameScreen's layout).
    std::string art;
    std::string headline;
    std::string text;
    std::vector<Variant> variants;
    Layout layout;
};

struct WorldManifest
{
    std::string id = "mm8";
    std::string name = "MM8";
    std::string sourceGame = "mm8";
    WorldStartDefinition start;
    WorldQBitDefinition qbits;
    WorldPartyMovementDefinition partyMovement;
    WorldActorAwarenessDefinition actorAwareness;
    WorldActorCombatDefinition actorCombat;
    WorldActorMovementDefinition actorMovement;
    WorldHumDefinition hum;
    WorldFloorBurnDefinition floorBurn;
    // world.yml objectives: the QBits of the world's major objectives; how many are set gates vendor stock rows
    // (vendor_stock min_objectives).
    std::vector<uint32_t> objectiveQBits;
    // world.yml loadingScreens: the full-screen loading pages this world shows (icon names), picked at random; empty:
    // the engine's loading1-loading5.
    std::vector<std::string> loadingScreens;
    WorldCompletionDefinition completion;
    // world.yml ambience: {map file: sound name}, a looping bed under the music on that map, at ambienceVolume.
    std::unordered_map<std::string, std::string> ambience;
    float ambienceVolume = 0.6f;
    // world.yml musicAreas: {map file: [{track, rect: [minX, minY, maxX, maxY]}]}: on an outdoor map the party inside
    // a rectangle hears its track instead of the map's (the first that holds the party).
    struct MusicArea
    {
        int track = 0;
        std::array<float, 4> rect = {};
    };
    std::unordered_map<std::string, std::vector<MusicArea>> musicAreas;
    // world.yml tavernHirelings: false seats no generated mercenaries in the world's taverns (default true, MMerge's).
    bool tavernHirelings = true;
    uint32_t contentSchemaVersion = 1;
    std::vector<std::string> dependencies;
    std::vector<ContentIdRangeDefinition> idRanges;
    std::vector<TableContributionDefinition> tableContributions;
    bool loadedFromFile = false;

    const ContentIdRangeDefinition *findIdRange(const std::string &domain) const;
};

WorldManifest loadActiveWorldManifestOrDefault(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    std::string &errorMessage
);

std::optional<WorldManifest> loadWorldManifest(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    const std::string &fallbackWorldId,
    std::string &errorMessage
);

// The manifests of every mounted world package, sorted by id; false when one fails to load, repeats an id or misses a
// dependency.
bool loadMountedWorldManifests(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<WorldManifest> &manifests,
    std::string &errorMessage);
}
