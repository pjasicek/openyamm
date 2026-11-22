#include "game/coop/CoopCharacter.h"

#include "engine/Localization.h"

#include <algorithm>
#include <cstdint>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
// A count both games change: the guest's value and the host's change since the base on top of it.
template <typename T>
T withHostChange(T base, T host, T put)
{
    const int64_t merged = int64_t(put) + (int64_t(host) - int64_t(base));
    return T(std::clamp<int64_t>(merged, std::numeric_limits<T>::min(), std::numeric_limits<T>::max()));
}

uint64_t withHostChange(uint64_t base, uint64_t host, uint64_t put)
{
    if (host >= base)
    {
        const uint64_t gained = host - base;
        const uint64_t most = std::numeric_limits<uint64_t>::max();
        return put > most - gained ? most : put + gained;
    }

    const uint64_t lost = base - host;
    return put > lost ? put - lost : 0;
}

// A value the host changes seldom and the guest's game not at all in the same moment: the host's when the host
// changed it, else the guest's.
template <typename T>
const T &hostChangeFirst(const T &base, const T &host, const T &put)
{
    return host == base ? put : host;
}

bool sameBuff(const PartyBuffState &left, const PartyBuffState &right)
{
    return left.active() == right.active() && left.spellId == right.spellId && left.skillLevel == right.skillLevel
        && left.skillMastery == right.skillMastery && left.power == right.power
        && left.casterMemberIndex == right.casterMemberIndex;
}

bool sameBuff(const CharacterBuffState &left, const CharacterBuffState &right)
{
    return left.active() == right.active() && left.spellId == right.spellId && left.skillLevel == right.skillLevel
        && left.skillMastery == right.skillMastery && left.power == right.power
        && left.casterMemberIndex == right.casterMemberIndex;
}

// What a character carries and wears.
bool sameThings(const Character &left, const Character &right)
{
    return left.inventory == right.inventory && left.equipment == right.equipment
        && left.equipmentRuntime == right.equipmentRuntime && left.implants == right.implants
        && left.rulesetState.storedBags == right.rulesetState.storedBags;
}

void mergeMember(const Character &base, const Character &host, Character &merged)
{
    merged.health = withHostChange(base.health, host.health, merged.health);
    merged.spellPoints = withHostChange(base.spellPoints, host.spellPoints, merged.spellPoints);
    merged.experience = withHostChange(base.experience, host.experience, merged.experience);
    merged.skillPoints = withHostChange(base.skillPoints, host.skillPoints, merged.skillPoints);
    merged.techPoints = withHostChange(base.techPoints, host.techPoints, merged.techPoints);

    // A condition the host set or lifted since the base.
    for (size_t condition = 0; condition < merged.conditions.size(); ++condition)
    {
        if (host.conditions.test(condition) != base.conditions.test(condition))
        {
            merged.conditions.set(condition, host.conditions.test(condition));
            merged.conditionStartGameMinutes[condition] = host.conditionStartGameMinutes[condition];
            merged.conditionExpireGameMinutes[condition] = host.conditionExpireGameMinutes[condition];
        }
    }

    for (uint32_t award : host.awards)
    {
        if (!base.awards.contains(award))
        {
            merged.awards.insert(award);
        }
    }

    for (uint32_t award : base.awards)
    {
        if (!host.awards.contains(award))
        {
            merged.awards.erase(award);
        }
    }

    // The world gave, took or broke something: all the character carries and wears is as the host has it, so that
    // nothing is there twice or gone.
    if (!sameThings(base, host))
    {
        merged.inventory = host.inventory;
        merged.equipment = host.equipment;
        merged.equipmentRuntime = host.equipmentRuntime;
        merged.implants = host.implants;
        merged.rulesetState.storedBags = host.rulesetState.storedBags;
        merged.rulesetState.currentBag = host.rulesetState.currentBag;
    }

    // What an event or a house changes (a promotion, a trained level, a stat from a barrel, a learned spell or
    // skill).
    merged.level = hostChangeFirst(base.level, host.level, merged.level);
    merged.className = hostChangeFirst(base.className, host.className, merged.className);
    merged.role = hostChangeFirst(base.role, host.role, merged.role);
    merged.might = hostChangeFirst(base.might, host.might, merged.might);
    merged.intellect = hostChangeFirst(base.intellect, host.intellect, merged.intellect);
    merged.personality = hostChangeFirst(base.personality, host.personality, merged.personality);
    merged.endurance = hostChangeFirst(base.endurance, host.endurance, merged.endurance);
    merged.speed = hostChangeFirst(base.speed, host.speed, merged.speed);
    merged.accuracy = hostChangeFirst(base.accuracy, host.accuracy, merged.accuracy);
    merged.luck = hostChangeFirst(base.luck, host.luck, merged.luck);
    merged.maxHealth = hostChangeFirst(base.maxHealth, host.maxHealth, merged.maxHealth);
    merged.maxSpellPoints = hostChangeFirst(base.maxSpellPoints, host.maxSpellPoints, merged.maxSpellPoints);
    merged.knownSpellIds = hostChangeFirst(base.knownSpellIds, host.knownSpellIds, merged.knownSpellIds);
    merged.playerBits = hostChangeFirst(base.playerBits, host.playerBits, merged.playerBits);
    merged.eventVariables = hostChangeFirst(base.eventVariables, host.eventVariables, merged.eventVariables);
    merged.ageModifier = hostChangeFirst(base.ageModifier, host.ageModifier, merged.ageModifier);

    // A skill the host taught or raised; the guest's own raises of the others stay.
    for (const auto &[name, skill] : host.skills)
    {
        const auto known = base.skills.find(name);

        if (known == base.skills.end() || known->second.level != skill.level
            || known->second.mastery != skill.mastery)
        {
            merged.skills[name] = skill;
        }
    }

    // A recovery the host began (the guest's own began in its game): the longer one holds.
    if (host.recoverySecondsRemaining > base.recoverySecondsRemaining)
    {
        merged.recoverySecondsRemaining = std::max(merged.recoverySecondsRemaining, host.recoverySecondsRemaining);
    }
}
}

Party::Snapshot mergeGuestCharacter(
    const Party::Snapshot &base,
    const Party::Snapshot &host,
    const Party::Snapshot &put)
{
    // A party of another shape than the host's is not the guest's to send.
    if (put.members.size() != host.members.size() || base.members.size() != host.members.size())
    {
        return host;
    }

    Party::Snapshot merged = put;
    merged.gold = withHostChange(base.gold, host.gold, put.gold);
    merged.bankGold = withHostChange(base.bankGold, host.bankGold, put.bankGold);
    merged.food = withHostChange(base.food, host.food, put.food);
    merged.fineGold = hostChangeFirst(base.fineGold, host.fineGold, put.fineGold);

    for (size_t buff = 0; buff < merged.partyBuffs.size(); ++buff)
    {
        if (!sameBuff(base.partyBuffs[buff], host.partyBuffs[buff]))
        {
            merged.partyBuffs[buff] = host.partyBuffs[buff];
        }
    }

    for (size_t member = 0; member < merged.characterBuffs.size(); ++member)
    {
        for (size_t buff = 0; buff < merged.characterBuffs[member].size(); ++buff)
        {
            if (!sameBuff(base.characterBuffs[member][buff], host.characterBuffs[member][buff]))
            {
                merged.characterBuffs[member][buff] = host.characterBuffs[member][buff];
            }
        }
    }

    // The party's own pouches go with what the characters carry.
    bool hostChangedThings = base.pouches != host.pouches;

    for (size_t member = 0; member < merged.members.size(); ++member)
    {
        hostChangedThings = hostChangedThings || !sameThings(base.members[member], host.members[member]);
    }

    for (size_t member = 0; member < merged.members.size(); ++member)
    {
        if (hostChangedThings)
        {
            // All of it, in every member and pouch: a thing may have moved between them.
            merged.members[member].inventory = host.members[member].inventory;
            merged.members[member].equipment = host.members[member].equipment;
            merged.members[member].equipmentRuntime = host.members[member].equipmentRuntime;
            merged.members[member].implants = host.members[member].implants;
            merged.members[member].rulesetState.storedBags = host.members[member].rulesetState.storedBags;
            merged.members[member].rulesetState.currentBag = host.members[member].rulesetState.currentBag;
        }

        mergeMember(base.members[member], host.members[member], merged.members[member]);
    }

    if (hostChangedThings)
    {
        merged.pouches = host.pouches;
    }

    // What the ruleset keeps for the party. Its auras are the host's when the host changed them (a cast, a scroll, a
    // temple: the host does those), else the guest's, whose game ends them (a map left, a time up, a holder down).
    // The held food and the deaths are the guest's game's to count.
    const PartyRulesetState &baseRules = base.rulesetState;
    const PartyRulesetState &hostRules = host.rulesetState;

    if (hostRules.auraHolders != baseRules.auraHolders || hostRules.fixedAuraMaps != baseRules.fixedAuraMaps
        || hostRules.fixedAuraEndMinutes != baseRules.fixedAuraEndMinutes)
    {
        merged.rulesetState.auraHolders = hostRules.auraHolders;
        merged.rulesetState.fixedAuraMaps = hostRules.fixedAuraMaps;
        merged.rulesetState.fixedAuraEndMinutes = hostRules.fixedAuraEndMinutes;
    }

    merged.rulesetState.heldFood =
        withHostChange(baseRules.heldFood, hostRules.heldFood, put.rulesetState.heldFood);

    // The host's alone: these follow its world and its clock.
    merged.campaign = {};
    merged.adventurersInnMembers = host.adventurersInnMembers;
    merged.hiredNpcFollowers = host.hiredNpcFollowers;
    merged.mm9Hirelings = host.mm9Hirelings;
    merged.itemEffectElapsedGameSeconds = host.itemEffectElapsedGameSeconds;
    merged.itemWeeklyEffectSequence = host.itemWeeklyEffectSequence;
    merged.daysWithoutRest = host.daysWithoutRest;
    merged.awakeDayIndex = host.awakeDayIndex;
    merged.lastOutdoorMapFileName = host.lastOutdoorMapFileName;
    return merged;
}

std::string coopRulesText(const RulesetSelection &ruleset)
{
    if (ruleset.isStandard())
    {
        return ruleset.id;
    }

    const RulesetOptions &options = ruleset.options;
    return ruleset.id + " " + std::string(rulesetDifficultyId(options.difficulty))
        + (options.challengeMode != RulesetChallengeMode::None
                ? " " + std::string(rulesetChallengeModeId(options.challengeMode)) : std::string())
        + (options.soloRun ? " solo" : "");
}

std::optional<std::string> coopRulesRefusal(const std::string &host, const std::string &guest)
{
    if (host == guest)
    {
        return std::nullopt;
    }

    // A text is the ruleset's id and then its options by their ids.
    struct Rules
    {
        std::string id;
        bool hasOptions = false;
        bool readable = true;
        RulesetOptions options;
    };
    const auto read = [](const std::string &text)
    {
        Rules rules;
        const size_t space = text.find(' ');
        rules.id = text.substr(0, space);

        if (space != std::string::npos)
        {
            std::string ids = text.substr(space + 1);
            std::replace(ids.begin(), ids.end(), ' ', ':');
            rules.hasOptions = true;
            rules.readable = applyRulesetOptionIds(ids, rules.options);
        }

        return rules;
    };
    const Rules hostRules = read(host);
    const Rules guestRules = read(guest);
    const std::string both = Engine::tr("the host plays \"{host}\" and this game \"{guest}\"",
        {{"host", host}, {"guest", guest}});

    if (hostRules.id != guestRules.id || hostRules.hasOptions != guestRules.hasOptions || !hostRules.readable
        || !guestRules.readable)
    {
        return both + ": " + Engine::tr("only games of the same ruleset play together");
    }

    if (!hostRules.hasOptions)
    {
        return std::nullopt;
    }

    if (hostRules.options.soloRun != guestRules.options.soloRun)
    {
        return both + ": " + Engine::tr("a solo run and a party do not play together under these rules");
    }

    // Another difficulty, progression or challenge mode, Nightmare and the modes a game keeps for good among them:
    // the guest plays by the host's for the session.
    return std::nullopt;
}

std::optional<std::string> coopContentDifference(
    const std::vector<std::string> &host,
    const std::vector<std::string> &guest)
{
    // The rules first, in words of their own: the commonest difference, and the one a player can do something about.
    // They need not be the same text to play together (coopRulesRefusal), so the lines' comparison leaves them out.
    constexpr std::string_view RulesPrefix = "ruleset ";
    const auto rulesOf = [RulesPrefix](const std::vector<std::string> &lines)
    {
        for (const std::string &line : lines)
        {
            if (line.starts_with(RulesPrefix))
            {
                return line.substr(RulesPrefix.size());
            }
        }

        return std::string();
    };
    const auto withoutRules = [RulesPrefix](std::vector<std::string> lines)
    {
        std::erase_if(lines, [RulesPrefix](const std::string &line) { return line.starts_with(RulesPrefix); });
        return lines;
    };

    if (const std::optional<std::string> refusal = coopRulesRefusal(rulesOf(host), rulesOf(guest)))
    {
        return refusal;
    }

    const std::vector<std::string> hostLines = withoutRules(host);
    const std::vector<std::string> guestLines = withoutRules(guest);

    for (const std::string &line : hostLines)
    {
        if (std::find(guestLines.begin(), guestLines.end(), line) == guestLines.end())
        {
            return Engine::tr("the host has \"{line}\" and this game does not", {{"line", line}});
        }
    }

    for (const std::string &line : guestLines)
    {
        if (std::find(hostLines.begin(), hostLines.end(), line) == hostLines.end())
        {
            return Engine::tr("this game has \"{line}\" and the host does not", {{"line", line}});
        }
    }

    // The same lines in another order: the mods mount differently.
    return hostLines == guestLines ? std::nullopt
        : std::optional<std::string>(Engine::tr("the two games mount their mods in a different order"));
}

Party::Snapshot characterForWire(Party::Snapshot party)
{
    party.campaign = {};

    for (Character &member : party.members)
    {
        member.portraitState = PortraitId::Normal;
        member.portraitElapsedTicks = 0;
        member.portraitDurationTicks = 0;
        member.portraitSequenceCounter = 0;
        member.portraitImageIndex = 0;
    }

    return party;
}

CharacterVitals takeCharacterVitals(const Party::Snapshot &party)
{
    CharacterVitals vitals;
    vitals.members.reserve(party.members.size());

    for (const Character &member : party.members)
    {
        vitals.members.push_back({member.health, member.spellPoints, member.recoverySecondsRemaining});
    }

    for (size_t buff = 0; buff < party.partyBuffs.size(); ++buff)
    {
        vitals.partyBuffSeconds[buff] = party.partyBuffs[buff].remainingSeconds;
    }

    // The rows of the members there are: the others hold nothing.
    for (size_t member = 0; member < party.members.size() && member < party.characterBuffs.size(); ++member)
    {
        for (const CharacterBuffState &buff : party.characterBuffs[member])
        {
            vitals.characterBuffSeconds.push_back(buff.remainingSeconds);
            vitals.characterBuffSeconds.push_back(buff.periodicAccumulatorSeconds);
        }
    }

    vitals.itemEffectElapsedGameSeconds = party.itemEffectElapsedGameSeconds;
    return vitals;
}

Party::Snapshot withoutCharacterVitals(Party::Snapshot party)
{
    for (Character &member : party.members)
    {
        member.health = 0;
        member.spellPoints = 0;
        member.recoverySecondsRemaining = 0.0f;
        // What else runs with the host's clock. A guest's game does not need these between two whole states: the
        // times it shows of them are then a little old.
        member.healthRegenAccumulator = 0.0f;
        member.spellRegenAccumulator = 0.0f;
        member.rulesetState.poisonSeconds = member.rulesetState.poisonSeconds > 0.0f ? 1.0f : 0.0f;

        for (TimedPrimaryStatBonus &bonus : member.timedPrimaryStatBonuses)
        {
            bonus.remainingSeconds = bonus.remainingSeconds > 0.0f ? 1.0f : 0.0f;
        }

        for (TimedPotionEffect &effect : member.rulesetState.potionEffects)
        {
            effect.remainingSeconds = effect.remainingSeconds > 0.0f ? 1.0f : 0.0f;
        }
    }

    // A buff that is there keeps a mark of it: one that began or ended is no change of vitals alone.
    for (PartyBuffState &buff : party.partyBuffs)
    {
        buff.remainingSeconds = buff.active() ? 1.0f : 0.0f;
    }

    for (auto &memberBuffs : party.characterBuffs)
    {
        for (CharacterBuffState &buff : memberBuffs)
        {
            buff.remainingSeconds = buff.active() ? 1.0f : 0.0f;
            buff.periodicAccumulatorSeconds = 0.0f;
        }
    }

    party.itemEffectElapsedGameSeconds = 0.0f;
    return party;
}

bool applyCharacterVitals(Party::Snapshot &party, const CharacterVitals &vitals)
{
    size_t characterBuffCount = 0;

    for (size_t member = 0; member < party.members.size() && member < party.characterBuffs.size(); ++member)
    {
        characterBuffCount += party.characterBuffs[member].size();
    }

    if (vitals.members.size() != party.members.size() || vitals.characterBuffSeconds.size() != characterBuffCount * 2)
    {
        return false;
    }

    for (size_t member = 0; member < party.members.size(); ++member)
    {
        party.members[member].health = vitals.members[member].health;
        party.members[member].spellPoints = vitals.members[member].spellPoints;
        party.members[member].recoverySecondsRemaining = vitals.members[member].recoverySecondsRemaining;
    }

    for (size_t buff = 0; buff < party.partyBuffs.size(); ++buff)
    {
        party.partyBuffs[buff].remainingSeconds = vitals.partyBuffSeconds[buff];
    }

    size_t next = 0;

    for (size_t member = 0; member < party.members.size() && member < party.characterBuffs.size(); ++member)
    {
        for (CharacterBuffState &buff : party.characterBuffs[member])
        {
            buff.remainingSeconds = vitals.characterBuffSeconds[next++];
            buff.periodicAccumulatorSeconds = vitals.characterBuffSeconds[next++];
        }
    }

    party.itemEffectElapsedGameSeconds = vitals.itemEffectElapsedGameSeconds;
    return true;
}
}
