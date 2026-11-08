#include "game/mm9/Mm9QuestMarkers.h"

#include "engine/AssetFileSystem.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9SkillTrainer.h"
#include "game/party/Party.h"
#include "game/tables/JournalQuestTable.h"

#include <algorithm>
#include <deque>
#include <optional>
#include <set>
#include <unordered_map>

#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Game
{
namespace
{
bool readQBitArray(const YAML::Node &node, const char *pFieldName, std::vector<uint32_t> &values, std::string &error)
{
    const YAML::Node arrayNode = node[pFieldName];
    if (!arrayNode || !arrayNode.IsSequence())
    {
        error = std::string("missing QBit array '") + pFieldName + "'";
        return false;
    }

    for (const YAML::Node &valueNode : arrayNode)
    {
        const uint32_t value = valueNode.as<uint32_t>(0);
        if (value == 0)
        {
            error = std::string("invalid QBit in '") + pFieldName + "'";
            return false;
        }
        values.push_back(value);
    }
    return true;
}

bool readKeyState(const YAML::Node &node, Mm9QuestKeyState &state, std::string &error)
{
    if (!node)
    {
        return true;
    }

    state.present = true;
    return node.IsMap() && readQBitArray(node, "required_qbits", state.requiredQBits, error)
        && readQBitArray(node, "forbidden_qbits", state.forbiddenQBits, error);
}

bool keyStateHolds(const Mm9QuestKeyState &state, const Party &party)
{
    const auto partyHasQBit = [&party](uint32_t qbitId)
    {
        return party.hasQuestBit(qbitId);
    };
    return state.present && std::all_of(state.requiredQBits.begin(), state.requiredQBits.end(), partyHasQBit)
        && std::none_of(state.forbiddenQBits.begin(), state.forbiddenQBits.end(), partyHasQBit);
}

bool hasRole(const YAML::Node &rolesNode, const std::string &role)
{
    if (!rolesNode || !rolesNode.IsSequence())
    {
        return false;
    }
    return std::any_of(
        rolesNode.begin(),
        rolesNode.end(),
        [&role](const YAML::Node &node)
        {
            return node.as<std::string>("") == role;
        });
}

bool journalEntryIsActive(uint32_t qbitId, const JournalQuestTable &table, const Party &party)
{
    const std::vector<JournalQuestEntry> &entries = table.entries();
    const std::vector<JournalQuestEntry>::const_iterator iterator = std::lower_bound(
        entries.begin(),
        entries.end(),
        qbitId,
        [](const JournalQuestEntry &entry, uint32_t value)
        {
            return entry.qbitId < value;
        });
    return iterator != entries.end() && iterator->qbitId == qbitId && table.isVisible(*iterator, party);
}

bool anyJournalEntryIsActive(const std::vector<uint32_t> &qbitIds, const JournalQuestTable &table, const Party &party)
{
    return std::any_of(
        qbitIds.begin(),
        qbitIds.end(),
        [&table, &party](uint32_t qbitId)
        {
            return journalEntryIsActive(qbitId, table, party);
        });
}

bool allJournalEntriesAreActive(const std::vector<uint32_t> &qbitIds, const JournalQuestTable &table,
                                const Party &party)
{
    return std::all_of(
        qbitIds.begin(),
        qbitIds.end(),
        [&table, &party](uint32_t qbitId)
        {
            return journalEntryIsActive(qbitId, table, party);
        });
}

bool scrPredicatePasses(const Mm9QuestInteraction &interaction, const Party &party)
{
    const auto partyHasQBit = [&party](uint32_t qbitId)
    {
        return party.hasQuestBit(qbitId);
    };
    if (!std::all_of(interaction.requiredQBits.begin(), interaction.requiredQBits.end(), partyHasQBit)
        || !std::none_of(interaction.forbiddenQBits.begin(), interaction.forbiddenQBits.end(), partyHasQBit)
        || (!interaction.anyRequiredQBits.empty()
            && !std::any_of(
                interaction.anyRequiredQBits.begin(),
                interaction.anyRequiredQBits.end(),
                partyHasQBit)))
    {
        return false;
    }
    return party.gold() >= interaction.minimumGold;
}

bool bindingMatches(const Mm9QuestInteraction &interaction, const Mm9QuestActorIdentity &actor)
{
    return std::any_of(interaction.bindings.begin(), interaction.bindings.end(),
                       [&actor](const Mm9QuestInteractionBinding &binding) {
                           return binding.mapId == actor.mapId && binding.sourceObjectIndex == actor.sourceObjectIndex;
                       });
}

struct PreviewQuestKeys
{
    const Party *pParty = nullptr;
    std::unordered_map<uint32_t, bool> changes;

    bool has(uint32_t qbitId) const
    {
        const std::unordered_map<uint32_t, bool>::const_iterator iterator = changes.find(qbitId);
        return iterator != changes.end() ? iterator->second : pParty->hasQuestBit(qbitId);
    }
};

// The row's key grants and removals the preview follows: only the keys some row tests (testedQBits, sorted).
void previewRowEffects(const Mm9RudeRow &row, const std::vector<uint32_t> &testedQBits, PreviewQuestKeys &keys)
{
    if (!mm9RudeRowAppliesQuestKeys(row))
    {
        return;
    }
    const auto apply = [&testedQBits, &keys](const std::vector<int32_t> &rawKeys, bool value)
    {
        for (int32_t rawKeyId : rawKeys)
        {
            const std::optional<uint32_t> qbitId = mm9QBitForRawQuestKey(rawKeyId);
            if (qbitId && std::binary_search(testedQBits.begin(), testedQBits.end(), *qbitId))
            {
                keys.changes[*qbitId] = value;
            }
        }
    };
    apply(row.grantedRawKeys, true);
    apply(row.removedRawKeys, false);
}

// The keys the dialogue's rows test (required or forbidden), sorted. Which rows a path shows depends on these alone:
// keys a row grants or removes but no row tests cannot change it, so the path search leaves them out of its states.
// Counting them made the states grow as 2^keys: Sturmford's Tyralt (RUDE 61, a dozen promotion keys granted in loops)
// took 400 ms per marker rebuild, a hitch on every quest-bit change in the city (2026-11-06).
std::vector<uint32_t> testedRudeQBits(const std::vector<Mm9RudeRow> &rows)
{
    std::vector<uint32_t> qbitIds;
    const auto appendKeys = [&qbitIds](const std::vector<int32_t> &rawKeys)
    {
        for (int32_t rawKeyId : rawKeys)
        {
            const std::optional<uint32_t> qbitId = mm9QBitForRawQuestKey(rawKeyId);
            if (qbitId && std::find(qbitIds.begin(), qbitIds.end(), *qbitId) == qbitIds.end())
            {
                qbitIds.push_back(*qbitId);
            }
        }
    };
    for (const Mm9RudeRow &row : rows)
    {
        appendKeys(row.requiredRawKeys);
        appendKeys(row.forbiddenRawKeys);
    }
    std::sort(qbitIds.begin(), qbitIds.end());
    return qbitIds;
}

std::string previewSignature(int32_t nodeId, const PreviewQuestKeys &keys, const std::vector<uint32_t> &qbitIds)
{
    std::string signature = std::to_string(nodeId) + ':';
    signature.reserve(signature.size() + qbitIds.size());
    for (uint32_t qbitId : qbitIds)
    {
        signature.push_back(keys.has(qbitId) ? '1' : '0');
    }
    return signature;
}

// Whether some path through the dialogue graph, with the quest keys its rows grant or remove on the way, shows the row.
bool rowIsShownOnSomePath(uint32_t rudeId, size_t targetRowIndex, const Party &party, const Mm9RudeDialogueTable &table)
{
    const std::vector<Mm9RudeRow> &rows = table.rows(rudeId);
    if (targetRowIndex >= rows.size())
    {
        return false;
    }

    struct PendingNode
    {
        int32_t nodeId = 0;
        PreviewQuestKeys keys;
    };

    const std::vector<uint32_t> qbitIds = testedRudeQBits(rows);
    std::deque<PendingNode> pending;
    pending.push_back({static_cast<int32_t>(rudeId), {&party, {}}});
    std::set<std::string> visited;
    while (!pending.empty())
    {
        PendingNode current = std::move(pending.front());
        pending.pop_front();
        if (!visited.insert(previewSignature(current.nodeId, current.keys, qbitIds)).second)
        {
            continue;
        }

        for (const Mm9RudeRow &row : rows)
        {
            if (row.nodeId != current.nodeId ||
                !mm9RudeRowPassesQuestKeys(row, [&current](uint32_t qbitId) { return current.keys.has(qbitId); }))
            {
                continue;
            }
            if (row.rowIndex == targetRowIndex)
            {
                return true;
            }
            if (row.next >= 0)
            {
                PreviewQuestKeys nextKeys = current.keys;
                previewRowEffects(row, qbitIds, nextKeys);
                pending.push_back({row.next, std::move(nextKeys)});
            }
        }
    }
    return false;
}

bool rowIsReachable(uint32_t rudeId, size_t targetRowIndex, const Party &party, const Mm9RudeDialogueTable &table)
{
    const std::vector<Mm9RudeRow> &rows = table.rows(rudeId);
    return targetRowIndex < rows.size()
        && mm9RudeRowAppliesQuestKeys(rows[targetRowIndex])
        && rowIsShownOnSomePath(rudeId, targetRowIndex, party, table);
}

// A trainer row the talk can show, with a lesson a party member can take. Gold is left out: the marker shows where the
// party can train, also before it has the money.
bool actorHasTrainerLesson(const Mm9QuestActorIdentity &actor, const Party &party,
                           const Mm9RudeDialogueTable &rudeDialogueTable, const Mm9TrainerMarkerTables &tables)
{
    for (const Mm9SkillTrainerService &service : tables.pSkillTrainerTable->entries())
    {
        if (service.rudeId != actor.rudeId
            || !rowIsShownOnSomePath(actor.rudeId, service.rudeRowIndex, party, rudeDialogueTable))
        {
            continue;
        }
        for (const std::string &skillName : service.topic.skillNames)
        {
            const SkillMasteryTrainingRequest request = {
                .skillName = skillName,
                .targetMastery = service.topic.targetMastery,
                .requiredGold = service.topic.requiredGold,
                .requiredSkill = service.topic.requiredSkillRank,
                .checkGold = false,
            };
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                const std::optional<MasteryTeacherEvaluation> evaluation = evaluateSkillMasteryTraining(
                    request, party, memberIndex, *tables.pClassSkillTable, *tables.pNpcDialogTable);
                if (evaluation && evaluation->approved)
                {
                    return true;
                }
            }
        }
    }
    return false;
}
} // namespace

bool Mm9QuestInteractionTable::load(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::string path = "state/quest_interactions.yml";
    const std::optional<std::string> text = assetFileSystem.readTextFile(path);
    if (!text)
    {
        clear();
        m_errors.push_back(path + ": could not read file");
        return false;
    }
    return loadText(path, *text);
}

bool Mm9QuestInteractionTable::loadText(const std::string &sourceName, const std::string &text)
{
    clear();
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (root["format_version"].as<uint32_t>(0) != 1 || root["world"].as<std::string>("") != "mm9")
        {
            m_errors.push_back(sourceName + ": unsupported quest-interaction metadata header");
            return false;
        }
        const YAML::Node interactionsNode = root["interactions"];
        if (!interactionsNode || !interactionsNode.IsSequence())
        {
            m_errors.push_back(sourceName + ": missing interactions sequence");
            return false;
        }
        std::set<std::string> seenIds;
        for (const YAML::Node &node : interactionsNode)
        {
            Mm9QuestInteraction interaction = {};
            interaction.id = node["id"].as<std::string>("");
            interaction.rudeId = node["rude_id"].as<uint32_t>(0);
            const std::string sourceKind = node["source_kind"].as<std::string>("rude");
            interaction.scrPredicate = sourceKind == "scr";
            interaction.keyStates = sourceKind == "keys";
            interaction.rudeRowIndex = node["provenance"]["row_index"].as<size_t>(static_cast<size_t>(-1));
            interaction.offer = hasRole(node["roles"], "offer");
            interaction.handoff = hasRole(node["roles"], "handoff");
            std::string error;
            if (interaction.keyStates)
            {
                const YAML::Node keysNode = node["conditions"]["keys"];
                if (interaction.id.empty() || !seenIds.insert(interaction.id).second || interaction.rudeId == 0
                    || !keysNode || !readKeyState(keysNode["available"], interaction.availableKeys, error)
                    || !readKeyState(keysNode["in_progress"], interaction.inProgressKeys, error)
                    || !readKeyState(keysNode["ready"], interaction.readyKeys, error))
                {
                    m_errors.push_back(sourceName + ": invalid key interaction " + interaction.id + ": " + error);
                    continue;
                }
            }
            else if (interaction.id.empty() || !seenIds.insert(interaction.id).second || interaction.rudeId == 0 ||
                (!interaction.scrPredicate && interaction.rudeRowIndex == static_cast<size_t>(-1)) ||
                (!interaction.offer && !interaction.handoff) ||
                !readQBitArray(node["conditions"]["available"], "activates_journal_entries",
                               interaction.activatedJournalEntries, error) ||
                !readQBitArray(node["conditions"]["ready"], "active_journal_entries",
                               interaction.completedJournalEntries, error))
            {
                m_errors.push_back(sourceName + ": invalid interaction " + interaction.id + ": " + error);
                continue;
            }

            if (interaction.scrPredicate)
            {
                const YAML::Node predicateNode = node["conditions"]["scr_predicate"];
                if (!predicateNode ||
                    !readQBitArray(predicateNode, "required_qbits", interaction.requiredQBits, error) ||
                    !readQBitArray(predicateNode, "forbidden_qbits", interaction.forbiddenQBits, error) ||
                    !readQBitArray(predicateNode, "any_required_qbits", interaction.anyRequiredQBits, error))
                {
                    m_errors.push_back(sourceName + ": invalid SCR predicate " + interaction.id + ": " + error);
                    continue;
                }
                interaction.minimumGold = predicateNode["minimum_gold"].as<int>(0);
                if (interaction.minimumGold < 0)
                {
                    m_errors.push_back(sourceName + ": invalid SCR minimum gold " + interaction.id);
                    continue;
                }
            }

            const YAML::Node bindingsNode = node["bindings"];
            if (!bindingsNode || !bindingsNode.IsSequence())
            {
                m_errors.push_back(sourceName + ": interaction " + interaction.id + " has no bindings array");
                continue;
            }
            for (const YAML::Node &bindingNode : bindingsNode)
            {
                Mm9QuestInteractionBinding binding = {};
                binding.mapId = bindingNode["map_id"].as<std::string>("");
                binding.sourceObjectIndex = bindingNode["source_object_index"].as<uint32_t>(0);
                if (binding.mapId.empty())
                {
                    m_errors.push_back(sourceName + ": interaction " + interaction.id + " has invalid binding");
                    continue;
                }
                interaction.bindings.push_back(std::move(binding));
            }
            m_interactions.push_back(std::move(interaction));
        }
    }
    catch (const YAML::Exception &exception)
    {
        m_errors.push_back(sourceName + ": " + exception.what());
    }
    if (!m_errors.empty())
    {
        m_interactions.clear();
        return false;
    }
    return !m_interactions.empty();
}

void Mm9QuestInteractionTable::clear()
{
    m_interactions.clear();
    m_errors.clear();
}

const std::vector<Mm9QuestInteraction> &Mm9QuestInteractionTable::interactions() const
{
    return m_interactions;
}

const std::vector<std::string> &Mm9QuestInteractionTable::errors() const
{
    return m_errors;
}

Mm9QuestMarkerState Mm9QuestMarkerResolver::markerFor(const Mm9QuestActorIdentity &actor, const Party &party,
                                                      const JournalQuestTable &journalQuestTable,
                                                      const Mm9RudeDialogueTable &rudeDialogueTable,
                                                      const Mm9QuestInteractionTable &interactionTable,
                                                      const Mm9TrainerMarkerTables *pTrainerTables) const
{
    if (!actor.interactable || actor.rudeId == 0)
    {
        return Mm9QuestMarkerState::None;
    }

    Mm9QuestMarkerState result = Mm9QuestMarkerState::None;
    for (const Mm9QuestInteraction &interaction : interactionTable.interactions())
    {
        if (interaction.rudeId != actor.rudeId || !bindingMatches(interaction, actor))
        {
            continue;
        }
        if (interaction.keyStates)
        {
            const Mm9QuestMarkerState candidate = keyStateHolds(interaction.readyKeys, party)
                ? Mm9QuestMarkerState::Ready
                : keyStateHolds(interaction.inProgressKeys, party) ? Mm9QuestMarkerState::InProgress
                : keyStateHolds(interaction.availableKeys, party) ? Mm9QuestMarkerState::Available
                : Mm9QuestMarkerState::None;
            result = std::max(result, candidate);
            continue;
        }
        const bool reachable = interaction.scrPredicate
                                   ? scrPredicatePasses(interaction, party)
                                   : rowIsReachable(actor.rudeId, interaction.rudeRowIndex, party, rudeDialogueTable);
        const bool handoffActive = interaction.handoff && anyJournalEntryIsActive(interaction.completedJournalEntries,
                                                                                  journalQuestTable, party);
        Mm9QuestMarkerState candidate = Mm9QuestMarkerState::None;
        if (handoffActive)
        {
            candidate = reachable ? Mm9QuestMarkerState::Ready : Mm9QuestMarkerState::InProgress;
        }
        if (interaction.offer && reachable &&
            !allJournalEntriesAreActive(interaction.activatedJournalEntries, journalQuestTable, party))
        {
            candidate = std::max(candidate, Mm9QuestMarkerState::Available);
        }
        result = std::max(result, candidate);
    }
    if (result < Mm9QuestMarkerState::Trainer
        && pTrainerTables != nullptr
        && pTrainerTables->pSkillTrainerTable != nullptr
        && pTrainerTables->pClassSkillTable != nullptr
        && pTrainerTables->pNpcDialogTable != nullptr
        && actorHasTrainerLesson(actor, party, rudeDialogueTable, *pTrainerTables))
    {
        result = Mm9QuestMarkerState::Trainer;
    }
    return result;
}

void Mm9LoadedLocationQuestMarkerCache::loadLocation(bool mm9Active,
                                                     const std::vector<Mm9LoadedQuestMarkerActor> &actors,
                                                     Mm9QuestEligibilityStamp stamp, const Party &party,
                                                     const JournalQuestTable &journalQuestTable,
                                                     const Mm9RudeDialogueTable &rudeDialogueTable,
                                                     const Mm9QuestInteractionTable &interactionTable,
                                                     const Mm9TrainerMarkerTables *pTrainerTables)
{
    clear();
    m_active = mm9Active;
    if (!m_active)
    {
        return;
    }
    rebuild(actors, party, journalQuestTable, rudeDialogueTable, interactionTable, pTrainerTables);
    m_evaluatedStamp = stamp;
}

bool Mm9LoadedLocationQuestMarkerCache::update(const std::vector<Mm9LoadedQuestMarkerActor> &actors,
                                               Mm9QuestEligibilityStamp stamp, const Party &party,
                                               const JournalQuestTable &journalQuestTable,
                                               const Mm9RudeDialogueTable &rudeDialogueTable,
                                               const Mm9QuestInteractionTable &interactionTable,
                                               const Mm9TrainerMarkerTables *pTrainerTables)
{
    if (!m_active || stamp == m_evaluatedStamp)
    {
        return false;
    }
    rebuild(actors, party, journalQuestTable, rudeDialogueTable, interactionTable, pTrainerTables);
    m_evaluatedStamp = stamp;
    return true;
}

void Mm9LoadedLocationQuestMarkerCache::clear()
{
    m_active = false;
    m_evaluatedStamp = {};
    m_markers.clear();
    m_rebuildCount = 0;
}

Mm9QuestMarkerState Mm9LoadedLocationQuestMarkerCache::markerForActor(uint32_t actorId) const
{
    const std::unordered_map<uint32_t, Mm9QuestMarkerState>::const_iterator iterator = m_markers.find(actorId);
    return iterator != m_markers.end() ? iterator->second : Mm9QuestMarkerState::None;
}

bool Mm9LoadedLocationQuestMarkerCache::active() const
{
    return m_active;
}

uint64_t Mm9LoadedLocationQuestMarkerCache::rebuildCount() const
{
    return m_rebuildCount;
}

void Mm9LoadedLocationQuestMarkerCache::rebuild(const std::vector<Mm9LoadedQuestMarkerActor> &actors,
                                                const Party &party, const JournalQuestTable &journalQuestTable,
                                                const Mm9RudeDialogueTable &rudeDialogueTable,
                                                const Mm9QuestInteractionTable &interactionTable,
                                                const Mm9TrainerMarkerTables *pTrainerTables)
{
    m_markers.clear();
    Mm9QuestMarkerResolver resolver;
    for (const Mm9LoadedQuestMarkerActor &actor : actors)
    {
        const Mm9QuestMarkerState state =
            resolver.markerFor(actor.identity, party, journalQuestTable, rudeDialogueTable, interactionTable,
                               pTrainerTables);
        if (state != Mm9QuestMarkerState::None)
        {
            m_markers[actor.actorId] = state;
        }
    }
    ++m_rebuildCount;
}
} // namespace OpenYAMM::Game
