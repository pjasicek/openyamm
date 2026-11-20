#include "doctest/doctest.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawRules.h"
#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <optional>

using namespace OpenYAMM::Game;

// The aura panel's report (SpellRules::auraReport, level_generation/ui/maw_aura_panel_20261025 A).
namespace
{
const AuraReportEntry *findAura(const AuraReport &report, uint32_t spellId)
{
    const auto it = std::find_if(report.auras.begin(), report.auras.end(),
        [spellId](const AuraReportEntry &entry)
        {
            return entry.spellId == spellId;
        });
    return it != report.auras.end() ? &*it : nullptr;
}

// Ariel (Knight), Brom a Light Grandmaster of level 92, Cedric an Earth Master of level 80, Daria a Fire
// Grandmaster of level 120, each with 1000 spell points.
Party makeAuraParty(const OpenYAMM::Tests::RegressionGameData &gameData)
{
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    const auto caster = [&party](size_t index, uint32_t level)
    {
        Character &member = *party.member(index);
        member.level = level;
        member.maxSpellPoints = 1000;
        member.spellPoints = 1000;
        return &member;
    };
    caster(1, 92)->skills["LightMagic"] = {"LightMagic", 30, SkillMastery::Grandmaster};
    Character *pDruid = caster(2, 80);
    pDruid->skills["EarthMagic"] = {"EarthMagic", 25, SkillMastery::Master};
    pDruid->skills["FireMagic"] = {"FireMagic", 15, SkillMastery::Expert};
    Character *pSorcerer = caster(3, 120);
    pSorcerer->skills["FireMagic"] = {"FireMagic", 60, SkillMastery::Grandmaster};
    pSorcerer->learnSpell(38);
    return party;
}
}

TEST_CASE("MAW's aura report: holders, reservations, strengths and the stronger sources (H.6 aura panel)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = makeAuraParty(gameData);
    party.setRules(&rules.gameRules());
    const SpellRules &spells = rules.gameRules().spells;

    // Standard has no auras and no panel.
    CHECK_FALSE(standardGameRules().spells.auraReport(party).has_value());

    rules.state().auraHolders = {{86, 1}, {38, 2}, {3, 2}, {5, 3}, {27, MawGameState::FixedAuraHolder}};
    rules.state().fixedAuraMaps = {{27, "oute3.odm"}};
    std::optional<AuraReport> report = spells.auraReport(party);
    REQUIRE(report.has_value());

    // By holder in party order, each holder's by spell id, the blessing last.
    REQUIRE_EQ(report->auras.size(), 5u);
    CHECK_EQ(report->auras[0].spellId, 86u);
    CHECK_EQ(report->auras[1].spellId, 3u);
    CHECK_EQ(report->auras[2].spellId, 38u);
    CHECK_EQ(report->auras[3].spellId, 5u);
    CHECK_EQ(report->auras[4].spellId, 27u);

    // Reservations as the spell rules hold them, per aura and per member.
    const AuraReportEntry &stoneSkin = *findAura(*report, 38);
    CHECK_EQ(stoneSkin.holder, std::optional<size_t>(2));
    CHECK_FALSE(stoneSkin.cost.flat);
    CHECK(stoneSkin.cost.percent > 0);
    CHECK_EQ(stoneSkin.cost.points, int(std::ceil(1000 * stoneSkin.cost.percent / 100)));
    REQUIRE_EQ(report->pools.size(), 4u);
    CHECK_EQ(report->pools[2].reserved, spells.reservedSpellPoints(party, 2));
    CHECK_EQ(report->pools[2].maximum, 1000);
    CHECK_EQ(report->reservedSpellPoints,
        spells.reservedSpellPoints(party, 1) + spells.reservedSpellPoints(party, 2)
            + spells.reservedSpellPoints(party, 3));
    CHECK_EQ(report->reservedHitPoints, 0);

    // Stone Skin +60 at Earth 25, level 80 adds nothing under Hour of Power's +60.2 (Light 30 / 1.5, level 92).
    CHECK_EQ(stoneSkin.skill, 25.0);
    CHECK_EQ(stoneSkin.mastery, int(SkillMastery::Master));
    REQUIRE_EQ(stoneSkin.effects.size(), 1u);
    CHECK_EQ(stoneSkin.effects[0].value, doctest::Approx(mawAuraFlat(20, 2, 80, 25)));
    CHECK_EQ(stoneSkin.effects[0].membersUsing, 0u);
    REQUIRE(stoneSkin.effects[0].stronger.has_value());
    CHECK_EQ(stoneSkin.effects[0].stronger->spellId, 86u);
    CHECK_EQ(stoneSkin.effects[0].stronger->memberIndex, std::optional<size_t>(1));
    CHECK_EQ(stoneSkin.effects[0].stronger->value, doctest::Approx(mawAuraFlat(20, 2, 92, 20)));
    CHECK_EQ(stoneSkin.state, AuraState::AddsNothing);
    CHECK(stoneSkin.members[0].effects.empty());
    REQUIRE(stoneSkin.members[0].coveredBy.has_value());
    CHECK_EQ(stoneSkin.members[0].coveredBy->spellId, 86u);

    // Hour of Power: Daria's Haste (Fire 50, the cap) beats its haste part; the rest is in use.
    const AuraReportEntry &hour = *findAura(*report, 86);
    CHECK_EQ(hour.state, AuraState::PartlyUsed);
    REQUIRE_EQ(hour.effects.size(), 4u);
    CHECK_EQ(hour.effects[0].membersUsing, 0u);
    CHECK_EQ(hour.effects[0].stronger->spellId, 5u);
    CHECK_EQ(hour.effects[1].membersUsing, 4u);
    CHECK_EQ(hour.effects[2].membersUsing, 4u);
    CHECK_EQ(hour.effects[3].membersUsing, 4u);
    CHECK_EQ(hour.members[2].effects, std::vector<size_t>{1, 2, 3});
    const AuraReportEntry &haste = *findAura(*report, 5);
    CHECK_EQ(haste.state, AuraState::Active);
    CHECK(haste.skillCapped);
    CHECK_EQ(haste.skill, 50.0);
    CHECK_EQ(findAura(*report, 3)->state, AuraState::Active);

    // The pedestal's Water Walk is a blessing of the place that reserves nothing.
    const AuraReportEntry &walk = *findAura(*report, 27);
    CHECK_FALSE(walk.holder.has_value());
    CHECK_EQ(walk.state, AuraState::Blessing);
    CHECK_FALSE(walk.templeBlessing);
    CHECK(walk.cost.free);
    CHECK_EQ(walk.skill, 7.0);

    // Moving Stone Skin: everyone but its holder, Daria knows it and it fits her free pool.
    REQUIRE_EQ(stoneSkin.moveTo.size(), 3u);
    const auto daria = std::find_if(stoneSkin.moveTo.begin(), stoneSkin.moveTo.end(),
        [](const AuraMoveOption &option)
        {
            return option.memberIndex == 3;
        });
    REQUIRE(daria != stoneSkin.moveTo.end());
    CHECK(daria->knowsSpell);
    CHECK(daria->fits);
    CHECK_EQ(daria->freePoints, 1000 - spells.reservedSpellPoints(party, 3));
    CHECK_FALSE(stoneSkin.moveTo[0].knowsSpell);

    // A strong Stone Skin potion makes Ariel's armour her own: Hour of Power's armour part reaches the other three.
    party.member(0)->rulesetState.potionEffects.push_back({TimedPotionEffect::Kind::Aura, 38, 200, 600});
    report = spells.auraReport(party);
    const AuraReportEntry &hourWithPotion = *findAura(*report, 86);
    CHECK_EQ(hourWithPotion.effects[2].membersUsing, 3u);
    CHECK(std::find(hourWithPotion.members[0].effects.begin(), hourWithPotion.members[0].effects.end(), size_t(2))
        == hourWithPotion.members[0].effects.end());
    REQUIRE(hourWithPotion.effects[2].stronger.has_value());
    CHECK(hourWithPotion.effects[2].stronger->potion);
    CHECK_EQ(hourWithPotion.effects[2].stronger->memberIndex, std::optional<size_t>(0));

    // An unconscious holder's auras are suspended and their reservation stays; they are no rival meanwhile.
    party.member(3)->conditions.set(size_t(CharacterCondition::Unconscious));
    report = spells.auraReport(party);
    CHECK_EQ(findAura(*report, 5)->state, AuraState::Suspended);
    CHECK_FALSE(report->pools[3].conscious);
    CHECK_EQ(report->pools[3].reserved, spells.reservedSpellPoints(party, 3));
    CHECK_EQ(findAura(*report, 86)->effects[0].membersUsing, 4u);

    // Releasing is the holder's toggle, unconscious or not; the report follows the holders.
    REQUIRE(spells.castAura(party, 3, 5) == AuraCastResult::Released);
    report = spells.auraReport(party);
    CHECK(findAura(*report, 5) == nullptr);
    CHECK_EQ(report->pools[3].reserved, 0);
}

TEST_CASE("MAW's aura report: Death Knights reserve nothing, utility auras reserve flat points")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = makeAuraParty(gameData);
    party.setRules(&rules.gameRules());
    party.member(0)->className = "DeathKnight";
    party.member(0)->skills["BodyMagic"] = {"BodyMagic", 10, SkillMastery::Expert};
    rules.state().auraHolders = {{69, 0}, {1, 2}};
    const std::optional<AuraReport> report = rules.gameRules().spells.auraReport(party);
    REQUIRE(report.has_value());

    const AuraReportEntry &body = *findAura(*report, 69);
    CHECK(body.cost.free);
    CHECK_EQ(body.cost.points, 0);
    CHECK(report->pools[0].reservesNothing);
    CHECK_EQ(report->pools[0].reserved, 0);

    // Torch Light reserves a flat number of points; its effect is words (the torch's power).
    const AuraReportEntry &torch = *findAura(*report, 1);
    CHECK(torch.cost.flat);
    CHECK_EQ(torch.cost.points, mawUtilityAuraReservation(5, 0));
    REQUIRE_EQ(torch.effects.size(), 1u);
    CHECK_EQ(torch.effects[0].kind, AuraValueKind::Text);
    CHECK_EQ(torch.state, AuraState::Active);
}

TEST_CASE("A quick-cast heal measures a legendary 32 wearer against the hit points its auras leave")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = makeAuraParty(gameData);
    party.setRules(&rules.gameRules());
    party.member(0)->skills["BodyMagic"] = {"BodyMagic", 10, SkillMastery::Grandmaster};

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        party.member(index)->maxHealth = 1000;
        party.member(index)->health = 1000;
    }

    // Cedric's Stone Skin holds hit points; he is full on what is left. Daria lacks 10.
    Character &cedric = *party.member(2);
    cedric.equipment.amulet = 1;
    cedric.equipmentRuntime.amulet.rulesetFields.legendaryAffixId = 32;
    rules.state().auraHolders = {{38, 2}};
    const int reserved = rules.gameRules().spells.reservedHitPoints(party, 2);
    REQUIRE_GT(reserved, 0);
    cedric.health = Party::effectiveMaximumHealth(cedric) - reserved;
    party.member(3)->health -= 10;
    CHECK_EQ(PartySpellSystem::quickCastCharacterTarget(party, 0, spellIdValue(SpellId::Heal), &gameData.spellTable),
        std::optional<size_t>(3));

    // Nobody else wounded: nobody to heal.
    party.member(3)->health += 10;
    CHECK_FALSE(
        PartySpellSystem::quickCastCharacterTarget(party, 0, spellIdValue(SpellId::Heal), &gameData.spellTable));

    // Regeneration and heals stop where the auras' share begins, so the clamp never pulls HP back (the gauge
    // flickered).
    CHECK_EQ(party.reachableMaximumHealth(2), cedric.health);
    cedric.health -= 5;
    cedric.healthRegenPerSecond = 100.0f;
    party.updateRecovery(1.0f);
    CHECK_EQ(cedric.health, party.reachableMaximumHealth(2));
    cedric.health -= 5;
    CHECK(party.healMember(2, 1000));
    CHECK_EQ(cedric.health, party.reachableMaximumHealth(2));
}
