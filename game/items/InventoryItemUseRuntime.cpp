#include "game/items/InventoryItemUseRuntime.h"

#include "game/gameplay/GameMechanics.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/party/SpellIds.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MinutesPerDay = 24 * 60;
constexpr int DaysPerMonth = 28;
constexpr uint32_t GreenAppleItemId = 655;
constexpr uint32_t HorseshoeItemId = 656;
constexpr uint32_t DimensionDoorScrollItemId = 190;
// A spell scroll casts at skill 7, Master, as in MMerge (ExtraEvents.lua PlayerCastSpell; the original games used 5).
constexpr uint32_t ScrollSpellSkillLevel = 7;
constexpr uint32_t ChargedConnectorStoneItemId = 624;
constexpr uint32_t DischargedConnectorStoneItemId = 625;
constexpr uint32_t DeckOfFateItemId = 2067;
constexpr uint32_t ExtraPotionPlayerBitBase = 200000;

std::string lowerAscii(std::string value)
{
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}

bool itemNameEquals(const ItemDefinition &itemDefinition, const std::string &name)
{
    return lowerAscii(itemDefinition.name) == lowerAscii(name);
}

bool itemNameContains(const ItemDefinition &itemDefinition, const std::string &text)
{
    return lowerAscii(itemDefinition.name).find(lowerAscii(text)) != std::string::npos;
}

std::vector<std::string> pipeSeparatedSkills(const std::string &value)
{
    std::vector<std::string> result;
    size_t begin = 0;

    while (begin <= value.size())
    {
        const size_t end = value.find('|', begin);
        const std::string canonicalName = canonicalSkillName(value.substr(begin, end - begin));

        if (!canonicalName.empty()
            && std::find(result.begin(), result.end(), canonicalName) == result.end())
        {
            result.push_back(canonicalName);
        }

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    return result;
}

int totalDaysFromGameMinutes(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes)));
    return totalMinutes / MinutesPerDay;
}

int monthIndexFromGameMinutes(float gameMinutes)
{
    return (totalDaysFromGameMinutes(gameMinutes) / DaysPerMonth) % 12;
}

int monthWeekFromGameMinutes(float gameMinutes)
{
    return (totalDaysFromGameMinutes(gameMinutes) % DaysPerMonth) / 7;
}

int dayOfMonthFromGameMinutes(float gameMinutes)
{
    return 1 + totalDaysFromGameMinutes(gameMinutes) % DaysPerMonth;
}

std::optional<uint32_t> tryParseSpellId(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.mod1.size() < 2
        || (itemDefinition.mod1[0] != 'S' && itemDefinition.mod1[0] != 's'))
    {
        return std::nullopt;
    }

    for (size_t index = 1; index < itemDefinition.mod1.size(); ++index)
    {
        if (!std::isdigit(static_cast<unsigned char>(itemDefinition.mod1[index])))
        {
            return std::nullopt;
        }
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(itemDefinition.mod1.substr(1)));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

int maxSpellPointsForMember(const Character &member)
{
    return Party::effectiveMaximumSpellPoints(member);
}

bool restoreSpellPoints(Character &member, int amount)
{
    if (amount <= 0)
    {
        return false;
    }

    const int previousSpellPoints = member.spellPoints;
    member.spellPoints = std::clamp(member.spellPoints + amount, 0, maxSpellPointsForMember(member));
    return member.spellPoints > previousSpellPoints;
}

// What a cure-all potion (Divine Cure) clears.
constexpr std::array<CharacterCondition, 14> RestorableConditions = {
    CharacterCondition::Cursed,
    CharacterCondition::Weak,
    CharacterCondition::Asleep,
    CharacterCondition::Fear,
    CharacterCondition::Drunk,
    CharacterCondition::Insane,
    CharacterCondition::PoisonWeak,
    CharacterCondition::DiseaseWeak,
    CharacterCondition::PoisonMedium,
    CharacterCondition::DiseaseMedium,
    CharacterCondition::PoisonSevere,
    CharacterCondition::DiseaseSevere,
    CharacterCondition::Paralyzed,
    CharacterCondition::Zombie,
};

bool clearAllRestorableConditions(Party &party, size_t memberIndex)
{
    bool changed = false;

    for (CharacterCondition condition : RestorableConditions)
    {
        changed = party.clearMemberCondition(memberIndex, condition) || changed;
    }

    return changed;
}

bool markExtraPotionUsed(Character &member, uint32_t itemId)
{
    const uint32_t bit = ExtraPotionPlayerBitBase + itemId;

    if (member.playerBits.contains(bit))
    {
        return false;
    }

    member.playerBits.insert(bit);
    return true;
}

// MM8 keeps a buff that would outlast the potion's.
void applyPotionBuff(
    Party &party,
    size_t memberIndex,
    CharacterBuffId buffId,
    float durationSeconds,
    int buffPower)
{
    const CharacterBuffState *pActiveBuff = party.characterBuff(memberIndex, buffId);

    if (pActiveBuff != nullptr && pActiveBuff->remainingSeconds >= durationSeconds)
    {
        return;
    }

    party.applyCharacterBuff(
        memberIndex,
        buffId,
        durationSeconds,
        buffPower,
        0,
        0,
        SkillMastery::Master,
        static_cast<uint32_t>(memberIndex));
}

void decreaseBaseStat(uint32_t &stat, uint32_t amount)
{
    stat = stat > amount ? stat - amount : 0;
}

void addPotionStat(Character &member, PotionStat stat, int amount, bool intoBonus)
{
    uint32_t *pBase = nullptr;
    int *pBonus = nullptr;

    switch (stat)
    {
        case PotionStat::Might:
            pBase = &member.might;
            pBonus = &member.permanentBonuses.might;
            break;
        case PotionStat::Intellect:
            pBase = &member.intellect;
            pBonus = &member.permanentBonuses.intellect;
            break;
        case PotionStat::Personality:
            pBase = &member.personality;
            pBonus = &member.permanentBonuses.personality;
            break;
        case PotionStat::Endurance:
            pBase = &member.endurance;
            pBonus = &member.permanentBonuses.endurance;
            break;
        case PotionStat::Accuracy:
            pBase = &member.accuracy;
            pBonus = &member.permanentBonuses.accuracy;
            break;
        case PotionStat::Speed:
            pBase = &member.speed;
            pBonus = &member.permanentBonuses.speed;
            break;
        case PotionStat::Luck:
            pBase = &member.luck;
            pBonus = &member.permanentBonuses.luck;
            break;
    }

    if (intoBonus)
    {
        *pBonus += amount;
    }
    else if (amount >= 0)
    {
        *pBase += static_cast<uint32_t>(amount);
    }
    else
    {
        decreaseBaseStat(*pBase, static_cast<uint32_t>(-amount));
    }
}

int &potionResistance(Character &member, PotionResistance resistance)
{
    switch (resistance)
    {
        case PotionResistance::Fire:
            return member.baseResistances.fire;
        case PotionResistance::Air:
            return member.baseResistances.air;
        case PotionResistance::Water:
            return member.baseResistances.water;
        case PotionResistance::Earth:
            return member.baseResistances.earth;
        case PotionResistance::Mind:
            return member.baseResistances.mind;
        case PotionResistance::Body:
        default:
            return member.baseResistances.body;
    }
}

// Sets a timed potion effect, replacing one of the same kind and key (a new drink restarts it at its own strength).
void setTimedPotionEffect(Character &member, TimedPotionEffect::Kind kind, uint32_t key, int amount, float seconds)
{
    std::erase_if(
        member.rulesetState.potionEffects,
        [kind, key](const TimedPotionEffect &effect)
        {
            return effect.kind == kind && effect.key == key;
        });
    member.rulesetState.potionEffects.push_back({kind, key, amount, seconds});
}

// The step a best-step potion reaches at this power (MAW's black potions: one step per 50 power).
int potionStep(const PotionDefinition &potion, int power)
{
    for (const PotionEffect &effect : potion.effects)
    {
        if (effect.limit == PotionLimit::BestStep && effect.amount.divisor > 0)
        {
            return power / effect.amount.divisor;
        }
    }

    return 0;
}

// How much a best-step effect adds over the step the character reached before.
int bestStepGain(const PotionEffect &effect, int step, int bestStep)
{
    const int divisor = std::max(1, effect.amount.divisor);
    return effect.amount.evaluate(step * divisor) - effect.amount.evaluate(bestStep * divisor);
}

enum class PotionDrinkOutcome : uint8_t
{
    Drunk,
    // A once-per-character potion the character drank before, or a best-step potion that does not beat their best.
    NoBenefit,
};

// Drinks a potion defined in potion_effects.yml at `power` (already capped). Nothing changes on NoBenefit.
PotionDrinkOutcome applyPotionEffects(
    Party &party,
    size_t memberIndex,
    Character &member,
    const PotionDefinition &potion,
    float durationSeconds,
    int power,
    const PotionRules &potionRules)
{
    const int step = potionStep(potion, power);
    const auto bestStep = member.rulesetState.potionSteps.find(potion.itemId);
    const int previousStep = bestStep != member.rulesetState.potionSteps.end() ? bestStep->second : 0;
    const bool hasBestStep = std::any_of(
        potion.effects.begin(),
        potion.effects.end(),
        [](const PotionEffect &effect)
        {
            return effect.limit == PotionLimit::BestStep;
        });

    if (hasBestStep && step <= previousStep)
    {
        return PotionDrinkOutcome::NoBenefit;
    }

    if (potion.oncePerCharacter && !markExtraPotionUsed(member, potion.itemId))
    {
        return PotionDrinkOutcome::NoBenefit;
    }

    for (const PotionEffect &effect : potion.effects)
    {
        const int amount = effect.limit == PotionLimit::BestStep
            ? bestStepGain(effect, step, previousStep)
            : effect.amount.evaluate(power, potionRules.estimatedPool(effect.amount.pool, power));

        switch (effect.kind)
        {
            case PotionEffectKind::Restore:
                if (effect.pool == PotionPool::HitPoints)
                {
                    party.healMember(memberIndex, amount);
                }
                else
                {
                    restoreSpellPoints(member, amount);
                }
                break;
            case PotionEffectKind::Cure:
                for (CharacterCondition condition : effect.conditions)
                {
                    party.clearMemberCondition(memberIndex, condition);
                }
                break;
            case PotionEffectKind::CureAllRestorable:
                clearAllRestorableConditions(party, memberIndex);
                break;
            case PotionEffectKind::Buff:
                if (effect.conditions.empty()
                    || !member.conditions.test(static_cast<size_t>(effect.conditions.front())))
                {
                    applyPotionBuff(party, memberIndex, effect.buffId, durationSeconds, amount);
                }
                break;
            case PotionEffectKind::PartyBuff:
                party.applyPartyBuff(
                    effect.partyBuffId,
                    durationSeconds,
                    amount,
                    0,
                    static_cast<uint32_t>(effect.partyBuffSkillLevel),
                    effect.partyBuffMastery,
                    static_cast<uint32_t>(memberIndex));
                break;
            case PotionEffectKind::PermanentStat:
                for (PotionStat stat : effect.stats)
                {
                    addPotionStat(member, stat, amount, effect.intoBonus);
                }
                break;
            case PotionEffectKind::PermanentResistance:
                for (PotionResistance resistance : effect.resistances)
                {
                    potionResistance(member, resistance) += amount;
                }
                break;
            case PotionEffectKind::Age:
                if (effect.setYears > 0)
                {
                    member.birthYear = uint32_t(std::max(0, CharacterAgeReferenceYear - effect.setYears));
                    member.ageModifier = 0;
                }
                else if (!effect.younger)
                {
                    member.ageModifier += amount;
                }
                else if (effect.clearMagicAgeFirst && member.ageModifier > 0)
                {
                    member.ageModifier = 0;
                }
                else
                {
                    member.ageModifier -= std::max(1, amount);
                }
                break;
            case PotionEffectKind::LevelModifier:
                member.levelModifier += amount;
                break;
            case PotionEffectKind::Immunity:
                for (CharacterCondition condition : effect.conditions)
                {
                    setTimedPotionEffect(
                        member, TimedPotionEffect::Kind::Immunity, uint32_t(condition), 1, durationSeconds);
                }
                break;
            case PotionEffectKind::AuraBuff:
                setTimedPotionEffect(member, TimedPotionEffect::Kind::Aura, effect.spellId, power, durationSeconds);
                break;
            case PotionEffectKind::SkillBonus:
                setTimedPotionEffect(
                    member,
                    TimedPotionEffect::Kind::SkillBonus,
                    skillIdForSkillName(effect.skillName).value_or(0),
                    amount,
                    durationSeconds);
                break;
            case PotionEffectKind::Regeneration:
                setTimedPotionEffect(member, TimedPotionEffect::Kind::Regeneration, 0, amount, durationSeconds);
                break;
            case PotionEffectKind::SkillPoints:
                member.skillPoints += uint32_t(std::max(0, amount));
                break;
        }
    }

    if (hasBestStep)
    {
        member.rulesetState.potionSteps[potion.itemId] = step;
    }

    party.rebuildMagicalBonusesFromBuffs();
    return PotionDrinkOutcome::Drunk;
}

// How long a potion's timed effects last: Standard a number of minutes per point of power; MAW a fixed time plus
// minutes per Alchemy point of the party's best Grandmaster alchemist.
float potionDurationSeconds(const Party &party, const PotionEffectTable &effects, int power)
{
    if (effects.timedSecondsPerPower() > 0)
    {
        return effects.timedSecondsPerPower() * static_cast<float>(power);
    }

    int bestGrandmasterSkill = 0;

    for (const Character &member : party.members())
    {
        const CharacterSkill *pAlchemy = member.findSkill("Alchemy");

        if (pAlchemy != nullptr && pAlchemy->mastery >= SkillMastery::Grandmaster)
        {
            bestGrandmasterSkill =
                std::max(bestGrandmasterSkill, static_cast<int>(pAlchemy->level) + member.skillBonus("Alchemy"));
        }
    }

    return effects.fixedDurationSeconds()
        + effects.grandmasterAlchemySecondsPerSkill() * static_cast<float>(bestGrandmasterSkill);
}

// Who pays a potion's recovery: the drinker when ready (MAW; not when the active member pays, as in the original
// games), else the active member, else the first ready one.
std::optional<size_t> potionRecoveryPayer(const Party &party, size_t drinkerIndex, bool activeMemberPays)
{
    const auto ready = [&party](size_t memberIndex)
    {
        const Character *pMember = party.member(memberIndex);
        return pMember != nullptr && GameMechanics::canTakeGameplayAction(*pMember);
    };

    if (!activeMemberPays && ready(drinkerIndex))
    {
        return drinkerIndex;
    }

    if (ready(party.activeMemberIndex()))
    {
        return party.activeMemberIndex();
    }

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        if (ready(memberIndex))
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

std::optional<CharacterCondition> majorCondition(const Character &member)
{
    constexpr CharacterCondition conditions[] = {
        CharacterCondition::Eradicated,
        CharacterCondition::Petrified,
        CharacterCondition::Dead,
        CharacterCondition::Unconscious,
        CharacterCondition::Paralyzed,
        CharacterCondition::Asleep,
        CharacterCondition::Insane,
        CharacterCondition::Fear,
        CharacterCondition::DiseaseSevere,
        CharacterCondition::DiseaseMedium,
        CharacterCondition::DiseaseWeak,
        CharacterCondition::PoisonSevere,
        CharacterCondition::PoisonMedium,
        CharacterCondition::PoisonWeak,
        CharacterCondition::Weak,
        CharacterCondition::Cursed,
        CharacterCondition::Drunk,
    };

    for (CharacterCondition condition : conditions)
    {
        if (member.conditions.test(static_cast<size_t>(condition)))
        {
            return condition;
        }
    }

    if (member.health <= 0)
    {
        return CharacterCondition::Unconscious;
    }

    return std::nullopt;
}

std::string conditionDisplayName(CharacterCondition condition)
{
    switch (condition)
    {
        case CharacterCondition::Cursed:
            return "Cursed";
        case CharacterCondition::Weak:
            return "Weak";
        case CharacterCondition::Asleep:
            return "Asleep";
        case CharacterCondition::Fear:
            return "Afraid";
        case CharacterCondition::Drunk:
            return "Drunk";
        case CharacterCondition::Insane:
            return "Insane";
        case CharacterCondition::PoisonWeak:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::PoisonSevere:
            return "Poisoned";
        case CharacterCondition::DiseaseWeak:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::DiseaseSevere:
            return "Diseased";
        case CharacterCondition::Paralyzed:
            return "Paralyzed";
        case CharacterCondition::Unconscious:
            return "Unconscious";
        case CharacterCondition::Dead:
            return "Dead";
        case CharacterCondition::Petrified:
            return "Petrified";
        case CharacterCondition::Eradicated:
            return "Eradicated";
        case CharacterCondition::Zombie:
            return "Zombie";
        case CharacterCondition::Count:
            break;
    }

    return {};
}

bool canUseSpellItem(const Character &member)
{
    const std::optional<CharacterCondition> condition = majorCondition(member);
    return !condition.has_value()
        || (*condition != CharacterCondition::Asleep
            && *condition != CharacterCondition::Paralyzed
            && *condition != CharacterCondition::Unconscious
            && *condition != CharacterCondition::Dead
            && *condition != CharacterCondition::Petrified
            && *condition != CharacterCondition::Eradicated);
}

std::string inactiveCharacterStatusText(const Character &member)
{
    const std::optional<CharacterCondition> condition = majorCondition(member);

    if (condition)
    {
        return "That player is " + conditionDisplayName(*condition);
    }

    return "That player is not active";
}

std::string itemDisplayNameForStatus(const ItemDefinition &itemDefinition)
{
    return itemDefinition.name.empty() ? "Item" : itemDefinition.name;
}

std::string itemCannotBeUsedStatusText(const ItemDefinition &itemDefinition)
{
    return itemDisplayNameForStatus(itemDefinition) + " can not be used that way";
}

bool isFoodItem(const InventoryItem &item, const ItemDefinition &itemDefinition)
{
    // Whole names only: "Labyrinth Grapple" is a polearm, not an apple.
    return item.objectDescriptionId == GreenAppleItemId
        || itemNameEquals(itemDefinition, "apple")
        || itemNameEquals(itemDefinition, "red apple")
        || itemNameEquals(itemDefinition, "green apple")
        || itemNameEquals(itemDefinition, "tobersk fruit");
}

std::optional<SoundId> instrumentSoundId(const ItemDefinition &itemDefinition)
{
    if (itemNameContains(itemDefinition, "lute"))
    {
        return SoundId::LuteGuitar;
    }

    if (itemNameContains(itemDefinition, "faerie pipes")
        || itemNameContains(itemDefinition, "pan flute")
        || itemNameContains(itemDefinition, "panflute"))
    {
        return SoundId::PanFlute;
    }

    if (itemNameContains(itemDefinition, "trumpet"))
    {
        return SoundId::Trumpet;
    }

    if (itemNameEquals(itemDefinition, "flute"))
    {
        return SoundId::Flute;
    }

    return std::nullopt;
}

void addPermanentStatBonus(Character &member, int CharacterStatBonuses::*field, int value)
{
    member.permanentBonuses.*field += value;
}

void addPermanentResistanceBonus(Character &member, int CharacterResistanceSet::*field, int value)
{
    member.permanentBonuses.resistances.*field += value;
}

std::string applyGenieLampReward(Party &party, Character &member, size_t memberIndex, float gameMinutes)
{
    const int value = monthWeekFromGameMinutes(gameMinutes) + 1;

    switch (monthIndexFromGameMinutes(gameMinutes))
    {
        case 0:
            addPermanentStatBonus(member, &CharacterStatBonuses::might, value);
            return "+" + std::to_string(value) + " Might Permanent";
        case 1:
            addPermanentStatBonus(member, &CharacterStatBonuses::intellect, value);
            return "+" + std::to_string(value) + " Intellect Permanent";
        case 2:
            addPermanentStatBonus(member, &CharacterStatBonuses::personality, value);
            return "+" + std::to_string(value) + " Personality Permanent";
        case 3:
            addPermanentStatBonus(member, &CharacterStatBonuses::endurance, value);
            return "+" + std::to_string(value) + " Endurance Permanent";
        case 4:
            addPermanentStatBonus(member, &CharacterStatBonuses::accuracy, value);
            return "+" + std::to_string(value) + " Accuracy Permanent";
        case 5:
            addPermanentStatBonus(member, &CharacterStatBonuses::speed, value);
            return "+" + std::to_string(value) + " Speed Permanent";
        case 6:
            addPermanentStatBonus(member, &CharacterStatBonuses::luck, value);
            return "+" + std::to_string(value) + " Luck Permanent";
        case 7:
        {
            const int gold = 1000 * value;
            party.addGold(gold);
            return "+" + std::to_string(gold) + " Gold";
        }
        case 8:
        {
            const int food = 5 * value;
            party.addFood(food);
            return "+" + std::to_string(food) + " Food";
        }
        case 9:
            member.skillPoints += static_cast<uint32_t>(2 * value);
            return "+" + std::to_string(2 * value) + " Skill Points";
        case 10:
            party.addExperienceToMember(memberIndex, 2500LL * value);
            return "+" + std::to_string(2500 * value) + " Experience";
        case 11:
        {
            static thread_local std::mt19937 rng(std::random_device{}());
            const int resistanceIndex = std::uniform_int_distribution<int>(0, 5)(rng);

            switch (resistanceIndex)
            {
                case 0:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::fire, value);
                    return "+" + std::to_string(value) + " Fire Permanent";
                case 1:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::air, value);
                    return "+" + std::to_string(value) + " Air Permanent";
                case 2:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::water, value);
                    return "+" + std::to_string(value) + " Water Permanent";
                case 3:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::earth, value);
                    return "+" + std::to_string(value) + " Earth Permanent";
                case 4:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::mind, value);
                    return "+" + std::to_string(value) + " Mind Permanent";
                default:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::body, value);
                    return "+" + std::to_string(value) + " Body Permanent";
            }
        }
        default:
            break;
    }

    return {};
}

std::string applyDeckOfFateReward(Character &member, float gameMinutes)
{
    const int value = monthWeekFromGameMinutes(gameMinutes) + 1;

    switch (monthIndexFromGameMinutes(gameMinutes))
    {
        case 0:
            addPermanentStatBonus(member, &CharacterStatBonuses::might, value);
            return "+" + std::to_string(value) + " Might!";
        case 1:
            addPermanentStatBonus(member, &CharacterStatBonuses::intellect, value);
            return "+" + std::to_string(value) + " Intellect!";
        case 2:
            addPermanentStatBonus(member, &CharacterStatBonuses::personality, value);
            return "+" + std::to_string(value) + " Personality!";
        case 3:
            addPermanentStatBonus(member, &CharacterStatBonuses::endurance, value);
            return "+" + std::to_string(value) + " Endurance!";
        case 4:
            addPermanentStatBonus(member, &CharacterStatBonuses::accuracy, value);
            return "+" + std::to_string(value) + " Accuracy!";
        case 5:
            addPermanentStatBonus(member, &CharacterStatBonuses::speed, value);
            return "+" + std::to_string(value) + " Speed!";
        case 6:
            addPermanentStatBonus(member, &CharacterStatBonuses::luck, value);
            return "+" + std::to_string(value) + " Luck!";
        case 7:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::fire, value);
            return "+" + std::to_string(value) + " Fire Resistance!";
        case 8:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::air, value);
            return "+" + std::to_string(value) + " Air Resistance!";
        case 9:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::water, value);
            return "+" + std::to_string(value) + " Water Resistance!";
        case 10:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::earth, value);
            return "+" + std::to_string(value) + " Earth Resistance!";
        case 11:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::body, value);
            return "+" + std::to_string(value) + " Body Resistance!";
        default:
            break;
    }

    return {};
}

SkillMastery requiredMasteryForSpell(uint32_t spellId)
{
    const std::optional<std::string> skillName = resolveMagicSkillName(spellId);

    if (!skillName)
    {
        return SkillMastery::None;
    }

    const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(*skillName);

    if (!spellRange || spellId < spellRange->first || spellId > spellRange->second)
    {
        return SkillMastery::None;
    }

    const uint32_t spellCount = spellRange->second - spellRange->first + 1;

    if (spellCount < 11)
    {
        return SkillMastery::Normal;
    }

    const uint32_t spellOrdinal = spellId - spellRange->first + 1;

    if (spellOrdinal <= 4)
    {
        return SkillMastery::Normal;
    }

    if (spellOrdinal <= 7)
    {
        return SkillMastery::Expert;
    }

    if (spellOrdinal <= 10)
    {
        return SkillMastery::Master;
    }

    return SkillMastery::Grandmaster;
}

InventoryItemUseResult makeFailure(
    InventoryItemUseAction action,
    const std::string &statusText,
    std::optional<SpeechId> speechId = std::nullopt)
{
    InventoryItemUseResult result = {};
    result.handled = true;
    result.action = action;
    result.statusText = statusText;
    result.speechId = speechId;
    return result;
}
}

InventoryItemUseAction InventoryItemUseRuntime::classifyItemUse(
    const InventoryItem &item,
    const ItemTable &itemTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return InventoryItemUseAction::None;
    }

    if (item.objectDescriptionId == DimensionDoorScrollItemId)
    {
        return InventoryItemUseAction::UseDimensionDoorScroll;
    }

    if (item.objectDescriptionId == ChargedConnectorStoneItemId
        || item.objectDescriptionId == DischargedConnectorStoneItemId)
    {
        return InventoryItemUseAction::UseConnectorStone;
    }

    if (lowerAscii(pItemDefinition->useAction) == "learnskill")
    {
        return InventoryItemUseAction::LearnSkill;
    }

    if (lowerAscii(pItemDefinition->useAction) == "readtext")
    {
        return InventoryItemUseAction::ReadMessageScroll;
    }

    if (lowerAscii(pItemDefinition->useAction) == "granttechpoints")
    {
        return InventoryItemUseAction::GrantTechPoints;
    }

    if (lowerAscii(pItemDefinition->useAction) == "useshieldcell")
    {
        return InventoryItemUseAction::UseShieldCell;
    }

    if (lowerAscii(pItemDefinition->useAction) == "useshieldburst")
    {
        return InventoryItemUseAction::UseShieldBurst;
    }

    if (lowerAscii(pItemDefinition->useAction) == "throwempgrenade")
    {
        return InventoryItemUseAction::ThrowEmpGrenade;
    }

    if (lowerAscii(pItemDefinition->useAction) == "usestim")
    {
        return InventoryItemUseAction::UseStim;
    }

    if (lowerAscii(pItemDefinition->useAction) == "placebreachcharge")
    {
        return InventoryItemUseAction::PlaceBreachCharge;
    }

    if (lowerAscii(pItemDefinition->useAction) == "eatfood")
    {
        return InventoryItemUseAction::EatFoodItem;
    }

    if (pItemDefinition->equipStat == "Sscroll")
    {
        return InventoryItemUseAction::CastScroll;
    }

    if (pItemDefinition->equipStat == "Book")
    {
        return InventoryItemUseAction::LearnSpell;
    }

    const MergedPotionSettingEntry *pPotionSetting =
        pPotionSettingTable != nullptr ? pPotionSettingTable->getByItemId(item.objectDescriptionId) : nullptr;

    if (pPotionSetting != nullptr)
    {
        return pPotionSetting->drinkable ? InventoryItemUseAction::ConsumePotion : InventoryItemUseAction::None;
    }

    if (pItemDefinition->equipStat == "Bottle")
    {
        return InventoryItemUseAction::ConsumePotion;
    }

    if (pItemDefinition->equipStat == "Mscroll")
    {
        return InventoryItemUseAction::ReadMessageScroll;
    }

    if (item.objectDescriptionId == HorseshoeItemId || itemNameEquals(*pItemDefinition, "horseshoe"))
    {
        return InventoryItemUseAction::UseHorseshoe;
    }

    if (itemNameEquals(*pItemDefinition, "genie lamp"))
    {
        return InventoryItemUseAction::UseGenieLamp;
    }

    if (item.objectDescriptionId == DeckOfFateItemId || itemNameEquals(*pItemDefinition, "deck of fate"))
    {
        return InventoryItemUseAction::UseDeckOfFate;
    }

    if (isFoodItem(item, *pItemDefinition))
    {
        return InventoryItemUseAction::EatFoodItem;
    }

    if (instrumentSoundId(*pItemDefinition).has_value())
    {
        return InventoryItemUseAction::PlayInstrument;
    }

    if (itemNameEquals(*pItemDefinition, "temple in a bottle"))
    {
        return InventoryItemUseAction::UseTempleInABottle;
    }

    if (pReagentSettingTable != nullptr
        && pReagentSettingTable->resultItemIdForReagent(item.objectDescriptionId).has_value())
    {
        return InventoryItemUseAction::UseReagent;
    }

    if (pItemDefinition->equipStat == "Reagent")
    {
        return InventoryItemUseAction::UseReagent;
    }

    if (!pItemDefinition->equipStat.empty()
        && pItemDefinition->equipStat != "0"
        && pItemDefinition->equipStat != "N / A"
        && pItemDefinition->equipStat != "Misc")
    {
        return InventoryItemUseAction::Equip;
    }

    return InventoryItemUseAction::None;
}

InventoryItemUseResult InventoryItemUseRuntime::useItemOnMember(
    Party &party,
    size_t targetMemberIndex,
    const InventoryItem &item,
    const ItemTable &itemTable,
    const ReadableScrollTable *pReadableScrollTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable,
    const InventoryItemUseContext &context)
{
    InventoryItemUseResult result = {};
    result.action = classifyItemUse(item, itemTable, pPotionSettingTable, pReagentSettingTable);

    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);
    Character *pTargetMember = party.member(targetMemberIndex);

    if (pItemDefinition == nullptr || pTargetMember == nullptr)
    {
        return makeFailure(result.action, "Item can not be used that way");
    }

    switch (result.action)
    {
        case InventoryItemUseAction::CastScroll:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            if (context.underwater)
            {
                return makeFailure(result.action, "You can not do that while you are underwater!");
            }

            if (pTargetMember->recoverySecondsRemaining > 0.0f)
            {
                return makeFailure(result.action, "That player is not active");
            }

            const std::optional<uint32_t> spellId = tryParseSpellId(*pItemDefinition);

            if (!spellId)
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
            }

            result.handled = true;
            result.consumed = true;
            result.spellId = *spellId;
            result.spellSkillLevelOverride = ScrollSpellSkillLevel;
            result.spellSkillMasteryOverride = SkillMastery::Master;
            result.spellBypassRequiredMastery = true;
            return result;
        }

        case InventoryItemUseAction::UseDimensionDoorScroll:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            if (context.underwater)
            {
                return makeFailure(result.action, "You can not do that while you are underwater!");
            }

            if (pTargetMember->recoverySecondsRemaining > 0.0f)
            {
                return makeFailure(result.action, "That player is not active");
            }

            result.handled = true;
            result.consumed = true;
            result.spellId = spellIdValue(SpellId::TownPortal);
            result.spellSkillLevelOverride = ScrollSpellSkillLevel;
            result.spellSkillMasteryOverride = SkillMastery::Master;
            result.spellBypassRequiredMastery = true;
            return result;
        }

        case InventoryItemUseAction::LearnSpell:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            const std::optional<uint32_t> spellId = tryParseSpellId(*pItemDefinition);

            if (!spellId)
            {
                return makeFailure(
                    result.action,
                    itemCannotBeUsedStatusText(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            const std::optional<std::string> skillName = resolveMagicSkillName(*spellId);

            if (!skillName)
            {
                return makeFailure(
                    result.action,
                    itemCannotBeUsedStatusText(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            const CharacterSkill *pSkill = pTargetMember->findSkill(*skillName);

            // Classes whose spells come from their school masteries or from casting (MAW) read no books.
            if (!boundGameRules().classes.learnsSpellsFromBooks(*pTargetMember))
            {
                return makeFailure(
                    result.action,
                    displayClassName(pTargetMember->className) + "s can't learn spells from books",
                    SpeechId::CantLearnSpell);
            }

            if (pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0)
            {
                return makeFailure(
                    result.action,
                    "You don't have the skill to learn " + itemDisplayNameForStatus(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            const SkillMastery requiredMastery = requiredMasteryForSpell(*spellId);

            if (requiredMastery != SkillMastery::None && pSkill->mastery < requiredMastery)
            {
                return makeFailure(
                    result.action,
                    "You don't have the skill to learn " + itemDisplayNameForStatus(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            if (pTargetMember->knowsSpell(*spellId))
            {
                result = makeFailure(
                    result.action,
                    "You already know the " + itemDisplayNameForStatus(*pItemDefinition) + " spell");
                result.alreadyKnown = true;
                return result;
            }

            pTargetMember->learnSpell(*spellId);
            result.handled = true;
            result.consumed = true;
            result.spellId = *spellId;
            result.speechId = SpeechId::LearnSpell;
            return result;
        }

        case InventoryItemUseAction::LearnSkill:
        {
            const std::vector<std::string> targetSkills = pipeSeparatedSkills(pItemDefinition->useTarget);

            if (targetSkills.empty())
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
            }

            std::vector<std::string> learnableSkills;
            bool hasAlreadyKnownSkill = false;
            const ClassSkillTable *pClassSkillTable = party.classSkillTable();

            for (const std::string &skillName : targetSkills)
            {
                const bool classCanLearn = pClassSkillTable != nullptr
                    && pClassSkillTable->getEffectiveCap(
                        pTargetMember->className,
                        pTargetMember->raceId,
                        skillName) != SkillMastery::None;

                if (!classCanLearn)
                {
                    continue;
                }

                if (pTargetMember->hasSkill(skillName))
                {
                    hasAlreadyKnownSkill = true;
                    continue;
                }

                if (party.canMemberLearnSkill(targetMemberIndex, skillName))
                {
                    learnableSkills.push_back(skillName);
                }
            }

            if (hasAlreadyKnownSkill)
            {
                result = makeFailure(
                    result.action,
                    "You already know one or more skills in " + itemDisplayNameForStatus(*pItemDefinition));
                result.alreadyKnown = true;
                return result;
            }

            if (learnableSkills.size() != targetSkills.size())
            {
                result = makeFailure(
                    result.action,
                    "This character cannot learn the skills in " + itemDisplayNameForStatus(*pItemDefinition));
                return result;
            }

            for (const std::string &skillName : learnableSkills)
            {
                if (!party.learnMemberSkill(targetMemberIndex, skillName))
                {
                    return makeFailure(result.action, "The skill could not be learned");
                }
            }

            result.handled = true;
            result.consumed = true;
            result.learnedSkills = learnableSkills;
            result.statusText = learnableSkills.size() == 1
                ? "Learned " + displaySkillName(learnableSkills.front())
                : "Learned the skills in " + itemDisplayNameForStatus(*pItemDefinition);
            return result;
        }

        case InventoryItemUseAction::ConsumePotion:
        {
            const PotionDefinition *pPotion = pPotionSettingTable != nullptr
                ? pPotionSettingTable->effects().find(item.objectDescriptionId)
                : nullptr;

            if (pPotion == nullptr || pPotion->effects.empty())
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition), SpeechId::PotionFail);
            }

            const PotionEffectTable &effects = pPotionSettingTable->effects();
            int potionPower = std::max(1, static_cast<int>(item.standardEnchantPower));

            if (effects.powerCap() > 0)
            {
                potionPower = std::min(potionPower, effects.powerCap());
            }

            if (potionPower < pPotion->minimumPower)
            {
                return makeFailure(result.action, "This potion has not enough power", SpeechId::PotionFail);
            }

            // A drink needs a ready member, who pays its recovery (the active member in Standard, as in the original
            // games; MAW's drinker, near monsters only, AL:86-110); nobody ready, no drink.
            std::optional<size_t> recoveryPayer;

            if (effects.combatRecoveryTicks() > 0.0f)
            {
                recoveryPayer =
                    potionRecoveryPayer(party, targetMemberIndex, effects.combatRecoveryActiveMemberPays());

                if (!recoveryPayer)
                {
                    return makeFailure(result.action, "Player must be active to consume the potion");
                }

                if (effects.combatRecoveryOnlyNearEnemies() && !context.enemiesNear)
                {
                    recoveryPayer.reset();
                }
            }

            const PotionDrinkOutcome outcome = applyPotionEffects(
                party,
                targetMemberIndex,
                *pTargetMember,
                *pPotion,
                potionDurationSeconds(party, effects, potionPower),
                potionPower,
                gameRulesFor(&party).potions);

            if (outcome == PotionDrinkOutcome::NoBenefit)
            {
                const std::optional<std::string> text = gameRulesFor(&party).potions.noBenefitText();
                return makeFailure(
                    result.action, text ? *text : itemCannotBeUsedStatusText(*pItemDefinition), SpeechId::PotionFail);
            }

            if (recoveryPayer)
            {
                party.applyRecoveryToMember(
                    *recoveryPayer, ticksToRecoverySeconds(static_cast<int>(effects.combatRecoveryTicks())));
            }

            // A bottle of several drinks keeps its uses in its charges, 0 meaning a full bottle. A potion of one drink
            // is gone after it, whatever charges a mix carried over from a bottle of several (audit ALC-5).
            const int usesBefore = pPotion->charges <= 1 ? 1
                : item.currentCharges > 0                ? static_cast<int>(item.currentCharges)
                                                         : pPotion->charges;
            result.handled = true;
            result.consumed = usesBefore <= 1;

            if (!result.consumed)
            {
                result.potionUsesLeft = static_cast<uint32_t>(usesBefore - 1);
            }

            return result;
        }

        case InventoryItemUseAction::ReadMessageScroll:
        {
            const ReadableScrollEntry *pEntry =
                pReadableScrollTable != nullptr ? pReadableScrollTable->get(item.objectDescriptionId) : nullptr;

            if (pEntry == nullptr || pEntry->text.empty())
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
            }

            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            result.handled = true;
            result.readableTitle = pItemDefinition->name.empty() ? pEntry->itemName : pItemDefinition->name;
            result.readableBody = pEntry->text;
            return result;
        }

        case InventoryItemUseAction::UseHorseshoe:
        {
            pTargetMember->skillPoints += 2;
            result.handled = true;
            result.consumed = true;
            result.statusText = "+2 Skill Points!";
            result.soundId = SoundId::Quest;
            result.speechId = SpeechId::QuestGot;
            return result;
        }

        case InventoryItemUseAction::GrantTechPoints:
        {
            const uint32_t techPoints = static_cast<uint32_t>(std::max(1, pItemDefinition->varA));
            pTargetMember->techPoints += techPoints;
            result.handled = true;
            result.consumed = true;
            result.statusText = "+" + std::to_string(techPoints) + " Tech Points!";
            result.soundId = SoundId::Quest;
            result.speechId = SpeechId::QuestGot;
            return result;
        }

        case InventoryItemUseAction::UseShieldCell:
        {
            result.handled = true;
            result.consumed = party.chargePersonalShield(targetMemberIndex);
            result.statusText = result.consumed ? "Shield charged" : "";
            result.soundId = result.consumed ? SoundId::Drink : SoundId::Error;
            return result;
        }

        case InventoryItemUseAction::UseShieldBurst:
        {
            result.handled = true;
            result.consumed = party.burstPersonalShields();
            result.statusText = result.consumed ? "Shields charged" : "No shields to charge";
            result.soundId = result.consumed ? SoundId::Drink : SoundId::Error;
            return result;
        }

        case InventoryItemUseAction::UseStim:
        {
            if (pTargetMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead))
                || pTargetMember->conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            const int percent = pItemDefinition->varA > 0 ? pItemDefinition->varA : 30;
            party.healMember(targetMemberIndex,
                std::max(1, party.member(targetMemberIndex)->maxHealth * percent / 100));
            pTargetMember->conditions.reset(static_cast<size_t>(CharacterCondition::Weak));
            result.handled = true;
            result.consumed = true;
            result.soundId = SoundId::Drink;
            return result;
        }

        case InventoryItemUseAction::PlaceBreachCharge:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            result.handled = true;
            result.consumed = true;
            result.statusText = "The charge blows!";
            return result;
        }

        case InventoryItemUseAction::ThrowEmpGrenade:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            result.handled = true;
            result.consumed = true;
            result.statusText = "EMP!";
            return result;
        }

        case InventoryItemUseAction::UseGenieLamp:
        {
            result.handled = true;
            result.consumed = true;
            result.statusText = applyGenieLampReward(party, *pTargetMember, targetMemberIndex, context.gameMinutes);
            result.soundId = SoundId::Chimes;
            result.speechId = SpeechId::QuestGot;

            const int dayOfMonth = dayOfMonthFromGameMinutes(context.gameMinutes);

            if (dayOfMonth == 6 || dayOfMonth == 20)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Eradicated, context.gameMinutes);
                result.soundId = SoundId::Gong;
            }
            else if (dayOfMonth == 12 || dayOfMonth == 26)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Dead, context.gameMinutes);
                result.soundId = SoundId::Gong;
            }
            else if (dayOfMonth == 4 || dayOfMonth == 25)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Petrified, context.gameMinutes);
                result.soundId = SoundId::Gong;
            }

            return result;
        }

        case InventoryItemUseAction::UseDeckOfFate:
        {
            result.handled = true;
            result.consumed = true;
            result.statusText = applyDeckOfFateReward(*pTargetMember, context.gameMinutes);
            return result;
        }

        case InventoryItemUseAction::EatFoodItem:
        {
            // An eatFood item (Hesper's rations) adds its VarA in food; MM's food items one.
            party.addFood(lowerAscii(pItemDefinition->useAction) == "eatfood" ? std::max(1, pItemDefinition->varA) : 1);
            result.handled = true;
            result.consumed = true;
            result.soundId = SoundId::Eat;
            return result;
        }

        case InventoryItemUseAction::PlayInstrument:
        {
            result.handled = true;
            result.soundId = instrumentSoundId(*pItemDefinition);
            return result;
        }

        case InventoryItemUseAction::UseTempleInABottle:
        {
            result.handled = true;
            return result;
        }

        case InventoryItemUseAction::UseReagent:
        {
            return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
        }

        case InventoryItemUseAction::UseConnectorStone:
        {
            result.handled = true;
            return result;
        }

        case InventoryItemUseAction::Equip:
        case InventoryItemUseAction::None:
        default:
        {
            return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
        }
    }
}

std::optional<uint32_t> InventoryItemUseRuntime::scrollSpellId(const ItemDefinition &itemDefinition)
{
    return tryParseSpellId(itemDefinition);
}

PotionPreview InventoryItemUseRuntime::previewPotion(
    const Party &party,
    size_t memberIndex,
    const InventoryItem &item,
    const MergedPotionSettingTable &potionSettingTable)
{
    PotionPreview preview;
    const Character *pMember = party.member(memberIndex);
    const PotionDefinition *pPotion = potionSettingTable.effects().find(item.objectDescriptionId);

    if (pMember == nullptr || pPotion == nullptr || pPotion->effects.empty())
    {
        return preview;
    }

    preview.known = true;
    const PotionEffectTable &effects = potionSettingTable.effects();
    int power = std::max(1, static_cast<int>(item.standardEnchantPower));

    if (effects.powerCap() > 0)
    {
        power = std::min(power, effects.powerCap());
    }

    const PotionRules &potionRules = gameRulesFor(&party).potions;
    const auto addCure = [&preview, pMember](CharacterCondition condition)
    {
        if (pMember->conditions.test(static_cast<size_t>(condition))
            && std::find(preview.cures.begin(), preview.cures.end(), condition) == preview.cures.end())
        {
            preview.cures.push_back(condition);
        }
    };

    for (const PotionEffect &effect : pPotion->effects)
    {
        if (effect.limit == PotionLimit::BestStep)
        {
            preview.otherEffects = true;
            continue;
        }

        const int amount = effect.amount.evaluate(power, potionRules.estimatedPool(effect.amount.pool, power));

        switch (effect.kind)
        {
            case PotionEffectKind::Restore:
                if (effect.pool == PotionPool::HitPoints)
                {
                    // As Party::healMember: up to the reachable maximum, nothing for the dead.
                    const bool dead = pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead))
                        || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));

                    if (!dead && amount > 0)
                    {
                        const int cap = std::max(pMember->health, party.reachableMaximumHealth(memberIndex));
                        preview.healthBefore = pMember->health;
                        preview.healthMaximum = Party::effectiveMaximumHealth(*pMember);
                        preview.healthGain += std::max(0, std::min(pMember->health + amount, cap) - pMember->health);
                    }
                }
                else
                {
                    const int maximum = maxSpellPointsForMember(*pMember);
                    preview.spellPointsBefore = pMember->spellPoints;
                    preview.spellPointsMaximum = maximum;
                    preview.spellPointGain +=
                        std::max(0, std::clamp(pMember->spellPoints + amount, 0, maximum) - pMember->spellPoints);
                }
                break;
            case PotionEffectKind::Cure:
                for (CharacterCondition condition : effect.conditions)
                {
                    addCure(condition);
                }
                break;
            case PotionEffectKind::CureAllRestorable:
                for (CharacterCondition condition : RestorableConditions)
                {
                    addCure(condition);
                }
                break;
            default:
                preview.otherEffects = true;
                break;
        }
    }

    return preview;
}

bool InventoryItemUseRuntime::drinkRecoveryApplies(const MergedPotionSettingTable *pPotionSettingTable)
{
    return pPotionSettingTable != nullptr && pPotionSettingTable->effects().combatRecoveryTicks() > 0.0f;
}

std::optional<size_t> InventoryItemUseRuntime::drinkRecoveryPayer(
    const MergedPotionSettingTable &potionSettingTable,
    const Party &party,
    size_t drinkerIndex)
{
    return potionRecoveryPayer(
        party, drinkerIndex, potionSettingTable.effects().combatRecoveryActiveMemberPays());
}
}
