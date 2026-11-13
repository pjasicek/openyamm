#pragma once

#include "game/audio/SoundRef.h"
#include "game/events/EvtEnums.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/NpcFollowerTypes.h"
#include "game/maps/MapDeltaData.h"
#include "game/events/MechanismAudioProfile.h"
#include "game/party/Party.h"
#include "game/tables/PortraitFxEventTable.h"

#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <memory>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class ISceneEventContext;
class HouseTable;
class NpcDialogTable;
struct LuaSessionCache;

enum class DialogueContextKind
{
    None,
    MapEvent,
    HouseService,
    NpcTalk,
    NpcNews,
    MapTransition,
    Mm9Rude,
};

enum class DialogueMenuId : uint32_t
{
    None = 0,
    LearnSkills,
    ShopEquipment,
    TavernArcomage,
    HouseServiceRoot,
    TeacherLedger,
};

enum class DialogueOfferKind : uint32_t
{
    None = 0,
    RosterJoin,
    MasteryTeacher,
    GuildMembership,
    NpcHire,
    Arena,
};

enum class MechanismAction
{
    Trigger = 0,
    Open = 1,
    Close = 2,
};

enum class EventRuntimeHookKind : uint8_t
{
    NpcEnter = 0,
    NpcExit,
    HouseTopicFilter,
    HouseTopicClick,
    RestFoodCost,
    GameplayAction,
    MapRefill,
    MapTransition,
    MonsterKilled,
    MonsterDamage,
    ChestOpen,
    InventoryOpen,
};

struct RuntimeMechanismState
{
    uint16_t state = 0;
    float timeSinceTriggeredMs = 0.0f;
    float currentDistance = 0.0f;
    int8_t rotationDirection = 1;
    bool isMoving = false;
    // A spinning mover (IndoorMoverSpin): its angle, its speed as a share of full speed (signed), whether it is
    // switched on, the direction it turns when on, and whether spinOn holds its state (set from its startOn when the
    // map first runs, then by evt.SpinMover).
    float spinDegrees = 0.0f;
    float spinRate = 0.0f;
    bool spinOn = false;
    int8_t spinDirection = 1;
    bool spinSet = false;
    // A door a monster opened (an MM9 monster's BaseDoor.inc): an open-away leaf swings away from that monster, not
    // from the party (IndoorSceneRuntime::chooseMoverOpenAwayDirections). Runtime only, not saved.
    bool openerSet = false;
    float openerX = 0.0f;
    float openerY = 0.0f;
    float openerZ = 0.0f;
};

// Whether a mechanism's faces are moving: a door on its way, or a mover spinning.
inline bool mechanismFacesMoving(const RuntimeMechanismState &mechanism)
{
    return mechanism.isMoving || mechanism.spinRate != 0.0f;
}

// Whether two states put the mechanism's faces in different poses.
inline bool mechanismPoseDiffers(const RuntimeMechanismState &left, const RuntimeMechanismState &right)
{
    const float distance = left.currentDistance - right.currentDistance;
    const float spin = left.spinDegrees - right.spinDegrees;
    return distance > 0.0001f || distance < -0.0001f || spin > 0.0001f || spin < -0.0001f;
}

struct RuntimeDestructibleState
{
    int hp = 1;
    bool damageEnabled = false;
    bool destroyed = false;
};

struct EventRuntimeState
{
    struct OutdoorModelMechanismDefinition
    {
        uint32_t mechanismId = 0;
        // Map interaction events and runtime mechanism ids use separate id spaces.
        uint16_t interactionEventId = 0;
        std::string modelName;
        size_t bmodelIndex = static_cast<size_t>(-1);
        int32_t dx = 0;
        int32_t dy = 0;
        int32_t dz = 0;
        // Interaction event, pivot, and rotation are map-derived and rebuilt from scene data after loading a save.
        int32_t pivotX = 0;
        int32_t pivotY = 0;
        int32_t pivotZ = 0;
        float rotationDegreesX = 0.0f;
        float rotationDegreesY = 0.0f;
        float rotationDegreesZ = 0.0f;
        uint32_t moveTimeMs = 0;
        bool closed = true;
        bool openAway = false;
        bool moveParty = false;
        MechanismAudioProfile audio = {};
    };

    struct PendingMapMove
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<std::string> mapName;
        std::optional<int32_t> directionDegrees;
        bool useMapStartPosition = false;
        // With useMapStartPosition: the start decoration to use ("north start", ...); empty means "party start".
        std::string startPointName;
        bool useFullscreenLoading = false;
        // Travel time, food or fare were already spent, so the travel autosave belongs to the arrival map.
        bool travelTimeApplied = false;
        // The party arrives at the given height and falls from there instead of standing on the ground below
        // (evt.MoveToMap's options keepHeight: falling off Celeste into the Bracada Desert sky, OY Celeste fall).
        // Not saved: a move pending in a save lands on the ground.
        bool keepHeight = false;
        std::string traceSourceKind;
        uint32_t traceSourceId = 0;
        uint32_t traceActionId = 0;
        uint32_t traceEventId = 0;
        std::string traceDestinationName;
    };

    struct MapNoteSourcePoint
    {
        int32_t x = 0;
        int32_t y = 0;
    };

    struct PendingDialogueContext
    {
        DialogueContextKind kind = DialogueContextKind::None;
        uint32_t sourceId = 0;
        std::optional<uint32_t> sourceActorIndex;
        // An MM9 dialogue opened by a decoration's click event (a posed talking prop, Ake the Righteous): that
        // decoration's sprite override key, hidden when the dialogue hires (evt.SetSprite's cog).
        std::optional<uint32_t> sourceDecorationKey;
        uint32_t hostHouseId = 0;
        uint32_t newsId = 0;
        uint32_t participantPictureId = 0;
        std::optional<std::string> titleOverride;
        std::optional<PendingMapMove> transitionMapMove;
        // Walking off an outdoor map edge (sourceId holds the MapBoundaryEdge); transitionMapMove is the arrival.
        bool boundaryTravel = false;
        // An MM9 exit's days on the road (Mm9MapTransition::travelDays), stated in the dialogue.
        int transitionTravelDays = 0;
        uint32_t transitionTextId = 0;
        uint32_t transitionImageId = 0;
        std::optional<MapNoteSourcePoint> mapNoteSourcePoint;
    };

    struct PendingMovie
    {
        std::string movieName;
        bool restoreAfterPlayback = false;
    };

    // evt.PlayCinematic(id[, doneEventId]): a cinematic of the map's .cinematics.yml (game/gameplay/CinematicRuntime).
    struct PendingCinematic
    {
        std::string id;
        uint16_t doneEventId = 0;
    };

    // evt.CameraShake(intensity, seconds[, x, y, z, innerRadius, outerRadius]): with a point, full strength within
    // innerRadius of the party and none past outerRadius (MM9's EarthQuake).
    struct CameraShakeRequest
    {
        float intensity = 0.0f;
        float seconds = 0.0f;
        bool positional = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float innerRadius = 0.0f;
        float outerRadius = 0.0f;
    };

    struct PendingInputPrompt
    {
        enum class Kind : uint8_t
        {
            InputString = 0,
            PressAnyKey,
            // One dialog button per answer (AskChoiceWithAnswerSteps): a click continues at that answer's step.
            Choice,
        };

        Kind kind = Kind::InputString;
        uint16_t eventId = 0;
        uint8_t continueStep = 0;
        uint8_t correctStep = 0;
        uint32_t textId = 0;
        std::vector<uint32_t> answerTextIds;
        std::vector<std::string> answers;
        std::vector<uint8_t> answerContinueSteps;
        std::optional<std::string> text;
    };

    struct PendingSound
    {
        enum class Kind
        {
            PlayOneShot,
            PlayLoopingKeyed,
            StopKeyed,
        };

        Kind kind = Kind::PlayOneShot;
        SoundScope soundScope = SoundScope::Engine;
        uint32_t soundId = 0;
        std::string soundName;
        // One-shot by name only: played instead while no sound of soundName exists (placeholder names). Not saved.
        std::string fallbackSoundName;
        uint64_t key = 0;
        std::optional<size_t> actorIndex;
        float pitch = 1.0f;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        bool positional = false;
        bool hasExplicitZ = false;
    };

    struct SpriteOverride
    {
        bool hidden = false;
        std::optional<std::string> textureName;
    };

    struct PendingArcomageGame
    {
        uint32_t houseId = 0;
    };

    struct DialogueOfferState
    {
        DialogueOfferKind kind = DialogueOfferKind::None;
        uint32_t npcId = 0;
        uint32_t topicId = 0;
        uint32_t messageTextId = 0;
        uint32_t rosterId = 0;
        uint32_t partyFullTextId = 0;
        std::optional<uint32_t> sourceActorIndex;
    };

    struct SuspendedMm9RudeDialogue
    {
        uint32_t rudeId = 0;
        int32_t nodeId = 0;
        std::optional<uint32_t> sourceActorIndex;
        // The talking prop whose click opened the talk (DialogueRuntimeState::mm9RudeSourceDecorationKey).
        std::optional<uint32_t> sourceDecorationKey;
        std::string response;
        uint32_t selectionIndex = 0;
        bool exitCallbackExecuted = false;
    };

    struct DialogueRuntimeState
    {
        struct GeneratedNpcGreeting
        {
            uint32_t npcId = 0;
            std::string text;
        };

        uint32_t hostHouseId = 0;
        std::vector<DialogueMenuId> menuStack;
        std::optional<DialogueOfferState> currentOffer;
        std::array<uint8_t, Party::MaxMembers> templeDonationCounters = {};
        uint32_t trainingHouseId = 0;
        std::vector<uint32_t> trainingLevelsByMember;
        std::optional<SuspendedMm9RudeDialogue> suspendedMm9RudeDialogue;
        // The open MM9 dialogue's source decoration (PendingDialogueContext::sourceDecorationKey); not saved.
        std::optional<uint32_t> mm9RudeSourceDecorationKey;
        // Presentation cache for the current conversation; only the greeting visit count is saved.
        std::optional<GeneratedNpcGreeting> generatedNpcGreeting;
    };

    using HiredNpcFollower = ::OpenYAMM::Game::HiredNpcFollower;

    struct GeneratedMercenaryRecruit
    {
        uint32_t npcId = 0;
        uint32_t rosterId = 0;
        uint32_t houseId = 0;
        uint32_t portraitPictureId = 0;
        uint32_t npcPictureId = 0;
        Character character = {};
    };

    struct ActiveDecorationContext
    {
        uint8_t decorVarIndex = 0;
        uint16_t baseEventId = 0;
        uint16_t currentEventId = 0;
        uint8_t eventCount = 0;
        bool hideWhenCleared = false;
    };

    struct PortraitFxRequest
    {
        PortraitFxEventKind kind = PortraitFxEventKind::None;
        std::vector<size_t> memberIndices;
    };

    struct SpellFxRequest
    {
        uint32_t spellId = 0;
        std::vector<size_t> memberIndices;
    };

    struct WorldEffectRequest
    {
        std::string id;
        std::array<float, 3> position = {};
        float scale = 1.0f;
        float yawRadians = 0.0f;
    };

    // evt.Beam / evt.BeamToParty: a named effect (its ribbons with `beam: true`) drawn from a point to a point, or to
    // the party (following it), for seconds (0: until evt.StopBeam). A request whose name is drawing replaces it.
    struct BeamRequest
    {
        std::string name;
        std::string effectId;
        std::array<float, 3> from = {};
        std::array<float, 3> to = {};
        bool toParty = false;
        float seconds = 0.0f;
    };

    // evt.SpawnActorEffect(actor, effect[, socket[, seconds[, scale]]]): a named effect carried on a map actor, on a
    // socket of its 3D model (an actors.yml animation.sockets name, or a node of the model) or, without a socket or a
    // model, at the middle of its body; for seconds (0: until the effect ends by itself or the actor is gone). A
    // comma-separated socket list ("palm_left,palm_right") carries one on each, sharing a hand effect's emitters as
    // actors.yml clip effects do (actorClipEffectSocketAnchor).
    // evt.StopActorEffect(actor[, effect]) (stop): ends the actor's carried effects, or those of one effect.
    struct ActorEffectRequest
    {
        size_t actorIndex = 0;
        std::string effectId;
        std::string socket;
        float seconds = 0.0f;
        float scale = 1.0f;
        bool stop = false;
    };

    // evt.MoveActorTo: a map actor walks (or runs) to a point, whatever it would do by itself, and stops there; its
    // arrival runs arrivalEventId (0: none) with the hook context's actor index (ScriptedActorMoves.h).
    struct ScriptedActorMove
    {
        std::array<float, 3> point = {};
        uint16_t arrivalEventId = 0;
        bool run = false;
        // Its progress (applyScriptedActorMoves): where it stood when it last got anywhere, and the seconds it has
        // walked since without leaving that spot.
        std::optional<std::array<float, 2>> progressAnchor;
        float stuckSeconds = 0.0f;
    };

    // evt.SetActorTarget: the target an actor's MM9 loop takes at its next AI step (applyScriptedActorTargets): the
    // party, or another map actor.
    struct ScriptedActorTarget
    {
        std::optional<uint32_t> actorIndex;
    };

    struct ScriptedActorArrival
    {
        uint32_t actorIndex = 0;
        uint16_t eventId = 0;
    };

    // evt.AimDecoration / evt.RecoilDecoration: a decoration model turned about its origin from its map facing
    // (counter-clockwise, as facings run), slewing at radiansPerSecond (0: at once), and kicked back along its front
    // (asset +z) for recoilSeconds. Keyed by cog as spriteOverrides; runtime only, advanced by advanceDecorationAims.
    struct DecorationAim
    {
        float targetRadians = 0.0f;
        float radiansPerSecond = 0.0f;
        float currentRadians = 0.0f;
        float recoilDistance = 0.0f;
        float recoilSeconds = 0.0f;
        float recoilElapsedSeconds = 0.0f;
        // evt.MoveDecoration and the cinematics' decoration cues: an offset from its map position (world units),
        // gliding from offsetFrom to offsetTo over offsetSeconds (0: at once).
        std::array<float, 3> offset = {};
        std::array<float, 3> offsetFrom = {};
        std::array<float, 3> offsetTo = {};
        float offsetSeconds = 0.0f;
        float offsetElapsedSeconds = 0.0f;

        // How far it is pulled back now: out in the first tenth of the recoil, then home again.
        float back() const;
    };

    // evt.PlayActorClip / evt.FaceActorTo and the cinematics' actor clip and face cues: a map actor's model plays a
    // named clip (an actors.yml script_clips role or the model's own clip name; once, then its own animation again,
    // or looping) and faces a heading, over what its AI shows. Presentation only, runtime only (never saved); the
    // worlds apply it in actorRuntimeState (applyActorPresentation), advanceActorPresentations runs its clocks.
    struct ActorPresentation
    {
        std::string clip;
        // Clips after `clip`, in order (evt.PlayActorClip with a list); `loop` applies to the last one.
        std::vector<std::string> then;
        bool loop = false;
        // Past its end the last clip holds its last frame (evt.PlayActorClip(..., "hold")) instead of releasing.
        bool hold = false;
        float clipSeconds = 0.0f;
        std::optional<float> yawRadians;
        float yawFromRadians = 0.0f;
        float yawToRadians = 0.0f;
        float turnSeconds = 0.0f;
        float turnElapsedSeconds = 0.0f;
    };

    // evt.PlayDecorationClip: the clip a decoration's moving part plays (DecorationModelSet parts: a coffin's lid),
    // keyed by cog as spriteOverrides; once (then held at its last frame) or looping. Runtime only, not saved: a map
    // shows a part left open again from its own map variables on load (mode "end").
    struct DecorationClip
    {
        std::string clip;
        float seconds = 0.0f;
        bool loop = false;
    };

    struct WorldModelRequest
    {
        std::string assetPath;
        std::string clipName;
        std::array<float, 3> position = {};
        float scale = 1.0f;
        float yawRadians = 0.0f;
    };

    struct RuntimeMapNote
    {
        uint32_t id = 0;
        int32_t x = 0;
        int32_t y = 0;
        std::string mapFileName;
        std::string text;
        bool active = false;
    };

    struct SavedLocation
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        uint32_t continentId = 0;
        std::string mapName;
    };

    struct TransportRouteOverride
    {
        uint32_t houseId = 0;
        uint32_t routeIndex = 0;
        std::string destinationName;
        std::string mapFileName;
        std::array<bool, 7> daysAvailable = {true, true, true, true, true, true, true};
        uint32_t travelDays = 0;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        int32_t directionDegrees = 0;
        uint32_t requiredQBit = 0;
        bool useMapStartPosition = false;
    };

    struct ChestItemRequest
    {
        uint32_t itemId = 0;
        uint8_t gridX = 0;
        uint8_t gridY = 0;
    };

    struct OpenedChestRequest
    {
        uint32_t chestId = 0;
        bool openedByTelekinesis = false;
        // The sprite override key of the decoration whose click opened it (activeEventDecorationKey), if any.
        std::optional<uint32_t> decorationKey;
    };

    struct PressurePlateTrigger
    {
        std::string world;
        uint32_t eventId = 0;
        size_t bmodelIndex = std::numeric_limits<size_t>::max();
        size_t faceIndex = std::numeric_limits<size_t>::max();
        uint32_t attributes = 0;
    };

    struct DialogueCanceled
    {
        std::string kind;
        uint32_t sourceId = 0;
        uint32_t activeSourceId = 0;
        bool houseDialog = false;
        size_t actionCount = 0;
    };

    struct MapTransitionTrace
    {
        std::string sourceKind;
        uint32_t sourceId = 0;
        uint32_t actionId = 0;
        uint32_t eventId = 0;
        std::optional<uint32_t> routeIndex;
        bool confirmationRequired = false;
        std::string destinationMap;
        std::string destinationName;
        uint32_t travelDays = 0;
        bool useStartPosition = false;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        std::optional<int32_t> directionDegrees;
    };

    struct ChestOpenedTrace
    {
        std::string sceneKind;
        std::string map;
        uint32_t chestId = 0;
        size_t itemCount = 0;
        size_t hiddenItemCount = 0;
    };

    struct ActorDialogStartedTrace
    {
        std::string kind;
        std::string map;
        uint32_t npcId = 0;
        uint32_t sourceId = 0;
        uint32_t hostHouseId = 0;
        std::optional<uint32_t> actorIndex;
    };

    struct ActiveHookContext
    {
        EventRuntimeHookKind kind = EventRuntimeHookKind::NpcEnter;
        uint32_t npcId = 0;
        std::optional<uint32_t> actorIndex;
        uint32_t monsterId = 0;
        int32_t damage = 0;
        uint32_t damageType = 0;
        // MonsterDamage, MonsterKilled: the party dealt the hit or the killing blow (its weapons, missiles and spells,
        // damage it reflects), not another monster, a trap or an area effect.
        bool byParty = false;
        uint32_t houseId = 0;
        uint32_t houseServiceType = 0;
        uint32_t menuId = 0;
        uint32_t houseActionId = 0;
        uint32_t gameplayActionId = 0;
        uint32_t boundaryEdge = 0;
        uint32_t chestId = 0;
        uint32_t heldItemId = 0;
        uint32_t inventorySource = 0;
        uint32_t inventorySourceIndex = 0;
        uint32_t inventoryPage = 0;
        std::string destinationMapName;
        // Mm9PromotionServiceEventId: the promotion to give (mm9_common.lua MM9.promoteParty).
        std::string mm9Promotion;
        int32_t baseRestFoodCost = 0;
        std::optional<int32_t> restFoodCostOverride;
        std::optional<int32_t> damageOverride;
        bool blocked = false;
        std::optional<std::string> statusText;
        std::vector<uint32_t> houseTopicActionIds;
    };

    std::string mapFileName;
    // World (mm6, mm7, mm8, ...) of the current map; event-granted random items follow its world gates.
    std::string mapWorldId;
    std::unordered_map<uint32_t, int32_t> variables;
    std::unordered_map<std::string, int32_t> namedMapVars;
    std::unordered_map<std::string, int32_t> namedGlobalVars;
    // Legacy saves only: journal map notes now live on the party and load migrates these there.
    std::unordered_map<uint32_t, RuntimeMapNote> runtimeMapNotes;
    std::unordered_map<std::string, SavedLocation> savedLocations;
    std::unordered_map<uint64_t, TransportRouteOverride> transportRouteOverrides;
    uint32_t eventRandomState = 0;
    std::optional<MapNoteSourcePoint> activeEventMapNoteSourcePoint;
    uint32_t activeHistoryContinentId = 1;
    std::unordered_map<uint32_t, int32_t> historyEventTimes;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> historyEventTimesByContinent;
    std::array<uint8_t, 75> mapVars = {};
    int32_t currentLocationReputation = 0;
    std::unordered_map<uint32_t, uint32_t> facetSetMasks;
    std::unordered_map<uint32_t, uint32_t> facetClearMasks;
    uint64_t outdoorSurfaceRevision = 0;
    mutable uint64_t facetInvisibleOverrideCacheRevision = std::numeric_limits<uint64_t>::max();
    mutable size_t facetInvisibleOverrideCacheSetSize = 0;
    mutable size_t facetInvisibleOverrideCacheClearSize = 0;
    mutable std::vector<uint8_t> facetInvisibleOverrideCache;
    std::unordered_map<uint32_t, RuntimeMechanismState> mechanisms;
    std::unordered_map<uint32_t, RuntimeDestructibleState> destructibles;
    std::unordered_map<uint32_t, OutdoorModelMechanismDefinition> outdoorModelMechanisms;
    // evt.SetTexture swaps: keyed by a face cog number (MM7/MM8: every face of the cog), or by
    // EventRuntime::indoorFaceReferenceKey(face index) (a negative reference, MMerge's MM6 maps: that one face).
    std::unordered_map<uint32_t, std::string> textureOverrides;
    std::unordered_map<uint32_t, std::string> outdoorModelFacetTextureOverrides;
    std::unordered_map<uint32_t, SpriteOverride> spriteOverrides;
    std::unordered_map<uint32_t, bool> indoorLightsEnabled;
    // evt.SetSectorAmbient: an indoor sector's ambient level (minAmbientLightLevel's 0-31 scale) instead of the map's.
    // Runtime only, not saved: a map that dims or lights a room sets it again from its own map variables on load.
    std::unordered_map<uint16_t, int16_t> sectorAmbientLevels;
    std::unordered_map<uint32_t, DecorationAim> decorationAims;
    std::unordered_map<uint32_t, DecorationClip> decorationClips;
    std::unordered_map<uint32_t, ActorPresentation> actorPresentations;
    // evt.SetActorRoutine: the MM9 routine a map actor runs, by actor index (Mm9AiRoutine::name; empty: none); an
    // actor without an entry runs its `default`. Runtime only: a map script sets it again on load.
    std::unordered_map<uint32_t, std::string> actorRoutines;
    // evt.MoveActorTo walks by map actor index, and the arrivals whose events the world runs at its next update.
    // Runtime only, not saved: a map that walks an actor walks it again from its own map variables on load.
    std::unordered_map<uint32_t, ScriptedActorMove> scriptedActorMoves;
    std::vector<ScriptedActorArrival> pendingActorArrivals;
    // evt.SetRestAlarm: the game minute a rest or wait stops at (MM9's clock triggers fire during a wait: Atli's dock
    // watch). Runtime only, not saved: the map's script arms it again from its own map variables.
    std::optional<float> restAlarmGameMinutes;
    // evt.SetActorTarget orders by map actor index, until the actor's next AI step takes them. Runtime only.
    std::unordered_map<uint32_t, ScriptedActorTarget> scriptedActorTargets;
    // evt.StartTimer / evt.StopTimer, applied by updateScriptedEventTimers (a timer's own handler's at once).
    using TimerControl = ScriptedEventTimerControl;
    std::vector<TimerControl> timerControls;
    // Bumped by every light switch and sector ambient change (the indoor lighting re-bakes).
    uint64_t indoorLightRevision = 0;
    std::optional<bool> snowEnabled;
    std::optional<bool> rainEnabled;
    std::optional<std::string> outdoorSkyTextureOverride;
    // evt.SetFog / evt.ClearFog: a map script's fog over an indoor map's scene fog (devdocs/INDOOR_FOG.md "Fog from
    // Lua"), faded in over `seconds` from the fog shown; each call raises `revision`. Not saved: the map's Lua sets it
    // again on load.
    struct ScriptedFog
    {
        bool active = false;
        std::array<float, 3> color = {0.0f, 0.0f, 0.0f};    // display space, 0..1
        float nearDistance = 0.0f;
        float farDistance = 0.0f;
        float sky = 0.0f;
        float seconds = 0.0f;
        uint32_t revision = 0;
    };
    ScriptedFog scriptedFog;
    std::optional<int32_t> outdoorFogWeakDistanceOverride;
    std::optional<int32_t> outdoorFogStrongDistanceOverride;
    std::unordered_map<uint32_t, uint32_t> actorSetMasks;
    std::unordered_map<uint32_t, uint32_t> actorClearMasks;
    std::unordered_map<uint32_t, uint32_t> actorGroupSetMasks;
    std::unordered_map<uint32_t, uint32_t> actorGroupClearMasks;
    std::unordered_map<uint32_t, bool> actorHostilityRequests;
    std::unordered_map<uint32_t, bool> actorGroupHostilityRequests;
    std::unordered_map<uint32_t, uint32_t> actorIdGroupOverrides;
    std::unordered_map<uint32_t, uint32_t> actorGroupOverrides;
    std::unordered_map<uint32_t, uint32_t> actorGroupAllyOverrides;
    std::unordered_map<uint32_t, uint32_t> chestSetMasks;
    std::unordered_map<uint32_t, uint32_t> chestClearMasks;
    std::optional<PressurePlateTrigger> lastPressurePlateTrigger;
    std::optional<DialogueCanceled> lastDialogueCanceled;
    std::optional<MapTransitionTrace> lastMapTransitionRequested;
    std::optional<MapTransitionTrace> lastMapTransitionConfirmed;
    std::optional<MapTransitionTrace> lastMapTransitionCanceled;
    std::optional<ChestOpenedTrace> lastChestOpened;
    std::optional<ActorDialogStartedTrace> lastActorDialogStarted;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> npcTopicOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGroupNews;
    std::unordered_map<uint32_t, uint32_t> npcGreetingOverrides;
    std::unordered_map<uint32_t, uint32_t> npcGreetingDisplayCounts;
    std::unordered_map<uint32_t, uint32_t> npcHouseOverrides;
    std::unordered_map<uint32_t, std::string> npcNameOverrides;
    std::unordered_map<uint32_t, uint32_t> npcPictureOverrides;
    std::unordered_map<uint32_t, uint32_t> npcProfessionOverrides;
    std::unordered_map<std::string, uint32_t> generatedNpcIdsByActorKey;
    std::unordered_map<uint32_t, GeneratedMercenaryRecruit> generatedMercenaryRecruitsByNpcId;
    std::unordered_map<uint32_t, uint32_t> npcItemOverrides;
    std::unordered_map<uint32_t, uint32_t> actorItemOverrides;
    std::unordered_map<uint32_t, std::vector<uint32_t>> actorExtraItemOverrides;
    std::unordered_map<uint32_t, int32_t> monsterRelationOverrides;
    std::unordered_map<uint32_t, std::vector<ChestItemRequest>> chestItemRequests;
    std::unordered_set<uint32_t> unavailableNpcIds;
    std::vector<HiredNpcFollower> hiredNpcFollowers;
    bool pendingDimensionDoorOverlay = false;
    DialogueRuntimeState dialogueState;
    std::array<uint8_t, 125> decorVars = {};
    // decorVars still use the numbering of saves before MMerge's campfire list (SaveVersionMMergeCampfireDecorVars);
    // the map renumbers them when it is next entered (legacyCampFireDecorVarRemap).
    bool legacyCampFireDecorVars = false;
    // decorVars hold MM6's small barrels as casks (saves before SaveVersionSmallStatBarrels); the map refills them as
    // stat barrels when it is next entered (refillLegacySmallBarrels).
    bool legacySmallBarrelDecorVars = false;
    std::optional<ActiveDecorationContext> activeDecorationContext;
    std::optional<ActiveHookContext> activeHookContext;
    std::vector<std::string> messages;
    std::vector<std::string> statusMessages;
    // The experience each member got from the running handler (not saved): a handler that shows no status text of its
    // own ends with "+N experience" (OY-489).
    int64_t handlerExperienceAward = 0;
    std::vector<uint32_t> openedChestIds;
    std::vector<OpenedChestRequest> openedChestRequests;
    bool activeEventOpenedByTelekinesis = false;
    uint32_t activeEventSpellId = 0;
    // The decoration (its sprite override key) whose click runs the current event, and the one whose chest is open
    // now: a chest's lid (a decoration part with open and close clips) opens with its chest and closes with it.
    std::optional<uint32_t> activeEventDecorationKey;
    std::optional<uint32_t> openChestDecorationKey;
    // How many times each decoration (its sprite override key) was used (a click that ran its event): a binding's
    // use_clips steps through its clips on each use (a book's pages). Runtime only.
    std::unordered_map<uint32_t, uint32_t> decorationUses;
    std::vector<InventoryItem> grantedItems;
    std::vector<uint32_t> grantedItemIds;
    bool clearHeldItemRequest = false;
    // An item an event took that no pack held: the one on the cursor goes, as the originals' Subtract takes it
    // (a quest item an event just gave lands on the cursor). Kept from event to event until the next frame takes the
    // item off the cursor (GameplayHeldItemController). 0: none.
    uint32_t takenHeldItemId = 0;
    std::vector<uint32_t> removedItemIds;
    std::vector<uint32_t> grantedAwardIds;
    std::vector<uint32_t> removedAwardIds;
    std::vector<PortraitFxRequest> portraitFxRequests;
    std::vector<SpellFxRequest> spellFxRequests;
    std::vector<WorldEffectRequest> worldEffectRequests;
    std::vector<BeamRequest> beamRequests;
    // evt.StopBeam: names of beams to end.
    std::vector<std::string> beamStops;
    // In call order: starts and stops.
    std::vector<ActorEffectRequest> actorEffectRequests;
    std::vector<WorldModelRequest> worldModelRequests;
    std::optional<PendingDialogueContext> pendingDialogueContext;
    std::optional<PendingMapMove> pendingMapMove;
    std::optional<PendingMovie> pendingMovie;
    // Transient requests the session takes each frame (never saved).
    std::optional<PendingCinematic> pendingCinematic;
    bool pendingCinematicSkip = false;
    std::vector<CameraShakeRequest> cameraShakeRequests;
    bool pendingReturnToMainMenu = false;
    // AddValue(Experience) gives the value as it is, past the rules' event experience (MAW's unscaled rewards).
    bool unscaledExperience = false;
    std::optional<PendingInputPrompt> pendingInputPrompt;
    std::optional<PendingArcomageGame> pendingArcomageGame;
    std::vector<PendingSound> pendingSounds;
    std::vector<uint32_t> lastAffectedMechanismIds;
    std::optional<std::string> lastActivationResult;
    size_t localOnLoadEventsExecuted = 0;
    size_t globalOnLoadEventsExecuted = 0;
    int32_t processedMapRespawnCount = 0;

    bool hasFacetInvisibleOverride(uint32_t faceId) const;
};

struct EventRuntimeBindingReport
{
    size_t localEventCount = 0;
    size_t localHandlerCount = 0;
    size_t globalEventCount = 0;
    size_t globalHandlerCount = 0;
    size_t canShowTopicEventCount = 0;
    size_t canShowTopicHandlerCount = 0;
    std::vector<uint16_t> missingLocalHandlerEventIds;
    std::vector<uint16_t> missingGlobalHandlerEventIds;
    std::vector<uint16_t> missingCanShowTopicEventIds;
    std::optional<std::string> errorMessage;
};

void clearTransientEventRuntimeState(EventRuntimeState &runtimeState);
std::vector<uint32_t> consumeOpenedChestIds(EventRuntimeState &runtimeState);
std::vector<EventRuntimeState::OpenedChestRequest> consumeOpenedChestRequests(EventRuntimeState &runtimeState);
uint32_t normalizedHistoryContinentId(uint32_t continentId);
// Game minute of a history entry every party knows from the start, if historyId is one.
std::optional<int32_t> forwardHistoryEntryTime(uint32_t continentId, uint32_t historyId);
void setActiveHistoryContinent(EventRuntimeState &runtimeState, uint32_t continentId);
const std::unordered_map<uint32_t, int32_t> &historyEventTimesForActiveContinent(
    const EventRuntimeState &runtimeState);

// Turns the aimed decorations toward their aims and plays their recoils on by deltaSeconds.
void advanceDecorationAims(EventRuntimeState &state, float deltaSeconds);
void advanceDecorationClips(EventRuntimeState &state, float deltaSeconds);
// A chest opened by a decoration's click plays the decoration's "open" clip, and its "close" clip when the chest view
// closes (a part without them stays still).
void openChestDecoration(EventRuntimeState &state, const EventRuntimeState::OpenedChestRequest &request);
void closeChestDecoration(EventRuntimeState &state);
// The clip the decorations with this sprite override key play (evt.PlayDecorationClip); false for none.
bool decorationClipFor(const EventRuntimeState *pState, uint32_t key, std::string &clip, float &seconds, bool &loop);
// Runs the actor presentations' clip and turn clocks by deltaSeconds.
void advanceActorPresentations(EventRuntimeState &state, float deltaSeconds);
// Starts a decoration's glide to offset (world units from its map position) over seconds (0: at once).
void moveDecoration(EventRuntimeState &state, uint32_t key, const std::array<float, 3> &offset, float seconds);

class EventRuntime
{
public:
    EventRuntime(const HouseTable *pHouseTable = nullptr, const NpcDialogTable *pNpcDialogTable = nullptr);
    ~EventRuntime();

    EventRuntime(const EventRuntime &) = delete;
    EventRuntime &operator=(const EventRuntime &) = delete;

    EventRuntime(EventRuntime &&other) noexcept;
    EventRuntime &operator=(EventRuntime &&other) noexcept;

    void bindHouseTable(const HouseTable *pHouseTable);
    const HouseTable *houseTable() const;
    void bindNpcDialogTable(const NpcDialogTable *pNpcDialogTable);
    const NpcDialogTable *npcDialogTable() const;

    static uint32_t outdoorModelFacetTextureOverrideKey(uint32_t modelIndex, uint32_t faceIndex);
    // The textureOverrides key of one indoor face named by its index (cog numbers are 16-bit, so never collide).
    // One indoor face named by a negative event reference (MMerge's MM6 maps), apart from the cog numbers.
    static uint32_t indoorFaceReferenceKey(uint32_t faceIndex);
    static uint32_t monsterRelationOverrideKey(uint32_t leftMonsterId, uint32_t rightMonsterId);
    static uint64_t transportRouteOverrideKey(uint32_t houseId, uint32_t routeIndex);

    static float calculateMechanismDistance(const MapDeltaDoor &door, const RuntimeMechanismState &runtimeMechanism);
    void initializeMapRuntimeState(
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState
    ) const;
    bool buildOnLoadState(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeOnLoadEvents(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeOnLeaveEvents(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool validateProgramBindings(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeBindingReport &report
    ) const;
    bool executeEventById(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t eventId,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr,
        std::optional<uint8_t> continueStep = std::nullopt,
        bool allowGlobalFallback = true,
        std::optional<ScriptedEventScope> requiredScope = std::nullopt,
        bool preservePendingOutputsOnBegin = false
    ) const;
    bool executeNpcTopicEventById(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t eventId,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr,
        std::optional<uint8_t> continueStep = std::nullopt
    ) const;
    bool canShowTopic(
        const std::optional<ScriptedEventProgram> &globalProgram,
        uint16_t topicId,
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        const ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeHooks(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        EventRuntimeHookKind kind,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    bool executeMapRefillHooks(
        const std::optional<ScriptedEventProgram> &localProgram,
        const std::optional<ScriptedEventProgram> &globalProgram,
        const std::optional<MapDeltaData> &mapDeltaData,
        EventRuntimeState &runtimeState,
        Party *pParty = nullptr,
        ISceneEventContext *pSceneEventContext = nullptr
    ) const;
    void advanceMechanisms(
        const std::optional<MapDeltaData> &mapDeltaData,
        float deltaMilliseconds,
        EventRuntimeState &runtimeState
    ) const;

    enum class VariableKind
    {
        Generic,
        PartyState,
        CharacterState,
        QBits,
        BoolFlag,
        AutoNote,
        History,
        Food,
        Inventory,
        Awards,
        Players,
        CircusPrises,
        ClassId,
        Experience,
        CurrentHealth,
        MaxHealth,
        CurrentSpellPoints,
        MaxSpellPoints,
        Hour,
        DayOfYear,
        DayOfWeek,
        Gold,
        GoldInBank,
        BaseLevel,
        LevelBonus,
        Sex,
        Race,
        Age,
        ArmorClass,
        ArmorClassBonus,
        BaseStat,
        ActualStat,
        StatMoreThanBase,
        StatBonus,
        BaseResistance,
        ResistanceBonus,
        Skill,
        Condition,
        MajorCondition,
        MapPersistent,
        DecorPersistent,
    };

    struct VariableRef
    {
        VariableKind kind = VariableKind::Generic;
        uint32_t rawId = 0;
        uint16_t tag = 0;
        uint32_t index = 0;
    };

    // A packed selector: index * 65536 + tag. 64 bits wide, so QBit ids above 65535 (the worlds' own blocks, Hesper's
    // 100000+) survive the packing.
    static VariableRef decodeVariable(uint64_t rawId);
    static int32_t getVariableValue(
        const EventRuntimeState &runtimeState,
        const VariableRef &variable,
        const Party *pParty,
        const std::optional<size_t> &memberIndex = std::nullopt,
        const ISceneEventContext *pSceneEventContext = nullptr
    );
    static void setVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices,
        const ISceneEventContext *pSceneEventContext = nullptr
    );
    static void addVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices,
        const ISceneEventContext *pSceneEventContext = nullptr
    );
    static void subtractVariableValue(
        EventRuntimeState &runtimeState,
        const VariableRef &variable,
        int32_t value,
        Party *pParty,
        const std::vector<size_t> &targetMemberIndices
    );
    static void setQuestBitValue(
        EventRuntimeState &runtimeState,
        Party &party,
        uint32_t qbitId,
        bool value,
        const std::vector<size_t> &targetMemberIndices = {});
    static void applyMechanismAction(
        RuntimeMechanismState &runtimeMechanism,
        const MapDeltaDoor *pDoor,
        MechanismAction action);
    static int32_t getInventoryItemCount(
        const EventRuntimeState &runtimeState,
        const Party *pParty,
        uint32_t objectDescriptionId,
        const std::optional<size_t> &memberIndex = std::nullopt
    );
    mutable std::unique_ptr<LuaSessionCache> m_luaSessionCache;
    mutable const ScriptedEventProgram *m_pCachedLocalProgram = nullptr;
    mutable const ScriptedEventProgram *m_pCachedGlobalProgram = nullptr;
    mutable uint64_t m_cachedLocalProgramCacheId = 0;
    mutable uint64_t m_cachedGlobalProgramCacheId = 0;
    const HouseTable *m_pHouseTable = nullptr;
    const NpcDialogTable *m_pNpcDialogTable = nullptr;
};
}
