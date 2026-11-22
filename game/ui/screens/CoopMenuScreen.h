#pragma once

#include "game/coop/CoopLobbyBrowser.h"
#include "game/ui/MenuDesignScreen.h"

#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The Multiplayer screen of the game menu (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "The screens as
// built"): hosting the game in progress, with or without a lobby; joining another game with one click on a game
// found (the local network's by themselves, a lobby's once its address is known), or by a code or an address, with
// the game's own character or a character file; and, while in a session, who plays, the code or address to give
// the others (copied with one click), leaving, and what a player can keep. What was typed is remembered. Its
// controls are laid out in code on the menu canvas; menu/coop.yml gives the frame.
class CoopMenuScreen : public MenuDesignScreen
{
  public:
    // The session as the screen shows it, asked every frame.
    struct State
    {
        bool hosting = false;
        bool joined = false;
        bool joining = false;
        // The session's name, port and lobby code as a host has them, and whether a lobby was asked.
        std::string hostName;
        int hostPort = 0;
        std::string hostCode;
        bool hostAsksLobby = false;
        // This machine's address on its network, for the others to type.
        std::string localAddress;
        // Every player's line: name, class and level.
        std::vector<std::string> players;
        // The members of this game's party, each as name and class, and which of them stands for its player in
        // the others' games (its body, its face in their players panel).
        std::vector<std::string> ownMembers;
        size_t avatarMember = 0;
        // The last thing the session had to say (a refusal, a lost host).
        std::string notice;
        // The character of the game in progress, and the rules it plays by as a session advertises them
        // (coopRulesText): only games of the same rules play together.
        std::string ownCharacter;
        std::string ownRules;
        // The session this game stepped out of for now (CoopSession::stepOut): its host's character, and whether
        // this game can join it again by itself.
        bool away = false;
        std::string awayHostName;
        bool awayCanReturn = false;
    };

    // What the player gave this screen before, kept between runs (settings.ini, [coop]).
    struct Remembered
    {
        std::string sessionName;
        // The player's own lobby server; empty for the one every game asks.
        std::string lobbyAddress;
        // No lobby at all: host for and look on the local network only.
        bool localNetworkOnly = false;
        std::string hostAddress;
        bool joinTab = false;
        std::string hostPassword;
    };

    struct Actions
    {
        std::function<State()> state;
        Remembered remembered;
        // The lobby server a game asks when none was typed; an invitation names a lobby only when it is another.
        std::string builtInLobby;
        std::function<void(const Remembered &remembered)> remember;
        // `password`: what a hosted game asks of who joins; empty for none.
        std::function<bool(const std::string &name, const std::string &lobby, const std::string &password,
            std::string &error)> host;
        // The password the next joining gives.
        std::function<void(const std::string &password)> joinPassword;
        // Which member of the party stands for this player (its place in the party).
        std::function<void(size_t member)> setAvatar;
        // `character`: a character file's name, or empty for the game's own character.
        std::function<bool(const std::string &address, const std::string &character, std::string &error)> joinAddress;
        std::function<bool(const std::string &lobby, const std::string &code, const std::string &character,
            std::string &error)> joinCode;
        std::function<void()> leave;
        // A guest leaves for its own game for now, its seat kept; and joins the session it stepped out of again.
        std::function<bool(std::string &error)> stepOut;
        std::function<bool(std::string &error)> stepBack;
        std::function<void()> forgetAway;
        std::function<bool(const std::string &name, std::string &error)> saveCharacter;
        std::function<bool(const std::string &name, std::string &error)> keepWorld;
        // Back to the game menu, and back to the game.
        std::function<void()> back;
        std::function<void()> resume;
    };

    CoopMenuScreen(const Engine::AssetFileSystem &assetFileSystem, Actions actions, GameAudioSystem *pAudio = nullptr);

    AppMode mode() const override;
    void handleSdlEvent(const SDL_Event &event) override;

  private:
    enum class Tab
    {
        Host,
        Join,
    };

    // A line the player types into; `pActive` is the one being typed into.
    struct Field
    {
        std::string text;
        size_t maximum = 48;
    };

    void drawScreen(float deltaSeconds) override;
    void drawSession(const State &state);
    void drawHost(const State &state);
    void drawJoin(const State &state);
    void drawField(const std::string &id, const Rect &rect, Field &field, const std::string &hint);
    void refreshGames();
    void refreshCharacters();
    void remember();
    // The message a host sends the others: a sentence saying what to do with it, and at its end what
    // pasteInvitation reads, [oyamm:CODE], [oyamm:CODE@lobby] or [oyamm:address].
    std::string invitation(const State &state) const;
    // Joins by the invitation on the clipboard (or a bare code or address there). True when joining began.
    bool pasteInvitation();
    // Joins a found game with the chosen character; the game goes on when that began.
    bool joinGame(const CoopLobbyBrowser::Entry &game);

    Actions m_actions;
    Tab m_tab = Tab::Host;
    Field m_sessionName;
    // The player's own lobby server, for hosting and for joining; empty for the one every game asks.
    Field m_lobby;
    // No lobby: the local network only.
    bool m_localOnly = false;
    // The lobby asked now: none with m_localOnly, else the player's own, else the built-in one.
    std::string lobbyInUse() const;
    Field m_joinAddress;
    Field m_joinCode;
    // The password a hosted game asks for, and the one given when joining.
    Field m_hostPassword;
    Field m_joinPassword;
    Field m_fileName;
    Field *m_pActiveField = nullptr;
    std::string m_message;
    CoopLobbyBrowser m_browser;
    bool m_browserAsked = false;
    // The games as listed, asked for again every few seconds; the list shown is kept while the answers come in.
    std::vector<CoopLobbyBrowser::Entry> m_games;
    float m_sinceRefreshSeconds = 0.0f;
    std::string m_askedLobby;
    float m_gamesScroll = 0.0f;
    // The character files by name, and the one chosen to join with (empty: the game's own character).
    std::vector<std::pair<std::string, std::string>> m_characters;
    bool m_charactersRead = false;
    std::string m_character;
    float m_charactersScroll = 0.0f;
};
} // namespace OpenYAMM::Game
