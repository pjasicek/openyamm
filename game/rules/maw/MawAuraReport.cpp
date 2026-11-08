#include "game/rules/maw/MawSpellRules.h"
#include "engine/Localization.h"

#include "game/party/Party.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawRules.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <unordered_map>

// The aura panel's report (SpellRules::auraReport; level_generation/ui/maw_aura_panel_20261025 A): what each held
// aura does at its holder's strength, set against the party's other auras and each member's own potion copies the
// way the aura pass (MawSpellRules::updateAuras) and the sheet and combat rules (MawRules::auraSkill, memberAura,
// addPotionAuraFlats) choose between them: each effect takes its strongest source, they never add up.
namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t DayOfTheGods = 83;
constexpr uint32_t DayOfProtection = 85;
constexpr uint32_t HourOfPower = 86;
constexpr uint32_t StoneSkin = 38;
constexpr uint32_t Bless = 46;
// A scroll's, pedestal's or temple's aura holds at skill 7, Master, level 40 (getSpecialBuffSkill).
constexpr MawAuraSource BlessingSource{7, 3, 40, 0};

// One effect an aura can have; several auras may give it, and the strongest source counts.
enum class Effect : uint8_t
{
    Resistance,
    Stat,
    Armour,
    Attack,
    HitChance,
    Haste,
    Shield,
    Fate,
    Heroism,
    Hammerhands,
    EmpowerMagic,
    Text,
};

struct EffectRef
{
    Effect effect = Effect::Text;
    // The element (fire, air, water, earth, mind, body) or the stat (Might ... Luck).
    size_t index = 0;
};

constexpr std::array<uint32_t, 6> ResistanceAuras = {3, 14, 25, 36, 58, 69};
constexpr std::array<std::string_view, 6> ResistanceNames = {Engine::trNoop("Fire resistance"),
    Engine::trNoop("Air resistance"), Engine::trNoop("Water resistance"), Engine::trNoop("Earth resistance"),
    Engine::trNoop("Mind resistance"), Engine::trNoop("Body resistance")};
// The aura that raises each stat (MawSkillRules::applyStatBonuses).
constexpr std::array<uint32_t, 7> StatAuras = {69, 3, 58, 36, 46, 14, 25};
constexpr std::array<std::string_view, 7> StatNames = {Engine::trNoop("Might"), Engine::trNoop("Intellect"),
    Engine::trNoop("Personality"), Engine::trNoop("Endurance"), Engine::trNoop("Accuracy"), Engine::trNoop("Speed"),
    Engine::trNoop("Luck")};

bool composite(uint32_t spellId)
{
    return spellId == DayOfTheGods || spellId == DayOfProtection || spellId == HourOfPower;
}

// Unconscious, dead, stoned or eradicated holders' auras are off (as the aura pass counts it).
bool conscious(const Character &member)
{
    return !member.conditions.test(size_t(CharacterCondition::Dead))
        && !member.conditions.test(size_t(CharacterCondition::Unconscious))
        && !member.conditions.test(size_t(CharacterCondition::Petrified))
        && !member.conditions.test(size_t(CharacterCondition::Eradicated));
}

std::vector<EffectRef> auraEffects(uint32_t spellId)
{
    for (size_t element = 0; element < ResistanceAuras.size(); ++element)
    {
        if (ResistanceAuras[element] == spellId)
        {
            const size_t stat = size_t(std::find(StatAuras.begin(), StatAuras.end(), spellId) - StatAuras.begin());
            return {{Effect::Resistance, element}, {Effect::Stat, stat}};
        }
    }

    switch (spellId)
    {
        case Bless:
            return {{Effect::Attack, 0}, {Effect::Stat, 4}, {Effect::HitChance, 0}};
        case StoneSkin:
            return {{Effect::Armour, 0}};
        case 5:
            return {{Effect::Haste, 0}};
        case 17:
            return {{Effect::Shield, 0}};
        case 47:
            return {{Effect::Fate, 0}};
        case 51:
            return {{Effect::Heroism, 0}};
        case 73:
            return {{Effect::Hammerhands, 0}};
        case 28:
            return {{Effect::EmpowerMagic, 0}};
        case HourOfPower:
            return {{Effect::Haste, 0}, {Effect::Shield, 0}, {Effect::Armour, 0}, {Effect::Fate, 0}};
        case DayOfTheGods:
        {
            std::vector<EffectRef> effects;

            for (size_t stat = 0; stat < StatAuras.size(); ++stat)
            {
                effects.push_back({Effect::Stat, stat});
            }

            return effects;
        }
        case DayOfProtection:
        {
            std::vector<EffectRef> effects;

            for (size_t element = 0; element < ResistanceAuras.size(); ++element)
            {
                effects.push_back({Effect::Resistance, element});
            }

            return effects;
        }
        default:
            return {{Effect::Text, 0}};
    }
}

// The auras that give the effect, and those of them a member's potion copy gives too.
std::vector<uint32_t> effectSources(const EffectRef &ref)
{
    switch (ref.effect)
    {
        case Effect::Resistance:
            return {ResistanceAuras[ref.index], DayOfProtection};
        case Effect::Stat:
            return {StatAuras[ref.index], DayOfTheGods};
        case Effect::Armour:
            return {StoneSkin, HourOfPower};
        case Effect::Haste:
            return {5, HourOfPower};
        case Effect::Shield:
            return {17, HourOfPower};
        case Effect::Fate:
            return {47, HourOfPower};
        case Effect::Attack:
        case Effect::HitChance:
            return {Bless};
        case Effect::Heroism:
            return {51};
        case Effect::Hammerhands:
            return {73};
        case Effect::EmpowerMagic:
            return {28};
        case Effect::Text:
            return {};
    }

    return {};
}

std::vector<uint32_t> potionSources(const EffectRef &ref)
{
    switch (ref.effect)
    {
        case Effect::Resistance:
            return {ResistanceAuras[ref.index], DayOfProtection};
        case Effect::Stat:
            return {StatAuras[ref.index], DayOfTheGods};
        case Effect::Armour:
            return {StoneSkin};
        case Effect::Attack:
        case Effect::HitChance:
            return {Bless};
        case Effect::Haste:
            return {5};
        case Effect::Shield:
            return {17};
        case Effect::Heroism:
            return {51};
        default:
            return {};
    }
}

// The effect's strength from one source of it: the flat auras (20 + level / 4) x (1 + 2 % x skill), the stat percent,
// the percent auras' multiplier; Day of Protection's skill counts / 1.4 and Hour of Power's / 1.5.
double effectValue(const EffectRef &ref, uint32_t spellId, const MawAuraSource &source, double buffScale)
{
    const double skill = spellId == DayOfProtection ? source.skill / 1.4
        : spellId == HourOfPower ? source.skill / 1.5 : source.skill;

    switch (ref.effect)
    {
        case Effect::Resistance:
        case Effect::Armour:
        case Effect::Attack:
            return mawAuraFlat(20, 2, source.level, skill, buffScale);
        case Effect::Stat:
            return mawAuraStatPercent(source.skill, spellId == DayOfTheGods);
        case Effect::HitChance:
            return 5 + 5 * std::min(source.skill, 50.0) / 50;
        case Effect::Haste:
            return 100 * mawBuffMultiplier(5, skill, buffScale);
        case Effect::Shield:
            return 100 * mawBuffMultiplier(17, skill, buffScale);
        case Effect::Fate:
            return 100 * mawBuffMultiplier(47, skill, buffScale);
        case Effect::Heroism:
            return 100 * mawBuffMultiplier(51, skill, buffScale);
        case Effect::Hammerhands:
            return 100 * mawBuffMultiplier(73, skill, buffScale);
        case Effect::EmpowerMagic:
            // MAW reads Haste's numbers for Empower Magic (CLASSES_SPELLS_SPEC.md §3.3).
            return 100 * mawBuffMultiplier(5, skill, buffScale);
        case Effect::Text:
            return 0;
    }

    return 0;
}

void describe(AuraEffect &effect, const EffectRef &ref, uint32_t spellId, const MawAuraSource &source)
{
    const bool hour = spellId == HourOfPower;

    switch (ref.effect)
    {
        case Effect::Resistance:
            effect.label = Engine::tr(ResistanceNames[ref.index]);
            effect.kind = AuraValueKind::Bonus;
            return;
        case Effect::Stat:
            effect.label = Engine::tr(StatNames[ref.index]);
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::Armour:
            effect.label = Engine::tr(hour ? "Stone Skin, armour" : "Armour class");
            effect.kind = AuraValueKind::Bonus;
            return;
        case Effect::Attack:
            effect.label = Engine::tr("Attack, melee and ranged");
            effect.kind = AuraValueKind::Bonus;
            return;
        case Effect::HitChance:
            effect.label = Engine::tr("Chance to hit");
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::Haste:
            effect.label = Engine::tr(hour ? "Haste, recovery" : "Faster recovery");
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::Shield:
            effect.label = Engine::tr(hour ? "Shield, magic damage taken" : "Magic damage taken");
            effect.kind = AuraValueKind::ReductionPercent;
            return;
        case Effect::Fate:
            effect.label = Engine::tr(hour ? "Fate, critical chance" : "Critical chance");
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::Heroism:
            effect.label = Engine::tr("Melee damage");
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::Hammerhands:
            effect.label = Engine::tr("Unarmed damage");
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::EmpowerMagic:
            effect.label = Engine::tr("Damage spells");
            effect.kind = AuraValueKind::BonusPercent;
            return;
        case Effect::Text:
            break;
    }

    effect.kind = AuraValueKind::Text;

    switch (spellId)
    {
        case 1:
            effect.label = Engine::tr("Light around the party");
            effect.text = Engine::tr("power {power}", {{"power", std::max(source.mastery, 0) + 1}});
            break;
        case 4:
            effect.label = Engine::tr("Weapons and arrows burn");
            effect.text = Engine::tr(
                "{percent} % of level damage", {{"percent", 10 + 5 * (std::clamp(source.mastery, 1, 4) - 1)}});
            break;
        case 8:
            effect.label = Engine::tr("Burns nearby monsters");
            effect.text = Engine::tr("10 + 1-30 per skill point");
            break;
        case 12:
            effect.label = Engine::tr("Minimap");
            effect.text = Engine::tr("monsters and points of interest");
            break;
        case 27:
            effect.label = Engine::tr("Walking on water");
            effect.text = Engine::tr("the whole party");
            break;
        case 50:
            effect.label = Engine::tr("Death");
            effect.text = Engine::tr("delayed at massive hit point loss");
            break;
        case 56:
            effect.label = Engine::tr("Spell points");
            effect.text = Engine::tr("regained over time");
            break;
        case 71:
            effect.label = Engine::tr("Hit points");
            effect.text = Engine::tr("regained over time");
            break;
        case 75:
            effect.label = Engine::tr("Immune to");
            effect.text = Engine::tr("poison, disease, stone, death");
            break;
        case 91:
            effect.label = Engine::tr("Attacks heal");
            effect.text = Engine::tr("part of the damage dealt");
            break;
        case 95:
            effect.label = Engine::tr("Monsters that hit");
            effect.text = Engine::tr("take what they inflict");
            break;
        default:
            effect.label = Engine::tr("Effect");
            effect.text = Engine::tr("party-wide");
            break;
    }
}

// Whether `rival` covers the effect over `own`: it is stronger, or as strong and the specific aura where `own` is
// Hour of Power, Day of Protection or Day of the Gods (the aura pass keeps the specific one on a tie). A potion copy
// counts only when stronger.
bool covers(const AuraRival &rival, uint32_t ownSpellId, double own)
{
    constexpr double Epsilon = 1e-6;

    if (rival.value > own + Epsilon)
    {
        return true;
    }

    return !rival.potion && rival.value > own - Epsilon && composite(ownSpellId) && !composite(rival.spellId);
}

struct HeldSource
{
    MawAuraSource source;
    std::optional<size_t> holder;
    bool active = false;
};
}

std::optional<AuraReport> MawSpellRules::auraReport(const Party &party) const
{
    const MawGameState &state = m_rules.state();
    const double buffScale = m_rules.buffScale();
    const size_t memberCount = party.members().size();
    std::unordered_map<uint32_t, HeldSource> held;

    for (const auto &[spellId, holder] : state.auraHolders)
    {
        const MawAura *pAura = mawAura(spellId);

        if (pAura == nullptr)
        {
            continue;
        }

        if (holder == MawGameState::FixedAuraHolder)
        {
            held[spellId] = {BlessingSource, std::nullopt, true};
            continue;
        }

        const Character *pHolder = party.member(holder);

        if (pHolder == nullptr)
        {
            continue;
        }

        const CharacterSkill *pSkill = pHolder->findSkill(mawSpellSchoolSkill(spellId));
        MawAuraSource source;
        source.skill = std::min(pSkill != nullptr ? double(pSkill->level) : 0.0, pAura->skillCap);
        source.mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
        source.level = pHolder->level;
        source.holder = holder;
        held[spellId] = {source, size_t(holder), conscious(*pHolder)};
    }

    AuraReport report;

    for (size_t memberIndex = 0; memberIndex < memberCount; ++memberIndex)
    {
        const Character &member = party.members()[memberIndex];
        // What any aura would cost names the member's kind of reservation.
        const AuraReservationCost kind = auraCost(party, memberIndex, StoneSkin);
        AuraMemberPool pool;
        pool.health = kind.health;
        pool.maximum = pool.health ? Party::effectiveMaximumHealth(member) : Party::effectiveMaximumSpellPoints(member);
        pool.current = pool.health ? member.health : member.spellPoints;
        pool.reserved = pool.health ? reservedHitPoints(party, memberIndex) : reservedSpellPoints(party, memberIndex);
        pool.reservesNothing = kind.free;
        pool.conscious = conscious(member);
        (pool.health ? report.reservedHitPoints : report.reservedSpellPoints) += pool.reserved;
        report.pools.push_back(pool);
    }

    for (const auto &[spellId, own] : held)
    {
        AuraReportEntry entry;
        entry.spellId = spellId;
        entry.holder = own.holder;
        entry.schoolSkill = mawSpellSchoolSkill(spellId);
        entry.skill = own.source.skill;
        entry.mastery = own.source.mastery;
        entry.level = int(own.source.level);

        if (own.holder)
        {
            const Character &holder = party.members()[*own.holder];
            const CharacterSkill *pSkill = holder.findSkill(entry.schoolSkill);
            entry.skillCapped = pSkill != nullptr && double(pSkill->level) > own.source.skill;
            entry.cost = auraCost(party, *own.holder, spellId);
            entry.state = own.active ? AuraState::Active : AuraState::Suspended;
        }
        else
        {
            const auto fixed = state.fixedAuraMaps.find(spellId);
            entry.templeBlessing = fixed != state.fixedAuraMaps.end() && fixed->second.empty();
            entry.cost.free = true;
            entry.state = AuraState::Blessing;
        }

        entry.members.resize(memberCount);
        const std::vector<EffectRef> refs = auraEffects(spellId);
        size_t usedEverywhere = 0;
        size_t usedNowhere = 0;

        for (size_t effectIndex = 0; effectIndex < refs.size(); ++effectIndex)
        {
            const EffectRef &ref = refs[effectIndex];
            AuraEffect effect;
            describe(effect, ref, spellId, own.source);
            effect.value = effectValue(ref, spellId, own.source, buffScale);
            effect.members = memberCount;

            // The party's other sources in effect now.
            std::vector<AuraRival> partyRivals;

            for (const uint32_t source : effectSources(ref))
            {
                const auto other = held.find(source);

                if (source != spellId && other != held.end() && other->second.active)
                {
                    partyRivals.push_back({source, other->second.holder, false,
                        effectValue(ref, source, other->second.source, buffScale)});
                }
            }

            for (size_t memberIndex = 0; memberIndex < memberCount; ++memberIndex)
            {
                std::vector<AuraRival> rivals = partyRivals;

                for (const uint32_t source : potionSources(ref))
                {
                    if (const std::optional<MawAuraSource> potion =
                            MawRules::potionAura(source, party.members()[memberIndex]))
                    {
                        rivals.push_back({source, memberIndex, true, effectValue(ref, source, *potion, buffScale)});
                    }
                }

                std::optional<AuraRival> stronger;

                for (const AuraRival &rival : rivals)
                {
                    if (covers(rival, spellId, effect.value) && (!stronger || rival.value > stronger->value))
                    {
                        stronger = rival;
                    }
                }

                AuraMemberBenefit &benefit = entry.members[memberIndex];

                if (stronger)
                {
                    if (!effect.stronger)
                    {
                        effect.stronger = stronger;
                    }

                    if (!benefit.coveredBy)
                    {
                        benefit.coveredBy = stronger;
                    }
                }
                else
                {
                    benefit.effects.push_back(effectIndex);
                    ++effect.membersUsing;
                }
            }

            usedEverywhere += effect.membersUsing == memberCount ? 1 : 0;
            usedNowhere += effect.membersUsing == 0 ? 1 : 0;
            entry.effects.push_back(std::move(effect));
        }

        for (AuraMemberBenefit &benefit : entry.members)
        {
            if (!benefit.effects.empty())
            {
                benefit.coveredBy.reset();
            }
        }

        if (entry.state == AuraState::Active && memberCount > 0)
        {
            entry.state = usedEverywhere == refs.size() ? AuraState::Active
                : usedNowhere == refs.size() ? AuraState::AddsNothing : AuraState::PartlyUsed;
        }

        // Moving it casts it as another member, or a member takes a blessing over.
        for (size_t memberIndex = 0; memberIndex < memberCount; ++memberIndex)
        {
            if (own.holder && *own.holder == memberIndex)
            {
                continue;
            }

            const Character &member = party.members()[memberIndex];
            const AuraMemberPool &pool = report.pools[memberIndex];
            AuraMoveOption option;
            option.memberIndex = memberIndex;
            option.knowsSpell = member.knowsSpell(spellId);
            option.cost = auraCost(party, memberIndex, spellId);
            option.freePoints = std::max(0, pool.maximum - pool.reserved);
            // A utility aura has to find its full cost free, before Enlightenment's discount, as castAura asks.
            const MawAura *pMoved = mawAura(spellId);
            const int needed =
                option.cost.flat && pMoved != nullptr ? int(mawRound(pMoved->cost)) : option.cost.points;
            option.fits = option.cost.free || needed <= option.freePoints;
            option.conscious = pool.conscious;
            entry.moveTo.push_back(option);
        }

        report.auras.push_back(std::move(entry));
    }

    std::sort(report.auras.begin(), report.auras.end(),
        [](const AuraReportEntry &left, const AuraReportEntry &right)
        {
            const size_t leftHolder = left.holder.value_or(SIZE_MAX);
            const size_t rightHolder = right.holder.value_or(SIZE_MAX);
            return leftHolder != rightHolder ? leftHolder < rightHolder : left.spellId < right.spellId;
        });
    return report;
}
}
