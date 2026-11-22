#include "game/coop/CoopInvitation.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game::Coop
{
namespace
{
constexpr std::string_view MarkBegin = "[oyamm:";
constexpr size_t MaxLength = 80;
}

std::string invitationMark(const Invitation &invitation)
{
    std::string where = invitation.address;

    if (!invitation.code.empty())
    {
        where = invitation.code + (invitation.lobby.empty() ? std::string() : "@" + invitation.lobby);
    }

    return std::string(MarkBegin) + where + (invitation.password.empty() ? std::string() : "#" + invitation.password)
        + "]";
}

std::optional<Invitation> readInvitation(std::string_view text)
{
    std::string where;
    const size_t mark = text.find(MarkBegin);

    if (mark != std::string_view::npos)
    {
        const size_t end = text.find(']', mark);

        if (end == std::string_view::npos)
        {
            return std::nullopt;
        }

        where = std::string(text.substr(mark + MarkBegin.size(), end - mark - MarkBegin.size()));
    }
    else
    {
        // No mark: a code or an address copied by itself, with whatever blanks came along.
        const auto blank = [](char character) { return std::isspace(static_cast<unsigned char>(character)) != 0; };
        const auto first = std::find_if_not(text.begin(), text.end(), blank);
        const auto last = std::find_if_not(text.rbegin(), text.rend(), blank).base();
        where = first < last ? std::string(first, last) : std::string();

        if (std::any_of(where.begin(), where.end(), blank))
        {
            return std::nullopt;
        }
    }

    if (where.empty() || where.size() > MaxLength)
    {
        return std::nullopt;
    }

    Invitation invitation;

    // The password is what follows the last #; a code and an address hold none.
    if (const size_t hash = where.rfind('#'); hash != std::string::npos)
    {
        invitation.password = where.substr(hash + 1);
        where.resize(hash);
    }

    const size_t at = where.find('@');

    if (at != std::string::npos)
    {
        invitation.code = where.substr(0, at);
        invitation.lobby = where.substr(at + 1);
    }
    else if (where.find('.') != std::string::npos || where.find(':') != std::string::npos)
    {
        invitation.address = where;
    }
    else
    {
        invitation.code = where;
    }

    std::transform(invitation.code.begin(), invitation.code.end(), invitation.code.begin(),
        [](unsigned char character) { return char(std::toupper(character)); });
    const bool nothingNamed = invitation.code.empty() && invitation.address.empty();
    const bool lobbyMissing = at != std::string::npos && invitation.lobby.empty();
    return nothingNamed || lobbyMissing ? std::nullopt : std::optional<Invitation>(invitation);
}
}
