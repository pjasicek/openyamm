#include "game/tables/MonsterRelationAddOns.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <exception>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *RelationsSchema = "openyamm.monsterRelations.v1";

std::optional<int> parseRelation(const YAML::Node &node)
{
    static constexpr std::array<std::pair<const char *, int>, 7> Names = {{
        {"friendly", 0}, {"neutral", 0}, {"close", 1}, {"short", 2}, {"medium", 3}, {"long", 4}, {"hostile", 4}}};
    const std::string text = node.as<std::string>("");
    for (const auto &[name, value] : Names)
    {
        if (text == name)
        {
            return value;
        }
    }
    try
    {
        const int value = node.as<int>();
        if (value >= 0 && value <= 4)
        {
            return value;
        }
    }
    catch (const std::exception &)
    {
    }
    return std::nullopt;
}

// Monster ids: 10065, or a range "10065-10069".
bool parseMonsterIds(const YAML::Node &node, std::vector<int> &ids, std::string &error)
{
    if (!node.IsSequence())
    {
        error = "monsters must be a list of ids or 'first-last' ranges";
        return false;
    }
    for (const YAML::Node &item : node)
    {
        const std::string text = item.as<std::string>();
        const size_t dash = text.find('-', 1);
        try
        {
            const int first = std::stoi(text.substr(0, dash));
            const int last = dash == std::string::npos ? first : std::stoi(text.substr(dash + 1));
            if (first <= 0 || last < first || last - first > 2000)
            {
                error = "invalid monster id range '" + text + "'";
                return false;
            }
            for (int id = first; id <= last; ++id)
            {
                ids.push_back(id);
            }
        }
        catch (const std::exception &)
        {
            error = "invalid monster id '" + text + "'";
            return false;
        }
    }
    return true;
}
}

bool MonsterRelationAddOns::loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t idBegin,
    uint32_t idEnd, std::string &error)
{
    const std::string where = "worlds/" + packageId + "/relations.yml: ";
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root.IsMap() || root["schema"].as<std::string>("") != RelationsSchema)
        {
            error = where + "expected schema " + RelationsSchema;
            return false;
        }

        const size_t firstFaction = m_factionNames.size();
        for (const auto &entry : root["factions"])
        {
            const std::string name = entry.first.as<std::string>();
            if (name == "party" || name == "any"
                || std::find(m_factionNames.begin(), m_factionNames.end(), name) != m_factionNames.end())
            {
                error = where + "faction '" + name + "' is reserved or declared twice";
                return false;
            }
            m_factionNames.push_back(name);
            m_kin.emplace_back();
        }

        const auto factionIndex = [&](const std::string &name) -> int
        {
            const auto found = std::find(m_factionNames.begin(), m_factionNames.end(), name);
            return found != m_factionNames.end() ? int(found - m_factionNames.begin()) : -1;
        };
        const auto factionList = [&](const YAML::Node &node, std::vector<int> &factions) -> bool
        {
            const std::vector<std::string> names = node.IsSequence()
                ? node.as<std::vector<std::string>>() : std::vector<std::string>{node.as<std::string>("")};
            for (const std::string &name : names)
            {
                const int faction = factionIndex(name);
                if (faction < 0)
                {
                    error = where + "unknown faction '" + name + "'";
                    return false;
                }
                factions.push_back(faction);
            }
            return !factions.empty();
        };

        size_t faction = firstFaction;
        for (const auto &entry : root["factions"])
        {
            std::vector<int> ids;
            if (!entry.second.IsMap() || !parseMonsterIds(entry.second["monsters"], ids, error))
            {
                error = where + "faction '" + m_factionNames[faction] + "': " + (error.empty()
                    ? std::string("expected {monsters: [...], kin: [...]}") : error);
                return false;
            }
            for (const int id : ids)
            {
                if (uint32_t(id) < idBegin || uint32_t(id) > idEnd || id > INT16_MAX)
                {
                    error = where + "monster " + std::to_string(id) + " lies outside the world's monster id range";
                    return false;
                }
                if (!m_factionByMonster.emplace(int16_t(id), int(faction)).second)
                {
                    error = where + "monster " + std::to_string(id) + " belongs to two factions";
                    return false;
                }
                m_minimumMonsterId = std::min(m_minimumMonsterId, int16_t(id));
                m_maximumMonsterId = std::max(m_maximumMonsterId, int16_t(id));
            }
            if (entry.second["kin"] && !factionList(entry.second["kin"], m_kin[faction]))
            {
                return false;
            }
            ++faction;
        }

        for (const YAML::Node &node : root["relations"])
        {
            Rule rule;
            if (!node.IsMap() || !node["from"] || !node["to"] || !node["relation"])
            {
                error = where + "a relation needs from, to and relation";
                return false;
            }
            if (!factionList(node["from"], rule.fromFactions))
            {
                return false;
            }
            const std::string target = node["to"].IsScalar() ? node["to"].as<std::string>() : "";
            if (target == "party")
            {
                rule.target = TargetKind::Party;
            }
            else if (target == "any")
            {
                rule.target = TargetKind::Any;
            }
            else if (!factionList(node["to"], rule.toFactions))
            {
                return false;
            }
            const std::optional<int> relation = parseRelation(node["relation"]);
            if (!relation)
            {
                error = where + "relation must be friendly, neutral, close, short, medium, long, hostile or 0-4";
                return false;
            }
            rule.relation = *relation;
            rule.untilQBit = node["until_qbit"].as<uint32_t>(0);
            rule.afterQBit = node["after_qbit"].as<uint32_t>(0);
            if (rule.untilQBit != 0 && rule.afterQBit != 0)
            {
                error = where + "a relation takes until_qbit or after_qbit, not both";
                return false;
            }
            m_hasConditions = m_hasConditions || rule.untilQBit != 0 || rule.afterQBit != 0;
            m_rules.push_back(std::move(rule));
        }
    }
    catch (const std::exception &exception)
    {
        error = where + exception.what();
        return false;
    }

    // Until the first refresh every QBit counts as clear.
    m_ruleActive.assign(m_rules.size(), 0);
    for (size_t index = 0; index < m_rules.size(); ++index)
    {
        m_ruleActive[index] = m_rules[index].afterQBit == 0 ? 1 : 0;
    }
    resolve();
    return true;
}

void MonsterRelationAddOns::clear()
{
    *this = {};
}

int MonsterRelationAddOns::factionOf(int16_t monsterId) const
{
    if (monsterId < m_minimumMonsterId || monsterId > m_maximumMonsterId)
    {
        return -1;
    }
    const auto found = m_factionByMonster.find(monsterId);
    return found != m_factionByMonster.end() ? found->second : -1;
}

const std::string &MonsterRelationAddOns::factionName(int faction) const
{
    static const std::string none;
    return faction >= 0 && size_t(faction) < m_factionNames.size() ? m_factionNames[size_t(faction)] : none;
}

std::optional<int> MonsterRelationAddOns::relationBetween(int16_t actorMonsterId, int16_t targetMonsterId) const
{
    const int from = factionOf(actorMonsterId);
    if (from < 0)
    {
        return std::nullopt;
    }
    const size_t width = m_factionNames.size() + 1;
    const int to = factionOf(targetMonsterId);
    if (to >= 0 && m_pairRelations[size_t(from) * width + size_t(to)] >= 0)
    {
        return m_pairRelations[size_t(from) * width + size_t(to)];
    }
    const int8_t any = m_pairRelations[size_t(from) * width + width - 1];
    return any >= 0 ? std::optional<int>(any) : std::nullopt;
}

std::optional<int> MonsterRelationAddOns::relationToParty(int16_t monsterId) const
{
    const int faction = factionOf(monsterId);
    return faction >= 0 && m_partyRelations[size_t(faction)] >= 0
        ? std::optional<int>(m_partyRelations[size_t(faction)]) : std::nullopt;
}

std::optional<bool> MonsterRelationAddOns::sameFaction(int16_t leftMonsterId, int16_t rightMonsterId) const
{
    const int left = factionOf(leftMonsterId);
    const int right = factionOf(rightMonsterId);
    if (left < 0 && right < 0)
    {
        return std::nullopt;
    }
    if (left < 0 || right < 0)
    {
        return false;
    }
    const std::vector<int> &kin = m_kin[size_t(left)];
    return left == right || std::find(kin.begin(), kin.end(), right) != kin.end();
}

bool MonsterRelationAddOns::refreshConditions(const std::function<bool(uint32_t)> &isQBitSet) const
{
    if (!m_hasConditions)
    {
        return false;
    }
    bool changed = false;
    for (size_t index = 0; index < m_rules.size(); ++index)
    {
        const Rule &rule = m_rules[index];
        const uint8_t active = rule.untilQBit != 0 ? !isQBitSet(rule.untilQBit)
            : rule.afterQBit != 0 ? isQBitSet(rule.afterQBit) : 1;
        changed = changed || active != m_ruleActive[index];
        m_ruleActive[index] = active;
    }
    if (changed || m_revision == 0)
    {
        resolve();
        ++m_revision;
        return true;
    }
    return false;
}

bool MonsterRelationAddOns::partyRelationIsConditional(int16_t monsterId) const
{
    const int faction = factionOf(monsterId);
    if (faction < 0)
    {
        return false;
    }
    return std::any_of(m_rules.begin(), m_rules.end(), [&](const Rule &rule)
    {
        return rule.target == TargetKind::Party && (rule.untilQBit != 0 || rule.afterQBit != 0)
            && std::find(rule.fromFactions.begin(), rule.fromFactions.end(), faction) != rule.fromFactions.end();
    });
}

void MonsterRelationAddOns::resolve() const
{
    const size_t factions = m_factionNames.size();
    const size_t width = factions + 1;
    m_pairRelations.assign(factions * width, -1);
    m_partyRelations.assign(factions, -1);
    // In file order: a later active rule overrides an earlier one for the same pair.
    for (size_t index = 0; index < m_rules.size(); ++index)
    {
        if (m_ruleActive[index] == 0)
        {
            continue;
        }
        const Rule &rule = m_rules[index];
        for (const int from : rule.fromFactions)
        {
            switch (rule.target)
            {
                case TargetKind::Party:
                    m_partyRelations[size_t(from)] = int8_t(rule.relation);
                    break;
                case TargetKind::Any:
                    // "any" also covers the factions: later specific rules still override it.
                    for (size_t to = 0; to < width; ++to)
                    {
                        m_pairRelations[size_t(from) * width + to] = int8_t(rule.relation);
                    }
                    break;
                case TargetKind::Factions:
                    for (const int to : rule.toFactions)
                    {
                        m_pairRelations[size_t(from) * width + size_t(to)] = int8_t(rule.relation);
                    }
                    break;
            }
        }
    }
}
}
