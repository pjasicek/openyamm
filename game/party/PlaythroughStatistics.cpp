#include "game/party/PlaythroughStatistics.h"

#include "game/party/Party.h"
#include "game/party/PlaythroughSeal.h"
#include "game/tables/MonsterTable.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <ctime>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<const char *, StatDamageSchoolCount> DamageSchoolNames = {
    "physical", "fire", "air", "water", "earth", "spirit", "mind", "body", "light", "dark", "energy", "irresistible"};
constexpr std::array<const char *, size_t(GoldReason::Count)> GoldReasonNames = {
    "other", "loot_corpse", "loot_chest", "loot_ground", "event", "sold", "shop", "training", "temple", "guild",
    "travel", "tavern", "bank", "defeat"};
constexpr std::array<const char *, size_t(ExperienceReason::Count)> ExperienceReasonNames = {"other", "monster", "event"};
constexpr std::array<const char *, size_t(StatKillMethod::Count)> KillMethodNames = {"melee", "missile", "spell"};
constexpr std::array<const char *, size_t(StatDamageTakenKind::Count)> DamageTakenNames = {
    "melee", "missile", "spell", "environment"};
constexpr size_t LargestHitCount = 5;
constexpr size_t DeathLogCount = 32;
constexpr size_t WipeLogCount = 16;
constexpr double WriteIntervalSeconds = 60.0;
constexpr int FileSchema = 1;

std::string utcNow()
{
    const std::time_t now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    std::tm utc = {};
#if defined(_WIN32)
    gmtime_s(&utc, &now);
#else
    gmtime_r(&now, &utc);
#endif
    char text[32] = {};
    std::strftime(text, sizeof(text), "%Y-%m-%dT%H:%M:%SZ", &utc);
    return text;
}

template<size_t N>
void emitArray(YAML::Emitter &out, const char *pKey, const std::array<uint64_t, N> &values,
    const std::array<const char *, N> &names)
{
    out << YAML::Key << pKey << YAML::Value << YAML::BeginMap;

    for (size_t index = 0; index < N; ++index)
    {
        if (values[index] != 0)
        {
            out << YAML::Key << names[index] << YAML::Value << values[index];
        }
    }

    out << YAML::EndMap;
}

template<size_t N>
void readArray(const YAML::Node &node, std::array<uint64_t, N> &values, const std::array<const char *, N> &names)
{
    if (!node || !node.IsMap())
    {
        return;
    }

    for (size_t index = 0; index < N; ++index)
    {
        if (const YAML::Node child = node[names[index]]; child)
        {
            values[index] = child.as<uint64_t>(0);
        }
    }
}

template<typename Value>
void emitMap(YAML::Emitter &out, const char *pKey, const std::map<std::string, Value> &values)
{
    out << YAML::Key << pKey << YAML::Value << YAML::BeginMap;

    for (const auto &[key, value] : values)
    {
        out << YAML::Key << key << YAML::Value << value;
    }

    out << YAML::EndMap;
}

template<typename Value>
void readMap(const YAML::Node &node, std::map<std::string, Value> &values)
{
    if (!node || !node.IsMap())
    {
        return;
    }

    for (const auto &entry : node)
    {
        values[entry.first.as<std::string>()] = entry.second.as<Value>(Value{});
    }
}

void emitHit(YAML::Emitter &out, const PlaythroughHitRecord &hit)
{
    out << YAML::Flow << YAML::BeginMap
        << YAML::Key << "amount" << YAML::Value << hit.amount
        << YAML::Key << "member" << YAML::Value << hit.member
        << YAML::Key << "source" << YAML::Value << hit.source
        << YAML::Key << "target" << YAML::Value << hit.target
        << YAML::Key << "day" << YAML::Value << hit.day
        << YAML::EndMap;
}

PlaythroughHitRecord readHit(const YAML::Node &node)
{
    PlaythroughHitRecord hit;

    if (node && node.IsMap())
    {
        hit.amount = node["amount"].as<uint64_t>(0);
        hit.member = node["member"].as<std::string>("");
        hit.source = node["source"].as<std::string>("");
        hit.target = node["target"].as<std::string>("");
        hit.day = node["day"].as<double>(0.0);
    }

    return hit;
}

void emitLog(YAML::Emitter &out, const char *pKey, const std::vector<PlaythroughLogEntry> &log)
{
    out << YAML::Key << pKey << YAML::Value << YAML::BeginSeq;

    for (const PlaythroughLogEntry &entry : log)
    {
        out << YAML::Flow << YAML::BeginMap
            << YAML::Key << "member" << YAML::Value << entry.member
            << YAML::Key << "cause" << YAML::Value << entry.cause
            << YAML::Key << "map" << YAML::Value << entry.map
            << YAML::Key << "day" << YAML::Value << entry.day
            << YAML::EndMap;
    }

    out << YAML::EndSeq;
}

void readLog(const YAML::Node &node, std::vector<PlaythroughLogEntry> &log)
{
    if (!node || !node.IsSequence())
    {
        return;
    }

    for (const YAML::Node &item : node)
    {
        PlaythroughLogEntry entry;
        entry.member = item["member"].as<std::string>("");
        entry.cause = item["cause"].as<std::string>("");
        entry.map = item["map"].as<std::string>("");
        entry.day = item["day"].as<double>(0.0);
        log.push_back(std::move(entry));
    }
}

void emitCounters(YAML::Emitter &out, const PlaythroughCounters &c)
{
    out << YAML::Key << "time" << YAML::Value << YAML::BeginMap
        << YAML::Key << "played_seconds" << YAML::Value << c.playedSeconds
        << YAML::Key << "turn_based_seconds" << YAML::Value << c.turnBasedSeconds
        << YAML::Key << "sessions" << YAML::Value << c.sessions
        << YAML::Key << "longest_session_seconds" << YAML::Value << c.longestSessionSeconds;
    emitMap(out, "by_world_seconds", c.playedSecondsByWorld);
    out << YAML::EndMap;

    out << YAML::Key << "saves" << YAML::Value << YAML::BeginMap
        << YAML::Key << "quick" << YAML::Value << c.quickSaves
        << YAML::Key << "auto" << YAML::Value << c.autoSaves
        << YAML::Key << "named" << YAML::Value << c.namedSaves
        << YAML::Key << "quickloads" << YAML::Value << c.quickLoads
        << YAML::Key << "menu_loads" << YAML::Value << c.menuLoads
        << YAML::Key << "loads_after_wipe" << YAML::Value << c.loadsAfterWipe
        << YAML::EndMap;

    out << YAML::Key << "combat" << YAML::Value << YAML::BeginMap
        << YAML::Key << "kills" << YAML::Value << c.kills;
    emitArray(out, "kills_by_method", c.killsByMethod, KillMethodNames);
    emitMap(out, "kills_by_monster", c.killsByMonster);
    out << YAML::Key << "strongest_kill" << YAML::Value << YAML::Flow << YAML::BeginMap
        << YAML::Key << "monster" << YAML::Value << c.strongestKill
        << YAML::Key << "level" << YAML::Value << c.strongestKillLevel
        << YAML::Key << "day" << YAML::Value << c.strongestKillDay
        << YAML::EndMap;
    emitArray(out, "damage_dealt", c.damageDealtBySchool, DamageSchoolNames);
    out << YAML::Key << "critical_hits" << YAML::Value << c.criticalHits;
    out << YAML::Key << "largest_hits" << YAML::Value << YAML::BeginSeq;

    for (const PlaythroughHitRecord &hit : c.largestHits)
    {
        emitHit(out, hit);
    }

    out << YAML::EndSeq;
    emitArray(out, "damage_taken", c.damageTaken, DamageTakenNames);
    out << YAML::Key << "largest_hit_taken" << YAML::Value;
    emitHit(out, c.largestHitTaken);
    out << YAML::Key << "turn_based" << YAML::Value << YAML::Flow << YAML::BeginMap
        << YAML::Key << "fights" << YAML::Value << c.turnBasedFights
        << YAML::Key << "turns" << YAML::Value << c.turnBasedTurns
        << YAML::Key << "kills" << YAML::Value << c.turnBasedKills
        << YAML::EndMap;
    out << YAML::EndMap;

    out << YAML::Key << "spells" << YAML::Value << YAML::BeginMap
        << YAML::Key << "cast" << YAML::Value << c.spellsCast
        << YAML::Key << "from_scrolls" << YAML::Value << c.scrollCasts
        << YAML::Key << "mana_spent" << YAML::Value << c.manaSpent
        << YAML::Key << "healing_given" << YAML::Value << c.healingGiven;
    emitMap(out, "by_spell", c.spellCasts);
    out << YAML::EndMap;

    out << YAML::Key << "experience" << YAML::Value << YAML::BeginMap;
    out << YAML::Key << "largest_award" << YAML::Value << c.largestAward
        << YAML::Key << "levels_gained" << YAML::Value << c.levelsGained;
    emitArray(out, "by_source", c.experience, ExperienceReasonNames);
    out << YAML::EndMap;

    out << YAML::Key << "losses" << YAML::Value << YAML::BeginMap
        << YAML::Key << "deaths" << YAML::Value << c.deaths
        << YAML::Key << "eradications" << YAML::Value << c.eradications
        << YAML::Key << "stonings" << YAML::Value << c.stonings
        << YAML::Key << "knockouts" << YAML::Value << c.knockouts
        << YAML::Key << "party_wipes" << YAML::Value << c.partyWipes;
    emitMap(out, "death_causes", c.deathCauses);
    emitLog(out, "death_log", c.deathLog);
    emitLog(out, "wipe_log", c.wipeLog);
    out << YAML::EndMap;

    out << YAML::Key << "services" << YAML::Value << YAML::Flow << YAML::BeginMap
        << YAML::Key << "temple_heals" << YAML::Value << c.templeHeals
        << YAML::Key << "donations" << YAML::Value << c.donations
        << YAML::EndMap;

    out << YAML::Key << "travel" << YAML::Value << YAML::BeginMap
        << YAML::Key << "town_portals" << YAML::Value << c.townPortals
        << YAML::Key << "lloyd_recalls" << YAML::Value << c.lloydRecalls
        << YAML::Key << "lloyd_sets" << YAML::Value << c.lloydSets
        << YAML::Key << "coach_trips" << YAML::Value << c.coachTrips
        << YAML::Key << "ship_trips" << YAML::Value << c.shipTrips
        << YAML::Key << "travel_days" << YAML::Value << c.travelDays;
    emitMap(out, "town_portal_destinations", c.townPortalDestinations);
    out << YAML::EndMap;

    out << YAML::Key << "exploration" << YAML::Value << YAML::BeginMap
        << YAML::Key << "maps_visited" << YAML::Value << YAML::Flow << YAML::BeginSeq;

    for (const std::string &map : c.mapsVisited)
    {
        out << map;
    }

    out << YAML::EndSeq << YAML::Key << "chests_opened" << YAML::Value << YAML::Flow << YAML::BeginSeq;

    for (const std::string &chest : c.chestsOpened)
    {
        out << chest;
    }

    out << YAML::EndSeq << YAML::EndMap;

    out << YAML::Key << "gold" << YAML::Value << YAML::BeginMap;
    emitArray(out, "gained", c.goldGained, GoldReasonNames);
    emitArray(out, "spent", c.goldSpent, GoldReasonNames);
    out << YAML::EndMap;

    out << YAML::Key << "artifacts_found" << YAML::Value << YAML::BeginSeq;

    for (const PlaythroughArtifactRecord &artifact : c.artifactsFound)
    {
        out << YAML::Flow << YAML::BeginMap
            << YAML::Key << "item" << YAML::Value << artifact.itemId
            << YAML::Key << "name" << YAML::Value << artifact.name
            << YAML::Key << "day" << YAML::Value << artifact.day
            << YAML::EndMap;
    }

    out << YAML::EndSeq;

    out << YAML::Key << "members" << YAML::Value << YAML::BeginMap;

    for (const auto &[key, member] : c.members)
    {
        out << YAML::Key << key << YAML::Value << YAML::Flow << YAML::BeginMap
            << YAML::Key << "name" << YAML::Value << member.name
            << YAML::Key << "class" << YAML::Value << member.className
            << YAML::Key << "joined_day" << YAML::Value << member.joinedDay
            << YAML::Key << "kills" << YAML::Value << member.kills
            << YAML::Key << "damage_dealt" << YAML::Value << member.damageDealt
            << YAML::Key << "largest_hit" << YAML::Value << member.largestHit
            << YAML::Key << "damage_taken" << YAML::Value << member.damageTaken
            << YAML::Key << "spells_cast" << YAML::Value << member.spellsCast
            << YAML::Key << "healing_given" << YAML::Value << member.healingGiven
            << YAML::Key << "knockouts" << YAML::Value << member.knockouts
            << YAML::Key << "deaths" << YAML::Value << member.deaths
            << YAML::Key << "eradications" << YAML::Value << member.eradications
            << YAML::Key << "experience" << YAML::Value << member.experience
            << YAML::Key << "levels_gained" << YAML::Value << member.levelsGained
            << YAML::EndMap;
    }

    out << YAML::EndMap;
}

void readCounters(const YAML::Node &root, PlaythroughCounters &c)
{
    c = {};

    if (const YAML::Node time = root["time"]; time)
    {
        c.playedSeconds = time["played_seconds"].as<double>(0.0);
        c.turnBasedSeconds = time["turn_based_seconds"].as<double>(0.0);
        c.sessions = time["sessions"].as<uint64_t>(0);
        c.longestSessionSeconds = time["longest_session_seconds"].as<double>(0.0);
        readMap(time["by_world_seconds"], c.playedSecondsByWorld);
    }

    if (const YAML::Node saves = root["saves"]; saves)
    {
        c.quickSaves = saves["quick"].as<uint64_t>(0);
        c.autoSaves = saves["auto"].as<uint64_t>(0);
        c.namedSaves = saves["named"].as<uint64_t>(0);
        c.quickLoads = saves["quickloads"].as<uint64_t>(0);
        c.menuLoads = saves["menu_loads"].as<uint64_t>(0);
        c.loadsAfterWipe = saves["loads_after_wipe"].as<uint64_t>(0);
    }

    if (const YAML::Node combat = root["combat"]; combat)
    {
        c.kills = combat["kills"].as<uint64_t>(0);
        readArray(combat["kills_by_method"], c.killsByMethod, KillMethodNames);
        readMap(combat["kills_by_monster"], c.killsByMonster);

        if (const YAML::Node strongest = combat["strongest_kill"]; strongest && strongest.IsMap())
        {
            c.strongestKill = strongest["monster"].as<std::string>("");
            c.strongestKillLevel = strongest["level"].as<int>(0);
            c.strongestKillDay = strongest["day"].as<double>(0.0);
        }

        readArray(combat["damage_dealt"], c.damageDealtBySchool, DamageSchoolNames);
        c.criticalHits = combat["critical_hits"].as<uint64_t>(0);

        if (const YAML::Node hits = combat["largest_hits"]; hits && hits.IsSequence())
        {
            for (const YAML::Node &hit : hits)
            {
                c.largestHits.push_back(readHit(hit));
            }
        }

        readArray(combat["damage_taken"], c.damageTaken, DamageTakenNames);
        c.largestHitTaken = readHit(combat["largest_hit_taken"]);

        if (const YAML::Node turnBased = combat["turn_based"]; turnBased && turnBased.IsMap())
        {
            c.turnBasedFights = turnBased["fights"].as<uint64_t>(0);
            c.turnBasedTurns = turnBased["turns"].as<uint64_t>(0);
            c.turnBasedKills = turnBased["kills"].as<uint64_t>(0);
        }
    }

    if (const YAML::Node spells = root["spells"]; spells)
    {
        c.spellsCast = spells["cast"].as<uint64_t>(0);
        c.scrollCasts = spells["from_scrolls"].as<uint64_t>(0);
        c.manaSpent = spells["mana_spent"].as<uint64_t>(0);
        c.healingGiven = spells["healing_given"].as<uint64_t>(0);
        readMap(spells["by_spell"], c.spellCasts);
    }

    if (const YAML::Node experience = root["experience"]; experience)
    {
        c.largestAward = experience["largest_award"].as<uint64_t>(0);
        c.levelsGained = experience["levels_gained"].as<uint64_t>(0);
        readArray(experience["by_source"], c.experience, ExperienceReasonNames);
    }

    if (const YAML::Node losses = root["losses"]; losses)
    {
        c.deaths = losses["deaths"].as<uint64_t>(0);
        c.eradications = losses["eradications"].as<uint64_t>(0);
        c.stonings = losses["stonings"].as<uint64_t>(0);
        c.knockouts = losses["knockouts"].as<uint64_t>(0);
        c.partyWipes = losses["party_wipes"].as<uint64_t>(0);
        readMap(losses["death_causes"], c.deathCauses);
        readLog(losses["death_log"], c.deathLog);
        readLog(losses["wipe_log"], c.wipeLog);
    }

    if (const YAML::Node services = root["services"]; services)
    {
        c.templeHeals = services["temple_heals"].as<uint64_t>(0);
        c.donations = services["donations"].as<uint64_t>(0);
    }

    if (const YAML::Node travel = root["travel"]; travel)
    {
        c.townPortals = travel["town_portals"].as<uint64_t>(0);
        c.lloydRecalls = travel["lloyd_recalls"].as<uint64_t>(0);
        c.lloydSets = travel["lloyd_sets"].as<uint64_t>(0);
        c.coachTrips = travel["coach_trips"].as<uint64_t>(0);
        c.shipTrips = travel["ship_trips"].as<uint64_t>(0);
        c.travelDays = travel["travel_days"].as<double>(0.0);
        readMap(travel["town_portal_destinations"], c.townPortalDestinations);
    }

    if (const YAML::Node exploration = root["exploration"]; exploration)
    {
        if (const YAML::Node maps = exploration["maps_visited"]; maps && maps.IsSequence())
        {
            for (const YAML::Node &map : maps)
            {
                c.mapsVisited.insert(map.as<std::string>(""));
            }
        }

        if (const YAML::Node chests = exploration["chests_opened"]; chests && chests.IsSequence())
        {
            for (const YAML::Node &chest : chests)
            {
                c.chestsOpened.insert(chest.as<std::string>(""));
            }
        }
    }

    if (const YAML::Node gold = root["gold"]; gold)
    {
        readArray(gold["gained"], c.goldGained, GoldReasonNames);
        readArray(gold["spent"], c.goldSpent, GoldReasonNames);
    }

    if (const YAML::Node artifacts = root["artifacts_found"]; artifacts && artifacts.IsSequence())
    {
        for (const YAML::Node &artifact : artifacts)
        {
            PlaythroughArtifactRecord record;
            record.itemId = artifact["item"].as<uint32_t>(0);
            record.name = artifact["name"].as<std::string>("");
            record.day = artifact["day"].as<double>(0.0);
            c.artifactsFound.push_back(std::move(record));
        }
    }

    if (const YAML::Node members = root["members"]; members && members.IsMap())
    {
        for (const auto &entry : members)
        {
            const YAML::Node &node = entry.second;
            PlaythroughMemberCounters member;
            member.name = node["name"].as<std::string>("");
            member.className = node["class"].as<std::string>("");
            member.joinedDay = node["joined_day"].as<double>(0.0);
            member.kills = node["kills"].as<uint64_t>(0);
            member.damageDealt = node["damage_dealt"].as<uint64_t>(0);
            member.largestHit = node["largest_hit"].as<uint64_t>(0);
            member.damageTaken = node["damage_taken"].as<uint64_t>(0);
            member.spellsCast = node["spells_cast"].as<uint64_t>(0);
            member.healingGiven = node["healing_given"].as<uint64_t>(0);
            member.knockouts = node["knockouts"].as<uint64_t>(0);
            member.deaths = node["deaths"].as<uint64_t>(0);
            member.eradications = node["eradications"].as<uint64_t>(0);
            member.experience = node["experience"].as<uint64_t>(0);
            member.levelsGained = node["levels_gained"].as<uint64_t>(0);
            c.members[entry.first.as<std::string>()] = std::move(member);
        }
    }
}

void emitTracking(YAML::Emitter &out, const PlaythroughTrackingInfo &info)
{
    out << YAML::Key << "tracking_since_utc" << YAML::Value << info.trackingSinceUtc
        << YAML::Key << "partial" << YAML::Value << info.partial
        << YAML::Key << "sequence" << YAML::Value << info.sequence
        << YAML::Key << "integrity" << YAML::Value << YAML::BeginMap
        << YAML::Key << "development_build" << YAML::Value << info.developmentBuild
        << YAML::Key << "restored_older" << YAML::Value << info.restoredOlder
        << YAML::Key << "unverified" << YAML::Value << info.unverified
        << YAML::Key << "assists" << YAML::Value << YAML::BeginMap;

    for (const auto &[reason, assist] : info.assists)
    {
        out << YAML::Key << reason << YAML::Value << YAML::Flow << YAML::BeginMap
            << YAML::Key << "first_utc" << YAML::Value << assist.firstUtc
            << YAML::Key << "first_day" << YAML::Value << assist.firstDay
            << YAML::Key << "sessions" << YAML::Value << assist.sessions;
        emitMap(out, "commands", assist.commands);
        out << YAML::EndMap;
    }

    out << YAML::EndMap << YAML::EndMap;
}

void readTracking(const YAML::Node &root, PlaythroughTrackingInfo &info)
{
    info.trackingSinceUtc = root["tracking_since_utc"].as<std::string>("");
    info.partial = root["partial"].as<bool>(false);
    info.sequence = root["sequence"].as<uint64_t>(0);

    if (const YAML::Node integrity = root["integrity"]; integrity && integrity.IsMap())
    {
        info.developmentBuild = integrity["development_build"].as<bool>(false);
        info.restoredOlder = integrity["restored_older"].as<bool>(false);
        info.unverified = integrity["unverified"].as<bool>(false);

        if (const YAML::Node assists = integrity["assists"]; assists && assists.IsMap())
        {
            for (const auto &entry : assists)
            {
                PlaythroughAssistRecord &assist = info.assists[entry.first.as<std::string>()];
                assist.firstUtc = entry.second["first_utc"].as<std::string>("");
                assist.firstDay = entry.second["first_day"].as<double>(0.0);
                assist.sessions = entry.second["sessions"].as<uint64_t>(0);
                readMap(entry.second["commands"], assist.commands);
            }
        }
    }
}

template<typename Entry>
void pushCapped(std::vector<Entry> &log, Entry entry, size_t cap)
{
    log.push_back(std::move(entry));

    if (log.size() > cap)
    {
        log.erase(log.begin(), log.begin() + std::ptrdiff_t(log.size() - cap));
    }
}

std::string hex64(uint64_t value)
{
    char text[17] = {};
    std::snprintf(text, sizeof(text), "%016llx", static_cast<unsigned long long>(value));
    return text;
}
}

void recordMonsterDeathStatistics(Party *pParty, const MonsterTable *pMonsterTable, int16_t monsterId, bool killedByParty)
{
    PlaythroughStatistics *pStatistics = pParty != nullptr ? pParty->statistics() : nullptr;

    if (pStatistics == nullptr || !killedByParty)
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr ? pMonsterTable->findStatsById(monsterId) : nullptr;
    pStatistics->recordMonsterKilled(pStats != nullptr ? pStats->name : std::string(), pStats != nullptr ? pStats->level : 0);
}

void recordChestOpenedStatistics(Party *pParty, const std::string &mapFileName, uint32_t chestId)
{
    if (PlaythroughStatistics *pStatistics = pParty != nullptr ? pParty->statistics() : nullptr)
    {
        pStatistics->recordChestOpened(mapFileName, chestId);
    }
}

const char *statDamageSchoolName(size_t school)
{
    return school < DamageSchoolNames.size() ? DamageSchoolNames[school] : "physical";
}

const char *goldReasonName(GoldReason reason)
{
    return size_t(reason) < GoldReasonNames.size() ? GoldReasonNames[size_t(reason)] : "other";
}

uint64_t PlaythroughCounters::experienceTotal() const
{
    uint64_t total = 0;

    for (uint64_t value : experience)
    {
        total += value;
    }

    return total;
}

uint64_t PlaythroughCounters::damageDealtTotal() const
{
    uint64_t total = 0;

    for (uint64_t value : damageDealtBySchool)
    {
        total += value;
    }

    return total;
}

uint64_t PlaythroughCounters::damageTakenTotal() const
{
    uint64_t total = 0;

    for (uint64_t value : damageTaken)
    {
        total += value;
    }

    return total;
}

uint64_t PlaythroughCounters::goldLooted() const
{
    return goldGained[size_t(GoldReason::LootCorpse)] + goldGained[size_t(GoldReason::LootChest)]
        + goldGained[size_t(GoldReason::LootGround)] + goldGained[size_t(GoldReason::Event)];
}

uint64_t PlaythroughCounters::goldSpentTotal() const
{
    uint64_t total = 0;

    for (size_t index = 0; index < goldSpent.size(); ++index)
    {
        // Gold deposited in the bank and gold lost to a defeat is not spent.
        if (index != size_t(GoldReason::Bank) && index != size_t(GoldReason::Defeat))
        {
            total += goldSpent[index];
        }
    }

    return total;
}

uint64_t PlaythroughCounters::saves() const
{
    return quickSaves + autoSaves + namedSaves;
}

uint64_t PlaythroughCounters::loads() const
{
    return quickLoads + menuLoads;
}

bool PlaythroughTrackingInfo::clean() const
{
    return assists.empty() && !developmentBuild && !restoredOlder && !unverified;
}

void PlaythroughTrackingInfo::absorb(const PlaythroughTrackingInfo &other)
{
    for (const auto &[reason, theirs] : other.assists)
    {
        const auto found = assists.find(reason);

        if (found == assists.end())
        {
            assists[reason] = theirs;
            continue;
        }

        PlaythroughAssistRecord &mine = found->second;

        if (mine.firstUtc.empty() || (!theirs.firstUtc.empty() && theirs.firstUtc < mine.firstUtc))
        {
            mine.firstUtc = theirs.firstUtc;
            mine.firstDay = theirs.firstDay;
        }

        mine.sessions = std::max(mine.sessions, theirs.sessions);

        for (const auto &[command, times] : theirs.commands)
        {
            mine.commands[command] = std::max(mine.commands[command], times);
        }
    }
    developmentBuild = developmentBuild || other.developmentBuild;
    restoredOlder = restoredOlder || other.restoredOlder;
    unverified = unverified || other.unverified;
}

std::string serializePlaythroughCounters(const PlaythroughCounters &counters, const PlaythroughTrackingInfo &info)
{
    YAML::Emitter out;
    out << YAML::BeginMap
        << YAML::Key << "schema" << YAML::Value << FileSchema;
    emitTracking(out, info);
    emitCounters(out, counters);
    out << YAML::EndMap;
    return out.c_str();
}

bool parsePlaythroughCounters(const std::string &text, PlaythroughCounters &counters, PlaythroughTrackingInfo &info)
{
    try
    {
        const YAML::Node root = YAML::Load(text);

        if (!root || !root.IsMap())
        {
            return false;
        }

        readTracking(root, info);
        readCounters(root, counters);
        return true;
    }
    catch (const YAML::Exception &exception)
    {
        std::cerr << "PlaythroughStatistics: unreadable statistics: " << exception.what() << '\n';
        return false;
    }
}

PlaythroughStatistics::PlaythroughStatistics() = default;

PlaythroughStatistics::~PlaythroughStatistics()
{
    {
        std::lock_guard<std::mutex> lock(m_writerMutex);
        m_writerStop = true;
    }

    m_writerCondition.notify_all();

    if (m_writerThread.joinable())
    {
        m_writerThread.join();
    }
}

void PlaythroughStatistics::setDirectory(const std::filesystem::path &directory)
{
    m_directory = directory;
}

const std::filesystem::path &PlaythroughStatistics::directory() const
{
    return m_directory;
}

std::string PlaythroughStatistics::newPlaythroughId()
{
    std::random_device device;
    const uint64_t high = (uint64_t(device()) << 32) ^ device();
    const uint64_t low = (uint64_t(device()) << 32) ^ device();
    return hex64(high) + hex64(low);
}

std::string PlaythroughStatistics::legacyPlaythroughId(uint64_t randomRootSeed)
{
    return "legacy-" + hex64(randomRootSeed);
}

namespace
{
// The key versions a playthrough's file may carry here: this build's, then (a release build) a development build's.
std::vector<std::string> storedKeyVersions()
{
    std::vector<std::string> versions = {PlaythroughSeal::sealingKeyVersion()};

    if (PlaythroughSeal::sealsWithReleaseKey())
    {
        versions.push_back("dev");
    }

    return versions;
}

}

std::vector<std::filesystem::path> PlaythroughStatistics::storedPaths(
    const std::filesystem::path &directory,
    const std::string &playthroughId)
{
    std::vector<std::filesystem::path> paths;

    for (const std::string &keyVersion : storedKeyVersions())
    {
        paths.push_back(directory / (playthroughId + "." + keyVersion + ".oystats"));
    }

    return paths;
}

std::optional<PlaythroughStatistics::StoredSummary> PlaythroughStatistics::readStoredSummary(
    const std::filesystem::path &directory,
    const std::string &playthroughId)
{
    for (const std::filesystem::path &path : storedPaths(directory, playthroughId))
    {
        std::ifstream file(path, std::ios::binary);

        if (!file)
        {
            continue;
        }

        std::stringstream bytes;
        bytes << file.rdbuf();
        const std::optional<PlaythroughSeal::Opened> opened =
            PlaythroughSeal::open(PlaythroughSeal::Kind::Lifetime, playthroughId, bytes.str());

        if (!opened)
        {
            continue;
        }

        try
        {
            const YAML::Node root = YAML::Load(opened->text);

            if (!root || !root.IsMap())
            {
                continue;
            }

            StoredSummary summary;
            summary.header.playthroughId = playthroughId;
            summary.header.createdUtc = root["created_utc"].as<std::string>("");
            summary.header.lastPlayedUtc = root["last_played_utc"].as<std::string>("");

            if (const YAML::Node start = root["start"]; start && start.IsMap())
            {
                summary.header.startWorld = start["world"].as<std::string>("");
                summary.header.ruleset = start["ruleset"].as<std::string>("");
                summary.header.difficulty = start["difficulty"].as<std::string>("");
            }

            if (const YAML::Node time = root["time"]; time && time.IsMap())
            {
                summary.playedSeconds = time["played_seconds"].as<double>(0.0);
            }

            return summary;
        }
        catch (const YAML::Exception &)
        {
        }
    }

    return std::nullopt;
}

void PlaythroughStatistics::removeStored(const std::filesystem::path &directory, const std::string &playthroughId)
{
    for (const std::filesystem::path &path : storedPaths(directory, playthroughId))
    {
        std::error_code error;
        std::filesystem::remove(path, error);
    }
}

std::string PlaythroughStatistics::playthroughIdOfSave(const std::string &savedPlaythroughId, uint64_t randomRootSeed)
{
    if (!savedPlaythroughId.empty())
    {
        return savedPlaythroughId;
    }

    return randomRootSeed != 0 ? legacyPlaythroughId(randomRootSeed) : std::string();
}

double PlaythroughStatistics::timelinePlayedSeconds(const std::string &playthroughId, const std::string &savedTimeline)
{
    std::string text;

    if (PlaythroughSeal::looksSealed(savedTimeline))
    {
        if (const std::optional<PlaythroughSeal::Opened> opened =
                PlaythroughSeal::open(PlaythroughSeal::Kind::Timeline, playthroughId, savedTimeline))
        {
            text = opened->text;
        }
    }
    else
    {
        // Written unsealed by an early development build.
        text = savedTimeline;
    }

    PlaythroughCounters counters;
    PlaythroughTrackingInfo info;
    return !text.empty() && parsePlaythroughCounters(text, counters, info) ? counters.playedSeconds : 0.0;
}

std::string PlaythroughStatistics::memberKey(uint64_t statsMemberId)
{
    return hex64(statsMemberId);
}

void PlaythroughStatistics::beginNewPlaythrough(
    const std::string &startWorld,
    const std::string &ruleset,
    const std::string &difficulty)
{
    if (m_active)
    {
        endPlaythrough();
    }

    m_header = {};
    m_header.playthroughId = newPlaythroughId();
    m_header.createdUtc = utcNow();
    m_header.startWorld = startWorld;
    m_header.ruleset = ruleset;
    m_header.difficulty = difficulty;
    m_timeline = {};
    m_lifetime = {};
    m_timelineInfo = {};
    m_timelineInfo.trackingSinceUtc = m_header.createdUtc;
    m_timelineInfo.developmentBuild = !PlaythroughSeal::sealsWithReleaseKey();
    m_lifetimeInfo = m_timelineInfo;
    m_wipeAwaitingLoad = false;
    m_active = true;
    startSession();
    requestWrite();
}

void PlaythroughStatistics::attachLoadedSave(
    const std::string &savedPlaythroughId,
    uint64_t randomRootSeed,
    const std::string &savedTimeline,
    StatLoadKind loadKind,
    const std::string &startWorld,
    const std::string &ruleset,
    const std::string &difficulty)
{
    std::string playthroughId = playthroughIdOfSave(savedPlaythroughId, randomRootSeed);

    if (playthroughId.empty())
    {
        playthroughId = newPlaythroughId();
    }

    const bool samePlaythrough = m_active && playthroughId == m_header.playthroughId;

    if (m_active && !samePlaythrough)
    {
        endPlaythrough();
    }

    const std::string now = utcNow();
    m_header.playthroughId = playthroughId;
    readTimeline(savedTimeline, now);

    if (!samePlaythrough)
    {
        m_header = {};
        m_header.playthroughId = playthroughId;
        m_lifetime = {};
        m_lifetimeInfo = {};
        bool loaded = false;
        bool failed = false;

        // This build's own file, then (a release build) what a development build wrote, which stays as it was.
        if (!m_directory.empty())
        {
            loaded = loadFile(filePath(PlaythroughSeal::sealingKeyVersion()), failed);

            if (!loaded && PlaythroughSeal::sealsWithReleaseKey())
            {
                bool developmentFailed = false;
                loaded = loadFile(filePath("dev"), developmentFailed);
                failed = failed || developmentFailed;
            }
        }

        if (!loaded)
        {
            // No file (another installation, a save from before statistics) or one that was changed: start from the
            // save's timeline.
            m_header.createdUtc = now;
            m_header.startWorld = startWorld;
            m_header.ruleset = ruleset;
            m_header.difficulty = difficulty;
            m_lifetime = m_timeline;
            m_lifetimeInfo = m_timelineInfo;
            m_lifetimeInfo.trackingSinceUtc =
                m_timelineInfo.trackingSinceUtc.empty() ? now : m_timelineInfo.trackingSinceUtc;
            m_lifetimeInfo.partial = true;
            m_lifetimeInfo.unverified = m_lifetimeInfo.unverified || failed;
        }
        else if (m_lifetimeInfo.sequence < m_timelineInfo.sequence)
        {
            // The save was made after this copy of the lifetime was written: an older copy was put back.
            m_lifetimeInfo.restoredOlder = true;
        }

        m_active = true;
        m_wipeAwaitingLoad = false;
        startSession();
    }

    // Both copies carry every flag: what helped one part of the playthrough marks all of it.
    m_lifetimeInfo.absorb(m_timelineInfo);
    m_timelineInfo.absorb(m_lifetimeInfo);

    if (!PlaythroughSeal::sealsWithReleaseKey())
    {
        m_lifetimeInfo.developmentBuild = true;
        m_timelineInfo.developmentBuild = true;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            (loadKind == StatLoadKind::Quick ? c.quickLoads : c.menuLoads) += 1;

            if (m_wipeAwaitingLoad)
            {
                c.loadsAfterWipe += 1;
            }
        });
    m_wipeAwaitingLoad = false;
    requestWrite();
}

void PlaythroughStatistics::endPlaythrough()
{
    if (!m_active)
    {
        return;
    }

    finishSession();
    writeNow();
    m_active = false;
    m_session = {};
}

bool PlaythroughStatistics::active() const
{
    return m_active;
}

const std::string &PlaythroughStatistics::playthroughId() const
{
    return m_header.playthroughId;
}

const PlaythroughStatistics::Header &PlaythroughStatistics::header() const
{
    return m_header;
}

const PlaythroughCounters &PlaythroughStatistics::timeline() const
{
    return m_timeline;
}

const PlaythroughCounters &PlaythroughStatistics::lifetime() const
{
    return m_lifetime;
}

const PlaythroughTrackingInfo &PlaythroughStatistics::timelineInfo() const
{
    return m_timelineInfo;
}

const PlaythroughTrackingInfo &PlaythroughStatistics::lifetimeInfo() const
{
    return m_lifetimeInfo;
}

const PlaythroughStatistics::SessionCounters &PlaythroughStatistics::session() const
{
    return m_session;
}

std::string PlaythroughStatistics::serializedTimeline() const
{
    if (!m_active)
    {
        return std::string();
    }

    // The lifetime's write count goes with the save, so a lifetime copy older than the save is caught when loaded.
    PlaythroughTrackingInfo info = m_timelineInfo;
    info.sequence = m_lifetimeInfo.sequence;
    return PlaythroughSeal::seal(PlaythroughSeal::Kind::Timeline, m_header.playthroughId,
        serializePlaythroughCounters(m_timeline, info));
}

void PlaythroughStatistics::readTimeline(const std::string &savedTimeline, const std::string &now)
{
    m_timeline = {};
    m_timelineInfo = {};
    std::string text;
    bool developmentKey = false;
    bool unverified = false;

    if (PlaythroughSeal::looksSealed(savedTimeline))
    {
        const std::optional<PlaythroughSeal::Opened> opened =
            PlaythroughSeal::open(PlaythroughSeal::Kind::Timeline, m_header.playthroughId, savedTimeline);

        if (opened)
        {
            text = opened->text;
            developmentKey = opened->developmentKey;
        }
        else
        {
            // Changed, or sealed with a key this build has not (a release save in a development build).
            unverified = PlaythroughSeal::knowsKey(PlaythroughSeal::keyVersionOf(savedTimeline));
            developmentKey = !unverified;
        }
    }
    else if (!savedTimeline.empty())
    {
        // Written unsealed by an early development build.
        text = savedTimeline;
        developmentKey = true;
    }

    if (text.empty() || !parsePlaythroughCounters(text, m_timeline, m_timelineInfo))
    {
        // A save from before statistics, or one whose timeline cannot be trusted: its earlier play is not known.
        m_timeline = {};
        m_timelineInfo = {};
        m_timelineInfo.trackingSinceUtc = now;
        m_timelineInfo.partial = true;
    }

    m_timelineInfo.developmentBuild = m_timelineInfo.developmentBuild || developmentKey;
    m_timelineInfo.unverified = m_timelineInfo.unverified || unverified;
}

void PlaythroughStatistics::markAssisted(const std::string &reason, const std::string &detail)
{
    if (!m_active || reason.empty())
    {
        return;
    }

    const bool firstThisSession = m_sessionAssists.insert(reason).second;

    if (!firstThisSession && detail.empty())
    {
        return;
    }

    const std::string now = utcNow();
    const double day = gameDay();

    for (PlaythroughTrackingInfo *pInfo : {&m_timelineInfo, &m_lifetimeInfo})
    {
        PlaythroughAssistRecord &assist = pInfo->assists[reason];

        if (assist.firstUtc.empty())
        {
            assist.firstUtc = now;
            assist.firstDay = day;
        }

        assist.sessions += firstThisSession ? 1 : 0;

        if (!detail.empty())
        {
            assist.commands[detail] += 1;
        }
    }

    if (firstThisSession)
    {
        requestWrite();
    }
}

void PlaythroughStatistics::setContext(
    float gameMinutes,
    const std::string &mapFileName,
    const std::string &worldId,
    bool turnBased)
{
    m_gameMinutes = gameMinutes;
    m_turnBased = turnBased;

    if (m_mapFileName != mapFileName)
    {
        m_mapFileName = mapFileName;
    }

    if (m_worldId != worldId)
    {
        m_worldId = worldId;
    }
}

double PlaythroughStatistics::gameDay() const
{
    return double(m_gameMinutes) / (24.0 * 60.0);
}

void PlaythroughStatistics::addPlayTime(double seconds, bool turnBased)
{
    if (!m_active || seconds <= 0.0)
    {
        return;
    }

    m_session.playedSeconds += seconds;
    const double sessionSeconds = m_session.playedSeconds;
    const std::string world = m_worldId.empty() ? std::string("unknown") : m_worldId;
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.playedSeconds += seconds;
            c.playedSecondsByWorld[world] += seconds;
            c.longestSessionSeconds = std::max(c.longestSessionSeconds, sessionSeconds);

            if (turnBased)
            {
                c.turnBasedSeconds += seconds;
            }
        });
    m_secondsSinceWrite += seconds;

    if (m_secondsSinceWrite >= WriteIntervalSeconds)
    {
        requestWrite();
    }
}

void PlaythroughStatistics::requestWrite()
{
    if (!m_active || m_directory.empty())
    {
        return;
    }

    m_secondsSinceWrite = 0.0;
    m_header.lastPlayedUtc = utcNow();
    m_lifetimeInfo.sequence += 1;
    enqueueWrite(filePath(PlaythroughSeal::sealingKeyVersion()), serializeFile());
}

void PlaythroughStatistics::writeNow()
{
    if (!m_active || m_directory.empty())
    {
        return;
    }

    requestWrite();
    waitForWriter();
}

void PlaythroughStatistics::syncMember(const StatMemberRef &member)
{
    if (!m_active || member.id == 0)
    {
        return;
    }

    forBoth([&](PlaythroughCounters &c) { memberCounters(c, member); });
}

void PlaythroughStatistics::recordSave(StatSaveKind kind)
{
    if (!m_active)
    {
        return;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            switch (kind)
            {
            case StatSaveKind::Quick:
                c.quickSaves += 1;
                break;
            case StatSaveKind::Auto:
                c.autoSaves += 1;
                break;
            case StatSaveKind::Named:
                c.namedSaves += 1;
                break;
            }
        });
    m_wipeAwaitingLoad = false;
}

void PlaythroughStatistics::recordMonsterKilled(const std::string &monsterName, int level)
{
    const bool turnBased = m_turnBased;
    if (!m_active)
    {
        return;
    }

    const double day = gameDay();
    m_session.kills += 1;
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.kills += 1;

            if (!monsterName.empty())
            {
                c.killsByMonster[monsterName] += 1;
            }

            if (turnBased)
            {
                c.turnBasedKills += 1;
            }

            if (!monsterName.empty() && (c.strongestKill.empty() || level > c.strongestKillLevel))
            {
                c.strongestKill = monsterName;
                c.strongestKillLevel = level;
                c.strongestKillDay = day;
            }
        });
}

void PlaythroughStatistics::recordKillCredit(const StatMemberRef *pMember, StatKillMethod method)
{
    if (!m_active)
    {
        return;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.killsByMethod[size_t(method)] += 1;

            if (pMember != nullptr && pMember->id != 0)
            {
                memberCounters(c, *pMember).kills += 1;
            }
        });
}

void PlaythroughStatistics::recordDamageDealt(
    const StatMemberRef *pMember,
    size_t school,
    uint64_t amount,
    bool critical,
    const std::string &source,
    const std::string &target)
{
    if (!m_active || amount == 0)
    {
        return;
    }

    const size_t schoolIndex = std::min(school, StatDamageSchoolCount - 1);
    const double day = gameDay();
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.damageDealtBySchool[schoolIndex] += amount;

            if (critical)
            {
                c.criticalHits += 1;
            }

            if (pMember != nullptr && pMember->id != 0)
            {
                PlaythroughMemberCounters &member = memberCounters(c, *pMember);
                member.damageDealt += amount;
                member.largestHit = std::max(member.largestHit, amount);
            }

            if (c.largestHits.size() < LargestHitCount || amount > c.largestHits.back().amount)
            {
                PlaythroughHitRecord hit;
                hit.amount = amount;
                hit.member = pMember != nullptr ? pMember->name : std::string();
                hit.source = source;
                hit.target = target;
                hit.day = day;
                const auto position = std::find_if(c.largestHits.begin(), c.largestHits.end(),
                    [amount](const PlaythroughHitRecord &existing) { return amount > existing.amount; });
                c.largestHits.insert(position, std::move(hit));

                if (c.largestHits.size() > LargestHitCount)
                {
                    c.largestHits.pop_back();
                }
            }
        });
}

void PlaythroughStatistics::recordDamageTaken(
    const StatMemberRef &member,
    StatDamageTakenKind kind,
    uint64_t amount,
    const std::string &cause)
{
    if (!m_active || amount == 0)
    {
        return;
    }

    const double day = gameDay();
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.damageTaken[size_t(kind)] += amount;

            if (member.id != 0)
            {
                memberCounters(c, member).damageTaken += amount;
            }

            if (amount > c.largestHitTaken.amount)
            {
                c.largestHitTaken = {amount, member.name, cause, std::string(), day};
            }
        });
}

void PlaythroughStatistics::recordKnockout(const StatMemberRef &member)
{
    if (!m_active)
    {
        return;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.knockouts += 1;

            if (member.id != 0)
            {
                memberCounters(c, member).knockouts += 1;
            }
        });
}

void PlaythroughStatistics::recordDeath(const StatMemberRef &member, bool eradicated, const std::string &cause)
{
    if (!m_active)
    {
        return;
    }

    m_session.deaths += 1;
    PlaythroughLogEntry entry = {member.name, cause, m_mapFileName, gameDay()};
    forBoth(
        [&](PlaythroughCounters &c)
        {
            (eradicated ? c.eradications : c.deaths) += 1;

            if (member.id != 0)
            {
                PlaythroughMemberCounters &counters = memberCounters(c, member);
                (eradicated ? counters.eradications : counters.deaths) += 1;
            }

            c.deathCauses[cause.empty() ? std::string("unknown") : cause] += 1;
            pushCapped(c.deathLog, entry, DeathLogCount);
        });
}

void PlaythroughStatistics::recordStoned()
{
    forBoth([](PlaythroughCounters &c) { c.stonings += 1; });
}

void PlaythroughStatistics::recordPartyWipe()
{
    if (!m_active)
    {
        return;
    }

    PlaythroughLogEntry entry = {std::string(), std::string(), m_mapFileName, gameDay()};
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.partyWipes += 1;
            pushCapped(c.wipeLog, entry, WipeLogCount);
        });
    m_wipeAwaitingLoad = true;
    requestWrite();
}

void PlaythroughStatistics::recordExperience(const StatMemberRef &member, ExperienceReason reason, uint64_t amount)
{
    if (!m_active || amount == 0)
    {
        return;
    }

    m_session.experience += amount;
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.experience[size_t(reason)] += amount;

            if (member.id != 0)
            {
                memberCounters(c, member).experience += amount;
            }
        });
}

void PlaythroughStatistics::recordExperienceAward(uint64_t totalAmount)
{
    forBoth([&](PlaythroughCounters &c) { c.largestAward = std::max(c.largestAward, totalAmount); });
}

void PlaythroughStatistics::recordLevelsGained(const StatMemberRef &member, uint64_t levels)
{
    if (!m_active || levels == 0)
    {
        return;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.levelsGained += levels;

            if (member.id != 0)
            {
                memberCounters(c, member).levelsGained += levels;
            }
        });
}

void PlaythroughStatistics::recordSpellCast(
    const StatMemberRef &member,
    const std::string &spellName,
    uint64_t mana,
    bool fromScroll)
{
    if (!m_active)
    {
        return;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.spellsCast += 1;
            c.manaSpent += mana;

            if (fromScroll)
            {
                c.scrollCasts += 1;
            }

            if (!spellName.empty())
            {
                c.spellCasts[spellName] += 1;
            }

            if (member.id != 0)
            {
                memberCounters(c, member).spellsCast += 1;
            }
        });
}

void PlaythroughStatistics::recordHealing(const StatMemberRef &caster, uint64_t amount)
{
    if (amount == 0)
    {
        return;
    }

    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.healingGiven += amount;

            if (caster.id != 0)
            {
                memberCounters(c, caster).healingGiven += amount;
            }
        });
}

void PlaythroughStatistics::recordTownPortal(const std::string &destination)
{
    forBoth(
        [&](PlaythroughCounters &c)
        {
            c.townPortals += 1;

            if (!destination.empty())
            {
                c.townPortalDestinations[destination] += 1;
            }
        });
}

void PlaythroughStatistics::recordLloydsBeacon(bool recall)
{
    forBoth([&](PlaythroughCounters &c) { (recall ? c.lloydRecalls : c.lloydSets) += 1; });
}

void PlaythroughStatistics::recordTravel(bool ship, double days)
{
    forBoth(
        [&](PlaythroughCounters &c)
        {
            (ship ? c.shipTrips : c.coachTrips) += 1;
            c.travelDays += std::max(0.0, days);
        });
}

void PlaythroughStatistics::recordTempleHeal()
{
    forBoth([](PlaythroughCounters &c) { c.templeHeals += 1; });
}

void PlaythroughStatistics::recordDonation()
{
    forBoth([](PlaythroughCounters &c) { c.donations += 1; });
}

void PlaythroughStatistics::recordMapEntered(const std::string &mapFileName)
{
    if (mapFileName.empty())
    {
        return;
    }

    std::string key = mapFileName;
    std::transform(key.begin(), key.end(), key.begin(), [](unsigned char ch) { return char(std::tolower(ch)); });
    forBoth([&](PlaythroughCounters &c) { c.mapsVisited.insert(key); });
}

void PlaythroughStatistics::recordChestOpened(const std::string &mapFileName, uint32_t chestId)
{
    std::string key = mapFileName;
    std::transform(key.begin(), key.end(), key.begin(), [](unsigned char ch) { return char(std::tolower(ch)); });
    key += "#" + std::to_string(chestId);
    forBoth([&](PlaythroughCounters &c) { c.chestsOpened.insert(key); });
}

void PlaythroughStatistics::recordGold(int64_t amount, GoldReason reason)
{
    if (amount == 0)
    {
        return;
    }

    const size_t index = std::min(size_t(reason), size_t(GoldReason::Count) - 1);
    forBoth(
        [&](PlaythroughCounters &c)
        {
            if (amount > 0)
            {
                c.goldGained[index] += uint64_t(amount);
            }
            else
            {
                c.goldSpent[index] += uint64_t(-amount);
            }
        });
}

void PlaythroughStatistics::recordArtifactFound(uint32_t itemId, const std::string &name)
{
    const double day = gameDay();
    forBoth(
        [&](PlaythroughCounters &c)
        {
            const bool known = std::any_of(c.artifactsFound.begin(), c.artifactsFound.end(),
                [itemId](const PlaythroughArtifactRecord &record) { return record.itemId == itemId; });

            if (!known)
            {
                c.artifactsFound.push_back({itemId, name, day});
            }
        });
}

void PlaythroughStatistics::recordTurnBasedFight()
{
    forBoth([](PlaythroughCounters &c) { c.turnBasedFights += 1; });
}

void PlaythroughStatistics::recordTurnBasedTurn()
{
    forBoth([](PlaythroughCounters &c) { c.turnBasedTurns += 1; });
}

void PlaythroughStatistics::forBoth(const std::function<void(PlaythroughCounters &)> &apply)
{
    if (!m_active)
    {
        return;
    }

    apply(m_timeline);
    apply(m_lifetime);
}

PlaythroughMemberCounters &PlaythroughStatistics::memberCounters(
    PlaythroughCounters &counters,
    const StatMemberRef &member)
{
    const std::string key = memberKey(member.id);
    const auto found = counters.members.find(key);

    if (found != counters.members.end())
    {
        if (!member.name.empty())
        {
            found->second.name = member.name;
        }

        if (!member.className.empty())
        {
            found->second.className = member.className;
        }

        return found->second;
    }

    PlaythroughMemberCounters &created = counters.members[key];
    created.name = member.name;
    created.className = member.className;
    created.joinedDay = gameDay();
    return created;
}

std::filesystem::path PlaythroughStatistics::filePath(const std::string &keyVersion) const
{
    return m_directory / (m_header.playthroughId + "." + keyVersion + ".oystats");
}

std::string PlaythroughStatistics::serializeFile() const
{
    YAML::Emitter out;
    out << YAML::BeginMap
        << YAML::Key << "schema" << YAML::Value << FileSchema
        << YAML::Key << "playthrough" << YAML::Value << m_header.playthroughId
        << YAML::Key << "created_utc" << YAML::Value << m_header.createdUtc
        << YAML::Key << "last_played_utc" << YAML::Value << m_header.lastPlayedUtc
        << YAML::Key << "start" << YAML::Value << YAML::Flow << YAML::BeginMap
        << YAML::Key << "world" << YAML::Value << m_header.startWorld
        << YAML::Key << "ruleset" << YAML::Value << m_header.ruleset
        << YAML::Key << "difficulty" << YAML::Value << m_header.difficulty
        << YAML::EndMap;
    emitTracking(out, m_lifetimeInfo);
    emitCounters(out, m_lifetime);
    out << YAML::EndMap;
    return PlaythroughSeal::seal(
        PlaythroughSeal::Kind::Lifetime, m_header.playthroughId, std::string(out.c_str()) + "\n");
}

bool PlaythroughStatistics::loadFile(const std::filesystem::path &path, bool &failed)
{
    failed = false;
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return false;
    }

    std::stringstream bytes;
    bytes << file.rdbuf();
    const std::optional<PlaythroughSeal::Opened> opened =
        PlaythroughSeal::open(PlaythroughSeal::Kind::Lifetime, m_header.playthroughId, bytes.str());

    if (!opened)
    {
        std::cerr << "PlaythroughStatistics: " << path.string() << " cannot be authenticated\n";
        failed = true;
        return false;
    }

    try
    {
        const YAML::Node root = YAML::Load(opened->text);

        if (!root || !root.IsMap())
        {
            return false;
        }

        m_header.createdUtc = root["created_utc"].as<std::string>("");
        m_header.lastPlayedUtc = root["last_played_utc"].as<std::string>("");

        if (const YAML::Node start = root["start"]; start && start.IsMap())
        {
            m_header.startWorld = start["world"].as<std::string>("");
            m_header.ruleset = start["ruleset"].as<std::string>("");
            m_header.difficulty = start["difficulty"].as<std::string>("");
        }

        readTracking(root, m_lifetimeInfo);
        m_lifetimeInfo.developmentBuild = m_lifetimeInfo.developmentBuild || opened->developmentKey;
        readCounters(root, m_lifetime);
        return true;
    }
    catch (const YAML::Exception &exception)
    {
        std::cerr << "PlaythroughStatistics: cannot read " << path.string() << ": " << exception.what() << '\n';
        return false;
    }
}

void PlaythroughStatistics::startSession()
{
    m_session = {};
    m_sessionAssists.clear();
    m_secondsSinceWrite = 0.0;
    forBoth([](PlaythroughCounters &c) { c.sessions += 1; });
}

void PlaythroughStatistics::finishSession()
{
    m_header.lastPlayedUtc = utcNow();
}

void PlaythroughStatistics::enqueueWrite(std::filesystem::path path, std::string text)
{
    {
        std::lock_guard<std::mutex> lock(m_writerMutex);
        m_pendingWrite = std::make_pair(std::move(path), std::move(text));

        if (!m_writerThread.joinable())
        {
            m_writerThread = std::thread([this]() { writerLoop(); });
        }
    }

    m_writerCondition.notify_all();
}

void PlaythroughStatistics::writerLoop()
{
    std::unique_lock<std::mutex> lock(m_writerMutex);

    while (true)
    {
        m_writerCondition.wait(lock, [this]() { return m_writerStop || m_pendingWrite.has_value(); });

        if (!m_pendingWrite)
        {
            return;
        }

        const auto [path, text] = std::move(*m_pendingWrite);
        m_pendingWrite.reset();
        m_writerBusy = true;
        lock.unlock();

        std::error_code error;
        std::filesystem::create_directories(path.parent_path(), error);
        std::filesystem::path temporaryPath = path;
        temporaryPath += ".tmp";

        {
            std::ofstream file(temporaryPath, std::ios::binary | std::ios::trunc);
            file << text;
        }

        std::filesystem::rename(temporaryPath, path, error);

        if (error)
        {
            std::cerr << "PlaythroughStatistics: cannot write " << path.string() << ": " << error.message() << '\n';
        }

        lock.lock();
        m_writerBusy = false;
        m_writerCondition.notify_all();
    }
}

void PlaythroughStatistics::waitForWriter()
{
    std::unique_lock<std::mutex> lock(m_writerMutex);
    m_writerCondition.wait(lock, [this]() { return !m_pendingWrite && !m_writerBusy; });
}
}
