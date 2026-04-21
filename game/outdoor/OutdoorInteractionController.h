#pragma once

#include "game/outdoor/OutdoorGameView.h"

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
    static const ActorPreviewBillboard *findActorPreviewBillboardForRuntimeActorIndex(
        const OutdoorGameView &view,
        size_t runtimeActorIndex,
        size_t *pBillboardIndex = nullptr);
    static const OutdoorGameView::InteractiveDecorationBinding *findInteractiveDecorationBindingForEntity(
        const OutdoorGameView &view,
        size_t entityIndex);
    static bool isInteractiveDecorationHidden(const OutdoorGameView &view, size_t entityIndex);
    static std::optional<uint16_t> resolveInteractiveDecorationEventId(
        const OutdoorGameView &view,
        size_t entityIndex);
    static std::optional<std::string> resolveInteractiveDecorationHoverText(
        const OutdoorGameView &view,
        size_t entityIndex);
    static std::optional<std::string> resolveHoverStatusBarText(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit);
    static bool canActivateInspectEvent(const OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit);
    static bool isInteractionInspectHitInRange(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool canActivateInteractionInspectEvent(
        const OutdoorGameView &view,
        const OutdoorGameView::InspectHit &inspectHit,
        InteractionInputMethod inputMethod);
    static bool tryActivateInspectEvent(OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit);

    static void presentPendingEventDialog(
        OutdoorGameView &view,
        size_t previousMessageCount,
        bool allowNpcFallbackContent);
    static void closeActiveEventDialog(OutdoorGameView &view);
    static void handleDialogueCloseRequest(OutdoorGameView &view);
    static void executeActiveDialogAction(OutdoorGameView &view);
    static void openDebugNpcDialogue(OutdoorGameView &view, uint32_t npcId);
    static void applyGrantedEventItemsToHeldInventory(OutdoorGameView &view);
    static bool tryTriggerLocalEventById(OutdoorGameView &view, uint16_t eventId);
    static void applyPendingCombatEvents(OutdoorGameView &view);

private:
    static void setHeldInventoryItem(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        const InventoryItem &item);
    static bool tryDisplaceHeldInventoryItem(OutdoorGameView &view);
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
