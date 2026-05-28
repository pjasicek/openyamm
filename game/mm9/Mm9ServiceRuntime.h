#pragma once

#include "game/mm9/Mm9DialogueRuntime.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
enum class Mm9ServiceSessionStatus
{
    None,
    OpenGeneratedContext,
    PendingExactRuntimeSemantics,
    UnknownOpcode,
};

struct Mm9ServiceSession
{
    bool active = false;
    Mm9ServiceSessionStatus status = Mm9ServiceSessionStatus::None;
    Mm9DialogueServiceRequest request;
    std::string statusText;
};

Mm9ServiceSession openMm9ServiceSession(const Mm9DialogueServiceRequest &request);
std::string mm9ServiceSessionStatusName(Mm9ServiceSessionStatus status);

class Mm9ServiceRuntime : public Mm9DialogueServiceHandler
{
public:
    void openService(const Mm9DialogueServiceRequest &request) override;

    const std::optional<Mm9ServiceSession> &activeSession() const;
    void clearActiveSession();

private:
    std::optional<Mm9ServiceSession> m_activeSession;
};
}
