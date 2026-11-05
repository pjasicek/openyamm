#pragma once

#include "engine/AssetFileSystem.h"
#include "game/content/ContentManifest.h"
#include "game/content/RulesetOptions.h"
#include "game/party/Party.h"

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The id of the certificate for every world of engine/ui/certificates.yml.
inline constexpr const char *GrandCertificateId = "grand";

// A completion certificate: one per world whose world.yml declares a completion, and the grand certificate
// (engine/ui/certificates.yml) for when every world it names is finished.
struct CompletionCertificateDefinition
{
    // The world's id, or GrandCertificateId.
    std::string id;
    std::string continent;
    std::string art;
    std::string headline;
    std::string text;
    // The world's completion qbit; 0 for the grand certificate.
    uint32_t qbit = 0;
    std::vector<WorldCompletionDefinition::Variant> variants;
    // Declared: an original game's certificate (WorldCompletionDefinition).
    WorldCompletionDefinition::Layout layout;
    // The grand certificate's worlds, in the order it lists them.
    std::vector<std::string> worldIds;
};

// What a certificate shows, ready to draw (WinGameScreen).
struct CompletionCertificate
{
    std::string id;
    std::string art;
    bool grand = false;
    // An original game's certificate background, with its layout; otherwise OpenYAMM's design.
    WorldCompletionDefinition::Layout originalLayout;
    std::string headline;
    // One per party member: "Name the Level N Class" on an original certificate, "Name, Level N Class" on OpenYAMM's.
    std::vector<std::string> partyLines;
    std::string text;
    // The grand certificate's worlds: "Enroth: 1 Year, 2 Months, 3 Days".
    std::vector<std::string> worldLines;
    std::string timeLine;
    std::string scoreLine;
    std::string dateLine;
    // The rules the game was played by, beside the OpenYAMM wordmark (certificateRulesetLabel); empty for Standard.
    std::string rulesetLabel;
};

// The certificates of the mounted worlds, then the grand one when certificates.yml names only mounted worlds that
// declare a completion. False with errorMessage on a malformed manifest or certificates.yml.
bool loadCompletionCertificates(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<CompletionCertificateDefinition> &certificates,
    std::string &errorMessage);

// Records the stories the party finished since the last call (a world's completion qbit set without a record; the grand
// certificate once all its worlds have one) and returns their certificate ids in the order to show them. A save from
// before the records first gets untimed records, without certificates, for the stories it had already finished.
std::vector<std::string> recordNewCompletions(
    Party &party,
    const std::vector<CompletionCertificateDefinition> &certificates,
    float gameMinutes,
    int64_t nowUnixSeconds);

// The rules a certificate names: empty for the Standard rules, else the ruleset's name with its challenge mode and the
// difficulty unless the challenge sets it ("MAW (Beyond Madness)", "MAW (Austerity, Hell)", "MAW (Hell)").
std::string certificateRulesetLabel(const RulesetSelection &selection, const std::string &rulesetName);

// The original games' score: the party's experience divided by the days played (at least one).
uint64_t completionScore(const Party &party, float gameMinutes);
// The time played as the original certificates give it: "1 Year, 2 Months, 3 Days" (28-day months, 12-month years).
std::string formatPlayTime(float gameMinutes);

CompletionCertificate buildCompletionCertificate(
    const CompletionCertificateDefinition &definition,
    const std::vector<CompletionCertificateDefinition> &certificates,
    const Party &party);
}
