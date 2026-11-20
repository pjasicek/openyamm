#include "game/gameplay/ActorBehaviorRuntime.h"
#include "engine/Localization.h"
#include "game/gameplay/Mm9ActorRules.h"

#include "game/audio/SoundRef.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/ActorBehaviorCatalog.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/MonsterSpellSupport.h"
#include "game/maps/MapDeltaData.h"
#include "game/party/Party.h"
#include "game/tables/MonsterModifiers.h"
#include "game/tables/SpellTable.h"

extern "C"
{
#include <lauxlib.h>
#include <lualib.h>
}

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <numbers>

namespace OpenYAMM::Game
{
struct ActorBehaviorRuntime::LuaCallContext
{
    ActorBehaviorInstanceState *pState = nullptr;
    const ActorBehaviorActorFacts *pActor = nullptr;
    ActorBehaviorFrameResult *pResult = nullptr;
    GameplayWorldPoint partyPosition;
    const Party *pParty = nullptr;
    // An MM9 boss script's hold on its loop (phase 5).
    ActorBehaviorMm9Script *pMm9 = nullptr;
};

namespace
{
constexpr const char *RuntimeRegistryKey = "openyamm.actorBehaviorRuntime";
// A climbing flyer's height above its target after its shield breaks (out of melee reach).
constexpr float ShieldBreakClimbHeight = 600.0f;
constexpr const char *SelfMetatableName = "openyamm.actorBehaviorSelf";
constexpr const char *SelfActorKey = "__actor";
constexpr float DefaultThinkIntervalSeconds = 0.5f;
constexpr float DefaultPerformSeconds = 1.5f;
constexpr int MaxSerializedDepth = 16;

enum class SerializedTag : uint8_t
{
    False = 1,
    True = 2,
    Integer = 3,
    Number = 4,
    String = 5,
    Table = 6,
};

uint32_t hashText(const std::string &text)
{
    uint32_t hash = 2166136261u;

    for (const char character : text)
    {
        hash = (hash ^ static_cast<uint8_t>(character)) * 16777619u;
    }

    return hash;
}

uint32_t nextRandom(uint32_t &state)
{
    state = state * 1664525u + 1013904223u;
    return state;
}

void appendBytes(std::vector<uint8_t> &out, const void *pData, size_t size)
{
    const uint8_t *pBytes = static_cast<const uint8_t *>(pData);
    out.insert(out.end(), pBytes, pBytes + size);
}

template <typename Value>
void appendValue(std::vector<uint8_t> &out, Value value)
{
    appendBytes(out, &value, sizeof(value));
}

template <typename Value>
bool readSerializedValue(const std::vector<uint8_t> &data, size_t &offset, Value &value)
{
    if (offset + sizeof(value) > data.size())
    {
        return false;
    }

    std::memcpy(&value, data.data() + offset, sizeof(value));
    offset += sizeof(value);
    return true;
}

// Script state holds plain data only: booleans, numbers, strings and nested tables of them.
bool serializeLuaValue(lua_State *pLuaState, int index, std::vector<uint8_t> &out, int depth, std::string &error)
{
    index = lua_absindex(pLuaState, index);

    switch (lua_type(pLuaState, index))
    {
        case LUA_TBOOLEAN:
            appendValue(out, lua_toboolean(pLuaState, index) ? SerializedTag::True : SerializedTag::False);
            return true;

        case LUA_TNUMBER:
            if (lua_isinteger(pLuaState, index))
            {
                appendValue(out, SerializedTag::Integer);
                appendValue(out, static_cast<int64_t>(lua_tointeger(pLuaState, index)));
            }
            else
            {
                appendValue(out, SerializedTag::Number);
                appendValue(out, static_cast<double>(lua_tonumber(pLuaState, index)));
            }
            return true;

        case LUA_TSTRING:
        {
            size_t length = 0;
            const char *pText = lua_tolstring(pLuaState, index, &length);
            appendValue(out, SerializedTag::String);
            appendValue(out, static_cast<uint32_t>(length));
            appendBytes(out, pText, length);
            return true;
        }

        case LUA_TTABLE:
        {
            if (depth >= MaxSerializedDepth)
            {
                error = "script state nests deeper than " + std::to_string(MaxSerializedDepth) + " tables";
                return false;
            }

            appendValue(out, SerializedTag::Table);
            const size_t countOffset = out.size();
            appendValue(out, uint32_t(0));
            uint32_t count = 0;
            lua_pushnil(pLuaState);

            while (lua_next(pLuaState, index) != 0)
            {
                const int keyType = lua_type(pLuaState, -2);

                if (keyType != LUA_TSTRING && keyType != LUA_TNUMBER && keyType != LUA_TBOOLEAN)
                {
                    lua_pop(pLuaState, 2);
                    error = "script state keys must be strings, numbers or booleans";
                    return false;
                }

                if (!serializeLuaValue(pLuaState, -2, out, depth + 1, error)
                    || !serializeLuaValue(pLuaState, -1, out, depth + 1, error))
                {
                    lua_pop(pLuaState, 2);
                    return false;
                }

                ++count;
                lua_pop(pLuaState, 1);
            }

            std::memcpy(out.data() + countOffset, &count, sizeof(count));
            return true;
        }

        default:
            error = std::string("script state cannot hold a ") + luaL_typename(pLuaState, index);
            return false;
    }
}

bool deserializeLuaValue(lua_State *pLuaState, const std::vector<uint8_t> &data, size_t &offset, int depth)
{
    SerializedTag tag = SerializedTag::False;

    if (depth > MaxSerializedDepth || !readSerializedValue(data, offset, tag))
    {
        return false;
    }

    switch (tag)
    {
        case SerializedTag::False:
        case SerializedTag::True:
            lua_pushboolean(pLuaState, tag == SerializedTag::True);
            return true;

        case SerializedTag::Integer:
        {
            int64_t value = 0;

            if (!readSerializedValue(data, offset, value))
            {
                return false;
            }

            lua_pushinteger(pLuaState, static_cast<lua_Integer>(value));
            return true;
        }

        case SerializedTag::Number:
        {
            double value = 0.0;

            if (!readSerializedValue(data, offset, value))
            {
                return false;
            }

            lua_pushnumber(pLuaState, static_cast<lua_Number>(value));
            return true;
        }

        case SerializedTag::String:
        {
            uint32_t length = 0;

            if (!readSerializedValue(data, offset, length) || offset + length > data.size())
            {
                return false;
            }

            lua_pushlstring(pLuaState, reinterpret_cast<const char *>(data.data() + offset), length);
            offset += length;
            return true;
        }

        case SerializedTag::Table:
        {
            uint32_t count = 0;

            if (!readSerializedValue(data, offset, count))
            {
                return false;
            }

            lua_createtable(pLuaState, 0, static_cast<int>(std::min<uint32_t>(count, 64)));

            for (uint32_t pairIndex = 0; pairIndex < count; ++pairIndex)
            {
                if (!deserializeLuaValue(pLuaState, data, offset, depth + 1))
                {
                    lua_pop(pLuaState, 1);
                    return false;
                }

                if (!deserializeLuaValue(pLuaState, data, offset, depth + 1))
                {
                    lua_pop(pLuaState, 2);
                    return false;
                }

                lua_rawset(pLuaState, -3);
            }

            return true;
        }
    }

    return false;
}

std::optional<ActorAiAnimationState> animationStateFromName(const std::string &name)
{
    if (name == "standing")
    {
        return ActorAiAnimationState::Standing;
    }

    if (name == "walking")
    {
        return ActorAiAnimationState::Walking;
    }

    if (name == "attack_melee")
    {
        return ActorAiAnimationState::AttackMelee;
    }

    if (name == "attack_ranged")
    {
        return ActorAiAnimationState::AttackRanged;
    }

    if (name == "hit")
    {
        return ActorAiAnimationState::GotHit;
    }

    if (name == "fidget")
    {
        return ActorAiAnimationState::Bored;
    }

    return std::nullopt;
}

std::optional<SkillMastery> masteryFromName(const std::string &name)
{
    if (name == "normal")
    {
        return SkillMastery::Normal;
    }

    if (name == "expert")
    {
        return SkillMastery::Expert;
    }

    if (name == "master")
    {
        return SkillMastery::Master;
    }

    if (name == "grandmaster")
    {
        return SkillMastery::Grandmaster;
    }

    return std::nullopt;
}

std::optional<GameplayActorAiType> aiTypeFromName(const std::string &name)
{
    if (name == "suicide")
    {
        return GameplayActorAiType::Suicide;
    }

    if (name == "wimp")
    {
        return GameplayActorAiType::Wimp;
    }

    if (name == "normal")
    {
        return GameplayActorAiType::Normal;
    }

    if (name == "aggressive")
    {
        return GameplayActorAiType::Aggressive;
    }

    return std::nullopt;
}

bool actorIsBusy(ActorAiAnimationState animationState)
{
    return animationState == ActorAiAnimationState::AttackMelee
        || animationState == ActorAiAnimationState::AttackRanged
        || animationState == ActorAiAnimationState::GotHit
        || animationState == ActorAiAnimationState::Dying
        || animationState == ActorAiAnimationState::Dead;
}

GameplayWorldPoint actorCenter(const ActorBehaviorActorFacts &actor)
{
    return {actor.position.x, actor.position.y, actor.position.z + actor.height * 0.5f};
}

ActorBehaviorRuntime &runtimeFromLua(lua_State *pLuaState)
{
    lua_getfield(pLuaState, LUA_REGISTRYINDEX, RuntimeRegistryKey);
    ActorBehaviorRuntime *pRuntime = static_cast<ActorBehaviorRuntime *>(lua_touserdata(pLuaState, -1));
    lua_pop(pLuaState, 1);
    return *pRuntime;
}

// Every self method acts on the actor whose handler is running; a self kept from another call raises an error.
ActorBehaviorRuntime::LuaCallContext &callContext(lua_State *pLuaState)
{
    ActorBehaviorRuntime::LuaCallContext *pContext = runtimeFromLua(pLuaState).activeCall();
    luaL_checktype(pLuaState, 1, LUA_TTABLE);
    lua_getfield(pLuaState, 1, SelfActorKey);
    const lua_Integer actorIndex = lua_tointeger(pLuaState, -1);
    lua_pop(pLuaState, 1);

    if (pContext == nullptr || static_cast<size_t>(actorIndex) != pContext->pState->actorIndex)
    {
        luaL_error(pLuaState, "actor behaviour self used outside its own handler");
    }

    return *pContext;
}

std::string optionalStringField(lua_State *pLuaState, int tableIndex, const char *pName)
{
    lua_getfield(pLuaState, tableIndex, pName);
    std::string value = lua_isstring(pLuaState, -1) ? lua_tostring(pLuaState, -1) : "";
    lua_pop(pLuaState, 1);
    return value;
}

std::optional<double> optionalNumberField(lua_State *pLuaState, int tableIndex, const char *pName)
{
    lua_getfield(pLuaState, tableIndex, pName);
    std::optional<double> value;

    if (lua_isnumber(pLuaState, -1))
    {
        value = lua_tonumber(pLuaState, -1);
    }

    lua_pop(pLuaState, 1);
    return value;
}

ActorBehaviorSpell readSpellOptions(lua_State *pLuaState, int tableIndex, const SpellTable *pSpellTable)
{
    luaL_checktype(pLuaState, tableIndex, LUA_TTABLE);
    ActorBehaviorSpell spell = {};
    lua_getfield(pLuaState, tableIndex, "spell");

    if (lua_isinteger(pLuaState, -1))
    {
        spell.spellId = static_cast<uint32_t>(lua_tointeger(pLuaState, -1));
    }
    else if (lua_isstring(pLuaState, -1) && pSpellTable != nullptr)
    {
        if (const SpellEntry *pEntry = pSpellTable->findByName(lua_tostring(pLuaState, -1)))
        {
            spell.spellId = static_cast<uint32_t>(pEntry->id);
        }
    }

    lua_pop(pLuaState, 1);

    if (spell.spellId == 0)
    {
        luaL_error(pLuaState, "unknown spell");
    }

    if (pSpellTable != nullptr)
    {
        const SpellEntry *pEntry = pSpellTable->findById(static_cast<int>(spell.spellId));

        if (pEntry == nullptr || !isMonsterProjectileSpellName(pEntry->name))
        {
            luaL_error(pLuaState, "actor behaviour spells must be monster projectile spells (spell %d)",
                static_cast<int>(spell.spellId));
        }
    }

    spell.skillLevel = static_cast<uint32_t>(std::max(1.0, optionalNumberField(pLuaState, tableIndex, "skill")
        .value_or(5.0)));
    const std::string masteryName = optionalStringField(pLuaState, tableIndex, "mastery");
    const std::optional<SkillMastery> mastery = masteryFromName(masteryName.empty() ? "expert" : masteryName);

    if (!mastery)
    {
        luaL_error(pLuaState, "unknown spell mastery: %s", masteryName.c_str());
    }

    spell.skillMastery = *mastery;
    spell.useChance = std::clamp(
        static_cast<int>(optionalNumberField(pLuaState, tableIndex, "chance").value_or(100.0)), 0, 100);
    return spell;
}

int luaSelfHp(lua_State *pLuaState)
{
    lua_pushinteger(pLuaState, callContext(pLuaState).pActor->currentHp);
    return 1;
}

int luaSelfMaxHp(lua_State *pLuaState)
{
    lua_pushinteger(pLuaState, callContext(pLuaState).pActor->maxHp);
    return 1;
}

int luaSelfHpFraction(lua_State *pLuaState)
{
    const ActorBehaviorActorFacts &actor = *callContext(pLuaState).pActor;
    lua_pushnumber(pLuaState, actor.maxHp > 0 ? double(actor.currentHp) / double(actor.maxHp) : 0.0);
    return 1;
}

int luaSelfPosition(lua_State *pLuaState)
{
    const ActorBehaviorActorFacts &actor = *callContext(pLuaState).pActor;
    lua_pushnumber(pLuaState, actor.position.x);
    lua_pushnumber(pLuaState, actor.position.y);
    lua_pushnumber(pLuaState, actor.position.z);
    return 3;
}

int luaSelfDistanceToParty(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const float dx = context.partyPosition.x - context.pActor->position.x;
    const float dy = context.partyPosition.y - context.pActor->position.y;
    const float dz = context.partyPosition.z - context.pActor->position.z;
    lua_pushnumber(pLuaState, std::sqrt(dx * dx + dy * dy + dz * dz));
    return 1;
}

int luaSelfIsHostile(lua_State *pLuaState)
{
    lua_pushboolean(pLuaState, callContext(pLuaState).pActor->hostileToParty);
    return 1;
}

int luaSelfMonsterId(lua_State *pLuaState)
{
    lua_pushinteger(pLuaState, callContext(pLuaState).pActor->monsterId);
    return 1;
}

int luaSelfAge(lua_State *pLuaState)
{
    lua_pushnumber(pLuaState, callContext(pLuaState).pState->ageSeconds);
    return 1;
}

// random() -> [0, 1); random(n) -> 1..n; random(a, b) -> a..b. Seeded per actor and saved with the map.
int luaSelfRandom(lua_State *pLuaState)
{
    ActorBehaviorInstanceState &state = *callContext(pLuaState).pState;
    const uint32_t value = nextRandom(state.randomState) >> 8;
    const int argumentCount = lua_gettop(pLuaState);

    if (argumentCount <= 1)
    {
        lua_pushnumber(pLuaState, double(value) / double(1u << 24));
        return 1;
    }

    const lua_Integer low = argumentCount >= 3 ? luaL_checkinteger(pLuaState, 2) : 1;
    const lua_Integer high = luaL_checkinteger(pLuaState, argumentCount >= 3 ? 3 : 2);
    luaL_argcheck(pLuaState, high >= low, argumentCount >= 3 ? 3 : 2, "empty random interval");
    lua_pushinteger(pLuaState, low + lua_Integer(value % uint32_t(high - low + 1)));
    return 1;
}

int luaSelfSay(lua_State *pLuaState)
{
    // A behaviour's line, in the interface language as the evt bindings show theirs.
    callContext(pLuaState).pResult->statusMessages.push_back(Engine::localize(luaL_checkstring(pLuaState, 2)));
    return 0;
}

int luaSelfPlaySound(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    context.pResult->sounds.push_back({luaL_checkstring(pLuaState, 2), actorCenter(*context.pActor)});
    return 0;
}

// effect(id [, scale [, heightFraction [, forward]]]): heightFraction 0 is the feet, 1 the head (default 0.5); forward
// moves it that far along the actor's facing (a dragon's snout).
int luaSelfEffect(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const float scale = static_cast<float>(luaL_optnumber(pLuaState, 3, 1.0));
    const float heightFraction = static_cast<float>(luaL_optnumber(pLuaState, 4, 0.5));
    const float forward = static_cast<float>(luaL_optnumber(pLuaState, 5, 0.0));
    luaL_argcheck(pLuaState, std::isfinite(scale) && scale > 0.0f, 3, "effect scale must be positive");
    luaL_argcheck(pLuaState, std::isfinite(forward), 5, "effect forward must be finite");
    GameplayWorldPoint position = context.pActor->position;
    position.x += std::cos(context.pActor->yawRadians) * forward;
    position.y += std::sin(context.pActor->yawRadians) * forward;
    position.z += context.pActor->height * heightFraction;
    context.pResult->effects.push_back({luaL_checkstring(pLuaState, 2), position, scale});
    return 0;
}

// effectAt(id, x, y, z [, scale]): the effect at a world point (a summoner's spawn location).
int luaSelfEffectAt(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const GameplayWorldPoint position = {static_cast<float>(luaL_checknumber(pLuaState, 3)),
        static_cast<float>(luaL_checknumber(pLuaState, 4)), static_cast<float>(luaL_checknumber(pLuaState, 5))};
    const float scale = static_cast<float>(luaL_optnumber(pLuaState, 6, 1.0));
    luaL_argcheck(pLuaState, std::isfinite(scale) && scale > 0.0f, 6, "effect scale must be positive");
    context.pResult->effects.push_back({luaL_checkstring(pLuaState, 2), position, scale});
    return 0;
}

// perform{clip=, seconds=, fallback=, sound=, effect=}: holds the native AI while the clip plays.
int luaSelfPerform(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    luaL_checktype(pLuaState, 2, LUA_TTABLE);
    ActorBehaviorPerform perform = {};
    perform.clip = optionalStringField(pLuaState, 2, "clip");
    perform.durationSeconds = static_cast<float>(
        optionalNumberField(pLuaState, 2, "seconds").value_or(DefaultPerformSeconds));
    const std::string fallbackName = optionalStringField(pLuaState, 2, "fallback");
    const std::optional<ActorAiAnimationState> fallback =
        animationStateFromName(fallbackName.empty() ? "attack_ranged" : fallbackName);
    luaL_argcheck(pLuaState, fallback.has_value(), 2, "unknown fallback animation");
    luaL_argcheck(pLuaState, std::isfinite(perform.durationSeconds) && perform.durationSeconds > 0.0f, 2,
        "perform seconds must be positive");
    perform.fallbackAnimation = *fallback;
    context.pState->perform = perform;

    const std::string sound = optionalStringField(pLuaState, 2, "sound");
    const std::string effect = optionalStringField(pLuaState, 2, "effect");

    if (!sound.empty())
    {
        context.pResult->sounds.push_back({sound, actorCenter(*context.pActor)});
    }

    if (!effect.empty())
    {
        context.pResult->effects.push_back({effect, actorCenter(*context.pActor), 1.0f});
    }

    return 0;
}

int luaSelfIsPerforming(lua_State *pLuaState)
{
    lua_pushboolean(pLuaState, callContext(pLuaState).pState->perform.has_value());
    return 1;
}

// visual = false draws no dome; visual = {color = {r, g, b}, intensity =, rim =, noise =} styles it.
void readWardVisual(lua_State *pLuaState, int tableIndex, ActorBehaviorWardVisual &visual)
{
    lua_getfield(pLuaState, tableIndex, "visual");

    if (lua_isboolean(pLuaState, -1))
    {
        visual.dome = lua_toboolean(pLuaState, -1) != 0;
    }
    else if (lua_istable(pLuaState, -1))
    {
        const int visualIndex = lua_gettop(pLuaState);
        lua_getfield(pLuaState, visualIndex, "color");

        if (lua_istable(pLuaState, -1))
        {
            for (lua_Integer channel = 0; channel < 3; ++channel)
            {
                lua_geti(pLuaState, -1, channel + 1);
                visual.color[channel] = static_cast<uint8_t>(std::clamp<lua_Integer>(
                    lua_isinteger(pLuaState, -1) ? lua_tointeger(pLuaState, -1) : visual.color[channel], 0, 255));
                lua_pop(pLuaState, 1);
            }
        }

        lua_pop(pLuaState, 1);
        visual.intensity = static_cast<float>(std::clamp(
            optionalNumberField(pLuaState, visualIndex, "intensity").value_or(visual.intensity), 0.0, 4.0));
        visual.rimPower = static_cast<float>(std::clamp(
            optionalNumberField(pLuaState, visualIndex, "rim").value_or(visual.rimPower), 0.5, 12.0));
        visual.noise = static_cast<float>(std::clamp(
            optionalNumberField(pLuaState, visualIndex, "noise").value_or(visual.noise), 0.0, 1.0));
    }
    else if (!lua_isnil(pLuaState, -1))
    {
        luaL_error(pLuaState, "ward visual must be false or a table");
    }

    lua_pop(pLuaState, 1);
}

// addWard{id=, radius=, seconds=, effect=, effectScale=, effectInterval=, visual=}
int luaSelfAddWard(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    luaL_checktype(pLuaState, 2, LUA_TTABLE);
    ActorBehaviorWard ward = {};
    ward.id = optionalStringField(pLuaState, 2, "id");
    ward.radius = static_cast<float>(optionalNumberField(pLuaState, 2, "radius").value_or(0.0));
    ward.remainingSeconds = static_cast<float>(optionalNumberField(pLuaState, 2, "seconds").value_or(-1.0));
    ward.effectId = optionalStringField(pLuaState, 2, "effect");
    ward.effectScale = static_cast<float>(optionalNumberField(pLuaState, 2, "effectScale").value_or(1.0));
    ward.effectIntervalSeconds =
        static_cast<float>(optionalNumberField(pLuaState, 2, "effectInterval").value_or(1.0));
    luaL_argcheck(pLuaState, !ward.id.empty(), 2, "ward id required");
    luaL_argcheck(pLuaState, std::isfinite(ward.radius) && ward.radius > 0.0f, 2, "ward radius must be positive");
    luaL_argcheck(pLuaState, std::isfinite(ward.effectScale) && ward.effectScale > 0.0f, 2,
        "ward effectScale must be positive");
    luaL_argcheck(pLuaState, std::isfinite(ward.effectIntervalSeconds) && ward.effectIntervalSeconds > 0.05f, 2,
        "ward effectInterval must exceed 0.05 seconds");
    readWardVisual(pLuaState, 2, ward.visual);

    std::vector<ActorBehaviorWard> &wards = context.pState->wards;
    wards.erase(std::remove_if(wards.begin(), wards.end(),
        [&](const ActorBehaviorWard &existing) { return existing.id == ward.id; }), wards.end());
    wards.push_back(std::move(ward));
    return 0;
}

int luaSelfRemoveWard(lua_State *pLuaState)
{
    std::vector<ActorBehaviorWard> &wards = callContext(pLuaState).pState->wards;
    const std::string id = luaL_checkstring(pLuaState, 2);
    wards.erase(std::remove_if(wards.begin(), wards.end(),
        [&](const ActorBehaviorWard &ward) { return ward.id == id; }), wards.end());
    return 0;
}

int luaSelfHasWard(lua_State *pLuaState)
{
    const std::vector<ActorBehaviorWard> &wards = callContext(pLuaState).pState->wards;
    const std::string id = luaL_checkstring(pLuaState, 2);
    lua_pushboolean(pLuaState, std::any_of(wards.begin(), wards.end(),
        [&](const ActorBehaviorWard &ward) { return ward.id == id; }));
    return 1;
}

int luaSelfStartTimer(lua_State *pLuaState)
{
    std::vector<ActorBehaviorTimer> &timers = callContext(pLuaState).pState->timers;
    const std::string name = luaL_checkstring(pLuaState, 2);
    const float seconds = static_cast<float>(luaL_checknumber(pLuaState, 3));
    luaL_argcheck(pLuaState, std::isfinite(seconds) && seconds >= 0.0f, 3, "timer seconds must not be negative");
    timers.erase(std::remove_if(timers.begin(), timers.end(),
        [&](const ActorBehaviorTimer &timer) { return timer.name == name; }), timers.end());
    timers.push_back({name, seconds});
    return 0;
}

int luaSelfStopTimer(lua_State *pLuaState)
{
    std::vector<ActorBehaviorTimer> &timers = callContext(pLuaState).pState->timers;
    const std::string name = luaL_checkstring(pLuaState, 2);
    timers.erase(std::remove_if(timers.begin(), timers.end(),
        [&](const ActorBehaviorTimer &timer) { return timer.name == name; }), timers.end());
    return 0;
}

int luaSelfHasTimer(lua_State *pLuaState)
{
    const std::vector<ActorBehaviorTimer> &timers = callContext(pLuaState).pState->timers;
    const std::string name = luaL_checkstring(pLuaState, 2);
    lua_pushboolean(pLuaState, std::any_of(timers.begin(), timers.end(),
        [&](const ActorBehaviorTimer &timer) { return timer.name == name; }));
    return 1;
}

// castNext{spell=, skill=, mastery=}: the next spell attack the native AI makes uses this spell.
int luaSelfCastNext(lua_State *pLuaState)
{
    ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    context.pState->nextCast = readSpellOptions(pLuaState, 2, runtimeFromLua(pLuaState).spellTable());
    context.pState->nextCast->useChance = 100;
    return 0;
}

// setSpell{spell=, skill=, mastery=, chance=}: replaces the monster's first spell until clearSpell().
int luaSelfSetSpell(lua_State *pLuaState)
{
    ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    context.pState->spellOverride = readSpellOptions(pLuaState, 2, runtimeFromLua(pLuaState).spellTable());
    return 0;
}

int luaSelfClearSpell(lua_State *pLuaState)
{
    callContext(pLuaState).pState->spellOverride.reset();
    return 0;
}

int luaSelfSetAiType(lua_State *pLuaState)
{
    ActorBehaviorInstanceState &state = *callContext(pLuaState).pState;

    if (lua_isnoneornil(pLuaState, 2))
    {
        state.aiTypeOverride.reset();
        return 0;
    }

    const std::string name = luaL_checkstring(pLuaState, 2);
    const std::optional<GameplayActorAiType> aiType = aiTypeFromName(name);
    luaL_argcheck(pLuaState, aiType.has_value(), 2, "unknown AI type");
    state.aiTypeOverride = aiType;
    return 0;
}

int luaSelfSetNoFlee(lua_State *pLuaState)
{
    callContext(pLuaState).pState->suppressFlee = lua_toboolean(pLuaState, 2) != 0;
    return 0;
}

// summon(monsterId, count [, radius]): hostile monsters around the actor.
int luaSelfSummon(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const lua_Integer monsterId = luaL_checkinteger(pLuaState, 2);
    const lua_Integer count = luaL_optinteger(pLuaState, 3, 1);
    const float radius = static_cast<float>(luaL_optnumber(pLuaState, 4, 256.0));
    luaL_argcheck(pLuaState, monsterId > 0 && monsterId <= 32767, 2, "invalid monster id");
    luaL_argcheck(pLuaState, count > 0 && count <= 16, 3, "summon count must be 1..16");

    for (lua_Integer index = 0; index < count; ++index)
    {
        const float angle = float(nextRandom(context.pState->randomState) >> 8) / float(1u << 24)
            * 6.2831853f;
        ActorBehaviorSummonRequest request = {};
        request.monsterId = static_cast<int16_t>(monsterId);
        request.count = 1;
        request.position = {
            context.pActor->position.x + std::cos(angle) * radius,
            context.pActor->position.y + std::sin(angle) * radius,
            context.pActor->position.z};
        context.pResult->summons.push_back(request);
    }

    return 0;
}

// self:summonAt(monsterId, x, y, z[, count[, spread]]): monsters around a point (count up to 16, spread 0).
int luaSelfSummonAt(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const lua_Integer monsterId = luaL_checkinteger(pLuaState, 2);
    const float x = static_cast<float>(luaL_checknumber(pLuaState, 3));
    const float y = static_cast<float>(luaL_checknumber(pLuaState, 4));
    const float z = static_cast<float>(luaL_checknumber(pLuaState, 5));
    const lua_Integer count = luaL_optinteger(pLuaState, 6, 1);
    const float spread = static_cast<float>(luaL_optnumber(pLuaState, 7, 0.0));
    luaL_argcheck(pLuaState, monsterId > 0 && monsterId <= 32767, 2, "invalid monster id");
    luaL_argcheck(pLuaState, count > 0 && count <= 16, 6, "summon count must be 1..16");

    for (lua_Integer index = 0; index < count; ++index)
    {
        const float angle = float(nextRandom(context.pState->randomState) >> 8) / float(1u << 24)
            * 6.2831853f;
        ActorBehaviorSummonRequest request = {};
        request.monsterId = static_cast<int16_t>(monsterId);
        request.count = 1;
        request.position = {x + std::cos(angle) * spread, y + std::sin(angle) * spread, z};
        context.pResult->summons.push_back(request);
    }

    return 0;
}

void pushActorCommand(lua_State *pLuaState, ActorBehaviorActorCommand::Kind kind, float seconds,
    const std::string &effectId)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    ActorBehaviorActorCommand command = {};
    command.kind = kind;
    command.actorIndex = context.pActor->actorIndex;
    command.seconds = seconds;
    command.effectId = effectId;
    context.pResult->actorCommands.push_back(std::move(command));
}

// self:blink(): blinks away now, as the blink modifier does (its range, or the default one without it).
int luaSelfBlink(lua_State *pLuaState)
{
    pushActorCommand(pLuaState, ActorBehaviorActorCommand::Kind::Blink, 0.0f, {});
    return 0;
}

// self:suspendShield([seconds]): its energy shield drops and does not regenerate for the seconds (none: until
// self:restoreShield()).
int luaSelfSuspendShield(lua_State *pLuaState)
{
    pushActorCommand(pLuaState, ActorBehaviorActorCommand::Kind::SuspendShield,
        static_cast<float>(luaL_optnumber(pLuaState, 2, -1.0)), {});
    return 0;
}

int luaSelfRestoreShield(lua_State *pLuaState)
{
    pushActorCommand(pLuaState, ActorBehaviorActorCommand::Kind::RestoreShield, 0.0f, {});
    return 0;
}

// self:leave([effect]): leaves the map (hidden for good, as SetMonsterBit's invisible bit), with the effect at it.
int luaSelfLeave(lua_State *pLuaState)
{
    pushActorCommand(pLuaState, ActorBehaviorActorCommand::Kind::Leave, 0.0f, luaL_optstring(pLuaState, 2, ""));
    return 0;
}

// self:setSpeed(multiplier): moves and attacks this much faster (1 restores); saved with the instance.
int luaSelfSetSpeed(lua_State *pLuaState)
{
    const float multiplier = static_cast<float>(luaL_checknumber(pLuaState, 2));
    luaL_argcheck(pLuaState, multiplier > 0.0f && multiplier <= 10.0f, 2, "speed must be in (0, 10]");
    callContext(pLuaState).pState->speedMultiplier = multiplier;
    return 0;
}

// self:setInvulnerable(on): no damage reaches it while on (the Bulwark while its couplings stand).
int luaSelfSetInvulnerable(lua_State *pLuaState)
{
    callContext(pLuaState).pState->invulnerable = lua_toboolean(pLuaState, 2) != 0;
    return 0;
}

// self:setLeash(radius): a post at most radius from its home, walking back with no target (nil or 0 clears it).
int luaSelfSetLeash(lua_State *pLuaState)
{
    const float radius = static_cast<float>(luaL_optnumber(pLuaState, 2, 0.0));
    ActorBehaviorInstanceState &state = *callContext(pLuaState).pState;
    state.leashRadius = radius > 0.0f ? std::optional<float>(radius) : std::nullopt;
    return 0;
}

// self:setRangedBand(min, max): keeps that distance to its target between shots (no arguments clears it).
int luaSelfSetRangedBand(lua_State *pLuaState)
{
    ActorBehaviorInstanceState &state = *callContext(pLuaState).pState;
    if (lua_isnoneornil(pLuaState, 2))
    {
        state.rangedBand.reset();
        return 0;
    }
    const float minimum = static_cast<float>(luaL_checknumber(pLuaState, 2));
    const float maximum = static_cast<float>(luaL_checknumber(pLuaState, 3));
    luaL_argcheck(pLuaState, minimum >= 0.0f && maximum > minimum, 3, "the band needs 0 <= min < max");
    state.rangedBand = std::array<float, 2>{minimum, maximum};
    return 0;
}

// self:moveTo(x, y, z): its home becomes the point: it walks there and holds it while it has no target (no arguments
// clears it).
int luaSelfMoveTo(lua_State *pLuaState)
{
    ActorBehaviorInstanceState &state = *callContext(pLuaState).pState;
    if (lua_isnoneornil(pLuaState, 2))
    {
        state.moveTarget.reset();
        return 0;
    }
    state.moveTarget = GameplayWorldPoint{static_cast<float>(luaL_checknumber(pLuaState, 2)),
        static_cast<float>(luaL_checknumber(pLuaState, 3)), static_cast<float>(luaL_checknumber(pLuaState, 4))};
    return 0;
}

// self:runEvent(eventId): runs a map event (a boss's phase handing the map its cue).
int luaSelfRunEvent(lua_State *pLuaState)
{
    const lua_Integer eventId = luaL_checkinteger(pLuaState, 2);
    luaL_argcheck(pLuaState, eventId > 0 && eventId <= 65535, 2, "invalid event id");
    callContext(pLuaState).pResult->mapEvents.push_back(uint16_t(eventId));
    return 0;
}

// self:bearingToParty(): degrees from its facing to the party, -180..180 (positive: the party is to its left).
int luaSelfBearingToParty(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const float toParty = std::atan2(context.partyPosition.y - context.pActor->position.y,
        context.partyPosition.x - context.pActor->position.x);
    const float bearing = std::remainder(toParty - context.pActor->yawRadians, 2.0f * std::numbers::pi_v<float>);
    lua_pushnumber(pLuaState, bearing * 180.0f / std::numbers::pi_v<float>);
    return 1;
}

// self:setArmoredFront(degrees, damageMultiplier): hits from within degrees either side of its facing deal this share
// of their damage (no arguments clears it).
int luaSelfSetArmoredFront(lua_State *pLuaState)
{
    ActorBehaviorInstanceState &state = *callContext(pLuaState).pState;
    if (lua_isnoneornil(pLuaState, 2))
    {
        state.armoredFront.reset();
        return 0;
    }
    const float degrees = static_cast<float>(luaL_checknumber(pLuaState, 2));
    const float multiplier = static_cast<float>(luaL_checknumber(pLuaState, 3));
    luaL_argcheck(pLuaState, degrees > 0.0f && degrees <= 180.0f, 2, "the arc is 0..180 degrees either side");
    luaL_argcheck(pLuaState, multiplier >= 0.0f && multiplier <= 1.0f, 3, "the multiplier is 0..1");
    state.armoredFront = std::array<float, 2>{degrees * std::numbers::pi_v<float> / 180.0f, multiplier};
    return 0;
}

// self:qbit(id): whether the party has the QBit set.
int luaSelfQBit(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const lua_Integer qbit = luaL_checkinteger(pLuaState, 2);
    lua_pushboolean(pLuaState,
        context.pParty != nullptr && qbit > 0 && context.pParty->hasQuestBit(uint32_t(qbit)) ? 1 : 0);
    return 1;
}

// MM9 boss scripts (MM9_MONSTER_AI_PLAN.md phase 5): queries of what the last AI step showed and commands to the
// actor's MM9 loop. A target is a table {kind = "party" | "actor", index = <actor index>, monster =, distance = <edge
// distance>, clear = <a line to it>, height = <above its feet>, hostile = <to the party>}.
void pushMm9Target(lua_State *pLuaState, ActorAiTargetKind kind, size_t actorIndex, int16_t monsterId, float distance,
    bool clear, float height, bool hostile)
{
    lua_createtable(pLuaState, 0, 7);
    lua_pushstring(pLuaState, kind == ActorAiTargetKind::Party ? "party" : "actor");
    lua_setfield(pLuaState, -2, "kind");

    if (kind == ActorAiTargetKind::Actor)
    {
        lua_pushinteger(pLuaState, lua_Integer(actorIndex));
        lua_setfield(pLuaState, -2, "index");
        lua_pushinteger(pLuaState, monsterId);
        lua_setfield(pLuaState, -2, "monster");
    }

    lua_pushnumber(pLuaState, distance);
    lua_setfield(pLuaState, -2, "distance");
    lua_pushboolean(pLuaState, clear ? 1 : 0);
    lua_setfield(pLuaState, -2, "clear");
    lua_pushnumber(pLuaState, height);
    lua_setfield(pLuaState, -2, "height");
    lua_pushboolean(pLuaState, hostile ? 1 : 0);
    lua_setfield(pLuaState, -2, "hostile");
}

ActorBehaviorMm9Script &mm9Script(lua_State *pLuaState)
{
    ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);

    if (context.pMm9 == nullptr)
    {
        luaL_error(pLuaState, "no MM9 loop state for this actor");
    }

    return *context.pMm9;
}

// self:target(): the target its MM9 loop holds, nil without one.
int luaSelfTarget(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);

    if (!script.viewValid || script.heldKind == ActorAiTargetKind::None)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    int16_t monsterId = 0;

    for (const ActorBehaviorAiActorView &other : runtimeFromLua(pLuaState).aiActors())
    {
        monsterId = script.heldKind == ActorAiTargetKind::Actor && other.actorIndex == script.heldActorIndex
            ? other.monsterId : monsterId;
    }

    pushMm9Target(pLuaState, script.heldKind, script.heldActorIndex, monsterId, script.targetDistance,
        script.targetClear, script.targetHeight, true);
    lua_pushboolean(pLuaState, script.targetOffered ? 1 : 0);
    lua_setfield(pLuaState, -2, "offered");
    return 1;
}

// self:targets([radius]): the party (when it is hostile to the party) and every other living actor of the last AI step
// within radius (edge distance; none: all), nearest first. The line is known only to the target it holds (assumed
// clear to the others: the behaviour layer traces no lines between actors).
int luaSelfTargets(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    const ActorBehaviorRuntime &runtime = runtimeFromLua(pLuaState);
    const float radius = static_cast<float>(luaL_optnumber(pLuaState, 2, 1.0e9));
    const ActorBehaviorActorFacts &self = *context.pActor;
    const GameplayWorldPoint centre = actorCenter(self);
    struct Entry
    {
        ActorAiTargetKind kind = ActorAiTargetKind::None;
        size_t actorIndex = 0;
        int16_t monsterId = 0;
        float distance = 0.0f;
        float height = 0.0f;
        bool hostile = false;
    };
    std::vector<Entry> entries;
    const auto edge = [&](const GameplayWorldPoint &point, float otherRadius)
    {
        const float dx = point.x - centre.x;
        const float dy = point.y - centre.y;
        const float dz = point.z - centre.z;
        return std::max(0.0f, std::sqrt(dx * dx + dy * dy + dz * dz) - script.radius - otherRadius);
    };

    if (self.hostileToParty)
    {
        const GameplayWorldPoint party = runtime.aiPartyPosition();
        entries.push_back({ActorAiTargetKind::Party, 0, 0, edge(party, runtime.aiPartyRadius()),
            party.z - self.position.z, true});
    }

    for (const ActorBehaviorAiActorView &other : runtime.aiActors())
    {
        if (other.actorIndex == self.actorIndex || other.dead || other.invisible)
        {
            continue;
        }

        const GameplayWorldPoint point = {other.position.x, other.position.y, other.position.z + other.height * 0.5f};
        entries.push_back({ActorAiTargetKind::Actor, other.actorIndex, other.monsterId, edge(point, other.radius),
            point.z - self.position.z, other.hostileToParty});
    }

    entries.erase(std::remove_if(entries.begin(), entries.end(),
        [radius](const Entry &entry) { return entry.distance > radius; }), entries.end());
    std::stable_sort(entries.begin(), entries.end(),
        [](const Entry &left, const Entry &right) { return left.distance < right.distance; });
    lua_createtable(pLuaState, int(entries.size()), 0);

    for (size_t index = 0; index < entries.size(); ++index)
    {
        const Entry &entry = entries[index];
        const bool held = entry.kind == script.heldKind
            && (entry.kind != ActorAiTargetKind::Actor || entry.actorIndex == script.heldActorIndex);
        pushMm9Target(pLuaState, entry.kind, entry.actorIndex, entry.monsterId, entry.distance,
            held ? script.targetClear : true, entry.height, entry.hostile);
        lua_rawseti(pLuaState, -2, lua_Integer(index + 1));
    }

    return 1;
}

// self:actor(index) -> {monster =, hp =, dead =, hidden =, distance = <edge>} for an actor of the last AI step, nil for
// one it did not include.
int luaSelfActor(lua_State *pLuaState)
{
    const ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    const lua_Integer actorIndex = luaL_checkinteger(pLuaState, 2);
    const GameplayWorldPoint centre = actorCenter(*context.pActor);

    for (const ActorBehaviorAiActorView &other : runtimeFromLua(pLuaState).aiActors())
    {
        if (lua_Integer(other.actorIndex) != actorIndex)
        {
            continue;
        }

        const float dx = other.position.x - centre.x;
        const float dy = other.position.y - centre.y;
        const float dz = other.position.z + other.height * 0.5f - centre.z;
        lua_createtable(pLuaState, 0, 5);
        lua_pushinteger(pLuaState, other.monsterId);
        lua_setfield(pLuaState, -2, "monster");
        lua_pushinteger(pLuaState, other.currentHp);
        lua_setfield(pLuaState, -2, "hp");
        lua_pushboolean(pLuaState, other.dead ? 1 : 0);
        lua_setfield(pLuaState, -2, "dead");
        lua_pushboolean(pLuaState, other.invisible ? 1 : 0);
        lua_setfield(pLuaState, -2, "hidden");
        const float distance = std::sqrt(dx * dx + dy * dy + dz * dz);
        lua_pushnumber(pLuaState, std::max(0.0f, distance - script.radius - other.radius));
        lua_setfield(pLuaState, -2, "distance");
        return 1;
    }

    lua_pushnil(pLuaState);
    return 1;
}

// self:setTarget("party" | actorIndex | nil): its MM9 loop holds that target from the next step (the world offers it
// whatever their relation), or drops the one it holds.
int luaSelfSetTarget(lua_State *pLuaState)
{
    ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    script.setTarget = true;
    script.targetActorIndex = static_cast<size_t>(-1);

    if (lua_isnoneornil(pLuaState, 2))
    {
        script.targetKind = ActorAiTargetKind::None;
    }
    else if (lua_type(pLuaState, 2) == LUA_TSTRING && std::strcmp(lua_tostring(pLuaState, 2), "party") == 0)
    {
        script.targetKind = ActorAiTargetKind::Party;
    }
    else
    {
        const lua_Integer actorIndex = luaL_checkinteger(pLuaState, 2);
        luaL_argcheck(pLuaState, actorIndex >= 0, 2, "actor index must not be negative");
        script.targetKind = ActorAiTargetKind::Actor;
        script.targetActorIndex = static_cast<size_t>(actorIndex);
    }

    return 0;
}

// self:attack("attack1" | "attack2" | "spell1" | "spell2"): a loop the script drives starts this attack at its target
// at the next step if its attack is ready (else it is dropped, traced as script not_ready).
int luaSelfAttack(lua_State *pLuaState)
{
    ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 2);

    if (name == "attack1")
    {
        script.attack = GameplayActorAttackAbility::Attack1;
    }
    else if (name == "attack2")
    {
        script.attack = GameplayActorAttackAbility::Attack2;
    }
    else if (name == "spell1")
    {
        script.attack = GameplayActorAttackAbility::Spell1;
    }
    else if (name == "spell2")
    {
        script.attack = GameplayActorAttackAbility::Spell2;
    }
    else
    {
        luaL_argerror(pLuaState, 2, "attack1, attack2, spell1 or spell2");
    }

    return 0;
}

// self:attackReady(): its attack has recovered and none is under way (MM9's CanAttack).
int luaSelfAttackReady(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    lua_pushboolean(pLuaState, script.viewValid && script.attackReady ? 1 : 0);
    return 1;
}

int luaSelfAttacking(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    lua_pushboolean(pLuaState, script.viewValid && script.attacking ? 1 : 0);
    return 1;
}

// self:seesParty(): it perceives the party (its sight, hearing and view; MM9's OnFoundPlayer), held or not.
int luaSelfSeesParty(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    lua_pushboolean(pLuaState, script.viewValid && script.sensesParty ? 1 : 0);
    return 1;
}

int luaSelfDormant(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    lua_pushboolean(pLuaState, script.viewValid && script.dormant ? 1 : 0);
    return 1;
}

std::optional<bool> optionalBooleanField(lua_State *pLuaState, int tableIndex, const char *pName)
{
    lua_getfield(pLuaState, tableIndex, pName);
    const std::optional<bool> value = lua_isboolean(pLuaState, -1)
        ? std::optional<bool>(lua_toboolean(pLuaState, -1) != 0) : std::nullopt;
    lua_pop(pLuaState, 1);
    return value;
}

// self:setMm9{drives_attacks =, passive =, ignores_calls =, chase_limit = <seconds, 0: none>, turn_degrees = <per
// second>, immune = "physical" | false}: how its MM9 loop runs for the script. Not saved: set it in onStart and onLoad.
int luaSelfSetMm9(lua_State *pLuaState)
{
    ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    luaL_checktype(pLuaState, 2, LUA_TTABLE);
    lua_pushnil(pLuaState);

    while (lua_next(pLuaState, 2) != 0)
    {
        const char *pKey = lua_type(pLuaState, -2) == LUA_TSTRING ? lua_tostring(pLuaState, -2) : "";
        const std::string key = pKey;
        lua_pop(pLuaState, 1);

        if (key != "drives_attacks" && key != "passive" && key != "ignores_calls" && key != "chase_limit"
            && key != "turn_degrees" && key != "immune")
        {
            luaL_error(pLuaState, "unknown setMm9 field '%s'", pKey);
        }
    }

    script.configured = true;
    script.drivesAttacks = optionalBooleanField(pLuaState, 2, "drives_attacks").value_or(script.drivesAttacks);
    script.passive = optionalBooleanField(pLuaState, 2, "passive").value_or(script.passive);
    script.ignoresCalls = optionalBooleanField(pLuaState, 2, "ignores_calls").value_or(script.ignoresCalls);
    script.chaseLimitSeconds = static_cast<float>(
        optionalNumberField(pLuaState, 2, "chase_limit").value_or(script.chaseLimitSeconds));
    script.turnRadiansPerSecond = static_cast<float>(optionalNumberField(pLuaState, 2, "turn_degrees")
        .value_or(script.turnRadiansPerSecond / (std::numbers::pi / 180.0)) * (std::numbers::pi / 180.0));
    lua_getfield(pLuaState, 2, "immune");

    if (lua_isstring(pLuaState, -1))
    {
        luaL_argcheck(pLuaState, std::strcmp(lua_tostring(pLuaState, -1), "physical") == 0, 2,
            "immune must be \"physical\" or false");
        script.immunePhysical = true;
    }
    else if (lua_isboolean(pLuaState, -1))
    {
        script.immunePhysical = false;
    }

    lua_pop(pLuaState, 1);
    return 0;
}

// self:trace(text): a decision of the script, in the decision trace as decision=script detail="<text>".
int luaSelfTrace(lua_State *pLuaState)
{
    mm9Script(pLuaState).traceLines.emplace_back(luaL_checkstring(pLuaState, 2));
    return 0;
}

// self:placement() -> script, params, summonClass: its placement's MM9 script (lower-case file name, "" for the
// row's), its ScriptParams and a summoner's class.
int luaSelfPlacement(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    lua_pushstring(pLuaState, script.script.c_str());
    lua_pushstring(pLuaState, script.scriptParams.c_str());
    lua_pushstring(pLuaState, script.summonClass.c_str());
    return 3;
}

// self:summonPoints() -> {{x, y, z}, ...}: a summoner placement's points (the scene's mm9_ai summon points).
int luaSelfSummonPoints(lua_State *pLuaState)
{
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    lua_createtable(pLuaState, int(script.summonPoints.size()), 0);

    for (size_t index = 0; index < script.summonPoints.size(); ++index)
    {
        lua_createtable(pLuaState, 3, 0);

        for (int axis = 0; axis < 3; ++axis)
        {
            lua_pushinteger(pLuaState, script.summonPoints[index][size_t(axis)]);
            lua_rawseti(pLuaState, -2, axis + 1);
        }

        lua_rawseti(pLuaState, -2, lua_Integer(index + 1));
    }

    return 1;
}

// self:push(distance): pushes the target its loop holds that far away from it (the Dragon King's wing buffet).
int luaSelfPush(lua_State *pLuaState)
{
    ActorBehaviorRuntime::LuaCallContext &context = callContext(pLuaState);
    const ActorBehaviorMm9Script &script = mm9Script(pLuaState);
    const float distance = static_cast<float>(luaL_checknumber(pLuaState, 2));
    luaL_argcheck(pLuaState, std::isfinite(distance) && distance > 0.0f, 2, "push distance must be positive");

    if (script.heldKind == ActorAiTargetKind::None)
    {
        return 0;
    }

    ActorBehaviorActorCommand command = {};
    command.kind = ActorBehaviorActorCommand::Kind::Push;
    command.actorIndex = context.pActor->actorIndex;
    command.seconds = distance;
    command.targetKind = script.heldKind;
    command.targetActorIndex = script.heldActorIndex;
    context.pResult->actorCommands.push_back(std::move(command));
    return 0;
}

const luaL_Reg SelfMethods[] = {
    {"hp", luaSelfHp},
    {"maxHp", luaSelfMaxHp},
    {"hpFraction", luaSelfHpFraction},
    {"position", luaSelfPosition},
    {"distanceToParty", luaSelfDistanceToParty},
    {"isHostile", luaSelfIsHostile},
    {"monsterId", luaSelfMonsterId},
    {"age", luaSelfAge},
    {"random", luaSelfRandom},
    {"say", luaSelfSay},
    {"playSound", luaSelfPlaySound},
    {"effect", luaSelfEffect},
    {"effectAt", luaSelfEffectAt},
    {"perform", luaSelfPerform},
    {"isPerforming", luaSelfIsPerforming},
    {"addWard", luaSelfAddWard},
    {"removeWard", luaSelfRemoveWard},
    {"hasWard", luaSelfHasWard},
    {"startTimer", luaSelfStartTimer},
    {"stopTimer", luaSelfStopTimer},
    {"hasTimer", luaSelfHasTimer},
    {"castNext", luaSelfCastNext},
    {"setSpell", luaSelfSetSpell},
    {"clearSpell", luaSelfClearSpell},
    {"setAiType", luaSelfSetAiType},
    {"setNoFlee", luaSelfSetNoFlee},
    {"summon", luaSelfSummon},
    {"summonAt", luaSelfSummonAt},
    {"blink", luaSelfBlink},
    {"suspendShield", luaSelfSuspendShield},
    {"restoreShield", luaSelfRestoreShield},
    {"leave", luaSelfLeave},
    {"setSpeed", luaSelfSetSpeed},
    {"setInvulnerable", luaSelfSetInvulnerable},
    {"qbit", luaSelfQBit},
    {"setLeash", luaSelfSetLeash},
    {"setRangedBand", luaSelfSetRangedBand},
    {"moveTo", luaSelfMoveTo},
    {"runEvent", luaSelfRunEvent},
    {"bearingToParty", luaSelfBearingToParty},
    {"setArmoredFront", luaSelfSetArmoredFront},
    {"target", luaSelfTarget},
    {"targets", luaSelfTargets},
    {"actor", luaSelfActor},
    {"setTarget", luaSelfSetTarget},
    {"attack", luaSelfAttack},
    {"attackReady", luaSelfAttackReady},
    {"attacking", luaSelfAttacking},
    {"dormant", luaSelfDormant},
    {"seesParty", luaSelfSeesParty},
    {"setMm9", luaSelfSetMm9},
    {"trace", luaSelfTrace},
    {"placement", luaSelfPlacement},
    {"summonPoints", luaSelfSummonPoints},
    {"push", luaSelfPush},
    {nullptr, nullptr},
};

void applySpellFacts(ActorStatsFacts &stats, const ActorBehaviorSpell &spell, const SpellTable *pSpellTable)
{
    stats.hasSpell1 = true;
    stats.spell1Id = spell.spellId;
    stats.spell1SkillLevel = spell.skillLevel;
    stats.spell1SkillMastery = spell.skillMastery;
    stats.spell1UseChance = spell.useChance;
    stats.spell1CastSupported = true;
    stats.spell1DamageType = GameMechanics::spellCombatDamageType(spell.spellId, pSpellTable);

    if (pSpellTable != nullptr)
    {
        if (const SpellEntry *pEntry = pSpellTable->findById(static_cast<int>(spell.spellId)))
        {
            stats.spell1Name = pEntry->name;
        }
    }
}
}

void ActorBehaviorRuntime::bind(const ActorBehaviorCatalog *pCatalog, const SpellTable *pSpellTable)
{
    if (pCatalog != m_pCatalog)
    {
        destroyLua();
    }

    m_pCatalog = pCatalog;
    m_pSpellTable = pSpellTable;
}

const SpellTable *ActorBehaviorRuntime::spellTable() const
{
    return m_pSpellTable;
}

void ActorBehaviorRuntime::reset()
{
    destroyLua();
    m_instances.clear();
    m_scannedActorCount = 0;
    m_projectileWards.clear();
    m_wardDisplays.clear();
    m_tacticAims.clear();
    m_tacticTurrets.clear();
}

void ActorBehaviorRuntime::step(IGameplayWorldRuntime &world, float deltaSeconds)
{
    if (m_pCatalog == nullptr || deltaSeconds <= 0.0f)
    {
        return;
    }

    if (m_instances.empty() && !m_pCatalog->hasMonsterDefaults())
    {
        m_scannedActorCount = static_cast<uint32_t>(world.mapActorCount());
        return;
    }

    for (auto &[actorIndex, record] : m_instances)
    {
        if (!record.mm9.placementRead)
        {
            readMm9Placement(world, actorIndex, record.mm9);
        }
    }

    const ActorBehaviorFrameResult result = update(collectFrameFacts(world, deltaSeconds));
    applyFrameResult(world, result);
}

ActorBehaviorFrameFacts ActorBehaviorRuntime::collectFrameFacts(
    const IGameplayWorldRuntime &world,
    float deltaSeconds) const
{
    ActorBehaviorFrameFacts facts = {};
    facts.deltaSeconds = deltaSeconds;
    facts.partyPosition = {world.partyX(), world.partyY(), world.partyFootZ()};
    facts.pParty = world.party();
    facts.actorCount = static_cast<uint32_t>(world.mapActorCount());

    std::vector<size_t> actorIndices;
    actorIndices.reserve(m_instances.size() + (facts.actorCount - std::min(facts.actorCount, m_scannedActorCount)));

    for (const auto &[actorIndex, record] : m_instances)
    {
        if (actorIndex < m_scannedActorCount)
        {
            actorIndices.push_back(actorIndex);
        }
    }

    for (size_t actorIndex = m_scannedActorCount; actorIndex < facts.actorCount; ++actorIndex)
    {
        actorIndices.push_back(actorIndex);
    }

    std::sort(actorIndices.begin(), actorIndices.end());
    facts.actors.reserve(actorIndices.size());

    for (const size_t actorIndex : actorIndices)
    {
        GameplayRuntimeActorState state = {};

        if (!world.actorRuntimeState(actorIndex, state))
        {
            continue;
        }

        ActorBehaviorActorFacts actor = {};
        actor.actorIndex = actorIndex;
        actor.actorId = state.actorId;
        actor.monsterId = state.monsterId;
        actor.currentHp = state.currentHp;
        actor.maxHp = state.maxHp;
        // Indoor actors report isDead only after the dying animation; health reaching zero is the death.
        actor.dead = state.isDead || (state.maxHp > 0 && state.currentHp <= 0);
        actor.hostileToParty = state.hostileToParty;
        actor.position = {state.preciseX, state.preciseY, state.preciseZ};
        actor.height = static_cast<float>(state.bodyHeight > 0 ? state.bodyHeight : state.height);
        actor.animationState = state.animationState;
        actor.yawRadians = state.yawRadians;
        facts.actors.push_back(actor);
    }

    return facts;
}

ActorBehaviorFrameResult ActorBehaviorRuntime::update(const ActorBehaviorFrameFacts &facts)
{
    ActorBehaviorFrameResult result = {};

    if (m_pCatalog == nullptr)
    {
        return result;
    }

    std::vector<size_t> seenActors;
    seenActors.reserve(facts.actors.size());

    for (const ActorBehaviorActorFacts &actor : facts.actors)
    {
        seenActors.push_back(actor.actorIndex);
        auto iterator = m_instances.find(actor.actorIndex);

        if (iterator == m_instances.end() && actor.actorIndex >= m_scannedActorCount)
        {
            const std::string *pBehaviorId = m_pCatalog->defaultBehaviorForMonster(actor.monsterId);
            std::string error;

            if (pBehaviorId != nullptr && !actor.dead && attach(actor.actorIndex, actor.actorId, *pBehaviorId, error))
            {
                iterator = m_instances.find(actor.actorIndex);
            }
            else if (!error.empty())
            {
                std::cerr << "Actor behaviour attach failed: " << error << '\n';
            }
        }

        if (iterator == m_instances.end())
        {
            continue;
        }

        if (iterator->second.state.actorId != actor.actorId)
        {
            m_instances.erase(iterator);
            continue;
        }

        updateInstance(iterator->second, actor, facts, result);
    }

    // Actors that no longer report state lose their behaviour.
    std::sort(seenActors.begin(), seenActors.end());

    for (auto iterator = m_instances.begin(); iterator != m_instances.end();)
    {
        const bool reported = std::binary_search(seenActors.begin(), seenActors.end(), iterator->first);
        iterator = reported ? std::next(iterator) : m_instances.erase(iterator);
    }

    m_scannedActorCount = std::max(m_scannedActorCount, facts.actorCount);
    rebuildProjectileWards(facts);
    return result;
}

void ActorBehaviorRuntime::applyFrameResult(IGameplayWorldRuntime &world, const ActorBehaviorFrameResult &result)
{
    EventRuntimeState *pEventRuntimeState = world.eventRuntimeState();

    if (pEventRuntimeState != nullptr)
    {
        for (const ActorBehaviorSoundRequest &sound : result.sounds)
        {
            EventRuntimeState::PendingSound request = {};
            request.soundScope = SoundScope::World;
            request.soundName = sound.soundName;
            request.x = static_cast<int32_t>(std::lround(sound.position.x));
            request.y = static_cast<int32_t>(std::lround(sound.position.y));
            request.z = static_cast<int32_t>(std::lround(sound.position.z));
            request.positional = true;
            request.hasExplicitZ = true;
            pEventRuntimeState->pendingSounds.push_back(std::move(request));
        }

        for (const ActorBehaviorEffectRequest &effect : result.effects)
        {
            EventRuntimeState::WorldEffectRequest request = {};
            request.id = effect.effectId;
            request.position = {effect.position.x, effect.position.y, effect.position.z};
            request.scale = effect.scale;
            pEventRuntimeState->worldEffectRequests.push_back(std::move(request));
        }

        for (const std::string &message : result.statusMessages)
        {
            pEventRuntimeState->statusMessages.push_back(message);
        }
    }

    for (const uint16_t eventId : result.mapEvents)
    {
        size_t previousMessageCount = 0;

        if (!world.executeMapEvent(eventId, previousMessageCount))
        {
            std::cerr << "Actor behaviour map event " << eventId << " did not run\n";
        }
    }

    for (const ActorBehaviorActorCommand &command : result.actorCommands)
    {
        switch (command.kind)
        {
            case ActorBehaviorActorCommand::Kind::Blink:
                world.blinkActor(command.actorIndex);
                break;
            case ActorBehaviorActorCommand::Kind::SuspendShield:
                world.suspendActorShield(command.actorIndex, command.seconds);
                break;
            case ActorBehaviorActorCommand::Kind::RestoreShield:
                world.restoreActorShield(command.actorIndex);
                break;
            case ActorBehaviorActorCommand::Kind::Leave:
            {
                GameplayRuntimeActorState actor = {};

                if (pEventRuntimeState != nullptr && world.actorRuntimeState(command.actorIndex, actor))
                {
                    if (!command.effectId.empty())
                    {
                        EventRuntimeState::WorldEffectRequest request = {};
                        request.id = command.effectId;
                        request.position = {actor.preciseX, actor.preciseY, actor.preciseZ + actor.height * 0.5f};
                        pEventRuntimeState->worldEffectRequests.push_back(std::move(request));
                    }

                    const uint32_t actorKey = uint32_t(command.actorIndex);
                    const uint32_t invisible = uint32_t(EvtActorAttribute::Invisible);
                    pEventRuntimeState->actorSetMasks[actorKey] |= invisible;
                    pEventRuntimeState->actorClearMasks[actorKey] &= ~invisible;
                }

                break;
            }
            case ActorBehaviorActorCommand::Kind::Push:
            {
                GameplayRuntimeActorState source = {};
                GameplayRuntimeActorState target = {};
                const bool party = command.targetKind == ActorAiTargetKind::Party;

                if (!world.actorRuntimeState(command.actorIndex, source)
                    || (!party && !world.actorRuntimeState(command.targetActorIndex, target)))
                {
                    break;
                }

                const float dx = (party ? world.partyX() : target.preciseX) - source.preciseX;
                const float dy = (party ? world.partyY() : target.preciseY) - source.preciseY;
                const float length = std::sqrt(dx * dx + dy * dy);

                if (length <= 0.001f)
                {
                    break;
                }

                if (party)
                {
                    world.dashParty(dx / length, dy / length, command.seconds);
                }
                else
                {
                    world.pushActor(command.targetActorIndex, dx / length, dy / length, command.seconds);
                }

                break;
            }
        }
    }

    for (const ActorBehaviorSummonRequest &summon : result.summons)
    {
        if (!world.summonHostileMonsterById(
                summon.monsterId,
                summon.count,
                summon.position.x,
                summon.position.y,
                summon.position.z,
                0))
        {
            std::cerr << "Actor behaviour summon failed: monster " << summon.monsterId << '\n';
        }
    }
}

void ActorBehaviorRuntime::applyAiFacts(ActorAiFrameFacts &facts)
{
    if (m_pCatalog != nullptr && m_pCatalog->hasTactics())
    {
        applyTactics(facts);
    }

    // MM9 monsters carry their row's AI profile with their placement's overrides (the MM9 loops read it).
    const bool mm9Profiles = m_pCatalog != nullptr && m_pCatalog->hasMm9AiProfiles();

    // A placement's own leash (scene leash_radius) over its monster's tactics, and a resting (dormant) one's hold.
    for (std::vector<ActorAiFacts> *pActors : {&facts.activeActors, &facts.backgroundActors})
    {
        for (ActorAiFacts &actor : *pActors)
        {
            if (mm9Profiles)
            {
                applyMm9AiProfile(actor);
            }

            if (actor.movement.dormant)
            {
                actor.behavior.holdActive = true;
                actor.behavior.holdAnimation = ActorAiAnimationState::Standing;
                actor.behavior.holdKeepsFacing = true;
            }

            if (actor.movement.placedLeashRadius > 0.0f)
            {
                actor.tactics.holdPost = true;
                actor.tactics.postLeashRadius = actor.movement.placedLeashRadius;
                actor.movement.movementAllowed = true;
            }

            // A patrol walks its waypoints as a post walks home: the waypoint is home while nothing is in reach.
            if (actor.movement.patrolTarget && !actor.movement.dormant)
            {
                actor.movement.homePosition = *actor.movement.patrolTarget;
                actor.movement.hasHomeYaw = false;
                actor.tactics.holdPost = true;
                actor.movement.movementAllowed = true;
            }
        }
    }

    if (m_instances.empty())
    {
        m_aiActors.clear();
        return;
    }

    // What MM9 boss scripts may ask of this step (self:targets): every actor's place, size and health, the party's.
    m_aiActors.clear();
    m_aiPartyPosition = {facts.party.position.x, facts.party.position.y,
        facts.party.position.z + facts.party.collisionHeight * 0.5f};
    m_aiPartyRadius = facts.party.collisionRadius;

    for (const std::vector<ActorAiFacts> *pActors : {&facts.activeActors, &facts.backgroundActors})
    {
        for (const ActorAiFacts &actor : *pActors)
        {
            m_aiActors.push_back({actor.actorIndex, actor.identity.monsterId, actor.movement.position,
                float(actor.stats.radius), float(actor.stats.height), actor.stats.currentHp,
                actor.status.hostileToParty, actor.status.dead || actor.stats.currentHp <= 0,
                actor.status.invisible});
        }
    }

    const auto applyToActor =
        [this](ActorAiFacts &actor)
        {
            const auto iterator = m_instances.find(actor.actorIndex);

            if (iterator == m_instances.end() || iterator->second.state.actorId != actor.actorId
                || iterator->second.state.deathHandled)
            {
                return;
            }

            InstanceRecord &record = iterator->second;
            const ActorBehaviorInstanceState &state = record.state;
            applyMm9Script(record, actor);

            if (state.perform && state.perform->started)
            {
                actor.behavior.holdActive = true;
                actor.behavior.holdAnimation = state.perform->fallbackAnimation;
                actor.behavior.holdRestartAnimation = record.performRestartPending;
                record.performRestartPending = false;
            }

            if (state.nextCast)
            {
                applySpellFacts(actor.stats, *state.nextCast, m_pSpellTable);
            }
            else if (state.spellOverride)
            {
                applySpellFacts(actor.stats, *state.spellOverride, m_pSpellTable);
            }

            if (state.aiTypeOverride)
            {
                actor.stats.aiType = *state.aiTypeOverride;
            }

            if (state.suppressFlee)
            {
                actor.status.suppressLowHealthFlee = true;
            }

            if (state.speedMultiplier != 1.0f)
            {
                actor.movement.effectiveMoveSpeed *= state.speedMultiplier;
                actor.behavior.attackRateMultiplier *= state.speedMultiplier;
            }

            if (state.rangedBand)
            {
                actor.tactics.rangedMinDistance = (*state.rangedBand)[0];
                actor.tactics.rangedMaxDistance = (*state.rangedBand)[1];
            }

            if (state.moveTarget)
            {
                actor.movement.homePosition = *state.moveTarget;
                actor.movement.hasHomeYaw = false;
                actor.tactics.holdPost = true;
                actor.movement.movementAllowed = true;
            }

            if (state.leashRadius)
            {
                actor.tactics.holdPost = true;
                actor.tactics.postLeashRadius = *state.leashRadius;
                actor.movement.movementAllowed = true;
            }
        };

    for (ActorAiFacts &actor : facts.activeActors)
    {
        applyToActor(actor);
    }

    for (ActorAiFacts &actor : facts.backgroundActors)
    {
        applyToActor(actor);
    }
}

void ActorBehaviorRuntime::applyMm9Script(InstanceRecord &record, ActorAiFacts &actor)
{
    ActorBehaviorMm9Script &script = record.mm9;
    ActorMm9ScriptFacts &directives = actor.behavior.mm9Script;
    directives.traceLines = std::move(script.traceLines);
    script.traceLines.clear();

    // Until its script starts (the step after this one shows it its loop) it does nothing by itself.
    if (!record.state.started)
    {
        directives.active = true;
        directives.passive = true;
    }

    if (script.configured)
    {
        directives.active = true;
        directives.drivesAttacks = script.drivesAttacks;
        directives.passive = script.passive;
        directives.ignoresCalls = script.ignoresCalls;
        directives.chaseLimitSeconds = script.chaseLimitSeconds;
        directives.turnRadiansPerSecond = script.turnRadiansPerSecond;
    }

    directives.setTarget = script.setTarget;
    directives.targetKind = script.targetKind;
    directives.targetActorIndex = script.targetActorIndex;
    directives.attack = script.attack;
    script.setTarget = false;
    script.attack.reset();

    // What this step shows the script (the AI's state after the last step), and the loop's events since then.
    const ActorMm9State &mm9 = actor.runtime.mm9;
    const bool attacking = actor.runtime.motionState == ActorAiMotionState::Attacking;
    const ActorMm9WorldFacts &world = actor.mm9World;

    if (script.viewValid)
    {
        if (mm9.targetKind != script.heldKind
            || (mm9.targetKind == ActorAiTargetKind::Actor && mm9.targetActorIndex != script.heldActorIndex))
        {
            script.events.push_back({"onTargetChanged", mm9.targetKind, mm9.targetActorIndex, {}});
        }

        if (script.attacking && !attacking)
        {
            script.events.push_back({"onAttackDone", ActorAiTargetKind::None, static_cast<size_t>(-1), {}});
        }

        if (world.damageSerial != script.damageSerial && world.attackerKind != ActorAiTargetKind::None)
        {
            script.events.push_back({"onHit", world.attackerKind, world.attackerActorIndex, {}});
        }
    }

    const bool offered = mm9.targetKind != ActorAiTargetKind::None && actor.target.currentCanSense
        && actor.target.currentKind == mm9.targetKind
        && (mm9.targetKind != ActorAiTargetKind::Actor || actor.target.currentActorIndex == mm9.targetActorIndex);
    script.viewValid = true;
    script.heldKind = mm9.targetKind;
    script.heldActorIndex = mm9.targetActorIndex;
    script.targetOffered = offered;
    script.attacking = attacking;
    script.attackReady = !attacking && actor.runtime.attackCooldownSeconds <= 0.0f;
    script.dormant = actor.movement.dormant;
    script.sensesParty = actor.target.currentKind == ActorAiTargetKind::Party && actor.target.currentCanSense;
    script.radius = float(actor.stats.radius);
    script.damageSerial = world.damageSerial;
    script.targetClear = offered && actor.target.currentHasAttackLineOfSight;

    // MM9's AIGetDistance: centre to centre (its feet plus half its height), less both radii.
    const bool party = mm9.targetKind == ActorAiTargetKind::Party;
    GameplayWorldPoint point = m_aiPartyPosition;
    float otherRadius = m_aiPartyRadius;

    for (const ActorBehaviorAiActorView &other : m_aiActors)
    {
        if (!party && other.actorIndex == mm9.targetActorIndex && !other.dead)
        {
            point = {other.position.x, other.position.y, other.position.z + other.height * 0.5f};
            otherRadius = other.radius;
        }
    }

    const float dx = point.x - actor.movement.position.x;
    const float dy = point.y - actor.movement.position.y;
    const float dz = point.z - (actor.movement.position.z + float(actor.stats.height) * 0.5f);
    script.targetDistance = std::max(0.0f, std::sqrt(dx * dx + dy * dy + dz * dz) - script.radius - otherRadius);
    script.targetHeight = point.z - actor.movement.position.z;
}

void ActorBehaviorRuntime::readMm9Placement(
    const IGameplayWorldRuntime &world, size_t actorIndex, ActorBehaviorMm9Script &script) const
{
    script.placementRead = true;
    const MapDeltaData *pMapDeltaData = world.mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size()
        || !pMapDeltaData->actors[actorIndex].mm9Ai)
    {
        return;
    }

    const Mm9AiPlacementRecord &record = *pMapDeltaData->actors[actorIndex].mm9Ai;
    script.script = record.script;
    script.scriptParams = record.scriptParams;
    script.summonClass = record.summonClass;
    script.summonPoints = record.summonPoints;
}

bool ActorBehaviorRuntime::trigger(size_t actorIndex, const std::string &message)
{
    const auto iterator = m_instances.find(actorIndex);

    if (iterator == m_instances.end() || iterator->second.state.deathHandled)
    {
        return false;
    }

    iterator->second.mm9.events.push_back({"onTrigger", ActorAiTargetKind::None, static_cast<size_t>(-1), message});
    return true;
}

const std::vector<ActorBehaviorAiActorView> &ActorBehaviorRuntime::aiActors() const
{
    return m_aiActors;
}

const GameplayWorldPoint &ActorBehaviorRuntime::aiPartyPosition() const
{
    return m_aiPartyPosition;
}

float ActorBehaviorRuntime::aiPartyRadius() const
{
    return m_aiPartyRadius;
}

float ActorBehaviorRuntime::speedMultiplier(size_t actorIndex, uint32_t actorId) const
{
    const auto iterator = m_instances.find(actorIndex);
    return iterator != m_instances.end() && iterator->second.state.actorId == actorId
        && !iterator->second.state.deathHandled ? iterator->second.state.speedMultiplier : 1.0f;
}

float ActorBehaviorRuntime::incomingDamageMultiplier(size_t actorIndex, const GameplayWorldPoint &actorPosition,
    float actorYawRadians, const GameplayWorldPoint &source) const
{
    const auto iterator = m_instances.find(actorIndex);

    if (iterator == m_instances.end() || !iterator->second.state.armoredFront)
    {
        return 1.0f;
    }

    const auto &[arc, multiplier] = *iterator->second.state.armoredFront;
    const float toSource = std::atan2(source.y - actorPosition.y, source.x - actorPosition.x);
    return std::abs(std::remainder(toSource - actorYawRadians, 2.0f * std::numbers::pi_v<float>)) <= arc
        ? multiplier : 1.0f;
}

bool ActorBehaviorRuntime::scripted(size_t actorIndex, int16_t monsterId) const
{
    return m_instances.contains(actorIndex)
        || (m_pCatalog != nullptr && m_pCatalog->defaultBehaviorForMonster(monsterId) != nullptr);
}

bool ActorBehaviorRuntime::invulnerable(size_t actorIndex, ShieldAttackTier tier) const
{
    const auto iterator = m_instances.find(actorIndex);
    return iterator != m_instances.end() && (iterator->second.state.invulnerable
        || (iterator->second.mm9.immunePhysical && tier == ShieldAttackTier::Physical));
}

void ActorBehaviorRuntime::applyTactics(ActorAiFrameFacts &facts)
{
    const float stepSeconds = facts.fixedStepSeconds;
    const auto applyToActor =
        [this, stepSeconds](ActorAiFacts &actor, bool active)
        {
            const ActorTacticsFacts *pTactics = m_pCatalog->tacticsForMonster(actor.identity.monsterId);

            if (pTactics == nullptr)
            {
                return;
            }

            actor.tactics = *pTactics;

            // Only an actor the map placed `immobile` holds a post; the same monster placed free wanders as usual.
            // A post may leave its spot to fight unless its monster is Stationary (no wander radius).
            if (!actor.movement.placedImmobile)
            {
                actor.tactics.holdPost = false;
                actor.tactics.postLeashRadius = 0.0f;
            }
            else if (actor.tactics.holdPost && actor.movement.wanderRadius > 0.0f)
            {
                actor.movement.movementAllowed = true;
            }

            // Shield broken: a hostile actor falls back from its target (the native flee) while the shield is down.
            const float shieldDownSeconds = actor.status.shieldDownSinceBreakSeconds;

            const bool fallsBack = actor.tactics.shieldBreakReaction == ActorShieldBreakReaction::FallBack
                || actor.tactics.shieldBreakReaction == ActorShieldBreakReaction::Climb;

            if (fallsBack && shieldDownSeconds >= 0.0f
                && shieldDownSeconds < actor.tactics.shieldBreakSeconds && actor.status.hostileToParty
                && !actor.status.dead && actor.target.currentKind != ActorAiTargetKind::None)
            {
                actor.status.forceFleeFromParty = true;

                if (actor.tactics.shieldBreakReaction == ActorShieldBreakReaction::Climb)
                {
                    actor.status.climbAboveTarget = ShieldBreakClimbHeight;
                }
            }

            // Shield broken: a staggering actor holds its hit pose for the reaction's seconds.
            if (actor.tactics.shieldBreakReaction == ActorShieldBreakReaction::Stagger && shieldDownSeconds >= 0.0f
                && shieldDownSeconds < actor.tactics.shieldBreakSeconds && !actor.status.dead)
            {
                actor.behavior.holdActive = true;
                actor.behavior.holdAnimation = ActorAiAnimationState::GotHit;
                actor.behavior.holdKeepsFacing = true;
            }

            // The turret state reads the last aim (its hold) before this step replaces it.
            if (actor.tactics.scan.enabled() || actor.tactics.leadSeconds > 0.0f)
            {
                updateTacticTurret(actor, active, stepSeconds);
            }

            if (active && actor.target.currentKind != ActorAiTargetKind::None && actor.target.currentCanSense
                && !actor.status.dead)
            {
                const GameplayWorldPoint &target = actor.target.currentPosition;
                const GameplayWorldPoint &lead = actor.tactics.aimLead;
                m_tacticAims[actor.actorIndex] =
                    TacticAim{actor.actorId, {target.x + lead.x, target.y + lead.y, target.z + lead.z}};
            }
            else
            {
                m_tacticAims.erase(actor.actorIndex);
            }
        };

    for (ActorAiFacts &actor : facts.activeActors)
    {
        applyToActor(actor, true);
    }

    for (ActorAiFacts &actor : facts.backgroundActors)
    {
        applyToActor(actor, false);
    }
}

void ActorBehaviorRuntime::applyMm9AiProfile(ActorAiFacts &actor) const
{
    const Mm9AiProfile *pProfile = m_pCatalog->mm9AiProfileForMonster(actor.identity.monsterId);

    if (pProfile == nullptr && actor.movement.mm9StandInCivilian)
    {
        pProfile = &mm9StandInCivilianProfile();
    }

    if (pProfile == nullptr)
    {
        return;
    }

    if (!actor.movement.mm9Placement)
    {
        actor.movement.mm9Placement = Mm9AiPlacement{};
    }

    actor.tactics.mm9Profile = placedMm9AiProfile(*pProfile, *actor.movement.mm9Placement);
    const Mm9AiProfile &placed = *actor.tactics.mm9Profile;

    // A placement script that gives or takes BaseMelee.inc's footwork (KingKong.scr on a BaseCrawl row, Honkies.scr on
    // a BaseMelee one) replaces the row's skirmisher modifier.
    if (const std::optional<Mm9AiFootwork> &footwork = actor.movement.mm9Placement->profile.footwork; footwork)
    {
        actor.tactics.skirmish = footwork->enabled;
        actor.tactics.strafeAttackChance = footwork->strafeAttackChance;
        actor.tactics.evadeChance = footwork->evadeChance;
        actor.tactics.tauntSeconds = footwork->tauntSeconds;
        actor.tactics.evadeSeconds = SkirmisherModifier{}.evadeSeconds;
        actor.tactics.backOffSeconds = SkirmisherModifier{}.backOffSeconds;
        actor.tactics.tauntChance = SkirmisherModifier{}.tauntChance;
    }

    // A crawler that evades after every attack (the Lobber Pods, lobberpod.scr: 1.8-2.2 s) runs the skirmisher's evade
    // without its strafe attacks.
    if (placed.alwaysEvade)
    {
        actor.tactics.skirmish = true;
        actor.tactics.strafeAttackChance = 0.0f;
        actor.tactics.evadeChance = 1.0f;
        actor.tactics.evadeSeconds = placed.evadeMaxSeconds > 0.0f ? placed.evadeMinSeconds : 2.0f;
        actor.tactics.evadeSecondsMax = placed.evadeMaxSeconds;
    }
}

const Mm9AiProfile *ActorBehaviorRuntime::mm9LoopProfile(int16_t monsterId, bool standInCivilian) const
{
    if (m_pCatalog == nullptr || !m_pCatalog->hasMm9AiProfiles())
    {
        return nullptr;
    }

    const Mm9AiProfile *pProfile = m_pCatalog->mm9AiProfileForMonster(monsterId);

    if (pProfile == nullptr && standInCivilian)
    {
        pProfile = &mm9StandInCivilianProfile();
    }

    return pProfile != nullptr && mm9LoopArchetype(*pProfile) ? pProfile : nullptr;
}

void ActorBehaviorRuntime::updateTacticTurret(ActorAiFacts &actor, bool active, float stepSeconds)
{
    // The lead's velocity estimate follows the target's movement over about this long (the party moves once a frame,
    // the AI steps 128 times a second), and ignores speeds above the cap (a teleport, a target swap).
    constexpr float LeadVelocitySmoothingSeconds = 0.3f;
    constexpr float MaximumLeadSpeed = 2000.0f;
    constexpr float RestartDelaySeconds = 0.4f;
    ActorTacticsFacts &tactics = actor.tactics;

    if (actor.status.dead)
    {
        m_tacticTurrets.erase(actor.actorIndex);
        return;
    }

    TacticTurret &turret = m_tacticTurrets[actor.actorIndex];

    if (turret.actorId != actor.actorId)
    {
        turret = {};
        turret.actorId = actor.actorId;
        turret.centreYawRadians = actor.movement.hasHomeYaw ? actor.movement.homeYawRadians : actor.runtime.yawRadians;
    }

    if (active && actor.target.currentKind != ActorAiTargetKind::None && actor.target.currentCanSense)
    {
        if (!turret.engaged)
        {
            turret.engaged = true;
            turret.scanning = false;
            turret.holdRemainingSeconds = 0.0f;
            turret.hasHeldAim = false;
            turret.hasTargetSample = false;
        }

        if (tactics.leadSeconds <= 0.0f)
        {
            return;
        }

        const GameplayWorldPoint &position = actor.target.currentPosition;
        const bool sameTarget = turret.hasTargetSample && turret.targetKind == actor.target.currentKind
            && turret.targetActorIndex == actor.target.currentActorIndex;
        GameplayWorldPoint &velocity = turret.targetVelocity;

        if (sameTarget && stepSeconds > 0.0f)
        {
            const float sampleX = (position.x - turret.targetSample.x) / stepSeconds;
            const float sampleY = (position.y - turret.targetSample.y) / stepSeconds;
            const float sampleZ = (position.z - turret.targetSample.z) / stepSeconds;
            const float follow = 1.0f - std::exp(-stepSeconds / LeadVelocitySmoothingSeconds);
            velocity.x += (sampleX - velocity.x) * follow;
            velocity.y += (sampleY - velocity.y) * follow;
            velocity.z += (sampleZ - velocity.z) * follow;
        }
        else
        {
            velocity = {};
        }

        turret.hasTargetSample = true;
        turret.targetSample = position;
        turret.targetKind = actor.target.currentKind;
        turret.targetActorIndex = actor.target.currentActorIndex;
        const float speed = std::sqrt(velocity.x * velocity.x + velocity.y * velocity.y + velocity.z * velocity.z);
        const float scale = speed > MaximumLeadSpeed ? 0.0f : tactics.leadSeconds;
        tactics.aimLead = {velocity.x * scale, velocity.y * scale, velocity.z * scale};
        return;
    }

    turret.hasTargetSample = false;
    turret.targetVelocity = {};

    if (turret.engaged)
    {
        // Lost its target: hold the last aim (facing and barrel) for the scan's hold time.
        turret.engaged = false;
        turret.holdRemainingSeconds = tactics.scan.holdSeconds;
        turret.heldYawRadians = actor.runtime.yawRadians;
        const auto aim = m_tacticAims.find(actor.actorIndex);
        turret.hasHeldAim = aim != m_tacticAims.end() && aim->second.actorId == actor.actorId;

        if (turret.hasHeldAim)
        {
            turret.heldAim = aim->second.point;
        }
    }

    if (!tactics.scan.enabled())
    {
        return;
    }

    if (turret.holdRemainingSeconds > 0.0f)
    {
        turret.holdRemainingSeconds -= stepSeconds;
        tactics.idleAimActive = true;
        tactics.idleAimYawRadians = turret.heldYawRadians;
        return;
    }

    turret.hasHeldAim = false;

    if (!turret.scanning)
    {
        // A fresh turret first waits its own part of a scan cycle, so neighbours never sweep in step; one back from
        // a fight sets off after a beat, from wherever it points (beyond the sweep it returns at half its traverse).
        const TurretScanSettings &scan = tactics.scan;
        const float cycleSeconds = scan.pauseMaxSeconds + 3.0f * scan.halfWidthRadians / scan.radiansPerSecond;
        const float phase = std::fmod(float(actor.actorId) * 0.618034f, 1.0f);
        const float delaySeconds = turret.scanStarts == 0 ? phase * cycleSeconds : RestartDelaySeconds;
        const float offset = std::remainder(
            actor.runtime.yawRadians - turret.centreYawRadians, 2.0f * std::numbers::pi_v<float>);
        startTurretScan(turret.scan, actor.actorId * 7919u + turret.scanStarts, offset, 0.0f, delaySeconds,
            0.5f * tactics.traverseRadiansPerSecond);
        ++turret.scanStarts;
        turret.scanning = true;
    }

    const TurretScanPose pose = advanceTurretScan(turret.scan, tactics.scan, stepSeconds);
    turret.scanPitchRadians = pose.pitchRadians;
    tactics.idleAimActive = true;
    tactics.idleAimYawRadians = std::remainder(
        turret.centreYawRadians + pose.yawOffsetRadians, 2.0f * std::numbers::pi_v<float>);
}

bool ActorBehaviorRuntime::turnsAtTraverseRate(int16_t monsterId) const
{
    if (m_pCatalog == nullptr || !m_pCatalog->hasTactics())
    {
        return false;
    }

    const ActorTacticsFacts *pTactics = m_pCatalog->tacticsForMonster(monsterId);
    return pTactics != nullptr && pTactics->traverseRadiansPerSecond > 0.0f;
}

float ActorBehaviorRuntime::postLeashRadius(int16_t monsterId) const
{
    if (m_pCatalog == nullptr || !m_pCatalog->hasTactics())
    {
        return 0.0f;
    }

    const ActorTacticsFacts *pTactics = m_pCatalog->tacticsForMonster(monsterId);
    return pTactics != nullptr && pTactics->holdPost ? pTactics->postLeashRadius : 0.0f;
}

void ActorBehaviorRuntime::observeAiResult(const ActorAiFrameResult &result)
{
    for (const ActorProjectileRequest &request : result.projectileRequests)
    {
        const auto iterator = m_instances.find(request.sourceActorIndex);

        if (iterator != m_instances.end() && iterator->second.state.nextCast
            && request.ability == GameplayActorAttackAbility::Spell1)
        {
            iterator->second.state.nextCast.reset();
        }
    }
}

void ActorBehaviorRuntime::applyPresentation(size_t actorIndex, GameplayRuntimeActorState &state) const
{
    if (!m_tacticAims.empty())
    {
        const auto aim = m_tacticAims.find(actorIndex);

        if (aim != m_tacticAims.end() && aim->second.actorId == state.actorId && !state.isDead)
        {
            state.hasAimTarget = true;
            state.aimTargetX = aim->second.point.x;
            state.aimTargetY = aim->second.point.y;
            state.aimTargetZ = aim->second.point.z;
        }
    }

    if (!m_tacticTurrets.empty() && !state.hasAimTarget && !state.isDead)
    {
        const auto turret = m_tacticTurrets.find(actorIndex);

        if (turret != m_tacticTurrets.end() && turret->second.actorId == state.actorId && !turret->second.engaged)
        {
            const TacticTurret &record = turret->second;

            if (record.holdRemainingSeconds > 0.0f && record.hasHeldAim)
            {
                // Holding its last aim: the barrel stays on it.
                state.hasAimTarget = true;
                state.aimTargetX = record.heldAim.x;
                state.aimTargetY = record.heldAim.y;
                state.aimTargetZ = record.heldAim.z;
            }
            else if (record.scanning || record.holdRemainingSeconds > 0.0f)
            {
                state.aimScanning = true;
                state.aimScanPitchRadians = record.scanPitchRadians;
            }
        }
    }

    const auto iterator = m_instances.find(actorIndex);

    if (iterator == m_instances.end() || iterator->second.state.actorId != state.actorId)
    {
        return;
    }

    const std::optional<ActorBehaviorPerform> &perform = iterator->second.state.perform;

    if (perform && perform->started && !perform->clip.empty() && !state.isDead)
    {
        state.scriptedClip = perform->clip;
        state.scriptedClipSeconds = perform->elapsedSeconds;
    }
}

const std::vector<GameplayProjectileService::ProjectileWardFacts> &ActorBehaviorRuntime::projectileWards() const
{
    return m_projectileWards;
}

const std::vector<ActorBehaviorWardDisplay> &ActorBehaviorRuntime::wardDisplays() const
{
    return m_wardDisplays;
}

void ActorBehaviorRuntime::recordWardBlock(const GameplayProjectileService::ProjectileWardBlock &block)
{
    const auto iterator = m_instances.find(block.ownerActorIndex);

    if (iterator != m_instances.end() && iterator->second.state.actorId == block.ownerActorId)
    {
        iterator->second.pendingWardBlocks.push_back(block.wardId);
        iterator->second.wardImpacts.push_back({block.wardId, block.point, 0.0f});
    }
}

bool ActorBehaviorRuntime::attach(
    size_t actorIndex,
    uint32_t actorId,
    const std::string &behaviorId,
    std::string &error)
{
    if (m_pCatalog == nullptr || m_pCatalog->findBehavior(behaviorId) == nullptr)
    {
        error = "unknown actor behaviour: " + behaviorId;
        return false;
    }

    InstanceRecord record = {};
    record.state.actorIndex = actorIndex;
    record.state.actorId = actorId;
    record.state.behaviorId = behaviorId;
    record.state.randomState = (actorId * 2654435761u) ^ hashText(behaviorId);
    const auto existing = m_instances.find(actorIndex);

    if (existing != m_instances.end())
    {
        if (m_lua)
        {
            m_lua->releaseRegistryReference(existing->second.selfReference);
            m_lua->releaseRegistryReference(existing->second.stateReference);
        }

        m_instances.erase(existing);
    }

    m_instances.emplace(actorIndex, std::move(record));
    return true;
}

bool ActorBehaviorRuntime::attachToWorldActor(
    const IGameplayWorldRuntime &world,
    size_t actorIndex,
    const std::string &behaviorId,
    std::string &error)
{
    GameplayRuntimeActorState state = {};

    if (!world.actorRuntimeState(actorIndex, state))
    {
        error = "invalid actor index " + std::to_string(actorIndex);
        return false;
    }

    const auto existing = m_instances.find(actorIndex);

    if (existing != m_instances.end() && existing->second.state.actorId == state.actorId
        && existing->second.state.behaviorId == behaviorId)
    {
        return true;
    }

    return attach(actorIndex, state.actorId, behaviorId, error);
}

const ActorBehaviorInstanceState *ActorBehaviorRuntime::instance(size_t actorIndex) const
{
    const auto iterator = m_instances.find(actorIndex);
    return iterator != m_instances.end() ? &iterator->second.state : nullptr;
}

std::vector<const ActorBehaviorInstanceState *> ActorBehaviorRuntime::instances() const
{
    std::vector<const ActorBehaviorInstanceState *> result;
    result.reserve(m_instances.size());

    for (const auto &[actorIndex, record] : m_instances)
    {
        result.push_back(&record.state);
    }

    std::sort(result.begin(), result.end(),
        [](const ActorBehaviorInstanceState *pLeft, const ActorBehaviorInstanceState *pRight)
        {
            return pLeft->actorIndex < pRight->actorIndex;
        });
    return result;
}

ActorBehaviorRuntime::Snapshot ActorBehaviorRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.scannedActorCount = m_scannedActorCount;

    for (const ActorBehaviorInstanceState *pState : instances())
    {
        snapshot.instances.push_back(*pState);
    }

    return snapshot;
}

void ActorBehaviorRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    destroyLua();
    m_instances.clear();
    m_projectileWards.clear();
    m_wardDisplays.clear();
    m_tacticAims.clear();
    m_scannedActorCount = snapshot.scannedActorCount;

    for (const ActorBehaviorInstanceState &state : snapshot.instances)
    {
        InstanceRecord record = {};
        record.state = state;
        record.needsLoadCallback = state.started;
        m_instances.emplace(state.actorIndex, std::move(record));
    }
}

ActorBehaviorRuntime::LuaCallContext *ActorBehaviorRuntime::activeCall() const
{
    return m_pActiveCall;
}

bool ActorBehaviorRuntime::ensureLua()
{
    if (m_lua)
    {
        return true;
    }

    if (m_luaFailed || m_pCatalog == nullptr)
    {
        return false;
    }

    Engine::LuaStateOwner lua;

    if (!lua.isValid())
    {
        m_luaFailed = true;
        return false;
    }

    lua.openApprovedLibraries();
    lua_State *pLuaState = lua.state();

    // Behaviours only use what the engine hands them: no file or chunk loading, and self:random() for randomness so
    // a fight replays identically from a save.
    for (const char *pName : {"dofile", "loadfile", "load", "require"})
    {
        lua_pushnil(pLuaState);
        lua_setglobal(pLuaState, pName);
    }

    lua_getglobal(pLuaState, LUA_MATHLIBNAME);
    lua_pushnil(pLuaState);
    lua_setfield(pLuaState, -2, "random");
    lua_pushnil(pLuaState);
    lua_setfield(pLuaState, -2, "randomseed");
    lua_pop(pLuaState, 1);

    lua_pushlightuserdata(pLuaState, this);
    lua_setfield(pLuaState, LUA_REGISTRYINDEX, RuntimeRegistryKey);

    luaL_newmetatable(pLuaState, SelfMetatableName);
    luaL_newlib(pLuaState, SelfMethods);
    lua_setfield(pLuaState, -2, "__index");
    lua_pop(pLuaState, 1);

    std::optional<std::string> error;

    if (!m_pCatalog->librarySource().empty()
        && !lua.runChunk(m_pCatalog->librarySource(), "@" + m_pCatalog->librarySourcePath(), error))
    {
        std::cerr << "Actor behaviour library failed: " << error.value_or("unknown error") << '\n';
        m_luaFailed = true;
        return false;
    }

    m_lua.emplace(std::move(lua));
    return true;
}

void ActorBehaviorRuntime::destroyLua()
{
    for (auto &[actorIndex, record] : m_instances)
    {
        record.selfReference = LUA_NOREF;
        record.stateReference = LUA_NOREF;
    }

    m_moduleReferences.clear();
    m_lua.reset();
    m_luaFailed = false;
}

int ActorBehaviorRuntime::moduleReference(const std::string &behaviorId)
{
    const auto cached = m_moduleReferences.find(behaviorId);

    if (cached != m_moduleReferences.end())
    {
        return cached->second;
    }

    const ActorBehaviorDefinition *pDefinition = m_pCatalog->findBehavior(behaviorId);

    if (pDefinition == nullptr || !ensureLua())
    {
        return LUA_NOREF;
    }

    lua_State *pLuaState = m_lua->state();
    const std::string chunkName = "@" + pDefinition->sourcePath;

    if (luaL_loadbuffer(pLuaState, pDefinition->source.c_str(), pDefinition->source.size(), chunkName.c_str())
        != LUA_OK)
    {
        std::cerr << "Actor behaviour load failed: " << lua_tostring(pLuaState, -1) << '\n';
        lua_pop(pLuaState, 1);
        m_moduleReferences[behaviorId] = LUA_NOREF;
        return LUA_NOREF;
    }

    // Each behaviour gets its own globals table that falls back to the shared ones.
    lua_newtable(pLuaState);
    lua_newtable(pLuaState);
    lua_pushglobaltable(pLuaState);
    lua_setfield(pLuaState, -2, "__index");
    lua_setmetatable(pLuaState, -2);
    lua_setupvalue(pLuaState, -2, 1);

    std::optional<std::string> error;

    if (!m_lua->call(0, 1, error))
    {
        std::cerr << "Actor behaviour " << behaviorId << " failed: " << error.value_or("unknown error") << '\n';
        m_moduleReferences[behaviorId] = LUA_NOREF;
        return LUA_NOREF;
    }

    if (!lua_istable(pLuaState, -1))
    {
        std::cerr << "Actor behaviour " << behaviorId << " must return Behavior.define{...}\n";
        lua_pop(pLuaState, 1);
        m_moduleReferences[behaviorId] = LUA_NOREF;
        return LUA_NOREF;
    }

    const int reference = m_lua->createRegistryReference();
    m_moduleReferences[behaviorId] = reference;
    return reference;
}

bool ActorBehaviorRuntime::ensureInstanceLua(InstanceRecord &record)
{
    if (record.failed)
    {
        return false;
    }

    if (moduleReference(record.state.behaviorId) == LUA_NOREF)
    {
        // A removed or broken script must not leave its saved wards or overrides active.
        reportScriptError(record, "behaviour script unavailable");
        return false;
    }

    lua_State *pLuaState = m_lua->state();

    if (record.selfReference == LUA_NOREF)
    {
        lua_newtable(pLuaState);
        lua_pushinteger(pLuaState, static_cast<lua_Integer>(record.state.actorIndex));
        lua_setfield(pLuaState, -2, SelfActorKey);
        luaL_setmetatable(pLuaState, SelfMetatableName);
        record.selfReference = m_lua->createRegistryReference();
    }

    if (record.stateReference == LUA_NOREF)
    {
        const int top = lua_gettop(pLuaState);
        size_t offset = 0;

        if (record.state.scriptState.empty())
        {
            lua_newtable(pLuaState);
        }
        else if (!deserializeLuaValue(pLuaState, record.state.scriptState, offset, 0) || !lua_istable(pLuaState, -1))
        {
            lua_settop(pLuaState, top);
            lua_newtable(pLuaState);
            std::cerr << "Actor behaviour state of actor " << record.state.actorIndex << " was unreadable; reset\n";
        }

        record.stateReference = m_lua->createRegistryReference();
    }

    return true;
}

bool ActorBehaviorRuntime::pushHandler(InstanceRecord &record, const char *pHandlerName, const char *pTableKey)
{
    if (!ensureInstanceLua(record))
    {
        return false;
    }

    lua_State *pLuaState = m_lua->state();
    const int top = lua_gettop(pLuaState);
    m_lua->pushRegistryReference(m_moduleReferences.at(record.state.behaviorId));
    lua_getfield(pLuaState, -1, pHandlerName);

    // A handler table (onTimer = {name = fn}) is indexed by the key; a plain function handles every key.
    if (pTableKey != nullptr && lua_istable(pLuaState, -1))
    {
        lua_getfield(pLuaState, -1, pTableKey);
        lua_remove(pLuaState, -2);
    }

    if (!lua_isfunction(pLuaState, -1))
    {
        lua_settop(pLuaState, top);
        return false;
    }

    lua_remove(pLuaState, -2);
    return true;
}

bool ActorBehaviorRuntime::callPushedHandler(
    InstanceRecord &record,
    const ActorBehaviorActorFacts &actor,
    const ActorBehaviorFrameFacts &facts,
    ActorBehaviorFrameResult &result,
    const char *pHandlerName,
    int argumentCount,
    const std::function<void(lua_State *)> &pushArguments)
{
    lua_State *pLuaState = m_lua->state();
    const int top = lua_gettop(pLuaState) - 1;
    m_lua->pushRegistryReference(record.selfReference);
    m_lua->pushRegistryReference(record.stateReference);

    if (pushArguments)
    {
        pushArguments(pLuaState);
    }

    LuaCallContext context = {};
    context.pState = &record.state;
    context.pActor = &actor;
    context.pResult = &result;
    context.partyPosition = facts.partyPosition;
    context.pParty = facts.pParty;
    context.pMm9 = &record.mm9;
    m_pActiveCall = &context;
    std::optional<std::string> error;
    const bool called = m_lua->call(2 + argumentCount, 0, error);
    m_pActiveCall = nullptr;

    if (!called)
    {
        lua_settop(pLuaState, top);
        reportScriptError(record, std::string(pHandlerName) + ": " + error.value_or("unknown error"));
        return false;
    }

    std::vector<uint8_t> serialized;
    std::string serializeError;
    m_lua->pushRegistryReference(record.stateReference);

    if (serializeLuaValue(pLuaState, -1, serialized, 0, serializeError))
    {
        record.state.scriptState = std::move(serialized);
    }
    else
    {
        reportScriptError(record, serializeError);
    }

    lua_settop(pLuaState, top);
    return true;
}

bool ActorBehaviorRuntime::callHandler(
    InstanceRecord &record,
    const ActorBehaviorActorFacts &actor,
    const ActorBehaviorFrameFacts &facts,
    ActorBehaviorFrameResult &result,
    const char *pHandlerName,
    const char *pTableKey,
    int argumentCount,
    const std::function<void(lua_State *)> &pushArguments)
{
    if (record.failed || !pushHandler(record, pHandlerName, pTableKey))
    {
        return false;
    }

    return callPushedHandler(record, actor, facts, result, pHandlerName, argumentCount, pushArguments);
}

void ActorBehaviorRuntime::updateInstance(
    InstanceRecord &record,
    const ActorBehaviorActorFacts &actor,
    const ActorBehaviorFrameFacts &facts,
    ActorBehaviorFrameResult &result)
{
    ActorBehaviorInstanceState &state = record.state;
    const float deltaSeconds = facts.deltaSeconds;
    const auto call =
        [&](const char *pHandlerName, const char *pTableKey, int argumentCount,
            const std::function<void(lua_State *)> &pushArguments)
        {
            return callHandler(record, actor, facts, result, pHandlerName, pTableKey, argumentCount, pushArguments);
        };

    // An MM9 monster's script starts once an AI step has shown it its loop (its target, dormant start, attack).
    if (!state.started && !record.mm9.viewValid && m_pCatalog->mm9AiProfileForMonster(actor.monsterId) != nullptr)
    {
        return;
    }

    if (!state.started)
    {
        state.started = true;
        state.lastHp = actor.currentHp;
        call("onStart", nullptr, 0, {});
    }
    else if (record.needsLoadCallback)
    {
        record.needsLoadCallback = false;

        if (!state.deathHandled)
        {
            call("onLoad", nullptr, 0, {});
        }
    }

    if (state.deathHandled)
    {
        return;
    }

    if (actor.dead)
    {
        state.deathHandled = true;
        state.perform.reset();
        state.wards.clear();
        state.timers.clear();
        state.nextCast.reset();
        call("onDeath", nullptr, 0, {});
        return;
    }

    state.ageSeconds += deltaSeconds;

    // An MM9 boss script's loop events since the last step (phase 5): a target the loop took or lost, the end of an
    // attack, a hit and its attacker, a map trigger.
    std::vector<ActorBehaviorMm9Script::Event> events = std::move(record.mm9.events);
    record.mm9.events.clear();

    for (const ActorBehaviorMm9Script::Event &event : events)
    {
        if (event.handler == "onTrigger")
        {
            call("onTrigger", nullptr, 1,
                [&event](lua_State *pLuaState) { lua_pushstring(pLuaState, event.text.c_str()); });
        }
        else if (event.handler == "onAttackDone")
        {
            call("onAttackDone", nullptr, 0, {});
        }
        else
        {
            const ActorBehaviorMm9Script &script = record.mm9;
            call(event.handler.c_str(), nullptr, 1,
                [&event, &script](lua_State *pLuaState)
                {
                    if (event.targetKind == ActorAiTargetKind::None)
                    {
                        lua_pushnil(pLuaState);
                        return;
                    }

                    const bool held = event.targetKind == script.heldKind
                        && event.targetActorIndex == script.heldActorIndex;
                    pushMm9Target(pLuaState, event.targetKind, event.targetActorIndex, 0,
                        held ? script.targetDistance : 0.0f, held && script.targetClear,
                        held ? script.targetHeight : 0.0f, true);
                });
        }
    }

    if (actor.currentHp < state.lastHp)
    {
        const int damage = state.lastHp - actor.currentHp;
        state.lastHp = actor.currentHp;
        call("onDamaged", nullptr, 1, [damage](lua_State *pLuaState) { lua_pushinteger(pLuaState, damage); });
        fireHealthThresholds(record, actor, facts, result);
    }
    else
    {
        state.lastHp = actor.currentHp;
    }

    std::vector<std::string> wardBlocks = std::move(record.pendingWardBlocks);
    record.pendingWardBlocks.clear();

    for (const std::string &wardId : wardBlocks)
    {
        call("onWardBlocked", nullptr, 1,
            [&wardId](lua_State *pLuaState) { lua_pushstring(pLuaState, wardId.c_str()); });
    }

    if (state.perform)
    {
        if (!state.perform->started && !actorIsBusy(actor.animationState))
        {
            state.perform->started = true;
            state.perform->elapsedSeconds = 0.0f;
            record.performRestartPending = true;
        }
        else if (state.perform->started)
        {
            state.perform->elapsedSeconds += deltaSeconds;

            if (state.perform->elapsedSeconds >= state.perform->durationSeconds)
            {
                const std::string clip = state.perform->clip;
                state.perform.reset();
                call("onPerformDone", nullptr, 1,
                    [&clip](lua_State *pLuaState) { lua_pushstring(pLuaState, clip.c_str()); });
            }
        }
    }

    constexpr float WardImpactSeconds = 0.8f;

    for (InstanceRecord::WardImpact &impact : record.wardImpacts)
    {
        impact.ageSeconds += deltaSeconds;
    }

    record.wardImpacts.erase(std::remove_if(record.wardImpacts.begin(), record.wardImpacts.end(),
        [](const InstanceRecord::WardImpact &impact) { return impact.ageSeconds > WardImpactSeconds; }),
        record.wardImpacts.end());

    for (size_t wardIndex = 0; wardIndex < state.wards.size();)
    {
        ActorBehaviorWard &ward = state.wards[wardIndex];
        ward.ageSeconds += deltaSeconds;

        if (!ward.effectId.empty())
        {
            ward.effectCooldownSeconds -= deltaSeconds;

            if (ward.effectCooldownSeconds <= 0.0f)
            {
                ward.effectCooldownSeconds = ward.effectIntervalSeconds;
                result.effects.push_back({ward.effectId, actorCenter(actor), ward.effectScale});
            }
        }

        if (ward.remainingSeconds >= 0.0f)
        {
            ward.remainingSeconds -= deltaSeconds;

            if (ward.remainingSeconds <= 0.0f)
            {
                const std::string wardId = ward.id;
                state.wards.erase(state.wards.begin() + static_cast<std::ptrdiff_t>(wardIndex));
                call("onWardExpired", nullptr, 1,
                    [&wardId](lua_State *pLuaState) { lua_pushstring(pLuaState, wardId.c_str()); });
                continue;
            }
        }

        ++wardIndex;
    }

    std::vector<std::string> expiredTimers;

    for (ActorBehaviorTimer &timer : state.timers)
    {
        timer.remainingSeconds -= deltaSeconds;

        if (timer.remainingSeconds <= 0.0f)
        {
            expiredTimers.push_back(timer.name);
        }
    }

    for (const std::string &name : expiredTimers)
    {
        state.timers.erase(std::remove_if(state.timers.begin(), state.timers.end(),
            [&](const ActorBehaviorTimer &timer) { return timer.name == name && timer.remainingSeconds <= 0.0f; }),
            state.timers.end());
        call("onTimer", name.c_str(), 1,
            [&name](lua_State *pLuaState) { lua_pushstring(pLuaState, name.c_str()); });
    }

    state.thinkCooldownSeconds -= deltaSeconds;

    if (state.thinkCooldownSeconds <= 0.0f && !record.failed && ensureInstanceLua(record))
    {
        lua_State *pLuaState = m_lua->state();
        m_lua->pushRegistryReference(m_moduleReferences.at(state.behaviorId));
        lua_getfield(pLuaState, -1, "think_interval");
        const float interval = lua_isnumber(pLuaState, -1)
            ? std::max(0.05f, static_cast<float>(lua_tonumber(pLuaState, -1))) : DefaultThinkIntervalSeconds;
        lua_pop(pLuaState, 2);
        state.thinkCooldownSeconds = interval;
        call("onThink", nullptr, 0, {});
    }
}

// onHealthBelow = {[0.6] = fn, [0.3] = fn}: each fires once, highest first, when health falls to or below it.
void ActorBehaviorRuntime::fireHealthThresholds(
    InstanceRecord &record,
    const ActorBehaviorActorFacts &actor,
    const ActorBehaviorFrameFacts &facts,
    ActorBehaviorFrameResult &result)
{
    if (record.failed || actor.maxHp <= 0 || !ensureInstanceLua(record))
    {
        return;
    }

    lua_State *pLuaState = m_lua->state();
    const int top = lua_gettop(pLuaState);
    m_lua->pushRegistryReference(m_moduleReferences.at(record.state.behaviorId));
    lua_getfield(pLuaState, -1, "onHealthBelow");

    if (!lua_istable(pLuaState, -1))
    {
        lua_settop(pLuaState, top);
        return;
    }

    const double fraction = double(actor.currentHp) / double(actor.maxHp);
    // Keys stay exact Lua numbers for the lookup below; the saved fired list holds them as floats.
    const std::vector<float> &fired = record.state.firedHealthThresholds;
    std::vector<lua_Number> crossed;
    lua_pushnil(pLuaState);

    while (lua_next(pLuaState, -2) != 0)
    {
        if (lua_type(pLuaState, -2) == LUA_TNUMBER && lua_isfunction(pLuaState, -1))
        {
            const lua_Number threshold = lua_tonumber(pLuaState, -2);

            if (fraction <= threshold
                && std::find(fired.begin(), fired.end(), static_cast<float>(threshold)) == fired.end())
            {
                crossed.push_back(threshold);
            }
        }

        lua_pop(pLuaState, 1);
    }

    lua_settop(pLuaState, top);
    std::sort(crossed.begin(), crossed.end(), std::greater<lua_Number>());

    for (const lua_Number threshold : crossed)
    {
        record.state.firedHealthThresholds.push_back(static_cast<float>(threshold));

        if (record.failed || !ensureInstanceLua(record))
        {
            return;
        }

        m_lua->pushRegistryReference(m_moduleReferences.at(record.state.behaviorId));
        lua_getfield(pLuaState, -1, "onHealthBelow");
        lua_pushnumber(pLuaState, threshold);
        lua_gettable(pLuaState, -2);

        if (!lua_isfunction(pLuaState, -1))
        {
            lua_settop(pLuaState, top);
            continue;
        }

        lua_replace(pLuaState, top + 1);
        lua_settop(pLuaState, top + 1);
        callPushedHandler(record, actor, facts, result, "onHealthBelow", 1,
            [threshold](lua_State *pState) { lua_pushnumber(pState, threshold); });
    }
}

void ActorBehaviorRuntime::rebuildProjectileWards(const ActorBehaviorFrameFacts &facts)
{
    m_projectileWards.clear();
    m_wardDisplays.clear();

    for (const ActorBehaviorActorFacts &actor : facts.actors)
    {
        const auto iterator = m_instances.find(actor.actorIndex);

        if (iterator == m_instances.end() || actor.dead)
        {
            continue;
        }

        for (const ActorBehaviorWard &ward : iterator->second.state.wards)
        {
            GameplayProjectileService::ProjectileWardFacts wardFacts = {};
            wardFacts.ownerActorIndex = actor.actorIndex;
            wardFacts.ownerActorId = actor.actorId;
            wardFacts.center = actorCenter(actor);
            wardFacts.radius = ward.radius;
            wardFacts.wardId = ward.id;
            m_projectileWards.push_back(std::move(wardFacts));

            if (!ward.visual.dome)
            {
                continue;
            }

            ActorBehaviorWardDisplay display = {};
            display.actorId = actor.actorId;
            display.wardId = ward.id;
            display.center = actorCenter(actor);
            display.radius = ward.radius;
            display.groundZ = actor.position.z;
            display.ageSeconds = ward.ageSeconds;
            display.remainingSeconds = ward.remainingSeconds;
            display.visual = ward.visual;

            for (const InstanceRecord::WardImpact &impact : iterator->second.wardImpacts)
            {
                const float dx = impact.point.x - display.center.x;
                const float dy = impact.point.y - display.center.y;
                const float dz = impact.point.z - display.center.z;
                const float length = std::sqrt(dx * dx + dy * dy + dz * dz);

                if (impact.wardId == ward.id && length > 0.001f)
                {
                    display.impacts.push_back({{dx / length, dy / length, dz / length}, impact.ageSeconds});
                }
            }

            m_wardDisplays.push_back(std::move(display));
        }
    }
}

void ActorBehaviorRuntime::reportScriptError(InstanceRecord &record, const std::string &message)
{
    std::cerr << "Actor behaviour " << record.state.behaviorId << " (actor " << record.state.actorIndex
              << ") stopped: " << message << '\n';
    record.failed = true;
    record.state.perform.reset();
    record.state.wards.clear();
    record.state.nextCast.reset();
    record.state.spellOverride.reset();
}
}
