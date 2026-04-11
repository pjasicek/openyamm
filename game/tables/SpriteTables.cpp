#include "game/tables/SpriteTables.h"
#include "game/BinaryReader.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <exception>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t SpriteFrameRecordSize = 60;

bool isNumericString(const std::string &value)
{
    if (value.empty())
    {
        return false;
    }

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}

std::string trimCopy(const std::string &value);

std::optional<SpriteFrameFlag> parseSpriteFrameFlagName(const std::string &value)
{
    const std::string normalizedValue = toLowerCopy(value);

    if (normalizedValue == "hasmore")
    {
        return SpriteFrameFlag::HasMore;
    }

    if (normalizedValue == "lit")
    {
        return SpriteFrameFlag::Lit;
    }

    if (normalizedValue == "first")
    {
        return SpriteFrameFlag::First;
    }

    if (normalizedValue == "image1")
    {
        return SpriteFrameFlag::Image1;
    }

    if (normalizedValue == "center")
    {
        return SpriteFrameFlag::Center;
    }

    if (normalizedValue == "fidget")
    {
        return SpriteFrameFlag::Fidget;
    }

    if (normalizedValue == "loaded")
    {
        return SpriteFrameFlag::Loaded;
    }

    if (normalizedValue == "mirror0")
    {
        return SpriteFrameFlag::Mirror0;
    }

    if (normalizedValue == "mirror1")
    {
        return SpriteFrameFlag::Mirror1;
    }

    if (normalizedValue == "mirror2")
    {
        return SpriteFrameFlag::Mirror2;
    }

    if (normalizedValue == "mirror3")
    {
        return SpriteFrameFlag::Mirror3;
    }

    if (normalizedValue == "mirror4")
    {
        return SpriteFrameFlag::Mirror4;
    }

    if (normalizedValue == "mirror5")
    {
        return SpriteFrameFlag::Mirror5;
    }

    if (normalizedValue == "mirror6")
    {
        return SpriteFrameFlag::Mirror6;
    }

    if (normalizedValue == "mirror7")
    {
        return SpriteFrameFlag::Mirror7;
    }

    if (normalizedValue == "images3")
    {
        return SpriteFrameFlag::Images3;
    }

    if (normalizedValue == "glowing")
    {
        return SpriteFrameFlag::Glowing;
    }

    if (normalizedValue == "transparent")
    {
        return SpriteFrameFlag::Transparent;
    }

    return std::nullopt;
}

bool parseSpriteFrameFlagsNode(const YAML::Node &node, uint32_t &flags)
{
    flags = 0;

    if (!node)
    {
        return true;
    }

    if (node.IsScalar())
    {
        const std::string value = trimCopy(node.as<std::string>());

        if (value.empty())
        {
            return true;
        }

        if (isNumericString(value) || value.starts_with("0x") || value.starts_with("0X"))
        {
            flags = static_cast<uint32_t>(std::stoul(value, nullptr, 0));
            return true;
        }

        const std::optional<SpriteFrameFlag> flag = parseSpriteFrameFlagName(value);

        if (!flag)
        {
            return false;
        }

        flags = static_cast<uint32_t>(*flag);
        return true;
    }

    if (!node.IsSequence())
    {
        return false;
    }

    for (const YAML::Node &entryNode : node)
    {
        if (!entryNode.IsScalar())
        {
            return false;
        }

        const std::optional<SpriteFrameFlag> flag = parseSpriteFrameFlagName(entryNode.as<std::string>());

        if (!flag)
        {
            return false;
        }

        flags |= static_cast<uint32_t>(*flag);
    }

    return true;
}

std::vector<uint16_t> buildSortedFirstFrameIndices(
    const std::vector<SpriteFrameEntry> &frames,
    const std::vector<bool> &framePresent)
{
    std::vector<uint16_t> firstFrameIndices;

    for (size_t frameIndex = 0; frameIndex < frames.size(); ++frameIndex)
    {
        if (frameIndex < framePresent.size() && framePresent[frameIndex] && !frames[frameIndex].spriteName.empty())
        {
            firstFrameIndices.push_back(static_cast<uint16_t>(frameIndex));
        }
    }

    std::sort(firstFrameIndices.begin(), firstFrameIndices.end(),
        [&frames](uint16_t leftIndex, uint16_t rightIndex)
        {
            return toLowerCopy(frames[leftIndex].spriteName) < toLowerCopy(frames[rightIndex].spriteName);
        });

    return firstFrameIndices;
}

int mirroredSourceOctant(int octant)
{
    static constexpr std::array<int, 8> MirroredOctants = {0, 7, 6, 5, 4, 3, 2, 1};
    return MirroredOctants[static_cast<size_t>(octant)];
}

void appendUnique(std::vector<std::string> &names, const std::string &name)
{
    if (name.empty())
    {
        return;
    }

    if (std::find(names.begin(), names.end(), name) == names.end())
    {
        names.push_back(name);
    }
}

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

bool parseInt16Cell(const std::vector<std::string> &row, size_t index, int16_t &value)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    if (parsed < std::numeric_limits<int16_t>::min() || parsed > std::numeric_limits<int16_t>::max())
    {
        return false;
    }

    value = static_cast<int16_t>(parsed);
    return true;
}

bool parseUInt16Cell(const std::vector<std::string> &row, size_t index, uint16_t &value)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty() || trimmed.front() == '-')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0' || parsed > std::numeric_limits<uint16_t>::max())
    {
        return false;
    }

    value = static_cast<uint16_t>(parsed);
    return true;
}

bool parseUInt8Cell(const std::vector<std::string> &row, size_t index, uint8_t &value)
{
    uint16_t parsed = 0;

    if (!parseUInt16Cell(row, index, parsed) || parsed > std::numeric_limits<uint8_t>::max())
    {
        return false;
    }

    value = static_cast<uint8_t>(parsed);
    return true;
}

bool parseDecorationFlagsCell(const std::vector<std::string> &row, size_t index, uint16_t &flags)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty() || trimmed == "0")
    {
        flags = 0;
        return true;
    }

    if (isNumericString(trimmed) || trimmed.starts_with("0x") || trimmed.starts_with("0X"))
    {
        return parseUInt16Cell(row, index, flags);
    }

    flags = 0;
    size_t tokenBegin = 0;

    while (tokenBegin < trimmed.size())
    {
        size_t tokenEnd = trimmed.find(',', tokenBegin);

        if (tokenEnd == std::string::npos)
        {
            tokenEnd = trimmed.size();
        }

        const std::string token = toLowerCopy(trimCopy(trimmed.substr(tokenBegin, tokenEnd - tokenBegin)));

        if (!token.empty())
        {
            if (token == "movethrough")
            {
                flags |= 0x0001;
            }
            else if (token == "dontdraw" || token == "invisible")
            {
                flags |= 0x0002;
            }
            else if (token == "flickerslow")
            {
                flags |= 0x0004;
            }
            else if (token == "flickeraverage")
            {
                flags |= 0x0008;
            }
            else if (token == "flickerfast")
            {
                flags |= 0x0010;
            }
            else if (token == "marker")
            {
                flags |= 0x0020;
            }
            else if (token == "slowloop")
            {
                flags |= 0x0040;
            }
            else if (token == "emitfire")
            {
                flags |= 0x0080;
            }
            else if (token == "soundondawn")
            {
                flags |= 0x0100;
            }
            else if (token == "soundondusk")
            {
                flags |= 0x0200;
            }
            else if (token == "emitsmoke" || token == "emitsmoke")
            {
                flags |= 0x0400;
            }
            else
            {
                return false;
            }
        }

        tokenBegin = tokenEnd + 1;
    }

    return true;
}

}

bool DecorationTable::loadRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || !isNumericString(trimCopy(row[0])))
        {
            continue;
        }

        const int decorationNumber = std::stoi(trimCopy(row[0]));
        const int decorationId = decorationNumber - 1;

        if (decorationId < 0 || static_cast<size_t>(decorationId) != m_entries.size())
        {
            return false;
        }

        DecorationEntry entry = {};
        entry.internalName = row.size() > 1 ? toLowerCopy(trimCopy(row[1])) : std::string();
        entry.hint = row.size() > 2 ? trimCopy(row[2]) : std::string();

        if (!parseInt16Cell(row, 3, entry.type)
            || !parseInt16Cell(row, 4, entry.radius)
            || !parseUInt16Cell(row, 5, entry.height)
            || !parseInt16Cell(row, 6, entry.lightRadius)
            || !parseUInt8Cell(row, 7, entry.lightRed)
            || !parseUInt8Cell(row, 8, entry.lightGreen)
            || !parseUInt8Cell(row, 9, entry.lightBlue)
            || !parseInt16Cell(row, 10, entry.soundId)
            || !parseDecorationFlagsCell(row, 11, entry.flags)
            || !parseUInt16Cell(row, 12, entry.spriteId))
        {
            return false;
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const DecorationEntry *DecorationTable::get(uint16_t decorationId) const
{
    if (decorationId >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[decorationId];
}

const DecorationEntry *DecorationTable::findByInternalName(const std::string &internalName) const
{
    std::string normalizedName;
    normalizedName.reserve(internalName.size());

    for (const char character : internalName)
    {
        normalizedName.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    while (!normalizedName.empty() && normalizedName.back() == ' ')
    {
        normalizedName.pop_back();
    }

    if (normalizedName.empty())
    {
        return nullptr;
    }

    for (const DecorationEntry &entry : m_entries)
    {
        if (entry.internalName == normalizedName)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool SpriteFrameTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t frameCount = 0;
    uint32_t eFrameCount = 0;

    if (!reader.readUInt32(0, frameCount) || !reader.readUInt32(4, eFrameCount))
    {
        return false;
    }

    const size_t expectedSize = 8
        + static_cast<size_t>(frameCount) * SpriteFrameRecordSize
        + static_cast<size_t>(eFrameCount) * sizeof(uint16_t);

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_frames.clear();
    m_framePresent.clear();
    m_frames.reserve(frameCount);
    m_framePresent.reserve(frameCount);

    for (uint32_t index = 0; index < frameCount; ++index)
    {
        const size_t offset = 8 + static_cast<size_t>(index) * SpriteFrameRecordSize;
        SpriteFrameEntry entry = {};
        int32_t scaleFixed = 0;
        int32_t flags = 0;
        int16_t frameLengthTicks = 0;
        int16_t animationLengthTicks = 0;

        entry.spriteName = reader.readFixedString(offset + 0x00, 12, true);
        entry.textureName = reader.readFixedString(offset + 0x0c, 12, true);

        if (!reader.readInt32(offset + 0x28, scaleFixed)
            || !reader.readInt32(offset + 0x2c, flags)
            || !reader.readInt16(offset + 0x30, entry.glowRadius)
            || !reader.readInt16(offset + 0x32, entry.paletteId)
            || !reader.readInt16(offset + 0x36, frameLengthTicks)
            || !reader.readInt16(offset + 0x38, animationLengthTicks))
        {
            return false;
        }

        entry.scale = static_cast<float>(scaleFixed) / 65536.0f;
        entry.flags = static_cast<uint32_t>(flags);
        entry.frameLengthTicks = static_cast<int32_t>(frameLengthTicks) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(animationLengthTicks) * 8;
        m_frames.push_back(std::move(entry));
        m_framePresent.push_back(true);
    }

    m_eFrames.clear();
    m_eFrames.reserve(eFrameCount);

    for (uint32_t index = 0; index < eFrameCount; ++index)
    {
        uint16_t eFrame = 0;

        if (!reader.readUInt16(8 + static_cast<size_t>(frameCount) * SpriteFrameRecordSize + index * 2, eFrame))
        {
            return false;
        }

        m_eFrames.push_back(eFrame);
    }

    return !m_frames.empty();
}

bool SpriteFrameTable::loadFromYaml(const std::string &yamlText, std::string &errorMessage, bool append)
{
    if (!append)
    {
        m_frames.clear();
        m_framePresent.clear();
        m_eFrames.clear();
    }

    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    const YAML::Node spritesNode = root["sprites"];

    if (!spritesNode || !spritesNode.IsSequence())
    {
        errorMessage = "sprites must be a YAML sequence";
        return false;
    }

    for (const YAML::Node &spriteNode : spritesNode)
    {
        if (!spriteNode.IsMap())
        {
            continue;
        }

        const YAML::Node spriteNameNode = spriteNode["sprite_name"];
        const YAML::Node framesNode = spriteNode["frames"];

        if (!spriteNameNode || !spriteNameNode.IsScalar() || !framesNode || !framesNode.IsSequence()
            || framesNode.size() == 0)
        {
            continue;
        }

        const YAML::Node spriteIdNode = spriteNode["sprite_id"];

        if (!spriteIdNode || !spriteIdNode.IsScalar())
        {
            errorMessage = "sprite_id is required for each sprite group";
            return false;
        }

        const size_t spriteId = spriteIdNode.as<size_t>();

        const std::string spriteName = toLowerCopy(trimCopy(spriteNameNode.as<std::string>()));
        const int32_t animationLengthRaw = spriteNode["animation_length_raw"].as<int32_t>(0);

        for (size_t frameOffset = 0; frameOffset < framesNode.size(); ++frameOffset)
        {
            const YAML::Node frameNode = framesNode[frameOffset];

            if (!frameNode.IsMap())
            {
                errorMessage = "frames entries must be maps";
                return false;
            }

            const YAML::Node textureNameNode = frameNode["texture_name"];
            const YAML::Node frameLengthNode = frameNode["frame_length_raw"];

            if (!textureNameNode || !textureNameNode.IsScalar() || !frameLengthNode || !frameLengthNode.IsScalar())
            {
                errorMessage = "frame entries require texture_name and frame_length_raw";
                return false;
            }

            SpriteFrameEntry entry = {};
            entry.spriteName = frameOffset == 0 ? spriteName : std::string();
            entry.textureName = toLowerCopy(trimCopy(textureNameNode.as<std::string>()));
            entry.scale = frameNode["scale"].as<float>(1.0f);
            entry.glowRadius = frameNode["glow_radius"].as<int16_t>(0);
            entry.paletteId = frameNode["palette_id"].as<int16_t>(0);
            entry.frameLengthTicks = frameLengthNode.as<int32_t>() * 8;
            entry.animationLengthTicks = frameOffset == 0 ? animationLengthRaw * 8 : 0;

            if (!parseSpriteFrameFlagsNode(frameNode["flags"], entry.flags))
            {
                errorMessage = "invalid sprite frame flags";
                return false;
            }

            if (frameOffset == 0)
            {
                entry.flags |= static_cast<uint32_t>(SpriteFrameFlag::First);
            }
            else
            {
                entry.flags &= ~static_cast<uint32_t>(SpriteFrameFlag::First);
            }

            if (frameOffset + 1 < framesNode.size())
            {
                entry.flags |= static_cast<uint32_t>(SpriteFrameFlag::HasMore);
            }
            else
            {
                entry.flags &= ~static_cast<uint32_t>(SpriteFrameFlag::HasMore);
            }

            const size_t targetFrameIndex = spriteId + frameOffset;

            if (targetFrameIndex > std::numeric_limits<uint16_t>::max())
            {
                errorMessage = "sprite_id exceeds supported frame index range";
                return false;
            }

            if (targetFrameIndex >= m_frames.size())
            {
                m_frames.resize(targetFrameIndex + 1);
                m_framePresent.resize(targetFrameIndex + 1, false);
            }

            if (m_framePresent[targetFrameIndex])
            {
                errorMessage = "duplicate sprite frame index in YAML data";
                return false;
            }

            m_frames[targetFrameIndex] = std::move(entry);
            m_framePresent[targetFrameIndex] = true;
        }
    }

    rebuildSpriteNameIndex();
    return !m_frames.empty();
}

const SpriteFrameEntry *SpriteFrameTable::getFrame(uint16_t spriteId, uint32_t timeTicks) const
{
    if (spriteId >= m_frames.size() || spriteId >= m_framePresent.size() || !m_framePresent[spriteId])
    {
        return nullptr;
    }

    const SpriteFrameEntry *pFrame = &m_frames[spriteId];

    if (!hasFlag(pFrame->flags, SpriteFrameFlag::HasMore) || pFrame->animationLengthTicks <= 0)
    {
        return pFrame;
    }

    uint32_t localTimeTicks = timeTicks % static_cast<uint32_t>(pFrame->animationLengthTicks);
    size_t frameIndex = spriteId;

    while (frameIndex < m_frames.size())
    {
        if (frameIndex >= m_framePresent.size() || !m_framePresent[frameIndex])
        {
            return pFrame;
        }

        const SpriteFrameEntry &frame = m_frames[frameIndex];

        if (frame.frameLengthTicks <= 0 || localTimeTicks < static_cast<uint32_t>(frame.frameLengthTicks))
        {
            return &frame;
        }

        localTimeTicks -= static_cast<uint32_t>(frame.frameLengthTicks);

        if (!hasFlag(frame.flags, SpriteFrameFlag::HasMore))
        {
            return &frame;
        }

        ++frameIndex;
    }

    return pFrame;
}

std::vector<std::string> SpriteFrameTable::collectTextureNames(uint16_t spriteId) const
{
    std::vector<std::string> textureNames;

    if (spriteId >= m_frames.size() || spriteId >= m_framePresent.size() || !m_framePresent[spriteId])
    {
        return textureNames;
    }

    size_t frameIndex = spriteId;

    while (frameIndex < m_frames.size())
    {
        if (frameIndex >= m_framePresent.size() || !m_framePresent[frameIndex])
        {
            break;
        }

        const SpriteFrameEntry &frame = m_frames[frameIndex];

        for (int octant = 0; octant < 8; ++octant)
        {
            const ResolvedSpriteTexture resolvedTexture = resolveTexture(frame, octant);
            appendUnique(textureNames, resolvedTexture.textureName);
        }

        if (!hasFlag(frame.flags, SpriteFrameFlag::HasMore))
        {
            break;
        }

        ++frameIndex;
    }

    return textureNames;
}

std::optional<uint16_t> SpriteFrameTable::findFrameIndexBySpriteName(const std::string &spriteName) const
{
    const std::string normalizedName = toLowerCopy(spriteName);

    if (!m_eFrames.empty())
    {
        const auto entryIt = std::lower_bound(m_eFrames.begin(), m_eFrames.end(), normalizedName,
            [this](uint16_t frameIndex, const std::string &name)
            {
                return toLowerCopy(m_frames[frameIndex].spriteName) < name;
            });

        if (entryIt != m_eFrames.end() && toLowerCopy(m_frames[*entryIt].spriteName) == normalizedName)
        {
            return *entryIt;
        }
    }

    for (size_t index = 0; index < m_frames.size(); ++index)
    {
        if (toLowerCopy(m_frames[index].spriteName) == normalizedName)
        {
            return static_cast<uint16_t>(index);
        }
    }

    return std::nullopt;
}

void SpriteFrameTable::rebuildSpriteNameIndex()
{
    m_eFrames = buildSortedFirstFrameIndices(m_frames, m_framePresent);
}

ResolvedSpriteTexture SpriteFrameTable::resolveTexture(const SpriteFrameEntry &frame, int octant)
{
    const int clampedOctant = std::clamp(octant, 0, 7);
    ResolvedSpriteTexture resolvedTexture = {};
    const bool isMirrored = hasFlag(frame.flags, static_cast<SpriteFrameFlag>(mirrorFlagForOctant(clampedOctant)));
    resolvedTexture.mirrored = isMirrored;

    if (frame.textureName.empty())
    {
        return resolvedTexture;
    }

    if (hasFlag(frame.flags, SpriteFrameFlag::Image1))
    {
        resolvedTexture.textureName = frame.textureName;
        return resolvedTexture;
    }

    if (hasFlag(frame.flags, SpriteFrameFlag::Images3))
    {
        int sourceOctant = 0;

        if (clampedOctant == 3 || clampedOctant == 4 || clampedOctant == 5)
        {
            sourceOctant = 4;
        }
        else if (clampedOctant == 2 || clampedOctant == 6)
        {
            sourceOctant = 2;
        }

        resolvedTexture.textureName = buildTextureName(frame.textureName, sourceOctant);
        return resolvedTexture;
    }

    if (hasFlag(frame.flags, SpriteFrameFlag::Fidget))
    {
        if (clampedOctant == 0)
        {
            resolvedTexture.textureName = buildTextureName(frame.textureName, 0);
            return resolvedTexture;
        }

        if (clampedOctant == 4)
        {
            if (frame.textureName.size() >= 3)
            {
                resolvedTexture.textureName = frame.textureName.substr(0, frame.textureName.size() - 3) + "sta4";
            }

            return resolvedTexture;
        }

        if (clampedOctant == 3 || clampedOctant == 5)
        {
            if (frame.textureName.size() >= 3)
            {
                resolvedTexture.textureName = frame.textureName.substr(0, frame.textureName.size() - 3) + "sta3";
            }

            return resolvedTexture;
        }

        if (clampedOctant == 2 || clampedOctant == 6)
        {
            resolvedTexture.textureName = buildTextureName(frame.textureName, 2);
            return resolvedTexture;
        }

        resolvedTexture.textureName = buildTextureName(frame.textureName, 1);
        return resolvedTexture;
    }

    const int sourceOctant = isMirrored ? mirroredSourceOctant(clampedOctant) : clampedOctant;
    resolvedTexture.textureName = buildTextureName(frame.textureName, sourceOctant);
    return resolvedTexture;
}

bool SpriteFrameTable::hasFlag(uint32_t flags, SpriteFrameFlag flag)
{
    return (flags & static_cast<uint32_t>(flag)) != 0;
}

uint32_t SpriteFrameTable::mirrorFlagForOctant(int octant)
{
    return 0x100u << std::clamp(octant, 0, 7);
}

std::string SpriteFrameTable::buildTextureName(const std::string &baseName, int suffixIndex)
{
    if (baseName.size() >= 7)
    {
        return baseName;
    }

    return baseName + std::to_string(std::clamp(suffixIndex, 0, 7));
}
}
