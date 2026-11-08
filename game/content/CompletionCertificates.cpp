#include "game/content/CompletionCertificates.h"

#include "engine/Localization.h"
#include "game/party/SkillData.h"
#include "game/ui/CalendarText.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <ctime>
#include <exception>
#include <optional>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *GrandCertificatePath = "Data/ui/certificates.yml";
constexpr float GameStartMinutes = 9.0f * 60.0f;
constexpr uint64_t MinutesPerDay = 24u * 60u;
constexpr uint64_t DaysPerMonth = 28u;
constexpr uint64_t MonthsPerYear = 12u;

const CompletionCertificateDefinition *findCertificate(
    const std::vector<CompletionCertificateDefinition> &certificates,
    const std::string &id)
{
    for (const CompletionCertificateDefinition &certificate : certificates)
    {
        if (certificate.id == id)
        {
            return &certificate;
        }
    }

    return nullptr;
}

std::string formatDate(int64_t unixSeconds)
{
    const std::time_t timestamp = static_cast<std::time_t>(unixSeconds);
    const std::tm *pLocal = std::localtime(&timestamp);

    if (pLocal == nullptr)
    {
        return {};
    }

    return formatCalendarDate(pLocal->tm_mday, pLocal->tm_mon + 1, pLocal->tm_year + 1900);
}
}

bool loadCompletionCertificates(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<CompletionCertificateDefinition> &certificates,
    std::string &errorMessage)
{
    certificates.clear();
    errorMessage.clear();
    std::vector<WorldManifest> manifests;

    if (!loadMountedWorldManifests(assetFileSystem, manifests, errorMessage))
    {
        return false;
    }

    for (const WorldManifest &manifest : manifests)
    {
        if (!manifest.completion.declared)
        {
            continue;
        }

        CompletionCertificateDefinition certificate;
        certificate.id = manifest.id;
        certificate.continent = manifest.completion.continent;
        certificate.art = manifest.completion.art;
        certificate.headline = manifest.completion.headline;
        certificate.text = manifest.completion.text;
        certificate.qbit = manifest.completion.qbit;
        certificate.variants = manifest.completion.variants;
        certificate.layout = manifest.completion.layout;
        certificates.push_back(std::move(certificate));
    }

    const std::optional<std::string> grandText = assetFileSystem.readTextFile(GrandCertificatePath);

    if (!grandText)
    {
        return true;
    }

    try
    {
        const YAML::Node grandNode = YAML::Load(*grandText)["grand"];

        if (!grandNode)
        {
            return true;
        }

        CompletionCertificateDefinition grand;
        grand.id = GrandCertificateId;
        grand.art = grandNode["art"].as<std::string>();
        grand.headline = grandNode["headline"].as<std::string>();
        grand.text = grandNode["text"].as<std::string>("");

        for (const YAML::Node &worldNode : grandNode["worlds"])
        {
            grand.worldIds.push_back(worldNode.as<std::string>());
        }

        if (grand.worldIds.empty())
        {
            errorMessage = std::string(GrandCertificatePath) + ": grand must name its worlds";
            return false;
        }

        // A grand certificate of worlds that are not all mounted could never be earned.
        for (const std::string &worldId : grand.worldIds)
        {
            if (findCertificate(certificates, worldId) == nullptr)
            {
                return true;
            }
        }

        certificates.push_back(std::move(grand));
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string(GrandCertificatePath) + ": " + exception.what();
        return false;
    }

    return true;
}

std::vector<std::string> recordNewCompletions(
    Party &party,
    const std::vector<CompletionCertificateDefinition> &certificates,
    float gameMinutes,
    int64_t nowUnixSeconds)
{
    const bool untracked = party.worldCompletionsUntracked();
    std::vector<std::string> newIds;

    for (const CompletionCertificateDefinition &certificate : certificates)
    {
        if (certificate.qbit == 0 || !party.hasQuestBit(certificate.qbit)
            || party.findWorldCompletion(certificate.id) != nullptr)
        {
            continue;
        }

        WorldCompletionRecord record;
        record.certificateId = certificate.id;
        record.gameMinutes = gameMinutes;
        record.score = completionScore(party, gameMinutes);
        record.completedAtUnixSeconds = nowUnixSeconds;
        record.timed = !untracked;
        party.addWorldCompletion(record);

        if (!untracked)
        {
            newIds.push_back(certificate.id);
        }
    }

    for (const CompletionCertificateDefinition &certificate : certificates)
    {
        if (certificate.worldIds.empty() || party.findWorldCompletion(certificate.id) != nullptr)
        {
            continue;
        }

        const bool everyWorldFinished = std::all_of(
            certificate.worldIds.begin(),
            certificate.worldIds.end(),
            [&party](const std::string &worldId)
            {
                return party.findWorldCompletion(worldId) != nullptr;
            });

        if (!everyWorldFinished)
        {
            continue;
        }

        WorldCompletionRecord record;
        record.certificateId = certificate.id;
        record.gameMinutes = gameMinutes;
        record.score = completionScore(party, gameMinutes);
        record.completedAtUnixSeconds = nowUnixSeconds;
        record.timed = !untracked;
        party.addWorldCompletion(record);

        if (!untracked)
        {
            newIds.push_back(certificate.id);
        }
    }

    party.clearWorldCompletionsUntracked();
    return newIds;
}

std::string certificateRulesetLabel(const RulesetSelection &selection, const std::string &rulesetName)
{
    if (selection.isStandard())
    {
        return {};
    }

    const RulesetOptions &options = selection.options;
    std::vector<std::string> details;

    if (options.challengeMode != RulesetChallengeMode::None)
    {
        details.push_back(Engine::tr(rulesetChallengeModeName(options.challengeMode)));
    }

    if (!rulesetChallengeModeDifficulty(options.challengeMode))
    {
        details.push_back(Engine::tr(rulesetDifficultyName(options.difficulty)));
    }

    if (options.randomizer)
    {
        details.push_back(Engine::tr("Randomizer"));
    }

    std::string label = rulesetName.empty() ? selection.id : Engine::localize(rulesetName);

    for (size_t index = 0; index < details.size(); ++index)
    {
        label += index == 0 ? " (" : ", ";
        label += details[index];
    }

    return details.empty() ? label : label + ")";
}

uint64_t completionScore(const Party &party, float gameMinutes)
{
    const float elapsedMinutes = std::max(0.0f, gameMinutes - GameStartMinutes);
    const uint64_t days = std::max<uint64_t>(1u, uint64_t(std::floor(elapsedMinutes / float(MinutesPerDay))));
    uint64_t experience = 0;

    for (const Character &member : party.members())
    {
        experience += member.experience;
    }

    return experience / days;
}

std::string formatPlayTime(float gameMinutes)
{
    const float elapsedMinutes = std::max(0.0f, gameMinutes - GameStartMinutes);
    uint64_t days = uint64_t(std::floor(elapsedMinutes / float(MinutesPerDay)));
    const uint64_t years = days / (DaysPerMonth * MonthsPerYear);
    days %= DaysPerMonth * MonthsPerYear;
    const uint64_t months = days / DaysPerMonth;
    days %= DaysPerMonth;
    return Engine::tr("{years}, {months}, {days}",
        {{"years", Engine::trn("{count} Year", "{count} Years", years, {{"count", years}})},
            {"months", Engine::trn("{count} Month", "{count} Months", months, {{"count", months}})},
            {"days", Engine::trn("{count} Day", "{count} Days", days, {{"count", days}})}});
}

CompletionCertificate buildCompletionCertificate(
    const CompletionCertificateDefinition &definition,
    const std::vector<CompletionCertificateDefinition> &certificates,
    const Party &party)
{
    CompletionCertificate certificate;
    certificate.id = definition.id;
    certificate.art = definition.art;
    certificate.grand = !definition.worldIds.empty();
    certificate.originalLayout = definition.layout;
    const bool original = definition.layout.declared;
    // A world's texts are English in its world.yml, translated under the world's context; the grand certificate's
    // come from the engine's certificates.yml.
    const std::string context = certificate.grand ? std::string() : "world:" + definition.id;
    certificate.headline = Engine::localize(definition.headline, context);
    certificate.text = Engine::localize(definition.text, context);

    for (const WorldCompletionDefinition::Variant &variant : definition.variants)
    {
        if (party.hasQuestBit(variant.qbit))
        {
            certificate.headline = Engine::localize(variant.headline, context);
            certificate.text = Engine::localize(variant.text, context);
            break;
        }
    }

    for (const Character &member : party.members())
    {
        const std::string className = !member.className.empty() ? member.className : member.role;
        const std::string displayClass =
            !className.empty() ? Engine::localizeKnown(displayClassName(className)) : Engine::tr("Adventurer");
        const uint32_t level = std::max<uint32_t>(1u, member.level);
        certificate.partyLines.push_back(original
                ? Engine::tr("{name} the Level {level} {class}",
                    {{"name", member.name}, {"level", level}, {"class", displayClass}})
                : Engine::tr("{name}, Level {level} {class}",
                    {{"name", member.name}, {"level", level}, {"class", displayClass}}));
    }

    for (const std::string &worldId : definition.worldIds)
    {
        const CompletionCertificateDefinition *pWorld = findCertificate(certificates, worldId);
        const WorldCompletionRecord *pRecord = party.findWorldCompletion(worldId);
        const std::string name = pWorld != nullptr && !pWorld->continent.empty()
            ? Engine::localize(pWorld->continent, "world:" + worldId)
            : worldId;

        if (pRecord != nullptr && pRecord->timed)
        {
            certificate.worldLines.push_back(
                Engine::tr("{world}: {time}", {{"world", name}, {"time", formatPlayTime(pRecord->gameMinutes)}}));
        }
        else
        {
            certificate.worldLines.push_back(Engine::tr("{world}: finished", {{"world", name}}));
        }
    }

    if (const WorldCompletionRecord *pRecord = party.findWorldCompletion(definition.id))
    {
        certificate.timeLine = Engine::tr("Total Time: {time}", {{"time", formatPlayTime(pRecord->gameMinutes)}});
        certificate.scoreLine = original ? Engine::tr("Your score: {score}", {{"score", pRecord->score}})
                                         : Engine::tr("Score: {score}", {{"score", pRecord->score}});
        certificate.dateLine = formatDate(pRecord->completedAtUnixSeconds);
    }

    return certificate;
}
}
