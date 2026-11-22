#include "game/coop/ReplicaWorldCalls.h"

#include "engine/net/ByteStream.h"
#include "game/maps/SaveSections.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game::ReplicaWorldCalls
{
namespace
{
enum class Call : uint8_t
{
    MeleeDamage = 1,
    MeleeEffects = 2,
    MeleeBModelDamage = 3,
    MeleeEntityDamage = 4,
    AttackProjectile = 5,
    AttackSpell = 6,
    SpellProjectile = 7,
    AttackResult = 8,
    StunActor = 9,
    DebuffActor = 10,
    HealActor = 11,
    ReflectedDamage = 12,
    PushActor = 13,
    SuspendActorShield = 14,
    RestoreActorShield = 15,
    RevealActorsAround = 16,
    ScareNearbyPeasants = 17,
    DropHeldItem = 18,
    ActorHitMarks = 19,
};

// More than any blow deals; a call beyond it is not a blow.
constexpr int MaximumDamage = 100000000;
// How much further than the party's reach a guest's blow may land: its player stood where its own game had it.
constexpr float ReachMargin = 384.0f;

Engine::ByteWriter begin(Call call)
{
    Engine::ByteWriter writer;
    writer.u8(uint8_t(call));
    return writer;
}

void writePoint(Engine::ByteWriter &writer, const GameplayWorldPoint &point)
{
    writer.f32(point.x);
    writer.f32(point.y);
    writer.f32(point.z);
}

GameplayWorldPoint readPoint(Engine::ByteReader &reader)
{
    GameplayWorldPoint point;
    point.x = reader.f32();
    point.y = reader.f32();
    point.z = reader.f32();
    return point;
}

bool finitePoint(const GameplayWorldPoint &point)
{
    return std::isfinite(point.x) && std::isfinite(point.y) && std::isfinite(point.z);
}

void writeShieldModifiers(Engine::ByteWriter &writer, const ShieldHitModifiers &modifiers)
{
    writer.f32(modifiers.shieldDamageMultiplier);
    writer.f32(modifiers.exposedMultiplier);
    writer.boolean(modifiers.cleave);
    writer.f32(modifiers.energyShare);
}

// A number that is no number fails the reader, so that the call is not run with it.
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

ShieldHitModifiers readShieldModifiers(Engine::ByteReader &reader)
{
    ShieldHitModifiers modifiers;
    modifiers.shieldDamageMultiplier = readFinite(reader);
    modifiers.exposedMultiplier = readFinite(reader);
    modifiers.cleave = reader.boolean();
    modifiers.energyShare = readFinite(reader);
    return modifiers;
}

void writeOptionalIndex(Engine::ByteWriter &writer, const std::optional<size_t> &index)
{
    writer.boolean(index.has_value());
    writer.u32(index ? uint32_t(*index) : 0);
}

std::optional<size_t> readOptionalIndex(Engine::ByteReader &reader)
{
    const bool present = reader.boolean();
    const uint32_t index = reader.u32();
    return present ? std::optional<size_t>(index) : std::nullopt;
}

void writeOptionalSeconds(Engine::ByteWriter &writer, const std::optional<float> &seconds)
{
    writer.boolean(seconds.has_value());
    writer.f32(seconds.value_or(0.0f));
}

std::optional<float> readOptionalSeconds(Engine::ByteReader &reader)
{
    const bool present = reader.boolean();
    const float seconds = readFinite(reader);
    return present ? std::optional<float>(seconds) : std::nullopt;
}

// A tier, a damage type or a debuff outside its list is not one.
template <typename Enum>
bool readEnum(Engine::ByteReader &reader, Enum last, Enum &value)
{
    const uint8_t raw = reader.u8();

    if (raw > uint8_t(last))
    {
        reader.fail();
        return false;
    }

    value = Enum(raw);
    return true;
}

bool saneDamage(int damage)
{
    return damage >= 0 && damage <= MaximumDamage;
}

// Whether the acting party stands near enough to the monster for a blow of its own.
bool actorInBlowReach(const IGameplayWorldRuntime &worldRuntime, size_t actorIndex)
{
    GameplayRuntimeActorState actor;

    if (!worldRuntime.actorRuntimeState(actorIndex, actor))
    {
        return false;
    }

    const float deltaX = actor.preciseX - worldRuntime.partyX();
    const float deltaY = actor.preciseY - worldRuntime.partyY();
    const float deltaZ = actor.preciseZ - worldRuntime.partyFootZ();
    const float reach = worldRuntime.partyHitReach() + float(actor.radius) + float(actor.height) + ReachMargin;
    return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ <= reach * reach;
}
}

std::vector<uint8_t> meleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source,
    ShieldAttackTier shieldTier,
    const ShieldHitModifiers &shieldModifiers,
    bool critical,
    bool hitReaction)
{
    Engine::ByteWriter writer = begin(Call::MeleeDamage);
    writer.u32(uint32_t(actorIndex));
    writer.i32(damage);
    writePoint(writer, source);
    writer.u8(uint8_t(shieldTier));
    writeShieldModifiers(writer, shieldModifiers);
    writer.boolean(critical);
    writer.boolean(hitReaction);
    return writer.take();
}

std::vector<uint8_t> meleeEffects(
    size_t actorIndex,
    const CharacterAttackResult &attack,
    const GameplayWorldPoint &source)
{
    // What the world reads of the attack for its effects on the monster.
    Engine::ByteWriter writer = begin(Call::MeleeEffects);
    writer.u32(uint32_t(actorIndex));
    writer.u32(attack.skillLevel);
    writer.boolean(attack.stunTarget);
    writeOptionalSeconds(writer, attack.stunSeconds);
    writer.boolean(attack.paralyzeTarget);
    writeOptionalSeconds(writer, attack.paralyzeSeconds);
    writer.boolean(attack.fearTarget);
    writer.boolean(attack.enrageTarget);
    writer.boolean(attack.halveTargetArmorClass);
    writePoint(writer, source);
    return writer.take();
}

std::vector<uint8_t> meleeBModelDamage(size_t bModelIndex, int damage)
{
    Engine::ByteWriter writer = begin(Call::MeleeBModelDamage);
    writer.u32(uint32_t(bModelIndex));
    writer.i32(damage);
    return writer.take();
}

std::vector<uint8_t> meleeEntityDamage(size_t entityIndex, int damage)
{
    Engine::ByteWriter writer = begin(Call::MeleeEntityDamage);
    writer.u32(uint32_t(entityIndex));
    writer.i32(damage);
    return writer.take();
}

std::vector<uint8_t> attackProjectile(const GameplayPartyAttackProjectileRequest &request)
{
    Engine::ByteWriter writer = begin(Call::AttackProjectile);
    writer.u32(uint32_t(request.sourcePartyMemberIndex));
    writer.u32(request.objectId);
    writer.u32(request.impactObjectId);
    writer.u32(request.impactSoundId);
    writer.i32(request.damage);
    writer.i32(request.attackBonus);
    writer.boolean(request.useActorHitChance);
    writer.u8(uint8_t(request.damageType));
    writer.u8(uint8_t(request.shieldTier));
    writeShieldModifiers(writer, request.shieldModifiers);
    writer.boolean(request.weakerOfPhysicalAndFire);
    writer.f32(request.explosionRadius);
    writer.i32(request.blastMinimumDamage);
    writer.i32(request.blastMaximumDamage);
    writePoint(writer, request.source);
    writePoint(writer, request.target);
    writeOptionalIndex(writer, request.targetActorIndex);
    writer.boolean(request.homing);
    writer.boolean(request.critical);
    writer.u8(request.chainCount);
    writer.f32(request.chainShare);
    writer.f32(request.chainRadius);
    writer.boolean(request.quietBlast);
    return writer.take();
}

std::vector<uint8_t> attackSpell(const GameplayPartyAttackSpellRequest &request)
{
    Engine::ByteWriter writer = begin(Call::AttackSpell);
    writer.u32(uint32_t(request.sourcePartyMemberIndex));
    writer.u32(request.spellId);
    writer.u32(request.skillLevel);
    writer.u32(request.skillMastery);
    writer.i32(request.damage);
    writer.i32(request.attackBonus);
    writer.boolean(request.useActorHitChance);
    writePoint(writer, request.source);
    writePoint(writer, request.target);
    return writer.take();
}

std::vector<uint8_t> spellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    Engine::ByteWriter writer = begin(Call::SpellProjectile);
    writer.u32(request.casterMemberIndex);
    writer.u32(request.spellId);
    writer.u32(request.skillLevel);
    writer.u8(uint8_t(request.skillMastery));
    writer.i32(request.damage);
    writer.u8(uint8_t(request.damageType));
    writePoint(writer, GameplayWorldPoint{request.sourceX, request.sourceY, request.sourceZ});
    writePoint(writer, GameplayWorldPoint{request.targetX, request.targetY, request.targetZ});
    writer.u32(request.effectSoundIdOverride);
    writer.u32(request.impactSoundIdOverride);
    writeOptionalIndex(writer, request.targetActorIndex);
    writer.boolean(request.critical);
    writer.u8(request.chainCount);
    writer.f32(request.chainShare);
    writer.f32(request.chainRadius);
    return writer.take();
}

std::vector<uint8_t> attackResult(std::optional<size_t> actorIndex, bool attacked, bool actionPerformed, bool missed)
{
    Engine::ByteWriter writer = begin(Call::AttackResult);
    writeOptionalIndex(writer, actorIndex);
    writer.boolean(attacked);
    writer.boolean(actionPerformed);
    writer.boolean(missed);
    return writer.take();
}

std::vector<uint8_t> stunActor(size_t actorIndex, float seconds)
{
    Engine::ByteWriter writer = begin(Call::StunActor);
    writer.u32(uint32_t(actorIndex));
    writer.f32(seconds);
    return writer.take();
}

std::vector<uint8_t> debuffActor(size_t actorIndex, GameplayActorHitDebuff debuff, float seconds, float power)
{
    Engine::ByteWriter writer = begin(Call::DebuffActor);
    writer.u32(uint32_t(actorIndex));
    writer.u8(uint8_t(debuff));
    writer.f32(seconds);
    writer.f32(power);
    return writer.take();
}

std::vector<uint8_t> healActor(size_t actorIndex, int amount)
{
    Engine::ByteWriter writer = begin(Call::HealActor);
    writer.u32(uint32_t(actorIndex));
    writer.i32(amount);
    return writer.take();
}

std::vector<uint8_t> reflectedDamage(uint32_t actorId, int damage, CombatDamageType damageType, uint32_t memberIndex)
{
    Engine::ByteWriter writer = begin(Call::ReflectedDamage);
    writer.u32(actorId);
    writer.i32(damage);
    writer.u8(uint8_t(damageType));
    writer.u32(memberIndex);
    return writer.take();
}

std::vector<uint8_t> pushActor(size_t actorIndex, float directionX, float directionY, float distance)
{
    Engine::ByteWriter writer = begin(Call::PushActor);
    writer.u32(uint32_t(actorIndex));
    writer.f32(directionX);
    writer.f32(directionY);
    writer.f32(distance);
    return writer.take();
}

std::vector<uint8_t> suspendActorShield(size_t actorIndex, float seconds)
{
    Engine::ByteWriter writer = begin(Call::SuspendActorShield);
    writer.u32(uint32_t(actorIndex));
    writer.f32(seconds);
    return writer.take();
}

std::vector<uint8_t> actorHitMarks(size_t actorIndex, const ActorHitMarks &marks)
{
    Engine::ByteWriter writer = begin(Call::ActorHitMarks);
    writer.u32(uint32_t(actorIndex));
    writer.f32(marks.spearDamage);
    writer.f32(marks.legendaryDamage);
    writer.u16(marks.regeneratingDamage);
    writer.f32(marks.exposedPercent);
    writer.f32(marks.exposedGameMinutes);
    return writer.take();
}

std::vector<uint8_t> restoreActorShield(size_t actorIndex)
{
    Engine::ByteWriter writer = begin(Call::RestoreActorShield);
    writer.u32(uint32_t(actorIndex));
    return writer.take();
}

std::vector<uint8_t> revealActorsAround(size_t actorIndex, float radius)
{
    Engine::ByteWriter writer = begin(Call::RevealActorsAround);
    writer.u32(uint32_t(actorIndex));
    writer.f32(radius);
    return writer.take();
}

std::vector<uint8_t> scareNearbyPeasants(float radius, float seconds)
{
    Engine::ByteWriter writer = begin(Call::ScareNearbyPeasants);
    writer.f32(radius);
    writer.f32(seconds);
    return writer.take();
}

std::vector<uint8_t> dropHeldItem(const GameplayHeldItemDropRequest &request)
{
    Engine::ByteWriter writer = begin(Call::DropHeldItem);
    writer.block(SaveSections::encode(request.item));
    writePoint(writer, GameplayWorldPoint{request.sourceX, request.sourceY, request.sourceZ});
    writer.f32(request.yawRadians);
    return writer.take();
}

bool goesWithCharacterChange(std::span<const uint8_t> call)
{
    return !call.empty() && call[0] == uint8_t(Call::DropHeldItem);
}

bool execute(IGameplayWorldRuntime &worldRuntime, std::span<const uint8_t> call)
{
    Engine::ByteReader reader(call);
    const Call kind = Call(reader.u8());
    const size_t actorCount = worldRuntime.mapActorCount();

    switch (kind)
    {
        case Call::MeleeDamage:
        {
            const size_t actorIndex = reader.u32();
            const int damage = reader.i32();
            const GameplayWorldPoint source = readPoint(reader);
            ShieldAttackTier shieldTier = ShieldAttackTier::Physical;
            readEnum(reader, ShieldAttackTier::Spell, shieldTier);
            const ShieldHitModifiers shieldModifiers = readShieldModifiers(reader);
            const bool critical = reader.boolean();
            const bool hitReaction = reader.boolean();

            if (!reader.ok() || actorIndex >= actorCount || !saneDamage(damage) || !finitePoint(source)
                || !actorInBlowReach(worldRuntime, actorIndex))
            {
                return false;
            }

            return worldRuntime.applyPartyAttackMeleeDamage(
                actorIndex, damage, source, shieldTier, shieldModifiers, critical, hitReaction);
        }

        case Call::MeleeEffects:
        {
            const size_t actorIndex = reader.u32();
            CharacterAttackResult attack;
            attack.skillLevel = reader.u32();
            attack.stunTarget = reader.boolean();
            attack.stunSeconds = readOptionalSeconds(reader);
            attack.paralyzeTarget = reader.boolean();
            attack.paralyzeSeconds = readOptionalSeconds(reader);
            attack.fearTarget = reader.boolean();
            attack.enrageTarget = reader.boolean();
            attack.halveTargetArmorClass = reader.boolean();
            const GameplayWorldPoint source = readPoint(reader);

            if (!reader.ok() || actorIndex >= actorCount || !finitePoint(source)
                || !actorInBlowReach(worldRuntime, actorIndex))
            {
                return false;
            }

            worldRuntime.applyPartyAttackMeleeEffects(actorIndex, attack, source);
            return true;
        }

        case Call::MeleeBModelDamage:
        {
            const size_t bModelIndex = reader.u32();
            const int damage = reader.i32();
            return reader.ok() && saneDamage(damage) && worldRuntime.isPartyAttackMeleeBModelTarget(bModelIndex)
                && worldRuntime.applyPartyAttackMeleeBModelDamage(bModelIndex, damage);
        }

        case Call::MeleeEntityDamage:
        {
            const size_t entityIndex = reader.u32();
            const int damage = reader.i32();
            return reader.ok() && saneDamage(damage) && worldRuntime.isPartyAttackMeleeEntityTarget(entityIndex)
                && worldRuntime.applyPartyAttackMeleeEntityDamage(entityIndex, damage);
        }

        case Call::AttackProjectile:
        {
            GameplayPartyAttackProjectileRequest request;
            request.sourcePartyMemberIndex = reader.u32();
            request.objectId = reader.u32();
            request.impactObjectId = reader.u32();
            request.impactSoundId = reader.u32();
            request.damage = reader.i32();
            request.attackBonus = reader.i32();
            request.useActorHitChance = reader.boolean();
            readEnum(reader, CombatDamageType::Irresistible, request.damageType);
            readEnum(reader, ShieldAttackTier::Spell, request.shieldTier);
            request.shieldModifiers = readShieldModifiers(reader);
            request.weakerOfPhysicalAndFire = reader.boolean();
            request.explosionRadius = reader.f32();
            request.blastMinimumDamage = reader.i32();
            request.blastMaximumDamage = reader.i32();
            request.source = readPoint(reader);
            request.target = readPoint(reader);
            request.targetActorIndex = readOptionalIndex(reader);
            request.homing = reader.boolean();
            request.critical = reader.boolean();
            request.chainCount = reader.u8();
            request.chainShare = readFinite(reader);
            request.chainRadius = readFinite(reader);
            request.quietBlast = reader.boolean();

            if (!reader.ok() || !saneDamage(request.damage) || !saneDamage(request.blastMinimumDamage)
                || !saneDamage(request.blastMaximumDamage) || !finitePoint(request.source)
                || !finitePoint(request.target) || !std::isfinite(request.explosionRadius)
                || (request.targetActorIndex && *request.targetActorIndex >= actorCount))
            {
                return false;
            }

            return worldRuntime.spawnPartyAttackProjectile(request);
        }

        case Call::AttackSpell:
        {
            GameplayPartyAttackSpellRequest request;
            request.sourcePartyMemberIndex = reader.u32();
            request.spellId = reader.u32();
            request.skillLevel = reader.u32();
            request.skillMastery = reader.u32();
            request.damage = reader.i32();
            request.attackBonus = reader.i32();
            request.useActorHitChance = reader.boolean();
            request.source = readPoint(reader);
            request.target = readPoint(reader);

            if (!reader.ok() || !saneDamage(request.damage) || !finitePoint(request.source)
                || !finitePoint(request.target))
            {
                return false;
            }

            return worldRuntime.castPartyAttackSpell(request);
        }

        case Call::SpellProjectile:
        {
            GameplayPartySpellProjectileRequest request;
            request.casterMemberIndex = reader.u32();
            request.spellId = reader.u32();
            request.skillLevel = reader.u32();
            readEnum(reader, SkillMastery::Grandmaster, request.skillMastery);
            request.damage = reader.i32();
            readEnum(reader, CombatDamageType::Irresistible, request.damageType);
            const GameplayWorldPoint source = readPoint(reader);
            const GameplayWorldPoint target = readPoint(reader);
            request.sourceX = source.x;
            request.sourceY = source.y;
            request.sourceZ = source.z;
            request.targetX = target.x;
            request.targetY = target.y;
            request.targetZ = target.z;
            request.effectSoundIdOverride = reader.u32();
            request.impactSoundIdOverride = reader.u32();
            request.targetActorIndex = readOptionalIndex(reader);
            request.critical = reader.boolean();
            request.chainCount = reader.u8();
            request.chainShare = readFinite(reader);
            request.chainRadius = readFinite(reader);

            if (!reader.ok() || !saneDamage(request.damage) || !finitePoint(source) || !finitePoint(target)
                || (request.targetActorIndex && *request.targetActorIndex >= actorCount))
            {
                return false;
            }

            return worldRuntime.castPartySpellProjectile(request);
        }

        case Call::AttackResult:
        {
            const std::optional<size_t> actorIndex = readOptionalIndex(reader);
            const bool attacked = reader.boolean();
            const bool actionPerformed = reader.boolean();
            const bool missed = reader.boolean();

            if (!reader.ok() || (actorIndex && *actorIndex >= actorCount))
            {
                return false;
            }

            worldRuntime.recordPartyAttackWorldResult(actorIndex, attacked, actionPerformed, missed);
            return true;
        }

        case Call::StunActor:
        {
            const size_t actorIndex = reader.u32();
            const float seconds = reader.f32();
            return reader.ok() && actorIndex < actorCount && std::isfinite(seconds)
                && worldRuntime.stunActor(actorIndex, seconds);
        }

        case Call::DebuffActor:
        {
            const size_t actorIndex = reader.u32();
            GameplayActorHitDebuff debuff = GameplayActorHitDebuff::DarkGrasp;
            readEnum(reader, GameplayActorHitDebuff::Demoralize, debuff);
            const float seconds = reader.f32();
            const float power = reader.f32();
            return reader.ok() && actorIndex < actorCount && std::isfinite(seconds) && std::isfinite(power)
                && worldRuntime.debuffActor(actorIndex, debuff, seconds, power);
        }

        case Call::HealActor:
        {
            const size_t actorIndex = reader.u32();
            const int amount = reader.i32();
            return reader.ok() && actorIndex < actorCount && saneDamage(amount)
                && worldRuntime.healMapActor(actorIndex, amount);
        }

        case Call::ReflectedDamage:
        {
            const uint32_t actorId = reader.u32();
            const int damage = reader.i32();
            CombatDamageType damageType = CombatDamageType::Physical;
            readEnum(reader, CombatDamageType::Irresistible, damageType);
            const uint32_t memberIndex = reader.u32();
            return reader.ok() && saneDamage(damage)
                && worldRuntime.applyReflectedDamageToActor(actorId, damage, damageType, memberIndex);
        }

        case Call::PushActor:
        {
            const size_t actorIndex = reader.u32();
            const float directionX = reader.f32();
            const float directionY = reader.f32();
            const float distance = reader.f32();
            return reader.ok() && actorIndex < actorCount && std::isfinite(directionX) && std::isfinite(directionY)
                && std::isfinite(distance) && worldRuntime.pushActor(actorIndex, directionX, directionY, distance);
        }

        case Call::SuspendActorShield:
        {
            const size_t actorIndex = reader.u32();
            const float seconds = reader.f32();
            return reader.ok() && actorIndex < actorCount && std::isfinite(seconds)
                && worldRuntime.suspendActorShield(actorIndex, seconds);
        }

        case Call::ActorHitMarks:
        {
            // One blow's worth at the most: a guest's game cannot pile a monster's weakness up in one call.
            constexpr float MaximumPercent = 100.0f;
            constexpr float MaximumGameMinutes = 60.0f;
            const size_t actorIndex = reader.u32();
            Game::ActorHitMarks marks;
            marks.spearDamage = reader.f32();
            marks.legendaryDamage = reader.f32();
            marks.regeneratingDamage = reader.u16();
            marks.exposedPercent = reader.f32();
            marks.exposedGameMinutes = reader.f32();
            const auto within = [](float value, float maximum)
            {
                return std::isfinite(value) && value >= 0.0f && value <= maximum;
            };
            return reader.ok() && actorIndex < actorCount && within(marks.spearDamage, MaximumPercent)
                && within(marks.legendaryDamage, MaximumPercent) && marks.regeneratingDamage <= 10000
                && within(marks.exposedPercent, MaximumPercent) && within(marks.exposedGameMinutes, MaximumGameMinutes)
                && worldRuntime.addActorHitMarks(actorIndex, marks);
        }

        case Call::RestoreActorShield:
        {
            const size_t actorIndex = reader.u32();
            return reader.ok() && actorIndex < actorCount && worldRuntime.restoreActorShield(actorIndex);
        }

        case Call::RevealActorsAround:
        {
            const size_t actorIndex = reader.u32();
            const float radius = reader.f32();

            if (!reader.ok() || actorIndex >= actorCount || !std::isfinite(radius))
            {
                return false;
            }

            worldRuntime.revealActorsAround(actorIndex, radius);
            return true;
        }

        case Call::ScareNearbyPeasants:
        {
            const float radius = reader.f32();
            const float seconds = reader.f32();

            if (!reader.ok() || !std::isfinite(radius) || !std::isfinite(seconds))
            {
                return false;
            }

            worldRuntime.scareNearbyPeasants(radius, seconds);
            return true;
        }

        case Call::DropHeldItem:
        {
            GameplayHeldItemDropRequest request;
            const std::vector<uint8_t> item = reader.block(64 * 1024);
            const GameplayWorldPoint source = readPoint(reader);
            request.sourceX = source.x;
            request.sourceY = source.y;
            request.sourceZ = source.z;
            request.yawRadians = reader.f32();

            if (!reader.ok() || !SaveSections::decode(item, request.item) || !finitePoint(source)
                || !std::isfinite(request.yawRadians))
            {
                return false;
            }

            return worldRuntime.dropHeldItemToWorld(request);
        }
    }

    return false;
}
}
