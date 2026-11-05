#include "game/tables/PotionEffectTable.h"

#include "game/items/ItemEnchantTables.h"
#include "game/party/CharacterState.h"
#include "game/party/Party.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <exception>
#include <optional>
#include <string_view>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
template <typename Enum, size_t Count>
std::optional<Enum> findNamed(const std::array<std::pair<std::string_view, Enum>, Count> &names, const std::string &name)
{
    for (const auto &[candidate, value] : names)
    {
        if (candidate == name)
        {
            return value;
        }
    }

    return std::nullopt;
}

constexpr std::array<std::pair<std::string_view, CharacterCondition>, 18> ConditionNames = {{
    {"Cursed", CharacterCondition::Cursed},
    {"Weak", CharacterCondition::Weak},
    {"Asleep", CharacterCondition::Asleep},
    {"Fear", CharacterCondition::Fear},
    {"Drunk", CharacterCondition::Drunk},
    {"Insane", CharacterCondition::Insane},
    {"PoisonWeak", CharacterCondition::PoisonWeak},
    {"DiseaseWeak", CharacterCondition::DiseaseWeak},
    {"PoisonMedium", CharacterCondition::PoisonMedium},
    {"DiseaseMedium", CharacterCondition::DiseaseMedium},
    {"PoisonSevere", CharacterCondition::PoisonSevere},
    {"DiseaseSevere", CharacterCondition::DiseaseSevere},
    {"Paralyzed", CharacterCondition::Paralyzed},
    {"Unconscious", CharacterCondition::Unconscious},
    {"Dead", CharacterCondition::Dead},
    {"Petrified", CharacterCondition::Petrified},
    {"Eradicated", CharacterCondition::Eradicated},
    {"Zombie", CharacterCondition::Zombie},
}};

constexpr std::array<std::pair<std::string_view, CharacterBuffId>, 28> CharacterBuffNames = {{
    {"Bless", CharacterBuffId::Bless},
    {"Fate", CharacterBuffId::Fate},
    {"Preservation", CharacterBuffId::Preservation},
    {"Regeneration", CharacterBuffId::Regeneration},
    {"Hammerhands", CharacterBuffId::Hammerhands},
    {"PainReflection", CharacterBuffId::PainReflection},
    {"FireAura", CharacterBuffId::FireAura},
    {"VampiricWeapon", CharacterBuffId::VampiricWeapon},
    {"Mistform", CharacterBuffId::Mistform},
    {"Glamour", CharacterBuffId::Glamour},
    {"Haste", CharacterBuffId::Haste},
    {"Heroism", CharacterBuffId::Heroism},
    {"Shield", CharacterBuffId::Shield},
    {"Stoneskin", CharacterBuffId::Stoneskin},
    {"WaterBreathing", CharacterBuffId::WaterBreathing},
    {"TempMight", CharacterBuffId::TempMight},
    {"TempIntellect", CharacterBuffId::TempIntellect},
    {"TempPersonality", CharacterBuffId::TempPersonality},
    {"TempEndurance", CharacterBuffId::TempEndurance},
    {"TempSpeed", CharacterBuffId::TempSpeed},
    {"TempAccuracy", CharacterBuffId::TempAccuracy},
    {"TempLuck", CharacterBuffId::TempLuck},
    {"FireResistance", CharacterBuffId::FireResistance},
    {"AirResistance", CharacterBuffId::AirResistance},
    {"WaterResistance", CharacterBuffId::WaterResistance},
    {"EarthResistance", CharacterBuffId::EarthResistance},
    {"MindResistance", CharacterBuffId::MindResistance},
    {"BodyResistance", CharacterBuffId::BodyResistance},
}};

constexpr std::array<std::pair<std::string_view, PartyBuffId>, 22> PartyBuffNames = {{
    {"TorchLight", PartyBuffId::TorchLight},
    {"WizardEye", PartyBuffId::WizardEye},
    {"FeatherFall", PartyBuffId::FeatherFall},
    {"DetectLife", PartyBuffId::DetectLife},
    {"WaterWalk", PartyBuffId::WaterWalk},
    {"Fly", PartyBuffId::Fly},
    {"Invisibility", PartyBuffId::Invisibility},
    {"Stoneskin", PartyBuffId::Stoneskin},
    {"DayOfGods", PartyBuffId::DayOfGods},
    {"ProtectionFromMagic", PartyBuffId::ProtectionFromMagic},
    {"FireResistance", PartyBuffId::FireResistance},
    {"WaterResistance", PartyBuffId::WaterResistance},
    {"AirResistance", PartyBuffId::AirResistance},
    {"EarthResistance", PartyBuffId::EarthResistance},
    {"MindResistance", PartyBuffId::MindResistance},
    {"BodyResistance", PartyBuffId::BodyResistance},
    {"Shield", PartyBuffId::Shield},
    {"Heroism", PartyBuffId::Heroism},
    {"Haste", PartyBuffId::Haste},
    {"Immolation", PartyBuffId::Immolation},
    {"Glamour", PartyBuffId::Glamour},
    {"Levitate", PartyBuffId::Levitate},
}};

// The special enchantments a potion can put on a weapon.
constexpr std::array<std::pair<std::string_view, SpecialItemEnchantKind>, 6> PotionEnchantNames = {{
    {"Flame", SpecialItemEnchantKind::Flame},
    {"Frost", SpecialItemEnchantKind::Frost},
    {"Poison", SpecialItemEnchantKind::Poison},
    {"Sparks", SpecialItemEnchantKind::Sparks},
    {"Swift", SpecialItemEnchantKind::Swift},
    {"DragonSlaying", SpecialItemEnchantKind::DragonSlaying},
}};

constexpr std::array<std::pair<std::string_view, PotionStat>, 7> StatNames = {{
    {"might", PotionStat::Might},
    {"intellect", PotionStat::Intellect},
    {"personality", PotionStat::Personality},
    {"endurance", PotionStat::Endurance},
    {"accuracy", PotionStat::Accuracy},
    {"speed", PotionStat::Speed},
    {"luck", PotionStat::Luck},
}};

constexpr std::array<std::pair<std::string_view, PotionResistance>, 6> ResistanceNames = {{
    {"fire", PotionResistance::Fire},
    {"air", PotionResistance::Air},
    {"water", PotionResistance::Water},
    {"earth", PotionResistance::Earth},
    {"mind", PotionResistance::Mind},
    {"body", PotionResistance::Body},
}};

constexpr std::array<std::pair<std::string_view, SkillMastery>, 4> MasteryNames = {{
    {"Normal", SkillMastery::Normal},
    {"Expert", SkillMastery::Expert},
    {"Master", SkillMastery::Master},
    {"Grandmaster", SkillMastery::Grandmaster},
}};

// Parsing throws this with a message naming the bad value; loadFromYaml reports it.
struct PotionParseError
{
    std::string message;
};

template <typename Enum, size_t Count>
Enum requireNamed(
    const std::array<std::pair<std::string_view, Enum>, Count> &names,
    const YAML::Node &node,
    const char *pWhat)
{
    const std::string name = node && node.IsScalar() ? node.as<std::string>() : std::string();
    const std::optional<Enum> value = findNamed(names, name);

    if (!value)
    {
        throw PotionParseError{std::string("unknown ") + pWhat + " '" + name + "'"};
    }

    return *value;
}

template <typename Enum, size_t Count>
std::vector<Enum> requireNamedList(
    const std::array<std::pair<std::string_view, Enum>, Count> &names,
    const YAML::Node &node,
    const char *pWhat)
{
    if (!node || !node.IsSequence() || node.size() == 0)
    {
        throw PotionParseError{std::string(pWhat) + " must be a non-empty list"};
    }

    std::vector<Enum> values;

    for (const YAML::Node &item : node)
    {
        values.push_back(requireNamed(names, item, pWhat));
    }

    return values;
}

PotionAmount parseAmount(const YAML::Node &node)
{
    PotionAmount amount = {};

    if (node && node.IsScalar())
    {
        amount.constant = node.as<int>();
        return amount;
    }

    if (node && node.IsMap() && node["linear"] && node["linear"].IsSequence() && node["linear"].size() == 2)
    {
        amount.constant = node["linear"][0].as<int>();
        amount.perPower = node["linear"][1].as<int>();
        return amount;
    }

    if (node && node.IsMap() && node["ceil_div"] && node["ceil_div"].as<int>() > 0)
    {
        amount.kind = PotionAmount::Kind::CeilDivide;
        amount.divisor = node["ceil_div"].as<int>();
        return amount;
    }

    if (node && node.IsMap() && node["step"] && node["step"]["per"] && node["step"]["per"].as<int>() > 0)
    {
        amount.kind = PotionAmount::Kind::Step;
        amount.divisor = node["step"]["per"].as<int>();
        amount.a = node["step"]["value"].as<double>();
        return amount;
    }

    if (node && node.IsMap() && node["half_floor"])
    {
        amount.kind = PotionAmount::Kind::Step;
        amount.divisor = 2;
        amount.a = 1;
        return amount;
    }

    if (node && node.IsMap() && node["step_quadratic"] && node["step_quadratic"]["per"].as<int>() > 0)
    {
        const YAML::Node quadratic = node["step_quadratic"];
        amount.kind = PotionAmount::Kind::StepQuadratic;
        amount.divisor = quadratic["per"].as<int>();
        amount.a = quadratic["a"].as<double>();
        amount.b = quadratic["b"].as<double>();
        return amount;
    }

    if (node && node.IsMap() && node["sqrt_ceil"] && node["sqrt_ceil"]["div"].as<double>() > 0)
    {
        amount.kind = PotionAmount::Kind::SqrtCeil;
        amount.b = node["sqrt_ceil"]["div"].as<double>();
        amount.a = node["sqrt_ceil"]["add"] ? node["sqrt_ceil"]["add"].as<double>() : 0;
        return amount;
    }

    if (node && node.IsMap() && node["pool_share"])
    {
        const YAML::Node share = node["pool_share"];
        const std::string pool = share["pool"] ? share["pool"].as<std::string>() : std::string();

        if (pool != "hp" && pool != "sp")
        {
            throw PotionParseError{"pool_share needs pool hp or sp"};
        }

        amount.kind = PotionAmount::Kind::PoolShare;
        amount.pool = pool == "hp" ? PotionPool::HitPoints : PotionPool::SpellPoints;
        amount.a = share["flat"] ? share["flat"].as<double>() : 0;
        amount.b = share["share"].as<double>();
        return amount;
    }

    throw PotionParseError{"an amount must be a number, {linear: [a, b]}, {ceil_div: D}, {step: ..}, "
                           "{step_quadratic: ..}, {sqrt_ceil: ..}, {half_floor: true} or {pool_share: ..}"};
}

PotionLimit parseLimit(const YAML::Node &node)
{
    const std::string limit = node ? node.as<std::string>() : std::string("none");

    if (limit == "none")
    {
        return PotionLimit::None;
    }

    if (limit == "once_per_character")
    {
        return PotionLimit::OncePerCharacter;
    }

    if (limit == "best_step")
    {
        return PotionLimit::BestStep;
    }

    throw PotionParseError{"unknown limit '" + limit + "'"};
}

PotionEffect parseEffect(const YAML::Node &node)
{
    if (!node.IsMap() || node.size() != 1)
    {
        throw PotionParseError{"each effect must be a map with one key"};
    }

    const std::string kind = node.begin()->first.as<std::string>();
    const YAML::Node value = node.begin()->second;
    PotionEffect effect = {};

    if (kind == "restore")
    {
        const std::string pool = value["pool"] ? value["pool"].as<std::string>() : std::string();

        if (pool != "hp" && pool != "sp")
        {
            throw PotionParseError{"restore needs pool hp or sp"};
        }

        effect.kind = PotionEffectKind::Restore;
        effect.pool = pool == "hp" ? PotionPool::HitPoints : PotionPool::SpellPoints;
        effect.amount = parseAmount(value["amount"]);
    }
    else if (kind == "cure" && value.IsScalar() && value.as<std::string>() == "all_restorable")
    {
        effect.kind = PotionEffectKind::CureAllRestorable;
    }
    else if (kind == "cure")
    {
        effect.kind = PotionEffectKind::Cure;
        effect.conditions = requireNamedList(ConditionNames, value, "condition");
    }
    else if (kind == "buff")
    {
        effect.kind = PotionEffectKind::Buff;
        effect.buffId = requireNamed(CharacterBuffNames, value["id"], "buff");
        effect.amount = parseAmount(value["strength"]);

        if (value["unless"])
        {
            effect.conditions.push_back(requireNamed(ConditionNames, value["unless"], "condition"));
        }
    }
    else if (kind == "party_buff")
    {
        effect.kind = PotionEffectKind::PartyBuff;
        effect.partyBuffId = requireNamed(PartyBuffNames, value["id"], "party buff");
        effect.amount = parseAmount(value["power"]);
        effect.partyBuffSkillLevel = value["skill_level"] ? value["skill_level"].as<int>() : 0;
        effect.partyBuffMastery = requireNamed(MasteryNames, value["mastery"], "mastery");
    }
    else if (kind == "immunity")
    {
        effect.kind = PotionEffectKind::Immunity;

        // Disease and Poison name all three stages.
        for (const YAML::Node &item : value)
        {
            const std::string name = item.as<std::string>();

            if (name == "Disease" || name == "Poison")
            {
                for (const char *pStage : {"Weak", "Medium", "Severe"})
                {
                    effect.conditions.push_back(*findNamed(ConditionNames, name + pStage));
                }
            }
            else
            {
                effect.conditions.push_back(requireNamed(ConditionNames, item, "condition"));
            }
        }

        if (effect.conditions.empty())
        {
            throw PotionParseError{"immunity must list conditions"};
        }
    }
    else if (kind == "aura_buff")
    {
        effect.kind = PotionEffectKind::AuraBuff;
        effect.spellId = value["spell"].as<uint32_t>();
    }
    else if (kind == "skill_bonus")
    {
        effect.kind = PotionEffectKind::SkillBonus;
        effect.skillName = canonicalSkillName(value["skill"].as<std::string>());
        effect.amount = parseAmount(value["amount"]);

        if (effect.skillName.empty())
        {
            throw PotionParseError{"unknown skill '" + value["skill"].as<std::string>() + "'"};
        }
    }
    else if (kind == "regeneration")
    {
        effect.kind = PotionEffectKind::Regeneration;
        effect.amount = parseAmount(value["skill"]);
    }
    else if (kind == "skill_points")
    {
        effect.kind = PotionEffectKind::SkillPoints;
        effect.amount = parseAmount(value["amount"]);
        effect.limit = parseLimit(value["limit"]);
    }
    else if (kind == "permanent_stat")
    {
        const std::string into = value["into"] ? value["into"].as<std::string>() : std::string("base");

        if (into != "base" && into != "bonus")
        {
            throw PotionParseError{"permanent_stat into must be base or bonus"};
        }

        effect.kind = PotionEffectKind::PermanentStat;
        effect.stats = requireNamedList(StatNames, value["stats"], "stat");
        effect.amount = parseAmount(value["amount"]);
        effect.intoBonus = into == "bonus";
        effect.limit = parseLimit(value["limit"]);
    }
    else if (kind == "permanent_resistance")
    {
        effect.kind = PotionEffectKind::PermanentResistance;
        effect.resistances = requireNamedList(ResistanceNames, value["resistances"], "resistance");
        effect.amount = parseAmount(value["amount"]);
        effect.limit = parseLimit(value["limit"]);
    }
    else if (kind == "age")
    {
        effect.kind = PotionEffectKind::Age;
        effect.younger = static_cast<bool>(value["younger"]);
        effect.setYears = value["set_years"] ? value["set_years"].as<int>() : 0;

        if (effect.setYears == 0)
        {
            effect.amount = parseAmount(effect.younger ? value["younger"] : value["years"]);
        }

        effect.clearMagicAgeFirst = value["clear_magic_age_first"] && value["clear_magic_age_first"].as<bool>();
    }
    else if (kind == "level_modifier")
    {
        effect.kind = PotionEffectKind::LevelModifier;
        effect.amount = parseAmount(value);
    }
    else
    {
        throw PotionParseError{"unknown effect '" + kind + "'"};
    }

    return effect;
}

void parseItemAction(const YAML::Node &node, PotionDefinition &potion)
{
    const std::string action = node["action"] ? node["action"].as<std::string>() : std::string();

    if (action == "recharge_wand")
    {
        potion.itemAction = PotionItemAction::RechargeWand;
    }
    else if (action == "harden")
    {
        potion.itemAction = PotionItemAction::Harden;
    }
    else if (action == "crafting")
    {
        potion.itemAction = PotionItemAction::Crafting;
    }
    else if (action == "temporary_special_enchant")
    {
        potion.itemAction = PotionItemAction::TemporarySpecialEnchant;
        potion.enchant = requireNamed(PotionEnchantNames, node["enchant"], "potion enchantment");
    }
    else
    {
        throw PotionParseError{"unknown item action '" + action + "'"};
    }
}
}

int PotionAmount::evaluate(int power, double estimatedPool) const
{
    switch (kind)
    {
        case Kind::CeilDivide:
            return static_cast<int>(std::ceil(static_cast<double>(power) / divisor));
        case Kind::Step:
            return static_cast<int>((power / divisor) * a);
        case Kind::StepQuadratic:
        {
            const double steps = power / divisor;
            return static_cast<int>(a * steps * steps + b * steps);
        }
        case Kind::SqrtCeil:
            return static_cast<int>(std::ceil(std::sqrt(static_cast<double>(power)) / b) + a);
        case Kind::PoolShare:
            return static_cast<int>(std::lround(a + b * estimatedPool));
        case Kind::Linear:
        default:
            return constant + perPower * power;
    }
}

bool PotionEffectTable::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    m_potions.clear();
    std::string context = "potion_effects.yml";

    try
    {
        const YAML::Node root = YAML::Load(text);
        const YAML::Node rules = root["rules"];
        const YAML::Node duration = rules["duration"];
        m_timedSecondsPerPower = 0.0f;
        m_fixedDurationSeconds = 0.0f;
        m_grandmasterAlchemySecondsPerSkill = 0.0f;

        if (duration && duration["per_power_minutes"] && duration["per_power_minutes"].as<float>() > 0)
        {
            m_timedSecondsPerPower = duration["per_power_minutes"].as<float>() * 60.0f;
        }
        else if (duration && duration["hours"] && duration["hours"].as<float>() > 0)
        {
            m_fixedDurationSeconds = duration["hours"].as<float>() * 3600.0f;
            m_grandmasterAlchemySecondsPerSkill = duration["gm_alchemy_minutes_per_skill"]
                ? duration["gm_alchemy_minutes_per_skill"].as<float>() * 60.0f
                : 0.0f;
        }
        else
        {
            throw PotionParseError{"rules.duration needs a positive per_power_minutes or hours"};
        }

        m_powerCap = rules["power_cap"] ? rules["power_cap"].as<int>() : 0;
        m_combatRecoveryTicks = rules["combat_recovery"] ? rules["combat_recovery"]["value"].as<float>() : 0.0f;
        m_combatRecoveryOnlyNearEnemies = rules["combat_recovery"]
            && rules["combat_recovery"]["only_when_enemies_near"]
            && rules["combat_recovery"]["only_when_enemies_near"].as<bool>();
        const std::string payer = rules["combat_recovery"] && rules["combat_recovery"]["payer"]
            ? rules["combat_recovery"]["payer"].as<std::string>()
            : "drinker";

        if (payer != "drinker" && payer != "active")
        {
            throw PotionParseError{"rules.combat_recovery.payer must be drinker or active"};
        }

        m_combatRecoveryActiveMemberPays = payer == "active";
        m_allRecipesKnown = rules["all_recipes_known"] && rules["all_recipes_known"].as<bool>();
        const YAML::Node potions = root["potions"];

        if (!potions || !potions.IsMap())
        {
            throw PotionParseError{"potions must be a map of item ids"};
        }

        for (const auto &entry : potions)
        {
            PotionDefinition potion = {};
            potion.itemId = entry.first.as<uint32_t>();
            context = "potion " + std::to_string(potion.itemId);
            const YAML::Node body = entry.second;
            potion.oncePerCharacter = body["once_per_character"] && body["once_per_character"].as<bool>();
            potion.minimumPower = body["min_power"] ? body["min_power"].as<int>() : 0;
            potion.charges = std::max(1, body["charges"] ? body["charges"].as<int>() : 1);
            potion.rechargeable = body["rechargeable"] && body["rechargeable"].as<bool>();

            if (body["effects"])
            {
                for (const YAML::Node &effect : body["effects"])
                {
                    potion.effects.push_back(parseEffect(effect));
                }
            }

            if (body["item"])
            {
                parseItemAction(body["item"], potion);
            }

            if (potion.effects.empty() == (potion.itemAction == PotionItemAction::None))
            {
                throw PotionParseError{"needs either effects or an item action"};
            }

            m_potions[potion.itemId] = std::move(potion);
        }
    }
    catch (const PotionParseError &error)
    {
        errorMessage = context + ": " + error.message;
        m_potions.clear();
        return false;
    }
    catch (const std::exception &exception)
    {
        errorMessage = context + ": " + exception.what();
        m_potions.clear();
        return false;
    }

    return true;
}

const PotionDefinition *PotionEffectTable::find(uint32_t itemId) const
{
    const auto potion = m_potions.find(itemId);
    return potion != m_potions.end() ? &potion->second : nullptr;
}

float PotionEffectTable::timedSecondsPerPower() const
{
    return m_timedSecondsPerPower;
}

float PotionEffectTable::fixedDurationSeconds() const
{
    return m_fixedDurationSeconds;
}

float PotionEffectTable::grandmasterAlchemySecondsPerSkill() const
{
    return m_grandmasterAlchemySecondsPerSkill;
}

int PotionEffectTable::powerCap() const
{
    return m_powerCap;
}

float PotionEffectTable::combatRecoveryTicks() const
{
    return m_combatRecoveryTicks;
}

bool PotionEffectTable::combatRecoveryOnlyNearEnemies() const
{
    return m_combatRecoveryOnlyNearEnemies;
}

bool PotionEffectTable::combatRecoveryActiveMemberPays() const
{
    return m_combatRecoveryActiveMemberPays;
}

bool PotionEffectTable::allRecipesKnown() const
{
    return m_allRecipesKnown;
}
}
