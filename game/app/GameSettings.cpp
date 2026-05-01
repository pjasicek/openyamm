#include "game/app/GameSettings.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
using IniSection = std::unordered_map<std::string, std::string>;
using IniDocument = std::unordered_map<std::string, IniSection>;

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;
    size_t end = value.size();

    while (begin < end && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

bool parseBoolValue(const std::string &value, bool &result)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "1" || normalized == "true" || normalized == "yes" || normalized == "on")
    {
        result = true;
        return true;
    }

    if (normalized == "0" || normalized == "false" || normalized == "no" || normalized == "off")
    {
        result = false;
        return true;
    }

    return false;
}

bool parseIntValue(const std::string &value, int &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    result = static_cast<int>(parsed);
    return true;
}

bool parseUInt32Value(const std::string &value, uint32_t &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    result = static_cast<uint32_t>(parsed);
    return true;
}

bool parseFloatValue(const std::string &value, float &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const float parsed = std::strtof(trimmed.c_str(), &pEnd);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    result = parsed;
    return true;
}

std::optional<std::string> getIniValue(const IniDocument &document, const std::string &section, const std::string &key)
{
    const auto sectionIt = document.find(section);

    if (sectionIt == document.end())
    {
        return std::nullopt;
    }

    const auto valueIt = sectionIt->second.find(key);

    if (valueIt == sectionIt->second.end())
    {
        return std::nullopt;
    }

    return valueIt->second;
}

IniDocument parseIniDocument(const std::string &text)
{
    IniDocument document;
    std::string currentSection = "global";
    std::istringstream stream(text);
    std::string line;

    while (std::getline(stream, line))
    {
        const std::string trimmed = trimCopy(line);

        if (trimmed.empty() || trimmed[0] == ';' || trimmed[0] == '#')
        {
            continue;
        }

        if (trimmed.size() >= 3 && trimmed.front() == '[' && trimmed.back() == ']')
        {
            currentSection = toLowerCopy(trimCopy(trimmed.substr(1, trimmed.size() - 2)));
            continue;
        }

        const size_t separatorPos = trimmed.find('=');

        if (separatorPos == std::string::npos)
        {
            continue;
        }

        const std::string key = toLowerCopy(trimCopy(trimmed.substr(0, separatorPos)));
        const std::string value = trimCopy(trimmed.substr(separatorPos + 1));

        if (!key.empty())
        {
            document[currentSection][key] = value;
        }
    }

    return document;
}

std::string turnRateModeString(TurnRateMode mode)
{
    switch (mode)
    {
    case TurnRateMode::X16:
        return "16x";

    case TurnRateMode::X32:
        return "32x";

    case TurnRateMode::Smooth:
        return "smooth";
    }

    return "32x";
}

std::string gameplayUiLayoutString(GameplayUiLayout layout)
{
    switch (layout)
    {
    case GameplayUiLayout::Standard:
        return "standard";

    case GameplayUiLayout::Widescreen:
        return "widescreen";
    }

    return "widescreen";
}

std::string windowModeString(WindowMode mode)
{
    switch (mode)
    {
    case WindowMode::Windowed:
        return "windowed";

    case WindowMode::WindowedFullscreen:
        return "windowed_fullscreen";

    case WindowMode::Fullscreen:
        return "fullscreen";
    }

    return "windowed";
}

TurnRateMode parseTurnRateMode(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "16x")
    {
        return TurnRateMode::X16;
    }

    if (normalized == "smooth")
    {
        return TurnRateMode::Smooth;
    }

    return TurnRateMode::X32;
}

GameplayUiLayout parseGameplayUiLayout(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "standard")
    {
        return GameplayUiLayout::Standard;
    }

    return GameplayUiLayout::Widescreen;
}

WindowMode parseWindowMode(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "fullscreen")
    {
        return WindowMode::Fullscreen;
    }

    if (normalized == "windowed_fullscreen"
        || normalized == "windowed-fullscreen"
        || normalized == "borderless")
    {
        return WindowMode::WindowedFullscreen;
    }

    return WindowMode::Windowed;
}

bool parseResolutionValue(const std::string &value, int &width, int &height)
{
    const std::string normalized = toLowerCopy(trimCopy(value));
    const size_t separatorPos = normalized.find('x');

    if (separatorPos == std::string::npos)
    {
        return false;
    }

    int parsedWidth = 0;
    int parsedHeight = 0;

    if (!parseIntValue(normalized.substr(0, separatorPos), parsedWidth)
        || !parseIntValue(normalized.substr(separatorPos + 1), parsedHeight))
    {
        return false;
    }

    if (parsedWidth <= 0 || parsedHeight <= 0)
    {
        return false;
    }

    width = parsedWidth;
    height = parsedHeight;
    return true;
}
}

GameSettings GameSettings::createDefault()
{
    return GameSettings();
}

std::optional<GameSettings> loadGameSettings(const std::filesystem::path &path, std::string &error)
{
    std::ifstream input(path);

    if (!input)
    {
        error = "Unable to open settings file";
        return std::nullopt;
    }

    std::ostringstream buffer;
    buffer << input.rdbuf();
    const IniDocument document = parseIniDocument(buffer.str());
    GameSettings settings = GameSettings::createDefault();

    if (const std::optional<std::string> value = getIniValue(document, "audio", "sound_volume"))
    {
        int parsed = settings.soundVolume;

        if (parseIntValue(*value, parsed))
        {
            settings.soundVolume = std::clamp(parsed, 0, 9);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "audio", "music_volume"))
    {
        int parsed = settings.musicVolume;

        if (parseIntValue(*value, parsed))
        {
            settings.musicVolume = std::clamp(parsed, 0, 9);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "audio", "voice_volume"))
    {
        int parsed = settings.voiceVolume;

        if (parseIntValue(*value, parsed))
        {
            settings.voiceVolume = std::clamp(parsed, 0, 9);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "turn_rate"))
    {
        settings.turnRate = parseTurnRateMode(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "walksound"))
    {
        bool parsed = settings.walksound;

        if (parseBoolValue(*value, parsed))
        {
            settings.walksound = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "walk_sound"))
    {
        bool parsed = settings.walksound;

        if (parseBoolValue(*value, parsed))
        {
            settings.walksound = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "show_hits"))
    {
        bool parsed = settings.showHits;

        if (parseBoolValue(*value, parsed))
        {
            settings.showHits = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "always_run"))
    {
        bool parsed = settings.alwaysRun;

        if (parseBoolValue(*value, parsed))
        {
            settings.alwaysRun = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "flip_on_exit"))
    {
        bool parsed = settings.flipOnExit;

        if (parseBoolValue(*value, parsed))
        {
            settings.flipOnExit = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "keyboard_interaction_depth"))
    {
        int parsed = settings.keyboardInteractionDepth;

        if (parseIntValue(*value, parsed))
        {
            settings.keyboardInteractionDepth = std::clamp(parsed, 32, 4096);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "mouse_interaction_depth"))
    {
        int parsed = settings.mouseInteractionDepth;

        if (parseIntValue(*value, parsed))
        {
            settings.mouseInteractionDepth = std::clamp(parsed, 32, 4096);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "blood_splats"))
    {
        bool parsed = settings.bloodSplats;

        if (parseBoolValue(*value, parsed))
        {
            settings.bloodSplats = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "colored_lights"))
    {
        bool parsed = settings.coloredLights;

        if (parseBoolValue(*value, parsed))
        {
            settings.coloredLights = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "tinting"))
    {
        bool parsed = settings.tinting;

        if (parseBoolValue(*value, parsed))
        {
            settings.tinting = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "shadows"))
    {
        bool parsed = settings.shadows;

        if (parseBoolValue(*value, parsed))
        {
            settings.shadows = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "texture_filtering"))
    {
        bool parsed = settings.textureFiltering;

        if (parseBoolValue(*value, parsed))
        {
            settings.textureFiltering = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_filtering"))
    {
        settings.terrainFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_anisotropy"))
    {
        settings.terrainAnisotropy = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "bmodel_filtering"))
    {
        settings.bmodelFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "billboard_filtering"))
    {
        settings.billboardFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "ui_filtering"))
    {
        settings.uiFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "text_filtering"))
    {
        settings.textFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "minimap_filtering"))
    {
        settings.minimapFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "gameplay_ui_layout"))
    {
        settings.gameplayUiLayout = parseGameplayUiLayout(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "window_mode"))
    {
        settings.windowMode = parseWindowMode(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "resolution"))
    {
        int parsedWidth = settings.resolutionWidth;
        int parsedHeight = settings.resolutionHeight;

        if (parseResolutionValue(*value, parsedWidth, parsedHeight))
        {
            settings.resolutionWidth = std::clamp(parsedWidth, 320, 16384);
            settings.resolutionHeight = std::clamp(parsedHeight, 200, 16384);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "startup", "start_in_main_menu"))
    {
        bool parsed = settings.startInMainMenu;

        if (parseBoolValue(*value, parsed))
        {
            settings.startInMainMenu = parsed;
        }
    }

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        const std::optional<std::string> value = getIniValue(document, "keyboard", std::string(definition.iniKey));

        if (!value.has_value())
        {
            continue;
        }

        const SDL_Scancode scancode = parseKeyboardBindingName(trimCopy(*value));

        if (scancode != SDL_SCANCODE_UNKNOWN)
        {
            settings.keyboard.setBinding(definition.action, scancode);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "preseed_party"))
    {
        bool parsed = settings.preseedParty;

        if (parseBoolValue(*value, parsed))
        {
            settings.preseedParty = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "party_seed_roster_id"))
    {
        uint32_t parsed = settings.partySeedRosterId;

        if (parseUInt32Value(*value, parsed))
        {
            settings.partySeedRosterId = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_map_file"))
    {
        const std::string trimmed = trimCopy(*value);

        if (!trimmed.empty())
        {
            settings.startMapFile = trimmed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "override_start_position"))
    {
        bool parsed = settings.overrideStartPosition;

        if (parseBoolValue(*value, parsed))
        {
            settings.overrideStartPosition = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_x"))
    {
        float parsed = settings.startX;

        if (parseFloatValue(*value, parsed))
        {
            settings.startX = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_y"))
    {
        float parsed = settings.startY;

        if (parseFloatValue(*value, parsed))
        {
            settings.startY = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_z"))
    {
        float parsed = settings.startZ;

        if (parseFloatValue(*value, parsed))
        {
            settings.startZ = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_flying"))
    {
        bool parsed = settings.startFlying;

        if (parseBoolValue(*value, parsed))
        {
            settings.startFlying = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "movement_speed_multiplier"))
    {
        float parsed = settings.movementSpeedMultiplier;

        if (parseFloatValue(*value, parsed))
        {
            settings.movementSpeedMultiplier = std::clamp(parsed, 0.1f, 20.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "immortal"))
    {
        bool parsed = settings.immortal;

        if (parseBoolValue(*value, parsed))
        {
            settings.immortal = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "unlimited_mana"))
    {
        bool parsed = settings.unlimitedMana;

        if (parseBoolValue(*value, parsed))
        {
            settings.unlimitedMana = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "new_game_god_lich"))
    {
        bool parsed = settings.newGameGodLich;

        if (parseBoolValue(*value, parsed))
        {
            settings.newGameGodLich = parsed;
        }
    }

    error.clear();
    return settings;
}

bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error)
{
    std::ofstream output(path);

    if (!output)
    {
        error = "Unable to write settings file";
        return false;
    }

    output
        << "; OpenYAMM settings\n"
        << "; Volumes use the original-style 0..9 scale.\n\n"
        << "[audio]\n"
        << "sound_volume=" << std::clamp(settings.soundVolume, 0, 9) << '\n'
        << "music_volume=" << std::clamp(settings.musicVolume, 0, 9) << '\n'
        << "voice_volume=" << std::clamp(settings.voiceVolume, 0, 9) << "\n\n"
        << "[controls]\n"
        << "turn_rate=" << turnRateModeString(settings.turnRate) << '\n'
        << "walksound=" << (settings.walksound ? "true" : "false") << '\n'
        << "show_hits=" << (settings.showHits ? "true" : "false") << '\n'
        << "always_run=" << (settings.alwaysRun ? "true" : "false") << '\n'
        << "flip_on_exit=" << (settings.flipOnExit ? "true" : "false") << "\n\n"
        << "[gameplay]\n"
        << "keyboard_interaction_depth=" << std::clamp(settings.keyboardInteractionDepth, 32, 4096) << '\n'
        << "mouse_interaction_depth=" << std::clamp(settings.mouseInteractionDepth, 32, 4096) << "\n\n"
        << "[startup]\n"
        << "start_in_main_menu=" << (settings.startInMainMenu ? "true" : "false") << "\n\n"
        << "[keyboard]\n";

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        output << definition.iniKey << '=' << keyboardBindingName(settings.keyboard.binding(definition.action)) << '\n';
    }

    output
        << '\n'
        << "[video]\n"
        << "blood_splats=" << (settings.bloodSplats ? "true" : "false") << '\n'
        << "colored_lights=" << (settings.coloredLights ? "true" : "false") << '\n'
        << "tinting=" << (settings.tinting ? "true" : "false") << '\n'
        << "shadows=" << (settings.shadows ? "true" : "false") << '\n'
        << "texture_filtering=" << (settings.textureFiltering ? "true" : "false") << '\n'
        << "terrain_filtering=" << settings.terrainFiltering << '\n'
        << "terrain_anisotropy=" << settings.terrainAnisotropy << '\n'
        << "bmodel_filtering=" << settings.bmodelFiltering << '\n'
        << "billboard_filtering=" << settings.billboardFiltering << '\n'
        << "ui_filtering=" << settings.uiFiltering << '\n'
        << "text_filtering=" << settings.textFiltering << '\n'
        << "minimap_filtering=" << settings.minimapFiltering << '\n'
        << "window_mode=" << windowModeString(settings.windowMode) << '\n'
        << "resolution=" << std::clamp(settings.resolutionWidth, 320, 16384)
        << 'x' << std::clamp(settings.resolutionHeight, 200, 16384) << '\n'
        << "gameplay_ui_layout=" << gameplayUiLayoutString(settings.gameplayUiLayout) << "\n\n"
        << "[debug]\n"
        << "preseed_party=" << (settings.preseedParty ? "true" : "false") << '\n'
        << "party_seed_roster_id=" << settings.partySeedRosterId << '\n'
        << "start_map_file=" << settings.startMapFile << '\n'
        << "override_start_position=" << (settings.overrideStartPosition ? "true" : "false") << '\n'
        << "start_x=" << settings.startX << '\n'
        << "start_y=" << settings.startY << '\n'
        << "start_z=" << settings.startZ << '\n'
        << "start_flying=" << (settings.startFlying ? "true" : "false") << '\n'
        << "movement_speed_multiplier=" << settings.movementSpeedMultiplier << '\n'
        << "immortal=" << (settings.immortal ? "true" : "false") << '\n'
        << "unlimited_mana=" << (settings.unlimitedMana ? "true" : "false") << '\n'
        << "new_game_god_lich=" << (settings.newGameGodLich ? "true" : "false") << '\n';

    if (!output.good())
    {
        error = "Failed while writing settings file";
        return false;
    }

    error.clear();
    return true;
}
}
