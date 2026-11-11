#pragma once

#include "game/fx/ActorClipEffects.h"
#include "game/fx/ActorClipSounds.h"
#include "game/fx/ActorPortraitKind.h"
#include "game/fx/TalkPortraitFrame.h"
#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelInstance.h"
#include "game/fx/EffectSystem.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleSystem.h"
#include "game/fx/ProjectileEffectBindings.h"
#include "game/items/WorldItemShape.h"
#include "game/fx/ProjectileModelBindings.h"
#include "game/fx/SpellAuraEffectBindings.h"
#include "game/fx/WaterRippleRuntime.h"
#include "game/fx/import/EffectResourceLibrary.h"
#include "game/gameplay/ActorModelPresentation.h"
#include "game/render/ShieldDomeRenderer.h"
#include "game/render/lighting/RenderLight.h"

#include <array>
#include <functional>
#include <optional>
#include <map>
#include <memory>
#include <span>
#include <string>
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
class ActorAiTrace;
struct GameplayRuntimeActorState;
struct GameplayWorldItemPresentationState;
enum class ActorAiAnimationState : uint8_t;
class ActorModelManifest;
class MonsterTable;
class MonsterProjectileTable;
class ObjectTable;
class ItemTable;
struct GameplayProjectilePresentationState;
struct GameplayProjectileImpactPresentationState;
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
    // Also makes the system the audio's clip sound owner (GameAudioSystem::setActorClipSoundOwner).
    void bindNamedEffectAudio(GameAudioSystem *pAudioSystem);
    // True while the actor is drawn by a model whose clips carry its sounds (actor_sounds.yml): its descriptor sounds
    // are then not played.
    bool actorPlaysClipSounds(size_t actorIndex) const;
    // Camera shakes the actors' clip events raised since the last call (intensity at the party, seconds), for the
    // session's CameraShake.
    std::vector<std::pair<float, float>> takeActorCameraShakes();
    // Actor models of the merged world manifests (ActorModelManifest). The monsters a map shows when it loads
    // (eagerDescriptors) get their models now; any other bound monster when it first appears (a summon, an arena
    // opponent). Called every frame: later calls only update the tables later bindings read.
    bool configureActorModels(const Engine::AssetFileSystem &assets,
        std::shared_ptr<const ActorModelManifest> pManifest, const MonsterTable &monsters,
        const SpriteFrameTable *pSpriteFrames, std::span<const std::string> eagerDescriptors, std::string &error);
    bool actorModelsConfigured() const
    {
        return m_actorModelsConfigured;
    }
    // Diagnostics: the bindings of one manifest, all built at once.
    bool configureActorModels(const Engine::AssetFileSystem &assets, const std::string &manifestPath,
        const MonsterTable &monsters, const SpriteFrameTable *pSpriteFrames, std::string &error);
    // While a dialogue pauses the world, its partner's model keeps running on the frame clock (liveDeltaSeconds), so
    // it turns to face the party and finishes its pose blend; every other model holds still.
    void syncActorModels(const IGameplayWorldRuntime &world, float deltaSeconds = 0.0f,
        std::optional<size_t> liveActorIndex = std::nullopt, float liveDeltaSeconds = 0.0f);
    // Animation tracing (an AI arena's `trace_animation`): syncActorModels reports each traced actor's clips, rate and
    // crossfades to the trace. Null (the default) reports nothing.
    void setAnimationTrace(ActorAiTrace *pTrace)
    {
        m_pAnimationTrace = pTrace;
    }
    // Shield domes of active actor behaviour wards (ActorBehaviorRuntime::wardDisplays): they grow in when raised,
    // swell and fade when they lapse, and ripple where projectiles hit them.
    void syncShieldDomes(const IGameplayWorldRuntime &world, float deltaSeconds);
    // Scripted beams (EventRuntimeState::beamRequests, beamStops): starts and ends them, keeps a party beam on the
    // party and ends each after its seconds.
    void syncBeams(IGameplayWorldRuntime &world, float deltaSeconds);
    // Scripted effects carried on actors (EventRuntimeState::actorEffectRequests, evt.SpawnActorEffect and
    // evt.StopActorEffect): starts and stops them and ends each after its seconds; syncProjectileFx keeps them on their
    // sockets.
    void syncScriptedActorEffects(IGameplayWorldRuntime &world, float deltaSeconds);
    size_t activeScriptedActorEffectCount() const
    {
        return m_scriptedActorEffects.size();
    }
    size_t activeBeamCount() const
    {
        return m_beams.size();
    }
    const std::vector<ShieldDomeDraw> &shieldDomes() const { return m_shieldDomes; }
    float shieldDomeTimeSeconds() const { return m_shieldDomeTimeSeconds; }
    // Animation LOD: actors far from the party sample their clips at 15 Hz (beyond ~14 m) and 8 Hz (beyond ~28 m).
    // Off by default (exact clip timing, e.g. for diagnostics); the game enables it with the model LOD setting.
    void setActorAnimationLod(bool enabled) { m_actorAnimationLod = enabled; }
    // Loot satchels: a slain creature's body, model or sprite, sinks and dissolves once it has come to rest, and a
    // satchel sized by its loot value takes its place (none for an empty corpse). Hover, picking and sprite hiding
    // then go through the satchel, as through an actor model.
    bool configureCorpseSatchels(const Engine::AssetFileSystem &assets, std::string &error);
    void syncCorpseSatchels(const IGameplayWorldRuntime &world, float deltaSeconds);
    // World units a sinking corpse sprite is lowered by (0 when it is not sinking).
    float actorCorpseSinkDepth(size_t actorIndex) const;
    // True when a model or a loot satchel presents this actor (its sprite is not drawn).
    bool hasActorModel(size_t actorIndex) const;
    const Engine::ModelBounds *actorModelBounds(size_t actorIndex) const;
    // Distance along direction to where the ray meets the posed model (or loot satchel) presenting the actor: its
    // triangles, not its bounds. Pickers test actorModelCullingBounds and actorModelPoseBounds first.
    std::optional<float> actorModelPickRay(size_t actorIndex, const std::array<float, 3> &origin,
        const std::array<float, 3> &direction) const;
    // World height of an actor model's standing pose above the actor's feet, at the actor's scale: where health bars
    // and quest markers sit. Empty without a model (also for a loot satchel).
    std::optional<float> actorModelStandingTop(size_t actorIndex) const;
    // World point a model actor launches its missile (spell = false) or spell (spell = true) from: the action's
    // actors.yml release point (ActionEvent). Empty without a model, without a release point for that action, or when
    // it lies away from the actor's body (x, y, z feet, collision radius and height: a stale or broken pose); the
    // caller then keeps the body origin.
    std::optional<std::array<float, 3>> actorLaunchPoint(size_t actorIndex, bool spell, float x, float y, float z,
        float radius, float height) const;
    // Name and time of the clip an actor's model last sampled, and of its upper-body layer (empty name without one).
    bool actorModelClipSample(size_t actorIndex, std::string &clip, float &time, std::string &layerClip,
        float &layerTime) const;
    const Engine::ModelBounds *actorModelCullingBounds(size_t actorIndex) const;
    const Engine::ModelBounds *actorModelPoseBounds(size_t actorIndex) const;
    void setActorModelOutline(size_t actorIndex, uint32_t colorAbgr);
    // Shows only the actor models and loot satchels whose actor passes visible (indoors: the actor's sector is
    // revealed through the portals, as for actor sprites). Hidden models are neither posed nor drawn.
    void setActorModelVisibility(const std::function<bool(size_t actorIndex)> &visible);
    // Actor inspect portrait (ActorModelPreview): a copy of the actor's model, hidden from the world passes and drawn
    // only into the inspect popup, facing +X at the origin. Like the sprite preview it demonstrates the creature on the
    // popup's own clock: fidget first, then standing, then a fidget or an attack (the monster's inspect attack
    // chance). Null when the actor has no model. A portrait not requested since the previous syncActorModels is
    // released there. The Talk kind is a second, independent portrait of a speaking actor: its head and shoulders
    // (the skin joints named for the head; the whole body for a model without one), standing and fidgeting only.
    struct InspectPortrait
    {
        Engine::ModelInstanceHandle handle;
        // Framing, in the portrait's space: corners of every demonstrated pose's bounds and of its carried items (not
        // swung in the attack). The first restPointCount belong to the standing and fidget poses, the rest to the
        // attack.
        std::vector<std::array<float, 3>> framePoints;
        size_t restPointCount = 0;
        std::optional<EffectSystem> effects;
    };
    const InspectPortrait *syncInspectPortrait(const IGameplayWorldRuntime &world, size_t actorIndex,
        uint32_t animationTicks, ActorPortraitKind kind = ActorPortraitKind::Inspect);
    // The talk portrait of a posed talking prop (an MM9 RUDEProp decoration, keyed by its sprite override key): a copy
    // of its decoration model, framed on its head and shoulders (talkPortraitStaticFigureFrame); it holds its pose.
    // Shares the Talk portrait's slot with speaking actors. Null without a model.
    const InspectPortrait *syncDecorationTalkPortrait(uint32_t decorationKey, const DecorationPortraitModel &model);
    void beginFrame();
    void updateParticles(float deltaSeconds, bool paused);
    void syncProjectileFx(GameSession &session, float deltaSeconds, bool refreshSpatialFx);
    void triggerPartySpellFx(const PartySpellCastResult &result);
    void setShadowsEnabled(bool enabled);
    // A debuff's onset on a creature: the enhanced style plays its bound aura effect (engine/effects/spell_auras.yml),
    // following the creature when its index is given; otherwise the procedural aura particles.
    void spawnActorDebuffFx(
        uint32_t spellId,
        uint32_t seed,
        float x,
        float y,
        float z,
        float actorHeight,
        float frontDirectionX,
        float frontDirectionY,
        size_t actorIndex = static_cast<size_t>(-1));
    // A debuff the party casts on an actor. When the enhanced style binds a flight to the spell's recipe (Shrinking
    // Ray), a visual-only bolt flies from the party to the actor first, and the debuff particles and the bound impact
    // play when it arrives; otherwise the debuff particles appear at once.
    void spawnPartyActorDebuffFx(
        uint32_t spellId,
        uint32_t seed,
        size_t actorIndex,
        float x,
        float y,
        float z,
        float actorHeight,
        float partyX,
        float partyY);
    // Plays the impact effect the enhanced style binds to the spell's recipe at a point (Armageddon's strikes).
    // Returns false when nothing is bound (the classic style).
    bool spawnSpellImpactEffect(uint32_t spellId, float x, float y, float z, uint32_t seed);
    // A creature's buff or heal on itself, as spawnActorDebuffFx.
    void spawnActorBuffFx(
        uint32_t spellId,
        uint32_t seed,
        float x,
        float y,
        float z,
        float actorHeight,
        float frontDirectionX,
        float frontDirectionY,
        size_t actorIndex = static_cast<size_t>(-1));
    // Projectile visuals: engine/effects/projectiles.yml binds recipes (and monsters' variants of them) to named
    // flight, settled and impact effects that replace the recipe's trail particles, beam and impact burst, and may
    // override the native sprite and the flight light.
    // The binding for a projectile of this recipe thrown by this monster (0: none) as this object (its object_list
    // name; a world's own missile is bound by it); null when nothing is bound.
    const ProjectileEffectBinding *projectileEffectBinding(FxRecipes::ProjectileRecipe recipe, int16_t monsterId,
        const std::string &objectName = std::string()) const;
    // Projectile models (engine/models/projectiles.yml): a bound projectile draws its model, pointed along its
    // flight, instead of its native sprite, in both projectile styles. Loads the bindings and their models.
    bool loadProjectileModels(const Engine::AssetFileSystem &assets, std::string &error);
    // The object table projectile models and the water splash are resolved through (each projectile sync sets the
    // session's; diagnostics without a session set it here).
    void setProjectileObjectTable(const ObjectTable *pObjectTable)
    {
        m_pProjectileObjectTable = pObjectTable;
    }
    // Whether a projectile model presents this object (object_list.txt ObjectId): its sprite is never drawn in flight.
    bool hasProjectileModel(int16_t objectId) const
    {
        return m_projectileModelBindings.contains(objectId);
    }
    // Shows only the projectile and item models whose sector passes visible (indoors: revealed through the portals).
    void setObjectModelVisibility(const std::function<bool(int16_t sectorId)> &visible);
    // Item models (engine/world_items/items.yml, GROUND_ITEMS_3D_BEHAVIOUR.md): every item lying on the ground draws
    // its model, with a yaw of its own; there are no ground-item sprites. Loads the missing-model placeholder, which
    // an item without a working model draws; each item model loads the first time one of its items appears.
    bool loadItemModels(const Engine::AssetFileSystem &assets, std::string &error);
    // Hover or context-action outline of an item's model (the world's presentation key), 0 for none.
    void setItemModelOutline(uint32_t key, uint32_t colorAbgr);
    // The drawn ground under one point of a resting item's footprint (outdoors: the smoothed terrain, which departs
    // from the native floor the item rests on), near the item's height z; nothing where nothing supports that point.
    using ItemGroundSampler = std::function<std::optional<float>(float x, float y, float z)>;
    void setItemGroundSampler(ItemGroundSampler sampler)
    {
        m_itemGroundSampler = std::move(sampler);
    }
    // Whether a projectile's native sprite draws: not when a model presents it; else its gameplay visual mode unless
    // its binding overrides it.
    bool projectileShowsNativeSprite(const GameplayProjectilePresentationState &projectile) const;
    // Whether a named effect (a debug rebind or a bound impact) replaces an impact's native sprite and recipe burst.
    bool projectileImpactUsesNamedEffect(const GameplayProjectileImpactPresentationState &impact) const;
    // Whether an impact's native sprite draws: not when a named effect (the water splash's too) or the recipe's
    // dedicated burst replaces it.
    bool projectileImpactShowsNativeSprite(const GameplayProjectileImpactPresentationState &impact) const;
    // The sprite resources of every bound projectile effect (none in the classic style), for preloading.
    std::vector<std::string> projectileEffectSpriteResources() const;
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
    // Points of a model's skinned surface (LOD 0 vertices) in burn order, where the flames of a burn rise.
    struct ActorBurnSurface
    {
        struct Point
        {
            float order = 0.0f;
            uint32_t nodeIndex = 0;
            uint32_t primitiveIndex = 0;
            uint32_t vertexIndex = 0;
        };
        // Ascending order.
        std::vector<Point> points;
    };
    // actors.yml `death_effect: {type: burn, ...}`: as dying starts, the body chars and burns away along its burn maps
    // (Engine::ModelBurn), with flames rising from the burning band and a fire light. The death clip plays to its end
    // (a longer clip continues after the AI's native death length); the burnt-out corpse draws nothing.
    struct ActorBurnDeath
    {
        // Seconds after dying starts at which the first texels begin to char and the last have burnt away (the fire
        // over them lingers for its width after that).
        float startSeconds = 0.0f;
        float endSeconds = 1.0f;
        Engine::ModelBurn style;
        float flamesPerSecond = 0.0f;
        // Flame width in world units at the binding's reference scale.
        float flameSize = 0.0f;
        uint32_t lightColorAbgr = 0;
        float lightRadius = 0.0f;
        // Flame particle RGB (flame_color); the particles' default orange without one.
        std::optional<std::array<uint8_t, 3>> flameTint;
        std::shared_ptr<const ActorBurnSurface> surface;
    };
    // The burn surface of a model in one material variant: every skinned material needs an uncooked burn map.
    static std::shared_ptr<const ActorBurnSurface> buildActorBurnSurface(const Engine::ModelAsset &asset,
        uint32_t variant, std::string &error);
    struct ActorModelBinding
    {
        std::shared_ptr<const Engine::ModelAsset> asset;
        uint32_t materialVariant = 0;
        uint32_t eyeColorAbgr = 0;
        // A persistent particle effect at the model origin; radius includes the particles for portrait framing.
        std::string ambientEffect;
        float ambientRadius = 0.0f;
        // Rigid models carried on nodes (actors.yml `attachments`): a staff split out of the body, a boss's weapon.
        std::vector<Engine::ModelAttachment> attachments;
        std::array<uint32_t, 8> clips = {};
        float scale = 1.0f;
        float fxReferenceScale = 1.0f;
        float yawOffset = 0.0f;
        // actors.yml `fixed_yaw_degrees`: the model keeps this world facing (0 = +x) instead of turning with the actor,
        // for bodies built into the scenery (the Demon Queen's rock alcove). A `look` block can still turn the upper body.
        std::optional<float> fixedYaw;
        float zOffset = 0.0f;
        bool disintegrates = false;
        // Fireball burst at the body centre when dying starts (models whose native death is an explosion).
        bool explodes = false;
        std::optional<ActorBurnDeath> burn;
        float height = 0.0f;
        // Top of the standing clip's first pose above the feet, in model units.
        float standingHeight = 0.0f;
        uint32_t castClip = UINT32_MAX;
        uint32_t runClip = UINT32_MAX;
        // actors.yml `animation.sprint`: optional longer-strided clip for speeds the run would only play too fast.
        uint32_t sprintClip = UINT32_MAX;
        // actors.yml `animation.look`: nodes, root to tip (neck, head), that share a turn toward the party's eyes over
        // the clip, and the turn's limits in radians. Empty when the model does not look.
        std::vector<uint32_t> lookNodes;
        float lookMaxYaw = 0.0f;
        float lookMaxPitch = 0.0f;
        // `min_pitch_degrees` (default -max_pitch_degrees): how far the look may turn down.
        float lookMinPitch = 0.0f;
        float lookHeadHeight = 0.0f;
        // `target: combat`: the look follows the actor's combat target (GameplayRuntimeActorState::aimTarget, set for
        // actors with tactics) at any distance instead of the party, and rests without one. `hold_clip`: while it has
        // that target and stands, this clip's first frame replaces the standing clip (a turret stops its idle scan).
        bool lookAtCombatTarget = false;
        uint32_t lookHoldClip = UINT32_MAX;
        // actors.yml `animation.sockets`: a named point on the skeleton, a node (a GLB socket node or a bone) and an
        // offset in that node's space, in model units.
        struct Socket
        {
            uint32_t node = UINT32_MAX;
            std::array<float, 3> offset = {};
        };
        // actors.yml `animation.events`, per action role (melee attack, ranged attack, cast): the clip time at which
        // the game applies the action (the melee hit lands, the missile or spell is released). A marked clip's wind-up
        // [0, impact] spans the native action, so the marker frame plays when the game acts; the rest follows the
        // action as follow-through. Unmarked clips run on the action clock as before.
        // Ranged roles may also name sockets: `glow`, where the projectile's element charges while the action winds
        // up (both palms, a staff head, an eye), and `release`, where it leaves; without `release` it leaves the one
        // glow socket, or the middle of several.
        // Every role may carry named effects on sockets over a span of its clip (`effect`/`effects`, ActorClipEffect),
        // with or instead of the glow.
        struct SocketEffect
        {
            ActorClipEffect effect;
            std::array<Socket, ActorClipEffectMaxSockets> sockets;
        };
        struct ActionEvent
        {
            float impactSeconds = -1.0f;
            std::array<Socket, 4> glow;
            size_t glowCount = 0;
            std::optional<Socket> release;
            // Size of the charge glows, their sparks and light relative to the default charge.
            float glowScale = 1.0f;
            // Charge colour instead of the projectile's (0 = the projectile's). A melee glow has no projectile and
            // requires one.
            uint32_t colorAbgr = 0;
            // Ranged attack only (`effects`, element -> named effect): drawn at the glow sockets instead of the glow
            // while the Attack1/Attack2 missile of that element winds up; empty for the plain glow.
            std::array<std::string, 2> effects;
            std::vector<SocketEffect> socketEffects;
        };
        std::array<ActionEvent, 3> actionEvents;
        // Events of other clips (a `clips` or `script_clips` role as the event's key: MM9's taunt, a resurrection
        // spell): their socket effects only.
        struct ClipEvent
        {
            uint32_t clip = UINT32_MAX;
            std::vector<SocketEffect> socketEffects;
        };
        std::vector<ClipEvent> clipEvents;
        // actors.yml `animation.sockets` by name (scripted effects carried on an actor name them).
        std::unordered_map<std::string, Socket> sockets;
        // The clips of the action roles (melee attack, ranged attack, cast; UINT32_MAX for a missing cast).
        std::array<uint32_t, 3> actionClips() const;
        // The socket effects of the action role (-1 for none), else of the clip's event; null without any.
        const std::vector<SocketEffect> *socketEffects(int role, uint32_t clip) const;
        // Behaviour script clip roles (actors.yml `script_clips`): role name -> clip index.
        std::unordered_map<std::string, uint32_t> scriptClips;
        // The `backpedal` and `backpedal_run` script clips (MM9 models): walking and running backwards while the actor
        // backs away; without one the walk or run plays forwards, as MM9's. UINT32_MAX without them.
        uint32_t backpedalClip = UINT32_MAX;
        uint32_t backpedalRunClip = UINT32_MAX;
        float strideLength = 0.0f;
        // Running clip stride (actors.yml `run_stride_length`); defaults to 1.55 x the walking stride.
        float runStrideLength = 0.0f;
        // Sprint clip stride (actors.yml `sprint_stride_length`, required with `sprint`).
        float sprintStrideLength = 0.0f;
        // Authored speeds of the walking, running and sprinting clips (stride over clip length, model units per
        // second; 0 without a sprint), which with the AI's hurry choose between them (actorModelGait).
        std::array<float, 3> gaitSpeeds = {};

        // The clip and stride of a locomotion gait (UINT32_MAX and 0 for a missing sprint).
        uint32_t gaitClip(ActorModelGait gait) const;
        float gaitStride(ActorModelGait gait) const;
        // actors.yml `animation.gait_rate: [min, max]`: the locomotion clip's playback rate range relative to authored
        // (actorModelGaitDistance; default [0, ActorModelDefaultMaxGaitRate]); max 0 is uncapped.
        float minGaitRate = 0.0f;
        float maxGaitRate = 0.0f;
        // ActorModelManifest::Entry::gaitFollowsIntent: the AI's walk or run picks the clip (actorModelIntendedGait).
        bool gaitFollowsIntent = false;
        // actors.yml `animation.blend_seconds`: blend length of every clip change except into dying (negative = the
        // defaults, 0.12 s and 0.06 s into a hit), for bodies whose clips change pose a lot (the drake's forward flight
        // and upright hover). `animation.death_blend_seconds`: blend into the death clip (default none).
        float blendSeconds = -1.0f;
        float deathBlendSeconds = 0.0f;
        std::shared_ptr<const std::vector<float>> upperBodyMask;
        // The sockets named `eye_left` and `eye_right`, lit with eyeColorAbgr; missing eyes have no glow.
        std::array<std::optional<Socket>, 2> eyes;
        // The timed sounds of its clips (actor_sounds.yml); null without.
        std::shared_ptr<const ActorClipSounds> clipSounds;
    };
    // Static copy of a model frozen in its Dead clip at timeSeconds, baked on the first corpse that holds that pose.
    std::shared_ptr<const Engine::ModelAsset> corpseAsset(const std::shared_ptr<const Engine::ModelAsset> &asset,
        uint32_t deadClip, float timeSeconds);
    // The action whose charge glows at its event's sockets (ActionEvent index + 1): a melee blow (glow only, in its
    // authored colour), a ranged attack or a spell.
    enum class ActorCharge : uint8_t
    {
        None,
        Melee,
        Ranged,
        Cast
    };

    struct ActorModelInstance
    {
        Engine::ModelInstanceHandle handle;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        // The syncActorModels pass that last kept this model.
        uint32_t syncPass = 0;
        bool dying = false;
        // Locomotion clip playing (actorModelGait, kept between frames for its hysteresis).
        ActorModelGait gait = ActorModelGait::Walk;
        float deathClipTime = -1.0f;
        // Seconds since the burn death started (ActorBurnDeath), -1 when not burning; flames owed and spawned so far.
        float burnSeconds = -1.0f;
        float burnFlameBudget = 0.0f;
        uint32_t burnFlameSerial = 0;
        // Drawn through its binding's baked corpse (static stand-in) once the Dead clip has reached its end.
        bool corpseStandIn = false;
        // The held items its attachments show (syncActorHeldItems): "model\nnode" per item, in order.
        std::vector<std::string> heldItemKeys;
        // Placement last sampled: a burning model outlives its actor in it (burningRemains).
        Engine::ModelTransform transform;
        bool initialized = false;
        float yaw = 0.0f;
        // Walking, the model faces its actual movement rather than the AI's yaw (actorModelFacesMovement).
        bool facingMovement = false;
        float previousX = 0.0f;
        float previousY = 0.0f;
        float gaitPhase = 0.0f;
        // Distance the body covered that the gait has not advanced by yet (smoothActorModelGaitDistance).
        float gaitTravelLead = 0.0f;
        bool backwards = false;
        // The legs of the attack playing (advanceActorModelAttackLegs), how long the AI has stood, and whether the last
        // frame showed a gait (ActorModelStandGraceSeconds).
        ActorModelAttackLegs attackLegs;
        float standSeconds = 0.0f;
        bool presentedGait = false;
        // How long actorModelGait has chosen another gait than `gait` (holdActorModelGait), and whether the last frame
        // showed a gait at all (under an attack too).
        float gaitHeldSeconds = 0.0f;
        bool locomoted = false;
        float previousTime = 0.0f;
        uint8_t previousState = 0;
        bool casting = false;
        bool scripted = false;
        bool secondaryAttack = false;
        // The action whose charge is showing, its wind-up length (the action up to the moment the game applies or
        // releases it, captured at its start) and progress through it.
        ActorCharge chargeRole = ActorCharge::None;
        uint32_t chargeSpellId = 0;
        float chargeDuration = 0.0f;
        float chargeProgress = 0.0f;
        // Resolved from the projectile when the charge is first drawn: colour, and the named effect replacing the
        // glow (empty for the glow; none at all for a physical missile such as an arrow).
        bool chargeResolved = false;
        bool chargeGlows = false;
        uint32_t chargeColor = 0;
        std::string chargeEffect;
        std::array<EffectHandle, 4> chargeEffects;
        EffectHandle ambientEffect;
        float fxScale = 1.0f;
        // Clip sounds played so far (presentActorClipSounds) and the actor's voice line playing.
        ActorClipSoundState clipSoundState;
        uint64_t voiceSoundInstance = 0;
        // Current head look relative to the body's facing (radians), eased toward the party on its own clock.
        float lookYaw = 0.0f;
        float lookPitch = 0.0f;
        float lookClock = 0.0f;
        bool lookStarted = false;
        // A marked action (ActionEvent) in progress: its clip, marker, wind-up length (the native action up to the
        // moment the game applies it, captured at its start) and the clip time last shown; then its follow-through,
        // played after the action while the actor stands or walks.
        // A fidget clip longer than the native fidget follows the same way after the AI returns to standing, but only
        // while the actor stands (followStandingOnly).
        uint32_t markedClip = UINT32_MAX;
        float markedImpact = 0.0f;
        float markedDuration = 0.0f;
        // Action clock when the game applied the marked action; the clip runs on from its marker from then.
        float markedReleaseElapsed = -1.0f;
        float markedTime = 0.0f;
        uint32_t followClip = UINT32_MAX;
        float followTime = 0.0f;
        bool followStandingOnly = false;
        float fxCooldown = 0.0f;
        bool pendingRelease = false;
        bool previousImpact = false;
        // The charge's glow sockets as last posed, and how long ago; the release sparkles there.
        bool hasChargeOrigin = false;
        float chargeOriginAge = 0.0f;
        std::array<std::array<float, 3>, 4> chargeOrigins = {};
        size_t chargeOriginCount = 0;
        // The clip whose socket effects play (ActorModelBinding::SocketEffect): its role (-1 for a clip event), the
        // clip time last shown, which effects have started this play (bit per effect) and their handles (effect *
        // ActorClipEffectMaxSockets + socket; allocated on first use).
        const std::vector<ActorModelBinding::SocketEffect> *pSocketEffects = nullptr;
        uint32_t socketEffectClip = UINT32_MAX;
        int socketEffectRole = -1;
        float socketEffectTime = 0.0f;
        uint32_t socketEffectsStarted = 0;
        std::vector<EffectHandle> socketEffectHandles;
        const ActorModelBinding *pBinding = nullptr;
    };
    struct InspectPortraitState
    {
        InspectPortrait portrait;
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        // Set for a talking prop's portrait (syncDecorationTalkPortrait), whose model is its decoration's.
        std::optional<uint32_t> decorationKey;
        std::shared_ptr<const Engine::ModelAsset> decorationAsset;
        bool requested = false;
        bool started = false;
        bool movingAtFirstInspect = false;
        ActorAiAnimationState animation = {};
        float timeSeconds = 0.0f;
        float lengthSeconds = 0.0f;
        uint32_t lastTicks = 0;
        uint32_t randomState = 0x6d2b79f5u;
        EffectHandle ambientEffect;
    };
    std::array<std::optional<InspectPortraitState>, ActorPortraitKindCount> m_portraits;
    void releaseInspectPortrait(ActorPortraitKind kind);
    // The binding of a bound monster, built on first use; null when unbound or when its binding failed to build.
    const ActorModelBinding *actorModelBinding(const std::string &descriptor);
    bool buildActorModelBinding(const std::string &descriptor, std::string &error);
    bool m_actorModelsConfigured = false;
    bool m_actorAnimationLod = false;
    std::shared_ptr<const ActorModelManifest> m_pActorModelManifest;
    const Engine::AssetFileSystem *m_pActorModelAssets = nullptr;
    const MonsterTable *m_pActorModelMonsters = nullptr;
    const SpriteFrameTable *m_pActorModelSpriteFrames = nullptr;
    // Built bindings keep their address: actor model instances point at them.
    std::unordered_map<std::string, ActorModelBinding> m_actorModelBindings;
    std::unordered_set<std::string> m_failedActorModelBindings;
    // Bindings of one model and skin share its burn surface.
    std::map<std::pair<const Engine::ModelAsset *, uint32_t>, std::shared_ptr<const ActorBurnSurface>>
        m_actorBurnSurfaces;
    // Baked corpse poses by (source asset, Dead clip, held time in ms).
    std::map<std::tuple<const Engine::ModelAsset *, uint32_t, uint32_t>, std::shared_ptr<const Engine::ModelAsset>>
        m_corpseAssets;
    std::unordered_map<size_t, ActorModelInstance> m_actorModels;
    uint32_t m_actorModelSyncPass = 0;
    std::vector<ActorClipSoundCue> m_actorClipSoundCues;
    std::vector<std::pair<float, float>> m_actorCameraShakes;
    struct ShieldDomeState
    {
        ShieldDomeDraw draw;
        float fadeOutSeconds = 0.0f;
        bool present = false;
    };
    std::unordered_map<std::string, ShieldDomeState> m_shieldDomeStates;
    std::vector<ShieldDomeDraw> m_shieldDomes;
    float m_shieldDomeTimeSeconds = 0.0f;
    struct ActiveBeam
    {
        std::string name;
        std::string effectId;
        EffectHandle handle;
        std::array<float, 3> to = {};
        bool toParty = false;
        // Without a time it lasts until stopped.
        bool timed = false;
        float remainingSeconds = 0.0f;
    };
    std::vector<ActiveBeam> m_beams;
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
    // The model picked for an actor: its body, or once gone or burnt out, its loot satchel (the remains without one).
    std::optional<Engine::ModelInstanceHandle> actorPickingHandle(size_t actorIndex) const;
    std::array<std::shared_ptr<const Engine::ModelAsset>, 6> m_satchelAssets;
    // By actor index, ordered: the per-frame sync walks it alongside the actors.
    std::map<size_t, CorpseSatchel> m_corpseSatchelStates;
    void syncActorModelFx(const IGameplayWorldRuntime &world, float deltaSeconds, bool refreshSpatialFx);
    // The burn front of a burning model, or null when it is not burning.
    std::optional<Engine::ModelBurn> actorBurn(const ActorModelInstance &model) const;
    bool burningRemains(ActorModelInstance &model, float deltaSeconds);
    void spawnActorBurnFlames(ActorModelInstance &model, const Engine::ModelBurn &burn, float deltaSeconds);
    void stopActorChargeFx(ActorModelInstance &model, EffectStopMode mode);
    // Socket effects (ActorModelBinding::SocketEffect): the clip and time showing now pick them (a new clip or a
    // restart stops the old ones); syncActorSocketEffects starts, carries and ends them.
    void selectActorSocketEffects(ActorModelInstance &model, const ActorModelBinding &binding, int role, uint32_t clip,
        float timeSeconds, bool restart);
    void syncActorSocketEffects(ActorModelInstance &model, float deltaSeconds, bool emitting);
    void stopActorSocketEffects(ActorModelInstance &model, EffectStopMode mode);
    // Effects a script carries on an actor (evt.SpawnActorEffect): on a socket or node of its model, else at the
    // middle of its body (one per socket of a list); timed ones end after their seconds, the rest when the effect
    // ends by itself.
    struct ScriptedActorEffect
    {
        EffectHandle handle;
        size_t actorIndex = 0;
        uint32_t actorId = 0;
        std::string effectId;
        // A name in the model's animation.sockets or a node of the model, resolved each frame (the model may come
        // later); empty for the body's middle.
        std::string socket;
        float scale = 1.0f;
        bool timed = false;
        float remainingSeconds = 0.0f;
    };
    std::vector<ScriptedActorEffect> m_scriptedActorEffects;
    // Where a scripted actor effect is now; empty when its actor is gone.
    std::optional<std::array<float, 3>> scriptedActorEffectPoint(const IGameplayWorldRuntime &world,
        const ScriptedActorEffect &effect) const;
    void updateScriptedActorEffects(const IGameplayWorldRuntime &world);
    // Plays the clip sounds the actor's full-body clip and upper-body layer passed this frame.
    // Its model's attachments: the binding's, then the items the actor holds (MapDeltaActor::heldItems) unless a
    // routine put them down; rebuilt only when those change.
    void syncActorHeldItems(
        ActorModelInstance &model, const ActorModelBinding &binding, const GameplayRuntimeActorState &state);
    void presentActorClipSounds(ActorModelInstance &model, const ActorModelBinding &binding, uint32_t clip,
        float timeSeconds, const Engine::ModelAnimationLayer &layer, float deltaSeconds,
        const std::array<float, 3> &position, const std::array<float, 3> &listener);
    // World point of an actor model's socket in its current pose; empty without the node's matrix.
    std::optional<std::array<float, 3>> actorSocketPoint(const ActorModelInstance &model,
        const ActorModelBinding::Socket &socket) const;
    // Colour, glow and effect of a charge that just started (chargeResolved), from the projectile it will release.
    void resolveActorCharge(ActorModelInstance &model) const;
    // talking: the actor is the party's dialogue partner (an MM9 one looks at the party only then or when it holds it).
    void updateActorLook(ActorModelInstance &model, const GameplayRuntimeActorState &state,
        const IGameplayWorldRuntime &world, float scale, float partyDistance, float deltaSeconds, bool canLook,
        bool talking);
    // The frame syncActorModels is about to sample, for the animation trace: a crossfade starts when sampleBlended
    // will start one (restart, or a new main or layer clip).
    void traceActorAnimation(size_t actorIndex, const ActorModelInstance &model, uint32_t clip, float time,
        const Engine::ModelAnimationLayer &layer, bool restart, float transitionSeconds, float speed,
        float deltaSeconds) const;
    ActorAiTrace *m_pAnimationTrace = nullptr;
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
        // Auras are sized to their creature.
        float scale = 1.0f;
    };

    // A buff or heal aura the party cast on itself: kept just in front of and below the party's eyes while it plays.
    struct PartyAuraEffect
    {
        // Spawned on the first update, once the party's view is known.
        EffectHandle handle;
        std::string effectId;
        uint32_t seed = 0;
        bool started = false;
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
    bool syncProjectileFlightEffect(
        uint32_t projectileId,
        const ProjectileEffectBinding *pBinding,
        bool settled,
        const std::array<float, 3> &projectilePosition,
        float anchorOffsetZ,
        const std::array<float, 3> &velocity);
    void stopProjectileFlightEffects();
    void syncProjectileImpacts(GameSession &session);
    void updateAttachedImpactEffects(GameSession &session);
    void updateSpellVisualFlights(GameSession &session, float deltaSeconds);
    void stopSpellVisualFlights();
    void updatePartyAuraEffects(GameSession &session);
    bool spawnActorAuraEffect(
        SpellAuraKind kind,
        uint32_t spellId,
        uint32_t seed,
        float x,
        float y,
        float z,
        float actorHeight,
        size_t actorIndex);
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
    struct ProjectileFlightEffect
    {
        EffectHandle handle;
        // The effect plays the binding's settled effect (the projectile lies on the ground), not its flight.
        bool settled = false;
        // Height of the effect above the projectile's position, and its last orientation, to place it at the
        // projectile's end point.
        float anchorOffsetZ = 0.0f;
        std::array<float, 4> rotation = {0.0f, 0.0f, 0.0f, 1.0f};
    };

    // A visual-only flight between the party and an actor, with no gameplay projectile behind it: a debuff's bolt
    // from the party to its target, or a drain's stolen life from a victim back to the party.
    struct SpellVisualFlight
    {
        // Spawned on the first update, once the party's eyes are known.
        EffectHandle handle;
        std::string flightEffect;
        std::array<float, 3> origin = {};
        std::array<float, 3> target = {};
        // Starts in front of the party's eyes instead of at origin.
        bool fromParty = false;
        bool started = false;
        // The actor flown to, followed while it lives; static_cast<size_t>(-1) flies to the party instead.
        size_t targetActorIndex = static_cast<size_t>(-1);
        float progress = 0.0f;
        // The flight takes its starting distance at speed (world units per second), kept within these times.
        float speed = 0.0f;
        float minSeconds = 0.0f;
        float maxSeconds = 0.0f;
        float durationSeconds = 0.0f;
        // Height of the upward bow at mid-flight (drains swoop; bolts fly straight).
        float bow = 0.0f;
        std::string impactEffect;
        bool impactFollowsTarget = false;
        // Debuff particles to spawn on the actor when the flight arrives (0: none).
        uint32_t debuffSpellId = 0;
        uint32_t seed = 0;
    };

    ProjectileEffectBindings m_projectileEffectBindings;
    struct LoadedProjectileModel
    {
        std::shared_ptr<const Engine::ModelAsset> asset;
        // World units per model unit (the binding's length over the model's extent along +Z).
        float scale = 1.0f;
        ProjectileModelSpinAxis spinAxis = ProjectileModelSpinAxis::None;
        float spinRadiansPerSecond = 0.0f;
    };
    // By object id.
    std::unordered_map<int16_t, LoadedProjectileModel> m_projectileModelBindings;
    struct ProjectileModel
    {
        Engine::ModelInstanceHandle handle;
        int16_t sectorId = -1;
        // Heading, kept while the projectile is still or settled (a settled one lies level).
        float yaw = 0.0f;
        float pitch = 0.0f;
        bool seen = false;
    };
    // By projectile id (low half); Fire Spike traps by trap id with the high half 1.
    std::unordered_map<uint64_t, ProjectileModel> m_projectileModels;
    // Whether an impact is the splash of a projectile falling into water.
    bool isWaterSplashImpact(const GameplayProjectileImpactPresentationState &impact) const;
    // Item models by the world's presentation key; a key whose item changes gets a new model.
    struct ItemModel
    {
        Engine::ModelInstanceHandle handle;
        uint32_t itemId = 0;
        int16_t sectorId = -1;
        bool seen = false;
        bool placeholder = false;
        // The resting pose, fitted once where the item came to rest.
        std::optional<std::array<float, 3>> restPosition;
        WorldItemRestingPose restPose;
        // The looping sparkle of a valuable, artifact or quest item (WorldItemSparkle), near the party.
        EffectHandle sparkle;
    };
    struct LoadedItemModel
    {
        // Null when the model failed to load (its items draw the placeholder).
        std::shared_ptr<const Engine::ModelAsset> asset;
        float scale = 1.0f;
    };
    const Engine::AssetFileSystem *m_pItemModelAssets = nullptr;
    // By model path, loaded on first use.
    std::unordered_map<std::string, LoadedItemModel> m_loadedItemModels;
    LoadedItemModel m_missingItemModel;
    // Icons already reported as drawing the placeholder this session.
    std::unordered_set<std::string> m_reportedMissingItemIcons;
    std::unordered_map<uint32_t, ItemModel> m_itemModels;
    float m_itemModelSeconds = 0.0f;
    const ItemTable *m_pItemTable = nullptr;
    ItemGroundSampler m_itemGroundSampler;
    // An item's model, or the placeholder (placeholder set) when its icon has none or its model fails to load.
    const LoadedItemModel &loadedItemModel(const GameplayWorldItemPresentationState &item, bool &placeholder);
    void syncItemModels(GameSession &session, float deltaSeconds);
    // The model binding of a projectile's object, or null.
    const LoadedProjectileModel *projectileModelBinding(uint16_t objectDescriptionId) const;
    void syncProjectileModels(GameSession &session);
    std::unordered_map<uint32_t, ProjectileFlightEffect> m_projectileFlightEffects;
    std::vector<SpellVisualFlight> m_spellVisualFlights;
    SpellAuraEffectBindings m_spellAuraEffectBindings;
    std::vector<PartyAuraEffect> m_partyAuraEffects;
    // The session's monster table, for monster variants of projectile bindings (set on each projectile sync).
    const MonsterTable *m_pProjectileMonsterTable = nullptr;
    // Missile token -> object -> projectile recipe, for the colour of a ranged attack's charge.
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pProjectileObjectTable = nullptr;
    bool m_shadowsEnabled = false;
};
}
