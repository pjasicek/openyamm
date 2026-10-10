#include "game/fx/WorldFxSystem.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/data/GameDataRepository.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/import/EffectDefinitionLoader.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/ActorModelPresentation.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"
#include "engine/AssetFileSystem.h"
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <numbers>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ParticleUpdateStepSeconds = 1.0f / 30.0f;
constexpr float MaxParticleUpdateAccumulationSeconds = 0.25f;
constexpr float DefaultProjectileTrailCooldownSeconds = 1.0f / 30.0f;
constexpr float HangingProjectileTrailCooldownSeconds = 2.0f / 128.0f;
constexpr float SparksProjectileTrailCooldownSeconds = 0.10f;
constexpr float ProjectileFxVisualSizeScale = 1.25f;
constexpr float PartySpellFxRingRadius = 28.0f;
constexpr float ImpactLightRadiusScale = 1.18f;
constexpr float ImpactLightIntensityScale = 1.35f;
constexpr uint32_t CannonballPseudoSpellId = 136;

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

bool isCannonballProjectile(const GameplayProjectilePresentationState &projectile)
{
    return projectile.spellId == CannonballPseudoSpellId
        || projectile.objectName == "Cannonball"
        || projectile.objectSpriteName == "CANNBL";
}

bool isSparksSpellProjectile(const GameplayProjectilePresentationState &projectile)
{
    return projectile.spellId >= 0
        && spellIdFromValue(static_cast<uint32_t>(projectile.spellId)) == SpellId::Sparks;
}

uint32_t partySpellFxColorAbgr(const PartySpellCastResult &result)
{
    if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
        || result.effectKind == PartySpellCastEffectKind::PartyRestore)
    {
        return makeAbgr(192, 255, 192, 224);
    }

    if (spellIdInRange(result.spellId, SpellId::LightBolt, SpellId::DivineIntervention))
    {
        return makeAbgr(255, 240, 180, 224);
    }

    if (spellIdInRange(result.spellId, SpellId::Reanimate, SpellId::SoulDrinker))
    {
        return makeAbgr(180, 112, 255, 224);
    }

    if (spellIdInRange(result.spellId, SpellId::CureWeakness, SpellId::PowerCure))
    {
        return makeAbgr(132, 224, 120, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::Telepathy, SpellId::Enslave))
    {
        return makeAbgr(224, 132, 255, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::DetectLife, SpellId::Resurrection))
    {
        return makeAbgr(208, 192, 255, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::Stun, SpellId::MassDistortion))
    {
        return makeAbgr(180, 220, 132, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::Awaken, SpellId::LloydsBeacon))
    {
        return makeAbgr(160, 224, 255, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::WizardEye, SpellId::Starburst))
    {
        return makeAbgr(255, 228, 132, 220);
    }

    if (spellIdInRange(result.spellId, SpellId::TorchLight, SpellId::Incinerate))
    {
        return makeAbgr(255, 144, 72, 224);
    }

    return makeAbgr(255, 255, 255, 208);
}

uint32_t withScaledAlpha(uint32_t colorAbgr, float alphaScale)
{
    const float clampedScale = std::clamp(alphaScale, 0.0f, 1.0f);
    const uint8_t red = static_cast<uint8_t>(colorAbgr & 0xffu);
    const uint8_t green = static_cast<uint8_t>((colorAbgr >> 8) & 0xffu);
    const uint8_t blue = static_cast<uint8_t>((colorAbgr >> 16) & 0xffu);
    const uint8_t alpha = static_cast<uint8_t>(
        std::clamp(
            static_cast<int>(std::lround(static_cast<float>((colorAbgr >> 24) & 0xffu) * clampedScale)),
            0,
            255));

    return makeAbgr(red, green, blue, alpha);
}

float impactLightDurationSeconds(
    FxRecipes::ProjectileRecipe recipe,
    const GameplayProjectileImpactPresentationState &impact)
{
    const float presentationSeconds =
        impact.lifetimeTicks > 0
            ? static_cast<float>(impact.lifetimeTicks) / 128.0f
            : 0.0f;
    float recipeSeconds = 0.68f;

    switch (recipe)
    {
    case FxRecipes::ProjectileRecipe::Blaster:
        recipeSeconds = 0.25f;
        break;
    case FxRecipes::ProjectileRecipe::Fireball:
    case FxRecipes::ProjectileRecipe::DragonBreath:
        recipeSeconds = 0.92f;
        break;
    case FxRecipes::ProjectileRecipe::MeteorShower:
    case FxRecipes::ProjectileRecipe::Starburst:
    case FxRecipes::ProjectileRecipe::Implosion:
        recipeSeconds = 1.08f;
        break;
    case FxRecipes::ProjectileRecipe::ToxicCloud:
        recipeSeconds = 1.0f;
        break;
    case FxRecipes::ProjectileRecipe::None:
        recipeSeconds = 0.0f;
        break;
    default:
        break;
    }

    return std::max(recipeSeconds, presentationSeconds);
}

float impactLightRadius(FxRecipes::ProjectileRecipe recipe)
{
    const float recipeGlowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);

    switch (recipe)
    {
    case FxRecipes::ProjectileRecipe::Blaster:
        return 256.0f;
    case FxRecipes::ProjectileRecipe::MeteorShower:
        return std::max(recipeGlowRadius, 128.0f) * ImpactLightRadiusScale;
    case FxRecipes::ProjectileRecipe::Starburst:
        return std::max(recipeGlowRadius, 136.0f) * ImpactLightRadiusScale;
    case FxRecipes::ProjectileRecipe::Implosion:
        return std::max(recipeGlowRadius, 152.0f) * ImpactLightRadiusScale;
    case FxRecipes::ProjectileRecipe::None:
        return 0.0f;
    default:
        return std::max(recipeGlowRadius, 96.0f) * ImpactLightRadiusScale;
    }
}

bool shouldTriggerPartySpellSparkles(PartySpellCastEffectKind effectKind)
{
    return effectKind == PartySpellCastEffectKind::CharacterRestore
        || effectKind == PartySpellCastEffectKind::PartyRestore;
}

bool shouldTriggerPartySpellBuffAura(PartySpellCastEffectKind effectKind)
{
    return effectKind == PartySpellCastEffectKind::PartyBuff
        || effectKind == PartySpellCastEffectKind::CharacterBuff;
}

float projectileTrailCooldownSeconds(FxRecipes::ProjectileRecipe recipe)
{
    switch (recipe)
    {
        case FxRecipes::ProjectileRecipe::Sparks:
            return SparksProjectileTrailCooldownSeconds;

        default:
            if (FxRecipes::projectileRecipeUsesHangingProjectileTrail(recipe))
            {
                return HangingProjectileTrailCooldownSeconds;
            }

            return DefaultProjectileTrailCooldownSeconds;
    }
}

bool projectileRecipeEmitsTrailParticles(int spellIdValue, FxRecipes::ProjectileRecipe recipe)
{
    if (recipe == FxRecipes::ProjectileRecipe::Blaster
        || recipe == FxRecipes::ProjectileRecipe::Sparks)
    {
        return false;
    }

    const FxRecipes::ProjectileFxRecipe &fxRecipe = FxRecipes::projectileFxRecipe(recipe);

    if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::RenderSprite)
    {
        return false;
    }

    if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::None
        && (fxRecipe.impactPrimitive != FxRecipes::ProjectileFxPrimitive::None
            || fxRecipe.mobileLightRadius > 0.0f
            || !fxRecipe.renderProjectileBillboard))
    {
        return false;
    }

    const SpellId spellId = spellIdFromValue(static_cast<uint32_t>(spellIdValue));
    return spellId != SpellId::MindBlast
        && spellId != SpellId::PsychicShock
        && spellId != SpellId::Harm
        && spellId != SpellId::ToxicCloud
        && spellId != SpellId::Incinerate;
}

std::optional<std::array<float, 3>> actorCenterPosition(GameSession &session, size_t actorIndex)
{
    IGameplayWorldRuntime *pWorldRuntime = session.activeWorldRuntime();
    GameplayRuntimeActorState actorState = {};
    if (pWorldRuntime == nullptr || !pWorldRuntime->actorRuntimeState(actorIndex, actorState))
    {
        return std::nullopt;
    }

    return std::array<float, 3>{
        actorState.preciseX,
        actorState.preciseY,
        actorState.preciseZ + static_cast<float>(actorState.height) * 0.5f
    };
}
}

WorldFxSystem::WorldFxSystem()
{
    m_namedEffects.setModelRuntime(
        &m_models,
        [this](const std::string &id)
        {
            return m_namedEffectResources.findModel(id);
        });
}

void WorldFxSystem::reset()
{
    m_particleUpdateAccumulatorSeconds = 0.0f;
    m_particleSystem.reset();
    m_waterRipples = {};
    m_namedEffects.clear();
    processNamedEffectAudio();
    for (const auto &[key, instanceId] : m_namedSoundInstances)
    {
        if (m_pNamedEffectAudioSystem != nullptr)
        {
            m_pNamedEffectAudioSystem->stopSoundInstance(instanceId);
        }
    }
    m_namedSoundInstances.clear();
    m_namedEffectLibrary.clear();
    m_namedEffectResources.clear();
    m_actorModels.clear();
    m_actorModelBindings.clear();
    m_corpseAssets.clear();
    m_actorModelsConfigured = false;
    m_corpseSatchelStates.clear();
    m_satchelAssets = {};
    m_models.clear();
    m_modelAssets.clear();
    m_glowBillboards.clear();
    m_lightEmitters.clear();
    m_contactShadows.clear();
    m_segmentProjectiles.clear();
    m_projectileTrailStates.clear();
    m_persistentImpactLights.clear();
    m_seenImpactIds.clear();
    m_projectileImpactEffectRebinds.clear();
    m_attachedImpactEffects.clear();
}

bool WorldFxSystem::configureActorModels(const Engine::AssetFileSystem &assets, const std::string &manifestPath,
    const MonsterTable &monsters, const SpriteFrameTable *pSpriteFrames, std::string &error)
{
    if (m_actorModelsConfigured)
    {
        return true;
    }
    const std::optional<std::string> text = assets.readTextFile(manifestPath);
    if (!text)
    {
        m_actorModelsConfigured = true;
        return true; // Worlds without a model binding keep their native presentation.
    }
    std::unordered_map<std::string, ActorModelBinding> bindings;
    try
    {
        const YAML::Node document = YAML::Load(*text);
        if (!document["actors"].IsSequence())
        {
            error = "actor model manifest requires an actors sequence: " + manifestPath;
            return false;
        }
        constexpr std::array<const char *, 8> StateNames = {
            "standing", "walking", "attack_melee", "attack_ranged", "hit", "dying", "dead", "fidget"};
        for (const YAML::Node &entry : document["actors"])
        {
            const std::string descriptor = entry["descriptor"].as<std::string>();
            if (monsters.findByInternalName(descriptor) == nullptr || bindings.contains(descriptor))
            {
                error = "unknown or duplicate actor model descriptor: " + descriptor;
                return false;
            }
            const Engine::ModelLoadResult loaded = m_modelAssets.load(assets, entry["model"].as<std::string>());
            if (!loaded)
            {
                error = loaded.error;
                return false;
            }
            ActorModelBinding binding;
            binding.asset = loaded.asset;
            if (entry["skin"])
            {
                const std::string skin = entry["skin"].as<std::string>();
                const std::optional<uint32_t> variant = binding.asset->findMaterialVariant(skin);
                if (!variant)
                {
                    throw std::runtime_error("actor model skin not found: " + skin);
                }
                binding.materialVariant = *variant;
            }
            const YAML::Node attachments = entry["attachments"];
            for (size_t attachmentIndex = 0; attachments && attachmentIndex < attachments.size(); ++attachmentIndex)
            {
                const YAML::Node item = attachments[attachmentIndex];
                const Engine::ModelLoadResult carried = m_modelAssets.load(assets, item["model"].as<std::string>());
                if (!carried)
                {
                    error = carried.error;
                    return false;
                }
                const std::optional<uint32_t> node = binding.asset->findNode(item["node"].as<std::string>());
                if (!node || !carried.asset->skins.empty())
                {
                    error = "actor attachment needs a node of the actor and an unskinned model: " + descriptor;
                    return false;
                }
                Engine::ModelAttachment attachment{carried.asset, *node, 0};
                // Without its own skin, an item split from the body follows the carrier's skin (same variant names).
                if (item["skin"])
                {
                    const std::optional<uint32_t> variant =
                        carried.asset->findMaterialVariant(item["skin"].as<std::string>());
                    if (!variant)
                    {
                        error = "actor attachment skin not found: " + item["skin"].as<std::string>();
                        return false;
                    }
                    attachment.materialVariant = *variant;
                }
                else if (entry["skin"])
                {
                    attachment.materialVariant =
                        carried.asset->findMaterialVariant(entry["skin"].as<std::string>()).value_or(0);
                }
                binding.attachments.push_back(std::move(attachment));
            }
            binding.scale = entry["scale"].as<float>();
            binding.fxReferenceScale = binding.scale;
            if (entry["scale_reference"])
            {
                const auto standingScale = [&](const std::string &name)
                {
                    const MonsterEntry *pMonster = monsters.findByInternalName(name);
                    const std::optional<uint16_t> frame = pMonster != nullptr && pSpriteFrames != nullptr
                        ? pSpriteFrames->findFrameIndexBySpriteName(pMonster->spriteNames[0]) : std::nullopt;
                    const SpriteFrameEntry *pFrame = frame ? pSpriteFrames->getFrame(*frame, 0) : nullptr;
                    if (pFrame == nullptr || !std::isfinite(pFrame->scale) || pFrame->scale <= 0.0f)
                    {
                        throw std::runtime_error("actor model scale requires a valid standing sprite: " + name);
                    }
                    return pFrame->scale;
                };
                binding.scale *= standingScale(descriptor) / standingScale(entry["scale_reference"].as<std::string>());
            }
            binding.yawOffset = entry["yaw_offset"].as<float>(0.0f);
            binding.zOffset = entry["z_offset"].as<float>(0.0f);
            const std::string deathEffect = entry["death_effect"].as<std::string>("none");
            if (deathEffect != "none" && deathEffect != "disintegration" && deathEffect != "explosion")
            {
                error = "unknown actor model death effect: " + deathEffect;
                return false;
            }
            binding.disintegrates = deathEffect == "disintegration";
            binding.explodes = deathEffect == "explosion";
            if (binding.disintegrates)
            {
                Engine::ModelPose rest;
                Engine::resetModelPose(*binding.asset, rest);
                Engine::evaluateModelHierarchy(*binding.asset, Engine::identityModelMatrix(), rest);
                const Engine::ModelBounds bounds = Engine::modelExactPoseBounds(*binding.asset, rest);
                binding.height = bounds.valid ? bounds.max[1] - bounds.min[1] : 0.0f;
            }
            if (!std::isfinite(binding.scale) || binding.scale <= 0 || !std::isfinite(binding.yawOffset)
                || !std::isfinite(binding.zOffset))
            {
                error = "invalid actor model placement: " + descriptor;
                return false;
            }
            for (size_t i = 0; i < StateNames.size(); ++i)
            {
                const std::string clipName = entry["clips"][StateNames[i]].as<std::string>();
                const std::optional<uint32_t> clip = binding.asset->findClip(clipName);
                if (!clip)
                {
                    error = "actor model clip not found: " + clipName;
                    return false;
                }
                binding.clips[i] = *clip;
            }
            const YAML::Node animation = entry["animation"];
            if (animation)
            {
                if (animation["eye_color"])
                {
                    const std::vector<int> color = animation["eye_color"].as<std::vector<int>>();
                    if (color.size() != 3 || std::any_of(color.begin(), color.end(),
                        [](int value) { return value < 0 || value > 255; }))
                    {
                        throw std::runtime_error("actor eye_color requires three sRGB bytes: " + descriptor);
                    }
                    binding.eyeColorAbgr = makeAbgr(uint8_t(color[0]), uint8_t(color[1]), uint8_t(color[2]), 176);
                }
                if (animation["cast_color"])
                {
                    const std::vector<int> color = animation["cast_color"].as<std::vector<int>>();
                    if (color.size() != 3 || std::any_of(color.begin(), color.end(),
                        [](int value) { return value < 0 || value > 255; }))
                    {
                        throw std::runtime_error("actor cast_color requires three sRGB bytes: " + descriptor);
                    }
                    binding.castColorAbgr = makeAbgr(uint8_t(color[0]), uint8_t(color[1]), uint8_t(color[2]), 255);
                }
                const auto requireClip = [&](const char *name)
                {
                    const std::string clipName = animation[name].as<std::string>();
                    const std::optional<uint32_t> clip = binding.asset->findClip(clipName);
                    if (!clip)
                    {
                        throw std::runtime_error("actor animation clip not found: " + clipName);
                    }
                    return *clip;
                };
                binding.castClip = requireClip("cast");
                binding.castGlowScale = animation["cast_glow_scale"].as<float>(1.0f);
                binding.castFocusGlowScale = animation["cast_focus_glow_scale"].as<float>(1.0f);
                if (!std::isfinite(binding.castGlowScale) || binding.castGlowScale <= 0.0f
                    || !std::isfinite(binding.castFocusGlowScale) || binding.castFocusGlowScale <= 0.0f)
                {
                    throw std::runtime_error("invalid actor cast glow scale: " + descriptor);
                }
                if (animation["cast_focus_socket"])
                {
                    const std::string name = animation["cast_focus_socket"].as<std::string>();
                    const std::optional<uint32_t> node = binding.asset->findNode(name);
                    if (!node)
                    {
                        throw std::runtime_error("actor cast focus socket not found: " + name);
                    }
                    binding.castFocusSocket = *node;
                }
                binding.runClip = requireClip("run");
                binding.strideLength = animation["stride_length"].as<float>();
                if (!std::isfinite(binding.strideLength) || binding.strideLength <= 0.0f)
                {
                    throw std::runtime_error("invalid actor animation stride: " + descriptor);
                }
                const std::string rootName = animation["upper_body_root"].as<std::string>();
                const std::optional<uint32_t> root = binding.asset->findNode(rootName);
                if (!root)
                {
                    throw std::runtime_error("actor animation mask root not found: " + rootName);
                }
                std::shared_ptr<std::vector<float>> mask =
                    std::make_shared<std::vector<float>>(binding.asset->nodes.size(), 0.0f);
                for (uint32_t node : binding.asset->hierarchyOrder)
                {
                    const int32_t parent = binding.asset->nodes[node].parentIndex;
                    (*mask)[node] = node == *root ? 1.0f : parent >= 0 ? (*mask)[parent] : 0.0f;
                }
                binding.upperBodyMask = std::move(mask);
                constexpr std::array<const char *, 4> SocketNames =
                    {"eye_left", "eye_right", "palm_left", "palm_right"};
                const YAML::Node sockets = animation["sockets"];
                for (size_t i = 0; sockets && i < SocketNames.size(); ++i)
                {
                    if (!sockets[SocketNames[i]])
                    {
                        continue;
                    }
                    const std::string name = sockets[SocketNames[i]].as<std::string>();
                    const std::optional<uint32_t> node = binding.asset->findNode(name);
                    if (!node)
                    {
                        throw std::runtime_error("actor animation socket not found: " + name);
                    }
                    binding.sockets[i] = *node;
                }
                if (animation["ranged_hand_effects"])
                {
                    const std::vector<std::string> sockets =
                        animation["ranged_hand_sockets"].as<std::vector<std::string>>();
                    if (sockets.empty() || sockets.size() > 2)
                    {
                        throw std::runtime_error("actor ranged hand effects require one or two sockets: " + descriptor);
                    }
                    for (size_t i = 0; i < sockets.size(); ++i)
                    {
                        const std::optional<uint32_t> node = binding.asset->findNode(sockets[i]);
                        if (!node || (i > 0 && *node == binding.rangedHandSockets[0]))
                        {
                            throw std::runtime_error("actor ranged hand socket missing or duplicated: " + sockets[i]);
                        }
                        binding.rangedHandSockets[i] = *node;
                    }
                    const MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsByPictureName(descriptor);
                    if (pStats == nullptr || !animation["ranged_hand_effects"].IsMap())
                    {
                        throw std::runtime_error(
                            "actor ranged hand effects require missile data and a map: " + descriptor);
                    }
                    for (const auto &recipe : animation["ranged_hand_effects"])
                    {
                        const FxRecipes::ProjectileRecipe element =
                            FxRecipes::classifyProjectileRecipe(0, recipe.first.as<std::string>(), "", 0);
                        const std::string effect = recipe.second.as<std::string>();
                        if (element < FxRecipes::ProjectileRecipe::MonsterAirBolt
                            || element > FxRecipes::ProjectileRecipe::MonsterDarkBolt
                            || m_namedEffectLibrary.find(effect) == nullptr)
                        {
                            throw std::runtime_error("actor ranged hand element/effect not found: " + descriptor);
                        }
                        for (size_t slot = 0; slot < 2; ++slot)
                        {
                            const bool hasMissile = slot == 0 ? pStats->attack1HasMissile : pStats->attack2HasMissile;
                            const std::string &token = slot == 0
                                ? pStats->attack1MissileType : pStats->attack2MissileType;
                            if (hasMissile && element == FxRecipes::classifyProjectileRecipe(0, token, "", 0))
                            {
                                if (!binding.rangedHandEffects[slot].empty())
                                {
                                    throw std::runtime_error("duplicate actor ranged hand element: " + descriptor);
                                }
                                binding.rangedHandEffects[slot] = effect;
                            }
                        }
                    }
                }
            }
            const MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsByPictureName(descriptor);
            if (pStats != nullptr && (pStats->hasSpell1 || pStats->hasSpell2)
                && (binding.castClip == UINT32_MAX || binding.castClip == binding.clips[2]
                    || binding.castClip == binding.clips[3]))
            {
                throw std::runtime_error("spellcasting actor model requires a distinct cast clip: " + descriptor);
            }
            bindings.emplace(descriptor, std::move(binding));
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = manifestPath + ": " + exception.what();
        return false;
    }
    catch (const std::runtime_error &exception)
    {
        error = manifestPath + ": " + exception.what();
        return false;
    }
    m_actorModelBindings = std::move(bindings);
    m_actorModelsConfigured = true;
    return true;
}

void WorldFxSystem::stopActorHandFx(ActorModelInstance &model, EffectStopMode mode)
{
    for (EffectHandle &effect : model.rangedHandEffects)
    {
        m_namedEffects.stop(effect, mode);
        effect = {};
    }
}

void WorldFxSystem::syncActorModels(const IGameplayWorldRuntime &world, float deltaSeconds)
{
    if (m_actorModelBindings.empty())
    {
        return;
    }
    std::unordered_set<size_t> retained;
    const MonsterTable *pMonsters = world.monsterTable();
    for (size_t index = 0; pMonsters != nullptr && index < world.mapActorCount(); ++index)
    {
        GameplayRuntimeActorState state;
        if (!world.actorRuntimeState(index, state) || state.isInvisible)
        {
            continue;
        }
        const MonsterEntry *pMonster = pMonsters->findById(state.monsterId);
        if (pMonster == nullptr)
        {
            continue;
        }
        const auto bindingIterator = m_actorModelBindings.find(pMonster->internalName);
        if (bindingIterator == m_actorModelBindings.end())
        {
            continue;
        }
        const ActorModelBinding &binding = bindingIterator->second;
        if (goneCorpse(index) != nullptr)
        {
            continue;   // sunk; its loot satchel presents the actor
        }
        auto instance = m_actorModels.find(index);
        if (instance != m_actorModels.end()
            && (instance->second.actorId != state.actorId || instance->second.monsterId != state.monsterId))
        {
            stopActorHandFx(instance->second, EffectStopMode::Drain);
            m_models.destroy(instance->second.handle);
            m_actorModels.erase(instance);
            instance = m_actorModels.end();
        }
        if (instance == m_actorModels.end())
        {
            const Engine::ModelInstanceHandle handle = m_models.create(binding.asset);
            m_models.setMaterialVariant(handle, binding.materialVariant);
            m_models.setAttachments(handle, binding.attachments);
            instance = m_actorModels.emplace(index, ActorModelInstance{handle, state.actorId, state.monsterId}).first;
        }
        retained.insert(index);
        m_models.setOutlineColor(instance->second.handle, 0);
        const size_t animationIndex = size_t(state.animationState);
        if (animationIndex >= binding.clips.size())
        {
            continue;
        }
        ActorModelInstance &model = instance->second;
        model.pBinding = &binding;
        const float scale = binding.scale * state.visualScale
            * (pMonster->height > 0 && state.bodyHeight > 0 ? float(state.bodyHeight) / pMonster->height : 1.0f);
        model.fxScale = scale / binding.fxReferenceScale;
        const float distance = std::hypot(state.preciseX - model.previousX, state.preciseY - model.previousY);
        const bool teleported = model.initialized && distance > std::max(256.0f, scale * 8.0f);
        const float speed = std::hypot(state.velocityX, state.velocityY);
        if (!model.initialized || teleported)
        {
            stopActorHandFx(model, EffectStopMode::Immediate);
            model.yaw = state.yawRadians;
            model.gaitPhase = 0.0f;
        }
        else if (!model.dying && state.animationState != ActorAiAnimationState::Dead)
        {
            // Visual facing only. Collision, LOS, paths and projectile aiming retain the AI's exact yaw.
            model.yaw = advanceActorModelYaw(model.yaw, state.yawRadians, deltaSeconds,
                3.0f * std::numbers::pi_v<float>);
            if (binding.strideLength > 0.0f && deltaSeconds > 0.0f)
            {
                const float stride = binding.strideLength * (speed > scale * 2.4f ? 1.55f : 1.0f);
                model.gaitPhase = advanceActorModelGait(model.gaitPhase, distance, stride * scale);
            }
        }
        const bool moving = speed > 4.0f && !teleported;
        const bool attacking = state.animationState == ActorAiAnimationState::AttackMelee
            || state.animationState == ActorAiAnimationState::AttackRanged;
        const bool casting = attacking && state.castingSpell && binding.castClip != UINT32_MAX;
        if (model.secondaryAttack != state.secondaryAttack)
        {
            stopActorHandFx(model, EffectStopMode::Drain);
        }
        model.secondaryAttack = state.secondaryAttack;
        model.rangedHandActive = state.animationState == ActorAiAnimationState::AttackRanged
            && !state.castingSpell && !state.attackImpactTriggered
            && !binding.rangedHandEffects[model.secondaryAttack].empty();
        const bool restart = model.initialized && (model.previousState != animationIndex
            || model.casting != casting || (attacking && state.animationTimeTicks + 0.01f < model.previousTime));
        if (casting && (!model.casting || restart))
        {
            model.castDuration = std::max(0.1f, state.animationTimeTicks / 128.0f + state.actionSeconds);
            model.hasCastOrigin = false;
            model.pendingRelease = false;
            const FxRecipes::ProjectileRecipe recipe =
                FxRecipes::classifyProjectileRecipe(int(state.castingSpellId), "", "", 0);
            model.castColor = binding.castColorAbgr != 0 ? binding.castColorAbgr
                : FxRecipes::projectileRecipeColorAbgr(recipe);
        }
        if (model.casting && state.attackImpactTriggered && !model.previousImpact)
        {
            model.pendingRelease = model.hasCastOrigin && model.castOriginAge < 0.15f;
        }
        if (state.animationState == ActorAiAnimationState::GotHit
            || state.animationState == ActorAiAnimationState::Dying || state.isInvisible)
        {
            model.pendingRelease = false;
            model.hasCastOrigin = false;
        }
        uint32_t clip = casting ? binding.castClip : binding.clips[animationIndex];
        float time = std::max(state.animationTimeTicks, 0.0f) / 128.0f;
        const float duration = binding.asset->clips[clip].durationSeconds;
        if (casting)
        {
            model.castProgress = std::clamp(time / model.castDuration, 0.0f, 1.0f);
            time = model.castProgress * duration;
        }
        const bool dying = state.animationState == ActorAiAnimationState::Dying;
        if (binding.disintegrates && dying && !instance->second.dying)
        {
            const float height = binding.scale * state.visualScale * binding.height
                * (pMonster->height > 0 && state.bodyHeight > 0 ? float(state.bodyHeight) / pMonster->height : 1.0f);
            FxRecipes::spawnActorDisintegrationParticles(m_particleSystem, state.actorId,
                state.preciseX, state.preciseY, state.preciseZ + binding.zOffset, height, time, duration);
        }
        if (binding.explodes && dying && !instance->second.dying)
        {
            FxRecipes::ImpactSpawnContext explosion = {};
            explosion.recipe = FxRecipes::ProjectileRecipe::Fireball;
            explosion.x = state.preciseX;
            explosion.y = state.preciseY;
            explosion.z = state.preciseZ + binding.zOffset + float(state.height) * 0.5f;
            FxRecipes::spawnImpactParticles(m_particleSystem, explosion);
        }
        instance->second.dying = dying;
        if (dying && !binding.disintegrates)
        {
            model.deathClipTime = time;
        }
        else if (state.animationState == ActorAiAnimationState::Dead && model.deathClipTime >= 0.0f)
        {
            // The AI switches to the corpse after the native sprite death length; a longer model death clip
            // finishes first, then the dead clip holds.
            const uint32_t deathClip = binding.clips[size_t(ActorAiAnimationState::Dying)];
            model.deathClipTime += deltaSeconds;
            if (model.deathClipTime < binding.asset->clips[deathClip].durationSeconds)
            {
                clip = deathClip;
                time = model.deathClipTime;
            }
            else
            {
                model.deathClipTime = -1.0f;
            }
        }
        else
        {
            model.deathClipTime = -1.0f;
        }
        if ((state.animationState == ActorAiAnimationState::Standing
                || state.animationState == ActorAiAnimationState::Walking) && duration > 0)
        {
            time = std::fmod(time, duration);
        }
        Engine::ModelAnimationLayer layer;
        bool backwardsChanged = false;
        if (binding.strideLength > 0.0f && (state.animationState == ActorAiAnimationState::Walking
                || (moving && attacking)))
        {
            uint32_t locomotion = binding.clips[size_t(ActorAiAnimationState::Walking)];
            if (speed > scale * 2.4f)
            {
                locomotion = binding.runClip;
            }
            const bool backwards = state.velocityX * std::cos(model.yaw)
                + state.velocityY * std::sin(model.yaw) < (model.backwards ? -0.15f : -0.35f) * speed;
            backwardsChanged = backwards != model.backwards;
            model.backwards = backwards;
            const float phase = backwards ? std::fmod(1.0f - model.gaitPhase, 1.0f) : model.gaitPhase;
            if (attacking && binding.upperBodyMask)
            {
                layer = {clip, time, 1.0f, binding.upperBodyMask};
            }
            clip = locomotion;
            time = phase * binding.asset->clips[clip].durationSeconds;
        }
        // Animation LOD: distant actors sample their clips at 15 Hz beyond ~14 m and at the native sprite rate (8 Hz)
        // beyond ~28 m. A per-actor phase offset spreads the updates; root motion stays per frame, and an unchanged
        // clip time only recomposes the joint hierarchy.
        const float partyDistance = std::hypot(state.preciseX - world.partyX(), state.preciseY - world.partyY());
        const float sampleStep = !m_actorAnimationLod ? 0.0f
            : partyDistance > 3000.0f ? 1.0f / 8.0f : partyDistance > 1500.0f ? 1.0f / 15.0f : 0.0f;
        if (sampleStep > 0.0f)
        {
            const float offset = sampleStep * std::fmod(float(model.actorId) * 0.618034f, 1.0f);
            const auto quantize = [&](float seconds)
            {
                return std::max(0.0f, std::floor((seconds + offset) / sampleStep) * sampleStep - offset);
            };
            time = quantize(time);
            if (layer.weight > 0.0f)
            {
                layer.timeSeconds = quantize(layer.timeSeconds);
            }
        }
        const float sink = actorCorpseSinkDepth(index);
        m_models.setCoverage(model.handle, sink > 0.0f
            ? corpseSinkPresentation(m_corpseSatchelStates.at(index).restSeconds).coverage : 1.0f);
        const Engine::ModelTransform transform = Engine::gltfModelPlacement(
            {state.preciseX, state.preciseY, state.preciseZ + binding.zOffset - sink},
            model.yaw + binding.yawOffset, scale);
        const float transitionSeconds = dying || state.animationState == ActorAiAnimationState::Dead
            || teleported ? 0.0f : state.animationState == ActorAiAnimationState::GotHit ? 0.06f : 0.12f;
        m_models.sampleBlended(model.handle, clip, time, transform, deltaSeconds, transitionSeconds,
            layer, restart || backwardsChanged);
        // A corpse no longer moves once the death clip has finished and its Dead clip is held (past its end, or the
        // corpse's clock stopped: dead actors are not updated). It is then drawn as a static instance of the baked pose
        // (instanced with every corpse of its model, no skinning, coarser LODs); picking and loot still use the actor
        // instance, whose frozen pose matches the bake.
        const uint32_t deadClip = binding.clips[size_t(ActorAiAnimationState::Dead)];
        const float deadDuration = binding.asset->clips[deadClip].durationSeconds;
        const bool corpseStandIn = state.animationState == ActorAiAnimationState::Dead && model.deathClipTime < 0.0f
            && clip == deadClip && layer.weight == 0.0f && model.initialized
            && (time >= deadDuration || state.animationTimeTicks == model.previousTime);
        if (corpseStandIn != model.corpseStandIn)
        {
            m_models.setStaticStandIn(model.handle,
                corpseStandIn ? corpseAsset(binding.asset, deadClip, std::min(time, deadDuration)) : nullptr);
            model.corpseStandIn = corpseStandIn;
        }
        model.initialized = true;
        model.previousX = state.preciseX;
        model.previousY = state.preciseY;
        model.previousTime = state.animationTimeTicks;
        model.previousState = uint8_t(animationIndex);
        model.casting = casting;
        model.previousImpact = state.attackImpactTriggered;
    }
    for (auto iterator = m_actorModels.begin(); iterator != m_actorModels.end();)
    {
        if (!retained.contains(iterator->first))
        {
            stopActorHandFx(iterator->second, EffectStopMode::Drain);
            m_models.destroy(iterator->second.handle);
            iterator = m_actorModels.erase(iterator);
        }
        else
        {
            ++iterator;
        }
    }
}

std::shared_ptr<const Engine::ModelAsset> WorldFxSystem::corpseAsset(
    const std::shared_ptr<const Engine::ModelAsset> &asset, uint32_t deadClip, float timeSeconds)
{
    // Keyed by the held time in milliseconds: a corpse shows its Dead clip at 0 s (actor clock stopped at death) or at
    // its end, so a model gets one or two bakes.
    const uint32_t milliseconds = uint32_t(std::lround(timeSeconds * 1000.0f));
    std::shared_ptr<const Engine::ModelAsset> &baked = m_corpseAssets[{asset.get(), deadClip, milliseconds}];
    if (baked == nullptr)
    {
        Engine::ModelPose pose;
        Engine::resetModelPose(*asset, pose);
        Engine::evaluateModelClip(*asset, deadClip, float(milliseconds) / 1000.0f, pose);
        Engine::evaluateModelHierarchy(*asset, Engine::identityModelMatrix(), pose);
        baked = Engine::bakeStaticModelPose(*asset, pose);
    }
    return baked;
}

bool WorldFxSystem::configureCorpseSatchels(const Engine::AssetFileSystem &assets, std::string &error)
{
    if (m_satchelAssets[0] != nullptr)
    {
        return true;
    }
    for (size_t tier = 0; tier < m_satchelAssets.size(); ++tier)
    {
        const std::string path = "engine/models/loot_satchel_t" + std::to_string(tier + 1) + ".glb";
        const Engine::ModelLoadResult loaded = m_modelAssets.load(assets, path);
        if (!loaded)
        {
            error = loaded.error;
            m_satchelAssets = {};
            return false;
        }
        m_satchelAssets[tier] = loaded.asset;
    }
    return true;
}

void WorldFxSystem::setCorpseSatchels(bool enabled)
{
    if (enabled == m_corpseSatchels)
    {
        return;
    }
    m_corpseSatchels = enabled;
    for (const auto &[index, corpse] : m_corpseSatchelStates)
    {
        m_models.destroy(corpse.handle);
    }
    m_corpseSatchelStates.clear();
}

void WorldFxSystem::syncCorpseSatchels(const IGameplayWorldRuntime &world, float deltaSeconds)
{
    if (!m_corpseSatchels || m_satchelAssets[0] == nullptr)
    {
        return;
    }
    // GLB metres to world units, as the creature models. The satchels are authored at their in-game widths
    // (0.5-1.25 m, the size of the game's dropped items, so grass does not hide them).
    constexpr float UnitsPerMetre = 105.0f;
    for (auto iterator = m_corpseSatchelStates.begin(); iterator != m_corpseSatchelStates.end();)
    {
        CorpseSatchel &corpse = iterator->second;
        GameplayRuntimeActorState state;
        const bool fallen = world.actorRuntimeState(iterator->first, state) && !state.isInvisible
            && state.actorId == corpse.actorId && (state.isDead || state.animationState == ActorAiAnimationState::Dying
                || state.animationState == ActorAiAnimationState::Dead);
        if (!fallen)
        {
            m_models.destroy(corpse.handle);
            iterator = m_corpseSatchelStates.erase(iterator);
        }
        else
        {
            ++iterator;
        }
    }
    for (size_t index = 0; index < world.mapActorCount(); ++index)
    {
        GameplayRuntimeActorState state;
        if (!world.actorRuntimeState(index, state) || state.isInvisible
            || (!state.isDead && state.animationState != ActorAiAnimationState::Dying
                && state.animationState != ActorAiAnimationState::Dead))
        {
            continue;
        }
        const std::optional<uint32_t> lootValue = world.corpseLootValue(index);
        auto found = m_corpseSatchelStates.find(index);
        if (found == m_corpseSatchelStates.end())
        {
            CorpseSatchel corpse;
            corpse.actorId = state.actorId;
            corpse.yaw = std::fmod(float(state.actorId) * 2.399963f, 2.0f * std::numbers::pi_v<float>);
            // A corpse first seen at rest (a loaded map) shows its satchel at once; a fresh death plays out.
            if (state.animationState == ActorAiAnimationState::Dead && lootValue)
            {
                corpse.restSeconds = CorpseRestSeconds + std::max(CorpseSinkSeconds, CorpseSatchelAppearSeconds);
                corpse.gone = true;
            }
            found = m_corpseSatchelStates.emplace(index, corpse).first;
        }
        CorpseSatchel &corpse = found->second;
        if (!corpse.gone)
        {
            // At rest: a model once its death clip has finished and its corpse pose is held, a sprite in its dead frame.
            // Without rolled loot (no corpse view), the body stays.
            const auto model = m_actorModels.find(index);
            const bool atRest = model != m_actorModels.end() ? model->second.corpseStandIn
                : state.animationState == ActorAiAnimationState::Dead;
            if (corpse.restSeconds < 0.0f && atRest && lootValue)
            {
                const Engine::ModelBounds *pPose =
                    model != m_actorModels.end() ? m_models.cullingBounds(model->second.handle) : nullptr;
                const float height = pPose != nullptr && pPose->valid ? pPose->max[2] - state.preciseZ
                    : float(state.bodyHeight > 0 ? state.bodyHeight : state.height);
                corpse.sinkDepth = std::max(height, 16.0f) + 8.0f;
                corpse.restSeconds = 0.0f;
            }
            else if (corpse.restSeconds >= 0.0f)
            {
                corpse.restSeconds += deltaSeconds;
            }
            corpse.gone = corpse.restSeconds >= 0.0f && corpseSinkPresentation(corpse.restSeconds).gone;
        }
        else
        {
            corpse.restSeconds += deltaSeconds;
        }
        // The satchel appears as the body starts to dissolve.
        const uint32_t tier = corpse.restSeconds >= CorpseRestSeconds && lootValue ? corpseSatchelTier(*lootValue) : 0;
        if (tier != corpse.tier)
        {
            m_models.destroy(corpse.handle);
            corpse.handle = tier > 0 ? m_models.create(m_satchelAssets[tier - 1]) : Engine::ModelInstanceHandle {};
            m_models.setStaticStandIn(corpse.handle, tier > 0 ? m_satchelAssets[tier - 1] : nullptr);
            corpse.tier = tier;
        }
        if (tier > 0)
        {
            const CorpseSinkPresentation presentation = corpseSinkPresentation(corpse.restSeconds);
            m_models.setCoverage(corpse.handle, presentation.satchelCoverage);
            m_models.setTransform(corpse.handle, Engine::gltfModelPlacement(
                {state.preciseX, state.preciseY, state.preciseZ - 2.0f}, corpse.yaw,
                UnitsPerMetre * presentation.satchelScale));
        }
    }
}

float WorldFxSystem::actorCorpseSinkDepth(size_t actorIndex) const
{
    const auto found = m_corpseSatchelStates.find(actorIndex);
    if (found == m_corpseSatchelStates.end() || found->second.restSeconds < 0.0f || found->second.gone)
    {
        return 0.0f;
    }
    return corpseSinkPresentation(found->second.restSeconds).depthFraction * found->second.sinkDepth;
}

const WorldFxSystem::CorpseSatchel *WorldFxSystem::goneCorpse(size_t actorIndex) const
{
    const auto found = m_corpseSatchelStates.find(actorIndex);
    return found != m_corpseSatchelStates.end() && found->second.gone ? &found->second : nullptr;
}

bool WorldFxSystem::hasActorModel(size_t actorIndex) const
{
    return m_actorModels.contains(actorIndex) || goneCorpse(actorIndex) != nullptr;
}

void WorldFxSystem::syncActorModelFx(const IGameplayWorldRuntime &world, float deltaSeconds, bool refreshSpatialFx)
{
    if (m_actorModels.empty())
    {
        return;
    }
    struct Candidate
    {
        ActorModelInstance *pModel;
        float distanceSquared;
    };
    std::array<Candidate, 8> candidates = {};
    size_t count = 0;
    const float yaw = world.gameplayCameraYawRadians();
    const float forwardX = std::cos(yaw), forwardY = std::sin(yaw);
    for (auto &[index, model] : m_actorModels)
    {
        model.fxCooldown = std::max(0.0f, model.fxCooldown - deltaSeconds);
        model.castOriginAge += deltaSeconds;
        const float dx = model.previousX - world.partyX();
        const float dy = model.previousY - world.partyY();
        const float distanceSquared = dx * dx + dy * dy;
        // ponytail: eight nearby attachments use a camera cone; reuse render visibility if hidden-room FX costs grow.
        const bool near = distanceSquared < 2048.0f * 2048.0f
            && dx * forwardX + dy * forwardY > 0.4f * std::sqrt(distanceSquared) - 160.0f;
        if (!near || model.dying || model.previousState == uint8_t(ActorAiAnimationState::Dead)
            || model.pBinding == nullptr
            || (model.pBinding->eyeColorAbgr == 0 && !model.casting && !model.rangedHandActive
                && !model.pendingRelease))
        {
            model.pendingRelease = false;
            model.hasCastOrigin = false;
            continue;
        }
        size_t insert = 0;
        while (insert < count && candidates[insert].distanceSquared <= distanceSquared)
        {
            ++insert;
        }
        if (insert < candidates.size())
        {
            count = std::min(count + 1, candidates.size());
            for (size_t i = count - 1; i > insert; --i)
            {
                candidates[i] = candidates[i - 1];
            }
            candidates[insert] = {&model, distanceSquared};
        }
    }
    for (auto &[index, model] : m_actorModels)
    {
        if (!model.rangedHandActive || std::none_of(candidates.begin(), candidates.begin() + count,
            [&](const Candidate &candidate) { return candidate.pModel == &model; }))
        {
            stopActorHandFx(model, EffectStopMode::Drain);
        }
    }
    for (size_t i = 0; i < count; ++i)
    {
        ActorModelInstance &model = *candidates[i].pModel;
        const ActorModelBinding &binding = *model.pBinding;
        if (model.rangedHandActive)
        {
            for (size_t hand = 0; hand < binding.rangedHandSockets.size(); ++hand)
            {
                const Engine::ModelMatrix *pSocket = m_models.nodeMatrix(model.handle, binding.rangedHandSockets[hand]);
                if (pSocket == nullptr)
                {
                    continue;
                }
                const std::array<float, 3> point = {(*pSocket)[12], (*pSocket)[13], (*pSocket)[14]};
                if (deltaSeconds > 0.0f && !m_namedEffects.contains(model.rangedHandEffects[hand]))
                {
                    EffectSpawnParams params;
                    params.position = point;
                    params.scale = model.fxScale;
                    params.seed = model.actorId;
                    model.rangedHandEffects[hand] = m_namedEffects.spawn(
                        binding.rangedHandEffects[model.secondaryAttack], params);
                }
                m_namedEffects.setTransform(model.rangedHandEffects[hand], point, {0, 0, 0, 1}, model.fxScale);
            }
        }
        if (model.casting)
        {
            const Engine::ModelMatrix *pLeft = m_models.nodeMatrix(model.handle, binding.sockets[2]);
            const Engine::ModelMatrix *pRight = m_models.nodeMatrix(model.handle, binding.sockets[3]);
            const Engine::ModelMatrix *pFocus = m_models.nodeMatrix(model.handle, binding.castFocusSocket);
            model.castOriginCount = 0;
            if (pLeft != nullptr || pRight != nullptr)
            {
                const Engine::ModelMatrix &left = pLeft != nullptr ? *pLeft : *pRight;
                const Engine::ModelMatrix &right = pRight != nullptr ? *pRight : *pLeft;
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    model.castOrigins[0][axis] = (left[12 + axis] + right[12 + axis]) * 0.5f;
                }
                model.castOriginScales[0] = binding.castGlowScale;
                model.castOriginCount = 1;
            }
            if (pFocus != nullptr)
            {
                model.castOrigins[model.castOriginCount] = {(*pFocus)[12], (*pFocus)[13], (*pFocus)[14]};
                model.castOriginScales[model.castOriginCount] = binding.castFocusGlowScale;
                ++model.castOriginCount;
            }
            if (model.castOriginCount > 0)
            {
                model.hasCastOrigin = true;
                model.castOriginAge = 0.0f;
            }
        }
        const float charge = std::clamp((model.castProgress - 0.25f) / 0.5f, 0.0f, 1.0f);
        if (refreshSpatialFx && model.casting && model.hasCastOrigin && charge > 0.0f)
        {
            const uint32_t coreColor = makeAbgr(
                ((model.castColor & 0xffu) + 255) / 2,
                (((model.castColor >> 8) & 0xffu) + 255) / 2,
                (((model.castColor >> 16) & 0xffu) + 255) / 2, 240);
            for (size_t origin = 0; origin < model.castOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.castOrigins[origin];
                const float castFxScale = 2.0f * model.fxScale * model.castOriginScales[origin];
                const float radius = (8.0f + 24.0f * charge) * castFxScale;
                addGlowBillboard(point[0], point[1], point[2], radius, (model.castColor & 0x00ffffffu) | 0xa0000000u);
                addGlowBillboard(point[0], point[1], point[2], radius * 0.5f, coreColor);
                if (origin == 0)
                {
                    addLightEmitter(point[0], point[1], point[2], 128.0f * charge * castFxScale, model.castColor, -1,
                        RenderLightKind::GenericFx, model.actorId, false);
                }
            }
        }
        if (deltaSeconds > 0.0f && model.pendingRelease && model.hasCastOrigin)
        {
            for (size_t origin = 0; origin < model.castOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.castOrigins[origin];
                FxRecipes::spawnBuffSparkles(m_particleSystem, model.actorId, point[0], point[1], point[2], 8.0f,
                    model.castColor);
            }
            model.pendingRelease = false;
            model.hasCastOrigin = false;
        }
        if (deltaSeconds <= 0.0f || model.fxCooldown > 0.0f)
        {
            continue;
        }
        model.fxCooldown = 0.10f;
        const auto spawnEmber = [&](const std::array<float, 3> &point, float size, uint32_t color,
            const std::array<float, 3> &velocity = {0, 0, 7}, float lifetimeSeconds = 0.18f)
        {
            FxParticleState ember;
            ember.x = point[0];
            ember.y = point[1];
            ember.z = point[2];
            ember.size = size;
            ember.endSize = size * 0.2f;
            ember.velocityX = velocity[0];
            ember.velocityY = velocity[1];
            ember.velocityZ = velocity[2];
            ember.motion = FxParticleMotion::Ascend;
            ember.lifetimeSeconds = lifetimeSeconds;
            ember.fadeOutStartSeconds = lifetimeSeconds - 0.13f;
            ember.startColorAbgr = color;
            ember.endColorAbgr = color & 0x00ffffffu;
            ember.blendMode = FxParticleBlendMode::Additive;
            ember.material = FxParticleMaterial::Ember;
            m_particleSystem.addParticle(ember);
        };
        if (model.casting && model.hasCastOrigin && charge > 0.0f)
        {
            for (size_t origin = 0; origin < model.castOriginCount; ++origin)
            {
                const std::array<float, 3> &point = model.castOrigins[origin];
                const float castFxScale = 2.0f * model.fxScale * model.castOriginScales[origin];
                for (size_t spark = 0; spark < 3; ++spark)
                {
                    const float angle = model.castProgress * 12.0f + float(model.actorId)
                        + float(spark) * (2.0f * std::numbers::pi_v<float> / 3.0f);
                    const float x = std::cos(angle), y = std::sin(angle);
                    const float radius = (4.0f + 10.0f * charge) * castFxScale;
                    spawnEmber({point[0] + x * radius, point[1] + y * radius,
                        point[2] + std::sin(angle * 2.0f) * radius * 0.5f},
                        12.0f * castFxScale, (model.castColor & 0x00ffffffu) | 0xe0000000u,
                        {x * 32.0f * castFxScale, y * 32.0f * castFxScale, 45.0f * castFxScale}, 0.35f);
                }
            }
        }
        for (size_t eye = 0; eye < 2; ++eye)
        {
            const Engine::ModelMatrix *pSocket = m_models.nodeMatrix(model.handle, binding.sockets[eye]);
            if (pSocket == nullptr)
            {
                continue;
            }
            if (binding.eyeColorAbgr != 0)
            {
                spawnEmber({(*pSocket)[12], (*pSocket)[13], (*pSocket)[14]}, 0.8f, binding.eyeColorAbgr);
            }
        }
    }
}

// A sunk corpse without loot has no satchel: its bounds are empty, so nothing is picked there.
namespace
{
const Engine::ModelBounds NoActorModelBounds = {};
}

const Engine::ModelBounds *WorldFxSystem::actorModelBounds(size_t actorIndex) const
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        const Engine::ModelBounds *pBounds = m_models.pickingBounds(pCorpse->handle);
        return pBounds != nullptr ? pBounds : &NoActorModelBounds;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    return iterator != m_actorModels.end() ? m_models.pickingBounds(iterator->second.handle) : nullptr;
}

const Engine::ModelBounds *WorldFxSystem::actorModelCullingBounds(size_t actorIndex) const
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        const Engine::ModelBounds *pBounds = m_models.motionBounds(pCorpse->handle);
        return pBounds != nullptr ? pBounds : &NoActorModelBounds;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    return iterator != m_actorModels.end() ? m_models.motionBounds(iterator->second.handle) : nullptr;
}

const Engine::ModelBounds *WorldFxSystem::actorModelPoseBounds(size_t actorIndex) const
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        const Engine::ModelBounds *pBounds = m_models.cullingBounds(pCorpse->handle);
        return pBounds != nullptr ? pBounds : &NoActorModelBounds;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    return iterator != m_actorModels.end() ? m_models.cullingBounds(iterator->second.handle) : nullptr;
}

void WorldFxSystem::setActorModelOutline(size_t actorIndex, uint32_t colorAbgr)
{
    if (const CorpseSatchel *pCorpse = goneCorpse(actorIndex))
    {
        m_models.setOutlineColor(pCorpse->handle, colorAbgr);
        return;
    }
    const auto iterator = m_actorModels.find(actorIndex);
    if (iterator != m_actorModels.end())
    {
        m_models.setOutlineColor(iterator->second.handle, colorAbgr);
    }
}

size_t WorldFxSystem::NamedSoundKeyHash::operator()(const NamedSoundKey &key) const
{
    size_t value = static_cast<size_t>(key.owner.index);
    value ^= static_cast<size_t>(key.owner.generation) + 0x9e3779b9u + (value << 6) + (value >> 2);
    value ^= static_cast<size_t>(key.componentId) + 0x9e3779b9u + (value << 6) + (value >> 2);
    return value;
}

void WorldFxSystem::bindNamedEffectAudio(GameAudioSystem *pAudioSystem)
{
    if (m_pNamedEffectAudioSystem == pAudioSystem)
    {
        return;
    }
    for (const auto &[key, instanceId] : m_namedSoundInstances)
    {
        if (m_pNamedEffectAudioSystem != nullptr)
        {
            m_pNamedEffectAudioSystem->stopSoundInstance(instanceId);
        }
    }
    m_namedSoundInstances.clear();
    m_pNamedEffectAudioSystem = pAudioSystem;
}

bool WorldFxSystem::loadNamedEffectLibrary(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &libraryPath,
    const std::string &bindingManifestPath,
    std::string &error)
{
    EffectDefinitionLoader loader(&assetFileSystem);
    const std::optional<std::vector<std::shared_ptr<const EffectDefinition>>> definitions =
        loader.load(libraryPath, error);
    if (!definitions)
    {
        return false;
    }
    EffectLibrary library;
    EffectResourceLibrary resources;
    Engine::ModelAssetCache modelAssets;
    if (!library.replace(*definitions, error) ||
        !resources.load(assetFileSystem, bindingManifestPath, *definitions, error, &modelAssets))
    {
        return false;
    }
    m_namedEffects.clear();
    m_namedEffectLibrary = std::move(library);
    m_namedEffectResources = std::move(resources);
    m_modelAssets = std::move(modelAssets);
    return true;
}

void WorldFxSystem::beginFrame()
{
    m_particleSystem.beginFrame();
}

void WorldFxSystem::updateParticles(float deltaSeconds, bool paused)
{
    m_waterRipples.advance(deltaSeconds, paused);
    beginFrame();
    m_namedEffects.update(deltaSeconds, paused);
    if (!paused)
    {
        m_models.update(deltaSeconds);
    }
    processNamedEffectAudio();

    if (paused)
    {
        return;
    }

    m_particleUpdateAccumulatorSeconds =
        std::min(MaxParticleUpdateAccumulationSeconds, m_particleUpdateAccumulatorSeconds + deltaSeconds);

    while (m_particleUpdateAccumulatorSeconds >= ParticleUpdateStepSeconds)
    {
        m_particleSystem.update(ParticleUpdateStepSeconds);
        m_particleUpdateAccumulatorSeconds -= ParticleUpdateStepSeconds;
    }
}

void WorldFxSystem::processNamedEffectAudio()
{
    const std::vector<EffectSoundEvent> events = m_namedEffects.consumeSoundEvents();
    for (const EffectSoundEvent &event : events)
    {
        const NamedSoundKey key = {.owner = event.owner, .componentId = event.componentId};
        if (event.kind == EffectSoundEventKind::Stop)
        {
            const auto iterator = m_namedSoundInstances.find(key);
            if (iterator != m_namedSoundInstances.end())
            {
                if (m_pNamedEffectAudioSystem != nullptr)
                {
                    m_pNamedEffectAudioSystem->stopSoundInstance(iterator->second);
                }
                m_namedSoundInstances.erase(iterator);
            }
            continue;
        }
        if (event.kind == EffectSoundEventKind::Move)
        {
            const auto iterator = m_namedSoundInstances.find(key);
            if (iterator != m_namedSoundInstances.end() && m_pNamedEffectAudioSystem != nullptr)
            {
                m_pNamedEffectAudioSystem->setSoundInstancePosition(
                    iterator->second,
                    {event.position[0], event.position[1], event.position[2]});
            }
            continue;
        }
        if (m_pNamedEffectAudioSystem == nullptr)
        {
            continue;
        }
        const std::optional<std::string> path = m_namedEffectResources.findAssetPath(event.soundResource);
        if (!path)
        {
            continue;
        }
        const std::optional<GameAudioSystem::WorldPosition> position = event.spatial
            ? std::optional<GameAudioSystem::WorldPosition>({
                event.position[0], event.position[1], event.position[2]})
            : std::nullopt;
        const uint64_t instanceId = m_pNamedEffectAudioSystem->playAssetInstance(
            *path,
            GameAudioSystem::PlaybackGroup::World,
            position,
            event.loop,
            event.volume,
            event.pitch,
            event.innerRadius,
            event.outerRadius);
        if (instanceId != 0)
        {
            m_namedSoundInstances[key] = instanceId;
        }
    }
}

EffectLibrary &WorldFxSystem::namedEffectLibrary()
{
    return m_namedEffectLibrary;
}

const EffectLibrary &WorldFxSystem::namedEffectLibrary() const
{
    return m_namedEffectLibrary;
}

EffectSystem &WorldFxSystem::namedEffects()
{
    return m_namedEffects;
}

const EffectSystem &WorldFxSystem::namedEffects() const
{
    return m_namedEffects;
}

const EffectResourceLibrary &WorldFxSystem::namedEffectResources() const
{
    return m_namedEffectResources;
}

bool WorldFxSystem::setProjectileImpactEffectRebind(
    FxRecipes::ProjectileRecipe recipe,
    const std::string &effectId)
{
    if (recipe == FxRecipes::ProjectileRecipe::None || m_namedEffectLibrary.find(effectId) == nullptr)
    {
        return false;
    }

    m_projectileImpactEffectRebinds[recipe] = effectId;
    return true;
}

bool WorldFxSystem::clearProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe)
{
    return m_projectileImpactEffectRebinds.erase(recipe) != 0;
}

bool WorldFxSystem::hasProjectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe) const
{
    return projectileImpactEffectRebind(recipe) != nullptr;
}

const std::string *WorldFxSystem::projectileImpactEffectRebind(FxRecipes::ProjectileRecipe recipe) const
{
    const std::unordered_map<FxRecipes::ProjectileRecipe, std::string>::const_iterator it =
        m_projectileImpactEffectRebinds.find(recipe);
    return it != m_projectileImpactEffectRebinds.end() ? &it->second : nullptr;
}

Engine::ModelAssetCache &WorldFxSystem::modelAssets()
{
    return m_modelAssets;
}

Engine::ModelInstanceSystem &WorldFxSystem::models()
{
    return m_models;
}

const Engine::ModelInstanceSystem &WorldFxSystem::models() const
{
    return m_models;
}

void WorldFxSystem::syncProjectileFx(GameSession &session, float deltaSeconds, bool refreshSpatialFx)
{
    if (const IGameplayWorldRuntime *pWorld = session.activeWorldRuntime())
    {
        syncActorModelFx(*pWorld, deltaSeconds, refreshSpatialFx);
    }
    updateProjectileTrailCooldowns(deltaSeconds);
    updatePersistentImpactLights(deltaSeconds);
    syncProjectileTrails(session, refreshSpatialFx);
    syncProjectileImpacts(session);
    emitPersistentImpactLights(refreshSpatialFx);
    cleanupSeenProjectileImpactIds(session);
}

void WorldFxSystem::triggerPartySpellFx(const PartySpellCastResult &result)
{
    if (!result.succeeded() || !result.hasSourcePoint)
    {
        return;
    }

    const uint32_t sparkleColorAbgr = partySpellFxColorAbgr(result);
    const size_t affectedCount = result.affectedCharacterIndices.size();
    const size_t sparkleCount = std::max<size_t>(1, affectedCount == 0 ? 1 : affectedCount);

    for (size_t sparkleIndex = 0; sparkleIndex < sparkleCount; ++sparkleIndex)
    {
        const float angleRadians =
            (6.28318530717958647692f * static_cast<float>(sparkleIndex)) / static_cast<float>(sparkleCount);
        const float offsetRadius = sparkleCount > 1 ? PartySpellFxRingRadius : 0.0f;
        const float sparkleX = result.sourceX + std::cos(angleRadians) * offsetRadius;
        const float sparkleY = result.sourceY + std::sin(angleRadians) * offsetRadius;
        const float sparkleZ =
            result.sourceZ + (sparkleCount > 1 ? static_cast<float>(sparkleIndex % 2) * 10.0f : 0.0f);
        const float sparkleRadius = result.effectKind == PartySpellCastEffectKind::PartyRestore ? 30.0f : 24.0f;
        const uint32_t sparkleSeed =
            (result.spellId * 2654435761u) ^ static_cast<uint32_t>(sparkleIndex * 2246822519u);

        if (shouldTriggerPartySpellBuffAura(result.effectKind))
        {
            FxRecipes::spawnActorBuffParticles(
                m_particleSystem,
                result.spellId,
                sparkleSeed,
                sparkleX,
                sparkleY,
                sparkleZ - 44.0f,
                148.0f,
                std::cos(angleRadians),
                std::sin(angleRadians));
        }
        else if (shouldTriggerPartySpellSparkles(result.effectKind))
        {
            FxRecipes::spawnBuffSparkles(
                m_particleSystem,
                sparkleSeed,
                sparkleX,
                sparkleY,
                sparkleZ,
                sparkleRadius,
                sparkleColorAbgr);
        }
    }
}

void WorldFxSystem::setShadowsEnabled(bool enabled)
{
    m_shadowsEnabled = enabled;

    if (!m_shadowsEnabled)
    {
        m_contactShadows.clear();
    }
}

void WorldFxSystem::spawnActorDebuffFx(
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY)
{
    FxRecipes::spawnActorDebuffParticles(
        m_particleSystem,
        spellId,
        seed,
        x,
        y,
        z,
        actorHeight,
        frontDirectionX,
        frontDirectionY);
}

void WorldFxSystem::spawnActorBuffFx(
    uint32_t spellId,
    uint32_t seed,
    float x,
    float y,
    float z,
    float actorHeight,
    float frontDirectionX,
    float frontDirectionY)
{
    FxRecipes::spawnActorBuffParticles(
        m_particleSystem,
        spellId,
        seed,
        x,
        y,
        z,
        actorHeight,
        frontDirectionX,
        frontDirectionY);
}

void WorldFxSystem::clearSpatialFx()
{
    m_glowBillboards.clear();
    m_lightEmitters.clear();
    m_contactShadows.clear();
    m_segmentProjectiles.clear();
}

void WorldFxSystem::addContactShadow(float x, float y, float z, float radius, uint32_t colorAbgr)
{
    if (!m_shadowsEnabled)
    {
        return;
    }

    WorldFxContactShadow shadow = {};
    shadow.x = x;
    shadow.y = y;
    shadow.z = z;
    shadow.radius = radius;
    shadow.colorAbgr = colorAbgr;
    m_contactShadows.push_back(shadow);
}

void WorldFxSystem::addSegmentProjectile(
    float startX,
    float startY,
    float startZ,
    float endX,
    float endY,
    float endZ,
    float width,
    uint32_t colorAbgr)
{
    if (width <= 0.0f)
    {
        return;
    }

    WorldFxSegmentProjectile segment = {};
    segment.startX = startX;
    segment.startY = startY;
    segment.startZ = startZ;
    segment.endX = endX;
    segment.endY = endY;
    segment.endZ = endZ;
    segment.width = width;
    segment.colorAbgr = colorAbgr;
    m_segmentProjectiles.push_back(segment);
}

void WorldFxSystem::addGlowBillboard(
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr,
    bool renderVisibleBillboard)
{
    if (!renderVisibleBillboard)
    {
        return;
    }

    WorldFxGlowBillboard billboard = {};
    billboard.x = x;
    billboard.y = y;
    billboard.z = z;
    billboard.radius = radius;
    billboard.colorAbgr = colorAbgr;
    billboard.renderVisibleBillboard = renderVisibleBillboard;
    m_glowBillboards.push_back(billboard);
}

void WorldFxSystem::addLightEmitter(
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr,
    int16_t sectorId,
    RenderLightKind kind,
    uint32_t stableId,
    bool important)
{
    WorldFxLightEmitter light = {};
    light.x = x;
    light.y = y;
    light.z = z;
    light.radius = radius;
    light.colorAbgr = colorAbgr;
    light.sectorId = sectorId;
    light.kind = kind;
    light.stableId = stableId;
    light.important = important;
    m_lightEmitters.push_back(light);
}

ParticleSystem &WorldFxSystem::particles()
{
    return m_particleSystem;
}

const ParticleSystem &WorldFxSystem::particles() const
{
    return m_particleSystem;
}

const std::vector<WorldFxGlowBillboard> &WorldFxSystem::glowBillboards() const
{
    return m_glowBillboards;
}

const std::vector<WorldFxContactShadow> &WorldFxSystem::contactShadows() const
{
    return m_contactShadows;
}

const std::vector<WorldFxSegmentProjectile> &WorldFxSystem::segmentProjectiles() const
{
    return m_segmentProjectiles;
}

void WorldFxSystem::updateProjectileTrailCooldowns(float deltaSeconds)
{
    for (std::unordered_map<uint32_t, ProjectileFxTrailState>::iterator it = m_projectileTrailStates.begin();
        it != m_projectileTrailStates.end();
        ++it)
    {
        it->second.cooldownSeconds = std::max(0.0f, it->second.cooldownSeconds - deltaSeconds);
    }
}

void WorldFxSystem::updatePersistentImpactLights(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (std::unordered_map<uint32_t, PersistentImpactLight>::iterator it = m_persistentImpactLights.begin();
        it != m_persistentImpactLights.end();)
    {
        it->second.elapsedSeconds += deltaSeconds;

        if (it->second.elapsedSeconds >= it->second.durationSeconds)
        {
            it = m_persistentImpactLights.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

void WorldFxSystem::emitPersistentImpactLights(bool refreshSpatialFx)
{
    if (!refreshSpatialFx)
    {
        return;
    }

    for (const std::pair<const uint32_t, PersistentImpactLight> &entry : m_persistentImpactLights)
    {
        const PersistentImpactLight &light = entry.second;

        if (light.radius <= 0.0f || light.durationSeconds <= 0.0f)
        {
            continue;
        }

        const float fade = std::clamp(1.0f - light.elapsedSeconds / light.durationSeconds, 0.0f, 1.0f);

        if (fade <= 0.0f)
        {
            continue;
        }

        addLightEmitter(
            light.x,
            light.y,
            light.z,
            light.radius,
            withScaledAlpha(light.colorAbgr, fade * ImpactLightIntensityScale),
            light.sectorId,
            RenderLightKind::Impact,
            entry.first);
    }
}

void WorldFxSystem::syncProjectileTrails(GameSession &session, bool refreshSpatialFx)
{
    const ObjectTable &objectTable = session.data().objectTable();
    const std::vector<GameplayProjectilePresentationState> &projectiles =
        session.gameplayFxService().activeProjectilePresentationStates();
    std::unordered_set<uint32_t> activeProjectileIds;
    activeProjectileIds.reserve(projectiles.size());

    for (const GameplayProjectilePresentationState &projectile : projectiles)
    {
        activeProjectileIds.insert(projectile.projectileId);

        if (isSparksSpellProjectile(projectile))
        {
            if (refreshSpatialFx)
            {
                constexpr FxRecipes::ProjectileRecipe recipe = FxRecipes::ProjectileRecipe::Sparks;
                const uint32_t colorAbgr = FxRecipes::projectileRecipeColorAbgr(recipe);
                const float glowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);
                const float projectileCenterZ =
                    projectile.z + FxRecipes::projectileRecipeAnchorOffset(
                        recipe,
                        projectile.radius,
                        projectile.height);

                if (glowRadius > 0.0f)
                {
                    addLightEmitter(
                        projectile.x,
                        projectile.y,
                        projectileCenterZ,
                        glowRadius,
                        makeAbgr(
                            static_cast<uint8_t>(colorAbgr & 0xffu),
                            static_cast<uint8_t>((colorAbgr >> 8) & 0xffu),
                            static_cast<uint8_t>((colorAbgr >> 16) & 0xffu),
                            255),
                        projectile.sectorId,
                        RenderLightKind::Projectile,
                        projectile.projectileId);
                }
            }

            continue;
        }

        const ObjectEntry *pObjectEntry = objectTable.get(projectile.objectDescriptionId);

        if (pObjectEntry == nullptr || isCannonballProjectile(projectile))
        {
            continue;
        }

        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            projectile.spellId,
            projectile.objectName,
            projectile.objectSpriteName,
            pObjectEntry->flags);
        const float projectileCenterZ =
            projectile.z + FxRecipes::projectileRecipeAnchorOffset(
                recipe,
                projectile.radius,
                projectile.height);

        if (projectileRecipeEmitsTrailParticles(projectile.spellId, recipe))
        {
            const float velocityLength = std::sqrt(
                projectile.velocityX * projectile.velocityX
                + projectile.velocityY * projectile.velocityY
                + projectile.velocityZ * projectile.velocityZ);
            float directionX = 0.0f;
            float directionY = 0.0f;
            float directionZ = 1.0f;

            if (velocityLength > 0.001f)
            {
                directionX = projectile.velocityX / velocityLength;
                directionY = projectile.velocityY / velocityLength;
                directionZ = projectile.velocityZ / velocityLength;
            }

            const float backOffset = FxRecipes::projectileRecipeBackOffset(recipe, projectile.radius);
            const float anchoredX = projectile.x - directionX * backOffset;
            const float anchoredY = projectile.y - directionY * backOffset;
            FxRecipes::ProjectileSpawnContext trailContext = {};
            trailContext.projectileId = projectile.projectileId;
            trailContext.objectFlags = pObjectEntry->flags;
            trailContext.radius = projectile.radius;
            trailContext.height = projectile.height;
            trailContext.spellId = projectile.spellId;
            trailContext.objectName = projectile.objectName;
            trailContext.spriteName = projectile.objectSpriteName;
            trailContext.x = anchoredX;
            trailContext.y = anchoredY;
            trailContext.z = projectileCenterZ;
            trailContext.velocityX = projectile.velocityX;
            trailContext.velocityY = projectile.velocityY;
            trailContext.velocityZ = projectile.velocityZ;
            ProjectileFxTrailState &trailState = m_projectileTrailStates[projectile.projectileId];

            if (!projectile.isSettled && trailState.cooldownSeconds <= 0.0f)
            {
                trailState.cooldownSeconds = projectileTrailCooldownSeconds(recipe);
                const FxRecipes::ProjectileFxRecipe &fxRecipe = FxRecipes::projectileFxRecipe(recipe);

                if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::SegmentProjectile)
                {
                    if (trailState.hasPreviousPosition)
                    {
                        addSegmentProjectile(
                            trailState.previousX,
                            trailState.previousY,
                            trailState.previousZ,
                            anchoredX,
                            anchoredY,
                            projectileCenterZ,
                            20.0f * ProjectileFxVisualSizeScale,
                            fxRecipe.colorAbgr);
                    }

                    trailState.previousX = anchoredX;
                    trailState.previousY = anchoredY;
                    trailState.previousZ = projectileCenterZ;
                    trailState.hasPreviousPosition = true;
                }
                else if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::HangingTrail)
                {
                    FxRecipes::ProjectileSegmentSpawnContext segmentContext = {};
                    segmentContext.projectileId = projectile.projectileId;
                    segmentContext.hasPreviousPosition = trailState.hasPreviousPosition;
                    segmentContext.previousX = trailState.previousX;
                    segmentContext.previousY = trailState.previousY;
                    segmentContext.previousZ = trailState.previousZ;
                    segmentContext.currentX = anchoredX;
                    segmentContext.currentY = anchoredY;
                    segmentContext.currentZ = projectileCenterZ;
                    segmentContext.velocityX = projectile.velocityX;
                    segmentContext.velocityY = projectile.velocityY;
                    segmentContext.velocityZ = projectile.velocityZ;
                    FxRecipes::spawnHangingProjectileTrailParticles(m_particleSystem, segmentContext, recipe);
                    trailState.previousX = anchoredX;
                    trailState.previousY = anchoredY;
                    trailState.previousZ = projectileCenterZ;
                    trailState.hasPreviousPosition = true;
                }
                else if (fxRecipe.trailPrimitive == FxRecipes::ProjectileFxPrimitive::Stun)
                {
                    FxRecipes::ProjectileSegmentSpawnContext segmentContext = {};
                    segmentContext.projectileId = projectile.projectileId;
                    segmentContext.hasPreviousPosition = trailState.hasPreviousPosition;
                    segmentContext.previousX = trailState.previousX;
                    segmentContext.previousY = trailState.previousY;
                    segmentContext.previousZ = trailState.previousZ;
                    segmentContext.currentX = anchoredX;
                    segmentContext.currentY = anchoredY;
                    segmentContext.currentZ = projectileCenterZ;
                    segmentContext.velocityX = projectile.velocityX;
                    segmentContext.velocityY = projectile.velocityY;
                    segmentContext.velocityZ = projectile.velocityZ;
                    FxRecipes::spawnStunTrailParticles(m_particleSystem, segmentContext, recipe);
                    trailState.previousX = anchoredX;
                    trailState.previousY = anchoredY;
                    trailState.previousZ = projectileCenterZ;
                    trailState.hasPreviousPosition = true;
                }
                else
                {
                    FxRecipes::spawnProjectileTrailParticles(m_particleSystem, trailContext, recipe);
                }
            }
        }

        const float glowRadius = FxRecipes::projectileRecipeGlowRadius(recipe);

        if (refreshSpatialFx && glowRadius > 0.0f)
        {
            const uint32_t lightColor = FxRecipes::projectileRecipeLightColorAbgr(recipe);
            addLightEmitter(
                projectile.x,
                projectile.y,
                projectileCenterZ,
                glowRadius,
                makeAbgr(
                    static_cast<uint8_t>(lightColor & 0xffu),
                    static_cast<uint8_t>((lightColor >> 8) & 0xffu),
                    static_cast<uint8_t>((lightColor >> 16) & 0xffu),
                    255),
                projectile.sectorId,
                RenderLightKind::Projectile,
                projectile.projectileId);
        }
    }

    for (std::unordered_map<uint32_t, ProjectileFxTrailState>::iterator it = m_projectileTrailStates.begin();
        it != m_projectileTrailStates.end();)
    {
        if (activeProjectileIds.find(it->first) == activeProjectileIds.end())
        {
            it = m_projectileTrailStates.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

void WorldFxSystem::syncProjectileImpacts(GameSession &session)
{
    updateAttachedImpactEffects(session);

    const std::vector<GameplayProjectileImpactPresentationState> &impacts =
        session.gameplayFxService().activeProjectileImpactPresentationStates();

    for (const GameplayProjectileImpactPresentationState &impact : impacts)
    {
        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            impact.sourceSpellId,
            impact.sourceObjectName,
            impact.sourceObjectSpriteName,
            impact.sourceObjectFlags);

        const std::string *pEffectRebind = projectileImpactEffectRebind(recipe);
        if (pEffectRebind == nullptr && !FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe))
        {
            continue;
        }

        const bool isNewImpact = m_seenImpactIds.insert(impact.effectId).second;

        if (isNewImpact)
        {
            if (pEffectRebind != nullptr)
            {
                EffectSpawnParams params;
                params.position = {impact.x, impact.y, impact.z};
                std::optional<std::array<float, 3>> targetPosition;
                if (impact.targetActorIndex != static_cast<size_t>(-1))
                {
                    targetPosition = actorCenterPosition(session, impact.targetActorIndex);
                    if (targetPosition)
                    {
                        params.position = *targetPosition;
                    }
                }
                params.seed = impact.effectId;
                const EffectHandle handle = m_namedEffects.spawn(*pEffectRebind, params);
                if (targetPosition && m_namedEffects.contains(handle))
                {
                    m_attachedImpactEffects.push_back({handle, impact.targetActorIndex, *targetPosition});
                }
            }
            else
            {
                FxRecipes::ImpactSpawnContext impactContext = {};
                impactContext.recipe = recipe;
                impactContext.objectName = impact.objectName;
                impactContext.spriteName = impact.objectSpriteName;
                impactContext.x = impact.x;
                impactContext.y = impact.y;
                impactContext.z = impact.z;
                FxRecipes::spawnImpactParticles(m_particleSystem, impactContext);
            }
        }

        if (pEffectRebind != nullptr)
        {
            continue;
        }

        const float lightRadius = impactLightRadius(recipe);
        const float lightDuration = impactLightDurationSeconds(recipe, impact);

        if (isNewImpact && lightRadius > 0.0f && lightDuration > 0.0f)
        {
            PersistentImpactLight light = {};
            light.x = impact.x;
            light.y = impact.y;
            light.z = impact.z + 16.0f;
            light.radius = lightRadius;
            light.durationSeconds = lightDuration;
            light.colorAbgr = FxRecipes::projectileRecipeImpactColorAbgr(recipe);
            light.sectorId = impact.sectorId;
            m_persistentImpactLights[impact.effectId] = light;
        }
    }
}

void WorldFxSystem::updateAttachedImpactEffects(GameSession &session)
{
    m_attachedImpactEffects.erase(
        std::remove_if(
            m_attachedImpactEffects.begin(),
            m_attachedImpactEffects.end(),
            [&](AttachedImpactEffect &attached)
            {
                if (!m_namedEffects.contains(attached.handle))
                {
                    return true;
                }

                const std::optional<std::array<float, 3>> position =
                    actorCenterPosition(session, attached.actorIndex);
                if (!position)
                {
                    return true;
                }
                if (*position == attached.position)
                {
                    return false;
                }

                attached.position = *position;
                return !m_namedEffects.setTransform(
                    attached.handle,
                    attached.position,
                    {0.0f, 0.0f, 0.0f, 1.0f},
                    1.0f);
            }),
        m_attachedImpactEffects.end());
}

void WorldFxSystem::cleanupSeenProjectileImpactIds(GameSession &session)
{
    std::unordered_set<uint32_t> activeImpactIds;
    const std::vector<GameplayProjectileImpactPresentationState> &impacts =
        session.gameplayFxService().activeProjectileImpactPresentationStates();
    activeImpactIds.reserve(impacts.size());

    for (const GameplayProjectileImpactPresentationState &impact : impacts)
    {
        activeImpactIds.insert(impact.effectId);
    }

    for (std::unordered_set<uint32_t>::iterator it = m_seenImpactIds.begin(); it != m_seenImpactIds.end();)
    {
        if (activeImpactIds.find(*it) == activeImpactIds.end())
        {
            it = m_seenImpactIds.erase(it);
        }
        else
        {
            ++it;
        }
    }
}
}
