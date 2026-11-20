#pragma once

#include "game/party/SkillData.h"
#include "game/maps/MapPresentation.h"

#include <array>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class HouseTable;
class MapStats;
class MergedTeacherAutonoteTable;
class MergedTeacherTopicTable;
class NpcDialogTable;
class Party;

// Every skill teacher of the mounted worlds, for the journal's trainer finder, the Ledger of Teachers and the skill
// tooltips' trainer hints (level_generation/ui/journal_trainers_20261105/native/README.md). The list comes from the
// loaded tables (npc.txt topic slots that are mastery-teacher topics, teacher_topics.txt, house_data.txt,
// map_stats.txt, teacher_autonotes.txt and the ruleset's extra houses), so ruleset patches count;
// trainer_places.txt (tools/trainer_places.py) only says where each house is entered.

// How a house is reached: its door on an outdoor map, the outdoor entrance of the dungeon or castle it is in, or
// neither (an indoor map no outdoor map leads to).
enum class TrainerPlaceKind : uint8_t
{
    Door,
    Entrance,
    Indoor,
};

struct TrainerPlace
{
    uint32_t houseId = 0;
    // The map whose script enters the house.
    std::string mapFileName;
    TrainerPlaceKind kind = TrainerPlaceKind::Indoor;
    // The outdoor map whose image shows the marker, at world (x, y); empty for Indoor.
    std::string markerMapFileName;
    float x = 0.0f;
    float y = 0.0f;
};

// trainer_places.txt: House, Map, Kind (door, entrance, indoor), Marker map, X, Y, Entrance chain. A later row of the
// same house replaces the earlier one (a world package's own rows).
class TrainerPlaceTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    void add(TrainerPlace place);
    const TrainerPlace *find(uint32_t houseId) const;
    size_t size() const;

private:
    std::unordered_map<uint32_t, TrainerPlace> m_places;
};

// teacher_ledger.yml: what a continent's Ledger of Teachers costs in its taverns and what the innkeeper says.
// {continent} and {price} are filled in.
struct TeacherLedgerSettings
{
    int price = 2000;
    std::string topic = "Ledger of Teachers";
    std::string description;
    std::string buy = "Buy the ledger: {price} gold";
    std::string bought;
    std::string tooPoor;

    bool loadFromYaml(const std::string &text, std::string &errorMessage);
    // The text with {continent} and {price} filled in.
    std::string fill(const std::string &text, const std::string &continentName) const;
};

// One place where an NPC teaches a mastery.
struct TrainerEntry
{
    uint32_t npcId = 0;
    std::string name;
    uint32_t houseId = 0;
    // Empty when the house has no name of its own (the tables call the ordinary Enroth teachers' homes "House").
    std::string houseName;
    uint32_t mapId = 0;
    std::string mapName;
    std::optional<uint32_t> continent;
    bool outdoor = false;
    uint32_t topicId = 0;
    // The canonical skill, its MM8 skill index (the teacher pins' ids use it) and the mastery taught.
    std::string skill;
    uint32_t skillId = 0;
    SkillMastery mastery = SkillMastery::None;
    // The topic's own price and skill level (teacher_topics.txt), 0 for the rules' defaults.
    uint32_t requiredGold = 0;
    uint32_t requiredSkill = 0;
    // The teacher autonote talking to the NPC gives (teacher_autonotes.txt); MM6's teachers have none.
    std::optional<uint32_t> autonoteId;
    // Another house the NPC also teaches in (MAW's moved teachers, npc_extra_houses.yml).
    bool extraHouse = false;
    // The map whose script enters the house (lower case), and where the journal map marks it.
    std::string mapFileName;
    std::optional<TrainerPlace> place;
    std::string markerMapName;
    // Actor teachers use a stable RUDE identity and their painted map, including its floor and world transform.
    uint32_t rudeId = 0;
    size_t dialogueRowCount = 0;
    float z = 0;
    std::optional<MapPresentation> mapPresentation;
};

// What a directory is built from: the session's tables, or a test's.
struct TrainerDirectorySource
{
    struct Npc
    {
        uint32_t id = 0;
        std::string name;
        uint32_t houseId = 0;
        std::vector<uint32_t> topicIds;
    };

    struct Topic
    {
        std::string skill;
        // The mastery the topic teaches: Expert, Master or Grandmaster.
        SkillMastery mastery = SkillMastery::None;
        uint32_t skillId = 0;
        uint32_t requiredGold = 0;
        uint32_t requiredSkill = 0;
    };

    struct House
    {
        std::string name;
        uint32_t mapId = 0;
    };

    struct Map
    {
        std::string name;
        std::string fileName;
        std::optional<uint32_t> continent;
    };

    std::vector<Npc> npcs;
    std::vector<TrainerEntry> actorTeachers;
    // Every teacher topic, taught by anyone or not, by topic id.
    std::unordered_map<uint32_t, Topic> topics;
    // The ruleset's moved teachers: the houses where an NPC also teaches (MAW's npc_extra_houses.yml).
    std::unordered_map<uint32_t, std::vector<uint32_t>> extraHouses;
    std::unordered_map<uint32_t, House> houses;
    std::unordered_map<uint32_t, Map> maps;
    // (topic id << 32 | npc id) -> teacher autonote.
    std::unordered_map<uint64_t, uint32_t> autonotes;
    TrainerPlaceTable places;
};

// The party's NPC state that moves or changes teachers: topic slots and houses set by scripts (MMMerge's map-load
// script gives Enroth's Grand Masters their lessons), and NPCs gone for good.
struct TrainerNpcState
{
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> topicOverrides;
    std::unordered_map<uint32_t, uint32_t> houseOverrides;
    std::vector<uint32_t> unavailableNpcIds;

    static TrainerNpcState of(const Party &party);
    bool empty() const;
    uint64_t fingerprint() const;
};

// How one gets from a map to another in one step: walking over its edge, or by a coach or boat (walking wins).
enum class TrainerLink : uint8_t
{
    Walk,
    Route,
};

using TrainerNeighbours = std::unordered_map<uint32_t, TrainerLink>;

// The one-step links between maps: edge crossings, and coach and boat routes (a route counts once the party has its
// QBit).
class TrainerLinks
{
public:
    void addWalk(uint32_t fromMap, uint32_t toMap);
    void addRoute(uint32_t fromMap, uint32_t toMap, uint32_t requiredQBit = 0);
    // The maps one step from the party's map and, indoors, from the outdoor map it came from; walking wins.
    TrainerNeighbours neighbours(
        std::optional<uint32_t> currentMap,
        std::optional<uint32_t> referenceMap,
        const std::function<bool(uint32_t)> &hasQBit) const;

private:
    struct Link
    {
        uint32_t toMap = 0;
        TrainerLink kind = TrainerLink::Walk;
        uint32_t requiredQBit = 0;
    };

    std::unordered_map<uint32_t, std::vector<Link>> m_links;
};

class TrainerDirectory
{
public:
    static TrainerDirectory build(const TrainerDirectorySource &source, TrainerNpcState state = {});
    static TrainerDirectory build(
        const NpcDialogTable &npcs,
        const MergedTeacherTopicTable &teacherTopics,
        const MergedTeacherAutonoteTable &teacherAutonotes,
        const HouseTable &houses,
        const MapStats &maps,
        TrainerPlaceTable places,
        TeacherLedgerSettings ledger = {},
        std::vector<TrainerEntry> actorTeachers = {});

    // [Expert, Master, Grandmaster] = where each mastery of the skill is taught. A skill some teacher topic names is
    // listed even when nobody teaches it.
    const std::array<std::vector<TrainerEntry>, 3> *find(const std::string &canonicalSkill) const;
    // Every place, by skill.
    const std::unordered_map<std::string, std::array<std::vector<TrainerEntry>, 3>> &skills() const;
    // This directory with the party's scripted topic slots and houses; itself when the party changed none. The one
    // built is kept, and the reference good, until a call for another NPC state.
    const TrainerDirectory &forParty(const Party &party) const;
    // The teacher autonotes of the continent's teachers (not counting their extra houses elsewhere).
    std::vector<uint32_t> continentAutonotes(uint32_t continent) const;
    std::optional<uint32_t> mapContinent(uint32_t mapId) const;
    // Lower-case map file name -> its name in map_stats.txt.
    std::string mapName(const std::string &mapFileName) const;
    const TrainerLinks &links() const;
    const TeacherLedgerSettings &ledger() const;
    const TrainerPlaceTable &places() const;

private:
    static TrainerDirectory buildFrom(
        std::shared_ptr<const TrainerDirectorySource> pSource,
        const TrainerNpcState &state,
        const TrainerLinks &links,
        const TeacherLedgerSettings &ledger);

    std::shared_ptr<const TrainerDirectorySource> m_pSource;
    std::unordered_map<std::string, std::array<std::vector<TrainerEntry>, 3>> m_skills;
    TrainerLinks m_links;
    TeacherLedgerSettings m_ledger;
    // forParty's last directory and the NPC state it was built for.
    mutable std::shared_ptr<const TrainerDirectory> m_pPartyDirectory;
    mutable uint64_t m_partyFingerprint = 0;
};

struct PickedTrainer
{
    TrainerEntry entry;
    // 0 the party's map (or, indoors, the outdoor map it came from), 1 one step away, 2 the same continent,
    // 3 elsewhere.
    int rank = 3;
    std::optional<TrainerLink> link;
    // A rank-0 teacher on the outdoor map the party came from rather than the one it stands on.
    bool outside = false;
};

// The nearest teachers, best first: rank, then outdoor maps before indoor, continent (unknown last), map name, NPC
// name. A teacher who stands in several places counts once, at the best one.
std::vector<PickedTrainer> pickTrainers(
    const std::vector<TrainerEntry> &entries,
    std::optional<uint32_t> currentMap,
    std::optional<uint32_t> currentContinent,
    size_t limit,
    const TrainerNeighbours &neighbours,
    std::optional<uint32_t> referenceMap);

// The continents with trainer lists, in the finder's order: 1 Jadame, 2 Antagarich, 3 Enroth.
constexpr std::array<uint32_t, 4> TrainerContinents = {1, 2, 3, 5};
// "Jadame", "Antagarich", "Enroth"; empty for any other continent.
std::string trainerContinentName(uint32_t continent);

// The journal map pin talking to a teacher without an autonote leaves (GameplayDialogController
// tryAddRuntimeMapNote): continent * 1000 + mastery rank * 100 + skill id, on the map the party stood on.
uint32_t teacherMapNoteId(uint32_t continent, SkillMastery mastery, uint32_t skillId);

// Whether the party knows the teacher: the continent's Ledger of Teachers, the teacher's autonote, or, for a teacher
// without one (MM6's), the pin talking to it left on the journal map.
bool trainerKnown(const TrainerEntry &entry, const Party &party);
// Talking to an actor teacher records their position using the existing saved journal notes.
void discoverActorTeacher(Party &party, uint32_t rudeId);

// The trainer finder's search: every word of `search` (case-insensitive, split at spaces) is in one of the fields.
bool trainerSearchMatches(const std::string &search, const std::vector<std::string> &fields);

// Buys the continent's Ledger of Teachers: takes the price, records the ledger and gives every teacher autonote of the
// continent. False, changing nothing, when the party lacks the gold or already has the ledger.
bool buyTeacherLedger(Party &party, const TrainerDirectory &directory, uint32_t continent);
}
