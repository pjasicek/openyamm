#include "game/gameplay/MasteryTeacherDialog.h"
#include "engine/Localization.h"

#include "game/gameplay/GameMechanics.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string npcTextOrFallback(const NpcDialogTable &npcDialogTable, uint32_t textId, const std::string &fallback)
{
    const std::optional<std::string> text = npcDialogTable.getText(textId);

    if (text && !text->empty())
    {
        return Engine::localize(*text);
    }

    return fallback;
}

std::string trimCopy(const std::string &text)
{
    size_t start = 0;
    size_t end = text.size();

    while (start < end && std::isspace(static_cast<unsigned char>(text[start])) != 0)
    {
        ++start;
    }

    while (end > start && std::isspace(static_cast<unsigned char>(text[end - 1])) != 0)
    {
        --end;
    }

    return text.substr(start, end - start);
}


SkillMastery masteryForMergedTeacherTopic(uint32_t mastery)
{
    switch (mastery)
    {
        case 1:
            return SkillMastery::Expert;
        case 2:
            return SkillMastery::Master;
        case 3:
            return SkillMastery::Grandmaster;
        default:
            return SkillMastery::None;
    }
}
}

std::optional<MasteryTeacherTopicDefinition> resolveMasteryTeacherTopic(
    uint32_t topicId,
    const MergedTeacherTopicTable *pTeacherTopicTable
)
{
    MasteryTeacherTopicDefinition definition = {};

    const MergedTeacherTopicEntry *pTeacherTopic =
        pTeacherTopicTable != nullptr ? pTeacherTopicTable->get(topicId) : nullptr;

    if (pTeacherTopic != nullptr)
    {
        definition.topicId = pTeacherTopic->topicId;
        definition.skillId = pTeacherTopic->skillId;
        definition.masteryRank = pTeacherTopic->mastery;
        definition.textId = pTeacherTopic->textId;
        definition.requiredGold = pTeacherTopic->requiredGold;
        definition.requiredSkill = pTeacherTopic->requiredSkill;
    }
    else if (topicId >= 300 && topicId <= 416)
    {
        // MMerge keeps these original MM8 topic ids active even when Teacher topics.txt only extends the table.
        definition.topicId = topicId;
        definition.skillId = (topicId - 300) / 3;
        definition.masteryRank = ((topicId - 300) % 3) + 1;
        definition.textId = topicId;
    }
    else
    {
        return std::nullopt;
    }

    const std::optional<std::string> skillName = skillNameForSkillId(definition.skillId);
    if (!skillName.has_value())
    {
        return std::nullopt;
    }

    definition.skillName = *skillName;
    definition.targetMastery = masteryForMergedTeacherTopic(definition.masteryRank);

    if (definition.skillName.empty() || definition.targetMastery == SkillMastery::None)
    {
        return std::nullopt;
    }

    return definition;
}

bool isMasteryTeacherTopic(
    uint32_t topicId,
    const MergedTeacherTopicTable *pTeacherTopicTable
)
{
    return resolveMasteryTeacherTopic(topicId, pTeacherTopicTable).has_value();
}

namespace
{
uint32_t alreadyHasTextId(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert:
            return 129;
        case SkillMastery::Master:
            return 130;
        case SkillMastery::Grandmaster:
            return 131;
        default:
            return 128;
    }
}

int masteryTeacherCost(const std::string &skillName, SkillMastery targetMastery)
{
    const std::string canonicalSkill = canonicalSkillName(skillName);

    // Technology lessons default to Hesper's prices; a topic's Req. Gold overrides them.
    if (isTechnologySkill(canonicalSkill))
    {
        switch (targetMastery)
        {
            case SkillMastery::Expert:
                return 15000;
            case SkillMastery::Master:
                return 40000;
            case SkillMastery::Grandmaster:
                return 100000;
            default:
                return 0;
        }
    }

    if (targetMastery == SkillMastery::Expert)
    {
        if (canonicalSkill == "Blaster")
        {
            return 2000;
        }

        if (canonicalSkill == "Shield"
            || canonicalSkill == "LeatherArmor"
            || canonicalSkill == "ChainArmor"
            || canonicalSkill == "PlateArmor"
            || canonicalSkill == "FireMagic"
            || canonicalSkill == "AirMagic"
            || canonicalSkill == "WaterMagic"
            || canonicalSkill == "EarthMagic"
            || canonicalSkill == "SpiritMagic"
            || canonicalSkill == "MindMagic"
            || canonicalSkill == "BodyMagic")
        {
            return 1000;
        }

        if (canonicalSkill == "Staff"
            || canonicalSkill == "Sword"
            || canonicalSkill == "Dagger"
            || canonicalSkill == "Axe"
            || canonicalSkill == "Spear"
            || canonicalSkill == "Bow"
            || canonicalSkill == "Throwing"
            || canonicalSkill == "Mace"
            || canonicalSkill == "LightMagic"
            || canonicalSkill == "DarkMagic"
            || canonicalSkill == "Merchant"
            || canonicalSkill == "Dodging"
            || canonicalSkill == "Unarmed"
            || canonicalSkill == "Armsmaster"
            || canonicalSkill == "Learning")
        {
            return 2000;
        }

        if (canonicalSkill == "IdentifyItem"
            || canonicalSkill == "RepairItem"
            || canonicalSkill == "Bodybuilding"
            || canonicalSkill == "Meditation"
            || canonicalSkill == "Perception"
            || canonicalSkill == "Regeneration"
            || canonicalSkill == "DisarmTraps"
            || canonicalSkill == "IdentifyMonster"
            || canonicalSkill == "Stealing"
            || canonicalSkill == "Alchemy"
            || canonicalSkill == "DarkElfAbility"
            || canonicalSkill == "VampireAbility"
            || canonicalSkill == "DragonAbility")
        {
            return 500;
        }
    }

    if (targetMastery == SkillMastery::Master)
    {
        if (canonicalSkill == "Blaster")
        {
            return 5000;
        }

        if (canonicalSkill == "Shield"
            || canonicalSkill == "LeatherArmor"
            || canonicalSkill == "ChainArmor"
            || canonicalSkill == "PlateArmor")
        {
            return 3000;
        }

        if (canonicalSkill == "FireMagic"
            || canonicalSkill == "AirMagic"
            || canonicalSkill == "WaterMagic"
            || canonicalSkill == "EarthMagic"
            || canonicalSkill == "SpiritMagic"
            || canonicalSkill == "MindMagic"
            || canonicalSkill == "BodyMagic")
        {
            return 4000;
        }

        if (canonicalSkill == "Staff"
            || canonicalSkill == "Sword"
            || canonicalSkill == "Dagger"
            || canonicalSkill == "Axe"
            || canonicalSkill == "Spear"
            || canonicalSkill == "Bow"
            || canonicalSkill == "Throwing"
            || canonicalSkill == "Mace"
            || canonicalSkill == "LightMagic"
            || canonicalSkill == "DarkMagic"
            || canonicalSkill == "Merchant"
            || canonicalSkill == "Dodging"
            || canonicalSkill == "Unarmed"
            || canonicalSkill == "Armsmaster"
            || canonicalSkill == "Learning")
        {
            return 5000;
        }

        if (canonicalSkill == "IdentifyItem"
            || canonicalSkill == "RepairItem"
            || canonicalSkill == "Bodybuilding"
            || canonicalSkill == "Meditation"
            || canonicalSkill == "Perception"
            || canonicalSkill == "Regeneration"
            || canonicalSkill == "DisarmTraps"
            || canonicalSkill == "IdentifyMonster"
            || canonicalSkill == "Stealing"
            || canonicalSkill == "Alchemy"
            || canonicalSkill == "DarkElfAbility"
            || canonicalSkill == "VampireAbility"
            || canonicalSkill == "DragonAbility")
        {
            return 2500;
        }
    }

    if (targetMastery == SkillMastery::Grandmaster)
    {
        if (canonicalSkill == "Blaster")
        {
            return 10000;
        }

        if (canonicalSkill == "Shield"
            || canonicalSkill == "LeatherArmor"
            || canonicalSkill == "ChainArmor"
            || canonicalSkill == "PlateArmor")
        {
            return 7000;
        }

        if (canonicalSkill == "Staff"
            || canonicalSkill == "Sword"
            || canonicalSkill == "Dagger"
            || canonicalSkill == "Axe"
            || canonicalSkill == "Spear"
            || canonicalSkill == "Bow"
            || canonicalSkill == "Throwing"
            || canonicalSkill == "Mace"
            || canonicalSkill == "FireMagic"
            || canonicalSkill == "AirMagic"
            || canonicalSkill == "WaterMagic"
            || canonicalSkill == "EarthMagic"
            || canonicalSkill == "SpiritMagic"
            || canonicalSkill == "MindMagic"
            || canonicalSkill == "BodyMagic"
            || canonicalSkill == "LightMagic"
            || canonicalSkill == "DarkMagic"
            || canonicalSkill == "Merchant"
            || canonicalSkill == "Dodging"
            || canonicalSkill == "Unarmed"
            || canonicalSkill == "Armsmaster"
            || canonicalSkill == "Learning")
        {
            return 8000;
        }

        if (canonicalSkill == "IdentifyItem"
            || canonicalSkill == "RepairItem"
            || canonicalSkill == "Bodybuilding"
            || canonicalSkill == "Meditation"
            || canonicalSkill == "Perception"
            || canonicalSkill == "Regeneration"
            || canonicalSkill == "DisarmTraps"
            || canonicalSkill == "IdentifyMonster"
            || canonicalSkill == "Stealing"
            || canonicalSkill == "Alchemy"
            || canonicalSkill == "DarkElfAbility"
            || canonicalSkill == "VampireAbility"
            || canonicalSkill == "DragonAbility")
        {
            return 6000;
        }
    }

    return 0;
}

enum class MasteryRequirementFailure
{
    None,
    General,
    IntellectTooLow,
    PersonalityTooLow,
    EnduranceTooLow,
};

MasteryRequirementFailure masteryRequirementFailure(
    const Character &character,
    const Party &party,
    const std::string &skillName,
    SkillMastery targetMastery,
    uint32_t requiredSkillLevel
)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);

    if (pSkill == nullptr)
    {
        return MasteryRequirementFailure::General;
    }

    if (requiredSkillLevel != 0 && pSkill->level < requiredSkillLevel)
    {
        return MasteryRequirementFailure::General;
    }

    if (pSkill->level < party.rules().skills.masteryRequiredLevel(skillName, targetMastery))
    {
        return MasteryRequirementFailure::General;
    }

    if (targetMastery == SkillMastery::Expert)
    {
        return MasteryRequirementFailure::None;
    }

    if (targetMastery == SkillMastery::Master)
    {
        if (pSkill->mastery != SkillMastery::Expert)
        {
            return MasteryRequirementFailure::General;
        }

        if (skillName == "Merchant")
        {
            const int personality = GameMechanics::resolveCharacterDisplayedBasePrimaryStat(
                character,
                0x22,
                party.itemTable(),
                party.standardItemEnchantTable(),
                party.specialItemEnchantTable());
            return personality >= 50
                ? MasteryRequirementFailure::None
                : MasteryRequirementFailure::PersonalityTooLow;
        }

        if (skillName == "Bodybuilding")
        {
            const int endurance = GameMechanics::resolveCharacterDisplayedBasePrimaryStat(
                character,
                0x23,
                party.itemTable(),
                party.standardItemEnchantTable(),
                party.specialItemEnchantTable());
            return endurance >= 50
                ? MasteryRequirementFailure::None
                : MasteryRequirementFailure::EnduranceTooLow;
        }

        if (skillName == "Learning")
        {
            const int intellect = GameMechanics::resolveCharacterDisplayedBasePrimaryStat(
                character,
                0x21,
                party.itemTable(),
                party.standardItemEnchantTable(),
                party.specialItemEnchantTable());
            return intellect >= 50
                ? MasteryRequirementFailure::None
                : MasteryRequirementFailure::IntellectTooLow;
        }

        return MasteryRequirementFailure::None;
    }

    if (targetMastery == SkillMastery::Grandmaster)
    {
        if (pSkill->mastery != SkillMastery::Master)
        {
            return MasteryRequirementFailure::General;
        }

        if (skillName == "Dodging")
        {
            const CharacterSkill *pUnarmed = character.findSkill("Unarmed");
            return pUnarmed != nullptr && pUnarmed->level >= 10
                ? MasteryRequirementFailure::None
                : MasteryRequirementFailure::General;
        }

        if (skillName == "Unarmed")
        {
            const CharacterSkill *pDodging = character.findSkill("Dodging");
            return pDodging != nullptr && pDodging->level >= 10
                ? MasteryRequirementFailure::None
                : MasteryRequirementFailure::General;
        }

        return MasteryRequirementFailure::None;
    }

    return MasteryRequirementFailure::General;
}

std::string joinPromotionClassNames(const std::vector<std::string> &classNames)
{
    std::string result;

    for (size_t index = 0; index < classNames.size(); ++index)
    {
        if (!result.empty())
        {
            result += index + 1 == classNames.size() ? Engine::tr(" or ") : Engine::tr(", ");
        }

        result += Engine::localize(displayClassName(classNames[index]), "class");
    }

    return result;
}
}

std::optional<MasteryTeacherEvaluation> evaluateMasteryTeacherTopic(
    uint32_t topicId,
    const Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    const MergedTeacherTopicTable *pTeacherTopicTable
)
{
    const std::optional<MasteryTeacherTopicDefinition> teacherTopic =
        resolveMasteryTeacherTopic(topicId, pTeacherTopicTable);

    if (!teacherTopic.has_value())
    {
        return std::nullopt;
    }

    const SkillMasteryTrainingRequest request = {
        .skillName = teacherTopic->skillName,
        .targetMastery = teacherTopic->targetMastery,
        .requiredGold = teacherTopic->requiredGold,
        .requiredSkill = teacherTopic->requiredSkill,
    };
    return evaluateSkillMasteryTraining(request, party, party.activeMemberIndex(), classSkillTable, npcDialogTable);
}

std::optional<MasteryTeacherEvaluation> evaluateSkillMasteryTraining(
    const SkillMasteryTrainingRequest &request,
    const Party &party,
    size_t memberIndex,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable
)
{
    const Character *pCharacter = party.member(memberIndex);

    if (pCharacter == nullptr)
    {
        return std::nullopt;
    }

    MasteryTeacherEvaluation evaluation = {};
    evaluation.skillName = canonicalSkillName(request.skillName);
    evaluation.targetMastery = request.targetMastery;
    evaluation.cost = static_cast<int>(request.requiredGold);

    if (evaluation.skillName.empty() || evaluation.targetMastery == SkillMastery::None)
    {
        return std::nullopt;
    }

    if (evaluation.cost == 0)
    {
        evaluation.cost = masteryTeacherCost(evaluation.skillName, evaluation.targetMastery);
    }

    evaluation.cost = party.rules().skills.masteryTeacherCost(
        *pCharacter, evaluation.skillName, evaluation.targetMastery, evaluation.cost);

    const SkillMastery classCap =
        classSkillTable.getEffectiveCap(pCharacter->className, pCharacter->raceId, evaluation.skillName);

    if (classCap < evaluation.targetMastery)
    {
        const std::vector<std::string> qualifyingPromotions =
            classSkillTable.getClosestPromotionClassesWithEffectiveCap(
                pCharacter->className,
                pCharacter->raceId,
                evaluation.skillName,
                evaluation.targetMastery);

        if (!qualifyingPromotions.empty())
        {
            evaluation.displayText =
                Engine::tr("You have to be promoted to {classes} to learn this skill.",
                           {{"classes", joinPromotionClassNames(qualifyingPromotions)}});
            return evaluation;
        }

        evaluation.displayText =
            Engine::tr("This skill level can not be learned by the {class} class.",
                {{"class", Engine::localize(displayClassName(pCharacter->className), "class")}});
        return evaluation;
    }

    if (!pCharacter->hasSkill(evaluation.skillName))
    {
        evaluation.displayText =
            npcTextOrFallback(npcDialogTable, 132, Engine::tr("This character does not know that skill."));
        return evaluation;
    }

    const CharacterSkill *pSkill = pCharacter->findSkill(evaluation.skillName);

    if (pSkill != nullptr && pSkill->mastery >= evaluation.targetMastery)
    {
        evaluation.displayText = npcTextOrFallback(
            npcDialogTable,
            alreadyHasTextId(evaluation.targetMastery),
            Engine::tr("This character already knows that mastery.")
        );
        return evaluation;
    }

    const MasteryRequirementFailure requirementFailure = masteryRequirementFailure(
        *pCharacter,
        party,
        evaluation.skillName,
        evaluation.targetMastery,
        request.requiredSkill);

    if (requirementFailure != MasteryRequirementFailure::None)
    {
        if (requirementFailure == MasteryRequirementFailure::IntellectTooLow)
        {
            evaluation.displayText = Engine::tr("You must have at least 50 base Intellect to learn Master Learning.");
        }
        else if (requirementFailure == MasteryRequirementFailure::PersonalityTooLow)
        {
            evaluation.displayText = Engine::tr("You must have at least 50 base Personality to learn Master Merchant.");
        }
        else if (requirementFailure == MasteryRequirementFailure::EnduranceTooLow)
        {
            evaluation.displayText =
                Engine::tr("You must have at least 50 base Endurance to learn Master Bodybuilding.");
        }
        else
        {
            evaluation.displayText = npcTextOrFallback(
                npcDialogTable,
                128,
                Engine::tr("The requirements for this training are unmet.")
            );
        }
        return evaluation;
    }

    if (request.checkGold && party.gold() < evaluation.cost)
    {
        evaluation.displayText = npcTextOrFallback(npcDialogTable, 125, Engine::tr("You do not have enough gold."));
        return evaluation;
    }

    evaluation.approved = true;
    evaluation.displayText = Engine::tr(
        "Become {mastery} in {skill} for {price} gold",
        {{"mastery", Engine::localize(masteryDisplayName(evaluation.targetMastery), "mastery")},
         {"skill", Engine::localize(displaySkillName(evaluation.skillName), "skill")},
         {"price", evaluation.cost}});
    return evaluation;
}

bool applySkillMasteryTraining(
    const SkillMasteryTrainingRequest &request,
    Party &party,
    size_t memberIndex,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    std::string &message
)
{
    const std::optional<MasteryTeacherEvaluation> evaluation =
        evaluateSkillMasteryTraining(request, party, memberIndex, classSkillTable, npcDialogTable);

    if (!evaluation || !evaluation->approved)
    {
        return false;
    }

    Character *pCharacter = party.member(memberIndex);

    if (pCharacter == nullptr || !pCharacter->setSkillMastery(evaluation->skillName, evaluation->targetMastery))
    {
        return false;
    }

    party.addGold(-evaluation->cost, GoldReason::Guild);
    message = Engine::tr(
        "{name} is now a {mastery} in {skill}.",
        {{"name", pCharacter->name},
         {"mastery", Engine::localize(masteryDisplayName(evaluation->targetMastery), "mastery")},
         {"skill", Engine::localize(displaySkillName(evaluation->skillName), "skill")}});
    return true;
}

bool applyMasteryTeacherTopic(
    uint32_t topicId,
    Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    const MergedTeacherTopicTable *pTeacherTopicTable,
    std::string &message
)
{
    const std::optional<MasteryTeacherTopicDefinition> teacherTopic =
        resolveMasteryTeacherTopic(topicId, pTeacherTopicTable);

    if (!teacherTopic)
    {
        return false;
    }

    const SkillMasteryTrainingRequest request = {
        .skillName = teacherTopic->skillName,
        .targetMastery = teacherTopic->targetMastery,
        .requiredGold = teacherTopic->requiredGold,
        .requiredSkill = teacherTopic->requiredSkill,
    };
    return applySkillMasteryTraining(
        request, party, party.activeMemberIndex(), classSkillTable, npcDialogTable, message);
}

int masteryTeacherStandardCost(const std::string &skillName, SkillMastery targetMastery)
{
    return masteryTeacherCost(skillName, targetMastery);
}
}
