#include "game/maps/ActorModelManifest.h"

#include "engine/AssetFileSystem.h"
#include "engine/models/GltfModelLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cmath>
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
            const std::string gait = document["gait"].as<std::string>("speed");
            if (gait != "speed" && gait != "intent")
            {
                error = "actor model manifest gait must be speed or intent: " + path;
                return false;
            }
            const bool gaitFollowsIntent = gait == "intent";
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
                    Entry{entry, path, clipsTimeAttacks, fidgetVariants, gaitFollowsIntent});
                if (!inserted)
                {
                    if (!active)
                    {
                        error = "actor model descriptor bound by " + iterator->second.manifestPath + " and " + path
                            + ": " + descriptor;
                        return false;
                    }
                    iterator->second = Entry{entry, path, clipsTimeAttacks, fidgetVariants, gaitFollowsIntent};
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
    // actor_sounds.yml beside each actors.yml: its entries join the bindings that file's actors.yml made.
    std::vector<std::string> manifestPaths = paths;
    if (!activePath.empty() && std::find(paths.begin(), paths.end(), activePath) == paths.end())
    {
        manifestPaths.push_back(activePath);
    }
    for (const std::string &path : manifestPaths)
    {
        const std::string soundsPath = path.substr(0, path.rfind('/') + 1) + "actor_sounds.yml";
        const std::optional<std::string> text = assets.readTextFile(soundsPath);
        if (!text)
        {
            continue;
        }
        try
        {
            const YAML::Node document = YAML::Load(*text);
            for (const YAML::Node &item : document["actors"])
            {
                const std::string descriptor = item["descriptor"].as<std::string>();
                const MonsterEntry *pMonster = monsters.findByInternalName(descriptor);
                const auto entry = pMonster != nullptr ? m_entries.find(pMonster->internalName) : m_entries.end();
                if (entry == m_entries.end())
                {
                    error = soundsPath + ": sounds for an unbound actor model descriptor: " + descriptor;
                    m_entries.clear();
                    return false;
                }
                if (entry->second.manifestPath == path)
                {
                    entry->second.sounds = item;
                }
            }
        }
        catch (const YAML::Exception &exception)
        {
            error = soundsPath + ": " + exception.what();
            m_entries.clear();
            return false;
        }
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
    m_scaleReferenceRatios = std::make_unique<std::atomic<float>[]>(monsterEntries.size());
    for (size_t monsterId = 0; monsterId < monsterEntries.size(); ++monsterId)
    {
        m_scaleReferenceRatios[monsterId].store(-1.0f, std::memory_order_relaxed);
    }
    return true;
}

float ActorModelManifest::scaleReferenceRatio(int16_t monsterId, const MonsterTable &monsters,
    const SpriteFrameTable *pSpriteFrames) const
{
    const BoundClips *pClips = boundClips(monsterId);
    if (pClips == nullptr || pClips->scaleReference.empty())
    {
        return 1.0f;
    }
    const float known = m_scaleReferenceRatios[monsterId].load(std::memory_order_relaxed);
    if (known > 0.0f || pSpriteFrames == nullptr)
    {
        return std::max(known, 0.0f);
    }
    // The scale of the monster's standing sprite's first frame (WorldFxSystem's scale_reference).
    const auto standingScale = [&](const MonsterEntry *pMonster)
    {
        const std::optional<uint16_t> frame = pMonster != nullptr
            ? pSpriteFrames->findFrameIndexBySpriteName(pMonster->spriteNames[0]) : std::nullopt;
        const SpriteFrameEntry *pFrame = frame ? pSpriteFrames->getFrame(*frame, 0) : nullptr;
        return pFrame != nullptr && std::isfinite(pFrame->scale) && pFrame->scale > 0.0f ? pFrame->scale : 0.0f;
    };
    const float scale = standingScale(monsters.findById(monsterId));
    const float reference = standingScale(monsters.findByInternalName(pClips->scaleReference));
    if (scale <= 0.0f || reference <= 0.0f)
    {
        return 0.0f;
    }
    m_scaleReferenceRatios[monsterId].store(scale / reference, std::memory_order_relaxed);
    return scale / reference;
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
        result.scaleReference = entry.node["scale_reference"].as<std::string>("");
        result.zOffset = entry.node["z_offset"].as<float>(0.0f);
        const std::optional<Engine::GltfModelSummary> summary = m_pAssets != nullptr
            ? Engine::readGltfModelSummary(*m_pAssets, entry.node["model"].as<std::string>(""))
            : std::nullopt;
        if (!summary)
        {
            return result;
        }
        // The model's height, where the party aims (actorTargetHeight).
        const float scale = entry.node["scale"].as<float>(0.0f);
        if (summary->bindPoseHeightRange && scale > 0.0f)
        {
            result.bodyBottom = (*summary->bindPoseHeightRange)[0] * scale;
            result.bodyTop = (*summary->bindPoseHeightRange)[1] * scale;
        }
        // Only clip-timed attacks and fidget variants use the clips' lengths.
        if (!entry.clipsTimeAttacks && !entry.fidgetVariants)
        {
            return result;
        }
        const std::unordered_map<std::string, float> &durations = summary->clipDurations;
        const auto clipSeconds = [&](const std::string &name)
        {
            const auto clip = durations.find(name);
            return clip != durations.end() ? clip->second : 0.0f;
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
                    if (result.fidgetRoles.size() >= ActorClipChoices::MaxVariants || clipSeconds(name) <= 0.0f
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
        // MM9's conversation list (MM9_AMBIENT_ANIMATION.md section 1): the clip named exactly Conv when the model has
        // one (the role `conv`), else Conv0-Conv9 (the roles conv<n>); a clip already listed adds nothing.
        const YAML::Node scriptClips = entry.node["script_clips"];
        const bool exactConv =
            scriptClips && scriptClips["conv"] && clipSeconds(scriptClips["conv"].as<std::string>("")) > 0.0f;
        std::vector<std::string> convClips;
        for (const auto &scriptClip : scriptClips)
        {
            const std::string role = scriptClip.first.as<std::string>();
            const std::string name = scriptClip.second.as<std::string>();
            const bool numbered = role.size() == 5 && role.starts_with("conv") && role[4] >= '0' && role[4] <= '9';
            if ((exactConv ? role != "conv" : !numbered) || result.convRoles.size() >= ActorClipChoices::MaxVariants
                || clipSeconds(name) <= 0.0f || std::find(convClips.begin(), convClips.end(), name) != convClips.end())
            {
                continue;
            }
            convClips.push_back(name);
            result.convRoles.push_back(role);
            result.convSeconds.push_back(clipSeconds(name));
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

float actorTargetHeight(const MonsterTable &monsters, const SpriteFrameTable *pSpriteFrames, int16_t monsterId,
    uint16_t height, uint16_t bodyHeight, float drawScale, float visualScale)
{
    const ActorModelManifest *pModels = monsters.actorModels();
    const MonsterEntry *pMonster = monsters.findById(monsterId);
    const float sizeScale = drawScale > 0.0f ? drawScale
        : pMonster != nullptr && pMonster->height > 0 && bodyHeight > 0 ? float(bodyHeight) / pMonster->height : 1.0f;
    const float modelScale = visualScale * sizeScale;
    const ActorModelManifest::BoundClips *pClips = pModels != nullptr ? pModels->boundClips(monsterId) : nullptr;
    const float referenceRatio =
        pClips != nullptr ? pModels->scaleReferenceRatio(monsterId, monsters, pSpriteFrames) : 0.0f;
    if (pClips == nullptr || !(pClips->bodyTop > pClips->bodyBottom) || referenceRatio <= 0.0f || modelScale <= 0.0f)
    {
        return GameMechanics::actorTargetHeight(height);
    }
    const float scale = referenceRatio * modelScale;
    return GameMechanics::actorTargetHeight(
        height, pClips->zOffset + pClips->bodyBottom * scale, pClips->zOffset + pClips->bodyTop * scale);
}

ActorClipChoices actorFidgetClips(const ActorModelManifest *pModels, int16_t monsterId)
{
    ActorClipChoices result;
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

ActorClipChoices actorConvClips(const ActorModelManifest *pModels, int16_t monsterId)
{
    ActorClipChoices result;
    const ActorModelManifest::BoundClips *pClips = pModels != nullptr ? pModels->boundClips(monsterId) : nullptr;
    for (size_t index = 0; pClips != nullptr && index < pClips->convSeconds.size(); ++index)
    {
        result.seconds[index] = pClips->convSeconds[index];
        result.count = uint8_t(index + 1);
    }
    return result;
}

std::string actorConvRole(const ActorModelManifest *pModels, int16_t monsterId, int8_t variant)
{
    const ActorModelManifest::BoundClips *pClips = pModels != nullptr ? pModels->boundClips(monsterId) : nullptr;
    return pClips != nullptr && variant >= 0 && size_t(variant) < pClips->convRoles.size()
        ? pClips->convRoles[size_t(variant)] : std::string();
}
}
