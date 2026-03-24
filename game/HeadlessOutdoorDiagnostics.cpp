#include "game/ActorNameResolver.h"
#include "game/HeadlessOutdoorDiagnostics.h"
#include "game/StringUtils.h"

#include "engine/AssetFileSystem.h"
#include "game/EventDialogContent.h"
#include "game/EventRuntime.h"
#include "game/GameDataLoader.h"
#include "game/GameMechanics.h"
#include "game/GenericActorDialog.h"
#include "game/HouseInteraction.h"
#include "game/MasteryTeacherDialog.h"
#include "game/OutdoorMovementController.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/OutdoorGeometryUtils.h"
#include "game/Party.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <limits>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t AdventurersInnHouseId = 185;
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = 10240.0f;

DialogueMenuId dialogueMenuIdForHouseAction(HouseActionId actionId)
{
    switch (actionId)
    {
        case HouseActionId::OpenLearnSkillsMenu:
            return DialogueMenuId::LearnSkills;

        case HouseActionId::OpenShopEquipmentMenu:
            return DialogueMenuId::ShopEquipment;

        case HouseActionId::OpenTavernArcomageMenu:
            return DialogueMenuId::TavernArcomage;

        default:
            return DialogueMenuId::None;
    }
}

const char *actorAiStateName(OutdoorWorldRuntime::ActorAiState state)
{
    switch (state)
    {
        case OutdoorWorldRuntime::ActorAiState::Standing:
            return "standing";
        case OutdoorWorldRuntime::ActorAiState::Wandering:
            return "wandering";
        case OutdoorWorldRuntime::ActorAiState::Pursuing:
            return "pursuing";
        case OutdoorWorldRuntime::ActorAiState::Fleeing:
            return "fleeing";
        case OutdoorWorldRuntime::ActorAiState::Stunned:
            return "stunned";
        case OutdoorWorldRuntime::ActorAiState::Attacking:
            return "attacking";
        case OutdoorWorldRuntime::ActorAiState::Dying:
            return "dying";
        case OutdoorWorldRuntime::ActorAiState::Dead:
            return "dead";
    }

    return "unknown";
}

const char *actorAnimationName(OutdoorWorldRuntime::ActorAnimation animation)
{
    switch (animation)
    {
        case OutdoorWorldRuntime::ActorAnimation::Standing:
            return "standing";
        case OutdoorWorldRuntime::ActorAnimation::Walking:
            return "walking";
        case OutdoorWorldRuntime::ActorAnimation::AttackMelee:
            return "attack_melee";
        case OutdoorWorldRuntime::ActorAnimation::AttackRanged:
            return "attack_ranged";
        case OutdoorWorldRuntime::ActorAnimation::GotHit:
            return "got_hit";
        case OutdoorWorldRuntime::ActorAnimation::Dying:
            return "dying";
        case OutdoorWorldRuntime::ActorAnimation::Dead:
            return "dead";
        case OutdoorWorldRuntime::ActorAnimation::Bored:
            return "bored";
    }

    return "unknown";
}

const char *debugTargetKindName(OutdoorWorldRuntime::DebugTargetKind kind)
{
    switch (kind)
    {
        case OutdoorWorldRuntime::DebugTargetKind::None:
            return "none";
        case OutdoorWorldRuntime::DebugTargetKind::Party:
            return "party";
        case OutdoorWorldRuntime::DebugTargetKind::Actor:
            return "actor";
    }

    return "unknown";
}

const char *monsterAiTypeName(int aiType)
{
    switch (static_cast<MonsterTable::MonsterAiType>(aiType))
    {
        case MonsterTable::MonsterAiType::Suicide:
            return "suicide";
        case MonsterTable::MonsterAiType::Wimp:
            return "wimp";
        case MonsterTable::MonsterAiType::Normal:
            return "normal";
        case MonsterTable::MonsterAiType::Aggressive:
            return "aggressive";
    }

    return "unknown";
}

struct TextureColorStats
{
    size_t opaquePixelCount = 0;
    size_t magentaPixelCount = 0;
    size_t greenPixelCount = 0;
};

struct ActorPreviewAnimationStats
{
    size_t sampleCount = 0;
    size_t greenDominantSampleCount = 0;
    size_t magentaDominantSampleCount = 0;
    size_t missingTextureSampleCount = 0;
    size_t distinctWalkingFrameCount = 0;
};

float normalizeAngleRadians(float angle)
{
    constexpr float Pi = 3.14159265358979323846f;

    while (angle <= -Pi)
    {
        angle += 2.0f * Pi;
    }

    while (angle > Pi)
    {
        angle -= 2.0f * Pi;
    }

    return angle;
}

float angleDistanceRadians(float left, float right)
{
    return std::abs(normalizeAngleRadians(left - right));
}

float hostilityRangeForRelation(int relation)
{
    switch (relation)
    {
        case 1:
            return HostilityCloseRange;
        case 2:
            return HostilityShortRange;
        case 3:
            return HostilityMediumRange;
        case 4:
            return HostilityLongRange;
        default:
            return 0.0f;
    }
}

float hostilePartyAcquisitionRange(
    const MonsterTable &monsterTable,
    const OutdoorWorldRuntime::MapActorState &actor)
{
    if (actor.hostileToParty)
    {
        return HostilityLongRange;
    }

    const int relationToParty = monsterTable.getRelationToParty(actor.monsterId);
    const float relationRange = hostilityRangeForRelation(relationToParty);

    return relationRange > 0.0f ? relationRange : 0.0f;
}

float signedDistanceToOutdoorFace(const OutdoorFaceGeometryData &geometry, const bx::Vec3 &point)
{
    if (!geometry.hasPlane || geometry.vertices.empty())
    {
        return 0.0f;
    }

    const bx::Vec3 delta = {
        point.x - geometry.vertices.front().x,
        point.y - geometry.vertices.front().y,
        point.z - geometry.vertices.front().z
    };
    return geometry.normal.x * delta.x + geometry.normal.y * delta.y + geometry.normal.z * delta.z;
}

TextureColorStats analyzeTextureColors(const std::vector<uint8_t> &pixels)
{
    TextureColorStats stats = {};

    for (size_t offset = 0; offset + 3 < pixels.size(); offset += 4)
    {
        const uint8_t blue = pixels[offset + 0];
        const uint8_t green = pixels[offset + 1];
        const uint8_t red = pixels[offset + 2];
        const uint8_t alpha = pixels[offset + 3];

        if (alpha == 0)
        {
            continue;
        }

        ++stats.opaquePixelCount;

        if (red >= 180 && blue >= 180 && green <= 120)
        {
            ++stats.magentaPixelCount;
        }

        if (green >= 100 && red <= 140 && blue <= 140)
        {
            ++stats.greenPixelCount;
        }
    }

    return stats;
}

const ActorPreviewBillboard *findCompanionActorBillboard(
    const ActorPreviewBillboardSet &billboardSet,
    size_t actorIndex,
    size_t &billboardIndex
)
{
    if (actorIndex >= billboardSet.mapDeltaActorCount || actorIndex >= billboardSet.billboards.size())
    {
        return nullptr;
    }

    billboardIndex = actorIndex;
    const ActorPreviewBillboard &billboard = billboardSet.billboards[billboardIndex];
    return billboard.source == ActorPreviewSource::Companion ? &billboard : nullptr;
}

const OutdoorBitmapTexture *findBillboardTexture(
    const ActorPreviewBillboardSet &billboardSet,
    const std::string &textureName,
    int16_t paletteId
)
{
    std::string normalizedTextureName = textureName;

    std::transform(
        normalizedTextureName.begin(),
        normalizedTextureName.end(),
        normalizedTextureName.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });

    for (const OutdoorBitmapTexture &texture : billboardSet.textures)
    {
        if (texture.textureName == normalizedTextureName && texture.paletteId == paletteId)
        {
            return &texture;
        }
    }

    return nullptr;
}

bool saveTextureAsPng(const OutdoorBitmapTexture &texture, const std::filesystem::path &outputPath)
{
    if (texture.width <= 0 || texture.height <= 0 || texture.pixels.empty())
    {
        return false;
    }

    SDL_Surface *pSurface = SDL_CreateSurfaceFrom(
        texture.width,
        texture.height,
        SDL_PIXELFORMAT_BGRA32,
        const_cast<uint8_t *>(texture.pixels.data()),
        texture.width * 4);

    if (pSurface == nullptr)
    {
        return false;
    }

    const bool saved = SDL_SavePNG(pSurface, outputPath.string().c_str());
    SDL_DestroySurface(pSurface);
    return saved;
}

ActorPreviewAnimationStats analyzeActorPreviewAnimation(
    const ActorPreviewBillboardSet &billboardSet,
    const ActorPreviewBillboard &billboard
)
{
    ActorPreviewAnimationStats stats = {};
    std::vector<std::string> observedWalkingTextureKeys;
    const std::array<OutdoorWorldRuntime::ActorAnimation, 2> actions = {
        OutdoorWorldRuntime::ActorAnimation::Standing,
        OutdoorWorldRuntime::ActorAnimation::Walking
    };

    for (OutdoorWorldRuntime::ActorAnimation action : actions)
    {
        uint16_t spriteFrameIndex = billboard.spriteFrameIndex;
        const uint16_t actionFrameIndex = billboard.actionSpriteFrameIndices[static_cast<size_t>(action)];

        if (actionFrameIndex != 0)
        {
            spriteFrameIndex = actionFrameIndex;
        }

        const SpriteFrameEntry *pBaseFrame = billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, 0);

        if (pBaseFrame == nullptr)
        {
            ++stats.missingTextureSampleCount;
            continue;
        }

        const uint32_t animationLengthTicks =
            pBaseFrame->animationLengthTicks > 0 ? static_cast<uint32_t>(pBaseFrame->animationLengthTicks) : 1u;
        const uint32_t sampleStride = std::max(1u, animationLengthTicks / 4u);

        for (uint32_t sampleTick = 0; sampleTick < animationLengthTicks; sampleTick += sampleStride)
        {
            const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, sampleTick);

            if (pFrame == nullptr)
            {
                ++stats.missingTextureSampleCount;
                continue;
            }

            for (int octant = 0; octant < 8; ++octant)
            {
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                const OutdoorBitmapTexture *pTexture =
                    findBillboardTexture(billboardSet, resolvedTexture.textureName, pFrame->paletteId);
                ++stats.sampleCount;

                if (pTexture == nullptr)
                {
                    ++stats.missingTextureSampleCount;
                    continue;
                }

                const TextureColorStats colorStats = analyzeTextureColors(pTexture->pixels);

                if (colorStats.greenPixelCount > colorStats.magentaPixelCount)
                {
                    ++stats.greenDominantSampleCount;
                }

                if (colorStats.magentaPixelCount > colorStats.greenPixelCount)
                {
                    ++stats.magentaDominantSampleCount;
                }
            }

            if (action == OutdoorWorldRuntime::ActorAnimation::Walking)
            {
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
                const std::string textureKey =
                    resolvedTexture.textureName + "|" + std::to_string(static_cast<int>(pFrame->paletteId));

                if (std::find(
                        observedWalkingTextureKeys.begin(),
                        observedWalkingTextureKeys.end(),
                        textureKey) == observedWalkingTextureKeys.end())
                {
                    observedWalkingTextureKeys.push_back(textureKey);
                }
            }
        }
    }

    stats.distinctWalkingFrameCount = observedWalkingTextureKeys.size();
    return stats;
}

std::string resolveRuntimeActorTextureKey(
    const ActorPreviewBillboardSet &billboardSet,
    const ActorPreviewBillboard &billboard,
    const OutdoorWorldRuntime::MapActorState &actorState,
    float cameraX,
    float cameraY
)
{
    constexpr float Pi = 3.14159265358979323846f;
    uint16_t spriteFrameIndex = billboard.spriteFrameIndex;
    const size_t animationIndex = static_cast<size_t>(actorState.animation);

    if (animationIndex < billboard.actionSpriteFrameIndices.size()
        && billboard.actionSpriteFrameIndices[animationIndex] != 0)
    {
        spriteFrameIndex = billboard.actionSpriteFrameIndices[animationIndex];
    }

    const SpriteFrameEntry *pFrame =
        billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, static_cast<uint32_t>(std::max(0.0f, actorState.animationTimeTicks)));

    if (pFrame == nullptr)
    {
        return {};
    }

    const float angleToCamera = std::atan2(
        static_cast<float>(actorState.x) - cameraX,
        static_cast<float>(actorState.y) - cameraY);
    const float actorYaw = (Pi * 0.5f) - actorState.yawRadians;
    const float octantAngle = actorYaw - angleToCamera + Pi + (Pi / 8.0f);
    const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);

    return resolvedTexture.textureName
        + "|"
        + std::to_string(static_cast<int>(pFrame->paletteId))
        + "|"
        + std::to_string(octant)
        + "|"
        + std::to_string(static_cast<int>(actorState.animation));
}

std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
{
    std::vector<uint32_t> residentNpcIds;

    auto appendNpcId = [&](uint32_t npcId)
    {
        if (std::find(residentNpcIds.begin(), residentNpcIds.end(), npcId) != residentNpcIds.end())
        {
            return;
        }

        const NpcEntry *pResident = npcDialogTable.getNpc(npcId);

        if (pResident == nullptr || pResident->name.empty())
        {
            return;
        }

        if (eventRuntimeState.unavailableNpcIds.contains(npcId))
        {
            return;
        }

        const auto overrideIt = eventRuntimeState.npcHouseOverrides.find(npcId);

        if (overrideIt != eventRuntimeState.npcHouseOverrides.end() && overrideIt->second != houseEntry.id)
        {
            return;
        }

        residentNpcIds.push_back(npcId);
    };

    for (uint32_t npcId : houseEntry.residentNpcIds)
    {
        appendNpcId(npcId);
    }

    for (uint32_t npcId : npcDialogTable.getNpcIdsForHouse(houseEntry.id, &eventRuntimeState.npcHouseOverrides))
    {
        appendNpcId(npcId);
    }

    std::optional<uint32_t> residentNpcId;

    for (uint32_t candidateNpcId : residentNpcIds)
    {
        if (residentNpcId)
        {
            return std::nullopt;
        }

        residentNpcId = candidateNpcId;
    }

    return residentNpcId;
}

void printChestSummary(const OutdoorWorldRuntime::ChestViewState &chestView, const ItemTable &itemTable)
{
    std::cout << "Headless diagnostic: active chest #" << chestView.chestId
              << " type=" << chestView.chestTypeId
              << " flags=0x" << std::hex << chestView.flags << std::dec
              << " entries=" << chestView.items.size()
              << '\n';

    for (size_t itemIndex = 0; itemIndex < chestView.items.size(); ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = chestView.items[itemIndex];
        std::cout << "  [" << itemIndex << "] ";

        if (item.isGold)
        {
            std::cout << "gold=" << item.goldAmount;

            if (item.goldRollCount > 1)
            {
                std::cout << " rolls=" << item.goldRollCount;
            }
        }
        else
        {
            const ItemDefinition *pItemDefinition = itemTable.get(item.itemId);
            std::cout << "item=" << item.itemId;

            if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
            {
                std::cout << " \"" << pItemDefinition->name << "\"";
            }

            std::cout << " quantity=" << item.quantity;
        }

        std::cout << '\n';
    }
}

void printCorpseSummary(const OutdoorWorldRuntime::CorpseViewState &corpseView, const ItemTable &itemTable)
{
    std::cout << "Headless diagnostic: active corpse title=\"" << corpseView.title
              << "\" entries=" << corpseView.items.size()
              << " summoned=" << (corpseView.fromSummonedMonster ? "yes" : "no")
              << '\n';

    for (size_t itemIndex = 0; itemIndex < corpseView.items.size(); ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = corpseView.items[itemIndex];
        std::cout << "  [" << itemIndex << "] ";

        if (item.isGold)
        {
            std::cout << "gold=" << item.goldAmount;
        }
        else
        {
            const ItemDefinition *pItemDefinition = itemTable.get(item.itemId);
            std::cout << "item=" << item.itemId;

            if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
            {
                std::cout << " \"" << pItemDefinition->name << "\"";
            }

            std::cout << " quantity=" << item.quantity;
        }

        std::cout << '\n';
    }
}

void printDialogSummary(const EventDialogContent &dialog)
{
    if (!dialog.isActive)
    {
        std::cout << "Headless diagnostic: no active dialog\n";
        return;
    }

    std::cout << "Headless diagnostic: dialog title=\"" << dialog.title << "\"\n";

    for (size_t lineIndex = 0; lineIndex < dialog.lines.size(); ++lineIndex)
    {
        std::cout << "  dialog[" << lineIndex << "] " << dialog.lines[lineIndex] << '\n';
    }

    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        const EventDialogAction &action = dialog.actions[actionIndex];
        std::cout << "  action[" << actionIndex << "] " << action.label
                  << " kind=" << static_cast<int>(action.kind)
                  << " id=" << action.id
                  << " enabled=" << (action.enabled ? "1" : "0");

        if (!action.disabledReason.empty())
        {
            std::cout << " reason=\"" << action.disabledReason << "\"";
        }

        std::cout << '\n';
    }
}

void promoteSingleResidentHouseContext(
    EventRuntimeState &eventRuntimeState,
    const HouseTable &houseTable,
    const NpcDialogTable &npcDialogTable,
    int currentHour
)
{
    if (!eventRuntimeState.pendingDialogueContext
        || eventRuntimeState.pendingDialogueContext->kind != DialogueContextKind::HouseService)
    {
        return;
    }

    const HouseEntry *pHouseEntry = houseTable.get(eventRuntimeState.pendingDialogueContext->sourceId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
        *pHouseEntry,
        nullptr,
        nullptr,
        currentHour,
        eventRuntimeState.dialogueState.menuStack.empty()
            ? DialogueMenuId::None
            : eventRuntimeState.dialogueState.menuStack.back()
    );
    const std::optional<uint32_t> residentNpcId = singleSelectableResidentNpcId(
        *pHouseEntry,
        npcDialogTable,
        eventRuntimeState
    );

    if (residentNpcId && houseActions.empty())
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = *residentNpcId;
        context.hostHouseId = pHouseEntry->id;
        eventRuntimeState.dialogueState.hostHouseId = pHouseEntry->id;
        eventRuntimeState.pendingDialogueContext = std::move(context);
    }
}

EventDialogContent buildHeadlessDialog(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<EventIrProgram> &globalEventIrProgram,
    const GameDataLoader &gameDataLoader,
    Party *pParty,
    int currentHour
)
{
    promoteSingleResidentHouseContext(
        eventRuntimeState,
        gameDataLoader.getHouseTable(),
        gameDataLoader.getNpcDialogTable(),
        currentHour
    );

    return buildEventDialogContent(
        eventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        &globalEventIrProgram,
        &gameDataLoader.getHouseTable(),
        &gameDataLoader.getClassSkillTable(),
        &gameDataLoader.getNpcDialogTable(),
        pParty,
        currentHour
    );
}

std::optional<size_t> findActionIndexByLabel(const EventDialogContent &dialog, const std::string &label)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label == label)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findActionIndexByLabelPrefix(const EventDialogContent &dialog, const std::string &prefix)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label.rfind(prefix, 0) == 0)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

bool dialogContainsText(const EventDialogContent &dialog, const std::string &fragment)
{
    for (const std::string &line : dialog.lines)
    {
        if (line.find(fragment) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

bool dialogHasActionLabel(const EventDialogContent &dialog, const std::string &label)
{
    return findActionIndexByLabel(dialog, label).has_value();
}

CharacterSkill *ensureCharacterSkill(
    Character &character,
    const std::string &skillName,
    uint32_t level,
    SkillMastery mastery
)
{
    CharacterSkill *pSkill = character.findSkill(skillName);

    if (pSkill == nullptr)
    {
        CharacterSkill skill = {};
        skill.name = canonicalSkillName(skillName);
        skill.level = level;
        skill.mastery = mastery;
        character.skills[skill.name] = skill;
        pSkill = character.findSkill(skillName);
    }

    if (pSkill != nullptr)
    {
        pSkill->level = level;
        pSkill->mastery = mastery;
    }

    return pSkill;
}

struct RegressionScenario
{
    OutdoorWorldRuntime world;
    Party party;
    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = nullptr;
};

EventDialogContent buildScenarioDialog(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t previousMessageCount,
    bool allowNpcFallbackContent
);

bool executeDialogActionInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actionIndex,
    EventDialogContent &dialog
);

bool initializeRegressionScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario
)
{
    scenario.world.initialize(
        selectedMap.map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        selectedMap.outdoorMapData,
        selectedMap.outdoorMapDeltaData,
        selectedMap.eventRuntimeState,
        selectedMap.outdoorActorPreviewBillboardSet,
        selectedMap.outdoorLandMask,
        selectedMap.outdoorDecorationCollisionSet,
        selectedMap.outdoorActorCollisionSet,
        selectedMap.outdoorSpriteObjectCollisionSet
    );

    scenario.party = {};
    scenario.party.setItemTable(&gameDataLoader.getItemTable());
    scenario.party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    scenario.party.reset();
    scenario.pEventRuntimeState = scenario.world.eventRuntimeState();
    return scenario.pEventRuntimeState != nullptr;
}

void applyPendingCombatEventsToScenarioParty(RegressionScenario &scenario)
{
    for (const OutdoorWorldRuntime::CombatEvent &event : scenario.world.pendingCombatEvents())
    {
        if (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
            || event.type == OutdoorWorldRuntime::CombatEvent::Type::PartyProjectileImpact)
        {
            const std::string status = event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
                ? "melee damage"
                : "projectile damage";
            scenario.party.applyDamageToActiveMember(event.damage, status);
        }
    }

    scenario.world.clearPendingCombatEvents();
}

EventDialogContent openNpcDialogInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint32_t npcId
)
{
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcTalk;
    context.sourceId = npcId;
    scenario.pEventRuntimeState->pendingDialogueContext = context;
    return buildScenarioDialog(gameDataLoader, selectedMap, scenario, 0, true);
}

bool openMasteryTeacherOfferInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint32_t npcId,
    const std::string &topicLabel,
    EventDialogContent &dialog
)
{
    dialog = openNpcDialogInScenario(gameDataLoader, selectedMap, scenario, npcId);
    const std::optional<size_t> offerIndex = findActionIndexByLabel(dialog, topicLabel);

    if (!offerIndex)
    {
        return false;
    }

    return executeDialogActionInScenario(gameDataLoader, selectedMap, scenario, *offerIndex, dialog);
}

bool executeLocalEventInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId
)
{
    if (scenario.pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = scenario.eventRuntime.executeEventById(
        selectedMap.localEventIrProgram,
        selectedMap.globalEventIrProgram,
        eventId,
        *scenario.pEventRuntimeState,
        &scenario.party,
        &scenario.world
    );

    if (!executed)
    {
        return false;
    }

    scenario.world.applyEventRuntimeState();
    scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);
    return true;
}

bool executeGlobalEventInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId
)
{
    if (scenario.pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = scenario.eventRuntime.executeEventById(
        std::nullopt,
        selectedMap.globalEventIrProgram,
        eventId,
        *scenario.pEventRuntimeState,
        &scenario.party,
        &scenario.world
    );

    if (!executed)
    {
        return false;
    }

    scenario.world.applyEventRuntimeState();
    scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);
    return true;
}

bool openLocalEventDialogInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId,
    EventDialogContent &dialog
)
{
    if (!executeLocalEventInScenario(gameDataLoader, selectedMap, scenario, eventId))
    {
        return false;
    }

    dialog = buildScenarioDialog(gameDataLoader, selectedMap, scenario, 0, true);
    return dialog.isActive;
}

bool openActorInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actorIndex
)
{
    if (scenario.pEventRuntimeState == nullptr || !selectedMap.outdoorMapDeltaData)
    {
        return false;
    }

    if (actorIndex >= selectedMap.outdoorMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = selectedMap.outdoorMapDeltaData->actors[actorIndex];
    const std::string actorName = resolveMapDeltaActorName(gameDataLoader.getMonsterTable(), actor);

    if (actor.npcId > 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(actor.npcId);
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        return true;
    }

    const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
        selectedMap.map.fileName,
        actorName,
        actor.group,
        *scenario.pEventRuntimeState,
        gameDataLoader.getNpcDialogTable()
    );

    if (!resolution)
    {
        return false;
    }

    const std::optional<std::string> newsText = gameDataLoader.getNpcDialogTable().getNewsText(resolution->newsId);

    if (!newsText)
    {
        return false;
    }

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcNews;
    context.sourceId = resolution->npcId;
    context.newsId = resolution->newsId;
    context.titleOverride = actorName;
    scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    scenario.pEventRuntimeState->messages.push_back(*newsText);
    return true;
}

EventDialogContent buildScenarioDialog(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t previousMessageCount,
    bool allowNpcFallbackContent
)
{
    return buildHeadlessDialog(
        *scenario.pEventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        selectedMap.globalEventIrProgram,
        gameDataLoader,
        &scenario.party,
        scenario.world.currentHour()
    );
}

bool executeDialogActionInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actionIndex,
    EventDialogContent &dialog
)
{
    if (scenario.pEventRuntimeState == nullptr || !dialog.isActive || actionIndex >= dialog.actions.size())
    {
        return false;
    }

    const EventDialogAction &action = dialog.actions[actionIndex];
    const size_t previousMessageCount = scenario.pEventRuntimeState->messages.size();

    if (action.kind == EventDialogActionKind::HouseResident)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = action.id;
        context.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::HouseService)
    {
        const HouseEntry *pHouseEntry = gameDataLoader.getHouseTable().get(dialog.sourceId);

        if (pHouseEntry == nullptr)
        {
            return false;
        }

        const DialogueMenuId menuId = dialogueMenuIdForHouseAction(static_cast<HouseActionId>(action.id));

        if (menuId != DialogueMenuId::None)
        {
            scenario.pEventRuntimeState->dialogueState.menuStack.push_back(menuId);
        }
        else
        {
            std::vector<std::string> messages;
            HouseActionOption option = {};
            option.id = static_cast<HouseActionId>(action.id);
            option.label = action.label;
            option.argument = action.argument;
            performHouseAction(
                option,
                *pHouseEntry,
                scenario.party,
                &gameDataLoader.getClassSkillTable(),
                &scenario.world,
                messages
            );

            for (const std::string &message : messages)
            {
                scenario.pEventRuntimeState->messages.push_back(message);
            }
        }

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::HouseService;
        context.sourceId = dialog.sourceId;
        context.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinOffer)
    {
        const std::optional<NpcDialogTable::RosterJoinOffer> offer =
            gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(action.id);

        if (!offer)
        {
            return false;
        }

        const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(offer->inviteTextId);

        if (inviteText && !inviteText->empty())
        {
            scenario.pEventRuntimeState->messages.push_back(*inviteText);
        }

        EventRuntimeState::DialogueOfferState invite = {};
        invite.kind = DialogueOfferKind::RosterJoin;
        invite.npcId = dialog.sourceId;
        invite.topicId = action.id;
        invite.messageTextId = offer->inviteTextId;
        invite.rosterId = offer->rosterId;
        invite.partyFullTextId = offer->partyFullTextId;
        scenario.pEventRuntimeState->dialogueState.currentOffer = std::move(invite);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = dialog.sourceId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinAccept)
    {
        if (!scenario.pEventRuntimeState->dialogueState.currentOffer
            || scenario.pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::RosterJoin)
        {
            return false;
        }

        const EventRuntimeState::DialogueOfferState invite = *scenario.pEventRuntimeState->dialogueState.currentOffer;
        scenario.pEventRuntimeState->dialogueState.currentOffer.reset();

        if (scenario.party.isFull())
        {
            scenario.pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;
            const std::optional<std::string> fullPartyText =
                gameDataLoader.getNpcDialogTable().getText(invite.partyFullTextId);

            if (fullPartyText && !fullPartyText->empty())
            {
                scenario.pEventRuntimeState->messages.push_back(*fullPartyText);
            }
        }
        else
        {
            const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(invite.rosterId);

            if (pRosterEntry == nullptr || !scenario.party.recruitRosterMember(*pRosterEntry))
            {
                return false;
            }

            scenario.pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
            scenario.pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
            scenario.pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");
        }

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = invite.npcId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinDecline)
    {
        const uint32_t npcId =
            (scenario.pEventRuntimeState->dialogueState.currentOffer
             && scenario.pEventRuntimeState->dialogueState.currentOffer->kind == DialogueOfferKind::RosterJoin)
            ? scenario.pEventRuntimeState->dialogueState.currentOffer->npcId
            : dialog.sourceId;
        scenario.pEventRuntimeState->dialogueState.currentOffer.reset();

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = npcId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
    {
        EventRuntimeState::DialogueOfferState offer = {};
        offer.kind = DialogueOfferKind::MasteryTeacher;
        offer.npcId = dialog.sourceId;
        offer.topicId = action.id;
        scenario.pEventRuntimeState->dialogueState.currentOffer = std::move(offer);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = dialog.sourceId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
    {
        if (!scenario.pEventRuntimeState->dialogueState.currentOffer
            || scenario.pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::MasteryTeacher)
        {
            return false;
        }

        std::string message;

        if (applyMasteryTeacherTopic(
                scenario.pEventRuntimeState->dialogueState.currentOffer->topicId,
                scenario.party,
                gameDataLoader.getClassSkillTable(),
                gameDataLoader.getNpcDialogTable(),
                message))
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = scenario.pEventRuntimeState->dialogueState.currentOffer->npcId;
            context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = scenario.pEventRuntimeState->dialogueState.currentOffer->npcId;
            context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
    }
    else if (action.kind == EventDialogActionKind::NpcTopic)
    {
        bool executed = false;

        if (action.textOnly)
        {
            const std::optional<NpcDialogTable::ResolvedTopic> topic =
                gameDataLoader.getNpcDialogTable().getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

            if (topic && !topic->text.empty())
            {
                scenario.pEventRuntimeState->messages.push_back(topic->text);
                executed = true;
            }
        }
        else
        {
            executed = scenario.eventRuntime.executeEventById(
                std::nullopt,
                selectedMap.globalEventIrProgram,
                static_cast<uint16_t>(action.id),
                *scenario.pEventRuntimeState,
                &scenario.party,
                &scenario.world
            );
        }

        if (!executed)
        {
            return false;
        }

        scenario.world.applyEventRuntimeState();
        scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);

        if (!scenario.pEventRuntimeState->pendingDialogueContext)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
    }
    else
    {
        return false;
    }

    dialog = buildScenarioDialog(
        gameDataLoader,
        selectedMap,
        scenario,
        previousMessageCount,
        action.kind != EventDialogActionKind::RosterJoinAccept
    );
    return true;
}
}

HeadlessOutdoorDiagnostics::HeadlessOutdoorDiagnostics(const Engine::ApplicationConfig &config)
    : m_config(config)
{
}

int HeadlessOutdoorDiagnostics::runProfileFullMapLoad(
    const std::filesystem::path &basePath,
    const std::string &mapFileName
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load base game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not full-load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap)
    {
        std::cerr << "Headless diagnostic failed: selected map missing after full load\n";
        return 1;
    }

    std::cout << "Headless load profile complete: map=\"" << selectedMap->map.name
              << "\" file=" << selectedMap->map.fileName
              << '\n';
    return 0;
}

int HeadlessOutdoorDiagnostics::runSimulateActor(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex,
    int stepCount,
    float deltaSeconds
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    const OutdoorWorldRuntime::MapActorState *pStartActor = outdoorWorldRuntime.mapActorState(actorIndex);

    if (pStartActor == nullptr)
    {
        std::cerr << "Headless diagnostic failed: actor " << actorIndex << " missing\n";
        return 1;
    }

    const int startX = pStartActor->x;
    const int startY = pStartActor->y;
    const int startZ = pStartActor->z;
    const float partyX = static_cast<float>(startX + 6000);
    const float partyY = static_cast<float>(startY);
    const float partyZ = static_cast<float>(startZ);
    bool sawStanding = pStartActor->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
    bool sawWandering = pStartActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
    bool sawWalkingAnimation = pStartActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
    bool sawMovement = false;

    std::cout << "Headless actor simulation: actor=" << actorIndex
              << " start_pos=(" << startX << "," << startY << "," << startZ << ")"
              << " start_ai=" << static_cast<int>(pStartActor->aiState)
              << " start_anim=" << static_cast<int>(pStartActor->animation)
              << '\n';

    for (int step = 0; step < stepCount; ++step)
    {
        outdoorWorldRuntime.updateMapActors(deltaSeconds, partyX, partyY, partyZ);
        const OutdoorWorldRuntime::MapActorState *pActor = outdoorWorldRuntime.mapActorState(actorIndex);

        if (pActor == nullptr)
        {
            std::cerr << "Headless diagnostic failed: actor disappeared during simulation\n";
            return 1;
        }

        sawStanding = sawStanding || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
        sawWandering = sawWandering || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
        sawWalkingAnimation = sawWalkingAnimation || pActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
        sawMovement = sawMovement || pActor->x != startX || pActor->y != startY;
    }

    const OutdoorWorldRuntime::MapActorState *pEndActor = outdoorWorldRuntime.mapActorState(actorIndex);
    std::cout << "Headless actor simulation result: actor=" << actorIndex
              << " end_pos=(" << pEndActor->x << "," << pEndActor->y << "," << pEndActor->z << ")"
              << " end_ai=" << static_cast<int>(pEndActor->aiState)
              << " end_anim=" << static_cast<int>(pEndActor->animation)
              << " saw_standing=" << (sawStanding ? "yes" : "no")
              << " saw_wandering=" << (sawWandering ? "yes" : "no")
              << " saw_walking_anim=" << (sawWalkingAnimation ? "yes" : "no")
              << " saw_movement=" << (sawMovement ? "yes" : "no")
              << '\n';
    return 0;
}

int HeadlessOutdoorDiagnostics::runTraceActorAi(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex,
    int stepCount,
    float deltaSeconds
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    const OutdoorWorldRuntime::MapActorState *pStartActor = outdoorWorldRuntime.mapActorState(actorIndex);

    if (pStartActor == nullptr)
    {
        std::cerr << "Headless diagnostic failed: actor " << actorIndex << " missing\n";
        return 1;
    }

    const float partyX = static_cast<float>(pStartActor->x + 6000);
    const float partyY = static_cast<float>(pStartActor->y);
    const float partyZ = static_cast<float>(pStartActor->z);

    std::cout << "Headless actor AI trace: actor=" << actorIndex
              << " start_pos=(" << pStartActor->x << "," << pStartActor->y << "," << pStartActor->z << ")"
              << " party_pos=(" << partyX << "," << partyY << "," << partyZ << ")"
              << " steps=" << stepCount
              << " delta=" << deltaSeconds
              << '\n';

    for (int step = 0; step < stepCount; ++step)
    {
        const std::optional<OutdoorWorldRuntime::ActorDecisionDebugInfo> before =
            outdoorWorldRuntime.debugActorDecisionInfo(actorIndex, partyX, partyY, partyZ);

        if (!before)
        {
            std::cerr << "Headless diagnostic failed: debug info unavailable before update\n";
            return 1;
        }

        std::cout << "step=" << step
                  << " before"
                  << " ai=" << actorAiStateName(before->aiState) << "(" << static_cast<int>(before->aiState) << ")"
                  << " anim=" << actorAnimationName(before->animation) << "(" << static_cast<int>(before->animation) << ")"
                  << " hostility=" << static_cast<unsigned>(before->hostilityType)
                  << " hostile_party=" << (before->hostileToParty ? "yes" : "no")
                  << " detected_party=" << (before->hasDetectedParty ? "yes" : "no")
                  << " ai_type=" << monsterAiTypeName(before->monsterAiType)
                  << " idle_secs=" << before->idleDecisionSeconds
                  << " action_secs=" << before->actionSeconds
                  << " cooldown=" << before->attackCooldownSeconds
                  << " decisions=(" << before->idleDecisionCount
                  << "," << before->pursueDecisionCount
                  << "," << before->attackDecisionCount << ")"
                  << " target=" << debugTargetKindName(before->targetKind);

        if (before->targetKind == OutdoorWorldRuntime::DebugTargetKind::Actor)
        {
            std::cout << ":" << before->targetActorIndex
                      << " monster=" << before->targetMonsterId;
        }

        std::cout << " relation=" << before->relationToTarget
                  << " target_dist=" << before->targetDistance
                  << " edge=" << before->targetEdgeDistance
                  << " target_sense=" << (before->targetCanSense ? "yes" : "no")
                  << " party_sense=" << (before->canSenseParty ? "yes" : "no")
                  << " party_range=" << before->partySenseRange
                  << " party_dist=" << before->distanceToParty
                  << " promote=" << (before->shouldPromoteHostility ? "yes" : "no")
                  << " promote_range=" << before->promotionRange
                  << " engage=" << (before->shouldEngageTarget ? "yes" : "no")
                  << " flee=" << (before->shouldFlee ? "yes" : "no")
                  << " melee=" << (before->inMeleeRange ? "yes" : "no")
                  << " atk_done=" << (before->attackJustCompleted ? "yes" : "no")
                  << " atk_progress=" << (before->attackInProgress ? "yes" : "no")
                  << " near_party=" << (before->friendlyNearParty ? "yes" : "no")
                  << '\n';

        outdoorWorldRuntime.updateMapActors(deltaSeconds, partyX, partyY, partyZ);

        const OutdoorWorldRuntime::MapActorState *pAfter = outdoorWorldRuntime.mapActorState(actorIndex);

        if (pAfter == nullptr)
        {
            std::cerr << "Headless diagnostic failed: actor disappeared during trace\n";
            return 1;
        }

        std::cout << "step=" << step
                  << " after"
                  << " pos=(" << pAfter->x << "," << pAfter->y << "," << pAfter->z << ")"
                  << " ai=" << actorAiStateName(pAfter->aiState) << "(" << static_cast<int>(pAfter->aiState) << ")"
                  << " anim=" << actorAnimationName(pAfter->animation) << "(" << static_cast<int>(pAfter->animation) << ")"
                  << " hostility=" << static_cast<unsigned>(pAfter->hostilityType)
                  << " detected_party=" << (pAfter->hasDetectedParty ? "yes" : "no")
                  << " decisions=(" << pAfter->idleDecisionCount
                  << "," << pAfter->pursueDecisionCount
                  << "," << pAfter->attackDecisionCount << ")"
                  << '\n';
    }

    return 0;
}

int HeadlessOutdoorDiagnostics::runInspectActorPreview(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not full-load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorActorPreviewBillboardSet)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actor previews\n";
        return 1;
    }

    const ActorPreviewBillboardSet &billboardSet = *selectedMap->outdoorActorPreviewBillboardSet;
    size_t billboardIndex = 0;
    const ActorPreviewBillboard *pBillboard = findCompanionActorBillboard(billboardSet, actorIndex, billboardIndex);

    if (pBillboard == nullptr)
    {
        std::cerr << "Headless diagnostic failed: companion actor billboard " << actorIndex << " missing\n";
        return 1;
    }

    std::cout << "Headless actor preview: actor=" << actorIndex
              << " billboard_index=" << billboardIndex
              << " name=\"" << pBillboard->actorName << "\""
              << '\n';

    const std::array<OutdoorWorldRuntime::ActorAnimation, 2> actions = {
        OutdoorWorldRuntime::ActorAnimation::Standing,
        OutdoorWorldRuntime::ActorAnimation::Walking
    };

    for (OutdoorWorldRuntime::ActorAnimation action : actions)
    {
        uint16_t spriteFrameIndex = pBillboard->spriteFrameIndex;
        const uint16_t actionFrameIndex = pBillboard->actionSpriteFrameIndices[static_cast<size_t>(action)];

        if (actionFrameIndex != 0)
        {
            spriteFrameIndex = actionFrameIndex;
        }

        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, 0);

        if (pFrame == nullptr)
        {
            std::cout << "  action=" << static_cast<int>(action) << " sprite frame missing\n";
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const OutdoorBitmapTexture *pTexture = findBillboardTexture(
            billboardSet,
            resolvedTexture.textureName,
            pFrame->paletteId
        );

        std::cout << "  action=" << static_cast<int>(action)
                  << " sprite_frame=" << spriteFrameIndex
                  << " sprite=\"" << pFrame->spriteName << "\""
                  << " texture=\"" << resolvedTexture.textureName << "\""
                  << " palette=" << pFrame->paletteId
                  << '\n';

        if (pTexture == nullptr)
        {
            std::cout << "    texture not found in loaded billboard textures\n";
            continue;
        }

        const TextureColorStats colorStats = analyzeTextureColors(pTexture->pixels);
        std::cout << "    texture size=" << pTexture->width << "x" << pTexture->height
                  << " opaque_pixels=" << colorStats.opaquePixelCount
                  << " magenta_pixels=" << colorStats.magentaPixelCount
                  << " green_pixels=" << colorStats.greenPixelCount
                  << '\n';
    }

    const ActorPreviewAnimationStats animationStats = analyzeActorPreviewAnimation(billboardSet, *pBillboard);
    std::cout << "  sampled_animation"
              << " samples=" << animationStats.sampleCount
              << " green_dominant=" << animationStats.greenDominantSampleCount
              << " magenta_dominant=" << animationStats.magentaDominantSampleCount
              << " missing=" << animationStats.missingTextureSampleCount
              << " distinct_walking_variants=" << animationStats.distinctWalkingFrameCount
              << '\n';

    return 0;
}

int HeadlessOutdoorDiagnostics::runDumpActorSupport(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem)
        || !gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    if (actorIndex >= selectedMap->outdoorMapDeltaData->actors.size())
    {
        std::cerr << "Headless diagnostic failed: actor index out of range\n";
        return 1;
    }

    const MapDeltaActor &rawActor = selectedMap->outdoorMapDeltaData->actors[actorIndex];
    const float worldX = static_cast<float>(-rawActor.x);
    const float worldY = static_cast<float>(rawActor.y);
    const float worldZ = static_cast<float>(rawActor.z);
    const float terrainHeight = sampleOutdoorTerrainHeight(*selectedMap->outdoorMapData, worldX, worldY);
    const OutdoorSupportFloorSample pointSupport = sampleOutdoorSupportFloor(
        *selectedMap->outdoorMapData,
        worldX,
        worldY,
        worldZ,
        std::numeric_limits<float>::max(),
        5.0f);
    const OutdoorSupportFloorSample radiusSupport = sampleOutdoorSupportFloor(
        *selectedMap->outdoorMapData,
        worldX,
        worldY,
        worldZ,
        std::numeric_limits<float>::max(),
        std::max(5.0f, static_cast<float>(rawActor.radius)));

    std::cout << "Actor support dump: actor=" << actorIndex
              << " name=\"" << rawActor.name << "\""
              << " pos=" << worldX << "," << worldY << "," << worldZ
              << " radius=" << rawActor.radius
              << " height=" << rawActor.height
              << '\n';
    std::cout << "  terrain_height=" << terrainHeight << '\n';
    std::cout << "  point_support=" << pointSupport.height
              << " from_bmodel=" << (pointSupport.fromBModel ? "yes" : "no")
              << " bmodel=" << pointSupport.bModelIndex
              << " face=" << pointSupport.faceIndex
              << '\n';
    std::cout << "  radius_support=" << radiusSupport.height
              << " from_bmodel=" << (radiusSupport.fromBModel ? "yes" : "no")
              << " bmodel=" << radiusSupport.bModelIndex
              << " face=" << radiusSupport.faceIndex
              << '\n';

    size_t printedCount = 0;

    for (size_t bModelIndex = 0; bModelIndex < selectedMap->outdoorMapData->bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = selectedMap->outdoorMapData->bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            OutdoorFaceGeometryData geometry = {};

            if (!buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry)
                || !geometry.isWalkable)
            {
                continue;
            }

            if (worldX < geometry.minX - static_cast<float>(rawActor.radius)
                || worldX > geometry.maxX + static_cast<float>(rawActor.radius)
                || worldY < geometry.minY - static_cast<float>(rawActor.radius)
                || worldY > geometry.maxY + static_cast<float>(rawActor.radius))
            {
                continue;
            }

            const bool insidePoint = isPointInsideOutdoorPolygon(worldX, worldY, geometry.vertices);
            const bool insideRadius = insidePoint;

            if (!insidePoint && !insideRadius)
            {
                continue;
            }

            const float faceHeight = geometry.polygonType == 0x3
                ? geometry.vertices.front().z
                : geometry.vertices.front().z
                    - (geometry.normal.x * (worldX - geometry.vertices.front().x)
                        + geometry.normal.y * (worldY - geometry.vertices.front().y))
                        / geometry.normal.z;

            std::cout << "  candidate[" << printedCount << "]"
                      << " bmodel=" << bModelIndex
                      << " face=" << faceIndex
                      << " poly=" << static_cast<int>(geometry.polygonType)
                      << " attrs=0x" << std::hex << geometry.attributes << std::dec
                      << " height=" << faceHeight
                      << " inside_point=" << (insidePoint ? "yes" : "no")
                      << " inside_radius=" << (insideRadius ? "yes" : "no")
                      << " model=\"" << geometry.modelName << "\""
                      << '\n';

            ++printedCount;

            if (printedCount >= 24)
            {
                return 0;
            }
        }
    }

    return 0;
}

int HeadlessOutdoorDiagnostics::runDumpActorPreviewTexture(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex,
    const std::filesystem::path &outputPath
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.load(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not full-load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorActorPreviewBillboardSet)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actor previews\n";
        return 1;
    }

    const ActorPreviewBillboardSet &billboardSet = *selectedMap->outdoorActorPreviewBillboardSet;
    size_t billboardIndex = 0;
    const ActorPreviewBillboard *pBillboard = findCompanionActorBillboard(billboardSet, actorIndex, billboardIndex);

    if (pBillboard == nullptr)
    {
        std::cerr << "Headless diagnostic failed: companion actor billboard " << actorIndex << " missing\n";
        return 1;
    }

    const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(pBillboard->spriteFrameIndex, 0);

    if (pFrame == nullptr)
    {
        std::cerr << "Headless diagnostic failed: actor preview frame missing\n";
        return 1;
    }

    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
    const OutdoorBitmapTexture *pTexture =
        findBillboardTexture(billboardSet, resolvedTexture.textureName, pFrame->paletteId);

    if (pTexture == nullptr)
    {
        std::cerr << "Headless diagnostic failed: resolved preview texture missing\n";
        return 1;
    }

    if (!saveTextureAsPng(*pTexture, outputPath))
    {
        std::cerr << "Headless diagnostic failed: could not save texture dump to \"" << outputPath.string() << "\"\n";
        return 1;
    }

    const TextureColorStats colorStats = analyzeTextureColors(pTexture->pixels);
    std::cout << "Headless actor preview dump: actor=" << actorIndex
              << " billboard_index=" << billboardIndex
              << " name=\"" << pBillboard->actorName << "\""
              << " sprite=\"" << pFrame->spriteName << "\""
              << " texture=\"" << resolvedTexture.textureName << "\""
              << " palette=" << pFrame->paletteId
              << " output=\"" << outputPath.string() << "\""
              << '\n';
    std::cout << "  size=" << pTexture->width << "x" << pTexture->height
              << " opaque_pixels=" << colorStats.opaquePixelCount
              << " magenta_pixels=" << colorStats.magentaPixelCount
              << " green_pixels=" << colorStats.greenPixelCount
              << '\n';

    return 0;
}

int HeadlessOutdoorDiagnostics::runOpenEvent(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    uint16_t eventId
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    std::cout << "Headless diagnostic: map=" << selectedMap->map.fileName
              << " id=" << selectedMap->map.id
              << " event=" << eventId
              << '\n';

    const bool executed = eventRuntime.executeEventById(
        selectedMap->localEventIrProgram,
        selectedMap->globalEventIrProgram,
        eventId,
        *pEventRuntimeState,
        &party,
        &outdoorWorldRuntime
    );

    if (!executed)
    {
        std::cout << "Headless diagnostic: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();
    party.applyEventRuntimeState(*pEventRuntimeState);

    if (const EventRuntimeState::PendingMapMove *pPendingMapMove = outdoorWorldRuntime.pendingMapMove())
    {
        std::cout << "Headless diagnostic: pending map move=("
                  << pPendingMapMove->x << ","
                  << pPendingMapMove->y << ","
                  << pPendingMapMove->z << ")";

        if (pPendingMapMove->mapName && !pPendingMapMove->mapName->empty())
        {
            std::cout << " name=\"" << *pPendingMapMove->mapName << "\"";
        }

        std::cout << '\n';
    }

    if (pEventRuntimeState->pendingDialogueContext)
    {
        promoteSingleResidentHouseContext(
            *pEventRuntimeState,
            gameDataLoader.getHouseTable(),
            gameDataLoader.getNpcDialogTable(),
            outdoorWorldRuntime.currentHour()
        );

        const EventRuntimeState::PendingDialogueContext &context = *pEventRuntimeState->pendingDialogueContext;

        if (context.kind == DialogueContextKind::HouseService)
        {
            std::cout << "Headless diagnostic: pending house=" << context.sourceId << '\n';
        }
        else if (context.kind == DialogueContextKind::NpcTalk)
        {
            std::cout << "Headless diagnostic: pending npc=" << context.sourceId << '\n';
        }
        else if (context.kind == DialogueContextKind::NpcNews)
        {
            std::cout << "Headless diagnostic: pending news=" << context.newsId << '\n';
        }
    }

    const EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventIrProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );
    printDialogSummary(dialog);

    if (!pEventRuntimeState->grantedItemIds.empty())
    {
        std::cout << "Headless diagnostic: granted items=";

        for (size_t itemIndex = 0; itemIndex < pEventRuntimeState->grantedItemIds.size(); ++itemIndex)
        {
            if (itemIndex > 0)
            {
                std::cout << ',';
            }

            std::cout << pEventRuntimeState->grantedItemIds[itemIndex];
        }

        std::cout << '\n';
    }

    if (!pEventRuntimeState->removedItemIds.empty())
    {
        std::cout << "Headless diagnostic: removed items=";

        for (size_t itemIndex = 0; itemIndex < pEventRuntimeState->removedItemIds.size(); ++itemIndex)
        {
            if (itemIndex > 0)
            {
                std::cout << ',';
            }

            std::cout << pEventRuntimeState->removedItemIds[itemIndex];
        }

        std::cout << '\n';
    }

    if (const OutdoorWorldRuntime::ChestViewState *pActiveChestView = outdoorWorldRuntime.activeChestView())
    {
        printChestSummary(*pActiveChestView, gameDataLoader.getItemTable());
    }
    else
    {
        std::cout << "Headless diagnostic: no active chest view\n";
    }

    if (const OutdoorWorldRuntime::CorpseViewState *pActiveCorpseView = outdoorWorldRuntime.activeCorpseView())
    {
        printCorpseSummary(*pActiveCorpseView, gameDataLoader.getItemTable());
    }
    else
    {
        std::cout << "Headless diagnostic: no active corpse view\n";
    }

    if (!outdoorWorldRuntime.pendingAudioEvents().empty())
    {
        std::cout << "Headless diagnostic: audio events=" << outdoorWorldRuntime.pendingAudioEvents().size() << '\n';

        for (const OutdoorWorldRuntime::AudioEvent &event : outdoorWorldRuntime.pendingAudioEvents())
        {
            std::cout << "  sound=" << event.soundId
                      << " source=" << event.sourceId
                      << " reason=" << event.reason
                      << '\n';
        }
    }

    return 0;
}

int HeadlessOutdoorDiagnostics::runOpenActor(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actors\n";
        return 1;
    }

    if (actorIndex >= selectedMap->outdoorMapDeltaData->actors.size())
    {
        std::cerr << "Headless diagnostic failed: actor index out of range\n";
        return 2;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    const MapDeltaActor &actor = selectedMap->outdoorMapDeltaData->actors[actorIndex];
    const std::string actorName = resolveMapDeltaActorName(gameDataLoader.getMonsterTable(), actor);
    std::cout << "Headless actor diagnostic: index=" << actorIndex
              << " name=\"" << actorName << "\""
              << " npc=" << actor.npcId
              << " monsterInfo=" << actor.monsterInfoId
              << " monsterId=" << actor.monsterId
              << " group=" << actor.group
              << " unique=" << actor.uniqueNameIndex
              << '\n';

    if (const OutdoorWorldRuntime::MapActorState *pActorState = outdoorWorldRuntime.mapActorState(actorIndex))
    {
        std::cout << "  runtime monster=" << pActorState->monsterId
                  << " hp=" << pActorState->currentHp << "/" << pActorState->maxHp
                  << " hostile=" << (pActorState->hostileToParty ? "yes" : "no")
                  << " hostilityType=" << static_cast<unsigned>(pActorState->hostilityType)
                  << '\n';
    }

    if (actor.npcId > 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(actor.npcId);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else
    {
        const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
            selectedMap->map.fileName,
            actorName,
            actor.group,
            *pEventRuntimeState,
            gameDataLoader.getNpcDialogTable()
        );

        std::cout << "  resolved_generic_npc="
                  << (resolution ? std::to_string(resolution->npcId) : "-")
                  << " resolved_news="
                  << (resolution ? std::to_string(resolution->newsId) : "0")
                  << '\n';

        if (resolution)
        {
            const std::optional<std::string> newsText =
                gameDataLoader.getNpcDialogTable().getNewsText(resolution->newsId);

            if (newsText)
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcNews;
                context.sourceId = resolution->npcId;
                context.newsId = resolution->newsId;
                context.titleOverride = actorName;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
                pEventRuntimeState->messages.push_back(*newsText);
            }
        }
    }

    const EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventIrProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );

    if (!dialog.isActive)
    {
        std::cout << "Headless actor diagnostic: no dialog resolved\n";
        return 3;
    }

    printDialogSummary(dialog);
    return 0;
}

int HeadlessOutdoorDiagnostics::runDialogSequence(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    uint16_t eventId,
    const std::vector<size_t> &actionIndices
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->eventRuntimeState
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    const bool executed = eventRuntime.executeEventById(
        selectedMap->localEventIrProgram,
        selectedMap->globalEventIrProgram,
        eventId,
        *pEventRuntimeState,
        &party,
        &outdoorWorldRuntime
    );

    if (!executed)
    {
        std::cerr << "Headless diagnostic failed: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();
    party.applyEventRuntimeState(*pEventRuntimeState);

    EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventIrProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );
    std::cout << "Headless diagnostic: initial dialog after event " << eventId << '\n';
    printDialogSummary(dialog);

    for (size_t sequenceIndex = 0; sequenceIndex < actionIndices.size(); ++sequenceIndex)
    {
        const size_t requestedActionIndex = actionIndices[sequenceIndex];

        if (!dialog.isActive || requestedActionIndex >= dialog.actions.size())
        {
            std::cerr << "Headless diagnostic failed: action index out of range at step " << sequenceIndex << '\n';
            return 3;
        }

        const EventDialogAction &action = dialog.actions[requestedActionIndex];
        const size_t previousMessageCount = pEventRuntimeState->messages.size();

        if (action.kind == EventDialogActionKind::HouseResident)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = action.id;
            context.hostHouseId = dialog.sourceId;
            pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::HouseService)
        {
            const HouseEntry *pHouseEntry = gameDataLoader.getHouseTable().get(dialog.sourceId);

            if (pHouseEntry == nullptr)
            {
                std::cerr << "Headless diagnostic failed: missing house entry for service action\n";
                return 4;
            }

            const DialogueMenuId menuId = dialogueMenuIdForHouseAction(static_cast<HouseActionId>(action.id));

            if (menuId != DialogueMenuId::None)
            {
                pEventRuntimeState->dialogueState.menuStack.push_back(menuId);
            }
            else
            {
                std::vector<std::string> messages;
                HouseActionOption option = {};
                option.id = static_cast<HouseActionId>(action.id);
                option.label = action.label;
                option.argument = action.argument;
                performHouseAction(
                    option,
                    *pHouseEntry,
                    party,
                    &gameDataLoader.getClassSkillTable(),
                    &outdoorWorldRuntime,
                    messages
                );

                for (const std::string &message : messages)
                {
                    pEventRuntimeState->messages.push_back(message);
                }
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = dialog.sourceId;
            pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinOffer)
        {
            const std::optional<NpcDialogTable::RosterJoinOffer> offer =
                gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(action.id);

            if (!offer)
            {
                std::cerr << "Headless diagnostic failed: missing roster join offer data\n";
                return 4;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(offer->inviteTextId);

            if (inviteText && !inviteText->empty())
            {
                pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::DialogueOfferState invite = {};
            invite.kind = DialogueOfferKind::RosterJoin;
            invite.npcId = dialog.sourceId;
            invite.topicId = action.id;
            invite.messageTextId = offer->inviteTextId;
            invite.rosterId = offer->rosterId;
            invite.partyFullTextId = offer->partyFullTextId;
            pEventRuntimeState->dialogueState.currentOffer = std::move(invite);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinAccept)
        {
            if (!pEventRuntimeState->dialogueState.currentOffer
                || pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::RosterJoin)
            {
                std::cerr << "Headless diagnostic failed: no pending roster invite\n";
                return 5;
            }

            const EventRuntimeState::DialogueOfferState invite = *pEventRuntimeState->dialogueState.currentOffer;
            pEventRuntimeState->dialogueState.currentOffer.reset();

            if (party.isFull())
            {
                pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;

                const std::optional<std::string> fullPartyText =
                    gameDataLoader.getNpcDialogTable().getText(invite.partyFullTextId);

                if (fullPartyText && !fullPartyText->empty())
                {
                    pEventRuntimeState->messages.push_back(*fullPartyText);
                }
            }
            else
            {
                const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(invite.rosterId);

                if (pRosterEntry == nullptr || !party.recruitRosterMember(*pRosterEntry))
                {
                    std::cerr << "Headless diagnostic failed: recruitment failed\n";
                    return 6;
                }

                pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
                pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
                pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = invite.npcId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinDecline)
        {
            const uint32_t npcId =
                (pEventRuntimeState->dialogueState.currentOffer
                 && pEventRuntimeState->dialogueState.currentOffer->kind == DialogueOfferKind::RosterJoin)
                ? pEventRuntimeState->dialogueState.currentOffer->npcId
                : dialog.sourceId;
            pEventRuntimeState->dialogueState.currentOffer.reset();

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = npcId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
        {
            EventRuntimeState::DialogueOfferState offer = {};
            offer.kind = DialogueOfferKind::MasteryTeacher;
            offer.npcId = dialog.sourceId;
            offer.topicId = action.id;
            pEventRuntimeState->dialogueState.currentOffer = std::move(offer);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
        {
            if (!pEventRuntimeState->dialogueState.currentOffer
                || pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::MasteryTeacher)
            {
                std::cerr << "Headless diagnostic failed: no pending mastery teacher offer\n";
                return 7;
            }

            std::string message;

            if (applyMasteryTeacherTopic(
                    pEventRuntimeState->dialogueState.currentOffer->topicId,
                    party,
                    gameDataLoader.getClassSkillTable(),
                    gameDataLoader.getNpcDialogTable(),
                    message))
            {
                if (!message.empty())
                {
                    pEventRuntimeState->messages.push_back(message);
                }

                pEventRuntimeState->dialogueState.currentOffer.reset();
            }
        }
        else if (action.kind == EventDialogActionKind::NpcTopic)
        {
            bool topicExecuted = false;

            if (action.textOnly)
            {
                const std::optional<NpcDialogTable::ResolvedTopic> topic =
                    gameDataLoader.getNpcDialogTable().getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

                if (topic && !topic->text.empty())
                {
                    pEventRuntimeState->messages.push_back(topic->text);
                    topicExecuted = true;
                }
            }
            else
            {
                topicExecuted = eventRuntime.executeEventById(
                    std::nullopt,
                    selectedMap->globalEventIrProgram,
                    static_cast<uint16_t>(action.id),
                    *pEventRuntimeState,
                    &party,
                    &outdoorWorldRuntime
                );
            }

            if (!topicExecuted)
            {
                std::cerr << "Headless diagnostic failed: topic event " << action.id << " unresolved\n";
                return 8;
            }

            outdoorWorldRuntime.applyEventRuntimeState();
            party.applyEventRuntimeState(*pEventRuntimeState);

            if (!pEventRuntimeState->pendingDialogueContext)
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcTalk;
                context.sourceId = dialog.sourceId;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
            }
        }
        else
        {
            std::cerr << "Headless diagnostic failed: unsupported action kind in sequence\n";
            return 9;
        }

        dialog = buildHeadlessDialog(
            *pEventRuntimeState,
            previousMessageCount,
            action.kind != EventDialogActionKind::RosterJoinAccept
                && action.kind != EventDialogActionKind::MasteryTeacherLearn,
            selectedMap->globalEventIrProgram,
            gameDataLoader,
            &party,
            outdoorWorldRuntime.currentHour()
        );
        std::cout << "Headless diagnostic: dialog after action[" << requestedActionIndex
                  << "] step " << sequenceIndex << '\n';
        printDialogSummary(dialog);
    }

    std::cout << "Headless diagnostic: party members=" << party.members().size() << '\n';
    for (const Character &member : party.members())
    {
        std::cout << "  party \"" << member.name << "\" role=\"" << member.role << "\" level=" << member.level << '\n';
    }

    return 0;
}

int HeadlessOutdoorDiagnostics::runRegressionSuite(
    const std::filesystem::path &basePath,
    const std::string &suiteName
) const
{
    if (suiteName != "dialogue")
    {
        std::cerr << "Unknown regression suite: " << suiteName << '\n';
        return 2;
    }

    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot))
    {
        std::cerr << "Regression suite failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Regression suite failed: could not load game data\n";
        return 1;
    }

    const std::string mapFileName = "out01.odm";
    const std::optional<MapAssetInfo> &initialSelectedMap = gameDataLoader.getSelectedMap();
    const bool alreadyLoadedTargetMap =
        initialSelectedMap
        && toLowerCopy(std::filesystem::path(initialSelectedMap->map.fileName).filename().string()) == mapFileName;

    if (!alreadyLoadedTargetMap && !gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Regression suite failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Regression suite failed: selected map is not an outdoor map\n";
        return 1;
    }

    int passedCount = 0;
    int failedCount = 0;

    auto runCase =
        [&](const std::string &caseName, auto &&fn)
        {
            std::string failure;
            const bool passed = fn(failure);
            std::cout << "["
                      << (passed ? "PASS" : "FAIL")
                      << "] "
                      << caseName;

            if (!passed && !failure.empty())
            {
                std::cout << " - " << failure;
            }

            std::cout << '\n';

            if (passed)
            {
                ++passedCount;
            }
            else
            {
                ++failedCount;
            }
        };

    runCase(
        "local_event_457_spawns_runtime_fireball_and_cannonball_projectiles",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 457))
            {
                failure = "event 457 did not execute";
                return false;
            }

            if (scenario.world.projectileCount() < 2)
            {
                failure = "event 457 did not spawn both runtime projectiles";
                return false;
            }

            bool sawFireball = false;
            bool sawCannonball = false;

            for (size_t projectileIndex = 0; projectileIndex < scenario.world.projectileCount(); ++projectileIndex)
            {
                const OutdoorWorldRuntime::ProjectileState *pProjectile = scenario.world.projectileState(projectileIndex);

                if (pProjectile == nullptr)
                {
                    failure = "projectile state missing";
                    return false;
                }

                sawFireball = sawFireball || pProjectile->spellId == 6 || pProjectile->objectName == "Fireball";
                sawCannonball = sawCannonball || pProjectile->spellId == 136 || pProjectile->objectName == "Cannonball";
            }

            if (!sawFireball || !sawCannonball)
            {
                failure = !sawFireball ? "fireball projectile missing" : "cannonball projectile missing";
                return false;
            }

            bool sawImpact = false;

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, 0.0f, 0.0f, 0.0f);

                if (scenario.world.projectileImpactCount() > 0)
                {
                    sawImpact = true;
                    break;
                }
            }

            if (!sawImpact)
            {
                failure = "event 457 projectiles never produced an impact";
                return false;
            }

            return true;
        }
    );

    runCase(
        "event_meteor_shower_ground_impact_damages_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const float partyX = -9216.0f;
            const float partyY = -12848.0f;
            const float partyZ = 110.0f;
            const int initialHealth = scenario.party.totalHealth();

            if (!scenario.world.castEventSpell(
                    9,
                    10,
                    static_cast<uint32_t>(SkillMastery::Master),
                    19872,
                    -19824,
                    5084,
                    static_cast<int32_t>(-partyX),
                    static_cast<int32_t>(partyY),
                    static_cast<int32_t>(partyZ)))
            {
                failure = "meteor shower cast failed";
                return false;
            }

            bool sawImpact = false;

            for (int step = 0; step < 8192; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                sawImpact = sawImpact || scenario.world.projectileImpactCount() > 0;
                applyPendingCombatEventsToScenarioParty(scenario);

                if (scenario.party.totalHealth() < initialHealth)
                {
                    return true;
                }
            }

            failure = !sawImpact ? "meteor shower never impacted" : "meteor shower impact never damaged party";
            return false;
        }
    );

    runCase(
        "dwi_world_actor_runtime_state",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pPeasant = scenario.world.mapActorState(5);
            const OutdoorWorldRuntime::MapActorState *pSergeant = scenario.world.mapActorState(53);

            if (pPeasant == nullptr || pSergeant == nullptr)
            {
                failure = "expected DWI actor runtime state is missing";
                return false;
            }

            if (pPeasant->monsterId != 1 || pPeasant->maxHp != 13 || pPeasant->hostileToParty)
            {
                failure = "unexpected peasant runtime state";
                return false;
            }

            if (pSergeant->monsterId != 5 || pSergeant->maxHp != 21 || pSergeant->hostileToParty)
            {
                failure = "unexpected sergeant runtime state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_peasant_actor_5_does_not_flee_on_start",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(5);

            if (pBefore == nullptr)
            {
                failure = "actor 5 missing";
                return false;
            }

            if (pBefore->hostilityType != 0)
            {
                failure = "actor 5 did not start friendly to nearby actors";
                return false;
            }

            for (int step = 0; step < 8; ++step)
            {
                scenario.world.updateMapActors(
                    0.125f,
                    pBefore->preciseX + 20000.0f,
                    pBefore->preciseY + 20000.0f,
                    pBefore->preciseZ);
                const OutdoorWorldRuntime::MapActorState *pStep = scenario.world.mapActorState(5);

                if (pStep == nullptr)
                {
                    failure = "actor 5 disappeared during startup simulation";
                    return false;
                }

                if (pStep->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
                {
                    failure = "actor 5 entered fleeing state on map start";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "monster_attack_style_classification_examples",
        [&](std::string &failure)
        {
            const MonsterTable::MonsterStatsEntry *pMelee =
                gameDataLoader.getMonsterTable().findStatsById(12);
            const MonsterTable::MonsterStatsEntry *pMixed =
                gameDataLoader.getMonsterTable().findStatsById(5);
            const MonsterTable::MonsterStatsEntry *pRanged =
                gameDataLoader.getMonsterTable().findStatsById(16);

            if (pMelee == nullptr || pMixed == nullptr || pRanged == nullptr)
            {
                failure = "classification sample stats missing";
                return false;
            }

            if (pMelee->attackStyle != MonsterTable::MonsterAttackStyle::MeleeOnly)
            {
                failure = "monster 12 should classify as melee-only";
                return false;
            }

            if (pMixed->attackStyle != MonsterTable::MonsterAttackStyle::MixedMeleeRanged)
            {
                failure = "monster 5 should classify as mixed melee+ranged";
                return false;
            }

            if (pRanged->attackStyle != MonsterTable::MonsterAttackStyle::Ranged)
            {
                failure = "monster 16 should classify as ranged";
                return false;
            }

            return true;
        }
    );

    runCase(
        "non_flying_actor_snaps_to_terrain",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map has no outdoor terrain";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            for (size_t actorIndex : {size_t(5), size_t(8)})
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr)
                {
                    failure = "expected grounded actor is missing";
                    return false;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats == nullptr)
                {
                    failure = "grounded actor stats missing";
                    return false;
                }

                if (pStats->canFly)
                {
                    failure = "grounded actor unexpectedly flies";
                    return false;
                }

                const int terrainZ = static_cast<int>(std::lround(sampleOutdoorSupportFloorHeight(
                    *selectedMap->outdoorMapData,
                    static_cast<float>(pActor->x),
                    static_cast<float>(pActor->y),
                    static_cast<float>(pActor->z))));

                if (pActor->z != terrainZ)
                {
                    failure = "non-flying actor is not grounded to terrain";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "dwi_world_spawn_runtime_state",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            bool foundFriendlyEncounterSpawn = false;
            bool foundHostileEncounterSpawn = false;

            for (size_t spawnIndex = 0; spawnIndex < scenario.world.spawnPointCount(); ++spawnIndex)
            {
                const OutdoorWorldRuntime::SpawnPointState *pSpawnState = scenario.world.spawnPointState(spawnIndex);

                if (pSpawnState == nullptr || pSpawnState->typeId != 3 || pSpawnState->encounterSlot == 0)
                {
                    continue;
                }

                if (pSpawnState->encounterSlot == 1 && !pSpawnState->hostileToParty)
                {
                    foundFriendlyEncounterSpawn = true;
                }

                if (pSpawnState->encounterSlot == 2 && pSpawnState->hostileToParty)
                {
                    foundHostileEncounterSpawn = true;
                }
            }

            if (!foundFriendlyEncounterSpawn)
            {
                failure = "missing friendly encounter spawn state";
                return false;
            }

            if (!foundHostileEncounterSpawn)
            {
                failure = "missing hostile encounter spawn state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "spawn_points_materialize_on_first_outdoor_load",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor actor data";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = selectedMap->outdoorMapDeltaData->actors.size();

            if (scenario.world.mapActorCount() <= baseActorCount)
            {
                failure = "spawn points did not materialize on first outdoor load";
                return false;
            }

            bool sawSpawnPointActor = false;

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr)
                {
                    failure = "spawned actor state missing";
                    return false;
                }

                if (!pActor->spawnedAtRuntime || !pActor->fromSpawnPoint)
                {
                    failure = "first-load spawned actor metadata mismatch";
                    return false;
                }

                if (scenario.world.spawnPointState(pActor->spawnPointIndex) == nullptr)
                {
                    failure = "spawned actor does not reference a valid spawn point";
                    return false;
                }

                sawSpawnPointActor = true;
            }

            if (!sawSpawnPointActor)
            {
                failure = "no spawn point actors materialized on first outdoor load";
                return false;
            }

            return true;
        }
    );

    runCase(
        "spawn_points_remain_metadata_after_first_visit",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = selectedMap->outdoorMapDeltaData->actors.size();

            if (scenario.world.mapActorCount() != baseActorCount)
            {
                failure = "spawn points should remain metadata after first visit";
                return false;
            }

            size_t chosenSpawnIndex = static_cast<size_t>(-1);
            const OutdoorWorldRuntime::SpawnPointState *pChosenSpawn = nullptr;

            for (size_t spawnIndex = 0; spawnIndex < scenario.world.spawnPointCount(); ++spawnIndex)
            {
                const OutdoorWorldRuntime::SpawnPointState *pSpawn = scenario.world.spawnPointState(spawnIndex);

                if (pSpawn != nullptr
                    && pSpawn->typeId == 3
                    && pSpawn->encounterSlot > 0
                    && pSpawn->maxCount > 0)
                {
                    chosenSpawnIndex = spawnIndex;
                    pChosenSpawn = pSpawn;
                    break;
                }
            }

            if (pChosenSpawn == nullptr)
            {
                failure = "no executable monster spawn point found";
                return false;
            }

            if (!scenario.world.debugSpawnEncounterFromSpawnPoint(chosenSpawnIndex))
            {
                failure = "could not execute spawn point encounter";
                return false;
            }

            const size_t spawnedCount = scenario.world.mapActorCount() - baseActorCount;

            if (spawnedCount < static_cast<size_t>(std::max(0, pChosenSpawn->minCount))
                || spawnedCount > static_cast<size_t>(std::max(0, pChosenSpawn->maxCount)))
            {
                failure = "spawn point execution ignored configured min/max count";
                return false;
            }

            bool sawDifferentPosition = spawnedCount <= 1;

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr)
                {
                    failure = "spawned actor state missing";
                    return false;
                }

                if (!pActor->spawnedAtRuntime || !pActor->fromSpawnPoint || pActor->spawnPointIndex != chosenSpawnIndex)
                {
                    failure = "spawned actor metadata mismatch";
                    return false;
                }

                if (actorIndex > baseActorCount)
                {
                    const OutdoorWorldRuntime::MapActorState *pFirstSpawnedActor =
                        scenario.world.mapActorState(baseActorCount);

                    if (pFirstSpawnedActor != nullptr
                        && (pActor->x != pFirstSpawnedActor->x || pActor->y != pFirstSpawnedActor->y))
                    {
                        sawDifferentPosition = true;
                    }
                }
            }

            if (!sawDifferentPosition)
            {
                failure = "multi-spawn encounter did not spread actor positions";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_actor_action_sprites_present_in_monster_data",
        [&](std::string &failure)
        {
            const MonsterEntry *pMonster = gameDataLoader.getMonsterTable().findById(5);

            if (pMonster == nullptr)
            {
                failure = "monster id 5 missing";
                return false;
            }

            if (pMonster->spriteNames[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Standing)].empty())
            {
                failure = "standing sprite missing";
                return false;
            }

            if (pMonster->spriteNames[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Walking)].empty())
            {
                failure = "walking sprite missing";
                return false;
            }

            if (pMonster->spriteNames[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::AttackRanged)].empty())
            {
                failure = "ranged attack sprite missing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_does_not_engage_party",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            scenario.world.updateMapActors(3.0f, static_cast<float>(startX + 512), static_cast<float>(startY), pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "actor 53 missing after update";
                return false;
            }

            if (pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                || pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                || pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
            {
                failure = "friendly actor should not engage the party";
                return false;
            }

            if (pAfter->hasDetectedParty)
            {
                failure = "friendly actor incorrectly detected the party as hostile";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_can_idle_wander",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            bool sawWandering = false;
            bool sawWalkingAnimation = false;

            for (int step = 0; step < 180; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(startX + 6000),
                    static_cast<float>(startY),
                    static_cast<float>(pBefore->z));

                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(53);

                if (pStepActor != nullptr)
                {
                    sawWandering = sawWandering || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
                    sawWalkingAnimation = sawWalkingAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
                }
            }
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "actor 53 missing after update";
                return false;
            }

            if (pAfter->x == startX && pAfter->y == startY)
            {
                failure = "friendly actor did not idle-wander";
                return false;
            }

            if (!sawWandering)
            {
                failure = "friendly actor did not enter wandering state";
                return false;
            }

            if (!sawWalkingAnimation)
            {
                failure = "friendly actor did not enter walking animation";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_cycles_idle_and_walk",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            bool sawStanding = pBefore->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
            bool sawWandering = pBefore->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
            bool sawWalkingAnimation = pBefore->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
            bool sawBoredAnimation = pBefore->animation == OutdoorWorldRuntime::ActorAnimation::Bored;

            for (int step = 0; step < 360; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(startX + 6000),
                    static_cast<float>(startY),
                    static_cast<float>(pBefore->z));

                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(3);

                if (pStepActor != nullptr)
                {
                    sawStanding = sawStanding
                        || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
                    sawWandering = sawWandering
                        || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
                    sawWalkingAnimation = sawWalkingAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
                    sawBoredAnimation = sawBoredAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Bored;
                }
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after update";
                return false;
            }

            if (pAfter->x == startX && pAfter->y == startY)
            {
                failure = "actor 3 did not move";
                return false;
            }

            if (!sawStanding || !sawWandering || !sawWalkingAnimation)
            {
                failure = "actor 3 did not cycle through idle/walk states";
                return false;
            }

            if (sawBoredAnimation)
            {
                failure = "actor 3 unexpectedly entered bored animation during ordinary idle wander";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_accumulates_motion_under_tiny_deltas",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            const float partyX = static_cast<float>(startX + 6000);
            const float partyY = static_cast<float>(startY);
            const float partyZ = static_cast<float>(pBefore->z);
            bool sawWandering = false;
            bool sawWalkingAnimation = false;

            for (int step = 0; step < 5000; ++step)
            {
                scenario.world.updateMapActors(0.0005f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(3);

                if (pStepActor != nullptr)
                {
                    sawWandering = sawWandering
                        || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
                    sawWalkingAnimation = sawWalkingAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
                }
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after tiny-delta simulation";
                return false;
            }

            if (pAfter->x == startX && pAfter->y == startY)
            {
                failure = "actor 3 did not accumulate movement under tiny deltas";
                return false;
            }

            if (!sawWandering || !sawWalkingAnimation)
            {
                failure = "actor 3 did not enter wandering/walking under tiny deltas";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actor_3_runtime_preview_changes_while_wandering",
        [&](std::string &failure)
        {
            GameDataLoader fullMapLoader;

            if (!fullMapLoader.load(assetFileSystem)
                || !fullMapLoader.loadMapByFileName(assetFileSystem, mapFileName))
            {
                failure = "could not load full map assets for actor preview regression";
                return false;
            }

            const std::optional<MapAssetInfo> &fullSelectedMap = fullMapLoader.getSelectedMap();

            if (!fullSelectedMap || !fullSelectedMap->outdoorActorPreviewBillboardSet)
            {
                failure = "selected map missing actor previews";
                return false;
            }

            size_t billboardIndex = 0;
            const ActorPreviewBillboard *pBillboard =
                findCompanionActorBillboard(*fullSelectedMap->outdoorActorPreviewBillboardSet, 3, billboardIndex);

            if (pBillboard == nullptr)
            {
                failure = "actor 3 billboard missing";
                return false;
            }

            RegressionScenario scenario = {};

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const float cameraX = static_cast<float>(pBefore->x + 2048);
            const float cameraY = static_cast<float>(pBefore->y + 2048);
            std::vector<std::string> observedTextureKeys;

            for (int step = 0; step < 360; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(pBefore->x + 6000),
                    static_cast<float>(pBefore->y),
                    static_cast<float>(pBefore->z));

                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(3);

                if (pStepActor == nullptr)
                {
                    failure = "actor 3 vanished during runtime preview test";
                    return false;
                }

                const std::string textureKey = resolveRuntimeActorTextureKey(
                    *fullSelectedMap->outdoorActorPreviewBillboardSet,
                    *pBillboard,
                    *pStepActor,
                    cameraX,
                    cameraY);

                if (!textureKey.empty()
                    && std::find(observedTextureKeys.begin(), observedTextureKeys.end(), textureKey)
                        == observedTextureKeys.end())
                {
                    observedTextureKeys.push_back(textureKey);
                }
            }

            if (observedTextureKeys.size() < 2)
            {
                failure = "actor 3 runtime preview never changed texture/frame selection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actor_51_stays_on_ship_support",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            if (selectedMap->outdoorMapDeltaData->actors.size() <= 51)
            {
                failure = "actor 51 missing from map delta";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const MapDeltaActor &rawActor = selectedMap->outdoorMapDeltaData->actors[51];
            const float worldX = static_cast<float>(-rawActor.x);
            const float worldY = static_cast<float>(rawActor.y);
            const float terrainHeight = sampleOutdoorTerrainHeight(*selectedMap->outdoorMapData, worldX, worldY);
            const float placementHeight = sampleOutdoorPlacementFloorHeight(
                *selectedMap->outdoorMapData,
                worldX,
                worldY,
                static_cast<float>(rawActor.z));
            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(51);

            if (pActor == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            if (placementHeight <= terrainHeight + 32.0f)
            {
                failure = "actor 51 support floor was not above terrain";
                return false;
            }

            if (std::fabs(static_cast<float>(pActor->z) - placementHeight) > 2.0f)
            {
                failure = "actor 51 runtime z does not match resolved support floor";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actor_51_movement_preserves_ship_floor",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(51);

            if (pBefore == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            const float startZ = pBefore->preciseZ;

            for (int step = 0; step < 300; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(pBefore->x + 20000),
                    static_cast<float>(pBefore->y + 20000),
                    static_cast<float>(pBefore->z));
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(51);

            if (pAfter == nullptr)
            {
                failure = "actor 51 missing after update";
                return false;
            }

            if (std::fabs(pAfter->preciseZ - startZ) > 2.0f)
            {
                failure = "actor 51 fell off ship support while moving";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_stands_and_faces_party_on_contact",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const float partyX = static_cast<float>(pBefore->x + 32);
            const float partyY = static_cast<float>(pBefore->y + 24);
            const float partyZ = static_cast<float>(pBefore->z);
            scenario.world.updateMapActors(0.25f, static_cast<float>(pBefore->x + 20000), static_cast<float>(pBefore->y + 20000), partyZ);
            scenario.world.notifyPartyContactWithMapActor(3, partyX, partyY, partyZ);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after update";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Standing)
            {
                failure = "actor 3 did not stand on party contact";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::Standing)
            {
                failure = "actor 3 did not use standing animation on party contact";
                return false;
            }

            if (std::abs(pAfter->velocityX) > 0.01f || std::abs(pAfter->velocityY) > 0.01f)
            {
                failure = "actor 3 kept moving on party contact";
                return false;
            }

            const float expectedYaw = std::atan2(partyY - pAfter->preciseY, partyX - pAfter->preciseX);

            if (angleDistanceRadians(pAfter->yawRadians, expectedYaw) > 0.35f)
            {
                failure = "actor 3 did not face the party on contact";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_stops_wandering_when_party_is_near",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const float partyX = pBefore->preciseX + 70.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            scenario.world.updateMapActors(0.25f, partyX, partyY, partyZ);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after update";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Standing)
            {
                failure = "actor 3 did not stand when party was near";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::Standing)
            {
                failure = "actor 3 did not use standing animation when party was near";
                return false;
            }

            if (std::abs(pAfter->velocityX) > 0.01f || std::abs(pAfter->velocityY) > 0.01f)
            {
                failure = "actor 3 kept moving when party was near";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_causes_damage_and_hostility",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const int beforeHp = pBefore->currentHp;

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    2,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after attack";
                return false;
            }

            if (!pAfter->hostileToParty)
            {
                failure = "actor 3 did not become hostile";
                return false;
            }

            if (pAfter->currentHp != std::max(0, beforeHp - 2))
            {
                failure = "actor 3 did not take the expected damage";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_stunned_hit_reaction_does_not_restart_on_second_hit",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData || selectedMap->outdoorMapDeltaData->actors.size() <= 53)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            modifiedMap.outdoorMapDeltaData->actors[3].monsterInfoId =
                selectedMap->outdoorMapDeltaData->actors[53].monsterInfoId;
            modifiedMap.outdoorMapDeltaData->actors[3].monsterId =
                selectedMap->outdoorMapDeltaData->actors[53].monsterId;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "first party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfterFirstHit = scenario.world.mapActorState(3);

            if (pAfterFirstHit == nullptr)
            {
                failure = "actor 3 missing after first hit";
                return false;
            }

            if (pAfterFirstHit->aiState != OutdoorWorldRuntime::ActorAiState::Stunned
                || pAfterFirstHit->animation != OutdoorWorldRuntime::ActorAnimation::GotHit)
            {
                failure = "actor 3 did not enter stunned hit reaction";
                return false;
            }

            scenario.world.updateMapActors(
                1.0f / 128.0f,
                pAfterFirstHit->preciseX + 64.0f,
                pAfterFirstHit->preciseY,
                pAfterFirstHit->preciseZ);

            const OutdoorWorldRuntime::MapActorState *pDuringReaction = scenario.world.mapActorState(3);

            if (pDuringReaction == nullptr)
            {
                failure = "actor 3 missing during hit reaction";
                return false;
            }

            const float animationTicksBeforeSecondHit = pDuringReaction->animationTimeTicks;
            const float actionSecondsBeforeSecondHit = pDuringReaction->actionSeconds;

            if (animationTicksBeforeSecondHit <= 0.0f)
            {
                failure = "actor 3 hit reaction animation did not advance";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    1,
                    pDuringReaction->preciseX + 64.0f,
                    pDuringReaction->preciseY,
                    pDuringReaction->preciseZ))
            {
                failure = "second party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfterSecondHit = scenario.world.mapActorState(3);

            if (pAfterSecondHit == nullptr)
            {
                failure = "actor 3 missing after second hit";
                return false;
            }

            if (pAfterSecondHit->aiState != OutdoorWorldRuntime::ActorAiState::Stunned
                || pAfterSecondHit->animation != OutdoorWorldRuntime::ActorAnimation::GotHit)
            {
                failure = "actor 3 left stunned hit reaction after second hit";
                return false;
            }

            if (std::abs(pAfterSecondHit->animationTimeTicks - animationTicksBeforeSecondHit) > 0.001f)
            {
                failure = "actor 3 hit reaction animation restarted on second hit";
                return false;
            }

            if (pAfterSecondHit->actionSeconds > actionSecondsBeforeSecondHit + 0.001f)
            {
                failure = "actor 3 hit reaction duration increased on second hit";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_lethal_damage_enters_dying_before_dead",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    pBefore->currentHp,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "lethal party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfterLethalHit = scenario.world.mapActorState(3);

            if (pAfterLethalHit == nullptr)
            {
                failure = "actor 3 missing after lethal hit";
                return false;
            }

            if (pAfterLethalHit->isDead)
            {
                failure = "actor 3 became dead immediately without dying state";
                return false;
            }

            if (pAfterLethalHit->aiState != OutdoorWorldRuntime::ActorAiState::Dying
                || pAfterLethalHit->animation != OutdoorWorldRuntime::ActorAnimation::Dying)
            {
                failure = "actor 3 did not enter dying state";
                return false;
            }

            if (pAfterLethalHit->actionSeconds <= 0.0f)
            {
                failure = "actor 3 dying state has no duration";
                return false;
            }

            bool sawDeadState = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pAfterLethalHit->preciseX + 64.0f,
                    pAfterLethalHit->preciseY,
                    pAfterLethalHit->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pAfterUpdate = scenario.world.mapActorState(3);

                if (pAfterUpdate == nullptr)
                {
                    failure = "actor 3 missing during dying update";
                    return false;
                }

                if (pAfterUpdate->isDead)
                {
                    sawDeadState = true;

                    if (pAfterUpdate->aiState != OutdoorWorldRuntime::ActorAiState::Dead
                        || pAfterUpdate->animation != OutdoorWorldRuntime::ActorAnimation::Dead)
                    {
                        failure = "actor 3 dead state animation/state mismatch";
                        return false;
                    }

                    break;
                }
            }

            if (!sawDeadState)
            {
                failure = "actor 3 never transitioned from dying to dead";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_aggros_nearby_lizard_guard",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pVictim = scenario.world.mapActorState(3);

            if (pVictim == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            size_t guardActorIndex = static_cast<size_t>(-1);

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || pActor->isDead || pActor->hostileToParty)
                {
                    continue;
                }

                if (!gameDataLoader.getMonsterTable().isLikelySameFaction(pVictim->monsterId, pActor->monsterId))
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats == nullptr || pStats->aiType == MonsterTable::MonsterAiType::Wimp)
                {
                    continue;
                }

                const float deltaX = pActor->preciseX - pVictim->preciseX;
                const float deltaY = pActor->preciseY - pVictim->preciseY;
                const float deltaZ = pActor->preciseZ - pVictim->preciseZ;
                const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);

                if (distance <= 4096.0f)
                {
                    guardActorIndex = actorIndex;
                    break;
                }
            }

            if (guardActorIndex == static_cast<size_t>(-1))
            {
                failure = "no nearby same-faction non-wimp actor found";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    2,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pGuard = scenario.world.mapActorState(guardActorIndex);

            if (pGuard == nullptr || !pGuard->hostileToParty)
            {
                failure = "nearby same-faction guard did not become hostile";
                return false;
            }

            bool sawEngageState = false;

            for (size_t stepIndex = 0; stepIndex < 256; ++stepIndex)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ);

                pGuard = scenario.world.mapActorState(guardActorIndex);

                if (pGuard != nullptr
                    && (pGuard->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                        || pGuard->aiState == OutdoorWorldRuntime::ActorAiState::Attacking))
                {
                    sawEngageState = true;
                    break;
                }
            }

            if (!sawEngageState)
            {
                failure = "nearby same-faction guard never engaged the party";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_causes_wimp_flee",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pVictim = scenario.world.mapActorState(3);

            if (pVictim == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    2,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            bool sawFleeing = false;

            for (size_t stepIndex = 0; stepIndex < 64; ++stepIndex)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
                {
                    sawFleeing = true;
                    break;
                }
            }

            if (!sawFleeing)
            {
                failure = "attacked wimp actor never entered fleeing state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_hostile_actor_61_still_applies_damage",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(61);

            if (pBefore == nullptr)
            {
                failure = "actor 61 missing";
                return false;
            }

            if (!pBefore->hostileToParty)
            {
                failure = "actor 61 is not hostile in baseline state";
                return false;
            }

            const int beforeHp = pBefore->currentHp;

            if (!scenario.world.applyPartyAttackToMapActor(
                    61,
                    3,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "party attack did not apply to hostile actor";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(61);

            if (pAfter == nullptr || pAfter->currentHp != std::max(0, beforeHp - 3))
            {
                failure = "hostile actor did not take expected damage";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_movement_ignores_friendly_actor_3_collision",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pFriendlyActor = scenario.world.mapActorState(3);

            if (pFriendlyActor == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            std::vector<OutdoorActorCollision> hostileColliders;

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr
                    || pActor->isDead
                    || pActor->isInvisible
                    || !pActor->hostileToParty
                    || pActor->radius == 0
                    || pActor->height == 0)
                {
                    continue;
                }

                OutdoorActorCollision collider = {};
                collider.sourceIndex = actorIndex;
                collider.source = OutdoorActorCollisionSource::MapDelta;
                collider.radius = pActor->radius;
                collider.height = pActor->height;
                collider.worldX = pActor->x;
                collider.worldY = pActor->y;
                collider.worldZ = pActor->z;
                collider.group = pActor->group;
                collider.name = pActor->displayName;
                hostileColliders.push_back(std::move(collider));
            }

            movementController.setActorColliders(hostileColliders);

            OutdoorMoveState state = movementController.initializeState(
                pFriendlyActor->preciseX - 160.0f,
                pFriendlyActor->preciseY,
                pFriendlyActor->preciseZ);
            std::vector<size_t> contactedActorIndices;
            const OutdoorMoveState resolved = movementController.resolveMove(
                state,
                768.0f,
                0.0f,
                false,
                false,
                false,
                0.0f,
                0.0f,
                0.5f,
                &contactedActorIndices);

            if (!contactedActorIndices.empty())
            {
                failure = "friendly actor produced a party collision contact";
                return false;
            }

            if (resolved.x <= pFriendlyActor->preciseX)
            {
                failure = "party did not move through friendly actor";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_movement_collides_with_hostile_actor_61",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pHostileActor = scenario.world.mapActorState(61);

            if (pHostileActor == nullptr)
            {
                failure = "actor 61 missing";
                return false;
            }

            if (!pHostileActor->hostileToParty)
            {
                failure = "actor 61 is not hostile in baseline state";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            OutdoorActorCollision collider = {};
            collider.sourceIndex = 61;
            collider.source = OutdoorActorCollisionSource::MapDelta;
            collider.radius = pHostileActor->radius;
            collider.height = pHostileActor->height;
            collider.worldX = pHostileActor->x;
            collider.worldY = pHostileActor->y;
            collider.worldZ = pHostileActor->z;
            collider.group = pHostileActor->group;
            collider.name = pHostileActor->displayName;
            movementController.setActorColliders({collider});

            OutdoorMoveState state = movementController.initializeState(
                pHostileActor->preciseX - 160.0f,
                pHostileActor->preciseY,
                pHostileActor->preciseZ);
            std::vector<size_t> contactedActorIndices;
            const OutdoorMoveState resolved = movementController.resolveMove(
                state,
                768.0f,
                0.0f,
                false,
                false,
                false,
                0.0f,
                0.0f,
                0.5f,
                &contactedActorIndices);

            if (contactedActorIndices.empty())
            {
                failure = "hostile actor did not produce a party collision contact";
                return false;
            }

            if (resolved.x > pHostileActor->preciseX - 16.0f)
            {
                failure = "party moved through hostile actor";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_is_pushed_out_of_actor_overlap",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            OutdoorMoveState state = movementController.initializeState(0.0f, 0.0f, 0.0f);
            OutdoorActorCollision blocker = {};
            blocker.radius = 64;
            blocker.height = 160;
            blocker.worldX = static_cast<int>(std::lround(state.x));
            blocker.worldY = static_cast<int>(std::lround(state.y));
            blocker.worldZ = static_cast<int>(std::floor(state.footZ));
            blocker.name = "test actor";
            movementController.setActorColliders({blocker});

            const OutdoorMoveState resolved = movementController.resolveMove(
                state,
                0.0f,
                0.0f,
                false,
                false,
                false,
                0.0f,
                0.0f,
                1.0f / 60.0f);

            const float deltaX = resolved.x - static_cast<float>(blocker.worldX);
            const float deltaY = resolved.y - static_cast<float>(blocker.worldY);
            const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY);

            if (distance < 101.0f)
            {
                failure = "party remained inside actor overlap after collision resolution";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_movement_reports_actor_contact",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            OutdoorMoveState state = movementController.initializeState(0.0f, 0.0f, 0.0f);
            OutdoorActorCollision blocker = {};
            blocker.sourceIndex = 123;
            blocker.radius = 64;
            blocker.height = 160;
            blocker.worldX = static_cast<int>(std::lround(state.x + 90.0f));
            blocker.worldY = static_cast<int>(std::lround(state.y));
            blocker.worldZ = static_cast<int>(std::floor(state.footZ));
            blocker.name = "contact test actor";
            movementController.setActorColliders({blocker});

            std::vector<size_t> contactedActorIndices;
            movementController.resolveMove(
                state,
                384.0f,
                0.0f,
                false,
                false,
                false,
                0.0f,
                0.0f,
                1.0f / 60.0f,
                &contactedActorIndices);

            if (contactedActorIndices.empty())
            {
                failure = "movement controller did not report actor contact";
                return false;
            }

            if (contactedActorIndices.front() != 123)
            {
                failure = "movement controller reported wrong actor contact index";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_preview_palette_and_frame_cycle",
        [&](std::string &failure)
        {
            GameDataLoader fullMapLoader;

            if (!fullMapLoader.loadForHeadlessGameplay(assetFileSystem))
            {
                failure = "full preview loader init failed";
                return false;
            }

            if (!fullMapLoader.loadMapByFileName(assetFileSystem, "out01.odm"))
            {
                failure = "full preview map load failed";
                return false;
            }

            const std::optional<MapAssetInfo> &previewSelectedMap = fullMapLoader.getSelectedMap();

            if (!previewSelectedMap || !previewSelectedMap->outdoorActorPreviewBillboardSet)
            {
                failure = "selected map missing actor previews";
                return false;
            }

            size_t billboardIndex = 0;
            const ActorPreviewBillboardSet &billboardSet = *previewSelectedMap->outdoorActorPreviewBillboardSet;
            const ActorPreviewBillboard *pBillboard = findCompanionActorBillboard(billboardSet, 3, billboardIndex);

            if (pBillboard == nullptr)
            {
                failure = "actor 3 billboard missing";
                return false;
            }

            const ActorPreviewAnimationStats animationStats =
                analyzeActorPreviewAnimation(billboardSet, *pBillboard);

            if (animationStats.sampleCount == 0)
            {
                failure = "actor 3 preview produced no samples";
                return false;
            }

            if (animationStats.missingTextureSampleCount != 0)
            {
                failure = "actor 3 preview has missing textures";
                return false;
            }

            if (animationStats.greenDominantSampleCount <= animationStats.magentaDominantSampleCount)
            {
                failure = "actor 3 preview colors skew magenta instead of green";
                return false;
            }

            if (animationStats.distinctWalkingFrameCount < 2)
            {
                failure = "actor 3 walking preview does not cycle frames";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_pursues_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                if (hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 2000.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float acquisitionRange = hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pBefore);
            const float partyDistance = std::min(2000.0f, acquisitionRange * 0.75f);
            const float partyX = static_cast<float>(pBefore->x) + partyDistance;
            const float partyY = static_cast<float>(pBefore->y);
            const float distanceBefore = std::abs(partyX - static_cast<float>(pBefore->x));
            scenario.world.updateMapActors(1.0f, partyX, partyY, static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);
            const float distanceAfter = std::abs(partyX - static_cast<float>(pAfter->x));

            if (distanceAfter >= distanceBefore)
            {
                failure = "hostile actor did not move toward the party";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing)
            {
                failure = "hostile actor did not enter pursuing state";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::Walking)
            {
                failure = "hostile actor did not enter walking animation";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_uses_long_party_acquisition_despite_short_relation",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            const MapDeltaActor quietLandActor = modifiedMap.outdoorMapDeltaData->actors[3];
            modifiedMap.outdoorMapDeltaData->actors[53].monsterInfoId = 184;
            modifiedMap.outdoorMapDeltaData->actors[53].monsterId = 184;
            modifiedMap.outdoorMapDeltaData->actors[53].attributes = 0;
            modifiedMap.outdoorMapDeltaData->actors[53].x = quietLandActor.x;
            modifiedMap.outdoorMapDeltaData->actors[53].y = quietLandActor.y;
            modifiedMap.outdoorMapDeltaData->actors[53].z = quietLandActor.z;

            for (size_t actorIndex = 0; actorIndex < modifiedMap.outdoorMapDeltaData->actors.size(); ++actorIndex)
            {
                if (actorIndex == 53)
                {
                    continue;
                }

                MapDeltaActor &otherActor = modifiedMap.outdoorMapDeltaData->actors[actorIndex];
                otherActor.x = quietLandActor.x + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.y = quietLandActor.y + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.z = quietLandActor.z;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "synthetic actor 53 missing";
                return false;
            }

            if (std::abs(hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pBefore) - 10240.0f) > 0.1f)
            {
                failure = "synthetic actor 53 did not resolve a long party acquisition range";
                return false;
            }

            const float partyX = pBefore->preciseX + 2000.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            scenario.world.updateMapActors(1.0f, partyX, partyY, partyZ);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "synthetic actor 53 disappeared";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing
                && pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor did not engage the party despite long acquisition range";
                return false;
            }

            return true;
        }
    );

    runCase(
        "long_hostile_actor_pair_engages_at_2048",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            MapDeltaActor &leftActor = modifiedMap.outdoorMapDeltaData->actors[3];
            MapDeltaActor &rightActor = modifiedMap.outdoorMapDeltaData->actors[53];
            leftActor.monsterInfoId = 4;
            leftActor.monsterId = 4;
            rightActor.monsterInfoId = 181;
            rightActor.monsterId = 181;
            leftActor.x = -9216;
            leftActor.y = -12848;
            leftActor.z = 110;
            rightActor.x = leftActor.x + 2048;
            rightActor.y = leftActor.y;
            rightActor.z = leftActor.z;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pLeftBefore = scenario.world.mapActorState(3);
            const OutdoorWorldRuntime::MapActorState *pRightBefore = scenario.world.mapActorState(53);

            if (pLeftBefore == nullptr || pRightBefore == nullptr)
            {
                failure = "synthetic hostile actor pair missing";
                return false;
            }

            if (gameDataLoader.getMonsterTable().getRelationBetweenMonsters(
                    pLeftBefore->monsterId,
                    pRightBefore->monsterId) != 4)
            {
                failure = "synthetic hostile actor pair did not resolve a long hostility relation";
                return false;
            }

            const float partyX = (pLeftBefore->preciseX + pRightBefore->preciseX) * 0.5f;
            const float partyY = pLeftBefore->preciseY;
            const float partyZ = pLeftBefore->preciseZ;
            bool sawEngagement = false;

            for (int step = 0; step < 128; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pLeftAfter = scenario.world.mapActorState(3);
                const OutdoorWorldRuntime::MapActorState *pRightAfter = scenario.world.mapActorState(53);

                if (pLeftAfter == nullptr || pRightAfter == nullptr)
                {
                    failure = "synthetic hostile actor pair disappeared";
                    return false;
                }

                sawEngagement = sawEngagement
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking;

                if (sawEngagement)
                {
                    return true;
                }
            }

            failure = "long-hostility actor pair never engaged from 2048 units apart";
            return false;
        }
    );

    runCase(
        "hostile_melee_actor_uses_side_pursuit_when_far",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary
                    && hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 2500.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float partyX = static_cast<float>(pBefore->x + 2500);
            const float partyY = static_cast<float>(pBefore->y);
            scenario.world.updateMapActors(0.1f, partyX, partyY, static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing)
            {
                failure = "hostile melee actor did not enter pursuing state";
                return false;
            }

            if (std::abs(pAfter->moveDirectionY) < 0.1f)
            {
                failure = "hostile melee actor did not choose a side-biased pursuit direction";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_melee_actor_far_pursuit_accumulates_motion",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary
                    && hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 2500.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float startX = pBefore->preciseX;
            const float startY = pBefore->preciseY;
            const float partyX = startX + 2500.0f;
            const float partyY = startY;
            bool sawPursuing = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, pBefore->preciseZ);
                const OutdoorWorldRuntime::MapActorState *pStep = scenario.world.mapActorState(hostileActorIndex);

                if (pStep != nullptr && pStep->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing)
                {
                    sawPursuing = true;
                }
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter == nullptr)
            {
                failure = "hostile melee actor disappeared";
                return false;
            }

            if (!sawPursuing)
            {
                failure = "hostile melee actor never entered pursuing state";
                return false;
            }

            if (std::abs(pAfter->preciseX - startX) < 8.0f && std::abs(pAfter->preciseY - startY) < 8.0f)
            {
                failure = "hostile melee actor did not accumulate movement during far pursuit";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_melee_actor_uses_direct_pursuit_when_close",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary
                    && hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 700.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float partyX = static_cast<float>(pBefore->x + 700);
            const float partyY = static_cast<float>(pBefore->y);
            scenario.world.updateMapActors(0.1f, partyX, partyY, static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing)
            {
                failure = "hostile melee actor did not enter pursuing state";
                return false;
            }

            if (std::abs(pAfter->moveDirectionY) >= 0.1f)
            {
                failure = "hostile melee actor did not choose direct pursuit when close";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_51_respects_nearby_blocking_face",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(51);

            if (pActor == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            std::vector<OutdoorFaceGeometryData> faces;

            for (size_t bModelIndex = 0; bModelIndex < selectedMap->outdoorMapData->bmodels.size(); ++bModelIndex)
            {
                const OutdoorBModel &bModel = selectedMap->outdoorMapData->bmodels[bModelIndex];

                for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
                {
                    OutdoorFaceGeometryData geometry = {};

                    if (buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry))
                    {
                        faces.push_back(std::move(geometry));
                    }
                }
            }

            const OutdoorFaceGeometryData *pBlockingFace = nullptr;
            float bestDistance = std::numeric_limits<float>::max();
            const bx::Vec3 actorCenter = {
                pActor->preciseX,
                pActor->preciseY,
                pActor->preciseZ + static_cast<float>(pActor->height) * 0.5f
            };

            for (const OutdoorFaceGeometryData &face : faces)
            {
                if (face.isWalkable || !face.hasPlane)
                {
                    continue;
                }

                const float signedDistance = std::abs(signedDistanceToOutdoorFace(face, actorCenter));

                if (signedDistance >= bestDistance || signedDistance > 256.0f)
                {
                    continue;
                }

                const bx::Vec3 projectedPoint = {
                    actorCenter.x - face.normal.x * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.y - face.normal.y * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.z - face.normal.z * signedDistanceToOutdoorFace(face, actorCenter)
                };

                if (!isPointInsideOutdoorPolygonProjected(projectedPoint, face.vertices, face.normal))
                {
                    continue;
                }

                bestDistance = signedDistance;
                pBlockingFace = &face;
            }

            if (pBlockingFace == nullptr)
            {
                failure = "no nearby blocking face found for actor 51";
                return false;
            }

            const float initialSignedDistance = signedDistanceToOutdoorFace(*pBlockingFace, actorCenter);
            const float pushSign = initialSignedDistance >= 0.0f ? -1.0f : 1.0f;
            const float partyX = pActor->preciseX + pBlockingFace->normal.x * pushSign * 700.0f;
            const float partyY = pActor->preciseY + pBlockingFace->normal.y * pushSign * 700.0f;
            const float partyZ = pActor->preciseZ;

            for (int step = 0; step < 600; ++step)
            {
                scenario.world.updateMapActors(1.0f / 60.0f, partyX, partyY, partyZ);
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(51);

            if (pAfter == nullptr)
            {
                failure = "actor 51 missing after update";
                return false;
            }

            const bx::Vec3 afterCenter = {
                pAfter->preciseX,
                pAfter->preciseY,
                pAfter->preciseZ + static_cast<float>(pAfter->height) * 0.5f
            };
            const float afterSignedDistance = signedDistanceToOutdoorFace(*pBlockingFace, afterCenter);

            if ((initialSignedDistance > 0.0f && afterSignedDistance < -40.0f)
                || (initialSignedDistance < 0.0f && afterSignedDistance > 40.0f))
            {
                failure = "actor 51 crossed a nearby blocking face";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_51_ignores_hostile_actor_across_blocking_face",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(51);

            if (pActor == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            const float actorZ = pActor->preciseZ;

            std::vector<OutdoorFaceGeometryData> faces;

            for (size_t bModelIndex = 0; bModelIndex < selectedMap->outdoorMapData->bmodels.size(); ++bModelIndex)
            {
                const OutdoorBModel &bModel = selectedMap->outdoorMapData->bmodels[bModelIndex];

                for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
                {
                    OutdoorFaceGeometryData geometry = {};

                    if (buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry))
                    {
                        faces.push_back(std::move(geometry));
                    }
                }
            }

            const OutdoorFaceGeometryData *pBlockingFace = nullptr;
            float bestDistance = std::numeric_limits<float>::max();
            const bx::Vec3 actorCenter = {
                pActor->preciseX,
                pActor->preciseY,
                pActor->preciseZ + static_cast<float>(pActor->height) * 0.5f
            };

            for (const OutdoorFaceGeometryData &face : faces)
            {
                if (face.isWalkable || !face.hasPlane)
                {
                    continue;
                }

                const float signedDistance = std::abs(signedDistanceToOutdoorFace(face, actorCenter));

                if (signedDistance >= bestDistance || signedDistance > 256.0f)
                {
                    continue;
                }

                const bx::Vec3 projectedPoint = {
                    actorCenter.x - face.normal.x * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.y - face.normal.y * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.z - face.normal.z * signedDistanceToOutdoorFace(face, actorCenter)
                };

                if (!isPointInsideOutdoorPolygonProjected(projectedPoint, face.vertices, face.normal))
                {
                    continue;
                }

                bestDistance = signedDistance;
                pBlockingFace = &face;
            }

            if (pBlockingFace == nullptr)
            {
                failure = "no nearby blocking face found for actor 51";
                return false;
            }

            const float signedDistance = signedDistanceToOutdoorFace(*pBlockingFace, actorCenter);
            const float actorSideSign = signedDistance >= 0.0f ? 1.0f : -1.0f;
            const bx::Vec3 projectedPoint = {
                actorCenter.x - pBlockingFace->normal.x * signedDistance,
                actorCenter.y - pBlockingFace->normal.y * signedDistance,
                actorCenter.z - pBlockingFace->normal.z * signedDistance
            };
            const float leftActorX = projectedPoint.x + pBlockingFace->normal.x * actorSideSign * 192.0f;
            const float leftActorY = projectedPoint.y + pBlockingFace->normal.y * actorSideSign * 192.0f;
            const float rightActorX = projectedPoint.x - pBlockingFace->normal.x * actorSideSign * 192.0f;
            const float rightActorY = projectedPoint.y - pBlockingFace->normal.y * actorSideSign * 192.0f;
            const float leftActorZ = sampleOutdoorPlacementFloorHeight(
                *selectedMap->outdoorMapData,
                leftActorX,
                leftActorY,
                actorZ + 256.0f);
            const float rightActorZ = sampleOutdoorPlacementFloorHeight(
                *selectedMap->outdoorMapData,
                rightActorX,
                rightActorY,
                actorZ + 256.0f);

            const size_t baseActorCount = scenario.world.mapActorCount();

            for (size_t actorIndex = 0; actorIndex < baseActorCount; ++actorIndex)
            {
                if (!scenario.world.setMapActorDead(actorIndex, true, false))
                {
                    failure = "could not clear existing actor";
                    return false;
                }
            }

            const size_t leftActorIndex = scenario.world.mapActorCount();

            if (!scenario.world.summonMonsters(
                    1,
                    2,
                    1,
                    -static_cast<int32_t>(std::lround(leftActorX)),
                    static_cast<int32_t>(std::lround(leftActorY)),
                    static_cast<int32_t>(std::lround(leftActorZ)),
                    12,
                    0))
            {
                failure = "could not spawn left hostile actor across blocking face";
                return false;
            }

            if (!scenario.world.summonMonsters(
                    2,
                    2,
                    1,
                    -static_cast<int32_t>(std::lround(rightActorX)),
                    static_cast<int32_t>(std::lround(rightActorY)),
                    static_cast<int32_t>(std::lround(rightActorZ)),
                    10,
                    0))
            {
                failure = "could not spawn right hostile actor across blocking face";
                return false;
            }

            const size_t rightActorIndex = leftActorIndex + 1;
            const OutdoorWorldRuntime::MapActorState *pLeftActor = scenario.world.mapActorState(leftActorIndex);
            const OutdoorWorldRuntime::MapActorState *pRightActor = scenario.world.mapActorState(rightActorIndex);

            if (pLeftActor == nullptr || pRightActor == nullptr)
            {
                failure = "spawned hostile actor pair missing";
                return false;
            }

            if (gameDataLoader.getMonsterTable().getRelationBetweenMonsters(
                    pLeftActor->monsterId,
                    pRightActor->monsterId) <= 0)
            {
                failure = "spawned actor pair is not hostile";
                return false;
            }

            const float partyX = actorCenter.x + 20000.0f;
            const float partyY = actorCenter.y + 20000.0f;
            const float partyZ = actorZ;
            const int leftInitialHp = pLeftActor->currentHp;
            const int rightInitialHp = pRightActor->currentHp;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                const OutdoorWorldRuntime::MapActorState *pLeftAfter = scenario.world.mapActorState(leftActorIndex);
                const OutdoorWorldRuntime::MapActorState *pRightAfter = scenario.world.mapActorState(rightActorIndex);

                if (pLeftAfter == nullptr || pRightAfter == nullptr)
                {
                    failure = "actor disappeared during blocked hostile simulation";
                    return false;
                }

                if (pLeftAfter->currentHp != leftInitialHp || pRightAfter->currentHp != rightInitialHp)
                {
                    failure = "blocked hostile actors still exchanged damage";
                    return false;
                }

                if (scenario.world.projectileCount() > 0)
                {
                    failure = "blocked hostile actors still launched a projectile";
                    return false;
                }

                if (pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
                {
                    failure = "blocked hostile actors still engaged through geometry";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "outdoor_geometry_reports_steep_terrain_tiles",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            bool foundSteepTile = false;

            for (int tileY = 0; tileY < OutdoorMapData::TerrainHeight - 1 && !foundSteepTile; ++tileY)
            {
                for (int tileX = 0; tileX < OutdoorMapData::TerrainWidth - 1; ++tileX)
                {
                    const float worldX =
                        static_cast<float>((64 - tileX - 1) * OutdoorMapData::TerrainTileSize + 256);
                    const float worldY =
                        static_cast<float>((64 - tileY) * OutdoorMapData::TerrainTileSize - 256);

                    if (outdoorTerrainSlopeTooHigh(*selectedMap->outdoorMapData, worldX, worldY))
                    {
                        foundSteepTile = true;
                        break;
                    }
                }
            }

            if (!foundSteepTile)
            {
                failure = "no steep terrain tile found on out01";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_enters_attack_state",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr && pActor->hostileToParty && !pActor->isDead)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            scenario.world.clearPendingAudioEvents();
            const float partyX = static_cast<float>(pBefore->x + 64);
            const float partyY = static_cast<float>(pBefore->y);
            const float partyZ = static_cast<float>(pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAfter = nullptr;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                pAfter = scenario.world.mapActorState(hostileActorIndex);

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking)
                {
                    break;
                }
            }

            if (pAfter == nullptr || pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor did not enter attack state";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::AttackMelee
                && pAfter->animation != OutdoorWorldRuntime::ActorAnimation::AttackRanged)
            {
                failure = "hostile actor did not enter attack animation";
                return false;
            }

            if (scenario.world.pendingAudioEvents().empty())
            {
                failure = "attack sound event missing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mixed_actor_53_pursues_and_can_choose_ranged_attack",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            const MonsterTable::MonsterStatsEntry *pStats =
                gameDataLoader.getMonsterTable().findStatsById(pBefore->monsterId);

            if (pStats == nullptr || pStats->attackStyle != MonsterTable::MonsterAttackStyle::MixedMeleeRanged)
            {
                failure = "actor 53 is not classified as mixed melee+ranged";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    53,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "could not provoke actor 53";
                return false;
            }

            const float partyX = pBefore->preciseX + 3000.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            bool sawRangedAttack = false;
            bool sawPursuing = false;
            const float startX = pBefore->preciseX;
            const float startY = pBefore->preciseY;

            for (size_t stepIndex = 0; stepIndex < 4096; ++stepIndex)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing)
                {
                    sawPursuing = true;
                }

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    && pAfter->animation == OutdoorWorldRuntime::ActorAnimation::AttackRanged)
                {
                    sawRangedAttack = true;
                    break;
                }
            }

            if (!sawRangedAttack)
            {
                failure = "mixed actor 53 never chose a ranged attack";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "actor 53 missing after simulation";
                return false;
            }

            if (!sawPursuing)
            {
                failure = "mixed actor 53 never pursued the party";
                return false;
            }

            if (std::abs(pAfter->preciseX - startX) < 8.0f && std::abs(pAfter->preciseY - startY) < 8.0f)
            {
                failure = "mixed actor 53 never accumulated movement";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mixed_actor_53_ranged_release_spawns_arrow_projectile",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    53,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "could not provoke actor 53";
                return false;
            }

            const float partyX = pBefore->preciseX + 3000.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            bool sawRangedRelease = false;
            bool sawProjectileMove = false;
            float previousProjectileX = 0.0f;
            float previousProjectileY = 0.0f;

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                for (const OutdoorWorldRuntime::CombatEvent &event : scenario.world.pendingCombatEvents())
                {
                    if (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterRangedRelease
                        && event.sourceId == 53)
                    {
                        sawRangedRelease = true;
                    }
                }

                if (scenario.world.projectileCount() > 0)
                {
                    const OutdoorWorldRuntime::ProjectileState *pProjectile = scenario.world.projectileState(0);

                    if (pProjectile == nullptr)
                    {
                        failure = "projectile state missing";
                        return false;
                    }

                    if (pProjectile->objectName != "Arrow")
                    {
                        failure = "actor 53 did not spawn arrow projectile";
                        return false;
                    }

                    if (previousProjectileX != 0.0f || previousProjectileY != 0.0f)
                    {
                        const float deltaX = std::abs(pProjectile->x - previousProjectileX);
                        const float deltaY = std::abs(pProjectile->y - previousProjectileY);
                        sawProjectileMove = sawProjectileMove || deltaX > 1.0f || deltaY > 1.0f;
                    }

                    previousProjectileX = pProjectile->x;
                    previousProjectileY = pProjectile->y;

                    if (sawRangedRelease && sawProjectileMove)
                    {
                        return true;
                    }
                }

                scenario.world.clearPendingCombatEvents();
            }

            failure = !sawRangedRelease ? "actor 53 never released a ranged projectile" : "arrow never advanced";
            return false;
        }
    );

    runCase(
        "mixed_actor_53_arrow_hits_party_without_impact_effect",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    53,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "could not provoke actor 53";
                return false;
            }

            const float partyX = pBefore->preciseX + 2200.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            bool sawProjectile = false;
            const int initialTotalHealth = scenario.party.totalHealth();

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                applyPendingCombatEventsToScenarioParty(scenario);

                if (scenario.world.projectileCount() > 0)
                {
                    sawProjectile = true;
                }

                if (sawProjectile && scenario.party.totalHealth() < initialTotalHealth)
                {
                    if (scenario.world.projectileImpactCount() != 0)
                    {
                        failure = "arrow impact should not spawn a lingering impact effect";
                        return false;
                    }

                    return true;
                }
            }

            failure = !sawProjectile ? "actor 53 never spawned arrow projectile" : "arrow hit did not damage the party";
            return false;
        }
    );

    runCase(
        "mixed_actor_53_arrow_ignores_friendly_lizardman_blocker",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData || selectedMap->outdoorMapDeltaData->actors.size() <= 53)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapData = *selectedMap->outdoorMapData;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapData->spawns.clear();

            const MapDeltaActor quietLandActor = modifiedMap.outdoorMapDeltaData->actors[3];
            MapDeltaActor &guardActor = modifiedMap.outdoorMapDeltaData->actors[53];
            guardActor.x = quietLandActor.x;
            guardActor.y = quietLandActor.y;
            guardActor.z = quietLandActor.z;
            MapDeltaActor &blockingActor = modifiedMap.outdoorMapDeltaData->actors[3];
            blockingActor.x = quietLandActor.x + 1100;
            blockingActor.y = quietLandActor.y;
            blockingActor.z = quietLandActor.z;

            for (size_t actorIndex = 0; actorIndex < modifiedMap.outdoorMapDeltaData->actors.size(); ++actorIndex)
            {
                if (actorIndex == 3 || actorIndex == 53)
                {
                    continue;
                }

                MapDeltaActor &otherActor = modifiedMap.outdoorMapDeltaData->actors[actorIndex];
                otherActor.x = quietLandActor.x + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.y = quietLandActor.y + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.z = quietLandActor.z;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pGuard = scenario.world.mapActorState(53);
            const OutdoorWorldRuntime::MapActorState *pBlocker = scenario.world.mapActorState(3);

            if (pGuard == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            if (pBlocker == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!gameDataLoader.getMonsterTable().isLikelySameFaction(pGuard->monsterId, pBlocker->monsterId))
            {
                failure = "actor 3 is not same-faction with actor 53";
                return false;
            }

            const float partyX = pGuard->preciseX + 2200.0f;
            const float partyY = pGuard->preciseY;
            const float partyZ = pGuard->preciseZ;
            const int initialTotalHealth = scenario.party.totalHealth();
            bool sawProjectile = false;

            if (!scenario.world.debugSpawnMapActorProjectile(
                    53,
                    OutdoorWorldRuntime::MonsterAttackAbility::Attack2,
                    partyX,
                    partyY,
                    partyZ))
            {
                failure = "could not spawn actor 53 arrow projectile";
                return false;
            }

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                applyPendingCombatEventsToScenarioParty(scenario);
                sawProjectile = sawProjectile || scenario.world.projectileCount() > 0;

                if (scenario.party.totalHealth() < initialTotalHealth)
                {
                    return true;
                }
            }

            failure = !sawProjectile
                ? "actor 53 arrow projectile never spawned"
                : "friendly actor blocked actor 53 arrow before it reached the party";
            return false;
        }
    );

    runCase(
        "pirate_and_lizardman_hostile_actors_damage_each_other",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t leftActorIndex = scenario.world.mapActorCount();
            constexpr float FightCenterX = -9216.0f;
            constexpr float FightCenterY = -12848.0f;
            constexpr float FightCenterZ = 110.0f;

            if (!scenario.world.summonMonsters(1, 2, 1, 9280, -12848, static_cast<int32_t>(FightCenterZ), 12, 0))
            {
                failure = "could not spawn lizardman encounter actor";
                return false;
            }

            if (!scenario.world.summonMonsters(2, 2, 1, 9152, -12848, static_cast<int32_t>(FightCenterZ), 10, 0))
            {
                failure = "could not spawn pirate encounter actor";
                return false;
            }

            const size_t rightActorIndex = leftActorIndex + 1;
            const OutdoorWorldRuntime::MapActorState *pLeftActorBefore =
                scenario.world.mapActorState(leftActorIndex);
            const OutdoorWorldRuntime::MapActorState *pRightActorBefore =
                scenario.world.mapActorState(rightActorIndex);

            if (pLeftActorBefore == nullptr || pRightActorBefore == nullptr)
            {
                failure = "spawned hostile actor pair missing";
                return false;
            }

            if (gameDataLoader.getMonsterTable().getRelationBetweenMonsters(
                    pLeftActorBefore->monsterId,
                    pRightActorBefore->monsterId) <= 0)
            {
                failure = "spawned pirate and lizardman are not hostile";
                return false;
            }

            const int leftInitialHp = pLeftActorBefore->currentHp;
            const int rightInitialHp = pRightActorBefore->currentHp;
            const float partyX = pRightActorBefore->preciseX + 6000.0f;
            const float partyY = pRightActorBefore->preciseY;
            const float partyZ = pRightActorBefore->preciseZ;
            bool sawEngagement = false;

            for (int step = 0; step < 8192; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                const OutdoorWorldRuntime::MapActorState *pLeftActor =
                    scenario.world.mapActorState(leftActorIndex);
                const OutdoorWorldRuntime::MapActorState *pRightActor =
                    scenario.world.mapActorState(rightActorIndex);

                if (pLeftActor == nullptr || pRightActor == nullptr)
                {
                    failure = "hostile actor disappeared during simulation";
                    return false;
                }

                sawEngagement = sawEngagement
                    || pLeftActor->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pLeftActor->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pRightActor->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pRightActor->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || scenario.world.projectileCount() > 0;

                if (pLeftActor->currentHp < leftInitialHp || pRightActor->currentHp < rightInitialHp
                    || pLeftActor->isDead || pRightActor->isDead)
                {
                    if ((pLeftActor->isDead && pLeftActor->currentHp == 0 && leftInitialHp > 0)
                        || (pRightActor->isDead && pRightActor->currentHp == 0 && rightInitialHp > 0))
                    {
                        failure = "first hostile hit still one-shot a spawned actor";
                        return false;
                    }

                    return true;
                }
            }

            failure = sawEngagement
                ? "hostile actor engagement never produced damage"
                : "hostile actor pair never engaged each other";
            return false;
        }
    );

    runCase(
        "spell_projectile_spawns_visible_impact_effect",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->actors[53].monsterInfoId = 80;
            modifiedMap.outdoorMapDeltaData->actors[53].monsterId = 80;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "synthetic actor 53 missing";
                return false;
            }

            const float partyX = pBefore->preciseX + 2600.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;

            if (!scenario.world.debugSpawnMapActorProjectile(
                    53,
                    OutdoorWorldRuntime::MonsterAttackAbility::Spell1,
                    partyX,
                    partyY,
                    partyZ))
            {
                failure = "could not spawn synthetic spell projectile";
                return false;
            }

            bool sawProjectile = false;

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                if (scenario.world.projectileCount() > 0)
                {
                    sawProjectile = true;
                }

                if (scenario.world.projectileImpactCount() > 0)
                {
                    const OutdoorWorldRuntime::ProjectileImpactState *pImpact =
                        scenario.world.projectileImpactState(0);

                    if (pImpact == nullptr)
                    {
                        failure = "impact state missing";
                        return false;
                    }

                    if (pImpact->objectName != "explosion")
                    {
                        failure = "spell impact did not spawn expected explosion effect";
                        return false;
                    }

                    return true;
                }
            }

            if (!sawProjectile)
            {
                failure = "synthetic spell projectile never spawned";
            }
            else
            {
                failure = "spell impact never spawned";
            }

            return false;
        }
    );

    runCase(
        "hostile_actor_attack_persists_when_party_moves_away",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float nearPartyX = static_cast<float>(pBefore->x + 64);
            const float nearPartyY = static_cast<float>(pBefore->y);
            const float partyZ = static_cast<float>(pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAttacking = nullptr;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, nearPartyX, nearPartyY, partyZ);
                pAttacking = scenario.world.mapActorState(hostileActorIndex);

                if (pAttacking != nullptr && pAttacking->aiState == OutdoorWorldRuntime::ActorAiState::Attacking)
                {
                    break;
                }
            }

            if (pAttacking == nullptr || pAttacking->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor did not enter attack state";
                return false;
            }

            if (pAttacking->actionSeconds <= 0.0f)
            {
                failure = "hostile actor attack duration did not start";
                return false;
            }

            const float previousActionSeconds = pAttacking->actionSeconds;
            scenario.world.updateMapActors(
                0.05f,
                static_cast<float>(pBefore->x + 4000),
                static_cast<float>(pBefore->y),
                static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor abandoned attack when party moved away";
                return false;
            }

            if (pAfter->actionSeconds >= previousActionSeconds)
            {
                failure = "hostile actor attack did not continue progressing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_melee_actor_respects_recovery_after_attack",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float partyX = static_cast<float>(pBefore->x + 64);
            const float partyY = static_cast<float>(pBefore->y);
            const float partyZ = static_cast<float>(pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAttacking = nullptr;

            for (int step = 0; step < 512; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                pAttacking = scenario.world.mapActorState(hostileActorIndex);

                if (pAttacking != nullptr && pAttacking->aiState == OutdoorWorldRuntime::ActorAiState::Attacking)
                {
                    break;
                }
            }

            if (pAttacking == nullptr || pAttacking->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile melee actor did not enter attack state";
                return false;
            }

            bool sawPostAttackStandWithCooldown = false;

            for (int step = 0; step < 512; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pStep = scenario.world.mapActorState(hostileActorIndex);

                if (pStep == nullptr)
                {
                    failure = "hostile melee actor disappeared";
                    return false;
                }

                if (pStep->aiState != OutdoorWorldRuntime::ActorAiState::Attacking
                    && pStep->attackCooldownSeconds > 0.2f)
                {
                    sawPostAttackStandWithCooldown = true;
                    break;
                }
            }

            if (!sawPostAttackStandWithCooldown)
            {
                failure = "hostile melee actor did not expose a post-attack recovery window";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_reinforcement_wave_event_463_spawns_all_groups",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = scenario.world.mapActorCount();

            for (size_t actorIndex = 0; actorIndex < baseActorCount; ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr
                    && pActor->group >= 10
                    && pActor->group <= 13
                    && !pActor->isDead)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not clear reinforcement source actor";
                        return false;
                    }
                }
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "event 463 execution failed";
                return false;
            }

            if (scenario.world.mapActorCount() != baseActorCount + 48)
            {
                failure = "expected 48 spawned runtime actors, got "
                    + std::to_string(scenario.world.mapActorCount() - baseActorCount);
                return false;
            }

            std::array<int, 4> counts = {};
            std::array<bool, 4> correctMonsterIds = {true, true, true, true};

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pMonster = scenario.world.mapActorState(actorIndex);

                if (pMonster == nullptr)
                {
                    failure = "missing spawned actor state";
                    return false;
                }

                if (pMonster->group >= 10 && pMonster->group <= 13)
                {
                    const size_t groupOffset = pMonster->group - 10;
                    ++counts[groupOffset];

                    const int16_t expectedMonsterId = pMonster->group <= 11 ? 182 : 5;

                    if (pMonster->monsterId != expectedMonsterId)
                    {
                        correctMonsterIds[groupOffset] = false;
                    }
                }
            }

            for (size_t index = 0; index < counts.size(); ++index)
            {
                if (counts[index] != 12)
                {
                    failure = "group " + std::to_string(index + 10) + " expected 12 summons";
                    return false;
                }

                if (!correctMonsterIds[index])
                {
                    failure = "group " + std::to_string(index + 10) + " summoned wrong monster tier";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "dwi_reinforcement_wave_event_463_does_not_duplicate_alive_groups",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr
                    && pActor->group >= 10
                    && pActor->group <= 13
                    && !pActor->isDead)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not clear reinforcement source actor";
                        return false;
                    }
                }
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "first event 463 execution failed";
                return false;
            }

            const size_t firstCount = scenario.world.mapActorCount();

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "second event 463 execution failed";
                return false;
            }

            if (scenario.world.mapActorCount() != firstCount)
            {
                failure = "reinforcement waves duplicated while groups were still alive";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_actor_killed_policy_actor_id_mm8",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (scenario.world.checkMonstersKilled(4, 8, 1, true))
            {
                failure = "actor 8 should not start as killed";
                return false;
            }

            if (!scenario.world.setMapActorDead(8, true))
            {
                failure = "could not mark actor 8 dead";
                return false;
            }

            if (!scenario.world.checkMonstersKilled(4, 8, 1, true))
            {
                failure = "actor-id kill check did not detect dead actor 8";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_actor_death_generates_corpse_loot",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.world.setMapActorDead(5, true))
            {
                failure = "could not kill actor 5";
                return false;
            }

            if (!scenario.world.openMapActorCorpseView(5))
            {
                failure = "corpse view did not open";
                return false;
            }

            const OutdoorWorldRuntime::CorpseViewState *pCorpseView = scenario.world.activeCorpseView();

            if (pCorpseView == nullptr)
            {
                failure = "active corpse view missing";
                return false;
            }

            if (pCorpseView->title != "Lizardman Peasant")
            {
                failure = "unexpected corpse title \"" + pCorpseView->title + "\"";
                return false;
            }

            if (pCorpseView->items.empty() || !pCorpseView->items[0].isGold || pCorpseView->items[0].goldAmount == 0)
            {
                failure = "expected gold loot on corpse";
                return false;
            }

            while (const OutdoorWorldRuntime::CorpseViewState *pActiveCorpseView = scenario.world.activeCorpseView())
            {
                if (pActiveCorpseView->items.empty())
                {
                    break;
                }

                OutdoorWorldRuntime::ChestItemState lootedItem = {};

                if (!scenario.world.takeActiveCorpseItem(0, lootedItem))
                {
                    failure = "could not remove corpse loot item";
                    return false;
                }
            }

            if (scenario.world.activeCorpseView() != nullptr)
            {
                failure = "empty corpse view should close itself";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(5);

            if (pActor == nullptr || !pActor->isInvisible)
            {
                failure = "looted corpse actor should disappear";
                return false;
            }

            if (scenario.world.openMapActorCorpseView(5))
            {
                failure = "looted corpse should no longer be reopenable";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_actor_death_emits_audio_event",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            scenario.world.clearPendingAudioEvents();

            if (!scenario.world.setMapActorDead(53, true))
            {
                failure = "could not kill actor 53";
                return false;
            }

            if (scenario.world.pendingAudioEvents().empty())
            {
                failure = "missing death audio event";
                return false;
            }

            const OutdoorWorldRuntime::AudioEvent &event = scenario.world.pendingAudioEvents().front();

            if (event.soundId != 1011 || event.reason != "monster_death")
            {
                failure = "unexpected audio event payload";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_group_killed_policy_counts_spawned_runtime_actors",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = scenario.world.mapActorCount();

            for (size_t actorIndex = 0; actorIndex < baseActorCount; ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr
                    && pActor->group == 10
                    && !pActor->isDead)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not clear group 10 source actor";
                        return false;
                    }
                }
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "event 463 execution failed";
                return false;
            }

            if (scenario.world.checkMonstersKilled(1, 10, 0, true))
            {
                failure = "group 10 should still be alive after spawning";
                return false;
            }

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pMonster = scenario.world.mapActorState(actorIndex);

                if (pMonster != nullptr && pMonster->group == 10)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not mark spawned runtime actor dead";
                        return false;
                    }
                }
            }

            if (!scenario.world.checkMonstersKilled(1, 10, 0, true))
            {
                failure = "group kill check did not treat dead spawned runtime actors as defeated";
                return false;
            }

            return true;
        }
    );

    runCase(
        "generic_actor_dialog_resolves_lizardman_portraits",
        [&](std::string &failure)
        {
            const EventRuntimeState runtimeState = {};

            const std::optional<GenericActorDialogResolution> villagerResolution = resolveGenericActorDialog(
                "out01.odm",
                "Lizardman Villager",
                1,
                runtimeState,
                gameDataLoader.getNpcDialogTable()
            );

            if (!villagerResolution || villagerResolution->npcId != 516)
            {
                failure = "villager did not resolve to lizardman peasant portrait npc";
                return false;
            }

            const std::optional<GenericActorDialogResolution> soldierResolution = resolveGenericActorDialog(
                "out01.odm",
                "Lizardman Soldier",
                2,
                runtimeState,
                gameDataLoader.getNpcDialogTable()
            );

            if (!soldierResolution || soldierResolution->npcId != 517)
            {
                failure = "soldier did not resolve to lizardman guard portrait npc";
                return false;
            }

            const std::optional<GenericActorDialogResolution> guardResolution = resolveGenericActorDialog(
                "out01.odm",
                "Guard",
                9,
                runtimeState,
                gameDataLoader.getNpcDialogTable()
            );

            if (!guardResolution || guardResolution->npcId != 517)
            {
                failure = "guard did not resolve to lizardman guard portrait npc";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_actor_peasant_news",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!openActorInScenario(gameDataLoader, *selectedMap, scenario, 5))
            {
                failure = "actor open failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Lizardman Peasant")
            {
                failure = "unexpected title \"" + dialog.title + "\"";
                return false;
            }

            if (dialog.participantPictureId != 800)
            {
                failure = "unexpected peasant picture id " + std::to_string(dialog.participantPictureId);
                return false;
            }

            if (!dialogContainsText(dialog, "If the pirates make it through our warriors"))
            {
                failure = "missing peasant news text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_actor_lookout_news",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!openActorInScenario(gameDataLoader, *selectedMap, scenario, 35))
            {
                failure = "actor open failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogContainsText(dialog, "Would you like to fire the cannons"))
            {
                failure = "missing lookout cannon prompt";
                return false;
            }

            return true;
        }
    );

    runCase(
        "single_resident_auto_open",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Fredrick Talimere")
            {
                failure = "unexpected title \"" + dialog.title + "\"";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Portals of Stone") || !dialogHasActionLabel(dialog, "Cataclysm"))
            {
                failure = "missing baseline Fredrick topics";
                return false;
            }

            return true;
        }
    );

    runCase(
        "fredrick_initial_topics_exact",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            std::vector<std::string> actionLabels;

            for (const EventDialogAction &action : dialog.actions)
            {
                actionLabels.push_back(action.label);
            }

            const std::vector<std::string> expectedLabels = {
                "Portals of Stone",
                "Cataclysm",
            };

            if (actionLabels != expectedLabels)
            {
                failure = "unexpected initial Fredrick topics";
                return false;
            }

            return true;
        }
    );

    runCase(
        "multi_resident_house_selection",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Clan Leader's Hall")
            {
                failure = "unexpected title \"" + dialog.title + "\"";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Brekish Onefang") || !dialogHasActionLabel(dialog, "Dadeross"))
            {
                failure = "missing resident actions";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_shop_service_menu_structure",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 171, dialog))
            {
                failure = "could not open True Mettle";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Buy Standard")
                || !dialogHasActionLabel(dialog, "Buy Special")
                || !dialogHasActionLabel(dialog, "Display Equipment")
                || !dialogHasActionLabel(dialog, "Learn Skills"))
            {
                failure = "shop root menu is incomplete";
                return false;
            }

            const std::optional<size_t> equipmentIndex = findActionIndexByLabel(dialog, "Display Equipment");

            if (!equipmentIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *equipmentIndex, dialog))
            {
                failure = "could not open equipment submenu";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Sell")
                || !dialogHasActionLabel(dialog, "Identify")
                || !dialogHasActionLabel(dialog, "Repair"))
            {
                failure = "shop equipment submenu is incomplete";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_temple_service_participant_identity",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 185, dialog))
            {
                failure = "could not open temple";
                return false;
            }

            if (dialog.houseTitle != "Mystic Medicine")
            {
                failure = "unexpected house title \"" + dialog.houseTitle + "\"";
                return false;
            }

            if (dialog.title != "Pish, Healer")
            {
                failure = "unexpected participant title \"" + dialog.title + "\"";
                return false;
            }

            if (dialog.participantPictureId != 2108)
            {
                failure = "unexpected participant picture id " + std::to_string(dialog.participantPictureId);
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_temple_skill_learning",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(1))
            {
                failure = "could not select cleric";
                return false;
            }

            scenario.party.addGold(2000);
            const int initialGold = scenario.party.gold();

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 185, dialog))
            {
                failure = "could not open temple";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Learn Skills"))
            {
                failure = "temple missing Learn Skills action";
                return false;
            }

            const std::optional<size_t> learnSkillsIndex = findActionIndexByLabel(dialog, "Learn Skills");

            if (!learnSkillsIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *learnSkillsIndex, dialog))
            {
                failure = "could not open temple skills menu";
                return false;
            }

            const std::optional<size_t> merchantIndex = findActionIndexByLabelPrefix(dialog, "Learn Merchant ");

            if (!merchantIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *merchantIndex, dialog))
            {
                failure = "could not learn Merchant in temple";
                return false;
            }

            const Character *pCleric = scenario.party.member(1);

            if (pCleric == nullptr || !pCleric->hasSkill("Merchant"))
            {
                failure = "cleric did not learn Merchant";
                return false;
            }

            if (scenario.party.gold() >= initialGold)
            {
                failure = "temple skill learning did not cost gold";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_guild_skill_learning",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            scenario.party.addGold(2000);

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 179, dialog))
            {
                failure = "could not open guild";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Buy Spellbooks") || !dialogHasActionLabel(dialog, "Learn Skills"))
            {
                failure = "guild root menu is incomplete";
                return false;
            }

            const std::optional<size_t> learnSkillsIndex = findActionIndexByLabel(dialog, "Learn Skills");

            if (!learnSkillsIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *learnSkillsIndex, dialog))
            {
                failure = "could not open guild skills menu";
                return false;
            }

            const std::optional<size_t> airIndex = findActionIndexByLabelPrefix(dialog, "Learn Air Magic ");

            if (!airIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *airIndex, dialog))
            {
                failure = "could not learn Air Magic in guild";
                return false;
            }

            const Character *pSorcerer = scenario.party.member(3);

            if (pSorcerer == nullptr || !pSorcerer->hasSkill("AirMagic"))
            {
                failure = "sorcerer did not learn Air Magic";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_training_service_uses_active_member",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 187, dialog))
            {
                failure = "could not open training hall";
                return false;
            }

            const std::optional<size_t> trainIndex = findActionIndexByLabelPrefix(dialog, "Train Ariel ");

            if (!trainIndex)
            {
                failure = "training hall did not target the default active member";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(1))
            {
                failure = "could not switch active member";
                return false;
            }

            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, scenario.pEventRuntimeState->messages.size(), true);

            if (!findActionIndexByLabelPrefix(dialog, "Train Brom "))
            {
                failure = "training hall did not update for the selected character";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_tavern_arcomage_submenu",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 191, dialog))
            {
                failure = "could not open tavern";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Play Arcomage"))
            {
                failure = "tavern missing Arcomage root action";
                return false;
            }

            const std::optional<size_t> arcomageIndex = findActionIndexByLabel(dialog, "Play Arcomage");

            if (!arcomageIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *arcomageIndex, dialog))
            {
                failure = "could not open Arcomage submenu";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Rules")
                || !dialogHasActionLabel(dialog, "Victory Conditions")
                || !dialogHasActionLabel(dialog, "Play"))
            {
                failure = "Arcomage submenu is incomplete";
                return false;
            }

            const std::optional<size_t> rulesIndex = findActionIndexByLabel(dialog, "Rules");

            if (!rulesIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *rulesIndex, dialog))
            {
                failure = "could not open Arcomage rules";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Rules")
                || !dialogHasActionLabel(dialog, "Victory Conditions")
                || !dialogHasActionLabel(dialog, "Play"))
            {
                failure = "Arcomage submenu did not remain available after rules";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_bank_deposit_withdraw_roundtrip",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 193, dialog))
            {
                failure = "could not open bank";
                return false;
            }

            const std::optional<size_t> depositIndex = findActionIndexByLabel(dialog, "Deposit all carried gold");

            if (!depositIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *depositIndex, dialog))
            {
                failure = "could not deposit gold";
                return false;
            }

            if (scenario.party.gold() != 0 || scenario.party.bankGold() <= 0)
            {
                failure = "deposit did not move gold into the bank";
                return false;
            }

            const std::optional<size_t> withdrawIndex = findActionIndexByLabelPrefix(dialog, "Withdraw all banked gold ");

            if (!withdrawIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *withdrawIndex, dialog))
            {
                failure = "could not withdraw gold";
                return false;
            }

            if (scenario.party.bankGold() != 0 || scenario.party.gold() <= 0)
            {
                failure = "withdraw did not return gold to the party";
                return false;
            }

            return true;
        }
    );

    runCase(
        "brekish_topic_mutation",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> brekishIndex = findActionIndexByLabel(dialog, "Brekish Onefang");

            if (!brekishIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *brekishIndex, dialog))
            {
                failure = "could not open Brekish";
                return false;
            }

            const std::optional<size_t> portalsIndex = findActionIndexByLabel(dialog, "Portals of Stone");

            if (!portalsIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *portalsIndex, dialog))
            {
                failure = "could not execute Portals of Stone";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Quest"))
            {
                failure = "Portals of Stone did not mutate into Quest";
                return false;
            }

            return true;
        }
    );

    runCase(
        "fredrick_topics_after_brekish_quest",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> brekishIndex = findActionIndexByLabel(dialog, "Brekish Onefang");

            if (!brekishIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *brekishIndex, dialog))
            {
                failure = "could not open Brekish";
                return false;
            }

            const std::optional<size_t> portalsIndex = findActionIndexByLabel(dialog, "Portals of Stone");

            if (!portalsIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *portalsIndex, dialog))
            {
                failure = "could not execute Portals of Stone";
                return false;
            }

            const std::optional<size_t> questIndex = findActionIndexByLabel(dialog, "Quest");

            if (!questIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *questIndex, dialog))
            {
                failure = "could not execute Quest";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed after quest";
                return false;
            }

            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogHasActionLabel(dialog, "Power Stone") || !dialogHasActionLabel(dialog, "Abandoned Temple"))
            {
                failure = "Fredrick missing unlocked quest topics";
                return false;
            }

            return true;
        }
    );

    runCase(
        "fredrick_topics_exact_after_brekish_quest",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 197))
            {
                failure = "event 197 failed";
                return false;
            }

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> brekishIndex = findActionIndexByLabel(dialog, "Brekish Onefang");

            if (!brekishIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *brekishIndex, dialog))
            {
                failure = "could not open Brekish";
                return false;
            }

            const std::optional<size_t> portalsIndex = findActionIndexByLabel(dialog, "Portals of Stone");

            if (!portalsIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *portalsIndex, dialog))
            {
                failure = "could not execute Portals of Stone";
                return false;
            }

            const std::optional<size_t> questIndex = findActionIndexByLabel(dialog, "Quest");

            if (!questIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *questIndex, dialog))
            {
                failure = "could not execute Quest";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed after quest";
                return false;
            }

            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            std::vector<std::string> actionLabels;

            for (const EventDialogAction &action : dialog.actions)
            {
                actionLabels.push_back(action.label);
            }

            const std::vector<std::string> expectedLabels = {
                "Portals of Stone",
                "Cataclysm",
                "Power Stone",
                "Abandoned Temple",
            };

            if (actionLabels != expectedLabels)
            {
                failure = "unexpected Fredrick topics after Brekish quest";
                return false;
            }

            return true;
        }
    );

    runCase(
        "award_gated_topic_stephen",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 72);

            if (!dialogHasActionLabel(dialog, "Clues"))
            {
                failure = "Stephen should initially expose Clues";
                return false;
            }

            scenario.party.addAward(30);
            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 72);

            if (dialogHasActionLabel(dialog, "Clues"))
            {
                failure = "Clues should hide once award 30 is present";
                return false;
            }

            scenario.party.removeAward(30);
            scenario.party.addAward(31);
            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 72);

            if (dialogHasActionLabel(dialog, "Clues"))
            {
                failure = "Clues should hide once award 31 is present";
                return false;
            }

            scenario.party.removeAward(31);
            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 72);

            if (!dialogHasActionLabel(dialog, "Clues"))
            {
                failure = "Clues should reappear after removing gating awards";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hiss_quest_followup_persists_across_reentry",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 11, dialog))
            {
                failure = "could not enter Hiss's Hut";
                return false;
            }

            const std::optional<size_t> questIndex = findActionIndexByLabel(dialog, "Quest");

            if (!questIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *questIndex, dialog))
            {
                failure = "could not execute Hiss Quest";
                return false;
            }

            scenario.pEventRuntimeState->pendingDialogueContext.reset();
            scenario.pEventRuntimeState->dialogueState = {};
            scenario.pEventRuntimeState->messages.clear();

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 11, dialog))
            {
                failure = "could not re-enter Hiss's Hut";
                return false;
            }

            const std::optional<size_t> idolIndex = findActionIndexByLabel(dialog, "Do you have the Idol?");

            if (!idolIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *idolIndex, dialog))
            {
                failure = "could not execute Hiss follow-up topic";
                return false;
            }

            if (!dialogContainsText(dialog, "Where is the Idol?  Do not waste my time unless you have it!"))
            {
                failure = "missing Hiss missing-idol follow-up text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_not_enough_gold",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr
                || ensureCharacterSkill(*pCharacter, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare Identify Item skill";
                return false;
            }

            scenario.party.addGold(-scenario.party.gold());

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty() || dialog.actions.front().label != "You don't have enough gold!")
            {
                failure = "missing not-enough-gold rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_missing_skill",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr)
            {
                failure = "missing active character";
                return false;
            }

            pCharacter->skills.erase("IdentifyItem");

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "You must know the skill before you can become an expert in it!")
            {
                failure = "missing missing-skill rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_insufficient_skill_level",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr
                || ensureCharacterSkill(*pCharacter, "IdentifyItem", 6, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare insufficient skill state";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label
                    != "You don't meet the requirements, and cannot be taught until you do.")
            {
                failure = "missing insufficient-requirements rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_wrong_class",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(0))
            {
                failure = "could not select knight";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr
                || ensureCharacterSkill(*pCharacter, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare wrong-class skill state";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "This skill level can not be learned by the Knight class.")
            {
                failure = "missing wrong-class rejection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_character_switch_changes_logic",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(0))
            {
                failure = "could not select knight";
                return false;
            }

            Character *pKnight = scenario.party.activeMember();

            if (pKnight == nullptr || ensureCharacterSkill(*pKnight, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare knight state";
                return false;
            }

            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer for knight";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "This skill level can not be learned by the Knight class.")
            {
                failure = "wrong-class baseline did not match";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not switch to sorcerer";
                return false;
            }

            Character *pSorcerer = scenario.party.activeMember();

            if (pSorcerer == nullptr
                || ensureCharacterSkill(*pSorcerer, "IdentifyItem", 7, SkillMastery::Expert) == nullptr)
            {
                failure = "could not prepare sorcerer state";
                return false;
            }

            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.actions.empty() || dialog.actions.front().label != "Become Master in Identify Item for 2500 gold")
            {
                failure = "dialog did not change after switching active character";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mastery_teacher_offer_and_learn",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setActiveMemberIndex(3))
            {
                failure = "could not select sorcerer";
                return false;
            }

            Character *pCharacter = scenario.party.activeMember();

            if (pCharacter == nullptr)
            {
                failure = "missing active character";
                return false;
            }

            CharacterSkill *pIdentifyItem = ensureCharacterSkill(*pCharacter, "IdentifyItem", 7, SkillMastery::Expert);

            if (pIdentifyItem == nullptr)
            {
                failure = "could not prepare Identify Item skill";
                return false;
            }

            const int initialGold = scenario.party.gold();
            scenario.party.addGold(5000);

            EventDialogContent dialog = {};

            if (!openMasteryTeacherOfferInScenario(
                    gameDataLoader,
                    *selectedMap,
                    scenario,
                    388,
                    "Master Identify Item",
                    dialog))
            {
                failure = "could not open mastery teacher offer";
                return false;
            }

            if (dialog.actions.empty()
                || dialog.actions.front().label != "Become Master in Identify Item for 2500 gold")
            {
                failure = "unexpected mastery teacher offer text";
                return false;
            }

            if (!executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, 0, dialog))
            {
                failure = "could not learn mastery";
                return false;
            }

            const Character *pUpdatedCharacter = scenario.party.activeMember();
            const CharacterSkill *pUpdatedSkill = pUpdatedCharacter != nullptr
                ? pUpdatedCharacter->findSkill("IdentifyItem")
                : nullptr;

            if (pUpdatedSkill == nullptr || pUpdatedSkill->mastery != SkillMastery::Master)
            {
                failure = "mastery was not increased";
                return false;
            }

            if (scenario.party.gold() != initialGold + 5000 - 2500)
            {
                failure = "gold was not deducted by trainer cost";
                return false;
            }

            if (dialog.actions.empty() || dialog.actions.front().label != "You are already a master in this skill.")
            {
                failure =
                    "did not remain on mastery teacher topic after learning: actions="
                    + std::to_string(dialog.actions.size())
                    + " first_action="
                    + (dialog.actions.empty() ? std::string("<none>") : dialog.actions.front().label);
                return false;
            }

            if (!dialogContainsText(dialog, "With Mastery of the Identify Items skill"))
            {
                failure = "missing mastery teacher topic text after learning";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actual_roster_join_rohani",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 455);
            const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

            if (!joinIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *joinIndex, dialog))
            {
                failure = "could not open Rohani roster join offer";
                return false;
            }

            if (!dialogContainsText(dialog, "Will you have Rohani Oscleton the Dark Elf join you?"))
            {
                failure = "missing Rohani roster join prompt text";
                return false;
            }

            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept Rohani roster join offer";
                return false;
            }

            if (!scenario.party.hasRosterMember(6))
            {
                failure = "Rohani roster member was not added to the party";
                return false;
            }

            if (!scenario.pEventRuntimeState->unavailableNpcIds.contains(455))
            {
                failure = "Rohani should become unavailable after recruitment";
                return false;
            }

            if (!dialogContainsText(dialog, "joined the party"))
            {
                failure = "missing Rohani join confirmation text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actual_roster_join_rohani_full_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const RosterEntry *pExtraMember = gameDataLoader.getRosterTable().get(3);

            if (pExtraMember == nullptr || !scenario.party.recruitRosterMember(*pExtraMember))
            {
                failure = "could not fill party to 5";
                return false;
            }

            EventDialogContent dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 455);
            const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

            if (!joinIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *joinIndex, dialog))
            {
                failure = "could not open Rohani full-party offer";
                return false;
            }

            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept Rohani full-party offer";
                return false;
            }

            if (!dialogContainsText(dialog, "I'm glad you've decided to take me"))
            {
                failure = "missing Rohani full-party text";
                return false;
            }

            if (scenario.pEventRuntimeState->unavailableNpcIds.contains(455))
            {
                failure = "Rohani should remain available after moving to the inn";
                return false;
            }

            const auto movedHouseIt = scenario.pEventRuntimeState->npcHouseOverrides.find(455);

            if (movedHouseIt == scenario.pEventRuntimeState->npcHouseOverrides.end()
                || movedHouseIt->second != AdventurersInnHouseId)
            {
                failure = "Rohani was not moved to the Adventurer's Inn";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actual_roster_join_dyson_direct",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 483);
            const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

            if (!joinIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *joinIndex, dialog))
            {
                failure = "could not open Dyson direct roster join offer";
                return false;
            }

            if (!dialogContainsText(dialog, "I will gladly join you."))
            {
                failure = "missing Dyson direct roster join prompt text";
                return false;
            }

            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept Dyson direct roster join offer";
                return false;
            }

            if (!scenario.party.hasRosterMember(34))
            {
                failure = "Dyson roster member was not added by direct join";
                return false;
            }

            return true;
        }
    );

    runCase(
        "promotion_champion_event_primary_knight",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            scenario.party.grantItem(539);

            if (!executeGlobalEventInScenario(gameDataLoader, *selectedMap, scenario, 58))
            {
                failure = "global event 58 failed";
                return false;
            }

            const Character *pMember0 = scenario.party.member(0);
            const Character *pMember1 = scenario.party.member(1);

            if (pMember0 == nullptr || pMember0->className != "Champion")
            {
                failure = "member 0 was not promoted to Champion";
                return false;
            }

            if (pMember1 == nullptr || pMember1->className != "Cleric")
            {
                failure = "non-knight member changed unexpectedly";
                return false;
            }

            if (!scenario.party.hasAward(0, 23))
            {
                failure = "member 0 missing Champion promotion award";
                return false;
            }

            if (scenario.party.hasAward(1, 23))
            {
                failure = "member 1 should not receive Champion promotion award";
                return false;
            }

            if (scenario.party.inventoryItemCount(539) != 0)
            {
                failure = "Ebonest was not consumed during promotion";
                return false;
            }

            return true;
        }
    );

    runCase(
        "promotion_champion_event_multiple_member_indices",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.party.setMemberClassName(0, "Cleric")
                || !scenario.party.setMemberClassName(1, "Knight")
                || !scenario.party.setMemberClassName(2, "Knight"))
            {
                failure = "could not prepare party class layout";
                return false;
            }

            if (!scenario.party.grantItemToMember(1, 539) || !scenario.party.grantItemToMember(2, 539))
            {
                failure = "could not place Ebonest on both knight members";
                return false;
            }

            if (!executeGlobalEventInScenario(gameDataLoader, *selectedMap, scenario, 58))
            {
                failure = "global event 58 failed";
                return false;
            }

            const Character *pMember0 = scenario.party.member(0);
            const Character *pMember1 = scenario.party.member(1);
            const Character *pMember2 = scenario.party.member(2);
            const Character *pMember3 = scenario.party.member(3);

            if (pMember0 == nullptr || pMember0->className != "Cleric")
            {
                failure = "member 0 should remain Cleric";
                return false;
            }

            if (pMember1 == nullptr || pMember1->className != "Champion")
            {
                failure = "member 1 was not promoted to Champion";
                return false;
            }

            if (pMember2 == nullptr || pMember2->className != "Champion")
            {
                failure = "member 2 was not promoted to Champion";
                return false;
            }

            if (pMember3 == nullptr || pMember3->className == "Champion")
            {
                failure = "member 3 changed unexpectedly";
                return false;
            }

            if (!scenario.party.hasAward(1, 23) || !scenario.party.hasAward(2, 23))
            {
                failure = "promoted members are missing Champion awards";
                return false;
            }

            if (scenario.party.hasAward(0, 23) || scenario.party.hasAward(3, 23))
            {
                failure = "non-targeted members received Champion awards";
                return false;
            }

            if (scenario.party.inventoryItemCount(539) != 0)
            {
                failure = "Ebonest was not consumed for each promoted knight";
                return false;
            }

            return true;
        }
    );

    runCase(
        "roster_join_offer_mapping_samples",
        [&](std::string &failure)
        {
            struct ExpectedRosterJoinOffer
            {
                uint32_t topicId = 0;
                uint32_t rosterId = 0;
                uint32_t inviteTextId = 0;
                uint32_t partyFullTextId = 0;
            };

            const std::array<ExpectedRosterJoinOffer, 7> expectedOffers = {
                ExpectedRosterJoinOffer{602, 2, 202, 203},
                ExpectedRosterJoinOffer{606, 6, 210, 211},
                ExpectedRosterJoinOffer{611, 11, 220, 221},
                ExpectedRosterJoinOffer{627, 27, 252, 253},
                ExpectedRosterJoinOffer{630, 30, 258, 259},
                ExpectedRosterJoinOffer{632, 32, 262, 263},
                ExpectedRosterJoinOffer{634, 34, 266, 267},
            };

            for (const ExpectedRosterJoinOffer &expectedOffer : expectedOffers)
            {
                const std::optional<NpcDialogTable::RosterJoinOffer> actualOffer =
                    gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(expectedOffer.topicId);

                if (!actualOffer)
                {
                    failure = "missing roster join offer for topic " + std::to_string(expectedOffer.topicId);
                    return false;
                }

                if (actualOffer->rosterId != expectedOffer.rosterId
                    || actualOffer->inviteTextId != expectedOffer.inviteTextId
                    || actualOffer->partyFullTextId != expectedOffer.partyFullTextId)
                {
                    failure = "unexpected roster join mapping for topic " + std::to_string(expectedOffer.topicId);
                    return false;
                }
            }

            if (gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(600))
            {
                failure = "topic 600 should not be classified as a roster join offer";
                return false;
            }

            if (gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(650))
            {
                failure = "topic 650 should not be classified as a roster join offer";
                return false;
            }

            return true;
        }
    );

    runCase(
        "synthetic_roster_join_accept",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(202);

            if (inviteText)
            {
                scenario.pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::DialogueOfferState invite = {};
            invite.kind = DialogueOfferKind::RosterJoin;
            invite.npcId = 32;
            invite.rosterId = 2;
            invite.messageTextId = 202;
            invite.partyFullTextId = 203;
            scenario.pEventRuntimeState->dialogueState.currentOffer = invite;

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = 32;
            scenario.pEventRuntimeState->pendingDialogueContext = context;

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept roster join offer";
                return false;
            }

            if (scenario.party.members().size() != 5)
            {
                failure = "expected party size 5 after recruit";
                return false;
            }

            if (!scenario.pEventRuntimeState->unavailableNpcIds.contains(32))
            {
                failure = "Fredrick was not marked unavailable";
                return false;
            }

            if (!dialogContainsText(dialog, "joined the party"))
            {
                failure = "missing join confirmation text";
                return false;
            }

            return true;
        }
    );

    runCase(
        "synthetic_roster_join_full_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const RosterEntry *pExtraMember = gameDataLoader.getRosterTable().get(3);

            if (pExtraMember == nullptr || !scenario.party.recruitRosterMember(*pExtraMember))
            {
                failure = "could not fill party to 5";
                return false;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(202);

            if (inviteText)
            {
                scenario.pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = 32;
            scenario.pEventRuntimeState->pendingDialogueContext = context;

            EventRuntimeState::DialogueOfferState invite = {};
            invite.kind = DialogueOfferKind::RosterJoin;
            invite.npcId = 32;
            invite.rosterId = 2;
            invite.messageTextId = 202;
            invite.partyFullTextId = 203;
            scenario.pEventRuntimeState->dialogueState.currentOffer = invite;

            EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);
            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept full-party offer";
                return false;
            }

            if (scenario.party.members().size() != 5)
            {
                failure = "party size changed unexpectedly";
                return false;
            }

            if (scenario.pEventRuntimeState->unavailableNpcIds.contains(32))
            {
                failure = "Fredrick should remain available after moving to the inn";
                return false;
            }

            const auto movedHouseIt = scenario.pEventRuntimeState->npcHouseOverrides.find(32);

            if (movedHouseIt == scenario.pEventRuntimeState->npcHouseOverrides.end()
                || movedHouseIt->second != AdventurersInnHouseId)
            {
                failure = "Fredrick was not moved to the Adventurer's Inn";
                return false;
            }

            if (!dialogContainsText(dialog, "party's all full up"))
            {
                failure = "missing full-party response text";
                return false;
            }

            EventRuntimeState::PendingDialogueContext innContext = {};
            innContext.kind = DialogueContextKind::HouseService;
            innContext.sourceId = AdventurersInnHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = innContext;
            dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (dialog.title != "Fredrick Talimere" && !dialogHasActionLabel(dialog, "Fredrick Talimere"))
            {
                failure = "Fredrick did not appear in the Adventurer's Inn";
                return false;
            }

            if (dialogHasActionLabel(dialog, "Rent room for 5 gold")
                || dialogHasActionLabel(dialog, "Fill packs to 14 days for 2 gold")
                || dialogHasActionLabel(dialog, "Play Arcomage"))
            {
                failure = "Adventurer's Inn exposed tavern actions";
                return false;
            }

            return true;
        }
    );

    runCase(
        "roster_join_mapping_and_players_can_show_topic",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 9);

            if (!dialogHasActionLabel(dialog, "Dyson Leland"))
            {
                failure = "Sandro should initially expose the Dyson Leland topic";
                return false;
            }

            scenario.pEventRuntimeState->npcTopicOverrides[11][3] = 634;
            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 11);

            const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

            if (!joinIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *joinIndex, dialog))
            {
                failure = "could not open Dyson roster join offer";
                return false;
            }

            if (!dialogContainsText(dialog, "I will gladly join you."))
            {
                failure = "missing Dyson roster join prompt text";
                return false;
            }

            const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

            if (!yesIndex || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *yesIndex, dialog))
            {
                failure = "could not accept Dyson roster join offer";
                return false;
            }

            if (!scenario.party.hasRosterMember(34))
            {
                failure = "Dyson roster member was not added to the party";
                return false;
            }

            dialog = openNpcDialogInScenario(gameDataLoader, *selectedMap, scenario, 9);

            if (dialogHasActionLabel(dialog, "Dyson Leland"))
            {
                failure = "Dyson Leland topic should hide once Dyson is in the party";
                return false;
            }

            return true;
        }
    );

    runCase(
        "inventory_auto_placement_uses_grid_rules",
        [&](std::string &failure)
        {
            Party party = {};
            party.setItemTable(&gameDataLoader.getItemTable());
            party.seed(Party::createDefaultSeed());
            Character *pSeedMember = party.member(0);

            if (pSeedMember != nullptr)
            {
                pSeedMember->inventory.clear();
            }

            if (!party.grantItemToMember(0, 104)
                || !party.grantItemToMember(0, 111)
                || !party.grantItemToMember(0, 25)
                || !party.grantItemToMember(0, 94))
            {
                failure = "could not seed member inventory";
                return false;
            }

            const Character *pMember = party.member(0);

            if (pMember == nullptr)
            {
                failure = "missing member 0";
                return false;
            }

            const auto findItem =
                [pMember](uint32_t objectDescriptionId) -> const InventoryItem *
                {
                    for (const InventoryItem &item : pMember->inventory)
                    {
                        if (item.objectDescriptionId == objectDescriptionId)
                        {
                            return &item;
                        }
                    }

                    return nullptr;
                };

            const InventoryItem *pShield = findItem(104);
            const InventoryItem *pFullHelm = findItem(111);
            const InventoryItem *pFangedBlade = findItem(25);
            const InventoryItem *pBreastplate = findItem(94);

            if (pShield == nullptr || pShield->gridX != 0 || pShield->gridY != 0)
            {
                failure = "2x2 shield did not place at 0,0";
                return false;
            }

            if (pFullHelm == nullptr || pFullHelm->gridX != 0 || pFullHelm->gridY != 2)
            {
                failure = "1x2 helm did not place at 0,2";
                return false;
            }

            if (pFangedBlade == nullptr || pFangedBlade->gridX != 0 || pFangedBlade->gridY != 4)
            {
                failure = "2x3 blade did not place at 0,4";
                return false;
            }

            if (pBreastplate == nullptr || pBreastplate->gridX != 0 || pBreastplate->gridY != 7)
            {
                failure = "3x2 breastplate did not place at 0,7";
                return false;
            }

            return true;
        }
    );

    runCase(
        "inventory_auto_placement_fills_columns_vertically",
        [&](std::string &failure)
        {
            Party party = {};
            party.setItemTable(&gameDataLoader.getItemTable());
            party.seed(Party::createDefaultSeed());
            Character *pSeedMember = party.member(0);

            if (pSeedMember != nullptr)
            {
                pSeedMember->inventory.clear();
            }

            if (!party.grantItemToMember(0, 109, 20))
            {
                failure = "could not seed member inventory with 1x1 items";
                return false;
            }

            const Character *pMember = party.member(0);

            if (pMember == nullptr)
            {
                failure = "missing member 0";
                return false;
            }

            if (pMember->inventoryItemAt(0, 0) == nullptr
                || pMember->inventoryItemAt(0, 8) == nullptr
                || pMember->inventoryItemAt(1, 0) == nullptr
                || pMember->inventoryItemAt(1, 8) == nullptr
                || pMember->inventoryItemAt(2, 0) == nullptr
                || pMember->inventoryItemAt(2, 1) == nullptr)
            {
                failure = "1x1 items did not fill columns from top to bottom";
                return false;
            }

            if (pMember->inventoryItemAt(2, 2) != nullptr)
            {
                failure = "vertical column fill placed too many items into the third column";
                return false;
            }

            return true;
        }
    );

    runCase(
        "inventory_move_accept_reject_and_swap",
        [&](std::string &failure)
        {
            Party party = {};
            party.setItemTable(&gameDataLoader.getItemTable());
            party.seed(Party::createDefaultSeed());
            Character *pSeedMember = party.member(0);

            if (pSeedMember != nullptr)
            {
                pSeedMember->inventory.clear();
            }

            if (!party.grantItemToMember(0, 104) || !party.grantItemToMember(0, 111))
            {
                failure = "could not seed member inventory";
                return false;
            }

            InventoryItem heldItem = {};

            if (!party.takeItemFromMemberInventoryCell(0, 0, 0, heldItem))
            {
                failure = "could not pick up initial 2x2 item";
                return false;
            }

            std::optional<InventoryItem> replacedItem;

            if (!party.tryPlaceItemInMemberInventoryCell(0, heldItem, 4, 4, replacedItem))
            {
                failure = "valid move to empty destination was rejected";
                return false;
            }

            if (replacedItem.has_value())
            {
                failure = "empty destination unexpectedly replaced an item";
                return false;
            }

            const Character *pMember = party.member(0);

            if (pMember == nullptr)
            {
                failure = "missing member 0 after move";
                return false;
            }

            const InventoryItem *pMovedItem = pMember->inventoryItemAt(4, 4);

            if (pMovedItem == nullptr || pMovedItem->objectDescriptionId != 104)
            {
                failure = "moved item not found at accepted destination";
                return false;
            }

            if (!party.takeItemFromMemberInventoryCell(0, 4, 4, heldItem))
            {
                failure = "could not pick moved item back up";
                return false;
            }

            if (party.tryPlaceItemInMemberInventoryCell(0, heldItem, 13, 8, replacedItem))
            {
                failure = "out-of-bounds move should be rejected";
                return false;
            }

            if (!party.tryPlaceItemInMemberInventoryCell(0, heldItem, 0, 2, replacedItem))
            {
                failure = "swap over single destination item was rejected";
                return false;
            }

            if (!replacedItem || replacedItem->objectDescriptionId != 111)
            {
                failure = "swap did not return the displaced helm";
                return false;
            }

            pMember = party.member(0);
            pMovedItem = pMember != nullptr ? pMember->inventoryItemAt(0, 2) : nullptr;

            if (pMovedItem == nullptr || pMovedItem->objectDescriptionId != 104)
            {
                failure = "swapped item not found at destination";
                return false;
            }

            return true;
        }
    );

    runCase(
        "inventory_cross_member_move_and_full_rejection",
        [&](std::string &failure)
        {
            Party party = {};
            party.setItemTable(&gameDataLoader.getItemTable());
            party.seed(Party::createDefaultSeed());
            Character *pSourceMember = party.member(0);
            Character *pDestinationMember = party.member(1);

            if (pSourceMember != nullptr)
            {
                pSourceMember->inventory.clear();
            }

            if (pDestinationMember != nullptr)
            {
                pDestinationMember->inventory.clear();
            }

            if (!party.grantItemToMember(0, 111))
            {
                failure = "could not grant source item";
                return false;
            }

            InventoryItem heldItem = {};

            if (!party.takeItemFromMemberInventoryCell(0, 0, 0, heldItem))
            {
                failure = "could not pick up source item";
                return false;
            }

            std::optional<InventoryItem> replacedItem;

            if (!party.tryPlaceItemInMemberInventoryCell(1, heldItem, 0, 0, replacedItem))
            {
                failure = "cross-member move into empty inventory failed";
                return false;
            }

            if (replacedItem.has_value())
            {
                failure = "cross-member move unexpectedly replaced an item";
                return false;
            }

            const Character *pMember1 = party.member(1);
            const InventoryItem *pTransferredItem =
                pMember1 != nullptr ? pMember1->inventoryItemAt(0, 0) : nullptr;

            if (pTransferredItem == nullptr || pTransferredItem->objectDescriptionId != 111)
            {
                failure = "transferred item not found on destination member";
                return false;
            }

            if (!party.grantItemToMember(0, 104))
            {
                failure = "could not grant second source item";
                return false;
            }

            if (!party.takeItemFromMemberInventoryCell(0, 0, 0, heldItem))
            {
                failure = "could not pick up second source item";
                return false;
            }

            Character *pFullMember = party.member(2);

            if (pFullMember == nullptr)
            {
                failure = "missing full destination member";
                return false;
            }

            pFullMember->inventory.clear();

            for (int gridY = 0; gridY < Character::InventoryHeight; ++gridY)
            {
                for (int gridX = 0; gridX < Character::InventoryWidth; ++gridX)
                {
                    InventoryItem fillerItem = {};
                    fillerItem.objectDescriptionId = 109;
                    fillerItem.quantity = 1;
                    fillerItem.width = 1;
                    fillerItem.height = 1;

                    if (!pFullMember->addInventoryItemAt(
                            fillerItem,
                            static_cast<uint8_t>(gridX),
                            static_cast<uint8_t>(gridY)))
                    {
                        failure = "could not fill destination inventory";
                        return false;
                    }
                }
            }

            if (party.tryPlaceItemInMemberInventoryCell(2, heldItem, 0, 0, replacedItem))
            {
                failure = "move into full destination inventory should be rejected";
                return false;
            }

            if (heldItem.objectDescriptionId != 104)
            {
                failure = "held item changed after failed full-inventory move";
                return false;
            }

            if (pFullMember->inventoryItemCount() != pFullMember->inventoryCapacity())
            {
                failure = "full destination inventory was modified by rejected move";
                return false;
            }

            return true;
        }
    );

    runCase(
        "character_sheet_uses_equipped_items_for_combat_and_ac",
        [&](std::string &failure)
        {
            Character character = {};
            character.level = 5;
            character.might = 20;
            character.intellect = 10;
            character.personality = 10;
            character.endurance = 15;
            character.accuracy = 15;
            character.speed = 15;
            character.luck = 10;
            character.maxHealth = 50;
            character.health = 50;
            character.skills["Sword"] = {"Sword", 2, SkillMastery::Normal};
            character.skills["Bow"] = {"Bow", 3, SkillMastery::Expert};
            character.skills["Shield"] = {"Shield", 1, SkillMastery::Normal};
            character.skills["PlateArmor"] = {"PlateArmor", 1, SkillMastery::Normal};
            character.equipment.mainHand = 2;
            character.equipment.offHand = 99;
            character.equipment.bow = 61;
            character.equipment.armor = 94;

            const CharacterSheetSummary summary =
                GameMechanics::buildCharacterSheetSummary(character, &gameDataLoader.getItemTable());

            if (summary.combat.attack != 6)
            {
                failure = "expected melee attack 6";
                return false;
            }

            if (!summary.combat.shoot || *summary.combat.shoot != 4)
            {
                failure = "expected ranged attack 4";
                return false;
            }

            if (summary.combat.meleeDamageText != "9 - 15")
            {
                failure = "expected melee damage 9 - 15";
                return false;
            }

            if (summary.combat.rangedDamageText != "4 - 8")
            {
                failure = "expected ranged damage 4 - 8";
                return false;
            }

            if (summary.armorClass.actual != 29 || summary.armorClass.base != 29)
            {
                failure = "expected armor class 29 / 29";
                return false;
            }

            return true;
        }
    );

    runCase(
        "character_sheet_uses_na_for_ranged_without_bow",
        [&](std::string &failure)
        {
            Character character = {};
            character.level = 1;
            character.might = 15;
            character.intellect = 10;
            character.personality = 10;
            character.endurance = 15;
            character.accuracy = 15;
            character.speed = 12;
            character.luck = 10;
            character.maxHealth = 40;
            character.health = 40;

            const CharacterSheetSummary summary =
                GameMechanics::buildCharacterSheetSummary(character, &gameDataLoader.getItemTable());

            if (summary.combat.shoot.has_value())
            {
                failure = "ranged attack should be N/A without a bow";
                return false;
            }

            if (summary.combat.rangedDamageText != "N/A")
            {
                failure = "ranged damage should be N/A without a bow";
                return false;
            }

            if (summary.conditionText != "Good")
            {
                failure = "healthy character should show Good condition";
                return false;
            }

            return true;
        }
    );

    runCase(
        "recruit_roster_member_loads_birth_experience_resistances_and_items",
        [&](std::string &failure)
        {
            const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(3);

            if (pRosterEntry == nullptr)
            {
                failure = "missing roster entry";
                return false;
            }

            Party party = {};
            party.setItemTable(&gameDataLoader.getItemTable());

            if (!party.recruitRosterMember(*pRosterEntry))
            {
                failure = "could not recruit roster entry";
                return false;
            }

            const Character *pMember = party.member(0);

            if (pMember == nullptr)
            {
                failure = "missing recruited member";
                return false;
            }

            if (pMember->birthYear != pRosterEntry->birthYear || pMember->experience != pRosterEntry->experience)
            {
                failure = "roster core values not copied to member";
                return false;
            }

            if (pMember->baseResistances.fire != pRosterEntry->baseResistances.fire
                || pMember->baseResistances.body != pRosterEntry->baseResistances.body)
            {
                failure = "roster resistances not copied to member";
                return false;
            }

            if (pMember->inventory.empty())
            {
                failure = "roster starting items not granted to inventory";
                return false;
            }

            return true;
        }
    );

    runCase(
        "gameplay_selection_blocks_impairing_conditions",
        [&](std::string &failure)
        {
            Party party = {};
            party.setItemTable(&gameDataLoader.getItemTable());
            party.seed(Party::createDefaultSeed());

            Character *pMember = party.member(0);

            if (pMember == nullptr)
            {
                failure = "missing member";
                return false;
            }

            const std::array<CharacterCondition, 6> blockedConditions = {
                CharacterCondition::Asleep,
                CharacterCondition::Paralyzed,
                CharacterCondition::Unconscious,
                CharacterCondition::Dead,
                CharacterCondition::Petrified,
                CharacterCondition::Eradicated,
            };

            for (CharacterCondition condition : blockedConditions)
            {
                pMember->conditions.reset();
                pMember->conditions.set(static_cast<size_t>(condition));

                if (party.canSelectMemberInGameplay(0))
                {
                    failure = "impairing condition did not block selection";
                    return false;
                }
            }

            pMember->conditions.reset();
            pMember->conditions.set(static_cast<size_t>(CharacterCondition::Weak));

            if (!party.canSelectMemberInGameplay(0))
            {
                failure = "weak should not block selection";
                return false;
            }

            pMember->conditions.reset();
            pMember->health = 0;

            if (party.canSelectMemberInGameplay(0))
            {
                failure = "zero health should block selection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "empty_house_after_departure",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            scenario.pEventRuntimeState->unavailableNpcIds.insert(32);

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 37))
            {
                failure = "event 37 failed";
                return false;
            }

            const EventDialogContent dialog = buildScenarioDialog(gameDataLoader, *selectedMap, scenario, 0, true);

            if (!dialogContainsText(dialog, "The house is empty."))
            {
                failure = "missing empty-house text";
                return false;
            }

            return true;
        }
    );

    std::cout << "Regression suite summary: passed=" << passedCount << " failed=" << failedCount << '\n';
    return failedCount == 0 ? 0 : 1;
}
}
