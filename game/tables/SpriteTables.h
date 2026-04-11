#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class SpriteFrameFlag : uint32_t
{
    HasMore = 0x1,
    Lit = 0x2,
    First = 0x4,
    Image1 = 0x10,
    Center = 0x20,
    Fidget = 0x40,
    Loaded = 0x80,
    Mirror0 = 0x100,
    Mirror1 = 0x200,
    Mirror2 = 0x400,
    Mirror3 = 0x800,
    Mirror4 = 0x1000,
    Mirror5 = 0x2000,
    Mirror6 = 0x4000,
    Mirror7 = 0x8000,
    Images3 = 0x10000,
    Glowing = 0x20000,
    Transparent = 0x40000
};

struct DecorationEntry
{
    std::string internalName;
    std::string hint;
    int16_t type = 0;
    uint16_t height = 0;
    int16_t radius = 0;
    int16_t lightRadius = 0;
    uint8_t lightRed = 255;
    uint8_t lightGreen = 255;
    uint8_t lightBlue = 255;
    uint16_t spriteId = 0;
    uint16_t flags = 0;
    int16_t soundId = 0;
};

class DecorationTable
{
public:
    bool loadRows(const std::vector<std::vector<std::string>> &rows);
    const DecorationEntry *get(uint16_t decorationId) const;
    const DecorationEntry *findByInternalName(const std::string &internalName) const;

private:
    std::vector<DecorationEntry> m_entries;
};

struct SpriteFrameEntry
{
    std::string spriteName;
    std::string textureName;
    float scale = 1.0f;
    uint32_t flags = 0;
    int16_t glowRadius = 0;
    int16_t paletteId = 0;
    int32_t frameLengthTicks = 0;
    int32_t animationLengthTicks = 0;
};

struct ResolvedSpriteTexture
{
    std::string textureName;
    bool mirrored = false;
};

class SpriteFrameTable
{
public:
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage, bool append = false);
    const SpriteFrameEntry *getFrame(uint16_t spriteId, uint32_t timeTicks) const;
    std::vector<std::string> collectTextureNames(uint16_t spriteId) const;
    std::optional<uint16_t> findFrameIndexBySpriteName(const std::string &spriteName) const;
    static ResolvedSpriteTexture resolveTexture(const SpriteFrameEntry &frame, int octant);
    static bool hasFlag(uint32_t flags, SpriteFrameFlag flag);

private:
    static uint32_t mirrorFlagForOctant(int octant);
    static std::string buildTextureName(const std::string &baseName, int suffixIndex);
    void rebuildSpriteNameIndex();

private:
    std::vector<SpriteFrameEntry> m_frames;
    std::vector<bool> m_framePresent;
    std::vector<uint16_t> m_eFrames;
};
}
