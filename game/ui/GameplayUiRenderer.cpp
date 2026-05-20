#include "game/ui/GameplayUiRenderer.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/StringUtils.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <initializer_list>
#include <limits>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float OeMeleeAlertDistance = 307.2f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr int EventNpcPortraitNativeWidth = 63;
constexpr int EventNpcPortraitNativeHeight = 73;
constexpr float EventNpcPortraitUvCropX = 2.0f;
constexpr float EventNpcPortraitUvCropY = 2.0f;
constexpr float TurnBasedIndicatorX = 394.0f;
constexpr float TurnBasedIndicatorY = 288.0f;

enum class PortraitAggroIndicator
{
    Hidden,
    Black,
    Green,
    Yellow,
    Red,
};

enum class ActiveGameplayHudLayout
{
    Overlay,
    Standard,
    Widescreen
};

struct PointerRenderInput
{
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    bool isLeftMousePressed = false;
};

PointerRenderInput pointerRenderInput(const GameplayScreenRuntime &context)
{
    PointerRenderInput input = {};
    const GameplayInputFrame *pInputFrame = context.currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        return input;
    }

    input.mouseX = pInputFrame->pointerX;
    input.mouseY = pInputFrame->pointerY;
    input.isLeftMousePressed = pInputFrame->leftMouseButton.held;
    return input;
}

std::string turnBasedIndicatorAnimationName(const TurnBasedCombatRuntime &turnBasedRuntime)
{
    if (!turnBasedRuntime.active())
    {
        return {};
    }

    switch (turnBasedRuntime.stage())
    {
        case TurnBasedCombatStage::Attack:
            return "turnstop";
        case TurnBasedCombatStage::Movement:
        {
            const int spentMovementSteps = std::clamp(5 - turnBasedRuntime.movementActionPoints() / 26, 0, 4);
            return "turn" + std::to_string(spentMovementSteps);
        }
        case TurnBasedCombatStage::Wait:
            return "turnhour";
        case TurnBasedCombatStage::None:
        default:
            return {};
    }
}

std::string normalizeGameplayLayoutRoleIdFromNormalized(const std::string &normalizedId);

std::string normalizeGameplayLayoutRoleId(const std::string &layoutId)
{
    std::string normalizedLayoutId = toLowerCopy(layoutId);
    return normalizeGameplayLayoutRoleIdFromNormalized(normalizedLayoutId);
}

std::string normalizeGameplayLayoutRoleIdFromNormalized(const std::string &normalizedId)
{
    std::string normalizedLayoutId = normalizedId;
    constexpr std::string_view standardPrefix = "outdoorstandard";

    if (normalizedLayoutId.rfind(standardPrefix, 0) == 0)
    {
        normalizedLayoutId = "outdoor" + normalizedLayoutId.substr(standardPrefix.size());
    }

    return normalizedLayoutId;
}

std::string npcPortraitTextureName(uint32_t pictureId)
{
    if (pictureId == 0)
    {
        return {};
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "npc%04u", pictureId);
    return buffer;
}

std::optional<size_t> followerPortraitSlotIndex(const std::string &normalizedLayoutId)
{
    constexpr std::string_view prefix = "outdoorfollowerportrait_";

    if (normalizedLayoutId.rfind(prefix, 0) != 0 || normalizedLayoutId.size() != prefix.size() + 1)
    {
        return std::nullopt;
    }

    const char slot = normalizedLayoutId[prefix.size()];
    if (slot < '1' || slot > '3')
    {
        return std::nullopt;
    }

    return static_cast<size_t>(slot - '1');
}

bool isOverlayHudState(GameplayHudScreenState hudScreenState)
{
    return hudScreenState == GameplayHudScreenState::Dialogue
        || hudScreenState == GameplayHudScreenState::Character
        || hudScreenState == GameplayHudScreenState::Chest
        || hudScreenState == GameplayHudScreenState::Spellbook
        || hudScreenState == GameplayHudScreenState::Rest
        || hudScreenState == GameplayHudScreenState::Menu
        || hudScreenState == GameplayHudScreenState::Controls
        || hudScreenState == GameplayHudScreenState::Keyboard
        || hudScreenState == GameplayHudScreenState::VideoOptions
        || hudScreenState == GameplayHudScreenState::SaveGame
        || hudScreenState == GameplayHudScreenState::LoadGame
        || hudScreenState == GameplayHudScreenState::Journal
        || hudScreenState == GameplayHudScreenState::QuickReference;
}

const char *basebarLayoutIdForHudLayout(ActiveGameplayHudLayout layout)
{
    switch (layout)
    {
    case ActiveGameplayHudLayout::Overlay:
        return "OutdoorBasebar";

    case ActiveGameplayHudLayout::Standard:
        return "OutdoorStandardBasebar";

    case ActiveGameplayHudLayout::Widescreen:
        return "OutdoorGameplayBasebar";
    }

    return "OutdoorGameplayBasebar";
}

const char *partyStripLayoutIdForHudLayout(ActiveGameplayHudLayout layout)
{
    switch (layout)
    {
    case ActiveGameplayHudLayout::Overlay:
        return "OutdoorPartyStrip";

    case ActiveGameplayHudLayout::Standard:
        return "OutdoorStandardPartyStrip";

    case ActiveGameplayHudLayout::Widescreen:
        return "OutdoorGameplayPartyStrip";
    }

    return "OutdoorGameplayPartyStrip";
}

int outdoorMinimapArrowIndex(float yawRadians)
{
    float normalizedYaw = std::fmod(yawRadians, Pi * 2.0f);

    if (normalizedYaw < 0.0f)
    {
        normalizedYaw += Pi * 2.0f;
    }

    const int octant = static_cast<int>(std::floor((normalizedYaw + Pi * 0.125f) / (Pi * 0.25f))) % 8;
    return (octant + 7) % 8;
}

float outdoorMinimapArrowYawRadians(const GameplayScreenRuntime &context)
{
    return context.gameplayMinimapArrowYawRadians();
}

float nearestHostileActorDistanceToParty(const IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime == nullptr)
    {
        return std::numeric_limits<float>::max();
    }

    const float partyX = pWorldRuntime->partyX();
    const float partyY = pWorldRuntime->partyY();
    const float partyFootZ = pWorldRuntime->partyFootZ();
    float nearestHostileDistance = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!pWorldRuntime->actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible
            || !actorState.hostileToParty)
        {
            continue;
        }

        const float deltaX = actorState.preciseX - partyX;
        const float deltaY = actorState.preciseY - partyY;
        const float deltaZ = actorState.preciseZ - partyFootZ;
        const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, centerDistance - static_cast<float>(actorState.radius));
        nearestHostileDistance = std::min(nearestHostileDistance, edgeDistance);
    }

    return nearestHostileDistance;
}

PortraitAggroIndicator classifyPortraitAggroIndicator(const Character &member, float nearestHostileDistance)
{
    if (!GameMechanics::canAct(member))
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (member.recoverySecondsRemaining > 0.0f)
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (nearestHostileDistance < OeMeleeAlertDistance)
    {
        return PortraitAggroIndicator::Red;
    }

    if (nearestHostileDistance < OeYellowAlertDistance)
    {
        return PortraitAggroIndicator::Yellow;
    }

    return PortraitAggroIndicator::Green;
}

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolveLayout(
    GameplayScreenRuntime &context,
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight,
    int screenWidth,
    int screenHeight)
{
    return context.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

void submitQuad(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    if (!bgfx::isValid(texture.textureHandle) || quadWidth <= 0.0f || quadHeight <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = quadWidth;
    quad.height = quadHeight;
    queuedHudQuads.push_back(quad);
}

void submitQuadUv(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1)
{
    if (!bgfx::isValid(texture.textureHandle) || quadWidth <= 0.0f || quadHeight <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = quadWidth;
    quad.height = quadHeight;
    quad.u0 = u0;
    quad.v0 = v0;
    quad.u1 = u1;
    quad.v1 = v1;
    queuedHudQuads.push_back(quad);
}

void submitQuadClipped(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    uint16_t scissorX,
    uint16_t scissorY,
    uint16_t scissorWidth,
    uint16_t scissorHeight)
{
    if (!bgfx::isValid(texture.textureHandle) || quadWidth <= 0.0f || quadHeight <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = quadWidth;
    quad.height = quadHeight;
    quad.clipped = true;
    quad.scissorX = scissorX;
    quad.scissorY = scissorY;
    quad.scissorWidth = scissorWidth;
    quad.scissorHeight = scissorHeight;
    queuedHudQuads.push_back(quad);
}

void submitLineClipped(
    std::vector<GameplayHudBatchQuad> &queuedHudQuads,
    const GameplayHudTextureHandle &texture,
    float x0,
    float y0,
    float x1,
    float y1,
    float thickness,
    uint16_t scissorX,
    uint16_t scissorY,
    uint16_t scissorWidth,
    uint16_t scissorHeight)
{
    if (!bgfx::isValid(texture.textureHandle) || thickness <= 0.0f)
    {
        return;
    }

    GameplayHudBatchQuad quad = {};
    quad.textureHandle = texture.textureHandle;
    quad.x = x0;
    quad.y = y0;
    quad.x2 = x1;
    quad.y2 = y1;
    quad.width = thickness;
    quad.height = thickness;
    quad.line = true;
    quad.clipped = true;
    quad.scissorX = scissorX;
    quad.scissorY = scissorY;
    quad.scissorWidth = scissorWidth;
    quad.scissorHeight = scissorHeight;
    queuedHudQuads.push_back(quad);
}

bool isBuffLayoutVisible(const Party &party, const std::string &layoutId)
{
    const std::string normalizedLayoutId = normalizeGameplayLayoutRoleId(layoutId);

    if (normalizedLayoutId == "outdoorbuffskullpanel" || normalizedLayoutId == "outdoorbuffbodypanel")
    {
        return true;
    }

    if (normalizedLayoutId == "outdoorbuffskull_torchlight")
    {
        return party.hasPartyBuff(PartyBuffId::TorchLight);
    }

    if (normalizedLayoutId == "outdoorbuffskull_wizardeye")
    {
        return party.hasPartyBuff(PartyBuffId::WizardEye);
    }

    if (normalizedLayoutId == "outdoorbuffskull_featherfall")
    {
        return party.hasPartyBuff(PartyBuffId::FeatherFall);
    }

    if (normalizedLayoutId == "outdoorbuffskull_detectlife")
    {
        return party.hasPartyBuff(PartyBuffId::DetectLife);
    }

    if (normalizedLayoutId == "outdoorbuffskull_waterwalk")
    {
        return party.hasPartyBuff(PartyBuffId::WaterWalk);
    }

    if (normalizedLayoutId == "outdoorbuffskull_fly")
    {
        return party.hasPartyBuff(PartyBuffId::Fly);
    }

    if (normalizedLayoutId == "outdoorbuffskull_invisibility")
    {
        return party.hasPartyBuff(PartyBuffId::Invisibility);
    }

    if (normalizedLayoutId == "outdoorbuffskull_immolation")
    {
        return party.hasPartyBuff(PartyBuffId::Immolation);
    }

    if (normalizedLayoutId == "outdoorflybufficon")
    {
        return party.hasPartyBuff(PartyBuffId::Fly);
    }

    if (normalizedLayoutId == "outdoorbuffskull_stoneskin")
    {
        return party.hasPartyBuff(PartyBuffId::Stoneskin);
    }

    if (normalizedLayoutId == "outdoorbuffskull_dayofgods")
    {
        return party.hasPartyBuff(PartyBuffId::DayOfGods);
    }

    if (normalizedLayoutId == "outdoorbuffskull_protectionfromgods")
    {
        return party.hasPartyBuff(PartyBuffId::ProtectionFromMagic);
    }

    if (normalizedLayoutId == "outdoorbuffbody_fireresistance")
    {
        return party.hasPartyBuff(PartyBuffId::FireResistance);
    }

    if (normalizedLayoutId == "outdoorbuffbody_waterresistance")
    {
        return party.hasPartyBuff(PartyBuffId::WaterResistance);
    }

    if (normalizedLayoutId == "outdoorbuffbody_airresistance")
    {
        return party.hasPartyBuff(PartyBuffId::AirResistance);
    }

    if (normalizedLayoutId == "outdoorbuffbody_earthresistance")
    {
        return party.hasPartyBuff(PartyBuffId::EarthResistance);
    }

    if (normalizedLayoutId == "outdoorbuffbody_mindresistance")
    {
        return party.hasPartyBuff(PartyBuffId::MindResistance);
    }

    if (normalizedLayoutId == "outdoorbuffbody_bodyresistance")
    {
        return party.hasPartyBuff(PartyBuffId::BodyResistance);
    }

    if (normalizedLayoutId == "outdoorbuffbody_shield")
    {
        return party.hasPartyBuff(PartyBuffId::Shield);
    }

    if (normalizedLayoutId == "outdoorbuffbody_heroism")
    {
        return party.hasPartyBuff(PartyBuffId::Heroism);
    }

    if (normalizedLayoutId == "outdoorbuffbody_haste")
    {
        return party.hasPartyBuff(PartyBuffId::Haste);
    }

    if (normalizedLayoutId == "outdoorbuffbody_immolation")
    {
        return party.hasPartyBuff(PartyBuffId::Immolation);
    }

    if (normalizedLayoutId.rfind("outdoorbuffskull_", 0) == 0
        || normalizedLayoutId.rfind("outdoorbuffbody_", 0) == 0)
    {
        return false;
    }

    return true;
}

bool isDescendantOfAny(
    GameplayScreenRuntime &context,
    const UiLayoutManager::LayoutElement &layout,
    std::initializer_list<std::string_view> ancestorIds)
{
    const UiLayoutManager::LayoutElement *pCurrent = &layout;

    while (pCurrent != nullptr)
    {
        const std::string normalizedLayoutId =
            !pCurrent->normalizedId.empty() ? pCurrent->normalizedId : toLowerCopy(pCurrent->id);

        for (std::string_view ancestorId : ancestorIds)
        {
            if (normalizedLayoutId == ancestorId)
            {
                return true;
            }
        }

        if (pCurrent->parentId.empty())
        {
            break;
        }

        pCurrent = context.findHudLayoutElement(pCurrent->parentId);
    }

    return false;
}

bool isGameplayElementVisibleInHudState(
    GameplayScreenRuntime &context,
    const UiLayoutManager::LayoutElement &layout,
    ActiveGameplayHudLayout gameplayHudLayout)
{
    const std::string normalizedScreen =
        !layout.normalizedScreen.empty() ? layout.normalizedScreen : toLowerCopy(layout.screen);

    if (normalizedScreen != "outdoorhud")
    {
        return false;
    }

    if (gameplayHudLayout == ActiveGameplayHudLayout::Overlay)
    {
        return isDescendantOfAny(context, layout, {"outdoorbasebar"});
    }

    if (gameplayHudLayout == ActiveGameplayHudLayout::Standard)
    {
        return isDescendantOfAny(context, layout, {"outdoorstandardbasebar", "outdoorstandardtopbar"});
    }

    if (isDescendantOfAny(context, layout, {"outdoorfollowerpanel"}))
    {
        return context.interactionState().followerPanelOpen;
    }

    if (isDescendantOfAny(context, layout, {"outdoorfollowertoggle"}))
    {
        return true;
    }

    return isDescendantOfAny(
        context,
        layout,
        {
            "outdoorgameplaybasebar",
            "outdooroptionsbar",
            "outdoorgoldbar",
            "outdoorfoodrestbar",
            "outdoorflybufficon",
            "outdoorbuffbodypanel",
            "outdoorbuffskullpanel",
            "outdoorminimapframe",
            "outdoormobileactionpanel",
            "outdoormobilesystempanel",
            "outdoormobilemovementzone",
        });
}
} // namespace

void GameplayUiRenderer::renderGameplayHudArt(GameplayScreenRuntime &context, int width, int height)
{
    Party *pParty = context.party();

    if (pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayHudScreenState hudScreenState = context.currentHudScreenState();
    const ActiveGameplayHudLayout gameplayHudLayout = isOverlayHudState(hudScreenState)
        ? ActiveGameplayHudLayout::Overlay
#if defined(__ANDROID__)
        : ActiveGameplayHudLayout::Widescreen;
#else
        : (context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? ActiveGameplayHudLayout::Standard
            : ActiveGameplayHudLayout::Widescreen);
#endif
    const bool useGameplayWideHud = gameplayHudLayout == ActiveGameplayHudLayout::Widescreen;
    const std::string basebarLayoutId = basebarLayoutIdForHudLayout(gameplayHudLayout);
    const std::string partyStripLayoutId = partyStripLayoutIdForHudLayout(gameplayHudLayout);
    const UiLayoutManager::LayoutElement *pBasebarLayout = context.findHudLayoutElement(basebarLayoutId);
    const UiLayoutManager::LayoutElement *pPartyStripLayout = context.findHudLayoutElement(partyStripLayoutId);

    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return;
    }

    const std::optional<GameplayHudTextureHandle> basebar =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pBasebarLayout->primaryAsset);
    const std::optional<GameplayHudTextureHandle> gameplayBasebarEnder =
        useGameplayWideHud ? context.gameplayUiRuntime().ensureHudTextureLoaded("Basebar_ender") : std::nullopt;
    const std::optional<GameplayHudTextureHandle> faceMask =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pPartyStripLayout->primaryAsset);
    const std::optional<GameplayHudTextureHandle> selectionRing =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pPartyStripLayout->secondaryAsset);
    const std::optional<GameplayHudTextureHandle> manaFrame =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pPartyStripLayout->tertiaryAsset);
    const std::optional<GameplayHudTextureHandle> healthBar =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pPartyStripLayout->quaternaryAsset);
    const std::optional<GameplayHudTextureHandle> healthBarYellow =
        context.gameplayUiRuntime().ensureHudTextureLoaded("manaY");
    const std::optional<GameplayHudTextureHandle> healthBarRed =
        context.gameplayUiRuntime().ensureHudTextureLoaded("manar");
    const std::optional<GameplayHudTextureHandle> manaBar =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pPartyStripLayout->quinaryAsset);
    const std::optional<GameplayHudTextureHandle> aggroBlack =
        context.gameplayUiRuntime().ensureHudTextureLoaded("statBL");
    const std::optional<GameplayHudTextureHandle> aggroRed =
        context.gameplayUiRuntime().ensureHudTextureLoaded("statR");
    const std::optional<GameplayHudTextureHandle> aggroYellow =
        context.gameplayUiRuntime().ensureHudTextureLoaded("statY");
    const std::optional<GameplayHudTextureHandle> aggroGreen =
        context.gameplayUiRuntime().ensureHudTextureLoaded("statG");
    const std::optional<GameplayHudTextureHandle> blessIcon =
        context.gameplayUiRuntime().ensureHudTextureLoaded("IB_spelico");
    const Party *pPartyReadOnly = context.partyReadOnly();

    if (!basebar || !faceMask || pPartyReadOnly == nullptr)
    {
        return;
    }

    const Party &party = *pPartyReadOnly;
    const std::vector<Character> &members = party.members();

    if (members.empty())
    {
        return;
    }

    context.fxService().consumePendingEventFxRequests(context);

    const std::optional<GameplayResolvedHudLayoutElement> resolvedBasebar = resolveLayout(
        context,
        basebarLayoutId,
        static_cast<float>(basebar->width),
        static_cast<float>(basebar->height),
        width,
        height);
    const std::optional<GameplayResolvedHudLayoutElement> resolvedPartyStrip = resolveLayout(
        context,
        partyStripLayoutId,
        static_cast<float>(basebar->width),
        static_cast<float>(basebar->height),
        width,
        height);

    if (!resolvedBasebar || !resolvedPartyStrip)
    {
        return;
    }

    const float uiScale = resolvedBasebar->scale;
    const float basebarWidth = resolvedBasebar->width;
    const float basebarHeight = resolvedBasebar->height;
    const float basebarX = resolvedBasebar->x;
    const float basebarY = resolvedBasebar->y;
    float partyStripX = resolvedPartyStrip->x;
    const float partyStripY = resolvedPartyStrip->y;
    const float partyStripWidth = resolvedPartyStrip->width;
    const float partyStripHeight = resolvedPartyStrip->height;
    const float portraitWidth = faceMask->width * uiScale;
    const float portraitHeight = faceMask->height * uiScale;
    const size_t displayedMemberCount = members.size();
    float renderedBasebarX = basebarX;
    float renderedBasebarWidth = basebarWidth;
    float portraitStartX = partyStripX + partyStripWidth * (20.0f / 471.0f);
    float portraitY = partyStripY + partyStripHeight * (23.0f / 92.0f);
    const float portraitDeltaX = partyStripWidth * (94.0f / 471.0f);
    std::vector<GameplayHudBatchQuad> queuedHudQuads;
    queuedHudQuads.reserve(256);
    const auto flushQueuedHudQuads =
        [&context, &queuedHudQuads, width, height]()
        {
            if (queuedHudQuads.empty())
            {
                return;
            }

            context.prepareHudView(width, height);
            context.submitHudQuadBatch(queuedHudQuads, width, height);
            queuedHudQuads.clear();
        };

    if (useGameplayWideHud)
    {
        const float partyFraction = std::clamp(static_cast<float>(displayedMemberCount) / 5.0f, 0.2f, 1.0f);
        const float basebarCenterX = basebarX + basebarWidth * 0.5f;
        renderedBasebarWidth = basebarWidth * partyFraction;
        renderedBasebarX = basebarCenterX - renderedBasebarWidth * 0.5f;
        partyStripX = renderedBasebarX;
        const float portraitGroupWidth =
            portraitWidth + static_cast<float>(displayedMemberCount - 1) * portraitDeltaX;
        portraitStartX = basebarCenterX - portraitGroupWidth * 0.5f;
        portraitY -= 15.0f * uiScale;
    }

    const PointerRenderInput pointerInput = pointerRenderInput(context);
    const float characterMouseX = pointerInput.mouseX;
    const float characterMouseY = pointerInput.mouseY;
    const bool isLeftMousePressed = pointerInput.isLeftMousePressed;

    const auto renderGameplayBasebarLeftAttachment =
        [&](const std::string &layoutId)
        {
            if (!useGameplayWideHud)
            {
                return;
            }

            const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty() || !pLayout->visible)
            {
                return;
            }

            const std::optional<GameplayHudTextureHandle> texture =
                context.gameplayUiRuntime().ensureHudTextureLoaded(pLayout->primaryAsset);

            if (!texture)
            {
                return;
            }

            const float ornamentWidth =
                (pLayout->width > 0.0f ? pLayout->width : static_cast<float>(texture->width)) * uiScale;
            const float ornamentHeight =
                (pLayout->height > 0.0f ? pLayout->height : static_cast<float>(texture->height)) * uiScale;
            const float ornamentX = renderedBasebarX - pLayout->gapX * uiScale;
            const float ornamentY = basebarY + basebarHeight + pLayout->gapY * uiScale;
            submitQuad(queuedHudQuads, *texture, ornamentX, ornamentY, ornamentWidth, ornamentHeight);
        };

    const auto renderGameplayBasebarRightAttachment =
        [&](const std::string &layoutId)
        {
            if (!useGameplayWideHud)
            {
                return;
            }

            const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty() || !pLayout->visible)
            {
                return;
            }

            const std::optional<GameplayHudTextureHandle> texture =
                context.gameplayUiRuntime().ensureHudTextureLoaded(pLayout->primaryAsset);

            if (!texture)
            {
                return;
            }

            const float ornamentWidth =
                (pLayout->width > 0.0f ? pLayout->width : static_cast<float>(texture->width)) * uiScale;
            const float ornamentHeight =
                (pLayout->height > 0.0f ? pLayout->height : static_cast<float>(texture->height)) * uiScale;
            const float ornamentX =
                renderedBasebarX + renderedBasebarWidth - ornamentWidth + pLayout->gapX * uiScale;
            const float ornamentY = basebarY + basebarHeight + pLayout->gapY * uiScale;
            submitQuad(queuedHudQuads, *texture, ornamentX, ornamentY, ornamentWidth, ornamentHeight);
        };

    renderGameplayBasebarLeftAttachment("OutdoorGameplayBasebar_OrnLeft1");
    renderGameplayBasebarLeftAttachment("OutdoorGameplayBasebar_OrnLeft2");
    renderGameplayBasebarRightAttachment("OutdoorGameplayBasebar_OrnRight1");
    renderGameplayBasebarRightAttachment("OutdoorGameplayBasebar_OrnRight2");

    if (useGameplayWideHud)
    {
        const float uSpan = std::clamp(renderedBasebarWidth / basebarWidth, 0.0f, 1.0f);
        submitQuadUv(
            queuedHudQuads,
            *basebar,
            renderedBasebarX,
            basebarY,
            renderedBasebarWidth,
            basebarHeight,
            0.0f,
            0.0f,
            uSpan,
            1.0f);

        if (gameplayBasebarEnder)
        {
            const float enderWidth = static_cast<float>(gameplayBasebarEnder->width) * uiScale;
            const float enderHeight = static_cast<float>(gameplayBasebarEnder->height) * uiScale;
            const float enderX =
                basebarX + basebarWidth * 0.5f + renderedBasebarWidth * 0.5f - 20.0f * uiScale;
            submitQuad(queuedHudQuads, *gameplayBasebarEnder, enderX, basebarY, enderWidth, enderHeight);
        }
    }
    else
    {
        submitQuad(queuedHudQuads, *basebar, basebarX, basebarY, basebarWidth, basebarHeight);
    }

    const size_t activeMemberIndex = party.activeMemberIndex();
    size_t selectedMemberRingIndex = activeMemberIndex;

    if (hudScreenState == GameplayHudScreenState::Character)
    {
        const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();

        if (characterScreen.open && characterScreen.source == GameplayUiController::CharacterScreenSource::Party)
        {
            selectedMemberRingIndex = characterScreen.sourceIndex;
        }
    }

    const Character *pSelectedMember = party.member(selectedMemberRingIndex);
    const bool showSelectedMemberRing = hudScreenState == GameplayHudScreenState::Gameplay
        ? (pSelectedMember != nullptr && GameMechanics::canTakeGameplayAction(*pSelectedMember))
        : pSelectedMember != nullptr;
    const float nearestHostileDistance =
        manaFrame ? nearestHostileActorDistanceToParty(context.worldRuntime()) : std::numeric_limits<float>::max();

    for (size_t memberIndex = 0; memberIndex < displayedMemberCount; ++memberIndex)
    {
        const Character &member = members[memberIndex];
        const float portraitX = portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX;
        const float portraitInset = 2.0f * uiScale;
        const std::optional<GameplayHudTextureHandle> portrait =
            context.gameplayUiRuntime().ensureHudTextureLoaded(context.resolvePortraitTextureName(member));

        if (portrait)
        {
            submitQuad(
                queuedHudQuads,
                *portrait,
                portraitX + portraitInset,
                portraitY + portraitInset,
                portraitWidth - portraitInset * 2.0f,
                portraitHeight - portraitInset * 2.0f);
        }

        flushQueuedHudQuads();
        context.renderPortraitFx(memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
        submitQuad(queuedHudQuads, *faceMask, portraitX, portraitY, portraitWidth, portraitHeight);

        if (showSelectedMemberRing && memberIndex == selectedMemberRingIndex && selectionRing)
        {
            submitQuad(queuedHudQuads, *selectionRing, portraitX - uiScale, portraitY, portraitWidth, portraitHeight);
        }

        if (manaFrame)
        {
            const PortraitAggroIndicator aggroIndicator =
                classifyPortraitAggroIndicator(member, nearestHostileDistance);
            const std::optional<GameplayHudTextureHandle> *pAggroTexture = nullptr;

            switch (aggroIndicator)
            {
            case PortraitAggroIndicator::Black:
                pAggroTexture = &aggroBlack;
                break;
            case PortraitAggroIndicator::Green:
                pAggroTexture = &aggroGreen;
                break;
            case PortraitAggroIndicator::Yellow:
                pAggroTexture = &aggroYellow;
                break;
            case PortraitAggroIndicator::Red:
                pAggroTexture = &aggroRed;
                break;
            case PortraitAggroIndicator::Hidden:
                break;
            }

            if (pAggroTexture != nullptr && *pAggroTexture)
            {
                const float barFrameHeight = manaFrame->height * uiScale;
                const float barFrameY = basebarY + basebarHeight - barFrameHeight - partyStripHeight * (1.0f / 92.0f);
                const float aggroWidth = static_cast<float>((*pAggroTexture)->width) * uiScale;
                const float aggroHeight = static_cast<float>((*pAggroTexture)->height) * uiScale;
                const float aggroX = portraitX - aggroWidth * 0.35f - 8.0f * uiScale;
                const float aggroY = barFrameY + barFrameHeight - aggroHeight;
                submitQuad(queuedHudQuads, **pAggroTexture, aggroX, aggroY, aggroWidth, aggroHeight);
            }
        }

        if (manaFrame)
        {
            const float barFrameX = portraitX + partyStripWidth * (63.0f / 471.0f);
            const float barFrameWidth = manaFrame->width * uiScale;
            const float barFrameHeight = manaFrame->height * uiScale;
            const float barFrameY = basebarY + basebarHeight - barFrameHeight - partyStripHeight * (1.0f / 92.0f);

            if (blessIcon && party.hasCharacterBuff(memberIndex, CharacterBuffId::Bless))
            {
                const float blessIconWidth = static_cast<float>(blessIcon->width) * uiScale;
                const float blessIconHeight = static_cast<float>(blessIcon->height) * uiScale;
                const float blessIconX = barFrameX - blessIconWidth - uiScale;
                const float blessIconY = portraitY + portraitHeight - blessIconHeight + 3.0f * uiScale;
                submitQuad(queuedHudQuads, *blessIcon, blessIconX, blessIconY, blessIconWidth, blessIconHeight);
            }

            submitQuad(queuedHudQuads, *manaFrame, barFrameX, barFrameY, barFrameWidth, barFrameHeight);

            const float fillHeight = 49.0f * uiScale;
            const float fillY = barFrameY + 1.0f * uiScale;
            const float leftFillX = barFrameX + 1.0f * uiScale;
            const float rightFillX = barFrameX + 5.0f * uiScale;
            const float fillWidth = 3.0f * uiScale;
            const int maxHealth = GameMechanics::calculateEffectiveCharacterMaxHealth(member);
            const int maxSpellPoints = GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
            const float healthPercent = (maxHealth > 0)
                ? std::clamp(static_cast<float>(member.health) / static_cast<float>(maxHealth), 0.0f, 1.0f)
                : 0.0f;
            const float manaPercent = (maxSpellPoints > 0)
                ? std::clamp(static_cast<float>(member.spellPoints) / static_cast<float>(maxSpellPoints), 0.0f, 1.0f)
                : 0.0f;
            const GameplayHudTextureHandle *pResolvedHealthBar = healthBar ? &*healthBar : nullptr;

            if (healthPercent > 0.0f)
            {
                if (healthPercent <= 0.25f && healthBarRed)
                {
                    pResolvedHealthBar = &*healthBarRed;
                }
                else if (healthPercent <= 0.5f && healthBarYellow)
                {
                    pResolvedHealthBar = &*healthBarYellow;
                }
            }

            if (pResolvedHealthBar != nullptr && healthPercent > 0.0f)
            {
                submitQuadUv(
                    queuedHudQuads,
                    *pResolvedHealthBar,
                    leftFillX,
                    fillY + (1.0f - healthPercent) * fillHeight,
                    fillWidth,
                    healthPercent * fillHeight,
                    0.0f,
                    1.0f - healthPercent,
                    1.0f,
                    1.0f);
            }

            if (manaBar && manaPercent > 0.0f)
            {
                submitQuadUv(
                    queuedHudQuads,
                    *manaBar,
                    rightFillX,
                    fillY + (1.0f - manaPercent) * fillHeight,
                    fillWidth,
                    manaPercent * fillHeight,
                    0.0f,
                    1.0f - manaPercent,
                    1.0f,
                    1.0f);
            }
        }
    }

    if (gameplayHudLayout != ActiveGameplayHudLayout::Widescreen)
    {
        const std::string shieldPrefix =
            gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardCharShield_" : "CharShield_";

        for (size_t memberIndex = displayedMemberCount; memberIndex < 5; ++memberIndex)
        {
            const std::string slotShieldId = shieldPrefix + std::to_string(memberIndex + 1);
            const UiLayoutManager::LayoutElement *pShieldLayout = context.findHudLayoutElement(slotShieldId);

            if (pShieldLayout == nullptr || pShieldLayout->primaryAsset.empty())
            {
                continue;
            }

            const std::optional<GameplayHudTextureHandle> shieldTexture =
                context.gameplayUiRuntime().ensureHudTextureLoaded(pShieldLayout->primaryAsset);

            if (!shieldTexture)
            {
                continue;
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolvedShield = resolveLayout(
                context,
                slotShieldId,
                pShieldLayout->width > 0.0f ? pShieldLayout->width : static_cast<float>(shieldTexture->width),
                pShieldLayout->height > 0.0f ? pShieldLayout->height : static_cast<float>(shieldTexture->height),
                width,
                height);

            if (!resolvedShield)
            {
                continue;
            }

            submitQuad(
                queuedHudQuads,
                *shieldTexture,
                resolvedShield->x,
                resolvedShield->y,
                resolvedShield->width,
                resolvedShield->height);
        }
    }

    GameplayMinimapState minimapState = {};
    bool hasMinimapState = false;
    GameplayResolvedHudLayoutElement minimapOverlay = {};

    for (const std::string &layoutId : context.sortedHudLayoutIdsForScreen("OutdoorHud"))
    {
        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || !pLayout->visible)
        {
            continue;
        }

        const std::string normalizedLayoutId =
            !pLayout->normalizedId.empty() ? pLayout->normalizedId : toLowerCopy(layoutId);
        const std::string normalizedRoleId = normalizeGameplayLayoutRoleIdFromNormalized(
            normalizedLayoutId);

        if (normalizedLayoutId == "outdoorbasebar"
            || normalizedLayoutId == "outdoorpartystrip"
            || normalizedLayoutId == "outdoorstandardbasebar"
            || normalizedLayoutId == "outdoorstandardpartystrip"
            || normalizedLayoutId == "outdoorstandardstatusbar"
            || normalizedLayoutId == "outdoorgameplaybasebar"
            || normalizedLayoutId == "outdoorgameplaypartystrip"
            || normalizedLayoutId == "outdoorgameplaystatusbar"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornleft1"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornleft2"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornright1"
            || normalizedLayoutId == "outdoorgameplaybasebar_ornright2"
            || normalizedLayoutId.rfind("charshield_", 0) == 0
            || normalizedLayoutId.rfind("outdoorstandardcharshield_", 0) == 0)
        {
            continue;
        }

        if (!isGameplayElementVisibleInHudState(context, *pLayout, gameplayHudLayout)
            || !isBuffLayoutVisible(party, layoutId))
        {
            continue;
        }

        if (normalizedRoleId == "outdoorminimap")
        {
            if (!context.tryGetGameplayMinimapState(minimapState) || pLayout->width <= 0.0f || pLayout->height <= 0.0f)
            {
                continue;
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolved =
                resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);

            if (!resolved)
            {
                continue;
            }

            minimapState.uSpan = std::min(1.0f, pLayout->width / std::max(1.0f, minimapState.zoom));
            minimapState.vSpan = std::min(1.0f, pLayout->height / std::max(1.0f, minimapState.zoom));
            minimapState.u0 = std::clamp(
                minimapState.partyU - minimapState.uSpan * 0.5f,
                0.0f,
                1.0f - minimapState.uSpan);
            minimapState.v0 = std::clamp(
                minimapState.partyV - minimapState.vSpan * 0.5f,
                0.0f,
                1.0f - minimapState.vSpan);

            if (minimapState.vectorBackground)
            {
                const std::optional<GameplayHudTextureHandle> backgroundTexture =
                    context.gameplayUiRuntime().ensureSolidHudTextureLoaded(
                        "__indoor_minimap_background__",
                        minimapState.backgroundColorAbgr);

                if (!backgroundTexture)
                {
                    continue;
                }

                submitQuad(
                    queuedHudQuads,
                    *backgroundTexture,
                    resolved->x,
                    resolved->y,
                    resolved->width,
                    resolved->height);
            }
            else
            {
                const std::optional<GameplayHudTextureHandle> minimapTexture =
                    context.gameplayUiRuntime().ensureHudTextureLoaded(minimapState.textureName);

                if (!minimapTexture)
                {
                    continue;
                }

                submitQuadUv(
                    queuedHudQuads,
                    *minimapTexture,
                    resolved->x,
                    resolved->y,
                    resolved->width,
                    resolved->height,
                    minimapState.u0,
                    minimapState.v0,
                    minimapState.u0 + minimapState.uSpan,
                    minimapState.v0 + minimapState.vSpan);
            }

            minimapOverlay = *resolved;
            hasMinimapState = true;
            continue;
        }

        const std::optional<size_t> followerSlotIndex = followerPortraitSlotIndex(normalizedRoleId);
        if (followerSlotIndex)
        {
            const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
            const EventRuntimeState *pEventRuntimeState =
                pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
            const NpcDialogTable *pNpcDialogTable = context.npcDialogTable();
            const MergedNpcProfessionTable *pNpcProfessionTable = context.mergedNpcProfessionTable();

            if (pEventRuntimeState != nullptr && pNpcDialogTable != nullptr && pNpcProfessionTable != nullptr)
            {
                const Party *pParty = context.partyReadOnly();
                const std::vector<HiredNpcFollowerView> followerViews =
                    buildHiredNpcFollowerViews(
                        *pEventRuntimeState,
                        pParty,
                        *pNpcDialogTable,
                        *pNpcProfessionTable);

                const size_t followerIndex =
                    context.interactionState().followerPanelScrollOffset + *followerSlotIndex;

                if (followerIndex < followerViews.size())
                {
                    const std::string textureName =
                        npcPortraitTextureName(followerViews[followerIndex].portraitPictureId);
                    const std::optional<GameplayHudTextureHandle> texture =
                        !textureName.empty()
                            ? context.gameplayUiRuntime().ensureHudTextureLoaded(textureName)
                            : std::nullopt;
                    const std::optional<GameplayResolvedHudLayoutElement> resolved =
                        resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);

                    if (texture && resolved)
                    {
                        if (texture->width == EventNpcPortraitNativeWidth
                            && texture->height == EventNpcPortraitNativeHeight)
                        {
                            submitQuadUv(
                                queuedHudQuads,
                                *texture,
                                resolved->x,
                                resolved->y,
                                resolved->width,
                                resolved->height,
                                EventNpcPortraitUvCropX / static_cast<float>(EventNpcPortraitNativeWidth),
                                EventNpcPortraitUvCropY / static_cast<float>(EventNpcPortraitNativeHeight),
                                (static_cast<float>(EventNpcPortraitNativeWidth) - EventNpcPortraitUvCropX)
                                    / static_cast<float>(EventNpcPortraitNativeWidth),
                                (static_cast<float>(EventNpcPortraitNativeHeight) - EventNpcPortraitUvCropY)
                                    / static_cast<float>(EventNpcPortraitNativeHeight));
                        }
                        else
                        {
                            submitQuad(
                                queuedHudQuads,
                                *texture,
                                resolved->x,
                                resolved->y,
                                resolved->width,
                                resolved->height);
                        }
                    }
                }
            }

            continue;
        }

        std::string primaryAsset = pLayout->primaryAsset;

        const bool flyBuffIcon = normalizedRoleId == "outdoorflybufficon";

        if (flyBuffIcon)
        {
            const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
            const bool activelyFlying = pWorldRuntime != nullptr && pWorldRuntime->partyIsActivelyFlyingForHud();
            const std::optional<std::string> animationFrame =
                context.gameplayUiRuntime().flyBuffIconAnimationFrameTextureName(activelyFlying, 1);

            if (animationFrame)
            {
                primaryAsset = *animationFrame;
            }
        }

        if (primaryAsset.empty())
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> interactiveResolved =
            resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);
        const std::string *pAssetName = interactiveResolved && !flyBuffIcon
            ? context.resolveInteractiveAssetName(
                *pLayout,
                *interactiveResolved,
                characterMouseX,
                characterMouseY,
                isLeftMousePressed)
            : nullptr;
        std::optional<GameplayHudTextureHandle> texture =
            pAssetName != nullptr ? context.gameplayUiRuntime().ensureHudTextureLoaded(*pAssetName) : std::nullopt;

        if (!texture)
        {
            texture = context.gameplayUiRuntime().ensureHudTextureLoaded(primaryAsset);
        }

        if (!texture)
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> resolved = resolveLayout(
            context,
            layoutId,
            pLayout->width > 0.0f ? pLayout->width : static_cast<float>(texture->width),
            pLayout->height > 0.0f ? pLayout->height : static_cast<float>(texture->height),
            width,
            height);

        if (!resolved)
        {
            continue;
        }

        submitQuad(queuedHudQuads, *texture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    if (hudScreenState == GameplayHudScreenState::Gameplay && hasMinimapState)
    {
        const float minimapCenterX =
            minimapOverlay.x + ((minimapState.partyU - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
        const float minimapCenterY =
            minimapOverlay.y + ((minimapState.partyV - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;
        const float markerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float worldItemMarkerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float projectileMarkerSize = std::max(1.0f, 1.0f * minimapOverlay.scale);
        const float decorationMarkerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float markerHalfSize = markerSize * 0.5f;
        const float worldItemMarkerHalfSize = worldItemMarkerSize * 0.5f;
        const float projectileMarkerHalfSize = projectileMarkerSize * 0.5f;
        const float decorationMarkerHalfSize = decorationMarkerSize * 0.5f;
        const float markerMargin = std::max(2.0f, 2.0f * minimapOverlay.scale);
        const float markerMinX = minimapOverlay.x + markerMargin + markerHalfSize;
        const float markerMaxX = minimapOverlay.x + minimapOverlay.width - markerMargin - markerHalfSize;
        const float markerMinY = minimapOverlay.y + markerMargin + markerHalfSize;
        const float markerMaxY = minimapOverlay.y + minimapOverlay.height - markerMargin - markerHalfSize;
        const uint16_t minimapScissorX =
            static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.x + markerMargin)));
        const uint16_t minimapScissorY =
            static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.y + markerMargin)));
        const uint16_t minimapScissorWidth =
            static_cast<uint16_t>(std::max(1.0f, std::ceil(minimapOverlay.width - markerMargin * 2.0f)));
        const uint16_t minimapScissorHeight =
            static_cast<uint16_t>(std::max(1.0f, std::ceil(minimapOverlay.height - markerMargin * 2.0f)));
        std::vector<GameplayMinimapLineState> minimapLines;
        context.collectGameplayMinimapLines(minimapLines);
        std::unordered_map<uint32_t, std::optional<GameplayHudTextureHandle>> lineTextureByColor;

        for (const GameplayMinimapLineState &line : minimapLines)
        {
            const float lineX0 =
                minimapOverlay.x + ((line.u0 - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
            const float lineY0 =
                minimapOverlay.y + ((line.v0 - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;
            const float lineX1 =
                minimapOverlay.x + ((line.u1 - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
            const float lineY1 =
                minimapOverlay.y + ((line.v1 - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;

            if ((lineX0 < minimapOverlay.x && lineX1 < minimapOverlay.x)
                || (lineX0 > minimapOverlay.x + minimapOverlay.width
                    && lineX1 > minimapOverlay.x + minimapOverlay.width)
                || (lineY0 < minimapOverlay.y && lineY1 < minimapOverlay.y)
                || (lineY0 > minimapOverlay.y + minimapOverlay.height
                    && lineY1 > minimapOverlay.y + minimapOverlay.height))
            {
                continue;
            }

            std::optional<GameplayHudTextureHandle> &lineTexture = lineTextureByColor[line.colorAbgr];

            if (!lineTexture)
            {
                lineTexture = context.gameplayUiRuntime().ensureSolidHudTextureLoaded(
                    "__minimap_line__",
                    line.colorAbgr);
            }

            if (!lineTexture)
            {
                continue;
            }

            submitLineClipped(
                queuedHudQuads,
                *lineTexture,
                lineX0,
                lineY0,
                lineX1,
                lineY1,
                std::max(1.0f, minimapOverlay.scale),
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }

        const std::optional<GameplayHudTextureHandle> friendlyMarkerTexture =
            minimapState.wizardEyeActive
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__minimap_marker_friendly__", 0xff00ff00u)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> hostileMarkerTexture =
            minimapState.wizardEyeActive
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__minimap_marker_hostile__", 0xff0000ffu)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> corpseMarkerTexture =
            minimapState.wizardEyeActive
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__minimap_marker_corpse__", 0xff00ffffu)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> worldItemMarkerTexture =
            minimapState.wizardEyeShowsExpertObjects
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__minimap_marker_world_item__", 0xffff0000u)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> projectileMarkerTexture =
            minimapState.wizardEyeShowsExpertObjects
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__minimap_marker_projectile__", 0xff0000ffu)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> decorationMarkerTexture =
            minimapState.wizardEyeShowsDecorations
                ? context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__minimap_marker_decoration__", 0xffffffffu)
                : std::nullopt;
        std::vector<GameplayMinimapMarkerState> markers;
        context.collectGameplayMinimapMarkers(markers);

        for (const GameplayMinimapMarkerState &marker : markers)
        {
            const GameplayHudTextureHandle *pTexture = nullptr;
            float markerHalfExtent = markerHalfSize;
            float markerDrawSize = markerSize;

            switch (marker.type)
            {
            case GameplayMinimapMarkerType::FriendlyActor:
                pTexture = friendlyMarkerTexture ? &*friendlyMarkerTexture : nullptr;
                break;
            case GameplayMinimapMarkerType::HostileActor:
                pTexture = hostileMarkerTexture ? &*hostileMarkerTexture : nullptr;
                break;
            case GameplayMinimapMarkerType::CorpseActor:
                pTexture = corpseMarkerTexture ? &*corpseMarkerTexture : nullptr;
                break;
            case GameplayMinimapMarkerType::WorldItem:
                pTexture = worldItemMarkerTexture ? &*worldItemMarkerTexture : nullptr;
                markerHalfExtent = worldItemMarkerHalfSize;
                markerDrawSize = worldItemMarkerSize;
                break;
            case GameplayMinimapMarkerType::Projectile:
                pTexture = projectileMarkerTexture ? &*projectileMarkerTexture : nullptr;
                markerHalfExtent = projectileMarkerHalfSize;
                markerDrawSize = projectileMarkerSize;
                break;
            case GameplayMinimapMarkerType::Decoration:
                pTexture = decorationMarkerTexture ? &*decorationMarkerTexture : nullptr;
                markerHalfExtent = decorationMarkerHalfSize;
                markerDrawSize = decorationMarkerSize;
                break;
            }

            if (pTexture == nullptr)
            {
                continue;
            }

            const float markerCenterX =
                minimapOverlay.x + ((marker.u - minimapState.u0) / minimapState.uSpan) * minimapOverlay.width;
            const float markerCenterY =
                minimapOverlay.y + ((marker.v - minimapState.v0) / minimapState.vSpan) * minimapOverlay.height;

            if (markerCenterX < markerMinX
                || markerCenterX > markerMaxX
                || markerCenterY < markerMinY
                || markerCenterY > markerMaxY)
            {
                continue;
            }

            submitQuadClipped(
                queuedHudQuads,
                *pTexture,
                markerCenterX - markerHalfExtent,
                markerCenterY - markerHalfExtent,
                markerDrawSize,
                markerDrawSize,
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }

        const int arrowIndex = outdoorMinimapArrowIndex(outdoorMinimapArrowYawRadians(context));
        const std::optional<GameplayHudTextureHandle> arrowTexture =
            context.gameplayUiRuntime().ensureHudTextureLoaded("MAPDIR" + std::to_string(arrowIndex + 1));

        if (arrowTexture)
        {
            const float arrowWidth = static_cast<float>(arrowTexture->width) * minimapOverlay.scale;
            const float arrowHeight = static_cast<float>(arrowTexture->height) * minimapOverlay.scale;
            submitQuadClipped(
                queuedHudQuads,
                *arrowTexture,
                minimapCenterX - arrowWidth * 0.5f,
                minimapCenterY - arrowHeight * 0.5f,
                arrowWidth,
                arrowHeight,
                minimapScissorX,
                minimapScissorY,
                minimapScissorWidth,
                minimapScissorHeight);
        }
    }

#if defined(__ANDROID__)
    if (hudScreenState == GameplayHudScreenState::Gameplay)
    {
        const GameplayInputFrame *pInputFrame = context.currentGameplayInputFrame();

        if (pInputFrame != nullptr && pInputFrame->mobileJoystickActive)
        {
            const std::optional<GameplayHudTextureHandle> joystickBase =
                context.gameplayUiRuntime().ensureHudTextureLoaded("joystick_base_active");
            const std::optional<GameplayHudTextureHandle> joystickKnob =
                context.gameplayUiRuntime().ensureHudTextureLoaded("joystick_knob_active");

            if (joystickBase && joystickKnob)
            {
                const float baseSize = 128.0f * uiScale;
                const float knobSize = 48.0f * uiScale;
                submitQuad(
                    queuedHudQuads,
                    *joystickBase,
                    pInputFrame->mobileJoystickBaseX - baseSize * 0.5f,
                    pInputFrame->mobileJoystickBaseY - baseSize * 0.5f,
                    baseSize,
                    baseSize);
                submitQuad(
                    queuedHudQuads,
                    *joystickKnob,
                    pInputFrame->mobileJoystickKnobX - knobSize * 0.5f,
                    pInputFrame->mobileJoystickKnobY - knobSize * 0.5f,
                    knobSize,
                    knobSize);
            }
        }
    }
#endif

    if (hudScreenState == GameplayHudScreenState::Gameplay)
    {
        const std::string turnBasedIndicatorAnimation =
            turnBasedIndicatorAnimationName(context.turnBasedCombatRuntime());

        if (!turnBasedIndicatorAnimation.empty())
        {
            const std::optional<std::string> turnBasedIndicatorTextureName =
                context.gameplayUiRuntime().iconAnimationFrameTextureName(
                    turnBasedIndicatorAnimation,
                    context.animationTicks());
            const std::optional<GameplayHudTextureHandle> turnBasedIndicator =
                turnBasedIndicatorTextureName
                    ? context.gameplayUiRuntime().ensureHudTextureLoaded(*turnBasedIndicatorTextureName)
                    : std::nullopt;

            if (turnBasedIndicator)
            {
                submitQuad(
                    queuedHudQuads,
                    *turnBasedIndicator,
                    TurnBasedIndicatorX * uiScale,
                    TurnBasedIndicatorY * uiScale,
                    turnBasedIndicator->width * uiScale,
                    turnBasedIndicator->height * uiScale);
            }
        }
    }

    flushQueuedHudQuads();
}
} // namespace OpenYAMM::Game
