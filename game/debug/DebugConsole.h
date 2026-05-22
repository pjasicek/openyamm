#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

struct ImGuiInputTextCallbackData;

namespace OpenYAMM::Game
{
class MapStats;
class DebugConsole
{
public:
    enum class MessageKind
    {
        Info,
        Success,
        Warning,
        Error,
        Command,
    };

    struct Message
    {
        MessageKind kind = MessageKind::Info;
        std::string text;
    };

    struct CommandContext
    {
        std::vector<std::string> args;
    };

    struct CommandResult
    {
        bool success = false;
        std::string message;
    };

    using CommandCallback = std::function<CommandResult(const CommandContext &)>;

    struct CommandDefinition
    {
        std::string name;
        std::string description;
        std::string usage;
        CommandCallback callback;
    };

    struct ItemOption
    {
        uint32_t itemId = 0;
        std::string name;
        std::string unidentifiedName;
        std::string iconName;
        std::string skillGroup;
        std::string notes;
    };

    enum class MapOptionKind
    {
        Outdoor,
        Dungeon,
    };

    struct MapOption
    {
        int mapId = 0;
        std::string worldId;
        std::string fileName;
        std::string displayName;
        MapOptionKind kind = MapOptionKind::Outdoor;
    };

    void registerCommand(CommandDefinition definition);
    void clearCommands();
    void setItemOptions(std::vector<ItemOption> itemOptions);
    void setMapOptions(std::vector<MapOption> mapOptions);
    void setMapOptionsFromMapStats(const MapStats &mapStats);
    void setDebugToggleStates(bool immortal, bool unlimitedMana, bool invisible);

    void setEnabled(bool enabled);
    void toggleEnabled();
    bool enabled() const;
    bool wantsGameplayInputBlocked() const;
    bool freezesGameplay() const;

    void addMessage(MessageKind kind, const std::string &message);
    void clearMessages();
    void executeLine(const std::string &line);
    void render(int width, int height);
    int handleInputTextCallback(ImGuiInputTextCallbackData *pData);

private:
    static std::string normalizeCommandName(std::string_view name);
    static std::vector<std::string> splitCommandLine(std::string_view line);
    static std::vector<std::string> tokenize(std::string_view line);
    static int itemOptionSearchScore(const ItemOption &item, const std::string &query);
    static int mapOptionSearchScore(const MapOption &map, const std::string &query);

    void renderConsoleWindow(int width, int height);
    void renderMobileConsoleWindow(int width, int height);
    void renderHelpPanelContents();
    void renderMobileHelpPanelContents();
    void renderMobileQuickActions();
    void renderMobileQuestBitControls();
    void renderMobileAwardControls();
    void renderQuickActions();
    void renderQuestBitControls();
    void renderAwardControls();
    void renderMapControls();
    void renderMapPicker(MapOptionKind kind, const char *label, char *pSearchBuffer, size_t searchBufferSize);
    void renderItemPicker();
    void giveSelectedItem();
    void renderHelpText() const;
    float activeMobileConsoleScale() const;
    void applyActiveMobileConsoleScale() const;

    std::unordered_map<std::string, CommandDefinition> m_commands;
    std::vector<Message> m_messages;
    std::vector<std::string> m_history;
    std::vector<ItemOption> m_itemOptions;
    std::vector<MapOption> m_mapOptions;
    char m_inputBuffer[512] = {};
    char m_itemSearchBuffer[128] = {};
    char m_outdoorMapSearchBuffer[128] = {};
    char m_dungeonMapSearchBuffer[128] = {};
    char m_qbitSetBuffer[32] = {};
    char m_qbitClearBuffer[32] = {};
    char m_awardSetBuffer[32] = {};
    char m_awardClearBuffer[32] = {};
    int m_itemQuantity = 1;
    uint32_t m_selectedItemId = 0;
    int m_selectedOutdoorMapId = 0;
    int m_selectedDungeonMapId = 0;
    float m_windowHeight = 0.0f;
    bool m_debugImmortal = false;
    bool m_debugUnlimitedMana = false;
    bool m_debugInvisible = false;
    bool m_enabled = false;
    bool m_freezeGameplay = true;
    bool m_showHelpPanel = true;
    bool m_scrollToBottom = false;
    bool m_focusCommandInput = true;
    bool m_renderingMobileConsole = false;
    float m_activeMobileConsoleScale = 1.0f;
    size_t m_historyCursor = 0;
};
}
