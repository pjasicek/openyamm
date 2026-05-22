#include "game/debug/DebugConsole.h"

#include "game/StringUtils.h"
#include "game/tables/MapStats.h"

#include <imgui.h>

#include <algorithm>
#include <cctype>
#include <cstring>
#include <cstdio>
#include <filesystem>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MaxMessages = 400;
constexpr size_t MaxHistory = 64;

std::string upperText(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::toupper(static_cast<unsigned char>(character)));
    }

    return value;
}

bool isDungeonMapFileName(const std::string &mapFileName)
{
    return toLowerCopy(mapFileName).ends_with(".blv");
}

std::string lowerSearchText(std::string_view value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)) != 0)
        {
            result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
        else if (!result.empty() && result.back() != ' ')
        {
            result.push_back(' ');
        }
    }

    while (!result.empty() && result.back() == ' ')
    {
        result.pop_back();
    }

    return result;
}

std::string compactSearchText(std::string_view value)
{
    std::string result;

    for (char character : lowerSearchText(value))
    {
        if (character != ' ')
        {
            result.push_back(character);
        }
    }

    return result;
}

std::vector<std::string> searchTokens(std::string_view query)
{
    std::vector<std::string> tokens;
    std::istringstream stream(lowerSearchText(query));
    std::string token;

    while (stream >> token)
    {
        tokens.push_back(token);
    }

    return tokens;
}

ImVec4 messageColor(DebugConsole::MessageKind kind)
{
    switch (kind)
    {
    case DebugConsole::MessageKind::Success:
        return ImVec4(0.48f, 0.88f, 0.52f, 1.0f);

    case DebugConsole::MessageKind::Warning:
        return ImVec4(0.92f, 0.74f, 0.36f, 1.0f);

    case DebugConsole::MessageKind::Error:
        return ImVec4(0.95f, 0.42f, 0.38f, 1.0f);

    case DebugConsole::MessageKind::Command:
        return ImVec4(0.58f, 0.74f, 0.96f, 1.0f);

    case DebugConsole::MessageKind::Info:
        return ImVec4(0.88f, 0.89f, 0.90f, 1.0f);
    }

    return ImVec4(0.88f, 0.89f, 0.90f, 1.0f);
}

int consoleInputTextCallback(ImGuiInputTextCallbackData *pData)
{
    DebugConsole *pConsole = static_cast<DebugConsole *>(pData->UserData);

    if (pConsole == nullptr)
    {
        return 0;
    }

    return pConsole->handleInputTextCallback(pData);
}
}

void DebugConsole::registerCommand(CommandDefinition definition)
{
    const std::string normalizedName = normalizeCommandName(definition.name);

    if (normalizedName.empty() || !definition.callback)
    {
        return;
    }

    definition.name = normalizedName;
    m_commands[normalizedName] = std::move(definition);
}

void DebugConsole::clearCommands()
{
    m_commands.clear();
}

void DebugConsole::setItemOptions(std::vector<ItemOption> itemOptions)
{
    std::sort(
        itemOptions.begin(),
        itemOptions.end(),
        [](const ItemOption &left, const ItemOption &right)
        {
            return left.itemId < right.itemId;
        });

    m_itemOptions = std::move(itemOptions);

    const auto selectedIt = std::find_if(
        m_itemOptions.begin(),
        m_itemOptions.end(),
        [this](const ItemOption &item)
        {
            return item.itemId == m_selectedItemId;
        });

    if (selectedIt == m_itemOptions.end())
    {
        m_selectedItemId = !m_itemOptions.empty() ? m_itemOptions.front().itemId : 0;
    }
}

void DebugConsole::setMapOptions(std::vector<MapOption> mapOptions)
{
    std::sort(
        mapOptions.begin(),
        mapOptions.end(),
        [](const MapOption &left, const MapOption &right)
        {
            if (left.worldId != right.worldId)
            {
                return left.worldId < right.worldId;
            }

            return left.fileName < right.fileName;
        });

    m_mapOptions = std::move(mapOptions);
    const auto outdoorIt = std::find_if(
        m_mapOptions.begin(),
        m_mapOptions.end(),
        [this](const MapOption &map)
        {
            return map.kind == MapOptionKind::Outdoor && map.mapId == m_selectedOutdoorMapId;
        });
    const auto dungeonIt = std::find_if(
        m_mapOptions.begin(),
        m_mapOptions.end(),
        [this](const MapOption &map)
        {
            return map.kind == MapOptionKind::Dungeon && map.mapId == m_selectedDungeonMapId;
        });

    if (outdoorIt == m_mapOptions.end())
    {
        const auto firstOutdoorIt = std::find_if(
            m_mapOptions.begin(),
            m_mapOptions.end(),
            [](const MapOption &map)
            {
                return map.kind == MapOptionKind::Outdoor;
            });
        m_selectedOutdoorMapId = firstOutdoorIt != m_mapOptions.end() ? firstOutdoorIt->mapId : 0;
    }

    if (dungeonIt == m_mapOptions.end())
    {
        const auto firstDungeonIt = std::find_if(
            m_mapOptions.begin(),
            m_mapOptions.end(),
            [](const MapOption &map)
            {
                return map.kind == MapOptionKind::Dungeon;
            });
        m_selectedDungeonMapId = firstDungeonIt != m_mapOptions.end() ? firstDungeonIt->mapId : 0;
    }
}

void DebugConsole::setMapOptionsFromMapStats(const MapStats &mapStats)
{
    std::vector<MapOption> mapOptions;

    for (const MapStatsEntry &map : mapStats.getEntries())
    {
        if (map.fileName.empty())
        {
            continue;
        }

        MapOption option = {};
        option.mapId = map.id;
        option.worldId = map.worldId;
        option.fileName = std::filesystem::path(map.fileName).stem().string();
        option.displayName = map.name.empty() ? map.fileName : map.name;
        option.kind = isDungeonMapFileName(map.fileName)
            ? MapOptionKind::Dungeon
            : MapOptionKind::Outdoor;

        mapOptions.push_back(std::move(option));
    }

    setMapOptions(std::move(mapOptions));
}

void DebugConsole::setDebugToggleStates(bool immortal, bool unlimitedMana, bool invisible)
{
    m_debugImmortal = immortal;
    m_debugUnlimitedMana = unlimitedMana;
    m_debugInvisible = invisible;
}

void DebugConsole::setEnabled(bool enabled)
{
    m_enabled = enabled;
    m_scrollToBottom = true;
}

void DebugConsole::toggleEnabled()
{
    setEnabled(!m_enabled);
}

bool DebugConsole::enabled() const
{
    return m_enabled;
}

bool DebugConsole::wantsGameplayInputBlocked() const
{
    return m_enabled;
}

bool DebugConsole::freezesGameplay() const
{
    return m_enabled && m_freezeGameplay;
}

void DebugConsole::addMessage(MessageKind kind, const std::string &message)
{
    if (message.empty())
    {
        return;
    }

    m_messages.push_back({kind, message});

    if (m_messages.size() > MaxMessages)
    {
        m_messages.erase(m_messages.begin(), m_messages.begin() + static_cast<std::ptrdiff_t>(
            m_messages.size() - MaxMessages));
    }

    m_scrollToBottom = true;
}

void DebugConsole::clearMessages()
{
    m_messages.clear();
}

void DebugConsole::executeLine(const std::string &line)
{
    const std::vector<std::string> commandLines = splitCommandLine(line);
    bool hasCommand = false;

    for (const std::string &commandLine : commandLines)
    {
        if (!tokenize(commandLine).empty())
        {
            hasCommand = true;
            break;
        }
    }

    if (!hasCommand)
    {
        return;
    }

    addMessage(MessageKind::Command, "> " + line);
    m_focusCommandInput = true;

    if (m_history.empty() || m_history.back() != line)
    {
        m_history.push_back(line);

        if (m_history.size() > MaxHistory)
        {
            m_history.erase(m_history.begin());
        }
    }

    m_historyCursor = m_history.size();

    for (const std::string &commandLine : commandLines)
    {
        const std::vector<std::string> tokens = tokenize(commandLine);

        if (tokens.empty())
        {
            continue;
        }

        const std::string commandName = normalizeCommandName(tokens.front());
        const auto commandIt = m_commands.find(commandName);

        if (commandIt == m_commands.end())
        {
            addMessage(MessageKind::Error, "Unknown command: " + tokens.front());
            continue;
        }

        CommandContext context = {};
        context.args.assign(tokens.begin() + 1, tokens.end());
        const CommandResult result = commandIt->second.callback(context);

        if (!result.message.empty())
        {
            addMessage(result.success ? MessageKind::Success : MessageKind::Error, result.message);
        }
    }
}

void DebugConsole::render(int width, int height)
{
    if (!m_enabled)
    {
        return;
    }

    renderConsoleWindow(width, height);
}

int DebugConsole::handleInputTextCallback(ImGuiInputTextCallbackData *pData)
{
    if (pData == nullptr || pData->EventFlag != ImGuiInputTextFlags_CallbackHistory)
    {
        return 0;
    }

    if (m_history.empty())
    {
        return 0;
    }

    if (pData->EventKey == ImGuiKey_UpArrow)
    {
        if (m_historyCursor > 0)
        {
            --m_historyCursor;
        }
    }
    else if (pData->EventKey == ImGuiKey_DownArrow)
    {
        if (m_historyCursor < m_history.size())
        {
            ++m_historyCursor;
        }
    }

    const std::string replacement = m_historyCursor < m_history.size() ? m_history[m_historyCursor] : std::string();
    pData->DeleteChars(0, pData->BufTextLen);
    pData->InsertChars(0, replacement.c_str());
    return 0;
}

std::string DebugConsole::normalizeCommandName(std::string_view name)
{
    std::string result(name);

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::vector<std::string> DebugConsole::splitCommandLine(std::string_view line)
{
    std::vector<std::string> commandLines;
    std::string current;
    bool inQuotes = false;

    for (char character : line)
    {
        if (character == '"')
        {
            inQuotes = !inQuotes;
            current.push_back(character);
            continue;
        }

        if (!inQuotes && character == ';')
        {
            commandLines.push_back(current);
            current.clear();
            continue;
        }

        current.push_back(character);
    }

    commandLines.push_back(current);
    return commandLines;
}

std::vector<std::string> DebugConsole::tokenize(std::string_view line)
{
    std::vector<std::string> tokens;
    std::string current;
    bool inQuotes = false;

    for (char character : line)
    {
        if (character == '"')
        {
            inQuotes = !inQuotes;
            continue;
        }

        if (!inQuotes && std::isspace(static_cast<unsigned char>(character)) != 0)
        {
            if (!current.empty())
            {
                tokens.push_back(current);
                current.clear();
            }

            continue;
        }

        current.push_back(character);
    }

    if (!current.empty())
    {
        tokens.push_back(current);
    }

    return tokens;
}

int DebugConsole::itemOptionSearchScore(const ItemOption &item, const std::string &query)
{
    const std::string normalizedQuery = lowerSearchText(query);
    const std::string compactQuery = compactSearchText(query);

    if (normalizedQuery.empty())
    {
        return 1;
    }

    const std::string idText = std::to_string(item.itemId);
    int score = 0;

    if (idText == normalizedQuery)
    {
        score = std::max(score, 30000);
    }

    if (idText.find(normalizedQuery) == 0)
    {
        score = std::max(score, 22000 - static_cast<int>(idText.size()));
    }

    const std::string name = lowerSearchText(item.name);
    const std::string unidentifiedName = lowerSearchText(item.unidentifiedName);
    const std::string haystack =
        item.name + " " + item.unidentifiedName + " " + item.iconName + " " + item.skillGroup + " " + item.notes;
    const std::string normalizedHaystack = lowerSearchText(haystack);
    const std::string compactHaystack = compactSearchText(haystack);

    if (name == normalizedQuery)
    {
        score = std::max(score, 20000 - static_cast<int>(item.name.size()));
    }

    if (name.find(normalizedQuery) == 0)
    {
        score = std::max(score, 18000 - static_cast<int>(item.name.size()));
    }

    if (!unidentifiedName.empty() && unidentifiedName.find(normalizedQuery) == 0)
    {
        score = std::max(score, 16000 - static_cast<int>(item.unidentifiedName.size()));
    }

    if (!compactQuery.empty())
    {
        const size_t namePosition = compactSearchText(item.name).find(compactQuery);

        if (namePosition != std::string::npos)
        {
            score = std::max(score, 12000 - static_cast<int>(namePosition));
        }

        const size_t haystackPosition = compactHaystack.find(compactQuery);

        if (haystackPosition != std::string::npos)
        {
            score = std::max(score, 9000 - static_cast<int>(haystackPosition));
        }
    }

    const std::vector<std::string> tokens = searchTokens(query);
    int tokenScore = 0;

    for (const std::string &token : tokens)
    {
        if (normalizedHaystack.find(token) == std::string::npos)
        {
            tokenScore = 0;
            break;
        }

        tokenScore += 600;
    }

    return std::max(score, tokenScore);
}

int DebugConsole::mapOptionSearchScore(const MapOption &map, const std::string &query)
{
    const std::string normalizedQuery = lowerSearchText(query);
    const std::string compactQuery = compactSearchText(query);

    if (normalizedQuery.empty())
    {
        return 1;
    }

    const std::string idText = std::to_string(map.mapId);
    int score = 0;

    if (idText == normalizedQuery)
    {
        score = std::max(score, 30000);
    }

    if (idText.find(normalizedQuery) == 0)
    {
        score = std::max(score, 22000 - static_cast<int>(idText.size()));
    }

    const std::string fileName = lowerSearchText(map.fileName);
    const std::string displayName = lowerSearchText(map.displayName);
    const std::string haystack = map.worldId + " " + map.fileName + " " + map.displayName;
    const std::string normalizedHaystack = lowerSearchText(haystack);
    const std::string compactHaystack = compactSearchText(haystack);

    if (fileName == normalizedQuery || displayName == normalizedQuery)
    {
        score = std::max(score, 20000);
    }

    if (fileName.find(normalizedQuery) == 0 || displayName.find(normalizedQuery) == 0)
    {
        score = std::max(score, 18000 - static_cast<int>(map.displayName.size()));
    }

    if (!compactQuery.empty())
    {
        const size_t haystackPosition = compactHaystack.find(compactQuery);

        if (haystackPosition != std::string::npos)
        {
            score = std::max(score, 10000 - static_cast<int>(haystackPosition));
        }
    }

    const std::vector<std::string> tokens = searchTokens(query);
    int tokenScore = 0;

    for (const std::string &token : tokens)
    {
        if (normalizedHaystack.find(token) == std::string::npos)
        {
            tokenScore = 0;
            break;
        }

        tokenScore += 600;
    }

    return std::max(score, tokenScore);
}

void DebugConsole::renderConsoleWindow(int width, int height)
{
#if defined(__ANDROID__)
    renderMobileConsoleWindow(width, height);
    return;
#endif

    const float windowWidth = std::max(640.0f, static_cast<float>(width));
    const float minWindowHeight = std::min(300.0f, std::max(220.0f, static_cast<float>(height) - 48.0f));
    const float maxWindowHeight = std::max(minWindowHeight, static_cast<float>(height) - 24.0f);

    if (m_windowHeight <= 0.0f)
    {
        m_windowHeight = std::clamp(
            static_cast<float>(height) * 0.52f,
            minWindowHeight,
            std::min(maxWindowHeight, 540.0f));
    }

    m_windowHeight = std::clamp(m_windowHeight, minWindowHeight, maxWindowHeight);
    const float windowHeight = m_windowHeight;
    ImGui::SetNextWindowPos(ImVec2(0.0f, 0.0f), ImGuiCond_Always);
    ImGui::SetNextWindowSize(ImVec2(windowWidth, windowHeight), ImGuiCond_Always);

    const ImGuiWindowFlags flags =
        ImGuiWindowFlags_NoTitleBar
        | ImGuiWindowFlags_NoCollapse
        | ImGuiWindowFlags_NoMove
        | ImGuiWindowFlags_NoResize;

    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);

    if (!ImGui::Begin("OpenYAMM Console", &m_enabled, flags))
    {
        ImGui::End();
        ImGui::PopStyleVar(2);
        return;
    }

    ImGui::TextUnformatted("OpenYAMM Console");
    ImGui::SameLine();
    ImGui::Checkbox("Freeze", &m_freezeGameplay);
    ImGui::SameLine();
    ImGui::Checkbox("Help", &m_showHelpPanel);
    ImGui::SameLine();

    if (ImGui::Button("Clear"))
    {
        clearMessages();
    }

    ImGui::Separator();
    const float inputHeight = ImGui::GetFrameHeightWithSpacing();
    const float resizeHandleHeight = 8.0f;
    const float contentHeight =
        std::max(100.0f, ImGui::GetContentRegionAvail().y - inputHeight - resizeHandleHeight - 6.0f);
    const float helpWidth = m_showHelpPanel ? std::clamp(windowWidth * 0.42f, 560.0f, 680.0f) : 0.0f;
    const float consoleWidth = m_showHelpPanel ? ImGui::GetContentRegionAvail().x - helpWidth - 10.0f : 0.0f;

    if (ImGui::BeginChild("Messages", ImVec2(consoleWidth, contentHeight), true))
    {
        for (const Message &message : m_messages)
        {
            ImGui::PushStyleColor(ImGuiCol_Text, messageColor(message.kind));
            ImGui::TextWrapped("%s", message.text.c_str());
            ImGui::PopStyleColor();
        }

        if (m_scrollToBottom)
        {
            ImGui::SetScrollHereY(1.0f);
            m_scrollToBottom = false;
        }
    }

    ImGui::EndChild();

    if (m_showHelpPanel)
    {
        ImGui::SameLine();

        const ImVec2 separatorTop = ImGui::GetCursorScreenPos();
        ImDrawList *pDrawList = ImGui::GetWindowDrawList();
        pDrawList->AddLine(
            separatorTop,
            ImVec2(separatorTop.x, separatorTop.y + contentHeight),
            ImGui::GetColorU32(ImGuiCol_Separator),
            1.0f);
        ImGui::Dummy(ImVec2(1.0f, contentHeight));
        ImGui::SameLine();

        if (ImGui::BeginChild("ConsoleHelpPanel", ImVec2(0.0f, contentHeight), false))
        {
            renderHelpPanelContents();
        }

        ImGui::EndChild();
    }

    ImGui::PushItemWidth(-62.0f);

    if (m_focusCommandInput)
    {
        ImGui::SetKeyboardFocusHere();
        m_focusCommandInput = false;
    }

    const bool submitted = ImGui::InputText(
        "##ConsoleInput",
        m_inputBuffer,
        sizeof(m_inputBuffer),
        ImGuiInputTextFlags_EnterReturnsTrue | ImGuiInputTextFlags_CallbackHistory,
        consoleInputTextCallback,
        this);
    ImGui::PopItemWidth();
    ImGui::SameLine();

    if (ImGui::Button("Send") || submitted)
    {
        const std::string line = m_inputBuffer;
        std::memset(m_inputBuffer, 0, sizeof(m_inputBuffer));
        executeLine(line);
        m_focusCommandInput = true;
    }

    const ImVec2 windowPosition = ImGui::GetWindowPos();
    const ImVec2 windowSize = ImGui::GetWindowSize();
    ImGui::SetCursorScreenPos(ImVec2(windowPosition.x, windowPosition.y + windowSize.y - resizeHandleHeight));
    ImGui::InvisibleButton("##ConsoleResizeBottom", ImVec2(windowSize.x, resizeHandleHeight));

    if (ImGui::IsItemHovered() || ImGui::IsItemActive())
    {
        ImGui::SetMouseCursor(ImGuiMouseCursor_ResizeNS);
    }

    if (ImGui::IsItemActive())
    {
        m_windowHeight = std::clamp(
            m_windowHeight + ImGui::GetIO().MouseDelta.y,
            minWindowHeight,
            maxWindowHeight);
    }

    ImGui::End();
    ImGui::PopStyleVar(2);
}

void DebugConsole::renderMobileConsoleWindow(int width, int height)
{
    const float windowWidth = std::max(1.0f, static_cast<float>(width));
    const float windowHeight = std::max(1.0f, static_cast<float>(height));
    const float layoutScale = std::clamp(
        std::min(windowWidth / 960.0f, windowHeight / 540.0f) * 1.2f,
        1.55f,
        2.45f);
    const bool wasRenderingMobileConsole = m_renderingMobileConsole;
    const float previousMobileConsoleScale = m_activeMobileConsoleScale;
    m_renderingMobileConsole = true;
    m_activeMobileConsoleScale = layoutScale;

    ImGui::SetNextWindowPos(ImVec2(0.0f, 0.0f), ImGuiCond_Always);
    ImGui::SetNextWindowSize(ImVec2(windowWidth, windowHeight), ImGuiCond_Always);
    ImGui::SetNextWindowBgAlpha(0.96f);

    const ImGuiWindowFlags flags =
        ImGuiWindowFlags_NoTitleBar
        | ImGuiWindowFlags_NoCollapse
        | ImGuiWindowFlags_NoMove
        | ImGuiWindowFlags_NoResize
        | ImGuiWindowFlags_NoSavedSettings;

    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(8.0f * layoutScale, 7.0f * layoutScale));
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(8.0f * layoutScale, 5.0f * layoutScale));
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(8.0f * layoutScale, 6.0f * layoutScale));

    if (!ImGui::Begin("OpenYAMM Console", &m_enabled, flags))
    {
        ImGui::End();
        ImGui::PopStyleVar(5);
        m_renderingMobileConsole = wasRenderingMobileConsole;
        m_activeMobileConsoleScale = previousMobileConsoleScale;
        return;
    }

    applyActiveMobileConsoleScale();

    ImGui::TextUnformatted("OpenYAMM Console");
    ImGui::SameLine();
    ImGui::Checkbox("Freeze", &m_freezeGameplay);
    ImGui::SameLine();
    ImGui::Checkbox("Tools", &m_showHelpPanel);
    ImGui::SameLine();

    if (ImGui::Button("Clear"))
    {
        clearMessages();
    }

    ImGui::SameLine();

    if (ImGui::Button("Close"))
    {
        m_enabled = false;
    }

    ImGui::Separator();

    const float spacing = ImGui::GetStyle().ItemSpacing.x;
    const float inputHeight = ImGui::GetFrameHeightWithSpacing();
    const float contentHeight = std::max(120.0f, ImGui::GetContentRegionAvail().y - inputHeight - spacing);
    const float availableWidth = ImGui::GetContentRegionAvail().x;
    const float maxToolsWidth = std::max(0.0f, availableWidth - 360.0f * layoutScale);
    const float minToolsWidth = std::min(500.0f * layoutScale, maxToolsWidth);
    const float toolsWidth = m_showHelpPanel
        ? std::clamp(availableWidth * 0.6f, minToolsWidth, maxToolsWidth)
        : 0.0f;
    const float messagesWidth = m_showHelpPanel
        ? std::max(320.0f * layoutScale, availableWidth - toolsWidth - spacing)
        : 0.0f;

    if (ImGui::BeginChild("MobileConsoleMessages", ImVec2(messagesWidth, contentHeight), true))
    {
        applyActiveMobileConsoleScale();

        for (const Message &message : m_messages)
        {
            ImGui::PushStyleColor(ImGuiCol_Text, messageColor(message.kind));
            ImGui::TextWrapped("%s", message.text.c_str());
            ImGui::PopStyleColor();
        }

        if (m_scrollToBottom)
        {
            ImGui::SetScrollHereY(1.0f);
            m_scrollToBottom = false;
        }
    }

    ImGui::EndChild();

    if (m_showHelpPanel)
    {
        ImGui::SameLine();

        if (ImGui::BeginChild("MobileConsoleTools", ImVec2(0.0f, contentHeight), true))
        {
            applyActiveMobileConsoleScale();
            renderMobileHelpPanelContents();
        }

        ImGui::EndChild();
    }

    ImGui::PushItemWidth(-(88.0f * layoutScale));

    if (m_focusCommandInput)
    {
        ImGui::SetKeyboardFocusHere();
        m_focusCommandInput = false;
    }

    const bool submitted = ImGui::InputText(
        "##MobileConsoleInput",
        m_inputBuffer,
        sizeof(m_inputBuffer),
        ImGuiInputTextFlags_EnterReturnsTrue | ImGuiInputTextFlags_CallbackHistory,
        consoleInputTextCallback,
        this);
    ImGui::PopItemWidth();
    ImGui::SameLine();

    if (ImGui::Button("Run", ImVec2(80.0f * layoutScale, 0.0f)) || submitted)
    {
        const std::string line = m_inputBuffer;
        std::memset(m_inputBuffer, 0, sizeof(m_inputBuffer));
        executeLine(line);
        m_focusCommandInput = true;
    }

    ImGui::End();
    ImGui::PopStyleVar(5);
    m_renderingMobileConsole = wasRenderingMobileConsole;
    m_activeMobileConsoleScale = previousMobileConsoleScale;
}

void DebugConsole::renderHelpPanelContents()
{
    const float contentHeight = ImGui::GetContentRegionAvail().y;
    const float separatorWidth = 1.0f;
    const float spacing = ImGui::GetStyle().ItemSpacing.x;
    const float availableWidth = ImGui::GetContentRegionAvail().x;
    const float columnWidth = std::max(220.0f, (availableWidth - separatorWidth - spacing * 2.0f) * 0.5f);

    if (ImGui::BeginChild("ConsoleToolsLeft", ImVec2(columnWidth, contentHeight), false))
    {
        renderMapControls();
        renderItemPicker();
    }

    ImGui::EndChild();
    ImGui::SameLine();

    const ImVec2 separatorTop = ImGui::GetCursorScreenPos();
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    pDrawList->AddLine(
        separatorTop,
        ImVec2(separatorTop.x, separatorTop.y + contentHeight),
        ImGui::GetColorU32(ImGuiCol_Separator),
        1.0f);
    ImGui::Dummy(ImVec2(separatorWidth, contentHeight));
    ImGui::SameLine();

    if (ImGui::BeginChild("ConsoleToolsRight", ImVec2(0.0f, contentHeight), false))
    {
        renderQuickActions();
        renderQuestBitControls();
        renderAwardControls();

        ImGui::Separator();
        renderHelpText();
    }

    ImGui::EndChild();
}

void DebugConsole::renderMobileHelpPanelContents()
{
    const ImGuiTableFlags tableFlags =
        ImGuiTableFlags_BordersInnerV
        | ImGuiTableFlags_Resizable
        | ImGuiTableFlags_SizingStretchProp;

    if (!ImGui::BeginTable("MobileConsoleToolColumns", 3, tableFlags, ImVec2(-1.0f, 0.0f)))
    {
        return;
    }

    ImGui::TableSetupColumn("Quick", ImGuiTableColumnFlags_WidthStretch, 0.85f);
    ImGui::TableSetupColumn("Maps", ImGuiTableColumnFlags_WidthStretch, 1.55f);
    ImGui::TableSetupColumn("Items", ImGuiTableColumnFlags_WidthStretch, 1.6f);
    ImGui::TableHeadersRow();

    ImGui::TableNextRow();
    ImGui::TableSetColumnIndex(0);
    renderMobileQuickActions();

    ImGui::TableSetColumnIndex(1);
    renderMapControls();

    ImGui::TableSetColumnIndex(2);
    renderItemPicker();

    ImGui::EndTable();
}

void DebugConsole::renderMobileQuickActions()
{
    const auto toggleLabel = [](std::string_view name, bool value)
    {
        std::string label(name);
        label += value ? " [On]" : " [Off]";
        return label;
    };

    const auto commandButton =
        [this](const char *pLabel, const char *pCommand)
        {
            if (ImGui::Button(pLabel, ImVec2(-1.0f, 0.0f)))
            {
                executeLine(pCommand);
            }
        };

    ImGui::SeparatorText("Quick");
    commandButton("Map Info", "map");
    commandButton("Full Heal", "hp full");
    commandButton("Next Day", "time advance 1");
    commandButton("Set up Breach", "setup breach");

    if (ImGui::Button("Clear Log", ImVec2(-1.0f, 0.0f)))
    {
        clearMessages();
    }

    const std::string immortalLabel = toggleLabel("Immortal", m_debugImmortal);
    const std::string manaLabel = toggleLabel("Unlimited Mana", m_debugUnlimitedMana);
    const std::string invisibleLabel = toggleLabel("Invisible", m_debugInvisible);

    commandButton(immortalLabel.c_str(), "config toggle immortal");
    commandButton(manaLabel.c_str(), "config toggle unlimited_mana");
    commandButton(invisibleLabel.c_str(), "config toggle invisible");
}

void DebugConsole::renderMobileQuestBitControls()
{
    ImGui::SeparatorText("QBits");

    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##MobileQBitSet", m_qbitSetBuffer, sizeof(m_qbitSetBuffer));
    ImGui::PopItemWidth();

    if (ImGui::Button("Set QBit", ImVec2(-1.0f, 0.0f)))
    {
        if (m_qbitSetBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Set QBit needs an id.");
        }
        else
        {
            executeLine(std::string("qbit set ") + m_qbitSetBuffer);
        }
    }

    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##MobileQBitClear", m_qbitClearBuffer, sizeof(m_qbitClearBuffer));
    ImGui::PopItemWidth();

    if (ImGui::Button("Clear QBit", ImVec2(-1.0f, 0.0f)))
    {
        if (m_qbitClearBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Clear QBit needs an id.");
        }
        else
        {
            executeLine(std::string("qbit clear ") + m_qbitClearBuffer);
        }
    }

    if (ImGui::Button("Dump Active QBits", ImVec2(-1.0f, 0.0f)))
    {
        executeLine("qbit dump active");
    }

    if (ImGui::Button("Dump All QBits", ImVec2(-1.0f, 0.0f)))
    {
        executeLine("qbit dump all");
    }
}

void DebugConsole::renderMobileAwardControls()
{
    ImGui::SeparatorText("Awards");

    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##MobileAwardSet", m_awardSetBuffer, sizeof(m_awardSetBuffer));
    ImGui::PopItemWidth();

    if (ImGui::Button("Set Award", ImVec2(-1.0f, 0.0f)))
    {
        if (m_awardSetBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Set Award needs an id.");
        }
        else
        {
            executeLine(std::string("award set ") + m_awardSetBuffer);
        }
    }

    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##MobileAwardClear", m_awardClearBuffer, sizeof(m_awardClearBuffer));
    ImGui::PopItemWidth();

    if (ImGui::Button("Clear Award", ImVec2(-1.0f, 0.0f)))
    {
        if (m_awardClearBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Clear Award needs an id.");
        }
        else
        {
            executeLine(std::string("award clear ") + m_awardClearBuffer);
        }
    }

    if (ImGui::Button("Dump Active Awards", ImVec2(-1.0f, 0.0f)))
    {
        executeLine("award dump active");
    }

    if (ImGui::Button("Dump All Awards", ImVec2(-1.0f, 0.0f)))
    {
        executeLine("award dump all");
    }
}

float DebugConsole::activeMobileConsoleScale() const
{
    return m_renderingMobileConsole ? std::max(1.0f, m_activeMobileConsoleScale) : 1.0f;
}

void DebugConsole::applyActiveMobileConsoleScale() const
{
    if (m_renderingMobileConsole)
    {
        ImGui::SetWindowFontScale(activeMobileConsoleScale());
    }
}

void DebugConsole::renderQuickActions()
{
    const auto toggleLabel = [](std::string_view name, bool value)
    {
        std::string label(name);
        label += value ? " [On]" : " [Off]";
        return label;
    };

    ImGui::SeparatorText("Quick");

    if (ImGui::SmallButton("Map Info"))
    {
        executeLine("map");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton("Full Heal"))
    {
        executeLine("hp full");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton("Next Day"))
    {
        executeLine("time advance 1");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton("Set up Breach"))
    {
        executeLine("setup breach");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton("Clear Log"))
    {
        clearMessages();
    }

    const std::string immortalLabel = toggleLabel("Immortal", m_debugImmortal);
    const std::string manaLabel = toggleLabel("Unlimited Mana", m_debugUnlimitedMana);
    const std::string invisibleLabel = toggleLabel("Invisible", m_debugInvisible);

    if (ImGui::SmallButton(immortalLabel.c_str()))
    {
        executeLine("config toggle immortal");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton(manaLabel.c_str()))
    {
        executeLine("config toggle unlimited_mana");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton(invisibleLabel.c_str()))
    {
        executeLine("config toggle invisible");
    }
}

void DebugConsole::renderQuestBitControls()
{
    ImGui::SeparatorText("QBits");

    if (ImGui::SmallButton("Set QBit"))
    {
        if (m_qbitSetBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Set QBit needs an id.");
        }
        else
        {
            executeLine(std::string("qbit set ") + m_qbitSetBuffer);
        }
    }

    ImGui::SameLine();
    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##QBitSet", m_qbitSetBuffer, sizeof(m_qbitSetBuffer));
    ImGui::PopItemWidth();

    if (ImGui::SmallButton("Clear QBit"))
    {
        if (m_qbitClearBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Clear QBit needs an id.");
        }
        else
        {
            executeLine(std::string("qbit clear ") + m_qbitClearBuffer);
        }
    }

    ImGui::SameLine();
    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##QBitClear", m_qbitClearBuffer, sizeof(m_qbitClearBuffer));
    ImGui::PopItemWidth();

    if (ImGui::SmallButton("Dump QBits"))
    {
        executeLine("qbit dump active");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton("Dump All QBits"))
    {
        executeLine("qbit dump all");
    }
}

void DebugConsole::renderAwardControls()
{
    ImGui::SeparatorText("Awards");

    if (ImGui::SmallButton("Set Award"))
    {
        if (m_awardSetBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Set Award needs an id.");
        }
        else
        {
            executeLine(std::string("award set ") + m_awardSetBuffer);
        }
    }

    ImGui::SameLine();
    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##AwardSet", m_awardSetBuffer, sizeof(m_awardSetBuffer));
    ImGui::PopItemWidth();

    if (ImGui::SmallButton("Clear Award"))
    {
        if (m_awardClearBuffer[0] == '\0')
        {
            addMessage(MessageKind::Error, "Clear Award needs an id.");
        }
        else
        {
            executeLine(std::string("award clear ") + m_awardClearBuffer);
        }
    }

    ImGui::SameLine();
    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("##AwardClear", m_awardClearBuffer, sizeof(m_awardClearBuffer));
    ImGui::PopItemWidth();

    if (ImGui::SmallButton("Dump Awards"))
    {
        executeLine("award dump active");
    }

    ImGui::SameLine();

    if (ImGui::SmallButton("Dump All Awards"))
    {
        executeLine("award dump all");
    }
}

void DebugConsole::renderMapControls()
{
    ImGui::SeparatorText("Map Jump");
    renderMapPicker(
        MapOptionKind::Outdoor,
        "Outdoor",
        m_outdoorMapSearchBuffer,
        sizeof(m_outdoorMapSearchBuffer));
    renderMapPicker(
        MapOptionKind::Dungeon,
        "Dungeon",
        m_dungeonMapSearchBuffer,
        sizeof(m_dungeonMapSearchBuffer));
}

void DebugConsole::renderMapPicker(
    MapOptionKind kind,
    const char *label,
    char *pSearchBuffer,
    size_t searchBufferSize)
{
    struct ScoredMap
    {
        const MapOption *pMap = nullptr;
        int score = 0;
    };

    ImGui::TextUnformatted(label);
    ImGui::SameLine();
    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText((std::string("##MapSearch") + label).c_str(), pSearchBuffer, searchBufferSize);
    ImGui::PopItemWidth();

    std::vector<ScoredMap> matches;

    for (const MapOption &map : m_mapOptions)
    {
        if (map.kind != kind)
        {
            continue;
        }

        const int score = mapOptionSearchScore(map, pSearchBuffer);

        if (score > 0)
        {
            matches.push_back({.pMap = &map, .score = score});
        }
    }

    std::sort(
        matches.begin(),
        matches.end(),
        [](const ScoredMap &left, const ScoredMap &right)
        {
            if (left.score != right.score)
            {
                return left.score > right.score;
            }

            return left.pMap->mapId < right.pMap->mapId;
        });

    int &selectedMapId = kind == MapOptionKind::Outdoor ? m_selectedOutdoorMapId : m_selectedDungeonMapId;
    const bool selectedVisible = std::find_if(
        matches.begin(),
        matches.end(),
        [&selectedMapId](const ScoredMap &match)
        {
            return match.pMap != nullptr && match.pMap->mapId == selectedMapId;
        }) != matches.end();

    if (!selectedVisible)
    {
        selectedMapId = !matches.empty() && matches.front().pMap != nullptr ? matches.front().pMap->mapId : 0;
    }

    const float mobileScale = activeMobileConsoleScale();

    if (ImGui::BeginListBox(
            (std::string("##MapSelect") + label).c_str(),
            ImVec2(-1.0f, 86.0f * mobileScale)))
    {
        applyActiveMobileConsoleScale();

        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(matches.size()));

        while (clipper.Step())
        {
            for (int rowIndex = clipper.DisplayStart; rowIndex < clipper.DisplayEnd; ++rowIndex)
            {
                const MapOption &map = *matches[static_cast<size_t>(rowIndex)].pMap;
                const bool selected = map.mapId == selectedMapId;
                const std::string rowLabel =
                    "[" + upperText(map.worldId) + "] " + map.fileName + " - " + map.displayName;

                if (selected)
                {
                    ImGui::PushStyleColor(ImGuiCol_Header, ImVec4(0.78f, 0.55f, 0.18f, 0.95f));
                    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, ImVec4(0.88f, 0.62f, 0.22f, 1.0f));
                    ImGui::PushStyleColor(ImGuiCol_HeaderActive, ImVec4(0.95f, 0.68f, 0.26f, 1.0f));
                    ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.08f, 0.07f, 0.05f, 1.0f));
                }

                if (ImGui::Selectable(rowLabel.c_str(), selected))
                {
                    selectedMapId = map.mapId;
                    executeLine("goto " + std::to_string(map.mapId));
                }

                if (selected)
                {
                    ImGui::PopStyleColor(4);
                    ImGui::SetItemDefaultFocus();
                }
            }
        }

        if (matches.empty())
        {
            ImGui::TextDisabled("No matching maps.");
        }

        ImGui::EndListBox();
    }
}

void DebugConsole::renderItemPicker()
{
    struct ScoredItem
    {
        const ItemOption *pItem = nullptr;
        int score = 0;
    };

    ImGui::SeparatorText("Give Item");
    ImGui::PushItemWidth(-1.0f);
    ImGui::InputText("Search", m_itemSearchBuffer, sizeof(m_itemSearchBuffer));
    ImGui::PopItemWidth();
    ImGui::SetItemTooltip("Search by item id, name, unidentified name, icon, skill group, or notes.");

    std::vector<ScoredItem> matches;
    matches.reserve(m_itemOptions.size());

    for (const ItemOption &item : m_itemOptions)
    {
        const int score = itemOptionSearchScore(item, m_itemSearchBuffer);

        if (score > 0)
        {
            matches.push_back({.pItem = &item, .score = score});
        }
    }

    std::sort(
        matches.begin(),
        matches.end(),
        [](const ScoredItem &left, const ScoredItem &right)
        {
            if (left.score != right.score)
            {
                return left.score > right.score;
            }

            return left.pItem->itemId < right.pItem->itemId;
        });

    const bool selectedVisible = std::find_if(
        matches.begin(),
        matches.end(),
        [this](const ScoredItem &match)
        {
            return match.pItem != nullptr && match.pItem->itemId == m_selectedItemId;
        }) != matches.end();

    if (!selectedVisible)
    {
        m_selectedItemId = !matches.empty() && matches.front().pItem != nullptr ? matches.front().pItem->itemId : 0;
    }

    const float mobileScale = activeMobileConsoleScale();

    if (ImGui::BeginListBox("##ItemSelect", ImVec2(-1.0f, 156.0f * mobileScale)))
    {
        applyActiveMobileConsoleScale();

        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(matches.size()));

        while (clipper.Step())
        {
            for (int rowIndex = clipper.DisplayStart; rowIndex < clipper.DisplayEnd; ++rowIndex)
            {
                const ItemOption &item = *matches[static_cast<size_t>(rowIndex)].pItem;
                const bool selected = item.itemId == m_selectedItemId;
                char itemLabel[384] = {};
                std::snprintf(itemLabel, sizeof(itemLabel), "%u  %s", item.itemId, item.name.c_str());

                if (selected)
                {
                    ImGui::PushStyleColor(ImGuiCol_Header, ImVec4(0.78f, 0.55f, 0.18f, 0.95f));
                    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, ImVec4(0.88f, 0.62f, 0.22f, 1.0f));
                    ImGui::PushStyleColor(ImGuiCol_HeaderActive, ImVec4(0.95f, 0.68f, 0.26f, 1.0f));
                    ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.08f, 0.07f, 0.05f, 1.0f));
                }

                const bool activated = ImGui::Selectable(itemLabel, selected);
                const bool doubleClicked = ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left);

                if (activated)
                {
                    m_selectedItemId = item.itemId;

                    if (doubleClicked)
                    {
                        giveSelectedItem();
                    }
                }
                else if (doubleClicked)
                {
                    m_selectedItemId = item.itemId;
                    giveSelectedItem();
                }

                if (selected)
                {
                    ImGui::PopStyleColor(4);
                    ImGui::SetItemDefaultFocus();
                }

                if (ImGui::IsItemHovered())
                {
                    ImGui::BeginTooltip();
                    ImGui::Text("%u  %s", item.itemId, item.name.c_str());

                    if (!item.unidentifiedName.empty() && item.unidentifiedName != item.name)
                    {
                        ImGui::Text("Unidentified: %s", item.unidentifiedName.c_str());
                    }

                    if (!item.skillGroup.empty())
                    {
                        ImGui::Text("Group: %s", item.skillGroup.c_str());
                    }

                    if (!item.iconName.empty())
                    {
                        ImGui::Text("Icon: %s", item.iconName.c_str());
                    }

                    if (!item.notes.empty())
                    {
                        ImGui::TextWrapped("%s", item.notes.c_str());
                    }

                    ImGui::EndTooltip();
                }
            }
        }

        if (matches.empty())
        {
            ImGui::TextDisabled("No matching items.");
        }

        ImGui::EndListBox();
    }

    ImGui::PushItemWidth(92.0f);
    ImGui::InputInt("Qty", &m_itemQuantity);
    ImGui::PopItemWidth();

    if (m_itemQuantity < 1)
    {
        m_itemQuantity = 1;
    }

    if (ImGui::Button("Give Selected", ImVec2(-1.0f, 0.0f)))
    {
        giveSelectedItem();
    }
}

void DebugConsole::giveSelectedItem()
{
    if (m_selectedItemId == 0)
    {
        addMessage(MessageKind::Error, "No item selected.");
        return;
    }

    char line[128] = {};
    std::snprintf(line, sizeof(line), "item give %u %d", m_selectedItemId, m_itemQuantity);
    executeLine(line);
}

void DebugConsole::renderHelpText() const
{
    ImGui::TextDisabled("Common commands");
    ImGui::BulletText("help");
    ImGui::BulletText("map");
    ImGui::BulletText("time [advance [days]]");
    ImGui::BulletText("event <id>");
    ImGui::BulletText("qbit get|set|clear <id>");
    ImGui::BulletText("qbit dump [active|all|filter]");
    ImGui::BulletText("npc greeting get|reset|set <npc-id> [greeting-id]");
    ImGui::BulletText("award dump [active|all|filter]");
    ImGui::BulletText("item search <text>");
    ImGui::BulletText("item give <id|text> [qty]");
    ImGui::BulletText("gold get|add|set <amount>");
    ImGui::BulletText("food get|add|set <amount>");
    ImGui::BulletText("tp <x> <y> <z>");
}
}
