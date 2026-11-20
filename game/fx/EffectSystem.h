#pragma once

#include "engine/models/ModelInstance.h"
#include "game/fx/EffectDefinition.h"

#include <array>
#include <cstdint>
#include <functional>
#include <limits>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_set>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct EffectHandle
{
    uint32_t index = std::numeric_limits<uint32_t>::max();
    uint32_t generation = 0;

    bool operator==(const EffectHandle &) const = default;
};

struct EffectSpawnParams
{
    std::array<float, 3> position = {};
    std::array<float, 4> rotation = {0.0f, 0.0f, 0.0f, 1.0f};
    float scale = 1.0f;
    uint32_t seed = 9;
    // Non-empty: only this body anchor's emitters (and the unanchored ones) emit, as MM9 puts each of an effect's
    // anchored emitters on its own body node (EffectSpriteEmitterDefinition::bodyAnchor).
    std::string bodyAnchor;
};

enum class EffectStopMode
{
    Immediate,
    Drain
};

struct EffectParticle
{
    EffectHandle owner;
    uint32_t componentId = 0;
    // Interned by the effect system; valid for as long as the system lives.
    std::string_view spriteResource;
    std::array<float, 3> position = {};
    std::array<float, 3> velocity = {};
    std::array<float, 3> localPosition = {};
    std::array<float, 3> localVelocity = {};
    std::array<float, 4> color = {1.0f, 1.0f, 1.0f, 1.0f};
    float scale = 1.0f;
    float stretchU = 1.0f;
    float stretchV = 1.0f;
    // Roll about the view axis in radians and its rate (camera-facing and world-plane sprites).
    float roll = 0.0f;
    float rollSpeed = 0.0f;
    float ageSeconds = 0.0f;
    float spriteAnimationSeconds = 0.0f;
    float lifetimeSeconds = 1.0f;
    EffectBlendMode blendMode = EffectBlendMode::Alpha;
    bool additiveTextureAlpha = true;
    EffectParticleSpace particleSpace = EffectParticleSpace::World;
    EffectSpriteAlignment alignment = EffectSpriteAlignment::CameraFacing;
    std::array<float, 3> planeRight = {1.0f, 0.0f, 0.0f};
    std::array<float, 3> planeUp = {0.0f, 0.0f, 1.0f};
};

struct EffectFixedSprite
{
    EffectHandle owner;
    uint32_t componentId = 0;
    // Interned by the effect system; valid for as long as the system lives.
    std::string_view spriteResource;
    std::array<float, 3> position = {};
    std::array<float, 4> color = {1.0f, 1.0f, 1.0f, 1.0f};
    float scale = 1.0f;
    float stretchU = 1.0f;
    float stretchV = 1.0f;
    float spriteAnimationSeconds = 0.0f;
    EffectBlendMode blendMode = EffectBlendMode::Additive;
    bool additiveTextureAlpha = true;
    EffectSpriteAlignment alignment = EffectSpriteAlignment::CameraFacing;
    std::array<float, 3> planeRight = {1.0f, 0.0f, 0.0f};
    std::array<float, 3> planeUp = {0.0f, 0.0f, 1.0f};
};

struct EffectRibbonPoint
{
    std::array<float, 3> position = {};
    float ageSeconds = 0.0f;
    // Path length from the ribbon's first sample: texture coordinates follow it, so the texture stays put in the world.
    float distance = 0.0f;
    // Stable per-sample number, for per-sample randomness (jitter) that survives older samples expiring.
    uint32_t serial = 0;
    // Sampled each tick from the definition: 0 at the head to 1 at expiry, full width in world units, colour and
    // opacity, and the sideways jitter displacement in world units.
    float phase = 0.0f;
    float width = 0.0f;
    std::array<float, 4> color = {1.0f, 1.0f, 1.0f, 1.0f};
    float jitterOffset = 0.0f;
};

struct EffectRibbon
{
    EffectHandle owner;
    uint32_t componentId = 0;
    std::shared_ptr<const EffectDefinition> definition;
    size_t definitionIndex = 0;
    float scale = 1.0f;
    float elapsedSeconds = 0.0f;
    bool emitting = true;
    // Oldest first. While emitting, the last point is the live head that follows the effect.
    std::vector<EffectRibbonPoint> points;
    uint32_t nextSerial = 0;

    const EffectRibbonDefinition &settings() const { return definition->ribbons[definitionIndex]; }
};

enum class EffectSoundEventKind
{
    Start,
    Stop,
    Move
};

struct EffectSoundEvent
{
    EffectSoundEventKind kind = EffectSoundEventKind::Start;
    EffectHandle owner;
    uint32_t componentId = 0;
    std::string soundResource;
    std::array<float, 3> position = {};
    bool spatial = true;
    bool loop = false;
    float volume = 1.0f;
    float pitch = 1.0f;
    float innerRadius = 100.0f;
    float outerRadius = 500.0f;
};

class EffectLibrary
{
public:
    bool add(std::shared_ptr<const EffectDefinition> definition, std::string &error);
    bool replace(
        const std::vector<std::shared_ptr<const EffectDefinition>> &definitions,
        std::string &error);
    const EffectDefinition *find(const std::string &id) const;
    std::vector<std::string> ids() const;
    void clear();
    size_t size() const;

private:
    friend class EffectSystem;
    std::unordered_map<std::string, std::shared_ptr<const EffectDefinition>> m_definitions;
};

class EffectSystem
{
public:
    explicit EffectSystem(const EffectLibrary *pLibrary = nullptr);

    void setLibrary(const EffectLibrary *pLibrary);
    void setModelRuntime(
        Engine::ModelInstanceSystem *pInstances,
        std::function<std::shared_ptr<const Engine::ModelAsset>(const std::string &)> resolver);
    EffectHandle spawn(const std::string &id, const EffectSpawnParams &params = {});
    bool setTransform(
        EffectHandle handle,
        const std::array<float, 3> &position,
        const std::array<float, 4> &rotation,
        float scale);
    bool stop(EffectHandle handle, EffectStopMode mode);
    // Where the effect's beam ribbons (EffectRibbonDefinition::beam) end; they start at its position.
    bool setBeamTarget(EffectHandle handle, const std::array<float, 3> &target);
    bool pause(EffectHandle handle, bool paused);
    bool restart(EffectHandle handle);
    bool seek(EffectHandle handle, float timeSeconds);
    bool setReferenceUpdateRate(uint32_t updatesPerSecond);
    uint32_t referenceUpdateRate() const;
    void update(float deltaSeconds, bool worldPaused = false);
    void clear();

    bool contains(EffectHandle handle) const;
    float elapsedSeconds(EffectHandle handle) const;
    size_t size() const;
    size_t estimatedTransientBytes() const;
    const std::vector<EffectParticle> &particles() const;
    const std::vector<EffectFixedSprite> &fixedSprites() const;
    const std::vector<EffectRibbon> &ribbons() const;
    // Includes delayed components, before their first particle or animation frame exists.
    std::vector<std::string> activeSpriteResources() const;
    std::vector<EffectSoundEvent> consumeSoundEvents();

private:
    struct Random
    {
        uint32_t state = 9;

        uint32_t next();
        float signedValue();
    };

    struct EmissionSample
    {
        std::array<float, 3> offset = {};
        std::array<float, 3> velocity = {};
    };

    struct EmitterState
    {
        bool started = false;
        bool finished = false;
        float lastEmissionSeconds = -1000000000.0f;
        std::array<float, 3> previousPosition = {};
        // Path length travelled since the last distance emission.
        float distanceSinceEmission = 0.0f;
        std::array<float, 3> rotation = {};
        std::vector<EmissionSample> cachedSamples;
    };

    struct SoundState
    {
        bool started = false;
        bool stopped = false;
    };

    struct ModelState
    {
        Engine::ModelInstanceHandle handle;
    };

    struct Slot
    {
        uint32_t generation = 1;
        bool active = false;
        bool paused = false;
        bool draining = false;
        float elapsedSeconds = 0.0f;
        EffectSpawnParams transform;
        // Unit direction of the effect's last movement (setTransform); velocity-aligned fixed sprites follow it.
        std::array<float, 3> travelDirection = {1.0f, 0.0f, 0.0f};
        std::vector<bool> ribbonsStarted;
        std::array<float, 3> beamTarget = {};
        bool hasBeamTarget = false;
        std::shared_ptr<const EffectDefinition> definition;
        Random random;
        std::vector<EmitterState> emitters;
        std::vector<SoundState> sounds;
        std::vector<ModelState> models;
    };

    Slot *find(EffectHandle handle);
    const Slot *find(EffectHandle handle) const;
    void tick(float stepSeconds);
    void tickInstance(uint32_t slotIndex, Slot &slot, float stepSeconds);
    void startEmitter(Slot &slot, size_t emitterIndex);
    // Fresh emitter states; those of another body anchor than the spawn's are finished before they start.
    static void resetEmitters(Slot &slot);
    EmissionSample createEmissionSample(Slot &slot, const EffectSpriteEmitterDefinition &definition);
    std::array<float, 3> emitterCenter(const Slot &slot, const EffectSpriteEmitterDefinition &definition) const;
    EmissionSample nextEmissionSample(Slot &slot, const EffectSpriteEmitterDefinition &definition, EmitterState &state);
    void spawnParticle(
        uint32_t slotIndex,
        Slot &slot,
        const EffectSpriteEmitterDefinition &definition,
        const EmissionSample &sample,
        const std::array<float, 3> &center,
        float ageSeconds);
    void emitParticles(uint32_t slotIndex, Slot &slot, size_t emitterIndex);
    void emitParticlesAlongPath(uint32_t slotIndex, Slot &slot, size_t emitterIndex, float stepSeconds);
    void updateParticles(float stepSeconds, const EffectHandle *pOwnerFilter = nullptr);
    void updateSounds(uint32_t slotIndex, Slot &slot);
    bool createModels(Slot &slot);
    void updateModels(Slot &slot);
    void updateFixedSprites(uint32_t slotIndex, Slot &slot);
    void updateRibbons(uint32_t slotIndex, Slot &slot, float stepSeconds);
    void updateBeam(EffectRibbon &ribbon, const Slot &slot, const std::array<float, 3> &start) const;
    bool hasRibbons(EffectHandle owner) const;
    std::optional<std::array<float, 3>> linkedPosition(
        const Slot &slot,
        const EffectComponentLink &link) const;
    void finishSlot(uint32_t slotIndex, Slot &slot, bool immediate);
    // The one stored copy of a sprite resource id, which particles and fixed sprites refer to without copying.
    std::string_view internSpriteResource(const std::string &id);

    struct StringHash
    {
        using is_transparent = void;
        size_t operator()(std::string_view value) const
        {
            return std::hash<std::string_view>{}(value);
        }
    };

    const EffectLibrary *m_pLibrary = nullptr;
    std::unordered_set<std::string, StringHash, std::equal_to<>> m_spriteResourceIds;
    uint32_t m_referenceUpdatesPerSecond = 60;
    float m_updateAccumulatorSeconds = 0.0f;
    std::vector<Slot> m_slots;
    std::vector<uint32_t> m_freeIndices;
    size_t m_activeCount = 0;
    std::vector<EffectParticle> m_particles;
    std::vector<EffectFixedSprite> m_fixedSprites;
    std::vector<EffectRibbon> m_ribbons;
    std::vector<EffectSoundEvent> m_soundEvents;
    Engine::ModelInstanceSystem *m_pModelInstances = nullptr;
    std::function<std::shared_ptr<const Engine::ModelAsset>(const std::string &)> m_modelResolver;
};
}
