#pragma once

#include "engine/AssetFileSystem.h"
#include "game/maps/OutdoorSceneYml.h"

#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Editor
{
struct Mm9ResolvedModelInstanceActorSource
{
    struct ActorSoundReference
    {
        std::string sourcePath;
    };

    struct ActorRow
    {
        std::string table;
        std::string row;
        std::string number;
        std::string monsterName;
        std::string typePicture;
        std::string baseName;
        std::string level;
        std::string hitPoints;
        std::string armorClass;
        std::string experience;
        std::string speed;
        std::string treasureType;
        std::string quest;
        std::string fly;
        std::string move;
        std::string walkVelocity;
        std::string runVelocity;
        std::string flyVelocity;
        std::string lungeVelocity;
        std::string attackReach;
        std::string attackRange;
        std::string recovery;
        std::string targetPreference;
        std::string bonus;
        std::string alertRadius;
        std::string accuracy;
        std::string scriptName;
        std::string footSound;
        std::string footRadius;
        std::string transparent;
        std::string headTurn;
        std::string special;
        std::string scale;
        std::string evadeChance;
        std::string strafeAttackPct;
        std::string isMonster;
        std::string hostilityGroup;
        std::string treasureLevel;
        std::string voiceRadius;
        std::vector<ActorSoundReference> footSoundReferences;
    };

    std::string variantId;
    std::string sourceModel;
    std::string sourceSkin;
    ActorRow actorRow;
    bool inferredFromActorClass = false;
};

struct Mm9ModelInstanceActorSourceLookup
{
    struct Candidate
    {
        std::string id;
        Mm9ResolvedModelInstanceActorSource source;
    };

    std::unordered_map<std::string, std::vector<Candidate>> sourceByActorKey;
    std::unordered_map<std::string, std::vector<Candidate>> sourceBySourceModelAndActorKey;
    std::unordered_map<std::string, std::vector<Candidate>> sourceByTypePictureKey;
};

std::optional<Mm9ModelInstanceActorSourceLookup> loadMm9ModelInstanceActorSourceLookup(
    const Engine::AssetFileSystem &assetFileSystem);
const Mm9ModelInstanceActorSourceLookup *cachedMm9ModelInstanceActorSourceLookup(
    const Engine::AssetFileSystem &assetFileSystem);

Mm9ResolvedModelInstanceActorSource resolveMm9ModelInstanceActorSource(
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup);

bool canResolveMm9ModelInstanceActorSource(
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup);

std::string normalizeMm9ModelInstanceVirtualPath(std::string value);
std::string normalizeMm9ModelInstanceImagePath(std::string value);
bool mm9ActorFootSoundRequiresResolution(const std::string &footSound);
std::vector<Mm9ResolvedModelInstanceActorSource::ActorSoundReference> resolveMm9ActorFootSoundReferences(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &footSound);
std::vector<std::string> splitMm9ModelInstanceSourceSkins(const std::string &sourceSkin);
std::vector<std::string> splitMm9ModelInstanceSourceSkinImages(const std::string &sourceSkin);
std::string mm9ModelInstanceActorVariantAssetPath(
    const std::string &sourceModel,
    const std::string &sourceSkin);
}
