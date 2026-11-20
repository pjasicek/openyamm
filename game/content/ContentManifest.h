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

// One condition of world.yml partyDeath `when`: every `qbits` bit set and every `notQbits` bit clear.
struct WorldPartyDeathCondition
{
    std::vector<uint32_t> qbits;
    std::vector<uint32_t> notQbits;
};

// world.yml partyDeath: where a party defeated in this world wakes (MM9: Arslegard City inside the Great Gate) and
// the movie shown first (none when unset); unset: MMerge's continent death maps (continent_settings.txt). With `when`,
// the destination applies only while one condition holds; otherwise the defeat is lost (MM9's game over): the
// `otherwise` movie, then the autosave. keepGold: the party wakes with its gold (MM9 takes none; MMerge takes it all).
struct WorldPartyDeathDefinition
{
    std::string mapFileName;
    std::array<int, 3> position = {};
    int directionYawUnits = 0;
    std::string movie;
    bool keepGold = false;
    std::vector<WorldPartyDeathCondition> when;
    std::string otherwiseMovie;
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
    // How monsters on MM9's loop (an mm9_ai profile) perceive the party (Mm9PartyAwareness; MM9_MONSTER_AI_PLAN.md
    // "Awareness of the party"): mm9Sight {allRound, scale, max} and mm9Provoke {range, radius}. Undeclared: MM9's
    // rules.
    bool mm9SightAllRound = false;
    float mm9SightScale = 1.0f;
    float mm9SightMax = 0.0f;
    float mm9ProvokeRange = 0.0f;
    float mm9ProvokeRadius = 0.0f;
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

// world.yml music (devdocs/mm9_rework/MM9_AMBIENT_AUDIO_RE.md section 2): how the world's music plays. Undeclared: the
// map's track loops seamlessly and there is no battle music (MM6-MM8).
struct WorldMusicDefinition
{
    float repeatGapSeconds = 0.0f;      // silence between two plays of a map's track (MM9: 10)
    int battleTrack = 0;                // played while hostile monsters that saw the party are near (MM9: Song03)
    float battleFadeSeconds = 2.5f;     // the battle track's fade out, and the map track's fade back in
};

// world.yml ambientSounds: the rules of the world's placed ambient sounds (devdocs/AMBIENT_SOUNDS.md). Undeclared:
// day 06:00-20:00, panned.
struct WorldAmbientSoundDefinition
{
    float dayStartHour = 6.0f;
    float dayEndHour = 20.0f;
    bool pan = true;                    // false: centred, heard by distance only (MM9)
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
        // false: the art carries its own headline (MM9's WINBG.pcx), which is then not drawn
        bool drawHeadline = true;
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
    WorldPartyDeathDefinition partyDeath;
    // world.yml autosave: `departure` (default, MM8): the autosave is written on the map being left, before its exit
    // runs; `arrival` (MM9, cshell.dll 0x100a6bb0): after the new map has loaded, and after a defeat's wake.
    bool autosaveOnArrival = false;
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
    WorldMusicDefinition music;
    WorldAmbientSoundDefinition ambientSounds;
    // world.yml tavernHirelings: false seats no generated mercenaries in the world's taverns (default true, MMerge's).
    bool tavernHirelings = true;
    // world.yml streetNpcs: false gives this world no MMerge street NPCs: a friendly actor without an NPC of its own
    // does not answer with its group's news (npc_group.txt) or a generated NPC (bolster creed Peasant). MM9, whose actor
    // groups are its maps' script groups and whose actors talk only through their RUDE ids and use events (a dog or a
    // townsperson without DoRude says nothing); default true.
    bool streetNpcs = true;
    // world.yml friendlyActorsBlockParty: true makes friendly actors (townsfolk, NPCs, animals) solid to the party as
    // hostile ones are. MM9, whose NPCs block the player; default false, MM6-MM8's walk-through rule.
    bool friendlyActorsBlockParty = false;
    // world.yml npcFollowers: false turns the MM6-MM8 hired NPC followers off in this world (not shown, no share of
    // found gold, no bonuses; the party keeps them for other worlds). MM9, whose own hirelings replace them.
    bool npcFollowers = true;
    // world.yml formations: true places the party on MM9's formation grid, and monsters pick their victims by its
    // ranks (Party::setFormationTargetingActive). MM9; default false.
    bool formations = false;
    // world.yml fleetFoot: true makes Fly's slot (Air, spell 21) this world's Fleet Foot, MM9's run-speed buff, under
    // its name, texts and spellbook picture (game/party/WorldSpells.h). MM9, which has no Fly; default false.
    bool fleetFoot = false;
    // world.yml combatLog: false hides the combat log in this world unless its setting is On (MM9, the user
    // 2026-11-06: the row under the minimap is the hireling rail's and the formation button's).
    bool combatLog = true;
    // world.yml chestArtifactsOnly: true gives this world's random artifacts and relics only from level-7 chest slots
    // (no 5% roll on level-6 loot), and a level-7 slot with none left gives gold and a level-6 item instead of
    // nothing. MM9, whose black chests hold them (the user, 2026-11-06); default false.
    bool chestArtifactsOnly = false;
    // world.yml groundGoldByItemTier: true rolls a treasure marker's gold heap by the tier its item would have (the
    // marker's level remapped by the map's, as chest slots do) instead of by the marker's own level (MM6-MM8). MM9,
    // whose markers are raised to the level that gives exactly the map's item tiers, so their gold came a tier too rich
    // (the user, 2026-11-09); default false.
    bool groundGoldByItemTier = false;
    // world.yml openAirMaps: this world's BLV maps that lie open to the sky (lowercase file names). Their spells follow
    // the outdoor rules: Meteor Shower, Starburst, Death Blossom, Sunray and Armageddon work there, Inferno and
    // Prismatic Light do not (MapStatsEntry::openAir, IGameplayWorldRuntime::isOpenAirMap). MM9, whose regions and
    // cities are BLVs (the user, 2026-11-09); default none, so every BLV keeps the indoor rules.
    std::vector<std::string> openAirMaps;
    // world.yml noTeleportMaps: this world's maps where Town Portal and Lloyd's Beacon fail (lowercase file names;
    // MapStatsEntry::noTeleport). MM9: the maps its MAPSTATS.txt gives TownPortal -1 (object.lto 0x1008c7ce,
    // 0x1008df77); default none.
    std::vector<std::string> noTeleportMaps;
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

// Whether the world package is installed: its world.yml resolves. A release may leave a world out (1.22 ships no MM9),
// so content that points into another world (its continent card, portal, portraits) is offered only when this holds.
bool isWorldPackageMounted(const Engine::AssetFileSystem &assetFileSystem, const std::string &worldId);

// The manifests of every mounted world package, sorted by id; false when one fails to load, repeats an id or misses a
// dependency.
bool loadMountedWorldManifests(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<WorldManifest> &manifests,
    std::string &errorMessage);
}
