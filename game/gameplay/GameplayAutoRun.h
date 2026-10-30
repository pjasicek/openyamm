#pragma once

#include "game/gameplay/GameplayInputFrame.h"

namespace OpenYAMM::Game
{
class GameplayAutoRun
{
public:
    void reset()
    {
        m_active = false;
    }

    void update(GameplayInputFrame &input, bool allowed)
    {
        const bool movementHeld =
            input.action(KeyboardAction::Forward).held
            || input.action(KeyboardAction::Backward).held
            || input.action(KeyboardAction::Left).held
            || input.action(KeyboardAction::Right).held
            || input.action(KeyboardAction::Jump).held
            || input.action(KeyboardAction::FlyUp).held
            || input.action(KeyboardAction::FlyDown).held
            || input.action(KeyboardAction::Land).held;

        if (!allowed || movementHeld)
        {
            reset();
        }
        else if (input.action(KeyboardAction::AutoRun).pressed)
        {
            m_active = !m_active;
        }

        input.autoRunActive = m_active;
        if (m_active)
        {
            input.actions[keyboardActionIndex(KeyboardAction::Forward)].held = true;
        }
    }

private:
    bool m_active = false;
};
}
