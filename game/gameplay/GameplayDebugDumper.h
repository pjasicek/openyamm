#pragma once

namespace OpenYAMM::Game
{
class GameSession;

class GameplayDebugDumper
{
public:
    static void dumpStateToConsole(const GameSession &session);
};
} // namespace OpenYAMM::Game
