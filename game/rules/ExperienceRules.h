#pragma once

#include "game/rules/ActorRulesetFacts.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Character;
class Party;

// A slain monster, as the experience rules see it.
struct MonsterKillReward
{
    // The monster table's experience and hit points, the bolster scaling of the kill (Standard), and the actor's own
    // maximum HP and ruleset facts (rulesets that size monsters themselves).
    int baseExperience = 0;
    int baseHitPoints = 0;
    float bolsterRewardMultiplier = 1.0f;
    int maxHp = 0;
    ActorRulesetFacts facts;
    // The continent of the map the kill happened on (map table id).
    uint32_t continentId = 0;
    // The slain monster fought for the party (ally 999), and the killer was a monster fighting for the party. Standard
    // rewards only the party's own kills, and those in full.
    bool partyAlly = false;
    bool byPartyAlly = false;
};

// How far the party has cleared the map it is on, counted after a kill.
struct MapKillProgress
{
    std::string mapFileName;
    uint32_t continentId = 0;
    bool indoor = false;
    // Monsters that count: the slain and the living hostile ones.
    int countedMonsters = 0;
    int slainMonsters = 0;
    // Living hostile monsters the map hides (invisible), counted apart.
    int hiddenMonsters = 0;
    // The living counted monsters, hidden ones included (actor indices): what is left to clear (`actor remaining`).
    std::vector<size_t> remainingActors;
    // The summed level of the counted monsters, hidden ones included, and how many they are.
    double monsterLevelSum = 0;
    int levelledMonsters = 0;
};

// How experience is earned and what training needs (devdocs/maw/HANDOFF.md §3.5). This class is the Standard
// MMMerge rules; a ruleset that changes them derives from it and overrides only what differs. The party holds the
// active one.
class ExperienceRules
{
public:
    virtual ~ExperienceRules() = default;

    // Experience a character of this level needs to train to the next.
    virtual uint64_t experienceForNextLevel(uint32_t level) const;
    // Grants a kill's experience to the party and returns the experience the kill was worth.
    virtual uint32_t grantKillExperience(Party &party, const MonsterKillReward &kill) const;
    // The experience each of recipientCount members gets from an event's AddValue(Experience, value) on a map of this
    // continent (MAW: more for a party with levels banked elsewhere, the rest banked once for all of them, so every
    // recipient gets the same). Standard: the value.
    virtual int64_t eventExperience(Party &party, int64_t value, uint32_t continentId, size_t recipientCount) const;
    // Extra gold for an NPC topic that paid gold and experience (MAW: gold x L / 100 + 250 L for the levels L banked
    // outside the continent). Standard: none.
    virtual int questGoldBonus(int gold, uint32_t continentId) const;
    // After a kill: a ruleset may reward clearing the map (MAW's map completion). Returns the status text to show, or
    // nothing. Standard has no map rewards.
    virtual std::string rewardMapProgress(Party &party, const MapKillProgress &progress) const;
    // The level a training hall trains up to (0: unlimited), from its table cap. Standard: the table's.
    virtual int trainingLevelCap(int tableCap) const;
    // The game minutes a training takes, from Standard's (a week, to the next dawn, plus 4 hours).
    virtual float trainingDurationMinutes(float standardMinutes) const;
    // Whether Learning adds its percent to shared experience (Standard; MAW's Learning is Ascension and adds none).
    virtual bool learningGrantsExperience() const;
    // The most experience a character can hold. Standard: 4 billion, as the original games.
    virtual uint64_t maximumExperience() const;
    // Once, when a new game's party is created, before the first map: a ruleset's own start (MAW's challenge modes:
    // starting gold and experience, Beyond Madness's level 1). Standard: nothing.
    virtual void prepareNewParty(Party &party) const;
    // A recruitable character just built from the roster table (not one dismissed and hired again). Standard: nothing.
    virtual void prepareRosterCharacter(Character &character) const;
    // A run's death count kept outside the save, for the character screen (MAW's Beyond Madness ledger). Standard:
    // nothing.
    virtual std::optional<int> runDeaths() const;
    // Real seconds until a pending death clears, for the gameplay HUD; nothing while none is pending. Standard: none.
    virtual std::optional<int> deathPendingSeconds(double gameMinutes) const;
    // What loading a save from play asks the player to confirm, when loading costs something now (MAW: a pending
    // death counts). Standard: nothing.
    virtual std::optional<std::string> loadWarning() const;
};

const ExperienceRules &standardExperienceRules();
}
