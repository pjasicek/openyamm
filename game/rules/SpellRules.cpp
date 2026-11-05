#include "game/rules/SpellRules.h"

#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/tables/SpellTable.h"

#include <functional>

namespace OpenYAMM::Game
{
std::string SpellRules::spellName(const Character &, const SpellEntry &spell) const
{
    return spell.name;
}

std::optional<std::string> SpellRules::castRefusal(const Party &, size_t, uint32_t) const
{
    return std::nullopt;
}

std::optional<SkillMastery> SpellRules::classSpellMastery(const Character &, uint32_t) const
{
    return std::nullopt;
}

void SpellRules::afterCast(Party &, size_t, uint32_t, const SpellTable &, bool, bool) const
{
}

std::optional<bool> SpellRules::toggleSpellRotation(Character &) const
{
    return std::nullopt;
}

int SpellRules::manaCost(const CharacterSpellCast &, int tableCost) const
{
    return tableCost;
}

int SpellRules::recoveryTicks(const CharacterSpellCast &, int tableTicks) const
{
    return tableTicks;
}

std::optional<int> SpellRules::healAmount(const CharacterSpellCast &) const
{
    return std::nullopt;
}

std::optional<AuraCastResult> SpellRules::castAura(Party &, size_t, uint32_t) const
{
    return std::nullopt;
}

void SpellRules::updateAuras(Party &, float) const
{
}

int SpellRules::reservedSpellPoints(const Party &, size_t) const
{
    return 0;
}

int SpellRules::reservedHitPoints(const Party &, size_t) const
{
    return 0;
}

void SpellRules::afterHeal(Party &, size_t, int, int, int, float &) const
{
}

SpellSplash SpellRules::spellSplash(uint32_t, SkillMastery) const
{
    return {};
}

bool SpellRules::ignoresCrowdControl(const ActorRulesetFacts &) const
{
    return false;
}

bool SpellRules::castSourceBuff(Party &, uint32_t, BuffSource) const
{
    return false;
}

std::optional<int> SpellRules::auraDamage(const Party &, uint32_t) const
{
    return std::nullopt;
}

std::optional<float> SpellRules::partyBuffSeconds(const Party &, uint32_t, uint32_t, SkillMastery, bool) const
{
    return std::nullopt;
}

bool SpellRules::keepsScroll(const Party &, uint32_t) const
{
    return false;
}

bool SpellRules::castsAsAura(const Party &, size_t, uint32_t) const
{
    return false;
}

bool SpellRules::shareLife(Party &, int) const
{
    return false;
}

void SpellRules::memberLeaving(const Party &, size_t) const
{
}

std::optional<std::string> SpellRules::heldBuffText(const Party &, uint32_t) const
{
    return std::nullopt;
}

std::vector<uint32_t> SpellRules::heldAurasWithoutBuffSlot(const Party &) const
{
    return {};
}

std::optional<std::string> SpellRules::removeAllBuffs(Party &) const
{
    return std::nullopt;
}

std::optional<AuraReport> SpellRules::auraReport(const Party &) const
{
    return std::nullopt;
}

bool SpellRules::tabCyclesSpellbookSchools() const
{
    return false;
}

bool SpellRules::sunrayWorksIndoors() const
{
    return false;
}

float SpellRules::spiritLashRadius(SkillMastery) const
{
    return 768.0f;
}

bool SpellRules::raiseDeadLiftsEradication(SkillMastery) const
{
    return true;
}

bool SpellRules::quickCastSpreadsDebuff(uint32_t) const
{
    return false;
}

size_t SpellRules::extraPermanentWisps(SkillMastery) const
{
    return 0;
}

bool SpellRules::protectionFromMagicRaisesResistances() const
{
    return true;
}

SpellTooltipText SpellRules::spellTooltip(const Party &, const Character &caster, const SpellEntry &spell) const
{
    SpellTooltipText text;
    text.name = spellName(caster, spell);
    text.description = spell.description;
    text.masteryLines = {spell.normalText, spell.expertText, spell.masterText, spell.grandmasterText};
    return text;
}

std::optional<float> SpellRules::crowdControlSeconds(const CrowdControlCast &) const
{
    return std::nullopt;
}

const SpellRules &standardSpellRules()
{
    static const SpellRules Rules;
    return Rules;
}

std::optional<float> partyCrowdControlSeconds(
    const Party *pParty,
    uint32_t casterIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery mastery,
    int resistance,
    const ActorRulesetFacts &targetFacts,
    int targetTableLevel,
    bool targetUndead,
    const std::string &mapName,
    size_t actorIndex,
    double gameMinutes)
{
    if (!targetUndead && (spellId == spellIdValue(SpellId::TurnUndead) || spellId == spellIdValue(SpellId::ControlUndead)))
    {
        return std::nullopt;
    }

    CrowdControlCast cast;
    cast.spellId = spellId;
    cast.mastery = mastery;
    cast.skillLevel = skillLevel;
    cast.pCaster = pParty != nullptr ? pParty->member(casterIndex) : nullptr;
    cast.resistance = resistance;
    cast.targetLevel = targetFacts.level > 0 ? targetFacts.level : targetTableLevel;
    cast.boss = targetFacts.bossAffix != 0;
    cast.pTargetFacts = &targetFacts;
    cast.targetKey = mapActorKey(mapName, actorIndex);
    cast.partySize = pParty != nullptr ? pParty->members().size() : 1;
    // A game minute is two real seconds.
    cast.nowSeconds = gameMinutes * 2.0;
    return gameRulesFor(pParty).spells.crowdControlSeconds(cast);
}
}
