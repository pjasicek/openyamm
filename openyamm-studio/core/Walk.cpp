#include "core/Walk.h"

#include "core/CanonicalYaml.h"
#include "core/CoreMath.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"
#include "game/events/EvtEnums.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/tables/MapStats.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
// The game's party movement, read from its sources on 2026-11-14 (they are local constants there): the movement step
// and accumulator cap of IndoorPartyRuntime.cpp and OutdoorMovementDriver.cpp, the walk and run speeds and the jump of
// GameApplication's input, the party gravity of IndoorPartyRuntime.cpp, the outdoor flight values of
// OutdoorMovementDriver.cpp. The body sizes come from the controllers' own defaults and world.yml (WalkParty).
constexpr float MovementStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedMovementSeconds = 0.1f;
constexpr float WalkSpeed = 384.0f;
constexpr float RunForwardMultiplier = 2.0f;
constexpr float StrafeMultiplier = 0.5f;
constexpr float JumpVelocity = 480.0f;
constexpr float IndoorJumpLift = 0.0f;
constexpr float OutdoorJumpLift = 1.0f;
constexpr float PartyGravityPerSecond = 1280.0f;
constexpr float OutdoorFlyVerticalSpeed = 1536.0f;
constexpr float DefaultFlightCeiling = 4000.0f;
// The MM6-MM8 outdoor party (GameApplication.cpp DefaultOutdoorParty*), when world.yml declares none.
constexpr float DefaultOutdoorRadius = 37.0f;
constexpr float DefaultOutdoorHeight = 192.0f;
constexpr float DefaultOutdoorMaxStepHeight = 128.0f;
constexpr float DefaultOutdoorEyeHeight = 176.0f;
// IndoorWorldRuntime: a decoration's sector is found this far above its foot.
constexpr float DecorationSectorProbeLift = 32.0f;
const char *const HeaderKey = "studio_walk";

bool loadDecorationTable(const std::string &text, Game::DecorationTable &table)
{
    const std::optional<Engine::TextTable> parsed = Engine::TextTable::parseTabSeparated(text);

    if (!parsed)
    {
        return false;
    }

    std::vector<std::vector<std::string>> rows;

    for (size_t rowIndex = 0; rowIndex < parsed->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsed->getRow(rowIndex));
    }

    return table.loadRows(rows);
}

// As MapAssetLoader's shouldSkipDecorationCollision (the outdoor colliders).
bool skipOutdoorDecoration(const Game::DecorationEntry &decoration)
{
    using Game::DecorationDescFlag;

    if (Game::hasDecorationFlag(decoration.flags, DecorationDescFlag::MoveThrough)
        || Game::hasDecorationFlag(decoration.flags, DecorationDescFlag::DontDraw))
    {
        return true;
    }

    if (decoration.spriteId == 0 || decoration.internalName.rfind("plant", 0) == 0)
    {
        return true;
    }

    return decoration.radius <= 0 || decoration.height == 0;
}

uint32_t floatBits(float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

// The studio's block at the head of <stem>.walk.yml: its own lines only, so the scene after it is parsed once (by the
// game's reader).
YAML::Node readHeader(const std::string &text, std::string &errorMessage)
{
    const std::string start = std::string(HeaderKey) + ":";
    const size_t at = text.find(start);

    if (at == std::string::npos || (at > 0 && text[at - 1] != '\n'))
    {
        errorMessage = "the movement state has no studio_walk block (built before S5a4: build again)";
        return {};
    }

    size_t end = text.find('\n', at);

    while (end != std::string::npos && end + 1 < text.size() && (text[end + 1] == ' ' || text[end + 1] == '\n'))
    {
        end = text.find('\n', end + 1);
    }

    try
    {
        const YAML::Node root = YAML::Load(text.substr(at, end == std::string::npos ? std::string::npos : end - at));
        return root[HeaderKey];
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = std::string("the studio_walk block does not parse: ") + exception.what();
        return {};
    }
}
}

struct WalkSession::Impl
{
    bool loaded = false;
    bool outdoor = false;
    WalkParty party;
    std::vector<WalkDoor> doors;
    std::vector<std::pair<int, std::string>> rooms;
    std::vector<std::array<uint32_t, 3>> faceAttributes;
    size_t faces = 0;
    size_t decorationColliders = 0;

    // Indoor. The controller keeps pointers to these: they never move after load.
    Game::IndoorMapData indoorMap;
    std::optional<Game::MapDeltaData> indoorDelta;
    std::optional<Game::EventRuntimeState> eventState;
    std::unique_ptr<Game::IndoorMovementController> pIndoor;
    Game::IndoorMoveState indoorState;
    Game::IndoorBodyDimensions indoorBody;

    // Outdoor.
    Game::OutdoorMapData outdoorMap;
    std::unique_ptr<Game::OutdoorMovementController> pOutdoor;
    Game::OutdoorMoveState outdoorState;
    Game::OutdoorBodyDimensions outdoorBody;
    float flightCeiling = DefaultFlightCeiling;

    float accumulator = 0.0f;
    bool landed = false;
    std::vector<size_t> contacts;

    bool loadIndoor(const std::vector<uint8_t> &mapBytes, const std::string &stateText,
        const std::string &decorationTableText, std::string &errorMessage);
    bool loadOutdoor(const std::vector<uint8_t> &mapBytes, const std::string &stateText,
        const std::string &decorationTableText, const std::vector<uint8_t> &terrainPack,
        const std::optional<Game::MapBounds> &bounds, std::string &errorMessage);
};

bool WalkSession::Impl::loadIndoor(const std::vector<uint8_t> &mapBytes, const std::string &stateText,
    const std::string &decorationTableText, std::string &errorMessage)
{
    std::optional<Game::IndoorMapData> map = Game::IndoorMapDataLoader().loadFromBytes(mapBytes);

    if (!map)
    {
        errorMessage = "the map is not a BLV the game reads";
        return false;
    }

    indoorMap = std::move(*map);
    const std::optional<Game::IndoorSceneData> scene = Game::IndoorSceneYmlLoader().loadFromText(stateText,
        errorMessage);

    if (!scene)
    {
        errorMessage = "the movement state does not read: " + errorMessage;
        return false;
    }

    Game::MapDeltaData delta;

    if (!Game::buildIndoorMapStateFromScene(*scene, indoorMap, delta, errorMessage))
    {
        errorMessage = "the movement state does not apply to the map: " + errorMessage;
        return false;
    }

    indoorDelta = std::move(delta);
    pIndoor = std::make_unique<Game::IndoorMovementController>(indoorMap, &indoorDelta, &eventState);
    pIndoor->setSlopeRule(indoorMap.partySteepSlopesBlock ? Game::IndoorSlopeRule::Actor
                                                         : Game::IndoorSlopeRule::Party);
    indoorBody.radius = party.radius;
    indoorBody.height = party.height;

    // Decoration colliders, as IndoorWorldRuntime::decorationMovementColliders over the decorations' billboards (their
    // sector found as the billboard loader finds it). Decorations an event hides are not hidden here.
    Game::DecorationTable table;

    if (!loadDecorationTable(decorationTableText, table))
    {
        errorMessage = "the decoration table does not read";
        return false;
    }

    std::vector<Game::IndoorCylinderCollision> colliders;
    Game::IndoorFaceGeometryCache geometryCache(indoorMap.faces.size());

    for (size_t entityIndex = 0; entityIndex < indoorMap.entities.size(); ++entityIndex)
    {
        const Game::IndoorEntity &entity = indoorMap.entities[entityIndex];
        const Game::DecorationEntry *pEntry = table.resolveMapDecoration(entity.decorationListId, entity.name).pEntry;

        if (pEntry == nullptr || pEntry->radius <= 0 || pEntry->height == 0)
        {
            continue;
        }

        const bool emitter = Game::hasDecorationFlag(pEntry->flags, Game::DecorationDescFlag::EmitFire)
            || Game::hasDecorationFlag(pEntry->flags, Game::DecorationDescFlag::EmitSmoke);

        if ((pEntry->spriteId == 0 && !emitter)
            || Game::hasDecorationFlag(pEntry->flags, Game::DecorationDescFlag::MoveThrough)
            || Game::hasDecorationFlag(pEntry->flags, Game::DecorationDescFlag::DontDraw))
        {
            continue;
        }

        const std::optional<int16_t> sector = Game::findIndoorSectorForPoint(indoorMap, indoorMap.vertices,
            {float(entity.x), float(entity.y), float(entity.z) + DecorationSectorProbeLift}, &geometryCache);
        colliders.push_back(Game::IndoorCylinderCollision{entityIndex, sector.value_or(int16_t(-1)), float(entity.x),
            float(entity.y), float(entity.z), float(pEntry->radius), float(pEntry->height)});
    }

    pIndoor->setDecorationColliders(colliders);
    decorationColliders = colliders.size();
    faces = indoorMap.faces.size();

    // Each door's state as the scene starts it.
    for (WalkDoor &door : doors)
    {
        for (const Game::MapDeltaDoor &mapDoor : indoorDelta->doors)
        {
            if (!door.mechanisms.empty() && mapDoor.doorId == door.mechanisms.front())
            {
                door.open = mapDoor.state == uint16_t(Game::EvtMechanismState::Open);
            }
        }
    }

    // The party where the scene starts it, until placed.
    const Game::IndoorPartyStartPoint start = indoorMap.partyStartPoint.value_or(Game::IndoorPartyStartPoint{});
    indoorState = pIndoor->initializeStateFromEyePosition(float(start.x), float(start.y),
        float(start.z) + party.eyeHeight, indoorBody);
    return true;
}

bool WalkSession::Impl::loadOutdoor(const std::vector<uint8_t> &mapBytes, const std::string &stateText,
    const std::string &decorationTableText, const std::vector<uint8_t> &terrainPack,
    const std::optional<Game::MapBounds> &bounds, std::string &errorMessage)
{
    std::optional<Game::OutdoorMapData> map = Game::OutdoorMapDataLoader().loadFromBytes(mapBytes);

    if (!map)
    {
        errorMessage = "the map is not an ODM the game reads";
        return false;
    }

    outdoorMap = std::move(*map);
    const std::optional<Game::OutdoorSceneData> scene = Game::OutdoorSceneYmlLoader().loadFromText(stateText,
        errorMessage);

    if (!scene)
    {
        errorMessage = "the movement state does not read: " + errorMessage;
        return false;
    }

    Game::MapDeltaData delta;

    if (!Game::buildOutdoorMapStateFromScene(*scene, outdoorMap, delta, errorMessage))
    {
        errorMessage = "the movement state does not apply to the map: " + errorMessage;
        return false;
    }

    for (const std::array<uint32_t, 3> &change : faceAttributes)
    {
        if (change[0] >= outdoorMap.bmodels.size() || change[1] >= outdoorMap.bmodels[change[0]].faces.size())
        {
            errorMessage = "the movement state names a face the map lacks";
            return false;
        }

        outdoorMap.bmodels[change[0]].faces[change[1]].attributes = change[2];
    }

    // The terrain pack: the tile attributes after the tile table's flags, and the land mask.
    uint32_t attributeSize = 0;
    uint32_t maskSize = 0;

    if (terrainPack.size() < 12 || std::memcmp(terrainPack.data(), "OYWT", 4) != 0
        || (std::memcpy(&attributeSize, terrainPack.data() + 4, 4), size_t(attributeSize) + 12 > terrainPack.size())
        || (std::memcpy(&maskSize, terrainPack.data() + 8 + attributeSize, 4),
            size_t(attributeSize) + 12 + maskSize != terrainPack.size()))
    {
        errorMessage = "no terrain pack (<stem>.walk.terrain), or not one";
        return false;
    }

    outdoorMap.attributeMap.assign(terrainPack.begin() + 8, terrainPack.begin() + 8 + attributeSize);
    std::optional<std::vector<uint8_t>> landMask;

    if (maskSize > 0)
    {
        landMask = std::vector<uint8_t>(terrainPack.begin() + 12 + attributeSize, terrainPack.end());
    }

    // Decoration colliders, as MapAssetLoader's outdoor collision set. Decorations an event hides stay.
    Game::DecorationTable table;

    if (!loadDecorationTable(decorationTableText, table))
    {
        errorMessage = "the decoration table does not read";
        return false;
    }

    Game::OutdoorDecorationCollisionSet decorations;

    for (size_t entityIndex = 0; entityIndex < outdoorMap.entities.size(); ++entityIndex)
    {
        const Game::OutdoorEntity &entity = outdoorMap.entities[entityIndex];
        const Game::DecorationLookupResult lookup = table.resolveMapDecoration(entity.decorationListId, entity.name);

        if (lookup.pEntry == nullptr || skipOutdoorDecoration(*lookup.pEntry))
        {
            continue;
        }

        Game::OutdoorDecorationCollision collision = {};
        collision.entityIndex = entityIndex;
        collision.decorationId = lookup.decorationId;
        collision.descriptionFlags = lookup.pEntry->flags;
        collision.instanceFlags = entity.aiAttributes;
        collision.radius = lookup.pEntry->radius;
        collision.height = lookup.pEntry->height;
        collision.worldX = entity.x;
        collision.worldY = entity.y;
        collision.worldZ = entity.z;
        collision.name = entity.name.empty() ? lookup.pEntry->internalName : entity.name;
        decorations.colliders.push_back(std::move(collision));
    }

    decorationColliders = decorations.colliders.size();
    const std::optional<Game::OutdoorDecorationCollisionSet> decorationSet =
        decorations.colliders.empty() ? std::nullopt : std::optional(decorations);
    pOutdoor = std::make_unique<Game::OutdoorMovementController>(outdoorMap, bounds, landMask, decorationSet,
        std::nullopt, std::nullopt);
    flightCeiling = outdoorMap.flightCeiling.value_or(DefaultFlightCeiling);
    outdoorBody.radius = party.radius;
    outdoorBody.height = party.height;
    outdoorBody.maxStepHeight = party.maxStepHeight;
    faces = 0;

    for (const Game::OutdoorBModel &model : outdoorMap.bmodels)
    {
        faces += model.faces.size();
    }

    // The party at the map's middle, until placed.
    outdoorState = pOutdoor->initializePartyArrivalState(0.0f, 0.0f, Game::sampleOutdoorTerrainHeight(outdoorMap,
        0.0f, 0.0f), outdoorBody.radius, outdoorBody.maxStepHeight, false);
    return true;
}

WalkSession::WalkSession()
    : m_pImpl(std::make_unique<Impl>())
{
}

WalkSession::~WalkSession() = default;

bool WalkSession::load(const std::vector<uint8_t> &mapBytes, const std::string &stateText,
    const std::string &decorationTableText, const std::vector<uint8_t> &terrainPack, std::string &errorMessage)
{
    m_pImpl = std::make_unique<Impl>();
    Impl &impl = *m_pImpl;
    const YAML::Node header = readHeader(stateText, errorMessage);

    if (!header.IsMap())
    {
        if (errorMessage.empty())
        {
            errorMessage = "the studio_walk block is not a mapping";
        }

        return false;
    }

    try
    {
        const std::string kind = header["kind"].as<std::string>("");

        if (kind != "indoor" && kind != "outdoor")
        {
            errorMessage = "the movement state's kind is neither indoor nor outdoor";
            return false;
        }

        impl.outdoor = kind == "outdoor";

        if (const YAML::Node party = header["party"]; party && party.IsMap())
        {
            impl.party.radius = party["radius"].as<float>(impl.party.radius);
            impl.party.height = party["height"].as<float>(impl.party.height);
            impl.party.eyeHeight = party["eye_height"].as<float>(impl.party.eyeHeight);
            impl.party.maxStepHeight = party["max_step_height"].as<float>(impl.party.maxStepHeight);
        }

        for (const YAML::Node &doorNode : header["doors"])
        {
            WalkDoor door;
            door.id = doorNode["id"].as<std::string>("");

            for (const YAML::Node &mechanism : doorNode["mechanisms"])
            {
                door.mechanisms.push_back(mechanism.as<uint32_t>());
            }

            impl.doors.push_back(std::move(door));
        }

        for (const YAML::Node &roomNode : header["rooms"])
        {
            impl.rooms.emplace_back(roomNode["sector"].as<int>(-1), roomNode["id"].as<std::string>(""));
        }

        if (const YAML::Node faces = header["face_attributes"]; faces && faces.IsSequence())
        {
            for (const YAML::Node &face : faces)
            {
                impl.faceAttributes.push_back({face[0].as<uint32_t>(), face[1].as<uint32_t>(), face[2].as<uint32_t>()});
            }
        }

        std::optional<Game::MapBounds> bounds;

        if (const YAML::Node boundsNode = header["bounds"];
            boundsNode && boundsNode.IsSequence() && boundsNode.size() == 4)
        {
            Game::MapBounds value;
            value.enabled = true;
            value.minX = boundsNode[0].as<int>();
            value.maxX = boundsNode[1].as<int>();
            value.minY = boundsNode[2].as<int>();
            value.maxY = boundsNode[3].as<int>();
            bounds = value;
        }

        impl.loaded = impl.outdoor
            ? impl.loadOutdoor(mapBytes, stateText, decorationTableText, terrainPack, bounds, errorMessage)
            : impl.loadIndoor(mapBytes, stateText, decorationTableText, errorMessage);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = std::string("the studio_walk block is not as the build writes it: ") + exception.what();
        impl.loaded = false;
    }

    return impl.loaded;
}

bool WalkSession::loaded() const
{
    return m_pImpl->loaded;
}

bool WalkSession::outdoor() const
{
    return m_pImpl->outdoor;
}

const WalkParty &WalkSession::party() const
{
    return m_pImpl->party;
}

const std::vector<WalkDoor> &WalkSession::doors() const
{
    return m_pImpl->doors;
}

size_t WalkSession::faceCount() const
{
    return m_pImpl->faces;
}

size_t WalkSession::decorationColliderCount() const
{
    return m_pImpl->decorationColliders;
}

std::string WalkSession::roomOfSector(int32_t sector) const
{
    for (const std::pair<int, std::string> &room : m_pImpl->rooms)
    {
        if (room.first == sector)
        {
            return room.second;
        }
    }

    return {};
}

WalkPose WalkSession::placeEye(float x, float y, float eyeZ)
{
    Impl &impl = *m_pImpl;
    impl.accumulator = 0.0f;

    if (impl.outdoor)
    {
        impl.outdoorState = impl.pOutdoor->initializePartyArrivalState(x, y, eyeZ - impl.party.eyeHeight,
            impl.outdoorBody.radius, impl.outdoorBody.maxStepHeight, false);
    }
    else
    {
        impl.indoorState = impl.pIndoor->initializeStateFromEyePosition(x, y, eyeZ, impl.indoorBody);
    }

    return pose();
}

WalkPose WalkSession::step(float yawRadians, uint32_t buttons, float frameSeconds)
{
    Impl &impl = *m_pImpl;
    // The core's own sin and cos (musl's, compiled in on every target), never the C library's.
    const float cosYaw = float(oy::cos(double(yawRadians)));
    const float sinYaw = float(oy::sin(double(yawRadians)));
    const float rightX = sinYaw;
    const float rightY = -cosYaw;
    const float runScale = (buttons & WalkRun) != 0 ? RunForwardMultiplier : 1.0f;
    const float forwardSpeed = WalkSpeed * runScale;
    const float backwardSpeed = WalkSpeed;
    const float strafeSpeed = WalkSpeed * StrafeMultiplier * runScale;
    float velocityX = 0.0f;
    float velocityY = 0.0f;

    if ((buttons & WalkForward) != 0)
    {
        velocityX += cosYaw * forwardSpeed;
        velocityY += sinYaw * forwardSpeed;
    }

    if ((buttons & WalkBackward) != 0)
    {
        velocityX -= cosYaw * backwardSpeed;
        velocityY -= sinYaw * backwardSpeed;
    }

    if ((buttons & WalkLeft) != 0)
    {
        velocityX -= rightX * strafeSpeed;
        velocityY -= rightY * strafeSpeed;
    }

    if ((buttons & WalkRight) != 0)
    {
        velocityX += rightX * strafeSpeed;
        velocityY += rightY * strafeSpeed;
    }

    bool jump = (buttons & WalkJump) != 0;
    impl.accumulator = std::min(impl.accumulator + std::max(frameSeconds, 0.0f), MaxAccumulatedMovementSeconds);
    impl.landed = false;

    while (impl.accumulator >= MovementStepSeconds)
    {
        impl.contacts.clear();

        if (impl.outdoor)
        {
            impl.outdoorState = impl.pOutdoor->resolveMoveForBody(impl.outdoorState, impl.outdoorBody, velocityX,
                velocityY, 0.0f, jump, false, false, false, false, JumpVelocity, OutdoorFlyVerticalSpeed,
                impl.flightCeiling, MovementStepSeconds, &impl.contacts, std::nullopt, OutdoorJumpLift, nullptr);
            impl.landed = impl.landed || impl.outdoorState.landedThisFrame;
        }
        else
        {
            impl.indoorState = impl.pIndoor->resolveMove(impl.indoorState, impl.indoorBody, velocityX, velocityY,
                jump, MovementStepSeconds, &impl.contacts, std::nullopt, true, nullptr, false, false, JumpVelocity,
                IndoorJumpLift, false, false, false, false, false, PartyGravityPerSecond);
            impl.landed = impl.landed || impl.indoorState.landedThisFrame;
        }

        jump = false;
        impl.accumulator -= MovementStepSeconds;
    }

    return pose();
}

WalkPose WalkSession::pose() const
{
    const Impl &impl = *m_pImpl;
    WalkPose result;
    result.landed = impl.landed;

    if (impl.outdoor)
    {
        const Game::OutdoorMoveState &state = impl.outdoorState;
        result.x = state.x;
        result.y = state.y;
        result.footZ = state.footZ;
        result.eyeZ = state.footZ + impl.party.eyeHeight;
        result.verticalVelocity = state.verticalVelocity;
        result.grounded = !state.airborne;
        result.onWater = state.supportOnWater;

        if (state.supportKind == Game::OutdoorSupportKind::BModelFace)
        {
            result.model = int32_t(state.supportBModelIndex);
            result.face = int32_t(state.supportFaceIndex);
        }
    }
    else
    {
        const Game::IndoorMoveState &state = impl.indoorState;
        result.x = state.x;
        result.y = state.y;
        result.footZ = state.footZ;
        result.eyeZ = state.eyeZ();
        result.verticalVelocity = state.verticalVelocity;
        result.grounded = state.grounded;
        result.sector = state.sectorId;
        result.eyeSector = state.eyeSectorId;
        result.face = state.supportFaceIndex == size_t(-1) ? -1 : int32_t(state.supportFaceIndex);
    }

    return result;
}

std::optional<bool> WalkSession::toggle(const std::string &doorId)
{
    Impl &impl = *m_pImpl;

    if (!impl.loaded || impl.outdoor)
    {
        return std::nullopt;
    }

    for (WalkDoor &door : impl.doors)
    {
        if (door.id != doorId)
        {
            continue;
        }

        door.open = !door.open;
        const uint16_t state = uint16_t(door.open ? Game::EvtMechanismState::Open : Game::EvtMechanismState::Closed);

        for (Game::MapDeltaDoor &mapDoor : impl.indoorDelta->doors)
        {
            if (std::find(door.mechanisms.begin(), door.mechanisms.end(), mapDoor.doorId) != door.mechanisms.end())
            {
                mapDoor.state = state;
                mapDoor.timeSinceTriggered = 0;
            }
        }

        // The worst case of the game's update (S5-0 spike 3: 0.7 ms on Darkmoor, 4 ms on Thjorgard): the controller's
        // geometry is made again on the next step.
        impl.pIndoor->invalidateRuntimeGeometryCache();
        return door.open;
    }

    return std::nullopt;
}

std::string walkPoseBits(const WalkPose &pose)
{
    char text[40] = {};
    std::snprintf(text, sizeof(text), "%08x%08x%08x%08x", floatBits(pose.x), floatBits(pose.y), floatBits(pose.footZ),
        floatBits(pose.verticalVelocity));
    return text;
}

std::string writeWalkStateText(const WalkStateHeader &header, const YAML::Node &scene)
{
    YAML::Node block(YAML::NodeType::Map);
    block["format"] = 1;
    block["kind"] = header.kind;
    block["world"] = header.world;
    block["map"] = header.map;
    YAML::Node party(YAML::NodeType::Map);
    party["radius"] = header.party.radius;
    party["height"] = header.party.height;
    party["eye_height"] = header.party.eyeHeight;
    party["max_step_height"] = header.party.maxStepHeight;
    block["party"] = party;
    YAML::Node doors(YAML::NodeType::Sequence);

    for (const WalkDoor &door : header.doors)
    {
        YAML::Node node(YAML::NodeType::Map);
        node["id"] = door.id;
        YAML::Node mechanisms(YAML::NodeType::Sequence);

        for (const uint32_t mechanism : door.mechanisms)
        {
            mechanisms.push_back(mechanism);
        }

        node["mechanisms"] = mechanisms;
        doors.push_back(node);
    }

    block["doors"] = doors;
    YAML::Node rooms(YAML::NodeType::Sequence);

    for (const std::pair<int, std::string> &room : header.rooms)
    {
        YAML::Node node(YAML::NodeType::Map);
        node["sector"] = room.first;
        node["id"] = room.second;
        rooms.push_back(node);
    }

    block["rooms"] = rooms;

    if (header.faceAttributes)
    {
        YAML::Node faces(YAML::NodeType::Sequence);

        for (const std::array<uint32_t, 3> &face : *header.faceAttributes)
        {
            YAML::Node entry(YAML::NodeType::Sequence);
            entry.SetStyle(YAML::EmitterStyle::Flow);

            for (const uint32_t value : face)
            {
                entry.push_back(value);
            }

            faces.push_back(entry);
        }

        block["face_attributes"] = faces;
    }

    if (header.bounds)
    {
        YAML::Node bounds(YAML::NodeType::Sequence);

        for (const int value : *header.bounds)
        {
            bounds.push_back(value);
        }

        block["bounds"] = bounds;
    }

    // The studio's block first, then the scene's keys but those movement never reads.
    YAML::Node document(YAML::NodeType::Map);
    document[HeaderKey] = block;

    for (YAML::const_iterator entry = scene.begin(); entry != scene.end(); ++entry)
    {
        const std::string key = entry->first.Scalar();

        if (key == "spawns" || key == "loot_containers" || key == "pulsing_lights" || key == "ambient_sounds"
            || key == "lights" || key == "cinematics")
        {
            // A list the reader may need stays, empty.
            if (entry->second.IsSequence())
            {
                document[key] = YAML::Node(YAML::NodeType::Sequence);
            }

            continue;
        }

        // Outdoors the face entries' attributes are in the studio's block: the entries stay, empty.
        if (key == "bmodel_faces" && header.faceAttributes)
        {
            document[key]["interactive_faces"] = YAML::Node(YAML::NodeType::Sequence);
            continue;
        }

        if (key != "initial_state" || !entry->second.IsMap())
        {
            document[key] = entry->second;
            continue;
        }

        YAML::Node state(YAML::NodeType::Map);

        for (YAML::const_iterator part = entry->second.begin(); part != entry->second.end(); ++part)
        {
            const std::string name = part->first.Scalar();

            // The game's reader needs the lists: they stay, empty.
            state[name] = name == "actors" || name == "sprite_objects" || name == "chests"
                ? YAML::Node(YAML::NodeType::Sequence) : part->second;
        }

        document[key] = state;
    }

    return writeCanonicalYaml(document);
}

WalkParty walkPartyOfWorld(const std::filesystem::path &assetRoot, const std::string &world, bool outdoor)
{
    WalkParty party;

    if (!outdoor)
    {
        // The indoor body (IndoorBodyDimensions, IndoorMoveState): the game declares no other.
        const Game::IndoorBodyDimensions body;
        const Game::IndoorMoveState state;
        party.radius = body.radius;
        party.height = body.height;
        party.eyeHeight = state.eyeHeight;
        party.maxStepHeight = 0.0f;
        return party;
    }

    party.radius = DefaultOutdoorRadius;
    party.height = DefaultOutdoorHeight;
    party.maxStepHeight = DefaultOutdoorMaxStepHeight;
    party.eyeHeight = DefaultOutdoorEyeHeight;

    if (assetRoot.empty() || world.empty())
    {
        return party;
    }

    try
    {
        const YAML::Node root = YAML::LoadFile((assetRoot / "worlds" / world / "world.yml").string());
        const YAML::Node movement = root["partyMovement"];

        if (movement.IsMap())
        {
            party.eyeHeight = movement["eyeHeight"].as<float>(party.eyeHeight);
            party.radius = movement["collisionRadius"].as<float>(party.radius);
            party.height = movement["collisionHeight"].as<float>(party.height);
            party.maxStepHeight = movement["maxStepHeight"].as<float>(party.maxStepHeight);
        }
    }
    catch (const YAML::Exception &)
    {
        // No world.yml, or one without a party: the defaults, as the game.
    }

    return party;
}

std::vector<std::array<uint32_t, 3>> walkFaceAttributeChanges(const Game::OutdoorMapData &plain,
    const Game::OutdoorMapData &scened)
{
    std::vector<std::array<uint32_t, 3>> changes;

    for (size_t model = 0; model < scened.bmodels.size() && model < plain.bmodels.size(); ++model)
    {
        const std::vector<Game::OutdoorBModelFace> &faces = scened.bmodels[model].faces;

        for (size_t face = 0; face < faces.size() && face < plain.bmodels[model].faces.size(); ++face)
        {
            if (faces[face].attributes != plain.bmodels[model].faces[face].attributes)
            {
                changes.push_back({uint32_t(model), uint32_t(face), uint32_t(faces[face].attributes)});
            }
        }
    }

    return changes;
}

std::vector<uint8_t> writeWalkTerrainPack(const Engine::AssetFileSystem &files, Game::OutdoorMapData map)
{
    if (!Game::applyTerrainTileDescriptorAttributes(files, map))
    {
        return {};
    }

    const std::optional<std::vector<Game::TerrainTileDescriptor>> tiles = Game::loadTerrainTileDescriptors(files, map);
    std::vector<uint8_t> landMask;

    // As MapAssetLoader's buildOutdoorLandMask: a cell whose tile is water is not land. (Shallow liquids, which it
    // counts as land, apply to faces of MM9 only today: liquids.yml.)
    if (tiles)
    {
        const int width = map.terrainSide;
        const int height = map.terrainSide;
        landMask.assign(size_t(width - 1) * size_t(height - 1), 0);

        for (int gridY = 0; gridY < height - 1; ++gridY)
        {
            for (int gridX = 0; gridX < width - 1; ++gridX)
            {
                const uint8_t tile = map.tileMap[size_t(gridY * width + gridX)];
                const bool water = ((*tiles)[tile].flags & Game::TerrainTileFlagWater) != 0;
                landMask[size_t(gridY * (width - 1) + gridX)] = water ? 0 : 1;
            }
        }
    }

    std::vector<uint8_t> pack = {'O', 'Y', 'W', 'T'};
    const auto appendSize = [&pack](uint32_t size)
    {
        for (int shift = 0; shift < 32; shift += 8)
        {
            pack.push_back(uint8_t(size >> shift));
        }
    };
    appendSize(uint32_t(map.attributeMap.size()));
    pack.insert(pack.end(), map.attributeMap.begin(), map.attributeMap.end());
    appendSize(uint32_t(landMask.size()));
    pack.insert(pack.end(), landMask.begin(), landMask.end());
    return pack;
}
}
