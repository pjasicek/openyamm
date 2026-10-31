#pragma once

#include <cstdint>
#include <initializer_list>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;

// An interface language besides English. engine/localization/<id>/language.yml names it and the code page its text
// is drawn in: windows-1252 (Western European) or windows-1251 (Cyrillic), the byte encodings the legacy faces index.
struct InterfaceLanguage
{
    std::string id;
    std::string name;
    std::string encoding;
};

constexpr const char *EnglishLanguageId = "en";

// A language id fit for settings.ini and a folder name: 1-16 lower-case letters, digits, '-' or '_'.
bool validLanguageId(std::string_view id);

// English, which needs no files, followed by the languages the mounted assets offer, by id.
std::vector<InterfaceLanguage> availableInterfaceLanguages(const AssetFileSystem &assetFileSystem);

// Makes `language` the interface language. Its catalogue is every .tsv file in engine/localization/<language>, such as
// strings.tsv for the interface and game_text.tsv for the game's own text, read in name order (a later file's entry
// wins), and the active world's worlds/<world>/localization/<language>/world_strings.tsv adds entries of its own that
// win over shared ones (a town name read differently in each world). English, or a language without language.yml, clears the catalogue. Call it again
// after the active world changes. A malformed catalogue throws std::runtime_error and keeps the previous one.
//
// A catalogue is UTF-8 tab-separated text: the English text, then its translation, quoted when it spans lines. An
// entry with printf-style values (%s, %d) also translates text assembled from them, such as "%s hits %s for %d damage",
// translating each text value that is itself an entry.
void loadTextCatalogue(const AssetFileSystem &assetFileSystem, const std::string &language);

// The interface language's id, EnglishLanguageId when no catalogue is loaded.
const std::string &interfaceLanguageId();
// Code page of the interface text: windows-1252 for English.
const std::string &interfaceTextEncoding();

// The language's own copy of an asset when it has one: "localization/<language>/" + path, such as the font descriptors
// of faces that draw its alphabet. Otherwise the path itself.
std::string localizedAssetPath(const AssetFileSystem &assetFileSystem, const std::string &path);

// Text as the interface language shows it, in the bytes of its code page: the catalogue's translation, or the text
// itself when the catalogue has none (or for English). Draw and measure code calls it on whole texts, before wrapping or
// shortening them, since only whole texts are catalogue entries. With OPENYAMM_UNTRANSLATED_TEXT_LOG=<file> set, the
// texts a loaded catalogue lacks are appended to that file once each, for translators.
std::string_view localizeDisplayText(std::string_view text);

// Fills an English printf-style template ("%s the %s", "%dh") through the template's translation, localizing each %s
// value on its own. For text that catalogue patterns cannot match: templates with fewer than four letters around their
// values, or around a typed name.
std::string formatDisplayText(std::string_view format, std::initializer_list<std::string_view> values);

bool hasTextCatalogue();

// The Unicode character a byte of a code page stands for; 0 for none (controls and unassigned bytes).
uint32_t codePageCharacter(const std::string &encoding, uint8_t byte);

// UTF-8 text in the bytes of a code page; std::runtime_error when the text is not UTF-8 or has a character the code
// page lacks.
std::string encodeCodePageText(std::string_view utf8Text, const std::string &encoding);

// Text the player types (UTF-8) in the bytes of the interface language's code page, without the characters it lacks.
std::string encodeTypedText(std::string_view utf8Text);

// Text in the bytes of a code page with its capitals lowercased: ASCII and the code page's own letters (Cyrillic in
// windows-1251, the accented Latin letters in windows-1252).
std::string lowercaseCodePageText(std::string_view text, const std::string &encoding);
}
