#include "game/coop/CharacterFile.h"

#include "engine/net/ByteStream.h"
#include "game/maps/SaveSections.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iterator>
#include <random>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t CharacterFileMagic = 0x4843594Fu; // "OYCH"
constexpr uint32_t CharacterFileFormat = 1;
constexpr size_t MaxCharacterBytes = 16u * 1024u * 1024u;
constexpr const char *CharacterFileExtension = ".oychar";
}

std::string CharacterFile::describe() const
{
    if (character.members.empty())
    {
        return "nobody";
    }

    const Character &member = character.members.front();
    return member.name + " (" + member.className + ' ' + std::to_string(member.level) + ", " + ruleset.id + ')';
}

std::filesystem::path characterFileFolder()
{
    return std::filesystem::path("saves") / "characters";
}

std::optional<std::filesystem::path> characterFilePath(const std::string &name)
{
    std::string fileName;

    for (const char character : name)
    {
        const unsigned char value = static_cast<unsigned char>(character);
        fileName.push_back(std::isalnum(value) != 0 || character == '-' || character == '_' ? character : '_');
    }

    if (fileName.empty() || std::all_of(fileName.begin(), fileName.end(), [](char c) { return c == '_'; }))
    {
        return std::nullopt;
    }

    return characterFileFolder() / (fileName + CharacterFileExtension);
}

CharacterFile makeCharacterFile(const Party::Snapshot &party, const RulesetSelection &ruleset)
{
    CharacterFile file;
    std::random_device device;

    for (uint8_t &byte : file.id)
    {
        byte = uint8_t(device());
    }

    file.ruleset = ruleset;
    file.character = party;
    file.character.campaign = {};
    file.character.adventurersInnMembers.clear();

    if (file.character.members.size() > 1)
    {
        file.character.members.resize(1);
    }

    file.character.activeMemberIndex = 0;
    return file;
}

bool writeCharacterFile(const std::filesystem::path &path, CharacterFile &file, std::string &error)
{
    // The character travels in a save's own layout, so a later build reads it as it reads an older save. A MAW
    // game's state is where a save keeps what the ruleset holds for the party.
    GameSaveData carrier = {};
    carrier.party = file.character;
    carrier.party.campaign = {};
    carrier.ruleset = file.ruleset;

    if (!file.ruleset.isStandard())
    {
        carrier.mawState.emplace();
    }

    const std::vector<uint8_t> body = SaveSections::encodeGame(carrier);
    Engine::ByteWriter writer;
    writer.u32(CharacterFileMagic);
    writer.u32(CharacterFileFormat);
    writer.u32(file.revision + 1);

    for (const uint8_t byte : file.id)
    {
        writer.u8(byte);
    }

    writer.block(body);
    std::error_code fileError;
    std::filesystem::create_directories(path.parent_path(), fileError);
    std::filesystem::path written = path;
    written += ".tmp";

    {
        std::ofstream stream(written, std::ios::binary | std::ios::trunc);
        const std::vector<uint8_t> &bytes = writer.bytes();
        stream.write(reinterpret_cast<const char *>(bytes.data()), std::streamsize(bytes.size()));

        if (!stream.good())
        {
            error = "could not write " + written.string();
            return false;
        }
    }

    // The copy before this one stays beside it.
    if (std::filesystem::exists(path, fileError))
    {
        std::filesystem::path previous = path;
        previous += ".bak";
        std::filesystem::rename(path, previous, fileError);
    }

    std::filesystem::rename(written, path, fileError);

    if (fileError)
    {
        error = "could not put " + path.string() + " in place: " + fileError.message();
        return false;
    }

    ++file.revision;
    return true;
}

std::optional<CharacterFile> readCharacterFile(const std::filesystem::path &path, std::string &error)
{
    std::ifstream stream(path, std::ios::binary);

    if (!stream.good())
    {
        error = "could not open " + path.string();
        return std::nullopt;
    }

    const std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    Engine::ByteReader reader(bytes);

    if (reader.u32() != CharacterFileMagic || !reader.ok())
    {
        error = path.string() + " is not a character file";
        return std::nullopt;
    }

    if (reader.u32() != CharacterFileFormat)
    {
        error = path.string() + " is a character file of a later OpenYAMM";
        return std::nullopt;
    }

    CharacterFile file;
    file.revision = reader.u32();

    for (uint8_t &byte : file.id)
    {
        byte = reader.u8();
    }

    const std::vector<uint8_t> body = reader.block(MaxCharacterBytes);

    if (!reader.ok())
    {
        error = path.string() + " is cut short";
        return std::nullopt;
    }

    std::string decodeError;
    std::optional<GameSaveData> carrier = SaveSections::decodeGame(body, decodeError);

    if (!carrier || carrier->party.members.empty())
    {
        error = path.string() + " holds no character" + (decodeError.empty() ? std::string() : ": " + decodeError);
        return std::nullopt;
    }

    file.ruleset = carrier->ruleset;
    file.character = std::move(carrier->party);
    file.character.campaign = {};
    return file;
}

std::vector<std::filesystem::path> listCharacterFiles()
{
    std::vector<std::filesystem::path> files;
    std::error_code fileError;

    for (std::filesystem::directory_iterator it(characterFileFolder(), fileError), end; !fileError && it != end;
         it.increment(fileError))
    {
        if (it->is_regular_file(fileError) && it->path().extension() == CharacterFileExtension)
        {
            files.push_back(it->path());
        }
    }

    std::sort(files.begin(), files.end());
    return files;
}
}
