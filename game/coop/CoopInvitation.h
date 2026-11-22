#pragma once

#include <optional>
#include <string>
#include <string_view>

namespace OpenYAMM::Game::Coop
{
// What a host's invitation names: a lobby's code (with the lobby's address when it is not the one every game
// asks), or the host's own address.
struct Invitation
{
    std::string code;
    std::string lobby;
    std::string address;
    // The session's password, when it has one: who has the invitation is invited.
    std::string password;
};

// The part of an invitation a game reads, which ends the message a host sends: [oyamm:CODE], [oyamm:CODE@lobby]
// or [oyamm:address], each with #password after it when the session has one.
std::string invitationMark(const Invitation &invitation);
// What a pasted text invites to: its mark, wherever it stands in the text, or else the text itself when it is a
// bare code or address. Nothing when it holds neither. A code comes back in capitals.
std::optional<Invitation> readInvitation(std::string_view text);
}
