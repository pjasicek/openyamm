#pragma once

#include "engine/Localization.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace OpenYAMM::Game
{
// The six implant sockets (Character::implants, indexed by socket): Hesper's Implants skill opens them all (DECISIONS
// H-91: no masteries).
enum class ImplantSocket : uint8_t
{
    Cranial = 0,
    Cardiac,
    Spinal,
    Dermal,
    Optic,
    Neural,
};

constexpr size_t ImplantSocketCount = 6;

// The sockets' names in data (the implants table's socket column) and as the player reads them.
constexpr std::array<std::string_view, ImplantSocketCount> ImplantSocketDataNames = {
    "cranial", "cardiac", "spinal", "dermal", "optic", "neural"};
constexpr std::array<std::string_view, ImplantSocketCount> ImplantSocketDisplayNames = {
    Engine::trNoop("Cranial"), Engine::trNoop("Cardiac"), Engine::trNoop("Spinal"),
    Engine::trNoop("Dermal"), Engine::trNoop("Optic"), Engine::trNoop("Neural")};

inline std::optional<ImplantSocket> parseImplantSocket(std::string_view name)
{
    for (size_t index = 0; index < ImplantSocketCount; ++index)
    {
        if (ImplantSocketDataNames[index] == name)
        {
            return ImplantSocket(index);
        }
    }

    return std::nullopt;
}
}
