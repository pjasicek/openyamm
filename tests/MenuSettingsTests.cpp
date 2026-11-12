#include "game/ui/MenuSettingsModel.h"
#include <doctest/doctest.h>
#include <algorithm>
#include <array>
#include <fstream>
#include <iterator>
#include <string>
#include <utility>

using namespace OpenYAMM::Game;

TEST_CASE("creature shadow quality and LOD settings validate and persist")
{
    GameSettings settings = GameSettings::createDefault();
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-model-settings.ini";
    std::string error;
    for (const std::string quality : {"0", "1", "2", "3"})
    {
        REQUIRE(setMenuSettingValue(settings, "model_shadow_quality", quality));
        CHECK(menuSettingValue(settings, "model_shadow_quality") == quality);
        CHECK(settings.shadows == (quality != "0"));
        REQUIRE(setMenuSettingValue(settings, "model_lods", "false"));
        REQUIRE(saveGameSettings(path, settings, error));
        const std::optional<GameSettings> loaded = loadGameSettings(path, error);
        REQUIRE_MESSAGE(loaded, error);
        CHECK(menuSettingValue(*loaded, "model_shadow_quality") == quality);
        CHECK_FALSE(loaded->modelLods);
    }
    CHECK_FALSE(setMenuSettingValue(settings, "model_shadow_quality", "4"));
    CHECK_FALSE(setMenuSettingValue(settings, "model_lods", "unknown"));
    CHECK(menuSettingValue(settings, "model_shadow_quality") == "3");
    std::filesystem::remove(path);
}

TEST_CASE("MAW number keys select a member by default and the bag choice persists")
{
    GameSettings settings = GameSettings::createDefault();
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-bag-number-keys.ini";
    std::string error;
    CHECK(menuSettingValue(settings, "bag_number_keys") == "member");
    CHECK_FALSE(setMenuSettingValue(settings, "bag_number_keys", "shift"));
    REQUIRE(setMenuSettingValue(settings, "bag_number_keys", "bag"));
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded, error);
    CHECK_EQ(loaded->bagNumberKeys, "bag");
    std::filesystem::remove(path);
}

TEST_CASE("menu settings validate input and preserve unrelated game configuration")
{
    GameSettings settings = GameSettings::createDefault();
    settings.assetRoot = "/custom/content";
    settings.immortal = true;
    settings.mouseSensitivity = 42;
    CHECK(setMenuSettingValue(settings, "music_volume", "0"));
    CHECK(settings.musicVolume == 0);
    CHECK_FALSE(setMenuSettingValue(settings, "music_volume", "10"));
    CHECK_FALSE(setMenuSettingValue(settings, "music_volume", "2noise"));
    CHECK(settings.musicVolume == 0);
    CHECK_FALSE(setMenuSettingValue(settings, "mouse_sensitivity", "-1"));
    CHECK(settings.mouseSensitivity == 42);
    CHECK(setMenuSettingValue(settings, "resolution", "1920x1080"));
    CHECK(menuSettingValue(settings, "resolution") == "1920x1080");
    CHECK_FALSE(setMenuSettingValue(settings, "resolution", "1920x1080junk"));
    CHECK_FALSE(setMenuSettingValue(settings, "resolution", "32x0"));
    CHECK(menuSettingValue(settings, "resolution") == "1920x1080");
    CHECK(setMenuSettingValue(settings, "window_mode", "windowed_fullscreen"));
    CHECK(settings.windowMode == WindowMode::WindowedFullscreen);
    CHECK_FALSE(setMenuSettingValue(settings, "window_mode", "fake"));
    CHECK(setMenuSettingValue(settings, "terrain_anisotropy", "16x"));
    CHECK(settings.terrainFiltering == "anisotropic");
    CHECK(settings.terrainAnisotropy == "16x");
    CHECK(setMenuSettingValue(settings, "bolster_monsters", "true"));
    CHECK(settings.bolsterMonsters);
    CHECK_FALSE(setMenuSettingValue(settings, "bolster_monsters", "yes"));
    CHECK_FALSE(setMenuSettingValue(settings, "immortal", "false"));
    CHECK(settings.immortal);
    CHECK(settings.assetRoot == "/custom/content");
}

TEST_CASE("menu binding reservation and equality follow native single input bindings")
{
    constexpr KeyboardAction Jump = KeyboardAction::Jump;
    CHECK(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_ESCAPE), Jump));
    // Quick save and load are bindings of their own (F9 and F10 by default), so those keys are free to assign.
    CHECK_FALSE(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_F9), Jump));
    CHECK_FALSE(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_F10), Jump));
    CHECK(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_5), Jump));
    CHECK_FALSE(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_F2), Jump));
    CHECK_FALSE(reservedMenuBinding(mouseButtonInputBinding(SDL_BUTTON_LEFT), Jump));
    // The bag keys may take the party's numbers: they use them only on the inventory pages.
    CHECK_FALSE(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_3), KeyboardAction::Bag3));
    CHECK(reservedMenuBinding(keyboardInputBinding(SDL_SCANCODE_ESCAPE), KeyboardAction::Bag3));
    CHECK(sameMenuBinding(mouseButtonInputBinding(SDL_BUTTON_LEFT), mouseButtonInputBinding(SDL_BUTTON_LEFT)));
    CHECK_FALSE(sameMenuBinding(mouseButtonInputBinding(SDL_BUTTON_LEFT), keyboardInputBinding(SDL_SCANCODE_A)));
    CHECK_FALSE(sameMenuBinding(mouseButtonInputBinding(SDL_BUTTON_LEFT), mouseButtonInputBinding(SDL_BUTTON_RIGHT)));
}

TEST_CASE("mouse wheel bindings distinguish directions and survive settings save and load")
{
    const InputBinding up = mouseWheelInputBinding(1.0f);
    const InputBinding down = mouseWheelInputBinding(-1.0f);
    CHECK(mouseWheelInputBinding(0.0f).kind == InputBindingKind::None);
    CHECK_FALSE(reservedMenuBinding(up, KeyboardAction::Jump));
    CHECK_FALSE(reservedMenuBinding(down, KeyboardAction::Jump));
    CHECK(sameMenuBinding(up, parseInputBindingName("MouseWheelUp")));
    CHECK(sameMenuBinding(down, parseInputBindingName("Wheel Down")));
    CHECK(sameMenuBinding(up, parseInputBindingName(inputBindingName(up))));
    CHECK(sameMenuBinding(down, parseInputBindingName(inputBindingName(down))));
    CHECK_FALSE(sameMenuBinding(up, down));
    CHECK_FALSE(sameMenuBinding(up, mouseButtonInputBinding(SDL_BUTTON_LEFT)));
    CHECK(inputBindingDisplayName(up) == "Wheel Up");
    CHECK(inputBindingDisplayName(down) == "Wheel Down");

    GameSettings settings = GameSettings::createDefault();
    settings.keyboard.setBinding(KeyboardAction::FlyUp, up);
    settings.keyboard.setBinding(KeyboardAction::FlyDown, down);
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-wheel-settings.ini";
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded, error);
    CHECK(sameMenuBinding(up, loaded->keyboard.binding(KeyboardAction::FlyUp)));
    CHECK(sameMenuBinding(down, loaded->keyboard.binding(KeyboardAction::FlyDown)));
    std::filesystem::remove(path);
}

TEST_CASE("extra mouse button bindings are polled and survive settings save and load")
{
    const InputBinding mouse4 = mouseButtonInputBinding(SDL_BUTTON_X1);
    const InputBinding mouse5 = mouseButtonInputBinding(SDL_BUTTON_X2);
    CHECK(inputBindingDisplayName(mouse5) == "Mouse 5");
    CHECK(sameMenuBinding(mouse5, parseInputBindingName(inputBindingName(mouse5))));
    CHECK(sameMenuBinding(mouse5, parseInputBindingName("Mouse 5")));
    CHECK(sameMenuBinding(
        mouseButtonInputBinding(SDL_BUTTON_MIDDLE),
        parseInputBindingName(inputBindingName(mouseButtonInputBinding(SDL_BUTTON_MIDDLE)))));
    CHECK_FALSE(sameMenuBinding(mouse4, mouse5));
    CHECK(parseInputBindingName("MouseButton_0").kind == InputBindingKind::None);
    CHECK(parseInputBindingName("MouseButton_33").kind == InputBindingKind::None);

    CHECK(mouseButtonHeldInFlags(SDL_BUTTON_X2MASK, SDL_BUTTON_X2));
    CHECK(mouseButtonHeldInFlags(SDL_BUTTON_X1MASK | SDL_BUTTON_LMASK, SDL_BUTTON_X1));
    CHECK_FALSE(mouseButtonHeldInFlags(SDL_BUTTON_X1MASK, SDL_BUTTON_X2));
    CHECK_FALSE(mouseButtonHeldInFlags(0, SDL_BUTTON_X2));
    CHECK_FALSE(mouseButtonHeldInFlags(SDL_BUTTON_X2MASK, 0));

    GameSettings settings = GameSettings::createDefault();
    settings.keyboard.setBinding(KeyboardAction::DoubleSpeed, mouse5);
    settings.keyboard.setBinding(KeyboardAction::Jump, mouse4);
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-mouse-button-settings.ini";
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded, error);
    CHECK(sameMenuBinding(mouse5, loaded->keyboard.binding(KeyboardAction::DoubleSpeed)));
    CHECK(sameMenuBinding(mouse4, loaded->keyboard.binding(KeyboardAction::Jump)));
    std::filesystem::remove(path);
}

TEST_CASE("invert mouse Y defaults off and persists menu changes")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-invert-mouse-settings.ini";
    std::string error;
    GameSettings settings = GameSettings::createDefault();
    CHECK_FALSE(settings.invertMouseY);
    CHECK(menuSettingValue(settings, "invert_mouse_y") == "false");

    for (const std::string value : {"true", "false"})
    {
        REQUIRE(setMenuSettingValue(settings, "invert_mouse_y", value));
        CHECK(menuSettingValue(settings, "invert_mouse_y") == value);
        CHECK_FALSE(setMenuSettingValue(settings, "invert_mouse_y", "invalid"));
        CHECK(menuSettingValue(settings, "invert_mouse_y") == value);
        REQUIRE(saveGameSettings(path, settings, error));
        const std::optional<GameSettings> loaded = loadGameSettings(path, error);
        REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
        CHECK(menuSettingValue(*loaded, "invert_mouse_y") == value);
    }

    {
        std::ofstream file(path);
        file << "[controls]\nmouse_sensitivity=42\n";
    }
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
    CHECK_FALSE(loaded->invertMouseY);
    CHECK(loaded->mouseSensitivity == 42);
    std::filesystem::remove(path);
}

TEST_CASE("repeated voice line interval defaults off, validates its steps and persists")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-repeated-voice-settings.ini";
    std::string error;
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.repeatedVoiceLineIntervalMs == 0);
    CHECK(menuSettingValue(settings, "repeated_voice_lines") == "0");

    for (const std::string value : {"500", "1000", "2000", "3000", "5000", "10000", "0"})
    {
        REQUIRE(setMenuSettingValue(settings, "repeated_voice_lines", value));
        CHECK(menuSettingValue(settings, "repeated_voice_lines") == value);
        REQUIRE(saveGameSettings(path, settings, error));
        const std::optional<GameSettings> loaded = loadGameSettings(path, error);
        REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
        CHECK(menuSettingValue(*loaded, "repeated_voice_lines") == value);
    }

    CHECK_FALSE(setMenuSettingValue(settings, "repeated_voice_lines", "750"));
    CHECK_FALSE(setMenuSettingValue(settings, "repeated_voice_lines", "off"));
    CHECK(settings.repeatedVoiceLineIntervalMs == 0);

    {
        std::ofstream file(path);
        file << "[audio]\nrepeated_voice_line_interval_ms=1800\n";
    }
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
    CHECK(loaded->repeatedVoiceLineIntervalMs == 1800);
    CHECK(menuSettingValue(*loaded, "repeated_voice_lines") == "2000");
    std::filesystem::remove(path);
}

TEST_CASE("enemy health menu settings validate modes and preserve other options")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(menuSettingValue(settings, "enemy_health_bars") == "combat");
    CHECK(setMenuSettingValue(settings, "enemy_health_bars", "target"));
    CHECK_FALSE(setMenuSettingValue(settings, "enemy_health_bars", "true"));
    CHECK(menuSettingValue(settings, "enemy_health_bars") == "target");
    CHECK(setMenuSettingValue(settings, "enemy_health_bar_values", "all"));
    CHECK_FALSE(setMenuSettingValue(settings, "enemy_health_bar_values", "unknown"));
    CHECK(menuSettingValue(settings, "enemy_health_bar_values") == "all");
    CHECK(setMenuSettingValue(settings, "enemy_health_bar_damage_trail", "false"));
    CHECK_FALSE(settings.enemyHealthBarDamageTrail);
    CHECK(settings.combatText);
    CHECK_FALSE(setMenuSettingValue(settings, "combat_target_panel", "true"));
}

TEST_CASE("enemy health settings migrate legacy toggles and roundtrip the replacement options")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-enemy-bars-settings.ini";
    std::string error;
    for (const char *panel : {"true", "false"})
    {
        {
            std::ofstream file(path);
            file << "[gameplay]\ncombat_actor_hp_bars=false\ncombat_target_panel=" << panel << '\n';
        }
        const std::optional<GameSettings> loaded = loadGameSettings(path, error);
        REQUIRE(loaded);
        CHECK(loaded->enemyHealthBarMode == (std::string_view(panel) == "true" ? "target" : "off"));
    }
    GameSettings settings = GameSettings::createDefault();
    settings.enemyHealthBarMode = "nearby";
    settings.enemyHealthBarValues = "all";
    settings.enemyHealthBarDamageTrail = false;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE(loaded);
    CHECK(loaded->enemyHealthBarMode == "nearby");
    CHECK(loaded->enemyHealthBarValues == "all");
    CHECK_FALSE(loaded->enemyHealthBarDamageTrail);
    std::filesystem::remove(path);
}

TEST_CASE("ambient occlusion is optional and its intensity validates and persists")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.ambientOcclusion); // Desktop default.
    CHECK(settings.ambientOcclusionStrength == 50);
    REQUIRE(setMenuSettingValue(settings, "ambient_occlusion", "false"));
    REQUIRE(setMenuSettingValue(settings, "ambient_occlusion", "true"));
    REQUIRE(setMenuSettingValue(settings, "ambient_occlusion_strength", "42"));
    CHECK_FALSE(setMenuSettingValue(settings, "ambient_occlusion", "yes"));
    for (const std::string value : {"-1", "101", "35junk", ""})
    {
        CHECK_FALSE(setMenuSettingValue(settings, "ambient_occlusion_strength", value));
    }
    CHECK(menuSettingValue(settings, "ambient_occlusion") == "true");
    CHECK(menuSettingValue(settings, "ambient_occlusion_strength") == "42");
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-ao-settings.ini";
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded, error);
    CHECK(loaded->ambientOcclusion);
    CHECK(loaded->ambientOcclusionStrength == 42);
    {
        std::ofstream file(path);
        file << "[profile]\nname=desktop\nversion=5\n"
             << "[video]\nambient_occlusion=false\nambient_occlusion_strength=900\n";
    }
    const std::optional<GameSettings> bounded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(bounded, error);
    CHECK_FALSE(bounded->ambientOcclusion);
    CHECK(bounded->ambientOcclusionStrength == 100);
    std::filesystem::remove(path);
}

TEST_CASE("the quicksaves kept setting defaults to three, validates one to twenty and persists")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.quickSaveSlots == 3);
    REQUIRE(setMenuSettingValue(settings, "quicksave_slots", "20"));
    REQUIRE(setMenuSettingValue(settings, "quicksave_slots", "1"));
    REQUIRE(setMenuSettingValue(settings, "quicksave_slots", "7"));
    for (const std::string value : {"0", "21", "-1", "7junk", ""})
    {
        CHECK_FALSE(setMenuSettingValue(settings, "quicksave_slots", value));
    }
    CHECK(menuSettingValue(settings, "quicksave_slots") == "7");
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-quicksave-slots-settings.ini";
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE(loaded);
    CHECK(loaded->quickSaveSlots == 7);
    std::filesystem::remove(path);
}

TEST_CASE("sharpening defaults to the desktop profile and its strength validates and persists")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.sharpening == 50);
    REQUIRE(setMenuSettingValue(settings, "sharpening", "40"));
    for (const std::string value : {"-1", "101", "40junk", ""})
    {
        CHECK_FALSE(setMenuSettingValue(settings, "sharpening", value));
    }
    CHECK(menuSettingValue(settings, "sharpening") == "40");
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-sharpening-settings.ini";
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded, error);
    CHECK(loaded->sharpening == 40);
    {
        std::ofstream file(path);
        file << "[video]\nsharpening=250\n";
    }
    const std::optional<GameSettings> bounded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(bounded, error);
    CHECK(bounded->sharpening == 100);
    std::filesystem::remove(path);
}

TEST_CASE("anti-aliasing defaults to 4x on desktop and its sample count validates and persists")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.antialiasing == 4);
    CHECK(menuSettingValue(settings, "antialiasing") == "4x");
    REQUIRE(setMenuSettingValue(settings, "antialiasing", "off"));
    REQUIRE(setMenuSettingValue(settings, "antialiasing", "4x"));
    for (const std::string value : {"8x", "1x", "4X", "on", ""})
    {
        CHECK_FALSE(setMenuSettingValue(settings, "antialiasing", value));
    }
    CHECK(menuSettingValue(settings, "antialiasing") == "4x");
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-antialiasing-settings.ini";
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded, error);
    CHECK(loaded->antialiasing == 4);
    {
        std::ofstream file(path);
        file << "[video]\nantialiasing=16x\n";
    }
    const std::optional<GameSettings> invalid = loadGameSettings(path, error);
    REQUIRE_MESSAGE(invalid, error);
    CHECK(invalid->antialiasing == GameSettings::createDefault().antialiasing);
    {
        std::ofstream file(path);
        file << "[video]\nantialiasing=2X\n";
    }
    const std::optional<GameSettings> twoSamples = loadGameSettings(path, error);
    REQUIRE_MESSAGE(twoSamples, error);
    CHECK(twoSamples->antialiasing == 2);
    std::filesystem::remove(path);
}

TEST_CASE("graphics quality presets match the default profile and report custom mixes")
{
    // Desktop defaults are the high preset (Android defaults are the low preset).
    std::optional<GameSettings> desktop = GameSettings::createDefault();
    CHECK(menuSettingValue(*desktop, "graphics_quality") == "high");
    desktop->ambientOcclusion = false;
    CHECK(menuSettingValue(*desktop, "graphics_quality") == "custom");

    GameSettings settings = *desktop;
    settings.sharpening = 40;
    settings.cinematicGrading = true;
    REQUIRE(setMenuSettingValue(settings, "graphics_quality", "high"));
    CHECK(menuSettingValue(settings, "graphics_quality") == "high");
    CHECK(settings.antialiasing == 4);
    CHECK(settings.ambientOcclusion);
    CHECK(settings.terrainAnisotropy == "8x");
    CHECK(settings.waterReflectionSize == 512);
    CHECK(settings.viewDistance == "default");
    CHECK(settings.sharpening == 40); // Taste options are not part of a preset.
    CHECK(settings.cinematicGrading);
    CHECK(settings.terrainAntiTiling);

    REQUIRE(setMenuSettingValue(settings, "graphics_quality", "medium"));
    CHECK(settings.terrainSubdivision == 4);
    CHECK_FALSE(settings.terrainAntiTiling);
    CHECK(menuSettingValue(settings, "graphics_quality") == "medium");
    settings.terrainAntiTiling = true; // INI-only options count too.
    CHECK(menuSettingValue(settings, "graphics_quality") == "custom");

    REQUIRE(setMenuSettingValue(settings, "graphics_quality", "low"));
    CHECK(settings.terrainSubdivision == 2);
    CHECK_FALSE(settings.terrainAntiTiling);
    CHECK(settings.skyResolutionScale == 0.5f);
    CHECK(menuSettingValue(settings, "graphics_quality") == "low");

    REQUIRE(setMenuSettingValue(settings, "bloom", "true"));
    CHECK(menuSettingValue(settings, "graphics_quality") == "custom");
    REQUIRE(setMenuSettingValue(settings, "graphics_quality", "custom"));
    CHECK(settings.bloom); // Choosing Custom keeps the current mix.
    settings.terrainSubdivision = 4; // INI-only options count too.
    REQUIRE(setMenuSettingValue(settings, "bloom", "false"));
    CHECK(menuSettingValue(settings, "graphics_quality") == "custom");
    CHECK_FALSE(setMenuSettingValue(settings, "graphics_quality", "ultra"));
}

TEST_CASE("party portrait frame defaults on and persists menu changes")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-party-frame-settings.ini";
    std::string error;
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.partyFrame);
    CHECK(menuSettingValue(settings, "party_frame") == "true");

    for (const std::string value : {"false", "true"})
    {
        REQUIRE(setMenuSettingValue(settings, "party_frame", value));
        CHECK(menuSettingValue(settings, "party_frame") == value);
        CHECK_FALSE(setMenuSettingValue(settings, "party_frame", "invalid"));
        CHECK(menuSettingValue(settings, "party_frame") == value);
        REQUIRE(saveGameSettings(path, settings, error));
        const std::optional<GameSettings> loaded = loadGameSettings(path, error);
        REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
        CHECK(loaded->partyFrame == (value == "true"));
    }

    settings.partyFrame = false;
    const std::vector<SettingsEntry> entries = settingsEntriesToSave(settings);
    CHECK(std::find(entries.begin(), entries.end(), SettingsEntry{"gameplay", "party_frame", "false"})
        != entries.end());

    {
        std::ofstream file(path);
        file << "[profile]\nname=desktop\nversion=5\n[gameplay]\nquest_markers=false\nmap_style=painted\n";
    }
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
    CHECK(loaded->partyFrame);
    CHECK_FALSE(loaded->questMarkers);
    CHECK(loaded->paintedMaps);
    CHECK(menuSettingValue(*loaded, "map_style") == "painted");
    CHECK(menuSettingValue(GameSettings::createDefault(), "map_style") == "lines");
    REQUIRE(setMenuSettingValue(settings, "map_style", "painted"));
    const std::vector<SettingsEntry> paintedEntries = settingsEntriesToSave(settings);
    CHECK(std::find(paintedEntries.begin(), paintedEntries.end(), SettingsEntry{"gameplay", "map_style", "painted"})
        != paintedEntries.end());
    std::filesystem::remove(path);
}

TEST_CASE("MMMerge's follower keys default to 0 and 6-9, clash with no other key and are in the bindings menu")
{
    const std::array<std::pair<KeyboardAction, SDL_Scancode>, 5> followerKeys = {{
        {KeyboardAction::FollowerPanel, SDL_SCANCODE_0}, {KeyboardAction::Follower1, SDL_SCANCODE_6},
        {KeyboardAction::Follower2, SDL_SCANCODE_7}, {KeyboardAction::Follower3, SDL_SCANCODE_8},
        {KeyboardAction::Follower4, SDL_SCANCODE_9}}};
    std::ifstream input(std::string(OPENYAMM_SOURCE_DIR) + "/assets_dev/engine/ui/menu/settings_catalog.yml");
    const std::string catalog{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};

    for (const auto &[action, scancode] : followerKeys)
    {
        const KeyboardBindingDefinition &definition = keyboardBindingDefinition(action);
        CAPTURE(definition.iniKey);
        CHECK(definition.implemented);
        CHECK_EQ(definition.defaultBinding.kind, InputBindingKind::Keyboard);
        CHECK_EQ(definition.defaultBinding.scancode, scancode);
        CHECK_NE(catalog.find("- id: " + std::string(definition.iniKey) + "\n"), std::string::npos);

        for (const KeyboardBindingDefinition &other : keyboardBindingDefinitions())
        {
            if (other.action != action)
            {
                CAPTURE(other.iniKey);
                CHECK_FALSE((other.defaultBinding.kind == InputBindingKind::Keyboard
                    && other.defaultBinding.scancode == scancode));
            }
        }
    }
}
