#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/CompletionCertificates.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"

#include <doctest/doctest.h>

#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
constexpr uint32_t EnrothQBit = 784;
constexpr uint32_t AntagarichQBit = 783;
constexpr uint32_t JadameQBit = 228;
constexpr uint32_t DarkPathQBit = 1606;
// Day 10 of the first year, at noon: 9 full days after the 9:00 start.
constexpr float TenthDayNoon = 9.0f * 24.0f * 60.0f + 12.0f * 60.0f;

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_certificates_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

Party certifiedParty()
{
    Character knight;
    knight.name = "Aldric";
    knight.className = "Knight";
    knight.level = 40;
    knight.experience = 600000;
    Character sorcerer;
    sorcerer.name = "Mira";
    sorcerer.className = "Sorcerer";
    sorcerer.level = 38;
    sorcerer.experience = 300000;
    PartySeed seed;
    seed.members = {knight, sorcerer};
    Party party;
    party.seed(seed);
    return party;
}

std::vector<CompletionCertificateDefinition> threeWorldCertificates()
{
    std::vector<CompletionCertificateDefinition> certificates(4);
    certificates[0].id = "mm6";
    certificates[0].continent = "Enroth";
    certificates[0].headline = "Enroth Is Saved";
    certificates[0].qbit = EnrothQBit;
    certificates[1].id = "mm7";
    certificates[1].continent = "Antagarich";
    certificates[1].headline = "Antagarich Is Saved";
    certificates[1].qbit = AntagarichQBit;
    certificates[1].variants = {{DarkPathQBit, "Antagarich Bows to the Dark", "The Forge burns."}};
    certificates[2].id = "mm8";
    certificates[2].continent = "Jadame";
    certificates[2].headline = "Jadame Is Saved";
    certificates[2].qbit = JadameQBit;
    certificates[3].id = GrandCertificateId;
    certificates[3].headline = "The Three Worlds Are Saved";
    certificates[3].worldIds = {"mm6", "mm7", "mm8"};
    return certificates;
}
}

TEST_CASE("completion certificates come from world manifests and the grand certificate file")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "worlds" / "alpha" / "world.yml",
        "id: alpha\nname: Alpha\nsourceGame: alpha\n"
        "completion:\n"
        "  qbit: 501\n"
        "  continent: Alphaland\n"
        "  art: hud_x2/certificates/alpha.png\n"
        "  headline: Alphaland Is Saved\n"
        "  text: The end.\n"
        "  variants:\n"
        "  - qbit: 502\n"
        "    headline: Alphaland Falls\n");
    writeTextFile(assetRoot / "worlds" / "beta" / "world.yml",
        "id: beta\nname: Beta\nsourceGame: beta\n"
        "completion:\n"
        "  qbit: 601\n"
        "  art: 7winbg\n"
        "  headline: Congratulations!\n"
        "  layout:\n"
        "    text: [100, 78, 540, 408]\n"
        "    mark: [320, 421, 16]\n");
    writeTextFile(assetRoot / "worlds" / "gamma" / "world.yml", "id: gamma\nname: Gamma\nsourceGame: gamma\n");
    writeTextFile(assetRoot / "engine" / "ui" / "certificates.yml",
        "grand:\n  worlds: [alpha, beta]\n  art: hud_x2/certificates/grand.png\n  headline: Both Saved\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, OpenYAMM::Engine::AssetScaleTier::X1, "alpha"));
        std::vector<CompletionCertificateDefinition> certificates;
        std::string error;
        REQUIRE_MESSAGE(loadCompletionCertificates(assetFileSystem, certificates, error), error);
        REQUIRE_EQ(certificates.size(), 3u);
        CHECK_EQ(certificates[0].id, "alpha");
        CHECK_EQ(certificates[0].qbit, 501u);
        CHECK_EQ(certificates[0].continent, "Alphaland");
        CHECK_EQ(certificates[0].text, "The end.");
        REQUIRE_EQ(certificates[0].variants.size(), 1u);
        CHECK_EQ(certificates[0].variants[0].headline, "Alphaland Falls");
        // A variant without its own text keeps the certificate's.
        CHECK_EQ(certificates[0].variants[0].text, "The end.");
        CHECK_EQ(certificates[1].id, "beta");
        CHECK_FALSE(certificates[0].layout.declared);
        REQUIRE(certificates[1].layout.declared);
        CHECK_EQ(certificates[1].layout.text, std::array<float, 4>{100.0f, 78.0f, 540.0f, 408.0f});
        CHECK_EQ(certificates[1].layout.mark, std::array<float, 3>{320.0f, 421.0f, 16.0f});
        CHECK_EQ(certificates[2].id, GrandCertificateId);
        CHECK_EQ(certificates[2].qbit, 0u);
        CHECK_EQ(certificates[2].worldIds, std::vector<std::string>{"alpha", "beta"});
    }

    // A grand certificate naming a world without a completion could never be earned: it is left out.
    writeTextFile(assetRoot / "engine" / "ui" / "certificates.yml",
        "grand:\n  worlds: [alpha, gamma]\n  art: hud_x2/certificates/grand.png\n  headline: Both Saved\n");
    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, OpenYAMM::Engine::AssetScaleTier::X1, "alpha"));
        std::vector<CompletionCertificateDefinition> certificates;
        std::string error;
        REQUIRE(loadCompletionCertificates(assetFileSystem, certificates, error));
        CHECK_EQ(certificates.size(), 2u);
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("a world's completion qbit earns its certificate once, and the last world also the grand one")
{
    const std::vector<CompletionCertificateDefinition> certificates = threeWorldCertificates();
    Party party = certifiedParty();
    CHECK(recordNewCompletions(party, certificates, TenthDayNoon, 1000).empty());

    party.setQuestBit(EnrothQBit, true);
    CHECK_EQ(recordNewCompletions(party, certificates, TenthDayNoon, 1000), std::vector<std::string>{"mm6"});
    const WorldCompletionRecord *pEnroth = party.findWorldCompletion("mm6");
    REQUIRE(pEnroth != nullptr);
    CHECK(pEnroth->timed);
    CHECK_EQ(pEnroth->gameMinutes, doctest::Approx(TenthDayNoon));
    // 900000 experience over 9 days.
    CHECK_EQ(pEnroth->score, 100000u);
    CHECK_EQ(pEnroth->completedAtUnixSeconds, 1000);
    CHECK(recordNewCompletions(party, certificates, TenthDayNoon + 60.0f, 1060).empty());

    // A cleared and set again qbit earns nothing more.
    party.setQuestBit(EnrothQBit, false);
    party.setQuestBit(EnrothQBit, true);
    CHECK(recordNewCompletions(party, certificates, TenthDayNoon + 120.0f, 1120).empty());

    party.setQuestBit(AntagarichQBit, true);
    party.setQuestBit(JadameQBit, true);
    CHECK_EQ(recordNewCompletions(party, certificates, TenthDayNoon * 2.0f, 2000),
        std::vector<std::string>{"mm7", "mm8", GrandCertificateId});
    CHECK_EQ(party.worldCompletions().size(), 4u);
}

TEST_CASE("a save from before the completion records certifies only the stories finished after it")
{
    const std::vector<CompletionCertificateDefinition> certificates = threeWorldCertificates();
    Party party = certifiedParty();
    party.setQuestBit(JadameQBit, true);
    Party::Snapshot snapshot = party.snapshot();
    snapshot.worldCompletionsUntracked = true;
    party.restoreSnapshot(snapshot);

    CHECK(recordNewCompletions(party, certificates, TenthDayNoon, 1000).empty());
    const WorldCompletionRecord *pJadame = party.findWorldCompletion("mm8");
    REQUIRE(pJadame != nullptr);
    CHECK_FALSE(pJadame->timed);
    CHECK_FALSE(party.worldCompletionsUntracked());

    party.setQuestBit(EnrothQBit, true);
    CHECK_EQ(recordNewCompletions(party, certificates, TenthDayNoon, 1000), std::vector<std::string>{"mm6"});
    party.setQuestBit(AntagarichQBit, true);
    CHECK_EQ(recordNewCompletions(party, certificates, TenthDayNoon, 1000),
        std::vector<std::string>{"mm7", GrandCertificateId});

    const CompletionCertificate grand = buildCompletionCertificate(certificates[3], certificates, party);
    CHECK(grand.grand);
    CHECK_EQ(grand.worldLines,
        std::vector<std::string>{"Enroth: 0 Years, 0 Months, 9 Days", "Antagarich: 0 Years, 0 Months, 9 Days",
                                 "Jadame: finished"});
}

TEST_CASE("a completion certificate shows the party, the variant of the path taken, time and score")
{
    const std::vector<CompletionCertificateDefinition> certificates = threeWorldCertificates();
    Party party = certifiedParty();
    party.setQuestBit(AntagarichQBit, true);
    party.setQuestBit(DarkPathQBit, true);
    // 1 year, 2 months and 3 days after the start.
    const float played = 9.0f * 60.0f + float((336 + 56 + 3) * 24 * 60) + 30.0f;
    recordNewCompletions(party, certificates, played, 1000);

    const CompletionCertificate certificate = buildCompletionCertificate(certificates[1], certificates, party);
    CHECK_FALSE(certificate.grand);
    CHECK_EQ(certificate.headline, "Antagarich Bows to the Dark");
    CHECK_EQ(certificate.text, "The Forge burns.");
    CHECK_EQ(certificate.partyLines, std::vector<std::string>{"Aldric, Level 40 Knight", "Mira, Level 38 Sorcerer"});
    CHECK_EQ(certificate.timeLine, "Total Time: 1 Year, 2 Months, 3 Days");
    CHECK_EQ(certificate.scoreLine, "Score: " + std::to_string(900000u / 395u));
    CHECK_FALSE(certificate.dateLine.empty());
    CHECK_EQ(formatPlayTime(9.0f * 60.0f), "0 Years, 0 Months, 0 Days");
}

TEST_CASE("an original game's certificate words its lines as the original did")
{
    std::vector<CompletionCertificateDefinition> certificates = threeWorldCertificates();
    certificates[2].headline = "Congratulations!";
    certificates[2].layout.declared = true;
    Party party = certifiedParty();
    party.setQuestBit(JadameQBit, true);
    recordNewCompletions(party, certificates, TenthDayNoon, 1000);

    const CompletionCertificate certificate = buildCompletionCertificate(certificates[2], certificates, party);
    CHECK(certificate.originalLayout.declared);
    CHECK_EQ(certificate.partyLines,
        std::vector<std::string>{"Aldric the Level 40 Knight", "Mira the Level 38 Sorcerer"});
    CHECK_EQ(certificate.timeLine, "Total Time: 0 Years, 0 Months, 9 Days");
    CHECK_EQ(certificate.scoreLine, "Your score: 100000");
}

TEST_CASE("a certificate names the rules of a game played by a ruleset")
{
    RulesetSelection selection;
    CHECK(certificateRulesetLabel(selection, "Standard MMMerge").empty());
    selection.id = MawRulesetId;
    selection.options.difficulty = RulesetDifficulty::Hell;
    CHECK_EQ(certificateRulesetLabel(selection, "MAW"), "MAW (Hell)");
    selection.options.challengeMode = RulesetChallengeMode::BeyondMadness;
    selection.options.difficulty = RulesetDifficulty::Nightmare;
    CHECK_EQ(certificateRulesetLabel(selection, "MAW"), "MAW (Beyond Madness)");
    selection.options.challengeMode = RulesetChallengeMode::Austerity;
    selection.options.difficulty = RulesetDifficulty::Hard;
    selection.options.randomizer = true;
    CHECK_EQ(certificateRulesetLabel(selection, ""), "maw (Austerity, Hard, Randomizer)");
}

TEST_CASE("completion records survive a save round trip")
{
    Party party = certifiedParty();
    WorldCompletionRecord record;
    record.certificateId = "mm6";
    record.gameMinutes = TenthDayNoon;
    record.score = 4321;
    record.completedAtUnixSeconds = 1793000000;
    party.addWorldCompletion(record);
    WorldCompletionRecord untimed;
    untimed.certificateId = "mm8";
    untimed.timed = false;
    party.addWorldCompletion(untimed);

    GameSaveData saveData = {};
    saveData.mapFileName = "completion_roundtrip.odm";
    saveData.party = party.snapshot();
    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_completion_roundtrip.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(savePath, saveData, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());
    REQUIRE_EQ(loaded->party.worldCompletions.size(), 2u);
    CHECK_EQ(loaded->party.worldCompletions[0].certificateId, "mm6");
    CHECK_EQ(loaded->party.worldCompletions[0].gameMinutes, doctest::Approx(TenthDayNoon));
    CHECK_EQ(loaded->party.worldCompletions[0].score, 4321u);
    CHECK_EQ(loaded->party.worldCompletions[0].completedAtUnixSeconds, 1793000000);
    CHECK(loaded->party.worldCompletions[0].timed);
    CHECK_FALSE(loaded->party.worldCompletions[1].timed);
    CHECK_FALSE(loaded->party.worldCompletionsUntracked);
}
