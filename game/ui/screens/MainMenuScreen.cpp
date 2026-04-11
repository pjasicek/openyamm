#include "game/ui/screens/MainMenuScreen.h"

#include "game/audio/GameAudioSystem.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string_view>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ReferenceWidth = 640.0f;
constexpr float ReferenceHeight = 480.0f;
constexpr const char *MainMenuLayoutPath = "Data/ui/menu/main_menu.yml";

struct ResolvedLayoutElement
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float scale = 1.0f;
};

ResolvedLayoutElement resolveAttachedLayoutRect(
    UiLayoutManager::LayoutAttachMode attachTo,
    const ResolvedLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    ResolvedLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
        case UiLayoutManager::LayoutAttachMode::None:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::RightOf:
            resolved.x = parent.x + parent.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::LeftOf:
            resolved.x = parent.x - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::Above:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::Below:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterAbove:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterBelow:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterIn:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;
    }

    return resolved;
}

std::optional<ResolvedLayoutElement> resolveLayoutElementRecursive(
    const UiLayoutManager &layoutManager,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight,
    std::unordered_set<std::string> &visited)
{
    if (visited.contains(layoutId))
    {
        return std::nullopt;
    }

    visited.insert(layoutId);
    const UiLayoutManager::LayoutElement *pElement = layoutManager.findElement(layoutId);

    if (pElement == nullptr)
    {
        visited.erase(layoutId);
        return std::nullopt;
    }

    const UiLayoutManager::LayoutElement &element = *pElement;
    const float baseScale = std::min(
        static_cast<float>(screenWidth) / ReferenceWidth,
        static_cast<float>(screenHeight) / ReferenceHeight);
    const float viewportWidth = ReferenceWidth * baseScale;
    const float viewportHeight = ReferenceHeight * baseScale;
    const float viewportX = (static_cast<float>(screenWidth) - viewportWidth) * 0.5f;
    const float viewportY = (static_cast<float>(screenHeight) - viewportHeight) * 0.5f;
    ResolvedLayoutElement resolved = {};

    if (!element.parentId.empty())
    {
        const UiLayoutManager::LayoutElement *pParent = layoutManager.findElement(element.parentId);

        if (pParent == nullptr)
        {
            visited.erase(layoutId);
            return std::nullopt;
        }

        const std::optional<ResolvedLayoutElement> parent = resolveLayoutElementRecursive(
            layoutManager,
            element.parentId,
            screenWidth,
            screenHeight,
            pParent->width,
            pParent->height,
            visited);

        if (!parent.has_value())
        {
            visited.erase(layoutId);
            return std::nullopt;
        }

        resolved.scale = element.hasExplicitScale
            ? std::clamp(baseScale, element.minScale, element.maxScale)
            : parent->scale;
        resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
        resolved.height = (element.height > 0.0f ? element.height : fallbackHeight) * resolved.scale;
        resolved = resolveAttachedLayoutRect(
            element.attachTo,
            *parent,
            resolved.width,
            resolved.height,
            element.gapX,
            element.gapY,
            resolved.scale);
        visited.erase(layoutId);
        return resolved;
    }

    resolved.scale = std::clamp(baseScale, element.minScale, element.maxScale);
    resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
    resolved.height = (element.height > 0.0f ? element.height : fallbackHeight) * resolved.scale;

    switch (element.anchor)
    {
        case UiLayoutManager::LayoutAnchor::TopLeft:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::TopCenter:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::TopRight:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Left:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Center:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Right:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomLeft:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomCenter:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomRight:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;
    }

    visited.erase(layoutId);
    return resolved;
}
}

MainMenuScreen::MainMenuScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    GameAudioSystem *pGameAudioSystem,
    Action newGameAction,
    Action loadGameAction,
    Action quitAction)
    : MenuScreenBase(assetFileSystem)
    , m_pGameAudioSystem(pGameAudioSystem)
    , m_newGameAction(std::move(newGameAction))
    , m_loadGameAction(std::move(loadGameAction))
    , m_quitAction(std::move(quitAction))
{
}

AppMode MainMenuScreen::mode() const
{
    return AppMode::MainMenu;
}

void MainMenuScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);
    ensureLayoutLoaded();

    const Rect backgroundRect = resolveLayoutRect("MainMenuBackground", ReferenceWidth, ReferenceHeight).value_or(
        Rect{0.0f, 0.0f, ReferenceWidth, ReferenceHeight});
    drawTexture(resolveAssetName("MainMenuBackground", "title"), backgroundRect);

    const ButtonState newGameButton = drawButton(
        resolveButtonVisuals("MainMenuNewGameButton", ButtonVisualSet{"T_new_up", "T_new_ht", "T_new_dn"}),
        resolveLayoutRect("MainMenuNewGameButton", 135.0f, 41.0f).value_or(Rect{}));
    const ButtonState loadGameButton = drawButton(
        resolveButtonVisuals("MainMenuLoadGameButton", ButtonVisualSet{"T_load_up", "T_load_ht", "T_load_dn"}),
        resolveLayoutRect("MainMenuLoadGameButton", 135.0f, 41.0f).value_or(Rect{}));
    const ButtonState creditsButton = drawButton(
        resolveButtonVisuals("MainMenuCreditsButton", ButtonVisualSet{"T_cred_up", "T_cred_ht", "T_cred_dn"}),
        resolveLayoutRect("MainMenuCreditsButton", 135.0f, 41.0f).value_or(Rect{}));
    const ButtonState quitButton = drawButton(
        resolveButtonVisuals("MainMenuQuitButton", ButtonVisualSet{"T_quit_up", "T_quit_ht", "T_quit_dn"}),
        resolveLayoutRect("MainMenuQuitButton", 135.0f, 41.0f).value_or(Rect{}));

    if (newGameButton.clicked && m_newGameAction)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        m_newGameAction();
        return;
    }

    if (loadGameButton.clicked && m_loadGameAction)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        m_loadGameAction();
        return;
    }

    if (creditsButton.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
    }

    if (quitButton.clicked && m_quitAction)
    {
        playUiClickSound(SoundId::ClickIn);
        m_quitAction();
        return;
    }
}

void MainMenuScreen::playUiClickSound(SoundId soundId) const
{
    if (m_pGameAudioSystem == nullptr || soundId == SoundId::None)
    {
        return;
    }

    m_pGameAudioSystem->playCommonSound(soundId, GameAudioSystem::PlaybackGroup::Ui);
}

bool MainMenuScreen::ensureLayoutLoaded()
{
    if (m_layoutLoaded)
    {
        return true;
    }

    m_layoutManager.clear();
    m_layoutLoaded = m_layoutManager.loadLayoutFile(assetFileSystem(), MainMenuLayoutPath);
    return m_layoutLoaded;
}

std::optional<MenuScreenBase::Rect> MainMenuScreen::resolveLayoutRect(
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight) const
{
    if (!m_layoutLoaded)
    {
        return std::nullopt;
    }

    std::unordered_set<std::string> visited;
    const std::optional<ResolvedLayoutElement> resolved = resolveLayoutElementRecursive(
        m_layoutManager,
        layoutId,
        frameWidth(),
        frameHeight(),
        fallbackWidth,
        fallbackHeight,
        visited);

    if (!resolved.has_value())
    {
        return std::nullopt;
    }

    return Rect{
        std::round(resolved->x),
        std::round(resolved->y),
        std::round(resolved->width),
        std::round(resolved->height)
    };
}

MenuScreenBase::ButtonVisualSet MainMenuScreen::resolveButtonVisuals(
    const std::string &layoutId,
    const ButtonVisualSet &fallbackVisuals) const
{
    if (!m_layoutLoaded)
    {
        return fallbackVisuals;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr)
    {
        return fallbackVisuals;
    }

    ButtonVisualSet visuals = fallbackVisuals;

    if (!pLayout->primaryAsset.empty())
    {
        visuals.defaultTextureName = pLayout->primaryAsset;
    }

    if (!pLayout->hoverAsset.empty())
    {
        visuals.highlightedTextureName = pLayout->hoverAsset;
    }

    if (!pLayout->pressedAsset.empty())
    {
        visuals.pressedTextureName = pLayout->pressedAsset;
    }

    return visuals;
}

std::string MainMenuScreen::resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const
{
    if (!m_layoutLoaded)
    {
        return fallbackAssetName;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr || pLayout->primaryAsset.empty())
    {
        return fallbackAssetName;
    }

    return pLayout->primaryAsset;
}
}
