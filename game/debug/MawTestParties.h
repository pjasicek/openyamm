#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameDataLoader;
class MawRules;
class Party;
struct Character;

// The debug console's MAW test parties (`testparty`): ready-made parties at stages of a MAW game, so MAW's authors
// can check any part of it without grinding. The catalog is engine/rulesets/maw/debug/test_parties.yml; nothing here
// runs outside the console and its scenario step.

// Gear in every slot a member can wear: MAW's rolled items of this rarity at this drop level.
struct MawTestPartyGear
{
    int level = 0;
    std::string rarity;
};

// One kind of item a kit gives: the ids firstId..lastId, count of each; or one rolled item per legendary affix
// firstAffix..lastAffix; or count dimension maps of a power; or every MAW artifact.
struct MawTestPartyKitItem
{
    uint32_t firstId = 0;
    uint32_t lastId = 0;
    uint32_t count = 1;
    int power = 0;
    int firstAffix = 0;
    int lastAffix = 0;
    int level = 0;
    bool dimensionMap = false;
    bool artifacts = false;
};

struct MawTestPartyKit
{
    std::string id;
    std::string title;
    std::vector<MawTestPartyKitItem> items;
};

struct MawTestPartyMember
{
    std::string name;
    std::string className;
    // The class the member plays at stages that promote (empty: the base class).
    std::string promotedClassName;
    // A race to pick the portrait by (empty: the class's own portraits).
    std::string race;
};

struct MawTestPartyParty
{
    std::string id;
    std::string title;
    std::vector<MawTestPartyMember> members;
};

// One worn item written out in full (the solo simulation's kits, devdocs/maw/solo_sim).
struct MawTestPartyExactItem
{
    int slot = 0;
    uint32_t itemId = 0;
    uint16_t enchantId = 0;
    uint16_t enchantPower = 0;
    uint16_t secondEnchantId = 0;
    uint16_t secondEnchantPower = 0;
    uint16_t specialEnchantId = 0;
    uint16_t itemPower = 0;
    uint8_t rarity = 0;
    uint16_t dropLevel = 0;
    uint16_t legendaryAffixId = 0;
    uint8_t qualityPercent = 0;
    uint8_t ancientTier = 0;
};

// A one-member party's build written out in full, in place of the stage's generic stats, skills and rolled gear:
// the seven stats (Might, Intellect, Personality, Endurance, Accuracy, Speed, Luck), its skills with their masteries
// and what it wears.
struct MawTestPartyBuild
{
    // The party it is for (MawTestPartyParty::id).
    std::string party;
    std::array<uint32_t, 7> stats = {};
    struct Skill
    {
        std::string name;
        uint32_t level = 1;
        uint32_t mastery = 1;
    };
    std::vector<Skill> skills;
    std::vector<MawTestPartyExactItem> worn;
};

struct MawTestPartyStage
{
    std::string id;
    std::string title;
    int level = 1;
    // Every skill the class can learn, at this level (within the ruleset's caps), at the highest mastery the class and
    // the level allow.
    int skillLevel = 1;
    int stats = 15;
    bool promoted = false;
    MawTestPartyGear gear;
    // MAW's level banks: MM8, MM7, MM6, other.
    std::vector<double> banks;
    int gold = 0;
    int food = 0;
    std::vector<std::string> kits;
    std::vector<std::string> completedMaps;
    // Every map counts as completed (the dimension map pool, map completion rewards taken).
    bool completeAllMaps = false;
    bool dimensionQuestDone = false;
    std::vector<uint32_t> questBits;
    // Where `testparty` starts the new game (empty: the start of MM8).
    std::string map;
    // The party it plays without one named.
    std::string party;
    // Builds written out in full for some parties (`builds`); the others get the generic stats, skills and gear.
    std::vector<MawTestPartyBuild> builds;

    const MawTestPartyBuild *build(const std::string &partyId) const;
};

struct MawTestPartyCatalog
{
    std::vector<MawTestPartyStage> stages;
    std::vector<MawTestPartyParty> parties;
    std::vector<MawTestPartyKit> kits;

    bool loadFromYaml(const std::string &text, std::string &errorMessage);
    const MawTestPartyStage *stage(const std::string &id) const;
    const MawTestPartyParty *party(const std::string &id) const;
    const MawTestPartyKit *kit(const std::string &id) const;
    // The stages, parties and kits with their titles, for the console.
    std::string listing() const;
};

inline constexpr const char *MawTestPartyCatalogPath = "engine/rulesets/maw/debug/test_parties.yml";
inline constexpr const char *MawTestPartyRulesetId = "maw";

// What the console asked for: `<stage> [party] [+kit ...] [ruleset option ...]`.
struct MawTestPartyRequest
{
    const MawTestPartyStage *pStage = nullptr;
    const MawTestPartyParty *pParty = nullptr;
    std::vector<const MawTestPartyKit *> kits;
    // Ruleset option ids joined by ':' (hell:horizontal:doom), for a new game.
    std::string rulesetOptions;
};

bool parseMawTestPartyRequest(
    const std::vector<std::string> &args,
    const MawTestPartyCatalog &catalog,
    MawTestPartyRequest &request,
    std::string &errorMessage);

// Level-1 members of the request's party with their names, classes and portraits, for the new game's party.
std::vector<Character> mawTestPartyShells(const MawTestPartyRequest &request, const GameDataLoader &data);

// Makes the party the request's: its members at the stage (level, stats, skills, spells, worn gear), the stage's and
// the request's kits in their bags, gold and food, and MAW's level banks and completed maps. Returns what it did.
std::string applyMawTestParty(
    Party &party,
    MawRules &rules,
    const GameDataLoader &data,
    const MawTestPartyCatalog &catalog,
    const MawTestPartyRequest &request,
    uint32_t seed);

// Puts a kit's items into the party's bags; returns what it did.
std::string addMawTestPartyKit(
    Party &party,
    MawRules &rules,
    const GameDataLoader &data,
    const MawTestPartyKit &kit,
    uint32_t seed);
}
