#include "game/MasteryTeacherDialog.h"

#include "game/NpcDialogTable.h"
#include "game/Party.h"

#include <array>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t FirstMasteryTeacherTopicId = 300;
constexpr uint32_t LastMasteryTeacherTopicId = 416;

const std::array<std::string, 39> MasteryTeacherSkillMap = {
    "Staff",
    "Sword",
    "Dagger",
    "Axe",
    "Spear",
    "Bow",
    "Mace",
    "Blaster",
    "Shield",
    "LeatherArmor",
    "ChainArmor",
    "PlateArmor",
    "FireMagic",
    "AirMagic",
    "WaterMagic",
    "EarthMagic",
    "SpiritMagic",
    "MindMagic",
    "BodyMagic",
    "LightMagic",
    "DarkMagic",
    "DarkElfAbility",
    "VampireAbility",
    "DragonAbility",
    "IdentifyItem",
    "Merchant",
    "RepairItem",
    "Bodybuilding",
    "Meditation",
    "Perception",
    "Regeneration",
    "DisarmTraps",
    "Dodging",
    "Unarmed",
    "IdentifyMonster",
    "Armsmaster",
    "Stealing",
    "Alchemy",
    "Learning",
};

std::string npcTextOrFallback(const NpcDialogTable &npcDialogTable, uint32_t textId, const std::string &fallback)
{
    const std::optional<std::string> text = npcDialogTable.getText(textId);

    if (text && !text->empty())
    {
        return *text;
    }

    return fallback;
}

bool tryDecodeMasteryTeacherTopic(
    uint32_t topicId,
    std::string &skillName,
    SkillMastery &targetMastery
)
{
    if (!isMasteryTeacherTopic(topicId))
    {
        return false;
    }

    const uint32_t zeroBased = topicId - FirstMasteryTeacherTopicId;
    const uint32_t skillIndex = zeroBased / 3;

    if (skillIndex >= MasteryTeacherSkillMap.size())
    {
        return false;
    }

    skillName = MasteryTeacherSkillMap[skillIndex];
    targetMastery = static_cast<SkillMastery>((zeroBased % 3) + 2);
    return true;
}

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

    if (targetMastery == SkillMastery::Expert)
    {
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

bool meetsMasteryRequirements(
    const Character &character,
    const std::string &skillName,
    SkillMastery targetMastery
)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    if (targetMastery == SkillMastery::Expert)
    {
        return pSkill->level >= 4;
    }

    if (targetMastery == SkillMastery::Master)
    {
        if (pSkill->level < 7 || pSkill->mastery != SkillMastery::Expert)
        {
            return false;
        }

        if (skillName == "Merchant")
        {
            return character.personality >= 50;
        }

        if (skillName == "Bodybuilding")
        {
            return character.endurance >= 50;
        }

        if (skillName == "Learning")
        {
            return character.intellect >= 50;
        }

        return true;
    }

    if (targetMastery == SkillMastery::Grandmaster)
    {
        if (pSkill->level < 10 || pSkill->mastery != SkillMastery::Master)
        {
            return false;
        }

        if (skillName == "Dodging")
        {
            const CharacterSkill *pUnarmed = character.findSkill("Unarmed");
            return pUnarmed != nullptr && pUnarmed->level >= 10;
        }

        if (skillName == "Unarmed")
        {
            const CharacterSkill *pDodging = character.findSkill("Dodging");
            return pDodging != nullptr && pDodging->level >= 10;
        }

        return true;
    }

    return false;
}
}

bool isMasteryTeacherTopic(uint32_t topicId)
{
    return topicId >= FirstMasteryTeacherTopicId && topicId <= LastMasteryTeacherTopicId;
}

std::optional<MasteryTeacherEvaluation> evaluateMasteryTeacherTopic(
    uint32_t topicId,
    const Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable
)
{
    const Character *pCharacter = party.activeMember();

    if (pCharacter == nullptr)
    {
        return std::nullopt;
    }

    MasteryTeacherEvaluation evaluation = {};

    if (!tryDecodeMasteryTeacherTopic(topicId, evaluation.skillName, evaluation.targetMastery))
    {
        return std::nullopt;
    }

    evaluation.cost = masteryTeacherCost(evaluation.skillName, evaluation.targetMastery);

    const SkillMastery classCap = classSkillTable.getClassCap(pCharacter->className, evaluation.skillName);

    if (classCap < evaluation.targetMastery)
    {
        const std::optional<std::string> nextPromotion = nextPromotionClassName(pCharacter->className);

        if (nextPromotion
            && classSkillTable.getClassCap(*nextPromotion, evaluation.skillName) >= evaluation.targetMastery)
        {
            evaluation.displayText =
                "You have to be promoted to " + displayClassName(*nextPromotion) + " to learn this skill.";
            return evaluation;
        }

        evaluation.displayText =
            "This skill level can not be learned by the " + displayClassName(pCharacter->className) + " class.";
        return evaluation;
    }

    if (!pCharacter->hasSkill(evaluation.skillName))
    {
        evaluation.displayText = npcTextOrFallback(npcDialogTable, 132, "This character does not know that skill.");
        return evaluation;
    }

    const CharacterSkill *pSkill = pCharacter->findSkill(evaluation.skillName);

    if (pSkill != nullptr && pSkill->mastery >= evaluation.targetMastery)
    {
        evaluation.displayText = npcTextOrFallback(
            npcDialogTable,
            alreadyHasTextId(evaluation.targetMastery),
            "This character already knows that mastery."
        );
        return evaluation;
    }

    if (!meetsMasteryRequirements(*pCharacter, evaluation.skillName, evaluation.targetMastery))
    {
        evaluation.displayText = npcTextOrFallback(
            npcDialogTable,
            128,
            "The requirements for this training are unmet."
        );
        return evaluation;
    }

    if (party.gold() < evaluation.cost)
    {
        evaluation.displayText = npcTextOrFallback(npcDialogTable, 125, "You do not have enough gold.");
        return evaluation;
    }

    evaluation.approved = true;
    evaluation.displayText =
        "Become " + masteryDisplayName(evaluation.targetMastery)
        + " in " + displaySkillName(evaluation.skillName)
        + " for " + std::to_string(evaluation.cost) + " gold";
    return evaluation;
}

bool applyMasteryTeacherTopic(
    uint32_t topicId,
    Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    std::string &message
)
{
    const std::optional<MasteryTeacherEvaluation> evaluation =
        evaluateMasteryTeacherTopic(topicId, party, classSkillTable, npcDialogTable);

    if (!evaluation || !evaluation->approved)
    {
        return false;
    }

    Character *pCharacter = party.activeMember();

    if (pCharacter == nullptr || !pCharacter->setSkillMastery(evaluation->skillName, evaluation->targetMastery))
    {
        return false;
    }

    party.addGold(-evaluation->cost);
    message =
        pCharacter->name + " is now a "
        + masteryDisplayName(evaluation->targetMastery)
        + " in " + displaySkillName(evaluation->skillName) + ".";
    return true;
}
}
