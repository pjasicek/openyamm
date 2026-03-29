#include "game/PortraitEnums.h"

#include "game/StringUtils.h"

#include <array>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeToken(std::string_view value)
{
    std::string normalized;
    normalized.reserve(value.size());

    for (char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)))
        {
            normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
    }

    return normalized;
}

template <typename EnumType, size_t Count>
std::optional<EnumType> findEnumByName(
    const std::array<std::pair<std::string_view, EnumType>, Count> &entries,
    std::string_view name)
{
    const std::string normalizedName = normalizeToken(name);

    if (normalizedName.empty())
    {
        return std::nullopt;
    }

    for (const auto &[entryName, entryValue] : entries)
    {
        if (normalizeToken(entryName) == normalizedName)
        {
            return entryValue;
        }
    }

    return std::nullopt;
}
}

std::optional<PortraitId> portraitIdFromName(std::string_view name)
{
    static const std::array<std::pair<std::string_view, PortraitId>, 53> PortraitNames = {{
        {"Normal", PortraitId::Normal},
        {"Cursed", PortraitId::Cursed},
        {"Weak", PortraitId::Weak},
        {"Sleep", PortraitId::Sleep},
        {"Asleep", PortraitId::Sleep},
        {"Fear", PortraitId::Fear},
        {"Afraid", PortraitId::Fear},
        {"Drunk", PortraitId::Drunk},
        {"Insane", PortraitId::Insane},
        {"Poisoned", PortraitId::Poisoned},
        {"Diseased", PortraitId::Diseased},
        {"Disease", PortraitId::Diseased},
        {"Paralyzed", PortraitId::Paralyzed},
        {"Unconscious", PortraitId::Unconscious},
        {"Petrified", PortraitId::Petrified},
        {"Stoned", PortraitId::Petrified},
        {"Blink", PortraitId::Blink},
        {"Wink", PortraitId::Wink},
        {"MouthOpenRandom", PortraitId::MouthOpenRandom},
        {"PurseLipsRandom", PortraitId::PurseLipsRandom},
        {"LookUp", PortraitId::LookUp},
        {"LookRight", PortraitId::LookRight},
        {"LookLeft", PortraitId::LookLeft},
        {"LookDown", PortraitId::LookDown},
        {"Talk", PortraitId::Talk},
        {"MouthOpenWide", PortraitId::MouthOpenWide},
        {"MouthOpenA", PortraitId::MouthOpenA},
        {"MouthOpenO", PortraitId::MouthOpenO},
        {"No", PortraitId::No},
        {"Yes", PortraitId::Yes},
        {"PurseLips1", PortraitId::PurseLips1},
        {"PurseLips2", PortraitId::PurseLips2},
        {"PurseLips3", PortraitId::PurseLips3},
        {"AvoidDamage", PortraitId::AvoidDamage},
        {"DamageReceivedMinor", PortraitId::DamageReceivedMinor},
        {"DamageReceivedModerate", PortraitId::DamageReceivedModerate},
        {"DamageReceivedMajor", PortraitId::DamageReceivedMajor},
        {"DmgRecvdMinor", PortraitId::DamageReceivedMinor},
        {"DmgRecvdModerate", PortraitId::DamageReceivedModerate},
        {"DmgRecvdMajor", PortraitId::DamageReceivedMajor},
        {"Smile", PortraitId::Smile},
        {"WideSmile", PortraitId::WideSmile},
        {"Sad", PortraitId::Sad},
        {"CastSpell", PortraitId::CastSpell},
        {"Portrait41", PortraitId::Portrait41},
        {"Portrait42", PortraitId::Portrait42},
        {"Portrait43", PortraitId::Portrait43},
        {"Portrait44", PortraitId::Portrait44},
        {"Portrait45", PortraitId::Portrait45},
        {"Scared", PortraitId::Scared},
        {"WakeUp", PortraitId::WakeUp},
        {"Dead", PortraitId::Dead},
        {"Eradicated", PortraitId::Eradicated},
    }};

    return findEnumByName(PortraitNames, name);
}

std::optional<FaceAnimationId> faceAnimationIdFromName(std::string_view name)
{
    static const auto FaceAnimationNames = std::to_array<std::pair<std::string_view, FaceAnimationId>>({
        {"KillSmallEnemy", FaceAnimationId::KillSmallEnemy},
        {"KillBigEnemy", FaceAnimationId::KillBigEnemy},
        {"StoreClosed", FaceAnimationId::StoreClosed},
        {"DisarmTrap", FaceAnimationId::DisarmTrap},
        {"TrapExploded", FaceAnimationId::TrapExploded},
        {"AvoidDamage", FaceAnimationId::AvoidDamage},
        {"IdentifyUseless", FaceAnimationId::IdentifyUseless},
        {"IdentifyGreat", FaceAnimationId::IdentifyGreat},
        {"IdentifyFail", FaceAnimationId::IdentifyFail},
        {"RepairItem", FaceAnimationId::RepairItem},
        {"RepairFail", FaceAnimationId::RepairFail},
        {"SetQuickSpell", FaceAnimationId::SetQuickSpell},
        {"CantRestHere", FaceAnimationId::CantRestHere},
        {"SkillIncreased", FaceAnimationId::SkillIncreased},
        {"CantCarry", FaceAnimationId::CantCarry},
        {"MixPotion", FaceAnimationId::MixPotion},
        {"PotionExplode", FaceAnimationId::PotionExplode},
        {"DoorLocked", FaceAnimationId::DoorLocked},
        {"WontBudge", FaceAnimationId::WontBudge},
        {"CantLearnSpell", FaceAnimationId::CantLearnSpell},
        {"LearnSpell", FaceAnimationId::LearnSpell},
        {"Hello", FaceAnimationId::Hello},
        {"HelloNight", FaceAnimationId::HelloNight},
        {"Damaged", FaceAnimationId::Damaged},
        {"Weak", FaceAnimationId::Weak},
        {"Afraid", FaceAnimationId::Afraid},
        {"Poisoned", FaceAnimationId::Poisoned},
        {"Diseased", FaceAnimationId::Diseased},
        {"Insane", FaceAnimationId::Insane},
        {"Cursed", FaceAnimationId::Cursed},
        {"Drunk", FaceAnimationId::Drunk},
        {"Unconscious", FaceAnimationId::Unconscious},
        {"Death", FaceAnimationId::Death},
        {"Stoned", FaceAnimationId::Stoned},
        {"Eradicated", FaceAnimationId::Eradicated},
        {"DrinkPotion", FaceAnimationId::DrinkPotion},
        {"ReadScroll", FaceAnimationId::ReadScroll},
        {"NotEnoughGold", FaceAnimationId::NotEnoughGold},
        {"CantEquip", FaceAnimationId::CantEquip},
        {"ItemBrokenStolen", FaceAnimationId::ItemBrokenStolen},
        {"SpellPointsDrained", FaceAnimationId::SpellPointsDrained},
        {"Aged", FaceAnimationId::Aged},
        {"SpellFailed", FaceAnimationId::SpellFailed},
        {"DamagedParty", FaceAnimationId::DamagedParty},
        {"Tired", FaceAnimationId::Tired},
        {"EnterDungeon", FaceAnimationId::EnterDungeon},
        {"LeaveDungeon", FaceAnimationId::LeaveDungeon},
        {"AlmostDead", FaceAnimationId::AlmostDead},
        {"CastSpell", FaceAnimationId::CastSpell},
        {"Shoot", FaceAnimationId::Shoot},
        {"AttackHit", FaceAnimationId::AttackHit},
        {"AttackMiss", FaceAnimationId::AttackMiss},
        {"ShopIdentify", FaceAnimationId::ShopIdentify},
        {"ShopRepair", FaceAnimationId::ShopRepair},
        {"AlreadyIdentified", FaceAnimationId::AlreadyIdentified},
        {"ItemSold", FaceAnimationId::ItemSold},
        {"WrongShop", FaceAnimationId::WrongShop},
    });

    return findEnumByName(FaceAnimationNames, name);
}

std::optional<PortraitId> portraitIdForCondition(CharacterCondition condition)
{
    switch (condition)
    {
        case CharacterCondition::Cursed:
            return PortraitId::Cursed;

        case CharacterCondition::Weak:
            return PortraitId::Weak;

        case CharacterCondition::Asleep:
            return PortraitId::Sleep;

        case CharacterCondition::Fear:
            return PortraitId::Fear;

        case CharacterCondition::Drunk:
            return PortraitId::Drunk;

        case CharacterCondition::Insane:
            return PortraitId::Insane;

        case CharacterCondition::PoisonWeak:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::PoisonSevere:
            return PortraitId::Poisoned;

        case CharacterCondition::DiseaseWeak:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::DiseaseSevere:
            return PortraitId::Diseased;

        case CharacterCondition::Paralyzed:
            return PortraitId::Paralyzed;

        case CharacterCondition::Unconscious:
            return PortraitId::Unconscious;

        case CharacterCondition::Dead:
            return PortraitId::Dead;

        case CharacterCondition::Petrified:
            return PortraitId::Petrified;

        case CharacterCondition::Eradicated:
            return PortraitId::Eradicated;

        case CharacterCondition::Zombie:
        case CharacterCondition::Count:
            return std::nullopt;
    }

    return std::nullopt;
}

bool isConditionPortrait(PortraitId portraitId)
{
    return portraitId == PortraitId::Cursed
        || portraitId == PortraitId::Weak
        || portraitId == PortraitId::Sleep
        || portraitId == PortraitId::Fear
        || portraitId == PortraitId::Drunk
        || portraitId == PortraitId::Insane
        || portraitId == PortraitId::Poisoned
        || portraitId == PortraitId::Diseased
        || portraitId == PortraitId::Paralyzed
        || portraitId == PortraitId::Unconscious
        || portraitId == PortraitId::Petrified
        || portraitId == PortraitId::Dead
        || portraitId == PortraitId::Eradicated;
}

bool isDamagePortrait(PortraitId portraitId)
{
    return portraitId == PortraitId::DamageReceivedMinor
        || portraitId == PortraitId::DamageReceivedModerate
        || portraitId == PortraitId::DamageReceivedMajor;
}

std::string portraitIdName(PortraitId portraitId)
{
    switch (portraitId)
    {
        case PortraitId::Invalid:
            return "Invalid";
        case PortraitId::Normal:
            return "Normal";
        case PortraitId::Cursed:
            return "Cursed";
        case PortraitId::Weak:
            return "Weak";
        case PortraitId::Sleep:
            return "Sleep";
        case PortraitId::Fear:
            return "Fear";
        case PortraitId::Drunk:
            return "Drunk";
        case PortraitId::Insane:
            return "Insane";
        case PortraitId::Poisoned:
            return "Poisoned";
        case PortraitId::Diseased:
            return "Diseased";
        case PortraitId::Paralyzed:
            return "Paralyzed";
        case PortraitId::Unconscious:
            return "Unconscious";
        case PortraitId::Petrified:
            return "Petrified";
        case PortraitId::Blink:
            return "Blink";
        case PortraitId::Wink:
            return "Wink";
        case PortraitId::MouthOpenRandom:
            return "MouthOpenRandom";
        case PortraitId::PurseLipsRandom:
            return "PurseLipsRandom";
        case PortraitId::LookUp:
            return "LookUp";
        case PortraitId::LookRight:
            return "LookRight";
        case PortraitId::LookLeft:
            return "LookLeft";
        case PortraitId::LookDown:
            return "LookDown";
        case PortraitId::Talk:
            return "Talk";
        case PortraitId::MouthOpenWide:
            return "MouthOpenWide";
        case PortraitId::MouthOpenA:
            return "MouthOpenA";
        case PortraitId::MouthOpenO:
            return "MouthOpenO";
        case PortraitId::No:
            return "No";
        case PortraitId::Yes:
            return "Yes";
        case PortraitId::PurseLips1:
            return "PurseLips1";
        case PortraitId::PurseLips2:
            return "PurseLips2";
        case PortraitId::PurseLips3:
            return "PurseLips3";
        case PortraitId::AvoidDamage:
            return "AvoidDamage";
        case PortraitId::DamageReceivedMinor:
            return "DamageReceivedMinor";
        case PortraitId::DamageReceivedModerate:
            return "DamageReceivedModerate";
        case PortraitId::DamageReceivedMajor:
            return "DamageReceivedMajor";
        case PortraitId::Smile:
            return "Smile";
        case PortraitId::WideSmile:
            return "WideSmile";
        case PortraitId::Sad:
            return "Sad";
        case PortraitId::CastSpell:
            return "CastSpell";
        case PortraitId::Portrait41:
            return "Portrait41";
        case PortraitId::Portrait42:
            return "Portrait42";
        case PortraitId::Portrait43:
            return "Portrait43";
        case PortraitId::Portrait44:
            return "Portrait44";
        case PortraitId::Portrait45:
            return "Portrait45";
        case PortraitId::Scared:
            return "Scared";
        case PortraitId::Portrait47:
            return "Portrait47";
        case PortraitId::Portrait48:
            return "Portrait48";
        case PortraitId::Portrait49:
            return "Portrait49";
        case PortraitId::Portrait50:
            return "Portrait50";
        case PortraitId::Portrait51:
            return "Portrait51";
        case PortraitId::Portrait52:
            return "Portrait52";
        case PortraitId::Portrait53:
            return "Portrait53";
        case PortraitId::Portrait54:
            return "Portrait54";
        case PortraitId::Portrait55:
            return "Portrait55";
        case PortraitId::Portrait56:
            return "Portrait56";
        case PortraitId::Portrait57:
            return "Portrait57";
        case PortraitId::WakeUp:
            return "WakeUp";
        case PortraitId::Dead:
            return "Dead";
        case PortraitId::Eradicated:
            return "Eradicated";
    }

    return "Unknown";
}
}
