#include "game/maps/ActorModelManifest.h"

#include "engine/AssetFileSystem.h"
#include "engine/models/GltfModelLoader.h"
#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <optional>
#include <unordered_set>

namespace OpenYAMM::Game
{
bool ActorModelManifest::load(const Engine::AssetFileSystem &assets, const std::vector<std::string> &paths,
    const std::string &activePath, const MonsterTable &monsters, std::string &error)
{
    m_entries.clear();
    m_boundMonsterIds.clear();
    m_entryByMonsterId.clear();
    m_pAssets = &assets;
    const auto read = [&](const std::string &path, bool active)
    {
        const std::optional<std::string> text = assets.readTextFile(path);
        if (!text)
        {
            return true;
        }
        try
        {
            const YAML::Node document = YAML::Load(*text);
            if (!document["actors"].IsSequence())
            {
                error = "actor model manifest requires an actors sequence: " + path;
                return false;
            }
            const std::string attackTiming = document["attack_timing"].as<std::string>("sprite");
            if (attackTiming != "sprite" && attackTiming != "clip")
            {
                error = "actor model manifest attack_timing must be sprite or clip: " + path;
                return false;
            }
            const bool clipsTimeAttacks = attackTiming == "clip";
            const bool fidgetVariants = document["fidget_variants"].as<bool>(false);
            std::unordered_set<std::string> fileDescriptors;
            for (const YAML::Node &entry : document["actors"])
            {
                const std::string descriptor = entry["descriptor"].as<std::string>();
                const MonsterEntry *pMonster = monsters.findByInternalName(descriptor);
                if (pMonster == nullptr || !fileDescriptors.insert(pMonster->internalName).second)
                {
                    error = path + ": unknown or duplicate actor model descriptor: " + descriptor;
                    return false;
                }
                const auto [iterator, inserted] = m_entries.try_emplace(pMonster->internalName,
                    Entry{entry, path, clipsTimeAttacks, fidgetVariants});
                if (!inserted)
                {
                    if (!active)
                    {
                        error = "actor model descriptor bound by " + iterator->second.manifestPath + " and " + path
                            + ": " + descriptor;
                        return false;
                    }
                    iterator->second = Entry{entry, path, clipsTimeAttacks, fidgetVariants};
                }
            }
        }
        catch (const YAML::Exception &exception)
        {
            error = path + ": " + exception.what();
            return false;
        }
        return true;
    };
    for (const std::string &path : paths)
    {
        if (path != activePath && !read(path, false))
        {
            m_entries.clear();
            return false;
        }
    }
    if (!activePath.empty() && !read(activePath, true))
    {
        m_entries.clear();
        return false;
    }
    // Monster ids index the table's entries (MonsterTable::findById).
    const std::vector<MonsterEntry> &monsterEntries = monsters.getEntries();
    m_boundMonsterIds.resize(monsterEntries.size());
    m_entryByMonsterId.resize(monsterEntries.size());
    for (size_t monsterId = 0; monsterId < monsterEntries.size(); ++monsterId)
    {
        m_entryByMonsterId[monsterId] = find(monsterEntries[monsterId].internalName);
        m_boundMonsterIds[monsterId] = m_entryByMonsterId[monsterId] != nullptr;
    }
    m_boundClipsRead = std::make_unique<std::once_flag[]>(monsterEntries.size());
    m_boundClips.assign(monsterEntries.size(), BoundClips{});
    return true;
}

const ActorModelManifest::BoundClips *ActorModelManifest::boundClips(int16_t monsterId) const
{
    if (monsterId < 0 || size_t(monsterId) >= m_entryByMonsterId.size() || m_entryByMonsterId[monsterId] == nullptr)
    {
        return nullptr;
    }
    std::call_once(m_boundClipsRead[monsterId], [&]()
    {
        const std::lock_guard<std::mutex> lock(m_boundClipsReadMutex);
        m_boundClips[monsterId] = readBoundClips(*m_entryByMonsterId[monsterId]);
    });
    return &m_boundClips[monsterId];
}

ActorModelManifest::BoundClips ActorModelManifest::readBoundClips(const Entry &entry) const
{
    BoundClips result;
    result.clipsTimeAttacks = entry.clipsTimeAttacks;
    try
    {
        const YAML::Node clips = entry.node["clips"];
        const YAML::Node animation = entry.node["animation"];
        const YAML::Node events = animation ? animation["events"] : YAML::Node();
        const std::string rangedClip = clips ? clips["attack_ranged"].as<std::string>("") : std::string();
        const std::string castClip = animation && animation["cast"] ? animation["cast"].as<std::string>() : rangedClip;
        const std::array<std::string, 3> clipNames = {
            clips ? clips["attack_melee"].as<std::string>("") : std::string(), rangedClip, castClip};
        const std::array<const char *, 3> eventNames = {"attack_melee", "attack_ranged", "cast"};
        for (size_t role = 0; role < eventNames.size(); ++role)
        {
            const YAML::Node event = events ? events[eventNames[role]] : YAML::Node();
            if (event && event["impact"])
            {
                result.impactSeconds[role] = event["impact"].as<float>();
            }
        }
        if (result.impactSeconds[size_t(AttackRole::Cast)] < 0.0f && castClip == rangedClip)
        {
            result.impactSeconds[size_t(AttackRole::Cast)] = result.impactSeconds[size_t(AttackRole::Ranged)];
        }
        // Only clip-timed attacks and fidget variants need the clips' lengths: the file is read for them alone.
        if ((!entry.clipsTimeAttacks && !entry.fidgetVariants) || m_pAssets == nullptr)
        {
            return result;
        }
        const std::optional<std::unordered_map<std::string, float>> durations =
            Engine::readGltfClipDurations(*m_pAssets, entry.node["model"].as<std::string>(""));
        if (!durations)
        {
            return result;
        }
        const auto clipSeconds = [&](const std::string &name)
        {
            const auto clip = durations->find(name);
            return clip != durations->end() ? clip->second : 0.0f;
        };
        for (size_t role = 0; entry.clipsTimeAttacks && role < clipNames.size(); ++role)
        {
            result.clipSeconds[role] = clipSeconds(clipNames[role]);
        }
        // MM9's fidget list (MM9_AMBIENT_ANIMATION.md section 1): its Fidget* clips, then its Search* clips; the
        // converted models name them `fidget` (the first) and the script clip roles fidget<n> and search<n>. A role
        // playing a clip already listed adds nothing.
        const std::string fidgetClip = clips ? clips["fidget"].as<std::string>("") : std::string();
        if (entry.fidgetVariants && clipSeconds(fidgetClip) > 0.0f)
        {
            std::vector<std::string> listedClips = {fidgetClip};
            result.fidgetRoles.push_back({});
            result.fidgetSeconds.push_back(clipSeconds(fidgetClip));
            const YAML::Node scriptClips = entry.node["script_clips"];
            for (const char *pPrefix : {"fidget", "search"})
            {
                for (const auto &scriptClip : scriptClips)
                {
                    const std::string role = scriptClip.first.as<std::string>();
                    const std::string name = scriptClip.second.as<std::string>();
                    const std::string prefix = pPrefix;
                    const bool numbered = role.size() > prefix.size() && role.starts_with(prefix)
                        && std::all_of(role.begin() + prefix.size(), role.end(),
                            [](char value) { return value >= '0' && value <= '9'; });
                    // `search` itself is MM9's Search; the binding's own `fidget` already stands for its Fidget.
                    const bool listed = numbered || (prefix == "search" && role == prefix);
                    if (!listed)
                    {
                        continue;
                    }
                    if (result.fidgetRoles.size() >= ActorFidgetClips::MaxVariants || clipSeconds(name) <= 0.0f
                        || std::find(listedClips.begin(), listedClips.end(), name) != listedClips.end())
                    {
                        continue;
                    }
                    listedClips.push_back(name);
                    result.fidgetRoles.push_back(role);
                    result.fidgetSeconds.push_back(clipSeconds(name));
                }
            }
        }
    }
    catch (const YAML::Exception &)
    {
        // A malformed binding fails when WorldFxSystem builds it; the gameplay keeps the sprite timing.
        return BoundClips{};
    }
    return result;
}

const ActorModelManifest::Entry *ActorModelManifest::find(const std::string &descriptor) const
{
    const auto iterator = m_entries.find(descriptor);
    return iterator != m_entries.end() ? &iterator->second : nullptr;
}

ActorAttackTiming actorAttackTiming(const ActorModelManifest *pModels, int16_t monsterId,
    ActorModelManifest::AttackRole role, float spriteSeconds, float spriteImpactSeconds)
{
    const ActorModelManifest::BoundClips *pClips = pModels != nullptr ? pModels->boundClips(monsterId) : nullptr;
    if (pClips == nullptr)
    {
        return {spriteSeconds, spriteImpactSeconds};
    }
    return resolveActorAttackTiming(spriteSeconds, spriteImpactSeconds, pClips->clipSeconds[size_t(role)],
        pClips->impactSeconds[size_t(role)], pClips->clipsTimeAttacks);
}

ActorFidgetClips actorFidgetClips(const ActorModelManifest *pModels, int16_t monsterId)
{
    ActorFidgetClips result;
    const ActorModelManifest::BoundClips *pClips = pModels != nullptr ? pModels->boundClips(monsterId) : nullptr;
    for (size_t index = 0; pClips != nullptr && index < pClips->fidgetSeconds.size(); ++index)
    {
        result.seconds[index] = pClips->fidgetSeconds[index];
        result.count = uint8_t(index + 1);
    }
    return result;
}

std::string actorFidgetRole(const ActorModelManifest *pModels, int16_t monsterId, int8_t variant)
{
    const ActorModelManifest::BoundClips *pClips = pModels != nullptr ? pModels->boundClips(monsterId) : nullptr;
    return pClips != nullptr && variant >= 0 && size_t(variant) < pClips->fidgetRoles.size()
        ? pClips->fidgetRoles[size_t(variant)] : std::string();
}
}
