#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
enum class FaceAttribute : uint32_t
{
    IsPortal = 0x00000001,
    IsSecret = 0x00000002,
    FlowDown = 0x00000004,
    TextureAlignDown = 0x00000008,
    Fluid = 0x00000010,
    FlowUp = 0x00000020,
    FlowLeft = 0x00000040,
    SeenByParty = 0x00000080,
    XYPlane = 0x00000100,
    XZPlane = 0x00000200,
    YZPlane = 0x00000400,
    FlowRight = 0x00000800,
    TextureAlignLeft = 0x00001000,
    Invisible = 0x00002000,
    Animated = 0x00004000,
    TextureAlignRight = 0x00008000,
    Outlined = 0x00010000,
    TextureAlignBottom = 0x00020000,
    TextureMoveByDoor = 0x00040000,
    TriggerByTouch = 0x00080000,
    HasHint = 0x00100000,
    IndoorCarpet = 0x00200000,
    IndoorSky = 0x00400000,
    FlipNormalU = 0x00800000,
    FlipNormalV = 0x01000000,
    Clickable = 0x02000000,
    PressurePlate = 0x04000000,
    Indicate = 0x06000000,
    TriggerByMonster = 0x08000000,
    TriggerByObject = 0x10000000,
    Untouchable = 0x20000000,
    Lava = 0x40000000,
    Picked = 0x80000000,
};

constexpr uint32_t faceAttributeBit(FaceAttribute attribute)
{
    return static_cast<uint32_t>(attribute);
}

constexpr bool hasFaceAttribute(uint32_t attributes, FaceAttribute attribute)
{
    return (attributes & faceAttributeBit(attribute)) != 0;
}
} // namespace OpenYAMM::Game
