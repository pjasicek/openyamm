#include "game/fx/EffectSystem.h"

#include <algorithm>
#include <cmath>
#include <unordered_set>

namespace OpenYAMM::Game
{
std::vector<std::string> EffectSystem::activeSpriteResources() const
{
    std::vector<std::string> result;
    for (const Slot &slot : m_slots)
    {
        if (!slot.active || !slot.definition)
        {
            continue;
        }
        for (const EffectSpriteDefinition &sprite : slot.definition->sprites)
        {
            result.push_back(sprite.spriteResource);
        }
        for (const EffectSpriteEmitterDefinition &emitter : slot.definition->spriteEmitters)
        {
            result.push_back(emitter.spriteResource);
        }
        for (const EffectRibbonDefinition &ribbon : slot.definition->ribbons)
        {
            result.push_back(ribbon.spriteResource);
        }
    }
    std::sort(result.begin(), result.end());
    result.erase(std::unique(result.begin(), result.end()), result.end());
    return result;
}

namespace
{
constexpr float MaximumAccumulationSeconds = 0.25f;

std::array<float, 3> add(const std::array<float, 3> &left, const std::array<float, 3> &right)
{
    return {left[0] + right[0], left[1] + right[1], left[2] + right[2]};
}

std::array<float, 3> multiply(const std::array<float, 3> &value, float scale)
{
    return {value[0] * scale, value[1] * scale, value[2] * scale};
}

float length(const std::array<float, 3> &value)
{
    return std::sqrt(value[0] * value[0] + value[1] * value[1] + value[2] * value[2]);
}

std::array<float, 3> normalized(
    const std::array<float, 3> &value,
    const std::array<float, 3> &fallback = {0.0f, 0.0f, 0.0f})
{
    const float valueLength = length(value);
    return valueLength > 0.0f ? multiply(value, 1.0f / valueLength) : fallback;
}

std::array<float, 3> cross(const std::array<float, 3> &left, const std::array<float, 3> &right)
{
    return {
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    };
}

std::array<float, 3> rotateByQuaternion(
    const std::array<float, 3> &value,
    const std::array<float, 4> &rotation)
{
    const std::array<float, 3> quaternionVector = {rotation[0], rotation[1], rotation[2]};
    const std::array<float, 3> twiceCross = multiply(cross(quaternionVector, value), 2.0f);
    return add(value, add(multiply(twiceCross, rotation[3]), cross(quaternionVector, twiceCross)));
}

std::array<float, 3> rotateByAxisAngleVector(
    const std::array<float, 3> &value,
    const std::array<float, 3> &rotation)
{
    const float angle = length(rotation);
    if (angle < 1.0e-9f)
    {
        return value;
    }
    const std::array<float, 3> axis = multiply(rotation, 1.0f / angle);
    const float cosine = std::cos(angle);
    const float sine = std::sin(angle);
    return add(
        add(multiply(value, cosine), multiply(cross(axis, value), sine)),
        multiply(axis, (axis[0] * value[0] + axis[1] * value[1] + axis[2] * value[2]) * (1.0f - cosine)));
}

std::array<float, 3> sampleVectorTrack(
    const std::vector<EffectVectorKey> &keys,
    float phase,
    const std::array<float, 3> &fallback)
{
    if (keys.empty())
    {
        return fallback;
    }
    if (phase <= keys.front().time)
    {
        return keys.front().value;
    }
    for (size_t index = 1; index < keys.size(); ++index)
    {
        if (phase < keys[index].time)
        {
            const EffectVectorKey &left = keys[index - 1];
            const EffectVectorKey &right = keys[index];
            const float amount = (phase - left.time) / (right.time - left.time);
            return add(left.value, multiply(add(right.value, multiply(left.value, -1.0f)), amount));
        }
    }
    return keys.back().value;
}

float sampleScalarTrack(const std::vector<EffectScalarKey> &keys, float phase, float fallback)
{
    if (keys.empty())
    {
        return fallback;
    }
    if (phase <= keys.front().time)
    {
        return keys.front().value;
    }
    for (size_t index = 1; index < keys.size(); ++index)
    {
        if (phase < keys[index].time)
        {
            const EffectScalarKey &left = keys[index - 1];
            const EffectScalarKey &right = keys[index];
            const float amount = (phase - left.time) / (right.time - left.time);
            return left.value + (right.value - left.value) * amount;
        }
    }
    return keys.back().value;
}

std::array<float, 4> sampleColorTrack(
    const std::vector<EffectColorKey> &keys,
    float phase,
    float lifetimeSeconds,
    EffectTimingProfile timingProfile)
{
    if (keys.empty())
    {
        return {1.0f, 1.0f, 1.0f, 1.0f};
    }
    const EffectColorKey *pLeft = &keys.front();
    const EffectColorKey *pRight = pLeft;
    float amount = 0.0f;
    if (timingProfile == EffectTimingProfile::Mm9Native && phase >= lifetimeSeconds)
    {
        pLeft = pRight = &keys.back();
    }
    else
    {
        for (size_t index = 1; index < keys.size(); ++index)
        {
            if (phase < keys[index].time)
            {
                pLeft = &keys[index - 1];
                pRight = &keys[index];
                amount = (phase - pLeft->time) / (pRight->time - pLeft->time);
                break;
            }
            pLeft = pRight = &keys[index];
        }
    }

    std::array<float, 4> color = {};
    for (size_t component = 0; component < 3; ++component)
    {
        color[component] = (static_cast<float>(pLeft->rgb[component]) +
            (static_cast<float>(pRight->rgb[component]) - static_cast<float>(pLeft->rgb[component])) * amount) /
            255.0f;
    }
    const float transparency = static_cast<float>(pLeft->transparency) +
        (static_cast<float>(pRight->transparency) - static_cast<float>(pLeft->transparency)) * amount;
    color[3] = std::clamp(1.0f - transparency / 255.0f, 0.0f, 1.0f);
    return color;
}

bool isFiniteVector(const std::array<float, 3> &value)
{
    return std::isfinite(value[0]) && std::isfinite(value[1]) && std::isfinite(value[2]);
}

bool isValidSpritePlane(
    EffectSpriteAlignment alignment,
    const std::array<float, 3> &planeRight,
    const std::array<float, 3> &planeUp)
{
    if (alignment != EffectSpriteAlignment::WorldPlane)
    {
        return true;
    }
    return isFiniteVector(planeRight) && isFiniteVector(planeUp) &&
        length(planeRight) > 1.0e-6f && length(planeUp) > 1.0e-6f &&
        length(cross(planeRight, planeUp)) > 1.0e-6f;
}

bool validateTrackValues(
    const std::vector<EffectScalarKey> &scaleKeys,
    const std::vector<EffectVectorKey> &motionKeys,
    std::string &error)
{
    for (const EffectScalarKey &key : scaleKeys)
    {
        if (!std::isfinite(key.value))
        {
            error = "scale keys must have finite values";
            return false;
        }
    }
    for (const EffectVectorKey &key : motionKeys)
    {
        if (!isFiniteVector(key.value))
        {
            error = "motion keys must have finite values";
            return false;
        }
    }
    return true;
}

template <typename Key>
bool validateTrack(const std::vector<Key> &keys, const std::string &name, std::string &error)
{
    float previousTime = -1.0f;
    for (const Key &key : keys)
    {
        if (!std::isfinite(key.time) || key.time < 0.0f || key.time > 1.0f || key.time < previousTime)
        {
            error = name + " keys must have finite, non-decreasing times in [0, 1]";
            return false;
        }
        previousTime = key.time;
    }
    return true;
}

bool validateDefinition(const EffectDefinition &definition, std::string &error)
{
    if (definition.id.empty())
    {
        error = "effect definition has no id";
        return false;
    }
    if (!std::isfinite(definition.durationSeconds) || definition.durationSeconds <= 0.0f)
    {
        error = "effect '" + definition.id + "' has invalid duration";
        return false;
    }
    std::unordered_set<uint32_t> componentIds;
    std::unordered_set<uint32_t> modelComponentIds;
    for (const EffectModelDefinition &model : definition.models)
    {
        if (!componentIds.insert(model.componentId).second)
        {
            error = "effect '" + definition.id + "' has duplicate component id";
            return false;
        }
        const bool valid = std::isfinite(model.startSeconds) && std::isfinite(model.endSeconds) &&
            model.startSeconds >= 0.0f && model.endSeconds >= model.startSeconds &&
            model.endSeconds <= definition.durationSeconds && model.repeatCount != 0 &&
            !model.modelResource.empty() && isFiniteVector(model.offset);
        if (!valid)
        {
            error = "effect '" + definition.id + "' has invalid model component " +
                std::to_string(model.componentId);
            return false;
        }
        modelComponentIds.insert(model.componentId);
    }
    for (const EffectNullDefinition &null : definition.nulls)
    {
        if (!componentIds.insert(null.componentId).second)
        {
            error = "effect '" + definition.id + "' has duplicate component id";
            return false;
        }
        const bool valid = std::isfinite(null.startSeconds) && std::isfinite(null.endSeconds) &&
            null.startSeconds >= 0.0f && null.endSeconds >= null.startSeconds &&
            null.endSeconds <= definition.durationSeconds && null.repeatCount != 0 &&
            isFiniteVector(null.offset) && isFiniteVector(null.rotationPerTick);
        if (!valid || !validateTrack(null.scaleKeys, "scale", error) ||
            !validateTrack(null.motionKeys, "motion", error) ||
            !validateTrackValues(null.scaleKeys, null.motionKeys, error))
        {
            error = "effect '" + definition.id + "' has invalid null component " +
                std::to_string(null.componentId) + (error.empty() ? "" : ": " + error);
            return false;
        }
    }
    for (const EffectSpriteDefinition &sprite : definition.sprites)
    {
        if (!componentIds.insert(sprite.componentId).second)
        {
            error = "effect '" + definition.id + "' has duplicate component id";
            return false;
        }
        const bool valid = std::isfinite(sprite.startSeconds) && std::isfinite(sprite.endSeconds) &&
            sprite.startSeconds >= 0.0f && sprite.endSeconds >= sprite.startSeconds &&
            sprite.endSeconds <= definition.durationSeconds && sprite.repeatCount != 0 &&
            !sprite.spriteResource.empty() && isFiniteVector(sprite.offset) &&
            std::isfinite(sprite.stretchU) && sprite.stretchU > 0.0f &&
            std::isfinite(sprite.stretchV) && sprite.stretchV > 0.0f &&
            isValidSpritePlane(sprite.alignment, sprite.planeRight, sprite.planeUp);
        if (!valid || !validateTrack(sprite.colorKeys, "color", error) ||
            !validateTrack(sprite.scaleKeys, "scale", error) ||
            !validateTrack(sprite.motionKeys, "motion", error) ||
            !validateTrackValues(sprite.scaleKeys, sprite.motionKeys, error))
        {
            error = "effect '" + definition.id + "' has invalid sprite component " +
                std::to_string(sprite.componentId) + (error.empty() ? "" : ": " + error);
            return false;
        }
    }
    for (const EffectSpriteEmitterDefinition &emitter : definition.spriteEmitters)
    {
        if (!componentIds.insert(emitter.componentId).second)
        {
            error = "effect '" + definition.id + "' has duplicate component id";
            return false;
        }
        const bool validTimes = std::isfinite(emitter.startSeconds) && std::isfinite(emitter.endSeconds) &&
            emitter.startSeconds >= 0.0f && emitter.endSeconds >= emitter.startSeconds &&
            emitter.endSeconds <= definition.durationSeconds;
        if (!validTimes || emitter.repeatCount == 0 || emitter.spriteResource.empty() ||
            !std::isfinite(emitter.emissionIntervalSeconds) || emitter.emissionIntervalSeconds < 0.0f ||
            !std::isfinite(emitter.emissionDistance) || emitter.emissionDistance < 0.0f ||
            !std::isfinite(emitter.spinSpeed) || !std::isfinite(emitter.gravity) ||
            (emitter.emissionDistance > 0.0f && emitter.particleSpace == EffectParticleSpace::Local) ||
            !std::isfinite(emitter.particleLifetimeSeconds) || emitter.particleLifetimeSeconds <= 0.0f ||
            !std::isfinite(emitter.radius) || emitter.radius < 0.0f || !std::isfinite(emitter.velocity) ||
            !isFiniteVector(emitter.planeDirection) || !isFiniteVector(emitter.windDirection) ||
            !isFiniteVector(emitter.offset) || !isFiniteVector(emitter.rotationPerTick) ||
            !isValidSpritePlane(emitter.alignment, emitter.planeRight, emitter.planeUp))
        {
            error = "effect '" + definition.id + "' has invalid sprite component " +
                std::to_string(emitter.componentId);
            return false;
        }
        if (!validateTrack(emitter.colorKeys, "color", error) ||
            !validateTrack(emitter.scaleKeys, "scale", error) ||
            !validateTrack(emitter.motionKeys, "motion", error) ||
            !validateTrackValues(emitter.scaleKeys, emitter.motionKeys, error))
        {
            error = "effect '" + definition.id + "': " + error;
            return false;
        }
    }
    for (const EffectRibbonDefinition &ribbon : definition.ribbons)
    {
        if (!componentIds.insert(ribbon.componentId).second)
        {
            error = "effect '" + definition.id + "' has duplicate component id";
            return false;
        }
        const bool valid = std::isfinite(ribbon.startSeconds) && std::isfinite(ribbon.endSeconds) &&
            ribbon.startSeconds >= 0.0f && ribbon.endSeconds >= ribbon.startSeconds &&
            ribbon.endSeconds <= definition.durationSeconds && !ribbon.spriteResource.empty() &&
            isFiniteVector(ribbon.offset) && std::isfinite(ribbon.lifetimeSeconds) && ribbon.lifetimeSeconds > 0.0f &&
            std::isfinite(ribbon.maxLength) && ribbon.maxLength >= 0.0f &&
            std::isfinite(ribbon.sampleDistance) && ribbon.sampleDistance > 0.0f &&
            std::isfinite(ribbon.width) && ribbon.width > 0.0f &&
            std::isfinite(ribbon.textureLength) && ribbon.textureLength > 0.0f && std::isfinite(ribbon.scrollSpeed) &&
            std::isfinite(ribbon.fill) && ribbon.fill >= 0.0f &&
            std::isfinite(ribbon.erosion) && ribbon.erosion >= 0.0f && ribbon.erosion <= 1.0f &&
            std::isfinite(ribbon.core) && ribbon.core >= 0.0f &&
            std::isfinite(ribbon.jitter) && ribbon.jitter >= 0.0f &&
            std::isfinite(ribbon.jitterRate) && ribbon.jitterRate >= 0.0f;
        if (!valid || !validateTrack(ribbon.widthKeys, "width", error) ||
            !validateTrack(ribbon.colorKeys, "color", error) ||
            !validateTrackValues(ribbon.widthKeys, {}, error))
        {
            error = "effect '" + definition.id + "' has invalid ribbon component " +
                std::to_string(ribbon.componentId) + (error.empty() ? "" : ": " + error);
            return false;
        }
    }
    for (const EffectSoundDefinition &sound : definition.sounds)
    {
        if (!componentIds.insert(sound.componentId).second)
        {
            error = "effect '" + definition.id + "' has duplicate component id";
            return false;
        }
        const bool valid = std::isfinite(sound.startSeconds) && std::isfinite(sound.endSeconds) &&
            sound.startSeconds >= 0.0f && sound.endSeconds >= sound.startSeconds &&
            sound.endSeconds <= definition.durationSeconds && !sound.soundResource.empty() &&
            std::isfinite(sound.volume) && sound.volume >= 0.0f && std::isfinite(sound.pitch) &&
            sound.pitch > 0.0f && std::isfinite(sound.innerRadius) && sound.innerRadius >= 0.0f &&
            std::isfinite(sound.outerRadius) && sound.outerRadius >= sound.innerRadius;
        if (!valid)
        {
            error = "effect '" + definition.id + "' has invalid sound component " +
                std::to_string(sound.componentId);
            return false;
        }
    }
    const auto validateLink = [&](const EffectComponentLink &link) -> bool
    {
        if (!link.componentId)
        {
            return true;
        }
        if (link.nodeName.empty() || !modelComponentIds.contains(*link.componentId))
        {
            error = "effect '" + definition.id + "' has invalid model-node link";
            return false;
        }
        return true;
    };
    for (const EffectModelDefinition &model : definition.models)
    {
        if (!validateLink(model.link))
        {
            return false;
        }
    }
    for (const EffectNullDefinition &null : definition.nulls)
    {
        if (!validateLink(null.link))
        {
            return false;
        }
    }
    for (const EffectSpriteDefinition &sprite : definition.sprites)
    {
        if (!validateLink(sprite.link))
        {
            return false;
        }
    }
    for (const EffectSpriteEmitterDefinition &emitter : definition.spriteEmitters)
    {
        if (!validateLink(emitter.link))
        {
            return false;
        }
    }
    return true;
}
}

bool EffectLibrary::add(std::shared_ptr<const EffectDefinition> definition, std::string &error)
{
    if (definition == nullptr)
    {
        error = "effect definition is null";
        return false;
    }
    if (!validateDefinition(*definition, error))
    {
        return false;
    }
    if (!m_definitions.emplace(definition->id, definition).second)
    {
        error = "duplicate effect definition id: " + definition->id;
        return false;
    }
    return true;
}

bool EffectLibrary::replace(
    const std::vector<std::shared_ptr<const EffectDefinition>> &definitions,
    std::string &error)
{
    std::unordered_map<std::string, std::shared_ptr<const EffectDefinition>> replacements;
    for (const std::shared_ptr<const EffectDefinition> &definition : definitions)
    {
        if (definition == nullptr || !validateDefinition(*definition, error))
        {
            if (definition == nullptr)
            {
                error = "effect definition is null";
            }
            return false;
        }
        if (!replacements.emplace(definition->id, definition).second)
        {
            error = "duplicate effect definition id: " + definition->id;
            return false;
        }
    }
    m_definitions = std::move(replacements);
    return true;
}

const EffectDefinition *EffectLibrary::find(const std::string &id) const
{
    const auto iterator = m_definitions.find(id);
    return iterator != m_definitions.end() ? iterator->second.get() : nullptr;
}

std::vector<std::string> EffectLibrary::ids() const
{
    std::vector<std::string> result;
    result.reserve(m_definitions.size());
    for (const auto &[id, definition] : m_definitions)
    {
        result.push_back(id);
    }
    std::sort(result.begin(), result.end());
    return result;
}

void EffectLibrary::clear()
{
    m_definitions.clear();
}

size_t EffectLibrary::size() const
{
    return m_definitions.size();
}

EffectSystem::EffectSystem(const EffectLibrary *pLibrary)
    : m_pLibrary(pLibrary)
{
}

void EffectSystem::setLibrary(const EffectLibrary *pLibrary)
{
    clear();
    m_pLibrary = pLibrary;
}

void EffectSystem::setModelRuntime(
    Engine::ModelInstanceSystem *pInstances,
    std::function<std::shared_ptr<const Engine::ModelAsset>(const std::string &)> resolver)
{
    clear();
    m_pModelInstances = pInstances;
    m_modelResolver = std::move(resolver);
}

EffectHandle EffectSystem::spawn(const std::string &id, const EffectSpawnParams &params)
{
    if (m_pLibrary == nullptr || !std::isfinite(params.scale) || params.scale <= 0.0f)
    {
        return {};
    }
    const EffectDefinition *pDefinition = m_pLibrary->find(id);
    if (pDefinition == nullptr)
    {
        return {};
    }

    uint32_t index = 0;
    if (m_freeIndices.empty())
    {
        index = static_cast<uint32_t>(m_slots.size());
        m_slots.emplace_back();
    }
    else
    {
        index = m_freeIndices.back();
        m_freeIndices.pop_back();
    }

    Slot &slot = m_slots[index];
    slot.active = true;
    slot.paused = false;
    slot.draining = false;
    slot.elapsedSeconds = 0.0f;
    slot.transform = params;
    slot.travelDirection = normalized(rotateByQuaternion({1.0f, 0.0f, 0.0f}, params.rotation), {1.0f, 0.0f, 0.0f});
    slot.ribbonsStarted.assign(pDefinition->ribbons.size(), false);
    slot.definition = m_pLibrary->m_definitions.at(id);
    slot.random.state = params.seed;
    resetEmitters(slot);
    slot.sounds.assign(pDefinition->sounds.size(), {});
    slot.models.clear();
    ++m_activeCount;
    if (!createModels(slot))
    {
        finishSlot(index, slot, true);
        return {};
    }
    updateModels(slot);
    updateFixedSprites(index, slot);
    updateSounds(index, slot);
    return {index, slot.generation};
}

bool EffectSystem::setTransform(
    EffectHandle handle,
    const std::array<float, 3> &position,
    const std::array<float, 4> &rotation,
    float scale)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr || !std::isfinite(scale) || scale <= 0.0f)
    {
        return false;
    }
    const std::array<float, 3> movement = add(position, multiply(pSlot->transform.position, -1.0f));
    if (length(movement) > 0.01f)
    {
        pSlot->travelDirection = normalized(movement);
    }
    pSlot->transform.position = position;
    pSlot->transform.rotation = rotation;
    pSlot->transform.scale = scale;
    updateModels(*pSlot);
    updateFixedSprites(handle.index, *pSlot);
    // Ribbon heads follow at once too, so a fast trail stays attached to its head between reference ticks.
    for (EffectRibbon &ribbon : m_ribbons)
    {
        if (ribbon.owner != handle || !ribbon.emitting || ribbon.points.size() < 2)
        {
            continue;
        }
        const EffectRibbonDefinition &definition = ribbon.settings();
        EffectRibbonPoint &head = ribbon.points.back();
        head.position = add(position, rotateByQuaternion(multiply(definition.offset, scale), rotation));
        const EffectRibbonPoint &previous = ribbon.points[ribbon.points.size() - 2];
        head.distance = previous.distance + length(add(head.position, multiply(previous.position, -1.0f)));
    }
    for (size_t soundIndex = 0; soundIndex < pSlot->sounds.size(); ++soundIndex)
    {
        const EffectSoundDefinition &sound = pSlot->definition->sounds[soundIndex];
        if (pSlot->sounds[soundIndex].started && !pSlot->sounds[soundIndex].stopped && sound.followsEmitter)
        {
            m_soundEvents.push_back({
                .kind = EffectSoundEventKind::Move,
                .owner = handle,
                .componentId = sound.componentId,
                .soundResource = sound.soundResource,
                .position = position,
                .spatial = sound.spatial,
                .loop = sound.loop,
                .volume = sound.volume,
                .pitch = sound.pitch,
                .innerRadius = sound.innerRadius,
                .outerRadius = sound.outerRadius,
            });
        }
    }
    return true;
}

bool EffectSystem::stop(EffectHandle handle, EffectStopMode mode)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    if (mode == EffectStopMode::Immediate)
    {
        finishSlot(handle.index, *pSlot, true);
    }
    else
    {
        pSlot->draining = true;
    }
    return true;
}

bool EffectSystem::pause(EffectHandle handle, bool paused)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->paused = paused;
    return true;
}

bool EffectSystem::restart(EffectHandle handle)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    for (size_t soundIndex = 0; soundIndex < pSlot->sounds.size(); ++soundIndex)
    {
        if (pSlot->sounds[soundIndex].started && !pSlot->sounds[soundIndex].stopped)
        {
            const EffectSoundDefinition &sound = pSlot->definition->sounds[soundIndex];
            m_soundEvents.push_back({
                .kind = EffectSoundEventKind::Stop,
                .owner = handle,
                .componentId = sound.componentId,
                .soundResource = sound.soundResource,
                .position = pSlot->transform.position,
            });
        }
    }
    m_particles.erase(
        std::remove_if(
            m_particles.begin(),
            m_particles.end(),
            [&](const EffectParticle &particle)
            {
                return particle.owner == handle;
            }),
        m_particles.end());
    m_ribbons.erase(
        std::remove_if(
            m_ribbons.begin(),
            m_ribbons.end(),
            [&](const EffectRibbon &ribbon)
            {
                return ribbon.owner == handle;
            }),
        m_ribbons.end());
    pSlot->ribbonsStarted.assign(pSlot->definition->ribbons.size(), false);
    pSlot->paused = false;
    pSlot->draining = false;
    pSlot->elapsedSeconds = 0.0f;
    pSlot->random.state = pSlot->transform.seed;
    resetEmitters(*pSlot);
    pSlot->sounds.assign(pSlot->definition->sounds.size(), {});
    updateModels(*pSlot);
    updateFixedSprites(handle.index, *pSlot);
    updateSounds(handle.index, *pSlot);
    return true;
}

bool EffectSystem::seek(EffectHandle handle, float timeSeconds)
{
    if (!std::isfinite(timeSeconds) || timeSeconds < 0.0f || !restart(handle))
    {
        return false;
    }
    const float stepSeconds = 1.0f / static_cast<float>(m_referenceUpdatesPerSecond);
    while (contains(handle) && elapsedSeconds(handle) + stepSeconds <= timeSeconds + 1.0e-6f)
    {
        Slot *pSlot = find(handle);
        updateParticles(stepSeconds, &handle);
        tickInstance(handle.index, *pSlot, stepSeconds);
    }
    return contains(handle);
}

bool EffectSystem::setReferenceUpdateRate(uint32_t updatesPerSecond)
{
    if (updatesPerSecond != 30 && updatesPerSecond != 60 && updatesPerSecond != 120)
    {
        return false;
    }
    m_referenceUpdatesPerSecond = updatesPerSecond;
    m_updateAccumulatorSeconds = 0.0f;
    return true;
}

uint32_t EffectSystem::referenceUpdateRate() const
{
    return m_referenceUpdatesPerSecond;
}

void EffectSystem::update(float deltaSeconds, bool worldPaused)
{
    if (worldPaused || !std::isfinite(deltaSeconds) || deltaSeconds <= 0.0f)
    {
        return;
    }
    m_updateAccumulatorSeconds = std::min(
        MaximumAccumulationSeconds,
        m_updateAccumulatorSeconds + deltaSeconds);
    const float stepSeconds = 1.0f / static_cast<float>(m_referenceUpdatesPerSecond);
    while (m_updateAccumulatorSeconds + 1.0e-6f >= stepSeconds)
    {
        tick(stepSeconds);
        m_updateAccumulatorSeconds = std::max(0.0f, m_updateAccumulatorSeconds - stepSeconds);
    }
}

void EffectSystem::clear()
{
    for (uint32_t slotIndex = 0; slotIndex < m_slots.size(); ++slotIndex)
    {
        if (m_slots[slotIndex].active)
        {
            finishSlot(slotIndex, m_slots[slotIndex], true);
        }
    }
    m_particles.clear();
    m_fixedSprites.clear();
    m_ribbons.clear();
    m_freeIndices.clear();
    for (uint32_t index = 0; index < m_slots.size(); ++index)
    {
        m_freeIndices.push_back(index);
    }
    m_activeCount = 0;
    m_updateAccumulatorSeconds = 0.0f;
}

bool EffectSystem::contains(EffectHandle handle) const
{
    return find(handle) != nullptr;
}

float EffectSystem::elapsedSeconds(EffectHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->elapsedSeconds : 0.0f;
}

size_t EffectSystem::size() const
{
    return m_activeCount;
}

size_t EffectSystem::estimatedTransientBytes() const
{
    size_t bytes = m_slots.capacity() * sizeof(Slot)
        + m_freeIndices.capacity() * sizeof(uint32_t)
        + m_particles.capacity() * sizeof(EffectParticle)
        + m_fixedSprites.capacity() * sizeof(EffectFixedSprite)
        + m_ribbons.capacity() * sizeof(EffectRibbon)
        + m_soundEvents.capacity() * sizeof(EffectSoundEvent);
    for (const Slot &slot : m_slots)
    {
        bytes += slot.emitters.capacity() * sizeof(EmitterState)
            + slot.sounds.capacity() * sizeof(SoundState)
            + slot.models.capacity() * sizeof(ModelState);
        for (const EmitterState &emitter : slot.emitters)
        {
            bytes += emitter.cachedSamples.capacity() * sizeof(EmissionSample);
        }
    }
    for (const EffectRibbon &ribbon : m_ribbons)
    {
        bytes += ribbon.points.capacity() * sizeof(EffectRibbonPoint);
    }
    return bytes;
}

const std::vector<EffectParticle> &EffectSystem::particles() const
{
    return m_particles;
}

const std::vector<EffectFixedSprite> &EffectSystem::fixedSprites() const
{
    return m_fixedSprites;
}

const std::vector<EffectRibbon> &EffectSystem::ribbons() const
{
    return m_ribbons;
}

std::vector<EffectSoundEvent> EffectSystem::consumeSoundEvents()
{
    std::vector<EffectSoundEvent> events = std::move(m_soundEvents);
    m_soundEvents.clear();
    return events;
}

uint32_t EffectSystem::Random::next()
{
    state = state * 214013u + 2531011u;
    return (state >> 16) & 32767u;
}

float EffectSystem::Random::signedValue()
{
    return static_cast<float>(static_cast<int>(next() % 20000u) - 10000) / 10000.0f;
}

EffectSystem::Slot *EffectSystem::find(EffectHandle handle)
{
    if (handle.index >= m_slots.size())
    {
        return nullptr;
    }
    Slot &slot = m_slots[handle.index];
    return slot.active && slot.generation == handle.generation ? &slot : nullptr;
}

const EffectSystem::Slot *EffectSystem::find(EffectHandle handle) const
{
    if (handle.index >= m_slots.size())
    {
        return nullptr;
    }
    const Slot &slot = m_slots[handle.index];
    return slot.active && slot.generation == handle.generation ? &slot : nullptr;
}

void EffectSystem::tick(float stepSeconds)
{
    updateParticles(stepSeconds);
    for (uint32_t slotIndex = 0; slotIndex < m_slots.size(); ++slotIndex)
    {
        Slot &slot = m_slots[slotIndex];
        if (slot.active && !slot.paused)
        {
            tickInstance(slotIndex, slot, stepSeconds);
        }
    }
}

void EffectSystem::tickInstance(uint32_t slotIndex, Slot &slot, float stepSeconds)
{
    slot.elapsedSeconds += stepSeconds;
    updateModels(slot);
    updateFixedSprites(slotIndex, slot);
    updateRibbons(slotIndex, slot, stepSeconds);
    for (size_t emitterIndex = 0; emitterIndex < slot.definition->spriteEmitters.size(); ++emitterIndex)
    {
        const EffectSpriteEmitterDefinition &definition = slot.definition->spriteEmitters[emitterIndex];
        EmitterState &state = slot.emitters[emitterIndex];
        if (!state.started && slot.elapsedSeconds >= definition.startSeconds)
        {
            startEmitter(slot, emitterIndex);
        }
        if (!state.started || state.finished)
        {
            continue;
        }
        const bool emitting = !slot.draining && slot.elapsedSeconds < definition.endSeconds;
        if (emitting && definition.emissionDistance > 0.0f)
        {
            emitParticlesAlongPath(slotIndex, slot, emitterIndex, stepSeconds);
        }
        else if (emitting && slot.elapsedSeconds - state.lastEmissionSeconds > definition.emissionIntervalSeconds)
        {
            emitParticles(slotIndex, slot, emitterIndex);
            state.lastEmissionSeconds = slot.elapsedSeconds;
        }
        state.rotation = add(state.rotation, definition.rotationPerTick);
        if (!emitting)
        {
            const EffectHandle owner = {slotIndex, slot.generation};
            state.finished = std::none_of(
                m_particles.begin(),
                m_particles.end(),
                [&](const EffectParticle &particle)
                {
                    return particle.owner == owner && particle.componentId == definition.componentId;
                });
        }
    }

    updateSounds(slotIndex, slot);
    const bool emittersFinished = std::all_of(
        slot.emitters.begin(),
        slot.emitters.end(),
        [](const EmitterState &state)
        {
            return !state.started || state.finished;
        });
    const bool soundsFinished = std::all_of(
        slot.sounds.begin(),
        slot.sounds.end(),
        [](const SoundState &state)
        {
            return !state.started || state.stopped;
        });
    if ((slot.draining || slot.elapsedSeconds >= slot.definition->durationSeconds) &&
        emittersFinished && soundsFinished && !hasRibbons({slotIndex, slot.generation}))
    {
        finishSlot(slotIndex, slot, false);
    }
}

void EffectSystem::resetEmitters(Slot &slot)
{
    slot.emitters.assign(slot.definition->spriteEmitters.size(), {});
    if (slot.transform.bodyAnchor.empty())
    {
        return;
    }
    for (size_t emitterIndex = 0; emitterIndex < slot.emitters.size(); ++emitterIndex)
    {
        const std::string &anchor = slot.definition->spriteEmitters[emitterIndex].bodyAnchor;
        if (!anchor.empty() && anchor != slot.transform.bodyAnchor)
        {
            slot.emitters[emitterIndex].started = true;
            slot.emitters[emitterIndex].finished = true;
        }
    }
}

void EffectSystem::startEmitter(Slot &slot, size_t emitterIndex)
{
    const EffectSpriteEmitterDefinition &definition = slot.definition->spriteEmitters[emitterIndex];
    EmitterState &state = slot.emitters[emitterIndex];
    state.started = true;
    const std::array<float, 3> basePosition =
        linkedPosition(slot, definition.link).value_or(slot.transform.position);
    state.previousPosition = definition.particleSpace == EffectParticleSpace::Local
        ? definition.offset
        : add(
            basePosition,
            rotateByQuaternion(multiply(definition.offset, slot.transform.scale), slot.transform.rotation));
    // A full spacing already travelled: the first distance emission lands on the starting point.
    state.distanceSinceEmission = definition.emissionDistance * slot.transform.scale;
    if (slot.definition->timingProfile != EffectTimingProfile::Mm9Native)
    {
        return;
    }
    state.cachedSamples.reserve(256);
    for (size_t sampleIndex = 0; sampleIndex < 256; ++sampleIndex)
    {
        state.cachedSamples.push_back(createEmissionSample(slot, definition));
    }
}

EffectSystem::EmissionSample EffectSystem::createEmissionSample(
    Slot &slot,
    const EffectSpriteEmitterDefinition &definition)
{
    const std::array<float, 3> normal = normalized(definition.planeDirection, {0.0f, 1.0f, 0.0f});
    const std::array<float, 3> basis = std::abs(normal[1]) > 0.99f
        ? std::array<float, 3>{1.0f, 0.0f, 0.0f}
        : std::array<float, 3>{0.0f, 1.0f, 0.0f};
    const std::array<float, 3> u = normalized(cross(normal, basis));
    const std::array<float, 3> v = cross(normal, u);
    EmissionSample sample;
    switch (definition.emissionShape)
    {
    case EffectEmissionShape::Point:
        sample.velocity = {
            slot.random.signedValue() * definition.velocity,
            slot.random.signedValue() * definition.velocity,
            slot.random.signedValue() * definition.velocity,
        };
        break;
    case EffectEmissionShape::Plane:
    case EffectEmissionShape::Circle:
        sample.offset = add(
            multiply(u, slot.random.signedValue() * definition.radius),
            multiply(v, slot.random.signedValue() * definition.radius));
        sample.velocity = multiply(normal, definition.velocity);
        break;
    case EffectEmissionShape::Sphere:
        sample.offset = multiply(normalized({
            slot.random.signedValue(),
            slot.random.signedValue(),
            slot.random.signedValue(),
        }), definition.radius);
        sample.velocity = multiply(normalized(sample.offset), definition.velocity);
        break;
    case EffectEmissionShape::PlaneIn:
    case EffectEmissionShape::PlaneOut:
        sample.offset = multiply(normalized(add(
            multiply(u, slot.random.signedValue() * definition.radius),
            multiply(v, slot.random.signedValue() * definition.radius))), definition.radius);
        sample.velocity = multiply(
            normalized(sample.offset),
            definition.emissionShape == EffectEmissionShape::PlaneIn
                ? -definition.velocity : definition.velocity);
        break;
    case EffectEmissionShape::Cone:
        sample.velocity = multiply(normalized(add(
            add(
                multiply(u, slot.random.signedValue() * definition.radius),
                multiply(v, slot.random.signedValue() * definition.radius)),
            multiply(normal, 100.0f))), definition.velocity);
        break;
    }
    return sample;
}

std::array<float, 3> EffectSystem::emitterCenter(
    const Slot &slot,
    const EffectSpriteEmitterDefinition &definition) const
{
    const float duration = (definition.endSeconds - definition.startSeconds) /
        static_cast<float>(std::max(1u, definition.repeatCount));
    const float phase = duration > 0.0f
        ? std::fmod(slot.elapsedSeconds - definition.startSeconds, duration) / duration : 0.0f;
    const std::array<float, 3> motion = sampleVectorTrack(definition.motionKeys, phase, {});
    const std::array<float, 3> localCenter = add(definition.offset, motion);
    if (definition.particleSpace == EffectParticleSpace::Local)
    {
        return localCenter;
    }
    const std::array<float, 3> basePosition =
        linkedPosition(slot, definition.link).value_or(slot.transform.position);
    return add(
        basePosition,
        rotateByQuaternion(
            multiply(localCenter, slot.transform.scale),
            slot.transform.rotation));
}

EffectSystem::EmissionSample EffectSystem::nextEmissionSample(
    Slot &slot,
    const EffectSpriteEmitterDefinition &definition,
    EmitterState &state)
{
    EmissionSample sample = state.cachedSamples.empty()
        ? createEmissionSample(slot, definition)
        : state.cachedSamples[slot.random.next() & 255u];
    sample.velocity = rotateByAxisAngleVector(sample.velocity, state.rotation);
    return sample;
}

void EffectSystem::spawnParticle(
    uint32_t slotIndex,
    Slot &slot,
    const EffectSpriteEmitterDefinition &definition,
    const EmissionSample &sample,
    const std::array<float, 3> &center,
    float ageSeconds)
{
    EffectParticle particle;
    particle.owner = {slotIndex, slot.generation};
    particle.componentId = definition.componentId;
    particle.spriteResource = internSpriteResource(definition.spriteResource);
    particle.particleSpace = definition.particleSpace;
    particle.alignment = definition.alignment;
    particle.planeRight = rotateByQuaternion(definition.planeRight, slot.transform.rotation);
    particle.planeUp = rotateByQuaternion(definition.planeUp, slot.transform.rotation);
    if (definition.particleSpace == EffectParticleSpace::Local)
    {
        particle.localPosition = add(center, sample.offset);
        particle.localVelocity = sample.velocity;
        particle.position = add(
            slot.transform.position,
            rotateByQuaternion(
                multiply(particle.localPosition, slot.transform.scale),
                slot.transform.rotation));
        particle.velocity = rotateByQuaternion(
            multiply(particle.localVelocity, slot.transform.scale),
            slot.transform.rotation);
    }
    else
    {
        particle.position = add(
            center,
            rotateByQuaternion(multiply(sample.offset, slot.transform.scale), slot.transform.rotation));
        particle.velocity = rotateByQuaternion(
            multiply(sample.velocity, slot.transform.scale),
            slot.transform.rotation);
    }
    particle.lifetimeSeconds = definition.particleLifetimeSeconds;
    particle.ageSeconds = ageSeconds;
    particle.spriteAnimationSeconds = ageSeconds;
    const float phase = ageSeconds / std::max(particle.lifetimeSeconds, 0.01f);
    particle.scale = sampleScalarTrack(definition.scaleKeys, phase, 0.2f) * slot.transform.scale;
    particle.color = sampleColorTrack(
        definition.colorKeys,
        phase,
        definition.particleLifetimeSeconds,
        slot.definition->timingProfile);
    particle.stretchU = definition.stretchU;
    particle.stretchV = definition.stretchV;
    particle.blendMode = definition.blendMode;
    particle.additiveTextureAlpha = definition.additiveTextureAlpha;
    if (definition.randomRoll)
    {
        particle.roll = (slot.random.signedValue() + 1.0f) * 3.14159265f;
    }
    if (definition.spinSpeed != 0.0f)
    {
        const float turn = slot.random.signedValue();
        particle.rollSpeed = definition.spinSpeed * (turn < 0.0f ? -0.5f + turn * 0.5f : 0.5f + turn * 0.5f);
        particle.roll += particle.rollSpeed * ageSeconds;
    }
    if (definition.alignment == EffectSpriteAlignment::Velocity)
    {
        particle.planeRight = normalized(particle.velocity, slot.travelDirection);
    }
    m_particles.push_back(std::move(particle));
}

void EffectSystem::emitParticles(uint32_t slotIndex, Slot &slot, size_t emitterIndex)
{
    const EffectSpriteEmitterDefinition &definition = slot.definition->spriteEmitters[emitterIndex];
    EmitterState &state = slot.emitters[emitterIndex];
    const std::array<float, 3> center = emitterCenter(slot, definition);
    const uint32_t particleCount = definition.spritesPerEmission;
    for (uint32_t particleIndex = 0; particleIndex < particleCount; ++particleIndex)
    {
        const EmissionSample sample = nextEmissionSample(slot, definition, state);
        const float interpolation = static_cast<float>(particleIndex) / static_cast<float>(particleCount);
        const std::array<float, 3> batchCenter = add(
            center,
            multiply(add(state.previousPosition, multiply(center, -1.0f)), interpolation));
        spawnParticle(slotIndex, slot, definition, sample, batchCenter, 0.0f);
    }
    state.previousPosition = center;
}

void EffectSystem::emitParticlesAlongPath(uint32_t slotIndex, Slot &slot, size_t emitterIndex, float stepSeconds)
{
    // A jump this many spacings long in one step is a teleport, not a path: restart the trail at the new position.
    constexpr float MaxEmissionsPerStep = 64.0f;
    const EffectSpriteEmitterDefinition &definition = slot.definition->spriteEmitters[emitterIndex];
    EmitterState &state = slot.emitters[emitterIndex];
    const std::array<float, 3> center = emitterCenter(slot, definition);
    const std::array<float, 3> segment = add(center, multiply(state.previousPosition, -1.0f));
    const float segmentLength = length(segment);
    const float spacing = std::max(definition.emissionDistance * slot.transform.scale, 0.01f);
    if (segmentLength > spacing * MaxEmissionsPerStep)
    {
        state.previousPosition = center;
        state.distanceSinceEmission = 0.0f;
        return;
    }
    // Points are spaced along the path; the older end of the step was passed earlier, so its particles start older.
    float distance = std::max(spacing - state.distanceSinceEmission, 0.0f);
    float lastEmission = -state.distanceSinceEmission;
    while (distance <= segmentLength)
    {
        const float fraction = segmentLength > 0.0f ? distance / segmentLength : 1.0f;
        const std::array<float, 3> point = add(state.previousPosition, multiply(segment, fraction));
        const float ageSeconds = (1.0f - fraction) * stepSeconds;
        for (uint32_t particleIndex = 0; particleIndex < definition.spritesPerEmission; ++particleIndex)
        {
            spawnParticle(slotIndex, slot, definition, nextEmissionSample(slot, definition, state), point, ageSeconds);
        }
        lastEmission = distance;
        distance += spacing;
    }
    state.distanceSinceEmission = segmentLength - lastEmission;
    state.previousPosition = center;
}

void EffectSystem::updateParticles(float stepSeconds, const EffectHandle *pOwnerFilter)
{
    for (EffectParticle &particle : m_particles)
    {
        if (pOwnerFilter != nullptr && particle.owner != *pOwnerFilter)
        {
            continue;
        }
        const Slot *pOwner = find(particle.owner);
        if (pOwner == nullptr || pOwner->paused)
        {
            continue;
        }
        const auto emitterIterator = std::find_if(
            pOwner->definition->spriteEmitters.begin(),
            pOwner->definition->spriteEmitters.end(),
            [&](const EffectSpriteEmitterDefinition &definition)
            {
                return definition.componentId == particle.componentId;
            });
        if (emitterIterator == pOwner->definition->spriteEmitters.end())
        {
            continue;
        }
        const EffectSpriteEmitterDefinition &definition = *emitterIterator;
        particle.ageSeconds += stepSeconds;
        particle.roll += particle.rollSpeed * stepSeconds;
        particle.spriteAnimationSeconds += pOwner->definition->timingProfile == EffectTimingProfile::Mm9Native
            ? std::floor(stepSeconds * 1000.0f) / 1000.0f : stepSeconds;
        const std::array<float, 3> localWind = multiply(definition.windDirection, definition.windAmount);
        if (particle.particleSpace == EffectParticleSpace::Local)
        {
            particle.localPosition = add(
                particle.localPosition,
                multiply(add(particle.localVelocity, localWind), stepSeconds));
            const std::array<float, 3> basePosition =
                linkedPosition(*pOwner, definition.link).value_or(pOwner->transform.position);
            particle.position = add(
                basePosition,
                rotateByQuaternion(
                    multiply(particle.localPosition, pOwner->transform.scale),
                    pOwner->transform.rotation));
            particle.velocity = rotateByQuaternion(
                multiply(particle.localVelocity, pOwner->transform.scale),
                pOwner->transform.rotation);
            if (definition.alignment == EffectSpriteAlignment::Velocity)
            {
                particle.planeRight = normalized(particle.velocity, pOwner->travelDirection);
            }
            else
            {
                particle.planeRight = rotateByQuaternion(definition.planeRight, pOwner->transform.rotation);
                particle.planeUp = rotateByQuaternion(definition.planeUp, pOwner->transform.rotation);
            }
        }
        else
        {
            const std::array<float, 3> wind = rotateByQuaternion(
                multiply(localWind, pOwner->transform.scale),
                pOwner->transform.rotation);
            if (definition.gravity != 0.0f)
            {
                particle.velocity[2] -= definition.gravity * pOwner->transform.scale * stepSeconds;
                if (definition.alignment == EffectSpriteAlignment::Velocity)
                {
                    particle.planeRight = normalized(particle.velocity, particle.planeRight);
                }
            }
            particle.position = add(particle.position, multiply(add(particle.velocity, wind), stepSeconds));
        }
        const float phase = particle.ageSeconds / std::max(particle.lifetimeSeconds, 0.01f);
        particle.color = sampleColorTrack(
            definition.colorKeys,
            phase,
            particle.lifetimeSeconds,
            pOwner->definition->timingProfile);
        particle.scale = sampleScalarTrack(
            definition.scaleKeys,
            std::fmod(phase, 1.0f),
            0.2f) * pOwner->transform.scale;
    }
    m_particles.erase(
        std::remove_if(
            m_particles.begin(),
            m_particles.end(),
            [&](const EffectParticle &particle)
            {
                if (pOwnerFilter != nullptr && particle.owner != *pOwnerFilter)
                {
                    return false;
                }
                const Slot *pOwner = find(particle.owner);
                if (pOwner == nullptr)
                {
                    return true;
                }
                const float earlyExpiry = pOwner->definition->timingProfile == EffectTimingProfile::Mm9Native
                    ? 0.1f : 0.0f;
                return particle.ageSeconds + 1.0e-6f >=
                    std::max(0.0f, particle.lifetimeSeconds - earlyExpiry);
            }),
        m_particles.end());
}

void EffectSystem::updateSounds(uint32_t slotIndex, Slot &slot)
{
    for (size_t soundIndex = 0; soundIndex < slot.definition->sounds.size(); ++soundIndex)
    {
        const EffectSoundDefinition &definition = slot.definition->sounds[soundIndex];
        SoundState &state = slot.sounds[soundIndex];
        const EffectHandle owner = {slotIndex, slot.generation};
        if (!state.started && !slot.draining && slot.elapsedSeconds >= definition.startSeconds)
        {
            state.started = true;
            m_soundEvents.push_back({
                .kind = EffectSoundEventKind::Start,
                .owner = owner,
                .componentId = definition.componentId,
                .soundResource = definition.soundResource,
                .position = slot.transform.position,
                .spatial = definition.spatial,
                .loop = definition.loop,
                .volume = definition.volume,
                .pitch = definition.pitch,
                .innerRadius = definition.innerRadius,
                .outerRadius = definition.outerRadius,
            });
        }
        if (state.started && !state.stopped && (slot.draining || slot.elapsedSeconds >= definition.endSeconds))
        {
            state.stopped = true;
            m_soundEvents.push_back({
                .kind = EffectSoundEventKind::Stop,
                .owner = owner,
                .componentId = definition.componentId,
                .soundResource = definition.soundResource,
                .position = slot.transform.position,
            });
        }
    }
}

bool EffectSystem::createModels(Slot &slot)
{
    if (slot.definition->models.empty())
    {
        return true;
    }
    if (m_pModelInstances == nullptr || !m_modelResolver)
    {
        return false;
    }
    slot.models.reserve(slot.definition->models.size());
    for (const EffectModelDefinition &definition : slot.definition->models)
    {
        const std::shared_ptr<const Engine::ModelAsset> asset = m_modelResolver(definition.modelResource);
        if (asset == nullptr)
        {
            return false;
        }
        const std::array<float, 3> basePosition =
            linkedPosition(slot, definition.link).value_or(slot.transform.position);
        const std::array<float, 3> position = add(
            basePosition,
            rotateByQuaternion(multiply(definition.offset, slot.transform.scale), slot.transform.rotation));
        const Engine::ModelInstanceHandle handle = m_pModelInstances->create(
            asset,
            Engine::gltfModelPlacement(position, slot.transform.rotation, slot.transform.scale));
        const bool playbackReady = definition.animationClip.empty()
            || (m_pModelInstances->play(handle, definition.animationClip, Engine::ModelPlaybackMode::Once)
                && m_pModelInstances->pause(handle, true));
        if (!m_pModelInstances->contains(handle) || !playbackReady || !m_pModelInstances->setVisible(handle, false))
        {
            if (m_pModelInstances->contains(handle))
            {
                m_pModelInstances->destroy(handle);
            }
            return false;
        }
        slot.models.push_back({handle});
    }
    return true;
}

void EffectSystem::updateModels(Slot &slot)
{
    if (m_pModelInstances == nullptr)
    {
        return;
    }
    for (size_t modelIndex = 0; modelIndex < slot.models.size(); ++modelIndex)
    {
        const EffectModelDefinition &definition = slot.definition->models[modelIndex];
        const Engine::ModelInstanceHandle handle = slot.models[modelIndex].handle;
        const std::array<float, 3> basePosition =
            linkedPosition(slot, definition.link).value_or(slot.transform.position);
        const std::array<float, 3> position = add(
            basePosition,
            rotateByQuaternion(multiply(definition.offset, slot.transform.scale), slot.transform.rotation));
        m_pModelInstances->setTransform(
            handle,
            Engine::gltfModelPlacement(position, slot.transform.rotation, slot.transform.scale));
        const bool active = !slot.draining && slot.elapsedSeconds >= definition.startSeconds &&
            slot.elapsedSeconds < definition.endSeconds;
        m_pModelInstances->setVisible(handle, active && definition.visible);
        if (!active)
        {
            continue;
        }
        const float cycleSeconds = (definition.endSeconds - definition.startSeconds) /
            static_cast<float>(definition.repeatCount);
        const float modelTime = cycleSeconds > 0.0f
            ? std::fmod(slot.elapsedSeconds - definition.startSeconds, cycleSeconds) : 0.0f;
        if (!definition.animationClip.empty())
        {
            m_pModelInstances->setTime(handle, modelTime);
        }
    }
}

void EffectSystem::updateFixedSprites(uint32_t slotIndex, Slot &slot)
{
    const EffectHandle owner = {slotIndex, slot.generation};
    m_fixedSprites.erase(
        std::remove_if(
            m_fixedSprites.begin(),
            m_fixedSprites.end(),
            [&](const EffectFixedSprite &sprite)
            {
                return sprite.owner == owner;
            }),
        m_fixedSprites.end());
    if (slot.draining)
    {
        return;
    }
    for (const EffectSpriteDefinition &definition : slot.definition->sprites)
    {
        if (slot.elapsedSeconds < definition.startSeconds || slot.elapsedSeconds >= definition.endSeconds)
        {
            continue;
        }
        const float cycleSeconds = (definition.endSeconds - definition.startSeconds) /
            static_cast<float>(definition.repeatCount);
        const float componentSeconds = slot.elapsedSeconds - definition.startSeconds;
        const float phase = cycleSeconds > 0.0f
            ? std::fmod(componentSeconds, cycleSeconds) / cycleSeconds : 0.0f;
        const std::array<float, 3> motion = sampleVectorTrack(definition.motionKeys, phase, {});
        const std::array<float, 3> localPosition = add(definition.offset, motion);
        const std::array<float, 3> basePosition =
            linkedPosition(slot, definition.link).value_or(slot.transform.position);
        EffectFixedSprite sprite;
        sprite.owner = owner;
        sprite.componentId = definition.componentId;
        sprite.spriteResource = internSpriteResource(definition.spriteResource);
        sprite.position = add(
            basePosition,
            rotateByQuaternion(multiply(localPosition, slot.transform.scale), slot.transform.rotation));
        sprite.color = sampleColorTrack(
            definition.colorKeys,
            phase,
            cycleSeconds,
            slot.definition->timingProfile);
        sprite.scale = sampleScalarTrack(definition.scaleKeys, phase, 1.0f) * slot.transform.scale;
        sprite.stretchU = definition.stretchU;
        sprite.stretchV = definition.stretchV;
        sprite.spriteAnimationSeconds = componentSeconds;
        sprite.blendMode = definition.blendMode;
        sprite.additiveTextureAlpha = definition.additiveTextureAlpha;
        sprite.alignment = definition.alignment;
        sprite.planeRight = definition.alignment == EffectSpriteAlignment::Velocity
            ? slot.travelDirection
            : rotateByQuaternion(definition.planeRight, slot.transform.rotation);
        sprite.planeUp = rotateByQuaternion(definition.planeUp, slot.transform.rotation);
        m_fixedSprites.push_back(std::move(sprite));
    }
}

void EffectSystem::updateBeam(EffectRibbon &ribbon, const Slot &slot, const std::array<float, 3> &start) const
{
    // A beam has no trail: while it lasts, samples every sample_distance from its start to the beam target (the start
    // itself without one); when it ends it is gone.
    ribbon.points.clear();
    if (!ribbon.emitting)
    {
        return;
    }
    const EffectRibbonDefinition &definition = ribbon.settings();
    const std::array<float, 3> end = slot.hasBeamTarget ? slot.beamTarget : start;
    const std::array<float, 3> span = add(end, multiply(start, -1.0f));
    const float beamLength = length(span);
    const size_t segments = std::clamp<size_t>(
        size_t(std::ceil(beamLength / std::max(1.0f, definition.sampleDistance * slot.transform.scale))), 1u, 512u);
    const uint32_t jitterStep = static_cast<uint32_t>(ribbon.elapsedSeconds * definition.jitterRate);
    const float width = definition.width * slot.transform.scale;
    const std::array<float, 4> color = sampleColorTrack(definition.colorKeys, 0.0f, definition.lifetimeSeconds,
        slot.definition->timingProfile);
    for (size_t index = 0; index <= segments; ++index)
    {
        const float along = float(index) / float(segments);
        EffectRibbonPoint point;
        point.position = add(start, multiply(span, along));
        point.distance = beamLength * along;
        point.serial = uint32_t(index);
        point.width = width * sampleScalarTrack(definition.widthKeys, along, 1.0f);
        point.color = color;
        if (definition.jitter > 0.0f && index != 0 && index != segments)
        {
            uint32_t hash = (point.serial + 1u) * 2654435761u ^ (jitterStep + 7u) * 2246822519u;
            hash ^= hash >> 15;
            hash *= 2246822519u;
            hash ^= hash >> 13;
            const float random = static_cast<float>(hash & 0xffffu) / 32767.5f - 1.0f;
            point.jitterOffset = random * definition.jitter * slot.transform.scale;
        }
        ribbon.points.push_back(point);
    }
}

bool EffectSystem::setBeamTarget(EffectHandle handle, const std::array<float, 3> &target)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->beamTarget = target;
    pSlot->hasBeamTarget = true;
    return true;
}

void EffectSystem::updateRibbons(uint32_t slotIndex, Slot &slot, float stepSeconds)
{
    const EffectHandle owner = {slotIndex, slot.generation};
    const std::vector<EffectRibbonDefinition> &definitions = slot.definition->ribbons;
    const auto headPosition = [&](const EffectRibbonDefinition &definition)
    {
        return add(
            slot.transform.position,
            rotateByQuaternion(multiply(definition.offset, slot.transform.scale), slot.transform.rotation));
    };
    for (size_t index = 0; index < definitions.size(); ++index)
    {
        if (slot.ribbonsStarted[index] || slot.draining || slot.elapsedSeconds < definitions[index].startSeconds)
        {
            continue;
        }
        slot.ribbonsStarted[index] = true;
        EffectRibbon ribbon;
        ribbon.owner = owner;
        ribbon.componentId = definitions[index].componentId;
        ribbon.definition = slot.definition;
        ribbon.definitionIndex = index;
        ribbon.scale = slot.transform.scale;
        const std::array<float, 3> head = headPosition(definitions[index]);
        ribbon.points.push_back({head, 0.0f, 0.0f, ribbon.nextSerial++});
        ribbon.points.push_back({head, 0.0f, 0.0f, ribbon.nextSerial++});
        m_ribbons.push_back(std::move(ribbon));
    }
    for (EffectRibbon &ribbon : m_ribbons)
    {
        if (ribbon.owner != owner)
        {
            continue;
        }
        const EffectRibbonDefinition &definition = ribbon.settings();
        ribbon.elapsedSeconds += stepSeconds;
        ribbon.scale = slot.transform.scale;
        ribbon.emitting = !slot.draining && slot.elapsedSeconds < definition.endSeconds;
        if (definition.beam)
        {
            updateBeam(ribbon, slot, headPosition(definition));
            continue;
        }
        for (EffectRibbonPoint &point : ribbon.points)
        {
            point.ageSeconds += stepSeconds;
        }
        if (ribbon.emitting)
        {
            if (ribbon.points.empty())
            {
                ribbon.points.push_back({headPosition(definition), 0.0f, 0.0f, ribbon.nextSerial++});
            }
            // The last point follows the effect; it is left behind as a sample once it is sample_distance from the
            // previous one, and a new live head takes its place.
            EffectRibbonPoint &head = ribbon.points.back();
            head.position = headPosition(definition);
            head.ageSeconds = 0.0f;
            if (ribbon.points.size() >= 2)
            {
                const EffectRibbonPoint &previous = ribbon.points[ribbon.points.size() - 2];
                const float segment = length(add(head.position, multiply(previous.position, -1.0f)));
                head.distance = previous.distance + segment;
                if (segment >= definition.sampleDistance * slot.transform.scale)
                {
                    EffectRibbonPoint next = head;
                    next.serial = ribbon.nextSerial++;
                    ribbon.points.push_back(next);
                }
            }
            else
            {
                EffectRibbonPoint next = head;
                next.serial = ribbon.nextSerial++;
                ribbon.points.push_back(next);
            }
        }
        const float maxLength = definition.maxLength * slot.transform.scale;
        const float headDistance = ribbon.points.empty() ? 0.0f : ribbon.points.back().distance;
        const auto pointPhase = [&](const EffectRibbonPoint &point)
        {
            const float agePhase = point.ageSeconds / definition.lifetimeSeconds;
            const float lengthPhase = maxLength > 0.0f ? (headDistance - point.distance) / maxLength : 0.0f;
            return std::max(agePhase, lengthPhase);
        };
        const size_t keep = ribbon.emitting ? 1u : 0u;
        size_t expired = 0;
        // Drop a sample once the next one has also run out, so the strip ends exactly at the limit (that last
        // segment is clipped by fading to transparent at phase 1).
        while (ribbon.points.size() - expired > keep &&
            (ribbon.points[expired].ageSeconds >= definition.lifetimeSeconds ||
                (ribbon.points.size() - expired > 1 && pointPhase(ribbon.points[expired + 1]) >= 1.0f)))
        {
            ++expired;
        }
        ribbon.points.erase(ribbon.points.begin(), ribbon.points.begin() + static_cast<std::ptrdiff_t>(expired));
        const uint32_t jitterStep = static_cast<uint32_t>(ribbon.elapsedSeconds * definition.jitterRate);
        for (EffectRibbonPoint &point : ribbon.points)
        {
            point.phase = std::clamp(pointPhase(point), 0.0f, 1.0f);
            point.width = definition.width * slot.transform.scale * sampleScalarTrack(definition.widthKeys, point.phase,
                1.0f);
            point.color = sampleColorTrack(definition.colorKeys, point.phase, definition.lifetimeSeconds,
                slot.definition->timingProfile);
            point.jitterOffset = 0.0f;
            if (definition.jitter > 0.0f)
            {
                // Hash of the sample and the current jitter step; the live head stays put.
                uint32_t hash = (point.serial + 1u) * 2654435761u ^ (jitterStep + 7u) * 2246822519u;
                hash ^= hash >> 15;
                hash *= 2246822519u;
                hash ^= hash >> 13;
                const float random = static_cast<float>(hash & 0xffffu) / 32767.5f - 1.0f;
                point.jitterOffset = random * definition.jitter * slot.transform.scale *
                    std::min(1.0f, point.phase * 6.0f + (point.ageSeconds > 0.0f ? 0.35f : 0.0f));
            }
        }
    }
    m_ribbons.erase(
        std::remove_if(
            m_ribbons.begin(),
            m_ribbons.end(),
            [&](const EffectRibbon &ribbon)
            {
                return ribbon.owner == owner && !ribbon.emitting && ribbon.points.empty();
            }),
        m_ribbons.end());
}

bool EffectSystem::hasRibbons(EffectHandle owner) const
{
    return std::any_of(
        m_ribbons.begin(),
        m_ribbons.end(),
        [&](const EffectRibbon &ribbon)
        {
            return ribbon.owner == owner;
        });
}

std::optional<std::array<float, 3>> EffectSystem::linkedPosition(
    const Slot &slot,
    const EffectComponentLink &link) const
{
    if (!link.componentId || m_pModelInstances == nullptr)
    {
        return std::nullopt;
    }
    for (size_t modelIndex = 0; modelIndex < slot.definition->models.size(); ++modelIndex)
    {
        if (slot.definition->models[modelIndex].componentId != *link.componentId ||
            modelIndex >= slot.models.size())
        {
            continue;
        }
        const Engine::ModelMatrix *pMatrix =
            m_pModelInstances->nodeMatrix(slot.models[modelIndex].handle, link.nodeName);
        if (pMatrix != nullptr)
        {
            return std::array<float, 3>{(*pMatrix)[12], (*pMatrix)[13], (*pMatrix)[14]};
        }
        return std::nullopt;
    }
    return std::nullopt;
}

void EffectSystem::finishSlot(uint32_t slotIndex, Slot &slot, bool immediate)
{
    const EffectHandle owner = {slotIndex, slot.generation};
    for (size_t soundIndex = 0; soundIndex < slot.sounds.size(); ++soundIndex)
    {
        if (slot.sounds[soundIndex].started && !slot.sounds[soundIndex].stopped)
        {
            const EffectSoundDefinition &sound = slot.definition->sounds[soundIndex];
            m_soundEvents.push_back({
                .kind = EffectSoundEventKind::Stop,
                .owner = owner,
                .componentId = sound.componentId,
                .soundResource = sound.soundResource,
                .position = slot.transform.position,
            });
        }
    }
    if (immediate)
    {
        m_particles.erase(
            std::remove_if(
                m_particles.begin(),
                m_particles.end(),
                [&](const EffectParticle &particle)
                {
                    return particle.owner == owner;
                }),
            m_particles.end());
    }
    m_fixedSprites.erase(
        std::remove_if(
            m_fixedSprites.begin(),
            m_fixedSprites.end(),
            [&](const EffectFixedSprite &sprite)
            {
                return sprite.owner == owner;
            }),
        m_fixedSprites.end());
    m_ribbons.erase(
        std::remove_if(
            m_ribbons.begin(),
            m_ribbons.end(),
            [&](const EffectRibbon &ribbon)
            {
                return ribbon.owner == owner;
            }),
        m_ribbons.end());
    if (m_pModelInstances != nullptr)
    {
        for (const ModelState &model : slot.models)
        {
            m_pModelInstances->destroy(model.handle);
        }
    }
    slot.active = false;
    slot.definition.reset();
    slot.emitters.clear();
    slot.sounds.clear();
    slot.models.clear();
    slot.ribbonsStarted.clear();
    ++slot.generation;
    if (slot.generation == 0)
    {
        slot.generation = 1;
    }
    m_freeIndices.push_back(slotIndex);
    --m_activeCount;
}

std::string_view EffectSystem::internSpriteResource(const std::string &id)
{
    const auto existing = m_spriteResourceIds.find(std::string_view(id));
    if (existing != m_spriteResourceIds.end())
    {
        return *existing;
    }
    return *m_spriteResourceIds.insert(id).first;
}
}
