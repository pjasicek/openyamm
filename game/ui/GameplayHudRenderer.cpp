#include "game/ui/GameplayHudRenderer.h"

#include "game/gameplay/GameMechanics.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/StringUtils.h"
#include "game/ui/HudUiService.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;
constexpr float Pi = 3.14159265358979323846f;
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr float OutdoorMinimapZoom = 512.0f;
constexpr float OeMeleeAlertDistance = 307.2f;
constexpr float OeYellowAlertDistance = 5120.0f;

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

enum class PortraitAggroIndicator
{
    Hidden,
    Black,
    Green,
    Yellow,
    Red,
};

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
    viewport.width = static_cast<float>(screenWidth);
    viewport.height = static_cast<float>(screenHeight);

    if (screenHeight > 0)
    {
        const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

        if (viewport.width > maxWidthForHeight)
        {
            viewport.width = maxWidthForHeight;
            viewport.x = (static_cast<float>(screenWidth) - viewport.width) * 0.5f;
        }
    }

    return viewport;
}

PortraitAggroIndicator classifyPortraitAggroIndicator(
    const Character &member,
    const OutdoorPartyRuntime *pPartyRuntime,
    const OutdoorWorldRuntime *pWorldRuntime)
{
    if (!GameMechanics::canAct(member))
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (member.recoverySecondsRemaining > 0.0f)
    {
        return PortraitAggroIndicator::Hidden;
    }

    if (pPartyRuntime == nullptr || pWorldRuntime == nullptr)
    {
        return PortraitAggroIndicator::Hidden;
    }

    const OutdoorMoveState &partyMoveState = pPartyRuntime->movementState();
    float nearestHostileDistance = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = pWorldRuntime->mapActorState(actorIndex);

        if (pActor == nullptr || pActor->isDead || pActor->isInvisible || !pActor->hostileToParty)
        {
            continue;
        }

        const float actorX = pActor->preciseX != 0.0f ? pActor->preciseX : static_cast<float>(pActor->x);
        const float actorY = pActor->preciseY != 0.0f ? pActor->preciseY : static_cast<float>(pActor->y);
        const float actorZ = pActor->movementStateInitialized
            ? pActor->movementState.footZ
            : (pActor->preciseZ != 0.0f ? pActor->preciseZ : static_cast<float>(pActor->z));
        const float deltaX = actorX - partyMoveState.x;
        const float deltaY = actorY - partyMoveState.y;
        const float deltaZ = actorZ - partyMoveState.footZ;
        const float centerDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, centerDistance - static_cast<float>(pActor->radius));
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

} // namespace

void GameplayHudRenderer::renderGameplayHudArt(OutdoorGameView &view, int width, int height)
{
    if (view.m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_programHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pBasebarLayout = HudUiService::findHudLayoutElement(view, "OutdoorBasebar");
    const OutdoorGameView::HudLayoutElement *pPartyStripLayout =
        HudUiService::findHudLayoutElement(view, "OutdoorPartyStrip");

    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return;
    }

    const OutdoorGameView::HudTextureHandle *pBasebar = HudUiService::ensureHudTextureLoaded(view, pBasebarLayout->primaryAsset);
    const OutdoorGameView::HudTextureHandle *pFaceMask =
        HudUiService::ensureHudTextureLoaded(view, pPartyStripLayout->primaryAsset);
    const OutdoorGameView::HudTextureHandle *pSelectionRing =
        HudUiService::ensureHudTextureLoaded(view, pPartyStripLayout->secondaryAsset);
    const OutdoorGameView::HudTextureHandle *pManaFrame =
        HudUiService::ensureHudTextureLoaded(view, pPartyStripLayout->tertiaryAsset);
    const OutdoorGameView::HudTextureHandle *pHealthBar =
        HudUiService::ensureHudTextureLoaded(view, pPartyStripLayout->quaternaryAsset);
    const OutdoorGameView::HudTextureHandle *pHealthBarYellow = HudUiService::ensureHudTextureLoaded(view, "manaY");
    const OutdoorGameView::HudTextureHandle *pHealthBarRed = HudUiService::ensureHudTextureLoaded(view, "manar");
    const OutdoorGameView::HudTextureHandle *pManaBar =
        HudUiService::ensureHudTextureLoaded(view, pPartyStripLayout->quinaryAsset);
    const OutdoorGameView::HudTextureHandle *pAggroBlack = HudUiService::ensureHudTextureLoaded(view, "statBL");
    const OutdoorGameView::HudTextureHandle *pAggroRed = HudUiService::ensureHudTextureLoaded(view, "statR");
    const OutdoorGameView::HudTextureHandle *pAggroYellow = HudUiService::ensureHudTextureLoaded(view, "statY");
    const OutdoorGameView::HudTextureHandle *pAggroGreen = HudUiService::ensureHudTextureLoaded(view, "statG");
    const Party &party = view.m_pOutdoorPartyRuntime->party();
    const std::vector<Character> &members = party.members();

    if (pBasebar == nullptr || pFaceMask == nullptr || members.empty())
    {
        return;
    }

    view.consumePendingPortraitEventFxRequests();

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedBasebar = HudUiService::resolveHudLayoutElement(
        view,
        "OutdoorBasebar",
        width,
        height,
        static_cast<float>(pBasebar->width),
        static_cast<float>(pBasebar->height));
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedPartyStrip = HudUiService::resolveHudLayoutElement(
        view,
        "OutdoorPartyStrip",
        width,
        height,
        static_cast<float>(pBasebar->width),
        static_cast<float>(pBasebar->height));

    if (!resolvedBasebar || !resolvedPartyStrip)
    {
        return;
    }

    const float uiScale = resolvedBasebar->scale;
    const float basebarWidth = resolvedBasebar->width;
    const float basebarHeight = resolvedBasebar->height;
    const float basebarX = resolvedBasebar->x;
    const float basebarY = resolvedBasebar->y;
    const float partyStripX = resolvedPartyStrip->x;
    const float partyStripY = resolvedPartyStrip->y;
    const float partyStripWidth = resolvedPartyStrip->width;
    const float partyStripHeight = resolvedPartyStrip->height;
    const float portraitWidth = pFaceMask->width * uiScale;
    const float portraitHeight = pFaceMask->height * uiScale;
    const float portraitStartX = partyStripX + partyStripWidth * (20.0f / 471.0f);
    const float portraitY = partyStripY + partyStripHeight * (23.0f / 92.0f);
    const float portraitDeltaX = partyStripWidth * (94.0f / 471.0f);
    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth
    );
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);
    float characterMouseX = 0.0f;
    float characterMouseY = 0.0f;
    const SDL_MouseButtonFlags characterMouseButtons = SDL_GetMouseState(&characterMouseX, &characterMouseY);
    const bool isLeftMousePressed = (characterMouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto submitTexturedQuad =
        [&view](const OutdoorGameView::HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            view.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
        };

    const auto submitTexturedQuadUv =
        [&view](const OutdoorGameView::HudTextureHandle &texture,
                float x,
                float y,
                float quadWidth,
                float quadHeight,
                float u0,
                float v0,
                float u1,
                float v1)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, OutdoorGameView::TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, OutdoorGameView::TexturedTerrainVertex::ms_layout);
            auto *pVertices = reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, u0, v0};
            pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[3] = {x, y, 0.0f, u0, v0};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[5] = {x, y + quadHeight, 0.0f, u0, v1};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, texture.textureHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, view.m_texturedTerrainProgramHandle);
        };

    const auto submitTexturedQuadClipped =
        [&view](const OutdoorGameView::HudTextureHandle &texture,
                float x,
                float y,
                float quadWidth,
                float quadHeight,
                uint16_t scissorX,
                uint16_t scissorY,
                uint16_t scissorWidth,
                uint16_t scissorHeight)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, OutdoorGameView::TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, OutdoorGameView::TexturedTerrainVertex::ms_layout);
            auto *pVertices = reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, 0.0f, 0.0f};
            pVertices[1] = {x + quadWidth, y, 0.0f, 1.0f, 0.0f};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
            pVertices[3] = {x, y, 0.0f, 0.0f, 0.0f};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
            pVertices[5] = {x, y + quadHeight, 0.0f, 0.0f, 1.0f};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, texture.textureHandle);
            bgfx::setScissor(scissorX, scissorY, scissorWidth, scissorHeight);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, view.m_texturedTerrainProgramHandle);
        };

    struct MinimapOverlayState
    {
        bool valid = false;
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
        float scale = 1.0f;
        float u0 = 0.0f;
        float v0 = 0.0f;
        float uSpan = 1.0f;
        float vSpan = 1.0f;
    };

    MinimapOverlayState minimapOverlay = {};
    const auto isBuffLayoutVisible =
        [&party](const std::string &layoutId) -> bool
        {
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

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
        };
    const OutdoorGameView::HudScreenState hudScreenState = view.currentHudScreenState();
    const bool isLimitedOverlayHud =
        hudScreenState == OutdoorGameView::HudScreenState::Dialogue
        || hudScreenState == OutdoorGameView::HudScreenState::Character
        || hudScreenState == OutdoorGameView::HudScreenState::Chest
        || hudScreenState == OutdoorGameView::HudScreenState::Spellbook;

    const auto isGameplayElementVisibleInHudState =
        [&view, hudScreenState, isLimitedOverlayHud](const OutdoorGameView::HudLayoutElement &layout) -> bool
        {
            (void)hudScreenState;

            if (toLowerCopy(layout.screen) != "outdoorhud")
            {
                return false;
            }

            if (!isLimitedOverlayHud)
            {
                return true;
            }

            const std::string normalizedId = toLowerCopy(layout.id);

            if (normalizedId == "outdoorbasebar"
                || normalizedId == "outdoorpartystrip"
                || normalizedId.rfind("charshield_", 0) == 0)
            {
                return true;
            }

            if (normalizedId.rfind("outdoorminimap", 0) == 0)
            {
                return false;
            }

            const OutdoorGameView::HudLayoutElement *pCurrent = &layout;

            while (pCurrent != nullptr && !pCurrent->parentId.empty())
            {
                if (toLowerCopy(pCurrent->parentId) == "outdoorbasebar")
                {
                    return true;
                }

                pCurrent = HudUiService::findHudLayoutElement(view, pCurrent->parentId);
            }

            return false;
        };

    submitTexturedQuad(*pBasebar, basebarX, basebarY, basebarWidth, basebarHeight);

    const size_t displayedMemberCount = members.size();
    const size_t activeMemberIndex = view.m_pOutdoorPartyRuntime->party().activeMemberIndex();
    const bool activeMemberReadyForSelection =
        view.m_pOutdoorPartyRuntime->party().canSelectMemberInGameplay(activeMemberIndex);

    for (size_t memberIndex = 0; memberIndex < displayedMemberCount; ++memberIndex)
    {
        const Character &member = members[memberIndex];
        const float portraitX = portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX;
        const float portraitInset = 2.0f * uiScale;
        const std::string portraitTextureName = view.resolvePortraitTextureName(member);
        const OutdoorGameView::HudTextureHandle *pPortrait = HudUiService::ensureHudTextureLoaded(view, portraitTextureName);

        if (pPortrait != nullptr)
        {
            submitTexturedQuad(
                *pPortrait,
                portraitX + portraitInset,
                portraitY + portraitInset,
                portraitWidth - portraitInset * 2.0f,
                portraitHeight - portraitInset * 2.0f
            );
        }

        view.renderPortraitFx(memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
        submitTexturedQuad(*pFaceMask, portraitX, portraitY, portraitWidth, portraitHeight);

        if (activeMemberReadyForSelection && memberIndex == activeMemberIndex && pSelectionRing != nullptr)
        {
            submitTexturedQuad(*pSelectionRing, portraitX - uiScale, portraitY, portraitWidth, portraitHeight);
        }

        if (pManaFrame != nullptr)
        {
            const PortraitAggroIndicator aggroIndicator =
                classifyPortraitAggroIndicator(member, view.m_pOutdoorPartyRuntime, view.m_pOutdoorWorldRuntime);
            const OutdoorGameView::HudTextureHandle *pAggroTexture = nullptr;

            switch (aggroIndicator)
            {
            case PortraitAggroIndicator::Black:
                pAggroTexture = pAggroBlack;
                break;
            case PortraitAggroIndicator::Green:
                pAggroTexture = pAggroGreen;
                break;
            case PortraitAggroIndicator::Yellow:
                pAggroTexture = pAggroYellow;
                break;
            case PortraitAggroIndicator::Red:
                pAggroTexture = pAggroRed;
                break;
            case PortraitAggroIndicator::Hidden:
                break;
            }

            if (pAggroTexture != nullptr)
            {
                const float barFrameHeight = pManaFrame->height * uiScale;
                const float barFrameY = basebarY + basebarHeight - barFrameHeight - partyStripHeight * (1.0f / 92.0f);
                const float aggroWidth = static_cast<float>(pAggroTexture->width) * uiScale;
                const float aggroHeight = static_cast<float>(pAggroTexture->height) * uiScale;
                const float aggroX = portraitX - aggroWidth * 0.35f - 8.0f * uiScale;
                const float aggroY = barFrameY + barFrameHeight - aggroHeight;
                submitTexturedQuad(*pAggroTexture, aggroX, aggroY, aggroWidth, aggroHeight);
            }
        }

        if (pManaFrame != nullptr)
        {
            const float barFrameX = portraitX + partyStripWidth * (63.0f / 471.0f);
            const float barFrameWidth = pManaFrame->width * uiScale;
            const float barFrameHeight = pManaFrame->height * uiScale;
            const float barFrameY = basebarY + basebarHeight - barFrameHeight - partyStripHeight * (1.0f / 92.0f);
            submitTexturedQuad(*pManaFrame, barFrameX, barFrameY, barFrameWidth, barFrameHeight);

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

            const OutdoorGameView::HudTextureHandle *pResolvedHealthBar = pHealthBar;

            if (healthPercent > 0.0f)
            {
                if (healthPercent <= 0.25f && pHealthBarRed != nullptr)
                {
                    pResolvedHealthBar = pHealthBarRed;
                }
                else if (healthPercent <= 0.5f && pHealthBarYellow != nullptr)
                {
                    pResolvedHealthBar = pHealthBarYellow;
                }
            }

            if (pResolvedHealthBar != nullptr && healthPercent > 0.0f)
            {
                submitTexturedQuadUv(
                    *pResolvedHealthBar,
                    leftFillX,
                    fillY + (1.0f - healthPercent) * fillHeight,
                    fillWidth,
                    healthPercent * fillHeight,
                    0.0f,
                    1.0f - healthPercent,
                    1.0f,
                    1.0f
                );
            }

            if (pManaBar != nullptr && manaPercent > 0.0f)
            {
                submitTexturedQuadUv(
                    *pManaBar,
                    rightFillX,
                    fillY + (1.0f - manaPercent) * fillHeight,
                    fillWidth,
                    manaPercent * fillHeight,
                    0.0f,
                    1.0f - manaPercent,
                    1.0f,
                    1.0f
                );
            }
        }
    }

    for (size_t memberIndex = displayedMemberCount; memberIndex < 5; ++memberIndex)
    {
        const std::string slotShieldId = "CharShield_" + std::to_string(memberIndex + 1);
        const OutdoorGameView::HudLayoutElement *pShieldLayout = HudUiService::findHudLayoutElement(view, slotShieldId);

        if (pShieldLayout == nullptr || pShieldLayout->primaryAsset.empty())
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pShieldTexture =
            HudUiService::ensureHudTextureLoaded(view, pShieldLayout->primaryAsset);

        if (pShieldTexture == nullptr)
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedShield = HudUiService::resolveHudLayoutElement(
            view,
            slotShieldId,
            width,
            height,
            pShieldLayout->width > 0.0f ? pShieldLayout->width : static_cast<float>(pShieldTexture->width),
            pShieldLayout->height > 0.0f ? pShieldLayout->height : static_cast<float>(pShieldTexture->height));

        if (!resolvedShield)
        {
            continue;
        }

        submitTexturedQuad(*pShieldTexture, resolvedShield->x, resolvedShield->y, resolvedShield->width, resolvedShield->height);
    }

    const auto renderOrderedSimpleHudElement =
        [&](const std::string &layoutId)
        {
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "outdoorbasebar"
                || normalizedLayoutId == "outdoorpartystrip"
                || normalizedLayoutId.rfind("charshield_", 0) == 0)
            {
                return;
            }

            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr || !pLayout->visible)
            {
                return;
            }

            if (!isGameplayElementVisibleInHudState(*pLayout) || !isBuffLayoutVisible(layoutId))
            {
                return;
            }

            if (normalizedLayoutId == "outdoorminimap")
            {
                if (!view.m_map || view.m_pOutdoorPartyRuntime == nullptr || pLayout->width <= 0.0f || pLayout->height <= 0.0f)
                {
                    return;
                }

                const std::string mapTextureName = toLowerCopy(std::filesystem::path(view.m_map->fileName).stem().string());
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(view, mapTextureName);

                if (pTexture == nullptr)
                {
                    return;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(
                    view,
                    layoutId,
                    width,
                    height,
                    pLayout->width,
                    pLayout->height);

                if (!resolved)
                {
                    return;
                }

                const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
                const float partyU = std::clamp((-moveState.x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
                const float partyV = std::clamp((32768.0f - moveState.y) / 65536.0f, 0.0f, 1.0f);
                const float uSpan = std::min(1.0f, pLayout->width / OutdoorMinimapZoom);
                const float vSpan = std::min(1.0f, pLayout->height / OutdoorMinimapZoom);
                const float u0 = std::clamp(partyU - uSpan * 0.5f, 0.0f, 1.0f - uSpan);
                const float v0 = std::clamp(partyV - vSpan * 0.5f, 0.0f, 1.0f - vSpan);

                submitTexturedQuadUv(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height, u0, v0, u0 + uSpan, v0 + vSpan);
                minimapOverlay.valid = true;
                minimapOverlay.x = resolved->x;
                minimapOverlay.y = resolved->y;
                minimapOverlay.width = resolved->width;
                minimapOverlay.height = resolved->height;
                minimapOverlay.scale = resolved->scale;
                minimapOverlay.u0 = u0;
                minimapOverlay.v0 = v0;
                minimapOverlay.uSpan = uSpan;
                minimapOverlay.vSpan = vSpan;
                return;
            }

            if (pLayout->primaryAsset.empty())
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> interactiveResolved =
                HudUiService::resolveHudLayoutElement(
                    view,
                    layoutId,
                    width,
                    height,
                    pLayout->width,
                    pLayout->height);
            const std::string *pAssetName = interactiveResolved
                ? HudUiService::resolveInteractiveAssetName(
                    *pLayout,
                    *interactiveResolved,
                    characterMouseX,
                    characterMouseY,
                    isLeftMousePressed)
                : nullptr;

            const OutdoorGameView::HudTextureHandle *pTexture =
                pAssetName != nullptr ? HudUiService::ensureHudTextureLoaded(view, *pAssetName) : nullptr;

            if (pTexture == nullptr)
            {
                pTexture = HudUiService::ensureHudTextureLoaded(view, pLayout->primaryAsset);
            }

            if (pTexture == nullptr)
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(
                view,
                layoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pTexture->height));

            if (!resolved)
            {
                return;
            }

            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        };

    const std::vector<std::string> orderedGameplayLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "OutdoorHud");

    for (const std::string &layoutId : orderedGameplayLayoutIds)
    {
        renderOrderedSimpleHudElement(layoutId);
    }

    if (hudScreenState == OutdoorGameView::HudScreenState::Gameplay && minimapOverlay.valid && view.m_pOutdoorPartyRuntime != nullptr)
    {
        const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
        const float partyU = std::clamp((-moveState.x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
        const float partyV = std::clamp((32768.0f - moveState.y) / 65536.0f, 0.0f, 1.0f);
        const float minimapCenterX = minimapOverlay.x + ((partyU - minimapOverlay.u0) / minimapOverlay.uSpan) * minimapOverlay.width;
        const float minimapCenterY = minimapOverlay.y + ((partyV - minimapOverlay.v0) / minimapOverlay.vSpan) * minimapOverlay.height;
        const float markerSize = std::max(1.5f, 2.0f * minimapOverlay.scale);
        const float markerHalfSize = markerSize * 0.5f;
        const float markerMargin = std::max(2.0f, 2.0f * minimapOverlay.scale);
        const float markerMinX = minimapOverlay.x + markerMargin + markerHalfSize;
        const float markerMaxX = minimapOverlay.x + minimapOverlay.width - markerMargin - markerHalfSize;
        const float markerMinY = minimapOverlay.y + markerMargin + markerHalfSize;
        const float markerMaxY = minimapOverlay.y + minimapOverlay.height - markerMargin - markerHalfSize;
        const uint16_t minimapScissorX = static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.x + markerMargin)));
        const uint16_t minimapScissorY = static_cast<uint16_t>(std::max(0.0f, std::floor(minimapOverlay.y + markerMargin)));
        const uint16_t minimapScissorWidth =
            static_cast<uint16_t>(std::max(1.0f, std::ceil(minimapOverlay.width - markerMargin * 2.0f)));
        const uint16_t minimapScissorHeight =
            static_cast<uint16_t>(std::max(1.0f, std::ceil(minimapOverlay.height - markerMargin * 2.0f)));
        const OutdoorGameView::HudTextureHandle *pFriendlyMarkerTexture =
            HudUiService::ensureSolidHudTextureLoaded(view, "__minimap_marker_friendly__", 0xff00ff00u);
        const OutdoorGameView::HudTextureHandle *pHostileMarkerTexture =
            HudUiService::ensureSolidHudTextureLoaded(view, "__minimap_marker_hostile__", 0xffff0000u);
        const OutdoorGameView::HudTextureHandle *pCorpseMarkerTexture =
            HudUiService::ensureSolidHudTextureLoaded(view, "__minimap_marker_corpse__", 0xffffff00u);

        if (view.m_pOutdoorWorldRuntime != nullptr)
        {
            for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

                if (pActor == nullptr || pActor->isInvisible)
                {
                    continue;
                }

                const float actorU = (-static_cast<float>(pActor->x) + 32768.0f) / 65536.0f;
                const float actorV = (32768.0f - static_cast<float>(pActor->y)) / 65536.0f;
                const float markerCenterX =
                    minimapOverlay.x + ((actorU - minimapOverlay.u0) / minimapOverlay.uSpan) * minimapOverlay.width;
                const float markerCenterY =
                    minimapOverlay.y + ((actorV - minimapOverlay.v0) / minimapOverlay.vSpan) * minimapOverlay.height;

                if (markerCenterX < markerMinX || markerCenterX > markerMaxX
                    || markerCenterY < markerMinY || markerCenterY > markerMaxY)
                {
                    continue;
                }

                const OutdoorGameView::HudTextureHandle *pMarkerTexture = pActor->isDead
                    ? pCorpseMarkerTexture
                    : pActor->hostileToParty ? pHostileMarkerTexture : pFriendlyMarkerTexture;

                if (pMarkerTexture == nullptr)
                {
                    continue;
                }

                submitTexturedQuadClipped(
                    *pMarkerTexture,
                    markerCenterX - markerHalfSize,
                    markerCenterY - markerHalfSize,
                    markerSize,
                    markerSize,
                    minimapScissorX,
                    minimapScissorY,
                    minimapScissorWidth,
                    minimapScissorHeight);
            }
        }

        float normalizedYaw = std::fmod(view.m_cameraYawRadians, Pi * 2.0f);

        if (normalizedYaw < 0.0f)
        {
            normalizedYaw += Pi * 2.0f;
        }

        const int octant = static_cast<int>(std::floor((normalizedYaw + Pi * 0.125f) / (Pi * 0.25f))) % 8;
        const int arrowIndex = (octant + 3) % 8;
        const std::string arrowTextureName = "MAPDIR" + std::to_string(arrowIndex + 1);
        const OutdoorGameView::HudTextureHandle *pArrowTexture =
            HudUiService::ensureHudTextureLoaded(view, arrowTextureName);

        if (pArrowTexture != nullptr)
        {
            const float arrowWidth = static_cast<float>(pArrowTexture->width) * minimapOverlay.scale;
            const float arrowHeight = static_cast<float>(pArrowTexture->height) * minimapOverlay.scale;
            submitTexturedQuadClipped(
                *pArrowTexture,
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
}

void GameplayHudRenderer::renderGameplayHud(const OutdoorGameView &view, int width, int height)
{
    if (view.m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const Party &party = view.m_pOutdoorPartyRuntime->party();
    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth
    );
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);
    const OutdoorGameView::HudScreenState hudScreenState = view.currentHudScreenState();
    const bool isLimitedOverlayHud =
        hudScreenState == OutdoorGameView::HudScreenState::Dialogue
        || hudScreenState == OutdoorGameView::HudScreenState::Character
        || hudScreenState == OutdoorGameView::HudScreenState::Chest
        || hudScreenState == OutdoorGameView::HudScreenState::Spellbook;
    const bool shouldRenderStatusBar =
        hudScreenState != OutdoorGameView::HudScreenState::Spellbook;

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

    if (shouldRenderStatusBar)
    {
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedStatusBar = HudUiService::resolveHudLayoutElement(
            view,
            "OutdoorStatusBar",
            width,
            height,
            360.0f,
            18.0f);

        if (!resolvedStatusBar)
        {
            return;
        }

        std::string statusBarLabel;

        if (view.m_statusBarEventRemainingSeconds > 0.0f && !view.m_statusBarEventText.empty())
        {
            statusBarLabel = view.m_statusBarEventText;
        }
        else if (!view.m_statusBarHoverText.empty())
        {
            statusBarLabel = view.m_statusBarHoverText;
        }

        if (const OutdoorGameView::HudLayoutElement *pStatusBarLayout =
                HudUiService::findHudLayoutElement(view, "OutdoorStatusBar"))
        {
            HudUiService::renderLayoutLabel(view, *pStatusBarLayout, *resolvedStatusBar, statusBarLabel);
        }
    }

    if (!isLimitedOverlayHud)
    {
        if (const OutdoorGameView::HudLayoutElement *pTopBarLayout = HudUiService::findHudLayoutElement(view, "OutdoorTopBar"))
        {
            if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> topBar = HudUiService::resolveHudLayoutElement(
                    view,
                    "OutdoorTopBar",
                    width,
                    height,
                    640.0f,
                    29.0f))
            {
                if (!pTopBarLayout->labelText.empty())
                {
                    const std::string label = replaceAll(
                        replaceAll(pTopBarLayout->labelText, "{gold}", std::to_string(party.gold())),
                        "{food}",
                        std::to_string(party.food()));
                    HudUiService::renderLayoutLabel(view, *pTopBarLayout, *topBar, label);
                }
            }
        }

        if (const OutdoorGameView::HudLayoutElement *pGoldLabelLayout =
                HudUiService::findHudLayoutElement(view, "OutdoorGoldLabel"))
        {
            if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> goldLabel = HudUiService::resolveHudLayoutElement(
                    view,
                    "OutdoorGoldLabel",
                    width,
                    height,
                    28.0f,
                    14.0f))
            {
                HudUiService::renderLayoutLabel(
                    view,
                    *pGoldLabelLayout,
                    *goldLabel,
                    resolveCounterLabel(pGoldLabelLayout->labelText, std::to_string(party.gold())));
            }
        }

        if (const OutdoorGameView::HudLayoutElement *pFoodLabelLayout =
                HudUiService::findHudLayoutElement(view, "OutdoorFoodLabel"))
        {
            if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> foodLabel = HudUiService::resolveHudLayoutElement(
                    view,
                    "OutdoorFoodLabel",
                    width,
                    height,
                    28.0f,
                    14.0f))
            {
                HudUiService::renderLayoutLabel(
                    view,
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

    if (const OutdoorGameView::HudLayoutElement *pBottomLeftButtonsLayout =
            HudUiService::findHudLayoutElement(view, "OutdoorBottomLeftButtons"))
    {
        if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bottomLeftButtons = HudUiService::resolveHudLayoutElement(
                view,
                "OutdoorBottomLeftButtons",
                width,
                height,
                180.0f,
                32.0f))
        {
            HudUiService::renderLayoutLabel(
                view,
                *pBottomLeftButtonsLayout,
                *bottomLeftButtons,
                pBottomLeftButtonsLayout->labelText);
        }
    }

    if (const OutdoorGameView::HudLayoutElement *pSkullPanelLayout =
            HudUiService::findHudLayoutElement(view, "OutdoorBuffSkullPanel"))
    {
        if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> skullPanel = HudUiService::resolveHudLayoutElement(
                view,
                "OutdoorBuffSkullPanel",
                width,
                height,
                96.0f,
                48.0f))
        {
            HudUiService::renderLayoutLabel(view, *pSkullPanelLayout, *skullPanel, pSkullPanelLayout->labelText);
        }
    }

    if (const OutdoorGameView::HudLayoutElement *pBodyPanelLayout =
            HudUiService::findHudLayoutElement(view, "OutdoorBuffBodyPanel"))
    {
        if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyPanel = HudUiService::resolveHudLayoutElement(
                view,
                "OutdoorBuffBodyPanel",
                width,
                height,
                96.0f,
                48.0f))
        {
            HudUiService::renderLayoutLabel(view, *pBodyPanelLayout, *bodyPanel, pBodyPanelLayout->labelText);
        }
    }
}
} // namespace OpenYAMM::Game
