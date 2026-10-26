#include "tests/AssetTestSupport.h"
#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "game/mm9/Mm9QuestMarkers.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/party/Party.h"
#include "game/render/QuestMarkerGeometry.h"
#include "game/tables/JournalQuestTable.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace
{
std::string rudeRow(int32_t rudeId, int32_t nodeId, int32_t choiceSlot, int32_t next,
                    std::initializer_list<std::pair<size_t, int32_t>> fields = {})
{
    std::vector<std::string> columns(30, "0");
    columns[0] = std::to_string(rudeId);
    columns[1] = std::to_string(nodeId);
    columns[2] = std::to_string(choiceSlot);
    columns[3] = "Prompt";
    columns[4] = "Response";
    columns[5] = std::to_string(next);
    for (const std::pair<size_t, int32_t> &field : fields)
    {
        columns.at(field.first - 1) = std::to_string(field.second);
    }
    std::string result;
    for (size_t index = 0; index < columns.size(); ++index)
    {
        result += (index == 0 ? "" : ",") + columns[index];
    }
    return result + '\n';
}

std::string interaction(const std::string &id, size_t rowIndex, const std::string &roles,
                        const std::string &activatedEntries, const std::string &completedEntries)
{
    return "  - id: " + id +
           "\n"
           "    rude_id: 1\n"
           "    bindings:\n"
           "      - map_id: testmap\n"
           "        source_object_index: 7\n"
           "    journal_entries: [90001]\n"
           "    roles: " +
           roles +
           "\n"
           "    conditions:\n"
           "      available:\n"
           "        activates_journal_entries: " +
           activatedEntries +
           "\n"
           "      ready:\n"
           "        active_journal_entries: " +
           completedEntries +
           "\n"
           "    provenance:\n"
           "      row_index: " +
           std::to_string(rowIndex) + "\n";
}

std::string metadata(const std::string &interactions)
{
    return "format_version: 1\n"
           "world: mm9\n"
           "interactions:\n" +
           interactions;
}

std::string scrInteraction()
{
    return "  - id: scr-handoff\n"
           "    source_kind: scr\n"
           "    rude_id: 1\n"
           "    bindings: [{map_id: testmap, source_object_index: 7}]\n"
           "    journal_entries: [90001]\n"
           "    roles: [handoff]\n"
           "    conditions:\n"
           "      scr_predicate:\n"
           "        required_qbits: [90030]\n"
           "        forbidden_qbits: [90040]\n"
           "        any_required_qbits: []\n"
           "        minimum_gold: 500\n"
           "      available: {activates_journal_entries: []}\n"
           "      ready: {active_journal_entries: [90001]}\n"
           "    provenance: {source: NPC1.scr, source_lines: [10]}\n";
}

OpenYAMM::Game::JournalQuestTable questTable()
{
    OpenYAMM::Game::JournalQuestTable table;
    const bool loaded = table.loadFromRows({
        {"90001", "Test quest", "", "MM9", "90010", "90020"},
    });
    REQUIRE(loaded);
    return table;
}
} // namespace

TEST_CASE("MM9 quest marker resolver performs the full available in-progress "
          "ready none sequence")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rudeRow(1, 1, 1, -1, {{16, 10}, {21, 10}}) +
                                                        rudeRow(1, 1, 2, -1, {{7, 10}, {9, 30}, {16, 20}})));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(interaction("offer", 0, "[offer]", "[90001]", "[]") +
                                                           interaction("handoff", 1, "[handoff]", "[]", "[90001]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;
    const OpenYAMM::Game::Mm9QuestActorIdentity actor = {"testmap", 7, 1, true};

    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::Available);
    party.setQuestBit(90010, true);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::InProgress);
    party.setQuestBit(90030, true);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    party.setQuestBit(90020, true);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::None);
}

TEST_CASE("MM9 quest marker resolver previews nested RUDE path effects without "
          "mutating party state")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude",
                                       rudeRow(1, 1, 1, 5, {{16, 40}}) + rudeRow(1, 5, 1, -1, {{7, 40}, {16, 10}})));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(
        interactionTable.loadText("test.yml", metadata(interaction("nested-offer", 1, "[offer]", "[90001]", "[]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    const uint64_t revision = party.dialogueEligibilityRevision();

    CHECK(OpenYAMM::Game::Mm9QuestMarkerResolver().markerFor({"testmap", 7, 1, true}, party, journalTable, rudeTable,
                                                             interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::Available);
    CHECK_FALSE(party.hasQuestBit(90040));
    CHECK(party.dialogueEligibilityRevision() == revision);
}

TEST_CASE("MM9 quest marker state priority and actor eligibility are centralized")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude",
                                       rudeRow(1, 1, 1, -1, {{16, 10}}) + rudeRow(1, 1, 2, -1, {{7, 10}, {16, 20}})));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(interaction("offer", 0, "[offer]", "[90001]", "[]") +
                                                           interaction("handoff", 1, "[handoff]", "[]", "[90001]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    party.setQuestBit(90010, true);
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;

    CHECK(resolver.markerFor({"testmap", 7, 1, true}, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    CHECK(resolver.markerFor({"testmap", 7, 1, false}, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::None);
    CHECK(resolver.markerFor({"othermap", 7, 1, true}, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::None);
}

TEST_CASE("Party dialogue eligibility revision changes only for actual "
          "relevant mutations")
{
    OpenYAMM::Game::Party party;
    const uint64_t initial = party.dialogueEligibilityRevision();
    party.setQuestBit(90010, false);
    CHECK(party.dialogueEligibilityRevision() == initial);
    party.setQuestBit(90010, true);
    CHECK(party.dialogueEligibilityRevision() == initial + 1);
    party.setQuestBit(90010, true);
    CHECK(party.dialogueEligibilityRevision() == initial + 1);
    party.setQuestBit(90010, false);
    CHECK(party.dialogueEligibilityRevision() == initial + 2);
    party.addGold(0);
    CHECK(party.dialogueEligibilityRevision() == initial + 2);
    party.addGold(500);
    CHECK(party.dialogueEligibilityRevision() == initial + 3);
}

TEST_CASE("MM9 pure SCR predicates distinguish incomplete and actionable handoffs")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rudeRow(1, 1, 1, -1)));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(scrInteraction())));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    party.setQuestBit(90010, true);
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;
    const OpenYAMM::Game::Mm9QuestActorIdentity actor = {"testmap", 7, 1, true};

    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::InProgress);
    party.setQuestBit(90030, true);
    party.addGold(499);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::InProgress);
    party.addGold(1);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    party.setQuestBit(90040, true);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::InProgress);
}

TEST_CASE("MM9 quest marker presentation data keeps marker semantics distinct "
          "and distance bounded")
{
    using OpenYAMM::Game::Mm9QuestMarkerState;

    CHECK(OpenYAMM::Game::questMarkerTextureName(Mm9QuestMarkerState::Available) == "quest_marker_exclamation");
    CHECK(OpenYAMM::Game::questMarkerTextureName(Mm9QuestMarkerState::InProgress) == "quest_marker_question");
    CHECK(OpenYAMM::Game::questMarkerTextureName(Mm9QuestMarkerState::Ready) == "quest_marker_question");
    CHECK(OpenYAMM::Game::questMarkerTextureName(Mm9QuestMarkerState::None).empty());
    CHECK(OpenYAMM::Game::questMarkerColorAbgr(Mm9QuestMarkerState::InProgress, 255) !=
          OpenYAMM::Game::questMarkerColorAbgr(Mm9QuestMarkerState::Ready, 255));
    CHECK(OpenYAMM::Game::questMarkerAlpha(3500.0f) == 255);
    CHECK(OpenYAMM::Game::questMarkerAlpha(4500.0f) > 0);
    CHECK(OpenYAMM::Game::questMarkerAlpha(5500.0f) == 0);
    CHECK(OpenYAMM::Game::questMarkerWorldScale(0.0f) == 42.0f);
    CHECK(OpenYAMM::Game::questMarkerWorldScale(10000.0f) == 92.0f);
    CHECK(OpenYAMM::Game::questMarkerHalfExtent(42.0f) == doctest::Approx(25.2f));
    CHECK(OpenYAMM::Game::questMarkerOriginOffset(42.0f) == doctest::Approx(29.1f));
}

TEST_CASE("MM9 quest marker sprite assets resolve through the mounted world"
    * OpenYAMM::Tests::requiresMm9Assets())
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Engine::DirectoryAssetPathCache directoryCache;
    OpenYAMM::Engine::AssetPathLookupCache pathCache;
    OpenYAMM::Engine::BinaryAssetCache binaryCache;
    for (const std::string &textureName : {"quest_marker_exclamation", "quest_marker_question"})
    {
        const std::optional<OpenYAMM::Engine::ImagePixelsBgra> image =
            OpenYAMM::Engine::loadImageAssetPixelsBgra(
                assetFileSystem,
                "Data/sprites",
                textureName,
                directoryCache,
                pathCache,
                binaryCache);
        REQUIRE(image.has_value());
        CHECK(image->width == 256);
        CHECK(image->height == 256);

        bool hasTransparentPixel = false;
        bool hasOpaquePixel = false;
        for (size_t pixelOffset = 3; pixelOffset < image->pixels.size(); pixelOffset += 4)
        {
            hasTransparentPixel |= image->pixels[pixelOffset] == 0;
            hasOpaquePixel |= image->pixels[pixelOffset] == 255;
        }
        CHECK(hasTransparentPixel);
        CHECK(hasOpaquePixel);
    }
}

TEST_CASE("Checked-in MM9 quest interaction metadata loads through the runtime "
          "schema"
    * OpenYAMM::Tests::requiresMm9Assets())
{
    const std::filesystem::path path =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/state/quest_interactions.yml";
    std::ifstream input(path);
    REQUIRE(input.is_open());
    std::ostringstream text;
    text << input.rdbuf();
    OpenYAMM::Game::Mm9QuestInteractionTable table;

    REQUIRE(table.loadText(path.string(), text.str()));
    CHECK(table.errors().empty());
    CHECK(table.interactions().size() == 125);
    CHECK(std::count_if(
              table.interactions().begin(), table.interactions().end(),
              [](const OpenYAMM::Game::Mm9QuestInteraction &interaction) { return interaction.scrPredicate; }) == 21);
}

TEST_CASE("MM9 service rows cannot be classified as quest interactions")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rudeRow(1, 1, 1, -4, {{16, 10}})));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(interaction("service", 0, "[offer]", "[90001]", "[]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;

    CHECK(OpenYAMM::Game::Mm9QuestMarkerResolver().markerFor({"testmap", 7, 1, true}, party, journalTable, rudeTable,
                                                             interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::None);
}

TEST_CASE("MM9 loaded-location marker cache coalesces mutations and has no "
          "non-MM9 work")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rudeRow(1, 1, 1, -1, {{16, 10}, {21, 10}}) +
                                                        rudeRow(1, 1, 2, -1, {{7, 10}, {9, 30}, {16, 20}})));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(interaction("offer", 0, "[offer]", "[90001]", "[]") +
                                                           interaction("handoff", 1, "[handoff]", "[]", "[90001]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    const std::vector<OpenYAMM::Game::Mm9LoadedQuestMarkerActor> actors = {
        {42, {"testmap", 7, 1, true}},
    };
    OpenYAMM::Game::Mm9LoadedLocationQuestMarkerCache cache;

    cache.loadLocation(false, actors, {party.dialogueEligibilityRevision(), 1}, party, journalTable, rudeTable,
                       interactionTable);
    CHECK_FALSE(cache.active());
    CHECK(cache.rebuildCount() == 0);

    cache.loadLocation(true, actors, {party.dialogueEligibilityRevision(), 1}, party, journalTable, rudeTable,
                       interactionTable);
    CHECK(cache.markerForActor(42) == OpenYAMM::Game::Mm9QuestMarkerState::Available);
    CHECK(cache.rebuildCount() == 1);
    CHECK_FALSE(cache.update(actors, {party.dialogueEligibilityRevision(), 1}, party, journalTable, rudeTable,
                             interactionTable));
    CHECK(cache.rebuildCount() == 1);

    party.setQuestBit(90010, true);
    party.setQuestBit(90030, true);
    CHECK(cache.rebuildCount() == 1);
    CHECK(cache.update(actors, {party.dialogueEligibilityRevision(), 1}, party, journalTable, rudeTable,
                       interactionTable));
    CHECK(cache.markerForActor(42) == OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    CHECK(cache.rebuildCount() == 2);

    std::vector<OpenYAMM::Game::Mm9LoadedQuestMarkerActor> hiddenActors = actors;
    hiddenActors[0].identity.interactable = false;
    CHECK(cache.update(hiddenActors, {party.dialogueEligibilityRevision(), 2}, party, journalTable, rudeTable,
                       interactionTable));
    CHECK(cache.markerForActor(42) == OpenYAMM::Game::Mm9QuestMarkerState::None);
}

TEST_CASE("MM9 marker cache rebuilds from restored party state and discards the previous map")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText(
        "NPC1.rude",
        rudeRow(1, 1, 1, -1, {{16, 10}, {21, 10}})
            + rudeRow(1, 1, 2, -1, {{7, 10}, {9, 30}, {16, 20}})));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText(
        "test.yml",
        metadata(
            interaction("offer", 0, "[offer]", "[90001]", "[]")
            + interaction("handoff", 1, "[handoff]", "[]", "[90001]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    const std::vector<OpenYAMM::Game::Mm9LoadedQuestMarkerActor> actors = {
        {42, {"testmap", 7, 1, true}},
    };
    OpenYAMM::Game::Mm9LoadedLocationQuestMarkerCache cache;
    cache.loadLocation(
        true,
        actors,
        {party.dialogueEligibilityRevision(), 10},
        party,
        journalTable,
        rudeTable,
        interactionTable);
    CHECK(cache.markerForActor(42) == OpenYAMM::Game::Mm9QuestMarkerState::Available);

    OpenYAMM::Game::Party::Snapshot restored = party.snapshot();
    restored.questBits.insert(90010);
    restored.questBits.insert(90030);
    party.restoreSnapshot(restored);
    REQUIRE(cache.update(
        actors,
        {party.dialogueEligibilityRevision(), 10},
        party,
        journalTable,
        rudeTable,
        interactionTable));
    CHECK(cache.markerForActor(42) == OpenYAMM::Game::Mm9QuestMarkerState::Ready);

    cache.clear();
    const std::vector<OpenYAMM::Game::Mm9LoadedQuestMarkerActor> nextMapActors = {
        {42, {"nextmap", 7, 1, true}},
    };
    cache.loadLocation(
        true,
        nextMapActors,
        {party.dialogueEligibilityRevision(), 11},
        party,
        journalTable,
        rudeTable,
        interactionTable);
    CHECK(cache.markerForActor(42) == OpenYAMM::Game::Mm9QuestMarkerState::None);
}
