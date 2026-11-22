#include "game/coop/CoopCodec.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game::CoopCodec
{
namespace
{
constexpr size_t MaxNameLength = 256;
constexpr size_t MaxSoundNameLength = 128;
constexpr size_t MaxListLength = 64;
// A Lloyd's Beacon's picture of where it was set.
constexpr size_t MaxPreviewBytes = 4u * 1024u * 1024u;

void writeVec3(Engine::ByteWriter &writer, const bx::Vec3 &value)
{
    writer.f32(value.x);
    writer.f32(value.y);
    writer.f32(value.z);
}

bx::Vec3 readVec3(Engine::ByteReader &reader)
{
    const float x = reader.f32();
    const float y = reader.f32();
    const float z = reader.f32();

    if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z))
    {
        reader.fail();
    }

    return {x, y, z};
}

float readFinite(Engine::ByteReader &reader)
{
    const float value = reader.f32();

    if (!std::isfinite(value))
    {
        reader.fail();
        return 0.0f;
    }

    return value;
}

void writeIndex(Engine::ByteWriter &writer, size_t index)
{
    // GameplayInvalidWorldIndex travels as all ones.
    writer.u32(index == GameplayInvalidWorldIndex ? 0xFFFFFFFFu : uint32_t(index));
}

size_t readIndex(Engine::ByteReader &reader)
{
    const uint32_t index = reader.u32();
    return index == 0xFFFFFFFFu ? GameplayInvalidWorldIndex : size_t(index);
}

template <typename Enum>
Enum readEnum(Engine::ByteReader &reader, Enum last)
{
    const uint8_t raw = reader.u8();

    if (raw > uint8_t(last))
    {
        reader.fail();
        return Enum{};
    }

    return Enum(raw);
}

template <typename T, typename Write>
void writeOptional(Engine::ByteWriter &writer, const std::optional<T> &value, const Write &write)
{
    writer.boolean(value.has_value());

    if (value)
    {
        write(*value);
    }
}
}

void writeBody(Engine::ByteWriter &writer, const GameplayPlayerBody &body)
{
    writer.f32(body.x);
    writer.f32(body.y);
    writer.f32(body.footZ);
    writer.f32(body.yawRadians);
    writer.boolean(body.flying);
}

GameplayPlayerBody readBody(Engine::ByteReader &reader)
{
    GameplayPlayerBody body;
    body.x = reader.f32();
    body.y = reader.f32();
    body.footZ = reader.f32();
    body.yawRadians = reader.f32();
    body.flying = reader.boolean();
    return body;
}

bool finiteBody(const GameplayPlayerBody &body)
{
    return std::isfinite(body.x) && std::isfinite(body.y) && std::isfinite(body.footZ)
        && std::isfinite(body.yawRadians);
}

void writePose(Engine::ByteWriter &writer, const ReplicaActorPose &pose)
{
    writer.u16(pose.actorIndex);
    writer.f32(pose.x);
    writer.f32(pose.y);
    writer.f32(pose.z);
    writer.f32(pose.yawRadians);
    writer.f32(pose.velocityX);
    writer.f32(pose.velocityY);
    writer.f32(pose.velocityZ);
    writer.f32(pose.intendedSpeed);
    writer.f32(pose.animationTimeTicks);
    writer.f32(pose.actionSeconds);
    writer.f32(pose.skirmishSeconds);
    writer.i32(pose.hp);
    writer.u8(pose.animation);
    writer.u8(pose.aiState);
    writer.u8(pose.attackAbility);
    writer.u8(pose.skirmishPhase);
    writer.u8(pose.flags);
}

ReplicaActorPose readPose(Engine::ByteReader &reader)
{
    ReplicaActorPose pose;
    pose.actorIndex = reader.u16();
    pose.x = reader.f32();
    pose.y = reader.f32();
    pose.z = reader.f32();
    pose.yawRadians = reader.f32();
    pose.velocityX = reader.f32();
    pose.velocityY = reader.f32();
    pose.velocityZ = reader.f32();
    pose.intendedSpeed = reader.f32();
    pose.animationTimeTicks = reader.f32();
    pose.actionSeconds = reader.f32();
    pose.skirmishSeconds = reader.f32();
    pose.hp = reader.i32();
    pose.animation = reader.u8();
    pose.aiState = reader.u8();
    pose.attackAbility = reader.u8();
    pose.skirmishPhase = reader.u8();
    pose.flags = reader.u8();
    return pose;
}

bool finitePose(const ReplicaActorPose &pose)
{
    return std::isfinite(pose.x) && std::isfinite(pose.y) && std::isfinite(pose.z) && std::isfinite(pose.yawRadians)
        && std::isfinite(pose.velocityX) && std::isfinite(pose.velocityY) && std::isfinite(pose.velocityZ)
        && std::isfinite(pose.intendedSpeed) && std::isfinite(pose.animationTimeTicks)
        && std::isfinite(pose.actionSeconds) && std::isfinite(pose.skirmishSeconds);
}

void writeSounds(Engine::ByteWriter &writer, const std::vector<EventRuntimeState::PendingSound> &sounds)
{
    const size_t count = std::min<size_t>(sounds.size(), 255);
    writer.u8(uint8_t(count));

    for (size_t index = 0; index < count; ++index)
    {
        const EventRuntimeState::PendingSound &sound = sounds[index];
        writer.u8(uint8_t(sound.kind));
        writer.u8(uint8_t(sound.soundScope));
        writer.u32(sound.soundId);
        writer.text(sound.soundName, MaxSoundNameLength);
        writer.text(sound.fallbackSoundName, MaxSoundNameLength);
        writer.u64(sound.key);
        writer.boolean(sound.actorIndex.has_value());
        writer.u32(sound.actorIndex ? uint32_t(*sound.actorIndex) : 0);
        writer.f32(sound.pitch);
        writer.i32(sound.x);
        writer.i32(sound.y);
        writer.i32(sound.z);
        writer.boolean(sound.positional);
        writer.boolean(sound.hasExplicitZ);
    }
}

bool readSounds(Engine::ByteReader &reader, std::vector<EventRuntimeState::PendingSound> &sounds)
{
    const size_t count = reader.u8();

    for (size_t index = 0; index < count && reader.ok(); ++index)
    {
        EventRuntimeState::PendingSound sound;
        const uint8_t kind = reader.u8();
        const uint8_t scope = reader.u8();
        sound.soundId = reader.u32();
        sound.soundName = reader.text(MaxSoundNameLength);
        sound.fallbackSoundName = reader.text(MaxSoundNameLength);
        sound.key = reader.u64();
        const bool hasActor = reader.boolean();
        const uint32_t actorIndex = reader.u32();
        sound.pitch = reader.f32();
        sound.x = reader.i32();
        sound.y = reader.i32();
        sound.z = reader.i32();
        sound.positional = reader.boolean();
        sound.hasExplicitZ = reader.boolean();

        if (kind > uint8_t(EventRuntimeState::PendingSound::Kind::StopKeyed) || scope > uint8_t(SoundScope::World)
            || !std::isfinite(sound.pitch))
        {
            return false;
        }

        sound.kind = EventRuntimeState::PendingSound::Kind(kind);
        sound.soundScope = SoundScope(scope);

        if (hasActor)
        {
            sound.actorIndex = actorIndex;
        }

        sounds.push_back(std::move(sound));
    }

    return reader.ok();
}

void writeWorldHit(Engine::ByteWriter &writer, const GameplayWorldHit &hit)
{
    writer.boolean(hit.hasHit);
    writer.u8(uint8_t(hit.kind));
    writeOptional(writer, hit.actor, [&](const GameplayActorTargetHit &actor)
    {
        writeIndex(writer, actor.actorIndex);
        writer.text(actor.displayName, MaxNameLength);
        writer.boolean(actor.isFriendly);
        writer.i16(actor.npcId);
        writer.u32(actor.actorGroup);
        writeVec3(writer, actor.hitPoint);
        writer.f32(actor.distance);
    });
    writeOptional(writer, hit.worldItem, [&](const GameplayWorldItemTargetHit &worldItem)
    {
        writeIndex(writer, worldItem.worldItemIndex);
        writer.text(worldItem.displayName, MaxNameLength);
        writer.u16(worldItem.objectDescriptionId);
        writer.u16(worldItem.objectSpriteId);
        writeVec3(writer, worldItem.hitPoint);
        writer.f32(worldItem.distance);
        writer.u32(worldItem.missingGroundModelItemId);
    });
    writeOptional(writer, hit.container, [&](const GameplayContainerTargetHit &container)
    {
        writer.u8(uint8_t(container.sourceKind));
        writeIndex(writer, container.sourceIndex);
        writer.text(container.displayName, MaxNameLength);
        writer.f32(container.distance);
    });
    writeOptional(writer, hit.eventTarget, [&](const GameplayEventTargetHit &target)
    {
        writer.u8(uint8_t(target.targetKind));
        writeIndex(writer, target.targetIndex);
        writeIndex(writer, target.secondaryIndex);
        writer.u16(target.eventIdPrimary);
        writer.u16(target.eventIdSecondary);
        writer.u16(target.triggeredEventId);
        writer.u16(target.trigger);
        writer.u16(target.variablePrimary);
        writer.u16(target.variableSecondary);
        writer.u16(target.specialTrigger);
        writer.u32(target.attributes);
        writer.text(target.name, MaxNameLength);
        writer.u16(target.nameEventId);
        writer.boolean(target.nameEventIsLocal);
        writer.u8(uint8_t(std::min(target.openedChestIds.size(), MaxListLength)));

        for (size_t index = 0; index < target.openedChestIds.size() && index < MaxListLength; ++index)
        {
            writer.u32(target.openedChestIds[index]);
        }

        // The context action's description is for the hover text of the game that picked; the host needs none of it.
        writeVec3(writer, target.hitPoint);
        writer.f32(target.distance);
        writer.boolean(target.hintOnlyEvent);
    });
    writeOptional(writer, hit.object, [&](const GameplayObjectTargetHit &object)
    {
        writeIndex(writer, object.objectIndex);
        writer.u16(object.objectDescriptionId);
        writer.u16(object.objectSpriteId);
        writer.i32(object.spellId);
        writeVec3(writer, object.hitPoint);
        writer.f32(object.distance);
    });
    writeOptional(writer, hit.ground, [&](const GameplayGroundTargetHit &ground)
    {
        writeVec3(writer, ground.worldPoint);
        writer.f32(ground.distance);
        writer.boolean(ground.isValid);
    });
}

GameplayWorldHit readWorldHit(Engine::ByteReader &reader)
{
    GameplayWorldHit hit;
    hit.hasHit = reader.boolean();
    hit.kind = readEnum(reader, GameplayWorldHitKind::Ground);

    if (reader.boolean())
    {
        GameplayActorTargetHit actor;
        actor.actorIndex = readIndex(reader);
        actor.displayName = reader.text(MaxNameLength);
        actor.isFriendly = reader.boolean();
        actor.npcId = reader.i16();
        actor.actorGroup = reader.u32();
        actor.hitPoint = readVec3(reader);
        actor.distance = readFinite(reader);
        hit.actor = std::move(actor);
    }

    if (reader.boolean())
    {
        GameplayWorldItemTargetHit worldItem;
        worldItem.worldItemIndex = readIndex(reader);
        worldItem.displayName = reader.text(MaxNameLength);
        worldItem.objectDescriptionId = reader.u16();
        worldItem.objectSpriteId = reader.u16();
        worldItem.hitPoint = readVec3(reader);
        worldItem.distance = readFinite(reader);
        worldItem.missingGroundModelItemId = reader.u32();
        hit.worldItem = std::move(worldItem);
    }

    if (reader.boolean())
    {
        GameplayContainerTargetHit container;
        container.sourceKind = readEnum(reader, GameplayWorldContainerSourceKind::Corpse);
        container.sourceIndex = readIndex(reader);
        container.displayName = reader.text(MaxNameLength);
        container.distance = readFinite(reader);
        hit.container = std::move(container);
    }

    if (reader.boolean())
    {
        GameplayEventTargetHit target;
        target.targetKind = readEnum(reader, GameplayWorldEventTargetKind::Mechanism);
        target.targetIndex = readIndex(reader);
        target.secondaryIndex = readIndex(reader);
        target.eventIdPrimary = reader.u16();
        target.eventIdSecondary = reader.u16();
        target.triggeredEventId = reader.u16();
        target.trigger = reader.u16();
        target.variablePrimary = reader.u16();
        target.variableSecondary = reader.u16();
        target.specialTrigger = reader.u16();
        target.attributes = reader.u32();
        target.name = reader.text(MaxNameLength);
        target.nameEventId = reader.u16();
        target.nameEventIsLocal = reader.boolean();
        const size_t chestCount = reader.u8();

        if (chestCount > MaxListLength)
        {
            reader.fail();
        }

        for (size_t index = 0; index < chestCount && reader.ok(); ++index)
        {
            target.openedChestIds.push_back(reader.u32());
        }

        target.hitPoint = readVec3(reader);
        target.distance = readFinite(reader);
        target.hintOnlyEvent = reader.boolean();
        hit.eventTarget = std::move(target);
    }

    if (reader.boolean())
    {
        GameplayObjectTargetHit object;
        object.objectIndex = readIndex(reader);
        object.objectDescriptionId = reader.u16();
        object.objectSpriteId = reader.u16();
        object.spellId = reader.i32();
        object.hitPoint = readVec3(reader);
        object.distance = readFinite(reader);
        hit.object = std::move(object);
    }

    if (reader.boolean())
    {
        GameplayGroundTargetHit ground;
        ground.worldPoint = readVec3(reader);
        ground.distance = readFinite(reader);
        ground.isValid = reader.boolean();
        hit.ground = std::move(ground);
    }

    return hit;
}

void writeSpellCastRequest(
    Engine::ByteWriter &writer,
    const PartySpellCastRequest &request,
    std::optional<PlayerId> targetPlayer)
{
    writer.u32(uint32_t(request.casterMemberIndex));
    writer.u32(request.spellId);
    writer.boolean(request.quickCast);
    writeOptional(writer, request.targetActorIndex, [&](size_t index) { writer.u32(uint32_t(index)); });
    writeOptional(writer, request.targetCharacterIndex, [&](size_t index) { writer.u32(uint32_t(index)); });
    writeOptional(writer, targetPlayer, [&](PlayerId player) { writer.u8(player); });
    writeOptional(writer, request.targetItemMemberIndex, [&](size_t index) { writer.u32(uint32_t(index)); });
    writeOptional(writer, request.targetInventoryGridX, [&](uint8_t cell) { writer.u8(cell); });
    writeOptional(writer, request.targetInventoryGridY, [&](uint8_t cell) { writer.u8(cell); });
    writeOptional(writer, request.targetEquipmentSlot, [&](EquipmentSlot slot) { writer.u8(uint8_t(slot)); });
    writer.boolean(request.hasTargetPoint);
    writer.f32(request.targetX);
    writer.f32(request.targetY);
    writer.f32(request.targetZ);
    writeOptional(writer, request.telekinesisTarget, [&](const GameplayWorldHit &hit) { writeWorldHit(writer, hit); });
    writeOptional(writer, request.targetWorldHit, [&](const GameplayWorldHit &hit) { writeWorldHit(writer, hit); });
    writer.u32(request.skillLevelOverride);
    writer.u8(uint8_t(request.skillMasteryOverride));
    writer.boolean(request.bypassRequiredMastery);
    writer.boolean(request.fromScroll);
    writer.boolean(request.spendMana);
    writer.boolean(request.applyRecovery);
    writer.boolean(request.hasViewTransform);
    writer.f32(request.viewX);
    writer.f32(request.viewY);
    writer.f32(request.viewZ);
    writer.f32(request.viewYawRadians);
    writer.f32(request.viewPitchRadians);
    writer.f32(request.viewAspectRatio);
    writeOptional(writer, request.handScreenPoint, [&](const std::array<float, 2> &point)
    {
        writer.f32(point[0]);
        writer.f32(point[1]);
    });
    writer.u8(uint8_t(request.utilityAction));
    writer.text(request.utilityActionId, MaxNameLength);
    writer.u8(request.utilitySlotIndex);
    writer.boolean(request.hasUtilityMapMove);
    writer.i32(request.utilityMapMoveX);
    writer.i32(request.utilityMapMoveY);
    writer.i32(request.utilityMapMoveZ);
    writer.text(request.utilityMapMoveMapName, MaxNameLength);
    writeOptional(writer, request.utilityMapMoveDirectionDegrees, [&](int32_t degrees) { writer.i32(degrees); });
    writer.boolean(request.utilityMapMoveUseMapStartPosition);
    writer.boolean(request.utilityMapMoveUseFullscreenLoading);
    writer.text(request.utilityStatusText, MaxNameLength);
    writer.i32(request.utilityPreviewWidth);
    writer.i32(request.utilityPreviewHeight);
    writer.block(request.utilityPreviewPixelsBgra);
}

PartySpellCastRequest readSpellCastRequest(Engine::ByteReader &reader, std::optional<PlayerId> &targetPlayer)
{
    PartySpellCastRequest request;
    targetPlayer.reset();
    request.casterMemberIndex = reader.u32();
    request.spellId = reader.u32();
    request.quickCast = reader.boolean();

    if (reader.boolean())
    {
        request.targetActorIndex = reader.u32();
    }

    if (reader.boolean())
    {
        request.targetCharacterIndex = reader.u32();
    }

    if (reader.boolean())
    {
        targetPlayer = reader.u8();
    }

    if (reader.boolean())
    {
        request.targetItemMemberIndex = reader.u32();
    }

    if (reader.boolean())
    {
        request.targetInventoryGridX = reader.u8();
    }

    if (reader.boolean())
    {
        request.targetInventoryGridY = reader.u8();
    }

    if (reader.boolean())
    {
        request.targetEquipmentSlot = readEnum(reader, EquipmentSlot::Ring6);
    }

    request.hasTargetPoint = reader.boolean();
    request.targetX = readFinite(reader);
    request.targetY = readFinite(reader);
    request.targetZ = readFinite(reader);

    if (reader.boolean())
    {
        request.telekinesisTarget = readWorldHit(reader);
    }

    if (reader.boolean())
    {
        request.targetWorldHit = readWorldHit(reader);
    }

    request.skillLevelOverride = reader.u32();
    request.skillMasteryOverride = readEnum(reader, SkillMastery::Grandmaster);
    request.bypassRequiredMastery = reader.boolean();
    request.fromScroll = reader.boolean();
    request.spendMana = reader.boolean();
    request.applyRecovery = reader.boolean();
    request.hasViewTransform = reader.boolean();
    request.viewX = readFinite(reader);
    request.viewY = readFinite(reader);
    request.viewZ = readFinite(reader);
    request.viewYawRadians = readFinite(reader);
    request.viewPitchRadians = readFinite(reader);
    request.viewAspectRatio = readFinite(reader);

    if (reader.boolean())
    {
        const float x = readFinite(reader);
        const float y = readFinite(reader);
        request.handScreenPoint = std::array<float, 2>{x, y};
    }

    request.utilityAction = readEnum(reader, PartySpellUtilityActionKind::LloydsBeaconRecall);
    request.utilityActionId = reader.text(MaxNameLength);
    request.utilitySlotIndex = reader.u8();
    request.hasUtilityMapMove = reader.boolean();
    request.utilityMapMoveX = reader.i32();
    request.utilityMapMoveY = reader.i32();
    request.utilityMapMoveZ = reader.i32();
    request.utilityMapMoveMapName = reader.text(MaxNameLength);

    if (reader.boolean())
    {
        request.utilityMapMoveDirectionDegrees = reader.i32();
    }

    request.utilityMapMoveUseMapStartPosition = reader.boolean();
    request.utilityMapMoveUseFullscreenLoading = reader.boolean();
    request.utilityStatusText = reader.text(MaxNameLength);
    request.utilityPreviewWidth = reader.i32();
    request.utilityPreviewHeight = reader.i32();
    request.utilityPreviewPixelsBgra = reader.block(MaxPreviewBytes);
    return request;
}
}
