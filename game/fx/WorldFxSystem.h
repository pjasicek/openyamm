#pragma once

#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelInstance.h"
#include "game/fx/EffectSystem.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleSystem.h"
#include "game/fx/WaterRippleRuntime.h"
#include "game/fx/import/EffectResourceLibrary.h"
#include "game/render/lighting/RenderLight.h"

#include <array>
#include <map>
#include <tuple>
#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class GameSession;
class GameAudioSystem;
class IGameplayWorldRuntime;
class MonsterTable;
class SpriteFrameTable;
struct PartySpellCastResult;

struct WorldFxGlowBillboard
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    bool renderVisibleBillboard = true;
};

struct WorldFxLightEmitter
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    float intensity = 1.0f;
    int16_t sectorId = -1;
    RenderLightKind kind = RenderLightKind::GenericFx;
    uint32_t stableId = 0;
    bool important = false;
};

struct WorldFxContactShadow
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    uint32_t colorAbgr = 0x50000000u;
};

struct WorldFxSegmentProjectile
{
    float startX = 0.0f;
    float startY = 0.0f;
    float startZ = 0.0f;
    float endX = 0.0f;
    float endY = 0.0f;
    float endZ = 0.0f;
    float width = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
};

class WorldFxSystem
{
public:
    WorldFxSystem();

    void reset();
    bool loadNamedEffectLibrary(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &libraryPath,
        const std::string &bindingManifestPath,
        std::string &error);
    void bindNamedEffectAudio(GameAudioSystem *pAudioSystem);
    bool configureActorModels(const Engine::AssetFileSystem &assets, const std::string &manifestPath,
        const MonsterTable &monsters, const SpriteFrameTable *pSpriteFrames, std::string &error);
    void syncActorModels(const IGameplayWorldRuntime &world, float deltaSeconds = 0.0f);
    // Animation LOD: actors far from the party sample their clips at 15 Hz (beyond ~14 m) and 8 Hz (beyond ~28 m).
    // Off by default (exact clip timing, e.g. for diagnostics); the game enables it with the model LOD setting.
    void setActorAnimationLod(bool enabled) { m_actorAnimationLod = enabled; }
    // Loot satchels (the default "corpses" setting): a slain creature's body, model or sprite, sinks and dissolves once
    // it has come to rest, and a satchel sized by its loot value takes its place (none for an empty corpse). Hover,
    // picking and sprite hiding then go through the satchel, as through an actor model. Off keeps the bodies.
    bool configureCorpseSatchels(const Engine::AssetFileSystem &assets, std::string &error);
    void setCorpseSatchels(bool enabled);
    void syncCorpseSatchels(const IGameplayWorldRuntime &world, float deltaSeconds);
    // World units a sinking corpse sprite is lowered by (0 when it is not sinking).
    float actorCorpseSinkDepth(size_t actorIndex) const;
    // True when a model or a loot satchel presents this actor (its sprite is not drawn).
    bool hasActorModel(size_t actorIndex) const;
    const Engine::ModelBounds *actorModelBounds(size_t actorIndex) const;
    const Engine::ModelBounds *actorModelCullingBounds(size_t actorIndex) const;
    const Engine::ModelBounds *actorModelPoseBounds(size_t actorIndex) const;
    void setActorModelOutline(size_t actorIndex, uint32_t colorAbgr);
    void beginFrame();
    void updateParticles(float deltaSeconds, bool paused);
    void syncProjectileFx(GameSession &session, float deltaSeconds, bool refreshSpatialFx);
    void triggerPartySpellFx(const PartySpellCastResult &result);
    void setShadowsEnabled(bool enabled);
    void spawnActorDebuffFx(
        uint32_t spellId,
        uint32_t seed,
        float x,
        float y,
        float z,
        float actorHeight,
        float frontDirectionX,
        float frontDirectionY);
    void spawnActorBuffFx(
        uint32_t spellId,
        uint32_t seed,
        float x,
        float y,
        float z,
        float actorHeight,
        float frontDirectionX,
        float frontDirectionY);
    bool setProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe, const std::string &effectId);
    bool clearProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe);
    bool hasProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe) const;
    const std::string *projectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe) const;

    void clearSpatialFx();
    void addContactShadow(float x, float y, float z, float radius, uint32_t colorAbgr = 0x50000000u);
    void addSegmentProjectile(
        float startX,
        float startY,
        float startZ,
        float endX,
        float endY,
        float endZ,
        float width,
        uint32_t colorAbgr);
    void addGlowBillboard(
        float x,
        float y,
        float z,
        float radius,
        uint32_t colorAbgr,
        bool renderVisibleBillboard = true);
    void addLightEmitter(
        float x,
        float y,
        float z,
        float radius,
        uint32_t colorAbgr,
        int16_t sectorId = -1,
        RenderLightKind kind = RenderLightKind::GenericFx,
        uint32_t stableId = 0,
        bool important = false);

    WaterRippleRuntime &waterRipples() { return m_waterRipples; }
    const WaterRippleRuntime &waterRipples() const { return m_waterRipples; }
    ParticleSystem &particles();
    const ParticleSystem &particles() const;
    EffectLibrary &namedEffectLibrary();
    const EffectLibrary &namedEffectLibrary() const;
    EffectSystem &namedEffects();
    const EffectSystem &namedEffects() const;
    const EffectResourceLibrary &namedEffectResources() const;
    Engine::ModelAssetCache &modelAssets();
    Engine::ModelInstanceSystem &models();
    const Engine::ModelInstanceSystem &models() const;
    const std::vector<WorldFxGlowBillboard> &glowBillboards() const;
    const std::vector<WorldFxLightEmitter> &lightEmitters() const
    {
        return m_lightEmitters;
    }
    const std::vector<WorldFxContactShadow> &contactShadows() const;
    const std::vector<WorldFxSegmentProjectile> &segmentProjectiles() const;

private:
    struct ActorModelBinding
    {
        std::shared_ptr<const Engine::ModelAsset> asset;
        uint32_t materialVariant = 0;
        uint32_t eyeColorAbgr = 0;
        // Cast charge colour instead of the spell's element colour (0 = the element's).
        uint32_t castColorAbgr = 0;
        // Rigid models carried on nodes (actors.yml `attachments`): a staff split out of the body, a boss's weapon.
        std::vector<Engine::ModelAttachment> attachments;
        std::array<uint32_t, 8> clips = {};
        float scale = 1.0f;
        float fxReferenceScale = 1.0f;
        float yawOffset = 0.0f;
        float zOffset = 0.0f;
        bool disintegrates = false;
        // Fireball burst at the body centre when dying starts (models whose native death is an explosion).
        bool explodes = false;
        float height = 0.0f;
        uint32_t castClip = UINT32_MAX;
        // Size of the palm cast charge glow, its sparks and light relative to the default charge.
        float castGlowScale = 1.0f;
        // Optional second charge glow at a held focus (e.g. a staff head), with its own size.
        uint32_t castFocusSocket = UINT32_MAX;
        float castFocusGlowScale = 1.0f;
        uint32_t runClip = UINT32_MAX;
        float strideLength = 0.0f;
        std::shared_ptr<const std::vector<float>> upperBodyMask;
        // Authored non-deforming socket nodes: eyes, palms. Missing sockets simply have no attached FX.
        std::array<uint32_t, 4> sockets = {UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX};
        // Resolved once from Attack1/Attack2 missile tokens; physical missiles have no hand recipe.
        std::array<std::string, 2> rangedHandEffects;
        std::array<uint32_t, 2> rangedHandSockets = {UINT32_MAX, UINT32_MAX};
    };
    // Static copy of a model frozen in its Dead clip at timeSeconds, baked on the first corpse that holds that pose.
    std::shared_ptr<const Engine::ModelAsset> corpseAsset(const std::shared_ptr<const Engine::ModelAsset> &asset,
        uint32_t deadClip, float timeSeconds);
    struct ActorModelInstance
    {
        Engine::ModelInstanceHandle handle;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        bool dying = false;
        float deathClipTime = -1.0f;
        // Drawn through its binding's baked corpse (static stand-in) once the Dead clip has reached its end.
        bool corpseStandIn = false;
        bool initialized = false;
        float yaw = 0.0f;
        float previousX = 0.0f;
        float previousY = 0.0f;
        float gaitPhase = 0.0f;
        bool backwards = false;
        float previousTime = 0.0f;
        uint8_t previousState = 0;
        bool casting = false;
        bool rangedHandActive = false;
        bool secondaryAttack = false;
        std::array<EffectHandle, 2> rangedHandEffects;
        float fxScale = 1.0f;
        float castDuration = 0.0f;
        float castProgress = 0.0f;
        uint32_t castColor = 0;
        float fxCooldown = 0.0f;
        bool pendingRelease = false;
        bool previousImpact = false;
        bool hasCastOrigin = false;
        float castOriginAge = 0.0f;
        // Palm midpoint and/or focus socket; castOriginScales are the bindings' glow scales.
        std::array<std::array<float, 3>, 2> castOrigins = {};
        std::array<float, 2> castOriginScales = {};
        size_t castOriginCount = 0;
        const ActorModelBinding *pBinding = nullptr;
    };
    bool m_actorModelsConfigured = false;
    bool m_actorAnimationLod = false;
    std::unordered_map<std::string, ActorModelBinding> m_actorModelBindings;
    // Baked corpse poses by (source asset, Dead clip, held time in ms).
    std::map<std::tuple<const Engine::ModelAsset *, uint32_t, uint32_t>, std::shared_ptr<const Engine::ModelAsset>>
        m_corpseAssets;
    std::unordered_map<size_t, ActorModelInstance> m_actorModels;
    struct CorpseSatchel
    {
        uint32_t actorId = 0;
        // Seconds since the body came to rest (-1 while it is still dying).
        float restSeconds = -1.0f;
        // World units the body sinks: its height at rest.
        float sinkDepth = 0.0f;
        // The body is gone; the satchel, if any, presents the actor.
        bool gone = false;
        Engine::ModelInstanceHandle handle;
        uint32_t tier = 0;
        float yaw = 0.0f;
    };
    // The satchel presenting an actor whose body is gone, or null.
    const CorpseSatchel *goneCorpse(size_t actorIndex) const;
    bool m_corpseSatchels = false;
    std::array<std::shared_ptr<const Engine::ModelAsset>, 6> m_satchelAssets;
    std::unordered_map<size_t, CorpseSatchel> m_corpseSatchelStates;
    void syncActorModelFx(const IGameplayWorldRuntime &world, float deltaSeconds, bool refreshSpatialFx);
    void stopActorHandFx(ActorModelInstance &model, EffectStopMode mode);
    struct ProjectileFxTrailState
    {
        bool hasPreviousPosition = false;
        float previousX = 0.0f;
        float previousY = 0.0f;
        float previousZ = 0.0f;
        float cooldownSeconds = 0.0f;
    };

    struct PersistentImpactLight
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float radius = 0.0f;
        float elapsedSeconds = 0.0f;
        float durationSeconds = 0.0f;
        uint32_t colorAbgr = 0xffffffffu;
        int16_t sectorId = -1;
    };

    struct AttachedImpactEffect
    {
        EffectHandle handle;
        size_t actorIndex = static_cast<size_t>(-1);
        std::array<float, 3> position = {};
    };

    struct NamedSoundKey
    {
        EffectHandle owner;
        uint32_t componentId = 0;

        bool operator==(const NamedSoundKey &) const = default;
    };

    struct NamedSoundKeyHash
    {
        size_t operator()(const NamedSoundKey &key) const;
    };

    void updateProjectileTrailCooldowns(float deltaSeconds);
    void updatePersistentImpactLights(float deltaSeconds);
    void emitPersistentImpactLights(bool refreshSpatialFx);
    void syncProjectileTrails(GameSession &session, bool refreshSpatialFx);
    void syncProjectileImpacts(GameSession &session);
    void updateAttachedImpactEffects(GameSession &session);
    void cleanupSeenProjectileImpactIds(GameSession &session);
    void processNamedEffectAudio();

    float m_particleUpdateAccumulatorSeconds = 0.0f;
    ParticleSystem m_particleSystem;
    WaterRippleRuntime m_waterRipples;
    EffectLibrary m_namedEffectLibrary;
    EffectSystem m_namedEffects{&m_namedEffectLibrary};
    EffectResourceLibrary m_namedEffectResources;
    Engine::ModelAssetCache m_modelAssets;
    Engine::ModelInstanceSystem m_models;
    GameAudioSystem *m_pNamedEffectAudioSystem = nullptr;
    std::unordered_map<NamedSoundKey, uint64_t, NamedSoundKeyHash> m_namedSoundInstances;
    std::vector<WorldFxGlowBillboard> m_glowBillboards;
    std::vector<WorldFxLightEmitter> m_lightEmitters;
    std::vector<WorldFxContactShadow> m_contactShadows;
    std::vector<WorldFxSegmentProjectile> m_segmentProjectiles;
    std::unordered_map<uint32_t, ProjectileFxTrailState> m_projectileTrailStates;
    std::unordered_map<uint32_t, PersistentImpactLight> m_persistentImpactLights;
    std::unordered_set<uint32_t> m_seenImpactIds;
    std::unordered_map<FxRecipes::ProjectileRecipe, std::string> m_projectileImpactEffectRebinds;
    std::vector<AttachedImpactEffect> m_attachedImpactEffects;
    bool m_shadowsEnabled = false;
};
}
