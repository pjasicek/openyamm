#include "game/tables/MonsterModifiers.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *ModifiersSchema = "openyamm.monsterModifiers.v1";
constexpr float DegreesToRadians = 3.14159265f / 180.0f;

using Kind = MonsterModifierParameterInfo::Kind;

constexpr const char *SpellConditionChoices = "none|afraid|asleep|cursed|weak|drunk|insane|paralyzed|poisoned_weak|"
    "poisoned_medium|poisoned_severe|diseased_weak|diseased_medium|diseased_severe|stoned";

MonsterSpecialAttackKind spellConditionKind(const std::string &name)
{
    static const std::pair<const char *, MonsterSpecialAttackKind> Kinds[] = {
        {"afraid", MonsterSpecialAttackKind::Fear},
        {"asleep", MonsterSpecialAttackKind::Sleep},
        {"cursed", MonsterSpecialAttackKind::Curse},
        {"weak", MonsterSpecialAttackKind::Weak},
        {"drunk", MonsterSpecialAttackKind::Drunk},
        {"insane", MonsterSpecialAttackKind::Insane},
        {"paralyzed", MonsterSpecialAttackKind::Paralyze},
        {"poisoned_weak", MonsterSpecialAttackKind::PoisonWeak},
        {"poisoned_medium", MonsterSpecialAttackKind::PoisonMedium},
        {"poisoned_severe", MonsterSpecialAttackKind::PoisonSevere},
        {"diseased_weak", MonsterSpecialAttackKind::DiseaseWeak},
        {"diseased_medium", MonsterSpecialAttackKind::DiseaseMedium},
        {"diseased_severe", MonsterSpecialAttackKind::DiseaseSevere},
        {"stoned", MonsterSpecialAttackKind::Petrify},
    };
    for (const auto &[pName, kind] : Kinds)
    {
        if (name == pName)
        {
            return kind;
        }
    }
    return MonsterSpecialAttackKind::None;
}

MonsterModifierParameterInfo number(const char *pName, float defaultValue, float minimum, float maximum,
    const char *pDescription)
{
    MonsterModifierParameterInfo info;
    info.pName = pName;
    info.kind = Kind::Number;
    info.defaultNumber = defaultValue;
    info.minimum = minimum;
    info.maximum = maximum;
    info.pDescription = pDescription;
    return info;
}

MonsterModifierParameterInfo boolean(const char *pName, bool defaultValue, const char *pDescription)
{
    MonsterModifierParameterInfo info;
    info.pName = pName;
    info.kind = Kind::Boolean;
    info.defaultNumber = defaultValue ? 1.0f : 0.0f;
    info.pDescription = pDescription;
    return info;
}

MonsterModifierParameterInfo text(const char *pName, const char *pDefault, const char *pDescription)
{
    MonsterModifierParameterInfo info;
    info.pName = pName;
    info.kind = Kind::Text;
    info.pDefaultText = pDefault;
    info.pDescription = pDescription;
    return info;
}

MonsterModifierParameterInfo choice(const char *pName, const char *pDefault, const char *pChoices,
    const char *pDescription)
{
    MonsterModifierParameterInfo info = text(pName, pDefault, pDescription);
    info.kind = Kind::Choice;
    info.pChoices = pChoices;
    return info;
}

std::vector<MonsterModifierInfo> buildCatalogue()
{
    return {
        {"true_aim",
            "Its projectiles home onto the target they were fired at (the party or an actor): they turn toward its "
            "current position, keep their speed and still hit whatever is in the way, so only cover stops them.",
            {
                number("turn_degrees_per_second", 180.0f, 1.0f, 3600.0f, "the most a projectile turns per second"),
                number("max_seconds", 4.0f, 0.0f, 60.0f, "how long it homes; 0: its whole flight"),
                choice("then", "straight", "straight|expire", "after max_seconds: fly straight on or expire"),
            }},
        {"never_staggers",
            "Hits never interrupt it: no hit reaction (the flinch and its knock-back). Stuns and paralysis from "
            "spells, skills and the EMP grenade still apply.",
            {}},
        {"indoor_meteor_shower",
            "It casts its Meteor Shower indoors too, each meteor from as high as the room's ceiling allows. Without "
            "it a monster never picks Meteor Shower indoors (the original game drops the cast there).",
            {}},
        {"stagger",
            "Without a shield it flinches only from heavy damage: the damage of the last window_seconds must reach "
            "threshold_percent of its maximum health, and after a flinch it ignores hits for cooldown_seconds.",
            {
                number("threshold_percent", 0.0f, 0.0f, 100.0f,
                    "share of its maximum health the window's damage must reach (0: every hit)"),
                number("cooldown_seconds", 0.5f, 0.0f, 60.0f, "no hit reaction for this long after a flinch"),
                number("window_seconds", 2.0f, 0.1f, 30.0f, "how far back its damage counts"),
            }},
        {"telegraphed_attack",
            "A long, readable wind-up: its melee and/or ranged attack lands this many seconds into the attack, while "
            "its model plays the telegraphed_melee or telegraphed_ranged script clip (actors.yml script_clips).",
            {
                number("melee_seconds", 0.0f, 0.0f, 10.0f, "seconds from the start of a melee attack to its hit (0: as is)"),
                number("ranged_seconds", 0.0f, 0.0f, 10.0f, "seconds from the start of a ranged attack to its release"),
            }},
        {"sounds",
            "Its own sounds: a loop at it while it moves (or always: a hover, a servo) and a one-shot when it first "
            "notices the party, each by name.",
            {
                text("loop", "", "looping sound while it moves (empty: none)"),
                boolean("loop_always", false, "the loop plays while it stands too"),
                number("loop_volume", 0.7f, 0.0f, 1.0f, "the loop's volume"),
                text("aware", "", "one-shot when it first notices the party (empty: none)"),
            }},
        {"kites_party",
            "Keeps its ranged band: the tactics ranged_band [min_distance, max_distance] (backs off inside, closes in "
            "beyond, circles between shots). A monster whose behaviors.yml tactics set ranged_band may not have it.",
            {
                number("min_distance", 768.0f, 0.0f, 20000.0f, "edge distance it backs off inside"),
                number("max_distance", 2304.0f, 1.0f, 20000.0f, "edge distance it closes in beyond"),
            }},
        {"blink",
            "A short teleport to a free spot it can see (floor, walls, actors and the party checked indoors and "
            "outdoors), with an effect and a sound at both ends. Needs at least one trigger.",
            {
                number("on_hit_chance", 0.0f, 0.0f, 1.0f, "chance per damaging hit"),
                boolean("on_shield_break", false, "when its energy shield breaks"),
                number("every_seconds", 0.0f, 0.0f, 600.0f, "periodically while it fights (0: never)"),
                number("cooldown_seconds", 6.0f, 0.0f, 600.0f, "at most one blink per this long"),
                number("min_distance", 384.0f, 32.0f, 8192.0f, "shortest jump"),
                number("max_distance", 1024.0f, 32.0f, 8192.0f, "longest jump"),
                number("max_height_change", 256.0f, 0.0f, 4096.0f, "how far the floor may rise or drop"),
                text("effect", "openyamm:fx/arcane_pulse", "effect id played where it leaves and arrives"),
                text("sound", "monster_blink", "placeholder sound name"),
                text("fallback_sound", "30teleport03", "sound played while the placeholder has no file"),
            }},
        {"charge",
            "A readable dash onto the party: with the party in sight within the trigger band it winds up (holds, "
            "flashes, a sound), then dashes straight at it, following the floor and stopping at walls, ledges and "
            "other bodies. Contact hits once and knocks the party back; a miss ends in a stumble.",
            {
                number("trigger_min_distance", 384.0f, 0.0f, 8192.0f, "closest party distance it charges from"),
                number("trigger_max_distance", 1280.0f, 32.0f, 8192.0f, "farthest party distance it charges from"),
                number("windup_seconds", 0.6f, 0.0f, 5.0f, "how long it holds and telegraphs before the dash"),
                number("speed", 1400.0f, 100.0f, 8000.0f, "dash speed in units a second"),
                number("max_distance", 1536.0f, 64.0f, 8192.0f, "longest dash"),
                number("damage", 0.0f, 0.0f, 10000.0f, "fixed damage of the hit instead of the melee attack"),
                boolean("use_melee", true, "the hit rolls the monster's melee attack (Attack1)"),
                number("knockback", 256.0f, 0.0f, 2048.0f, "how far the hit throws the party back"),
                number("cooldown_seconds", 8.0f, 0.0f, 600.0f, "time from the end of one charge to the next"),
                number("stumble_seconds", 1.2f, 0.0f, 10.0f, "how long it stumbles after a miss"),
                number("strike_seconds", 0.0f, 0.0f, 5.0f,
                    "after a hit, how long its model's charge_strike script clip plays (0: none)"),
                number("strike_impact_seconds", 0.0f, 0.0f, 5.0f,
                    "where the charge_strike clip's blow lands; the clip starts there at the contact"),
                text("effect", "openyamm:fx/ember_impact", "effect id of the wind-up flash"),
                text("windup_sound", "monster_charge_windup", "placeholder sound of the wind-up"),
                text("windup_fallback_sound", "roar 1", "sound played while the wind-up placeholder has no file"),
                text("hit_sound", "monster_charge_hit", "placeholder sound of the hit"),
                text("hit_fallback_sound", "swing with blunt weapon01",
                    "sound played while the hit placeholder has no file"),
            }},
        {"frenzy",
            "A haste power-up: below a share of health (once), periodically while it fights or when its shield "
            "breaks, it roars (holds, a flash and a sound), then moves and attacks faster with its glow flared, "
            "then holds spent.",
            {
                number("health_below", 0.0f, 0.0f, 0.95f,
                    "starts once when its health falls below this share (0: off)"),
                number("every_seconds", 0.0f, 0.0f, 600.0f,
                    "periodically while it fights (0: never); with health_below only below it"),
                boolean("on_shield_break", false, "when its energy shield breaks"),
                number("windup_seconds", 0.8f, 0.0f, 5.0f, "the roar; a stun, paralysis or death in it cancels it"),
                number("seconds", 6.0f, 0.5f, 60.0f, "how long it lasts"),
                number("speed_multiplier", 1.4f, 1.0f, 3.0f, "its walking and running speed"),
                number("attack_rate_multiplier", 1.5f, 1.0f, 3.0f, "its attack recovery is divided by this"),
                number("spent_seconds", 0.0f, 0.0f, 10.0f, "afterwards it holds this long (the punish window)"),
                number("cooldown_seconds", 20.0f, 0.0f, 600.0f, "time from the end of one frenzy to the next"),
                number("glow_multiplier", 2.0f, 1.0f, 5.0f, "its model's emission while it lasts"),
                text("effect", "openyamm:fx/ember_impact", "effect id of the roar's flash"),
                text("sound", "monster_frenzy", "placeholder sound of the roar"),
                text("fallback_sound", "roar 1", "sound played while the placeholder has no file"),
            }},
        {"skirmisher",
            "MM9's melee footwork: it keeps chasing a target that steps away while it attacks (its model swings over "
            "its gait), may run a strafe attack past the target, and after a melee attack evades (backpedals, then "
            "circles the target) or backs off. While evading it may shoot or cast but not strike. Real-time only.",
            {
                number("strafe_attack_chance", 0.8f, 0.0f, 1.0f,
                    "chance of a strafe attack (45 degrees past the target) when it was moving as the attack began"),
                number("evade_chance", 0.4f, 0.0f, 1.0f, "chance it evades after a melee attack"),
                number("evade_seconds", 2.0f, 0.2f, 10.0f, "how long an evade lasts; it backpedals the first half"),
                number("back_off_seconds", 0.3f, 0.0f, 3.0f, "how long it backpedals after a strafe attack it does "
                    "not evade from"),
                number("taunt_chance", 0.4f, 0.0f, 1.0f,
                    "chance it taunts when it first notices the party and after a back-off"),
                number("taunt_seconds", 0.0f, 0.0f, 10.0f,
                    "length of its model's taunt script clip, which it holds still for (0: it never taunts)"),
            }},
        {"spell_conditions",
            "A hit on a party member by its first or second spell (monster_data Spell1/Spell2) leaves a condition, by "
            "chance and then the member's save as against a special attack. It also lets it cast Paralyze and Fear "
            "(no damage), which a monster without a condition for them never casts.",
            {
                choice("spell1", "none", SpellConditionChoices, "the condition its first spell leaves"),
                choice("spell2", "none", SpellConditionChoices, "the condition its second spell leaves"),
                number("chance", 1.0f, 0.0f, 1.0f, "chance per struck member before the save"),
            }},
        {"reposition",
            "An OpenYAMM addition for a monster that holds its place to shoot or cast (an MM9 ranged holder): with its "
            "target unseen it walks to a nearby spot within its leash from which it sees the target (else back to "
            "its post), and a target rushing it makes it backpedal a few steps before it shoots or casts.",
            {
                number("lost_sight_seconds", 2.0f, 0.1f, 7.0f,
                    "its target unseen this long, it looks for a spot (MM9 loses a target after 8 s)"),
                number("leash_radius", 1024.0f, 64.0f, 8192.0f, "its spots and back-offs stay this close to its post"),
                number("search_distance", 640.0f, 64.0f, 4096.0f,
                    "candidate spots lie on rings at half and all of this distance around it"),
                number("candidates", 8.0f, 1.0f, 16.0f, "candidate spots per search"),
                number("max_sight_checks", 12.0f, 1.0f, 32.0f, "sight lines one search may test"),
                number("retry_seconds", 2.0f, 0.2f, 30.0f, "after a search, the wait before the next one"),
                number("back_off_trigger_distance", 640.0f, 0.0f, 4096.0f,
                    "a target closing inside this edge distance (outside its reach) rushes it"),
                number("back_off_closing_speed", 200.0f, 0.0f, 4000.0f,
                    "the speed toward it at which a target rushes it"),
                number("back_off_distance", 384.0f, 32.0f, 2048.0f, "how far it backpedals from a rush"),
                number("back_off_cooldown_seconds", 5.0f, 0.0f, 60.0f, "time from one back-off to the next"),
            }},
        {"mm9_ai",
            "MM9's AI profile of the monster row, generated from MONSTERS.txt and its script "
            "(devdocs/mm9_rework/monster_ai/PROFILE.md). Distances and speeds in our units (MM9's x 2.56).",
            {
                choice("archetype", "skirmisher",
                    "crawler|skirmisher|ranged_holder|flier|swimmer|turret|civilian|guard",
                    "its behaviour loop (MM9's base script family)"),
                choice("movement", "walk", "walk|fly|swim", "how it moves (its MM9 native class)"),
                choice("ranged", "none", "none|walker|flier", "the ranged add-on of its script"),
                number("attack_reach", 0.0f, 0.0f, 4096.0f, "the distance at which it decides to attack"),
                number("melee_sweep", 0.0f, 0.0f, 4096.0f, "how far its melee hit sweeps beyond its radius"),
                number("alert_radius", 3072.0f, 0.0f, 16384.0f, "the radius of its alerts to friends"),
                number("walk_speed", 0.0f, 0.0f, 4096.0f, "MM9 walk speed"),
                number("run_speed", 0.0f, 0.0f, 4096.0f, "MM9 run speed"),
                number("fly_speed", 0.0f, 0.0f, 4096.0f, "MM9 fly (or swim) speed"),
                number("lunge_velocity", 0.0f, 0.0f, 4096.0f, "the impulse of its attack's lunge key"),
                number("eye_below_top", 5.12f, 0.0f, 256.0f,
                    "its eye below the top of its body, where its sight lines start (GetEyePos: 2 LT)"),
                choice("wince", "low_health", "low_health|never",
                    "MM9's wince roll: 20-50 % once at most 20 % health, or never (Always Wince? = 1)"),
                boolean("resurrecter", false, "it raises dead friends"),
                boolean("head_turn", true, "its head turns toward its target or the party talking to it (HeadTurn)"),
                boolean("cower", false, "its MM9 model has a Cower clip (it may cower instead of fleeing)"),
                number("raise_seconds", 0.0f, 0.0f, 60.0f,
                    "its MM9 model's Resurrect clip (0: none, it cannot be raised)"),
                number("resurrect_spell_seconds", 0.0f, 0.0f, 60.0f,
                    "its MM9 model's ResurrectSpell clip (0: none, it raises no one else)"),
                number("resurrect_key_seconds", 0.0f, 0.0f, 60.0f,
                    "the ResurrectSpell clip's DoResurrection key: the corpse rises"),
                boolean("boss", false, "a boss row: its fight is a Lua behaviour"),
                number("spell1_recovery", 0.0f, 0.0f, 60.0f,
                    "its first spell's own recovery from the cast (SPELL.txt at its mastery; 0: its Recovery)"),
                number("spell2_recovery", 0.0f, 0.0f, 60.0f,
                    "its second spell's own recovery from the cast (SPELL.txt at its mastery; 0: its Recovery)"),
                boolean("throttle", true, "it keeps pace with a moving target while it strikes (SpeedThrottle)"),
                boolean("always_evade", false, "it evades after every attack"),
                number("evade_min_seconds", 0.0f, 0.0f, 10.0f,
                    "shortest evade after an attack with always_evade (0: the skirmisher's evade_seconds)"),
                number("evade_max_seconds", 0.0f, 0.0f, 10.0f, "longest evade after an attack with always_evade"),
                boolean("ranged_weapon", false,
                    "it holds a ranged weapon prop: in reach it shoots or casts by Att% instead of striking"),
                number("pod_launch", 0.0f, 0.0f, 32767.0f, "the monster id a turret launches (0: none)"),
                number("pod_cooldown_min", 5.0f, 0.0f, 600.0f, "shortest time between launches"),
                number("pod_cooldown_max", 10.0f, 0.0f, 600.0f, "longest time between launches"),
                number("melee_window_seconds", 0.0f, 0.0f, 60.0f,
                    "how long it is undead (immune) during each melee pass (0: never)"),
                boolean("spawn_in", false, "a spawned one (p0 = 1) appears with its spawn clip"),
                number("death_spawn", 0.0f, 0.0f, 32767.0f,
                    "the monster id a spawned one's (p0 = 1) corpse spawns (0: none)"),
                choice("dormant_until", "none", "none|trigger|disturbed|sighted", "a dormant start: what wakes it"),
                choice("dormant_pose", "stand", "stand|lie|sleep|hang|underground|hidden|caged|coffin",
                    "a dormant start: how it waits"),
                boolean("guard_refuge", false, "a townsperson that flees runs to a town guard (NPCBase.inc)"),
                number("wake_seconds", 0.0f, 0.0f, 60.0f, "the clip a hanging start plays as it wakes (Launch)"),
                number("wakeup_seconds", 0.0f, 0.0f, 60.0f,
                    "the clip a lying start (coffin, sleep, lie) plays as it gets up (Wakeup)"),
                number("dormant_fidget_seconds", 0.0f, 0.0f, 60.0f, "its hanging fidget clip (HangFidget)"),
                number("spawn_seconds", 0.0f, 0.0f, 60.0f, "its spawn clip (Spawn), played as it spawns in"),
                number("aware_seconds", 0.0f, 0.0f, 60.0f, "its Aware clip (its Taunt without one) after a spawn-in"),
            }},
    };
}

struct ParsedModifier
{
    const MonsterModifierInfo *pInfo = nullptr;
    std::vector<float> numbers;
    std::vector<std::string> texts;
    // The parameters the file gives (not defaults).
    std::vector<bool> given;

    size_t index(const char *pName) const
    {
        for (size_t parameter = 0; parameter < pInfo->parameters.size(); ++parameter)
        {
            if (std::string(pInfo->parameters[parameter].pName) == pName)
            {
                return parameter;
            }
        }
        return 0;
    }
    float numberOf(const char *pName) const
    {
        return numbers[index(pName)];
    }
    bool flagOf(const char *pName) const
    {
        return numbers[index(pName)] != 0.0f;
    }
    const std::string &textOf(const char *pName) const
    {
        return texts[index(pName)];
    }
    bool givenOf(const char *pName) const
    {
        return given[index(pName)];
    }
};

std::string lineOf(const YAML::Node &node)
{
    const YAML::Mark mark = node.Mark();
    return mark.line >= 0 ? std::to_string(mark.line + 1) : "?";
}

std::string knownNames()
{
    std::string names;
    for (const MonsterModifierInfo &info : monsterModifierCatalogue())
    {
        names += names.empty() ? "" : ", ";
        names += info.pName;
    }
    return names;
}

// Names that are not modifiers because the data lives elsewhere: the error says where.
const char *redirectFor(const std::string &name)
{
    if (name == "energy_immune")
    {
        return "energy_immune belongs to shields.yml (monsters: {<id>: {energy_immune: true}})";
    }
    if (name == "stationary")
    {
        return "stationary is the monster row's Movement column (Stationary) in monster_data";
    }
    return nullptr;
}

bool parseParameters(const MonsterModifierInfo &info, const YAML::Node &params, ParsedModifier &parsed,
    std::string &error)
{
    parsed.pInfo = &info;
    parsed.numbers.resize(info.parameters.size());
    parsed.texts.resize(info.parameters.size());
    parsed.given.assign(info.parameters.size(), false);
    for (size_t parameter = 0; parameter < info.parameters.size(); ++parameter)
    {
        parsed.numbers[parameter] = info.parameters[parameter].defaultNumber;
        parsed.texts[parameter] = info.parameters[parameter].pDefaultText;
    }

    if (!params || params.IsNull())
    {
        return true;
    }
    if (!params.IsMap())
    {
        error = lineOf(params) + ": " + info.pName + " takes a map of parameters";
        return false;
    }

    for (const auto &entry : params)
    {
        const std::string key = entry.first.as<std::string>();
        const auto found = std::find_if(info.parameters.begin(), info.parameters.end(),
            [&](const MonsterModifierParameterInfo &parameter) { return key == parameter.pName; });
        if (found == info.parameters.end())
        {
            std::string known;
            for (const MonsterModifierParameterInfo &parameter : info.parameters)
            {
                known += known.empty() ? "" : ", ";
                known += parameter.pName;
            }
            error = lineOf(entry.first) + ": " + info.pName + " has no parameter '" + key + "'"
                + (known.empty() ? std::string(" (it takes none)") : " (known: " + known + ")");
            return false;
        }

        const size_t parameter = size_t(found - info.parameters.begin());
        parsed.given[parameter] = true;
        const std::string where = lineOf(entry.second) + ": " + info.pName + "." + key;
        if (!entry.second.IsScalar())
        {
            error = where + " must be a single value";
            return false;
        }

        switch (found->kind)
        {
            case Kind::Number:
            {
                float value = 0.0f;
                if (!YAML::convert<float>::decode(entry.second, value) || !std::isfinite(value)
                    || value < found->minimum || value > found->maximum)
                {
                    std::ostringstream range;
                    range << found->minimum << "-" << found->maximum;
                    error = where + " must be a number in " + range.str();
                    return false;
                }
                parsed.numbers[parameter] = value;
                break;
            }
            case Kind::Boolean:
            {
                bool value = false;
                if (!YAML::convert<bool>::decode(entry.second, value))
                {
                    error = where + " must be true or false";
                    return false;
                }
                parsed.numbers[parameter] = value ? 1.0f : 0.0f;
                break;
            }
            case Kind::Text:
            {
                const std::string value = entry.second.as<std::string>();
                if (value.empty())
                {
                    error = where + " must not be empty";
                    return false;
                }
                parsed.texts[parameter] = value;
                break;
            }
            case Kind::Choice:
            {
                const std::string value = entry.second.as<std::string>();
                std::istringstream choices(found->pChoices);
                std::string option;
                bool known = false;
                while (std::getline(choices, option, '|'))
                {
                    known = known || option == value;
                }
                if (!known)
                {
                    error = where + " must be one of " + found->pChoices;
                    return false;
                }
                parsed.texts[parameter] = value;
                break;
            }
        }
    }
    return true;
}

bool applyModifier(const ParsedModifier &parsed, const std::string &line, MonsterModifierSet &set,
    std::string &error)
{
    const std::string name = parsed.pInfo->pName;
    if (std::find(set.names.begin(), set.names.end(), name) != set.names.end())
    {
        error = line + ": " + name + " is listed twice";
        return false;
    }

    if (name == "true_aim")
    {
        TrueAimModifier trueAim;
        trueAim.turnRadiansPerSecond = parsed.numberOf("turn_degrees_per_second") * DegreesToRadians;
        trueAim.maxSeconds = parsed.numberOf("max_seconds");
        trueAim.expireAfter = parsed.textOf("then") == "expire";
        set.trueAim = trueAim;
    }
    else if (name == "never_staggers")
    {
        set.neverStaggers = true;
    }
    else if (name == "indoor_meteor_shower")
    {
        set.indoorMeteorShower = true;
    }
    else if (name == "kites_party")
    {
        KitesPartyModifier kites;
        kites.minDistance = parsed.numberOf("min_distance");
        kites.maxDistance = parsed.numberOf("max_distance");
        if (kites.minDistance >= kites.maxDistance)
        {
            error = line + ": kites_party.min_distance must be below max_distance";
            return false;
        }
        set.kitesParty = kites;
    }
    else if (name == "blink")
    {
        BlinkModifier blink;
        blink.onHitChance = parsed.numberOf("on_hit_chance");
        blink.onShieldBreak = parsed.flagOf("on_shield_break");
        blink.everySeconds = parsed.numberOf("every_seconds");
        blink.cooldownSeconds = parsed.numberOf("cooldown_seconds");
        blink.minDistance = parsed.numberOf("min_distance");
        blink.maxDistance = parsed.numberOf("max_distance");
        blink.maxHeightChange = parsed.numberOf("max_height_change");
        blink.effect = parsed.textOf("effect");
        blink.sound = parsed.textOf("sound");
        blink.fallbackSound = parsed.textOf("fallback_sound");
        if (blink.minDistance > blink.maxDistance)
        {
            error = line + ": blink.min_distance must not exceed max_distance";
            return false;
        }
        if (blink.onHitChance <= 0.0f && !blink.onShieldBreak && blink.everySeconds <= 0.0f)
        {
            error = line + ": blink needs a trigger (on_hit_chance, on_shield_break or every_seconds)";
            return false;
        }
        set.blink = blink;
    }
    else if (name == "charge")
    {
        ChargeModifier charge;
        charge.triggerMinDistance = parsed.numberOf("trigger_min_distance");
        charge.triggerMaxDistance = parsed.numberOf("trigger_max_distance");
        charge.windupSeconds = parsed.numberOf("windup_seconds");
        charge.speed = parsed.numberOf("speed");
        charge.maxDistance = parsed.numberOf("max_distance");
        charge.damage = parsed.numberOf("damage");
        // A damage given without use_melee replaces the melee attack.
        charge.useMelee = parsed.givenOf("use_melee") ? parsed.flagOf("use_melee") : charge.damage <= 0.0f;
        charge.knockback = parsed.numberOf("knockback");
        charge.cooldownSeconds = parsed.numberOf("cooldown_seconds");
        charge.stumbleSeconds = parsed.numberOf("stumble_seconds");
        charge.strikeSeconds = parsed.numberOf("strike_seconds");
        charge.strikeImpactSeconds = parsed.numberOf("strike_impact_seconds");
        charge.effect = parsed.textOf("effect");
        charge.windupSound = parsed.textOf("windup_sound");
        charge.windupFallbackSound = parsed.textOf("windup_fallback_sound");
        charge.hitSound = parsed.textOf("hit_sound");
        charge.hitFallbackSound = parsed.textOf("hit_fallback_sound");
        if (charge.triggerMinDistance >= charge.triggerMaxDistance)
        {
            error = line + ": charge.trigger_min_distance must be below trigger_max_distance";
            return false;
        }
        if (charge.useMelee == (charge.damage > 0.0f))
        {
            error = line + ": charge hits with its melee attack (use_melee: true, no damage) or with a fixed damage "
                "above 0 (use_melee: false)";
            return false;
        }
        set.charge = charge;
    }
    else if (name == "frenzy")
    {
        FrenzyModifier frenzy;
        frenzy.healthBelow = parsed.numberOf("health_below");
        frenzy.everySeconds = parsed.numberOf("every_seconds");
        frenzy.onShieldBreak = parsed.flagOf("on_shield_break");
        frenzy.windupSeconds = parsed.numberOf("windup_seconds");
        frenzy.seconds = parsed.numberOf("seconds");
        frenzy.speedMultiplier = parsed.numberOf("speed_multiplier");
        frenzy.attackRateMultiplier = parsed.numberOf("attack_rate_multiplier");
        frenzy.spentSeconds = parsed.numberOf("spent_seconds");
        frenzy.cooldownSeconds = parsed.numberOf("cooldown_seconds");
        frenzy.glowMultiplier = parsed.numberOf("glow_multiplier");
        frenzy.effect = parsed.textOf("effect");
        frenzy.sound = parsed.textOf("sound");
        frenzy.fallbackSound = parsed.textOf("fallback_sound");
        if (frenzy.healthBelow <= 0.0f && frenzy.everySeconds <= 0.0f && !frenzy.onShieldBreak)
        {
            error = line + ": frenzy needs a trigger (health_below, every_seconds or on_shield_break)";
            return false;
        }
        set.frenzy = frenzy;
    }
    else if (name == "telegraphed_attack")
    {
        TelegraphedAttackModifier telegraph;
        telegraph.meleeSeconds = parsed.numberOf("melee_seconds");
        telegraph.rangedSeconds = parsed.numberOf("ranged_seconds");
        if (telegraph.meleeSeconds <= 0.0f && telegraph.rangedSeconds <= 0.0f)
        {
            error = line + ": telegraphed_attack needs melee_seconds or ranged_seconds above 0";
            return false;
        }
        set.telegraphedAttack = telegraph;
    }
    else if (name == "skirmisher")
    {
        SkirmisherModifier skirmisher;
        skirmisher.strafeAttackChance = parsed.numberOf("strafe_attack_chance");
        skirmisher.evadeChance = parsed.numberOf("evade_chance");
        skirmisher.evadeSeconds = parsed.numberOf("evade_seconds");
        skirmisher.backOffSeconds = parsed.numberOf("back_off_seconds");
        skirmisher.tauntChance = parsed.numberOf("taunt_chance");
        skirmisher.tauntSeconds = parsed.numberOf("taunt_seconds");
        set.skirmisher = skirmisher;
    }
    else if (name == "mm9_ai")
    {
        Mm9AiProfile profile;
        parseMm9AiArchetype(parsed.textOf("archetype"), profile.archetype);
        parseMm9AiMovement(parsed.textOf("movement"), profile.movement);
        parseMm9AiRanged(parsed.textOf("ranged"), profile.ranged);
        parseMm9AiWince(parsed.textOf("wince"), profile.wince);
        parseMm9AiDormantUntil(parsed.textOf("dormant_until"), profile.dormantUntil);
        parseMm9AiDormantPose(parsed.textOf("dormant_pose"), profile.dormantPose);
        profile.attackReach = parsed.numberOf("attack_reach");
        profile.meleeSweep = parsed.numberOf("melee_sweep");
        profile.alertRadius = parsed.numberOf("alert_radius");
        profile.walkSpeed = parsed.numberOf("walk_speed");
        profile.runSpeed = parsed.numberOf("run_speed");
        profile.flySpeed = parsed.numberOf("fly_speed");
        profile.lungeVelocity = parsed.numberOf("lunge_velocity");
        profile.eyeBelowTop = parsed.numberOf("eye_below_top");
        profile.resurrecter = parsed.flagOf("resurrecter");
        profile.headTurn = parsed.flagOf("head_turn");
        profile.cower = parsed.flagOf("cower");
        profile.raiseSeconds = parsed.numberOf("raise_seconds");
        profile.resurrectSpellSeconds = parsed.numberOf("resurrect_spell_seconds");
        profile.resurrectKeySeconds = parsed.numberOf("resurrect_key_seconds");
        profile.boss = parsed.flagOf("boss");
        profile.spell1RecoverySeconds = parsed.numberOf("spell1_recovery");
        profile.spell2RecoverySeconds = parsed.numberOf("spell2_recovery");
        profile.throttle = parsed.flagOf("throttle");
        profile.alwaysEvade = parsed.flagOf("always_evade");
        profile.evadeMinSeconds = parsed.numberOf("evade_min_seconds");
        profile.evadeMaxSeconds = parsed.numberOf("evade_max_seconds");
        profile.rangedWeapon = parsed.flagOf("ranged_weapon");
        profile.podLaunchMonsterId = int16_t(parsed.numberOf("pod_launch"));
        profile.podCooldownMinSeconds = parsed.numberOf("pod_cooldown_min");
        profile.podCooldownMaxSeconds = parsed.numberOf("pod_cooldown_max");
        profile.meleeWindowSeconds = parsed.numberOf("melee_window_seconds");
        profile.spawnIn = parsed.flagOf("spawn_in");
        profile.deathSpawnMonsterId = int16_t(parsed.numberOf("death_spawn"));
        profile.guardRefuge = parsed.flagOf("guard_refuge");
        profile.wakeSeconds = parsed.numberOf("wake_seconds");
        profile.wakeupSeconds = parsed.numberOf("wakeup_seconds");
        profile.dormantFidgetSeconds = parsed.numberOf("dormant_fidget_seconds");
        profile.spawnSeconds = parsed.numberOf("spawn_seconds");
        profile.awareSeconds = parsed.numberOf("aware_seconds");

        if (!parsed.givenOf("archetype"))
        {
            error = line + ": mm9_ai needs its archetype";
            return false;
        }
        if (profile.archetype == Mm9AiArchetype::Flier && profile.movement != Mm9AiMovement::Fly)
        {
            error = line + ": mm9_ai archetype flier needs movement fly";
            return false;
        }
        if (profile.archetype == Mm9AiArchetype::Swimmer && profile.movement != Mm9AiMovement::Swim)
        {
            error = line + ": mm9_ai archetype swimmer needs movement swim";
            return false;
        }
        if (profile.ranged == Mm9AiRanged::Flier && profile.movement != Mm9AiMovement::Fly)
        {
            error = line + ": mm9_ai ranged flier needs movement fly";
            return false;
        }
        if (profile.podLaunchMonsterId != 0 && profile.archetype != Mm9AiArchetype::Turret)
        {
            error = line + ": mm9_ai pod_launch belongs to a turret";
            return false;
        }
        if (profile.evadeMinSeconds > profile.evadeMaxSeconds)
        {
            error = line + ": mm9_ai evade_min_seconds must not exceed evade_max_seconds";
            return false;
        }
        if (profile.podCooldownMinSeconds > profile.podCooldownMaxSeconds)
        {
            error = line + ": mm9_ai pod_cooldown_min must not exceed pod_cooldown_max";
            return false;
        }
        if ((profile.dormantUntil == Mm9AiDormantUntil::None) != !parsed.givenOf("dormant_until")
            || (parsed.givenOf("dormant_pose") && profile.dormantUntil == Mm9AiDormantUntil::None))
        {
            error = line + ": mm9_ai dormant_until must be trigger, disturbed or sighted, and dormant_pose needs it";
            return false;
        }
        set.mm9Ai = profile;
    }
    else if (name == "spell_conditions")
    {
        SpellConditionsModifier conditions;
        conditions.spell1 = spellConditionKind(parsed.textOf("spell1"));
        conditions.spell2 = spellConditionKind(parsed.textOf("spell2"));
        conditions.chance = parsed.numberOf("chance");
        if (conditions.spell1 == MonsterSpecialAttackKind::None && conditions.spell2 == MonsterSpecialAttackKind::None)
        {
            error = line + ": spell_conditions needs a condition for spell1 or spell2";
            return false;
        }
        set.spellConditions = conditions;
    }
    else if (name == "reposition")
    {
        RepositionModifier reposition;
        reposition.lostSightSeconds = parsed.numberOf("lost_sight_seconds");
        reposition.leashRadius = parsed.numberOf("leash_radius");
        reposition.searchDistance = parsed.numberOf("search_distance");
        reposition.candidates = int(parsed.numberOf("candidates"));
        reposition.maxSightChecks = int(parsed.numberOf("max_sight_checks"));
        reposition.retrySeconds = parsed.numberOf("retry_seconds");
        reposition.backOffTriggerDistance = parsed.numberOf("back_off_trigger_distance");
        reposition.backOffClosingSpeed = parsed.numberOf("back_off_closing_speed");
        reposition.backOffDistance = parsed.numberOf("back_off_distance");
        reposition.backOffCooldownSeconds = parsed.numberOf("back_off_cooldown_seconds");
        if (std::floor(parsed.numberOf("candidates")) != parsed.numberOf("candidates")
            || std::floor(parsed.numberOf("max_sight_checks")) != parsed.numberOf("max_sight_checks"))
        {
            error = line + ": reposition.candidates and max_sight_checks must be whole numbers";
            return false;
        }
        set.reposition = reposition;
    }
    else if (name == "sounds")
    {
        ActorSoundsModifier sounds;
        sounds.loop = parsed.textOf("loop");
        sounds.loopAlways = parsed.flagOf("loop_always");
        sounds.loopVolume = parsed.numberOf("loop_volume");
        sounds.aware = parsed.textOf("aware");
        if (sounds.loop.empty() && sounds.aware.empty())
        {
            error = line + ": sounds needs a loop or an aware sound";
            return false;
        }
        set.sounds = sounds;
    }
    else if (name == "stagger")
    {
        StaggerModifier stagger;
        stagger.thresholdPercent = parsed.numberOf("threshold_percent");
        stagger.cooldownSeconds = parsed.numberOf("cooldown_seconds");
        stagger.windowSeconds = parsed.numberOf("window_seconds");
        if (set.neverStaggers)
        {
            error = line + ": stagger and never_staggers contradict each other";
            return false;
        }
        set.stagger = stagger;
    }
    set.names.push_back(name);
    return true;
}

// "10065" or "10050-10052".
bool parseIdKey(const std::string &key, int &first, int &last)
{
    const size_t dash = key.find('-', 1);
    try
    {
        size_t used = 0;
        first = std::stoi(key.substr(0, dash), &used);
        if (used != (dash == std::string::npos ? key.size() : dash))
        {
            return false;
        }
        last = first;
        if (dash != std::string::npos)
        {
            const std::string tail = key.substr(dash + 1);
            last = std::stoi(tail, &used);
            if (used != tail.size())
            {
                return false;
            }
        }
    }
    catch (const std::exception &)
    {
        return false;
    }
    return first <= last;
}
}

const std::vector<MonsterModifierInfo> &monsterModifierCatalogue()
{
    static const std::vector<MonsterModifierInfo> catalogue = buildCatalogue();
    return catalogue;
}

const MonsterModifierInfo *findMonsterModifierInfo(const std::string &name)
{
    for (const MonsterModifierInfo &info : monsterModifierCatalogue())
    {
        if (name == info.pName)
        {
            return &info;
        }
    }
    return nullptr;
}

bool MonsterModifierTable::loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t idBegin,
    uint32_t idEnd, std::string &error)
{
    const std::string file = "worlds/" + packageId + "/modifiers.yml";
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root.IsMap() || root["schema"].as<std::string>("") != ModifiersSchema)
        {
            error = file + ": expected schema " + ModifiersSchema;
            return false;
        }

        const YAML::Node monsters = root["monsters"];
        if (monsters && !monsters.IsMap())
        {
            error = file + ":" + lineOf(monsters) + ": monsters must map ids to lists of modifiers";
            return false;
        }

        std::unordered_map<int16_t, MonsterModifierSet> loaded;
        for (const auto &entry : monsters)
        {
            const std::string key = entry.first.as<std::string>();
            const std::string keyLine = file + ":" + lineOf(entry.first);
            int first = 0;
            int last = 0;
            if (!parseIdKey(key, first, last))
            {
                error = keyLine + ": '" + key + "' is not a monster id or an id range (first-last)";
                return false;
            }
            if (first <= 0 || uint32_t(first) < idBegin || uint32_t(last) > idEnd || last > INT16_MAX)
            {
                error = keyLine + ": " + key + " lies outside the world's monster id range";
                return false;
            }
            if (!entry.second.IsSequence())
            {
                error = keyLine + ": " + key + " must list its modifiers ([name, {name: {parameters}}])";
                return false;
            }

            MonsterModifierSet set;
            for (const YAML::Node &item : entry.second)
            {
                std::string name;
                YAML::Node params;
                if (item.IsScalar())
                {
                    name = item.as<std::string>();
                }
                else if (item.IsMap() && item.size() == 1)
                {
                    name = item.begin()->first.as<std::string>();
                    params = item.begin()->second;
                }
                else
                {
                    error = file + ":" + lineOf(item) + ": a modifier is a name or {name: {parameters}}";
                    return false;
                }

                const MonsterModifierInfo *pInfo = findMonsterModifierInfo(name);
                if (pInfo == nullptr)
                {
                    const char *pRedirect = redirectFor(name);
                    error = file + ":" + lineOf(item) + ": "
                        + (pRedirect != nullptr ? std::string(pRedirect)
                                                : "unknown modifier '" + name + "' (known: " + knownNames() + ")");
                    return false;
                }

                ParsedModifier parsed;
                std::string parameterError;
                if (!parseParameters(*pInfo, params, parsed, parameterError)
                    || !applyModifier(parsed, lineOf(item), set, parameterError))
                {
                    error = file + ":" + parameterError;
                    return false;
                }
            }

            for (int id = first; id <= last; ++id)
            {
                if (loaded.contains(int16_t(id)) || m_sets.contains(int16_t(id)))
                {
                    error = keyLine + ": monster " + std::to_string(id) + " is listed twice";
                    return false;
                }
                MonsterModifierSet copy = set;
                copy.monsterId = int16_t(id);
                loaded.emplace(int16_t(id), std::move(copy));
            }
        }

        for (auto &entry : loaded)
        {
            set(entry.second);
        }
    }
    catch (const std::exception &exception)
    {
        error = file + ": " + exception.what();
        return false;
    }
    return true;
}

void MonsterModifierTable::clear()
{
    *this = {};
}

const MonsterModifierSet *MonsterModifierTable::find(int16_t monsterId) const
{
    if (monsterId < m_minimumMonsterId || monsterId > m_maximumMonsterId)
    {
        return nullptr;
    }
    const auto found = m_sets.find(monsterId);
    return found != m_sets.end() ? &found->second : nullptr;
}

void MonsterModifierTable::set(const MonsterModifierSet &modifiers)
{
    m_sets[modifiers.monsterId] = modifiers;
    m_hasBlink = m_hasBlink || modifiers.blink.has_value();
    m_hasCharge = m_hasCharge || modifiers.charge.has_value();
    m_hasFrenzy = m_hasFrenzy || modifiers.frenzy.has_value();
    m_hasStagger = m_hasStagger || modifiers.stagger.has_value();
    m_hasSounds = m_hasSounds || modifiers.sounds.has_value();
    m_hasMm9Ai = m_hasMm9Ai || modifiers.mm9Ai.has_value();
    m_minimumMonsterId = std::min(m_minimumMonsterId, modifiers.monsterId);
    m_maximumMonsterId = std::max(m_maximumMonsterId, modifiers.monsterId);
}
}
