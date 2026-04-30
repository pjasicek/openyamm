#pragma once

#include "game/outdoor/OutdoorGameView.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplayWorldInteraction.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include <bx/math.h>

namespace OpenYAMM::Game
{
class ActorPreviewBillboard;
class OutdoorMapData;

class OutdoorInteractionController
{
    friend class OutdoorWorldRuntime;

public:
    enum class InteractionInputMethod
    {
        Keyboard,
        Mouse,
    };

    enum class FacePickMode
    {
        AnyVisible,
        InteractionActivatable,
    };

    static void rebuildInteractiveDecorationBindings(OutdoorGameView &view);
    static void seedInteractiveDecorationRuntimeStateIfNeeded(OutdoorGameView &view);
    static OutdoorGameView::InspectHit inspectBModelFace(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const bx::Vec3 &rayOrigin,
        const bx::Vec3 &rayDirection,
        float mouseX,
        float mouseY,
        int viewWidth,
        int viewHeight,
        const float *pViewMatrix,
        const float *pProjectionMatrix,
        OutdoorGameView::DecorationPickMode decorationPickMode,
        FacePickMode facePickMode = FacePickMode::AnyVisible);
    static uint16_t resolveDecorationBillboardSpriteId(
        const OutdoorGameView &view,
        const DecorationBillboard &billboard,
        bool &hidden);
    static void buildDecorationBillboardSpatialIndex(OutdoorGameView &view);
    static void collectDecorationBillboardCandidates(
        const OutdoorGameView &view,
        float minX,
        float minY,
        float maxX,
        float maxY,
        std::vector<size_t> &indices);
    static const OutdoorWorldRuntime::MapActorState *runtimeActorStateForBillboard(
        const OutdoorGameView &view,
        const ActorPreviewBillboard &billboard);
    static bool isInteractiveDecorationHidden(const OutdoorGameView &view, size_t entityIndex);
    static std::optional<uint16_t> resolveInteractiveDecorationEventId(
        const OutdoorGameView &view,
        size_t entityIndex);
    static std::optional<size_t> resolveRuntimeActorIndexForInspectHit(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool tryActivateInspectEvent(OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit);

private:
    static OutdoorGameView::InspectHit pickKeyboardInteractionInspectHit(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        int viewWidth,
        int viewHeight,
        const float *pViewMatrix,
        const float *pProjectionMatrix);
    static bool buildInspectRayForScreenPoint(
        float screenX,
        float screenY,
        int viewWidth,
        int viewHeight,
        const float *pViewMatrix,
        const float *pProjectionMatrix,
        bx::Vec3 &rayOrigin,
        bx::Vec3 &rayDirection);
    static const ActorPreviewBillboard *findActorPreviewBillboardForRuntimeActorIndex(
        const OutdoorGameView &view,
        size_t runtimeActorIndex,
        size_t *pBillboardIndex = nullptr);
    static const OutdoorGameView::InteractiveDecorationBinding *findInteractiveDecorationBindingForEntity(
        const OutdoorGameView &view,
        size_t entityIndex);
    static std::optional<std::string> resolveInteractiveDecorationHoverText(
        const OutdoorGameView &view,
        size_t entityIndex);
    static std::optional<std::string> resolveEventTargetHoverStatusText(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static GameplayWorldHit translateInspectHitToGameplayWorldHit(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static GameplayHoverStatusPayload resolveGameplayHoverStatusPayload(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const GameplayWorldPickRequest &request);
    static GameplayWorldHit pickKeyboardInteractionTarget(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const GameplayWorldPickRequest &request);
    static GameplayWorldHit pickHeldItemWorldTarget(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const GameplayWorldPickRequest &request);
    static GameplayWorldHit pickCurrentInteractionTarget(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const GameplayWorldPickRequest &request);
    static GameplayWorldHoverCacheState worldHoverCacheState(const OutdoorGameView &view);
    static GameplayHoverStatusPayload refreshWorldHover(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const GameplayWorldHoverRequest &request);
    static GameplayHoverStatusPayload readCachedWorldHover(OutdoorGameView &view);
    static void clearWorldHover(OutdoorGameView &view);
    static GameplayWorldPickRequest buildWorldPickRequest(
        const OutdoorGameView &view,
        const GameplayWorldPickRequestInput &input);
    static bool worldInspectModeActive(const OutdoorGameView &view);
    static std::optional<GameplayHeldItemDropRequest> buildHeldItemDropRequest(const OutdoorGameView &view);
    static GameplayPartyAttackFrameInput buildPartyAttackFrameInput(
        const OutdoorGameView &view,
        const GameplayWorldPickRequest &pickRequest);
    static std::optional<size_t> resolveSpellActionHoveredActorIndex(const OutdoorGameView &view);
    static std::optional<size_t> resolveClosestVisibleHostileActorIndex(
        const OutdoorGameView &view,
        float sourceX,
        float sourceY,
        float sourceZ);
    static std::optional<bx::Vec3> resolveSpellActionActorTargetPoint(
        const OutdoorGameView &view,
        size_t actorIndex);
    static std::optional<bx::Vec3> resolveQuickCastCursorTargetPoint(
        const OutdoorGameView &view,
        float cursorX,
        float cursorY);
    static std::optional<bx::Vec3> resolveSpellActionForwardGroundTargetPoint(const OutdoorGameView &view);
    static bool canActivateInspectEvent(const OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit);
    static bool canActivateActorInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool inspectHitTargetsLivingHostileActor(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool canActivateWorldItemInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool canActivateContainerInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool canActivateEventTargetInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool isInteractionInspectHitInRange(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canActivateInteractionInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canActivateInteractionActorInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canActivateInteractionWorldItemInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canActivateInteractionContainerInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canActivateInteractionEventTargetInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canDispatchWorldActivation(
        const OutdoorGameView &view,
        const GameplayWorldHit &worldHit,
        InteractionInputMethod inputMethod);
    static bool dispatchWorldActivation(
        OutdoorGameView &view,
        const GameplayWorldHit &worldHit);
    static bool tryActivateActorInspectEvent(OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit);
    static bool tryActivateWorldItemInspectEvent(
        OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool tryActivateContainerInspectEvent(
        OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool tryActivateEventTargetInspectEvent(
        OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static void presentPendingEventDialog(
        OutdoorGameView &view,
        size_t previousMessageCount,
        bool allowNpcFallbackContent);
    static void closeActiveEventDialog(OutdoorGameView &view);
    static void handleDialogueCloseRequest(OutdoorGameView &view);
    static void executeActiveDialogAction(OutdoorGameView &view);
    static void openDebugNpcDialogue(OutdoorGameView &view, uint32_t npcId);
    static void applyGrantedEventItemsToHeldInventory(OutdoorGameView &view);
    static bool requestTravelAutosave(OutdoorGameView &view);
    static void cancelPendingMapTransition(OutdoorGameView &view);
    static bool executeNpcTopicEvent(
        OutdoorGameView &view,
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt);
    static bool tryTriggerLocalEventById(OutdoorGameView &view, uint16_t eventId);

    static bool buildQuickCastInspectRayForScreenPoint(
        const OutdoorGameView &view,
        float screenX,
        float screenY,
        bx::Vec3 &rayOrigin,
        bx::Vec3 &rayDirection);
    static OutdoorGameView::InspectHit inspectHitFromGameplayWorldHit(const GameplayWorldHit &worldHit);
    static GameplayDialogController::Context createGameplayDialogContext(
        OutdoorGameView &view,
        EventRuntimeState &eventRuntimeState,
        const char *reason);
    static std::optional<std::string> resolveEventHintText(const OutdoorGameView &view, uint16_t eventId);
    static const OutdoorBitmapTexture *findDecorationBillboardTexture(
        const OutdoorGameView &view,
        const std::string &textureName);
    static const OutdoorBitmapTexture *findActorBillboardTexture(
        const OutdoorGameView &view,
        const std::string &textureName,
        int16_t paletteId);
    static bool hitTestDecorationBillboard(
        OutdoorGameView &view,
        const DecorationBillboard &billboard,
        uint16_t spriteId,
        const OutdoorGameView::BillboardTextureHandle &texture,
        bool mirrored,
        float mouseX,
        float mouseY,
        int viewWidth,
        int viewHeight,
        const float *pViewMatrix,
        const float *pProjectionMatrix,
        const bx::Vec3 &rayOrigin,
        const bx::Vec3 &rayDirection,
        float &distance);
    static bool hitTestActorBillboard(
        const OutdoorGameView &view,
        const OutdoorWorldRuntime::MapActorState *pRuntimeActor,
        int actorX,
        int actorY,
        int actorZ,
        uint16_t actorHeight,
        uint16_t sourceBillboardHeight,
        uint16_t spriteFrameIndex,
        const std::array<uint16_t, 8> &actionSpriteFrameIndices,
        bool useStaticFrame,
        float mouseX,
        float mouseY,
        int viewWidth,
        int viewHeight,
        const float *pViewMatrix,
        const float *pProjectionMatrix,
        const bx::Vec3 &rayOrigin,
        const bx::Vec3 &rayDirection,
        float &distance,
        bool &usedBillboardHit);
};
} // namespace OpenYAMM::Game
