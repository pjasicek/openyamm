#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
class Party;
struct Character;
struct ClassMultiplierEntry;

// What a class counter at a member's portrait counts (MAW: an Assassin's combo points, an Elementalist's stacks).
enum class PortraitCounterKind
{
    None,
    ComboPoints,
    Stacks
};

// A class counter the HUD shows as gems beside the member's portrait: the amount (half points light half a gem), the
// number of gems (an amount past them fills them again as a second lap) and the hover popup's title and lines.
struct PortraitCounter
{
    PortraitCounterKind kind = PortraitCounterKind::None;
    double amount = 0;
    int pips = 0;
    std::string title;
    std::vector<std::string> notes;
};

// A hire the rules forbid: what the follower's "Join" topic says instead, and the answer when chosen.
struct FollowerHireRefusal
{
    std::string topic;
    std::string message;
};

// What a character's class gives beyond its tables (devdocs/maw/HANDOFF.md phase 6): maximum HP and SP and the
// class's own bonuses. This class is the Standard MMMerge rules; a ruleset with its own classes derives from it.
class ClassRules
{
public:
    virtual ~ClassRules() = default;

    // The class's maximum HP and SP before items, buffs and skill percents, or nothing for Standard's formulas.
    virtual std::optional<int> baseMaxHealth(const Character &character, const ClassMultiplierEntry &entry) const;
    virtual std::optional<int> baseMaxSpellPoints(const Character &character, const ClassMultiplierEntry &entry) const;
    // After items, buffs and skills: what the class adds or takes away. Every ruleset: the undead (the Undead race, a
    // Lich) are immune to Mind and Body, vampires to Mind; overrides call this first.
    virtual void applyClassBonuses(Character &member) const;
    // Whether spell books can teach the character. Standard: always.
    virtual bool learnsSpellsFromBooks(const Character &character) const;
    // Whether the character fights as a dragon: breath attack, Dragon Ability bite and scales. Standard: the Dragon and
    // Great Wyrm classes.
    virtual bool isDragon(const Character &character) const;
    // The class counter the HUD shows at the member's portrait (MAW: an Assassin's combo points, an Elementalist's
    // stacks). Standard: none.
    virtual PortraitCounter portraitCounter(const Character &member) const;
    // The class name a party member's screens show (MAW: Elder and Ultimate for a final step promoted on two or three
    // worlds). Standard: the class's display name.
    virtual std::string displayName(const Party &party, const Character &member) const;
    // Each frame of play: promotions the rules grant from the party's quest state and the classes' and races' own
    // timed effects (MAW's cross-world promotions, the vampires' night). Standard: none; promotions come from the
    // events.
    virtual void update(Party &party, const IGameplayWorldRuntime &world, float deltaSeconds) const;
    // Whether the inns offer generated mercenaries at all. Standard: yes.
    virtual bool offersMercenaries() const;
    // The skill points a generated mercenary of this level spends. Standard: 5 a level after the first.
    virtual uint32_t mercenarySkillPoints(uint32_t level) const;
    // The class kinds mercenaries come from on a continent (1 Jadame, 2 Antagarich, 3 Enroth), given the kinds the
    // character selection offers there. Standard: those.
    virtual std::vector<uint32_t> mercenaryClassKinds(uint32_t continentId, std::vector<uint32_t> offeredKinds) const;
    // The race card of character creation: what the character's race gives. Standard: nothing, no card.
    virtual std::vector<std::string> raceNotes(const Character &character) const;
    // Whether character creation's class popup lists the class/skill matrix (MAW). Standard: no.
    virtual bool showsCreationSkillMatrix() const;
    // How high the Unstuck action lifts the party at this game minute (MAW: 100, once per five game minutes), or
    // nothing when it may not. Standard: nothing.
    virtual std::optional<float> unstuckLift(double gameMinutes) const;
    // The charge action at the monster under the cursor (MAW's Knight Charge): the rules check it, throw the party at
    // the monster and stun it, and return the status line (empty without a target); nothing when the party has no
    // charge. Standard: nothing.
    virtual std::optional<std::string> partyCharge(
        Party &party,
        IGameplayWorldRuntime &world,
        std::optional<size_t> targetActorIndex) const;
    // Why NPC followers will not join in this house (0 outdoors), or nothing when they do. Standard: they do.
    virtual std::optional<FollowerHireRefusal> followerHireRefusal(uint32_t houseId) const;
    // Why a paid MM9 hireling will not join, or nothing when it does (MAW: as its followers, from Doom up; story
    // companions always join). Standard: it does.
    virtual std::optional<FollowerHireRefusal> paidHirelingRefusal() const;
};

const ClassRules &standardClassRules();
}
