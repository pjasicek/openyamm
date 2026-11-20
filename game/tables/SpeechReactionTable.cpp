#include "game/tables/SpeechReactionTable.h"

#include <algorithm>
#include <cctype>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeIdentifier(const std::string &value)
{
    std::string normalized;
    normalized.reserve(value.size());

    for (char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)) != 0)
        {
            normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
    }

    return normalized;
}

std::optional<SpeechId> speechIdFromName(const std::string &value)
{
    static const std::unordered_map<std::string, SpeechId> SpeechIdsByName = {
        {"disarmtrap", SpeechId::DisarmTrap},
        {"storeclosed", SpeechId::StoreClosed},
        {"trapexploded", SpeechId::TrapExploded},
        {"selectcharacter", SpeechId::SelectCharacter},
        {"identifyweakitem", SpeechId::IdentifyWeakItem},
        {"identifygreatitem", SpeechId::IdentifyGreatItem},
        {"identifyfailitem", SpeechId::IdentifyFailItem},
        {"repairsuccess", SpeechId::RepairSuccess},
        {"repairfail", SpeechId::RepairFail},
        {"setquickspell", SpeechId::SetQuickSpell},
        {"hungry", SpeechId::Hungry},
        {"damageminor", SpeechId::DamageMinor},
        {"damagemajor", SpeechId::DamageMajor},
        {"dying", SpeechId::Dying},
        {"drunk", SpeechId::Drunk},
        {"insane", SpeechId::Insane},
        {"poisoned", SpeechId::Poisoned},
        {"cursed", SpeechId::Cursed},
        {"falling", SpeechId::Falling},
        {"cantresthere", SpeechId::CantRestHere},
        {"notenoughgold", SpeechId::NotEnoughGold},
        {"inventoryroom", SpeechId::InventoryRoom},
        {"potionsuccess", SpeechId::PotionSuccess},
        {"potionfail", SpeechId::PotionFail},
        {"doorlocked", SpeechId::DoorLocked},
        {"learnspell", SpeechId::LearnSpell},
        {"cantlearnspell", SpeechId::CantLearnSpell},
        {"cantequip", SpeechId::CantEquip},
        {"helloday", SpeechId::HelloDay},
        {"helloevening", SpeechId::HelloEvening},
        {"hellohouse", SpeechId::HelloHouse},
        {"killstrongenemy", SpeechId::KillStrongEnemy},
        {"killweakenemy", SpeechId::KillWeakEnemy},
        {"lastpersonstanding", SpeechId::LastPersonStanding},
        {"leavedungeon", SpeechId::LeaveDungeon},
        {"enterdungeon", SpeechId::EnterDungeon},
        {"yes", SpeechId::Yes},
        {"thankyou", SpeechId::ThankYou},
        {"indignant", SpeechId::Indignant},
        {"yell", SpeechId::Yell},
        {"attackhit", SpeechId::AttackHit},
        {"attackmiss", SpeechId::AttackMiss},
        {"shoot", SpeechId::Shoot},
        {"castspell", SpeechId::CastSpell},
        {"damagedparty", SpeechId::DamagedParty},
        {"founditem", SpeechId::FoundItem},
        {"skillincreased", SpeechId::SkillIncreased},
        {"questgot", SpeechId::QuestGot},
        {"awardgot", SpeechId::AwardGot},
        {"templeheal", SpeechId::TempleHeal},
        {"templedonate", SpeechId::TempleDonate},
        {"travelboat", SpeechId::TravelBoat},
        {"travelhorse", SpeechId::TravelHorse},
        {"shopidentify", SpeechId::ShopIdentify},
        {"shoprepair", SpeechId::ShopRepair},
        {"alreadyidentified", SpeechId::AlreadyIdentified},
        {"itemsold", SpeechId::ItemSold},
        {"wrongshop", SpeechId::WrongShop},
        {"bankdeposit", SpeechId::BankDeposit},
        {"levelup", SpeechId::LevelUp},
        {"beg", SpeechId::Beg},
        {"begfail", SpeechId::BegFail},
        {"threat", SpeechId::Threat},
        {"threatfail", SpeechId::ThreatFail},
        {"bribe", SpeechId::Bribe},
        {"bribefail", SpeechId::BribeFail},
        {"npcdonttalk", SpeechId::NpcDontTalk},
        {"hirenpc", SpeechId::HireNpc},
        {"tavernpacksfull", SpeechId::TavernPacksFull},
        {"taverndrink", SpeechId::TavernDrink},
        {"taverngotdrunk", SpeechId::TavernGotDrunk},
        {"taverntip", SpeechId::TavernTip},
        {"shopitembought", SpeechId::ShopItemBought},
        {"skilllearned", SpeechId::SkillLearned},
        {"shoprude", SpeechId::ShopRude},
        {"skillmasteryincreased", SpeechId::SkillMasteryIncreased},
        {"joinedguild", SpeechId::JoinedGuild},
        {"statbonusincreased", SpeechId::StatBonusIncreased},
        {"statbaseincreased", SpeechId::StatBaseIncreased},
        {"afraidsilent", SpeechId::AfraidSilent},
        {"cheateddeath", SpeechId::CheatedDeath},
        {"inprison", SpeechId::InPrison},
        {"awaken", SpeechId::Awaken},
        {"identifymonsterweak", SpeechId::IdentifyMonsterWeak},
        {"identifymonsterbig", SpeechId::IdentifyMonsterBig},
        {"identifymonsterfail", SpeechId::IdentifyMonsterFail},
        {"deathblow", SpeechId::DeathBlow},
        {"drinkpotion", SpeechId::DrinkPotion},
        {"tired", SpeechId::Tired},
    };

    const std::unordered_map<std::string, SpeechId>::const_iterator speechIt =
        SpeechIdsByName.find(normalizeIdentifier(value));

    if (speechIt == SpeechIdsByName.end())
    {
        return std::nullopt;
    }

    return speechIt->second;
}

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::vector<std::string> splitSoundTypes(const std::string &value)
{
    std::vector<std::string> result;
    std::stringstream stream(value);
    std::string item;

    while (std::getline(stream, item, ','))
    {
        item = trimCopy(item);

        if (!item.empty())
        {
            result.push_back(std::move(item));
        }
    }

    return result;
}
}

bool SpeechReactionTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexBySpeechId.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 3)
        {
            continue;
        }

        const std::optional<SpeechId> speechId = speechIdFromName(row[0]);

        if (!speechId)
        {
            continue;
        }

        SpeechReactionEntry entry = {};
        entry.speechId = *speechId;
        entry.name = row[1];
        entry.soundTypes = row.size() > 2 ? splitSoundTypes(row[2]) : std::vector<std::string>{};

        if (row.size() > 3 && !row[3].empty())
        {
            entry.faceAnimationId = faceAnimationIdFromName(row[3]);
        }

        m_entryIndexBySpeechId[entry.speechId] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const SpeechReactionEntry *SpeechReactionTable::find(SpeechId speechId) const
{
    const std::unordered_map<SpeechId, size_t>::const_iterator entryIt = m_entryIndexBySpeechId.find(speechId);

    if (entryIt == m_entryIndexBySpeechId.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}
}
