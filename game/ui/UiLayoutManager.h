#pragma once

#include "engine/AssetFileSystem.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class UiLayoutManager
{
public:
    enum class LayoutAnchor
    {
        TopLeft,
        TopCenter,
        TopRight,
        Left,
        Center,
        Right,
        BottomLeft,
        BottomCenter,
        BottomRight
    };

    enum class LayoutAttachMode
    {
        None,
        RightOf,
        LeftOf,
        Above,
        Below,
        CenterAbove,
        CenterBelow,
        InsideLeft,
        InsideRight,
        InsideTopCenter,
        InsideTopLeft,
        InsideTopRight,
        InsideBottomLeft,
        InsideBottomCenter,
        InsideBottomRight,
        CenterIn
    };

    enum class LayoutAnchorSpace
    {
        Viewport,
        Screen
    };

    enum class TextAlignX
    {
        Left,
        Center,
        Right
    };

    enum class TextAlignY
    {
        Top,
        Middle,
        Bottom
    };

    struct LayoutElement
    {
        std::string id;
        std::string screen;
        LayoutAnchor anchor = LayoutAnchor::TopLeft;
        LayoutAnchorSpace anchorSpace = LayoutAnchorSpace::Viewport;
        std::string parentId;
        LayoutAttachMode attachTo = LayoutAttachMode::None;
        float gapX = 0.0f;
        float gapY = 0.0f;
        float offsetX = 0.0f;
        float offsetY = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
        std::string bottomToId;
        float bottomGap = 0.0f;
        float minScale = 1.0f;
        float maxScale = 3.0f;
        bool hasExplicitScale = false;
        int zIndex = 0;
        bool visible = true;
        bool interactive = false;
        std::string primaryAsset;
        std::string hoverAsset;
        std::string pressedAsset;
        std::string secondaryAsset;
        std::string tertiaryAsset;
        std::string quaternaryAsset;
        std::string quinaryAsset;
        std::string fontName;
        std::string labelText;
        uint32_t textColorAbgr = 0xffffffffu;
        TextAlignX textAlignX = TextAlignX::Left;
        TextAlignY textAlignY = TextAlignY::Top;
        float textScale = 1.0f;
        float textPadX = 0.0f;
        float textPadY = 0.0f;
        std::string notes;
    };

    void clear();
    bool loadLayoutFile(const Engine::AssetFileSystem &assetFileSystem, const std::string &path);

    const LayoutElement *findElement(const std::string &layoutId) const;
    std::vector<std::string> sortedLayoutIdsForScreen(const std::string &screen) const;
    int maxZIndexForScreen(const std::string &screen) const;
    static int defaultZIndexForScreen(const std::string &screen);

    const std::unordered_map<std::string, LayoutElement> &elements() const;

private:
    std::vector<std::string> m_layoutOrder;
    std::unordered_map<std::string, LayoutElement> m_layoutElements;
    mutable std::unordered_map<std::string, std::vector<std::string>> m_sortedLayoutIdsByScreen;
};
}
