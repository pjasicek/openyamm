#pragma once

#include "core/IndoorLowering.h"
#include "core/MonsterRelations.h"
#include "core/OutdoorEvents.h"
#include "core/OutdoorLowering.h"
#include "core/OutdoorPlaces.h"
#include "core/Project.h"

#include "game/outdoor/OutdoorMapData.h"

#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What an outdoor map holds beside its land and its houses: the sketch's `structures` (models that are no house:
// walls, bridges, wells, fountains, chests, signs), the single things placed by name (decorations, townsfolk),
// and the events all of them carry. The forms and what the shipped maps use for which are told at the top of
// OutdoorThings.cpp.

// An event of the map's script.
// The id of the one event every thing with `hint_shared` and this hint carries (batch O-H).
inline std::string outdoorSharedHintId(const std::string &hint)
{
    return "evt:hint_shared:" + hint;
}

struct OutdoorEventPlan
{
    uint16_t number = 0;
    // The id it has in ids.lock.yml.
    std::string id;
    // What the thing says when looked at; empty for an event nothing shows.
    std::string title;
    // The handler's lines of Lua; empty for an event that only has a title.
    std::vector<std::string> body;
};

// A chest of the map: the scene's chest record a chest event opens.
struct OutdoorChestPlan
{
    std::string id;
    // The chest's picture in the chest table (1 to 8 in the shipped games).
    int picture = 1;
    // The treasure level of what the game puts in on the first opening, 1 to 7 (0: nothing by level), and how
    // many such things.
    int level = 0;
    int randomItems = 0;
    // More things chosen by the game, each of its own treasure level (`random_levels`): a chest of mixed levels.
    std::vector<int> randomLevels;
    // Things that are in the chest for certain, by item number.
    std::vector<int> items;
    int gold = 0;
    bool trapped = false;
};

// A person or creature standing on the map from the start.
struct OutdoorActorPlan
{
    std::string id;
    // The monster's name in the monster table and the row's number.
    std::string monster;
    int monsterId = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    // The NPC the actor speaks as (a row of the NPC table), 0 for none.
    int npc = 0;
    // The actors of one group stand and fight together; 0 for none.
    int group = 0;
    // Hostile from the start, whatever the monster table says of its kind.
    bool hostile = false;
    // Not there until an event shows its group (`hidden: true`; the effect show_actors).
    bool hidden = false;
    // Its home radius (`leash`, the scene's leash_radius), 0 for none.
    int leash = 0;
    // The item it carries (`carries: <item number>`, the scene's carried_item_id): left in its corpse or dropped where
    // it dies, as a quest item a monster holds (F15); 0 for none.
    int carriedItem = 0;
    // What the monster tables give it.
    int hitPoints = 0;
    int height = 0;
    int radius = 0;
    int moveSpeed = 0;
};

struct OutdoorThings
{
    // The models of the structures, after the buildings' in the map.
    std::vector<Game::OutdoorBModel> models;
    std::vector<OutdoorEventPlan> events;
    // Single decorations standing at their own places, each with the event it carries (0 for none).
    std::vector<OutdoorPlacedDecoration> decorations;
    std::vector<uint16_t> decorationEvents;
    // The structure each of them is, by id: what events name to change its picture or hide it.
    std::vector<std::string> decorationIds;
    // Filled by the build once every handler is written: the number events change each by (the entity's
    // `event_id_primary`; 0 for one no event names), and whether it starts hidden.
    std::vector<int> decorationNumbers;
    std::vector<bool> decorationHidden;
    std::vector<OutdoorChestPlan> chests;
    std::vector<OutdoorActorPlan> actors;
    // sketch.yml `items`: items that lie on the ground from the start (the scene's sprite objects).
    std::vector<LoweredItem> items;
    // Events the game runs when the map is entered.
    std::vector<int> onLoad;
    // Events the game runs when the party leaves the map (`trigger: leave`).
    std::vector<int> onLeave;
    // Timer events that act only on a flying party (`when_flying`): the script's `levitateTrapEvents`.
    std::vector<int> levitateTraps;
    // Events the game runs by the clock: event number to the half minutes of game time (seconds of play) between
    // two runs.
    std::map<int, int> timers;
    // Calendar timers (`trigger: daily|weekly`) by event number: the fields of the timer's record after its numbers.
    std::map<int, std::string> calendarTimers;
    // Chest event to the chest it opens.
    std::map<int, int> chestOfEvent;
    // Given to the raise: the events of the buildings that structures may carry (`same_event_as`), by
    // building:<id> (its own door, else its name), building:<id>/door:<n> (n-th of `doors`, 0 its own door) and
    // building:<id>/part:<id>.
    std::map<std::string, uint16_t> buildingEvents;
    // The ground the structures cover, in sketch cells [west, north, east, south]: scattered things keep off it.
    std::vector<std::array<double, 4>> covered;
    // The groups of `actors` made peaceful (`hostile: false`) and the map's own monster relations (`relations`):
    // what the build's hostility check reads.
    std::set<int> peacefulGroups;
    std::vector<MonsterRelationRow> relations;
    // sketch.yml `sounds` (E9): the scene's placed ambient sounds, as objects.yml's indoors.
    std::vector<LoweredAmbientSound> sounds;
};

// Reads the sketch's `structures`, `actors` and `events` and raises what they describe. Event, chest and
// container numbers come from `ids` (ids.lock.yml), which takes the new ones; what the events test and do is
// written by `words`. `assetRoot` is where the monster
// and decoration tables are read from; empty when there is none (what needs a table is then left out, with a
// warning). `mountRoot`, read in front of it, and it hold the installed maps whose arrivals `into` names. False with issues when the sketch asks for what cannot be built.
bool raiseOutdoorThings(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::filesystem::path &assetRoot,
    IdsLock &ids,
    OutdoorEventWords &words,
    OutdoorThings &things,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings,
    const std::filesystem::path &mountRoot = std::filesystem::path());
}
