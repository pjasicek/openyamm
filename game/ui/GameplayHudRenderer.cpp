#include "game/ui/GameplayHudRenderer.h"

#include "game/gameplay/GameMechanics.h"
#include "game/StringUtils.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <limits>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float OutdoorMinimapZoom = 512.0f;
constexpr float OeMeleeAlertDistance = 307.2f;
constexpr float OeYellowAlertDistance = 5120.0f;
constexpr uint32_t LevelDecorationVisibleOnMap = 0x0008;

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

std::string normalizeGameplayLayoutRoleId(const std::string &layoutId)
{
    std::string normalizedLayoutId = toLowerCopy(layoutId);
    constexpr std::string_view standardPrefix = "outdoorstandard";

    if (normalizedLayoutId.rfind(standardPrefix, 0) == 0)
    {
        normalizedLayoutId = "outdoor" + normalizedLayoutId.substr(standardPrefix.size());
    }

    return normalizedLayoutId;
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
        || hudScreenState == GameplayHudScreenState::Journal;
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

const char *statusBarLayoutIdForHudLayout(ActiveGameplayHudLayout layout)
{
    switch (layout)
    {
    case ActiveGameplayHudLayout::Overlay:
        return "OutdoorStatusBar";

    case ActiveGameplayHudLayout::Standard:
        return "OutdoorStandardStatusBar";

    case ActiveGameplayHudLayout::Widescreen:
        return "OutdoorGameplayStatusBar";
    }

    return "OutdoorGameplayStatusBar";
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

PortraitAggroIndicator classifyPortraitAggroIndicator(
    const Character &member,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    if (!GameMechanics::canAct(member))
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (member.recoverySecondsRemaining > 0.0f)
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (pWorldRuntime == nullptr)
    {
        return PortraitAggroIndicator::Hidden;
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

    return true;
}

bool isDescendantOf(
    GameplayScreenRuntime &context,
    const UiLayoutManager::LayoutElement &layout,
    const std::string &ancestorId)
{
    const std::string normalizedAncestorId = toLowerCopy(ancestorId);
    const UiLayoutManager::LayoutElement *pCurrent = &layout;

    while (pCurrent != nullptr)
    {
        if (toLowerCopy(pCurrent->id) == normalizedAncestorId)
        {
            return true;
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
    if (toLowerCopy(layout.screen) != "outdoorhud")
    {
        return false;
    }

    if (gameplayHudLayout == ActiveGameplayHudLayout::Overlay)
    {
        return isDescendantOf(context, layout, "OutdoorBasebar");
    }

    if (gameplayHudLayout == ActiveGameplayHudLayout::Standard)
    {
        return isDescendantOf(context, layout, "OutdoorStandardBasebar")
            || isDescendantOf(context, layout, "OutdoorStandardTopBar");
    }

    return isDescendantOf(context, layout, "OutdoorGameplayBasebar")
        || isDescendantOf(context, layout, "OutdoorOptionsBar")
        || isDescendantOf(context, layout, "OutdoorGoldBar")
        || isDescendantOf(context, layout, "OutdoorFoodRestBar")
        || isDescendantOf(context, layout, "OutdoorBuffBodyPanel")
        || isDescendantOf(context, layout, "OutdoorBuffSkullPanel")
        || isDescendantOf(context, layout, "OutdoorMinimapFrame");
}

} // namespace

void GameplayHudRenderer::renderGameplayHudArt(GameplayScreenRuntime &context, int width, int height)
{
    Party *pParty = context.party();

    if (pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayHudScreenState hudScreenState = context.currentHudScreenState();
    const ActiveGameplayHudLayout gameplayHudLayout = isOverlayHudState(hudScreenState)
        ? ActiveGameplayHudLayout::Overlay
        : (context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? ActiveGameplayHudLayout::Standard
            : ActiveGameplayHudLayout::Widescreen);
    const bool useGameplayWideHud = gameplayHudLayout == ActiveGameplayHudLayout::Widescreen;
    const std::string basebarLayoutId = basebarLayoutIdForHudLayout(gameplayHudLayout);
    const std::string partyStripLayoutId = partyStripLayoutIdForHudLayout(gameplayHudLayout);
    const UiLayoutManager::LayoutElement *pBasebarLayout = context.findHudLayoutElement(basebarLayoutId);
    const UiLayoutManager::LayoutElement *pPartyStripLayout = context.findHudLayoutElement(partyStripLayoutId);

    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return;
    }

    const std::optional<GameplayHudTextureHandle> basebar = context.ensureHudTextureLoaded(pBasebarLayout->primaryAsset);
    const std::optional<GameplayHudTextureHandle> gameplayBasebarEnder =
        useGameplayWideHud ? context.ensureHudTextureLoaded("Basebar_ender") : std::nullopt;
    const std::optional<GameplayHudTextureHandle> faceMask = context.ensureHudTextureLoaded(pPartyStripLayout->primaryAsset);
    const std::optional<GameplayHudTextureHandle> selectionRing =
        context.ensureHudTextureLoaded(pPartyStripLayout->secondaryAsset);
    const std::optional<GameplayHudTextureHandle> manaFrame =
        context.ensureHudTextureLoaded(pPartyStripLayout->tertiaryAsset);
    const std::optional<GameplayHudTextureHandle> healthBar =
        context.ensureHudTextureLoaded(pPartyStripLayout->quaternaryAsset);
    const std::optional<GameplayHudTextureHandle> healthBarYellow = context.ensureHudTextureLoaded("manaY");
    const std::optional<GameplayHudTextureHandle> healthBarRed = context.ensureHudTextureLoaded("manar");
    const std::optional<GameplayHudTextureHandle> manaBar =
        context.ensureHudTextureLoaded(pPartyStripLayout->quinaryAsset);
    const std::optional<GameplayHudTextureHandle> aggroBlack = context.ensureHudTextureLoaded("statBL");
    const std::optional<GameplayHudTextureHandle> aggroRed = context.ensureHudTextureLoaded("statR");
    const std::optional<GameplayHudTextureHandle> aggroYellow = context.ensureHudTextureLoaded("statY");
    const std::optional<GameplayHudTextureHandle> aggroGreen = context.ensureHudTextureLoaded("statG");
    const std::optional<GameplayHudTextureHandle> blessIcon = context.ensureHudTextureLoaded("IB_spelico");
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

    context.consumePendingPortraitEventFxRequests();

    const std::optional<GameplayResolvedHudLayoutElement> resolvedBasebar =
        resolveLayout(context, basebarLayoutId, static_cast<float>(basebar->width), static_cast<float>(basebar->height), width, height);
    const std::optional<GameplayResolvedHudLayoutElement> resolvedPartyStrip =
        resolveLayout(
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

    float characterMouseX = 0.0f;
    float characterMouseY = 0.0f;
    const SDL_MouseButtonFlags characterMouseButtons = SDL_GetMouseState(&characterMouseX, &characterMouseY);
    const bool isLeftMousePressed = (characterMouseButtons & SDL_BUTTON_LMASK) != 0;

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

            const std::optional<GameplayHudTextureHandle> texture = context.ensureHudTextureLoaded(pLayout->primaryAsset);

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

            const std::optional<GameplayHudTextureHandle> texture = context.ensureHudTextureLoaded(pLayout->primaryAsset);

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
        submitQuadUv(queuedHudQuads, *basebar, renderedBasebarX, basebarY, renderedBasebarWidth, basebarHeight, 0.0f, 0.0f, uSpan, 1.0f);

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
    const bool activeMemberReadyForSelection = party.canSelectMemberInGameplay(activeMemberIndex);

    for (size_t memberIndex = 0; memberIndex < displayedMemberCount; ++memberIndex)
    {
        const Character &member = members[memberIndex];
        const float portraitX = portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX;
        const float portraitInset = 2.0f * uiScale;
        const std::optional<GameplayHudTextureHandle> portrait =
            context.ensureHudTextureLoaded(context.resolvePortraitTextureName(member));

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

        if (activeMemberReadyForSelection && memberIndex == activeMemberIndex && selectionRing)
        {
            submitQuad(queuedHudQuads, *selectionRing, portraitX - uiScale, portraitY, portraitWidth, portraitHeight);
        }

        if (manaFrame)
        {
            const PortraitAggroIndicator aggroIndicator =
                classifyPortraitAggroIndicator(member, context.worldRuntime());
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
            const float healthPercent = (member.maxHealth > 0)
                ? std::clamp(static_cast<float>(member.health) / static_cast<float>(member.maxHealth), 0.0f, 1.0f)
                : 0.0f;
            const float manaPercent = (member.maxSpellPoints > 0)
                ? std::clamp(static_cast<float>(member.spellPoints) / static_cast<float>(member.maxSpellPoints), 0.0f, 1.0f)
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
                context.ensureHudTextureLoaded(pShieldLayout->primaryAsset);

            if (!shieldTexture)
            {
                continue;
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolvedShield =
                resolveLayout(
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
        const std::string normalizedLayoutId = toLowerCopy(layoutId);
        const std::string normalizedRoleId = normalizeGameplayLayoutRoleId(layoutId);

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

        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || !pLayout->visible)
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

            const std::optional<GameplayHudTextureHandle> minimapTexture =
                context.ensureHudTextureLoaded(minimapState.textureName);

            if (!minimapTexture)
            {
                continue;
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolved =
                resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);

            if (!resolved)
            {
                continue;
            }

            minimapState.uSpan = std::min(1.0f, pLayout->width / OutdoorMinimapZoom);
            minimapState.vSpan = std::min(1.0f, pLayout->height / OutdoorMinimapZoom);
            minimapState.u0 = std::clamp(minimapState.partyU - minimapState.uSpan * 0.5f, 0.0f, 1.0f - minimapState.uSpan);
            minimapState.v0 = std::clamp(minimapState.partyV - minimapState.vSpan * 0.5f, 0.0f, 1.0f - minimapState.vSpan);
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
            minimapOverlay = *resolved;
            hasMinimapState = true;
            continue;
        }

        if (pLayout->primaryAsset.empty())
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> interactiveResolved =
            resolveLayout(context, layoutId, pLayout->width, pLayout->height, width, height);
        const std::string *pAssetName = interactiveResolved
            ? context.resolveInteractiveAssetName(*pLayout, *interactiveResolved, characterMouseX, characterMouseY, isLeftMousePressed)
            : nullptr;
        std::optional<GameplayHudTextureHandle> texture =
            pAssetName != nullptr ? context.ensureHudTextureLoaded(*pAssetName) : std::nullopt;

        if (!texture)
        {
            texture = context.ensureHudTextureLoaded(pLayout->primaryAsset);
        }

        if (!texture)
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> resolved =
            resolveLayout(
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
        const std::optional<GameplayHudTextureHandle> friendlyMarkerTexture =
            minimapState.wizardEyeActive
                ? context.ensureSolidHudTextureLoaded("__minimap_marker_friendly__", 0xff00ff00u)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> hostileMarkerTexture =
            minimapState.wizardEyeActive
                ? context.ensureSolidHudTextureLoaded("__minimap_marker_hostile__", 0xff0000ffu)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> corpseMarkerTexture =
            minimapState.wizardEyeActive
                ? context.ensureSolidHudTextureLoaded("__minimap_marker_corpse__", 0xff00ffffu)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> worldItemMarkerTexture =
            minimapState.wizardEyeShowsExpertObjects
                ? context.ensureSolidHudTextureLoaded("__minimap_marker_world_item__", 0xffff0000u)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> projectileMarkerTexture =
            minimapState.wizardEyeShowsExpertObjects
                ? context.ensureSolidHudTextureLoaded("__minimap_marker_projectile__", 0xff0000ffu)
                : std::nullopt;
        const std::optional<GameplayHudTextureHandle> decorationMarkerTexture =
            minimapState.wizardEyeShowsMasterDecorations
                ? context.ensureSolidHudTextureLoaded("__minimap_marker_decoration__", 0xffffffffu)
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

        const int arrowIndex = outdoorMinimapArrowIndex(context.gameplayCameraYawRadians());
        const std::optional<GameplayHudTextureHandle> arrowTexture =
            context.ensureHudTextureLoaded("MAPDIR" + std::to_string(arrowIndex + 1));

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

    flushQueuedHudQuads();
}

void GameplayHudRenderer::renderGameplayHud(GameplayScreenRuntime &context, int width, int height)
{
    Party *pParty = context.party();

    if (pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    context.prepareHudView(width, height);
    const Party &party = *pParty;
    const GameplayHudScreenState hudScreenState = context.currentHudScreenState();
    const bool isLimitedOverlayHud = isOverlayHudState(hudScreenState);
    const ActiveGameplayHudLayout gameplayHudLayout = isLimitedOverlayHud
        ? ActiveGameplayHudLayout::Overlay
        : (context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? ActiveGameplayHudLayout::Standard
            : ActiveGameplayHudLayout::Widescreen);
    const bool useGameplayWideHud = gameplayHudLayout == ActiveGameplayHudLayout::Widescreen;
    const bool shouldRenderStatusBar =
        hudScreenState != GameplayHudScreenState::Spellbook
        && hudScreenState != GameplayHudScreenState::Rest
        && hudScreenState != GameplayHudScreenState::Menu
        && hudScreenState != GameplayHudScreenState::Controls
        && hudScreenState != GameplayHudScreenState::Keyboard
        && hudScreenState != GameplayHudScreenState::VideoOptions
        && hudScreenState != GameplayHudScreenState::SaveGame
        && hudScreenState != GameplayHudScreenState::LoadGame
        && hudScreenState != GameplayHudScreenState::Journal;

    const auto replaceAll =
        [](std::string text, const std::string &from, const std::string &to) -> std::string
        {
            size_t position = 0;

            while ((position = text.find(from, position)) != std::string::npos)
            {
                text.replace(position, from.size(), to);
                position += to.size();
            }

            return text;
        };
    const auto resolveCounterLabel =
        [&replaceAll](const std::string &labelText, const std::string &value) -> std::string
        {
            if (labelText.empty())
            {
                return value;
            }

            const std::string replacedGold = replaceAll(labelText, "{gold}", value);
            const std::string replacedFood = replaceAll(replacedGold, "{food}", value);
            return replacedFood == labelText ? value : replacedFood;
        };

    std::string statusBarLabel;

    if (context.statusBarEventRemainingSeconds() > 0.0f && !context.statusBarEventText().empty())
    {
        statusBarLabel = context.statusBarEventText();
    }
    else if (!context.statusBarHoverText().empty())
    {
        statusBarLabel = context.statusBarHoverText();
    }

    if (shouldRenderStatusBar)
    {
        const std::string statusBarLayoutId = statusBarLayoutIdForHudLayout(gameplayHudLayout);
        const UiLayoutManager::LayoutElement *pStatusBarLayout = context.findHudLayoutElement(statusBarLayoutId);

        if (pStatusBarLayout != nullptr)
        {
            float logicalStatusBarWidth = pStatusBarLayout->width > 0.0f ? pStatusBarLayout->width : 360.0f;

            if (useGameplayWideHud && !statusBarLabel.empty())
            {
                logicalStatusBarWidth = std::clamp(
                    context.measureHudTextWidth(pStatusBarLayout->fontName, statusBarLabel)
                        * std::max(0.1f, pStatusBarLayout->textScale)
                        + 6.0f,
                    24.0f,
                    483.0f);
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolvedStatusBar =
                resolveLayout(
                    context,
                    statusBarLayoutId,
                    logicalStatusBarWidth,
                    pStatusBarLayout->height > 0.0f ? pStatusBarLayout->height : 18.0f,
                    width,
                    height);

            if (resolvedStatusBar)
            {
                if (useGameplayWideHud && !statusBarLabel.empty() && !pStatusBarLayout->primaryAsset.empty())
                {
                    const std::optional<GameplayHudTextureHandle> statusBarTexture =
                        context.ensureHudTextureLoaded(pStatusBarLayout->primaryAsset);

                    if (statusBarTexture)
                    {
                        context.submitHudTexturedQuad(
                            *statusBarTexture,
                            resolvedStatusBar->x,
                            resolvedStatusBar->y,
                            resolvedStatusBar->width,
                            resolvedStatusBar->height);
                    }
                }

                context.renderLayoutLabel(*pStatusBarLayout, *resolvedStatusBar, statusBarLabel);
            }
        }
    }

    if (!isLimitedOverlayHud)
    {
        const char *pTopBarLayoutId =
            gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardTopBar" : nullptr;

        if (pTopBarLayoutId != nullptr)
        {
            const UiLayoutManager::LayoutElement *pTopBarLayout = context.findHudLayoutElement(pTopBarLayoutId);

            if (pTopBarLayout != nullptr)
            {
                const std::optional<GameplayResolvedHudLayoutElement> topBar =
                    resolveLayout(
                        context,
                        pTopBarLayoutId,
                        pTopBarLayout->width > 0.0f ? pTopBarLayout->width : 640.0f,
                        pTopBarLayout->height > 0.0f ? pTopBarLayout->height : 29.0f,
                        width,
                        height);

                if (topBar && !pTopBarLayout->labelText.empty())
                {
                    const std::string label = replaceAll(
                        replaceAll(pTopBarLayout->labelText, "{gold}", std::to_string(party.gold())),
                        "{food}",
                        std::to_string(party.food()));
                    context.renderLayoutLabel(*pTopBarLayout, *topBar, label);
                }
            }
        }

        const char *pGoldLabelLayoutId = gameplayHudLayout == ActiveGameplayHudLayout::Standard
            ? "OutdoorStandardGoldLabel"
            : "OutdoorGoldLabel";
        const UiLayoutManager::LayoutElement *pGoldLabelLayout = context.findHudLayoutElement(pGoldLabelLayoutId);

        if (pGoldLabelLayout != nullptr)
        {
            const std::optional<GameplayResolvedHudLayoutElement> goldLabel =
                resolveLayout(
                    context,
                    pGoldLabelLayoutId,
                    pGoldLabelLayout->width > 0.0f ? pGoldLabelLayout->width : 28.0f,
                    pGoldLabelLayout->height > 0.0f ? pGoldLabelLayout->height : 14.0f,
                    width,
                    height);

            if (goldLabel)
            {
                context.renderLayoutLabel(
                    *pGoldLabelLayout,
                    *goldLabel,
                    resolveCounterLabel(pGoldLabelLayout->labelText, std::to_string(party.gold())));
            }
        }

        const char *pFoodLabelLayoutId = gameplayHudLayout == ActiveGameplayHudLayout::Standard
            ? "OutdoorStandardFoodLabel"
            : "OutdoorFoodLabel";
        const UiLayoutManager::LayoutElement *pFoodLabelLayout = context.findHudLayoutElement(pFoodLabelLayoutId);

        if (pFoodLabelLayout != nullptr)
        {
            const std::optional<GameplayResolvedHudLayoutElement> foodLabel =
                resolveLayout(
                    context,
                    pFoodLabelLayoutId,
                    pFoodLabelLayout->width > 0.0f ? pFoodLabelLayout->width : 28.0f,
                    pFoodLabelLayout->height > 0.0f ? pFoodLabelLayout->height : 14.0f,
                    width,
                    height);

            if (foodLabel)
            {
                context.renderLayoutLabel(
                    *pFoodLabelLayout,
                    *foodLabel,
                    resolveCounterLabel(pFoodLabelLayout->labelText, std::to_string(party.food())));
            }
        }
    }

    if (isLimitedOverlayHud)
    {
        return;
    }

    const UiLayoutManager::LayoutElement *pBottomLeftButtonsLayout =
        context.findHudLayoutElement("OutdoorBottomLeftButtons");

    if (pBottomLeftButtonsLayout != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> bottomLeftButtons =
            resolveLayout(context, "OutdoorBottomLeftButtons", 180.0f, 32.0f, width, height);

        if (bottomLeftButtons)
        {
            context.renderLayoutLabel(
                *pBottomLeftButtonsLayout,
                *bottomLeftButtons,
                pBottomLeftButtonsLayout->labelText);
        }
    }

    const std::string skullPanelLayoutId =
        gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardBuffSkullPanel" : "OutdoorBuffSkullPanel";
    const UiLayoutManager::LayoutElement *pSkullPanelLayout = context.findHudLayoutElement(skullPanelLayoutId);

    if (pSkullPanelLayout != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> skullPanel =
            resolveLayout(context, skullPanelLayoutId, 96.0f, 48.0f, width, height);

        if (skullPanel)
        {
            context.renderLayoutLabel(*pSkullPanelLayout, *skullPanel, pSkullPanelLayout->labelText);
        }
    }

    const std::string bodyPanelLayoutId =
        gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardBuffBodyPanel" : "OutdoorBuffBodyPanel";
    const UiLayoutManager::LayoutElement *pBodyPanelLayout = context.findHudLayoutElement(bodyPanelLayoutId);

    if (pBodyPanelLayout != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> bodyPanel =
            resolveLayout(context, bodyPanelLayoutId, 96.0f, 48.0f, width, height);

        if (bodyPanel)
        {
            context.renderLayoutLabel(*pBodyPanelLayout, *bodyPanel, pBodyPanelLayout->labelText);
        }
    }
}
} // namespace OpenYAMM::Game
