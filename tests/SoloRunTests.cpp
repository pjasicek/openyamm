#include "game/content/RulesetOptions.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/ui/GameplayPortraitGems.h"
#include "game/ui/SoloBarSelectorModel.h"
#include "game/ui/SoloHudLayout.h"

#include <doctest/doctest.h>

#include <chrono>
#include <filesystem>
#include <optional>
#include <string>

using namespace OpenYAMM::Game;

TEST_CASE("solo run: the option id turns it on and the badge names it in every ruleset")
{
    RulesetOptions options;
    CHECK_FALSE(options.soloRun);
    REQUIRE(applyRulesetOptionIds("solo", options));
    CHECK(options.soloRun);

    RulesetSelection standard;
    CHECK(describeRulesetSelection(standard, "").empty());
    standard.options.soloRun = true;
    CHECK(describeRulesetSelection(standard, "") == "Solo run");

    RulesetSelection maw;
    maw.id = "maw";
    maw.options.soloRun = true;
    CHECK(describeRulesetSelection(maw, "MAW").find("Solo run") != std::string::npos);
}

TEST_CASE("solo run: a save keeps the flag and the action bar; a party game stays a party game")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.ruleset.options.soloRun = true;
    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    Character &member = *party.member(0);
    member.actionBar[0] = {ActionBarSlotKind::Weapon, 0, {}};
    member.actionBar[1] = {ActionBarSlotKind::Spell, 2, {}};
    member.actionBar[9] = {ActionBarSlotKind::Item, 0, {222, QuickItemBottleRule::Strongest}};
    member.actionBar[12] = {ActionBarSlotKind::Talent, 7, {}};
    save.party = party.snapshot();

    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / ("openyamm_solo_run_save_" + std::to_string(ticks) + ".oysav");
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    const std::optional<GameSaveSummary> summary = loadGameSaveSummaryFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    CHECK(loaded->ruleset.options.soloRun);
    REQUIRE(summary.has_value());
    CHECK(summary->ruleset.options.soloRun);
    REQUIRE_FALSE(loaded->party.members.empty());
    CHECK(loaded->party.members.front().actionBar == member.actionBar);

    GameSaveData partyGame;
    partyGame.mapFileName = "oute3.odm";
    partyGame.party = party.snapshot();
    REQUIRE_MESSAGE(saveGameDataToPath(path, partyGame, error), error);
    const std::optional<GameSaveData> loadedParty = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE(loadedParty.has_value());
    CHECK_FALSE(loadedParty->ruleset.options.soloRun);
}

TEST_CASE("solo run: a new character's bar holds the weapon first, then its spells in book order")
{
    Character member;
    member.knownSpellIds = {11, 2, 5};
    member.actionBar[2] = {ActionBarSlotKind::Item, 0, {222, QuickItemBottleRule::Weakest}};
    prefillSoloActionBar(member);
    CHECK(member.actionBar[0].kind == ActionBarSlotKind::Weapon);
    CHECK(member.actionBar[1] == ActionBarSlot{ActionBarSlotKind::Spell, 2, {}});
    CHECK(member.actionBar[2].kind == ActionBarSlotKind::Item);
    CHECK(member.actionBar[3] == ActionBarSlot{ActionBarSlotKind::Spell, 5, {}});
    CHECK(member.actionBar[4] == ActionBarSlot{ActionBarSlotKind::Spell, 11, {}});
    CHECK(member.actionBar[5].kind == ActionBarSlotKind::Empty);

    // A second pass adds nothing twice.
    const std::array<ActionBarSlot, ActionBarSlotCount> before = member.actionBar;
    prefillSoloActionBar(member);
    CHECK(member.actionBar == before);
}

TEST_CASE("solo hud: the bar's panel size decides its grid and the keys")
{
    const SoloActionBarGrid twoByFive = soloActionBarGrid(175.3f, 81.7f, 27.7f, 3.2f, 4.3f, 12, 11);
    CHECK(twoByFive.columns == 5);
    CHECK(twoByFive.rows == 2);
    CHECK(soloActionBarSlotAt(twoByFive, 0, 0) == 0);
    CHECK(soloActionBarSlotAt(twoByFive, 1, 4) == 9);
    CHECK(soloActionSlotRect(twoByFive, 1, 1).x == doctest::Approx(12 + 27.7f + 3.2f));
    CHECK(soloActionSlotRect(twoByFive, 1, 1).y == doctest::Approx(11 + 27.7f + 4.3f));

    const SoloActionBarGrid oneRow = soloActionBarGrid(334, 49.7f, 27.7f, 3.2f, 4.3f, 12, 11);
    CHECK(oneRow.columns == 10);
    CHECK(oneRow.rows == 1);
    CHECK(soloActionBarSlotAt(oneRow, 0, 9) == 9);

    // Two rows of ten: the main row (keys 1-0) at the bottom, the second row above.
    const SoloActionBarGrid twoByTen = soloActionBarGrid(334, 81.7f, 27.7f, 3.2f, 4.3f, 12, 11);
    CHECK(twoByTen.columns == 10);
    CHECK(twoByTen.rows == 2);
    CHECK(soloActionBarSlotAt(twoByTen, 1, 0) == 0);
    CHECK(soloActionBarSlotAt(twoByTen, 0, 0) == 10);
    CHECK(soloActionBarKeyOfSlot(9) == std::optional<size_t>(9));
    CHECK_FALSE(soloActionBarKeyOfSlot(10).has_value());
}

TEST_CASE("solo hud: recovery and buff sweeps run from 0 to 1")
{
    CHECK(soloRecoveryProgress(0, 1.2f) == doctest::Approx(1));
    CHECK(soloRecoveryProgress(0.3f, 1.2f) == doctest::Approx(0.75f));
    CHECK(soloRecoveryProgress(2, 1.2f) == doctest::Approx(0));
    CHECK(soloRecoveryProgress(0.5f, 0) == doctest::Approx(1));
    CHECK(soloBuffSpent(30, 120) == doctest::Approx(0.75f));
    CHECK(soloBuffSpent(10, 0) == doctest::Approx(0));

    // The unit frame's medallion overlaps the box's left end and the bars sit inside the box.
    const SoloUnitFrameLayout layout = soloUnitFrameLayout();
    CHECK(layout.box.x < layout.medallion.x + layout.medallion.width);
    CHECK(layout.health.x + layout.health.width <= layout.box.x + layout.box.width);
    CHECK(layout.mana.y + layout.mana.height <= layout.box.y + layout.box.height);

    // The class counter's gems sit on the box's top edge, right of the weapon socket, over the name row and under
    // the frame's top; ten gems with a two-digit badge stay inside the box's width.
    for (int pips : {5, 10})
    {
        const std::vector<PortraitGemPlace> gems = counterGemRowPlaces(pips, layout.counterX, layout.counterY);
        REQUIRE(gems.size() == size_t(pips));
        CHECK(gems.front().x - gems.front().radius > layout.weapon.x + layout.weapon.width);
        CHECK(gems.front().y - gems.front().radius > 0);
        CHECK(gems.front().y + gems.front().radius < layout.name.y);
    }
    const PortraitGemPlace badge = counterGemRowBadgePlace(10, 18.0f, 9.2f, layout.counterX, layout.counterY);
    CHECK(badge.x + 9.0f < layout.box.x + layout.box.width);
}

TEST_CASE("solo run: a recovery's total is the longest applied since the member was ready")
{
    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE(party.applyRecoveryToMember(0, 1.0f));
    CHECK(party.member(0)->recoveryTotalSeconds == doctest::Approx(1.0f));
    REQUIRE(party.applyRecoveryToMember(0, 0.5f));
    CHECK(party.member(0)->recoveryTotalSeconds == doctest::Approx(1.0f));
    party.member(0)->recoverySecondsRemaining = 0;
    REQUIRE(party.applyRecoveryToMember(0, 0.4f));
    CHECK(party.member(0)->recoveryTotalSeconds == doctest::Approx(0.4f));
}

TEST_CASE("solo hud: a panel one slot wide is the left column of keys 1-0")
{
    // gameplay.yml's SoloActionBar: 64 px slots at 1600 x 900, keys 1-0 top to bottom.
    const SoloActionBarGrid column = soloActionBarGrid(51.2f, 382.4f, 34.13f, 2.67f, 2.67f, 8.53f, 8.53f);
    CHECK(column.columns == 1);
    CHECK(column.rows == 10);
    CHECK(soloActionBarSlotAt(column, 0, 0) == 0);
    CHECK(soloActionBarSlotAt(column, 9, 0) == 9);
    CHECK(soloActionSlotRect(column, 9, 0).y + column.slot <= doctest::Approx(382.4f - 8.53f + 0.01f));

    // The scroll and potion sockets sit on the medallion's upper-left rim, clear of the coin at its foot.
    const SoloUnitFrameLayout layout = soloUnitFrameLayout();
    CHECK(layout.scrollSocket.x < layout.medallion.x);
    CHECK(layout.potionSocket.y + layout.potionSocket.height < layout.coin.y);
}

TEST_CASE("solo run: hits, heals and conditions queue self combat text, at most sixteen")
{
    Party party;
    party.seed(Party::createDefaultSeed());
    Character &member = *party.member(0);
    member.health = member.maxHealth = 200;
    REQUIRE(party.applyDamageToMember(0, 30, ""));
    REQUIRE(party.healMember(0, 10));
    REQUIRE(party.applyMemberCondition(0, CharacterCondition::Weak));
    REQUIRE(party.clearMemberCondition(0, CharacterCondition::Weak));
    const std::vector<Party::SelfTextEvent> events = party.takeSelfTextEvents();
    REQUIRE(events.size() == 4);
    CHECK(events[0].kind == Party::SelfTextEvent::Kind::Damage);
    CHECK(events[0].amount == 30);
    CHECK(events[1].kind == Party::SelfTextEvent::Kind::Heal);
    CHECK(events[1].amount == 10);
    CHECK(events[2].kind == Party::SelfTextEvent::Kind::ConditionGained);
    CHECK(events[3].kind == Party::SelfTextEvent::Kind::ConditionCleared);
    CHECK(party.takeSelfTextEvents().empty());

    // A regeneration tick is its own kind, so the HUD can sum the ticks into one line.
    REQUIRE(party.healMember(0, 3, true));
    const std::vector<Party::SelfTextEvent> ticks = party.takeSelfTextEvents();
    REQUIRE(ticks.size() == 1);
    CHECK(ticks[0].kind == Party::SelfTextEvent::Kind::Regeneration);
    CHECK(ticks[0].amount == 3);

    for (int hit = 0; hit < 20; ++hit)
    {
        party.applyDamageToMember(0, 1, "");
    }
    CHECK(party.takeSelfTextEvents().size() == 16);
}

namespace
{
std::vector<SoloBarSelectorEntry> selectorEntries()
{
    const auto entry = [](ActionBarSlot slot, SoloBarSelectorTab category, const char *pName)
    {
        SoloBarSelectorEntry result;
        result.slot = slot;
        result.category = category;
        result.name = pName;
        return result;
    };
    return {
        entry({ActionBarSlotKind::Spell, 2, {}}, SoloBarSelectorTab::Spells, "Fire Bolt"),
        entry({ActionBarSlotKind::Spell, 4, {}}, SoloBarSelectorTab::Spells, "Torch Light"),
        entry({ActionBarSlotKind::Item, 0, {222, QuickItemBottleRule::Weakest}}, SoloBarSelectorTab::Potions,
            "Cure Wounds"),
        entry({ActionBarSlotKind::Item, 0, {300, QuickItemBottleRule::Weakest}}, SoloBarSelectorTab::Scrolls,
            "Fire Bolt scroll"),
        entry({ActionBarSlotKind::Weapon, 0, {}}, SoloBarSelectorTab::Actions, "Attack"),
    };
}
}

TEST_CASE("solo run: the slot selector filters by tab and by a case-insensitive part of the name")
{
    const std::vector<SoloBarSelectorEntry> entries = selectorEntries();

    // All: each category under its heading, in tab order; no heading for an empty category (Talents).
    const std::vector<SoloBarSelectorRow> all = soloBarSelectorRows(entries, SoloBarSelectorTab::All, "");
    REQUIRE(all.size() == 9);
    CHECK(all[0] == SoloBarSelectorRow{true, SoloBarSelectorTab::Spells, 0});
    CHECK(all[1] == SoloBarSelectorRow{false, SoloBarSelectorTab::Spells, 0});
    CHECK(all[2] == SoloBarSelectorRow{false, SoloBarSelectorTab::Spells, 1});
    CHECK(all[3].heading);
    CHECK(all[3].category == SoloBarSelectorTab::Potions);
    CHECK(all[7] == SoloBarSelectorRow{true, SoloBarSelectorTab::Actions, 0});
    CHECK(all[8].entry == 4);

    // One tab: its entries, no headings.
    const std::vector<SoloBarSelectorRow> spells = soloBarSelectorRows(entries, SoloBarSelectorTab::Spells, "");
    REQUIRE(spells.size() == 2);
    CHECK_FALSE(spells[0].heading);
    CHECK(spells[1].entry == 1);

    // The search: any part of the name, whatever its case; under All only the categories with a match.
    const std::vector<SoloBarSelectorRow> fire = soloBarSelectorRows(entries, SoloBarSelectorTab::All, "fIRE");
    REQUIRE(fire.size() == 4);
    CHECK(fire[1].entry == 0);
    CHECK(fire[2].category == SoloBarSelectorTab::Scrolls);
    CHECK(fire[3].entry == 3);
    CHECK(soloBarSelectorRows(entries, SoloBarSelectorTab::Potions, "fire").empty());
    CHECK(soloBarSelectorRows(entries, SoloBarSelectorTab::Spells, "light").size() == 1);
    CHECK(soloBarSelectorRows(entries, SoloBarSelectorTab::All, "nothing").empty());

    // Tabs without entries are disabled; All has everything.
    CHECK(soloBarSelectorTabHasEntries(entries, SoloBarSelectorTab::All));
    CHECK(soloBarSelectorTabHasEntries(entries, SoloBarSelectorTab::Scrolls));
    CHECK_FALSE(soloBarSelectorTabHasEntries(entries, SoloBarSelectorTab::Talents));
    CHECK_FALSE(soloBarSelectorTabHasEntries({}, SoloBarSelectorTab::All));
}

TEST_CASE("solo run: the slot selector puts a thing on a key, moves it from another key, and empties a key")
{
    std::array<ActionBarSlot, ActionBarSlotCount> bar = {};
    const ActionBarSlot fireBolt = {ActionBarSlotKind::Spell, 2, {}};
    const ActionBarSlot potion = {ActionBarSlotKind::Item, 0, {222, QuickItemBottleRule::Weakest}};
    const ActionBarSlot strongPotion = {ActionBarSlotKind::Item, 0, {222, QuickItemBottleRule::Strongest}};
    bar[1] = fireBolt;
    bar[2] = {ActionBarSlotKind::Weapon, 0, {}};

    // A new thing on an empty key.
    soloBarAssign(bar, 5, potion);
    CHECK(bar[5] == potion);
    CHECK(soloBarKeyOf(bar, potion) == 5u);
    // The same kind of potion (whatever bottle it drinks first) is the same thing: it moves.
    CHECK(soloBarSameEntry(potion, strongPotion));
    soloBarAssign(bar, 7, strongPotion);
    CHECK(bar[5].kind == ActionBarSlotKind::Empty);
    CHECK(bar[7] == strongPotion);

    // A spell moved onto a full key replaces what was there and leaves its old key empty.
    soloBarAssign(bar, 2, fireBolt);
    CHECK(bar[1].kind == ActionBarSlotKind::Empty);
    CHECK(bar[2] == fireBolt);
    CHECK(soloBarKeyOf(bar, {ActionBarSlotKind::Weapon, 0, {}}) == std::nullopt);

    // The same thing on its own key stays; a different spell or the swap slot is not the same thing.
    soloBarAssign(bar, 2, fireBolt);
    CHECK(bar[2] == fireBolt);
    CHECK_FALSE(soloBarSameEntry(fireBolt, {ActionBarSlotKind::Spell, 3, {}}));
    CHECK_FALSE(soloBarSameEntry({ActionBarSlotKind::Weapon, 0, {}}, {ActionBarSlotKind::Weapon, 1, {}}));
    CHECK_FALSE(soloBarSameEntry({}, {}));

    // Emptying a key touches no other.
    soloBarAssign(bar, 2, {});
    CHECK(bar[2].kind == ActionBarSlotKind::Empty);
    CHECK(bar[7] == strongPotion);
    soloBarAssign(bar, ActionBarSlotCount, fireBolt);
    CHECK(soloBarKeyOf(bar, fireBolt) == std::nullopt);
}
