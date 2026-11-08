#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "game/mm9/Mm9QuestMarkers.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9SkillTrainer.h"
#include "game/party/Party.h"
#include "game/render/QuestMarkerGeometry.h"
#include "game/tables/JournalQuestTable.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <chrono>
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

TEST_CASE("MM9 key interactions mark a journal-less quest by its quest keys")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rudeRow(1, 1, 1, -1)));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(
        "  - id: deal\n"
        "    source_kind: keys\n"
        "    rude_id: 1\n"
        "    bindings: [{map_id: testmap, source_object_index: 7}]\n"
        "    roles: [offer, handoff]\n"
        "    conditions:\n"
        "      keys:\n"
        "        available: {required_qbits: [], forbidden_qbits: [95004, 95006]}\n"
        "        in_progress: {required_qbits: [95004], forbidden_qbits: [90369]}\n"
        "        ready: {required_qbits: [90369], forbidden_qbits: [90370]}\n"
        "    provenance: {source: NPC1.rude}\n")));
    REQUIRE(interactionTable.errors().empty());
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;
    const OpenYAMM::Game::Mm9QuestActorIdentity actor = {"testmap", 7, 1, true};
    const auto marker = [&]() { return resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable); };

    CHECK(marker() == OpenYAMM::Game::Mm9QuestMarkerState::Available);
    party.setQuestBit(95006, true);
    CHECK(marker() == OpenYAMM::Game::Mm9QuestMarkerState::None);
    party.setQuestBit(95006, false);
    party.setQuestBit(95004, true);
    CHECK(marker() == OpenYAMM::Game::Mm9QuestMarkerState::InProgress);
    party.setQuestBit(90369, true);
    CHECK(marker() == OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    party.setQuestBit(90370, true);
    CHECK(marker() == OpenYAMM::Game::Mm9QuestMarkerState::None);
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

TEST_CASE("MM9 quest marker path search ignores keys that no row tests")
{
    // Node 1 loops through 18 rows that each grant a key no row tests (raw 100-117), like the promotion keys of
    // Sturmford's Tyralt (RUDE 61): counted in the search states they made 2^18 of them (a 400 ms hitch per marker
    // rebuild there). One more row grants the tested key 40 and leads to node 5, whose offer row requires it.
    std::string rows;
    for (int32_t key = 100; key < 118; ++key)
    {
        rows += rudeRow(1, 1, key - 99, 1, {{16, key}});
    }
    rows += rudeRow(1, 1, 19, 5, {{16, 40}});
    rows += rudeRow(1, 5, 1, -1, {{7, 40}, {21, 41}});
    const size_t offerRow = 19;
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rows));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml",
                                      metadata(interaction("offer", offerRow, "[offer]", "[90001]", "[]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();
    OpenYAMM::Game::Party party;
    const OpenYAMM::Game::Mm9QuestActorIdentity actor = {"testmap", 7, 1, true};

    const std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    CHECK(OpenYAMM::Game::Mm9QuestMarkerResolver().markerFor(actor, party, journalTable, rudeTable,
                                                             interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::Available);
    CHECK(std::chrono::steady_clock::now() - begin < std::chrono::milliseconds(200));
    // The tested keys still decide: the row forbids key 41, which no path removes.
    party.setQuestBit(90041, true);
    CHECK(OpenYAMM::Game::Mm9QuestMarkerResolver().markerFor(actor, party, journalTable, rudeTable,
                                                             interactionTable) ==
          OpenYAMM::Game::Mm9QuestMarkerState::None);
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
    CHECK(OpenYAMM::Game::questMarkerTextureName(Mm9QuestMarkerState::Trainer) == "trainer_marker_book");
    CHECK(OpenYAMM::Game::questMarkerColorAbgr(Mm9QuestMarkerState::InProgress, 255) !=
          OpenYAMM::Game::questMarkerColorAbgr(Mm9QuestMarkerState::Ready, 255));
    CHECK(OpenYAMM::Game::questMarkerColorAbgr(Mm9QuestMarkerState::Trainer, 255) !=
          OpenYAMM::Game::questMarkerColorAbgr(Mm9QuestMarkerState::Ready, 255));
    CHECK(OpenYAMM::Game::questMarkerAlpha(3500.0f) == 255);
    CHECK(OpenYAMM::Game::questMarkerAlpha(4500.0f) > 0);
    CHECK(OpenYAMM::Game::questMarkerAlpha(5500.0f) == 0);
    CHECK(OpenYAMM::Game::questMarkerWorldScale(0.0f) == 42.0f);
    CHECK(OpenYAMM::Game::questMarkerWorldScale(10000.0f) == 92.0f);
    CHECK(OpenYAMM::Game::questMarkerHalfExtent(42.0f) == doctest::Approx(25.2f));
    CHECK(OpenYAMM::Game::questMarkerOriginOffset(42.0f) == doctest::Approx(29.1f));
}

TEST_CASE("MM9 quest marker sprite assets resolve through the mounted world")
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
    for (const std::string &textureName : {"quest_marker_exclamation", "quest_marker_question", "trainer_marker_book"})
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
          "schema")
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
    CHECK(table.interactions().size() == 199);
    CHECK(std::count_if(
              table.interactions().begin(), table.interactions().end(),
              [](const OpenYAMM::Game::Mm9QuestInteraction &interaction) { return interaction.scrPredicate; }) == 29);
}

TEST_CASE("MM9 authored key interactions mark the Drangheim cook, the Frosgard pledgers and Erlend")
{
    const std::filesystem::path path =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/state/quest_interactions.yml";
    std::ifstream input(path);
    REQUIRE(input.is_open());
    std::ostringstream text;
    text << input.rdbuf();
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText(path.string(), text.str()));
    const OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    const OpenYAMM::Game::JournalQuestTable journalTable;
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;
    OpenYAMM::Game::Party party;
    const auto marker = [&](const OpenYAMM::Game::Mm9QuestActorIdentity &actor)
    {
        return resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable);
    };
    const OpenYAMM::Game::Mm9QuestActorIdentity cook = {"drangheimprison", 1039, 419, true};
    const OpenYAMM::Game::Mm9QuestActorIdentity gudrun = {"frosgardcity", 563, 191, true};
    const OpenYAMM::Game::Mm9QuestActorIdentity pules = {"frosgardcity", 595, 218, true};

    CHECK(marker(cook) == OpenYAMM::Game::Mm9QuestMarkerState::Available);
    CHECK(marker(gudrun) == OpenYAMM::Game::Mm9QuestMarkerState::None);
    party.setQuestBit(90265, true);   // the Green Man asks for pledges
    CHECK(marker(gudrun) == OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    CHECK(marker(pules) == OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    party.setQuestBit(90270, true);   // Gudrun's slot, which Pules can also give
    CHECK(marker(gudrun) == OpenYAMM::Game::Mm9QuestMarkerState::None);
    CHECK(marker(pules) == OpenYAMM::Game::Mm9QuestMarkerState::None);

    // Thronheim City's Erlend: the Scroll of Bad News goes to him while journal stage 660 (key 316) is open.
    const OpenYAMM::Game::Mm9QuestActorIdentity erlend = {"thronheimcity", 98, 246, true};
    CHECK(marker(erlend) == OpenYAMM::Game::Mm9QuestMarkerState::None);
    party.setQuestBit(90316, true);
    CHECK(marker(erlend) == OpenYAMM::Game::Mm9QuestMarkerState::Ready);
    party.setQuestBit(90318, true);
    CHECK(marker(erlend) == OpenYAMM::Game::Mm9QuestMarkerState::None);
}

TEST_CASE("MM9 promotion quests are offered to any party, whatever its classes")
{
    const std::filesystem::path path =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/state/quest_interactions.yml";
    std::ifstream input(path);
    REQUIRE(input.is_open());
    std::ostringstream text;
    text << input.rdbuf();
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText(path.string(), text.str()));
    const OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    const OpenYAMM::Game::JournalQuestTable journalTable;
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;
    OpenYAMM::Game::Party party;
    const auto marker = [&](const OpenYAMM::Game::Mm9QuestActorIdentity &actor)
    {
        return resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable);
    };
    // MM9's per-character promotion keys (401-448) are never set, so these offers wait for none of them.
    const OpenYAMM::Game::Mm9QuestActorIdentity scholar = {"thjorgardcity", 1058, 161, true};
    const OpenYAMM::Game::Mm9QuestActorIdentity healer = {"guberlandcity", 813, 128, true};
    const OpenYAMM::Game::Mm9QuestActorIdentity priest = {"guberlandcity", 811, 129, true};

    CHECK(marker(scholar) == OpenYAMM::Game::Mm9QuestMarkerState::Available);
    CHECK(marker(healer) == OpenYAMM::Game::Mm9QuestMarkerState::Available);
    CHECK(marker(priest) == OpenYAMM::Game::Mm9QuestMarkerState::Available);
    party.setQuestBit(90201, true);   // the scholar's task taken
    party.setQuestBit(90206, true);   // the healer's task taken
    party.setQuestBit(90250, true);   // the priest's three tasks taken
    CHECK(marker(scholar) == OpenYAMM::Game::Mm9QuestMarkerState::None);
    CHECK(marker(healer) == OpenYAMM::Game::Mm9QuestMarkerState::None);
    CHECK(marker(priest) == OpenYAMM::Game::Mm9QuestMarkerState::None);
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

TEST_CASE("MM9 trainer marker shows a lesson a member can take, gold aside, below quest markers")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    using OpenYAMM::Game::Mm9QuestMarkerState;
    using OpenYAMM::Game::SkillMastery;

    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC1.rude", rudeRow(1, 1, 1, -1, {{16, 10}, {21, 10}}) +
                                                        rudeRow(1, 1, 2, -4, {{16, 2006}})));
    OpenYAMM::Game::Mm9SkillTrainerTable trainerTable;
    REQUIRE(trainerTable.loadFromRows(
        {
            {"mm9:trainer/1/2", "1", "1", "2", "2", "2006", "Blade", "Sword|Dagger|Axe", "Expert", "4", "0", "", "",
             "Sturmford", "Test Trainer", "Test Trainer teaches Blade.", "static", "test.scene.yml", "NPC1.rude",
             "rude:-4"},
        },
        rudeTable));
    OpenYAMM::Game::Mm9QuestInteractionTable interactionTable;
    REQUIRE(interactionTable.loadText("test.yml", metadata(interaction("offer", 0, "[offer]", "[90001]", "[]"))));
    OpenYAMM::Game::JournalQuestTable journalTable = questTable();

    OpenYAMM::Game::Character knight = {};
    knight.name = "Ada";
    knight.className = "Knight";
    knight.skills["Sword"] = {"Sword", 4, SkillMastery::Normal};
    OpenYAMM::Game::Party party;
    party.setClassSkillTable(&gameData.classSkillTable);
    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 0;
    seed.members = {knight};
    party.seed(seed);

    const OpenYAMM::Game::Mm9TrainerMarkerTables trainerTables = {
        &trainerTable, &gameData.classSkillTable, &gameData.npcDialogTable};
    const OpenYAMM::Game::Mm9QuestActorIdentity actor = {"testmap", 7, 1, true};
    OpenYAMM::Game::Mm9QuestMarkerResolver resolver;
    const auto marker = [&]()
    {
        return resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable, &trainerTables);
    };

    // A quest offer outranks the trainer; once taken, the trainer shows although the party has no gold.
    CHECK(marker() == Mm9QuestMarkerState::Available);
    party.setQuestBit(90010, true);
    CHECK(marker() == Mm9QuestMarkerState::Trainer);
    CHECK(resolver.markerFor(actor, party, journalTable, rudeTable, interactionTable) == Mm9QuestMarkerState::None);

    // Nothing to learn: the rank is too low, or the mastery is already known.
    party.member(0)->skills["Sword"].level = 3;
    CHECK(marker() == Mm9QuestMarkerState::None);
    party.member(0)->skills["Sword"] = {"Sword", 4, SkillMastery::Expert};
    CHECK(marker() == Mm9QuestMarkerState::None);

    // A hidden actor shows nothing.
    party.member(0)->skills["Dagger"] = {"Dagger", 5, SkillMastery::Normal};
    CHECK(marker() == Mm9QuestMarkerState::Trainer);
    const OpenYAMM::Game::Mm9QuestActorIdentity hidden = {"testmap", 7, 1, false};
    CHECK(resolver.markerFor(hidden, party, journalTable, rudeTable, interactionTable, &trainerTables)
          == Mm9QuestMarkerState::None);
}
