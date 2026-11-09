#pragma once

#include "game/party/SkillData.h"
#include "game/rules/ClassRules.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class MawRules;

// MAW's classes (devdocs/maw/CLASSES_SPELLS_SPEC.md §5): HP and SP from MAW's stat effects, with Personality adding to
// every class's mana and Elder and Ultimate promotions raising the per-level gains; fixed spell point pools for
// Death Knights, Dragons and the Assassin line.
class MawClassRules : public ClassRules
{
public:
    explicit MawClassRules(MawRules &rules);

    // HPBase + HPFactor x (level + E(Endurance) + Bodybuilding skill x mastery), Grandmaster counting 5 (IT:3097-3128).
    std::optional<int> baseMaxHealth(const Character &character, const ClassMultiplierEntry &entry) const override;
    // SPBase + SPFactor x (level + 2 E(Personality)) for every class with SP: MAW's SP stat is Personality for all
    // (IT:4427-4433) and addMana adds its effect again (IT:3131-3146).
    std::optional<int> baseMaxSpellPoints(const Character &character, const ClassMultiplierEntry &entry) const override;
    // SPFactor x Meditation skill x mastery (Grandmaster 5): what Meditation adds to Enlightenment's base, the only
    // place it counts (IT:3131-3146). 0 for classes without SP.
    double enlightenmentMeditationMana(const Character &character) const;
    // Death Knights and Dragons take no SP from items; the Assassin line takes 10 per Assassination (Earth) mastery
    // instead (MCC:838-840, SP:3628-3634). Races add +3 (+1 per 10 levels of the skill) to a few skills, even
    // unlearned (S:2348-2400), and their resistances and immunities (ST:1349-1383).
    void applyClassBonuses(Character &member) const override;
    // Death Knights, Elementalists and Assassins learn their spells their own way (MCC:482-493, 589-593).
    bool learnsSpellsFromBooks(const Character &character) const override;
    // MAW's dragons are the dragon race, whatever their class (zzClasses.lua:500, 652).
    bool isDragon(const Character &character) const override;
    // The counters MAW prints over the portraits (zzClasses.lua:640-650, 693-702), shown as gems: five for the
    // Assassin's combo points, ten for the Elementalist's stacks (at 10 the cast delay is back to normal).
    PortraitCounter portraitCounter(const Character &member) const override;
    // A final step promoted on two worlds reads "Elder", on three "Ultimate" (zzClasses.lua:96-104), on all four
    // "Supreme" (ours: Chedian is MAW's fourth world).
    std::string displayName(const Party &party, const Character &member) const override;
    // A kind's promotion completed on any world promotes every member of that kind to its final step (one of
    // several final classes, picked once per character from the save's seed); MAW's own kinds also take the mid step
    // from the first-tier bits of the line they borrow; two or three worlds make the final classes Elder or Ultimate
    // (CL:62-155).
    // Vampires keep Preservation up at night and indoors, except in 7d25 (SP:1081-1088, 2957-2967). Dragon-race
    // characters learn Fangs, Scales and Dragon Ability at 1 (zzClasses.lua dragonSkill); the Dragon class's pool
    // refills by 2 SP a second (5 for a Great Wyrm), doubled 20 seconds after it last fell and four times over with
    // no enemy near (S:1438-1477). Austerity gives every member Identify Monster 10 Grandmaster on each map, none after
    // a respec until the next (AL:40-46).
    void update(Party &party, const IGameplayWorldRuntime &world, float deltaSeconds) const override;
    // None in Beyond Madness (NPCMercenaries.lua:562-768).
    bool offersMercenaries() const override;
    // 4 + floor(i / 10 + 1) for each level i from 2 (NPCMercenaries.lua:196-199).
    uint32_t mercenarySkillPoints(uint32_t level) const override;
    // MAW's kinds: every continent's vanilla kinds and Peasants, MAW's own classes in Enroth (NPCMercenaries.lua:13-17).
    std::vector<uint32_t> mercenaryClassKinds(uint32_t continentId, std::vector<uint32_t> offeredKinds) const override;
    // The race's flat skill bonuses, resistances and immunities, and the vampires' night Preservation.
    std::vector<std::string> raceNotes(const Character &character) const override;
    bool showsCreationSkillMatrix() const override;
    // MAW's L key lifts the party 100 units, then waits five game minutes (zzMAW-Skills.lua:2501-2510).
    std::optional<float> unstuckLift(double gameMinutes) const override;
    // A lone Knight, Cavalier, Black Knight or Champion charges a monster 500-3000 units away: the party covers 20/22
    // of the way and the monster is paralysed 3, 4 or 5 seconds by promotion (diminishing returns), once every 25
    // seconds (zzMAW-Skills.lua:950-1037).
    std::optional<std::string> partyCharge(
        Party &party,
        IGameplayWorldRuntime &world,
        std::optional<size_t> targetActorIndex) const override;
    // Doom and the modes after it: followers join only in houses 1466 and 1486 (NPCFollowers.lua:248-253, 490-497).
    std::optional<FollowerHireRefusal> followerHireRefusal(uint32_t houseId) const override;
    std::optional<FollowerHireRefusal> paidHirelingRefusal() const override;

    // The promotions part of update(): no world needed.
    void updatePromotions(Party &party) const;
    // MM9's hirelings at the party's level: each keeps the share of MAW's expected character it has at its row's
    // level (damage, health, armour, spell skill), at the party's mean level when that is higher.
    void scaleHirelings(Party &party) const;

private:
    // The class's HP and SP per level: the table's, MAW's Lua override, times Elder (x1.25), Ultimate (x1.5) or Supreme
    // (x1.75).
    double healthPerLevel(const ClassMultiplierEntry &entry) const;
    double manaPerLevel(const ClassMultiplierEntry &entry) const;
    double promotionFactor(const ClassMultiplierEntry &entry) const;

    MawRules &m_rules;
    mutable float m_pendingSeconds = 0;
    // Runtime only: the game minute Knight Charge is ready again (MAW saves its cooldown).
    mutable double m_chargeReadyGameMinutes = 0;
    // The map Austerity last gave Identify Monster on.
    mutable std::optional<std::string> m_identifyMonsterMap;
};

// The class line a MAW class belongs to, by canonical class name: "seraphim", "death_knight", "shaman",
// "elementalist", "assassin" (the reworked Thief line), "dragon"; empty for the rest.
std::string mawClassLine(const std::string &className);

// MAW's dragon rules (Fangs, breath, Scales, no dodge, items x3) follow the portrait's race, whatever the class; only
// the fixed SP pool and its refills follow the Dragon class (zzClasses.lua, CL:765-818, S:1469-1473).
bool mawIsDragon(const Character &character);

// The Knight line reaches Supreme Armsmaster at Grandmaster and 30 base points (50 on Road to Insanity, 70 in Beyond
// Madness; S:2587-2620).
// `effectiveLevel`: the level with item and follower bonuses, as the damage rank reads it (IT:2829-2833, SKL-3); the
// weapon-skill bonus reads the trained level (S:2612-2617).
bool mawSupremeArmsmaster(const MawRules &rules, const Character &character, bool effectiveLevel = false);

// The class's flat melee damage, added the Armsmaster way (multiplied by the weapon skill's damage percent, halved
// with a weapon in the off hand; IT:2878-2919): Seraphim Mind s(m+1)/2, Shaman Earth sm/2, Death Knight Frost and
// Unholy gradual {0.5, 0.75, 1, 1} x s each, Assassin Assassination s(1+m).
double mawClassMeleeFlatDamage(const MawRules &rules, const Character &character);
// The class's melee damage multiplier: Shaman Spirit 1 + s/100 (IT:3338-3347).
double mawClassMeleeMultiplier(const Character &character);
// A character's life leech shares by kind of hit (COMBAT_SPEC.md §3.7): Vampiric and "of Darkness" weapons, Lichs'
// spells, the Vampiric Aura, the Vampire race (doubled for the Vampire classes), the Death Knight's Blood, and the
// Hades artifact's drain.
struct MawLeech
{
    double melee = 0;
    double ranged = 0;
    double spell = 0;
};

MawLeech mawLeech(const MawRules &rules, const Character &character, const ItemTable *pItemTable);

// What the class takes off hits on it (calcMawDamage's classCut and flatClassReduction, ST:742-787).
struct MawClassDefense
{
    double physicalCutSkill = 0;
    double magicCutSkill = 0;
    double flatReduction = 0;
};

// Shaman Air divides every hit by 1 + s/100, Death Knight Blood physical and Unholy other hits; the Seraphim's
// Spirit and Shaman's Water take round(monsterDamage(L + 1) x s / estimatedSkill(L) x averageTaken / 2 x
// 0.99^estimatedSkill(L)) off each hit, L the party's banked level, by the balance model of the party's size (CMB-8).
MawClassDefense mawClassDefense(const MawRules &rules, const Character &character, int partyCount);

// What an Ascension level is read for: a spell's mana, its heal, its damage, its cast time or a crowd control's
// duration.
enum class MawAscensionUse : uint8_t
{
    Cost,
    Heal,
    Damage,
    CastTime,
    // Crowd control's duration (an Elementalist reads Learning) and its cast time (an Elementalist reads the floored
    // average of the four elements, ST:176-187; SPL-11).
    CrowdControl,
    CrowdControlCastTime,
};

struct MawAscension
{
    double skill = 0;
    SkillMastery mastery = SkillMastery::None;
};

// The caster's Ascension (CLASSES_SPELLS_SPEC.md §2.1): the Learning skill; Elementalists a quarter of their four
// elements (floored for cast time) at Grandmaster for spells and their cast time; Shamans a seventh of their seven
// schools at Grandmaster for costs and heals only (their damage and cast time read Learning, which they cannot
// learn); Death Knights and Assassins none.
MawAscension mawAscension(const Character &caster, MawAscensionUse use);
// The Shaman's sum of the seven elemental and self schools (spell damage x (1 + sum/200), heals x (1 + sum/400));
// 0 for every other class.
double mawShamanSchoolSum(const Character &caster);

// The class's attack speed bonus in percent: Seraphim Light sm/2, Death Knight Frost s (S:532-539).
double mawClassAttackSpeedPercent(const Character &character);
}
