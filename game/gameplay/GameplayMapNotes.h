#pragma once

#include "game/events/EventRuntime.h"
#include "engine/Utf8.h"
#include "game/StringUtils.h"

#include <limits>

namespace OpenYAMM::Game
{
constexpr size_t GameplayMapNoteMaximumLength = 60;
// Automatic teacher notes use low, content-derived ids. Keep player notes in their own range.
constexpr uint32_t GameplayUserMapNoteFirstId = 0x80000000u;

inline void appendGameplayMapNoteText(std::string &buffer, const std::string &text)
{
    size_t length = Engine::utf8Length(buffer);
    for (const Engine::Utf8CodePoint &point : Engine::decodeUtf8(text))
    {
        if (length >= GameplayMapNoteMaximumLength)
        {
            break;
        }
        if (point.value >= 32 && point.value != 127)
        {
            buffer.append(text, point.byteOffset, point.byteLength);
            ++length;
        }
    }
}

inline EventRuntimeState::RuntimeMapNote *findEditableGameplayMapNote(
    EventRuntimeState &state, uint32_t id, const std::string &mapFileName)
{
    const auto it = state.runtimeMapNotes.find(id);
    return it != state.runtimeMapNotes.end() && it->second.active && it->second.userCreated
        && toLowerCopy(it->second.mapFileName) == toLowerCopy(mapFileName) ? &it->second : nullptr;
}

inline uint32_t saveGameplayUserMapNote(EventRuntimeState &state, uint32_t id,
    const std::string &mapFileName, int32_t x, int32_t y, const std::string &text)
{
    std::string filtered;
    appendGameplayMapNoteText(filtered, text);
    const size_t first = filtered.find_first_not_of(' ');
    filtered = first == std::string::npos ? std::string()
        : filtered.substr(first, filtered.find_last_not_of(' ') - first + 1);
    if (mapFileName.empty() || filtered.empty())
    {
        return 0;
    }
    if (id != 0)
    {
        EventRuntimeState::RuntimeMapNote *pNote = findEditableGameplayMapNote(state, id, mapFileName);
        if (pNote == nullptr)
        {
            return 0;
        }
        pNote->text = std::move(filtered);
        return id;
    }
    id = GameplayUserMapNoteFirstId;
    while (state.runtimeMapNotes.contains(id))
    {
        if (id == std::numeric_limits<uint32_t>::max())
        {
            return 0;
        }
        ++id;
    }
    EventRuntimeState::RuntimeMapNote note = {};
    note.id = id;
    note.x = x;
    note.y = y;
    note.mapFileName = toLowerCopy(mapFileName);
    note.text = std::move(filtered);
    note.active = true;
    note.userCreated = true;
    state.runtimeMapNotes.emplace(id, std::move(note));
    return id;
}

inline bool deleteGameplayUserMapNote(EventRuntimeState &state, uint32_t id, const std::string &mapFileName)
{
    return findEditableGameplayMapNote(state, id, mapFileName) != nullptr && state.runtimeMapNotes.erase(id) != 0;
}
}
