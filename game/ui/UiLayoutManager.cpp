#include "game/ui/UiLayoutManager.h"

#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cstdlib>
#include <functional>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeLayoutToken(const std::string &value)
{
    const std::string lowerValue = toLowerCopy(value);
    std::string normalizedValue;

    for (char character : lowerValue)
    {
        if (character != '_' && character != '-' && character != ' ')
        {
            normalizedValue.push_back(character);
        }
    }

    return normalizedValue;
}

uint32_t makeAbgrColor(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

std::optional<UiLayoutManager::LayoutAnchor> parseRootAnchor(const std::string &value)
{
    const std::string normalizedValue = normalizeLayoutToken(value);

    if (normalizedValue == "topleft")
    {
        return UiLayoutManager::LayoutAnchor::TopLeft;
    }

    if (normalizedValue == "topcenter")
    {
        return UiLayoutManager::LayoutAnchor::TopCenter;
    }

    if (normalizedValue == "topright")
    {
        return UiLayoutManager::LayoutAnchor::TopRight;
    }

    if (normalizedValue == "left")
    {
        return UiLayoutManager::LayoutAnchor::Left;
    }

    if (normalizedValue == "center")
    {
        return UiLayoutManager::LayoutAnchor::Center;
    }

    if (normalizedValue == "right")
    {
        return UiLayoutManager::LayoutAnchor::Right;
    }

    if (normalizedValue == "bottomleft")
    {
        return UiLayoutManager::LayoutAnchor::BottomLeft;
    }

    if (normalizedValue == "bottomcenter")
    {
        return UiLayoutManager::LayoutAnchor::BottomCenter;
    }

    if (normalizedValue == "bottomright")
    {
        return UiLayoutManager::LayoutAnchor::BottomRight;
    }

    return std::nullopt;
}

std::optional<UiLayoutManager::LayoutAttachMode> parseChildAnchor(const std::string &value)
{
    const std::string normalizedValue = normalizeLayoutToken(value);

    if (normalizedValue.empty() || normalizedValue == "none")
    {
        return UiLayoutManager::LayoutAttachMode::None;
    }

    if (normalizedValue == "rightof")
    {
        return UiLayoutManager::LayoutAttachMode::RightOf;
    }

    if (normalizedValue == "leftof")
    {
        return UiLayoutManager::LayoutAttachMode::LeftOf;
    }

    if (normalizedValue == "right" || normalizedValue == "insideright")
    {
        return UiLayoutManager::LayoutAttachMode::InsideRight;
    }

    if (normalizedValue == "left" || normalizedValue == "insideleft")
    {
        return UiLayoutManager::LayoutAttachMode::InsideLeft;
    }

    if (normalizedValue == "above")
    {
        return UiLayoutManager::LayoutAttachMode::Above;
    }

    if (normalizedValue == "below")
    {
        return UiLayoutManager::LayoutAttachMode::Below;
    }

    if (normalizedValue == "centerabove")
    {
        return UiLayoutManager::LayoutAttachMode::CenterAbove;
    }

    if (normalizedValue == "centerbelow")
    {
        return UiLayoutManager::LayoutAttachMode::CenterBelow;
    }

    if (normalizedValue == "top"
        || normalizedValue == "topcenter"
        || normalizedValue == "insidetopcenter")
    {
        return UiLayoutManager::LayoutAttachMode::InsideTopCenter;
    }

    if (normalizedValue == "topleft" || normalizedValue == "insidetopleft")
    {
        return UiLayoutManager::LayoutAttachMode::InsideTopLeft;
    }

    if (normalizedValue == "topright" || normalizedValue == "insidetopright")
    {
        return UiLayoutManager::LayoutAttachMode::InsideTopRight;
    }

    if (normalizedValue == "bottomleft" || normalizedValue == "insidebottomleft")
    {
        return UiLayoutManager::LayoutAttachMode::InsideBottomLeft;
    }

    if (normalizedValue == "bottomcenter" || normalizedValue == "insidebottomcenter")
    {
        return UiLayoutManager::LayoutAttachMode::InsideBottomCenter;
    }

    if (normalizedValue == "bottomright" || normalizedValue == "insidebottomright")
    {
        return UiLayoutManager::LayoutAttachMode::InsideBottomRight;
    }

    if (normalizedValue == "center" || normalizedValue == "centerin")
    {
        return UiLayoutManager::LayoutAttachMode::CenterIn;
    }

    return std::nullopt;
}

std::optional<UiLayoutManager::TextAlignX> parseTextAlignX(const std::string &value)
{
    const std::string normalizedValue = normalizeLayoutToken(value);

    if (normalizedValue.empty() || normalizedValue == "left")
    {
        return UiLayoutManager::TextAlignX::Left;
    }

    if (normalizedValue == "center")
    {
        return UiLayoutManager::TextAlignX::Center;
    }

    if (normalizedValue == "right")
    {
        return UiLayoutManager::TextAlignX::Right;
    }

    return std::nullopt;
}

std::optional<UiLayoutManager::TextAlignY> parseTextAlignY(const std::string &value)
{
    const std::string normalizedValue = normalizeLayoutToken(value);

    if (normalizedValue.empty() || normalizedValue == "top")
    {
        return UiLayoutManager::TextAlignY::Top;
    }

    if (normalizedValue == "middle" || normalizedValue == "center")
    {
        return UiLayoutManager::TextAlignY::Middle;
    }

    if (normalizedValue == "bottom")
    {
        return UiLayoutManager::TextAlignY::Bottom;
    }

    return std::nullopt;
}

bool yamlBoolOrDefault(const YAML::Node &node, const char *key, bool defaultValue)
{
    const YAML::Node child = node[key];
    return child ? child.as<bool>() : defaultValue;
}

float yamlFloatOrDefault(const YAML::Node &node, const char *key, float defaultValue)
{
    const YAML::Node child = node[key];
    return child ? child.as<float>() : defaultValue;
}

std::string yamlStringOrEmpty(const YAML::Node &node, const char *key)
{
    const YAML::Node child = node[key];
    return child ? child.as<std::string>() : "";
}
}

void UiLayoutManager::clear()
{
    m_layoutOrder.clear();
    m_layoutElements.clear();
    m_sortedLayoutIdsByScreen.clear();
}

bool UiLayoutManager::loadLayoutFile(const Engine::AssetFileSystem &assetFileSystem, const std::string &path)
{
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(path);

    if (!fileContents)
    {
        return false;
    }

    try
    {
        m_sortedLayoutIdsByScreen.clear();
        const YAML::Node root = YAML::Load(*fileContents);

        if (!root.IsMap())
        {
            return false;
        }

        const YAML::Node screenNode = root["screen"];
        const YAML::Node elementsNode = root["elements"];

        if (!screenNode || !screenNode.IsScalar() || !elementsNode || !elementsNode.IsSequence())
        {
            return false;
        }

        const std::string screen = screenNode.as<std::string>();
        std::function<bool(const YAML::Node &, const std::string &)> appendElement;

        appendElement =
            [this, &appendElement, &screen](const YAML::Node &node, const std::string &parentId) -> bool
            {
                if (!node.IsMap())
                {
                    return false;
                }

                const YAML::Node idNode = node["id"];
                const YAML::Node anchorNode = node["anchor"];

                if (!idNode || !idNode.IsScalar() || !anchorNode || !anchorNode.IsScalar())
                {
                    return false;
                }

                LayoutElement element = {};
                element.id = idNode.as<std::string>();
                element.screen = screen;
                element.parentId = parentId;
                element.zIndex = defaultZIndexForScreen(screen);

                if (parentId.empty())
                {
                    const std::optional<LayoutAnchor> anchor = parseRootAnchor(anchorNode.as<std::string>());

                    if (!anchor)
                    {
                        return false;
                    }

                    element.anchor = *anchor;
                    element.offsetX = yamlFloatOrDefault(node, "offset_x", 0.0f);
                    element.offsetY = yamlFloatOrDefault(node, "offset_y", 0.0f);
                }
                else
                {
                    const LayoutElement *pParent = findElement(parentId);

                    if (pParent != nullptr)
                    {
                        element.zIndex = pParent->zIndex;
                    }

                    const std::optional<LayoutAttachMode> attachTo = parseChildAnchor(anchorNode.as<std::string>());

                    if (!attachTo)
                    {
                        return false;
                    }

                    element.attachTo = *attachTo;
                    element.gapX = yamlFloatOrDefault(node, "offset_x", 0.0f);
                    element.gapY = yamlFloatOrDefault(node, "offset_y", 0.0f);
                }

                const YAML::Node zIndexNode = node["z_index"];

                if (zIndexNode && zIndexNode.IsScalar())
                {
                    element.zIndex = zIndexNode.as<int>();
                }

                element.width = yamlFloatOrDefault(node, "width", 0.0f);
                element.height = yamlFloatOrDefault(node, "height", 0.0f);
                element.bottomToId = yamlStringOrEmpty(node, "bottom_to");
                element.bottomGap = yamlFloatOrDefault(node, "bottom_gap", 0.0f);
                element.visible = yamlBoolOrDefault(node, "visible", true);
                element.interactive = yamlBoolOrDefault(node, "interactive", false);
                element.notes = yamlStringOrEmpty(node, "notes");

                const YAML::Node scaleNode = node["scale"];

                if (scaleNode && scaleNode.IsMap())
                {
                    element.hasExplicitScale = true;
                    element.minScale = yamlFloatOrDefault(scaleNode, "min", 1.0f);
                    element.maxScale = yamlFloatOrDefault(scaleNode, "max", element.minScale);
                }

                const YAML::Node assetNode = node["asset"];

                if (assetNode)
                {
                    if (assetNode.IsScalar())
                    {
                        element.primaryAsset = assetNode.as<std::string>();
                    }
                    else if (assetNode.IsMap())
                    {
                        element.primaryAsset = yamlStringOrEmpty(assetNode, "default");
                        element.hoverAsset = yamlStringOrEmpty(assetNode, "highlighted");

                        if (element.hoverAsset.empty())
                        {
                            element.hoverAsset = yamlStringOrEmpty(assetNode, "hover");
                        }

                        element.pressedAsset = yamlStringOrEmpty(assetNode, "pressed");
                        element.secondaryAsset = yamlStringOrEmpty(assetNode, "selected");
                        element.tertiaryAsset = yamlStringOrEmpty(assetNode, "frame");
                        element.quaternaryAsset = yamlStringOrEmpty(assetNode, "health_bar");
                        element.quinaryAsset = yamlStringOrEmpty(assetNode, "mana_bar");
                    }
                }

                const YAML::Node textNode = node["text"];

                if (textNode && textNode.IsMap())
                {
                    element.fontName = yamlStringOrEmpty(textNode, "font");
                    element.labelText = yamlStringOrEmpty(textNode, "value");
                    const std::string textColor = yamlStringOrEmpty(textNode, "color");

                    const std::optional<TextAlignX> textAlignX = parseTextAlignX(yamlStringOrEmpty(textNode, "align_x"));
                    const std::optional<TextAlignY> textAlignY = parseTextAlignY(yamlStringOrEmpty(textNode, "align_y"));

                    if (!textAlignX || !textAlignY)
                    {
                        return false;
                    }

                    element.textAlignX = *textAlignX;
                    element.textAlignY = *textAlignY;
                    element.textScale = yamlFloatOrDefault(textNode, "scale", 1.0f);
                    element.textPadX = yamlFloatOrDefault(textNode, "pad_x", 0.0f);
                    element.textPadY = yamlFloatOrDefault(textNode, "pad_y", 0.0f);

                    if (!textColor.empty())
                    {
                        const std::string normalizedTextColor = normalizeLayoutToken(textColor);
                        std::string hexTextColor = toLowerCopy(textColor);

                        hexTextColor.erase(
                            std::remove_if(
                                hexTextColor.begin(),
                                hexTextColor.end(),
                                [](char character)
                                {
                                    return character == ' ' || character == '\t';
                                }),
                            hexTextColor.end());

                        if (normalizedTextColor == "white")
                        {
                            element.textColorAbgr = makeAbgrColor(255, 255, 255);
                        }
                        else if (normalizedTextColor == "easternblue")
                        {
                            element.textColorAbgr = makeAbgrColor(21, 153, 233);
                        }
                        else if (hexTextColor.size() == 6
                                 || (hexTextColor.size() == 7 && hexTextColor[0] == '#'))
                        {
                            std::string hex = hexTextColor;

                            if (!hex.empty() && hex[0] == '#')
                            {
                                hex.erase(hex.begin());
                            }

                            if (hex.size() != 6)
                            {
                                return false;
                            }

                            const uint32_t rgb = static_cast<uint32_t>(std::strtoul(hex.c_str(), nullptr, 16));
                            element.textColorAbgr = makeAbgrColor(
                                static_cast<uint8_t>((rgb >> 16) & 0xff),
                                static_cast<uint8_t>((rgb >> 8) & 0xff),
                                static_cast<uint8_t>(rgb & 0xff));
                        }
                        else
                        {
                            return false;
                        }
                    }
                }

                m_layoutOrder.push_back(element.id);
                m_layoutElements[toLowerCopy(element.id)] = element;

                const YAML::Node childrenNode = node["children"];

                if (childrenNode)
                {
                    if (!childrenNode.IsSequence())
                    {
                        return false;
                    }

                    for (const YAML::Node &childNode : childrenNode)
                    {
                        if (!appendElement(childNode, element.id))
                        {
                            return false;
                        }
                    }
                }

                return true;
            };

        for (const YAML::Node &elementNode : elementsNode)
        {
            if (!appendElement(elementNode, ""))
            {
                std::cerr << "HUD layout YAML parse failed in " << path << '\n';
                return false;
            }
        }

        return true;
    }
    catch (const YAML::Exception &exception)
    {
        std::cerr << "HUD layout YAML exception in " << path << ": " << exception.what() << '\n';
        return false;
    }
}

const UiLayoutManager::LayoutElement *UiLayoutManager::findElement(const std::string &layoutId) const
{
    const auto iterator = m_layoutElements.find(toLowerCopy(layoutId));

    if (iterator == m_layoutElements.end())
    {
        return nullptr;
    }

    return &iterator->second;
}

std::vector<std::string> UiLayoutManager::sortedLayoutIdsForScreen(const std::string &screen) const
{
    const std::string normalizedScreen = toLowerCopy(screen);
    const auto cachedIterator = m_sortedLayoutIdsByScreen.find(normalizedScreen);

    if (cachedIterator != m_sortedLayoutIdsByScreen.end())
    {
        return cachedIterator->second;
    }

    std::vector<std::string> result;

    for (const std::string &layoutId : m_layoutOrder)
    {
        const LayoutElement *pLayout = findElement(layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != normalizedScreen)
        {
            continue;
        }

        result.push_back(layoutId);
    }

    std::stable_sort(
        result.begin(),
        result.end(),
        [this](const std::string &leftId, const std::string &rightId)
        {
            const LayoutElement *pLeft = findElement(leftId);
            const LayoutElement *pRight = findElement(rightId);

            if (pLeft == nullptr || pRight == nullptr)
            {
                return false;
            }

            return pLeft->zIndex < pRight->zIndex;
        });

    m_sortedLayoutIdsByScreen[normalizedScreen] = result;
    return result;
}

int UiLayoutManager::maxZIndexForScreen(const std::string &screen) const
{
    int maxZIndex = defaultZIndexForScreen(screen);
    const std::string normalizedScreen = toLowerCopy(screen);

    for (const auto &[id, element] : m_layoutElements)
    {
        (void)id;

        if (toLowerCopy(element.screen) == normalizedScreen)
        {
            maxZIndex = std::max(maxZIndex, element.zIndex);
        }
    }

    return maxZIndex;
}

int UiLayoutManager::defaultZIndexForScreen(const std::string &screen)
{
    if (toLowerCopy(screen) == "outdoorhud")
    {
        return 100;
    }

    return 0;
}

const std::unordered_map<std::string, UiLayoutManager::LayoutElement> &UiLayoutManager::elements() const
{
    return m_layoutElements;
}
}
