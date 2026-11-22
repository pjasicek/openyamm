#include "game/ui/screens/CoopMenuScreen.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/coop/CoopCharacter.h"
#include "game/coop/CharacterFile.h"
#include "game/coop/CoopInvitation.h"
#include "game/coop/CoopProtocol.h"

#include <SDL3/SDL_clipboard.h>

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t BodyColor = 0xffc6dfeau;
constexpr uint32_t DimColor = 0xffa9bbb7u;
constexpr uint32_t TitleColor = 0xffa4d1e8u;
constexpr uint32_t ErrorColor = 0xff8aa9e6u;
// The body of the panel, in canvas units.
constexpr float Left = 96.0f;
constexpr float Right = 757.0f;
constexpr float Top = 124.0f;
constexpr float RowHeight = 24.0f;
// The screen's small text: the game's plain reading face (the enemy labels' and the popups'), which stays sharp at
// this size where the calligraphic menu face does not.
constexpr const char *SmallFont = "alegreya_semibold";
// The games found are asked for again this often, and the answers of an asking have come by this long after it.
constexpr float RefreshSeconds = 4.0f;
constexpr float AnswerSeconds = 1.0f;
}

CoopMenuScreen::CoopMenuScreen(const Engine::AssetFileSystem &assetFileSystem, Actions actions,
                               GameAudioSystem *pAudio)
    : MenuDesignScreen(assetFileSystem, true, pAudio)
    , m_actions(std::move(actions))
{
    m_joinAddress.maximum = 64;
    m_lobby.maximum = 64;
    m_joinCode.maximum = 8;
    m_fileName.maximum = 32;
    m_hostPassword.maximum = Coop::MaxPasswordLength;
    m_joinPassword.maximum = Coop::MaxPasswordLength;
    m_hostPassword.text = m_actions.remembered.hostPassword;
    m_sessionName.text = m_actions.remembered.sessionName;
    m_lobby.text = m_actions.remembered.lobbyAddress;
    m_localOnly = m_actions.remembered.localNetworkOnly;
    m_joinAddress.text = m_actions.remembered.hostAddress;
    m_tab = m_actions.remembered.joinTab ? Tab::Join : Tab::Host;
}

AppMode CoopMenuScreen::mode() const
{
    return AppMode::PauseMenu;
}

void CoopMenuScreen::handleSdlEvent(const SDL_Event &event)
{
    if (m_pActiveField == nullptr || modalOpen())
    {
        return;
    }

    if (event.type == SDL_EVENT_TEXT_INPUT)
    {
        Engine::Utf8::appendPrintable(m_pActiveField->text, event.text.text != nullptr ? event.text.text : "",
            m_pActiveField->maximum);
    }

    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_BACKSPACE
        && !m_pActiveField->text.empty())
    {
        Engine::Utf8::popBack(m_pActiveField->text);
    }

    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_RETURN && !event.key.repeat)
    {
        m_pActiveField = nullptr;
        setTextEditing(false);
    }
}

void CoopMenuScreen::drawField(const std::string &id, const Rect &rect, Field &field, const std::string &hint)
{
    const bool active = m_pActiveField == &field;

    if (button(id, rect, "", "text_field"))
    {
        m_pActiveField = &field;
        setTextEditing(true);
    }

    // The words typed, with a caret while typing; what belongs there, dimmed, while the line is empty.
    const Rect text = {rect.x + 8.0f * designScale(), rect.y, rect.width - 16.0f * designScale(), rect.height};
    const bool empty = field.text.empty() && !active;
    textInRect({text.x, text.y + 2.0f * designScale(), text.width, text.height},
        empty ? hint : field.text + (active ? "_" : ""), SmallFont, 11.5f, empty ? DimColor : BodyColor);
}

std::string CoopMenuScreen::lobbyInUse() const
{
    return m_localOnly ? std::string() : m_lobby.text.empty() ? m_actions.builtInLobby : m_lobby.text;
}

void CoopMenuScreen::refreshGames()
{
    std::string error;
    m_browser.refresh(Coop::DefaultPort, lobbyInUse(), error);
    m_browserAsked = true;
    m_sinceRefreshSeconds = 0.0f;
    m_askedLobby = lobbyInUse();

    if (!error.empty())
    {
        m_message = error;
    }
}

void CoopMenuScreen::remember()
{
    if (m_actions.remember)
    {
        m_actions.remember(Remembered{
            .sessionName = m_sessionName.text,
            .lobbyAddress = m_lobby.text,
            .localNetworkOnly = m_localOnly,
            .hostAddress = m_joinAddress.text,
            .joinTab = m_tab == Tab::Join,
            .hostPassword = m_hostPassword.text,
        });
    }
}

std::string CoopMenuScreen::invitation(const State &state) const
{
    Coop::Invitation invitation;
    invitation.code = state.hostCode;
    // The lobby is named only when it is the player's own: every game knows the built-in one.
    invitation.lobby = m_lobby.text != m_actions.builtInLobby ? m_lobby.text : std::string();
    invitation.address = state.hostCode.empty() ? state.localAddress : std::string();
    invitation.password = m_hostPassword.text;
    return Engine::tr("Join my OpenYAMM game \"{name}\": copy this message, then in the game's menu choose "
                      "Multiplayer, Join, Paste Invitation.",
               {{"name", state.hostName}})
        + " " + Coop::invitationMark(invitation);
}

bool CoopMenuScreen::pasteInvitation()
{
    char *pClipboard = SDL_GetClipboardText();
    const std::string text = pClipboard != nullptr ? pClipboard : "";
    SDL_free(pClipboard);
    const std::optional<Coop::Invitation> invitation = Coop::readInvitation(text);

    if (!invitation)
    {
        m_message = Engine::tr("The clipboard holds no invitation. Copy the host's message first.");
        return false;
    }

    // The invitation's password is the one given.
    if (!invitation->password.empty())
    {
        m_joinPassword.text = invitation->password;
    }

    // An invitation that names its lobby is joined through that one, from now on.
    if (!invitation->lobby.empty())
    {
        m_lobby.text = invitation->lobby;
    }

    // A code is a lobby's: the invitation is followed there, whatever was ticked for looking on one's own.
    if (!invitation->code.empty() && m_localOnly)
    {
        m_localOnly = false;
        remember();
    }

    return joinGame(CoopLobbyBrowser::Entry{.address = invitation->address, .code = invitation->code});
}

bool CoopMenuScreen::joinGame(const CoopLobbyBrowser::Entry &game)
{
    if (game.locked && m_joinPassword.text.empty())
    {
        m_message = Engine::tr("That game asks for a password: type it on the left first.");
        return false;
    }

    if (m_actions.joinPassword)
    {
        m_actions.joinPassword(m_joinPassword.text);
    }

    std::string error;
    const bool joining = game.code.empty() ? m_actions.joinAddress(game.address, m_character, error)
                                           : m_actions.joinCode(lobbyInUse(), game.code, m_character, error);

    if (!joining)
    {
        m_message = error;
        return false;
    }

    remember();
    m_actions.resume();
    return true;
}

void CoopMenuScreen::refreshCharacters()
{
    m_characters.clear();
    m_charactersRead = true;

    for (const std::filesystem::path &path : listCharacterFiles())
    {
        std::string error;

        if (const std::optional<CharacterFile> file = readCharacterFile(path, error))
        {
            m_characters.emplace_back(path.stem().string(), file->describe());
        }
    }
}

void CoopMenuScreen::drawScreen(float deltaSeconds)
{
    m_sinceRefreshSeconds += deltaSeconds;
    loadDesign("menu/coop");
    beginDesign("CoopMenu");
    drawDesign();
    const State state = m_actions.state();

    if (!modalOpen() && keyPressed(SDL_SCANCODE_ESCAPE))
    {
        if (m_pActiveField != nullptr)
        {
            m_pActiveField = nullptr;
            setTextEditing(false);
        }
        else
        {
            m_actions.back();
            return;
        }
    }

    // A line being typed loses the keyboard to Tab.
    if (m_pActiveField != nullptr && keyPressed(SDL_SCANCODE_TAB))
    {
        m_pActiveField = nullptr;
        setTextEditing(false);
    }

    const bool inSession = state.hosting || state.joined || state.joining;

    if (inSession)
    {
        drawSession(state);
    }
    else
    {
        // Host or join: the two ways into a session.
        if (button("coop-tab-host", canvasRect(Left, 96.0f, 120.0f, 24.0f), Engine::tr("Host"), "tab", true,
                m_tab == Tab::Host))
        {
            m_tab = Tab::Host;
            remember();
        }

        if (button("coop-tab-join", canvasRect(Left + 126.0f, 96.0f, 120.0f, 24.0f), Engine::tr("Join"), "tab", true,
                m_tab == Tab::Join))
        {
            m_tab = Tab::Join;
            remember();
        }

        // The game this one stepped out of: one click back into the kept seat.
        if (state.away)
        {
            const std::string label = state.awayHostName.empty() ? Engine::tr("Return to the Game You Left")
                : Engine::tr("Return to {name}'s Game", {{"name", state.awayHostName}});

            if (button("coop-step-back", canvasRect(Right - 300.0f, 96.0f, 300.0f, 24.0f), label, "button_primary",
                    state.awayCanReturn))
            {
                std::string error;
                m_message = m_actions.stepBack(error) ? std::string() : error;
            }

            if (button("coop-forget-away", canvasRect(Right - 386.0f, 96.0f, 80.0f, 24.0f), Engine::tr("Forget"),
                    "button_quiet"))
            {
                m_actions.forgetAway();
            }
        }

        if (m_tab == Tab::Host)
        {
            drawHost(state);
        }
        else
        {
            drawJoin(state);
        }
    }

    // What went wrong or what the session last said, and the way back.
    const std::string &message = m_message.empty() ? state.notice : m_message;

    if (!message.empty())
    {
        // A line of its own above the buttons.
        textInRect(canvasRect(Left, 402.0f, Right - Left, 16.0f), message, SmallFont, 10.5f, ErrorColor);
    }

    if (button("coop-back", canvasRect(Left, 422.0f, 120.0f, 24.0f), Engine::tr("Back"), "button_quiet"))
    {
        m_actions.back();
        return;
    }

    drawConfirmation();
}

void CoopMenuScreen::drawSession(const State &state)
{
    float y = Top - 28.0f;
    const auto line = [this, &y](const std::string &text, uint32_t color = BodyColor)
    {
        textInRect(canvasRect(Left, y, Right - Left, 16.0f), text, SmallFont, 12.0f, color);
        y += 18.0f;
    };
    // What the others need to get in, large enough to read out.
    const auto shown = [this, &y](const std::string &label, const std::string &value)
    {
        textInRect(canvasRect(Left, y + 4.0f, 190.0f, 16.0f), label, SmallFont, 12.0f, BodyColor);
        textInRect(canvasRect(Left + 190.0f, y + 2.0f, 300.0f, 20.0f), value, SmallFont, 14.0f, TitleColor);
        y += 24.0f;
    };

    if (state.hosting)
    {
        line(Engine::tr("You are hosting \"{name}\"", {{"name", state.hostName}}), TitleColor);
        y += 6.0f;
        const bool waitsForCode = state.hostAsksLobby && state.hostCode.empty();

        if (waitsForCode)
        {
            line(Engine::tr("Waiting for the lobby server to answer ..."), DimColor);
        }
        else if (state.hostAsksLobby)
        {
            shown(Engine::tr("Code for the others to join:"), state.hostCode);
        }

        if (!state.localAddress.empty())
        {
            shown(Engine::tr("Address on your network:"), state.localAddress);
        }

        y += 4.0f;

        // One message with all of it, for a chat with the other players.
        if (button("coop-copy-invitation", canvasRect(Left, y, 190.0f, 24.0f), Engine::tr("Copy Invitation"),
                "button_small", !waitsForCode))
        {
            m_message = SDL_SetClipboardText(invitation(state).c_str())
                ? Engine::tr("The invitation is copied. Paste it into a message to the other players.")
                : Engine::tr("The clipboard could not be written");
        }

        textInRect(canvasRect(Left + 200.0f, y + 5.0f, Right - Left - 200.0f, 16.0f),
            Engine::tr("Players on your network also find this game by themselves, under Join."), SmallFont,
            11.0f, DimColor);
        y += 34.0f;
    }
    else
    {
        line(state.joined ? Engine::tr("You are in another player's world") : Engine::tr("Joining ..."), TitleColor);
    }

    y += 8.0f;
    // Only games of the same rules join: said here so that a host knows what its game asks for.
    if (!state.ownRules.empty())
    {
        line(Engine::tr("Rules: {rules}", {{"rules", state.ownRules}}));
    }

    const float playersY = y;
    line(Engine::tr("Players"), TitleColor);

    for (const std::string &player : state.players)
    {
        line(player);
    }

    // Who of the party the others see, beside the list: a click takes the next member.
    if (state.ownMembers.size() > 1 && m_actions.setAvatar)
    {
        const float pickLeft = Right - 300.0f;
        const size_t avatar = state.avatarMember < state.ownMembers.size() ? state.avatarMember : 0;
        textInRect(canvasRect(pickLeft, playersY, 300.0f, 16.0f), Engine::tr("The others see you as"), SmallFont,
            12.0f, TitleColor);

        if (button("coop-avatar", canvasRect(pickLeft, playersY + 20.0f, 300.0f, 24.0f), state.ownMembers[avatar],
                "button_small"))
        {
            m_actions.setAvatar((avatar + 1) % state.ownMembers.size());
        }

        textInRect(canvasRect(pickLeft, playersY + 48.0f, 300.0f, 14.0f),
            Engine::tr("Click for the next member of your party."), SmallFont, 10.5f, DimColor);
    }

    // What a player can keep, each under the name typed.
    const float actionsY = 350.0f;
    textInRect(canvasRect(Left, actionsY - 18.0f, Right - Left, 16.0f),
        state.joined ? Engine::tr("A copy of this world to play on by yourself (asked of the host):")
                     : Engine::tr("A copy of your character, to join other games with:"),
        SmallFont, 10.5f, DimColor);
    drawField("coop-file-name", canvasRect(Left, actionsY, 220.0f, RowHeight), m_fileName,
        Engine::tr("a name for it"));

    if (!state.joined && !state.joining
        && button("coop-save-character", canvasRect(Left + 228.0f, actionsY, 200.0f, RowHeight),
            Engine::tr("Save Character"), "button_small", !m_fileName.text.empty()))
    {
        std::string error;
        m_message = m_actions.saveCharacter(m_fileName.text, error)
            ? Engine::tr("The character was saved as {name}", {{"name", m_fileName.text}})
            : error;
    }

    if (state.joined
        && button("coop-keep-world", canvasRect(Left + 228.0f, actionsY, 200.0f, RowHeight),
            Engine::tr("Keep a Copy of This World"), "button_small", !m_fileName.text.empty()))
    {
        std::string error;
        m_message = m_actions.keepWorld(m_fileName.text, error)
            ? Engine::tr("Asked the host for a copy of its world") : error;
    }

    if (button("coop-resume", canvasRect(Left + 130.0f, 422.0f, 170.0f, 24.0f), Engine::tr("Return to Game"),
            "button_primary"))
    {
        m_actions.resume();
        return;
    }

    if (state.joined
        && button("coop-step-out", canvasRect(Left + 308.0f, 422.0f, 170.0f, 24.0f), Engine::tr("Step Out for Now"),
            "button_quiet"))
    {
        confirm(Engine::tr("Step out for now?"),
            Engine::tr("You go back to your own game with what your character gained. Your seat is kept: this "
                       "screen brings you back."),
            {Engine::tr("Cancel"), Engine::tr("Step Out")},
            [this](int choice)
            {
                if (choice == 1)
                {
                    std::string error;
                    m_message = m_actions.stepOut(error) ? std::string() : error;
                }
            });
    }

    if (button("coop-leave", canvasRect(Right - 180.0f, 422.0f, 180.0f, 24.0f),
            state.hosting ? Engine::tr("Stop Hosting") : Engine::tr("Leave"), "button_danger"))
    {
        confirm(state.hosting ? Engine::tr("Stop hosting?") : Engine::tr("Leave this world?"),
            state.hosting ? Engine::tr("Every other player goes back to their own game.")
                          : Engine::tr("You go back to your own game with what your character gained."),
            {Engine::tr("Cancel"), state.hosting ? Engine::tr("Stop Hosting") : Engine::tr("Leave")},
            [this](int choice)
            {
                if (choice == 1)
                {
                    m_actions.leave();
                    m_message.clear();
                }
            });
    }
}

void CoopMenuScreen::drawHost(const State &state)
{
    float y = Top + 6.0f;
    textInRect(canvasRect(Left, y, 300.0f, 16.0f), Engine::tr("Name of your game"), SmallFont, 10.5f, DimColor);
    y += 16.0f;
    drawField("coop-host-name", canvasRect(Left, y, 320.0f, RowHeight), m_sessionName,
        Engine::tr("{name}'s world", {{"name", state.ownCharacter}}));
    textInRect(canvasRect(Left + 340.0f, y - 16.0f, 220.0f, 16.0f), Engine::tr("Password (optional)"), SmallFont,
        10.5f, DimColor);
    drawField("coop-host-password", canvasRect(Left + 340.0f, y, 220.0f, RowHeight), m_hostPassword,
        Engine::tr("none: anyone may join"));
    // A password travels inside an invitation's brackets, so it holds none of their marks and no blanks.
    std::erase_if(m_hostPassword.text, [](char character)
    {
        return character == ']' || character == '[' || character == '#' || character == '@' || character == ' ';
    });
    y += 38.0f;
    textInRect(canvasRect(Left, y, 300.0f, 16.0f), Engine::tr("Your own lobby server (optional)"), SmallFont, 10.5f,
        DimColor);
    y += 16.0f;
    drawField("coop-host-lobby", canvasRect(Left, y, 320.0f, RowHeight), m_lobby,
        Engine::tr("the OpenYAMM lobby, {address}", {{"address", m_actions.builtInLobby}}));

    if (button("coop-host-local", canvasRect(Left + 340.0f, y, 220.0f, RowHeight), Engine::tr("Local Network Only"),
            "tab", true, m_localOnly))
    {
        m_localOnly = !m_localOnly;
        remember();
    }

    y += 34.0f;
    textInRect(canvasRect(Left, y, Right - Left, 48.0f),
        m_localOnly
            ? Engine::tr("Only players on your network will find this game, by themselves. No lobby server is "
                         "asked.")
            : Engine::tr("Your game will get a code from the lobby server; anyone with the code can join. Players "
                         "on your network find it by themselves."),
        SmallFont, 11.0f, DimColor);
    y += 52.0f;

    if (button("coop-host-go", canvasRect(Left, y, 220.0f, 27.0f), Engine::tr("Host This Game"), "button_primary"))
    {
        std::string error;
        m_message =
            m_actions.host(m_sessionName.text, lobbyInUse(), m_hostPassword.text, error) ? std::string() : error;
        m_pActiveField = nullptr;
        setTextEditing(false);
        remember();
    }

    // A copy of the character for other worlds can be made before any session.
    const float fileY = 368.0f;
    textInRect(canvasRect(Left, fileY - 18.0f, Right - Left, 16.0f),
        Engine::tr("A copy of your character, to join other games with:"), SmallFont, 10.5f, DimColor);
    drawField("coop-file-name", canvasRect(Left, fileY, 220.0f, RowHeight), m_fileName,
        Engine::tr("a name for it"));

    if (button("coop-save-character", canvasRect(Left + 228.0f, fileY, 200.0f, RowHeight),
            Engine::tr("Save Character"), "button_small", !m_fileName.text.empty()))
    {
        std::string error;
        m_charactersRead = false;
        m_message = m_actions.saveCharacter(m_fileName.text, error)
            ? Engine::tr("The character was saved as {name}", {{"name", m_fileName.text}})
            : error;
    }
}

void CoopMenuScreen::drawJoin(const State &state)
{
    if (!m_charactersRead)
    {
        refreshCharacters();
    }

    // The games are asked for by themselves: on opening, every few seconds, and when the lobby's address changed
    // and is no longer being typed.
    const bool lobbyTyped = m_pActiveField != &m_lobby && m_askedLobby != lobbyInUse();

    if (!m_browserAsked || m_sinceRefreshSeconds >= RefreshSeconds || lobbyTyped || m_browser.takeLobbyFound())
    {
        refreshGames();
    }

    m_browser.update();
    std::vector<CoopLobbyBrowser::Entry> found = m_browser.entries();

    // A game hosted on this network with a lobby answers both ways: listed once, by its address.
    std::erase_if(found, [&found](const CoopLobbyBrowser::Entry &game)
    {
        return !game.code.empty()
            && std::any_of(found.begin(), found.end(), [&game](const CoopLobbyBrowser::Entry &other)
            {
                return other.code.empty() && other.name == game.name;
            });
    });

    // The list shown stays while the answers of a new asking come in.
    if (found.size() >= m_games.size() || m_sinceRefreshSeconds >= AnswerSeconds)
    {
        m_games = std::move(found);
    }

    const float unit = designScale();
    const float columnWidth = 250.0f;
    const float gamesLeft = Left + columnWidth + 20.0f;

    // Right: the games found on the local network and in the lobby. A click on one joins it.
    textInRect(canvasRect(gamesLeft, Top + 2.0f, Right - gamesLeft - 160.0f, 16.0f),
        state.ownRules.empty() ? Engine::tr("Games found - click one to join it")
            : Engine::tr("Games found - click one to join it; you play by its rules (this game's: {rules})",
                  {{"rules", state.ownRules}}),
        SmallFont, 10.5f, DimColor);

    // The host's message, copied out of a chat: one click joins by it.
    if (button("coop-paste-invitation", canvasRect(Right - 150.0f, Top - 6.0f, 150.0f, 22.0f),
            Engine::tr("Paste Invitation"), "button_small")
        && pasteInvitation())
    {
        return;
    }

    const Rect list = canvasRect(gamesLeft, Top + 20.0f, Right - gamesLeft, 276.0f);
    const float gamePitch = 34.0f;
    scrollViewport(list, float(m_games.size()) * gamePitch * unit, m_gamesScroll, gamePitch * unit);
    setDesignClip(list);

    for (size_t index = 0; index < m_games.size(); ++index)
    {
        const CoopLobbyBrowser::Entry &game = m_games[index];
        const Rect row = {list.x, list.y + float(index) * gamePitch * unit - m_gamesScroll, list.width - 10.0f * unit,
            31.0f * unit};

        if (row.y + row.height < list.y || row.y > list.y + list.height)
        {
            continue;
        }

        const bool sameVersion = game.protocol == Coop::ProtocolVersion;
        const bool full = game.maxPlayers > 0 && game.players >= game.maxPlayers;
        // The rules must be the same (a ruleset's difficulty and solo run with them). A character file is of rules
        // of its own, which the host checks.
        const bool sameRules = !m_character.empty() || state.ownRules.empty()
            || !coopRulesRefusal(game.ruleset, state.ownRules);

        // A game of another version, of other rules or a full one cannot be joined; it is listed so that the player
        // sees why.
        if (button("coop-game-" + std::to_string(index), row, "", "save_row", sameVersion && sameRules && !full,
                false))
        {
            setDesignClip(std::nullopt);

            if (joinGame(game))
            {
                return;
            }

            setDesignClip(list);
        }

        textInRect({row.x + 8.0f * unit, row.y + 3.0f * unit, row.width - 16.0f * unit, 14.0f * unit}, game.name,
            SmallFont, 11.5f, BodyColor);
        const std::string where = game.code.empty() ? Engine::tr("on your network")
                                                    : Engine::tr("lobby, code {code}", {{"code", game.code}});
        const std::string detail = !sameVersion ? Engine::tr("another version of OpenYAMM")
            : !sameRules ? Engine::tr("rules this game cannot join: {ruleset} (this game: {own})",
                               {{"ruleset", game.ruleset}, {"own", state.ownRules}})
            : Engine::tr("{world}, {ruleset}, {players} of {most} players",
                  {{"world", game.world}, {"ruleset", game.ruleset}, {"players", game.players},
                      {"most", game.maxPlayers}});
        textInRect({row.x + 8.0f * unit, row.y + 17.0f * unit, row.width - 16.0f * unit, 12.0f * unit},
            where + "  -  " + detail + (full ? "  -  " + Engine::tr("full") : std::string())
                + (game.locked ? "  -  " + Engine::tr("asks for a password") : std::string()),
            SmallFont, 9.5f, DimColor);
    }

    setDesignClip(std::nullopt);

    if (m_games.empty())
    {
        textInRect(canvasRect(gamesLeft + 8.0f, Top + 28.0f, Right - gamesLeft - 16.0f, 40.0f),
            m_localOnly
                ? Engine::tr("No games found yet. A game on your network shows here by itself.")
                : Engine::tr("No games found yet. Games on your network and on the lobby server show here by "
                             "themselves."),
            SmallFont, 11.0f, DimColor);
    }

    // Left: who joins, and the ways to name a game that is not in the list.
    float y = Top + 2.0f;
    textInRect(canvasRect(Left, y, columnWidth, 16.0f), Engine::tr("Join as"), SmallFont, 10.5f, DimColor);
    y += 16.0f;
    const Rect characters = canvasRect(Left, y, columnWidth, 62.0f);
    const float characterPitch = 22.0f;
    scrollViewport(characters, float(m_characters.size() + 1) * characterPitch * unit, m_charactersScroll,
        characterPitch * unit);
    setDesignClip(characters);

    for (size_t index = 0; index <= m_characters.size(); ++index)
    {
        const bool own = index == 0;
        const std::string &name = own ? std::string() : m_characters[index - 1].first;
        const Rect row = {characters.x, characters.y + float(index) * characterPitch * unit - m_charactersScroll,
            characters.width - 10.0f * unit, 20.0f * unit};

        if (row.y + row.height < characters.y || row.y > characters.y + characters.height)
        {
            continue;
        }

        if (button("coop-character-" + std::to_string(index), row, "", "save_row", true, m_character == name))
        {
            m_character = name;
        }

        textInRect({row.x + 8.0f * unit, row.y + 4.0f * unit, row.width - 16.0f * unit, row.height},
            own ? Engine::tr("This game's character: {name}", {{"name", state.ownCharacter}})
                : m_characters[index - 1].second,
            SmallFont, 10.5f, BodyColor);
    }

    setDesignClip(std::nullopt);
    y += 68.0f;
    textInRect(canvasRect(Left, y, columnWidth, 16.0f), Engine::tr("Password, if the game has one"), SmallFont,
        10.5f, DimColor);
    y += 16.0f;
    drawField("coop-join-password", canvasRect(Left, y, columnWidth, RowHeight), m_joinPassword,
        Engine::tr("the password"));
    y += 30.0f;
    textInRect(canvasRect(Left, y, columnWidth, 16.0f), Engine::tr("Your own lobby server (optional)"), SmallFont,
        10.5f, DimColor);
    y += 16.0f;
    drawField("coop-join-lobby", canvasRect(Left, y, columnWidth - 96.0f, RowHeight), m_lobby,
        Engine::tr("the OpenYAMM lobby"));

    if (button("coop-join-local", canvasRect(Left + columnWidth - 90.0f, y, 90.0f, RowHeight),
            Engine::tr("Local Only"), "tab", true, m_localOnly))
    {
        m_localOnly = !m_localOnly;
        remember();
    }

    y += 30.0f;
    textInRect(canvasRect(Left, y, columnWidth, 16.0f), Engine::tr("Join by a code"), SmallFont, 10.5f, DimColor);
    y += 16.0f;
    drawField("coop-join-code", canvasRect(Left, y, columnWidth - 76.0f, RowHeight), m_joinCode,
        Engine::tr("the code"));

    if (button("coop-join-code-go", canvasRect(Left + columnWidth - 70.0f, y, 70.0f, RowHeight), Engine::tr("Join"),
            "button_small", !m_joinCode.text.empty() && !m_localOnly))
    {
        if (joinGame(CoopLobbyBrowser::Entry{.code = m_joinCode.text}))
        {
            return;
        }
    }

    y += 30.0f;
    textInRect(canvasRect(Left, y, columnWidth, 16.0f), Engine::tr("Join by the host's address"), SmallFont,
        10.5f, DimColor);
    y += 16.0f;
    drawField("coop-join-address", canvasRect(Left, y, columnWidth - 76.0f, RowHeight), m_joinAddress,
        Engine::tr("the address"));

    if (button("coop-join-address-go", canvasRect(Left + columnWidth - 70.0f, y, 70.0f, RowHeight), Engine::tr("Join"),
            "button_small", !m_joinAddress.text.empty()))
    {
        if (joinGame(CoopLobbyBrowser::Entry{.address = m_joinAddress.text}))
        {
            return;
        }
    }
}
} // namespace OpenYAMM::Game
