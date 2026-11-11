#pragma once

#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "game/app/GameApplication.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/party/Party.h"

#include <array>
#include <cstddef>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class CombatLog;
class TurnBasedCombatRuntime;
class MawRules;
struct ScenarioPose
{
    std::string mapFileName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
};

struct ScenarioInteractionResult
{
    bool picked = false;
    bool activated = false;
    std::string mapFileName;
    GameplayWorldHit hit = {};
};

struct ScenarioMovementCommand
{
    ScenarioPose startPose = {};
    float durationSeconds = 0.0f;
    bool forward = true;
    bool backward = false;
    bool strafeLeft = false;
    bool strafeRight = false;
    bool jump = false;
    bool flyUp = false;
    bool flyDown = false;
    bool shift = false;
    bool ctrl = false;
    bool actorCollision = true;
    bool actorAi = true;
    std::optional<float> endYawRadians;
    std::optional<float> endPitchRadians;
};

// The party's water state on a map with scene water volumes (assert `water`).
struct ScenarioWaterStatus
{
    std::string state;
    bool eyeUnder = false;
    float breath = 1.0f;
    uint32_t drowningTicks = 0;
    float footZ = 0.0f;
};

struct ScenarioMovementResult
{
    ScenarioPose startPose = {};
    ScenarioPose finalPose = {};
};

// walk_to: the party walks to a point as a player would, with the movement keys only. The route comes from the
// monsters' indoor path planner (straight on outdoor maps); the party turns toward each waypoint and holds Forward,
// jumps when stuck and plans again from where it stands.
struct ScenarioWalkRequest
{
    std::vector<ScenarioPose> points;           // the hand-placed waypoints, the last one the target
    float arriveRadius = 64.0f;
    std::optional<float> zTolerance;            // arrival also needs the feet this near the target's height
    float timeoutSeconds = 180.0f;
    float clearHostilesRadius = 0.0f;           // kills the party's enemies this near every half second (0: none)
    std::string expectMap;                      // arriving on this map ends the walk (an exit on the way)
    bool plan = true;
    size_t nodeLimit = 400000;
    bool closeDialogs = false;                  // a dialogue an event opens on the way is closed, else it ends the walk
};

struct ScenarioWalkResult
{
    bool arrived = false;
    bool dialogOpened = false;
    float seconds = 0.0f;
    size_t replans = 0;
    size_t jumps = 0;
    size_t clicks = 0;
    size_t hostilesKilled = 0;
    size_t closedDialogs = 0;
    std::vector<std::string> trail;             // positions and events along the way, the run's evidence
    ScenarioPose finalPose = {};
};

struct ScenarioCombatLootRequest
{
    std::optional<size_t> actorIndex;
    std::string targetName;
    uint32_t expectedItemId = 0;
};

struct ScenarioCombatLootResult
{
    size_t actorIndex = GameplayInvalidWorldIndex;
    bool damageApplied = false;
    bool corpseActivated = false;
    bool worldItemActivated = false;
    bool expectedItemExposed = false;
    bool expectedItemAcquired = false;
};

// A party member's real attacks on an actor (party_attack), the actor healed after each so it stays up.
struct ScenarioPartyAttackRequest
{
    size_t actorIndex = 0;
    size_t memberIndex = 0;
    int count = 1;
    // Conditions the member has for these attacks; they are lifted again afterwards.
    std::vector<CharacterCondition> conditions;
    // The member's attack spell for these attacks (restored afterwards); when set, the attacks go through the
    // gameplay runtime and spell service, so a castable attack spell is really cast.
    std::optional<std::string> attackSpell;
};

// A spell a party member casts (cast_spell): its school skill set first when `skill` is given, from a scroll at that
// skill when `scroll`, on an actor or a member.
struct ScenarioSpellCastRequest
{
    size_t memberIndex = 0;
    uint32_t spellId = 0;
    uint32_t skill = 0;
    SkillMastery mastery = SkillMastery::None;
    std::optional<size_t> actorIndex;
    std::optional<size_t> targetMemberIndex;
    // A ground point (Meteor Shower, Starburst and the other spells cast at the ground).
    std::optional<std::array<float, 3>> targetPoint;
    bool scroll = false;
};

struct ScenarioPartyAttackResult
{
    int attacks = 0;
    int hits = 0;
    int criticals = 0;
    // Attacks that swung or shot a weapon (an attack spell cast instead does not count).
    int weaponAttacks = 0;
    // Per landed hit: the damage the rules resolved for the blow, and the HP the actor lost.
    double averageDamage = 0;
    double averageAppliedDamage = 0;
    double averageRecoverySeconds = 0;
};

struct ScenarioDialogActionSnapshot
{
    size_t index = 0;
    std::string kind;
    uint32_t id = 0;
    uint32_t secondaryId = 0;
    bool enabled = true;
    bool textOnly = false;
    std::string label;
};

struct ScenarioDialogSnapshot
{
    bool active = false;
    bool houseDialog = false;
    uint32_t sourceId = 0;
    std::string title;
    std::string houseTitle;
    size_t lineCount = 0;
    uint64_t textHash = 0;
    // The lines joined with newlines.
    std::string text;
    std::vector<ScenarioDialogActionSnapshot> actions;
};

struct ScenarioInputPromptSnapshot
{
    bool active = false;
    uint16_t eventId = 0;
    uint8_t continueStep = 0;
    uint8_t correctStep = 0;
    uint32_t textId = 0;
    std::string text;
    size_t answerCount = 0;
};

struct ScenarioInputPromptAnswerResult
{
    ScenarioInputPromptSnapshot prompt = {};
    bool matched = false;
    size_t matchedIndex = 0;
    uint8_t selectedContinueStep = 0;
};

class ScenarioRuntimeDriver
{
public:
    ScenarioRuntimeDriver(
        const std::filesystem::path &basePath,
        const Engine::ApplicationConfig &config,
        Engine::AssetFileSystem &assetFileSystem);
    ~ScenarioRuntimeDriver();

    bool initialize(std::string &failure);
    // Keeps MAW's Beyond Madness death ledger in the scenario's save folder, not the game's.
    void setMadnessLedgerFile(const std::filesystem::path &file);
    void setPlaythroughStatisticsDirectory(const std::filesystem::path &directory);
    bool startNewGame(
        uint32_t continentId,
        const std::string &startMapFileName,
        std::string &failure,
        const PartySeed *pSeed = nullptr,
        const RulesetSelection &ruleset = {});
    // The ruleset of the running session.
    const RulesetSelection &ruleset() const;
    // The running MAW game's rules, or nothing (Standard).
    const MawRules *mawRules() const;
    const CombatLog &combatLog() const;
    bool holdGameplayAction(KeyboardAction action, float seconds, std::string &failure);
    bool selectPartyMember(size_t memberIndex, std::string &failure);
    bool loadMap(const std::string &mapFileName, std::string &failure);
    bool processPendingMapMove(std::string &failure);
    bool openMapTransitionPrompt(uint32_t sourceId, std::string &failure);
    bool speakNpc(uint32_t npcId, std::string &failure);
    // Saves under the name the Load screen shows.
    bool saveGameToPath(const std::filesystem::path &path, const std::string &saveName, std::string &failure);
    bool loadGameFromPath(const std::filesystem::path &path, std::string &failure);
    // One press of the quick load key (F10), loading `savePath` as the quicksave: the game's quicksave path is
    // relative, so the press runs with `workDirectory` (a scenario folder) as the working directory. `loaded` says
    // whether the press loaded; `status` is the status bar text afterwards.
    bool pressQuickLoad(
        const std::filesystem::path &savePath,
        const std::filesystem::path &workDirectory,
        bool &loaded,
        std::string &status,
        std::string &failure);
    bool setPose(const ScenarioPose &pose, std::string &failure);
    ScenarioPose currentPose() const;
    bool simulateMovementSegment(
        const ScenarioMovementCommand &command,
        ScenarioMovementResult &result,
        std::string &failure);
    bool walkTo(const ScenarioWalkRequest &request, ScenarioWalkResult &result, std::string &failure);
    // Kills the party's living enemies within `radius` of it through the ordinary damage path (deaths, corpses and
    // loot as in combat); `killed` counts them.
    bool killHostilesNear(float radius, size_t &killed, std::string &failure);
    // Lets the world run until nobody in the party can act (at most waitSeconds; knockOut: every member falls at
    // once), then the game's defeat: the respawn at the world's death destination (its movie skipped); `destination`
    // is the map it woke on.
    bool defeatParty(float waitSeconds, bool knockOut, std::string &destination, std::string &failure);
    // Why a player could not save now (a dialogue, a chest, a cinematic or a map move in progress), empty when
    // they could.
    std::string saveBlockedReason();
    // Climbs a ladder of the map (its scene id) as a player does: walks to its foot (down: to its top exit), faces it
    // and holds the movement keys until the ladder's own rules let go of the party at the other end. Down needs a
    // ladder that can be taken from its top. `trail` gets what happened.
    bool climbLadder(const std::string &ladderId, bool down, float timeoutSeconds, std::vector<std::string> &trail,
        std::string &failure);
    // Picks up an item lying in the map as a player does: the nearest of this id within `reach` of the party's eye,
    // the camera turned at it, the use key pressed (the game's pick). `log` says what happened.
    bool pickUpWorldItem(uint32_t itemId, float reach, std::string &log, std::string &failure);
    // A bank's amount box (house Deposit or Withdraw) is open.
    bool houseBankInputActive();
    // Types the amount into the bank's box and confirms it, as Enter does (GameplayScreenRuntime::confirmHouseBankInput).
    bool answerHouseBankInput(const std::string &text, std::string &failure);
    // The item on the cursor (0: none).
    uint32_t heldCursorItemId();
    // The open chest's Take All: false when no chest is open.
    bool takeAllFromOpenChest(std::string &failure);
    // The Immortal cheat for this run only: settings.ini is not written.
    bool setPartyImmortal(bool immortal, std::string &failure);
    bool waterStatus(ScenarioWaterStatus &status, std::string &failure);
    bool actorInspectState(
        size_t actorIndex,
        GameplayActorInspectState &inspectState,
        GameplayRuntimeActorState &runtimeState,
        bool &hasRuntimeState,
        std::string &failure) const;
    ScenarioInteractionResult pressKeyboardInteract(std::string &failure);
    ScenarioInteractionResult pressKeyboardInteractWithEventTargetActorOcclusion(
        uint32_t expectedTargetKind,
        size_t expectedTargetIndex,
        size_t expectedSecondaryIndex,
        uint16_t expectedTriggeredEventId,
        std::optional<uint16_t> expectedTrigger,
        bool &usedActorlessPick,
        std::string &failure);
    bool executeMapEvent(uint16_t eventId, std::string &failure);
    // A scenario's own Lua (lua_event) run as an event of the current map, after the map's event support.
    bool runLuaEvent(const std::string &source, std::string &failure);
    bool selectDialogAction(size_t actionIndex, std::string &failure);
    bool selectDialogActionById(uint32_t actionId, std::string &failure);
    bool answerPendingInputPrompt(
        const std::string &text,
        ScenarioInputPromptAnswerResult &result,
        std::string &failure);
    ScenarioInputPromptSnapshot activeInputPromptSnapshot() const;
    bool closeDialog(std::string &failure);
    ScenarioDialogSnapshot activeDialogSnapshot() const;
    // The quick item ring's member while it is open (the potion radial), else none.
    std::optional<size_t> quickItemRingMember() const;
    // The basebar popup open ("potions", "scrolls" or "none") and its member.
    std::pair<std::string, size_t> quickItemPopup() const;
    std::string activeDialogSummary() const;
    // presentDialogs: a dialogue that a world event queued during the step is presented at once, as the game's frame
    // presents it (off by default: older scenarios open queued dialogues themselves).
    bool advanceRuntime(float seconds, std::string &failure, bool presentDialogs = false,
        bool followMapMove = false);
    bool advanceGameMinutes(float minutes, std::string &failure);
    // The days of a journey as the game's own travel passes them (applyTravelDaysSideEffects): the party rests on the
    // road, so they are not days without rest.
    bool travelDays(float days, std::string &failure);
    // The turn engine of the running game (turn_based_turns, assert turn_based).
    const TurnBasedCombatRuntime &turnBasedCombat() const;
    // Plays `turns` turn-based turns from the live input path: the party presses Pass whenever it may (each ready
    // member passes, each movement phase ends) and the monsters take their turns. A turn counts when it reaches its
    // movement phase. False when that takes longer than maxSeconds of game frames or turn-based mode ends.
    bool playTurnBasedTurns(int turns, float maxSeconds, int &completed, std::string &failure);
    bool executeCombatLoot(
        const ScenarioCombatLootRequest &request,
        ScenarioCombatLootResult &result,
        std::string &failure);
    ScenarioInteractionResult activateActor(size_t actorIndex, std::string &failure);
    // A party melee hit on a living actor through the normal damage path (it turns on the party, alerts its kin);
    // shieldTier: what the hit is to an energy shield.
    bool damageActor(size_t actorIndex, int amount, ShieldAttackTier shieldTier, std::string &failure);
    bool partyAttack(
        const ScenarioPartyAttackRequest &request, ScenarioPartyAttackResult &result, std::string &failure);
    // Applies colon-separated ruleset option ids to the game in progress, as the pause menu's Rules tab does.
    bool setRulesetOptions(const std::string &optionIds, std::string &failure);
    // Hostile monsters of a table row summoned at a point (outdoor maps), as the console's actor spawn does; they
    // are appended after the map's actors. A boss affix (the ruleset's id) makes them bosses with it; a party ally is
    // summoned as a party spell's summon instead.
    bool spawnActor(int16_t monsterId, uint32_t count, float x, float y, float z, uint32_t group, uint8_t bossAffix,
        bool partyAlly, std::string &failure);
    // Sets up an AI arena (game/debug/AiArena.h), loading its map first when another one (or none) is loaded;
    // logPath: the trace log (empty: none).
    bool applyAiArena(const AiArena &arena, const std::filesystem::path &logPath, std::string &failure);
    // The arena's decision trace and its monsters' actor indices in arena order.
    const ActorAiTrace &aiTrace() const;
    const std::vector<size_t> &aiArenaActorIndices() const;
    // Actors on the active map (0 without one).
    size_t mapActorCount() const;
    // The actor fires its attack or spell at the party now, as an AI shot (a true_aim monster's shot homes).
    bool fireActorProjectileAtParty(size_t actorIndex, GameplayActorAttackAbility ability, int damage,
        std::string &failure);
    // The actor blinks now as its blink modifier would.
    bool blinkActor(size_t actorIndex, std::string &failure);
    // The actor starts its charge at the party now (its charge modifier's wind-up, then the dash).
    bool chargeActor(size_t actorIndex, std::string &failure);
    // The actor starts its frenzy now (its frenzy modifier's roar, then the frenzy).
    bool frenzyActor(size_t actorIndex, std::string &failure);
    // The map's charges so far (empty without a map that runs them).
    std::optional<GameplayChargeCounts> chargeCounts() const;
    // The active map's projectiles (null without a map).
    const GameplayProjectileService *projectileService() const;
    ScenarioInteractionResult activateWorldItem(
        size_t worldItemIndex,
        std::optional<uint16_t> recordedObjectDescriptionId,
        std::optional<uint16_t> recordedSpriteId,
        std::string &failure);
    bool worldItemContainsItem(
        std::optional<size_t> worldItemIndex,
        uint32_t itemId,
        bool &containsItem,
        std::string &failure) const;
    bool activeChestContainsItem(
        std::optional<uint32_t> chestId,
        uint32_t itemId,
        bool &containsItem,
        std::string &failure) const;
    bool takeActiveChestItemById(
        std::optional<uint32_t> chestId,
        uint32_t itemId,
        GameplayChestItemState &item,
        std::string &failure);
    bool takeInventoryItemToCursor(size_t memberIndex, uint8_t gridX, uint8_t gridY, std::string &failure);
    bool placeHeldItemInInventory(std::string &failure);
    // The cursor item into the first member's packs it fits, the active member first (a player drops it on a portrait).
    bool placeHeldItemInAnyMemberInventory();
    // A MAW game's banked levels by world (Jadame, Antagarich, Enroth, other); false outside MAW.
    bool setRulesetBanks(const std::array<double, 4> &levels, std::string &failure);
    // The MAW rules of the game, or null outside MAW.
    MawRules *mawRules();
    // Runs a debug console line as typed; output gets what the console printed. False when it reported an error.
    bool runConsoleLine(const std::string &line, std::string &output, std::string &failure);
    // Puts the item into the member's pack, or with `equipSlot` onto the member (whatever was there goes to the pack).
    bool grantItem(
        size_t memberIndex,
        const InventoryItem &item,
        uint32_t count,
        std::optional<EquipmentSlot> equipSlot,
        std::string &failure);
    // Uses (drinks, reads) the first pack item of this id on the member through the inventory's use path, as a
    // right-click on the portrait does; `used` tells whether the game took it.
    bool useInventoryItem(size_t memberIndex, uint32_t itemId, bool &used, std::string &failure);
    // Right-clicks the target member's portrait with the carrier's first pack item of this id under the cursor,
    // through the live input path (on the inventory page when `inventoryOpen`). By default the press lands on the
    // portrait and a scroll's text must close with the release; with `releaseOverPortrait` (Modern controls) the
    // press lands on the screen centre, the release on the portrait, and a scroll's text must stay until a left
    // click, which must not drop the item. `used` tells whether the item was used or its text shown; a broken rule
    // is a failure.
    bool rightClickPortraitWithItem(
        size_t carrierIndex,
        size_t targetIndex,
        uint32_t itemId,
        bool inventoryOpen,
        bool releaseOverPortrait,
        bool &used,
        std::string &failure);
    // Casts the spell through the party's spell system with full mana and no recovery left (the rules' auras, heals
    // and splashes, the world's projectiles); `status` is the cast's outcome.
    bool castSpell(const ScenarioSpellCastRequest &request, PartySpellCastStatus &status, std::string &failure);
    // The Knight Charge action at the actor (party_charge): the rules' status line, or nothing without a charge.
    bool partyCharge(std::optional<size_t> actorIndex, std::optional<std::string> &status, std::string &failure);
    // The Workbench's crafting with a material on the member's item (worn in `wornSlot`, else the first pack item of
    // the id); `all` is Apply All and `choice` the option picked (the Pearl's enchantment). `crafted` tells whether the
    // step was applied.
    bool craftItem(
        size_t memberIndex,
        uint32_t targetItemId,
        std::optional<EquipmentSlot> wornSlot,
        uint32_t materialItemId,
        bool all,
        size_t choice,
        bool &crafted,
        std::string &reason,
        std::string &failure);
    // The Workbench's gem merge of this tier, once or as often as the gems allow.
    bool combineGems(uint32_t gemItemId, bool all, bool &combined, std::string &failure);
    bool triggerIndoorPressurePlate(size_t faceIndex, std::string &failure);
    bool triggerIndoorEventTarget(size_t faceIndex, std::string &failure);
    bool activeCorpseContainsItem(
        std::optional<uint32_t> sourceIndex,
        uint32_t itemId,
        bool &containsItem,
        std::string &failure) const;

    bool hasActiveRuntime() const;
    const std::string &currentMapFileName() const;
    float gameMinutes() const;
    void setPartyState(const Party &party);
    void setEventRuntimeState(const EventRuntimeState &eventRuntimeState);
    void setGameMinutes(float gameMinutes);
    Party *party();
    const Party *party() const;
    EventRuntimeState *eventRuntimeState();
    const EventRuntimeState *eventRuntimeState() const;
    const IGameplayWorldRuntime *worldRuntime() const;

private:
    IGameplayWorldRuntime *worldRuntime();
    bool loadSelectedMapRuntime(const std::string &mapFileName, std::string &failure);
    GameplayWorldPickRequest buildCenterPickRequest();
    ScenarioInteractionResult pickCenterInteractionTarget(bool ignoreActors, std::string &failure);
    bool activateInteractionResult(ScenarioInteractionResult &result, std::string &failure);
    void presentGrantedEventItems();
    // One gameplay frame with this input, as simulateMovementSegment and walkTo run it.
    bool advanceMovementFrame(const GameplayInputFrame &input, float deltaSeconds, bool actorAi, std::string &failure);
    std::vector<ScenarioPose> planWalkRoute(const ScenarioPose &from, const ScenarioPose &to, size_t nodeLimit,
        std::string &status);

    std::filesystem::path m_basePath;
    Engine::ApplicationConfig m_config;
    Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    GameApplication m_application;
    bool m_initialized = false;
};
}
