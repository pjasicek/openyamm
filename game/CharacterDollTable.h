#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct CharacterDollTypeEntry
{
    uint32_t id = 0;
    bool canEquipBow = false;
    bool canEquipArmor = false;
    bool canEquipHelm = false;
    bool canEquipBelt = false;
    bool canEquipBoots = false;
    bool canEquipCloak = false;
    bool canEquipWeapon = false;
    int rightHandOpenX = 0;
    int rightHandOpenY = 0;
    int rightHandClosedX = 0;
    int rightHandClosedY = 0;
    int rightHandFingersX = 0;
    int rightHandFingersY = 0;
    int leftHandOpenX = 0;
    int leftHandOpenY = 0;
    int leftHandClosedX = 0;
    int leftHandClosedY = 0;
    int leftHandFingersX = 0;
    int leftHandFingersY = 0;
    int offHandOffsetX = 0;
    int offHandOffsetY = 0;
    int mainHandOffsetX = 0;
    int mainHandOffsetY = 0;
    int bowOffsetX = 0;
    int bowOffsetY = 0;
    int shieldX = 0;
    int shieldY = 0;
};

struct CharacterDollEntry
{
    uint32_t id = 0;
    uint32_t dollTypeId = 0;
    uint32_t defaultClassId = 0;
    uint32_t defaultVoiceId = 0;
    uint32_t defaultSex = 0;
    bool availableAtStart = false;
    int bodyOffsetX = 0;
    int bodyOffsetY = 0;
    std::string backgroundAsset;
    std::string bodyAsset;
    std::string headAsset;
    std::string leftHandClosedAsset;
    std::string leftHandHoldAsset;
    std::string leftHandOpenAsset;
    std::string rightHandFingersAsset;
    std::string rightHandOpenAsset;
    std::string rightHandHoldAsset;
    std::string facePicturesPrefix;
    uint32_t npcPictureId = 0;
    int32_t raceId = -1;
};

class CharacterDollTable
{
public:
    bool loadCharacterRows(const std::vector<std::vector<std::string>> &rows);
    bool loadDollTypeRows(const std::vector<std::vector<std::string>> &rows);

    const CharacterDollEntry *getCharacter(uint32_t characterId) const;
    const CharacterDollTypeEntry *getDollType(uint32_t dollTypeId) const;

private:
    std::unordered_map<uint32_t, CharacterDollEntry> m_characterEntries;
    std::unordered_map<uint32_t, CharacterDollTypeEntry> m_dollTypeEntries;
};
}
