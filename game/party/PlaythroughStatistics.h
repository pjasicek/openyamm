#pragma once

#include "game/party/PlaythroughStatisticsTypes.h"

#include <array>
#include <condition_variable>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <thread>
#include <vector>

namespace OpenYAMM::Game
{
class MonsterTable;
class Party;

// Damage schools in CombatDamageType order (game/gameplay/GameMechanics.h).
constexpr size_t StatDamageSchoolCount = 12;
const char *statDamageSchoolName(size_t school);
const char *goldReasonName(GoldReason reason);

struct PlaythroughMemberCounters
{
    std::string name;
    std::string className;
    double joinedDay = 0.0;
    uint64_t kills = 0;
    uint64_t damageDealt = 0;
    uint64_t largestHit = 0;
    uint64_t damageTaken = 0;
    uint64_t spellsCast = 0;
    uint64_t healingGiven = 0;
    uint64_t knockouts = 0;
    uint64_t deaths = 0;
    uint64_t eradications = 0;
    uint64_t experience = 0;
    uint64_t levelsGained = 0;
};

struct PlaythroughHitRecord
{
    uint64_t amount = 0;
    std::string member;
    std::string source;
    std::string target;
    double day = 0.0;
};

struct PlaythroughLogEntry
{
    std::string member;
    std::string cause;
    std::string map;
    double day = 0.0;
};

struct PlaythroughArtifactRecord
{
    uint32_t itemId = 0;
    std::string name;
    double day = 0.0;
};

// One copy of every counter. The statistics keep two: the timeline (saved inside each save, so loading puts it back)
// and the lifetime (the playthrough's sidecar file, which loading never lowers).
struct PlaythroughCounters
{
    // Real time, in seconds; counted only while playing (GameApplication::updatePlaythroughPlayTime).
    double playedSeconds = 0.0;
    double turnBasedSeconds = 0.0;
    std::map<std::string, double> playedSecondsByWorld;
    uint64_t sessions = 0;
    double longestSessionSeconds = 0.0;
    uint64_t turnBasedFights = 0;
    uint64_t turnBasedTurns = 0;
    uint64_t turnBasedKills = 0;

    uint64_t quickSaves = 0;
    uint64_t autoSaves = 0;
    uint64_t namedSaves = 0;
    uint64_t quickLoads = 0;
    uint64_t menuLoads = 0;
    uint64_t loadsAfterWipe = 0;

    // Kills by the party: the total, those with a known member and method, and by monster name.
    uint64_t kills = 0;
    std::array<uint64_t, size_t(StatKillMethod::Count)> killsByMethod = {};
    std::map<std::string, uint64_t> killsByMonster;
    std::string strongestKill;
    int strongestKillLevel = 0;
    double strongestKillDay = 0.0;

    std::array<uint64_t, StatDamageSchoolCount> damageDealtBySchool = {};
    uint64_t criticalHits = 0;
    // The five largest single hits, largest first.
    std::vector<PlaythroughHitRecord> largestHits;
    std::array<uint64_t, size_t(StatDamageTakenKind::Count)> damageTaken = {};
    PlaythroughHitRecord largestHitTaken;

    std::map<std::string, uint64_t> spellCasts;
    uint64_t spellsCast = 0;
    uint64_t scrollCasts = 0;
    uint64_t manaSpent = 0;
    uint64_t healingGiven = 0;

    std::array<uint64_t, size_t(ExperienceReason::Count)> experience = {};
    uint64_t largestAward = 0;
    uint64_t levelsGained = 0;

    uint64_t deaths = 0;
    uint64_t eradications = 0;
    uint64_t stonings = 0;
    uint64_t knockouts = 0;
    uint64_t partyWipes = 0;
    std::map<std::string, uint64_t> deathCauses;
    // The latest deaths and wipes, newest last.
    std::vector<PlaythroughLogEntry> deathLog;
    std::vector<PlaythroughLogEntry> wipeLog;

    uint64_t templeHeals = 0;
    uint64_t donations = 0;

    uint64_t townPortals = 0;
    std::map<std::string, uint64_t> townPortalDestinations;
    uint64_t lloydRecalls = 0;
    uint64_t lloydSets = 0;
    uint64_t coachTrips = 0;
    uint64_t shipTrips = 0;
    double travelDays = 0.0;

    std::set<std::string> mapsVisited;
    // "<map>#<chest id>": each chest counts once, however often it is opened.
    std::set<std::string> chestsOpened;

    std::array<uint64_t, size_t(GoldReason::Count)> goldGained = {};
    std::array<uint64_t, size_t(GoldReason::Count)> goldSpent = {};
    std::vector<PlaythroughArtifactRecord> artifactsFound;

    // Keyed by Character::statsMemberId in hex.
    std::map<std::string, PlaythroughMemberCounters> members;

    uint64_t experienceTotal() const;
    uint64_t damageDealtTotal() const;
    uint64_t damageTakenTotal() const;
    uint64_t goldLooted() const;
    uint64_t goldSpentTotal() const;
    uint64_t saves() const;
    uint64_t loads() const;
};

// One kind of help the party had (a development option, the debug console): when it was first used, in how many
// sessions, and the console commands by name.
struct PlaythroughAssistRecord
{
    std::string firstUtc;
    double firstDay = 0.0;
    uint64_t sessions = 0;
    std::map<std::string, uint64_t> commands;
};

// When tracking began, whether earlier play is missing, and why the record may not be a clean playthrough. The flags
// are sticky: once set they stay in both copies for the rest of the playthrough.
struct PlaythroughTrackingInfo
{
    std::string trackingSinceUtc;
    bool partial = false;
    // What helped the party: "debug console", "immortal", "turbo movement" and the like (markAssisted).
    std::map<std::string, PlaythroughAssistRecord> assists;
    // A build with the public development key wrote the record, or wrote it unsealed.
    bool developmentBuild = false;
    // The lifetime file was older than a save of the playthrough: an older copy was put back.
    bool restoredOlder = false;
    // A copy was changed or could not be authenticated, so the record restarted from what could be.
    bool unverified = false;
    // Lifetime: how often it was written. Timeline: the lifetime's count when the save was made.
    uint64_t sequence = 0;

    bool clean() const;
    // Takes on the other copy's sticky flags.
    void absorb(const PlaythroughTrackingInfo &other);
};

std::string serializePlaythroughCounters(const PlaythroughCounters &counters, const PlaythroughTrackingInfo &info);
bool parsePlaythroughCounters(const std::string &text, PlaythroughCounters &counters, PlaythroughTrackingInfo &info);

// A monster died on the map (both worlds' death hooks): the party's kills by monster name.
void recordMonsterDeathStatistics(Party *pParty, const MonsterTable *pMonsterTable, int16_t monsterId, bool killedByParty);

// A chest opened (both worlds' attemptOpenChest).
void recordChestOpenedStatistics(Party *pParty, const std::string &mapFileName, uint32_t chestId);

// One playthrough's statistics: the timeline and lifetime counters, the session, and the sidecar file
// saves/playthroughs/<id>.yml. Every record call adds to both copies. GameSession owns it; Party points to it.
class PlaythroughStatistics
{
public:
    struct Header
    {
        std::string playthroughId;
        std::string createdUtc;
        std::string lastPlayedUtc;
        std::string startWorld;
        std::string ruleset;
        std::string difficulty;
    };

    // What a playthrough's statistics file says of it, for the save lists.
    struct StoredSummary
    {
        Header header;
        double playedSeconds = 0.0;
    };

    struct SessionCounters
    {
        double playedSeconds = 0.0;
        uint64_t kills = 0;
        uint64_t experience = 0;
        uint64_t deaths = 0;
    };

    PlaythroughStatistics();
    ~PlaythroughStatistics();
    PlaythroughStatistics(const PlaythroughStatistics &) = delete;
    PlaythroughStatistics &operator=(const PlaythroughStatistics &) = delete;

    // The folder of the sidecar files; empty disables writing (tools, headless tests).
    void setDirectory(const std::filesystem::path &directory);
    const std::filesystem::path &directory() const;

    // A new party: a new id, empty counters, the first session.
    void beginNewPlaythrough(const std::string &startWorld, const std::string &ruleset, const std::string &difficulty);
    // A loaded save. The id is the save's, else derived from its random root seed (saves made before statistics).
    // The timeline comes from the save; the lifetime from the sidecar, else from the timeline (marked partial).
    void attachLoadedSave(
        const std::string &savedPlaythroughId,
        uint64_t randomRootSeed,
        const std::string &savedTimeline,
        StatLoadKind loadKind,
        const std::string &startWorld,
        const std::string &ruleset,
        const std::string &difficulty);
    // Returning to the menu: writes the file and ends the session.
    void endPlaythrough();
    bool active() const;

    const std::string &playthroughId() const;
    const Header &header() const;
    const PlaythroughCounters &timeline() const;
    const PlaythroughCounters &lifetime() const;
    const PlaythroughTrackingInfo &timelineInfo() const;
    const PlaythroughTrackingInfo &lifetimeInfo() const;
    const SessionCounters &session() const;
    // The timeline as saved inside a save.
    std::string serializedTimeline() const;

    // The world clock, place and turn-based mode the next recordings are stamped with.
    void setContext(float gameMinutes, const std::string &mapFileName, const std::string &worldId, bool turnBased);
    double gameDay() const;

    // Real time spent playing; turnBased adds it to the turn-based time as well.
    void addPlayTime(double seconds, bool turnBased);

    // Writes the sidecar on a worker thread when due (every 60 s of play) or when forced.
    void requestWrite();
    // Writes the sidecar now and waits for it.
    void writeNow();

    // Marks the playthrough as helped (a development option or the debug console); shown on the Statistics page.
    // Cheap to call every frame: after the first call of a session only `detail` (a console command) adds anything.
    void markAssisted(const std::string &reason, const std::string &detail = std::string());

    void syncMember(const StatMemberRef &member);

    void recordSave(StatSaveKind kind);
    void recordMonsterKilled(const std::string &monsterName, int level);
    void recordKillCredit(const StatMemberRef *pMember, StatKillMethod method);
    void recordDamageDealt(
        const StatMemberRef *pMember,
        size_t school,
        uint64_t amount,
        bool critical,
        const std::string &source,
        const std::string &target);
    void recordDamageTaken(const StatMemberRef &member, StatDamageTakenKind kind, uint64_t amount, const std::string &cause);
    void recordKnockout(const StatMemberRef &member);
    void recordDeath(const StatMemberRef &member, bool eradicated, const std::string &cause);
    void recordStoned();
    void recordPartyWipe();
    void recordExperience(const StatMemberRef &member, ExperienceReason reason, uint64_t amount);
    void recordExperienceAward(uint64_t totalAmount);
    void recordLevelsGained(const StatMemberRef &member, uint64_t levels);
    void recordSpellCast(const StatMemberRef &member, const std::string &spellName, uint64_t mana, bool fromScroll);
    void recordHealing(const StatMemberRef &caster, uint64_t amount);
    void recordTownPortal(const std::string &destination);
    void recordLloydsBeacon(bool recall);
    void recordTravel(bool ship, double days);
    void recordTempleHeal();
    void recordDonation();
    void recordMapEntered(const std::string &mapFileName);
    void recordChestOpened(const std::string &mapFileName, uint32_t chestId);
    void recordGold(int64_t amount, GoldReason reason);
    void recordArtifactFound(uint32_t itemId, const std::string &name);
    void recordTurnBasedFight();
    void recordTurnBasedTurn();

    // Statistics files: tests and the headless runs.
    // Reads a playthrough's statistics file in `directory` (this build's, else a development build's) without
    // attaching to it; nothing when it has none here or the file cannot be opened.
    static std::optional<StoredSummary> readStoredSummary(
        const std::filesystem::path &directory,
        const std::string &playthroughId);
    // The files that readStoredSummary tries, in its order.
    static std::vector<std::filesystem::path> storedPaths(
        const std::filesystem::path &directory,
        const std::string &playthroughId);
    // Deletes a playthrough's statistics files in `directory` (the playthrough is not the active one).
    static void removeStored(const std::filesystem::path &directory, const std::string &playthroughId);
    static std::string newPlaythroughId();
    static std::string legacyPlaythroughId(uint64_t randomRootSeed);
    // The playthrough a save belongs to: its own id, else the one its random root seed names (saves from before
    // statistics), else none.
    static std::string playthroughIdOfSave(const std::string &savedPlaythroughId, uint64_t randomRootSeed);
    // The real time played that a save's timeline holds; 0 when it has none or cannot be opened.
    static double timelinePlayedSeconds(const std::string &playthroughId, const std::string &savedTimeline);
    static std::string memberKey(uint64_t statsMemberId);

private:
    void forBoth(const std::function<void(PlaythroughCounters &)> &apply);
    PlaythroughMemberCounters &memberCounters(PlaythroughCounters &counters, const StatMemberRef &member);
    std::filesystem::path filePath(const std::string &keyVersion) const;
    std::string serializeFile() const;
    // Opens the lifetime file sealed with this key version; nothing when it is missing. `failed` reports one that
    // exists but cannot be authenticated with a key this build has.
    bool loadFile(const std::filesystem::path &path, bool &failed);
    void readTimeline(const std::string &savedTimeline, const std::string &now);
    void startSession();
    void finishSession();
    void enqueueWrite(std::filesystem::path path, std::string text);
    void writerLoop();
    void waitForWriter();

    std::filesystem::path m_directory;
    bool m_active = false;
    Header m_header;
    PlaythroughCounters m_timeline;
    PlaythroughCounters m_lifetime;
    PlaythroughTrackingInfo m_timelineInfo;
    PlaythroughTrackingInfo m_lifetimeInfo;
    SessionCounters m_session;
    bool m_wipeAwaitingLoad = false;
    double m_secondsSinceWrite = 0.0;
    float m_gameMinutes = 0.0f;
    std::string m_mapFileName;
    std::string m_worldId;
    bool m_turnBased = false;
    // Assists already counted this session.
    std::set<std::string> m_sessionAssists;

    std::mutex m_writerMutex;
    std::condition_variable m_writerCondition;
    std::optional<std::pair<std::filesystem::path, std::string>> m_pendingWrite;
    bool m_writerBusy = false;
    bool m_writerStop = false;
    std::thread m_writerThread;
};
}
