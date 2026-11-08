#pragma once

#include "game/tables/Mm9MonsterAi.h"
#include "game/tables/MonsterSpecialAttackKind.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// One parameter of a catalogued modifier: its YAML key, its kind, its default and its range (numbers) or its choices
// (`straight|expire`).
struct MonsterModifierParameterInfo
{
    enum class Kind
    {
        Number,
        Boolean,
        Text,
        Choice,
    };

    const char *pName = "";
    Kind kind = Kind::Number;
    float defaultNumber = 0.0f;
    float minimum = 0.0f;
    float maximum = 0.0f;
    // The default of a Text or Choice parameter; Choice lists its values separated by '|'.
    const char *pDefaultText = "";
    const char *pChoices = "";
    const char *pDescription = "";
};

struct MonsterModifierInfo
{
    const char *pName = "";
    const char *pDescription = "";
    std::vector<MonsterModifierParameterInfo> parameters;
};

// The modifiers a world's modifiers.yml may give its monsters, with their parameters and defaults
// (devdocs/MONSTER_MODIFIERS.md).
const std::vector<MonsterModifierInfo> &monsterModifierCatalogue();
const MonsterModifierInfo *findMonsterModifierInfo(const std::string &name);

// true_aim: the monster's projectiles home onto the target they were fired at (the party or an actor), turning at
// most turnRadiansPerSecond and keeping their speed; after maxSeconds (0: their whole flight) they fly straight on,
// or expire with expireAfter. They still collide with everything in their way.
struct TrueAimModifier
{
    float turnRadiansPerSecond = 3.14159265f;
    float maxSeconds = 4.0f;
    bool expireAfter = false;
};

// kites_party: the tactics' ranged band (ActorTacticsFacts::rangedMinDistance/rangedMaxDistance).
struct KitesPartyModifier
{
    float minDistance = 768.0f;
    float maxDistance = 2304.0f;
};

// blink: a short teleport to a free spot in sight (GameplayActorModifiers), on a hit (onHitChance), when its energy
// shield breaks (onShieldBreak) and/or every everySeconds while it fights, at most once per cooldownSeconds.
struct BlinkModifier
{
    float onHitChance = 0.0f;
    bool onShieldBreak = false;
    float everySeconds = 0.0f;
    float cooldownSeconds = 6.0f;
    float minDistance = 384.0f;
    float maxDistance = 1024.0f;
    float maxHeightChange = 256.0f;
    std::string effect = "openyamm:fx/arcane_pulse";
    // A placeholder sound name (a file of that name in a world's or the engine's audio), and what plays meanwhile.
    std::string sound = "monster_blink";
    std::string fallbackSound = "30teleport03";
};

// charge: a readable dash onto the party (GameplayActorModifiers). While the party is within
// [triggerMinDistance, triggerMaxDistance] and in sight and its cooldown is ready, it winds up for windupSeconds
// (holds and faces the party, a flash and windupSound), then dashes straight along that line at speed for up to
// maxDistance, following the floor and stopping at walls, ledges, obstacles and other actors. Reaching the party it
// hits once (its melee attack, or damage) and knocks the party back knockback units; a miss ends in a stumble of
// stumbleSeconds. Then cooldownSeconds before the next charge.
struct ChargeModifier
{
    float triggerMinDistance = 384.0f;
    float triggerMaxDistance = 1280.0f;
    float windupSeconds = 0.6f;
    float speed = 1400.0f;
    float maxDistance = 1536.0f;
    // 0 with useMelee: the monster's melee attack (Attack1) rolls the damage.
    float damage = 0.0f;
    bool useMelee = true;
    float knockback = 256.0f;
    float cooldownSeconds = 8.0f;
    float stumbleSeconds = 1.2f;
    // After a hit the charger holds this long playing its model's `charge_strike` script clip, started at
    // strikeImpactSeconds into the clip so the clip's blow meets the contact. 0: the plain 0.35 s recovery.
    float strikeSeconds = 0.0f;
    float strikeImpactSeconds = 0.0f;
    std::string effect = "openyamm:fx/ember_impact";
    // Placeholder sound names (a file of that name in a world's or the engine's audio), and what plays meanwhile.
    std::string windupSound = "monster_charge_windup";
    std::string windupFallbackSound = "roar 1";
    std::string hitSound = "monster_charge_hit";
    std::string hitFallbackSound = "swing with blunt weapon01";
};

// frenzy: a haste power-up (GameplayActorModifiers). Triggered when its health falls below healthBelow (once), every
// everySeconds while it fights (only below healthBelow when both are given) and/or when its energy shield breaks, at
// most once per cooldownSeconds. It roars for windupSeconds (holds and faces the party, effect and sound; a stun,
// paralysis or death cancels it and uses the trigger), then for seconds moves speedMultiplier faster and recovers
// from its attacks attackRateMultiplier faster with its emission glowMultiplier brighter, then holds spentSeconds.
struct FrenzyModifier
{
    float healthBelow = 0.0f;
    float everySeconds = 0.0f;
    bool onShieldBreak = false;
    float windupSeconds = 0.8f;
    float seconds = 6.0f;
    float speedMultiplier = 1.4f;
    float attackRateMultiplier = 1.5f;
    float spentSeconds = 0.0f;
    float cooldownSeconds = 20.0f;
    float glowMultiplier = 2.0f;
    std::string effect = "openyamm:fx/ember_impact";
    std::string sound = "monster_frenzy";
    std::string fallbackSound = "roar 1";
};

// stagger (COMBAT "Hesper's rules"): without a shield it flinches only when the damage it took in the last
// windowSeconds reaches thresholdPercent of its maximum health (0: every hit, as without the modifier), and after a
// flinch it ignores hit reactions for cooldownSeconds.
struct StaggerModifier
{
    float thresholdPercent = 0.0f;
    float cooldownSeconds = 0.5f;
    float windowSeconds = 2.0f;
};

// telegraphed_attack: a long, readable wind-up: its melee (and/or ranged) attack lands meleeSeconds (rangedSeconds) into
// the attack instead of at the sprite's contact frame, while its model plays the telegraphed_melee
// (telegraphed_ranged) script clip; 0 leaves that attack as it is.
struct TelegraphedAttackModifier
{
    float meleeSeconds = 0.0f;
    float rangedSeconds = 0.0f;
};

// sounds: a looping sound at the actor while it moves (or always: a hover, a servo) and a one-shot when it first
// notices the party (a turret's wind-up), by name (a world's audio files or sounds.txt).
struct ActorSoundsModifier
{
    std::string loop;
    bool loopAlways = false;
    std::string aware;
    float loopVolume = 0.7f;
};

// skirmisher: MM9's BaseMelee footwork (ActorTacticsFacts::skirmish). It keeps chasing a target that steps away while
// it attacks, runs a strafe attack at 45 degrees past the target by strafeAttackChance when it was moving as the attack
// began, and after a melee attack evades by evadeChance (backpedals for half of evadeSeconds, then circles the target)
// or backs off backOffSeconds from a strafe attack. By tauntChance it taunts (holds still for tauntSeconds, playing its
// model's taunt script clip) when it first notices the party and after a back-off; tauntSeconds 0: never.
struct SkirmisherModifier
{
    float strafeAttackChance = 0.8f;
    float evadeChance = 0.4f;
    float evadeSeconds = 2.0f;
    float backOffSeconds = 0.3f;
    float tauntChance = 0.4f;
    float tauntSeconds = 0.0f;
};

// spell_conditions: a hit on a party member by its first or second spell leaves that condition (by chance, then the
// member's save as against a special attack). None: the spell only does its damage. It also lets the monster cast
// Paralyze and Fear, which deal no damage and which a monster without a condition for them never casts. A slot's
// minutes make its condition wear off after that many game minutes (MM9's spell durations); 0 lasts until cured.
struct SpellConditionsModifier
{
    MonsterSpecialAttackKind spell1 = MonsterSpecialAttackKind::None;
    MonsterSpecialAttackKind spell2 = MonsterSpecialAttackKind::None;
    float chance = 1.0f;
    float spell1Minutes = 0.0f;
    float spell2Minutes = 0.0f;
};

// missile_blast: its first or second attack's missile bursts where it strikes (an actor, a wall, the floor), hitting
// everyone within the radius but its shooter and the shooter's friends (MM9 PROJECTILE.txt damageRadius; our units).
struct MissileBlastModifier
{
    float attack1Radius = 0.0f;
    float attack2Radius = 0.0f;
};

// reposition (an OpenYAMM addition, devdocs/MONSTER_MODIFIERS.md): a monster that holds its place to shoot or cast
// (today an MM9 ranged holder) moves to see its target again and steps back from a rush. With its target unseen for
// lostSightSeconds it asks the world for a spot within leashRadius of its post, from which it sees the target: up to
// candidates spots on two rings (half and all of searchDistance) around it, nearest first, testing at most
// maxSightChecks sight lines; it walks to the first that passes, else back to its post, and searches again only after
// retrySeconds. A target closing on it faster than backOffClosingSpeed, within backOffTriggerDistance (edge to edge)
// and outside its reach, makes it backpedal backOffDistance (a spot the world checks), then shoot or cast; the next
// back-off waits backOffCooldownSeconds.
struct RepositionModifier
{
    float lostSightSeconds = 2.0f;
    float leashRadius = 1024.0f;
    float searchDistance = 640.0f;
    int candidates = 8;
    int maxSightChecks = 12;
    float retrySeconds = 2.0f;
    float backOffTriggerDistance = 640.0f;
    float backOffClosingSpeed = 200.0f;
    float backOffDistance = 384.0f;
    float backOffCooldownSeconds = 5.0f;
};

// The modifiers of one monster id.
struct MonsterModifierSet
{
    int16_t monsterId = 0;
    std::optional<TrueAimModifier> trueAim;
    bool neverStaggers = false;
    bool indoorMeteorShower = false;
    std::optional<KitesPartyModifier> kitesParty;
    std::optional<BlinkModifier> blink;
    std::optional<ChargeModifier> charge;
    std::optional<FrenzyModifier> frenzy;
    std::optional<StaggerModifier> stagger;
    std::optional<TelegraphedAttackModifier> telegraphedAttack;
    std::optional<ActorSoundsModifier> sounds;
    std::optional<SkirmisherModifier> skirmisher;
    std::optional<SpellConditionsModifier> spellConditions;
    std::optional<MissileBlastModifier> missileBlast;
    std::optional<RepositionModifier> reposition;
    // mm9_ai: the MM9 AI profile of an MM9 row (devdocs/mm9_rework/monster_ai/PROFILE.md); generated, data only.
    std::optional<Mm9AiProfile> mm9Ai;
    // The modifier names in file order (console, logs).
    std::vector<std::string> names;
};

// Per-monster modifiers from the mounted worlds' modifiers.yml (schema openyamm.monsterModifiers.v1). A monster no
// world lists has none, so the engine behaves exactly as without the file.
class MonsterModifierTable
{
public:
    // Adds one world's file; its monster ids (single ids or ranges "first-last") must lie in [idBegin, idEnd].
    // Errors name the file and line: unknown modifiers or parameters, bad values, ids listed twice.
    bool loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t idBegin, uint32_t idEnd,
        std::string &error);
    void clear();
    bool empty() const
    {
        return m_sets.empty();
    }
    const MonsterModifierSet *find(int16_t monsterId) const;
    const std::unordered_map<int16_t, MonsterModifierSet> &sets() const
    {
        return m_sets;
    }
    // Some monster blinks (GameplayActorModifiers has work to do).
    bool hasBlink() const
    {
        return m_hasBlink;
    }
    // Some monster charges.
    bool hasCharge() const
    {
        return m_hasCharge;
    }
    // Some monster frenzies.
    bool hasFrenzy() const
    {
        return m_hasFrenzy;
    }
    // Some monster has sounds.
    bool hasSounds() const
    {
        return m_hasSounds;
    }
    // Some monster has stagger rules.
    bool hasStagger() const
    {
        return m_hasStagger;
    }
    // Some monster has an MM9 AI profile.
    bool hasMm9Ai() const
    {
        return m_hasMm9Ai;
    }

    // Test and tool setup without YAML.
    void set(const MonsterModifierSet &modifiers);

private:
    std::unordered_map<int16_t, MonsterModifierSet> m_sets;
    bool m_hasBlink = false;
    bool m_hasCharge = false;
    bool m_hasFrenzy = false;
    bool m_hasStagger = false;
    bool m_hasSounds = false;
    bool m_hasMm9Ai = false;
    int16_t m_minimumMonsterId = INT16_MAX;
    int16_t m_maximumMonsterId = INT16_MIN;
};
}
