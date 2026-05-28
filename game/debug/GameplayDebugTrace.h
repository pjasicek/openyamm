#pragma once

#include "game/gameplay/GameplayWorldInteraction.h"

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;

bool gameplayDebugTraceEnabled();
bool gameplayDebugTraceSuppressed();
void gameplayDebugTraceWrite(const std::string &message);
void configureGameplayDebugTrace(bool enabled, const std::string &filePath, bool append);
void configureGameplayCombatTrace(bool enabled, const std::string &filePath, bool append);
bool gameplayCombatTraceEnabled();
void gameplayCombatTraceWrite(const std::string &message);
std::string gameplayDebugTraceWorldHitSummary(const GameplayWorldHit &hit);
bool gameplayDebugTraceItemLooksQuestRelevant(uint32_t itemId, const ItemTable *pItemTable);
std::string gameplayDebugTraceItemSummary(uint32_t itemId, const ItemTable *pItemTable);
std::string gameplayDebugTraceMm9KeyQbitSummary(uint32_t qbitId);
const char *gameplayDebugTraceMechanismStateName(uint16_t state);
const char *gameplayDebugTraceMechanismActionName(uint32_t action);

#define GAMEPLAY_DEBUG_TRACE(message) \
    do \
    { \
        if (::OpenYAMM::Game::gameplayDebugTraceEnabled() \
            && !::OpenYAMM::Game::gameplayDebugTraceSuppressed()) \
        { \
            ::OpenYAMM::Game::gameplayDebugTraceWrite(message); \
        } \
    } while (false)

#define GAMEPLAY_DEBUG_TRACE_BLOCK(...) \
    do \
    { \
        if (::OpenYAMM::Game::gameplayDebugTraceEnabled() \
            && !::OpenYAMM::Game::gameplayDebugTraceSuppressed()) \
        { \
            __VA_ARGS__ \
        } \
    } while (false)

#define GAMEPLAY_COMBAT_TRACE(message) \
    do \
    { \
        if (::OpenYAMM::Game::gameplayCombatTraceEnabled()) \
        { \
            ::OpenYAMM::Game::gameplayCombatTraceWrite(message); \
        } \
    } while (false)

#define GAMEPLAY_COMBAT_TRACE_BLOCK(...) \
    do \
    { \
        if (::OpenYAMM::Game::gameplayCombatTraceEnabled()) \
        { \
            __VA_ARGS__ \
        } \
    } while (false)

class ScopedGameplayDebugTraceSuppression
{
public:
    ScopedGameplayDebugTraceSuppression();
    ~ScopedGameplayDebugTraceSuppression();

    ScopedGameplayDebugTraceSuppression(const ScopedGameplayDebugTraceSuppression &) = delete;
    ScopedGameplayDebugTraceSuppression &operator=(const ScopedGameplayDebugTraceSuppression &) = delete;
};
}
