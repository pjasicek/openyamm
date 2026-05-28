#include "game/mm9/Mm9ServiceRuntime.h"

#include <utility>

namespace OpenYAMM::Game
{
namespace
{
bool mm9ServiceKindHasGeneratedContext(Mm9ServiceKind kind)
{
    switch (kind)
    {
    case Mm9ServiceKind::Shop:
    case Mm9ServiceKind::Training:
    case Mm9ServiceKind::SkillTraining:
    case Mm9ServiceKind::Travel:
    case Mm9ServiceKind::Bank:
    case Mm9ServiceKind::Inn:
    case Mm9ServiceKind::Healer:
    case Mm9ServiceKind::Hire:
    case Mm9ServiceKind::Dismiss:
    case Mm9ServiceKind::ItemCombine:
    case Mm9ServiceKind::TownPortal:
    case Mm9ServiceKind::Donation:
        return true;
    case Mm9ServiceKind::QuestHandoff:
    case Mm9ServiceKind::Unknown:
        return false;
    }

    return false;
}
}

Mm9ServiceSession openMm9ServiceSession(const Mm9DialogueServiceRequest &request)
{
    Mm9ServiceSession session = {};
    session.active = true;
    session.request = request;

    if (request.kind == Mm9ServiceKind::Unknown)
    {
        session.status = Mm9ServiceSessionStatus::UnknownOpcode;
        session.statusText = "unknown MM9 service opcode";
        return session;
    }

    if (!mm9ServiceKindHasGeneratedContext(request.kind))
    {
        session.status = Mm9ServiceSessionStatus::PendingExactRuntimeSemantics;
        session.statusText = "MM9 service preserved pending exact runtime semantics";
        return session;
    }

    session.status = Mm9ServiceSessionStatus::OpenGeneratedContext;
    session.statusText = "MM9 service context opened: " + mm9ServiceKindName(request.kind);
    return session;
}

std::string mm9ServiceSessionStatusName(Mm9ServiceSessionStatus status)
{
    switch (status)
    {
    case Mm9ServiceSessionStatus::None:
        return "none";
    case Mm9ServiceSessionStatus::OpenGeneratedContext:
        return "open_generated_context";
    case Mm9ServiceSessionStatus::PendingExactRuntimeSemantics:
        return "pending_exact_runtime_semantics";
    case Mm9ServiceSessionStatus::UnknownOpcode:
        return "unknown_opcode";
    }

    return "unknown_opcode";
}

void Mm9ServiceRuntime::openService(const Mm9DialogueServiceRequest &request)
{
    m_activeSession = openMm9ServiceSession(request);
}

const std::optional<Mm9ServiceSession> &Mm9ServiceRuntime::activeSession() const
{
    return m_activeSession;
}

void Mm9ServiceRuntime::clearActiveSession()
{
    m_activeSession.reset();
}
}
